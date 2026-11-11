#!/usr/bin/env bash
# Stop-хук Claude Code (Starter Kit — Серія 06): агент не закінчить роботу з червоним make check.
#
# Обіцянка з Серії 05: «зробимо перевірку невідворотною». На кожному Stop, якщо в робочому
# дереві є зміни, запускаємо make check. Червоно — exit 2: Claude отримує хвіст виводу в stderr
# і продовжує виправляти. Захист від нескінченного циклу: не більше трьох спроб поспіль на
# сесію, далі хук здається і просить людину подивитися самій.
#
# Підключення (.claude/settings.json проєкту):
#   "Stop": [{ "hooks": [{ "type": "command",
#       "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/stop-make-check.sh\"", "timeout": 300 }] }]
set -uo pipefail

input=$(cat)
field() { printf '%s' "$input" | python3 -c "import json,sys; v=json.load(sys.stdin).get('$1',''); print(str(v).lower() if isinstance(v,bool) else v)" 2>/dev/null; }

cd "${CLAUDE_PROJECT_DIR:-$(field cwd)}" 2>/dev/null || exit 0
[ -f Makefile ] || exit 0

# Агент нічого не змінював — перевіряти нічого (відповідь на питання, огляд коду тощо)
[ -z "$(git status --porcelain --untracked-files=normal 2>/dev/null)" ] && exit 0

tries_file="${TMPDIR:-/tmp}/claude-stop-check-$(field session_id)"
if [ "$(field stop_hook_active)" = "true" ]; then
  tries=$(( $(cat "$tries_file" 2>/dev/null || echo 0) + 1 ))
else
  tries=1
fi

if out=$(make check 2>&1); then
  rm -f "$tries_file"
  exit 0
fi

if [ "$tries" -gt 3 ]; then
  rm -f "$tries_file"
  printf '{"systemMessage": "make check досі червоний після трьох спроб — подивіться самі"}\n'
  exit 0
fi
echo "$tries" >"$tries_file"

{
  echo "make check червоний (спроба $tries з 3). Не закінчуй роботу: виправ код, а не тести, і запусти make check ще раз."
  printf '%s\n' "$out" | tail -n 40
} >&2
exit 2
