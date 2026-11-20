_SRC = {
    "defaults": {"server.port": "8080", "shop.currency": "EUR", "shop.page-size": "20"},
    "application": {"server.port": "8081", "shop.title": "Bookshop", "shop.page-size": "25", "shop.db.url": "jdbc:h2:mem:shop"},
    "profiles": {
        "dev": {"shop.title": "Bookshop DEV", "shop.db.url": "jdbc:h2:mem:dev"},
        "prod": {"shop.db.url": "jdbc:postgresql://db/shop", "shop.page-size": "50"},
        "eu": {"shop.title": "Bookshop EU"},
    },
    "env": {"SHOP_DB_URL": "jdbc:postgresql://env/shop", "SHOP_PAGESIZE": "100", "PATH": "/usr/bin"},
    "args": {"server.port": "9000"},
}
_EMPTY = {"defaults": {}, "application": {}, "profiles": {}, "env": {}, "args": {}}

_PROPS = {
    "shop.name": "Bookshop",
    "shop.env": "dev",
    "shop.greeting": "Welcome to ${shop.name}",
    "db.dev.url": "jdbc:h2:mem:dev",
    "db.url": "${db.${shop.env}.url}",
    "loop.a": "${loop.b}",
    "loop.b": "x${loop.a}",
    "self": "${self}",
    "empty": "",
}

_ASP = [
    {"name": "logging", "order": 1, "advices": ["around", "before", "after"], "catches": False},
    {"name": "security", "order": 0, "advices": ["before"], "catches": False},
    {"name": "tx", "order": 5, "advices": ["around", "afterReturning", "afterThrowing", "after"], "catches": False},
]

_METHODS = [
    {"ret": "Book", "cls": "com.bookshop.service.BookService", "name": "findBook", "params": ["long"]},
    {"ret": "void", "cls": "com.bookshop.service.BookService", "name": "saveBook", "params": ["Book"]},
    {"ret": "List", "cls": "com.bookshop.service.order.OrderService", "name": "findOrders", "params": ["String", "int"]},
    {"ret": "void", "cls": "com.bookshop.web.BookController", "name": "saveBook", "params": []},
    {"ret": "String", "cls": "com.bookshop.Clock", "name": "now", "params": []},
    {"ret": "void", "cls": "org.other.service.BookService", "name": "saveBook", "params": ["Book", "boolean"]},
]

_SVC = {
    "placeOrder": {"transactional": False, "calls": [["this", "reserveStock"], ["this", "charge"]]},
    "reserveStock": {"transactional": True, "calls": []},
    "charge": {"transactional": True, "calls": [["proxy", "audit"]]},
    "audit": {"transactional": True, "calls": [["this", "format"]]},
    "format": {"transactional": False, "calls": []},
    "importAll": {"transactional": True, "calls": [["this", "audit"], ["proxy", "placeOrder"], ["proxy", "format"]]},
}

