# Security foundations: principles, the five functions, secrets, patching and backups

## Before this lesson

> **Before this lesson:** read [From logical to physical and the principles of deployment](#/lesson/microservices/logical-to-physical), for infrastructure as code and automation, and [Continuous integration and build pipelines](#/lesson/microservices/ci-pipelines). No security background is assumed.

## In plain words

Think about how a veterinary clinic is protected. There is a lock on the front door, and nobody relies on that lock alone. The controlled medicines are in a locked cabinet inside a locked room. Each member of staff has keys only for the rooms their job needs: the receptionist cannot open the drug cabinet. There is an alarm, and a camera, so that a break-in is noticed. There is a plan for what to do afterwards: whom to call, how to check what is missing. And the clinic's records are copied somewhere else, in case of fire.

No single measure makes the clinic safe. The combination does, and the combination covers more than keeping intruders out: it includes noticing, reacting and recovering.

Securing software works the same way. Moving to microservices changes the picture in two directions. There are now many more doors: more services, more network connections, more machines, more things to keep up to date. This larger exposed area is called the **attack surface**. On the other hand there are also many more internal walls. A break-in to one small service need not give access to everything, where a break-in to a monolith often does.

Why this matters for a job: security is part of every engineer's work, and interviewers expect candidates for backend roles to know the basic principles and the common failures: secrets in source code, unpatched libraries and credentials with far too much access.

## 1. Three core principles

### Least privilege

The **principle of least privilege** says: give each person and each program the minimum access needed to do its job, for the shortest time needed.

If the Reminders service only reads appointment times, its database account should have read access to that one table. If an attacker takes over Reminders, the credentials they find allow very little. The amount of damage a single compromise can cause is called the **blast radius**, and least privilege is how you keep it small.

```python-run
# Which tables can each stolen credential reach?
ALL_TABLES = ["appointments", "patients", "prescriptions", "invoices", "card_tokens", "staff"]

shared_account = {svc: ALL_TABLES for svc in ["reminders", "appointments", "billing", "pharmacy"]}
least_privilege = {
    "reminders":    ["appointments"],                       # read-only in practice
    "appointments": ["appointments", "patients"],
    "billing":      ["invoices", "card_tokens"],
    "pharmacy":     ["prescriptions", "patients"],
}

def blast_radius(grants, compromised):
    reachable = grants[compromised]
    return len(reachable), reachable

for label, grants in [("one shared database account", shared_account), ("one scoped account per service", least_privilege)]:
    n, tables = blast_radius(grants, "reminders")
    print(f"{label:31s}: attacker in Reminders reaches {n} of {len(ALL_TABLES)} tables {tables if n < 4 else '(everything)'}")
```

`shared_account` models the lazy arrangement: every service connects to the database with the same powerful account. `least_privilege` gives each service access to the tables it needs. `blast_radius` returns what an attacker can reach after taking over one service. With the shared account, a flaw in Reminders, the least important service, exposes card tokens and medical records. With scoped accounts it exposes appointment times. The flaw is the same; the consequence is very different.

### Defence in depth

**Defence in depth** means having several independent layers of protection, so that when one fails, another still stands. Every single measure will fail one day: a password is guessed, a firewall rule is wrong, a library has a flaw.

```mermaid
flowchart LR
  A[Attacker] --> L1[Edge: firewall and gateway]
  L1 --> L2[Network: services isolated from each other]
  L2 --> L3[Service: authentication and authorisation on every call]
  L3 --> L4[Data: encrypted, minimum access]
  L4 --> L5[Detection: logs and alerts]
  L5 --> L6[Recovery: backups and rebuild]
```

Microservices are well suited to this, because the system is already divided into small parts that can each be protected separately and placed in separate network zones.

It also helps to think of controls in three kinds:

| Kind | Purpose | Examples |
|---|---|---|
| Preventive | Stop an attack happening | Encryption, access checks, firewalls |
| Detective | Notice an attack in progress or afterwards | Central logs, intrusion detection, alerts |
| Responsive | Limit damage and recover | An incident plan, revoking credentials, restoring backups |

A design that has only preventive controls assumes they never fail.

### Automation

With thirty services there are thirty sets of credentials, hundreds of machines and thousands of library dependencies. Changing passwords by hand, patching by hand and reviewing firewall rules by hand does not keep up, and people make mistakes under pressure. Automation, the same principle as in deployment, is what makes least privilege and defence in depth affordable: credentials that are replaced automatically, patches that are detected and applied by the pipeline, infrastructure that is rebuilt from code.

### Build security into delivery

Security used to be a review at the end, done by a separate team. With frequent releases that cannot work. Put the checks into the pipeline (dependency scanning, secret scanning, static analysis that looks for dangerous code patterns) so that every commit is examined, and give developers enough training to recognise the common mistakes. Security specialists then spend their time helping teams and improving tools, instead of being a gate at the end.

## 2. The five functions of cybersecurity

The United States National Institute of Standards and Technology (NIST) publishes a widely used framework that divides security work into five functions. It is a helpful checklist because it stops you thinking only about prevention.

```mermaid
flowchart LR
  I[Identify] --> P[Protect] --> D[Detect] --> R[Respond] --> V[Recover]
  V -. lessons learned .-> I
```

| Function | Question | For Pawprint |
|---|---|---|
| Identify | Who might attack us, what do they want, and where are we weak? | Medical records and card data are the valuable assets; criminals seeking money are the likely attackers |
| Protect | How do we keep them out and limit what they can reach? | Encryption, least privilege, patching |
| Detect | How would we know an attack is happening? | Central logs, alerts on unusual access |
| Respond | What do we do when it happens? | A written, rehearsed plan: who decides, who tells customers and regulators |
| Recover | How do we get back to normal? | Restore from backups, rebuild services, rotate every credential |

**Identify** deserves a note, because it prevents wasted effort. **Threat modelling** is the exercise of looking at your system as an attacker would: what is worth stealing or disrupting, and which path to it is easiest? It tells you where to spend your limited time. Without it, teams tend to harden whatever is technically interesting while the real weak point is something dull, such as an administrator's reused password.

**Respond** and **recover** are the functions most often missing. Assume that a breach will happen one day. An organisation that has decided in advance who does what, and has practised it, limits the damage. One that improvises loses days.

## 3. Credentials

**Credentials** are what a person or program presents to prove who it is and gain access: passwords, keys, certificates. They are the most common way in for attackers. It is usually easier to obtain a valid credential than to break a system technically.

### User credentials

The people who operate the system (developers, administrators) hold powerful credentials. Basic measures:

- Use a password manager, so that every password is long, random and unique.
- Turn on **multi-factor authentication (MFA)**: logging in needs a second proof, such as a code from a phone app or a hardware key, as well as the password.
- Do not force frequent arbitrary password changes; current guidance (including NIST's) is that this leads to weaker passwords. Change them when there is reason to think they were exposed.
- Give administrators separate, limited accounts for daily work.

### Secrets

A **secret** is a credential used by a program: a database password, an API key for the text-message provider, the private key of a certificate. Microservices multiply them. Managing secrets well means meeting these needs:

| Need | Meaning |
|---|---|
| Creation | Secrets are generated by a tool, not invented by a person |
| Distribution | The right secret reaches the right service, and no other |
| Storage | Secrets are stored encrypted and are never written to logs |
| Monitoring | You can see who used which secret, and when |
| Rotation | Secrets are replaced regularly and automatically |
| Revocation | A secret can be cancelled immediately if it leaks |
| Scope | Each secret gives access to as little as possible |

**Rotation** means replacing a secret with a new one on a schedule. Its value is that a stolen secret stops working soon. Taken to its conclusion, you get **short-lived credentials**: a service is issued a database password that is valid for an hour and is then given a fresh one. A stolen copy is useless by the time the attacker tries to sell it.

```python-run
def exposure_hours(leak_hour, lifetime_hours, noticed_after_hours=None):
    """How long can an attacker use a secret that leaked at leak_hour?"""
    next_rotation = ((leak_hour // lifetime_hours) + 1) * lifetime_hours
    until_rotation = next_rotation - leak_hour
    if noticed_after_hours is not None:
        return min(until_rotation, noticed_after_hours)       # revoked when someone notices
    return until_rotation

LEAK = 50          # the secret is copied at hour 50
print("lifetime of the secret        usable by the attacker for")
for label, lifetime in [("never rotated (10 years)", 87600), ("rotated every 90 days", 2160),
                        ("rotated daily", 24), ("issued for 1 hour", 1)]:
    print(f"{label:28s}  {exposure_hours(LEAK, lifetime):7d} hours")
print(f"{'90 days, leak noticed in 6 h':28s}  {exposure_hours(LEAK, 2160, noticed_after_hours=6):7d} hours")
```

`exposure_hours` finds the next rotation after the leak and returns how many hours remain until then. If someone notices the leak sooner and revokes the secret, the exposure ends at that point. A secret that is never rotated stays useful to the attacker for years. Rotated every 90 days it is useful for up to 88 days. Issued for one hour, it is useful for at most one hour. The last line shows that fast detection and revocation help too. The two measures support each other.

Tools exist for all of this. A **secrets manager** (HashiCorp Vault and the cloud providers' secret stores are common) creates, stores, hands out and rotates secrets, and records every access. Kubernetes has a basic built-in mechanism.

### Keep secrets out of source code

The most common secrets mistake is to paste a key into a source file and commit it. Version control keeps every past version, so deleting the line later does not remove it from history. Anyone with access to the repository, or to a copy of it, has the key.

The defence is automatic scanning, on the developer's machine before a commit and again in the pipeline.

```python-run
import re

PATTERNS = {
    "cloud access key":     re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key block":    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "password in a string": re.compile(r"(password|passwd|secret|api_key)\s*=\s*['\"][^'\"]{6,}['\"]", re.I),
}

files = {
    "billing/settings.py": 'DB_HOST = "billing-db.internal"\nDB_PASSWORD = os.environ["BILLING_DB_PASSWORD"]\n',
    "reminders/sms.py":    'api_key = "sk_live_9f8a7b6c5d4e3f2a1b0c"\nsend(api_key, phone, text)\n',
    "tools/deploy.sh":     'export AWS_KEY=AKIAIOSFODNN7EXAMPLE\n./deploy --all\n',
    "docs/README.md":      'Set the password in the secrets manager, never in code.\n',
}

findings = [(path, kind) for path, text in files.items()
            for kind, pattern in PATTERNS.items() if pattern.search(text)]
for path, kind in findings:
    print(f"BLOCK COMMIT  {path:22s} looks like: {kind}")
print(f"{len(findings)} finding(s) in {len(files)} files")
```

`PATTERNS` holds three **regular expressions** (text patterns): one for the recognisable shape of a cloud access key, one for the header of a private key, and one for a variable with a password-like name assigned a quoted value. `files` holds four small pretend files. The list comprehension tests every pattern against every file. Two files are flagged: the text-message key pasted into `sms.py` and the cloud key in the deploy script. `settings.py` passes, because it reads the password from the environment at run time, which is the right approach. The README passes because it only talks about passwords. Real scanners use hundreds of patterns and also look for strings that are suspiciously random.

If a secret has been committed, treat it as leaked: revoke and replace it. Removing it from the file is not enough.

## 4. Patching

Most successful attacks use flaws that are already publicly known and already fixed in a newer version. The breach of the credit agency Equifax in 2017, which exposed the personal data of roughly 147 million people, used a flaw in a web framework for which a fix had been available for about two months. Staying up to date is unglamorous and it is one of the most effective protections there is.

In a microservice system the software to patch comes in layers, and it is easy to assume someone else is handling one of them:

| Layer | Example | Who usually patches it |
|---|---|---|
| Your own code | The Reminders service | The owning team |
| Third-party libraries | The HTTP library, the JSON library | The owning team, prompted by a scanner |
| Language runtime | The Python or Java version | The owning team or a platform team |
| Container image's operating system | The base image | Whoever maintains the base image, then every team must rebuild |
| Host operating system and orchestrator | The node's Linux, Kubernetes | The cloud provider or a platform team |
| Hardware and hypervisor | | The cloud provider |

A container image is a snapshot. An image built eight months ago contains eight-month-old libraries, however recently it was started. Images must be rebuilt regularly.

Again the answer is automation: a scanner that knows every service's dependencies and compares them with public lists of known flaws.

```python-run
# What each service is built with (name, version).
services = {
    "appointments": {"webframe": "5.2.1", "jsonlib": "2.9.0", "base-image": "2026-10"},
    "billing":      {"webframe": "5.3.0", "jsonlib": "2.9.0", "paylib": "1.4.2", "base-image": "2026-11"},
    "reminders":    {"webframe": "4.8.0", "jsonlib": "2.7.1", "base-image": "2026-02"},
    "kiosk-api":    {"webframe": "4.1.0", "jsonlib": "2.7.1", "base-image": "2025-06"},
}
# Known flaws: library -> (fixed in version, severity)
advisories = {"webframe": ("5.2.0", "critical"), "jsonlib": ("2.8.0", "medium")}

def older(a, b):
    return tuple(map(int, a.split("."))) < tuple(map(int, b.split(".")))

for svc, deps in services.items():
    problems = [f"{lib} {ver} < {advisories[lib][0]} ({advisories[lib][1]})"
                for lib, ver in deps.items() if lib in advisories and older(ver, advisories[lib][0])]
    print(f"{svc:13s} image built {deps['base-image']}  " + ("; ".join(problems) if problems else "up to date"))
```

`services` lists each service's libraries and when its base image was built. `advisories` lists two known flaws and the version that fixes each. `older` compares version numbers part by part. The loop reports, per service, every library older than its fixed version. Appointments and Billing are current. Reminders and the kiosk API both run a web framework with a critical flaw, and the kiosk API's image is seventeen months old. Without an inventory like this, nobody would know: both services work perfectly.

## 5. Backups and the ability to rebuild

**Backups** are copies of data kept so that it can be restored after loss. Loss includes hardware failure, a faulty release that corrupts records, and **ransomware**: an attack in which criminals encrypt your data and demand payment for the key.

Three rules:

- **Test the restore.** A backup that has never been restored is a hope. Restore regularly, automatically if possible, into a scratch environment, and check that the data is usable.
- **Keep copies somewhere the attacker cannot reach.** If the backups sit on the same network with the same credentials as the live system, ransomware encrypts them too.
- **Know how much you can lose.** Nightly backups mean up to a day of data is gone. Decide whether that is acceptable for each service.

**Rebuild** is the companion capability. If an attacker has been inside a machine, you cannot be sure what they left behind. The safe response is to destroy it and build a clean one. With infrastructure as code, automated deployment and tested backups, rebuilding a service from nothing is a routine operation. That ability also happens to be the best protection against ordinary disasters.

> [!INTERVIEW]
> If asked "how do you approach security in a microservice system?", give structure: *three principles: least privilege to keep the blast radius of any compromise small, defence in depth because every single control fails eventually, and automation because there is too much to do by hand. I think across identify, protect, detect, respond and recover, not only prevention. Concretely: per-service scoped credentials from a secrets manager with automatic rotation, secret and dependency scanning in the pipeline, regular image rebuilds, and tested backups with the ability to rebuild any service from code.*

## 6. Pitfalls

- **One shared database account.** A compromise of the smallest service exposes everything.
- **Prevention only.** With no detection or response plan, a breach goes unnoticed for months.
- **Secrets in source code or in container images.** History and image layers keep them for ever.
- **Secrets that never change.** A copy made by a contractor two years ago still works.
- **Removing a leaked secret without revoking it.** The attacker already has it.
- **Assuming another team patches the base image.** Old images run old flaws.
- **Untested backups.** The first restore attempt is during the disaster.
- **Backups reachable with production credentials.** They are lost in the same attack.
- **Security as a final review.** It arrives too late to change the design.

## Summary

- Microservices enlarge the attack surface and also provide more internal boundaries to contain an attacker.
- Least privilege keeps the blast radius small; defence in depth layers preventive, detective and responsive controls; automation makes both sustainable.
- The five functions (identify, protect, detect, respond, recover) keep attention on the whole life of an incident; threat modelling directs effort to what matters.
- Credentials are the usual way in: use MFA and password managers for people, and a secrets manager with scoped, rotated, revocable secrets for services.
- Never commit secrets; scan for them, and revoke any that leak.
- Patch every layer, track dependencies with scanners, and rebuild images regularly.
- Test restores, keep backups out of the attacker's reach, and be able to rebuild any service from code.

## Glossary

| Term | Meaning |
|---|---|
| Attack surface | All the points where an attacker could try to get in |
| Least privilege | Granting the minimum access needed, for the shortest time |
| Blast radius | How much damage one compromise can cause |
| Defence in depth | Several independent layers of protection |
| Preventive / detective / responsive control | A measure that stops / notices / limits and repairs an attack |
| Threat modelling | Analysing a system from an attacker's point of view |
| Credential | Something presented to prove identity and gain access |
| Multi-factor authentication | Requiring a second proof in addition to a password |
| Secret | A credential used by a program |
| Rotation / revocation | Replacing a secret on a schedule / cancelling it immediately |
| Secrets manager | A tool that creates, stores, distributes and rotates secrets |
| Patching | Updating software to remove known flaws |
| Ransomware | An attack that encrypts data and demands payment |
| Backup / restore | A stored copy of data / bringing data back from it |
| Rebuild | Recreating a service and its infrastructure from code and backups |

```quiz
[
  {"q": "What does the principle of least privilege aim to limit?", "options": ["The number of developers", "The blast radius: how much an attacker can reach after compromising one account or service", "The size of log files", "The number of deployments per day"], "answer": 1,
   "explain": "Giving each service only the access it needs means a compromise of that service exposes little."},
  {"q": "Why is defence in depth needed even with a strong firewall?", "options": ["Firewalls are illegal in some countries", "Any single control can fail, so independent layers are needed to stop or notice what gets through", "It makes the system faster", "Firewalls only work for monoliths"], "answer": 1,
   "explain": "No measure is perfect. Layers of prevention, detection and response cover each other's failures."},
  {"q": "Which of the five functions of cybersecurity are most often neglected?", "options": ["Protect", "Identify and protect", "Respond and recover", "None"], "answer": 2,
   "explain": "Organisations tend to focus on prevention. Planning and rehearsing what to do during and after a breach limits the damage."},
  {"q": "A developer committed an API key to the repository and removed it in the next commit. What must happen?", "options": ["Nothing; it is gone", "The key must be revoked and replaced, because it remains in the history", "The repository must be renamed", "The developer should change their password"], "answer": 1,
   "explain": "Version control keeps every past version. A committed secret must be treated as leaked."},
  {"q": "What is the benefit of short-lived credentials?", "options": ["They are easier to remember", "A stolen credential stops working soon, shrinking the time an attacker can use it", "They never need a secrets manager", "They make services faster"], "answer": 1,
   "explain": "If a credential is valid for an hour, a leaked copy is useless after that hour."},
  {"q": "A container image was built ten months ago and restarted yesterday. How old are its libraries?", "options": ["One day", "Ten months", "It depends on the node", "They update themselves"], "answer": 1,
   "explain": "An image is a snapshot from build time. Restarting does not update it; it must be rebuilt."},
  {"q": "Why should restores from backup be tested regularly?", "options": ["To use spare disk space", "An untested backup may be incomplete or unusable, and you would only find out during an emergency", "Regulators forbid untested files", "It makes backups smaller"], "answer": 1,
   "explain": "Only a successful restore proves that the backup works and that the team knows the procedure."},
  {"q": "After an attacker has had access to a server, why is rebuilding it from code preferred over cleaning it?", "options": ["Rebuilding is slower, which gives time to think", "You cannot be sure what the attacker changed or left behind; a clean rebuild removes the doubt", "Cleaning is forbidden", "It increases the attack surface"], "answer": 1,
   "explain": "With infrastructure as code and automated deployment, replacing a possibly tainted machine with a fresh one is routine and trustworthy."}
]
```

> **Source:** Newman, *Building Microservices*, 2nd ed., ch. 11 (topic coverage only; wording and the Pawprint example are original). NIST Cybersecurity Framework, https://www.nist.gov/cyberframework ; NIST Special Publication 800-63B, Digital Identity Guidelines.
