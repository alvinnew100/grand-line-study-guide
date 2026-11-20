"""Problems for modules 9-13: Lamport clocks, 2PC, MapReduce, stream windows, IVF vector search."""
import random as _r

_rng = _r.Random(23)


def _rand_events(n_proc, n):
    """Random but valid event list: every recv follows its send and each message is received at most once."""
    events, sent, mid = [], [], 0
    for _ in range(n):
        p = _rng.randrange(n_proc)
        kind = _rng.choice(["local", "send", "recv"])
        if kind == "recv" and sent:
            m = sent.pop(_rng.randrange(len(sent)))
            events.append(["recv", p, m])
        elif kind == "send":
            mid += 1
            sent.append(mid)
            events.append(["send", p, mid])
        else:
            events.append(["local", p])
    return events


_WORDS = ["log", "page", "index", "shard", "quorum", "leader", "commit", "abort", "stream", "batch", "Log", "PAGE"]


def _rand_docs(n, k):
    return [" ".join(_rng.choice(_WORDS) + _rng.choice(["", ",", ".", "!"]) for _ in range(k)) for _ in range(n)]


def _rand_stream(n, size):
    t, out = 0, []
    for _ in range(n):
        t += _rng.randint(0, size // 2)
        out.append([max(0, t - _rng.choice([0, 0, 0, size, 3 * size])), _rng.choice(["a", "b", "c"])])
    return out


def _rand_vecs(n, d, lo=-10, hi=10):
    return [[_rng.randint(lo, hi) for _ in range(d)] for _ in range(n)]


PROBLEMS = [
dict(
    id="db-lamport-order",
    title="Lamport Timestamps and Total Order",
    difficulty="Medium",
    pattern="Distributed Systems",
    kind="function",
    entry="lamport_order",
    description=r"""
There are `n` processes numbered `0 .. n-1`, each with a Lamport clock starting at 0. `events` lists what
happened, in the order it really happened:

- `["local", p]` - process `p` does some internal work;
- `["send", p, m]` - process `p` sends message `m` (message ids are unique);
- `["recv", p, m]` - process `p` receives message `m` (always after its send).

Clock rules: before a local or send event, the process increments its clock; a message carries the sender's
timestamp of the send event; on receive, the process sets its clock to `max(own clock, message timestamp) + 1`.

Return `[timestamps, order]`:

- `timestamps[i]` is the Lamport timestamp assigned to `events[i]`;
- `order` is the list of event indices sorted by `(timestamp, process id)` - the total order that Lamport
  timestamps induce.

**Example:** `n = 2`, `events = [["send", 0, 1], ["local", 1], ["recv", 1, 1], ["local", 0]]`
→ `[[1, 1, 2, 2], [0, 1, 3, 2]]`
""",
    starter='''def lamport_order(n: int, events: List[list]) -> list:
    pass
''',
    solution='''def lamport_order(n, events):
    clock = [0] * n
    msg_ts = {}
    ts = []
    for ev in events:
        kind, p = ev[0], ev[1]
        if kind == "recv":
            clock[p] = max(clock[p], msg_ts[ev[2]]) + 1
        else:
            clock[p] += 1
            if kind == "send":
                msg_ts[ev[2]] = clock[p]
        ts.append(clock[p])
    order = sorted(range(len(events)), key=lambda i: (ts[i], events[i][1]))
    return [ts, order]
''',
    tests=[
        [2, [["send", 0, 1], ["local", 1], ["recv", 1, 1], ["local", 0]]],
        [1, []],
        [1, [["local", 0], ["local", 0], ["local", 0]]],
        [3, [["local", 2], ["local", 1], ["local", 0]]],
        [2, [["local", 0], ["local", 0], ["local", 0], ["send", 0, 9], ["recv", 1, 9], ["local", 1]]],
        [2, [["local", 1], ["local", 1], ["local", 1], ["send", 0, 5], ["recv", 1, 5]]],
        [2, [["send", 0, 1], ["send", 1, 2], ["recv", 0, 2], ["recv", 1, 1]]],
        [3, [["send", 0, 1], ["recv", 1, 1], ["send", 1, 2], ["recv", 2, 2], ["send", 2, 3], ["recv", 0, 3]]],
        [3, [["send", 0, 1], ["send", 0, 2], ["recv", 2, 2], ["recv", 1, 1], ["local", 2], ["send", 2, 3], ["recv", 1, 3]]],
        [2, [["send", 0, 7], ["local", 0], ["local", 0]]],
        [4, _rand_events(4, 40)],
        [5, _rand_events(5, 300)],
        [3, _rand_events(3, 1500)],
    ],
    examples=1,
    wrong_solutions=[
        '''def lamport_order(n, events):
    clock, msg, ts = [0] * n, {}, []
    for ev in events:
        p = ev[1]
        clock[p] += 1
        if ev[0] == "send":
            msg[ev[2]] = clock[p]
        ts.append(clock[p])
    return [ts, sorted(range(len(events)), key=lambda i: (ts[i], events[i][1]))]
''',
        '''def lamport_order(n, events):
    clock, msg, ts = [0] * n, {}, []
    for ev in events:
        p = ev[1]
        if ev[0] == "recv":
            clock[p] = max(clock[p], msg[ev[2]])
        else:
            clock[p] += 1
            if ev[0] == "send":
                msg[ev[2]] = clock[p]
        ts.append(clock[p])
    return [ts, sorted(range(len(events)), key=lambda i: (ts[i], events[i][1]))]
''',
        '''def lamport_order(n, events):
    clock, msg, ts = [0] * n, {}, []
    for ev in events:
        p = ev[1]
        if ev[0] == "recv":
            clock[p] = max(clock[p], msg[ev[2]]) + 1
        else:
            clock[p] += 1
            if ev[0] == "send":
                msg[ev[2]] = clock[p]
        ts.append(clock[p])
    return [ts, sorted(range(len(events)), key=lambda i: (ts[i], i))]
''',
        '''def lamport_order(n, events):
    clock, msg, ts = [0] * n, {}, []
    for ev in events:
        p = ev[1]
        if ev[0] == "recv":
            clock[p] = msg[ev[2]] + 1
        else:
            clock[p] += 1
            if ev[0] == "send":
                msg[ev[2]] = clock[p]
        ts.append(clock[p])
    return [ts, sorted(range(len(events)), key=lambda i: (ts[i], events[i][1]))]
''',
    ],
    guide=dict(
        prereqs="Lesson *Ordering, causality, Lamport clocks and total order broadcast*.",
        intuition="Physical clocks cannot be trusted to order events across machines, but causality can be tracked with a counter: every event ticks the local counter, and every message drags the receiver's counter past the sender's. The result is a number that always grows along any chain of cause and effect.",
        hints=[
            "Keep one integer per process and a dict from message id to the timestamp it carries.",
            "On receive, take the max of the local clock and the message's timestamp **and then** add one.",
            "The total order is a sort by the pair `(timestamp, process id)`; the process id only matters for ties.",
        ],
        brute_force="Build the happened-before graph explicitly and topologically sort it: O(E^2) if done naively, and it yields one of many valid orders rather than the specific Lamport order.",
        approach="Single pass assigning timestamps, then one sort.\n\nDry run of the example: `send` by P0 → P0 = 1 (message carries 1). `local` on P1 → 1. `recv` on P1 → max(1, 1) + 1 = 2. `local` on P0 → 2. Sorting `(1,P0) (1,P1) (2,P1) (2,P0)` by timestamp then process gives indices `[0, 1, 3, 2]`.",
        complexity="O(E log E) for E events (the sort); O(E + n) space.",
        pitfalls="Forgetting the `+ 1` on receive (the receive would share a timestamp with its own cause); overwriting the clock with the message timestamp instead of taking the max (clocks would run backwards); breaking ties by event index, which uses global knowledge no real process has.",
        follow_up="If a → b then L(a) < L(b), but not the other way round: two events with different Lamport timestamps may still be concurrent. Which data structure does give you the converse, and what does it cost?",
    ),
),
dict(
    id="db-2pc-outcome",
    title="Two-Phase Commit Coordinator Outcome",
    difficulty="Medium",
    pattern="Distributed Transactions",
    kind="function",
    entry="two_phase_commit",
    description=r"""
Simulate one round of two-phase commit (2PC).

`votes[i]` is participant `i`'s answer to the coordinator's *prepare* request:

- `"yes"` - it has durably prepared and promises to commit if told to;
- `"no"` - it refuses and aborts its local transaction immediately;
- `"timeout"` - no answer arrived; that participant never made a promise and aborts on its own.

`crash` describes the coordinator:

- `None` - it does not crash;
- `"before_decision"` - it crashes after collecting the votes but **before** writing its decision to its log;
- `"after_decision"` - it crashes **after** logging the decision but before telling any participant.

The decision is `"commit"` iff every vote is `"yes"`, otherwise `"abort"`.

Return `[decision, states]` describing the system while the coordinator is still down (or after completion if it never crashed):

- `decision`: the decision in the coordinator's log - `"commit"`, `"abort"`, or `None` if nothing was logged;
- `states[i]`: `"committed"`, `"aborted"` or `"in_doubt"`. A participant that voted yes and has not heard the
  outcome is **in doubt**: it must keep waiting and may neither commit nor abort on its own.

With zero participants the decision is `"commit"` (when logged) and `states` is empty.

**Example:** `votes = ["yes", "yes"], crash = None` → `["commit", ["committed", "committed"]]`

**Example:** `votes = ["yes", "no", "yes"], crash = "after_decision"` → `["abort", ["in_doubt", "aborted", "in_doubt"]]`
""",
    starter='''def two_phase_commit(votes: List[str], crash: Optional[str]) -> list:
    pass
''',
    solution='''def two_phase_commit(votes, crash):
    decision = "commit" if all(v == "yes" for v in votes) else "abort"
    if crash is None:
        final = "committed" if decision == "commit" else "aborted"
        return [decision, [final] * len(votes)]
    states = ["in_doubt" if v == "yes" else "aborted" for v in votes]
    return [None if crash == "before_decision" else decision, states]
''',
    tests=[
        [["yes", "yes"], None],
        [["yes", "no", "yes"], "after_decision"],
        [["yes", "yes", "yes"], "before_decision"],
        [["yes", "yes", "yes"], "after_decision"],
        [["yes", "no", "yes"], None],
        [["yes", "timeout"], None],
        [["timeout", "yes", "no"], "before_decision"],
        [["no", "no"], "after_decision"],
        [[], None],
        [[], "before_decision"],
        [[], "after_decision"],
        [["yes"], "before_decision"],
        [["yes", "yes", "yes", "yes", "no"], None],
        [["yes"] * 200 + ["timeout"], "after_decision"],
    ],
    examples=2,
    wrong_solutions=[
        '''def two_phase_commit(votes, crash):
    yes = sum(v == "yes" for v in votes)
    decision = "commit" if yes * 2 > len(votes) or not votes else "abort"
    if crash is None:
        return [decision, ["committed" if decision == "commit" else "aborted"] * len(votes)]
    states = ["in_doubt" if v == "yes" else "aborted" for v in votes]
    return [None if crash == "before_decision" else decision, states]
''',
        '''def two_phase_commit(votes, crash):
    decision = "commit" if all(v == "yes" for v in votes) else "abort"
    if crash is None:
        return [decision, ["committed" if decision == "commit" else "aborted"] * len(votes)]
    return [None if crash == "before_decision" else decision, ["aborted"] * len(votes)]
''',
        '''def two_phase_commit(votes, crash):
    decision = "commit" if all(v == "yes" for v in votes) else "abort"
    final = "committed" if decision == "commit" else "aborted"
    if crash == "before_decision":
        return [None, ["in_doubt" if v == "yes" else "aborted" for v in votes]]
    return [decision, [final] * len(votes)]
''',
        '''def two_phase_commit(votes, crash):
    decision = "commit" if all(v == "yes" for v in votes) else "abort"
    if crash is None:
        return [decision, ["committed" if v == "yes" else "aborted" for v in votes]]
    states = ["in_doubt" if v == "yes" else "aborted" for v in votes]
    return [None if crash == "before_decision" else decision, states]
''',
    ],
    guide=dict(
        prereqs="Lesson *Distributed transactions, 2PC and consensus*.",
        intuition="2PC has two points of no return. A participant that votes yes gives up its right to abort. The coordinator's log write is the moment the outcome becomes fact. Everything awkward about 2PC lives in the gap between those two moments: prepared participants hold locks and can do nothing but wait for a coordinator that may be down.",
        hints=[
            "Compute the decision first: unanimity, not majority.",
            "Without a crash everyone ends in the same state, including those who voted yes in an aborted round.",
            "With a crash, look at each participant alone: did it promise (yes → in doubt) or not (no/timeout → aborted)? Only the logged decision differs between the two crash points.",
        ],
        brute_force="Enumerating the 3 crash cases times 3 vote kinds as nine hand-written branches works but hides the structure: the per-participant state depends only on its own vote and on whether the decision was delivered.",
        approach="1. `decision = commit iff all yes`.\n2. No crash → `[decision, [final]*n]`.\n3. Crash → states from each vote; logged decision is `None` for `before_decision`, else `decision`.\n\nDry run: `[yes, no, yes]` with `after_decision` → the log says abort, but nobody was told: the no-voter already aborted itself, the two yes-voters are stuck in doubt even though the answer exists on the coordinator's disk.",
        complexity="O(n) time and space.",
        pitfalls="Using a majority rule (that is consensus voting, not atomic commit); letting in-doubt participants abort after a timeout - if the coordinator had logged commit and another participant later learns it, atomicity is broken; forgetting that `all([])` is true.",
        follow_up="On recovery, a coordinator that finds no decision in its log aborts the transaction; one that finds a decision re-sends it. Why does this make the coordinator's disk a single point of failure, and how do consensus-based commit protocols remove it?",
    ),
),
dict(
    id="db-mapreduce-wordcount",
    title="MapReduce Word Count",
    difficulty="Easy",
    pattern="Batch Processing",
    kind="function",
    entry="word_count",
    description=r"""
Simulate the three stages of a MapReduce job that counts words.

- **Map:** for each document, lower-case it and emit `(word, 1)` for every maximal run of the characters `a-z` and `0-9` (everything else is a separator).
- **Shuffle:** send each pair to reducer number `sum(ord(c) for c in word) % num_reducers`, and sort each reducer's input by key.
- **Reduce:** each reducer sums the counts per word.

Return a list with one entry per reducer (index = reducer number): that reducer's output as a list of
`[word, count]` sorted by word. Reducers that receive nothing output an empty list.

**Example:** `docs = ["the cat", "The dog, the END"], num_reducers = 2`
→ `[["the", 3]]` goes to reducer `(116+104+101) % 2 = 1`, and so on:
`[[["cat", 1], ["dog", 1]], [["end", 1], ["the", 3]]]`
""",
    starter='''def word_count(docs: List[str], num_reducers: int) -> List[List[list]]:
    pass
''',
    solution='''def word_count(docs, num_reducers):
    import re
    # map
    pairs = []
    for doc in docs:
        for w in re.findall(r"[a-z0-9]+", doc.lower()):
            pairs.append((w, 1))
    # shuffle: partition, then sort each partition by key
    parts = [[] for _ in range(num_reducers)]
    for w, c in pairs:
        parts[sum(ord(ch) for ch in w) % num_reducers].append((w, c))
    # reduce: one pass over each sorted partition
    out = []
    for part in parts:
        part.sort()
        res = []
        for w, c in part:
            if res and res[-1][0] == w:
                res[-1][1] += c
            else:
                res.append([w, c])
        out.append(res)
    return out
''',
    tests=[
        [["the cat", "The dog, the END"], 2],
        [[], 3],
        [[""], 1],
        [["...!!!"], 2],
        [["a a a a"], 1],
        [["Hello, hello; HELLO!"], 4],
        [["don't stop"], 3],
        [["node1 node2 node1", "2 nodes"], 3],
        [["tab\tseparated\nlines here", "here\r\nagain"], 2],
        [["x"], 5],
        [["snake_case and kebab-case"], 2],
        [_rand_docs(30, 40), 4],
        [_rand_docs(200, 100), 7],
    ],
    examples=1,
    wrong_solutions=[
        '''def word_count(docs, num_reducers):
    out = [dict() for _ in range(num_reducers)]
    for doc in docs:
        for w in doc.lower().split():
            d = out[sum(ord(ch) for ch in w) % num_reducers]
            d[w] = d.get(w, 0) + 1
    return [[[w, d[w]] for w in sorted(d)] for d in out]
''',
        '''def word_count(docs, num_reducers):
    import re
    out = [dict() for _ in range(num_reducers)]
    for doc in docs:
        for w in re.findall(r"[A-Za-z0-9]+", doc):
            d = out[sum(ord(ch) for ch in w) % num_reducers]
            d[w] = d.get(w, 0) + 1
    return [[[w, d[w]] for w in sorted(d)] for d in out]
''',
        '''def word_count(docs, num_reducers):
    import re
    out = [dict() for _ in range(num_reducers)]
    for doc in docs:
        for w in re.findall(r"[a-z0-9]+", doc.lower()):
            d = out[len(w) % num_reducers]
            d[w] = d.get(w, 0) + 1
    return [[[w, d[w]] for w in sorted(d)] for d in out]
''',
        '''def word_count(docs, num_reducers):
    import re
    out = [dict() for _ in range(num_reducers)]
    for doc in docs:
        for w in re.findall(r"[a-z0-9]+", doc.lower()):
            d = out[sum(ord(ch) for ch in w) % num_reducers]
            d[w] = d.get(w, 0) + 1
    return [[[w, d[w]] for w in d] for d in out]
''',
    ],
    guide=dict(
        prereqs="Regular expressions or manual tokenising; lesson *From Unix pipes to MapReduce*.",
        intuition="MapReduce is `sort | uniq -c` spread over many machines. The mapper only decides *what the key is*; the framework guarantees that all pairs with the same key arrive at the same reducer, adjacent to each other. The reducer then needs nothing more than a running total.",
        hints=[
            "`re.findall(r\"[a-z0-9]+\", doc.lower())` does the whole map-side tokenising.",
            "The partition function must depend only on the key, so that every occurrence of a word lands on the same reducer.",
            "After sorting a partition, equal words are neighbours: compare with the last output entry instead of using a dict.",
        ],
        brute_force="One global `Counter`, then distribute the finished counts over reducers. It gives the same answer here, but it assumes all distinct words fit in one machine's memory - the assumption MapReduce exists to remove.",
        approach="1. Map: emit `(word, 1)`.\n2. Partition by `sum(ord) % R`.\n3. Sort each partition.\n4. Reduce by scanning runs of equal keys.\n\nDry run: `the cat` / `The dog, the END` → pairs the, cat, the, dog, the, end. Partitions (R=2): cat→0 (312), dog→0 (314), the→1 (321), end→1 (311). Sorted and summed: `[[cat,1],[dog,1]]`, `[[end,1],[the,3]]`.",
        complexity="O(N log N) for N word occurrences (dominated by the sort), O(N) space. In a real cluster the mappers also sort and may pre-aggregate with a combiner to shrink the shuffle.",
        pitfalls="Splitting on whitespace only (punctuation sticks to words); forgetting to lower-case before tokenising; partitioning on something other than the key; returning reducers' output unsorted.",
        follow_up="The word `the` makes one reducer far busier than the others. How do a combiner, and for joins a skew-aware technique such as salting the hot key, reduce the damage?",
    ),
),
dict(
    id="db-tumbling-window",
    title="Tumbling-Window Aggregation with Late Events",
    difficulty="Medium",
    pattern="Stream Processing",
    kind="function",
    entry="tumbling_counts",
    description=r"""
Count events per key in fixed, non-overlapping (**tumbling**) windows of **event time**, coping with
out-of-order arrival.

`events` is a list of `[event_time, key]` in **arrival order** (`event_time` is a non-negative integer).
A window of length `size` covers `[start, start + size)` where `start` is a multiple of `size`.

The operator tracks a **watermark**: `(largest event_time seen so far) - allowed_lateness`. Before any
event has arrived the watermark is minus infinity. When an event arrives:

1. if its window has already closed, i.e. `window_end <= watermark` (using the watermark from the events
   **before** this one), the event is **dropped** as too late;
2. otherwise it is counted in its window;
3. in both cases the event then advances the largest-seen event time.

Return `[counts, dropped]`: `counts` is a list of `[window_start, key, count]` sorted by window start then
key, and `dropped` is the number of discarded events.

**Example:** `events = [[1,"a"],[12,"a"],[3,"a"],[25,"b"],[4,"a"]], size = 10, allowed_lateness = 5`
→ `[[[0,"a",2],[10,"a",1],[20,"b",1]], 1]`
(the event at time 3 arrives when the watermark is 7, window `[0,10)` is still open; the event at time 4
arrives when the watermark is 20, so it is dropped)
""",
    starter='''def tumbling_counts(events: List[list], size: int, allowed_lateness: int) -> list:
    pass
''',
    solution='''def tumbling_counts(events, size, allowed_lateness):
    counts = {}
    max_seen = None
    dropped = 0
    for t, key in events:
        start = t - t % size
        if max_seen is not None and start + size <= max_seen - allowed_lateness:
            dropped += 1
        else:
            counts[(start, key)] = counts.get((start, key), 0) + 1
        if max_seen is None or t > max_seen:
            max_seen = t
    return [[[s, k, c] for (s, k), c in sorted(counts.items())], dropped]
''',
    tests=[
        [[[1, "a"], [12, "a"], [3, "a"], [25, "b"], [4, "a"]], 10, 5],
        [[], 10, 0],
        [[[0, "a"]], 10, 0],
        [[[0, "a"], [9, "a"], [10, "a"], [19, "b"], [20, "a"]], 10, 0],
        [[[10, "a"], [9, "a"]], 10, 0],
        [[[9, "a"], [10, "a"], [9, "b"]], 10, 0],
        [[[9, "a"], [10, "a"], [9, "b"]], 10, 1],
        [[[100, "x"], [5, "x"], [95, "x"], [89, "x"], [90, "x"]], 10, 10],
        [[[5, "b"], [5, "a"], [5, "b"], [15, "a"], [5, "a"]], 10, 5],
        [[[5, "b"], [5, "a"], [5, "b"], [15, "a"], [5, "a"]], 10, 4],
        [[[3, "k"], [3, "k"], [3, "k"]], 1, 0],
        [[[50, "a"], [0, "a"], [49, "a"], [60, "a"], [40, "a"]], 10, 1000],
        [_rand_stream(300, 10), 10, 5],
        [_rand_stream(2000, 60), 60, 30],
    ],
    examples=1,
    wrong_solutions=[
        '''def tumbling_counts(events, size, allowed_lateness):
    counts = {}
    for t, key in events:
        s = t - t % size
        counts[(s, key)] = counts.get((s, key), 0) + 1
    return [[[s, k, c] for (s, k), c in sorted(counts.items())], 0]
''',
        '''def tumbling_counts(events, size, allowed_lateness):
    counts, mx, dropped = {}, None, 0
    for t, key in events:
        s = t - t % size
        if mx is not None and t < mx - allowed_lateness:
            dropped += 1
        else:
            counts[(s, key)] = counts.get((s, key), 0) + 1
        if mx is None or t > mx:
            mx = t
    return [[[s, k, c] for (s, k), c in sorted(counts.items())], dropped]
''',
        '''def tumbling_counts(events, size, allowed_lateness):
    counts, mx, dropped = {}, None, 0
    for t, key in events:
        s = t - t % size
        if mx is not None and s + size < mx - allowed_lateness:
            dropped += 1
        else:
            counts[(s, key)] = counts.get((s, key), 0) + 1
        if mx is None or t > mx:
            mx = t
    return [[[s, k, c] for (s, k), c in sorted(counts.items())], dropped]
''',
        '''def tumbling_counts(events, size, allowed_lateness):
    counts, mx, dropped = {}, None, 0
    for t, key in events:
        s = t - t % size
        if mx is not None and s + size <= mx - allowed_lateness:
            dropped += 1
        else:
            counts[(s, key)] = counts.get((s, key), 0) + 1
        mx = t
    return [[[s, k, c] for (s, k), c in sorted(counts.items())], dropped]
''',
    ],
    guide=dict(
        prereqs="Lesson *Processing streams: time, windows, joins, fault tolerance* (event time vs processing time, watermarks).",
        intuition="Events carry the time at which they happened, but they arrive when the network feels like it. The operator therefore needs a rule for declaring a window finished. The watermark is that rule: 'I do not expect anything older than this any more.' Lateness tolerance trades result delay for completeness.",
        hints=[
            "The window of time `t` starts at `t - t % size`.",
            "Decide whether to drop using the maximum event time seen **before** the current event, then update the maximum.",
            "A window `[s, s+size)` is closed once `s + size <= watermark`; compare the window's end, not the event's own time.",
        ],
        brute_force="Ignore lateness, group everything by window at the end. That is the batch answer and the most *complete* one, but a streaming job cannot wait until the end of an unbounded stream to emit results.",
        approach="One pass with a dict keyed by `(window_start, key)`, a running `max_seen` and a `dropped` counter; sort the dict items at the end.\n\nDry run (size 10, lateness 5): t=1 → window 0, count. t=12 → window 10, count, max 12. t=3 → watermark 7, window 0 ends at 10 > 7 → count. t=25 → window 20, max 25. t=4 → watermark 20, window end 10 <= 20 → dropped.",
        complexity="O(n + w log w) for n events and w distinct (window, key) pairs; O(w) space. A real operator would also emit and free windows as the watermark passes them, keeping state bounded.",
        pitfalls="Comparing the event's timestamp instead of its window end against the watermark (drops events from windows that are still open); letting a late event move the maximum backwards; off-by-one on the half-open window boundary.",
        follow_up="Instead of dropping late events you can emit a correction for the already-published window (retraction). What does that require of the downstream consumer? How would hopping (overlapping) windows change the code?",
    ),
),
dict(
    id="db-ivf-search",
    title="IVF Approximate Nearest-Neighbour Search",
    difficulty="Medium",
    pattern="Vector Search",
    kind="function",
    entry="ivf_search",
    description=r"""
An **inverted file (IVF)** index speeds up vector search by clustering the vectors and scanning only the
few clusters nearest to the query.

Given

- `centroids`: a non-empty list of cluster centres,
- `vectors`: the stored vectors (vector `i` has id `i`),
- `query`, `nprobe` (number of clusters to scan, `1 <= nprobe`), and `k`,

do the following with **squared Euclidean distance**:

1. **Build:** assign every vector to its nearest centroid (ties → lower centroid index).
2. **Probe:** pick the `nprobe` centroids nearest to the query (ties → lower index; if `nprobe` exceeds the number of centroids, use them all).
3. **Scan:** among the vectors assigned to those centroids, return the ids of the `k` nearest to the query,
   nearest first (ties → lower id). Return fewer than `k` ids if the probed clusters hold fewer vectors.

**Example:** `centroids = [[0,0],[10,10]]`, `vectors = [[1,1],[9,9],[0,2],[6,6]]`, `query = [5,5]`, `nprobe = 1`, `k = 2`
→ `[2, 0]`. Vector 3 at `[6,6]` is the true nearest neighbour, but it lives in the other cluster and is
missed - that is the recall cost of approximate search. (The query is equally far from both centroids, and the tie goes to centroid 0.)
""",
    starter='''def ivf_search(centroids: List[List[float]], vectors: List[List[float]],
               query: List[float], nprobe: int, k: int) -> List[int]:
    pass
''',
    solution='''def ivf_search(centroids, vectors, query, nprobe, k):
    def d2(a, b):
        return sum((x - y) * (x - y) for x, y in zip(a, b))

    lists = [[] for _ in centroids]
    for i, v in enumerate(vectors):
        best = min(range(len(centroids)), key=lambda c: (d2(v, centroids[c]), c))
        lists[best].append(i)
    probe = sorted(range(len(centroids)), key=lambda c: (d2(query, centroids[c]), c))[:nprobe]
    cand = [i for c in probe for i in lists[c]]
    cand.sort(key=lambda i: (d2(query, vectors[i]), i))
    return cand[:k]
''',
    tests=[
        [[[0, 0], [10, 10]], [[1, 1], [9, 9], [0, 2], [6, 6]], [5, 5], 1, 2],
        [[[0, 0], [10, 10]], [[1, 1], [9, 9], [0, 2], [6, 6]], [5, 5], 2, 2],
        [[[0, 0]], [], [1, 1], 1, 3],
        [[[0, 0]], [[3, 4]], [0, 0], 1, 1],
        [[[0, 0], [10, 10]], [[1, 1], [9, 9], [0, 2], [6, 6]], [5, 5], 5, 10],
        [[[0, 0], [100, 100]], [[1, 0], [0, 1], [2, 2]], [99, 99], 1, 2],
        [[[0], [10], [20]], [[1], [9], [11], [19], [21], [5]], [10], 1, 3],
        [[[0], [10], [20]], [[1], [9], [11], [19], [21], [5]], [14], 2, 4],
        [[[0, 0], [4, 0]], [[2, 0], [2, 1], [2, -1]], [3, 0], 1, 3],
        [[[1, 1], [1, 1]], [[1, 1], [2, 2]], [0, 0], 1, 2],
        [[[0, 0, 0], [5, 5, 5]], [[1, 2, 3], [4, 4, 4], [0, 0, 1], [6, 5, 4]], [2, 2, 2], 1, 0],
        [[[0.5, 0.5], [-0.5, -0.5]], [[0.1, 0.2], [-0.3, -0.1], [0.9, 0.8], [-0.7, -0.9]], [0.0, 0.1], 1, 2],
        [_rand_vecs(8, 4), _rand_vecs(300, 4), [1, -2, 3, 0], 2, 10],
        [_rand_vecs(16, 8), _rand_vecs(600, 8), [0] * 8, 3, 5],
        [_rand_vecs(5, 2, -3, 3), _rand_vecs(200, 2, -3, 3), [0, 0], 1, 20],
    ],
    examples=2,
    wrong_solutions=[
        '''def ivf_search(centroids, vectors, query, nprobe, k):
    d2 = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b))
    return sorted(range(len(vectors)), key=lambda i: (d2(query, vectors[i]), i))[:k]
''',
        '''def ivf_search(centroids, vectors, query, nprobe, k):
    d2 = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b))
    lists = [[] for _ in centroids]
    for i, v in enumerate(vectors):
        lists[min(range(len(centroids)), key=lambda c: (d2(v, centroids[c]), c))].append(i)
    probe = sorted(range(len(centroids)), key=lambda c: (d2(query, centroids[c]), c))[:1]
    cand = [i for c in probe for i in lists[c]]
    return sorted(cand, key=lambda i: (d2(query, vectors[i]), i))[:k]
''',
        '''def ivf_search(centroids, vectors, query, nprobe, k):
    d2 = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b))
    lists = [[] for _ in centroids]
    for i, v in enumerate(vectors):
        lists[min(range(len(centroids)), key=lambda c: (d2(v, centroids[c]), c))].append(i)
    probe = sorted(range(len(centroids)), key=lambda c: (d2(query, centroids[c]), c))[:nprobe]
    cand = [i for c in probe for i in lists[c]]
    return cand[:k]
''',
        '''def ivf_search(centroids, vectors, query, nprobe, k):
    d2 = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b))
    lists = [[] for _ in centroids]
    for i, v in enumerate(vectors):
        lists[min(range(len(centroids)), key=lambda c: (d2(v, centroids[c]), -c))].append(i)
    probe = sorted(range(len(centroids)), key=lambda c: (d2(query, centroids[c]), c))[:nprobe]
    cand = [i for c in probe for i in lists[c]]
    return sorted(cand, key=lambda i: (d2(query, vectors[i]), i))[:k]
''',
    ],
    guide=dict(
        prereqs="Euclidean distance, sorting with a key. Lesson *Redis and vector databases* (IVF and HNSW).",
        intuition="Comparing the query with every stored vector is exact but linear. If vectors are grouped by region of space beforehand, a query only needs to visit the regions close to it. You give up a little recall - a true neighbour may sit just across a cluster border - for a large cut in work.",
        hints=[
            "Write `d2(a, b)` once; no square root is needed because it does not change the ordering.",
            "Build `lists[c]` = ids of vectors whose nearest centroid is `c`.",
            "Rank centroids by distance to the query, keep `nprobe`, gather their lists, then sort candidates by `(distance, id)`.",
        ],
        brute_force="Exact k-NN: compute the distance to all N vectors and take the k smallest - O(N d). It is the recall = 100 % baseline against which every approximate index is measured (and the first wrong solution here, since it ignores `nprobe`).",
        approach="1. Assign vectors to centroids (`min` with a `(distance, index)` key handles ties).\n2. Choose the probe set.\n3. Collect candidates and sort.\n\nDry run of the example: lists = {0: [0, 2], 1: [1, 3]}. The query `[5,5]` is 50 from both centroids → tie → centroid 0. Candidates 0 (`[1,1]`, distance 32) and 2 (`[0,2]`, distance 34) → `[0, 2]`... check the order: 32 < 34, so the answer is `[0, 2]`? Recompute: `[0,2]` → 25 + 9 = 34 and `[1,1]` → 16 + 16 = 32, so id 0 comes first.",
        complexity="Build O(N C d); query O(C d + (N nprobe / C) d) on balanced clusters, versus O(N d) for brute force. Choosing C near sqrt(N) balances the two terms.",
        pitfalls="Returning candidates in list order instead of by distance; ignoring `nprobe`; inconsistent tie-breaking; taking square roots of every distance for no benefit.",
        follow_up="Increase `nprobe` and watch recall rise towards the brute-force answer while cost grows linearly. Production systems combine IVF with product quantisation to compress the vectors inside each list; graph indexes (HNSW) take a different route entirely.",
    ),
),
]
