_SCOPES = {"catalog": "singleton", "requestLog": "request", "cart": "session", "visitCounter": "application",
           "priceQuote": "prototype"}

_RULES = [
    ["GET", "/", "permitAll"],
    ["*", "/actuator/health", "permitAll"],
    ["*", "/actuator/**", "hasRole:OPS"],
    ["GET", "/api/books/**", "permitAll"],
    ["POST", "/api/books", "hasAnyRole:EDITOR,ADMIN"],
    ["DELETE", "/api/books/*", "hasRole:ADMIN"],
    ["*", "/api/orders/**", "authenticated"],
    ["*", "/api/reports/*/export", "hasAuthority:SCOPE_reports:read"],
    ["*", "/internal/**", "denyAll"],
]
_ANON = None
_READER = {"authorities": ["ROLE_USER"]}
_EDITOR = {"authorities": ["ROLE_EDITOR", "SCOPE_reports:read"]}
_ADMIN = {"authorities": ["ROLE_ADMIN", "ROLE_OPS"]}

_CFG = {"issuer": "https://auth.bookshop.example", "audience": "bookshop-api", "skew": 60,
        "algorithms": ["RS256", "ES256"], "required_scopes": ["orders:read"]}


def _tok(alg="RS256", **claims):
    base = {"iss": "https://auth.bookshop.example", "aud": "bookshop-api", "exp": 2000, "scope": "orders:read profile"}
    base.update(claims)
    return {"header": {"alg": alg}, "claims": {k: v for k, v in base.items() if v != "DROP"}}


_APP = [
    {"name": "bookController", "kind": "controller", "deps": ["bookService"]},
    {"name": "orderController", "kind": "controller", "deps": ["orderService", "priceFormatter"]},
    {"name": "apiErrors", "kind": "controller-advice", "deps": []},
    {"name": "requestIdFilter", "kind": "filter", "deps": []},
    {"name": "priceFormatter", "kind": "converter", "deps": []},
    {"name": "moneySerializer", "kind": "json-component", "deps": []},
    {"name": "bookService", "kind": "service", "deps": ["bookRepository", "clock"]},
    {"name": "orderService", "kind": "service", "deps": ["orderRepository", "bookService", "paymentClient"]},
    {"name": "bookRepository", "kind": "repository", "deps": []},
    {"name": "orderRepository", "kind": "repository", "deps": []},
    {"name": "paymentClient", "kind": "component", "deps": []},
    {"name": "clock", "kind": "configuration", "deps": []},
]

_ORDER = ["DOWN", "OUT_OF_SERVICE", "UP", "UNKNOWN"]

