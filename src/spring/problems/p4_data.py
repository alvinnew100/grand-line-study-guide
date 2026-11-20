def _n(name, propagation, fails=False, caught=False, calls=()):
    return {"name": name, "propagation": propagation, "fails": fails, "caught": caught, "calls": list(calls)}


_EX = {
    "Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception",
    "IOException": "Exception", "FileNotFoundException": "IOException", "SQLException": "Exception",
    "IllegalStateException": "RuntimeException", "ShopException": "RuntimeException",
    "OutOfStockException": "ShopException", "PaymentException": "Exception",
    "CardDeclinedException": "PaymentException", "OutOfMemoryError": "Error",
}

_BOOKS = [
    {"id": 1, "title": "Dune", "author": "Herbert", "price": 12, "inStock": True, "genre": "scifi", "isbn": "111"},
    {"id": 2, "title": "Emma", "author": "Austen", "price": 8, "inStock": False, "genre": "classic", "isbn": None},
    {"id": 3, "title": "Dracula", "author": "Stoker", "price": 8, "inStock": True, "genre": "horror", "isbn": "333"},
    {"id": 4, "title": "Persuasion", "author": "Austen", "price": 9, "inStock": True, "genre": "classic", "isbn": "444"},
    {"id": 5, "title": "Neuromancer", "author": "Gibson", "price": 15, "inStock": False, "genre": "scifi", "isbn": None},
    {"id": 6, "title": "dune messiah", "author": "herbert", "price": 11, "inStock": True, "genre": "scifi", "isbn": "666"},
]

_ITEMS = [{"id": i, "genre": ["scifi", "classic", "horror"][i % 3], "price": (i * 7) % 5} for i in range(1, 12)]

