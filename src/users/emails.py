from django.contrib.auth.tokens import default_token_generator
from djoser import email, utils
from djoser.conf import settings


class ActivationEmail(email.ActivationEmail):
    """
    Overrides djoser Activation email with our own
    """
    template_name = 'users/activation.html'

    def get_context_data(self):
        # ActivationEmail can be deleted
        context = super().get_context_data()

        user = context.get("user")
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = settings.ACTIVATION_URL.format(**context)

        return context


class ConfirmationEmail(email.ConfirmationEmail):
    """
    Overrides djoser Confirmation email with our own
    """
    template_name = "users/confirmation.html"
