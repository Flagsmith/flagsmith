import json
import pathlib

import shortuuid


def create_hash():
    """Helper function to create a short hash"""
    return shortuuid.uuid()


def get_version_info() -> dict:
    """Reads the version info baked into src folder of the docker container"""
    release_please_manifest_location = "./.versions.json"
    manifest_versions = None
    version_json = {}
    image_tag = "unknown"

    manifest_versions = json.loads(_get_file_contents(release_please_manifest_location))

    if manifest_versions:
        version_json["package_versions"] = manifest_versions
        image_tag = manifest_versions["."]

    version_json = version_json | {
        "ci_commit_sha": _get_file_contents("./CI_COMMIT_SHA"),
        "image_tag": image_tag,
        "is_enterprise": pathlib.Path("./ENTERPRISE_VERSION").exists(),
    }

    return version_json


def _get_file_contents(file_path: str) -> str:
    """Attempts to read a file from the filesystem and return the contents"""
    try:
        with open(file_path) as f:
            return f.read().replace("\n", "")
    except FileNotFoundError:
        return "unknown"
