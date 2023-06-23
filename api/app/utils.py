import pathlib

import shortuuid


def create_hash():
    """Helper function to create a short hash"""
    return shortuuid.uuid()


def get_version_info():
    """Reads the version info baked into src folder of the docker container"""
    version_json = {
        "ci_commit_sha": get_ci_commit_sha(),
        "image_tag": get_image_tag(),
    }

    return version_json


def get_image_tag():
    return get_file("./IMAGE_TAG")


def get_ci_commit_sha():
    return get_file("./CI_COMMIT_SHA")


def get_file(file_path):
    """Attempts to read a file from the filesystem and return the contents"""
    if pathlib.Path(file_path).is_file():
        return open(file_path).read().replace("\n", "")

    return "unknown"
