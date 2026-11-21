# Interview readiness: process and behavioural questions

> **Before this lesson:** the whole track, especially [Scrum reports and how they are misused](#/lesson/jira/scrum-reports) and [A sprint in the life of an engineer](#/lesson/jira/day-in-the-life). From the behavioural track, [STAR in depth](#/lesson/behavioural/star-in-depth) explains the answer structure used below.

## In plain words

When a job posting lists "Jira, Agile, Scrum", the interview rarely includes a quiz on Jira buttons. Instead you get two kinds of questions:

1. **Process questions**: "How does your team plan a sprint?", "What's the difference between Scrum and Kanban?", "What do you think of story points?". These test whether you understand *why* teams work this way.
2. **Behavioural questions** set in an agile team: "Tell me about a time a sprint went wrong", "...when you disagreed with your Product Owner", "...when a deadline was at risk". These test how you behave when the process meets reality.

Occasionally there is a **practical task**: write a JQL query, design a workflow, or read a burndown chart.

This lesson gives you a structure for each kind, model answers you can adapt, the red flags to avoid, and a practice tool. Everything refers back to earlier lessons, so you can revise the detail behind each answer.

Why it matters for a job: for many engineering roles in Singapore and at large tech companies, process and collaboration questions are part of the behavioural or hiring-manager round, and they often decide close calls between technically similar candidates. Showing that you understand the purpose behind ceremonies and metrics, and can tell honest stories about using them, signals that you will be easy to work with.

## How to answer process questions

A reliable shape for any "what is / how do you" process question:

1. **Define it in one sentence**, accurately.
2. **Say why it exists**: the problem it solves.
3. **Give a concrete example** from your own experience (or a realistic one, clearly framed).
4. **Name a limitation or a misuse**, and how you avoid it.

That fourth step is what separates a strong answer from a memorised one.

**Example: "What is velocity?"**

1. "Velocity is how much work, usually in story points, a Scrum team completes per sprint, averaged over recent sprints."
2. "It helps the team forecast how much to take into the next sprint and roughly how long a backlog will take."
3. "Our last six sprints ranged from 22 to 31 points, so we planned around 26 and adjusted for holidays."
4. "It's a planning tool, not a performance measure: points are relative to each team, so comparing teams is meaningless, and targeting velocity only inflates estimates."

## How to answer behavioural questions

Use **STAR**: **S**ituation, **T**ask, **A**ction, **R**esult (behavioural track: [STAR in depth](#/lesson/behavioural/star-in-depth)). In an agile context, three habits make stories stronger:

- **Show the process helping you**, not only following it: "Because the board showed Review over its WIP limit, we..."
- **Say "I" for your actions**, while crediting the team for team results.
- **End with what changed afterwards**: a new working agreement, an automation, a Definition of Done item. Retrospective thinking is exactly what agile interviewers want to see.

The Tech Interview Handbook's list of common behavioural questions includes many that fit agile settings directly: conflicts with teammates, missed deadlines, receiving feedback, prioritising competing demands, and dealing with ambiguity.

## A question bank with model answers

Each answer below is a skeleton: adapt it to your own experience. Never claim experience you do not have; it is fine to say "In my internship we... " or "I haven't run sprints myself, but in my capstone project we..."

### Agile and Scrum fundamentals

**"What is Scrum, in your own words?"**
A lightweight framework for complex work, built on empiricism: short fixed-length Sprints, a Sprint Goal, a Done Increment, and regular inspection (Daily Scrum, Review, Retrospective) so the team adapts quickly. Three accountabilities: Developers, Product Owner, Scrum Master. *(Lessons 2 to 5.)*

**"Scrum or Kanban: when would you use each?"**
Scrum when the team can plan a goal per cycle, such as product feature work. Kanban when work arrives unpredictably and must flow continuously, such as support or platform teams; it limits WIP and measures flow. Many teams mix them. *(Lesson 6.)*

**"What makes a good user story?"**
Written from the user's perspective with a reason ("so that"), small enough for a few days, testable through acceptance criteria, ideally meeting INVEST; a placeholder for conversation, not a contract. *(Lesson 7.)*

**"Definition of Done versus acceptance criteria?"**
DoD is the quality bar for every item; acceptance criteria are specific to one item. Done requires both. *(Lesson 5.)*

### Estimation and planning

**"How does your team estimate?"**
Relative sizing with story points on a Fibonacci-like scale, planning poker with simultaneous reveal; the value is in the discussion when estimates differ. Large items get split. *(Lesson 9.)*

**"How do you decide how much goes into a sprint?"**
Recent completed work, this sprint's capacity (leave, holidays, on-call), the Sprint Goal, and some slack for unplanned work. *(Lesson 15.)*

**"Your manager asks for a delivery date. What do you say?"**
A range with assumptions, based on data (velocity or throughput, or a Monte Carlo forecast), what would change it, and a promise to update. *(Lessons 9 and 22; thinking track: [Planning questions](#/lesson/thinking/planning-estimating).)*

### Metrics

**"What do you think about measuring teams by velocity?"**
Useful for a team's own planning; harmful as a performance target or cross-team comparison (Goodhart's law). Prefer outcomes and flow metrics such as cycle time, plus delivery metrics like DORA's. *(Lessons 21 and 22.)*

**"What does a burndown going up mean?"**
Scope was added or estimates increased; check the sprint report's asterisks and estimate changes; burnup separates the two. *(Lesson 21.)*

### Jira practice

**"Write a query for open high-priority bugs assigned to nobody in PAY."**
`project = PAY AND type = Bug AND priority IN (High, Highest) AND assignee IS EMPTY AND statusCategory != Done`. Mention `IS EMPTY` and `statusCategory`. *(Lessons 16 and 17.)*

**"Why might `assignee != alice` miss items?"**
`!=` does not match empty fields; add `OR assignee IS EMPTY`. *(Lesson 17.)*

**"Design a workflow for a team with code review and QA."**
To Do, In Progress, In Review, QA, Done, plus Won't Do; backward transitions for review changes and failed QA; finishing statuses set a resolution; every status mapped to a column, only truly finished ones in the rightmost. *(Lessons 13 and 14.)*

**"How did you link code to tickets?"**
Uppercase key in branch names, commit messages and PR titles; Development panel; automation on PR merge; possibly smart commits. *(Lesson 24.)*

### Behavioural, agile-flavoured

**"Tell me about a sprint that went badly."**
Pick a real one. Situation (what went wrong: scope creep, an outage, an underestimated story), your task, what you did (raised it at the Daily Scrum, split the story, renegotiated scope with the PO), result (what was delivered against the goal), and the retrospective action that prevented a repeat.

**"Tell me about a time you disagreed with your Product Owner."**
Show respect for the PO's accountability for ordering, and how you brought evidence (user data, effort, risk). Outcome: either you persuaded them, or you committed to their decision and learned something. Behavioural track: [Conflict and disagreement](#/lesson/behavioural/conflict).

**"Tell me about a deadline you were at risk of missing."**
Early transparency, options presented (cut scope, add a simpler version, move the date), the decision made with stakeholders, delivery against what was agreed. Behavioural track: [Ownership and delivering results](#/lesson/behavioural/ownership-results).

**"How do you handle changing priorities mid-sprint?"**
Protect the Sprint Goal; route requests through the PO; make trade-offs visible; reserve capacity for genuine emergencies. Behavioural track: [Ambiguity and changing priorities](#/lesson/behavioural/ambiguity).

**"Tell me about a process improvement you drove."**
A retrospective action you owned, such as a WIP limit on review, a Jira automation, or a Definition of Done addition, with a measurable before-and-after.

## A sample STAR answer, fully written

> **Question:** "Tell me about a time a sprint didn't go to plan."
>
> **Situation.** "I was a backend engineer on a six-person team at an online grocery company. Midway through a two-week sprint whose goal was a delivery-slot waitlist, support escalated a bug where some customers' orders showed as undelivered."
>
> **Task.** "I was the engineer most familiar with the order-status service, so I needed to help fix it without losing the sprint goal."
>
> **Action.** "I raised it at the next Daily Scrum with the support ticket and the number of affected customers, about 3% of orders that day. Our Product Owner agreed it should come in, so I suggested we drop the admin dashboard story, which was the least important for the goal; she agreed and we updated the sprint in Jira so the trade-off was visible. I paired with a colleague and found the cause in two hours: a time-zone conversion for orders crossing midnight. We added a test for midnight cases before fixing it."
>
> **Result.** "The fix shipped the next morning, support confirmed no new cases, and we still met the sprint goal; the admin view moved to the next sprint. In the retrospective I proposed adding time-zone edge cases to our testing checklist, and we haven't had that class of bug since."

About 230 words: roughly 90 seconds to two minutes spoken. Notice the specific numbers, the explicit trade-off, the "I" actions, and the lasting change.

## Red flags to avoid

| Red flag | Why it hurts | Instead |
|---|---|---|
| Reciting definitions with no example | Sounds memorised | Add one real detail |
| "Scrum is just a lot of meetings" | Signals you missed the purpose | Explain what each event is for, then critique honestly |
| Blaming the Product Owner, QA or "management" | Suggests poor collaboration | Describe the disagreement neutrally and your part |
| Bragging about velocity numbers | Shows misunderstanding of the metric | Talk about outcomes and what you learned |
| Claiming you never miss estimates | Not believable | Show how you handle being wrong |
| Overstating your role | Probes will expose it | Say "I" for your actions, "we" for team outcomes |
| Tool worship ("Jira solved our process") | Ignores people and practices | Tools support conversations |

## Practice tool: shuffle the questions

Use this card deck to practise out loud. Press **Next question**, answer aloud for up to two minutes, then reveal the prompts to check what you covered. The questions are stored in the page; nothing is saved or sent anywhere.

```html-run
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Agile interview practice</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 12px; color: #1f2937; background: #fff; }
  .card { border: 1px solid #d1d5db; border-radius: 10px; padding: 14px; min-height: 120px; }
  .kind { font-size: 12px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.05em; }
  .q { font-size: 18px; font-weight: 600; margin: 6px 0 10px; }
  .hints { display: none; }
  .hints li { margin: 3px 0; }
  button { font: inherit; margin: 10px 6px 0 0; cursor: pointer; }
  #timer { font-variant-numeric: tabular-nums; margin-left: 8px; }
</style>
</head>
<body>
<div class="card">
  <div class="kind" id="kind"></div>
  <div class="q" id="q">Press "Next question" to start.</div>
  <ul class="hints" id="hints"></ul>
</div>
<button id="next">Next question</button>
<button id="show">Reveal prompts</button>
<button id="start">Start 2-minute timer</button><span id="timer"></span>
<script>
var CARDS = [
  ["Process", "What is Scrum, in your own words?", ["Empiricism: inspect and adapt", "Sprint, Sprint Goal, Increment", "Three accountabilities", "One honest limitation"]],
  ["Process", "Scrum or Kanban for an on-call support team?", ["Unpredictable arrivals", "WIP limits and pull", "Flow metrics: cycle time, throughput", "Mixing is fine"]],
  ["Process", "What do you think of velocity as a metric?", ["Team planning tool", "Points are team-relative", "Goodhart's law", "Prefer outcomes and flow"]],
  ["Process", "Definition of Done versus acceptance criteria?", ["DoD: every item", "AC: one item", "Done needs both", "An example of each"]],
  ["Process", "How do you decide how much to take into a sprint?", ["Recent completed work", "Capacity: leave, holidays, on-call", "Sprint Goal", "Slack for interruptions"]],
  ["Process", "Your burndown went up mid-sprint. Why?", ["Scope added", "Estimate increased", "Check the sprint report asterisks", "Burnup separates the two"]],
  ["Jira", "Write JQL: my unfinished work, most urgent first.", ["assignee = currentUser()", "statusCategory != Done", "ORDER BY priority DESC"]],
  ["Jira", "Why can `assignee != alice` miss work?", ["!= skips empty fields", "Add OR assignee IS EMPTY"]],
  ["Jira", "Design a workflow with code review and QA.", ["States and backward transitions", "Won't Do exit", "Resolution set on finish", "Column mapping, rightmost = done"]],
  ["Jira", "How did your team link code to tickets?", ["Uppercase key in branch, commit, PR", "Development panel", "Automation on merge", "Smart commit rules"]],
  ["Behavioural", "Tell me about a sprint that went badly.", ["Situation with numbers", "What you did, in I-statements", "Scope trade-off with the PO", "Retrospective action afterwards"]],
  ["Behavioural", "Tell me about disagreeing with your Product Owner.", ["Respect PO accountability", "Bring evidence", "Outcome either way", "What you learned"]],
  ["Behavioural", "Tell me about a deadline at risk.", ["Raised early", "Options: scope, simpler version, date", "Decision with stakeholders", "Delivered what was agreed"]],
  ["Behavioural", "Tell me about a process improvement you drove.", ["Problem with evidence", "Your change: WIP limit, automation, DoD item", "Before-and-after measure"]],
  ["Forecast", "Your manager wants a date. What do you say?", ["Range, not a point", "Data: velocity or throughput", "Assumptions and risks", "When you will update"]]
];
var order = [], pos = -1, timerId = null;
function shuffle() {
  order = CARDS.map(function (_, i) { return i; });
  for (var i = order.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = order[i]; order[i] = order[j]; order[j] = t; }
  pos = -1;
}
function show(i) {
  var c = CARDS[i];
  document.getElementById("kind").textContent = c[0];
  document.getElementById("q").textContent = c[1];
  var ul = document.getElementById("hints");
  ul.innerHTML = ""; ul.style.display = "none";
  c[2].forEach(function (h) { var li = document.createElement("li"); li.textContent = h; ul.appendChild(li); });
}
document.getElementById("next").onclick = function () {
  if (pos + 1 >= order.length) shuffle();
  pos++; show(order[pos]);
};
document.getElementById("show").onclick = function () { document.getElementById("hints").style.display = "block"; };
document.getElementById("start").onclick = function () {
  var left = 120, el = document.getElementById("timer");
  if (timerId) clearInterval(timerId);
  el.textContent = "2:00";
  timerId = setInterval(function () {
    left--;
    el.textContent = Math.floor(left / 60) + ":" + ("0" + (left % 60)).slice(-2);
    if (left <= 0) { clearInterval(timerId); el.textContent = "Time!"; }
  }, 1000);
};
shuffle();
</script>
</body>
</html>
```

## Practical tasks you may be given

- **"Here's a burndown; what happened?"** Look for steps up (scope or estimates), flat stretches (blocked or batch finishing), and the end gap. Ask what the board filter and done column are.
- **"Write three JQL queries for a team lead."** Use functions (`currentUser()`, `openSprints()`, `startOfWeek()`), `statusCategory`, and handle empties.
- **"Set up a board for this team."** Filter, columns mapped to statuses, WIP limits, swimlanes, quick filters, card fields (lesson 14).
- **"Split this epic."** Vertical slices with a first thin end-to-end story and a spike if needed (lesson 8).

The auto-graded problems in this track practise the same skills in code: [Mini-JQL: boolean queries](#/problem/jira-jql-boolean), [Sprint burndown](#/problem/jira-burndown), [Velocity from sprint records](#/problem/jira-velocity), [Monte Carlo: when will it be done](#/problem/jira-monte-carlo-when).

## A one-week revision plan

| Day | Focus | Do |
|---|---|---|
| 1 | Agile, Scrum theory, events, artifacts | Explain each event's purpose aloud; write your team's DoD |
| 2 | Kanban, stories, splitting, estimation | Split one epic from your experience into vertical slices |
| 3 | Jira model, workflows, boards | Draw a workflow and board for your last team |
| 4 | JQL | Write ten queries in the lesson 16 playground |
| 5 | Reports and forecasting | Read a burndown and a CFD; run the Monte Carlo demo |
| 6 | Behavioural stories | Prepare four STAR stories: sprint gone wrong, disagreement, deadline, improvement |
| 7 | Mock interview | Use the practice deck above with a timer |

## Summary

- Process questions: define, explain why, give an example, name a limitation or misuse.
- Behavioural questions: STAR, with the process visibly helping you, "I" for your actions, and a lasting change at the end.
- Know the model answers for Scrum versus Kanban, user stories, DoD versus acceptance criteria, estimation, sprint planning, velocity misuse and burndown reading.
- Be ready for practical tasks: JQL, workflow and board design, reading charts, splitting work.
- Avoid red flags: memorised definitions, blaming others, bragging about velocity, overstating your role, tool worship.

## Glossary

- **Process question** — an interview question about how and why a team works the way it does.
- **Behavioural question** — a question about how you acted in a past situation.
- **STAR** — Situation, Task, Action, Result: a structure for behavioural answers.
- **Model answer** — a well-structured example answer to adapt, not recite.
- **Red flag** — something in an answer that worries interviewers.
- **Working agreement** — a team's explicit rule about how it works, such as "review before you start".
- **Practical task** — a hands-on exercise in an interview, such as writing JQL.

## Check yourself

```quiz
[
  {"q": "What is the fourth step of the suggested structure for process questions?",
   "options": ["Give a definition", "Name a limitation or misuse and how you avoid it", "Mention Jira", "Ask the interviewer a question"],
   "answer": 1,
   "explain": "Discussing limitations shows understanding rather than memorisation."},
  {"q": "Which ending makes a behavioural sprint story strongest?",
   "options": ["The team worked overtime", "A retrospective action that prevented the problem recurring", "The sprint was cancelled", "The manager was happy"],
   "answer": 1,
   "explain": "Interviewers value learning and improvement, the essence of inspect-and-adapt."},
  {"q": "Which statement about velocity is most likely to impress an interviewer?",
   "options": ["Our velocity was the highest in the department", "It's a team planning tool; comparing teams or targeting it backfires", "Velocity measures individual productivity", "We doubled velocity by working weekends"],
   "answer": 1,
   "explain": "Understanding the purpose and misuse of the metric is the signal."},
  {"q": "You disagreed with your Product Owner about priorities. Which approach fits Scrum's accountabilities?",
   "options": ["Build your preferred item anyway", "Bring evidence to the PO; respect that ordering is their accountability", "Escalate to the CEO immediately", "Ignore the backlog"],
   "answer": 1,
   "explain": "The PO orders the backlog; you influence with evidence."},
  {"q": "In a STAR answer, how should you describe your contribution?",
   "options": ["Always 'we'", "'I' for your actions, credit the team for team results", "Avoid pronouns", "Only mention results"],
   "answer": 1,
   "explain": "Interviewers need to know what you did."},
  {"q": "A practical task asks you to explain a burndown that jumps up on day 6. What is your first hypothesis?",
   "options": ["The team was lazy", "Scope was added or an estimate increased", "Jira lost data", "The sprint ended early"],
   "answer": 1,
   "explain": "Remaining work rises only when scope or estimates increase (or items reopen)."},
  {"q": "You have never worked in a Scrum team. What is the best approach?",
   "options": ["Pretend you have", "Say so honestly and use a realistic example from a project or internship", "Refuse to answer", "Talk only about Jira features"],
   "answer": 1,
   "explain": "Honesty plus a relevant example beats a story that falls apart under probing."}
]
```

> **Source:** Tech Interview Handbook, Behavioral interview questions, https://www.techinterviewhandbook.org/behavioral-interview-questions/; Ken Schwaber and Jeff Sutherland, The Scrum Guide (2020), https://scrumguides.org/scrum-guide.html; The Kanban Guide (2025.5), https://kanbanguides.org/english/; Atlassian, View and understand the velocity chart, https://support.atlassian.com/jira-software-cloud/docs/view-and-understand-the-velocity-chart/; Atlassian, JQL operators, https://support.atlassian.com/jira-software-cloud/docs/jql-operators/; DORA metrics guide, https://dora.dev/guides/dora-metrics/
