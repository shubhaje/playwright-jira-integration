#Shared interface/ABC
from abc import ABC, abstractmethod

class BaseEngine(ABC):

    @abstractmethod
    def generate_scenarios(self, jira_story: dict, page_context: dict) -> list[dict]:
        """
        Takes a Jira story dict and page context dict.
        Returns a list of scenario dicts:
        [
          {
            "title":           str,
            "preconditions":   str,
            "steps":           list[str],
            "expected_result": str,
            "priority":        str   # High | Medium | Low
          }
        ]
        """
        pass

    def _build_prompt(self, jira_story: dict, page_context: dict) -> str:
        """Shared prompt — identical for both engines."""
        buttons  = ", ".join([b["text"] for b in page_context.get("buttons", [])])
        inputs   = ", ".join([
            f"{i['type']}:{i['name'] or i['placeholder']}"
            for i in page_context.get("inputs", [])
        ])
        forms    = ", ".join([f["action"] for f in page_context.get("forms", [])])
        headings = ", ".join([h["text"] for h in page_context.get("headings", [])])

        return f"""
You are a senior QA engineer. Generate exactly 5 detailed test scenarios as a JSON array.

JIRA STORY
----------
Key        : {jira_story.get('key', 'N/A')}
Summary    : {jira_story.get('summary', 'N/A')}
Description: {jira_story.get('description', 'N/A')}
Priority   : {jira_story.get('priority', 'Medium')}

PAGE CONTEXT
------------
URL      : {page_context.get('url', 'N/A')}
Title    : {page_context.get('title', 'N/A')}
Headings : {headings}
Buttons  : {buttons}
Inputs   : {inputs}
Forms    : {forms}
Page text: {page_context.get('text', '')[:800]}

INSTRUCTIONS
------------
- Cover: happy path, empty fields, invalid data, boundary values, UX/error messages
- Each scenario must be specific to the page elements above
- Return ONLY a valid JSON array, no markdown, no explanation

REQUIRED FORMAT
---------------
[
  {{
    "title":           "short scenario title",
    "preconditions":   "what must be true before this test",
    "steps":           ["step 1", "step 2", "step 3"],
    "expected_result": "what should happen",
    "priority":        "High"
  }}
]
""".strip()