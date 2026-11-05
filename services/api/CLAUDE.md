# services/api

- Точка входу — `main.py`; роутери в `routers/`, бізнес-логіка в `domain/`, моделі в `db/models.py`.
- Фонові воркери — `workers/`; вони використовують той самий `core/http.py`, що й API.
- Smoke-перевірка без зовнішніх сервісів: `uv run python services/api/smoke.py`.
