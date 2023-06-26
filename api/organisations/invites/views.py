from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import GenericViewSet

from organisations.invites.exceptions import InviteExpiredError
from organisations.invites.models import Invite, InviteLink
from organisations.invites.serializers import (
    InviteLinkSerializer,
    InviteListSerializer,
)
from organisations.models import Organisation
from organisations.permissions.permissions import (
    NestedOrganisationEntityPermission,
)
from organisations.serializers import (
    InviteSerializer,
    OrganisationSerializerFull,
)
from organisations.subscriptions.exceptions import (
    SubscriptionDoesNotSupportSeatUpgrade,
)
from users.exceptions import InvalidInviteError


@api_view(["POST"])
def join_organisation_from_email(request, hash):
    invite = get_object_or_404(Invite, hash=hash)
    try:
        request.user.join_organisation_from_invite_email(invite)

    except InvalidInviteError as e:
        error_data = {"detail": str(e)}
        return Response(data=error_data, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        OrganisationSerializerFull(
            invite.organisation, context={"request": request}
        ).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def join_organisation_from_link(request, hash):
    if settings.DISABLE_INVITE_LINKS:
        raise PermissionDenied("Invite links are disabled.")

    invite = get_object_or_404(InviteLink, hash=hash)

    if (
        invite.organisation.over_plan_seats_limit(additional_seats=1)
        and not invite.organisation.is_auto_seat_upgrade_available()
    ):
        raise SubscriptionDoesNotSupportSeatUpgrade()

    if invite.is_expired:
        raise InviteExpiredError()

    request.user.join_organisation_from_invite_link(invite)

    return Response(
        OrganisationSerializerFull(
            invite.organisation, context={"request": request}
        ).data,
        status=status.HTTP_200_OK,
    )


class InviteLinkViewSet(
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticated, NestedOrganisationEntityPermission]
    serializer_class = InviteLinkSerializer
    pagination_class = None

    def get_queryset(self):
        organisation_pk = self.kwargs.get("organisation_pk")
        user = self.request.user
        organisation = Organisation.objects.get(id=organisation_pk)

        if (
            organisation.over_plan_seats_limit(additional_seats=1)
            and not organisation.is_auto_seat_upgrade_available()
        ):
            raise SubscriptionDoesNotSupportSeatUpgrade()

        return InviteLink.objects.filter(
            organisation__in=user.organisations.all()
        ).filter(organisation__pk=organisation_pk)

    def perform_create(self, serializer):
        serializer.save(organisation_id=self.kwargs.get("organisation_pk"))


class InviteViewSet(
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
    RetrieveModelMixin,
):
    permission_classes = [IsAuthenticated, NestedOrganisationEntityPermission]
    throttle_scope = "invite"

    def get_serializer_class(self):
        return {
            "list": InviteListSerializer,
            "retrieve": InviteListSerializer,
            "create": InviteSerializer,
        }.get(self.action, InviteListSerializer)

    def get_queryset(self):
        organisation_pk = self.kwargs.get("organisation_pk")
        user = self.request.user

        return Invite.objects.filter(organisation__in=user.organisations.all()).filter(
            organisation__id=organisation_pk
        )

    @action(detail=True, methods=["POST"], throttle_classes=[ScopedRateThrottle])
    def resend(self, request, organisation_pk, pk):
        invite = self.get_object()
        invite.send_invite_mail()
        return Response(status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        organisation = Organisation.objects.get(id=self.kwargs.get("organisation_pk"))
        subscription_metadata = organisation.subscription.get_subscription_metadata()

        if (
            len(settings.AUTO_SEAT_UPGRADE_PLANS) > 0
            and organisation.num_seats >= subscription_metadata.seats
            and not organisation.subscription.can_auto_upgrade_seats
        ):
            raise SubscriptionDoesNotSupportSeatUpgrade()

        serializer.save(
            organisation_id=self.kwargs.get("organisation_pk"),
            invited_by=self.request.user,
        )
