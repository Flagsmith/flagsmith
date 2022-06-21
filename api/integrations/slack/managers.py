from django.db.models import Manager


class SlackConfigurationManager(Manager):
    def get_by_natural_key(self, project_id, created_data, api_token):
        return self.get(
            project=project_id, created_data=created_data, api_token=api_token
        )
