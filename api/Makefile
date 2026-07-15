.EXPORT_ALL_VARIABLES:

DOCKER_TAG ?= flagsmith/flagsmith-api:local

COMPOSE_FILE ?= ../docker/api/docker-compose.local.yml
COMPOSE_PROJECT_NAME ?= flagsmith

DOTENV_OVERRIDE_FILE ?= .env

UV_VERSION ?= $(shell python -c 'import tomllib; print(tomllib.load(open("pyproject.toml","rb"))["tool"]["uv"]["required-version"].lstrip("<=>"))')

OPENAPI_FORMAT_VERSION ?= 1.23.0

-include .env-local
-include .env-codeartifact
-include $(DOTENV_OVERRIDE_FILE)

.PHONY: codeartifact-login
codeartifact-login:
	@token=$$(aws codeartifact get-authorization-token \
		--domain flagsmith-production --domain-owner 084060095745 \
		--region eu-west-2 \
		--query authorizationToken --output text) && \
	printf 'UV_INDEX_FLAGSMITH_PYPI_PRODUCTION_USERNAME=aws\nUV_INDEX_FLAGSMITH_PYPI_PRODUCTION_PASSWORD=%s\n' "$$token" > .env-codeartifact

.PHONY: install-packages
install-packages:
	uv sync --frozen $(opts)

.PHONY: install
install: install-packages

.PHONY: lint
lint:
	uv run pre-commit run -a

.PHONY: typecheck
typecheck:
	uv run mypy .

.PHONY: docker-up
docker-up:
	docker compose up --force-recreate --remove-orphans -d
	docker compose ps

.PHONY: docker-down
docker-down:
	docker compose stop

.PHONY: docker-logs
docker-logs:
	docker compose logs --follow

.PHONY: docker-build
docker-build:
	@docker build \
		--tag=$(DOCKER_TAG) \
		--file=../Dockerfile \
		--target=oss-api \
		../

.PHONY: wait-for-db
wait-for-db:
	uv run python manage.py waitfordb
	uv run python manage.py waitfordb --database analytics

.PHONY: test
test: docker-up wait-for-db
	uv run pytest $(opts)

.PHONY: django-make-migrations
django-make-migrations: docker-up wait-for-db
	uv run python manage.py waitfordb
	uv run python manage.py makemigrations $(opts)

.PHONY: django-squash-migrations
django-squash-migrations: docker-up wait-for-db
	uv run python manage.py waitfordb
	uv run python manage.py squashmigrations $(opts)

.PHONY: django-migrate
django-migrate: docker-up wait-for-db
	uv run python manage.py waitfordb
	uv run python manage.py migrate
	uv run python manage.py createcachetable

.PHONY: django-shell
django-shell:
	uv run python manage.py shell_plus

.PHONY: django-collect-static
django-collect-static:
	uv run python manage.py collectstatic --noinput

.PHONY: serve
serve: docker-up wait-for-db
	uv run flagsmith start --reload api

.PHONY: run-task-processor
run-task-processor: docker-up wait-for-db
	uv run flagsmith start --reload --bind 0.0.0.0:8001 task-processor

.PHONY: serve-with-task-processor
serve-with-task-processor: TASK_RUN_METHOD=TASK_PROCESSOR
serve-with-task-processor:
	make -j2 serve run-task-processor

.PHONY: generate-flagsmith-sdk-openapi
generate-flagsmith-sdk-openapi: OPENAPI_SERVERS=[{"url": "https://edge.api.flagsmith.com", "description": "Flagsmith Edge API"}]
generate-flagsmith-sdk-openapi:
	uv run python manage.py spectacular | \
	  npx openapi-format@${OPENAPI_FORMAT_VERSION} /dev/fd/0 \
	    --filterFile openapi-filter-flagsmith-sdk.yml \
	    --output ../sdk/openapi.yaml

.PHONY: generate-ld-client-types
generate-ld-client-types:
	curl -sSL https://app.launchdarkly.com/api/v2/openapi.json | \
	npx openapi-format@${OPENAPI_FORMAT_VERSION} /dev/fd/0 \
		--filterFile openapi-filter-launchdarkly.yaml | \
	datamodel-codegen \
		--output integrations/launch_darkly/types.py \
		--output-model-type typing.TypedDict \
		--target-python-version 3.10 \
		--use-double-quotes \
		--use-standard-collections \
		--wrap-string-literal \
		--special-field-name-prefix=

