from django.db.models import Manager


class IdentityManager(Manager):
    def get_by_natural_key(self, identifier, environment_id):
        return self.get(identifier=identifier, environment=environment_id)
