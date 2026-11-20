# Security misconfiguration and secrets management

> **Before this lesson:** read [The attacker's view: leaks and attack surface](#/lesson/web-security/attack-surface) for information disclosure and debug endpoints, and [Security headers, CSP and CORS](#/lesson/web-security/headers-csp-cors). You should know what an environment variable is in outline; it is explained below.

## In plain words

You buy a new safe. It arrives with the combination set to `0000`, the instruction leaflet taped to the door, and a little service hatch at the back left unlocked "for the installer". The safe is well made. Whether it protects anything depends entirely on what you do next: change the combination, remove the leaflet, lock the hatch.

Software arrives the same way. Web servers, databases, cloud storage, frameworks and admin tools ship with settings chosen to be *easy to start with*, not safe to run on the internet: sample accounts, debugging pages, everything listening on every network interface, generous permissions. **Security misconfiguration** means leaving such settings in place, or choosing unsafe ones — and it is consistently among the most common causes of real breaches, because it requires no bug in your code at all.

The combination itself is the second half of this lesson. Every application holds **secrets**: database passwords, API keys, signing keys. Writing the combination on the door — that is, putting secrets in source code — is one of the most frequent and most expensive mistakes in the industry. **Secrets management** is the discipline of keeping them out of code, limiting who can read them, and being able to change them quickly.

Neither topic is glamorous. Both are where a great deal of practical security is won or lost, and both come up in interviews as "what would you check before going to production?"

## Part 1: security misconfiguration

### What it looks like

Misconfiguration is a family, not a single bug. The common members:

| Category | Examples |
|---|---|
| **Debug features left on** | Framework debug mode; interactive error pages; verbose stack traces; profiling endpoints |
| **Default credentials** | `admin` / `admin` on a database, a router, a monitoring dashboard |
| **Unnecessary things enabled** | Sample applications, unused ports and services, directory listing, unneeded HTTP methods |
| **Over-broad access** | Storage buckets readable by the public; databases reachable from the internet; a firewall rule allowing `0.0.0.0/0` to an admin port |
| **Excessive permissions** | The application running as an administrator; a cloud role allowed to do everything |
| **Missing hardening** | No security headers; old TLS versions accepted; permissive CORS |
| **Stale software** | Unpatched servers and base images (next lesson) |
| **Inconsistent environments** | Production configured by hand, differently from what was tested |

### The simplest example: debug mode

```python
# VULNERABLE: development conveniences enabled for everyone on the internet
app = FastAPI(debug=True)                       # detailed error pages with source code
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

Three settings, each convenient on a laptop: debug mode shows a full stack trace in the browser on any error; the CORS line was added to silence an error during front-end development; `reload=True` restarts the server when files change. Some frameworks' debug pages go further and include an interactive console that runs code typed into the browser — on a public server, that is remote code execution offered as a feature.

```python
# FIXED: safe values are the default; conveniences must be switched on deliberately
import os

ENVIRONMENT = os.environ.get("APP_ENV", "production")       # unset means production
DEBUG = ENVIRONMENT == "development"

app = FastAPI(debug=DEBUG, docs_url="/docs" if DEBUG else None, redoc_url=None)
```

`os.environ.get("APP_ENV", "production")` reads a setting from the process's environment and falls back to `"production"` when it is missing. That fallback is the important design choice: **secure by default**. If someone forgets to configure a new server, it comes up locked down, not wide open. Interactive API documentation is disabled outside development by passing `None`.

### Secure defaults and failing closed

The same principle generalises. Compare two ways of reading a setting:

```python-run
def debug_enabled_risky(env: dict) -> bool:
    # Anything except the exact string "false" turns debugging ON
    return env.get("DEBUG", "true").lower() != "false"

def debug_enabled_safe(env: dict) -> bool:
    # Only an explicit, recognised "on" value enables debugging
    return env.get("DEBUG", "").strip().lower() in ("1", "true", "yes")

for env in [{}, {"DEBUG": "false"}, {"DEBUG": "False "}, {"DEBUG": "0"}, {"DEBUG": "true"}]:
    print(f"{str(env):22} risky -> {str(debug_enabled_risky(env)):5}  safe -> {debug_enabled_safe(env)}")
```

`env.get("DEBUG", "true")` returns the value of `DEBUG`, or the second argument when it is absent. The risky version is on when the variable is missing, on for `"False "` with a trailing space, and on for `"0"`. The safe version is off in all of those cases and on only when somebody clearly asked for it. When you review configuration code, look at what happens for the missing and the malformed case; that is where the default really lives.

### Validate configuration at start-up

A good application refuses to start with dangerous or incomplete settings — loudly, at deployment time, instead of quietly at 3 a.m.

```python-run
def check_config(config: dict) -> list:
    problems = []
    production = config.get("APP_ENV", "production") == "production"
    if production and config.get("DEBUG", "").lower() in ("1", "true", "yes"):
        problems.append("DEBUG must be off in production")
    key = config.get("SECRET_KEY", "")
    if len(key) < 32 or key.lower() in ("changeme", "secret", "dev"):
        problems.append("SECRET_KEY missing, too short or a placeholder")
    if production and not config.get("DATABASE_URL", "").startswith("postgresql+ssl://"):
        problems.append("DATABASE_URL must use an encrypted connection")
    if production and "*" in config.get("ALLOWED_HOSTS", "*"):
        problems.append("ALLOWED_HOSTS must list exact host names")
    return problems

bad = {"DEBUG": "true", "SECRET_KEY": "changeme", "DATABASE_URL": "postgresql://db/shop"}
good = {"APP_ENV": "production", "SECRET_KEY": "k" * 48,
        "DATABASE_URL": "postgresql+ssl://db.internal/shop", "ALLOWED_HOSTS": "shop.example"}

print("bad :", *check_config(bad), sep="\n   - ")
print("good:", check_config(good) or "ok - start the server")
```

Each rule appends a message when violated. In a real program the caller would print the list and exit with an error if it is not empty. The `bad` configuration fails four checks; the server would never start in that state.

### Hardening checklist

**Hardening** means reducing a system to what it needs and tightening what remains:

- Remove or disable sample content, unused features, ports, accounts and HTTP methods.
- Change every default password; better, disable password login for infrastructure in favour of keys or single sign-on.
- Bind internal services to private interfaces; expose only the load balancer.
- Run the application as an unprivileged user with a read-only file system where possible.
- Turn off directory listing and detailed errors; set the headers from the previous lesson.
- Accept only modern TLS versions.
- Apply the same rules to *every* environment — staging and "temporary demo" servers included.

### Cloud and infrastructure as code

In cloud platforms almost everything is configuration: who may read a storage bucket, which ports are open, what each machine's role may do. A single wrong setting — a bucket set to public, a database with a public address — exposes data without any application flaw.

The effective defence is to stop configuring by hand. **Infrastructure as code** means describing servers, networks and permissions in text files (Terraform, CloudFormation, Kubernetes manifests) kept in version control. That brings three benefits: changes are **reviewed** like code; environments are **identical** because they are built from the same files; and configuration can be **scanned automatically** for known-bad patterns before it is applied. Afterwards, tools continuously compare what is running with what the files say, and report **drift**.

```mermaid
flowchart LR
    D[Developer edits config files] --> R[Code review]
    R --> S[Automated config scan]
    S -->|pass| A[Apply to environment]
    S -->|fail| D
    A --> M[Continuous drift and posture monitoring]
    M -->|finding| D
```

> [!WARNING]
> "It's only the staging server" is how many incidents begin. Staging systems tend to hold copies of production data, are reachable from the internet for convenience, and receive the least attention. Give non-production environments synthetic data and the same hardening.

## Part 2: secrets management

### What counts as a secret

A **secret** is any value that grants access: database passwords, API keys for payment or email providers, session and token signing keys, encryption keys, private TLS keys, cloud access keys, webhook signing secrets, OAuth client secrets.

### How secrets leak

The simplest example is the most common real one:

```python
# VULNERABLE: credentials typed into the source file
import stripe
stripe.api_key = "<a live payment key pasted here>"      # placeholder for illustration
DATABASE_URL = "postgresql://shop_admin:Summer2026!@db.internal/shop"
```

Why this is so damaging:

- **Version control remembers.** Deleting the line in a later commit does not remove it from history; every clone of the repository still contains it.
- **Repositories spread.** Laptops, build servers, contractors, backups, a fork made public by accident. Automated scanners search public code hosts for key formats continuously, and leaked cloud keys are typically abused within minutes.
- **Everyone with code access gets production access**, whether or not they should.
- **Rotation requires a code change and a deployment**, so it does not happen.

Other leak routes: secrets printed in logs or error pages; passed as command-line arguments (visible in process lists); baked into container images or front-end bundles; pasted into chat or tickets; left in `.env` files that are committed or served by the web server.

### The fix, in three levels

**Level 1 — out of the code: environment variables.** An **environment variable** is a named value the operating system hands to a process when it starts. The code reads the name; the value is supplied by the deployment system.

```python
# FIXED (level 1): the code names the secret; the platform provides it
import os

stripe.api_key = os.environ["STRIPE_API_KEY"]            # KeyError at start-up if missing: fail fast
DATABASE_URL = os.environ["DATABASE_URL"]
```

`os.environ["NAME"]` raises an error when the variable is not set, so a misconfigured deployment stops immediately. For local development, values live in a `.env` file that is listed in `.gitignore` (so git never records it), with a committed `.env.example` containing placeholders only.

**Level 2 — a secrets manager.** Dedicated services (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, Google Secret Manager, Kubernetes secrets with encryption enabled) store secrets encrypted, release them only to identities that are authorised, record every access in an audit log, and support **rotation** — replacing a secret on a schedule or on demand. The application authenticates as *itself* (through its cloud role) and fetches what it needs at start-up.

**Level 3 — no long-lived secrets at all.** The best secret is one that expires in an hour. Cloud platforms can issue short-lived credentials to a workload based on its identity; databases can generate temporary per-application accounts; build pipelines can obtain deployment access through identity federation (OIDC) instead of stored keys. A leaked value is then useless almost at once.

### Principles that apply at every level

- **Least privilege per secret.** The email-sending key should be able to send email — not read the billing account. Use separate keys per service and per environment; never share production secrets with development.
- **Rotate**, routinely and whenever someone with access leaves or a leak is suspected. Design for it: support two valid keys during a changeover.
- **Never log secrets.** Redact `Authorization` headers, cookies and known secret fields in logging (see [Logging, monitoring and vulnerability management](#/lesson/web-security/logging-vuln-management)).
- **Keep server secrets on the server.** Anything in a JavaScript bundle or mobile app is public. A front-end key must be one *designed* to be public and restricted by origin or scope.
- **Encrypt in transit and at rest**, with keys held in a key-management service.

### Detecting leaked secrets

Because mistakes happen, add automated detection. **Secret scanning** tools search text for the recognisable shapes of credentials — fixed prefixes, lengths and character sets — and for suspicious assignments. Run them in three places: as a **pre-commit hook** on the developer's machine, in **continuous integration** on every change, and across the **whole repository history**.

A miniature scanner shows the idea:

```python-run
import re

RULES = {
    "private key":          re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
    "cloud access key id":  re.compile(r"(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])"),
    "hard-coded credential": re.compile(
        r"(?i)(?:password|passwd|secret|api_key|token)[\"']?\s*[:=]\s*([\"'])([^\"']{8,})\1"),
}
PLACEHOLDERS = ("example", "changeme", "placeholder", "xxxx")

def scan(lines):
    findings = []
    for number, line in enumerate(lines, start=1):
        for kind, pattern in RULES.items():
            match = pattern.search(line)
            if not match:
                continue
            if kind == "hard-coded credential":
                value = match.group(2).lower()
                if value.startswith(("${", "<")) or any(word in value for word in PLACEHOLDERS):
                    continue                              # a placeholder, not a real secret
            findings.append((number, kind))
    return findings

source = [
    'DB_PASSWORD = "Summer2026!rain"',
    'DB_PASSWORD = os.environ["DB_PASSWORD"]',
    'API_KEY = "changeme-before-deploy"',
    "aws_access_key_id = " + "AKIA" + "IOSFODNN7EXAMPLE",
    "-----BEGIN " + "RSA PRIVATE KEY-----",
    "# remember to rotate the token every quarter",
]
for line_number, kind in scan(source):
    print(f"line {line_number}: {kind}")
```

Each rule is a regular expression. The key-ID rule looks for the prefix `AKIA` followed by exactly sixteen capital letters or digits; the look-arounds `(?<!…)` and `(?!…)` insist that no further such character sits on either side. The credential rule looks for a suspicious name, then `=` or `:`, then a quoted literal of at least eight characters; `\1` requires the closing quote to match the opening one. Lines 2, 3 and 6 are correctly ignored: reading from the environment is the right pattern, `changeme…` is a placeholder, and a comment mentioning the word "token" assigns nothing. (The access-key value used here is the well-known example from vendor documentation, assembled from two pieces so that this page itself does not trip scanners.)

### When a secret has leaked

The order of operations matters, and it is a popular interview question.

1. **Revoke or rotate the secret immediately.** Assume it has been copied. This is the only step that actually ends the exposure.
2. **Check logs** for use of the secret during the exposure window.
3. **Remove it** from the code and, where practical, from history — understanding that removal alone fixes nothing, because copies exist.
4. **Find out how it happened** and add the missing control (a pre-commit hook, a scanner, a narrower permission).

> [!TIP]
> Give every secret an owner, a purpose and a rotation date in a simple inventory. When someone asks "what does this key do, and what breaks if we rotate it?", the answer should take one minute, not one week. Unknown keys are never rotated, and never-rotated keys are the ones that leak.

> [!INTERVIEW]
> "Where do you keep API keys and database passwords?" Not in source code or images. Inject at runtime from environment variables at minimum, preferably fetched from a secrets manager using the workload's own identity, with least-privilege scoping, audit logging and rotation; prefer short-lived credentials. Separate secrets per environment. Add secret scanning in pre-commit and CI. If asked "a key was pushed to a public repository — what now?", lead with *rotate first*, then investigate, then clean up.

## Defence in depth

1. **Secure defaults** in code: unset means locked down.
2. **Start-up validation** of configuration; refuse to run when unsafe.
3. **Hardening** of every component and environment.
4. **Infrastructure as code**, reviewed and scanned; drift detection.
5. **Least privilege** for processes, cloud roles and each credential.
6. **Secrets out of code**; managed, audited, rotated; short-lived where possible.
7. **Automated scanning** for misconfiguration and for secrets.
8. **Network controls** so that a leaked database password is useless from outside.
9. **Monitoring** for use of credentials from unusual places.

## How to test for it

**In code and configuration review:**

- Search for `debug`, `DEBUG`, `reload`, `allow_origins`, `0.0.0.0`, `verify=False` (disabled TLS verification), `chmod 777`.
- For each setting read from the environment, check the default used when it is absent.
- Search for literals near `password`, `secret`, `key`, `token`; for connection strings with embedded credentials; for `.env`, `.pem` and key files in the repository.
- Check `.gitignore` and the container build's ignore file.
- Read infrastructure files for public buckets, open security groups and wildcard permissions (`"Action": "*"`).

**In testing your own systems:**

- Trigger an error in production-like mode and confirm the response is generic.
- Request `/docs`, `/debug`, `/.env`, `/.git/config`, `/server-status` and expect 404.
- Try default credentials on every admin interface you operate.
- Run a secret scanner (gitleaks, trufflehog) over the full history, and a configuration scanner (Checkov, tfsec, kube-bench or the cloud provider's own) over infrastructure files and live accounts.
- From outside your network, scan your own address range for open ports and compare with what you expect.

## Pitfalls

- **A setting that is safe only if someone remembers to set it.**
- **Hand-edited production servers** that no file describes.
- **Committing `.env`** "only this once" — the history keeps it. (Rotate.)
- **Environment variables shown on debug pages** or dumped into crash reports.
- **One shared key** for all services and environments.
- **Rotating in the vault but not in running processes**, which keep the old value until restarted.
- **Encrypting secrets in the repository with a key kept beside them.**
- **Secrets in build arguments or image layers**, recoverable by anyone who pulls the image.
- **Believing private repositories are safe places for secrets.**
- **Cloud roles with administrator rights** given "temporarily" to make a deployment work.

## Summary

- Misconfiguration is unsafe settings, not unsafe code: debug modes, defaults, open access, excess permissions, missing hardening.
- Make the secure state the default, validate configuration at start-up, harden every environment, and manage infrastructure as reviewed, scanned code.
- Secrets must never be in source code; version control and its copies remember them indefinitely.
- Inject secrets at runtime, preferably from a secrets manager with least privilege, audit logs and rotation; prefer short-lived credentials.
- Scan for secrets before and after commit, and when one leaks, rotate first.

## Glossary

- **Security misconfiguration** — insecure settings in software, servers or cloud resources.
- **Default credentials** — the user name and password a product ships with.
- **Debug mode** — a development setting exposing detailed errors or tooling.
- **Secure by default** — the safe behaviour applies unless deliberately changed.
- **Fail closed** — on error or missing configuration, the system denies or stops.
- **Hardening** — removing unnecessary functionality and tightening the rest.
- **Infrastructure as code** — defining infrastructure in version-controlled files.
- **Drift** — a difference between the intended and the actual configuration.
- **Secret** — any value that grants access, such as a password or key.
- **Environment variable** — a named value given to a process by its environment.
- **Secrets manager** — a service that stores, controls access to, audits and rotates secrets.
- **Rotation** — replacing a secret with a new one and retiring the old.
- **Short-lived credential** — one that expires automatically after minutes or hours.
- **Secret scanning** — automated search of code and history for credentials.
- **`.gitignore`** — a file listing paths that git must not record.

```quiz
[
  {"q": "Which of these is a security misconfiguration and not a coding bug?",
   "options": ["Concatenating user input into SQL", "Leaving the framework's debug mode enabled in production", "Missing output encoding in a template", "Using == to compare tokens"], "answer": 1,
   "explain": "Debug mode is a setting. The code can be flawless and the deployment still exposes internals or even code execution."},
  {"q": "A setting is read as env.get('DEBUG', 'true') != 'false'. What is wrong with this design?",
   "options": ["It is too slow", "Debugging is enabled whenever the variable is missing or has an unexpected value, so the default is insecure", "Environment variables cannot hold booleans", "Nothing"], "answer": 1,
   "explain": "Secure by default means the dangerous option requires an explicit, recognised value; absence and typos must fall to the safe side."},
  {"q": "Why is an application that refuses to start with an unsafe configuration a good thing?",
   "options": ["It reduces uptime", "The problem is discovered at deployment, loudly, instead of silently running in an unsafe state", "It hides errors from developers", "It saves memory"], "answer": 1,
   "explain": "Start-up validation turns configuration mistakes into immediate, visible failures."},
  {"q": "A database password was committed to git and removed in the next commit. Is it safe now?",
   "options": ["Yes, the file no longer contains it", "No: it remains in the repository history and in every clone, so it must be rotated", "Yes, if the repository is private", "Only if the commit message is edited"], "answer": 1,
   "explain": "Version control preserves history. The only real remedy for an exposed secret is to revoke or rotate it."},
  {"q": "What does a secrets manager provide beyond environment variables?",
   "options": ["Faster code", "Encrypted storage, access control per identity, audit logs and rotation", "Automatic bug fixing", "Source code hosting"], "answer": 1,
   "explain": "It centralises secrets with fine-grained access, records who read what, and makes changing them practical."},
  {"q": "A secret key for a payment provider is found in the public JavaScript bundle. What does this mean?",
   "options": ["It is safe because the code is minified", "Anyone can read it; server-side secrets must never be shipped to the browser", "It is safe over HTTPS", "Only logged-in users can see it"], "answer": 1,
   "explain": "Everything delivered to a client is public. Only keys designed to be public and restricted may appear there."},
  {"q": "An access key was pushed to a public repository ten minutes ago. What is the first action?",
   "options": ["Delete the commit", "Revoke or rotate the key", "Make the repository private", "Wait to see whether it is abused"], "answer": 1,
   "explain": "Assume it was copied. Only invalidating the key ends the exposure; cleaning history and investigating follow."},
  {"q": "What is the main security benefit of infrastructure as code?",
   "options": ["It makes servers faster", "Configuration is reviewed, repeatable and automatically scannable, with drift detectable afterwards", "It removes the need for passwords", "It encrypts all traffic"], "answer": 1,
   "explain": "Treating configuration like code brings review, consistency between environments and automated checks."}
]
```

> **Source:** Hoffman, *Web Application Security*, ch. 18 (secure credentials and architecture), ch. 19 (secure-coding anti-patterns) and ch. 7 (signals of insecure architecture), extended in original wording. OWASP Top 10 A05 Security Misconfiguration — https://owasp.org/Top10/A05_2021-Security_Misconfiguration/ ; OWASP Secrets Management Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html ; OWASP Infrastructure as Code Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheat_Sheet.html ; OWASP Top 10 A02 Cryptographic Failures — https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
