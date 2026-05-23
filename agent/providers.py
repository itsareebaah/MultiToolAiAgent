"""AI provider presets (OpenAI-compatible APIs)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    id: str
    label: str
    base_url: str
    default_model: str
    models: tuple[str, ...]
    api_key_env: str
    api_key_fallback_env: str | None = None
    timeout_seconds: float = 120.0


PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        id="openai",
        label="OpenAI",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        models=("gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"),
        api_key_env="OPENAI_API_KEY",
    ),
    "grok": ProviderConfig(
        id="grok",
        label="Grok / Groq (gsk key)",
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        models=(
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ),
        api_key_env="GROK_API_KEY",
        api_key_fallback_env="GROQ_API_KEY",
        timeout_seconds=120.0,
    ),
    "xai": ProviderConfig(
        id="xai",
        label="Grok xAI (xai- key)",
        base_url="https://api.x.ai/v1",
        default_model="grok-3-mini",
        models=(
            "grok-3-mini",
            "grok-3",
            "grok-4.3",
            "grok-4.20-0309-non-reasoning",
        ),
        api_key_env="XAI_API_KEY",
        timeout_seconds=360.0,
    ),
    "gemini": ProviderConfig(
        id="gemini",
        label="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-2.0-flash",
        models=("gemini-2.0-flash", "gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06"),
        api_key_env="GEMINI_API_KEY",
        api_key_fallback_env="GOOGLE_API_KEY",
    ),
    "deepseek": ProviderConfig(
        id="deepseek",
        label="DeepSeek",
        base_url="https://api.deepseek.com",
        default_model="deepseek-chat",
        models=("deepseek-chat", "deepseek-reasoner"),
        api_key_env="DEEPSEEK_API_KEY",
    ),
    "ollama": ProviderConfig(
        id="ollama",
        label="Ollama (local)",
        base_url="http://localhost:11434/v1",
        default_model="llama3.2",
        models=("llama3.2", "mistral", "qwen2.5", "gemma2"),
        api_key_env="OLLAMA_API_KEY",
        api_key_fallback_env="OPENAI_API_KEY",
    ),
}


def get_provider(provider_id: str | None) -> ProviderConfig:
    key = (provider_id or os.getenv("AI_PROVIDER", "openai")).strip().lower()
    if key not in PROVIDERS:
        valid = ", ".join(PROVIDERS)
        raise ValueError(f"Unknown provider '{key}'. Choose from: {valid}")
    return PROVIDERS[key]


def resolve_api_key(cfg: ProviderConfig) -> str:
    """Return API key for this provider only — never fall back to OPENAI_API_KEY."""
    env_names: list[str] = [cfg.api_key_env]
    if cfg.api_key_fallback_env:
        env_names.append(cfg.api_key_fallback_env)
    if cfg.id == "grok":
        env_names.append("GROQ_API_KEY")
    for name in env_names:
        key = os.getenv(name, "").strip()
        if key:
            return key
    if cfg.id == "ollama":
        return "ollama"
    return ""


def resolve_base_url(cfg: ProviderConfig) -> str:
    """Provider base URL; OPENAI_BASE_URL applies only when provider is openai."""
    if cfg.id == "openai":
        return os.getenv("OPENAI_BASE_URL", "").strip() or cfg.base_url
    return cfg.base_url


def resolve_model(cfg: ProviderConfig, model_override: str | None = None) -> str:
    if model_override and model_override.strip():
        return model_override.strip()
    per_provider = os.getenv(f"{cfg.api_key_env.replace('_API_KEY', '_MODEL')}", "").strip()
    if per_provider:
        return per_provider
    if cfg.id == "openai":
        return os.getenv("OPENAI_MODEL", "").strip() or cfg.default_model
    return cfg.default_model


def validate_api_key(cfg: ProviderConfig, key: str) -> None:
    if not key or cfg.id == "ollama":
        return
    placeholders = ("your-key", "your_key", "xai-your", "sk-your", "placeholder")
    lower = key.lower()
    if any(p in lower for p in placeholders):
        raise ValueError(
            f"Replace the placeholder in {cfg.api_key_env} with a real API key from the provider console."
        )
    if cfg.id == "grok":
        if key.startswith("sk-") and not key.startswith("gsk"):
            raise ValueError(
                "GROK_API_KEY looks like an OpenAI key (sk-...). "
                "Use a Groq key from https://console.groq.com — it starts with 'gsk_'."
            )
        if not (key.startswith("gsk") or key.startswith("gsk_")):
            raise ValueError(
                "GROK_API_KEY should be a Groq key starting with 'gsk_' from https://console.groq.com"
            )
    if cfg.id == "xai":
        if key.startswith("gsk"):
            raise ValueError(
                "This is a Groq key (gsk_). Set AI_PROVIDER=grok and use GROK_API_KEY instead."
            )
        if not key.startswith("xai-"):
            raise ValueError(
                "XAI keys from https://console.x.ai start with 'xai-'."
            )
    if cfg.id == "openai" and (key.startswith("xai-") or key.startswith("gsk")):
        raise ValueError(
            "OPENAI_API_KEY is not for Groq/Grok. Use GROK_API_KEY with AI_PROVIDER=grok."
        )


def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def list_provider_choices() -> list[tuple[str, str]]:
    return [(p.label, p.id) for p in PROVIDERS.values()]
