from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListField,
    Serializer,
)


class PaymentFailedInvoiceSerializer(Serializer):
    dunning_status = CharField(allow_null=False)
    subscription_id = CharField(allow_null=False)

    def validate_dunning_status(self, value):
        if value != "in_progress":
            raise ValidationError("To be valid dunning must be in progress")
        return value


class ProcessSubscriptionCustomerSerializer(Serializer):
    email = CharField(allow_null=False)


class ProcessSubscriptionAddonsSerializer(Serializer):
    id = CharField()
    quantity = IntegerField()
    unit_price = IntegerField()
    amount = IntegerField()
    object = CharField()


class ProcessSubscriptionSubscriptionSerializer(Serializer):
    id = CharField(allow_null=False)
    status = CharField(allow_null=False)
    plan_id = CharField(allow_null=True, required=False, default=None)
    current_term_start = IntegerField(required=False, default=None)
    current_term_end = IntegerField(required=False, default=None)
    addons = ListField(
        child=ProcessSubscriptionAddonsSerializer(), required=False, default=list
    )


class ProcessSubscriptionContentSerializer(Serializer):
    customer = ProcessSubscriptionCustomerSerializer(required=True)
    subscription = ProcessSubscriptionSubscriptionSerializer(required=True)


class ProcessSubscriptionSerializer(Serializer):
    content = ProcessSubscriptionContentSerializer(required=True)


class PaymentSucceededInvoiceSerializer(Serializer):
    subscription_id = CharField(allow_null=False)


class PaymentFailedContentSerializer(Serializer):
    invoice = PaymentFailedInvoiceSerializer(required=True)


class PaymentSucceededContentSerializer(Serializer):
    invoice = PaymentSucceededInvoiceSerializer(required=True)


class PaymentFailedSerializer(Serializer):
    content = PaymentFailedContentSerializer(required=True)


class PaymentSucceededSerializer(Serializer):
    content = PaymentSucceededContentSerializer(required=True)
