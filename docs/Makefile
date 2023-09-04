.EXPORT_ALL_VARIABLES:

DOTENV_OVERRIDE_FILE ?= .env

-include .env-local
-include $(DOTENV_OVERRIDE_FILE)

.PHONY: install
install:
	npm install

.PHONY: lint-prettier
lint-prettier:
	npx prettier --check .

.PHONY: lint
lint: lint-prettier build

.PHONY: build
build:
	npm run build

.PHONY: serve
serve:
	npm run serve
