class HideSensitiveFieldsSerializerMixin:
    def to_representation(self, instance):  # type: ignore[no-untyped-def]
        data = super().to_representation(instance)  # type: ignore[misc]
        environment = self.context["request"].environment  # type: ignore[attr-defined]
        if environment.hide_sensitive_data:
            for field in self.sensitive_fields:  # type: ignore[attr-defined]
                data[field] = [] if isinstance(data[field], list) else None
        return data
