import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    billing_api_url: str
    billing_api_token: str
    webhook_endpoint_url: str
    webhook_signing_secret: str


def get_settings() -> Settings:
    # Секрети — лише зі змінних оточення (.env у .gitignore), ніколи не в коді.
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./pulse.db"),
        billing_api_url=os.environ.get("BILLING_API_URL", "https://billing.example.test"),
        billing_api_token=os.environ.get("BILLING_API_TOKEN", ""),
        webhook_endpoint_url=os.environ.get(
            "WEBHOOK_ENDPOINT_URL", "https://partner.example.test/hooks"
        ),
        webhook_signing_secret=os.environ.get("WEBHOOK_SIGNING_SECRET", ""),
    )
