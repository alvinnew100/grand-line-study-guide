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
]
