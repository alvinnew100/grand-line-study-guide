# Testing digital products: login, search, payments API, chat and a recommendation model

> **Before this lesson:** read [A repeatable template, and the vending machine in full](#/lesson/thinking/template-vending-machine) and [Testing physical products](#/lesson/thinking/testing-physical-products).

## In plain words

Checking a bridge and checking a telephone exchange are both inspections, but they worry about different things. A bridge inspector thinks about rust, weight and weather. A telephone engineer thinks about thousands of calls at once, two people being connected to the wrong line, and messages arriving twice.

Software products are like the telephone exchange. The same testing template applies, but three new concerns replace weather and wear: **scale** (very many users at the same time), **concurrency** (several things happening at once and interfering) and **data integrity** (what is stored staying correct). Software also offers something physical products do not: most checks can be run automatically, thousands of times a day, by small programs called automated tests.

This lesson applies the template to five digital products, from a login page to a recommendation system. Each example is one you are likely to be asked about, and each brings out a technique worth knowing.

Software prompts use the same template as physical ones, with a different set of special concerns. Where a machine has environment, wear and physical safety, software has **scale** (many users at once), **concurrency** (things happening simultaneously) and **data integrity** (what is stored stays correct). Software also has something hardware lacks: a **test pyramid** — the option of checking most behaviour cheaply at a low level and reserving slow end-to-end tests for a few journeys.

This lesson works five prompts: a login page, a search box, a payments API, a chat application and a recommendation model. Attempt each for eight to ten minutes before opening its answer.

## Where each test runs: the pyramid

For a digital product, part of a good answer is *where* a check lives.

| Level | Checks | Speed | Share of tests |
|---|---|---|---|
| Unit | One function or class in isolation: validation rules, calculations | Milliseconds | Most |
| Integration / service | A component with its real neighbours: database, queue, another service or a faithful fake | Seconds | Fewer |
| End-to-end | A whole user journey through the deployed system | Minutes | A handful |
| Production checks | Synthetic probes, canary analysis, monitoring | Continuous | Always on |

The reasoning: low-level tests are fast and tell you exactly what broke; high-level tests are slow and flaky but are the only ones that see the pieces working together. So push each check down to the lowest level that can meaningfully perform it, and keep a thin layer of journeys on top. Saying "the password rules are unit tests, lockout is a service test against the real store, and I'd keep two or three end-to-end journeys" earns the *levels* part of the template in one sentence.

## 1. A login page

**Prompt:** *"How would you test a login page?"*

It looks tiny — two fields and a button — which is the trap. Almost everything interesting is invisible: sessions, lockout, error messages that leak information, and attackers.

<details><summary>Model answer</summary>

**Clarify.** Username or email? Password only, or also single sign-on and multi-factor authentication? Web, mobile app or both? Is there "remember me", "forgot password", account lockout? What is the user base — a bank, a game, an internal tool?

**Assume.** Email and password, optional time-based one-time code as second factor, "remember me", lockout after five failures, forgot-password by email; consumer web application with a few million users.

**Decompose.** (1) Input and form behaviour, (2) authentication decision, (3) lockout and throttling, (4) session after login, (5) recovery — forgot password, (6) security, (7) non-functional.

**Model.** A decision table for the authentication outcome:

| Rule | Account exists | Password correct | Account locked | Second factor required | Code correct | Outcome |
|---|---|---|---|---|---|---|
| 1 | N | – | – | – | – | Generic failure |
| 2 | Y | N | N | – | – | Generic failure; count +1 |
| 3 | Y | – | Y | – | – | Refused (even with the right password) |
| 4 | Y | Y | N | N | – | Logged in |
| 5 | Y | Y | N | Y | N | Stay at code step; count attempts |
| 6 | Y | Y | N | Y | Y | Logged in |

And the lockout state machine from module 2 for the failure counter.

**Tests by area.**

- *Form.* Partitions of email: valid; missing `@`; leading and trailing spaces (trimmed?); upper versus lower case (the same account?); very long; non-Latin characters. Password: empty, minimum and maximum length, spaces, emoji, pasted text, password-manager autofill. Enter key submits; double submit sends one request.
- *Decision.* Each rule in the table. The message for rule 1 and rule 2 must be identical, and so should the response time, or the page tells an attacker which emails are registered.
- *Lockout.* Boundaries: the fourth and fifth failure; success on the fifth attempt; counter reset after success; counter expiry over time; the correct password while locked. Abuse: locking out someone else on purpose by failing their login — a denial-of-service on a victim; mitigations such as throttling by source and progressive delays need tests.
- *Session.* A new session identifier is issued at login (no fixation); cookies have the secure and http-only attributes; logout invalidates the session on the server, not only in the browser; "back" after logout shows nothing private; session expiry at exactly the timeout; "remember me" survives a browser restart and can be revoked; password change ends other sessions.
- *Recovery.* Reset link is single-use, expires, and is long and random; requesting a reset does not reveal whether the email exists; the old password stops working.
- *Security.* Transport encryption everywhere; injection strings in both fields; script tags reflected in error messages; passwords never logged; rate limits against credential stuffing; common-password rejection at sign-up.

**Non-functional.** Performance: login is the front door, so peak load on a Monday morning or after an outage, when everyone returns at once. Reliability: behaviour when the user database or the session store is down — a clear error, not a blank page, and not "logged in as nobody". Accessibility: labels, keyboard-only use, error announcements for screen readers. Compatibility: browsers, password managers, mobile keyboards. Localisation: translated messages, right-to-left layouts.

**Prioritised plan.**

| Rank | Risk | L | I | Level |
|---|---|---|---|---|
| 1 | Authentication bypass or session takeover | 2 | 5 | Service tests + security review + penetration test |
| 2 | Valid users cannot log in (regression, outage, bad deploy) | 3 | 5 | End-to-end smoke test in every deploy; synthetic probe in production |
| 3 | Brute force and credential stuffing succeed | 4 | 4 | Service tests of lockout and rate limits |
| 4 | Account enumeration through messages or timing | 4 | 3 | Service tests comparing responses |
| 5 | Reset flow abused | 2 | 5 | Service tests of token expiry and reuse |
| 6 | Load at peak | 3 | 4 | Load test |
| 7 | Validation and cosmetic errors | 4 | 1 | Unit tests |

**Summary.** The visible form is the least risky part. I'd spend effort on the decision table, lockout state machine and session handling, keep a production probe that logs in every minute, and have security specialists review it.

</details>

## 2. A search box

**Prompt:** *"How would you test the search box on an e-commerce site?"*

The new difficulty: there is no single correct output. "Good results" is a matter of degree, so the answer has to include how quality is *measured*.

<details><summary>Model answer</summary>

**Clarify.** What is being searched — products only? How large is the catalogue? Are there suggestions as you type, spelling correction, filters and sorting? Personalised results? Which languages?

**Assume.** A product catalogue of two million items, autocomplete, spelling tolerance, filters, sort options, one language to start.

**Decompose.** (1) Query input, (2) correctness of matching, (3) relevance and ranking, (4) autocomplete, (5) filters, sorting and pagination, (6) freshness of the index, (7) non-functional.

**Tests by area.**

- *Input partitions.* Empty; one character; a typical two-word query; a very long query; only spaces; punctuation and symbols; numbers and model codes (`XJ-200`); quotes; mixed case; accents and non-Latin scripts; emoji; an injection string; a script tag (rendered back safely in "results for …").
- *Matching.* Exact product name; partial word; plural versus singular; misspelling; synonyms (sofa and couch); a query with no results — helpful empty page with suggestions, not a blank or an error; a query matching everything.
- *Relevance.* This cannot be asserted item by item across millions of queries, so I'd use three complementary methods:
  1. A **golden set**: a few hundred important queries with human-judged ideal results, scored automatically with a ranking metric on every change; the build fails if the score drops beyond a threshold.
  2. **Invariant (metamorphic) checks** that need no judge: adding a filter never increases the result count; the same query in different letter case gives the same results; sorting by price really is monotonic; page 2 does not repeat page 1; a query for an exact product code returns that product first.
  3. **Online measurement** after release: click-through on the first results, searches with no click, searches followed by a reformulated search, and conversion — compared in an A/B test.
- *Autocomplete.* Suggestions appear within the latency budget; typing quickly does not show stale suggestions for an earlier prefix (out-of-order responses); offensive terms are not suggested; keyboard navigation works.
- *Filters and pagination.* Combinations of filters (pairwise across brand, price band, rating, availability); boundaries of a price range; the last page; a page number beyond the end; deep pagination performance.
- *Freshness.* A new product becomes searchable within the agreed delay; a price change shows consistently in results and on the product page; a deleted or out-of-stock product disappears or is marked.

**Non-functional.** Performance: latency at the 95th and 99th percentile under peak load, since search is used on almost every visit; very expensive queries (single common letter) must not exhaust the service. Reliability: if the search cluster is degraded, show partial or cached results rather than failing the page. Security: injection, and scraping by bots. Accessibility: results announced to screen readers, focus management. Localisation: word segmentation and stemming differ by language.

**Prioritised plan.**

| Rank | Risk | L | I | How |
|---|---|---|---|---|
| 1 | Relevant products not found or ranked low (lost sales, silently) | 4 | 4 | Golden set + online metrics |
| 2 | Search slow or down at peak | 3 | 5 | Load tests; degradation tests |
| 3 | Stale index: wrong price or unavailable items | 3 | 4 | Freshness tests on the indexing pipeline |
| 4 | Filters or sorting wrong | 3 | 3 | Invariant checks, pairwise combinations |
| 5 | Unsafe rendering of the query | 2 | 4 | Security tests |
| 6 | Autocomplete glitches | 4 | 2 | UI tests with delayed responses |

**Summary.** Because quality is a matter of degree, I combined exact checks for the things that are exact, invariants that need no oracle, a judged golden set for ranking, and live metrics for what only real users can tell us.

</details>

> [!NOTE]
> The phrase to remember is the **oracle problem**: how do you know the expected result? When no exact oracle exists — search ranking, recommendations, machine translation — fall back on (a) a judged sample, (b) properties that must hold whatever the answer is, and (c) measured outcomes in production.

## 3. A payments API

**Prompt:** *"How would you test an API that charges a customer's card?"*

There is no screen. The users are other programs, which retry, time out, and send things twice.

<details><summary>Model answer</summary>

**Clarify.** What operations — charge, refund, capture after authorisation? Who calls it — our own checkout service or third-party merchants? Which processor sits behind it? What volume? What are the consistency requirements with the order system?

**Assume.** `POST /charges` with amount, currency, a tokenised card and an idempotency key; `POST /refunds`; called by internal services and external merchants; forwards to an external card processor.

**Decompose.** (1) Contract — request validation and responses, (2) business rules, (3) idempotency and retries, (4) dependency failures, (5) concurrency, (6) security and compliance, (7) reconciliation and observability, (8) performance.

**Tests by area.**

- *Contract.* Each field: missing, null, wrong type, unknown extra fields. Amount partitions: negative, zero, the smallest unit, typical, the maximum, above the maximum, a fractional minor unit, a currency with no decimals versus one with three. Unsupported currency. Each documented error returns the documented status code and a machine-readable error body. Backward compatibility: an old client's request still works after a new release.
- *Business rules.* Refund more than was charged; refund twice; partial refunds summing to exactly the charge and to one unit more; refund of a charge that failed; charge with an expired token.
- *Idempotency.* The same request with the same key sent twice returns the same result and charges once. Sent concurrently, twice at the same instant, still charges once. The same key with a *different* body is rejected. A retry after the first attempt timed out at the client but succeeded at the server returns the original success.
- *Dependency failures.* The processor is slow, returns an error, returns garbage, or — the hard one — **accepts the request and the reply is lost**. The API must not report failure for a charge that succeeded, so it needs a status lookup or a reconciliation path, and I test it by cutting the connection after the request is sent. Retry policy: only retryable errors are retried, with backoff and a limit; a declined card is never retried.
- *Concurrency.* Two refunds racing for the same charge; a refund racing a capture; many charges for one customer.
- *Security.* Authentication and authorisation per merchant (merchant A cannot refund merchant B's charge); no card numbers in logs; rate limits per key; input injection; transport encryption; compliance with card-industry rules.
- *Reconciliation.* Every charge in our ledger matches the processor's daily settlement report — a test that runs in production forever.
- *Performance.* Latency percentiles under expected and peak load; behaviour at and beyond the rate limit (a clean "too many requests" rather than collapse).

**Prioritised plan.**

| Rank | Risk | L | I | Level |
|---|---|---|---|---|
| 1 | Double charge under retries or concurrency | 3 | 5 | Service tests with a fake processor; concurrency tests |
| 2 | Charge succeeded at the processor but recorded as failed (or vice versa) | 3 | 5 | Fault-injection tests; reconciliation job |
| 3 | Cross-merchant access | 2 | 5 | Authorisation tests for every endpoint |
| 4 | Card data leaked in logs | 2 | 5 | Automated log scanning; review |
| 5 | Refund arithmetic wrong | 3 | 4 | Unit and service tests at boundaries |
| 6 | Breaking change for existing clients | 3 | 4 | Contract tests run against recorded client requests |
| 7 | Overload | 3 | 3 | Load and rate-limit tests |

**Levels.** Validation and arithmetic as unit tests. Idempotency, retries and failure handling as service tests against a programmable fake processor that can delay, fail and drop replies. A small end-to-end suite against the processor's sandbox. Canary release with error-rate and decline-rate comparison, because a subtle bug here shows up as a change in decline rate.

**Summary.** For an API that moves money the dominant risks are duplication and disagreement between systems, so the plan centres on idempotency, lost-reply handling and continuous reconciliation.

</details>

## 4. A chat application

**Prompt:** *"How would you test a messaging app like the ones on your phone?"*

The special concerns are real-time delivery, ordering, offline behaviour and multiple devices.

<details><summary>Model answer</summary>

**Clarify.** One-to-one only, or groups? Text only, or media, voice, read receipts, typing indicators? Which platforms? End-to-end encrypted? Roughly what scale?

**Assume.** One-to-one and group text with images, delivery and read receipts, push notifications, phone and web clients, multi-device, tens of millions of users.

**Decompose.** (1) Sending and receiving, (2) ordering and delivery guarantees, (3) offline and reconnection, (4) groups, (5) multi-device sync, (6) notifications, (7) media, (8) privacy and security, (9) non-functional.

**Model.** The life of one message is a state machine: composing → sending → sent to server → delivered to recipient device → read; with a failure branch: sending → failed → retry.

**Tests by area.**

- *Send and receive.* Partitions of content: empty (blocked), one character, the maximum length and one more, emoji, right-to-left text, links, text that resembles markup or script.
- *Guarantees.* Each message is delivered **exactly once** from the user's point of view and **in order** within a conversation. Tests: sender loses connection right after sending — the client retries; the server must de-duplicate so the recipient does not see it twice. Two people send at the same instant — both devices end up showing the same order. Messages sent rapidly arrive in order.
- *Offline.* Compose while offline: queued, visibly pending, sent on reconnection in the original order. Recipient offline for a week: receives everything on return. Flapping network: no loss and no duplicates. Airplane mode toggled mid-send. App killed mid-send.
- *Groups.* A member added mid-conversation sees only later messages (or history, per the design); a removed member receives nothing afterwards; boundaries at group-size limit; a message to a 1,000-member group fans out without delaying others.
- *Multi-device.* Read on the phone clears the unread badge on the web client; a message sent from the web appears on the phone's history; a newly linked device gets the agreed amount of history.
- *Notifications.* One per message, not zero and not three; none for a muted chat; none when the conversation is open on screen; content hidden on the lock screen if set; tapping it opens the right chat.
- *Media.* Size limits, formats, a corrupt file, upload interrupted and resumed, a slow network.
- *Privacy and security.* Blocked users cannot deliver messages; deleted messages disappear from all devices; encryption keys change when a device is added; a user cannot read a group they do not belong to by guessing identifiers.

**Non-functional.** Performance: send-to-delivery latency percentiles; app start time; battery and data use, since a persistent connection can drain both. Scale: a celebrity-sized group; a regional event where everyone messages at midnight. Reliability: a server node dies with open connections — clients reconnect without losing messages. Compatibility: operating-system versions, small screens, old devices. Accessibility: screen readers, font scaling. Localisation: scripts, time formats.

**Prioritised plan.**

| Rank | Risk | L | I | How |
|---|---|---|---|---|
| 1 | Message lost | 3 | 5 | Fault injection on the network at each step; soak tests with counted messages |
| 2 | Message delivered to the wrong person, or readable by non-members | 1 | 5 | Authorisation tests; security review |
| 3 | Duplicates or wrong order | 4 | 3 | Retry and concurrency tests with a controllable network |
| 4 | Notifications missing or excessive | 4 | 3 | Device-farm tests across OS versions |
| 5 | Sync between devices inconsistent | 3 | 3 | Multi-client automated scenarios |
| 6 | Battery and data drain | 3 | 3 | Profiling on real devices |
| 7 | Media edge cases | 3 | 2 | Partition tests |

**Summary.** I would build a test harness with several simulated clients and a network I can cut, delay and reorder, then verify the invariants "no loss, no duplicates, same order everywhere" over long randomised runs.

</details>

## 5. A recommendation model

**Prompt:** *"Your team trained a new model that recommends products on the home page. How do you test it before and after launch?"*

A model has no specification table. Its "correctness" is statistical, its inputs drift, and it can be technically accurate while harming the business. This prompt is increasingly common, also for general software roles.

<details><summary>Model answer</summary>

**Clarify.** What does it replace — an older model or a simple popularity list? What is the business goal: clicks, purchases, long-term retention? How is it served — precomputed daily or computed per request? What data does it learn from?

**Assume.** It replaces an existing model, is trained nightly on interaction logs, served in real time with a 100 ms budget, and the goal is purchases without hurting retention.

**Decompose along the pipeline.** (1) Data, (2) training code, (3) offline model quality, (4) behavioural and safety checks, (5) serving system, (6) online experiment, (7) monitoring after launch.

**Tests by stage.**

- *Data.* Schema and range checks on the training data: no missing identifiers, no future timestamps, expected volume within tolerance of yesterday's, no sudden change in the share of a category. **Leakage** check: no feature contains information from after the moment being predicted. Training and serving compute each feature the same way — compare the two on a sample of live requests.
- *Training code.* Ordinary unit tests for feature transformations; a tiny-dataset test where the model must overfit, which catches wiring mistakes; reproducibility with a fixed seed.
- *Offline quality.* Evaluate on a held-out period *later* than the training data, not a random split, because the model will be used on the future. Compare ranking metrics against the current model and against a trivial baseline such as "most popular". Slice the metric: new users, heavy users, each country, each product category — an average can improve while one group gets much worse.
- *Behavioural checks.* Invariants: never recommend out-of-stock, already-purchased-and-not-repeatable, or age-restricted items to the wrong audience; no duplicates in one list; results are stable for identical input; a brand-new user with no history still gets a sensible list (the cold-start partition); a user with one unusual purchase is not swamped by it. Diversity and fairness: not twenty near-identical items; no systematic exclusion of small sellers if that matters to the business.
- *Serving.* Latency percentiles under peak load; fallback to the old model or to a popularity list on timeout or error; behaviour with missing features; correct model version loaded; memory use.
- *Online experiment.* Offline metrics are a proxy, so the real test is an A/B experiment: a small percentage of users, primary metric purchases per session, **guardrail metrics** such as latency, returns, complaints, and revenue per user, a pre-decided duration and sample size, and a rule for stopping early if a guardrail is breached.
- *After launch.* Monitor input drift (feature distributions versus training), output drift (share of categories recommended), business metrics, and data-pipeline freshness. A model that is fine today degrades as the world changes, so testing never really ends.

**Prioritised plan.**

| Rank | Risk | L | I | How |
|---|---|---|---|---|
| 1 | Training–serving skew or leakage: great offline, bad online | 4 | 4 | Feature parity check; time-based split; A/B test |
| 2 | Harmful or embarrassing recommendations | 2 | 5 | Behavioural invariants as automated gates; manual review of samples |
| 3 | Serving latency or failure breaks the home page | 3 | 5 | Load tests; fallback tests; canary |
| 4 | Worse for an important segment | 3 | 4 | Sliced evaluation offline and in the experiment |
| 5 | Silent degradation from drift or a broken data feed | 4 | 3 | Monitoring and alerts on data and outputs |
| 6 | Not reproducible, cannot roll back | 2 | 4 | Versioned data, code and model; tested rollback |

**Summary.** I'd treat the model as one component in a pipeline: validate data, compare offline against a baseline on future data by segment, enforce hard behavioural rules, protect the page with a fallback, prove value in a guarded experiment, and keep watching for drift.

</details>

> [!INTERVIEW]
> For any machine-learning prompt, three phrases show that you understand why it differs from ordinary software: **"compare against a baseline"**, **"evaluate by slice, not only on average"**, and **"offline metrics are a proxy, so confirm with a guarded online experiment"**.

## Patterns across the five

| Product | Invariant to state | Special difficulty | Technique that unlocks it |
|---|---|---|---|
| Login | Only the right person gets a session | Invisible security properties | Decision table + lockout state machine |
| Search | Filters only narrow; exact code ranks first | No exact oracle | Golden set + invariants + online metrics |
| Payments API | One charge per idempotency key | Retries and lost replies | Programmable fake dependency; reconciliation |
| Chat | No loss, no duplicates, same order | Unreliable networks, many devices | Multi-client harness with a controllable network |
| Recommender | Never show forbidden items; no worse than baseline | Statistical correctness, drift | Baselines, slices, guardrailed experiment, monitoring |

## Summary

- Digital products add scale, concurrency and data integrity to the template, and let you place each check at the cheapest level of the test pyramid.
- When there is no exact expected result, use a judged sample, invariants and measured outcomes.
- For anything called by other programs, test retries, duplicates, timeouts and lost replies; idempotency is the central idea.
- For models, test the data and the pipeline as well as the predictions, compare with a baseline by segment, and confirm online behind guardrails.

## Glossary

| Term | Meaning |
|---|---|
| Unit test | An automated check of one small piece of code in isolation |
| Integration test | A check that several components work together |
| End-to-end test | A check of a whole user journey through the real system |
| Test pyramid | The advice to have many fast low-level tests and few slow high-level ones |
| Oracle | The means of knowing what the correct result should be |
| Metamorphic check | A property that must hold between related inputs, whatever the exact answer |
| Golden set | A fixed set of inputs with human-judged correct results |
| Idempotent | Having the same effect whether done once or several times |
| Session | The period during which a signed-in user is remembered |
| Enumeration | Discovering which accounts exist by observing different responses |
| Baseline | A simple existing method that a new one is compared against |
| Guardrail metric | A measure that must not get worse while another is improved |

## Check yourself

```quiz
[
  {"q": "Why should 'unknown email' and 'wrong password' produce the same message and similar response time?",
   "options": ["To save translation effort", "Otherwise an attacker can discover which emails are registered", "Because browsers require it", "To make the page load faster"],
   "answer": 1,
   "explain": "Different responses allow account enumeration, which feeds targeted attacks."},
  {"q": "A locked account receives the correct password. What is the expected behaviour?",
   "options": ["Log in, because the password is right", "Refuse, without revealing that the password was correct", "Delete the account", "Reset the lock timer and log in"],
   "answer": 1,
   "explain": "Lockout only protects the account if it holds even against the right password."},
  {"q": "Which is an invariant (metamorphic) check for search that needs no human judgment?",
   "options": ["The best sofa appears first", "Adding a filter never increases the number of results", "Users like the results", "The page looks modern"],
   "answer": 1,
   "explain": "Narrowing can only keep or reduce the result set; the property holds whatever the correct ranking is."},
  {"q": "A client sends the same charge request twice with the same idempotency key. What must happen?",
   "options": ["Two charges", "One charge; the second call returns the original result", "An error on both", "The second call charges a different card"],
   "answer": 1,
   "explain": "Idempotency keys exist so that retries after timeouts cannot duplicate a payment."},
  {"q": "The processor accepted a charge but its reply was lost. Which test covers this?",
   "options": ["A unit test of amount validation", "Cutting the connection after the request is sent and checking that the API reconciles to the true outcome", "A load test", "A screenshot comparison"],
   "answer": 1,
   "explain": "The unknown-outcome case needs fault injection after the send and a status lookup or reconciliation path."},
  {"q": "Which trio describes the core delivery invariants for a chat app?",
   "options": ["Fast, cheap, pretty", "No loss, no duplicates, consistent order", "Blue, green, canary", "Unit, integration, system"],
   "answer": 1,
   "explain": "These three properties must hold through retries, reconnections and multiple devices."},
  {"q": "Why evaluate a recommendation model on a later time period rather than a random split?",
   "options": ["It uses less memory", "The model will be used on future data, and a random split can leak future information into training", "Random splits are illegal", "Later data is always cleaner"],
   "answer": 1,
   "explain": "A time-based split mirrors real use and guards against leakage that inflates offline scores."},
  {"q": "What is a guardrail metric in an A/B test of a new model?",
   "options": ["The primary metric being optimised", "A metric that must not get worse, such as latency or complaints, whose breach stops the experiment", "The number of engineers on the team", "The model's training loss"],
   "answer": 1,
   "explain": "Guardrails protect against winning the primary metric while damaging something else."}
]
```

> **Source:** Original worked examples. Test-level reasoning follows Martin Fowler, "Test Pyramid" (https://martinfowler.com/bliki/TestPyramid.html) and *Software Engineering at Google*, ch. 11 "Testing Overview" and ch. 14 "Larger Testing" (https://abseil.io/resources/swe-book/html/ch11.html, https://abseil.io/resources/swe-book/html/ch14.html). Technique names follow the ISTQB Foundation Level syllabus v4.0, ch. 4 (https://www.istqb.org/certifications/certified-tester-foundation-level). Canary analysis: Martin Fowler, "Canary Release" (https://martinfowler.com/bliki/CanaryRelease.html).
