lint-fix:
	poetry run black .
	poetry run ruff check --fix .
	cd tests/e2e_tests && npm run lint-fix
	cd tests/e2e_tests && npm run prettier-fix

dev: lint-fix
	poetry run pyright .

lint-check:
	poetry run black --check .
	poetry run ruff check .
	poetry run pyright .
	cd tests/e2e_tests && npm run lint
	cd tests/e2e_tests && npm run prettier

unit-tests:
	poetry run python -m pytest

unit-tests-no-coverage:
	poetry run python -m pytest -m "skip_coverage"

e2e-tests:
	cd tests/e2e_tests && node_modules/cypress/bin/cypress run --browser chromium --spec "cypress/e2e/basic-test/*.cy.js"

e2e-stress-tests-generate-data:
	python tests/e2e_tests/cypress/support/generate_stress_test_data.py

e2e-stress-tests:
	cd tests/e2e_tests && node_modules/cypress/bin/cypress run --browser chromium --spec cypress/e2e/stress-test/*

coverage:
	poetry run coverage run --branch --source=goodmap -m pytest -m "not skip_coverage"
	poetry run coverage lcov

html-cov: coverage
	poetry run coverage html

run-e2e-env:
	poetry run flask --app "goodmap.goodmap:create_app(config_path='tests/e2e_tests/e2e_test_config.yml')" --debug run

run-e2e-stress-env:
	poetry run flask --app "goodmap.goodmap:create_app(config_path='tests/e2e_tests/e2e_stress_test_config.yml')" --debug run

verify-json-data:
ifndef JSON_DATA_FILE
	$(error "Missing required argument JSON_DATA_FILE: make verify-json-data JSON_DATA_FILE=path/to/json")
else
	poetry run python -m goodmap.data_validator $(JSON_DATA_FILE)
endif

extract-translations:
	poetry run pybabel extract ./goodmap -o extracted.pot -F ./babel.cfg --project=goodmap
	poetry run pybabel update -i extracted.pot -d goodmap/locale --ignore-pot-creation-date --ignore-obsolete

build:
	poetry run pybabel compile -d goodmap/locale
	poetry build
