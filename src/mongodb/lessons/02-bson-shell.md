# BSON types, ObjectId and the shell

> **Before this lesson:** you should know what a document, a field and a collection are - see [Documents, collections and why a document database](#/lesson/mongodb/document-model). No other knowledge is assumed; binary and hexadecimal notation are explained here when they are needed.

## In plain words

When you write a number on paper, nobody can tell whether you meant a count of apples, a price or a phone number. Computers have the same problem, so every value stored in a database carries a **type**: a label saying what kind of value it is (whole number, text, date and so on). The type decides how much space the value takes, how it is compared with other values and what you may do with it.

MongoDB stores documents in a format called **BSON**. An everyday analogy: a recipe written for humans says "a cup of flour"; the same recipe prepared for a factory says "128.0 grams, flour type 550". The human version is easy to read; the factory version is exact and fast for machines. JSON is the human version of a document, BSON is the factory version.

Why it matters for a job: a large share of real MongoDB bugs are type bugs - a date stored as text that will not sort, a price stored as a floating-point number that loses a cent, an id compared as a string when it is an ObjectId. Knowing the types prevents them, and "what is an ObjectId made of?" is a classic interview question.

## From JSON to BSON

**JSON** (JavaScript Object Notation) is a text format for structured data. It has six kinds of value: string, number, boolean (`true`/`false`), `null`, array and object. It is readable and universal, but it has gaps:

- there is one "number", with no distinction between whole numbers and fractions;
- there is no date type, so dates travel as strings or numbers by private agreement;
- there is no way to carry raw bytes such as an image;
- a program must read the text character by character to find anything.

**BSON** (Binary JSON) fixes these. It is a **binary** format, meaning it is written as raw bytes for programs and not as characters for people. Each field is stored as: one byte naming the type, the field name, then the value in a fixed layout for that type. Strings, arrays and embedded documents are prefixed with their length, so a program can skip over a field it does not care about without reading it. That is the "fast for machines" part.

You never write BSON by hand. You write something JSON-like in the shell or a dictionary in Python, and the driver converts it.

## The types you will meet

| type | shell example | Python equivalent | notes |
|---|---|---|---|
| null | `null` | `None` | "no value"; also what a query for `null` matches when the field is absent |
| boolean | `true`, `false` | `True`, `False` | |
| 32-bit integer | `42` or `Int32(42)` | `int` (small) | whole numbers up to about ±2.1 billion |
| 64-bit integer | `Long("9007199254740993")` | `int` (large) | whole numbers up to about ±9.2 quintillion |
| double | `3.5` | `float` | 64-bit floating point; fractions are approximate |
| decimal128 | `Decimal128("19.99")` | `bson.Decimal128` | exact decimal arithmetic, for money |
| string | `"hello"` | `str` | text, stored as UTF-8 |
| date | `new Date()` or `ISODate("2026-05-01T09:30:00Z")` | `datetime.datetime` | milliseconds since 1 January 1970 UTC; no time zone stored |
| ObjectId | `ObjectId()` | `bson.ObjectId` | 12-byte unique id, default for `_id` |
| array | `[1, "a", null]` | `list` | ordered; may mix types |
| embedded document | `{ city: "Riga" }` | `dict` | nesting up to 100 levels |
| binary data | `BinData(0, "aGVsbG8=")` | `bytes` | arbitrary bytes |
| regular expression | `/^bra/i` | `re.compile(...)` or `bson.Regex` | a text pattern, used mostly in queries |

A few terms from the table need a sentence each.

- **Bit**: one binary digit, 0 or 1. A **32-bit integer** uses 32 of them and can therefore tell about 4.3 billion values apart.
- **Floating point**: a way of storing numbers with fractions using a fixed number of bits. It stores many fractions only approximately, for the same reason one third cannot be written exactly in decimal digits.
- **UTC** (Coordinated Universal Time): the world's reference clock, without daylight-saving shifts.
- **UTF-8**: the standard way to turn characters from every writing system into bytes.

### Numbers: the trap that costs money

Try `0.1 + 0.2` in almost any programming language and the answer is `0.30000000000000004`. Neither 0.1 nor 0.2 has an exact binary representation, and the tiny errors add up. For measurements this is harmless. For money it is not.

Two safe choices exist for currency amounts:

1. store whole numbers of the smallest unit (cents) as integers: `price_cents: 1999`;
2. store a `Decimal128`, which keeps decimal digits exactly: `price: Decimal128("19.99")`.

How a plain number typed in the shell is stored also matters. In `mongosh`, a literal such as `42` that fits in 32 bits is stored as a 32-bit integer; a literal with a fraction, or one too large for 32 bits, is stored as a double. A double can represent whole numbers exactly only up to 2 to the power 53 (about 9 quadrillion). Beyond that, write `Long("...")` with the digits in quotes so that no precision is lost on the way in.

### Dates: store instants, not text

A BSON date is a single number: the count of milliseconds since the start of 1970 in UTC. It records an *instant*. It does not record a time zone. Convert to the user's local time when displaying.

In the shell, `new Date()` produces a date value. Calling `Date()` without `new` returns a *string* describing the current time. Mixing the two is a classic source of collections in which some dates are dates and some are text.

> [!WARNING]
> Dates stored as strings such as `"03/04/2026"` sort alphabetically, not chronologically, cannot be used by TTL indexes (indexes that delete old documents, module 4) and are ambiguous (3 April or 4 March?). Always store a real date type.

### Arrays and embedded documents

Arrays keep their order and may contain any mix of types, including documents and other arrays. MongoDB can search inside them: asking for documents where `accessories` equals `"charger"` finds every document whose array *contains* `"charger"`. Embedded documents are reached with **dot notation**: the field `city` inside `address` is called `"address.city"`.

## ObjectId under the microscope

An **ObjectId** is the value MongoDB generates for `_id` when you do not provide one. It is 12 **bytes** long (a byte is 8 bits). Because raw bytes are unreadable, it is displayed in **hexadecimal**: base-16 notation that uses the digits `0-9` and letters `a-f`, where two hexadecimal characters describe exactly one byte. Twelve bytes therefore appear as 24 characters:

```
66f0a1c2 e4b0a1b2c3 d4e5f6
|        |          |
|        |          +-- bytes 9-11: a counter that increases by one per id
|        +------------- bytes 4-8:  a random value chosen once per process
+---------------------- bytes 0-3:  seconds since 1 January 1970 (the creation time)
```

The three parts answer three questions.

- *Why is it unique without asking the server?* Two ids made in the same second by the same program differ in the counter. Two ids made in the same second by different programs differ in the random part. No coordination is needed, which matters when many machines insert at once.
- *Why does it start with a timestamp?* Ids created later are larger, so sorting by `_id` gives roughly creation order, and new entries are added at the right-hand edge of the `_id` index, which keeps that index compact.
- *Why 12 bytes and not a longer random identifier?* Every document and every index entry stores the id, so a few bytes saved are saved billions of times.

Because the creation time is inside the id, you can read it back. In the shell, `ObjectId("66f0a1c2e4b0a1b2c3d4e5f6").getTimestamp()` returns the date. In Python, `oid.generation_time` does the same.

> [!INTERVIEW]
> **"Is an ObjectId guaranteed to be ordered by insertion time?"** Only approximately. The timestamp has a resolution of one second, and it is taken from the clock of whichever machine created the id - usually the application server, not the database. Two clients inserting in the same second, or with slightly different clocks, can produce ids whose order does not match the order in which the server stored them. Use it as a convenient rough ordering, not as a precise sequence number.

> [!TIP]
> An ObjectId and the 24-character string that displays it are different values of different types. `{_id: "66f0a1c2e4b0a1b2c3d4e5f6"}` will not find a document whose `_id` is `ObjectId("66f0a1c2e4b0a1b2c3d4e5f6")`. Web applications receive ids as strings and must convert them before querying.

## Working in mongosh

`mongosh` is more than a command prompt. It is a full JavaScript **interpreter** (a program that runs code as you type it), connected to a database.

```javascript
$ mongosh "mongodb://localhost:27017"
test> 6 * 7
42
test> const greet = (who) => "hello " + who
test> greet("shell")
hello shell
```

The first line starts the shell and connects to a server on this machine. The prompt `test>` shows that the current database is called `test`. The next lines show ordinary JavaScript working: arithmetic, and a small function.

The commands used most often:

| command | meaning |
|---|---|
| `show dbs` | list databases that contain data |
| `use toolshare` | switch the current database |
| `show collections` | list collections in the current database |
| `db` | print the name of the current database |
| `db.tools.help()` | list the methods available on a collection |
| `db.getCollection("my-odd name")` | reach a collection whose name is not valid JavaScript |
| `load("seed.js")` | run a script file inside the shell |
| `exit` | leave the shell |

The four basic operations on data are known by the acronym **CRUD**: Create, Read, Update, Delete. Each has a collection method:

```javascript
toolshare> db.members.insertOne({ name: "Ilse", joined: new Date("2026-02-10"), loans: 0 })
{ acknowledged: true, insertedId: ObjectId("67a9c3f0b1d2e3f4a5b6c7d8") }

toolshare> db.members.findOne({ name: "Ilse" })
{ _id: ObjectId("67a9c3f0b1d2e3f4a5b6c7d8"), name: 'Ilse', joined: ISODate("2026-02-10T00:00:00.000Z"), loans: 0 }

toolshare> db.members.updateOne({ name: "Ilse" }, { $set: { loans: 1 } })
{ acknowledged: true, matchedCount: 1, modifiedCount: 1, upsertedId: null, upsertedCount: 0 }

toolshare> db.members.deleteOne({ name: "Ilse" })
{ acknowledged: true, deletedCount: 1 }
```

- `insertOne` creates a document. The value of `joined` is a real date because of `new Date(...)`.
- `findOne` reads back the first document matching the query document. The shell prints the date as `ISODate(...)`, its way of showing a date type.
- `updateOne` takes two arguments: which document to change, and how. `$set` is an **update operator**, an instruction beginning with a dollar sign; here it means "set the field `loans` to 1 and leave the rest of the document alone". The reply says one document matched and one was changed.
- `deleteOne` removes the first matching document and reports how many were deleted.

Each of these is the subject of the next module. For now, notice the shape: the method says *what kind* of operation, the first argument says *which documents*.

To check a value's type, use the `$type` query operator: `db.members.find({ joined: { $type: "date" } })` returns the documents where `joined` is a real date, and replacing `"date"` with `"string"` finds the broken ones.

## The same from Python

```python
import datetime
from bson import ObjectId, Decimal128
from pymongo import MongoClient

members = MongoClient()["toolshare"]["members"]                  # 1

doc = {
    "name": "Ilse",
    "joined": datetime.datetime(2026, 2, 10, tzinfo=datetime.timezone.utc),   # 2
    "deposit": Decimal128("25.00"),                              # 3
    "loans": 0,
}
new_id = members.insert_one(doc).inserted_id                     # 4
print(type(new_id).__name__, new_id.generation_time)             # 5

print(members.find_one({"_id": str(new_id)}))                    # 6
print(members.find_one({"_id": ObjectId(str(new_id))})["name"])  # 7
```

1. `MongoClient()` with no argument connects to `localhost:27017`.
2. A Python `datetime` becomes a BSON date. Supplying the UTC time zone avoids guessing.
3. `Decimal128` keeps the two decimal places exactly.
4. `insert_one` returns a result object whose `inserted_id` is the new `_id`.
5. Prints `ObjectId` and the creation time read from the id's first four bytes.
6. Prints `None`. The query compares `_id` with a *string*, and no document has a string `_id`.
7. Prints `Ilse`. Converting the string back to an `ObjectId` makes the types agree.

## Simulate it yourself

The code below builds ObjectIds by hand so that you can see the three parts, shows that sorting them gives creation order, and demonstrates the floating-point problem.

```python-run
import os, itertools
from datetime import datetime, timedelta
from decimal import Decimal

PROCESS_RANDOM = os.urandom(5)            # 5 random bytes, chosen once per process
counter = itertools.count(0x00A000)       # the 3-byte counter starts at an arbitrary value

def make_object_id(seconds_since_1970):
    timestamp = seconds_since_1970.to_bytes(4, "big")     # 4 bytes, most significant first
    count = (next(counter) % 2**24).to_bytes(3, "big")    # 3 bytes
    return (timestamp + PROCESS_RANDOM + count).hex()     # 12 bytes shown as 24 hex characters

def describe(oid):
    seconds = int(oid[:8], 16)                            # first 8 hex characters = 4 bytes
    when = datetime(1970, 1, 1) + timedelta(seconds=seconds)
    return {"created": when.isoformat() + "Z", "random": oid[8:18], "counter": int(oid[18:], 16)}

noon = 1_780_000_000                      # an arbitrary moment
ids = [make_object_id(noon + offset) for offset in (30, 0, 0, 5)]
for oid in ids:
    print(oid, describe(oid))

print("sorted by id equals sorted by creation time:",
      sorted(ids) == sorted(ids, key=lambda o: (int(o[:8], 16), int(o[18:], 16))))
print("two ids made in the same second differ only in the counter:",
      ids[1][:18] == ids[2][:18], ids[1][18:], ids[2][18:])

print()
print("float  :", 0.1 + 0.2, "-> equal to 0.3?", 0.1 + 0.2 == 0.3)
print("decimal:", Decimal("0.1") + Decimal("0.2"), "-> equal to 0.3?", Decimal("0.1") + Decimal("0.2") == Decimal("0.3"))
print("cents  :", 10 + 20, "-> equal to 30?", 10 + 20 == 30)

print()
print("string '66f0...' == ObjectId bytes?", "66f0a1c2e4b0a1b2c3d4e5f6" == bytes.fromhex("66f0a1c2e4b0a1b2c3d4e5f6"))
```

Reading the output:

- The four ids share the same middle ten characters, because they come from one process. Your random part will differ from run to run.
- The ids were created for moments 30, 0, 0 and 5 seconds after "noon", in that order. Sorting the id strings puts them in time order, with the counter deciding between the two created in the same second.
- The float line prints `0.30000000000000004` and `False`. The decimal and integer-cents lines are exact.
- The last line prints `False`: text and bytes are different types even when they describe the same id. That is the string-versus-ObjectId trap in miniature.

## Pitfalls

- **Dates as strings.** They do not sort or compare as dates. Use `new Date(...)` in the shell and `datetime` in Python.
- **`Date()` without `new`** in the shell yields a string.
- **Money as a double.** Use integer cents or `Decimal128`.
- **Large integers typed as plain numbers** in the shell may be rounded; pass them to `Long("...")` as quoted digits.
- **String versus ObjectId.** Convert incoming id strings before querying.
- **Mixed types in one field.** A field holding numbers in some documents and strings in others sorts in type groups, not by value, and range searches match only one type at a time.
- **Relying on ObjectId order as exact insertion order.** It is accurate to about one second.

## Cheat sheet

| need | use | avoid |
|---|---|---|
| a moment in time | date (`new Date()`, `datetime`) | string dates |
| money | integer cents or `Decimal128` | double |
| a counter or quantity | 32-bit or 64-bit integer | string digits |
| an identifier you do not care to design | default ObjectId | home-made random strings |
| a yes/no flag | boolean | `"yes"`, `1` |
| "unknown" | `null` or leave the field out (choose one convention) | empty string |

| ObjectId part | bytes | hex characters | meaning |
|---|---|---|---|
| timestamp | 4 | 0-7 | seconds since 1970, creation time |
| random | 5 | 8-17 | unique per machine and process |
| counter | 3 | 18-23 | increases per id |

## Summary

- BSON is a binary encoding of JSON-like documents that adds types JSON lacks: dates, several kinds of number, binary data and ObjectId.
- The type of a value controls how it is stored, compared and sorted; two values that look alike but differ in type do not match each other.
- Store instants as dates, money as integer cents or `Decimal128`, and be explicit about 64-bit integers in the shell.
- An ObjectId is 12 bytes: a 4-byte creation timestamp, 5 random bytes and a 3-byte counter. It is unique without coordination and sorts roughly by creation time.
- `mongosh` is a JavaScript interpreter with a `db` variable; CRUD is done through collection methods such as `insertOne`, `findOne`, `updateOne` and `deleteOne`.

## Glossary

- **Type** - the kind of a value (integer, string, date, ...), which decides how it is stored and compared.
- **JSON** - a text format for structured data with six kinds of value.
- **BSON** - the binary, typed format in which MongoDB stores and transmits documents.
- **Bit / byte** - a single binary digit / a group of eight bits.
- **Hexadecimal** - base-16 notation; two characters represent one byte.
- **Double** - a 64-bit floating-point number; fractions are approximate.
- **Decimal128** - a number type that stores decimal digits exactly.
- **UTC** - the reference time standard, free of time-zone and daylight-saving offsets.
- **ObjectId** - the 12-byte identifier MongoDB generates for `_id` by default.
- **Dot notation** - writing `"address.city"` to name a field inside an embedded document.
- **CRUD** - Create, Read, Update, Delete: the four basic data operations.
- **Update operator** - an instruction such as `$set` that describes a change to a document.

## Check yourself

```quiz
[
  {"q": "Why does MongoDB use BSON instead of plain JSON text for storage?",
   "options": ["BSON is easier for humans to read", "BSON has more types (dates, integers, binary) and can be scanned quickly because values carry their length", "BSON documents have no size limit", "JSON cannot represent arrays"],
   "answer": 1,
   "explain": "BSON is a typed binary encoding: richer types than JSON and length prefixes that let programs skip fields."},
  {"q": "What do the first four bytes of an ObjectId contain?",
   "options": ["A random number", "The id of the collection", "The creation time in seconds since 1970", "A counter"],
   "answer": 2,
   "explain": "Bytes 0-3 are a big-endian timestamp in seconds, which is why ObjectIds sort roughly by creation time."},
  {"q": "A document has _id: ObjectId(\"66f0a1c2e4b0a1b2c3d4e5f6\"). What does find({_id: \"66f0a1c2e4b0a1b2c3d4e5f6\"}) return?",
   "options": ["The document", "Nothing, because a string is a different type from an ObjectId", "An error", "Every document in the collection"],
   "answer": 1,
   "explain": "Values of different types do not match. The string must be converted to an ObjectId first."},
  {"q": "Which is the safest way to store a price of 19.99?",
   "options": ["The double 19.99", "The string \"19.99\"", "The integer 1999 (cents) or Decimal128(\"19.99\")", "An array [19, 99]"],
   "answer": 2,
   "explain": "Doubles are approximate, strings do not add or sort numerically; integer cents and Decimal128 are exact."},
  {"q": "In mongosh, what is the difference between new Date() and Date()?",
   "options": ["None", "new Date() gives a date value; Date() gives a string", "Date() gives UTC and new Date() gives local time", "new Date() works only inside insertOne"],
   "answer": 1,
   "explain": "Without new, JavaScript returns a human-readable string, which would be stored as text."},
  {"q": "A BSON date stores which of the following?",
   "options": ["Day, month, year and time zone as text", "Milliseconds since 1 January 1970 UTC, with no time zone", "Seconds since the server started", "A 24-character hexadecimal string"],
   "answer": 1,
   "explain": "It is a 64-bit count of milliseconds since the Unix epoch in UTC; time zones are applied when displaying."},
  {"q": "Two ObjectIds are generated in the same second by the same process. Which part differs?",
   "options": ["The timestamp", "The random value", "The counter", "Nothing; they collide"],
   "answer": 2,
   "explain": "Timestamp and per-process random value are identical; the 3-byte counter increments for every id."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 2 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/reference/bson-types/ , https://www.mongodb.com/docs/manual/reference/method/ObjectId/ , https://www.mongodb.com/docs/mongodb-shell/reference/data-types/
