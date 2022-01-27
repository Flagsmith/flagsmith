import pathlib

import shortuuid


def create_hash():
    """Helper function to create a short hash"""
    return shortuuid.uuid()


def get_version_info():
    """Reads the version info baked into src folder of the docker container"""
    version_json = {
        "CI_COMMIT_REF_NAME": get_file("./src/CI_COMMIT_REF_NAME"),
        "CI_COMMIT_SHA": get_file("./src/CI_COMMIT_SHA"),
        "IMAGE_TAG": get_file("./src/IMAGE_TAG"),
    }

    return version_json


def get_file(file_path):
    """Attempts to read a file from the filesystem and return the contents"""
    if pathlib.Path(file_path).is_file():
        return open(file_path).read().replace("\n", "")

    return "unknown"
