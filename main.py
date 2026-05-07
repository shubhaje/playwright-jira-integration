from jira_integration.fetcher import JiraFetcher
from jira_integration.creator import JiraCreator

def test_jira():
    fetcher = JiraFetcher()
    creator = JiraCreator()

    print("\n── Issue types ──")
    creator.get_issue_types()

    print("\n── Link types ──")
    creator.get_link_types()          # printed once, cached

    print("\n── All open issues ──")
    issues = fetcher.get_all_issues(max_results=5)
    for i in issues:
        print(f"  {i['key']}  [{i['issuetype']}]  [{i['priority']}]  {i['summary']}")

    if issues:
        print("\n── Creating test case ──")
        test_key = creator.create_test_case(
            summary="Login — empty credentials validation",
            description=(
                "Steps:\n"
                "1. Go to /login\n"
                "2. Leave fields blank and click Submit\n"
                "Expected: Validation errors shown, no API call made."
            ),
            priority="High"
        )
        if test_key:
            creator.link_issues(test_key, issues[0]["key"])   # uses "Relates" by default
            creator.add_comment(
                issues[0]["key"],
                f"Test case {test_key} auto-generated and linked by QA bot."
            )

if __name__ == "__main__":
    test_jira()