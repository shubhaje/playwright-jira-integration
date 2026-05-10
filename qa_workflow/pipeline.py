#Approve → push flow
from jira_integration.fetcher       import JiraFetcher
from jira_integration.creator       import JiraCreator
from browser_intelligence.extractor import PageExtractor
from ai_engine.engine_factory       import get_engine
import re

class QAPipeline:
    def __init__(self):
        self.fetcher   = JiraFetcher()
        self.creator   = JiraCreator()
        self.extractor = PageExtractor(headless=True)
        self.engine    = get_engine()

    def fetch_issues(self, max_results=10):
        return self.fetcher.get_all_issues(max_results=max_results)

    def run_for_issue(self, issue: dict, url: str) -> list[dict]:
        """Crawl URL + generate scenarios for one Jira issue."""
        page_context = self.extractor.extract(url)
        if not page_context:
            return []
        scenarios = self.engine.generate_scenarios(issue, page_context)
        # Attach source info to each scenario
        for s in scenarios:
            s["_issue_key"] = issue["key"]
            s["_url"]       = url
        return scenarios

    def push_scenarios(self, scenarios: list[dict], story_key: str) -> list[str]:
        """Create approved scenarios as Jira test cases. Returns created keys."""
        created = []
        for s in scenarios:
            steps_text  = "\n".join(
                f"{i+1}. {step}" for i, step in enumerate(s.get("steps", []))
            )
            description = (
                f"Preconditions:\n{s.get('preconditions', 'N/A')}\n\n"
                f"Steps:\n{steps_text}\n\n"
                f"Expected Result:\n{s.get('expected_result', 'N/A')}"
            )
            test_key = self.creator.create_test_case(
                summary     = s.get("title", "Untitled"),
                description = description,
                priority    = s.get("priority", "Medium")
            )
            if test_key:
                self.creator.link_issues(test_key, story_key)
                self.creator.add_comment(
                    story_key,
                    f"Auto-generated test case {test_key} linked by QA bot."
                )
                created.append(test_key)
        return created

    @staticmethod
    def extract_url_from_description(description: str) -> str:
        match = re.search(r'https?://[^\s]+', description or "")
        return match.group(0) if match else ""