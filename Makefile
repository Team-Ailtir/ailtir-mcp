.DEFAULT_GOAL := help

.PHONY: help
help: ## Show help for all targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: checks
checks: format-check lint-check type-check security-check ## Run all checks
	@echo "All checks passed!"

.PHONY: checks-fix
checks-fix: format-fix lint-fix ## Fix all fixable issues

.PHONY: clean
clean: ## Clean cache and build artefacts
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
	find . -type f -name "*.pyc" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf dist/

.PHONY: format-check
format-check: ## Check formatting with ruff
	uv run ruff format --check .

.PHONY: format-fix
format-fix: ## Fix formatting with ruff
	uv run ruff format .

.PHONY: inspect
inspect: ## Launch MCP Inspector (requires dev dependencies)
	uv run mcp dev src/ailtir_mcp/server.py

.PHONY: install
install: ## Install production dependencies
	uv sync --no-dev

.PHONY: install-dev
install-dev: ## Install all dependencies including dev
	uv sync --group dev

.PHONY: lint-check
lint-check: ## Lint with ruff
	uv run ruff check .

.PHONY: lint-fix
lint-fix: ## Fix lint issues with ruff
	uv run ruff check --fix .

.PHONY: security-check
security-check: ## Security scan with bandit
	uv run bandit -c .bandit -r src/

.PHONY: serve
serve: ## Run the MCP server
	uv run --frozen --no-dev python -m ailtir_mcp.server

.PHONY: build
build: ## Build distribution packages (sdist + wheel)
	rm -rf dist/
	uv build

.PHONY: publish
publish: build ## Build and publish to PyPI (reads UV_PUBLISH_TOKEN or .pypi.token)
	@if [ -f .pypi.token ]; then \
		UV_PUBLISH_TOKEN=$$(cat .pypi.token) uv publish; \
	else \
		uv publish; \
	fi

.PHONY: bump-version
bump-version: ## Bump minor version and append current commit hash (e.g. 1.2.0+abc1234)
	@current=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/' | cut -d'+' -f1); \
	major=$$(echo $$current | cut -d'.' -f1); \
	minor=$$(echo $$current | cut -d'.' -f2); \
	patch=$$(echo $$current | cut -d'.' -f3); \
	new_minor=$$((minor + 1)); \
	hash=$$(git rev-parse --short HEAD); \
	new_version="$$major.$$new_minor.$$patch+$$hash"; \
	sed -i "s/^version = \".*\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "Version bumped to $$new_version"

.PHONY: release
release: bump-version ## Bump version, commit, push, then publish to PyPI
	@version=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	git add pyproject.toml && \
	git commit -m "Bump version to $$version" && \
	git push && \
	$(MAKE) publish

.PHONY: tests
tests: tests-unit ## Run all tests

.PHONY: tests-unit
tests-unit: ## Run unit tests
	uv run pytest --cov --cov-fail-under 80 tests/unit

.PHONY: type-check
type-check: ## Type-check with mypy
	uv run mypy src/
