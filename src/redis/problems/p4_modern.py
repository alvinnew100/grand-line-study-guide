"""Redis track problems 21-27: HyperLogLog, bitmaps, cluster slots, consistent hashing, search, timelines, visitors."""
import random as _r


def _seq(seed, n, ctor, ctor_args, step):
    rng, state = _r.Random(seed), {"now": 0, "post": 0}
    ops, args = [ctor], [list(ctor_args)]
    for _ in range(n):
        op, a = step(rng, state)
        ops.append(op)
        args.append(a)
    return [ops, args]


def _bitmap_step(rng, st):
    d = rng.choice(["mon", "tue", "wed"])
    op = rng.choice(["mark", "mark", "mark", "is_active", "count", "active_all", "active_any", "size_bytes"])
    if op in ("mark", "is_active"):
        return op, [d, rng.choice([0, 1, 7, 8, 9, 15, 16, 40, 100])]
    if op in ("count", "size_bytes"):
        return op, [d]
    return op, [rng.sample(["mon", "tue", "wed", "sun"], rng.randint(1, 3))]


def _ring_step(rng, st):
    op = rng.choice(["add_node", "add_node", "remove_node", "get_node", "get_node", "distribution"])
    if op in ("add_node", "remove_node"):
        return op, [rng.choice(["A", "B", "C", "D"])]
    if op == "get_node":
        return op, ["user:%d" % rng.randint(0, 50)]
    return op, [["k%d" % i for i in range(rng.randint(0, 40))]]


_TEXTS = ["Slow rye bread with honey", "Banana bread and walnuts", "Honey cake, the spiced one", "A loaf of seeds",
          "Rye crackers to go", "Tea and honey", "THE BREAD OF BREADS", "x y zz 42 bread"]


def _index_step(rng, st):
    op = rng.choice(["add", "add", "add", "remove", "search_and", "search_or", "search_not"])
    words = ["bread", "honey", "rye", "cake", "seeds", "the", "Loaf", "42", "tea", "zz"]
    if op == "add":
        return op, [rng.randint(1, 5), rng.choice(_TEXTS)]
    if op == "remove":
        return op, [rng.randint(1, 5)]
    if op == "search_not":
        return op, [rng.sample(words, rng.randint(1, 2)), rng.sample(words, rng.randint(0, 2))]
    return op, [rng.sample(words, rng.randint(0, 3))]


def _tl_step(rng, st):
    u, v = rng.sample(["ann", "bo", "cy", "di"], 2)
    op = rng.choice(["follow", "follow", "unfollow", "post", "post", "post", "home", "profile", "delete"])
    if op in ("follow", "unfollow"):
        return op, [u, v]
    if op == "post":
        st["post"] += 1
        st["now"] += rng.choice([0, 1, 2])
        return op, [u, st["post"], st["now"]]
    if op in ("home", "profile"):
        return op, [u, rng.randint(0, 5)]
    return op, [rng.randint(1, max(1, st["post"] + 1))]


def _vis_step(rng, st):
    st["now"] += rng.choice([0, 1, 3, 12, 30])
    v = rng.choice(["u1", "u2", "u3", "u4"])
    op = rng.choice(["record", "record", "record", "unique", "unique_range", "buckets", "expire_before"])
    if op == "record":
        return op, [st["now"], v]
    if op == "unique":
        return op, [rng.randint(0, st["now"] + 10)]
    if op == "unique_range":
        a = rng.randint(0, st["now"] + 5)
        return op, [a, a + rng.randint(0, 80)]
    if op == "expire_before":
        return op, [rng.randint(0, st["now"])]
    return op, []


_rng = _r.Random(2026)
_HLL_OK = '''def hll_estimate(items, b):
    m = 1 << b
    reg = [0] * m
    width = 32 - b
    for item in items:
        h = 2166136261
        for byte in item.encode("utf-8"):
            h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
        index = h >> width
        rest = h & ((1 << width) - 1)
        rank = width - rest.bit_length() + 1
        if rank > reg[index]:
            reg[index] = rank
    alpha = {16: 0.673, 32: 0.697, 64: 0.709}.get(m, 0.7213 / (1 + 1.079 / m))
    estimate = alpha * m * m / sum(2.0 ** -r for r in reg)
    zeros = reg.count(0)
    if %s:
        estimate = m * math.log(m / zeros)
    return estimate
'''

_SLOT_OK = '''def key_slot(key):
    start = key.find("{")
    if start != -1:
        end = key.find("}", start + 1)
        if end != -1 and end != start + 1:
            key = key[start + 1:end]
    crc = 0
    for byte in key.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc % 16384
'''

