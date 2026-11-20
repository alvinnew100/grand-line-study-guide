# Slow or flaky test suites, and designing code review rules

> **Before this lesson:** read [Buggy code on main](#/lesson/thinking/buggy-code-on-main). It helps to know what a unit test and an end-to-end test are — see [Testing digital products](#/lesson/thinking/testing-digital-products).

## In plain words

A smoke alarm is only useful if two things are true: it goes off quickly when there is a fire, and it does not go off when there is none. An alarm that takes an hour to sound is useless. An alarm that shrieks every time you make toast is worse than useless, because within a week you will have taken the battery out — and then it will not sound for a real fire either.

A team's automated tests are its smoke alarm. A **test suite** is the whole collection of them. A **slow** suite is the alarm that takes an hour: people stop waiting for it. A **flaky** test is one that sometimes passes and sometimes fails although nothing has changed — the alarm that goes off for toast. People learn to ignore it, and then they ignore real failures too.

The second half of the lesson is about **code review** — colleagues reading each other's changes before they are accepted — and how to set rules for it that people follow willingly. Both are questions about keeping a safety check trustworthy and affordable, which is why they are asked together.

Two process prompts arrive together so often that they are worth learning as a pair: *"Our CI takes ninety minutes and fails randomly — what would you do?"* and *"Design the code review rules for a team."* Both are about the same underlying thing: a quality gate is only useful while people **trust** it and can **afford** it. A gate that is slow gets worked around; a gate that cries wolf gets ignored; a review rule that feels like bureaucracy gets rubber-stamped.

## Part 1 — The slow, flaky suite

### Why it matters

A slow suite lengthens every feedback loop. Developers batch their work into larger changes to pay the waiting cost less often, and larger changes are harder to review and riskier to merge. A **flaky** test — one that passes and fails on the same code — does something worse: it teaches people that red means "press retry". Once that habit forms, real failures are retried into green too, and the suite stops protecting anything. *Software Engineering at Google* describes this erosion of trust as the central cost of flakiness.

A little arithmetic shows how quickly it bites. If each test has a 0.1 % chance of failing for no reason, a run of 2,000 tests passes cleanly only $0.999^{2000} \approx 13.5\,\%$ of the time.

```python-run
for per_test in (0.0001, 0.0005, 0.001, 0.005):
    for n in (500, 2000, 10000):
        print(f"flake rate {per_test:.2%} x {n:5d} tests -> clean run {((1 - per_test) ** n):6.1%}")
    print()
```

At that point nearly every pipeline is "red for no reason", and the retry button becomes the real merge gate.

### Clarify

- Slow **and** flaky, or mainly one?
- Where does the time go — one giant end-to-end stage, or thousands of small tests run serially?
- Does the suite gate merges, deploys or both?
- How large is the team, and is there a budget for CI machines?

Then state the principle: **measure before changing anything.** Both problems are concentrated — a small fraction of tests accounts for most of the time and most of the flakes — so data tells you where a week of work removes the most pain.

### Structure

| Phase | Slow | Flaky |
|---|---|---|
| **Measure** | Duration per stage and per test; queue time versus run time | Failure rate per test on unchanged code; retry counts |
| **Stop the bleeding** | Parallelise; cache | Quarantine the worst offenders |
| **Fix causes** | Push tests down the pyramid; select by impact | Fix the root causes by category |
| **Prevent regression** | Time budgets; trend dashboards | Detect new flakes on arrival; ownership |

### Making it faster

1. **Find the time.** Often a third of the wall-clock is waiting for a machine, not running tests. That is solved with capacity, not test work.
2. **Parallelise and shard.** Split the suite across machines. Tests must then be independent — which exposes hidden order dependencies, a useful side effect.
3. **Cache.** Dependencies, build outputs and container layers. Rebuilding the world on every commit is the commonest avoidable cost.
4. **Run only what the change can affect.** With a dependency graph of the code, a change to the billing module need not run the search tests. Run everything periodically on main as a backstop.
5. **Rebalance the pyramid.** The slow tests are almost always end-to-end tests driving a browser or a full environment. Ask of each: what does it check that a lower-level test could not? Keep a few journeys end to end, and move the many variations down to unit and service tests — Fowler's test-pyramid argument.
6. **Tier the pipeline.** Fast, reliable tests gate the merge (a ten-minute budget is a common target); slower suites run after merge and before or during deployment.
7. **Fail fast.** Order stages so the cheapest checks — lint, compile, unit — run first.

Trade-off to state: test selection and tiering mean a failure can be discovered after merge rather than before. That is acceptable if post-merge failures are detected quickly and reverted quickly, which the previous lessons arranged.

### Making it trustworthy

**Detect flakes with data.** A test that fails and then passes on retry with no code change is flaky by definition. Record every such event; also re-run suites on unchanged main overnight. Rank tests by flake rate.

**Quarantine, with a deadline.** Move the worst offenders out of the blocking path so they stop poisoning everyone's merges. They still run and report, but do not gate. Each quarantined test gets an owner and an expiry date: fix it or delete it. Quarantine without an owner is where tests go to die — and each one in quarantine is a hole in coverage, so say what covers that risk meanwhile.

**Fix by cause.** Flakiness has a short list of causes, each with a standard repair:

| Cause | Symptom | Repair |
|---|---|---|
| Timing and async waits | `sleep(2)` then assert; fails on a slow machine | Wait for a condition, with a timeout; inject a fake clock |
| Shared state | Passes alone, fails in a suite or in parallel | Fresh data per test; isolated databases, files and ports |
| Order dependence | Fails only when run after a certain test | Remove hidden set-up; randomise order to expose it |
| External services | Fails when a third-party sandbox or the network hiccups | Hermetic tests: fakes or recorded responses; contract tests separately |
| Concurrency in the product | A real race, rare | This is a **product bug** — fix the code, keep the test |
| Non-determinism | Random seeds, dates, time zones, hash ordering | Fix seeds; inject time; sort before comparing |
| Resource limits | Fails on busy CI machines | Right-size machines; remove leaks; avoid tight real-time assertions |

The fifth row deserves emphasis. Some "flaky tests" are accurate reports of an intermittent defect. Deleting them deletes the only evidence. Triage before repair.

**Retries: a painkiller, not a cure.** Automatic retry of a failed test keeps people moving, and it is reasonable as a temporary measure *if every retry is recorded and counted*. Silent retries hide both test flakiness and real intermittent bugs.

**Hermetic by default.** Tests that bring their own dependencies — an in-memory or containerised database, fake versions of other services — are deterministic and isolated. The Google book notes the cost of full hermeticity and suggests record-and-replay as a cheaper middle ground, with the caveat that recordings can become brittle.

**Keep it fixed.** Give every test an owning team. Set a budget — for example "pre-merge suite under ten minutes; flake rate under 0.5 % of runs" — put it on a dashboard, and treat a breach like any other regression.

<details><summary>Model answer — "CI takes 90 minutes and fails randomly"</summary>

"I'd ask where the ninety minutes goes and how often a run fails on code that later passes unchanged. I'll assume it gates merges for forty engineers, the time is mostly a serial end-to-end stage, and about one run in three needs a retry.

My principle is to measure first, because both problems are usually concentrated in a few tests.

**Week one — measure and stop the bleeding.** Instrument per-test duration and per-test outcome on retries. Rank the top twenty by time and the top twenty by flake rate. Quarantine the worst flakes out of the blocking path, each with an owner and a two-week deadline. Enable recorded automatic retry for the rest as a temporary measure. Shard the suite across machines and turn on dependency and build caching. That alone typically takes ninety minutes to well under thirty.

**Weeks two to six — fix causes.** For flakes, work through the list by cause: replace sleeps with condition waits, give each test its own data, replace calls to external sandboxes with fakes, and investigate any that turn out to be real races in the product. For speed, review the end-to-end tests: keep the handful of critical journeys and move the variations to unit and service level. Split the pipeline into a pre-merge tier with a ten-minute budget and a post-merge tier with everything else.

**Ongoing — keep it healthy.** Automatic flake detection that files a ticket to the owning team; a dashboard of pipeline duration and flake rate; a rule that new tests must pass fifty consecutive runs before becoming blocking.

**Trade-offs.** Quarantining reduces coverage for a while, so I'd check each quarantined test's risk and cover the critical ones manually. Moving tests after merge means some failures are found later, which is acceptable only with fast detection and a revert-first rule.

**Success looks like:** pre-merge under ten minutes, fewer than one run in fifty failing spuriously, and nobody reaching for retry by reflex."

</details>

> [!INTERVIEW]
> The follow-up is usually: *"Why not delete the flaky tests?"* Answer in three parts: some are reporting real intermittent bugs; each deletion is a coverage decision that should be made deliberately; and the right order is quarantine → diagnose → fix, rewrite at a lower level, or delete with a recorded reason.

## Part 2 — Designing code review rules

### What review is for

Start by saying what you want from review, because the rules follow from the goals. Google's engineering-practices guide lists what a reviewer should look at: design, functionality, complexity, tests, naming, comments, style, consistency, documentation, and the wider context of the change. Behind that list sit four purposes:

1. **Correctness and design** — a second mind on the change.
2. **Comprehension** — at least one other person understands the code; the bus factor rises.
3. **Consistency** — the codebase stays coherent over time.
4. **Knowledge sharing** — review is how conventions and context spread.

Review is *not* a reliable way to find every bug (tests are better at that), and it is not the place to argue about formatting (automation is better at that).

### Clarify

Team size and seniority mix? Regulated domain (finance, health) needing audit trails? Monorepo or many repositories? Current pain: slow reviews, shallow reviews, or conflict?

### A rule set, layer by layer

**Before a human looks.**

- Formatting, linting, type checks, static analysis and tests run automatically; a red change is not reviewable. People should not spend attention on what a machine can check.
- The author writes a description: what, why, how it was tested, and anything risky. A reviewer cannot judge a change whose purpose is not stated.
- **Small changes.** Aim for something reviewable in under half an hour — a few hundred lines at most. Large changes get skimmed and approved. Split refactoring from behaviour change so that each is easy to verify.

**Who reviews.**

- At least one approval from someone other than the author.
- **Code owners** for each area: a change in the payments module needs an approval from the payments team. Sensitive paths — authentication, billing, infrastructure, data migrations — require a second, specialist reviewer.
- Spread the load: rotate or auto-assign, so that two senior people do not become the queue for everything.

**What the reviewer checks** — a short checklist in priority order:

1. Does it do what it claims, including edge cases and failure paths?
2. Is the design reasonable for this codebase? Is anything more complicated than it needs to be?
3. Are there tests that would fail if the behaviour broke?
4. Security and data: input validation, authorisation, secrets, personal data, injection.
5. Operability: logging, metrics, a flag, a rollback path for risky changes.
6. Readability: names, comments that explain *why*.
7. Style last — and only what the linter cannot enforce.

**How the conversation runs.**

- A **turnaround expectation**: first response within one working day, sooner for small changes. Slow review is the main reason people build giant branches.
- **Label the severity of comments**: blocking, suggestion, or nit. The Google guide recommends prefixing minor preferences with "Nit:" so that the author knows they need not block.
- **The standard for approval** is that the change improves the overall health of the code, not that it is perfect. Insisting on perfection stalls delivery; approving anything lets quality rot.
- Comment on the code, not the person; ask questions rather than issue verdicts; say what is good as well.
- Disagreement that cannot be settled in two rounds goes to a call, and then to a designated tie-breaker such as the tech lead — not to a comment thread forty messages long.

**After approval.**

- New commits after approval dismiss it, or at least are re-checked.
- The author merges, through the merge queue.
- Emergency changes may be merged with expedited review but never with none; they are logged and reviewed afterwards.

**Measure lightly.** Time to first review, time to merge, change size, and how often defects escape review. Do not count comments per reviewer or approvals per person; those numbers are easy to game and distort behaviour.

<details><summary>Model answer — "Design code review rules for a team of twenty"</summary>

"First I'd ask what problem we are solving — is review slow, shallow, or contentious? — and whether there are compliance requirements. I'll assume a twenty-person product team, mixed seniority, no heavy regulation, and that reviews currently take two or three days.

My goals for review, in order: catch design and correctness problems, make sure a second person understands every change, keep the codebase consistent, and share knowledge. I'd leave formatting and simple bug-finding to tools.

**Rules.**

1. Automation first: format, lint, type-check and fast tests must pass before a reviewer is asked.
2. Every change has a description — what, why, how tested, risk.
3. Changes are small: a guideline of a few hundred lines; larger ones are split or come with a design note agreed beforehand.
4. One approval from a non-author; code owners approve changes in their area; a second specialist approval for authentication, payments, infrastructure and migrations.
5. A reviewer checklist ordered by importance: behaviour, design, tests, security, operability, readability, style.
6. First response within one working day; reviewers are auto-assigned in rotation to spread load.
7. Comments are marked blocking, suggestion or nit. Approve when the change is a net improvement, even if not perfect.
8. Stalemates go to a short call, then the tech lead decides.
9. Approval is re-checked after further commits; merging goes through the queue.
10. Emergencies get expedited review, never none, and are looked at again the next day.

**Trade-offs.** Every rule costs time. Requiring two approvals everywhere would double the wait for little gain, so I reserve it for high-risk paths. A strict size limit irritates people during large refactors, so it is a guideline with an escape hatch — a pre-agreed plan and a sequence of mechanical changes.

**How I'd know it works:** time to first review under a day, median change size falling, fewer review-escaped defects in incident reviews, and — asked in a retrospective — people saying review is useful rather than a toll booth."

</details>

### Follow-ups

**"Reviews are rubber-stamped."** Usually the changes are too big or the reviewers lack context. Shrink changes, route by code ownership, and ask authors to guide reviewers through the risky part. Occasionally audit a sample of merged changes.

**"A senior engineer blocks everything on style."** Move style into the formatter and linter so that the argument has nowhere to live; require severity labels; anything not in the written style guide is a nit by definition.

**"Should juniors review seniors' code?"** Yes. They learn the codebase, they ask the questions that reveal unclear code, and review authority should rest on reasoning, not rank.

**"What about AI-generated code?"** The same rules: the author is responsible for every line they submit, must understand it and must test it. Generated code tends to be plausible and verbose, so small changes and real tests matter more, not less.

**"Pair programming instead of review?"** Pairing gives continuous review and can replace the asynchronous step for many changes, as trunk-based practitioners point out; keep a lightweight record and still require owner sign-off for sensitive paths.

## Summary

- Gates work only while they are trusted and affordable.
- For a slow suite: measure, parallelise, cache, select tests by impact, move tests down the pyramid, tier the pipeline.
- For flakiness: detect with data, quarantine with owners and deadlines, fix by cause, record retries, prefer hermetic tests — and remember that some flakes are real product races.
- For review rules: decide the goals; automate the mechanical; keep changes small; route by ownership; order the checklist by importance; set a turnaround time; label comment severity; approve net improvements; give stalemates an exit.

## Glossary

| Term | Meaning |
|---|---|
| Test suite | The complete set of automated tests for a project |
| Flaky test | A test that passes and fails on the same code |
| Pipeline | The automated sequence of build, test and release steps |
| Quarantine | Moving an unreliable test out of the blocking path until it is fixed |
| Hermetic test | A test that depends on nothing outside itself |
| Sharding | Splitting tests across several machines to run in parallel |
| Test selection | Running only the tests a change could affect |
| Retry | Automatically re-running a failed test |
| Code review | Colleagues examining a change before it is merged |
| Code owner | A person or team whose approval is required for part of the code |
| Nit | A minor, optional review comment |
| Linter / formatter | Tools that check or fix code style automatically |
| Turnaround time | How long a change waits for a first review |

## Check yourself

```quiz
[
  {"q": "Each of 3,000 tests has a 0.1% chance of failing spuriously. Roughly how often does the whole run pass cleanly?",
   "options": ["About 99.9%", "About 50%", "About 5%", "Never"],
   "answer": 2,
   "explain": "0.999^3000 ≈ 0.05. Tiny per-test flake rates compound into a suite that is almost always red."},
  {"q": "What is the main harm of flaky tests?",
   "options": ["They use more disk space", "People learn to retry until green, so real failures get ignored too", "They run faster than stable tests", "They cannot be measured"],
   "answer": 1,
   "explain": "Loss of trust in red is the cost; once retry is a reflex the suite no longer protects."},
  {"q": "A test passes alone and fails when the suite runs in parallel. Most likely cause?",
   "options": ["A typo in the test name", "Shared state between tests", "The CPU is too fast", "Too many assertions"],
   "answer": 1,
   "explain": "Shared databases, files, ports or globals make tests interfere; give each test isolated data."},
  {"q": "What must accompany quarantining a flaky test?",
   "options": ["Nothing", "An owner, a deadline, and awareness of the coverage gap it leaves", "Deleting its history", "Doubling its timeout"],
   "answer": 1,
   "explain": "Without ownership and an expiry, quarantine becomes permanent and the risk it covered is forgotten."},
  {"q": "Which change most directly shortens a pipeline dominated by browser-driven end-to-end tests?",
   "options": ["Adding more end-to-end tests", "Keeping a few journeys end to end and moving variations to unit and service tests", "Running tests serially", "Removing the linter"],
   "answer": 1,
   "explain": "Rebalancing toward the base of the pyramid replaces slow, brittle tests with fast, precise ones."},
  {"q": "Which task should NOT consume a human reviewer's attention?",
   "options": ["Whether the design fits the codebase", "Whether tests would catch a regression", "Whether the code is indented correctly", "Whether authorisation is checked"],
   "answer": 2,
   "explain": "Formatting is mechanical and belongs to a formatter; reviewers should spend effort on what tools cannot judge."},
  {"q": "What is a sensible standard for approving a change?",
   "options": ["It is perfect", "It improves the overall health of the code, even if not perfect", "The author is senior", "It has more than 500 lines"],
   "answer": 1,
   "explain": "Demanding perfection stalls delivery; the bar is net improvement with blocking issues resolved."},
  {"q": "Reviews take three days on average. Which rule addresses this most directly?",
   "options": ["Require three approvals", "A first-response expectation of one working day plus smaller changes and rotating assignment", "Ban comments", "Review only on Fridays"],
   "answer": 1,
   "explain": "Turnaround targets, smaller changes and spreading reviewer load attack the delay; more approvals would worsen it."}
]
```

> **Source:** *Software Engineering at Google*, ch. 11 "Testing Overview", ch. 23 "Continuous Integration" and ch. 9 "Code Review" (https://abseil.io/resources/swe-book/html/ch11.html, https://abseil.io/resources/swe-book/html/ch23.html, https://abseil.io/resources/swe-book/html/ch09.html); Google Engineering Practices, "What to look for in a code review" (https://google.github.io/eng-practices/review/reviewer/looking-for.html); Martin Fowler, "Test Pyramid" (https://martinfowler.com/bliki/TestPyramid.html) and "Eradicating Non-Determinism in Tests" (https://martinfowler.com/articles/nonDeterminism.html); Trunk Based Development (https://trunkbaseddevelopment.com/). Wording and examples are original.
