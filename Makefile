CONFIG_PATH ?= examples/e2e_test_config.yml
E2E_CONFIG_PATH ?= e2e-tests/e2e_test_config.yml
E2E_STRESS_CONFIG_PATH ?= e2e-tests/e2e_stress_test_config.yml

PYTHON = poetry run

lint-fix:
	$(PYTHON) black goodmap/ tests/
	$(PYTHON) ruff check --fix goodmap/ tests/

# Convenience target for local use only - not called by any CI job, since
# each sub-project's CI workflow already lints itself independently.
lint-fix-all: lint-fix
	$(MAKE) -C frontend lint-fix
	$(MAKE) -C e2e-tests lint-fix

dev: lint-fix-all lint-check-all unit-tests

lint-check:
	$(PYTHON) black --check goodmap/ tests/
	$(PYTHON) ruff check goodmap/ tests/
	$(PYTHON) pyright goodmap/ tests/
	$(PYTHON) interrogate goodmap/ --verbose

# Convenience target for local use only - not called by any CI job, since
# each sub-project's CI workflow already lints itself independently.
lint-check-all: lint-check
	$(MAKE) -C frontend lint
	$(MAKE) -C e2e-tests lint-check

dependency-check:
	$(PYTHON) pip-audit

# Approximates the dependency-review-action gate used in CI (license-check.yml)
# across all three sub-projects, so vulnerable transitive deps can be caught
# before pushing instead of discovered in a PR check.
dependency-check-all: dependency-check
	$(MAKE) -C frontend audit
	$(MAKE) -C e2e-tests audit

unit-tests:
	$(PYTHON) python -m pytest

unit-tests-no-coverage:
	$(PYTHON) python -m pytest -m "skip_coverage"

coverage:
	$(PYTHON) coverage run --branch --source=goodmap -m pytest -m "not skip_coverage"
	$(PYTHON) coverage lcov

html-cov: coverage
	$(PYTHON) coverage html

run-example-env:
	$(PYTHON) flask --app "goodmap.goodmap:create_app(config_path='$(CONFIG_PATH)')" --debug run

run-e2e-stress-env:
	$(PYTHON) flask --app "goodmap.goodmap:create_app(config_path='$(E2E_STRESS_CONFIG_PATH)')" --debug run

# Regenerates the templated e2e config (absolute paths) and a fresh copy of the
# test data. Prerequisite of run-e2e-backend, not e2e-tests, so the json_file DB
# is reset once when the backend boots rather than mid-session from the tests.
setup-e2e-data:
	$(MAKE) -C e2e-tests setup-test-data

run-e2e-backend: setup-e2e-data
	$(PYTHON) flask --app "goodmap.goodmap:create_app(config_path='$(E2E_CONFIG_PATH)')" run

run-frontend:
	$(MAKE) -C frontend serve-prod

check-e2e-servers:
	@curl -sf http://localhost:5000 -o /dev/null || (echo "Backend not running at :5000 — run: make run-e2e-backend" >&2; exit 1)
	@curl -sf http://localhost:8080/index.min.js -o /dev/null || (echo "Frontend not running at :8080 — run: make run-frontend" >&2; exit 1)

e2e-tests: check-e2e-servers
	$(MAKE) -C e2e-tests e2e-tests

verify-json-data:
ifndef JSON_DATA_FILE
	$(error "Missing required argument JSON_DATA_FILE: make verify-json-data JSON_DATA_FILE=path/to/json")
else
	$(PYTHON) python -m goodmap.data_validator $(JSON_DATA_FILE)
endif

extract-translations:
	$(PYTHON) pybabel extract ./goodmap -o extracted.pot -F ./babel.cfg --project=goodmap
	$(PYTHON) pybabel update -i extracted.pot -d goodmap/locale --ignore-pot-creation-date --ignore-obsolete

build-frontend:
	mkdir -p goodmap/static/frontend
	$(MAKE) -C frontend install-ci
	OUTPUT_DIR=$(CURDIR)/goodmap/static/frontend $(MAKE) -C frontend build
	@test -f goodmap/static/frontend/index.min.js \
		|| (echo "ERROR: build-frontend did not produce goodmap/static/frontend/index.min.js" >&2; exit 1)

build:
	$(PYTHON) pybabel compile -d goodmap/locale
	$(MAKE) build-frontend
	poetry build
