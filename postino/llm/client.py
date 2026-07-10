from django.conf import settings

from .base import BaseLLMClient


def get_llm_client() -> BaseLLMClient:
    """Return an LLM client instance based on POSTINO_LLM_PROVIDER setting."""
    provider = getattr(settings, 'POSTINO_LLM_PROVIDER', 'openai')

    if provider == 'openai':
        from .openai_client import OpenAIClient
        return OpenAIClient()

    if provider == 'anthropic':
        from .anthropic_client import AnthropicClient
        return AnthropicClient()

    raise ValueError(
        f"Unknown LLM provider '{provider}'. "
        "Set POSTINO_LLM_PROVIDER to 'openai' or 'anthropic'."
    )
