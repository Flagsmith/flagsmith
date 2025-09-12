from django.urls import path

__all__ = [
    "urlpatterns",
]

from custom_auth.mfa.trench.views import (
    ListUserActiveMFAMethods,
    MFAMethodActivationView,
    MFAMethodConfirmActivationView,
    MFAMethodDeactivationView,
)

urlpatterns = (
    path(
        "<str:method>/activate/",
        MFAMethodActivationView.as_view(),
        name="mfa-activate",
    ),
    path(
        "<str:method>/activate/confirm/",
        MFAMethodConfirmActivationView.as_view(),
        name="mfa-activate-confirm",
    ),
    path(
        "<str:method>/deactivate/",
        MFAMethodDeactivationView.as_view(),
        name="mfa-deactivate",
    ),
    path(
        "mfa/user-active-methods/",
        ListUserActiveMFAMethods.as_view(),
        name="mfa-list-user-active-methods",
    ),
)
