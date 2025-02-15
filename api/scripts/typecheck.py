"""
Feeds filepaths provided as command line arguments to mypy
and compares the output with a baseline file.
Exits 1 in case issues that are not present in the baseline were found.

Usage:
    python scripts/typecheck.py [filenames]

Options:
    --baseline  Check all files (`mypy .`) and update the baseline file
"""

import json
import os
import sys
from dataclasses import dataclass, field

from mypy.api import run as run_mypy


@dataclass
class Config:
    pre_commit_mode: bool = bool(os.environ.get("PRE_COMMIT"))
    baseline_mode: bool = False
    baseline_path: str = "scripts/mypy-baseline.jsonl"
    filenames: list[str] = field(default_factory=lambda: ["."])


@dataclass(frozen=True, eq=False)
class MypyIssue:
    file: str
    line: int
    column: int
    code: int
    severity: str
    original_line: str

    # We need the following two methods
    # because apparently "message" and "hint" can differ between runs

    def __hash__(self) -> int:
        return hash((self.file, self.line, self.column, self.code, self.severity))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MypyIssue) and (
            self.file == other.file
            and self.line == other.line
            and self.column == other.column
            and self.code == other.code
            and self.severity == other.severity
        )


def _get_config() -> Config:
    config = Config()
    if arguments := sys.argv[1:]:
        if "--baseline" in arguments:
            config.baseline_mode = True
            arguments.remove("--baseline")
        elif config.pre_commit_mode:
            # pre-commit collects files from the root of the repository
            # so we need to correctly prepend the current working directory
            # to the filenames
            config.filenames = [
                os.path.abspath(os.path.join(os.path.join(os.getcwd(), "..", filename)))
                for filename in arguments
            ]
        else:
            config.filenames = [filename for filename in arguments]
    return config


def _get_mypy_issues(content: str) -> set[MypyIssue]:
    mypy_issues = set()
    for line in content.splitlines():
        kwargs = json.loads(line)
        mypy_issues.add(
            MypyIssue(
                file=kwargs["file"],
                line=kwargs["line"],
                column=kwargs["column"],
                code=kwargs["code"],
                severity=kwargs["severity"],
                original_line=line,
            )
        )
    return mypy_issues


def main() -> int:
    config = _get_config()

    out, err, code = run_mypy(
        [
            *config.filenames,
            "--output",
            "json",
        ]
    )

    sys.stderr.write(err)

    if config.baseline_mode:
        with open(config.baseline_path, "w") as f:
            f.write(out)
        sys.stdout.write(out)
        return 0

    baseline_issues = _get_mypy_issues(open(config.baseline_path).read())

    if code > 1:
        sys.stdout.write(out)
        return code

    new_issues = set()

    if code == 1:
        current_issues = _get_mypy_issues(out)

        new_issues = current_issues - baseline_issues
        if new_issues:
            sys.stdout.writelines(
                [
                    "New issues detected:\n\n",
                    *sorted(issue.original_line + "\n" for issue in new_issues),
                    "\n",
                ]
            )

        else:
            code = 0

    # When checking all files, we want to make sure that the baseline
    # does not contain issues that are no longer present
    if config.filenames == ["."]:
        removed_issues = baseline_issues - current_issues - new_issues
        if removed_issues:
            with open(config.baseline_path, "w") as f:
                f.writelines(
                    sorted(
                        issue.original_line + "\n"
                        for issue in (current_issues - removed_issues)
                    )
                )

            sys.stdout.writelines(
                [
                    "Stale baseline issues detected. "
                    f"Removed following lines from {config.baseline_path}:\n\n",
                    *sorted(issue.original_line + "\n" for issue in removed_issues),
                ]
            )
            code = 1

    return code


if __name__ == "__main__":
    sys.exit(main())