.PHONY: generate-grafana-client-types
generate-grafana-client-types:
	curl -sSL https://raw.githubusercontent.com/grafana/grafana/refs/heads/main/public/openapi3.json | \
	npx openapi-format@${OPENAPI_FORMAT_VERSION} /dev/fd/0 \
		--filterFile openapi-filter-grafana.yaml | \
	datamodel-codegen \
		--output integrations/grafana/types.py \
		--output-model-type typing.TypedDict \
		--target-python-version 3.10 \
		--use-double-quotes \
		--use-standard-collections \
		--wrap-string-literal \
		--special-field-name-prefix=

PRIVATE_TEST_DIRS := tests/rbac_tests tests/workflow_tests tests/auth_controller_tests tests/saml_integration_tests tests/licensing_integration_tests tests/ldap_integration_tests tests/saml_unit_tests

.PHONY: clean-private-tests
clean-private-tests:
	rm -rf $(PRIVATE_TEST_DIRS)

# scim and release_pipelines_logic are deliberately not pulled here: scim's
# compliance tests need an SCIM_SERVICE_PROVIDER config that conflicts with Core
# API's own scim tests (django-scim2 caches it globally), and release_pipelines
# has an order-dependent assertion that only holds in isolation. Both run in
# flagsmith-private's own CI.
# TODO https://github.com/Flagsmith/flagsmith-private/issues/177
.PHONY: integrate-private-tests
integrate-private-tests:
	@for dir in $(PRIVATE_TEST_DIRS); do \
		if [ -d "$$dir" ]; then \
			echo "Warning: $$dir already exists. Run 'make clean-private-tests' to remove all private test directories before re-running this command."; \
			exit 1; \
		fi; \
	done
	$(eval FLAGSMITH_PRIVATE_REVISION := v$(shell uv run python -c 'import importlib.metadata; print(importlib.metadata.version("flagsmith-private"))'))
	git clone https://github.com/Flagsmith/flagsmith-private --depth 1 --branch ${FLAGSMITH_PRIVATE_REVISION}
	mv ./flagsmith-private/integration_tests/rbac tests/rbac_tests
	mv ./flagsmith-private/integration_tests/workflows_logic tests/workflow_tests
	mv ./flagsmith-private/integration_tests/auth_controller tests/auth_controller_tests
	mv ./flagsmith-private/integration_tests/saml tests/saml_integration_tests
	mv ./flagsmith-private/integration_tests/licensing tests/licensing_integration_tests
	mv ./flagsmith-private/integration_tests/flagsmith_ldap tests/ldap_integration_tests
	mv ./flagsmith-private/unit_tests/saml tests/saml_unit_tests
	rm -rf ./flagsmith-private

CORE_OPENAPI_SERVERS := [{"url": "https://api.flagsmith.com", "description": "Flagsmith API"}]

.PHONY: generate-full-openapi
generate-full-openapi: OPENAPI_SERVERS=$(CORE_OPENAPI_SERVERS)
generate-full-openapi:
	uv run python manage.py spectacular | \
	  npx openapi-format@${OPENAPI_FORMAT_VERSION} /dev/fd/0 \
	    --output ../openapi.yaml

.PHONY: generate-mcp-openapi
generate-mcp-openapi:
	npx openapi-format@${OPENAPI_FORMAT_VERSION} ../openapi.yaml \
	  --filterFile openapi-filter-mcp.yaml \
	  --output ../mcp/src/flagsmith_mcp/openapi.json

.PHONY: generate-docs
generate-docs: generate-flagsmith-sdk-openapi generate-mcp-openapi
	uv run flagsmith docgen metrics > ../docs/docs/deployment-self-hosting/observability/_metrics-catalogue.md
	uv run flagsmith docgen events > ../docs/docs/deployment-self-hosting/observability/_events-catalogue.md
	uv run python manage.py generate_mcp_tool_catalogue > ../docs/docs/integrating-with-flagsmith/_mcp-tool-catalogue.md

.PHONY: add-known-sdk-version
add-known-sdk-version:
	uv run python scripts/add-known-sdk-version.py $(opts)
