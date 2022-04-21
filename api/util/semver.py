def is_semver(value: str) -> bool:
    """
    Checks if the given string have `:semver` suffix or not
    >>> is_semver("2.1.41-beta:semver")
    True
    >>> is_semver("2.1.41-beta")
    False
    """
    return value[-7:] == ":semver"


def remove_semver_suffix(value: str) -> str:
    return value[:-7]
