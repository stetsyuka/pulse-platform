#!/usr/bin/env bash
# Stop-хук Claude Code (Starter Kit — Серія 06)
# Призначення: м'яке нагадування наприкінці відповіді про незакомічені або незапушені зміни.
# Особливості:
#   - Не блокує завершення роботи агента (завжди exit 0).
#   - Захищений від нескінченного циклу через перевірку stop_hook_active.
#   - Має антиспам-кеш на 30 хвилин (1800 с) на сесію та репозиторій, щоб не шуміти після кожної репліки.
set -uo pipefail

input=$(cat 2>/dev/null || true)
field() {
  printf '%s' "$input" | python3 -c "import json, sys; val = json.load(sys.stdin).get('$1', ''); print(str(val).lower() if isinstance(val, bool) else val)" 2>/dev/null
}

# Захист від повторного виклику всередині циклу Stop-хука
[ "$(field stop_hook_active)" = "true" ] && exit 0

dir=$(field cwd)
dir="${dir:-${CLAUDE_PROJECT_DIR:-$PWD}}"
roots="${CLAUDE_GIT_SYNC_ROOTS:-$HOME/Projects:$HOME/Work}"

in_root=0
IFS=: read -ra root_list <<<"$roots"
for r in "${root_list[@]}"; do
  case "$dir/" in
    "$r"/?*) in_root=1 ;;
  esac
done
[ "$in_root" = 1 ] || exit 0

top=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || exit 0
repo=${top/#$HOME/\~}

dirty=$(git -C "$top" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if git -C "$top" rev-parse -q --verify '@{u}' >/dev/null 2>&1; then
  ahead=$(git -C "$top" rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)
else
  ahead=$(git -C "$top" rev-list --count HEAD --not --remotes 2>/dev/null || echo 0)
fi

# Якщо робоче дерево чисте й усі коміти на сервері — мовчки виходимо
[ "$dirty" -eq 0 ] && [ "$ahead" -eq 0 ] && exit 0

# Антиспам: показуємо однаковий стан не частіше ніж раз на 30 хвилин у межах сесії
sid=$(field session_id)
state_dir="${TMPDIR:-/tmp}/claude-git-sync"
mkdir -p "$state_dir"
repo_hash=$(printf '%s' "$top" | cksum | cut -d' ' -f1)
state_file="$state_dir/${sid:-nosession}-${repo_hash}"

now=$(date +%s)
key="${dirty}:${ahead}"
if [ -f "$state_file" ]; then
  read -r last_key last_ts <"$state_file" || true
  if [ "${last_key:-}" = "$key" ] && [ $((now - ${last_ts:-0})) -lt 1800 ]; then
    exit 0
  fi
fi
printf '%s %s\n' "$key" "$now" >"$state_file"

hint="перед переходом на іншу робочу машину закомітьте та запуште зміни"
case "$top/" in
  "$HOME"/Work/*)
    hint="перед завершенням закомітьте зміни (git push у ~/Work — після підтвердження)"
    ;;
esac

python3 - "⚠ $repo: незакомічено $dirty, незапушено $ahead — $hint" <<'PY'
import json, sys
print(json.dumps({"systemMessage": sys.argv[1]}, ensure_ascii=False))
PY
