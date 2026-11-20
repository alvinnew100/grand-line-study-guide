TRACK = dict(
    id="fastapi",
    title="FastAPI & Backend Engineering",
    icon="⚡",
    color="#059669",
    group="Machine Learning & MLOps",
    blurb="From HTTP fundamentals to production APIs: FastAPI, Pydantic, dependencies, async, databases, "
          "auth, testing, streaming and deployment — ending with a complete ML model-serving service.",
    sources=[
        "Bill Lubanovic, FastAPI: Modern Python Web Development (O'Reilly, 2023)",
        "FastAPI official documentation — https://fastapi.tiangolo.com/",
        "Pydantic v2 documentation — https://docs.pydantic.dev/",
    ],
    modules=[
        dict(
            id="web-http",
            title="Web & HTTP Fundamentals",
            summary="Requests, responses, methods, status codes, headers, REST, JSON, and the ASGI stack under FastAPI.",
            lessons=[
                dict(id="http-basics", title="HTTP: methods, status codes and headers", file="01-http-basics.md"),
                dict(id="rest-json", title="REST design and JSON", file="02-rest-json.md"),
                dict(id="asgi-stack", title="WSGI vs ASGI, Starlette and Uvicorn", file="03-asgi-stack.md"),
            ],
            problems=["api-status-class", "api-etag-check"],
        ),
        dict(
            id="fastapi-tour",
            title="FastAPI Tour",
            summary="Your first app: path and query parameters, request bodies, response models and automatic OpenAPI docs.",
            lessons=[
                dict(id="first-app", title="Your first FastAPI app", file="04-first-app.md"),
                dict(id="body-responses", title="Request bodies, responses and status codes", file="05-body-responses.md"),
                dict(id="openapi-docs", title="Headers, cookies, forms of input and automatic docs", file="06-openapi-docs.md"),
            ],
            problems=["api-route-match", "api-query-parse"],
        ),
        dict(
            id="pydantic",
            title="Pydantic Deep Dive",
            summary="Models, types, Field constraints, validators, serialization and settings management with Pydantic v2.",
            lessons=[
                dict(id="pydantic-models", title="Pydantic models, types and Field", file="07-pydantic-models.md"),
                dict(id="pydantic-validators", title="Validators and serialization", file="08-pydantic-validators.md"),
                dict(id="pydantic-settings", title="Settings and configuration management", file="09-pydantic-settings.md"),
            ],
            problems=["api-validate-schema"],
        ),
        dict(
            id="dependencies",
            title="Dependencies",
            summary="Dependency injection with Depends and Annotated: sub-dependencies, classes, yield, scopes and overrides.",
            lessons=[
                dict(id="depends-basics", title="Depends, Annotated and sub-dependencies", file="10-depends-basics.md"),
                dict(id="yield-deps", title="Yield dependencies, scopes and test overrides", file="11-yield-deps.md"),
            ],
            problems=["api-di-resolver"],
        ),
        dict(
            id="async",
            title="Async Python for APIs",
            summary="The event loop, async def vs def, blocking calls, background tasks and bounding concurrency.",
            lessons=[
                dict(id="async-fundamentals", title="async def, await and the event loop", file="12-async-fundamentals.md"),
                dict(id="background-concurrency", title="Background tasks and concurrency limits", file="13-background-concurrency.md"),
            ],
            problems=["api-concurrency-schedule"],
        ),
        dict(
            id="structure",
            title="Project Structure",
            summary="APIRouter, bigger applications, and the book's web / service / data layered architecture.",
            lessons=[
                dict(id="routers", title="APIRouter and bigger applications", file="14-routers.md"),
                dict(id="layers", title="Layered architecture: web, service, data", file="15-layers.md"),
            ],
            problems=["api-pagination"],
        ),
        dict(
            id="databases",
            title="Databases",
            summary="SQLAlchemy and SQLModel, a session per request, Alembic migrations, async drivers, Redis caching.",
            lessons=[
                dict(id="sql-sqlmodel", title="SQL with SQLAlchemy and SQLModel", file="16-sql-sqlmodel.md"),
                dict(id="migrations-async-db", title="Migrations, pooling and async drivers", file="17-migrations-async-db.md"),
                dict(id="nosql-redis", title="NoSQL and Redis caching", file="18-nosql-redis.md"),
            ],
            problems=["api-lru-ttl-cache", "api-idempotency-store"],
        ),
        dict(
            id="security",
            title="Auth & Security",
            summary="OAuth2 password flow, password hashing, JWT, scopes, CORS, rate limiting and common vulnerabilities.",
            lessons=[
                dict(id="oauth2-jwt", title="OAuth2 password flow, hashing and JWT", file="19-oauth2-jwt.md"),
                dict(id="authz-cors", title="Authorization, CORS, rate limiting and common vulnerabilities", file="20-authz-cors.md"),
            ],
            problems=["api-password-hash", "api-jwt-hs256", "api-token-bucket", "api-cors-preflight"],
        ),
        dict(
            id="errors-testing",
            title="Errors, Middleware, Logging & Testing",
            summary="HTTPException, custom exception handlers, middleware, structured logging, TestClient and async tests.",
            lessons=[
                dict(id="errors-middleware", title="Errors, exception handlers and middleware", file="21-errors-middleware.md"),
                dict(id="testing", title="Testing FastAPI apps", file="22-testing.md"),
            ],
            problems=["api-middleware-chain"],
        ),
        dict(
            id="files-streaming",
            title="Files, Forms, WebSockets & Streaming",
            summary="Uploads and downloads, form data, WebSockets, StreamingResponse and Server-Sent Events.",
            lessons=[
                dict(id="files-forms", title="Files, forms and static content", file="23-files-forms.md"),
                dict(id="websockets-streaming", title="WebSockets, streaming and Server-Sent Events", file="24-websockets-streaming.md"),
            ],
            problems=["api-sse-parse"],
        ),
        dict(
            id="deployment",
            title="Performance & Deployment",
            summary="Workers, Docker images, environment config, health checks, logging, metrics and tracing.",
            lessons=[
                dict(id="deploy-docker", title="Workers, Docker and running in production", file="25-deploy-docker.md"),
                dict(id="observability", title="Health checks, logging and observability", file="26-observability.md"),
            ],
            problems=["api-retry-backoff"],
        ),
        dict(
            id="ml-serving",
            title="FastAPI for ML: Serving Models",
            summary="Load models in lifespan, typed inputs, batching, async inference, LLM token streaming, versioning — and a full project.",
            lessons=[
                dict(id="serving-models", title="Serving an ML model with FastAPI", file="27-serving-models.md"),
                dict(id="llm-streaming-versioning", title="Streaming LLM output and versioned endpoints", file="28-llm-streaming.md"),
                dict(id="ml-project", title="End-to-end project: a production model service", file="29-ml-project.md"),
            ],
            problems=["api-micro-batcher"],
        ),
    ],
)
