PYTHON = poetry run

lint-fix:
	$(PYTHON) ruff check --fix tests/
	$(PYTHON) black tests/

lint-check:
	$(PYTHON) ruff check tests/
	$(PYTHON) black --check tests/

audit:
	$(PYTHON) pip-audit

setup-test-data:
	cp e2e_test_data_initial.json e2e_test_data.json
	sed 's|__E2E_TESTS_DIR__|$(CURDIR)|g' e2e_test_config.template.yml > e2e_test_config.yml
	$(MAKE) compile-translations

e2e-tests:
	$(PYTHON) pytest tests/basic -v

e2e-stress-tests-generate-data:
	$(PYTHON) python scripts/generate_stress_test_data.py

e2e-stress-tests:
	$(PYTHON) pytest tests/stress -v

compile-translations:
	$(PYTHON) pybabel compile -d translations
