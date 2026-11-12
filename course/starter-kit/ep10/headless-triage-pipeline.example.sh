#!/usr/bin/env bash
# headless-triage-pipeline.example.sh
# Детермінований Unix-пайплайн тріажу збоїв збірки/тестів через Claude Code (звірено з v2.1.322)
# Starter Kit курсу «Архітектор проєктів з Claude Code» (InferenceLab, 2026)
#
# Приклад запуску:
#   (ключ — з .env або Vault, не в історії шелла: set -a; . ./.env; set +a)
#   ./headless-triage-pipeline.example.sh ./logs/pytest-failure.log
#   pytest -q --tb=short 2>&1 | ./headless-triage-pipeline.example.sh -

set -euo pipefail

usage() {
  cat <<'EOF'
Використання:
  headless-triage-pipeline.example.sh <шлях-до-лог-файла | ->

Опис:
  Читає останні 250 рядків логу помилки з файла або stdin (-), запускає Claude Code
  у стерильному режимі (--bare --permission-prompts none) із примусовою валідацією
  JSON Schema, друкує структурований діагноз і повертає код виходу:
    0 — неблокуюче попередження (flaky / оточення)
    2 — виявлено блокуючий інженерний дефект у коді (blocking == true)
    1 — помилка конфігурації або перевищення бюджету
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "[ПОМИЛКА] У стерильному режимі --bare обов'язкова змінна ANTHROPIC_API_KEY." >&2
  exit 1
fi

for cmd in claude jq tail; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ПОМИЛКА] Не знайдено обов'язкову утиліту: $cmd" >&2
    exit 1
  fi
done

INPUT_SOURCE="$1"
MAX_BUDGET="${CLAUDE_TRIAGE_BUDGET_USD:-0.40}"
MAX_TURNS="${CLAUDE_TRIAGE_MAX_TURNS:-5}"
PRIMARY_MODEL="${CLAUDE_TRIAGE_MODEL:-sonnet}"
FALLBACK_MODEL="${CLAUDE_TRIAGE_FALLBACK:-haiku}"

# Сувора JSON-схема виходу: клієнт перевіряє об'єкт і кладе його в .structured_output
TRIAGE_SCHEMA='{
  "type": "object",
  "properties": {
    "blocking": { "type": "boolean" },
    "category": {
      "type": "string",
      "enum": ["code_bug", "type_error", "migration_mismatch", "infra_flaky", "dependency_issue"]
    },
    "severity": { "type": "integer", "minimum": 1, "maximum": 5 },
    "suspect_file": { "type": "string" },
    "root_cause": { "type": "string" },
    "proposed_fix": { "type": "string" }
  },
  "required": ["blocking", "category", "severity", "suspect_file", "root_cause", "proposed_fix"]
}'

TMP_LOG="$(mktemp)"
TMP_OUT="$(mktemp)"
trap 'rm -f "$TMP_LOG" "$TMP_OUT"' EXIT

if [[ "$INPUT_SOURCE" == "-" ]]; then
  tail -n 250 > "$TMP_LOG"
else
  if [[ ! -f "$INPUT_SOURCE" ]]; then
    echo "[ПОМИЛКА] Лог-файл не знайдено: $INPUT_SOURCE" >&2
    exit 1
  fi
  tail -n 250 "$INPUT_SOURCE" > "$TMP_LOG"
fi

SYS_PROMPT_ARGS=()
FALLBACK_ARGS=()
# Резервна модель має відрізнятися від основної
[[ "$FALLBACK_MODEL" != "$PRIMARY_MODEL" ]] && FALLBACK_ARGS=(--fallback-model "$FALLBACK_MODEL")
if [[ -f "CLAUDE.md" ]]; then
  SYS_PROMPT_ARGS=(--append-system-prompt-file "CLAUDE.md")
fi

# Запуск стерильного програмованого рушія Claude Code
cat "$TMP_LOG" | claude -p \
  "Проаналізуй лог падіння збірки або тестів. Звір стек-трейс із поточними файлами проєкту через Read/Grep і поверни точну першопричину українською мовою за заданою схемою." \
  --bare \
  "${SYS_PROMPT_ARGS[@]}" \
  --permission-prompts none \
  --tools "Read,Grep,Glob" \
  --allowedTools "Read,Grep,Glob" \
  --model "$PRIMARY_MODEL" \
  "${FALLBACK_ARGS[@]}" \
  --output-format json \
  --json-schema "$TRIAGE_SCHEMA" \
  --max-turns "$MAX_TURNS" \
  --max-budget-usd "$MAX_BUDGET" \
  --no-session-persistence > "$TMP_OUT"

COST_USD="$(jq -r '.total_cost_usd // 0' "$TMP_OUT")"
IS_BLOCKING="$(jq -r '.structured_output.blocking' "$TMP_OUT")"

echo "============================================================"
echo " ДІАГНОЗ HEADLESS ТРІАЖУ CLAUDE CODE (cost: \$${COST_USD})"
echo "============================================================"
jq -r '.structured_output |
  "Категорія:     \(.category) (рівень критичності: \(.severity)/5)\n" +
  "Підозрюваний:  \(.suspect_file)\n" +
  "Першопричина:  \(.root_cause)\n" +
  "План фіксу:    \(.proposed_fix)\n" +
  "Блокує реліз:  \(.blocking)"
' "$TMP_OUT"
echo "============================================================"

if [[ "$IS_BLOCKING" == "true" ]]; then
  exit 2
fi

exit 0
