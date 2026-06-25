CONFIG_PATH ?= examples/e2e_test_config.yml
RUNNING_DIRECTORY ?= .

lint-fix:
	poetry run black goodmap/ tests/
	poetry run ruff check --fix goodmap/ tests/

# Convenience target for local use only - not called by any CI job, since
# each sub-project's CI workflow already lints itself independently.
lint-fix-all: lint-fix
	cd frontend && $(MAKE) lint-fix
	cd e2e-tests && $(MAKE) lint-fix

dev: lint-fix-all
	poetry run pyright goodmap/ tests/

lint-check:
	poetry run black --check goodmap/ tests/
	poetry run ruff check goodmap/ tests/
	poetry run pyright goodmap/ tests/
	poetry run interrogate goodmap/ --verbose

# Convenience target for local use only - not called by any CI job, since
# each sub-project's CI workflow already lints itself independently.
lint-check-all: lint-check
	cd frontend && $(MAKE) lint
	cd e2e-tests && $(MAKE) lint-check

dependency-check:
	poetry run pip-audit

# Approximates the dependency-review-action gate used in CI (license-check.yml)
# across all three sub-projects, so vulnerable transitive deps can be caught
# before pushing instead of discovered in a PR check.
dependency-check-all: dependency-check
	cd frontend && $(MAKE) audit
	cd e2e-tests && $(MAKE) audit

unit-tests:
	poetry run python -m pytest

unit-tests-no-coverage:
	poetry run python -m pytest -m "skip_coverage"

coverage:
	poetry run coverage run --branch --source=goodmap -m pytest -m "not skip_coverage"
	poetry run coverage lcov

html-cov: coverage
	poetry run coverage html

run-example-env:
	poetry --project '$(RUNNING_DIRECTORY)' run flask --app "goodmap.goodmap:create_app(config_path='$(CONFIG_PATH)')" --debug run

verify-json-data:
ifndef JSON_DATA_FILE
	$(error "Missing required argument JSON_DATA_FILE: make verify-json-data JSON_DATA_FILE=path/to/json")
else
	poetry run python -m goodmap.data_validator $(JSON_DATA_FILE)
endif

extract-translations:
	poetry run pybabel extract ./goodmap -o extracted.pot -F ./babel.cfg --project=goodmap
	poetry run pybabel update -i extracted.pot -d goodmap/locale --ignore-pot-creation-date --ignore-obsolete

build-frontend:
	mkdir -p goodmap/static/frontend
	cd frontend && npm ci && OUTPUT_DIR=../goodmap/static/frontend npm run build

build:
	poetry run pybabel compile -d goodmap/locale
	$(MAKE) build-frontend
	poetry build
