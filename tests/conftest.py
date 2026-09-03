import os

# HARD-set test values (assignment, not setdefault) before any app module
# is imported. That way the test env wins over:
#   1. a local .env file (which pydantic-settings would also load;
#      Env > Dotenv in pydantic-settings)
#   2. values leaked from the shell (e.g. a real OBSIDIAN_VAULT_PATH)
# Keeps tests reproducible regardless of local environment.
os.environ["TELEGRAM_WEBHOOK_SECRET"] = "test-webhook-secret"
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:TEST-BOT-TOKEN"
os.environ["TELEGRAM_ALLOWED_USER_IDS"] = ""
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["OPENAI_MODEL"] = "gpt-4o-mini"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["OBSIDIAN_VAULT_PATH"] = "/tmp/seiton-test-vault"
os.environ["SEITON_API_KEY"] = "test-seiton-api-key"
os.environ["SEITON_LICENSE_KEY"] = ""
os.environ["SEITON_LICENSE_REQUIRED"] = "false"
os.environ["SEITON_DEBUG"] = "false"


import pytest


@pytest.fixture(autouse=True)
def _clear_vault_category_cache():
    """E4-3: category cache must not poison tests across each other."""
    from app.vault.categories import clear_category_cache

    clear_category_cache()
    yield
    clear_category_cache()

