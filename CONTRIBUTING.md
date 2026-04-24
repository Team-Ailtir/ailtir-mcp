# Contributing to ailtir-mcp

For a general overview of the project structure and how to make code changes,
see [CLAUDE.md][]. For what the project does and how to install it, see
[README][].

## Development setup

```bash
git clone https://github.com/Team-Ailtir/ailtir-mcp
cd ailtir-mcp
uv sync --group dev
cp .env.example .env   # add your AILTIR_MCP_API_TOKEN
```

## Workflow

```bash
make checks        # format + lint + type-check + security scan
make tests-unit    # pytest with coverage (≥80% required)
make inspect       # launch MCP Inspector for interactive testing
```

All checks and tests must pass before opening a PR.

## Releasing to PyPI

### Prerequisites

A PyPI API token is required. It is stored in **1Password** under
`PyPI / ailtir-mcp publish token` and also saved locally in `.pypi.token`
(gitignored). `make publish` reads it automatically — no export needed.

If the file is missing, restore it from 1Password:

```bash
echo "pypi-..." > .pypi.token
chmod 600 .pypi.token
```

### Steps

1. Bump the version in `pyproject.toml` (`version = "x.y.z"`)
2. Update `CHANGELOG.md` (if present) or ensure the git log is clean
3. Commit and push:
   ```bash
   git add pyproject.toml
   git commit -m "Release x.y.z"
   git push
   ```
4. Tag the release:
   ```bash
   git tag vx.y.z
   git push --tags
   ```
5. Build and publish:
   ```bash
   make publish    # runs: uv build && uv publish
   ```

`make build` and `make publish` can also be run independently:

```bash
make build      # produces dist/ailtir_mcp-x.y.z-py3-none-any.whl and .tar.gz
make publish    # uploads dist/ to PyPI (requires UV_PUBLISH_TOKEN)
```

[CLAUDE.md]: CLAUDE.md
[README]: README.md
