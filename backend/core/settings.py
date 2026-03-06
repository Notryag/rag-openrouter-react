import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    name: str
    api_key_env: str
    base_url_env: str
    model_env: str
    embedding_env: str
    default_base_url: str
    default_model: str
    default_embedding_model: str


PROVIDER_PRESETS = {
    "dashscope": ProviderPreset(
        name="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        base_url_env="DASHSCOPE_BASE_URL",
        model_env="DASHSCOPE_MODEL",
        embedding_env="DASHSCOPE_EMBEDDING_MODEL",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
        default_embedding_model="text-embedding-v4",
    ),
    "gemini": ProviderPreset(
        name="gemini",
        api_key_env="GEMINI_API_KEY",
        base_url_env="GEMINI_BASE_URL",
        model_env="GEMINI_MODEL",
        embedding_env="GEMINI_EMBEDDING_MODEL",
        default_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-2.5-flash",
        default_embedding_model="gemini-embedding-001",
    ),
    "openrouter": ProviderPreset(
        name="openrouter",
        api_key_env="OPENROUTER_API_KEY",
        base_url_env="OPENROUTER_BASE_URL",
        model_env="OPENROUTER_MODEL",
        embedding_env="OPENROUTER_EMBEDDING_MODEL",
        default_base_url="https://openrouter.ai/api/v1",
        default_model="openai/gpt-4o-mini",
        default_embedding_model="openai/text-embedding-3-small",
    ),
}
DEFAULT_PROVIDER = "dashscope"


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _first_non_empty(*values: str, default: str) -> str:
    for value in values:
        if value:
            return value
    return default


def _is_truthy(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def _resolve_provider() -> str:
    explicit_provider = _env("AI_PROVIDER") or _env("LLM_PROVIDER")
    if explicit_provider:
        normalized = explicit_provider.lower()
        if normalized not in PROVIDER_PRESETS:
            supported = ", ".join(sorted(PROVIDER_PRESETS))
            raise ValueError(f"Unsupported AI_PROVIDER '{explicit_provider}'. Supported values: {supported}")
        return normalized

    for provider_name in ("dashscope", "gemini", "openrouter"):
        preset = PROVIDER_PRESETS[provider_name]
        if any(
            _env(name)
            for name in (
                preset.api_key_env,
                preset.base_url_env,
                preset.model_env,
                preset.embedding_env,
            )
        ):
            return provider_name

    return DEFAULT_PROVIDER


@dataclass(frozen=True)
class AppSettings:
    provider: str
    api_key: str
    base_url: str
    model: str
    embedding_model: str
    app_name: str | None
    app_url: str | None
    rerank_enabled: bool
    rerank_fetch_k: int
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    log_level: str

    @classmethod
    def from_env(cls) -> "AppSettings":
        provider = _resolve_provider()
        preset = PROVIDER_PRESETS[provider]

        rerank_enabled = _is_truthy(
            _first_non_empty(
                _env("RAG_RERANK_ENABLED"),
                _env("OPENROUTER_RERANK_ENABLED"),
                default="false",
            )
        )
        rerank_fetch_k = int(
            _first_non_empty(
                _env("RAG_RERANK_FETCH_K"),
                _env("OPENROUTER_RERANK_FETCH_K"),
                default="8",
            )
        )

        return cls(
            provider=provider,
            api_key=_first_non_empty(_env("AI_API_KEY"), _env(preset.api_key_env), default=""),
            base_url=_first_non_empty(
                _env("AI_BASE_URL"),
                _env(preset.base_url_env),
                default=preset.default_base_url,
            ),
            model=_first_non_empty(
                _env("AI_MODEL"),
                _env(preset.model_env),
                default=preset.default_model,
            ),
            embedding_model=_first_non_empty(
                _env("AI_EMBEDDING_MODEL"),
                _env(preset.embedding_env),
                default=preset.default_embedding_model,
            ),
            app_name=_first_non_empty(
                _env("AI_APP_NAME"),
                _env("OPENROUTER_APP_NAME"),
                default="",
            )
            or None,
            app_url=_first_non_empty(
                _env("AI_APP_URL"),
                _env("OPENROUTER_APP_URL"),
                default="",
            )
            or None,
            rerank_enabled=rerank_enabled,
            rerank_fetch_k=rerank_fetch_k,
            jwt_secret=_first_non_empty(_env("JWT_SECRET"), default="change-me-in-production"),
            jwt_algorithm="HS256",
            access_token_expire_minutes=int(
                _first_non_empty(_env("ACCESS_TOKEN_EXPIRE_MINUTES"), default="720")
            ),
            log_level=_first_non_empty(_env("LOG_LEVEL"), default="INFO").upper(),
        )
