#!/usr/bin/env python3
"""Шукає в міграціях Alembic операції, що блокують живу таблицю PostgreSQL або ламають відкат.

    python3 check_locks.py services/api/migrations/versions/

Правила (детерміновані, без моделі):
  1. create_index на таблиці, яку створила не ця міграція, без postgresql_concurrently=True;
  2. add_column з nullable=False без server_default — впаде на наявних рядках;
  3. create_foreign_key без postgresql_not_valid=True — скан усієї таблиці під локом;
  4. downgrade(), що складається лише з pass.
Вихід: «OK (0 lock hazards found)» і код 0, або список проблем і код 1.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def call_name(node: ast.Call) -> str:
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")


def kw(node: ast.Call, name: str) -> ast.expr | None:
    return next((k.value for k in node.keywords if k.arg == name), None)


def is_true(value: ast.expr | None) -> bool:
    return isinstance(value, ast.Constant) and value.value is True


def check(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    funcs = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}
    problems: list[str] = []
    up = funcs.get("upgrade")
    if up:
        calls = [n for n in ast.walk(up) if isinstance(n, ast.Call)]
        created = {
            c.args[0].value
            for c in calls
            if call_name(c) == "create_table" and c.args and isinstance(c.args[0], ast.Constant)
        }
        for c in calls:
            name, line = call_name(c), f"{path.name}:{c.lineno}"
            if name == "create_index" and len(c.args) > 1 and isinstance(c.args[1], ast.Constant):
                table = c.args[1].value
                if table not in created and not is_true(kw(c, "postgresql_concurrently")):
                    problems.append(
                        f"{line} індекс на живій таблиці {table} без postgresql_concurrently=True"
                    )
            if name == "add_column":
                col = next(
                    (a for a in c.args if isinstance(a, ast.Call) and call_name(a) == "Column"),
                    None,
                )
                nullable = kw(col, "nullable") if col else None
                if (
                    col is not None
                    and isinstance(nullable, ast.Constant)
                    and nullable.value is False
                    and kw(col, "server_default") is None
                ):
                    problems.append(f"{line} NOT NULL колонка без server_default")
            if name == "create_foreign_key" and not is_true(kw(c, "postgresql_not_valid")):
                problems.append(f"{line} зовнішній ключ без postgresql_not_valid=True")
    down = funcs.get("downgrade")
    empty = down is None or all(
        isinstance(s, ast.Pass) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
        for s in down.body
    )
    if empty:
        problems.append(f"{path.name} порожній downgrade() — відкат неможливий")
    return problems


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "services/api/migrations/versions")
    files = sorted(root.glob("*.py")) if root.is_dir() else [root]
    problems = [p for f in files for p in check(f)]
    if not problems:
        print(f"OK (0 lock hazards found) · {len(files)} файлів")
        return 0
    print("\n".join(problems))
    print(f"FAIL ({len(problems)} lock hazards found)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
