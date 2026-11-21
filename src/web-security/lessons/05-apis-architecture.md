# APIs, dependencies and architecture review

> **Before this lesson:** you should be comfortable with HTTP methods and JSON from [HTTP, origins and the same-origin policy](#/lesson/web-security/http-same-origin) and with the three authorisation questions from [Authentication and authorisation models](#/lesson/web-security/authn-authz).

## In plain words

A restaurant has two faces. Customers see the dining room: menus, tables, a waiter. Behind a door is the kitchen, with its ovens, knives and storeroom. The waiter is the only link between the two. You tell the waiter what you want in an agreed form ("number 14, no onions"), and the waiter brings back a plate. You never walk into the kitchen yourself.

In a modern web application the web page or phone app is the dining room, and the server with its database is the kitchen. The waiter is the **API** — the *application programming interface*: a published list of requests the server will accept and the answers it will give. Every interesting thing the application can do goes through that list.

For security this has a blunt consequence. An attacker does not need your web page. They can talk to the waiter directly, order things that are not on the printed menu, and see how the kitchen reacts. So to protect an application you first need a clear picture of **what is in it**: which requests exist, what data flows where, and which parts were written by someone else. This lesson builds that picture. You cannot defend what you have not mapped.

## The shape of a modern application

Twenty years ago a typical site built complete pages on the server. Today most are split:

```mermaid
flowchart LR
    U[Browser or phone app] -->|HTTPS + JSON| G[API server]
    G --> D[(Database)]
    G --> C[(Cache)]
    G -->|HTTPS| P[Payment provider]
    G -->|HTTPS| M[Email service]
    U -->|loads scripts| N[CDN and third-party scripts]
    subgraph Yours
      G
      D
      C
    end
```

- The **front end** runs in the browser. Sites built this way are often called *single-page applications* (SPAs) because the browser loads one page and then fetches data as needed.
- The **back end** is the API server and its data stores.
- **Third parties** provide payments, email, analytics, and scripts delivered through a **CDN** (content delivery network — servers around the world that hand out static files quickly).

Every arrow in the diagram crosses a trust boundary and is a place where data must be checked. Every box you do not own is a dependency you are trusting.

## REST: the common style of API

Most web APIs follow a style called **REST** (Representational State Transfer). You do not need the theory, only the conventions:

- Things are **resources** with addresses: `/orders`, `/orders/17`, `/orders/17/items`.
- The HTTP **method** says what to do with the resource.
- Data travels as **JSON**.
- The **status code** reports the outcome.

| Request | Meaning |
|---|---|
| `GET /orders` | List orders |
| `GET /orders/17` | Read order 17 |
| `POST /orders` | Create an order |
| `PATCH /orders/17` | Change part of order 17 |
| `DELETE /orders/17` | Remove order 17 |

The regularity is pleasant for developers and equally pleasant for attackers: once someone has seen `GET /orders/17`, they will guess that `GET /orders/18`, `DELETE /orders/17` and `GET /users/1` exist. An API's **attack surface** — the total set of places where it accepts input — is the full table of resources × methods, not the handful your own front end happens to call.

## Three API mistakes, from simplest to subtlest

OWASP maintains a separate *API Security Top 10*. Three of its entries appear in almost every code base and are worth learning as patterns. We will take them one at a time with the same toy shop.

### 1. Returning too much

The simplest example first. An endpoint returns the user's profile by handing the database record straight to the JSON encoder:

```python
# VULNERABLE: whatever columns the table has are sent to the browser
@app.get("/api/me")
def me(user=Depends(current_user)):
    return db.get_user(user.id)       # includes password_hash, reset_token, is_admin...
```

The page only *displays* the name and email, so everything looks fine. But the full JSON is visible to anyone who opens the Network tab. This is **excessive data exposure**: relying on the front end to hide fields the API should never have sent.

```python
# FIXED: an explicit list of fields that may leave the server
class PublicUser(BaseModel):
    id: int
    name: str
    email: str

@app.get("/api/me", response_model=PublicUser)
def me(user=Depends(current_user)):
    return db.get_user(user.id)
```

`PublicUser` is a Pydantic model — a class that describes the exact shape of some data. `response_model=PublicUser` tells FastAPI to copy only those three fields into the response and drop everything else. This is an **allow-list for output**: a new column added to the table next year stays private unless someone deliberately adds it to the model.

The same idea in plain Python, so you can run it:

```python-run
PUBLIC_FIELDS = ("id", "name", "email")          # the allow-list

def to_public(record: dict) -> dict:
    # build a NEW dict containing only the permitted keys
    return {key: record[key] for key in PUBLIC_FIELDS if key in record}

row = {"id": 7, "name": "Ann", "email": "ann@shop.example",
       "password_hash": "pbkdf2_sha256$600000$...", "is_admin": False, "reset_token": "t-91f"}

print(to_public(row))
```

The expression in braces is a *dict comprehension*: it loops over the allowed names and copies each one that exists. `password_hash`, `is_admin` and `reset_token` are never mentioned, so they cannot leak.

### 2. Accepting too much (mass assignment)

Now the mirror image. An update endpoint copies every field from the request body onto the record:

```python
# VULNERABLE: the client chooses which columns to overwrite
@app.patch("/api/me")
def update_me(changes: dict, user=Depends(current_user)):
    db.update_user(user.id, **changes)     # {"name": "Ann"} ... or {"is_admin": true}
```

The form on the page sends `{"name": "Ann"}`. Nothing prevents a curious user from sending `{"is_admin": true}` or `{"credit_balance": 99999}` instead. This is **mass assignment**: binding request data to internal fields wholesale.

```python
# FIXED: only named fields are accepted, and unknown ones are an error
class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")   # reject fields not listed below
    name: str | None = None
    email: EmailStr | None = None

@app.patch("/api/me")
def update_me(changes: ProfileUpdate, user=Depends(current_user)):
    db.update_user(user.id, **changes.model_dump(exclude_unset=True))
```

`extra="forbid"` makes any unexpected key a validation error (`422`). `model_dump(exclude_unset=True)` returns only the fields the client actually sent. Input and output now each have their own explicit allow-list — and they are *different* lists, which is the point.

### 3. Forgetting the third question

`GET /api/orders/17` checks that the caller is logged in and returns order 17 — whoever it belongs to. This is **broken object-level authorisation**, also known as IDOR (insecure direct object reference). It is the most common serious API flaw, and has a whole lesson: [Broken access control and IDOR](#/lesson/web-security/broken-access-control). For now, note the fix in one line: the query must include the owner, `WHERE id = ? AND customer_id = ?`.

> [!WARNING]
> "The front end never sends that field" and "the front end never shows that field" are not security properties. The API is the product; the front end is merely one of its clients.

## Prototype pollution: when merged JSON reaches the object blueprint

The two mistakes above are about *which fields* a client may send. There is a JavaScript-specific cousin that is about *which object* the fields land on. It matters whenever your back end or front end is written in JavaScript (Node.js, for example), and it is a favourite interview topic because it needs a little language knowledge to understand.

### First, what a prototype is

In JavaScript almost every object has a hidden link to another object called its **prototype**, which acts as a shared blueprint. When you read a property that the object itself does not have, JavaScript does not give up. It follows the link and looks in the prototype, then in the prototype's prototype, and so on until the chain ends. This lookup path is the **prototype chain**.

An everyday comparison: you ask an employee for the office wifi password. They do not know it, so they say "ask my manager". The manager does not know either and says "ask the front desk". The question climbs a chain of people until someone answers or there is nobody left.

```javascript
const user = { name: "Ann" };

user.name;        // "Ann"      found on the object itself
user.toString;    // a function found one step up, on Object.prototype
user.isAdmin;     // undefined  nobody in the chain has it
```

`toString` was never written on `user`, yet it works, because `user` is linked to **`Object.prototype`**, the blueprint that nearly every plain object inherits from. The name `__proto__` is a special property that exposes that link: `user.__proto__` is `Object.prototype`. (`constructor.prototype` is another route to the same place.)

The consequence that makes this a security topic: **`Object.prototype` is shared by every plain object in the whole program.** If something adds a property to it, every object that does not define that property itself suddenly appears to have it.

### How the pollution happens

**Prototype pollution** is a bug where attacker-controlled data ends up *writing into a prototype* instead of into an ordinary object. The usual route is a **merge** (also called deep merge or "extend") function: code that copies every key of one object into another, descending into nested objects. Settings loaders, "update my profile" handlers and utility libraries all contain one.

```javascript
// VULNERABLE: copies keys without asking which keys they are
function merge(target, source) {
  for (const key in source) {
    if (typeof source[key] === "object" && source[key] !== null) {
      target[key] = merge(target[key] || {}, source[key]);   // descend
    } else {
      target[key] = source[key];                             // copy
    }
  }
  return target;
}

const settings = merge({}, JSON.parse(requestBody));
```

Walk through what a normal body does: `{"theme": "dark"}` copies one key. Now think about a body whose key is the special name `__proto__` with a nested object as its value. `JSON.parse` happily creates an ordinary property with that name. The merge sees an object, so it descends: `target["__proto__"]` does not hold a new empty object, it resolves to the **real `Object.prototype`**, and the merge then writes the nested keys straight onto it. From then on:

```javascript
const someOtherObject = {};
someOtherObject.isAdmin;   // now true, although nobody ever set it on this object
```

The attacker never touched `someOtherObject`. They changed the blueprint, and every object inherited the change until the process restarts.

```mermaid
flowchart TD
    A[Untrusted JSON with a __proto__ key] --> B[Merge function descends into it]
    B --> C[target dot __proto__ resolves to Object.prototype]
    C --> D[New properties are written onto the shared blueprint]
    D --> E[Every plain object inherits them]
    E --> F[Code that checks a missing property is fooled]
```

### Why it matters: the impact

On its own, adding a property seems harmless. The damage comes from code that **reads a property that is normally absent** and trusts a present value:

- **Authorisation bypass.** A check such as `if (user.isAdmin)` is true for any user object without its own `isAdmin` once the prototype has one.
- **Denial of service.** Overwriting a built-in such as `toString` with a value that is not a function makes ordinary operations throw errors in every request until the server is restarted.
- **Changed behaviour of libraries.** Code that reads optional settings (`options.timeout`, `options.template`) takes the polluted defaults. In some applications this has been chained into much worse outcomes, including code execution through template engines or process-spawning options. Those chains depend on the specific library, which is why the root cause is treated as serious in itself.
- **In the browser**, polluted properties can reach XSS sinks, linking this topic to the previous lesson.

Because the state is **process-wide and persistent**, one request can change the behaviour of all later requests from all users. That is what separates it from most input bugs, which affect one request.

### Prevention

No single trick covers everything, so use several layers.

1. **Validate against a schema before merging.** Define exactly which fields are allowed and reject everything else, exactly as the `extra="forbid"` example did for mass assignment. In JavaScript this is what libraries such as Zod, Ajv (JSON Schema) and Joi are for. A strict schema simply never lets a `__proto__` key through.
2. **Never use a generic recursive merge on untrusted input.** Copy a short list of named fields instead. If you must merge, skip the dangerous keys (`__proto__`, `constructor`, `prototype`) and use a well-maintained library that already does, kept up to date.
3. **Use objects that have no prototype.** `Object.create(null)` makes an object with no link at all, so there is no shared blueprint to reach.
4. **Use a `Map` for dictionaries keyed by user data.** A `Map` stores entries separately from its properties, so a key named `__proto__` is just a key.
5. **Check ownership when reading.** `Object.hasOwn(obj, "isAdmin")` is true only for a property on the object itself, so inherited (polluted) values are ignored.
6. **Freeze the blueprint.** `Object.freeze(Object.prototype)` at start-up makes writes to it fail. This is a useful safety net, but test it: some old libraries modify built-ins and will break. Node.js also offers a start-up flag that removes the `__proto__` accessor, `--disable-proto=delete`, for applications that do not need it.
7. **Keep dependencies updated.** Most real-world cases were bugs in popular merge and query-string libraries, found and fixed one by one; the lesson on dependencies covers how to keep up.

```javascript
// SAFER: a prototype-free dictionary, a Map, and a schema-checked update
const counts = Object.create(null);          // no inherited keys at all
counts[userKey] = (counts[userKey] ?? 0) + 1;

const byName = new Map();                    // user keys are never confused with properties
byName.set(userKey, profile);

const update = ProfileSchema.strict().parse(JSON.parse(requestBody));   // unknown keys rejected
```

`counts[userKey] ?? 0` means "use the stored number, or 0 if absent". `.strict()` is the schema library's way of saying that keys not listed are an error.

> [!NOTE]
> The same family of bug exists wherever a language lets data choose *which attribute or key it writes to* on a shared structure. The habit that prevents it is the one this lesson keeps repeating: decide the allowed keys on the server, never let the client name them.

> [!INTERVIEW]
> "What is prototype pollution?" Untrusted data reaches a merge or assignment that writes into `Object.prototype` through a key such as `__proto__`, so every object in the process inherits attacker-chosen properties. It leads to authorisation bypass, denial of service or worse. Prevent with schema validation, no generic merges on untrusted input, `Object.create(null)` or `Map`, `Object.hasOwn`, and updated libraries.

## GraphQL: one endpoint, many questions

**GraphQL** is an alternative to REST in which the client sends a *query* describing exactly which fields it wants, usually to a single address such as `/graphql`:

```graphql
query {
  order(id: 17) {
    id
    total
    customer { name email }
  }
}
```

The server replies with JSON in the same shape. This flexibility is convenient, and it moves the security work rather than removing it:

- **Authorisation must be per field and per object.** Because clients compose their own queries, there is no single handler in which to put one check. Each *resolver* — the function that fetches one field — must enforce access, or `customer { email }` becomes reachable through some path nobody thought about.
- **Introspection.** GraphQL servers can describe their entire schema on request. That is helpful in development and, in production, hands an outsider the complete menu, including fields the front end never uses. Many teams disable it in production or restrict it to authenticated staff. Hiding the schema is not a substitute for authorisation; it only removes a convenience.
- **Expensive queries.** A client can nest relationships deeply — orders → customer → orders → customer… — and make the server do enormous work with one small request. Defences are limits on **depth**, on computed **cost**, on result sizes, and timeouts.
- **Batching.** Many operations can be packed into one HTTP request, which can slip past rate limits that count requests. Limit operations per request and count them individually.

A depth limiter is a pleasant small example. Here a query is represented as nested dictionaries, where each key is a field and each value is the set of sub-fields requested:

```python-run
def depth(selection: dict) -> int:
    if not selection:                 # a leaf field such as "id" has no children
        return 0
    return 1 + max(depth(child) for child in selection.values())

ok_query = {"order": {"id": {}, "total": {}, "customer": {"name": {}}}}
deep_query = {"order": {"customer": {"orders": {"customer": {"orders": {"customer": {"email": {}}}}}}}}

MAX_DEPTH = 4
for name, q in [("ok", ok_query), ("deep", deep_query)]:
    d = depth(q)
    print(name, "depth", d, "->", "accepted" if d <= MAX_DEPTH else "rejected")
```

`depth` is *recursive*: it calls itself on each child and adds one for the current level. The first query is three levels deep and is accepted; the second loops between `customer` and `orders` to reach seven levels and is rejected before any database work is done. Real GraphQL libraries provide this as a validation rule you switch on.

## Code you did not write: third-party dependencies

Open any project's dependency file — `requirements.txt` or `pyproject.toml` in Python, `package.json` in JavaScript — and you will find a dozen or two libraries. A **dependency** is someone else's code that yours needs in order to run. Those libraries have their own dependencies, called **transitive dependencies**, and the full tree commonly holds hundreds or thousands of packages.

All of that code runs with the same permissions as code you typed yourself. It can read your environment variables, open network connections and touch the database. Three consequences follow:

1. A **known vulnerability** in any package in the tree may be a vulnerability in your application.
2. A **malicious package** — a hijacked maintainer account, or a look-alike name such as `reqeusts` — runs inside your walls.
3. **Third-party scripts in the page** (analytics, chat widgets, advertising) run with your origin's full power in every visitor's browser.

The defences — lock files, automated scanning, pinning, integrity hashes — are the subject of [Vulnerable dependencies and the supply chain](#/lesson/web-security/dependencies-supply-chain). At the architecture stage the task is more basic: **know what you depend on**, and prefer fewer, well-maintained dependencies over many obscure ones.

> [!TIP]
> Before adding a package, spend two minutes on it: When was the last release? How many maintainers? How many dependencies does *it* pull in? Could twenty lines of your own code do the job? Each dependency is a long-term trust relationship, not a free download.

## Architecture review: reading a system for weak points

An **architecture review** looks at the design as a whole, before or alongside reading code. You are not hunting individual bugs yet; you are looking for *signs* of where bugs will cluster. It takes four steps.

**Step 1 — Draw it.** Boxes for components, arrows for data flows, a dashed line around what you control. The diagram near the top of this lesson is enough to start.

**Step 2 — List the entry points.** Every route, every method, every webhook (an HTTP call another company makes *to* you), file upload, message queue and admin tool. This is the attack surface.

**Step 3 — For each entry point, answer five questions.**

| Question | What a good answer looks like |
|---|---|
| Who may call it? | "Authenticated customers" — enforced by shared middleware |
| What input does it accept? | A schema with types, lengths and no unknown fields |
| What does it touch? | Named tables or services, with least privilege |
| What does it return? | A response model, not a raw record |
| What is logged? | Who did what to which object, without secrets |

**Step 4 — Look for the signals.**

| Signals of a healthy design | Warning signs |
|---|---|
| One shared mechanism for authentication and authorisation | Each endpoint doing its own checks, each slightly differently |
| Standard, well-known libraries for cryptography, sessions, sanitising | Home-made encryption, token formats or sanitisers |
| Validation and encoding done in one layer, the same way everywhere | Copy-pasted validation with small variations |
| Database access through parameterised queries or an ORM | SQL built by joining strings |
| Secrets loaded from the environment or a secrets manager | Keys in source files |
| Old and new parts following the same rules | A legacy area "nobody touches" that predates current practice |

The idea behind the table is consistency. Where a project solves a security problem once, centrally, a mistake is unlikely and easy to fix everywhere. Where every feature re-solves the same problem, some attempts will be wrong — and those are where you focus your code review. Home-made security mechanisms deserve particular suspicion: a team that wrote its own password-hashing or session scheme has probably repeated mistakes that the standard libraries fixed years ago.

> [!INTERVIEW]
> "How would you approach securing an application you have recently joined?" A good structure: (1) map it — components, data flows, entry points, dependencies; (2) identify the most valuable assets and the most exposed entry points; (3) check that authentication, authorisation, validation and logging are centralised; (4) prioritise the gaps by risk. Starting with a map shows you will not chase random bugs.

## Defence in depth for APIs

- **Authenticate every route by default**; mark public ones explicitly.
- **Authorise at the object and field level**, on the server.
- **Schemas for input** (types, ranges, lengths, no extra fields) **and for output** (response models).
- **Limits**: page sizes, request body size, query depth and cost, rate limits per user and per address.
- **Consistent errors** that do not reveal internals.
- **Inventory**: a generated list of all routes (for example from OpenAPI), reviewed when it changes, so that forgotten or "temporary" endpoints do not linger.
- **Dependency hygiene**: lock, scan, update.

## How to test it

- **Generate the route list** from the framework and compare it with what the front end uses. Routes nobody calls are prime suspects — old versions (`/api/v1/…`), debug helpers, internal tools.
- **Read raw responses** in the Network tab, not the rendered page, looking for fields that should not be there.
- **Send extra fields** in create and update requests (`"role"`, `"is_admin"`, `"price"`, `"owner_id"`) and see whether they stick.
- **Request huge things**: `?limit=1000000`, deeply nested GraphQL queries, large bodies. The answer should be a polite refusal.
- **Try other methods** on each path.
- **For GraphQL**, check whether introspection is available to anonymous callers in production and whether each resolver enforces access.

## Pitfalls

- **"Internal" APIs that are reachable from the internet.** If a browser can call it, so can anyone.
- **Old API versions left running** without the fixes applied to the new one.
- **Different rules on the mobile API** than on the web API for the same data.
- **Filtering in the client.** The server sends all records and the page shows "yours"; the rest are one click away in the developer tools.
- **Trusting webhooks** without verifying the sender's signature.
- **Assuming GraphQL is safer because there is only one URL.** One URL can expose the whole data model.
- **Adding dependencies casually**, then never updating them.

## Summary

- The API is the real application; the front end is one client among many possible ones.
- REST makes resources predictable, so every resource × method must be protected, not only those your pages use.
- Return only allow-listed fields; accept only allow-listed fields; check the specific object.
- GraphQL shifts authorisation into resolvers and adds risks from introspection, deep queries and batching.
- Dependencies run with your privileges; know what is in the tree.
- An architecture review maps components, flows and entry points, then looks for consistency: central mechanisms are a good sign, reinvention and inconsistency are where bugs hide.

## Glossary

- **API** — the set of requests a server accepts from programs.
- **REST** — a style of API built from resources, HTTP methods and JSON.
- **Resource** — a thing addressed by a URL, such as an order.
- **Single-page application (SPA)** — a front end that loads once and fetches data through an API.
- **CDN** — a network of servers distributing static files.
- **Attack surface** — all the points where a system accepts input.
- **Excessive data exposure** — returning more fields than the caller should see.
- **Mass assignment** — letting request data overwrite internal fields wholesale.
- **Response model / schema** — an explicit description of permitted fields and types.
- **GraphQL** — a query language in which clients choose the fields returned.
- **Resolver** — the function that fetches one GraphQL field.
- **Introspection** — a GraphQL server describing its own schema.
- **Dependency / transitive dependency** — a library you use / a library your library uses.
- **Webhook** — an HTTP request another service sends to your application.
- **Architecture review** — examining a system's design for structural weaknesses.
- **Prototype** — the object another object is linked to and inherits missing properties from.
- **Prototype chain** — the sequence of links JavaScript follows when looking up a property.
- **`Object.prototype`** — the blueprint shared by almost every plain JavaScript object.
- **Prototype pollution** — writing attacker-chosen properties onto a shared prototype, usually through a merge of untrusted data.
- **Deep merge** — copying one object's keys into another, descending into nested objects.
- **`Object.create(null)`** — makes an object with no prototype.
- **`Map`** — a key-value collection that keeps entries separate from object properties.

```quiz
[
  {"q": "An endpoint returns the full user record as JSON and the page displays only the name. Why is this a vulnerability?",
   "options": ["JSON is insecure", "The hidden fields are still delivered to the client and readable in the developer tools", "The page will render slowly", "It is not a vulnerability"], "answer": 1,
   "explain": "What the page shows is irrelevant; what the API sends is what an attacker receives. Use a response model that lists permitted fields."},
  {"q": "A profile update handler applies every key in the request body to the user record. A user sends {\"is_admin\": true}. What is this flaw called?",
   "options": ["Cross-site scripting", "Mass assignment", "SQL injection", "Clickjacking"], "answer": 1,
   "explain": "Mass assignment binds client input to internal fields without an allow-list. Accept only named fields and reject unknown ones."},
  {"q": "Why does a REST API's predictability matter for security?",
   "options": ["It makes HTTPS unnecessary", "Seeing one endpoint lets an attacker guess others, so all resource and method combinations must be protected", "It prevents injection", "It hides the database"], "answer": 1,
   "explain": "Conventions help attackers enumerate the surface. Protection cannot depend on an endpoint being unknown."},
  {"q": "In GraphQL, where must authorisation be enforced?",
   "options": ["Only at the /graphql URL", "In the front end's query builder", "In the resolvers, per object and field", "It is not needed because there is one endpoint"], "answer": 2,
   "explain": "Clients compose arbitrary queries, so a single check at the endpoint cannot know which data will be reached. Each resolver must enforce access."},
  {"q": "Which defence addresses a GraphQL query that nests relationships ten levels deep?",
   "options": ["HttpOnly cookies", "A query depth or cost limit", "A longer session timeout", "Disabling HTTPS"], "answer": 1,
   "explain": "Depth and cost limits reject queries that would make the server do disproportionate work."},
  {"q": "What is a transitive dependency?",
   "options": ["A library you install directly", "A library required by one of your libraries", "A deprecated library", "A library loaded from a CDN"], "answer": 1,
   "explain": "Most of a dependency tree consists of packages you never chose explicitly, and they run with the same privileges as your own code."},
  {"q": "During an architecture review you find that each endpoint implements its own, slightly different, permission check. What does this signal?",
   "options": ["A flexible design", "A higher chance that some checks are wrong or missing; review them closely", "That RBAC is in use", "Nothing"], "answer": 1,
   "explain": "Inconsistency means the problem was solved many times, and some solutions will be flawed. Centralised mechanisms are a sign of health."},
  {"q": "Which is the best first step when asked to assess an unfamiliar application's security?",
   "options": ["Run random payloads against the login form", "Map components, data flows, entry points and dependencies", "Rewrite the authentication system", "Enable every scanner at once and read nothing"], "answer": 1,
   "explain": "You cannot prioritise or defend what you have not mapped. The map tells you where the valuable assets and exposed entry points are."},
  {"q": "What makes prototype pollution more serious than many input bugs?",
   "options": ["It only affects the attacker", "It changes a blueprint shared by all objects, so the effect is process-wide and lasts until restart", "It requires physical access", "It only breaks the logging"], "answer": 1,
   "explain": "Object.prototype is shared. One polluted request can alter behaviour for every later request and every user in that process."},
  {"q": "Which request body key is the classic route into Object.prototype through a vulnerable merge?",
   "options": ["name", "__proto__", "email", "id"], "answer": 1,
   "explain": "__proto__ exposes the link to the prototype, so a merge that descends into it writes onto the shared blueprint."},
  {"q": "Which choice avoids the problem for a dictionary keyed by user-supplied names?",
   "options": ["A plain object literal", "A Map or Object.create(null)", "A longer variable name", "JSON.stringify on every key"], "answer": 1,
   "explain": "A Map keeps entries apart from properties, and Object.create(null) has no prototype to reach."},
  {"q": "Why does a check like if (user.isAdmin) become dangerous after pollution?",
   "options": ["isAdmin is a reserved word", "Objects without their own isAdmin inherit the polluted value and pass the check", "The check runs slower", "It throws an error"], "answer": 1,
   "explain": "Code that reads a normally absent property trusts whatever the prototype chain returns. Use Object.hasOwn or explicit fields."}
]
```

> **Source:** Hoffman, *Web Application Security*, ch. 3 (structure of a modern web application), ch. 5 (API analysis), ch. 6 (third-party dependencies) and ch. 7 (weak points in application architecture), in original wording. OWASP API Security Top 10 — https://owasp.org/API-Security/ ; OWASP GraphQL Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html ; OWASP Mass Assignment Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html ; OWASP REST Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
