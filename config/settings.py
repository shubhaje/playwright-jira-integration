import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="config/.env")

JIRA_URL         = os.getenv("JIRA_URL")
JIRA_EMAIL       = os.getenv("JIRA_EMAIL")
JIRA_TOKEN       = os.getenv("JIRA_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "QA")

# Validate on import — fail fast if anything is missing
for var, val in [("JIRA_URL", JIRA_URL), ("JIRA_EMAIL", JIRA_EMAIL), ("JIRA_TOKEN", JIRA_TOKEN)]:
    if not val:
        raise EnvironmentError(f"Missing required env var: {var}")