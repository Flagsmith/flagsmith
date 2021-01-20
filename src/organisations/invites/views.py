from threading import Thread

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from organisations.invites.serializers import InviteLinkSerializer
from organisations.models import OrganisationRole
from organisations.permissions import NestedOrganisationEntityPermission
from organisations.serializers import OrganisationSerializerFull
from users.exceptions import InvalidInviteError
from organisations.invites.models import Invite, InviteLink
from users.models import FFAdminUser
from users.serializers import InviteListSerializer


@api_view(["POST"])
def join_organisation_from_email(request, hash):
    invite = get_object_or_404(Invite, hash=hash)

    try:
        request.user.join_organisation(invite)
    except InvalidInviteError as e:
        error_data = {"detail": str(e)}
        return Response(data=error_data, status=status.HTTP_400_BAD_REQUEST)

    if invite.organisation.over_plan_seats_limit():
        Thread(
            target=FFAdminUser.send_organisation_over_limit_alert,
            args=[invite.organisation],
        ).start()

    return Response(
        OrganisationSerializerFull(
            invite.organisation, context={"request": request}
        ).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def join_organisation_from_link(request, hash):
    invite = get_object_or_404(InviteLink, hash=hash)

    if invite.is_expired:
        return Response(data={"detail": "Invite has expired."})

    request.user.add_organisation(
        invite.organisation, role=OrganisationRole(invite.role)
    )

    if invite.organisation.over_plan_seats_limit():
        Thread(
            target=FFAdminUser.send_organisation_over_limit_alert,
            args=[invite.organisation],
        ).start()

    return Response(
        OrganisationSerializerFull(
            invite.organisation, context={"request": request}
        ).data,
        status=status.HTTP_200_OK,
    )


class InviteLinkViewSet(
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = InviteLinkSerializer
    permission_classes = (IsAuthenticated, NestedOrganisationEntityPermission)
    pagination_class = None

    def get_queryset(self):
        organisation_pk = self.kwargs.get("organisation_pk")
        user = self.request.user
        return InviteLink.objects.filter(
            organisation__in=user.organisations.all()
        ).filter(organisation__pk=organisation_pk)

    def perform_create(self, serializer):
        serializer.save(organisation_id=self.kwargs.get("organisation_pk"))

    def perform_update(self, serializer):
        serializer.save(organisation_id=self.kwargs.get("organisation_pk"))


class InviteViewSet(viewsets.ModelViewSet):
    serializer_class = InviteListSerializer
    permission_classes = (IsAuthenticated, NestedOrganisationEntityPermission)

    def get_queryset(self):
        organisation_pk = self.kwargs.get("organisation_pk")
        user = self.request.user

        return Invite.objects.filter(organisation__in=user.organisations.all()).filter(
            organisation__id=organisation_pk
        )

    @action(detail=True, methods=["POST"])
    def resend(self, request, organisation_pk, pk):
        invite = self.get_object()
        invite.send_invite_mail()
        return Response(status=status.HTTP_200_OK)
