"""One-off author helper: bring lessons 01-06 in line with AUTHORING.md section 6.

Adds the "Before this lesson" note, an "In plain words" opening and a glossary. Safe to re-run:
a lesson that already has "## In plain words" is skipped.
"""
import os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lessons")

ADD = {
"01-what-is-redis.md": dict(
before="""> **Before this lesson:** nothing is assumed. If you can open a terminal and have seen a little
> Python, you are ready. Every technical word is explained when it first appears, and collected in
> the glossary at the end.""",
plain="""A **database** is a program that stores information for other programs and hands it back on
request. Most databases keep their information on a disk, organised into tables with rows and
columns, and you ask questions in a language called SQL. They are built to be careful and general.

**Redis** is a different kind of store, built to be *fast*. It keeps everything in the computer's
working memory (**RAM**), which is thousands of times quicker to reach than a disk. And instead of
tables it gives you a few ready-made containers: a labelled box for one value, a queue, a bag of
unique items, a small record, and a ranking table.

An everyday picture: the main database is the filing room in the basement - complete, orderly, and a
walk away. Redis is the whiteboard and the sticky notes next to your desk: the things you need to
see or update many times a minute. You would not keep the company's legal archive on sticky notes,
and you would not walk to the basement to check who is next in the queue.

Each piece of information in Redis is stored under a name called a **key**, and what is stored is
its **value**. A program that talks to Redis is a **client**; Redis itself is the **server**; one
instruction sent to it, such as "set this key", is a **command**.

Why this matters for a job: Redis is among the most widely used pieces of backend software. It is
the usual answer for caching (keeping copies of slow results), login sessions, counters, rankings,
queues and rate limits, and questions about it are routine in backend interviews.

The examples below type commands into `redis-cli`, a small program shipped with Redis that sends
what you type to the server and prints the reply. The text before the `>` is its prompt.""",
glossary="""- **Database** - a program that stores data for other programs.
- **RAM (memory)** - a computer's fast working storage, emptied when the power goes off.
- **Disk** - slower storage that keeps its contents without power.
- **Key / value** - the name under which something is stored / the thing stored.
- **Client / server** - a program that sends requests / the program that answers them.
- **Command** - one instruction sent to Redis, such as `SET` or `GET`.
- **redis-cli** - the command-line client that ships with Redis.
- **Data structure** - a way of organising data, such as a list or a set.
- **String** - a sequence of bytes: text, a number or binary data.
- **List** - an ordered sequence with cheap access at both ends.
- **Set** - an unordered collection without duplicates.
- **Hash** - a small record of named fields inside one key.
- **Sorted set (ZSET)** - unique members kept in order of a numeric score.
- **Atomic** - happening completely, with no other command able to run in the middle.
- **Persistence** - saving in-memory data to disk so it survives a restart.
- **Replication / replica** - keeping a live copy of the data on another server / that copy.
- **Cache** - a fast store of copies of data that is slow to fetch or compute.
- **Time complexity (O-notation)** - how the cost of an operation grows with the amount of data:
  O(1) is constant, O(log n) grows very slowly, O(n) grows in proportion."""),

"02-first-app-voting.md": dict(
before="""> **Before this lesson:** read [What Redis is](#/lesson/redis/what-is-redis) first. You should
> recognise the five basic types (string, list, set, hash, sorted set) and commands such as `INCR`,
> `HSET`, `SADD` and `ZADD`. Basic Python (functions, dictionaries) is used.""",
plain="""The best way to understand a toolbox is to build something with it. In this lesson we build
the core of a voting site: people post items, other people vote for the ones they like, and a front
page shows the most popular recent items first. Reddit, Hacker News and every "top ideas" board work
this way.

Think of a noticeboard in a community hall. Anyone may pin up a proposal. Each visitor may put one
sticker on a proposal they support - one sticker per person per proposal. The caretaker keeps
re-arranging the board so that well-supported, recent proposals sit at eye level. Our program is
the caretaker, and Redis is the board: it has to remember each proposal, who has already put a
sticker on it, and the current order.

Three ideas appear here that return throughout the track. A **record** (the facts about one thing)
is stored in a hash. An **index** is extra data kept only so that a question can be answered
quickly - here, "what is the current order?". And a **score** is the number a sorted set orders its
members by.

Why this matters for a job: ranking things by a mix of freshness and popularity is one of the most
common features in consumer software, and designing it is a classic interview exercise. The habit
this lesson teaches - start from the questions the application will ask, then choose the structure
that answers each one - is the core skill of working with Redis.""",
glossary="""- **Record** - the stored facts about one thing (here, one proposal).
- **Index** - extra data maintained so that a particular lookup is fast.
- **Identifier (id)** - a unique number or name for a record.
- **Score** - the number by which a sorted set orders a member.
- **Unix time (timestamp)** - a moment expressed as seconds since 1 January 1970.
- **Denormalisation** - storing the same fact in more than one place to make reads cheap.
- **Counter** - a number increased atomically, for example with `INCR`.
- **Expiry (TTL)** - a time limit after which Redis deletes a key by itself.
- **Intersection** - the items present in every one of several collections.
- **Round trip** - one request to the server and its reply.
- **Race condition** - a bug that depends on the unlucky timing of two programs acting at once.
- **Atomic** - completed as one indivisible step.
- **Pagination** - returning results one page at a time."""),

"03-sessions-carts.md": dict(
before="""> **Before this lesson:** you should know hashes and sorted sets from
> [What Redis is](#/lesson/redis/what-is-redis) and have seen records and indexes combined in
> [a first application](#/lesson/redis/first-app-voting). No web-development experience is assumed.""",
plain="""When you log in to a website, it remembers you as you click from page to page. That is odd
when you think about it, because the web's underlying protocol, **HTTP**, treats every page request
as a message from a stranger. The memory has to be added on top.

The usual trick works like a cloakroom. You hand over your coat and receive a numbered ticket. The
ticket says nothing about you; it is the attendant's rack that links number 4417 to your coat.
On a website the ticket is a **cookie** - a small piece of text the site asks your browser to send
back with every request - containing a long random code called a **token**. The site's rack is a
table that maps each token to "this is customer 5120". That table entry, with whatever else the
site remembers about your visit, is a **session**.

The rack is consulted on *every single request*, so it must be fast, and its contents are
short-lived: sessions end. Fast and short-lived is exactly what Redis is good at. The same goes for
a **shopping cart**: a small list of what you intend to buy, changed often, abandoned often.

Why this matters for a job: session storage is the single most common production use of Redis.
Getting it wrong has security consequences, so the lesson also covers how tokens must be generated
and how old sessions are removed.""",
glossary="""- **HTTP** - the protocol browsers and web servers use to exchange requests and pages.
- **Cookie** - a small piece of text a site stores in the browser, sent back with each request.
- **Token** - a long random value that identifies a session.
- **Session** - what a site remembers about one visitor between requests.
- **Authentication** - checking who someone is (for example by password).
- **Signed cookie** - a cookie carrying data plus a cryptographic signature proving it is unaltered.
- **TTL (time to live)** - the seconds remaining before a key is deleted automatically.
- **Sliding expiration** - a deadline that is pushed forward on every use.
- **Lazy expiry / active expiry** - deleting an expired key when it is next touched / by periodic
  background sampling.
- **Pipeline** - several commands sent together in one round trip.
- **Sweeper (cleanup worker)** - a background program that removes old data.
- **Shopping cart** - the list of items and quantities a visitor intends to buy.
- **Cryptographically secure** - random in a way that cannot feasibly be predicted."""),

"04-caching-analytics.md": dict(
before="""> **Before this lesson:** you should know strings with expiry (`SET ... EX`) and sorted sets
> ([What Redis is](#/lesson/redis/what-is-redis)), and have read
> [sessions and carts](#/lesson/redis/sessions-carts), which introduced the bookshop used here and
> the idea of a time to live (TTL).""",
plain="""A **cache** is a place where you keep a ready-made copy of something that is slow to
produce, so that next time you can hand over the copy instead of doing the work again.

A café does this every morning. Making each sandwich to order would be slow, so the popular ones
are made in advance and kept in the display case. Most customers are served in seconds from the
case; only an unusual order goes to the kitchen. The price is freshness: a sandwich in the case may
be an hour old. Decide how old is acceptable, and throw out anything older.

Websites have the same shape. Building a page may need a dozen questions to the database; most
visitors ask for the same pages; and a page that is a few minutes old is usually fine. So: build it
once, keep the result in Redis for a few minutes, and serve the copy.

Four words carry the whole topic. A **hit** is finding the copy; a **miss** is not finding it and
doing the real work. The **hit ratio** is the fraction of requests served from the copy. The **time
to live (TTL)** is how long a copy is kept - the maximum staleness you accept.

This lesson builds three things: a cache of whole pages, a cache of individual database rows that
refreshes itself on a schedule, and the small amount of **analytics** (measurements of what visitors
do) needed to decide which pages are worth caching at all.

Why this matters for a job: caching is the cheapest large performance improvement available to most
systems and the most common reason companies run Redis.""",
glossary="""- **Cache** - a store of ready-made copies of results that are slow to produce.
- **Hit / miss** - finding / not finding a wanted item in the cache.
- **Hit ratio** - hits divided by all lookups.
- **TTL (time to live)** - how long an entry is kept before it expires.
- **Stale** - out of date compared with the original data.
- **Render** - produce the final page (HTML) from templates and data.
- **Cache key** - the name under which a cached result is stored; it must include everything that
  affects the result.
- **Latency** - how long one request takes.
- **Row** - one record in a database table.
- **Invalidation** - removing or replacing a cached copy because the original changed.
- **Jitter** - a small random variation, here added to TTLs.
- **Analytics** - measurements of how a system is used.
- **Exponential decay** - repeatedly multiplying by a fraction so that old contributions fade.
- **Cache stampede** - many requests rebuilding the same expired entry at the same time."""),

"05-strings-lists-sets.md": dict(
before="""> **Before this lesson:** read [What Redis is](#/lesson/redis/what-is-redis) for the overview of
> the data types. This lesson and the next two go through the commands of each type in detail.""",
plain="""The first lesson showed each kind of container Redis offers. This lesson looks closely at
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
locks, queues and search indexes built later in this track.""",
glossary="""- **Command** - one instruction to Redis.
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
- **NX / XX** - options meaning "only if the key does not exist" / "only if it exists"."""),

"06-hashes-sorted-sets.md": dict(
before="""> **Before this lesson:** read [strings, lists and sets](#/lesson/redis/strings-lists-sets),
> which uses the same support-desk scenario, and [What Redis is](#/lesson/redis/what-is-redis) for
> the first look at hashes and sorted sets.""",
plain="""This lesson covers the two remaining classic containers.

A **hash** is a small record: one key holding several named **fields**, each with its own value.
Think of an index card for a support ticket with labelled lines - *subject*, *status*, *priority*.
You can read or change one line without rewriting the card.

A **sorted set** is a ranking table. Every **member** appears once and carries a number called its
**score**, and Redis keeps the members in order of score at all times. Think of a league table:
each team appears once, has a points total, and the table re-orders itself whenever a result comes
in. You can ask "who is in the top three?", "what position is this team in?" (its **rank**), or
"which teams have between 40 and 50 points?" - and each answer comes back almost instantly, however
long the table is.

The sorted set is the most versatile structure in Redis, because many problems are rankings in
disguise. Use a time as the score and you have a timeline, or a list of things due at a certain
moment. Use a priority and you have a priority queue. Use a count and you have a "most popular"
chart.

Why this matters for a job: hashes are how records are stored in Redis, and sorted sets are behind
leaderboards, feeds, schedulers, rate limiters and autocomplete - all of which appear later in this
track and regularly in interviews. How a sorted set achieves its speed (a structure called a skip
list) is itself a common interview question, explained in this lesson from the ground up.""",
glossary="""- **Hash** - one key holding a small record of named fields.
- **Field** - one named entry inside a hash.
- **Sorted set (ZSET)** - unique members kept in order of a numeric score.
- **Member / score** - an item in a sorted set / the number it is ordered by.
- **Rank** - a member's position in the ordering, counted from 0.
- **Inclusive / exclusive bound** - a range end that includes / excludes the stated value.
- **Lexicographic order** - dictionary order, comparing byte by byte.
- **Aggregate** - how scores of the same member are combined (sum, minimum or maximum).
- **Weight** - a multiplier applied to an input's scores before combining.
- **Priority queue** - a queue from which the lowest (or highest) scored item is taken first.
- **Skip list** - a layered linked list that allows fast search in sorted data.
- **Hash table** - a structure that finds an entry directly from its key in constant time.
- **Listpack** - the compact encoding Redis uses for small collections.
- **Double (floating-point number)** - the number format of scores; exact for whole numbers up to
  2^53."""),
}

