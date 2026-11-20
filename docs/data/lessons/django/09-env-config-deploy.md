# Deploying with environment variables

> **Before this lesson:** the `lostfound` project lists items from the database ([ListView, querysets and tests with a database](#/lesson/django/listview-querysets)) and is committed to Git ([Git, requirements and a tidy project folder](#/lesson/django/setup-git-project)). You have met the settings `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` and `DATABASES` in [Projects, apps and the settings file](#/lesson/django/project-vs-app).

## In plain words

The same code has to run in at least two places: on your laptop while you develop, and on a server where the public uses it. The code is identical; a handful of facts differ. On the laptop, show detailed error pages; on the server, never. On the laptop, use a throw-away database file; on the server, use the real database with its password.

Those differing facts are **configuration**. The widely adopted rule is: *code goes in the repository, configuration comes from the environment*. An **environment variable** is a named piece of text that the operating system hands to a program when it starts. The program reads it; the repository never contains it.

An everyday picture: a chain of cafés using one recipe book. The recipes (code) are the same in every branch. The alarm code, the supplier's phone number and the opening hours (configuration) are written on a card kept in each branch's office, not printed in the book.

Why it matters for a job: leaked secrets in repositories are among the most common real-world security incidents, and "how do you manage settings across environments?" is a routine interview question. Every hosting platform you will meet expects configuration through environment variables.

## The problem in the generated settings

Look at what `startproject` wrote:

```python
# config/settings.py (as generated)
SECRET_KEY = "django-insecure-4k!x..."
DEBUG = True
ALLOWED_HOSTS = []
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
```

Four problems for a public site:

1. The secret key is in Git, so everyone with access to the repository can forge signed data such as session cookies.
2. `DEBUG = True` shows source code and settings to any visitor who triggers an error.
3. `ALLOWED_HOSTS` is empty, which is only accepted while `DEBUG` is on.
4. The database is a local file. Many hosting platforms wipe the application's disk on every release, so the data would vanish.

## Step 1: reading the environment in Python

Python exposes environment variables as the dictionary-like object `os.environ`:

```python
import os

os.environ["HOME"]                     # raises KeyError if the variable is not set
os.environ.get("DJANGO_DEBUG")         # returns None if it is not set
os.environ.get("DJANGO_DEBUG", "0")    # returns "0" if it is not set
```

One fact causes most beginner bugs: **every environment variable is a string**. There is no boolean `False`, only the text `"False"`. And in Python any non-empty string counts as true:

```python-run
import os

os.environ["DJANGO_DEBUG"] = "False"          # what an operator would type

naive = bool(os.environ.get("DJANGO_DEBUG"))  # WRONG: any non-empty text is truthy
print("naive reading :", naive)

def env_bool(name, default=False):
    """Read a boolean setting written as text."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

print("careful reading:", env_bool("DJANGO_DEBUG"))

def env_list(name, default=""):
    """Read 'a.example, b.example' as ['a.example', 'b.example']."""
    return [part.strip() for part in os.environ.get(name, default).split(",") if part.strip()]

os.environ["DJANGO_ALLOWED_HOSTS"] = "lostfound.example, www.lostfound.example"
print(env_list("DJANGO_ALLOWED_HOSTS"))
print(env_list("NOT_SET"))                    # an unset variable gives an empty list
```

The naive line prints `True`: a server configured with `DJANGO_DEBUG=False` would run in debug mode. The two helper functions are all you need for a small project.

## Step 2: settings that read the environment

Rewrite the four risky settings. Each line is explained below.

```python
# config/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [part.strip() for part in os.environ.get(name, default).split(",") if part.strip()]


DEBUG = env_bool("DJANGO_DEBUG", default=False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-key-not-for-production"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY is not set")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
```

- `DEBUG` defaults to **`False`**. Safe defaults mean that forgetting to configure a server produces a locked-down site, not an exposed one. You switch debug on explicitly on your laptop.
- `SECRET_KEY` has no usable default in production: if the variable is missing, the program stops with a clear message at start-up. A site that refuses to start is better than one that runs with a publicly known key.
- `ALLOWED_HOSTS` is a comma-separated list in one variable.
- `CSRF_TRUSTED_ORIGINS` lists origins, including the scheme (`https://lostfound.example`), from which form submissions are accepted. It is needed when the site sits behind a proxy or uses several domains; the forms module explains what it protects.

Generate a strong secret key with Django's own helper:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 3: a `.env` file for your laptop

Typing variables into the terminal each time is tedious. A **`.env` file** is a plain text file of `NAME=value` lines kept in the project root, loaded into the environment when the program starts, and **never committed** (it is in the `.gitignore` from the Git lesson).

```
# .env   (local machine only; listed in .gitignore)
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=local-development-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Python does not read this file by itself. Install a small loader and call it at the top of the settings:

```bash
python -m pip install python-dotenv
python -m pip freeze > requirements.txt
```

```python
# config/settings.py (top of the file, after the imports)
from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")
```

`load_dotenv` copies the file's entries into `os.environ` **without overwriting** variables that already exist. That gives a clear order of precedence: a real environment variable beats the `.env` file, which beats the default written in code.

```mermaid
flowchart TD
    A[Real environment variable set on the server or in the terminal] -->|highest priority| R[Value used by settings.py]
    B[.env file on the developer machine] -->|used if no real variable| R
    C[Default written in settings.py] -->|used if neither exists| R
```

Commit a file named `.env.example` containing the variable names with harmless placeholder values. It documents what a new colleague must set, without revealing anything.

> [!TIP]
> Packages such as `django-environ` and `environs` bundle the loader, the type conversions (`env.bool`, `env.list`, `env.int`) and URL parsing in one tool. They are worth adopting on real projects; the hand-written helpers above show that nothing magical is involved.

## Step 4: the database from one URL

Hosting platforms hand you database credentials as a single address in a variable conventionally called `DATABASE_URL`:

```
postgres://lostfound_user:s3cr3t@db.internal.example:5432/lostfound
```

Reading left to right: the kind of database, a user name and password, the server's host name and port, and the database name. **PostgreSQL** is the open-source database most Django sites use in production. The `dj-database-url` package converts such an address into the dictionary Django expects, and `psycopg` is the driver, the library Python uses to speak to PostgreSQL:

```bash
python -m pip install dj-database-url "psycopg[binary]"
python -m pip freeze > requirements.txt
```

```python
# config/settings.py
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}
```

`config()` reads `DATABASE_URL`. If the variable is absent it falls back to the SQLite file, so the laptop keeps working with no extra setup. `conn_max_age=600` keeps each database connection open for up to ten minutes instead of reconnecting on every request.

## Step 5: a production server and a start command

Install the server and a static-file helper (both explained fully in the deployment module):

```bash
python -m pip install gunicorn whitenoise
python -m pip freeze > requirements.txt
```

**Gunicorn** is a production-grade WSGI server: the program that receives requests and calls your Django code. The command that starts the site is:

```bash
gunicorn config.wsgi --bind 0.0.0.0:8000
```

`config.wsgi` is the module `config/wsgi.py` that `startproject` created. Platforms need to be told this command. Many read it from a one-line file called `Procfile` in the project root:

```
web: gunicorn config.wsgi
release: python manage.py migrate
```

The `web` line is the long-running process that serves requests. The `release` line runs once for each new version before it goes live; applying migrations there keeps the database in step with the code.

For static files, add WhiteNoise's middleware directly below the security middleware and name a folder for collected files:

```python
# config/settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # ... the rest unchanged ...
]

