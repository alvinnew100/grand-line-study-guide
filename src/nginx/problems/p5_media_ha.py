_PAIR = [["A", 110, 30], ["B", 100, 30]]

PROBLEMS = [
dict(
    id="nginx-range-request",
    title="Answer a Range Request",
    difficulty="Medium",
    pattern="Media Streaming",
    entry="serve_range",
    description=r"""
Video players fetch files in pieces with the `Range` request header. Decide how NGINX answers for a static file of
`size` bytes.

`serve_range(header, size)` returns `[status, first, last]`, the status code and the first and last byte positions
sent (positions start at 0):

- `[200, 0, size - 1]`: the whole file.
- `[206, first, last]`: part of the file (Partial Content).
- `[416, -1, -1]`: Range Not Satisfiable.

Rules:

1. No header (`None` or empty), a header that does not start with `bytes=`, or a header listing several ranges
   (containing a comma) → the whole file with 200. (Real NGINX can answer several ranges at once; this problem covers
   a single range.)
2. Otherwise the text after `bytes=` must be `A-B`, `A-` or `-N`, where A, B and N are non-negative integers written
   in digits. Anything else → 416.
3. `A-B`: bytes A to B. `A-`: from A to the end. If `A >= size` or `A > B` → 416. If B is past the end, it is
   reduced to the last byte.
4. `-N`: the final N bytes (the whole file if N is larger than the file). `N = 0`, or an empty file → 416.

**Example:** `"bytes=0-999"`, `10000` → `[206, 0, 999]`

**Example:** `"bytes=-200"`, `10000` → `[206, 9800, 9999]`
""",
    starter='''def serve_range(header, size):
    # return [status, first, last]
    pass
''',
    solution='''def serve_range(header, size):
    whole = [200, 0, size - 1]
    if not header or not header.startswith("bytes="):
        return whole
    spec = header[6:].strip()
    if "," in spec:
        return whole
    first, dash, last = spec.partition("-")
    first, last = first.strip(), last.strip()
    bad = [416, -1, -1]
    if not dash or (first and not first.isdigit()) or (last and not last.isdigit()) or (not first and not last):
        return bad
    if first == "":
        n = int(last)
        if n == 0 or size == 0:
            return bad
        return [206, max(0, size - n), size - 1]
    start = int(first)
    end = int(last) if last else size - 1
    if start >= size or start > end:
        return bad
    return [206, start, min(end, size - 1)]
''',
    tests=[
        ["bytes=0-999", 10000],
        ["bytes=-200", 10000],
        [None, 10000],
        ["bytes=9500-", 10000],
        ["bytes=9000-20000", 10000],
        ["bytes=10000-", 10000],
        ["bytes=500-100", 10000],
        ["bytes=-0", 10000],
        ["bytes=-50000", 10000],
        ["bytes=0-0", 1],
        ["items=0-5", 10000],
        ["bytes=0-10,20-30", 10000],
        ["bytes=abc-def", 10000],
        ["bytes=-", 10000],
        ["bytes=0-", 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def serve_range(header, size):
    if not header or not header.startswith("bytes=") or "," in header:
        return [200, 0, size - 1]
    first, _, last = header[6:].partition("-")
    try:
        start = int(first) if first else 0
        end = int(last) if last else size - 1
    except ValueError:
        return [416, -1, -1]
    if start >= size or start > end:
        return [416, -1, -1]
    return [206, start, end]
''',
        '''def serve_range(header, size):
    whole = [200, 0, size - 1]
    if not header or not header.startswith("bytes="):
        return whole
    spec = header[6:].strip()
    first, dash, last = spec.partition("-")
    if not first.isdigit():
        return whole
    start = int(first)
    end = int(last) if last.isdigit() else size - 1
    if start >= size:
        return [416, -1, -1]
    return [206, start, min(end, size - 1)]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Media streaming: MP4, HLS and bandwidth control*. `str.partition` and `str.isdigit`.",
        intuition="A range is a polite request for a slice of a file. There are three spellings: both ends, only the start, or \"the last N bytes\". The server either sends the slice trimmed to the file, sends everything because it was not really asked for a slice, or says the slice does not exist.",
        hints=[
            "Decide first whether the header is a usable single byte range; if not, answer 200 with the whole file.",
            "`partition(\"-\")` gives the two sides. An empty left side means a suffix range.",
            "Trim an end that is past the file, but reject a start that is.",
        ],
        brute_force="Not applicable; the work is constant-time parsing. A common shortcut treats `-N` as `0-N`, which returns the first bytes instead of the last and breaks every player that reads an index stored at the end of a file.",
        approach="1. Unusable header → `[200, 0, size-1]`.\n2. Validate the two sides as digits.\n3. Suffix form: `[206, max(0, size-N), size-1]`, or 416 for N = 0 or an empty file.\n4. Otherwise compute start and end, reject `start >= size` or `start > end`, clamp the end.\n\nDry run: `bytes=9000-20000` with size 10000. Start 9000 is inside the file; end 20000 is clamped to 9999 → `[206, 9000, 9999]`.",
        complexity="Time O(length of the header); space O(1).",
        pitfalls="Returning the first N bytes for `-N`; not clamping the end; answering 416 for a unit other than bytes instead of ignoring the header; accepting negative or non-numeric positions; forgetting the empty file.",
        follow_up="Produce the `Content-Range` header (`bytes first-last/size`, or `bytes */size` with 416), and support several ranges with a `multipart/byteranges` response.",
    ),
),
dict(
    id="nginx-vrrp-master",
    title="Who Holds the Virtual IP?",
    difficulty="Medium",
    pattern="High Availability",
    entry="vrrp_holder",
    description=r"""
Two or more NGINX machines share one virtual IP address with keepalived. Simulate which machine holds the address as
things fail and recover.

`vrrp_holder(nodes, events)`:

- `nodes` is a list of `[name, priority, penalty]`. `penalty` is how much a failing health script lowers the
  priority (the absolute value of keepalived's negative `weight`).
- `events` is a list of `[name, what]` in time order, where `what` is one of `"nginx_down"`, `"nginx_up"`,
  `"power_off"`, `"power_on"`.

At the start every machine is powered on with NGINX healthy. A machine that is powered off cannot hold the address.
A powered-on machine's **effective priority** is `priority`, minus `penalty` while its NGINX is down. `power_on`
brings a machine back with its NGINX in whatever state it was last set to.

The holder is the powered-on machine with the highest effective priority. On a tie, the current holder keeps the
address if it is one of the tied machines; otherwise the tied machine whose name sorts first takes it. If no machine
is powered on, the holder is `""`.

Return a list with the holder at the start followed by the holder after each event.

**Example:** nodes `[["A", 110, 30], ["B", 100, 30]]`, events `[["A", "nginx_down"], ["A", "nginx_up"]]`
→ `["A", "B", "A"]`
""",
    starter='''def vrrp_holder(nodes, events):
    # return the holder at the start and after each event
    pass
''',
    solution='''def vrrp_holder(nodes, events):
    powered = {name: True for name, _, _ in nodes}
    healthy = {name: True for name, _, _ in nodes}
    holder = ""
    out = []

    def elect(current):
        alive = {name: prio - (0 if healthy[name] else penalty) for name, prio, penalty in nodes if powered[name]}
        if not alive:
            return ""
        best = max(alive.values())
        tied = sorted(name for name, value in alive.items() if value == best)
        return current if current in tied else tied[0]

    holder = elect(holder)
    out.append(holder)
    for name, what in events:
        if what == "nginx_down":
            healthy[name] = False
        elif what == "nginx_up":
            healthy[name] = True
        elif what == "power_off":
            powered[name] = False
        elif what == "power_on":
            powered[name] = True
        holder = elect(holder)
        out.append(holder)
    return out
''',
    tests=[
        [_PAIR, [["A", "nginx_down"], ["A", "nginx_up"]]],
        [_PAIR, [["A", "power_off"], ["A", "power_on"]]],
        [_PAIR, []],
        [_PAIR, [["B", "nginx_down"], ["B", "power_off"], ["A", "power_off"], ["B", "power_on"], ["A", "power_on"]]],
        [_PAIR, [["A", "nginx_down"], ["B", "nginx_down"], ["A", "nginx_up"], ["B", "nginx_up"]]],
        [[["A", 110, 5], ["B", 100, 5]], [["A", "nginx_down"], ["A", "power_off"]]],
        [[["A", 100, 30], ["B", 100, 30]], [["A", "nginx_down"], ["A", "nginx_up"], ["B", "nginx_down"], ["B", "nginx_up"]]],
        [[["B", 100, 30], ["A", 100, 30]], [["A", "power_off"], ["A", "power_on"]]],
        [[["A", 120, 50], ["B", 100, 50], ["C", 90, 50]], [["A", "nginx_down"], ["B", "nginx_down"], ["C", "power_off"], ["A", "nginx_up"]]],
        [[["A", 110, 10], ["B", 100, 10]], [["A", "nginx_down"], ["B", "power_off"], ["A", "power_off"], ["A", "nginx_up"], ["A", "power_on"]]],
        [[["only", 100, 30]], [["only", "nginx_down"], ["only", "power_off"], ["only", "power_on"]]],
        [[["A", 110, 30], ["B", 100, 30], ["C", 105, 30]], [[n, w] for n in "ABC" for w in ("nginx_down", "power_off", "power_on", "nginx_up")]],
    ],
    examples=1,
    wrong_solutions=[
        '''def vrrp_holder(nodes, events):
    powered = {name: True for name, _, _ in nodes}
    out = []

    def elect():
        alive = sorted((-prio, name) for name, prio, _ in nodes if powered[name])
        return alive[0][1] if alive else ""

    out.append(elect())
    for name, what in events:
        if what == "power_off":
            powered[name] = False
        elif what == "power_on":
            powered[name] = True
        out.append(elect())
    return out
''',
        '''def vrrp_holder(nodes, events):
    powered = {name: True for name, _, _ in nodes}
    healthy = {name: True for name, _, _ in nodes}
    out = []

    def elect():
        alive = sorted((-(prio - (0 if healthy[name] else penalty)), name) for name, prio, penalty in nodes if powered[name])
        return alive[0][1] if alive else ""

    out.append(elect())
    for name, what in events:
        if what in ("nginx_down", "nginx_up"):
            healthy[name] = what == "nginx_up"
        else:
            powered[name] = what == "power_on"
        out.append(elect())
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: *High-availability deployment modes*. Dictionaries and `max`.",
        intuition="VRRP is a continuous election in which the candidate with the highest number wins. A health script is a way of lowering your own number when you are not fit to serve, so that a healthier neighbour outranks you. The address follows the winner.",
        hints=[
            "Keep two flags per machine: powered on, and NGINX healthy. They change independently.",
            "Recompute the effective priorities and run the election after every event.",
            "A tie does not move the address away from a current holder that is still among the best.",
        ],
        brute_force="Tracking only power and ignoring the health script matches plain VRRP without `track_script`, and shows why that is not enough: the machine with a crashed NGINX would keep the address.",
        approach="1. Initialise both flags to true for every node.\n2. Write `elect(current)`: collect effective priorities of powered-on nodes; empty → `\"\"`; find the maximum; keep the current holder if tied, else the first name.\n3. Record the initial holder, then apply each event and re-elect.\n\nDry run of the example: A (110) holds. NGINX on A fails: A drops to 80, B's 100 wins. NGINX on A recovers: A is 110 again and takes the address back, which is preemption.",
        complexity="Time O(events × nodes); space O(nodes).",
        pitfalls="Ignoring the penalty; letting a powered-off machine win; a penalty too small to change the order (110 - 5 is still above 100), which is a real misconfiguration the sixth test demonstrates; moving the address on a tie.",
        follow_up="Add keepalived's `nopreempt`: a recovered higher-priority machine does not take the address back from a healthy holder.",
    ),
),
]
