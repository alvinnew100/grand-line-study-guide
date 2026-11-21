# JQL functions, dates and ordering

> **Before this lesson:** read [JQL basics](#/lesson/jira/jql-basics) and [JQL operators in depth](#/lesson/jira/jql-operators). The sample items and playground from lesson 16 are used again here.

## In plain words

A saved shopping list that says "buy milk on 3 March" is useless on 10 March. A list that says "buy milk every week" stays useful forever. The difference is between a **fixed** value and a **relative** one.

JQL **functions** give you relative values. Instead of writing `assignee = farah` you write `assignee = currentUser()`, and the same query works for every person who runs it. Instead of `created >= "2026-03-09"` you write `created >= startOfWeek()`, and the query always means "this week". Instead of naming Sprint 14 you write `sprint in openSprints()`, and the query follows the team from Sprint to Sprint.

This lesson covers the functions engineers use most (people, sprints, versions, links and dates) and finishes with `ORDER BY`.

Why it matters for a job: saved filters, dashboards and board quick filters are reused for months. If they contain fixed names and dates, they quietly go stale. Functions keep them correct. A shared dashboard built on `currentUser()` gives every viewer their own view.

## What a function is

A **function** is a named value that Jira computes when the query runs. It is written as a name followed by parentheses, sometimes with arguments inside:

```text
currentUser()
startOfWeek("-1w")
linkedIssues(SHOP-1042)
```

Functions appear in the **value** position of a clause. Some return one value (used with `=`, `>` and similar), others return a list (used with `IN` or `NOT IN`):

```text
assignee = currentUser()                    one value
sprint in openSprints()                     a list of sprints
fixVersion in unreleasedVersions()          a list of versions
```

## People functions

| Function | Returns | Example | Reads as |
|---|---|---|---|
| `currentUser()` | The person running the query | `assignee = currentUser()` | Assigned to me |
| `membersOf("group")` | Everyone in a user group | `assignee in membersOf("payments-team")` | Assigned to anyone in the payments team |
| `updatedBy(user, from, to)` | Items that user updated (optionally in a date range) | `issuekey in updatedBy(wei, "-8d")` | Items Wei touched in the last 8 days |

`currentUser()` is the most important function in Jira. One shared filter, "My open work":

```text
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC
```

works for every engineer on the team. In the lesson 16 sample data, where the current user is farah, it returns SHOP-2.

`membersOf()` turns team membership into a search, so filters keep working when people join or leave, as long as the group is maintained.

## Sprint functions

| Function | Returns |
|---|---|
| `openSprints()` | Sprints that are currently active |
| `closedSprints()` | Sprints that have been completed |
| `futureSprints()` | Sprints that have been created but not started |

Examples:

```text
project = SHOP AND sprint in openSprints()
```

The SHOP team's current sprint work. Note the `project` clause: `openSprints()` returns active sprints on **every** board you can see, so without narrowing you would get other teams' sprints too.

```text
project = SHOP AND sprint in openSprints() AND statusCategory = "To Do"
```

Work in the current sprint that has not started, a useful mid-sprint check.

```text
project = SHOP AND sprint in openSprints() AND sprint in closedSprints()
```

Items in the current sprint that were **also** in a completed sprint: carried-over work. The `sprint` field can hold several sprints for one item, which is why both conditions can be true at once.

```text
project = SHOP AND sprint in futureSprints() AND "Story Points" IS EMPTY
```

Items planned for an upcoming sprint that still have no estimate, a refinement checklist in one query. (Use your site's name for the story point field.)

## Version functions

| Function | Returns |
|---|---|
| `unreleasedVersions()` / `unreleasedVersions(SHOP)` | Versions not yet released, optionally for one space |
| `releasedVersions()` / `releasedVersions(SHOP)` | Versions already released |
| `earliestUnreleasedVersion(SHOP)` | The next upcoming release |
| `latestReleasedVersion(SHOP)` | The most recent release |

Examples:

```text
fixVersion = earliestUnreleasedVersion(SHOP) AND statusCategory != Done
```

What is still outstanding for the next release, the classic release-readiness query.

```text
fixVersion = latestReleasedVersion(SHOP) AND type = Bug
```

Bugs fixed in the last release, ready for release notes.

## Link and history functions

| Function | Returns | Example |
|---|---|---|
| `linkedIssues(KEY)` / `linkedIssues(KEY, "link type")` | Items linked to a given item | `issue in linkedIssues(SHOP-1042, "is blocked by")` |
| `issueHistory()` | Items you viewed recently | `issue in issueHistory() ORDER BY lastViewed DESC` |

> **Newer names.** Current Jira Cloud documentation also lists work-item names for these functions: `linkedWorkItems()`, `workItemHistory()`, `watchedWorkItems()`, `votedWorkItems()` and `standardWorkTypes()`. The older names (`linkedIssues()`, `issueHistory()`, and so on) still work, so this track keeps the long-established forms, as lesson 16 does for `space`.

`linkedIssues()` is perfect for dependency checks: "which items are blocking SHOP-1042, and are they done?"

```text
issue in linkedIssues(SHOP-1042, "is blocked by") AND statusCategory != Done
```

`issueHistory()` answers "what was that ticket I looked at this morning?"

## Dates: absolute, relative and calendar functions

Date fields include `created`, `updated`, `resolved` and `due` (also written `duedate`). There are three ways to give a date value.

**1. Absolute dates**, quoted, in a format such as `"2026-03-01"`, `"2026/03/01"` or with a time `"2026-03-01 14:30"`:

```text
created >= "2026-03-01" AND created < "2026-04-01"
```

Everything created in March 2026.

**2. Relative offsets** from now, quoted, using units such as `w` (weeks), `d` (days), `h` (hours) and `m` (minutes):

```text
updated >= "-2w"            updated in roughly the last two weeks
resolved >= "-7d"           resolved in roughly the last seven days
due <= "3d"                 due within the next three days (no minus sign means the future)
```

**3. Calendar functions**, which snap to boundaries of days, weeks, months and years:

| Function | Meaning |
|---|---|
| `startOfDay()`, `endOfDay()` | Midnight at the start or end of today |
| `startOfWeek()`, `endOfWeek()` | Start or end of this week |
| `startOfMonth()`, `endOfMonth()` | Start or end of this month |
| `startOfYear()`, `endOfYear()` | Start or end of this year |
| `now()` | This exact moment |

Each calendar function accepts an optional **increment** in quotes. According to Atlassian's function reference, the units are `y` (years), `M` (months, capital M), `w` (weeks), `d` (days), `h` (hours) and `m` (minutes, lower-case m). A missing sign means plus, and a missing unit means the function's own period:

```text
startOfWeek("-1w")      start of last week
startOfWeek("-1")       the same: the unit defaults to weeks for startOfWeek
startOfMonth("-1M")     start of last month
startOfDay("+1d")       midnight at the start of tomorrow
```

The first day of the week is **not** taken from your locale. By default `startOfWeek()` treats Sunday as the first day, unless ISO8601 is enabled for the date picker in Look and feel settings. To get Monday regardless, add an offset of one day: `startOfWeek("+1d")`. Everything below that says "weeks start Monday" assumes ISO8601 is enabled on the site or that you use the `"+1d"` form.

### Relative offset or calendar function?

They answer different questions, and mixing them up is a classic bug.

```python-run
from datetime import datetime, timedelta

now = datetime(2026, 3, 10, 15, 30)                 # a Tuesday afternoon
start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0)  # Monday start (assumes ISO8601 or the "+1d" form)
print("now                    :", now)
print('"-7d"  (rolling 7 days):', now - timedelta(days=7))
print("startOfWeek()          :", start_of_week)
print('startOfWeek("-1w")     :', start_of_week - timedelta(weeks=1))
print("last week, as a range  :", start_of_week - timedelta(weeks=1), "to", start_of_week)
```

On a Tuesday afternoon, `"-7d"` reaches back to last Tuesday afternoon, while `startOfWeek()` is this Monday at midnight (with Monday weeks, as above). For "what did we resolve last week?" use the calendar boundaries, so the answer is the same whenever you run it during the week:

```text
resolved >= startOfWeek("-1w") AND resolved < startOfWeek()
```

For "anything that changed recently", a rolling window such as `updated >= "-24h"` or `"-7d"` is fine.

### Worked date examples on the sample data

With "today" as Tuesday 2026-03-10 (week starting Monday, which assumes ISO8601 is enabled or `startOfWeek("+1d")` is used):

| Query | Result | Why |
|---|---|---|
| `created >= startOfWeek()` | PAY-7 | Only PAY-7 was created on or after Monday 9 March |
| `created >= startOfWeek("-1w")` | SHOP-2, SHOP-3, SHOP-4, PAY-7 | Created on or after Monday 2 March |
| `created >= startOfMonth()` | SHOP-2, SHOP-3, SHOP-4, PAY-7 | Created in March |
| `created >= startOfMonth("-1M") AND created < startOfMonth()` | SHOP-1, SHOP-5, SHOP-6, SHOP-10, PAY-8 | Created in February |

The lesson 16 playground supports relative offsets like `-7d` but not the calendar functions, so try the absolute equivalents there (for example `created >= "2026-03-02"`).

## ORDER BY in depth

`ORDER BY` sorts results. Rules from Atlassian's keyword documentation:

- It must be the **last** part of the query.
- Several fields are separated by commas and applied in order: the second field breaks ties in the first.
- Each field can be followed by `ASC` or `DESC`. Without one, the field's **default** sort order is used.
- Sorting by components or versions lists results by space first, then by the field's natural order.

Useful orderings:

| ORDER BY | Purpose |
|---|---|
| `ORDER BY Rank ASC` | The backlog order set by the Product Owner; boards use this |
| `ORDER BY priority DESC, created ASC` | Most urgent first, oldest first within a priority: a fair triage queue |
| `ORDER BY updated DESC` | Most recently changed first: "what's happening?" |
| `ORDER BY due ASC` | Nearest deadline first |
| `ORDER BY created DESC` | Newest first, for incoming bug queues |

Example on the sample data:

```text
statusCategory != Done ORDER BY priority DESC, created ASC
```

Result order: PAY-7 and SHOP-2 are both Highest, so `created ASC` puts SHOP-2 (4 March) before PAY-7 (9 March); then PAY-8 and SHOP-4 (High; PAY-8 created 27 February comes first); then SHOP-10, SHOP-6, SHOP-3 (Medium, oldest first); then SHOP-5 (Low). So: SHOP-2, PAY-7, PAY-8, SHOP-4, SHOP-10, SHOP-6, SHOP-3, SHOP-5.

The problem [Mini-JQL: ORDER BY](#/problem/jira-jql-order-by) asks you to implement multi-field ordering with a defined rule for empty values.

## A library of reusable filters

Here are queries teams commonly save. Each uses functions so it never goes stale.

| Name | JQL |
|---|---|
| My open work | `assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC` |
| Reported by me, still open | `reporter = currentUser() AND resolution = Unresolved ORDER BY updated DESC` |
| Current sprint, not started | `project = SHOP AND sprint in openSprints() AND statusCategory = "To Do"` |
| Carried over this sprint | `project = SHOP AND sprint in openSprints() AND sprint in closedSprints()` |
| Bugs created this week | `project = SHOP AND type = Bug AND created >= startOfWeek()` |
| Resolved last week | `project = SHOP AND resolved >= startOfWeek("-1w") AND resolved < startOfWeek()` |
| Next release, outstanding | `fixVersion = earliestUnreleasedVersion(SHOP) AND statusCategory != Done` |
| Overdue | `due < startOfDay() AND statusCategory != Done ORDER BY due ASC` |
| Stale in progress | `statusCategory = "In Progress" AND updated <= "-5d" ORDER BY updated ASC` |
| Team's open work | `assignee in membersOf("shop-team") AND statusCategory != Done` |

## Scenario: the release-readiness check

Mei Ling is release captain for the SHOP space's `2026.04` release, due Thursday. On Monday she builds a filter step by step:

1. `fixVersion = earliestUnreleasedVersion(SHOP)` shows all 34 items planned for 2026.04.
2. Adding `AND statusCategory != Done` leaves 6.
3. She saves it as "Next release: outstanding" and adds it to the team dashboard.
4. For one of the six, she checks blockers: `issue in linkedIssues(SHOP-1201, "is blocked by") AND statusCategory != Done` reveals a PAY bug owned by another team.
5. She subscribes the team to the filter (lesson 20), so it arrives by email each morning until release.

On Wednesday the list is down to one item, which the Product Owner moves to the next version. Because the filter uses `earliestUnreleasedVersion`, the moment 2026.04 is released the same filter starts tracking 2026.05 with no edits.

## How interviewers probe this

> [!INTERVIEW]
> "Write a filter for bugs resolved last week in the PAY space." A strong answer uses calendar functions and explains why: `project = PAY AND type = Bug AND resolved >= startOfWeek("-1w") AND resolved < startOfWeek()`. "I use week boundaries rather than -7d so the result is the same whichever day I run it."

Other likely questions:

- "How would you find work carried over from previous sprints?" `sprint in openSprints() AND sprint in closedSprints()`, narrowed by project.
- "Why use `currentUser()` instead of your name?" So a shared filter or dashboard works for everyone.
- "How do you sort a triage queue?" `ORDER BY priority DESC, created ASC`.

## Summary

- Functions compute values when the query runs, keeping saved filters correct over time.
- People: `currentUser()`, `membersOf()`, `updatedBy()`. Sprints: `openSprints()`, `closedSprints()`, `futureSprints()`. Versions: `unreleasedVersions()`, `releasedVersions()`, `earliestUnreleasedVersion()`, `latestReleasedVersion()`. Links and history: `linkedIssues()`, `issueHistory()` (newer docs also name `linkedWorkItems()`, `workItemHistory()`; the older names still work).
- Dates can be absolute (`"2026-03-01"`), relative offsets (`"-7d"`) or calendar functions (`startOfWeek("-1w")`), with units y, M, w, d, h, m.
- Use calendar boundaries for "last week" questions and rolling offsets for "recently".
- `ORDER BY` comes last, accepts several fields with `ASC` or `DESC`, and uses each field's default order otherwise; `ORDER BY Rank` is the backlog order.

## Glossary

- **Function** — a JQL value computed when the query runs, written with parentheses.
- **Argument** — a value passed into a function, such as a key or a group name.
- **`currentUser()`** — the person running the query.
- **`openSprints()`** — currently active sprints, across all boards.
- **`closedSprints()`** — completed sprints.
- **`futureSprints()`** — created but not started sprints.
- **`earliestUnreleasedVersion()`** — the next upcoming release of a space.
- **`linkedIssues()`** — items linked to a given item, optionally by link type (newer docs also call it `linkedWorkItems()`).
- **Relative date** — a date given as an offset from now, such as `"-7d"`.
- **Calendar function** — a function snapping to a day, week, month or year boundary, such as `startOfWeek()`.
- **Increment** — the optional offset passed to a calendar function, such as `"-1w"`.
- **Rank** — the backlog order; `ORDER BY Rank` sorts by it.
- **Carry-over** — an item that stays unfinished across sprints.

## Check yourself

```quiz
[
  {"q": "Why use `assignee = currentUser()` in a shared filter?",
   "options": ["It is faster", "Each person who runs it sees their own items", "It includes unassigned items", "It is required for dashboards"],
   "answer": 1,
   "explain": "currentUser() is evaluated per viewer, so one filter serves everyone."},
  {"q": "Which query finds items carried over into the current sprint?",
   "options": ["`sprint in openSprints()`", "`sprint in openSprints() AND sprint in closedSprints()`", "`sprint in futureSprints()`", "`sprint = EMPTY`"],
   "answer": 1,
   "explain": "An item in both an open and a closed sprint was in an earlier sprint and is still in progress."},
  {"q": "Why add `project = SHOP` to `sprint in openSprints()`?",
   "options": ["openSprints() needs a project argument", "openSprints() covers active sprints on all boards you can see", "It sorts the results", "It is not needed"],
   "answer": 1,
   "explain": "Without narrowing, other teams' active sprints are included."},
  {"q": "What does `startOfMonth(\"-1M\")` mean?",
   "options": ["One minute ago", "The start of last month", "The end of this month", "One month from now"],
   "answer": 1,
   "explain": "Capital M is months; lower-case m is minutes."},
  {"q": "Which query best answers 'what did we resolve last week?' consistently on any day?",
   "options": ["`resolved >= \"-7d\"`", "`resolved >= startOfWeek(\"-1w\") AND resolved < startOfWeek()`", "`resolved = startOfWeek()`", "`resolved <= now()`"],
   "answer": 1,
   "explain": "Calendar boundaries give the same answer whichever day you run the query."},
  {"q": "Using the sample data (today Tuesday 10 March, weeks start Monday, e.g. ISO8601 enabled), what does `created >= startOfWeek()` return?",
   "options": ["SHOP-2, SHOP-3, SHOP-4, PAY-7", "PAY-7", "Nothing", "Everything"],
   "answer": 1,
   "explain": "Only PAY-7 was created on or after Monday 9 March."},
  {"q": "In `ORDER BY priority DESC, created ASC`, what does `created ASC` do?",
   "options": ["It is ignored", "It breaks ties between items with the same priority, oldest first", "It sorts before priority", "It filters by date"],
   "answer": 1,
   "explain": "Later fields in ORDER BY break ties in earlier ones."}
]
```

> **Source:** Atlassian, JQL functions, https://support.atlassian.com/jira-software-cloud/docs/jql-functions/; Atlassian, JQL keywords (ORDER BY), https://support.atlassian.com/jira-software-cloud/docs/jql-keywords/; Atlassian, JQL fields, https://support.atlassian.com/jira-software-cloud/docs/jql-fields/; Jira Data Center functions reference, https://confluence.atlassian.com/jirasoftwareserver/advanced-searching-functions-reference-939938746.html; Jira Data Center fields reference, https://confluence.atlassian.com/jirasoftwareserver/advanced-searching-fields-reference-939938743.html
