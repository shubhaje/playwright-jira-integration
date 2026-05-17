import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="config/.env")

JIRA_URL         = os.getenv("JIRA_URL")
JIRA_EMAIL       = os.getenv("JIRA_EMAIL")
JIRA_TOKEN       = os.getenv("JIRA_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "QA")
GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY")
AI_ENGINE        = os.getenv("AI_ENGINE", "gemini")   # gemini | ollama
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_URL       = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Validate on import — fail fast if anything is missing
for var, val in [("JIRA_URL", JIRA_URL), ("JIRA_EMAIL", JIRA_EMAIL), ("JIRA_TOKEN", JIRA_TOKEN)]:
    if not val:
        raise EnvironmentError(f"Missing required env var: {var}")