import re
import subprocess
import sys
from pathlib import Path


def main() -> None:
    baseline_path = Path("scripts/mypy_baseline.txt")
    if not baseline_path.exists():
        print("Baseline file not found. Run mypy and create mypy_baseline.txt first.")
        sys.exit(1)

    # Run mypy and capture output
    files_to_check = [f"../{filename}" for filename in sys.argv[1:]]
    command = [
        "poetry",
        "run",
        "mypy",
        "--config-file",
        "pyproject.toml",
    ] + files_to_check

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    # Mypy found no issues for the targeted file
    if result.returncode == 0:
        print(result.stdout.strip())
        sys.exit(0)

    # Mypy failed in some other way other than listing failing file lines
    if result.returncode != 1:
        print(command)
        print(
            f"Error running mypy with return code {result.returncode} and error:",
            result.stderr,
        )
        print(result.stdout.strip())
        sys.exit(1)

    current_output = result.stdout.strip().splitlines()

    with open(baseline_path, "r") as f:
        baseline = set(line.strip() for line in f if line.strip())

    # Detect new errors and remove information line filtering out third party packages
    current_errors = {line for line in current_output if "site-packages" not in line}
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
