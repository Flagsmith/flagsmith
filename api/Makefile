.EXPORT_ALL_VARIABLES:

DOCKER_TAG ?= flagsmith/flagsmith-api:local

COMPOSE_FILE ?= ../docker/api/docker-compose.local.yml
COMPOSE_PROJECT_NAME ?= flagsmith

DOTENV_OVERRIDE_FILE ?= .env

UV_VERSION ?= 0.5.14

SAML_REVISION ?= v1.6.6
RBAC_REVISION ?= v0.12.1

-include .env-local
-include $(DOTENV_OVERRIDE_FILE)

.PHONY: install-uv
install-uv:
	@command -v uv >/dev/null 2>&1 || pip install uv==${UV_VERSION}

.PHONY: install-packages
install-packages:
	uv sync $(opts)

.PHONY: install-private-modules
install-private-modules:
	$(eval SITE_PACKAGES_DIR := $(shell uv run python -c 'import site; print(site.getsitepackages()[0])'))
	git clone https://github.com/flagsmith/flagsmith-saml --depth 1 --branch ${SAML_REVISION} && mv ./flagsmith-saml/saml $(SITE_PACKAGES_DIR)
	git clone https://github.com/flagsmith/flagsmith-rbac --depth 1 --branch ${RBAC_REVISION} && mv ./flagsmith-rbac/rbac $(SITE_PACKAGES_DIR)
	rm -rf ./flagsmith-saml ./flagsmith-rbac

.PHONY: install
install: install-uv install-packages

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

.PHONY: test
test:
	uv run pytest $(opts)

.PHONY: django-make-migrations
django-make-migrations:
	uv run python manage.py waitfordb
	uv run python manage.py makemigrations $(opts)

.PHONY: django-squash-migrations
django-squash-migrations:
	uv run python manage.py waitfordb
	uv run python manage.py squashmigrations $(opts)

.PHONY: django-migrate
django-migrate:
	uv run python manage.py waitfordb
	uv run python manage.py migrate
	uv run python manage.py createcachetable

.PHONY: django-shell
django-shell:
	uv run python manage.py shell

.PHONY: django-collect-static
django-collect-static:
	uv run python manage.py collectstatic --noinput

.PHONY: serve
serve: docker-up
	uv run flagsmith start --reload api

.PHONY: run-task-processor
run-task-processor: docker-up
	uv run flagsmith start --reload --bind 0.0.0.0:8001 task-processor

.PHONY: serve-with-task-processor
serve-with-task-processor: TASK_RUN_METHOD=TASK_PROCESSOR
serve-with-task-processor:
	make -j2 serve run-task-processor

.PHONY: generate-ld-client-types
generate-ld-client-types:
	curl -sSL https://app.launchdarkly.com/api/v2/openapi.json | \
	npx openapi-format /dev/fd/0 \
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
	npx openapi-format /dev/fd/0 \
		--filterFile openapi-filter-grafana.yaml | \
	datamodel-codegen \
		--output integrations/grafana/types.py \
		--output-model-type typing.TypedDict \
		--target-python-version 3.10 \
		--use-double-quotes \
		--use-standard-collections \
		--wrap-string-literal \
		--special-field-name-prefix=

.PHONY: integrate-private-tests
integrate-private-tests:
	$(eval WORKFLOW_REVISION := $(shell uv run python -c "import tomllib; deps=tomllib.load(open('pyproject.toml','rb'))['dependency-groups']['private']; print([d.split('@')[-1] for d in deps if 'flagsmith-workflows' in d][0])"))
	$(eval AUTH_CONTROLLER_REVISION := $(shell uv run python -c "import tomllib; deps=tomllib.load(open('pyproject.toml','rb'))['dependency-groups']['private']; print([d.split('@')[-1] for d in deps if 'flagsmith-auth-controller' in d][0])"))

	git clone https://github.com/flagsmith/flagsmith-saml --depth 1 --branch ${SAML_REVISION} && mv ./flagsmith-saml/tests tests/saml_tests
	git clone https://github.com/flagsmith/flagsmith-rbac --depth 1 --branch ${RBAC_REVISION} && mv ./flagsmith-rbac/tests tests/rbac_tests
	git clone https://github.com/flagsmith/flagsmith-workflows --depth 1 --branch ${WORKFLOW_REVISION} && mv ./flagsmith-workflows/tests tests/workflow_tests
	git clone https://github.com/flagsmith/flagsmith-auth-controller --depth 1 --branch ${AUTH_CONTROLLER_REVISION} && mv ./flagsmith-auth-controller/tests tests/auth_controller_tests
	rm -rf ./flagsmith-saml ./flagsmith-rbac ./flagsmith-workflows ./flagsmith-auth-controller

.PHONY: generate-docs
generate-docs:
	uv run flagsmith docgen metrics > ../docs/docs/administration-and-security/platform-configuration/metrics.md

.PHONY: add-known-sdk-version
add-known-sdk-version:
	uv run python scripts/add-known-sdk-version.py $(opts)
