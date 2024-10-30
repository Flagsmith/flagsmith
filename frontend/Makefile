.EXPORT_ALL_VARIABLES:

COMPOSE_FILE ?= docker-compose-e2e-tests.postgres.yml
COMPOSE_PROJECT_NAME ?= flagsmith-e2e

DOTENV_OVERRIDE_FILE ?= .env

E2E_CONCURRENCY ?= 3

-include .env-local
-include $(DOTENV_OVERRIDE_FILE)

.PHONY: install
install:
	npm install

.PHONY: lint
lint:
	npm run lint

.PHONY: build
build:
	npm run build

.PHONY: serve
serve:
	npm run dev

.PHONY: test
test:
	docker compose run frontend \
		npx cross-env E2E_CONCURRENCY=${E2E_CONCURRENCY} npm run test -- $(opts) \
		|| (docker compose logs flagsmith-api; exit 1)
