# More "which would you choose?" answers: build versus buy, consistency versus availability, sync versus async

> **Before this lesson:** read [A decision framework](#/lesson/thinking/tradeoff-framework) for the five CRISP steps — context, deciding requirements, inventory of options, select, pivot point — which every answer here follows. The words queue, replica and cache come from [Lightweight system design](#/lesson/thinking/system-design-template).

## In plain words

Someone planning a wedding faces a run of choices that look unrelated: cook the meal themselves or hire a caterer; make every guest confirm before printing the seating plan, or print now and fix surprises on the day; phone each supplier and wait on the line, or send messages and get on with other things. None has a universally right answer. Each trades effort, money, certainty and time against one another, and a good planner decides each one by what matters most *for this wedding*.

Those three everyday choices are the three engineering choices in this lesson. **Build versus buy** is cook or hire. **Consistency versus availability** is "wait until everyone agrees" against "carry on with what we know". **Synchronous versus asynchronous** is staying on the phone against leaving a message. They are among the most frequently asked comparisons in interviews, because engineers at every level meet them constantly, often without noticing that a decision is being made.

A short table of further common comparisons closes the lesson so that you can practise the same pattern on them.

## Worked choice 1 — Build or buy?

**Build** means writing and running the thing yourselves. **Buy** covers every way of using someone else's: paying for a hosted service (often called **SaaS**, software as a service), licensing a product, or adopting **open-source** software — code published for anyone to use — which costs no licence fee but must still be run and maintained.

### What to weigh

| Question | Leans build | Leans buy |
|---|---|---|
| Is this what makes our product special? | Yes — it is our **core** advantage | No — every company needs it and nobody chooses us for it |
| How well do existing products fit? | Poorly; our needs are unusual | Well; 90 % of what we need exists |
| How fast do we need it? | We can wait months | We need it this quarter |
| What does it cost over several years? | Cheaper at our scale, counting people's time | Cheaper, counting people's time |
| How risky is it to get wrong? | Low | High: security, payments, compliance, where specialists do better |
| How locked in would we be? | — | Can we leave? Can we export our data? |
| Can we run it? | We have the skills and the on-call capacity | We do not want a new thing to operate |

Two ideas carry most of the weight.

**Total cost of ownership.** The price of building is not the weeks of writing it. It is those weeks **plus** every year of fixing bugs, applying security patches, upgrading, being woken at night, and training new colleagues — and the features that were not built because engineers were busy with this. Maintenance over a system's life commonly costs several times its initial development. A fair comparison sets *that* against the subscription price.

**Core versus context.** Spend scarce engineering time on what customers choose you for. A food-delivery company wins on delivery; it does not win by having written its own email-sending system.

### Try it

**Prompt:** *"Our product needs user sign-in with passwords, social login and two-factor authentication. Should we build it or use an identity provider?"*

<details><summary>Model answer</summary>

**Context.** I'll assume a twelve-person company building, say, a scheduling tool for clinics. No security specialists on staff.

**Deciding requirements.** Security — a mistake leaks every customer's account. Speed — we want engineers on the scheduling features. Trust — clinics will ask how we protect logins.

**Options.**

- *Build.* Full control and no per-user fee. But secure authentication is a long list of things that are easy to get subtly wrong: storing passwords safely, reset flows, protection against automated guessing, session handling, two-factor enrolment and recovery, and keeping all of it patched as attacks evolve. It is permanent work, and none of it makes our scheduling better.
- *Buy a hosted identity provider.* Days to integrate, maintained by specialists, with features such as single sign-on that large customers will later demand. Costs: a fee that grows with users; dependence on their uptime — if they are down, nobody can sign in; and migration effort if we ever leave.
- *Adopt open-source identity software and host it ourselves.* No fee and more control, but we operate and patch a security-critical system.

**Select.** Buy a hosted provider. Authentication is high-risk and not what sets us apart — the textbook case for buying.

**Risk reduction.** Keep our code's contact with the provider behind one small internal interface, so that switching later means rewriting one module. Use standard protocols instead of provider-specific features where possible. Confirm that we can export our users. Check their published reliability record and what our product does during their outage — for instance, letting already signed-in sessions continue.

**Pivot point.** If the fee becomes a major cost at very large user counts, or a regulator requires data to stay in a place the provider cannot serve, revisit self-hosting.

</details>

**The reverse case.** *"We are a logistics company. Should we buy an off-the-shelf route-planning engine?"* If routing quality is the reason customers choose you, it is core: owning it lets you improve what no competitor can copy. A sensible path is to **start by buying** to learn the problem, and build once you know exactly where the bought product limits you. "Buy now, build later, behind an interface" is often the best answer to either prompt.

> [!INTERVIEW]
> Avoid the two instinctive answers. "Build — it would be fun and we'd control it" ignores years of maintenance. "Buy — never reinvent the wheel" ignores lock-in and fit. The strong answer weighs **core versus context** and **total cost of ownership**, and adds an **exit plan**.

## Worked choice 2 — Consistency or availability?

Start from the smallest example. A shop keeps its stock count on two computers, one in each of two cities, so that if one fails the other carries on. They copy every change to each other. Then the cable between the cities is cut. A customer in each city tries to buy the last umbrella.

There are only two possible policies:

1. **Refuse** to sell while the computers cannot talk. No mistake is possible — and the shop is, in effect, closed. The system stays **consistent** and gives up **availability**.
2. **Keep selling** on each side. The shop stays open — and both customers may buy the same umbrella. The system stays **available** and gives up consistency for a while; when the cable is repaired, somebody must sort out the conflict.

No third option exists while the cable is cut. That, in plain terms, is the **CAP theorem**: when a **network partition** (a break in communication between parts of a system) occurs, a system must choose between **consistency** — every reader sees the latest data — and **availability** — every request gets an answer. Partitions cannot be ruled out, so the real choice is between the other two.

Two refinements matter in practice.

**It is not all-or-nothing.** Between "everyone always agrees" (*strong consistency*) and "they will agree eventually" (*eventual consistency*) lie useful middle levels, such as *read-your-own-writes*: you always see your own changes immediately, though others may lag.

**The trade exists even without a failure.** Making every copy agree before answering takes time. So in normal operation the same choice appears as **consistency against latency**: wait for all copies and be slower, or answer from the nearest copy and risk being slightly out of date.

### Decide per piece of data

The practical skill is not choosing one side for a whole system. It is sorting the data.

| Data | What a wrong answer costs | Choose |
|---|---|---|
| Account balance, payment | Money lost or created | Consistency — refuse if unsure |
| Stock of the last item, seat booking | Selling something twice | Consistency for the final reservation step |
| Password or permission change | A revoked user keeps access | Consistency |
| Number of likes, view counter | A number briefly off | Availability |
| Social feed, product reviews | Slightly old content | Availability |
| Shopping basket | An item reappears after removal | Availability — merge, never lose an addition |
| "Last seen online" | Nobody cares | Availability |

The test question: **"What is the worst thing that happens if two people see different answers for a few seconds?"** If the answer is "money or safety", choose consistency. If it is "someone sees 41 likes instead of 42", choose availability.

### Try it

**Prompt:** *"You are designing seat booking for a cinema chain. During a network problem between data centres, should the system keep accepting bookings?"*

<details><summary>Model answer</summary>

**Context.** Seats are unique: two people cannot sit in H7. Browsing is far more frequent than booking.

**Deciding requirement.** Never sell the same seat twice — the cost is two angry customers at the door. But a completely dead website during a network problem is also costly.

**Options.** Treat the whole system as consistent and refuse everything during a partition: safe and needlessly harsh. Treat it all as available: double bookings. Or split by operation.

**Select — split it.**

- *Browsing films, times and the seat map*: availability. Serve from the nearest copy even if slightly old. A seat shown as free that was taken a second ago is harmless, because —
- *The final "reserve this seat" step*: consistency. It goes to the single authoritative copy for that screening and succeeds only if the seat is still free there. If that copy cannot be reached, the booking is refused with a clear message.

So during the problem, customers can still look and some can book — those whose requests reach the authoritative copy — and nobody is double-booked.

**Risk reduction.** Hold a selected seat for a few minutes while the customer pays, so that they do not lose it on the payment page. Keep each screening's authoritative data in one place to make "the single copy" well defined.

**Pivot point.** If double booking were cheap to resolve — as airlines accept by overbooking — availability for bookings could be the better business choice. For numbered cinema seats it is not.

</details>

## Worked choice 3 — Synchronous or asynchronous?

A **synchronous** call waits: the caller asks, stops, and continues only when the answer arrives — like a phone call. An **asynchronous** interaction does not wait: the caller hands over the request, usually through a **queue**, and gets on with other work; the result arrives later or is collected later — like leaving a note.

### What each gives and costs

| Criterion | Synchronous | Asynchronous |
|---|---|---|
| Simplicity | Straightforward to write, follow and debug | More moving parts: queue, workers, status tracking |
| The caller learns the result | Immediately, including errors | Later; needs polling or a notification |
| If the other side is slow | The caller is slow too | The caller is unaffected |
| If the other side is down | The caller fails | Work waits in the queue and is done on recovery |
| Bursts of traffic | Hit the other side directly | Are smoothed: the queue absorbs them |
| Chains of calls | Latencies add up; one slow link stalls all | Links are decoupled |
| Consistency | The result is known before continuing | Eventual: there is a period when the work is "in progress" |
| Duplicates and ordering | Rarely a concern | Must be handled: retries cause repeats, messages can overtake each other |

### How to choose

Ask three questions about the piece of work.

1. **Does the user need the result to continue?** Checking a password, showing a price: yes → synchronous. Sending a receipt email, generating a report: no → asynchronous.
2. **How long does it take, and how reliable is whoever does it?** Milliseconds and dependable → synchronous is fine. Seconds, or an outside provider that sometimes fails → asynchronous.
3. **What happens if it fails?** If the whole action must fail with it (payment declined → no order), keep it synchronous. If it can be retried later without the user (the email will go out in a minute), make it asynchronous.

### Try it

**Prompt:** *"When a customer places an order, we must: check stock, charge the card, save the order, send a confirmation email, update the recommendation engine, and notify the warehouse. Which steps are synchronous?"*

<details><summary>Model answer</summary>

Apply the three questions to each step.

| Step | Needed to answer the customer? | Verdict |
|---|---|---|
| Check and reserve stock | Yes — we cannot confirm what we do not have | Synchronous |
| Charge the card | Yes — the customer must know whether payment worked | Synchronous, with a timeout |
| Save the order | Yes — it is the record of what was promised | Synchronous, in the same transaction as the reservation |
| Send confirmation email | No — a minute's delay is fine; the provider is sometimes slow | Asynchronous |
| Update recommendations | No — irrelevant to this order | Asynchronous |
| Notify the warehouse | No — within minutes is fine, but it must not be lost | Asynchronous, with guaranteed delivery |

**Design.** The order request does the three synchronous steps and returns "order confirmed". In the same database transaction that saves the order, it also saves a record "order placed, to be announced". A background process reads those records and publishes them to a queue; email, recommendation and warehouse workers each take the event and do their part. Writing the announcement in the same transaction as the order is the **outbox pattern**: it guarantees that an order can never be saved without its announcement, or announced without being saved — which could happen if the code saved to the database and then separately sent to the queue, and crashed in between.

**What this buys.** The customer waits only for what matters. If the email provider is down for an hour, orders continue and emails go out afterwards. A sale's burst of orders is absorbed by the queue instead of overwhelming the warehouse system.

**What it costs.** Workers must tolerate duplicates — each checks whether it has already handled that order id. There is a visible "in progress" period, so the order page should say "confirmation email on its way". And we need monitoring of queue length and of jobs that keep failing.

**Pivot point.** If the business required that an order is never accepted unless the warehouse has acknowledged it, that step would have to become synchronous — and the warehouse system's reliability would become our checkout's reliability.

</details>

> [!INTERVIEW]
> A compact rule to quote: **"Synchronous for what the user must know now; asynchronous for what must happen eventually."** Then show that you know the price of asynchrony: duplicates, ordering, and an in-between state that the user interface must explain.

## More comparisons to practise

Use the same five steps on each. The table gives the heart of the trade and the factor that usually decides.

| Choice | A gives | B gives | Usually decided by |
|---|---|---|---|
| **Cache or no cache** | Speed, lower load | Always-fresh data, simplicity | How often the data changes; how costly staleness is |
| **Scale up or scale out** | Simplicity, no code change | No ceiling, survives a machine failing | How near the single-machine limit you are |
| **REST or GraphQL** | Simple, cacheable, widely understood | Clients fetch exactly the fields they need in one request | Variety of clients and screens; team experience |
| **Polling or push** | Simplicity | Immediacy, less wasted traffic | How fresh the data must be |
| **Batch or stream processing** | Simpler, cheaper, easy to re-run | Results within seconds | Whether anyone acts on the result within minutes |
| **Normalise or denormalise** | One copy of each fact, easy updates | Fast reads | Read-to-write ratio |
| **Strict typing or dynamic typing** | Errors caught before running | Quicker to write small things | Codebase size and team size |
| **Rewrite or refactor** | A clean start | Continuous delivery, lower risk | How well the old behaviour is understood and tested — rewrites lose hidden knowledge |
| **Optimistic or pessimistic locking** | No waiting when conflicts are rare | No retries when conflicts are common | How often two writers collide |
| **Fail open or fail closed** | Service continues | Safety is preserved | Whether the protected thing is convenience or security |
| **Retry or fail fast** | Hides brief faults | Avoids piling load onto a struggling service | Whether the error is temporary and the operation idempotent |
| **Monorepo or many repositories** | Easy cross-project changes, one version of everything | Independent teams and access control | Tooling maturity and how intertwined the projects are |

Pick three, set a timer for two minutes each, and speak the answer using the template from the previous lesson: *it depends on…; here…; A gives… at the cost of…; I'd choose… because…; I'd change my mind if…*

## Common mistakes

- **A universal winner.** "Async is better." Better for what?
- **Listing pros and cons and never choosing.**
- **Ignoring people.** The team's skills and size are often the deciding factor.
- **Counting only the purchase or build price**, not years of ownership.
- **One answer for the whole system** when the right answer differs per data type or per step.
- **Forgetting the exit**: no thought for how to reverse the decision.

## Summary

- Build or buy: weigh core versus context, fit, speed, total cost of ownership, risk and lock-in. Buy what is not your advantage; put it behind an interface; keep an exit.
- Consistency or availability: during a partition you must pick one. Decide per piece of data by asking what the worst result of a brief disagreement is. Money, unique items and permissions need consistency; counters and feeds do not.
- Synchronous or asynchronous: wait for what the user must know now; queue what must happen eventually. Asynchrony buys resilience and smoothness and costs duplicates, ordering concerns and an in-progress state.
- The same five-step pattern handles every other comparison.

## Glossary

| Term | Meaning |
|---|---|
| Build versus buy | Whether to create software in-house or use someone else's |
| SaaS | Software as a service: a product hosted and run by its vendor |
| Open source | Software whose code is published for anyone to use and modify |
| Total cost of ownership | The full cost of something over its life, including maintenance and operation |
| Core versus context | Work that differentiates a company versus work every company must do |
| Vendor lock-in | Difficulty of leaving a supplier once you depend on it |
| Network partition | A break in communication between parts of a system |
| CAP theorem | During a partition a system must give up either consistency or availability |
| Strong consistency | Every read reflects the latest write |
| Eventual consistency | Copies may differ briefly but converge |
| Synchronous | The caller waits for the result before continuing |
| Asynchronous | The caller continues; the work completes later |
| Decoupling | Arranging parts so that one's slowness or failure does not directly affect another |
| Outbox pattern | Saving a message in the same transaction as the data change, to be published afterwards |

## Check yourself

```quiz
[
  {"q": "Which cost is most often forgotten when estimating 'build'?",
   "options": ["The price of keyboards", "Years of maintenance, patching, on-call and upgrades after the first version", "The colour scheme", "Meeting rooms"],
   "answer": 1,
   "explain": "Total cost of ownership is dominated by what happens after the initial build."},
  {"q": "A delivery company is deciding whether to write its own email-sending system. What does 'core versus context' suggest?",
   "options": ["Build, because email is important", "Buy, because email does not differentiate the company", "Build, because it is fun", "Neither; avoid email"],
   "answer": 1,
   "explain": "Engineering time should go to what customers choose the company for; commodity needs are bought."},
  {"q": "The link between two data centres fails. What does the CAP theorem say about a system spanning both?",
   "options": ["It can remain fully consistent and fully available", "It must give up either consistency or availability until the link returns", "It must shut down permanently", "Nothing"],
   "answer": 1,
   "explain": "With copies unable to communicate, the system either refuses some requests or risks disagreeing answers."},
  {"q": "Which data most needs consistency over availability?",
   "options": ["A like counter", "The reservation of the last seat", "A 'last seen' indicator", "A list of trending topics"],
   "answer": 1,
   "explain": "Selling a unique item twice has a real cost; briefly wrong counters do not."},
  {"q": "Which step of placing an order should be synchronous?",
   "options": ["Sending the confirmation email", "Charging the customer's card", "Updating recommendations", "Notifying the marketing system"],
   "answer": 1,
   "explain": "The customer must know whether payment succeeded before the order can be confirmed."},
  {"q": "What new problems does asynchronous processing introduce?",
   "options": ["None", "Possible duplicates, out-of-order messages and an in-progress state to explain to users", "Slower typing", "Larger screens"],
   "answer": 1,
   "explain": "Queues retry, so handlers must be idempotent, and results are no longer immediate."},
  {"q": "What does the outbox pattern guarantee?",
   "options": ["Emails are never sent", "A data change and its announcement are saved together, so neither can exist without the other", "Queues are unnecessary", "All calls become synchronous"],
   "answer": 1,
   "explain": "Writing the message in the same transaction avoids saving the order and then crashing before publishing the event."}
]
```

> **Source:** Martin Fowler, "Microservice Trade-Offs" for distribution and eventual consistency (https://martinfowler.com/articles/microservice-trade-offs.html) and "What do you mean by Event-Driven?" (https://martinfowler.com/articles/201701-event-driven.html); the availability-versus-consistency section of Donne Martin's System Design Primer (https://github.com/donnemartin/system-design-primer); Google SRE Book, "Embracing Risk" (https://sre.google/sre-book/embracing-risk/); DORA capability guidance on loosely coupled teams (https://dora.dev/capabilities/loosely-coupled-teams/). Scenarios and wording are original.
