# Еталонний кресленик Капстоун-проєкту Архітектора (Серії 01–10, v2.1.322)

> Фінальний архітектурний паспорт зі **Starter Kit курсу «Архітектор проєктів з Claude Code» (`InferenceLab`, листопад 2026)**.
> Використовуйте цей кресленик як шаблон для розгортання власної платформи з нуля або для переведення існуючого командного монорепозиторію на повний дев'ятишаровий стандарт **AI-Native SDLC**.

---

## 1. Еталонна структура монорепозиторію (`pulseops-platform/`)

```text
pulseops-platform/
├── AGENTS.md                                # Крос-агентний паспорт (сумісність і резерв v2.1.277+)
├── CLAUDE.md                                # Лаконічне ядро інструкцій (≤120 рядків: стек, make check, інваріанти)
├── HANDOFF.md                               # Живий міст передачі стану між сесіями та субагентами
├── Makefile                                 # Єдина 4-шарова команда верифікації: `make check`
├── docs/
│   ├── specs/                               # Spec-driven розробка: intent.md -> design-spec.md -> tasks.md
│   └── adr/                                 # Архітектурні рішення (Architecture Decision Records)
├── .claude/
│   ├── settings.json                        # Командна політика: Auto Mode, Sandbox, blockOutsideWorkingDirectories, Hooks
│   ├── settings.local.json                  # Локальні перевизначення (у .gitignore!)
│   ├── rules/                               # Модульні правила з glob-фільтрами (нульовий податок поза папкою)
│   │   ├── api-fastapi.md                   # globs: ["services/api/**"]
│   │   ├── web-nextjs.md                    # globs: ["apps/web/**"]
│   │   └── db-migrations.md                 # globs: ["services/api/migrations/**"]
│   ├── hooks/                               # Детерміновані запобіжники (exit 0 / exit 2)
│   │   ├── block-secrets-and-blind-add.sh   # PreToolUse: захист .env/*.pem та табу на `git add .`
│   │   ├── auto-format-on-write.sh          # PostToolUse: миттєвий ruff / biome format
│   │   └── git-sync-and-notify.sh           # SessionStart / Stop: перевірка гілки та десктоп-алерт
│   ├── skills/                              # Ліниві командні рецепти (перевірені через `claude plugin eval`)
│   │   ├── new-endpoint/SKILL.md            # Генерація FastAPI маршруту + схеми + інтеграційного тесту
│   │   └── db-migration/SKILL.md            # Безпечна міграція Alembic із перевіркою зворотного відкату
│   ├── agents/                              # Спеціалізовані ізольовані субагенти
│   │   ├── security-auditor.md              # Read-only аудит OWASP, токенів і прав доступу
│   │   └── sql-tuning-reviewer.md           # Оптимізація індексів та пошук N+1 запитів
│   └── mods/
│       └── context-bar/                     # Кастомний TypeScript Claude Mod живого бюджету 1M контексту
├── services/
│   └── api/                                 # Python 3.13 + FastAPI + SQLAlchemy + Pytest
├── apps/
│   └── web/                                 # TypeScript + Next.js + Vitest + Biome
├── infra/
│   ├── mcp-postgres-vault/                  # Read-only PostgreSQL MCP із короткоживучими секретами з Vault
│   └── runner/                              # Docker Compose для приватного `claude self-hosted-runner`
└── .github/
    ├── PULL_REQUEST_TEMPLATE.md             # Чекліст верифікації PR (зі Starter Kit ep05)
    └── workflows/
        └── claude-review-hardened.yml       # Броньований headless-пайплайн рев'ю PR (зі Starter Kit ep10)
```

---

## 2. Дев'ять архітектурних шарів платформи (Матриця всіх 10 серій)

