_W = [{"value": "1.1.1.1", "weight": 70, "healthy": True}, {"value": "2.2.2.2", "weight": 20, "healthy": True},
      {"value": "3.3.3.3", "weight": 10, "healthy": True}]
_W_SICK = [{"value": "1.1.1.1", "weight": 70, "healthy": False}, {"value": "2.2.2.2", "weight": 20, "healthy": True},
           {"value": "3.3.3.3", "weight": 10, "healthy": True}]
_LAT = [{"value": "eu", "region": "eu-west-1", "healthy": True}, {"value": "us", "region": "us-east-1", "healthy": True},
        {"value": "ap", "region": "ap-southeast-1", "healthy": True}]
_FO = [{"value": "primary", "role": "PRIMARY", "healthy": True}, {"value": "standby", "role": "SECONDARY", "healthy": True}]
_GEO = [{"value": "fr", "location": "FR", "healthy": True}, {"value": "eu", "location": "EU", "healthy": True},
        {"value": "world", "location": "*", "healthy": True}]
_POLICY = {"query": ["w", "h"], "headers": ["Accept-Language"], "min_ttl": 60, "default_ttl": 86400, "max_ttl": 31536000}
_SUBS = [
    ["audit", None],
    ["eu-orders", {"region": ["eu-west-1", "eu-central-1"], "type": ["order"]}],
    ["big-orders", {"type": ["order"], "amount": [{"numeric": [">=", 1000]}]}],
    ["not-test", {"env": [{"anything-but": ["test", "dev"]}]}],
    ["images", {"key": [{"prefix": "img/"}]}],
    ["anonymous", {"user": [{"exists": False}]}],
]


def _sick(recs, *idx):
    out = [dict(r) for r in recs]
    for i in idx:
        out[i]["healthy"] = False
    return out


