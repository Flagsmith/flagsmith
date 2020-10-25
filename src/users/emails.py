from djoser import email


class ActivationEmail(email.ActivationEmail):
    """
    Overrides djoser Activation email with our own
    """
    template_name = 'users/activation.html'


class ConfirmationEmail(email.ConfirmationEmail):
    """
    Overrides djoser Confirmation email with our own
    """
    template_name = "users/confirmation.html"
