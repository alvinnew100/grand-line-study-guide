TRACK = dict(
    id="django",
    title="Django",
    icon="🎸",
    color="#0c7c59",
    group="Web",
    blurb="Django 5.x from an empty folder to a deployed, tested, secure product: projects and apps, views and "
          "templates, models and the ORM in depth, forms, accounts and permissions, REST APIs and async, "
          "deployment, and interview practice with worked answers. Written for complete beginners.",
    sources=[
        "William S. Vincent, Django for Beginners (topics per chapter; rewritten for Django 5.x)",
        "Django documentation — https://docs.djangoproject.com/en/5.2/",
        "Django REST framework documentation — https://www.django-rest-framework.org/",
        "pytest-django, factory_boy, WhiteNoise, Channels, Gunicorn and Uvicorn documentation",
    ],
    modules=[
        dict(
            id="setup",
            title="Initial setup",
            summary="Python, virtual environments, installing Django, Git and a tidy project folder.",
            lessons=[
                dict(id="setup-python-venv", title="Python, virtual environments and installing Django", file="01-python-venv-install.md"),
                dict(id="setup-git-project", title="Git, requirements and a tidy project folder", file="02-git-project-hygiene.md"),
            ],
            problems=[],
        ),
        dict(
            id="first-app",
            title="A first app",
            summary="Project versus app, the settings file, the request/response cycle, views, URLs and first tests.",
            lessons=[
                dict(id="project-vs-app", title="Projects, apps and the settings file", file="03-project-vs-app.md"),
                dict(id="request-response", title="The request/response cycle, views, URLs and first tests", file="04-request-response.md"),
            ],
            problems=["django-url-match", "django-url-reverse"],
        ),
        dict(
            id="pages",
            title="Pages: templates and class-based views",
            summary="The template language, class-based views, template inheritance, page tests and what deployment means.",
            lessons=[
                dict(id="templates-dtl", title="Templates and the Django template language", file="05-templates-dtl.md"),
                dict(id="cbv-inheritance", title="Class-based views, template inheritance, page tests and a first deployment", file="06-cbv-inheritance.md"),
            ],
            problems=["django-template-render", "django-template-blocks"],
        ),
        dict(
            id="board",
            title="A lost-and-found board: models and lists",
            summary="Models, migrations, the admin, ListView, querysets, database tests and configuration from the environment.",
            lessons=[
                dict(id="models-migrations-admin", title="Models, migrations and the admin", file="07-models-migrations-admin.md"),
                dict(id="listview-querysets", title="ListView, querysets and tests with a database", file="08-listview-querysets.md"),
                dict(id="env-config-deploy", title="Deploying with environment variables", file="09-env-config-deploy.md"),
            ],
            problems=["django-queryset-filter", "django-queryset-shape", "django-pagination"],
        ),
        dict(
            id="journal",
            title="A trail journal: relationships and static files",
            summary="Foreign keys, detail views, slugs, get_absolute_url, static files and CSS.",
            lessons=[
                dict(id="fk-detail-slugs", title="Foreign keys, detail views and slugs", file="10-fk-detail-slugs.md"),
                dict(id="static-css", title="Static files and CSS", file="11-static-css.md"),
            ],
            problems=["django-slugify"],
        ),
        dict(
            id="forms",
            title="Forms",
            summary="Forms, ModelForm, validation, CSRF and the generic create, update and delete views.",
            lessons=[
                dict(id="forms-validation-csrf", title="Forms, ModelForm, validation and CSRF", file="12-forms-validation-csrf.md"),
                dict(id="edit-views", title="CreateView, UpdateView and DeleteView", file="13-edit-views.md"),
            ],
            problems=["django-form-validate", "django-modelform-fields", "django-csrf-compare"],
        ),
        dict(
            id="accounts",
            title="User accounts",
            summary="The auth app, password hashing, sessions, and the login, logout and sign-up pages.",
            lessons=[
                dict(id="auth-app", title="The auth app: users, passwords and sessions", file="14-auth-app.md"),
                dict(id="login-logout-signup", title="Login, logout and sign-up views", file="15-login-logout-signup.md"),
            ],
            problems=["django-session-expiry", "django-login-redirect"],
        ),
        dict(
            id="custom-user",
            title="A custom user model",
            summary="Why every project should start with one, how to define it, and how to wire it into forms and the admin.",
            lessons=[
                dict(id="custom-user-why-how", title="A custom user model: why and how", file="16-custom-user-why-how.md"),
                dict(id="custom-user-admin", title="Custom user forms and admin integration", file="17-custom-user-admin.md"),
            ],
            problems=[],
        ),
        dict(
            id="auth-flows",
            title="Authentication flows and templates",
            summary="Complete account flows, authentication backends, auth-aware navigation, messages and template tags.",
            lessons=[
                dict(id="auth-flows", title="Authentication flows end to end", file="18-auth-flows.md"),
                dict(id="auth-templates", title="Auth-aware templates, messages and navigation", file="19-auth-templates.md"),
            ],
            problems=[],
        ),
        dict(
            id="styling",
            title="Styling",
            summary="Bootstrap 5 with crispy forms, and the modern alternatives: Pico, Tailwind and htmx.",
            lessons=[
                dict(id="bootstrap", title="Styling with Bootstrap 5 and crispy forms", file="20-bootstrap.md"),
                dict(id="modern-css", title="Tailwind, Pico and htmx: modern alternatives", file="21-modern-css.md"),
            ],
            problems=[],
        ),
        dict(
            id="password-email",
            title="Password change, reset and email",
            summary="The built-in password views, how reset tokens work, and sending email reliably.",
            lessons=[
                dict(id="password-change-reset", title="Password change and reset", file="22-password-change-reset.md"),
                dict(id="email", title="Sending email", file="23-email.md"),
            ],
            problems=["django-password-validators"],
        ),
        dict(
            id="gazette",
            title="A newspaper app: stories, permissions, replies",
            summary="A full feature slice with a draft/published life cycle, permissions and mixins, and comments with model relationships.",
            lessons=[
                dict(id="gazette-stories", title="The Gazette: the stories app end to end", file="24-gazette-stories.md"),
                dict(id="permissions-mixins", title="Permissions, authorisation and mixins", file="25-permissions-mixins.md"),
                dict(id="comments-relationships", title="Replies: comments and model relationships", file="26-comments-relationships.md"),
            ],
            problems=["django-permission-check"],
        ),
        dict(
            id="deployment",
            title="Deployment",
            summary="Production settings, the security checklist, WhiteNoise, databases, Gunicorn and Uvicorn, Docker and a PaaS.",
            lessons=[
                dict(id="production-settings", title="Production settings and the security checklist", file="27-production-settings.md"),
                dict(id="servers-docker-paas", title="Gunicorn, Uvicorn, Docker and deploying to a PaaS", file="28-servers-docker-paas.md"),
            ],
            problems=["django-settings-env"],
        ),
        dict(
            id="orm",
            title="The ORM in depth",
            summary="Lazy querysets, lookups, Q and F, aggregation, select_related versus prefetch_related, transactions, indexes, migrations in teams and raw SQL.",
            lessons=[
                dict(id="orm-querysets", title="Querysets in depth: laziness, lookups, Q and F", file="29-orm-querysets.md"),
                dict(id="orm-aggregation-nplus1", title="Aggregation, joins and the N+1 problem", file="30-orm-aggregation-nplus1.md"),
                dict(id="orm-transactions-migrations", title="Transactions, indexes, migrations in teams and raw SQL", file="31-orm-transactions-migrations.md"),
            ],
            problems=["django-q-objects", "django-f-update", "django-annotate", "django-n-plus-one",
                      "django-related-query-count", "django-migration-order", "django-migration-squash"],
        ),
        dict(
            id="drf-async",
            title="Django REST framework and async",
            summary="Serializers, viewsets, routers, API authentication, permissions, pagination, throttling, async views, Channels and a comparison with FastAPI.",
            lessons=[
                dict(id="drf-serializers-viewsets", title="Django REST framework: serializers, viewsets and routers", file="32-drf-serializers-viewsets.md"),
                dict(id="drf-auth-pagination", title="API authentication, permissions, pagination and throttling", file="33-drf-auth-pagination.md"),
                dict(id="async-channels-fastapi", title="Async views, Channels and Django compared with FastAPI", file="34-async-channels-fastapi.md"),
            ],
            problems=[],
        ),
        dict(
            id="quality",
            title="Testing, performance and security",
            summary="pytest-django and factories, caching, the debug toolbar, the security middleware and the mistakes that undo it.",
            lessons=[
                dict(id="pytest-factories", title="Testing with pytest-django and factories", file="35-pytest-factories.md"),
                dict(id="caching-security", title="Caching, the debug toolbar and the security middleware", file="36-caching-security.md"),
            ],
            problems=["django-cache-key"],
        ),
        dict(
            id="interview",
            title="Django interview essentials",
            summary="Worked answers: MTV versus MVC, the request lifecycle, middleware order, signals, how migrations work, N+1 and sessions versus tokens.",
            lessons=[
                dict(id="interview-architecture", title="Architecture questions: MTV, the request lifecycle, middleware order and signals", file="37-interview-architecture.md"),
                dict(id="interview-data-state", title="Data and state questions: how migrations work, N+1 and sessions versus tokens", file="38-interview-data-state.md"),
            ],
            problems=["django-middleware-chain", "django-signal-dispatch"],
        ),
    ],
)
