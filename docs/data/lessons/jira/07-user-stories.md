# User stories, INVEST and acceptance criteria

> **Before this lesson:** read [Artifacts and commitments](#/lesson/jira/artifacts-commitments). You should know what the Product Backlog is and what the Definition of Done means.

## In plain words

Suppose a friend asks you to "make a website for my bakery". You could disappear for a month and build what you imagine. Or you could ask: who will use it, and what do they need to do? "A customer wants to see today's bread so they know whether to come before it sells out." "A customer wants to order a birthday cake online so they don't have to phone during work hours." Each of those sentences is small, written from the user's point of view, and says why it matters. That is a **user story**.

A user story is a short, informal description of a piece of functionality, told from the perspective of the person who wants it. It is deliberately not a full specification. It is a placeholder for a conversation between the people who need the feature and the people who will build it.

Why it matters for a job: most Jira backlogs you will meet are full of stories. As an engineer you will read them, question them, split them, estimate them and check them against their acceptance criteria. A vague story leads to wasted work; a sharp one makes the work obvious. Interviewers sometimes hand you a vague requirement and watch how you turn it into clear, testable pieces.

> [!NOTE]
> The Scrum Guide does not mention user stories. It talks about "Product Backlog items", which can take any form. User stories are the most common form, especially for user-facing features, but a backlog can also hold bugs, technical tasks, experiments and research spikes.

## The standard template

Atlassian's Agile Coach and many teams use this template:

> As a **[type of user]**, I want **[some goal]** so that **[some reason]**.

Each part has a job:

| Part | Question it answers | Example |
|---|---|---|
| As a ... | Who benefits? A specific type of user, often called a **persona** (a described, representative user) | As a returning customer |
| I want ... | What do they want to do? An action or capability, not a technical solution | I want to reorder a previous meal in one tap |
| so that ... | Why? The value or outcome | so that I can get lunch quickly during a short break |

Full example: *As a returning customer, I want to reorder a previous meal in one tap so that I can get lunch quickly during a short break.*

The "so that" is the most often skipped part and the most valuable. It tells the team what success looks like, which lets them propose a better solution than the one requested. If the reason is "get lunch quickly", perhaps saving a default address matters as much as the reorder button.

### Weak stories and how to fix them

| Weak story | Problem | Better |
|---|---|---|
| "As a user, I want a database index" | Technical solution, no user value stated | "As a customer, I want order history to load in under a second so that I can find past receipts quickly" (the index is how, not what) |
| "As a user, I want the app to be better" | Not specific, not testable | "As a first-time visitor, I want to see delivery fees before signing up so that I'm not surprised at checkout" |
| "As a developer, I want to refactor the payment module" | Valuable, but not user-facing; forcing the template hides the real reason | Write it as a technical item: "Refactor payment module to remove duplicate retry logic. Reason: two incidents last quarter came from inconsistent retries." |
| "As an admin, I want to manage users" | Far too big: create, edit, delete, roles, audit, bulk import... | Split into several stories (lesson 8) |

Not everything must be squeezed into the template. A bug report or an infrastructure task is clearer written plainly. The template is a tool for user-facing value, not a law.

## The three C's: card, conversation, confirmation

A popular way to remember what a story really is, commonly attributed to Ron Jeffries (one of the Agile Manifesto's authors), is the **three C's**:

1. **Card.** The story is short enough to fit on an index card. It is a reminder, not the whole requirement. In Jira, the "card" is the work item's summary line.
2. **Conversation.** The details come from conversations between the Product Owner, the Developers and, ideally, users. Those conversations happen during refinement and planning, and their conclusions are written down (in Jira: the description and comments).
3. **Confirmation.** The acceptance criteria let everyone confirm that the story is finished and correct.

The point of the three C's: a story is not a contract thrown over a wall. If you, as an engineer, receive a story you do not understand, the agile answer is to talk, not to guess.

## INVEST: a checklist for good stories

In 2003, Bill Wake proposed the acronym **INVEST** for the qualities of a good story. Each letter is a test you can apply in refinement.

| Letter | Quality | Plain meaning | Quick test |
|---|---|---|---|
| **I** | Independent | Can be built and delivered without waiting for another story | Could we do this one first? |
| **N** | Negotiable | Details are open for discussion; it is not a fixed contract | Is there room to choose how? |
| **V** | Valuable | Delivers value to a user or customer | Would anyone notice if it shipped? |
| **E** | Estimable | The team understands it well enough to size it | Can we give it a rough size? |
| **S** | Small | Fits comfortably in a Sprint, ideally a few days of work | Could we finish it well before the Sprint ends? |
| **T** | Testable | There is a clear way to check it is done | Can we write the acceptance criteria? |

Some tensions are worth knowing. "Independent" is an ideal: some dependency is unavoidable, and the aim is to reduce it, not eliminate it. "Small" and "Valuable" pull against each other: the smallest pieces of work are often technical layers with no value on their own. Lesson 8 shows how to split stories so that each small piece is still valuable (a thin vertical slice).

Wake's same article proposed **SMART** for the smaller tasks a story is broken into: Specific, Measurable, Achievable, Relevant and Time-boxed. You will meet INVEST far more often.

> [!TIP]
> If a story fails "Estimable" (the team says "we have no idea how long this takes"), the usual fix is a **spike**: a short, time-boxed research item whose output is knowledge (for example "Find out whether the payment provider supports partial refunds; max 1 day"). After the spike, the real story becomes estimable.

## Acceptance criteria

**Acceptance criteria** are the conditions a specific story must satisfy to be accepted by the Product Owner. They make a story testable and settle arguments about scope before work starts.

Two common formats:

**1. A checklist of rules**

Story: *As a customer, I want to apply a promo code at checkout so that I get the advertised discount.*

- A valid, unexpired code reduces the order total by its stated amount or percentage.
- An expired or unknown code shows the message "This code is not valid" and does not change the total.
- Only one code can be applied per order.
- The discount never makes the total negative.
- The applied code appears on the receipt email.

**2. Given / When / Then scenarios**

This format comes from **behaviour-driven development** (BDD), a practice of describing behaviour as examples that can become automated tests. Each scenario says the starting situation, the action and the expected outcome:

```text
Scenario: expired code is rejected
  Given a cart with a total of 40.00 SGD
  And the code "CNY2026" expired yesterday
  When the customer applies "CNY2026"
  Then the message "This code is not valid" is shown
  And the cart total is still 40.00 SGD
```

Scenarios like this can be turned directly into automated acceptance tests. The CI/CD track's lesson [Acceptance criteria and executable specifications](#/lesson/cicd/executable-specs) shows how.

### Good acceptance criteria

- **Testable**: each one can be checked as pass or fail.
- **About behaviour, not implementation**: "the code is rejected", not "add an `if` in `PromoService`".
- **Include the unhappy paths**: invalid input, limits, errors. Beginners write only the happy path.
- **Agreed before the work starts**, during refinement or planning, not discovered at the review.

### Acceptance criteria versus Definition of Done, again

Lesson 5 introduced the difference; here it is with the promo-code story:

- **Acceptance criteria (this story only):** expired codes are rejected; one code per order; total never negative.
- **Definition of Done (every story):** code reviewed, tests pass in CI, deployed to staging, monitoring added.

The story is finished only when both are met.

## User stories in Jira

In Jira, a user story is usually a work item of the type **Story** (lesson 11 covers work types). Typical usage:

- **Summary**: a short title, such as "Apply promo code at checkout". Many teams put the short form here and the full "As a..." sentence in the description.
- **Description**: the story sentence, context, links to designs, and the acceptance criteria. Some companies add a dedicated custom field for acceptance criteria.
- **Story point estimate**: the team's size estimate (lesson 9).
- **Parent**: the epic this story belongs to (lesson 8).
- **Sub-tasks**: the technical steps the Developers plan, such as "API endpoint", "UI form", "tests".
- **Comments**: the conversation part of the three C's, captured.

A practical description template that many teams paste into new stories:

```text
Story
As a <user>, I want <goal> so that <reason>.

Context
Why now, links to designs, data or customer feedback.

Acceptance criteria
1. ...
2. ...

Out of scope
Things we explicitly agreed NOT to do in this story.

Notes / open questions
```

The "Out of scope" section is underrated: it prevents the story from growing silently during the Sprint.

## Try it: a tiny story checker

Here is a small script that applies a few automatic checks to story text: does it follow the template, does the "so that" exist, does the summary contain "and" (often a sign of two stories in one), and are there acceptance criteria? Edit the stories and run it. It is a toy, not a substitute for conversation.

```python-run
import re

stories = [
    {"summary": "Reorder a previous meal",
     "text": "As a returning customer, I want to reorder a previous meal in one tap so that I get lunch quickly.",
     "criteria": ["Shows last 5 orders", "Unavailable dishes are greyed out"]},
    {"summary": "Login and profile page and settings",
     "text": "As a user, I want to log in",
     "criteria": []},
    {"summary": "Add DB index",
     "text": "Add an index on orders.customer_id",
     "criteria": ["Query plan uses the index"]},
]

pattern = re.compile(r"^As an? (.+?), I want (.+?)(?: so that (.+))?\.?$", re.IGNORECASE)

for s in stories:
    problems = []
    m = pattern.match(s["text"].strip())
    if not m:
        problems.append("not in 'As a ..., I want ... so that ...' form (fine for technical items)")
    elif not m.group(3):
        problems.append("missing 'so that': why does the user want this?")
    if re.search(r"\band\b", s["summary"], re.IGNORECASE):
        problems.append("summary contains 'and': maybe two stories")
    if not s["criteria"]:
        problems.append("no acceptance criteria: not testable yet")
    print(s["summary"])
    for p in problems or ["looks fine on these simple checks"]:
        print("   -", p)
```

The first story passes. The second has no reason, no criteria and an "and" in its summary, a classic over-stuffed story. The third is a technical task that does not fit the template; that is acceptable, but the warning prompts the team to write down *why* the index is needed.

## Scenario: refining a vague request

A Product Owner at a Singapore food-delivery start-up adds a backlog item: "Riders need better navigation." In refinement, the team asks questions:

- *Who exactly?* New riders in their first month, who get lost most.
- *What is the problem?* They miss the right entrance at large condominiums and HDB estates, and calls to customers delay delivery.
- *How will we know it helped?* Fewer "I can't find you" calls per delivery.

The team writes:

*As a new rider, I want to see the building entrance the customer marked on the map so that I can reach the right block without calling them.*

Acceptance criteria:

1. If the customer marked an entrance, the rider's map shows a pin at that point.
2. If no entrance is marked, the map shows the address pin as today.
3. The pin appears within 2 seconds of accepting the order on a mid-range phone.
4. The customer can set or change the entrance when placing the order.

Criterion 4 is clearly a separate piece of work for a different app, so the team splits it into its own story. The original vague request has become two small, testable, valuable stories. That is refinement doing its job.

## How interviewers probe this

> [!INTERVIEW]
> "Here's a requirement: 'users should be able to export their data'. How would you approach it?" Do not start designing. Ask who the users are and why they want to export (moving to a competitor? accounting? a legal right of access?). Then propose a first thin story with acceptance criteria, for example "export my last 12 months of transactions as CSV", and list the obvious follow-ups (other formats, larger ranges) as separate items. This shows you turn ambiguity into testable increments.

Other likely questions:

- "What makes a good user story?" Mention the template, INVEST, and clear acceptance criteria, with one example.
- "Who writes user stories?" Usually the Product Owner, but anyone can, and the best stories come from collaboration.
- "What's the difference between a story and a task?" A story describes user value; tasks are the technical steps to deliver it.

## Summary

- A user story is a short description of functionality from a user's perspective, a placeholder for a conversation.
- The common template is "As a [user], I want [goal] so that [reason]"; the reason is the most valuable part.
- The three C's: card, conversation, confirmation.
- INVEST (Bill Wake, 2003): Independent, Negotiable, Valuable, Estimable, Small, Testable.
- Acceptance criteria are specific, testable conditions for one story, written as a checklist or as Given/When/Then scenarios.
- In Jira, stories are usually the Story work type, with acceptance criteria in the description or a custom field.

## Glossary

- **User story** — a short description of a feature from the perspective of the person who wants it.
- **Persona** — a described, representative type of user.
- **Three C's** — card, conversation, confirmation: what a user story really consists of.
- **INVEST** — Independent, Negotiable, Valuable, Estimable, Small, Testable: qualities of a good story.
- **SMART** — Specific, Measurable, Achievable, Relevant, Time-boxed: qualities of a good task.
- **Acceptance criteria** — conditions a specific story must meet to be accepted.
- **Behaviour-driven development (BDD)** — describing behaviour as concrete examples, often in Given/When/Then form, that can become tests.
- **Given / When / Then** — a scenario format: starting situation, action, expected outcome.
- **Spike** — a short, time-boxed research item whose output is knowledge.
- **Happy path** — the normal, error-free way through a feature.
- **Unhappy path** — the error cases and edge conditions.
- **Work type** — Jira's category for a work item, such as Story, Bug or Task.

## Check yourself

```quiz
[
  {"q": "Which part of 'As a ..., I want ..., so that ...' is most often skipped but most valuable?",
   "options": ["As a", "I want", "so that", "The title"],
   "answer": 2,
   "explain": "The reason explains the value, which lets the team judge success and suggest better solutions."},
  {"q": "What do the three C's stand for?",
   "options": ["Code, commit, check", "Card, conversation, confirmation", "Customer, contract, completion", "Clarity, cost, capacity"],
   "answer": 1,
   "explain": "The story is a card reminding the team of a conversation, confirmed by acceptance criteria."},
  {"q": "In INVEST, what does the E stand for?",
   "options": ["Efficient", "Estimable", "Essential", "Executable"],
   "answer": 1,
   "explain": "Estimable: the team understands the story well enough to size it."},
  {"q": "The team cannot estimate a story because nobody knows whether the provider's API supports partial refunds. What is a common fix?",
   "options": ["Guess a large number", "Create a short, time-boxed spike to find out", "Remove the story", "Ask the Scrum Master to estimate"],
   "answer": 1,
   "explain": "A spike produces the missing knowledge so the real story becomes estimable."},
  {"q": "Which is a well-written acceptance criterion?",
   "options": ["The code is clean", "Add an if statement in PromoService", "An expired code shows 'This code is not valid' and does not change the total", "It works well"],
   "answer": 2,
   "explain": "It is specific, testable and describes behaviour rather than implementation."},
  {"q": "'Code reviewed and tests pass in CI' applies to every story. What is it?",
   "options": ["An acceptance criterion", "Part of the Definition of Done", "A user story", "A spike"],
   "answer": 1,
   "explain": "Rules that apply to every item belong to the Definition of Done."},
  {"q": "Does the Scrum Guide require Product Backlog items to be user stories?",
   "options": ["Yes", "No, items can take any form", "Only for Sprint Backlog items", "Only for bugs"],
   "answer": 1,
   "explain": "The Guide does not mention user stories; they are a popular practice."}
]
```

> **Source:** Atlassian Agile Coach, User stories, https://www.atlassian.com/agile/project-management/user-stories; Bill Wake, INVEST in Good Stories, and SMART Tasks (2003), https://xp123.com/invest-in-good-stories-and-smart-tasks/; Atlassian Agile Coach, Definition of Done, https://www.atlassian.com/agile/project-management/definition-of-done; The Scrum Guide (2020), https://scrumguides.org/scrum-guide.html
