import os

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole, Subscription
from projects.models import Project
from users.models import FFAdminUser

from .permissions import E2ETestPermission


class Teardown(APIView):
    schema = None
    permission_classes = (E2ETestPermission,)
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        # delete users created for e2e test by front end
        fe_e2e_test_user_email = os.environ["FE_E2E_TEST_USER_EMAIL"]
        password = "pbkdf2_sha256$260000$RuWdd52KA8sgO7taxBtRH1$N81RojtN9tVUp9vd8nyBthp7EJZ+NYFrjn2QCm76QME="
        if fe_e2e_test_user_email:
            FFAdminUser.objects.filter(email=fe_e2e_test_user_email).delete()
            FFAdminUser.objects.filter(email=fe_e2e_test_user_email + ".io").delete()
            FFAdminUser.objects.filter(email="changeMail@test.com").delete()

        # create user and organisation for e2e test by front end
        organisation = Organisation.objects.create(name="Bullet Train Ltd")
        org_admin = FFAdminUser.objects.create(
            email=fe_e2e_test_user_email,
            password=password,
            username=fe_e2e_test_user_email,
        )
        org_admin.add_organisation(organisation, OrganisationRole.ADMIN)

        project = Project.objects.create(
            name="My Test Project", organisation=organisation
        )

        Environment.objects.create(name="Development", project=project)

        Environment.objects.create(name="Production", project=project)

        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateSeats(APIView):
    permission_classes = (E2ETestPermission,)
    authentication_classes = (TokenAuthentication,)

    def put(self, request):
        user = FFAdminUser.objects.get(email=os.environ["FE_E2E_TEST_USER_EMAIL"])
        Subscription.objects.filter(organisation__in=user.organisations.all()).update(
            max_seats=request.data.get("seats", 3)
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