PROBLEMS = [
dict(
    id="spring-tx-propagation",
    title="Transaction propagation over a call tree",
    difficulty="Hard",
    pattern="Transactions",
    entry="run",
    description=r"""
Every `@Transactional` method declares a **propagation**: what to do about a transaction that may already be
running. Simulate a tree of calls and report which rows end up in the database.

`run(root)` receives a node `{"name", "propagation", "fails", "caught", "calls"}`:

- When a method's body runs it first **writes one row** named after the method, then calls each node in `calls`
  in order, and finally throws `RuntimeException` if `fails` is true.
- `caught` (ignored on the root) says the *caller* wraps this call in try/catch and carries on. Uncaught
  exceptions travel up to the caller's caller.
- A write made inside a transaction becomes permanent only if that transaction commits. A write made with no
  transaction is permanent immediately (auto-commit).

Propagation, with *T* = the transaction active in the caller (possibly none):

| value | T exists | no T |
|---|---|---|
| `REQUIRED` | join T | start a new transaction |
| `SUPPORTS` | join T | run without a transaction |
| `MANDATORY` | join T | throw `IllegalTransactionStateException` before the body |
| `REQUIRES_NEW` | suspend T, start an independent new transaction | start a new transaction |
| `NOT_SUPPORTED` | suspend T, run without a transaction | run without a transaction |
| `NEVER` | throw `IllegalTransactionStateException` before the body | run without a transaction |
| `NESTED` | take a savepoint in T | start a new transaction |

Boundaries:

- **A method that started a transaction**: if an exception leaves its body, the transaction rolls back and the
  exception continues upward. Otherwise it commits — unless the transaction was marked *rollback-only*, in which
  case it rolls back and the method throws `UnexpectedRollbackException` to its caller.
- **A method that joined T**: if an exception leaves its body, T is marked rollback-only and the exception
  continues upward (even if the caller then catches it, T is doomed).
- **NESTED with a savepoint**: if an exception leaves the body, every row T gained since the savepoint is removed,
  the rollback-only mark is restored to what it was at the savepoint, and the exception continues upward.

Return `{"rows": [...], "error": ...}`: the permanent rows in the order they were written, and the name of the
exception that escapes the root (`None` if none).

**Example:** `checkout` (REQUIRED) calls `audit` (REQUIRES_NEW), then fails →
`{"rows": ["audit"], "error": "RuntimeException"}`.
""",
    starter='''def run(root: dict) -> dict:
    pass
''',
    solution='''class _Failure(Exception):
    pass


class _Tx:
    def __init__(self):
        self.rows = []
        self.rollback_only = False


def run(root):
    permanent = []
    clock = [0]

    def write(name, tx):
        clock[0] += 1
        (tx.rows if tx else permanent).append((clock[0], name))

    def body(node, tx):
        write(node["name"], tx)
        for child in node["calls"]:
            try:
                call(child, tx)
            except _Failure:
                if not child["caught"]:
                    raise
        if node["fails"]:
            raise _Failure("RuntimeException")

    def in_new_tx(node):
        tx = _Tx()
        body(node, tx)                      # an exception here discards tx.rows
        if tx.rollback_only:
            raise _Failure("UnexpectedRollbackException")
        permanent.extend(tx.rows)

    def joined(node, tx):
        try:
            body(node, tx)
        except _Failure:
            tx.rollback_only = True
            raise

    def call(node, tx):
        mode = node["propagation"]
        if mode == "REQUIRES_NEW" or (tx is None and mode in ("REQUIRED", "NESTED")):
            in_new_tx(node)
        elif mode == "MANDATORY" and tx is None:
            raise _Failure("IllegalTransactionStateException")
        elif mode == "NEVER" and tx is not None:
            raise _Failure("IllegalTransactionStateException")
        elif mode == "NOT_SUPPORTED" or mode == "NEVER" or (mode == "SUPPORTS" and tx is None):
            body(node, None)
        elif mode == "NESTED":
            mark, flag = len(tx.rows), tx.rollback_only
            try:
                body(node, tx)
            except _Failure:
                del tx.rows[mark:]
                tx.rollback_only = flag
                raise
        else:
            joined(node, tx)

    error = None
    try:
        call(root, None)
    except _Failure as failure:
        error = str(failure)
    return {"rows": [name for _, name in sorted(permanent)], "error": error}
''',
    tests=[
        [_n("checkout", "REQUIRED", fails=True, calls=[_n("audit", "REQUIRES_NEW")])],
        [_n("checkout", "REQUIRED", calls=[_n("stock", "REQUIRED"), _n("invoice", "REQUIRED")])],
        [_n("checkout", "REQUIRED", calls=[_n("stock", "REQUIRED", fails=True, caught=True), _n("invoice", "REQUIRED")])],
        [_n("checkout", "REQUIRED", calls=[_n("stock", "NESTED", fails=True, caught=True), _n("invoice", "REQUIRED")])],
        [_n("checkout", "REQUIRED", calls=[_n("email", "REQUIRES_NEW", fails=True, caught=True), _n("invoice", "REQUIRED")])],
        [_n("checkout", "REQUIRED", calls=[_n("email", "REQUIRES_NEW", fails=True)])],
        [_n("report", "SUPPORTS", fails=True, calls=[_n("line", "SUPPORTS")])],
        [_n("report", "MANDATORY")],
        [_n("job", "NOT_SUPPORTED", calls=[_n("a", "MANDATORY", caught=True), _n("b", "REQUIRED"), _n("c", "NEVER")])],
        [_n("checkout", "REQUIRED", calls=[_n("legacy", "NEVER", caught=True), _n("invoice", "MANDATORY")])],
        [_n("checkout", "REQUIRED", fails=True, calls=[_n("log", "NOT_SUPPORTED"), _n("stock", "SUPPORTS")])],
        [_n("checkout", "NESTED", calls=[_n("stock", "NESTED", calls=[_n("deep", "REQUIRED", fails=True, caught=True)]),
                                         _n("invoice", "REQUIRED")])],
        [_n("checkout", "REQUIRED", calls=[
            _n("stock", "NESTED", fails=True, caught=True, calls=[_n("deep", "REQUIRED", fails=True, caught=True),
                                                                 _n("sideAudit", "REQUIRES_NEW")]),
            _n("invoice", "REQUIRED")])],
        [_n("batch", "NEVER", calls=[_n("one", "REQUIRED"), _n("two", "REQUIRED", fails=True, caught=True),
                                     _n("three", "REQUIRES_NEW", calls=[_n("inner", "REQUIRED", fails=True, caught=True)], caught=True),
                                     _n("four", "SUPPORTS")])],
        [_n("outer", "REQUIRED", calls=[_n("mid", "REQUIRES_NEW", caught=True, calls=[
            _n("leaf", "MANDATORY", fails=True, caught=True)]), _n("tail", "REQUIRED")])],
    ],
    examples=2,
    wrong_solutions=[
        '''class F(Exception): pass
def run(root):
    perm = []
    def body(node, tx):
        (tx if tx is not None else perm).append(node["name"])
        for c in node["calls"]:
            try: call(c, tx)
            except F:
                if not c["caught"]: raise
        if node["fails"]: raise F("RuntimeException")
    def new(node):
        tx = []
        body(node, tx)
        perm.extend(tx)
    def call(node, tx):
        m = node["propagation"]
        if m == "REQUIRES_NEW" or (tx is None and m in ("REQUIRED", "NESTED")): new(node)
        elif m == "MANDATORY" and tx is None: raise F("IllegalTransactionStateException")
        elif m == "NEVER" and tx is not None: raise F("IllegalTransactionStateException")
        elif m in ("NOT_SUPPORTED", "NEVER") or (m == "SUPPORTS" and tx is None): body(node, None)
        elif m == "NESTED":
            mark = len(tx)
            try: body(node, tx)
            except F:
                del tx[mark:]; raise
        else: body(node, tx)
    err = None
    try: call(root, None)
    except F as f: err = str(f)
    return {"rows": perm, "error": err}
''',
        '''class F(Exception): pass
def run(root):
    perm = []
    def body(node, tx):
        tx.append(node["name"])
        for c in node["calls"]:
            try: body(c, tx)
            except F:
                if not c["caught"]: raise
        if node["fails"]: raise F("RuntimeException")
    tx = []
    try:
        body(root, tx)
    except F as f:
        return {"rows": [], "error": str(f)}
    return {"rows": tx, "error": None}
''',
    ],
    guide=dict(
        prereqs="Lessons: *@Transactional, rollback rules and the self-invocation pitfall* and *Propagation and isolation*. Python exceptions and recursion.",
        intuition="Separate two things: the *physical* transaction (a bag of uncommitted rows with a rollback-only "
                  "flag) and the *methods* that either own it, borrow it, or stay out of it. Only the owner commits "
                  "or rolls back; a borrower that fails can merely poison the bag.",
        hints=[
            "Model a transaction as an object with `rows` and `rollback_only`. Pass it (or `None`) down the recursion.",
            "Write three helpers: run in a new transaction, run joined, run without one. `call` only chooses among them.",
            "Global write order across independent transactions is easiest with a counter attached to every row; sort at the end.",
        ],
        brute_force="Treat the whole tree as one transaction: everything commits or nothing does. It is right for "
                    "all-REQUIRED trees with no caught exceptions and wrong for everything interesting.",
        approach=r"""
**Dry run** of the classic surprise: `checkout` (REQUIRED) calls `stock` (REQUIRED, fails, **caught**), then
`invoice`. `checkout` starts T and writes. `stock` joins, writes, throws: T is marked rollback-only; `checkout`
catches and continues; `invoice` writes. `checkout` returns normally, tries to commit, finds the mark →
everything rolls back and the caller receives `UnexpectedRollbackException`. Rows: none.

Change `stock` to `NESTED` and its row alone is undone; `checkout` and `invoice` commit. Change it to
`REQUIRES_NEW` and it has its own transaction that rolls back alone.

```java
@Service
class CheckoutService {
    @Transactional                                   // REQUIRED is the default
    public void checkout(Order o) {
        orders.save(o);
        try {
            stockService.reserve(o);                 // @Transactional -> joins; failure dooms the outer tx
        } catch (OutOfStockException e) { /* too late */ }
        auditService.record(o);                      // @Transactional(propagation = Propagation.REQUIRES_NEW)
    }
}
```
""",
        complexity="Time and space O(number of nodes).",
        pitfalls="Believing that catching an exception saves a joined transaction; committing rows of a new "
                 "transaction at the moment of writing instead of at its boundary; letting `MANDATORY`/`NEVER` write before throwing; "
                 "marking the outer transaction rollback-only for a `NESTED` or `REQUIRES_NEW` failure.",
        follow_up="Add `noRollbackFor`, or a checked exception that commits (see the rollback-rules problem).",
    ),
),
dict(
    id="spring-rollback-rules",
    title="Rollback rules: checked versus unchecked",
    difficulty="Easy",
    pattern="Transactions",
    entry="decide",
    description=r"""
When an exception leaves a `@Transactional` method, Spring must decide between rollback and commit.

`decide(parents, thrown, rollback_for, no_rollback_for)`:

- `parents` — dict `class -> parent` describing the exception hierarchy (root `Throwable` has parent `None`),
- `thrown` — the exception class, or `None` if the method returned normally,
- `rollback_for`, `no_rollback_for` — lists of classes from the annotation's attributes.

Rules:

1. `thrown` is `None` → `"COMMIT"`.
2. A rule *applies* if its class is `thrown` or one of its ancestors. Its **distance** is the number of steps up
   (0 for the class itself). Among all applying rules from both lists, the one with the smallest distance wins:
   from `rollback_for` → `"ROLLBACK"`, from `no_rollback_for` → `"COMMIT"`. If the smallest distance is shared by
   a rule of each kind, rollback wins.
3. No rule applies → the default: `"ROLLBACK"` when `thrown` is `RuntimeException`, `Error`, or a descendant of
   either (the *unchecked* exceptions); `"COMMIT"` for everything else (the *checked* exceptions).

**Example:** throwing `IOException` with empty lists → `"COMMIT"` (checked). With
`rollback_for = ["Exception"]` → `"ROLLBACK"`.
""",
    starter='''def decide(parents: dict, thrown, rollback_for: list, no_rollback_for: list) -> str:
    pass
''',
    solution='''def decide(parents, thrown, rollback_for, no_rollback_for):
    if thrown is None:
        return "COMMIT"
    distance, current, steps = {}, thrown, 0
    while current is not None:
        distance[current] = steps
        current = parents.get(current)
        steps += 1
    best = None
    for cls in rollback_for:
        if cls in distance and (best is None or distance[cls] < best[0]):
            best = (distance[cls], "ROLLBACK")
    for cls in no_rollback_for:
        if cls in distance and (best is None or distance[cls] < best[0]):
            best = (distance[cls], "COMMIT")
    if best:
        return best[1]
    return "ROLLBACK" if "RuntimeException" in distance or "Error" in distance else "COMMIT"
''',
    tests=[
        [_EX, "IOException", [], []],
        [_EX, "IOException", ["Exception"], []],
        [_EX, None, ["Exception"], []],
        [_EX, "IllegalStateException", [], []],
        [_EX, "OutOfMemoryError", [], []],
        [_EX, "OutOfStockException", [], ["ShopException"]],
        [_EX, "OutOfStockException", ["OutOfStockException"], ["ShopException"]],
        [_EX, "OutOfStockException", ["RuntimeException"], ["ShopException"]],
        [_EX, "CardDeclinedException", ["PaymentException"], ["CardDeclinedException"]],
        [_EX, "CardDeclinedException", ["CardDeclinedException"], ["CardDeclinedException"]],
        [_EX, "FileNotFoundException", ["SQLException"], ["IllegalStateException"]],
        [_EX, "RuntimeException", [], ["Exception"]],
        [_EX, "Exception", [], []],
        [_EX, "IllegalStateException", ["Throwable"], ["Exception", "RuntimeException"]],
        [_EX, "Throwable", [], []],
    ],
    examples=2,
    wrong_solutions=[
        '''def decide(parents, thrown, rollback_for, no_rollback_for):
    if thrown is None:
        return "COMMIT"
    line, c = [], thrown
    while c is not None:
        line.append(c); c = parents.get(c)
    if any(c in line for c in no_rollback_for):
        return "COMMIT"
    if any(c in line for c in rollback_for):
        return "ROLLBACK"
    return "ROLLBACK" if "RuntimeException" in line or "Error" in line else "COMMIT"
''',
        '''def decide(parents, thrown, rollback_for, no_rollback_for):
    if thrown is None:
        return "COMMIT"
    line, c = [], thrown
    while c is not None:
        line.append(c); c = parents.get(c)
    if any(c in line for c in rollback_for):
        return "ROLLBACK"
    if any(c in line for c in no_rollback_for):
        return "COMMIT"
    return "ROLLBACK" if "Exception" in line or "Error" in line else "COMMIT"
''',
        '''def decide(parents, thrown, rollback_for, no_rollback_for):
    if thrown is None:
        return "COMMIT"
    if thrown in rollback_for:
        return "ROLLBACK"
    if thrown in no_rollback_for:
        return "COMMIT"
    line, c = [], thrown
    while c is not None:
        line.append(c); c = parents.get(c)
    return "ROLLBACK" if "RuntimeException" in line or "Error" in line else "COMMIT"
''',
    ],
    guide=dict(
        prereqs="Checked and unchecked exceptions (Java track). Lesson: *@Transactional, rollback rules and the self-invocation pitfall*.",
        intuition="The default follows an old convention: an unchecked exception signals a bug or an unrecoverable "
                  "state, a checked exception is an expected business outcome. Explicit rules override that default, "
                  "and the most specific rule is the one nearest to the thrown class.",
        hints=[
            "Compute `class -> distance` for the thrown class and all its ancestors in one walk.",
            "Scan `rollback_for` first and replace the best only on a *strictly* smaller distance; ties then favour rollback.",
            "The default needs the same ancestor map: is `RuntimeException` or `Error` in it?",
        ],
        brute_force="Check `no_rollback_for` then `rollback_for` with simple membership. It ignores distance and "
                    "fails whenever both lists contain ancestors of the thrown class.",
        approach=r"""
**Dry run:** `OutOfStockException → ShopException → RuntimeException → Exception → Throwable`, with
`rollback_for = [RuntimeException]` (distance 2) and `no_rollback_for = [ShopException]` (distance 1).
Distance 1 wins → `COMMIT`, although the exception is unchecked.

```java
@Transactional(rollbackFor = Exception.class)            // also roll back for checked exceptions
public void importCatalogue(Path file) throws IOException { ... }

@Transactional(noRollbackFor = OutOfStockException.class) // keep the order row, mark it BACKORDERED
public void placeOrder(Order order) { ... }
```
""",
        complexity="Time O(D + R) for hierarchy depth D and R rules. Space O(D).",
        pitfalls="Assuming every exception rolls back (checked ones commit by default, the number-one "
                 "`@Transactional` surprise); giving one list blanket priority over the other; forgetting `Error`.",
        follow_up="An exception that is caught inside the method never reaches the proxy. What does the transaction do then?",
    ),
),
dict(
    id="spring-isolation-anomaly",
    title="Spot the isolation anomalies in a schedule",
    difficulty="Hard",
    pattern="Transactions",
    entry="anomalies",
    description=r"""
Two or more transactions run at the same time; their operations interleave in a **schedule**. Decide which read
anomalies the schedule contains.

`anomalies(schedule)` receives a list of steps, each a list:

- `[tx, "read", key]`, `[tx, "write", key]` — read or update one row,
- `[tx, "scan", prefix]` — a range query returning every row whose key starts with `prefix`,
- `[tx, "insert", key]` — add a new row,
- `[tx, "commit"]`, `[tx, "rollback"]` — finish the transaction.

Let positions be indexes in the list, and A, B two **different** transactions. The schedule contains:

- **dirty read** — A reads `k` at position *i*, and B wrote or inserted `k` at some *j < i* without B committing
  or rolling back between *j* and *i*.
- **non-repeatable read** — A reads `k` at *i*; B writes `k` at *j > i*; B commits at *c > j*; A reads `k` again
  at *m > c*.
- **phantom read** — A scans prefix `p` at *i*; B inserts a key starting with `p` at *j > i*; B commits at
  *c > j*; A scans `p` again at *m > c*.
- **lost update** — A reads `k` at *i*; B writes `k` at *j > i*; B commits at *c > j*; A writes `k` at *m > c*
  **without** A reading `k` anywhere between *c* and *m*.

Return the names of the anomalies present, sorted alphabetically (each at most once).

**Example:** `[["T1","write","stock"], ["T2","read","stock"], ["T1","rollback"]]` → `["dirty read"]`.
""",
    starter='''def anomalies(schedule: list) -> list:
    pass
''',
    solution='''def anomalies(schedule):
    found = set()
    n = len(schedule)

    def finished_between(tx, lo, hi):
        return any(schedule[x][0] == tx and schedule[x][1] in ("commit", "rollback") for x in range(lo + 1, hi))

    def commit_after(tx, pos):
        for x in range(pos + 1, n):
            if schedule[x][0] == tx and schedule[x][1] == "commit":
                return x
            if schedule[x][0] == tx and schedule[x][1] == "rollback":
                return None
        return None

    for i, step in enumerate(schedule):
        a, op = step[0], step[1]
        if op == "read":
            key = step[2]
            for j in range(i):
                b, bop = schedule[j][0], schedule[j][1]
                if b != a and bop in ("write", "insert") and schedule[j][2] == key and not finished_between(b, j, i):
                    found.add("dirty read")
            for j in range(i + 1, n):
                b, bop = schedule[j][0], schedule[j][1]
                if b == a or bop != "write" or schedule[j][2] != key:
                    continue
                c = commit_after(b, j)
                if c is None:
                    continue
                for m in range(c + 1, n):
                    if schedule[m][0] != a or len(schedule[m]) < 3 or schedule[m][2] != key:
                        continue
                    if schedule[m][1] == "read":
                        found.add("non-repeatable read")
                    if schedule[m][1] == "write":
                        reread = any(schedule[x][0] == a and schedule[x][1] == "read" and schedule[x][2] == key
                                     for x in range(c + 1, m))
                        if not reread:
                            found.add("lost update")
        if op == "scan":
            prefix = step[2]
            for j in range(i + 1, n):
                b, bop = schedule[j][0], schedule[j][1]
                if b == a or bop != "insert" or not schedule[j][2].startswith(prefix):
                    continue
                c = commit_after(b, j)
                if c is None:
                    continue
                if any(schedule[m][0] == a and schedule[m][1] == "scan" and schedule[m][2] == prefix
                       for m in range(c + 1, n)):
                    found.add("phantom read")
    return sorted(found)
''',
    tests=[
        [[["T1", "write", "stock"], ["T2", "read", "stock"], ["T1", "rollback"]]],
        [[["T1", "read", "stock"], ["T2", "write", "stock"], ["T2", "commit"], ["T1", "read", "stock"], ["T1", "commit"]]],
        [[]],
        [[["T1", "read", "a"], ["T1", "write", "a"], ["T1", "commit"], ["T2", "read", "a"], ["T2", "commit"]]],
        [[["T1", "scan", "order:"], ["T2", "insert", "order:9"], ["T2", "commit"], ["T1", "scan", "order:"], ["T1", "commit"]]],
        [[["T1", "scan", "order:"], ["T2", "insert", "book:9"], ["T2", "commit"], ["T1", "scan", "order:"]]],
        [[["T1", "read", "stock"], ["T2", "read", "stock"], ["T2", "write", "stock"], ["T2", "commit"],
          ["T1", "write", "stock"], ["T1", "commit"]]],
        [[["T1", "read", "stock"], ["T2", "write", "stock"], ["T2", "commit"], ["T1", "read", "stock"],
          ["T1", "write", "stock"], ["T1", "commit"]]],
        [[["T1", "write", "a"], ["T1", "commit"], ["T2", "read", "a"]]],
        [[["T1", "read", "a"], ["T2", "write", "a"], ["T2", "rollback"], ["T1", "read", "a"]]],
        [[["T1", "read", "a"], ["T2", "write", "a"], ["T1", "read", "a"], ["T2", "commit"]]],
        [[["T1", "write", "a"], ["T1", "read", "a"], ["T1", "commit"]]],
        [[["T1", "scan", "o:"], ["T1", "read", "a"], ["T2", "insert", "o:1"], ["T3", "write", "a"], ["T3", "read", "o:1"],
          ["T2", "commit"], ["T3", "commit"], ["T1", "scan", "o:"], ["T1", "write", "a"], ["T1", "read", "a"]]],
        [[["T1", "read", "a"], ["T2", "write", "b"], ["T2", "commit"], ["T1", "read", "a"], ["T1", "write", "b"]]],
        [[["T2", "insert", "o:1"], ["T1", "scan", "o:"], ["T2", "commit"], ["T1", "scan", "o:"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def anomalies(schedule):
    found = set()
    for i, s in enumerate(schedule):
        if s[1] == "read":
            for j in range(i):
                t = schedule[j]
                if t[0] != s[0] and t[1] in ("write", "insert") and t[2] == s[2]:
                    found.add("dirty read")
            for j in range(i + 1, len(schedule)):
                t = schedule[j]
                if t[0] != s[0] and t[1] == "write" and t[2] == s[2]:
                    for m in range(j + 1, len(schedule)):
                        u = schedule[m]
                        if u[0] == s[0] and u[1] == "read" and u[2] == s[2]:
                            found.add("non-repeatable read")
                        if u[0] == s[0] and u[1] == "write" and u[2] == s[2]:
                            found.add("lost update")
        if s[1] == "scan":
            for j in range(i + 1, len(schedule)):
                t = schedule[j]
                if t[0] != s[0] and t[1] == "insert" and t[2].startswith(s[2]):
                    if any(u[0] == s[0] and u[1] == "scan" and u[2] == s[2] for u in schedule[j + 1:]):
                        found.add("phantom read")
    return sorted(found)
''',
    ],
    guide=dict(
        prereqs="Lesson: *Propagation and isolation*. Nested loops over a list with indexes.",
        intuition="Each anomaly is a fixed pattern of 'A did this, B did that in between, A looked again'. The "
                  "definitions are already algorithms; the work is translating 'between' and 'committed' into index checks.",
        hints=[
            "Write two helpers: 'did transaction X finish between positions lo and hi?' and 'where does X commit after position j (if it does)?'.",
            "Drive everything from A's first `read` (three anomalies start there) and A's first `scan`.",
            "A rolled-back writer can cause a dirty read but never the other three, which all need B's commit.",
        ],
        brute_force="The definitions give an O(n³)–O(n⁴) scan directly, which is fine for schedules of a few dozen steps.",
        approach=r"""
**Dry run** of the lost update: T1 reads `stock` (say 5). T2 reads 5, writes 4, commits. T1 writes 4 (computed
from its stale 5). Pattern: A read at 0, B write at 2, B commit at 3, A write at 4 with no re-read between 3 and
4 → `lost update`. No second read by T1, so it is not a non-repeatable read.

Which isolation level prevents what (SQL standard):

| level | dirty read | non-repeatable read | phantom read |
|---|---|---|---|
| READ_UNCOMMITTED | possible | possible | possible |
| READ_COMMITTED | prevented | possible | possible |
| REPEATABLE_READ | prevented | prevented | possible |
| SERIALIZABLE | prevented | prevented | prevented |

```java
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void reserve(long bookId, int quantity) {
    int stock = repository.readStock(bookId);
    repository.writeStock(bookId, stock - quantity);
}
```
""",
        complexity="Time O(n³) in the worst case with these loops; space O(1) beyond the result.",
        pitfalls="Calling a read after the writer **committed** a dirty read; ignoring that a rollback ends the "
                 "writer; requiring a second read for the lost update; matching inserts whose key does not start with the scanned prefix.",
        follow_up="Add *write skew*: two transactions read overlapping data and write disjoint rows based on it.",
    ),
),
dict(
    id="spring-derived-query",
    title="Derived queries: from method name to filter",
    difficulty="Hard",
    pattern="Spring Data",
    entry="run_query",
    description=r"""
Spring Data builds a query from a repository **method name** such as `findByAuthorAndPriceLessThanOrderByTitleAsc`.
Write the translator and run the result against a list of rows.

`run_query(method, args, rows)` — `rows` is a list of dicts, `args` the method arguments in order.

**Grammar**

```
<subject>By<predicate>[OrderBy<ordering>]
```

- Subject: `find` (return matching rows), `count` (return how many), `exists` (return a boolean). `find` may be
  followed by `First` or `Top` and an optional number (`findFirstBy`, `findTop3By`), limiting the rows returned
  after sorting; no number means 1.
- Predicate: conditions joined by `And` / `Or`. Split on `Or` first, then each part on `And`, so `And` binds
  tighter. Only split where the keyword is followed by an upper-case letter. The predicate may be empty
  (`findByOrderByPriceAsc` selects everything).
- Condition: a property name optionally followed by one keyword. The row field is the property with its first
  letter lower-cased (`InStock` → `inStock`).

| keyword | arguments | true when |
|---|---|---|
| *(none)* | 1 | field == arg |
| `Not` | 1 | field != arg |
| `GreaterThan`, `GreaterThanEqual`, `LessThan`, `LessThanEqual` | 1 | field compared with arg |
| `Between` | 2 | low <= field <= high |
| `StartingWith`, `Containing` | 1 | string test |
| `In` | 1 (a list) | field is in the list |
| `IgnoreCase` | 1 | equal ignoring case |
| `IsNull`, `IsNotNull` | 0 | field is / is not `None` |
| `True`, `False` | 0 | field is `True` / `False` |

  A field holding `None` makes every keyword false except `IsNull` (and plain equality/`Not` compare normally).
  Arguments are consumed left to right.
- Ordering: one or more `<Property>Asc` / `<Property>Desc` written one after another; earlier ones are more
  significant. Without an ordering, keep the input order. Sorting is stable.

**Example:** `run_query("findByAuthorAndPriceLessThanOrderByTitleAsc", ["Austen", 9], books)` returns the Austen
books cheaper than 9, by title.
""",
    starter='''def run_query(method: str, args: list, rows: list):
    pass
''',
    solution='''import re

_KEYWORDS = ["IsNotNull", "IsNull", "GreaterThanEqual", "GreaterThan", "LessThanEqual", "LessThan", "Between",
             "StartingWith", "Containing", "IgnoreCase", "Not", "In", "True", "False"]
_ARITY = {"IsNotNull": 0, "IsNull": 0, "True": 0, "False": 0, "Between": 2}


def _field(prop):
    return prop[0].lower() + prop[1:]


def _test(keyword, value, a):
    if keyword == "IsNull":
        return value is None
    if keyword == "IsNotNull":
        return value is not None
    if keyword == "":
        return value == a[0]
    if keyword == "Not":
        return value != a[0]
    if value is None:
        return False
    if keyword == "True":
        return value is True
    if keyword == "False":
        return value is False
    if keyword == "GreaterThan":
        return value > a[0]
    if keyword == "GreaterThanEqual":
        return value >= a[0]
    if keyword == "LessThan":
        return value < a[0]
    if keyword == "LessThanEqual":
        return value <= a[0]
    if keyword == "Between":
        return a[0] <= value <= a[1]
    if keyword == "StartingWith":
        return value.startswith(a[0])
    if keyword == "Containing":
        return a[0] in value
    if keyword == "IgnoreCase":
        return value.lower() == a[0].lower()
    return value in a[0]


def run_query(method, args, rows):
    m = re.match(r"(find|count|exists)(?:(?:First|Top)([0-9]*))?By(.*)\\Z", method)
    subject, rest = m.group(1), m.group(3)
    limit = None
    if m.group(2) is not None:
        limit = int(m.group(2)) if m.group(2) else 1
    predicate, _, ordering = rest.partition("OrderBy")
    position = 0
    groups = []
    if predicate:
        for or_part in re.split(r"Or(?=[A-Z])", predicate):
            conditions = []
            for part in re.split(r"And(?=[A-Z])", or_part):
                keyword = next((k for k in _KEYWORDS if part.endswith(k) and len(part) > len(k)), "")
                prop = part[:len(part) - len(keyword)] if keyword else part
                arity = _ARITY.get(keyword, 1)
                conditions.append((_field(prop), keyword, args[position:position + arity]))
                position += arity
            groups.append(conditions)
    if groups:
        selected = [r for r in rows if any(all(_test(k, r.get(f), a) for f, k, a in g) for g in groups)]
    else:
        selected = list(rows)
    if subject == "count":
        return len(selected)
    if subject == "exists":
        return len(selected) > 0
    for prop, direction in reversed(re.findall(r"([A-Z][A-Za-z0-9]*?)(Asc|Desc)", ordering)):
        selected.sort(key=lambda r: r[_field(prop)], reverse=(direction == "Desc"))
    return selected if limit is None else selected[:limit]
''',
    tests=[
        ["findByAuthorAndPriceLessThanOrderByTitleAsc", ["Austen", 9], _BOOKS],
        ["findByGenre", ["scifi"], _BOOKS],
        ["countByInStockTrue", [], _BOOKS],
        ["existsByAuthorIgnoreCase", ["HERBERT"], _BOOKS],
        ["findByOrderByPriceDescTitleAsc", [], _BOOKS],
        ["findByPriceBetweenAndInStockTrueOrGenre", [9, 12, "horror"], _BOOKS],
        ["findTop2ByGenreInOrderByPriceDesc", [["scifi", "classic"]], _BOOKS],
        ["findFirstByOrderByPriceAsc", [], _BOOKS],
        ["findByIsbnIsNull", [], _BOOKS],
        ["countByIsbnIsNotNullAndTitleStartingWith", ["D"], _BOOKS],
        ["findByTitleContainingOrAuthorNotOrderByIdDesc", ["une", "Austen"], _BOOKS],
        ["existsByPriceGreaterThanEqual", [16], _BOOKS],
        ["findByGenreAndInStockFalseOrPriceLessThanEqualAndAuthorNot", ["scifi", 8, "Stoker"], _BOOKS],
        ["findByIsbnStartingWith", ["3"], _BOOKS],
        ["findByGenreOrAuthorAndPriceGreaterThan", ["horror", "Austen", 100], _BOOKS],
        ["findByGenre", ["poetry"], []],
        ["findTop10ByPriceGreaterThanOrderByAuthorAscPriceDesc", [0], _BOOKS],
    ],
    examples=2,
    wrong_solutions=[
        '''import re
_K = ["IsNotNull", "IsNull", "GreaterThanEqual", "GreaterThan", "LessThanEqual", "LessThan", "Between",
      "StartingWith", "Containing", "IgnoreCase", "Not", "In", "True", "False"]
_A = {"IsNotNull": 0, "IsNull": 0, "True": 0, "False": 0, "Between": 2}
def _t(k, v, a):
    if k == "IsNull": return v is None
    if k == "IsNotNull": return v is not None
    if k == "": return v == a[0]
    if k == "Not": return v != a[0]
    if v is None: return False
    if k == "True": return v is True
    if k == "False": return v is False
    if k == "GreaterThan": return v > a[0]
    if k == "GreaterThanEqual": return v >= a[0]
    if k == "LessThan": return v < a[0]
    if k == "LessThanEqual": return v <= a[0]
    if k == "Between": return a[0] <= v <= a[1]
    if k == "StartingWith": return v.startswith(a[0])
    if k == "Containing": return a[0] in v
    if k == "IgnoreCase": return v.lower() == a[0].lower()
    return v in a[0]
def run_query(method, args, rows):
    m = re.match(r"(find|count|exists)(?:(?:First|Top)([0-9]*))?By(.*)\\Z", method)
    limit = None if m.group(2) is None else int(m.group(2) or 1)
    pred, _, ordering = m.group(3).partition("OrderBy")
    pos, conds, ops = 0, [], []
    for tok in re.split(r"(And|Or)(?=[A-Z])", pred) if pred else []:
        if tok in ("And", "Or"):
            ops.append(tok); continue
        k = next((x for x in _K if tok.endswith(x) and len(tok) > len(x)), "")
        p = tok[:len(tok) - len(k)] if k else tok
        n = _A.get(k, 1)
        conds.append((p[0].lower() + p[1:], k, args[pos:pos + n])); pos += n
    out = []
    for r in rows:
        ok = True
        for i, (f, k, a) in enumerate(conds):
            v = _t(k, r.get(f), a)
            ok = v if i == 0 else (ok and v if ops[i - 1] == "And" else ok or v)
        if ok: out.append(r)
    if m.group(1) == "count": return len(out)
    if m.group(1) == "exists": return bool(out)
    for p, d in reversed(re.findall(r"([A-Z][A-Za-z0-9]*?)(Asc|Desc)", ordering)):
        out.sort(key=lambda r: r[p[0].lower() + p[1:]], reverse=(d == "Desc"))
    return out if limit is None else out[:limit]
''',
        '''import re
def run_query(method, args, rows):
    m = re.match(r"(find|count|exists)(?:(?:First|Top)([0-9]*))?By(.*)\\Z", method)
    pred, _, ordering = m.group(3).partition("OrderBy")
    fields = [p[0].lower() + p[1:] for p in re.split(r"And(?=[A-Z])", pred)] if pred else []
    out = [r for r in rows if all(r.get(f) == a for f, a in zip(fields, args))]
    if m.group(1) == "count": return len(out)
    if m.group(1) == "exists": return bool(out)
    for p, d in re.findall(r"([A-Z][A-Za-z0-9]*?)(Asc|Desc)", ordering):
        out.sort(key=lambda r: r[p[0].lower() + p[1:]], reverse=(d == "Desc"))
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: *Spring Data repositories: derived queries and @Query*. Regular expressions, `sorted` with keys.",
        intuition="The method name is a tiny language. Parse it into a structure — subject, OR-groups of AND-ed "
                  "conditions, ordering, limit — and only then touch the data. Mixing parsing with filtering is where solutions go wrong.",
        hints=[
            "Peel the name from the outside in: subject and limit, then split off `OrderBy`, then `Or`, then `And`.",
            "For each condition find the keyword by testing suffixes, longest first (`GreaterThanEqual` before `GreaterThan`, `IsNotNull` before `IsNull`).",
            "Sort by the *last* ordering property first; stable sorts then leave the first property dominant.",
        ],
        brute_force="Hard-code the handful of method names you expect. Spring Data exists precisely so nobody has to.",
        approach=r"""
**Dry run** of `findByPriceBetweenAndInStockTrueOrGenre` with `[9, 12, "horror"]`. Split on `Or`:
`PriceBetweenAndInStockTrue` | `Genre`. First group: `price Between (9,12)` and `inStock True` (no argument).
Second group: `genre == "horror"`. A row passes if either group passes entirely.

```java
public interface BookRepository extends JpaRepository<Book, Long> {

    List<Book> findByAuthorAndPriceLessThanOrderByTitleAsc(String author, BigDecimal price);

    long countByInStockTrue();

    boolean existsByAuthorIgnoreCase(String author);

    List<Book> findTop2ByGenreInOrderByPriceDesc(Collection<String> genres);
}
```

Spring generates, for the first one, roughly
`select b from Book b where b.author = ?1 and b.price < ?2 order by b.title asc`.
""",
        complexity="Parsing is O(length of the name). Filtering is O(rows × conditions); sorting O(k · r log r) for k ordering keys.",
        pitfalls="Evaluating `And`/`Or` strictly left to right instead of giving `And` precedence; matching "
                 "`GreaterThan` when the name says `GreaterThanEqual`; consuming an argument for `True`/`IsNull`; "
                 "applying the limit before sorting; comparing `None` with `<`, which raises in Python.",
        follow_up="Real names may traverse relations (`findByAuthorCountryCode`). When names grow that long, switch to `@Query`.",
    ),
),
dict(
    id="spring-page-request",
    title="Build a Page from a PageRequest",
    difficulty="Easy",
    pattern="Spring Data",
    entry="page",
    description=r"""
Repository methods accept a `Pageable` (page number, page size, sort) and return a `Page` that carries one slice
of the data plus enough numbers for a UI to draw "page 2 of 7".

`page(items, number, size, sort)`:

- `items` — list of dicts (the full query result),
- `number` — zero-based page index, `size` — rows per page,
- `sort` — list of `[field, direction]` with direction `"asc"` or `"desc"`; the first entry is the most
  significant; an empty list keeps the given order. Sorting is stable.

If `number < 0` return the string `"Page index must not be less than zero"`. If `size < 1` return
`"Page size must not be less than one"` (check the index first).

Otherwise return a dict with:

`content` (the rows of that page, possibly empty), `number`, `size`, `totalElements`, `totalPages`
(ceiling of total / size, `0` when there are no rows), `numberOfElements` (rows in this page), `first`
(`number == 0`), `last` (there is no later page: `number + 1 >= totalPages`), `hasNext` (`number + 1 < totalPages`).

**Example:** 11 rows, `page(rows, 2, 5, [])` → content has 1 row, `totalPages = 3`, `last = True`, `first = False`.
""",
    starter='''def page(items: list, number: int, size: int, sort: list):
    pass
''',
    solution='''def page(items, number, size, sort):
    if number < 0:
        return "Page index must not be less than zero"
    if size < 1:
        return "Page size must not be less than one"
    ordered = list(items)
    for field, direction in reversed(sort):
        ordered.sort(key=lambda row: row[field], reverse=(direction == "desc"))
    total = len(ordered)
    total_pages = (total + size - 1) // size
    content = ordered[number * size:(number + 1) * size]
    return {
        "content": content,
        "number": number,
        "size": size,
        "totalElements": total,
        "totalPages": total_pages,
        "numberOfElements": len(content),
        "first": number == 0,
        "last": number + 1 >= total_pages,
        "hasNext": number + 1 < total_pages,
    }
''',
    tests=[
        [_ITEMS, 2, 5, []],
        [_ITEMS, 0, 5, [["price", "desc"]]],
        [[], 0, 10, []],
        [_ITEMS, -1, 5, []],
        [_ITEMS, 0, 0, []],
        [_ITEMS, -1, 0, []],
        [_ITEMS, 1, 4, [["genre", "asc"], ["price", "desc"]]],
        [_ITEMS, 9, 5, []],
        [_ITEMS, 0, 11, [["genre", "desc"], ["id", "desc"]]],
        [_ITEMS, 0, 100, [["price", "asc"]]],
        [_ITEMS[:10], 1, 5, [["id", "desc"]]],
        [_ITEMS[:1], 0, 1, []],
        [[], 3, 1, [["id", "asc"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def page(items, number, size, sort):
    if number < 0: return "Page index must not be less than zero"
    if size < 1: return "Page size must not be less than one"
    ordered = list(items)
    for field, direction in sort:
        ordered.sort(key=lambda row: row[field], reverse=(direction == "desc"))
    total = len(ordered); tp = (total + size - 1) // size
    content = ordered[number * size:(number + 1) * size]
    return {"content": content, "number": number, "size": size, "totalElements": total, "totalPages": tp,
            "numberOfElements": len(content), "first": number == 0, "last": number + 1 >= tp, "hasNext": number + 1 < tp}
''',
        '''def page(items, number, size, sort):
    if number < 0: return "Page index must not be less than zero"
    if size < 1: return "Page size must not be less than one"
    ordered = list(items)
    for field, direction in reversed(sort):
        ordered.sort(key=lambda row: row[field], reverse=(direction == "desc"))
    total = len(ordered); tp = total // size + 1
    content = ordered[number * size:(number + 1) * size]
    return {"content": content, "number": number, "size": size, "totalElements": total, "totalPages": tp,
            "numberOfElements": len(content), "first": number == 0, "last": number + 1 >= tp, "hasNext": number + 1 < tp}
''',
        '''def page(items, number, size, sort):
    if size < 1: return "Page size must not be less than one"
    if number < 0: return "Page index must not be less than zero"
    ordered = list(items)
    for field, direction in reversed(sort):
        ordered.sort(key=lambda row: row[field], reverse=(direction == "desc"))
    total = len(ordered); tp = (total + size - 1) // size
    content = ordered[(number - 1) * size:number * size] if number else ordered[:size]
    return {"content": content, "number": number, "size": size, "totalElements": total, "totalPages": tp,
            "numberOfElements": len(content), "first": number == 0, "last": number + 1 >= tp, "hasNext": number + 1 < tp}
''',
    ],
    guide=dict(
        prereqs="List slicing and integer division. Lesson: *Spring Data repositories: derived queries and @Query*.",
        intuition="A page is a slice plus arithmetic. The arithmetic has three classic off-by-one traps: zero-based "
                  "page numbers, the ceiling division, and the empty result.",
        hints=[
            "Sort a copy first, then slice `[number*size : (number+1)*size]`; Python slices past the end are empty, not errors.",
            "Ceiling division without floats: `(total + size - 1) // size`.",
            "Express `last` and `hasNext` with `number + 1` and `totalPages`; check them against the empty case.",
        ],
        brute_force="Chunk the whole list into pages and index the list of chunks. Correct, but it builds every "
                    "page to return one, and a page number past the end needs special handling.",
        approach=r"""
**Dry run:** 11 rows, `number = 2`, `size = 5`. `totalPages = (11 + 4) // 5 = 3`. Slice `[10:15]` → one row.
`first = False`, `last = 3 >= 3 = True`, `hasNext = False`.

Empty table: `totalPages = 0`, so page 0 is both `first` and `last`.

```java
Page<Book> result = bookRepository.findByGenre(
        "scifi", PageRequest.of(2, 5, Sort.by(Sort.Order.asc("genre"), Sort.Order.desc("price"))));

result.getContent();        // the rows
result.getTotalElements();  // needs an extra "select count(*)" query
result.hasNext();
```

A database does this with `ORDER BY ... LIMIT 5 OFFSET 10`. Use `Slice` instead of `Page` to skip the count query.
""",
        complexity="Time O(k · n log n) for k sort keys (a database would use an index). Space O(n) for the copy.",
        pitfalls="Treating page numbers as one-based; `total // size + 1` (wrong when total divides evenly and for "
                 "an empty result); sorting the most significant key last; mutating the caller's list.",
        follow_up="Deep `OFFSET` pagination gets slow. Sketch keyset pagination (`WHERE id > :lastSeen ORDER BY id LIMIT n`).",
    ),
),
dict(
    id="spring-n-plus-one",
    title="Count the queries: the N+1 problem and its fixes",
    difficulty="Medium",
    pattern="Spring Data",
    entry="count_queries",
    description=r"""
An `Author` entity has a collection of `Book`s. The application runs `authorRepository.findAll()` (one query
returning `n` authors) and then touches `author.getBooks()` for some authors. How many SQL statements run in
total?

`count_queries(n, strategy, accesses, batch_size)`:

- `n` — number of authors returned (indexes `0 .. n-1`),
- `accesses` — list of author indexes whose book collection is read, in order (repeats allowed),
- `strategy` — how the collection is fetched:

| strategy | behaviour |
|---|---|
| `"lazy"` | the first time an author's collection is read, one query loads it; later reads are free |
| `"eager-select"` | right after the first query, one extra query per author runs immediately, whether or not the collection is used |
| `"join-fetch"` | the first query joins the books (`JOIN FETCH` / `@EntityGraph`): no further queries |
| `"subselect"` | the first time **any** collection is read, one query loads the collections of all authors |
| `"batch"` | reading an uninitialised collection runs one query that loads it **together with** the collections of the next uninitialised authors by lowest index, up to `batch_size` collections in total |

`batch_size` is only used by `"batch"`.

Return the total number of queries, including the initial one.

**Example:** `count_queries(100, "lazy", list(range(100)), 0)` → `101` (the "N+1" problem).
With `"batch"` and `batch_size = 25` → `5`.
""",
    starter='''def count_queries(n: int, strategy: str, accesses: list, batch_size: int) -> int:
    pass
''',
    solution='''def count_queries(n, strategy, accesses, batch_size):
    queries = 1
    if strategy == "join-fetch":
        return queries
    if strategy == "eager-select":
        return queries + n
    if strategy == "subselect":
        return queries + (1 if accesses else 0)
    loaded = [False] * n
    for index in accesses:
        if loaded[index]:
            continue
        queries += 1
        loaded[index] = True
        if strategy == "batch":
            room = batch_size - 1
            for other in range(n):
                if room <= 0:
                    break
                if not loaded[other]:
                    loaded[other] = True
                    room -= 1
    return queries
''',
    tests=[
        [100, "lazy", list(range(100)), 0],
        [100, "batch", list(range(100)), 25],
        [0, "lazy", [], 0],
        [0, "eager-select", [], 0],
        [50, "eager-select", [], 0],
        [50, "join-fetch", list(range(50)), 0],
        [50, "subselect", [7, 7, 9], 0],
        [50, "subselect", [], 0],
        [10, "lazy", [3, 3, 3, 4, 3, 4], 0],
        [10, "batch", [9, 0, 5], 4],
        [10, "batch", [9, 8, 7, 6, 5, 4, 3, 2, 1, 0], 3],
        [7, "batch", [6, 5, 4, 3], 1],
        [1000, "batch", list(range(999, -1, -1)), 100],
        [5, "batch", [2], 50],
        [12, "batch", [11, 3, 10, 2, 9], 5],
    ],
    examples=2,
    wrong_solutions=[
        '''def count_queries(n, strategy, accesses, batch_size):
    if strategy == "join-fetch": return 1
    if strategy == "eager-select": return 1 + n
    if strategy == "subselect": return 2 if accesses else 1
    if strategy == "lazy": return 1 + len(accesses)
    return 1 + -(-len(set(accesses)) // batch_size)
''',
        '''def count_queries(n, strategy, accesses, batch_size):
    if strategy == "join-fetch": return 1
    if strategy == "eager-select": return 1 + len(set(accesses))
    if strategy == "subselect": return 2
    distinct = len(set(accesses))
    if strategy == "lazy": return 1 + distinct
    return 1 + -(-n // batch_size)
''',
    ],
    guide=dict(
        prereqs="Lesson: *JPA basics: entity mapping, relationships and the N+1 problem*.",
        intuition="Count round trips to the database, not rows. Lazy loading turns a loop over N parents into N "
                  "extra round trips; every fix works by loading many collections per round trip.",
        hints=[
            "Three strategies have closed-form answers. Only `lazy` and `batch` need simulation.",
            "Keep a boolean per author: is its collection loaded yet?",
            "For `batch`, after loading the requested author, sweep from index 0 marking unloaded authors until the batch is full.",
        ],
        brute_force="Simulating every strategy step by step is fine and is what the solution does for two of them.",
        approach=r"""
**Dry run** `n = 10`, `batch`, `batch_size = 4`, accesses `[9, 0, 5]`. Access 9: query 2 loads 9 plus the three
lowest unloaded → 0, 1, 2. Access 0: already loaded. Access 5: query 3 loads 5 plus 3, 4, 6. Total 3.

```java
@Entity
class Author {
    @Id @GeneratedValue Long id;

    @OneToMany(mappedBy = "author", fetch = FetchType.LAZY)   // LAZY is the default for collections
    @BatchSize(size = 25)                                     // Hibernate: load in batches
    List<Book> books = new ArrayList<>();
}

interface AuthorRepository extends JpaRepository<Author, Long> {
    @Query("select distinct a from Author a join fetch a.books")   // one query
    List<Author> findAllWithBooks();

    @EntityGraph(attributePaths = "books")                           // same idea, declaratively
    List<Author> findByCountry(String country);
}
```

Turn on `spring.jpa.show-sql=true` (or better, a query-count assertion in tests) to see the problem.
""",
        complexity="Time O(accesses + n · batches) for the naive batch sweep; O(1) for the closed forms. Space O(n).",
        pitfalls="Counting repeated reads of the same collection; thinking `EAGER` solves N+1 (with a list query it "
                 "*guarantees* N extra selects); computing batches as `ceil(n / size)` even when few collections are touched.",
        follow_up="`JOIN FETCH` with pagination loads everything into memory. Why, and what do DTO projections change?",
    ),
),
dict(
    id="spring-connection-pool",
    title="Simulate a connection pool with a timeout",
    difficulty="Medium",
    pattern="Data access",
    entry="simulate",
    description=r"""
Opening a database connection is slow, so applications keep a fixed **pool** of open connections (Spring Boot
uses HikariCP). A request borrows a connection, uses it, and returns it. If all connections are busy the request
waits in a first-come-first-served queue, but only up to a **connection timeout**.

`simulate(pool_size, timeout, requests)`:

- `pool_size` — number of connections (≥ 1), `timeout` — maximum wait in milliseconds (≥ 0),
- `requests` — list of `[arrival, hold]` sorted by arrival time (ties keep list order): the request asks for a
  connection at time `arrival` and, once it has one, keeps it for `hold` milliseconds.

A connection released at time *t* can be handed to a waiting request at the same time *t*. A request gets the
earliest available connection; earlier requests in the list are always served before later ones. If a request
would have to wait **longer than** `timeout` (waiting exactly `timeout` is still fine), it gives up at
`arrival + timeout` without ever holding a connection.

Return, for each request in order, the time it **obtained** its connection, or `-1` if it timed out.

**Example:** `simulate(1, 50, [[0, 100], [10, 10], [60, 10]])` → `[0, -1, 100]`: the second request would wait
90 ms; the third waits 40 ms.
""",
    starter='''def simulate(pool_size: int, timeout: int, requests: list) -> list:
    pass
''',
    solution='''import heapq


def simulate(pool_size, timeout, requests):
    free_at = [0] * pool_size
    heapq.heapify(free_at)
    result = []
    for arrival, hold in requests:
        start = max(arrival, free_at[0])
        if start - arrival > timeout:
            result.append(-1)
            continue
        heapq.heapreplace(free_at, start + hold)
        result.append(start)
    return result
''',
    tests=[
        [1, 50, [[0, 100], [10, 10], [60, 10]]],
        [2, 30, [[0, 100], [0, 100], [5, 10]]],
        [1, 0, [[0, 10], [10, 10], [19, 1], [20, 5]]],
        [3, 100, []],
        [1, 1000, [[0, 10], [0, 10], [0, 10], [0, 10]]],
        [2, 15, [[0, 20], [1, 30], [2, 5], [3, 5], [30, 1]]],
        [2, 1000, [[0, 50], [0, 10], [5, 10], [6, 10], [7, 100], [200, 1]]],
        [1, 10, [[5, 0], [5, 0], [5, 20], [14, 3], [16, 3]]],
        [4, 5, [[i, 12] for i in range(20)]],
        [10, 30000, [[i * 3, 250] for i in range(400)]],
        [1, 50, [[100, 60], [110, 1], [111, 1], [160, 1]]],
        [3, 20, [[0, 100], [0, 40], [0, 10], [1, 5], [2, 50], [3, 50], [12, 1]]],
    ],
    examples=2,
    wrong_solutions=[
        '''import heapq
def simulate(pool_size, timeout, requests):
    free_at = [0] * pool_size
    result = []
    for arrival, hold in requests:
        start = max(arrival, free_at[0])
        if start - arrival >= timeout and start != arrival:
            result.append(-1); continue
        heapq.heapreplace(free_at, start + hold)
        result.append(start)
    return result
''',
        '''import heapq
def simulate(pool_size, timeout, requests):
    free_at = [0] * pool_size
    result = []
    for arrival, hold in requests:
        start = max(arrival, free_at[0])
        heapq.heapreplace(free_at, start + hold)
        result.append(start if start - arrival <= timeout else -1)
    return result
''',
        '''def simulate(pool_size, timeout, requests):
    busy_until = []
    result = []
    for arrival, hold in requests:
        busy_until = [t for t in busy_until if t > arrival]
        if len(busy_until) < pool_size:
            busy_until.append(arrival + hold)
            result.append(arrival)
        else:
            result.append(-1)
    return result
''',
    ],
    guide=dict(
        prereqs="Heaps / priority queues (`heapq`). Lesson: *Configuring the DataSource and connection pools*.",
        intuition="All that matters about a connection is *when it is next free*. Keep those times in a min-heap; "
                  "the top is the connection the next request in line will get. Because the queue is first-come-first-served, "
                  "requests can be decided one by one in input order.",
        hints=[
            "Start with `pool_size` zeros in a heap: every connection is free from time 0.",
            "The start time of a request is `max(arrival, earliest free time)`.",
            "A request that times out must leave the heap untouched: it never held a connection.",
        ],
        brute_force="Advance a clock millisecond by millisecond with an explicit waiting queue. Correct but O(total "
                    "time × pool), hopeless for long holds.",
        approach=r"""
**Dry run** `pool_size = 1, timeout = 50`: heap `[0]`.
`[0,100]` → start 0, heap `[100]`. `[10,10]` → start would be 100, wait 90 > 50 → `-1`, heap unchanged.
`[60,10]` → start 100, wait 40 → OK, heap `[110]`.

Why input order is safe: an earlier request has an earlier (or equal) deadline and priority in the queue, so
nothing a later request does can change its fate.

```yaml
# src/main/resources/application.yml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/bookshop
    hikari:
      maximum-pool-size: 10        # pool_size
      connection-timeout: 30000    # timeout in ms (the default)
```

```java
// what a timeout looks like in the log:
// SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 30000ms.
```
""",
        complexity="Time O(R log P) for R requests and pool size P. Space O(P).",
        pitfalls="Occupying a connection for a request that timed out; rejecting immediately instead of waiting; "
                 "an off-by-one on 'exactly the timeout'; forgetting that a connection freed at *t* is usable at *t*.",
        follow_up="A slow query holding connections is the usual cause of pool exhaustion. How does `@Transactional` around a remote HTTP call make it worse?",
    ),
),
]
