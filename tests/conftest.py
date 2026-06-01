import os

# Test-Werte HART setzen (Assignment, nicht setdefault) bevor irgendein
# App-Modul importiert wird. Damit hat die Test-Umgebung Vorrang vor:
#   1. einer lokalen .env-Datei (die pydantic-settings sonst zusaetzlich laedt;
#      Env > Dotenv in pydantic-settings)
#   2. evtl. aus der Shell geleakten Werten (z.B. echter OBSIDIAN_VAULT_PATH)
# Tests werden so reproduzierbar, egal in welcher lokalen Umgebung sie laufen.
os.environ["TELEGRAM_WEBHOOK_SECRET"] = "test-webhook-secret"
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:TEST-BOT-TOKEN"
os.environ["TELEGRAM_ALLOWED_USER_IDS"] = ""
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["OPENAI_MODEL"] = "gpt-4o-mini"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["OBSIDIAN_VAULT_PATH"] = "/tmp/seiton-test-vault"
