.EXPORT_ALL_VARIABLES:

COMPOSE_FILE ?= docker-compose-e2e-tests.yml
COMPOSE_PROJECT_NAME ?= flagsmith-e2e

DOTENV_OVERRIDE_FILE ?= .env

E2E_CONCURRENCY ?= 3
E2E_RETRIES ?= 1

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
	@echo "Running E2E tests..."
	@docker compose run --name e2e-test-run frontend \
		sh -c 'npx cross-env E2E_CONCURRENCY=${E2E_CONCURRENCY} E2E_RETRIES=${E2E_RETRIES} npm run test -- $(opts); \
		EXIT=$$?; \
		if [ "$${VISUAL_REGRESSION}" = "1" ]; then npm run test:visual:compare -- $${VISUAL_REGRESSION_ARGS} || true; fi; \
		exit $$EXIT' \
		|| TEST_FAILED=1; \
	echo "Copying test results from container..."; \
	docker cp e2e-test-run:/srv/flagsmith/e2e/test-results ./e2e/test-results 2>/dev/null || echo "No test results to copy"; \
	docker cp e2e-test-run:/srv/flagsmith/e2e/playwright-report ./e2e/playwright-report 2>/dev/null || echo "No HTML report to copy"; \
	docker cp e2e-test-run:/srv/flagsmith/e2e/visual-regression-screenshots ./e2e/visual-regression-screenshots 2>/dev/null || echo "No visual regression screenshots to copy"; \
	docker cp e2e-test-run:/srv/flagsmith/e2e/visual-regression-report ./e2e/visual-regression-report 2>/dev/null || echo "No visual regression report to copy"; \
	docker rm e2e-test-run 2>/dev/null || true; \
	if [ "$$TEST_FAILED" = "1" ]; then \
		echo "\n=== API logs ===" && docker compose logs flagsmith-api && \
		echo "\n=== Frontend logs (includes test results) ===" && docker compose logs frontend && \
		exit 1; \
	fi

.PHONY: test-oss
test-oss:
	@$(MAKE) test opts="--grep @oss"

.PHONY: test-enterprise
test-enterprise:
	@$(MAKE) test opts="--grep @enterprise"

# Visual regression: run E2E tests with screenshot comparison enabled.
# Snapshots are shared via volume mount in docker-compose-e2e-tests.yml.
.PHONY: test-visual
test-visual:
	@mkdir -p e2e/visual-regression-snapshots
	@VISUAL_REGRESSION=1 $(MAKE) test opts="$(opts)"
