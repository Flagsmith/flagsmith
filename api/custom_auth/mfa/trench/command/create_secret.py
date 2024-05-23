from django.conf import settings
from pyotp import random_base32


def create_secret_command() -> str:
    generator = random_base32
    return generator(length=settings.TRENCH_AUTH["SECRET_KEY_LENGTH"])
