from jira_integration.fetcher        import JiraFetcher
from jira_integration.creator        import JiraCreator
from browser_intelligence.extractor  import PageExtractor
from ai_engine.engine_factory        import get_engine

def run_pipeline():
    fetcher   = JiraFetcher()
    creator   = JiraCreator()
    extractor = PageExtractor(headless=True)
    engine    = get_engine()

    # 1. Fetch real open issues from Jira
    print("\n── Fetching Jira issues ──")
    issues = fetcher.get_all_issues(max_results=3)
    if not issues:
        print("❌ No issues found")
        return

    for issue in issues:
        print(f"\n{'='*60}")
        print(f"Processing: {issue['key']} — {issue['summary']}")
        print(f"{'='*60}")

        # 2. Extract URL from description or use a default test URL
        url = _extract_url(issue) or "https://the-internet.herokuapp.com/login"
        print(f"🔗 URL: {url}")

        # 3. Crawl the page
        page_context = extractor.extract(url)
        if not page_context:
            print(f"⚠️  Skipping {issue['key']} — page extraction failed")
            continue

        # 4. Generate scenarios
        scenarios = engine.generate_scenarios(issue, page_context)
        if not scenarios:
            print(f"⚠️  No scenarios generated for {issue['key']}")
            continue

        # 5. Print scenarios
        print(f"\n── {len(scenarios)} scenarios for {issue['key']} ──")
        for i, s in enumerate(scenarios, 1):
            print(f"\n  {i}. {s.get('title')} [{s.get('priority')}]")
            print(f"     Pre : {s.get('preconditions')}")
            for step in s.get("steps", []):
                print(f"       - {step}")
            print(f"     Exp : {s.get('expected_result')}")

        # 6. Ask before pushing to Jira
        print(f"\n📤 Push these {len(scenarios)} scenarios to Jira? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == "y":
            _push_to_jira(creator, scenarios, issue["key"])

def _extract_url(issue):
    """Pull a URL from the issue description if one exists."""
    import re
    text = issue.get("description", "")
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else None

def _push_to_jira(creator, scenarios, story_key):
    """Create test cases in Jira and link them to the story."""
    for s in scenarios:
        steps_text = "\n".join(
            [f"{i+1}. {step}" for i, step in enumerate(s.get("steps", []))]
        )
        description = (
            f"Preconditions:\n{s.get('preconditions', '')}\n\n"
            f"Steps:\n{steps_text}\n\n"
            f"Expected Result:\n{s.get('expected_result', '')}"
        )
        test_key = creator.create_test_case(
            summary     = s.get("title", "Untitled scenario"),
            description = description,
            priority    = s.get("priority", "Medium")
        )
        if test_key:
            creator.link_issues(test_key, story_key)
            creator.add_comment(
                story_key,
                f"Auto-generated test case {test_key} created by QA bot."
            )

if __name__ == "__main__":
    run_pipeline()