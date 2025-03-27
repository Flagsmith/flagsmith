# usage: mypy . -output json | python baseline.py
import json
import re
import sys


def parse_mypy_output(output: str) -> None:
    # Parse the mypy output
    # We're interested in the following fields:
    # - `path` - the file path
    # - `line` - the line number
    # - `column` - the column number
    # - `code` - the error code

    # Split the output into lines
    lines = output.splitlines()

    # Iterate over the lines
    for line in lines:
        # Parse the line as json
        data = json.loads(line)

        # Extract the path, line, column and code
        path = data["file"]
        line = data["line"]
        code = data["code"]

        print(f"Processing {code} in {path} at line {line}")

        # Process the error code
        add_type_ignore(path, line, code)  # type: ignore[arg-type]


def add_type_ignore(path: str, line: int, error_code: str) -> None:
    # Add a `type-ignore` comment to the file at the specified line and column
    # We need to read the file, insert the comment and write the file back

    # Read the file
    with open(path, "r") as file:
        lines = file.readlines()

    # Find the line
    line_text = lines[line - 1]

    # If the line already contains a `type-ignore` comment
    # add the error_code to square brackets section
    # e.g. `# type: ignore[error_code] -> # type: ignore[error_code,error_code]`

    # Find the `type-ignore` comment
    match = re.search(r"# type: ignore\[(.*)\]", line_text)
    if match:
        # if error_code is "unused-ignore", remove the comment entirely
        if error_code == "unused-ignore":
            # Remove the old comment
            lines[line - 1] = line_text.replace(match.group(0), "")

        else:
            # Extract the existing error codes
            existing_error_codes = match.group(1).split(",")

            # Add the new error code
            existing_error_codes.append(error_code)

            # Create the new comment
            new_comment = f"# type: ignore[{','.join(sorted(existing_error_codes))}]"

            # Replace the old comment with the new one
            lines[line - 1] = line_text.replace(match.group(0), new_comment)
    else:
        # Create the new comment
        new_comment = f"# type: ignore[{error_code}]\n"

        # Append the comment to the line
        lines[line - 1] = line_text.replace("\n", "") + "  " + new_comment

    # Write the file
    with open(path, "w") as file:
        file.write("".join(lines))


if __name__ == "__main__":
    # Read the mypy output from stdin
    output = sys.stdin.read()

    # Parse the mypy output
    parse_mypy_output(output)
