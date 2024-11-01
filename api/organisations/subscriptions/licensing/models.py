from django.db import models

from organisations.subscriptions.licensing.licensing import LicenceInformation


class OrganisationLicence(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    organisation = models.OneToOneField(
        "organisations.Organisation", related_name="licence", on_delete=models.CASCADE
    )

    content = models.TextField(blank=True)

    def get_licence_information(self) -> LicenceInformation:
        return LicenceInformation.parse_raw(self.content)