| Шар | Серії | Механізми Claude Code `v2.1.322` | Критерій приймання у вашому проєкті |
|---|---|---|---|
| **1. Середовище і Контекст** | `01–02` | Нативна Linux/macOS ФС, `AGENTS.md`, `CLAUDE.md`, `.claude/rules/`, `chezmoi`, `/doctor prompt-audit` | `git status` виконується за `<0.15с`; `CLAUDE.md` не містить «води» і проходить `prompt-audit` без зауважень |
| **2. Безпечний Периметр** | `03` | Штатний `Auto Mode` (`/auto-mode-setup`), `Sandbox`, `blockReads/WritesOutsideWorkingDirectories`, `includeIf` | Жодного `--dangerously-skip-permissions` у щоденній роботі; спроба запису поза проєктом блокується |
| **3. Декомпозиція** | `04` | `intent.md`, `Plan Mode` (`Shift+Tab`), гібрид `opusplan`, `/subtask`, фокусний `/compact`, `HANDOFF.md` | Складні фічі мають затверджений план перед першою правкою коду; `HANDOFF.md` дозволяє відновити роботу за 10с |
| **4. Верифікація і TDD** | `05` | `claude -w` (`git worktree`), Agentic TDD (`Red → Green → Refactor`), 4-шаровий `make check`, `/simplify`, `/code-review ultra` | Тести пишуться до коду; на зеленій фазі `git diff tests/` порожній; `make check` закриває типи, лінтер, тести й smoke-test |
| **5. Детерміновані Hooks** | `06` | `PreToolUse` (`exit 2`), `PostToolUse`, `SessionStart`, `Stop`, JSON у `stdin`, умовне поле `if` | Агент фізично не може прочитати `.env`/`*.key` або зробити `git add .` навіть при прямій інструкції у промпті |
| **6. Скіли, Плагіни і Моди** | `07` | `SKILL.md` (`references/`), `/skill-doctor`, `claude plugin eval`, TypeScript **Claude Mod** (`context-bar`) | Мінімум 2 типові задачі проєкту оформлені у скіли з оцінкою якості через `plugin eval`; мод відображає стан контексту |
| **7. Зовнішні протоколи MCP** | `08` | Ліниве завантаження MCP, `claude mcp login --no-browser`, `claude --chrome`, власний DB MCP + HashiCorp Vault | Жодного статичного прод-пароля у конфігах MCP; стартовий податок схем MCP не перевищує 5–8K токенів |
| **8. Оркестрація роїв** | `09` | `.claude/agents/*.md`, `claude --bg`, панель `claude agents`, `/goal`, динамічні рої `/effort ultracode` | Важкий аудит винесено у субагентів із чистим контекстом; масові крос-модульні зміни виконуються через `ultracode` |
| **9. Конвеєр 24/7** | `10` | `claude -p --bare --json-schema`, `/loop`, `/schedule`, `Remote Control (--spawn=worktree)`, броньований CI/CD, `self-hosted-runner` | Пайплайн PR відповідає 5 правилам безпеки; регулярні перевірки працюють автономно за розкладом `/schedule` |

---

## 3. Ізольований контур для альтернативних моделей (щоб ANTHROPIC_BASE_URL не витік в основний профіль)

Ніколи не змішуйте альтернативні роутери (`LiteLLM`, `OpenRouter`, локальний `vLLM`) із вашим головним робочим профілем `~/.claude`:

```bash
# 1. Створіть окрему фізично ізольовану директорію конфігурації:
mkdir -p ~/.claude-alt && chmod 700 ~/.claude-alt

# 2. Запишіть ізольований конфіг ~/.claude-alt/settings.json (БЕЗ /v1 у кінці BASE_URL!):
cat <<'EOF' > ~/.claude-alt/settings.json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8000",
    "ANTHROPIC_AUTH_TOKEN": "<YOUR_LOCAL_OR_ROUTER_TOKEN>",
    "ANTHROPIC_API_KEY": "",
    "ANTHROPIC_MODEL": "<PROVIDER_MODEL_ID>"
  },
  "permissions": {
    "blockReadsOutsideWorkingDirectories": true,
    "blockWritesOutsideWorkingDirectories": true
  }
}
EOF

# 3. Додайте явну команду у ~/.zshrc (основна команда `claude` залишається на 100% нативною!):
claude-local() {
  CLAUDE_CONFIG_DIR="$HOME/.claude-alt" claude "$@"
}
```

---

## 4. Шаблон приватного раннера `claude self-hosted-runner` (`infra/runner/compose.yml`)

Для виконання хмарних сесій (`claude --cloud --environment <ccpool_id>`), мобільних задач та `/schedule` усередині вашого VPC або домашнього сервера:

```yaml
services:
  claude-runner:
    image: ghcr.io/example-org/claude-code-runner:latest
    container_name: pulseops-self-hosted-runner
    restart: unless-stopped
    user: "10001:10001"
    read_only: false
    secrets:
      - runner_pool_secret
    tmpfs:
      - /tmp:size=2G
    volumes:
      - runner_workspace:/workspace
    command:
      - claude
      - self-hosted-runner
      - --environment-secret-file=/run/secrets/runner_pool_secret
      - --base-dir=/workspace
      - --capacity=4
      - --drain-wait-sec=60
      - --remove-session-state
      - --confine-repo-settings=enforce
      - --kill-session-after-min=120
      - --health-port=8080
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:8080/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

secrets:
  runner_pool_secret:
    file: ./secrets/ccpool_registration.secret

volumes:
  runner_workspace:
```

---

## 5. Фінальний чекліст випуску вашого Капстоун-проєкту

- [ ] Репозиторій проходить `/doctor` та `/doctor prompt-audit` без критичних попереджень.
- [ ] Команда `make check` виконує всі 4 шари верифікації за один виклик із коротким інформативним виводом.
- [ ] Спроба виконати `cat .env` або `git add .` усередині сесії гарантовано перехоплюється хуком із кодом виходу `2`.
- [ ] Скіли проєкту проходять автоматичну перевірку `claude plugin eval`.
- [ ] Броньований CI-воркфлоу використовує `--bare`, `--permission-prompts none`, `--json-schema`, `--max-budget-usd` і розділяє права `contents: read` та `pull-requests: write` по різних job-кроках.
- [ ] Налаштовано щонайменше одну регулярну задачу `/schedule` (наприклад, щотижневий аудит залежностей та технічного боргу) зі створенням звіту для рев'ю людиною.
