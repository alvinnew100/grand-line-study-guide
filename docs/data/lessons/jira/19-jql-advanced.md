# Advanced JQL: history, hierarchy and board filters

> **Before this lesson:** read [JQL operators in depth](#/lesson/jira/jql-operators) and [JQL functions, dates and ordering](#/lesson/jira/jql-functions-dates). You should be comfortable with `IN`, `IS EMPTY`, `currentUser()` and date functions.

## In plain words

A normal search asks about the present: "Which bugs are open now?" Some of the most useful questions are about the past: "Which bugs were reopened after being closed?", "Who moved this to Done?", "Which items did the team have in progress on the last day of the sprint?". A photo shows the present; a video shows how things changed.

Jira keeps a **history** of every change to every work item, and JQL's **history operators**, `WAS` and `CHANGED`, let you search that video. This lesson also covers searching the **hierarchy** (children of an epic) and writing good **board filters**, the queries that decide what every board and report shows.

Why it matters for a job: questions such as "how often do we reopen bugs?" or "what changed priority this week?" come up in retrospectives, incident reviews and audits. The person who can answer them with a precise query, rather than a guess, is trusted with process decisions.

## History operators

From Atlassian's operator documentation:

| Operator | Matches items whose field... | Example |
|---|---|---|
| `WAS` | has or previously had a value | `status WAS "In Review"` |
| `WAS IN` | has or previously had any of the values | `status WAS IN ("In Review", "QA")` |
| `WAS NOT` | has never had the value | `status WAS NOT "In Review"` |
| `WAS NOT IN` | has never had any of the values | `status WAS NOT IN ("In Review", "QA")` |
| `CHANGED` | changed (optionally from, to, by, or at a time) | `priority CHANGED` |

History operators work on a limited set of fields. Atlassian lists **Assignee, Fix Version, Priority, Reporter, Resolution and Status**. You cannot, for example, ask whether `labels WAS cny` or whether the summary changed.

### Predicates: narrowing when and by whom

History clauses can take **predicates**, extra words that narrow the change:

| Predicate | Meaning | Example |
|---|---|---|
| `AFTER date` | after a moment | `status CHANGED AFTER startOfWeek()` |
| `BEFORE date` | before a moment | `status WAS "In Progress" BEFORE "2026-03-01"` |
| `ON date` | on a given day | `assignee CHANGED ON "2026-03-05"` |
| `DURING (date1, date2)` | within a period | `status WAS "In Review" DURING ("2026-03-02", "2026-03-06")` |
| `BY user` | made by that person | `status CHANGED BY wei` |
| `FROM value` / `TO value` | the old and new value (for `CHANGED`) | `status CHANGED FROM "Done" TO "In Progress"` |

Predicates can be combined: `status CHANGED FROM "In Progress" TO "Done" BY currentUser() AFTER startOfWeek()`.

### How WAS and CHANGED think: a worked history

To see exactly what these operators match, take one work item's history:

| When | Field | From | To | By |
|---|---|---|---|---|
| 2 Mar 09:00 | Status | To Do | In Progress | farah |
| 4 Mar 15:00 | Status | In Progress | In Review | farah |
| 5 Mar 10:00 | Status | In Review | Done | wei |
| 7 Mar 11:00 | Priority | Medium | High | siti |
| 8 Mar 14:00 | Status | Done | In Progress | farah |

This item was finished on 5 March and **reopened** on 8 March. Checking clauses against it:

| Clause | Matches? | Why |
|---|---|---|
| `status = Done` | No | Its current status is In Progress |
| `status WAS Done` | Yes | It was Done between 5 and 8 March |
| `status WAS NOT "QA"` | Yes | It has never been in QA |
| `status CHANGED FROM Done TO "In Progress"` | Yes | The reopen on 8 March |
| `status CHANGED BY wei` | Yes | Wei moved it to Done |
| `status WAS "In Review" ON "2026-03-06"` | No | On 6 March it was Done |
| `status WAS "In Review" ON "2026-03-04"` | Yes | It entered In Review on 4 March |
| `priority CHANGED AFTER "2026-03-06"` | Yes | Changed on 7 March |
| `assignee CHANGED` | No | No assignee change in this history |

Here is the same reasoning in code. Edit the history or the questions and run it.

```python-run
from datetime import datetime as dt

history = [  # (when, field, from, to, by)
    (dt(2026, 3, 2, 9),  "status",   "To Do",       "In Progress", "farah"),
    (dt(2026, 3, 4, 15), "status",   "In Progress", "In Review",   "farah"),
    (dt(2026, 3, 5, 10), "status",   "In Review",   "Done",        "wei"),
    (dt(2026, 3, 7, 11), "priority", "Medium",      "High",        "siti"),
    (dt(2026, 3, 8, 14), "status",   "Done",        "In Progress", "farah"),
]
created, first_status = dt(2026, 3, 1, 8), "To Do"

def values_over_time(field, initial):
    """List of (start, end, value) intervals for one field."""
    spans, start, value = [], created, initial
    for when, f, old, new, _ in history:
        if f == field:
            spans.append((start, when, value))
            start, value = when, new
    spans.append((start, dt.max, value))
    return spans

def was(field, initial, value, on_day=None):
    for start, end, v in values_over_time(field, initial):
        if v != value:
            continue
        if on_day is None:
            return True
        day_start, day_end = on_day, on_day.replace(hour=23, minute=59)
        if start <= day_end and end > day_start:
            return True
    return False

def changed(field, frm=None, to=None, by=None, after=None):
    return any(f == field and (frm is None or old == frm) and (to is None or new == to)
               and (by is None or who == by) and (after is None or when > after)
               for when, f, old, new, who in history)

print("status WAS Done                        :", was("status", first_status, "Done"))
print("status WAS 'In Review' ON 2026-03-06   :", was("status", first_status, "In Review", dt(2026, 3, 6)))
print("status WAS 'In Review' ON 2026-03-04   :", was("status", first_status, "In Review", dt(2026, 3, 4)))
print("status CHANGED FROM Done TO In Progress:", changed("status", "Done", "In Progress"))
print("status CHANGED BY wei                  :", changed("status", by="wei"))
print("assignee CHANGED                       :", changed("assignee"))
```

The script prints the same answers as the table. It is a simplified model, not Jira's implementation, but it shows the idea: `WAS` looks at the intervals during which a field held a value; `CHANGED` looks at individual change events.

## Useful history queries

| Question | JQL |
|---|---|
| Bugs reopened after being done | `type = Bug AND status CHANGED FROM Done TO "In Progress"` |
| Anything ever reopened this month | `status CHANGED FROM Done AFTER startOfMonth()` |
| What I moved to Done this week | `status CHANGED TO Done BY currentUser() AFTER startOfWeek()` |
| Items whose priority was raised recently | `priority CHANGED AFTER "-7d"` |
| Items that skipped code review | `statusCategory = Done AND status WAS NOT "In Review"` |
| Work that was assigned to wei at some point | `assignee WAS wei` |
| Items in progress on a given day | `status WAS "In Progress" ON "2026-03-06"` |
| Items moved out of a release | `fixVersion CHANGED FROM "2026.04"` |

"Items that skipped code review" is a favourite for engineering leads: it checks a Definition of Done rule ("every change is reviewed") against the actual history, without trusting anyone's memory.

> [!WARNING]
> History queries are powerful but can be slow on very large sites, and they only see fields Jira tracks for history (the six listed above). If a question needs other fields over time, export the data or use the API, or use the problems in this track's reports module as a model for computing it yourself.

## Searching the hierarchy

Lesson 8 introduced the hierarchy: Epic (level 1), standard types such as Story, Task and Bug (level 0), and Sub-task (level -1), joined by the `parent` field.

**Children of one parent:**

```text
parent = SHOP-10
```

Sample data (lesson 16): SHOP-1, SHOP-2, SHOP-3, the three items under the "Promo codes" epic.

**Children of several parents:**

```text
parent IN (SHOP-10, SHOP-20)
```

**Open children of an epic, by status:**

```text
parent = SHOP-10 AND statusCategory != Done ORDER BY status
```

Sample data: SHOP-2 (In Progress), SHOP-3 (To Do).

**Items with no epic.** `parent IS EMPTY` is not available, because Atlassian lists `IS` and `IS NOT` as unsupported for `parent`. A supported route takes two steps: first list the children, then exclude them by key.

```text
project = SHOP AND parent IN (SHOP-10, SHOP-20)
```

```text
project = SHOP AND type IN (Story, Task, Bug) AND key NOT IN (SHOP-1, SHOP-2, SHOP-3)
```

Paste the keys returned by the first query into the second (here the three items under the "Promo codes" epic), which leaves SHOP-4, SHOP-5, SHOP-6 in the sample data. For a whole-site view, the hierarchy-aware screens on higher Jira plans are the other route. Useful in refinement: work floating without a home is often work nobody prioritised.

**By level.** `type = Epic` finds epics under the default hierarchy. Jira Cloud's field reference also describes a `hierarchyLevel` field for searching by level number, for example `hierarchyLevel = 1` for epics or `hierarchyLevel = -1` for sub-tasks, which keeps working if your site renames or adds work types. Check that your site supports it; `type = ...` works everywhere.

> [!NOTE]
> Old filters may contain `"Epic Link" = SHOP-10`. Epic Link was retired in February 2024; rewrite such clauses as `parent = SHOP-10`.

`parent` supports only `=`, `!=`, `IN` and `NOT IN` (Atlassian's Jira Cloud field reference lists `IS`, `IS NOT`, `~`, `!~` and comparison operators as unsupported for it), so you cannot write `parent > SHOP-10` or `parent IS EMPTY`. To find grandchildren (sub-tasks under an epic's stories), you usually need two steps: find the stories, then search `parent IN (...)` with their keys, or use a plan-level feature on higher Jira plans.

## Board filters: the queries behind every board

Every board is built on a saved filter (lesson 14). A good board filter is:

1. **Scoped**: it selects exactly the team's work. Often `project = SHOP`; for teams sharing a space, add `component = Checkout` or a team field.
2. **Ordered by rank**: boards and backlogs use the rank order, so board filters end with `ORDER BY Rank ASC`. Without rank ordering, drag-and-drop ranking on the board does not work as expected.
3. **Lean**: it does not pull in years of resolved work.

Examples:

```text
project = SHOP ORDER BY Rank ASC
```

A one-team, one-space board.

```text
project IN (SHOP, PAY) AND component = Checkout ORDER BY Rank ASC
```

A cross-space board for a checkout team whose work lives in two spaces.

```text
project = OPS AND (resolution IS EMPTY OR resolved >= "-14d") ORDER BY Rank ASC
```

An operations Kanban board showing all open work plus anything resolved in the last two weeks, keeping the Done column short.

Company-managed Kanban boards also offer a **sub-filter** in their settings, commonly used to hide items belonging to versions that have already been released.

> [!WARNING]
> Changing a board's filter changes its reports, including past sprints' burndowns and velocity. Agree changes with the team, and note them in the retrospective, so nobody misreads the next velocity chart.

## Putting it together: a retrospective investigation

At a retrospective, the SHOP team feels that "QA keeps bouncing things back". Instead of arguing, the Scrum Master runs three queries over the last sprint period (2 to 13 March):

1. How many items went into QA?
   `project = SHOP AND status WAS QA DURING ("2026-03-02", "2026-03-13")` → 18 items.
2. How many bounced back?
   `project = SHOP AND status CHANGED FROM QA TO "In Progress" DURING ("2026-03-02", "2026-03-13")` → 7 items.
3. Which areas?
   The same query with `ORDER BY component` shows 6 of the 7 are in the Payments component.

Seven of eighteen is a high bounce rate, concentrated in one component. The team agrees on an experiment: the QA engineer joins refinement for Payments stories to agree test cases before development starts. Two sprints later the same queries show 2 bounces out of 16. The history operators turned a feeling into a measurable improvement.

## How interviewers probe this

> [!INTERVIEW]
> "How would you find out how many bugs were reopened last quarter?" Use a history operator with a date range and explain the limits: `type = Bug AND status CHANGED FROM Done TO "In Progress" DURING ("2026-01-01", "2026-03-31")`, adjusting the status names to the team's workflow. "History operators work on status, assignee, priority, reporter, resolution and fix version, so this is answerable directly in JQL."

Other likely questions:

- "What's the difference between `status WAS X` and `status = X`?" `WAS` includes past values; `=` checks only the current value.
- "How would you list all stories under an epic?" `parent = EPIC-KEY`, since Epic Link was replaced by `parent`.
- "What should a board filter end with?" `ORDER BY Rank ASC`, so the board uses the backlog's rank order.

## Summary

- History operators search the past: `WAS`, `WAS IN`, `WAS NOT`, `WAS NOT IN` and `CHANGED`.
- They work on Assignee, Fix Version, Priority, Reporter, Resolution and Status.
- Predicates narrow history clauses: `AFTER`, `BEFORE`, `ON`, `DURING`, `BY`, and `FROM` / `TO` for `CHANGED`.
- `WAS` reasons about the periods a value was held; `CHANGED` reasons about individual change events.
- Search the hierarchy with `parent = KEY`, `parent IN (...)`; there is no `parent IS EMPTY`, so find orphans by excluding known children; Jira Cloud also documents `hierarchyLevel`.
- Board filters should be scoped, lean and end with `ORDER BY Rank ASC`; changing them changes every report.

## Glossary

- **History** — the record of every change made to a work item.
- **History operator** — `WAS`, `WAS IN`, `WAS NOT`, `WAS NOT IN` or `CHANGED`.
- **Predicate** — a word that narrows a history clause by time, person or values (`AFTER`, `BEFORE`, `ON`, `DURING`, `BY`, `FROM`, `TO`).
- **Reopen** — a move from a done status back to an active one.
- **Bounce** — an item sent back from a later stage (such as QA) to an earlier one.
- **`parent`** — the field linking an item to the one above it in the hierarchy.
- **`hierarchyLevel`** — a Jira Cloud field for searching by hierarchy level number.
- **Board filter** — the saved query behind a board.
- **Sub-filter** — an extra filter on company-managed Kanban boards, often hiding released work.
- **Rank** — the backlog order that boards use.

## Check yourself

```quiz
[
  {"q": "An item was Done last week and is now In Progress. Does `status WAS Done` match it?",
   "options": ["No, it is not Done now", "Yes, WAS includes past values", "Only if it was Done today", "Only with a BY predicate"],
   "answer": 1,
   "explain": "WAS matches current or previous values."},
  {"q": "Which fields support history operators according to Atlassian?",
   "options": ["Every field", "Assignee, Fix Version, Priority, Reporter, Resolution and Status", "Only Status", "Labels and Components"],
   "answer": 1,
   "explain": "History search is limited to those six fields."},
  {"q": "Which query finds bugs that were reopened?",
   "options": ["`type = Bug AND status = Reopened`", "`type = Bug AND status CHANGED FROM Done TO \"In Progress\"`", "`type = Bug AND status WAS NOT Done`", "`type = Bug AND resolution IS EMPTY`"],
   "answer": 1,
   "explain": "CHANGED FROM ... TO ... finds the reopen transition itself (adjust status names to your workflow)."},
  {"q": "What does `statusCategory = Done AND status WAS NOT \"In Review\"` find?",
   "options": ["Items still in review", "Finished items that never went through In Review", "Items reviewed twice", "Nothing; it is invalid"],
   "answer": 1,
   "explain": "It checks history for a missing step, useful for auditing a review rule."},
  {"q": "What replaced `\"Epic Link\" = SHOP-10` in current Jira Cloud?",
   "options": ["`epic = SHOP-10`", "`parent = SHOP-10`", "`labels = SHOP-10`", "`linkedIssues(SHOP-10)`"],
   "answer": 1,
   "explain": "Epic Link was retired in February 2024 in favour of parent."},
  {"q": "Why should a board filter end with `ORDER BY Rank ASC`?",
   "options": ["Jira rejects filters without it", "Boards and backlogs rely on rank order for ranking work", "It hides resolved items", "It speeds up history queries"],
   "answer": 1,
   "explain": "Rank is the backlog order; boards use it for drag-and-drop ordering."},
  {"q": "Which predicate restricts `CHANGED` to changes made by a particular person?",
   "options": ["FROM", "BY", "DURING", "ON"],
   "answer": 1,
   "explain": "BY user limits the change to that person."}
]
```

> **Source:** Atlassian, JQL operators (history operators and predicates), https://support.atlassian.com/jira-software-cloud/docs/jql-operators/; Atlassian, JQL fields (parent, hierarchyLevel), https://support.atlassian.com/jira-software-cloud/docs/jql-fields/; Jira Data Center operators reference, https://confluence.atlassian.com/jirasoftwareserver/advanced-searching-operators-reference-939938745.html; Jira Data Center fields reference, https://confluence.atlassian.com/jirasoftwareserver/advanced-searching-fields-reference-939938743.html; Atlassian, Configure the issue type hierarchy, https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/; Atlassian, What is a Jira board, https://support.atlassian.com/jira-software-cloud/docs/what-is-a-jira-software-board/
