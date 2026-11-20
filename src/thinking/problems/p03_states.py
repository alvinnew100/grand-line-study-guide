_TURNSTILE = [["locked", "coin", "unlocked"], ["unlocked", "push", "locked"],
              ["locked", "push", "locked"], ["unlocked", "coin", "unlocked"]]
_ORDER = [["new", "pay", "paid"], ["new", "cancel", "cancelled"], ["paid", "ship", "shipped"],
          ["paid", "cancel", "refunded"], ["shipped", "deliver", "delivered"], ["delivered", "return", "refunded"]]
_DOOR = [["closed", "open", "opened"], ["opened", "close", "closed"], ["closed", "lock", "locked"],
         ["locked", "unlock", "closed"]]
_RING = [["s%d" % i, "next", "s%d" % ((i + 1) % 8)] for i in range(8)] + [["s%d" % i, "reset", "s0"] for i in range(8)]
_LINE = [["a", "f", "b"], ["b", "f", "c"], ["c", "f", "d"], ["d", "f", "e"], ["b", "r", "a"], ["c", "r", "b"],
         ["d", "r", "c"], ["e", "r", "d"]]
_STAR = [["hub", "go%d" % i, "leaf%d" % i] for i in range(5)] + [["leaf%d" % i, "back", "hub"] for i in range(5)]
_PRICES = {"cola": 125, "chips": 75, "gum": 35}
_BANK = [[100, 0], [25, 4], [10, 2], [5, 1]]

