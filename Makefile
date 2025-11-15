CONFIG_PATH ?= examples/e2e_test_config.yml
RUNNING_DIRECTORY ?= .

lint-fix:
	poetry run black .
	poetry run ruff check --fix .

dev: lint-fix
	poetry run pyright .

lint-check:
	poetry run black --check .
	poetry run ruff check .
	poetry run pyright .
	poetry run interrogate goodmap/ --verbose

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

build:
	poetry run pybabel compile -d goodmap/locale
	poetry build

