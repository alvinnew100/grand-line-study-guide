# Trust, encryption and identity: zero trust, JWTs and the confused deputy

## Before this lesson

> **Before this lesson:** read [Security foundations](#/lesson/microservices/security-foundations). You should know least privilege, defence in depth, blast radius and what a secret is. API gateways and service meshes were introduced in [Handling change](#/lesson/microservices/handling-change).

## In plain words

An old castle is protected by a wall and a moat. Anyone inside the wall is assumed to be a friend and may walk into any room. It is cheap to run, and it fails completely the day one enemy gets across the moat.

A modern office building works differently. The front door needs a badge. So does the lift, each floor, the server room and the finance office. Being inside the building proves nothing: every door checks your badge again. This is slower to set up, and one intruder in the lobby gets no further than the lobby.

For services, the castle is called **implicit trust** and the office building is called **zero trust**.

The badge deserves a closer look. Reception issues it after checking your identity once. It states who you are, which areas you may enter and when it expires, and it carries a hologram that is hard to forge. Each door can read the badge and decide without telephoning reception. A **JSON Web Token (JWT)** is such a badge for software, and this lesson builds one from scratch.

Last, a trick as old as offices. You have no right to see a certain file, so you ask a helpful clerk who does have access to fetch it for you. The clerk never asks whether *you* are allowed. The clerk has been made into a **confused deputy**. Services fall for this easily, and JWTs are one way to stop it.

Why this matters for a job: authentication, authorisation, TLS and JWTs come up in nearly every backend interview, and mistakes here cause real data leaks.

## 1. Implicit trust and zero trust

**Implicit trust** (also called perimeter security) assumes that any call coming from inside the network is safe. Services do not check who is calling. All protection sits at the edge.

**Zero trust** assumes the network is already compromised. Every call is treated as possibly hostile, wherever it comes from. Every service checks who is calling and whether that caller may do what it asks, and all traffic is encrypted, including traffic between your own services.

```mermaid
flowchart LR
  subgraph Castle[Implicit trust]
    E1[Edge check] --> A1[Appointments]
    A1 -->|no checks| P1[Patients]
    A1 -->|no checks| B1[Billing]
    X1[Attacker inside] -->|no checks| P1
  end
  subgraph Office[Zero trust]
    E2[Edge check] --> A2[Appointments]
    A2 -->|identity checked, encrypted| P2[Patients]
    A2 -->|identity checked, encrypted| B2[Billing]
    X2[Attacker inside] -. rejected .-> P2
  end
```

Zero trust is not a product you install. It is a way of thinking that leads to concrete measures, and it costs effort. Many organisations sit between the two extremes, and a sensible way to do so is by **zones**: classify data by sensitivity, and apply stricter rules where the data is more sensitive.

| Zone | Example at Pawprint | Rules |
|---|---|---|
| Public | Clinic opening hours | Could be published; basic controls |
| Private | Appointment times, pet names | Authenticated callers, encrypted in transit |
| Secret | Medical records, card tokens | Zero trust: mutual authentication, fine-grained authorisation, full audit log |

A service in a less sensitive zone may not read from a more sensitive one without an explicit, checked path.

## 2. Protecting data in transit

**Data in transit** is data moving over a network. Four separate things can go wrong, and it helps to keep them apart:

| Concern | Question | Without protection |
|---|---|---|
| Server identity | Am I really talking to Billing? | An impostor receives the card data |
| Client identity | Is this caller really Appointments? | Anyone on the network can call Billing |
| Visibility | Can someone read the data on the way? | Medical notes are readable by eavesdroppers |
| Manipulation | Can someone change the data on the way? | An amount of 20 becomes 2000 |

**TLS** (transport layer security) is the standard answer. It is what puts the "S" in HTTPS. With ordinary TLS, the server presents a **certificate**, a document signed by a trusted authority stating "this is billing.pawprint.internal". The client checks it, which settles server identity, and the connection is then encrypted and protected against tampering, which settles visibility and manipulation.

**Mutual TLS (mTLS)** adds the remaining item: the client presents a certificate too, so each side has proof of the other's identity. Issuing, distributing and renewing certificates for every service instance is a lot of work by hand. A service mesh (lesson 12) does it automatically, which is one of the main reasons teams adopt one.

How does a receiver know data was not changed? By a **signature**: a short value computed from the message and a secret key. Anyone who alters the message cannot produce the matching signature without the key.

```python-run
import hmac, hashlib

SHARED_KEY = b"key-known-only-to-appointments-and-billing"

def sign(message):
    return hmac.new(SHARED_KEY, message.encode(), hashlib.sha256).hexdigest()

def verify(message, signature):
    return hmac.compare_digest(sign(message), signature)

original = "charge visit=551 amount=2000"
tag = sign(original)
print("signature:", tag[:24], "...")
print("original message accepted:", verify(original, tag))

tampered = "charge visit=551 amount=9000"
print("tampered message accepted:", verify(tampered, tag))
```

`sign` uses HMAC, a standard way of combining a message with a secret key through a **hash function** (a function that turns any input into a fixed-size fingerprint). `verify` recomputes the signature and compares. The original message is accepted. Change a single digit and the check fails, because the attacker cannot compute the right signature without `SHARED_KEY`. TLS does this for you on every packet. The same idea reappears below inside the JWT.

## 3. Protecting data at rest

**Data at rest** is data stored on disk: databases, files, backups. If an attacker gets past everything else and copies the database, encryption at rest is the last layer of defence in depth.

Five rules cover most of what matters.

**Use well-known implementations.** Never design your own encryption. Use a mature, widely reviewed library and algorithm, and keep it up to date.

**Hash passwords; do not encrypt them.** A password should never be stored in a form that can be turned back into the password. Store a **salted hash**: combine the password with a random value unique to that user (the **salt**), then run a deliberately slow hash function designed for passwords. Slowness is a feature: it makes guessing billions of passwords impractical.

```python-run
import hashlib, os

def fast_unsalted(password):
    return hashlib.sha256(password.encode()).hexdigest()[:16]

def slow_salted(password, salt=None):
    salt = salt or os.urandom(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 20_000)
    return salt.hex(), digest.hex()[:16]

users = {"kai": "miso2019", "priya": "miso2019", "dr-lim": "correct horse battery"}

print("Unsalted fast hash: equal passwords are visible at a glance")
for user, pw in users.items():
    print(f"   {user:7s} {fast_unsalted(pw)}")

print("Salted slow hash: equal passwords look unrelated")
stored = {user: slow_salted(pw) for user, pw in users.items()}
for user, (salt, digest) in stored.items():
    print(f"   {user:7s} salt={salt} hash={digest}")

salt_hex, expected = stored["kai"]
attempt = slow_salted("miso2019", bytes.fromhex(salt_hex))[1]
print("login check for kai with the right password:", attempt == expected)
```

`fast_unsalted` is what not to do. Kai and Priya chose the same password and get the same hash, so an attacker who cracks one has both, and can look the hash up in precomputed tables. `slow_salted` generates a random salt per user and runs PBKDF2, a password-hashing function, for 20,000 rounds. Now the two identical passwords produce unrelated values. To check a login, the service repeats the calculation with the stored salt and compares. (Your salts and hashes will differ on each run, because the salt is random.) In production use a library implementing a current password-hashing algorithm such as Argon2 or bcrypt.

**Encrypt selectively and know why.** Decide which data is sensitive and encrypt that. Encrypting everything sounds safe, and it costs performance and complicates operations.

**Collect less.** Data you never stored cannot leak. Keep only what the business needs, and delete it when it is no longer needed. Privacy laws such as the EU's GDPR and Singapore's PDPA turn this into an obligation.

**Guard the keys, and encrypt the backups.** Encryption moves the problem to the **key**: the secret value needed to decrypt. If the key is stored beside the data, an attacker takes both. Keep keys in a separate key management service with its own access controls. And remember that a backup is a full copy of the data; it needs the same protection.

## 4. Authentication and authorisation

Two words that look alike and mean different things:

- **Authentication** answers *who are you?* It is the process of confirming identity.
- **Authorisation** answers *what are you allowed to do?* It maps an identity to permitted actions.

The thing being authenticated, a person or a program, is called the **principal**.

### Service-to-service

One service proves its identity to another most commonly with mutual TLS, or with an API key (a secret string sent with each request, weaker because it can be copied). Authorisation then asks: may Appointments call *this operation* on Billing?

### People

Users should not log in separately to each of thirty services. **Single sign-on (SSO)** lets a person authenticate once with an **identity provider**, a system that holds user accounts and checks credentials. The common protocol today is **OpenID Connect**, built on OAuth 2.0.

Individual services should not each implement the login redirect. A gateway at the edge usually does it: it sends unauthenticated users to the identity provider, establishes a session, and passes the request inward with information about who the user is.

Two cautions about that gateway:

- If the gateway is the *only* place where anything is checked, you are back in the castle. Defence in depth says services check too.
- Keep its authorisation **coarse-grained**: "is this a logged-in owner or a staff member?" Fine-grained decisions, such as "may this vet change this prescription?", depend on business rules that belong to the owning service. Putting every service's rules in the gateway or in the identity provider creates a central component that every team must change.

## 5. The confused deputy

Kai is a pet owner and is properly logged in. Kai's pet is number 7. Kai edits the address in the browser and asks for the appointment history of pet 9, which belongs to someone else.

```mermaid
sequenceDiagram
  participant K as Kai, logged in
  participant G as Gateway
  participant A as Appointments
  participant P as Patients
  K->>G: GET /pets/9/history
  G->>G: is the user logged in? yes
  G->>A: get history for pet 9
  A->>P: get pet 9
  Note over P: the caller is Appointments, which I trust
  P-->>A: pet 9 belongs to another owner
  A-->>K: full history of someone else's pet
```

Every individual check passed. The gateway confirmed Kai is logged in. Patients confirmed the call came from Appointments, a trusted service. Yet Kai received another owner's data. Appointments has authority that Kai lacks, and it used that authority on Kai's behalf without asking whether Kai was entitled. That is the **confused deputy** problem: a more privileged intermediary is tricked into misusing its privileges for a less privileged requester.

There are two ways to deal with it.

**Centralised upstream authorisation.** The gateway checks everything before forwarding: "does pet 9 belong to Kai?" This requires the gateway to understand the rules of every service behind it. It becomes large, and every team's changes pass through it.

**Decentralised authorisation.** Each service decides for itself whether the *original user* may perform the action. For that, the service must reliably know who the original user is, even when the call arrives through two other services. The identity must travel with the request in a form that cannot be forged. That is what a JWT is for.

## 6. JSON Web Tokens

A **JSON Web Token (JWT)**, defined in RFC 7519, is a compact, signed piece of data that carries statements about a principal. Each statement is called a **claim**.

A JWT has three parts separated by dots: `header.payload.signature`.

- The **header** says which signing algorithm was used.
- The **payload** holds the claims: for example `sub` (the subject: who this is about), `exp` (the expiry time) and application claims such as a role or a list of scopes.
- The **signature** is computed over the header and payload with a key held by the issuer.

Two properties are worth stating firmly. A JWT is **signed, not encrypted**: anyone holding it can read the payload, so never put secrets in it. And it is **self-contained**: a service can validate it by checking the signature and the expiry, without calling the identity provider. This suits microservices well, because validation adds no network hop.

```python-run
import base64, hashlib, hmac, json

SIGNING_KEY = b"held-by-the-token-issuer"

def b64(data):                       # URL-safe base64 without padding, as JWTs use
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))

def issue(claims):
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64(json.dumps(claims).encode())
    signature = b64(hmac.new(SIGNING_KEY, f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"

def validate(token, now):
    header, payload, signature = token.split(".")
    expected = b64(hmac.new(SIGNING_KEY, f"{header}.{payload}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None, "rejected: bad signature"
    claims = json.loads(unb64(payload))
    if now >= claims["exp"]:
        return None, "rejected: expired"
    return claims, "valid"

token = issue({"sub": "owner-31", "role": "owner", "pets": [7], "exp": 1000})
print("token:", token[:40], "...")
print("payload is readable by anyone:", json.loads(unb64(token.split(".")[1])))
print("at time 900 :", validate(token, now=900)[1])
print("at time 1001:", validate(token, now=1001)[1])

# The holder edits the payload to claim pet 9 as well, keeping the old signature.
h, p, s = token.split(".")
forged_payload = b64(json.dumps({"sub": "owner-31", "role": "owner", "pets": [7, 9], "exp": 1000}).encode())
print("forged token:", validate(f"{h}.{forged_payload}.{s}", now=900)[1])

# The Patients service makes its own decision from the validated claims.
def patients_get_history(token, pet_id, now):
    claims, status = validate(token, now)
    if claims is None:
        return f"401 {status}"
    if claims["role"] == "owner" and pet_id not in claims["pets"]:
        return f"403 {claims['sub']} may not see pet {pet_id}"
    return f"200 history of pet {pet_id}"

print(patients_get_history(token, 7, now=900))
print(patients_get_history(token, 9, now=900))
```

`b64` and `unb64` convert bytes to and from the text encoding JWTs use. `issue` builds the three parts: an encoded header, an encoded payload of claims, and an HMAC signature over the first two. `validate` recomputes the signature, compares, and then checks the expiry.

The output shows each property in turn. The payload can be decoded by anyone, with no key. The token is valid before its expiry and rejected after. When the holder rewrites the payload to add pet 9, the old signature no longer matches and the token is rejected. Finally, `patients_get_history` shows the cure for the confused deputy: the Patients service validates the token it was handed and decides from the claims. Kai may see pet 7 and is refused pet 9, no matter which trusted service forwarded the request.

### How it fits together

1. The user logs in through the gateway and has an ordinary session.
2. For each incoming request, the gateway obtains a JWT for that user, valid for a short time (a minute or so), and attaches it to the request.
3. Each service passes the same token along when it calls another service.
4. Each service validates the token and applies its own authorisation rules.

In practice tokens are signed with a **private key** and checked with the matching **public key**. The issuer keeps the private key; every service may have the public key, which can verify signatures and cannot create them. Then no service is able to forge a token.

### Limits to know

- **Expiry against long processes.** A token valid for one minute is safe if stolen, and a saga that takes an hour will be holding an expired token. Options are longer lifetimes for specific flows, or re-issuing a token for the later steps.
- **Size.** Many claims make a large token that travels with every call.
- **Revocation is hard.** A self-contained token stays valid until it expires, which is the reason to keep lifetimes short.
- **Key distribution.** Services need the current public keys and must cope when keys are rotated.

The practice problem *Token Scopes Across a Call Chain and the Confused Deputy* has you trace which calls a token permits along a chain of services.

> [!INTERVIEW]
> For "how do services know who the end user is, and how do you prevent one user reading another's data?": *the gateway authenticates the user through an identity provider with OpenID Connect and does coarse authorisation. It then attaches a short-lived signed JWT carrying the user's identity and claims. Each service passes the token on, validates the signature and expiry locally with the issuer's public key, and makes its own fine-grained decision. That avoids the confused deputy, where a trusted service fetches data its caller should not see. Between services I use mutual TLS, so the channel is encrypted and both ends are authenticated.*

## 7. Pitfalls

- **Trusting anything inside the network.** One compromised service or stolen laptop then reaches everything.
- **Checking only at the gateway.** Services that skip checks are open to the confused deputy.
- **Authorising the calling service and not the user.** "It came from Appointments" says nothing about what Kai may see.
- **Secrets in a JWT payload.** The payload is readable by anyone who holds the token.
- **Not checking the signature or the expiry.** An unvalidated token is a note the user wrote to themselves.
- **Very long-lived tokens.** They cannot easily be revoked.
- **Inventing encryption or storing passwords reversibly.** Use reviewed libraries and salted, slow password hashes.
- **Keys stored next to the data.** Whoever copies one copies both.
- **All authorisation rules in a central gateway.** It turns into a bottleneck every team must edit.

## Summary

- Implicit trust protects only the perimeter; zero trust checks and encrypts every call. Zoning by data sensitivity is a practical middle path.
- Data in transit raises four concerns: server identity, client identity, visibility and manipulation. TLS covers three, and mutual TLS covers all four.
- For data at rest: use reviewed libraries, store passwords as salted slow hashes, encrypt what is sensitive, collect less, keep keys apart from data, and encrypt backups.
- Authentication establishes identity; authorisation decides what that identity may do.
- Users sign on once through an identity provider; the gateway handles login and coarse checks, and services make fine-grained decisions.
- The confused deputy is a privileged intermediary acting for a requester without checking the requester's rights.
- A JWT is a signed, readable, self-contained set of claims that carries the user's identity through a chain of calls so that each service can decide for itself.

## Glossary

| Term | Meaning |
|---|---|
| Implicit trust | Treating all calls from inside the network as safe |
| Zero trust | Treating every call as possibly hostile and verifying each one |
| Data in transit / at rest | Data moving over a network / data stored on disk |
| TLS | The standard protocol for encrypted, tamper-evident connections |
| Certificate | A signed document binding an identity to a key |
| Mutual TLS | TLS in which both client and server present certificates |
| Signature | A value proving a message came from a key holder and was not altered |
| Hash function | A function producing a fixed-size fingerprint of its input |
| Salt | A random per-user value mixed into a password hash |
| Authentication | Confirming who a principal is |
| Authorisation | Deciding what a principal may do |
| Principal | The person or program being authenticated |
| Single sign-on | Logging in once to use many services |
| Identity provider | The system that holds accounts and verifies credentials |
| Confused deputy | A privileged intermediary tricked into acting beyond the requester's rights |
| JWT | A signed token carrying claims about a principal |
| Claim | One statement inside a token, such as the subject or expiry |

```quiz
[
  {"q": "What is the core assumption of zero trust?", "options": ["Calls from inside the network are safe", "The network may already be compromised, so every call must be verified and encrypted", "Only the gateway needs security", "Users never make mistakes"], "answer": 1,
   "explain": "Zero trust removes the idea of a safe inside. Each service authenticates and authorises every caller."},
  {"q": "What does mutual TLS add to ordinary TLS?", "options": ["Faster connections", "The client also proves its identity with a certificate, so both sides are authenticated", "Compression", "Password hashing"], "answer": 1,
   "explain": "Ordinary TLS authenticates the server and protects the channel. Mutual TLS also authenticates the client."},
  {"q": "Why should passwords be stored as salted, slow hashes?", "options": ["So administrators can read them", "A unique salt hides equal passwords and defeats precomputed tables, and slowness makes mass guessing impractical", "Hashes can be decrypted when needed", "It saves disk space"], "answer": 1,
   "explain": "The stored value cannot be reversed, differs between users with the same password, and is expensive to brute-force."},
  {"q": "What is the difference between authentication and authorisation?", "options": ["They are the same", "Authentication confirms who you are; authorisation decides what you may do", "Authorisation happens first", "Authentication is only for services"], "answer": 1,
   "explain": "Identity is established first, and permissions are then decided for that identity."},
  {"q": "A logged-in owner requests another owner's pet history, and a trusted internal service fetches it without checking. What is this problem called?", "options": ["A cold start", "The confused deputy", "Clock skew", "A semantic break"], "answer": 1,
   "explain": "An intermediary with more privilege acted for a requester without verifying the requester's own rights."},
  {"q": "Which statement about a JWT is correct?", "options": ["Its payload is encrypted and unreadable", "Its payload is readable by anyone holding it; the signature stops it being altered undetected", "It never expires", "It must be checked with the identity provider on every call"], "answer": 1,
   "explain": "A standard JWT is signed, not encrypted. Validation checks the signature and expiry locally."},
  {"q": "A user edits the payload of their JWT to add a permission and keeps the original signature. What happens when a service validates it?", "options": ["It is accepted", "It is rejected, because the signature no longer matches the altered content", "The service crashes", "The token is automatically re-signed"], "answer": 1,
   "explain": "The signature is computed over the header and payload with a key the user does not have. Any change invalidates it."},
  {"q": "Why are JWTs usually given short lifetimes?", "options": ["To save bandwidth", "A self-contained token is hard to revoke, so a short expiry limits how long a stolen one is useful", "Long tokens cannot be signed", "Browsers reject long lifetimes"], "answer": 1,
   "explain": "Services validate tokens without contacting the issuer, so the main control over a leaked token is that it soon expires."}
]
```

> **Source:** Newman, *Building Microservices*, 2nd ed., ch. 11 (topic coverage only; wording and the Pawprint example are original). RFC 7519, "JSON Web Token (JWT)", https://www.rfc-editor.org/rfc/rfc7519 ; NIST Special Publication 800-207, "Zero Trust Architecture".
