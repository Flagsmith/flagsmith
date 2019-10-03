from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organisations.models import Organisation
from organisations.permissions import NestedOrganisationEntityPermission
from organisations.serializers import OrganisationSerializerFull, UserOrganisationSerializer
from users.exceptions import InvalidInviteError
from users.models import FFAdminUser, Invite
from users.serializers import UserListSerializer


class AdminInitView(View):
    def get(self, request):
        if FFAdminUser.objects.count() == 0:
            admin = FFAdminUser.objects.create_superuser(
                settings.ADMIN_EMAIL,
                settings.ADMIN_INITIAL_PASSWORD,
                is_active=True,
            )
            admin.save()
            return HttpResponse("ADMIN USER CREATED")
        else:
            return HttpResponse("FAILED TO INIT ADMIN USER. USER(S) ALREADY EXIST IN SYSTEM.")


class FFAdminUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, NestedOrganisationEntityPermission)
    pagination_class = None

    def get_queryset(self):
        if self.kwargs.get('organisation_pk'):
            return FFAdminUser.objects.filter(organisations__id=self.kwargs.get('organisation_pk'))
        else:
            return FFAdminUser.objects.none()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'update_role':
            return UserOrganisationSerializer

        return UserListSerializer

    def get_serializer_context(self):
        context = super(FFAdminUserViewSet, self).get_serializer_context()
        if self.kwargs.get('organisation_pk'):
            context['organisation'] = Organisation.objects.get(pk=self.kwargs.get('organisation_pk'))
        return context

    @action(detail=True, methods=['POST'], url_path='update-role')
    def update_role(self, request, organisation_pk, pk):
        user = self.get_object()
        organisation = Organisation.objects.get(pk=organisation_pk)
        user_organisation = user.get_user_organisation(organisation)

        serializer = self.get_serializer(instance=user_organisation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserListSerializer(user, context={'organisation': organisation}).data)


def password_reset_redirect(request, uidb64, token):
    protocol = "https" if request.is_secure() else "https"
    current_site = get_current_site(request)
    domain = current_site.domain
    return redirect(protocol + "://" + domain + "/password-reset/" + uidb64 + "/" + token)


@api_view(['POST'])
def join_organisation(request, invite_hash):
    invite = get_object_or_404(Invite, hash=invite_hash)

    try:
        request.user.join_organisation(invite)
    except InvalidInviteError as e:
        error_data = {'detail': str(e)}
        return Response(data=error_data, status=status.HTTP_400_BAD_REQUEST)

    return Response(OrganisationSerializerFull(invite.organisation).data, status=status.HTTP_200_OK)
