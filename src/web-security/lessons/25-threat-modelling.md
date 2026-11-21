# Secure architecture and threat modelling (STRIDE)

> **Before this lesson:** read [The security mindset and a short history](#/lesson/web-security/security-mindset) for assets, threats, risk and the six principles, and [APIs, dependencies and architecture review](#/lesson/web-security/apis-architecture) for drawing a system and listing entry points. The vulnerability lessons in between supply the examples.

## In plain words

Before an architect lets anyone pour concrete, they walk through the drawings asking uncomfortable questions. Where does the fire spread if it starts in the kitchen? What if this beam fails? Where would a burglar get in? Changing a line on a drawing costs minutes. Moving a staircase in a finished building costs a fortune.

**Threat modelling** is that walk-through for software. A few people sit down with a diagram of the system — before or while it is built — and ask, methodically, "what could go wrong here, and what are we going to do about it?" The output is a list of threats with a decision for each.

It is the most cost-effective security activity there is, because it finds *design* flaws, the kind no scanner detects and no patch fixes: a missing authorisation model, a service that trusts another too much, a feature with no abuse limits. It needs no special tools and no security title. And it is a favourite in interviews, usually phrased as "design X — now how would you secure it?" This lesson gives you a repeatable way to answer.

## The four questions

Every threat-modelling method, whatever its name, answers four questions. Memorise them; they are the skeleton of the exercise.

1. **What are we working on?** — draw it.
2. **What can go wrong?** — find threats.
3. **What are we going to do about it?** — decide on responses.
4. **Did we do a good job?** — check the work.

We take them in order, using the toy shop from the earlier lessons.

## Question 1: what are we working on?

You cannot find threats in a system you cannot see. The standard picture is a **data-flow diagram (DFD)**. It has only four kinds of element plus one kind of line:

| Element | Meaning | Examples |
|---|---|---|
| **External entity** | Someone or something outside your control | A customer's browser, a payment provider |
| **Process** | Code that you run | The web API, a background worker |
| **Data store** | Where data rests | A database, a file bucket, a cache, a log |
| **Data flow** | Data moving between two elements | An HTTPS request, a database query |
| **Trust boundary** | A line where the level of trust changes | Internet ↔ your network; your API ↔ a third party |

```mermaid
flowchart LR
    C[Customer browser] -->|1 HTTPS requests| API[Shop API]
    API -->|2 SQL queries| DB[(Orders database)]
    API -->|3 payment request| PAY[Payment provider]
    PAY -->|4 signed webhook| API
    API -->|5 job messages| Q[(Job queue)]
    Q --> W[Email worker]
    W -->|6 SMTP| MAIL[Email service]
    subgraph Trusted network
      API
      DB
      Q
      W
    end
```

The numbered arrows are the data flows. The box marks the main trust boundary: everything crossing it — flows 1, 3, 4 and 6 — deserves the closest attention, because that is where data from a less trusted place enters a more trusted one.

While drawing, also write down:

- the **assets** — what is worth protecting (customer personal data, payment status, admin access, availability of checkout);
- the **actors** — anonymous visitor, customer, support agent, administrator, other services;
- **assumptions** — "the payment provider is trusted to tell us the truth about payments". Assumptions are where threats hide.

Keep the diagram modest. One screen, ten to twenty elements. A model that is too detailed to finish is worth less than a rough one that is done.

## Question 2: what can go wrong? — STRIDE

Staring at a diagram and "thinking like an attacker" produces patchy results. **STRIDE** is a checklist that makes the search systematic. It was developed at Microsoft in the late 1990s, and each letter names a category of threat. Every category is the violation of one security property — which is the easiest way to remember them.

| Letter | Threat | Property violated | Plain question | Example in the shop | Typical controls |
|---|---|---|---|---|---|
| **S** | **Spoofing** | Authentication | Can someone pretend to be someone or something else? | A forged "payment succeeded" webhook | Authentication, signatures, MFA, TLS certificates |
| **T** | **Tampering** | Integrity | Can someone change data or code they should not? | Editing the price in a request; altering an order row | Validation, authorisation, signatures, hashes, parameterised queries |
| **R** | **Repudiation** | Non-repudiation | Can someone deny an action because we cannot prove it? | An admin issues a refund and no record shows who | Audit logs, timestamps, signed records |
| **I** | **Information disclosure** | Confidentiality | Can someone see what they should not? | IDOR on invoices; stack traces; secrets in logs | Authorisation, encryption, minimal responses, redaction |
| **D** | **Denial of service** | Availability | Can someone stop it working for others? | Unbounded export; regex blow-up | Limits, rate limiting, timeouts, scaling |
| **E** | **Elevation of privilege** | Authorisation | Can someone gain rights they should not have? | A customer reaching an admin endpoint; command injection | Deny by default, least privilege, sandboxing |

*Non-repudiation* means being able to prove afterwards who did what. Notice that the first three letters of the CIA triad are all here (T, I, D), joined by authentication, authorisation and accountability.

### STRIDE-per-element

Not every category applies to every kind of element. A data flow cannot "elevate privilege"; an external entity is not yours to protect from tampering. The usual table:

| Element | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| External entity | ✓ | | ✓ | | | |
| Process | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Data store | | ✓ | ✓ | ✓ | ✓ | |
| Data flow | | ✓ | | ✓ | ✓ | |

(Repudiation applies to data stores chiefly when they hold logs.) So the method is mechanical: for each element, ask the questions its row allows. A short program can generate the worksheet:

```python-run
APPLICABLE = {"external": "SR", "process": "STRIDE", "datastore": "TRID", "dataflow": "TID"}
NAMES = {"S": "Spoofing", "T": "Tampering", "R": "Repudiation",
         "I": "Information disclosure", "D": "Denial of service", "E": "Elevation of privilege"}

elements = [
    ("Customer browser", "external"),
    ("Shop API", "process"),
    ("Orders database", "datastore"),
    ("Flow 4: payment webhook", "dataflow"),
]

total = 0
for name, kind in elements:
    letters = [c for c in "STRIDE" if c in APPLICABLE[kind]]     # keep STRIDE order
    total += len(letters)
    print(f"{name} ({kind})")
    for letter in letters:
        print(f"    [{letter}] {NAMES[letter]}: how could this happen here? what stops it?")
print("questions to answer:", total)
```

`APPLICABLE` maps each element type to the letters that apply. The list comprehension walks through the word `STRIDE` and keeps the letters allowed for that type, which preserves the conventional order. Four elements produce fifteen focused questions — a manageable agenda for a one-hour session, and far better than a blank page.

### Working one element through

Take **flow 4**, the webhook by which the payment provider tells the shop a payment succeeded. It is a data flow crossing a trust boundary, so T, I and D apply — and its *source* is an external entity, so S and R apply to that.

- **Spoofing:** can anyone on the internet call `/webhooks/payment` and claim an order is paid? → Verify the provider's signature on every webhook; reject otherwise.
- **Tampering:** could the amount or order ID be altered in transit, or could an old genuine message be replayed? → HTTPS; signature covers the body; check a timestamp and store processed event IDs to refuse replays.
- **Information disclosure:** does the webhook or our response carry card data or internal details? → Accept only the fields needed; return a bare `200`.
- **Denial of service:** could a flood of webhook calls exhaust the API? → Rate-limit; verify the signature before doing any expensive work; process asynchronously through the queue.
- **Repudiation:** if a customer disputes a charge, can we show what the provider told us and when? → Log the event ID, time and outcome.

That is five concrete, testable requirements from one arrow. Compare the order-shipping bug in [Business-logic flaws](#/lesson/web-security/business-logic): threat modelling is where it would have been caught.

### Other ways to find threats

STRIDE is the one to know. Three complements are worth recognising:

- **Abuse cases**: "As a dishonest customer I want to…" — excellent for business logic.
- **Attack trees**: start from an attacker's goal ("read another customer's orders") and branch into the ways to achieve it.
- **Checklists and catalogues**: the OWASP Top 10 and the Application Security Verification Standard (ASVS) as prompts for what you may have missed.

## Question 3: what are we going to do about it?

### Rate the risk

A session produces more threats than can be fixed at once. Order them by **risk = likelihood × impact**, each judged on a small scale.

```python-run
threats = [
    {"id": "T1", "what": "Forged payment webhook marks orders paid",     "likelihood": 4, "impact": 5},
    {"id": "T2", "what": "Customer reads other customers' invoices",     "likelihood": 4, "impact": 4},
    {"id": "T3", "what": "No audit record of admin refunds",             "likelihood": 2, "impact": 4},
    {"id": "T4", "what": "Version banner in Server header",              "likelihood": 3, "impact": 1},
    {"id": "T5", "what": "Unbounded CSV export exhausts the database",   "likelihood": 3, "impact": 3},
]

def level(score):
    if score >= 15: return "critical"
    if score >= 10: return "high"
    if score >= 5:  return "medium"
    return "low"

for t in threats:
    t["score"] = t["likelihood"] * t["impact"]

# Highest score first; on a tie, the higher impact first; then by id for a stable order
for t in sorted(threats, key=lambda t: (-t["score"], -t["impact"], t["id"])):
    print(f"{t['id']}  score {t['score']:2}  {level(t['score']):8}  {t['what']}")
```

Each threat is a dictionary. The loop computes `score`. `sorted(..., key=...)` orders by a tuple; negating a number sorts it descending. T1 and T2 lead the list; the version banner, real but minor, comes last. The numbers are judgements, not measurements — their value is in forcing the team to *agree* on an order and to write it down.

Likelihood considers: how exposed is it (internet-facing, unauthenticated)? How easy? How attractive? Impact considers: how much data, money or downtime, and how many users? Published schemes exist for consistency — CVSS for rating individual vulnerabilities, OWASP's Risk Rating Methodology for threats — but a simple 1–5 grid is a good start.

### Choose a response

For each threat there are four possible decisions:

| Response | Meaning | Example |
|---|---|---|
| **Mitigate** | Add a control that reduces likelihood or impact | Verify webhook signatures |
| **Eliminate** | Remove the feature or data that creates the threat | Stop storing card numbers; drop the export endpoint |
| **Transfer** | Hand the risk to another party | Use a payment provider's hosted checkout; buy insurance |
| **Accept** | Decide, consciously and on record, to live with it | Low-impact banner disclosure until the next maintenance window |

"Accept" is legitimate only when it is explicit, made by someone with the authority to accept that risk, and written down. The dangerous state is the fifth, unofficial one: *ignored*.

Every "mitigate" becomes a ticket and — ideally — a test. A mitigation without a test tends to disappear in a later refactoring.

## Question 4: did we do a good job?

- Does the diagram still match what was built? Revisit the model when the architecture changes: a new integration, a new data store, a new kind of user.
- Does every identified threat have a recorded decision, an owner and a status?
- Do the mitigations have tests?
- When an incident or a penetration-test finding occurs, ask: *was this in the model?* If not, why not — and what similar things did we miss?

A threat model is a living document, kept with the code. A lightweight version is a markdown file in the repository with the diagram, the table of threats and the decisions.

```mermaid
flowchart LR
    D[Draw the system] --> F[Find threats with STRIDE]
    F --> R[Rate and decide a response]
    R --> B[Build mitigations and tests]
    B --> V[Verify and review]
    V -->|system changes| D
```

## Secure architecture: principles that remove threats wholesale

Threat modelling finds problems one at a time. Good architecture makes whole categories unlikely. These are the design-level habits behind the specific defences in this track.

**Minimise the attack surface.** Every endpoint, port, feature and dependency is a liability. Expose only the load balancer; put admin tools behind single sign-on on a private network.

**Establish trust boundaries and validate at each.** Do not let "it came from our other service" excuse a lack of validation or authentication between services. Internal calls carry identities and are checked — the *zero trust* stance.

**Least privilege everywhere.** Separate database accounts per service with only the rights they need; cloud roles scoped to specific resources; processes running as unprivileged users.

**Defence in depth.** Pair every preventive control with a second, independent one and with detection: encoding *and* CSP; parameterised queries *and* a restricted database account *and* alerting on errors.

**Secure defaults and fail closed.** Authentication required unless a route is marked public; errors deny.

**Centralise security decisions.** One authentication mechanism, one authorisation layer, one validation approach, one logging pipeline. Central code is reviewed once and fixed once.

**Do not invent security mechanisms.** Use standard protocols and vetted libraries for cryptography, sessions, password hashing and token handling.

**Separate duties and segment.** The public site and the admin console are different applications with different sessions. Sensitive data lives in its own store with its own access path. A compromise of one part should not hand over the rest.

**Minimise and classify data.** Data you do not collect cannot leak. Decide what is sensitive — personal data, credentials, payment data — and apply stronger controls there: encryption at rest, tighter access, shorter retention, no logging.

**Design for failure and recovery.** Assume a breach will happen: can you detect it, limit it, rotate credentials quickly and restore from backups?

```python
# A design smell and its repair, in miniature

# VULNERABLE DESIGN: every service connects as the database owner
DATABASE_URL = "postgresql://owner:...@db/shop"          # used by API, worker, reporting

# SAFER DESIGN: one narrowly scoped account per component
API_DATABASE_URL       = "postgresql://shop_api:...@db/shop"        # read/write own tables
WORKER_DATABASE_URL    = "postgresql://shop_worker:...@db/shop"     # read orders, write email_log
REPORTING_DATABASE_URL = "postgresql://shop_reports:...@replica/shop"   # read-only, on a replica
```

Nothing about the application's features changed. But an injection flaw in the reporting tool now reaches a read-only copy instead of everything.

> [!TIP]
> You do not need a formal meeting to start. On any design document or pull request that adds an endpoint, a data store or an integration, spend ten minutes asking the six STRIDE questions about the new piece and write the answers in the description. Small, frequent threat modelling beats a large annual one.

> [!WARNING]
> Threat modelling fails in two characteristic ways: it produces a beautiful diagram and no tickets, or it lists two hundred threats with no priorities. Aim for the top handful of risks, each with an owner and a test.

> [!INTERVIEW]
> For "design a secure X" — a login system, a file-sharing feature, a payments flow — structure the answer on the four questions. Sketch the components and trust boundaries; name the assets; walk STRIDE across the main elements, giving one concrete threat and control per letter; rank the top risks; mention logging and how you would verify. Using the names *trust boundary*, *STRIDE*, *least privilege* and *defence in depth* naturally, attached to specifics, is what distinguishes a prepared candidate.

## Sensitive data: PII and financial data

Many threats in a model reduce to one question: what is stored where, and what would it be worth to an attacker? Marking the data on your diagram makes the answer visible.

**Classify first.** *Data classification* sorts information into a few levels, each with handling rules. A common four-level scheme is *public* (the marketing page), *internal* (staff wiki), *confidential* (customer records) and *restricted* (card numbers, passwords, health data). The rules attach to the level: restricted data is encrypted at rest and in transit, access is logged and limited to few roles, and it never appears in logs, test data or screenshots. **Personally identifiable information** (PII) is anything that identifies a real person, alone or in combination: a name with an address, an email address, a national ID number, a device identifier. Law, such as GDPR in Europe, adds obligations on top.

**Minimise.** The cheapest data to protect is data you do not hold. Ask of every field: do we need it, do we need it *now*, do we need it in this form? Collect less; delete on a schedule; show only the last four digits on screen; keep PII out of logs and error messages; give analytics a pseudonymous ID instead of an email address. In the model, every data store that holds PII is a threat target, so every one you remove shrinks the model.

**Tokenise.** **Tokenisation** replaces a sensitive value with a meaningless stand-in (a token) and keeps the real value in a tightly guarded **vault**. Your database stores `tok_8f3a...` instead of a card number; only the vault, or the payment provider, can turn it back. Unlike encryption there is no key that decrypts a stolen token, so the rest of your system holds nothing worth stealing. Tokens can even be shaped like the original (for example, the same length) so that old software keeps working.

**Shrink the PCI DSS scope.** **PCI DSS** is the industry security standard for anyone who handles payment-card data. Its requirements apply to every system that stores, processes or transmits card numbers, plus every system connected to those. That *scope* is where the cost is, so the best strategy is to make it small:

- let a payment provider collect the card number through a hosted page or hosted fields inside an iframe, so card data never touches your servers (this puts you in the lightest compliance category);
- store the provider's token and the last four digits, never the full number;
- never store the security code (CVV) after authorisation;
- separate any remaining card-handling systems on their own network segment.

This is a high-level orientation, not legal advice; read the standard and your provider's guidance for the details that apply to you.

## Protecting search features

A search box feels harmless, yet it takes free text from anyone, runs a query against your data and returns what it finds. That shape invites three threats.

**Search injection.** If the text is pasted into a query, the user controls part of it. SQL `LIKE` clauses, NoSQL operator objects, LDAP filters and the query syntax of full-text engines are all injectable. In some engines the special syntax lets a visitor write `field:value`, reach fields you never meant to expose, or submit a regular expression or leading wildcard that burns CPU for minutes. Defences: parameterise queries; use a *simple* query parser that treats input as plain words; escape special characters; allow only listed fields and sort columns; and cap the query length and number of terms.

**Rate limiting.** Search is expensive and easy to automate, so it is a target for **denial of service** (overload) and for **scraping** (harvesting everything by querying `a`, `b`, `c`...). Limit requests per account, address and token; weight costly queries more heavily; cap page size and page depth; and require login for deep or bulk results.

**Result leakage.** The most common flaw is applying access control *after* the search. If the engine finds 40 documents and the application then hides the 38 the user may not see, the response is correct but the page still shows "40 results", facet counts, spell-check suggestions or autocomplete entries that reveal that the hidden documents exist. The fix is to put the user's permissions *inside* the query as a filter, so counts and suggestions only describe what that user may see. Related traps: caches shared between users, error messages that echo the query's internals, and indexes that include fields the user may not read.

## How to test a threat model

- **Trace to tests.** For each mitigated threat, point to the automated test or control that verifies it.
- **Compare diagram and reality.** Generate the route list, the list of cloud resources and the network rules, and reconcile them with the picture.
- **Run abuse cases** against a test environment as part of regular testing.
- **Invite a fresh pair of eyes** — someone outside the team — to walk the diagram and ask the STRIDE questions again.
- **Use external findings as a mirror**: each penetration-test or bug-bounty report either confirms a threat you listed or reveals a gap in the model.

## Pitfalls

- **Modelling after launch**, when only cheap fixes are still affordable.
- **Leaving it to a security team alone.** The people who know the system best must be in the room.
- **Diagrams without trust boundaries**, or with a single boundary around everything.
- **Treating STRIDE as a classification exercise.** The category matters less than finding the threat and deciding what to do.
- **Skipping "boring" elements**: logs, backups, build pipelines, admin tools, support processes.
- **Ignoring people and process**: password resets handled by support staff over the phone are part of the system.
- **Unrecorded acceptance** of risks.
- **Never updating** the model.
- **False precision**: debating whether a likelihood is 3 or 4 instead of fixing the thing.

## Summary

- Threat modelling is a structured design review answering four questions: what are we building, what can go wrong, what will we do about it, and did we do well?
- A data-flow diagram of external entities, processes, data stores, flows and trust boundaries makes the system visible.
- STRIDE supplies six categories — spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege — each violating one security property; apply them per element.
- Rank threats by likelihood × impact and choose to mitigate, eliminate, transfer or explicitly accept each.
- Turn mitigations into tickets and tests, and keep the model current.
- Architectural habits — small attack surface, least privilege, central controls, secure defaults, segmentation, data minimisation — prevent whole categories of threat.

## Glossary

- **Threat modelling** — systematically identifying and responding to potential threats to a system's design.
- **Data-flow diagram (DFD)** — a picture of external entities, processes, data stores and the flows between them.
- **External entity / process / data store / data flow** — the four DFD element types.
- **Trust boundary** — a line across which the level of trust changes.
- **STRIDE** — spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege.
- **Spoofing** — pretending to be another identity. **Tampering** — unauthorised modification.
- **Repudiation** — being able to deny having done something. **Non-repudiation** — being able to prove it.
- **Elevation of privilege** — gaining rights beyond those granted.
- **STRIDE-per-element** — applying only the relevant categories to each element type.
- **Risk rating** — scoring a threat by likelihood and impact.
- **Mitigate / eliminate / transfer / accept** — the four risk responses.
- **Abuse case** — a description of how a feature could be misused.
- **Attack tree** — a diagram branching from an attacker's goal into ways of achieving it.
- **Zero trust** — verifying every request regardless of its network origin.
- **Data minimisation** — collecting and keeping only the data that is needed.
- **PII** — Personally identifiable information: data that identifies a real person alone or in combination
- **Data classification** — Sorting data into levels such as public, internal, confidential and restricted, each with handling rules
- **Tokenisation** — Replacing a sensitive value with a meaningless token and keeping the real value in a protected vault
- **PCI DSS** — The security standard for organisations that store, process or transmit payment-card data
- **Search injection** — Altering a search query's meaning by supplying text that the search engine treats as syntax
- **Result leakage** — Revealing hidden data through search counts, facets or suggestions even when the results list is filtered

```quiz
[
  {"q": "What are the four questions of threat modelling?",
   "options": ["Who, what, when, where", "What are we working on, what can go wrong, what are we going to do about it, did we do a good job", "Scan, patch, test, deploy", "Plan, build, run, retire"], "answer": 1,
   "explain": "These four questions underlie every threat-modelling method and give the exercise its structure."},
  {"q": "In STRIDE, which security property does 'Tampering' violate?",
   "options": ["Confidentiality", "Integrity", "Availability", "Authentication"], "answer": 1,
   "explain": "Tampering is unauthorised modification of data or code, which is a loss of integrity."},
  {"q": "A customer changes an order ID in the URL and views another customer's invoice. Which STRIDE category fits best?",
   "options": ["Spoofing", "Repudiation", "Information disclosure", "Denial of service"], "answer": 2,
   "explain": "Data was exposed to someone not authorised to see it. (The same flaw may also allow tampering if writes are possible.)"},
  {"q": "An administrator issues refunds and the system keeps no record of who did so. Which category is this?",
   "options": ["Repudiation", "Tampering", "Elevation of privilege", "Spoofing"], "answer": 0,
   "explain": "Without an audit trail the action can be denied. The control is logging that attributes actions to identities."},
  {"q": "In STRIDE-per-element, which categories apply to a data flow?",
   "options": ["All six", "Spoofing and repudiation", "Tampering, information disclosure and denial of service", "Elevation of privilege only"], "answer": 2,
   "explain": "Data in motion can be altered, observed or interrupted. Spoofing and privilege apply to the endpoints, not the flow."},
  {"q": "A team decides to stop storing card numbers and use the payment provider's hosted checkout. Which risk responses are these?",
   "options": ["Accept and ignore", "Eliminate and transfer", "Mitigate only", "Detect and respond"], "answer": 1,
   "explain": "Removing the data eliminates the threat to it; relying on the provider transfers part of the risk."},
  {"q": "When is 'accepting' a risk legitimate?",
   "options": ["Whenever fixing it is inconvenient", "When it is an explicit, recorded decision by someone with authority to accept it", "Never", "When nobody has noticed it"], "answer": 1,
   "explain": "Acceptance is a conscious choice with an owner. An unrecorded, undiscussed risk is merely ignored."},
  {"q": "Why give each service its own narrowly scoped database account?",
   "options": ["It makes queries faster", "A flaw in one service then reaches only that service's data and rights (least privilege)", "Databases require it", "It replaces the need for validation"], "answer": 1,
   "explain": "Least privilege limits the blast radius of any single compromise."},
  {"q": "What is the most effective way to reduce a web shop's PCI DSS scope?", "options": ["Encrypt the card numbers in your own database", "Let a payment provider collect the card number so it never reaches your servers", "Hide the card form with JavaScript", "Store card numbers in log files"], "answer": 1, "explain": "Systems that never see card data are outside the scope, which removes the biggest costs."},
  {"q": "A search page filters hidden documents out of the list but shows 'About 40 results'. What is the problem?", "options": ["Nothing: the list is correct", "The count leaks that restricted documents exist", "The page is too slow", "The query is too short"], "answer": 1, "explain": "Authorisation must be part of the query itself so that counts, facets and suggestions cover only visible documents."}
]
```

> **Source:** Hoffman, *Web Application Security*, ch. 7 (weak points in application architecture), ch. 17 (securing modern web applications) and ch. 18 (secure application architecture), in original wording with original examples; STRIDE and the four-question framing come from the threat-modelling literature. OWASP Threat Modeling Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html ; OWASP Threat Modeling Process — https://owasp.org/www-community/Threat_Modeling_Process ; Threat Modeling Manifesto — https://www.threatmodelingmanifesto.org/ ; OWASP Risk Rating Methodology — https://owasp.org/www-community/OWASP_Risk_Rating_Methodology ; OWASP Top 10 A04 Insecure Design — https://owasp.org/Top10/A04_2021-Insecure_Design/