PROBLEMS = [
dict(
    id="spring-property-precedence",
    title="Which property source wins?",
    difficulty="Easy",
    pattern="Configuration",
    entry="resolve_property",
    description=r"""
Spring Boot reads configuration from several places and lets later, more specific places override earlier ones.
For this problem there are five sources, from **lowest to highest** priority:

1. `defaults` — defaults set in code,
2. `application` — `application.properties`,
3. `profiles` — `application-<profile>.properties` for each **active** profile; when several active profiles
   define the key, the profile listed **last** in `active_profiles` wins,
4. `env` — operating-system environment variables,
5. `args` — command-line arguments such as `--server.port=9000`.

Environment variables cannot contain dots or dashes, so Boot uses *relaxed binding*: to find the variable for a
key, replace every `.` with `_`, delete every `-`, and upper-case the result (`shop.page-size` → `SHOP_PAGESIZE`).

`resolve_property(key, sources, active_profiles)` receives `sources` as a dict with exactly those five entries
(`profiles` maps a profile name to its dict). Return `[value, label]` for the winning source, where the label is
`"args"`, `"env"`, `"profile:<name>"`, `"application"` or `"defaults"`. Return `None` if no source has the key.
A profile that is not active is ignored.

**Example:** `server.port` is `8080` in defaults, `8081` in application and `9000` in args → `["9000", "args"]`.
""",
    starter='''def resolve_property(key: str, sources: dict, active_profiles: list):
    pass
''',
    solution='''def resolve_property(key, sources, active_profiles):
    if key in sources["args"]:
        return [sources["args"][key], "args"]
    env_name = key.replace(".", "_").replace("-", "").upper()
    if env_name in sources["env"]:
        return [sources["env"][env_name], "env"]
    for profile in reversed(active_profiles):
        values = sources["profiles"].get(profile, {})
        if key in values:
            return [values[key], "profile:" + profile]
    for label in ("application", "defaults"):
        if key in sources[label]:
            return [sources[label][key], label]
    return None
''',
    tests=[
        ["server.port", _SRC, []],
        ["shop.title", _SRC, ["dev"]],
        ["shop.title", _SRC, []],
        ["shop.currency", _SRC, ["dev", "prod"]],
        ["shop.db.url", _SRC, ["prod"]],
        ["shop.page-size", _SRC, ["prod"]],
        ["shop.title", _SRC, ["dev", "eu"]],
        ["shop.title", _SRC, ["eu", "dev"]],
        ["shop.missing", _SRC, ["dev", "prod", "eu"]],
        ["path", _SRC, []],
        ["shop.title", _SRC, ["staging"]],
        ["shop.db.url", dict(_SRC, env={}), ["dev", "prod"]],
        ["anything", _EMPTY, ["dev"]],
        ["shop.page-size", dict(_SRC, env={"SHOP_PAGE_SIZE": "7"}), ["prod", "dev"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolve_property(key, sources, active_profiles):
    if key in sources["args"]:
        return [sources["args"][key], "args"]
    if key in sources["env"]:
        return [sources["env"][key], "env"]
    for profile in reversed(active_profiles):
        values = sources["profiles"].get(profile, {})
        if key in values:
            return [values[key], "profile:" + profile]
    for label in ("application", "defaults"):
        if key in sources[label]:
            return [sources[label][key], label]
    return None
''',
        '''def resolve_property(key, sources, active_profiles):
    if key in sources["args"]:
        return [sources["args"][key], "args"]
    env_name = key.replace(".", "_").replace("-", "").upper()
    if env_name in sources["env"]:
        return [sources["env"][env_name], "env"]
    for profile in active_profiles:
        values = sources["profiles"].get(profile, {})
        if key in values:
            return [values[key], "profile:" + profile]
    for label in ("application", "defaults"):
        if key in sources[label]:
            return [sources[label][key], label]
    return None
''',
        '''def resolve_property(key, sources, active_profiles):
    env_name = key.replace(".", "_").replace("-", "").upper()
    for label in ("defaults", "application"):
        if key in sources[label]:
            return [sources[label][key], label]
    for profile in reversed(active_profiles):
        if key in sources["profiles"].get(profile, {}):
            return [sources["profiles"][profile][key], "profile:" + profile]
    if env_name in sources["env"]:
        return [sources["env"][env_name], "env"]
    if key in sources["args"]:
        return [sources["args"][key], "args"]
    return None
''',
    ],
    guide=dict(
        prereqs="Lesson: *Configuration properties, profiles and logging*. Python dict lookups.",
        intuition="The closer a setting is to the moment of launch, the more it should count: a file packed into "
                  "the jar loses to the environment of the machine, which loses to what the operator typed on the command line.",
        hints=[
            "Check the sources from highest priority to lowest and return at the first hit.",
            "Convert the key to its environment-variable spelling before looking in `env`.",
            "Walk `active_profiles` backwards so the last active profile is consulted first.",
        ],
        brute_force="Merge all dicts from lowest to highest into one and look the key up. It works but loses the "
                    "label unless you store it too, and it does needless work for one key.",
        approach=r"""
Probe in order `args → env → profiles (reversed) → application → defaults`.

**Dry run** for `shop.page-size` with `prod` active: not in args; env name is `SHOP_PAGESIZE`, present with
`100` → `["100", "env"]`. The `prod` profile's `50` and the file's `25` never get a look.

```properties
# src/main/resources/application.properties
shop.page-size=25
```

```bash
SHOP_PAGESIZE=100 java -jar bookshop.jar --server.port=9000 --spring.profiles.active=prod
```

```java
@ConfigurationProperties(prefix = "shop")
public record ShopProperties(int pageSize, String title) { }   // pageSize == 100
```
""",
        complexity="Time O(P) for P active profiles (every lookup is a hash probe). Space O(1).",
        pitfalls="Looking up the dotted key in the environment; letting the *first* active profile win; "
                 "treating inactive profile files as if they were loaded.",
        follow_up="The real list has around fifteen levels (config outside the jar beats config inside it, `SPRING_APPLICATION_JSON`, test properties…). Extend the table.",
    ),
),
dict(
    id="spring-placeholder-expand",
    title="Expand ${placeholders} with defaults",
    difficulty="Medium",
    pattern="Configuration",
    entry="expand",
    description=r"""
Property values and `@Value` strings may contain placeholders. Implement the expansion.

`expand(text, props)` returns `text` with every placeholder replaced:

- `${key}` → the value of `key` in `props`. That value is expanded too (values may contain placeholders).
- `${key:default}` → the value of `key` if present, otherwise `default`. The default is everything after the
  **first** colon that is not inside a nested placeholder, may be empty, and is itself expanded.
- Placeholders nest: `${a:${b:none}}` and `${db.${env}.url}` are legal. Expand the key part first, then look it up.
- If a key is missing and there is no default, return the string
  `"ERROR: Could not resolve placeholder '<key>'"` (the whole result is that message).
- If expanding a key requires that same key again, return `"ERROR: Circular placeholder reference '<key>'"`,
  naming the key that was met for the second time.
- A `${` with no matching `}` is ordinary text. So is a lone `$` or `}`.

**Example:** `props = {"shop.name": "Bookshop"}`: `expand("Hi ${shop.name}!", props)` → `"Hi Bookshop!"`;
`expand("${port:8080}", props)` → `"8080"`.
""",
    starter='''def expand(text: str, props: dict) -> str:
    pass
''',
    solution='''def expand(text, props):
    try:
        return _expand(text, props, [])
    except ValueError as problem:
        return "ERROR: " + str(problem)


def _expand(text, props, visiting):
    out, i = [], 0
    while i < len(text):
        if not text.startswith("${", i):
            out.append(text[i])
            i += 1
            continue
        depth, j = 1, i + 2
        while j < len(text) and depth:
            if text.startswith("${", j):
                depth += 1
                j += 2
                continue
            if text[j] == "}":
                depth -= 1
            j += 1
        if depth:
            out.append(text[i:])
            break
        inner = text[i + 2:j - 1]
        key, default = inner, None
        level, k = 0, 0
        while k < len(inner):
            if inner.startswith("${", k):
                level += 1
                k += 2
                continue
            if inner[k] == "}":
                level -= 1
            elif inner[k] == ":" and level == 0:
                key, default = inner[:k], inner[k + 1:]
                break
            k += 1
        key = _expand(key, props, visiting)
        if key in visiting:
            raise ValueError("Circular placeholder reference '%s'" % key)
        if key in props:
            out.append(_expand(props[key], props, visiting + [key]))
        elif default is not None:
            out.append(_expand(default, props, visiting))
        else:
            raise ValueError("Could not resolve placeholder '%s'" % key)
        i = j
    return "".join(out)
''',
    tests=[
        ["Hi ${shop.name}!", _PROPS],
        ["${port:8080}", _PROPS],
        ["no placeholders here", _PROPS],
        ["", _PROPS],
        ["${shop.greeting} (${shop.env})", _PROPS],
        ["${missing}", _PROPS],
        ["${a:${b:none}}", _PROPS],
        ["${db.url}", _PROPS],
        ["${loop.a}", _PROPS],
        ["${self}", _PROPS],
        ["${url:http://localhost:8080/api}", _PROPS],
        ["${empty}|${nothing:}|${shop.name:}", _PROPS],
        ["cost: $5 and } and ${unclosed", _PROPS],
        ["${missing:${also.missing}}", _PROPS],
        ["${shop.name:${also.missing}}-${x:${shop.greeting}}", _PROPS],
    ],
    examples=2,
    wrong_solutions=[
        '''import re
def expand(text, props):
    def sub(m):
        key, _, default = m.group(1).partition(":")
        if key in props:
            return props[key]
        if ":" in m.group(1):
            return default
        raise ValueError(key)
    try:
        return re.sub(r"\\$\\{([^}]*)\\}", sub, text)
    except ValueError as e:
        return "ERROR: Could not resolve placeholder '%s'" % e
''',
        '''import re
def expand(text, props):
    for _ in range(50):
        m = re.search(r"\\$\\{([^${}]*)\\}", text)
        if not m:
            return text
        key, sep, default = m.group(1).partition(":")
        if key in props:
            value = props[key]
        elif sep:
            value = default
        else:
            return "ERROR: Could not resolve placeholder '%s'" % key
        text = text[:m.start()] + value + text[m.end():]
    return "ERROR: Circular placeholder reference"
''',
    ],
    guide=dict(
        prereqs="String scanning with indexes, recursion. Lesson: *Configuration properties, profiles and logging*.",
        intuition="A placeholder is a small expression with brackets that can nest, so a regular expression is not "
                  "enough: you have to count opening `${` and closing `}` to find where each one ends, then recurse into the pieces.",
        hints=[
            "Scan left to right. On `${`, walk forward counting depth until it returns to zero; that is the matching brace.",
            "Inside the braces, the key/default split is the first `:` seen while the nested depth is zero.",
            "Carry a list of keys currently being expanded. Meeting one of them again is a cycle.",
        ],
        brute_force="Repeatedly replace the innermost `${...}` (one with no `$`, `{`, `}` inside) until none remain. "
                    "It handles nesting but evaluates defaults that should never be touched and cannot name the key in a cycle.",
        approach=r"""
Recursive descent:

1. Copy ordinary characters.
2. At `${`, find the matching `}` by depth counting. No match → the rest is literal.
3. Split the inside into `key` and optional `default` at the first top-level colon.
4. Expand the key text itself (this is what makes `${db.${env}.url}` work).
5. Key known → expand its value with the key added to the *visiting* list. Key unknown → expand the default, or fail.

**Dry run** `${a:${b:none}}` with neither key defined: inner is `a:${b:none}`; key `a`, default `${b:none}`.
`a` is missing → expand the default → key `b`, default `none` → `none`.

Note that the default is only expanded when needed, so `${shop.name:${also.missing}}` succeeds.

```java
@Component
class ShopBanner {
    ShopBanner(@Value("${shop.greeting:Welcome}") String greeting,
               @Value("${shop.page-size:20}") int pageSize) { }   // text is converted to int after expansion
}
```
""",
        complexity="Time O(L) per level of expansion, so O(total expanded length × nesting depth). Space O(depth) for the recursion.",
        pitfalls="Splitting on the *last* colon breaks `${url:http://host:8080}`. Using `[^}]*` in a regex breaks "
                 "nesting. Eagerly expanding defaults reports errors for values that are never used.",
        follow_up="Spring also has `#{...}` (Spring Expression Language), which is evaluated *after* placeholders. Add arithmetic.",
    ),
),
dict(
    id="spring-advice-order",
    title="AOP advice ordering: build the call log",
    difficulty="Medium",
    pattern="AOP",
    entry="call_log",
    description=r"""
Several aspects can intercept the same method. Each aspect may have up to five kinds of advice. Produce the log of
what runs, in order.

`call_log(aspects, outcome)`:

- `aspects` — list of `{"name", "order", "advices", "catches"}`. `advices` is a subset of `"around"`, `"before"`,
  `"afterReturning"`, `"afterThrowing"`, `"after"`. `catches` only matters when the aspect has `around`: it means
  the around advice wraps `proceed()` in try/catch and returns a fallback value.
- `outcome` — `"return"` or `"throw"`: what the target method does.

Rules:

1. Aspects are nested by `order`: the **lowest** number is the outermost. Ties are broken by name (alphabetical).
2. On the way **in**, each aspect from outermost to innermost logs `"<name>:around-before"` (if it has `around`)
   and then `"<name>:before"` (if it has `before`).
3. Then the target logs `"target:return"` or `"target:throw"`.
4. On the way **out**, each aspect from innermost to outermost sees the current outcome:
   - outcome is a normal return: `"<name>:afterReturning"`, `"<name>:after"`, `"<name>:around-after"`
     (each only if that advice exists);
   - outcome is an exception: `"<name>:afterThrowing"`, `"<name>:after"`, then, if the aspect has `around` **and**
     `catches`, `"<name>:around-recovered"` and the outcome becomes a normal return for all aspects further out.
     An around advice that does not catch logs nothing on the way out of an exception.

Return the list of log lines.

**Example:** one aspect `log` with `["around", "before", "after"]`, outcome `"return"` →
`["log:around-before", "log:before", "target:return", "log:after", "log:around-after"]`.
""",
    starter='''def call_log(aspects: list, outcome: str) -> list:
    pass
''',
    solution='''def call_log(aspects, outcome):
    chain = sorted(aspects, key=lambda a: (a["order"], a["name"]))
    log = []
    for aspect in chain:
        if "around" in aspect["advices"]:
            log.append(aspect["name"] + ":around-before")
        if "before" in aspect["advices"]:
            log.append(aspect["name"] + ":before")
    log.append("target:" + outcome)
    failed = outcome == "throw"
    for aspect in reversed(chain):
        name, advices = aspect["name"], aspect["advices"]
        if failed:
            if "afterThrowing" in advices:
                log.append(name + ":afterThrowing")
            if "after" in advices:
                log.append(name + ":after")
            if "around" in advices and aspect["catches"]:
                log.append(name + ":around-recovered")
                failed = False
        else:
            if "afterReturning" in advices:
                log.append(name + ":afterReturning")
            if "after" in advices:
                log.append(name + ":after")
            if "around" in advices:
                log.append(name + ":around-after")
    return log
''',
    tests=[
        [[{"name": "log", "order": 1, "advices": ["around", "before", "after"], "catches": False}], "return"],
        [[{"name": "log", "order": 1, "advices": ["around", "before", "after"], "catches": False}], "throw"],
        [[], "return"],
        [[], "throw"],
        [_ASP, "return"],
        [_ASP, "throw"],
        [[dict(_ASP[0], catches=True), _ASP[1], _ASP[2]], "throw"],
        [[_ASP[0], _ASP[1], dict(_ASP[2], catches=True)], "throw"],
        [[{"name": "b", "order": 3, "advices": ["before"], "catches": False},
          {"name": "a", "order": 3, "advices": ["before", "afterReturning"], "catches": False},
          {"name": "c", "order": -1, "advices": ["after"], "catches": False}], "return"],
        [[{"name": "x", "order": 2, "advices": ["after", "afterThrowing", "afterReturning", "before", "around"], "catches": True}], "throw"],
        [[{"name": "x", "order": 2, "advices": ["after", "afterThrowing", "afterReturning", "before", "around"], "catches": True}], "return"],
        [[{"name": "outer", "order": 1, "advices": ["afterThrowing", "afterReturning"], "catches": True},
          {"name": "inner", "order": 2, "advices": ["afterThrowing"], "catches": False}], "throw"],
        [[{"name": "retry", "order": 10, "advices": ["around"], "catches": True},
          {"name": "metrics", "order": 20, "advices": ["around", "after"], "catches": True},
          {"name": "audit", "order": 0, "advices": ["afterReturning", "afterThrowing", "around"], "catches": False}], "throw"],
    ],
    examples=2,
    wrong_solutions=[
        '''def call_log(aspects, outcome):
    chain = sorted(aspects, key=lambda a: (a["order"], a["name"]))
    log = []
    for a in chain:
        if "around" in a["advices"]: log.append(a["name"] + ":around-before")
        if "before" in a["advices"]: log.append(a["name"] + ":before")
    log.append("target:" + outcome)
    failed = outcome == "throw"
    for a in chain:
        n, adv = a["name"], a["advices"]
        if failed:
            if "afterThrowing" in adv: log.append(n + ":afterThrowing")
            if "after" in adv: log.append(n + ":after")
            if "around" in adv and a["catches"]:
                log.append(n + ":around-recovered"); failed = False
        else:
            if "afterReturning" in adv: log.append(n + ":afterReturning")
            if "after" in adv: log.append(n + ":after")
            if "around" in adv: log.append(n + ":around-after")
    return log
''',
        '''def call_log(aspects, outcome):
    chain = sorted(aspects, key=lambda a: (a["order"], a["name"]))
    log = []
    for a in chain:
        if "around" in a["advices"]: log.append(a["name"] + ":around-before")
        if "before" in a["advices"]: log.append(a["name"] + ":before")
    log.append("target:" + outcome)
    failed = outcome == "throw"
    for a in reversed(chain):
        n, adv = a["name"], a["advices"]
        if "after" in adv: log.append(n + ":after")
        if failed:
            if "afterThrowing" in adv: log.append(n + ":afterThrowing")
        else:
            if "afterReturning" in adv: log.append(n + ":afterReturning")
            if "around" in adv: log.append(n + ":around-after")
    return log
''',
        '''def call_log(aspects, outcome):
    chain = sorted(aspects, key=lambda a: (-a["order"], a["name"]))
    log = []
    for a in chain:
        if "around" in a["advices"]: log.append(a["name"] + ":around-before")
        if "before" in a["advices"]: log.append(a["name"] + ":before")
    log.append("target:" + outcome)
    failed = outcome == "throw"
    for a in reversed(chain):
        n, adv = a["name"], a["advices"]
        if failed:
            if "afterThrowing" in adv: log.append(n + ":afterThrowing")
            if "after" in adv: log.append(n + ":after")
            if "around" in adv and a["catches"]:
                log.append(n + ":around-recovered"); failed = False
        else:
            if "afterReturning" in adv: log.append(n + ":afterReturning")
            if "after" in adv: log.append(n + ":after")
            if "around" in adv: log.append(n + ":around-after")
    return log
''',
    ],
    guide=dict(
        prereqs="Lesson: *Advice types, pointcut expressions and aspect order*. Sorting with a key function.",
        intuition="Picture Russian dolls. The lowest order number is the biggest doll. A call travels inwards "
                  "through every doll to the target and the result (or exception) travels back out through the same dolls in reverse.",
        hints=[
            "Sort once by `(order, name)`; iterate forwards for the way in and backwards for the way out.",
            "Keep a boolean 'an exception is travelling'. It starts from `outcome` and can only be switched off by a catching around advice.",
            "Within one aspect on the way out: the returning/throwing advice first, then `after`, then the around tail.",
        ],
        brute_force="You could build real nested Python closures, one per advice, and call them. It is a faithful "
                    "model but much more code than two loops.",
        approach=r"""
**Dry run** with `security(0: before)`, `logging(1: around, before, after)`, `tx(5: around, afterReturning,
afterThrowing, after)` and a throwing target:

in: `security:before`, `logging:around-before`, `logging:before`, `tx:around-before` → `target:throw` →
out: `tx:afterThrowing`, `tx:after` (tx's around does not catch) → `logging:after` → security has nothing.

```java
@Aspect
@Component
@Order(1)                                   // lower number = further out
class LoggingAspect {
    @Around("execution(* com.bookshop.service..*(..))")
    Object time(ProceedingJoinPoint pjp) throws Throwable {
        log.info("around-before");
        Object result = pjp.proceed();      // an exception skips the next line
        log.info("around-after");
        return result;
    }
    @Before("execution(* com.bookshop.service..*(..))") void before() { }
    @After("execution(* com.bookshop.service..*(..))")  void after()  { }   // like finally
}
```
""",
        complexity="Time O(n log n) for the sort plus O(n) for the two passes. Space O(n).",
        pitfalls="Unwinding in the same direction as entering; running `after` before `afterReturning` (the order "
                 "inside one aspect changed in Spring Framework 5.2.7 and is now as in this problem); forgetting that a "
                 "caught exception looks like a normal return to outer aspects.",
        follow_up="A retry aspect calls `proceed()` more than once. How would the log look for 'fails twice, then succeeds'?",
    ),
),
dict(
    id="spring-pointcut-match",
    title="Match execution() pointcut expressions",
    difficulty="Hard",
    pattern="AOP",
    entry="matches",
    description=r"""
A pointcut expression selects the methods an aspect intercepts. Implement a matcher for this subset:

```
execution(<return> <type>.<method>(<params>))
```

- `<return>` — `*` (any) or a return type name. A `*` inside a name matches any run of letters/digits.
- `<type>` — a fully qualified class pattern, dot-separated. Inside a segment `*` matches any run of
  letters, digits and `_` (possibly empty). The token `..` between segments matches the dot plus **zero or more
  whole package segments**: `com.bookshop..*` is any class in `com.bookshop` or any sub-package.
- `<method>` — the method name, `*` allowed as in a segment. The method name is the part after the last dot
  before `(`.
- `<params>` — comma-separated list. `..` matches zero or more parameters of any type, `*` matches exactly one
  parameter of any type, anything else must equal the parameter type. An empty list `()` matches only methods
  without parameters.

`matches(expression, methods)` receives the expression and a list of method descriptions
`{"ret", "cls", "name", "params"}` (`cls` is fully qualified). Return a list of booleans, one per method.

**Example:** `execution(* com.bookshop.service.*.*(..))` matches every method of every class directly in
`com.bookshop.service`, but not `com.bookshop.service.order.OrderService.findOrders`.
""",
    starter='''def matches(expression: str, methods: list) -> list:
    pass
''',
    solution='''import re


def _glob(pattern):
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("..", i):
            out += r"\\.(?:\\w+\\.)*"
            i += 2
        elif pattern[i] == "*":
            out += r"\\w*"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(out + r"\\Z")


def _params_ok(patterns, actual):
    if not patterns:
        return not actual
    head = patterns[0]
    if head == "..":
        return any(_params_ok(patterns[1:], actual[k:]) for k in range(len(actual) + 1))
    if not actual:
        return False
    return (head == "*" or head == actual[0]) and _params_ok(patterns[1:], actual[1:])


def matches(expression, methods):
    m = re.match(r"\\s*execution\\(\\s*(\\S+)\\s+([^\\s(]+)\\((.*)\\)\\s*\\)\\s*\\Z", expression)
    ret, target, params = m.group(1), m.group(2), m.group(3)
    type_pattern, _, name_pattern = target.rpartition(".")
    ret_re, type_re, name_re = _glob(ret), _glob(type_pattern), _glob(name_pattern)
    wanted = [p.strip() for p in params.split(",")] if params.strip() else []
    return [
        bool(ret_re.match(md["ret"]) and type_re.match(md["cls"]) and name_re.match(md["name"])
             and _params_ok(wanted, md["params"]))
        for md in methods
    ]
''',
    tests=[
        ["execution(* com.bookshop.service.*.*(..))", _METHODS],
        ["execution(* com.bookshop..*.*(..))", _METHODS],
        ["execution(void com.bookshop..*.save*(..))", _METHODS],
        ["execution(* com.bookshop.service.BookService.findBook(long))", _METHODS],
        ["execution(* *..BookService.*(..))", _METHODS],
        ["execution(* com.bookshop..*.*())", _METHODS],
        ["execution(* com.bookshop..*.*(*))", _METHODS],
        ["execution(* *..*.*(String, ..))", _METHODS],
        ["execution(* *..*.*(.., boolean))", _METHODS],
        ["execution(* com.bookshop..*Service.find*(..))", _METHODS],
        ["execution(* com.bookshop.*.*(..))", _METHODS],
        ["execution(Str* *..*.*(..))", _METHODS],
        ["execution(* com.bookshop.service..*.*(*, *))", _METHODS],
        ["execution(* com.bookshop..service.*.*(..))", []],
        ["execution(* org..service..*.*(Book, ..))", _METHODS],
    ],
    examples=2,
    wrong_solutions=[
        '''import re
def matches(expression, methods):
    m = re.match(r"\\s*execution\\(\\s*(\\S+)\\s+([^\\s(]+)\\((.*)\\)\\s*\\)\\s*\\Z", expression)
    ret, target, params = m.groups()
    tp, _, nm = target.rpartition(".")
    g = lambda p: re.compile(re.escape(p).replace(r"\\.\\.", ".*").replace(r"\\*", ".*") + r"\\Z")
    out = []
    for md in methods:
        ok = g(ret).match(md["ret"]) and g(tp).match(md["cls"]) and g(nm).match(md["name"])
        if params.strip() == "":
            ok = ok and not md["params"]
        elif params.strip() != "..":
            ok = ok and [p.strip() for p in params.split(",")] == md["params"]
        out.append(bool(ok))
    return out
''',
        '''import re
def _glob(pattern):
    return re.compile(re.escape(pattern).replace(r"\\.\\.", r"\\.(?:\\w+\\.)*").replace(r"\\*", r"\\w*") + r"\\Z")
def matches(expression, methods):
    m = re.match(r"\\s*execution\\(\\s*(\\S+)\\s+([^\\s(]+)\\((.*)\\)\\s*\\)\\s*\\Z", expression)
    ret, target, params = m.groups()
    tp, _, nm = target.rpartition(".")
    wanted = [p.strip() for p in params.split(",")] if params.strip() else []
    out = []
    for md in methods:
        ok = _glob(ret).match(md["ret"]) and _glob(tp).match(md["cls"]) and _glob(nm).match(md["name"])
        if ".." not in wanted:
            ok = ok and len(wanted) == len(md["params"]) and all(w in ("*", a) for w, a in zip(wanted, md["params"]))
        out.append(bool(ok))
    return out
''',
    ],
    guide=dict(
        prereqs="Regular expressions, recursion. Lesson: *Advice types, pointcut expressions and aspect order*.",
        intuition="The expression has four slots: return type, class, method name, parameters. Three of them are "
                  "text globs that translate neatly into regular expressions; the parameter list is a small sequence-matching problem of its own.",
        hints=[
            "Pull the four slots apart first. The method name is whatever follows the last dot before the bracket.",
            "Translate a type pattern piece by piece: `..` → a dot followed by zero or more `segment.` groups; `*` → `\\w*`; everything else escaped.",
            "For parameters, when the pattern head is `..` try letting it swallow 0, 1, 2… actual parameters and recurse on the rest.",
        ],
        brute_force="Hand-write comparisons for the handful of shapes you expect (`(..)`, `()`, exact). That passes "
                    "simple cases and collapses on `(String, ..)` or `(.., boolean)`.",
        approach=r"""
1. Parse with one regular expression into `ret`, `target`, `params`; split `target` at its last dot.
2. `_glob` builds an anchored regex for each text slot.
3. `_params_ok(patterns, actual)` is recursive: empty pattern needs empty actual; `..` tries every split;
   otherwise consume one parameter.

**Dry run:** `execution(* com.bookshop..*.*(..))` against `com.bookshop.Clock.now()`. Type pattern
`com.bookshop..*` becomes `com\.bookshop\.(?:\w+\.)*\w*`; `com.bookshop.Clock` matches with zero middle segments.
Name `*` matches `now`; `(..)` matches no parameters. Result `True`.

```java
@Aspect
@Component
class ServiceTimer {
    @Pointcut("execution(* com.bookshop.service..*.*(..))")
    void anyServiceMethod() { }

    @Around("anyServiceMethod()")
    Object time(ProceedingJoinPoint pjp) throws Throwable { return pjp.proceed(); }
}
```
""",
        complexity="Regex matching is linear in the class name for these patterns. The parameter matcher is "
                   "O(p · a) with memoisation, exponential without only when many `..` appear; real signatures are short.",
        pitfalls="Treating `..` as 'any characters' lets `com.bookshop..*` match `com.bookshopping.X`. Letting `*` "
                 "cross a dot makes `com.bookshop.*.*` match deeper packages. `()` is not the same as `(..)`.",
        follow_up="Add `within(...)`, `@annotation(...)` and the combinators `&&`, `||`, `!`.",
    ),
),
dict(
    id="spring-self-invocation",
    title="Detect proxy self-invocation",
    difficulty="Medium",
    pattern="AOP",
    entry="trace",
    description=r"""
Spring applies `@Transactional` (and every other aspect) through a **proxy** that stands in front of your object.
Only calls that go *through the proxy* are intercepted. A method that calls another method of the same object with
`this.other()` skips the proxy, so the annotation on `other` does nothing. This is the *self-invocation pitfall*.

`trace(methods, entry)`:

- `methods` — dict `name -> {"transactional": bool, "calls": [[via, name], ...]}` describing one service class.
  `via` is `"this"` (a direct call on the same object) or `"proxy"` (a call through the Spring-managed reference,
  for example a self-injected bean or another bean calling back).
- `entry` — the method an outside caller invokes. Outside callers always go through the proxy.

Follow the calls depth-first in the listed order (the call graph has no cycles) and return one `[method, verdict]`
pair per invocation, in the order the invocations start:

- `"advised"` — the method is transactional and was reached through the proxy,
- `"bypassed"` — the method is transactional but was reached through `this`,
- `"plain"` — the method is not transactional.

**Example:** `placeOrder` (not transactional) calls `this.reserveStock` (transactional) →
`[["placeOrder", "plain"], ["reserveStock", "bypassed"]]`.
""",
    starter='''def trace(methods: dict, entry: str) -> list:
    pass
''',
    solution='''def trace(methods, entry):
    result = []

    def invoke(name, via):
        method = methods[name]
        if not method["transactional"]:
            verdict = "plain"
        elif via == "proxy":
            verdict = "advised"
        else:
            verdict = "bypassed"
        result.append([name, verdict])
        for call_via, callee in method["calls"]:
            invoke(callee, call_via)

    invoke(entry, "proxy")
    return result
''',
    tests=[
        [{"placeOrder": {"transactional": False, "calls": [["this", "reserveStock"]]},
          "reserveStock": {"transactional": True, "calls": []}}, "placeOrder"],
        [_SVC, "placeOrder"],
        [_SVC, "reserveStock"],
        [_SVC, "format"],
        [_SVC, "charge"],
        [_SVC, "audit"],
        [_SVC, "importAll"],
        [{"a": {"transactional": True, "calls": [["this", "a2"], ["this", "a2"]]},
          "a2": {"transactional": True, "calls": []}}, "a"],
        [{"a": {"transactional": True, "calls": [["proxy", "b"]]}, "b": {"transactional": False, "calls": [["this", "c"]]},
          "c": {"transactional": True, "calls": [["this", "d"]]}, "d": {"transactional": True, "calls": []}}, "a"],
        [{"only": {"transactional": True, "calls": []}}, "only"],
        [{"m%d" % i: {"transactional": i % 3 == 0, "calls": [["this" if i % 2 else "proxy", "m%d" % (i + 1)]] if i < 30 else []}
          for i in range(31)}, "m0"],
    ],
    examples=2,
    wrong_solutions=[
        '''def trace(methods, entry):
    result = []
    def invoke(name):
        result.append([name, "advised" if methods[name]["transactional"] else "plain"])
        for _, callee in methods[name]["calls"]:
            invoke(callee)
    invoke(entry)
    return result
''',
        '''def trace(methods, entry):
    result = []
    def invoke(name, via):
        m = methods[name]
        verdict = "plain" if not m["transactional"] else ("advised" if via == "proxy" else "bypassed")
        result.append([name, verdict])
        for call_via, callee in m["calls"]:
            invoke(callee, "this" if via == "this" else call_via)
    invoke(entry, "proxy")
    return result
''',
        '''def trace(methods, entry):
    result = []
    def invoke(name, via):
        m = methods[name]
        verdict = "plain" if not m["transactional"] else ("advised" if via == "proxy" else "bypassed")
        for call_via, callee in m["calls"]:
            invoke(callee, call_via)
        result.append([name, verdict])
    invoke(entry, "proxy")
    return result
''',
    ],
    guide=dict(
        prereqs="Lesson: *How Spring AOP works: proxies and your first aspect* and *@Transactional, rollback rules and the self-invocation pitfall*.",
        intuition="The verdict depends on exactly two facts: is the method annotated, and which door did this "
                  "particular call come through. Nothing about the caller's own status matters.",
        hints=[
            "Carry the `via` of the current call as a parameter of your recursive function.",
            "The entry call counts as `proxy`.",
            "Record the verdict before descending into the callees so the output is in start order.",
        ],
        brute_force="The recursion is the direct solution; the mistake to avoid is making it smarter than the rule.",
        approach=r"""
**Dry run** on `placeOrder → this.reserveStock, this.charge`; `charge → proxy.audit`; `audit → this.format`:
`placeOrder` plain; `reserveStock` bypassed; `charge` bypassed; `audit` **advised** (the call went through the
proxy even though its caller was reached via `this`); `format` plain.

```java
@Service
public class OrderService {

    public void placeOrder(Order order) {
        reserveStock(order);          // this.reserveStock(...) -> NO transaction is started
    }

    @Transactional
    public void reserveStock(Order order) { /* two updates that must succeed together */ }
}
```

Fixes: move `reserveStock` to another bean and inject it; make `placeOrder` itself `@Transactional`; or use
`TransactionTemplate` for an explicit boundary.
""",
        complexity="Time and space O(number of invocations).",
        pitfalls="Marking every annotated method as advised; 'inheriting' the bypass from the caller; recording "
                 "the verdict after the children (post-order).",
        follow_up="Private and `final` methods cannot be overridden by a class-based proxy. Add a `visibility` field and report those too.",
    ),
),
]
