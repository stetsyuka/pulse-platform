#!/usr/bin/env python3
# ruff: noqa: E501  — описи інструментів і демо-записи свідомо довгі: їх читає модель
"""
ЕПІЗОД 08 • Starter Kit: Власний компактний MCP-сервер для інженерної бази знань (FastMCP).

Запуск у режимі локальної перевірки (через uv):
  uv run --python 3.12 --with "mcp==1.30.0" python mcp-knowledge-server.example.py

Підключення до проєкту в Claude Code:
  claude mcp add --scope project arch-kg -- uv run --python 3.12 --with "mcp==1.30.0" python ./course/starter-kit/ep08/mcp-knowledge-server.example.py
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

# КРИТИЧНЕ ПРАВИЛО MCP STDIO:
# Жодного print() у stdout! Усі логи пишемо виключно у sys.stderr.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [arch-kg] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("arch-kg")

mcp = FastMCP("arch-knowledge-graph")

# Демо-набір архітектурних нотаток (ADR), щоб сервер працював із коробки без піднятої БД.
# У продакшені цей шар читає PostgreSQL (read-only роль) через змінну оточення DATABASE_URL,
# передану в оперативній пам'яті з HashiCorp Vault.
DEMO_ADR_RECORDS = [
    {
        "id": "ADR-014",
        "domain": "security",
        "service": "auth-gateway",
        "title": "Перехід на короткоживучі креденшели БД через HashiCorp Vault",
        "summary": "Відмова від статичних DATABASE_URL у .env/.mcp.json; TTL сесії 1 година, роль app_readonly для аналітики.",
    },
    {
        "id": "ADR-019",
        "domain": "backend",
        "service": "billing-api",
        "title": "Ідемпотентна обробка вебхуків оплати через ключ X-Idempotency-Key",
        "summary": "Повторні події платіжного шлюзу дедуплікуються у таблиці webhook_inbox за унікальним індексом.",
    },
    {
        "id": "ADR-023",
        "domain": "infra",
        "service": "worker-dispatcher",
        "title": "Обмеження часу запитів агентів (statement_timeout = 5s)",
        "summary": "Окрема репліка db-readonly.internal.example для MCP-запитів із жорстким лімітом пам'яті та часу.",
    },
]

DEMO_DEPENDENCIES = {
    "billing-api": {
        "upstream": ["auth-gateway (gRPC)", "pricing-catalog (HTTP)"],
        "downstream": ["postgres-billing (primary)", "notification-worker (queue)"],
        "sla": "99.95%, p99 < 180ms",
    },
    "auth-gateway": {
        "upstream": ["edge-ingress"],
        "downstream": ["redis-sessions", "vault.internal.example:8200"],
        "sla": "99.99%, p99 < 45ms",
    },
}


@mcp.tool(
    name="search_architecture_notes",
    description=(
        "Шукає затверджені архітектурні рішення (ADR) та інженерні правила проєкту за ключовими словами. "
        "Викликай перед проектуванням змін у бекенді, безпеці чи інфраструктурі."
    ),
)
def search_architecture_notes(
    query: str = Field(
        ...,
        min_length=2,
        max_length=120,
        description="Пошуковий запит: назва сервісу, технологія або проблема (наприклад, 'billing', 'vault', 'webhook').",
    ),
    domain: Literal["all", "backend", "infra", "security"] = Field(
        default="all",
        description="Фільтр інженерного домену для звуження результатів.",
    ),
    limit: int = Field(
        default=5,
        ge=1,
        le=15,
        description="Максимальна кількість записів у відповіді (1..15) для економії контекстного вікна.",
    ),
) -> str:
    logger.info("Пошук ADR: query=%r, domain=%s, limit=%d", query, domain, limit)
    needle = query.strip().lower()

    matches = []
    for row in DEMO_ADR_RECORDS:
        if domain != "all" and row["domain"] != domain:
            continue
        haystack = f"{row['id']} {row['service']} {row['title']} {row['summary']}".lower()
        if needle in haystack:
            matches.append(row)

    matches = matches[:limit]
    if not matches:
        return f"За запитом '{query}' (domain={domain}) архітектурних записів не знайдено."

    # ЗАКОН ЕКОНОМІЇ ТОКЕНІВ: повертаємо стислий Markdown замість сирого мегабайтного JSON-дампу
    lines = [f"Знайдено записів ADR: {len(matches)}"]
    for item in matches:
        lines.append(
            f"- [{item['id']}] ({item['domain']} | {item['service']}) {item['title']}\n"
            f"  Суть: {item['summary']}"
        )
    return "\n".join(lines)


@mcp.tool(
    name="get_service_dependencies",
    description=(
        "Повертає актуальну карту upstream/downstream залежностей та SLA для вказаного мікросервісу."
    ),
)
def get_service_dependencies(
    service_name: str = Field(
        ...,
        pattern=r"^[a-z0-9-]+$",
        description="Канонічна назва мікросервісу у форматі kebab-case, наприклад 'billing-api' або 'auth-gateway'.",
    ),
) -> str:
    logger.info("Запит карти залежностей сервісу: %s", service_name)
    # Чесна позначка джерела: DSN із Vault отримано, але в шаблоні дані — демонстраційні.
    mode = "DSN із Vault у RAM · демо-дані" if os.environ.get("DATABASE_URL") else "демо-дані"
    info = DEMO_DEPENDENCIES.get(service_name)
    if not info:
        known = ", ".join(sorted(DEMO_DEPENDENCIES.keys()))
        return f"Сервіс '{service_name}' не знайдено в реєстрі. Доступні сервіси: {known}"

    return (
        f"Сервіс: {service_name} [джерело: {mode}]\n"
        f"- SLA: {info['sla']}\n"
        f"- Upstream (хто викликає / від кого залежить на вході): {', '.join(info['upstream'])}\n"
        f"- Downstream (куди ходить сервіс): {', '.join(info['downstream'])}"
    )


if __name__ == "__main__":
    logger.info("Старт MCP-сервера arch-knowledge-graph у режимі stdio...")
    mcp.run(transport="stdio")
