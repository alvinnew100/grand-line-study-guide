# Exploratory testing, risk and non-functional categories

> **Before this lesson:** read [Equivalence partitioning and boundary value analysis](#/lesson/thinking/partitions-boundaries) and [Decision tables, state transitions and pairwise testing](#/lesson/thinking/tables-states-pairwise).

## In plain words

An experienced car mechanic handed an unfamiliar car does three things that a manual cannot teach. They poke at the places where cars of that age usually fail. They decide what to check first — brakes before the radio — because time is limited and some faults matter more. And they look beyond "does it move?" to "is it safe, is it comfortable, will it start on a cold morning?"

Those are the three subjects of this lesson. **Exploratory testing** and **error guessing** use experience to hunt for problems that no written specification mentions (a **specification** is the document saying what a product should do). **Risk-based prioritisation** decides the order of work by asking how likely each problem is and how bad it would be. And **non-functional** testing covers the qualities beyond "it gives the right answer": speed, security, ease of use, and so on.

In interviews these are what separate a list of test cases from a plan. At work they are how a tester with one day decides what to do with it.

The techniques so far derive tests from a specification. Three things remain. First, specifications are incomplete, so you need ways to find problems nobody wrote down: **exploratory testing** and **error guessing**. Second, you will always have more ideas than time, so you need a defensible way to rank them: **risk-based prioritisation**. Third, "does it do the right thing?" is only one kind of quality; a product can compute the correct answer and still be too slow, unsafe, unusable or inaccessible. Those are the **non-functional** categories, and a candidate who sweeps through them calmly sounds senior.

## Experience-based techniques

### Error guessing

Error guessing means using knowledge of how software and hardware usually fail to predict where this one will. It sounds informal, and it is, but it becomes systematic when you carry a checklist of classic failure sources. The list below is worth memorising, because it applies to nearly every prompt.

| Trigger | Ask yourself | Example |
|---|---|---|
| **Nothing** | What if the input is empty, zero, null, missing? | Search with an empty box; a machine with no stock |
| **One** | Does a single item behave differently from many? | A cart with one line; one coin tube |
| **Many / too many** | What happens at and beyond capacity? | A 5,000-item order; credit above the maximum |
| **Twice** | What if the action is repeated or duplicated? | Double-click on "Pay"; the same request retried |
| **Out of order** | What if steps happen in an unexpected sequence? | Select product, then insert coins; back button after payment |
| **At the same time** | What if two things happen concurrently? | Two users buy the last seat; a coin drops as refund is pressed |
| **Interrupted** | What if it stops halfway? | Power cut while dispensing; network loss mid-payment |
| **Too slow / too fast** | What about timeouts and rapid input? | A bank reply after 60 s; button mashing |
| **Wrong type or format** | What if the data is not what was expected? | Letters in a number field; a foreign coin |
| **Hostile** | What would someone trying to cheat or break it do? | A coin on a string; SQL in a text field |
| **Old state** | What if leftover data or an old version is involved? | Stale cache; upgrade with existing saved settings |
| **Time** | What about clocks, dates and durations? | Midnight, leap day, clock change, a device left on for 40 days |

In an interview you do not recite the table. You pick an area from your map and run a few triggers across it aloud: "Payment — what if it happens twice, what if it is interrupted, what if it is slow?"

### Exploratory testing

Exploratory testing is simultaneous learning, test design and execution: you use the product, notice something interesting, and let that observation steer the next test. It is not random clicking. The disciplined form uses a **charter** — a one-sentence mission — and a **time box**.

A charter has three parts: *explore* (a target) *with* (resources or techniques) *to discover* (the kind of information wanted).

- "Explore the coin return path with worn, foreign and bent coins to discover jams and wrong credits."
- "Explore checkout with the network throttled and interrupted to discover duplicate or lost orders."
- "Explore the search box with very long, empty and non-Latin queries to discover crashes and misleading results."

During the session the tester keeps brief notes: what was tried, what was found, what questions arose. Afterwards there is a short debrief. This makes exploration reportable and repeatable enough to manage.

**When it earns its place:**

- early, when the specification is thin or the product is new to you;
- on physical products, where feel, sound, force and timing matter and nobody specified them;
- after scripted tests pass, to look in the places scripts do not reach;
- when time is very short and writing detailed cases first would consume it.

**What it does not replace:** a regression suite. Exploration finds new problems; automated checks keep old ones from returning.

### Checklist-based testing

The third experience-based technique is the plain checklist: a list of conditions to verify, built from past defects and standards — an accessibility checklist, a release checklist, a "new API endpoint" checklist. Its value is consistency; its danger is going stale. In an interview, the non-functional sweep later in this lesson is your checklist.

> [!INTERVIEW]
> A sentence that reliably lands well: "After the designed tests I'd book a couple of time-boxed exploratory sessions with specific charters, because the specification cannot anticipate everything — especially on hardware." It shows you know both that scripted testing has limits and that exploration should be organised.

## Risk-based prioritisation

### Risk in one line

**Risk = likelihood of a failure × impact if it happens.**

A test is worth running early when it guards against something probable, something severe, or both. Prioritising by risk gives you the two things an interviewer listens for: an order, and a reason for the order.

### What raises each factor

| Likelihood goes up with… | Impact goes up with… |
|---|---|
| New or recently changed code | Harm to people (safety) |
| Complex logic, many combinations | Money lost or miscounted |
| Integration with external systems | Data loss or exposure of personal data |
| Parts with a history of defects | Legal or regulatory consequences |
| Unclear or changing requirements | Number of users affected |
| Time pressure, new team, new technology | No workaround; hard to reverse |
| Hardware that wears, jams or drifts | Damage to reputation; visibility |

### A simple scoring scheme

Score each on 1–5 and multiply. The numbers are rough judgments; their purpose is to force a comparison, not to be precise.

Take a self-service library kiosk:

| Item | Likelihood | Impact | Score | Note |
|---|---|---|---|---|
| Book checked out but not recorded | 3 | 5 | 15 | Inventory silently diverges |
| Card reader rejects valid cards | 4 | 4 | 16 | Blocks every user |
| Receipt printer out of paper not detected | 4 | 2 | 8 | Annoying; has a workaround |
| Screen text truncated in one language | 3 | 2 | 6 | Cosmetic |
| Kiosk overheats in direct sunlight | 2 | 4 | 8 | Site-dependent |
| Personal data shown to the next user | 2 | 5 | 10 | Privacy breach |

Sorted: card reader (16), unrecorded checkout (15), data shown to next user (10), then the 8s and the 6.

### Tie-breaks and corrections

Pure multiplication has known weaknesses. Mention them and you sound experienced.

- **Catastrophic-but-rare items.** A 1 × 5 scores the same as 5 × 1, yet a rare catastrophe and a frequent nuisance are not equivalent. A common rule: among equal scores, higher impact first — and any item with maximum impact gets tested regardless of its score.
- **Cost of the test.** If two tests guard equal risk and one takes five minutes while the other takes a day, run the cheap one first. More formally you can rank by risk reduced per hour.
- **Detectability.** A failure that would be noticed immediately in production (the screen is blank) is less dangerous than one that stays hidden (totals are off by a cent). Hidden failures deserve extra testing because nothing else will catch them.
- **Reversibility.** A bad colour can be patched tomorrow. A wrong firmware in ten thousand shipped devices cannot. Irreversible risks move up.

```python-run
cases = [
    # name, likelihood, impact, minutes
    ("checkout not recorded",   3, 5, 45),
    ("card reader rejects",     4, 4, 20),
    ("printer out of paper",    4, 2, 10),
    ("truncated translation",   3, 2, 15),
    ("overheats in sun",        2, 4, 240),
    ("data shown to next user", 2, 5, 30),
    ("refund after timeout",    2, 4, 25),
]
ordered = sorted(cases, key=lambda c: (-(c[1] * c[2]), -c[2], c[3], c[0]))
budget, used = 120, 0
for name, l, i, m in ordered:
    fits = used + m <= budget
    used += m if fits else 0
    print(f"{l*i:3d}  impact {i}  {m:4d} min  {'RUN ' if fits else 'skip'} {name}")
print("minutes used:", used, "of", budget)
```

Change the budget and watch what falls off the end. Being able to say "with half the time, these are the ones I drop, and here is the risk I am accepting by dropping them" is the heart of a good prioritisation answer.

### Risk drives depth, not only order

Risk does not only sort the list. It decides how thoroughly each item is treated:

| Risk level | Typical treatment |
|---|---|
| High | Full decision table, 3-value boundaries, invalid transitions, exploratory session, automated regression, review by a second person |
| Medium | Collapsed table, 2-value boundaries, valid-transition coverage |
| Low | One representative per partition, or a quick check during exploration |

## Functional and non-functional categories

**Functional** testing asks *what* the system does: given this input in this state, is the result correct? Everything in the previous two lessons is functional.

**Non-functional** testing asks *how well* it does it. These qualities are easy to forget because requirements often omit them, and they are the source of many real-world failures. Run this sweep near the end of every "how would you test…" answer.

| Category | Question | Physical example (vending machine) | Digital example (login page) |
|---|---|---|---|
| **Performance** | Fast enough, under expected and peak load? | Time from selection to product; a queue of users at lunchtime | Response time at 1,000 logins per second; behaviour when the database is slow |
| **Reliability** | Does it keep working over time and recover from faults? | 10,000 vend cycles; recovery after a power cut | Session store failover; no memory growth over a week |
| **Security** | Can it be abused, cheated or broken into? | Coin on a string, slugs, tilting, forced door, tampered card reader | Brute force, credential stuffing, injection, session fixation |
| **Usability** | Can real people use it without help? | Reachable buttons, readable in sunlight, clear messages when sold out | Clear errors, password visibility toggle, sensible tab order |
| **Accessibility** | Can people with disabilities use it? | Height for wheelchair users, tactile keys, audio feedback | Screen-reader labels, keyboard-only use, colour contrast |
| **Compatibility** | Does it work with what surrounds it? | Card schemes, coin series, mains voltage, telemetry backend versions | Browsers, devices, password managers, single sign-on providers |
| **Localisation** | Does it suit each language and region? | Currency, languages on screen, date formats on receipts | Translated messages, right-to-left layout, names with accents |
| **Safety** | Can it hurt anyone or anything? | Tipping, pinch points, electrical leakage, hot surfaces, food temperature | (Indirect) lockout of an emergency responder; unsafe defaults |
| **Maintainability / operability** | Can it be serviced, monitored and updated? | Restocking time, error codes for technicians, remote firmware update | Logs, metrics, alerts, feature flags, rollback |
| **Compliance** | Does it meet the rules that apply? | Payment card standards, electrical certification, food hygiene | Data-protection law, password policy standards, audit logging |

Three practical notes.

**Non-functional requirements need numbers.** "It should be fast" is untestable. "95 % of vends complete within 8 seconds of selection" is testable. If the prompt gives no number, propose one and say how you would agree it with the product owner.

**Different categories need different environments.** Function can be checked on a bench or in a unit test. Performance needs realistic load. Reliability needs time or accelerated cycles. Environmental and safety testing may need a specialised laboratory. Mentioning *where* a test can meaningfully run is a sign of practical experience.

**They trade off against each other.** Stronger security checks slow the login; more logging helps operability and may hurt privacy; a heavier machine is safer against tipping and harder to install. Saying one such tension aloud covers the trade-off step of your answer.

### A quick mental checklist

Many people remember the sweep as a sentence. One possibility: **"Fast, Reliable, Secure, Usable by Everyone, Everywhere, Safely, and Supportable."** That gives performance, reliability, security, usability, accessibility ("everyone"), compatibility and localisation ("everywhere"), safety, and maintainability. Invent your own; the point is to have one.

## Putting the lesson to work

**Prompt:** *"You have two days to test a new hotel-room safe (four-digit code, motorised bolt, battery powered) before a shipment decision. What do you do?"* Give a prioritised plan before opening.

<details><summary>Model answer</summary>

**Clarify and assume.** Guests set their own code on each stay; staff have an override key or master code; four AA batteries; the two-day limit means I cannot run long endurance tests. I'm deciding go or no-go for a shipment of the existing design.

**Risks, scored.**

| Item | L | I | Score | Treatment in two days |
|---|---|---|---|---|
| Safe opens without the correct code (default codes, master code leaked, bolt forced, a sharp knock or magnet) | 2 | 5 | 10 — maximum impact, so first | Half a day of adversarial exploratory testing with a charter |
| Guest locked out: batteries die with belongings inside | 4 | 4 | 16 | Low-battery warning threshold; behaviour at very low voltage; override procedure works |
| Code logic: set, lock, open, wrong-code lockout | 3 | 4 | 12 | State table, all transitions including invalid ones |
| Bolt jams when the door is not fully closed or is overfilled | 3 | 3 | 9 | Hands-on session with obstructed door |
| Keypad usability: no feedback, unclear instructions | 3 | 2 | 6 | A short test with three people who have not seen it |
| Endurance of the motor | 2 | 3 | 6 | Cannot be done properly; request supplier data, run a short rig cycle overnight |

**Order.** Unauthorised opening first despite its score, because the impact is the product's entire purpose. Then battery behaviour, then the code state machine, then jams, then usability. Endurance is acknowledged as a gap.

**Depth on the top item.** Error-guessing triggers: *nothing* (press lock with no code set), *default* (0000, 1234, a factory reset sequence found in the manual), *interrupted* (remove batteries mid-lock: does the bolt stay shut or spring open?), *hostile* (strike the top while turning the handle; a strong magnet near the solenoid), *old state* (does the previous guest's code survive checkout? is there a reset staff must perform?).

**Depth on the state machine.** States: open-unlocked, closed-unlocked, locked, locked-out after N wrong codes, low battery. I check every event in every state: entering a code while open, pressing lock twice, a fifth wrong code, the correct code during lockout (must be refused), battery removal in each state.

**Non-functional sweep.** Security and reliability are covered above. Accessibility: keypad height and tactile feedback. Usability: can a tired traveller set a code without reading a manual? Safety: pinch risk from the motorised bolt. Localisation: icons instead of text. Operability: how long does a staff override take, and is it logged?

**Trade-off and summary.** With two days I am choosing breadth on security and lockout over endurance evidence. My recommendation would be conditional: ship if no unauthorised-opening method is found and the low-battery behaviour is safe, with endurance covered by supplier certificates and a monitored first installation.

</details>

## Summary

- **Error guessing** applies a checklist of classic triggers: nothing, one, many, twice, out of order, concurrent, interrupted, slow or fast, wrong format, hostile, old state, time.
- **Exploratory testing** is learning and testing at once, kept honest by a charter and a time box. It complements designed and automated tests; it does not replace them.
- **Risk = likelihood × impact.** Rank by it, break ties by impact, then by cost; always test maximum-impact items; give extra weight to failures that are hidden or irreversible.
- Risk sets depth as well as order: full tables and invalid transitions for high risk, a representative value for low.
- Sweep the **non-functional** categories every time: performance, reliability, security, usability, accessibility, compatibility, localisation, safety, maintainability, compliance. Give each a number where possible.

## Glossary

| Term | Meaning |
|---|---|
| Specification | A document describing what a product should do |
| Error guessing | Using knowledge of typical failures to predict where defects lie |
| Exploratory testing | Designing and running tests while learning about the product |
| Charter | A one-sentence mission for an exploratory session |
| Time box | A fixed limit on how long an activity may take |
| Risk | Likelihood of a failure multiplied by its impact |
| Likelihood / impact | How probable a failure is / how bad it would be |
| Functional testing | Checking what the system does |
| Non-functional testing | Checking how well it does it: speed, security, usability and so on |
| Accessibility | Usability by people with disabilities |
| Localisation | Suitability for a particular language and region |
| Regression suite | A set of tests re-run to check that old behaviour still works |

## Check yourself

```quiz
[
  {"q": "Which is a well-formed exploratory testing charter?",
   "options": ["Test everything for two hours", "Click around the app and see what breaks", "Explore checkout with an unreliable network to discover duplicate or lost orders", "Run regression suite number 4"],
   "answer": 2,
   "explain": "A charter names a target, the resources or conditions used, and the information sought, and is run inside a time box."},
  {"q": "Two test items both score 10: one is likelihood 5 × impact 2, the other likelihood 2 × impact 5. Which usually goes first?",
   "options": ["The 5 × 2, because it happens more often", "The 2 × 5, because higher impact breaks the tie", "Whichever was written first", "Neither should be run"],
   "answer": 1,
   "explain": "A rare catastrophe is usually worse than a frequent nuisance, so impact is the common tie-break."},
  {"q": "Which error-guessing trigger does 'the user double-clicks the Pay button' belong to?",
   "options": ["Nothing", "Twice", "Old state", "Wrong format"],
   "answer": 1,
   "explain": "Repeated or duplicated actions are a classic source of double charges and duplicate records."},
  {"q": "Why does a hidden failure (totals off by one cent) deserve more testing than an obvious one (blank screen) of similar impact?",
   "options": ["It is easier to test", "Nothing else will catch it, so it can persist and accumulate before anyone notices", "Blank screens never happen", "Hidden failures are always security issues"],
   "answer": 1,
   "explain": "Low detectability means production monitoring and users will not act as a safety net; testing is the only chance to catch it."},
  {"q": "Which requirement is testable as written?",
   "options": ["The kiosk should be fast", "The kiosk should be user-friendly", "95% of checkouts complete within 5 seconds of scanning", "The kiosk should be reliable"],
   "answer": 2,
   "explain": "Non-functional requirements need a measurable threshold; the others have to be turned into numbers first."},
  {"q": "'Can a wheelchair user reach the buttons and hear confirmation?' belongs to which category?",
   "options": ["Performance", "Compatibility", "Accessibility", "Localisation"],
   "answer": 2,
   "explain": "Accessibility asks whether people with disabilities can use the product; reach and non-visual feedback are central."},
  {"q": "What is the relationship between exploratory testing and an automated regression suite?",
   "options": ["Exploration replaces regression", "Regression replaces exploration", "Exploration finds new problems; regression stops known ones returning", "They are the same thing"],
   "answer": 2,
   "explain": "They answer different questions and are used together."},
  {"q": "With the test budget halved, what should a strong answer include?",
   "options": ["A promise to work twice as fast", "The same plan, unchanged", "Which lower-risk items are dropped and what risk is being accepted by dropping them", "A request to cancel the launch"],
   "answer": 2,
   "explain": "Prioritisation is shown by naming what is cut and making the accepted risk explicit."}
]
```

> **Source:** ISTQB Certified Tester Foundation Level syllabus v4.0, section 4.4 "Experience-based Test Techniques" and section 5.2 "Risk Management" (https://www.istqb.org/certifications/certified-tester-foundation-level); quality characteristic names loosely follow ISO/IEC 25010. Google SRE Book, "Testing for Reliability" (https://sre.google/sre-book/testing-reliability/). Explanations, tables and examples are original.
