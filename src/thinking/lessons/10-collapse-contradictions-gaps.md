# Collapsing tables, contradictions and gaps

> **Before this lesson:** read [Building a decision table from requirements](#/lesson/thinking/building-decision-tables). You should be comfortable reading a rule such as `Y N –`.

## In plain words

Imagine a bus timetable. Three things can be wrong with it. A stop might be missing altogether, so that passengers there have no idea when a bus comes: a **gap**. Two lines of the timetable might give different times for the same bus at the same stop: a **contradiction**. Or the same information might be printed five times where once would do, making the sheet hard to read: **redundancy**.

A decision table can have the same three faults. A gap is a combination of circumstances that no rule covers. A contradiction is a combination that two rules cover with different outcomes. Redundancy is repetition that can be merged away — the tidying-up is called **collapsing**.

Interview exercises of the form "here is a table — what is wrong with it?" are checking for exactly these. This lesson gives a method for each that you can carry out by hand and that also translates directly into the small programs in this module's problems.

A decision table is only useful if it is **correct as a table**, before anyone asks whether the business rules themselves are wise. Three properties make it correct:

- **Complete** — every possible input is covered by some rule (no *gaps*).
- **Consistent** — no input is covered by two rules that disagree (no *contradictions*).
- **Minimal enough to read** — no pointless repetition (no *redundancy*), achieved by collapsing rules with don't-cares.

Interview exercises of the form "here is a table — what is wrong with it?" are checking exactly these three. This lesson gives you a method for each that works by hand and translates directly to code.

Notation, as in the previous lesson: a rule is a pattern over the conditions plus an action, such as `Y N – → standard`. A dash means the condition is irrelevant to that rule.

## Counting with don't-cares

The single most useful fact:

> A rule with $d$ dashes covers $2^d$ fully specified inputs.

`Y N –` covers `YNY` and `YNN`. `– – –` covers all eight inputs of a three-condition table. `Y Y Y` covers one.

This gives a fast completeness check, the **$2^n$ rule**: add up $2^d$ over all rules. For a complete table with no overlapping rules, the sum is exactly $2^n$.

| Sum compared with $2^n$ | What it tells you |
|---|---|
| Less | There are definitely gaps |
| Equal | Complete **if** no two rules overlap |
| More | Some rules definitely overlap (redundancy or contradiction) |

The middle row hides a trap. A sum equal to $2^n$ does not prove completeness, because an overlap and a gap can cancel out. Example with two conditions ($2^2 = 4$):

| Rule | A | B | Action | Covers |
|---|---|---|---|---|
| 1 | Y | – | x | 2 |
| 2 | – | Y | y | 2 |

The sum is 4. Yet `YY` is covered twice and `NN` is not covered at all. So the counting rule is a quick screen; a full check needs one of the methods below.

## Finding gaps

### Method 1 — expand and tick

Write all $2^n$ inputs in binary order. For each rule, tick the inputs it covers. Unticked inputs are gaps. This is foolproof and fine up to four or five conditions.

A three-condition example: a streaming service decides video quality from *premium account* (P), *fast connection* (F), *data-saver on* (D).

| Rule | P | F | D | Action |
|---|---|---|---|---|
| 1 | – | – | Y | low |
| 2 | Y | Y | N | ultra |
| 3 | N | Y | N | high |
| 4 | N | N | N | low |

Count: 4 + 1 + 1 + 1 = 7, less than 8, so there is a gap. Expanding:

| Input PFD | Covered by |
|---|---|
| YYY | 1 |
| YYN | 2 |
| YNY | 1 |
| **YNN** | **none** |
| NYY | 1 |
| NYN | 3 |
| NNY | 1 |
| NNN | 4 |

The gap is `YNN`: a premium customer on a slow connection without data-saver. The authors thought about premium only in terms of what it *adds*. That is how most gaps arise — a condition is considered only in the scenario where it is exciting.

### Method 2 — split on a condition

For larger tables, divide and conquer. Pick a condition, split the rules into those that apply when it is Y and those that apply when it is N (a rule with a dash goes to both sides), drop that condition, and check each half the same way. A half with no rules at all is a block of gaps; a half containing an all-dash rule is fully covered.

For the table above, split on D. *D = Y:* rule 1 becomes `– –`, which covers everything. Done. *D = N:* rules 2, 3, 4 become `YY`, `NY`, `NN` over (P, F); splitting on P: for P = Y only `Y` (F = Y) remains, so F = N is missing → the gap `Y N N`. Same answer, less writing.

### What to do with a gap

A gap is a question, not only a hole. The possible resolutions:

1. **A rule is missing** — ask the business what should happen and add it.
2. **The combination is impossible** — record it as infeasible, and check that the rest of the system truly prevents it.
3. **A default applies** — then write the default as an explicit final rule, so that "nothing happens" was decided by somebody.

In live systems, gaps turn into whatever the code happens to do: an exception, a null, or — in first-match engines with a catch-all — a default that nobody consciously chose for that case.

```python-run
import itertools

def matches(pattern, inp):
    return all(p == "-" or p == c for p, c in zip(pattern, inp))

def gaps(n, rules):
    return [s for s in ("".join(p) for p in itertools.product("NY", repeat=n))
            if not any(matches(pat, s) for pat, _ in rules)]

quality = [("--Y", "low"), ("YYN", "ultra"), ("NYN", "high"), ("NNN", "low")]
print("sum of 2^dashes:", sum(2 ** pat.count("-") for pat, _ in quality), "of", 2 ** 3)
print("gaps:", gaps(3, quality))
```

## Finding contradictions

Two rules **overlap** when some input matches both. They **contradict** when they overlap and prescribe different actions. They are merely **redundant** when they overlap and agree.

### The pairwise overlap test

You do not need to expand anything. Compare two patterns position by position:

> Two rules overlap **unless** there is at least one position where one says Y and the other says N.

A dash is compatible with anything. So `Y – N` and `– Y N` overlap (no position clashes; the shared input is `YYN`), while `Y – N` and `N Y –` do not (position 1 clashes).

To construct a **witness** — a concrete input matching both — take, at each position, whichever rule has a definite value, and choose either value if both have dashes.

A four-condition example: an expense system routes claims using *amount over 1,000* (A), *has receipt* (R), *submitter is a manager* (M), *travel category* (T).

| Rule | A | R | M | T | Action |
|---|---|---|---|---|---|
| 1 | N | Y | – | – | auto-approve |
| 2 | – | N | – | – | reject |
| 3 | Y | Y | N | – | director approval |
| 4 | Y | Y | Y | – | auto-approve |
| 5 | – | – | – | Y | travel-desk review |

Check each pair:

| Pair | Clash position? | Overlap | Actions | Verdict |
|---|---|---|---|---|
| 1, 2 | R: Y vs N | no | | fine |
| 1, 3 | A: N vs Y | no | | fine |
| 1, 4 | A: N vs Y | no | | fine |
| 1, 5 | none | yes — witness `N Y – Y` | approve vs travel desk | **contradiction** |
| 2, 3 | R | no | | fine |
| 2, 4 | R | no | | fine |
| 2, 5 | none | yes — `– N – Y` | reject vs travel desk | **contradiction** |
| 3, 4 | M | no | | fine |
| 3, 5 | none | yes — `Y Y N Y` | director vs travel desk | **contradiction** |
| 4, 5 | none | yes — `Y Y Y Y` | approve vs travel desk | **contradiction** |

Rule 5 collides with every other rule. Someone added "travel claims go to the travel desk" as an afterthought, without saying how it interacts with what was already there. This is the most common way contradictions are born: **a new rule written in isolation with dashes everywhere it did not think about.**

### Resolving a contradiction

There are only three honest fixes, and choosing between them is a business decision you should surface, not make silently:

1. **Priority.** Declare that one rule wins — "travel-desk review overrides everything except rejection for a missing receipt" — and rewrite the patterns so they no longer overlap (add T = N to rules 1, 3 and 4; narrow rule 5 to R = Y).
2. **Both actions.** Perhaps the claim needs director approval *and* a travel-desk review. Then the action set for the overlapping inputs is the union, and the table needs action columns rather than one action per rule.
3. **Ordering by design.** Keep the overlap and state that the table is first-match, with rule order as the priority. This is legitimate but fragile; document it at the top of the table.

```python-run
def overlap(p, q):
    return all(a == "-" or b == "-" or a == b for a, b in zip(p, q))

def witness(p, q):
    return "".join(a if a != "-" else (b if b != "-" else "Y") for a, b in zip(p, q))

expenses = [("NY--", "auto-approve"), ("-N--", "reject"), ("YYN-", "director"),
            ("YYY-", "auto-approve"), ("---Y", "travel desk")]
for i in range(len(expenses)):
    for j in range(i + 1, len(expenses)):
        (p, a), (q, b) = expenses[i], expenses[j]
        if overlap(p, q):
            kind = "REDUNDANT" if a == b else "CONTRADICTION"
            print(f"rules {i+1} and {j+1}: {kind}, e.g. input {witness(p, q)} -> {a} / {b}")
```

> [!INTERVIEW]
> When asked "is anything wrong with this table?", run three checks in a fixed order and say so: "First I count coverage against 2^n. Then I look for overlaps pair by pair. Then I look for rows that can be merged." Announcing the procedure matters as much as the findings — it shows that your thoroughness does not depend on luck.

## Collapsing: merging rules with don't-cares

### The merge rule

> Two rules can be merged when they have the **same action** and their patterns are **identical except in exactly one position**, where one has Y and the other N. The merged rule has a dash in that position.

`Y Y N → a` and `Y N N → a` merge to `Y – N → a`. Then `Y – N → a` and `N – N → a` merge to `– – N → a`. Repeat until no pair qualifies.

Take the fully expanded table for the gym door from the previous lesson, restricted to members (three conditions: active membership M, staffed hours H, 24-hour plan T):

| M | H | T | Action |
|---|---|---|---|
| Y | Y | Y | open |
| Y | Y | N | open |
| Y | N | Y | open |
| Y | N | N | refuse |
| N | Y | Y | refuse |
| N | Y | N | refuse |
| N | N | Y | refuse |
| N | N | N | refuse |

Merging: `YYY` + `YYN` → `YY–` open. The four `N..` rows merge pairwise then again → `N––` refuse. Result so far:

| M | H | T | Action |
|---|---|---|---|
| Y | Y | – | open |
| Y | N | Y | open |
| Y | N | N | refuse |
| N | – | – | refuse |

Four disjoint rules; 2 + 1 + 1 + 4 = 8. This is the natural hand-collapsed table.

### Overlap can make it smaller still

Can "open" be expressed in fewer than two rules? No single pattern covers exactly {YYY, YYN, YNY}. But notice an alternative pair: `Y Y –` and `Y – Y`. Both are legal — everything they cover is "open" — and they overlap on `YYY`. The count is still two, so nothing is gained here, but in other tables allowing overlap *does* reduce the count. Classic example over two conditions:

| A | B | Action |
|---|---|---|
| Y | Y | go |
| Y | N | go |
| N | Y | go |
| N | N | stop |

Disjoint merging gives `Y –` go, `N Y` go, `N N` stop — three rules. The overlapping form `Y –` go, `– Y` go, `N N` stop is also three, but each "go" rule is simpler: it reads "go if A; go if B". With more conditions, the overlapping form can have strictly fewer rules. Engineers will recognise this as Boolean minimisation, the same problem solved by Karnaugh maps; each maximal legal pattern is a *prime implicant*, and the task is to cover all inputs of an action with as few of them as possible.

For hand work the practical rule is: **merge greedily, then look for any rule whose inputs are all covered by wider legal patterns.** For exact minimisation on small tables, a program can try every candidate pattern — which is what the hardest problem in this module asks for.

### Merge order matters

Greedy merging can get stuck above the minimum, depending on which pairs you take first. Consider "a" on six inputs of three conditions arranged in a ring: `NNN, NNY, NYY, YYY, YYN, YNN`.

- Lucky order: `NNN+NNY → NN–`, `NYY+YYY → –YY`, `YYN+YNN → Y–N`. Three rules.
- Other lucky order: `NNY+NYY → N–Y`, `YYY+YYN → YY–`, `YNN+NNN → –NN`. Also three.
- Unlucky mix: `NNN+NNY → NN–`, `YYY+YYN → YY–`, leaving `NYY` and `YNN` alone. Four rules, and nothing more merges.

So if a hand-collapsed table looks suspiciously large, try a different starting pair.

### When *not* to collapse

A don't-care is a claim: "this condition has no effect here". Collapsing is safe for documentation. For testing it is a risk decision:

- If the conditions are evaluated independently in the implementation, one test per collapsed rule is reasonable.
- If the dashed condition might take a different code path — even one that should lead to the same action — test both values for high-risk rules.
- Never merge across a **gap**. If `YNN` is unspecified, you may not write `Y – N` merely because `YYN` has the action you like. A gap must stay a gap until someone decides it.
- Never merge rules whose actions merely *look* similar ("approve" and "approve with note").

## A full audit, start to finish

**Exercise.** A parcel company prices deliveries with four conditions: *weight over 20 kg* (W), *international* (I), *customer has a contract* (C), *fragile* (F). Audit this table: list gaps, contradictions and redundancies, then propose a corrected, collapsed table. Attempt before opening.

| Rule | W | I | C | F | Action |
|---|---|---|---|---|---|
| 1 | N | N | – | N | standard |
| 2 | N | N | – | Y | standard + care fee |
| 3 | Y | N | Y | – | freight (contract rate) |
| 4 | Y | N | N | N | freight |
| 5 | – | Y | Y | – | international (contract rate) |
| 6 | N | Y | N | – | international |
| 7 | Y | – | Y | Y | freight (contract rate) + care fee |

<details><summary>Model answer</summary>

**1. Count.** Rule sizes: 2, 2, 2, 1, 4, 2, 2 → 15. There are $2^4 = 16$ inputs. Fifteen is less than sixteen, so at least one gap exists — and possibly more, if rules overlap.

**2. Overlaps, pair by pair** (only pairs without a clashing position):

- Rules 3 and 7: `Y N Y –` versus `Y – Y Y` → no clash; witness `Y N Y Y`. Actions differ (contract freight versus contract freight + care fee) → **contradiction**. A heavy, domestic, fragile contract parcel: does it pay the care fee?
- Rules 5 and 7: `– Y Y –` versus `Y – Y Y` → no clash; witness `Y Y Y Y`. International contract rate versus freight contract rate + care fee → **contradiction**.
- All other pairs clash somewhere (check: 1–2 on F; 1, 2 versus 3, 4, 7 on W; 1, 2 versus 5, 6 on I; 3–4 on C; 3, 4 versus 5, 6 on I; 4–7 on C; 5–6 on C; 6–7 on W).

Two inputs are double-covered, so the distinct inputs covered are 15 − 2 = 13, meaning **three gaps**.

**3. Gaps** (expand and tick, or reason by region):

- Domestic and light (W = N, I = N): rules 1 and 2 cover all four. Fine.
- Domestic and heavy (W = Y, I = N): contract → rule 3 (both F); no contract, not fragile → rule 4; **no contract, fragile → nothing: `Y N N Y`**.
- International with contract: rule 5. Fine.
- International, no contract: light → rule 6; **heavy → nothing: `Y Y N N` and `Y Y N Y`**.

Gaps: `YNNY`, `YYNN`, `YYNY`. All three involve a heavy parcel from a customer without a contract — the authors treated heavy freight as something contract customers do.

**4. Redundancy.** None beyond the contradictions.

**5. Questions for the business.**

- Does the care fee apply to fragile freight for contract customers? (Rule 7 suggests yes; then rule 3 should be restricted to F = N.)
- Is the care fee charged on international parcels at all? Rules 5 and 6 ignore F; rule 7 partly says yes.
- What is charged for heavy, non-contract, fragile domestic parcels, and for heavy international parcels without a contract — or are those refused?

**6. A corrected proposal**, assuming the answers are "care fee applies to all fragile freight, not to international; heavy international needs a contract":

| Rule | W | I | C | F | Action |
|---|---|---|---|---|---|
| 1 | N | N | – | N | standard |
| 2 | N | N | – | Y | standard + care fee |
| 3 | Y | N | Y | N | freight (contract rate) |
| 4 | Y | N | Y | Y | freight (contract rate) + care fee |
| 5 | Y | N | N | N | freight |
| 6 | Y | N | N | Y | freight + care fee |
| 7 | – | Y | Y | – | international (contract rate) |
| 8 | N | Y | N | – | international |
| 9 | Y | Y | N | – | refuse: contract required |

Count: 2 + 2 + 1 + 1 + 1 + 1 + 4 + 2 + 2 = 16, and every pair clashes in some position, so the table is complete and consistent. It cannot be collapsed further without changing an action, because the remaining adjacent rules differ in their fees.

**What to say at the end.** "The table had three gaps and two contradictions, all around heavy parcels and the care fee. I have listed the three questions I would need answered, and shown what the table looks like under one plausible set of answers."

</details>

## Summary

- A rule with $d$ dashes covers $2^d$ inputs. Summing these against $2^n$ is a fast screen: less means gaps, more means overlaps, equal means complete only if nothing overlaps.
- Find gaps by expanding and ticking, or by splitting on one condition at a time. A gap is a question: missing rule, impossible case or unstated default.
- Two rules overlap unless some position has Y in one and N in the other. Overlap with different actions is a contradiction; with the same action, a redundancy.
- Contradictions usually come from a new rule written with dashes for everything its author did not consider. Resolve by priority, by combining actions, or by explicit ordering — and make the choice visible.
- Merge rules that share an action and differ in exactly one position. Allowing overlap can reduce the count further; merge order can leave you above the minimum.
- Never merge across a gap, and test both values of a don't-care when the risk is high.

## Glossary

| Term | Meaning |
|---|---|
| Complete | Every possible input is covered by at least one rule |
| Consistent | No input is covered by rules with different actions |
| Gap | An input that no rule covers |
| Contradiction | Two overlapping rules that prescribe different actions |
| Redundancy | Overlapping rules that prescribe the same action |
| Overlap | Two rules that both match at least one input |
| Witness | A concrete input demonstrating an overlap or a gap |
| Collapse (merge) | Combine rules into fewer rules using don't-cares |
| 2^n rule | Comparing the inputs covered by all rules with the total of 2 to the power n |
| Prime implicant | A rule that cannot be widened further without changing an outcome |
| Karnaugh map | A grid method for simplifying yes/no logic by eye |

## Check yourself

```quiz
[
  {"q": "A table over 4 conditions has rules with 3, 2, 1, 1 and 0 dashes. What does the 2^n rule say?",
   "options": ["Sum is 16, so it is certainly complete", "Sum is 17, so at least two rules overlap", "Sum is 15, so there is a gap", "Nothing can be concluded"],
   "answer": 1,
   "explain": "8 + 4 + 2 + 2 + 1 = 17, which exceeds 2^4 = 16, so some input is covered more than once."},
  {"q": "Do the rules 'Y - N -' and '- Y - N' overlap?",
   "options": ["No, they differ in every position", "Yes; for example input Y Y N N matches both", "Only under first-match evaluation", "Only if their actions are equal"],
   "answer": 1,
   "explain": "No position has Y in one and N in the other, so a common input exists: take the definite value at each position."},
  {"q": "The sum of 2^dashes equals 2^n exactly. Is the table complete?",
   "options": ["Yes, always", "Only if no two rules overlap; an overlap can hide a gap", "No, never", "Only for tables with one action"],
   "answer": 1,
   "explain": "Double-covered inputs inflate the sum, so an overlap and a gap can cancel out."},
  {"q": "Which pair of rules can be merged?",
   "options": ["Y N Y → a and Y N N → b", "Y N Y → a and N Y Y → a", "Y N Y → a and Y Y Y → a", "Y - Y → a and N N N → a"],
   "answer": 2,
   "explain": "Same action and they differ in exactly one position (the second), giving Y - Y → a."},
  {"q": "A new rule '- - - Y → manual review' is added to an existing complete table. What is the most likely defect?",
   "options": ["A gap", "Contradictions with existing rules for inputs where the fourth condition is Y", "Nothing; more rules are always safe", "The table becomes too small"],
   "answer": 1,
   "explain": "A rule with dashes everywhere overlaps every existing rule that allows Y in that position; unless actions agree, each overlap is a contradiction."},
  {"q": "Input Y N N is unspecified, and Y Y N → approve. Why must you not write 'Y - N → approve'?",
   "options": ["Dashes are not allowed in the middle", "It would silently assign an action to a gap that nobody decided", "It makes the table longer", "It violates first-match order"],
   "answer": 1,
   "explain": "Merging across a gap invents a rule. The gap should be raised as a question."},
  {"q": "What are the honest ways to resolve a contradiction between two overlapping rules?",
   "options": ["Delete whichever rule is longer", "Decide a priority, combine the actions, or make ordering explicit — and surface the choice", "Ignore it if tests pass", "Add a third rule that overlaps both"],
   "answer": 1,
   "explain": "The overlap reflects an undecided business question; the fix is a visible decision, not a silent edit."},
  {"q": "Greedy pairwise merging produced four rules for an action; a colleague found three. What happened?",
   "options": ["One of you made an arithmetic error for certain", "Merge order matters: a different choice of first pairs can leave isolated rules that no longer merge", "Three is impossible", "Greedy merging is always optimal"],
   "answer": 1,
   "explain": "On ring-shaped layouts, some pairings strand single inputs. Trying another order, or allowing overlap, reaches the smaller table."}
]
```

> **Source:** ISTQB Certified Tester Foundation Level syllabus v4.0, section 4.2.3 "Decision Table Testing" (https://www.istqb.org/certifications/certified-tester-foundation-level). The collapsing procedure is standard Boolean minimisation (Karnaugh maps, Quine–McCluskey) presented in original wording with original examples and code.