PROBLEMS = [
dict(
    id="aws-route53-resolve",
    title="Route 53 Routing Policy Resolution",
    difficulty="Hard",
    pattern="DNS",
    entry="resolve",
    description=r"""
Route 53 can answer the same DNS name differently depending on a **routing policy** and on the health
of the endpoints. Implement the choice.

`resolve(policy, records, query)` returns the **list of values** in the answer (`[]` = no answer).

Every record is a dict with `"value"` and `"healthy"` plus policy-specific fields. `query` is a dict
with what Route 53 knows about the request.

- **`"simple"`** — return all values in listed order; health is not considered.
- **`"multivalue"`** — return the values of the healthy records, at most the first 8; if no record is
  healthy, return the first 8 of all records.
- **`"weighted"`** — records have `"weight"` (integer ≥ 0). Candidates are the healthy records with
  weight > 0; if there are none, the candidates are all records with weight > 0 regardless of health
  (when everything looks down, Route 53 answers anyway). If **every** record has weight 0, treat every
  weight as 1 first. Let `total` be the sum of candidate weights and `r = query["roll"] % total`; walk
  the candidates in listed order subtracting weights and return the record in whose slice `r` falls
  (the first candidate owns `0 … w1-1`, the second `w1 … w1+w2-1`, and so on).
- **`"latency"`** — records have `"region"`; `query["latency"]` maps region → milliseconds measured
  from the user. Consider only records whose region appears in the map. Among the healthy ones return
  the record with the lowest latency (ties → first listed). If none is healthy, choose among all of
  them the same way.
- **`"failover"`** — records have `"role"`: exactly one `"PRIMARY"` and one `"SECONDARY"`. Return the
  primary if healthy; otherwise the secondary if healthy; otherwise the primary.
- **`"geolocation"`** — records have `"location"`: a country code, a continent code, or `"*"`
  (default). `query` has `"country"` and `"continent"`. Try, in order, the records whose location
  equals the country, then the continent, then `"*"`. At each level return the values of the
  **healthy** records of that level if there are any; otherwise fall through to the next level.
  Nothing left → `[]`.

**Example:** `resolve("failover", [primary unhealthy, secondary healthy], {})` → `["standby"]`
""",
    starter='''def resolve(policy, records, query):
    pass
''',
    solution='''def resolve(policy, records, query):
    if policy == "simple":
        return [r["value"] for r in records]
    if policy == "multivalue":
        healthy = [r["value"] for r in records if r["healthy"]]
        return (healthy or [r["value"] for r in records])[:8]
    if policy == "weighted":
        if not records:
            return []
        weights = [r["weight"] for r in records]
        if all(w == 0 for w in weights):
            weights = [1] * len(records)
        cands = [(r, w) for r, w in zip(records, weights) if w > 0 and r["healthy"]]
        if not cands:
            cands = [(r, w) for r, w in zip(records, weights) if w > 0]
        total = sum(w for _, w in cands)
        roll = query["roll"] % total
        for r, w in cands:
            if roll < w:
                return [r["value"]]
            roll -= w
    if policy == "latency":
        lat = query["latency"]
        known = [r for r in records if r["region"] in lat]
        cands = [r for r in known if r["healthy"]] or known
        if not cands:
            return []
        best = cands[0]
        for r in cands[1:]:
            if lat[r["region"]] < lat[best["region"]]:
                best = r
        return [best["value"]]
    if policy == "failover":
        primary = next(r for r in records if r["role"] == "PRIMARY")
        secondary = next(r for r in records if r["role"] == "SECONDARY")
        if primary["healthy"] or not secondary["healthy"]:
            return [primary["value"]]
        return [secondary["value"]]
    if policy == "geolocation":
        for loc in (query["country"], query["continent"], "*"):
            hit = [r["value"] for r in records if r["location"] == loc and r["healthy"]]
            if hit:
                return hit
        return []
    return []
''',
    tests=[
        ["failover", _sick(_FO, 0), {}],
        ["weighted", _W, {"roll": 69}],
        ["weighted", _W, {"roll": 70}],
        ["weighted", _W, {"roll": 199}],
        ["weighted", _W_SICK, {"roll": 25}],
        ["weighted", _W_SICK, {"roll": 0}],
        ["weighted", _sick(_W, 0, 1, 2), {"roll": 95}],
        ["weighted", [{"value": "a", "weight": 0, "healthy": True}, {"value": "b", "weight": 0, "healthy": True}], {"roll": 3}],
        ["weighted", [{"value": "a", "weight": 0, "healthy": True}, {"value": "b", "weight": 5, "healthy": False}], {"roll": 3}],
        ["simple", _sick(_W, 1), {}],
        ["multivalue", [{"value": str(i), "healthy": i % 3 != 0} for i in range(15)], {}],
        ["multivalue", [{"value": str(i), "healthy": False} for i in range(10)], {}],
        ["latency", _LAT, {"latency": {"eu-west-1": 30, "us-east-1": 90, "ap-southeast-1": 200}}],
        ["latency", _sick(_LAT, 0), {"latency": {"eu-west-1": 30, "us-east-1": 90, "ap-southeast-1": 200}}],
        ["latency", _sick(_LAT, 0, 1, 2), {"latency": {"eu-west-1": 30, "us-east-1": 90, "ap-southeast-1": 20}}],
        ["latency", _LAT, {"latency": {"us-east-1": 50, "ap-southeast-1": 50}}],
        ["latency", _LAT, {"latency": {}}],
        ["failover", _FO, {}],
        ["failover", _sick(_FO, 0, 1), {}],
        ["failover", _sick(_FO, 1), {}],
        ["geolocation", _GEO, {"country": "FR", "continent": "EU"}],
        ["geolocation", _GEO, {"country": "DE", "continent": "EU"}],
        ["geolocation", _GEO, {"country": "JP", "continent": "AS"}],
        ["geolocation", _sick(_GEO, 0), {"country": "FR", "continent": "EU"}],
        ["geolocation", _sick(_GEO, 0, 1, 2), {"country": "FR", "continent": "EU"}],
        ["geolocation", _GEO[:2], {"country": "US", "continent": "NA"}],
    ],
    examples=3,
    wrong_solutions=[
        '''def resolve(policy, records, query):
    if policy == "simple":
        return [r["value"] for r in records]
    if policy == "multivalue":
        return [r["value"] for r in records if r["healthy"]][:8]
    if policy == "weighted":
        cands = [r for r in records if r["weight"] > 0 and r["healthy"]]
        total = sum(r["weight"] for r in cands)
        if not total:
            return []
        roll = query["roll"] % total
        for r in cands:
            if roll < r["weight"]:
                return [r["value"]]
            roll -= r["weight"]
    if policy == "latency":
        cands = [r for r in records if r["healthy"] and r["region"] in query["latency"]]
        return [min(cands, key=lambda r: query["latency"][r["region"]])["value"]] if cands else []
    if policy == "failover":
        for role in ("PRIMARY", "SECONDARY"):
            for r in records:
                if r["role"] == role and r["healthy"]:
                    return [r["value"]]
        return []
    if policy == "geolocation":
        for loc in (query["country"], query["continent"], "*"):
            hit = [r["value"] for r in records if r["location"] == loc and r["healthy"]]
            if hit:
                return hit
    return []
''',
        '''def resolve(policy, records, query):
    if policy == "simple":
        return [r["value"] for r in records]
    if policy == "multivalue":
        healthy = [r["value"] for r in records if r["healthy"]]
        return (healthy or [r["value"] for r in records])[:8]
    if policy == "weighted":
        if not records:
            return []
        weights = [r["weight"] for r in records]
        if all(w == 0 for w in weights):
            weights = [1] * len(records)
        total = sum(weights)
        roll = query["roll"] % total
        for r, w in zip(records, weights):
            if roll < w:
                return [r["value"]]
            roll -= w
    if policy == "latency":
        lat = query["latency"]
        known = [r for r in records if r["region"] in lat]
        return [min(known, key=lambda r: lat[r["region"]])["value"]] if known else []
    if policy == "failover":
        primary = next(r for r in records if r["role"] == "PRIMARY")
        secondary = next(r for r in records if r["role"] == "SECONDARY")
        return [primary["value"]] if primary["healthy"] or not secondary["healthy"] else [secondary["value"]]
    if policy == "geolocation":
        for loc in (query["country"], query["continent"], "*"):
            hit = [r["value"] for r in records if r["location"] == loc]
            if hit:
                return hit
    return []
''',
    ],
    guide=dict(
        prereqs="The Route 53 lesson: routing policies and health checks.",
        intuition="Every policy is 'filter by health, then pick by a rule', with one shared safety net: if the health filter removes everything, Route 53 would rather return something than nothing.",
        hints=["Write one branch per policy and test each alone.",
               "Weighted: build the candidate list with its weights first, then a single cumulative walk using `roll % total`.",
               "Geolocation is a three-level fallback loop over `(country, continent, '*')`."],
        brute_force="For the weighted policy you could expand each record `weight` times into a list and index it with the roll: O(total weight) memory instead of O(records).",
        approach="Dry run weighted with weights 70/20/10 where the first record is unhealthy and roll = 25: candidates are the 20 and the 10 → total 30 → r = 25 → not < 20, subtract → 5 < 10 → third record `3.3.3.3`. The unhealthy record's share is redistributed proportionally.",
        complexity="O(R) time for R records, O(R) space.",
        pitfalls="Returning nothing when all endpoints are unhealthy (weighted, latency, failover and multivalue all still answer); using the original total weight after filtering; ignoring ties in latency; letting an unhealthy country record block the fallback to continent.",
    ),
),
dict(
    id="aws-cloudfront-cache",
    title="CloudFront Cache Key and TTL",
    difficulty="Medium",
    pattern="CDN",
    entry="cacheDecision",
    description=r"""
A content delivery network stores responses under a **cache key** and keeps them for a **TTL** (time
to live, in seconds). Two requests share a cached copy only if their keys are identical, so the key
should contain exactly the parts of the request that change the response.

`cacheDecision(request, policy, cache_control)` returns `[cache_key, ttl]`.

- `request = {"path": "/img/a.png", "query": {name: value}, "headers": {name: value}}`.
- `policy = {"query": "none" | "all" | [names], "headers": [names], "min_ttl", "default_ttl", "max_ttl"}`.
- `cache_control`: the origin's `Cache-Control` response header (string) or `null` if absent.

**Cache key** = the path, then:

- the included query parameters (none, all, or only the listed names — query names are
  case-sensitive), sorted by name, written `name=value` and joined with `&`, preceded by `?` — omit
  the `?` when no parameter is included;
- then, for each header named in the policy that is present in the request (header names are
  **case-insensitive**), `|name=value` with the name lower-cased, sorted by lower-cased name.

**TTL.** Split `cache_control` on commas, trim spaces and lower-case the directives.

1. If it contains `no-store`, `no-cache` or `private` → `min_ttl`.
2. Else if it has `s-maxage=N` → `N` clamped to `[min_ttl, max_ttl]`.
3. Else if it has `max-age=N` → `N` clamped to `[min_ttl, max_ttl]`.
4. Else (no header, or none of these directives) → `default_ttl`.

**Example:** path `/img/a.png`, query `{"w":"200","utm_source":"mail"}`, header
`accept-language: fr`, policy query `["w","h"]`, headers `["Accept-Language"]`, min 60, default 86400,
max 31536000, `Cache-Control: max-age=10` → `["/img/a.png?w=200|accept-language=fr", 60]`
""",
    starter='''def cacheDecision(request, policy, cache_control):
    pass
''',
    solution='''def cacheDecision(request, policy, cache_control):
    key = request["path"]
    q = request.get("query") or {}
    if policy["query"] == "all":
        names = sorted(q)
    elif policy["query"] == "none":
        names = []
    else:
        names = sorted(n for n in q if n in policy["query"])
    if names:
        key += "?" + "&".join("%s=%s" % (n, q[n]) for n in names)
    headers = {k.lower(): v for k, v in (request.get("headers") or {}).items()}
    for h in sorted({h.lower() for h in policy["headers"]}):
        if h in headers:
            key += "|%s=%s" % (h, headers[h])
    lo, hi = policy["min_ttl"], policy["max_ttl"]
    directives = [d.strip().lower() for d in cache_control.split(",")] if cache_control else []
    ttl = policy["default_ttl"]
    if any(d in ("no-store", "no-cache", "private") for d in directives):
        ttl = lo
    else:
        found = None
        for prefix in ("s-maxage=", "max-age="):
            for d in directives:
                if d.startswith(prefix) and found is None:
                    found = int(d[len(prefix):])
            if found is not None:
                break
        if found is not None:
            ttl = max(lo, min(hi, found))
    return [key, ttl]
''',
    tests=[
        [{"path": "/img/a.png", "query": {"w": "200", "utm_source": "mail"}, "headers": {"accept-language": "fr"}}, _POLICY, "max-age=10"],
        [{"path": "/index.html", "query": {}, "headers": {}}, _POLICY, None],
        [{"path": "/a", "query": {"h": "9", "w": "3", "x": "1"}, "headers": {"Accept-Language": "en", "Cookie": "s=1"}}, _POLICY, "public, max-age=3600"],
        [{"path": "/a", "query": {"b": "2", "a": "1"}, "headers": {}}, dict(_POLICY, query="all"), "max-age=600, s-maxage=120"],
        [{"path": "/a", "query": {"b": "2", "a": "1"}, "headers": {}}, dict(_POLICY, query="none"), "s-maxage=5"],
        [{"path": "/api/me", "query": {}, "headers": {"Authorization": "t1"}}, dict(_POLICY, headers=["authorization"], min_ttl=0), "private, max-age=600"],
        [{"path": "/api/me", "query": {}, "headers": {"AUTHORIZATION": "t1", "Host": "x"}}, dict(_POLICY, headers=["Host", "Authorization"], min_ttl=0), "No-Store"],
        [{"path": "/v", "query": {"W": "1"}, "headers": {}}, _POLICY, "max-age=99999999999"],
        [{"path": "/v", "query": {"w": ""}, "headers": {}}, _POLICY, "must-revalidate"],
        [{"path": "/v", "query": {"w": "1"}, "headers": {}}, dict(_POLICY, min_ttl=0), "max-age=0"],
        [{"path": "/v", "query": {}, "headers": {"accept-language": "de"}}, dict(_POLICY, headers=[]), " S-MaxAge=300 , max-age=10"],
        [{"path": "/v", "query": {"h": "2"}, "headers": {}}, dict(_POLICY, default_ttl=5), "public"],
        [{"path": "/v", "query": {"h": "2"}, "headers": {}}, dict(_POLICY, min_ttl=0), "no-cache"],
    ],
    examples=2,
    wrong_solutions=[
        '''def cacheDecision(request, policy, cache_control):
    key = request["path"]
    q = request.get("query") or {}
    if q:
        key += "?" + "&".join("%s=%s" % (n, q[n]) for n in sorted(q))
    ttl = policy["default_ttl"]
    if cache_control and "max-age=" in cache_control:
        ttl = int(cache_control.split("max-age=")[1].split(",")[0])
    return [key, ttl]
''',
        '''def cacheDecision(request, policy, cache_control):
    key = request["path"]
    q = request.get("query") or {}
    names = sorted(q) if policy["query"] == "all" else [] if policy["query"] == "none" else sorted(n for n in q if n in policy["query"])
    if names:
        key += "?" + "&".join("%s=%s" % (n, q[n]) for n in names)
    headers = {k.lower(): v for k, v in (request.get("headers") or {}).items()}
    for h in sorted({h.lower() for h in policy["headers"]}):
        if h in headers:
            key += "|%s=%s" % (h, headers[h])
    lo, hi = policy["min_ttl"], policy["max_ttl"]
    directives = [d.strip().lower() for d in cache_control.split(",")] if cache_control else []
    ttl = policy["default_ttl"]
    for d in directives:
        if d.startswith("max-age="):
            ttl = max(lo, min(hi, int(d[8:])))
    for d in directives:
        if d in ("no-store", "no-cache", "private"):
            ttl = 0
    return [key, ttl]
''',
    ],
    guide=dict(
        prereqs="The CloudFront lesson: cache keys, cache policies and how the origin's Cache-Control interacts with minimum, default and maximum TTL.",
        intuition="Two independent halves. The key is a canonical string: only whitelisted parts, in sorted order, so that equivalent requests collide on purpose. The TTL is a priority list over the origin's directives, squeezed between the policy's minimum and maximum.",
        hints=["Build the key in three steps: path, sorted query part, sorted header part.",
               "Lower-case request header names into a dict before looking anything up.",
               "Parse directives into a clean list first; check the three 'do not cache' words, then `s-maxage`, then `max-age`."],
        brute_force="Using the full URL and all headers as the key always gives correct content but a hit ratio near zero — tracking parameters such as `utm_source` would split every object into thousands of copies.",
        approach="Dry run of the example: included query names = {w} (utm_source is not whitelisted) → `?w=200`; policy header Accept-Language is present (case-insensitively) → `|accept-language=fr`. Directives `[max-age=10]` → 10 clamped to at least 60 → 60.",
        complexity="O(q log q + h log h) for q query parameters and h headers; O(key length) space.",
        pitfalls="Leaving a dangling `?`; case-sensitive header matching; letting `max-age` win over `s-maxage`; returning 0 for `no-cache` instead of the minimum TTL; forgetting to clamp.",
    ),
),
dict(
    id="aws-sns-filter-fanout",
    title="SNS Fan-Out with Filter Policies",
    difficulty="Medium",
    pattern="Messaging",
    entry="deliver",
    description=r"""
An SNS **topic** copies each published message to all its subscriptions (fan-out). A subscription may
carry a **filter policy** so that it receives only the messages whose attributes match.

`deliver(subscriptions, attributes)` returns the names of the subscriptions that receive the message,
in the given order.

- `subscriptions`: list of `[name, policy]`; `policy` is `null` or `{}` (receive everything) or a dict
  `attribute_name -> list of rules`.
- `attributes`: the message attributes, a dict `name -> string or number`.
- A policy matches when **every** attribute name in it is satisfied (AND), and a name is satisfied
  when **at least one** rule in its list matches (OR). Rules:
  - a plain string or number: the attribute exists and equals it exactly (`"5"` and `5` are different);
  - `{"prefix": "abc"}`: the attribute exists, is a string and starts with `abc`;
  - `{"anything-but": [v1, v2, ...]}`: the attribute exists and is not equal to any listed value;
  - `{"numeric": [op, n]}` with `op` in `">"`, `">="`, `"<"`, `"<="`, `"="`: the attribute exists, is
    a number (not a string, not a boolean) and satisfies the comparison;
  - `{"exists": true}`: the attribute exists; `{"exists": false}`: the attribute does **not** exist.
- If the attribute is absent, only `{"exists": false}` can match.

**Example:** policy `{"type": ["order"], "amount": [{"numeric": [">=", 1000]}]}` with attributes
`{"type": "order", "amount": 1500}` matches; with `amount: 200` it does not.
""",
    starter='''def deliver(subscriptions, attributes):
    pass
''',
    solution='''def _rule_ok(rule, present, value):
    if isinstance(rule, dict):
        if "exists" in rule:
            return present == rule["exists"]
        if not present:
            return False
        if "prefix" in rule:
            return isinstance(value, str) and value.startswith(rule["prefix"])
        if "anything-but" in rule:
            return all(not (type(value) == type(v) and value == v) for v in rule["anything-but"])
        if "numeric" in rule:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            op, n = rule["numeric"]
            return {">": value > n, ">=": value >= n, "<": value < n, "<=": value <= n, "=": value == n}[op]
        return False
    if not present:
        return False
    if isinstance(rule, str) != isinstance(value, str):
        return False
    return rule == value

def deliver(subscriptions, attributes):
    out = []
    for name, policy in subscriptions:
        ok = True
        for attr, rules in (policy or {}).items():
            present = attr in attributes
            value = attributes.get(attr)
            if not any(_rule_ok(r, present, value) for r in rules):
                ok = False
                break
        if ok:
            out.append(name)
    return out
''',
    tests=[
        [[["big", {"type": ["order"], "amount": [{"numeric": [">=", 1000]}]}]], {"type": "order", "amount": 1500}],
        [[["big", {"type": ["order"], "amount": [{"numeric": [">=", 1000]}]}]], {"type": "order", "amount": 200}],
        [_SUBS, {"type": "order", "region": "eu-west-1", "amount": 1000, "env": "prod", "key": "img/1.png", "user": "u1"}],
        [_SUBS, {"type": "refund", "region": "eu-west-1", "amount": 5000, "env": "test"}],
        [_SUBS, {}],
        [_SUBS, {"type": "order", "region": "us-east-1", "amount": "1500", "env": "Test", "key": "images/1.png"}],
        [[], {"a": 1}],
        [[["a", {}], ["b", None]], {}],
        [[["n", {"n": [5]}], ["s", {"n": ["5"]}]], {"n": 5}],
        [[["n", {"n": [5]}], ["s", {"n": ["5"]}]], {"n": "5"}],
        [[["x", {"k": [{"exists": True}]}], ["y", {"k": [{"exists": False}]}]], {"k": ""}],
        [[["x", {"p": [{"numeric": ["<", 0]}, {"numeric": ["=", 7]}, "free"]}]], {"p": 7}],
        [[["x", {"p": [{"numeric": ["<", 0]}, {"numeric": ["=", 7]}, "free"]}]], {"p": "free"}],
        [[["x", {"p": [{"numeric": ["<", 0]}, {"numeric": ["=", 7]}, "free"]}]], {"p": 3}],
        [[["x", {"a": [{"anything-but": ["x"]}], "b": [{"prefix": ""}]}]], {"a": "y", "b": "anything"}],
        [[["x", {"a": [{"anything-but": ["x"]}], "b": [{"prefix": ""}]}]], {"a": "y", "b": 12}],
        [[["x", {"a": [{"numeric": ["<=", 2.5]}]}]], {"a": 2.5}],
    ],
    examples=2,
    wrong_solutions=[
        '''def deliver(subscriptions, attributes):
    out = []
    for name, policy in subscriptions:
        ok = True
        for attr, rules in (policy or {}).items():
            if attributes.get(attr) not in rules:
                ok = False
        if ok:
            out.append(name)
    return out
''',
        '''def _ok(rule, present, value):
    if isinstance(rule, dict):
        if "exists" in rule:
            return present == rule["exists"]
        if "prefix" in rule:
            return isinstance(value, str) and value.startswith(rule["prefix"])
        if "anything-but" in rule:
            return value not in rule["anything-but"]
        if "numeric" in rule:
            if not isinstance(value, (int, float)):
                return False
            op, n = rule["numeric"]
            return {">": value > n, ">=": value >= n, "<": value < n, "<=": value <= n, "=": value == n}[op]
        return False
    return present and rule == value and isinstance(rule, str) == isinstance(value, str)
def deliver(subscriptions, attributes):
    out = []
    for name, policy in subscriptions:
        if any(any(_ok(r, a in attributes, attributes.get(a)) for r in rules) for a, rules in (policy or {}).items()) or not policy:
            out.append(name)
    return out
''',
    ],
    guide=dict(
        prereqs="The SQS and SNS lesson: topics, subscriptions, fan-out and filter policies.",
        intuition="AND across attribute names, OR across the rules of one name. Write a function that judges one rule against one attribute and the rest is two nested loops.",
        hints=["Pass three things to the rule checker: the rule, whether the attribute is present, and its value.",
               "Handle `exists` first — it is the only rule that can match an absent attribute.",
               "Strings and numbers never equal each other here; check the types before comparing."],
        brute_force="Not applicable; matching is linear in the size of the policy.",
        approach="Dry run of the fourth test (refund, eu-west-1, amount 5000, env test, no key, no user): audit → no policy → yes. eu-orders → region ok, type refund ≠ order → no. big-orders → type fails → no. not-test → env is `test`, which is excluded → no. images → `key` absent → prefix cannot match → no. anonymous → `user` absent and rule is exists:false → yes. Result `[audit, anonymous]`.",
        complexity="O(S × P) for S subscriptions and P rules per policy.",
        pitfalls="Using OR between attribute names; matching `anything-but` when the attribute is absent; treating the string '1500' as the number 1500; `True` passing as a number in Python (`isinstance(True, int)` is true).",
    ),
),
dict(
    id="aws-sqs-simulator",
    title="SQS Queue Simulator",
    difficulty="Hard",
    pattern="Messaging",
    kind="class",
    entry="Queue",
    description=r"""
Build a small in-memory model of an SQS queue. Every method receives the current time `t` explicitly
(integer seconds, never decreasing across calls) — there is no real clock.

```
Queue(visibility_timeout, max_receive, fifo)
send(t, body, group)        -> message id (1, 2, 3, ... in send order)
receive(t, max_n)           -> list of [id, body, receipt]
delete(t, receipt)          -> True / False
dlq(t)                      -> list of message ids moved to the dead-letter queue, in order
```

**Visibility timeout.** A received message is not removed. It becomes invisible until
`t + visibility_timeout`; if it is not deleted by then, it becomes visible again and can be received
again (this is how SQS gives *at-least-once* delivery).

**receive(t, max_n).** Scan the stored messages in send order and collect up to `max_n` messages that
are visible at `t` (`visible_at <= t`). For each visible message in the scan:

- if it has already been received `max_receive` times, move it to the dead-letter queue instead (it
  leaves this queue, is not returned and does not count towards `max_n`);
- otherwise increment its receive count, hide it until `t + visibility_timeout` and return
  `[id, body, receipt]` where `receipt` is the string `"<id>:<receive_count>"`.

**FIFO mode** (`fifo=True`). Messages have a `group` (a string). Within a group, order is strict:
only the **oldest remaining** message of each group can be considered, and while it is invisible
(in flight) the whole group is blocked. One `receive` call returns at most one message per group.
If the oldest message of a group is moved to the dead-letter queue during a scan, the next message of
that group is considered in the same scan. In standard mode (`fifo=False`), `group` is ignored.

**delete(t, receipt).** Succeeds (returns `True` and removes the message) only if the message is
still in this queue and the receipt is the one from its **most recent** receive. A stale receipt, an
unknown one, or a message already deleted or dead-lettered → `False`.

Tests use the LeetCode design format: a list of method names and a list of argument lists.
""",
    starter='''class Queue:
    def __init__(self, visibility_timeout, max_receive, fifo):
        pass

    def send(self, t, body, group):
        pass

    def receive(self, t, max_n):
        pass

    def delete(self, t, receipt):
        pass

    def dlq(self, t):
        pass
''',
    solution='''class Queue:
    def __init__(self, visibility_timeout, max_receive, fifo):
        self.vt, self.max_receive, self.fifo = visibility_timeout, max_receive, fifo
        self.msgs = []          # dicts in send order
        self.dead = []
        self.next_id = 1

    def send(self, t, body, group):
        m = {"id": self.next_id, "body": body, "group": group, "visible_at": t, "count": 0}
        self.next_id += 1
        self.msgs.append(m)
        return m["id"]

    def receive(self, t, max_n):
        out, keep, blocked = [], [], set()
        for m in self.msgs:
            if len(out) >= max_n:
                keep.append(m)
                continue
            if self.fifo and m["group"] in blocked:
                keep.append(m)
                continue
            if m["visible_at"] > t:
                if self.fifo:
                    blocked.add(m["group"])
                keep.append(m)
                continue
            if m["count"] >= self.max_receive:
                self.dead.append(m["id"])
                continue
            m["count"] += 1
            m["visible_at"] = t + self.vt
            if self.fifo:
                blocked.add(m["group"])
            out.append([m["id"], m["body"], "%d:%d" % (m["id"], m["count"])])
            keep.append(m)
        self.msgs = keep
        return out

    def delete(self, t, receipt):
        for i, m in enumerate(self.msgs):
            if "%d:%d" % (m["id"], m["count"]) == receipt and m["count"] > 0:
                del self.msgs[i]
                return True
        return False

    def dlq(self, t):
        return list(self.dead)
''',
    tests=[
        [["Queue", "send", "send", "receive", "receive", "receive", "delete", "receive"],
         [[30, 3, False], [0, "a", None], [1, "b", None], [2, 1], [3, 5], [10, 5], [11, "1:1"], [32, 5]]],
        [["Queue", "send", "receive", "receive", "receive", "receive", "dlq", "delete"],
         [[10, 2, False], [0, "poison", None], [0, 1], [10, 1], [20, 1], [30, 1], [30], [30, "1:2"]]],
        [["Queue", "send", "send", "send", "receive", "receive", "delete", "receive", "receive"],
         [[30, 5, True], [0, "a1", "A"], [0, "a2", "A"], [0, "b1", "B"], [1, 10], [2, 10], [3, "1:1"], [4, 10], [40, 10]]],
        [["Queue", "receive", "dlq", "delete"], [[30, 1, False], [0, 10], [0], [0, "1:1"]]],
        [["Queue", "send", "receive", "delete", "delete", "receive", "dlq"],
         [[5, 3, False], [0, "x", None], [0, 1], [1, "1:1"], [2, "1:1"], [100, 1], [100]]],
        [["Queue", "send", "receive", "receive", "delete", "delete", "receive"],
         [[5, 3, False], [0, "x", None], [0, 1], [5, 1], [6, "1:1"], [6, "1:2"], [50, 1]]],
        [["Queue", "send", "receive", "delete", "delete"],
         [[5, 3, False], [0, "x", None], [0, 0], [0, "1:0"], [0, "1:1"]]],
        [["Queue", "send", "send", "send", "receive", "receive", "receive", "dlq", "receive"],
         [[10, 1, True], [0, "a1", "A"], [0, "a2", "A"], [0, "b1", "B"], [0, 1], [10, 5], [20, 5], [20], [30, 5]]],
        [["Queue", "send", "send", "send", "send", "receive", "receive", "receive"],
         [[100, 9, False], [0, "m1", None], [0, "m2", None], [0, "m3", None], [0, "m4", None], [1, 3], [2, 3], [3, 3]]],
        [["Queue", "send", "send", "receive", "send", "receive", "delete", "receive", "delete", "receive"],
         [[20, 4, True], [0, "o1", "order-7"], [1, "o2", "order-7"], [2, 2], [3, "p1", "order-8"], [4, 2], [5, "1:1"], [6, 2], [7, "2:1"], [8, 2]]],
        [["Queue", "send", "send", "receive", "receive", "receive", "dlq", "receive", "dlq"],
         [[10, 1, False], [0, "a", None], [0, "b", None], [0, 1], [5, 1], [10, 2], [10], [15, 2], [15]]],
        [["Queue"] + ["send"] * 20 + ["receive", "receive", "receive", "dlq"],
         [[7, 2, True]] + [[i, "m%d" % i, "g%d" % (i % 3)] for i in range(20)] + [[20, 10], [27, 2], [34, 10], [34]]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Queue:
    def __init__(self, visibility_timeout, max_receive, fifo):
        self.msgs, self.dead, self.n = [], [], 1
    def send(self, t, body, group):
        self.msgs.append([self.n, body]); self.n += 1
        return self.n - 1
    def receive(self, t, max_n):
        out = [[i, b, "%d:1" % i] for i, b in self.msgs[:max_n]]
        self.msgs = self.msgs[max_n:]
        return out
    def delete(self, t, receipt):
        return True
    def dlq(self, t):
        return []
''',
        '''class Queue:
    def __init__(self, visibility_timeout, max_receive, fifo):
        self.vt, self.max_receive, self.fifo = visibility_timeout, max_receive, fifo
        self.msgs, self.dead, self.next_id = [], [], 1
    def send(self, t, body, group):
        m = {"id": self.next_id, "body": body, "group": group, "visible_at": t, "count": 0}
        self.next_id += 1
        self.msgs.append(m)
        return m["id"]
    def receive(self, t, max_n):
        out, keep = [], []
        for m in self.msgs:
            if len(out) >= max_n or m["visible_at"] > t:
                keep.append(m); continue
            if m["count"] >= self.max_receive:
                self.dead.append(m["id"]); continue
            m["count"] += 1
            m["visible_at"] = t + self.vt
            out.append([m["id"], m["body"], "%d:%d" % (m["id"], m["count"])])
            keep.append(m)
        self.msgs = keep
        return out
    def delete(self, t, receipt):
        for i, m in enumerate(self.msgs):
            if "%d:%d" % (m["id"], m["count"]) == receipt and m["count"] > 0:
                del self.msgs[i]
                return True
        return False
    def dlq(self, t):
        return list(self.dead)
''',
        '''class Queue:
    def __init__(self, visibility_timeout, max_receive, fifo):
        self.vt, self.max_receive, self.fifo = visibility_timeout, max_receive, fifo
        self.msgs, self.dead, self.next_id = [], [], 1
    def send(self, t, body, group):
        m = {"id": self.next_id, "body": body, "group": group, "visible_at": t, "count": 0}
        self.next_id += 1
        self.msgs.append(m)
        return m["id"]
    def receive(self, t, max_n):
        out, keep, blocked = [], [], set()
        for m in self.msgs:
            if len(out) >= max_n or (self.fifo and m["group"] in blocked):
                keep.append(m); continue
            if m["visible_at"] > t:
                if self.fifo:
                    blocked.add(m["group"])
                keep.append(m); continue
            if m["count"] >= self.max_receive:
                self.dead.append(m["id"]); continue
            m["count"] += 1
            m["visible_at"] = t + self.vt
            if self.fifo:
                blocked.add(m["group"])
            out.append([m["id"], m["body"], "%d:%d" % (m["id"], m["count"])])
            keep.append(m)
        self.msgs = keep
        return out
    def delete(self, t, receipt):
        mid = int(receipt.split(":")[0])
        for i, m in enumerate(self.msgs):
            if m["id"] == mid:
                del self.msgs[i]
                return True
        return False
    def dlq(self, t):
        return list(self.dead)
''',
    ],
    guide=dict(
        prereqs="The SQS and SNS lesson: visibility timeout, at-least-once delivery, dead-letter queues, FIFO message groups.",
        intuition="A message is a small record: when it becomes visible again and how many times it has been handed out. `receive` is a single ordered scan that either skips, dead-letters or hands out each message. FIFO adds one set: the groups already blocked or served in this scan.",
        hints=["Store `visible_at` (initially the send time) and `count` per message; a message is in flight exactly when `visible_at > t`.",
               "Check the dead-letter condition **before** incrementing the count: a message received `max_receive` times moves on its next visible scan.",
               "In FIFO mode add the group to a `blocked` set both when you return its head and when its head is invisible — but not when the head is dead-lettered."],
        brute_force="Advancing a simulated clock second by second and expiring timers is unnecessary: comparing `visible_at` with the `t` passed in gives the same behaviour lazily.",
        approach="Dry run of the second test (timeout 10, max_receive 2): send at 0. receive(0) → count 1, receipt `1:1`, hidden until 10. receive(10) → visible again → count 2, receipt `1:2`, hidden until 20. receive(20) → count is already 2 = max → moved to the dead-letter queue, returns `[]`. receive(30) → `[]`. dlq → `[1]`. delete(`1:2`) → False, the message is no longer in this queue.",
        complexity="`receive` and `delete` are O(n) in the number of stored messages; `send` is O(1). Space O(n).",
        pitfalls="Removing a message on receive; accepting stale receipts; counting dead-lettered messages towards `max_n`; in FIFO mode delivering the second message of a group while the first is in flight; accepting the receipt `id:0` for a message never received.",
        follow_up="Real FIFO queues also deduplicate sends for five minutes using a deduplication id, and can return several messages of one group in a single batch, in order.",
    ),
),
dict(
    id="aws-kinesis-shards",
    title="Kinesis Shard Count and Partition Keys",
    difficulty="Medium",
    pattern="Streaming",
    entry="shardPlan",
    description=r"""
A Kinesis data stream in provisioned mode is made of **shards**. Each shard accepts at most
**1,024 KB/s and 1,000 records/s** of writes and serves at most **2,048 KB/s** of reads. Each record
has a **partition key**; the MD5 hash of the key (a 128-bit number) decides the shard, and the shards
split the hash range `0 … 2^128 - 1` into equal consecutive slices.

`shardPlan(write_kb_per_s, records_per_s, read_kb_per_s, keys)`:

1. Compute the number of shards needed:
   `n = max(1, ceil(write_kb_per_s / 1024), ceil(records_per_s / 1000), ceil(read_kb_per_s / 2048))`.
2. For each partition key in `keys` (a list of strings, one per record of a sample; keys repeat),
   compute `h = int(md5(key as UTF-8).hexdigest(), 16)` and the shard index `h * n // 2**128`.
3. Return `[n, counts]` where `counts[i]` is the number of sample records landing on shard `i`.

Use `hashlib.md5`. All inputs are non-negative integers.

**Example:** `shardPlan(3000, 500, 1000, ["user-1", "user-2", "user-1"])` → 3 shards (write volume is
the constraint) and the two `user-1` records necessarily share a shard.
""",
    starter='''import hashlib

def shardPlan(write_kb_per_s, records_per_s, read_kb_per_s, keys):
    pass
''',
    solution='''import hashlib

def shardPlan(write_kb_per_s, records_per_s, read_kb_per_s, keys):
    n = max(1, -(-write_kb_per_s // 1024), -(-records_per_s // 1000), -(-read_kb_per_s // 2048))
    counts = [0] * n
    for k in keys:
        h = int(hashlib.md5(k.encode("utf-8")).hexdigest(), 16)
        counts[h * n // 2 ** 128] += 1
    return [n, counts]
''',
    tests=[
        [3000, 500, 1000, ["user-1", "user-2", "user-1"]],
        [0, 0, 0, []],
        [1024, 1000, 2048, ["a", "b", "c", "d"]],
        [1025, 1000, 2048, ["a", "b", "c", "d"]],
        [100, 4001, 100, ["k%d" % i for i in range(50)]],
        [100, 100, 20480, ["k%d" % i for i in range(50)]],
        [10, 10, 10, ["tenant-42"] * 30],
        [8192, 8000, 100, ["tenant-42"] * 30 + ["tenant-%d" % i for i in range(10)]],
        [5000, 100, 100, ["é", "日本", "x" * 300, ""]],
        [2048, 2001, 4097, ["dev-%d" % (i % 7) for i in range(200)]],
        [16384, 0, 0, ["sensor-%04d" % i for i in range(2000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib
def shardPlan(write_kb_per_s, records_per_s, read_kb_per_s, keys):
    n = max(1, -(-write_kb_per_s // 1024), -(-records_per_s // 1000), -(-read_kb_per_s // 2048))
    counts = [0] * n
    for k in keys:
        counts[int(hashlib.md5(k.encode("utf-8")).hexdigest(), 16) % n] += 1
    return [n, counts]
''',
        '''import hashlib
def shardPlan(write_kb_per_s, records_per_s, read_kb_per_s, keys):
    n = max(1, write_kb_per_s // 1024, records_per_s // 1000, read_kb_per_s // 2048)
    counts = [0] * n
    for k in keys:
        h = int(hashlib.md5(k.encode("utf-8")).hexdigest(), 16)
        counts[h * n // 2 ** 128] += 1
    return [n, counts]
''',
    ],
    guide=dict(
        prereqs="The Kinesis lesson: shards, per-shard limits and partition keys. `hashlib` and integer ceiling division.",
        intuition="Capacity planning is 'the tightest of three limits'. Routing is range partitioning of a hash: scale the 128-bit hash down to an index with multiply-then-divide.",
        hints=["Ceiling division: `-(-a // b)`.", "`int(hexdigest, 16)` gives the 128-bit integer.",
               "`h * n // 2**128` maps the range evenly to `0 … n-1`; this is not the same as `h % n`."],
        brute_force="Building explicit `(start, end)` hash ranges per shard and scanning them for every key is O(keys × shards); the arithmetic mapping is O(keys).",
        approach="Dry run for the example: ceil(3000/1024) = 3, ceil(500/1000) = 1, ceil(1000/2048) = 1 → 3 shards. Hash each key and compute the slice. Identical keys always produce the same hash, so thirty records with the key `tenant-42` land on one shard no matter how many shards exist — a hot shard that adding shards cannot fix.",
        complexity="O(k × L) for k keys of length L; O(n) space.",
        pitfalls="Floor instead of ceiling; modulo instead of range partitioning (real streams use ranges, which is why a shard can be split in two); forgetting the minimum of one shard; forgetting to encode the key as UTF-8.",
    ),
),
]