PROBLEMS = [
dict(
    id="spring-web-scope-lifetime",
    title="Request, session and application scope lifetimes",
    difficulty="Medium",
    pattern="Web scopes",
    entry="instances",
    description=r"""
In a web application a bean's scope can follow the HTTP traffic. Count how many instances of each bean the
container creates for a stream of events.

`instances(beans, events)`:

- `beans` — dict `name -> scope`, with scope one of `"singleton"`, `"application"`, `"session"`, `"request"`,
  `"prototype"`.
- `events` — in time order, each either
  - `["request", session_id, [bean names used]]` — one HTTP request belonging to the HTTP session `session_id`;
    the list says which beans the request's code touches, in order, possibly the same bean several times; or
  - `["invalidate", session_id]` — the session ends (logout or timeout). A later request with the same id starts
    a brand-new session.

Creation rules:

| scope | a new instance is created… |
|---|---|
| `singleton` | once, at start-up, even if never used |
| `application` | on first use, then shared by everybody for the life of the app |
| `session` | on first use within each HTTP session |
| `request` | on first use within each HTTP request |
| `prototype` | on every single use |

Return a dict `name -> number of instances created`.

**Example:** beans `{"cart": "session", "requestLog": "request"}`, events
`[["request","s1",["cart","requestLog","requestLog"]], ["request","s1",["cart","requestLog"]]]` →
`{"cart": 1, "requestLog": 2}`.
""",
    starter='''def instances(beans: dict, events: list) -> dict:
    pass
''',
    solution='''def instances(beans, events):
    count = {name: (1 if scope == "singleton" else 0) for name, scope in beans.items()}
    application = set()
    sessions = {}
    for event in events:
        if event[0] == "invalidate":
            sessions.pop(event[1], None)
            continue
        _, session_id, used = event
        session_beans = sessions.setdefault(session_id, set())
        request_beans = set()
        for name in used:
            scope = beans[name]
            if scope == "singleton":
                continue
            if scope == "prototype":
                count[name] += 1
                continue
            store = {"application": application, "session": session_beans, "request": request_beans}[scope]
            if name not in store:
                store.add(name)
                count[name] += 1
    return count
''',
    tests=[
        [{"cart": "session", "requestLog": "request"},
         [["request", "s1", ["cart", "requestLog", "requestLog"]], ["request", "s1", ["cart", "requestLog"]]]],
        [_SCOPES, []],
        [_SCOPES, [["request", "s1", ["catalog", "requestLog", "cart", "visitCounter", "priceQuote", "priceQuote"]]]],
        [_SCOPES, [["request", "s1", ["cart"]], ["request", "s2", ["cart"]], ["request", "s1", ["cart", "cart"]]]],
        [_SCOPES, [["request", "s1", ["cart"]], ["invalidate", "s1"], ["request", "s1", ["cart"]]]],
        [_SCOPES, [["invalidate", "ghost"], ["request", "s1", []], ["request", "s1", ["requestLog"]]]],
        [_SCOPES, [["request", "s%d" % (i % 3), ["visitCounter", "requestLog", "cart", "catalog"]] for i in range(12)]],
        [_SCOPES, [["request", "a", ["priceQuote"] * 5 + ["requestLog"] * 5]]],
        [_SCOPES, [["request", "a", ["cart"]], ["request", "b", ["visitCounter"]], ["invalidate", "a"],
                   ["invalidate", "b"], ["request", "b", ["cart", "visitCounter"]], ["request", "a", ["requestLog"]]]],
        [{"x": "application"}, [["request", "s1", []], ["invalidate", "s1"]]],
        [{"x": "session", "y": "session"}, [["request", "s", ["x"]], ["request", "s", ["y", "x"]],
                                            ["invalidate", "s"], ["request", "s", ["y"]], ["request", "t", ["y", "y"]]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def instances(beans, events):
    count = {n: (1 if s == "singleton" else 0) for n, s in beans.items()}
    app, sessions = set(), {}
    for e in events:
        if e[0] == "invalidate":
            continue
        sb = sessions.setdefault(e[1], set()); rb = set()
        for n in e[2]:
            s = beans[n]
            if s == "singleton": continue
            if s == "prototype": count[n] += 1; continue
            store = {"application": app, "session": sb, "request": rb}[s]
            if n not in store:
                store.add(n); count[n] += 1
    return count
''',
        '''def instances(beans, events):
    count = {n: 0 for n in beans}
    seen = set()
    for e in events:
        if e[0] == "invalidate":
            seen = set(k for k in seen if k[1] != e[1]); continue
        for n in e[2]:
            s = beans[n]
            key = (n, e[1]) if s in ("session", "request") else (n, None)
            if s == "prototype" or key not in seen:
                seen.add(key); count[n] += 1
    return count
''',
    ],
    guide=dict(
        prereqs="Lesson: *Request and session scope* and *Application scope and choosing a scope*. Sets and dicts.",
        intuition="Each scope is a storage box with a different lifetime. Using a bean means: look in the box that "
                  "matches its scope; create and store it only if it is not there. The boxes differ only in when they are thrown away.",
        hints=[
            "One set for the application, one set per live session, and a fresh set at the start of every request.",
            "Invalidating a session deletes its set, so the next request with that id starts empty.",
            "Singletons are counted up front; prototypes are counted on every use and stored nowhere.",
        ],
        brute_force="Direct simulation is the solution; the state is three kinds of sets.",
        approach=r"""
**Dry run:** `cart` is session-scoped. `s1` uses it (count 1), `s2` uses it (2), `s1` uses it twice more (still
2). After `invalidate s1` the next `s1` request creates a third cart.

```java
@Component
@RequestScope                 // one instance per HTTP request
class RequestLog { }

@Component
@SessionScope                 // one per HTTP session: survives across that user's requests
class Cart implements Serializable { }

@Component
@ApplicationScope             // one per ServletContext, created lazily
class VisitCounter { }

@RestController
class CartController {        // a singleton!
    private final Cart cart;  // Spring injects a scoped PROXY that finds the right Cart for the current session
    CartController(Cart cart) { this.cart = cart; }
}
```
""",
        complexity="Time O(total uses). Space O(live sessions × session beans).",
        pitfalls="Counting a request-scoped bean once per use rather than once per request; keeping session state "
                 "after invalidation; forgetting that the singleton exists even when no request arrives.",
        follow_up="Session-scoped state breaks when a second server instance is added, unless sessions are stored centrally (Spring Session with Redis) or the app is made stateless.",
    ),
),
dict(
    id="spring-security-filter-chain",
    title="Security filter chain: who gets in?",
    difficulty="Medium",
    pattern="Spring Security",
    entry="authorize",
    description=r"""
Spring Security checks every request against an ordered list of authorization rules. The **first** rule whose
method and path pattern match decides; if none matches, access is denied.

`authorize(rules, request)`:

- `rules` — ordered list of `[method, pattern, access]`. `method` is an HTTP method or `"*"` for any.
- `request` — `{"method", "path", "user"}`; `user` is `None` for an anonymous request, otherwise
  `{"authorities": [...]}`.

**Patterns** are compared segment by segment after splitting on `/`: a literal must be equal, `*` matches exactly
one segment, `**` matches zero or more segments (and may appear anywhere). `/` alone has no segments.

**Access expressions**

| access | allowed when |
|---|---|
| `permitAll` | always |
| `denyAll` | never |
| `authenticated` | there is a user |
| `hasRole:X` | the user has authority `ROLE_X` |
| `hasAnyRole:X,Y` | the user has `ROLE_X` or `ROLE_Y` |
| `hasAuthority:a` | the user has authority `a` exactly |

**Result** `[status, rule_index]`: `200` when allowed. When refused: `401` if the request is anonymous (the
client should log in), `403` if a user is present but not allowed. `rule_index` is the index of the deciding
rule, or `-1` when no rule matched (treated like `denyAll`).

**Example:** rules `[["GET", "/api/books/**", "permitAll"], ["*", "/api/**", "authenticated"]]`; an anonymous
`POST /api/books` → `[401, 1]`.
""",
    starter='''def authorize(rules: list, request: dict) -> list:
    pass
''',
    solution='''def _segments(text):
    return [s for s in text.split("/") if s != ""]


def _matches(pattern, path):
    if not pattern:
        return not path
    if pattern[0] == "**":
        return any(_matches(pattern[1:], path[k:]) for k in range(len(path) + 1))
    if not path:
        return False
    return (pattern[0] == "*" or pattern[0] == path[0]) and _matches(pattern[1:], path[1:])


def _allowed(access, user):
    if access == "permitAll":
        return True
    if access == "denyAll" or user is None:
        return False
    if access == "authenticated":
        return True
    kind, _, value = access.partition(":")
    owned = user["authorities"]
    if kind == "hasRole":
        return "ROLE_" + value in owned
    if kind == "hasAnyRole":
        return any("ROLE_" + role in owned for role in value.split(","))
    return value in owned


def authorize(rules, request):
    path = _segments(request["path"])
    user = request["user"]
    for index, (method, pattern, access) in enumerate(rules):
        if method not in ("*", request["method"]) or not _matches(_segments(pattern), path):
            continue
        if _allowed(access, user):
            return [200, index]
        return [401 if user is None else 403, index]
    return [401 if user is None else 403, -1]
''',
    tests=[
        [[["GET", "/api/books/**", "permitAll"], ["*", "/api/**", "authenticated"]],
         {"method": "POST", "path": "/api/books", "user": None}],
        [_RULES, {"method": "GET", "path": "/", "user": _ANON}],
        [_RULES, {"method": "POST", "path": "/", "user": _ADMIN}],
        [_RULES, {"method": "GET", "path": "/actuator/health", "user": _ANON}],
        [_RULES, {"method": "GET", "path": "/actuator/env", "user": _READER}],
        [_RULES, {"method": "GET", "path": "/actuator", "user": _ADMIN}],
        [_RULES, {"method": "GET", "path": "/api/books/42/reviews", "user": _ANON}],
        [_RULES, {"method": "POST", "path": "/api/books", "user": _EDITOR}],
        [_RULES, {"method": "POST", "path": "/api/books", "user": _READER}],
        [_RULES, {"method": "DELETE", "path": "/api/books/42", "user": _EDITOR}],
        [_RULES, {"method": "DELETE", "path": "/api/books/42/reviews", "user": _ADMIN}],
        [_RULES, {"method": "GET", "path": "/api/orders", "user": _ANON}],
        [_RULES, {"method": "PUT", "path": "/api/orders/7/items/2", "user": _READER}],
        [_RULES, {"method": "GET", "path": "/api/reports/2026/export", "user": _EDITOR}],
        [_RULES, {"method": "GET", "path": "/api/reports/2026/q1/export", "user": _EDITOR}],
        [_RULES, {"method": "GET", "path": "/internal/debug", "user": _ADMIN}],
        [_RULES, {"method": "GET", "path": "/internal/debug", "user": _ANON}],
        [[["*", "/**/secret/**", "hasAuthority:ROLE_ADMIN"], ["*", "/**", "permitAll"]],
         {"method": "GET", "path": "/a/b/secret", "user": {"authorities": ["ADMIN"]}}],
        [[], {"method": "GET", "path": "/", "user": _ADMIN}],
    ],
    examples=2,
    wrong_solutions=[
        '''def _seg(t): return [s for s in t.split("/") if s != ""]
def _m(p, s):
    if not p: return not s
    if p[0] == "**": return any(_m(p[1:], s[k:]) for k in range(len(s) + 1))
    return bool(s) and (p[0] == "*" or p[0] == s[0]) and _m(p[1:], s[1:])
def _ok(a, u):
    if a == "permitAll": return True
    if a == "denyAll" or u is None: return False
    if a == "authenticated": return True
    k, _, v = a.partition(":")
    if k == "hasRole": return "ROLE_" + v in u["authorities"]
    if k == "hasAnyRole": return any("ROLE_" + r in u["authorities"] for r in v.split(","))
    return v in u["authorities"]
def authorize(rules, request):
    path, user = _seg(request["path"]), request["user"]
    last = -1
    for i, (m, p, a) in enumerate(rules):
        if m in ("*", request["method"]) and _m(_seg(p), path):
            if _ok(a, user):
                return [200, i]
            last = i
    return [401 if user is None else 403, last]
''',
        '''def _seg(t): return [s for s in t.split("/") if s != ""]
def _m(p, s):
    if not p: return not s
    if p[0] == "**": return True
    return bool(s) and (p[0] == "*" or p[0] == s[0]) and _m(p[1:], s[1:])
def _ok(a, u):
    if a == "permitAll": return True
    if a == "denyAll" or u is None: return False
    if a == "authenticated": return True
    k, _, v = a.partition(":")
    if k == "hasRole": return v in u["authorities"] or "ROLE_" + v in u["authorities"]
    if k == "hasAnyRole": return any("ROLE_" + r in u["authorities"] for r in v.split(","))
    return v in u["authorities"]
def authorize(rules, request):
    path, user = _seg(request["path"]), request["user"]
    for i, (m, p, a) in enumerate(rules):
        if m in ("*", request["method"]) and _m(_seg(p), path):
            return [200 if _ok(a, user) else 403, i]
    return [403, -1]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Spring Security basics and JWT resource servers*. The request-mapping problem for segment matching.",
        intuition="Authorization rules are a firewall list: read top to bottom, stop at the first line that "
                  "matches the request, and let that single line decide. Order therefore matters more than anything else.",
        hints=[
            "Split the work in three functions: does the pattern match, is this access expression satisfied, and the loop.",
            "`**` in the middle needs backtracking: try letting it absorb 0, 1, 2… segments.",
            "Decide 401 versus 403 by one question only: is there a user?",
        ],
        brute_force="Checking all rules and allowing if *any* allows is a different (and insecure) policy: a broad "
                    "`permitAll` at the bottom would open everything above it.",
        approach=r"""
**Dry run:** `GET /actuator/env` as a plain user. Rule 1 `/actuator/health` does not match. Rule 2
`/actuator/**` matches; `hasRole:OPS` needs `ROLE_OPS`, the user has only `ROLE_USER` → `[403, 2]`.

```java
@Configuration
@EnableWebSecurity
class SecurityConfig {
    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/actuator/**").hasRole("OPS")
                .requestMatchers(HttpMethod.GET, "/api/books/**").permitAll()
                .requestMatchers(HttpMethod.DELETE, "/api/books/*").hasRole("ADMIN")
                .anyRequest().authenticated())            // always finish with a catch-all
            .oauth2ResourceServer(oauth -> oauth.jwt(Customizer.withDefaults()))
            .build();
    }
}
```
""",
        complexity="Time O(R · S) for R rules and S segments in the common case (backtracking on `**` can add a factor). Space O(S).",
        pitfalls="Continuing past a matching rule that refuses; returning 403 to anonymous callers (they need 401 "
                 "to trigger a login); forgetting the `ROLE_` prefix that `hasRole` adds; putting a broad rule above a narrow one.",
        follow_up="Add method security (`@PreAuthorize(\"hasRole('ADMIN')\")`) as a second, independent check.",
    ),
),
dict(
    id="spring-jwt-validate",
    title="Validate the claims of a JWT",
    difficulty="Medium",
    pattern="Spring Security",
    entry="check_token",
    description=r"""
A resource server receives a JSON Web Token (JWT) on each request. After verifying the signature (not part of
this problem) it validates the **claims** and turns scopes into authorities.

`check_token(token, now, config)`:

- `token` — `{"header": {"alg": ...}, "claims": {...}}`,
- `now` — current time in seconds,
- `config` — `{"issuer", "audience", "skew", "algorithms", "required_scopes"}`; `skew` is the tolerated clock
  difference in seconds.

Run the checks in this order and stop at the first failure, returning `[401, reason]`:

1. `header.alg` must be in `config["algorithms"]` → otherwise `"unsupported algorithm"`.
2. Claim `exp` must exist → `"missing exp"`. The token is expired when `now - skew > exp` → `"expired"`.
3. If claim `nbf` exists and `now + skew < nbf` → `"not yet valid"`.
4. Claim `iss` must equal `config["issuer"]` → `"wrong issuer"`.
5. Claim `aud` may be a string or a list of strings and must contain `config["audience"]` → `"wrong audience"`
   (also when `aud` is missing).

If all pass, collect the scopes: claim `scope` is a space-separated string; claim `scp` is a list. Use `scope` if
present, otherwise `scp`, otherwise no scopes. If any scope in `config["required_scopes"]` is missing, return
`[403, "insufficient scope"]`. Otherwise return `[200, authorities]` where `authorities` is the sorted list of
scopes each prefixed with `SCOPE_`.

**Example:** a token with `exp = 2000`, `scope = "orders:read profile"`, at `now = 1500` →
`[200, ["SCOPE_orders:read", "SCOPE_profile"]]`. At `now = 2061` (skew 60) → `[401, "expired"]`.
""",
    starter='''def check_token(token: dict, now: int, config: dict) -> list:
    pass
''',
    solution='''def check_token(token, now, config):
    claims = token["claims"]
    skew = config["skew"]
    if token["header"].get("alg") not in config["algorithms"]:
        return [401, "unsupported algorithm"]
    if "exp" not in claims:
        return [401, "missing exp"]
    if now - skew > claims["exp"]:
        return [401, "expired"]
    if "nbf" in claims and now + skew < claims["nbf"]:
        return [401, "not yet valid"]
    if claims.get("iss") != config["issuer"]:
        return [401, "wrong issuer"]
    audience = claims.get("aud", [])
    if isinstance(audience, str):
        audience = [audience]
    if config["audience"] not in audience:
        return [401, "wrong audience"]
    if "scope" in claims:
        scopes = claims["scope"].split()
    else:
        scopes = list(claims.get("scp", []))
    if any(required not in scopes for required in config["required_scopes"]):
        return [403, "insufficient scope"]
    return [200, sorted("SCOPE_" + s for s in set(scopes))]
''',
    tests=[
        [_tok(), 1500, _CFG],
        [_tok(), 2061, _CFG],
        [_tok(), 2060, _CFG],
        [_tok(alg="none"), 1500, _CFG],
        [_tok(alg="HS256", exp=1), 1500, _CFG],
        [_tok(exp="DROP"), 1500, _CFG],
        [_tok(nbf=1561), 1500, _CFG],
        [_tok(nbf=1560), 1500, _CFG],
        [_tok(iss="https://evil.example"), 1500, _CFG],
        [_tok(aud=["other-api", "bookshop-api"]), 1500, _CFG],
        [_tok(aud="other-api"), 1500, _CFG],
        [_tok(aud="DROP", iss="DROP"), 1500, _CFG],
        [_tok(scope="profile"), 1500, _CFG],
        [_tok(scope="DROP", scp=["orders:write", "orders:read"]), 1500, _CFG],
        [_tok(scope="DROP"), 1500, _CFG],
        [_tok(scope="DROP"), 1500, dict(_CFG, required_scopes=[])],
        [_tok(scope="a  b a orders:read", aud="DROP"), 1500, dict(_CFG, audience="x")],
        [_tok(scope="a  b a orders:read"), 3000, dict(_CFG, skew=1000)],
    ],
    examples=2,
    wrong_solutions=[
        '''def check_token(token, now, config):
    c = token["claims"]
    if token["header"].get("alg") not in config["algorithms"]: return [401, "unsupported algorithm"]
    if "exp" not in c: return [401, "missing exp"]
    if now > c["exp"]: return [401, "expired"]
    if "nbf" in c and now < c["nbf"]: return [401, "not yet valid"]
    if c.get("iss") != config["issuer"]: return [401, "wrong issuer"]
    aud = c.get("aud", [])
    aud = [aud] if isinstance(aud, str) else aud
    if config["audience"] not in aud: return [401, "wrong audience"]
    scopes = c["scope"].split() if "scope" in c else list(c.get("scp", []))
    if any(r not in scopes for r in config["required_scopes"]): return [403, "insufficient scope"]
    return [200, sorted("SCOPE_" + s for s in set(scopes))]
''',
        '''def check_token(token, now, config):
    c = token["claims"]; skew = config["skew"]
    if token["header"].get("alg") == "none": return [401, "unsupported algorithm"]
    if "exp" not in c: return [401, "missing exp"]
    if now - skew > c["exp"]: return [401, "expired"]
    if "nbf" in c and now + skew < c["nbf"]: return [401, "not yet valid"]
    if c.get("iss") != config["issuer"]: return [401, "wrong issuer"]
    if config["audience"] not in c.get("aud", ""): return [401, "wrong audience"]
    scopes = c.get("scope", "").split(" ") + list(c.get("scp", []))
    if any(r not in scopes for r in config["required_scopes"]): return [401, "insufficient scope"]
    return [200, sorted("SCOPE_" + s for s in scopes)]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Spring Security basics and JWT resource servers* (what a JWT is, header/payload/signature).",
        intuition="A signed token only proves *who issued it*. Whether it is meant for **this** API, **now**, with "
                  "**these** permissions is decided by the claims, checked one at a time like a bouncer reading an ID card.",
        hints=[
            "Follow the numbered order exactly; each check is one `if` that returns.",
            "Normalise `aud` to a list before testing membership.",
            "401 means 'I do not accept this token'; 403 means 'the token is fine but does not grant this'.",
        ],
        brute_force="There is nothing to optimise; the common mistakes are skipped checks, not slow ones.",
        approach=r"""
**Dry run** at `now = 2060`, `exp = 2000`, skew 60: `2060 - 60 = 2000`, which is not greater than 2000 → still
accepted. One second later it is expired. The skew exists because the clocks of the token issuer and of your
server never agree exactly.

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.bookshop.example     # discovers the signing keys, validates iss
          audiences: bookshop-api
```

```java
@Bean
SecurityFilterChain api(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(a -> a
            .requestMatchers("/api/orders/**").hasAuthority("SCOPE_orders:read")
            .anyRequest().authenticated())
        .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
        .build();
}
```
""",
        complexity="Time O(number of scopes + audiences). Space the same.",
        pitfalls="Accepting `alg: none` or any algorithm you did not configure; ignoring `aud`, so a token issued "
                 "for another service works on yours; `in` on a string audience (substring match!); returning 401 for a missing scope.",
        follow_up="Opaque tokens are validated by calling the issuer's introspection endpoint instead. What are the trade-offs?",
    ),
),
dict(
    id="spring-test-slice",
    title="Test slices: which beans are loaded?",
    difficulty="Medium",
    pattern="Testing",
    entry="loaded_beans",
    description=r"""
`@SpringBootTest` starts the whole application context. *Slice* annotations start only the part needed to test
one layer, which is faster but means the other layers' beans are absent.

`loaded_beans(beans, test)`:

- `beans` — list of `{"name", "kind", "deps"}` describing the application. `kind` is one of `controller`,
  `controller-advice`, `filter`, `converter`, `json-component`, `service`, `component`, `repository`,
  `configuration`. `deps` are bean names it needs injected.
- `test` — `{"annotation", "controllers", "mocks", "imports"}`.

Which kinds each annotation scans:

| annotation | kinds included |
|---|---|
| `SpringBootTest` | everything |
| `WebMvcTest` | `controller`, `controller-advice`, `filter`, `converter`, `json-component`. If `controllers` is non-empty, only the controllers named there are included (the other kinds are unaffected) |
| `DataJpaTest` | `repository` |
| `JsonTest` | `json-component` |

Then:

- every bean named in `imports` is added (`@Import`),
- every name in `mocks` is registered as a mock (`@MockitoBean`): it replaces the real bean of that name if it
  was included, or adds a stand-in if it was not. Mocks have no dependencies.

The context **starts** only if every dependency of every real loaded bean is itself loaded or mocked.

Return `{"loaded": [...], "mocked": [...], "missing": [...], "starts": bool}` — real loaded beans, mocks and
missing dependency names, each sorted alphabetically and without duplicates.

**Example:** `@WebMvcTest` for a `bookController` that needs `bookService`: with no mocks, `missing` is
`["bookService"]` and `starts` is `False`. Adding `bookService` to `mocks` makes it start.
""",
    starter='''def loaded_beans(beans: list, test: dict) -> dict:
    pass
''',
    solution='''_SLICES = {
    "WebMvcTest": {"controller", "controller-advice", "filter", "converter", "json-component"},
    "DataJpaTest": {"repository"},
    "JsonTest": {"json-component"},
}


def loaded_beans(beans, test):
    by_name = {b["name"]: b for b in beans}
    annotation = test["annotation"]
    loaded = set()
    for bean in beans:
        if annotation == "SpringBootTest":
            loaded.add(bean["name"])
        elif bean["kind"] in _SLICES[annotation]:
            if (annotation == "WebMvcTest" and bean["kind"] == "controller" and test["controllers"]
                    and bean["name"] not in test["controllers"]):
                continue
            loaded.add(bean["name"])
    loaded.update(test["imports"])
    mocked = set(test["mocks"])
    loaded -= mocked
    missing = set()
    for name in loaded:
        for dep in by_name[name]["deps"]:
            if dep not in loaded and dep not in mocked:
                missing.add(dep)
    return {"loaded": sorted(loaded), "mocked": sorted(mocked), "missing": sorted(missing), "starts": not missing}
''',
    tests=[
        [_APP, {"annotation": "WebMvcTest", "controllers": ["bookController"], "mocks": [], "imports": []}],
        [_APP, {"annotation": "WebMvcTest", "controllers": ["bookController"], "mocks": ["bookService"], "imports": []}],
        [_APP, {"annotation": "SpringBootTest", "controllers": [], "mocks": [], "imports": []}],
        [_APP, {"annotation": "SpringBootTest", "controllers": [], "mocks": ["paymentClient"], "imports": []}],
        [_APP, {"annotation": "WebMvcTest", "controllers": [], "mocks": ["bookService"], "imports": []}],
        [_APP, {"annotation": "WebMvcTest", "controllers": [], "mocks": ["bookService", "orderService"], "imports": []}],
        [_APP, {"annotation": "DataJpaTest", "controllers": [], "mocks": [], "imports": []}],
        [_APP, {"annotation": "DataJpaTest", "controllers": [], "mocks": [], "imports": ["bookService"]}],
        [_APP, {"annotation": "DataJpaTest", "controllers": [], "mocks": [], "imports": ["bookService", "clock"]}],
        [_APP, {"annotation": "JsonTest", "controllers": [], "mocks": [], "imports": []}],
        [_APP, {"annotation": "WebMvcTest", "controllers": ["orderController"], "mocks": ["orderService", "priceFormatter"],
                "imports": []}],
        [_APP, {"annotation": "WebMvcTest", "controllers": ["bookController"], "mocks": [], "imports": ["bookService"]}],
        [[], {"annotation": "SpringBootTest", "controllers": [], "mocks": ["ghost"], "imports": []}],
        [_APP, {"annotation": "JsonTest", "controllers": ["bookController"], "mocks": [], "imports": ["orderController"]}],
    ],
    examples=2,
    wrong_solutions=[
        '''_S = {"WebMvcTest": {"controller", "controller-advice", "filter", "converter", "json-component"},
      "DataJpaTest": {"repository"}, "JsonTest": {"json-component"}}
def loaded_beans(beans, test):
    by = {b["name"]: b for b in beans}
    a = test["annotation"]
    loaded = set(b["name"] for b in beans if a == "SpringBootTest" or b["kind"] in _S[a])
    if a == "WebMvcTest" and test["controllers"]:
        loaded = set(n for n in loaded if n in test["controllers"])
    loaded.update(test["imports"])
    mocked = set(test["mocks"]); loaded -= mocked
    missing = set(d for n in loaded for d in by[n]["deps"] if d not in loaded and d not in mocked)
    return {"loaded": sorted(loaded), "mocked": sorted(mocked), "missing": sorted(missing), "starts": not missing}
''',
        '''_S = {"WebMvcTest": {"controller", "controller-advice", "filter", "converter", "json-component"},
      "DataJpaTest": {"repository"}, "JsonTest": {"json-component"}}
def loaded_beans(beans, test):
    by = {b["name"]: b for b in beans}
    a = test["annotation"]
    loaded = set()
    for b in beans:
        if a == "SpringBootTest" or b["kind"] in _S[a]:
            if a == "WebMvcTest" and b["kind"] == "controller" and test["controllers"] and b["name"] not in test["controllers"]:
                continue
            loaded.add(b["name"])
    loaded.update(test["imports"])
    mocked = set(test["mocks"])
    todo = list(loaded)
    while todo:
        n = todo.pop()
        for d in by[n]["deps"]:
            if d not in loaded and d not in mocked:
                loaded.add(d); todo.append(d)
    loaded -= mocked
    return {"loaded": sorted(loaded), "mocked": sorted(mocked), "missing": [], "starts": True}
''',
    ],
    guide=dict(
        prereqs="Lesson: *Integration tests with @SpringBootTest and test slices*. Python sets.",
        intuition="A slice is a filter on bean kinds. Whatever the filter removes but a remaining bean still needs "
                  "must be put back by you, either as a mock or with an explicit import. Spring never pulls dependencies in automatically.",
        hints=[
            "Compute the included set from the annotation first, then apply `imports`, then `mocks`.",
            "The `controllers` attribute narrows only beans of kind `controller`.",
            "A mocked name leaves the 'real' set, and its own dependencies stop mattering.",
        ],
        brute_force="Set operations are the whole solution. The tempting error is to follow dependencies transitively, "
                    "which is exactly what a slice does *not* do.",
        approach=r"""
**Dry run** `@WebMvcTest(BookController.class)`: included are `bookController`, `apiErrors`, `requestIdFilter`,
`priceFormatter`, `moneySerializer`. `bookController` needs `bookService`, a `service` → missing. The context
fails with `NoSuchBeanDefinitionException` until the test declares the mock.

```java
@WebMvcTest(BookController.class)
class BookControllerTest {

    @Autowired MockMvc mvc;

    @MockitoBean BookService bookService;        // Spring Boot 3.4+; @MockBean in earlier versions

    @Test
    void returns404ForUnknownBook() throws Exception {
        given(bookService.find(99L)).willThrow(new BookNotFoundException(99L));

        mvc.perform(get("/api/books/99"))
           .andExpect(status().isNotFound());
    }
}
```
""",
        complexity="Time O(beans + dependencies). Space O(beans).",
        pitfalls="Letting the `controllers` filter remove advice and filters; adding dependencies automatically; "
                 "checking the dependencies of mocked beans; reporting duplicates in `missing`.",
        follow_up="Each distinct combination of mocks creates a new cached context. Why can many different `@MockitoBean` sets slow a test suite down?",
    ),
),
dict(
    id="spring-health-aggregate",
    title="Aggregate Actuator health",
    difficulty="Easy",
    pattern="Production",
    entry="aggregate",
    description=r"""
Spring Boot Actuator's `/actuator/health` endpoint combines the status of many **health indicators** (database,
disk space, message broker…) into one overall status and an HTTP status code for load balancers.

`aggregate(components, order)`:

- `components` — dict `name -> status` where a status is a string such as `"UP"`, **or** a nested dict of the
  same shape (a composite contributor, e.g. one entry per database).
- `order` — list of statuses from **most severe to least severe**, e.g.
  `["DOWN", "OUT_OF_SERVICE", "UP", "UNKNOWN"]`.

Aggregation rule: the overall status of a group is the most severe status found among its members, i.e. the one
appearing earliest in `order`. Statuses that do not appear in `order` are ignored. A group with no usable member
statuses is `"UNKNOWN"`. A nested dict is first aggregated by the same rule and then counts as one member.

HTTP mapping: `DOWN` and `OUT_OF_SERVICE` → `503`; anything else → `200`.

Return `{"status": overall, "http": code, "components": {...}}` where `components` maps each **top-level** name
to its (aggregated) status string.

**Example:** `aggregate({"db": "UP", "diskSpace": "UP", "mail": "DOWN"}, order)` →
`{"status": "DOWN", "http": 503, "components": {"db": "UP", "diskSpace": "UP", "mail": "DOWN"}}`.
""",
    starter='''def aggregate(components: dict, order: list) -> dict:
    pass
''',
    solution='''def _status(node, order):
    if isinstance(node, str):
        return node
    known = [s for s in (_status(child, order) for child in node.values()) if s in order]
    return min(known, key=order.index) if known else "UNKNOWN"


def aggregate(components, order):
    flat = {name: _status(node, order) for name, node in components.items()}
    overall = _status(flat, order)
    return {"status": overall, "http": 503 if overall in ("DOWN", "OUT_OF_SERVICE") else 200, "components": flat}
''',
    tests=[
        [{"db": "UP", "diskSpace": "UP", "mail": "DOWN"}, _ORDER],
        [{"db": "UP", "diskSpace": "UP"}, _ORDER],
        [{}, _ORDER],
        [{"db": {"primary": "UP", "replica": "DOWN"}, "ping": "UP"}, _ORDER],
        [{"db": {"primary": "UP", "replica": "UP"}, "broker": "OUT_OF_SERVICE", "cache": "UNKNOWN"}, _ORDER],
        [{"cache": "UNKNOWN", "ping": "UP"}, _ORDER],
        [{"cache": "UNKNOWN"}, _ORDER],
        [{"payments": "DEGRADED", "ping": "UP"}, _ORDER],
        [{"payments": "DEGRADED"}, _ORDER],
        [{"payments": "DEGRADED", "ping": "UP", "db": "DOWN"}, ["DEGRADED", "DOWN", "UP"]],
        [{"a": {"b": {"c": "OUT_OF_SERVICE", "d": "UP"}, "e": "UP"}, "f": {}}, _ORDER],
        [{"db": "DOWN", "broker": "OUT_OF_SERVICE"}, ["OUT_OF_SERVICE", "DOWN", "UP", "UNKNOWN"]],
        [{"x": {"y": "WEIRD"}, "z": "UP"}, _ORDER],
    ],
    examples=2,
    wrong_solutions=[
        '''def aggregate(components, order):
    def st(node):
        if isinstance(node, str): return node
        vals = [st(c) for c in node.values()]
        return "UP" if all(v == "UP" for v in vals) else "DOWN"
    flat = {n: st(c) for n, c in components.items()}
    overall = st(flat)
    return {"status": overall, "http": 503 if overall in ("DOWN", "OUT_OF_SERVICE") else 200, "components": flat}
''',
        '''def aggregate(components, order):
    def st(node):
        if isinstance(node, str): return node
        known = [s for s in (st(c) for c in node.values()) if s in order]
        return max(known, key=order.index) if known else "UNKNOWN"
    flat = {n: st(c) for n, c in components.items()}
    overall = st(flat)
    return {"status": overall, "http": 503 if overall in ("DOWN", "OUT_OF_SERVICE") else 200, "components": flat}
''',
        '''def aggregate(components, order):
    def st(node):
        if isinstance(node, str): return node
        vals = [st(c) for c in node.values()]
        return min(vals, key=lambda s: order.index(s) if s in order else -1) if vals else "UNKNOWN"
    flat = {n: st(c) for n, c in components.items()}
    overall = st(flat)
    return {"status": overall, "http": 503 if overall != "UP" else 200, "components": flat}
''',
    ],
    guide=dict(
        prereqs="Recursion over nested dicts. Lesson: *Actuator, Docker images and virtual threads*.",
        intuition="Health is as bad as its worst part. 'Worst' is defined by a configurable ranking, so the "
                  "aggregation is a minimum over positions in that ranking.",
        hints=[
            "Write `status(node)` that returns the string itself for a leaf and recurses for a dict.",
            "Filter out statuses that are not in `order` before taking the minimum by `order.index`.",
            "The overall status is the same function applied to the flattened top level.",
        ],
        brute_force="Hard-coding 'if anything is DOWN then DOWN else UP' ignores `OUT_OF_SERVICE`, `UNKNOWN`, "
                    "custom statuses and custom orders.",
        approach=r"""
**Dry run:** `{"db": {"primary": "UP", "replica": "DOWN"}, "ping": "UP"}`. `db` aggregates to `DOWN`
(index 0 beats index 2). Top level: `DOWN`, `UP` → `DOWN`, HTTP 503.

```java
@Component
class PaymentGatewayHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        return gateway.ping() ? Health.up().withDetail("latencyMs", 42).build()
                              : Health.down().withDetail("reason", "timeout").build();
    }
}
```

```properties
management.endpoints.web.exposure.include=health,info,metrics
management.endpoint.health.show-details=when-authorized
management.endpoint.health.status.order=DOWN,OUT_OF_SERVICE,UP,UNKNOWN
```
""",
        complexity="Time O(number of nodes × length of the order list). Space O(depth) for recursion.",
        pitfalls="Using `max` instead of `min` over the order; crashing on a status missing from the order; "
                 "returning 503 for `UNKNOWN`; treating an empty group as `UP`.",
        follow_up="Kubernetes distinguishes *liveness* from *readiness*. Boot exposes them as health groups: which indicators belong in which?",
    ),
),
]
