CONFIG_PATH ?= e2e_test_config.yml
PYTEST_SPEC ?= tests/

lint-fix:
	poetry run ruff check --fix tests/
	poetry run black tests/

lint-check:
	poetry run ruff check tests/
	poetry run black --check tests/

audit:
	poetry run pip-audit

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


compile-translations:
	poetry run pybabel compile -d translations

