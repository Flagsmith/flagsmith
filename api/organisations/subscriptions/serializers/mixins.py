import typing

from organisations.models import Subscription


class ReadOnlyIfNotValidPlanMixin:
    """
    Mixin to add read only status to fields in a given serializer based on the existence
    of a subscription and a black list of plan ids

    Example usage:

        class MySerializer(ReadOnlyIfNotValidPlanMixin, ModelSerializer):
            class Meta:
                model = MyModel
                fields = ("my_field",)

            invalid_plans = ("free",)
            field_names = ("my_field",)

            def get_subscription(self):
                return subscription
    """

    invalid_plans: typing.Iterable[str] = None
    field_names: typing.Iterable[str] = None

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)

        if not self.get_subscription:
            raise AttributeError("get_subscription must be set.")  # custom exception?
        if not (self.context and "view" in self.context):
            raise RuntimeError("view must be in the context.")

        subscription = self.get_subscription()
        field_names = self.field_names or []
        invalid_plans = self.invalid_plans or []

        for field_name in field_names:
            if (
                field_name in fields
                and not (subscription and subscription.plan)
                or subscription.plan in invalid_plans
            ):
                fields[field_name].read_only = True

        return fields

    def get_subscription(self) -> typing.Optional[Subscription]:
        raise NotImplementedError()
