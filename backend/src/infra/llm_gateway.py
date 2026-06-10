"""LlmGateway adapter: Azure AI Foundry / Azure OpenAI with a seed-keyed cache.

Caching on a deterministic ``seed_key`` keeps runs reproducible even though the
model itself is not: the first call hits the model, every later call with the same
key returns the cached completion.

Two endpoint styles are supported automatically:

* **v1 surface** — when ``WC_AOAI_ENDPOINT`` ends in ``/openai/v1`` (the modern Azure
  AI Foundry endpoint, required for gpt-5-class models). Reached with the standard
  ``AsyncOpenAI`` client and ``api-version=preview``.
* **classic** — a bare ``https://<res>.openai.azure.com`` endpoint, reached with
  ``AsyncAzureOpenAI`` and a dated ``api_version``.

Auth is the API key when ``WC_AOAI_API_KEY`` is set, otherwise Entra ID via
``DefaultAzureCredential`` (Managed Identity in the cloud) on the classic surface.
"""
from __future__ import annotations

from src.app.config import Settings
from .ports import Cache


class AzureOpenAIGateway:
    def __init__(self, settings: Settings, cache: Cache) -> None:
        self._s = settings
        self._cache = cache
        self._client = None  # lazy: only construct an SDK client when first used

    def _is_v1(self) -> bool:
        ep = self._s.aoai_endpoint.rstrip("/")
        return ep.endswith("/v1") or "/openai/v1" in ep

    def _ensure_client(self):
        if self._client is not None:
            return self._client

        # The v1 surface (.../openai/v1) is OpenAI-compatible: use the *standard*
        # client so the path is .../openai/v1/chat/completions. The Azure client
        # would inject /deployments/{model}/ here, which 404s on the v1 surface.
        if self._is_v1():
            from openai import AsyncOpenAI

            base = self._s.aoai_endpoint
            if not base.endswith("/"):
                base += "/"
            api_version = self._s.aoai_api_version or "preview"
            return self._set_client(AsyncOpenAI(
                base_url=base,
                api_key=self._s.aoai_api_key or "missing",
                default_query={"api-version": api_version},
            ))

        # Classic surface: the Azure client builds /openai/deployments/{model}/...
        from openai import AsyncAzureOpenAI

        if self._s.aoai_api_key:
            return self._set_client(AsyncAzureOpenAI(
                azure_endpoint=self._s.aoai_endpoint,
                api_key=self._s.aoai_api_key,
                api_version=self._s.aoai_api_version,
            ))

        from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
        return self._set_client(AsyncAzureOpenAI(
            azure_endpoint=self._s.aoai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=self._s.aoai_api_version,
        ))

    def _set_client(self, client):
        self._client = client
        return client

    async def complete(self, prompt: str, seed_key: str) -> str:
        cache_key = f"llm:{seed_key}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        if not self._s.llm_enabled or not self._s.aoai_endpoint:
            # Disabled / unconfigured: degrade gracefully, the core sim is deterministic.
            return ""

        client = self._ensure_client()
        # No temperature / seed / max_tokens: gpt-5-class models reject non-default
        # sampling params; reproducibility comes from the cache above.
        resp = await client.chat.completions.create(
            model=self._s.aoai_deployment,
            messages=[{"role": "user", "content": prompt}],
        )
        text: str = resp.choices[0].message.content or ""
        await self._cache.set(cache_key, text)
        return text


class NullLlmGateway:
    """No-op gateway used when the LLM is disabled (returns empty completions)."""

    async def complete(self, prompt: str, seed_key: str) -> str:  # noqa: D401
        return ""
