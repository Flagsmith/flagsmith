import json
import os
import pathlib

import shortuuid


def create_hash():
    """Helper function to create a short hash"""
    return shortuuid.uuid()


def get_version_info() -> dict:
    """Reads the version info baked into src folder of the docker container"""
    release_please_manifest_location = "./.release-please-manifest.json"
    manifest_versions = None

    if os.path.isfile(release_please_manifest_location):
        manifest_versions = json.loads(
            _get_file_contents(release_please_manifest_location)
        )
        image_tag = manifest_versions["."]
    else:
        image_tag = "unknown"

    version_json = {
        "ci_commit_sha": _get_file_contents("./CI_COMMIT_SHA"),
        "image_tag": image_tag,
        "is_enterprise": pathlib.Path("./ENTERPRISE_VERSION").exists(),
    }

    if manifest_versions:
        version_json["package_versions"] = manifest_versions

    return version_json


def _get_file_contents(file_path: str) -> str:
    """Attempts to read a file from the filesystem and return the contents"""
    try:
        with open(file_path) as f:
            return f.read().replace("\n", "")
    except FileNotFoundError:
        return "unknown"
