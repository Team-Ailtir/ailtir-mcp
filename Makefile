.DEFAULT_GOAL := help

GIT_REPO := $(shell basename -s .git $(shell git config --get remote.origin.url))
GIT_SHA  := $(shell git rev-parse --short HEAD)

define get_aws_repo
  $(shell aws ecr describe-repositories | jq -r '.repositories[] | select(.repositoryName | startswith("$(GIT_REPO)")) | .repositoryUri')
endef

.PHONY: help
help: ## Show help for all targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: checks
checks: format-check lint-check type-check security-check deploy-check ## Run all checks
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

.PHONY: serve-http
serve-http: ## Run the MCP HTTP (Streamable HTTP) server locally
	MCP_MOUNT_PATH=/mcp uv run --frozen --no-dev python -m ailtir_mcp.server_http

.PHONY: docker-build
docker-build: ## Build the Docker image
	docker build -t $(GIT_REPO) .
	docker tag $(GIT_REPO):latest $(GIT_REPO):$(GIT_SHA)

.PHONY: deploy-check
deploy-check: ## Verify release resolution, SSH trust, Compose, and rollback behavior
	.github/scripts/test-resolve-release-image.sh
	.github/scripts/test-deploy-workflow.sh
	deploy/test-deploy.sh
	AILTIR_MCP_ENV_FILE=/dev/null \
		AILTIR_MCP_IMAGE=ghcr.io/team-ailtir/ailtir-mcp:0123456789abcdef0123456789abcdef01234567 \
		docker compose -f deploy/docker-compose.yml config --quiet

.PHONY: docker-run
docker-run: ## Run the HTTP server container locally (requires AILTIR_MCP_API_TOKEN)
	docker run --rm -p 8000:8000 \
		-e AILTIR_MCP_API_TOKEN=$(AILTIR_MCP_API_TOKEN) \
		-e MCP_MOUNT_PATH=/mcp \
		$(GIT_REPO):latest

.PHONY: docker-push
docker-push: ## Push Docker image to ECR
	$(eval AWS_REPO := $(call get_aws_repo))
	docker tag $(GIT_REPO):latest $(AWS_REPO):$(GIT_SHA)
	docker push $(AWS_REPO):$(GIT_SHA)
	docker tag $(GIT_REPO):latest $(AWS_REPO):latest
	docker push $(AWS_REPO):latest

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

.PHONY: bump-major
bump-major: ## Bump major version (e.g. 1.2.3 → 2.0.0)
	@current=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/' | cut -d'+' -f1); \
	major=$$(echo $$current | cut -d'.' -f1); \
	new_version="$$((major + 1)).0.0"; \
	sed -i "s/^version = \".*\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "Version bumped to $$new_version"

.PHONY: bump-minor
bump-minor: ## Bump minor version (e.g. 1.2.3 → 1.3.0)
	@current=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/' | cut -d'+' -f1); \
	major=$$(echo $$current | cut -d'.' -f1); \
	minor=$$(echo $$current | cut -d'.' -f2); \
	new_version="$$major.$$((minor + 1)).0"; \
	sed -i "s/^version = \".*\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "Version bumped to $$new_version"

.PHONY: bump-patch
bump-patch: ## Bump patch version (e.g. 1.2.3 → 1.2.4)
	@current=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/' | cut -d'+' -f1); \
	major=$$(echo $$current | cut -d'.' -f1); \
	minor=$$(echo $$current | cut -d'.' -f2); \
	patch=$$(echo $$current | cut -d'.' -f3); \
	new_version="$$major.$$minor.$$((patch + 1))"; \
	sed -i "s/^version = \".*\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "Version bumped to $$new_version"

.PHONY: release
release: ## Commit, tag, push, and publish current version in pyproject.toml
	@version=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	git add pyproject.toml && \
	git commit -m "Bump version to $$version" && \
	git tag "v$$version" && \
	git push && \
	git push --tags && \
	$(MAKE) publish

.PHONY: tests
tests: tests-unit ## Run all tests

.PHONY: tests-unit
tests-unit: ## Run unit tests
	uv run pytest --cov --cov-fail-under 80 tests/unit

.PHONY: type-check
type-check: ## Type-check with mypy
	uv run mypy src/
