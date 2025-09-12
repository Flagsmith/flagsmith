from djoser import email  # type: ignore[import-untyped]


class ActivationEmail(email.ActivationEmail):  # type: ignore[misc]
    """
    Overrides djoser Activation email with our own
    """

    template_name = "users/activation.html"


class ConfirmationEmail(email.ConfirmationEmail):  # type: ignore[misc]
    """
    Overrides djoser Confirmation email with our own
    """

    template_name = "users/confirmation.html"
