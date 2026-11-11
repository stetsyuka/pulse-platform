#!/usr/bin/env bash
# ==============================================================================
# ЕПІЗОД 08 • Starter Kit: обгортка MCP-сервера бази знань + HashiCorp Vault
# Призначення: Динамічне отримання рядка підключення в RAM без запису паролів
#              у .mcp.json, settings.json або історію шелла.
#
# Перевірка зв'язку: ./vault-postgres-mcp-wrapper.example.sh --test
# Робочий запуск:    викликається автоматично клієнтом Claude Code через stdio
# ==============================================================================

set -euo pipefail

TEST_MODE=0
if [[ "${1:-}" == "--test" ]]; then
    TEST_MODE=1
fi

# ВАЖЛИВО: У протоколі MCP stdio потік stdout зарезервований під JSON-RPC!
# Будь-який звичайний echo у stdout зламає рукостискання з Claude Code,
# тому всі діагностичні логи перенаправляємо СУВОРО у stderr (>&2).
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] vault-mcp-wrapper: $*" >&2
}

export VAULT_ADDR="${VAULT_ADDR:-https://vault.internal.example:8200}"
VAULT_SECRET_PATH="${VAULT_SECRET_PATH:-secret/demo-app/database}"
VAULT_SECRET_FIELD="${VAULT_SECRET_FIELD:-connection_string}"

if ! command -v vault >/dev/null 2>&1; then
    log "ERROR: утиліту 'vault' не знайдено в PATH."
    exit 1
fi

# Варіант А (стандартний): пряме читання з HashiCorp Vault через локальний агент/токен.
# Прапорець < /dev/null гарантує, що дочірня команда не перехопить JSON-RPC потік stdin.
#
# Варіант Б (якщо Vault доступний лише через внутрішній бастіон по SSH):
# Обов'язково додавайте прапорець 'ssh -n', інакше ssh вичитає stdin клієнта MCP!
# DB_CONN=$(ssh -n -o ConnectTimeout=5 -o BatchMode=yes deploy-bot@bastion.internal.example \
#     "vault kv get -field=${VAULT_SECRET_FIELD} ${VAULT_SECRET_PATH}" 2>/dev/null)

if ! DB_CONN=$(vault kv get -field="${VAULT_SECRET_FIELD}" "${VAULT_SECRET_PATH}" </dev/null 2>/dev/null); then
    log "ERROR: не вдалося отримати секрет '${VAULT_SECRET_PATH}' з ${VAULT_ADDR}."
    log "Перевірте активну сесію 'vault token lookup' та мережевий доступ."
    exit 1
fi

if [[ -z "${DB_CONN}" ]]; then
    log "ERROR: сховище Vault повернуло порожній рядок підключення."
    exit 1
fi

if [[ ${TEST_MODE} -eq 1 ]]; then
    # Ніколи не виводимо пароль або повний DSN навіть у режимі перевірки!
    log "OK: секрет успішно отримано в RAM зі шляху '${VAULT_SECRET_PATH}' (довжина: ${#DB_CONN} символів)."
    exit 0
fi

# Запускаємо власний FastMCP-сервер бази знань (архівований npm-пакет server-postgres
# не підтримується і не має гарантій безпеки). Рядок підключення — лише у змінній оточення.
# exec заміщує процес bash самим сервером: той самий PID, сигнали завершення доходять напряму.
export DATABASE_URL="${DB_CONN}"
KG_SERVER="${KG_SERVER:-$(dirname "$0")/mcp-knowledge-server.example.py}"
exec uv run --quiet --python 3.12 --with "mcp==1.30.0" python "${KG_SERVER}"
