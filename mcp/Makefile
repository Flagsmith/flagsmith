.EXPORT_ALL_VARIABLES:
FLAGSMITH_API_URL ?= https://api.flagsmith.com/api/v1
TRANSPORT ?= http


.PHONY: install
install:
	uv sync --frozen $(opts)

.PHONY: test
test:
	uv run pytest $(opts)
