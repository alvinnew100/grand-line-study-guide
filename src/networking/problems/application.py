_ZONE = [
    ["www.shop.test", "CNAME", 300, "shop.cdn.test"],
    ["shop.cdn.test", "CNAME", 60, "edge7.cdn.test"],
    ["edge7.cdn.test", "A", 20, "203.0.113.7"],
    ["api.shop.test", "A", 120, "198.51.100.20"],
    ["loop-a.test", "CNAME", 50, "loop-b.test"],
    ["loop-b.test", "CNAME", 50, "loop-a.test"],
    ["dangling.test", "CNAME", 100, "gone.test"],
    ["zero.test", "A", 0, "192.0.2.1"],
]
_CHAIN = [["c%d.test" % i, "CNAME", 10 * (i + 1), "c%d.test" % (i + 1)] for i in range(8)] + [["c8.test", "A", 5, "192.0.2.88"]]
_CHAIN9 = [["d%d.test" % i, "CNAME", 30, "d%d.test" % (i + 1)] for i in range(9)] + [["d9.test", "A", 30, "192.0.2.99"]]

_STATIC_DOC = """| index | name | value |
|---|---|---|
| 1 | `:method` | `GET` |
| 2 | `:method` | `POST` |
| 3 | `:path` | `/` |
| 4 | `:scheme` | `https` |
| 5 | `:status` | `200` |
| 6 | `accept-encoding` | `gzip, deflate` |
| 7 | `content-type` | *(empty)* |
| 8 | `user-agent` | *(empty)* |"""

_HPACK_SOL = '''STATIC = [(":method", "GET"), (":method", "POST"), (":path", "/"), (":scheme", "https"),
          (":status", "200"), ("accept-encoding", "gzip, deflate"), ("content-type", ""), ("user-agent", "")]


def hpack_encode(headers, max_entries):
    dyn = []
    out = []
    for name, value in headers:
        table = STATIC + dyn
        full = None
        name_idx = None
        for i, (n, v) in enumerate(table, 1):
            if n == name:
                if name_idx is None:
                    name_idx = i
                if v == value:
                    full = i
                    break
        if full is not None:
            out.append(["I", full])
            continue
        if name_idx is not None:
            out.append(["N", name_idx, value])
        else:
            out.append(["L", name, value])
        if max_entries > 0:
            dyn.insert(0, (name, value))
            del dyn[max_entries:]
    return out
'''

_REQ1 = [[":method", "GET"], [":scheme", "https"], [":path", "/"], ["user-agent", "demo/1.0"], ["cookie", "sid=abc"]]
_REQ2 = [[":method", "GET"], [":scheme", "https"], [":path", "/cart"], ["user-agent", "demo/1.0"], ["cookie", "sid=abc"]]


def _frame(first, second, ext, key, payload):
    data = [first, second] + ext + key
    if key:
        data += [b ^ key[i % 4] for i, b in enumerate(payload)]
    else:
        data += payload
    return data


