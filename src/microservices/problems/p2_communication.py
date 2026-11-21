PROBLEMS = [
dict(
    id="msvc-contract-verify",
    title="Consumer-driven Contract Verification",
    difficulty="Medium",
    pattern="Contract Testing",
    entry="verify_contracts",
    description=r"""
Each consumer of a provider service writes down what it needs. You must check those expectations against what the provider really returns.

- `contracts`: a list of dicts `{"consumer": str, "method": str, "path": str, "status": int, "body": {...}}`. `body` maps a field name to an expected type name, or to a nested dict of the same shape (meaning "this field is an object containing at least these fields").
- `provider`: a dict mapping `"METHOD path"` (for example `"GET /pets/7"`) to `{"status": int, "body": {...}}` holding a real example response.

Type names: `"string"`, `"integer"`, `"number"`, `"boolean"`, `"array"`, `"object"`, `"null"`. An integer value also satisfies `"number"`. A boolean is **not** an integer or a number.

Check each contract in order:

1. If the provider has no such endpoint, report `"missing endpoint"` and nothing else for that contract.
2. If the status differs, report `"status <actual> != <expected>"`, then still check the body.
3. For each expected field in alphabetical order: if absent report `"missing field <name>"`; if the type is wrong report `"field <name> is <actual>, expected <expected>"`. For a nested expectation the value must be an object (else the type message with expected `object`), and its inner fields are checked the same way with names joined by a dot, such as `owner.phone`.

Extra fields in the provider response are fine. Return a list of `[consumer, "METHOD path", message]`.

**Example:** contract `{"consumer": "reminders", "method": "GET", "path": "/pets/7", "status": 200, "body": {"name": "string", "age": "integer"}}` against provider `{"GET /pets/7": {"status": 200, "body": {"name": "Miso", "age": "4"}}}` → `[["reminders", "GET /pets/7", "field age is string, expected integer"]]`
""",
    starter='''def verify_contracts(contracts: List[dict], provider: dict) -> List[List[str]]:
    pass
''',
    solution='''def verify_contracts(contracts, provider):
    def type_of(v):
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "boolean"
        if isinstance(v, int):
            return "integer"
        if isinstance(v, float):
            return "number"
        if isinstance(v, str):
            return "string"
        if isinstance(v, list):
            return "array"
        return "object"

    def check(expected, actual, prefix, out):
        for name in sorted(expected):
            full = prefix + name
            want = expected[name]
            if name not in actual:
                out.append("missing field " + full)
                continue
            got = type_of(actual[name])
            if isinstance(want, dict):
                if got != "object":
                    out.append("field %s is %s, expected object" % (full, got))
                else:
                    check(want, actual[name], full + ".", out)
            elif got != want and not (want == "number" and got == "integer"):
                out.append("field %s is %s, expected %s" % (full, got, want))

    result = []
    for c in contracts:
        key = c["method"] + " " + c["path"]
        if key not in provider:
            result.append([c["consumer"], key, "missing endpoint"])
            continue
        resp = provider[key]
        msgs = []
        if resp["status"] != c["status"]:
            msgs.append("status %d != %d" % (resp["status"], c["status"]))
        check(c["body"], resp["body"], "", msgs)
        for m in msgs:
            result.append([c["consumer"], key, m])
    return result
''',
    tests=[
        [[{"consumer": "reminders", "method": "GET", "path": "/pets/7", "status": 200, "body": {"name": "string", "age": "integer"}}],
         {"GET /pets/7": {"status": 200, "body": {"name": "Miso", "age": "4"}}}],
        [[{"consumer": "billing", "method": "GET", "path": "/pets/7", "status": 200, "body": {"name": "string"}}],
         {"GET /pets/7": {"status": 200, "body": {"name": "Miso", "age": 4, "extra": [1, 2]}}}],
        [[], {"GET /x": {"status": 200, "body": {}}}],
        [[{"consumer": "a", "method": "POST", "path": "/pets", "status": 201, "body": {"id": "integer"}}],
         {"GET /pets": {"status": 200, "body": {"id": 1}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"z": "string", "a": "string"}}],
         {"GET /p": {"status": 404, "body": {}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"weight": "number", "chipped": "integer", "n": "number"}}],
         {"GET /p": {"status": 200, "body": {"weight": 4, "chipped": True, "n": True}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"owner": {"phone": "string", "name": "string"}}}],
         {"GET /p": {"status": 200, "body": {"owner": {"name": "Ada", "phone": 123}}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"owner": {"phone": "string"}}}],
         {"GET /p": {"status": 200, "body": {"owner": "Ada"}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"tags": "array", "gone": "null", "meta": "object", "w": "number"}}],
         {"GET /p": {"status": 200, "body": {"tags": [], "gone": None, "meta": {}, "w": 2.5}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"x": "string"}},
          {"consumer": "b", "method": "GET", "path": "/p", "status": 200, "body": {"y": "integer"}},
          {"consumer": "c", "method": "GET", "path": "/q", "status": 200, "body": {}}],
         {"GET /p": {"status": 200, "body": {"x": "ok", "y": 1.5}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"o": {"i": {"deep": "boolean"}}, "gone": "null"}}],
         {"GET /p": {"status": 200, "body": {"o": {"i": {"deep": 0}}, "gone": 0}}}],
        [[{"consumer": "a", "method": "GET", "path": "/p", "status": 200, "body": {"tags": "array", "meta": "object"}}],
         {"GET /p": {"status": 200, "body": {"tags": {}, "meta": []}}}],
    ],
    examples=2,
    wrong_solutions=[
        '''def verify_contracts(contracts, provider):
    names = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object", type(None): "null"}
    result = []
    for c in contracts:
        key = c["method"] + " " + c["path"]
        if key not in provider:
            result.append([c["consumer"], key, "missing endpoint"])
            continue
        resp = provider[key]
        if resp["status"] != c["status"]:
            result.append([c["consumer"], key, "status %d != %d" % (resp["status"], c["status"])])
        for name in sorted(c["body"]):
            want = c["body"][name]
            if name not in resp["body"]:
                result.append([c["consumer"], key, "missing field " + name])
            elif not isinstance(want, dict) and names[type(resp["body"][name])] != want:
                result.append([c["consumer"], key, "field %s is %s, expected %s" % (name, names[type(resp["body"][name])], want)])
    return result
''',
        '''def verify_contracts(contracts, provider):
    def type_of(v):
        if v is None:
            return "null"
        if isinstance(v, int):
            return "integer"
        if isinstance(v, float):
            return "number"
        if isinstance(v, str):
            return "string"
        if isinstance(v, list):
            return "array"
        return "object"
    def check(expected, actual, prefix, out):
        for name in sorted(expected):
            full = prefix + name
            want = expected[name]
            if name not in actual:
                out.append("missing field " + full)
                continue
            got = type_of(actual[name])
            if isinstance(want, dict):
                if got != "object":
                    out.append("field %s is %s, expected object" % (full, got))
                else:
                    check(want, actual[name], full + ".", out)
            elif got != want and not (want == "number" and got == "integer"):
                out.append("field %s is %s, expected %s" % (full, got, want))
    result = []
    for c in contracts:
        key = c["method"] + " " + c["path"]
        if key not in provider:
            result.append([c["consumer"], key, "missing endpoint"])
            continue
        resp = provider[key]
        msgs = []
        if resp["status"] != c["status"]:
            msgs.append("status %d != %d" % (resp["status"], c["status"]))
        check(c["body"], resp["body"], "", msgs)
        for m in msgs:
            result.append([c["consumer"], key, m])
    return result
''',
    ],
    guide=dict(
        prereqs="Consumer-driven contracts from the lesson *Contract tests and testing in production*. Recursion over nested dictionaries; `isinstance`.",
        intuition="A contract is a list of small promises: this endpoint exists, it answers with this status, and these fields have these types. The provider may offer more, never less. Verification walks the promises and collects each broken one.",
        hints=[
            "Write a helper that names the type of a Python value. Test `bool` before `int`, because in Python `True` is also an `int`.",
            "Write a recursive helper that checks one expected dict against one actual dict and carries a dotted prefix.",
            "Loop over contracts in order; a missing endpoint ends that contract early.",
        ],
        brute_force="Compare the whole expected response for equality with the real one. That fails every time the provider adds a harmless field, which is exactly the brittleness contract tests are meant to avoid.",
        approach="`type_of` maps a value to a name. `check(expected, actual, prefix, out)` loops over sorted names: missing → message; nested expectation → require an object and recurse with `prefix + name + '.'`; otherwise compare names, letting an integer pass for number.\n\n**Dry run** on the first example: endpoint exists; status equal; field `age` has value `\"4\"`, a string, expected integer → one message; `name` is a string as expected.",
        complexity="Time O(total number of expected fields); space O(depth) for the recursion plus the output.",
        pitfalls="`isinstance(True, int)` is `True` in Python, so check booleans first. Do not fail on extra provider fields. Report the nested path, not only the leaf name.",
        follow_up="Real tools such as Pact record these expectations from consumer tests and replay them in the provider's build. Add array element types as an extension.",
    ),
),
dict(
    id="msvc-schema-evolution",
    title="Schema Evolution: Read Old Data with a New Schema",
    difficulty="Medium",
    pattern="Serialisation",
    entry="read_record",
    description=r"""
A record was written with the **writer schema** and is now read by code that expects the **reader schema**. Resolve the two, as binary formats with schemas do.

- `record`: a dict of the values that were written (it has exactly the writer's fields).
- `writer`: a list of `{"name": str, "type": str}`.
- `reader`: a list of `{"name": str, "type": str}` where a field may also have a `"default"` key (its value may be `None`).

Types are `"int"`, `"float"`, `"string"`, `"bool"`.

For each reader field, in reader order:

1. If the writer has the field with the same type, copy the value.
2. If the writer has it as `"int"` and the reader wants `"float"`, convert the value with `float(...)`.
3. If the writer has it with any other different type, stop and return the string `"ERROR: type mismatch on <name>"`.
4. If the writer does not have it: use the default if the reader field has a `"default"` key, otherwise stop and return `"ERROR: no default for <name>"`.

Writer fields unknown to the reader are dropped. Return the resulting dict (or the first error string).

**Example:** `record = {"id": 7, "name": "Miso"}`, writer `[id:int, name:string]`, reader `[id:int, species:string default "cat"]` → `{"id": 7, "species": "cat"}`
""",
    starter='''def read_record(record: dict, writer: List[dict], reader: List[dict]):
    pass
''',
    solution='''def read_record(record, writer, reader):
    wtypes = {f["name"]: f["type"] for f in writer}
    out = {}
    for f in reader:
        name, rtype = f["name"], f["type"]
        if name in wtypes:
            wtype = wtypes[name]
            if wtype == rtype:
                out[name] = record[name]
            elif wtype == "int" and rtype == "float":
                out[name] = float(record[name])
            else:
                return "ERROR: type mismatch on " + name
        elif "default" in f:
            out[name] = f["default"]
        else:
            return "ERROR: no default for " + name
    return out
''',
    tests=[
        [{"id": 7, "name": "Miso"}, [{"name": "id", "type": "int"}, {"name": "name", "type": "string"}],
         [{"name": "id", "type": "int"}, {"name": "species", "type": "string", "default": "cat"}]],
        [{"id": 7}, [{"name": "id", "type": "int"}], [{"name": "id", "type": "float"}]],
        [{}, [], []],
        [{"id": 7}, [{"name": "id", "type": "int"}], []],
        [{"id": 7}, [{"name": "id", "type": "int"}], [{"name": "id", "type": "int"}, {"name": "email", "type": "string"}]],
        [{"id": 7.5}, [{"name": "id", "type": "float"}], [{"name": "id", "type": "int"}]],
        [{"id": 7}, [{"name": "id", "type": "int"}], [{"name": "id", "type": "int"}, {"name": "note", "type": "string", "default": None}]],
        [{"a": 1, "b": "x"}, [{"name": "a", "type": "int"}, {"name": "b", "type": "string"}],
         [{"name": "b", "type": "int"}, {"name": "c", "type": "int"}]],
        [{"a": 1, "b": "x"}, [{"name": "a", "type": "int"}, {"name": "b", "type": "string"}],
         [{"name": "c", "type": "int"}, {"name": "b", "type": "int"}]],
        [{"ok": True, "n": 3}, [{"name": "ok", "type": "bool"}, {"name": "n", "type": "int"}],
         [{"name": "n", "type": "float"}, {"name": "ok", "type": "bool"}, {"name": "extra", "type": "bool", "default": False}]],
        [{"a": "1"}, [{"name": "a", "type": "string"}], [{"name": "a", "type": "float", "default": 0.0}]],
        [{"f%d" % i: i for i in range(40)}, [{"name": "f%d" % i, "type": "int"} for i in range(40)],
         [{"name": "f%d" % i, "type": "float" if i % 2 else "int"} for i in range(39, -1, -3)] + [{"name": "new", "type": "int", "default": -1}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def read_record(record, writer, reader):
    out = {}
    for f in reader:
        name = f["name"]
        if name in record:
            out[name] = record[name]
        elif f.get("default") is not None:
            out[name] = f["default"]
        else:
            return "ERROR: no default for " + name
    return out
''',
        '''def read_record(record, writer, reader):
    wtypes = {f["name"]: f["type"] for f in writer}
    out = dict(record)
    for f in reader:
        name, rtype = f["name"], f["type"]
        if name in wtypes:
            if wtypes[name] == rtype:
                pass
            elif wtypes[name] == "int" and rtype == "float":
                out[name] = float(record[name])
            else:
                return "ERROR: type mismatch on " + name
        elif "default" in f:
            out[name] = f["default"]
        else:
            return "ERROR: no default for " + name
    return out
''',
    ],
    guide=dict(
        prereqs="Schemas and serialisation formats from the lesson *Technology choices*. Dictionaries.",
        intuition="The reader's schema decides the shape of the result. The writer's schema only tells you which values exist and what type they have. Defaults fill the gap when old data lacks a new field.",
        hints=[
            "Build a dictionary from writer field name to writer type.",
            "Loop over the reader fields, not the record. Check for the key `\"default\"` with `in`, because a default of `None` is legal.",
            "Return the error string as soon as you meet the first problem.",
        ],
        brute_force="Copy the record and patch it. This keeps fields the reader does not know about and misses type promotion; the rule-by-rule loop over reader fields is both simpler and correct.",
        approach="For each reader field: same type → copy; int to float → convert; other type difference → error; absent with default → default; absent without → error.\n\n**Dry run** on the example: `id` is int in both → 7. `species` is not written; the reader has default `\"cat\"` → use it. `name` is not in the reader → dropped. Result `{id: 7, species: cat}`.",
        complexity="Time O(W + R) for the two field lists; space O(W + R).",
        pitfalls="Using `f.get(\"default\")` treats a `None` default as missing. Converting float to int silently loses data and must be an error. The first error in reader order wins.",
        follow_up="This is forward and backward compatibility in miniature: new readers with old data need defaults on added fields; old readers with new data need to ignore unknown fields.",
    ),
),
dict(
    id="msvc-service-registry",
    title="Service Registry with Heartbeats and Round Robin",
    difficulty="Medium",
    pattern="Service Discovery",
    kind="class",
    entry="ServiceRegistry",
    description=r"""
Implement a service discovery registry with explicit timestamps (integers that never decrease from call to call).

`ServiceRegistry(ttl)`: an instance is **live** at time `ts` if `ts < last_seen + ttl`, where `last_seen` is the time of its registration or latest accepted heartbeat. An instance that is no longer live counts as removed.

- `register(service, instance, ts)` → `None`. Adds the instance, or refreshes `last_seen` if it is already there.
- `heartbeat(service, instance, ts)` → `True` and refreshes `last_seen` if the instance is live at `ts`; otherwise `False` (an expired instance must register again).
- `deregister(service, instance, ts)` → `True` if the instance was live at `ts` and is now removed, otherwise `False`.
- `lookup(service, ts)` → the sorted list of live instance names.
- `pick(service, ts)` → client-side round robin. Each service has a counter starting at 0. Let `live` be `lookup(service, ts)`. If it is empty return `None` and leave the counter alone. Otherwise return `live[counter % len(live)]` and add 1 to the counter.

**Example:** `ServiceRegistry(10)`: `register("pets","a",0)`, `register("pets","b",3)`, `lookup("pets",9)` → `["a","b"]`, `lookup("pets",10)` → `["b"]`, `heartbeat("pets","a",11)` → `False`, `pick("pets",11)` → `"b"`.
""",
    starter='''class ServiceRegistry:
    def __init__(self, ttl: int):
        pass

    def register(self, service: str, instance: str, ts: int) -> None:
        pass

    def heartbeat(self, service: str, instance: str, ts: int) -> bool:
        pass

    def deregister(self, service: str, instance: str, ts: int) -> bool:
        pass

    def lookup(self, service: str, ts: int) -> List[str]:
        pass

    def pick(self, service: str, ts: int) -> Optional[str]:
        pass
''',
    solution='''class ServiceRegistry:
    def __init__(self, ttl):
        self.ttl = ttl
        self.seen = {}        # service -> {instance: last_seen}
        self.counter = {}     # service -> round-robin counter

    def _live(self, service, instance, ts):
        last = self.seen.get(service, {}).get(instance)
        return last is not None and ts < last + self.ttl

    def register(self, service, instance, ts):
        self.seen.setdefault(service, {})[instance] = ts

    def heartbeat(self, service, instance, ts):
        if not self._live(service, instance, ts):
            self.seen.get(service, {}).pop(instance, None)
            return False
        self.seen[service][instance] = ts
        return True

    def deregister(self, service, instance, ts):
        live = self._live(service, instance, ts)
        self.seen.get(service, {}).pop(instance, None)
        return live

    def lookup(self, service, ts):
        return sorted(i for i in self.seen.get(service, {}) if self._live(service, i, ts))

    def pick(self, service, ts):
        live = self.lookup(service, ts)
        if not live:
            return None
        c = self.counter.get(service, 0)
        self.counter[service] = c + 1
        return live[c % len(live)]
''',
    tests=[
        [["ServiceRegistry", "register", "register", "lookup", "lookup", "heartbeat", "pick"],
         [[10], ["pets", "a", 0], ["pets", "b", 3], ["pets", 9], ["pets", 10], ["pets", "a", 11], ["pets", 11]]],
        [["ServiceRegistry", "lookup", "pick", "heartbeat", "deregister"],
         [[5], ["x", 0], ["x", 0], ["x", "i", 0], ["x", "i", 0]]],
        [["ServiceRegistry", "register", "register", "register", "pick", "pick", "pick", "pick"],
         [[100], ["s", "c", 0], ["s", "a", 0], ["s", "b", 0], ["s", 1], ["s", 2], ["s", 3], ["s", 4]]],
        [["ServiceRegistry", "register", "heartbeat", "heartbeat", "lookup", "heartbeat", "lookup"],
         [[10], ["s", "a", 0], ["s", "a", 9], ["s", "a", 18], ["s", 27], ["s", "a", 28], ["s", 28]]],
        [["ServiceRegistry", "register", "deregister", "deregister", "lookup", "register", "lookup"],
         [[10], ["s", "a", 0], ["s", "a", 1], ["s", "a", 2], ["s", 2], ["s", "a", 3], ["s", 4]]],
        [["ServiceRegistry", "register", "deregister", "register", "heartbeat"],
         [[10], ["s", "a", 0], ["s", "a", 10], ["s", "a", 10], ["s", "a", 19]]],
        [["ServiceRegistry", "register", "register", "pick", "pick", "lookup", "pick", "pick", "pick"],
         [[10], ["s", "a", 0], ["s", "b", 5], ["s", 6], ["s", 7], ["s", 12], ["s", 12], ["s", 20], ["s", 20]]],
        [["ServiceRegistry", "register", "register", "lookup", "lookup", "pick", "pick"],
         [[10], ["pets", "a", 0], ["billing", "a", 0], ["pets", 1], ["billing", 1], ["pets", 1], ["billing", 1]]],
        [["ServiceRegistry", "register", "register", "lookup", "register", "lookup"],
         [[10], ["s", "a", 0], ["s", "a", 8], ["s", 15], ["s", "a", 30], ["s", 39]]],
        [["ServiceRegistry", "register", "register", "register", "pick", "deregister", "pick", "pick", "pick"],
         [[50], ["s", "a", 0], ["s", "b", 0], ["s", "c", 0], ["s", 1], ["s", "a", 2], ["s", 3], ["s", 4], ["s", 5]]],
        [["ServiceRegistry", "register", "heartbeat", "register", "heartbeat", "lookup"],
         [[1], ["s", "a", 0], ["s", "a", 1], ["s", "a", 1], ["s", "a", 1], ["s", 1]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class ServiceRegistry:
    def __init__(self, ttl):
        self.ttl = ttl
        self.seen = {}
        self.counter = {}
    def _live(self, service, instance, ts):
        last = self.seen.get(service, {}).get(instance)
        return last is not None and ts <= last + self.ttl
    def register(self, service, instance, ts):
        self.seen.setdefault(service, {})[instance] = ts
    def heartbeat(self, service, instance, ts):
        if not self._live(service, instance, ts):
            return False
        self.seen[service][instance] = ts
        return True
    def deregister(self, service, instance, ts):
        live = self._live(service, instance, ts)
        self.seen.get(service, {}).pop(instance, None)
        return live
    def lookup(self, service, ts):
        return sorted(i for i in self.seen.get(service, {}) if self._live(service, i, ts))
    def pick(self, service, ts):
        live = self.lookup(service, ts)
        if not live:
            return None
        c = self.counter.get(service, 0)
        self.counter[service] = c + 1
        return live[c % len(live)]
''',
        '''class ServiceRegistry:
    def __init__(self, ttl):
        self.ttl = ttl
        self.seen = {}
        self.counter = 0
    def _live(self, service, instance, ts):
        last = self.seen.get(service, {}).get(instance)
        return last is not None and ts < last + self.ttl
    def register(self, service, instance, ts):
        self.seen.setdefault(service, {})[instance] = ts
    def heartbeat(self, service, instance, ts):
        self.seen.setdefault(service, {})[instance] = ts
        return True
    def deregister(self, service, instance, ts):
        live = self._live(service, instance, ts)
        self.seen.get(service, {}).pop(instance, None)
        return live
    def lookup(self, service, ts):
        return sorted(i for i in self.seen.get(service, {}) if self._live(service, i, ts))
    def pick(self, service, ts):
        live = self.lookup(service, ts)
        self.counter += 1
        return live[(self.counter - 1) % len(live)] if live else None
''',
    ],
    guide=dict(
        prereqs="Service discovery from the lesson *Handling change*. Nested dictionaries; the modulo operator.",
        intuition="The registry does not know whether an instance is alive; it only knows when it last heard from it. Liveness is a comparison between the clock and that last-heard time, so nothing needs a background timer.",
        hints=[
            "Store `last_seen` per service and instance. Write one helper `_live(service, instance, ts)` and use it everywhere.",
            "Expiry is lazy: decide at read time with `ts < last_seen + ttl`. At exactly `last_seen + ttl` the instance is gone.",
            "Keep one round-robin counter per service and advance it only when an instance is returned.",
        ],
        brute_force="Sweep and delete all expired entries at the start of every call: O(total instances) per operation. It is correct, and many real registries run such a sweep on a timer, but the lazy check gives the same answers with less work.",
        approach="`seen[service][instance] = last_seen`. `register` writes the time. `heartbeat` refuses a non-live instance. `deregister` reports whether it was live, then removes it. `lookup` filters and sorts. `pick` indexes the sorted live list with the counter.\n\n**Dry run** of the example with ttl 10: `a` seen at 0, `b` at 3. At 9 both are live. At 10, `a` fails `10 < 0 + 10` and is gone. Its heartbeat at 11 returns False. `pick` at 11 sees `[b]`, counter 0 → `b`.",
        complexity="`register`, `heartbeat`, `deregister` O(1). `lookup` and `pick` O(k log k) for k instances of the service. Space O(total instances).",
        pitfalls="Using `<=` for liveness. Letting a heartbeat revive an expired instance. Sharing one counter between services. Advancing the counter when nothing is live.",
        follow_up="Round robin over a changing list is not perfectly even. Compare with least-connections balancing, and with DNS-based discovery where the cache time of a name plays the role of the TTL.",
    ),
),
dict(
    id="msvc-gateway-routes",
    title="API Gateway: Route Matching and Aggregation",
    difficulty="Medium",
    pattern="API Gateway",
    entry="handle",
    description=r"""
An API gateway receives a request, finds the matching route, calls the route's upstream services and merges their answers.

- `routes`: a list of `[method, pattern, services]`. `method` is an HTTP method or `"ANY"`. `pattern` is a path such as `/pets/{id}/visits`; a segment written `{name}` matches exactly one segment and captures it; a final segment `*` matches one or more remaining segments. `services` is a non-empty list of upstream service names.
- `responses`: a dict from service name to the dict that service returns, or to `None` if the call failed. A service missing from `responses` also counts as failed.

**Choosing a route.** A route is a candidate if its method equals the request method or is `"ANY"`, and its pattern matches the path. Among candidates pick the one with the most literal segments (segments that are neither `{name}` nor `*`); on a tie prefer a route without `*`; then prefer an exact method over `"ANY"`; then the earliest in the list.

**Answer.**

- No candidate → `{"status": 404}`
- Every upstream failed → `{"status": 502}`
- Otherwise → `{"status": 200, "params": {captured names}, "body": {service: response for each successful service}, "missing": [sorted names of failed services]}`

Paths and patterns start with `/` and have no trailing slash. The path `/` has zero segments.

**Example:** routes `[["GET", "/pets/{id}", ["patients", "billing"]]]`, responses `{"patients": {"name": "Miso"}, "billing": None}`, request `GET /pets/7` → `{"status": 200, "params": {"id": "7"}, "body": {"patients": {"name": "Miso"}}, "missing": ["billing"]}`
""",
    starter='''def handle(routes: List[list], responses: dict, method: str, path: str) -> dict:
    pass
''',
    solution='''def handle(routes, responses, method, path):
    segs = [s for s in path.split("/") if s]
    best = None
    for idx, (m, pattern, services) in enumerate(routes):
        if m != method and m != "ANY":
            continue
        pats = [s for s in pattern.split("/") if s]
        star = bool(pats) and pats[-1] == "*"
        fixed = pats[:-1] if star else pats
        if star:
            if len(segs) < len(fixed) + 1:
                continue
        elif len(segs) != len(fixed):
            continue
        params, literals, ok = {}, 0, True
        for p, s in zip(fixed, segs):
            if p.startswith("{") and p.endswith("}"):
                params[p[1:-1]] = s
            elif p == s:
                literals += 1
            else:
                ok = False
                break
        if not ok:
            continue
        key = (-literals, 1 if star else 0, 0 if m == method else 1, idx)
        if best is None or key < best[0]:
            best = (key, params, services)
    if best is None:
        return {"status": 404}
    _, params, services = best
    body, missing = {}, []
    for s in services:
        r = responses.get(s)
        if r is None:
            missing.append(s)
        else:
            body[s] = r
    if not body:
        return {"status": 502}
    return {"status": 200, "params": params, "body": body, "missing": sorted(set(missing))}
''',
    tests=[
        [[["GET", "/pets/{id}", ["patients", "billing"]]], {"patients": {"name": "Miso"}, "billing": None}, "GET", "/pets/7"],
        [[["GET", "/pets/{id}", ["patients"]]], {"patients": {"name": "Miso"}}, "POST", "/pets/7"],
        [[], {}, "GET", "/"],
        [[["GET", "/pets/{id}", ["patients"]]], {}, "GET", "/pets/7"],
        [[["GET", "/pets/{id}", ["a"]], ["GET", "/pets/new", ["b"]]], {"a": {"v": 1}, "b": {"v": 2}}, "GET", "/pets/new"],
        [[["GET", "/files/*", ["a"]], ["GET", "/files/{name}", ["b"]]], {"a": {"v": 1}, "b": {"v": 2}}, "GET", "/files/x"],
        [[["GET", "/files/*", ["a"]], ["GET", "/files/{name}", ["b"]]], {"a": {"v": 1}, "b": {"v": 2}}, "GET", "/files/x/y/z"],
        [[["GET", "/files/*", ["a"]]], {"a": {"v": 1}}, "GET", "/files"],
        [[["ANY", "/pets/{id}", ["a"]], ["GET", "/pets/{id}", ["b"]]], {"a": {"v": 1}, "b": {"v": 2}}, "GET", "/pets/3"],
        [[["ANY", "/pets/{id}", ["a"]], ["GET", "/pets/{id}", ["b"]]], {"a": {"v": 1}, "b": {"v": 2}}, "DELETE", "/pets/3"],
        [[["GET", "/", ["home"]]], {"home": {"ok": True}}, "GET", "/"],
        [[["GET", "/clinics/{clinic}/pets/{pet}", ["z", "a", "m"]]], {"m": {"x": 1}, "a": None}, "GET", "/clinics/north/pets/12"],
        [[["GET", "/a/{x}", ["one"]], ["GET", "/{y}/b", ["two"]]], {"one": {"r": 1}, "two": {"r": 2}}, "GET", "/a/b"],
        [[["GET", "/pets/{id}", ["a"]]], {"a": {"v": 1}}, "GET", "/pets/7/visits"],
    ],
    examples=2,
    wrong_solutions=[
        '''def handle(routes, responses, method, path):
    segs = [s for s in path.split("/") if s]
    for m, pattern, services in routes:
        if m != method and m != "ANY":
            continue
        pats = [s for s in pattern.split("/") if s]
        star = bool(pats) and pats[-1] == "*"
        fixed = pats[:-1] if star else pats
        if (star and len(segs) < len(fixed) + 1) or (not star and len(segs) != len(fixed)):
            continue
        params, ok = {}, True
        for p, s in zip(fixed, segs):
            if p.startswith("{"):
                params[p[1:-1]] = s
            elif p != s:
                ok = False
        if not ok:
            continue
        body = {s: responses[s] for s in services if responses.get(s) is not None}
        missing = sorted(s for s in services if responses.get(s) is None)
        if not body:
            return {"status": 502}
        return {"status": 200, "params": params, "body": body, "missing": missing}
    return {"status": 404}
''',
        '''def handle(routes, responses, method, path):
    segs = [s for s in path.split("/") if s]
    best = None
    for idx, (m, pattern, services) in enumerate(routes):
        if m != method and m != "ANY":
            continue
        pats = [s for s in pattern.split("/") if s]
        star = bool(pats) and pats[-1] == "*"
        fixed = pats[:-1] if star else pats
        if star:
            if len(segs) < len(fixed):
                continue
        elif len(segs) != len(fixed):
            continue
        params, literals, ok = {}, 0, True
        for p, s in zip(fixed, segs):
            if p.startswith("{") and p.endswith("}"):
                params[p[1:-1]] = s
            elif p == s:
                literals += 1
            else:
                ok = False
                break
        if not ok:
            continue
        key = (-literals, 1 if star else 0, 0 if m == method else 1, idx)
        if best is None or key < best[0]:
            best = (key, params, services)
    if best is None:
        return {"status": 404}
    _, params, services = best
    body = {s: responses[s] for s in services if responses.get(s) is not None}
    missing = sorted(s for s in services if responses.get(s) is None)
    return {"status": 200, "params": params, "body": body, "missing": missing}
''',
    ],
    guide=dict(
        prereqs="API gateways from the lesson *Handling change* and aggregation from *Gateways, backends for frontends and GraphQL*. Tuples as sort keys.",
        intuition="Routing is a specificity contest: the route that names more of the path literally is the better match. Aggregation is a merge that tolerates partial failure but not total failure.",
        hints=[
            "Split the path and each pattern into segments, dropping empty strings.",
            "Give each matching route a tuple such as `(-literals, has_star, method_is_any, index)` and keep the smallest tuple.",
            "After choosing, split the upstream answers into successes and failures; an empty success set means 502.",
        ],
        brute_force="Take the first route that matches. It is what many gateways do, and it forces people to order the route file carefully. The scoring rule here removes that ordering trap.",
        approach="For each route: check the method; handle the trailing `*` (needs at least one extra segment); compare segment by segment, capturing parameters and counting literals; score. Then aggregate.\n\n**Dry run** for `GET /pets/new` with routes `/pets/{id}` and `/pets/new`: the first matches with 1 literal, the second with 2. The second wins, so service `b` is called and `params` is empty.",
        complexity="Time O(R × S) for R routes and S segments; space O(S).",
        pitfalls="Letting `/files/*` match `/files`. Returning 200 with an empty body when every upstream failed. Forgetting services absent from `responses`. Taking the first match instead of the most specific.",
        follow_up="A general gateway should stay thin. When the merge logic becomes specific to one user interface, move it into a backend for frontend owned by that interface's team.",
    ),
),
dict(
    id="msvc-saga-orchestrator",
    title="Saga Orchestrator with Compensation",
    difficulty="Medium",
    pattern="Sagas",
    entry="run_saga",
    description=r"""
Simulate an orchestrated saga and return its log.

- `steps`: a list of dicts `{"name": str, "compensable": bool, "retries": int}` in execution order.
- `outcomes`: a dict from step name to a list of booleans: the results of successive attempts of that step's action. If the list is missing or used up, further attempts **succeed**.

The orchestrator runs the steps in order. For each step it tries the action up to `1 + retries` times, appending `"do:<name>:ok"` or `"do:<name>:fail"` for every attempt, and stops trying at the first success.

- If a step fails on all its attempts, the orchestrator compensates the steps that **completed earlier**, in reverse order: append `"undo:<name>"` for a compensable step and `"skip:<name>"` for a non-compensable one. Then append `"saga:aborted"` and stop. (The failed step itself is not compensated.)
- If every step succeeds, append `"saga:completed"`.

**Example:** steps `reserve_slot` (compensable), `take_deposit` (compensable), `send_email` (not compensable), all with 0 retries, and `outcomes = {"send_email": [False]}` → `["do:reserve_slot:ok", "do:take_deposit:ok", "do:send_email:fail", "undo:take_deposit", "undo:reserve_slot", "saga:aborted"]`
""",
    starter='''def run_saga(steps: List[dict], outcomes: Dict[str, List[bool]]) -> List[str]:
    pass
''',
    solution='''def run_saga(steps, outcomes):
    log, done = [], []
    used = {}
    for step in steps:
        name = step["name"]
        ok = False
        for _ in range(1 + step["retries"]):
            results = outcomes.get(name, [])
            i = used.get(name, 0)
            used[name] = i + 1
            ok = results[i] if i < len(results) else True
            log.append("do:%s:%s" % (name, "ok" if ok else "fail"))
            if ok:
                break
        if not ok:
            for prev in reversed(done):
                log.append(("undo:" if prev["compensable"] else "skip:") + prev["name"])
            log.append("saga:aborted")
            return log
        done.append(step)
    log.append("saga:completed")
    return log
''',
    tests=[
        [[{"name": "reserve_slot", "compensable": True, "retries": 0}, {"name": "take_deposit", "compensable": True, "retries": 0}, {"name": "send_email", "compensable": False, "retries": 0}],
         {"send_email": [False]}],
        [[{"name": "a", "compensable": True, "retries": 0}, {"name": "b", "compensable": True, "retries": 0}], {}],
        [[], {}],
        [[{"name": "a", "compensable": True, "retries": 0}], {"a": [False]}],
        [[{"name": "a", "compensable": True, "retries": 2}, {"name": "b", "compensable": True, "retries": 0}], {"a": [False, False, True]}],
        [[{"name": "a", "compensable": True, "retries": 2}, {"name": "b", "compensable": True, "retries": 0}], {"a": [False, False, False, True]}],
        [[{"name": "a", "compensable": False, "retries": 0}, {"name": "b", "compensable": True, "retries": 0}, {"name": "c", "compensable": True, "retries": 1}],
         {"c": [False, False]}],
        [[{"name": "a", "compensable": True, "retries": 0}, {"name": "b", "compensable": True, "retries": 0}, {"name": "c", "compensable": True, "retries": 0}],
         {"b": [False], "c": [False]}],
        [[{"name": "a", "compensable": True, "retries": 5}], {"a": [False, True, False]}],
        [[{"name": "a", "compensable": True, "retries": 1}, {"name": "b", "compensable": False, "retries": 1}, {"name": "c", "compensable": True, "retries": 0}, {"name": "d", "compensable": True, "retries": 0}],
         {"a": [False], "b": [False], "d": [False]}],
        [[{"name": "s%d" % i, "compensable": i % 3 != 0, "retries": i % 2} for i in range(12)], {"s11": [False, False], "s4": [True, False]}],
        [[{"name": "a", "compensable": True, "retries": 0}, {"name": "b", "compensable": True, "retries": 0}], {"zzz": [False]}],
    ],
    examples=1,
    wrong_solutions=[
        '''def run_saga(steps, outcomes):
    log, done = [], []
    for step in steps:
        name = step["name"]
        results = outcomes.get(name, [])
        ok = results[0] if results else True
        log.append("do:%s:%s" % (name, "ok" if ok else "fail"))
        if not ok:
            for prev in reversed(done):
                log.append(("undo:" if prev["compensable"] else "skip:") + prev["name"])
            log.append("saga:aborted")
            return log
        done.append(step)
    log.append("saga:completed")
    return log
''',
        '''def run_saga(steps, outcomes):
    log, done = [], []
    used = {}
    for step in steps:
        name = step["name"]
        ok = False
        done.append(step)
        for _ in range(1 + step["retries"]):
            results = outcomes.get(name, [])
            i = used.get(name, 0)
            used[name] = i + 1
            ok = results[i] if i < len(results) else True
            log.append("do:%s:%s" % (name, "ok" if ok else "fail"))
            if ok:
                break
        if not ok:
            for prev in done:
                log.append(("undo:" if prev["compensable"] else "skip:") + prev["name"])
            log.append("saga:aborted")
            return log
    log.append("saga:completed")
    return log
''',
    ],
    guide=dict(
        prereqs="Sagas from the lesson *Sagas: orchestration, choreography and compensation*. Loops with early exit.",
        intuition="A saga has no global undo. The orchestrator remembers which steps finished, and when a later step gives up, it walks that memory backwards, running each step's own reversal.",
        hints=[
            "Keep a list `done` of completed steps; append to it only after a step succeeds.",
            "Track how many attempt results you have consumed per step name; an exhausted list means success.",
            "On final failure iterate `reversed(done)` and choose the `undo:` or `skip:` prefix.",
        ],
        brute_force="There is no asymptotically different method. A common simpler but wrong version ignores retries and reads only the first outcome.",
        approach="Loop over steps. Inner loop of `1 + retries` attempts, logging each and breaking on success. On failure, compensate in reverse and return. Otherwise record the step.\n\n**Dry run** on the example: reserve ok, deposit ok, email fails once with no retries. Completed steps are reserve and deposit, so the log continues `undo:take_deposit`, `undo:reserve_slot`, `saga:aborted`.",
        complexity="Time O(total attempts + steps); space O(steps).",
        pitfalls="Compensating the step that failed. Compensating in forward order. Forgetting that attempts after the scripted list succeed. Logging nothing for non-compensable steps instead of `skip:`.",
        follow_up="Compensations can fail too. Real orchestrators retry them until they succeed, which is why a compensation must be idempotent.",
    ),
),
dict(
    id="msvc-saga-choreography",
    title="Choreographed Saga Event Trace",
    difficulty="Medium",
    pattern="Sagas",
    entry="trace_events",
    description=r"""
In a choreographed saga no one is in charge: each service listens for events and publishes new ones. Produce the trace of who handled what.

- `subscriptions`: a list of `[service, listens_to, on_success, on_failure]`. When the event `listens_to` is published, `service` handles it and then publishes `on_success`, or `on_failure` if the service is failing. Either may be `""`, meaning nothing is published.
- `start`: the first event published.
- `failing`: the list of services whose handling fails.

Process events in first-in, first-out order, starting with `start`. When an event is taken from the queue, every subscription listening to it reacts, in list order. Each reaction appends the string `"<event> -> <service> -> <published>"` to the trace, using `-` when nothing is published, and puts the published event (if any) at the back of the queue.

A given subscription (position in the list) reacts **at most once**; later publications of the same event skip it. This guarantees the trace ends.

Return the trace.

**Example:** subscriptions `[["billing", "Booked", "DepositTaken", "DepositFailed"], ["booking", "DepositFailed", "BookingCancelled", ""]]`, `start = "Booked"`, `failing = ["billing"]` → `["Booked -> billing -> DepositFailed", "DepositFailed -> booking -> BookingCancelled"]`
""",
    starter='''def trace_events(subscriptions: List[List[str]], start: str, failing: List[str]) -> List[str]:
    pass
''',
    solution='''def trace_events(subscriptions, start, failing):
    from collections import deque
    bad = set(failing)
    queue = deque([start])
    reacted = set()
    trace = []
    while queue:
        event = queue.popleft()
        for i, (service, listens, ok_event, fail_event) in enumerate(subscriptions):
            if listens != event or i in reacted:
                continue
            reacted.add(i)
            out = fail_event if service in bad else ok_event
            trace.append("%s -> %s -> %s" % (event, service, out or "-"))
            if out:
                queue.append(out)
    return trace
''',
    tests=[
        [[["billing", "Booked", "DepositTaken", "DepositFailed"], ["booking", "DepositFailed", "BookingCancelled", ""]], "Booked", ["billing"]],
        [[["billing", "Booked", "DepositTaken", "DepositFailed"], ["booking", "DepositFailed", "BookingCancelled", ""]], "Booked", []],
        [[], "Booked", []],
        [[["a", "X", "Y", ""]], "Nothing", []],
        [[["a", "X", "X", ""]], "X", []],
        [[["a", "X", "Y", ""], ["b", "Y", "X", ""]], "X", []],
        [[["billing", "Booked", "Paid", "PayFailed"], ["reminders", "Booked", "ReminderSet", ""], ["pharmacy", "Paid", "Held", "HoldFailed"],
          ["billing", "HoldFailed", "Refunded", ""], ["booking", "Refunded", "Cancelled", ""], ["reminders", "Cancelled", "", ""]], "Booked", ["pharmacy"]],
        [[["billing", "Booked", "Paid", "PayFailed"], ["reminders", "Booked", "ReminderSet", ""], ["pharmacy", "Paid", "Held", "HoldFailed"],
          ["billing", "HoldFailed", "Refunded", ""], ["booking", "Refunded", "Cancelled", ""], ["reminders", "Cancelled", "", ""]], "Booked", []],
        [[["a", "E", "F", "G"], ["b", "E", "F", "G"], ["c", "F", "", ""], ["d", "G", "", ""]], "E", ["b"]],
        [[["a", "E", "", "Oops"]], "E", ["a"]],
        [[["a", "E", "F", ""], ["a", "F", "G", ""], ["a", "G", "", ""]], "E", ["zzz"]],
        [[["s%d" % i, "e%d" % i, "e%d" % (i + 1), "fail"] for i in range(30)] + [["cleanup", "fail", "", ""]], "e0", ["s17"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def trace_events(subscriptions, start, failing):
    trace = []
    event = start
    seen = set()
    while event and event not in seen:
        seen.add(event)
        nxt = ""
        for service, listens, ok_event, fail_event in subscriptions:
            if listens == event:
                out = fail_event if service in failing else ok_event
                trace.append("%s -> %s -> %s" % (event, service, out or "-"))
                nxt = out
                break
        event = nxt
    return trace
''',
        '''def trace_events(subscriptions, start, failing):
    bad = set(failing)
    stack = [start]
    reacted = set()
    trace = []
    while stack:
        event = stack.pop()
        for i, (service, listens, ok_event, fail_event) in enumerate(subscriptions):
            if listens != event or i in reacted:
                continue
            reacted.add(i)
            out = fail_event if service in bad else ok_event
            trace.append("%s -> %s -> %s" % (event, service, out or "-"))
            if out:
                stack.append(out)
    return trace
''',
    ],
    guide=dict(
        prereqs="Choreography from the lesson *Sagas: orchestration, choreography and compensation*. A queue (`collections.deque`).",
        intuition="The flow of a choreographed saga is not written down in any one place. It emerges from the subscriptions. Following it means doing what a broker does: deliver each event to every listener and queue whatever they publish.",
        hints=[
            "Use a first-in, first-out queue of events, seeded with the start event.",
            "For each event loop over the subscriptions in order; remember by index which have already reacted.",
            "Pick `on_failure` when the service is in `failing`, and write `-` when the chosen event is empty.",
        ],
        brute_force="Follow only one listener per event in a straight line. This misses fan-out, where two services react to the same event, and that fan-out is the main reason people choose events.",
        approach="Breadth-first processing with a deque. A set of reacted indices prevents endless loops.\n\n**Dry run** on the example with billing failing: queue [Booked]. Billing listens, fails, publishes DepositFailed → trace line 1. Queue [DepositFailed]. Booking listens and publishes BookingCancelled → line 2. Nobody listens to BookingCancelled, so the trace ends.",
        complexity="Time O(E × S) for E published events and S subscriptions (an index from event to subscriptions makes it O(E + S)); space O(S).",
        pitfalls="Using a stack changes the order. Stopping after the first listener. Forgetting the once-per-subscription rule and looping forever on cycles.",
        follow_up="Compare the size of the subscription list with the equivalent orchestrator. The orchestrator is easier to read; the choreography is easier to extend without touching existing services.",
    ),
),
dict(
    id="msvc-outbox-delivery",
    title="Outbox Relay and the Idempotent Consumer",
    difficulty="Medium",
    pattern="Reliable Messaging",
    entry="relay_outbox",
    description=r"""
A service stores outgoing messages in an **outbox** table. A relay process forwards them to a broker in batches. The relay can crash after publishing a message but before recording that fact, so messages can be delivered more than once (at-least-once delivery). The consumer protects itself with an idempotency key: the message id.

- `outbox`: a list of `[message_id, amount]` in commit order. Ids are unique.
- `batch_size`: at least 1.
- `crashes`: a list of message ids. Each occurrence causes one crash.
- `dedupe`: whether the consumer remembers ids it has already applied.

**Relay loop.** While unsent messages remain: read the next `batch_size` unsent messages in order. Publish them one at a time. Immediately after publishing a message, if its id occurs in `crashes`, remove one occurrence and crash: the batch is **not** marked as sent and the loop restarts. If the whole batch is published without a crash, mark all its messages as sent.

**Consumer.** Messages arrive in publication order. If `dedupe` is true, a message whose id was already applied is dropped. Otherwise every message is applied. Applying adds `amount` to a running total.

Return `{"published": [ids in publication order], "applied": [ids in application order], "total": int, "dropped": int}`.

**Example:** `outbox = [["m1", 10], ["m2", 5]]`, `batch_size = 2`, `crashes = ["m2"]`, `dedupe = True` → published `["m1", "m2", "m1", "m2"]`, applied `["m1", "m2"]`, total `15`, dropped `2`.
""",
    starter='''def relay_outbox(outbox: List[list], batch_size: int, crashes: List[str], dedupe: bool) -> dict:
    pass
''',
    solution='''def relay_outbox(outbox, batch_size, crashes, dedupe):
    pending_crashes = {}
    for c in crashes:
        pending_crashes[c] = pending_crashes.get(c, 0) + 1
    published = []
    sent = 0
    while sent < len(outbox):
        batch = outbox[sent:sent + batch_size]
        crashed = False
        for mid, _ in batch:
            published.append(mid)
            if pending_crashes.get(mid, 0) > 0:
                pending_crashes[mid] -= 1
                crashed = True
                break
        if not crashed:
            sent += len(batch)
    amounts = {mid: amount for mid, amount in outbox}
    seen, applied, total, dropped = set(), [], 0, 0
    for mid in published:
        if dedupe and mid in seen:
            dropped += 1
            continue
        seen.add(mid)
        applied.append(mid)
        total += amounts[mid]
    return {"published": published, "applied": applied, "total": total, "dropped": dropped}
''',
    tests=[
        [[["m1", 10], ["m2", 5]], 2, ["m2"], True],
        [[["m1", 10], ["m2", 5]], 2, ["m2"], False],
        [[], 3, [], True],
        [[["m1", 10]], 1, [], True],
        [[["m1", 10], ["m2", 5], ["m3", 1]], 1, ["m2", "m2"], True],
        [[["m1", 10], ["m2", 5], ["m3", 1]], 1, ["m2", "m2"], False],
        [[["m1", 10], ["m2", 5], ["m3", 1], ["m4", 7]], 3, ["m3", "m1"], True],
        [[["m1", 10], ["m2", 5], ["m3", 1], ["m4", 7]], 3, ["m4"], False],
        [[["m1", 10], ["m2", 5]], 5, ["zzz"], True],
        [[["m1", -4], ["m2", 4], ["m3", 0]], 2, ["m1", "m3"], False],
        [[["id%d" % i, i] for i in range(40)], 7, ["id6", "id13", "id13", "id39"], True],
        [[["id%d" % i, i] for i in range(40)], 7, ["id6", "id13", "id13", "id39"], False],
    ],
    examples=2,
    wrong_solutions=[
        '''def relay_outbox(outbox, batch_size, crashes, dedupe):
    pending = list(crashes)
    published = []
    sent = 0
    while sent < len(outbox):
        mid = outbox[sent][0]
        published.append(mid)
        if mid in pending:
            pending.remove(mid)
            continue
        sent += 1
    amounts = dict((m, a) for m, a in outbox)
    seen, applied, total, dropped = set(), [], 0, 0
    for mid in published:
        if dedupe and mid in seen:
            dropped += 1
            continue
        seen.add(mid)
        applied.append(mid)
        total += amounts[mid]
    return {"published": published, "applied": applied, "total": total, "dropped": dropped}
''',
        '''def relay_outbox(outbox, batch_size, crashes, dedupe):
    pending = list(crashes)
    published = []
    sent = 0
    while sent < len(outbox):
        batch = outbox[sent:sent + batch_size]
        crashed = False
        for mid, _ in batch:
            published.append(mid)
            if mid in pending:
                pending.remove(mid)
                crashed = True
                break
        if not crashed:
            sent += len(batch)
    amounts = dict((m, a) for m, a in outbox)
    applied = list(dict.fromkeys(published))
    total = sum(amounts[m] for m in applied)
    return {"published": published, "applied": applied, "total": total, "dropped": len(published) - len(applied)}
''',
    ],
    guide=dict(
        prereqs="The outbox pattern and idempotency from the lessons on sagas and stability patterns. List slicing, sets.",
        intuition="The relay can only promise that every message is published at least once. Exactly-once *effect* comes from the receiving side: remember which ids you have processed and ignore repeats.",
        hints=[
            "Keep one number: how many messages from the start of the outbox are marked as sent.",
            "A crash means you leave that number unchanged and start the loop again, so the whole batch is published again.",
            "Simulate the consumer afterwards, walking the published list with a set of seen ids.",
        ],
        brute_force="Simulating message by message is already linear in the number of publications. The interesting part is getting the batch restart right, not speed.",
        approach="Count crashes per id in a dictionary. Loop while `sent < len(outbox)`: slice a batch, publish each id, crash if scheduled, otherwise advance `sent` by the batch length. Then run the consumer.\n\n**Dry run** on the example: batch [m1, m2]. Publish m1, publish m2, crash on m2. Restart with the same batch: publish m1, m2, no crash, mark sent. Published m1 m2 m1 m2. With dedupe the second pair is dropped: total 15, dropped 2.",
        complexity="Time O(P) where P is the number of publications, at most (crashes + 1) × batch size more than the outbox length; space O(n).",
        pitfalls="Marking messages sent one by one when the task says per batch. Treating a crash id as permanent instead of consuming one occurrence. Without dedupe the total is wrong, and that is the expected answer for that case.",
        follow_up="The set of seen ids must be stored in the same local transaction as the business change, otherwise the consumer has the same crash window the relay has.",
    ),
),
dict(
    id="msvc-two-phase-commit",
    title="Two-phase Commit Outcome with Failures",
    difficulty="Medium",
    pattern="Distributed Transactions",
    entry="two_phase_commit",
    description=r"""
Simulate a two-phase commit (2PC) and report where everyone ends up.

- `participants`: a list of `[name, vote]` where vote is `"yes"`, `"no"` or `"timeout"` (no answer).
- `coordinator_crash_after`: `None` if the coordinator does not crash. Otherwise an integer `k ≥ 0`: the coordinator records its decision and then crashes after delivering it to the first `k` participants in list order.
- `unreachable`: names of participants that never receive the phase-two message, even if the coordinator sends it.

**Phase 1 (prepare).** Every participant is asked. A `"yes"` voter moves to state `"prepared"` (it has promised to commit and holds its locks). A `"no"` or `"timeout"` participant is in state `"aborted"`.

**Decision.** `"commit"` if every vote is `"yes"`, otherwise `"abort"`. With no participants the decision is `"commit"`.

**Phase 2.** The coordinator sends the decision to participants in list order, stopping after `k` of them if it crashes. A participant that receives it and is not in `unreachable` moves to `"committed"` or `"aborted"`. A participant that does not receive it keeps its phase-1 state.

Return `{"decision": ..., "states": {name: state}, "blocked": [sorted names still "prepared"]}`.

**Example:** `[["booking", "yes"], ["billing", "yes"]]`, `coordinator_crash_after = 1`, `unreachable = []` → `{"decision": "commit", "states": {"booking": "committed", "billing": "prepared"}, "blocked": ["billing"]}`
""",
    starter='''def two_phase_commit(participants: List[List[str]], coordinator_crash_after: Optional[int], unreachable: List[str]) -> dict:
    pass
''',
    solution='''def two_phase_commit(participants, coordinator_crash_after, unreachable):
    states = {}
    for name, vote in participants:
        states[name] = "prepared" if vote == "yes" else "aborted"
    decision = "commit" if all(v == "yes" for _, v in participants) else "abort"
    limit = len(participants) if coordinator_crash_after is None else coordinator_crash_after
    lost = set(unreachable)
    for i, (name, _) in enumerate(participants):
        if i >= limit:
            break
        if name in lost:
            continue
        states[name] = "committed" if decision == "commit" else "aborted"
    blocked = sorted(n for n, s in states.items() if s == "prepared")
    return {"decision": decision, "states": states, "blocked": blocked}
''',
    tests=[
        [[["booking", "yes"], ["billing", "yes"]], 1, []],
        [[["booking", "yes"], ["billing", "yes"]], None, []],
        [[], None, []],
        [[["booking", "yes"], ["billing", "no"]], None, []],
        [[["booking", "yes"], ["billing", "timeout"], ["pharmacy", "yes"]], 0, []],
        [[["booking", "yes"], ["billing", "yes"], ["pharmacy", "yes"]], None, ["billing"]],
        [[["a", "yes"], ["b", "yes"], ["c", "no"], ["d", "yes"]], 1, ["a"]],
        [[["a", "yes"], ["b", "yes"], ["c", "yes"]], 0, []],
        [[["a", "no"]], None, ["a"]],
        [[["a", "yes"], ["b", "yes"], ["c", "yes"]], 99, ["c", "zzz"]],
        [[["z", "yes"], ["m", "yes"], ["a", "yes"]], 0, []],
        [[["p%d" % i, "yes" if i != 17 else "timeout"] for i in range(30)], 20, ["p3", "p25"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def two_phase_commit(participants, coordinator_crash_after, unreachable):
    decision = "commit" if all(v == "yes" for _, v in participants) else "abort"
    states = {name: ("committed" if decision == "commit" else "aborted") for name, _ in participants}
    return {"decision": decision, "states": states, "blocked": []}
''',
        '''def two_phase_commit(participants, coordinator_crash_after, unreachable):
    states = {}
    for name, vote in participants:
        states[name] = "prepared" if vote == "yes" else "aborted"
    decision = "commit" if all(v == "yes" for _, v in participants) else "abort"
    limit = coordinator_crash_after or len(participants)
    for i, (name, _) in enumerate(participants):
        if i >= limit or name in unreachable:
            continue
        states[name] = "committed" if decision == "commit" else "aborted"
    blocked = [n for n, s in states.items() if s == "prepared"]
    return {"decision": decision, "states": states, "blocked": blocked}
''',
    ],
    guide=dict(
        prereqs="Two-phase commit from the lesson *Transactions, ACID and why distributed transactions hurt*.",
        intuition="After voting yes, a participant has given up its right to decide. If the answer never arrives it is stuck holding locks. The simulation makes that stuck state visible as `prepared`.",
        hints=[
            "Compute the phase-1 state of every participant first.",
            "Decide with `all(...)`; a timeout counts as a no.",
            "Deliver the decision to the first `limit` participants, skipping unreachable ones; be careful that a crash value of 0 is not the same as `None`.",
        ],
        brute_force="There is nothing to optimise: one pass for votes and one for delivery. The traps are in the edge cases.",
        approach="1. `states[name] = prepared` for yes voters, else `aborted`. 2. Decision. 3. `limit` = all participants, or `k` on a crash. 4. For the first `limit` reachable participants set the final state. 5. Collect and sort the names still prepared.\n\n**Dry run** on the example: both prepared, decision commit, limit 1. Booking receives it → committed. Billing does not → prepared and blocked.",
        complexity="Time O(n log n) because of the sorted blocked list; space O(n).",
        pitfalls="Writing `crash or len(...)` treats 0 as no crash. A no voter is already aborted and can never be blocked. On an abort decision, yes voters that hear nothing are still blocked.",
        follow_up="The window between the two phases is why 2PC hurts across services: the system is briefly inconsistent, and locks are held across network calls. Sagas avoid the locks and accept visible intermediate states instead.",
    ),
),
]