STATIC_ROOT = BASE_DIR / "staticfiles"
```

## Step 6: the deployment itself

The exact buttons differ per platform (Render, Fly.io, Railway, Heroku and others), but the sequence is the same everywhere:

1. **Push** the repository to your Git host.
2. **Create an app** on the platform and connect it to the repository.
3. **Attach a PostgreSQL database.** The platform sets `DATABASE_URL` for you.
4. **Set the environment variables** in the platform's dashboard or command-line tool:

   | Variable | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | the long random string you generated |
   | `DJANGO_DEBUG` | leave unset, or `false` |
   | `DJANGO_ALLOWED_HOSTS` | `lostfound.example` (the address the platform gives you) |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://lostfound.example` |

5. **Deploy.** The platform installs `requirements.txt`, runs `collectstatic`, runs the release command, then starts `gunicorn`.
6. **Create the first admin account** with the platform's "run a command" feature: `python manage.py createsuperuser`.

Before step 1, ask Django to audit the configuration as production would see it:

```bash
DJANGO_DEBUG=false DJANGO_SECRET_KEY=test python manage.py check --deploy
```

(On PowerShell set the variables first with `$env:DJANGO_DEBUG = "false"`.) The command lists warnings such as `security.W004` (no HTTP Strict Transport Security configured) and `security.W012` (session cookie not marked secure). Each has an explanation in the deployment checklist; the deployment module resolves them one by one.

