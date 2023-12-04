from contextlib import suppress

from core.helpers import get_current_site_url
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch, Q, QuerySet
from django.http import (
    Http404,
    HttpRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.edit import FormView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from organisations.models import Organisation, UserOrganisation
from organisations.permissions.permissions import (
    MANAGE_USER_GROUPS,
    NestedIsOrganisationAdminPermission,
    OrganisationUsersPermission,
    UserPermissionGroupPermission,
)
from organisations.serializers import UserOrganisationSerializer
from users.models import (
    FFAdminUser,
    UserPermissionGroup,
    UserPermissionGroupMembership,
)
from users.serializers import (
    ListUserPermissionGroupSerializer,
    ListUsersQuerySerializer,
    UserIdsSerializer,
    UserListSerializer,
    UserPermissionGroupSerializerDetail,
    UserPermissionGroupSummarySerializer,
)
from users.services import (
    create_initial_superuser,
    should_skip_create_initial_superuser,
)

from .forms import InitConfigForm


class InitialConfigurationView(PermissionRequiredMixin, FormView):
    template_name = "users/onboard.html"
    form_class = InitConfigForm
    permission_denied_message = (
        "FAILED TO INIT Configuration. USER(S) ALREADY EXIST IN SYSTEM."
    )

    def has_permission(self):
        return not should_skip_create_initial_superuser()

    def handle_no_permission(self):
        raise Http404("CAN NOT INIT CONFIGURATION. USER(S) ALREADY EXIST IN SYSTEM.")

    def form_valid(self, form):
        form.update_site()
        password_reset_url = form.create_admin().password_reset_url
        return JsonResponse(
            {
                "message": "INSTALLATION CONFIGURED SUCCESSFULLY",
                "passwordResetUrl": password_reset_url,
            }
        )


class AdminInitView(View):
    def get(self, request):
        if should_skip_create_initial_superuser():
            return JsonResponse(
                {
                    "adminUserCreated": False,
                    "message": "FAILED TO INIT ADMIN USER. USER(S) ALREADY EXIST IN SYSTEM.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = create_initial_superuser()
        return JsonResponse(
            {
                "adminUserCreated": True,
                "passwordResetUrl": response.password_reset_url,
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(
    decorator=swagger_auto_schema(query_serializer=ListUsersQuerySerializer()),
    name="list",
)
class FFAdminUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, OrganisationUsersPermission)
    pagination_class = None

    def get_queryset(self):
        if self.kwargs.get("organisation_pk"):
            queryset = FFAdminUser.objects.prefetch_related(
                Prefetch(
                    "userorganisation_set",
                    queryset=UserOrganisation.objects.select_related("organisation"),
                )
            ).filter(organisations__id=self.kwargs.get("organisation_pk"))
            queryset = self._apply_query_filters(queryset)
            return queryset
        else:
            return FFAdminUser.objects.none()

    def _apply_query_filters(self, queryset: QuerySet):
        serializer = ListUsersQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        filter_data = serializer.data

        if filter_data.get("exclude_current"):
            queryset = queryset.exclude(id=self.request.user.id)

        return queryset

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "update_role":
            return UserOrganisationSerializer

        return UserListSerializer

    def get_serializer_context(self):
        context = super(FFAdminUserViewSet, self).get_serializer_context()
        if self.kwargs.get("organisation_pk"):
            context["organisation"] = Organisation.objects.get(
                pk=self.kwargs.get("organisation_pk")
            )
        return context

    @action(detail=True, methods=["POST"], url_path="update-role")
    def update_role(self, request, organisation_pk, pk):
        user = self.get_object()
        organisation = Organisation.objects.get(pk=organisation_pk)
        user_organisation = user.get_user_organisation(organisation)

        serializer = self.get_serializer(
            instance=user_organisation, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            UserListSerializer(user, context={"organisation": organisation}).data
        )


def password_reset_redirect(
    request: HttpRequest,
    uidb64: str,
    token: str,
) -> HttpResponseRedirect:
    current_site_url = get_current_site_url(request)
    return redirect(f"{current_site_url}/password-reset/{uidb64}/{token}")


class UserPermissionGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, UserPermissionGroupPermission]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return UserPermissionGroup.objects.none()

        organisation_pk = self.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_pk)

        qs = UserPermissionGroup.objects.filter(organisation=organisation)
        if (
            self.action != "summaries"
            and not self.request.user.has_organisation_permission(
                organisation, MANAGE_USER_GROUPS
            )
        ):
            # my_groups and summaries return a very cut down set of data, we can safely allow all users
            # of the groups / organisation to retrieve them in this case, otherwise they must be a group admin.
            q = Q(userpermissiongroupmembership__ffadminuser=self.request.user)
            if self.action != "my_groups":
                q = q & Q(userpermissiongroupmembership__group_admin=True)
            qs = qs.filter(q)

        return qs

    def paginate_queryset(self, queryset: QuerySet) -> list[UserPermissionGroup] | None:
        if self.action == "summaries":
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserPermissionGroupSerializerDetail
        elif self.action in ("my_groups", "summaries"):
            return UserPermissionGroupSummarySerializer
        return ListUserPermissionGroupSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False) and self.detail is True:
            with suppress(ValueError):
                context["group_admins"] = UserPermissionGroupMembership.objects.filter(
                    userpermissiongroup__id=int(self.kwargs["pk"]), group_admin=True
                ).values_list("ffadminuser__id", flat=True)
        return context

    def perform_create(self, serializer):
        serializer.save(organisation_id=self.kwargs["organisation_pk"])

    def perform_update(self, serializer):
        serializer.save(organisation_id=self.kwargs["organisation_pk"])

    @swagger_auto_schema(
        request_body=UserIdsSerializer,
        responses={200: UserPermissionGroupSerializerDetail},
    )
    @action(detail=True, methods=["POST"], url_path="add-users")
    def add_users(self, request, organisation_pk, pk):
        group = self.get_object()
        user_ids = request.data["user_ids"]

        if request.user.id in user_ids and not request.user.is_organisation_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            raise PermissionDenied("Non-admin users cannot add themselves to a group.")

        try:
            group.add_users_by_id(user_ids)
        except FFAdminUser.DoesNotExist as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(UserPermissionGroupSerializerDetail(instance=group).data)

    @swagger_auto_schema(
        request_body=UserIdsSerializer,
        responses={200: UserPermissionGroupSerializerDetail},
    )
    @action(detail=True, methods=["POST"], url_path="remove-users")
    def remove_users(self, request, organisation_pk, pk):
        group = self.get_object()
        user_ids = request.data["user_ids"]

        if request.user.id in user_ids and not request.user.is_organisation_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            raise PermissionDenied(
                "Non-admin users cannot remove themselves from a group."
            )

        group.remove_users_by_id(user_ids)
        return Response(UserPermissionGroupSerializerDetail(instance=group).data)

    @action(detail=False, methods=["GET"], url_path="my-groups")
    def my_groups(self, request: Request, organisation_pk: int) -> Response:
        """
        Returns a list of summary group objects only for the groups a user is a member of.
        """
        return self.list(request, organisation_pk)

    @action(detail=False, methods=["GET"])
    def summaries(self, request: Request, organisation_pk: int) -> Response:
        """
        Returns a list of summary group objects for all groups in the organisation.
        """
        return self.list(request, organisation_pk)


@api_view(["POST"])
@permission_classes([IsAuthenticated, NestedIsOrganisationAdminPermission])
def make_user_group_admin(
    request: Request, organisation_pk: int, group_pk: int, user_pk: int
) -> Response:
    user = get_object_or_404(
        FFAdminUser,
        userorganisation__organisation_id=organisation_pk,
        permission_groups__id=group_pk,
        id=user_pk,
    )
    user.make_group_admin(group_pk)
    return Response()


@api_view(["POST"])
@permission_classes([IsAuthenticated, NestedIsOrganisationAdminPermission])
def remove_user_as_group_admin(
    request: Request, organisation_pk: int, group_pk: int, user_pk: int
) -> Response:
    user = get_object_or_404(
        FFAdminUser,
        userorganisation__organisation_id=organisation_pk,
        permission_groups__id=group_pk,
        id=user_pk,
    )
    user.remove_as_group_admin(group_pk)
    return Response()
