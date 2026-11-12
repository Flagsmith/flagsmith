import argparse
import re
from pathlib import Path

MODULE_PATH = "app_analytics/constants.py"
VERSIONS_CONSTANT_NAME = "SDK_USER_AGENT_KNOWN_VERSIONS"


def add_version(sdk_name: str, new_version: str) -> None:
    """Add a new version to known versions constants"""
    contents = Path(MODULE_PATH).read_text()

    # Add SDK version
    contents = re.sub(
        pattern=rf"""
            ^  # Expect to have definition at module-level
            (?P<constant_def>{VERSIONS_CONSTANT_NAME}[^=]*=\s*\{{)
            (?P<prior_sdks>[^\}}]+)
            (?P<sdk_def>"{sdk_name}"\s*:\s*\[)
            (?P<sdk_versions>[^\]]*)
            (?P<latest_version>"(?:unknown|\d[^"]+)"),?
        """,
        repl=(
            r"\g<constant_def>\g<prior_sdks>\g<sdk_def>\g<sdk_versions>\g<latest_version>"
            f',\n        "{new_version}",\n    '
        ),
        string=contents,
        count=1,
        flags=re.MULTILINE | re.VERBOSE,
    )

    Path(MODULE_PATH).write_text(contents)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a known SDK version to an existing constants entry."
    )
    parser.add_argument(
        "--sdk",
        type=str,
        required=True,
        help="The SDK name, e.g. flagsmith-js-sdk",
    )
    parser.add_argument(
        "--version",
        type=str,
        required=True,
        help="The SDK version, e.g. 9.4.0",
    )
    args = parser.parse_args()
    add_version(args.sdk, args.version)


if __name__ == "__main__":
    main()
