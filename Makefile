.PHONY: install-pre-commit
install-pre-commit:
	curl -LsSf uvx.sh/pre-commit/install.sh | sh

.PHONY: install-hooks
install-hooks: install-pre-commit
	pre-commit install

.PHONY: install
install:
	$(MAKE) -C api install
	$(MAKE) -C docs install
	$(MAKE) -C frontend install

.PHONY: lint
lint:
	$(MAKE) -C api lint
	$(MAKE) -C docs lint
	$(MAKE) -C frontend lint

# Run `make docker-up flags-only=1` to run Flagsmith without experimentation.
compose-file = $(if $(flags-only),docker-compose.flags-only.yml,docker-compose.yml)

.PHONY: docker-up
docker-up:
	docker compose -f $(compose-file) up -d

.PHONY: docker-down
docker-down:
	docker compose -f $(compose-file) down
