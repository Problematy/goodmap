install:
	python -m pip install --upgrade pip
	pip install poetry
	poetry install

lint:
	poetry run pyright .

unit-test:
	poetry run coverage run -m pytest
	poetry run coverage lcov
