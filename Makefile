lint:
	poetry run black .
	poetry run ruff check --fix .

dev: lint
	poetry run pyright .

lint-check:
	poetry run black --check .
	poetry run ruff check .
	poetry run pyright .

unit-test:
	poetry run coverage run --source=goodmap -m pytest
	poetry run coverage lcov
