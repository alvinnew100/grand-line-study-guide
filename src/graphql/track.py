TRACK = dict(
    id="graphql",
    title="GraphQL & API Design",
    icon="🕸️",
    color="#d6338a",
    group="Web",
    blurb="APIs explained from zero, then GraphQL end to end: the query language, schema design, resolvers, clients and "
          "their caches, security, performance at scale, and how to choose between REST, GraphQL and gRPC in an interview. "
          "Every idea runs in the page through small hand-written models of a GraphQL engine, plus 27 judged problems.",
    sources=[
        "Porcello & Banks, Learning GraphQL (O'Reilly, 2018)",
        "graphql.org/learn (official GraphQL documentation)",
        "spec.graphql.org (GraphQL specification)",
        "apollographql.com/docs (Apollo Server, Client and Federation documentation)",
    ],
    modules=[
        dict(
            id="apis-from-zero",
            title="APIs from Zero",
            summary="What an API is, how HTTP and JSON carry a request and a response, REST in plain words, and the first taste of asking only for what you need.",
            lessons=[
                dict(id="what-is-an-api", title="What an API is: HTTP and JSON from zero", file="01-what-is-an-api.md"),
                dict(id="rest-in-plain-words", title="REST in plain words", file="02-rest-in-plain-words.md"),
            ],
            problems=["gql-select-fields"],
        ),
        dict(
            id="welcome",
            title="Welcome to GraphQL",
            summary="Where GraphQL came from, its design principles, and the REST drawbacks it answers: over-fetching, under-fetching and endpoint sprawl.",
            lessons=[
                dict(id="what-is-graphql", title="What GraphQL is: history and design principles", file="03-what-is-graphql.md"),
                dict(id="rest-drawbacks", title="Over-fetching, under-fetching and endpoint sprawl", file="04-rest-drawbacks.md"),
            ],
            problems=["gql-aliases-args"],
        ),
        dict(
            id="graph-theory",
            title="Graph Theory",
            summary="Nodes, edges and paths; trees as a special kind of graph; and how real products are graphs underneath.",
            lessons=[
                dict(id="graph-vocabulary", title="Graph vocabulary: nodes, edges and paths", file="05-graph-vocabulary.md"),
                dict(id="trees-and-real-graphs", title="Trees as graphs, and graphs in the real world", file="06-trees-and-real-graphs.md"),
            ],
            problems=["gql-unused-types"],
        ),
        dict(
            id="query-language",
            title="The GraphQL Query Language",
            summary="Fields, arguments, aliases, fragments, variables, mutations, subscriptions, introspection and the syntax tree behind every query.",
            lessons=[
                dict(id="fields-args-fragments", title="Fields, arguments, aliases and fragments", file="07-fields-args-fragments.md"),
                dict(id="variables-mutations-subscriptions", title="Variables, mutations and subscriptions", file="08-variables-mutations-subscriptions.md"),
                dict(id="introspection-ast", title="Introspection and abstract syntax trees", file="09-introspection-ast.md"),
            ],
            problems=["gql-fragments-lists", "gql-variables-defaults", "gql-introspection-list"],
        ),
        dict(
            id="schema-design",
            title="Designing a Schema",
            summary="The type system, connections between types, arguments for filtering, paging and sorting, mutations with input types, and documentation.",
            lessons=[
                dict(id="types-scalars-nonnull", title="Types, scalars, enums, lists and non-null", file="10-types-scalars-nonnull.md"),
                dict(id="connections-through-types", title="Connections: one-to-one, one-to-many, many-to-many", file="11-connections-through-types.md"),
                dict(id="arguments-pagination", title="Arguments, filtering, pagination and sorting", file="12-arguments-pagination.md"),
                dict(id="mutations-inputs-docs", title="Mutations, input types, return types and subscriptions", file="13-mutations-inputs-docs.md"),
            ],
            problems=["gql-type-check", "gql-validate-query", "gql-non-null-propagation", "gql-offset-pagination",
                      "gql-cursor-pagination", "gql-filter-sort", "gql-mutation-input"],
        ),
        dict(
            id="creating-api",
            title="Creating a GraphQL API",
            summary="Project setup, resolvers and the resolver chain, context, custom scalars, a database, signing in with an OAuth provider and authorising users.",
            lessons=[
                dict(id="resolvers-context", title="Resolvers, the resolver chain and context", file="14-resolvers-context.md"),
                dict(id="scalars-db-auth", title="Custom scalars, databases, authentication and authorisation", file="15-scalars-db-auth.md"),
            ],
            problems=["gql-resolver-chain", "gql-field-auth"],
        ),
        dict(
            id="clients",
            title="GraphQL Clients",
            summary="Calling a GraphQL API with fetch, what client libraries add, the normalised cache, fetch policies, local state and optimistic UI.",
            lessons=[
                dict(id="fetch-and-clients", title="Calling GraphQL: fetch and client libraries", file="16-fetch-and-clients.md"),
                dict(id="cache-optimistic", title="The normalised cache, fetch policies, local state and optimistic UI", file="17-cache-optimistic.md"),
            ],
            problems=["gql-normalized-cache", "gql-optimistic-rollback"],
        ),
        dict(
            id="real-world",
            title="GraphQL in the Real World",
            summary="Subscriptions over WebSocket, file uploads, migrating from REST step by step, schema-first versus code-first, security limits and monitoring.",
            lessons=[
                dict(id="subscriptions-uploads-migration", title="Subscriptions, file uploads, migration and schema-first versus code-first", file="18-subscriptions-uploads-migration.md"),
                dict(id="security-monitoring", title="Security and monitoring", file="19-security-monitoring.md"),
            ],
            problems=["gql-subscription-filter", "gql-query-depth", "gql-complexity-score", "gql-persisted-queries"],
        ),
        dict(
            id="performance",
            title="Performance and Scale",
            summary="The N+1 problem and DataLoader batching, caching strategies, federation and schema stitching, and rate limiting by complexity.",
            lessons=[
                dict(id="n-plus-one-dataloader", title="The N+1 problem and DataLoader", file="20-n-plus-one-dataloader.md"),
                dict(id="caching-federation-rate-limits", title="Caching, federation and rate limiting", file="21-caching-federation-rate-limits.md"),
            ],
            problems=["gql-n-plus-one-count", "gql-dataloader-batch", "gql-schema-stitch"],
        ),
        dict(
            id="interview",
            title="REST vs GraphQL vs gRPC and API-Design Interview Essentials",
            summary="When to choose which style, designing a schema live, versioning and deprecation, error conventions and pagination styles, with worked answers.",
            lessons=[
                dict(id="rest-graphql-grpc", title="REST vs GraphQL vs gRPC: when to choose which", file="22-rest-graphql-grpc.md"),
                dict(id="design-interview", title="Designing a schema live: versioning, errors and pagination styles", file="23-design-interview.md"),
            ],
            problems=["gql-rest-to-schema", "gql-schema-diff", "gql-deprecation-report"],
        ),
    ],
)
