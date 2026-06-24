# Include .env file if it exists (for GOODMAP_PATH, etc.)
-include .env

CONFIG_PATH ?= e2e_test_config.yml
STRESS_CONFIG_PATH ?= e2e_stress_test_config.yml
GOODMAP_PATH ?= .
PYTEST_SPEC ?= tests/

lint-fix:
	poetry run ruff check --fix tests/
	poetry run black tests/

lint-check:
	poetry run ruff check tests/
	poetry run black --check tests/

pytest-run:
	poetry run pytest $(PYTEST_SPEC) -v

setup-test-data:
	cp e2e_test_data_template.json e2e_test_data.json
	sed 's|__E2E_TESTS_DIR__|$(CURDIR)|g' e2e_test_config.template.yml > e2e_test_config.yml
	$(MAKE) compile-translations

e2e-tests:
	$(MAKE) pytest-run PYTEST_SPEC="tests/basic"

e2e-stress-tests-generate-data:
	python scripts/generate_stress_test_data.py

e2e-stress-tests:
	$(MAKE) pytest-run PYTEST_SPEC="tests/stress"

run-e2e-env:
	poetry --project '$(GOODMAP_PATH)' run flask --app "goodmap.goodmap:create_app(config_path='$(CONFIG_PATH)')" --debug run

run-e2e-stress-env:
	poetry --project '$(GOODMAP_PATH)' run flask --app "goodmap.goodmap:create_app(config_path='$(STRESS_CONFIG_PATH)')" --debug run

compile-translations:
	poetry run pybabel compile -d translations

