_LINE = ('203.0.113.9 - rosa [21/Nov/2026:14:02:11 +0800] "GET /products/42?ref=mail HTTP/2.0" '
         '200 5123 "https://shop.test/" "Mozilla/5.0 (X11; Linux x86_64)"')

_GZ = {"enabled": True, "min_length": 1024, "types": ["text/css", "application/json"], "proxied": "off", "http_version": "1.1"}
_REQ = {"accept_encoding": "gzip, deflate, br", "http_version": "1.1", "via": ""}
_RES = {"status": 200, "content_type": "application/json", "content_length": 5000, "content_encoding": ""}


def _entries(n):
    """Deterministic synthetic log: [address, status, request_time]."""
    out = []
    for i in range(n):
        addr = "10.0.%d.%d" % (i % 7, (i * 13) % 5)
        status = 502 if i % 23 == 0 else (404 if i % 11 == 0 else 200)
        out.append([addr, status, ((i * 37) % 400) / 100])
    return out


PROBLEMS = [
dict(
    id="nginx-log-parse",
    title="Parse an Access Log Line",
    difficulty="Medium",
    pattern="Logging",
    entry="parse_log",
    description=r"""
Turn one line of NGINX's default `combined` access log into a dictionary. The format is

```
$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
```

`parse_log(line)` returns a dictionary with these keys, or `None` if the line does not have this shape:

| Key | Value |
|---|---|
| `addr`, `user`, `time`, `referer`, `agent` | the text of the field, unchanged (`-` stays `-`) |
| `status`, `bytes` | integers |
| `method`, `uri`, `protocol` | the three space-separated parts of the request |

Details:

- Ignore whitespace at the ends of the line. The line must contain exactly these fields and nothing after them.
- The address and user contain no spaces. The time is whatever stands between `[` and `]`. The status is exactly
  three digits. Quoted fields contain no `"` (NGINX writes a quote inside a value as `\x22`).
- Scanners send requests that are not HTTP. If the quoted request does not consist of exactly three parts separated
  by single spaces, set `method` and `protocol` to `""` and `uri` to the whole request text.

**Example:** `203.0.113.9 - rosa [21/Nov/2026:14:02:11 +0800] "GET /a?b=1 HTTP/1.1" 200 512 "-" "curl/8.5.0"`
→ `{"addr": "203.0.113.9", "user": "rosa", "time": "21/Nov/2026:14:02:11 +0800", "method": "GET", "uri": "/a?b=1", "protocol": "HTTP/1.1", "status": 200, "bytes": 512, "referer": "-", "agent": "curl/8.5.0"}`
""",
    starter='''import re

def parse_log(line):
    # return a dictionary of fields, or None
    pass
''',
    solution=r'''import re

_PATTERN = re.compile(r'^(\S+) - (\S+) \[([^\]]+)\] "([^"]*)" (\d{3}) (\d+) "([^"]*)" "([^"]*)"$')

def parse_log(line):
    m = _PATTERN.match(line.strip())
    if not m:
        return None
    addr, user, when, request, status, size, referer, agent = m.groups()
    parts = request.split(" ")
    if len(parts) == 3 and all(parts):
        method, uri, protocol = parts
    else:
        method, uri, protocol = "", request, ""
    return {"addr": addr, "user": user, "time": when, "method": method, "uri": uri, "protocol": protocol,
            "status": int(status), "bytes": int(size), "referer": referer, "agent": agent}
''',
    tests=[
        ['203.0.113.9 - rosa [21/Nov/2026:14:02:11 +0800] "GET /a?b=1 HTTP/1.1" 200 512 "-" "curl/8.5.0"'],
        [_LINE],
        ['198.51.100.4 - - [21/Nov/2026:14:02:12 +0800] "\\x16\\x03\\x01" 400 157 "-" "-"'],
        ['2001:db8::7 - - [21/Nov/2026:14:02:13 +0800] "POST /api/login HTTP/2.0" 429 0 "https://shop.test/login" "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"\n'],
        [""],
        ["not a log line at all"],
        ['203.0.113.9 - rosa [21/Nov/2026:14:02:11 +0800] "GET / HTTP/1.1" 200 512 "-" "curl/8.5.0" rt=0.004'],
        ['203.0.113.9 - rosa [21/Nov/2026:14:02:11 +0800] "GET / HTTP/1.1" OK 512 "-" "curl/8.5.0"'],
        ['203.0.113.9 - - [21/Nov/2026:14:02:11 +0800] "GET /a b HTTP/1.1" 400 0 "-" "-"'],
        ['203.0.113.9 - - [21/Nov/2026:14:02:11 +0800] "" 400 0 "-" "-"'],
        ['10.0.0.1 - - [01/Jan/2027:00:00:00 +0000] "HEAD /healthz HTTP/1.0" 204 0 "" ""'],
        ['203.0.113.9 rosa [21/Nov/2026:14:02:11 +0800] "GET / HTTP/1.1" 200 512 "-" "curl/8.5.0"'],
        ['   172.16.0.9 - bot [21/Nov/2026:23:59:59 +0800] "GET /big.iso HTTP/1.1" 206 9482113000 "-" "Wget/1.21"   '],
    ],
    examples=1,
    wrong_solutions=[
        '''def parse_log(line):
    f = line.strip().split(" ")
    if len(f) < 12:
        return None
    try:
        return {"addr": f[0], "user": f[2], "time": (f[3] + " " + f[4]).strip("[]"), "method": f[5].strip('"'),
                "uri": f[6], "protocol": f[7].strip('"'), "status": int(f[8]), "bytes": int(f[9]),
                "referer": f[10].strip('"'), "agent": " ".join(f[11:]).strip('"')}
    except ValueError:
        return None
''',
        r'''import re

def parse_log(line):
    m = re.match(r'^(\S+) - (\S+) \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+) "([^"]*)" "([^"]*)"$', line.strip())
    if not m:
        return None
    g = m.groups()
    return {"addr": g[0], "user": g[1], "time": g[2], "method": g[3], "uri": g[4], "protocol": g[5],
            "status": int(g[6]), "bytes": int(g[7]), "referer": g[8], "agent": g[9]}
''',
    ],
    guide=dict(
        prereqs="Lesson: *Access logs, error logs and request tracing*. Regular expressions with groups.",
        intuition="The line is a sentence with fixed punctuation: a hyphen, square brackets around the time, quotes around three free-text fields. Describe that punctuation in one regular expression and let it cut the fields out. Splitting on spaces cannot work, because the time and the user agent contain spaces.",
        hints=[
            "Anchor the pattern at both ends with `^` and `$` so that lines with extra fields are rejected.",
            "Capture the whole quoted request first, then split it yourself. That keeps malformed requests from making the whole line fail.",
            "Use `[^\"]*` for quoted fields and `[^\\]]+` for the time.",
        ],
        brute_force="`line.split(\" \")` and pick fields by position. It breaks on the first user agent containing a space, and on any request that is not three words.",
        approach="1. Compile one pattern with eight groups.\n2. `match` against the stripped line; no match → `None`.\n3. Split the request on single spaces; exactly three non-empty parts → method, URI, protocol; otherwise keep it whole as the URI.\n4. Convert status and bytes to integers and build the dictionary.\n\nDry run on the scanner line with request `\\x16\\x03\\x01`: the overall pattern matches, the request has one part, so `method=\"\"`, `uri=\"\\x16\\x03\\x01\"`, `protocol=\"\"`, status 400.",
        complexity="Time O(length of the line); space O(length of the line).",
        pitfalls="Splitting on spaces; returning `None` for malformed requests, which hides attack traffic from the statistics; accepting lines from a different log format; forgetting IPv6 addresses contain colons, not dots.",
        follow_up="Parse a custom format with `rt=$request_time urt=$upstream_response_time`, where the upstream time may be `-` or a comma-separated list after retries.",
    ),
),
dict(
    id="nginx-log-topn",
    title="Summarise an Access Log: Top Clients, Error Rate, p95",
    difficulty="Medium",
    pattern="Logging",
    entry="log_summary",
    description=r"""
Given parsed access-log entries, compute the three numbers an on-call engineer asks for first.

`log_summary(entries, n)` receives `entries`, a list of `[address, status, request_time]`, and returns
`[top, error_rate, p95]`:

- `top`: the `n` addresses with the most requests, as `[address, count]` pairs, highest count first. Break ties by
  address in ascending string order. If there are fewer than `n` distinct addresses, return them all.
- `error_rate`: the fraction of entries with a status from 500 to 599, rounded to 4 decimal places.
- `p95`: the 95th percentile of `request_time` by the **nearest-rank** method: sort the times in ascending order and
  take the value at position `ceil(0.95 * count)`, counting from 1.

For an empty list return `[[], 0.0, 0.0]`.

**Example:** `[["a", 200, 0.1], ["b", 502, 2.0], ["a", 200, 0.3], ["a", 404, 0.2]]`, `n=1`
→ `[[["a", 3]], 0.25, 2.0]`
""",
    starter='''def log_summary(entries, n):
    # return [top, error_rate, p95]
    pass
''',
    solution='''def log_summary(entries, n):
    if not entries:
        return [[], 0.0, 0.0]
    counts = {}
    for addr, status, rt in entries:
        counts[addr] = counts.get(addr, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    errors = sum(1 for e in entries if 500 <= e[1] <= 599)
    times = sorted(e[2] for e in entries)
    rank = -(-95 * len(times) // 100)
    return [[[a, c] for a, c in ranked], round(errors / len(entries), 4), times[rank - 1]]
''',
    tests=[
        [[["a", 200, 0.1], ["b", 502, 2.0], ["a", 200, 0.3], ["a", 404, 0.2]], 1],
        [[], 3],
        [[["x", 200, 1.5]], 5],
        [[["b", 200, 0.1], ["a", 200, 0.2], ["c", 200, 0.3], ["b", 500, 0.4], ["a", 599, 0.5], ["c", 600, 0.6]], 2],
        [[["10.0.0.%d" % (i % 4), 200, float(i)] for i in range(1, 21)], 4],
        [[["10.0.0.1", 200, float(i)] for i in range(1, 101)], 1],
        [[["10.0.0.1", 503, 0.5]] * 3 + [["10.0.0.2", 200, 0.1]] * 3, 0],
        [[["z", 499, 30.0], ["y", 499, 30.0], ["x", 499, 30.0]], 2],
        [_entries(19), 3],
        [_entries(40), 3],
        [_entries(1000), 5],
        [[["a", 500, 9.0], ["a", 200, 0.1], ["a", 200, 0.1]], 1],
    ],
    examples=1,
    wrong_solutions=[
        '''def log_summary(entries, n):
    if not entries:
        return [[], 0.0, 0.0]
    counts = {}
    for addr, status, rt in entries:
        counts[addr] = counts.get(addr, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    errors = sum(1 for e in entries if 500 <= e[1] <= 599)
    times = sorted(e[2] for e in entries)
    return [[[a, c] for a, c in ranked], round(errors / len(entries), 4), times[int(0.95 * len(times))]]
''',
        '''def log_summary(entries, n):
    if not entries:
        return [[], 0.0, 0.0]
    counts = {}
    for addr, status, rt in entries:
        counts[addr] = counts.get(addr, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:n]
    errors = sum(1 for e in entries if e[1] >= 400)
    times = sorted(e[2] for e in entries)
    rank = -(-95 * len(times) // 100)
    return [[[a, c] for a, c in ranked], round(errors / len(entries), 4), times[rank - 1]]
''',
    ],
    guide=dict(
        prereqs="Lessons: *Access logs, error logs and request tracing* and *Workers, connections, keepalive and OS tuning* (percentiles). Sorting with a key.",
        intuition="Three classic aggregations over one list: a frequency count, a ratio, and an order statistic. Each answers a different question: who is hitting us, how much is failing, and how slow is the slow tail.",
        hints=[
            "Count with a dictionary, then sort the items by `(-count, address)` to get both orderings in one key.",
            "Only 5xx counts as a server error here. 4xx and NGINX's 499 are the client's doing.",
            "Nearest rank needs a ceiling. With integers, `-(-95 * n // 100)` is `ceil(0.95 * n)` without floating point.",
        ],
        brute_force="For the top list, repeatedly scan for the most frequent remaining address: O(n × distinct). Sorting the counts once is O(d log d).",
        approach="1. Empty input → the fixed answer.\n2. Count addresses; sort; cut to `n`.\n3. Count statuses in 500..599; divide; round.\n4. Sort the times; rank = ceil(0.95 × count); take index `rank - 1`.\n\nDry run of the example: counts a=3, b=1 → top 1 is `[a, 3]`. One 5xx out of four → 0.25. Sorted times 0.1, 0.2, 0.3, 2.0; rank = ceil(3.8) = 4 → 2.0.",
        complexity="Time O(n log n) for the two sorts; space O(n).",
        pitfalls="An off-by-one in the percentile (indexing with `int(0.95 * n)` picks the next element); leaving tie order to chance; counting 4xx as errors; dividing by zero on an empty log; float rounding in `0.95 * n` for sizes such as 20.",
        follow_up="Process a log too large for memory: keep the counts in a dictionary but estimate the percentile from a fixed-size histogram of buckets.",
    ),
),
dict(
    id="nginx-status-diagnosis",
    title="502, 504 or 499? Follow the Upstream Attempts",
    difficulty="Medium",
    pattern="Troubleshooting",
    entry="upstream_outcome",
    description=r"""
Work out the status code a proxied request ends with, and after how many seconds, when NGINX tries upstream servers
one after another.

`upstream_outcome(attempts, connect_timeout, read_timeout, client_patience)`:

- `attempts` lists, in the order NGINX tries them, what each server does:
  - `["refused"]`: the connection is refused at once. Takes 0 seconds. An error.
  - `["closed"]`: the server accepts and immediately closes without answering. 0 seconds. An error.
  - `["connect_hang"]`: no reply to the connection attempt. NGINX gives up after `connect_timeout` seconds. A timeout.
  - `["respond", s]`: the server connects at once and sends its response after `s` seconds. If `s > read_timeout`,
    NGINX gives up after `read_timeout` seconds: a timeout. Otherwise the request succeeds after `s` seconds.
- After an error or timeout NGINX moves to the next attempt, and the time spent adds up.
- A success ends with status `200`.
- If every attempt fails, the status comes from the **last** failure: `502` for an error, `504` for a timeout.
- An empty list means no server was available: `502` after 0 seconds.
- The client waits `client_patience` seconds in total. If the moment of the final outcome, successful or not, is
  **later** than that, the result is `[499, client_patience]`: the client closed the connection first.

Return `[status, seconds]`.

**Example:** `[["refused"], ["respond", 2]]`, `5`, `60`, `120` → `[200, 2]`

**Example:** `[["connect_hang"], ["respond", 90]]`, `5`, `60`, `120` → `[504, 65]`
""",
    starter='''def upstream_outcome(attempts, connect_timeout, read_timeout, client_patience):
    # return [status, seconds]
    pass
''',
    solution='''def upstream_outcome(attempts, connect_timeout, read_timeout, client_patience):
    elapsed = 0
    status = 502
    for attempt in attempts:
        kind = attempt[0]
        if kind in ("refused", "closed"):
            status = 502
        elif kind == "connect_hang":
            elapsed += connect_timeout
            status = 504
        elif attempt[1] > read_timeout:
            elapsed += read_timeout
            status = 504
        else:
            elapsed += attempt[1]
            status = 200
            break
    if elapsed > client_patience:
        return [499, client_patience]
    return [status, elapsed]
''',
    tests=[
        [[["refused"], ["respond", 2]], 5, 60, 120],
        [[["connect_hang"], ["respond", 90]], 5, 60, 120],
        [[["respond", 1]], 5, 60, 120],
        [[["refused"]], 5, 60, 120],
        [[], 5, 60, 120],
        [[["respond", 90]], 5, 60, 120],
        [[["respond", 90]], 5, 120, 120],
        [[["respond", 90]], 5, 120, 30],
        [[["connect_hang"], ["connect_hang"], ["connect_hang"]], 60, 60, 120],
        [[["connect_hang"], ["refused"]], 3, 60, 120],
        [[["refused"], ["connect_hang"]], 3, 60, 120],
        [[["closed"], ["closed"], ["respond", 0]], 3, 60, 120],
        [[["respond", 60]], 3, 60, 60],
        [[["respond", 61], ["respond", 61]], 3, 60, 120],
        [[["connect_hang"], ["respond", 10], ["refused"]], 5, 60, 12],
    ],
    examples=2,
    wrong_solutions=[
        '''def upstream_outcome(attempts, connect_timeout, read_timeout, client_patience):
    if not attempts:
        return [502, 0]
    kind = attempts[0][0]
    if kind in ("refused", "closed"):
        status, elapsed = 502, 0
    elif kind == "connect_hang":
        status, elapsed = 504, connect_timeout
    elif attempts[0][1] > read_timeout:
        status, elapsed = 504, read_timeout
    else:
        status, elapsed = 200, attempts[0][1]
    if elapsed > client_patience:
        return [499, client_patience]
    return [status, elapsed]
''',
        '''def upstream_outcome(attempts, connect_timeout, read_timeout, client_patience):
    elapsed = 0
    status = 502
    for attempt in attempts:
        kind = attempt[0]
        if kind in ("refused", "closed"):
            status = 502
        elif kind == "connect_hang":
            elapsed += connect_timeout
            status = 504
        elif attempt[1] > read_timeout:
            elapsed += read_timeout
            status = 504
        else:
            elapsed += attempt[1]
            status = 200
            break
    return [status, elapsed]
''',
        '''def upstream_outcome(attempts, connect_timeout, read_timeout, client_patience):
    elapsed = 0
    statuses = []
    for attempt in attempts:
        kind = attempt[0]
        if kind in ("refused", "closed"):
            statuses.append(502)
        elif kind == "connect_hang":
            elapsed += connect_timeout
            statuses.append(504)
        elif attempt[1] >= read_timeout:
            elapsed += read_timeout
            statuses.append(504)
        else:
            elapsed += attempt[1]
            statuses.append(200)
            break
    if elapsed > client_patience:
        return [499, client_patience]
    if 200 in statuses:
        return [200, elapsed]
    return [statuses[0] if statuses else 502, elapsed]
''',
    ],
    guide=dict(
        prereqs="Lesson: *A troubleshooting method and the gateway status codes*. Loops and conditionals.",
        intuition="The gateway codes describe how the *last* conversation with an upstream ended. Refusals and early closes are errors (502). Silence until a timer expires is a timeout (504). Retries on other servers add their waiting time together, and if the total exceeds what the client will tolerate, the client is gone before any of it matters (499).",
        hints=[
            "Keep a running clock and a current status while walking the attempts.",
            "Stop at the first success; otherwise the status after the loop is that of the last failure.",
            "Check the client's patience once, at the end, against the total elapsed time.",
        ],
        brute_force="Looking only at the first attempt gives the right answer for a single server and the wrong one whenever NGINX retries, which is the normal case with an upstream group.",
        approach="1. `elapsed = 0`, `status = 502` (the answer for an empty list).\n2. For each attempt: error → 502, no time. Hang → add `connect_timeout`, 504. Slow → add `read_timeout`, 504. Otherwise add its time, 200, stop.\n3. If `elapsed > client_patience` → `[499, client_patience]`, else `[status, elapsed]`.\n\nDry run: `[connect_hang], [respond 90]` with timeouts 5 and 60. The first attempt costs 5 s (504). The second would answer after 90 s, more than 60, so NGINX gives up after 60 more: total 65 s, status 504.",
        complexity="Time O(number of attempts); space O(1).",
        pitfalls="Reporting the first failure instead of the last; forgetting to add timeouts from earlier attempts; using `>=` at the read-timeout boundary; ignoring the client's own timeout, which is why many real 504 investigations find 499 in the log instead.",
        follow_up="Add `proxy_next_upstream_timeout` (a cap on the total time spent retrying) and `proxy_next_upstream_tries`, and the rule that a non-idempotent request is not retried once it has been sent.",
    ),
),
dict(
    id="nginx-worker-capacity",
    title="How Many Clients Can This NGINX Serve?",
    difficulty="Easy",
    pattern="Performance",
    entry="worker_capacity",
    description=r"""
Estimate how many clients one NGINX instance can serve at the same moment, and name the limit that decides.

`worker_capacity(worker_processes, worker_connections, nofile_limit, proxying)` returns `[clients, bottleneck]`.

Model, per worker process:

- Each client needs **connections** from the worker's `worker_connections` budget: 1 when NGINX serves the content
  itself, 2 when `proxying` is true (one to the client, one to the upstream).
- Each client needs **2 file descriptors** from the worker's `nofile_limit` budget (a socket and a file, or two
  sockets).
- Clients per worker by connections = `worker_connections // connections_per_client`.
- Clients per worker by descriptors = `nofile_limit // 2`.
- The smaller of the two applies. `bottleneck` is `"worker_connections"` if the connection figure is smaller or the
  two are equal, otherwise `"file descriptors"`.

`clients` is that per-worker figure multiplied by `worker_processes`.

**Example:** `4, 1024, 1024, True` → `[2048, "worker_connections"]`

**Example:** `4, 8192, 1024, True` → `[2048, "file descriptors"]`
""",
    starter='''def worker_capacity(worker_processes, worker_connections, nofile_limit, proxying):
    # return [clients, bottleneck]
    pass
''',
    solution='''def worker_capacity(worker_processes, worker_connections, nofile_limit, proxying):
    by_connections = worker_connections // (2 if proxying else 1)
    by_descriptors = nofile_limit // 2
    if by_connections <= by_descriptors:
        return [worker_processes * by_connections, "worker_connections"]
    return [worker_processes * by_descriptors, "file descriptors"]
''',
    tests=[
        [4, 1024, 1024, True],
        [4, 8192, 1024, True],
        [1, 512, 1024, False],
        [1, 512, 1024, True],
        [4, 8192, 20000, True],
        [8, 4096, 4096, False],
        [8, 4096, 8192, False],
        [2, 1025, 65535, True],
        [16, 65535, 65535, False],
        [1, 1, 2, True],
        [3, 1000, 1001, True],
        [32, 100000, 1048576, True],
    ],
    examples=2,
    wrong_solutions=[
        '''def worker_capacity(worker_processes, worker_connections, nofile_limit, proxying):
    by_connections = worker_connections
    by_descriptors = nofile_limit // 2
    if by_connections <= by_descriptors:
        return [worker_processes * by_connections, "worker_connections"]
    return [worker_processes * by_descriptors, "file descriptors"]
''',
        '''def worker_capacity(worker_processes, worker_connections, nofile_limit, proxying):
    per_client = 2 if proxying else 1
    return [worker_processes * worker_connections // per_client, "worker_connections"]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Workers, connections, keepalive and OS tuning*. Integer division.",
        intuition="Capacity is set by whichever resource runs out first. A worker has a budget of connection slots and a separate budget of file descriptors; every client spends from both. Raising one budget far beyond the other changes nothing.",
        hints=[
            "Compute two per-worker figures, one for each budget, then take the smaller.",
            "Proxying doubles the connections a client uses but not the descriptors in this model.",
            "Multiply by the number of workers at the end, after the integer division.",
        ],
        brute_force="Not applicable; this is arithmetic. The common shortcut `worker_processes * worker_connections` ignores both the halving for proxied traffic and the descriptor limit.",
        approach="1. `by_connections = worker_connections // (2 if proxying else 1)`.\n2. `by_descriptors = nofile_limit // 2`.\n3. Compare; ties go to `worker_connections`.\n4. Multiply by `worker_processes`.\n\nDry run: 4 workers, 8,192 connections, descriptor limit 1,024, proxying. By connections: 4,096 per worker. By descriptors: 512 per worker. The smaller is 512 → 2,048 clients, limited by file descriptors.",
        complexity="Time and space O(1).",
        pitfalls="Forgetting the halving; multiplying before dividing, which gives a different result for odd values; believing a larger `worker_connections` alone raises capacity.",
        follow_up="Include idle keep-alive connections: given a number of idle clients that hold one connection and one descriptor each, how many active proxied requests still fit?",
    ),
),
dict(
    id="nginx-gzip-decision",
    title="Will NGINX gzip This Response?",
    difficulty="Medium",
    pattern="Performance",
    entry="gzip_decision",
    description=r"""
Decide whether the gzip module compresses a response. `gzip_decision(config, request, response)` returns `True` or
`False`.

`config` has the keys `enabled` (bool), `min_length` (int), `types` (list of MIME types), `proxied` (`"off"` or
`"any"`) and `http_version` (`"1.0"` or `"1.1"`).
`request` has `accept_encoding` (the header text, possibly empty), `http_version` (`"1.0"`, `"1.1"`, `"2.0"` or
`"3.0"`) and `via` (the `Via` header, empty when absent).
`response` has `status` (int), `content_type` (text, possibly with parameters such as `; charset=utf-8`),
`content_length` (int, or `None` when unknown) and `content_encoding` (text, empty when absent).

The response is compressed only if **all** of these hold:

1. `enabled` is true.
2. The status is 200, 403 or 404.
3. The response has no `content_encoding` yet.
4. The request's HTTP version is at least the configured `http_version`.
5. `accept_encoding` lists `gzip`: split it on commas; one of the items, ignoring case and spaces, must be `gzip` or
   `gzip;q=VALUE` with a VALUE greater than 0.
6. If the request has a `Via` header (it came through a proxy), `proxied` must be `"any"`.
7. The content type, taken before any `;`, trimmed and lower-cased, is `text/html` (always eligible), or appears in
   `types`, or `types` contains `"*"`.
8. `content_length` is unknown, or at least `min_length`.

**Example:** a 5,000-byte `application/json` response with status 200, `types` containing `application/json`,
`Accept-Encoding: gzip, deflate, br` → `True`. The same response to a request with `Via: 1.1 cdn` and `proxied` set to
`"off"` → `False`.
""",
    starter='''def gzip_decision(config, request, response):
    # return True if the response is gzipped
    pass
''',
    solution='''def gzip_decision(config, request, response):
    if not config["enabled"]:
        return False
    if response["status"] not in (200, 403, 404):
        return False
    if response["content_encoding"]:
        return False
    if float(request["http_version"]) < float(config["http_version"]):
        return False
    accepted = False
    for item in request["accept_encoding"].split(","):
        name, _, params = item.strip().lower().partition(";")
        if name.strip() != "gzip":
            continue
        params = params.replace(" ", "")
        if params.startswith("q="):
            try:
                accepted = float(params[2:]) > 0
            except ValueError:
                accepted = False
        else:
            accepted = True
    if not accepted:
        return False
    if request["via"] and config["proxied"] != "any":
        return False
    ctype = response["content_type"].split(";")[0].strip().lower()
    types = [t.lower() for t in config["types"]]
    if ctype != "text/html" and ctype not in types and "*" not in types:
        return False
    length = response["content_length"]
    if length is not None and length < config["min_length"]:
        return False
    return True
''',
    tests=[
        [_GZ, _REQ, _RES],
        [_GZ, dict(_REQ, via="1.1 cdn"), _RES],
        [dict(_GZ, proxied="any"), dict(_REQ, via="1.1 cdn"), _RES],
        [dict(_GZ, enabled=False), _REQ, _RES],
        [_GZ, _REQ, dict(_RES, content_type="text/html; charset=utf-8")],
        [_GZ, _REQ, dict(_RES, content_type="image/png")],
        [dict(_GZ, types=["*"]), _REQ, dict(_RES, content_type="image/png")],
        [_GZ, _REQ, dict(_RES, content_length=1023)],
        [_GZ, _REQ, dict(_RES, content_length=1024)],
        [_GZ, _REQ, dict(_RES, status=500)],
        [_GZ, _REQ, dict(_RES, content_encoding="br")],
        [_GZ, dict(_REQ, accept_encoding="br, GZIP ; q=0.5"), _RES],
        [_GZ, dict(_REQ, accept_encoding="gzip;q=0, br"), _RES],
        [_GZ, dict(_REQ, http_version="1.0"), _RES],
        [_GZ, dict(_REQ, http_version="2.0", accept_encoding="x-gzip, identity"), _RES],
    ],
    examples=2,
    wrong_solutions=[
        '''def gzip_decision(config, request, response):
    if not config["enabled"] or response["status"] not in (200, 403, 404) or response["content_encoding"]:
        return False
    if float(request["http_version"]) < float(config["http_version"]):
        return False
    if "gzip" not in request["accept_encoding"].lower():
        return False
    if request["via"] and config["proxied"] != "any":
        return False
    ctype = response["content_type"].split(";")[0].strip().lower()
    types = [t.lower() for t in config["types"]]
    if ctype != "text/html" and ctype not in types and "*" not in types:
        return False
    length = response["content_length"]
    return length is None or length >= config["min_length"]
''',
        '''def gzip_decision(config, request, response):
    if not config["enabled"] or response["content_encoding"]:
        return False
    items = [i.strip().lower().split(";")[0].strip() for i in request["accept_encoding"].split(",")]
    if "gzip" not in items:
        return False
    ctype = response["content_type"].split(";")[0].strip().lower()
    if ctype not in [t.lower() for t in config["types"]]:
        return False
    length = response["content_length"]
    return length is None or length >= config["min_length"]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Buffering, sendfile, gzip, brotli and file caches*. String parsing.",
        intuition="Compression is a chain of gates, and a response must pass every one. Some gates concern the configuration, some the client's abilities, some the response itself. Most real \"why is this not compressed?\" questions are answered by finding the one gate that was shut: the type list, the `Via` header, or the length.",
        hints=[
            "Write one early `return False` per rule, in the order given. Do not try to combine them into a single expression.",
            "Parse `Accept-Encoding` properly: split on commas, then split each item at `;` to separate the name from `q=`.",
            "`text/html` is eligible even when `types` is empty, and the content type may carry a charset parameter.",
        ],
        brute_force="Check only `enabled`, a substring test for `gzip`, and the type list. It gives the right answer in the happy path and the wrong one in exactly the cases that confuse people in production: `gzip;q=0`, `x-gzip`, a request through a CDN, an error status.",
        approach="Translate the eight rules one by one.\n\nDry run: JSON response of 5,000 bytes, status 200, no encoding; request HTTP/1.1 with `gzip, deflate, br` and `Via: 1.1 cdn`; `proxied` is `off`. Rules 1 to 5 pass. Rule 6: there is a `Via` header and `proxied` is not `any` → `False`. This is the default behaviour that makes compression silently disappear behind a CDN.",
        complexity="Time O(length of the headers + number of types); space O(number of types).",
        pitfalls="A substring test that accepts `x-gzip` or `gzip;q=0`; forgetting that `text/html` is always included; comparing the content type with its charset still attached; treating an unknown length as too short; compressing 500 responses.",
        follow_up="Add the other `gzip_proxied` parameters (`expired`, `no-cache`, `no-store`, `private`, `auth`), which allow compression of proxied requests depending on the response's caching headers.",
    ),
),
]
