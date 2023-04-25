class HideSensitiveFieldsSerializerMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        environment = self.context["request"].environment
        if environment.hide_sensitive_data:
            for field in self.sensitive_fields:
                data.pop(field)
        return data
