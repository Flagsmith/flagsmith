import re
import subprocess
import sys
from pathlib import Path


def main():
    baseline_path = Path("scripts/mypy_baseline.txt")
    if not baseline_path.exists():
        print("Baseline file not found. Run mypy and create mypy_baseline.txt first.")
        sys.exit(1)

    # Run mypy and capture output
    result = subprocess.run(
        ["poetry", "run", "mypy", "--config-file", "pyproject.toml", "."],
        capture_output=True,
        text=True,
    )
    current_output = result.stdout.strip().splitlines()
    if result.returncode != 1:
        print("Error running mypy:", result.stderr)
        sys.exit(1)

    with open(baseline_path, "r") as f:
        baseline = set(line.strip() for line in f if line.strip())

    # Detect new errors and remove information line
    current_errors = set(current_output)
    new_errors = current_errors - baseline
    pattern = r"Found (\d+) errors in (\d+) files \(checked (\d+) source files\)"
    removal = None

    for error in new_errors:
        has_match = re.match(pattern, error)
        if has_match:
            removal = error
            break

    if removal:
        new_errors.remove(removal)

    if new_errors:
        print("New mypy errors detected:")
        print("\n".join(new_errors))
        sys.exit(1)

    print("No new mypy errors detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