PROBLEMS = [
dict(
    id="think-vending-machine",
    title="Vending Machine Simulator",
    difficulty="Medium",
    pattern="State Machines",
    entry="vending",
    description=r"""
Simulate a coin-operated vending machine and report what it says after each event.

**Inputs**

- `prices`: dict item → price in cents. `stock`: dict item → units left (every priced item has an entry).
- `bank`: list of `[denomination, count]` — the coins in the machine's change tubes. The denominations
  listed here (even with count 0) are the **only coins accepted**.
- `events`: list of `["coin", value]`, `["select", item]` or `["refund"]`.

**State.** `credit` (starts 0) and an *escrow* holding the coins inserted since the last vend or refund.

**Rules — produce one output string per event**

- `["coin", v]`: if `v` is not an accepted denomination output `"REJECT v"` (coin handed back, nothing
  changes). Otherwise add it to escrow and credit and output `"CREDIT <credit>"`.
- `["refund"]`: output `"REFUND <credit>"`; the escrow coins are returned; credit becomes 0.
- `["select", item]` — check **in this order**:
  1. item not in `prices` → `"INVALID"`;
  2. stock is 0 → `"SOLD_OUT"`;
  3. `credit < price` → `"NEED <price - credit>"`;
  4. change `= credit - price` must be paid from the bank **plus the escrow coins**, greedily: repeatedly
     use the largest denomination that still fits and is still available. If the greedy procedure
     cannot reach the exact amount → `"EXACT_CHANGE_ONLY"` (nothing changes; the customer may refund);
  5. otherwise vend: stock decreases by 1, escrow coins move into the bank, the change coins leave the
     bank, credit becomes 0, output `"VEND <item> <change>"`.

Return `[outputs, bank_after]` where `bank_after` lists `[denomination, count]` for every
denomination in **descending** order. Coins still in escrow at the end are *not* part of the bank.

**Example:** `prices = {"gum": 35}`, `stock = {"gum": 1}`, `bank = [[25, 0], [10, 1], [5, 0]]`,
`events = [["coin", 25], ["coin", 25], ["select", "gum"], ["select", "gum"]]`
→ `[["CREDIT 25", "CREDIT 50", "EXACT_CHANGE_ONLY", "EXACT_CHANGE_ONLY"], [[25, 0], [10, 1], [5, 0]]]`

(Change of 15 needs a 10 and a 5, and the machine has no 5.)
""",
    starter='''def vending(prices: dict, stock: dict, bank: List[List[int]], events: List[list]) -> list:
    pass
''',
    solution='''def vending(prices, stock, bank, events):
    coins = {d: c for d, c in bank}
    denoms = sorted(coins, reverse=True)
    stock = dict(stock)
    credit = 0
    escrow = {}
    out = []
    for ev in events:
        kind = ev[0]
        if kind == "coin":
            v = ev[1]
            if v not in coins:
                out.append("REJECT %d" % v)
            else:
                escrow[v] = escrow.get(v, 0) + 1
                credit += v
                out.append("CREDIT %d" % credit)
        elif kind == "refund":
            out.append("REFUND %d" % credit)
            credit = 0
            escrow = {}
        else:
            item = ev[1]
            if item not in prices:
                out.append("INVALID")
            elif stock.get(item, 0) == 0:
                out.append("SOLD_OUT")
            elif credit < prices[item]:
                out.append("NEED %d" % (prices[item] - credit))
            else:
                change = credit - prices[item]
                pool = {d: coins[d] + escrow.get(d, 0) for d in denoms}
                rem = change
                used = {}
                for d in denoms:
                    k = min(pool[d], rem // d)
                    used[d] = k
                    rem -= k * d
                if rem != 0:
                    out.append("EXACT_CHANGE_ONLY")
                else:
                    for d in denoms:
                        coins[d] = pool[d] - used[d]
                    stock[item] -= 1
                    credit = 0
                    escrow = {}
                    out.append("VEND %s %d" % (item, change))
    return [out, [[d, coins[d]] for d in denoms]]
''',
    tests=[
        [{"gum": 35}, {"gum": 1}, [[25, 0], [10, 1], [5, 0]], [["coin", 25], ["coin", 25], ["select", "gum"], ["select", "gum"]]],
        [_PRICES, {"cola": 2, "chips": 1, "gum": 0}, _BANK, [["coin", 100], ["coin", 25], ["select", "cola"]]],
        [_PRICES, {"cola": 2, "chips": 1, "gum": 0}, _BANK, []],
        [_PRICES, {"cola": 2, "chips": 1, "gum": 0}, _BANK, [["select", "gum"], ["select", "tea"], ["select", "cola"], ["refund"]]],
        [_PRICES, {"cola": 2, "chips": 1, "gum": 0}, _BANK, [["coin", 100], ["select", "chips"], ["select", "chips"], ["coin", 100], ["select", "chips"], ["refund"]]],
        [_PRICES, {"cola": 1, "chips": 1, "gum": 5}, _BANK, [["coin", 50], ["coin", 1], ["coin", 25], ["refund"], ["refund"]]],
        [_PRICES, {"cola": 1, "chips": 1, "gum": 5}, [[100, 0], [25, 0], [10, 0], [5, 0]], [["coin", 25], ["coin", 10], ["select", "gum"], ["coin", 25], ["coin", 25], ["select", "gum"], ["select", "gum"]]],
        [{"gum": 35}, {"gum": 3}, [[25, 1], [10, 3], [5, 0]], [["coin", 25], ["coin", 25], ["coin", 10], ["coin", 5], ["select", "gum"]]],
        [{"gum": 35}, {"gum": 3}, [[25, 0], [10, 0], [5, 0]], [["coin", 10], ["coin", 10], ["coin", 10], ["coin", 10], ["select", "gum"], ["refund"], ["coin", 25], ["coin", 5], ["coin", 5], ["select", "gum"], ["coin", 10], ["coin", 10], ["coin", 10], ["coin", 10], ["select", "gum"]]],
        [_PRICES, {"cola": 1, "chips": 0, "gum": 1}, _BANK, [["coin", 25], ["select", "chips"], ["select", "cola"], ["coin", 100], ["select", "cola"], ["coin", 100], ["select", "cola"], ["select", "gum"]]],
        [{"x": 0}, {"x": 2}, [[5, 0]], [["select", "x"], ["coin", 5], ["select", "x"], ["select", "x"]]],
        [{"tea": 60}, {"tea": 50}, [[50, 0], [20, 0], [10, 0]], [e for _ in range(20) for e in (["coin", 50], ["coin", 20], ["select", "tea"], ["coin", 50], ["coin", 50], ["select", "tea"], ["refund"])]],
        [{"gum": 35}, {"gum": 2}, [[25, 1], [10, 3], [5, 0]], [["coin", 25], ["coin", 25], ["coin", 25], ["select", "gum"], ["refund"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def vending(prices, stock, bank, events):
    coins = {d: c for d, c in bank}
    denoms = sorted(coins, reverse=True)
    stock = dict(stock); credit = 0; escrow = {}; out = []
    for ev in events:
        if ev[0] == "coin":
            v = ev[1]
            if v not in coins:
                out.append("REJECT %d" % v)
            else:
                escrow[v] = escrow.get(v, 0) + 1; credit += v
                out.append("CREDIT %d" % credit)
        elif ev[0] == "refund":
            out.append("REFUND %d" % credit); credit = 0; escrow = {}
        else:
            item = ev[1]
            if item not in prices:
                out.append("INVALID")
            elif stock.get(item, 0) == 0:
                out.append("SOLD_OUT")
            elif credit < prices[item]:
                out.append("NEED %d" % (prices[item] - credit))
            else:
                change = credit - prices[item]
                for d in escrow:
                    coins[d] += escrow[d]
                rem = change
                for d in denoms:
                    k = min(coins[d], rem // d)
                    coins[d] -= k; rem -= k * d
                stock[item] -= 1; credit = 0; escrow = {}
                out.append("VEND %s %d" % (item, change))
    return [out, [[d, coins[d]] for d in denoms]]
''',
        '''def vending(prices, stock, bank, events):
    coins = {d: c for d, c in bank}
    denoms = sorted(coins, reverse=True)
    stock = dict(stock); credit = 0; escrow = {}; out = []
    for ev in events:
        if ev[0] == "coin":
            v = ev[1]
            if v not in coins:
                out.append("REJECT %d" % v)
            else:
                escrow[v] = escrow.get(v, 0) + 1; credit += v
                out.append("CREDIT %d" % credit)
        elif ev[0] == "refund":
            out.append("REFUND %d" % credit); credit = 0; escrow = {}
        else:
            item = ev[1]
            if item not in prices:
                out.append("INVALID")
            elif credit < prices[item]:
                out.append("NEED %d" % (prices[item] - credit))
            elif stock.get(item, 0) == 0:
                out.append("SOLD_OUT")
            else:
                change = credit - prices[item]
                pool = {d: coins[d] + escrow.get(d, 0) for d in denoms}
                rem = change; used = {}
                for d in denoms:
                    k = min(pool[d], rem // d); used[d] = k; rem -= k * d
                if rem:
                    out.append("EXACT_CHANGE_ONLY")
                else:
                    for d in denoms:
                        coins[d] = pool[d] - used[d]
                    stock[item] -= 1; credit = 0; escrow = {}
                    out.append("VEND %s %d" % (item, change))
    return [out, [[d, coins[d]] for d in denoms]]
''',
        '''def vending(prices, stock, bank, events):
    coins = {d: c for d, c in bank}
    denoms = sorted(coins, reverse=True)
    stock = dict(stock); credit = 0; escrow = {}; out = []
    for ev in events:
        if ev[0] == "coin":
            v = ev[1]
            if v not in coins:
                out.append("REJECT %d" % v)
            else:
                escrow[v] = escrow.get(v, 0) + 1; credit += v
                out.append("CREDIT %d" % credit)
        elif ev[0] == "refund":
            out.append("REFUND %d" % credit); credit = 0; escrow = {}
        else:
            item = ev[1]
            if item not in prices:
                out.append("INVALID")
            elif stock.get(item, 0) == 0:
                out.append("SOLD_OUT")
            elif credit < prices[item]:
                out.append("NEED %d" % (prices[item] - credit))
            else:
                change = credit - prices[item]
                rem = change; used = {}
                for d in denoms:
                    k = min(coins[d], rem // d); used[d] = k; rem -= k * d
                if rem:
                    out.append("EXACT_CHANGE_ONLY")
                else:
                    for d in denoms:
                        coins[d] += escrow.get(d, 0) - used[d]
                    stock[item] -= 1; credit = 0; escrow = {}
                    out.append("VEND %s %d" % (item, change))
    return [out, [[d, coins[d]] for d in denoms]]
''',
    ],
    guide=dict(
        prereqs="Lessons *Modelling a device as a state machine* and the vending-machine worked answer. Dicts.",
        intuition="The machine is a small state machine whose state is (credit, escrow, bank, stock). Each event is "
                  "a guarded transition: check the guards in the stated order, and only mutate state on the one "
                  "branch that succeeds.",
        hints=[
            "Keep four pieces of state: `credit`, an escrow counter per denomination, the bank counter, the stock.",
            "For a selection, compute the change on a *copy* (bank + escrow) so that a failed attempt changes nothing.",
            "Greedy change: for each denomination from largest to smallest take `min(available, remaining // d)`; "
            "succeed only if the remainder reaches zero.",
        ],
        brute_force="Model the bank as a flat list of individual coins and remove coins one at a time while making "
                    "change. It works, but each vend costs O(number of coins) instead of O(number of denominations).",
        approach="Process events in order with an `if/elif` ladder that mirrors the rule list.\n\n"
                 "**Dry run** of the example: coin 25 → credit 25; coin 25 → credit 50; select gum: price 35, change 15; "
                 "pool = 25×2, 10×1, 5×0; greedy: 25 does not fit 15, one 10 → 5 left, no 5s → remainder 5 → "
                 "`EXACT_CHANGE_ONLY`; nothing moved, so the bank is unchanged and the second select repeats the answer.",
        complexity="Time O(E · D) for E events and D denominations; space O(D + items).",
        pitfalls="- Mutating the bank before knowing whether change can be made.\n"
                 "- Forgetting that the customer's own coins are available for change.\n"
                 "- Checking price before stock (the spec says sold-out wins).\n"
                 "- Not clearing the escrow after a vend, so a later refund pays out twice.",
        follow_up="Replace greedy change-making with an exact bounded-coin search and count how many "
                  "`EXACT_CHANGE_ONLY` answers disappear.",
    ),
),
dict(
    id="think-validate-sequence",
    title="Validate an Event Sequence Against a Transition Table",
    difficulty="Easy",
    pattern="State Machines",
    entry="run_events",
    description=r"""
A deterministic state machine is given as a list of transitions `[from_state, event, to_state]` (no two
transitions share the same `from_state` and `event`). Starting in `start`, feed it `events` one by one.

- If every event has a transition from the current state, return `[final_state, -1]`.
- Otherwise stop at the first event with no transition and return `[state_at_that_moment, index]`
  where `index` is the 0-based position of the offending event.

**Example:** turnstile `[["locked","coin","unlocked"],["unlocked","push","locked"]]`, `start = "locked"`,
`events = ["coin","push","push"]` → `["locked", 2]` (pushing a locked turnstile is undefined here)

**Example:** same machine, `events = ["coin","push"]` → `["locked", -1]`

Constraints: up to `10^4` transitions and `10^5` events.
""",
    starter='''def run_events(transitions: List[List[str]], start: str, events: List[str]) -> list:
    pass
''',
    solution='''def run_events(transitions, start, events):
    table = {(a, e): b for a, e, b in transitions}
    state = start
    for i, e in enumerate(events):
        if (state, e) not in table:
            return [state, i]
        state = table[(state, e)]
    return [state, -1]
''',
    tests=[
        [_TURNSTILE[:2], "locked", ["coin", "push", "push"]],
        [_TURNSTILE[:2], "locked", ["coin", "push"]],
        [_TURNSTILE, "locked", []],
        [[], "idle", ["go"]],
        [[], "idle", []],
        [_TURNSTILE, "locked", ["push", "push", "coin", "coin", "push"]],
        [_ORDER, "new", ["pay", "ship", "deliver", "return"]],
        [_ORDER, "new", ["pay", "ship", "cancel"]],
        [_ORDER, "new", ["cancel", "pay"]],
        [_ORDER, "new", ["refund"]],
        [_DOOR, "closed", ["lock", "open"]],
        [_DOOR, "closed", ["lock", "unlock", "open", "close", "lock"]],
        [_RING, "s0", ["next"] * 20000 + ["reset"] + ["next"] * 3],
        [_RING, "s3", ["next", "next", "jump", "next"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def run_events(transitions, start, events):
    table = {(a, e): b for a, e, b in transitions}
    state = start
    for i, e in enumerate(events):
        if (state, e) in table:
            state = table[(state, e)]
    return [state, -1]
''',
        '''def run_events(transitions, start, events):
    table = {e: b for a, e, b in transitions}
    state = start
    for i, e in enumerate(events):
        if e not in table:
            return [state, i]
        state = table[e]
    return [state, -1]
''',
        '''def run_events(transitions, start, events):
    table = {(a, e): b for a, e, b in transitions}
    state = start
    for i, e in enumerate(events):
        if (state, e) not in table:
            return [state, i + 1]
        state = table[(state, e)]
    return [state, -1]
''',
    ],
    guide=dict(
        prereqs="Lesson *Modelling a device as a state machine*. Dict lookups with tuple keys.",
        intuition="A transition table is a function from (state, event) to the next state. Put it in a dictionary "
                  "and replay the events; the first missing key is the invalid transition.",
        hints=[
            "What is a natural dictionary key for 'in state S, on event E'?",
            "Build `{(from, event): to}` once, before the loop.",
            "Inside the loop: if the key is missing return `[state, i]`; otherwise move.",
        ],
        brute_force="For each event scan the whole transition list for a matching (state, event): O(E · T), up to "
                    "10⁹ comparisons at the limits.",
        approach="Dictionary plus a single pass.\n\n**Dry run** events coin, push, push from locked: coin → unlocked; "
                 "push → locked; push from locked has no entry → `['locked', 2]`.",
        complexity="Time O(T + E), space O(T).",
        pitfalls="- Silently ignoring an undefined event instead of stopping.\n- Keying on the event alone.\n"
                 "- Returning a 1-based index.",
        follow_up="Support guard conditions on transitions, or report *all* invalid events while staying in place.",
    ),
),
dict(
    id="think-transition-coverage",
    title="Cover Every Transition (0-Switch Coverage)",
    difficulty="Medium",
    pattern="State Machines",
    entry="cover_transitions",
    description=r"""
Given a deterministic state machine as transitions `[from_state, event, to_state]` and a `start` state,
design a set of **test sequences** that together exercise **every transition at least once**
(valid-transition coverage, also called 0-switch coverage).

Return a list of sequences; each sequence is a list of events that is replayed **from `start`**.

Your answer is accepted when

1. every event in every sequence is defined in the state the machine is in at that moment,
2. every transition in the table is taken by at least one sequence, and
3. the total number of events over all sequences is at most `T * S`, where `T` is the number of
   transitions and `S` the number of distinct states (including `start`).

Every transition is guaranteed to be reachable from `start`. For an empty table return `[]`.

**Example:** `[["locked","coin","unlocked"],["unlocked","push","locked"]]`, `start = "locked"` →
`[["coin", "push"]]` is valid (so is `[["coin"], ["coin", "push"]]`).
""",
    starter='''def cover_transitions(transitions: List[List[str]], start: str) -> List[List[str]]:
    pass
''',
    solution='''def cover_transitions(transitions, start):
    adj = collections.defaultdict(list)
    for a, e, b in transitions:
        adj[a].append((e, b))
    path = {start: []}
    queue = collections.deque([start])
    while queue:
        s = queue.popleft()
        for e, b in adj[s]:
            if b not in path:
                path[b] = path[s] + [e]
                queue.append(b)
    return [path[a] + [e] for a, e, b in transitions]
''',
    checker='''def check(args, got, expected):
    try:
        transitions, start = args
        table = {(a, e): b for a, e, b in transitions}
        states = {start} | {a for a, _, _ in transitions} | {b for _, _, b in transitions}
        if not isinstance(got, list):
            return False
        seen = set()
        total = 0
        for seq in got:
            if not isinstance(seq, list):
                return False
            s = start
            for e in seq:
                if not isinstance(e, str) or (s, e) not in table:
                    return False
                seen.add((s, e))
                s = table[(s, e)]
                total += 1
        return len(seen) == len(table) and total <= len(table) * len(states)
    except Exception:
        return False
''',
    tests=[
        [_TURNSTILE[:2], "locked"],
        [_TURNSTILE, "locked"],
        [[], "idle"],
        [_ORDER, "new"],
        [_DOOR, "closed"],
        [_DOOR, "locked"],
        [_RING, "s0"],
        [_RING, "s5"],
        [_LINE, "a"],
        [_LINE, "c"],
        [_STAR, "hub"],
        [_STAR, "leaf3"],
        [[["a", "x", "a"]], "a"],
    ],
    examples=2,
    wrong_solutions=[
        '''def cover_transitions(transitions, start):
    return [[e] for a, e, b in transitions]
''',
        '''def cover_transitions(transitions, start):
    table = {}
    for a, e, b in transitions:
        table.setdefault(a, []).append((e, b))
    seq, s, seen = [], start, set()
    while True:
        nxt = [(e, b) for e, b in table.get(s, []) if (s, e) not in seen]
        if not nxt:
            break
        e, b = nxt[0]
        seen.add((s, e)); seq.append(e); s = b
    return [seq]
''',
        '''def cover_transitions(transitions, start):
    return []
''',
    ],
    guide=dict(
        prereqs="Lesson *Deriving test paths and invalid transitions*; breadth-first search.",
        intuition="To exercise a transition you must first *get to* its source state. BFS from the start gives the "
                  "shortest event path to every state; append the transition's own event and you have one test per "
                  "transition.",
        hints=[
            "A single greedy walk can strand you in a state whose outgoing transitions are all used.",
            "Compute, for every state, the shortest list of events that reaches it from `start` (BFS).",
            "Return `path[from] + [event]` for each transition. Each has at most S events, so the total is ≤ T·S.",
        ],
        brute_force="Enumerate all event sequences up to some length and keep those that add coverage — exponential "
                    "in the length.",
        approach="1. Build adjacency lists.\n2. BFS from `start`, storing the event path to each state.\n"
                 "3. One sequence per transition.\n\n**Dry run** on the two-rule turnstile: paths locked=[], "
                 "unlocked=[coin]. Transition locked–coin → `[coin]`; transition unlocked–push → `[coin, push]`.",
        complexity="BFS is O(S + T); building outputs costs O(T · S) events in the worst case.",
        pitfalls="- Assuming you can jump straight to any state: every sequence restarts from `start`.\n"
                 "- A single walk that ends in a dead-end state (e.g. `cancelled`) before covering everything.\n"
                 "- Counting a transition as covered when only its event name was used from a different state.",
        follow_up="Minimise the total length (the Chinese Postman problem when the graph is strongly connected), "
                  "or extend to 1-switch coverage: every pair of consecutive transitions.",
    ),
),
dict(
    id="think-shortest-all-states",
    title="Shortest Test Sequence Visiting All States",
    difficulty="Hard",
    pattern="State Machines",
    entry="shortest_tour",
    description=r"""
Given transitions `[from_state, event, to_state]` and a `start` state, find the **minimum number of
events** in a single sequence, replayed from `start`, that visits **every state** at least once
(all-states coverage). The set of states is `start` plus every state named in the table; `start`
counts as visited before any event.

Return that minimum, or `-1` if no single sequence can visit all states.

**Example:** `[["a","f","b"],["b","f","c"],["b","r","a"],["c","r","b"]]`, `start = "b"` → `3`
(for instance `r, f, f`: b → a → b → c)

**Example:** `[["new","pay","paid"],["new","cancel","cancelled"]]`, `start = "new"` → `-1`

Constraints: at most 12 states and 100 transitions.
""",
    starter='''def shortest_tour(transitions: List[List[str]], start: str) -> int:
    pass
''',
    solution='''def shortest_tour(transitions, start):
    names = [start]
    for a, _, b in transitions:
        for s in (a, b):
            if s not in names:
                names.append(s)
    idx = {s: i for i, s in enumerate(names)}
    adj = [set() for _ in names]
    for a, _, b in transitions:
        adj[idx[a]].add(idx[b])
    full = (1 << len(names)) - 1
    seen = {(0, 1)}
    queue = collections.deque([(0, 1, 0)])
    while queue:
        s, mask, d = queue.popleft()
        if mask == full:
            return d
        for t in adj[s]:
            key = (t, mask | (1 << t))
            if key not in seen:
                seen.add(key)
                queue.append((t, key[1], d + 1))
    return -1
''',
    tests=[
        [[["a", "f", "b"], ["b", "f", "c"], ["b", "r", "a"], ["c", "r", "b"]], "b"],
        [[["new", "pay", "paid"], ["new", "cancel", "cancelled"]], "new"],
        [[], "only"],
        [[["a", "x", "a"]], "a"],
        [_TURNSTILE, "locked"],
        [_ORDER, "new"],
        [_DOOR, "closed"],
        [_DOOR, "opened"],
        [_RING, "s0"],
        [_LINE, "a"],
        [_LINE, "c"],
        [_STAR, "hub"],
        [_STAR, "leaf2"],
        [[["m", "e1", "a1"], ["a1", "e2", "a2"], ["a2", "e3", "a3"], ["a3", "b", "a2"], ["a2", "b", "a1"], ["a1", "b", "m"], ["m", "z", "zz"], ["zz", "b", "m"]], "m"],
        [[["s%d" % i, "e%d" % j, "s%d" % j] for i in range(12) for j in range(12) if (i * 5 + j * 3) % 4 == 0 and i != j], "s0"],
    ],
    examples=2,
    wrong_solutions=[
        '''def shortest_tour(transitions, start):
    states = {start} | {a for a, _, _ in transitions} | {b for _, _, b in transitions}
    return len(states) - 1
''',
        '''def shortest_tour(transitions, start):
    adj = collections.defaultdict(set)
    states = {start}
    for a, _, b in transitions:
        adj[a].add(b); states |= {a, b}
    seen = {start}; s = start; d = 0
    while len(seen) < len(states):
        dist = {s: 0}; q = collections.deque([s]); target = None
        while q and target is None:
            u = q.popleft()
            for v in sorted(adj[u]):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    if v not in seen:
                        target = v
                        break
                    q.append(v)
        if target is None:
            return -1
        d += dist[target]; seen.add(target); s = target
    return d
''',
        '''def shortest_tour(transitions, start):
    adj = collections.defaultdict(set)
    states = {start}
    for a, _, b in transitions:
        adj[a].add(b); states |= {a, b}
    best = [-1]
    def dfs(s, seen, d):
        if len(seen) == len(states):
            if best[0] < 0 or d < best[0]:
                best[0] = d
            return
        for v in adj[s]:
            if v not in seen:
                dfs(v, seen | {v}, d + 1)
    dfs(start, {start}, 0)
    return best[0]
''',
    ],
    guide=dict(
        prereqs="Lesson *Deriving test paths and invalid transitions*. BFS; bitmasks (see the DSA track on "
                "shortest path visiting all nodes).",
        intuition="Where you are is not enough to know how far along you are; you also need *which states you have "
                  "already seen*. Search over the pair (current state, visited set). BFS over those pairs finds the "
                  "fewest events.",
        hints=[
            "Revisiting a state is sometimes necessary (think of a hub with dead-end spokes that return).",
            "Number the states and store the visited set as a bitmask; a search node is `(state, mask)`.",
            "BFS from `(start, 1 << start_index)`; the first time `mask` is all ones, the depth is the answer.",
        ],
        brute_force="Try all orders in which to first visit the states (S! permutations) and sum the shortest-path "
                    "distances between consecutive ones: 12! ≈ 479 million orders — too slow.",
        approach="1. Index the states, with `start` as 0.\n2. BFS over `(state, mask)` with a visited set.\n"
                 "3. Return the depth on reaching the full mask, else −1.\n\n**Dry run** example 1 from b: "
                 "(b,{b}) → (a,{a,b}) or (c,{b,c}) at depth 1; from (a,{a,b}) → (b,{a,b}) at depth 2 → (c, all) at depth 3.",
        complexity="At most S · 2^S nodes (12 · 4096 ≈ 49k), each expanding ≤ S neighbours: O(S² · 2^S) time, "
                   "O(S · 2^S) space.",
        pitfalls="- Assuming the answer is S − 1 (true only when a simple path exists).\n"
                 "- Greedy 'go to the nearest unseen state', which can be longer than optimal.\n"
                 "- A DFS that refuses to revisit states, returning −1 on a star-shaped machine.\n"
                 "- Forgetting `start` when it has no transitions at all.",
        follow_up="Return the event sequence itself, or minimise events needed to cover all *transitions*.",
    ),
),
dict(
    id="think-elevator-scheduler",
    title="Elevator Request Scheduler (LOOK)",
    difficulty="Easy",
    pattern="Scenario Modelling",
    entry="elevator_plan",
    description=r"""
A single elevator car sits at floor `start`, currently heading in `direction` (`"up"` or `"down"`).
`requests` lists the floors people have asked for (duplicates possible). Using the **LOOK** policy the
car:

1. serves a request for the current floor immediately (if any);
2. keeps moving in its current direction, stopping at each requested floor in that direction in
   order, as far as the furthest request;
3. then reverses and serves the remaining requests in order.

If there is nothing to serve in the current direction it simply reverses at once.

Return `[stops, travelled]`: the floors in the order they are served (each floor once) and the total
number of floors moved.

**Example:** `start = 5, direction = "up", requests = [3, 8, 6, 1, 8]` → `[[6, 8, 3, 1], 10]`
(up 3 floors to 8, then down 7 floors to 1)

**Example:** `start = 4, direction = "down", requests = [4, 9]` → `[[4, 9], 5]`

Constraints: floors are integers in `[-5, 200]`; up to `10^5` requests.
""",
    starter='''def elevator_plan(start: int, direction: str, requests: List[int]) -> list:
    pass
''',
    solution='''def elevator_plan(start, direction, requests):
    floors = set(requests)
    above = sorted(f for f in floors if f > start)
    below = sorted((f for f in floors if f < start), reverse=True)
    stops = [start] if start in floors else []
    stops += above + below if direction == "up" else below + above
    travelled, pos = 0, start
    for f in stops:
        travelled += abs(f - pos)
        pos = f
    return [stops, travelled]
''',
    tests=[
        [5, "up", [3, 8, 6, 1, 8]],
        [4, "down", [4, 9]],
        [0, "up", []],
        [5, "down", [3, 8, 6, 1, 8]],
        [5, "up", [1, 2, 3]],
        [5, "down", [9, 7]],
        [10, "up", [10, 10, 10]],
        [0, "down", [-2, 3, -5, 0]],
        [1, "up", [200, -5]],
        [1, "down", [200, -5]],
        [7, "up", [6, 8]],
        [100, "down", list(range(0, 200, 3)) * 3],
        [50, "up", [(i * 37) % 201 - 5 for i in range(5000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def elevator_plan(start, direction, requests):
    stops, pos, travelled = [], start, 0
    for f in requests:
        if f not in stops:
            stops.append(f); travelled += abs(f - pos); pos = f
    return [stops, travelled]
''',
        '''def elevator_plan(start, direction, requests):
    floors = set(requests)
    above = sorted(f for f in floors if f > start)
    below = sorted(f for f in floors if f < start)
    stops = [start] if start in floors else []
    stops += above + below if direction == "up" else below + above
    travelled, pos = 0, start
    for f in stops:
        travelled += abs(f - pos); pos = f
    return [stops, travelled]
''',
        '''def elevator_plan(start, direction, requests):
    floors = set(requests)
    above = sorted(f for f in floors if f >= start)
    below = sorted((f for f in floors if f < start), reverse=True)
    stops = above + below if direction == "up" else below + above
    travelled, pos = 0, start
    for f in stops:
        travelled += abs(f - pos); pos = f
    return [stops, travelled]
''',
    ],
    guide=dict(
        prereqs="The elevator worked answer in *Testing physical products*. Sorting.",
        intuition="LOOK is a sweep: everything on the current side in travel order, then everything on the other "
                  "side in the opposite order. No simulation of individual floors is needed.",
        hints=[
            "Remove duplicates first; a floor is served once.",
            "Split the floors into those above and those below the start. In what order is each group visited?",
            "Above is ascending, below is descending; concatenate according to `direction`, with the start floor first if requested.",
        ],
        brute_force="Simulate floor by floor: move one floor at a time, check whether it is requested, reverse when "
                    "nothing remains ahead. O(range of floors) per sweep and easy to get wrong at the turn-around.",
        approach="Set → two sorted lists → concatenate → sum of absolute differences.\n\n**Dry run** start 5 up, "
                 "requests {1,3,6,8}: above [6,8], below [3,1]; stops [6,8,3,1]; distance 1+2+5+2 = 10.",
        complexity="Time O(n log n) for sorting distinct floors, space O(n).",
        pitfalls="- First-come-first-served order (that is FCFS, not LOOK).\n"
                 "- Sorting the lower group ascending, making the car jump to the bottom first.\n"
                 "- Putting the current floor in the wrong place when the direction is down.",
        follow_up="Compare total travel with FCFS and with SCAN (which always runs to the end of the shaft).",
    ),
),
dict(
    id="think-atm-withdraw",
    title="ATM Withdrawal with Denominations and Limits",
    difficulty="Medium",
    pattern="Scenario Modelling",
    entry="atm_withdraw",
    description=r"""
Decide what an ATM does for a withdrawal request.

- `amount`: requested amount (integer).
- `cassettes`: list of `[denomination, notes_available]` (distinct denominations, any order).
- `balance`: the customer's account balance. `daily_left`: how much of today's limit remains.

Checks, **in this order** — return the first error that applies, as a string:

1. `amount <= 0` → `"INVALID_AMOUNT"`
2. `amount > daily_left` → `"LIMIT_EXCEEDED"`
3. `amount > balance` → `"INSUFFICIENT_FUNDS"`
4. the notes in the cassettes cannot form the amount exactly → `"CANNOT_DISPENSE"`

Otherwise return the notes to dispense as `[[denomination, count], ...]` in **descending denomination
order, omitting zero counts**, choosing the combination with the **fewest notes**. If several
combinations tie, prefer the one using more notes of the largest denomination, then more of the next
largest, and so on.

**Example:** `amount = 60, cassettes = [[50, 10], [20, 10]], balance = 500, daily_left = 300` →
`[[20, 3]]` (taking a 50 first leaves 10, which cannot be paid)

**Example:** `amount = 120, cassettes = [[50, 1], [20, 10], [100, 1]], balance = 1000, daily_left = 1000`
→ `[[100, 1], [20, 1]]`

Constraints: at most 4 denominations, at most 40 notes per cassette, `amount <= 10^5`.
""",
    starter='''def atm_withdraw(amount: int, cassettes: List[List[int]], balance: int, daily_left: int):
    pass
''',
    solution='''def atm_withdraw(amount, cassettes, balance, daily_left):
    if amount <= 0:
        return "INVALID_AMOUNT"
    if amount > daily_left:
        return "LIMIT_EXCEEDED"
    if amount > balance:
        return "INSUFFICIENT_FUNDS"
    cs = sorted(cassettes, reverse=True)
    best = [None, 0]
    counts = [0] * len(cs)

    def go(i, rem, used):
        if best[0] is not None and used >= best[1]:
            return
        if rem == 0:
            best[0], best[1] = counts[:i] + [0] * (len(cs) - i), used
            return
        if i == len(cs):
            return
        d, avail = cs[i]
        for k in range(min(avail, rem // d), -1, -1):
            counts[i] = k
            go(i + 1, rem - k * d, used + k)
        counts[i] = 0

    go(0, amount, 0)
    if best[0] is None:
        return "CANNOT_DISPENSE"
    return [[cs[i][0], best[0][i]] for i in range(len(cs)) if best[0][i]]
''',
    tests=[
        [60, [[50, 10], [20, 10]], 500, 300],
        [120, [[50, 1], [20, 10], [100, 1]], 1000, 1000],
        [0, [[20, 5]], 100, 100],
        [-20, [[20, 5]], 100, 100],
        [400, [[20, 50]], 300, 200],
        [250, [[20, 50]], 200, 300],
        [30, [[20, 5], [50, 5]], 100, 100],
        [100, [[20, 4]], 500, 500],
        [100, [[20, 5]], 100, 100],
        [200, [[100, 1], [50, 2], [20, 5]], 1000, 1000],
        [80, [[50, 3], [20, 10], [10, 0]], 1000, 1000],
        [110, [[50, 3], [20, 10], [100, 5]], 1000, 1000],
        [300, [[100, 2], [60, 5], [50, 4]], 1000, 1000],
        [1990, [[100, 40], [50, 40], [20, 40], [10, 1]], 5000, 2000],
        [40, [], 100, 100],
        [150, [[100, 1], [75, 2], [50, 1]], 1000, 1000],
    ],
    examples=2,
    wrong_solutions=[
        '''def atm_withdraw(amount, cassettes, balance, daily_left):
    if amount <= 0:
        return "INVALID_AMOUNT"
    if amount > daily_left:
        return "LIMIT_EXCEEDED"
    if amount > balance:
        return "INSUFFICIENT_FUNDS"
    out, rem = [], amount
    for d, avail in sorted(cassettes, reverse=True):
        k = min(avail, rem // d)
        if k:
            out.append([d, k]); rem -= k * d
    return out if rem == 0 else "CANNOT_DISPENSE"
''',
        '''def atm_withdraw(amount, cassettes, balance, daily_left):
    if amount <= 0:
        return "INVALID_AMOUNT"
    if amount > balance:
        return "INSUFFICIENT_FUNDS"
    if amount > daily_left:
        return "LIMIT_EXCEEDED"
    cs = sorted(cassettes, reverse=True)
    best = [None, 0]
    counts = [0] * len(cs)

    def go(i, rem, used):
        if best[0] is not None and used >= best[1]:
            return
        if rem == 0:
            best[0], best[1] = counts[:i] + [0] * (len(cs) - i), used
            return
        if i == len(cs):
            return
        d, avail = cs[i]
        for k in range(min(avail, rem // d), -1, -1):
            counts[i] = k
            go(i + 1, rem - k * d, used + k)
        counts[i] = 0

    go(0, amount, 0)
    if best[0] is None:
        return "CANNOT_DISPENSE"
    return [[cs[i][0], best[0][i]] for i in range(len(cs)) if best[0][i]]
''',
        '''def atm_withdraw(amount, cassettes, balance, daily_left):
    if amount <= 0:
        return "INVALID_AMOUNT"
    if amount > daily_left:
        return "LIMIT_EXCEEDED"
    if amount > balance:
        return "INSUFFICIENT_FUNDS"
    cs = sorted(cassettes, reverse=True)
    best = [None, 0]
    counts = [0] * len(cs)

    def go(i, rem, used):
        if best[0] is not None and used >= best[1]:
            return
        if rem == 0:
            best[0], best[1] = counts[:i] + [0] * (len(cs) - i), used
            return
        if i == len(cs):
            return
        d, avail = cs[i]
        for k in range(0, min(avail, rem // d) + 1):
            counts[i] = k
            go(i + 1, rem - k * d, used + k)
        counts[i] = 0

    go(0, amount, 0)
    if best[0] is None:
        return "CANNOT_DISPENSE"
    return [[cs[i][0], best[0][i]] for i in range(len(cs)) if best[0][i]]
''',
    ],
    guide=dict(
        prereqs="The ATM worked answer in *Testing physical products*; backtracking; why greedy coin change fails.",
        intuition="The validation ladder is a tiny decision table — order matters. The dispensing part is bounded "
                  "coin change: greedy 'biggest note first' is wrong for sets like {50, 20}, so search over how many "
                  "of each note to use, biggest first, and keep the combination with the fewest notes.",
        hints=[
            "Write the four checks first and test them; they are independent of the note search.",
            "Try 60 with notes {50, 20} by hand. Why does grabbing the 50 fail?",
            "Recurse over denominations in descending order, trying the count from the maximum down to 0. Record a "
            "solution only if it uses strictly fewer notes than the best so far — the first one found among ties "
            "is automatically the one preferring large notes.",
        ],
        brute_force="Enumerate every count vector with `itertools.product(range(avail+1) ...)`: up to 41⁴ ≈ 2.8 "
                    "million combinations. Correct if you apply the tie-break, but slow.",
        approach="Depth-first search with pruning (`used >= best` → stop).\n\n**Dry run** 60 with 50×10, 20×10: "
                 "try one 50 → remaining 10 → zero 20s → remainder 10, dead end. Try zero 50s → three 20s → remainder 0 "
                 "→ answer `[[20, 3]]`.",
        complexity="Worst case O(Π(counts)) but pruning by note count cuts it sharply; ≤ 40³ leaf checks here. "
                   "Space O(number of denominations).",
        pitfalls="- Greedy dispensing.\n- Ignoring cassette counts (an empty cassette still has a denomination).\n"
                 "- Checking balance before the daily limit — the spec orders the errors.\n"
                 "- Emitting zero-count entries or ascending order.",
        follow_up="Real ATMs sometimes prefer a *mix* of notes to preserve small denominations — redefine the "
                  "objective and see how the search changes.",
    ),
),
]
