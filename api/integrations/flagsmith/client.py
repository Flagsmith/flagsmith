import json
import os
import typing

from django.conf import settings
from flagsmith import Flagsmith
from flagsmith.models import DefaultFlag

_flagsmith_wrapper = None


class FlagsmithWrapper:
    def __init__(
        self,
        environment_key: str,
        api_url: str,
    ):
        self._defaults = self._build_defaults()
        self._client = Flagsmith(
            environment_key=environment_key,
            api_url=api_url,
            default_flag_handler=self._default_handler,
        )

    def get_client(self) -> Flagsmith:
        return self._client

    @classmethod
    def get_instance(cls) -> "FlagsmithWrapper":
        global _flagsmith_wrapper

        if not _flagsmith_wrapper:
            _flagsmith_wrapper = cls(
                environment_key=settings.FLAGSMITH_SERVER_KEY,
                api_url=settings.FLAGSMITH_API_URL,
            )

        return _flagsmith_wrapper

    def _default_handler(self, feature_name: str) -> DefaultFlag:
        return self._defaults.get(feature_name, DefaultFlag(enabled=False, value=None))

    @staticmethod
    def _build_defaults() -> typing.Dict[str, DefaultFlag]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, "defaults.json")) as defaults:
            return {
                flag["feature"]["name"]: DefaultFlag(
                    enabled=flag["enabled"], value=flag["feature_state_value"]
                )
                for flag in json.loads(defaults.read())
            }
