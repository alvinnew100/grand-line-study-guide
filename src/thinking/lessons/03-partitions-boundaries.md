# Equivalence partitioning and boundary value analysis

> **Before this lesson:** read [A seven-step answer framework](#/lesson/thinking/answer-framework). No testing background is assumed; if you can compare two numbers you can follow everything here.

## In plain words

A baker who wants to know whether a batch of a thousand biscuits is good does not eat all thousand. They taste one from each tray — because biscuits on the same tray baked under the same conditions — and they look hardest at the ones from the edge of the tray, where things most often go wrong.

Testing software uses the same two ideas. **Testing** means running a program with chosen inputs to see whether it behaves as it should; a single such check is a **test case**. Since nobody can try every possible input, **equivalence partitioning** groups inputs that the program should treat alike and tries one from each group (one biscuit per tray). **Boundary value analysis** then adds the values at the edges of each group (the biscuits at the edge), because mistakes cluster there.

Interviewers hope to hear these two ideas in any "how would you test…?" answer, and working testers use them every day to turn an endless set of possibilities into a short, defensible list.

A text field that accepts an age can receive billions of different inputs. You cannot try them all, and you do not need to. Two of the oldest ideas in test design tell you which handful to try: **equivalence partitioning** chooses *which kinds* of value, and **boundary value analysis** chooses *which exact values*. They are the techniques interviewers most hope to hear in a "how would you test…" answer, because they turn "I'd try some inputs" into a reasoned, countable set.

Both are *black-box* techniques: they work from what the product is supposed to do, with no need to read its code.

## The problem: too many inputs

Suppose a cinema's booking form has one rule: *tickets are sold to people aged 0 to 120; under 12 is a child ticket, 12 to 64 an adult ticket, 65 and over a senior ticket.*

Exhaustive testing would try every integer the field can hold, plus letters, blanks, decimals and pasted emoji. That is unbounded. The opposite extreme — try `30`, see an adult ticket, declare victory — tests one behaviour out of several. We want the smallest set of inputs that still gives each *distinct behaviour* a chance to fail.

## Equivalence partitioning

**Idea:** divide the input space into groups such that the system is expected to treat every member of a group the same way. If one member works, the others very probably work; if one fails, the others very probably fail. Then test one representative from each group.

A group is called an **equivalence partition** or equivalence class. Two properties make a set of partitions correct:

1. **They cover everything** — every possible input falls into some partition.
2. **They do not overlap** — no input falls into two.

For the cinema rule, the partitions of the age field are:

| # | Partition | Kind | Expected behaviour | Representative |
|---|---|---|---|---|
| 1 | below 0 | invalid | rejected | −5 |
| 2 | 0 to 11 | valid | child ticket | 6 |
| 3 | 12 to 64 | valid | adult ticket | 30 |
| 4 | 65 to 120 | valid | senior ticket | 80 |
| 5 | above 120 | invalid | rejected | 200 |
| 6 | not an integer | invalid | rejected | `abc`, `12.5`, empty |

Six tests instead of infinity, and each has a clear reason to exist. Note two things.

**Invalid partitions count.** Beginners list the three ticket types and stop. Half of the partitions above are invalid, and real defects cluster there, because developers spend most of their attention on the cases the product was built for.

**"Not an integer" is really several partitions.** Empty input, text, a decimal, a number with spaces, a number too large for the variable — each might be handled by a different piece of code. How finely you split depends on risk and on how the system is likely to be built. Splitting more is cheap; forgetting a class is expensive.

### Partitions are not only numeric ranges

The same thinking applies to any kind of input or situation:

| Input | Example partitions |
|---|---|
| A set of allowed values | each value may be its own partition (payment by coin / card / phone), plus "anything else" |
| A string | empty; typical; maximum length; too long; contains special characters; different script |
| A file upload | allowed type; disallowed type; zero bytes; huge; corrupted; correct extension with wrong content |
| A collection | empty; one item; many; duplicates; at capacity; over capacity |
| Time | before opening; during; after closing; across midnight; across a clock change |
| State of the system | logged in / out; stock available / sold out; network up / down |
| Output | each distinct kind of result (approved / referred / rejected) should be produced at least once |

The last row is easy to miss: you can partition by **outputs** as well. If a loan system can answer "approve", "refer" or "reject", make sure your tests cause each answer at least once, then work backwards to inputs that produce them.

### Combining several inputs

When a form has several fields, the usual rule is:

- **Valid partitions can share tests.** One test can use a valid age, a valid seat and a valid payment type at once, covering one valid partition from each field.
- **Invalid partitions get a test each.** If a single test has an invalid age *and* an invalid seat, the system may stop at the first error and never exercise the second check — one failure hides the other. So change one field to invalid at a time, keeping the others valid.

With three fields that have 3, 2 and 4 valid partitions and 2, 1 and 2 invalid ones, you need max(3, 2, 4) = 4 valid tests and 2 + 1 + 2 = 5 invalid tests: nine in total, not 5 × 3 × 6 = 90.

> [!NOTE]
> The ISTQB syllabus defines coverage for this technique as the number of partitions exercised by at least one test divided by the number of partitions identified. "100 % partition coverage" therefore means every partition you listed has a test — it says nothing about partitions you failed to think of.

## Boundary value analysis

Partitioning says "pick any value from 12–64". Experience says the value matters: defects love the edges. Somewhere in the code is a comparison, and the programmer had to choose between `<` and `<=`, between `12` and `11`. A test with age 30 cannot tell those apart. A test with age 12 can.

**Boundary value analysis (BVA)** tests the values at and around the edge of each ordered partition. It only applies when the partition has an order — numbers, dates, lengths, counts.

For a partition from `lo` to `hi` inclusive, the boundary values are `lo` and `hi`. There are two common intensities:

- **2-value BVA:** for each boundary, test the boundary itself and its nearest neighbour in the adjacent partition: `lo − 1, lo` and `hi, hi + 1`.
- **3-value BVA:** for each boundary, test the boundary and both neighbours: `lo − 1, lo, lo + 1` and `hi − 1, hi, hi + 1`.

For the adult partition 12–64:

| Variant | Values |
|---|---|
| 2-value | 11, 12, 64, 65 |
| 3-value | 11, 12, 13, 63, 64, 65 |

Why would anyone need the third value? Consider the faulty condition `if age == 12` written where `age >= 12` was intended. With 2-value BVA you test 11 (rejected as adult — correct) and 12 (adult — correct). The bug survives. The 3-value variant adds 13, which exposes it. The cheaper variant catches the common `<` versus `<=` slip; the fuller one also catches a wrong operator.

Across the whole age field, adjacent partitions share boundaries, so the full 2-value set is small:

`−1, 0, 11, 12, 64, 65, 120, 121`

Eight numbers, and each sits on one side of a decision.

```python-run
def boundary_values(lo, hi, three_value=False):
    vals = {lo - 1, lo, hi, hi + 1}
    if three_value:
        vals |= {lo + 1, hi - 1}
    return sorted(vals)

partitions = {"child": (0, 11), "adult": (12, 64), "senior": (65, 120)}
all_vals = set()
for name, (lo, hi) in partitions.items():
    v = boundary_values(lo, hi)
    all_vals |= set(v)
    print(f"{name:7s} 2-value: {v}   3-value: {boundary_values(lo, hi, True)}")
print("whole field, 2-value:", sorted(all_vals))
```

### A buggy implementation, caught

Run the next block. The function has a single-character defect. See which of the two test sets finds it.

```python-run
def ticket(age):
    if age < 0 or age > 120:
        return "reject"
    if age < 12:
        return "child"
    if age < 64:          # bug: should be age < 65
        return "adult"
    return "senior"

def expected(age):
    if age < 0 or age > 120: return "reject"
    if age <= 11: return "child"
    if age <= 64: return "adult"
    return "senior"

representatives = [-5, 6, 30, 80, 200]
boundaries = [-1, 0, 11, 12, 64, 65, 120, 121]
for name, tests in [("partition representatives", representatives), ("boundary values", boundaries)]:
    fails = [a for a in tests if ticket(a) != expected(a)]
    print(f"{name}: {len(tests)} tests, failures at {fails}")
```

The mid-range representatives all pass. Only the boundary test at 64 fails. That is the whole argument for BVA in six lines of output.

### Where boundaries hide

Interviewers like candidates who find boundaries that are not written in the prompt.

- **Lengths and sizes:** minimum and maximum characters, 0 items, 1 item, the maximum count, one more than the maximum.
- **Time:** the last second of a discount, midnight, the end of a month, 29 February, the hour that repeats or vanishes on a clock change, a session that expires at exactly its timeout.
- **Money:** zero, the smallest unit, an amount exactly equal to the balance, one unit above the limit, rounding at half a cent.
- **Capacity:** a full disk, a full coin tube, the last item in stock, the 101st connection to a pool of 100.
- **Data types:** the largest 32-bit integer, the longest string a column can store, precision of floating-point numbers.
- **Counters:** the third failed login when lockout is at three, the first request after a rate-limit window resets.

A boundary always has two sides. When someone tells you a limit, your next question is "inclusive or exclusive?" — and then you test both sides whatever the answer was.

> [!INTERVIEW]
> Saying "is the 100-character limit inclusive?" during the clarify step is a tiny, high-value signal. It shows that you hear a specification the way a tester does: every number in it is a place where two people may have understood different things.

## Using both together: a worked field

**Prompt fragment:** *"The password must be 8 to 64 characters, with at least one digit."* Design the tests for the length and digit rules. Try before opening.

<details><summary>Model answer</summary>

Two characteristics: **length** (ordered, so partitions and boundaries) and **contains a digit** (yes or no).

Length partitions: 0 (empty) — arguably its own class; 1–7 too short; 8–64 valid; 65 and above too long.

Boundary values, 2-value: 7, 8, 64, 65. I add 0 and a very long value (say 10,000 characters) as special cases, because empty input and oversized input often take different code paths (a required-field check; a request-size limit).

Digit partitions: has at least one digit; has none. Position may matter if the check is sloppy, so I vary it: digit first, digit last, digit only.

Tests, changing one thing at a time for the invalid cases:

| # | Length | Digit | Expected | Why |
|---|---|---|---|---|
| 1 | 8 | yes, at the end | accept | lower boundary, valid |
| 2 | 64 | yes, at the start | accept | upper boundary, valid |
| 3 | 30 | yes, in the middle | accept | typical |
| 4 | 7 | yes | reject: too short | immediately below the lower boundary |
| 5 | 65 | yes | reject: too long | immediately above the upper boundary |
| 6 | 0 | — | reject: required | empty class |
| 7 | 10,000 | yes | reject, no crash or slowdown | oversize class |
| 8 | 8 | no | reject: needs a digit | invalid digit class, valid length |
| 9 | 8 | all digits | accept (unless another rule forbids it) | edge of the digit rule |

Then questions that reveal hidden boundaries: is length counted in characters or bytes (an emoji may be four bytes)? Are leading and trailing spaces trimmed before counting? Does a full-width digit `７` count as a digit? Each answer adds one or two tests.

Nine tests, each with a reason, plus three questions. That is a complete answer for this fragment.

</details>

## Common mistakes

**Forgetting the invalid side.** The lists above are roughly half invalid. If yours is not, look again.

**Overlapping or leaky partitions.** "0–12 child, 12–64 adult" assigns 12 twice. Spotting this in a specification is a finding in itself — report it rather than quietly choosing.

**Testing two invalid values at once.** One error masks the other.

**Picking the boundary on only one side.** Testing 12 and never 11 proves that 12 is an adult but not that 11 is a child.

**Treating BVA as applying to unordered sets.** There is no "boundary" between coin, card and phone payment. Use one test per value instead.

**Assuming partitions are truly equivalent.** They are a hypothesis. If you know that amounts over 999 are displayed with a thousands separator, then 1,000 is a boundary even though the requirement never mentions it. Knowledge of likely implementation refines the partitions.

**Stopping at inputs.** Outputs, configuration values and internal counters have partitions and boundaries too.

## How this sounds in an interview

You will rarely be asked "explain equivalence partitioning". You will be asked to test something, and the technique shows up as a way of speaking:

> "For the coin slot I'd group inputs into classes rather than listing coins one by one: each accepted denomination; coins of the right currency that the machine does not take; foreign coins of similar size; damaged or bent coins; and non-coins such as washers or tokens. One or two from each class. Then for the credit total I'd look at boundaries: exactly the price, one unit under, one unit over, and the largest credit the machine will hold."

That paragraph names no technique and plainly uses both. If the interviewer asks "why those values?", you can now give the reason: each represents a class the machine should treat uniformly, and the numeric picks sit where a comparison flips.

## Summary

- Equivalence partitioning groups inputs the system should treat alike and tests one per group. Partitions must cover everything and must not overlap.
- Always include invalid partitions; change only one input to an invalid value per test.
- Boundary value analysis tests at the edges of ordered partitions. 2-value: the boundary and its neighbour across the edge. 3-value: the boundary and both neighbours.
- 2-value BVA catches `<` versus `<=`; 3-value also catches a wrong operator such as `==`.
- Boundaries hide in lengths, time, money, capacity, data types and counters — ask "inclusive or exclusive?" for every limit.
- In an answer, the techniques appear as *classes of input* and *values at the edges*, each with a stated reason.

## Glossary

| Term | Meaning |
|---|---|
| Test case | One check: a chosen input and the result expected |
| Black-box technique | Designing tests from what a product should do, without reading its code |
| Equivalence partition (class) | A group of inputs the system should treat in the same way |
| Valid / invalid partition | A group that should be accepted / one that should be rejected |
| Representative | One value chosen to stand for its whole partition |
| Boundary value | A value at the edge of a partition |
| 2-value BVA | Testing each boundary and its nearest neighbour across the edge |
| 3-value BVA | Testing each boundary and the neighbour on both sides |
| Off-by-one error | A mistake of exactly one, typically from using < where <= was meant |
| Coverage | The share of identified items, such as partitions, exercised by tests |

## Check yourself

```quiz
[
  {"q": "A field accepts integers 1 to 50. Which set is the 2-value boundary analysis?",
   "options": ["1, 25, 50", "0, 1, 50, 51", "0, 1, 2, 49, 50, 51", "1, 50"],
   "answer": 1,
   "explain": "Each boundary plus its nearest neighbour in the adjacent partition: 0 and 1 at the low edge, 50 and 51 at the high edge."},
  {"q": "Why should a single test contain at most one invalid partition?",
   "options": ["Invalid tests are slow", "The first validation error can stop processing, so a second invalid value would never be checked", "Standards forbid it", "It makes the test name too long"],
   "answer": 1,
   "explain": "This is fault masking. Changing one input at a time shows that each check works on its own."},
  {"q": "A specification says: '0–17 minor, 17–64 adult'. What should a tester do first?",
   "options": ["Assume 17 is a minor and continue", "Assume 17 is an adult and continue", "Report that the partitions overlap at 17 and ask which is intended", "Skip testing 17"],
   "answer": 2,
   "explain": "Overlapping partitions are a defect in the specification. Finding it is a result, and guessing hides it."},
  {"q": "The code has 'if qty == 10' where 'qty >= 10' was intended. Valid range starts at 10. Which test exposes the bug?",
   "options": ["qty = 9", "qty = 10", "qty = 11", "None of these"],
   "answer": 2,
   "explain": "9 and 10 both behave correctly. Only a value immediately inside the range, supplied by 3-value BVA, shows the wrong operator."},
  {"q": "Which input does NOT have meaningful boundary values?",
   "options": ["Order quantity 1–99", "Username length 3–20", "Payment method: coin, card or phone", "Session timeout of 30 minutes"],
   "answer": 2,
   "explain": "Payment methods are an unordered set. Boundary analysis needs an ordering; here each value is its own partition."},
  {"q": "Three fields have 4, 2 and 3 valid partitions and 1, 2 and 1 invalid partitions. Minimum tests under the usual rule?",
   "options": ["24", "13", "8", "9"],
   "answer": 2,
   "explain": "Valid partitions share tests: max(4, 2, 3) = 4. Invalid partitions get one each: 1 + 2 + 1 = 4. Total 8."},
  {"q": "What does '100 % equivalence partition coverage' guarantee?",
   "options": ["No defects remain", "Every partition that was identified has at least one test", "Every input value has been tried", "All boundaries were tested"],
   "answer": 1,
   "explain": "Coverage is measured against the partitions you listed. A class you never thought of is not counted."},
  {"q": "Which is a hidden boundary worth raising for a 'maximum 280 characters' rule?",
   "options": ["The font used to render the text", "Whether an emoji counts as one character or several", "The colour of the text box", "The user's time zone"],
   "answer": 1,
   "explain": "Characters, code points and bytes differ, so the place where the limit bites depends on how length is counted."}
]
```

> **Source:** ISTQB Certified Tester Foundation Level syllabus v4.0, section 4.2.1 "Equivalence Partitioning" and 4.2.2 "Boundary Value Analysis" (https://www.istqb.org/certifications/certified-tester-foundation-level), explained in original wording with original examples. See also *Software Engineering at Google*, ch. 12 "Unit Testing" (https://abseil.io/resources/swe-book/html/ch12.html).
