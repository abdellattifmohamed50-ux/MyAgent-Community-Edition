import pytest

from core.config.settings import Settings


def test_settings_defaults_are_safe_for_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_PORT", raising=False)
    settings = Settings.model_validate({})
    assert settings.environment in {"development", "testing", "production"}
    assert settings.api_port == 8000


def test_production_rejects_default_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValueError, match="Production secrets"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/myagent",
            CORS_ORIGINS="https://app.example.com",
            SEED_DEMO_USER=False,
        )


def test_production_rejects_sqlite() -> None:
    with pytest.raises(ValueError, match="must use PostgreSQL through the asyncpg driver"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="s" * 40,
            JWT_SECRET="j" * 40,
            DATABASE_URL="sqlite+aiosqlite:///test.db",
            CORS_ORIGINS="https://app.example.com",
            SEED_DEMO_USER=False,
        )


def test_provider_pricing_rejects_non_finite_rates() -> None:
    with pytest.raises(ValueError, match="finite non-negative"):
        Settings(PROVIDER_PRICING_JSON='{"openai":{"input":1e309,"output":1}}')


def test_platform_postgres_url_is_normalized_for_asyncpg() -> None:
    settings = Settings(DATABASE_URL="postgres://user:pass@database.example/myagent")
    assert settings.database_url == "postgresql+asyncpg://user:pass@database.example/myagent"
