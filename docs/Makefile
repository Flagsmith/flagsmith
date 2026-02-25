.EXPORT_ALL_VARIABLES:

DOTENV_OVERRIDE_FILE ?= .env

-include .env-local
-include $(DOTENV_OVERRIDE_FILE)

.PHONY: install
install:
	npm install

.PHONY: generate-sdk-api-docs
generate-sdk-api-docs:
	npm run docusaurus clean-api-docs all
	npm run docusaurus gen-api-docs all

.PHONY: lint-prettier
lint-prettier:
	npx prettier --check .

.PHONY: lint
lint: lint-prettier build

.PHONY: build
build: generate-sdk-api-docs
	npm run build

.PHONY: serve
serve: generate-sdk-api-docs
	npm run start
