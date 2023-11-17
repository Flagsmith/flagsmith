from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, Serializer


class PaymentFailedInvoiceSerializer(Serializer):
    dunning_status = CharField(allow_null=False)
    subscription_id = CharField(allow_null=False)

    def validate_dunning_status(self, value):
        if value != "in_progress":
            raise ValidationError("To be valid dunning must be in progress")
        return value


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
