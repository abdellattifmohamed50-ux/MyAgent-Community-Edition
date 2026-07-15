from __future__ import annotations

from dataclasses import dataclass

import httpx

from agents.base import Agent
from agents.conversational_agent import ConversationalAgent
from core.config.settings import Settings
from core.database.session import DatabaseManager
from core.memory.manager import ConversationMemory, MemoryPolicy
from core.providers.client import LazyAsyncClient
from core.providers.costs import UsageCostEstimator
from core.providers.http_providers import (
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    OpenAIResponsesProvider,
)
from core.providers.mock import MockProvider
from core.providers.registry import ProviderRegistry
from core.providers.router import ProviderRouter
from core.security.password import hash_password
from core.tools.builtins import CalculatorTool, DateTimeTool, TextStatsTool
from core.tools.registry import ToolRegistry
from models.entities import User
from repositories.sql_repositories import UserRepository


@dataclass
class ApplicationContainer:
    settings: Settings
    database: DatabaseManager
    http_client: LazyAsyncClient
    providers: ProviderRegistry
    agent: Agent
    memory: ConversationMemory
    costs: UsageCostEstimator
    tools: ToolRegistry

    @classmethod
    def build(cls, settings: Settings) -> ApplicationContainer:
        timeout = httpx.Timeout(
            settings.provider_timeout_seconds,
            connect=min(settings.provider_timeout_seconds, 10.0),
        )
        http_client = LazyAsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            headers={"User-Agent": f"MyAgent-Engine/{settings.app_version}"},
            trust_env=settings.provider_trust_environment_proxy,
        )
        providers = ProviderRegistry()
        providers.register(MockProvider())
        providers.register(
            OpenAIResponsesProvider(
                settings.openai_api_key,
                settings.openai_model,
                settings.openai_base_url,
                settings.provider_timeout_seconds,
                http_client,
            )
        )
        providers.register(
            GeminiProvider(
                settings.gemini_api_key,
                settings.gemini_model,
                settings.provider_timeout_seconds,
                http_client,
            )
        )
        providers.register(
            OpenAICompatibleProvider(
                name="openrouter",
                api_key=settings.openrouter_api_key,
                model=settings.openrouter_model,
                base_url="https://openrouter.ai/api/v1",
                timeout=settings.provider_timeout_seconds,
                client=http_client,
                extra_headers={"X-Title": settings.app_name},
                include_stream_usage=True,
            )
        )
        providers.register(
            AnthropicProvider(
                settings.anthropic_api_key,
                settings.anthropic_model,
                settings.provider_timeout_seconds,
                http_client,
            )
        )
        compatible = [
            (
                "deepseek",
                settings.deepseek_api_key,
                settings.deepseek_model,
                "https://api.deepseek.com",
            ),
            ("kimi", settings.kimi_api_key, settings.kimi_model, settings.kimi_base_url),
            ("zai", settings.zai_api_key, settings.zai_model, settings.zai_base_url),
        ]
        for name, api_key, model, base_url in compatible:
            providers.register(
                OpenAICompatibleProvider(
                    name=name,
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    timeout=settings.provider_timeout_seconds,
                    client=http_client,
                )
            )
        providers.register(
            OllamaProvider(
                settings.ollama_base_url,
                settings.ollama_model,
                settings.provider_timeout_seconds,
                http_client,
            )
        )
        for provider_name in [settings.default_provider, *settings.provider_fallback_list]:
            providers.get(provider_name)
        tools = ToolRegistry()
        if settings.feature_tools:
            tools.register(CalculatorTool())
            tools.register(DateTimeTool())
            tools.register(TextStatsTool())
        router = ProviderRouter(
            providers,
            default_provider=settings.default_provider,
            retry_count=settings.provider_retry_count,
            fallback_names=settings.provider_fallback_list,
            retry_base_seconds=settings.provider_retry_base_seconds,
        )
        return cls(
            settings=settings,
            database=DatabaseManager(settings.database_url, echo=settings.debug),
            http_client=http_client,
            providers=providers,
            agent=ConversationalAgent(router),
            memory=ConversationMemory(
                MemoryPolicy(
                    recent_message_limit=settings.context_message_limit,
                    character_limit=settings.context_character_limit,
                    summary_trigger=settings.conversation_summary_trigger,
                    summary_max_chars=settings.conversation_summary_max_chars,
                )
            ),
            costs=UsageCostEstimator(settings.provider_pricing),
            tools=tools,
        )

    async def start(self) -> None:
        if self.settings.auto_create_tables:
            await self.database.create_schema()
        if self.settings.seed_demo_user and self.settings.environment != "production":
            await self._seed_demo_user()

    async def close(self) -> None:
        await self.http_client.aclose()
        await self.database.close()

    async def _seed_demo_user(self) -> None:
        async with self.database.session_factory() as session:
            repository = UserRepository(session)
            if await repository.get_by_email(self.settings.demo_user_email) is not None:
                return
            user = User(
                id="usr_demo",
                email=self.settings.demo_user_email,
                display_name="MyAgent Demo",
                password_hash=hash_password(self.settings.demo_user_password),
                role="admin",
                is_active=True,
            )
            await repository.add(user)
            await session.commit()
