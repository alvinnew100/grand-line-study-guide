# Commands in depth: strings, lists and sets

> **Before this lesson:** read [What Redis is](#/lesson/redis/what-is-redis) for the overview of
> the data types. This lesson and the next two go through the commands of each type in detail.

## In plain words

The first lesson showed each kind of container Redis offers. This lesson looks closely at
three of them and at the instructions - **commands** - that work on each.

- A **string** is the plainest container: one labelled box holding one value. The value may be
  text, a number, or raw bytes. Think of a labelled jar.
- A **list** is a row of items kept in order, where adding or removing at either end is quick.
  Think of a queue at a counter (people join at the back and are served from the front) or a stack
  of plates (the last one put on is the first taken off).
- A **set** is a collection where each item appears at most once and order means nothing. Think of
  a guest list: a name is either on it or not, and writing it twice changes nothing.

Why look at commands one by one? Because in Redis the *command is the design*. There is no query
language to rescue a poor layout; a feature is fast when a single command does what you need.
Knowing that one command can "take an item from this queue and put it on that one, in a single
step" is what lets you build a reliable job queue later.

Two words used throughout: an operation is **atomic** if it happens completely with nothing able to
interleave, and a command is **blocking** if it waits on the server until something arrives.

Why this matters for a job: these commands are the daily vocabulary of anyone who works with Redis,
and several of them (`SET` with `NX`, `BLPOP`, `LMOVE`, `SINTER`) are the building blocks of the
locks, queues and search indexes built later in this track.

## Motivation

The first module showed each data type in a single short session. That is enough to recognise them,
not enough to design with them. Real designs hinge on the less famous commands: the option on `SET`
that turns it into a lock, the list command that moves an element between two queues without ever
letting it exist in neither, the set command that samples random members without removing them.

This lesson and the next two walk through the command families methodically. To keep it concrete we
use one running scenario, **Beacon Desk**, a customer-support tool: tickets arrive, wait in queues, get
tagged, and are picked up by agents. Each command appears next to the small problem it solves.

Throughout, keep one rule in mind: every command is atomic. Whatever a single command does, no other
client can observe it half done.

## Strings: bytes, numbers and bits

A Redis string is a sequence of bytes. Depending on which commands you use, you may treat it as text,
as a number or as an array of bits.

### Plain values and the options on SET

```bash
127.0.0.1:6379> SET ticket:501:subject "Cannot reset password"
OK
127.0.0.1:6379> SET ticket:501:owner agent:lena NX
OK
127.0.0.1:6379> SET ticket:501:owner agent:omar NX
(nil)
127.0.0.1:6379> SET ticket:501:owner agent:omar XX GET
"agent:lena"
127.0.0.1:6379> SET otp:501 "839201" EX 120
OK
127.0.0.1:6379> GETDEL otp:501
"839201"
127.0.0.1:6379> GETDEL otp:501
(nil)
```

- `NX` writes only if the key does **not** exist. The second attempt returns `nil` and changes nothing:
  Omar cannot claim a ticket Lena already holds. `SET key value NX EX seconds` is the foundation of
  the distributed lock built later in this track.
- `XX` writes only if the key **does** exist. `GET` makes `SET` return the previous value, giving an
  atomic swap.
- `EX seconds` and `PX milliseconds` attach a lifetime; `KEEPTTL` preserves the lifetime a key
  already has when you overwrite it (a plain `SET` would clear it).
- `GETDEL` reads and deletes in one step - exactly what a one-time code needs, because a second use
  must find nothing. `GETEX` reads and changes the expiry in one step.

`MSET` and `MGET` write and read several keys in one command, saving round trips:

```bash
127.0.0.1:6379> MSET ticket:502:subject "Invoice missing" ticket:503:subject "App crashes on login"
OK
127.0.0.1:6379> MGET ticket:502:subject ticket:999:subject ticket:503:subject
1) "Invoice missing"
2) (nil)
3) "App crashes on login"
```

### Numbers

When the bytes spell a decimal integer, the counter commands apply.

```bash
127.0.0.1:6379> INCR stats:tickets:opened
(integer) 1
127.0.0.1:6379> INCRBY stats:tickets:opened 10
(integer) 11
127.0.0.1:6379> DECRBY stats:tickets:opened 3
(integer) 8
127.0.0.1:6379> INCRBYFLOAT stats:avg-wait 2.5
"2.5"
127.0.0.1:6379> SET greeting hello
OK
127.0.0.1:6379> INCR greeting
(error) ERR value is not an integer or out of range
```

Integers are signed 64-bit; overflow is an error rather than wrap-around. A missing key counts as 0.
`INCRBYFLOAT` works on doubles and replies with a string.

### Substrings and bits

```bash
127.0.0.1:6379> APPEND ticket:501:log "opened;"
(integer) 7
127.0.0.1:6379> APPEND ticket:501:log "assigned;"
(integer) 16
127.0.0.1:6379> GETRANGE ticket:501:log 0 5
"opened"
127.0.0.1:6379> STRLEN ticket:501:log
(integer) 16
127.0.0.1:6379> SETBIT agents:online:2026-01-01 42 1
(integer) 0
127.0.0.1:6379> GETBIT agents:online:2026-01-01 42
(integer) 1
127.0.0.1:6379> BITCOUNT agents:online:2026-01-01
(integer) 1
```

`APPEND` returns the new length. `GETRANGE` takes inclusive byte offsets. `SETBIT key offset value`
addresses individual bits, growing the string with zero bytes as needed and returning the bit's old
value; `BITCOUNT` counts the ones. One bit per agent id records who was online on a day in
`max_id / 8` bytes - a technique the Modern Redis module develops into daily-active-user counting.

## Lists: queues, stacks and capped logs

A list is an ordered sequence in which pushes and pops at either end cost constant time. Internally it
is a linked chain of small compact arrays (a *quicklist*), so access near the ends is cheap and access
in the middle walks the chain.

### Pushing, popping and reading

```bash
127.0.0.1:6379> RPUSH queue:billing ticket:502 ticket:507
(integer) 2
127.0.0.1:6379> LPUSH queue:billing ticket:500
(integer) 3
127.0.0.1:6379> LRANGE queue:billing 0 -1
1) "ticket:500"
2) "ticket:502"
3) "ticket:507"
127.0.0.1:6379> LLEN queue:billing
(integer) 3
127.0.0.1:6379> LPOP queue:billing
"ticket:500"
127.0.0.1:6379> RPOP queue:billing
"ticket:507"
127.0.0.1:6379> LPUSH letters a b c
(integer) 3
127.0.0.1:6379> LRANGE letters 0 -1
1) "c"
2) "b"
3) "a"
```

Push on one end and pop from the other and you have a first-in-first-out queue; push and pop on the
same end and you have a stack. Note the last example: `LPUSH` with several values inserts them one
after another at the head, so the *last* argument ends up first.

Index rules for `LRANGE key start stop`: both ends are inclusive; negative numbers count from the
tail (`-1` is the last element); out-of-range indices are clamped rather than rejected; and if
`start` lies beyond the end, or after `stop`, the reply is an empty list.

### Capped lists with LTRIM

```bash
127.0.0.1:6379> LPUSH recent:agent:lena ticket:501
(integer) 1
127.0.0.1:6379> LTRIM recent:agent:lena 0 49
OK
```

`LTRIM key start stop` keeps only the given range. Pushing at the head and trimming to `0 49` after
each push maintains "the fifty most recent items" in constant work per update - the standard recipe
for activity feeds and bounded logs.

### Blocking pops and safe hand-off

Workers should not poll an empty queue in a tight loop. The blocking variants park the connection
until an element arrives or a timeout passes.

```bash
127.0.0.1:6379> BLPOP queue:urgent queue:billing 5
1) "queue:billing"
2) "ticket:502"
127.0.0.1:6379> BLPOP queue:urgent queue:billing 5
(nil)
(5.03s)
```

`BLPOP` checks the listed keys in order and pops from the first non-empty one, which gives you
priority queues for free: list `queue:urgent` first. The reply names the key the element came from.

A plain pop has a weakness: if the worker crashes right after popping, the ticket is gone. `LMOVE`
removes an element from one list and pushes it onto another in a single atomic step, so the element
is always in exactly one place.

```bash
127.0.0.1:6379> RPUSH queue:billing ticket:510
(integer) 1
127.0.0.1:6379> LMOVE queue:billing working:lena LEFT RIGHT
"ticket:510"
127.0.0.1:6379> LRANGE working:lena 0 -1
1) "ticket:510"
127.0.0.1:6379> LREM working:lena 1 ticket:510
(integer) 1
```

The worker moves a ticket to its own "in progress" list, does the work, and only then removes it with
`LREM`. A supervisor can inspect `working:*` lists for items that have sat too long and push them back.
`LMOVE` (and blocking `BLMOVE`) replaced the older `RPOPLPUSH` in Redis 6.2.

```mermaid
flowchart LR
    P[Producers] -->|RPUSH| Q[queue:billing]
    Q -->|LMOVE LEFT RIGHT| W[working:lena]
    W -->|LREM when done| D[Finished]
    W -.->|stuck too long: push back| Q
```

> [!WARNING]
> `LINDEX`, `LSET`, `LINSERT` and `LREM` walk the list and cost O(n). A list used as a queue should be
> touched only at its ends. If you find yourself indexing into the middle of a long list, you probably
> want a sorted set or a stream.

## Sets: membership and algebra

A set holds unique strings with constant-time add, remove and membership test.

```bash
127.0.0.1:6379> SADD tag:billing ticket:502 ticket:507 ticket:510
(integer) 3
127.0.0.1:6379> SADD tag:urgent ticket:507 ticket:511
(integer) 2
127.0.0.1:6379> SCARD tag:billing
(integer) 3
127.0.0.1:6379> SMISMEMBER tag:urgent ticket:507 ticket:502
1) (integer) 1
2) (integer) 0
127.0.0.1:6379> SINTER tag:billing tag:urgent
1) "ticket:507"
127.0.0.1:6379> SUNION tag:billing tag:urgent
1) "ticket:502"
2) "ticket:507"
3) "ticket:510"
4) "ticket:511"
127.0.0.1:6379> SDIFF tag:billing tag:urgent
1) "ticket:502"
2) "ticket:510"
127.0.0.1:6379> SINTERSTORE view:urgent-billing tag:billing tag:urgent
(integer) 1
```

- `SINTER` returns members present in **all** listed sets, `SUNION` members present in **any**.
- `SDIFF a b c` returns members of the *first* set that appear in none of the others. Order matters.
- The `...STORE` variants write the result to a destination key and return its size, so a later
  command can page through it or intersect it again.
- `SMISMEMBER` (6.2) tests several members in one call; `SINTERCARD` (7.0) returns only the size of an
  intersection, optionally stopping at a `LIMIT`.

Random access and movement:

```bash
127.0.0.1:6379> SRANDMEMBER tag:billing 2
1) "ticket:510"
2) "ticket:502"
127.0.0.1:6379> SPOP tag:billing
"ticket:507"
127.0.0.1:6379> SMOVE tag:billing tag:resolved ticket:502
(integer) 1
```

`SRANDMEMBER` samples without removing (a negative count allows repeats); `SPOP` removes and returns a
random member - a fair "pick any available item" primitive; `SMOVE` transfers a member between sets
atomically.

For large sets, never fetch everything with `SMEMBERS` from a request handler. Iterate with `SSCAN`,
which returns a cursor and a small batch each call:

```bash
127.0.0.1:6379> SSCAN tag:billing 0 COUNT 100
1) "0"
2) 1) "ticket:510"
```

A returned cursor of `0` means the iteration is complete.

## The same operations with redis-py

```python
import redis

r = redis.Redis(decode_responses=True)

# claim a ticket only if nobody owns it; the claim evaporates after 15 minutes of silence
claimed = r.set("ticket:501:owner", "agent:lena", nx=True, ex=900)
print(claimed)                      # True the first time, None afterwards

# a worker loop with a safe hand-off
def next_ticket(agent, queues=("queue:urgent", "queue:billing")):
    for q in queues:
        ticket = r.lmove(q, f"working:{agent}", "LEFT", "RIGHT")
        if ticket:
            return ticket
    return None

def finish(agent, ticket):
    r.lrem(f"working:{agent}", 1, ticket)

# tags: which urgent billing tickets is nobody working on?
r.sadd("tag:billing", "ticket:502", "ticket:507")
r.sadd("tag:urgent", "ticket:507", "ticket:511")
r.sadd("tickets:claimed", "ticket:511")
print(r.sinter("tag:billing", "tag:urgent"))                    # {'ticket:507'}
print(r.sdiff("tag:urgent", "tickets:claimed"))                 # {'ticket:507'}
```

redis-py returns Python `set` objects for set commands and lists for list commands. `set(..., nx=True)`
returns `True` on success and `None` when the condition was not met - test with `if claimed:`, not
`== 1`.

## Simulating list and set semantics

The model below reproduces the exact index rules of `LRANGE` and `LTRIM`, the argument order of
multi-value `LPUSH`, the atomic move, and the three set operations. Experiment with odd index pairs
such as `(-100, 100)` or `(5, 1)`.

```python-run
class ListsAndSets:
    def __init__(self): self.lists, self.sets = {}, {}

    # ---- lists ----
    def rpush(self, k, *vals):
        l = self.lists.setdefault(k, []); l.extend(vals); return len(l)
    def lpush(self, k, *vals):
        l = self.lists.setdefault(k, [])
        for v in vals: l.insert(0, v)          # one at a time: last argument ends up first
        return len(l)
    def _bounds(self, n, start, stop):
        if start < 0: start = max(n + start, 0)
        if stop < 0: stop = n + stop
        return start, min(stop, n - 1)
    def lrange(self, k, start, stop):
        l = self.lists.get(k, []); start, stop = self._bounds(len(l), start, stop)
        return l[start:stop + 1] if start <= stop else []
    def ltrim(self, k, start, stop):
        kept = self.lrange(k, start, stop)
        if kept: self.lists[k] = kept
        else: self.lists.pop(k, None)          # an emptied list key disappears
        return "OK"
    def lmove(self, src, dst):                 # LEFT of src -> RIGHT of dst
        l = self.lists.get(src)
        if not l: return None
        v = l.pop(0)
        if not l: del self.lists[src]
        self.lists.setdefault(dst, []).append(v)
        return v

    # ---- sets ----
    def sadd(self, k, *members):
        s = self.sets.setdefault(k, set()); n = len(s); s.update(members); return len(s) - n
    def sinter(self, *keys):
        return sorted(set.intersection(*[self.sets.get(k, set()) for k in keys]))
    def sunion(self, *keys):
        return sorted(set.union(*[self.sets.get(k, set()) for k in keys]))
    def sdiff(self, first, *rest):
        out = set(self.sets.get(first, set()))
        for k in rest: out -= self.sets.get(k, set())
        return sorted(out)

r = ListsAndSets()
r.lpush("letters", "a", "b", "c"); r.rpush("letters", "d", "e")
print("all       ", r.lrange("letters", 0, -1))
print("last two  ", r.lrange("letters", -2, -1))
print("clamped   ", r.lrange("letters", -100, 100))
print("inverted  ", r.lrange("letters", 3, 1))
r.ltrim("letters", 0, 2); print("after trim", r.lrange("letters", 0, -1))

r.rpush("queue:billing", "t502", "t507")
print("moved     ", r.lmove("queue:billing", "working:lena"),
      "| queue:", r.lrange("queue:billing", 0, -1), "| working:", r.lrange("working:lena", 0, -1))

r.sadd("billing", "t502", "t507", "t510"); r.sadd("urgent", "t507", "t511")
print("SINTER", r.sinter("billing", "urgent"))
print("SUNION", r.sunion("billing", "urgent"))
print("SDIFF billing urgent", r.sdiff("billing", "urgent"), "| SDIFF urgent billing", r.sdiff("urgent", "billing"))
```

The first line prints `['c', 'b', 'a', 'd', 'e']`: the three left pushes reversed, the two right pushes
in order. Clamping makes `(-100, 100)` return the whole list, while `(3, 1)` yields nothing. The two
`SDIFF` results differ, a reminder that difference is not symmetric.

> [!TIP]
> When several commands would do, prefer the one that does the whole job in a single step:
> `SET ... NX EX` over `SETNX` plus `EXPIRE`, `LMOVE` over a pop followed by a push, `SADD`'s reply
> over a separate membership check. One command is one atomic step and one round trip.

> [!INTERVIEW]
> A common warm-up question is "which Redis type would you use for X?". Answer with the type *and*
> the command that makes it fit: a job queue is a list with `RPUSH` and `BLPOP`; "has this user
> already done this?" is a set with `SADD`; a lock or one-time code is a string with `SET ... NX EX`
> or `GETDEL`. Then name the cost: list ends are O(1), the middle is O(n).

## Pitfalls

- **Plain `SET` erases the TTL.** Overwriting a key that had an expiry makes it permanent unless you
  pass `EX` again or `KEEPTTL`.
- **`SETNX` followed by `EXPIRE`.** Two commands, so a crash between them leaves an immortal lock. Use
  the single command `SET key value NX EX seconds`.
- **Multi-value `LPUSH` order.** `LPUSH k a b c` yields `c b a`, which surprises almost everyone once.
- **Polling instead of blocking.** A loop of `LPOP` plus `sleep` either wastes CPU or adds latency.
  Use `BLPOP`/`BLMOVE` with a timeout.
- **Blocking commands on a shared connection.** A connection parked in `BLPOP` can do nothing else;
  give each blocking worker its own connection, and keep the timeout below any idle-connection limit
  in between.
- **`SMEMBERS` on a huge set.** It returns everything in one reply and blocks the server while building
  it. Use `SSCAN`, or redesign so sets stay small.
- **Assuming set iteration order.** Small integer-only sets happen to come back sorted because of
  their compact encoding; that is an implementation detail, not a promise.
- **Empty collections do not exist.** When the last element is removed, the key is deleted. `EXISTS`
  returning 0 and "empty list" are the same state.

## Command cheat sheet

`n` = number of elements in the structure, `m` = elements returned or affected.

| Command | Meaning | Time |
|---|---|---|
| `SET k v [NX\|XX] [EX s\|PX ms\|KEEPTTL] [GET]` | conditional write, expiry, swap | O(1) |
| `GETDEL k` / `GETEX k EX s` | read-and-delete / read-and-set-expiry | O(1) |
| `MSET` / `MGET` | several keys in one command | O(keys) |
| `INCR`, `INCRBY`, `DECRBY`, `INCRBYFLOAT` | atomic arithmetic | O(1) |
| `APPEND k v` / `STRLEN k` | grow / measure | O(1) amortised |
| `GETRANGE k a b` / `SETRANGE k off v` | substring read / overwrite | O(m) |
| `SETBIT` / `GETBIT` | single bit | O(1) |
| `BITCOUNT k` | count set bits | O(n) |
| `LPUSH` / `RPUSH` / `LPOP` / `RPOP` | ends of a list | O(1) per element |
| `LRANGE k a b` | inclusive slice | O(s + m) |
| `LTRIM k a b` | keep a range | O(removed) |
| `LINDEX`, `LSET`, `LREM`, `LINSERT` | middle access | O(n) |
| `BLPOP k1 k2 timeout` | blocking pop with priority | O(keys) |
| `LMOVE src dst LEFT\|RIGHT LEFT\|RIGHT` | atomic transfer | O(1) |
| `SADD` / `SREM` / `SISMEMBER` / `SMISMEMBER` | membership | O(1) per member |
| `SCARD k` | size | O(1) |
| `SINTER` / `SINTERCARD` | intersection / its size | O(smallest × sets) |
| `SUNION` / `SDIFF` | union / difference | O(total members) |
| `SRANDMEMBER k c` / `SPOP k` | sample / remove at random | O(c) / O(1) |
| `SSCAN k cursor` | incremental iteration | O(1) per call |

## Summary

- `SET` with `NX`, `XX`, `EX`, `GET` and `KEEPTTL` covers conditional writes, swaps and expiring
  values in single atomic commands.
- Strings double as 64-bit counters and as bit arrays.
- Lists are for the ends: queues, stacks, capped logs. Blocking pops remove polling and `LMOVE` makes
  hand-off crash-safe.
- Sets answer membership in O(1) and combine with intersection, union and difference on the server.
- Know which commands are linear in the size of the structure and keep them away from large keys.

## Glossary

- **Command** - one instruction to Redis.
- **String** - a value made of bytes: text, a number or binary data.
- **Counter** - a number changed atomically with `INCR` or `DECR`.
- **Bit / byte** - a single 0 or 1 / a group of eight bits.
- **List** - an ordered sequence with fast access at both ends.
- **Head / tail** - the left end / the right end of a list.
- **Queue (FIFO)** - first in, first out: add at one end, remove from the other.
- **Stack (LIFO)** - last in, first out: add and remove at the same end.
- **Blocking command** - a command that waits on the server until data arrives or a timeout passes.
- **Set** - an unordered collection of unique members.
- **Intersection / union / difference** - members in all sets / in any set / in the first set but
  not the others.
- **Cursor** - a bookmark returned by `SCAN`-style commands so iteration can continue.
- **Atomic** - performed as one indivisible step.
- **NX / XX** - options meaning "only if the key does not exist" / "only if it exists".

```quiz
[
  {"q": "After LPUSH q x y z, what does LRANGE q 0 -1 return?",
   "options": ["x, y, z", "z, y, x", "y, z, x", "An error, LPUSH takes one value"],
   "answer": 1,
   "explain": "Values are pushed at the head one after another, so the last argument ends up first."},
  {"q": "A list holds five elements. What does LRANGE key -100 100 return?",
   "options": ["An error for out-of-range indices", "An empty list", "All five elements", "Only the first element"],
   "answer": 2,
   "explain": "Out-of-range indices are clamped to the ends of the list, so the full list is returned."},
  {"q": "Why is LMOVE queue working LEFT RIGHT safer than LPOP queue followed by RPUSH working?",
   "options": ["It is faster because it uses less memory", "It is one atomic command, so a crash cannot lose the element between the pop and the push", "It works on sets as well", "It never blocks"],
   "answer": 1,
   "explain": "With two commands the element exists only in the client between them; a crash there loses it."},
  {"q": "Set A = {1,2,3}, set B = {3,4}. What is SDIFF B A?",
   "options": ["{1, 2}", "{4}", "{1, 2, 4}", "{3}"],
   "answer": 1,
   "explain": "SDIFF returns members of the first set not present in the others: B minus A is {4}."},
  {"q": "A key was written with SET k v EX 60. Ten seconds later the app runs SET k v2. What is the TTL now?",
   "options": ["50 seconds", "60 seconds", "No expiry: the plain SET removed it", "The key was deleted"],
   "answer": 2,
   "explain": "A plain SET replaces the value and discards any existing TTL unless KEEPTTL or a new EX is given."},
  {"q": "Which single command implements 'take the lock only if it is free, and let it expire after 30 seconds'?",
   "options": ["SETNX lock me, then EXPIRE lock 30", "SET lock me NX EX 30", "GETSET lock me", "INCR lock"],
   "answer": 1,
   "explain": "Combining NX and EX in one SET is atomic; the two-command version can leave a lock with no expiry."},
  {"q": "What does BLPOP urgent normal 5 do when both lists are non-empty?",
   "options": ["Pops from both", "Pops from normal because it is listed last", "Pops from urgent because keys are checked in the order given", "Waits five seconds first"],
   "answer": 2,
   "explain": "Keys are examined left to right and the first non-empty list is popped, giving simple priority ordering."},
  {"q": "Which command should replace SMEMBERS when a set may contain millions of members?",
   "options": ["SCARD", "SSCAN with a cursor", "SPOP", "SINTER with itself"],
   "answer": 1,
   "explain": "SSCAN returns small batches and a cursor, avoiding one huge blocking reply."}
]
```

> **Source:** Carlson, *Redis in Action*, ch. 3 (sections 3.1-3.3: strings, lists, sets); newer commands (SET options, GETDEL, LMOVE, SMISMEMBER, SINTERCARD) from redis.io. Scenario and code are original.
> Further reading: <https://redis.io/docs/latest/commands/set/>, <https://redis.io/docs/latest/commands/lmove/>, <https://redis.io/docs/latest/develop/data-types/lists/>, <https://redis.io/docs/latest/develop/data-types/sets/>
