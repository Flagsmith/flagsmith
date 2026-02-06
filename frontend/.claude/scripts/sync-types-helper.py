#!/usr/bin/env python3
"""
Helper script for API type syncing operations.
Minimizes token usage by batching cache operations.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

CACHE_FILE = Path(__file__).parent.parent / "api-type-map.json"


def load_cache() -> Dict:
    """Load the type cache from JSON file."""
    if not CACHE_FILE.exists():
        return {"_metadata": {}, "response_types": {}, "request_types": {}}
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
        # Migrate old format to new format if needed
        if "types" in cache and "response_types" not in cache:
            cache["response_types"] = cache.pop("types")
            cache["request_types"] = {}
        return cache


def save_cache(cache: Dict) -> None:
    """Save the type cache to JSON file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
        f.write("\n")


def get_changed_serializers(
    old_commit: str, new_commit: str, api_path: str
) -> List[str]:
    """Get list of serializer files changed between commits."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", f"{old_commit}..{new_commit}", "--name-only"],
        cwd=api_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return []

    files = result.stdout.strip().split("\n")
    return [f for f in files if "serializers.py" in f]


def find_types_using_serializer(
    cache: Dict, serializer_path: str, serializer_name: str
) -> List[str]:
    """Find all type keys that use a specific serializer."""
    search_string = f"{serializer_path}:{serializer_name}"
    types = []

    for key, value in cache.items():
        if key == "_metadata":
            continue
        if value.get("serializer", "").startswith(search_string.split(":")[0]):
            if serializer_name in value.get("serializer", ""):
                types.append(key)

    return types


def update_metadata(stats: Dict) -> None:
    """Update cache metadata with sync statistics."""
    cache = load_cache()

    if "_metadata" not in cache:
        cache["_metadata"] = {}

    cache["_metadata"].update(stats)
    save_cache(cache)


def get_types_needing_sync(
    serializer_files: List[str], api_path: str, type_category: str = "response"
) -> List[Dict]:
    """
    Get list of types that need syncing based on changed serializer files.

    Args:
        serializer_files: List of changed serializer file paths
        api_path: Path to backend API repository
        type_category: Either "response" or "request"

    Returns:
        List of dicts with type info: {key, serializer_file, serializer_class, type_name}
    """
    cache = load_cache()
    types_to_check = []

    # Select the appropriate cache section
    cache_key = f"{type_category}_types"
    type_cache = cache.get(cache_key, {})

    for file_path in serializer_files:
        # Extract serializer classes from the file path in cache
        for type_key, type_data in type_cache.items():
            if type_key == "_metadata":
                continue

            serializer = type_data.get("serializer", "")
            if file_path in serializer and ":" in serializer:
                serializer_class = serializer.split(":")[-1].strip()
                types_to_check.append(
                    {
                        "key": type_key,
                        "serializer_file": file_path,
                        "serializer_class": serializer_class,
                        "type_name": type_data.get("type", ""),
                    }
                )

    return types_to_check


def filter_syncable_types(cache: Dict, type_category: str = "response") -> List[Dict]:
    """
    Filter cache to only include types with Django serializers (exclude custom/ChargeBee/empty).

    Args:
        cache: Full cache dict
        type_category: Either "response" or "request"

    Returns:
        List of type info dicts
    """
    syncable = []
    cache_key = f"{type_category}_types"
    type_cache = cache.get(cache_key, {})

    for type_key, type_data in type_cache.items():
        if type_key == "_metadata":
            continue

        serializer = type_data.get("serializer", "")
        note = type_data.get("note", "")

        # Skip custom responses, ChargeBee, NOT_IMPLEMENTED, and view methods
        if any(x in note.lower() for x in ["custom", "chargebee", "empty"]):
            continue
        if "NOT_IMPLEMENTED" in serializer:
            continue
        if "views.py:" in serializer and "(" in serializer:
            continue

        # Only include Django serializers
        if "serializers.py:" in serializer and ":" in serializer:
            parts = serializer.split(":")
            if len(parts) == 2:
                syncable.append(
                    {
                        "key": type_key,
                        "serializer_file": parts[0],
                        "serializer_class": parts[1].strip(),
                        "type_name": type_data.get("type", ""),
                    }
                )

    return syncable


def get_last_commit() -> str:
    """Get the last backend commit hash from cache metadata."""
    cache = load_cache()
    return cache.get("_metadata", {}).get("lastBackendCommit", "")


if __name__ == "__main__":
    # Command-line interface
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command == "changed-serializers":
        # Usage: python sync-types-helper.py changed-serializers OLD_COMMIT NEW_COMMIT API_PATH
        old_commit = sys.argv[2]
        new_commit = sys.argv[3]
        api_path = sys.argv[4]
        changed = get_changed_serializers(old_commit, new_commit, api_path)
        print("\n".join(changed))

    elif command == "types-to-sync":
        # Usage: python sync-types-helper.py types-to-sync [response|request] FILE1 FILE2 ... API_PATH
        type_category = sys.argv[2] if len(sys.argv) > 2 else "response"
        files = sys.argv[3:]
        api_path = sys.argv[-1] if files else ""
        types = get_types_needing_sync(files[:-1], api_path, type_category)
        print(json.dumps(types, indent=2))

    elif command == "update-metadata":
        # Usage: echo '{"lastSync": "..."}' | python sync-types-helper.py update-metadata
        stats = json.load(sys.stdin)
        update_metadata(stats)
        print("Metadata updated")

    elif command == "syncable-types":
        # Usage: python sync-types-helper.py syncable-types [response|request]
        type_category = sys.argv[2] if len(sys.argv) > 2 else "response"
        cache = load_cache()
        types = filter_syncable_types(cache, type_category)
        print(json.dumps(types, indent=2))

    elif command == "get-last-commit":
        # Usage: python sync-types-helper.py get-last-commit
        commit = get_last_commit()
        print(commit)

    else:
        print("Usage:")
        print(
            "  changed-serializers OLD NEW PATH           - Get changed serializer files"
        )
        print(
            "  types-to-sync [response|request] FILE... PATH - Get types needing sync"
        )
        print(
            "  update-metadata                            - Update metadata (JSON via stdin)"
        )
        print(
            "  syncable-types [response|request]          - Get all syncable type info"
        )
        print(
            "  get-last-commit                            - Get last backend commit from cache"
        )
