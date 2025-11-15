CONFIG_PATH ?= e2e_test_config.yml
GOODMAP_PATH ?= .
CYPRESS_SPEC ?= cypress/e2e/**/*.cy.js

lint-fix:
	npm run lint-fix
	npm run prettier-fix

lint-check:
	npm run lint
	npm run prettier

cypress-run:
	node_modules/cypress/bin/cypress run --browser chromium --spec "$(CYPRESS_SPEC)"

e2e-tests:
	$(MAKE) cypress-run CYPRESS_SPEC="cypress/e2e/basic-test/*.cy.js"

e2e-stress-tests-generate-data:
	python cypress/support/generate_stress_test_data.py

e2e-stress-tests:
	$(MAKE) cypress-run CYPRESS_SPEC="cypress/e2e/stress-test/*"

run-e2e-env:
	poetry --project '$(GOODMAP_PATH)' run flask --app "goodmap.goodmap:create_app(config_path='$(CONFIG_PATH)')" --debug run

