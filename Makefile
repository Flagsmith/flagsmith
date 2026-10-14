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

.PHONY: docker-up
docker-up:
	docker compose up -d

.PHONY: docker-up-flags-only
docker-up-flags-only:
	EXPERIMENTATION_ENABLED=false docker compose up -d flagsmith flagsmith-task-processor

.PHONY: docker-down
docker-down:
	docker compose down
