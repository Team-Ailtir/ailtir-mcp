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

.PHONY: publish
publish: ## Build and publish to PyPI
	uv build
	uv publish

.PHONY: tests
tests: tests-unit ## Run all tests

.PHONY: tests-unit
tests-unit: ## Run unit tests
	uv run pytest --cov --cov-fail-under 80 tests/unit

.PHONY: type-check
type-check: ## Type-check with mypy
	uv run mypy src/
