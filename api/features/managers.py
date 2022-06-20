from django.db.models import Manager
from ordered_model.models import OrderedModelManager


class FeatureManager(Manager):
    def get_by_natural_key(self, name, project_id):
        return self.get(name=name, project=project_id)


class FeatureSegmentManager(OrderedModelManager):
    def get_by_natural_key(self, feature_id, segment_id, environment_id):
        return self.get(
            feature=feature_id, segment=segment_id, environment=environment_id
        )


class FeatureStateManager(Manager):
    def get_by_natural_key(
        self,
        feature_id,
        environment_id,
        feature_segment_id,
        identity_id,
        version,
        change_request_id,
    ):
        return self.get(
            feature=feature_id,
            environment_id=environment_id,
            feature_segment=feature_segment_id,
            identity=identity_id,
            version=version,
            change_request=change_request_id,
        )
