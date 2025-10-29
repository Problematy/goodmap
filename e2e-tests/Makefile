GOODMAP_VERSION ?=
CONFIG_PATH ?= e2e_test_config.yml
GOODMAP_PATH ?= .

install-goodmap:
	pip install goodmap${GOODMAP_VERSION:+==}${GOODMAP_VERSION}

lint-fix:
	npm run lint-fix
	npm run prettier-fix

lint-check:
	npm run lint
	npm run prettier

run-e2e-goodmap:
	@PYTHONPATH="$(GOODMAP_PATH)" $$(cd "$(GOODMAP_PATH)" && poetry run which flask) --app "goodmap.goodmap:create_app(config_path='$(CONFIG_PATH)')" run

install-test-dependencies:
	npm install

e2e-tests:
	node_modules/cypress/bin/cypress run --browser chromium --spec "cypress/e2e/basic-test/*.cy.js"

e2e-stress-tests-generate-data:
	python tests/e2e_tests/cypress/support/generate_stress_test_data.py

e2e-stress-tests:
	node_modules/cypress/bin/cypress run --browser chromium --spec cypress/e2e/stress-test/*

run-e2e-stress-env:
	poetry run flask --app "goodmap.goodmap:create_app(config_path='e2e_stress_test_config.yml')" --debug run

cleanup:
	pip remove goodmap
	npm remove
