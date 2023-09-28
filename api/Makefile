.EXPORT_ALL_VARIABLES:

DOCKER_TAG ?= flagsmith/flagsmith-api:local

COMPOSE_FILE ?= ../docker/db.yaml
COMPOSE_PROJECT_NAME ?= flagsmith

DOTENV_OVERRIDE_FILE ?= .env

POETRY_VERSION ?= 1.5.1

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
	poetry install $(opts)

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
	docker-compose up --force-recreate --remove-orphans -d
	docker-compose ps

.PHONY: docker-down
docker-down:
	docker-compose stop

.PHONY: docker-logs
docker-logs:
	docker-compose logs --follow

.PHONY: docker-build
docker-build:
	@docker build \
		--tag=$(DOCKER_TAG) \
		--file=Dockerfile \
		.

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
	poetry run gunicorn --bind 0.0.0.0:8000 app.wsgi --reload

.PHONY: generate-ld-client-types
generate-ld-client-types:
	curl -sSL https://static.launchdarkly.com/app/s/openapi.2161bd87d.json | \
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
