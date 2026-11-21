# Settings and configuration management

> **Before this lesson:** you should be able to define a Pydantic model with typed fields and
> defaults ([lesson 7](#/lesson/fastapi/pydantic-models)) and write a model validator
> ([lesson 8](#/lesson/fastapi/pydantic-validators)). Nothing about servers or deployment is assumed;
> environment variables are explained from the beginning.

## In plain words

A program needs some facts that are not part of its logic: the address of its database, a password,
the path of a file to load, whether extra logging is on. These facts are its **configuration**. They
differ from one place the program runs to another. On your laptop the database is a toy on the same
machine; on the company's servers it is the real one holding customer data.

An everyday picture: a new employee's first-day card. The job is the same in every office of the
company, but the card says which building, which desk and which door code apply *here*. Nobody
rewrites the job description for each office, and nobody prints the door code in the public
handbook. Configuration is that card. The handbook is your code.

This lesson shows how a FastAPI program reads its card safely: one typed class, named `Settings`,
that is filled from outside the code when the program starts, and that refuses to start when
something is missing or wrong.

Why this matters for a job: passwords committed to a code repository are one of the most common real
security incidents, and "how do you manage configuration and secrets?" is a routine interview
question. The method here is also the place where settings for database connections, logins and
machine-learning models live in every later lesson.

## Three ways to hold configuration, two of them bad

**Writing values into the code** ("hard-coding") is wrong for two reasons. A password in the source
ends up in **Git**, the version-control system that keeps every past version of every file, where
everyone with access to the repository can read it forever. And the value cannot differ between your
laptop and the production servers without editing code.

The usual fix is the **environment variable**: a named text value that the operating system hands to
a program when it starts. Every operating system and hosting platform supports them. You can read one
in Python with `os.getenv("DATABASE_URL", "default")`.

But scattering `os.getenv` calls all through a codebase is fragile. A misspelled name silently gives
the default. Every value is text, so `"false"` counts as true. And there is no single place that
lists what the program needs.

The FastAPI world's answer is **pydantic-settings**: a `Settings` class that is an ordinary Pydantic
model, except that its fields are filled from environment variables. You get types, validation and
one list of everything the program needs.

## The twelve-factor principle

The *Twelve-Factor App* is a widely cited list of rules for building software that runs well on
servers. Rule three says: *store config in the environment*. The idea is that one and the same built
package of your program (for example a Docker image, lesson 25) runs in every **environment**:
development ("dev", your own machine), staging (a rehearsal copy of the real system) and production
("prod", the system real users reach). Only the environment variables differ. The benefits:

- Secrets (passwords, keys) never live in the repository.
- Changing a setting does not require rebuilding the program.
- Every platform (Docker, Kubernetes, plain Linux services, cloud hosting) can supply environment
  variables.

Lubanovic's production chapter makes the same point in passing: configuration and secrets should come
from outside the code, so that the deployment, not the source, decides where the database lives.

## pydantic-settings

```bash
pip install pydantic-settings
```

```python
# app/config.py
from functools import lru_cache
from pydantic import Field, SecretStr, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",              # read a local .env file if present
        env_prefix="APP_",            # APP_DATABASE_URL -> database_url
        env_nested_delimiter="__",    # APP_REDIS__HOST -> redis.host
        extra="ignore",
    )

    app_name: str = "House Price API"
    environment: str = "dev"                     # dev | staging | prod
    debug: bool = False
    database_url: PostgresDsn
    secret_key: SecretStr                        # required: no default -> fails fast if missing
    access_token_expire_minutes: int = Field(30, ge=1)
    cors_origins: list[str] = []                 # JSON in env: APP_CORS_ORIGINS='["https://a.com"]'
    model_path: str = "models/model.joblib"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Reading the file:

- `class Settings(BaseSettings):` is a model whose values come from the environment.
- `model_config = SettingsConfigDict(...)` configures the loading. `env_file=".env"` also reads a
  local file named `.env` when one exists (explained below). `env_prefix="APP_"` means the field
  `database_url` is filled from the variable `APP_DATABASE_URL`; a prefix avoids clashes with other
  programs' variables. `env_nested_delimiter="__"` lets `APP_REDIS__HOST` fill a nested field
  `redis.host`. `extra="ignore"` skips unknown variables.
- The fields follow. Those with a default (`app_name`, `debug`) are optional. `database_url` and
  `secret_key` have **no default**, so they are required.
- `PostgresDsn` is a Pydantic type for a database address (DSN means "data source name"); it rejects
  text that is not a valid PostgreSQL address. `SecretStr` is the self-hiding text type from lesson 7.
- `get_settings()` creates the object. `@lru_cache` is a standard-library decorator that remembers a
  function's result: the first call builds `Settings`, and every later call returns that same object
  without reading anything again.

Where does each value come from? pydantic-settings checks several sources and takes the first that
has the value, in this order:

1. Arguments passed directly to `Settings(...)` (handy in tests).
2. Environment variables (upper or lower case both match, with the prefix).
3. The `.env` file.
4. A secrets directory (`secrets_dir="/run/secrets"`), where Docker and Kubernetes can place one file
   per secret.
5. The field's default.

Because this is a Pydantic model, values are **typed and validated when the program starts**.
`APP_DEBUG=yes` becomes `True`. `APP_ACCESS_TOKEN_EXPIRE_MINUTES=abc` stops the program immediately
with a clear error. A missing `APP_SECRET_KEY` prevents the program from starting at all, which is far
better than a failure hours later when the first user tries to log in. This behaviour has a name,
**fail fast**, and it is a feature.

## How it works: a mini implementation

`pydantic-settings` is not available in this browser, but its central idea is small enough to build
with plain Pydantic, and building it makes the mechanism concrete:

```python-run
import json, os
from pydantic import BaseModel, Field, SecretStr, ValidationError

class MiniSettings(BaseModel):
    """Toy BaseSettings: fills fields from os.environ using a prefix."""
    app_name: str = "House Price API"
    debug: bool = False
    secret_key: SecretStr
    access_token_expire_minutes: int = Field(30, ge=1)
    cors_origins: list[str] = []

    @classmethod
    def from_env(cls, prefix="APP_", environ=os.environ, **overrides):
        data = {}
        for name, field in cls.model_fields.items():
            key = (prefix + name).upper()
            if key in environ:
                raw = environ[key]
                # complex types (lists/dicts) are given as JSON, like pydantic-settings does
                if raw.startswith(("[", "{")):
                    raw = json.loads(raw)
                data[name] = raw
        data.update(overrides)            # explicit arguments win
        return cls.model_validate(data)

env = {"APP_DEBUG": "true", "APP_SECRET_KEY": "s3cr3t-from-vault",
       "APP_CORS_ORIGINS": '["https://app.example.com"]', "UNRELATED": "x"}
s = MiniSettings.from_env(environ=env)
print(s)                                   # SecretStr is masked in repr and logs
print("real secret:", s.secret_key.get_secret_value())

try:
    MiniSettings.from_env(environ={"APP_ACCESS_TOKEN_EXPIRE_MINUTES": "0"})
except ValidationError as e:
    print("fail fast at startup:")
    for err in e.errors():
        print("  ", err["loc"], err["type"])
```

- `MiniSettings` is a normal model. Its class method `from_env` does the loading.
- `cls.model_fields` is a dictionary of the model's fields. For each field name the loop builds the
  variable name (`APP_` + name, upper-cased) and looks it up in `environ`, a dictionary that stands in
  for the real environment.
- A value starting with `[` or `{` is parsed as JSON, which is how lists and dictionaries are written
  in environment variables.
- `data.update(overrides)` lets explicit arguments win, and `cls.model_validate(data)` performs the
  usual Pydantic checking.

The first print shows the loaded settings: `debug=True` (from the text `"true"`), the origin list
parsed from JSON, and `secret_key=SecretStr('**********')`, hidden. `UNRELATED` was ignored because it
lacks the prefix. The second print reveals the secret on purpose with `get_secret_value()`. The final
block passes an environment with an expiry of `0` and no secret key, and prints two errors: `missing`
for `secret_key` and `greater_than_equal` for the expiry. A real program would stop there, at
start-up.

## Using settings in FastAPI

There are two common patterns.

**1. As a dependency.** A *dependency* in FastAPI is something an endpoint declares that it needs,
which FastAPI then supplies. Lesson 10 teaches the mechanism in full; the shape is simple enough to
preview here:

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()
SettingsDep = Annotated[Settings, Depends(get_settings)]

@app.get("/info")
def info(settings: SettingsDep):
    return {"app_name": settings.app_name, "environment": settings.environment}
```

`Depends(get_settings)` means "before calling this endpoint, call `get_settings` and pass the result
in". `SettingsDep` is a short name for that annotation. The endpoint receives a ready `Settings`
object as its `settings` parameter. The FastAPI documentation recommends this pattern because the
function behind a dependency can be swapped in tests.

**2. As a module-level object.** Write `settings = Settings()` once in `config.py` and import it
wherever needed. An object that exists exactly once in a program is called a **singleton**. This is
shorter, but harder to replace in tests; you end up patching module attributes while tests run.

With the dependency pattern, a test swaps the function:

```python
def get_settings_override():
    return Settings(database_url="postgresql://test@localhost/test", secret_key="test")

app.dependency_overrides[get_settings] = get_settings_override
```

`app.dependency_overrides` is a dictionary on the app: "whenever `get_settings` is asked for, call
this other function instead". Lesson 11 returns to it.

## `.env` files

Typing a dozen variables into a terminal for every development session is tedious. A `.env` file is
a plain text file of `NAME=value` lines that pydantic-settings reads at start-up:

```dotenv
# .env  (never commit real secrets; commit a .env.example instead)
APP_ENVIRONMENT=dev
APP_DEBUG=true
APP_DATABASE_URL=postgresql://app:app@localhost:5432/app
APP_SECRET_KEY=dev-only-not-secret
APP_CORS_ORIGINS=["http://localhost:5173"]
```

Conventions that prevent pain:

- List `.env` in `.gitignore`, the file that tells Git what not to store. Commit a `.env.example`
  that names every variable with harmless dummy values, so that a new colleague knows what to fill in.
- Real environments (staging, production) receive their variables from the platform's secret store
  (Kubernetes Secrets, AWS Secrets Manager, Vault, Docker secrets), not from a `.env` file packed into
  the image.
- Never copy `.env` into a Docker image; exclude it with `.dockerignore`.

## Secrets hygiene

- Give secrets the type `SecretStr`. They then print as `**********` in logs, error traces and
  `repr`; call `.get_secret_value()` only at the point of use.
- Never return settings from an endpoint (no `return settings` in a debugging route).
- Change secrets periodically (this is called *rotation*), and design so that an old and a new key
  can both be valid while the change is in progress.
- Generate keys with a cryptographically secure random generator, never by typing something
  memorable: `openssl rand -hex 32` or
  `python -c "import secrets; print(secrets.token_hex(32))"`.

```python-run
import secrets
from pydantic import BaseModel, SecretStr

class S(BaseModel):
    api_key: SecretStr

s = S(api_key=secrets.token_urlsafe(32))
print(s)                       # masked
print(s.model_dump())          # still masked in dumps
print(s.model_dump_json())     # and in JSON
print(len(s.api_key.get_secret_value()), "chars of real key available when you ask explicitly")
```

`secrets.token_urlsafe(32)` produces a random key. Printing the model, dumping it to a dictionary and
dumping it to JSON all show stars in place of the key. Only the last line, which asks explicitly,
gets at the real value (and prints only its length, 43 characters).

## Environment-specific behaviour

A program often needs to behave differently depending on where it runs: the `/docs` page on in
development and off in production, readable logs in development and machine-readable logs in
production.

```python
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    openapi_url="/openapi.json" if settings.environment != "prod" else None,
)
```

Here the documentation is switched off when the environment is `prod`. Prefer *explicit switches*
(`docs_enabled: bool`) over scattering `if environment == "prod"` tests through the code. A named
switch is easier to test and to reason about.

## Nested settings

Related settings can be grouped into a nested model, filled through the delimiter configured earlier:

```python
class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_nested_delimiter="__")
    redis: RedisSettings = RedisSettings()

# APP_REDIS__HOST=cache.internal APP_REDIS__PORT=6380
```

The comment at the bottom shows the variables: `APP_REDIS__HOST` fills `settings.redis.host`. (Redis
is a fast in-memory data store, lesson 18.)

## Settings for ML services

A program that serves a machine-learning model has configuration of its own, and it is worth making
it explicit and typed:

```python
class ModelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODEL_")
    name: str = "house-price"
    version: str = "2025-01-15"
    uri: str = "s3://models/house-price/2025-01-15/model.joblib"
    device: Literal["cpu", "cuda"] = "cpu"
    max_batch_size: int = Field(32, ge=1, le=1024)
    max_wait_ms: int = Field(5, ge=0)
    warmup: bool = True
```

Keeping the model **version** in settings, not in code, means a new model is released by changing one
variable and restarting, and the version can be repeated in every prediction response so that results
are traceable. The limits (`max_batch_size` at most 1024) stop a typing slip by an operator from
exhausting the memory of a graphics card.

## Testing your configuration

Because `Settings` is a Pydantic model, its rules can be tested like any other code: that a bad
environment is rejected, that defaults are sensible, that secrets are hidden. These tests use
`pytest`, the standard Python test tool (lesson 22):

```python
def test_missing_secret_fails(monkeypatch):
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)          # ignore any local .env during the test

def test_debug_parsing(monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "x")
    monkeypatch.setenv("APP_DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("APP_DEBUG", "yes")
    assert Settings(_env_file=None).debug is True
```

`monkeypatch` is a pytest helper that changes environment variables for the duration of one test and
restores them afterwards. `Settings(_env_file=None)` tells the class to ignore any local `.env`. The
first test asserts that a missing secret raises `ValidationError`; the second that `"yes"` is read as
`True`.

Remember to clear the cache (`get_settings.cache_clear()`) between tests that change the environment.
Otherwise the object built by the first test is reused.

> [!INTERVIEW]
> "How do you manage configuration and secrets in a FastAPI service?" — A typed `BaseSettings` class
> from pydantic-settings, filled from environment variables (and a git-ignored `.env` in development),
> validated at start-up so that misconfiguration fails fast. Secrets are `SecretStr` and come from the
> platform's secret manager. Settings are provided through a cached dependency (`@lru_cache` plus
> `Depends(get_settings)`), so tests can replace them through `app.dependency_overrides`.

## Worked example: source precedence, step by step

Suppose the class declares `debug: bool = False` and `log_level: str = "INFO"`. The `.env` file
contains `APP_DEBUG=true` and `APP_LOG_LEVEL=DEBUG`. The real environment has
`APP_LOG_LEVEL=WARNING`. Which values win? The demo reproduces the lookup order and reports the
source of each value:

```python-run
import os
from pydantic import BaseModel

class Settings(BaseModel):
    debug: bool = False
    log_level: str = "INFO"
    workers: int = 1

def load(init_kwargs, environ, dotenv_text, prefix="APP_"):
    """Resolve each field from the highest-priority source that has it; report where it came from."""
    dotenv = dict(line.split("=", 1) for line in dotenv_text.strip().splitlines()
                  if line.strip() and not line.startswith("#"))
    values, origin = {}, {}
    for name in Settings.model_fields:
        key = (prefix + name).upper()
        for label, source, k in (("init argument", init_kwargs, name),
                                 ("environment", environ, key),
                                 (".env file", dotenv, key)):
            if k in source:
                values[name], origin[name] = source[k], label
                break
        else:
            origin[name] = "class default"
    return Settings.model_validate(values), origin

dotenv_text = """
# local development overrides
APP_DEBUG=true
APP_LOG_LEVEL=DEBUG
"""
settings, origin = load({}, {"APP_LOG_LEVEL": "WARNING", "PATH": "/usr/bin"}, dotenv_text)
for field, value in settings.model_dump().items():
    print(f"{field:10} = {value!r:10} from {origin[field]}")

print("--- a test passes an explicit argument ---")
settings, origin = load({"debug": False}, {"APP_LOG_LEVEL": "WARNING"}, dotenv_text)
print("debug =", settings.debug, "from", origin["debug"])
```

`load` parses the `.env` text into a dictionary, then for each field tries three sources in priority
order (explicit arguments, the environment, the `.env` file) and stops at the first that has the
value. If none has it, the class default applies. The output:

- `debug = True` from the `.env` file (nothing higher mentioned it).
- `log_level = 'WARNING'` from the environment, even though the `.env` file says `DEBUG`.
- `workers = 1` from the class default.
- In the second run a test passes `debug=False` directly, and that beats the `.env` file.

The real environment beating the `.env` file is deliberate: a `.env` file left behind in an image or
a working folder can never override what the platform supplies. If a value "refuses to change"
however you edit `.env`, a variable exported in your shell is usually hiding it. The command
`printenv | grep APP_` settles the question in seconds.

## Parsing rules worth knowing

Environment variables are always text. pydantic-settings converts them according to the field types:

| Field type | Environment value | Result |
|---|---|---|
| `bool` | `true`, `1`, `yes`, `on` (any case) | `True` |
| `int` / `float` | `"8"`, `"0.25"` | `8`, `0.25` |
| `list[str]` | `'["a","b"]'` (JSON) | `["a", "b"]` |
| `dict[str, int]` | `'{"a": 1}'` (JSON) | `{"a": 1}` |
| nested model | `APP_REDIS__PORT=6380` with `env_nested_delimiter="__"`, or one JSON value | `settings.redis.port == 6380` |
| `SecretStr` | any string | masked wrapper |
| `Literal["dev","prod"]` / `Enum` | `prod` | validated choice |

A comma-separated list (`APP_CORS_ORIGINS=https://a.com,https://b.com`) is not JSON and fails with a
parsing error. Either write JSON, or declare the field as `Annotated[list[str], NoDecode]` and add a
`field_validator(mode="before")` that splits on commas.

The variable name for a single field can be set with `Field(validation_alias="DATABASE_URL")`, which
helps when the hosting platform dictates a name without your prefix. Matching ignores case unless you
set `case_sensitive=True`.

## Cross-field rules for configuration

Configuration has rules that involve several values at once, and a model validator (lesson 8) can
enforce them at start-up instead of letting them surface as an incident in the middle of the night:

```python-run
from typing import Literal
from pydantic import BaseModel, SecretStr, ValidationError, model_validator

class Settings(BaseModel):
    environment: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    secret_key: SecretStr
    cors_origins: list[str] = []
    docs_enabled: bool = True

    @model_validator(mode="after")
    def production_safety(self):
        if self.environment == "prod":
            problems = []
            if self.debug:
                problems.append("debug must be off")
            if len(self.secret_key.get_secret_value()) < 32:
                problems.append("secret_key must be at least 32 characters")
            if "*" in self.cors_origins:
                problems.append("wildcard CORS origin is not allowed")
            if problems:
                raise ValueError("unsafe production config: " + "; ".join(problems))
        return self

print(Settings(secret_key="dev").environment, "- lenient in dev")
try:
    Settings(environment="prod", debug=True, secret_key="short", cors_origins=["*"])
except ValidationError as e:
    print(e.errors()[0]["msg"])
print(Settings(environment="prod", secret_key="k" * 40, cors_origins=["https://app.example.com"]).environment,
      "- accepted")
```

The validator only acts when `environment` is `prod`. It collects every problem it finds (debug mode
on, a secret shorter than 32 characters, a `*` wildcard among the allowed browser origins) and raises
one `ValueError` listing them all. The three lines of output: the development settings are accepted
with a short secret; the unsafe production settings are refused with all three problems named; the
safe production settings are accepted.

A deployment with a development secret or wide-open browser access now refuses to start, which is far
better than reading about it in a security audit.

## Feature flags and what does *not* belong in settings

Settings are read once, at start-up. That makes them the right place for things that change **per
deployment** (addresses, credentials, pool sizes, model version) and the wrong place for things that
must change **while the program is running**: an emergency off-switch, a feature being released to
10% of users, limits per customer. Those need a source that can be re-read, such as a database row,
Redis or a feature-flag service, reached through a dependency with a short cache. (A **feature flag**
is a switch that turns a piece of functionality on or off without changing code.) Fixed true/false
flags in settings are still valuable: they let you ship code switched off and turn it on with a
restart.

## Printing configuration safely

A log line at start-up that shows the configuration in force is extremely useful when you are asking
"which environment is this copy of the program really using?", provided that secrets stay hidden:

```python-run
from pydantic import BaseModel, SecretStr

class Settings(BaseModel):
    environment: str = "staging"
    database_url: SecretStr = SecretStr("postgresql://app:hunter2@db.internal/app")
    api_key: SecretStr = SecretStr("sk-live-123")
    pool_size: int = 10

s = Settings()
print("startup config:", s.model_dump_json())      # SecretStr fields stay masked automatically
print("NEVER do this :", {k: (v.get_secret_value() if isinstance(v, SecretStr) else v)
                           for k, v in s if k == "pool_size"})   # only reveal what you need
```

The first print shows the JSON dump with `"**********"` for both secret fields, with no special
effort. The second shows the disciplined way to reveal a value: select only what you need. Mark
anything that contains a credential as `SecretStr`, including whole database addresses with a
password in them, and the safe behaviour is the default one.

## Pitfalls

- Reading `os.environ` all over the codebase: no validation and no single list of what is needed.
- Creating `Settings()` on every request without caching (the `.env` file is re-read each time).
- Committing `.env`, or packing it into images.
- Logging the whole settings object when secrets are plain `str`.
- Writing lists or dictionaries in environment variables as comma-separated text. They must be JSON
  (`'["a","b"]'`) unless you add a validator.

## Summary

- Configuration belongs in the environment (twelve-factor); the same image runs everywhere.
- `pydantic-settings` gives a typed, validated `Settings` class filled from environment variables,
  `.env` files and secrets directories.
- Validate at start-up, so that missing or invalid configuration fails fast.
- Provide settings through an `lru_cache`d dependency so tests can replace them.
- Use `SecretStr`, git-ignore `.env`, and supply real secrets from a secret store.

## Glossary

- **Configuration** — values a program needs that differ between the places it runs.
- **Environment variable** — a named text value the operating system gives a program at start.
- **Hard-coding** — writing a configuration value directly into the source code.
- **Secret** — a configuration value that must stay private (password, key, token).
- **Environment (dev / staging / prod)** — one place a program runs: your machine, a rehearsal
  system, the real system.
- **Twelve-factor** — a well-known set of rules for server software; rule three is "config in the
  environment".
- **pydantic-settings / `BaseSettings`** — the package and base class for settings models.
- **`.env` file** — a local text file of `NAME=value` lines read at start-up.
- **`.gitignore`** — the file listing what Git must not store.
- **Fail fast** — stop immediately at start-up when something is wrong.
- **`lru_cache`** — a decorator that remembers a function's result for later calls.
- **Singleton** — an object that exists exactly once in a program.
- **`SecretStr`** — a text type that hides its value when printed.
- **Precedence** — the order in which sources are consulted; the first one with a value wins.
- **Rotation** — replacing a secret with a new one on a schedule.
- **Feature flag** — a switch that turns functionality on or off without a code change.

```quiz
[
  {"q": "With env_prefix='APP_', which variable populates the field 'database_url'?", "options": ["DATABASE_URL", "APP_DATABASE_URL", "app.database_url", "APP__DATABASE_URL"], "answer": 1,
   "explain": "The prefix is prepended to the field name; matching is case-insensitive by default."},
  {"q": "Why give secret_key no default value?", "options": ["Defaults are not allowed for strings", "So the application fails fast at startup if the secret isn't configured", "To make it optional", "For OpenAPI docs"], "answer": 1,
   "explain": "A required field makes Settings() raise immediately when the variable is missing, rather than failing later at runtime."},
  {"q": "What does @lru_cache on get_settings achieve?", "options": ["Encrypts the settings", "Builds the Settings object once and reuses it", "Reloads settings on every request", "Makes settings thread-local"], "answer": 1,
   "explain": "Without caching, every call would re-read env and .env; the cache returns the same instance."},
  {"q": "How should a list setting be provided in an environment variable for pydantic-settings?", "options": ["a,b,c", "JSON like '[\"a\",\"b\"]'", "Separate variables A_0, A_1", "It cannot be done"], "answer": 1,
   "explain": "Complex types are parsed from JSON strings by default."},
  {"q": "What is the benefit of SecretStr?", "options": ["It encrypts values at rest", "It masks the value in repr, logs and dumps unless explicitly revealed", "It validates password strength", "It stores the value in a vault"], "answer": 1,
   "explain": "SecretStr prevents accidental disclosure in logs and tracebacks; get_secret_value() reveals it on purpose."},
  {"q": "Which is the best way to provide production secrets to a containerised FastAPI app?", "options": ["COPY .env into the image", "Hard-code them in config.py", "Inject them as environment variables or mounted files from the platform's secret manager", "Put them in query strings"], "answer": 2,
   "explain": "Secrets should be injected at runtime by the platform, never baked into images or source."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 13 "Production" (Deployment, Docker); https://fastapi.tiangolo.com/advanced/settings/; https://docs.pydantic.dev/latest/concepts/pydantic_settings/; The Twelve-Factor App, "III. Config" (https://12factor.net/config)
