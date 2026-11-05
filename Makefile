# Піраміда верифікації (Серія 05): типи → лінтер → юніт-тести → smoke.
.PHONY: check types lint test smoke dev

check: types lint test smoke

types:
	uv run mypy services/api

lint:
	uv run ruff check .

test:
	uv run pytest -q

smoke:
	uv run python services/api/smoke.py

dev:
	uv run uvicorn main:app --app-dir services/api --port 8001 --reload
