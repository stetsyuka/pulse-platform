#!/usr/bin/env bash
# SessionStart-хук Claude Code (Starter Kit — Серія 06)
# Призначення: безпечна мультимашинна синхронізація Git-репозиторіїв на старті сесії.
# Що робить:
#   1. Пропускає повторний запуск після стиснення контексту (source == "compact").
#   2. Перевіряє, що робоча директорія належить до дозволених контурів (~/Projects або ~/Work).
#   3. Виконує швидкий git fetch з таймаутом (не зависає без мережі чи корпоративного VPN).
#   4. Робить автоматичний fast-forward (git merge --ff-only) ТІЛЬКИ якщо дерево чисте й немає розбіжностей.
#   5. Повертає стислий статус користувачу (systemMessage) та інструкцію агенту (additionalContext).
set -uo pipefail

input=$(cat 2>/dev/null || true)
field() {
  printf '%s' "$input" | python3 -c "import json, sys; print(json.load(sys.stdin).get('$1', ''))" 2>/dev/null
}

# Після /compact стан репозиторію вже присутній у контексті сесії
[ "$(field source)" = "compact" ] && exit 0

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

# Обмежуємо час очікування SSH/мережі, щоб не блокувати старт сесії без VPN
export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5"
fetch_ok=1
python3 -c '
import subprocess, sys
try:
    subprocess.run(sys.argv[1:], timeout=15, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception:
    sys.exit(1)
' git -C "$top" fetch --quiet --prune || fetch_ok=0

branch=$(git -C "$top" symbolic-ref --short -q HEAD) || branch=""
dirty=$(git -C "$top" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
upstream=$(git -C "$top" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null) || upstream=""

ahead=0
behind=0
if [ -n "$upstream" ]; then
  read -r ahead behind < <(git -C "$top" rev-list --left-right --count 'HEAD...@{u}' 2>/dev/null) || true
fi
ahead=${ahead:-0}
behind=${behind:-0}

pulled=0
if [ -n "$upstream" ] && [ "$behind" -gt 0 ] && [ "$ahead" -eq 0 ] && [ "$dirty" -eq 0 ]; then
  if git -C "$top" merge --ff-only --quiet '@{u}' >/dev/null 2>&1; then
    pulled=$behind
    behind=0
  fi
fi

notes=()
[ "$fetch_ok" = 0 ] && notes+=("fetch не вдався (перевірте мережу або VPN) — стан віддаленого сервера може бути застарілим")
[ "$pulled" -gt 0 ] && notes+=("підтягнуто з $upstream нових комітів: $pulled (fast-forward)")
[ -z "$branch" ] && notes+=("detached HEAD")
[ -n "$branch" ] && [ -z "$upstream" ] && notes+=("гілка $branch ще не має upstream")

if [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ]; then
  notes+=("гілка розійшлася з $upstream (локально +$ahead, на сервері +$behind) — НЕ зливати самостійно, запитати користувача")
elif [ "$behind" -gt 0 ]; then
  notes+=("на сервері нових комітів: $behind, але є локальні зміни — НЕ підтягнуто, узгодити з користувачем")
elif [ "$ahead" -gt 0 ]; then
  notes+=("незапушених локальних комітів: $ahead")
fi

[ "$dirty" -gt 0 ] && notes+=("незакомічених змін у робочому дереві: $dirty — уточнити у користувача перед правками")

if [ ${#notes[@]} -eq 0 ]; then
  user_msg="✓ $repo ($branch): синхронізовано з $upstream"
  ctx_msg="git-sync: $repo, гілка $branch — актуальна з $upstream, робоче дерево чисте."
else
  joined=$(printf '%s; ' "${notes[@]}")
  joined=${joined%; }
  mark="⚠"
  [ "$pulled" -gt 0 ] && [ ${#notes[@]} -eq 1 ] && mark="⇣"
  user_msg="$mark $repo (${branch:-detached}): $joined"
  ctx_msg="git-sync: $repo, гілка ${branch:-detached HEAD} — $joined."
fi

case "$top/" in
  "$HOME"/Work/*)
    ctx_msg="$ctx_msg Це робочий контур ~/Work: локальні коміти дозволені, але перед git push обов'язково запитай підтвердження користувача."
    ;;
esac

python3 - "$user_msg" "$ctx_msg" <<'PY'
import json, sys
print(json.dumps({
    "systemMessage": sys.argv[1],
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": sys.argv[2]
    }
}, ensure_ascii=False))
PY
