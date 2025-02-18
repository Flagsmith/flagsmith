from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListField,
    Serializer,
)


class PaymentFailedInvoiceSerializer(Serializer):  # type: ignore[type-arg]
    dunning_status = CharField(allow_null=False)
    subscription_id = CharField(allow_null=False)

    def validate_dunning_status(self, value):  # type: ignore[no-untyped-def]
        if value != "in_progress":
            raise ValidationError("To be valid dunning must be in progress")
        return value


class ProcessSubscriptionCustomerSerializer(Serializer):  # type: ignore[type-arg]
    email = CharField(allow_null=False)


class ProcessSubscriptionAddonsSerializer(Serializer):  # type: ignore[type-arg]
    id = CharField()
    quantity = IntegerField()
    unit_price = IntegerField()
    amount = IntegerField()
    object = CharField()


class ProcessSubscriptionSubscriptionSerializer(Serializer):  # type: ignore[type-arg]
    id = CharField(allow_null=False)
    status = CharField(allow_null=False)
    plan_id = CharField(allow_null=True, required=False, default=None)
    current_term_start = IntegerField(required=False, default=None)
    current_term_end = IntegerField(required=False, default=None)
    addons = ListField(
        child=ProcessSubscriptionAddonsSerializer(), required=False, default=list
    )


class ProcessSubscriptionContentSerializer(Serializer):  # type: ignore[type-arg]
    customer = ProcessSubscriptionCustomerSerializer(required=True)
    subscription = ProcessSubscriptionSubscriptionSerializer(required=True)


class ProcessSubscriptionSerializer(Serializer):  # type: ignore[type-arg]
    content = ProcessSubscriptionContentSerializer(required=True)


class PaymentSucceededInvoiceSerializer(Serializer):  # type: ignore[type-arg]
    subscription_id = CharField(allow_null=False)


class PaymentFailedContentSerializer(Serializer):  # type: ignore[type-arg]
    invoice = PaymentFailedInvoiceSerializer(required=True)


class PaymentSucceededContentSerializer(Serializer):  # type: ignore[type-arg]
    invoice = PaymentSucceededInvoiceSerializer(required=True)


class PaymentFailedSerializer(Serializer):  # type: ignore[type-arg]
    content = PaymentFailedContentSerializer(required=True)


class PaymentSucceededSerializer(Serializer):  # type: ignore[type-arg]
    content = PaymentSucceededContentSerializer(required=True)
