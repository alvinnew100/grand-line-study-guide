# Query operators and how documents match

> **Before this lesson:** you should know documents, arrays and embedded documents ([Documents, collections and why a document database](#/lesson/mongodb/document-model)), the BSON types ([BSON types, ObjectId and the shell](#/lesson/mongodb/bson-shell)) and what a filter is ([Inserting, deleting and write concern](#/lesson/mongodb/insert-delete)).

## In plain words

A **query** is a question put to the database: "which documents look like this?". In MongoDB the question is itself written as a document, called the **query document** or **filter**. The database holds each stored document up against the filter and keeps the ones that fit.

Think of a hiking club's box of trail cards and a volunteer who helps you choose. You say: "under ten kilometres, in the northern region, and dog-friendly". The volunteer flips through the cards and hands over those meeting all three conditions. A query document is that sentence written down precisely. Query **operators** are the vocabulary for conditions beyond plain equality: "less than", "one of", "not", "has this field".

Why it matters for a job: reading data is the most frequent thing an application does. The rules for matching arrays and missing fields are different from what most people guess, and those differences are behind many wrong-result bugs and a good number of interview questions.

## The simplest query: equality

Here are four trail documents used throughout the lesson:

```javascript
{ _id: 1, name: "Heron Loop",   region: "north", km: 6,  tags: ["lake", "family"],  guide: { name: "Mira", years: 4 }, ratings: [5, 4, 4] }
{ _id: 2, name: "Slate Ridge",  region: "north", km: 14, tags: ["views", "steep"],  guide: { name: "Otto", years: 11 }, ratings: [3, 9] }
{ _id: 3, name: "Fern Hollow",  region: "south", km: 9,  tags: ["forest"],          guide: { name: "Mira", years: 4 }, closed: null }
{ _id: 4, name: "Kestrel Pass", region: "east",  km: 22, tags: [],                  ratings: [] }
```

`find` takes a filter and returns the matching documents:

```javascript
hike> db.trails.find({ region: "north" })
// returns _id 1 and 2
hike> db.trails.find({ region: "north", km: 6 })
// returns _id 1
hike> db.trails.find({})
// returns all four
```

- `{ region: "north" }` means "the field `region` equals `"north"`".
- Two fields in one filter mean **both must hold**. A comma between conditions is an implicit *and*.
- An empty filter matches everything.

Equality is type-sensitive: `{ km: "6" }` matches nothing, because the string `"6"` is not the number `6`. The one tolerance is between number types: the integer `6` and the double `6.0` are equal.

## Comparison operators

For anything other than equality, the value in the filter becomes a small document containing an operator:

| operator | meaning |
|---|---|
| `$eq` | equal (the long form of plain equality) |
| `$ne` | not equal |
| `$gt`, `$gte` | greater than, greater than or equal |
| `$lt`, `$lte` | less than, less than or equal |
| `$in` | equal to any value in a list |
| `$nin` | equal to none of the values in a list |

```javascript
hike> db.trails.find({ km: { $lt: 10 } })
// _id 1 and 3
hike> db.trails.find({ km: { $gte: 9, $lte: 14 } })
// _id 2 and 3: two operators on one field form a range
hike> db.trails.find({ region: { $in: ["south", "east"] } })
// _id 3 and 4
```

Read `{ km: { $lt: 10 } }` as "`km` is less than 10". The outer key is the field, the inner key is the operator, the inner value is what to compare with.

Comparison only happens between values of the same type family. `{ km: { $gt: 5 } }` never matches a document whose `km` is the string `"far"`; that document is skipped, not reported as an error.

## Combining conditions

| operator | meaning | value |
|---|---|---|
| `$and` | all conditions hold | array of filters |
| `$or` | at least one holds | array of filters |
| `$nor` | none holds | array of filters |
| `$not` | the condition does not hold | one operator document |

```javascript
hike> db.trails.find({ $or: [ { km: { $lt: 7 } }, { region: "east" } ] })
// _id 1 (short) and 4 (east)

hike> db.trails.find({ km: { $not: { $gt: 10 } } })
// _id 1 and 3
```

`$or` takes an array of complete filters and returns documents satisfying at least one. Because a comma already means *and*, `$and` is needed only in the uncommon case where the same key would otherwise appear twice in one document, for example two separate `$or` clauses.

> [!TIP]
> When all alternatives concern the same field, prefer `$in` to `$or`: `{ region: { $in: ["south", "east"] } }` is shorter and lets the database plan the query more efficiently than an `$or` of two equalities.

## Missing fields and null

Trail 3 has `closed: null`. Trails 1, 2 and 4 have no `closed` field at all. These are different situations, and the query language treats them in a way that surprises people:

```javascript
hike> db.trails.find({ closed: null })
// all four! null matches both "the value is null" and "the field is absent"

hike> db.trails.find({ closed: { $exists: true } })
// only _id 3: the field is present (even though its value is null)

hike> db.trails.find({ closed: { $exists: false } })
// _id 1, 2 and 4

hike> db.trails.find({ closed: { $type: "null" } })
// only _id 3: present and of type null
```

`$exists` tests whether the field is present. `$type` tests the BSON type of the value.

The same logic explains the behaviour of the negative operators. `{ region: { $ne: "north" } }` asks for documents in which `region` is not `"north"`. A document with **no** `region` field qualifies, since its region is certainly not `"north"`. The same holds for `$nin` and `$not`. If you want "has a region, and it is not north", say both: `{ region: { $ne: "north", $exists: true } }`.

## Querying text with regular expressions

A **regular expression** (regex) is a compact pattern for describing text, for instance "starts with *Sl*" or "contains *ridge* in any letter case". MongoDB accepts them in filters:

```javascript
hike> db.trails.find({ name: /^Sl/ })          // names starting with "Sl" -> _id 2
hike> db.trails.find({ name: /hollow/i })      // contains "hollow", ignoring case -> _id 3
hike> db.trails.find({ name: { $regex: "pass$", $options: "i" } })   // ends with "pass" -> _id 4
```

The caret `^` anchors the pattern to the start of the text, the dollar sign anchors it to the end, and the trailing `i` means "ignore upper and lower case". Only a pattern anchored to the start and case-sensitive (like `/^Sl/`) can use an index efficiently; the others examine every value.

## Querying arrays

Arrays are where MongoDB's matching rules differ most from intuition. The governing rule is:

> A condition on an array field is satisfied if the array **as a whole** satisfies it **or any single element** satisfies it.

```javascript
hike> db.trails.find({ tags: "lake" })
// _id 1: the array contains "lake"

hike> db.trails.find({ tags: ["lake", "family"] })
// _id 1: the whole array equals this exact list, in this order

hike> db.trails.find({ tags: { $all: ["steep", "views"] } })
// _id 2: contains both, in any order

hike> db.trails.find({ tags: { $size: 0 } })
// _id 4: the array is empty

hike> db.trails.find({ "ratings.0": 5 })
// _id 1: the first element (position 0) is 5
```

So `{ tags: "lake" }` means "contains", while `{ tags: ["lake"] }` means "is exactly the one-element list". `$all` means "contains every one of these". `$size` matches an exact length (it cannot express "more than two"; store a count field for that).

### The range trap

Now the subtle part. What does this return?

```javascript
hike> db.trails.find({ ratings: { $gt: 8, $lt: 4 } })
```

No number is both above 8 and below 4, so you might expect nothing. Yet trail 2, with `ratings: [3, 9]`, is returned. Each operator is checked against the array separately: `$gt: 8` is satisfied by the 9, and `$lt: 4` is satisfied by the 3. Different elements may satisfy different conditions.

To demand that **one and the same element** satisfies all the conditions, use `$elemMatch`:

```javascript
hike> db.trails.find({ ratings: { $elemMatch: { $gte: 4, $lte: 5 } } })
// _id 1: it has an element that is between 4 and 5
```

`$elemMatch` reads "there is an element that matches all of this".

> [!WARNING]
> A range such as `{ ratings: { $gt: 3, $lt: 5 } }` on an array field does not mean "has a rating between 3 and 5". It means "has some rating above 3 **and** some (possibly different) rating below 5". Whenever two or more conditions must hold for the same array element, wrap them in `$elemMatch`.

## Querying embedded documents

There are two ways to match on an embedded document, and they behave very differently.

**Whole-document equality** compares the entire subdocument, including the order of its fields:

```javascript
hike> db.trails.find({ guide: { name: "Mira", years: 4 } })    // _id 1 and 3
hike> db.trails.find({ guide: { years: 4, name: "Mira" } })    // nothing: field order differs
hike> db.trails.find({ guide: { name: "Mira" } })              // nothing: the subdocument has more fields
```

**Dot notation** tests individual fields inside it and ignores the rest:

```javascript
hike> db.trails.find({ "guide.name": "Mira" })                 // _id 1 and 3
hike> db.trails.find({ "guide.years": { $gt: 10 } })           // _id 2
```

Dot notation is almost always what you want. It keeps working when someone later adds a field to the subdocument.

Dot notation also walks through arrays of documents. Suppose trails had `stops: [ { name: "hut", km: 3 }, { name: "falls", km: 8 } ]`. Then `{ "stops.name": "falls" }` matches if any stop is named falls. And the range trap returns in a new form: `{ "stops.name": "hut", "stops.km": { $gt: 5 } }` matches the example, because one stop is a hut and *another* stop is beyond 5 km. To ask for a hut beyond 5 km, write `{ stops: { $elemMatch: { name: "hut", km: { $gt: 5 } } } }`.

## Comparing two fields, and the `$where` caveat

Every operator so far compares a field with a constant you supply. Sometimes you need to compare two fields of the same document: "trails where the ascent in metres is more than a hundred times the length in kilometres".

The historical tool is `$where`, which runs a piece of JavaScript against each document:

```javascript
hike> db.trails.find({ $where: "this.ascent_m > this.km * 100" })
```

Avoid it. Three reasons:

1. **It is slow.** Each document must be converted into a JavaScript object and passed to a JavaScript engine. No index can be used, so every document in the collection is examined.
2. **It is a security risk.** If any part of that string comes from user input, an attacker can inject code that runs inside your database server. This class of attack is called **injection**.
3. **It is often disabled.** Many managed services switch server-side JavaScript off altogether.

The modern replacement is `$expr`, which evaluates an expression written with MongoDB's own operators, with no JavaScript involved:

```javascript
hike> db.trails.find({ $expr: { $gt: [ "$ascent_m", { $multiply: [ "$km", 100 ] } ] } })
```

Inside `$expr`, a string beginning with a dollar sign such as `"$km"` means "the value of the field `km` in this document". These expressions are the same ones the aggregation framework uses (module 5).

> [!INTERVIEW]
> **"A query on an array field returns documents that should not match. What do you check?"** First, whether several conditions were written on the array without `$elemMatch`: separate conditions can be satisfied by separate elements. Second, whether a negative operator (`$ne`, `$nin`) is matching documents in which the field is missing. Third, type mismatches - numbers stored as strings never match numeric ranges. Naming `$elemMatch` and the "missing field matches `$ne` and `null`" rule unprompted is what interviewers listen for.

## The same from Python

```python
import re
from pymongo import MongoClient

trails = MongoClient()["hike"]["trails"]

short_north = trails.find({"region": "north", "km": {"$lt": 10}})                   # 1
print([t["name"] for t in short_north])                                            # 2

print(trails.count_documents({"tags": {"$all": ["steep", "views"]}}))              # 3
print(trails.count_documents({"ratings": {"$elemMatch": {"$gte": 4, "$lte": 5}}})) # 4
print(trails.count_documents({"closed": None}))                                    # 5
print(trails.find_one({"name": re.compile("^sl", re.IGNORECASE)})["name"])        # 6

user_input = {"$ne": None}            # imagine this arrived as JSON from a login form
print(trails.count_documents({"name": user_input}))                                # 7
```

1. Operators are quoted dictionary keys. The filter has the same structure as in the shell.
2. Prints `['Heron Loop']`.
3. Prints `1` (Slate Ridge). `count_documents` returns how many documents match.
4. Prints `1` (Heron Loop).
5. Python's `None` is BSON `null`, so this prints `4`: one explicit null and three missing fields.
6. A compiled Python regular expression is sent as a BSON regular expression. Prints `Slate Ridge`.
7. Prints `4`. The "input" was not a string but an operator document, and it turned an equality test into "anything not null". When a web form's JSON body is placed straight into a filter, an attacker can do this to a password check. Always verify that values coming from users are of the expected plain type (a string, a number) before putting them in a filter.

## Simulate it yourself

The matcher below implements the array rule and a few operators over plain lists and dictionaries. Use it to convince yourself of the range trap and the missing-field rule.

```python-run
trails = [
    {"_id": 1, "name": "Heron Loop",   "region": "north", "km": 6,  "tags": ["lake", "family"], "ratings": [5, 4, 4]},
    {"_id": 2, "name": "Slate Ridge",  "region": "north", "km": 14, "tags": ["views", "steep"], "ratings": [3, 9]},
    {"_id": 3, "name": "Fern Hollow",  "region": "south", "km": 9,  "tags": ["forest"], "closed": None},
    {"_id": 4, "name": "Kestrel Pass", "km": 22, "tags": [], "ratings": []},
]

COMPARE = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b,
           "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}

def candidates(doc, field):
    """The values a condition may be tested against: the field itself and, for an array, each element."""
    if field not in doc:
        return []                               # missing field: nothing to test
    value = doc[field]
    return [value] + (value if isinstance(value, list) else [])

def test(op, arg, cands):
    if op == "$eq":
        return any(c == arg for c in cands) or (arg is None and not cands)   # null also matches "missing"
    if op == "$ne":
        return not test("$eq", arg, cands)      # true for a missing field!
    if op == "$in":
        return any(test("$eq", a, cands) for a in arg)
    if op == "$exists":
        return bool(cands) == arg
    if op == "$elemMatch":                      # ONE element must pass every inner operator
        elements = [c for c in cands if not isinstance(c, list)]
        return any(all(test(k, v, [e]) for k, v in arg.items()) for e in elements)
    numbers = [c for c in cands if isinstance(c, (int, float)) and not isinstance(c, bool)]
    return any(COMPARE[op](c, arg) for c in numbers)

def find(docs, query):
    out = []
    for doc in docs:
        ok = True
        for field, cond in query.items():
            cands = candidates(doc, field)
            if isinstance(cond, dict):          # operator document: every operator must hold
                ok = all(test(op, arg, cands) for op, arg in cond.items())
            else:                               # plain value: equality
                ok = test("$eq", cond, cands)
            if not ok:
                break
        if ok:
            out.append(doc["_id"])
    return out

queries = [
    {"region": "north"},
    {"km": {"$gte": 9, "$lte": 14}},
    {"tags": "lake"},
    {"region": {"$ne": "north"}},
    {"region": {"$ne": "north", "$exists": True}},
    {"closed": None},
    {"closed": {"$exists": True}},
    {"ratings": {"$gt": 8, "$lt": 4}},
    {"ratings": {"$elemMatch": {"$gt": 8, "$lt": 4}}},
    {"ratings": {"$elemMatch": {"$gte": 4, "$lte": 5}}},
]
for q in queries:
    print(str(q).ljust(52), "->", find(trails, q))
```

Reading the output:

- `{'region': {'$ne': 'north'}}` returns `[3, 4]`. Trail 4 has no region at all and still matches. Adding `$exists: True` narrows it to `[3]`.
- `{'closed': None}` returns all four ids; `$exists: True` returns only `[3]`.
- `{'ratings': {'$gt': 8, '$lt': 4}}` returns `[2]`: the 9 satisfies one condition and the 3 the other. The `$elemMatch` version of the same range returns `[]`, because no single rating is both above 8 and below 4.
- The last query returns `[1]`, the trail that has a rating between 4 and 5.

Try adding a trail with `ratings: [4]` and predict which queries change.

## Pitfalls

- **Range on an array without `$elemMatch`**: conditions are satisfied by different elements.
- **`$ne`, `$nin` and `$not` match documents lacking the field.** Add `$exists: true` if that is not wanted.
- **`{ field: null }` matches missing fields too.** Use `$type: "null"` or `$exists` to distinguish.
- **Whole-subdocument equality** depends on field order and breaks when fields are added. Use dot notation.
- **Type mismatches**: `"6"` is not `6`; a string id is not an ObjectId.
- **Unanchored or case-insensitive regular expressions** scan every value.
- **`$where` and unvalidated user input in filters** open the door to injection.
- **`$size` with a range.** It accepts only an exact number.

## Cheat sheet

| question | filter |
|---|---|
| equals | `{ f: v }` |
| range | `{ f: { $gte: a, $lt: b } }` |
| one of | `{ f: { $in: [a, b] } }` |
| either condition | `{ $or: [ {...}, {...} ] }` |
| field present | `{ f: { $exists: true } }` |
| present and not null | `{ f: { $ne: null } }` |
| value has a given type | `{ f: { $type: "string" } }` |
| array contains | `{ arr: v }` |
| array contains all | `{ arr: { $all: [a, b] } }` |
| array length | `{ arr: { $size: n } }` |
| one element meets several conditions | `{ arr: { $elemMatch: { ... } } }` |
| field inside a subdocument | `{ "sub.f": v }` |
| compare two fields | `{ $expr: { $gt: ["$a", "$b"] } }` |
| starts with | `{ f: /^abc/ }` |

## Summary

- A filter is a document; several fields in it are combined with *and*.
- Comparison operators (`$gt`, `$lt`, `$in`, ...) go inside a small document as the field's value; `$or`, `$and`, `$nor` and `$not` combine conditions.
- A missing field matches `null`, `$ne`, `$nin` and `$not`; use `$exists` and `$type` to be exact.
- A condition on an array holds if any element satisfies it; separate conditions may be met by separate elements unless wrapped in `$elemMatch`.
- Use dot notation for fields of embedded documents; whole-subdocument equality is exact and order-sensitive.
- Prefer `$expr` to `$where`, and never place unvalidated user input into a filter.

## Glossary

- **Query / filter** - a document describing which documents an operation should select.
- **Query operator** - a `$`-prefixed keyword expressing a condition, such as `$gt` or `$in`.
- **Implicit and** - the rule that all fields of one filter must match.
- **`$exists`** - tests whether a field is present in a document.
- **`$type`** - tests the BSON type of a field's value.
- **Regular expression (regex)** - a pattern describing a set of strings.
- **`$all`** - matches arrays containing every listed value.
- **`$elemMatch`** - matches arrays in which a single element satisfies all the given conditions.
- **Dot notation** - a path such as `"guide.name"` addressing a field inside an embedded document or array.
- **`$where`** - an operator that runs JavaScript per document; slow and risky.
- **`$expr`** - an operator that evaluates an aggregation expression, allowing fields to be compared with each other.
- **Injection** - an attack in which user input is interpreted as part of a query or as code.

## Check yourself

```quiz
[
  {"q": "A document has ratings: [3, 9]. Does {ratings: {$gt: 8, $lt: 4}} match it?",
   "options": ["No, because no number is both above 8 and below 4", "Yes, because 9 satisfies $gt: 8 and 3 satisfies $lt: 4", "It raises an error on arrays", "Only if the array is sorted"],
   "answer": 1,
   "explain": "Each operator may be satisfied by a different element. Use $elemMatch to require one element to satisfy both."},
  {"q": "Which documents does {region: {$ne: \"north\"}} return?",
   "options": ["Only documents whose region is a value other than north", "Documents whose region differs from north and documents with no region field", "Only documents without a region field", "Nothing"],
   "answer": 1,
   "explain": "Negative operators also match documents in which the field is missing."},
  {"q": "What does {closed: null} match?",
   "options": ["Only documents where closed is explicitly null", "Only documents without a closed field", "Documents where closed is null and documents without the field", "Documents where closed is false"],
   "answer": 2,
   "explain": "Querying for null matches both an explicit null and an absent field; use $exists or $type to tell them apart."},
  {"q": "A document has guide: {name: \"Mira\", years: 4}. Which filter matches it reliably even if more fields are added to guide later?",
   "options": ["{guide: {name: \"Mira\"}}", "{guide: {years: 4, name: \"Mira\"}}", "{\"guide.name\": \"Mira\"}", "{guide: \"Mira\"}"],
   "answer": 2,
   "explain": "Dot notation tests one inner field. Whole-subdocument equality requires the exact fields in the exact order."},
  {"q": "What is the difference between {tags: \"lake\"} and {tags: [\"lake\"]}?",
   "options": ["None", "The first matches arrays containing lake; the second matches only the exact array [\"lake\"]", "The first is an error", "The second matches arrays containing lake"],
   "answer": 1,
   "explain": "A scalar tests membership; an array literal tests equality with the whole array."},
  {"q": "Why should $where be avoided?",
   "options": ["It returns results in random order", "It runs JavaScript per document, cannot use indexes and is an injection risk", "It only works on arrays", "It modifies the documents it reads"],
   "answer": 1,
   "explain": "$where is slow and dangerous; $expr with built-in operators is the replacement for comparing fields."},
  {"q": "Which filter finds trails in the south or east regions most idiomatically?",
   "options": ["{region: \"south\", region: \"east\"}", "{region: {$in: [\"south\", \"east\"]}}", "{region: {$all: [\"south\", \"east\"]}}", "{region: {$size: 2}}"],
   "answer": 1,
   "explain": "$in matches any listed value. Repeating a key in one document is invalid, and $all would require both values at once."},
  {"q": "A login handler builds the filter {user: name, pass: pw} from JSON sent by the browser. What can go wrong?",
   "options": ["Nothing; filters are always safe", "The browser may send pw as {\"$ne\": null}, turning the equality into a condition that matches any password", "The query will be slow", "The document will be deleted"],
   "answer": 1,
   "explain": "Operator documents supplied as input change the meaning of the filter. Check that inputs are plain strings."}
]
```

> **Source:** MongoDB: The Definitive Guide 3e, ch. 4 (topics only; wording and examples are original). MongoDB Manual: https://www.mongodb.com/docs/manual/reference/operator/query/ , https://www.mongodb.com/docs/manual/tutorial/query-arrays/ , https://www.mongodb.com/docs/manual/reference/operator/query/where/
