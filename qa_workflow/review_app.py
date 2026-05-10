#Streamlit UI
import streamlit as st
import pandas as pd
from qa_workflow.pipeline import QAPipeline

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title = "QA Review Workflow",
    page_icon  = "🧪",
    layout     = "wide"
)

# ── Session state init ────────────────────────────────────
def init_state():
    defaults = {
        "pipeline":       None,
        "issues":         [],
        "selected_issue": None,
        "scenarios":      [],
        "approved":       {},    # index → bool
        "edited":         {},    # index → dict
        "pushed_keys":    [],
        "page":           "home" # home | generate | review | done
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Load pipeline once ────────────────────────────────────
@st.cache_resource
def load_pipeline():
    return QAPipeline()

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.title("🧪 QA Bot")
    st.caption("Playwright + AI + Jira")
    st.divider()
    st.markdown("**Workflow**")
    steps = ["1️⃣ Select issue", "2️⃣ Generate", "3️⃣ Review", "4️⃣ Push to Jira"]
    page_map = {"home": 0, "generate": 1, "review": 2, "done": 3}
    for i, step in enumerate(steps):
        if i == page_map.get(st.session_state.page, 0):
            st.markdown(f"**→ {step}**")
        else:
            st.markdown(f"  {step}")

    st.divider()
    if st.button("🔄 Reset", use_container_width=True):
        for k in ["scenarios", "approved", "edited",
                  "pushed_keys", "selected_issue"]:
            st.session_state[k] = {} if k in ["approved", "edited"] else []
        st.session_state.page = "home"
        st.rerun()

# ══════════════════════════════════════════════════════════
# PAGE 1 — Home: select Jira issue
# ══════════════════════════════════════════════════════════
if st.session_state.page == "home":
    st.title("QA Review Workflow")
    st.markdown("Select a Jira issue to generate and review test scenarios.")
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        max_results = st.slider("Max issues to fetch", 5, 30, 10)
    with col2:
        fetch_btn = st.button("📥 Fetch Jira Issues",
                              use_container_width=True, type="primary")

    if fetch_btn:
        with st.spinner("Connecting to Jira..."):
            pipeline = load_pipeline()
            st.session_state.pipeline = pipeline
            st.session_state.issues   = pipeline.fetch_issues(max_results)

    if st.session_state.issues:
        st.success(f"Found {len(st.session_state.issues)} issues")
        st.divider()

        for issue in st.session_state.issues:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 4, 1, 1])
                c1.code(issue["key"])
                c2.markdown(f"**{issue['summary']}**")
                c3.markdown(f"`{issue['priority']}`")
                if c4.button("Select →", key=f"sel_{issue['key']}"):
                    st.session_state.selected_issue = issue
                    st.session_state.page           = "generate"
                    st.rerun()

