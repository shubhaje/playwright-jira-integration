from jira_integration.client import JiraClient
from config.settings import JIRA_PROJECT_KEY

class JiraCreator:
    def __init__(self):
        self.client     = JiraClient()
        self.project    = JIRA_PROJECT_KEY
        self._link_types = None          # cache so we fetch only once

    def create_test_case(self, summary, description, priority="Medium", labels=None):
        payload = {
            "fields": {
                "project":     {"key": self.project},
                "summary":     f"[TEST] {summary}",
                "description": {
                    "type": "doc", "version": 1,
                    "content": [{
                        "type":    "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }]
                },
                "issuetype": {"name": "Task"},
                "priority":  {"name": priority},
                "labels":    labels or ["auto-generated", "qa-bot"]
            }
        }
        try:
            data = self.client.post("issue", payload)
            key  = data["key"]
            print(f"✅ Created: {key}")
            return key
        except Exception as e:
            print(f"❌ Create failed: {e}")
            return None

    def link_issues(self, from_key, to_key, link_type="Relates"):
        try:
            self.client.post("issueLink", {
                "type":         {"name": link_type},
                "inwardIssue":  {"key": from_key},
                "outwardIssue": {"key": to_key}
            })
            print(f"✅ Linked {from_key} → {to_key} [{link_type}]")
        except Exception as e:
            print(f"❌ Link failed: {e}")

    def add_comment(self, issue_key, text):
        try:
            self.client.post(f"issue/{issue_key}/comment", {
                "body": {
                    "type": "doc", "version": 1,
                    "content": [{
                        "type":    "paragraph",
                        "content": [{"type": "text", "text": text}]
                    }]
                }
            })
            print(f"✅ Comment added to {issue_key}")
        except Exception as e:
            print(f"❌ Comment failed: {e}")

    def transition_issue(self, issue_key, target_status):
        try:
            data   = self.client.get(f"issue/{issue_key}/transitions")
            match  = next(
                (t for t in data.get("transitions", [])
                 if t["name"].lower() == target_status.lower()), None)
            if not match:
                names = [t["name"] for t in data.get("transitions", [])]
                print(f"❌ '{target_status}' not found. Available: {names}")
                return
            self.client.post(f"issue/{issue_key}/transitions",
                             {"transition": {"id": match["id"]}})
            print(f"✅ {issue_key} → {target_status}")
        except Exception as e:
            print(f"❌ Transition failed: {e}")

    def get_link_types(self):
        """Fetch once, cache, and print link types."""
        if self._link_types:
            return self._link_types
        try:
            data = self.client.get("issueLinkType")
            self._link_types = data.get("issueLinkTypes", [])
            for t in self._link_types:
                print(f"  name='{t['name']}'  inward='{t['inward']}'  outward='{t['outward']}'")
            return self._link_types
        except Exception as e:
            print(f"❌ get_link_types failed: {e}")
            return []

    def get_issue_types(self):
        try:
            data = self.client.get(f"project/{self.project}/statuses")
            for issuetype in data:
                print(f"  type='{issuetype['name']}'")
        except Exception as e:
            print(f"❌ get_issue_types failed: {e}")