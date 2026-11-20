# Test doubles and strategy for real projects

> **Before this lesson:** read [Testing quadrants and the test pyramid](#/lesson/cicd/quadrants-pyramid) for the kinds of test. The Python examples use classes; each one is explained as it appears.

## In plain words

A film does not throw its lead actor off a building. A stunt double stands in for the dangerous scene. A flight simulator lets a pilot practise an engine failure without a real aircraft.

Tests use stand-ins for the same reason. Suppose you want to check what your program does when a payment is refused. You do not want to call a real bank, wait for the internet and hope the bank refuses. You put a pretend bank in its place that always says "refused". Such a stand-in is called a **test double**.

A **dependency** here means any other part that your code relies on: a database, another company's service, the clock. The first half of this lesson describes the five kinds of double and when to use each. The second half is about the bigger picture: how to introduce testing on a new project, on one that is already under way, and on old code that has no tests at all (often called **legacy** code).

Why this matters for a job: "what is the difference between a mock and a stub?" is a classic interview question, and "how would you add tests to a legacy system?" is its senior version.

## Motivation: the test that needs the whole world

You want to test that an order is marked *paid* when the payment provider accepts the charge. The real code calls an HTTP API owned by another company, writes to a database, publishes an event to a queue and sends an email. If the test uses all the real things, it needs network access, a sandbox account, a seeded database, a running broker and a mailbox — and it fails whenever any of them hiccups. If the test uses none of them, what is it actually verifying?

Replacing a collaborator with a stand-in for the purpose of a test is one of the most useful and most abused techniques in automated testing. The stand-in is called a **test double** (by analogy with a stunt double). This lesson explains the five kinds, when each is appropriate, and how to keep doubles from lying to you. The second half takes the testing strategy from the previous lesson and adapts it to three situations you will actually meet: a new project, a project already in flight, and a legacy system with no tests at all.

## The five kinds of double

The vocabulary comes from Gerard Meszaros. People say "mock" for all of them, which hides useful distinctions.

| kind | what it does | typical use |
|---|---|---|
| **Dummy** | Passed around but never used | Filling a required parameter |
| **Stub** | Returns canned answers to calls | Driving the code down a chosen path ("the gateway says *declined*") |
| **Spy** | A stub that also records how it was called | Checking afterwards that an email was requested |
| **Mock** | Pre-programmed with expectations; fails if they are not met | Verifying an interaction protocol strictly |
| **Fake** | A working but simplified implementation | In-memory repository, local object store, embedded broker |

```mermaid
flowchart LR
  T[Test] --> S[System under test: OrderService]
  S --> G[PaymentGateway]
  S --> R[OrderRepository]
  S --> M[Mailer]
  G -.replaced by.-> GS[Stub: returns approved or declined]
  R -.replaced by.-> RF[Fake: dict in memory]
  M -.replaced by.-> MS[Spy: records messages]
```

Two styles of verification follow from these:

- **State verification**: run the code, then inspect the result or the fake's contents. ("The order's status is `paid`.")
- **Behaviour verification**: assert that particular calls were made. ("`gateway.charge` was called once with 49.90.")

Prefer state verification wherever the outcome is observable. Tests that assert on *how* the work was done break every time the implementation is refactored, even when the behaviour is unchanged. Reserve behaviour verification for cases where the call *is* the outcome — an email sent, an event published, a charge made.

### All five in one example

```python-run
class PaymentDeclined(Exception):
    pass

class OrderService:
    def __init__(self, gateway, repo, mailer, clock):
        self.gateway, self.repo, self.mailer, self.clock = gateway, repo, mailer, clock

    def pay(self, order_id, card_token, audit_ctx=None):
        order = self.repo.get(order_id)
        if not self.gateway.charge(card_token, order["total"]):
            raise PaymentDeclined(order_id)
        order["status"] = "paid"
        order["paid_at"] = self.clock()
        self.repo.save(order)
        self.mailer.send(order["email"], f"Receipt for order {order_id}")
        return order

# --- doubles -----------------------------------------------------------------
class StubGateway:                      # STUB: canned answer
    def __init__(self, approve): self.approve = approve
    def charge(self, token, amount): return self.approve

class FakeRepo:                         # FAKE: real behaviour, simple storage
    def __init__(self): self.rows = {}
    def get(self, oid): return dict(self.rows[oid])
    def save(self, order): self.rows[order["id"]] = dict(order)

class SpyMailer:                        # SPY: records calls for later inspection
    def __init__(self): self.sent = []
    def send(self, to, subject): self.sent.append((to, subject))

fixed_clock = lambda: "2026-06-01T12:00:00Z"   # STUB for time
DUMMY = object()                               # DUMMY: required but irrelevant

def make(approve):
    repo, mailer = FakeRepo(), SpyMailer()
    repo.save({"id": 7, "total": 49.90, "email": "ana@example.com", "status": "new"})
    return OrderService(StubGateway(approve), repo, mailer, fixed_clock), repo, mailer

# test 1: approved payment -> state changed, receipt sent
svc, repo, mailer = make(approve=True)
svc.pay(7, "tok_1", audit_ctx=DUMMY)
assert repo.rows[7]["status"] == "paid"                       # state verification
assert repo.rows[7]["paid_at"] == "2026-06-01T12:00:00Z"
assert mailer.sent == [("ana@example.com", "Receipt for order 7")]   # behaviour (the email IS the outcome)
print("approved path: ok")

# test 2: declined payment -> nothing saved, nothing sent
svc, repo, mailer = make(approve=False)
try:
    svc.pay(7, "tok_1")
    raise SystemExit("expected PaymentDeclined")
except PaymentDeclined:
    pass
assert repo.rows[7]["status"] == "new"
assert mailer.sent == []
print("declined path: ok")
```

Three design points make this easy, and they are worth copying:

1. **Dependencies are injected.** `OrderService` receives its collaborators through the constructor instead of creating them. Swapping in a double needs no patching trickery.
2. **Time is a dependency.** The clock is passed in, so tests are deterministic. Code that calls the system clock directly cannot be tested for "what happens at midnight on the last day of the month" without waiting for it.
3. **The doubles are hand-written and tiny.** Mocking libraries are convenient, but a ten-line fake is often clearer and can be reused across hundreds of tests.

## When doubles lie

A double encodes your *belief* about how the real collaborator behaves. If the belief is wrong, or becomes wrong when the other team changes their API, every test passes and production breaks. Three defences:

**Double at the edge of what you own.** Wrap a third-party client in a thin adapter with an interface in your own vocabulary (`PaymentGateway.charge`), and double the adapter, not the vendor's SDK. Your tests then do not depend on the SDK's internals.

**Test the adapter against the real thing, separately.** A small number of integration tests exercise the real adapter against the provider's sandbox or a containerised instance. They are slow and occasionally unreliable, so they run in a later stage and are few.

**Use contract tests between services.** In *consumer-driven contract testing*, the consuming service records the requests it makes and the responses it relies on. That record (the contract) is replayed against the real provider in the provider's own pipeline. If the provider breaks an expectation, its build fails before it deploys. Tools such as Pact implement this pattern.

```mermaid
sequenceDiagram
  participant C as Consumer pipeline
  participant B as Contract broker
  participant P as Provider pipeline
  C->>C: unit tests run against a stub of the provider
  C->>B: publish contract: requests sent and responses relied on
  P->>B: fetch contracts from all consumers
  P->>P: replay each contract against the real provider build
  P-->>B: verification result
  Note over C,P: a provider change that breaks a consumer fails the provider build
```

> [!WARNING]
> Over-mocking produces tests that restate the implementation line by line: "expect `a()` then `b()` then `c()`". They pass when the code is wrong in the same way the test is, and fail whenever the code is refactored correctly. If a test would still pass after you deleted the logic it is supposed to cover, it is testing the mocks.

### Real dependencies in a box

For databases and brokers, a third option now sits between "mock it" and "shared test server": start the real thing in a throwaway container for the duration of the test run.

```yaml
# GitHub Actions: a real PostgreSQL for component tests, discarded afterwards
jobs:
  component-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16.4
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s --health-timeout 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - run: make test-component
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/postgres
```

A rule of thumb: use an in-memory fake for unit tests of logic, a real engine in a container for tests of your SQL and mapping code, and a double only for systems you cannot run yourself.

## Strategy by project situation

### A new project

This is the easy case, and the time to set the rules while they are cheap.

- From the first story, write acceptance criteria as testable scenarios and automate them.
- Establish the commit stage on day one, even when it has three tests in it. An empty pipeline that deploys "hello world" to a production-like environment is worth more than a hundred tests with nowhere to run.
- Agree that a story is not finished until its automated tests are in the pipeline.
- Have developers and testers pair on acceptance tests, so the tests are maintainable code and the scenarios reflect real risk.

Starting later is always more expensive: code written without tests in mind tends to be hard to test, because dependencies are hard-wired.

### A project already under way

You have a codebase, some tests, perhaps a slow manual regression cycle, and no time to stop and rewrite. Work in priority order:

1. **Automate the most valuable, most common journeys first.** Pick the handful of end-to-end happy paths that would be embarrassing to break — sign up, search, buy — and automate those. A small, reliable suite that is always run beats a large, aspirational one.
2. **Use the manual regression script as a backlog.** Each time a manual test is run, ask whether it can be automated, and move the cheapest high-value ones over.
3. **Apply the Boy Scout rule to everything you touch.** New features get tests at the right level; a bug fix starts with a failing test that reproduces the bug.
4. **Resist testing through the UI only because it is the only seam.** If there is no API to test against, adding one is usually worth it.

### A legacy system with no tests

A widely quoted definition (Michael Feathers) is that legacy code is code without tests. The danger is obvious: you must change it, and you have no way to know what you broke.

The order of work matters:

1. **Automate the build and deployment first**, so you can create an environment to run anything at all.
2. **Write a thin layer of broad characterisation tests.** These pin down what the system *currently does* — right or wrong — at its outermost boundary. They are a safety net, not a specification.
3. **Add tests around each area before you change it.** Do not try to retrofit unit tests to the whole codebase; coverage should follow the changes.
4. **Introduce seams as you go.** Extract an interface around a hard-wired dependency so it can be doubled next time.

```python-run
import hashlib, json

def legacy_shipping_quote(weight_kg, country, express):
    """Imagine 400 lines nobody dares touch. Behaviour includes at least one 'bug'."""
    base = 4.9 if country == "DE" else 9.9
    if weight_kg > 20:
        base += (weight_kg - 20) * 0.5
    if express:
        base *= 2
    if country == "CH" and express:
        base = base - 0.01          # an oddity that customers' systems may now rely on
    return round(base, 2)

# 1) Record current behaviour over a grid of inputs: the "golden master".
grid = [(w, c, e) for w in (0, 1, 20, 21, 35) for c in ("DE", "FR", "CH") for e in (False, True)]
golden = {json.dumps(k): legacy_shipping_quote(*k) for k in grid}
print(f"recorded {len(golden)} cases, fingerprint",
      hashlib.sha256(json.dumps(golden, sort_keys=True).encode()).hexdigest()[:12])

# 2) Refactor, then compare against the recording.
def refactored_quote(weight_kg, country, express):
    base = {"DE": 4.9}.get(country, 9.9) + max(0, weight_kg - 20) * 0.5
    if express:
        base *= 2
    return round(base, 2)            # the refactorer "cleaned up" the CH oddity

diffs = [(k, golden[json.dumps(k)], refactored_quote(*k))
         for k in grid if refactored_quote(*k) != golden[json.dumps(k)]]
print(f"{len(diffs)} behaviour change(s) detected:")
for k, old, new in diffs:
    print(f"  input={k}  before={old}  after={new}")
```

The characterisation test does not say whether the Swiss express oddity is right. It says the refactoring changed behaviour, which forces a conscious decision instead of an accidental one. That is exactly the safety a legacy change needs.

> [!TIP]
> When a bug escapes to production, the first step of the fix is a test that fails because of it, placed at the lowest level that can reproduce it. Over time the suite grows precisely where the code is weakest.

## Integration tests against external systems

Some risk can only be covered by talking to a system you do not control. Rules that keep this manageable:

- **Keep the set small and focused** on the contract: the calls you make, the responses and error cases you handle.
- **Run them in their own stage**, not in the commit stage, so an outage at the provider does not block every merge. Report their failures clearly as "provider or contract problem".
- **Also build a simulator** (a stub service) of each external system. It lets acceptance and capacity tests run without the real dependency, and lets you inject conditions the real system rarely produces: timeouts, malformed responses, slow replies, rate-limit errors.
- **Test the unhappy paths deliberately.** What happens when the provider takes 30 seconds, or returns HTML instead of JSON? The simulator can do that on demand.

## Managing the defect backlog

A strategy also has to say what happens to bugs that are found. A large backlog of known defects is itself a quality problem: nobody can tell what state the product is in, and new bugs hide among old ones.

Two workable policies:

- **Zero-defect policy.** A bug is either fixed straight away or explicitly closed as "will not fix". The backlog stays empty by construction.
- **Bugs are prioritised like features.** Every defect goes into the same queue as feature work and the product owner ranks them together, with severity and likelihood stated. A low-impact cosmetic bug may sit below a valuable feature, and that is a legitimate business choice, made visibly.

Either beats the common third state: an ever-growing list in a tracker that nobody reads.

## Pitfalls

- **Doubles for things you could run yourself.** A mocked database tells you nothing about your SQL. Use the real engine in a container.
- **Shared mutable test environments** used as "integration" by several teams. Failures become unattributable. Prefer per-run, isolated dependencies.
- **Doubling value objects and simple helpers.** If the real thing is fast, deterministic and has no side effects, use it.
- **Fakes that drift.** An in-memory repository that sorts differently from the real database gives false confidence. Run the same behavioural test suite against both the fake and the real implementation.
- **Rewriting legacy code before pinning its behaviour.** The most expensive way to discover what the old code did.
- **Tests that share state.** One test's leftovers make another pass or fail depending on order. Each test sets up what it needs and cleans up.

> [!INTERVIEW]
> "What's the difference between a mock and a stub?" A stub supplies canned return values so the code under test can proceed; you assert on the resulting state. A mock carries expectations about the calls it should receive and the test fails if they are not met; you are verifying behaviour. Add the judgement: prefer stubs and fakes with state assertions, use mocks or spies only when the interaction itself is the required outcome, and back any doubled external dependency with contract or integration tests.

## Summary

- A test double replaces a collaborator: dummies fill parameters, stubs give canned answers, spies record calls, mocks enforce expectations, fakes are simplified working implementations.
- Prefer state verification; verify behaviour only when the call is the outcome.
- Inject dependencies, including the clock, so doubles are easy to supply.
- Guard against doubles that lie with adapter integration tests and consumer-driven contract tests; use real engines in containers where you can.
- New projects: automate from the first story. Mid-flight projects: automate the highest-value journeys and test everything you touch. Legacy systems: automate build and deploy, pin behaviour with characterisation tests, then add tests where you change code.
- Keep external integration tests few and separate, build simulators for unhappy paths, and manage defects with an explicit policy.

## Glossary

- **Test double** — a stand-in that replaces a real collaborator during a test.
- **Dependency (collaborator)** — another component that the code under test relies on.
- **Dummy** — a value passed only to fill a parameter; never used.
- **Stub** — a double that returns fixed, pre-arranged answers.
- **Spy** — a stub that also records how it was called.
- **Mock** — a double programmed with expectations that fails the test if they are not met.
- **Fake** — a simplified but working implementation, such as an in-memory database.
- **State verification** — checking the result after the code has run.
- **Behaviour verification** — checking which calls the code made.
- **Dependency injection** — passing a component its collaborators instead of letting it create them.
- **Adapter** — a thin wrapper that presents an outside service through your own interface.
- **Contract test** — a check that a service still meets what its consumers expect.
- **Legacy code** — existing code, typically without automated tests.
- **Characterisation test** — a test that records what code currently does, to detect unintended changes.
- **Seam** — a place where behaviour can be changed for a test without editing the code under test.

## Check yourself

```quiz
[
  {"q": "Which double is a simplified but working implementation, such as an in-memory repository?",
   "options": ["Dummy", "Stub", "Mock", "Fake"],
   "answer": 3,
   "explain": "A fake actually behaves like the real thing in a lightweight way, so tests can verify state through it."},
  {"q": "What distinguishes a mock from a stub?",
   "options": ["A mock is faster", "A mock carries expectations about calls and fails the test if they are not met; a stub only supplies canned answers", "A stub records calls and a mock does not", "They are the same thing"],
   "answer": 1,
   "explain": "Stubs support state verification by steering the code. Mocks perform behaviour verification."},
  {"q": "Why inject the clock into code that depends on the current time?",
   "options": ["System clocks are inaccurate", "So tests can control time and stay deterministic", "To reduce memory use", "Because dates cannot be compared otherwise"],
   "answer": 1,
   "explain": "Hidden calls to the real clock make outcomes depend on when the test runs and make edge cases such as month-end untestable."},
  {"q": "All unit tests pass using a stub of another team's API, but production fails because that API changed its response format. Which practice would have caught this earliest?",
   "options": ["More unit tests with the same stub", "Consumer-driven contract tests verified in the provider's pipeline", "Higher code coverage", "Manual testing after release"],
   "answer": 1,
   "explain": "A contract replayed against the real provider fails the provider's build as soon as it breaks an expectation a consumer relies on."},
  {"q": "What is the purpose of a characterisation (golden master) test on legacy code?",
   "options": ["To prove the code is correct", "To record current behaviour so that unintended changes are detected during refactoring", "To measure performance", "To replace acceptance tests permanently"],
   "answer": 1,
   "explain": "It pins what the system does today, right or wrong, providing a safety net before any change."},
  {"q": "On a project already in progress with little automation, what should be automated first?",
   "options": ["Every edge case of every feature", "The few most common and most valuable user journeys", "Only the newest feature", "The UI layout checks"],
   "answer": 1,
   "explain": "A small reliable suite on the critical happy paths delivers the most protection for the least cost, and can be grown from there."},
  {"q": "Why run tests against real external systems in a separate pipeline stage?",
   "options": ["They are unimportant", "Their slowness and occasional unavailability should not block every merge in the commit stage", "They cannot be automated", "External systems forbid frequent calls in all cases"],
   "answer": 1,
   "explain": "Isolating them keeps the fast gate reliable while still exercising the real contract regularly."},
  {"q": "Which is a sign of over-mocking?",
   "options": ["Tests assert on the final state of an order", "Tests break whenever the implementation is refactored without any behaviour change", "Tests use an in-memory fake", "Tests run in under a second"],
   "answer": 1,
   "explain": "Tests that specify the sequence of internal calls are coupled to the implementation rather than the behaviour."}
]
```

> **Source:** Humble & Farley, *Continuous Delivery*, ch. 4 (test doubles; strategies for new, mid-project and legacy systems; integration testing; defect backlogs). Double taxonomy after Gerard Meszaros, *xUnit Test Patterns*. GitHub Actions service containers: https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/about-service-containers — Pact: https://docs.pact.io
