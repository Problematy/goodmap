lint-fix:
	npm run lint-fix
	npm run prettier-fix

lint-check:
	npm run lint
	npm run prettier

e2e-tests:
	node_modules/cypress/bin/cypress run --browser chromium --spec "cypress/e2e/basic-test/*.cy.js"

e2e-stress-tests-generate-data:
	python tests/e2e_tests/cypress/support/generate_stress_test_data.py

e2e-stress-tests:
	node_modules/cypress/bin/cypress run --browser chromium --spec cypress/e2e/stress-test/*

run-e2e-env:
	poetry run flask --app "goodmap.goodmap:create_app(config_path='tests/e2e_tests/e2e_test_config.yml')" --debug run

run-e2e-stress-env:
	poetry run flask --app "goodmap.goodmap:create_app(config_path='tests/e2e_tests/e2e_stress_test_config.yml')" --debug run