# ══════════════════════════════════════════════════════════
# PAGE 2 — Generate scenarios
# ══════════════════════════════════════════════════════════
elif st.session_state.page == "generate":
    issue = st.session_state.selected_issue
    st.title(f"Generate scenarios — {issue['key']}")
    st.markdown(f"**{issue['summary']}**")

    with st.container(border=True):
        st.markdown("**Issue details**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Priority", issue["priority"])
        col2.metric("Status",   issue["status"])
        col3.metric("Type",     issue["issuetype"])
        if issue["description"]:
            st.caption(issue["description"][:300])

    st.divider()

    # URL input
    auto_url = QAPipeline.extract_url_from_description(issue["description"])
    url = st.text_input(
        "🔗 URL to crawl",
        value = auto_url or "https://the-internet.herokuapp.com/login",
        help  = "Enter the URL of the page this story relates to"
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        gen_btn = st.button("🤖 Generate Scenarios",
                            use_container_width=True, type="primary")
    with col2:
        st.caption("Playwright will crawl the URL, then AI generates test scenarios")

    if gen_btn:
        if not url:
            st.error("Please enter a URL")
        else:
            with st.spinner(f"🌐 Crawling {url}..."):
                pipeline  = st.session_state.pipeline or load_pipeline()
                scenarios = pipeline.run_for_issue(issue, url)

            if not scenarios:
                st.error("No scenarios generated. Check the URL and try again.")
            else:
                st.session_state.scenarios = scenarios
                st.session_state.approved  = {i: True for i in range(len(scenarios))}
                st.session_state.edited    = {i: s.copy() for i, s in enumerate(scenarios)}
                st.session_state.page      = "review"
                st.rerun()

# ══════════════════════════════════════════════════════════
# PAGE 3 — Review scenarios
# ══════════════════════════════════════════════════════════
elif st.session_state.page == "review":
    issue     = st.session_state.selected_issue
    scenarios = st.session_state.scenarios

    st.title(f"Review scenarios — {issue['key']}")
    approved_count = sum(1 for v in st.session_state.approved.values() if v)
    st.markdown(f"**{approved_count} of {len(scenarios)} approved** — edit, approve or reject each scenario below.")
    st.divider()

    # Bulk actions
    bc1, bc2, bc3 = st.columns(3)
    if bc1.button("✅ Approve all"):
        st.session_state.approved = {i: True for i in range(len(scenarios))}
        st.rerun()
    if bc2.button("❌ Reject all"):
        st.session_state.approved = {i: False for i in range(len(scenarios))}
        st.rerun()
    bc3.caption(f"{approved_count}/{len(scenarios)} approved")

    st.divider()

    # Individual scenario cards
    for i, scenario in enumerate(scenarios):
        edited    = st.session_state.edited.get(i, scenario)
        is_approved = st.session_state.approved.get(i, True)

        border_color = "✅" if is_approved else "❌"
        with st.expander(f"{border_color} Scenario {i+1}: {edited.get('title', '')}", expanded=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                # Editable fields
                new_title = st.text_input(
                    "Title", value=edited.get("title", ""),
                    key=f"title_{i}"
                )
                new_priority = st.selectbox(
                    "Priority",
                    ["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(
                        edited.get("priority", "Medium")
                    ),
                    key=f"priority_{i}"
                )
                new_pre = st.text_area(
                    "Preconditions",
                    value=edited.get("preconditions", ""),
                    height=68, key=f"pre_{i}"
                )
                # Steps
                st.markdown("**Steps**")
                steps     = edited.get("steps", [])
                new_steps = []
                for j, step in enumerate(steps):
                    new_step = st.text_input(
                        f"Step {j+1}", value=step,
                        key=f"step_{i}_{j}"
                    )
                    new_steps.append(new_step)

                new_expected = st.text_area(
                    "Expected result",
                    value=edited.get("expected_result", ""),
                    height=68, key=f"exp_{i}"
                )

                # Save edits back to state
                st.session_state.edited[i] = {
                    **edited,
                    "title":           new_title,
                    "priority":        new_priority,
                    "preconditions":   new_pre,
                    "steps":           new_steps,
                    "expected_result": new_expected,
                }

            with col2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                approve = st.toggle(
                    "Approve",
                    value=is_approved,
                    key=f"approve_{i}"
                )
                st.session_state.approved[i] = approve
                if approve:
                    st.success("Approved")
                else:
                    st.error("Rejected")

    st.divider()

    # Summary table
    st.markdown("**Summary**")
    summary_data = []
    for i, s in st.session_state.edited.items():
        summary_data.append({
            "#":        i + 1,
            "Title":    s.get("title", ""),
            "Priority": s.get("priority", ""),
            "Status":   "✅ Approved" if st.session_state.approved.get(i) else "❌ Rejected"
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

    st.divider()

    # Push button
    approved_scenarios = [
        st.session_state.edited[i]
        for i in range(len(scenarios))
        if st.session_state.approved.get(i)
    ]

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        push_disabled = len(approved_scenarios) == 0
        push_btn = st.button(
            f"📤 Push {len(approved_scenarios)} to Jira",
            type             = "primary",
            use_container_width = True,
            disabled         = push_disabled
        )

    if push_btn:
        with st.spinner(f"Creating {len(approved_scenarios)} test cases in Jira..."):
            pipeline    = st.session_state.pipeline or load_pipeline()
            pushed_keys = pipeline.push_scenarios(approved_scenarios, issue["key"])
            st.session_state.pushed_keys = pushed_keys
            st.session_state.page        = "done"
            st.rerun()

# ══════════════════════════════════════════════════════════
# PAGE 4 — Done
# ══════════════════════════════════════════════════════════
elif st.session_state.page == "done":
    from reporting.report_generator import ReportGenerator
    import webbrowser

    issue = st.session_state.selected_issue
    keys  = st.session_state.pushed_keys

    # Mark approved/rejected on scenarios for report
    all_scenarios = st.session_state.scenarios
    for i, s in enumerate(all_scenarios):
        s["_approved"] = st.session_state.approved.get(i, True)

    st.title("✅ Done!")
    st.success(f"{len(keys)} test cases created in Jira for {issue['key']}")

    # Generate reports
    reporter = ReportGenerator()
    paths    = reporter.generate(issue, all_scenarios, keys)

    st.divider()

    # Show created Jira keys
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Created test cases**")
        base_url = st.session_state.pipeline.creator.client.base.replace(
            "/rest/api/3", "")
        for k in keys:
            st.markdown(f"- [{k}]({base_url}/browse/{k})")

    with col2:
        st.markdown("**Reports**")
        st.markdown(f"📄 HTML: `{paths['html']}`")
        st.markdown(f"📊 CSV:  `{paths['csv']}`")
        st.markdown(f"🗂️  JSON: `{paths['json']}`")

    st.divider()

    # Download buttons
    dc1, dc2, dc3 = st.columns(3)

    with open(paths["html"], "r", encoding="utf-8") as f:
        dc1.download_button("⬇️ Download HTML", f.read(),
                            file_name="qa_report.html",
                            mime="text/html",
                            use_container_width=True)

    with open(paths["csv"], "r", encoding="utf-8") as f:
        dc2.download_button("⬇️ Download CSV", f.read(),
                            file_name="qa_report.csv",
                            mime="text/csv",
                            use_container_width=True)

    with open(paths["json"], "r", encoding="utf-8") as f:
        dc3.download_button("⬇️ Download JSON", f.read(),
                            file_name="qa_report.json",
                            mime="application/json",
                            use_container_width=True)

    st.divider()

    # Post summary as Jira comment
    if st.button("💬 Post summary to Jira", type="primary"):
        comment = reporter.build_jira_comment(all_scenarios, keys)
        pipeline = st.session_state.pipeline
        pipeline.creator.add_comment(issue["key"], comment)
        st.success(f"Summary posted as comment on {issue['key']}")

    st.divider()

    if st.button("▶ Run another issue", use_container_width=True):
        st.session_state.page           = "home"
        st.session_state.selected_issue = None
        st.session_state.scenarios      = []
        st.session_state.approved       = {}
        st.session_state.edited         = {}
        st.session_state.pushed_keys    = []
        st.rerun()