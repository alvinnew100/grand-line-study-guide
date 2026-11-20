"""System design problems 3: crawler, notifications, feed, chat, autocomplete, video and file sync."""


def _ops(cls, ctor_args, calls):
    return [[cls] + [c[0] for c in calls], [list(ctor_args)] + [list(c[1]) for c in calls]]


_LADDER = [[240, 400], [360, 800], [480, 1400], [720, 2800], [1080, 5000], [2160, 16000]]

PROBLEMS = [
dict(
    id="sd-crawler-frontier",
    title="URL Frontier with Per-Host Politeness",
    difficulty="Hard",
    pattern="Web Crawler",
    kind="class",
    entry="Frontier",
    description=r"""
A crawler's frontier decides which URL to fetch next without hitting any one host too often.

The **host** of a URL is the text after `"://"` up to the next `"/"` (or the end of the string): the host of `https://a.com/x/y` is `a.com`.

`Frontier(delay)`: after a URL of a host is handed out at time `t`, no other URL of that host may be handed out before time `t + delay`.

- `add(url)` → `True` and queue the URL if this exact URL has never been added before; otherwise `False`.
- `next(now)` → among hosts that have queued URLs and are ready (`ready_time <= now`; a host that has never been fetched is ready), choose the host whose **oldest queued URL was added earliest**, remove and return that URL, and set the host's `ready_time` to `now + delay`. Return `None` if no host is ready or nothing is queued.
- `next_ready_time()` → the earliest time at which `next` could return a URL: the minimum `ready_time` over hosts with queued URLs (0 for a host never fetched), or `-1` if nothing is queued.
- `pending()` → the number of queued URLs.

`now` never decreases.

**Example:** `Frontier(10)`; add `https://a.com/1`, `https://a.com/2`, `https://b.com/1`. `next(0)` → `https://a.com/1`; `next(0)` → `https://b.com/1` (a.com must wait); `next(5)` → `None`; `next_ready_time()` → 10; `next(10)` → `https://a.com/2`.
""",
    starter='''class Frontier:
    def __init__(self, delay: int):
        pass

    def add(self, url: str) -> bool:
        pass

    def next(self, now: int):
        pass

    def next_ready_time(self) -> int:
        pass

    def pending(self) -> int:
        pass
''',
    solution='''from collections import deque

class Frontier:
    def __init__(self, delay):
        self.delay = delay
        self.seen = set()
        self.queues = {}            # host -> deque of (order, url)
        self.ready = {}             # host -> earliest time it may be fetched again
        self.counter = 0
        self.size = 0

    @staticmethod
    def _host(url):
        rest = url.split("://", 1)[1] if "://" in url else url
        return rest.split("/", 1)[0]

    def add(self, url):
        if url in self.seen:
            return False
        self.seen.add(url)
        self.queues.setdefault(self._host(url), deque()).append((self.counter, url))
        self.counter += 1
        self.size += 1
        return True

    def next(self, now):
        best = None
        for host, q in self.queues.items():
            if q and self.ready.get(host, 0) <= now:
                if best is None or q[0][0] < self.queues[best][0][0]:
                    best = host
        if best is None:
            return None
        _, url = self.queues[best].popleft()
        self.ready[best] = now + self.delay
        self.size -= 1
        return url

    def next_ready_time(self):
        times = [self.ready.get(h, 0) for h, q in self.queues.items() if q]
        return min(times) if times else -1

    def pending(self):
        return self.size
''',
    tests=[
        _ops("Frontier", [10], [("add", ["https://a.com/1"]), ("add", ["https://a.com/2"]), ("add", ["https://b.com/1"]), ("next", [0]), ("next", [0]), ("next", [5]), ("next_ready_time", []), ("next", [10]), ("pending", [])]),
        _ops("Frontier", [5], [("next", [0]), ("next_ready_time", []), ("pending", [])]),
        _ops("Frontier", [5], [("add", ["http://x.org/a"]), ("add", ["http://x.org/a"]), ("pending", []), ("next", [0]), ("add", ["http://x.org/a"]), ("next", [100])]),
        _ops("Frontier", [3], [("add", [f"https://h{i % 3}.com/p{i}"]) for i in range(9)] + [("next", [t]) for t in (0, 0, 0, 0, 2, 3, 3, 3, 3, 6, 6, 6, 6)] + [("pending", [])]),
        _ops("Frontier", [0], [("add", [f"https://same.com/{i}"]) for i in range(5)] + [("next", [0])] * 6),
        _ops("Frontier", [7], [("add", ["https://a.com"]), ("add", ["https://a.com/"]), ("add", ["https://b.com"]), ("next", [1]), ("next", [1]), ("next", [1]), ("next_ready_time", []), ("next", [7]), ("next", [8])]),
        _ops("Frontier", [10], [("add", ["https://b.com/1"]), ("add", ["https://a.com/1"]), ("add", ["https://a.com/2"]), ("add", ["https://b.com/2"]), ("next", [0]), ("next", [0]), ("next", [10]), ("next", [10])]),
        _ops("Frontier", [10], [("add", ["https://a.com/1"]), ("next", [3]), ("add", ["https://a.com/2"]), ("add", ["https://c.com/1"]), ("next_ready_time", []), ("next", [4]), ("next_ready_time", []), ("next", [12]), ("next", [13]), ("next_ready_time", [])]),
        _ops("Frontier", [4], [("add", ["https://a.com/1"]), ("add", ["https://b.com/1"]), ("next", [0]), ("add", ["https://a.com/2"]), ("next", [1]), ("add", ["https://b.com/2"]), ("next", [4]), ("next", [4]), ("next", [5]), ("pending", [])]),
        _ops("Frontier", [2], [("add", [f"https://site{i % 4}.net/page/{i}"]) for i in range(20)] + [("next", [t // 3]) for t in range(40)] + [("pending", [])]),
        _ops("Frontier", [100], [("add", ["ftp://files.example/a"]), ("add", ["https://files.example/a"]), ("next", [0]), ("next", [50]), ("next_ready_time", []), ("next", [100])]),
    ],
    examples=1,
    wrong_solutions=[
        '''from collections import deque
class Frontier:
    def __init__(self, delay):
        self.q, self.seen = deque(), set()
    def add(self, url):
        if url in self.seen:
            return False
        self.seen.add(url); self.q.append(url); return True
    def next(self, now):
        return self.q.popleft() if self.q else None
    def next_ready_time(self):
        return 0 if self.q else -1
    def pending(self):
        return len(self.q)
''',
        '''from collections import deque
class Frontier:
    def __init__(self, delay):
        self.delay, self.seen, self.queues, self.ready, self.c, self.size = delay, set(), {}, {}, 0, 0
    def _host(self, url):
        rest = url.split("://", 1)[1] if "://" in url else url
        return rest.split("/", 1)[0]
    def add(self, url):
        if url in self.seen:
            return False
        self.seen.add(url); self.queues.setdefault(self._host(url), deque()).append((self.c, url))
        self.c += 1; self.size += 1; return True
    def next(self, now):
        for host, q in self.queues.items():
            if q and self.ready.get(host, 0) <= now:
                self.ready[host] = now + self.delay
                self.size -= 1
                return q.popleft()[1]
        return None
    def next_ready_time(self):
        t = [self.ready.get(h, 0) for h, q in self.queues.items() if q]
        return min(t) if t else -1
    def pending(self):
        return self.size
''',
        '''from collections import deque
class Frontier:
    def __init__(self, delay):
        self.delay, self.seen, self.queues, self.ready, self.c, self.size = delay, set(), {}, {}, 0, 0
    def _host(self, url):
        rest = url.split("://", 1)[1] if "://" in url else url
        return rest.split("/", 1)[0]
    def add(self, url):
        if url in self.seen:
            return False
        self.seen.add(url); self.queues.setdefault(self._host(url), deque()).append((self.c, url))
        self.c += 1; self.size += 1; return True
    def next(self, now):
        best = None
        for host, q in self.queues.items():
            if q and self.ready.get(host, 0) < now:
                if best is None or q[0][0] < self.queues[best][0][0]:
                    best = host
        if best is None:
            return None
        self.ready[best] = now + self.delay; self.size -= 1
        return self.queues[best].popleft()[1]
    def next_ready_time(self):
        t = [self.ready.get(h, 0) for h, q in self.queues.items() if q]
        return min(t) if t else -1
    def pending(self):
        return self.size
''',
        '''from collections import deque
class Frontier:
    def __init__(self, delay):
        self.delay, self.queues, self.ready, self.c, self.size = delay, {}, {}, 0, 0
    def _host(self, url):
        rest = url.split("://", 1)[1] if "://" in url else url
        return rest.split("/", 1)[0]
    def add(self, url):
        q = self.queues.setdefault(self._host(url), deque())
        if any(u == url for _, u in q):
            return False
        q.append((self.c, url)); self.c += 1; self.size += 1; return True
    def next(self, now):
        best = None
        for host, q in self.queues.items():
            if q and self.ready.get(host, 0) <= now:
                if best is None or q[0][0] < self.queues[best][0][0]:
                    best = host
        if best is None:
            return None
        self.ready[best] = now + self.delay; self.size -= 1
        return self.queues[best].popleft()[1]
    def next_ready_time(self):
        t = [self.ready.get(h, 0) for h, q in self.queues.items() if q]
        return min(t) if t else -1
    def pending(self):
        return self.size
''',
    ],
    guide=dict(
        prereqs="Both web crawler lessons: the frontier, politeness, one queue per host. `collections.deque`.",
        intuition="One big queue cannot be polite, because consecutive entries share a host. Give every host its own queue and a 'not before' time. Picking the next URL means choosing among the hosts that are allowed to be fetched right now.",
        hints=[
            "Keep a `seen` set for all URLs ever added, separate from the queues, so a URL already fetched is still rejected.",
            "Stamp each URL with an increasing counter when it is added; a host's priority is the stamp at the front of its queue.",
            "In `next`, skip hosts whose `ready_time > now`; among the rest take the smallest front stamp, pop it, and set `ready_time = now + delay`.",
        ],
        brute_force="One list of all URLs; on each `next`, scan from the oldest for the first URL whose host is ready. Correct, but O(total URLs) per call. Per-host queues make it O(hosts), and a heap keyed by ready time makes it O(log hosts).",
        approach="""State: `seen`, `queues[host]` (deque of `(stamp, url)`), `ready[host]`, a counter and a size.

1. `add`: reject if seen; otherwise stamp and append to the host's queue.
2. `next(now)`: among hosts with a non-empty queue and `ready <= now`, choose the minimum front stamp; pop; set `ready`.
3. `next_ready_time`: minimum `ready` over hosts with queued URLs (default 0).

**Dry run**, delay 10: queues a.com: [1, 2], b.com: [1]. `next(0)`: both ready; a.com's front is older → `a.com/1`, a.com ready at 10. `next(0)`: only b.com is ready → `b.com/1`. `next(5)`: a.com not ready, b.com empty → None. `next_ready_time()` → 10. `next(10)` → `a.com/2`.""",
        complexity="`add` O(1). `next` O(H) for H hosts with this scan (O(log H) with heaps). Space O(total URLs ever added) for the seen set.",
        pitfalls="Deduplicating only against queued URLs, so a fetched URL can be re-added; using `<` instead of `<=` for readiness; choosing the first ready host in dictionary order instead of the one with the oldest URL; parsing the host incorrectly when the URL has no path.",
        follow_up="Replace the scan with two heaps (ready hosts by front stamp, waiting hosts by ready time). Add per-host delays taken from robots.txt, and priorities.",
    ),
),
dict(
    id="sd-bloom-filter",
    title="Bloom Filter for Duplicate URL Detection",
    difficulty="Medium",
    pattern="Web Crawler",
    kind="class",
    entry="BloomFilter",
    description=r"""
A Bloom filter answers "have I possibly seen this before?" in a fixed amount of memory. It can give false positives and never false negatives.

`BloomFilter(m, k)` has `m` bits, all 0 at first, and `k` hash functions. Hash function number `i` (for `i = 0 .. k-1`) maps an item to bit

`int(hashlib.md5((str(i) + ":" + item).encode()).hexdigest(), 16) % m`

- `add(item)` → set the item's `k` bits. Return `True` if at least one of them was 0 before (the item was definitely new), `False` if all were already 1 (the item was possibly seen before).
- `might_contain(item)` → `True` if all `k` bits are 1.
- `bits_set()` → how many of the `m` bits are 1.
- `estimated_fp_rate()` → the chance that a random new item would be reported as present: `(bits_set / m) ** k`, rounded to 6 decimal places.

**Example:** `BloomFilter(64, 3)`: `add("a")` → True, `add("a")` → False, `might_contain("a")` → True, `bits_set()` is at most 3.
""",
    starter='''import hashlib

class BloomFilter:
    def __init__(self, m: int, k: int):
        pass

    def add(self, item: str) -> bool:
        pass

    def might_contain(self, item: str) -> bool:
        pass

    def bits_set(self) -> int:
        pass

    def estimated_fp_rate(self) -> float:
        pass
''',
    solution='''import hashlib

class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k = m, k
        self.bits = [0] * m
        self.count = 0

    def _positions(self, item):
        return [int(hashlib.md5((str(i) + ":" + item).encode()).hexdigest(), 16) % self.m
                for i in range(self.k)]

    def add(self, item):
        new = False
        for p in self._positions(item):
            if not self.bits[p]:
                self.bits[p] = 1
                self.count += 1
                new = True
        return new

    def might_contain(self, item):
        return all(self.bits[p] for p in self._positions(item))

    def bits_set(self):
        return self.count

    def estimated_fp_rate(self):
        return round((self.count / self.m) ** self.k, 6)
''',
    tests=[
        _ops("BloomFilter", [64, 3], [("add", ["a"]), ("add", ["a"]), ("might_contain", ["a"]), ("might_contain", ["b"]), ("bits_set", []), ("estimated_fp_rate", [])]),
        _ops("BloomFilter", [1, 1], [("might_contain", ["x"]), ("add", ["x"]), ("might_contain", ["y"]), ("add", ["y"]), ("bits_set", []), ("estimated_fp_rate", [])]),
        _ops("BloomFilter", [16, 2], [("add", [f"u{i}"]) for i in range(30)] + [("bits_set", []), ("estimated_fp_rate", [])]),
        _ops("BloomFilter", [16, 2], [("add", [f"u{i}"]) for i in range(8)] + [("might_contain", [f"v{i}"]) for i in range(20)]),
        _ops("BloomFilter", [1024, 4], [("add", [f"https://a.com/{i}"]) for i in range(50)] + [("might_contain", [f"https://a.com/{i}"]) for i in range(45, 60)] + [("bits_set", []), ("estimated_fp_rate", [])]),
        _ops("BloomFilter", [8, 8], [("add", ["one"]), ("bits_set", []), ("add", ["two"]), ("bits_set", []), ("add", ["three"]), ("bits_set", []), ("estimated_fp_rate", [])]),
        _ops("BloomFilter", [100, 1], [("add", [str(i)]) for i in range(40)] + [("bits_set", []), ("estimated_fp_rate", [])]),
        _ops("BloomFilter", [32, 5], [("might_contain", [""]), ("add", [""]), ("add", [""]), ("might_contain", [""]), ("bits_set", [])]),
        _ops("BloomFilter", [50, 3], [("bits_set", []), ("estimated_fp_rate", []), ("might_contain", ["anything"])]),
        _ops("BloomFilter", [12, 3], [("add", [f"k{i}"]) for i in range(12)] + [("might_contain", [f"z{i}"]) for i in range(12)] + [("bits_set", [])]),
        _ops("BloomFilter", [2048, 7], [("add", [f"page-{i}"]) for i in range(100)] + [("add", [f"page-{i}"]) for i in range(95, 105)] + [("bits_set", []), ("estimated_fp_rate", [])]),
    ],
    examples=1,
    wrong_solutions=[
        '''import hashlib
class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k, self.items = m, k, set()
    def add(self, item):
        new = item not in self.items
        self.items.add(item)
        return new
    def might_contain(self, item):
        return item in self.items
    def bits_set(self):
        return len(self.items) * self.k
    def estimated_fp_rate(self):
        return round((self.bits_set() / self.m) ** self.k, 6)
''',
        '''import hashlib
class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k, self.bits = m, k, [0] * m
    def _p(self, item):
        return [int(hashlib.md5((str(i) + ":" + item).encode()).hexdigest(), 16) % self.m for i in range(self.k)]
    def add(self, item):
        new = False
        for p in self._p(item):
            if not self.bits[p]:
                self.bits[p] = 1
                new = True
        return new
    def might_contain(self, item):
        return any(self.bits[p] for p in self._p(item))
    def bits_set(self):
        return sum(self.bits)
    def estimated_fp_rate(self):
        return round((sum(self.bits) / self.m) ** self.k, 6)
''',
        '''import hashlib
class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k, self.bits = m, k, [0] * m
    def _p(self, item):
        return [int(hashlib.md5((item + ":" + str(i)).encode()).hexdigest(), 16) % self.m for i in range(self.k)]
    def add(self, item):
        new = False
        for p in self._p(item):
            if not self.bits[p]:
                self.bits[p] = 1
                new = True
        return new
    def might_contain(self, item):
        return all(self.bits[p] for p in self._p(item))
    def bits_set(self):
        return sum(self.bits)
    def estimated_fp_rate(self):
        return round((sum(self.bits) / self.m) ** self.k, 6)
''',
        '''import hashlib
class BloomFilter:
    def __init__(self, m, k):
        self.m, self.k, self.bits = m, k, [0] * m
    def _p(self, item):
        return [int(hashlib.md5((str(i) + ":" + item).encode()).hexdigest(), 16) % self.m for i in range(self.k)]
    def add(self, item):
        was = all(self.bits[p] for p in self._p(item))
        for p in self._p(item):
            self.bits[p] = 1
        return not was
    def might_contain(self, item):
        return all(self.bits[p] for p in self._p(item))
    def bits_set(self):
        return sum(self.bits)
    def estimated_fp_rate(self):
        return round(sum(self.bits) / self.m * self.k, 6)
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a web crawler II' (URL seen test) and 'Design a key-value store II' (Bloom filters on SSTables).",
        intuition="Each item switches on k lights in a row of m. To ask about an item, look at its k lights: if any is off, the item was never added. If all are on, it was probably added, or other items happened to switch those lights on.",
        hints=[
            "Write `_positions(item)` returning the k bit indexes, exactly as the formula says.",
            "`add` returns whether any bit changed from 0 to 1.",
            "`might_contain` needs ALL k bits set, not any.",
        ],
        brute_force="A plain set of every item is exact, and its memory grows with the number and length of the items: tens of terabytes for sixty billion URLs. The Bloom filter uses a fixed number of bits per item regardless of item length.",
        approach="""1. Bits as a list of m zeros; keep a running count of set bits.
2. `add`: for each position, if the bit is 0 set it, bump the count and remember that something changed.
3. `might_contain`: `all(...)` over the positions.
4. `estimated_fp_rate`: `(count / m) ** k`.

**Dry run**, m = 8, k = 2: `add("x")` sets bits 3 and 5 → True. `add("y")` sets 5 (already 1) and 6 → True. `might_contain("z")` where z maps to 3 and 6 → True, although z was never added: a false positive. `add("z")` → False.""",
        complexity="O(k) hashes per operation; O(m) bits of space, independent of the number of items.",
        pitfalls="Using `any` instead of `all`; counting bits as `items * k` (bits overlap); swapping the order of index and item in the hash input; believing a positive answer without confirming against the real store.",
        follow_up="For n items and a target false-positive rate p, the best sizes are m = -n ln p / (ln 2)^2 and k = (m/n) ln 2. Compute m for 1 billion URLs at 1%.",
    ),
),
dict(
    id="sd-notification-dedup-retry",
    title="Notification Deduplication and Retry Scheduling",
    difficulty="Medium",
    pattern="Notification System",
    kind="class",
    entry="Notifier",
    description=r"""
A notification worker must not send the same event twice and must retry failed sends with exponential backoff.

`Notifier(dedup_window, max_attempts, base_delay)`:

- `submit(event_id, ts)` → `"duplicate"` if this `event_id` was accepted before and `ts - accepted_ts < dedup_window`. Otherwise accept it: remember `accepted_ts = ts`, set its attempt count to 0 and its status to `"queued"`, and return `"queued"`.
- `record_failure(event_id, ts)` → a delivery attempt failed at time `ts`. Add 1 to the attempt count. If the count has reached `max_attempts`, set the status to `"dead"` (it goes to the dead-letter queue) and return `-1`. Otherwise set the status to `"retrying"` and return the time of the next attempt: `ts + base_delay * 2 ** (attempts - 1)`.
- `record_success(event_id)` → a delivery attempt succeeded. Add 1 to the attempt count, set the status to `"sent"` and return the total number of attempts.
- `status(event_id)` → `"queued"`, `"retrying"`, `"sent"`, `"dead"`, or `"unknown"` for an id never accepted.

`record_failure` and `record_success` are only called for events whose status is `"queued"` or `"retrying"`.

**Example:** `Notifier(60, 3, 10)`: `submit("e1", 0)` → `"queued"`; `submit("e1", 30)` → `"duplicate"`; `record_failure("e1", 31)` → 41; `record_failure("e1", 41)` → 61; `record_failure("e1", 61)` → -1; `status("e1")` → `"dead"`; `submit("e1", 60)` → `"queued"`.
""",
    starter='''class Notifier:
    def __init__(self, dedup_window: int, max_attempts: int, base_delay: int):
        pass

    def submit(self, event_id: str, ts: int) -> str:
        pass

    def record_failure(self, event_id: str, ts: int) -> int:
        pass

    def record_success(self, event_id: str) -> int:
        pass

    def status(self, event_id: str) -> str:
        pass
''',
    solution='''class Notifier:
    def __init__(self, dedup_window, max_attempts, base_delay):
        self.window, self.max_attempts, self.base = dedup_window, max_attempts, base_delay
        self.events = {}                # id -> [accepted_ts, attempts, status]

    def submit(self, event_id, ts):
        e = self.events.get(event_id)
        if e is not None and ts - e[0] < self.window:
            return "duplicate"
        self.events[event_id] = [ts, 0, "queued"]
        return "queued"

    def record_failure(self, event_id, ts):
        e = self.events[event_id]
        e[1] += 1
        if e[1] >= self.max_attempts:
            e[2] = "dead"
            return -1
        e[2] = "retrying"
        return ts + self.base * 2 ** (e[1] - 1)

    def record_success(self, event_id):
        e = self.events[event_id]
        e[1] += 1
        e[2] = "sent"
        return e[1]

    def status(self, event_id):
        e = self.events.get(event_id)
        return e[2] if e else "unknown"
''',
    tests=[
        _ops("Notifier", [60, 3, 10], [("submit", ["e1", 0]), ("submit", ["e1", 30]), ("record_failure", ["e1", 31]), ("record_failure", ["e1", 41]), ("record_failure", ["e1", 61]), ("status", ["e1"]), ("submit", ["e1", 60])]),
        _ops("Notifier", [10, 5, 1], [("status", ["x"]), ("submit", ["x", 5]), ("status", ["x"]), ("record_success", ["x"]), ("status", ["x"]), ("submit", ["x", 14]), ("submit", ["x", 15]), ("status", ["x"])]),
        _ops("Notifier", [100, 6, 2], [("submit", ["a", 0])] + [("record_failure", ["a", t]) for t in (0, 2, 6, 14, 30)] + [("status", ["a"]), ("record_success", ["a"]), ("status", ["a"])]),
        _ops("Notifier", [100, 1, 5], [("submit", ["a", 0]), ("record_failure", ["a", 1]), ("status", ["a"]), ("submit", ["a", 50]), ("submit", ["a", 100])]),
        _ops("Notifier", [0, 3, 5], [("submit", ["a", 0]), ("submit", ["a", 0]), ("submit", ["a", 1])]),
        _ops("Notifier", [30, 4, 3], [("submit", [f"e{i % 3}", i * 7]) for i in range(15)]),
        _ops("Notifier", [50, 4, 10], [("submit", ["a", 0]), ("record_failure", ["a", 100]), ("status", ["a"]), ("record_failure", ["a", 200]), ("record_success", ["a"]), ("submit", ["a", 49]), ("submit", ["a", 50]), ("status", ["a"]), ("record_success", ["a"])]),
        _ops("Notifier", [10, 3, 4], [("submit", ["a", 0]), ("submit", ["b", 0]), ("record_failure", ["a", 1]), ("record_success", ["b"]), ("status", ["a"]), ("status", ["b"]), ("record_failure", ["a", 5]), ("record_failure", ["a", 13]), ("status", ["a"])]),
        _ops("Notifier", [5, 10, 1], [("submit", ["z", 0])] + [("record_failure", ["z", t]) for t in range(0, 9)] + [("record_failure", ["z", 9]), ("status", ["z"])]),
        _ops("Notifier", [20, 2, 100], [("submit", ["a", 10]), ("submit", ["a", 29]), ("submit", ["a", 30]), ("submit", ["a", 49]), ("submit", ["a", 50]), ("record_failure", ["a", 60]), ("record_failure", ["a", 160]), ("status", ["a"])]),
        _ops("Notifier", [1000, 3, 7], [("submit", ["p", 3]), ("record_failure", ["p", 3]), ("record_success", ["p"]), ("submit", ["p", 500]), ("status", ["p"]), ("status", ["q"])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class Notifier:
    def __init__(self, w, m, b):
        self.w, self.m, self.b, self.e = w, m, b, {}
    def submit(self, i, ts):
        if i in self.e:
            return "duplicate"
        self.e[i] = [ts, 0, "queued"]
        return "queued"
    def record_failure(self, i, ts):
        e = self.e[i]; e[1] += 1
        if e[1] >= self.m:
            e[2] = "dead"; return -1
        e[2] = "retrying"
        return ts + self.b * 2 ** (e[1] - 1)
    def record_success(self, i):
        e = self.e[i]; e[1] += 1; e[2] = "sent"; return e[1]
    def status(self, i):
        return self.e[i][2] if i in self.e else "unknown"
''',
        '''class Notifier:
    def __init__(self, w, m, b):
        self.w, self.m, self.b, self.e = w, m, b, {}
    def submit(self, i, ts):
        e = self.e.get(i)
        if e is not None and ts - e[0] < self.w:
            return "duplicate"
        self.e[i] = [ts, 0, "queued"]
        return "queued"
    def record_failure(self, i, ts):
        e = self.e[i]; e[1] += 1
        if e[1] >= self.m:
            e[2] = "dead"; return -1
        e[2] = "retrying"
        return ts + self.b * e[1]
    def record_success(self, i):
        e = self.e[i]; e[1] += 1; e[2] = "sent"; return e[1]
    def status(self, i):
        return self.e[i][2] if i in self.e else "unknown"
''',
        '''class Notifier:
    def __init__(self, w, m, b):
        self.w, self.m, self.b, self.e = w, m, b, {}
    def submit(self, i, ts):
        e = self.e.get(i)
        if e is not None and ts - e[0] <= self.w:
            return "duplicate"
        self.e[i] = [ts, 0, "queued"]
        return "queued"
    def record_failure(self, i, ts):
        e = self.e[i]; e[1] += 1
        if e[1] >= self.m:
            e[2] = "dead"; return -1
        e[2] = "retrying"
        return ts + self.b * 2 ** (e[1] - 1)
    def record_success(self, i):
        e = self.e[i]; e[1] += 1; e[2] = "sent"; return e[1]
    def status(self, i):
        return self.e[i][2] if i in self.e else "unknown"
''',
        '''class Notifier:
    def __init__(self, w, m, b):
        self.w, self.m, self.b, self.e = w, m, b, {}
    def submit(self, i, ts):
        e = self.e.get(i)
        if e is not None and ts - e[0] < self.w:
            return "duplicate"
        self.e[i] = [ts, 0, "queued"]
        return "queued"
    def record_failure(self, i, ts):
        e = self.e[i]; e[1] += 1
        if e[1] > self.m:
            e[2] = "dead"; return -1
        e[2] = "retrying"
        return ts + self.b * 2 ** (e[1] - 1)
    def record_success(self, i):
        e = self.e[i]; e[1] += 1; e[2] = "sent"; return e[1]
    def status(self, i):
        return self.e[i][2] if i in self.e else "unknown"
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a notification system II': event ids for deduplication, exponential backoff, dead-letter queues.",
        intuition="Deduplication is a lookup: 'have I accepted this id recently?'. Retrying is a small counter with a doubling delay and a ceiling after which the event is parked for a human to inspect.",
        hints=[
            "Keep one record per event id: when it was accepted, how many attempts were made, and its status.",
            "A resubmission is a duplicate only while `ts - accepted_ts < dedup_window`; after that it is accepted afresh and the record is reset.",
            "After the n-th failure the wait is `base_delay * 2 ** (n - 1)`: base, 2 x base, 4 x base, ...",
        ],
        brute_force="Scan a list of all accepted `(id, ts)` pairs on each submit: O(n). A dictionary keyed by id makes every operation O(1).",
        approach="""1. `submit`: look the id up; duplicate if inside the window; else (re)create `[ts, 0, "queued"]`.
2. `record_failure`: increment attempts; dead if `attempts >= max_attempts`; else return `ts + base * 2 ** (attempts - 1)`.
3. `record_success`: increment attempts, mark sent, return the count.

**Dry run**, window 60, max 3, base 10: `submit(e1, 0)` queued. `submit(e1, 30)`: 30 < 60 → duplicate. Failure at 31: attempts 1 → retry at 31 + 10 = 41. Failure at 41: attempts 2 → 41 + 20 = 61. Failure at 61: attempts 3 = max → dead, -1. `submit(e1, 60)`: 60 - 0 = 60 is not < 60 → accepted again.""",
        complexity="O(1) per operation; O(number of distinct event ids) space (a real system expires them with a TTL).",
        pitfalls="Deduplicating for ever instead of within the window; linear instead of exponential delays; an off-by-one on `max_attempts` (the attempt that reaches the limit is the last); not resetting the attempt count when an id is accepted again.",
        follow_up="Add jitter (a random extra delay) and explain why. Add a cap on the maximum delay.",
    ),
),
dict(
    id="sd-feed-fanout",
    title="News Feed: Fan-out on Write and K-way Merge",
    difficulty="Medium",
    pattern="News Feed",
    kind="class",
    entry="Feed",
    description=r"""
Implement the two ways of building a news feed.

`Feed(feed_size)` keeps, for every user, a precomputed feed holding at most `feed_size` post ids.

**Fan-out on write (push)**

- `follow(follower, followee)` → `None`. Following yourself is ignored. Following does **not** add the followee's older posts to the follower's feed.
- `unfollow(follower, followee)` → `None`. Removes the relationship and removes that followee's posts from the follower's feed.
- `post(author, post_id)` → write the post into the author's own feed and into the feed of every current follower, then trim each of those feeds to the `feed_size` **newest** posts. Return the number of feeds written (followers + 1). Posts are ordered by the order in which `post` is called.
- `get_feed(user)` → the user's feed, newest first.

**Fan-out on read (pull)**

- `merge(timelines, k)` → `timelines` is a list of lists of `[timestamp, post_id]` pairs, each list sorted newest first (descending timestamp). Return the `post_id`s of the `k` newest posts overall, newest first. For equal timestamps, the smaller `post_id` comes first. This is what a feed service does at read time for accounts that are too large to push.

**Example:** `Feed(2)`: `follow("bob","ann")`, `post("ann", 1)` → 2, `post("bob", 2)` → 1, `post("ann", 3)` → 2, `get_feed("bob")` → `[3, 2]`, `get_feed("ann")` → `[3, 1]`.
""",
    starter='''class Feed:
    def __init__(self, feed_size: int):
        pass

    def follow(self, follower: str, followee: str) -> None:
        pass

    def unfollow(self, follower: str, followee: str) -> None:
        pass

    def post(self, author: str, post_id: int) -> int:
        pass

    def get_feed(self, user: str) -> List[int]:
        pass

    def merge(self, timelines: List[List[List[int]]], k: int) -> List[int]:
        pass
''',
    solution='''import heapq

class Feed:
    def __init__(self, feed_size):
        self.size = feed_size
        self.followers = {}          # followee -> set of followers
        self.feeds = {}              # user -> list of (seq, post_id, author), oldest first
        self.seq = 0

    def follow(self, follower, followee):
        if follower != followee:
            self.followers.setdefault(followee, set()).add(follower)

    def unfollow(self, follower, followee):
        self.followers.get(followee, set()).discard(follower)
        if follower != followee and follower in self.feeds:
            self.feeds[follower] = [e for e in self.feeds[follower] if e[2] != followee]

    def post(self, author, post_id):
        self.seq += 1
        targets = [author] + sorted(self.followers.get(author, ()))
        for user in targets:
            feed = self.feeds.setdefault(user, [])
            feed.append((self.seq, post_id, author))
            if len(feed) > self.size:
                del feed[:len(feed) - self.size]
        return len(targets)

    def get_feed(self, user):
        return [e[1] for e in reversed(self.feeds.get(user, []))]

    def merge(self, timelines, k):
        heap = []
        for i, t in enumerate(timelines):
            if t:
                heapq.heappush(heap, (-t[0][0], t[0][1], i, 0))
        out = []
        while heap and len(out) < k:
            _, post_id, i, j = heapq.heappop(heap)
            out.append(post_id)
            if j + 1 < len(timelines[i]):
                nxt = timelines[i][j + 1]
                heapq.heappush(heap, (-nxt[0], nxt[1], i, j + 1))
        return out
''',
    tests=[
        _ops("Feed", [2], [("follow", ["bob", "ann"]), ("post", ["ann", 1]), ("post", ["bob", 2]), ("post", ["ann", 3]), ("get_feed", ["bob"]), ("get_feed", ["ann"])]),
        _ops("Feed", [5], [("get_feed", ["nobody"]), ("post", ["a", 1]), ("get_feed", ["a"]), ("follow", ["a", "a"]), ("post", ["a", 2]), ("get_feed", ["a"])]),
        _ops("Feed", [10], [("post", ["ann", 1]), ("follow", ["bob", "ann"]), ("get_feed", ["bob"]), ("post", ["ann", 2]), ("get_feed", ["bob"]), ("unfollow", ["bob", "ann"]), ("get_feed", ["bob"]), ("post", ["ann", 3]), ("get_feed", ["bob"])]),
        _ops("Feed", [3], [("follow", [f"u{i}", "star"]) for i in range(5)] + [("post", ["star", p]) for p in (10, 11, 12, 13)] + [("get_feed", ["u0"]), ("get_feed", ["u4"]), ("get_feed", ["star"])]),
        _ops("Feed", [4], [("follow", ["c", "a"]), ("follow", ["c", "b"]), ("post", ["a", 1]), ("post", ["b", 2]), ("post", ["c", 3]), ("post", ["a", 4]), ("post", ["b", 5]), ("get_feed", ["c"]), ("unfollow", ["c", "a"]), ("get_feed", ["c"]), ("get_feed", ["a"])]),
        _ops("Feed", [0], [("post", ["a", 1]), ("get_feed", ["a"])]),
        _ops("Feed", [3], [("merge", [[[[9, 1], [5, 2], [1, 3]], [[8, 4], [7, 5]], [[6, 6]]], 4]), ("merge", [[[[9, 1], [5, 2]], [[8, 4]]], 10]), ("merge", [[], 3]), ("merge", [[[], [[1, 1]]], 3]), ("merge", [[[[5, 2]], [[5, 1]]], 2])]),
        _ops("Feed", [3], [("merge", [[[[t, t * 10 + s] for t in range(20, 0, -1)] for s in range(4)], 9]), ("merge", [[[[3, 30], [3, 10], [1, 5]], [[3, 20], [2, 7]]], 5]), ("merge", [[[[1, 1]]], 0])]),
        _ops("Feed", [2], [("follow", ["b", "a"]), ("follow", ["b", "a"]), ("post", ["a", 1]), ("unfollow", ["b", "a"]), ("unfollow", ["b", "a"]), ("post", ["a", 2]), ("get_feed", ["b"]), ("unfollow", ["x", "y"]), ("get_feed", ["x"])]),
        _ops("Feed", [5], [("follow", ["r", f"w{i}"]) for i in range(4)] + [("post", [f"w{i % 4}", i]) for i in range(12)] + [("get_feed", ["r"]), ("unfollow", ["r", "w3"]), ("get_feed", ["r"]), ("post", ["w3", 99]), ("get_feed", ["r"])]),
        _ops("Feed", [3], [("follow", ["b", "a"]), ("post", ["a", 5]), ("post", ["b", 6]), ("unfollow", ["b", "b"]), ("get_feed", ["b"]), ("unfollow", ["a", "a"]), ("get_feed", ["a"])]),
    ],
    examples=1,
    wrong_solutions=[
        '''import heapq
class Feed:
    def __init__(self, n):
        self.size, self.followers, self.feeds, self.seq = n, {}, {}, 0
    def follow(self, f, e):
        if f != e:
            self.followers.setdefault(e, set()).add(f)
    def unfollow(self, f, e):
        self.followers.get(e, set()).discard(f)
    def post(self, a, p):
        self.seq += 1
        t = [a] + sorted(self.followers.get(a, ()))
        for u in t:
            feed = self.feeds.setdefault(u, [])
            feed.append((self.seq, p, a))
            if len(feed) > self.size:
                del feed[:len(feed) - self.size]
        return len(t)
    def get_feed(self, u):
        return [e[1] for e in reversed(self.feeds.get(u, []))]
    def merge(self, timelines, k):
        allp = sorted((-t, p) for tl in timelines for t, p in tl)
        return [p for _, p in allp[:k]]
''',
        '''import heapq
class Feed:
    def __init__(self, n):
        self.size, self.followers, self.feeds, self.seq = n, {}, {}, 0
    def follow(self, f, e):
        if f != e:
            self.followers.setdefault(e, set()).add(f)
    def unfollow(self, f, e):
        self.followers.get(e, set()).discard(f)
        if f != e and f in self.feeds:
            self.feeds[f] = [x for x in self.feeds[f] if x[2] != e]
    def post(self, a, p):
        self.seq += 1
        t = [a] + sorted(self.followers.get(a, ()))
        for u in t:
            feed = self.feeds.setdefault(u, [])
            feed.append((self.seq, p, a))
            if len(feed) > self.size:
                del feed[self.size:]
        return len(t)
    def get_feed(self, u):
        return [e[1] for e in reversed(self.feeds.get(u, []))]
    def merge(self, timelines, k):
        allp = sorted((-t, p) for tl in timelines for t, p in tl)
        return [p for _, p in allp[:k]]
''',
        '''import heapq
class Feed:
    def __init__(self, n):
        self.size, self.followers, self.feeds, self.seq = n, {}, {}, 0
    def follow(self, f, e):
        if f != e:
            self.followers.setdefault(e, set()).add(f)
    def unfollow(self, f, e):
        self.followers.get(e, set()).discard(f)
        if f != e and f in self.feeds:
            self.feeds[f] = [x for x in self.feeds[f] if x[2] != e]
    def post(self, a, p):
        self.seq += 1
        t = [a] + sorted(self.followers.get(a, ()))
        for u in t:
            feed = self.feeds.setdefault(u, [])
            feed.append((self.seq, p, a))
            if len(feed) > self.size:
                del feed[:len(feed) - self.size]
        return len(t)
    def get_feed(self, u):
        return [e[1] for e in reversed(self.feeds.get(u, []))]
    def merge(self, timelines, k):
        allp = sorted(((t, p) for tl in timelines for t, p in tl), reverse=True)
        return [p for _, p in allp[:k]]
''',
        '''import heapq
class Feed:
    def __init__(self, n):
        self.size, self.followers, self.feeds, self.seq = n, {}, {}, 0
    def follow(self, f, e):
        self.followers.setdefault(e, set()).add(f)
    def unfollow(self, f, e):
        self.followers.get(e, set()).discard(f)
        if f != e and f in self.feeds:
            self.feeds[f] = [x for x in self.feeds[f] if x[2] != e]
    def post(self, a, p):
        self.seq += 1
        t = sorted(set([a]) | self.followers.get(a, set()))
        for u in t:
            feed = self.feeds.setdefault(u, [])
            feed.append((self.seq, p, a))
            if len(feed) > self.size:
                del feed[:len(feed) - self.size]
        return len(self.followers.get(a, set())) + 1
    def get_feed(self, u):
        return [e[1] for e in reversed(self.feeds.get(u, []))]
    def merge(self, timelines, k):
        allp = sorted((-t, p) for tl in timelines for t, p in tl)
        return [p for _, p in allp[:k]]
''',
    ],
    guide=dict(
        prereqs="Both news feed lessons: fan-out on write, fan-out on read, the hybrid. `heapq` for merging sorted lists.",
        intuition="Push does the work when someone posts: copy the post id into every follower's ready-made list, so reading is trivial. Pull does the work when someone reads: take the newest items of several already-sorted lists and merge them, always taking the largest head next.",
        hints=[
            "Store `followers[followee]` as a set, and each feed as a list of `(sequence, post_id, author)` so that unfollow can filter by author.",
            "After appending to a feed, cut it down from the old end to `feed_size` entries.",
            "For `merge`, a heap holding one candidate per timeline (its current head) gives the next newest post in O(log T).",
        ],
        brute_force="Pull everything: on every `get_feed`, collect all posts of everyone the user follows, sort, and take the top N. Reads cost O(total posts log total posts). Push makes reads O(feed_size); the heap merge makes pull O(k log T).",
        approach="""**Push.** `post`: increment a global sequence; targets = author + followers; append `(seq, post_id, author)` to each target's feed and trim from the front. `get_feed`: reverse the list. `unfollow`: remove the edge and filter the feed.

**Pull.** Push the head of every non-empty timeline onto a max-heap (negated timestamp, then post id). Pop the best, output it, push that timeline's next element. Stop after k.

**Dry run** of merge with `[[9,1],[5,2],[1,3]]`, `[[8,4],[7,5]]`, `[[6,6]]`, k = 4: heap heads 9, 8, 6 → pop 9 (post 1), push 5 → pop 8 (post 4), push 7 → pop 7 (post 5) → pop 6 (post 6). Result `[1, 4, 5, 6]`.""",
        complexity="`post` O(F) for F followers (this is the cost that explodes for celebrity accounts). `get_feed` O(feed_size). `merge` O(T + k log T) for T timelines.",
        pitfalls="Trimming the newest posts instead of the oldest; backfilling on follow or forgetting to remove posts on unfollow, against the stated rules; letting a self-follow double-write the author's feed; breaking timestamp ties the wrong way in `merge`.",
        follow_up="Implement the hybrid: push for authors with fewer than a threshold of followers, and at read time merge the pushed feed with the recent posts of the large accounts the user follows.",
    ),
),
dict(
    id="sd-chat-sequencer",
    title="Chat: Per-Channel Message Ordering and Presence",
    difficulty="Medium",
    pattern="Chat System",
    kind="class",
    entry="ChatServer",
    description=r"""
Implement the two pieces of state at the heart of a chat service: ordered message logs and heartbeat-based presence.

`ChatServer(heartbeat_timeout)`:

**Messages**

- `send(channel, user, client_msg_id, text)` → store the message in the channel and return its **sequence number**. Each channel numbers its messages 1, 2, 3, ... independently. If the same `user` has already sent a message with the same `client_msg_id` to that channel, do **not** store a second copy: return the original sequence number (this makes client retries safe).
- `fetch(channel, after_seq, limit)` → up to `limit` messages of the channel with sequence number greater than `after_seq`, in increasing order, each as `[seq, user, text]`. An unknown channel gives `[]`.

**Presence**

- `heartbeat(user, ts)` → `None`. Records that the user's client was alive at time `ts`.
- `online(ts)` → the sorted list of users whose latest heartbeat satisfies `ts - last <= heartbeat_timeout`.
- `last_seen(user)` → the time of the user's latest heartbeat, or `-1` if there is none.

**Example:** `ChatServer(30)`: `send("c1","ann","m1","hi")` → 1, `send("c1","bob","m1","yo")` → 2, `send("c1","ann","m1","hi")` → 1 (retry), `send("c2","ann","m1","hi")` → 1, `fetch("c1",0,10)` → `[[1,"ann","hi"],[2,"bob","yo"]]`.
""",
    starter='''class ChatServer:
    def __init__(self, heartbeat_timeout: int):
        pass

    def send(self, channel: str, user: str, client_msg_id: str, text: str) -> int:
        pass

    def fetch(self, channel: str, after_seq: int, limit: int) -> List[list]:
        pass

    def heartbeat(self, user: str, ts: int) -> None:
        pass

    def online(self, ts: int) -> List[str]:
        pass

    def last_seen(self, user: str) -> int:
        pass
''',
    solution='''class ChatServer:
    def __init__(self, heartbeat_timeout):
        self.timeout = heartbeat_timeout
        self.logs = {}               # channel -> list of [seq, user, text]
        self.sent = {}               # (channel, user, client_msg_id) -> seq
        self.beats = {}              # user -> last heartbeat time

    def send(self, channel, user, client_msg_id, text):
        key = (channel, user, client_msg_id)
        if key in self.sent:
            return self.sent[key]
        log = self.logs.setdefault(channel, [])
        seq = len(log) + 1
        log.append([seq, user, text])
        self.sent[key] = seq
        return seq

    def fetch(self, channel, after_seq, limit):
        log = self.logs.get(channel, [])
        start = max(0, after_seq)
        return [list(m) for m in log[start:start + max(0, limit)]]

    def heartbeat(self, user, ts):
        self.beats[user] = max(ts, self.beats.get(user, ts))

    def online(self, ts):
        return sorted(u for u, last in self.beats.items() if ts - last <= self.timeout)

    def last_seen(self, user):
        return self.beats.get(user, -1)
''',
    tests=[
        _ops("ChatServer", [30], [("send", ["c1", "ann", "m1", "hi"]), ("send", ["c1", "bob", "m1", "yo"]), ("send", ["c1", "ann", "m1", "hi"]), ("send", ["c2", "ann", "m1", "hi"]), ("fetch", ["c1", 0, 10])]),
        _ops("ChatServer", [10], [("fetch", ["none", 0, 5]), ("online", [100]), ("last_seen", ["ghost"])]),
        _ops("ChatServer", [10], [("send", ["room", f"u{i % 3}", f"id{i}", f"msg {i}"]) for i in range(8)] + [("fetch", ["room", 0, 3]), ("fetch", ["room", 3, 3]), ("fetch", ["room", 6, 3]), ("fetch", ["room", 8, 3]), ("fetch", ["room", 100, 3]), ("fetch", ["room", 2, 0])]),
        _ops("ChatServer", [30], [("heartbeat", ["ann", 0]), ("heartbeat", ["bob", 10]), ("online", [20]), ("online", [30]), ("online", [31]), ("online", [40]), ("online", [41]), ("last_seen", ["ann"]), ("last_seen", ["bob"])]),
        _ops("ChatServer", [5], [("heartbeat", ["z", 1]), ("heartbeat", ["a", 2]), ("heartbeat", ["m", 3]), ("online", [4]), ("heartbeat", ["z", 9]), ("online", [9]), ("last_seen", ["z"]), ("online", [15])]),
        _ops("ChatServer", [5], [("send", ["c", "ann", "x", "first"]), ("send", ["c", "ann", "y", "second"]), ("send", ["c", "ann", "x", "first again"]), ("send", ["c", "bob", "x", "bob x"]), ("fetch", ["c", 0, 10]), ("send", ["c", "ann", "y", "dup"]), ("fetch", ["c", 1, 10])]),
        _ops("ChatServer", [0], [("heartbeat", ["a", 5]), ("online", [5]), ("online", [6])]),
        _ops("ChatServer", [100], [("send", [f"ch{i % 2}", "u", f"k{i}", str(i)]) for i in range(7)] + [("fetch", ["ch0", 0, 100]), ("fetch", ["ch1", 1, 1])]),
        _ops("ChatServer", [20], [("send", ["g", "a", "1", "one"]), ("heartbeat", ["a", 100]), ("send", ["g", "b", "1", "two"]), ("heartbeat", ["b", 115]), ("online", [121]), ("fetch", ["g", 1, 5]), ("last_seen", ["a"])]),
        _ops("ChatServer", [10], [("send", ["c", "a", "r", "t"])] * 5 + [("fetch", ["c", 0, 10]), ("send", ["c", "a", "s", "t"]), ("fetch", ["c", 0, 10])]),
        _ops("ChatServer", [3], [("heartbeat", [f"user{i}", i]) for i in range(10)] + [("online", [t]) for t in (9, 10, 12, 13)]),
    ],
    examples=1,
    wrong_solutions=[
        '''class ChatServer:
    def __init__(self, t):
        self.t, self.logs, self.beats, self.n = t, {}, {}, 0
    def send(self, c, u, i, text):
        self.n += 1
        self.logs.setdefault(c, []).append([self.n, u, text])
        return self.n
    def fetch(self, c, a, l):
        return [m for m in self.logs.get(c, []) if m[0] > a][:l]
    def heartbeat(self, u, ts):
        self.beats[u] = ts
    def online(self, ts):
        return sorted(u for u, x in self.beats.items() if ts - x <= self.t)
    def last_seen(self, u):
        return self.beats.get(u, -1)
''',
        '''class ChatServer:
    def __init__(self, t):
        self.t, self.logs, self.sent, self.beats = t, {}, {}, {}
    def send(self, c, u, i, text):
        if (c, i) in self.sent:
            return self.sent[(c, i)]
        log = self.logs.setdefault(c, [])
        log.append([len(log) + 1, u, text])
        self.sent[(c, i)] = len(log)
        return len(log)
    def fetch(self, c, a, l):
        return [m for m in self.logs.get(c, []) if m[0] > a][:l]
    def heartbeat(self, u, ts):
        self.beats[u] = ts
    def online(self, ts):
        return sorted(u for u, x in self.beats.items() if ts - x <= self.t)
    def last_seen(self, u):
        return self.beats.get(u, -1)
''',
        '''class ChatServer:
    def __init__(self, t):
        self.t, self.logs, self.sent, self.beats = t, {}, {}, {}
    def send(self, c, u, i, text):
        if (c, u, i) in self.sent:
            return self.sent[(c, u, i)]
        log = self.logs.setdefault(c, [])
        log.append([len(log) + 1, u, text])
        self.sent[(c, u, i)] = len(log)
        return len(log)
    def fetch(self, c, a, l):
        return [m for m in self.logs.get(c, []) if m[0] >= a][:l]
    def heartbeat(self, u, ts):
        self.beats[u] = ts
    def online(self, ts):
        return sorted(u for u, x in self.beats.items() if ts - x <= self.t)
    def last_seen(self, u):
        return self.beats.get(u, -1)
''',
        '''class ChatServer:
    def __init__(self, t):
        self.t, self.logs, self.sent, self.beats = t, {}, {}, {}
    def send(self, c, u, i, text):
        if (c, u, i) in self.sent:
            return self.sent[(c, u, i)]
        log = self.logs.setdefault(c, [])
        log.append([len(log) + 1, u, text])
        self.sent[(c, u, i)] = len(log)
        return len(log)
    def fetch(self, c, a, l):
        return [m for m in self.logs.get(c, []) if m[0] > a][:l]
    def heartbeat(self, u, ts):
        self.beats[u] = ts
    def online(self, ts):
        return sorted(u for u, x in self.beats.items() if ts - x < self.t)
    def last_seen(self, u):
        return self.beats.get(u, -1)
''',
    ],
    guide=dict(
        prereqs="Both chat lessons: per-channel sequence numbers, the sync cursor, client message ids, heartbeats.",
        intuition="Ordering only needs to hold inside one conversation, so each channel keeps its own counter. A client that is unsure whether a send arrived retries with the same client id, and the server recognises it. Presence is not 'connected or not' but 'heard from recently'.",
        hints=[
            "A channel's next sequence number is the length of its log plus one.",
            "Remember `(channel, user, client_msg_id) -> seq` so that a retry returns the old number.",
            "`fetch` with `after_seq = n` starts at list index `n`, because sequence numbers start at 1.",
        ],
        brute_force="One global counter and one global list gives a total order, but every fetch scans all messages of all channels, and a global counter is a single hot spot. Per-channel logs make fetch O(limit).",
        approach="""1. `send`: check the dedup map; otherwise append `[len + 1, user, text]` and record it.
2. `fetch`: slice `log[after_seq : after_seq + limit]`.
3. `heartbeat`: store the latest time. `online`: users with `ts - last <= timeout`, sorted.

**Dry run**: `send(c1, ann, m1)` → 1; `send(c1, bob, m1)` → 2 (different user, so not a duplicate); `send(c1, ann, m1)` → 1 again, nothing stored; `send(c2, ann, m1)` → 1, because c2 has its own numbering. `fetch(c1, 1, 10)` → only message 2.""",
        complexity="`send` and `heartbeat` O(1); `fetch` O(limit); `online` O(U log U) for U users (a real system would not list everyone).",
        pitfalls="One counter shared by all channels; deduplicating on the client id alone (two users may reuse the same id); including the message with `seq == after_seq`; using `<` where presence needs `<=`.",
        follow_up="How would two chat servers assign sequence numbers to the same channel without clashing? (One writer per channel, or an atomic counter in a shared store.)",
    ),
),
dict(
    id="sd-autocomplete-trie",
    title="Autocomplete: Top-k Queries from a Trie",
    difficulty="Medium",
    pattern="Search Autocomplete",
    kind="class",
    entry="Autocomplete",
    description=r"""
Build the data structure behind search suggestions.

`Autocomplete(k)`:

- `add(query, count)` → `None`. Record that `query` (a non-empty lower-case string, which may contain spaces) was searched `count` more times. Counts accumulate across calls.
- `top(prefix)` → up to `k` stored queries that start with `prefix`, ordered by total count descending, ties broken alphabetically (ascending). An empty prefix matches every query.
- `count(query)` → the total count recorded for exactly this query (0 if never added).

**Example:** `Autocomplete(2)`; `add("tree", 10)`, `add("true", 35)`, `add("try", 29)`, `add("toy", 14)`: `top("tr")` → `["true", "try"]`, `top("t")` → `["true", "try"]`, `top("to")` → `["toy"]`, `top("x")` → `[]`.
""",
    starter='''class Autocomplete:
    def __init__(self, k: int):
        pass

    def add(self, query: str, count: int) -> None:
        pass

    def top(self, prefix: str) -> List[str]:
        pass

    def count(self, query: str) -> int:
        pass
''',
    solution='''class Autocomplete:
    def __init__(self, k):
        self.k = k
        self.root = {}                 # char -> child dict; "$" holds the count at a terminal

    def add(self, query, count):
        node = self.root
        for ch in query:
            node = node.setdefault(ch, {})
        node["$"] = node.get("$", 0) + count

    def _find(self, text):
        node = self.root
        for ch in text:
            node = node.get(ch)
            if node is None:
                return None
        return node

    def top(self, prefix):
        start = self._find(prefix)
        if start is None:
            return []
        found = []
        stack = [(start, prefix)]
        while stack:
            node, text = stack.pop()
            for ch, child in node.items():
                if ch == "$":
                    found.append((-child, text))
                else:
                    stack.append((child, text + ch))
        found.sort()
        return [text for _, text in found[:self.k]]

    def count(self, query):
        node = self._find(query)
        return node.get("$", 0) if node else 0
''',
    tests=[
        _ops("Autocomplete", [2], [("add", ["tree", 10]), ("add", ["true", 35]), ("add", ["try", 29]), ("add", ["toy", 14]), ("top", ["tr"]), ("top", ["t"]), ("top", ["to"]), ("top", ["x"])]),
        _ops("Autocomplete", [3], [("top", [""]), ("count", ["a"]), ("add", ["a", 1]), ("top", [""]), ("top", ["a"]), ("top", ["ab"]), ("count", ["a"])]),
        _ops("Autocomplete", [5], [("add", ["wish", 25]), ("add", ["win", 50]), ("add", ["be", 15]), ("add", ["bet", 29]), ("add", ["buy", 14]), ("add", ["best", 35]), ("add", ["bee", 20]), ("top", ["b"]), ("top", ["be"]), ("top", ["w"]), ("top", [""])]),
        _ops("Autocomplete", [2], [("add", ["cat", 5]), ("add", ["car", 5]), ("add", ["cab", 5]), ("top", ["ca"]), ("add", ["cat", 1]), ("top", ["ca"]), ("count", ["cat"]), ("count", ["ca"])]),
        _ops("Autocomplete", [3], [("add", ["new york", 9]), ("add", ["new york times", 7]), ("add", ["new", 3]), ("add", ["news", 8]), ("top", ["new"]), ("top", ["new "]), ("top", ["new york"]), ("count", ["new"])]),
        _ops("Autocomplete", [1], [("add", ["a", 1]), ("add", ["ab", 2]), ("add", ["abc", 3]), ("top", ["a"]), ("top", ["ab"]), ("top", ["abc"]), ("top", ["abcd"])]),
        _ops("Autocomplete", [0], [("add", ["a", 1]), ("top", ["a"])]),
        _ops("Autocomplete", [5], [("add", ["banana", 9]), ("add", ["apple", 2]), ("add", ["grape", 5]), ("top", ["a"]), ("top", ["an"]), ("top", ["ap"])]),
        _ops("Autocomplete", [4], [("add", [f"q{i:02d}", i % 7]) for i in range(30)] + [("top", ["q"]), ("top", ["q0"]), ("top", ["q1"]), ("top", ["q29"])]),
        _ops("Autocomplete", [3], [("add", ["apple", 3]), ("add", ["app", 3]), ("add", ["apply", 3]), ("add", ["ape", 3]), ("top", ["ap"]), ("add", ["apply", 1]), ("top", ["ap"]), ("top", ["app"])]),
        _ops("Autocomplete", [2], [("add", ["x", 1])] * 5 + [("count", ["x"]), ("add", ["xy", 4]), ("top", ["x"]), ("add", ["xy", 2]), ("top", ["x"])]),
        _ops("Autocomplete", [5], [("add", [w, c]) for w, c in [("go", 100), ("golang", 80), ("google", 300), ("good", 80), ("gopher", 20), ("goal", 80), ("g", 1)]] + [("top", ["go"]), ("top", ["goo"]), ("top", ["g"])]),
    ],
    examples=1,
    wrong_solutions=[
        '''class Autocomplete:
    def __init__(self, k):
        self.k, self.c = k, {}
    def add(self, q, n):
        self.c[q] = n
    def top(self, p):
        m = sorted((-n, q) for q, n in self.c.items() if q.startswith(p))
        return [q for _, q in m[:self.k]]
    def count(self, q):
        return self.c.get(q, 0)
''',
        '''class Autocomplete:
    def __init__(self, k):
        self.k, self.c = k, {}
    def add(self, q, n):
        self.c[q] = self.c.get(q, 0) + n
    def top(self, p):
        m = sorted(((n, q) for q, n in self.c.items() if q.startswith(p)), reverse=True)
        return [q for _, q in m[:self.k]]
    def count(self, q):
        return self.c.get(q, 0)
''',
        '''class Autocomplete:
    def __init__(self, k):
        self.k, self.c = k, {}
    def add(self, q, n):
        self.c[q] = self.c.get(q, 0) + n
    def top(self, p):
        m = sorted((-n, q) for q, n in self.c.items() if p in q)
        return [q for _, q in m[:self.k]]
    def count(self, q):
        return self.c.get(q, 0)
''',
        '''class Autocomplete:
    def __init__(self, k):
        self.k, self.c = k, {}
    def add(self, q, n):
        self.c[q] = self.c.get(q, 0) + n
    def top(self, p):
        m = sorted((-n, q) for q, n in self.c.items() if q.startswith(p) and q != p)
        return [q for _, q in m[:self.k]]
    def count(self, q):
        return self.c.get(q, 0)
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design search autocomplete I': the trie, prefix lookup, top-k by frequency. Dictionaries of dictionaries.",
        intuition="A trie stores words by their letters, so every word with a given prefix lives in the subtree under that prefix's node. Walk to the node, collect the completed queries below it, and rank them.",
        hints=[
            "Represent a node as a dict from character to child node, with a special key (such as `$`) holding the count where a query ends.",
            "Walking the prefix costs one step per character; if a character is missing, there are no suggestions.",
            "Collect `(-count, query)` pairs from the subtree and sort: that gives count descending, then alphabetical.",
        ],
        brute_force="Keep a flat dictionary of counts and test `startswith(prefix)` on every stored query: O(N) per keystroke. The trie visits only the matching subtree. (A flat dictionary is in fact a valid solution here; the trie is what scales.)",
        approach="""1. `add`: walk or create nodes for each character; add to the terminal count.
2. `top`: walk to the prefix node; depth-first search the subtree, rebuilding each query's text; sort by `(-count, text)`; take k.
3. `count`: walk to the node and read its terminal count.

**Dry run** with tree 10, true 35, try 29, toy 14 and `top("tr")`: walk t → r. Under it: `tree` (10), `true` (35), `try` (29). Sorted: true, try, tree. With k = 2: `["true", "try"]`.""",
        complexity="`add` O(L) for a query of length L. `top` O(P + S log S) where P is the prefix length and S the size of the subtree. Caching the top k at every node, as the lessons describe, makes `top` O(P).",
        pitfalls="Overwriting counts instead of accumulating; sorting ties in reverse alphabetical order (a side effect of `reverse=True`); matching the prefix anywhere in the string; excluding the query that equals the prefix.",
        follow_up="Store the top-k list at every node and update it on `add`. What does that do to the cost of `add`, and why do production systems rebuild the trie offline instead?",
    ),
),
dict(
    id="sd-bitrate-ladder",
    title="Adaptive Bitrate: Choose the Next Rendition",
    difficulty="Easy",
    pattern="Video Streaming",
    kind="function",
    entry="choose_rendition",
    description=r"""
A video player holds a **bitrate ladder**: a list of renditions `[height, kbps]` (for example `[720, 2800]` is 720p at 2,800 kilobits per second). Before downloading each segment it picks a rendition.

Write `choose_rendition(ladder, throughput_kbps, buffer_s, current_height)` returning the **height** to use next. The ladder is not necessarily sorted; bitrates are distinct; `current_height` is in the ladder. Apply the rules in order:

1. **Panic:** if `buffer_s < 5`, return the height of the lowest-bitrate rendition.
2. **Budget:** a rendition fits if its bitrate is at most 80% of the measured throughput. To avoid rounding problems test `kbps * 10 <= throughput_kbps * 8`. The **target** is the highest-bitrate rendition that fits, or the lowest-bitrate rendition if none fits.
3. **Careful upswitch:** if the target's bitrate is higher than the current rendition's bitrate and `buffer_s < 15`, move up only **one** step: return the rendition with the next higher bitrate above the current one.
4. Otherwise return the target (this includes staying put and switching down any number of steps).

**Example** with ladder `[[240,400],[360,800],[480,1400],[720,2800],[1080,5000]]`:
`choose_rendition(ladder, 4000, 20, 360)` → `720` (2800 <= 3200, buffer healthy);
`choose_rendition(ladder, 4000, 10, 360)` → `480` (one step up only);
`choose_rendition(ladder, 4000, 3, 720)` → `240` (panic).
""",
    starter='''def choose_rendition(ladder: List[List[int]], throughput_kbps: int, buffer_s: int, current_height: int) -> int:
    pass
''',
    solution='''def choose_rendition(ladder, throughput_kbps, buffer_s, current_height):
    steps = sorted(ladder, key=lambda r: r[1])            # lowest bitrate first
    if buffer_s < 5:
        return steps[0][0]
    target = 0
    for i, (_, kbps) in enumerate(steps):
        if kbps * 10 <= throughput_kbps * 8:
            target = i
    current = next(i for i, r in enumerate(steps) if r[0] == current_height)
    if target > current and buffer_s < 15:
        return steps[current + 1][0]
    return steps[target][0]
''',
    tests=[
        [_LADDER[:5], 4000, 20, 360],
        [_LADDER[:5], 4000, 10, 360],
        [_LADDER[:5], 4000, 3, 720],
        [_LADDER, 100, 30, 1080],
        [_LADDER, 100000, 30, 240],
        [_LADDER, 100000, 14, 240],
        [_LADDER, 3500, 15, 240],
        [_LADDER, 3500, 14, 480],
        [_LADDER, 1000, 50, 1080],
        [_LADDER, 1000, 5, 240],
        [_LADDER, 1000, 4, 240],
        [list(reversed(_LADDER)), 6250, 60, 480],
        [list(reversed(_LADDER)), 6249, 60, 480],
        [[[480, 1400]], 50, 2, 480],
        [[[1080, 5000], [240, 400], [720, 2800]], 3500, 8, 240],
        [_LADDER, 1750, 12, 480],
        [_LADDER, 1000, 10, 1080],
        [_LADDER, 2000, 6, 2160],
    ],
    examples=3,
    wrong_solutions=[
        '''def choose_rendition(ladder, t, b, cur):
    steps = sorted(ladder, key=lambda r: r[1])
    target = 0
    for i, (_, k) in enumerate(steps):
        if k * 10 <= t * 8:
            target = i
    return steps[target][0]
''',
        '''def choose_rendition(ladder, t, b, cur):
    steps = sorted(ladder, key=lambda r: r[1])
    if b < 5:
        return steps[0][0]
    target = 0
    for i, (_, k) in enumerate(steps):
        if k <= t:
            target = i
    c = next(i for i, r in enumerate(steps) if r[0] == cur)
    if target > c and b < 15:
        return steps[c + 1][0]
    return steps[target][0]
''',
        '''def choose_rendition(ladder, t, b, cur):
    steps = ladder
    if b < 5:
        return steps[0][0]
    target = 0
    for i, (_, k) in enumerate(steps):
        if k * 10 <= t * 8:
            target = i
    c = next(i for i, r in enumerate(steps) if r[0] == cur)
    if target > c and b < 15:
        return steps[c + 1][0]
    return steps[target][0]
''',
        '''def choose_rendition(ladder, t, b, cur):
    steps = sorted(ladder, key=lambda r: r[1])
    if b < 5:
        return steps[0][0]
    target = 0
    for i, (_, k) in enumerate(steps):
        if k * 10 <= t * 8:
            target = i
    c = next(i for i, r in enumerate(steps) if r[0] == cur)
    if target != c and b < 15:
        return steps[c + 1][0] if target > c else steps[c - 1][0]
    return steps[target][0]
''',
    ],
    guide=dict(
        prereqs="Lesson 'Design a video platform II': the bitrate ladder and adaptive bitrate streaming.",
        intuition="The player wants the best picture it can download faster than it plays. It keeps a safety margin on the measured speed, drops to the bottom rung if it is about to stall, and climbs cautiously so that one lucky measurement does not cause a stall later.",
        hints=[
            "Sort the ladder by bitrate first; then 'one step up' is the next index.",
            "Find the target index: the last rendition with `kbps * 10 <= throughput * 8`, defaulting to index 0.",
            "Only the upward move is limited to one step, and only when the buffer is below 15 seconds.",
        ],
        brute_force="The ladder has a handful of entries, so a linear scan is already the best approach. The work is in applying the rules in the right order.",
        approach="""1. Sort by bitrate. 2. Buffer below 5 → lowest. 3. Target = highest fitting index, else 0. 4. If target is above current and buffer below 15 → current + 1. 5. Else target.

**Dry run**, throughput 4000, buffer 10, current 360p: not panic. Budget 3200: 400, 800, 1400, 2800 fit; 5000 does not → target 720p (index 3). Current is index 1; target is higher and the buffer is under 15 → index 2 → 480.""",
        complexity="O(n log n) for the sort over a ladder of n renditions (n is about 6); O(n) if the ladder is stored sorted.",
        pitfalls="Assuming the ladder is sorted; using 100% of the throughput; limiting downward switches to one step (when the network collapses you must drop at once); forgetting the default when nothing fits.",
        follow_up="Real players smooth the throughput estimate over several segments. Take a list of recent measurements and use their harmonic mean.",
    ),
),
dict(
    id="sd-block-delta",
    title="File Sync: Which Blocks Changed?",
    difficulty="Medium",
    pattern="File Sync",
    kind="function",
    entry="block_delta",
    description=r"""
A sync client splits files into fixed-size blocks and uploads only what the server does not already have.

Split a string into blocks of `block_size` characters; the last block may be shorter. An empty string has zero blocks.

Write `block_delta(old, new, block_size)` returning a list of three values:

1. `changed`: the ascending list of block indexes `i` of the **new** file whose content differs from block `i` of the old file, or for which the old file has no block `i`.
2. `removed`: how many trailing blocks the old file has beyond the end of the new file (`max(0, old_blocks - new_blocks)`).
3. `uploads`: the number of **distinct** block contents in the new file that do not appear among the old file's blocks at **any** position. This is what a content-addressed store must actually receive: a block that only moved, or that repeats, costs nothing.

**Example:** `block_delta("aaaabbbbcccc", "aaaaXXXXcccc", 4)` → `[[1], 0, 1]`

**Example:** `block_delta("aaaabbbb", "bbbbaaaa", 4)` → `[[0, 1], 0, 0]` (both positions changed, but both contents are already stored)
""",
    starter='''def block_delta(old: str, new: str, block_size: int):
    pass
''',
    solution='''def block_delta(old, new, block_size):
    def split(s):
        return [s[i:i + block_size] for i in range(0, len(s), block_size)]
    a, b = split(old), split(new)
    changed = [i for i, blk in enumerate(b) if i >= len(a) or a[i] != blk]
    have = set(a)
    uploads = len({blk for blk in b if blk not in have})
    return [changed, max(0, len(a) - len(b)), uploads]
''',
    tests=[
        ["aaaabbbbcccc", "aaaaXXXXcccc", 4],
        ["aaaabbbb", "bbbbaaaa", 4],
        ["", "", 4],
        ["", "hello world", 4],
        ["hello world", "", 4],
        ["abcdefgh", "abcdefgh", 3],
        ["abcdefgh", "abcdefghij", 4],
        ["abcdefghij", "abcdefgh", 4],
        ["aaaaaaaaaaaa", "aaaabbbbbbbbbbbb", 4],
        ["abcdefgh", "Xabcdefgh", 4],
        ["x" * 100, "x" * 50 + "y" + "x" * 49, 10],
        ["abcabcabc", "abcabcabcabc", 3],
        ["ab", "abab", 2],
        ["the quick brown fox", "the quick red fox", 1],
        ["0123456789" * 30, "0123456789" * 15 + "ZZZZZZZZZZ" + "0123456789" * 14, 10],
    ],
    examples=2,
    wrong_solutions=[
        '''def block_delta(old, new, n):
    sp = lambda s: [s[i:i + n] for i in range(0, len(s), n)]
    a, b = sp(old), sp(new)
    ch = [i for i, x in enumerate(b) if i >= len(a) or a[i] != x]
    return [ch, max(0, len(a) - len(b)), len(ch)]
''',
        '''def block_delta(old, new, n):
    sp = lambda s: [s[i:i + n] for i in range(0, len(s), n)]
    a, b = sp(old), sp(new)
    ch = [i for i, x in enumerate(b) if i >= len(a) or a[i] != x]
    have = set(a)
    return [ch, max(0, len(a) - len(b)), len([x for x in b if x not in have])]
''',
        '''def block_delta(old, new, n):
    sp = lambda s: [s[i:i + n] for i in range(0, len(s), n)]
    a, b = sp(old), sp(new)
    ch = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    have = set(a)
    return [ch, max(0, len(a) - len(b)), len({x for x in b if x not in have})]
''',
        '''def block_delta(old, new, n):
    sp = lambda s: [s[i:i + n] for i in range(0, len(s), n)]
    a, b = sp(old), sp(new)
    ch = [i for i, x in enumerate(b) if i >= len(a) or a[i] != x]
    have = set(a)
    return [ch, len(a) - len(b), len({x for x in b if x not in have})]
''',
    ],
    guide=dict(
        prereqs="Both file sync lessons: block-level storage, delta sync and content-addressed deduplication.",
        intuition="Two different questions are being asked. 'Which positions changed?' compares block i with block i. 'What must be uploaded?' asks whether the server already holds a block with this content anywhere, which is a set lookup.",
        hints=[
            "Write a helper that slices a string into blocks with `range(0, len(s), block_size)`.",
            "`changed`: index i is changed if the old file has no block i or the two blocks differ.",
            "`uploads`: put the old blocks in a set; collect the new blocks not in it into another set and take its size.",
        ],
        brute_force="Upload the whole new file every time: correct and wasteful, O(file size) of network for a one-character edit. Position-by-position comparison finds the changed blocks; the set lookup avoids re-uploading content the store already has.",
        approach="""1. Split both strings.
2. `changed = [i for i in range(len(b)) if i >= len(a) or a[i] != b[i]]`.
3. `removed = max(0, len(a) - len(b))`.
4. `uploads = len(set(b) - set(a))`.

**Dry run**, `old = "aaaabbbb"`, `new = "bbbbaaaa"`, size 4: old blocks `[aaaa, bbbb]`, new `[bbbb, aaaa]`. Position 0 differs, position 1 differs → `[0, 1]`. Removed 0. New contents `{bbbb, aaaa}` are both in the old set → 0 uploads.""",
        complexity="O(len(old) + len(new)) time and space (hashing each block once).",
        pitfalls="Counting changed positions as uploads; counting a repeated new block twice; ignoring new blocks beyond the old file's length; returning a negative `removed`. Also notice the insertion test: inserting one character at the front shifts every fixed-size block, which is the weakness that content-defined chunking fixes.",
        follow_up="Implement content-defined chunking with a rolling hash so that an insertion changes only the blocks around it.",
    ),
),
]
