_SHOP = [
    {"name": "priceCalculator", "types": ["PriceCalculator"], "needs": []},
    {"name": "jdbcBookRepository", "types": ["JdbcBookRepository", "BookRepository"], "needs": ["DataSource"]},
    {"name": "dataSource", "types": ["HikariDataSource", "DataSource"], "needs": []},
    {"name": "orderService", "types": ["OrderService"], "needs": ["BookRepository", "PriceCalculator"]},
    {"name": "orderController", "types": ["OrderController"], "needs": ["OrderService"]},
]

_CANDS = [
    {"name": "emailNotifier", "types": ["EmailNotifier", "Notifier"], "primary": False},
    {"name": "smsNotifier", "types": ["SmsNotifier", "Notifier"], "primary": False},
    {"name": "pushNotifier", "types": ["PushNotifier", "Notifier"], "primary": False},
    {"name": "clock", "types": ["Clock"], "primary": False},
]
_CANDS_P = [dict(c, primary=(c["name"] == "smsNotifier")) for c in _CANDS]
_CANDS_PP = [dict(c, primary=(c["name"] in ("smsNotifier", "pushNotifier"))) for c in _CANDS]

_AUTO = [
    {"name": "DataSourceAutoConfiguration", "bean": "dataSource",
     "conditions": [["onClass", "javax.sql.DataSource"], ["onMissingBean", "dataSource"]]},
    {"name": "JdbcTemplateAutoConfiguration", "bean": "jdbcTemplate",
     "conditions": [["onClass", "org.springframework.jdbc.core.JdbcTemplate"], ["onBean", "dataSource"],
                    ["onMissingBean", "jdbcTemplate"]]},
    {"name": "CacheAutoConfiguration", "bean": "cacheManager",
     "conditions": [["onProperty", "shop.cache.enabled", None, False], ["onMissingBean", "cacheManager"]]},
    {"name": "MetricsAutoConfiguration", "bean": "meterRegistry",
     "conditions": [["onProperty", "shop.metrics.enabled", None, True]]},
    {"name": "MailAutoConfiguration", "bean": "mailSender",
     "conditions": [["onProperty", "shop.mail.transport", "smtp", False], ["onMissingClass", "com.fake.NoMail"]]},
]
_CP = ["javax.sql.DataSource", "org.springframework.jdbc.core.JdbcTemplate"]

