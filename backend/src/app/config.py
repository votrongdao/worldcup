"""Runtime settings bound from environment / Key Vault.

All variables are prefixed ``WC_`` (e.g. ``WC_BACKEND``, ``WC_REDIS_URL``).
``backend`` selects which adapter set ``app.deps`` wires:

* ``memory`` — single-process, in-memory queue/store/log (no external services).
              Great for tests and ``uvicorn ... --reload`` without Docker.
* ``local``  — Redis + Postgres + Azurite, the Docker Compose stack.
* ``azure``  — the Azure adapters (Service Bus / Postgres / Blob / SignalR).
"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WC_", extra="ignore")

    backend: str = "memory"          # memory | local | azure
    worker_concurrency: int = 4      # in-process workers (memory mode)

    # --- local / Docker service endpoints -----------------------------
    redis_url: str = "redis://localhost:6379/0"
    pg_dsn: str = "postgresql+asyncpg://worldcup:worldcup@localhost:5432/worldcup"
    # Azurite well-known development connection string.
    blob_conn: str = (
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
        "K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://localhost:10000/devstoreaccount1;"
    )

    # --- Azure-native (cloud) connection strings ----------------------
    servicebus_conn: str = ""
    signalr_conn: str = ""

    # --- Azure AI Foundry / Azure OpenAI ------------------------------
    aoai_endpoint: str = ""          # e.g. https://<resource>.openai.azure.com
    aoai_api_key: str = ""           # leave empty to use Entra ID (DefaultAzureCredential)
    aoai_deployment: str = "gpt-4o"
    aoai_api_version: str = "2024-10-21"
    llm_enabled: bool = False        # opt-in; the simulation is deterministic without it
