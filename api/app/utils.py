import pathlib

import shortuuid


def create_hash():
    """Helper function to create a short hash"""
    return shortuuid.uuid()


def get_version_info() -> dict:
    """Reads the version info baked into src folder of the docker container"""
    version_json = {
        "ci_commit_sha": _get_file_contents("./CI_COMMIT_SHA"),
        "image_tag": _get_file_contents("./IMAGE_TAG"),
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
