import os

import shortuuid


def create_hash() -> str:
    """Helper function to create a short hash"""
    return shortuuid.uuid()


def get_numbered_env_vars_with_prefix(prefix: str) -> list[str]:
    """
    Returns a list containing the values of all environment variables whose names have a given prefix followed by an
    integer, starting from 0, until no more variables with that prefix are found.
    """
    db_urls = []
    i = 0
    while True:
        db_url = os.getenv(f"{prefix}{i}")
        if not db_url:
            break
        db_urls.append(db_url)
        i += 1
    return db_urls
