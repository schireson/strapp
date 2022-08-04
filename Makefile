.PHONY: install build test lint format publish
.DEFAULT_GOAL := test

install:
	poetry install -E click -E sqlalchemy -E sentry -E flask -E http -E datadog -E dramatiq

build:
	poetry build

test:
	coverage run -a -m py.test src tests -vv
	coverage report
	coverage xml

lint:
	flake8 src tests || exit 1
	isort --check-only --recursive src tests || exit 1
	pydocstyle src tests || exit 1
	black --check src tests || exit 1
	mypy src tests || exit 1
	bandit -r src || exit 1

format:
	isort --recursive src tests
	black src tests

publish: build
	poetry publish -u __token__ -p '${PYPI_PASSWORD}' --no-interaction
