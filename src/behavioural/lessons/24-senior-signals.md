# Senior-level signals: scope, stakeholders, risk, hiring and mentoring

## Before this lesson

Read [Ownership and delivering results](#/lesson/behavioural/ownership-results) and [Influence without authority](#/lesson/behavioural/influence); senior stories are mostly those two families at larger scale. [Amazon](#/lesson/behavioural/amazon) and [Singapore companies](#/lesson/behavioural/singapore-companies) describe what manager and leadership interviews cover at specific employers. If you are a student or early in your career, this lesson is still useful: it shows what "growth" looks like, which helps you describe your own trajectory.

## In plain words

A junior chef cooks the dishes on their station well. A head chef also cooks, but their real job is bigger: designing the menu, deciding what the kitchen will not attempt on a busy night, training the juniors, dealing with suppliers, and making sure a mistake on one station does not ruin a table's whole meal. Ask both "Tell me about a great dinner service" and you should hear very different stories.

Companies arrange engineering roles into **levels**: steps such as junior, mid-level, senior, staff and principal for individual contributors, and engineering manager and above for people managers. Each level has expectations about how large a problem you handle and how much you affect others. Behavioural interviews are one of the main ways interviewers judge which level fits you, because the **size and shape** of your stories reveal how you work.

The risk for experienced candidates is **down-levelling**: being offered a lower level than you hoped because your stories sounded like a mid-level engineer's. It usually happens not because the candidate lacks senior experience, but because they told the stories at the wrong altitude: all code, no trade-offs, no people.

## What changes with seniority

The table below summarises common expectations. Exact definitions differ by company; treat it as a general guide.

| Dimension | Junior | Mid-level | Senior | Staff, principal or manager |
|---|---|---|---|---|
| Scope | A task | A feature | A system or project | Several teams or an organisation's direction |
| Ambiguity | Clear tasks | Some unclear details | Unclear problems; defines the work | Defines which problems are worth solving |
| Influence | Own work | Own team | Other teams | The wider organisation |
| Risk | Follows the plan | Flags risks | Identifies and mitigates risks early | Sets how the organisation handles risk |
| People | Learns from others | Helps peers | Mentors; shapes hiring | Develops leaders; builds teams |
| Trade-offs | Implements decisions | Suggests options | Makes and explains trade-offs | Balances technical and business strategy |

The published material from several employers points the same way. Amazon's preparation page for Software Development Manager candidates lists, among other things, motivating, mentoring and managing teams; risk management, adaptability and resource management; stakeholder management; and owning work from conception to delivery in line with business goals. Google's re:Work guide describes leadership for managers as enabling a team, shaping direction and developing people. Grab's "How we hire" page says leadership candidates should expect a deeper look at management style and should prepare examples of leading teams, mentoring and making impactful decisions. A 2017 Grab engineering post (dated) said senior candidates were asked about their most important technical decisions for scalability and availability, and how they would hire engineers and build a team.

## The five senior signals

### 1. Scope

**What it means:** the size of the problem and how many people or systems it touched.
**How to show it:** state scope early in the Situation: team count, users affected, systems involved, money or time at stake. "Three teams, about 2 million monthly users, the checkout path."

### 2. Stakeholders

A **stakeholder** is anyone affected by or with influence over your work: other teams, product managers, leadership, customers, legal, operations.
**How to show it:** name who had to agree, what each cared about, and how you brought them together. A senior story almost always has at least two stakeholders with different interests.

### 3. Risk

**What it means:** seeing what could go wrong before it does, reducing it, and making decisions when some risk remains.
**How to show it:** describe the risks you identified, what you did to reduce them (pilots, rollbacks, phased rollouts, monitoring), and the risk you chose to accept and why.

### 4. Trade-offs and saying no

**What it means:** choosing between good options, and deciding what not to do.
**How to show it:** name the alternative you rejected and why, and one thing you deliberately did not build. "We chose to keep the old reporting system for a quarter longer, because migrating it would have delayed checkout by six weeks."

### 5. Hiring and developing people

Amazon's Leadership Principle "Hire and Develop the Best" describes raising the performance bar with every hire and coaching others.
**How to show it:** mentoring with a visible result (the person now leads something), improving how your team interviews, onboarding that cut ramp-up time, delegating real ownership rather than tasks.

## Common phrasings for senior candidates

- "Tell me about the most complex project you have led."
- "Describe a time you had to align several teams with different priorities."
- "Tell me about a significant technical decision you made and the trade-offs."
- "Tell me about a risk you identified early. What did you do?"
- "Describe how you have helped someone on your team grow."
- "Tell me about a time you decided not to do something."
- "How have you contributed to hiring?"
- "Tell me about a time a project you were leading was going off track."

## An example rubric for senior candidates

An **example** rubric, written for this lesson, for a question like "Tell me about the most complex project you have led":

| Level | What it looks like |
|---|---|
| Strong senior | Clear scope across teams; named stakeholders with different interests, aligned; risks identified early and mitigated; explicit trade-offs and something deliberately not done; developed others along the way; business-relevant measured outcome; honest reflection |
| Solid senior | Clear technical leadership of a significant project, some cross-team work, sensible trade-offs, measured outcome |
| Mid-level | Excellent individual technical work on a feature; little sign of stakeholders, risk management or developing others |
| Not yet | Unclear role; story is about following a plan someone else set |

## A mid-level-sounding answer (dialogue)

> **Example (fictional).** Question: "Tell me about the most complex project you have led."
>
> **Candidate:** I led the migration of our order service from a single database to a sharded setup, where the data is split across several databases so each holds part of it. It was technically really challenging. I designed the sharding key, the value used to decide which database holds each order. I chose customer ID so all of a customer's orders stayed together. I wrote the migration scripts, built a dual-write layer so new orders went to both old and new databases during the move, and wrote a comparison job to make sure the data matched. It took about four months. We had a couple of issues with hot shards, where one database got far more traffic than others, but I rebalanced them. In the end the migration was successful and the service could handle much more traffic.
>
> **Interviewer:** Who else was involved?
>
> **Candidate:** A couple of engineers on my team helped with the scripts.

This is strong engineering. But it is told almost entirely at the level of code. There are no stakeholders, no risks discussed before they happened, no trade-offs explained, no one developed, and the result is "much more traffic". On the example rubric it lands at mid-level, and the candidate may be offered a lower level than their experience deserves.

## A senior answer (dialogue, full STAR)

> **Example (fictional).** Same question.
>
> **Candidate:** I'll tell you about leading the move of our order service to a split, or sharded, database ahead of a regional expansion, which involved three teams, a hard deadline and a decision to leave one important thing unfinished.
>
> *(Situation)* I was a senior engineer at a food delivery company. Our order database was at about 70% of its capacity at evening peak, and the company planned to launch in two new countries in six months, which would roughly double order volume. Three teams depended on the order data: ours, payments and the analytics team.
>
> *(Task)* I was asked to lead the technical plan and its delivery. Success meant handling at least twice the peak load before the launch, with no lost orders and no disruption to payments.
>
> *(Action)* I started with the stakeholders, because the technical part was the easier half. I met each team's lead. Payments needed every order to stay in one place for refunds. Analytics needed their nightly reports to keep working. Our product manager needed the launch date protected. Those three needs shaped the design: I chose to split by customer, so each customer's orders stayed together for payments, and I proposed a separate copy of the data for analytics so their reports wouldn't depend on the new layout.
>
> I wrote a six-page design document with the options I'd rejected, including buying a larger database, which would have bought about a year at much higher cost, and asked the three leads and our principal engineer to review it. The main risk was data loss during the move, so I planned it in phases: new orders written to both databases, a comparison job checking every order nightly, and a switch to move reads back in under a minute. We rehearsed the switch twice before the real move.
>
> I also made a trade-off explicitly: moving the analytics copy to the new layout would have added six weeks. I proposed leaving it on the old database for one more quarter and got the analytics lead's agreement in writing.
>
> I delegated ownership of the comparison job to a mid-level engineer, Ana, who hadn't led anything that size. I paired with her for the first week, then stepped back to reviewing; she presented its results at each weekly checkpoint.
>
> *(Result)* We finished seven weeks before the launch. At launch, peak orders rose about 2.3 times and the databases stayed under 50% capacity. The comparison job found 41 mismatches during the move, all from a time-zone bug that we fixed before switching over, and no orders were lost. Ana went on to lead the analytics migration the following quarter.
>
> *(Reflection)* The thing I'd do differently is involve analytics a month earlier. Their reports turned out to depend on one table I hadn't listed, and finding that late cost us a week.
>
> **Interviewer:** Why not buy the bigger database and avoid the risk?
>
> **Candidate:** It was the safer short-term option and I took it seriously. But it would have cost about three times as much each year, and we'd have hit the same limit within about eighteen months at our growth rate. With six months of runway, I judged it was worth doing properly once, with the phased plan reducing the risk.

## Why the senior answer scores higher

| Senior signal | Mid-level answer | Senior answer |
|---|---|---|
| Scope | One service | Three teams, a regional launch, a hard deadline |
| Stakeholders | "A couple of engineers helped" | Payments, analytics, product: different needs, shaped the design |
| Risk | Hot shards fixed after they happened | Phased plan, nightly comparison, one-minute switch, rehearsed twice |
| Trade-offs | None explained | Rejected bigger database with reasons; analytics deferred with agreement |
| Developing people | None | Delegated the comparison job to Ana; she later led a migration |
| Business outcome | "Much more traffic" | 2.3 times peak under 50% capacity, no lost orders, seven weeks early |
| Reflection | None | Involve analytics earlier, with the cost of not doing so |

Notice that the senior answer contains **less** technical detail than the mid-level one. It explains the key decisions and leaves the rest for follow-up probes. Choosing what to leave out is itself a senior signal.

## Stories for people managers

If you are interviewing for an engineering manager role, expect questions focused on people. Prepare at least one story for each:

- **Hiring**: a hire you made or helped make, how you assessed the candidate, and how it worked out; or how you improved your team's interviews.
- **Developing someone**: a person whose growth you supported, with a visible outcome.
- **Underperformance**: a team member who was struggling, how you found out why, the support and clear expectations you set, and the outcome, whatever it was.
- **Conflict between team members**: how you helped two people resolve a disagreement.
- **Delegation**: giving away ownership of something important and supporting the person without taking it back.
- **Prioritisation and saying no**: protecting your team from too much work, with stakeholders kept on side.

Be careful with people stories: protect the privacy of the people involved. Use roles rather than names when the story is sensitive, and never share details of someone's health, personal life or performance ratings beyond what the story needs.

## Pitfalls for senior candidates

1. **Telling stories at code altitude.** Brilliant technical detail, no stakeholders or trade-offs.
2. **"We" hiding your leadership.** At senior level, the interviewer must see what you decided and drove.
3. **"I" hiding the team.** The opposite: claiming everything. Senior people credit others specifically.
4. **No trade-offs or decisions not to do things.**
5. **Old stories.** As general advice, prefer stories from the last few years that reflect your current level.
6. **No people development.** Seniors are expected to grow others.
7. **Too long.** Senior stories have more material; the job is to choose.

## Your turn

1. Take your biggest project and fill in the five signals: scope, stakeholders, risk, trade-offs, people. Any empty box is a part of the story you are not telling, or a gap in your experience to work on.
2. Rewrite the headline to include scope ("three teams", "a regional launch").
3. Write the rejected alternative and the thing you deliberately did not do, each in one sentence.
4. Prepare one mentoring story with a visible outcome for the other person.
5. Tell the story in under three minutes and answer "Why not the simpler option?".

## Summary

- Companies use levels; behavioural answers strongly influence which level you are offered. Telling stories at the wrong altitude risks down-levelling.
- Five senior signals: scope, stakeholders, risk, trade-offs (including saying no) and developing people.
- Amazon's SDM page, Google's re:Work and Grab's page all describe leadership and management signals of this kind; a 2017 Grab post (dated) described senior questions on technical decisions and building teams.
- Senior answers often contain less technical detail and more decisions, people and outcomes.
- Managers need stories on hiring, development, underperformance, conflict, delegation and prioritisation, told with care for others' privacy.

## Glossary

- **Level**: a step in a company's career ladder that sets expectations for scope and impact.
- **Down-levelling**: being offered a lower level than you applied for.
- **Scope**: the size of a problem and how many people or systems it affects.
- **Stakeholder**: anyone affected by or with influence over your work.
- **Sharding**: splitting a database's data across several databases, each holding part of it.
- **Phased rollout**: introducing a change in steps, with checks between them.
- **Delegation**: giving someone real ownership of a piece of work, with support.
- **Staff or principal engineer**: senior individual contributor levels whose scope spans several teams.

```quiz
[
  {"q": "A very experienced engineer tells only code-level stories with no stakeholders or trade-offs. What is the main risk?",
   "options": ["Being rejected for being too technical", "Down-levelling: being offered a lower level because the stories sound mid-level", "Being hired as a manager", "No risk"],
   "answer": 1,
   "explain": "The altitude of the stories signals level; missing senior signals suggests a lower level."},
  {"q": "In the senior answer, which part shows a deliberate trade-off?",
   "options": ["Splitting the data by customer", "Leaving analytics on the old database for one more quarter, with the analytics lead's written agreement", "Rehearsing the switch twice", "Finishing seven weeks early"],
   "answer": 1,
   "explain": "Choosing not to do something, with reasons and agreement, is a key senior signal."},
  {"q": "Which item is NOT one of the five senior signals in this lesson?",
   "options": ["Scope", "Stakeholders", "Typing speed", "Developing people"],
   "answer": 2,
   "explain": "The five are scope, stakeholders, risk, trade-offs and developing people."},
  {"q": "What does Amazon's SDM preparation page list among the areas assessed?",
   "options": ["Brainteasers", "Mentoring and managing teams, risk management, stakeholder management and ownership from conception to delivery", "Only coding speed", "Knowledge of Amazon's stock price"],
   "answer": 1,
   "explain": "The SDM page covers people, project and risk management, stakeholders and end-to-end ownership."},
  {"q": "After a senior project story, which probe is most likely?",
   "options": ["Why not the simpler option, such as a bigger database?", "What is a variable?", "Where did you go to primary school?", "Can you type faster?"],
   "answer": 0,
   "explain": "Senior probes target trade-offs and rejected alternatives."},
  {"q": "Why does the senior answer contain less technical detail than the mid-level one?",
   "options": ["The candidate knew less", "Choosing the key decisions and leaving detail for probes is itself a senior signal", "Technical detail is forbidden", "It was a non-technical project"],
   "answer": 1,
   "explain": "Senior candidates show judgement about what matters most and offer depth on request."},
  {"q": "A manager candidate tells a story about an underperforming team member. What should they be careful about?",
   "options": ["Naming the person and their health details", "Protecting privacy: using roles rather than names where sensitive and sharing only what the story needs", "Making the person sound as bad as possible", "Avoiding any outcome"],
   "answer": 1,
   "explain": "People stories should respect privacy and focus on what the manager did and the outcome."}
]
```

> **Source:** Amazon, SDM interview prep (https://atoz.amazon/en-us/jobs/hiring-process/interview-prep/software-development-manager); Amazon, Leadership Principles (https://atoz.amazon/en-us/discover/leadership-principles); Google re:Work, A guide to structured interviewing (https://rework.withgoogle.com/intl/en/guides/a-guide-to-structured-interviewing-for-better-hiring-practices); Grab, How we hire (https://grab.careers/en/how-we-hire/general/); Grab Engineering, How Grab hires engineers in Singapore, 2017 (https://engineering.grab.com/how-grab-hires-engineers-in-singapore). The level table is general guidance; rubric and dialogues are original and fictional.