EXTRA_05 = """> [!TIP]
> When several commands would do, prefer the one that does the whole job in a single step:
> `SET ... NX EX` over `SETNX` plus `EXPIRE`, `LMOVE` over a pop followed by a push, `SADD`'s reply
> over a separate membership check. One command is one atomic step and one round trip.

> [!INTERVIEW]
> A common warm-up question is "which Redis type would you use for X?". Answer with the type *and*
> the command that makes it fit: a job queue is a list with `RPUSH` and `BLPOP`; "has this user
> already done this?" is a set with `SADD`; a lock or one-time code is a string with `SET ... NX EX`
> or `GETDEL`. Then name the cost: list ends are O(1), the middle is O(n).

"""

for name, parts in ADD.items():
    path = os.path.join(HERE, name)
    text = open(path, encoding="utf-8").read()
    if "## In plain words" in text:
        continue
    title, rest = text.split("\n", 1)
    text = f"{title}\n\n{parts['before']}\n\n## In plain words\n\n{parts['plain']}\n{rest}"
    marker = "```quiz"
    head, tail = text.rsplit(marker, 1)
    if name.startswith("05") and "[!INTERVIEW]" not in head:
        head = head.replace("## Pitfalls\n", EXTRA_05 + "## Pitfalls\n", 1)
    text = f"{head}## Glossary\n\n{parts['glossary']}\n\n{marker}{tail}"
    open(path, "w", encoding="utf-8").write(text)
    print("updated", name)
