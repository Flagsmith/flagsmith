import io
from pathlib import Path

from django.core.management import call_command


def _tool_names(table: str) -> list[str]:
    return [line.split("`")[1] for line in table.splitlines() if line.startswith("| `")]


def test_generate_mcp_tool_catalogue__no_args__renders_sorted_mcp_tool_table() -> None:
    # Given
    out = io.StringIO()

    # When
    call_command("generate_mcp_tool_catalogue", stdout=out)

    # Then
    table = out.getvalue()
    lines = table.splitlines()
    assert lines[0].startswith("| Tool ")
    assert set(lines[1].replace("|", "").replace(" ", "")) == {"-"}

    names = _tool_names(table)
    assert "list_environments" in names
    assert names == sorted(names)
    assert "Lists all environments the user has access to" in table


def test_generate_mcp_tool_catalogue__exclude_file__omits_listed_tools(
    tmp_path: Path,
) -> None:
    # Given
    exclude = tmp_path / "_mcp-tool-catalogue.md"
    exclude.write_text("| Tool | Description |\n| `list_environments` | ... |\n")
    out = io.StringIO()

    # When
    call_command("generate_mcp_tool_catalogue", exclude=exclude, stdout=out)

    # Then
    names = _tool_names(out.getvalue())
    assert "list_environments" not in names
    assert "get_project" in names


def test_generate_mcp_tool_catalogue__description_with_pipe__escapes_pipe() -> None:
    # Given / When
    out = io.StringIO()
    call_command("generate_mcp_tool_catalogue", stdout=out)

    # Then
    # No raw pipe should appear inside a description cell (only as a column
    # separator), so every table row has exactly two unescaped delimiters plus
    # the leading and trailing ones.
    for line in out.getvalue().splitlines():
        if line.startswith("| `"):
            assert line.replace("\\|", "").count("|") == 3
