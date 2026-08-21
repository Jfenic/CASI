.PHONY: test lint format

test:
	pytest

lint:
	python -m compileall src tests

format:
	python -m black src tests
