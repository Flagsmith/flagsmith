from typing import Callable, Set

from django.conf import settings
from django.utils.crypto import get_random_string


class GenerateBackupCodesCommand:
    def __init__(self, random_string_generator: Callable) -> None:  # type: ignore[type-arg]
        self._random_string_generator = random_string_generator

    def execute(
        self,
        quantity: int = settings.TRENCH_AUTH["BACKUP_CODES_QUANTITY"],  # type: ignore[assignment]
        length: int = settings.TRENCH_AUTH["BACKUP_CODES_LENGTH"],  # type: ignore[assignment]
        allowed_chars: str = settings.TRENCH_AUTH["BACKUP_CODES_CHARACTERS"],  # type: ignore[assignment]
    ) -> Set[str]:
        """
        Generates random encrypted backup codes.

        :param quantity: How many codes should be generated
        :type quantity: int
        :param length: How long codes should be
        :type length: int
        :param allowed_chars: Characters to create backup codes from
        :type allowed_chars: str

        :returns: Encrypted backup codes
        :rtype: set[str]
        """
        return {
            self._random_string_generator(length, allowed_chars)
            for _ in range(quantity)
        }


generate_backup_codes_command = GenerateBackupCodesCommand(
    random_string_generator=get_random_string,
).execute
