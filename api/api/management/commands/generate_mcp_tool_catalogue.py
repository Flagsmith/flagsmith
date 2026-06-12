import re
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from api.openapi import MCPSchemaGenerator

_TOOL_NAME_RE = re.compile(r"^\| `([^`]+)`")


class Command(BaseCommand):
    help = (
        "Generate a Markdown table of the MCP tool catalogue from the OpenAPI "
        "schema. The set of tools reflects the apps installed in the current "
        "environment, so private/enterprise tools only appear when their packages "
        "are installed. Pass --exclude to omit tools already listed in an existing "
        "catalogue (used to derive the enterprise-only catalogue against the core one)."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--exclude",
            type=Path,
            default=None,
            help="Path to an existing catalogue whose tools should be omitted.",
        )

    def handle(self, *args: Any, exclude: Path | None = None, **options: Any) -> None:
        excluded = _read_tool_names(exclude) if exclude else set()
        generator = MCPSchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        rows = sorted(
            (operation["operationId"], _one_line(operation.get("description", "")))
            for path_item in schema.get("paths", {}).values()
            for operation in path_item.values()
            if isinstance(operation, dict) and "operationId" in operation
            if operation["operationId"] not in excluded
        )

        self.stdout.write(_render_table(("Tool", "Description"), rows))


def _read_tool_names(path: Path) -> set[str]:
    return {
        match.group(1)
        for line in path.read_text().splitlines()
        if (match := _TOOL_NAME_RE.match(line))
    }


def _one_line(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _render_table(header: tuple[str, str], rows: list[tuple[str, str]]) -> str:
    # Render an aligned Markdown table matching Prettier's output so the committed
    # catalogue is reproducible by `make generate-docs` and passes the docs
    # Prettier check unchanged.
    cells = [list(header)] + [[f"`{name}`", description] for name, description in rows]
    widths = [max(len(row[col]) for row in cells) for col in range(len(header))]
    lines = [
        _render_row(cells[0], widths),
        "| " + " | ".join("-" * width for width in widths) + " |",
        *(_render_row(row, widths) for row in cells[1:]),
    ]
    return "\n".join(lines)


def _render_row(cells: list[str], widths: list[int]) -> str:
    padded = " | ".join(cell.ljust(width) for cell, width in zip(cells, widths))
    return f"| {padded} |"
