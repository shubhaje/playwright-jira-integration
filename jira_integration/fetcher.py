from jira_integration.client import JiraClient
from config.settings import JIRA_PROJECT_KEY

class JiraFetcher:
    def __init__(self):
        self.client  = JiraClient()          # ← no .get() here
        self.project = JIRA_PROJECT_KEY

    def get_open_stories(self, max_results=50):
        jql = (f"project={self.project} AND issuetype=Story "
               f"AND status != Done ORDER BY priority DESC")
        return self._fetch(jql, max_results)

    def get_bugs(self, max_results=50):
        jql = (f"project={self.project} AND issuetype=Bug "
               f"AND status != Done ORDER BY created DESC")
        return self._fetch(jql, max_results)

    def get_issue(self, issue_key):
        try:
            data = self.client.get(f"issue/{issue_key}")
            return self._parse(data)
        except Exception as e:
            print(f"❌ Could not fetch {issue_key}: {e}")
            return None

    def get_all_issues(self, max_results=50):
        jql = f"project={self.project} AND status != Done ORDER BY created DESC"
        return self._fetch(jql, max_results)

    def _fetch(self, jql, max_results=50):
        try:
            data = self.client.get("search/jql", params={
                "jql":        jql,
                "maxResults": max_results,
                "fields":     "summary,description,status,priority,assignee,issuetype,labels"
            })
            return [self._parse_fields(i["key"], i["fields"]) for i in data.get("issues", [])]
        except Exception as e:
            print(f"❌ JQL fetch failed: {e}")
            return []

    def _parse(self, issue):
        return self._parse_fields(issue["key"], issue["fields"])

    def _parse_fields(self, key, f):
        return {
            "key":         key,
            "summary":     f.get("summary", ""),
            "description": self._extract_text(f.get("description")),
            "status":      f["status"]["name"]    if f.get("status")    else "",
            "priority":    f["priority"]["name"]  if f.get("priority")  else "Medium",
            "assignee":    f["assignee"]["displayName"] if f.get("assignee") else "Unassigned",
            "issuetype":   f["issuetype"]["name"] if f.get("issuetype") else "",
            "labels":      f.get("labels", []),
            "url":         f"https://shubhangiajegaonkar.atlassian.net/browse/{key}"
        }

    def _extract_text(self, desc):
        """Extract plain text from Atlassian Document Format (ADF)."""
        if not desc or not isinstance(desc, dict):
            return ""
        texts = []
        for block in desc.get("content", []):
            for inline in block.get("content", []):
                if inline.get("type") == "text":
                    texts.append(inline.get("text", ""))
        return " ".join(texts)