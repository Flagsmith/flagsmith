.EXPORT_ALL_VARIABLES:

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
	docker compose -f docker-compose-e2e-tests.yml run frontend \
		npx cross-env E2E_CONCURRENCY=${E2E_CONCURRENCY} npm run test -- ${NPM_TEST_ARGS}
