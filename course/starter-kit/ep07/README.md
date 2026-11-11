# Starter Kit — Серія 07: Skills, Plugins і Claude Mods

| Що | Куди класти | Перевірка |
|---|---|---|
| `db-migration/` — навичка: `SKILL.md`, `scripts/check_locks.py`, `references/`, `evals/` | `.claude/skills/db-migration/` у проєкті | `/reload-skills`, `/skill-doctor` |
| `db-migration/evals/index-on-live-table/case.yaml` — регресійний тест навички | лежить у навичці | `claude plugin eval .claude/skills/db-migration --model haiku --max-cost-usd 1.50 --no-publish --allow-tools Write Edit` |
| `context-bar/` — Claude Mod: смуга контексту над полем вводу, `/context-bar` | будь-яка тека | `claude plugin test ./context-bar`, `claude --plugin-dir ./context-bar` |

Те саме — у pulse-platform, гілка `ep07-end` (навичка вже в `.claude/skills/`).

Домашнє завдання червоного рівня: додати в легенду `context-bar` вартість сесії (`$.session.usage()` → `cost`)
і світлофор Context Rot (зелений до 25 %, жовтий до 50 %, червоний вище), з тестом у `hooks/register.test.ts`.
