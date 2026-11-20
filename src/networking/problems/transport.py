def _hs(c=100, s=300):
    return [["C", "SYN", c, 0, 0], ["S", "SYN+ACK", s, c + 1, 0], ["C", "ACK", c + 1, s + 1, 0]]


PROBLEMS = [
dict(
    id="net-tcp-handshake-validate",
    title="Validate a TCP Segment Trace",
    difficulty="Medium",
    pattern="TCP",
    entry="tcp_trace_check",
    description=r"""
You are given a capture of one TCP connection on a loss-free, in-order path. Each segment is
`[sender, flags, seq, ack, length]` where `sender` is `"C"` (client) or `"S"` (server), `flags` is one of
`"SYN"`, `"SYN+ACK"`, `"ACK"`, `"FIN+ACK"`, and `length` is the number of payload bytes.

Return `-1` if the whole trace obeys the rules below, otherwise the **index of the first segment that breaks
a rule**. If the trace ends before the three-way handshake is complete, return `len(segments)` (the index
where the missing segment should have been).

**Handshake** (segments 0, 1, 2):

0. from `C`, flags `SYN`, length 0. The client's next sequence number becomes `seq + 1` (a SYN consumes one number).
1. from `S`, flags `SYN+ACK`, length 0, `ack` equal to the client's next sequence number. The server's next becomes `seq + 1`.
2. from `C`, flags `ACK`, length 0, `seq` equal to the client's next, `ack` equal to the server's next.

**After the handshake**, every segment from side X (peer Y) must satisfy all of:

- flags are `ACK` or `FIN+ACK`;
- `seq` equals X's next sequence number;
- `ack` is at most Y's next sequence number (you cannot acknowledge bytes never sent) and at least the last `ack` value X sent (acknowledgements never move backwards). The last `ack` sent by C starts at the value in segment 2; by S, at the value in segment 1;
- if X has already sent a FIN, the segment must be a plain `ACK` with length 0.

Then X's next sequence number grows by `length`, plus 1 if the segment carries FIN.

**Example:** `[["C","SYN",100,0,0], ["S","SYN+ACK",300,101,0], ["C","ACK",101,301,0], ["C","ACK",101,301,5], ["S","ACK",301,106,0]]` → `-1`

**Example:** the same trace with the server's last ack changed to `107` → `4`
""",
    starter='''def tcp_trace_check(segments: list) -> int:
    pass
''',
    solution='''def tcp_trace_check(segments):
    n = len(segments)
    if n == 0:
        return 0
    s = segments[0]
    if not (s[0] == "C" and s[1] == "SYN" and s[4] == 0):
        return 0
    nxt = {"C": s[2] + 1}
    if n == 1:
        return 1
    s = segments[1]
    if not (s[0] == "S" and s[1] == "SYN+ACK" and s[3] == nxt["C"] and s[4] == 0):
        return 1
    nxt["S"] = s[2] + 1
    if n == 2:
        return 2
    s = segments[2]
    if not (s[0] == "C" and s[1] == "ACK" and s[2] == nxt["C"] and s[3] == nxt["S"] and s[4] == 0):
        return 2
    last_ack = {"C": nxt["S"], "S": nxt["C"]}
    fin = {"C": False, "S": False}
    for i in range(3, n):
        who, flags, seq, ack, ln = segments[i]
        peer = "S" if who == "C" else "C"
        if flags not in ("ACK", "FIN+ACK"):
            return i
        if seq != nxt[who]:
            return i
        if ack > nxt[peer] or ack < last_ack[who]:
            return i
        if fin[who] and (ln > 0 or flags == "FIN+ACK"):
            return i
        nxt[who] += ln
        if flags == "FIN+ACK":
            nxt[who] += 1
            fin[who] = True
        last_ack[who] = ack
    return -1
''',
    tests=[
        [_hs() + [["C", "ACK", 101, 301, 5], ["S", "ACK", 301, 106, 0]]],
        [_hs() + [["C", "ACK", 101, 301, 5], ["S", "ACK", 301, 107, 0]]],
        [[]],
        [_hs()[:1]],
        [_hs()[:2]],
        [_hs()],
        [[["S", "SYN", 1, 0, 0]] + _hs()[1:]],
        [[["C", "SYN", 100, 0, 0], ["S", "SYN+ACK", 300, 100, 0], ["C", "ACK", 101, 301, 0]]],
        [[["C", "SYN", 100, 0, 0], ["S", "SYN+ACK", 300, 101, 0], ["C", "ACK", 100, 301, 0]]],
        [_hs(0, 0) + [["C", "ACK", 1, 1, 10], ["S", "ACK", 1, 11, 20], ["C", "ACK", 11, 21, 0],
                      ["C", "FIN+ACK", 11, 21, 0], ["S", "ACK", 21, 12, 0], ["S", "FIN+ACK", 21, 12, 0], ["C", "ACK", 12, 22, 0]]],
        [_hs(0, 0) + [["C", "ACK", 1, 1, 10], ["S", "ACK", 1, 11, 20], ["C", "FIN+ACK", 11, 21, 0], ["C", "ACK", 12, 21, 4]]],
        [_hs(0, 0) + [["C", "ACK", 1, 1, 10], ["S", "ACK", 1, 11, 0], ["S", "ACK", 1, 5, 7]]],
        [_hs(0, 0) + [["C", "ACK", 1, 1, 10], ["C", "ACK", 10, 1, 10]]],
        [_hs(0, 0) + [["C", "FIN+ACK", 1, 1, 3], ["S", "ACK", 1, 5, 0], ["S", "ACK", 1, 5, 8], ["C", "ACK", 5, 9, 0]]],
        [_hs(7, 9) + [["S", "SYN+ACK", 10, 8, 0]]],
        [_hs(4000000000, 5) + [["C", "ACK", 4000000001, 6, 1000 + i * 0] for i in range(1)] + [["S", "ACK", 6, 4000001001, 0]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def tcp_trace_check(segments):
    n = len(segments)
    if n == 0:
        return 0
    s = segments[0]
    if not (s[0] == "C" and s[1] == "SYN" and s[4] == 0):
        return 0
    nxt = {"C": s[2] + 1}
    if n == 1:
        return 1
    s = segments[1]
    if not (s[0] == "S" and s[1] == "SYN+ACK" and s[3] == nxt["C"] and s[4] == 0):
        return 1
    nxt["S"] = s[2] + 1
    if n == 2:
        return 2
    s = segments[2]
    if not (s[0] == "C" and s[1] == "ACK" and s[2] == nxt["C"] and s[3] == nxt["S"] and s[4] == 0):
        return 2
    for i in range(3, n):
        who, flags, seq, ack, ln = segments[i]
        if flags not in ("ACK", "FIN+ACK"):
            return i
        if seq != nxt[who]:
            return i
        nxt[who] += ln + (1 if flags == "FIN+ACK" else 0)
    return -1
''',
        '''def tcp_trace_check(segments):
    n = len(segments)
    if n < 3:
        return n
    nxt = {"C": segments[0][2] + 1, "S": segments[1][2] + 1}
    last_ack = {"C": nxt["S"], "S": nxt["C"]}
    fin = {"C": False, "S": False}
    for i in range(3, n):
        who, flags, seq, ack, ln = segments[i]
        peer = "S" if who == "C" else "C"
        if flags not in ("ACK", "FIN+ACK") or seq != nxt[who]:
            return i
        if ack > nxt[peer] or ack < last_ack[who]:
            return i
        if fin[who] and (ln > 0 or flags == "FIN+ACK"):
            return i
        nxt[who] += ln
        if flags == "FIN+ACK":
            nxt[who] += 1
            fin[who] = True
        last_ack[who] = ack
    return -1
''',
    ],
    guide=dict(
        prereqs="The lesson *UDP and the TCP connection lifecycle*: sequence and acknowledgement numbers, SYN and FIN each consuming one sequence number.",
        intuition="Keep one counter per side: the next sequence number that side will use. A segment is legal when it starts exactly at its sender's counter and acknowledges no more than the peer's counter. SYN and FIN are 'phantom bytes' that advance the counter by one.",
        hints=[
            "Handle the first three segments as three explicit special cases; they have fixed senders and flags.",
            "After the handshake you need four pieces of state: `next[C]`, `next[S]`, the last ack each side sent, and whether each side has sent FIN.",
            "The acknowledgement must lie in the closed range `[last ack this side sent, peer's next]`.",
        ],
        brute_force="Re-derive each side's byte count from scratch for every segment by summing the lengths of all earlier segments: O(n²). Carrying running counters makes it one pass.",
        approach="""1. Check segments 0–2 against the handshake rules, returning the index of the first failure or `len(segments)` if the trace is too short.
2. Initialise the running state and scan the rest, applying the four established-state checks in order.
3. Advance the sender's counter by `length` (+1 for FIN) and remember its ack.

**Dry run** (example 1): after the handshake `next = {C:101, S:301}`. Segment 3: C sends 5 bytes at seq 101 ✓, ack 301 ≤ 301 ✓ → `next[C] = 106`. Segment 4: S at seq 301 ✓, ack 106 ≤ 106 ✓. Result `-1`. With ack 107 the server would be acknowledging a byte the client never sent → index 4.""",
        complexity="Time O(n), space O(1).",
        pitfalls="Forgetting that SYN and FIN consume a sequence number (acks will look off by one). Checking only an upper bound on the ack. Allowing data after a FIN: a side that has sent FIN may still *receive* and acknowledge data (half-close) but may not send more.",
        follow_up="Extend the checker to tolerate retransmissions and out-of-order arrival, or to report the final state of each endpoint (ESTABLISHED, FIN_WAIT, TIME_WAIT, CLOSED).",
    ),
),
dict(
    id="net-cwnd-evolution",
    title="Congestion Window Evolution",
    difficulty="Medium",
    pattern="TCP",
    entry="cwnd_trace",
    description=r"""
Trace a simplified TCP Reno congestion window, measured in whole segments (MSS), one step per round trip.

The window starts at `cwnd = 1` with the given initial `ssthresh`. `events[i]` says what happened to the
window of data sent in round `i`:

- `"ok"`: everything was acknowledged.
  - If `cwnd < ssthresh` (slow start): `cwnd = min(2 * cwnd, ssthresh)`.
  - Otherwise (congestion avoidance): `cwnd = cwnd + 1`.
- `"3dup"`: loss detected by three duplicate ACKs (fast retransmit / fast recovery):
  `ssthresh = max(cwnd // 2, 2)`, then `cwnd = ssthresh`.
- `"timeout"`: loss detected by the retransmission timer:
  `ssthresh = max(cwnd // 2, 2)`, then `cwnd = 1`.

Return the list of `cwnd` values: the value at the start of every round followed by the final value
(so the result has `len(events) + 1` entries).

**Example:** `ssthresh = 8`, `events = ["ok","ok","ok","ok","3dup","ok"]` → `[1, 2, 4, 8, 9, 4, 5]`
""",
    starter='''def cwnd_trace(ssthresh: int, events: list) -> list:
    pass
''',
    solution='''def cwnd_trace(ssthresh, events):
    cwnd = 1
    out = [cwnd]
    for e in events:
        if e == "ok":
            if cwnd < ssthresh:
                cwnd = min(cwnd * 2, ssthresh)
            else:
                cwnd += 1
        elif e == "3dup":
            ssthresh = max(cwnd // 2, 2)
            cwnd = ssthresh
        else:
            ssthresh = max(cwnd // 2, 2)
            cwnd = 1
        out.append(cwnd)
    return out
''',
    tests=[
        [8, ["ok", "ok", "ok", "ok", "3dup", "ok"]],
        [16, []],
        [16, ["ok"] * 8],
        [6, ["ok"] * 6],
        [8, ["ok", "ok", "ok", "ok", "timeout", "ok", "ok", "ok", "ok"]],
        [1, ["ok", "ok", "ok"]],
        [64, ["timeout", "ok", "ok", "ok"]],
        [64, ["3dup", "ok", "ok", "ok"]],
        [10, ["ok"] * 7 + ["3dup"] + ["ok"] * 5 + ["timeout"] + ["ok"] * 6],
        [32, ["ok", "ok", "3dup", "3dup", "3dup", "ok", "ok"]],
        [12, ["ok"] * 10 + ["timeout", "timeout", "ok", "ok", "ok", "ok"]],
        [100, (["ok"] * 9 + ["3dup"]) * 12],
        [5, ["ok", "ok", "ok", "ok", "ok", "3dup", "ok", "timeout", "ok", "ok", "ok"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def cwnd_trace(ssthresh, events):
    cwnd = 1
    out = [cwnd]
    for e in events:
        if e == "ok":
            cwnd = cwnd * 2 if cwnd < ssthresh else cwnd + 1
        elif e == "3dup":
            ssthresh = max(cwnd // 2, 2)
            cwnd = ssthresh
        else:
            ssthresh = max(cwnd // 2, 2)
            cwnd = 1
        out.append(cwnd)
    return out
''',
        '''def cwnd_trace(ssthresh, events):
    cwnd = 1
    out = [cwnd]
    for e in events:
        if e == "ok":
            cwnd = min(cwnd * 2, ssthresh) if cwnd < ssthresh else cwnd + 1
        else:
            ssthresh = max(cwnd // 2, 2)
            cwnd = 1
        out.append(cwnd)
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Flow control and congestion control*: slow start, congestion avoidance, fast retransmit and recovery.",
        intuition="It is a tiny state machine with two variables. `ssthresh` remembers where trouble was last met; below it the window doubles, above it the window creeps up by one. A mild loss signal halves the window, a severe one collapses it to one.",
        hints=[
            "Record the window *before* applying each event, then append the final value once at the end (or start the list with 1 and append after each event).",
            "Slow start must not overshoot: cap the doubling at `ssthresh`.",
            "Both loss events set `ssthresh` from the *current* `cwnd` before changing `cwnd`.",
        ],
        brute_force="There is no asymptotically slower approach worth writing: the simulation is inherently one pass. A common first attempt handles only the `ok` case and bolts the loss cases on afterwards.",
        approach="""1. `cwnd = 1`, output `[1]`.
2. For each event update `(cwnd, ssthresh)` by the rule for that event, then append `cwnd`.

**Dry run** `ssthresh = 8`, events `ok ok ok ok 3dup ok`:

| round | cwnd before | event | ssthresh after | cwnd after |
|---|---|---|---|---|
| 0 | 1 | ok (slow start) | 8 | 2 |
| 1 | 2 | ok | 8 | 4 |
| 2 | 4 | ok | 8 | 8 |
| 3 | 8 | ok (avoidance) | 8 | 9 |
| 4 | 9 | 3dup | 4 | 4 |
| 5 | 4 | ok (avoidance, 4 ≥ 4) | 4 | 5 |""",
        complexity="Time O(n) for n events; space O(n) for the output.",
        pitfalls="Doubling past `ssthresh` (e.g. 4 → 8 when ssthresh is 6). Treating three duplicate ACKs like a timeout (that is TCP Tahoe). Computing the new `cwnd` before the new `ssthresh`. Using `<=` in the slow-start test: at `cwnd == ssthresh` the sender is already in congestion avoidance.",
        follow_up="Model CUBIC's cubic growth function, or count total segments delivered to compare the throughput of Tahoe and Reno on the same loss pattern.",
    ),
),
dict(
    id="net-sliding-window-sender",
    title="Sliding-Window Sender with Cumulative ACKs",
    difficulty="Medium",
    pattern="Reliable Delivery",
    entry="sender_trace",
    description=r"""
A sender must deliver packets numbered `0 .. total - 1` using a window of `window` packets and
Go-Back-N recovery. It keeps two counters: `base` (the oldest unacknowledged packet) and `next`
(the next never-sent packet). At any time it may have sent only packets `p` with `p < base + window`.

Whenever it is allowed to, the sender immediately transmits new packets in increasing order until the window
is full or nothing is left.

`events` is a list of integers processed in order:

- a value `a >= 0` is a **cumulative ACK**: the receiver has everything below `a`. If `base < a <= next`,
  set `base = a`; otherwise ignore it (stale or impossible).
- `-1` is a **timeout**: retransmit every outstanding packet `base .. next - 1` in order.

Return a list of lists: first the packets transmitted at start-up, then, for each event, the packets
transmitted in reaction to it (retransmissions first, then any new packets the window now allows).

**Example:** `total = 6`, `window = 3`, `events = [1, 3, -1, 6]` → `[[0,1,2], [3], [4,5], [3,4,5], []]`
""",
    starter='''def sender_trace(total: int, window: int, events: list) -> list:
    pass
''',
    solution='''def sender_trace(total, window, events):
    base = 0
    nxt = 0
    out = []

    def fill():
        nonlocal nxt
        sent = []
        while nxt < base + window and nxt < total:
            sent.append(nxt)
            nxt += 1
        return sent

    out.append(fill())
    for e in events:
        if e == -1:
            resend = list(range(base, nxt))
            out.append(resend + fill())
        else:
            if base < e <= nxt:
                base = e
            out.append(fill())
    return out
''',
    tests=[
        [6, 3, [1, 3, -1, 6]],
        [0, 4, [-1, 0]],
        [1, 1, []],
        [5, 1, [1, 2, 3, 4, 5]],
        [5, 10, [-1, 5, -1]],
        [8, 4, [2, 2, 1, 0, 4]],
        [8, 4, [9, 5, 4]],
        [8, 4, [3, 1, -1, 2, -1]],
        [10, 3, [-1, -1, 3, -1, 4, 6, 10]],
        [4, 2, [2, 4, -1, 4]],
        [7, 3, [3, 6, 7, -1]],
        [12, 5, [1, 2, 3, -1, 8, 7, 12]],
        [200, 16, [i for i in range(4, 201, 4)]],
        [50, 7, [(-1 if i % 4 == 3 else min(50, i * 3)) for i in range(30)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def sender_trace(total, window, events):
    base = nxt = 0
    out = []
    def fill():
        nonlocal nxt
        sent = []
        while nxt < base + window and nxt < total:
            sent.append(nxt)
            nxt += 1
        return sent
    out.append(fill())
    for e in events:
        if e == -1:
            out.append(list(range(base, nxt)) + fill())
        else:
            if e <= nxt:
                base = e
            out.append(fill())
    return out
''',
        '''def sender_trace(total, window, events):
    base = nxt = 0
    out = []
    def fill():
        nonlocal nxt
        sent = []
        while nxt < base + window and nxt < total:
            sent.append(nxt)
            nxt += 1
        return sent
    out.append(fill())
    for e in events:
        if e == -1:
            out.append(list(range(base, nxt)) + fill())
        else:
            if base < nxt:
                base += 1
            out.append(fill())
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Flow control and congestion control* (sliding windows); cumulative acknowledgements.",
        intuition="The window is the half-open range `[base, base + window)`. ACKs slide its left edge to the right, which opens room on the right for new packets. A timeout does not move the window; it just replays what is inside it.",
        hints=[
            "Write one helper that sends new packets while `next < base + window` and `next < total`; call it after every event.",
            "A cumulative ACK `a` can acknowledge several packets at once: set `base = a`, not `base += 1`.",
            "Ignore ACKs that do not advance `base` or that claim packets you never sent.",
        ],
        brute_force="Track a boolean 'acked' flag per packet and rescan from 0 on every event to find the window: O(total) per event. Two integer counters carry the same information.",
        approach="""1. `base = next = 0`; transmit the first window.
2. ACK `a`: if `base < a <= next` then `base = a`; then top the window up.
3. Timeout: output `base .. next-1`, then top up (normally nothing new fits).

**Dry run** `total=6, window=3, events=[1,3,-1,6]`:

| event | base | next | transmitted |
|---|---|---|---|
| start | 0 | 3 | 0 1 2 |
| ack 1 | 1 | 4 | 3 |
| ack 3 | 3 | 6 | 4 5 |
| timeout | 3 | 6 | 3 4 5 |
| ack 6 | 6 | 6 | (nothing) |""",
        complexity="Time O(total + number of retransmitted packets + events); space O(output).",
        pitfalls="Letting a stale ACK move `base` backwards (duplicates of old ACKs are normal). Accepting an ACK beyond `next`. Sending past `total`. Forgetting that a timeout with an empty window produces an empty list.",
        follow_up="Replace Go-Back-N with selective repeat (per-packet timers and a receiver buffer), or add a receiver-advertised window that changes with each ACK.",
    ),
),
dict(
    id="net-gbn-vs-sr",
    title="Go-Back-N vs Selective Repeat Transmission Counts",
    difficulty="Medium",
    pattern="Reliable Delivery",
    entry="gbn_vs_sr",
    description=r"""
Compare how many data transmissions two ARQ schemes need to deliver packets `0 .. n - 1` with window `window`.

Losses are described per attempt: `lost` contains pairs `[packet, attempt]` meaning the `attempt`-th
transmission (1-based) of that packet is lost. Acknowledgements are never lost, and every packet eventually
gets through.

Both protocols work in rounds, starting with `base = 0`:

**Go-Back-N.** While `base < n`: transmit packets `base .. min(base + window, n) - 1` in order (each counts as
one more attempt of that packet). The receiver accepts only in-order packets, so let `f` be the first packet
of this round whose transmission was lost. If there is one, set `base = f` (everything after it in the round
was wasted); otherwise `base` moves to the end of the round.

**Selective Repeat.** While `base < n`: transmit every packet in `base .. min(base + window, n) - 1` that has
**not yet been received** (one more attempt each); those not lost become received. Then advance `base` past
all consecutively received packets.

Return `[gbn_transmissions, sr_transmissions]`.

**Example:** `n = 5`, `window = 3`, `lost = [[1, 1]]` → `[7, 6]`

(GBN sends 0 1 2, loses 1, goes back and sends 1 2 3, then 4. SR sends 0 1 2, then 1 3 4.)
""",
    starter='''def gbn_vs_sr(n: int, window: int, lost: list) -> list:
    pass
''',
    solution='''def gbn_vs_sr(n, window, lost):
    lostset = set((p, a) for p, a in lost)
    att = [0] * n
    base = 0
    g = 0
    while base < n:
        end = min(base + window, n)
        first_lost = None
        for p in range(base, end):
            att[p] += 1
            g += 1
            if first_lost is None and (p, att[p]) in lostset:
                first_lost = p
        base = end if first_lost is None else first_lost
    att = [0] * n
    got = [False] * n
    base = 0
    s = 0
    while base < n:
        for p in range(base, min(base + window, n)):
            if not got[p]:
                att[p] += 1
                s += 1
                if (p, att[p]) not in lostset:
                    got[p] = True
        while base < n and got[base]:
            base += 1
    return [g, s]
''',
    tests=[
        [5, 3, [[1, 1]]],
        [0, 4, []],
        [10, 4, []],
        [1, 1, [[0, 1], [0, 2]]],
        [6, 1, [[2, 1], [4, 1]]],
        [8, 4, [[0, 1]]],
        [8, 4, [[3, 1]]],
        [8, 4, [[7, 1]]],
        [8, 8, [[0, 1], [0, 2], [0, 3]]],
        [10, 5, [[2, 1], [3, 1], [2, 2]]],
        [10, 5, [[4, 2]]],
        [12, 4, [[1, 1], [5, 1], [9, 1], [5, 2]]],
        [300, 16, [[i, 1] for i in range(0, 300, 7)]],
        [64, 10, [[i, a] for i in range(5, 64, 9) for a in (1, 2)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def gbn_vs_sr(n, window, lost):
    return [n + len(lost), n + len(lost)]
''',
        '''def gbn_vs_sr(n, window, lost):
    lostset = set((p, a) for p, a in lost)
    att = [0] * n
    base = 0
    g = 0
    while base < n:
        end = min(base + window, n)
        first_lost = None
        for p in range(base, end):
            att[p] += 1
            g += 1
            if (p, att[p]) in lostset:
                first_lost = p
        base = end if first_lost is None else first_lost
    att = [0] * n
    got = [False] * n
    base = 0
    s = 0
    while base < n:
        for p in range(base, min(base + window, n)):
            if not got[p]:
                att[p] += 1
                s += 1
                if (p, att[p]) not in lostset:
                    got[p] = True
        while base < n and got[base]:
            base += 1
    return [g, s]
''',
    ],
    guide=dict(
        prereqs="Problem *Sliding-Window Sender with Cumulative ACKs*; the difference between cumulative and selective acknowledgement.",
        intuition="Go-Back-N has a dumb receiver: one hole and everything after it must be sent again. Selective Repeat has a buffering receiver: only the holes are sent again. Simulate each literally, counting attempts per packet so the `lost` pairs can be consulted.",
        hints=[
            "Keep `attempts[p]` so you know which attempt number the current transmission of `p` is.",
            "In Go-Back-N, find the **first** lost packet of the round, but still count every packet of the round as transmitted.",
            "In Selective Repeat, keep a `received` flag per packet and skip received ones when re-sending the window.",
        ],
        brute_force="Simulate one packet per time step with explicit timers and ACK queues. It reaches the same counts with far more bookkeeping; the round model captures what matters.",
        approach="""1. Put the loss pairs in a set of tuples for O(1) lookup.
2. Run the Go-Back-N loop, then reset the attempt counters and run the Selective Repeat loop.

**Dry run** `n=5, window=3, lost={(1,1)}`:
- GBN: round 1 sends 0,1,2 (3 transmissions); packet 1's first attempt is lost → `base = 1`. Round 2 sends 1,2,3 (attempt 2 of packet 1 succeeds) → `base = 4`. Round 3 sends 4. Total 7.
- SR: round 1 sends 0,1,2; 0 and 2 received, `base = 1`. Round 2 covers 1..3: sends 1 and 3 (2 is already held) → `base = 4`. Round 3 sends 4. Total 6.""",
        complexity="Time O(total transmissions), which is O(n·window) in the worst case for GBN; space O(n + |lost|).",
        pitfalls="Assuming the answer is `n + len(lost)`: true for SR only when every listed loss is actually reached, and never for GBN. In GBN, taking the *last* lost packet of a round instead of the first. Forgetting to reset attempt counters between the two simulations.",
        follow_up="Why does real TCP sit between the two? Cumulative ACKs look like GBN, but receivers buffer out-of-order data and SACK lets the sender retransmit only the holes.",
    ),
),
dict(
    id="net-rto-estimator",
    title="RTT Estimation and Retransmission Timeout",
    difficulty="Medium",
    pattern="TCP",
    entry="rto_trace",
    compare="float",
    description=r"""
TCP picks its retransmission timeout from smoothed round-trip measurements (Jacobson/Karels, RFC 6298).
Implement the estimator for a list of RTT `samples` (milliseconds), in this exact order of operations:

- **First sample** `R`: `SRTT = R`, `RTTVAR = R / 2`.
- **Every later sample** `R`:
  1. `RTTVAR = 0.75 * RTTVAR + 0.25 * |SRTT - R|` (uses the **old** SRTT),
  2. `SRTT = 0.875 * SRTT + 0.125 * R`.
- After each sample: `RTO = SRTT + 4 * RTTVAR`, then clamp it into `[min_rto, max_rto]`.

Return a list with one `[SRTT, RTTVAR, RTO]` triple per sample (floats; answers are compared with a small tolerance).

**Example:** `samples = [100, 120]`, `min_rto = 200`, `max_rto = 60000`
→ `[[100, 50, 300], [102.5, 42.5, 272.5]]`
""",
    starter='''def rto_trace(samples: list, min_rto: float, max_rto: float) -> list:
    pass
''',
    solution='''def rto_trace(samples, min_rto, max_rto):
    out = []
    srtt = rttvar = None
    for r in samples:
        if srtt is None:
            srtt = float(r)
            rttvar = r / 2
        else:
            rttvar = 0.75 * rttvar + 0.25 * abs(srtt - r)
            srtt = 0.875 * srtt + 0.125 * r
        rto = srtt + 4 * rttvar
        rto = max(min_rto, min(max_rto, rto))
        out.append([srtt, rttvar, rto])
    return out
''',
    tests=[
        [[100, 120], 200, 60000],
        [[], 200, 60000],
        [[50], 200, 60000],
        [[50], 10, 60000],
        [[100] * 12, 1, 60000],
        [[100, 100, 100, 500, 100, 100], 200, 60000],
        [[20, 22, 19, 21, 20, 23, 18], 200, 60000],
        [[20, 22, 19, 21, 20, 23, 18], 1, 60000],
        [[1000, 3000, 9000, 27000], 1000, 20000],
        [[10, 200, 10, 200, 10, 200, 10, 200], 5, 500],
        [[0, 0, 0], 0, 100],
        [[(i * 37) % 90 + 30 for i in range(200)], 100, 3000],
        [[80 + (i % 5) * 3 for i in range(40)] + [900] + [80] * 20, 50, 5000],
    ],
    examples=1,
    wrong_solutions=[
        '''def rto_trace(samples, min_rto, max_rto):
    out = []
    srtt = rttvar = None
    for r in samples:
        if srtt is None:
            srtt = float(r)
            rttvar = r / 2
        else:
            srtt = 0.875 * srtt + 0.125 * r
            rttvar = 0.75 * rttvar + 0.25 * abs(srtt - r)
        rto = max(min_rto, min(max_rto, srtt + 4 * rttvar))
        out.append([srtt, rttvar, rto])
    return out
''',
        '''def rto_trace(samples, min_rto, max_rto):
    out = []
    srtt = rttvar = None
    for r in samples:
        if srtt is None:
            srtt = float(r)
            rttvar = 0.0
        else:
            rttvar = 0.75 * rttvar + 0.25 * abs(srtt - r)
            srtt = 0.875 * srtt + 0.125 * r
        rto = max(min_rto, min(max_rto, srtt + 4 * rttvar))
        out.append([srtt, rttvar, rto])
    return out
''',
    ],
    guide=dict(
        prereqs="Exponentially weighted moving averages; the lesson *Flow control and congestion control* (retransmission timers).",
        intuition="A timeout must be longer than a typical round trip, but by how much depends on how jumpy the path is. So TCP tracks two moving averages: the RTT itself and its mean deviation, and sets the timer to 'average plus four deviations'.",
        hints=[
            "The first sample is special: there is no history to smooth with.",
            "Update the variance term **before** the smoothed RTT, because it needs the old SRTT.",
            "Clamp last: `max(min_rto, min(max_rto, rto))`.",
        ],
        brute_force="Recompute a plain mean and standard deviation over all samples seen so far for each new sample: O(n²), and it reacts ever more slowly to change. The EWMA needs O(1) state and forgets old conditions.",
        approach="""1. On the first sample set `SRTT = R`, `RTTVAR = R/2`.
2. Afterwards apply the two EWMA updates in order (alpha = 1/8, beta = 1/4).
3. `RTO = SRTT + 4·RTTVAR`, clamped.

**Dry run** `[100, 120]`, min 200: sample 100 → SRTT 100, RTTVAR 50, RTO 300. Sample 120 → RTTVAR = 0.75·50 + 0.25·|100−120| = 42.5; SRTT = 87.5 + 15 = 102.5; RTO = 102.5 + 170 = 272.5.""",
        complexity="Time O(n), space O(1) besides the output.",
        pitfalls="Swapping the update order (the deviation is then measured against the already-updated mean). Initialising RTTVAR to 0, which makes the first RTO dangerously tight. Forgetting the clamp. Real TCP also applies Karn's rule: never sample the RTT of a retransmitted segment, and double the RTO on each timeout.",
        follow_up="Add exponential timer backoff: after each timeout the RTO doubles (up to `max_rto`) until a fresh, unambiguous sample arrives.",
    ),
),
]
