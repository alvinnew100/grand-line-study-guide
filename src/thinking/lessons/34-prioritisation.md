# Prioritisation questions: too many bugs and features, and technical debt versus delivery

> **Before this lesson:** the likelihood × impact idea from [Exploratory testing, risk and non-functional categories](#/lesson/thinking/exploratory-risk-nonfunctional) and the impact-against-effort grid from ["Should we ship it?"](#/lesson/thinking/ship-decisions-product-sense) are reused here. No management experience is assumed.

## In plain words

A hospital's emergency room never has enough doctors for everyone at once. So a nurse at the door sorts arrivals: the person who cannot breathe goes first, the sprained ankle waits, however long the ankle has already been waiting and however loudly its owner complains. The nurse is not deciding who *matters*; the nurse is deciding the **order**, using a simple rule that everyone can understand. That sorting is called **triage**.

Every software team is that emergency room. There are always more bugs to fix, features to build and clean-ups to do than there are hours. **Prioritisation** is deciding the order, and — the part people find hard — deciding what will *not* be done. Interviewers ask *"you have ten bugs and five feature requests and one week; what do you do?"* because an engineer who cannot choose will either work on whatever is loudest or try to do everything and finish nothing. They are not looking for the "right" order. They want to see a **rule you can explain**, applied calmly, and communicated to the people who will be disappointed.

## The two questions behind every priority

Strip away the jargon and every method asks the same two things about each item:

1. **How much good does doing it create — or how much harm does leaving it cause?** (value)
2. **How much does it cost to do?** (effort)

Do first what has high value and low cost. Everything else in this lesson is a refinement of that sentence.

### Refinement 1 — What "value" is made of

For a **bug**, value means harm avoided:

| Factor | Question |
|---|---|
| **Severity** | How bad is it for one affected user? Data lost, money wrong, blocked, annoyed, or merely ugly? |
| **Reach** | How many users meet it, and how often? |
| **Workaround** | Can they get the job done another way? |
| **Trend** | Is it getting worse — more users, growing data corruption? |
| **Exposure** | Security, legal or reputational risk? |

For a **feature**, value means benefit gained: how many users want it, how much it helps each, what it does for revenue or retention, and whether a commitment (a contract, a regulation, a date) depends on it.

### Refinement 2 — Urgency is not importance

A general's old observation, popularised as the **Eisenhower matrix**, separates two things people confuse. *Important* means it contributes to your goals. *Urgent* means it demands attention now.

| | Urgent | Not urgent |
|---|---|---|
| **Important** | Do now — the outage, the data-loss bug | **Schedule** — tests, clean-up, the design that prevents next year's outages |
| **Not important** | Deflect or batch — most interruptions | Drop |

The top-right box is where teams fail. Important-but-not-urgent work never shouts, so it is postponed for ever, until it becomes urgent in the worst way.

### Refinement 3 — A score, when you need one

To compare many items, teams use a simple formula. A common one is **RICE**:

$$\text{score} = \frac{\text{Reach} \times \text{Impact} \times \text{Confidence}}{\text{Effort}}$$

*Reach*: how many users in a period. *Impact*: how much each is helped, on a small scale such as 0.25, 0.5, 1, 2, 3. *Confidence*: how sure you are, as a percentage. *Effort*: person-weeks.

```python-run
items = [
    # name,                         reach, impact, confidence, effort (person-weeks)
    ("Checkout crash on old phones", 4000, 3,   0.9, 1),
    ("Dark mode",                    9000, 0.5, 0.8, 4),
    ("Export to spreadsheet",        1500, 2,   0.7, 2),
    ("Typo on settings page",        9000, 0.25, 1.0, 0.1),
    ("Rewrite search",               9000, 2,   0.4, 12),
]
scored = sorted(((r * i * c / e, name) for name, r, i, c, e in items), reverse=True)
for score, name in scored:
    print(f"{score:9.0f}  {name}")
```

Each line of the list holds one item's four numbers; the `sorted` line computes reach × impact × confidence ÷ effort for each and orders them from highest. Notice two results. The typo ranks near the top — tiny value, but almost no cost: do it between other tasks. And the search rewrite ranks last despite the largest reach, because of low confidence and huge effort; the score is telling you to *shrink it or learn more* before committing.

Two warnings to state when you use a score. The numbers are guesses, so treat the result as a starting order to discuss, not a verdict. And some things override any score: a legal deadline, a security hole, or a promise already made.

### Refinement 4 — Dependencies and sequence

Sometimes a low-value item must come first because others need it: you cannot build the report before the data is collected. And sometimes doing a *small* piece of several items teaches more than finishing one. Check for both before fixing the order.

## A method you can say aloud

1. **Clarify the goal and the constraint.** What is the team trying to achieve this month? What is fixed — time, people, a date?
2. **List everything**, including the invisible items (maintenance, on-call, promised work).
3. **Triage** into must / should / could / will not (this split is known as **MoSCoW**).
4. **Rank** within the groups by value over effort, using a score if needed.
5. **Cut.** Draw the line where capacity ends and say what is below it.
6. **Communicate** the order and the reasons to the people affected, and when you will look again.

Steps 5 and 6 are what separate a prioritisation from a wish list.

## Worked question 1 — Ten bugs, five features, one week

**Prompt:** *"You join a team. The backlog has ten open bugs and five feature requests. You and one colleague have one week. What do you do?"* Give a three-minute answer, then compare.

<details><summary>Model answer</summary>

"I'd begin by asking what the team's goal is right now — a launch date, a retention target, an important customer? — because the same list sorts differently under each. And I'd check what is already promised.

Then I'd look at every item quickly, a few minutes each, to sort before going deep on any.

**Bugs first, by harm.** For each: what does the user experience, how many users, is there a workaround, is it getting worse? That gives three piles.

- *Now*: anything losing data, charging wrong amounts, breaking security, or blocking a core task for many users. These go ahead of all features. If one of the ten is 'payment fails for 5 % of users', that is day one.
- *Soon*: real problems with a workaround, or affecting few users.
- *Later or never*: cosmetic issues and rare edge cases. Some should be closed with an honest note instead of lingering.

**Features by value over effort.** For each, who asked and why, how many users benefit, and a rough size. I'd ask the product owner for the value side — I should not guess what customers need — and supply the effort side myself. A feature tied to a contract or a regulatory date moves up regardless of score.

**Then fit it to the week.** Two people for five days is ten person-days, of which meetings, review and surprises take perhaps a third. So about six or seven days of real work. I'd fill that with the *now* bugs, then alternate the best-scoring feature with the cheapest *soon* bugs, and stop.

**The cut.** Say explicitly what is not happening this week — for example three features and four minor bugs — and why.

**Communicate.** A short note to the product owner and whoever raised the dropped items: here is the order, here is the reasoning, here is what we would need to do more. And I'd expect them to push back; if the product owner says a feature I ranked low is vital for a customer meeting, the order changes. The engineer supplies facts about cost and risk; the owner of the product decides value.

**One more thing.** Ten open bugs suggest asking why they arise. If six are in the same module, an hour of investigation there may be worth more than fixing them one at a time."

</details>

> [!INTERVIEW]
> Three signals that interviewers listen for in this answer: you **asked for the goal** before sorting; you **said what you would not do**; and you **involved the product owner** instead of deciding value alone. Leaving out the cut is the most common weakness.

## Worked question 2 — Everything is "priority one"

**Prompt:** *"Three stakeholders each say their request is the top priority. How do you handle it?"*

<details><summary>Model answer</summary>

"If everything is top priority, nothing is, so my job is to turn three opinions into one order that all three can see.

First, understand each request properly: what problem it solves, for whom, what happens if it waits a month, and whether a real date is attached. 'Top priority' often turns out to mean 'I have been waiting a long time' or 'my manager asked'.

Second, size each one honestly: a day, a week, a month.

Third, put them side by side against the team's stated goal, with value and cost visible. Often the order then becomes obvious to everyone — one request has a contractual date, one is a nice-to-have dressed up.

If it is not obvious, I should not pick a winner between three colleagues by myself. I'd bring the comparison to the person who owns the team's priorities — the product owner or my manager — with a recommendation: 'Given goal X, I suggest A then C then B, because…; B would then start in three weeks.' And I'd get the three in one conversation if possible, because people accept an order they have seen being reasoned through far more readily than one announced to them.

Then I tell each of them when their item will be done, not merely that it is 'second'. And I look for small moves that reduce the pain of waiting: a temporary workaround for B, or a thin first version of C.

What I would avoid: quietly doing the request of whoever asks most often; saying yes to all three and delivering all late; or starting all three at once, which makes each take longest."

</details>

That last point deserves a number. If three tasks take a week each and you do them one after another, they finish at weeks 1, 2 and 3 — an average of 2. If you split your time evenly among all three, all finish around week 3 — an average of 3, and nobody gets anything early. Limiting **work in progress** is one of the cheapest ways to deliver sooner.

## Technical debt versus delivery

### What technical debt is

You need to send a parcel today, so you tape the box shut instead of sealing it properly. It works. But every later time you handle that box you have to be careful, re-tape it, and worry. **Technical debt** is the same thing in software: a shortcut taken now that makes future work slower or riskier. The comparison with money is deliberate. The shortcut is the *loan*; the extra effort on every later change is the *interest*; cleaning it up is *repaying* the loan.

Debt is not always a mistake. Borrowing to hit a date that matters can be the right business decision — if it is done knowingly and repaid. A useful classification by Martin Fowler sorts debt on two axes: taken **deliberately** or **inadvertently**, and **prudently** or **recklessly**. "We must ship now and will deal with the consequences" is deliberate and prudent. "What is layering?" is inadvertent and reckless. The dangerous kind is the debt nobody decided to take and nobody is tracking.

Signs that interest is being paid: small changes take much longer than they should; the same area keeps producing bugs; engineers are afraid to touch certain files; new colleagues take months to become useful; releases need heroics.

### Why the conversation goes wrong

Engineers say "we need to refactor" and the business hears "we want to stop delivering in order to tidy up". Both are speaking truthfully and past each other. The fix is to describe debt in the same terms as features: **what it costs us now and what repaying it would buy.**

| Weak | Strong |
|---|---|
| "The billing code is a mess." | "Every billing change takes about three weeks instead of one, and two of our last five incidents started there. Two weeks of restructuring should halve that." |
| "We need to upgrade the framework." | "Our version stops receiving security fixes in March. After that, any vulnerability found stays open." |
| "We need more tests." | "We find checkout bugs in production about once a month; each costs a day of two engineers plus refunds. Tests on the three riskiest flows would catch most of them." |

### How to balance it

There is no formula; there are four workable approaches, often combined.

1. **Fix as you go.** When you work in an area, leave it a little better: rename, add a test, split a function. Small, continuous, and needs nobody's permission. This is the default.
2. **A standing allowance.** Reserve a steady share of each planning period — commonly quoted as around a fifth — for debt and maintenance. Predictable, and it prevents the "never urgent" trap.
3. **Attach it to features.** If the next feature touches the bad module, do the clean-up first as part of that feature's cost. This is the easiest to justify, because the benefit arrives immediately.
4. **A dedicated project**, for large items — a database migration, replacing a framework — with its own plan, milestones and measurable goal, proposed like any other project.

And choose *which* debt by the same rule as everything else: interest paid × how often you go there, against the cost to fix. Ugly code that nobody touches costs nothing; leave it alone.

## Worked question 3 — Clean-up or features?

**Prompt:** *"Your team wants a quarter to clean up the codebase. The product manager wants three new features. You are asked for your view."*

<details><summary>Model answer</summary>

"I would not accept the framing of all clean-up or all features. A quarter with no visible delivery is very hard to defend and risky in itself — large clean-ups without a deadline tend to expand — and a quarter of features on top of code that is slowing us down makes every later quarter worse.

**First, make the debt concrete.** Which parts hurt, and how do we know? I'd gather evidence: how long changes take in each area, where the incidents and bugs cluster, which files are changed most often. Usually a small part of the codebase causes most of the pain.

**Second, connect it to the three features.** Which of them touch the painful areas? If feature A needs changes in the module everyone fears, then cleaning that module is not an alternative to A; it is the first step of A, and probably makes A faster and safer overall.

**Third, propose a mix.** Something like: feature A, including the clean-up of the module it touches; feature B as planned; feature C moved to next quarter; and a steady fifth of the team's time for the two worst remaining items, each with a stated benefit — 'cuts release time from a day to an hour', 'removes the framework that loses security support in March'.

**Fourth, present it in business terms.** Not 'the code is ugly' but 'this is what the current state costs each month, and this is what we get back'. And commit to measuring — time to make a typical change, incidents from that area — so that next quarter we can show whether the investment worked.

**The decision is shared.** I supply the cost and risk; the product manager supplies the value of the features; and if we still disagree, we have a clear comparison to put before whoever owns the outcome.

**One exception.** If part of the debt is a real risk rather than a nuisance — unsupported software with known vulnerabilities, no working backups, a single person who understands a critical system — I would raise that separately and urgently. That is not tidying; it is a risk the business needs to accept or fix knowingly."

</details>

## Common mistakes

- **Sorting without knowing the goal.**
- **Loudest first**, or oldest first, or easiest first, without saying so.
- **No cut**: a ranked list that still pretends everything will be done.
- **Deciding value alone**, without the people who know the customers.
- **Starting everything at once.**
- **Describing debt as ugliness** instead of as cost and risk.
- **Asking for a big-bang clean-up** with no measurable aim.
- **Treating the order as permanent.** Priorities are revisited as facts change.

## Summary

- Prioritising is choosing an order and choosing what not to do, by an explainable rule.
- Value over effort is the core; value comes from severity, reach, workaround, trend and exposure for bugs, and from users helped and commitments for features.
- Separate urgent from important; protect the important-but-not-urgent work.
- Scores such as RICE organise a discussion; they do not replace it. Legal, security and promised items can override them.
- Method: goal → list → triage → rank → cut → communicate.
- Technical debt is a loan with interest. Describe it as cost and risk; repay it as you go, with a steady allowance, attached to features, or as a planned project — and only where the interest is high.

## Glossary

| Term | Meaning |
|---|---|
| Backlog | The list of work a team has not yet done |
| Triage | Quickly sorting items to decide what is handled first |
| Severity | How bad a problem is for an affected user |
| Reach | How many users are affected in a period |
| Eisenhower matrix | A grid separating urgent from important |
| MoSCoW | Sorting into must, should, could and will not |
| RICE | A score: reach × impact × confidence ÷ effort |
| Stakeholder | Someone with an interest in or authority over the outcome |
| Work in progress | Tasks started and not finished |
| Technical debt | A shortcut that makes future changes slower or riskier |
| Interest (on debt) | The extra effort paid each time the affected code is worked on |
| Refactoring | Improving the structure of code without changing what it does |
| Product owner | The person responsible for deciding what is most valuable to build |

## Check yourself

```quiz
[
  {"q": "What is the first thing to establish before ordering a backlog?",
   "options": ["Which item is oldest", "The team's current goal and constraints", "Which requester is most senior", "Which item is easiest"],
   "answer": 1,
   "explain": "The same items sort differently under different goals; without the goal there is no basis for the order."},
  {"q": "Which item belongs in 'important but not urgent'?",
   "options": ["A production outage", "Adding tests to a fragile area that has not yet failed", "A colleague's chat message", "A cosmetic bug nobody notices"],
   "answer": 1,
   "explain": "It contributes to goals and never demands attention by itself, so it must be scheduled deliberately."},
  {"q": "Item X: reach 2,000, impact 1, confidence 50%, effort 2 weeks. Item Y: reach 500, impact 2, confidence 100%, effort 1 week. Which has the higher RICE score?",
   "options": ["X (500) beats Y (1,000)", "Y, with 1,000 against X's 500", "They are equal", "Neither can be computed"],
   "answer": 1,
   "explain": "X = 2000 × 1 × 0.5 / 2 = 500. Y = 500 × 2 × 1 / 1 = 1,000."},
  {"q": "Three one-week tasks are worked on in parallel instead of one after another. What happens to delivery?",
   "options": ["All three finish in week 1", "Nothing finishes before about week 3, so average completion is later", "They finish faster", "No difference"],
   "answer": 1,
   "explain": "Sequential work delivers at weeks 1, 2 and 3; splitting attention delays the first deliveries without helping the last."},
  {"q": "Which statement makes the best case for paying down technical debt?",
   "options": ["The code is ugly", "Changes in billing take three times longer than elsewhere and caused two recent incidents; two weeks of work should halve that", "Engineers would enjoy it", "Other companies do it"],
   "answer": 1,
   "explain": "It states the current cost and the expected benefit in terms a business can weigh against features."},
  {"q": "Which technical debt is least worth repaying?",
   "options": ["A fragile module changed every week", "Messy code in a stable area nobody needs to change", "An unsupported library with security exposure", "A slow release process used daily"],
   "answer": 1,
   "explain": "Interest is paid only when the code is touched; untouched code costs nothing."},
  {"q": "After ranking, what makes it a real prioritisation?",
   "options": ["Colour-coding the list", "Stating what will not be done and telling the people affected, with reasons", "Adding more items", "Keeping it private"],
   "answer": 1,
   "explain": "Without an explicit cut and communication, the list still implies everything will happen."}
]
```

> **Source:** Martin Fowler, "Technical Debt" and "Technical Debt Quadrant" (https://martinfowler.com/bliki/TechnicalDebt.html, https://martinfowler.com/bliki/TechnicalDebtQuadrant.html); *Software Engineering at Google*, ch. 1 on trade-offs and the cost of change over time (https://abseil.io/resources/swe-book/html/ch01.html); DORA capability guidance on work-in-process limits (https://dora.dev/capabilities/wip-limits/). RICE is a publicly described product-prioritisation formula; the examples, numbers and wording are original.
