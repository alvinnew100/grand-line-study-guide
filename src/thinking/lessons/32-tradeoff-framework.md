# "Which would you choose?" — a decision framework, with monolith versus microservices and SQL versus NoSQL

> **Before this lesson:** [Data modelling questions](#/lesson/thinking/data-modelling-basics) explains relational and NoSQL databases, and [Lightweight system design: a repeatable template](#/lesson/thinking/system-design-template) explains servers, queues and scaling. Both are assumed for the two worked choices.

## In plain words

Should you rent a flat or buy a house? Anyone who answers "buy, always" or "rent, always" has not thought about it. The honest answer starts with questions: how long will you stay, how steady is your income, how much do you value freedom to move? Then it weighs what each option gives and takes away — buying builds something you own but ties you down and makes you responsible for the roof — and ends with a choice *for this person*, along with what would change the answer.

Engineering is full of such forks: one big program or many small ones, one kind of database or another, build it or buy it. A **trade-off** is a choice in which getting more of one good thing means accepting less of another. Interviewers ask "which would you choose?" to see whether you understand that there is no free option. A candidate who names a winner with no conditions sounds junior; a candidate who says "it depends" and stops sounds evasive. The skill is to say **what it depends on, and then decide.**

## The framework: CRISP

Five steps. The name is only a memory aid.

| Step | Do | Example sentence |
|---|---|---|
| **C — Context** | Ask or state the situation: team size, scale, stage, deadline, skills | "Is this a five-person start-up or a two-hundred-person company?" |
| **R — Requirements that decide** | Pick the two or three qualities that matter most here | "What matters is shipping quickly and keeping operations simple." |
| **I — Inventory of options** | Describe each option fairly: what it gives, what it costs | "A monolith gives X and costs Y; microservices give P and cost Q." |
| **S — Select** | Choose for this context and say why | "For this team I'd choose the monolith, because…" |
| **P — Pivot point** | Say what would change your mind, and how you would reduce the risk of being wrong | "If the team passes about fifty people, I'd revisit." |

Two habits make answers stronger still.

**Compare on named criteria.** Vague praise ("more scalable", "cleaner") is not comparison. Pick criteria and score each option against them, as in a table.

**Ask how reversible the choice is.** A decision that is cheap to undo can be made quickly and tried. One that is expensive to undo — a database, a programming language, a public API — deserves more care and, where possible, a design that keeps the door open.

```mermaid
flowchart LR
    C[Context] --> R[Deciding requirements]
    R --> I[Options: gains and costs]
    I --> S[Select for this context]
    S --> P[Pivot point and risk reduction]
```

### The qualities you trade between

Most engineering trade-offs are exchanges among a short list.

| Quality | Meaning |
|---|---|
| **Delivery speed** | How quickly the team can build and change things |
| **Operational simplicity** | How little effort it takes to run, monitor and fix |
| **Performance** | Latency and throughput |
| **Scalability** | Ability to handle growth in users, data or team size |
| **Reliability** | Staying correct and available when parts fail |
| **Consistency** | Everyone seeing the same, correct data |
| **Cost** | Money for machines, licences and people's time |
| **Flexibility** | Ease of changing direction later |
| **Security and compliance** | Meeting obligations to protect data |

Typical pairs that pull against each other: delivery speed against flexibility later; consistency against availability; performance against cost; simplicity against scalability.

## Worked choice 1 — Monolith or microservices?

First the terms, from the ground up.

A **monolith** is an application built and deployed as one unit. All the features — sign-up, catalogue, checkout, emails — live in one codebase and run as one program, usually with one database. Picture a single large workshop where every craftsperson works under one roof.

**Microservices** split the application into many small programs, each responsible for one area, each deployed separately, each owning its own data, talking to one another over the network. Picture a street of specialist workshops that send each other parts by courier.

A third option is often the best answer and is worth naming: a **modular monolith** — one deployable program whose insides are divided into well-separated modules with clear boundaries.

### What each gives and costs

| Criterion | Monolith | Microservices |
|---|---|---|
| Getting started | Fast: one project, one deploy | Slow: much groundwork before the first feature |
| Changing something that crosses areas | One change, one deploy | Several services, coordinated releases |
| Calls between parts | In-process function calls: fast, cannot fail on their own | Network calls: slower, can fail or time out |
| Data consistency | One database, ordinary transactions | Each service has its own data; changes across services are eventually consistent |
| Deploying | Everything together; a bug anywhere can block a release | Each service independently |
| Team independence | Many teams in one codebase get in each other's way | Teams own services and move independently |
| Scaling | The whole application scales together | Scale only the busy part |
| Failure isolation | A memory leak in one feature can take down all | A failing service need not take the others down — if the callers cope |
| Running it | One thing to monitor | Dozens: needs automation, tracing, on-call maturity |
| Understanding the whole | Read one codebase | Follow requests across many services |
| Technology choice | One stack | Each service may differ |

Martin Fowler's well-known summary lists the benefits of microservices as strong module boundaries, independent deployment and technology diversity, and the costs as distribution, eventual consistency and operational complexity. The right-hand column buys *independence* and pays in *complexity*.

The deepest point: **microservices mainly solve an organisational problem** — many teams needing to work without blocking one another. They are rarely the answer to a technical problem that a small team has.

### Try it

**Prompt:** *"We are a start-up of six engineers building an online marketplace. Should we use microservices?"* Answer with the five steps, then open.

<details><summary>Model answer</summary>

**Context.** Six engineers, a new product, requirements still changing weekly, no dedicated operations people, and the main risk is not finding customers before the money runs out.

**Deciding requirements.** Delivery speed and the ability to change direction. Operational simplicity, because nobody is employed to run infrastructure. Scale is not yet a concern: the traffic of an early start-up fits on one modest server.

**Options.**

- *Microservices* would give independent deployment and scaling that six people do not need, and would cost a great deal: service-to-service calls to secure and monitor, distributed data, a deployment pipeline per service, and debugging across the network. Worse, service boundaries drawn now — before we understand the business — will probably be drawn in the wrong places, and moving a boundary between services is far harder than moving one inside a single codebase.
- *A monolith* is the fastest way to build and change. Its dangers — tangled code, slow builds, teams colliding — are problems of size that we do not have.
- *A modular monolith* keeps the monolith's speed and guards against the tangle: separate modules for listings, orders and payments, each with a clear interface, and no reaching into another module's tables.

**Select.** A modular monolith with one database. One deployment, ordinary transactions, one thing to monitor.

**Pivot point.** I would revisit when one of these becomes true: the team grows past a few dozen and release coordination becomes the bottleneck; one part has a very different load or reliability need from the rest (for example image processing); or one part needs a different technology. Then extract *that one* module as a service — which is feasible because its boundary already exists.

**Risk reduction.** Enforce module boundaries from the start with code review and tooling; keep slow jobs on a queue; automate deployment so that releases are routine.

</details>

**The reverse prompt.** *"We have three hundred engineers on one monolith. Deployments take a day and are often rolled back. Should we move to microservices?"*

<details><summary>Model answer</summary>

**Context.** Large organisation; the pain is coordination — many teams queue to release one unit, and one team's bug blocks everyone.

**Deciding requirements.** Independent delivery per team, and failure isolation. The company can afford platform engineers.

**Options.**

- *Stay and improve*: faster tests, a merge queue, feature flags, clearer module ownership. Cheaper, and it may be enough — some very large companies run monoliths this way.
- *Split everything into services*: maximal independence, and a multi-year project with high risk of producing a "distributed monolith" — services so entangled that they must still be released together, with all the cost and none of the benefit.
- *Extract gradually*: carve off the parts whose separation pays most, one at a time, routing traffic to the new service while the old code still exists. This incremental approach is known as the **strangler fig** pattern, after a plant that grows around a tree and slowly replaces it.

**Select.** Improve the monolith's delivery pipeline now, because that helps in every scenario, and extract gradually, starting with a module that has a clear boundary, a single owning team and a distinct load profile. Measure deploy frequency and failure rate before and after the first extraction to check that it is worth continuing.

**Pivot point.** If the first two extractions do not improve those numbers, stop: the bottleneck is the pipeline or the organisation, not the architecture.

**Risks to name.** Shared database tables are the hardest part: each service must come to own its data. Invest first in the platform — deployment, monitoring, tracing — or the new services will be harder to run than the monolith was.

</details>

> [!INTERVIEW]
> The sentence that shows you understand this topic: **"Microservices trade simplicity for independence, so they pay off when coordination between many teams is the bottleneck — not before."** Follow it with the modular monolith as the starting point and gradual extraction as the path.

## Worked choice 2 — SQL or NoSQL?

The data-modelling lesson described the families. Here is the choice made with the framework.

### The criteria that decide

| Question | Leans relational (SQL) | Leans NoSQL |
|---|---|---|
| Do several records have to change together or not at all? | Yes: orders with stock, transfers of money | No: each item stands alone |
| How do you read the data? | Many different ways, including questions not yet thought of | By one known key, or a few fixed patterns |
| How regular is the shape? | Regular, with rules worth enforcing | Varies item to item, or changes quickly |
| How big, and how fast are writes? | Fits one strong machine with replicas | Beyond one machine: must scale out |
| Are the relationships themselves the question? | Joins across a few tables | Many-hop connections → a graph database |
| What does the team know? | SQL is widely known | Requires learning its modelling style |

### Try it

**Prompt A:** *"We are building an online shop: products, customers, orders, payments. SQL or NoSQL?"*

<details><summary>Model answer</summary>

**Context.** A typical shop; assume thousands of orders a day to begin with.

**Deciding requirements.** Correctness of orders and money; flexible reporting for the business; modest scale.

**Options.** A relational database gives transactions (reduce stock and create the order together), constraints (no negative stock, no order without a customer) and ad-hoc queries (sales by region last month) for free. A document store would make varied product attributes easy to keep, and would make "order plus stock" consistency our code's responsibility.

**Select.** Relational for customers, orders, payments and stock. Varied product attributes can sit in a flexible column within the same database — most relational systems support a JSON column — so I do not need a second database for that alone.

**Pivot point.** If the catalogue grows to many millions of products with heavy search and filtering, add a search index beside the database. If order volume ever exceeds what one primary can write, shard by customer or move the highest-volume, simplest data — for instance the browsing history — to a store built for scale.

**Trade-off stated.** I give up effortless horizontal scaling, which I do not need, in exchange for correctness guarantees, which I need from day one.

</details>

**Prompt B:** *"We collect temperature readings from two million sensors, one reading per sensor every ten seconds. Where do we store them?"*

<details><summary>Model answer</summary>

**Context and numbers.** 200,000 writes per second; about 17 billion rows per day. Readings are never updated. Queries are "readings for sensor X between two times" and aggregates over time.

**Deciding requirements.** Very high, steady write rate; cheap storage at great volume; reads by sensor and time range. No transactions across sensors. Losing a single reading is tolerable.

**Options.** One relational server cannot absorb that write rate or volume without substantial partitioning work. A wide-column or purpose-built time-series store, partitioned by sensor (and a time bucket such as the day) and sorted by time, is designed for exactly this shape: appends are cheap, each query touches one partition, and capacity grows by adding machines.

**Select.** A time-series or wide-column store for readings. The *list of sensors* — owner, location, model — is small, relational in nature and rarely changes, so it stays in a relational database. Two stores, each used for what it is good at.

**Pivot point.** If analysts need free-form questions across all sensors, copy the data periodically into an analytics warehouse instead of forcing the operational store to answer them.

**Trade-off stated.** I give up joins and ad-hoc queries on the raw readings, and design the table around the two queries I know.

</details>

**Prompt C:** *"Where should we keep users' login sessions?"*

<details><summary>Model answer</summary>

A session is looked up by one key (the session id) on every request, is small, expires, and losing one merely forces a user to sign in again. That is the textbook key-value case: an in-memory key-value store with expiry times gives sub-millisecond reads and automatic clean-up. Putting sessions in the main relational database would work at small scale and adds read load for no benefit. **Pivot:** if sessions must survive a restart without logging everyone out, turn on persistence or replication in that store.

</details>

### Statements to avoid

- "NoSQL is faster." Faster at what? Key lookups at scale, perhaps; flexible queries, no.
- "SQL does not scale." Relational databases serve very large systems, with replicas, partitioning and sharding.
- "NoSQL has no schema." The structure still exists — in your code, where the database cannot check it.
- "We might be huge one day, so NoSQL." Design for the next order of magnitude, not for an imagined final one; migrating later, with real data about how the system is used, is normal.

## Speaking the answer

A compact spoken template, about ninety seconds:

> "It depends on **[two factors]**. In this case **[context]**, so what matters most is **[requirements]**. **[Option A]** gives **[gain]** at the cost of **[cost]**; **[option B]** gives **[gain]** at the cost of **[cost]**. Here I'd choose **[A]**, because **[reason tied to the requirements]**. I'd change my mind if **[pivot]**, and to limit the risk I'd **[mitigation]**."

Practise it on small questions too — tabs or spaces is a joke, but "library X or library Y", "cache here or not", "retry or fail fast" are daily decisions with the same shape.

## Summary

- A trade-off question wants the conditions, a decision, and what would change it.
- CRISP: context, deciding requirements, inventory of options with gains and costs, select, pivot point.
- Compare on named criteria and consider how reversible the choice is.
- Monolith versus microservices: microservices buy team independence and isolation with distribution, eventual consistency and operational load. Start with a modular monolith; extract gradually when coordination becomes the bottleneck.
- SQL versus NoSQL: transactions, enforced rules and flexible queries versus scale-out, flexible shape and key-based access. Choose per kind of data; mixing is normal.

## Glossary

| Term | Meaning |
|---|---|
| Trade-off | A choice where gaining one benefit means giving up some of another |
| Criterion | A named quality on which options are compared |
| Reversibility | How cheaply a decision can be undone |
| Monolith | An application built and deployed as a single unit |
| Microservices | An application split into small, separately deployed services, each owning its data |
| Modular monolith | One deployable application divided internally into well-separated modules |
| Distributed monolith | Services so interdependent that they must be changed and released together |
| Strangler fig pattern | Replacing a system gradually by routing pieces of it to new components |
| Throughput | The amount of work completed per unit of time |
| Operational complexity | The effort needed to deploy, monitor and repair a system |
| Time-series store | A database specialised for timestamped measurements |
| Pivot point | The condition under which you would revise a decision |

## Check yourself

```quiz
[
  {"q": "What is the weakness of answering 'it depends' and stopping?",
   "options": ["It is impolite", "It names no factors and makes no decision", "It is too long", "It is always wrong"],
   "answer": 1,
   "explain": "The value lies in saying what it depends on and then choosing for the given context."},
  {"q": "According to the lesson, what do microservices mainly buy?",
   "options": ["Faster function calls", "Independence between teams and isolation of failures", "Simpler debugging", "Lower operating effort"],
   "answer": 1,
   "explain": "They let teams deploy and scale separately, at the price of distribution and operational complexity."},
  {"q": "Why is drawing service boundaries early risky for a new product?",
   "options": ["Services cannot be renamed", "The business is not yet understood, so boundaries are likely wrong and are expensive to move later", "It uses too little memory", "It prevents testing"],
   "answer": 1,
   "explain": "Moving a boundary between services means changing interfaces, data ownership and deployments; inside one codebase it is a refactoring."},
  {"q": "What is a modular monolith?",
   "options": ["Many services sharing one database", "One deployable application with well-separated internal modules", "A monolith with no tests", "A service with one function"],
   "answer": 1,
   "explain": "It keeps single deployment and ordinary transactions while preparing clean seams for later extraction."},
  {"q": "An online shop must reduce stock and record an order together or not at all. Which requirement is this, and what does it favour?",
   "options": ["Flexible shape; document store", "A multi-record transaction; relational database", "High write volume; wide-column store", "Many-hop relationships; graph database"],
   "answer": 1,
   "explain": "Atomic changes across records with enforced rules are the central strength of relational databases."},
  {"q": "Two million sensors each write a reading every ten seconds; queries are by sensor and time range. What fits best?",
   "options": ["A single relational table with no partitioning", "A time-series or wide-column store partitioned by sensor and sorted by time", "A graph database", "Browser local storage"],
   "answer": 1,
   "explain": "The workload is append-only, enormous and read by key and time — the shape those stores are built for."},
  {"q": "What is the purpose of stating a pivot point?",
   "options": ["To avoid deciding", "To show which change in circumstances would alter the decision", "To lengthen the answer", "To blame someone later"],
   "answer": 1,
   "explain": "It shows that the choice is tied to conditions and that you know when to revisit it."}
]
```

> **Source:** Martin Fowler, "Microservice Trade-Offs" (https://martinfowler.com/articles/microservice-trade-offs.html), "Monolith First" (https://martinfowler.com/bliki/MonolithFirst.html), "Strangler Fig" (https://martinfowler.com/bliki/StranglerFigApplication.html) and "NoSQL" (https://martinfowler.com/nosql.html); SQL-or-NoSQL discussion in Donne Martin's System Design Primer (https://github.com/donnemartin/system-design-primer). The CRISP framing, examples and wording are original.
