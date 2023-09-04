.PHONY: install
install:
	cd api && $(MAKE) install
	cd docs && $(MAKE) install

.PHONY: lint
lint:
	cd api && $(MAKE) lint
	cd docs && $(MAKE) lint
