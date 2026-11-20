"""Problems for the replication, sharding and Python/ML modules."""


def _m(name, priority=1, votes=1, up=True, optime=100, arbiter=False):
    return {"name": name, "priority": priority, "votes": votes, "up": up, "optime": optime, "arbiter": arbiter}


def _r(name, state, lag=0, ping=10, tags=None):
    return {"name": name, "state": state, "lag": lag, "ping": ping, "tags": tags or {}}


_SET5 = [_m("a", 2, optime=90), _m("b", 1, optime=100), _m("c", 1, optime=100), _m("d", 1, optime=95), _m("e", 0, optime=100)]

_READERS = [
    _r("p", "PRIMARY", 0, 40, {"dc": "east", "use": "app"}),
    _r("s1", "SECONDARY", 2, 12, {"dc": "east", "use": "app"}),
    _r("s2", "SECONDARY", 95, 5, {"dc": "west", "use": "reports"}),
    _r("s3", "SECONDARY", 8, 26, {"dc": "west", "use": "app"}),
    _r("s4", "SECONDARY", 30, 28, {"dc": "west"}),
    _r("arb", "ARBITER", 0, 1),
    _r("x", "DOWN", 0, 2, {"dc": "east", "use": "app"}),
]

_RANGED = [
    {"min": None, "max": 100, "shard": "sA"},
    {"min": 100, "max": 250, "shard": "sB"},
    {"min": 250, "max": 400, "shard": "sA"},
    {"min": 400, "max": 900, "shard": "sC"},
    {"min": 900, "max": None, "shard": "sB"},
]

_HASHED = [
    {"min": None, "max": 1000000000, "shard": "sA"},
    {"min": 1000000000, "max": 2000000000, "shard": "sB"},
    {"min": 2000000000, "max": 3000000000, "shard": "sC"},
    {"min": 3000000000, "max": None, "shard": "sD"},
]

_OPLOG = [
    {"ts": 1, "op": "i", "o": {"_id": 1, "name": "kettle", "qty": 4}},
    {"ts": 2, "op": "i", "o": {"_id": 2, "name": "mug", "qty": 10}},
    {"ts": 3, "op": "u", "o2": {"_id": 1}, "o": {"$set": {"qty": 3, "low": True}}},
    {"ts": 4, "op": "n", "o": {"msg": "periodic noop"}},
    {"ts": 5, "op": "d", "o": {"_id": 2}},
    {"ts": 6, "op": "u", "o2": {"_id": 2}, "o": {"$set": {"qty": 99}}},
    {"ts": 7, "op": "i", "o": {"_id": 3, "name": "tray", "qty": 1}},
    {"ts": 8, "op": "u", "o2": {"_id": 1}, "o": {"$unset": {"low": True}, "$set": {"qty": 8}}},
    {"ts": 9, "op": "d", "o": {"_id": 7}},
]

_EVENTS = [
    {"token": "t01", "op": "insert", "doc_id": 1},
    {"token": "t02", "op": "insert", "doc_id": 2},
    {"token": "t03", "op": "update", "doc_id": 1},
    {"token": "t05", "op": "delete", "doc_id": 2},
    {"token": "t06", "op": "update", "doc_id": 1},
    {"token": "t08", "op": "insert", "doc_id": 3},
    {"token": "t09", "op": "replace", "doc_id": 3},
    {"token": "t12", "op": "update", "doc_id": 3},
]

