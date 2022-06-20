from django.db.models import Manager


class ChangeRequestManager(Manager):
    def get_by_natural_key(self, environment_id, created_at, title, user_id):
        return self.get(
            environment=environment_id, created_at=created_at, title=title, user=user_id
        )
