from typing import Any

from djoser import email  # type: ignore[import-untyped]

from e2etests.helpers import is_e2e_request


class ActivationEmail(email.ActivationEmail):  # type: ignore[misc]
    """
    Overrides djoser Activation email with our own
    """

    template_name = "users/activation.html"

    def send(self, to: list[str], *args: Any, **kwargs: Any) -> None:
        if is_e2e_request(self.request):
            return
        super().send(to, *args, **kwargs)


class ConfirmationEmail(email.ConfirmationEmail):  # type: ignore[misc]
    """
    Overrides djoser Confirmation email with our own
    """

    template_name = "users/confirmation.html"
