.PHONY: test lint format

test:
	pytest

lint:
	ruff check src tests benchmarks/development benchmarks/capabilities_v2
	ruff format --check src tests benchmarks/development benchmarks/capabilities_v2

format:
	ruff format src tests benchmarks/development benchmarks/capabilities_v2
