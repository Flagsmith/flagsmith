from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from organisations.serializers import OrganisationSerializer
from users import serializers
from users.models import FFAdminUser, Invite


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


class FFAdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.UserFullSerializer

    def get_queryset(self):
        return FFAdminUser.objects.filter(pk=self.request.user.id).prefetch_related('organisations',
                                                                                    'organisations__users')

    @action(detail=False, methods=["POST"], url_path="join/(?P<invite_hash>\w+)")
    def join_organisation(self, request, invite_hash):
        invite = get_object_or_404(Invite, hash=invite_hash)
        organisation = invite.organisation
        user = request.user

        user.organisations.add(organisation)
        invite.delete()

        self.alert_if_num_seats_above_limit(organisation)

        return Response(OrganisationSerializer(organisation).data, status=status.HTTP_200_OK)

    def alert_if_num_seats_above_limit(self, organisation):
        if settings.HOSTED_SEATS_LIMIT and organisation.users.count() > settings.HOSTED_SEATS_LIMIT:
            send_mail(
                subject='Organisation over number of seats',
                message='Organisation %s has gone over the limit on number of seats' % str(organisation.name),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=FFAdminUser.get_admin_user_emails(),
                fail_silently=True
            )


def password_reset_redirect(request, uidb64, token):
    protocol = "https" if request.is_secure() else "https"
    current_site = get_current_site(request)
    domain = current_site.domain
    return redirect(protocol + "://" + domain + "/password-reset/" + uidb64 + "/" + token)