PROBLEMS = [
dict(
    id="spring-wire-by-type",
    title="Wire a bean graph by type",
    difficulty="Easy",
    pattern="Spring container",
    entry="wire",
    description=r"""
A Spring container keeps a list of **bean definitions**. When a bean's constructor asks for a parameter of some
type, the container looks for the bean that **is of that type** (its own class or any interface it implements) and
passes it in. Build that lookup.

`wire(beans)` receives a list of dicts:

- `name` — the bean name,
- `types` — every type the bean can be seen as (its class first, then its interfaces),
- `needs` — the types of its constructor parameters, in order.

Return a dict that maps every bean name to the list of **bean names** injected into it, in parameter order.
If a needed type matches no bean, return the string `"NoSuchBeanDefinitionException: <type>"` for the first
problem found (scan beans in list order, parameters left to right). The input guarantees that a type never
matches more than one bean.

**Example:** a bean `orderService` needing `["BookRepository"]` and a bean `jdbcBookRepository` whose types are
`["JdbcBookRepository", "BookRepository"]` → `{"orderService": ["jdbcBookRepository"], "jdbcBookRepository": []}`.
""",
    starter='''def wire(beans: list):
    pass
''',
    solution='''def wire(beans):
    wired = {}
    for bean in beans:
        injected = []
        for needed in bean["needs"]:
            matches = [c["name"] for c in beans if needed in c["types"]]
            if not matches:
                return "NoSuchBeanDefinitionException: " + needed
            injected.append(matches[0])
        wired[bean["name"]] = injected
    return wired
''',
    tests=[
        [_SHOP],
        [[{"name": "a", "types": ["A"], "needs": []}]],
        [[]],
        [[{"name": "a", "types": ["A"], "needs": ["B"]}]],
        [_SHOP[:2]],
        [[{"name": "x", "types": ["X", "Runnable"], "needs": ["Runnable"]}]],
        [[{"name": "report", "types": ["Report"], "needs": ["Clock", "Clock"]},
          {"name": "systemClock", "types": ["SystemClock", "Clock"], "needs": []}]],
        [[{"name": "a", "types": ["A"], "needs": ["C"]}, {"name": "b", "types": ["B"], "needs": ["Missing"]},
          {"name": "c", "types": ["C"], "needs": []}]],
        [[{"name": "a", "types": ["A"], "needs": ["Zed", "Missing"]}, {"name": "b", "types": ["B"], "needs": ["Gone"]}]],
        [list(reversed(_SHOP))],
        [[{"name": "svc", "types": ["Svc"], "needs": ["Repo", "Mailer", "Clock"]},
          {"name": "mailer", "types": ["SmtpMailer", "Mailer", "AutoCloseable"], "needs": ["Clock"]},
          {"name": "repo", "types": ["Repo"], "needs": []},
          {"name": "clock", "types": ["Clock"], "needs": []}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def wire(beans):
    wired = {}
    for bean in beans:
        injected = []
        for needed in bean["needs"]:
            matches = [c["name"] for c in beans if c["types"][0] == needed]
            if not matches:
                return "NoSuchBeanDefinitionException: " + needed
            injected.append(matches[0])
        wired[bean["name"]] = injected
    return wired
''',
        '''def wire(beans):
    wired = {}
    for bean in beans:
        wired[bean["name"]] = [c["name"] for needed in bean["needs"] for c in beans if needed in c["types"]]
    return wired
''',
    ],
    guide=dict(
        prereqs="Python lists and dicts. The lesson *The application context and @Bean* explains what a bean is.",
        intuition="Injection by type is a search: for each constructor parameter, find the one bean that can be "
                  "viewed as that type. An interface counts, which is why `types` holds more than the class name.",
        hints=[
            "Handle one bean at a time, and inside it one needed type at a time.",
            "A bean matches when the needed type appears anywhere in its `types` list, not only at index 0.",
            "Return the error string immediately when a search comes back empty; otherwise collect the names.",
        ],
        brute_force="The direct double loop (for every need, scan all beans) is already what is asked. It costs "
                    "O(B · N · T) for B beans, N needs and T types per bean.",
        approach=r"""
1. Create an empty result dict.
2. For each bean, for each needed type, collect the names of beans whose `types` contain it.
3. No match → return the error string. Otherwise append the single match.

**Dry run** with `orderService` needing `BookRepository`, `PriceCalculator`: the scan for `BookRepository` finds
`jdbcBookRepository` (second entry of its types), the scan for `PriceCalculator` finds `priceCalculator`, giving
`["jdbcBookRepository", "priceCalculator"]`.

A faster version first builds an index `type -> bean name` in one pass, then every lookup is O(1).

The same thing in Spring:

```java
@Service
public class OrderService {
    private final BookRepository books;      // an interface
    private final PriceCalculator prices;

    public OrderService(BookRepository books, PriceCalculator prices) {  // Spring fills both by type
        this.books = books;
        this.prices = prices;
    }
}
```
""",
        complexity="Time O(B · N · T) with the scan, O(total types + total needs) with an index. Space O(B + N).",
        pitfalls="Comparing only against the class name misses interface injection, the most common style. "
                 "Silently skipping a missing type hides the error Spring would raise at start-up.",
        follow_up="What should happen when two beans match? That is the next problem, *Pick the bean to inject*.",
    ),
),
dict(
    id="spring-creation-order",
    title="Constructor injection order and cycle detection",
    difficulty="Medium",
    pattern="Spring container",
    entry="creation_order",
    description=r"""
With constructor injection a bean cannot be built until every constructor argument exists. The container
therefore walks the definitions **in the order they were registered** and, before building a bean, first builds
each of its dependencies **in parameter order** (a depth-first walk). Every bean is a singleton: once built it is
reused.

`creation_order(beans)` receives a list of `[name, [dependency names]]` pairs. Every dependency name is the name
of a bean in the list.

- If all beans can be built, return `{"order": [...]}` with the names in the order their constructors finish.
- If the walk reaches a bean that is *currently being built*, there is a circular dependency. Return
  `{"cycle": [...]}` with the chain from that bean back to itself, for example `["a", "b", "a"]`. Report the
  first cycle the walk meets and stop.

**Example:** `[["controller", ["service"]], ["repo", []], ["service", ["repo"]]]` →
`{"order": ["repo", "service", "controller"]}`.

**Example:** `[["a", ["b"]], ["b", ["a"]]]` → `{"cycle": ["a", "b", "a"]}`.
""",
    starter='''def creation_order(beans: list) -> dict:
    pass
''',
    solution='''def creation_order(beans):
    deps = {name: needs for name, needs in beans}
    built, order, in_creation = set(), [], []

    def create(name):
        if name in built:
            return None
        if name in in_creation:
            return in_creation[in_creation.index(name):] + [name]
        in_creation.append(name)
        for dep in deps[name]:
            cycle = create(dep)
            if cycle:
                return cycle
        in_creation.pop()
        built.add(name)
        order.append(name)
        return None

    for name, _ in beans:
        cycle = create(name)
        if cycle:
            return {"cycle": cycle}
    return {"order": order}
''',
    tests=[
        [[["controller", ["service"]], ["repo", []], ["service", ["repo"]]]],
        [[["a", ["b"]], ["b", ["a"]]]],
        [[]],
        [[["solo", []]]],
        [[["self", ["self"]]]],
        [[["a", ["b", "c"]], ["b", ["d"]], ["c", ["d"]], ["d", []]]],
        [[["a", ["c", "b"]], ["b", ["d"]], ["c", ["d"]], ["d", []]]],
        [[["x", []], ["a", ["b"]], ["b", ["c"]], ["c", ["a"]]]],
        [[["a", ["b"]], ["b", ["c"]], ["c", ["d"]], ["d", ["b"]]]],
        [[["z", []], ["y", ["z"]], ["x", ["y", "z"]], ["w", ["x", "y", "z"]]]],
        [[["a", ["b"]], ["b", []], ["c", ["d"]], ["d", ["c"]]]],
        [[["n%d" % i, ["n%d" % (i + 1)] if i < 300 else []] for i in range(301)]],
        [[["a", ["d", "b"]], ["b", ["c"]], ["c", ["b"]], ["d", []]]],
        [[["a", ["b"]], ["b", ["d", "c"]], ["c", ["b"]], ["d", []]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def creation_order(beans):
    return {"order": [n for n, _ in beans]}
''',
        '''def creation_order(beans):
    deps = dict((n, d) for n, d in beans)
    seen, order = [], []
    def create(name):
        if name in seen:
            return None if name in order else seen[seen.index(name):] + [name]
        seen.append(name)
        for dep in deps[name]:
            c = create(dep)
            if c:
                return c
        order.append(name)
        return None
    for n, _ in beans:
        c = create(n)
        if c:
            return {"cycle": c}
    return {"order": order}
''',
    ],
    guide=dict(
        prereqs="Recursion and depth-first search. Lesson: *Circular dependencies, @Primary and @Qualifier*.",
        intuition="Keep two collections: beans that are finished, and beans whose constructor is *waiting* for "
                  "arguments right now. Meeting a waiting bean again means the chain has closed into a loop.",
        hints=[
            "Write a recursive `create(name)` that builds dependencies first and appends the name last.",
            "A finished bean is skipped. A bean that is still on the 'in creation' list is a cycle.",
            "The in-creation list is ordered, so the cycle is the slice from the repeated name to the end, plus the name.",
        ],
        brute_force="Repeatedly scan for a bean whose dependencies are all built (O(n²)); if a pass builds nothing, "
                    "there is a cycle. That finds *whether* a cycle exists but not the order Spring would use.",
        approach=r"""
Depth-first search with three states: not started, in creation, built.

**Dry run** on `a→[b]`, `b→[c]`, `c→[a]`: `create(a)` puts `a` in creation and calls `create(b)`, which calls
`create(c)`, which calls `create(a)`. `a` is still in creation at index 0, so the answer is the slice
`["a","b","c"]` plus `"a"`.

A diamond (`a→b,c`, `b→d`, `c→d`) is not a cycle: when `c` asks for `d`, `d` is already *built*.

Spring raises the same thing as `BeanCurrentlyInCreationException`:

```java
@Component
class Invoicing {
    Invoicing(Shipping shipping) { }   // needs Shipping first
}

@Component
class Shipping {
    Shipping(Invoicing invoicing) { }  // needs Invoicing first -> start-up fails
}
```
""",
        complexity="Time O(V + E): each bean is built once and each dependency edge is followed once. Space O(V).",
        pitfalls="Using a single 'seen' set reports a diamond as a cycle. Forgetting to remove a bean from the "
                 "in-creation list when it finishes has the same effect. A bean depending on itself is a cycle of length one.",
        follow_up="Topological sort with Kahn's algorithm gives *an* order, but not necessarily the depth-first one.",
    ),
),
dict(
    id="spring-resolve-candidate",
    title="Pick the bean to inject: @Primary, @Qualifier and names",
    difficulty="Medium",
    pattern="Spring container",
    entry="resolve",
    description=r"""
Several beans may share a type. Spring then needs a tie-breaker. Implement the decision for a single injection
point.

`resolve(candidates, required_type, qualifier, param_name)`:

- `candidates` — list of `{"name", "types", "primary"}` dicts (every bean in the context),
- `required_type` — the parameter's type,
- `qualifier` — the value of `@Qualifier` on the parameter, or `None`,
- `param_name` — the name of the constructor parameter.

Rules, in this order:

1. Keep only beans whose `types` contain `required_type`. None left → return `"NoSuchBeanDefinitionException"`.
2. If `qualifier` is given, the answer is the remaining bean whose **name equals the qualifier**; if there is none,
   return `"NoSuchBeanDefinitionException"`. (`@Primary` is ignored in this case.)
3. Exactly one bean left → that bean.
4. Exactly one of them is primary → that bean. More than one primary → `"NoUniqueBeanDefinitionException"`.
5. No primary: if a bean's name equals `param_name`, pick it. Otherwise `"NoUniqueBeanDefinitionException"`.

Return the chosen bean's name or the exception name.

**Example:** beans `emailNotifier` and `smsNotifier` both of type `Notifier`, none primary, no qualifier,
parameter named `notifier` → `"NoUniqueBeanDefinitionException"`; parameter named `smsNotifier` → `"smsNotifier"`.
""",
    starter='''def resolve(candidates: list, required_type: str, qualifier, param_name: str) -> str:
    pass
''',
    solution='''def resolve(candidates, required_type, qualifier, param_name):
    matches = [c for c in candidates if required_type in c["types"]]
    if not matches:
        return "NoSuchBeanDefinitionException"
    if qualifier is not None:
        for c in matches:
            if c["name"] == qualifier:
                return c["name"]
        return "NoSuchBeanDefinitionException"
    if len(matches) == 1:
        return matches[0]["name"]
    primaries = [c for c in matches if c["primary"]]
    if len(primaries) == 1:
        return primaries[0]["name"]
    if len(primaries) > 1:
        return "NoUniqueBeanDefinitionException"
    for c in matches:
        if c["name"] == param_name:
            return c["name"]
    return "NoUniqueBeanDefinitionException"
''',
    tests=[
        [_CANDS, "Notifier", None, "notifier"],
        [_CANDS, "Notifier", None, "smsNotifier"],
        [_CANDS, "Clock", None, "anything"],
        [_CANDS, "Mailer", None, "mailer"],
        [_CANDS, "Notifier", "pushNotifier", "notifier"],
        [_CANDS_P, "Notifier", None, "notifier"],
        [_CANDS_P, "Notifier", "emailNotifier", "notifier"],
        [_CANDS_P, "Notifier", None, "emailNotifier"],
        [_CANDS_PP, "Notifier", None, "smsNotifier"],
        [_CANDS, "Notifier", "clock", "notifier"],
        [_CANDS, "Notifier", "faxNotifier", "emailNotifier"],
        [_CANDS_PP, "PushNotifier", None, "x"],
        [[], "Notifier", None, "notifier"],
        [_CANDS, "Notifier", None, "clock"],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolve(candidates, required_type, qualifier, param_name):
    matches = [c for c in candidates if required_type in c["types"]]
    if not matches:
        return "NoSuchBeanDefinitionException"
    primaries = [c for c in matches if c["primary"]]
    if len(primaries) == 1:
        return primaries[0]["name"]
    if qualifier is not None:
        for c in matches:
            if c["name"] == qualifier:
                return c["name"]
        return "NoSuchBeanDefinitionException"
    if len(matches) == 1:
        return matches[0]["name"]
    for c in matches:
        if c["name"] == param_name:
            return c["name"]
    return "NoUniqueBeanDefinitionException"
''',
        '''def resolve(candidates, required_type, qualifier, param_name):
    matches = [c for c in candidates if required_type in c["types"]]
    if not matches:
        return "NoSuchBeanDefinitionException"
    if qualifier is not None:
        for c in matches:
            if c["name"] == qualifier:
                return c["name"]
        return "NoSuchBeanDefinitionException"
    if len(matches) == 1:
        return matches[0]["name"]
    for c in matches:
        if c["name"] == param_name:
            return c["name"]
    primaries = [c for c in matches if c["primary"]]
    if len(primaries) == 1:
        return primaries[0]["name"]
    return "NoUniqueBeanDefinitionException"
''',
        '''def resolve(candidates, required_type, qualifier, param_name):
    matches = [c for c in candidates if required_type in c["types"]]
    if qualifier is not None:
        matches = [c for c in candidates if c["name"] == qualifier]
    if not matches:
        return "NoSuchBeanDefinitionException"
    if len(matches) == 1:
        return matches[0]["name"]
    primaries = [c for c in matches if c["primary"]]
    if primaries:
        return primaries[0]["name"]
    for c in matches:
        if c["name"] == param_name:
            return c["name"]
    return "NoUniqueBeanDefinitionException"
''',
    ],
    guide=dict(
        prereqs="Lesson: *Circular dependencies, @Primary and @Qualifier*. Python list comprehensions.",
        intuition="The container narrows a list. Type narrows it first. An explicit qualifier is the strongest "
                  "statement the developer can make; a primary flag is a default; the parameter name is the last resort.",
        hints=[
            "Start by filtering on type, and return early when the filtered list is empty.",
            "Treat the qualifier branch completely separately: it either finds a name or fails.",
            "Count primaries: one wins, several is ambiguous, zero falls through to the parameter-name comparison.",
        ],
        brute_force="There is no cheaper or dearer algorithm here: the work is a linear filter. The difficulty is the order of the rules.",
        approach=r"""
Follow the five rules as five `if` blocks.

**Dry run:** candidates `emailNotifier`, `smsNotifier` (primary), `pushNotifier`; type `Notifier`; qualifier
`emailNotifier`. Step 1 keeps three beans. Step 2 has a qualifier and finds `emailNotifier`, so the primary flag on
`smsNotifier` never gets a say.

```java
@Component @Primary
class SmsNotifier implements Notifier { }

@Component
class EmailNotifier implements Notifier { }

@Service
class ReminderService {
    ReminderService(@Qualifier("emailNotifier") Notifier notifier) { }  // qualifier beats @Primary
}

@Service
class AlertService {
    AlertService(Notifier notifier) { }                                  // gets smsNotifier (@Primary)
}
```
""",
        complexity="Time O(n · t) to filter n beans with t types each. Space O(n) for the filtered list.",
        pitfalls="Checking `@Primary` before the qualifier, or the parameter name before `@Primary`, both give "
                 "plausible but wrong answers. A qualifier naming a bean of a *different* type must not match. "
                 "Two primaries are an error, not 'first one wins'.",
        follow_up="Real Spring also lets you inject `List<Notifier>` to receive every candidate. How would you add that?",
    ),
),
dict(
    id="spring-scope-count",
    title="Count instances: singleton versus prototype",
    difficulty="Easy",
    pattern="Bean scopes",
    entry="count_instances",
    description=r"""
A **singleton** bean has one instance per container. A **prototype** bean gets a fresh instance every time
someone asks the container for it, including every time it is injected into another bean that is being created.

`count_instances(defs, gets)`:

- `defs` — list of `[name, scope, deps]` where `scope` is `"singleton"` or `"prototype"` and `deps` are the names
  of the beans injected into it when an instance is created. The graph has no cycles.
- `gets` — a list of bean names requested with `context.getBean(name)` after start-up, in order.

At start-up the container creates every singleton in definition order (dependencies are obtained first as needed).
Prototypes are created only on demand. *Obtaining* a singleton creates it the first time and reuses it afterwards;
*obtaining* a prototype always creates a new instance, and creating any instance obtains each of its `deps`.

Return a dict `name -> number of instances created`.

**Example:** `defs = [["cart", "prototype", ["catalog"]], ["catalog", "singleton", []]]`, `gets = ["cart", "cart"]`
→ `{"cart": 2, "catalog": 1}`.
""",
    starter='''def count_instances(defs: list, gets: list) -> dict:
    pass
''',
    solution='''def count_instances(defs, gets):
    info = {name: (scope, deps) for name, scope, deps in defs}
    count = {name: 0 for name in info}
    singletons = set()

    def obtain(name):
        scope, deps = info[name]
        if scope == "singleton":
            if name in singletons:
                return
            singletons.add(name)
        count[name] += 1
        for dep in deps:
            obtain(dep)

    for name, scope, _ in defs:
        if scope == "singleton":
            obtain(name)
    for name in gets:
        obtain(name)
    return count
''',
    tests=[
        [[["cart", "prototype", ["catalog"]], ["catalog", "singleton", []]], ["cart", "cart"]],
        [[["catalog", "singleton", []]], ["catalog", "catalog", "catalog"]],
        [[["cart", "prototype", []]], []],
        [[], []],
        [[["checkout", "singleton", ["cart"]], ["cart", "prototype", []]], ["checkout", "checkout"]],
        [[["checkout", "singleton", ["cart"]], ["cart", "prototype", []]], ["cart", "checkout", "cart"]],
        [[["a", "prototype", ["b", "b"]], ["b", "prototype", ["c"]], ["c", "prototype", []]], ["a", "a"]],
        [[["a", "prototype", ["b", "b"]], ["b", "prototype", ["c"]], ["c", "singleton", []]], ["a", "b"]],
        [[["s1", "singleton", ["p"]], ["s2", "singleton", ["p"]], ["p", "prototype", ["s1"]]], ["p"]],
        [[["report", "prototype", ["formatter", "clock"]], ["formatter", "prototype", ["clock"]],
          ["clock", "singleton", []]], ["report"] * 50],
        [[["a", "singleton", ["b"]], ["b", "singleton", ["c"]], ["c", "singleton", []]], ["c", "b", "a"]],
        [[["p", "prototype", ["q"]], ["q", "prototype", []], ["s", "singleton", ["p", "q"]]], ["s", "p"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def count_instances(defs, gets):
    count = {name: (1 if scope == "singleton" else 0) for name, scope, _ in defs}
    scopes = {name: scope for name, scope, _ in defs}
    for name in gets:
        if scopes[name] == "prototype":
            count[name] += 1
    return count
''',
        '''def count_instances(defs, gets):
    info = {name: (scope, deps) for name, scope, deps in defs}
    count = {name: 0 for name in info}
    done = set()
    def obtain(name):
        scope, deps = info[name]
        if scope == "singleton":
            if name in done:
                return
            done.add(name)
        count[name] += 1
        for dep in deps:
            obtain(dep)
    for name in gets:
        obtain(name)
    return count
''',
    ],
    guide=dict(
        prereqs="Lesson: *Singleton scope, eager and lazy beans, thread safety*. Recursion.",
        intuition="'Obtain' is the only operation. For a singleton it is create-once-then-reuse; for a prototype "
                  "it is always create. Creating anything obtains its dependencies, so prototypes cascade.",
        hints=[
            "Write one helper, `obtain(name)`, and call it for start-up and for every `getBean`.",
            "Remember which singletons exist in a set. Return early when a singleton is already there.",
            "A prototype injected into a singleton is created once, at the moment the singleton is created.",
        ],
        brute_force="Simulating the container literally, as described, is the straightforward solution. A closed "
                    "formula exists (multiply counts along paths) but is harder to get right.",
        approach=r"""
1. Index the definitions by name; start all counts at 0.
2. `obtain(name)`: singleton already made → stop. Otherwise count one instance and obtain each dependency.
3. Obtain every singleton in definition order, then every name in `gets`.

**Dry run:** `checkout` (singleton) depends on `cart` (prototype); `gets = ["cart","checkout","cart"]`.
Start-up creates `checkout` and with it one `cart`. The three gets add a `cart`, nothing, and another `cart`:
`{"checkout": 1, "cart": 3}`.

```java
@Component
@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)
class Cart { }

@Service                      // singleton by default
class CheckoutService {
    private final Cart cart;  // ONE Cart forever: injected once when the singleton is built
    CheckoutService(Cart cart) { this.cart = cart; }
}
```
""",
        complexity="Time O(total instances created × average dependency count). Space O(number of beans + recursion depth).",
        pitfalls="Forgetting the eager start-up pass undercounts singletons nobody asks for. Assuming a prototype "
                 "inside a singleton is recreated on each call is the classic interview trap: it is injected once.",
        follow_up="How would `ObjectProvider<Cart>` or `@Lookup` change the count for the checkout example?",
    ),
),
dict(
    id="spring-lazy-eager-order",
    title="Eager and lazy initialisation order",
    difficulty="Medium",
    pattern="Bean scopes",
    entry="init_log",
    description=r"""
Singleton beans are **eager** by default: the container creates them while it starts. A bean marked `@Lazy` is
created only when something first needs it, and "something" can be another bean's constructor.

`init_log(defs, requests)`:

- `defs` — list of `{"name", "lazy", "deps"}` in registration order. All beans are singletons and the graph is acyclic.
- `requests` — bean names asked for with `getBean` after start-up.

Start-up: go through `defs` in order; for each bean that is **not lazy** and not created yet, create it. Creating a
bean first creates each of its not-yet-created `deps` in order (lazy or not), then the bean itself.
Afterwards serve `requests` in order, creating on first use with the same dependencies-first rule.

Return `{"startup": [...], "runtime": [...]}` listing bean names in creation order for each phase.

**Example:** `report` (lazy) depends on `clock`; `clock` is eager; requests `["report", "report"]` →
`{"startup": ["clock"], "runtime": ["report"]}`.
""",
    starter='''def init_log(defs: list, requests: list) -> dict:
    pass
''',
    solution='''def init_log(defs, requests):
    by_name = {d["name"]: d for d in defs}
    created = set()

    def create(name, log):
        if name in created:
            return
        for dep in by_name[name]["deps"]:
            create(dep, log)
        created.add(name)
        log.append(name)

    startup, runtime = [], []
    for d in defs:
        if not d["lazy"]:
            create(d["name"], startup)
    for name in requests:
        create(name, runtime)
    return {"startup": startup, "runtime": runtime}
''',
    tests=[
        [[{"name": "report", "lazy": True, "deps": ["clock"]}, {"name": "clock", "lazy": False, "deps": []}], ["report", "report"]],
        [[{"name": "a", "lazy": False, "deps": ["b"]}, {"name": "b", "lazy": True, "deps": []}], ["b"]],
        [[], []],
        [[{"name": "a", "lazy": True, "deps": []}], []],
        [[{"name": "a", "lazy": True, "deps": ["b"]}, {"name": "b", "lazy": True, "deps": ["c"]},
          {"name": "c", "lazy": True, "deps": []}], ["b", "a", "c"]],
        [[{"name": "c", "lazy": False, "deps": []}, {"name": "b", "lazy": False, "deps": ["c"]},
          {"name": "a", "lazy": False, "deps": ["b"]}], ["a"]],
        [[{"name": "a", "lazy": False, "deps": ["c", "b"]}, {"name": "b", "lazy": False, "deps": []},
          {"name": "c", "lazy": True, "deps": ["d"]}, {"name": "d", "lazy": True, "deps": []},
          {"name": "e", "lazy": True, "deps": ["d"]}], ["e", "d"]],
        [[{"name": "pdf", "lazy": True, "deps": ["fonts", "clock"]}, {"name": "fonts", "lazy": True, "deps": []},
          {"name": "clock", "lazy": False, "deps": []}, {"name": "mail", "lazy": True, "deps": ["pdf"]}], ["mail", "fonts"]],
        [[{"name": "x", "lazy": True, "deps": []}, {"name": "y", "lazy": False, "deps": []}], ["y", "x", "y", "x"]],
        [[{"name": "z", "lazy": False, "deps": ["y"]}, {"name": "y", "lazy": True, "deps": ["x"]},
          {"name": "x", "lazy": False, "deps": []}, {"name": "w", "lazy": True, "deps": ["z"]}], ["w"]],
        [[{"name": "b%d" % i, "lazy": i % 2 == 0, "deps": ["b%d" % (i + 1)] if i < 40 else []} for i in range(41)], ["b0"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def init_log(defs, requests):
    startup = [d["name"] for d in defs if not d["lazy"]]
    runtime = []
    for r in requests:
        if r not in startup and r not in runtime:
            runtime.append(r)
    return {"startup": startup, "runtime": runtime}
''',
        '''def init_log(defs, requests):
    by_name = {d["name"]: d for d in defs}
    created = set()
    def create(name, log):
        if name in created:
            return
        created.add(name)
        log.append(name)
        for dep in by_name[name]["deps"]:
            create(dep, log)
    startup, runtime = [], []
    for d in defs:
        if not d["lazy"]:
            create(d["name"], startup)
    for name in requests:
        create(name, runtime)
    return {"startup": startup, "runtime": runtime}
''',
        '''def init_log(defs, requests):
    by_name = {d["name"]: d for d in defs}
    created = set()
    def create(name, log):
        if name in created:
            return
        for dep in by_name[name]["deps"]:
            if not by_name[dep]["lazy"]:
                create(dep, log)
        created.add(name)
        log.append(name)
    startup, runtime = [], []
    for d in defs:
        if not d["lazy"]:
            create(d["name"], startup)
    for name in requests:
        create(name, runtime)
    return {"startup": startup, "runtime": runtime}
''',
    ],
    guide=dict(
        prereqs="Lesson: *Singleton scope, eager and lazy beans, thread safety*. The previous problem on creation order.",
        intuition="`@Lazy` on a class only says 'do not create me for my own sake at start-up'. If an eager bean "
                  "needs it as a constructor argument, it has to exist, so it is created anyway.",
        hints=[
            "Reuse the dependencies-first recursion from the creation-order problem.",
            "Pass the log list into the helper so the same code serves both phases.",
            "Start-up loops only over non-lazy definitions, but the recursion ignores the lazy flag.",
        ],
        brute_force="A two-list simulation is the solution; there is no slower alternative worth describing.",
        approach=r"""
One `created` set shared by both phases, one recursive `create(name, log)`.

**Dry run:** `a` eager needs `c` then `b`; `c` lazy needs `d` (lazy). Start-up visits `a`: create `d`, `c`, `b`,
then `a`. `e` (lazy, needs `d`) is untouched. Request `e` → runtime `["e"]` because `d` already exists.

```java
@Service
@Lazy                       // created on first use...
class PdfRenderer { }

@Service
class InvoiceService {      // ...unless an eager bean needs it in its constructor
    InvoiceService(PdfRenderer renderer) { }
}
```

To keep the dependency itself lazy you put `@Lazy` on the *injection point*, which injects a proxy that creates
the real bean on the first method call.
""",
        complexity="Time O(V + E + R) for V beans, E dependency edges and R requests. Space O(V).",
        pitfalls="Logging the bean before its dependencies reverses constructor order. Skipping lazy dependencies "
                 "of eager beans is the misconception this problem exists to remove.",
        follow_up="`spring.main.lazy-initialization=true` makes every bean lazy. Which bugs would then surface only at runtime?",
    ),
),
dict(
    id="spring-lifecycle-order",
    title="Bean lifecycle callback order",
    difficulty="Medium",
    pattern="Bean lifecycle",
    entry="lifecycle",
    description=r"""
After the container constructs a bean it runs the bean's initialisation callbacks, and when the context closes it
runs destruction callbacks. Produce the complete log.

`lifecycle(beans)` receives a list of dicts in registration order:

- `name`, `deps` (constructor dependencies, acyclic),
- `scope` — `"singleton"` or `"prototype"`,
- `callbacks` — any subset of `"postConstruct"`, `"afterPropertiesSet"`, `"initMethod"`, `"preDestroy"`,
  `"destroy"`, `"destroyMethod"`, in any order.

**Start-up.** For each singleton in registration order (if not created yet): obtain its dependencies in order, then
log `"<name>:constructor"`, then its initialisation callbacks that are present, always in the order
`postConstruct`, `afterPropertiesSet`, `initMethod`. Obtaining a singleton that exists does nothing. Obtaining a
prototype always builds a new instance in the same way (dependencies, constructor, init callbacks). A prototype
that nobody depends on is never built.

**Shutdown.** Log `"context:close"`. Then for each **singleton** in the reverse of the order their constructors
ran, log its destruction callbacks that are present in the order `preDestroy`, `destroy`, `destroyMethod`.
Prototype instances never receive destruction callbacks.

Return the list of log lines, each formatted `"<name>:<event>"`.

**Example:** one singleton `pool` with callbacks `["destroy", "postConstruct"]` →
`["pool:constructor", "pool:postConstruct", "context:close", "pool:destroy"]`.
""",
    starter='''def lifecycle(beans: list) -> list:
    pass
''',
    solution='''INIT = ["postConstruct", "afterPropertiesSet", "initMethod"]
DESTROY = ["preDestroy", "destroy", "destroyMethod"]


def lifecycle(beans):
    by_name = {b["name"]: b for b in beans}
    log, singletons = [], []

    def obtain(name):
        bean = by_name[name]
        if bean["scope"] == "singleton" and name in singletons:
            return
        for dep in bean["deps"]:
            obtain(dep)
        log.append(name + ":constructor")
        if bean["scope"] == "singleton":
            singletons.append(name)
        for cb in INIT:
            if cb in bean["callbacks"]:
                log.append(name + ":" + cb)

    for bean in beans:
        if bean["scope"] == "singleton":
            obtain(bean["name"])
    log.append("context:close")
    for name in reversed(singletons):
        for cb in DESTROY:
            if cb in by_name[name]["callbacks"]:
                log.append(name + ":" + cb)
    return log
''',
    tests=[
        [[{"name": "pool", "scope": "singleton", "deps": [], "callbacks": ["destroy", "postConstruct"]}]],
        [[{"name": "svc", "scope": "singleton", "deps": ["pool"], "callbacks": ["preDestroy", "postConstruct"]},
          {"name": "pool", "scope": "singleton", "deps": [], "callbacks": ["initMethod", "destroyMethod"]}]],
        [[]],
        [[{"name": "p", "scope": "prototype", "deps": [], "callbacks": ["postConstruct", "preDestroy"]}]],
        [[{"name": "a", "scope": "singleton", "deps": [],
           "callbacks": ["destroyMethod", "destroy", "preDestroy", "initMethod", "afterPropertiesSet", "postConstruct"]}]],
        [[{"name": "s", "scope": "singleton", "deps": ["p"], "callbacks": ["preDestroy"]},
          {"name": "p", "scope": "prototype", "deps": [], "callbacks": ["postConstruct", "preDestroy"]}]],
        [[{"name": "s1", "scope": "singleton", "deps": ["p"], "callbacks": []},
          {"name": "s2", "scope": "singleton", "deps": ["p", "s1"], "callbacks": ["destroy"]},
          {"name": "p", "scope": "prototype", "deps": ["c"], "callbacks": ["initMethod"]},
          {"name": "c", "scope": "singleton", "deps": [], "callbacks": ["afterPropertiesSet", "destroyMethod"]}]],
        [[{"name": "a", "scope": "singleton", "deps": [], "callbacks": ["preDestroy"]},
          {"name": "b", "scope": "singleton", "deps": [], "callbacks": ["preDestroy"]},
          {"name": "c", "scope": "singleton", "deps": [], "callbacks": ["preDestroy"]}]],
        [[{"name": "web", "scope": "singleton", "deps": ["svc"], "callbacks": ["postConstruct", "preDestroy"]},
          {"name": "svc", "scope": "singleton", "deps": ["repo"], "callbacks": ["postConstruct", "preDestroy"]},
          {"name": "repo", "scope": "singleton", "deps": [], "callbacks": ["postConstruct", "preDestroy"]}]],
        [[{"name": "plain", "scope": "singleton", "deps": [], "callbacks": []}]],
        [[{"name": "x", "scope": "singleton", "deps": ["q", "q"], "callbacks": ["initMethod"]},
          {"name": "q", "scope": "prototype", "deps": [], "callbacks": ["afterPropertiesSet", "destroy"]}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def lifecycle(beans):
    by_name = {b["name"]: b for b in beans}
    log, made = [], []
    def obtain(name):
        bean = by_name[name]
        if bean["scope"] == "singleton" and name in made:
            return
        for dep in bean["deps"]:
            obtain(dep)
        log.append(name + ":constructor")
        if bean["scope"] == "singleton":
            made.append(name)
        for cb in bean["callbacks"]:
            if cb in ("postConstruct", "afterPropertiesSet", "initMethod"):
                log.append(name + ":" + cb)
    for bean in beans:
        if bean["scope"] == "singleton":
            obtain(bean["name"])
    log.append("context:close")
    for name in reversed(made):
        for cb in by_name[name]["callbacks"]:
            if cb in ("preDestroy", "destroy", "destroyMethod"):
                log.append(name + ":" + cb)
    return log
''',
        '''INIT = ["postConstruct", "afterPropertiesSet", "initMethod"]
DESTROY = ["preDestroy", "destroy", "destroyMethod"]
def lifecycle(beans):
    by_name = {b["name"]: b for b in beans}
    log, made = [], []
    def obtain(name):
        bean = by_name[name]
        if bean["scope"] == "singleton" and name in made:
            return
        for dep in bean["deps"]:
            obtain(dep)
        log.append(name + ":constructor")
        made.append(name)
        for cb in INIT:
            if cb in bean["callbacks"]:
                log.append(name + ":" + cb)
    for bean in beans:
        if bean["scope"] == "singleton":
            obtain(bean["name"])
    log.append("context:close")
    for name in made:
        for cb in DESTROY:
            if cb in by_name[name]["callbacks"]:
                log.append(name + ":" + cb)
    return log
''',
    ],
    guide=dict(
        prereqs="Lesson: *Prototype scope and the bean lifecycle*. The creation-order problem.",
        intuition="Initialisation follows dependencies (what I need is ready before me); destruction is the mirror "
                  "image (I shut down before the things I rely on). Within one bean the three callback styles have a fixed order.",
        hints=[
            "Keep a list, not a set, of created singletons: its order is needed again at shutdown.",
            "Loop over the fixed order `postConstruct, afterPropertiesSet, initMethod` and test membership, rather than looping over the input list.",
            "Prototype instances are never remembered, so they cannot appear in the shutdown phase.",
        ],
        brute_force="Direct simulation is the intended solution.",
        approach=r"""
**Dry run:** `svc` (needs `pool`) is registered first. Obtain `svc` → obtain `pool` → `pool:constructor`,
`pool:initMethod` → `svc:constructor`, `svc:postConstruct`. Close → reverse order: `svc:preDestroy`, then
`pool:destroyMethod`.

```java
@Component
class ConnectionWarmer implements InitializingBean, DisposableBean {
    ConnectionWarmer() { }                         // 1. constructor (dependencies injected)

    @PostConstruct void warm() { }                 // 2. annotation callback
    @Override public void afterPropertiesSet() { } // 3. interface callback
    // 4. @Bean(initMethod = "start") custom method, if declared

    @PreDestroy void drain() { }                   // on close: annotation first
    @Override public void destroy() { }            // then the interface
    // then @Bean(destroyMethod = "stop")
}
```
""",
        complexity="Time O(instances × callbacks). Space O(number of singletons).",
        pitfalls="Emitting callbacks in the order they are listed in the input; destroying in creation order "
                 "instead of reverse; calling destroy callbacks on prototypes, which Spring never does because it does not track them.",
        follow_up="Where do `BeanPostProcessor.postProcessBeforeInitialization` and `…AfterInitialization` fit? (Around the three init callbacks; proxies are created in the 'after' step.)",
    ),
),
dict(
    id="spring-component-scan",
    title="Component scanning: which classes become beans?",
    difficulty="Easy",
    pattern="Spring container",
    entry="scan",
    description=r"""
`@ComponentScan` tells Spring which packages to search for annotated classes. Model that search.

`scan(base_packages, classes)`:

- `base_packages` — list of package names such as `"com.bookshop"`,
- `classes` — list of `[fully_qualified_class_name, [annotations]]`, for example
  `["com.bookshop.web.CartController", ["RestController"]]`.

A class becomes a bean when **both** hold:

1. its package is one of the base packages or a **sub-package** of one (`com.bookshop.web` is inside
   `com.bookshop`; `com.bookshopping` is not), and
2. it carries at least one stereotype annotation: `Component`, `Service`, `Repository`, `Controller`,
   `RestController` or `Configuration`.

The bean name is the simple class name with its first letter lower-cased, **except** when the first two characters
are both upper-case, in which case the name is left unchanged (`URLShortener` stays `URLShortener`).

Return the bean names sorted alphabetically (plain `sorted`).

**Example:** base `["com.bookshop"]`, classes `com.bookshop.web.CartController` (`RestController`) and
`com.other.Tool` (`Component`) → `["cartController"]`.
""",
    starter='''def scan(base_packages: list, classes: list) -> list:
    pass
''',
    solution='''STEREOTYPES = {"Component", "Service", "Repository", "Controller", "RestController", "Configuration"}


def scan(base_packages, classes):
    names = []
    for fqcn, annotations in classes:
        package, _, simple = fqcn.rpartition(".")
        inside = any(package == base or package.startswith(base + ".") for base in base_packages)
        if not inside or not STEREOTYPES.intersection(annotations):
            continue
        if len(simple) > 1 and simple[0].isupper() and simple[1].isupper():
            names.append(simple)
        else:
            names.append(simple[0].lower() + simple[1:])
    return sorted(names)
''',
    tests=[
        [["com.bookshop"], [["com.bookshop.web.CartController", ["RestController"]], ["com.other.Tool", ["Component"]]]],
        [["com.bookshop"], [["com.bookshop.BookshopApplication", ["SpringBootApplication"]], ["com.bookshop.Clock", ["Component"]]]],
        [["com.bookshop"], []],
        [[], [["com.bookshop.Clock", ["Component"]]]],
        [["com.bookshop"], [["com.bookshopping.Basket", ["Service"]], ["com.bookshop.Basket", ["Service"]]]],
        [["com.bookshop.web"], [["com.bookshop.Clock", ["Component"]], ["com.bookshop.web.api.v1.BookApi", ["Controller"]]]],
        [["com.bookshop"], [["com.bookshop.util.URLShortener", ["Component"]], ["com.bookshop.util.Xml", ["Component"]],
                            ["com.bookshop.util.X", ["Component"]]]],
        [["com.a", "org.b"], [["com.a.One", ["Service"]], ["org.b.c.Two", ["Repository"]], ["net.c.Three", ["Service"]]]],
        [["com.bookshop"], [["com.bookshop.model.Book", ["Entity"]], ["com.bookshop.model.BookDto", []],
                            ["com.bookshop.config.JdbcConfig", ["Configuration", "EnableScheduling"]]]],
        [["com.bookshop"], [["com.bookshop.b.Zeta", ["Service"]], ["com.bookshop.a.Alpha", ["Service"]],
                            ["com.bookshop.c.IOHelper", ["Component"]]]],
        [["com.bookshop.web"], [["com.bookshop.webhooks.Hook", ["Component"]], ["com.bookshop.web.Page", ["Controller"]]]],
        [["com"], [["com.Top", ["Component"]], ["company.Other", ["Component"]]]],
    ],
    examples=2,
    wrong_solutions=[
        '''S = {"Component", "Service", "Repository", "Controller", "RestController", "Configuration"}
def scan(base_packages, classes):
    names = []
    for fqcn, annotations in classes:
        simple = fqcn.rsplit(".", 1)[-1]
        if any(fqcn.startswith(b) for b in base_packages) and S.intersection(annotations):
            names.append(simple[0].lower() + simple[1:] if not (len(simple) > 1 and simple[1].isupper()) else simple)
    return sorted(names)
''',
        '''S = {"Component", "Service", "Repository", "Controller", "RestController", "Configuration"}
def scan(base_packages, classes):
    names = []
    for fqcn, annotations in classes:
        package, _, simple = fqcn.rpartition(".")
        if any(package == b or package.startswith(b + ".") for b in base_packages) and S.intersection(annotations):
            names.append(simple[0].lower() + simple[1:])
    return sorted(names)
''',
    ],
    guide=dict(
        prereqs="Lesson: *Stereotype annotations, component scanning and programmatic registration*. String methods.",
        intuition="Two filters and a rename. The package filter must respect dots: a sub-package starts with the "
                  "base package *followed by a dot*.",
        hints=[
            "Split the fully qualified name at the last dot to get package and simple name.",
            "`package == base or package.startswith(base + '.')` avoids matching `com.bookshopping`.",
            "The naming rule follows the JavaBeans convention: two leading capitals mean 'acronym, leave it alone'.",
        ],
        brute_force="The scan is linear already. A naive `startswith(base)` is the tempting shortcut and is wrong.",
        approach=r"""
**Dry run:** base `com.bookshop`; class `com.bookshop.util.URLShortener` with `Component`. Package
`com.bookshop.util` starts with `com.bookshop.` → inside. Stereotype present. First two letters `UR` are capitals →
name stays `URLShortener`.

```java
package com.bookshop;

@SpringBootApplication   // includes @ComponentScan of com.bookshop and everything beneath it
public class BookshopApplication {
    public static void main(String[] args) {
        SpringApplication.run(BookshopApplication.class, args);
    }
}
```

A class in `com.payments` would be ignored unless you add `@ComponentScan(basePackages = {"com.bookshop", "com.payments"})`.
""",
        complexity="Time O(C · B) for C classes and B base packages, plus O(C log C) to sort. Space O(C).",
        pitfalls="Prefix matching without the dot; forgetting that `@Entity` or a plain class is not a bean; "
                 "lower-casing `URLShortener` to `uRLShortener`.",
        follow_up="Add `excludeFilters` support, or meta-annotations (an annotation that is itself annotated with `@Component`).",
    ),
),
dict(
    id="spring-conditional-autoconfig",
    title="Auto-configuration: evaluate the conditions",
    difficulty="Medium",
    pattern="Spring Boot",
    entry="evaluate",
    description=r"""
Spring Boot's auto-configuration is a list of configuration classes, each guarded by **conditions**. Boot evaluates
them after your own beans are registered and adds a bean only when every condition passes.

`evaluate(configs, classpath, user_beans, properties)`:

- `configs` — ordered list of `{"name", "bean", "conditions"}`; `bean` is the bean name the configuration would add.
- `classpath` — list of class names present.
- `user_beans` — bean names the application defined itself.
- `properties` — dict of configuration properties (string values).

Conditions are checked left to right; the first failing one decides:

| condition | passes when |
|---|---|
| `["onClass", c]` | `c` is on the classpath |
| `["onMissingClass", c]` | `c` is not on the classpath |
| `["onBean", b]` | a bean named `b` is registered so far |
| `["onMissingBean", b]` | no bean named `b` is registered so far |
| `["onProperty", key, having, match_if_missing]` | key absent → `match_if_missing`. Key present and `having` is `None` → the value is anything except `"false"` (case-insensitive). Otherwise the value equals `having` (case-insensitive) |

"Registered so far" means the user beans plus beans added by earlier configurations in the list.

Return `{"beans": [...], "report": [...]}` where `beans` is user beans followed by auto-configured beans in the
order they were added, and `report` has one `[config_name, verdict]` pair per configuration: `"matched"` or the
failing condition written as `"<kind>:<first argument>"`, e.g. `"onMissingBean:dataSource"`.
""",
    starter='''def evaluate(configs: list, classpath: list, user_beans: list, properties: dict) -> dict:
    pass
''',
    solution='''def evaluate(configs, classpath, user_beans, properties):
    beans = list(user_beans)
    report = []

    def passes(cond):
        kind, arg = cond[0], cond[1]
        if kind == "onClass":
            return arg in classpath
        if kind == "onMissingClass":
            return arg not in classpath
        if kind == "onBean":
            return arg in beans
        if kind == "onMissingBean":
            return arg not in beans
        having, match_if_missing = cond[2], cond[3]
        if arg not in properties:
            return match_if_missing
        value = properties[arg].lower()
        if having is None:
            return value != "false"
        return value == having.lower()

    for config in configs:
        verdict = "matched"
        for cond in config["conditions"]:
            if not passes(cond):
                verdict = cond[0] + ":" + cond[1]
                break
        if verdict == "matched":
            beans.append(config["bean"])
        report.append([config["name"], verdict])
    return {"beans": beans, "report": report}
''',
    tests=[
        [_AUTO, _CP, [], {}],
        [_AUTO, _CP, ["dataSource"], {"shop.cache.enabled": "true"}],
        [_AUTO, [], [], {}],
        [[], _CP, ["x"], {}],
        [_AUTO, _CP, ["jdbcTemplate", "cacheManager"], {"shop.cache.enabled": "TRUE", "shop.metrics.enabled": "False"}],
        [_AUTO, _CP, [], {"shop.cache.enabled": "yes", "shop.mail.transport": "SMTP"}],
        [_AUTO, _CP + ["com.fake.NoMail"], [], {"shop.mail.transport": "smtp"}],
        [_AUTO, ["javax.sql.DataSource"], [], {"shop.cache.enabled": "false", "shop.mail.transport": "imap"}],
        [_AUTO[1:], _CP, [], {}],
        [list(reversed(_AUTO)), _CP, [], {"shop.metrics.enabled": "0"}],
        [[{"name": "A", "bean": "a", "conditions": []}, {"name": "B", "bean": "b", "conditions": [["onBean", "a"]]},
          {"name": "A2", "bean": "a", "conditions": [["onMissingBean", "a"]]}], [], [], {}],
        [[{"name": "P", "bean": "p", "conditions": [["onProperty", "k", "on", True], ["onClass", "Z"]]}], ["Z"], [], {"k": "off"}],
    ],
    examples=2,
    wrong_solutions=[
        '''def evaluate(configs, classpath, user_beans, properties):
    beans = list(user_beans)
    report = []
    def passes(cond):
        kind, arg = cond[0], cond[1]
        if kind == "onClass": return arg in classpath
        if kind == "onMissingClass": return arg not in classpath
        if kind == "onBean": return arg in user_beans
        if kind == "onMissingBean": return arg not in user_beans
        if arg not in properties: return cond[3]
        v = properties[arg].lower()
        return v != "false" if cond[2] is None else v == cond[2].lower()
    for c in configs:
        verdict = "matched"
        for cond in c["conditions"]:
            if not passes(cond):
                verdict = cond[0] + ":" + cond[1]; break
        if verdict == "matched": beans.append(c["bean"])
        report.append([c["name"], verdict])
    return {"beans": beans, "report": report}
''',
        '''def evaluate(configs, classpath, user_beans, properties):
    beans = list(user_beans)
    report = []
    def passes(cond):
        kind, arg = cond[0], cond[1]
        if kind == "onClass": return arg in classpath
        if kind == "onMissingClass": return arg not in classpath
        if kind == "onBean": return arg in beans
        if kind == "onMissingBean": return arg not in beans
        if arg not in properties: return False
        v = properties[arg]
        return v == "true" if cond[2] is None else v == cond[2]
    for c in configs:
        verdict = "matched"
        for cond in c["conditions"]:
            if not passes(cond):
                verdict = cond[0] + ":" + cond[1]; break
        if verdict == "matched": beans.append(c["bean"])
        report.append([c["name"], verdict])
    return {"beans": beans, "report": report}
''',
    ],
    guide=dict(
        prereqs="Lesson: *Spring Boot: starters and auto-configuration*.",
        intuition="Auto-configuration is 'if nobody has supplied this already and the library is present, I will'. "
                  "Each condition is a yes/no question about the classpath, the bean registry or the properties.",
        hints=[
            "Keep one growing list of registered bean names, seeded with the user's beans.",
            "Write a helper that answers one condition; the loop then only needs to find the first `False`.",
            "For `onProperty` handle 'key absent' first; only then look at `having`.",
        ],
        brute_force="A straight loop is the solution. The care is in `onProperty` and in using the *growing* bean list.",
        approach=r"""
**Dry run** with the user defining `dataSource`: `DataSourceAutoConfiguration` passes `onClass` but fails
`onMissingBean:dataSource` — Boot backs off. `JdbcTemplateAutoConfiguration` then passes `onBean dataSource`
(the user's bean) and adds `jdbcTemplate`.

```java
@AutoConfiguration
@ConditionalOnClass(DataSource.class)
public class ShopDataSourceAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean                      // back off if the application declares its own
    @ConditionalOnProperty(name = "shop.db.enabled", matchIfMissing = true)
    DataSource dataSource() {
        return new HikariDataSource();
    }
}
```

Run any Boot app with `--debug` to print the real "CONDITIONS EVALUATION REPORT".
""",
        complexity="Time O(total conditions × lookup cost). Using sets for the classpath and beans makes each lookup O(1).",
        pitfalls="Checking bean conditions against only the user's beans misses chains such as JdbcTemplate needing "
                 "the auto-configured DataSource. `havingValue` unset does not mean 'must be true': any value except `false` passes.",
        follow_up="Real Boot orders configurations with `@AutoConfigureAfter`/`@AutoConfigureBefore`. Add a topological sort in front.",
    ),
),
]
