import json
import pathlib
from functools import lru_cache
from typing import TypedDict

import shortuuid
from django.conf import settings

UNKNOWN = "unknown"
VERSIONS_INFO_FILE_LOCATION = ".versions.json"


class SelfHostedData(TypedDict):
    has_users: bool
    has_logins: bool
    is_bootstrapped: bool


class VersionInfo(TypedDict):
    ci_commit_sha: str
    image_tag: str
    is_enterprise: bool
    is_saas: bool
    self_hosted_data: SelfHostedData | None


def create_hash() -> str:
    """Helper function to create a short hash"""
    return shortuuid.uuid()


def is_enterprise() -> bool:
    return pathlib.Path("./ENTERPRISE_VERSION").exists()


def is_saas() -> bool:
    return pathlib.Path("./SAAS_DEPLOYMENT").exists()


@lru_cache
def get_version_info() -> VersionInfo:
    """Reads the version info baked into src folder of the docker container"""
    version_json = {}
    image_tag = UNKNOWN

    _is_saas = is_saas()

    manifest_versions_content: str = _get_file_contents(VERSIONS_INFO_FILE_LOCATION)

    if manifest_versions_content != UNKNOWN:
        manifest_versions = json.loads(manifest_versions_content)
        version_json["package_versions"] = manifest_versions
        image_tag = manifest_versions["."]

    version_json = version_json | {
        "ci_commit_sha": _get_file_contents("./CI_COMMIT_SHA"),
        "image_tag": image_tag,
        "is_enterprise": is_enterprise(),
        "is_saas": _is_saas,
        "self_hosted_data": None,
    }

    if not _is_saas:
        from users.models import FFAdminUser

        version_json["self_hosted_data"] = {
            "has_users": FFAdminUser.objects.count() > 0,
            "has_logins": FFAdminUser.objects.filter(last_login__isnull=False).exists(),
            "is_bootstrapped": (
                settings.ALLOW_ADMIN_INITIATION_VIA_CLI is True
                and FFAdminUser.objects.filter(email=settings.ADMIN_EMAIL).exists()
            ),
        }

    return version_json


def _get_file_contents(file_path: str) -> str:
    """Attempts to read a file from the filesystem and return the contents"""
    try:
        with open(file_path) as f:
            return f.read().replace("\n", "")
    except FileNotFoundError:
        return UNKNOWN
