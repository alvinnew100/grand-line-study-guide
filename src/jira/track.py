import pathlib as _pl
import re as _re

_HERE = _pl.Path(__file__).parent
_DEFINED = set()
for _f in (_HERE / "problems").glob("*.py"):
    _DEFINED.update(_re.findall(r'^\s*id="(jira-[a-z0-9-]+)"', _f.read_text(encoding="utf-8"), _re.M))


def _m(mid, title, summary, lessons, problems=()):
    return dict(
        id=mid, title=title, summary=summary,
        lessons=[dict(id=i, title=t, file=f) for i, t, f in lessons if (_HERE / "lessons" / f).exists()],
        problems=[p for p in problems if p in _DEFINED],
    )


TRACK = dict(
    id="jira",
    title="Jira & Agile Delivery",
    icon="🗂️",
    color="#2684ff",
    group="Engineering Practice",
    blurb="Agile, Scrum and Kanban from the official guides, then Jira the way engineering teams really use it: "
          "work items, workflows, boards, sprints, JQL, reports and their misuse, automation and smart commits - "
          "with interactive boards, a JQL playground and auto-graded metric and query problems.",
    sources=[
        "Schwaber & Sutherland, The Scrum Guide (2020), https://scrumguides.org/scrum-guide.html",
        "The Kanban Guide (May 2025), https://kanbanguides.org/english/",
        "Manifesto for Agile Software Development and its principles, https://agilemanifesto.org/",
        "Atlassian Support, Jira Cloud documentation (JQL, workflows, boards, reports, smart commits, automation)",
        "Atlassian Agile Coach, https://www.atlassian.com/agile",
        "DORA metrics guide, https://dora.dev/guides/dora-metrics/",
    ],
    modules=[
        _m("agile-foundations", "1. Agile and Scrum Foundations",
           "What agile means, how Scrum is built on empiricism, and who is accountable for what.",
           [("agile-values", "What agile is: four values, twelve principles", "01-agile-values.md"),
            ("scrum-theory", "Scrum theory: empiricism, pillars and values", "02-scrum-theory.md"),
            ("scrum-accountabilities", "Scrum accountabilities: Developers, Product Owner, Scrum Master", "03-scrum-accountabilities.md")]),
        _m("scrum-events-artifacts", "2. Scrum Events and Artifacts",
           "The five events with their timeboxes, the three artifacts and the commitment attached to each.",
           [("scrum-events", "The Scrum events and their timeboxes", "04-scrum-events.md"),
            ("artifacts-commitments", "Artifacts and commitments: Product Goal, Sprint Goal, Definition of Done", "05-artifacts-commitments.md")],
           ["jira-sprint-capacity", "jira-dod-check"]),
        _m("kanban", "3. Kanban and Flow",
           "Visualising work, limiting work in progress, pulling, and the four flow measures.",
           [("kanban-flow", "Kanban: workflow, WIP limits, pull and service level expectations", "06-kanban-flow.md")],
           ["jira-wip-check", "jira-throughput-age"]),
        _m("backlog-craft", "4. Backlog Craft",
           "Writing user stories, splitting epics into small slices, and estimating with story points.",
           [("user-stories", "User stories, INVEST and acceptance criteria", "07-user-stories.md"),
            ("epics-splitting", "Epics, stories, initiatives and splitting work", "08-epics-splitting.md"),
            ("estimation", "Estimation: story points, planning poker and their limits", "09-estimation.md")],
           ["jira-planning-poker", "jira-hierarchy-rollup"]),
        _m("jira-fundamentals", "5. Jira Fundamentals",
           "What Jira is, its data model of spaces, work types and fields, and the two kinds of space.",
           [("what-is-jira", "What Jira is: sites, spaces, keys and the new names", "10-what-is-jira.md"),
            ("data-model", "The Jira data model: work types, hierarchy and fields", "11-data-model.md"),
            ("team-company-managed", "Team-managed and company-managed spaces", "12-team-company-managed.md")],
           ["jira-issue-keys"]),
        _m("workflows-boards", "6. Workflows, Boards and Sprints",
           "Statuses and transitions, boards with column mapping and WIP limits, and running sprints in Jira.",
           [("workflows", "Workflows: statuses, transitions and status categories", "13-workflows.md"),
            ("boards", "Boards: columns, WIP limits, swimlanes and quick filters", "14-boards.md"),
            ("sprints-in-jira", "Backlog refinement and sprint planning in Jira", "15-sprints-in-jira.md")],
           ["jira-workflow-transitions"]),
        _m("jql", "7. Jira Query Language",
           "Searching with JQL from the first clause to history operators, then saving filters and building dashboards.",
           [("jql-basics", "JQL basics: field, operator, value", "16-jql-basics.md"),
            ("jql-operators", "JQL operators in depth", "17-jql-operators.md"),
            ("jql-functions-dates", "JQL functions, dates and ordering", "18-jql-functions-dates.md"),
            ("jql-advanced", "Advanced JQL: history, hierarchy and board filters", "19-jql-advanced.md"),
            ("filters-dashboards", "Filters, subscriptions and dashboards", "20-filters-dashboards.md")],
           ["jira-jql-tokenize", "jira-jql-clause", "jira-jql-boolean", "jira-jql-order-by"]),
        _m("reports-metrics", "8. Reports and Metrics",
           "Burndown, burnup, velocity and the sprint report; cumulative flow, control charts, forecasting and DORA.",
           [("scrum-reports", "Scrum reports and how they are misused", "21-scrum-reports.md"),
            ("flow-metrics", "Flow reports, forecasting and DORA", "22-flow-metrics.md")],
           ["jira-velocity", "jira-sprint-report", "jira-burndown", "jira-burnup", "jira-cycle-lead-time",
            "jira-control-chart", "jira-cfd", "jira-monte-carlo-how-many", "jira-monte-carlo-when"]),
        _m("automation-integration", "9. Automation and Developer Tools",
           "Automation flows, issue keys in branches and commits, smart commits and permissions.",
           [("automation", "Automation: triggers, conditions, actions and branches", "23-automation.md"),
            ("dev-integration", "Jira and your code: keys, smart commits and permissions", "24-dev-integration.md")],
           ["jira-smart-commit"]),
        _m("in-practice", "10. In Practice and in Interviews",
           "A sprint from planning to retrospective, service desks and scaling, and the questions interviewers ask.",
           [("day-in-the-life", "A sprint in the life of an engineer, service desks and scaling", "25-day-in-the-life.md"),
            ("interview-readiness", "Interview readiness: process and behavioural questions", "26-interview-readiness.md")]),
    ],
)
TRACK["modules"] = [m for m in TRACK["modules"] if m["lessons"]]
