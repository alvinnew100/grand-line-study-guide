# Logging, monitoring and vulnerability management

> **Before this lesson:** read [Security in the SDLC: SAST, DAST and CI gates](#/lesson/web-security/sdlc-automation) for how findings are produced, and [Secure architecture and threat modelling (STRIDE)](#/lesson/web-security/threat-modelling) for risk rating and the *repudiation* threat. The log-injection idea builds on [SQL injection and parameterised queries](#/lesson/web-security/sql-injection).

## In plain words

A shop has locks on the doors — and also a security camera, an alarm, and a procedure for what to do when the alarm rings. The locks are *prevention*. The camera and alarm are *detection*. The procedure is *response*. A shop with excellent locks and no camera will, one day, be burgled without anyone knowing how, when, or what was taken.

Every lesson so far has been about locks. This one is about the camera and the procedure. **Logging** is the application's camera: a written record of what happened. **Monitoring** is somebody — or something — actually watching the footage and raising the alarm. **Vulnerability management** is the procedure for the other kind of bad news: a report that one of your locks is faulty. It covers how such reports arrive, how you decide which to fix first, and how you fix them and make sure they stay fixed.

OWASP lists *Security Logging and Monitoring Failures* in its Top 10 for a sobering reason: studies of real breaches keep finding that intruders were inside for weeks or months before being noticed, and were often noticed by an outsider. And every engineer will at some point receive a message beginning "I think I found a security problem in your site." Handling that well is a professional skill, and interviewers ask about both.

## Part 1: logging

### What to record

A **log** is a time-ordered list of **events**. For security, the events worth recording are the ones that answer "who did what, to what, when, from where, and did it work?"

| Category | Events |
|---|---|
| **Authentication** | Login success and failure, logout, password change and reset, MFA enrolment and failure, lockouts |
| **Authorisation** | Access denied (403/404 on protected resources), permission and role changes |
| **Sensitive actions** | Payments, refunds, exports, account deletion, administrative operations, impersonation |
| **Input validation failures** | Rejected requests, especially bursts of them |
| **Security controls firing** | Rate limit exceeded, CSRF token mismatch, signature verification failure |
| **System and configuration** | Start-up with configuration summary, deployments, changes to security settings |
| **Errors** | Unhandled exceptions with a correlation ID |

Each event should carry: a timestamp in UTC from a synchronised clock; the user or service identity; the source address; the action; the object acted on; the outcome; and a **correlation ID** — a random identifier attached to a request as it enters the system and passed along to every service that handles it, so that one request can be followed across many log files.

### Structured logs

Write logs as data, not as sentences. A **structured log** entry is a set of named fields, normally one JSON object per line:

```python
# VULNERABLE (as engineering): free text is hard to search and easy to forge
logger.info("User " + email + " failed login from " + ip)
```

```python
# FIXED: named fields
logger.info("login_failed", extra={"user_id": user_id, "ip": ip, "reason": "bad_password",
                                   "request_id": request_id})
```

With fields, a monitoring system can count `login_failed` events per `ip` without guessing at sentence structure.

### What never to record

Logs are copied to many systems, kept for a long time and read by many people. Whatever is in them is, in effect, widely shared. Never log:

- passwords — including *failed* attempts, which are often the right password with one typo;
- session identifiers, access tokens, API keys, `Authorization` and `Cookie` headers;
- full payment card numbers, security codes;
- secrets and encryption keys;
- more personal data than the investigation needs.

The safe design is an allow-list: log named fields that you chose, not whole request bodies or headers. As a second layer, pass every event through a **redaction** step.

```python-run
import json, re

SENSITIVE_KEYS = {"password", "token", "authorization", "cookie", "secret", "api_key", "card_number"}
CARD_LIKE = re.compile(r"(?<!\d)\d{13,19}(?!\d)")          # a run of 13 to 19 digits

def redact(value):
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item))
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        masked = CARD_LIKE.sub(lambda m: "*" * (len(m.group()) - 4) + m.group()[-4:], value)
        return masked.replace("\r", "\\r").replace("\n", "\\n")      # one event = one line
    return value

event = {
    "event": "checkout_failed",
    "user_id": 7,
    "headers": {"Authorization": "Bearer eyJhbGciOi...", "Accept": "application/json"},
    "form": {"email": "ann@shop.example", "Password": "hunter2", "note": "card 4111111111111111 declined"},
    "message": "gateway timeout\n2026-11-21 INFO admin login ok user=root",
}
print(json.dumps(redact(event), indent=2))
print("original untouched:", event["form"]["Password"])
```

`redact` is recursive: for a dictionary it builds a **new** dictionary, replacing the value of any key whose lower-cased name is on the sensitive list and calling itself on the rest; for a list it processes each element; for a string it masks card-like digit runs, keeping the last four, and then turns real line breaks into the visible two-character sequences `\r` and `\n`. Other values pass through. The output shows `Authorization` and `Password` hidden regardless of capitalisation, the card number masked, and the multi-line message flattened. The last line confirms the original event was not modified.

### Log injection

Why flatten line breaks? Because logs have an injection problem of their own. If user-supplied text is written into a line-based log unaltered, a value containing a newline followed by something shaped like a log entry — as in the `message` field above — creates a **forged entry**: a fake "admin login ok" line that could mislead an investigator or a detection rule. Log viewers that render HTML add a second risk: script in a logged value becomes stored XSS against whoever views the logs.

Defences: structured logging (the JSON encoder escapes newlines and quotes for you), neutralising control characters, and output encoding in any log viewer.

### Protecting the logs

Logs are evidence, and an intruder's first wish is to erase their tracks.

- **Ship logs off the machine** immediately to a central, separate system; a compromised server should not be able to delete its own history.
- **Append-only** storage with restricted access; few people may read, almost nobody may delete.
- **Integrity protection** where it matters — write-once storage or signed log batches.
- **Retention** long enough to investigate (often many months for security logs) and no longer than privacy rules allow.
- **Synchronised clocks** across servers, or events cannot be put in order.

## Part 2: monitoring and detection

A log nobody reads is a diary, not an alarm. **Monitoring** turns events into signals; **alerting** brings a person in when a signal crosses a line.

```mermaid
flowchart LR
    A[Applications and servers] -->|structured events| C[Central log platform]
    C --> D[Detection rules and dashboards]
    D -->|threshold crossed| AL[Alert to on-call]
    AL --> T[Triage - real or false alarm?]
    T -->|real| IR[Incident response]
    T -->|false| TU[Tune the rule]
    IR --> L[Lessons learned - new rules, fixes, tests]
```

Large organisations run a **SIEM** (security information and event management) platform for this; a small team can start with the alerting features of its logging service.

### What to alert on

Aim at behaviour, mapped to the attacks from this track:

| Signal | What it may indicate |
|---|---|
| Many failed logins for one account | Brute force |
| Failed logins across many accounts from few addresses | Password spraying, credential stuffing |
| A successful login after many failures | A guessed password |
| Bursts of 403/404 on object URLs from one user | IDOR enumeration |
| Spike in validation errors or `500`s on one endpoint | Injection probing, fuzzing |
| CSRF or signature failures | Forgery attempts — or a broken client |
| Requests for `/.env`, `/.git/`, admin paths | Automated reconnaissance |
| Unusually large export or data volume by one account | Data theft |
| New administrator created; MFA disabled; security setting changed | Persistence after a compromise |
| Login from a new country followed by a password or email change | Account takeover |
| Outbound connections from the web tier to unexpected hosts | SSRF or a compromised dependency |

A detection rule is, at heart, a small program over the event stream:

```python-run
from collections import defaultdict

events = [
    {"t": 0,   "type": "login_failed", "account": "ann",   "ip": "198.51.100.7"},
    {"t": 5,   "type": "login_failed", "account": "bob",   "ip": "198.51.100.7"},
    {"t": 9,   "type": "login_failed", "account": "carol", "ip": "198.51.100.7"},
    {"t": 14,  "type": "login_failed", "account": "dave",  "ip": "198.51.100.7"},
    {"t": 20,  "type": "login_failed", "account": "erin",  "ip": "198.51.100.7"},
    {"t": 300, "type": "login_failed", "account": "ann",   "ip": "203.0.113.50"},   # Ann mistypes once
    {"t": 320, "type": "login_ok",     "account": "ann",   "ip": "203.0.113.50"},
]

def spraying_alerts(events, window=60, distinct_accounts=5):
    failures = defaultdict(list)                       # ip -> list of (time, account)
    alerts = []
    for e in events:
        if e["type"] != "login_failed":
            continue
        recent = [(t, a) for t, a in failures[e["ip"]] if t > e["t"] - window]
        recent.append((e["t"], e["account"]))
        failures[e["ip"]] = recent
        accounts = {a for _, a in recent}
        if len(accounts) >= distinct_accounts:
            alerts.append((e["t"], e["ip"], len(accounts)))
    return alerts

for when, ip, count in spraying_alerts(events):
    print(f"t={when}: possible password spraying from {ip} - {count} different accounts in 60 s")
```

`defaultdict(list)` is a dictionary that creates an empty list the first time a key is used. For each failed login the function keeps that address's failures from the last 60 seconds and counts the **distinct accounts** among them. Five different accounts from one address within a minute raises an alert; Ann's single typo from her own address does not. Counting distinct accounts instead of raw failures is what separates an attack from a forgetful user.

### Alerts that people can act on

- Every alert must be **actionable**: it says what happened and links to a short **runbook** describing what to check and do.
- Tune relentlessly. Too many false alarms cause **alert fatigue**, and the real one is missed.
- Use severity levels: page a person for the critical few; send the rest to a queue.
- Test detection: deliberately trigger each rule in a test environment and confirm the alert arrives.

### Incident response in one paragraph

When an alert is real, follow a plan prepared in advance. The standard phases: **prepare** (contacts, access, runbooks, practice); **identify** (confirm and scope); **contain** (stop the bleeding — revoke sessions and keys, block the path, isolate the system, while preserving evidence); **eradicate** (remove the cause); **recover** (restore service, watch closely); and **learn** (a blameless review that produces fixes, tests and new detections). Depending on the data and jurisdiction there may also be legal duties to notify regulators and affected users within a fixed time — one more reason to know quickly what happened.

## Part 3: vulnerability management

### Where vulnerability reports come from

| Source | Notes |
|---|---|
| Your own tools | SAST, SCA, DAST, configuration scanners |
| Code review and threat modelling | Design and logic issues |
| **Penetration tests** | Hired specialists attack the system, with permission and a defined scope, and write a report |
| **Responsible disclosure / bug bounty** | Outside researchers report what they find |
| Vendors and public advisories | CVEs in products and libraries you use |
| Incidents | A flaw discovered because it was used |

### The process

```mermaid
flowchart LR
    R[Report received] --> V[Reproduce and validate]
    V --> S[Assess severity and risk]
    S --> P[Prioritise and assign with a deadline]
    P --> F[Fix the instance and the class]
    F --> T[Verify the fix and add a regression test]
    T --> D[Deploy and disclose as appropriate]
    D --> L[Learn - prevent recurrence]
```

**Reproduce.** Confirm the report in a safe environment. Reproducing establishes that the issue is real, shows its true reach, and gives you the test case you will later automate.

**Assess severity.** The common language is **CVSS**, the Common Vulnerability Scoring System, which produces a score from 0.0 to 10.0. Its *base* score derives from characteristics of the flaw: can it be exploited over the network or only locally? How complex is the attack? Are privileges or user interaction required? What is the impact on confidentiality, integrity and availability? Scores map to labels:

| Score | Rating |
|---|---|
| 0.1 – 3.9 | Low |
| 4.0 – 6.9 | Medium |
| 7.0 – 8.9 | High |
| 9.0 – 10.0 | Critical |

A base score describes the flaw *in general*. Your priority must also consider **your** context: Is the affected system internet-facing? Does it hold sensitive data? Is the vulnerable code reachable? Is the flaw being actively exploited in the wild (public "known exploited" lists and probability scores such as EPSS help here)? A critical-rated flaw on an isolated internal tool may reasonably wait behind a medium one on the public login page.

**Prioritise with deadlines.** Agree **remediation targets** by severity in advance, so the discussion is not repeated for every finding:

```python-run
SLA_DAYS = {"critical": 2, "high": 14, "medium": 45, "low": 90}

def triage(findings, today):
    rows = []
    for f in findings:
        priority = f["severity"]
        # Context can raise priority: exposure and known exploitation
        if f.get("actively_exploited") and priority != "critical":
            priority = "critical"
        elif f.get("internet_facing") and priority == "medium":
            priority = "high"
        due = f["reported_day"] + SLA_DAYS[priority]
        status = "OVERDUE" if today > due else f"due in {due - today} d"
        rows.append((list(SLA_DAYS).index(priority), due, f["id"], priority, status))
    return sorted(rows)

findings = [
    {"id": "V-1 IDOR on invoices",          "severity": "high",   "reported_day": 0,  "internet_facing": True},
    {"id": "V-2 old TLS on admin intranet", "severity": "medium", "reported_day": 0},
    {"id": "V-3 library flaw, exploited",   "severity": "high",   "reported_day": 8,  "actively_exploited": True},
    {"id": "V-4 verbose error on API",      "severity": "medium", "reported_day": 2,  "internet_facing": True},
    {"id": "V-5 missing header",            "severity": "low",    "reported_day": 1},
]
for _, due, name, priority, status in triage(findings, today=12):
    print(f"{priority:8} {status:12} {name}")
```

Each finding starts at its reported severity; two context rules can raise it. The due date is the report day plus the agreed number of days. `list(SLA_DAYS).index(priority)` gives 0 for critical through 3 for low, so sorting the tuples lists the most urgent first, and earlier deadlines first within a level. V-3 jumps to critical because it is being exploited, and at day 12 it is already overdue.

**Fix the class.** Patch the reported instance, then search for the same mistake elsewhere and remove the *possibility* of it — a shared helper, a lint rule, a framework default.

**Verify and regress.** Confirm the original reproduction no longer works; add it to the test suite; ask the reporter to confirm where appropriate.

**Record.** Keep a register: what, where, severity, owner, dates, decision. Risks accepted instead of fixed are recorded with an owner and a review date.

### Responsible disclosure

Sooner or later someone outside your organisation will find a flaw. Whether they tell *you* depends on how easy and safe you make it.

**Coordinated (responsible) vulnerability disclosure** is the practice in which a researcher reports privately, the organisation fixes the issue within a reasonable time, and details are published — if at all — afterwards, usually with credit to the finder. To receive such reports well:

- **Publish a contact.** The convention is a file at `/.well-known/security.txt` listing a security contact and a link to your policy:

```text
Contact: mailto:security@shop.example
Expires: 2027-12-31T23:59:59Z
Policy: https://shop.example/security-policy
Preferred-Languages: en
```

- **Publish a policy** stating what is in scope, what testing is not acceptable (denial of service, accessing other users' data, social engineering of staff), and a **safe-harbour** commitment that you will not pursue legal action against good-faith research within those rules.
- **Acknowledge quickly** — within a few days — and keep the reporter informed.
- **Fix within an agreed window.** Ninety days is a widely used norm before public disclosure.
- **Give credit**, if the reporter wants it.

A **bug bounty programme** adds payment for valid reports, often run through a platform that handles intake and triage. It suits organisations that already fix findings promptly; opening one before your own scanning and review are in order produces a flood you cannot handle.

And from the other side — if *you* stumble on a flaw in someone else's product: stop as soon as you have enough to describe it; do not access, copy or change other people's data; report privately through the published channel; give reasonable time. Testing systems without permission is illegal in most countries, whatever your intentions.

> [!WARNING]
> The worst responses to an outside report are silence and legal threats. Both teach researchers to publish first or to say nothing — and the flaw remains for someone less friendly to find.

> [!TIP]
> When something goes wrong, the first question is always "what do the logs say?" Decide *now* which questions you would need answered — who accessed this record, from where, what else did that session do — and check today that your logs can answer them. Discovering mid-incident that a crucial event was never recorded is a very common and very avoidable experience.

> [!INTERVIEW]
> Two frequent questions. **"What would you log for security, and what would you never log?"** — authentication and authorisation events, sensitive actions, control failures, with who/what/when/where/outcome and a correlation ID; never passwords, tokens, session IDs, card data or secrets; centralise, protect and alert. **"A researcher emails you about a vulnerability — what do you do?"** — thank them and acknowledge promptly; reproduce in a safe environment; rate severity in context; contain if it is being exploited; fix the instance and the class; add a regression test; check logs for earlier exploitation; keep the reporter informed and credit them; review how it got through.

## Defence in depth

1. **Prevent** — everything in the earlier lessons.
2. **Record** — structured, redacted, centralised, tamper-resistant logs of security-relevant events.
3. **Detect** — tuned rules with runbooks; tested regularly.
4. **Respond** — a practised incident plan; the ability to revoke sessions and rotate secrets fast.
5. **Find weaknesses first** — scanning, review, penetration tests, a disclosure channel.
6. **Fix by risk** — severity in context, agreed deadlines, tracked to closure.
7. **Learn** — every incident and finding leaves behind a test, a rule or a design change.

## How to test for it

**In code review:**

- For each authentication, authorisation and sensitive handler: is there a log event for success *and* failure, with identity, object and outcome?
- Search logging calls for request bodies, headers, passwords, tokens and whole objects.
- Is user-controlled text written into logs through a structured logger?
- Are correlation IDs generated and propagated?

**In practice:**

- Perform a failed login, an access-denied request and an admin action in a test environment, then find all three in the central log platform. How long did it take? Were the fields sufficient to say who and what?
- Search stored logs for the test account's password and session token; expect no matches.
- Submit a value containing a line break and check the stored entry is still one event.
- Trigger each alert rule deliberately; confirm it fires and reaches a person.
- Run a **tabletop exercise**: talk through a scenario ("a customer says their account was taken over") step by step and note every point where information or access was missing.
- Review the vulnerability register for overdue items, and try your own `security.txt` contact address to see that someone answers.

## Pitfalls

- **Logging only errors**, not security-relevant successes such as logins and permission changes.
- **Logs kept only on the server that was compromised.**
- **Secrets and personal data in logs**, turning the log store into a breach target.
- **No alerting** — events are recorded and never examined.
- **Alert floods** that are muted.
- **Clocks out of sync.**
- **Treating CVSS as the priority** without considering exposure and exploitation.
- **Fixing the reported instance only.**
- **No named owner or deadline** for findings, so they age indefinitely.
- **No public security contact**, leaving researchers to guess — or to post publicly.
- **Blame after incidents**, which teaches people to hide mistakes.

## Summary

- Prevention is never complete; logging, monitoring and response determine how soon and how well you recover.
- Log authentication, authorisation, sensitive actions and control failures as structured events with who, what, when, where and outcome.
- Never log credentials, tokens, card data or secrets; redact by key and pattern, and neutralise line breaks to prevent forged entries.
- Centralise and protect logs; alert on behaviour patterns with tuned, actionable rules backed by runbooks.
- Vulnerability management is a loop: receive, reproduce, rate in context, prioritise with deadlines, fix the class, verify with a regression test, record and learn.
- CVSS gives a common severity scale; exposure and active exploitation determine real priority.
- Make it easy and safe for outsiders to report problems: a published contact, a clear policy, prompt and courteous handling.

## Glossary

- **Log / event** — a time-ordered record / one entry in it.
- **Structured logging** — writing events as named fields instead of free text.
- **Correlation ID** — an identifier linking all events of one request.
- **Redaction** — removing or masking sensitive values before storage.
- **Log injection (log forging)** — inserting crafted input that creates false log entries.
- **Audit log** — a record of who performed which sensitive actions.
- **Monitoring / alerting** — observing signals / notifying a person when a threshold is crossed.
- **SIEM** — a platform collecting and analysing security events.
- **Alert fatigue** — desensitisation caused by too many alerts.
- **Runbook** — written steps for handling a specific alert or incident.
- **Incident response** — the organised handling of a security incident.
- **Vulnerability management** — the continuous process of finding, assessing, fixing and tracking vulnerabilities.
- **CVSS** — Common Vulnerability Scoring System, a 0–10 severity scale.
- **Remediation target (SLA)** — the agreed time to fix findings of a given severity.
- **Penetration test** — an authorised simulated attack by specialists.
- **Responsible (coordinated) disclosure** — privately reporting a flaw and allowing time to fix before publication.
- **Bug bounty** — a programme rewarding outside reports of vulnerabilities.
- **`security.txt`** — a standard file publishing an organisation's security contact.
- **Safe harbour** — a promise not to take legal action against good-faith research within the policy.

```quiz
[
  {"q": "Why does OWASP treat insufficient logging and monitoring as a top risk?",
   "options": ["Logs slow down applications", "Without them breaches go undetected for long periods and cannot be investigated", "Logging is required by browsers", "It causes SQL injection"], "answer": 1,
   "explain": "Detection and response depend on records. Many real intrusions lasted months because nobody was watching."},
  {"q": "Which of these should never be written to a log?",
   "options": ["The user ID that performed an action", "The outcome of a login attempt", "The password a user typed in a failed login", "A correlation ID"], "answer": 2,
   "explain": "Failed attempts are often the real password with a typo. Credentials, tokens and secrets must stay out of logs."},
  {"q": "A user-supplied value containing a newline followed by text shaped like a log entry is written unaltered to a line-based log. What is the risk?",
   "options": ["The log file is deleted", "A forged log entry that may mislead investigators or detection rules", "The server restarts", "No risk"], "answer": 1,
   "explain": "This is log injection. Structured logging or neutralising line breaks keeps one event on one line."},
  {"q": "Why should logs be shipped to a separate central system?",
   "options": ["To save disk space only", "So an intruder who compromises a server cannot erase or alter the evidence", "Because local logs are illegal", "To make logs public"], "answer": 1,
   "explain": "Logs are evidence and a target. Off-host, append-only storage preserves them."},
  {"q": "Which detection signal best distinguishes password spraying from a forgetful user?",
   "options": ["One failed login", "Failed logins against many different accounts from the same source in a short time", "A successful login", "A password change"], "answer": 1,
   "explain": "A legitimate user fails on their own account. Many accounts from one source indicates an attack."},
  {"q": "A flaw has a CVSS base score of 9.8 but exists only on an isolated internal test tool. Another scores 6.5 and is on the public login page, with exploitation observed elsewhere. Which is usually fixed first?",
   "options": ["Always the 9.8", "The 6.5, because exposure and active exploitation raise its real risk", "Neither", "Whichever was reported first"], "answer": 1,
   "explain": "Base scores describe the flaw generically. Priority must reflect context: exposure, data, reachability and exploitation."},
  {"q": "An external researcher privately reports a vulnerability. What is the appropriate first response?",
   "options": ["Ignore it", "Threaten legal action", "Acknowledge promptly, thank them, and begin reproducing the issue", "Publish the details immediately"], "answer": 2,
   "explain": "Courteous, prompt handling encourages responsible reporting. Reproduction confirms and scopes the issue."},
  {"q": "After fixing a reported SQL injection in one endpoint, what else should be done?",
   "options": ["Nothing", "Search for the same pattern elsewhere, remove the possibility with a safe data-access pattern, and add a regression test", "Disable logging", "Lower the severity"], "answer": 1,
   "explain": "One instance usually signals a class. Fix the class and guard the fix with a test."}
]
```

> **Source:** Hoffman, *Web Application Security*, ch. 20 (vulnerability discovery: regression testing, responsible disclosure programmes, bug bounty programmes, third-party penetration testing) and ch. 21 (vulnerability management: reproducing vulnerabilities, ranking severity, CVSS), in original wording with original examples. OWASP Logging Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html ; OWASP Top 10 A09 Security Logging and Monitoring Failures — https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/ ; OWASP Vulnerability Disclosure Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Vulnerability_Disclosure_Cheat_Sheet.html ; FIRST, CVSS — https://www.first.org/cvss/ ; security.txt (RFC 9116) — https://securitytxt.org/
