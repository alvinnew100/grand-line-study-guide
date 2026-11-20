TRACK = dict(
    id="thinking",
    title="Open-Ended Engineering Questions",
    icon="🧩",
    color="#7b5ea7",
    group="Engineering Practice",
    blurb="How to answer interview questions that have no single right answer: testing a product, updating a decision table, "
          "designing classes, APIs, schemas and systems, debugging from evidence, weighing trade-offs, planning, security, ML and "
          "behavioural stories. Reusable frameworks, fully worked answers, 230 practice questions and judged coding problems.",
    sources=[
        "ISTQB Certified Tester Foundation Level syllabus v4.0 (https://www.istqb.org)",
        "Winters, Manshreck & Wright, Software Engineering at Google (https://abseil.io/resources/swe-book)",
        "Beyer et al., Site Reliability Engineering (https://sre.google/sre-book/table-of-contents/)",
        "Martin Fowler and colleagues, articles on delivery, design and data (https://martinfowler.com)",
        "Trunk Based Development (https://trunkbaseddevelopment.com) and DORA research (https://dora.dev)",
        "Google API Improvement Proposals (https://google.aip.dev) and Google Engineering Practices (https://google.github.io/eng-practices/)",
        "OWASP threat modelling, Top 10 and cheat sheets (https://owasp.org)",
        "Donne Martin, System Design Primer (https://github.com/donnemartin/system-design-primer); Yangshun Tay, Tech Interview Handbook (https://www.techinterviewhandbook.org)",
        "Martin Zinkevich, Rules of Machine Learning (https://developers.google.com/machine-learning/guides/rules-of-ml)",
    ],
    modules=[
        dict(
            id="framework",
            title="1. How These Interviews Work",
            summary="What open-ended questions measure, the six families, and a seven-step answer shape with spoken drills.",
            lessons=[
                dict(id="how-interviews-work", title="How open-ended interviews work and what they score", file="01-how-interviews-work.md"),
                dict(id="answer-framework", title="A seven-step answer framework and how to practise it aloud", file="02-answer-framework.md"),
            ],
            problems=[],
        ),
        dict(
            id="test-techniques",
            title="2. Test Design Techniques",
            summary="Equivalence partitions, boundaries, decision tables, state transitions, pairwise testing, exploratory testing, risk and non-functional categories.",
            lessons=[
                dict(id="partitions-boundaries", title="Equivalence partitioning and boundary value analysis", file="03-partitions-boundaries.md"),
                dict(id="tables-states-pairwise", title="Decision tables, state transitions and pairwise testing", file="04-tables-states-pairwise.md"),
                dict(id="exploratory-risk-nonfunctional", title="Exploratory testing, risk and non-functional categories", file="05-exploratory-risk-nonfunctional.md"),
            ],
            problems=["think-boundary-values", "think-equivalence-classes", "think-pairwise-uncovered", "think-pairwise-generate", "think-risk-priority"],
        ),
        dict(
            id="test-anything",
            title="3. \"How Would You Test X?\"",
            summary="A repeatable template and ten fully worked products, physical and digital, each with a prioritised test plan.",
            lessons=[
                dict(id="template-vending-machine", title="A repeatable template, and the vending machine in full", file="06-template-vending-machine.md"),
                dict(id="testing-physical-products", title="Testing physical products: elevator, ATM, pen and self-checkout kiosk", file="07-testing-physical-products.md"),
                dict(id="testing-digital-products", title="Testing digital products: login, search, payments API, chat and a recommendation model", file="08-testing-digital-products.md"),
            ],
            problems=["think-elevator-scheduler", "think-atm-withdraw"],
        ),
        dict(
            id="decision-tables",
            title="4. Decision Tables in Depth",
            summary="Build a table from requirements, find gaps and contradictions, collapse it, and update it when the rules change.",
            lessons=[
                dict(id="building-decision-tables", title="Building a decision table from requirements", file="09-building-decision-tables.md"),
                dict(id="collapse-contradictions-gaps", title="Collapsing tables, contradictions and gaps", file="10-collapse-contradictions-gaps.md"),
                dict(id="rules-changed", title="Updating a table when the rules change", file="11-rules-changed.md"),
            ],
            problems=["think-table-first-match", "think-table-unique-match", "think-table-missing", "think-table-contradictions", "think-table-collapse", "think-table-add-condition", "think-table-diff"],
        ),
        dict(
            id="state-machines",
            title="5. State Machines and Scenario Modelling",
            summary="Draw the states of a device or workflow, find the undefined transitions, and derive test paths.",
            lessons=[
                dict(id="modelling-state-machines", title="Modelling a device as a state machine", file="12-modelling-state-machines.md"),
                dict(id="test-paths-invalid-transitions", title="Deriving test paths and invalid transitions", file="13-test-paths-invalid-transitions.md"),
            ],
            problems=["think-vending-machine", "think-validate-sequence", "think-transition-coverage", "think-shortest-all-states"],
        ),
        dict(
            id="delivery-process",
            title="6. CI/CD and Process Design",
            summary="Buggy code on main, a bad deploy, hotfixes, slow and flaky tests, review rules, and zero-downtime migrations and rollouts.",
            lessons=[
                dict(id="buggy-code-on-main", title="Buggy code on main: designing a process that copes", file="14-buggy-code-on-main.md"),
                dict(id="bad-deploy-hotfix", title="A bad deploy in production and the hotfix flow", file="15-bad-deploy-hotfix.md"),
                dict(id="flaky-tests-review-rules", title="Slow or flaky test suites, and designing code review rules", file="16-flaky-tests-review-rules.md"),
                dict(id="migrations-rollouts", title="Migration and rollout planning", file="17-migrations-rollouts.md"),
            ],
            problems=["think-revert-set", "think-canary-decision"],
        ),
        dict(
            id="debugging",
            title="7. Debugging, Incidents and Root-Cause Analysis",
            summary="Hypothesis-driven triage, partial outages, model regressions, and reading logs, graphs and stack traces.",
            lessons=[
                dict(id="hypothesis-triage", title="Hypothesis-driven triage: \"the site is slow\" and \"the nightly job failed\"", file="18-hypothesis-triage.md"),
                dict(id="region-login-model-accuracy", title="\"Users in one region cannot log in\" and \"the model's accuracy dropped\"", file="19-region-login-model-accuracy.md"),
                dict(id="rca-from-evidence", title="Root-cause analysis from evidence: logs, graphs, stack traces, bisecting and five whys", file="20-rca-from-evidence.md"),
            ],
            problems=["think-triage-order"],
        ),
        dict(
            id="estimation-metrics",
            title="8. Estimation, Metrics and Ship Decisions",
            summary="Back-of-envelope sizing, Fermi questions and puzzles, success metrics and A/B tests, and whether to ship.",
            lessons=[
                dict(id="estimation-fermi", title="Back-of-envelope estimation, Fermi questions and logic puzzles", file="21-estimation-fermi.md"),
                dict(id="metrics-experiments", title="Metrics, experiments and \"a number moved — why?\"", file="22-metrics-experiments.md"),
                dict(id="ship-decisions-product-sense", title="\"Should we ship it?\" and product-sense questions for engineers", file="23-ship-decisions-product-sense.md"),
            ],
            problems=["think-estimate-capacity", "think-ab-significance", "think-metric-attribution"],
        ),
        dict(
            id="object-design",
            title="9. Object-Oriented and Low-Level Design",
            summary="Requirements, entities, class diagrams and patterns for a parking lot, vending machine, elevator controller, library and rate limiter.",
            lessons=[
                dict(id="object-design-framework", title="Object-oriented design questions: a framework, a parking lot and a vending machine", file="24-object-design-framework.md"),
                dict(id="object-design-worked", title="More object-design answers: elevator controller, library system and a rate limiter", file="25-object-design-worked.md"),
            ],
            problems=["think-parking-lot", "think-rate-limiter"],
        ),
        dict(
            id="api-design",
            title="10. API Design",
            summary="Resources, methods, status codes, errors, idempotency, pagination, versioning and auth, with a URL shortener, payments and file upload.",
            lessons=[
                dict(id="api-design-principles", title="API design questions: the building blocks", file="26-api-design-principles.md"),
                dict(id="api-design-worked", title="API design, worked: a URL shortener, payments and file upload", file="27-api-design-worked.md"),
            ],
            problems=["think-pagination-cursor", "think-idempotency-keys"],
        ),
        dict(
            id="data-modelling",
            title="11. Data Modelling and Schema Design",
            summary="Entities, relationships, normalisation, SQL versus NoSQL, and models for a ride-sharing trip, a social feed and inventory.",
            lessons=[
                dict(id="data-modelling-basics", title="Data modelling questions: entities, relationships and SQL versus NoSQL", file="28-data-modelling-basics.md"),
                dict(id="data-modelling-worked", title="Data modelling, worked: a ride-sharing trip, a social feed and an inventory system", file="29-data-modelling-worked.md"),
            ],
            problems=["think-fd-check"],
        ),
        dict(
            id="system-design",
            title="12. Lightweight System Design",
            summary="A six-step template applied to a URL shortener, notification service, news feed and chat, plus the follow-ups that always come.",
            lessons=[
                dict(id="system-design-template", title="Lightweight system design: a repeatable template, a URL shortener and a notification service", file="30-system-design-template.md"),
                dict(id="system-design-feed-chat", title="Lightweight system design: a news feed, a chat service and the follow-ups that always come", file="31-system-design-feed-chat.md"),
            ],
            problems=[],
        ),
        dict(
            id="trade-offs",
            title="13. Trade-offs: \"Which Would You Choose?\"",
            summary="A decision framework for monolith or microservices, SQL or NoSQL, build or buy, consistency or availability, sync or async.",
            lessons=[
                dict(id="tradeoff-framework", title="\"Which would you choose?\" — a decision framework, with monolith versus microservices and SQL versus NoSQL", file="32-tradeoff-framework.md"),
                dict(id="tradeoffs-worked", title="More \"which would you choose?\" answers: build versus buy, consistency versus availability, sync versus async", file="33-tradeoffs-worked.md"),
            ],
            problems=[],
        ),
        dict(
            id="prioritisation-planning",
            title="14. Prioritisation and Planning",
            summary="Too many bugs and features, technical debt, breaking down vague work, estimating, and a slipping deadline.",
            lessons=[
                dict(id="prioritisation", title="Prioritisation questions: too many bugs and features, and technical debt versus delivery", file="34-prioritisation.md"),
                dict(id="planning-estimating", title="Planning questions: breaking down a vague task, estimating a project, and a deadline that is slipping", file="35-planning-estimating.md"),
            ],
            problems=[],
        ),
        dict(
            id="code-quality",
            title="15. Code Review and Code Quality",
            summary="A six-pass method for reviewing a snippet and a safe way to change legacy code.",
            lessons=[
                dict(id="code-review-snippets", title="\"Review this code\": a method for code-review questions", file="36-code-review-snippets.md"),
                dict(id="refactoring-legacy", title="Changing legacy code safely: refactoring questions", file="37-refactoring-legacy.md"),
            ],
            problems=[],
        ),
        dict(
            id="concurrency-failure",
            title="16. Concurrency and Failure Scenarios",
            summary="The last item, the double charge, lost updates, deadlocks, cascading failures, retry storms and split brain, told as stories.",
            lessons=[
                dict(id="concurrency-stories", title="Concurrency questions told as stories: the last item, the double charge and the lost update", file="38-concurrency-stories.md"),
                dict(id="distributed-failures", title="Failure scenarios in distributed systems, told as stories", file="39-distributed-failures.md"),
            ],
            problems=["think-inventory-race", "think-retry-outcome"],
        ),
        dict(
            id="scaling-cost",
            title="17. Scaling, Performance and Cost",
            summary="A ten-times-slower endpoint, a database at capacity, a doubled cloud bill and a tenfold traffic event.",
            lessons=[
                dict(id="performance-scenarios", title="Performance scenarios: \"the endpoint is ten times slower\" and \"the database is at capacity\"", file="40-performance-scenarios.md"),
                dict(id="cost-and-load", title="Cost and load scenarios: \"the bill doubled\" and \"traffic will be ten times higher next month\"", file="41-cost-and-load.md"),
            ],
            problems=[],
        ),
        dict(
            id="security-privacy",
            title="18. Security and Privacy for Generalists",
            summary="Threat-modelling a feature, responding to a leaked credential, and handling personal data — defensive only.",
            lessons=[
                dict(id="threat-modelling", title="Security thinking for generalists: threat-modelling a feature", file="42-threat-modelling.md"),
                dict(id="credentials-and-personal-data", title="Security and privacy scenarios: a leaked credential and handling personal data", file="43-credentials-and-personal-data.md"),
            ],
            problems=[],
        ),
        dict(
            id="ml-ai",
            title="19. Machine-Learning and AI Questions",
            summary="When not to use ML, choosing a metric, data leakage, evaluating LLM features, hallucinations and RAG.",
            lessons=[
                dict(id="ml-open-ended", title="Machine-learning questions with no single answer: when to use it, which metric, and data leakage", file="44-ml-open-ended.md"),
                dict(id="llm-and-rag-questions", title="Questions about language-model features: evaluation, hallucinations and retrieval-augmented generation", file="45-llm-and-rag-questions.md"),
            ],
            problems=[],
        ),
        dict(
            id="behavioural",
            title="20. Behavioural-Technical Hybrids",
            summary="STAR, disagreeing about a design, owning an outage, unclear requirements, and explaining technical ideas plainly.",
            lessons=[
                dict(id="behavioural-star", title="Behavioural-technical questions: the STAR method, disagreeing about a design, and owning an outage", file="46-behavioural-star.md"),
                dict(id="behavioural-communication", title="Behavioural-technical questions: unclear requirements and explaining technical ideas to non-technical people", file="47-behavioural-communication.md"),
            ],
            problems=[],
        ),
        dict(
            id="question-bank",
            title="21. Question Bank and Practice Plan",
            summary="230 further questions with outline answers, a four-week plan and a self-scoring rubric.",
            lessons=[
                dict(id="question-bank-design", title="Question bank 1: testing, rules, states, object design, APIs and data models", file="48-question-bank-design.md"),
                dict(id="question-bank-systems", title="Question bank 2: system design, trade-offs, delivery process, incidents, concurrency and scale", file="49-question-bank-systems.md"),
                dict(id="question-bank-judgment", title="Question bank 3: estimation, metrics, planning, code quality, security, machine learning and behavioural questions", file="50-question-bank-judgment.md"),
                dict(id="practice-plan-rubric", title="A four-week practice plan and a self-scoring rubric", file="51-practice-plan-rubric.md"),
            ],
            problems=[],
        ),
    ],
)
