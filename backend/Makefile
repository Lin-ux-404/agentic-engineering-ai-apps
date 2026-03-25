.PHONY: lint typecheck test run

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

test:
	pytest tests/ -v

run:
	uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
