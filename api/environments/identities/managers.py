from django.db.models import Manager


class IdentityManager(Manager):
    def get_by_natural_key(self, identifier, environment_api_key):
        return self.get(identifier=identifier, environment__api_key=environment_api_key)
