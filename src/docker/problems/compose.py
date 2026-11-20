_chain = {"s%03d" % i: (["s%03d" % (i + 1)] if i < 399 else []) for i in range(400)}

PROBLEMS = [
dict(
    id="docker-compose-start-order",
    title="Compose Start Order",
    difficulty="Medium",
    pattern="Docker Compose",
    entry="startOrder",
    description=r"""
`docker compose up` starts services so that every service comes after the services it depends on.
Write `startOrder(services)`.

`services` is a dict: service name → list of the names in its `depends_on` (duplicates may appear).

Return a list of all service names in start order, where:

- every service appears after all of its dependencies;
- whenever several services are ready to start, the **alphabetically smallest** name goes first (this makes the
  answer unique).

Return `[]` if a service depends on a name that is not defined, or if the dependencies contain a cycle
(a service that depends on itself is a cycle).

**Example 1:** `{"web": ["api"], "api": ["db", "cache"], "db": [], "cache": []}` → `["cache", "db", "api", "web"]`

**Example 2:** `{"a": ["b"], "b": ["a"]}` → `[]`
""",
    starter='''def startOrder(services):
    pass
''',
    solution='''import heapq

def startOrder(services):
    indeg = {s: 0 for s in services}
    dependants = {s: [] for s in services}
    for s, deps in services.items():
        for d in set(deps):
            if d not in services:
                return []
            indeg[s] += 1
            dependants[d].append(s)
    ready = [s for s in services if indeg[s] == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        s = heapq.heappop(ready)
        order.append(s)
        for t in dependants[s]:
            indeg[t] -= 1
            if indeg[t] == 0:
                heapq.heappush(ready, t)
    return order if len(order) == len(services) else []
''',
    tests=[
        [{"web": ["api"], "api": ["db", "cache"], "db": [], "cache": []}],
        [{"a": ["b"], "b": ["a"]}],
        [{}],
        [{"solo": []}],
        [{"self": ["self"]}],
        [{"api": ["db"], "worker": ["queue"]}],
        [{"z": [], "y": [], "x": []}],
        [{"api": ["db", "db", "db"], "db": []}],
        [{"web": ["api"], "api": ["db", "cache"], "worker": ["db", "cache"], "db": [], "cache": [], "migrate": ["db"]}],
        [{"a": [], "b": ["a"], "c": ["b"], "d": ["c", "e"], "e": ["d"]}],
        [{"b": ["z"], "a": ["z"], "z": [], "c": ["a", "b"]}],
        [_chain],
        [{"proxy": ["web", "api"], "web": ["api"], "api": ["db"], "db": [], "metrics": [], "grafana": ["metrics"]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def startOrder(services):
    order, seen = [], set()
    def visit(s):
        if s in seen or s not in services:
            return
        seen.add(s)
        for d in sorted(services[s]):
            visit(d)
        order.append(s)
    for s in sorted(services):
        visit(s)
    return order
''',
        '''def startOrder(services):
    indeg = {s: len(set(d)) for s, d in services.items()}
    for s, deps in services.items():
        for d in deps:
            if d not in services:
                return []
    order = []
    ready = [s for s in services if indeg[s] == 0]
    while ready:
        s = ready.pop(0)
        order.append(s)
        for t, deps in services.items():
            if s in deps:
                indeg[t] -= 1
                if indeg[t] == 0:
                    ready.append(t)
    return order if len(order) == len(services) else []
''',
    ],
    guide=dict(
        prereqs="Lesson *Compose fundamentals: services, projects and start order*. Graphs, in-degree, a min-heap (`heapq`).",
        intuition="A service can start once all of its dependencies have started. Count, for each service, how many dependencies are still "
                  "outstanding. Services at zero are ready. Starting one lowers the count of everything that depends on it. This is Kahn's algorithm "
                  "for topological sorting; the heap gives the alphabetical tie-break.",
        hints=[
            "Build the reverse map: for each service, who depends on it.",
            "Keep the ready services in a min-heap so that the smallest name is always popped next.",
            "If you finish with fewer services than you started with, the ones left over are stuck in a cycle.",
        ],
        brute_force="Repeatedly scan all services for one whose dependencies are all started, picking the smallest: O(n^2) or worse. Fine for a real Compose file, slow for the 400-service chain.",
        approach="1. In-degree and dependants (deduplicate `depends_on` with `set`).\n2. Heapify the zero in-degree services.\n3. Pop, append, decrement dependants, push those that reach zero.\n"
                 "4. Compare lengths to detect a cycle.\n\n**Dry run** (example 1): in-degrees web 1, api 2, db 0, cache 0. Heap `[cache, db]`. Pop cache → api 1. "
                 "Pop db → api 0, push. Pop api → web 0, push. Pop web. Order `[cache, db, api, web]`.",
        complexity="Time O((V + E) log V), space O(V + E).",
        pitfalls="- Counting a duplicated dependency twice, which leaves the in-degree above zero forever.\n- A depth-first search gives *a* valid order but not the "
                 "required tie-break, and needs explicit cycle detection.\n- Forgetting undefined names.\n- Recursion depth on long chains.",
        follow_up="Return the services grouped into waves that Compose could start in parallel, or name the services involved in the cycle.",
    ),
),
dict(
    id="docker-compose-merge",
    title="Merge Compose Override Files",
    difficulty="Medium",
    pattern="Docker Compose",
    entry="mergeServices",
    description=r"""
`docker compose -f base.yaml -f override.yaml` merges two files. Implement the rules for a subset.
`mergeServices(base, override)` takes the two `services` mappings (service name → dict of keys) and returns the
merged mapping. Do not modify the inputs.

A service present in only one input is copied unchanged, **except** that its `environment` is normalised (see below).
For a service in both, merge key by key; a key present on only one side is copied. For a key on both sides:

| Key | Rule |
|---|---|
| `environment` | Normalise each side to a dict, then merge per variable; override wins. |
| `ports`, `expose`, `dns`, `cap_add`, `cap_drop`, `profiles` | Concatenate base then override; drop duplicates, keeping the first occurrence. |
| `volumes` | Entries are strings `target`, `source:target` or `source:target:mode`. The identity of an entry is its **target**. An override entry replaces the base entry with the same target **in the same position**; other override entries are appended in order. |
| any other key, both values dicts | Merge recursively: keys on one side are copied; for keys on both sides, recurse if both are dicts, else override wins. |
| any other key | Override replaces base. |

**Normalising `environment`:** a dict stays as it is. A list of strings becomes a dict: `"K=V"` splits at the first
`=`; an item without `=` maps the name to `None`.

**Example:** base `{"api": {"image": "a:1", "environment": ["LOG=info", "TZ=UTC"], "ports": ["8000:8000"]}}`,
override `{"api": {"environment": {"LOG": "debug"}, "ports": ["9000:8000"]}}`
→ `{"api": {"image": "a:1", "environment": {"LOG": "debug", "TZ": "UTC"}, "ports": ["8000:8000", "9000:8000"]}}`
""",
    starter='''def mergeServices(base, override):
    pass
''',
    solution='''import copy

LISTS = {"ports", "expose", "dns", "cap_add", "cap_drop", "profiles"}

def _env(v):
    if isinstance(v, dict):
        return dict(v)
    out = {}
    for item in v:
        if "=" in item:
            k, val = item.split("=", 1)
            out[k] = val
        else:
            out[item] = None
    return out

def _target(entry):
    parts = entry.split(":")
    return parts[0] if len(parts) == 1 else parts[1]

def _deep(a, b):
    out = copy.deepcopy(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out

def _service(a, b):
    out = copy.deepcopy(a)
    if "environment" in out:
        out["environment"] = _env(out["environment"])
    for k, v in b.items():
        if k == "environment":
            env = dict(out.get("environment", {}))
            env.update(_env(v))
            out[k] = env
        elif k not in a:
            out[k] = copy.deepcopy(v)
        elif k in LISTS:
            merged = []
            for item in list(a[k]) + list(v):
                if item not in merged:
                    merged.append(item)
            out[k] = merged
        elif k == "volumes":
            merged = list(a[k])
            for entry in v:
                for i, old in enumerate(merged):
                    if _target(old) == _target(entry):
                        merged[i] = entry
                        break
                else:
                    merged.append(entry)
            out[k] = merged
        elif isinstance(a[k], dict) and isinstance(v, dict):
            out[k] = _deep(a[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out

def mergeServices(base, override):
    out = {}
    for name in list(base) + [n for n in override if n not in base]:
        out[name] = _service(base.get(name, {}), override.get(name, {}))
    return out
''',
    tests=[
        [{"api": {"image": "a:1", "environment": ["LOG=info", "TZ=UTC"], "ports": ["8000:8000"]}},
         {"api": {"environment": {"LOG": "debug"}, "ports": ["9000:8000"]}}],
        [{}, {}],
        [{"db": {"image": "postgres:16"}}, {}],
        [{}, {"db": {"image": "postgres:16", "environment": ["A=1", "PASS"]}}],
        [{"api": {"image": "a:1", "command": ["run", "--fast"]}}, {"api": {"image": "a:2", "command": ["run"]}}],
        [{"api": {"ports": ["80:80", "443:443"], "dns": ["1.1.1.1"]}}, {"api": {"ports": ["443:443", "81:80"], "dns": ["1.1.1.1"]}}],
        [{"api": {"volumes": ["data:/data", "./src:/app/src:ro", "/cache"]}},
         {"api": {"volumes": ["./local:/app/src", "/cache", "logs:/logs"]}}],
        [{"api": {"deploy": {"resources": {"limits": {"memory": "256M", "cpus": "0.5"}}, "replicas": 1}}},
         {"api": {"deploy": {"resources": {"limits": {"memory": "512M"}}, "replicas": 3}}}],
        [{"api": {"healthcheck": {"test": ["CMD", "a"], "interval": "5s"}}}, {"api": {"healthcheck": {"test": ["CMD", "b"]}}}],
        [{"api": {"environment": {"A": "1", "B": "2"}}}, {"api": {"environment": ["B=3", "C=x=y", "D"]}}],
        [{"api": {"image": "a"}, "db": {"image": "d"}}, {"cache": {"image": "c"}, "db": {"restart": "always"}}],
        [{"api": {"labels": {"a": "1"}, "restart": "no"}}, {"api": {"labels": ["b=2"], "restart": {"x": 1}}}],
        [{"api": {"environment": ["A=1"]}}, {"api": {"image": "x"}}],
        [{"api": {"cap_add": ["NET_ADMIN"], "profiles": ["debug"]}}, {"api": {"cap_add": ["SYS_TIME", "NET_ADMIN"], "expose": ["9000"]}}],
    ],
    examples=1,
    wrong_solutions=[
        '''def mergeServices(base, override):
    out = {k: dict(v) for k, v in base.items()}
    for name, svc in override.items():
        out.setdefault(name, {}).update(svc)
    return out
''',
        '''import copy

def mergeServices(base, override):
    def env(v):
        if isinstance(v, dict):
            return dict(v)
        return {i.split("=", 1)[0]: (i.split("=", 1)[1] if "=" in i else None) for i in v}
    def deep(a, b):
        out = copy.deepcopy(a)
        for k, v in b.items():
            if k == "environment":
                e = env(out.get(k, {})); e.update(env(v)); out[k] = e
            elif isinstance(out.get(k), dict) and isinstance(v, dict):
                out[k] = deep(out[k], v)
            elif isinstance(out.get(k), list) and isinstance(v, list):
                out[k] = out[k] + [x for x in v if x not in out[k]]
            else:
                out[k] = copy.deepcopy(v)
        if "environment" in out:
            out["environment"] = env(out["environment"])
        return out
    return {n: deep(base.get(n, {}), override.get(n, {})) for n in list(base) + [n for n in override if n not in base]}
''',
    ],
    guide=dict(
        prereqs="Lesson *Environment, configuration and override files* (merge rules). Recursion over nested dicts; `copy.deepcopy`.",
        intuition="There is no single merge rule: the right behaviour depends on what a key *means*. Scalars are replaced, mappings are combined per key, "
                  "some lists are unions, and volumes are keyed by where they are mounted. Write one small function per kind and dispatch on the key name.",
        hints=[
            "Normalise `environment` to a dict first; after that it is an ordinary per-key merge.",
            "For `volumes`, write a helper that extracts the target: the only field, or the second of two or three.",
            "`command` is a list but is not in the append set, so it must be replaced whole; do not treat every list alike.",
        ],
        brute_force="`dict.update` per service: one line, and wrong for every key that is a mapping or a list, because it throws the base value away.",
        approach="For each service name (base order, then new ones): deep-copy the base service, normalise its environment, then fold in each override key using the table.\n\n"
                 "**Dry run** volumes `['data:/data', './src:/app/src:ro', '/cache']` + `['./local:/app/src', '/cache', 'logs:/logs']`: targets of the base are "
                 "`/data`, `/app/src`, `/cache`. First override entry has target `/app/src` → replaces position 1. Second has `/cache` → replaces position 2 (same text). "
                 "Third `/logs` is new → appended. Result `['data:/data', './local:/app/src', '/cache', 'logs:/logs']`.",
        complexity="Time O(total size of both inputs) apart from the small quadratic duplicate checks on lists; space the same for the copy.",
        pitfalls="- Appending for *every* list (breaks `command`, `entrypoint`, `healthcheck.test`).\n- Replacing `ports` instead of appending.\n"
                 "- Splitting `K=V` on every `=` (values may contain `=`).\n- Mutating the inputs.\n- Forgetting to normalise `environment` for a service that exists in only one file.",
        follow_up="Support the `!override` and `!reset` tags, which force replacement or removal.",
    ),
),
dict(
    id="docker-env-substitution",
    title="Environment Precedence and Variable Substitution",
    difficulty="Hard",
    pattern="Docker Compose",
    entry="effectiveEnv",
    description=r"""
Compute the environment a Compose service's container really gets. Write
`effectiveEnv(image_env, env_file, environment, shell, dotenv)`. All arguments are dicts of strings, except that
values in `environment` may also be `None`.

**Step 1: interpolation.** Each string value in `environment` may contain variable references. A referenced variable
is looked up in `shell` first, then in `dotenv`; if it is in neither it is *unset*. A variable is *empty* if its
value is `""`.

| Syntax | Unset | Set but empty | Set and non-empty |
|---|---|---|---|
| `$NAME` or `${NAME}` | `""` | `""` | value |
| `${NAME:-text}` | `text` | `text` | value |
| `${NAME-text}` | `text` | `""` | value |
| `${NAME:?text}` | **error** | **error** | value |
| `${NAME?text}` | **error** | `""` | value |
| `${NAME:+text}` | `""` | `""` | `text` |
| `${NAME+text}` | `""` | `text` | `text` |
| `$$` | a literal `$` | | |

`NAME` is letters, digits and underscores, not starting with a digit (for the brace-less form take the longest such
run). `text` is everything up to the next `}` and is used literally (no nested substitution). A `$` that starts none
of these forms is kept as it is.

**Step 2: pass-through.** An `environment` entry whose value is `None` takes its value from `shell` only; if the name
is not in `shell` the entry is dropped.

**Step 3: precedence.** Start from `image_env`, overlay `env_file` (taken literally, no interpolation), then overlay
the processed `environment`.

Return the final dict. If any error occurs in step 1, return `{"ERROR": NAME}` for the first failing variable,
scanning `environment` in its insertion order and each value left to right.

**Example:** `image_env={"LOG":"warning","TZ":"UTC"}`, `env_file={"LOG":"info","DB":"db"}`,
`environment={"LOG":"${LEVEL:-debug}","TAG":"v${TAG}","HOME":None}`, `shell={"TAG":"2","HOME":"/root"}`, `dotenv={"TAG":"1"}`
→ `{"LOG":"debug","TZ":"UTC","DB":"db","TAG":"v2","HOME":"/root"}`
""",
    starter='''def effectiveEnv(image_env, env_file, environment, shell, dotenv):
    pass
''',
    solution='''import re

_PAT = re.compile(r"\\$\\$|\\$\\{([A-Za-z_][A-Za-z0-9_]*)(?:(:?[-?+])([^}]*))?\\}|\\$([A-Za-z_][A-Za-z0-9_]*)")

class _Missing(Exception):
    pass

def effectiveEnv(image_env, env_file, environment, shell, dotenv):
    def get(name):
        if name in shell:
            return True, shell[name]
        if name in dotenv:
            return True, dotenv[name]
        return False, ""

    def repl(m):
        if m.group(0) == "$$":
            return "$"
        name = m.group(1) or m.group(4)
        op, text = m.group(2), m.group(3) or ""
        is_set, value = get(name)
        if op is None:
            return value
        missing = (not is_set) or (op.startswith(":") and value == "")
        kind = op[-1]
        if kind == "-":
            return text if missing else value
        if kind == "?":
            if missing:
                raise _Missing(name)
            return value
        return "" if missing else text

    result = dict(image_env)
    result.update(env_file)
    processed = {}
    try:
        for key, value in environment.items():
            if value is None:
                if key in shell:
                    processed[key] = shell[key]
            else:
                processed[key] = _PAT.sub(repl, value)
    except _Missing as e:
        return {"ERROR": e.args[0]}
    for key in environment:
        if environment[key] is None and key not in shell:
            continue
        result[key] = processed[key]
    return result
''',
    tests=[
        [{"LOG": "warning", "TZ": "UTC"}, {"LOG": "info", "DB": "db"}, {"LOG": "${LEVEL:-debug}", "TAG": "v${TAG}", "HOME": None}, {"TAG": "2", "HOME": "/root"}, {"TAG": "1"}],
        [{}, {}, {}, {}, {}],
        [{"A": "img"}, {"A": "file"}, {}, {"A": "shell"}, {"A": "dot"}],
        [{"A": "img"}, {}, {"A": None}, {}, {"A": "dot"}],
        [{}, {"X": "${NOT_EXPANDED}"}, {"Y": "$X-${X}"}, {}, {"X": "1"}],
        [{}, {}, {"A": "${E:-d}", "B": "${E-d}", "C": "${U:-d}", "D": "${U-d}"}, {"E": ""}, {}],
        [{}, {}, {"A": "${E:+alt}", "B": "${E+alt}", "C": "${S:+alt}", "D": "${U+alt}"}, {"E": "", "S": "x"}, {}],
        [{}, {}, {"A": "ok", "B": "${NEED:?must be set}", "C": "${ALSO?x}"}, {}, {}],
        [{}, {}, {"A": "${E?fine}", "B": "${E:?boom}"}, {}, {"E": ""}],
        [{}, {}, {"PRICE": "$$5 and $$${CUR}", "ODD": "100% $ $1 ${}"}, {"CUR": "USD"}, {}],
        [{}, {}, {"URL": "postgres://${DB_USER:-app}:${DB_PASS:?required}@${DB_HOST-db}/x"}, {"DB_PASS": "s3"}, {"DB_USER": ""}],
        [{}, {}, {"A": "$FOO_BAR.$FOO-bar", "B": "${FOO}BAR"}, {"FOO": "f", "FOO_BAR": "fb"}, {}],
        [{"KEEP": "1"}, {"KEEP": "2", "ONLY": "f"}, {"KEEP": "${KEEP:-3}", "PASS": None, "GONE": None}, {"PASS": ""}, {}],
        [{}, {}, {"A": "${X:-a b:c-d}", "B": "${X:-}", "C": "${Y:-${X}}"}, {}, {}],
    ],
    examples=1,
    wrong_solutions=[
        '''import re

def effectiveEnv(image_env, env_file, environment, shell, dotenv):
    look = dict(dotenv); look.update(shell)
    out = dict(image_env); out.update(env_file)
    for k, v in environment.items():
        if v is None:
            if k in look:
                out[k] = look[k]
            continue
        def repl(m):
            name, default = m.group(1), m.group(3)
            val = look.get(name)
            return val if val else (default or "")
        out[k] = re.sub(r"\\$\\{?(\\w+)(:-([^}]*))?\\}?", repl, v)
    return out
''',
        '''import re

_P = re.compile(r"\\$\\$|\\$\\{([A-Za-z_][A-Za-z0-9_]*)(?:(:?[-?+])([^}]*))?\\}|\\$([A-Za-z_][A-Za-z0-9_]*)")

def effectiveEnv(image_env, env_file, environment, shell, dotenv):
    look = dict(shell); look.update(dotenv)
    err = []
    def repl(m):
        if m.group(0) == "$$":
            return "$"
        name = m.group(1) or m.group(4)
        op, text = m.group(2), m.group(3) or ""
        value = look.get(name, "")
        if op is None:
            return value
        missing = value == ""
        if op[-1] == "-":
            return text if missing else value
        if op[-1] == "?":
            if missing:
                err.append(name)
            return value
        return "" if missing else text
    out = dict(env_file); out.update(image_env)
    for k, v in environment.items():
        if v is None:
            if k in shell:
                out[k] = shell[k]
        else:
            out[k] = _P.sub(repl, v)
    return {"ERROR": err[0]} if err else out
''',
    ],
    guide=dict(
        prereqs="Lesson *Environment, configuration and override files*. Regular expressions with groups and a replacement function.",
        intuition="Two independent ideas are stacked. **Interpolation** rewrites text using the shell and `.env`, and its operators all ask the same "
                  "question: 'is the variable missing?', where the colon decides whether *empty* counts as missing. **Precedence** is then three "
                  "dictionary overlays in a fixed order.",
        hints=[
            "One regular expression with alternatives can find `$$`, `${NAME...}` and `$NAME`; pass a function to `re.sub`.",
            "Compute `missing = unset or (operator has ':' and value == '')` once, then switch on the last character of the operator.",
            "Raise an exception inside the replacement function for `?` and catch it outside to return the error dict.",
        ],
        brute_force="A hand-written character scanner works and is the right tool if nesting were required. Chained `str.replace` calls cannot work: "
                    "they cannot tell `$$` from `$` followed by a name, and they re-expand text that was just inserted.",
        approach="1. Build the result from `image_env`, then `env_file`.\n2. For each `environment` entry in order: pass-through or interpolate.\n3. Overlay.\n\n"
                 "**Dry run** `${DB_USER:-app}` with `dotenv = {'DB_USER': ''}`: set but empty; operator `:-` has a colon so it is missing → `app`. "
                 "`${DB_HOST-db}`: unset → `db`. `${DB_PASS:?required}` with shell value `s3` → `s3`. Result `postgres://app:s3@db/x`.",
        complexity="Time O(total length of the environment values), space O(size of the result).",
        pitfalls="- Giving `.env` priority over the shell.\n- Treating empty and unset alike for the operators without a colon.\n- Interpolating `env_file` values.\n"
                 "- Putting the image's `ENV` above `env_file`.\n- Dropping a pass-through whose shell value is the empty string (it is set, so it is kept).\n"
                 "- Expanding `$$NAME`.",
        follow_up="Allow nested references in the default text, as real Compose does: `${A:-${B}}`.",
    ),
),
dict(
    id="docker-dns-resolution",
    title="Container DNS Resolution",
    difficulty="Medium",
    pattern="Networking",
    entry="resolveName",
    description=r"""
Model Docker's embedded DNS on user-defined networks. Write `resolveName(containers, asker, name)`.

`containers` is a list of dicts:

```
{"name": "shop-api-1", "service": "api",
 "networks": {"front": {"ip": "172.21.0.3", "aliases": []},
              "back":  {"ip": "172.22.0.3", "aliases": ["backend"]}}}
```

The container named `asker` looks up `name`. A container `C` answers **on network `N`** when:

- the asker is attached to `N` and `C` is attached to `N`; and
- `name` equals `C`'s container name, or `C`'s service name, or one of `C`'s aliases **on `N`**.

Each such `(C, N)` contributes `C`'s IP address on `N`. The asker itself can answer.

Return the distinct IP addresses, sorted numerically by their four numbers. Return `[]` if `asker` is not a known
container name or nothing answers.

**Example:** with web on `front` (172.21.0.2), api on `front` (172.21.0.3) and `back` (172.22.0.3), db on `back`
(172.22.0.2, alias `postgres`): `resolveName(c, "shop-web-1", "db")` → `[]`,
`resolveName(c, "shop-api-1", "postgres")` → `["172.22.0.2"]`.
""",
    starter='''def resolveName(containers, asker, name):
    pass
''',
    solution='''def resolveName(containers, asker, name):
    me = next((c for c in containers if c["name"] == asker), None)
    if me is None:
        return []
    mine = set(me["networks"])
    ips = set()
    for c in containers:
        for net, info in c["networks"].items():
            if net not in mine:
                continue
            if name == c["name"] or name == c["service"] or name in info.get("aliases", []):
                ips.add(info["ip"])
    return sorted(ips, key=lambda ip: tuple(int(p) for p in ip.split(".")))
''',
    tests=[
        [[{"name": "shop-web-1", "service": "web", "networks": {"front": {"ip": "172.21.0.2", "aliases": []}}},
          {"name": "shop-api-1", "service": "api", "networks": {"front": {"ip": "172.21.0.3", "aliases": []}, "back": {"ip": "172.22.0.3", "aliases": []}}},
          {"name": "shop-db-1", "service": "db", "networks": {"back": {"ip": "172.22.0.2", "aliases": ["postgres"]}}}], "shop-web-1", "db"],
        [[{"name": "shop-web-1", "service": "web", "networks": {"front": {"ip": "172.21.0.2", "aliases": []}}},
          {"name": "shop-api-1", "service": "api", "networks": {"front": {"ip": "172.21.0.3", "aliases": []}, "back": {"ip": "172.22.0.3", "aliases": []}}},
          {"name": "shop-db-1", "service": "db", "networks": {"back": {"ip": "172.22.0.2", "aliases": ["postgres"]}}}], "shop-api-1", "postgres"],
        [[], "x", "y"],
        [[{"name": "a", "service": "a", "networks": {"n": {"ip": "10.0.0.2", "aliases": []}}}], "ghost", "a"],
        [[{"name": "a-1", "service": "a", "networks": {"n": {"ip": "10.0.0.2", "aliases": []}}}], "a-1", "a"],
        [[{"name": "w-1", "service": "w", "networks": {"n": {"ip": "10.0.0.10", "aliases": []}}},
          {"name": "w-2", "service": "w", "networks": {"n": {"ip": "10.0.0.9", "aliases": []}}},
          {"name": "w-3", "service": "w", "networks": {"n": {"ip": "10.0.0.100", "aliases": []}}},
          {"name": "c-1", "service": "c", "networks": {"n": {"ip": "10.0.0.2", "aliases": []}}}], "c-1", "w"],
        [[{"name": "api-1", "service": "api", "networks": {"front": {"ip": "172.21.0.3", "aliases": []}, "back": {"ip": "172.22.0.3", "aliases": []}}},
          {"name": "proxy-1", "service": "proxy", "networks": {"front": {"ip": "172.21.0.9", "aliases": []}, "back": {"ip": "172.22.0.9", "aliases": []}}}], "proxy-1", "api"],
        [[{"name": "api-1", "service": "api", "networks": {"front": {"ip": "172.21.0.3", "aliases": ["public"]}, "back": {"ip": "172.22.0.3", "aliases": ["internal"]}}},
          {"name": "db-1", "service": "db", "networks": {"back": {"ip": "172.22.0.2", "aliases": []}}}], "db-1", "public"],
        [[{"name": "api-1", "service": "api", "networks": {"front": {"ip": "172.21.0.3", "aliases": ["public"]}, "back": {"ip": "172.22.0.3", "aliases": ["internal"]}}},
          {"name": "db-1", "service": "db", "networks": {"back": {"ip": "172.22.0.2", "aliases": []}}}], "db-1", "internal"],
        [[{"name": "a", "service": "svc", "networks": {}}, {"name": "b", "service": "svc", "networks": {"n": {"ip": "10.1.1.1", "aliases": []}}}], "a", "svc"],
        [[{"name": "x-1", "service": "x", "networks": {"n1": {"ip": "10.2.0.5", "aliases": ["db"]}}},
          {"name": "y-1", "service": "db", "networks": {"n1": {"ip": "10.2.0.4", "aliases": []}, "n2": {"ip": "10.3.0.4", "aliases": []}}},
          {"name": "db", "service": "z", "networks": {"n2": {"ip": "10.3.0.7", "aliases": []}}},
          {"name": "q-1", "service": "q", "networks": {"n1": {"ip": "10.2.0.9", "aliases": []}}}], "q-1", "db"],
        [[{"name": "svc-%d" % i, "service": "svc", "networks": {"n": {"ip": "10.9.%d.%d" % (i // 250, i % 250 + 1), "aliases": []}}} for i in range(300)], "svc-7", "svc"],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolveName(containers, asker, name):
    ips = []
    for c in containers:
        for net, info in c["networks"].items():
            if name in (c["name"], c["service"]) or name in info.get("aliases", []):
                ips.append(info["ip"])
    return sorted(set(ips))
''',
        '''def resolveName(containers, asker, name):
    me = next((c for c in containers if c["name"] == asker), None)
    if me is None:
        return []
    mine = set(me["networks"])
    ips = set()
    for c in containers:
        aliases = [a for i in c["networks"].values() for a in i.get("aliases", [])]
        if name == c["name"] or name == c["service"] or name in aliases:
            for net, info in c["networks"].items():
                if net in mine:
                    ips.add(info["ip"])
    return sorted(ips, key=lambda ip: tuple(int(p) for p in ip.split(".")))
''',
    ],
    guide=dict(
        prereqs="Lesson *Container networking and DNS on user-defined networks*. Sets; sorting with a key function.",
        intuition="DNS in Docker is **per network**. Think of each network as its own phone book. The asker may only consult the phone books of "
                  "the networks it is attached to, and each book lists a container under its name, its service and the aliases given *for that network*.",
        hints=[
            "Find the asker first and take the set of its network names.",
            "Loop over every container and every one of its networks; skip networks the asker is not on.",
            "Sort IPs by `tuple(int(p) for p in ip.split('.'))`, not as strings.",
        ],
        brute_force="This direct scan is already the simple approach: O(containers x networks). An index from `(network, name)` to IPs would speed up many lookups.",
        approach="1. Locate the asker.\n2. For each `(container, network)` pair on a shared network, test the three name sources.\n3. Collect into a set, then sort numerically.\n\n"
                 "**Dry run** web asks for `db`: web is on `{front}`. db-1 is only on `back` → skipped. Nothing collected → `[]`. "
                 "api asks for `postgres`: api is on `{front, back}`; db-1 on `back` has alias `postgres` → `172.22.0.2`.",
        complexity="Time O(C x N x A) (containers, networks per container, aliases), plus O(k log k) to sort k answers. Space O(k).",
        pitfalls="- Ignoring network scoping, so every container can resolve every other.\n- Applying an alias from one network on another.\n"
                 "- String-sorting IPs (`10.0.0.10` before `10.0.0.9`).\n- Returning the same IP twice.",
        follow_up="Add Swarm's virtual IP mode, where a service name resolves to one stable address that load-balances.",
    ),
),
dict(
    id="docker-secret-audit",
    title="Audit Secrets and Config in a Compose File",
    difficulty="Medium",
    pattern="Configuration & Secrets",
    entry="auditCompose",
    description=r"""
Review a Compose file (already parsed into a dict) for the way it handles sensitive values.
Write `auditCompose(compose)` returning a sorted list of findings `[service, rule, name]`.

`compose` may have the keys `services` (name → service dict), `secrets` (name → definition) and
`configs` (name → definition). A service may have `environment` (a dict of name → string or `None`),
`secrets` (a list of secret names) and `configs` (a list of config names). Missing keys mean "empty".

A name is **sensitive** if, after upper-casing it and splitting on `_`, `-` and `.`, one of the parts is
`PASSWORD`, `PASSWD`, `SECRET`, `TOKEN`, `KEY`, `KEYS` or `CREDENTIALS`.

| Rule | Finding | When |
|---|---|---|
| `env-secret` | `[service, "env-secret", VAR]` | An environment variable with a sensitive name, whose name does not end in `_FILE`, and whose value is a non-empty string that does not contain `${`. |
| `secret-in-config` | `[service, "secret-in-config", config]` | The service uses a config whose name is sensitive. |
| `undefined-secret` | `[service, "undefined-secret", secret]` | The service lists a secret that is not defined in the top-level `secrets`. |
| `unused-secret` | `["", "unused-secret", secret]` | A top-level secret that no service lists. |

Sort the findings as lists (by service, then rule, then name).

**Example:** `{"services": {"api": {"environment": {"DB_PASSWORD": "hunter2", "DB_PASSWORD_FILE": "/run/secrets/db", "LOG": "info"}, "secrets": ["db"]}}, "secrets": {"db": {}, "old": {}}}`
→ `[["", "unused-secret", "old"], ["api", "env-secret", "DB_PASSWORD"]]`
""",
    starter='''def auditCompose(compose):
    pass
''',
    solution='''import re

WORDS = {"PASSWORD", "PASSWD", "SECRET", "TOKEN", "KEY", "KEYS", "CREDENTIALS"}

def _sensitive(name):
    return any(p in WORDS for p in re.split(r"[_.-]", name.upper()))

def auditCompose(compose):
    services = compose.get("services") or {}
    defined = compose.get("secrets") or {}
    used = set()
    out = []
    for sname, svc in services.items():
        for var, value in (svc.get("environment") or {}).items():
            if (_sensitive(var) and not var.upper().endswith("_FILE")
                    and isinstance(value, str) and value != "" and "${" not in value):
                out.append([sname, "env-secret", var])
        for cfg in svc.get("configs") or []:
            if _sensitive(cfg):
                out.append([sname, "secret-in-config", cfg])
        for sec in svc.get("secrets") or []:
            used.add(sec)
            if sec not in defined:
                out.append([sname, "undefined-secret", sec])
    for sec in defined:
        if sec not in used:
            out.append(["", "unused-secret", sec])
    out.sort()
    return out
''',
    tests=[
        [{"services": {"api": {"environment": {"DB_PASSWORD": "hunter2", "DB_PASSWORD_FILE": "/run/secrets/db", "LOG": "info"}, "secrets": ["db"]}}, "secrets": {"db": {}, "old": {}}}],
        [{}],
        [{"services": {}}],
        [{"services": {"api": {}}}],
        [{"services": {"api": {"environment": {"API_TOKEN": "${API_TOKEN}", "SECRET_KEY": "", "JWT_SECRET": None, "MONKEY": "banana", "KEYBOARD": "us"}}}}],
        [{"services": {"api": {"environment": {"aws.secret-key": "abc", "Api_Key": "k", "PUBLIC_KEYS": "x", "TOKENS": "many"}}}}],
        [{"services": {"web": {"configs": ["nginx-conf", "tls-private-key", "db.password"]}}, "configs": {"nginx-conf": {}, "tls-private-key": {}, "db.password": {}}}],
        [{"services": {"a": {"secrets": ["x", "y"]}, "b": {"secrets": ["y", "z"]}}, "secrets": {"y": {}, "w": {}}}],
        [{"services": {"zeta": {"environment": {"PASSWORD": "p"}}, "alpha": {"environment": {"TOKEN": "t", "PASSWD": "q"}}}}],
        [{"secrets": {"only": {"file": "./only.txt"}}}],
        [{"services": {"db": {"environment": {"POSTGRES_PASSWORD_FILE": "/run/secrets/pg", "POSTGRES_PASSWORD": "prefix-${PG}"}, "secrets": ["pg"]}}, "secrets": {"pg": {"file": "pg.txt"}}}],
        [{"services": {"api": {"environment": None, "secrets": None, "configs": None}}, "secrets": None}],
        [{"services": {"s%d" % i: {"environment": {"APP_SECRET": "v%d" % i}, "secrets": ["sec%d" % (i % 5)]} for i in range(30)}, "secrets": {"sec%d" % i: {} for i in range(7)}}],
    ],
    examples=1,
    wrong_solutions=[
        '''def auditCompose(compose):
    out = []
    services = compose.get("services") or {}
    defined = compose.get("secrets") or {}
    used = set()
    for sname, svc in services.items():
        for var, value in (svc.get("environment") or {}).items():
            if any(w in var.upper() for w in ("PASSWORD", "PASSWD", "SECRET", "TOKEN", "KEY", "CREDENTIALS")) and value:
                out.append([sname, "env-secret", var])
        for cfg in svc.get("configs") or []:
            if any(w in cfg.upper() for w in ("PASSWORD", "SECRET", "TOKEN", "KEY")):
                out.append([sname, "secret-in-config", cfg])
        for sec in svc.get("secrets") or []:
            used.add(sec)
            if sec not in defined:
                out.append([sname, "undefined-secret", sec])
    for sec in defined:
        if sec not in used:
            out.append(["", "unused-secret", sec])
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="Lesson *Configs and secrets*. Dictionaries with missing keys; `re.split`.",
        intuition="Each rule is a simple membership test once two helpers exist: 'is this name sensitive?' and 'which secrets are defined and which are used?'. "
                  "Matching whole **parts** of the name, not substrings, is what stops `MONKEY` and `KEYBOARD` from being flagged.",
        hints=[
            "Write `sensitive(name)` with `re.split(r'[_.-]', name.upper())` and a set of words.",
            "Use `x.get(key) or {}` (or `or []`) so that both a missing key and an explicit `None` behave as empty.",
            "Collect every secret name used by any service in a set while you loop; compare with the defined names at the end.",
        ],
        brute_force="Substring search for the sensitive words. It reports many false positives (`KEYBOARD`, `MONKEY`, `TOKENS` is not in the list) and misses nothing, "
                    "which makes the audit noisy enough that people stop reading it.",
        approach="One pass over the services applying the three per-service rules, one pass over defined secrets for the fourth, then sort.\n\n"
                 "**Dry run** (example): `DB_PASSWORD` → parts `DB`, `PASSWORD` → sensitive, literal value → finding. `DB_PASSWORD_FILE` ends in `_FILE` → skipped. "
                 "`LOG` not sensitive. Secret `db` is defined and used; `old` is defined, never used → `['', 'unused-secret', 'old']`. Sorting puts the empty service first.",
        complexity="Time O(total number of variables, configs and secrets), space O(number of secrets + findings).",
        pitfalls="- Substring matching.\n- Flagging `*_FILE` variables, which hold a path, not the secret.\n- Flagging `${VAR}` references, which carry no literal value.\n"
                 "- Crashing on `None` sections.\n- Forgetting to sort.",
        follow_up="Also flag secrets mounted into services that run as root, or environment values that look like high-entropy strings.",
    ),
),
]
