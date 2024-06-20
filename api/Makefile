.EXPORT_ALL_VARIABLES:

DOCKER_TAG ?= flagsmith/flagsmith-api:local

COMPOSE_FILE ?= ../docker/db.yml
COMPOSE_PROJECT_NAME ?= flagsmith

DOTENV_OVERRIDE_FILE ?= .env

POETRY_VERSION ?= 1.8.3

GUNICORN_LOGGER_CLASS ?= util.logging.GunicornJsonCapableLogger

SAML_REVISION ?= v1.6.2
RBAC_REVISION ?= v0.7.0

-include .env-local
-include $(DOTENV_OVERRIDE_FILE)

.PHONY: install-pip
install-pip:
	python -m pip install --upgrade pip

.PHONY: install-poetry
install-poetry:
	curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}

.PHONY: install-packages
install-packages:
	poetry install --no-root $(opts)

.PHONY: install-private-modules
install-private-modules:
	$(eval SITE_PACKAGES_DIR := $(shell poetry run python -c 'import site; print(site.getsitepackages()[0])'))
	git clone https://github.com/flagsmith/flagsmith-saml --depth 1 --branch ${SAML_REVISION} && mv ./flagsmith-saml/saml $(SITE_PACKAGES_DIR)
	git clone https://github.com/flagsmith/flagsmith-rbac --depth 1 --branch ${RBAC_REVISION} && mv ./flagsmith-rbac/rbac $(SITE_PACKAGES_DIR)
	rm -rf ./flagsmith-saml ./flagsmith-rbac

.PHONY: install
install: install-pip install-poetry install-packages

.PHONY: lint-black
lint-black:
	poetry run black --check .

.PHONY: lint-isort
lint-isort:
	poetry run isort  --check-only --diff .

.PHONY: lint-flake8
lint-flake8:
	poetry run flake8

.PHONY: lint
lint: lint-black lint-isort lint-flake8

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
	poetry run pytest $(opts)

.PHONY: django-make-migrations
django-make-migrations:
	poetry run python manage.py waitfordb
	poetry run python manage.py makemigrations $(opts)

.PHONY: django-migrate
django-migrate:
	poetry run python manage.py waitfordb
	poetry run python manage.py migrate
	poetry run python manage.py createcachetable

.PHONY: django-collect-static
django-collect-static:
	poetry run python manage.py collectstatic --noinput

.PHONY: serve
serve:
	poetry run gunicorn --bind 0.0.0.0:8000 \
		--logger-class ${GUNICORN_LOGGER_CLASS} \
		--reload \
		app.wsgi

.PHONY: generate-ld-client-types
generate-ld-client-types:
	curl -sSL https://app.launchdarkly.com/api/v2/openapi.json | \
	npx openapi-format /dev/fd/0 \
		--filterFile ld-openapi-filter.yaml | \
	datamodel-codegen \
		--output integrations/launch_darkly/types.py \
		--output-model-type typing.TypedDict \
		--target-python-version 3.10 \
		--use-double-quotes \
		--use-standard-collections \
		--wrap-string-literal \
		--special-field-name-prefix=
