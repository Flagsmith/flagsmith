.EXPORT_ALL_VARIABLES:

DOCKER_TAG ?= flagsmith/flagsmith-api:local

COMPOSE_FILE ?= ../docker/db.yaml
COMPOSE_PROJECT_NAME ?= flagsmith

DOTENV_OVERRIDE_FILE ?= .env

-include .env-local
-include $(DOTENV_OVERRIDE_FILE)

.PHONY: install-pip
install-pip:
	python -m pip install --upgrade pip

.PHONY: install-packages
install-packages:
	pip install -r requirements-all.txt

.PHONY: install-packages-dev
install-packages-dev:
	pip install -r requirements-dev.txt

.PHONY: install
install: install-pip install-packages

.PHONY: lint-black
lint-black:
	pre-commit run --all-files black

.PHONY: lint-isort
lint-isort:
	pre-commit run --all-files isort

.PHONY: lint-flake8
lint-flake8:
	pre-commit run --all-files flake8

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
	pytest $(opts)

.PHONY: django-make-migrations
django-make-migrations:
	python manage.py waitfordb
	python manage.py makemigrations $(opts)

.PHONY: django-migrate
django-migrate:
	python manage.py waitfordb
	python manage.py migrate

.PHONY: django-collect-static
django-collect-static:
	python manage.py collectstatic --noinput

.PHONY: serve
serve:
	gunicorn --bind 0.0.0.0:8000 app.wsgi --reload