```mermaid
flowchart LR
    L[Laptop: DEBUG on, SQLite, .env file] -- git push --> G[Git host]
    G --> P[Platform build: pip install, collectstatic]
    P --> R[Release: migrate]
    R --> W[Web process: gunicorn config.wsgi]
    E[Platform environment variables] --> W
    W --> DB[(PostgreSQL via DATABASE_URL)]
```

## Testing configuration code

Settings are code and deserve tests. The helper functions are pure functions, so `SimpleTestCase` suffices; `mock.patch.dict` temporarily changes the environment for one block.

```python
# board/test_settings_helpers.py
import os
from unittest import mock

from django.test import SimpleTestCase

from config.settings import env_bool, env_list


class EnvHelperTests(SimpleTestCase):
    def test_false_text_is_false(self):
        with mock.patch.dict(os.environ, {"FLAG": "False"}):
            self.assertFalse(env_bool("FLAG"))

    def test_missing_uses_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(env_bool("FLAG", default=True))

    def test_list_strips_and_drops_empties(self):
        with mock.patch.dict(os.environ, {"HOSTS": " a.example, ,b.example,"}):
            self.assertEqual(env_list("HOSTS"), ["a.example", "b.example"])
```

> [!NOTE]
> **What changed since the book.** The source book hard-codes `ALLOWED_HOSTS = ['*']` and installs packages with Pipenv before pushing to Heroku's free tier. Wildcard hosts are no longer recommended, Heroku's free tier ended in 2022, and since Django 4.0 `CSRF_TRUSTED_ORIGINS` entries must include the scheme. The environment-variable approach shown here is what current platforms and Django's own deployment checklist expect.

> [!INTERVIEW]
> **"How do you handle settings for different environments?"** One settings module that reads from environment variables, with safe defaults (`DEBUG` off, no fallback for the secret key outside development), a git-ignored `.env` file for local work and platform-managed variables in production. Mention the precedence (real environment over `.env` over code defaults), that everything arrives as a string and must be converted deliberately, and that failing fast at start-up on a missing required value is a feature. An alternative you should be able to name: a settings package with `base.py`, `local.py` and `production.py` selected through `DJANGO_SETTINGS_MODULE`.

> [!WARNING]
> Never paste real secrets into chat tools, screenshots, issue trackers or the `.env.example` file. Treat any secret that has left its intended store as leaked and rotate it.

## Pitfalls

- **`bool(os.environ.get("DEBUG"))`.** The text `"False"` is truthy. Compare against known words.
- **`DisallowedHost` after deploying.** The domain is missing from `DJANGO_ALLOWED_HOSTS`. Do not "solve" it with `["*"]`.
- **Forms fail with "CSRF verification failed" only in production.** The origin with its `https://` scheme is missing from `CSRF_TRUSTED_ORIGINS`.
- **Stale `requirements.txt`.** The build succeeds locally and fails remotely with `ModuleNotFoundError: gunicorn`.
- **Committing `.env`.** Check `git status` before the first commit that follows creating it.
- **Forgetting migrations on the server.** New code with an old schema crashes with "no such column"; a release command prevents it.
- **Keeping SQLite on a platform with an ephemeral disk.** Data disappears at the next release.

## Cheat sheet

| Need | Code or command |
|---|---|
| Read a variable | `os.environ.get("NAME", "default")` |
| Boolean from text | compare `.lower()` with `{"1", "true", "yes", "on"}` |
| List from text | split on commas, strip, drop empties |
| Load a `.env` file | `load_dotenv(BASE_DIR / ".env")` |
| New secret key | `get_random_secret_key()` |
| Database from a URL | `dj_database_url.config(default=..., conn_max_age=600)` |
| Start command | `gunicorn config.wsgi` |
| Apply migrations on release | `release: python manage.py migrate` |
| Production audit | `python manage.py check --deploy` |

## Summary

