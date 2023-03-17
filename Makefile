lint:
	poetry run pyright .

unit-test:
	poetry run coverage run -m pytest
	poetry run coverage lcov