PROBLEMS = [
dict(
    id="mongo-election-winner",
    title="Replica Set Election Winner",
    difficulty="Medium",
    pattern="Replication",
    kind="function",
    entry="elect",
    description=r"""
The primary of a replica set has become unreachable. Decide who, if anyone, becomes the new primary under
this simplified model of MongoDB's election protocol.

Each member is a dict:

- `name` (unique string), `priority` (number; 0 means "may never be primary"), `votes` (1 or 0),
- `up` (bool: reachable right now), `optime` (int: position of its last applied oplog entry - bigger is newer).

A member with `priority > 0` always has `votes = 1`.

**Rules.**

1. *Majority.* A candidate needs at least `floor(V / 2) + 1` votes, where `V` is the number of members with
   `votes = 1`, **whether they are up or not**.
2. *Who can stand.* A member that is `up` and has `priority > 0`.
3. *Who votes for whom.* A member votes for a candidate only if the voter is `up`, has `votes = 1`, and the
   candidate's `optime` is **greater than or equal to** the voter's own. A candidate may vote for itself.
4. *Order.* Candidates are tried from the highest `priority` down; equal priorities are tried from the highest
   `optime` down; remaining ties in ascending `name` order. The first candidate reaching a majority wins.

Return the winner's `name`, or `None` if nobody can win.

**Example:** three healthy members `a`, `b`, `c` with equal priority and optimes 100, 100, 98 → `"a"`.

**Example:** five voting members of which only two are up → `None` (2 votes < majority of 3).
""",
    starter='''def elect(members: List[dict]) -> Optional[str]:
    pass
''',
    solution='''def elect(members):
    voters = [m for m in members if m["votes"] == 1]
    need = len(voters) // 2 + 1
    candidates = [m for m in members if m["up"] and m["priority"] > 0]
    candidates.sort(key=lambda m: (-m["priority"], -m["optime"], m["name"]))
    for cand in candidates:
        got = sum(1 for v in voters if v["up"] and cand["optime"] >= v["optime"])
        if got >= need:
            return cand["name"]
    return None
''',
    tests=[
        [[_m("a", optime=100), _m("b", optime=100), _m("c", optime=98)]],
        [[_m("a", up=False), _m("b", up=False), _m("c", up=False), _m("d"), _m("e")]],
        [_SET5],
        [[_m("a", 5, optime=90), _m("b", 1, optime=100), _m("c", 1, optime=100)]],
        [[_m("a", 5, optime=100), _m("b", 1, optime=100), _m("c", 1, optime=100)]],
        [[_m("a", 0, optime=100), _m("b", 0, optime=100), _m("c", 0, optime=100)]],
        [[_m("a", up=False), _m("b", optime=50), _m("arb", 0, optime=0)]],
        [[_m("a", up=False), _m("b", optime=50), _m("arb", 0, optime=0, up=False)]],
        [[_m("a", optime=10), _m("b", optime=10), _m("c", 0, votes=0, optime=99), _m("d", 0, votes=0, optime=99)]],
        [[_m("z", optime=70), _m("y", optime=70), _m("x", optime=70), _m("w", up=False, optime=999)]],
        [[_m("a", 3, optime=80), _m("b", 2, optime=85), _m("c", 1, optime=90), _m("d", 1, optime=90), _m("e", 1, optime=70)]],
        [[_m("solo", optime=1)]],
        [[_m("solo", optime=1, up=False)]],
        [[]],
        [[_m("a", 1, optime=100), _m("b", 1, optime=101, up=False), _m("c", 1, optime=99), _m("d", 2, optime=97),
          _m("e", 0, votes=0), _m("f", 0, votes=0), _m("g", 0, optime=100)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def elect(members):
    up = [m for m in members if m["up"] and m["priority"] > 0]
    if not up:
        return None
    return sorted(up, key=lambda m: (-m["priority"], -m["optime"], m["name"]))[0]["name"]
''',
        '''def elect(members):
    voters = [m for m in members if m["votes"] == 1 and m["up"]]
    need = len(voters) // 2 + 1
    cands = sorted([m for m in members if m["up"] and m["priority"] > 0], key=lambda m: (-m["priority"], -m["optime"], m["name"]))
    for c in cands:
        if sum(1 for v in voters if c["optime"] >= v["optime"]) >= need:
            return c["name"]
    return None
''',
        '''def elect(members):
    voters = [m for m in members if m["votes"] == 1]
    need = len(voters) // 2 + 1
    cands = sorted([m for m in members if m["up"] and m["priority"] > 0], key=lambda m: (-m["optime"], -m["priority"], m["name"]))
    for c in cands:
        if sum(1 for v in voters if v["up"]) >= need:
            return c["name"]
    return None
''',
    ],
    guide=dict(
        prereqs="Lesson *Replica sets, members and elections*.",
        intuition="Two questions decide an election. *Is there a quorum?* - a strict majority of all voting members, "
                  "counted against the configured set and not against whoever happens to be alive; this is what "
                  "prevents two halves of a partitioned network from each electing a primary. *Is the candidate "
                  "fresh enough?* - nobody votes for a candidate that is behind them, so acknowledged-by-majority "
                  "writes cannot be lost. Priority only decides the order in which eligible members get to try.",
        hints=[
            "Compute the majority from every member with `votes == 1`, including the ones that are down.",
            "Sort the candidates with a tuple key: `(-priority, -optime, name)`.",
            "For each candidate count voters that are up and whose optime is not ahead of the candidate's.",
        ],
        brute_force="There is no heavier alternative worth writing; the trap is the opposite one - returning the highest-priority "
                    "live member without counting votes, which elects a primary on the minority side of a partition.",
        approach="""1. `need = V // 2 + 1` over all voting members.
2. Candidates = up and `priority > 0`, ordered by priority, then optime, then name.
3. First candidate whose supporters (up voters with `optime <= candidate optime`) number at least `need` wins.

**Dry run** - members a (priority 2, optime 90), b, c (100), d (95), e (priority 0, 100), all up, 5 voters →
need 3. Candidate a: nobody but a itself is at or behind 90 → 1 vote, fails. Next b (priority 1, optime 100,
name before c): every up voter has optime ≤ 100 → 5 votes → b wins. A high priority does not help a stale member.""",
        complexity="Time O(n log n + c · n) for n members and c candidates; space O(n).",
        pitfalls="- Computing the majority from live members only (split-brain).\n"
                 "- Forgetting that priority-0 members and arbiters still vote.\n"
                 "- Letting non-voting members (`votes = 0`) cast votes or count towards `V`.\n"
                 "- Using strict `>` for the freshness test: members at the same optime do vote for each other.",
        follow_up="Real elections add terms (each member votes once per term), randomised election timeouts, and a priority "
                  "takeover in which a caught-up higher-priority member later calls a new election. Model terms to see why two candidates cannot both win.",
    ),
),
dict(
    id="mongo-majority-ack",
    title="Write Concern: Is the Write Acknowledged?",
    difficulty="Medium",
    pattern="Replication",
    kind="function",
    entry="write_status",
    description=r"""
A client wrote an operation whose oplog position is `optime` and is waiting for write concern `w`.
Given the current state of the replica set, decide whether the wait is over and compute the set's
majority commit point.

Each member: `name`, `votes` (1 or 0), `up` (bool), `arbiter` (bool: votes but stores no data), `optime` (int:
last oplog position it has applied). A member **has the write** when it is `up`, is not an arbiter, and its
`optime >= optime`.

`write_status(members, w, optime)` returns a dict:

- `"majority"`: `floor(V / 2) + 1` where `V` counts every member with `votes = 1` (arbiters and down members included);
- `"acknowledged"`:
  - `w` is an integer → at least `w` members have the write (non-voting data members count; `w = 0` is always true);
  - `w == "majority"` → at least `majority` **voting** members have the write;
- `"commit_point"`: the largest position `T` such that at least `majority` voting, data-bearing, up members
  have `optime >= T`; `None` if there are not that many such members.

**Example:** three data members (all voting, all up) with optimes `[120, 120, 110]`, `w = "majority"`, `optime = 120`
→ `{"majority": 2, "acknowledged": True, "commit_point": 120}`

**Example:** primary + one secondary + one arbiter, secondary down, primary at 50, `w = "majority"`, `optime = 50`
→ `{"majority": 2, "acknowledged": False, "commit_point": None}` - the arbiter cannot acknowledge data.
""",
    starter='''def write_status(members: List[dict], w, optime: int) -> dict:
    pass
''',
    solution='''def write_status(members, w, optime):
    voting = [m for m in members if m["votes"] == 1]
    majority = len(voting) // 2 + 1

    def holders(pool):
        return sum(1 for m in pool if m["up"] and not m["arbiter"] and m["optime"] >= optime)

    if w == "majority":
        acknowledged = holders(voting) >= majority
    else:
        acknowledged = holders(members) >= w
    positions = sorted((m["optime"] for m in voting if m["up"] and not m["arbiter"]), reverse=True)
    commit_point = positions[majority - 1] if len(positions) >= majority else None
    return {"majority": majority, "acknowledged": acknowledged, "commit_point": commit_point}
''',
    tests=[
        [[_m("a", optime=120), _m("b", optime=120), _m("c", optime=110)], "majority", 120],
        [[_m("p", optime=50), _m("s", optime=50, up=False), _m("arb", 0, optime=0, arbiter=True)], "majority", 50],
        [[_m("a", optime=120), _m("b", optime=120), _m("c", optime=110)], 3, 120],
        [[_m("a", optime=120), _m("b", optime=120), _m("c", optime=110)], 3, 110],
        [[_m("a", optime=120), _m("b", optime=119), _m("c", optime=110)], 1, 120],
        [[_m("a", optime=120), _m("b", optime=119), _m("c", optime=110)], "majority", 120],
        [[_m("a", optime=120), _m("b", optime=119), _m("c", optime=110)], 0, 500],
        [_SET5, "majority", 100],
        [_SET5, "majority", 96],
        [_SET5, 5, 90],
        [[_m("a", optime=30), _m("b", optime=10), _m("c", optime=10), _m("h1", 0, votes=0, optime=30), _m("h2", 0, votes=0, optime=30)], 3, 30],
        [[_m("a", optime=30), _m("b", optime=10), _m("c", optime=10), _m("h1", 0, votes=0, optime=30), _m("h2", 0, votes=0, optime=30)], "majority", 30],
        [[_m("p", optime=50), _m("s", optime=50), _m("arb", 0, optime=0, arbiter=True)], "majority", 50],
        [[_m("p", optime=50), _m("s", optime=40), _m("arb", 0, optime=999, arbiter=True)], 2, 50],
        [[_m("a", optime=7), _m("b", optime=9, up=False), _m("c", optime=9, up=False), _m("d", optime=5), _m("e", optime=6)], "majority", 6],
        [[_m("solo", optime=3)], "majority", 3],
    ],
    examples=2,
    wrong_solutions=[
        '''def write_status(members, w, optime):
    voting = [m for m in members if m["votes"] == 1]
    majority = len(voting) // 2 + 1
    have = sum(1 for m in members if m["up"] and m["optime"] >= optime)
    ack = have >= (majority if w == "majority" else w)
    pos = sorted((m["optime"] for m in voting if m["up"]), reverse=True)
    return {"majority": majority, "acknowledged": ack, "commit_point": pos[majority - 1] if len(pos) >= majority else None}
''',
        '''def write_status(members, w, optime):
    data = [m for m in members if m["up"] and not m["arbiter"]]
    majority = len(data) // 2 + 1
    have = sum(1 for m in data if m["optime"] >= optime)
    ack = have >= (majority if w == "majority" else w)
    pos = sorted((m["optime"] for m in data), reverse=True)
    return {"majority": majority, "acknowledged": ack, "commit_point": pos[majority - 1] if len(pos) >= majority else None}
''',
        '''def write_status(members, w, optime):
    voting = [m for m in members if m["votes"] == 1]
    majority = len(voting) // 2 + 1
    def holders(pool):
        return sum(1 for m in pool if m["up"] and not m["arbiter"] and m["optime"] >= optime)
    ack = holders(voting) >= majority if w == "majority" else holders(members) >= w
    pos = sorted((m["optime"] for m in voting if m["up"] and not m["arbiter"]), reverse=True)
    return {"majority": majority, "acknowledged": ack, "commit_point": pos[0] if len(pos) >= majority else None}
''',
    ],
    guide=dict(
        prereqs="Lesson *The oplog, write concern, read concern and read preference*.",
        intuition="Replication progress is a list of numbers: how far along the oplog each member is. A write concern "
                  "is a question about that list - *how many members have reached position X?* The majority commit "
                  "point turns the question around - *what is the highest position that a majority has reached?* - "
                  "and the answer is an order statistic: sort the positions descending and take the `majority`-th one.",
        hints=[
            "Compute `majority` from the configuration (all voting members), never from who is currently up.",
            "Arbiters vote in elections but hold no data, so they never count as having a write.",
            "Sort the optimes of the voting, data-bearing, up members in descending order; index `majority - 1` is the commit point.",
        ],
        brute_force="Try every distinct optime as a candidate commit point and count the members at or beyond it: O(n²). Sorting once gives it directly.",
        approach="""1. `majority = V // 2 + 1`.
2. `holders(pool)` counts up, data-bearing members at or past `optime`.
3. `w == "majority"` → `holders(voting) >= majority`; integer → `holders(all) >= w`.
4. Commit point = `majority`-th largest optime among voting, data-bearing, up members.

**Dry run** - optimes a=120, b=119, c=110, all voting → majority 2. For a write at 120: only a has it → `w: 1`
is satisfied, `w: "majority"` is not. Sorted positions `[120, 119, 110]`, second entry 119 → everything up to
119 is majority-committed and can never be rolled back; position 120 still can be.""",
        complexity="Time O(n log n) for the sort, space O(n).",
        pitfalls="- Counting arbiters as acknowledgers: a primary-secondary-arbiter set cannot satisfy `w: majority` with one data node down.\n"
                 "- Shrinking the majority when members go down.\n"
                 "- Counting non-voting members towards `majority` writes.\n"
                 "- Returning the *highest* optime as the commit point.",
        follow_up="Add a `wtimeout`: simulate secondaries advancing over time and report whether the acknowledgement arrives before the timeout. "
                  "Note that a timeout does not undo the write - it only stops the wait.",
    ),
),
dict(
    id="mongo-read-preference",
    title="Read Preference Routing",
    difficulty="Medium",
    pattern="Replication",
    kind="function",
    entry="route_read",
    description=r"""
A driver must pick a replica-set member for each read. Implement server selection and return the **sorted
list of names** of the members the driver may choose from (it picks one at random).

Each member: `name`, `state` (`"PRIMARY"`, `"SECONDARY"`, `"ARBITER"` or `"DOWN"`), `lag` (seconds behind the
primary), `ping` (round-trip time in ms), `tags` (dict). At most one member is `PRIMARY`.

`route_read(members, mode, max_staleness, tags)`:

**Eligible secondaries** are members in state `SECONDARY` that (a) have every key/value of `tags` in their own
tags (`{}` matches everyone) and (b) have `lag <= max_staleness` when `max_staleness` is not `None`.

**Latency window.** Given a non-empty pool of members, keep those whose `ping` is at most the pool's smallest
`ping` plus 15 ms.

| mode | result |
|---|---|
| `"primary"` | the primary, or `[]` if there is none (tags and staleness are ignored) |
| `"primaryPreferred"` | the primary if there is one; otherwise the latency window over the eligible secondaries |
| `"secondary"` | the latency window over the eligible secondaries (`[]` if none) |
| `"secondaryPreferred"` | as `"secondary"`; if that is empty, the primary (or `[]`) |
| `"nearest"` | the latency window over the eligible secondaries **plus** the primary if its tags match (`max_staleness` does not apply to the primary) |

**Example:** primary `p` (ping 40), secondaries `s1` (ping 12, lag 2) and `s2` (ping 5, lag 95); mode
`"secondary"`, `max_staleness = None`, `tags = {}` → `["s1", "s2"]`; with `max_staleness = 90` → `["s1"]`.
""",
    starter='''def route_read(members: List[dict], mode: str, max_staleness: Optional[int], tags: dict) -> List[str]:
    pass
''',
    solution='''def route_read(members, mode, max_staleness, tags):
    def tag_ok(m):
        return all(m["tags"].get(k) == v for k, v in tags.items())

    def window(pool):
        if not pool:
            return []
        fastest = min(m["ping"] for m in pool)
        return sorted(m["name"] for m in pool if m["ping"] <= fastest + 15)

    primary = [m for m in members if m["state"] == "PRIMARY"]
    secondaries = [m for m in members if m["state"] == "SECONDARY" and tag_ok(m)
                   and (max_staleness is None or m["lag"] <= max_staleness)]
    names = [m["name"] for m in primary]
    if mode == "primary":
        return names
    if mode == "primaryPreferred":
        return names if names else window(secondaries)
    if mode == "secondary":
        return window(secondaries)
    if mode == "secondaryPreferred":
        return window(secondaries) or names
    return window(secondaries + [m for m in primary if tag_ok(m)])
''',
    tests=[
        [[_r("p", "PRIMARY", 0, 40), _r("s1", "SECONDARY", 2, 12), _r("s2", "SECONDARY", 95, 5)], "secondary", None, {}],
        [[_r("p", "PRIMARY", 0, 40), _r("s1", "SECONDARY", 2, 12), _r("s2", "SECONDARY", 95, 5)], "secondary", 90, {}],
        [_READERS, "primary", 5, {"dc": "west"}],
        [_READERS, "primaryPreferred", None, {"dc": "west"}],
        [_READERS[1:], "primaryPreferred", None, {"dc": "west"}],
        [_READERS[1:], "primary", None, {}],
        [_READERS, "secondary", None, {}],
        [_READERS, "secondary", 90, {}],
        [_READERS, "secondary", 90, {"dc": "west"}],
        [_READERS, "secondary", None, {"use": "app", "dc": "west"}],
        [_READERS, "secondary", 1, {}],
        [_READERS, "secondaryPreferred", 1, {}],
        [_READERS[1:], "secondaryPreferred", 1, {}],
        [_READERS, "nearest", None, {}],
        [_READERS, "nearest", 90, {"use": "app"}],
        [_READERS, "nearest", 0, {"dc": "east"}],
        [_READERS, "nearest", 90, {"dc": "west"}],
        [_READERS, "secondary", None, {"dc": "mars"}],
        [[], "nearest", None, {}],
    ],
    examples=2,
    wrong_solutions=[
        '''def route_read(members, mode, max_staleness, tags):
    def tag_ok(m):
        return all(m["tags"].get(k) == v for k, v in tags.items())
    primary = [m["name"] for m in members if m["state"] == "PRIMARY"]
    secs = sorted(m["name"] for m in members if m["state"] == "SECONDARY" and tag_ok(m) and (max_staleness is None or m["lag"] <= max_staleness))
    if mode == "primary":
        return primary
    if mode == "primaryPreferred":
        return primary or secs
    if mode == "secondary":
        return secs
    if mode == "secondaryPreferred":
        return secs or primary
    return sorted(secs + [m["name"] for m in members if m["state"] == "PRIMARY" and tag_ok(m)])
''',
        '''def route_read(members, mode, max_staleness, tags):
    def tag_ok(m):
        return all(m["tags"].get(k) == v for k, v in tags.items())
    def window(pool):
        if not pool:
            return []
        lo = min(m["ping"] for m in pool)
        return sorted(m["name"] for m in pool if m["ping"] <= lo + 15)
    live = [m for m in members if m["state"] in ("PRIMARY", "SECONDARY")]
    primary = [m["name"] for m in live if m["state"] == "PRIMARY"]
    fresh = [m for m in live if tag_ok(m) and (max_staleness is None or m["lag"] <= max_staleness)]
    secs = [m for m in fresh if m["state"] == "SECONDARY"]
    if mode == "primary":
        return primary
    if mode == "primaryPreferred":
        return primary or window(secs)
    if mode == "secondary":
        return window(secs)
    if mode == "secondaryPreferred":
        return window(secs) or primary
    return window([m for m in members if tag_ok(m)])
''',
    ],
    guide=dict(
        prereqs="Lesson *The oplog, write concern, read concern and read preference* (read preference section).",
        intuition="Server selection is a pipeline of filters: *right role* → *right tags* → *fresh enough* → *close enough*. "
                  "The mode decides which roles are allowed and what the fallback is. The latency window is the "
                  "last step and is relative: it keeps every member within 15 ms of the fastest *remaining* one, "
                  "which spreads load instead of hammering a single nearest node.",
        hints=[
            "Build two lists up front: the primary (zero or one member) and the eligible secondaries after tag and staleness filtering.",
            "Write `window(pool)` once and reuse it; return `[]` for an empty pool before calling `min`.",
            "`secondaryPreferred` is `window(secondaries) or primary`; `nearest` runs the window over secondaries plus a tag-matching primary.",
        ],
        brute_force="Enumerating the five modes with five separate copies of the filtering logic works but hides the shared structure and invites inconsistencies between modes.",
        approach="""1. `primary` = members in state PRIMARY; `secondaries` = SECONDARY members passing tags and staleness.
2. Dispatch on the mode using the table, applying `window` wherever secondaries are involved.

**Dry run** - mode `nearest`, `max_staleness = 90`, tags `{use: app}` on the seven-member fixture: eligible
secondaries are s1 (ping 12) and s3 (ping 26); s2 fails both filters, s4 has no `use` tag. The primary p
(ping 40) matches the tags and joins the pool. Fastest ping 12 → window up to 27 → `["s1", "s3"]`; the primary
is too far away.""",
        complexity="Time O(n · t) for n members and t tag pairs, plus O(n log n) to sort the names; space O(n).",
        pitfalls="- Applying the latency window before the tag and staleness filters (a fast but ineligible member would shrink the window).\n"
                 "- Including arbiters or unreachable members.\n"
                 "- Applying `max_staleness` to the primary, whose lag is zero by definition.\n"
                 "- Falling back to the primary in plain `secondary` mode.",
        follow_up="Real drivers require `maxStalenessSeconds >= 90` and accept a *list* of tag sets tried in order. Add both. "
                  "Then explain why reading from secondaries does not increase write capacity and can return stale data.",
    ),
),
dict(
    id="mongo-oplog-replay",
    title="Oplog Replay Must Be Idempotent",
    difficulty="Medium",
    pattern="Replication",
    kind="function",
    entry="replay",
    description=r"""
A secondary keeps up by applying the primary's **oplog** (operations log). After a restart or during initial
sync it may apply some entries a second time, so every entry must be *idempotent*: applying it twice leaves
the same result as applying it once.

`replay(docs, oplog, from_ts)`: `docs` is the member's current collection (flat documents with unique integer
`_id`). Apply, **in list order**, every oplog entry whose `ts >= from_ts`, then return the collection sorted
by `_id`. Do not mutate the inputs.

| entry | meaning |
|---|---|
| `{"ts", "op": "i", "o": doc}` | insert `doc`; if a document with that `_id` already exists, **replace** it |
| `{"ts", "op": "u", "o2": {"_id": id}, "o": {"$set": {...}, "$unset": {...}}}` | set and/or remove fields of that document (either key may be absent); if the document does not exist, **do nothing** |
| `{"ts", "op": "d", "o": {"_id": id}}` | delete that document; if it does not exist, do nothing |
| `{"ts", "op": "n", ...}` | no-op: ignore |

The list is not necessarily sorted by `ts` (a replayed stretch appears as repeated entries); apply entries
exactly in the order given.

**Example:** docs `[]`, oplog `[insert {_id: 1, qty: 4}, update _id 1 $set {qty: 3}]` (ts 1 and 2), `from_ts = 1`
→ `[{"_id": 1, "qty": 3}]`. With `from_ts = 2` → `[]`: the update finds no document and is skipped.
""",
    starter='''def replay(docs: List[dict], oplog: List[dict], from_ts: int) -> List[dict]:
    pass
''',
    solution='''def replay(docs, oplog, from_ts):
    store = {d["_id"]: dict(d) for d in docs}
    for entry in oplog:
        if entry["ts"] < from_ts:
            continue
        op = entry["op"]
        if op == "i":
            store[entry["o"]["_id"]] = dict(entry["o"])
        elif op == "u":
            doc = store.get(entry["o2"]["_id"])
            if doc is None:
                continue
            for k, v in entry["o"].get("$set", {}).items():
                doc[k] = v
            for k in entry["o"].get("$unset", {}):
                doc.pop(k, None)
        elif op == "d":
            store.pop(entry["o"]["_id"], None)
    return [store[k] for k in sorted(store)]
''',
    tests=[
        [[], [{"ts": 1, "op": "i", "o": {"_id": 1, "qty": 4}}, {"ts": 2, "op": "u", "o2": {"_id": 1}, "o": {"$set": {"qty": 3}}}], 1],
        [[], [{"ts": 1, "op": "i", "o": {"_id": 1, "qty": 4}}, {"ts": 2, "op": "u", "o2": {"_id": 1}, "o": {"$set": {"qty": 3}}}], 2],
        [[], _OPLOG, 0],
        [[], _OPLOG + _OPLOG, 0],
        [[], _OPLOG[:5] + _OPLOG[2:], 0],
        [[{"_id": 1, "name": "kettle", "qty": 3, "low": True}, {"_id": 2, "name": "mug", "qty": 10}], _OPLOG, 5],
        [[{"_id": 1, "name": "old kettle", "qty": 0, "dusty": True}, {"_id": 9, "name": "lamp"}], _OPLOG, 0],
        [[{"_id": 1, "name": "old kettle", "qty": 0, "dusty": True}, {"_id": 9, "name": "lamp"}], _OPLOG, 2],
        [[{"_id": 3, "name": "stale tray", "qty": 50, "extra": 1}], _OPLOG, 7],
        [[{"_id": 5, "a": 1}], _OPLOG, 100],
        [[{"_id": 5, "a": 1}, {"_id": 4, "b": 2}], [], 0],
        [[{"_id": 2, "x": 1}], [{"ts": 3, "op": "u", "o2": {"_id": 2}, "o": {"$unset": {"x": True, "y": True}}},
                                {"ts": 4, "op": "u", "o2": {"_id": 2}, "o": {}}, {"ts": 5, "op": "d", "o": {"_id": 2}},
                                {"ts": 5, "op": "d", "o": {"_id": 2}}, {"ts": 6, "op": "i", "o": {"_id": 2, "z": 0}}], 3],
        [[], [{"ts": i, "op": "i", "o": {"_id": i % 10, "v": i}} for i in range(50)]
         + [{"ts": 50 + i, "op": "u", "o2": {"_id": i % 13}, "o": {"$set": {"w": i}}} for i in range(30)]
         + [{"ts": 90, "op": "d", "o": {"_id": 4}}], 12],
    ],
    examples=2,
    wrong_solutions=[
        '''def replay(docs, oplog, from_ts):
    store = {d["_id"]: dict(d) for d in docs}
    for e in oplog:
        if e["ts"] < from_ts:
            continue
        if e["op"] == "i":
            if e["o"]["_id"] not in store:
                store[e["o"]["_id"]] = dict(e["o"])
        elif e["op"] == "u":
            doc = store.get(e["o2"]["_id"])
            if doc is not None:
                doc.update(e["o"].get("$set", {}))
                for k in e["o"].get("$unset", {}):
                    doc.pop(k, None)
        elif e["op"] == "d":
            store.pop(e["o"]["_id"], None)
    return [store[k] for k in sorted(store)]
''',
        '''def replay(docs, oplog, from_ts):
    store = {d["_id"]: dict(d) for d in docs}
    for e in oplog:
        if e["ts"] < from_ts:
            continue
        if e["op"] == "i":
            store[e["o"]["_id"]] = dict(e["o"])
        elif e["op"] == "u":
            doc = store.setdefault(e["o2"]["_id"], {"_id": e["o2"]["_id"]})
            doc.update(e["o"].get("$set", {}))
            for k in e["o"].get("$unset", {}):
                doc.pop(k, None)
        elif e["op"] == "d":
            store.pop(e["o"]["_id"], None)
    return [store[k] for k in sorted(store)]
''',
        '''def replay(docs, oplog, from_ts):
    store = {d["_id"]: dict(d) for d in docs}
    for e in sorted(oplog, key=lambda e: e["ts"]):
        if e["ts"] <= from_ts:
            continue
        if e["op"] == "i":
            store[e["o"]["_id"]] = dict(e["o"])
        elif e["op"] == "u":
            doc = store.get(e["o2"]["_id"])
            if doc is not None:
                doc.update(e["o"].get("$set", {}))
                for k in e["o"].get("$unset", {}):
                    doc.pop(k, None)
        elif e["op"] == "d":
            store.pop(e["o"]["_id"], None)
    return [store[k] for k in sorted(store)]
''',
    ],
    guide=dict(
        prereqs="Lesson *The oplog, write concern, read concern and read preference* (oplog section).",
        intuition="The oplog does not record what the client *asked for*; it records the *effect* in a form that is safe "
                  "to repeat. `$inc: {qty: -1}` is stored as `$set: {qty: 3}`. Inserting over an existing `_id` "
                  "replaces, updating or deleting something absent is a no-op. With those three conventions, "
                  "applying any suffix of the log - even one that overlaps what was already applied - converges on the same state.",
        hints=[
            "Keep the collection in a dict keyed by `_id` for O(1) access.",
            "Insert is an unconditional assignment; delete is `pop(id, None)`.",
            "For an update, fetch the document first and skip the entry entirely when it is missing.",
        ],
        brute_force="A list scan per entry to find the target document is O(entries × documents). The `_id` dictionary plays the role of the `_id` index every MongoDB collection has.",
        approach="""1. `store = {_id: copy of doc}`.
2. For each entry with `ts >= from_ts`, in list order: `i` → assign; `u` → `$set` then `$unset` on an existing document; `d` → pop.
3. Return the values sorted by `_id`.

**Dry run** - apply the nine-entry log twice in a row to an empty member. First pass ends with `_id 1`
(`qty 8`, no `low`) and `_id 3`. Second pass: the insert of `_id 1` resets it to `qty 4`, the two updates walk
it forward to `qty 8` again; `_id 2` is re-inserted and re-deleted; the update at ts 6 finds nothing. Same final state.""",
        complexity="Time O(d + e + k log k) for d documents, e entries and k surviving documents; space O(d + e).",
        pitfalls="- Treating a duplicate insert as an error or skipping it: the copy already on disk may be stale.\n"
                 "- Turning an update of a missing document into an upsert, which resurrects deleted documents as fragments.\n"
                 "- Sorting the entries by `ts`: the order given is the order of application.\n"
                 "- Using `>` instead of `>=` for `from_ts`.",
        follow_up="Show with a counter-example why logging `$inc` verbatim would break replay. Then read about how initial sync relies on exactly this property: it copies data while writes continue and afterwards replays the oplog over the copy.",
    ),
),
dict(
    id="mongo-shard-routing",
    title="Shard Routing: Targeted or Scatter-Gather",
    difficulty="Medium",
    pattern="Sharding",
    kind="function",
    entry="route",
    description=r"""
Play the role of `mongos`, the query router of a sharded cluster. The collection's shard-key space is cut
into **chunks**; each chunk `{"min": lo, "max": hi, "shard": name}` owns keys `lo <= k < hi`, where
`min = None` means minus infinity and `max = None` plus infinity. The chunks cover the whole space without
overlap. Shard keys are integers.

`route(chunks, strategy, query)` returns `{"shards": [sorted shard names], "type": "targeted" | "scatter-gather"}`.

`strategy` is `"ranged"` (chunks are ranges of the key itself) or `"hashed"` (chunks are ranges of
`h(key) = (key * 2654435761) % 2**32`).

`query` is one of:

| query | ranged | hashed |
|---|---|---|
| `{"eq": k}` | targeted: the shard owning `k` | targeted: the shard owning `h(k)` |
| `{"in": [k1, k2, ...]}` (non-empty) | targeted: the shards owning those keys | targeted: the shards owning their hashes |
| `{"range": [lo, hi]}` (inclusive, `lo <= hi`) | targeted: every shard with a chunk overlapping `[lo, hi]` | scatter-gather: all shards (hashing destroys order) |
| `{}` (no shard key in the query) | scatter-gather: all shards | scatter-gather: all shards |

"All shards" means every shard that owns at least one chunk.

**Example:** chunks `(-inf, 100) → sA`, `[100, 250) → sB`, `[250, +inf) → sA`; ranged; `{"range": [90, 120]}`
→ `{"shards": ["sA", "sB"], "type": "targeted"}`; `{"eq": 250}` → `{"shards": ["sA"], "type": "targeted"}`.
""",
    starter='''def route(chunks: List[dict], strategy: str, query: dict) -> dict:
    pass
''',
    solution='''def route(chunks, strategy, query):
    def position(key):
        return (key * 2654435761) % 2 ** 32 if strategy == "hashed" else key

    def owner(pos):
        for c in chunks:
            if (c["min"] is None or c["min"] <= pos) and (c["max"] is None or pos < c["max"]):
                return c["shard"]

    if "eq" in query:
        return {"shards": [owner(position(query["eq"]))], "type": "targeted"}
    if "in" in query:
        return {"shards": sorted({owner(position(k)) for k in query["in"]}), "type": "targeted"}
    if "range" in query and strategy == "ranged":
        lo, hi = query["range"]
        hit = {c["shard"] for c in chunks
               if (c["max"] is None or lo < c["max"]) and (c["min"] is None or c["min"] <= hi)}
        return {"shards": sorted(hit), "type": "targeted"}
    return {"shards": sorted({c["shard"] for c in chunks}), "type": "scatter-gather"}
''',
    tests=[
        [[{"min": None, "max": 100, "shard": "sA"}, {"min": 100, "max": 250, "shard": "sB"}, {"min": 250, "max": None, "shard": "sA"}], "ranged", {"range": [90, 120]}],
        [[{"min": None, "max": 100, "shard": "sA"}, {"min": 100, "max": 250, "shard": "sB"}, {"min": 250, "max": None, "shard": "sA"}], "ranged", {"eq": 250}],
        [_RANGED, "ranged", {"eq": 99}],
        [_RANGED, "ranged", {"eq": 100}],
        [_RANGED, "ranged", {"eq": -5000}],
        [_RANGED, "ranged", {"eq": 900}],
        [_RANGED, "ranged", {"in": [5, 260, 399]}],
        [_RANGED, "ranged", {"in": [899, 900, 100]}],
        [_RANGED, "ranged", {"range": [250, 399]}],
        [_RANGED, "ranged", {"range": [250, 400]}],
        [_RANGED, "ranged", {"range": [100, 100]}],
        [_RANGED, "ranged", {"range": [-10, 10 ** 6]}],
        [_RANGED, "ranged", {}],
        [_HASHED, "hashed", {"eq": 1}],
        [_HASHED, "hashed", {"eq": 2}],
        [_HASHED, "hashed", {"eq": -7}],
        [_HASHED, "hashed", {"in": [1, 2, 3, 4, 5, 6]}],
        [_HASHED, "hashed", {"in": [10, 10]}],
        [_HASHED, "hashed", {"range": [1, 2]}],
        [_HASHED[:1] + [{"min": 1000000000, "max": None, "shard": "sA"}], "hashed", {}],
    ],
    examples=2,
    wrong_solutions=[
        '''def route(chunks, strategy, query):
    def owner(pos):
        for c in chunks:
            if (c["min"] is None or c["min"] <= pos) and (c["max"] is None or pos < c["max"]):
                return c["shard"]
    if "eq" in query:
        return {"shards": [owner(query["eq"])], "type": "targeted"}
    if "in" in query:
        return {"shards": sorted({owner(k) for k in query["in"]}), "type": "targeted"}
    if "range" in query:
        lo, hi = query["range"]
        return {"shards": sorted({c["shard"] for c in chunks if (c["max"] is None or lo < c["max"]) and (c["min"] is None or c["min"] <= hi)}), "type": "targeted"}
    return {"shards": sorted({c["shard"] for c in chunks}), "type": "scatter-gather"}
''',
        '''def route(chunks, strategy, query):
    def position(key):
        return (key * 2654435761) % 2 ** 32 if strategy == "hashed" else key
    def owner(pos):
        for c in chunks:
            if (c["min"] is None or c["min"] < pos) and (c["max"] is None or pos <= c["max"]):
                return c["shard"]
    if "eq" in query:
        return {"shards": [owner(position(query["eq"]))], "type": "targeted"}
    if "in" in query:
        return {"shards": sorted({owner(position(k)) for k in query["in"]}), "type": "targeted"}
    if "range" in query and strategy == "ranged":
        lo, hi = query["range"]
        return {"shards": sorted({c["shard"] for c in chunks if (c["max"] is None or lo <= c["max"]) and (c["min"] is None or c["min"] <= hi)}), "type": "targeted"}
    return {"shards": sorted({c["shard"] for c in chunks}), "type": "scatter-gather"}
''',
    ],
    guide=dict(
        prereqs="Lessons *Sharded cluster components and query routing* and *Choosing a shard key: ranged, hashed and zoned*.",
        intuition="`mongos` holds a table of chunk boundaries. If the query pins the shard key, the router looks the key "
                  "up in the table and talks to one shard (*targeted*). If the query says nothing about the shard "
                  "key, every shard might hold matches and all must be asked (*scatter-gather*). Hashing scatters "
                  "neighbouring keys across the hash space, so an exact key can still be located, but a key *range* no "
                  "longer corresponds to any range of chunks.",
        hints=[
            "Write `owner(position)` using half-open intervals: `min <= p < max`, with `None` as infinity.",
            "For the hashed strategy, convert a key to its hash before looking up the owner; nothing else changes for `eq` and `in`.",
            "Two intervals `[lo, hi]` and `[min, max)` overlap when `lo < max` and `min <= hi`.",
        ],
        brute_force="For a range, enumerate every integer between `lo` and `hi` and look up its owner. That is O(range width × chunks) "
                    "and useless for wide ranges; interval-overlap arithmetic is O(chunks).",
        approach="""1. `eq` → `[owner(position(k))]`, targeted.
2. `in` → the set of owners, targeted.
3. `range` on a ranged key → shards of all overlapping chunks, targeted. `range` on a hashed key falls through.
4. Everything else → all shards, scatter-gather.

**Dry run** - chunks `(-inf,100)→sA`, `[100,250)→sB`, `[250,400)→sA`, `[400,900)→sC`, `[900,+inf)→sB`; query
`range [250, 400]`: chunk 3 overlaps (250 ≤ 400 and 250 < 400); chunk 4 overlaps because 400 is included
(`min 400 <= hi 400`); chunk 2 does not (`lo 250 < max 250` is false) → `["sA", "sC"]`.""",
        complexity="Time O(c) per looked-up key or range for c chunks (a real router binary-searches the sorted boundaries: O(log c)); space O(s) for the shard set.",
        pitfalls="- Treating a chunk's `max` as inclusive: the boundary key belongs to the *next* chunk.\n"
                 "- Routing a range query on a hashed key as if hashes preserved order.\n"
                 "- Forgetting to hash for `eq` / `in` lookups under the hashed strategy.\n"
                 "- Returning duplicate shard names when two chunks of one shard are hit.",
        follow_up="Add compound shard keys: a query on a *prefix* of the key is still targeted. Then add writes: an insert must carry the full shard key, and a single-document update without it has to be broadcast or rejected depending on the server version.",
    ),
),
dict(
    id="mongo-chunk-balancer",
    title="Chunk Splits and the Balancer",
    difficulty="Hard",
    pattern="Sharding",
    kind="function",
    entry="split_and_balance",
    description=r"""
Simulate the two background mechanisms that keep a sharded collection even: **splitting** chunks that grew
too large and **migrating** chunks from crowded shards to empty ones.

`split_and_balance(shards, chunks, max_size, threshold)`:

- `shards`: list of all shard names (some may own no chunk);
- `chunks`: ordered list of `{"shard": name, "keys": [sorted ints]}`;
- `max_size >= 1`: the largest number of keys a chunk may hold;
- `threshold >= 2`: the balancer acts while the difference in chunk counts is at least this.

**Phase 1 - split.** Process chunks in order. A chunk with more than `max_size` keys is cut in two: the first
`len(keys) // 2` keys and the rest, both on the same shard, taking the original's place in the list in that
order. Keep splitting any piece that is still too large. Count one split for every cut.

**Phase 2 - balance.** Repeat:

1. count chunks per shard (0 for a shard that owns none);
2. `source` = the shard with the most chunks, `target` = the shard with the fewest; break ties by the
   alphabetically smallest name in both cases;
3. if `count[source] - count[target] < threshold`, stop;
4. otherwise move the **first chunk in list order** owned by `source` to `target` (its position in the list
   does not change) and record `[source, target]`.

Return `{"chunks": [...], "splits": n, "migrations": [[source, target], ...]}` with chunks in final list order.

**Example:** shards `["s1", "s2"]`, one chunk on `s1` with keys `1..8`, `max_size = 2`, `threshold = 2` → three
splits give four chunks of two keys on `s1`; two migrations `[["s1", "s2"], ["s1", "s2"]]` leave two chunks each.
""",
    starter='''def split_and_balance(shards: List[str], chunks: List[dict], max_size: int, threshold: int) -> dict:
    pass
''',
    solution='''def split_and_balance(shards, chunks, max_size, threshold):
    def split(keys):
        if len(keys) <= max_size:
            return [keys]
        mid = len(keys) // 2
        return split(keys[:mid]) + split(keys[mid:])

    out, splits = [], 0
    for chunk in chunks:
        parts = split(list(chunk["keys"]))
        splits += len(parts) - 1
        for part in parts:
            out.append({"shard": chunk["shard"], "keys": part})

    migrations = []
    while True:
        counts = {s: 0 for s in shards}
        for chunk in out:
            counts[chunk["shard"]] += 1
        source = min(shards, key=lambda s: (-counts[s], s))
        target = min(shards, key=lambda s: (counts[s], s))
        if counts[source] - counts[target] < threshold:
            break
        for chunk in out:
            if chunk["shard"] == source:
                chunk["shard"] = target
                migrations.append([source, target])
                break
    return {"chunks": out, "splits": splits, "migrations": migrations}
''',
    tests=[
        [["s1", "s2"], [{"shard": "s1", "keys": [1, 2, 3, 4, 5, 6, 7, 8]}], 2, 2],
        [["s1", "s2"], [{"shard": "s1", "keys": [1, 2, 3]}, {"shard": "s2", "keys": [9]}], 5, 2],
        [["s1", "s2", "s3"], [{"shard": "s1", "keys": list(range(10))}], 3, 2],
        [["s1", "s2", "s3"], [{"shard": "s2", "keys": list(range(7))}, {"shard": "s2", "keys": [50]}, {"shard": "s3", "keys": []}], 1, 2],
        [["b", "a", "c"], [{"shard": "c", "keys": [i]} for i in range(9)], 4, 3],
        [["b", "a", "c"], [{"shard": "c", "keys": [i]} for i in range(9)], 4, 8],
        [["x"], [{"shard": "x", "keys": list(range(5))}], 2, 2],
        [["x", "y"], [], 3, 2],
        [["x", "y"], [{"shard": "x", "keys": []}, {"shard": "x", "keys": []}, {"shard": "x", "keys": []}], 1, 2],
        [["n1", "n2", "n3", "n4"], [{"shard": "n1", "keys": list(range(0, 33))}, {"shard": "n3", "keys": list(range(40, 49))}], 4, 2],
        [["n1", "n2", "n3", "n4"], [{"shard": "n%d" % (1 + i % 2), "keys": list(range(i * 10, i * 10 + i))} for i in range(8)], 3, 3],
        [["p", "q"], [{"shard": "p", "keys": [1, 2, 3, 4, 5]}, {"shard": "q", "keys": [6, 7, 8, 9, 10, 11]}], 5, 2],
        [["p", "q", "r"], [{"shard": "q", "keys": list(range(100))}], 7, 2],
    ],
    examples=1,
    wrong_solutions=[
        '''def split_and_balance(shards, chunks, max_size, threshold):
    out, splits = [], 0
    for c in chunks:
        keys = list(c["keys"])
        if len(keys) > max_size:
            mid = len(keys) // 2
            out.append({"shard": c["shard"], "keys": keys[:mid]})
            out.append({"shard": c["shard"], "keys": keys[mid:]})
            splits += 1
        else:
            out.append({"shard": c["shard"], "keys": keys})
    migrations = []
    while True:
        counts = {s: 0 for s in shards}
        for c in out:
            counts[c["shard"]] += 1
        src = min(shards, key=lambda s: (-counts[s], s))
        dst = min(shards, key=lambda s: (counts[s], s))
        if counts[src] - counts[dst] < threshold:
            break
        for c in out:
            if c["shard"] == src:
                c["shard"] = dst
                migrations.append([src, dst])
                break
    return {"chunks": out, "splits": splits, "migrations": migrations}
''',
        '''def split_and_balance(shards, chunks, max_size, threshold):
    def split(keys):
        if len(keys) <= max_size:
            return [keys]
        mid = len(keys) // 2
        return split(keys[:mid]) + split(keys[mid:])
    out, splits = [], 0
    for c in chunks:
        parts = split(list(c["keys"]))
        splits += len(parts) - 1
        out.extend({"shard": c["shard"], "keys": p} for p in parts)
    migrations = []
    while True:
        counts = {}
        for c in out:
            counts[c["shard"]] = counts.get(c["shard"], 0) + 1
        if not counts:
            break
        src = min(counts, key=lambda s: (-counts[s], s))
        dst = min(counts, key=lambda s: (counts[s], s))
        if counts[src] - counts[dst] < threshold:
            break
        for c in out:
            if c["shard"] == src:
                c["shard"] = dst
                migrations.append([src, dst])
                break
    return {"chunks": out, "splits": splits, "migrations": migrations}
''',
        '''def split_and_balance(shards, chunks, max_size, threshold):
    def split(keys):
        if len(keys) <= max_size:
            return [keys]
        mid = len(keys) // 2
        return split(keys[:mid]) + split(keys[mid:])
    out, splits = [], 0
    for c in chunks:
        parts = split(list(c["keys"]))
        splits += len(parts) - 1
        out.extend({"shard": c["shard"], "keys": p} for p in parts)
    migrations = []
    while True:
        counts = {s: 0 for s in shards}
        for c in out:
            counts[c["shard"]] += 1
        src = max(shards, key=lambda s: counts[s])
        dst = min(shards, key=lambda s: counts[s])
        if counts[src] - counts[dst] <= threshold:
            break
        for c in reversed(out):
            if c["shard"] == src:
                c["shard"] = dst
                migrations.append([src, dst])
                break
    return {"chunks": out, "splits": splits, "migrations": migrations}
''',
    ],
    guide=dict(
        prereqs="Lesson *Chunks, the balancer and sharding administration*. Recursion; `min` with a tuple key.",
        intuition="Splitting is cheap bookkeeping - a chunk is a range in a metadata table, and a split inserts one more "
                  "boundary without moving any data. Balancing is the expensive part - whole ranges of documents are "
                  "copied between machines - so it moves one chunk at a time and stops as soon as the cluster is "
                  "*even enough*, which is what the threshold expresses.",
        hints=[
            "Write `split(keys)` recursively: return `[keys]` when small enough, otherwise split both halves and concatenate.",
            "Recount chunks per shard on every round, starting from a zero for every shard in `shards`.",
            "`min(shards, key=lambda s: (-counts[s], s))` finds the fullest shard with the alphabetical tie-break in one expression.",
        ],
        brute_force="Splitting a chunk only once leaves pieces that are still oversized when a chunk is more than twice the limit; the recursion is needed. "
                    "For balancing, recounting every round is O(rounds × chunks), which is fine at this scale; a real balancer keeps running totals.",
        approach="""1. Phase 1: for each chunk, `parts = split(keys)`; add `len(parts) - 1` to the split counter; append the parts in order.
2. Phase 2: loop - count, pick source and target, stop when the gap is below the threshold, otherwise reassign the first chunk of the source.

**Dry run** - one chunk on s1 with keys 1..8, `max_size = 2`: `[1..8]` → `[1..4]` + `[5..8]` → `[1,2] [3,4] [5,6] [7,8]`,
three cuts. Counts s1=4, s2=0, gap 4 ≥ 2 → move `[1,2]` to s2. Counts 3 and 1, gap 2 ≥ 2 → move `[3,4]`. Counts 2
and 2 → stop. Two migrations.""",
        complexity="Splitting is O(k) per chunk of k keys per recursion level, O(k log(k / max_size)) overall. Balancing is O(m · (c + s)) for m migrations, c chunks, s shards.",
        pitfalls="- Splitting each chunk only once.\n"
                 "- Counting only shards that currently own chunks, so an empty new shard never receives anything.\n"
                 "- Using `<=` in the stop test: with a gap equal to the threshold the balancer must still act.\n"
                 "- Reordering the chunk list when a chunk migrates.",
        follow_up="Since MongoDB 6.0 the balancer evens out *data size* per shard rather than chunk counts. Change the cost function to the number of keys per shard and compare the migrations on a skewed input. Also model a *jumbo* chunk: all keys identical, so it cannot be split.",
    ),
),
dict(
    id="mongo-change-stream-resume",
    title="Resume a Change Stream from a Token",
    difficulty="Easy",
    pattern="Change Streams",
    kind="function",
    entry="resume",
    description=r"""
A change stream delivers every insert, update, replace and delete on a collection, each tagged with a
**resume token**. A consumer that stores the token of the last event it processed can crash, restart and
continue exactly where it stopped - as long as that event is still in the server's history (the oplog).

`resume(events, resume_token, ops, limit)`:

- `events`: the history, oldest first; each event is `{"token": str, "op": str, "doc_id": ...}` and tokens are unique;
- `resume_token`: `None` to start from the oldest retained event, otherwise the token of the last event the
  consumer processed;
- `ops`: list of operation types the consumer wants (its `$match` filter); an empty list means all types;
- `limit >= 1`: the maximum number of events to return in this batch.

Return `{"events": [...], "token": t, "error": e}`:

- If `resume_token` is not `None` and no event has that token, the history has been lost: return
  `{"events": [], "token": resume_token, "error": "ChangeStreamHistoryLost"}`.
- Otherwise scan the events strictly after the token (or from the start), keep those whose `op` passes the
  filter, and stop once `limit` events have been collected. `token` is the token of the last returned event,
  or `resume_token` unchanged if none was returned. `error` is `None`.

**Example:** events with tokens `t01` insert, `t02` insert, `t03` update; `resume("t01", ops=[], limit=10)` →
events `t02`, `t03`, token `"t03"`. With `ops = ["update"]` → only `t03`.
""",
    starter='''def resume(events: List[dict], resume_token: Optional[str], ops: List[str], limit: int) -> dict:
    pass
''',
    solution='''def resume(events, resume_token, ops, limit):
    start = 0
    if resume_token is not None:
        tokens = [e["token"] for e in events]
        if resume_token not in tokens:
            return {"events": [], "token": resume_token, "error": "ChangeStreamHistoryLost"}
        start = tokens.index(resume_token) + 1
    batch = []
    for event in events[start:]:
        if len(batch) == limit:
            break
        if ops and event["op"] not in ops:
            continue
        batch.append(event)
    token = batch[-1]["token"] if batch else resume_token
    return {"events": batch, "token": token, "error": None}
''',
    tests=[
        [_EVENTS[:3], "t01", [], 10],
        [_EVENTS[:3], "t01", ["update"], 10],
        [_EVENTS, None, [], 100],
        [_EVENTS, None, [], 3],
        [_EVENTS, "t03", [], 3],
        [_EVENTS, "t08", [], 3],
        [_EVENTS, "t12", [], 3],
        [_EVENTS, "t04", [], 3],
        [_EVENTS, "t00", ["insert"], 3],
        [_EVENTS, None, ["update", "delete"], 2],
        [_EVENTS, "t05", ["update", "delete"], 2],
        [_EVENTS, "t02", ["drop"], 5],
        [_EVENTS, None, ["insert"], 1],
        [[], None, [], 5],
        [[], "t01", [], 5],
        [_EVENTS[3:], "t02", [], 5],
    ],
    examples=2,
    wrong_solutions=[
        '''def resume(events, resume_token, ops, limit):
    rest = [e for e in events if resume_token is None or e["token"] > resume_token]
    batch = [e for e in rest if not ops or e["op"] in ops][:limit]
    return {"events": batch, "token": batch[-1]["token"] if batch else resume_token, "error": None}
''',
        '''def resume(events, resume_token, ops, limit):
    start = 0
    if resume_token is not None:
        tokens = [e["token"] for e in events]
        if resume_token not in tokens:
            return {"events": [], "token": resume_token, "error": "ChangeStreamHistoryLost"}
        start = tokens.index(resume_token)
    batch = [e for e in events[start:start + limit] if not ops or e["op"] in ops]
    return {"events": batch, "token": batch[-1]["token"] if batch else resume_token, "error": None}
''',
    ],
    guide=dict(
        prereqs="Lesson *Change streams and Atlas Vector Search for RAG*.",
        intuition="A resume token is a bookmark into the oplog. Resuming is *find the bookmark, read on from the next "
                  "entry*. If the bookmark's page has already been recycled - the oplog is a fixed-size, circular log - "
                  "the server cannot prove that nothing was missed, so it refuses rather than silently skipping events. "
                  "Persisting the token after each processed event gives at-least-once delivery.",
        hints=[
            "Find the index of the resume token; start reading at the index after it.",
            "Apply the `ops` filter while scanning, and count only the events that pass towards `limit`.",
            "Distinguish *token not found* (an error) from *token found but nothing new* (an empty batch and the same token).",
        ],
        brute_force="Re-reading the whole history and de-duplicating in the consumer works only while the history is small "
                    "and forces every consumer to remember every event it has ever seen.",
        approach="""1. `resume_token is None` → `start = 0`. Otherwise locate it; absent → history-lost result.
2. Walk `events[start:]`; skip filtered-out operations; stop when the batch holds `limit` events.
3. Report the last returned token, or the old one if the batch is empty.

**Dry run** - tokens t01 i, t02 i, t03 u, t05 d, t06 u, t08 i, t09 r, t12 u; `resume("t05", ["update", "delete"], 2)`:
start after t05 → t06 update (kept), t08 insert (skipped), t09 replace (skipped), t12 update (kept) → batch
`[t06, t12]`, token `t12`. `resume("t04", ...)`: no event carries t04 → `ChangeStreamHistoryLost`.""",
        complexity="Time O(n) to locate the token and scan; space O(limit). A server seeks in the oplog by timestamp instead of scanning.",
        pitfalls="- Returning the bookmark event itself again (off by one).\n"
                 "- Slicing `limit` events *before* filtering, which returns short or empty batches while matching events remain.\n"
                 "- Comparing tokens with `>` and silently resuming after a lost token.\n"
                 "- Resetting the token to `None` when a batch is empty, which restarts the stream from the beginning.",
        follow_up="Make processing idempotent so that replaying the last event after a crash between *process* and *save token* is harmless. "
                  "Look at `startAtOperationTime` and `startAfter` and when each is preferable to `resumeAfter`.",
    ),
),
]
