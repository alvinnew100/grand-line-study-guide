import random as _r

_r.seed(7)
_big_rows = []
for _i in range(3000):
    _big_rows.append({
        "id": _i if _i % 997 else 5,
        "age": None if _i % 501 == 0 else (_i * 37) % 140,
        "country": ["US", "DE", "FR", "XX", "IN"][_i % 5],
        "email": f"user{_i}@example.com" if _i % 333 else f"user{_i}-at-example",
    })

_big_train = [{"x": _r.gauss(10, 2), "y": _r.gauss(0, 1), "z": (None if _r.random() < 0.02 else _r.random())} for _ in range(2000)]
_big_serve = [{"x": _r.gauss(10.1, 2), "y": _r.gauss(0.9, 1), "z": (None if _r.random() < 0.2 else _r.random())} for _ in range(2000)]

PROBLEMS = [
dict(
    id="mlops-validate-rows",
    title="Data Validation Against Expectations",
    difficulty="Medium",
    pattern="Data Validation",
    entry="validate",
    description=r"""
Before a batch of data reaches training or a feature store, a **validation step** (think Great
Expectations, pandera, or TFDV) checks it against declared *expectations*. Implement a tiny
expectation engine.

`validate(rows, expectations)` receives:

- `rows`: a list of dicts (one per record). A key may be missing or have value `None`; both count as **null**.
- `expectations`: a list of dicts, each with a `"column"` and a `"type"`:

| type | extra keys | a row **fails** when... |
|---|---|---|
| `not_null` | — | the value is null |
| `between` | `min`, `max` | value is not null and not `min <= value <= max` |
| `in_set` | `values` | value is not null and not in `values` |
| `regex` | `pattern` | value is not null and `re.fullmatch(pattern, str(value))` is `None` |
| `unique` | — | value is not null and the same value appears in **another** row (every duplicate row fails) |

Nulls are ignored by every expectation except `not_null` (this mirrors how Great Expectations treats
missing values).

Return the list of failures as `[row_index, column, type]`, sorted by `row_index`, and for the same row
in the order the expectations were given.

**Example:**
```
rows = [{"age": 30}, {"age": -1}, {}]
expectations = [{"column": "age", "type": "not_null"},
                {"column": "age", "type": "between", "min": 0, "max": 120}]
-> [[1, "age", "between"], [2, "age", "not_null"]]
```
""",
    starter='''import re

def validate(rows, expectations):
    pass
''',
    solution='''import re
from collections import Counter

def validate(rows, expectations):
    counts = {}
    for e in expectations:
        if e["type"] == "unique":
            c = e["column"]
            counts[c] = Counter(r.get(c) for r in rows if r.get(c) is not None)
    out = []
    for i, r in enumerate(rows):
        for e in expectations:
            c, t = e["column"], e["type"]
            v = r.get(c)
            bad = False
            if t == "not_null":
                bad = v is None
            elif v is None:
                bad = False
            elif t == "between":
                bad = not (e["min"] <= v <= e["max"])
            elif t == "in_set":
                bad = v not in e["values"]
            elif t == "regex":
                bad = re.fullmatch(e["pattern"], str(v)) is None
            elif t == "unique":
                bad = counts[c][v] > 1
            if bad:
                out.append([i, c, t])
    return out
''',
    tests=[
        [[{"age": 30}, {"age": -1}, {}], [{"column": "age", "type": "not_null"}, {"column": "age", "type": "between", "min": 0, "max": 120}]],
        [[{"id": 1}, {"id": 2}, {"id": 1}, {"id": None}, {"id": None}], [{"column": "id", "type": "unique"}]],
        [[], [{"column": "a", "type": "not_null"}]],
        [[{"a": 1}], []],
        [[{"c": "US"}, {"c": "us"}, {"c": None}, {"c": "DE"}], [{"column": "c", "type": "in_set", "values": ["US", "DE"]}]],
        [[{"e": "a@b.co"}, {"e": "nope"}, {"e": "x@y.org"}, {"e": 12}], [{"column": "e", "type": "regex", "pattern": r"[^@\s]+@[^@\s]+\.[a-z]+"}]],
        [[{"x": 0}, {"x": 10}, {"x": 10.0001}, {"x": -0.0}], [{"column": "x", "type": "between", "min": 0, "max": 10}]],
        [[{"x": None, "y": 5}, {"y": 5}], [{"column": "y", "type": "unique"}, {"column": "x", "type": "not_null"}, {"column": "x", "type": "between", "min": 0, "max": 1}]],
        [[{"code": "A12"}, {"code": "A12x"}], [{"column": "code", "type": "regex", "pattern": r"A\d+"}]],
        [[{"a": 1, "b": 1}, {"a": 1, "b": 2}], [{"column": "b", "type": "unique"}, {"column": "a", "type": "unique"}]],
        [_big_rows, [
            {"column": "id", "type": "unique"},
            {"column": "age", "type": "not_null"},
            {"column": "age", "type": "between", "min": 0, "max": 120},
            {"column": "country", "type": "in_set", "values": ["US", "DE", "FR", "IN"]},
            {"column": "email", "type": "regex", "pattern": r"[^@]+@[^@]+\.[a-z]+"},
        ]],
    ],
    examples=2,
    wrong_solutions=[
        '''def validate(rows, expectations):
    out = []
    for i, r in enumerate(rows):
        for e in expectations:
            c, t = e["column"], e["type"]
            v = r.get(c)
            if t == "not_null" and v is None:
                out.append([i, c, t])
            elif t == "between" and (v is None or not (e["min"] <= v <= e["max"])):
                out.append([i, c, t])
    return out
''',
        '''import re
def validate(rows, expectations):
    out = []
    for i, r in enumerate(rows):
        for e in expectations:
            c, t = e["column"], e["type"]
            v = r.get(c)
            bad = False
            if t == "not_null":
                bad = v is None
            elif v is None:
                bad = False
            elif t == "between":
                bad = not (e["min"] <= v <= e["max"])
            elif t == "in_set":
                bad = v not in e["values"]
            elif t == "regex":
                bad = re.match(e["pattern"], str(v)) is None
            elif t == "unique":
                bad = any(rr.get(c) == v for rr in rows[:i])
            if bad:
                out.append([i, c, t])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Data validation and versioning*. Python dicts, `collections.Counter`, `re.fullmatch`.",
        intuition="Each expectation is a predicate over a single value, except `unique`, which needs a "
                  "**global** view of the column. Pre-compute value counts once, then every check is O(1) per row.",
        hints=[
            "Use `row.get(col)` so that missing keys and `None` behave the same.",
            "For `unique`, count non-null values per column before the main loop; a row fails if its value's count is > 1.",
            "Use `re.fullmatch`, not `re.match`: `match` only anchors at the start, so `A12x` would wrongly pass `A\\d+`.",
        ],
        brute_force="For `unique`, scan all other rows for each row: O(n²) per unique expectation — too slow for big batches.",
        approach="1. For each `unique` expectation, build `Counter` of non-null values.\n"
                 "2. Loop rows in order; inside, loop expectations in order (this yields the required sort order for free).\n"
                 "3. Evaluate: `not_null` checks for None; every other type first skips nulls, then applies its predicate.\n"
                 "4. Append `[i, column, type]` on failure.\n\n"
                 "Dry run on the example: row 0 (30) passes both; row 1 (-1) fails `between`; row 2 has no `age` → fails `not_null`, skipped by `between`.",
        complexity="Time O(R·E) plus O(R) per unique expectation; space O(R) for the counters.",
        pitfalls="- Treating `None` as failing `between`/`in_set` (double-reporting nulls).\n"
                 "- Marking only the *second* occurrence of a duplicate — every duplicate row should fail.\n"
                 "- `re.match` vs `re.fullmatch`.\n- Forgetting to `str()` the value before regex matching.",
        follow_up="Great Expectations adds a `mostly` parameter (pass if ≥ 95% of rows succeed). Add it and return a per-expectation success ratio.",
    ),
),
dict(
    id="mlops-feature-cache-key",
    title="Deterministic Cache Keys for Feature Vectors",
    difficulty="Medium",
    pattern="Serving & Caching",
    entry="cacheKeys",
    description=r"""
A prediction cache in front of a model must map *the same logical request* to *the same key*, no matter
how the client ordered its JSON fields — and it must **change** when the model version changes, or stale
predictions leak across deployments.

Implement `cacheKeys(model_version, rows)` that returns one key per feature dict in `rows`:

1. **Normalize** a feature dict:
   - drop keys whose value is `None`;
   - round every `float` (not `int`, not `bool`) to 6 decimals with `round(x, 6)`;
   - apply the same normalization recursively inside lists and nested dicts.
2. **Canonicalize**: `json.dumps({"v": model_version, "f": normalized}, sort_keys=True, separators=(",", ":"))`.
3. **Hash**: SHA-256 of the UTF-8 bytes, hex digest, first 16 characters.
4. The key is `f"{model_version}:{digest16}"`.

**Example:** `cacheKeys("v1", [{"a": 1, "b": 2.0}, {"b": 2.0000001, "a": 1}])` → two identical keys,
because key order is canonicalized and `2.0000001` rounds to `2.0`.
""",
    starter='''import hashlib, json

def cacheKeys(model_version, rows):
    pass
''',
    solution='''import hashlib, json

def _norm(x):
    if isinstance(x, bool):
        return x
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in x.items() if v is not None}
    if isinstance(x, list):
        return [_norm(v) for v in x]
    return x

def cacheKeys(model_version, rows):
    out = []
    for r in rows:
        canon = json.dumps({"v": model_version, "f": _norm(r)}, sort_keys=True, separators=(",", ":"))
        out.append(model_version + ":" + hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16])
    return out
''',
    tests=[
        ["v1", [{"a": 1, "b": 2.0}, {"b": 2.0000001, "a": 1}]],
        ["v2", [{"a": 1, "b": 2.0}]],
        ["v1", []],
        ["v1", [{}]],
        ["v1", [{"a": None, "b": 3}, {"b": 3}]],
        ["v1", [{"a": 1}, {"a": 1.0}, {"a": True}]],
        ["m-3.2.0", [{"emb": [0.1234567, 0.7654321], "meta": {"z": 1, "y": None, "x": 0.33333333}}]],
        ["v1", [{"city": "Zürich", "n": 5}]],
        ["v1", [{"a": [None, 1.23456789]}]],
        ["v9", [{"user": i, "score": i / 7} for i in range(200)]],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib, json
def cacheKeys(model_version, rows):
    return [model_version + ":" + hashlib.sha256(json.dumps({"v": model_version, "f": r}).encode()).hexdigest()[:16] for r in rows]
''',
        '''import hashlib, json
def _norm(x):
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in x.items() if v is not None}
    if isinstance(x, list):
        return [_norm(v) for v in x]
    return x
def cacheKeys(model_version, rows):
    out = []
    for r in rows:
        canon = json.dumps({"f": _norm(r)}, sort_keys=True, separators=(",", ":"))
        out.append(model_version + ":" + hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Model servers, batching, autoscaling and caching*. `json.dumps(sort_keys=True)`, `hashlib`.",
        intuition="A hash is only as stable as the bytes you feed it. Make the bytes canonical first: fixed key "
                  "order, fixed separators, fixed float precision, no optional nulls — then hash.",
        hints=[
            "Write a recursive `_norm` that handles dict, list, float, and leaves everything else alone.",
            "`bool` is a subclass of `int` in Python, so check `isinstance(x, bool)` before anything numeric.",
            "Include the model version inside the hashed payload as well as in the prefix.",
        ],
        brute_force="Using `str(dict)` as the key: depends on insertion order and float repr, so logically equal requests miss the cache.",
        approach="1. Normalize recursively (drop None values in dicts, round floats).\n2. Dump with `sort_keys=True` and compact separators.\n"
                 "3. SHA-256 → hex → slice 16 chars.\n4. Prefix with the version so you can also bulk-invalidate by prefix in Redis.",
        complexity="O(total size of the feature payload) per row.",
        pitfalls="- `None` *inside a list* is kept (only dict keys with None are dropped).\n- `1`, `1.0` and `True` serialize differently (`1`, `1.0`, `true`) and so get different keys — that is intended.\n"
                 "- Non-ASCII strings: `json.dumps` escapes them by default, which is fine as long as you are consistent.",
        follow_up="Add a TTL and an LRU bound (see `functools.lru_cache` or Redis `EXPIRE`). How would you avoid caching per-user personalised answers (see Huyen's data-leak warning)?",
    ),
),
dict(
    id="mlops-train-serve-skew",
    title="Training/Serving Skew Detector",
    difficulty="Medium",
    pattern="Monitoring & Drift",
    entry="skewReport",
    description=r"""
**Training/serving skew** happens when the features a model sees in production differ systematically from
the ones it was trained on — e.g. a unit change, a broken join that yields nulls, or a feature computed
differently online. Write a detector comparing a training sample to a serving sample.

`skewReport(train_rows, serve_rows, tolerance)`:

- Rows are dicts of **numeric** features. A missing key or `None` is a null.
- The features to check are the keys appearing in **any training row**.
- For each feature `f`, compute on each sample: null rate (nulls / number of rows) and, over non-null values,
  the mean and the **population** standard deviation (divide by N).
- Flag `f` with the **first** reason that applies, in this priority order:
  1. `"missing"` — `f` has no non-null values in `serve_rows` (includes empty `serve_rows`).
  2. `"null_rate"` — `|null_serve - null_train| > 0.05`.
  3. `"mean_shift"` — `|mean_serve - mean_train| > tolerance * std_train`. If `std_train == 0`, use
     `|mean_serve - mean_train| > 1e-9` instead.
- A feature with no non-null training values is skipped entirely.

Return `[[feature, reason], ...]` sorted by feature name.

**Example:** train `x` = 1,2,3 (mean 2, std≈0.816); serve `x` = 4,5,6 (mean 5) with `tolerance=1` → `[["x", "mean_shift"]]`.
""",
    starter='''def skewReport(train_rows, serve_rows, tolerance):
    pass
''',
    solution='''import math

def _stats(rows, f):
    vals = [r.get(f) for r in rows]
    nn = [v for v in vals if v is not None]
    null_rate = (len(vals) - len(nn)) / len(vals) if vals else 0.0
    if not nn:
        return null_rate, None, None
    m = sum(nn) / len(nn)
    sd = math.sqrt(sum((v - m) ** 2 for v in nn) / len(nn))
    return null_rate, m, sd

def skewReport(train_rows, serve_rows, tolerance):
    feats = set()
    for r in train_rows:
        feats.update(r.keys())
    out = []
    for f in sorted(feats):
        nt, mt, st = _stats(train_rows, f)
        if mt is None:
            continue
        ns, ms, ss = _stats(serve_rows, f)
        if ms is None:
            out.append([f, "missing"])
        elif abs(ns - nt) > 0.05:
            out.append([f, "null_rate"])
        elif (st == 0 and abs(ms - mt) > 1e-9) or (st > 0 and abs(ms - mt) > tolerance * st):
            out.append([f, "mean_shift"])
    return out
''',
    tests=[
        [[{"x": 1}, {"x": 2}, {"x": 3}], [{"x": 4}, {"x": 5}, {"x": 6}], 1],
        [[{"x": 1}, {"x": 2}, {"x": 3}], [{"x": 2}, {"x": 2.5}], 1],
        [[{"a": 1, "b": 2}], [], 1],
        [[], [{"a": 1}], 1],
        [[{"a": 1, "b": 5}, {"a": 2, "b": 5}], [{"a": 1}, {"a": 2}], 3],
        [[{"a": 5}, {"a": 5}], [{"a": 5}, {"a": 5.1}], 3],
        [[{"a": 5}, {"a": 5}], [{"a": 5}, {"a": 5}], 3],
        [[{"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}], [{"a": 1}, {"a": None}, {"a": 3}, {"a": 4}], 1],
        [[{"a": None}, {"a": None}], [{"a": 1}], 1],
        [[{"t": 20.0}, {"t": 22.0}, {"t": 21.0}], [{"t": 68.0}, {"t": 71.6}, {"t": 69.8}], 5],
        [[{"a": 1, "c": 1}, {"a": 3, "c": 3}], [{"a": 2, "c": 4}, {"a": 2, "c": 4}], 1],
        [_big_train, _big_serve, 0.25],
    ],
    examples=2,
    wrong_solutions=[
        '''import statistics
def skewReport(train_rows, serve_rows, tolerance):
    feats = set()
    for r in train_rows:
        feats.update(r.keys())
    out = []
    for f in sorted(feats):
        t = [r.get(f) for r in train_rows if r.get(f) is not None]
        s = [r.get(f) for r in serve_rows if r.get(f) is not None]
        if not t:
            continue
        if not s:
            out.append([f, "missing"]); continue
        sd = statistics.stdev(t) if len(t) > 1 else 0
        if abs(statistics.mean(s) - statistics.mean(t)) > tolerance * sd:
            out.append([f, "mean_shift"])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Feature stores, training/serving skew and labeling*; mean / standard deviation.",
        intuition="Skew shows up as (a) a feature that silently disappears, (b) more nulls than before, or (c) "
                  "a shifted distribution. Check the cheapest, most catastrophic signals first.",
        hints=[
            "Write a helper returning `(null_rate, mean, std)` for one feature over one sample.",
            "The null rate's denominator is *all* rows, including those where the key is missing.",
            "Population std: divide by N, not N-1. Handle `std_train == 0` separately.",
        ],
        brute_force="This is already linear; the 'naive' failure is conceptual — e.g. comparing only means and missing the null-rate explosion from a broken join.",
        approach="1. Collect feature names from training rows.\n2. For each (sorted) feature compute stats on both samples.\n"
                 "3. Apply the rules in priority order and record the first match.\n\nIn the Celsius→Fahrenheit test (`t`), the mean jumps from 21 to ~69.8 — a classic unit-change skew.",
        complexity="O(F · (T + S)) time, O(T + S) extra space per feature.",
        pitfalls="- Using sample std (N-1).\n- Dividing the null rate by the number of non-null rows.\n- Forgetting that serving rows may contain features not present in training (ignore them).",
        follow_up="Replace the mean-shift rule with PSI or a KS test per feature (see the monitoring module problems).",
    ),
),
dict(
    id="mlops-semver-bump",
    title="Model Registry Semantic Versioning",
    difficulty="Easy",
    pattern="Experiment Tracking & Registry",
    entry="nextVersions",
    description=r"""
Your team versions registered models with **semantic versions** `MAJOR.MINOR.PATCH`:

| change kind | meaning for a model | bump |
|---|---|---|
| `"schema"` | input/output signature changed — clients must update | MAJOR (`M+1.0.0`) |
| `"retrain"` | new weights, same signature | MINOR (`M.m+1.0`) |
| `"fix"` | metadata, preprocessing bug fix, no API change | PATCH (`M.m.p+1`) |

`nextVersions(existing, changes)`:

- `existing`: list of version strings already in the registry (unsorted, may be empty).
- `changes`: list of change kinds to register **in order**; each new version is computed from the
  **highest** version registered so far (including ones you just created).
- With an empty registry the base is `0.0.0`.

Return the list of newly created version strings.

Versions must be compared **numerically** (`0.10.0` > `0.9.0`).

**Example:** `nextVersions(["1.2.3", "1.10.0"], ["fix", "retrain", "schema"])` → `["1.10.1", "1.11.0", "2.0.0"]`
""",
    starter='''def nextVersions(existing, changes):
    pass
''',
    solution='''def nextVersions(existing, changes):
    cur = max((tuple(int(p) for p in v.split(".")) for v in existing), default=(0, 0, 0))
    out = []
    for c in changes:
        M, m, p = cur
        if c == "schema":
            cur = (M + 1, 0, 0)
        elif c == "retrain":
            cur = (M, m + 1, 0)
        else:
            cur = (M, m, p + 1)
        out.append("%d.%d.%d" % cur)
    return out
''',
    tests=[
        [["1.2.3", "1.10.0"], ["fix", "retrain", "schema"]],
        [[], ["fix"]],
        [[], ["retrain", "retrain"]],
        [[], ["schema"]],
        [["0.9.0", "0.10.0"], ["fix"]],
        [["2.0.0", "10.0.0", "9.9.9"], ["retrain"]],
        [["1.0.0"], []],
        [["3.4.5"], ["fix", "fix", "schema", "fix", "retrain"]],
        [["0.0.9", "0.0.10"], ["fix"]],
        [["1.2.3", "1.2.3"], ["fix"]],
        [[], ["fix"] * 120],
    ],
    examples=2,
    wrong_solutions=[
        '''def nextVersions(existing, changes):
    cur = max(existing, default="0.0.0")
    cur = tuple(int(p) for p in cur.split("."))
    out = []
    for c in changes:
        M, m, p = cur
        cur = (M + 1, 0, 0) if c == "schema" else (M, m + 1, 0) if c == "retrain" else (M, m, p + 1)
        out.append("%d.%d.%d" % cur)
    return out
''',
        '''def nextVersions(existing, changes):
    cur = max((tuple(int(p) for p in v.split(".")) for v in existing), default=(0, 0, 0))
    out = []
    for c in changes:
        M, m, p = cur
        cur = (M + 1, m, p) if c == "schema" else (M, m + 1, p) if c == "retrain" else (M, m, p + 1)
        out.append("%d.%d.%d" % cur)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Model registry, model cards and governance*.",
        intuition="Parse versions into integer tuples — Python compares tuples lexicographically, which is exactly semver precedence (ignoring pre-release tags).",
        hints=["`max(existing)` on strings is wrong: `'1.9.0' > '1.10.0'` as strings.", "Bumping MAJOR resets MINOR and PATCH; bumping MINOR resets PATCH.", "Use `max(..., default=(0,0,0))` for the empty registry."],
        brute_force="Sorting strings — subtly wrong once any component reaches two digits.",
        approach="Parse → max → for each change, bump the right component and reset the lower ones → format and append; keep the new tuple as the running maximum.",
        complexity="O(E + C).",
        pitfalls="- String comparison.\n- Not resetting lower components.\n- Duplicated versions in `existing` (harmless with `max`).",
        follow_up="Support pre-release tags like `2.0.0-rc.1` (they sort *before* `2.0.0`). MLflow itself uses monotonically increasing integer versions plus aliases such as `@champion` — discuss trade-offs.",
    ),
),
dict(
    id="mlops-champion-model",
    title="Pick the Champion Run",
    difficulty="Easy",
    pattern="Experiment Tracking & Registry",
    entry="pickChampion",
    description=r"""
After a hyperparameter sweep you have many tracked runs. Promote exactly one as the **champion**.

`pickChampion(runs, metric, mode)`:

- `runs`: list of dicts `{"run_id": str, "status": str, "start_time": int, "metrics": {name: float}}`.
- Only runs with `status == "FINISHED"` **and** containing `metric` in their metrics are eligible.
- `mode` is `"max"` (higher is better, e.g. AUC) or `"min"` (lower is better, e.g. RMSE).
- Ties on the metric (exact equality) are broken by:
  1. lower `metrics["latency_ms"]` (a run without `latency_ms` counts as infinitely slow),
  2. then earlier `start_time`,
  3. then lexicographically smaller `run_id`.

Return the champion's `run_id`, or `None` if no run is eligible.

**Example:** two FINISHED runs with AUC 0.91, latencies 12 and 9 → the one with latency 9 wins.
""",
    starter='''def pickChampion(runs, metric, mode):
    pass
''',
    solution='''def pickChampion(runs, metric, mode):
    best, best_key = None, None
    for r in runs:
        if r.get("status") != "FINISHED" or metric not in r.get("metrics", {}):
            continue
        v = r["metrics"][metric]
        key = (-v if mode == "max" else v, r["metrics"].get("latency_ms", float("inf")), r["start_time"], r["run_id"])
        if best_key is None or key < best_key:
            best, best_key = r["run_id"], key
    return best
''',
    tests=[
        [[{"run_id": "a", "status": "FINISHED", "start_time": 1, "metrics": {"auc": 0.91, "latency_ms": 12}},
          {"run_id": "b", "status": "FINISHED", "start_time": 2, "metrics": {"auc": 0.91, "latency_ms": 9}}], "auc", "max"],
        [[{"run_id": "a", "status": "FAILED", "start_time": 1, "metrics": {"rmse": 1.0}},
          {"run_id": "b", "status": "FINISHED", "start_time": 2, "metrics": {"rmse": 2.0}}], "rmse", "min"],
        [[], "auc", "max"],
        [[{"run_id": "a", "status": "RUNNING", "start_time": 1, "metrics": {"auc": 0.99}}], "auc", "max"],
        [[{"run_id": "a", "status": "FINISHED", "start_time": 1, "metrics": {"f1": 0.99}}], "auc", "max"],
        [[{"run_id": "x", "status": "FINISHED", "start_time": 5, "metrics": {"auc": 0.8}},
          {"run_id": "y", "status": "FINISHED", "start_time": 3, "metrics": {"auc": 0.8}}], "auc", "max"],
        [[{"run_id": "z", "status": "FINISHED", "start_time": 3, "metrics": {"auc": 0.8}},
          {"run_id": "y", "status": "FINISHED", "start_time": 3, "metrics": {"auc": 0.8}}], "auc", "max"],
        [[{"run_id": "a", "status": "FINISHED", "start_time": 1, "metrics": {"auc": 0.8}},
          {"run_id": "b", "status": "FINISHED", "start_time": 2, "metrics": {"auc": 0.8, "latency_ms": 50}}], "auc", "max"],
        [[{"run_id": "a", "status": "FINISHED", "start_time": 1, "metrics": {"rmse": 3.5}},
          {"run_id": "b", "status": "FINISHED", "start_time": 2, "metrics": {"rmse": 3.1}},
          {"run_id": "c", "status": "FINISHED", "start_time": 3, "metrics": {"rmse": 4.0}}], "rmse", "min"],
        [[{"run_id": "a", "status": "FINISHED", "start_time": 1, "metrics": {"rmse": 3.5}},
          {"run_id": "b", "status": "FINISHED", "start_time": 2, "metrics": {"rmse": 3.1}},
          {"run_id": "c", "status": "FINISHED", "start_time": 3, "metrics": {"rmse": 4.0}}], "rmse", "max"],
        [[{"run_id": "r%03d" % i, "status": "FINISHED" if i % 3 else "FAILED", "start_time": 1000 - i,
           "metrics": {"auc": round(0.5 + (i * 7 % 50) / 100, 2), "latency_ms": i % 17}} for i in range(300)], "auc", "max"],
    ],
    examples=2,
    wrong_solutions=[
        '''def pickChampion(runs, metric, mode):
    ok = [r for r in runs if metric in r["metrics"]]
    if not ok: return None
    f = max if mode == "max" else min
    return f(ok, key=lambda r: r["metrics"][metric])["run_id"]
''',
        '''def pickChampion(runs, metric, mode):
    ok = [r for r in runs if r["status"] == "FINISHED" and metric in r["metrics"]]
    if not ok: return None
    f = max if mode == "max" else min
    return f(ok, key=lambda r: r["metrics"][metric])["run_id"]
''',
    ],
    guide=dict(
        prereqs="Lesson *Experiment tracking with MLflow*.",
        intuition="Turn every eligibility rule into a filter and every preference into one component of a sort key. Then the champion is simply `min(key)`.",
        hints=["Negate the metric when `mode == 'max'` so a single `min` works for both modes.",
               "Use `float('inf')` as the default latency.", "The key tuple is `(±metric, latency, start_time, run_id)`."],
        brute_force="Sort all eligible runs with the composite key — O(n log n); fine, but a single pass is O(n).",
        approach="Filter by status and metric presence, build the composite key, keep the smallest key seen.",
        complexity="O(n) time, O(1) extra space.",
        pitfalls="- Including FAILED/RUNNING runs.\n- `max(..., key=metric)` returns the *first* max, ignoring the tie-break rules.\n- Exact float ties are rare in practice; real systems often add a tolerance band (e.g. within 0.001 AUC prefer the cheaper model).",
        follow_up="In MLflow: `mlflow.search_runs(filter_string=\"attributes.status = 'FINISHED'\", order_by=['metrics.auc DESC'])` then set the `champion` alias on the registered version.",
    ),
),
dict(
    id="mlops-downstream-impact",
    title="Who Is Affected by This Change?",
    difficulty="Easy",
    pattern="Lineage & Technical Debt",
    entry="impactedArtifacts",
    description=r"""
In a real ML platform, tables, feature sets and models feed each other. A **lineage graph** records
who reads whose output: the edge `["clicks_table", "ctr_features"]` means the job that builds
`ctr_features` reads `clicks_table`. The person who changes `clicks_table` often has no idea who reads
it: those readers are the **undeclared consumers** from the technical-debt lesson.

Write `impactedArtifacts(edges, changed)`:

- `edges`: a list of `[producer, consumer]` pairs (strings). It may contain duplicates, and it may
  contain cycles (a model whose predictions end up in its own training data is a **feedback loop**).
- `changed`: a list of artifact names that were just modified. A name may not appear in any edge.

An artifact is **impacted** when there is a path of **one or more** edges from some changed artifact to
it. Return all impacted artifacts as a list sorted alphabetically, without duplicates.

Note the "one or more edges": a changed artifact is itself in the answer only if another changed artifact
reaches it, or if it sits on a cycle (it feeds itself).

**Example:** `edges = [["raw", "clean"], ["clean", "features"], ["features", "model"], ["clean", "report"]]`,
`changed = ["clean"]` → `["features", "model", "report"]`

**Example (feedback loop):** `edges = [["model", "logs"], ["logs", "train_set"], ["train_set", "model"]]`,
`changed = ["logs"]` → `["logs", "model", "train_set"]`
""",
    starter='''def impactedArtifacts(edges, changed):
    # Build a map producer -> list of consumers, then walk it from every changed artifact.
    pass
''',
    solution='''def impactedArtifacts(edges, changed):
    readers = {}
    for producer, consumer in edges:
        readers.setdefault(producer, []).append(consumer)
    seen = set()
    stack = []
    for c in changed:
        stack.extend(readers.get(c, []))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(readers.get(node, []))
    return sorted(seen)
''',
    tests=[
        [[["raw", "clean"], ["clean", "features"], ["features", "model"], ["clean", "report"]], ["clean"]],
        [[["model", "logs"], ["logs", "train_set"], ["train_set", "model"]], ["logs"]],
        [[], ["anything"]],
        [[["a", "b"]], []],
        [[["a", "b"], ["b", "c"]], ["a", "b"]],
        [[["a", "a"]], ["a"]],
        [[["a", "b"], ["a", "b"], ["b", "c"], ["b", "c"]], ["a"]],
        [[["x", "y"]], ["ghost"]],
        [[["s", "m1"], ["s", "m2"], ["m1", "dash"], ["m2", "dash"], ["dash", "s"]], ["m1"]],
        [[["src", "f1"], ["src", "f2"], ["f1", "m"], ["f2", "m"], ["other", "o2"]], ["src", "other"]],
        [[["n%d" % i, "n%d" % (i + 1)] for i in range(3000)], ["n0"]],
        [[["n%d" % i, "n%d" % ((i + 1) % 2000)] for i in range(2000)], ["n500"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def impactedArtifacts(edges, changed):
    out = set()
    for p, c in edges:
        if p in changed:
            out.add(c)
    return sorted(out)
''',
        '''def impactedArtifacts(edges, changed):
    readers = {}
    for p, c in edges:
        readers.setdefault(p, []).append(c)
    seen = set(changed)
    stack = list(changed)
    while stack:
        n = stack.pop()
        for r in readers.get(n, []):
            if r not in seen:
                seen.add(r); stack.append(r)
    return sorted(seen)
''',
    ],
    guide=dict(
        prereqs="Lesson *Roles, teams and hidden technical debt* (undeclared consumers, feedback loops). Python dictionaries and lists.",
        intuition="This is reachability in a directed graph. Start from the changed artifacts, follow every \"is read by\" arrow, and collect everything you touch. A `seen` set stops you from going around a cycle forever.",
        hints=["First turn the edge list into a dictionary: producer -> list of consumers.",
               "Put the *consumers* of the changed artifacts on a stack (not the changed artifacts themselves), because a path needs at least one edge.",
               "Pop from the stack; if the node is new, record it and push its consumers. Stop when the stack is empty."],
        brute_force="Repeatedly scan the whole edge list, adding consumers of anything already marked, until a full pass adds nothing. Correct but O(E x V) in the worst case (a long chain).",
        approach="1. Build `readers[producer] = [consumers...]`.\n2. Seed a stack with `readers[c]` for every changed `c`.\n3. Iterative depth-first search with a `seen` set.\n4. Return `sorted(seen)`.\n\nDry run on the first example: stack = [features, report] -> pop report (new) -> pop features (new), push model -> pop model (new). seen = {features, model, report}.",
        complexity="Time O(V + E) because each edge is followed at most once per node discovery; space O(V + E) for the map and the set.",
        pitfalls="- Recursion on a 3,000-node chain can exceed Python's default recursion limit: use an explicit stack.\n- Adding the changed artifacts to `seen` up front hides feedback loops (a changed table that feeds itself must be reported).\n- Only looking at direct consumers misses the model three hops away, which is exactly the one that breaks silently.",
        follow_up="Real lineage tools (OpenLineage, Marquez, DataHub, the lineage view of a feature store) build this graph automatically from job metadata. A natural extension: return the impacted artifacts in an order that is safe to rebuild (topological order, see `mlops-dag-order`).",
    ),
),
dict(
    id="mlops-version-satisfies",
    title="Which Package Versions Are Allowed?",
    difficulty="Medium",
    pattern="Packaging",
    entry="allowedVersions",
    description=r"""
A Python project declares its dependencies with **version specifiers** such as `pandas>=2.2,<3`. Before
installing, a package installer such as `pip` lists the versions that exist and keeps only the ones the
specifier allows, then picks the newest. You will write that filtering step.

`allowedVersions(available, spec)`:

- `available`: a list of version strings made of dot-separated non-negative integers, such as `"2.2.1"`
  or `"3.0"`. Missing trailing parts count as zero, so `"3.0"` equals `"3.0.0"`. No two strings in one
  list are numerically equal.
- `spec`: clauses separated by commas, for example `">=1.4, <2.0, !=1.5.2"`. Spaces around clauses and
  operators may appear. An empty or blank `spec` allows everything. A version is allowed only if it
  passes **every** clause.

The operators:

| clause | allowed when |
|---|---|
| `==V` / `!=V` | version equals / differs from V (numeric comparison) |
| `>=V`, `<=V`, `>V`, `<V` | the usual numeric ordering |
| `==V.*` / `!=V.*` | the version starts / does not start with the parts of V (`==1.4.*` allows `1.4`, `1.4.0`, `1.4.9`, not `1.40`) |
| `~=V` | "compatible release": `>=V` **and** the version starts with V minus its last part. `~=2.2` means `>=2.2, ==2.*`; `~=1.4.5` means `>=1.4.5, ==1.4.*`. V always has at least two parts here. |

Compare versions **numerically**, part by part (`1.10` is newer than `1.9`). Return the allowed versions
sorted from **newest to oldest**.

**Example:** `allowedVersions(["1.9.0", "1.10.0", "2.0.0", "1.4.2"], ">=1.4,<2")` → `["1.10.0", "1.9.0", "1.4.2"]`

**Example:** `allowedVersions(["2.1", "2.2", "2.2.3", "2.9", "3.0"], "~=2.2")` → `["2.9", "2.2.3", "2.2"]`
""",
    starter='''def allowedVersions(available, spec):
    # Parse each version into a list of ints, check every clause, then sort newest first.
    pass
''',
    solution='''def allowedVersions(available, spec):
    def parse(v):
        return [int(p) for p in v.strip().split(".")]

    def cmp(a, b):
        n = max(len(a), len(b))
        a = a + [0] * (n - len(a))
        b = b + [0] * (n - len(b))
        return (a > b) - (a < b)

    def starts_with(v, prefix):
        return (v + [0] * len(prefix))[:len(prefix)] == prefix

    clauses = [c.strip() for c in spec.split(",") if c.strip()]

    def ok(v):
        pv = parse(v)
        for clause in clauses:
            for op in ("~=", "==", "!=", ">=", "<=", ">", "<"):
                if clause.startswith(op):
                    target = clause[len(op):].strip()
                    break
            if target.endswith(".*"):
                match = starts_with(pv, parse(target[:-2]))
                if op == "==" and not match:
                    return False
                if op == "!=" and match:
                    return False
                continue
            t = parse(target)
            r = cmp(pv, t)
            if op == "==" and r != 0:
                return False
            if op == "!=" and r == 0:
                return False
            if op == ">=" and r < 0:
                return False
            if op == "<=" and r > 0:
                return False
            if op == ">" and r <= 0:
                return False
            if op == "<" and r >= 0:
                return False
            if op == "~=" and (r < 0 or not starts_with(pv, t[:-1])):
                return False
        return True

    keep = [v for v in available if ok(v)]
    return sorted(keep, key=lambda v: parse(v) + [0] * (12 - len(parse(v))), reverse=True)
''',
    tests=[
        [["1.9.0", "1.10.0", "2.0.0", "1.4.2"], ">=1.4,<2"],
        [["2.1", "2.2", "2.2.3", "2.9", "3.0"], "~=2.2"],
        [["1.0", "2.0", "0.9"], ""],
        [["1.0", "2.0"], "   "],
        [[], ">=1.0"],
        [["1.4", "1.4.0.1", "1.4.9", "1.40.0", "1.5"], "==1.4.*"],
        [["1.4", "1.4.9", "1.40.0", "1.5"], "!=1.4.*"],
        [["1.4.4", "1.4.5", "1.4.9", "1.5.0", "2.0"], "~=1.4.5"],
        [["1.5.1", "1.5.2", "1.5.3"], ">= 1.4 , != 1.5.2"],
        [["3.0", "3.0.1", "2.9.9"], "==3"],
        [["3.0", "3.0.1", "2.9.9"], ">3.0"],
        [["3.0", "3.0.1", "2.9.9"], "<=3.0.0"],
        [["0.9", "0.10", "0.11", "0.2"], ">0.9"],
        [["1.0", "2.0", "3.0"], ">=2.0,<2.0"],
        [["%d.%d.%d" % (a, b, c) for a in range(3) for b in range(12) for c in range(6)], "~=1.3, !=1.7.*, <1.10"],
    ],
    examples=2,
    wrong_solutions=[
        '''def allowedVersions(available, spec):
    clauses = [c.strip() for c in spec.split(",") if c.strip()]
    def ok(v):
        for c in clauses:
            for op in ("~=", "==", "!=", ">=", "<=", ">", "<"):
                if c.startswith(op):
                    t = c[len(op):].strip(); break
            if op in (">=", "~=") and not v >= t: return False
            if op == "<=" and not v <= t: return False
            if op == ">" and not v > t: return False
            if op == "<" and not v < t: return False
            if op == "==" and v != t: return False
            if op == "!=" and v == t: return False
        return True
    return sorted([v for v in available if ok(v)], reverse=True)
''',
        '''def allowedVersions(available, spec):
    def parse(v):
        return [int(p) for p in v.strip().split(".")]
    def cmp(a, b):
        n = max(len(a), len(b)); a = a + [0] * (n - len(a)); b = b + [0] * (n - len(b))
        return (a > b) - (a < b)
    clauses = [c.strip() for c in spec.split(",") if c.strip()]
    def ok(v):
        pv = parse(v)
        for c in clauses:
            for op in ("~=", "==", "!=", ">=", "<=", ">", "<"):
                if c.startswith(op):
                    t = c[len(op):].strip(); break
            if t.endswith(".*"):
                m = (pv + [0] * 9)[:len(parse(t[:-2]))] == parse(t[:-2])
                if (op == "==") != m: return False
                continue
            r = cmp(pv, parse(t))
            if op in (">=", "~=") and r < 0: return False
            if op == "<=" and r > 0: return False
            if op == ">" and r <= 0: return False
            if op == "<" and r >= 0: return False
            if op == "==" and r != 0: return False
            if op == "!=" and r == 0: return False
        return True
    return sorted([v for v in available if ok(v)], key=lambda v: parse(v) + [0] * 9, reverse=True)
''',
    ],
    guide=dict(
        prereqs="Lesson *Python packaging, Makefiles and pre-commit* (version ranges vs lockfiles). Python lists compare element by element.",
        intuition="Turn every version into a list of integers padded with zeros. Python compares lists left to right, which is exactly version ordering. Every operator then becomes a comparison result (-1, 0 or +1) or a prefix check.",
        hints=["`\"1.10\" > \"1.9\"` is False for strings. Convert to `[1, 10]` and `[1, 9]` first.",
               "Pad the shorter list with zeros before comparing so `3.0` equals `3.0.0`.",
               "`~=2.2` is two checks: `>= 2.2` and \"starts with `[2]`\". Drop the last part of V to get the prefix."],
        brute_force="There is no slow-but-simple alternative worth writing: the work is in parsing correctly. The common wrong shortcut is comparing strings.",
        approach="1. Split `spec` on commas, strip, drop empty pieces.\n2. For each clause, find the operator (check two-character operators before `>` and `<`).\n3. Wildcard targets (`.*`) become prefix tests; others become a numeric compare.\n4. Keep versions passing every clause; sort by the padded integer list, newest first.\n\nDry run `~=2.2` on `2.9`: 2.9 >= 2.2 and [2, 9] starts with [2], so it is allowed. `3.0` fails the prefix test.",
        complexity="O(n x c x k) for n versions, c clauses and k parts per version, plus O(n log n) for the sort.",
        pitfalls="- Checking `>` before `>=` makes `>=1.4` parse as operator `>` with target `=1.4`.\n- Forgetting that `==1.4.*` must reject `1.40`: compare integer parts, not string prefixes.\n- `~=1.4.5` allows `1.4.9` but not `1.5.0`; `~=1.4` allows `1.5.0`. The prefix is V minus its last part.",
        follow_up="Real installers follow PEP 440, which adds pre-releases (`2.0rc1`), post-releases and local versions; the `packaging` library implements it (`SpecifierSet`). Lockfiles avoid this question at deploy time by pinning exact versions and hashes.",
    ),
),
dict(
    id="mlops-config-merge",
    title="Layered Configuration with Environment Overrides",
    difficulty="Medium",
    pattern="Configuration",
    entry="resolveConfig",
    description=r"""
A service that runs in dev, staging and production usually keeps one **base** configuration, a small
**overlay** file per environment holding only what differs, and lets **environment variables** (named
settings the operating system hands to a running program) override single values at deploy time.

Write `resolveConfig(base, overlay, env, prefix)` that returns `{"config": <final dict>, "ignored": <list>}`:

1. **Deep merge.** Start from `base` and apply `overlay`: when both sides hold a dictionary under the same
   key, merge those dictionaries recursively; otherwise the overlay value replaces the base value (lists
   are replaced whole, not merged). Keys only in one side are kept. Do **not** modify the inputs.
2. **Environment overrides.** Look at the variables in `env` (a dict of name -> string) in
   **alphabetical order of name**. Skip names that do not start with `prefix`. For the rest, remove the
   prefix, lowercase what is left and split it on a double underscore `__` to get a key path:
   `APP_FEATURE_STORE__TIMEOUT_MS` with prefix `APP_` -> `["feature_store", "timeout_ms"]`.
   - If that path leads, through dictionaries only, to an **existing key whose value is not a
     dictionary**, replace the value with the parsed string (rules below).
   - Otherwise (unknown key, a path through a non-dictionary, or a path ending on a dictionary) leave the
     config unchanged and add the variable name to `ignored`. Typos are caught this way instead of being
     silently accepted.
3. **Parsing env strings:** `"true"`/`"false"` in any letter case -> boolean; else if `int(s)` works ->
   integer; else if `float(s)` works -> float; else keep the string.

`ignored` lists names in the alphabetical order you processed them.

**Example:** `base = {"threshold": 0.5, "log_level": "INFO", "feature_store": {"timeout_ms": 50, "retries": 2}}`,
`overlay = {"log_level": "WARNING", "feature_store": {"timeout_ms": 30}}`,
`env = {"APP_THRESHOLD": "0.7", "APP_THRESHHOLD": "0.9", "HOME": "/root"}`, `prefix = "APP_"` ->
`{"config": {"threshold": 0.7, "log_level": "WARNING", "feature_store": {"timeout_ms": 30, "retries": 2}}, "ignored": ["APP_THRESHHOLD"]}`
""",
    starter='''def resolveConfig(base, overlay, env, prefix):
    # 1) deep-merge overlay into a COPY of base  2) apply env overrides  3) report ignored names
    pass
''',
    solution='''import copy

def resolveConfig(base, overlay, env, prefix):
    def merge(a, b):
        out = copy.deepcopy(a)
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = merge(out[k], v)
            else:
                out[k] = copy.deepcopy(v)
        return out

    def parse(s):
        low = s.lower()
        if low in ("true", "false"):
            return low == "true"
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            return s

    cfg = merge(base, overlay)
    ignored = []
    for name in sorted(env):
        if not name.startswith(prefix):
            continue
        path = name[len(prefix):].lower().split("__")
        node = cfg
        reachable = True
        for key in path[:-1]:
            if isinstance(node.get(key), dict):
                node = node[key]
            else:
                reachable = False
                break
        last = path[-1]
        if reachable and last in node and not isinstance(node[last], dict):
            node[last] = parse(env[name])
        else:
            ignored.append(name)
    return {"config": cfg, "ignored": ignored}
''',
    tests=[
        [{"threshold": 0.5, "log_level": "INFO", "feature_store": {"timeout_ms": 50, "retries": 2}},
         {"log_level": "WARNING", "feature_store": {"timeout_ms": 30}},
         {"APP_THRESHOLD": "0.7", "APP_THRESHHOLD": "0.9", "HOME": "/root"}, "APP_"],
        [{"a": 1}, {}, {}, "APP_"],
        [{}, {"new": {"x": 1}}, {}, "APP_"],
        [{"model": {"name": "gbm", "params": {"depth": 6, "lr": 0.1}}},
         {"model": {"params": {"lr": 0.05}}},
         {"APP_MODEL__PARAMS__DEPTH": "8", "APP_MODEL__PARAMS": "oops", "APP_MODEL__NAME__X": "1"}, "APP_"],
        [{"tags": ["a", "b"], "opts": {"k": 1}}, {"tags": ["c"], "opts": 5}, {}, "X_"],
        [{"debug": False, "workers": 2, "ratio": 0.5, "name": "svc"}, {},
         {"SVC_DEBUG": "TRUE", "SVC_WORKERS": "-4", "SVC_RATIO": "1e-3", "SVC_NAME": "12abc"}, "SVC_"],
        [{"x": {"y": 1}}, {"x": None}, {"APP_X__Y": "2"}, "APP_"],
        [{"x": 1}, {}, {"APP_X": "2", "app_x": "3", "APPX": "4"}, "APP_"],
        [{"retries": 3}, {}, {"APP_RETRIES": "3.0"}, "APP_"],
        [{"a": {"b": {"c": {"d": 1}}}}, {"a": {"b": {"c": {"e": 2}}}}, {"P_A__B__C__D": "false", "P_A__B__Z": "1"}, "P_"],
        [{"k%d" % i: {"v": i} for i in range(300)}, {"k%d" % i: {"w": -i} for i in range(0, 300, 3)},
         {"C_K%d__V" % i: str(i * 10) for i in range(0, 300, 7)}, "C_"],
    ],
    examples=1,
    wrong_solutions=[
        '''def resolveConfig(base, overlay, env, prefix):
    cfg = dict(base)
    cfg.update(overlay)
    ignored = []
    for name in sorted(env):
        if not name.startswith(prefix):
            continue
        path = name[len(prefix):].lower().split("__")
        node = cfg
        for key in path[:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = env[name]
    return {"config": cfg, "ignored": ignored}
''',
        '''import copy
def resolveConfig(base, overlay, env, prefix):
    def merge(a, b):
        out = copy.deepcopy(a)
        for k, v in b.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
        return out
    cfg = merge(base, overlay)
    ignored = []
    for name in sorted(env):
        if not name.startswith(prefix):
            continue
        path = name[len(prefix):].lower().split("__")
        node = cfg
        ok = True
        for key in path[:-1]:
            if isinstance(node.get(key), dict): node = node[key]
            else: ok = False; break
        if ok and path[-1] in node and not isinstance(node[path[-1]], dict):
            node[path[-1]] = env[name]
        else:
            ignored.append(name)
    return {"config": cfg, "ignored": ignored}
''',
    ],
    guide=dict(
        prereqs="Lesson *Linux shell essentials and configuration management* (layered configuration, environment variables). Python dictionaries and recursion.",
        intuition="Configuration is a tree of dictionaries. Merging walks both trees together and lets the more specific layer win at each leaf. An environment variable is a path into that tree written as one string.",
        hints=["Write a recursive `merge(a, b)` that copies `a` and, key by key, either recurses (both values are dicts) or replaces.",
               "`copy.deepcopy` protects the caller's dictionaries from being changed.",
               "Walk the env path one key at a time; the moment a step is not a dictionary, the variable is ignored."],
        brute_force="A shallow `dict.update` looks like it works on flat configs but wipes out sibling keys in nested sections (`feature_store.retries` disappears).",
        approach="1. `cfg = merge(base, overlay)` with deep copies.\n2. For each env name in sorted order with the prefix: build the path, walk intermediate keys (must be dicts), and require the final key to exist with a non-dict value.\n3. Parse the string (bool, then int, then float, then string) and assign; otherwise record the name in `ignored`.",
        complexity="O(size of base + overlay) for the merge plus O(E x depth) for E environment variables (and O(E log E) to sort them).",
        pitfalls="- Shallow merge loses nested keys.\n- Mutating `base` (tests may reuse it).\n- Creating new keys from env variables: a typo like `APP_THRESHHOLD` would silently do nothing useful. Report it instead.\n- Parse order matters: `\"3\"` must become the int 3, not the float 3.0; `\"TRUE\"` must become a boolean.",
        follow_up="`pydantic-settings` implements this pattern (with `env_nested_delimiter=\"__\"`) and validates types against a schema; Hydra and OmegaConf do deep merging of YAML layers and command-line overrides such as `model.params.lr=0.05`.",
    ),
),
dict(
    id="mlops-hash-split",
    title="Stable Train/Test Split by Hashing",
    difficulty="Easy",
    pattern="Reproducibility",
    entry="assignSplits",
    description=r"""
A random train/test split changes every time new rows arrive: a customer who was in the test set last
month can land in the training set this month, and your evaluation quietly leaks. A common fix is to
decide each row's split from a **hash** of its ID. A hash function turns any text into a big number that
looks random but is always the same for the same input, so the decision never changes.

Write `assignSplits(ids, test_pct, salt)`:

- For each ID (a string), build the text `salt + ":" + id`, encode it as UTF-8, compute its MD5 digest
  with Python's `hashlib.md5(...).hexdigest()`, read that hexadecimal string as an integer
  (`int(hex_string, 16)`) and take the remainder modulo 100. Call this the bucket (0 to 99).
- The row goes to `"test"` if `bucket < test_pct`, otherwise to `"train"`.
- `test_pct` is an integer from 0 to 100. The **salt** is a short string that lets you draw a different
  but still reproducible split for a new project.

Return the list of `"train"` / `"test"` labels in the same order as `ids`. Repeated IDs must get the same
label every time they appear.

**Example:** `assignSplits(["cust-1", "cust-2", "cust-3", "cust-4"], 50, "v1")` -> `["train", "test", "train", "train"]`

With only four IDs the split is not exactly 50/50; over thousands of IDs the share of `"test"` gets close to `test_pct` percent.
""",
    starter='''import hashlib

def assignSplits(ids, test_pct, salt):
    # bucket = int(hashlib.md5((salt + ":" + id).encode("utf-8")).hexdigest(), 16) % 100
    pass
''',
    solution='''import hashlib

def assignSplits(ids, test_pct, salt):
    out = []
    for i in ids:
        digest = hashlib.md5((salt + ":" + i).encode("utf-8")).hexdigest()
        bucket = int(digest, 16) % 100
        out.append("test" if bucket < test_pct else "train")
    return out
''',
    tests=[
        [["cust-1", "cust-2", "cust-3", "cust-4"], 50, "v1"],
        [["a", "b", "c"], 0, "s"],
        [["a", "b", "c"], 100, "s"],
        [[], 20, "s"],
        [["same", "same", "same", "other"], 30, "x"],
        [["cust-1", "cust-2", "cust-3", "cust-4"], 50, "v2"],
        [["user-%d" % i for i in range(40)], 25, ""],
        [["ü-ñ-é", "日本", "plain"], 50, "unicode"],
        [["row%d" % i for i in range(5000)], 20, "churn-2025"],
    ],
    examples=2,
    wrong_solutions=[
        '''import random
def assignSplits(ids, test_pct, salt):
    rng = random.Random(salt)
    return ["test" if rng.random() * 100 < test_pct else "train" for _ in ids]
''',
        '''import hashlib
def assignSplits(ids, test_pct, salt):
    out = []
    for i in ids:
        b = int(hashlib.md5((salt + ":" + i).encode("utf-8")).hexdigest(), 16) % 100
        out.append("test" if b <= test_pct else "train")
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Reproducibility: seeds, environments and lineage*. Python's `hashlib` module.",
        intuition="A random split depends on the order and number of rows. A hash split depends only on the row's own ID, so adding rows never moves old rows between train and test, and anyone can recompute the split.",
        hints=["`hashlib.md5(text.encode(\"utf-8\")).hexdigest()` gives a 32-character hex string.",
               "`int(hex_string, 16)` reads it as a (large) integer; `% 100` gives a bucket from 0 to 99.",
               "Strictly less than: `bucket < test_pct`, so 0 means no test rows and 100 means all rows."],
        brute_force="Shuffling with a seeded random generator is reproducible only while the data stays identical; one new row reshuffles everything. That is the bug this method avoids.",
        approach="Loop over the IDs, compute the bucket from the salted MD5, compare with `test_pct`, collect labels.",
        complexity="O(n x L) where L is the average ID length (hashing reads every character).",
        pitfalls="- Python's built-in `hash()` of a string is randomised per process (unless `PYTHONHASHSEED` is set), so it is NOT stable across runs.\n- Using `<=` puts 1% too many rows in test and makes `test_pct=0` produce some test rows.\n- Splitting by row when several rows belong to one customer leaks that customer into both sets: hash the customer ID, not the row number.",
        follow_up="Time-based splits are better when the future must be predicted from the past (fraud, churn); hash splits are for stable random holdouts. The same trick assigns users to A/B test arms deterministically.",
    ),
),
dict(
    id="mlops-slice-gate",
    title="Promotion Gate with Slice Checks",
    difficulty="Medium",
    pattern="Promotion Gates",
    entry="promotionGate",
    description=r"""
Before a newly trained model (the **candidate**) may replace the model in production (the **champion**),
an automated **gate** compares their offline metrics. An average can improve while one group of users,
a **slice** such as customers on the basic plan, gets worse, so the gate checks slices too.

Metrics arrive as dictionaries. The overall metric uses its plain name (`"pr_auc"`); slice metrics use the
name, two underscores and the slice, for example `"pr_auc__plan=basic"`.

Write `promotionGate(candidate, champion, metric, min_overall, max_slice_drop)` returning a list of
failure reasons (an empty list means the candidate passes):

1. If `candidate[metric] < min_overall`: add `"below floor"`.
2. If `champion` is not `None` and `candidate[metric] < champion[metric]`: add `"worse than champion"`.
3. If `champion` is not `None`, for every key of `champion` that starts with `metric + "__"`, in
   alphabetical order of key:
   - if the key is missing from `candidate`: add `"missing: " + key`;
   - else if `champion[key] - candidate[key] > max_slice_drop`: add `"regressed: " + key`.

Keys for other metrics (for example `"brier"` or `"roc_auc__plan=pro"` when `metric` is `"pr_auc"`) are
ignored. Slices that exist only in the candidate are ignored. `champion` is `None` for the very first model.

**Example:** `candidate = {"pr_auc": 0.62, "pr_auc__plan=basic": 0.50, "pr_auc__plan=pro": 0.66}`,
`champion = {"pr_auc": 0.60, "pr_auc__plan=basic": 0.58, "pr_auc__plan=pro": 0.64}`, `metric = "pr_auc"`,
`min_overall = 0.45`, `max_slice_drop = 0.02` -> `["regressed: pr_auc__plan=basic"]`
""",
    starter='''def promotionGate(candidate, champion, metric, min_overall, max_slice_drop):
    reasons = []
    # check the floor, then the champion, then every champion slice in sorted order
    return None
''',
    solution='''def promotionGate(candidate, champion, metric, min_overall, max_slice_drop):
    reasons = []
    if candidate[metric] < min_overall:
        reasons.append("below floor")
    if champion is not None:
        if candidate[metric] < champion[metric]:
            reasons.append("worse than champion")
        for key in sorted(champion):
            if not key.startswith(metric + "__"):
                continue
            if key not in candidate:
                reasons.append("missing: " + key)
            elif champion[key] - candidate[key] > max_slice_drop:
                reasons.append("regressed: " + key)
    return reasons
''',
    tests=[
        [{"pr_auc": 0.62, "pr_auc__plan=basic": 0.50, "pr_auc__plan=pro": 0.66},
         {"pr_auc": 0.60, "pr_auc__plan=basic": 0.58, "pr_auc__plan=pro": 0.64}, "pr_auc", 0.45, 0.02],
        [{"pr_auc": 0.50}, None, "pr_auc", 0.45, 0.02],
        [{"pr_auc": 0.40}, None, "pr_auc", 0.45, 0.02],
        [{"pr_auc": 0.40, "pr_auc__a": 0.1}, {"pr_auc": 0.55, "pr_auc__a": 0.5}, "pr_auc", 0.45, 0.02],
        [{"pr_auc": 0.70, "pr_auc__region=eu": 0.70}, {"pr_auc": 0.65, "pr_auc__region=eu": 0.69, "pr_auc__region=us": 0.60}, "pr_auc", 0.45, 0.02],
        [{"pr_auc": 0.70, "pr_auc__x": 0.695, "pr_auc__new": 0.1}, {"pr_auc": 0.65, "pr_auc__x": 0.70}, "pr_auc", 0.45, 0.02],
        [{"pr_auc": 0.70, "roc_auc__x": 0.1, "brier": 0.9}, {"pr_auc": 0.65, "roc_auc__x": 0.9, "brier": 0.1}, "pr_auc", 0.45, 0.02],
        [{"roc_auc": 0.80, "roc_auc__plan=basic": 0.70, "pr_auc__plan=basic": 0.1},
         {"roc_auc": 0.81, "roc_auc__plan=basic": 0.78, "pr_auc__plan=basic": 0.9}, "roc_auc", 0.75, 0.05],
        [{"pr_auc": 0.6, "pr_auc_basic": 0.1}, {"pr_auc": 0.6, "pr_auc_basic": 0.9}, "pr_auc", 0.0, 0.0],
        [{"pr_auc": 0.9, **{"pr_auc__s%03d" % i: 0.5 + (i % 10) / 100 for i in range(200)}},
         {"pr_auc": 0.8, **{"pr_auc__s%03d" % i: 0.55 for i in range(0, 220, 2)}}, "pr_auc", 0.5, 0.025],
    ],
    examples=2,
    wrong_solutions=[
        '''def promotionGate(candidate, champion, metric, min_overall, max_slice_drop):
    reasons = []
    if candidate[metric] < min_overall:
        reasons.append("below floor")
    if champion is not None and candidate[metric] < champion[metric]:
        reasons.append("worse than champion")
    return reasons
''',
        '''def promotionGate(candidate, champion, metric, min_overall, max_slice_drop):
    reasons = []
    if candidate[metric] < min_overall:
        reasons.append("below floor")
    if champion is not None:
        if candidate[metric] < champion[metric]:
            reasons.append("worse than champion")
        for key in sorted(champion):
            if key.startswith(metric) and key != metric and key in candidate:
                if champion[key] - candidate[key] > max_slice_drop:
                    reasons.append("regressed: " + key)
    return reasons
''',
    ],
    guide=dict(
        prereqs="Lessons *Capstone part 1* (the promotion gate in `promote.py`) and *Testing ML systems* (slice-based evaluation).",
        intuition="A gate is a list of independent checks, each adding a human-readable reason when it fails. Reasons, rather than a bare True/False, tell the engineer reading the CI log exactly what to fix.",
        hints=["Handle `champion is None` first: only the floor applies to the very first model.",
               "Use `key.startswith(metric + \"__\")` so `pr_auc_basic` (one underscore) and other metrics are skipped.",
               "A slice the champion had but the candidate lacks is suspicious (data for that group vanished): report it."],
        brute_force="Not applicable: this is careful specification-following. The usual mistake is skipping the slice loop or matching keys too loosely.",
        approach="1. Floor check.\n2. If there is a champion: overall comparison, then loop over `sorted(champion)` keeping slice keys of this metric; report missing or regressed slices.\n3. Return the list.",
        complexity="O(k log k) for k champion keys (sorting).",
        pitfalls="- Comparing `candidate - champion` instead of `champion - candidate` (the drop).\n- Forgetting that the gate tolerates a small slice drop (`> max_slice_drop`, not `> 0`): tiny differences are often noise.\n- Very small slices give noisy metrics; real gates also require a minimum slice size or a confidence interval.",
        follow_up="Add a minimum number of examples per slice, compare against a confidence interval from bootstrapping, or require a human sign-off when a protected-attribute slice regresses.",
    ),
),
]
