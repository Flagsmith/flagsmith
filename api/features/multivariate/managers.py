from django.db.models import Manager


class MultivariateFeatureOptionManager(Manager):
    def get_by_natural_key(
        self, feature_id, type, string_value, integer_value, boolean_value
    ):
        return self.get(
            feature=feature_id,
            type=type,
            string_value=string_value,
            integer_value=integer_value,
            boolean_value=boolean_value,
        )


class MultivariateFeatureStateValueManager(Manager):
    def get_by_natural_key(self, feature_state_id, multivariate_feature_option_id):
        return self.get(
            feature_state=feature_state_id,
            multivariate_feature_option=multivariate_feature_option_id,
        )