PROBLEMS = [
dict(
    id="redis-hyperloglog",
    title="A Toy HyperLogLog Cardinality Estimator",
    difficulty="Hard",
    pattern="Probabilistic structures",
    kind="function",
    entry="hll_estimate",
    compare="float",
    tolerance=1e-6,
    description=r"""
Implement the estimator behind `PFADD` / `PFCOUNT` in a small, fully specified form.

`hll_estimate(items, b)` receives a list of strings (duplicates allowed) and the number of index bits `b`
(`4 <= b <= 8`), and returns the estimated number of **distinct** strings as a float.

1. **Hash** each string with 32-bit FNV-1a over its UTF-8 bytes: start with `h = 2166136261`; for each byte,
   `h = ((h XOR byte) * 16777619) mod 2^32`.
2. Let `m = 2^b` registers, all 0. The **top `b` bits** of `h` choose the register. The remaining `32 - b` bits
   form `rest`. The **rank** is the position of the first 1-bit of `rest` counted from the left starting at 1
   (so `rank = (32 - b) - bit_length(rest) + 1`; if `rest` is 0 the rank is `32 - b + 1`).
   Set `register = max(register, rank)`.
3. Raw estimate: `E = alpha * m^2 / sum(2^(-register))` with `alpha = 0.673` for m = 16, `0.697` for m = 32,
   `0.709` for m = 64, and `0.7213 / (1 + 1.079 / m)` otherwise.
4. Small-range correction: if `E <= 2.5 * m` and `V > 0` registers are still 0, return `m * ln(m / V)`.
   Otherwise return `E`.

**Example:** `hll_estimate([], 4)` → `0.0` (all 16 registers are 0, so `16 * ln(16/16)`)
""",
    starter='''def hll_estimate(items: List[str], b: int) -> float:
    pass
''',
    solution=_HLL_OK % "estimate <= 2.5 * m and zeros > 0",
    tests=[
        [[], 4],
        [["a"], 4],
        [["a", "a", "a", "a"], 4],
        [["a", "b", "c"], 5],
        [["user-%d" % i for i in range(10)], 4],
        [["user-%d" % i for i in range(50)], 4],
        [["user-%d" % i for i in range(50)] * 3, 4],
        [["user-%d" % i for i in range(300)], 6],
        [["v%d" % i for i in range(2000)], 8],
        [["v%d" % i for i in range(2000)], 4],
        [["k%d" % _rng.randint(0, 400) for _ in range(3000)], 7],
        [["é%d" % i for i in range(120)] + ["日本%d" % i for i in range(120)], 6],
        [["x" * i for i in range(1, 700)], 5],
    ],
    examples=2,
    wrong_solutions=[
        _HLL_OK % "False",
        _HLL_OK.replace("index = h >> width", "index = h & (m - 1)").replace(
            "rest = h & ((1 << width) - 1)", "rest = h >> b") % "estimate <= 2.5 * m and zeros > 0",
        '''def hll_estimate(items, b):
    return float(len(set(items)))
''',
    ],
    guide=dict(
        prereqs="Bit operations (`>>`, `&`, `int.bit_length`). The HyperLogLog part of *Modern Redis: HyperLogLog, bitmaps and geospatial indexes*.",
        intuition="A hash turns each item into 32 random-looking bits, and the same item always gives the same bits, so duplicates change nothing. Seeing a hash that starts with many zeros is rare - about one in 2^k for k zeros - so the longest run of leading zeros hints at how many distinct items there were. One such observation is noisy, so the first `b` bits split items into `m` groups, each keeping its own maximum, and the estimates are combined with a harmonic mean.",
        hints=[
            "Write the hash first and check it: FNV-1a of the empty string is 2166136261.",
            "`index = h >> (32 - b)`; `rest = h & ((1 << (32 - b)) - 1)`; `rank = (32 - b) - rest.bit_length() + 1`.",
            "Compute the raw estimate, then count zero registers and apply `m * math.log(m / zeros)` only when the raw estimate is at most `2.5 * m` and at least one register is zero.",
        ],
        brute_force="`len(set(items))` is exact and uses memory proportional to the number of distinct items. The point of HyperLogLog is to use a fixed `m` small registers instead - 12 KB in Redis for any count.",
        approach="""1. Hash each item. 2. Split the hash into register index and remainder. 3. Update the register with the rank. 4. Combine.

**Dry run for an empty list, b = 4:** all 16 registers are 0. The sum of `2^-0` over 16 registers is 16, so E = 0.673 × 256 / 16 = 10.768. That is <= 2.5 × 16 = 40 and V = 16 registers are zero, so the result is 16 × ln(16/16) = 0.0. With one item, one register becomes non-zero, V = 15, and the result is 16 × ln(16/15) ≈ 1.03.""",
        complexity="O(total bytes of all items) time; O(2^b) space regardless of how many items there are.",
        pitfalls="Forgetting to mask to 32 bits after the multiplication. Using the low bits for the index when the specification says the top bits. Off-by-one in the rank (it starts at 1). Skipping the small-range correction, which makes small counts badly wrong. Dividing by zero zero-registers.",
        follow_up="Implement `merge` (register-wise maximum) and check that the estimate of a union does not double-count shared items. Measure the error for b = 4..14 and compare with 1.04 / sqrt(m).",
    ),
),
dict(
    id="redis-bitmap-dau",
    title="Daily Active Users with Bitmaps",
    difficulty="Medium",
    pattern="Bitmaps",
    kind="class",
    entry="ActivityBitmap",
    description=r"""
Track which users were active on which day with one bitmap per day, as `SETBIT`, `GETBIT`, `BITCOUNT` and
`BITOP` do. User ids are non-negative integers; days are strings.

- `mark(day, user_id)` - set the user's bit for that day. Returns the bit's **previous** value (`0` or `1`).
- `is_active(day, user_id)` - `1` or `0` (unknown days and ids beyond the bitmap are `0`).
- `count(day)` - number of active users that day.
- `active_all(days)` - number of users active on **every** listed day (`BITOP AND`). `days` is non-empty.
- `active_any(days)` - number of users active on **at least one** listed day (`BITOP OR`).
- `size_bytes(day)` - bytes the bitmap occupies: `highest marked id // 8 + 1`, or `0` if nothing was marked.

**Example:** `mark("mon",9)` → `0`, `mark("mon",9)` → `1`, `mark("mon",2)`, `mark("tue",9)`:
`count("mon")` → `2`, `active_all(["mon","tue"])` → `1`, `active_any(["mon","tue"])` → `2`, `size_bytes("mon")` → `2`
""",
    starter='''class ActivityBitmap:
    def __init__(self):
        pass

    def mark(self, day: str, user_id: int) -> int:
        pass

    def is_active(self, day: str, user_id: int) -> int:
        pass

    def count(self, day: str) -> int:
        pass

    def active_all(self, days: List[str]) -> int:
        pass

    def active_any(self, days: List[str]) -> int:
        pass

    def size_bytes(self, day: str) -> int:
        pass
''',
    solution='''class ActivityBitmap:
    def __init__(self):
        self.bits = {}          # day -> Python int used as a bit set

    def mark(self, day, user_id):
        old = (self.bits.get(day, 0) >> user_id) & 1
        self.bits[day] = self.bits.get(day, 0) | (1 << user_id)
        return old

    def is_active(self, day, user_id):
        return (self.bits.get(day, 0) >> user_id) & 1

    def count(self, day):
        return bin(self.bits.get(day, 0)).count("1")

    def active_all(self, days):
        acc = self.bits.get(days[0], 0)
        for d in days[1:]:
            acc &= self.bits.get(d, 0)
        return bin(acc).count("1")

    def active_any(self, days):
        acc = 0
        for d in days:
            acc |= self.bits.get(d, 0)
        return bin(acc).count("1")

    def size_bytes(self, day):
        b = self.bits.get(day, 0)
        return 0 if b == 0 else (b.bit_length() - 1) // 8 + 1
''',
    tests=[
        [["ActivityBitmap", "mark", "mark", "mark", "mark", "count", "active_all", "active_any", "size_bytes"],
         [[], ["mon", 9], ["mon", 9], ["mon", 2], ["tue", 9], ["mon"], [["mon", "tue"]], [["mon", "tue"]], ["mon"]]],
        [["ActivityBitmap", "is_active", "count", "size_bytes", "active_all", "active_any"],
         [[], ["mon", 5], ["mon"], ["mon"], [["mon"]], [["mon", "tue"]]]],
        [["ActivityBitmap", "mark", "size_bytes", "mark", "size_bytes", "mark", "size_bytes", "mark", "size_bytes"],
         [[], ["d", 0], ["d"], ["d", 7], ["d"], ["d", 8], ["d"], ["d", 5120], ["d"]]],
        [["ActivityBitmap", "mark", "mark", "mark", "active_all", "active_all", "active_any"],
         [[], ["a", 1], ["b", 1], ["c", 2], [["a", "b", "c"]], [["a", "b"]], [["a", "b", "c"]]]],
        [["ActivityBitmap", "mark", "mark", "active_all", "active_all", "is_active", "is_active"],
         [[], ["a", 3], ["a", 4], [["a", "nope"]], [["a", "a"]], ["a", 4], ["a", 99999]]],
    ] + [_seq(s, 50, "ActivityBitmap", [], _bitmap_step) for s in range(1, 8)],
    examples=2,
    wrong_solutions=[
        '''class ActivityBitmap:
    def __init__(self): self.sets = {}
    def mark(self, day, user_id):
        s = self.sets.setdefault(day, set()); old = int(user_id in s); s.add(user_id); return old
    def is_active(self, day, user_id): return int(user_id in self.sets.get(day, set()))
    def count(self, day): return len(self.sets.get(day, set()))
    def active_all(self, days):                       # bug: union instead of intersection
        return len(set().union(*[self.sets.get(d, set()) for d in days]))
    def active_any(self, days): return len(set().union(*[self.sets.get(d, set()) for d in days]))
    def size_bytes(self, day):
        s = self.sets.get(day, set()); return max(s) // 8 + 1 if s else 0
''',
        '''class ActivityBitmap:
    def __init__(self): self.sets = {}
    def mark(self, day, user_id):
        s = self.sets.setdefault(day, set()); old = int(user_id in s); s.add(user_id); return old
    def is_active(self, day, user_id): return int(user_id in self.sets.get(day, set()))
    def count(self, day): return len(self.sets.get(day, set()))
    def active_all(self, days):
        return len(set.intersection(*[self.sets.get(d, set()) for d in days]))
    def active_any(self, days): return len(set().union(*[self.sets.get(d, set()) for d in days]))
    def size_bytes(self, day):                        # bug: size by number of users, not by highest id
        s = self.sets.get(day, set()); return (len(s) + 7) // 8
''',
    ],
    guide=dict(
        prereqs="Bit operations. The bitmap part of *Modern Redis: HyperLogLog, bitmaps and geospatial indexes*.",
        intuition="Give every user one position in a row of bits; a 1 means 'was active'. Counting users is counting 1-bits, 'active on both days' is a bitwise AND of two rows, and 'active on either' is an OR. A Python integer of unlimited size works as such a row: bit `i` is `(x >> i) & 1`.",
        hints=[
            "Store one integer per day. Set a bit with `x | (1 << user_id)`.",
            "Read the old bit *before* setting it, so `mark` can return the previous value.",
            "The size in bytes depends on the highest set bit: `(x.bit_length() - 1) // 8 + 1`.",
        ],
        brute_force="Keep a Python `set` of ids per day. It gives the same counts, but each id costs dozens of bytes instead of one bit; ten million users are hundreds of megabytes instead of 1.25 MB.",
        approach="""**Dry run:** `mark("mon",9)` → old bit 0, mon = 1<<9. Again → old bit 1. `mark("mon",2)` → mon has bits 2 and 9. `mark("tue",9)`. `count("mon")` → 2. AND of mon and tue → only bit 9 → 1. OR → bits 2 and 9 → 2. Highest bit of mon is 9 → 9 // 8 + 1 = 2 bytes.""",
        complexity="`mark` and `is_active` are O(1) conceptually (Python copies the integer, so O(size) here). Counting and combining are O(size of the bitmap in bytes), as with `BITCOUNT` and `BITOP`.",
        pitfalls="Returning the new bit from `mark`. Using OR where AND is required. Treating a missing day as 'everyone' in an AND instead of 'no one'. Computing the size from the number of users instead of the highest id - the reason bitmaps are a poor fit for sparse ids.",
        follow_up="Compute 7-day retention: users active on day 1 and on day 8. How large is the bitmap if only user 4,000,000,000 is active?",
    ),
),
dict(
    id="redis-cluster-slot",
    title="CRC16 Hash Slot of a Cluster Key",
    difficulty="Medium",
    pattern="Scaling",
    kind="function",
    entry="key_slot",
    description=r"""
Compute the Redis Cluster hash slot of a key, exactly as `CLUSTER KEYSLOT` does.

1. **Hash tag.** Find the first `{` in the key. If there is a `}` somewhere **after** it and at least one
   character lies between them, hash only the text between that `{` and the **first** `}` after it. In every
   other case (no `{`, no later `}`, or nothing between them) hash the whole key.
2. **CRC16** (the XMODEM variant) over the UTF-8 bytes of the chosen text: start with `crc = 0`; for each byte
   do `crc = crc XOR (byte << 8)`, then eight times: if the top bit (`0x8000`) is set,
   `crc = ((crc << 1) XOR 0x1021) AND 0xFFFF`, otherwise `crc = (crc << 1) AND 0xFFFF`.
3. The slot is `crc mod 16384`.

**Examples:** `key_slot("123456789")` → `12739`; `key_slot("foo")` → `12182`;
`key_slot("{user:41}:home")` equals `key_slot("user:41")` → `3691`; `key_slot("foo{}bar")` hashes the whole key
""",
    starter='''def key_slot(key: str) -> int:
    pass
''',
    solution=_SLOT_OK,
    tests=[
        ["123456789"], ["foo"], ["{user:41}:home"], ["user:41"], ["foo{}bar"], [""], ["a{b}{c}"], ["{{x}}y"],
        ["foo{bar"], ["foo}bar{baz"], ["}{"], ["{}{tag}"], ["x{tag}y{other}"], ["日本語{キー}"], ["{a}"],
    ],
    examples=3,
    wrong_solutions=[
        '''def key_slot(key):
    crc = 0                                           # bug: hash tags ignored
    for byte in key.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc % 16384
''',
        _SLOT_OK.replace('end = key.find("}", start + 1)', 'end = key.rfind("}")'),
        _SLOT_OK.replace("if end != -1 and end != start + 1:", "if end != -1:"),
        _SLOT_OK.replace("% 16384", "% 16383"),
    ],
    guide=dict(
        prereqs="Bit shifts and XOR. The slot sections of *Modern Redis: Sentinel and Redis Cluster* and hash tags in *Scaling Redis: complex queries across shards*.",
        intuition="Two independent steps. First decide *which text* is hashed - normally the whole key, but only the tag when the key contains a non-empty `{...}`. That rule is what lets related keys land on the same server. Then compute a checksum of that text and reduce it to one of 16,384 slots. CRC16 is a shift-and-XOR loop processed one bit at a time.",
        hints=[
            "`start = key.find(\"{\")`, then `end = key.find(\"}\", start + 1)`. Use the tag only if both exist and `end != start + 1`.",
            "Work on bytes (`key.encode(\"utf-8\")`), not characters.",
            "Check your CRC against the standard test value: the bytes of `\"123456789\"` give `0x31C3` = 12739.",
        ],
        brute_force="There is nothing slower to fall back on, but a common shortcut is a 256-entry lookup table that processes one byte per step instead of one bit; it gives the same result faster.",
        approach="""**Dry run of the tag rule:** `{user:41}:home` → first `{` at 0, first `}` after it at 8, non-empty → hash `user:41`. `foo{}bar` → `}` immediately follows `{` → whole key. `a{b}{c}` → only the first tag, `b`. `{{x}}y` → from the first `{` to the first `}` → `{x`. `foo{bar` → no `}` → whole key. `}{` → the only `}` is before the `{` → whole key.

**CRC step for one byte:** XOR the byte into the top 8 bits, then shift left 8 times, XOR-ing with 0x1021 whenever a 1 falls off the top.""",
        complexity="O(length of the key) time, O(1) space.",
        pitfalls="Using the last `}` instead of the first one after the `{`. Accepting an empty tag. Hashing characters instead of UTF-8 bytes. Forgetting the `& 0xFFFF` mask (Python integers do not overflow). Taking the result modulo 16383.",
        follow_up="Given a slot map of ranges per node, write `node_for(key)`. Then generate a key whose tag makes it land in a chosen slot.",
    ),
),
dict(
    id="redis-consistent-hash",
    title="Consistent Hashing of Keys to Shards",
    difficulty="Medium",
    pattern="Scaling",
    kind="class",
    entry="HashRing",
    description=r"""
Implement a consistent-hash ring with virtual nodes, the classic way to spread keys over cache servers so that
adding or removing a server moves only a small share of the keys.

Use this hash for everything: **32-bit FNV-1a** over UTF-8 bytes - start with `h = 2166136261`; for each byte
`h = ((h XOR byte) * 16777619) mod 2^32`.

`HashRing(replicas)`:

- `add_node(node)` - place the node at `replicas` points: `hash(node + "#" + str(i))` for `i` in
  `0 .. replicas-1`. Adding a node that is already present changes nothing. Returns the number of points on the ring.
- `remove_node(node)` - remove all its points (no effect if absent). Returns the number of points on the ring.
- `get_node(key)` - the owner is the node of the first point, in ascending order of `(position, node)`, whose
  position is `>= hash(key)`; if there is none, wrap around to the first point of the ring. Returns `None`
  when the ring is empty.
- `distribution(keys)` - `[[node, count], ...]` for the nodes that own at least one of the given keys, sorted
  by node name.

**Example:** with one node `"A"`, `get_node` returns `"A"` for every key; after `remove_node("A")` it returns `None`.
""",
    starter='''class HashRing:
    def __init__(self, replicas: int):
        pass

    def add_node(self, node: str) -> int:
        pass

    def remove_node(self, node: str) -> int:
        pass

    def get_node(self, key: str):
        pass

    def distribution(self, keys: List[str]) -> List[list]:
        pass
''',
    solution='''class HashRing:
    def __init__(self, replicas):
        self.replicas = replicas
        self.ring = []            # sorted list of (position, node)
        self.nodes = set()

    @staticmethod
    def _hash(text):
        h = 2166136261
        for byte in text.encode("utf-8"):
            h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
        return h

    def add_node(self, node):
        if node not in self.nodes:
            self.nodes.add(node)
            for i in range(self.replicas):
                bisect.insort(self.ring, (self._hash(node + "#" + str(i)), node))
        return len(self.ring)

    def remove_node(self, node):
        if node in self.nodes:
            self.nodes.remove(node)
            self.ring = [p for p in self.ring if p[1] != node]
        return len(self.ring)

    def get_node(self, key):
        if not self.ring:
            return None
        i = bisect.bisect_left(self.ring, (self._hash(key), ""))
        return self.ring[i % len(self.ring)][1]

    def distribution(self, keys):
        counts = {}
        for k in keys:
            n = self.get_node(k)
            if n is not None:
                counts[n] = counts.get(n, 0) + 1
        return [[n, counts[n]] for n in sorted(counts)]
''',
    tests=[
        [["HashRing", "get_node", "add_node", "get_node", "get_node", "remove_node", "get_node"],
         [[3], ["k"], ["A"], ["k"], ["other"], ["A"], ["k"]]],
        [["HashRing", "add_node", "add_node", "add_node", "remove_node", "remove_node", "distribution"],
         [[4], ["A"], ["A"], ["B"], ["C"], ["A"], [["k1", "k2", "k3"]]]],
        [["HashRing", "add_node", "add_node", "add_node", "distribution", "get_node", "get_node", "get_node"],
         [[50], ["A"], ["B"], ["C"], [["user:%d" % i for i in range(300)]], ["user:1"], ["user:2"], ["user:3"]]],
        [["HashRing", "add_node", "add_node", "add_node", "distribution", "add_node", "distribution"],
         [[100], ["A"], ["B"], ["C"], [["k%d" % i for i in range(500)]], ["D"], [["k%d" % i for i in range(500)]]]],
        [["HashRing", "add_node", "add_node", "distribution", "remove_node", "distribution", "distribution"],
         [[1], ["A"], ["B"], [["k%d" % i for i in range(200)]], ["B"], [["k%d" % i for i in range(200)]], [[]]]],
        [["HashRing", "add_node", "add_node", "add_node", "add_node", "distribution"],
         [[2], ["n1"], ["n2"], ["n3"], ["n4"], [["item:%d" % i for i in range(400)]]]],
    ] + [_seq(s, 40, "HashRing", [r], _ring_step) for s, r in [(11, 1), (12, 3), (13, 8), (14, 20), (15, 2), (16, 5)]],
    examples=2,
    wrong_solutions=[
        '''class HashRing:
    def __init__(self, replicas): self.nodes = []
    @staticmethod
    def _hash(text):
        h = 2166136261
        for byte in text.encode("utf-8"): h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
        return h
    def add_node(self, node):
        if node not in self.nodes: self.nodes.append(node); self.nodes.sort()
        return len(self.nodes)
    def remove_node(self, node):
        if node in self.nodes: self.nodes.remove(node)
        return len(self.nodes)
    def get_node(self, key):                          # bug: hash mod N, not a ring
        return self.nodes[self._hash(key) % len(self.nodes)] if self.nodes else None
    def distribution(self, keys):
        c = {}
        for k in keys:
            n = self.get_node(k)
            if n is not None: c[n] = c.get(n, 0) + 1
        return [[n, c[n]] for n in sorted(c)]
''',
        '''class HashRing:
    def __init__(self, replicas): self.replicas, self.ring, self.nodes = replicas, [], set()
    @staticmethod
    def _hash(text):
        h = 2166136261
        for byte in text.encode("utf-8"): h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
        return h
    def add_node(self, node):
        if node not in self.nodes:
            self.nodes.add(node)
            for i in range(self.replicas): bisect.insort(self.ring, (self._hash(node + "#" + str(i)), node))
        return len(self.ring)
    def remove_node(self, node):
        if node in self.nodes: self.nodes.remove(node); self.ring = [p for p in self.ring if p[1] != node]
        return len(self.ring)
    def get_node(self, key):
        if not self.ring: return None
        i = bisect.bisect_left(self.ring, (self._hash(key), ""))
        return self.ring[i - 1][1]                    # bug: walks anticlockwise
    def distribution(self, keys):
        c = {}
        for k in keys:
            n = self.get_node(k)
            if n is not None: c[n] = c.get(n, 0) + 1
        return [[n, c[n]] for n in sorted(c)]
''',
    ],
    guide=dict(
        prereqs="`bisect`. The consistent-hashing section of *Scaling Redis: more reads, more writes, more memory*.",
        intuition="Imagine all possible hash values arranged on a circle. Servers are dropped onto the circle at pseudo-random positions; a key belongs to the first server found walking clockwise from the key's own position. Adding a server only captures the keys in the arc just before it, so most keys stay where they were. Placing each server at many points ('virtual nodes') evens out the arc lengths.",
        hints=[
            "Keep a sorted list of `(position, node)` tuples; insert with `bisect.insort`.",
            "Lookup: `i = bisect_left(ring, (hash(key), \"\"))`, then take `ring[i % len(ring)]` - the modulo is the wrap-around.",
            "Track the set of node names so adding twice or removing an absent node changes nothing.",
        ],
        brute_force="`hash(key) % number_of_nodes`. It balances well and is one line - and remaps about (N-1)/N of all keys whenever N changes.",
        approach="""**Dry run idea (positions made small for illustration):** ring points at 10 (A), 40 (B), 70 (A), 90 (C). A key hashing to 45 walks clockwise to 70 → A. A key hashing to 95 finds nothing beyond it and wraps to 10 → A. Adding D at 50 changes the owner only for keys hashing in (40, 50].

In the tests, the fourth case shows it on real hashes: after adding a fourth node, the counts of A, B and C shrink a little and nothing moves between the old nodes.""",
        complexity="`get_node` O(log P) for P ring points; `add_node` O(R·P) with a list (O(R log P) with a tree); `remove_node` O(P).",
        pitfalls="Forgetting the wrap-around. Walking anticlockwise. Using Python's built-in `hash`, which differs between processes for strings. Adding the same node twice and doubling its share. Too few virtual nodes, giving very uneven loads.",
        follow_up="Measure the fraction of keys that move when a node is added, for 1, 10 and 200 replicas, and compare with `1/N`. Add weights so that a larger server gets more points.",
    ),
),
dict(
    id="redis-inverted-index",
    title="Inverted-Index Search with AND, OR and NOT",
    difficulty="Medium",
    pattern="Search",
    kind="class",
    entry="SearchIndex",
    description=r"""
Build the search index that Redis implements with one set of document ids per word, queried with `SINTER`,
`SUNION` and `SDIFF`.

**Tokenising** (used for documents and for query words): lower-case the text, take every maximal run of the
characters `a-z` and `0-9`, and drop tokens shorter than 2 characters and the stop words
`the, and, of, to, in, a, is`.

- `add(doc_id, text)` - index the document (an integer id). If the id was already indexed, its **old text is
  replaced**. Returns the number of distinct tokens indexed for it.
- `remove(doc_id)` - `1` if the document was indexed, else `0`.
- `search_and(words)` - ascending ids of documents containing **all** the words.
- `search_or(words)` - ascending ids of documents containing **any** of the words.
- `search_not(include, exclude)` - documents containing all of `include` and none of `exclude`.

Each query word is tokenised first; words that tokenise to nothing are ignored. If no usable word remains in
`words` (or in `include`), the result is `[]`.

**Example:** `add(1,"Slow rye bread with honey")` → `5`; `add(2,"Banana bread")` → `2`;
`search_and(["bread","HONEY"])` → `[1]`; `search_or(["rye","banana"])` → `[1,2]`; `search_not(["bread"],["rye"])` → `[2]`
""",
    starter='''class SearchIndex:
    def __init__(self):
        pass

    def add(self, doc_id: int, text: str) -> int:
        pass

    def remove(self, doc_id: int) -> int:
        pass

    def search_and(self, words: List[str]) -> List[int]:
        pass

    def search_or(self, words: List[str]) -> List[int]:
        pass

    def search_not(self, include: List[str], exclude: List[str]) -> List[int]:
        pass
''',
    solution='''class SearchIndex:
    STOP = {"the", "and", "of", "to", "in", "a", "is"}

    def __init__(self):
        self.index = {}       # token -> set of doc ids
        self.docs = {}        # doc id -> set of tokens

    def _tokens(self, text):
        out, cur = set(), []
        for ch in text.lower() + " ":
            if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
                cur.append(ch)
            else:
                word = "".join(cur)
                cur = []
                if len(word) >= 2 and word not in self.STOP:
                    out.add(word)
        return out

    def _words(self, words):
        out = []
        for w in words:
            out.extend(sorted(self._tokens(w)))
        return out

    def add(self, doc_id, text):
        self.remove(doc_id)
        tokens = self._tokens(text)
        self.docs[doc_id] = tokens
        for t in tokens:
            self.index.setdefault(t, set()).add(doc_id)
        return len(tokens)

    def remove(self, doc_id):
        if doc_id not in self.docs:
            return 0
        for t in self.docs.pop(doc_id):
            self.index[t].discard(doc_id)
            if not self.index[t]:
                del self.index[t]
        return 1

    def _all(self, words):
        ws = self._words(words)
        if not ws:
            return set()
        result = set(self.index.get(ws[0], set()))
        for w in ws[1:]:
            result &= self.index.get(w, set())
        return result

    def search_and(self, words):
        return sorted(self._all(words))

    def search_or(self, words):
        result = set()
        for w in self._words(words):
            result |= self.index.get(w, set())
        return sorted(result)

    def search_not(self, include, exclude):
        result = self._all(include)
        for w in self._words(exclude):
            result -= self.index.get(w, set())
        return sorted(result)
''',
    tests=[
        [["SearchIndex", "add", "add", "search_and", "search_or", "search_not"],
         [[], [1, "Slow rye bread with honey"], [2, "Banana bread"], [["bread", "HONEY"]], [["rye", "banana"]], [["bread"], ["rye"]]]],
        [["SearchIndex", "search_and", "search_or", "search_not", "remove", "add"],
         [[], [["x"]], [[]], [[], ["x"]], [1], [1, "a I of THE to"]]],
        [["SearchIndex", "add", "add", "search_and", "search_and", "remove", "search_or", "remove"],
         [[], [1, "rye bread"], [1, "honey cake"], [["rye"]], [["honey"]], [1], [["honey", "cake"]], [1]]],
        [["SearchIndex", "add", "add", "add", "search_and", "search_and", "search_and", "search_or"],
         [[], [3, "Tea, honey & lemon-zest!"], [1, "honey-tea"], [2, "TEA"], [["tea", "honey"]], [["the", "tea"]],
          [["the", "a"]], [["zest", "nothing"]]]],
        [["SearchIndex", "add", "add", "search_not", "search_not", "search_not", "search_and"],
         [[], [1, "bread 42 x zz"], [2, "bread 7 zz 42"], [["bread"], []], [["bread", "zz"], ["x", "7"]],
          [["bread"], ["42"]], [["rye bread"]]]],
        [["SearchIndex", "add", "add", "add", "search_and", "search_or", "search_not"],
         [[], [10, "bread bread bread"], [2, "Bread"], [7, "breadth"], [["bread"]], [["bread", "breadth"]], [["bread"], ["missing"]]]],
    ] + [_seq(s, 45, "SearchIndex", [], _index_step) for s in range(21, 28)],
    examples=2,
    wrong_solutions=[
        '''class SearchIndex:
    STOP = {"the", "and", "of", "to", "in", "a", "is"}
    def __init__(self): self.index, self.docs = {}, set()
    def _tokens(self, text):
        import re
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 2 and w not in self.STOP}
    def _words(self, words): return [t for w in words for t in sorted(self._tokens(w))]
    def add(self, doc_id, text):                      # bug: old tokens of a re-added document stay indexed
        self.docs.add(doc_id); tokens = self._tokens(text)
        for t in tokens: self.index.setdefault(t, set()).add(doc_id)
        return len(tokens)
    def remove(self, doc_id):
        if doc_id not in self.docs: return 0
        self.docs.discard(doc_id)
        for s in self.index.values(): s.discard(doc_id)
        return 1
    def _all(self, words):
        ws = self._words(words)
        if not ws: return set()
        r = set(self.index.get(ws[0], set()))
        for w in ws[1:]: r &= self.index.get(w, set())
        return r
    def search_and(self, words): return sorted(self._all(words))
    def search_or(self, words):
        r = set()
        for w in self._words(words): r |= self.index.get(w, set())
        return sorted(r)
    def search_not(self, include, exclude):
        r = self._all(include)
        for w in self._words(exclude): r -= self.index.get(w, set())
        return sorted(r)
''',
        '''class SearchIndex:
    STOP = {"the", "and", "of", "to", "in", "a", "is"}
    def __init__(self): self.docs = {}
    def _tokens(self, text):
        import re
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 2 and w not in self.STOP}
    def _words(self, words): return [t for w in words for t in self._tokens(w)]
    def add(self, doc_id, text): self.docs[doc_id] = self._tokens(text); return len(self.docs[doc_id])
    def remove(self, doc_id): return 1 if self.docs.pop(doc_id, None) is not None else 0
    def search_and(self, words):                      # bug: AND behaves like OR
        ws = self._words(words); return sorted(d for d, t in self.docs.items() if any(w in t for w in ws))
    def search_or(self, words):
        ws = self._words(words); return sorted(d for d, t in self.docs.items() if any(w in t for w in ws))
    def search_not(self, include, exclude):
        inc, exc = self._words(include), self._words(exclude)
        return sorted(d for d, t in self.docs.items() if inc and all(w in t for w in inc) and not any(w in t for w in exc))
''',
    ],
    guide=dict(
        prereqs="Python sets. The lesson *Search with Redis: inverted indexes and sorted results*.",
        intuition="Searching every document for a word is slow. Turn the relation around once, at indexing time: for each word keep the set of documents that contain it. A query then never touches documents at all - 'all of these words' is an intersection of sets, 'any of them' a union, 'but not these' a difference. Keeping the reverse map (document → its words) is what makes removal and re-indexing cheap.",
        hints=[
            "Write the tokeniser first and use the same function for documents and for query words.",
            "Keep two maps: `index[word] -> set of ids` and `docs[id] -> set of words`. `add` starts by calling `remove` so old words disappear.",
            "For AND, start from the first word's set (a copy) and intersect with the rest; a word that is not in the index contributes an empty set.",
        ],
        brute_force="Keep only the documents and test each one against the query: O(number of documents × words) per search. The index answers in time proportional to the sizes of the word sets involved.",
        approach="""**Dry run:** `add(1,"Slow rye bread with honey")` → tokens slow, rye, bread, with, honey (5). `add(2,"Banana bread")` → banana, bread. Index: bread → {1,2}, honey → {1}, rye → {1}, banana → {2}, ... `search_and(["bread","HONEY"])` → {1,2} ∩ {1} = [1]. `search_or(["rye","banana"])` → {1} ∪ {2} = [1,2]. `search_not(["bread"],["rye"])` → {1,2} − {1} = [2].""",
        complexity="`add`/`remove` O(tokens in the document). AND is bounded by the smallest set times the number of words; OR and NOT are linear in the sets involved; sorting the result adds O(r log r).",
        pitfalls="Leaving old words indexed when a document is re-added. Returning every document for an empty AND query. Tokenising documents and queries differently (case, punctuation). Mutating the index's own set when intersecting. Treating a stop word in the query as a word no document contains.",
        follow_up="Rank results: store a score per document and return the top k by score, which in Redis is `ZINTERSTORE` with weights. Support synonyms as a union inside an AND.",
    ),
),
dict(
    id="redis-timeline-fanout",
    title="Timeline Fan-out on Write",
    difficulty="Hard",
    pattern="Social feeds",
    kind="class",
    entry="Timeline",
    description=r"""
Implement the heart of a microblog: each user has a **profile** timeline (their own posts) and a **home**
timeline (their own posts plus posts of the users they follow), maintained at write time.

Timelines list post ids **newest first: by timestamp descending, then by post id descending**.

`Timeline(cap)` - a home timeline keeps only its `cap` newest entries; older ones are dropped when it grows
past the cap (profiles are not capped).

- `post(user, post_id, ts)` - a new post (ids are unique integers). It goes into the author's profile and home,
  and into the home of every current follower. Returns the number of home timelines written (followers + 1).
- `follow(a, b)` - `a` starts following `b`. Returns `False` if `a == b` or `a` already follows `b`. Otherwise
  all of `b`'s existing posts are merged into `a`'s home (then the cap is applied) and it returns `True`.
- `unfollow(a, b)` - returns `False` if `a` does not follow `b`; otherwise removes all of `b`'s posts from
  `a`'s home and returns `True`.
- `delete(post_id)` - removes the post from every timeline. Returns `True` if it existed.
- `home(user, n)` / `profile(user, n)` - the first `n` post ids of that timeline.

**Example:** `Timeline(10)`: `post("ann",1,100)` → `1`; `follow("bo","ann")` → `True`; `home("bo",5)` → `[1]`;
`post("ann",2,101)` → `2`; `post("bo",3,101)` → `1`; `home("bo",5)` → `[3,2,1]`; `unfollow("bo","ann")`; `home("bo",5)` → `[3]`
""",
    starter='''class Timeline:
    def __init__(self, cap: int):
        pass

    def post(self, user: str, post_id: int, ts: int) -> int:
        pass

    def follow(self, a: str, b: str) -> bool:
        pass

    def unfollow(self, a: str, b: str) -> bool:
        pass

    def delete(self, post_id: int) -> bool:
        pass

    def home(self, user: str, n: int) -> List[int]:
        pass

    def profile(self, user: str, n: int) -> List[int]:
        pass
''',
    solution='''class Timeline:
    def __init__(self, cap):
        self.cap = cap
        self.posts = {}                                   # post id -> (author, ts)
        self.followers = collections.defaultdict(set)     # user -> who follows them
        self.following = collections.defaultdict(set)
        self.profiles = collections.defaultdict(set)      # user -> post ids
        self.homes = collections.defaultdict(set)

    def _key(self, pid):
        return (self.posts[pid][1], pid)

    def _trim(self, user):
        h = self.homes[user]
        if len(h) > self.cap:
            keep = sorted(h, key=self._key, reverse=True)[:self.cap]
            self.homes[user] = set(keep)

    def post(self, user, post_id, ts):
        self.posts[post_id] = (user, ts)
        self.profiles[user].add(post_id)
        targets = [user] + sorted(self.followers[user])
        for u in targets:
            self.homes[u].add(post_id)
            self._trim(u)
        return len(targets)

    def follow(self, a, b):
        if a == b or b in self.following[a]:
            return False
        self.following[a].add(b)
        self.followers[b].add(a)
        self.homes[a] |= self.profiles[b]
        self._trim(a)
        return True

    def unfollow(self, a, b):
        if b not in self.following[a]:
            return False
        self.following[a].discard(b)
        self.followers[b].discard(a)
        self.homes[a] -= self.profiles[b]
        return True

    def delete(self, post_id):
        if post_id not in self.posts:
            return False
        author = self.posts[post_id][0]
        self.profiles[author].discard(post_id)
        for h in self.homes.values():
            h.discard(post_id)
        del self.posts[post_id]
        return True

    def _newest(self, ids, n):
        return sorted(ids, key=self._key, reverse=True)[:max(n, 0)]

    def home(self, user, n):
        return self._newest(self.homes[user], n)

    def profile(self, user, n):
        return self._newest(self.profiles[user], n)
''',
    tests=[
        [["Timeline", "post", "follow", "home", "post", "post", "home", "unfollow", "home"],
         [[10], ["ann", 1, 100], ["bo", "ann"], ["bo", 5], ["ann", 2, 101], ["bo", 3, 101], ["bo", 5], ["bo", "ann"], ["bo", 5]]],
        [["Timeline", "home", "profile", "follow", "unfollow", "delete", "follow"],
         [[5], ["x", 3], ["x", 3], ["x", "x"], ["x", "y"], [1], ["x", "y"]]],
        [["Timeline", "follow", "follow", "post", "post", "post", "home", "home", "profile", "home"],
         [[2], ["bo", "ann"], ["bo", "ann"], ["ann", 1, 1], ["ann", 2, 2], ["ann", 3, 3], ["bo", 9], ["ann", 9], ["ann", 9], ["bo", 1]]],
        [["Timeline", "post", "post", "post", "follow", "home", "delete", "home", "profile", "delete"],
         [[2], ["ann", 1, 5], ["ann", 2, 6], ["ann", 3, 7], ["bo", "ann"], ["bo", 9], [3], ["bo", 9], ["ann", 9], [3]]],
        [["Timeline", "follow", "follow", "post", "post", "post", "home", "unfollow", "home", "home"],
         [[10], ["cy", "ann"], ["cy", "bo"], ["ann", 1, 7], ["bo", 2, 7], ["cy", 3, 7], ["cy", 9], ["cy", "bo"], ["cy", 9], ["cy", 0]]],
        [["Timeline", "follow", "follow", "post", "post", "home", "home", "home"],
         [[10], ["bo", "ann"], ["cy", "ann"], ["ann", 5, 1], ["bo", 4, 1], ["bo", 9], ["cy", 9], ["ann", 9]]],
    ] + [_seq(s, 45, "Timeline", [c], _tl_step) for s, c in [(31, 3), (32, 5), (33, 2), (34, 10), (35, 4), (36, 3), (37, 6)]],
    examples=2,
    wrong_solutions=[
        '''class Timeline:
    def __init__(self, cap):
        self.cap, self.posts = cap, {}
        self.followers, self.following = collections.defaultdict(set), collections.defaultdict(set)
        self.profiles, self.homes = collections.defaultdict(set), collections.defaultdict(set)
    def _key(self, pid): return (self.posts[pid][1], pid)
    def _trim(self, u):
        if len(self.homes[u]) > self.cap:
            self.homes[u] = set(sorted(self.homes[u], key=self._key, reverse=True)[:self.cap])
    def post(self, user, post_id, ts):
        self.posts[post_id] = (user, ts); self.profiles[user].add(post_id)
        targets = [user] + sorted(self.followers[user])
        for u in targets: self.homes[u].add(post_id); self._trim(u)
        return len(targets)
    def follow(self, a, b):
        if a == b or b in self.following[a]: return False
        self.following[a].add(b); self.followers[b].add(a)    # bug: no backfill of existing posts
        return True
    def unfollow(self, a, b):
        if b not in self.following[a]: return False
        self.following[a].discard(b); self.followers[b].discard(a); self.homes[a] -= self.profiles[b]; return True
    def delete(self, post_id):
        if post_id not in self.posts: return False
        self.profiles[self.posts[post_id][0]].discard(post_id)
        for h in self.homes.values(): h.discard(post_id)
        del self.posts[post_id]; return True
    def home(self, user, n): return sorted(self.homes[user], key=self._key, reverse=True)[:max(n, 0)]
    def profile(self, user, n): return sorted(self.profiles[user], key=self._key, reverse=True)[:max(n, 0)]
''',
        '''class Timeline:
    def __init__(self, cap):
        self.posts = {}
        self.followers, self.following = collections.defaultdict(set), collections.defaultdict(set)
        self.profiles, self.homes = collections.defaultdict(set), collections.defaultdict(set)
    def _key(self, pid): return (self.posts[pid][1], pid)
    def post(self, user, post_id, ts):                        # bug: the cap is never applied
        self.posts[post_id] = (user, ts); self.profiles[user].add(post_id)
        targets = [user] + sorted(self.followers[user])
        for u in targets: self.homes[u].add(post_id)
        return len(targets)
    def follow(self, a, b):
        if a == b or b in self.following[a]: return False
        self.following[a].add(b); self.followers[b].add(a); self.homes[a] |= self.profiles[b]; return True
    def unfollow(self, a, b):
        if b not in self.following[a]: return False
        self.following[a].discard(b); self.followers[b].discard(a); self.homes[a] -= self.profiles[b]; return True
    def delete(self, post_id):
        if post_id not in self.posts: return False
        self.profiles[self.posts[post_id][0]].discard(post_id)
        for h in self.homes.values(): h.discard(post_id)
        del self.posts[post_id]; return True
    def home(self, user, n): return sorted(self.homes[user], key=self._key, reverse=True)[:max(n, 0)]
    def profile(self, user, n): return sorted(self.profiles[user], key=self._key, reverse=True)[:max(n, 0)]
''',
    ],
    guide=dict(
        prereqs="The lessons *Building a social network: users, posts and timelines* and *...following, fan-out, deletion and live streams*.",
        intuition="People read feeds far more often than they post, so do the work at write time: when someone posts, copy the post's id into each follower's home timeline. Reading is then only 'give me the newest n ids'. Three operations must keep the precomputed timelines honest: following (merge in the other user's existing posts), unfollowing (take them out), and deleting (remove the id everywhere). The cap keeps each home timeline bounded.",
        hints=[
            "Store each post's author and timestamp once; timelines hold only ids. Sort by `(ts, post_id)` descending when reading.",
            "Keep both directions of the follow relation: `followers[b]` is needed by `post`, `following[a]` by `follow`/`unfollow`.",
            "Apply the cap after every change that can grow a home timeline: `post` and `follow`.",
        ],
        brute_force="Fan-out on read: store only profiles and build a home timeline on demand by merging the profiles of everyone the user follows. Writes are trivial, but each read costs a merge over all followed users.",
        approach="""**Dry run, cap 10:** `post("ann",1,100)` → ann's profile and home: {1}; returns 1. `follow("bo","ann")` → bo's home gains ann's posts: {1}. `post("ann",2,101)` → homes of ann and bo; returns 2. `post("bo",3,101)` → bo's home {1,2,3}; returns 1. `home("bo",5)`: sort by (ts, id) descending → 3 (101), 2 (101), 1 (100). `unfollow("bo","ann")` removes ann's posts 1 and 2 → [3].""",
        complexity="`post` is O(followers) writes - the fan-out cost, which is why very large accounts are handled differently in real systems. Reads sort a set of at most `cap` ids. `delete` here scans all homes; a real system does that lazily.",
        pitfalls="Forgetting the backfill on follow. Not capping on follow as well as on post. Breaking timestamp ties by insertion order instead of by id. Leaving a deleted post's id in follower timelines. Counting the author twice in the value returned by `post`.",
        follow_up="Switch large accounts to fan-out on read and merge at read time (the hybrid model). Make `delete` lazy: hide the post immediately and filter missing ids when reading.",
    ),
),
dict(
    id="redis-unique-visitors",
    title="Unique Visitors per Time Bucket",
    difficulty="Medium",
    pattern="Counters",
    kind="class",
    entry="VisitorCounter",
    description=r"""
Count distinct visitors per fixed-width time bucket, as you would with one Redis set (or HyperLogLog) per
bucket key and an `EXPIRE` for old buckets.

`VisitorCounter(bucket_seconds)`: the bucket containing timestamp `ts` starts at
`(ts // bucket_seconds) * bucket_seconds`.

- `record(ts, visitor)` - returns `1` if this is the visitor's first visit in that bucket, else `0`.
- `unique(ts)` - number of distinct visitors in the bucket containing `ts`.
- `unique_range(start_ts, end_ts)` - number of distinct visitors across every bucket from the one containing
  `start_ts` to the one containing `end_ts`, inclusive. A visitor seen in several buckets counts **once**.
- `buckets()` - `[[bucket_start, distinct_count], ...]` for the stored buckets, ascending.
- `expire_before(ts)` - delete every bucket that has ended, meaning `bucket_start + bucket_seconds <= ts`.
  Returns how many buckets were deleted.

**Example:** `VisitorCounter(60)`: `record(5,"u1")` → `1`, `record(59,"u1")` → `0`, `record(61,"u1")` → `1`,
`record(70,"u2")` → `1`; `unique(0)` → `1`; `unique_range(0,119)` → `2`; `buckets()` → `[[0,1],[60,2]]`;
`expire_before(60)` → `1`
""",
    starter='''class VisitorCounter:
    def __init__(self, bucket_seconds: int):
        pass

    def record(self, ts: int, visitor: str) -> int:
        pass

    def unique(self, ts: int) -> int:
        pass

    def unique_range(self, start_ts: int, end_ts: int) -> int:
        pass

    def buckets(self) -> List[List[int]]:
        pass

    def expire_before(self, ts: int) -> int:
        pass
''',
    solution='''class VisitorCounter:
    def __init__(self, bucket_seconds):
        self.width = bucket_seconds
        self.seen = {}            # bucket start -> set of visitors

    def _start(self, ts):
        return (ts // self.width) * self.width

    def record(self, ts, visitor):
        s = self.seen.setdefault(self._start(ts), set())
        if visitor in s:
            return 0
        s.add(visitor)
        return 1

    def unique(self, ts):
        return len(self.seen.get(self._start(ts), ()))

    def unique_range(self, start_ts, end_ts):
        lo, hi = self._start(start_ts), self._start(end_ts)
        everyone = set()
        for start, visitors in self.seen.items():
            if lo <= start <= hi:
                everyone |= visitors
        return len(everyone)

    def buckets(self):
        return [[start, len(self.seen[start])] for start in sorted(self.seen)]

    def expire_before(self, ts):
        old = [start for start in self.seen if start + self.width <= ts]
        for start in old:
            del self.seen[start]
        return len(old)
''',
    tests=[
        [["VisitorCounter", "record", "record", "record", "record", "unique", "unique_range", "buckets", "expire_before"],
         [[60], [5, "u1"], [59, "u1"], [61, "u1"], [70, "u2"], [0], [0, 119], [], [60]]],
        [["VisitorCounter", "unique", "unique_range", "buckets", "expire_before"], [[10], [5], [0, 100], [], [1000]]],
        [["VisitorCounter", "record", "record", "record", "unique_range", "unique_range", "unique_range"],
         [[10], [0, "a"], [10, "a"], [20, "b"], [0, 19], [9, 10], [10, 29]]],
        [["VisitorCounter", "record", "record", "expire_before", "expire_before", "expire_before", "buckets", "record", "unique"],
         [[10], [3, "a"], [14, "b"], [9], [10], [19], [], [3, "a"], [3]]],
        [["VisitorCounter", "record", "record", "record", "record", "buckets", "unique", "unique"],
         [[1], [0, "a"], [0, "b"], [1, "a"], [1, "a"], [], [0], [2]]],
        [["VisitorCounter", "record", "record", "record", "unique_range", "expire_before", "unique_range", "buckets"],
         [[100], [99, "a"], [100, "a"], [250, "c"], [0, 299], [200], [0, 299], []]],
    ] + [_seq(s, 50, "VisitorCounter", [w], _vis_step) for s, w in [(41, 10), (42, 60), (43, 5), (44, 30), (45, 1), (46, 20)]],
    examples=2,
    wrong_solutions=[
        '''class VisitorCounter:
    def __init__(self, bucket_seconds): self.width, self.seen = bucket_seconds, {}
    def _start(self, ts): return (ts // self.width) * self.width
    def record(self, ts, visitor):
        s = self.seen.setdefault(self._start(ts), set())
        if visitor in s: return 0
        s.add(visitor); return 1
    def unique(self, ts): return len(self.seen.get(self._start(ts), ()))
    def unique_range(self, start_ts, end_ts):          # bug: adds per-bucket counts
        lo, hi = self._start(start_ts), self._start(end_ts)
        return sum(len(v) for s, v in self.seen.items() if lo <= s <= hi)
    def buckets(self): return [[s, len(self.seen[s])] for s in sorted(self.seen)]
    def expire_before(self, ts):
        old = [s for s in self.seen if s + self.width <= ts]
        for s in old: del self.seen[s]
        return len(old)
''',
        '''class VisitorCounter:
    def __init__(self, bucket_seconds): self.width, self.seen = bucket_seconds, {}
    def _start(self, ts): return (ts // self.width) * self.width
    def record(self, ts, visitor):
        s = self.seen.setdefault(self._start(ts), set())
        if visitor in s: return 0
        s.add(visitor); return 1
    def unique(self, ts): return len(self.seen.get(self._start(ts), ()))
    def unique_range(self, start_ts, end_ts):
        lo, hi = self._start(start_ts), self._start(end_ts)
        everyone = set()
        for s, v in self.seen.items():
            if lo <= s <= hi: everyone |= v
        return len(everyone)
    def buckets(self): return [[s, len(self.seen[s])] for s in sorted(self.seen)]
    def expire_before(self, ts):                       # bug: also deletes the bucket still in progress
        old = [s for s in self.seen if s <= ts]
        for s in old: del self.seen[s]
        return len(old)
''',
    ],
    guide=dict(
        prereqs="Integer division and sets. The time-bucket counters in *Application support: logging, counters and statistics* and unique counting in *Modern Redis: HyperLogLog, bitmaps and geospatial indexes*.",
        intuition="Two ideas combine. **Bucketing**: every timestamp in the same interval maps to the same bucket start, `(ts // width) * width`, which names the key. **Distinctness**: a set per bucket ignores repeat visits, and the reply of the add tells you whether the visitor was new. Distinct counts cannot be added across buckets, because the same person may appear in several - you must take the union first.",
        hints=[
            "Write `_start(ts)` once and use it everywhere.",
            "`record` returns 1 only when the visitor was not yet in that bucket's set - exactly the reply of `SADD`.",
            "For a range, union the sets of all buckets whose start lies between the two bucket starts, then take the size.",
        ],
        brute_force="Store every visit as `(ts, visitor)` in a list and recompute each answer by scanning it: O(visits) per query and unbounded memory.",
        approach="""**Dry run, width 60:** `record(5,"u1")` → bucket 0, new → 1. `record(59,"u1")` → bucket 0 again → 0. `record(61,"u1")` → bucket 60, new there → 1. `record(70,"u2")` → 1. `unique(0)` → 1. `unique_range(0,119)` → buckets 0 and 60 → {u1} ∪ {u1,u2} = 2 (not 1 + 2 = 3). `expire_before(60)`: bucket 0 ended at 60 <= 60 → deleted; bucket 60 ends at 120 → kept.""",
        complexity="`record` and `unique` O(1). `unique_range` is linear in the visitors of the buckets covered. Memory is O(distinct visitors per bucket) - the cost that a HyperLogLog replaces with 12 KB and a small error.",
        pitfalls="Summing bucket counts for a range. Deleting the bucket that is still in progress. Using the raw timestamp as the bucket key. Returning 1 for a repeat visit. Forgetting that timestamps exactly on a boundary belong to the new bucket.",
        follow_up="Replace each set with a HyperLogLog and use `PFMERGE` for ranges: what accuracy and memory do you get for a million visitors per bucket?",
    ),
),
]
