def _L(id, title, file):
    return dict(id=id, title=title, file=file)


_MODULES = [
    dict(
        id="from-zero",
        title="0. Architecture from zero",
        summary="What a monolith, a service and an API are; what a network call costs; why teams split systems; and why you probably should not start with microservices.",
        lessons=[
            _L("monolith-service-api", "Monoliths, services and APIs in plain words", "01-monolith-service-api.md"),
            _L("network-cost-why-split", "What a network call costs, why teams split, and why not to start with microservices", "02-network-cost-why-split.md"),
        ],
        problems=["msvc-chain-availability"],
    ),
    dict(
        id="what-are-microservices",
        title="1. What are microservices?",
        summary="Independent deployability, business-domain boundaries, owning your own state, size and flexibility; the forms of monolith; enabling technology; benefits, pain points and when to say no.",
        lessons=[
            _L("key-concepts", "The key concepts: independent deployability, domain boundaries and owned state", "03-key-concepts.md"),
            _L("monolith-forms-tradeoffs", "The monolith in its forms, enabling technology, benefits, pain points and when not to use microservices", "04-monolith-forms-tradeoffs.md"),
        ],
        problems=["msvc-distributed-monolith"],
    ),
    dict(
        id="modelling",
        title="2. How to model microservices",
        summary="Information hiding, coupling and cohesion, the four types of coupling, and domain-driven design: ubiquitous language, aggregates, bounded contexts and event storming.",
        lessons=[
            _L("coupling-cohesion", "Information hiding, coupling and cohesion", "05-coupling-cohesion.md"),
            _L("ddd-boundaries", "Domain-driven design: language, aggregates, bounded contexts and event storming", "06-ddd-boundaries.md"),
        ],
        problems=["msvc-coupling-type", "msvc-cohesion-score", "msvc-bounded-contexts"],
    ),
    dict(
        id="splitting-the-monolith",
        title="3. Splitting the monolith",
        summary="Having a goal, migrating incrementally, what to split first, the strangler fig, parallel run and feature toggle patterns, and the hard part: splitting the data.",
        lessons=[
            _L("migration-planning", "Planning a migration: goals, increments and what to split first", "07-migration-planning.md"),
            _L("migration-patterns-data", "Migration patterns and splitting the data", "08-migration-patterns-data.md"),
        ],
        problems=["msvc-strangler-routing"],
    ),
    dict(
        id="communication-styles",
        title="4. Communication styles",
        summary="In-process versus inter-process calls; synchronous blocking and asynchronous non-blocking; request-response, event-driven and common data; how to choose.",
        lessons=[
            _L("sync-async", "From in-process to inter-process: synchronous and asynchronous calls", "09-sync-async.md"),
            _L("request-response-events", "Request-response, event-driven and common data: choosing a style", "10-request-response-events.md"),
        ],
        problems=["msvc-outbox-delivery"],
    ),
    dict(
        id="implementing-communication",
        title="5. Implementing communication",
        summary="RPC and gRPC, REST, GraphQL and message brokers; serialisation formats and schemas; breaking changes and versioning; code reuse; service discovery, meshes, gateways and documentation.",
        lessons=[
            _L("technology-choices", "Technology choices: RPC, REST, GraphQL, brokers, formats and schemas", "11-technology-choices.md"),
            _L("handling-change", "Handling change: breaking changes, versioning, reuse, discovery, meshes and gateways", "12-handling-change.md"),
        ],
        problems=["msvc-schema-compat", "msvc-semver-bump", "msvc-schema-evolution", "msvc-service-registry", "msvc-gateway-routes"],
    ),
    dict(
        id="workflow",
        title="6. Workflow",
        summary="Database transactions and ACID, why two-phase commit hurts across services, and sagas with orchestration, choreography and compensating actions.",
        lessons=[
            _L("transactions-2pc", "Transactions, ACID and why distributed transactions hurt", "13-transactions-2pc.md"),
            _L("sagas", "Sagas: orchestration, choreography and compensation", "14-sagas.md"),
        ],
        problems=["msvc-two-phase-commit", "msvc-saga-orchestrator", "msvc-saga-choreography"],
    ),
    dict(
        id="build",
        title="7. Build",
        summary="Continuous integration, build pipelines and artifacts, and how to map source code and builds to services: one giant repo, one repo per service, or a monorepo.",
        lessons=[
            _L("ci-pipelines", "Continuous integration and build pipelines", "15-ci-pipelines.md"),
            _L("monorepo-multirepo", "Monorepo or multirepo: mapping source code and builds to services", "16-monorepo-multirepo.md"),
        ],
        problems=["msvc-monorepo-affected"],
    ),
    dict(
        id="deployment",
        title="8. Deployment",
        summary="From the logical picture to physical instances; isolated execution, automation, infrastructure as code, zero downtime and desired state; machines, containers, platforms and functions; Kubernetes; progressive delivery.",
        lessons=[
            _L("logical-to-physical", "From logical to physical and the principles of deployment", "17-logical-to-physical.md"),
            _L("deployment-options", "Deployment options, Kubernetes and progressive delivery", "18-deployment-options.md"),
        ],
        problems=["msvc-deploy-order", "msvc-canary-decision", "msvc-blue-green", "msvc-feature-toggle"],
    ),
    dict(
        id="testing",
        title="9. Testing",
        summary="Types of tests and the test pyramid, service tests with stubs, the cost of end-to-end tests, consumer-driven contracts, testing in production and cross-functional testing.",
        lessons=[
            _L("test-pyramid", "Test types, the pyramid, service tests and the cost of end-to-end tests", "19-test-pyramid.md"),
            _L("contract-tests", "Contract tests, testing in production and cross-functional testing", "20-contract-tests.md"),
        ],
        problems=["msvc-contract-verify"],
    ),
    dict(
        id="observability",
        title="10. From monitoring to observability",
        summary="Log aggregation, metrics aggregation and distributed tracing; service level objectives and error budgets; alerting; semantic monitoring and testing in production.",
        lessons=[
            _L("logs-metrics-traces", "Logs, metrics and traces", "21-logs-metrics-traces.md"),
            _L("slo-alerting", "Are we doing OK? SLOs, error budgets, alerting and semantic monitoring", "22-slo-alerting.md"),
        ],
        problems=["msvc-trace-slowest-path", "msvc-slo-burn-rate"],
    ),
    dict(
        id="security",
        title="11. Security",
        summary="Least privilege, defence in depth and automation; the five functions of cybersecurity; credentials, patching, backups and rebuild; zero trust; encryption; authentication, authorisation, JWTs and the confused deputy.",
        lessons=[
            _L("security-foundations", "Security foundations: principles, the five functions, secrets, patching and backups", "23-security-foundations.md"),
            _L("trust-identity", "Trust, encryption and identity: zero trust, JWTs and the confused deputy", "24-trust-identity.md"),
        ],
        problems=["msvc-jwt-confused-deputy"],
    ),
    dict(
        id="resiliency",
        title="12. Resiliency",
        summary="What resiliency means, why failure is everywhere, degrading functionality, the stability patterns, the CAP theorem, chaos engineering and blameless post-mortems.",
        lessons=[
            _L("resiliency-concepts", "What resiliency is: failure, degradation, CAP, chaos and blame", "25-resiliency-concepts.md"),
            _L("stability-patterns", "Stability patterns: timeouts, retries, bulkheads, circuit breakers and idempotency", "26-stability-patterns.md"),
        ],
        problems=["msvc-timeout-budget", "msvc-retry-backoff", "msvc-circuit-breaker", "msvc-bulkhead", "msvc-cascading-failure"],
    ),
    dict(
        id="scaling",
        title="13. Scaling",
        summary="The four axes of scaling (vertical, horizontal duplication, data partitioning, functional decomposition), combining them, starting small, caching and autoscaling.",
        lessons=[
            _L("scaling-axes", "The four axes of scaling", "27-scaling-axes.md"),
            _L("caching-autoscaling", "Caching and autoscaling", "28-caching-autoscaling.md"),
        ],
        problems=["msvc-ttl-cache"],
    ),
    dict(
        id="user-interfaces",
        title="14. User interfaces",
        summary="Ownership of the user interface, stream-aligned teams, the monolithic frontend, micro frontends, page-based and widget-based decomposition, aggregating gateways, backends for frontends and GraphQL.",
        lessons=[
            _L("ui-decomposition", "Who owns the user interface? Monolithic frontends and micro frontends", "29-ui-decomposition.md"),
            _L("gateway-bff", "Aggregating gateways, backends for frontends and GraphQL", "30-gateway-bff.md"),
        ],
        problems=["msvc-bff-aggregate"],
    ),
    dict(
        id="organisation",
        title="15. Organisational structures",
        summary="Loosely coupled organisations, Conway's law, team size, stream-aligned and enabling teams, shared microservices, internal open source and the paved road.",
        lessons=[
            _L("conway-teams", "Conway's law and team structure", "31-conway-teams.md"),
            _L("shared-services-paved-road", "Shared microservices, internal open source and the paved road", "32-shared-services-paved-road.md"),
        ],
        problems=["msvc-conway-mismatch", "msvc-tenant-rate-limiter"],
    ),
    dict(
        id="evolutionary-architect",
        title="16. The evolutionary architect",
        summary="What the architect's role is, defining system boundaries, principles and practices, guiding an evolving architecture, governance, exemplars, technical debt and exceptions.",
        lessons=[
            _L("architect-role", "The architect's role: boundaries, principles and practices", "33-architect-role.md"),
            _L("governance-debt", "Guiding an evolutionary architecture: governance, exemplars and technical debt", "34-governance-debt.md"),
        ],
        problems=["msvc-fitness-functions"],
    ),
    dict(
        id="interview",
        title="17. Architecture interview essentials",
        summary="Trade-off answers for monolith versus microservices, splitting a system live, saga versus two-phase commit, sync versus async, failing dependencies, idempotency, and 40 practice prompts.",
        lessons=[
            _L("interview-core", "Interview essentials I: the six questions you will be asked", "35-interview-core.md"),
            _L("interview-prompts", "Interview essentials II: 40 practice prompts with outline answers", "36-interview-prompts.md"),
        ],
        problems=["msvc-design-review"],
    ),
]

TRACK = dict(
    id="microservices",
    title="Microservices & Software Architecture",
    icon="🧩",
    color="#7b5ea7",
    group="Engineering Practice",
    blurb="From a single-server application to a system of independently deployable services: boundaries, communication, sagas, deployment, testing, observability, security, resilience, scaling and the people side, with simulations you can run.",
    sources=[
        "Newman, Building Microservices, 2nd ed., ch. 1-16",
        "martinfowler.com (MonolithFirst, StranglerFigApplication, CircuitBreaker, Consumer-Driven Contracts)",
        "microservices.io (Saga, Transactional Outbox)",
    ],
    modules=_MODULES,
)
