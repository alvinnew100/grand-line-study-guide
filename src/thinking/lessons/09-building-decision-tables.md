# Building a decision table from requirements

> **Before this lesson:** read [Decision tables, state transitions and pairwise testing](#/lesson/thinking/tables-states-pairwise), which introduces decision tables in a few paragraphs. This module treats them in full.

## In plain words

A restaurant's ordering rules might read: "Children eat free on Sundays if an adult orders a main course, unless it is a public holiday." Try to answer "what does a family of four pay on a holiday Sunday?" from that sentence and you will find yourself re-reading it three times. Now imagine a small grid: one column for *child?*, one for *Sunday?*, one for *adult ordered?*, one for *holiday?*, and a row for every combination, each ending with the price. The question is answered by finding the right row.

That grid is a **decision table**: a way of writing rules so that every combination of circumstances is listed exactly once with its outcome. The circumstances are called **conditions**; the outcomes are **actions**.

Interviews use decision tables because building one from a paragraph of rules shows, very quickly, whether you can be thorough without getting lost — and because the act of filling in every row nearly always exposes a case the rule-writer forgot.

Module 2 introduced decision tables in a few paragraphs. This module treats them as a full skill, because a growing number of interviews hand you a block of business rules — or a ready-made table — and ask you to build, check or change it. The task is deliberately mechanical-looking. What it measures is whether you can be **exhaustive without getting lost**: whether you notice the combination nobody specified, the two sentences that contradict each other, the word "unless" that quietly reverses a rule.

This lesson covers construction: reading requirements, choosing conditions and actions, sizing the table, filling it in, and reading rules off it. The next lesson covers checking and simplifying; the one after that covers updating a table when the policy changes.

## Anatomy of a table

A decision table has four parts.

| Part | Contains | Example |
|---|---|---|
| **Conditions** | The questions whose answers determine the outcome | "Is the customer a member?" |
| **Condition entries** | The answers for each rule: Y, N, or "–" for irrelevant | Y |
| **Actions** | The things the system may do | "Apply free shipping" |
| **Action entries** | Which actions happen under each rule | X or a value |

Tables can be laid out with rules as columns (the traditional form) or with rules as rows. This track uses **rules as rows**, because rows are easier to read in Markdown and map directly onto code: each row is "pattern → action".

A row such as `Y N – → standard` reads: *when condition 1 is yes and condition 2 is no, whatever condition 3 is, the action is standard.* In the coding problems the same row is written as the pair `["YN-", "standard"]`.

## Step 1 — Extract conditions and actions from prose

Requirements arrive as sentences. Your first job is to separate *what is asked about the situation* from *what is done*.

A worked requirement, which we will use for the rest of the lesson:

> *A bike-share scheme charges for each ride. Rides of 30 minutes or less are free for subscribers. Non-subscribers pay a flat unlock fee plus a per-minute rate. Subscribers who ride longer than 30 minutes pay the per-minute rate for the extra time only. Electric bikes add a surcharge for everyone, except that subscribers on the Plus plan do not pay it.*

Go through the text with two highlighters.

**Conditions** (facts about the situation that vary):

1. Is the rider a subscriber?
2. Is the ride longer than 30 minutes?
3. Is the bike electric?
4. Is the rider on the Plus plan?

**Actions** (charges that may apply):

- A — unlock fee
- B — per-minute rate on the whole ride
- C — per-minute rate on minutes beyond 30
- D — electric surcharge

Rules of thumb for this step:

- **Make each condition a yes/no question about one fact.** "Subscriber and long ride" is two conditions, not one.
- **Phrase conditions positively.** "Is the ride longer than 30 minutes?" is easier to reason about than "Is the ride not short?"
- **Turn numeric thresholds into conditions and note the boundary.** "30 minutes or less" versus "longer than 30" — exactly 30 belongs to the free side. Write that down; it becomes a boundary test later.
- **Keep actions atomic.** If two things can happen independently (a fee *and* a surcharge), they are two actions, so that a rule can switch each on or off.
- **Watch the connecting words.** *And* narrows a rule; *or* widens it; *unless*, *except* and *but* introduce an exception that overrides something said earlier; *only if* is a requirement, not a guarantee. Most table mistakes are misread connectives.

> [!WARNING]
> "A if B" and "A only if B" are different. "Free shipping if the order is over 50" promises free shipping above 50 and says nothing about orders below. "Free shipping only if the order is over 50" forbids it below 50 and does not promise it above. When a requirement uses one and probably means both, ask.

## Step 2 — Size the table

With $n$ independent yes/no conditions, there are $2^n$ combinations. Four conditions give 16 rows. Say the number aloud in an interview — "four conditions, so sixteen combinations before simplification" — because it shows you know what complete means before you start.

| Conditions | Rows |
|---|---|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 5 | 32 |
| 6 | 64 |

If a condition has more than two values — plan is *none*, *Basic* or *Plus* — the count is the product of the numbers of values: a three-valued condition and two yes/no conditions give 3 × 2 × 2 = 12. Such a table is called an *extended-entry* table. You can always convert it to yes/no form by splitting the condition ("is subscriber?", "is Plus?"), at the cost of creating impossible combinations, which we handle in step 4.

Six conditions is roughly the limit of what a person can fill in reliably by hand. Beyond that, split the decision into two smaller tables — one deciding an intermediate result such as "customer tier", the other using it.

## Step 3 — Generate every combination systematically

Never write combinations in the order they occur to you. Use a fixed pattern so that none can be skipped. The standard one: the last condition alternates every row, the one before it every two rows, the one before that every four, and so on — binary counting.

For the bike-share conditions (S = subscriber, L = long ride, E = electric, P = Plus plan):

| # | S | L | E | P |
|---|---|---|---|---|
| 1 | Y | Y | Y | Y |
| 2 | Y | Y | Y | N |
| 3 | Y | Y | N | Y |
| 4 | Y | Y | N | N |
| 5 | Y | N | Y | Y |
| 6 | Y | N | Y | N |
| 7 | Y | N | N | Y |
| 8 | Y | N | N | N |
| 9 | N | Y | Y | Y |
| 10 | N | Y | Y | N |
| 11 | N | Y | N | Y |
| 12 | N | Y | N | N |
| 13 | N | N | Y | Y |
| 14 | N | N | Y | N |
| 15 | N | N | N | Y |
| 16 | N | N | N | N |

In code this is one line, which is also how the judged problems enumerate inputs:

```python-run
import itertools
conditions = ["subscriber", "long ride", "electric", "plus plan"]
rows = ["".join(p) for p in itertools.product("YN", repeat=len(conditions))]
print(len(rows), "combinations")
print(rows)
```

## Step 4 — Mark impossible combinations

Some combinations cannot occur. A rider cannot be on the Plus plan without being a subscriber, so rows 9, 11, 13 and 15 (S = N, P = Y) are **infeasible**.

Do not delete them silently. Mark them, for two reasons. First, "cannot occur" is a claim about the rest of the system, and it deserves a test: *can* a lapsed subscriber still carry a Plus flag in the database? If the answer is "it should not, but it might", the table needs a defined behaviour for that row — usually "treat as non-subscriber" or "reject as inconsistent". Second, a reader checking completeness needs to see that those rows were considered, not forgotten.

## Step 5 — Fill in the actions, one sentence at a time

Take each sentence of the requirement and apply it to all the rows it covers. Working sentence by sentence, not row by row, makes contradictions visible: when a sentence wants to write into a cell that an earlier sentence already filled with something different, you have found a conflict.

1. *"Rides of 30 minutes or less are free for subscribers."* → rows with S = Y, L = N (5–8): no A, no B, no C.
2. *"Non-subscribers pay a flat unlock fee plus a per-minute rate."* → rows with S = N (10, 12, 14, 16): A and B.
3. *"Subscribers who ride longer than 30 minutes pay the per-minute rate for the extra time only."* → rows with S = Y, L = Y (1–4): C.
4. *"Electric bikes add a surcharge for everyone, except Plus subscribers."* → rows with E = Y and P = N (2, 6, 10, 14): D.

The result:

| # | S | L | E | P | A unlock | B per-min all | C per-min extra | D e-surcharge |
|---|---|---|---|---|---|---|---|---|
| 1 | Y | Y | Y | Y | | | X | |
| 2 | Y | Y | Y | N | | | X | X |
| 3 | Y | Y | N | Y | | | X | |
| 4 | Y | Y | N | N | | | X | |
| 5 | Y | N | Y | Y | | | | |
| 6 | Y | N | Y | N | | | | **X ?** |
| 7 | Y | N | N | Y | | | | |
| 8 | Y | N | N | N | | | | |
| 9, 11, 13, 15 | N | – | – | Y | *infeasible* | | | |
| 10 | N | Y | Y | N | X | X | | X |
| 12 | N | Y | N | N | X | X | | |
| 14 | N | N | Y | N | X | X | | X |
| 16 | N | N | N | N | X | X | | |

Look at row 6: a Basic subscriber takes an electric bike for twenty minutes. Sentence 1 says the ride is **free**. Sentence 4 says electric bikes add a surcharge **for everyone** except Plus. Which wins? The requirement does not say. That question mark is the most valuable thing the table has produced. In an interview you would point at it and say: "The text is ambiguous here. I would ask the product owner; my guess is that the surcharge applies, because otherwise there is no reason for the Plus exemption to exist on short rides — but I would not ship on a guess."

> [!INTERVIEW]
> Interviewers who set decision-table exercises nearly always plant one ambiguity or contradiction in the prose. Finding it and *reasoning about the likely intent* is the high-score outcome. Filling in the table perfectly while silently picking an interpretation is the average outcome.

## Step 6 — Read the table back as rules

A finished table should be readable back into sentences. If you cannot say a row as a sentence that a business person would agree with, something is wrong.

- Row 2: "A Basic subscriber on an electric bike for more than 30 minutes pays for the extra minutes and the electric surcharge."
- Row 16: "A non-subscriber on a normal bike for a short ride pays the unlock fee and per-minute rate."

Reading back also catches a quiet omission in this requirement: does the long-ride condition matter at all for non-subscribers? Rows 10 and 14 have identical actions, as do 12 and 16. So for non-subscribers, L is a don't-care. That is a fact worth confirming ("non-subscribers never get a free period?") and it will let us collapse the table in the next lesson.

## Step 7 — Derive tests

Each feasible row is a test case: set the conditions, perform the ride, check the charges. For this table that is twelve tests, plus:

- **Boundary tests for every threshold condition.** L hides the number 30. Test rides of 29, 30 and 31 minutes for a subscriber (and decide whether a ride of 30 minutes and 20 seconds is "longer than 30").
- **Tests for infeasible rows**, if the state can arise in the data.
- **Amount checks**, not only which charges apply: the table says C applies; a separate calculation says how much.

The ISTQB syllabus measures coverage for this technique as the share of feasible rule columns exercised by at least one test, so "full decision-table coverage" here means all twelve.

## The table as executable specification

Once written as patterns, a table can be run. This is the bridge to the coding problems in this module.

```python-run
# conditions: subscriber, long ride, electric, plus
RULES = [
    ("N--Y", {"INCONSISTENT"}),
    ("YY-Y", {"C"}),
    ("YYYN", {"C", "D"}),
    ("YYNN", {"C"}),
    ("YN-Y", set()),
    ("YNYN", {"D?"}),            # the ambiguous row
    ("YNNN", set()),
    ("N-YN", {"A", "B", "D"}),
    ("N-NN", {"A", "B"}),
]

def matches(pattern, inp):
    return all(p == "-" or p == c for p, c in zip(pattern, inp))

import itertools
for combo in itertools.product("YN", repeat=4):
    inp = "".join(combo)
    hits = [sorted(a) for p, a in RULES if matches(p, inp)]
    status = "ok" if len(hits) == 1 else ("GAP" if not hits else "CONFLICT")
    print(inp, hits, status)
```

Every input prints exactly one rule: the table is complete and consistent. Delete a rule and run it again to see a gap appear; add `("Y---", {"X"})` to see conflicts.

Two evaluation policies exist, and you must know which one a given system uses:

| Policy | Behaviour | Consequence |
|---|---|---|
| **First match** | Rules are tried top to bottom; the first that matches wins | Order matters; a broad rule placed early hides everything below it; a final catch-all gives a default |
| **Unique match** (order-independent) | Exactly one rule may match each input | Overlapping rules with different actions are an error; the table can be reordered freely |

Firewall rule lists, routing tables and many rule engines are first-match. Specification tables written by analysts are usually meant to be unique-match. Many real defects come from someone editing a first-match list as though order did not matter.

## Practice: build one yourself

**Requirement:** *A gym door opens for members with an active membership during staffed hours. Outside staffed hours it opens only for members on the 24-hour plan. Staff badges always open the door. A badge reported lost never opens the door.*

Build the full table, mark anything unclear, and state the number of tests. Then open the answer.

<details><summary>Model answer</summary>

**Conditions.**

1. S — is it a staff badge?
2. M — is the membership active? (meaningful for members)
3. H — is it within staffed hours?
4. T — is the holder on the 24-hour plan?
5. L — is the badge reported lost?

Five conditions → $2^5 = 32$ combinations.

**Actions.** Open the door; refuse. (A realistic system adds "log the attempt" and "alert on a lost badge", which I would raise.)

**Apply the sentences.**

- "A badge reported lost never opens the door" — *never* is the strongest word in the text, so it overrides "staff badges always open". All 16 rows with L = Y → refuse. This is the planted contradiction: *always* versus *never*. I state my reading and flag it for confirmation.
- "Staff badges always open the door" — the 8 rows with L = N, S = Y → open, regardless of M, H, T.
- Members (S = N, L = N), 8 rows:
  - M = N → refuse (4 rows). The text only grants access to active memberships.
  - M = Y, H = Y → open (2 rows).
  - M = Y, H = N, T = Y → open (1 row).
  - M = Y, H = N, T = N → refuse (1 row).

**Collapsed for reading** (order of conditions L S M H T):

| Rule | L | S | M | H | T | Action | Covers |
|---|---|---|---|---|---|---|---|
| 1 | Y | – | – | – | – | refuse | 16 |
| 2 | N | Y | – | – | – | open | 8 |
| 3 | N | N | N | – | – | refuse | 4 |
| 4 | N | N | Y | Y | – | open | 2 |
| 5 | N | N | Y | N | Y | open | 1 |
| 6 | N | N | Y | N | N | refuse | 1 |

16 + 8 + 4 + 2 + 1 + 1 = 32, so it is complete.

**Unclear points to raise.**

- Lost staff badge: refuse (my reading) — confirm.
- An *expired* membership on the 24-hour plan: the plan flag is irrelevant once M = N — confirm that expiry removes plan privileges.
- "Staffed hours" has boundaries: the minute staff arrive and leave; what if a member enters at 21:59 and the door also controls exit?
- Infeasible or odd rows: a staff badge with a membership plan. Harmless here because rule 2 ignores M and T.

**Tests.** Six from the collapsed table at minimum; for an access-control system I would run all 32, since the cost is small and a wrong "open" is a security failure. Plus boundary tests on the hour condition.

</details>

## Common construction mistakes

- **Starting to fill in before counting.** Without the target number you cannot know you are done.
- **Compound conditions.** "Member with a valid coupon" as one condition hides two of the four combinations.
- **Hiding a threshold.** A condition such as "large order" without the number attached loses the boundary test.
- **Filling in row by row.** You re-read the whole requirement sixteen times and still miss conflicts. Go sentence by sentence.
- **Deleting impossible rows.** Mark them instead, and ask whether "impossible" is guaranteed.
- **Resolving ambiguity silently.** Your interpretation may be right; the unasked question is still a defect in the requirement.
- **Forgetting the default.** What happens when no sentence applies? "Nothing" is an answer only if someone decided it.

## Summary

- A decision table separates conditions from actions and gives one rule per combination of condition values.
- Extract conditions as single yes/no facts with thresholds noted; keep actions atomic; read connectives carefully.
- $n$ yes/no conditions give $2^n$ rows; state the number first; generate rows in binary order.
- Mark infeasible rows instead of deleting them.
- Fill in sentence by sentence so that conflicts surface; read each row back as a sentence.
- Know whether the table is evaluated first-match or unique-match.
- Each feasible row is a test; every threshold adds boundary tests.

## Glossary

| Term | Meaning |
|---|---|
| Requirement | A statement of what a system must do |
| Condition | A yes/no question about the situation that affects the outcome |
| Action | Something the system does as a result |
| Rule | One row: a combination of condition values and the resulting actions |
| Condition entry | The value (Y, N or dash) of one condition in one rule |
| Don't-care | A dash meaning the condition is irrelevant to that rule |
| Infeasible combination | A combination that cannot occur in reality |
| Extended-entry table | A table in which a condition can take more than two values |
| First match | Evaluating rules top to bottom and stopping at the first that applies |
| Unique match | Requiring that exactly one rule applies to each input |
| Threshold | A numeric limit at which behaviour changes |

## Check yourself

```quiz
[
  {"q": "A requirement mentions these facts: is member, order over 50, has coupon, item on sale, express requested. How many rows does the full yes/no table have?",
   "options": ["10", "16", "25", "32"],
   "answer": 3,
   "explain": "Five independent yes/no conditions give 2^5 = 32 combinations."},
  {"q": "Which is a well-formed condition?",
   "options": ["Member with coupon", "Is the order total over 50?", "Apply the discount", "Large or urgent order"],
   "answer": 1,
   "explain": "It asks about one fact, is phrased positively and names its threshold. The others are compound, an action, or vague."},
  {"q": "Why fill in the table sentence by sentence rather than row by row?",
   "options": ["It uses less paper", "A sentence that tries to write a different action into an already filled cell exposes a contradiction", "Rows must be filled alphabetically", "It avoids the need to count combinations"],
   "answer": 1,
   "explain": "Applying one requirement at a time across all matching rows makes conflicting requirements collide visibly."},
  {"q": "A combination is believed impossible (Plus plan without a subscription). What is the best handling?",
   "options": ["Delete the row", "Mark it infeasible, and ask whether the data could still contain it and what should happen", "Give it a random action", "Ignore the Plus condition entirely"],
   "answer": 1,
   "explain": "Marking shows it was considered; asking guards against states the rest of the system fails to prevent."},
  {"q": "One condition has three values (none, Basic, Plus) and two others are yes/no. How many combinations?",
   "options": ["7", "8", "12", "16"],
   "answer": 2,
   "explain": "Multiply the numbers of values: 3 × 2 × 2 = 12."},
  {"q": "In a first-match rule list, a rule '- - -  → deny' is placed at the top. What happens?",
   "options": ["Nothing changes", "Every input matches it first, so all later rules are unreachable", "Only the last rule applies", "The table becomes unique-match"],
   "answer": 1,
   "explain": "Under first-match evaluation, order matters and a catch-all hides everything below it; it belongs at the bottom as a default."},
  {"q": "'Free delivery only if the order exceeds 50' guarantees what?",
   "options": ["Orders over 50 always get free delivery", "Orders of 50 or less never get free delivery", "Both of the above", "Neither"],
   "answer": 1,
   "explain": "'Only if' states a necessary condition. It forbids free delivery below the threshold and does not promise it above."},
  {"q": "Besides one test per feasible rule, what should always be added for a condition like 'ride longer than 30 minutes'?",
   "options": ["Tests with a different font", "Boundary tests at 29, 30 and 31 minutes", "A second copy of every test", "Nothing"],
   "answer": 1,
   "explain": "A yes/no condition built on a threshold hides a boundary; the table tests the logic and boundary tests check the threshold itself."}
]
```

> **Source:** ISTQB Certified Tester Foundation Level syllabus v4.0, section 4.2.3 "Decision Table Testing" (https://www.istqb.org/certifications/certified-tester-foundation-level), explained in original wording with original examples and code.