PROBLEMS = [
dict(
    id="net-dns-resolver",
    title="DNS Resolver with CNAME Chains and a TTL Cache",
    difficulty="Medium",
    pattern="DNS",
    entry="resolve",
    description=r"""
Simulate a caching resolver in front of an authoritative data set.

`records` is the authoritative data: `[name, type, ttl, value]` with `type` either `"A"` (value is an
address) or `"CNAME"` (value is another name). Each name has at most one record.

`queries` is a list of `[time, name]` with non-decreasing times (seconds). For each query, start at `name`
and repeat:

1. If the cache holds an entry for the current name with `time < expiry`, use it (no upstream lookup).
2. Otherwise perform one **upstream lookup**. If the name has no record, the answer is `"NXDOMAIN"`
   (negative answers are not cached). Otherwise store the record in the cache with `expiry = time + ttl`.
3. An `A` record ends the resolution with its address. A `CNAME` makes its value the current name;
   if this would be the **9th** CNAME followed for this query, stop with `"SERVFAIL"` instead (loop protection).

Return, for every query, `[answer, upstream_lookups]`.

**Example:** `records = [["www.a.test","CNAME",300,"a.test"], ["a.test","A",30,"192.0.2.1"]]`,
`queries = [[0,"www.a.test"], [10,"www.a.test"], [40,"www.a.test"]]`
→ `[["192.0.2.1",2], ["192.0.2.1",0], ["192.0.2.1",1]]`

(At time 40 the CNAME is still cached but the A record, cached at time 0 with TTL 30, has expired.)
""",
    starter='''def resolve(records: list, queries: list) -> list:
    pass
''',
    solution='''def resolve(records, queries):
    zone = {name: (typ, ttl, val) for name, typ, ttl, val in records}
    cache = {}
    out = []
    for now, name in queries:
        lookups = 0
        cur = name
        hops = 0
        while True:
            ent = cache.get(cur)
            if ent is not None and now < ent[2]:
                typ, val = ent[0], ent[1]
            else:
                lookups += 1
                if cur not in zone:
                    ans = "NXDOMAIN"
                    break
                typ, ttl, val = zone[cur]
                cache[cur] = (typ, val, now + ttl)
            if typ == "A":
                ans = val
                break
            hops += 1
            if hops > 8:
                ans = "SERVFAIL"
                break
            cur = val
        out.append([ans, lookups])
    return out
''',
    tests=[
        [[["www.a.test", "CNAME", 300, "a.test"], ["a.test", "A", 30, "192.0.2.1"]], [[0, "www.a.test"], [10, "www.a.test"], [40, "www.a.test"]]],
        [_ZONE, []],
        [[], [[0, "nothing.test"], [1, "nothing.test"]]],
        [_ZONE, [[0, "api.shop.test"], [119, "api.shop.test"], [120, "api.shop.test"], [121, "api.shop.test"]]],
        [_ZONE, [[0, "www.shop.test"], [5, "www.shop.test"], [25, "www.shop.test"], [70, "www.shop.test"], [400, "www.shop.test"]]],
        [_ZONE, [[0, "www.shop.test"], [1, "shop.cdn.test"], [2, "edge7.cdn.test"], [30, "edge7.cdn.test"]]],
        [_ZONE, [[0, "loop-a.test"], [1, "loop-a.test"], [60, "loop-b.test"]]],
        [_ZONE, [[0, "dangling.test"], [10, "dangling.test"], [200, "dangling.test"]]],
        [_ZONE, [[0, "zero.test"], [0, "zero.test"], [1, "zero.test"]]],
        [_CHAIN, [[0, "c0.test"], [4, "c0.test"], [7, "c0.test"], [15, "c0.test"], [100, "c0.test"]]],
        [_CHAIN9, [[0, "d0.test"], [1, "d1.test"], [2, "d0.test"]]],
        [_ZONE, [[t, ["www.shop.test", "api.shop.test", "missing.test", "edge7.cdn.test"][t % 4]] for t in range(0, 600, 7)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def resolve(records, queries):
    zone = {name: (typ, ttl, val) for name, typ, ttl, val in records}
    cache = {}
    out = []
    for now, name in queries:
        lookups, cur, hops = 0, name, 0
        while True:
            if cur in cache:
                typ, val = cache[cur]
            else:
                lookups += 1
                if cur not in zone:
                    ans = "NXDOMAIN"
                    break
                typ, ttl, val = zone[cur]
                cache[cur] = (typ, val)
            if typ == "A":
                ans = val
                break
            hops += 1
            if hops > 8:
                ans = "SERVFAIL"
                break
            cur = val
        out.append([ans, lookups])
    return out
''',
        '''def resolve(records, queries):
    zone = {name: (typ, ttl, val) for name, typ, ttl, val in records}
    cache = {}
    out = []
    for now, name in queries:
        lookups, cur, hops = 0, name, 0
        while True:
            ent = cache.get(cur)
            if ent is not None and now <= ent[2]:
                typ, val = ent[0], ent[1]
            else:
                lookups += 1
                if cur not in zone:
                    ans = "NXDOMAIN"
                    break
                typ, ttl, val = zone[cur]
                cache[cur] = (typ, val, now + ttl)
            if typ == "A":
                ans = val
                break
            hops += 1
            if hops > 8:
                ans = "SERVFAIL"
                break
            cur = val
        out.append([ans, lookups])
    return out
''',
    ],
    guide=dict(
        prereqs="The lessons *How DNS resolution works* and *DNS caching, TTLs, anycast and failures*; dictionaries.",
        intuition="Resolution is a walk along a linked list of names, where every step is either answered from memory or costs one upstream trip. Each link has its own lifetime, so a later query may reuse the first half of a chain and refetch only the part that expired.",
        hints=[
            "Cache per **name**, not per query: store `(type, value, expiry)`.",
            "An entry is usable only while `time < expiry`; at exactly `expiry` it is stale.",
            "Count CNAME hops inside one query and bail out with `SERVFAIL` when the count would exceed 8.",
        ],
        brute_force="No cache at all: every query walks the whole chain upstream. Correct answers, but the lookup counts are wrong and in real life every page view would pay full resolution latency.",
        approach="""1. Index the authoritative records by name.
2. For each query loop: cache hit → use it; miss → count a lookup, handle NXDOMAIN, store with expiry.
3. Stop on an A record; on a CNAME increment the hop count, check the limit, and continue with the target.

**Dry run** (example): t=0 misses `www.a.test` (lookup 1, cached until 300) and `a.test` (lookup 2, cached until 30). t=10: both cached → 0 lookups. t=40: CNAME cached, `a.test` expired (40 ≥ 30) → 1 lookup.""",
        complexity="Time O(chain length) per query, at most 9 steps; space O(number of names cached).",
        pitfalls="Caching the final answer under the original name (ignores the shorter TTL further down the chain). Using `<=` for the expiry test. No loop protection: two CNAMEs pointing at each other spin forever. Caching NXDOMAIN when the specification says not to.",
        follow_up="Add negative caching with the SOA minimum TTL, or cap every TTL at a resolver-chosen maximum and floor, as real resolvers do.",
    ),
),
dict(
    id="net-http-parse",
    title="Parse an HTTP/1.1 Message",
    difficulty="Medium",
    pattern="HTTP",
    entry="parse_http",
    description=r"""
Parse one well-formed HTTP/1.1 message given as a string `raw`. Lines of the head end with `\r\n` and the
head is separated from the body by an empty line (`\r\n\r\n`).

- If the start line begins with `HTTP/` it is a **response** `version status reason` (the reason phrase may
  contain spaces or be missing). Return `["response", version, status_as_int, reason, headers, body]`.
- Otherwise it is a **request** `method target version`. Return `["request", method, target, version, headers, body]`.

`headers` is a dict:

- split each header line at the **first** colon; lower-case the name; strip spaces and tabs around the value;
- if a name repeats, join the values with `", "` in order of appearance.

`body` is everything after the blank line; if a `content-length` header is present, keep only that many
characters. A message with no blank line has an empty body.

**Example:** `"GET /a?b=1 HTTP/1.1\r\nHost: x.test:8080\r\n\r\n"` → `["request", "GET", "/a?b=1", "HTTP/1.1", {"host": "x.test:8080"}, ""]`
""",
    starter='''def parse_http(raw: str) -> list:
    pass
''',
    solution='''def parse_http(raw):
    head, _, body = raw.partition("\\r\\n\\r\\n")
    lines = head.split("\\r\\n")
    start = lines[0]
    headers = {}
    for line in lines[1:]:
        if not line:
            continue
        name, _, value = line.partition(":")
        name = name.strip().lower()
        value = value.strip(" \\t")
        if name in headers:
            headers[name] = headers[name] + ", " + value
        else:
            headers[name] = value
    if "content-length" in headers:
        body = body[:int(headers["content-length"])]
    if start.startswith("HTTP/"):
        parts = start.split(" ", 2)
        reason = parts[2] if len(parts) > 2 else ""
        return ["response", parts[0], int(parts[1]), reason, headers, body]
    method, target, version = start.split(" ")
    return ["request", method, target, version, headers, body]
''',
    tests=[
        ["GET /a?b=1 HTTP/1.1\r\nHost: x.test:8080\r\n\r\n"],
        ["HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nnot here!"],
        ["HTTP/1.1 204\r\n\r\n"],
        ["HTTP/1.1 200 OK\r\nSet-Cookie: a=1\r\nSet-Cookie: b=2\r\nX-Note:   padded value  \r\n\r\nbody"],
        ["POST /submit HTTP/1.1\r\nHost: api.test\r\nContent-Length: 5\r\n\r\nhelloEXTRA"],
        ["POST /submit HTTP/1.1\r\nHost: api.test\r\nCONTENT-LENGTH: 0\r\n\r\nignored"],
        ["DELETE /items/9 HTTP/1.1\r\nHost: api.test"],
        ["OPTIONS * HTTP/1.1\r\nHost: api.test\r\nAccept: text/html\r\naccept: application/json\r\nACCEPT: */*\r\n\r\n"],
        ["HTTP/1.1 301 Moved Permanently\r\nLocation: https://x.test/new?a=b:c\r\nDate: Mon, 02 Mar 2026 10:00:00 GMT\r\n\r\n"],
        ["PUT /blob HTTP/1.1\r\nHost: s.test\r\n\r\nline1\r\n\r\nline3"],
        ["HTTP/1.0 500 Internal Server Error\r\nX-Empty:\r\nX-Tab:\tv\t\r\n\r\n"],
        ["GET / HTTP/1.1\r\n" + "".join("X-H%d: v%d\r\n" % (i % 40, i) for i in range(300)) + "\r\n"],
    ],
    examples=2,
    wrong_solutions=[
        '''def parse_http(raw):
    head, _, body = raw.partition("\\r\\n\\r\\n")
    lines = head.split("\\r\\n")
    start = lines[0]
    headers = {}
    for line in lines[1:]:
        if not line:
            continue
        bits = line.split(":")
        name, value = bits[0].strip().lower(), bits[1].strip(" \\t")
        headers[name] = headers[name] + ", " + value if name in headers else value
    if "content-length" in headers:
        body = body[:int(headers["content-length"])]
    if start.startswith("HTTP/"):
        parts = start.split(" ", 2)
        return ["response", parts[0], int(parts[1]), parts[2] if len(parts) > 2 else "", headers, body]
    method, target, version = start.split(" ")
    return ["request", method, target, version, headers, body]
''',
        '''def parse_http(raw):
    head, _, body = raw.partition("\\r\\n\\r\\n")
    lines = head.split("\\r\\n")
    start = lines[0]
    headers = {}
    for line in lines[1:]:
        if not line:
            continue
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip(" \\t")
    if start.startswith("HTTP/"):
        parts = start.split(" ")
        return ["response", parts[0], int(parts[1]), parts[2] if len(parts) > 2 else "", headers, body]
    method, target, version = start.split(" ")
    return ["request", method, target, version, headers, body]
''',
    ],
    guide=dict(
        prereqs="The lesson *From HTTP/0.9 to HTTP/1.1*: message structure, start line, headers, blank line, body.",
        intuition="An HTTP/1.1 message is text with a rigid skeleton: one start line, zero or more `name: value` lines, a blank line, then opaque bytes. Split on the first blank line, then treat the head line by line.",
        hints=[
            "`str.partition` splits at the first occurrence only, which is what you want both for the blank line and for the header colon.",
            "Decide request or response from the first five characters of the start line.",
            "Split a status line with `split(' ', 2)` so a multi-word reason phrase stays in one piece.",
        ],
        brute_force="Walk the string character by character with a hand-written state machine (as real parsers do for speed and safety). For well-formed input, a few `partition` and `split` calls say the same thing in a dozen lines.",
        approach="""1. `head, _, body = raw.partition('\\r\\n\\r\\n')`.
2. First line of `head` is the start line; each remaining line is partitioned at its first `:`.
3. Normalise names to lower case, strip values, merge duplicates with `", "`.
4. Truncate the body to `content-length` when given.
5. Build the request or response list.

**Dry run:** `HTTP/1.1 404 Not Found` → `split(' ', 2)` → `['HTTP/1.1', '404', 'Not Found']`. Header `Host: x.test:8080` partitions into `Host` and ` x.test:8080`; a naive `split(':')` would lose the port.""",
        complexity="Time O(n) in the message length; space O(n).",
        pitfalls="Splitting header lines on every colon (breaks URLs, times and host:port). Splitting the status line on every space (truncates `Not Found`). Treating header names as case-sensitive. Splitting the whole message on `\\r\\n`, which corrupts bodies containing blank lines.",
        follow_up="Handle `Transfer-Encoding: chunked` (next problem), reject messages with both `Content-Length` and `Transfer-Encoding` (request smuggling), and parse incrementally from a byte stream.",
    ),
),
dict(
    id="net-chunked-decode",
    title="Decode Chunked Transfer Encoding",
    difficulty="Easy",
    pattern="HTTP",
    entry="decode_chunked",
    description=r"""
With `Transfer-Encoding: chunked` an HTTP/1.1 body is sent as a series of chunks so the sender need not know
the total length in advance:

```
<size in hexadecimal>[;extensions]\r\n
<exactly size characters of data>\r\n
...
0\r\n
[optional trailer header lines]\r\n
```

Given the encoded body `data` (well-formed), return the decoded payload.

- The size may use upper- or lower-case hex digits; ignore anything after a `;` on the size line.
- Chunk data can contain any characters, **including `\r\n`**; only the declared size tells you where it ends.
- Stop at the zero-size chunk; ignore trailers.

**Example:** `"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"` → `"Wikipedia"`
""",
    starter='''def decode_chunked(data: str) -> str:
    pass
''',
    solution='''def decode_chunked(data):
    i = 0
    out = []
    while True:
        j = data.index("\\r\\n", i)
        size = int(data[i:j].split(";")[0].strip(), 16)
        i = j + 2
        if size == 0:
            break
        out.append(data[i:i + size])
        i += size + 2
    return "".join(out)
''',
    tests=[
        ["4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"],
        ["0\r\n\r\n"],
        ["1\r\nx\r\n0\r\n\r\n"],
        ["a\r\n0123456789\r\n0\r\n\r\n"],
        ["A\r\n0123456789\r\n1F\r\n" + "z" * 31 + "\r\n0\r\n\r\n"],
        ["10\r\n" + "q" * 16 + "\r\n0\r\n\r\n"],
        ["6\r\nab\r\ncd\r\n2\r\n\r\n\r\n0\r\n\r\n"],
        ["5;name=value\r\nhello\r\n1;x\r\n!\r\n0;last\r\n\r\n"],
        ["3\r\nabc\r\n0\r\nExpires: never\r\nX-Sum: 99\r\n\r\n"],
        ["7\r\n0\r\n\r\n12\r\n0\r\n\r\n"],
        ["".join("%x\r\n%s\r\n" % (n, "k" * n) for n in range(1, 60)) + "0\r\n\r\n"],
        ["3e8\r\n" + "m" * 1000 + "\r\n0\r\n\r\n"],
    ],
    examples=1,
    wrong_solutions=[
        '''def decode_chunked(data):
    i = 0
    out = []
    while True:
        j = data.index("\\r\\n", i)
        size = int(data[i:j].split(";")[0].strip())
        i = j + 2
        if size == 0:
            break
        out.append(data[i:i + size])
        i += size + 2
    return "".join(out)
''',
        '''def decode_chunked(data):
    parts = data.split("\\r\\n")
    out = []
    for k in range(0, len(parts) - 1, 2):
        if int(parts[k].split(";")[0], 16) == 0:
            break
        out.append(parts[k + 1])
    return "".join(out)
''',
    ],
    guide=dict(
        prereqs="The lesson *From HTTP/0.9 to HTTP/1.1* (message framing); hexadecimal.",
        intuition="This is length-prefixed framing. Read a length, read exactly that many characters, skip the trailing CRLF, repeat. The data is never inspected for delimiters.",
        hints=[
            "Keep a cursor index into the string instead of splitting it.",
            "`int(text, 16)` parses the size; cut off extensions with `split(';')[0]` first.",
            "After copying `size` characters, advance by `size + 2` to skip the CRLF that follows the data.",
        ],
        brute_force="Split the whole body on `\\r\\n` and take every second piece. It passes simple cases but breaks as soon as a chunk's data contains a line break, because it trusts delimiters rather than lengths.",
        approach="""1. `i = 0`. Find the next `\\r\\n` from `i`; the text before it is the size line.
2. Parse the hex size. Zero → done.
3. Append `data[i : i+size]`, move `i` past the data and its CRLF.

**Dry run** `"4\\r\\nWiki\\r\\n5\\r\\npedia\\r\\n0\\r\\n\\r\\n"`: size 4 → `Wiki`, cursor to 9. Size 5 → `pedia`, cursor to 19. Size 0 → stop. Result `Wikipedia`.""",
        complexity="Time O(n), space O(n) for the output.",
        pitfalls="Parsing the size as decimal (`10` means sixteen). Searching the data for CRLF. Forgetting chunk extensions. Stopping at an empty data segment instead of at a zero **size**.",
        follow_up="Write the encoder, and a streaming decoder that accepts input in arbitrary pieces (a chunk header may be split across two reads).",
    ),
),
dict(
    id="net-cache-freshness",
    title="Cache-Control Freshness Decision",
    difficulty="Medium",
    pattern="HTTP Caching",
    entry="cache_decision",
    description=r"""
Decide what an HTTP cache may do with a stored response. Inputs:

- `headers`: a dict that may contain `"cache-control"` (a string of comma-separated directives) and the
  integers `"date"` and `"expires"` (already converted to epoch seconds);
- `age`: how many seconds the response has been in caches;
- `shared`: `True` for a shared cache (CDN, proxy), `False` for a private browser cache.

Directive names are case-insensitive and may be surrounded by spaces; some carry `=number`.
Apply these rules **in order** and return the first result that applies:

1. `no-store` present → `"no-store"`.
2. `private` present and the cache is shared → `"no-store"`.
3. `no-cache` present → `"revalidate"`.
4. Compute the freshness lifetime: for a shared cache with `s-maxage`, that value; otherwise `max-age` if
   present; otherwise `max(0, expires - date)` if both keys exist; otherwise `0`.
5. `age < lifetime` → `"fresh"`.
6. `must-revalidate` present, or `proxy-revalidate` present and the cache is shared → `"revalidate"`.
7. `stale-while-revalidate=N` present and `age < lifetime + N` → `"stale-while-revalidate"`.
8. Otherwise → `"revalidate"`.

**Example:** `headers = {"cache-control": "public, max-age=600"}`, `age = 120`, `shared = False` → `"fresh"`

**Example:** `headers = {"cache-control": "max-age=60, stale-while-revalidate=30"}`, `age = 75`, `shared = True` → `"stale-while-revalidate"`
""",
    starter='''def cache_decision(headers: dict, age: int, shared: bool) -> str:
    pass
''',
    solution='''def cache_decision(headers, age, shared):
    d = {}
    for part in headers.get("cache-control", "").split(","):
        part = part.strip().lower()
        if not part:
            continue
        k, _, v = part.partition("=")
        d[k.strip()] = v.strip().strip('"')
    if "no-store" in d:
        return "no-store"
    if shared and "private" in d:
        return "no-store"
    if "no-cache" in d:
        return "revalidate"
    if shared and "s-maxage" in d:
        life = int(d["s-maxage"])
    elif "max-age" in d:
        life = int(d["max-age"])
    elif "expires" in headers and "date" in headers:
        life = max(0, headers["expires"] - headers["date"])
    else:
        life = 0
    if age < life:
        return "fresh"
    if "must-revalidate" in d or (shared and "proxy-revalidate" in d):
        return "revalidate"
    if "stale-while-revalidate" in d and age < life + int(d["stale-while-revalidate"]):
        return "stale-while-revalidate"
    return "revalidate"
''',
    tests=[
        [{"cache-control": "public, max-age=600"}, 120, False],
        [{"cache-control": "max-age=60, stale-while-revalidate=30"}, 75, True],
        [{}, 0, False],
        [{"cache-control": "no-store, max-age=600"}, 1, False],
        [{"cache-control": "private, max-age=600"}, 1, True],
        [{"cache-control": "private, max-age=600"}, 1, False],
        [{"cache-control": "No-Cache , Max-Age=600"}, 1, False],
        [{"cache-control": "max-age=600, s-maxage=30"}, 100, True],
        [{"cache-control": "max-age=600, s-maxage=30"}, 100, False],
        [{"cache-control": "max-age=60"}, 60, False],
        [{"cache-control": "max-age=60"}, 59, False],
        [{"date": 1000, "expires": 1300}, 299, True],
        [{"date": 1000, "expires": 900}, 0, True],
        [{"cache-control": "max-age=10", "date": 1000, "expires": 5000}, 50, False],
        [{"cache-control": "max-age=60, stale-while-revalidate=30, must-revalidate"}, 75, False],
        [{"cache-control": "max-age=60, stale-while-revalidate=30, proxy-revalidate"}, 75, False],
        [{"cache-control": "max-age=60, stale-while-revalidate=30, proxy-revalidate"}, 75, True],
        [{"cache-control": "max-age=60, stale-while-revalidate=30"}, 90, False],
        [{"cache-control": "s-maxage=0, max-age=31536000, immutable"}, 5, True],
    ],
    examples=2,
    wrong_solutions=[
        '''def cache_decision(headers, age, shared):
    d = {}
    for part in headers.get("cache-control", "").split(","):
        part = part.strip().lower()
        if part:
            k, _, v = part.partition("=")
            d[k.strip()] = v.strip()
    if "no-store" in d:
        return "no-store"
    if shared and "private" in d:
        return "no-store"
    if "no-cache" in d:
        return "revalidate"
    if "max-age" in d:
        life = int(d["max-age"])
    elif shared and "s-maxage" in d:
        life = int(d["s-maxage"])
    elif "expires" in headers and "date" in headers:
        life = max(0, headers["expires"] - headers["date"])
    else:
        life = 0
    if age < life:
        return "fresh"
    if "must-revalidate" in d or (shared and "proxy-revalidate" in d):
        return "revalidate"
    if "stale-while-revalidate" in d and age < life + int(d["stale-while-revalidate"]):
        return "stale-while-revalidate"
    return "revalidate"
''',
        '''def cache_decision(headers, age, shared):
    d = {}
    for part in headers.get("cache-control", "").split(","):
        part = part.strip().lower()
        if part:
            k, _, v = part.partition("=")
            d[k.strip()] = v.strip()
    if "no-store" in d or "private" in d:
        return "no-store"
    if "no-cache" in d:
        return "revalidate"
    if shared and "s-maxage" in d:
        life = int(d["s-maxage"])
    elif "max-age" in d:
        life = int(d["max-age"])
    elif "expires" in headers and "date" in headers:
        life = max(0, headers["expires"] - headers["date"])
    else:
        life = 0
    if age <= life:
        return "fresh"
    if "stale-while-revalidate" in d and age < life + int(d["stale-while-revalidate"]):
        return "stale-while-revalidate"
    return "revalidate"
''',
    ],
    guide=dict(
        prereqs="The lesson *HTTP caching, cookies and content negotiation*: Cache-Control directives, freshness lifetime, validation.",
        intuition="A cache asks three questions in order: am I allowed to keep this at all, how long is it good for, and if it has gone off, how strict is the origin about serving it anyway? The rule list is that conversation written down.",
        hints=[
            "Parse the directive string into a dict first; flags map to an empty string, valued directives to their number.",
            "The lifetime has a strict priority: `s-maxage` (shared only), then `max-age`, then `Expires − Date`.",
            "`must-revalidate` is checked before `stale-while-revalidate`: it forbids serving stale content.",
        ],
        brute_force="Chains of `if 'max-age' in header_string` substring tests. They break on case differences, on `s-maxage` containing the text `maxage`, and on spacing; a single tokenising pass removes all of that.",
        approach="""1. Tokenise: split on commas, trim, lower-case, partition on `=`.
2. Walk rules 1–8 in order, returning at the first match.

**Dry run** `max-age=60, stale-while-revalidate=30`, age 75, shared: not `no-store`, not `private`, not `no-cache`. Lifetime 60. `75 < 60` false → not fresh. No `must-revalidate`. `75 < 60 + 30` → `"stale-while-revalidate"`: serve the stored copy now and refresh it in the background.""",
        complexity="Time O(d) in the number of directives; space O(d).",
        pitfalls="Giving `max-age` priority over `s-maxage` in a shared cache. Treating `no-cache` as 'do not store' (it means 'store, but revalidate before every use'). Using `<=` for freshness. Treating `private` as uncacheable in the browser.",
        follow_up="Add the `Age` header arithmetic, heuristic freshness (10% of the time since `Last-Modified`), and request directives such as `max-stale` and `only-if-cached`.",
    ),
),
dict(
    id="net-cookie-match",
    title="Cookie Jar: Which Cookies Are Sent?",
    difficulty="Hard",
    pattern="HTTP State",
    entry="cookies_to_send",
    description=r"""
Implement a small cookie jar. `set_cookies` is a list of `[host, header]` pairs: the `Set-Cookie` header
value received in a response from `host`, in chronological order. Afterwards a request
`[scheme, host, path]` is made; return the exact `Cookie` header value to send (or `""`).

**Storing.** Split the header on `;`. The first piece is `name=value` (split at the first `=`, trim both).
The remaining pieces are attributes with case-insensitive names:

- `Domain=d`: drop one leading `.` and lower-case. If the responding host is neither equal to `d` nor ends
  with `"." + d`, **ignore the whole cookie**. Without a (non-empty) Domain attribute the cookie is *host-only*
  and its domain is the responding host.
- `Path=p`: used if it starts with `/`; otherwise (or if absent) the path is `/`.
- `Secure`: flag.
- `Max-Age=n` (an integer): if `n <= 0` the cookie is a **deletion**.
- Anything else (HttpOnly, SameSite, …) is ignored.

A cookie's identity is `(name, domain, path)`. Storing a cookie with an existing identity replaces the value
and flags but **keeps the original creation order**. A deletion removes the cookie with that identity (if any)
and stores nothing.

**Sending.** A stored cookie is sent when all hold:

- host: host-only cookies need `request host == domain`; others need equality or the request host ending in `"." + domain`;
- path: the request path equals the cookie path, or starts with it and either the cookie path ends in `/` or the
  next character of the request path is `/`;
- `Secure` cookies need scheme `https`.

Order: longer cookie paths first; ties by earlier creation. Join as `name=value` with `"; "`.
Hosts compare case-insensitively.

**Example:** `set_cookies = [["shop.test", "sid=abc; Path=/; Secure"], ["shop.test", "theme=dark; Path=/account"]]`,
`request = ["https", "shop.test", "/account/orders"]` → `"theme=dark; sid=abc"`
""",
    starter='''def cookies_to_send(set_cookies: list, request: list) -> str:
    pass
''',
    solution='''def cookies_to_send(set_cookies, request):
    jar = {}
    order = 0
    for host, header in set_cookies:
        host = host.lower()
        parts = header.split(";")
        name, _, value = parts[0].partition("=")
        name = name.strip()
        value = value.strip()
        domain = None
        path = "/"
        secure = False
        delete = False
        for attr in parts[1:]:
            k, _, v = attr.partition("=")
            k = k.strip().lower()
            v = v.strip()
            if k == "domain" and v:
                if v.startswith("."):
                    v = v[1:]
                domain = v.lower()
            elif k == "path":
                path = v if v.startswith("/") else "/"
            elif k == "secure":
                secure = True
            elif k == "max-age":
                delete = int(v) <= 0
        if domain is None:
            host_only = True
            domain = host
        else:
            host_only = False
            if not (host == domain or host.endswith("." + domain)):
                continue
        key = (name, domain, path)
        if delete:
            jar.pop(key, None)
            continue
        if key in jar:
            seq = jar[key][0]
        else:
            seq = order
            order += 1
        jar[key] = (seq, value, host_only, secure)
    scheme, rhost, rpath = request
    rhost = rhost.lower()
    chosen = []
    for (name, domain, path), (seq, value, host_only, secure) in jar.items():
        if host_only:
            if rhost != domain:
                continue
        elif not (rhost == domain or rhost.endswith("." + domain)):
            continue
        if secure and scheme != "https":
            continue
        if rpath != path:
            if not rpath.startswith(path):
                continue
            if not (path.endswith("/") or rpath[len(path)] == "/"):
                continue
        chosen.append((-len(path), seq, name + "=" + value))
    chosen.sort()
    return "; ".join(c[2] for c in chosen)
''',
    tests=[
        [[["shop.test", "sid=abc; Path=/; Secure"], ["shop.test", "theme=dark; Path=/account"]], ["https", "shop.test", "/account/orders"]],
        [[], ["https", "shop.test", "/"]],
        [[["shop.test", "sid=abc; Path=/; Secure"], ["shop.test", "theme=dark; Path=/account"]], ["http", "shop.test", "/account"]],
        [[["shop.test", "a=1; Path=/app"]], ["https", "shop.test", "/apple"]],
        [[["shop.test", "a=1; Path=/app"], ["shop.test", "b=2; Path=/app/"]], ["https", "shop.test", "/app/x"]],
        [[["shop.test", "a=1; Path=/app/"]], ["https", "shop.test", "/app"]],
        [[["www.shop.test", "wide=1; Domain=shop.test"], ["www.shop.test", "narrow=2"]], ["https", "api.shop.test", "/"]],
        [[["www.shop.test", "wide=1; Domain=.Shop.Test"], ["www.shop.test", "narrow=2"]], ["https", "WWW.shop.test", "/x"]],
        [[["evil.test", "x=1; Domain=shop.test"], ["notshop.test", "y=2; Domain=shop.test"], ["shop.test", "z=3; Domain=shop.test"]], ["https", "shop.test", "/"]],
        [[["shop.test", "x=1; Domain=shop.test"]], ["https", "badshop.test", "/"]],
        [[["shop.test", "a=1"], ["shop.test", "b=2"], ["shop.test", "a=3; HttpOnly; SameSite=Lax"]], ["http", "shop.test", "/"]],
        [[["shop.test", "a=1"], ["shop.test", "b=2"], ["shop.test", "a=; Max-Age=0"], ["shop.test", "c=3; Max-Age=3600"]], ["http", "shop.test", "/"]],
        [[["shop.test", "a=1; Path=/x"], ["shop.test", "a=; Max-Age=0"]], ["http", "shop.test", "/x"]],
        [[["shop.test", "tok=a=b=c; path=relative"], ["shop.test", "  spaced  =  v  ; SECURE"]], ["https", "shop.test", "/deep/er"]],
        [[["a.b.shop.test", "k%d=%d; Domain=%s; Path=%s" % (i, i, ["shop.test", "b.shop.test", "a.b.shop.test"][i % 3], ["/", "/p", "/p/q", "/p/q/r"][i % 4])] for i in range(40)], ["https", "b.shop.test", "/p/q/zzz"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def cookies_to_send(set_cookies, request):
    jar = {}
    order = 0
    for host, header in set_cookies:
        host = host.lower()
        parts = header.split(";")
        name, _, value = parts[0].partition("=")
        name, value = name.strip(), value.strip()
        domain, path, secure, delete = None, "/", False, False
        for attr in parts[1:]:
            k, _, v = attr.partition("=")
            k, v = k.strip().lower(), v.strip()
            if k == "domain" and v:
                domain = v.lstrip(".").lower()
            elif k == "path":
                path = v if v.startswith("/") else "/"
            elif k == "secure":
                secure = True
            elif k == "max-age":
                delete = int(v) <= 0
        host_only = domain is None
        if host_only:
            domain = host
        elif not host.endswith(domain):
            continue
        key = (name, domain, path)
        if delete:
            jar.pop(key, None)
            continue
        seq = jar[key][0] if key in jar else order
        if key not in jar:
            order += 1
        jar[key] = (seq, value, host_only, secure)
    scheme, rhost, rpath = request
    rhost = rhost.lower()
    chosen = []
    for (name, domain, path), (seq, value, host_only, secure) in jar.items():
        if host_only and rhost != domain:
            continue
        if not rhost.endswith(domain):
            continue
        if secure and scheme != "https":
            continue
        if not rpath.startswith(path):
            continue
        chosen.append((-len(path), seq, name + "=" + value))
    chosen.sort()
    return "; ".join(c[2] for c in chosen)
''',
        '''def cookies_to_send(set_cookies, request):
    jar = []
    for host, header in set_cookies:
        parts = header.split(";")
        name, _, value = parts[0].partition("=")
        jar.append((name.strip(), value.strip(), host.lower()))
    scheme, rhost, rpath = request
    return "; ".join(n + "=" + v for n, v, h in jar if h == rhost.lower())
''',
    ],
    guide=dict(
        prereqs="The lesson *HTTP caching, cookies and content negotiation*: Set-Cookie attributes, domain and path scoping.",
        intuition="A cookie is a small record with a scope (domain, path, secure) and an identity (name, domain, path). Storing is upsert-or-delete by identity; sending is a filter by scope followed by a sort.",
        hints=[
            "Parse each header into a record first; keep parsing and matching as two separate phases.",
            "Domain matching needs a dot boundary: `badshop.test` must not match `shop.test`. Path matching needs a slash boundary: `/apple` must not match `/app`.",
            "Use a dict keyed by `(name, domain, path)` holding a creation counter that is assigned once and preserved on replacement.",
        ],
        brute_force="Store every header in a list and, at request time, re-parse them all and resolve replacements by scanning backwards. O(n²) and easy to get wrong; a keyed jar makes replacement and deletion one dictionary operation.",
        approach="""1. For each `Set-Cookie`: parse name/value and attributes; determine host-only vs domain cookie; reject foreign domains; upsert or delete by identity.
2. For the request: keep cookies whose host rule, path rule and secure rule all pass.
3. Sort by `(-len(path), creation)` and join.

**Dry run** (example): `sid` is stored host-only for `shop.test`, path `/`, secure, creation 0; `theme` with path `/account`, creation 1. Request `https://shop.test/account/orders`: both hosts match; `/account/orders` starts with `/account` and the next character is `/` ✓; `/` matches everything ✓. Longer path first → `theme=dark; sid=abc`.""",
        complexity="Time O(n) to store and O(m log m) to select m matching cookies; space O(n).",
        pitfalls="Plain `endswith(domain)` and `startswith(path)` are the classic security bugs. A host-only cookie must not be sent to subdomains. Replacement must not change ordering. A value may itself contain `=`. `Max-Age=0` is how servers delete cookies.",
        follow_up="Add `Expires`, the `SameSite` rules for cross-site requests, the `__Host-` prefix requirements, and public-suffix checks (a site must not set a cookie for `.com`).",
    ),
),
dict(
    id="net-url-normalize",
    title="URL Parsing and Normalisation",
    difficulty="Medium",
    pattern="HTTP",
    entry="normalize_url",
    description=r"""
Caches, crawlers and routers need to recognise that two differently written URLs are the same resource.
Normalise an absolute `http` or `https` URL of the form

`scheme://host[:port][/path][?query][#fragment]`

by applying exactly these steps:

1. Remove the fragment (`#` and everything after it).
2. Lower-case the scheme and the host.
3. Remove the port if it is the scheme's default (`80` for http, `443` for https).
4. In the path and in the query, fix percent-escapes: write the two hex digits in **upper case**, and
   **decode** the escape if it stands for an unreserved character (`A–Z a–z 0–9 - . _ ~`). Leave everything else alone.
5. Remove dot segments from the path: split it on `/`; a `.` segment is dropped; a `..` segment removes the
   previous segment (if any). If the **last** segment was `.` or `..`, the path ends with `/`. Other empty
   segments are kept as they are.
6. An empty path becomes `/`.
7. Keep the query (after step 4) exactly as is; if it is empty, drop the `?`.

Return `scheme://host[:port]path[?query]`. Percent-escapes in the input are always well formed.

**Example:** `"HTTP://Example.TEST:80/a/./b/../c?x=1#top"` → `"http://example.test/a/c?x=1"`

**Example:** `"https://example.test/%7euser/%2fetc"` → `"https://example.test/~user/%2Fetc"`
""",
    starter='''def normalize_url(url: str) -> str:
    pass
''',
    solution='''def normalize_url(url):
    UNRESERVED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")

    def pct(s):
        out = []
        i = 0
        while i < len(s):
            if s[i] == "%":
                hx = s[i + 1:i + 3].upper()
                ch = chr(int(hx, 16))
                out.append(ch if ch in UNRESERVED else "%" + hx)
                i += 3
            else:
                out.append(s[i])
                i += 1
        return "".join(out)

    url = url.split("#", 1)[0]
    scheme, rest = url.split("://", 1)
    scheme = scheme.lower()
    cut = len(rest)
    for ch in "/?":
        k = rest.find(ch)
        if k != -1:
            cut = min(cut, k)
    authority, tail = rest[:cut], rest[cut:]
    path, _, query = tail.partition("?")
    host, _, port = authority.partition(":")
    host = host.lower()
    if port and not ((scheme == "http" and port == "80") or (scheme == "https" and port == "443")):
        host += ":" + port
    path = pct(path)
    query = pct(query)
    if path == "":
        path = "/"
    segs = path.split("/")[1:]
    out = []
    for idx, seg in enumerate(segs):
        last = idx == len(segs) - 1
        if seg == ".":
            if last:
                out.append("")
        elif seg == "..":
            if out:
                out.pop()
            if last:
                out.append("")
        else:
            out.append(seg)
    path = "/" + "/".join(out)
    return scheme + "://" + host + path + ("?" + query if query else "")
''',
    tests=[
        ["HTTP://Example.TEST:80/a/./b/../c?x=1#top"],
        ["https://example.test/%7euser/%2fetc"],
        ["http://example.test"],
        ["http://example.test?"],
        ["https://EXAMPLE.test:443"],
        ["https://example.test:8443/Path/Stays/Mixed?Q=Yes"],
        ["http://example.test:443/x"],
        ["http://example.test/a/b/.."],
        ["http://example.test/a/b/."],
        ["http://example.test/../../a"],
        ["http://example.test/a//b/"],
        ["http://example.test/a/%2e%2e/b"],
        ["http://example.test?q=%41%2f%7E#frag?not=query"],
        ["https://example.test/search?q=a/../b&r=./c"],
        ["http://example.test/%e4%bd%a0/%5Bx%5d"],
        ["HTTPS://A.B.C.example.TEST:80/./x/y/z/../../../../w/"],
    ],
    examples=2,
    wrong_solutions=[
        '''def normalize_url(url):
    url = url.split("#", 1)[0].lower()
    scheme, rest = url.split("://", 1)
    rest = rest.replace(":80", "") if scheme == "http" else rest.replace(":443", "")
    if "/" not in rest:
        rest += "/"
    return scheme + "://" + rest
''',
        '''def normalize_url(url):
    UNRESERVED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
    def pct(s):
        out, i = [], 0
        while i < len(s):
            if s[i] == "%":
                hx = s[i + 1:i + 3].upper()
                ch = chr(int(hx, 16))
                out.append(ch if ch in UNRESERVED else "%" + hx)
                i += 3
            else:
                out.append(s[i])
                i += 1
        return "".join(out)
    url = url.split("#", 1)[0]
    scheme, rest = url.split("://", 1)
    scheme = scheme.lower()
    authority, slash, tail = rest.partition("/")
    path, _, query = (slash + tail).partition("?")
    host, _, port = authority.partition(":")
    host = host.lower()
    if port and not ((scheme == "http" and port == "80") or (scheme == "https" and port == "443")):
        host += ":" + port
    path, query = pct(path) or "/", pct(query)
    out = []
    for seg in path.split("/")[1:]:
        if seg == ".":
            continue
        if seg == "..":
            if out:
                out.pop()
        else:
            out.append(seg)
    return scheme + "://" + host + "/" + "/".join(out) + ("?" + query if query else "")
''',
    ],
    guide=dict(
        prereqs="URL anatomy (see *What happens when you type a URL*); percent-encoding; stacks.",
        intuition="Peel the URL apart from the outside in (fragment, scheme, authority, path, query), normalise each piece by its own rules, and glue it back. Dot-segment removal is a stack: `..` pops.",
        hints=[
            "Remove the fragment first; then the authority ends at the first `/` **or** `?`, whichever comes first.",
            "Only the scheme and host are case-insensitive. Never lower-case the path or query.",
            "For dot segments, push normal segments on a list, pop on `..`, and remember to leave a trailing slash when the final segment was a dot segment.",
        ],
        brute_force="Repeated string replacement (`replace('/./', '/')`, regexes for `/x/../`) until nothing changes. It is quadratic and mishandles edge cases such as leading `..` and trailing dots; a single stack pass is linear and exact.",
        approach="""1. Strip the fragment; split off the scheme at `://`.
2. Cut the authority at the first `/` or `?`; split host and port; drop a default port.
3. Normalise percent-escapes in path and query.
4. Run the segment stack over the path.
5. Reassemble, omitting an empty query.

**Dry run** `/a/./b/../c`: segments `a . b .. c` → push a; skip `.`; push b; `..` pops b; push c → `/a/c`.""",
        complexity="Time O(n), space O(n).",
        pitfalls="Lower-casing the entire URL. Decoding reserved escapes such as `%2F` (changes the meaning: it is data, not a separator). Decoding escapes before splitting would also be wrong. Missing the case where the query appears with no path (`http://h?x=1`). Removing a non-default port.",
        follow_up="Sort query parameters, strip tracking parameters, handle IDN hosts with punycode and IPv6 literals in brackets.",
    ),
),
dict(
    id="net-hpack-toy",
    title="HPACK-Style Header Table Indexing",
    difficulty="Medium",
    pattern="HTTP/2",
    entry="hpack_encode",
    description=(r"""
HTTP/2 compresses headers by referring to entries in a table shared by encoder and decoder. Implement the
encoder for this simplified scheme.

**Static table** (fixed):

""" + _STATIC_DOC + r"""

**Dynamic table.** Starts empty and holds at most `max_entries` entries. New entries are inserted at the
**front**: the newest dynamic entry always has index 9, the next newest 10, and so on. When the table is
over capacity the oldest entry is evicted. With `max_entries = 0` nothing is ever stored.

`headers` is the list of `[name, value]` pairs sent on one connection, in order (possibly several requests
one after another). For each header, search static then dynamic entries in index order:

- if some entry matches both name and value, emit `["I", index]` using the **lowest** such index; the table does not change;
- otherwise, if some entry matches the name, emit `["N", lowest_name_index, value]`;
- otherwise emit `["L", name, value]`.

In the last two cases, insert `(name, value)` into the dynamic table **after** emitting.

Return the list of emitted items.

**Example:** `headers = [[":method","GET"], [":path","/cart"], [":path","/cart"]]`, `max_entries = 4`
→ `[["I",1], ["N",3,"/cart"], ["I",9]]`
"""),
    starter='''def hpack_encode(headers: list, max_entries: int) -> list:
    pass
''',
    solution=_HPACK_SOL,
    tests=[
        [[[":method", "GET"], [":path", "/cart"], [":path", "/cart"]], 4],
        [[], 4],
        [_REQ1, 8],
        [_REQ1 + _REQ2, 8],
        [_REQ1 + _REQ2 + _REQ1, 8],
        [_REQ1 + _REQ2, 0],
        [_REQ1 + _REQ2 + _REQ1, 1],
        [[["x-a", "1"], ["x-b", "2"], ["x-c", "3"], ["x-a", "1"], ["x-b", "2"], ["x-c", "3"]], 2],
        [[["x-a", "1"], ["x-a", "2"], ["x-a", "1"], ["x-a", "3"], ["x-a", "2"]], 3],
        [[["content-type", ""], ["content-type", "text/html"], ["user-agent", ""], ["content-type", "text/html"]], 4],
        [[[":method", "POST"], [":method", "PUT"], [":method", "PUT"], [":status", "200"], [":status", "404"], [":status", "404"]], 5],
        [[["h%d" % (i % 13), "v%d" % (i % 5)] for i in range(120)], 6],
        [[["cookie", "a"], ["cookie", "b"], ["cookie", "a"], ["cookie", "c"], ["cookie", "b"], ["cookie", "a"]], 2],
    ],
    examples=1,
    wrong_solutions=[
        '''STATIC = [(":method", "GET"), (":method", "POST"), (":path", "/"), (":scheme", "https"),
          (":status", "200"), ("accept-encoding", "gzip, deflate"), ("content-type", ""), ("user-agent", "")]


def hpack_encode(headers, max_entries):
    dyn, out = [], []
    for name, value in headers:
        table = STATIC + dyn
        full = name_idx = None
        for i, (n, v) in enumerate(table, 1):
            if n == name:
                if name_idx is None:
                    name_idx = i
                if v == value:
                    full = i
                    break
        if full is not None:
            out.append(["I", full])
            continue
        out.append(["N", name_idx, value] if name_idx is not None else ["L", name, value])
        if max_entries > 0:
            dyn.append((name, value))
            if len(dyn) > max_entries:
                dyn.pop(0)
    return out
''',
        '''STATIC = [(":method", "GET"), (":method", "POST"), (":path", "/"), (":scheme", "https"),
          (":status", "200"), ("accept-encoding", "gzip, deflate"), ("content-type", ""), ("user-agent", "")]


def hpack_encode(headers, max_entries):
    dyn, out = [], []
    for name, value in headers:
        table = STATIC + dyn
        full = name_idx = None
        for i, (n, v) in enumerate(table, 1):
            if n == name:
                if name_idx is None:
                    name_idx = i
                if v == value:
                    full = i
                    break
        if full is not None:
            out.append(["I", full])
            continue
        out.append(["N", name_idx, value] if name_idx is not None else ["L", name, value])
        dyn.insert(0, (name, value))
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *HTTP/2: streams, multiplexing and HPACK*.",
        intuition="Most headers repeat from one request to the next. If both ends remember what was sent, a repeated header shrinks to a small number. The only subtlety is the numbering: new entries push older ones to higher indices, like a stack of plates with the newest on top.",
        hints=[
            "Model the dynamic table as a list with the newest entry at position 0; index = 9 + position.",
            "Search before you insert: the header being encoded cannot refer to itself.",
            "Stop at the first full match, but remember the first name-only match on the way in case no full match exists.",
        ],
        brute_force="Send every header literally (`[\"L\", name, value]`). Always decodable, zero compression: this is what HTTP/1.1 does, and why its header overhead is hundreds of bytes per request.",
        approach="""1. For each header scan `STATIC + dynamic` with indices starting at 1, recording the first name match and stopping at the first full match.
2. Emit `I`, `N` or `L` accordingly.
3. For `N` and `L`, insert at the front and trim the list to `max_entries`.

**Dry run** (example): `:method GET` is static entry 1 → `["I",1]`. `:path /cart`: name matches static 3, no full match → `["N",3,"/cart"]`, table becomes `[(:path,/cart)]`. Again `:path /cart`: static 3 matches the name only; dynamic index 9 matches fully → `["I",9]`.""",
        complexity="Time O(h·(S + max_entries)) with a linear scan; real encoders keep hash maps for O(1) lookups. Space O(max_entries).",
        pitfalls="Appending to the end of the dynamic table (indices then point at the wrong entries after the first eviction, and the decoder desynchronises). Inserting on an indexed hit. Forgetting `max_entries = 0`. Returning the first *name* match when a later *full* match exists.",
        follow_up="Real HPACK measures the table in bytes (name + value + 32 per entry), Huffman-codes strings, and has a never-indexed form for secrets. QPACK (HTTP/3) changes the design so a lost packet cannot stall header decoding.",
    ),
),
dict(
    id="net-websocket-frame",
    title="Decode a WebSocket Frame",
    difficulty="Medium",
    pattern="Framing",
    entry="decode_frame",
    description=r"""
Decode one WebSocket frame (RFC 6455) from `data`, a list of byte values. Layout:

```
byte 0:  FIN (bit 7) | RSV1-3 (bits 6-4, ignore) | opcode (bits 3-0)
byte 1:  MASK (bit 7) | payload length indicator (bits 6-0)
         indicator 0-125 : that is the payload length
         indicator 126   : the next 2 bytes hold the length (big-endian)
         indicator 127   : the next 8 bytes hold the length (big-endian)
then:    4-byte masking key, only if MASK is set
then:    the payload
```

If MASK is set, the real payload byte `i` is `payload[i] XOR key[i % 4]`.

Return `[fin, opcode, masked, payload_length, payload]` where `fin` and `masked` are booleans and `payload`
is the list of **unmasked** byte values. If `data` is too short to contain the complete frame, return `[]`.
Bytes after the end of the frame are ignored.

**Example:** `[0x81, 0x02, 0x48, 0x69]` → `[True, 1, False, 2, [72, 105]]` (an unmasked text frame "Hi")
""",
    starter='''def decode_frame(data: list) -> list:
    pass
''',
    solution='''def decode_frame(data):
    if len(data) < 2:
        return []
    fin = bool(data[0] & 0x80)
    opcode = data[0] & 0x0F
    masked = bool(data[1] & 0x80)
    length = data[1] & 0x7F
    pos = 2
    if length == 126:
        if len(data) < 4:
            return []
        length = (data[2] << 8) | data[3]
        pos = 4
    elif length == 127:
        if len(data) < 10:
            return []
        length = 0
        for b in data[2:10]:
            length = (length << 8) | b
        pos = 10
    key = []
    if masked:
        if len(data) < pos + 4:
            return []
        key = data[pos:pos + 4]
        pos += 4
    if len(data) < pos + length:
        return []
    payload = data[pos:pos + length]
    if masked:
        payload = [b ^ key[i % 4] for i, b in enumerate(payload)]
    return [fin, opcode, masked, length, payload]
''',
    tests=[
        [[0x81, 0x02, 0x48, 0x69]],
        [[0x81, 0x85, 0x37, 0xfa, 0x21, 0x3d, 0x7f, 0x9f, 0x4d, 0x51, 0x58]],
        [[]],
        [[0x81]],
        [[0x89, 0x00]],
        [[0x8A, 0x80, 1, 2, 3, 4]],
        [[0x8A, 0x80, 1, 2, 3]],
        [[0x01, 0x03, 0x61, 0x62]],
        [[0x01, 0x03, 0x61, 0x62, 0x63, 0x99, 0x98]],
        [_frame(0x82, 0x7E, [0x00, 0xC8], [], [i % 256 for i in range(200)])],
        [_frame(0x82, 0xFE, [0x01, 0x2C], [9, 8, 7, 6], [(i * 3) % 256 for i in range(300)])],
        [_frame(0x82, 0xFE, [0x01, 0x2C], [9, 8, 7, 6], [(i * 3) % 256 for i in range(300)])[:-1]],
        [[0x82, 0x7E, 0x00]],
        [_frame(0xF2, 0x7F, [0, 0, 0, 0, 0, 0, 0x01, 0x00], [], [7] * 256)],
        [_frame(0x88, 0xFF, [0, 0, 0, 0, 0, 0, 0, 0x05], [0xAA, 0xBB, 0xCC, 0xDD], [3, 232, 79, 75, 33])],
        [[0x82, 0xFF, 0, 0, 0, 0, 0, 0, 0]],
        [[0x08, 0x7D] + [1] * 125],
    ],
    examples=2,
    wrong_solutions=[
        '''def decode_frame(data):
    if len(data) < 2:
        return []
    fin = bool(data[0] & 0x80)
    opcode = data[0] & 0x0F
    masked = bool(data[1] & 0x80)
    length = data[1] & 0x7F
    pos = 2
    if length == 126:
        if len(data) < 4:
            return []
        length = (data[2] << 8) | data[3]
        pos = 4
    elif length == 127:
        if len(data) < 10:
            return []
        length = 0
        for b in data[2:10]:
            length = (length << 8) | b
        pos = 10
    if masked:
        pos += 4
    if len(data) < pos + length:
        return []
    return [fin, opcode, masked, length, data[pos:pos + length]]
''',
        '''def decode_frame(data):
    if len(data) < 2:
        return []
    fin = bool(data[0] & 0x80)
    opcode = data[0] & 0x0F
    masked = bool(data[1] & 0x80)
    length = data[1] & 0x7F
    pos = 2
    key = []
    if masked:
        if len(data) < pos + 4:
            return []
        key = data[pos:pos + 4]
        pos += 4
    if len(data) < pos + length:
        return []
    payload = data[pos:pos + length]
    if masked:
        payload = [b ^ key[i % 4] for i, b in enumerate(payload)]
    return [fin, opcode, masked, length, payload]
''',
    ],
    guide=dict(
        prereqs="The lesson *WebSocket, WebRTC and choosing a transport*; bit masks and XOR.",
        intuition="The header is variable-length, so decode it as a cursor walk: fixed two bytes, then an optional extended length, then an optional key, then the payload. At every step check that enough bytes remain before reading them.",
        hints=[
            "`byte & 0x80` tests the top bit; `byte & 0x0F` and `byte & 0x7F` extract the low fields.",
            "Keep a `pos` variable for where the next field starts; the 126 and 127 cases move it to 4 and 10.",
            "Unmask with `payload[i] ^ key[i % 4]`. XOR is its own inverse, so masking and unmasking are the same operation.",
        ],
        brute_force="Write three separate decoders for the three length encodings, each duplicated for masked and unmasked frames. Six code paths; the cursor approach has one.",
        approach="""1. Need at least 2 bytes. Extract FIN, opcode, MASK, 7-bit length.
2. Extended length: 126 → 2 bytes, 127 → 8 bytes, big-endian.
3. If masked, read the 4-byte key.
4. Check that the payload is fully present, slice it, unmask if needed.

**Dry run** `81 85 37 fa 21 3d 7f 9f 4d 51 58`: `0x81` → FIN, opcode 1 (text). `0x85` → masked, length 5. Key `37 fa 21 3d`. Payload `7f^37=48 'H'`, `9f^fa=65 'e'`, `4d^21=6c 'l'`, `51^3d=6c 'l'`, `58^37=6f 'o'` → "Hello".""",
        complexity="Time O(n) in the payload length; space O(n).",
        pitfalls="Treating 126/127 as actual lengths. Reading the key before the extended length. Forgetting to unmask (client-to-server frames are always masked; server-to-client never). Indexing past the end on truncated input instead of returning `[]`.",
        follow_up="Reassemble fragmented messages (FIN = 0 followed by continuation frames, opcode 0), and handle interleaved control frames (ping 0x9, pong 0xA, close 0x8).",
    ),
),
]
