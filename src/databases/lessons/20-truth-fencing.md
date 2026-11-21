# Truth, majorities, fencing tokens and Byzantine faults

> **Before this lesson:** read [Partial failures and unreliable networks](#/lesson/databases/networks-faults) and [Unreliable clocks and process pauses](#/lesson/databases/clocks-pauses). You need: timeout, network partition, heartbeat, lease, process pause and garbage collection. Quorums and split brain come from the replication lessons ([Single-leader replication](#/lesson/databases/leader-follower), [Multi-leader and leaderless replication](#/lesson/databases/multi-leader-leaderless)).

## In plain words

The last two lessons showed that a machine in a distributed system can be wrong about almost everything: whether its messages arrived, what time it is, and even whether it has been frozen for the past minute. This lesson is about how to build something trustworthy when no single participant can be trusted to know the truth, including the truth about itself.

An everyday picture: a committee whose members sit in separate rooms and communicate by notes passed under the doors. One member's door jams. He can still read the notes coming in, but his own never get out. The others, hearing nothing from him, vote to replace him as chairman. From inside his room, he still feels like the chairman. Who is right? The committee has to be, because it is the only body that can act. That is the first idea of this lesson: **what is true is decided by a majority vote, not by any individual**.

Now suppose the door comes unstuck and the old chairman walks to the bank with the committee's chequebook. He sincerely believes he is still authorised. The only thing that can stop him is the bank teller, who checks a list and says "your authority was number 33, and I have already served number 34". That is the second idea: a **fencing token**, a number that lets the place where the damage would happen refuse anyone whose authority is out of date.

Why this matters for a job: any time a design includes "only one server does X at a time" (one leader, one holder of a lock, one scheduled job), these two ideas are what make it safe. "Is a lock in Redis safe?" is a well-known interview question whose answer is in section 3. The lesson also gives you the vocabulary (safety, liveness, system model) in which the guarantees of every distributed database are stated.

## What a node can know

The two preceding lessons took away most of what a program normally relies on. Messages may be lost or arbitrarily delayed. Clocks disagree. A process may be frozen at any instruction and wake up later without noticing. Put together, these facts lead to an unsettling conclusion: **a node in a distributed system cannot be sure of anything beyond its own local state**. All it can do is draw inferences from the messages it receives - or does not receive.

This lesson asks how correct systems can be built on such thin ground. The answers come in three layers. First, *who decides what is true*: not any single node, but a quorum. Second, *how do we stop a node that is wrong about itself* from doing damage: fencing tokens. Third, *how do we reason rigorously* about algorithms in such an environment: system models, and the distinction between safety and liveness. Along the way we look at the far nastier case of nodes that lie on purpose.

## 1. A node cannot judge itself

Consider three situations.

**The one-way link.** A node can receive every message sent to it, but a faulty network interface drops everything it sends. It hears requests, computes answers, and transmits them into the void. The other nodes, getting no replies, declare it dead. The node itself is like a patient who can hear the doctors saying he has passed away and cannot make himself heard.

**The half-aware node.** A slightly luckier node notices that nobody acknowledges its messages and concludes that something is wrong with the network. It is still declared dead by the others, and there is nothing it can do about that.

**The sleeper.** A node is paused for a full minute by a stop-the-world garbage collection. Its threads are frozen; no requests are handled. The other nodes wait, time out, declare it dead and elect a replacement. Then the pause ends. From the node's own perspective no time has passed - it finishes the statement it was executing as if nothing had happened.

In all three cases the node's opinion about its own status - alive, in charge, holding the lock - differs from the rest of the system's opinion. And in a system that must make progress, the rest of the system has to win.

### The majority decides

A distributed system therefore cannot depend on the judgement of one node, since any node may fail or be cut off at any time. Decisions are made by a **quorum**: a vote among the nodes, most commonly requiring an **absolute majority**, more than half.

That includes decisions about who is dead. If a quorum declares a node dead, it *is* dead as far as the system is concerned, however lively it feels. The node must accept the verdict and step down.

Why more than half? Because **two majorities of the same set always share at least one member**, so there cannot be two disjoint groups each believing it has the authority to decide. With three nodes, one failure is tolerated; with five, two. The system keeps working with a minority of nodes down, and it stays safe, since a minority can never decide alone.

The program below checks the overlap claim by listing every possible majority for several cluster sizes.

```python-run
from itertools import combinations

def majorities(n):
    need = n // 2 + 1
    return [set(c) for c in combinations(range(n), need)]

for n in (3, 4, 5, 7):
    ms = majorities(n)
    overlap = all(a & b for a in ms for b in ms)
    print(f"n={n}: majority size {n // 2 + 1}, tolerates {n - (n // 2 + 1)} failures, "
          f"every pair of majorities overlaps: {overlap}")

# A network split of 5 nodes into {0,1} and {2,3,4}
side_a, side_b = {0, 1}, {2, 3, 4}
print("side A can decide:", len(side_a) > 5 // 2, "| side B can decide:", len(side_b) > 5 // 2)
```

What each part does:

- `n // 2 + 1` is the smallest number that is more than half of `n`. The `//` operator divides and rounds down, so for 5 nodes it gives 2 + 1 = 3.
- `combinations(range(n), need)` produces every way of choosing `need` nodes out of `n`. `majorities(n)` returns all of them as sets.
- `all(a & b for a in ms for b in ms)` takes every pair of majorities and checks that the two sets have at least one node in common. (`a & b` is the set of shared members, and an empty set counts as false.)
- The last two lines model a network fault that divides five nodes into a group of two and a group of three, and ask which group is big enough to decide.

```
n=3: majority size 2, tolerates 1 failures, every pair of majorities overlaps: True
n=4: majority size 3, tolerates 1 failures, every pair of majorities overlaps: True
n=5: majority size 3, tolerates 2 failures, every pair of majorities overlaps: True
n=7: majority size 4, tolerates 3 failures, every pair of majorities overlaps: True
side A can decide: False | side B can decide: True
```

Note that four nodes tolerate no more failures than three - an even cluster size buys nothing. And in a split, at most one side can have a majority.

## 2. The leader and the lock

Systems often need exactly one of something:

- one node that is the leader of a database partition, to avoid split brain;
- one transaction or client holding the lock on a resource, to prevent concurrent conflicting writes;
- one user who gets a particular username.

Implementing "exactly one" in a distributed system needs care. A node may sincerely believe it is "the chosen one" - partition leader, lock holder - although a quorum no longer agrees. It may have been the leader once; then the others, hearing nothing from it during a network interruption or a GC pause, declared it dead and promoted someone else.

If such a node carries on acting as leader, and other parts of the system accept what it says, things break. Consider a storage service that only one client at a time may write to, with exclusivity arranged through a lock service. A real bug of exactly this kind once affected HBase:

1. Client 1 obtains the lease.
2. Client 1 is paused for a long time by garbage collection.
3. The lease expires. Client 2 obtains it and starts writing.
4. Client 1 wakes up, still convinced that its lease is valid, and writes too.

Two writers, one file, damaged data. The lock service did nothing wrong, and neither did client 2. Client 1's belief was out of date, and nothing checked it. A node like client 1, which has been replaced and does not know it, is often called a **zombie**.

## 3. Fencing tokens

The protection has to sit at the **resource**, because that is the one place every write must pass through.

Every time the lock service grants the lock or lease, it also hands out a **fencing token**: a number that increases with every grant. A client must include its current token in every write request to the storage service. The storage service remembers the highest token it has processed and **rejects any request with a lower one**.

```mermaid
sequenceDiagram
  participant C1 as Client 1
  participant LS as Lock service
  participant C2 as Client 2
  participant ST as Storage
  C1->>LS: acquire lease
  LS-->>C1: granted, token 33
  Note over C1: long pause
  Note over LS: lease expires
  C2->>LS: acquire lease
  LS-->>C2: granted, token 34
  C2->>ST: write with token 34
  ST-->>C2: accepted, highest seen = 34
  Note over C1: resumes
  C1->>ST: write with token 33
  ST-->>C1: rejected, 33 is older than 34
```

Client 1 never learns in advance that it was paused. It finds out when the storage service turns its request away - and that is enough. Correctness no longer depends on timeouts being right, on clocks, or on the client's good behaviour.

The program below runs that scenario twice, first with a storage service that accepts anything and then with one that checks tokens.

```python-run
class LockService:
    def __init__(self): self.token, self.holder = 0, None
    def grant(self, client):
        self.token += 1; self.holder = client
        return self.token

class Storage:
    def __init__(self, fencing): self.fencing, self.highest, self.log = fencing, 0, []
    def write(self, client, token, data):
        if self.fencing and token < self.highest:
            return f"REJECT {client} (token {token} < {self.highest})"
        self.highest = max(self.highest, token)
        self.log.append((client, data))
        return f"accept {client} (token {token})"

for fencing in (False, True):
    locks, store = LockService(), Storage(fencing)
    t1 = locks.grant("client-1")                 # client-1 gets the lease, then freezes
    t2 = locks.grant("client-2")                 # lease expired; client-2 takes over
    print(f"--- fencing {'on' if fencing else 'off'}")
    print(store.write("client-2", t2, "v2 of the file"))
    print(store.write("client-1", t1, "stale v1 of the file"))     # the zombie wakes up
    print("stored:", [d for _, d in store.log])
```

What each part does:

- `LockService.grant(client)` raises its counter by one, records the new holder, and returns the counter. That number is the fencing token.
- `Storage.write` is the resource. With fencing on, it compares the token on the request with the highest token it has accepted so far and refuses anything lower. Otherwise it remembers the new highest token and stores the data.
- In the loop, client 1 is granted the lease (token 1). The lease is then granted to client 2 (token 2), standing for client 1's lease having expired during a pause.
- Client 2 writes first. Then client 1, the zombie, wakes up and writes with its old token.

```
--- fencing off
accept client-2 (token 2)
accept client-1 (token 1)
stored: ['v2 of the file', 'stale v1 of the file']
--- fencing on
accept client-2 (token 2)
REJECT client-1 (token 1 < 2)
stored: ['v2 of the file']
```

Without fencing, the stale write lands on top of the valid one. With fencing, the storage service turns it away, and the stored data is what the rightful holder wrote.

Practical notes:

- The token has to come from a service that can number its grants reliably. Coordination services such as **ZooKeeper** and **etcd** (small, highly reliable stores used for locks and cluster information) number every change they make with a counter that only goes up, and that number can serve as the token.
- The resource itself must take part in the check. It is **not sufficient for clients to check their own lock status**. For a resource that does not understand tokens you may be able to smuggle one in - for instance, include it in a file name, or use a conditional write - but some check on the server side is unavoidable.
- This is another case of a general principle: a service should not assume its clients are well behaved. The people who run a service and the people who write its clients often have different priorities, so services protect themselves.

> [!INTERVIEW]
> "Is a Redis lock safe?" The precise answer separates two purposes. For **efficiency** - avoiding duplicate work, where an occasional double execution costs a little - a lease with a timeout is fine. For **correctness** - where two holders at once would corrupt data - no lease is sufficient by itself, whatever the lock service, because the holder may pause after acquiring it. You need a fencing token checked by the resource, and the token must come from a system that can order grants reliably.

## 4. Byzantine faults

Fencing tokens catch a node that is *honestly mistaken*. A node that deliberately sent a forged, high token could walk straight through. So far we have assumed that nodes are unreliable but **honest**: slow, silent, out of date - yet whatever they say is true to the best of their knowledge and they follow the protocol.

Drop that assumption and the problem becomes far harder. A node that sends false or contradictory messages - claiming to have received something it never got, telling different peers different things - exhibits a **Byzantine fault**. Reaching agreement in the presence of such nodes is the **Byzantine Generals Problem**, named after a thought experiment about generals who must agree on a battle plan although some of them are traitors sending conflicting messages. A system that continues to operate correctly even if some nodes malfunction arbitrarily or are controlled by an adversary is **Byzantine fault-tolerant**.

Where it matters:

- **Aerospace and other safety-critical control systems.** Radiation can corrupt memory or CPU registers, making a component behave unpredictably. A failure could cost lives, so flight control systems tolerate such faults.
- **Systems with mutually distrusting participants.** In a blockchain, there is no central authority and any participant may try to cheat. The network must agree on whether a transaction happened without trusting individual nodes.

In the kind of systems this track is about - databases and services inside your own data centres - Byzantine faults are normally **not** assumed, for good reasons:

- All nodes are run by one organisation, so they are presumed not to be malicious, and radiation levels on the ground are low.
- Protocols that tolerate Byzantine faults are intricate and costly, and they typically work only while **over two thirds** of the nodes are healthy - one traitor already calls for four nodes.
- They do not help against **software bugs**: if every node runs the same code, the same bug affects all of them. One would need several independent implementations.
- They do not help against **attackers** either: an attacker who compromises one node can usually compromise the rest in the same way. Authentication, access control, encryption and firewalls remain the main defences.

Clients on the public internet are another matter. A web browser or a mobile app is under its user's control and may send anything at all. That is why servers check every input they receive and reject or clean up anything unexpected. But the usual arrangement there is that the server is the single authority and decides what is allowed. No agreement among untrusted parties is needed.

### Weak forms of lying

Even when nodes are assumed honest, cheap precautions against accidental "lies" from hardware faults, bugs and misconfiguration are worthwhile:

- **Checksums** in the application protocol. Packets are occasionally corrupted in ways that slip past the checksums of TCP and Ethernet, for example through buggy network equipment or faulty memory.
- **Input validation.** Check that values from users lie within sensible ranges and limit the size of strings, so malformed input cannot exhaust memory or trigger undefined behaviour. Internal services can be less paranoid, but basic sanity checks are still wise.
- **Several time sources.** An NTP client that consults multiple servers, estimates their errors and discards the ones that disagree with the majority is robust against one badly configured server.

The program below shows two of these precautions.

```python-run
import zlib, statistics

# 1. End-to-end checksum catches corruption that lower layers missed
payload = b'{"account": 42, "amount": 1500}'
frame = (payload, zlib.crc32(payload))
corrupted = (payload.replace(b"1500", b"9500"), frame[1])          # a flipped digit in transit
for name, (data, crc) in (("intact", frame), ("corrupted", corrupted)):
    print(f"{name:<9} checksum ok: {zlib.crc32(data) == crc}")

# 2. Outlier rejection among time sources (offsets in ms reported by five NTP servers)
offsets = [1.2, -0.8, 0.4, 3600_000.0, 0.9]                        # one server is an hour off
med = statistics.median(offsets)
trusted = [o for o in offsets if abs(o - med) < 50]
print("naive mean offset :", round(statistics.mean(offsets), 1), "ms")
print("after outlier drop:", round(statistics.mean(trusted), 2), "ms using", len(trusted), "servers")
```

What each part does:

- `zlib.crc32(payload)` computes a checksum of the message: a number that depends on every byte. The sender transmits the message together with its checksum.
- `corrupted` imitates damage on the way: one digit of the amount has changed, while the checksum that travels with it is still the original.
- The loop recomputes the checksum of what arrived and compares it with the one that was sent.
- `offsets` is the clock correction, in milliseconds, suggested by each of five time servers. One of them is wrong by an hour.
- `statistics.median(offsets)` is the middle value, which one wild value cannot drag far. `trusted` keeps only the servers within 50 milliseconds of the median.

```
intact    checksum ok: True
corrupted checksum ok: False
naive mean offset : 720000.3 ms
after outlier drop: 0.42 ms using 4 servers
```

The damaged message is caught, because its bytes no longer match the checksum. In the second half, averaging all five servers would move the clock by twelve minutes. Dropping the one that disagrees with the rest leaves a correction of under half a millisecond.

## 5. System models

Algorithms have to tolerate the faults we have listed without depending too heavily on the details of particular hardware and software. To reason precisely, we write down the faults we expect as a **system model**: an abstraction stating what an algorithm may assume.

**Timing assumptions** - three common models:

| Model | Assumption | Realism |
|---|---|---|
| **Synchronous** | Network delay, process pauses and clock error all have known, fixed upper bounds | Not realistic for most practical systems |
| **Partially synchronous** | The system behaves synchronously *most of the time*, but occasionally exceeds the bounds for network delay, pauses and clock drift - sometimes by a lot | **A realistic model of most systems** |
| **Asynchronous** | No timing assumptions whatsoever; there is not even a clock, so timeouts cannot be used | Very restrictive; few algorithms are possible |

**Node failure assumptions** - three common models:

| Model | Assumption |
|---|---|
| **Crash-stop** | A node can fail in only one way: it stops and never comes back |
| **Crash-recovery** | A node may crash at any moment and may start responding again after an unknown time. Stable storage survives the crash; in-memory state is lost |
| **Byzantine (arbitrary)** | A node may do absolutely anything, including deceiving other nodes |

The pairing that describes real deployments best is **partial synchrony together with crash-recovery faults**. Good algorithms keep working when timing goes wrong for a while and when nodes restart.

### Safety and liveness

What does it mean for an algorithm to be *correct* in a given model? We state the **properties** it must have. For fencing-token generation, for example:

- **Uniqueness:** no two requests receive the same token.
- **Monotonic sequence:** if request $x$ received token $t_x$ and request $y$ received $t_y$, and $x$ completed before $y$ began, then $t_x < t_y$.
- **Availability:** whoever asks for a token and stays up gets an answer sooner or later.

These fall into two fundamentally different classes.

- A **safety** property says *nothing bad happens*. If it is violated, you can point to the exact moment it went wrong, and the damage cannot be undone. Uniqueness and monotonic sequence are safety properties: once a duplicate token has been issued, it has been issued.
- A **liveness** property says *something good eventually happens*. It may not hold at a given moment, but there is always hope that it will be satisfied later. Availability is a liveness property; its definition typically contains the word "eventually". So does eventual consistency.

The distinction is what makes hard system models manageable. For distributed algorithms we commonly demand that **safety always holds**, in every situation the model allows - even if all nodes crash or the whole network fails, the algorithm must never return a wrong result. For **liveness** we may attach conditions: we promise an answer only on condition that most nodes are still running and that the network comes back at some point. The partially synchronous model fits exactly: during the bad periods we guarantee no progress, but we still guarantee no mistakes.

```mermaid
flowchart LR
  P[Property of an algorithm] --> S[Safety: nothing bad happens]
  P --> L[Liveness: something good eventually happens]
  S --> S1[Must hold always, even if all assumptions about timing fail]
  S --> S2[Examples: uniqueness, monotonic tokens, at most one leader per term]
  L --> L1[May depend on conditions: majority alive, network eventually recovers]
  L --> L2[Examples: availability, eventual consistency, a leader is eventually elected]
```

### Models and reality

A system model is a simplification, and reality has a habit of stepping outside it. Algorithms in the crash-recovery model assume that data on stable storage survives a crash. What if the disk is corrupted, or a firmware bug makes it lose data, or a misconfiguration wipes it? Quorum algorithms assume a node remembers what it previously stored and promised. A node that "forgets" breaks the quorum condition, and with it the algorithm's correctness.

A theoretical description can declare such things impossible and move on. An implementation cannot. It may still need code for the supposedly impossible case, even if all that code does is record an error and stop, so that a person can sort things out. That is the difference between computer science and software engineering.

None of this makes models useless. On the contrary, they are how we tame the overwhelming complexity of real systems into a set of faults we can reason about. **Proving an algorithm correct shows that it always satisfies its properties within the model** - a real implementation can still have bugs, but the proof is an excellent first step, and theoretical analysis regularly uncovers problems that would stay hidden for years in a running system, striking only when an unusual combination of circumstances defeats an assumption. Analysis and testing are both needed.

## Pitfalls

- **A node trusting its own belief** that it is the leader or holds a lock. That belief may be arbitrarily stale.
- **Fencing implemented only on the client side.** A client that checks its own lease before writing is exactly the check-then-act gap; the resource must enforce the token.
- **Even-sized clusters.** Four nodes tolerate one failure, like three, at higher cost and with a higher chance of a tied split.
- **Using a lock service that cannot produce monotonically increasing tokens** for a correctness-critical lock.
- **Reaching for Byzantine fault tolerance to fix bugs or security problems.** Identical software has identical bugs, and a compromised node usually means all are compromised.
- **Skipping application-level checksums and input validation** because "the network already does that".
- **Confusing safety with liveness.** "The system was unavailable for a minute" and "the system returned a wrong answer" are different kinds of failure; only the first is acceptable during a partition.
- **Treating a proof in a model as proof about production.** Know which assumptions of the model your deployment might violate (lost disks, unsynchronised config, forgotten state).

## Summary

- A node knows only what messages tell it, and cannot reliably judge its own status. **Truth is decided by a quorum**, usually a majority, because any two majorities overlap; a node declared dead by a quorum must step down.
- Leases and locks can be held by nodes whose belief is out of date. **Fencing tokens** - increasing numbers issued with each grant and checked by the resource - make such zombie writers harmless.
- **Byzantine faults** are arbitrary or malicious behaviour. Tolerating them matters in aerospace and between mutually distrusting parties; ordinary data-centre systems assume honest nodes, and use checksums, validation and redundant time sources against accidental corruption.
- **System models** state assumptions about timing (synchronous, partially synchronous, asynchronous) and node failures (crash-stop, crash-recovery, Byzantine). Partial synchrony with crash-recovery matches most real systems.
- **Safety** properties must never be violated; **liveness** properties may hold only under conditions. Proofs within a model are valuable, and implementations must still handle what the model rules out.

## Glossary

- **Quorum** - the minimum number of nodes that must agree for a decision to count.
- **Absolute majority** - more than half of all the nodes.
- **Zombie** - a node that still acts as leader or lock holder after the system has replaced it.
- **Lock service** - a service that grants exclusive rights (locks or leases) to one client at a time.
- **Lease** - a lock that expires after a set time unless renewed.
- **Fencing token** - a number that increases with every grant of a lock; the resource rejects any request with a token lower than one it has seen.
- **Resource** - the thing being protected, such as a storage service, which every write must pass through.
- **ZooKeeper / etcd** - coordination services often used as lock services.
- **Byzantine fault** - a node behaving arbitrarily, including sending false or contradictory messages.
- **Byzantine fault-tolerant** - still correct when some nodes behave in that way.
- **Checksum** - a number computed from data, used to detect that the data has been damaged.
- **Input validation** - checking that incoming values are well formed and within sensible limits.
- **System model** - a precise statement of the faults and timing an algorithm is allowed to assume.
- **Synchronous / partially synchronous / asynchronous model** - delays always bounded / usually bounded with occasional exceptions / no timing assumptions at all.
- **Crash-stop / crash-recovery** - a failed node never returns / a failed node may return with its disk contents but without its memory.
- **Stable storage** - storage whose contents survive a crash, such as a disk.
- **Safety property** - a guarantee that nothing bad ever happens.
- **Liveness property** - a guarantee that something good eventually happens.

```quiz
[
  {"q": "Why does a distributed system use a majority quorum rather than a single node's judgement to declare a node dead or elect a leader?",
   "options": ["A majority is faster to contact", "Any single node may be faulty or isolated, and two majorities always overlap, so two conflicting decisions cannot both be made", "It reduces network traffic", "Majorities do not need timeouts"],
   "answer": 1,
   "explain": "The overlap of majorities is what prevents split decisions, and no individual node's view can be trusted."},
  {"q": "A cluster has 5 nodes. How many node failures can it tolerate while still being able to form a majority?",
   "options": ["1", "2", "3", "4"],
   "answer": 1,
   "explain": "A majority of 5 is 3, so up to 2 nodes may be unavailable. Six nodes would also tolerate only 2."},
  {"q": "A client holds a lease, pauses for a long time, and then writes after the lease has passed to another client. What prevents data corruption?",
   "options": ["The client checks its lease before every write", "The storage service rejects writes carrying a fencing token lower than one it has already seen", "A shorter lease timeout", "NTP synchronisation"],
   "answer": 1,
   "explain": "The paused client cannot detect its own staleness. Only the resource, comparing monotonically increasing tokens, can reject the outdated writer."},
  {"q": "What property must fencing tokens have?",
   "options": ["They must be random", "They must increase every time the lock is granted", "They must encode the client's IP address", "They must expire after one use"],
   "answer": 1,
   "explain": "Monotonic increase lets the resource tell a newer grant from an older one by a simple comparison."},
  {"q": "Why are Byzantine fault-tolerant protocols usually not used inside a single organisation's data centre?",
   "options": ["They are illegal", "Nodes are trusted to be honest, the protocols are costly, and they would not protect against shared software bugs or a compromise that affects every node", "They cannot run on Linux", "They require GPS clocks"],
   "answer": 1,
   "explain": "The threat they address is rarely present there, while their cost is high. Bugs and attackers typically affect all nodes at once, which the protocols do not survive."},
  {"q": "Which system model best describes most real distributed systems?",
   "options": ["Synchronous with crash-stop faults", "Partially synchronous with crash-recovery faults", "Asynchronous with Byzantine faults", "Synchronous with Byzantine faults"],
   "answer": 1,
   "explain": "Systems behave well most of the time but occasionally exceed timing bounds, and nodes crash and come back with their disk state intact."},
  {"q": "Which of these is a liveness property?",
   "options": ["No two clients ever receive the same fencing token", "Tokens are issued in increasing order", "Every request from a non-crashed node eventually receives a response", "At most one leader exists per term"],
   "answer": 2,
   "explain": "Liveness says something good eventually happens. The other three are safety properties: a violation happens at a definite moment and cannot be undone."},
  {"q": "During a long network partition, what do we normally require of a well-designed consensus-based system?",
   "options": ["It must keep making progress on both sides", "It may stop making progress, but it must never violate its safety properties", "It may return incorrect results as long as it stays available", "It must shut down permanently"],
   "answer": 1,
   "explain": "Safety must hold unconditionally. Liveness is allowed to depend on conditions such as a majority being reachable."}
]
```

> **Source:** DDIA ch. 8 (The Trouble with Distributed Systems) - knowledge, truth and lies: the majority, fencing tokens, Byzantine faults, system model and reality. Written in original wording with original examples.
