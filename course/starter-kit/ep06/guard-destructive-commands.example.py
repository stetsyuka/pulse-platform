#!/usr/bin/env python3
"""PreToolUse-хук безпеки для Claude Code (Starter Kit — Серія 06).

Кладемо в .claude/hooks/guard-destructive-commands.py і підключаємо в .claude/settings.json
з matcher "Read|Edit|Write|Bash". Три лінії оборони:

1. Секрети. Read/Edit/Write чутливого файлу (.env, .env.production, *.pem, *.key, credentials,
   client_secret, ключі SSH) і будь-яка Bash-команда, що згадує такий файл (cat .env, grep … .env,
   source .env, cp ~/.ssh/id_ed25519 …), — exit 2.
   Шаблони .env.example/.sample/.template/.test дозволені.
2. Руйнівні команди. rm -r за межами проєкту, DROP/TRUNCATE, alembic downgrade base,
   git push --force у main/master/prod, terraform destroy — exit 2 з підказкою безпечного шляху.
3. kubectl apply без --dry-run — дописуємо --dry-run=client через updatedInput.
   "allow" повертаємо лише для простої команди без ланцюжків; інакше "ask",
   щоб разом із kubectl не пройшло щось причеплене.

Перевірка вручну:
    echo '{"tool_name":"Bash","tool_input":{"command":"cat .env"}}' | python3 guard.py; echo $?
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import PurePosixPath

SAFE_ENV_SUFFIXES = (".env.example", ".env.sample", ".env.template", ".env.test")

SENSITIVE_PATH_PATTERNS = [
    re.compile(r"(^|/)\.env(\.[\w-]+)?$"),
    re.compile(r"\.(pem|key|p12|pfx|keystore)$", re.IGNORECASE),
    re.compile(r"(^|/)(credentials|client_secret|secrets?)(\.[\w-]+)?$", re.IGNORECASE),
    re.compile(r"(^|/)\.aws/credentials$"),
    re.compile(r"(^|/)\.ssh/id_[\w]+$", re.IGNORECASE),
]

DESTRUCTIVE_BASH_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\b(DROP\s+(TABLE|DATABASE|SCHEMA)|TRUNCATE\s+TABLE)\b", re.IGNORECASE),
        "Пряме видалення таблиць PostgreSQL заборонено. "
        "Згенеруй ревізію міграції Alembic і покажи людині.",
    ),
    (
        re.compile(r"\balembic\b.*\bdowngrade\s+base\b", re.IGNORECASE),
        "Повний відкат бази (alembic downgrade base) заборонено. "
        "Відкочуй на один крок (-1) і лише на тестовій БД.",
    ),
    (
        re.compile(
            r"\bgit\s+push\b.*(--force\b|--force-with-lease\b|\s-f\b).*\b(main|master|prod|production)\b"
        ),
        "Примусовий git push у main/master/prod заборонено. "
        "Зроби звичайний push у робочу гілку і відкрий PR.",
    ),
    (
        re.compile(r"\bterraform\s+destroy\b"),
        "terraform destroy заблоковано. Згенеруй terraform plan -destroy і передай план людині.",
    ),
]

# Розділювачі команд у рядку Bash і символи, що не входять у шлях.
SEGMENTS = re.compile(r"&&|\|\||[;|&\n]")
TOKEN_SPLIT = re.compile(r"[\s;&|<>()`'\"=]+")


def is_sensitive_path(raw: str) -> bool:
    if not raw:
        return False
    norm = PurePosixPath(raw).as_posix()
    if norm.lower().endswith(SAFE_ENV_SUFFIXES):
        return False
    return any(p.search(norm) for p in SENSITIVE_PATH_PATTERNS)


def block(reason: str) -> None:
    """exit 2: інструмент не виконується, а stderr іде моделі як причина відмови."""
    sys.stderr.write(f"[HOOK BLOCKED] {reason}\n")
    sys.exit(2)


def resolve(target: str, cwd: str) -> str:
    target = os.path.expandvars(os.path.expanduser(target))
    return os.path.normpath(target if os.path.isabs(target) else os.path.join(cwd, target))


def rm_outside_project(command: str, cwd: str, project: str) -> str | None:
    """Ціль рекурсивного rm, що лежить поза проєктом (або сам корінь проєкту), інакше None."""
    for seg in SEGMENTS.split(command):
        try:
            words = shlex.split(seg)
        except ValueError:
            words = seg.split()
        while words and words[0] in {"sudo", "command", "env", "nohup", "time"}:
            words = words[1:]
        if not words or os.path.basename(words[0]) != "rm":
            continue
        flags = [w for w in words[1:] if w.startswith("-")]
        recursive = any(
            w in {"--recursive"} or (not w.startswith("--") and re.search(r"[rR]", w))
            for w in flags
        )
        if not recursive:
            continue
        for t in (w for w in words[1:] if not w.startswith("-")):
            path = resolve(t, cwd)
            if path == project or not path.startswith(project + os.sep):
                return t
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = payload.get("tool_name", "")
    args = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    project = os.path.normpath(os.environ.get("CLAUDE_PROJECT_DIR") or cwd)

    # Лінія 1 — секрети у файлових інструментах
    if tool in {"Read", "Edit", "Write"}:
        path = str(args.get("file_path") or "")
        if is_sensitive_path(path):
            block(
                f"Доступ до '{path}' заборонено політикою безпеки. "
                "Перелік змінних візьми з безпечного шаблону .env.example."
            )

    if tool != "Bash":
        sys.exit(0)
    command = str(args.get("command") or "")

    # Лінія 1 — ті самі секрети, але через шелл (cat .env, grep DB .env.local, source .env …)
    for tok in TOKEN_SPLIT.split(command):
        if is_sensitive_path(tok):
            block(
                f"Bash-команда звертається до чутливого файлу '{tok}' — "
                "це витік секретів у контекст. "
                "Перелік змінних візьми з .env.example, значення не потрібні."
            )

    # Лінія 2 — руйнівні команди
    target = rm_outside_project(command, cwd, project)
    if target:
        block(
            f"Рекурсивне видалення '{target}' поза робочою папкою проєкту заборонено. "
            "Видаляй лише всередині проєкту або попроси людину."
        )
    for pattern, message in DESTRUCTIVE_BASH_RULES:
        if pattern.search(command):
            block(message)

    # Лінія 3 — kubectl apply завжди спершу в режимі клієнтської перевірки
    if re.search(r"\bkubectl\s+apply\b", command) and "--dry-run" not in command:
        simple = not re.search(r"[;&|`$<>\n]", command)
        print(
            json.dumps(
                {
                    "systemMessage": "🛡 Хук безпеки додав --dry-run=client до kubectl apply",
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow" if simple else "ask",
                        "permissionDecisionReason": "kubectl apply переведено в --dry-run=client.",
                        "updatedInput": {
                            **args,
                            "command": re.sub(
                                r"\bkubectl\s+apply\b",
                                "kubectl apply --dry-run=client",
                                command,
                                count=1,
                            ),
                        },
                    },
                },
                ensure_ascii=False,
            )
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
