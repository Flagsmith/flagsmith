.EXPORT_ALL_VARIABLES:
FLAGSMITH_API_URL ?= https://api.flagsmith.com/api/v1
TRANSPORT ?= http


.PHONY: install
install:
	uv sync --frozen $(opts)

.PHONY: serve
serve:
	uv run flagsmith-mcp

.PHONY: lint
lint:
	uv run ruff check $(opts)
	uv run ruff format --check $(opts)

.PHONY: typecheck
typecheck:
	uv run mypy .

.PHONY: test
test:
	uv run pytest $(opts)
