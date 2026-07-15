from __future__ import annotations

import json
import math
from functools import lru_cache
from typing import Literal, cast

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "testing", "production"]


class Settings(BaseSettings):
    """Typed runtime configuration for MyAgent Community Edition.

    Community startup requires only FastAPI, SQLite, authentication, providers,
    tools, memory, logging and health checks. Optional/enterprise capabilities
    default to disabled and must never be imported or initialized by the runtime
    unless their feature flag is explicitly enabled.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
    )

    environment: Environment = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    app_name: str = Field(default="MyAgent Community Edition", alias="APP_NAME")
    app_version: str = Field(default="3.0.0", alias="APP_VERSION")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, ge=1, le=65_535, alias="API_PORT")
    cors_origins: str = Field(default="http://localhost:8080", alias="CORS_ORIGINS")
    trusted_hosts: str = Field(default="localhost,127.0.0.1,testserver", alias="TRUSTED_HOSTS")
    auto_create_tables: bool = Field(default=True, alias="AUTO_CREATE_TABLES")
    seed_demo_user: bool = Field(default=False, alias="SEED_DEMO_USER")
    enable_legacy_routes: bool = Field(default=False, alias="ENABLE_LEGACY_ROUTES")
    demo_user_email: str = Field(default="demo@myagent.dev", alias="DEMO_USER_EMAIL")
    demo_user_password: str = Field(default="MyAgentDemo123!", alias="DEMO_USER_PASSWORD")

    secret_key: str = Field(default="dev-only-secret-key-32-characters-minimum", alias="SECRET_KEY")
    jwt_secret: str = Field(default="dev-only-jwt-secret-32-characters-minimum", alias="JWT_SECRET")
    access_token_expire_minutes: int = Field(
        default=30, ge=1, le=1_440, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=30, ge=1, le=365, alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    rate_limit_requests: int = Field(default=120, ge=1, le=100_000, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(
        default=60, ge=1, le=86_400, alias="RATE_LIMIT_WINDOW_SECONDS"
    )
    auth_rate_limit_requests: int = Field(
        default=10, ge=1, le=1_000, alias="AUTH_RATE_LIMIT_REQUESTS"
    )
    max_request_body_bytes: int = Field(
        default=3_145_728,
        ge=1_024,
        le=20_971_520,
        alias="MAX_REQUEST_BODY_BYTES",
    )

    database_url: str = Field(default="sqlite+aiosqlite:///./myagent.db", alias="DATABASE_URL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.6", alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_MODEL")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4.1-mini", alias="OPENROUTER_MODEL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-5", alias="ANTHROPIC_MODEL")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    kimi_api_key: str | None = Field(default=None, alias="KIMI_API_KEY")
    kimi_model: str = Field(default="moonshot-v1-8k", alias="KIMI_MODEL")
    kimi_base_url: str = Field(default="https://api.moonshot.cn/v1", alias="KIMI_BASE_URL")
    zai_api_key: str | None = Field(default=None, alias="ZAI_API_KEY")
    zai_model: str = Field(default="glm-4.5-flash", alias="ZAI_MODEL")
    zai_base_url: str = Field(default="https://api.z.ai/api/paas/v4", alias="ZAI_BASE_URL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    default_provider: str = Field(default="mock", alias="DEFAULT_PROVIDER")
    provider_fallbacks: str = Field(default="mock", alias="PROVIDER_FALLBACKS")
    provider_timeout_seconds: float = Field(
        default=60.0, ge=1.0, le=300.0, alias="PROVIDER_TIMEOUT_SECONDS"
    )
    provider_retry_count: int = Field(default=2, ge=0, le=5, alias="PROVIDER_RETRY_COUNT")
    provider_retry_base_seconds: float = Field(
        default=0.25, ge=0.0, le=5.0, alias="PROVIDER_RETRY_BASE_SECONDS"
    )
    provider_trust_environment_proxy: bool = Field(
        default=False, alias="PROVIDER_TRUST_ENVIRONMENT_PROXY"
    )
    provider_pricing_json: str = Field(default="{}", alias="PROVIDER_PRICING_JSON")
    system_prompt: str = Field(
        default="You are MyAgent, a secure, accurate and helpful AI assistant.",
        alias="SYSTEM_PROMPT",
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Community feature flags.
    feature_tools: bool = Field(default=True, alias="FEATURE_TOOLS")
    feature_rag: bool = Field(default=False, alias="FEATURE_RAG")

    # Enterprise extension flags. These are intentionally inert in Community
    # Edition. Disabled flags do not import, initialize or require dependencies.
    feature_redis: bool = Field(default=False, alias="FEATURE_REDIS")
    feature_qdrant: bool = Field(default=False, alias="FEATURE_QDRANT")
    feature_marketplace: bool = Field(default=False, alias="FEATURE_MARKETPLACE")
    feature_analytics: bool = Field(default=False, alias="FEATURE_ANALYTICS")
    feature_workers: bool = Field(default=False, alias="FEATURE_WORKERS")
    feature_queues: bool = Field(default=False, alias="FEATURE_QUEUES")
    feature_background_tasks: bool = Field(default=False, alias="FEATURE_BACKGROUND_TASKS")
    feature_metrics: bool = Field(default=False, alias="FEATURE_METRICS")
    feature_monitoring: bool = Field(default=False, alias="FEATURE_MONITORING")
    feature_clustering: bool = Field(default=False, alias="FEATURE_CLUSTERING")
    feature_enterprise_providers: bool = Field(default=False, alias="FEATURE_ENTERPRISE_PROVIDERS")

    context_message_limit: int = Field(default=30, ge=4, le=200, alias="CONTEXT_MESSAGE_LIMIT")
    context_character_limit: int = Field(
        default=60_000, ge=4_000, le=500_000, alias="CONTEXT_CHARACTER_LIMIT"
    )
    conversation_summary_trigger: int = Field(
        default=40, ge=8, le=500, alias="CONVERSATION_SUMMARY_TRIGGER"
    )
    conversation_summary_max_chars: int = Field(
        default=4_000, ge=500, le=20_000, alias="CONVERSATION_SUMMARY_MAX_CHARS"
    )
    knowledge_result_limit: int = Field(default=4, ge=1, le=12, alias="KNOWLEDGE_RESULT_LIMIT")
    knowledge_excerpt_chars: int = Field(
        default=1_800, ge=300, le=8_000, alias="KNOWLEDGE_EXCERPT_CHARS"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Normalize platform-provided PostgreSQL URLs for SQLAlchemy async use."""
        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [item.strip() for item in self.trusted_hosts.split(",") if item.strip()]

    @property
    def provider_fallback_list(self) -> list[str]:
        return [item.strip() for item in self.provider_fallbacks.split(",") if item.strip()]

    @property
    def provider_pricing(self) -> dict[str, dict[str, float]]:
        raw = json.loads(self.provider_pricing_json)
        return cast(dict[str, dict[str, float]], raw)

    @property
    def requested_enterprise_features(self) -> tuple[str, ...]:
        names = (
            "redis",
            "qdrant",
            "marketplace",
            "analytics",
            "workers",
            "queues",
            "background_tasks",
            "metrics",
            "monitoring",
            "clustering",
            "enterprise_providers",
        )
        return tuple(name for name in names if getattr(self, f"feature_{name}"))

    @property
    def enabled_features(self) -> tuple[str, ...]:
        names = (
            "tools",
            "rag",
            "redis",
            "qdrant",
            "marketplace",
            "analytics",
            "workers",
            "queues",
            "background_tasks",
            "metrics",
            "monitoring",
            "clustering",
            "enterprise_providers",
        )
        return tuple(name for name in names if getattr(self, f"feature_{name}"))

    @model_validator(mode="after")
    def validate_settings(self) -> Settings:
        """Validate invariants and fail closed on unsafe production settings."""
        if not self.api_prefix.startswith("/") or self.api_prefix.endswith("/"):
            raise ValueError("API_PREFIX must start with '/' and must not end with '/'.")
        if not self.cors_origin_list:
            raise ValueError("At least one CORS origin must be configured.")
        if not self.trusted_host_list:
            raise ValueError("At least one trusted host must be configured.")

        if self.requested_enterprise_features:
            requested = ", ".join(self.requested_enterprise_features)
            raise ValueError(
                "Community Edition does not bundle enterprise extensions: " + requested
            )

        try:
            pricing = json.loads(self.provider_pricing_json)
        except json.JSONDecodeError as exc:
            raise ValueError("PROVIDER_PRICING_JSON must be valid JSON.") from exc
        if not isinstance(pricing, dict):
            raise ValueError("PROVIDER_PRICING_JSON must contain a JSON object.")
        for key, rates in pricing.items():
            if not isinstance(key, str) or not isinstance(rates, dict):
                raise ValueError("Provider pricing entries must be objects.")
            if any(
                isinstance(rates.get(name), bool)
                or not isinstance(rates.get(name), int | float)
                or rates[name] < 0
                or not math.isfinite(rates[name])
                for name in ("input", "output")
            ):
                raise ValueError(
                    "Provider pricing requires finite non-negative input/output rates."
                )

        if self.environment != "production":
            return self

        unsafe = {
            "dev-only-secret",
            "dev-only-jwt-secret",
            "dev-only-secret-key-32-characters-minimum",
            "dev-only-jwt-secret-32-characters-minimum",
            "replace_me_with_a_strong_secret",
            "replace_me_with_a_strong_jwt_secret",
        }
        placeholders = ("change_this", "local-", "replace_me", "do_not_use")
        if (
            self.secret_key in unsafe
            or self.jwt_secret in unsafe
            or any(marker in self.secret_key.lower() for marker in placeholders)
            or any(marker in self.jwt_secret.lower() for marker in placeholders)
        ):
            raise ValueError("Production secrets must be provided through secret management.")
        if len(self.secret_key) < 32 or len(self.jwt_secret) < 32:
            raise ValueError("Production secrets must contain at least 32 characters.")
        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError("Production mode must use PostgreSQL through the asyncpg driver.")
        if any(marker in self.database_url for marker in ("myagent_local_password", "change_this")):
            raise ValueError("Production database credentials must be replaced.")
        if "*" in self.cors_origin_list:
            raise ValueError("Wildcard CORS is not allowed in production.")
        if "*" in self.trusted_host_list:
            raise ValueError("Wildcard trusted hosts are not allowed in production.")
        if any(not origin.startswith("https://") for origin in self.cors_origin_list):
            raise ValueError("Production CORS origins must use HTTPS.")
        if self.debug:
            raise ValueError("DEBUG must be false in production.")
        if self.auto_create_tables:
            raise ValueError(
                "AUTO_CREATE_TABLES must be false in production; use Alembic migrations."
            )
        if self.seed_demo_user:
            raise ValueError("SEED_DEMO_USER must be false in production.")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
