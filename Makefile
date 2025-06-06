.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run pytest tests -vv

.PHONY: test-cov
test-cov: ## Test the code with pytest and generate coverage report
	@uv run pytest tests --cov --cov-config=pyproject.toml --cov-report=xml --cov-context=test


.PHONY: release
release: ## Create a GitHub release for the current version
	@version=$$(grep -Po '(?<=__version__ = \")([^\"]+)' skippy_cov/__init__.py); \
	echo "🚀 Creating release for version $$version".; \
	gh release create "$$version" --generate-notes

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_.-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
