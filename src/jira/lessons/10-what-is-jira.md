# What Jira is: sites, spaces, keys and the new names

> **Before this lesson:** read [Scrum theory](#/lesson/jira/scrum-theory) and [Kanban](#/lesson/jira/kanban-flow). You should know what a backlog, a sprint and a board are as ideas; this lesson shows where they live in a real tool.

## In plain words

A team without a shared tracker keeps its work in many places: an email thread for one bug, a spreadsheet for the feature list, sticky notes for this week, a chat message for the urgent fix. Nobody can answer "what is everyone working on, and what is blocked?" without asking around.

**Jira** is a product from the company Atlassian that gives a team one place to record and track its work. Each piece of work, a bug, a feature, a task, becomes a **work item** with a unique key like `SHOP-123`. Work items move through stages on a **board**, are planned into **sprints**, are searched with a query language called **JQL**, and feed charts and reports. Jira also connects to code tools, so a commit or pull request can show up on the work item it relates to.

Why it matters for a job: Jira is the most widely used work tracker in software teams, and it appears constantly in job postings in Singapore and at large tech companies, sometimes alongside alternatives such as Linear, Azure Boards or GitHub Projects. On your first day you will be given access to a Jira site, assigned work items, and expected to move them along, link your branches to them and find things with search. The ideas in this track transfer to other trackers too.

## The words have changed recently

Before going further, a warning that will save you confusion. In 2025 Atlassian began renaming core terms in **Jira Cloud** (the version Atlassian hosts for you):

| Older term (still very common) | Newer term in Jira Cloud |
|---|---|
| Issue | **Work item** |
| Issue type | **Work type** |
| Project | **Space** |
| Automation rule | **Flow** (in newer automation docs) |
| Automation component | **Step** (in newer automation docs) |

What we know from Atlassian's own announcements and documentation:

- The change from "issue" to "work item" was announced on **6 February 2025**, with the rollout beginning in **March 2025**. Atlassian stated that existing **APIs keep the word "issue"** (for example `IssueTypes`) to avoid breaking integrations.
- Jira Cloud documentation now also says **space** where it used to say **project**. The JQL documentation shows newer forms such as `space = ...` but also notes that the new terms may not work yet everywhere. The old forms such as `project = ...` and `issue = ...` keep working.
- **Jira Data Center** (the self-hosted version) documentation still uses "issue" and "project".

In this track we use the new words in explanations, often with the old word in brackets, and we teach the **old JQL field names** (`project`, `issue`, `issuetype`) as the safe forms, because they work on every Jira version you are likely to meet. In interviews and at work, both sets of words are understood; most engineers still say "ticket" or "issue" in conversation.

> [!WARNING]
> Do not be thrown when a colleague says "raise a ticket in the PAY project" and your screen says "create a work item in the PAY space". It is the same thing.

## Sites, products and hosting

A **site** is your organisation's Jira installation, usually reached at an address such as `yourcompany.atlassian.net`. Everything in this track happens inside a site. One site can contain many spaces, and many teams.

Atlassian sells several related products that often share a site:

- **Jira**: work tracking for software and business teams. This track is about it.
- **Jira Service Management** (JSM): help-desk and IT service management built on the same work items, with a customer-facing portal and queues (lesson 25). Atlassian now sells it as part of its "Service Collection".
- **Confluence**: a wiki for documents such as specs, meeting notes and runbooks, which links nicely to Jira.

Hosting options:

- **Jira Cloud**: hosted by Atlassian, updated continuously. Most new teams use this. Features and names change over time, which is why documentation and screenshots online often disagree.
- **Jira Data Center**: installed on the organisation's own servers. Common in banks and government-linked organisations with strict data rules. It changes more slowly and keeps the older terms.

## Spaces and keys

A **space** (formerly a project) is a container for work items, usually belonging to one team or one product. A space has:

- a **name**, such as "Shop Checkout";
- a **space key**, a short code such as `SHOP`;
- its own configuration: work types, workflows, boards, permissions (lessons 11 to 13).

Atlassian's documentation describes the space key as a series of alphanumeric characters, at least 2 characters long, starting with an uppercase letter. Jira suggests one based on the name when the space is created, and admins can change it later.

Every work item gets a **work item key** (issue key) made of the space key, a hyphen, and a sequential number:

```text
SHOP-1     the first work item in space SHOP
SHOP-2     the second
SHOP-1042  the one thousand and forty-second
```

Keys are how everyone refers to work. They appear on board cards, in search results, in links between items, and in the work item's URL. They are also how code tools connect to Jira: put `SHOP-1042` in a branch name, commit message or pull-request title and Jira can link them (lesson 24). Smart commits, a feature that lets commit messages act on Jira, only recognise keys in the default format of two or more uppercase letters, a hyphen and a number.

> [!TIP]
> Keys are case-sensitive in practice for developer tools: `shop-1042` in a branch name will not be recognised. Atlassian's guidance is to use the uppercase key. The problem [Extract work item keys](#/problem/jira-issue-keys) asks you to find keys in branch names and commit messages the way these integrations do.

## Work items

A **work item** (issue) is Atlassian's basic building block. It represents one piece of work: a bug, a story, a task, or in non-software teams something like a leave request. Each work item has:

- a **key** and a **summary** (a one-line title);
- a **work type**, such as Story, Bug, Task, Epic or Sub-task;
- a **status**, such as To Do, In Progress or Done, controlled by a **workflow**;
- **fields** such as assignee, reporter, priority, labels, components, fix version, sprint and story points;
- a **description**, **comments**, **attachments** and **links** to other work items;
- a **history** of every change, who made it and when.

Lesson 11 goes through the data model in detail.

## A tour of the main screens

Jira's layout changes over time, but the main views stay recognisable:

| View | What it shows | Who uses it most |
|---|---|---|
| **Your work** / home | Items assigned to you, recently viewed, starred spaces | Everyone, every morning |
| **Board** | Cards in columns by status for the current sprint or continuous flow | Developers during the Daily Scrum |
| **Backlog** (Scrum) | Ordered list of items not yet in a sprint, plus upcoming sprints | Product Owner, team in refinement and planning |
| **List** | Spreadsheet-like table of work items | Anyone doing bulk edits or triage |
| **Timeline** | Epics as bars over time with their children | Product Owners, managers |
| **Work item view** | All details of one item, its comments, history, linked code | Everyone |
| **Search / filters** | JQL search results, saved filters | Everyone; power users live here |
| **Dashboards** | Gadgets showing charts and filter results | Leads, managers, the team on a TV screen |
| **Reports** | Burndown, velocity, cumulative flow and others | Scrum Masters, leads, retrospectives |

You will meet each of these in later lessons.

## How an engineer actually uses Jira: one day

To make this concrete, here is a realistic day for Farah, a backend engineer on the `SHOP` space at a Singapore online retailer.

1. **09:00.** She opens *Your work* and sees `SHOP-1042` "Apply promo code at checkout" assigned to her, status In Progress.
2. **09:45, Daily Scrum.** The team walks the board. Farah says she will finish the API today and needs a review this afternoon.
3. **10:00.** She creates a branch named `SHOP-1042-promo-code-api`. Because the key is in the branch name, the branch appears in the *Development* panel of the work item.
4. **13:00.** She commits with the message `SHOP-1042 validate expiry dates`. The commit appears on the work item too.
5. **15:00.** She opens a pull request titled `SHOP-1042 Apply promo code API`, then drags the card from In Progress to Code Review.
6. **15:30.** A teammate finds an edge case. Farah creates a linked bug `SHOP-1050` "Promo code accepted on empty cart" with a link type "relates to".
7. **17:00.** Before leaving, she runs a saved search, `project = SHOP AND assignee = currentUser() AND statusCategory != Done`, to check nothing else is waiting on her.

Every step uses an idea you will learn properly later in the track: keys in code (lesson 24), boards and columns (lesson 14), linking and fields (lesson 11), JQL (lessons 16 to 19).

The git track explains branches and pull requests themselves; see [What a branch really is](#/lesson/git/branches-in-a-nutshell) and [Accounts, forks and the pull-request flow](#/lesson/git/github-forks-prs).

## What Jira is not

- **Not a method.** Jira supports Scrum and Kanban, but a team can use it badly with either. A tool cannot make work small, goals clear or feedback fast.
- **Not documentation.** Long design discussions belong in a design document (often in Confluence), linked from the work item.
- **Not a performance-review system.** Counting how many tickets each person closed creates perverse incentives: people split work artificially and avoid hard problems. Reports are for teams to improve, not to rank individuals (lesson 21).
- **Not the conversation.** The Agile Manifesto values individuals and interactions over processes and tools. A comment thread of 40 messages is a sign the people involved should talk.

## How interviewers probe this

> [!INTERVIEW]
> "Have you used Jira? How did your team use it?" Give specifics, not "yes": "We had one space per team with a Scrum board. I'd pick up stories from the sprint, put the key in my branch name so the PR showed on the ticket, and move cards through To Do, In Progress, Review, Done. I wrote a few saved JQL filters for bugs assigned to our component and we had a dashboard for the on-call engineer." Concrete details like these are what interviewers want.

Other likely questions:

- "What is the difference between a project (space) and a board?" A space holds work items and their configuration; a board is a view that shows work items selected by a filter, which can even span several spaces (lesson 14).
- "What is an issue key?" Space key, hyphen, sequential number; used to reference work everywhere, including in code tools.
- "Have you used another tracker?" Explain how its concepts map: a Linear "issue", an Azure DevOps "work item", a GitHub "issue" on a GitHub Projects board.

## Summary

- Jira is Atlassian's work-tracking product: work items with keys, moving through workflows on boards, planned in sprints, searched with JQL, reported in charts.
- In Jira Cloud, "issue" became "work item" (announced 6 February 2025, rollout from March 2025) and "project" became "space"; APIs keep "issue", and Data Center documentation keeps the old names.
- Teach yourself the old JQL names (`project`, `issue`) as the safe forms, and recognise the new ones.
- A site holds spaces; a space has a key; each work item key is the space key, a hyphen and a number, such as `SHOP-1042`.
- Uppercase keys in branch names, commit messages and pull-request titles link code to work items.
- Jira supports agile ways of working but does not create them; it is not a method, a documentation store or a performance-review tool.

## Glossary

- **Jira** — Atlassian's product for tracking and planning work.
- **Atlassian** — the company that makes Jira, Confluence and related products.
- **Site** — an organisation's Jira installation, usually at an address like `yourcompany.atlassian.net`.
- **Jira Cloud** — Jira hosted by Atlassian.
- **Jira Data Center** — Jira installed on an organisation's own infrastructure.
- **Space** — a container for work items with its own key and configuration; formerly called a project.
- **Space key** — the short uppercase code of a space, such as `SHOP`.
- **Work item** — one piece of tracked work; formerly called an issue.
- **Work item key** — the unique identifier of a work item, such as `SHOP-1042`.
- **Work type** — the category of a work item, such as Story or Bug; formerly issue type.
- **Ticket** — an informal word engineers use for a work item.
- **Jira Service Management (JSM)** — Atlassian's service desk product built on Jira work items.
- **Confluence** — Atlassian's wiki product for documents.
- **JQL** — Jira Query Language, used to search for work items.
- **Development panel** — the part of a work item that shows linked branches, commits and pull requests.

## Check yourself

```quiz
[
  {"q": "In current Jira Cloud wording, what is a 'space'?",
   "options": ["A board column", "What used to be called a project", "A dashboard gadget", "A type of sprint"],
   "answer": 1,
   "explain": "Jira Cloud renamed projects to spaces; the old word is still widely used."},
  {"q": "What did Atlassian say about its existing APIs when renaming 'issue' to 'work item'?",
   "options": ["All APIs were renamed immediately", "Existing APIs keep the 'issue' terminology", "APIs were removed", "Only GraphQL changed"],
   "answer": 1,
   "explain": "Existing APIs such as IssueTypes keep their names to avoid breaking changes."},
  {"q": "Which JQL form does this track teach as the safe one?",
   "options": ["space = SHOP", "project = SHOP", "workspace = SHOP", "board = SHOP"],
   "answer": 1,
   "explain": "The older project form works across Jira versions; newer space forms may not work everywhere yet."},
  {"q": "What is the structure of a work item key such as SHOP-1042?",
   "options": ["Board name and sprint number", "Space key, a hyphen, and a sequential number", "Assignee initials and date", "Random characters"],
   "answer": 1,
   "explain": "The key combines the space key and a sequential number."},
  {"q": "A developer names a branch shop-1042-fix. What is the likely problem?",
   "options": ["Branches cannot contain numbers", "The lowercase key may not be recognised; use SHOP-1042", "Branch names must start with feature/", "Nothing; keys are case-insensitive everywhere"],
   "answer": 1,
   "explain": "Developer integrations look for uppercase keys."},
  {"q": "Which hosting option keeps the older 'issue' and 'project' wording in its documentation?",
   "options": ["Jira Cloud", "Jira Data Center", "Confluence Cloud", "Jira Mobile"],
   "answer": 1,
   "explain": "Data Center documentation still uses issue and project."},
  {"q": "Why is counting closed tickets per person a poor performance measure?",
   "options": ["Jira cannot count tickets", "It encourages splitting work artificially and avoiding hard problems", "Tickets are always the same size", "It is too accurate"],
   "answer": 1,
   "explain": "Using a count as a target distorts behaviour; reports are for team improvement."}
]
```

> **Source:** Atlassian, What is a work item, https://support.atlassian.com/jira-software-cloud/docs/what-is-a-work-item/; Atlassian Developer Community, "Work" is the new collective term for items tracked in Jira (6 Feb 2025), https://community.developer.atlassian.com/t/work-is-the-new-collective-term-for-items-tracked-in-jira/88552; Atlassian, JQL keywords, https://support.atlassian.com/jira-software-cloud/docs/jql-keywords/; Atlassian, Process work items with smart commits, https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/; Atlassian, Reference work items in your development work, https://support.atlassian.com/jira-software-cloud/docs/reference-issues-in-your-development-work/; Atlassian, Introduction to the Service Collection, https://www.atlassian.com/collections/service/guides/introduction-service-collection; Jira Data Center advanced searching, https://confluence.atlassian.com/jirasoftwareserver/advanced-searching-939938733.html
