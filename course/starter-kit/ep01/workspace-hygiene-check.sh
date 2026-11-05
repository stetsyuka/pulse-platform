#!/usr/bin/env bash
# Перевірка гігієни середовища перед роботою з Claude Code (macOS / Linux / WSL)
set -euo pipefail

echo "=== 1. Поточна директорія ==="
pwd

if [[ "$PWD" == /mnt/* ]]; then
  echo "⚠️  УВАГА: Ви знаходитесь на змонтованому диску Windows ($PWD)!"
  echo "   Перенесіть репозиторій усередину нативної ФС Linux у WSL (~/Projects/...), щоб прискорити git та Claude Code до ×50 разів."
fi

if [[ "$PWD" == *"Google Drive"* || "$PWD" == *"CloudStorage"* || "$PWD" == *"Dropbox"* || "$PWD" == *"Mobile Documents"* ]]; then
  echo "⚠️  УВАГА: Репозиторій лежить у хмарній папці синхронізації! Перенесіть його у локальну директорію ~/Projects/."
fi

echo ""
echo "=== 2. Швидкість git status ==="
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  time git status -sb
else
  echo "Поточна папка не є Git-репозиторієм."
fi

echo ""
echo "=== 3. Версія Claude Code ==="
if command -v claude >/dev/null 2>&1; then
  claude --version
else
  echo "Claude Code ще не встановлено. Встановіть через: curl -fsSL https://claude.ai/install.sh | bash"
fi

