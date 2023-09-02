import os

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from users.models import FFAdminUser


class E2ESeedData:
    fe_e2e_test_user_email = (
        os.environ["FE_E2E_TEST_USER_EMAIL"]
        if "FE_E2E_TEST_USER_EMAIL" in os.environ
        else None
    )
    password = "str0ngp4ssw0rd!"

    def teardown(self):
        # delete users created for e2e test by front end
        if self.fe_e2e_test_user_email:
            FFAdminUser.objects.filter(email=self.fe_e2e_test_user_email).delete()
            FFAdminUser.objects.filter(
                email=self.fe_e2e_test_user_email + ".io"
            ).delete()
            FFAdminUser.objects.filter(email="changeMail@test.com").delete()

    def seed_data(self):
        # create user and organisation for e2e test by front end
        if self.fe_e2e_test_user_email:
            organisation = Organisation.objects.create(name="Bullet Train Ltd")
            org_admin = FFAdminUser.objects.create_user(
                email=self.fe_e2e_test_user_email,
                password=self.password,
                username=self.fe_e2e_test_user_email,
            )
            org_admin.add_organisation(organisation, OrganisationRole.ADMIN)

            project = Project.objects.create(
                name="My Test Project", organisation=organisation
            )

            Environment.objects.create(name="Development", project=project)

            Environment.objects.create(name="Production", project=project)
