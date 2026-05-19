#report + csv generation
import os
import csv
import json
from datetime import datetime

class ReportGenerator:

    def __init__(self, output_dir="reporting/output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, issue: dict, scenarios: list[dict],
                 pushed_keys: list[str]) -> dict:
        """
        Master method — generates all report formats.
        Returns dict with file paths.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix    = f"{issue['key']}_{timestamp}"

        paths = {
            "html": self._generate_html(issue, scenarios, pushed_keys, prefix),
            "csv":  self._generate_csv(issue, scenarios, pushed_keys, prefix),
            "json": self._generate_json(issue, scenarios, pushed_keys, prefix),
        }

        print(f"✅ Reports generated in {self.output_dir}/")
        for fmt, path in paths.items():
            print(f"   {fmt.upper()}: {path}")

        return paths

    # ── HTML ──────────────────────────────────────────────

    def _generate_html(self, issue, scenarios, pushed_keys, prefix):
        approved = [s for s in scenarios if s.get("_approved", True)]
        rejected = [s for s in scenarios if not s.get("_approved", True)]

        rows = ""
        for i, s in enumerate(scenarios):
            status     = "Approved" if s.get("_approved", True) else "Rejected"
            status_cls = "approved" if s.get("_approved", True) else "rejected"
            jira_key   = pushed_keys[i] if i < len(pushed_keys) else "—"
            steps_html = "".join(f"<li>{step}</li>"
                                 for step in s.get("steps", []))
            rows += f"""
            <tr>
                <td><span class="badge {status_cls}">{status}</span></td>
                <td><strong>{s.get('title','')}</strong></td>
                <td><span class="priority p-{s.get('priority','Medium').lower()}">{s.get('priority','')}</span></td>
                <td>{s.get('preconditions','')}</td>
                <td><ol>{steps_html}</ol></td>
                <td>{s.get('expected_result','')}</td>
                <td><code>{jira_key}</code></td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QA Report — {issue['key']}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #f5f7fa; color: #333; padding: 2rem; }}
  .header {{ background: #1e1e2e; color: white; padding: 2rem;
             border-radius: 12px; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  .header p  {{ opacity: 0.7; font-size: 0.9rem; }}
  .metrics   {{ display: flex; gap: 1rem; margin-bottom: 2rem; }}
  .metric    {{ background: white; padding: 1.5rem; border-radius: 10px;
                flex: 1; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  .metric h2 {{ font-size: 2rem; margin-bottom: 0.3rem; }}
  .metric p  {{ color: #666; font-size: 0.85rem; }}
  .green {{ color: #22c55e; }} .red {{ color: #ef4444; }}
  .blue  {{ color: #3b82f6; }}
  table  {{ width: 100%; border-collapse: collapse; background: white;
            border-radius: 10px; overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  th     {{ background: #1e1e2e; color: white; padding: 0.85rem 1rem;
            text-align: left; font-size: 0.8rem; text-transform: uppercase;
            letter-spacing: 0.05em; }}
  td     {{ padding: 0.85rem 1rem; border-bottom: 1px solid #f0f0f0;
            vertical-align: top; font-size: 0.88rem; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #fafafa; }}
  ol {{ padding-left: 1.2rem; }}
  ol li {{ margin-bottom: 0.3rem; }}
  .badge    {{ padding: 0.25rem 0.6rem; border-radius: 20px;
               font-size: 0.75rem; font-weight: 600; }}
  .approved {{ background: #dcfce7; color: #166534; }}
  .rejected {{ background: #fee2e2; color: #991b1b; }}
  .priority {{ padding: 0.2rem 0.5rem; border-radius: 4px;
               font-size: 0.75rem; font-weight: 600; }}
  .p-high   {{ background: #fee2e2; color: #991b1b; }}
  .p-medium {{ background: #fef9c3; color: #854d0e; }}
  .p-low    {{ background: #dcfce7; color: #166534; }}
  code {{ background: #f1f5f9; padding: 0.2rem 0.4rem;
          border-radius: 4px; font-size: 0.8rem; }}
  .footer {{ text-align: center; margin-top: 2rem;
             color: #999; font-size: 0.8rem; }}
</style>
</head>
<body>
<div class="header">
  <h1>🧪 QA Test Report — {issue['key']}</h1>
  <p>{issue['summary']}</p>
  <p style="margin-top:0.5rem">Generated: {datetime.now().strftime('%d %b %Y %H:%M')} &nbsp;|&nbsp;
     Priority: {issue['priority']} &nbsp;|&nbsp; Status: {issue['status']}</p>
</div>

<div class="metrics">
  <div class="metric">
    <h2>{len(scenarios)}</h2>
    <p>Total scenarios</p>
  </div>
  <div class="metric">
    <h2 class="green">{len(approved)}</h2>
    <p>Approved</p>
  </div>
  <div class="metric">
    <h2 class="red">{len(rejected)}</h2>
    <p>Rejected</p>
  </div>
  <div class="metric">
    <h2 class="blue">{len(pushed_keys)}</h2>
    <p>Pushed to Jira</p>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th>Status</th><th>Title</th><th>Priority</th>
      <th>Preconditions</th><th>Steps</th>
      <th>Expected result</th><th>Jira key</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>

<div class="footer">
  Generated by QA Automation Bot &nbsp;|&nbsp;
  Playwright + Ollama + Jira
</div>
</body>
</html>"""

        path = os.path.join(self.output_dir, f"{prefix}_report.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    # ── CSV ───────────────────────────────────────────────

    def _generate_csv(self, issue, scenarios, pushed_keys, prefix):
        path = os.path.join(self.output_dir, f"{prefix}_report.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Jira Story", "Test Key", "Title", "Priority",
                "Status", "Preconditions", "Steps", "Expected Result"
            ])
            for i, s in enumerate(scenarios):
                writer.writerow([
                    issue["key"],
                    pushed_keys[i] if i < len(pushed_keys) else "",
                    s.get("title", ""),
                    s.get("priority", ""),
                    "Approved" if s.get("_approved", True) else "Rejected",
                    s.get("preconditions", ""),
                    " | ".join(s.get("steps", [])),
                    s.get("expected_result", "")
                ])
        return path

    # ── JSON ──────────────────────────────────────────────

    def _generate_json(self, issue, scenarios, pushed_keys, prefix):
        payload = {
            "generated_at": datetime.now().isoformat(),
            "issue":        issue,
            "summary": {
                "total":    len(scenarios),
                "approved": sum(1 for s in scenarios if s.get("_approved", True)),
                "rejected": sum(1 for s in scenarios if not s.get("_approved", True)),
                "pushed":   len(pushed_keys)
            },
            "scenarios": [
                {**s, "jira_key": pushed_keys[i] if i < len(pushed_keys) else None}
                for i, s in enumerate(scenarios)
            ]
        }
        path = os.path.join(self.output_dir, f"{prefix}_report.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path

    def build_jira_comment(self, scenarios: list[dict],
                           pushed_keys: list[str]) -> str:
        """Plain text summary to post as a Jira comment."""
        approved = [s for s in scenarios if s.get("_approved", True)]
        rejected = [s for s in scenarios if not s.get("_approved", True)]
        lines = [
            f"*QA Bot Report — {datetime.now().strftime('%d %b %Y %H:%M')}*",
            f"Total: {len(scenarios)} | Approved: {len(approved)} "
            f"| Rejected: {len(rejected)} | Created: {len(pushed_keys)}",
            "",
            "*Created test cases:*",
        ]
        for key in pushed_keys:
            lines.append(f"- {key}")
        return "\n".join(lines)