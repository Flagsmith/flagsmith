.EXPORT_ALL_VARIABLES:

COMPOSE_FILE ?= docker-compose-e2e-tests.yml
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
	mkdir -p e2e-videos
	docker rm -f e2e-test-runner 2>/dev/null || true
	docker compose run --rm=false --name e2e-test-runner frontend \
		npx cross-env E2E_CONCURRENCY=${E2E_CONCURRENCY} npm run test -- $(opts); \
		TEST_EXIT_CODE=$$?; \
		docker cp e2e-test-runner:/srv/flagsmith/reports/screen-captures/. e2e-videos/ 2>/dev/null || true; \
		docker rm e2e-test-runner 2>/dev/null || true; \
		if [ $$TEST_EXIT_CODE -ne 0 ]; then docker compose logs flagsmith-api; exit $$TEST_EXIT_CODE; fi