- Keep code in Git and configuration in the environment; the same commit must be deployable anywhere.
- Environment variables are strings: convert booleans and lists explicitly, and choose safe defaults.
- A git-ignored `.env` file serves the laptop; the hosting platform's variable store serves production; real variables override the file.
- `DATABASE_URL` plus `dj-database-url` switches databases without code changes.
- Deployment is: push, build, migrate, start Gunicorn, and audit with `check --deploy`.

## Glossary

- **Configuration**: values that differ between places where the code runs.
- **Environment variable**: a named string given to a process by its operating system.
- **`.env` file**: a local file of `NAME=value` lines loaded into the environment at start-up.
- **Secret**: a value that grants access or signing power, such as `SECRET_KEY` or a database password.
- **Precedence**: the order deciding which source wins when several define the same name.
- **PostgreSQL**: a widely used open-source relational database.
- **Driver**: the library a program uses to talk to a database (`psycopg` for PostgreSQL).
- **`DATABASE_URL`**: one address string holding all database connection details.
- **Gunicorn**: a production WSGI server for Python web applications.
- **Release command**: a command run once per deployment before the new version serves traffic.
- **Ephemeral disk**: storage that is erased when the application restarts or redeploys.

```quiz
[
  {"q": "An operator sets DJANGO_DEBUG=False. What does `bool(os.environ.get('DJANGO_DEBUG'))` return?",
   "options": ["False", "True", "None", "It raises an error"],
   "answer": 1,
   "explain": "Environment variables are strings, and the non-empty string 'False' is truthy. Compare the lower-cased text against known true words."},
  {"q": "With python-dotenv's default behaviour, which source wins when a name is defined in both the real environment and the .env file?",
   "options": ["The .env file", "The real environment variable", "Whichever was written last", "The default in settings.py"],
   "answer": 1,
   "explain": "load_dotenv does not override existing variables, so the real environment has the highest precedence."},
  {"q": "Why should DEBUG default to False in settings code?",
   "options": ["It makes development faster", "So that a server missing its configuration is locked down instead of exposing debug pages", "Django requires it", "It enables static files"],
   "answer": 1,
   "explain": "Safe defaults mean mistakes fail closed. Debug is switched on explicitly on a developer machine."},
  {"q": "What is the recommended behaviour when DJANGO_SECRET_KEY is missing in production?",
   "options": ["Fall back to the insecure key in the repository", "Generate a new random key on every start", "Stop at start-up with a clear error", "Disable sessions"],
   "answer": 2,
   "explain": "A known key allows forged cookies; a random key per start invalidates all sessions and breaks multi-process setups. Failing fast is the safe choice."},
  {"q": "What does `dj_database_url.config(default=...)` do?",
   "options": ["Creates the database", "Parses the DATABASE_URL variable into Django's DATABASES dictionary, using the default when it is unset", "Runs migrations", "Encrypts the connection"],
   "answer": 1,
   "explain": "It turns one URL into ENGINE, NAME, USER, PASSWORD, HOST and PORT entries."},
  {"q": "Which file should be committed to help colleagues know which variables to set?",
   "options": [".env", ".env.example with placeholder values", "db.sqlite3", "The platform's dashboard export with real values"],
   "answer": 1,
   "explain": "An example file documents names without containing secrets. The real .env stays ignored."},
  {"q": "After deploying, every page shows 'Bad Request (400)' and the log says DisallowedHost. What is the fix?",
   "options": ["Set DEBUG to True", "Add the site's domain to the allowed hosts variable", "Delete the migrations", "Restart the browser"],
   "answer": 1,
   "explain": "Django rejects requests whose Host header is not in ALLOWED_HOSTS. List the real domain; do not use a wildcard."},
  {"q": "What is the purpose of a release command such as `python manage.py migrate`?",
   "options": ["To start the web server", "To bring the database schema in line with the new code before it serves traffic", "To install packages", "To clear the cache"],
   "answer": 1,
   "explain": "New code usually expects new columns or tables; applying migrations as part of each release keeps code and schema in step."}
]
```

> **Source:** Vincent, *Django for Beginners*, ch. 4 (Message Board app: Heroku configuration and deployment), rewritten for environment-based configuration. Docs: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ · https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-trusted-origins · https://12factor.net/config · https://docs.gunicorn.org/en/stable/run.html
