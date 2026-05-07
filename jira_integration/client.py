import requests
from requests.auth import HTTPBasicAuth
from config.settings import JIRA_URL, JIRA_EMAIL, JIRA_TOKEN

class JiraClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        self.base  = f"{JIRA_URL}rest/api/3"
        self.auth  = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
        self.heads = {
            "Accept":       "application/json",
            "Content-Type": "application/json"
        }
        # Validate connection
        r = requests.get(f"{self.base}/myself", auth=self.auth, headers=self.heads)
        if r.status_code == 200:
            name = r.json().get("displayName", "")
            print(f"✅ Connected to Jira as: {name}")
        else:
            raise ConnectionError(f"❌ Jira auth failed {r.status_code}: {r.text}")

    def get(self, path, params=None):
        r = requests.get(f"{self.base}/{path}",
                         auth=self.auth, headers=self.heads, params=params)
        r.raise_for_status()
        return r.json()

    def post(self, path, payload):
        r = requests.post(f"{self.base}/{path}",
                        auth=self.auth, headers=self.heads, json=payload)
        r.raise_for_status()
        # issueLink and transitions return 201/204 with empty body
        if r.content and r.content.strip():
            return r.json()
        return {}

    def put(self, path, payload):
        r = requests.put(f"{self.base}/{path}",
                         auth=self.auth, headers=self.heads, json=payload)
        r.raise_for_status()
        return r.json()