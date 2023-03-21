lint:
	poetry run black .
	poetry run pyright .
	poetry run ruff check --fix .


lint-check:
	poetry run black --check .
	poetry run pyright .
	poetry run ruff check .

unit-test:
	poetry run coverage run -m pytest
	poetry run coverage lcov
