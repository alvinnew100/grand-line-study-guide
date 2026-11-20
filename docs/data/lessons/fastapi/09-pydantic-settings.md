# Settings and configuration management

Every service has configuration: database URLs, secret keys, model paths, feature flags, CORS origins,
log levels. Hard-coding them is wrong (secrets in Git, can't change per environment); sprinkling
`os.getenv("X", "default")` everywhere is fragile (typos, everything is a string, no single place to see
what the app needs). The FastAPI ecosystem's answer is **pydantic-settings**: a typed, validated
`Settings` class populated from environment variables and `.env` files.

## The twelve-factor principle

The Twelve-Factor App methodology says: *store config in the environment*. The same build artefact (a
Docker image) runs in dev, staging and production; only environment variables differ. Benefits:

- Secrets never live in the repository.
- Changing config doesn't require a rebuild.
- Every platform (Docker, Kubernetes, systemd, cloud run services) supports env vars.

Lubanovic's production chapter makes the same point in passing: configuration and secrets should come from
outside the code, so the deployment — not the source — decides where the database lives.

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

How values are resolved, highest priority first:

1. Arguments passed to `Settings(...)` explicitly (handy in tests).
2. Environment variables (case-insensitive by default, with the prefix).
3. Variables from the `.env` file.
4. Secrets directory files (`secrets_dir="/run/secrets"`, for Docker/Kubernetes secrets).
5. Field defaults.

Because it's a Pydantic model, values are **typed and validated** at startup: `APP_DEBUG=yes` becomes
`True`, `APP_ACCESS_TOKEN_EXPIRE_MINUTES=abc` fails immediately with a clear error, and a missing
`APP_SECRET_KEY` stops the app from booting rather than failing on the first login hours later. Failing
fast at startup is a feature.

## How it works — a mini implementation

`pydantic-settings` isn't available in this browser runtime, but its core idea is small enough to build
with plain Pydantic, which makes the mechanism concrete:

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

## Using settings in FastAPI

There are two common patterns:

**1. As a dependency** (recommended by the FastAPI docs, because it can be overridden in tests):

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()
SettingsDep = Annotated[Settings, Depends(get_settings)]

@app.get("/info")
def info(settings: SettingsDep):
    return {"app_name": settings.app_name, "environment": settings.environment}
```

`@lru_cache` makes `get_settings()` construct the object once (reading `.env` from disk only once) and
return the same instance afterwards.

**2. As a module-level singleton** (`settings = Settings()` in `config.py`, imported everywhere). Simpler,
but harder to override in tests — you end up monkeypatching.

In tests, override the dependency:

```python
def get_settings_override():
    return Settings(database_url="postgresql://test@localhost/test", secret_key="test")

app.dependency_overrides[get_settings] = get_settings_override
```

## `.env` files

```dotenv
# .env  (never commit real secrets; commit a .env.example instead)
APP_ENVIRONMENT=dev
APP_DEBUG=true
APP_DATABASE_URL=postgresql://app:app@localhost:5432/app
APP_SECRET_KEY=dev-only-not-secret
APP_CORS_ORIGINS=["http://localhost:5173"]
```

Conventions that save pain:

- Add `.env` to `.gitignore`; commit `.env.example` listing every variable with safe dummy values.
- Real environments (staging/prod) inject variables from the platform's secret store (Kubernetes
  Secrets, AWS Secrets Manager, Vault, Docker secrets), not from a `.env` file baked into the image.
- Never `COPY .env` into a Docker image (use `.dockerignore`).

## Secrets hygiene

- Type secrets as `SecretStr`: they print as `**********` in logs, tracebacks and `repr`; call
  `.get_secret_value()` only where needed.
- Don't expose settings through an endpoint (no `return settings` in a debug route!).
- Rotate secrets; design for multiple valid keys during rotation (e.g. JWT `kid` header).
- Generate keys with a CSPRNG: `openssl rand -hex 32` or `python -c "import secrets; print(secrets.token_hex(32))"`.

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

## Environment-specific behaviour

A common need is to vary behaviour by environment — enable `/docs` in dev but not in prod, verbose logs in
dev, JSON logs in prod:

```python
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    openapi_url="/openapi.json" if settings.environment != "prod" else None,
)
```

Prefer *explicit flags* (`docs_enabled: bool`) over scattering `if environment == "prod"` checks; flags are
easier to test and reason about.

## Nested settings

Group related settings with nested models and the `env_nested_delimiter`:

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

## Settings for ML services

Model-serving apps have their own configuration surface, and it is worth making it explicit and typed:

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

The model **version** in settings (rather than in code) means a new model ships by changing one variable and
restarting — no code change — and the version can be echoed in every prediction response for traceability.
Validation bounds (`max_batch_size <= 1024`) stop an operator typo from exhausting GPU memory.

## Testing your configuration

Because `Settings` is a Pydantic model, you can unit-test configuration rules directly — that misconfigured
environments are rejected, that defaults are sane, that secrets are masked:

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

Remember to clear the `lru_cache` (`get_settings.cache_clear()`) between tests that change the environment,
or the first test's settings will be reused.

> [!INTERVIEW]
> "How do you manage configuration and secrets in a FastAPI service?" — A typed `BaseSettings` class from
> pydantic-settings, populated from environment variables (and a git-ignored `.env` in dev), validated at
> startup so misconfiguration fails fast. Secrets are `SecretStr` and come from the platform's secret
> manager. Settings are provided through a cached dependency (`@lru_cache` + `Depends(get_settings)`), so
> tests can override them via `app.dependency_overrides`.

## Pitfalls

- Reading `os.environ` all over the codebase — no validation, no single source of truth.
- Instantiating `Settings()` per request without caching (re-reads `.env` each time).
- Committing `.env` or baking it into images.
- Logging the whole settings object with plain `str` secrets.
- Lists/dicts in env vars must be JSON (`'["a","b"]'`), not comma-separated (unless you add a validator).

## Summary

- Config belongs in the environment (twelve-factor); the same image runs everywhere.
- `pydantic-settings` gives a typed, validated `Settings` class from env vars, `.env` files and secrets dirs.
- Validate at startup → fail fast on missing/invalid config.
- Provide settings via an `lru_cache`d dependency so tests can override them.
- Use `SecretStr`, git-ignore `.env`, inject real secrets from a secret store.

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
