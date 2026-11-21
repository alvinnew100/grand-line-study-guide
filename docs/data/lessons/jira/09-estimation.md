# Estimation: story points, planning poker and their limits

> **Before this lesson:** read [User stories, INVEST and acceptance criteria](#/lesson/jira/user-stories) and [Epics, stories, initiatives and splitting work](#/lesson/jira/epics-splitting). You should know why small stories are easier to handle.

## In plain words

If someone asks how long it takes to walk to the MRT station, you might say "about ten minutes". If they ask how long it takes to walk to an address you have never been to, in a city you do not know, you can still say "about three times as far as the MRT walk" by looking at a map. You are not certain about minutes, but you are fairly confident about *relative* size.

**Estimation** in agile teams leans on that second skill. Instead of predicting hours for each piece of work, many teams compare items with each other: "this one is about twice as big as that one". The unit they use is the **story point**, a relative measure of the overall effort needed for an item. A popular way to agree on story points as a group is **planning poker**.

Why it matters for a job: estimates feed sprint planning, release forecasts and conversations with managers about dates. Engineers are asked to estimate constantly, and interviewers ask "How does your team estimate?" and "What do you do when a manager wants a date you don't believe?". Knowing the techniques, and their limits, helps you give honest, useful answers.

> [!NOTE]
> The Scrum Guide does not mention story points or any estimation unit. It says the Developers forecast what can be done, informed by past performance, capacity and the Definition of Done. Story points are one popular way to do that; counting items is another (lesson 22).

## Why not estimate in hours?

Hour estimates look precise, but they have problems in complex work:

- **People's speeds differ.** The same task might take a senior engineer 4 hours and a new joiner 12. Whose hours?
- **Hours hide uncertainty.** "16 hours" sounds exact even when it really means "somewhere between 8 and 40".
- **Hours become promises.** Managers easily turn "about 16 hours" into "due Wednesday 5pm".
- **Humans are better at comparing than at measuring.** Most people can say which of two items is bigger far more reliably than they can predict either one's duration.

Relative estimation sidesteps these issues. The team agrees on the size of a few reference items, then sizes everything else by comparison.

Hours still have their place. Sub-tasks within a Sprint are often small enough (under a day) that hours are reasonable, and some organisations need time tracking for billing. Jira supports both styles.

## Story points

Atlassian describes **story points** as units of measure for expressing an estimate of the overall effort required to fully implement a piece of work. A story point estimate considers together:

- **Amount of work**: how much there is to do.
- **Complexity**: how hard it is to do.
- **Uncertainty or risk**: how much is unknown.

An item with little work but high uncertainty (integrating with an unfamiliar partner API) may deserve more points than one with lots of routine work.

Points are **relative to the team**. Team A's "5" and team B's "5" mean different things, in the same way that "three times the MRT walk" depends on where you start. That is why comparing points or velocity between teams is meaningless (lesson 21).

### Scales

Teams usually restrict themselves to a fixed scale so they do not argue between 7 and 8. The most common is a Fibonacci-like sequence:

```text
0, 1, 2, 3, 5, 8, 13, 20, 40, 100
```

The gaps grow as the numbers grow. That reflects reality: the bigger an item, the less precisely you can size it. Arguing whether something is 21 or 22 is false precision; choosing between 13 and 20 is honest. Many teams treat 13 or above as a signal to split the item before it enters a Sprint.

Other scales:

- **Powers of two**: 1, 2, 4, 8, 16.
- **T-shirt sizes**: XS, S, M, L, XL. Popular for rough, early sizing of epics, before detailed refinement. Not numeric, so they cannot be added up without converting.

### Reference stories

To calibrate, the team picks a few finished items as anchors:

| Reference | Points | Why |
|---|---|---|
| Add a new field to the customer profile form, saved to the DB | 2 | Familiar, well understood, touches the whole stack lightly |
| Add CSV export of transactions with date filtering | 5 | More work, a few edge cases |
| Integrate a new payment provider's refund API | 13 | Unknown API, error handling, reconciliation risk |

New items are sized by comparing: "Is this more like the profile field or the CSV export?"

## Planning poker

**Planning poker** is a consensus-based technique for estimating as a group. Each person has cards with the scale's numbers (physical cards or an app). The steps:

1. The Product Owner (or whoever knows the item best) describes the story and its acceptance criteria.
2. The team asks clarifying questions.
3. Everyone privately chooses a card.
4. All cards are revealed **at the same time**.
5. If the estimates agree or are close, that is the estimate.
6. If they differ, the people with the **highest and lowest** cards explain their reasoning.
7. The team discusses, then votes again. Usually two or three rounds are enough.

Why reveal simultaneously? To avoid **anchoring**: the tendency to be pulled towards the first number you hear. If the senior engineer says "3" first, a junior who saw a hidden risk may quietly go along with it.

Why ask the outliers? Because the spread is the valuable part. A "2" and a "13" on the same story mean two people understand it differently. Maybe the "13" knows the old code is fragile; maybe the "2" knows a library that does it already. Either way, the team learns something before it starts work. The conversation is worth more than the number.

### Try it: a planning poker round

```python-run
SCALE = [0, 1, 2, 3, 5, 8, 13, 20, 40, 100]

def round_up_to_scale(x):
    """Smallest scale value >= x (used when someone suggests an off-scale number)."""
    for s in SCALE:
        if s >= x:
            return s
    return SCALE[-1]

def review_round(votes):
    vals = sorted(votes.values())
    lo, hi = vals[0], vals[-1]
    gap = SCALE.index(round_up_to_scale(hi)) - SCALE.index(round_up_to_scale(lo))
    print("votes:", votes)
    if gap <= 1:
        # close enough: many teams take the higher of two adjacent values
        print("consensus ->", round_up_to_scale(hi))
    else:
        low = [p for p, v in votes.items() if v == lo]
        high = [p for p, v in votes.items() if v == hi]
        print("spread too wide (", lo, "to", hi, "). Ask", low, "and", high, "to explain, then vote again.")

review_round({"Aisha": 5, "Ben": 5, "Chen": 8, "Divya": 5})
review_round({"Aisha": 2, "Ben": 3, "Chen": 13, "Divya": 3})
```

The first round is within one step on the scale, so the team settles on 8 (taking the higher value is one common convention; others discuss briefly). The second round spans 2 to 13, so Aisha and Chen explain before a re-vote. The "within one step" rule here is a team convention, not a standard. The problem [Planning poker consensus](#/problem/jira-planning-poker) builds a fuller version.

## Estimation in Jira

Jira supports estimation in several ways. What you see depends on how the space is set up (lessons 11 and 12):

- **Story point estimate field.** A numeric field on stories (company-managed spaces often call it "Story Points"; team-managed spaces show "Story point estimate").
- **Time tracking.** Fields for **original estimate**, **remaining estimate** and **time logged** (also called time spent). Developers log work against items; smart commits can log time from a commit message (lesson 24).
- **Board estimation statistic.** A board chooses which value its reports use: story points, original time estimate, work item count, or another numeric field. Burndown, burnup and velocity charts all use this statistic.

Two behaviours to remember, both documented by Atlassian for the reports:

- **Story points on sub-tasks are not counted** in the burndown and velocity reports; only the parent item's estimate counts. Put points on stories, not on their sub-tasks.
- **Changing estimates mid-Sprint** shows up in the sprint report as an old and new value, so the change is visible rather than hidden.

> [!TIP]
> Decide as a team where estimates live (stories only, in points) and stick to it. Mixed habits, such as some people pointing sub-tasks, make every report wrong.

## The limits of estimation

Estimates are useful for planning and for surfacing misunderstandings. They become harmful when treated as something they are not.

**Estimates are not commitments.** A forecast of "about 30 points this Sprint" is not a promise. Treating it as one encourages padding and hiding problems, the opposite of Scrum's transparency.

**Points are not productivity.** Rewarding teams for "more points" leads to **point inflation**: the same work quietly gets bigger numbers. Velocity goes up; nothing real changes. This is **Goodhart's law** in action: when a measure becomes a target, it stops being a good measure.

**Converting points to hours defeats the purpose.** "1 point = 4 hours" turns relative estimates back into time estimates with extra steps.

**Big items are unreliable.** A 40-point estimate is a guess. Split first (lesson 8).

**Estimation takes time.** If a team spends hours debating points every week and the estimates do not change any decisions, consider simpler options: T-shirt sizes for epics, and for stories, only checking they are "small enough" and counting items.

> [!NOTE]
> Many teams, especially Kanban teams, forecast by **counting items** instead of summing points. If items are kept reasonably small, the number of items finished per week (throughput) is a strong basis for forecasts, especially with a Monte Carlo simulation (lesson 22). Some teams call this a "no estimates" approach: they still think about size, but only to decide whether an item needs splitting.

## Scenario: a manager asks for a date

Daniel, a senior engineer at a Singapore e-commerce company, is asked by his director: "How long will the new loyalty points feature take? I need a date for the board meeting."

A weak response is a single date pulled from the air. Daniel's response:

1. He checks the epic: 9 stories refined and estimated, about 48 points in total, plus 3 stories not yet refined.
2. The team's last six Sprints completed between 22 and 31 points, typically about 26.
3. 48 points at 22 to 31 per Sprint is roughly 2 Sprints; the 3 unrefined stories could add another Sprint.
4. He says: "Most likely 3 Sprints, which is mid-June. If the unrefined stories turn out small, end of May. If the partner integration is as hard as it looks, early July. We'll know much better after the spike next week. I'll update you then."

He gives a range, explains the assumptions, says what would change it, and promises an update. That is honest and useful. Lesson 22 shows how a Monte Carlo forecast turns this kind of reasoning into probabilities.

The thinking track's [Planning questions](#/lesson/thinking/planning-estimating) lesson covers how to talk through estimates and slipping deadlines in an interview.

## How interviewers probe this

> [!INTERVIEW]
> "How does your team estimate work?" Describe the method (story points with planning poker on a Fibonacci-like scale), the calibration (reference stories), and what you do with the numbers (sprint planning and rough release forecasts), then show maturity: "We treat them as forecasts, not commitments, and we split anything 13 or bigger. The most useful part is when two people vote 2 and 13, because it exposes a misunderstanding early."

Other likely questions:

- "Why story points instead of hours?" Relative sizing is more reliable, absorbs different individual speeds, and expresses uncertainty.
- "Can you compare two teams' velocities?" No; points are relative to each team.
- "Your estimate was badly wrong. What happened next?" A behavioural question: explain what you learned (hidden complexity, unclear acceptance criteria) and what you changed (a spike first, better splitting).

## Summary

- Agile estimation is usually relative: compare items instead of predicting hours.
- Story points express overall effort, combining amount of work, complexity and uncertainty, and are specific to each team.
- Fibonacci-like scales (0, 1, 2, 3, 5, 8, 13, 20, 40, 100) reflect growing uncertainty with size; large items should be split.
- Planning poker: discuss, vote privately, reveal together, let the outliers explain, re-vote. The discussion is the main value.
- Jira offers story point fields, time tracking and a per-board estimation statistic; sub-task story points are excluded from burndown and velocity.
- Estimates are forecasts, not commitments; turning points into targets causes inflation.

## Glossary

- **Estimation** — forecasting the size or duration of work.
- **Relative estimation** — sizing items by comparing them with each other.
- **Story point** — a team-specific, relative unit expressing the overall effort for an item.
- **Fibonacci-like scale** — a sequence such as 1, 2, 3, 5, 8, 13 with growing gaps, used for estimates.
- **T-shirt sizing** — rough sizing with XS, S, M, L, XL.
- **Reference story** — a finished item with an agreed size used to calibrate new estimates.
- **Planning poker** — a group technique of private votes revealed together, followed by discussion.
- **Anchoring** — being pulled towards the first number you hear.
- **Original estimate** — Jira's time-tracking field for the initial time estimate.
- **Remaining estimate** — Jira's time-tracking field for time still needed.
- **Time logged** — time recorded as spent on an item.
- **Estimation statistic** — the value a Jira board uses in its reports (story points, time, item count and so on).
- **Point inflation** — estimates growing over time without the work growing.
- **Goodhart's law** — when a measure becomes a target, it ceases to be a good measure.

## Check yourself

```quiz
[
  {"q": "What does a story point estimate combine?",
   "options": ["Hours and cost", "Amount of work, complexity and uncertainty", "Lines of code and tests", "Number of people and days"],
   "answer": 1,
   "explain": "Story points express overall effort, which includes work, complexity and risk."},
  {"q": "Why do planning poker players reveal their cards at the same time?",
   "options": ["It is faster", "To avoid anchoring on the first number said aloud", "Jira requires it", "To hide who voted what"],
   "answer": 1,
   "explain": "Simultaneous reveal keeps each estimate independent."},
  {"q": "Votes are 2, 3, 3 and 13. What should happen next?",
   "options": ["Take the average, 5.25", "The people who voted 2 and 13 explain their reasoning, then re-vote", "Take the majority, 3", "Ask the manager to decide"],
   "answer": 1,
   "explain": "A wide spread signals different understandings; the outliers explain first."},
  {"q": "Why do Fibonacci-like scales have growing gaps?",
   "options": ["They are easier to type", "Uncertainty grows with size, so fine distinctions between large numbers are false precision", "Jira only accepts these numbers", "They make velocity higher"],
   "answer": 1,
   "explain": "Large items cannot be sized precisely; the scale reflects that."},
  {"q": "A team puts story points on sub-tasks only. What happens in Jira's burndown and velocity reports?",
   "options": ["They count normally", "Those points are excluded; only parent items' estimates count", "They are doubled", "The board breaks"],
   "answer": 1,
   "explain": "Atlassian documents that sub-task story points are excluded from these reports."},
  {"q": "Team A's velocity is 40 and team B's is 20. What can you conclude?",
   "options": ["Team A is twice as productive", "Nothing about relative productivity; points are team-specific", "Team B should be disbanded", "Team A's estimates are wrong"],
   "answer": 1,
   "explain": "Story points are relative to each team, so velocities cannot be compared across teams."},
  {"q": "Management starts rewarding teams for higher velocity. What is the likely effect?",
   "options": ["Faster delivery", "Point inflation: bigger estimates for the same work", "Better quality", "Smaller stories"],
   "answer": 1,
   "explain": "A measure turned into a target gets gamed (Goodhart's law)."}
]
```

> **Source:** Atlassian, What are story points, https://support.atlassian.com/jira-software-cloud/docs/what-are-story-points/; Atlassian, What is estimation in Jira, https://support.atlassian.com/jira-software-cloud/docs/what-is-estimation-in-jira/; Atlassian Agile Coach, Estimation, https://www.atlassian.com/agile/project-management/estimation; Atlassian, Burndown and velocity chart documentation, https://support.atlassian.com/jira-software-cloud/docs/view-and-understand-the-velocity-chart/; The Scrum Guide (2020), https://scrumguides.org/scrum-guide.html
