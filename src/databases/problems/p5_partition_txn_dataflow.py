"""Beginner-friendly simulations for modules 6-13: rebalancing, lost updates, Raft commit index,
sort-merge join, session windows and a sliding-window rate limiter."""
import random as _r

_rng = _r.Random(23)


def _schedule(n_ops, txs, keys):
    return [[_rng.choice(txs), _rng.choice(["r", "r", "w"]), _rng.choice(keys)] for _ in range(n_ops)]


def _events(n, users, span):
    return [[_rng.choice(users), _rng.randrange(span)] for _ in range(n)]


def _requests(n, clients):
    t, out = 0.0, []
    for _ in range(n):
        t += _rng.choice([0, 0.5, 1, 1, 2, 7])
        out.append([_rng.choice(clients), t])
    return out


PROBLEMS = [
dict(
    id="db-rebalance-partitions",
    title="Rebalance Partitions onto a New Node",
    difficulty="Medium",
    pattern="Partitioning",
    kind="function",
    entry="add_node",
    description=r"""
A database uses a **fixed number of partitions**. `assignment[p]` is the name of the node that
currently stores partition `p`. A new, empty node joins the cluster, and some partitions must move
to it. Whole partitions move; nothing else changes.

Use this procedure so that as little data as possible moves and the answer is unique:

1. `target = number_of_partitions // (number_of_existing_nodes + 1)`, where the existing nodes are
   the distinct names in `assignment`. The new node should end up with exactly `target` partitions.
2. While the new node has fewer than `target` partitions: find the existing node that currently
   owns the **most** partitions (if several tie, the one whose name comes first alphabetically),
   and move its **highest-numbered** partition to the new node.

Write `add_node(assignment, new_node)` returning the new assignment list. The new node's name does
not appear in the input.

**Example:** `assignment = ["a", "b", "a", "b", "a", "b"]`, `new_node = "c"` → `["a", "b", "a", "b", "c", "c"]`
(target is 6 // 3 = 2. Nodes a and b tie with 3 each, so a gives up its highest partition, 4.
Then b has the most and gives up partition 5.)

**Example:** `assignment = ["a", "a", "a"]`, `new_node = "b"` → `["a", "a", "b"]`
""",
    starter='''def add_node(assignment: List[str], new_node: str) -> List[str]:
    pass
''',
    solution='''def add_node(assignment, new_node):
    result = list(assignment)
    owned = {}                                   # node -> list of its partitions, ascending
    for p, node in enumerate(result):
        owned.setdefault(node, []).append(p)
    target = len(result) // (len(owned) + 1)
    for _ in range(target):
        donor = min(owned, key=lambda n: (-len(owned[n]), n))
        p = owned[donor].pop()                   # highest-numbered partition of the donor
        result[p] = new_node
    return result
''',
    tests=[
        [["a", "b", "a", "b", "a", "b"], "c"],
        [["a", "a", "a"], "b"],
        [[], "x"],
        [["a"], "b"],
        [["a", "b", "c"], "d"],
        [["n%d" % (p % 4) for p in range(20)], "n4"],
        [["a"] * 9 + ["b"], "c"],
        [["b", "a", "b", "a", "b", "a", "b", "a"], "c"],
        [["a", "a", "b", "b", "c", "c", "a", "b", "c", "a", "b", "c"], "d"],
        [["x%02d" % (p % 10) for p in range(1000)], "x99"],
        [["a", "b"] * 5 + ["a"], "ab"],
        [["solo"] * 7, "new"],
    ],
    examples=2,
    wrong_solutions=[
        '''def add_node(assignment, new_node):
    nodes = sorted(set(assignment)) + [new_node]
    return [nodes[p % len(nodes)] for p in range(len(assignment))]   # reshuffles nearly everything
''',
        '''def add_node(assignment, new_node):
    result = list(assignment)
    owned = {}
    for p, node in enumerate(result):
        owned.setdefault(node, []).append(p)
    target = len(result) // (len(owned) + 1)
    for _ in range(target):
        donor = min(owned, key=lambda n: (-len(owned[n]), n))
        p = owned[donor].pop(0)                  # takes the lowest-numbered partition
        result[p] = new_node
    return result
''',
    ],
    guide=dict(
        prereqs="Lists, dictionaries, `min` with a key function. See the lesson *Secondary indexes, rebalancing and request routing* (fixed number of partitions).",
        intuition="Rebalancing should move the minimum: the new node needs its fair share, and every partition it does not take stays exactly where it was. Taking one partition at a time from whichever node is currently fullest keeps the remaining nodes as even as possible.",
        hints=[
            "Build a dictionary from each node to the list of partition numbers it owns. Going through the assignment in order gives each list in ascending order.",
            "The fair share for the new node is `len(assignment) // (number of old nodes + 1)`.",
            "Repeat that many times: choose the donor with `min(owned, key=lambda n: (-len(owned[n]), n))`, which prefers more partitions and then the smaller name; pop the donor's last partition and assign it to the new node.",
        ],
        brute_force="Recompute `partition % number_of_nodes` for every partition. It balances the load and moves almost every partition, which is exactly what the fixed-partition scheme exists to avoid.",
        approach="Dry run on `[a, b, a, b, a, b]` adding `c`: owned = a:[0,2,4], b:[1,3,5]; target = 6 // 3 = 2.\n- Round 1: a and b tie at 3, a wins alphabetically, gives partition 4. a:[0,2].\n- Round 2: b has 3, gives partition 5. b:[1,3].\n- Result `[a, b, a, b, c, c]`. Four of six partitions did not move.",
        complexity="Time O(P + target * N) for P partitions and N nodes. Space O(P).",
        pitfalls="Changing the caller's list in place. Counting the new node among the existing ones when computing the target. Breaking ties differently from the specification. An empty assignment has target 0 and must return an empty list.",
        follow_up="Give nodes different capacities (weights) so that a machine with twice the disk receives twice as many partitions.",
    ),
),
dict(
    id="db-lost-update-detect",
    title="Detect Lost Updates in a Schedule",
    difficulty="Medium",
    pattern="Transactions",
    kind="function",
    entry="lost_updates",
    description=r"""
A **lost update** happens when a transaction reads a value, another transaction changes it, and
the first transaction then writes a new value based on what it read. The other transaction's
change is overwritten without ever having been seen.

You are given a `schedule`: the operations of several transactions in the order the database
performed them. Each operation is `[tx, op, key]`, where `op` is `"r"` (read) or `"w"` (write).

A write by transaction `T` to `key` is a **stale write** when both of these hold:

1. `T` read `key` earlier in the schedule. Let `i` be the position of `T`'s **most recent** read of
   that key before the write. (A write with no earlier read by `T` is a blind write and is never stale.)
2. Some **other** transaction wrote `key` at a position after `i` and before `T`'s write.

Write `lost_updates(schedule)` returning `[tx, key]` for every stale write, in the order the
stale writes appear in the schedule.

**Example:** `[["A","r","x"], ["B","r","x"], ["A","w","x"], ["B","w","x"]]` → `[["B", "x"]]`
(B read x, then A wrote x, then B wrote x based on its old read)

**Example:** `[["A","r","x"], ["A","w","x"], ["B","r","x"], ["B","w","x"]]` → `[]`
(one after the other: nothing is lost)
""",
    starter='''def lost_updates(schedule: List[List[str]]) -> List[List[str]]:
    pass
''',
    solution='''def lost_updates(schedule):
    last_read = {}                 # (tx, key) -> position of tx's most recent read of key
    writes = {}                    # key -> list of (position, tx) for every write so far
    out = []
    for pos, (tx, op, key) in enumerate(schedule):
        if op == "r":
            last_read[(tx, key)] = pos
        else:
            i = last_read.get((tx, key))
            if i is not None and any(p > i and other != tx for p, other in writes.get(key, [])):
                out.append([tx, key])
            writes.setdefault(key, []).append((pos, tx))
    return out
''',
    tests=[
        [[["A", "r", "x"], ["B", "r", "x"], ["A", "w", "x"], ["B", "w", "x"]]],
        [[["A", "r", "x"], ["A", "w", "x"], ["B", "r", "x"], ["B", "w", "x"]]],
        [[]],
        [[["A", "r", "x"], ["B", "w", "x"], ["A", "r", "x"], ["A", "w", "x"]]],
        [[["A", "r", "x"], ["B", "r", "y"], ["A", "w", "y"], ["B", "w", "x"]]],
        [[["A", "w", "x"], ["B", "w", "x"], ["A", "w", "x"]]],
        [[["A", "r", "x"], ["B", "r", "x"], ["C", "r", "x"], ["A", "w", "x"], ["B", "w", "x"], ["C", "w", "x"]]],
        [[["A", "r", "x"], ["A", "w", "x"], ["A", "w", "x"]]],
        [[["A", "r", "x"], ["B", "w", "x"], ["A", "w", "x"], ["A", "w", "x"]]],
        [[["A", "r", "x"], ["A", "r", "y"], ["B", "w", "y"], ["A", "w", "x"], ["A", "w", "y"]]],
        [[["mira", "r", "admins"], ["tom", "r", "admins"], ["mira", "w", "mira_role"], ["tom", "w", "tom_role"]]],
        [_schedule(400, ["A", "B", "C", "D"], ["x", "y", "z"])],
        [_schedule(120, ["A", "B"], ["x"])],
    ],
    examples=2,
    wrong_solutions=[
        '''def lost_updates(schedule):
    out, writers = [], {}
    for tx, op, key in schedule:           # flags any key written by two transactions
        if op == "w":
            if any(other != tx for other in writers.get(key, [])):
                out.append([tx, key])
            writers.setdefault(key, []).append(tx)
    return out
''',
        '''def lost_updates(schedule):
    first_read, writes, out = {}, {}, []
    for pos, (tx, op, key) in enumerate(schedule):
        if op == "r":
            first_read.setdefault((tx, key), pos)      # remembers the FIRST read, not the latest
        else:
            i = first_read.get((tx, key))
            if i is not None and any(p > i and other != tx for p, other in writes.get(key, [])):
                out.append([tx, key])
            writes.setdefault(key, []).append((pos, tx))
    return out
''',
    ],
    guide=dict(
        prereqs="Dictionaries with tuple keys, `enumerate`. See the lesson *Lost updates, write skew and phantoms* (the read-modify-write cycle).",
        intuition="A write is only as fresh as the read it was based on. So for every write, look back to the writer's own latest read of that key and ask whether anyone else slipped a write into the gap between that read and this write.",
        hints=[
            "Go through the schedule once with `enumerate` so you know each operation's position.",
            "Remember, for each `(tx, key)` pair, the position of that transaction's latest read. Remember, for each key, the positions and authors of all writes so far.",
            "On a write: look up the writer's latest read position `i`. If there is one, check whether the key's write list contains a write by a different transaction at a position greater than `i`. Record this write afterwards, not before the check.",
        ],
        brute_force="For every write, scan backwards through the schedule to find the writer's last read, then scan the stretch in between for foreign writes. O(n^2), and fine for short schedules.",
        approach="Dry run on `A r x, B r x, A w x, B w x`:\n- pos 0: last_read[(A,x)] = 0\n- pos 1: last_read[(B,x)] = 1\n- pos 2: A writes; its read was at 0; no writes to x yet; not stale. writes[x] = [(2, A)]\n- pos 3: B writes; its read was at 1; a write by A at position 2 > 1; stale. Output `[[B, x]]`.",
        complexity="Time O(n * w) in the worst case, where w is the number of writes to one key (it can be made O(n) by storing only the latest foreign write position per key). Space O(n).",
        pitfalls="Flagging blind writes, which have no read to be stale against. Using a transaction's first read when it has read the key again more recently. Counting the transaction's own earlier write as someone else's. Note the admin example in the tests: two transactions writing *different* keys is write skew, not a lost update, and must return nothing.",
        follow_up="This is how snapshot-isolation databases detect lost updates automatically. Extend the detector to report write skew: two transactions that read the same key and then write different keys.",
    ),
),
dict(
    id="db-raft-commit-index",
    title="Raft Commit Index",
    difficulty="Medium",
    pattern="Consensus",
    kind="function",
    entry="commit_index",
    description=r"""
In the Raft consensus algorithm the leader keeps a log of entries, numbered from 1. An entry is
**committed**, and so safe to apply, once it is stored on a **majority** of the nodes. The leader
has to work out how far the log is committed.

You are given:

- `match_index`: one number per node in the cluster, **the leader included**. `match_index[k]` is
  the highest log index known to be stored on node `k` (0 means nothing).
- `log_terms`: the leader's log. `log_terms[i - 1]` is the term in which entry `i` was created.
- `current_term`: the leader's current term.
- `commit`: the commit index so far.

Return the new commit index: the **largest** index `N` such that

1. `N > commit`,
2. more than half of the nodes have `match_index >= N`, and
3. entry `N` was created in the current term: `log_terms[N - 1] == current_term`.

If no such `N` exists, return `commit` unchanged. Rule 3 is Raft's safety rule: a leader never
declares an entry from an earlier term committed by counting copies. (When a current-term entry
is committed, everything before it is committed with it.)

**Example:** `match_index = [5, 5, 3, 2, 1]`, `log_terms = [1, 1, 2, 2, 2]`, `current_term = 2`, `commit = 0` → `3`
(three of five nodes store entry 3, and entry 3 is from term 2)

**Example:** `match_index = [3, 3, 3]`, `log_terms = [1, 1, 1]`, `current_term = 2`, `commit = 0` → `0`
(every entry is from an old term, so nothing may be committed by counting)
""",
    starter='''def commit_index(match_index: List[int], log_terms: List[int], current_term: int, commit: int) -> int:
    pass
''',
    solution='''def commit_index(match_index, log_terms, current_term, commit):
    majority = len(match_index) // 2 + 1
    for n in range(len(log_terms), commit, -1):          # try the highest index first
        if log_terms[n - 1] != current_term:
            continue
        if sum(1 for m in match_index if m >= n) >= majority:
            return n
    return commit
''',
    tests=[
        [[5, 5, 3, 2, 1], [1, 1, 2, 2, 2], 2, 0],
        [[3, 3, 3], [1, 1, 1], 2, 0],
        [[1], [1], 1, 0],
        [[4, 4, 1, 1], [1, 1, 1, 1], 1, 0],
        [[4, 4, 4, 1], [1, 1, 1, 1], 1, 0],
        [[0, 0, 0], [], 1, 0],
        [[5, 5, 5, 5, 5], [1, 1, 2, 2, 3], 3, 2],
        [[5, 4, 4, 2, 2], [1, 1, 2, 3, 3], 3, 2],
        [[5, 3, 3, 0, 0], [1, 2, 2, 3, 3], 3, 1],
        [[6, 6, 2, 2, 2], [1, 1, 1, 1, 1, 1], 1, 2],
        [[7, 7, 7, 3, 3, 3, 3], [2, 2, 2, 2, 2, 2, 2], 2, 0],
        [[3, 3, 0], [1, 1, 1], 1, 3],
        [[10, 9, 8, 7, 6], [1, 1, 1, 2, 2, 2, 3, 3, 4, 4], 4, 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def commit_index(match_index, log_terms, current_term, commit):
    ordered = sorted(match_index, reverse=True)
    n = ordered[len(match_index) // 2]           # majority value, but ignores the term rule
    return max(n, commit)
''',
        '''def commit_index(match_index, log_terms, current_term, commit):
    half = len(match_index) // 2                 # "at least half" is not a majority for even sizes
    for n in range(len(log_terms), commit, -1):
        if log_terms[n - 1] == current_term and sum(1 for m in match_index if m >= n) >= max(half, 1):
            return n
    return commit
''',
    ],
    guide=dict(
        prereqs="Loops and counting. See the lesson *Distributed transactions, 2PC and consensus* (Raft in brief, majorities, terms).",
        intuition="An index is safe when most of the cluster holds it. Start from the end of the log and walk backwards: the first index that passes both tests (current term, majority) is the largest one, so you can stop there.",
        hints=[
            "A majority of `k` nodes is `k // 2 + 1`. For 4 nodes that is 3, not 2.",
            "Loop `n` from `len(log_terms)` down to `commit + 1`. For each `n`, skip it if `log_terms[n - 1]` is not the current term.",
            "Count the nodes with `match_index >= n`. If the count reaches the majority, return `n`. If the loop ends without returning, return `commit`.",
        ],
        brute_force="Check every index from 1 upward and remember the last one that passes. It gives the same answer and does not stop early.",
        approach="Dry run for `match_index = [5,5,3,2,1]`, `log_terms = [1,1,2,2,2]`, term 2, commit 0: majority is 3.\n- n = 5: term 2, stored on 2 nodes. No.\n- n = 4: term 2, stored on 2 nodes. No.\n- n = 3: term 2, stored on 3 nodes. Yes: return 3.",
        complexity="Time O(L * k) for a log of length L and k nodes; sorting `match_index` first would make it O(k log k + L). Space O(1).",
        pitfalls="Using `k // 2` as the majority, which lets half of an even-sized cluster decide and so allows two halves to decide differently. Ignoring the term rule. Off-by-one between the 1-based log index and the 0-based list. Returning something lower than the existing commit index.",
        follow_up="Why does Raft forbid committing old-term entries by counting? Read section 5.4.2 of the Raft paper: an old-term entry stored on a majority can still be overwritten by a later leader.",
    ),
),
dict(
    id="db-sort-merge-join",
    title="Sort-Merge Join",
    difficulty="Medium",
    pattern="Batch Joins",
    kind="function",
    entry="merge_join",
    description=r"""
A batch job has to join two large datasets and has no index. The classic method is to **sort both
sides by the join key and then walk through them together**, like closing a zip.

`left` is a list of `[key, left_value]` pairs and `right` is a list of `[key, right_value]` pairs.
Neither is sorted, and a key **may appear several times on either side**.

Write `merge_join(left, right)` returning the **inner join**: one `[key, left_value, right_value]`
for every pair of a left record and a right record with the same key.

Order of the result:

- by key, ascending;
- for the same key, by the left record's original position in `left`;
- for the same key and left record, by the right record's original position in `right`.

All keys in one call have the same type (all integers or all strings).

**Example:** `left = [[2, "b"], [1, "a"]]`, `right = [[1, "x"], [3, "z"], [1, "y"]]` → `[[1, "a", "x"], [1, "a", "y"]]`

**Example:** `left = [[1, "a"], [1, "b"]]`, `right = [[1, "x"], [1, "y"]]` →
`[[1, "a", "x"], [1, "a", "y"], [1, "b", "x"], [1, "b", "y"]]`
""",
    starter='''def merge_join(left: List[list], right: List[list]) -> List[list]:
    pass
''',
    solution='''def merge_join(left, right):
    ls = sorted(left, key=lambda rec: rec[0])        # sorted() is stable: ties keep input order
    rs = sorted(right, key=lambda rec: rec[0])
    out = []
    i = j = 0
    while i < len(ls) and j < len(rs):
        if ls[i][0] < rs[j][0]:
            i += 1
        elif ls[i][0] > rs[j][0]:
            j += 1
        else:
            key = ls[i][0]
            i_end = i
            while i_end < len(ls) and ls[i_end][0] == key:
                i_end += 1
            j_end = j
            while j_end < len(rs) and rs[j_end][0] == key:
                j_end += 1
            for a in range(i, i_end):                # every left record with this key ...
                for b in range(j, j_end):            # ... pairs with every right record
                    out.append([key, ls[a][1], rs[b][1]])
            i, j = i_end, j_end
    return out
''',
    tests=[
        [[[2, "b"], [1, "a"]], [[1, "x"], [3, "z"], [1, "y"]]],
        [[[1, "a"], [1, "b"]], [[1, "x"], [1, "y"]]],
        [[], []],
        [[[1, "a"]], []],
        [[], [[1, "x"]]],
        [[[1, "a"], [2, "b"]], [[3, "x"], [4, "y"]]],
        [[[5, "e"], [3, "c"], [4, "d"], [1, "a"]], [[4, "D"], [1, "A"], [5, "E"], [2, "B"]]],
        [[["u2", 20], ["u1", 10], ["u2", 21]], [["u1", "/home"], ["u2", "/cart"], ["u9", "/x"]]],
        [[[7, i] for i in range(30)], [[7, -i] for i in range(20)]],
        [[[i % 50, i] for i in range(600)], [[i % 75, i] for i in range(300)]],
        [[[i, "L%d" % i] for i in range(3000, 0, -1)], [[i, "R%d" % i] for i in range(1, 3001, 2)]],
        [[[1, None], [1, 0]], [[1, ""], [2, "q"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def merge_join(left, right):
    lookup = {k: v for k, v in right}                # keeps only the last right record per key
    return [[k, lv, lookup[k]] for k, lv in sorted(left, key=lambda rec: rec[0]) if k in lookup]
''',
        '''def merge_join(left, right):
    ls = sorted(left, key=lambda rec: rec[0])
    rs = sorted(right, key=lambda rec: rec[0])
    out, i, j = [], 0, 0
    while i < len(ls) and j < len(rs):
        if ls[i][0] < rs[j][0]:
            i += 1
        elif ls[i][0] > rs[j][0]:
            j += 1
        else:                                        # advances both: misses many-to-many matches
            out.append([ls[i][0], ls[i][1], rs[j][1]])
            i += 1
            j += 1
    return out
''',
    ],
    guide=dict(
        prereqs="Sorting with a key function, two-pointer loops. See the lesson *Batch joins and dataflow engines* (sort-merge join).",
        intuition="Once both sides are sorted by key, equal keys sit next to each other on each side. Keep one finger on each list. Whichever finger points at the smaller key moves forward. When both point at the same key, gather the whole block of that key on each side and pair every left record in the block with every right record in the block.",
        hints=[
            "Sort both lists by key only (`key=lambda rec: rec[0]`). Python's sort is stable, so records with equal keys keep their original order, which is the order the result must have.",
            "Use two indexes `i` and `j`. If the left key is smaller, advance `i`. If the right key is smaller, advance `j`.",
            "When the keys are equal, find where the block of that key ends on each side, emit the cross product of the two blocks (left block outside, right block inside), and jump both indexes to the ends of their blocks.",
        ],
        brute_force="A nested loop: for every left record, scan all right records. O(n * m) comparisons, and you would still have to sort the output. Fine for a few thousand records and impossible for billions.",
        approach="Dry run on left `[[2,b],[1,a]]`, right `[[1,x],[3,z],[1,y]]`: sorted left `[1,a],[2,b]`, sorted right `[1,x],[1,y],[3,z]`.\n- keys 1 and 1 match: left block is one record, right block is two; emit `[1,a,x]`, `[1,a,y]`.\n- left key 2 < right key 3: advance left; left is exhausted. Done.",
        complexity="Time O(n log n + m log m) for the sorts plus O(n + m + size of output) for the merge. Space O(n + m) for the sorted copies.",
        pitfalls="Advancing both pointers by one on a match loses pairs when a key repeats on both sides. Building a dictionary from one side keeps only one record per key. Sorting by the whole record changes the order of equal keys. Sorting the caller's lists in place.",
        follow_up="When one side is small enough for memory, a **hash join** skips both sorts: load the small side into a dictionary of lists and stream the large side past it. Implement it and compare.",
    ),
),
dict(
    id="db-session-windows",
    title="Session Windows",
    difficulty="Medium",
    pattern="Stream Windows",
    kind="function",
    entry="sessionize",
    description=r"""
A **session window** groups the events of one user that happen close together in time. A session
continues as long as each event comes **at most `gap` time units after the previous event of the
same user**. A longer silence ends the session, and the next event starts a new one.

`events` is a list of `[user, timestamp]` pairs. As in real streams, they arrive **out of order**.
Timestamps are non-negative integers and may repeat.

Write `sessionize(events, gap)` returning one `[user, start, end, count]` per session, where
`start` and `end` are the timestamps of the session's first and last events and `count` is the
number of events in it. Sort the result by user, then by start.

**Example:** `events = [["u1", 2], ["u1", 7], ["u1", 31], ["u1", 34], ["u1", 12]]`, `gap = 10`
→ `[["u1", 2, 12, 3], ["u1", 31, 34, 2]]`

**Example:** `events = [["u2", 50], ["u1", 5]]`, `gap = 10` → `[["u1", 5, 5, 1], ["u2", 50, 50, 1]]`
""",
    starter='''def sessionize(events: List[list], gap: int) -> List[list]:
    pass
''',
    solution='''def sessionize(events, gap):
    out = []
    for user, ts in sorted(events):              # by user, then by timestamp
        if out and out[-1][0] == user and ts - out[-1][2] <= gap:
            out[-1][2] = ts                      # extend the current session
            out[-1][3] += 1
        else:
            out.append([user, ts, ts, 1])        # start a new session
    return out
''',
    tests=[
        [[["u1", 2], ["u1", 7], ["u1", 31], ["u1", 34], ["u1", 12]], 10],
        [[["u2", 50], ["u1", 5]], 10],
        [[], 5],
        [[["a", 0]], 0],
        [[["a", 0], ["a", 10], ["a", 20]], 10],
        [[["a", 0], ["a", 11], ["a", 22]], 10],
        [[["a", 5], ["a", 5], ["a", 5]], 0],
        [[["a", 1], ["a", 2], ["a", 3]], 0],
        [[["b", 9], ["a", 9], ["b", 1], ["a", 1], ["b", 5], ["a", 30]], 4],
        [[["a", 100], ["a", 1], ["a", 50], ["a", 2], ["a", 99], ["a", 51]], 1],
        [[["a", 0], ["a", 6], ["a", 12], ["a", 18]], 6],
        [_events(600, ["u1", "u2", "u3", "u4", "u5"], 5000), 15],
        [_events(200, ["x"], 300), 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def sessionize(events, gap):
    out = []
    for user, ts in events:                      # forgot to sort: out-of-order events break it
        if out and out[-1][0] == user and ts - out[-1][2] <= gap:
            out[-1][2] = ts
            out[-1][3] += 1
        else:
            out.append([user, ts, ts, 1])
    return sorted(out)
''',
        '''def sessionize(events, gap):
    out = []
    for user, ts in sorted(events):
        if out and out[-1][0] == user and ts - out[-1][1] <= gap:   # measures from the session START
            out[-1][2] = ts
            out[-1][3] += 1
        else:
            out.append([user, ts, ts, 1])
    return out
''',
    ],
    guide=dict(
        prereqs="Sorting lists of lists, comparing neighbours in a loop. See the lesson *Processing streams: time, windows, joins, fault tolerance* (session windows).",
        intuition="Sessions are about neighbouring events of the same user. Sorting by user and then by time puts those neighbours next to each other, after which a single pass can decide for each event: does it continue the session in progress, or start a new one?",
        hints=[
            "`sorted(events)` orders the pairs by user first and timestamp second, which is exactly what is needed.",
            "Keep the session being built as the last item of the output list: `[user, start, end, count]`.",
            "For each event: if the output is not empty, the last session belongs to the same user, and `ts - last_end <= gap`, update that session's end and count. Otherwise append a new session.",
        ],
        brute_force="For each user, repeatedly merge any two events or groups that lie within `gap` of each other until nothing changes. Correct and quadratic or worse.",
        approach="Dry run with gap 10 on sorted `u1: 2, 7, 12, 31, 34`:\n- 2 starts `[u1, 2, 2, 1]`\n- 7 is 5 after 2: `[u1, 2, 7, 2]`\n- 12 is 5 after 7: `[u1, 2, 12, 3]`\n- 31 is 19 after 12: new session `[u1, 31, 31, 1]`\n- 34 is 3 after 31: `[u1, 31, 34, 2]`.",
        complexity="Time O(n log n) for the sort and O(n) for the pass. Space O(n).",
        pitfalls="Measuring the gap from the session's start, so a long but busy session is cut up wrongly. Not sorting. Letting one user's event extend another user's session. A gap exactly equal to `gap` still belongs to the same session.",
        follow_up="A real stream processor cannot sort, because the stream never ends. It keeps open sessions in state and must **merge** two sessions when a late event lands between them. Rewrite the function to process events one at a time in arrival order.",
    ),
),
dict(
    id="db-sliding-window-limiter",
    title="Sliding-Window Rate Limiter",
    difficulty="Medium",
    pattern="Rate Limiting",
    kind="function",
    entry="rate_limit",
    description=r"""
An API allows each client at most `limit` requests in any period of `window` seconds. This is the
sliding-window limiter usually built on a Redis sorted set.

`requests` is a list of `[client, t]` pairs in non-decreasing order of time `t`. For each request,
decide whether it is allowed:

- Look at the **allowed** requests of the same client with a time strictly greater than
  `t - window`. (A request made exactly `window` seconds ago has left the window.)
- If there are fewer than `limit` of them, the request is **allowed** and is remembered.
- Otherwise it is **rejected**. A rejected request is **not** remembered: it does not count
  against later requests.

Write `rate_limit(requests, limit, window)` returning a list of booleans, one per request, `True`
for allowed.

**Example:** `requests = [["ana", 0], ["ana", 1], ["ana", 2], ["ana", 3], ["ana", 10.5]]`, `limit = 3`, `window = 10`
→ `[True, True, True, False, True]`
(at 10.5 the request made at time 0 has left the window)

**Example:** `requests = [["ana", 0], ["bob", 0], ["ana", 1]]`, `limit = 1`, `window = 5` → `[True, True, False]`
""",
    starter='''def rate_limit(requests: List[list], limit: int, window: float) -> List[bool]:
    pass
''',
    solution='''import collections

def rate_limit(requests, limit, window):
    recent = {}                                   # client -> deque of times of allowed requests
    out = []
    for client, t in requests:
        q = recent.setdefault(client, collections.deque())
        while q and q[0] <= t - window:           # drop requests that have left the window
            q.popleft()
        if len(q) < limit:
            q.append(t)
            out.append(True)
        else:
            out.append(False)
    return out
''',
    tests=[
        [[["ana", 0], ["ana", 1], ["ana", 2], ["ana", 3], ["ana", 10.5]], 3, 10],
        [[["ana", 0], ["bob", 0], ["ana", 1]], 1, 5],
        [[], 3, 10],
        [[["a", 0], ["a", 0], ["a", 0]], 0, 10],
        [[["a", 0], ["a", 10]], 1, 10],
        [[["a", 0], ["a", 9.999]], 1, 10],
        [[["a", 0], ["a", 1], ["a", 2], ["a", 3], ["a", 9], ["a", 10.5], ["a", 11.5], ["a", 12.5], ["a", 13]], 3, 10],
        [[["a", 0], ["a", 0], ["a", 0], ["a", 0], ["a", 5], ["a", 5]], 2, 5],
        [[["a", 0], ["a", 1], ["a", 2], ["a", 3], ["a", 4], ["a", 5], ["a", 6]], 2, 3],
        [[["a", 1], ["b", 1], ["a", 2], ["b", 2], ["a", 3], ["b", 3], ["c", 3]], 2, 100],
        [[["a", i * 0.125] for i in range(300)], 5, 1],
        [[["a", 8], ["a", 9], ["a", 10], ["a", 11]], 2, 10],
        [_requests(500, ["a", "b", "c"]), 4, 6],
        [_requests(200, ["solo"]), 1, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def rate_limit(requests, limit, window):
    recent, out = {}, []
    for client, t in requests:
        q = recent.setdefault(client, [])
        q[:] = [x for x in q if x > t - window]
        out.append(len(q) < limit)
        q.append(t)                               # remembers rejected requests too
    return out
''',
        '''def rate_limit(requests, limit, window):
    counts, out = {}, []
    for client, t in requests:                    # fixed windows: allows bursts across a boundary
        bucket = (client, int(t // window)) if window else (client, t)
        counts[bucket] = counts.get(bucket, 0) + 1
        out.append(counts[bucket] <= limit)
    return out
''',
    ],
    guide=dict(
        prereqs="Dictionaries, and a queue (`collections.deque`, already imported). See the lesson *Redis and vector databases* (rate limiting with a sliding window).",
        intuition="For each client keep only the times of its recent allowed requests. Before deciding on a new request, throw away the times that have fallen out of the window. What is left is exactly the number to compare with the limit.",
        hints=[
            "Use a dictionary from client to a queue of timestamps. Requests arrive in time order, so each queue is sorted and the oldest time is always at the front.",
            "While the front of the queue is `<= t - window`, remove it.",
            "If the queue now holds fewer than `limit` times, append `t` and answer `True`. Otherwise answer `False` and do **not** append.",
        ],
        brute_force="Keep every allowed request for ever and count, for each new request, how many of the client's times are greater than `t - window`. Correct, with time growing with the full history.",
        approach="Dry run with limit 3, window 10 on times 0, 1, 2, 3, 10.5:\n- 0, 1, 2: queue grows to [0, 1, 2], all allowed\n- 3: nothing has expired (0 > 3 - 10), queue is full: rejected, queue unchanged\n- 10.5: 0 <= 0.5 expires, queue [1, 2], allowed, queue [1, 2, 10.5].",
        complexity="Time O(n) overall, because each timestamp is appended once and removed at most once. Space O(number of clients * limit).",
        pitfalls="Counting rejected requests lets a client that keeps hammering stay blocked for ever. Using `<` where `<=` is needed at the edge of the window. Fixed buckets of time let a client make `limit` requests at the end of one bucket and `limit` more at the start of the next. A limit of 0 must reject everything.",
        follow_up="In Redis this is three commands on a sorted set: `ZREMRANGEBYSCORE`, `ZCARD`, `ZADD`. Why must they run as one atomic step (a Lua script or a transaction) when several application servers share the limiter?",
    ),
),
]
