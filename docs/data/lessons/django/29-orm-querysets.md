# Querysets in depth: laziness, lookups, Q and F

> **Before this lesson:** you have used `filter`, `exclude`, `order_by`, lookups such as `__icontains` and the idea of lazy evaluation ([ListView, querysets and tests with a database](#/lesson/django/listview-querysets)), and you have written custom queryset methods ([The Gazette: the stories app end to end](#/lesson/django/gazette-stories)). Basic SQL (`SELECT ... WHERE`) helps; see [SELECT and FROM](#/lesson/sql/select-from).

## In plain words

Every page of a Django site is, underneath, a few questions put to the database: "the ten newest published stories", "does this user exist?", "add one to this counter". The **ORM** (object-relational mapper) lets you ask in Python and translates your question into **SQL**, the database's own language.

Most of the time you can forget the translation. Performance and correctness problems begin exactly where you forget it for too long: a loop that quietly asks a thousand small questions, or two people clicking at once and one click being lost.

This lesson opens the translator. You will learn precisely *when* a query is sent, how to ask for "this OR that" and "NOT this" with **Q objects**, and how to tell the database to compute with its own current values using **F expressions**.

An everyday picture: ordering through an interpreter in a foreign restaurant. For "soup, please" you need not know the language. For "the fish, but only if it is fresh today, otherwise the lamb, and add one more bread to what the table already has", you had better understand what the interpreter will say, or you get a surprise and a larger bill.

Why it matters for a job: the ORM is where Django developers spend their careers and where senior and junior work differ most visibly. Interviewers ask about laziness, `Q`, `F` and race conditions in nearly every Django interview.

## From Python to SQL

Use the Gazette's `Story` model. In `python manage.py shell`:

```python
from stories.models import Story

qs = Story.objects.filter(section="harbour").exclude(status="draft").order_by("-published_at")[:5]
print(qs.query)
```

```sql
SELECT "stories_story"."id", "stories_story"."headline", ...
FROM "stories_story"
WHERE ("stories_story"."section" = harbour AND NOT ("stories_story"."status" = draft))
ORDER BY "stories_story"."published_at" DESC
LIMIT 5
```

Each method contributes one clause: `filter` and `exclude` build the `WHERE`, `order_by` the `ORDER BY`, the slice a `LIMIT`. Printing `qs.query` is the quickest way to learn what a queryset means. (The printed text omits quotes around values; the real query sends values separately as parameters.)

```mermaid
flowchart LR
    A[Story.objects.filter ... : a QuerySet object] --> B[Query: a tree describing tables, conditions, ordering]
    B --> C[SQL compiler for the configured database]
    C --> D[SQL text plus parameters]
    D --> E[(Database)]
    E --> F[Rows]
    F --> G[Model instances, cached on the QuerySet]
```

## Laziness, exactly

A queryset is a description. Nothing is sent until the queryset is **evaluated**. These operations evaluate:

| Operation | Example | SQL sent |
|---|---|---|
| Iteration | `for s in qs:` | `SELECT` all rows |
| `list()`, `tuple()` | `list(qs)` | `SELECT` all rows |
| `len()` | `len(qs)` | `SELECT` all rows, then counts in Python |
| `bool()` / `if qs:` | `if qs:` | `SELECT` all rows |
| Index or slice with a step | `qs[0]`, `qs[::2]` | `SELECT` with `LIMIT` |
| `repr()` | printing in the shell | `SELECT ... LIMIT 21` |

And these send their own, cheaper query **without** loading the rows:

| Method | SQL | Returns |
|---|---|---|
| `.count()` | `SELECT COUNT(*)` | an integer |
| `.exists()` | `SELECT 1 ... LIMIT 1` | `True` / `False` |
| `.first()`, `.last()` | `... LIMIT 1` | one object or `None` |
| `.get(...)` | `SELECT ...` | exactly one object, else an exception |
| `.aggregate(...)` | one summary row | a dictionary |

### The result cache and its trap

After a full evaluation, the rows are stored on that queryset object. Looping again is free. Three behaviours follow, and the third surprises people:

```python
qs = Story.objects.published()

for s in qs: ...        # query 1
for s in qs: ...        # no query: cache
qs.filter(section="sport")   # a NEW queryset with an empty cache; its evaluation is another query

qs2 = Story.objects.published()
qs2[0]                  # query (LIMIT 1); the cache is NOT filled by indexing
qs2[0]                  # the same query again
```

Indexing or slicing an **unevaluated** queryset asks the database every time. If you need several elements, evaluate once (`stories = list(qs)`) and index the list.

Templates trigger evaluation too. A queryset passed in the context is evaluated when the template loops over it, which is why queries appear "during rendering" in debugging tools.

### Fetching less

By default every column of every row is loaded and turned into a model instance. For large results, ask for less:

```python
Story.objects.values("id", "headline")            # dictionaries: {"id": 1, "headline": "..."}
Story.objects.values_list("id", "headline")       # tuples: (1, "...")
Story.objects.values_list("slug", flat=True)      # bare values: "harbour-reopens", ...
Story.objects.only("headline", "slug")            # model instances with only these columns loaded
Story.objects.defer("body")                       # model instances without the heavy column

for story in Story.objects.iterator(chunk_size=2000):   # stream rows; do not cache the whole result
    ...
```

`only` and `defer` have a sting: touching a column that was left out triggers a query **per object** to fetch it. Use them when you are certain which columns the code path reads.

## Q objects: OR, NOT and dynamic conditions

Keyword arguments to `filter` are joined with AND. For anything else, wrap conditions in `Q` objects and combine them with operators:

| Operator | Meaning | Example |
|---|---|---|
| `&` | AND | `Q(section="sport") & Q(status="published")` |
| `\|` | OR | `Q(section="sport") \| Q(section="culture")` |
| `~` | NOT | `~Q(status="draft")` |
| `^` | exclusive OR (Django 4.1+) | `Q(a=1) ^ Q(b=2)` |

```python
from django.db.models import Q

# headline or summary mentions "ferry", and the story is not a draft
Story.objects.filter(
    Q(headline__icontains="ferry") | Q(summary__icontains="ferry"),
    ~Q(status="draft"),
)
```

Positional `Q` arguments must come **before** keyword arguments, and several arguments to `filter` are ANDed together. Use parentheses generously: `&` binds tighter than `|`, as `and` does compared with `or`.

### Building a search step by step

Because `Q` objects are ordinary Python objects, a condition can be assembled in a loop. A search box in which every word must appear in the headline or the body:

```python
def search(text):
    query = Q()                                  # an empty Q matches everything
    for word in text.split():
        query &= Q(headline__icontains=word) | Q(body__icontains=word)
    return Story.objects.published().filter(query)
```

The model below shows what a `Q` tree is and how it becomes a `WHERE` clause. It supports `|`, `&` and `~` through Python's operator methods, the same technique Django uses.

```python-run
class Q:
    def __init__(self, **conditions):
        self.connector, self.negated = "AND", False
        self.children = list(conditions.items())       # leaves: ("field__lookup", value)

    def _combine(self, other, connector):
        node = Q()
        node.connector, node.children = connector, [self, other]
        return node

    def __or__(self, other):  return self._combine(other, "OR")
    def __and__(self, other): return self._combine(other, "AND")

    def __invert__(self):
        node = Q()
        node.children, node.negated = [self], True
        return node

    def as_sql(self):
        parts, params = [], []
        for child in self.children:
            if isinstance(child, Q):
                sql, child_params = child.as_sql()
                parts.append(f"({sql})")
                params += child_params
            else:
                key, value = child
                field, _, lookup = key.partition("__")
                operator = {"": "= ?", "icontains": "LIKE ?", "gte": ">= ?", "lt": "< ?"}[lookup]
                parts.append(f"{field} {operator}")
                params.append(f"%{value}%" if lookup == "icontains" else value)
        sql = f" {self.connector} ".join(parts)
        return (f"NOT ({sql})" if self.negated else sql), params

query = (Q(headline__icontains="ferry") | Q(summary__icontains="ferry")) & ~Q(status="draft")
sql, params = query.as_sql()
print("WHERE", sql)
print("params:", params)
```

The printed parameters travel separately from the SQL text. That separation is why user input in a lookup cannot change the structure of the query.

### `exclude` with several conditions

A subtle point worth memorising: `exclude(a=1, b=2)` removes rows where **both** hold. It is `NOT (a AND b)`, not "neither". To remove rows where either holds, chain two excludes or use `exclude(Q(a=1) | Q(b=2))`.

## F expressions: let the database use its own values

An `F("field")` object means "the value of this column **in the database, for the row being processed**". It has two main uses.

### Comparing two columns of the same row

```python
from django.db.models import F

Story.objects.filter(updated_at__gt=F("published_at"))            # edited after publication
Story.objects.filter(recommendations__gte=F("reply_count") * 2)   # arithmetic is allowed
```

Without `F` you would have to load every row and compare in Python.

### Updating without a race condition

The Gazette counts recommendations. The obvious code:

```python
story = Story.objects.get(pk=pk)       # read: recommendations is 41
story.recommendations += 1             # compute in Python: 42
story.save()                           # write 42
```

It is correct for one visitor at a time. With two visitors clicking in the same instant, both requests read 41, both compute 42 and both write 42. One click has vanished. This is a **race condition** called a **lost update**: the result depends on the unlucky timing of two requests.

The fix is to never bring the old value into Python:

```python
Story.objects.filter(pk=pk).update(recommendations=F("recommendations") + 1)
```

```sql
UPDATE stories_story SET recommendations = recommendations + 1 WHERE id = 7
```

The database reads and writes in one **atomic** statement (one that cannot be interleaved with another), so two clicks always add two.

The simulation below replays both versions with an unlucky schedule. Each request is split into its steps; the schedule decides who goes when.

```python-run
def run(schedule, use_f):
    db = {"recommendations": 41}
    local = {}                                    # each request's private Python variable
    for request, step in schedule:
        if use_f:
            if step == "update":
                db["recommendations"] = db["recommendations"] + 1    # one atomic statement in the database
        else:
            if step == "read":
                local[request] = db["recommendations"]               # SELECT
            elif step == "write":
                db["recommendations"] = local[request] + 1           # UPDATE ... SET recommendations = <python value>
    return db["recommendations"]

unlucky = [("A", "read"), ("B", "read"), ("A", "write"), ("B", "write")]     # interleaved
lucky   = [("A", "read"), ("A", "write"), ("B", "read"), ("B", "write")]     # one after the other

print("read-modify-write, lucky timing  :", run(lucky, use_f=False))
print("read-modify-write, unlucky timing:", run(unlucky, use_f=False), "<- one click lost")
print("F expression, any timing         :", run([("A", "update"), ("B", "update")], use_f=True))
```

One thing to remember after an `F` update: the Python object you hold still has the old value. Reload it with `story.refresh_from_db()` before displaying the number.

## `update()` versus `save()`, and working in bulk

| | `instance.save()` | `queryset.update(...)` |
|---|---|---|
| SQL | one `UPDATE` per object (all columns by default) | one `UPDATE` for all matching rows |
| Calls the model's `save()` | yes | no |
| Sends `pre_save` / `post_save` signals | yes | no |
| Updates `auto_now` fields | yes | no |
| Returns | nothing | the number of rows matched |

Use `save(update_fields=["headline"])` to write only named columns; it avoids overwriting a column another request changed meanwhile.

For many rows, the bulk methods cut thousands of statements to a handful:

```python
Reply.objects.bulk_create([Reply(story=s, author=member, text=t) for t in texts], batch_size=500)
Story.objects.bulk_update(stories, ["section"], batch_size=500)     # after changing .section on each
Story.objects.filter(status="draft", created_at__lt=cutoff).delete()
```

Like `update`, the bulk methods bypass `save()` and its signals.

### Find or create

```python
topic, created = Topic.objects.get_or_create(slug="ferry", defaults={"name": "Ferry"})
stats, created = StoryStats.objects.update_or_create(story=story, defaults={"views": 10})
```

The keyword arguments identify the row; `defaults` are used only when creating (or, for `update_or_create`, also when updating). Both can raise `IntegrityError` when two requests create the same row at once, so back them with a unique constraint on the identifying fields; Django then retries the lookup for you.

## A few more tools

Conditional values computed by the database, with `Case` and `When`:

```python
from django.db.models import Case, IntegerField, Value, When

Story.objects.annotate(
    priority=Case(
        When(section="harbour", then=Value(1)),
        When(recommendations__gte=50, then=Value(2)),
        default=Value(3),
        output_field=IntegerField(),
    )
).order_by("priority", "-published_at")
```

Subqueries and set operations:

```python
commented = Reply.objects.filter(author=member).values("story_id")
Story.objects.filter(pk__in=commented)                 # one query with a subquery, not two

sport = Story.objects.filter(section="sport")
culture = Story.objects.filter(section="culture")
sport.union(culture).order_by("-published_at")         # also intersection() and difference()
```

Passing a queryset to `__in` embeds it as a subquery; the inner queryset is never evaluated in Python.

## Seeing what is sent

```python
# in the shell (DEBUG must be True)
from django.db import connection, reset_queries

reset_queries()
list(Story.objects.published()[:5])
print(len(connection.queries), connection.queries[-1]["sql"])

print(Story.objects.published().explain())      # the database's execution plan
```

In tests, `assertNumQueries` pins the count; in the browser, the debug toolbar (covered in the lesson on caching) lists every query of a page.

## Tests

```python
# stories/test_orm.py
from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.test import TestCase
from django.utils import timezone

from .models import Story


class QuerysetBehaviourTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = get_user_model().objects.create_user("marisol", email="m@gazette.example", password="x")
        now = timezone.now()
        for headline, section, recs in [("Ferry strike looms", "harbour", 3), ("Regatta results", "sport", 60),
                                        ("Ferry timetable", "harbour", 0), ("Choir tour", "culture", 12)]:
            Story.objects.create(headline=headline, body="...", author=cls.member, section=section,
                                 status="published", published_at=now, recommendations=recs)

    def test_building_is_free_and_evaluation_is_cached(self):
        with self.assertNumQueries(0):
            qs = Story.objects.filter(section="harbour").order_by("headline")
        with self.assertNumQueries(1):
            list(qs)
            list(qs)                      # served from the cache

    def test_indexing_unevaluated_queryset_queries_each_time(self):
        qs = Story.objects.order_by("headline")
        with self.assertNumQueries(2):
            qs[0]
            qs[0]

    def test_q_or_and_not(self):
        found = Story.objects.filter(Q(section="sport") | Q(headline__icontains="ferry"), ~Q(recommendations=0))
        self.assertEqual({s.headline for s in found}, {"Regatta results", "Ferry strike looms"})

    def test_exclude_with_two_conditions_is_not_and(self):
        remaining = Story.objects.exclude(section="harbour", recommendations=0)
        self.assertEqual(remaining.count(), 3)          # only "Ferry timetable" matches both

    def test_f_update_is_atomic_and_instance_is_stale(self):
        story = Story.objects.get(headline="Choir tour")
        Story.objects.filter(pk=story.pk).update(recommendations=F("recommendations") + 1)
        Story.objects.filter(pk=story.pk).update(recommendations=F("recommendations") + 1)
        self.assertEqual(story.recommendations, 12)     # the Python object has not changed
        story.refresh_from_db()
        self.assertEqual(story.recommendations, 14)

    def test_exists_and_count_do_not_load_rows(self):
        with self.assertNumQueries(2):
            self.assertTrue(Story.objects.filter(section="sport").exists())
            self.assertEqual(Story.objects.count(), 4)
```

> [!NOTE]
> **What changed since the book.** The book uses only `all()` and simple filters. Newer ORM features relevant here: `Q` XOR (4.1), asynchronous query methods such as `aget`, `afirst` and `async for` (4.1), `bulk_create` with `update_conflicts` for upserts (4.1), `save(update_fields=...)` improvements, and `QuerySet.explain()` (2.1). Since 5.0, model fields can declare `db_default` so that the database supplies defaults for rows created outside Django.

> [!INTERVIEW]
> **"What is an F expression and when do you need it?"** `F("field")` refers to a column's value inside the database. It allows filters that compare two columns of the same row and updates expressed relative to the current value (`update(count=F("count") + 1)`), which compile to a single SQL statement. That makes increments safe under concurrency, where read-modify-write in Python loses updates. Mention the caveats: the in-memory instance is stale afterwards (`refresh_from_db`), and `update()` skips `save()` and signals. A natural follow-up is `select_for_update()` for cases where logic must run in Python between read and write, covered with transactions.

> [!WARNING]
> `if queryset:` and `len(queryset)` load every row. On a table with a million rows that is a memory spike and a slow page for a question that `exists()` or `count()` answers in a millisecond.

> [!TIP]
> When a queryset misbehaves, print `str(queryset.query)` before changing anything. Reading the SQL usually reveals the mistake at once: an unintended join, a missing condition, or an `exclude` that means something other than you thought.

## Pitfalls

- **Read-modify-write on counters.** Use `F` updates.
- **Stale objects after `update()`.** Call `refresh_from_db()`.
- **Repeated indexing of an unevaluated queryset.** Evaluate to a list first.
- **`only()`/`defer()` followed by access to a deferred field** in a loop: one query per object.
- **Expecting `update()` or `bulk_create()` to run `save()` logic or signals.** They do not.
- **Keyword arguments before `Q` objects.** A `SyntaxError`; positional arguments come first.
- **Forgetting parentheses** around `|` expressions combined with `&`.
- **`get()` on a non-unique condition.** `MultipleObjectsReturned` in production data that your test data did not reproduce.
- **`.count()` after you have already evaluated the queryset.** An unnecessary query; use `len()` on the evaluated result.

## Cheat sheet

| Need | Code |
|---|---|
| See the SQL | `print(qs.query)`, `qs.explain()` |
| Cheap existence / size | `qs.exists()`, `qs.count()` |
| OR / NOT | `Q(a=1) \| Q(b=2)`, `~Q(c=3)` |
| Dynamic conditions | start with `Q()` and combine in a loop |
| Compare columns | `filter(updated_at__gt=F("published_at"))` |
| Atomic increment | `qs.update(n=F("n") + 1)` |
| Reload an instance | `obj.refresh_from_db()` |
| Save some columns | `obj.save(update_fields=["headline"])` |
| Dictionaries / tuples | `values(...)`, `values_list(..., flat=True)` |
| Partial model loading | `only(...)`, `defer(...)` |
| Large result sets | `qs.iterator(chunk_size=2000)` |
| Many rows at once | `bulk_create`, `bulk_update`, `qs.update`, `qs.delete` |
| Find or create | `get_or_create(..., defaults={...})` |
| Subquery | `filter(pk__in=other_qs.values("story_id"))` |
| Conditional value | `Case(When(..., then=Value(1)), default=Value(0))` |

## Summary

- A queryset is a query description compiled to SQL at evaluation time; `print(qs.query)` shows the translation.
- Iteration, `list`, `len` and `bool` evaluate and cache; `exists`, `count`, `first` and `aggregate` run their own small queries; indexing an unevaluated queryset queries each time.
- `Q` objects express OR, NOT and dynamically built conditions; `exclude(a, b)` means NOT (a AND b).
- `F` expressions refer to column values inside the database, enabling column comparisons and atomic updates that avoid lost updates.
- `update()` and the bulk methods are fast because they bypass `save()` and signals; know when that matters.

## Glossary

- **ORM**: the layer translating between Python objects and SQL.
- **Evaluation**: the moment a queryset's SQL is executed and rows are loaded.
- **Result cache**: the rows remembered on a queryset after full evaluation.
- **Lookup**: the comparison part of a filter keyword, after the double underscore.
- **Q object**: an object wrapping conditions so that they can be combined with OR, AND and NOT.
- **F expression**: a reference to a column's value on the database side.
- **Race condition**: a bug whose occurrence depends on the timing of concurrent operations.
- **Lost update**: a race in which one of two concurrent writes overwrites the other.
- **Atomic**: executed as one indivisible step.
- **Subquery**: a query nested inside another query.
- **Bulk operation**: a single statement that creates, changes or deletes many rows.
- **Execution plan**: the database's description of how it will run a query (`explain`).

```quiz
[
  {"q": "Which of these does NOT load the matching rows into Python?",
   "options": ["list(qs)", "len(qs)", "qs.exists()", "if qs:"],
   "answer": 2,
   "explain": "exists() sends SELECT 1 ... LIMIT 1. The others evaluate the full queryset."},
  {"q": "`qs = Story.objects.order_by('headline')`; then `qs[0]` is executed twice. How many queries run?",
   "options": ["0", "1", "2", "It depends on DEBUG"],
   "answer": 2,
   "explain": "Indexing an unevaluated queryset issues a LIMIT query each time and does not fill the cache."},
  {"q": "What does `Story.objects.exclude(section='sport', status='draft')` remove?",
   "options": ["All sport stories and all drafts", "Only stories that are both sport and draft", "Nothing", "Stories that are neither"],
   "answer": 1,
   "explain": "Multiple conditions in one exclude are ANDed and then negated: NOT (sport AND draft)."},
  {"q": "How do you express 'section is sport OR recommendations >= 50'?",
   "options": ["filter(section='sport', recommendations__gte=50)", "filter(Q(section='sport') | Q(recommendations__gte=50))", "filter(section='sport').filter(recommendations__gte=50)", "filter(section='sport' or recommendations__gte=50)"],
   "answer": 1,
   "explain": "Keyword arguments and chained filters are ANDed. OR requires Q objects combined with |."},
  {"q": "Two requests run `s = Story.objects.get(pk=1); s.recommendations += 1; s.save()` at the same time, starting from 41. What can the final value be?",
   "options": ["Always 43", "42, because both read 41 and write 42", "41", "An IntegrityError is raised"],
   "answer": 1,
   "explain": "This is a lost update. Both compute from the same stale value. An F expression makes the increment atomic."},
  {"q": "After `Story.objects.filter(pk=s.pk).update(recommendations=F('recommendations') + 1)`, what does `s.recommendations` hold?",
   "options": ["The new value", "The old value until s.refresh_from_db() is called", "None", "An F object"],
   "answer": 1,
   "explain": "update() changes the database row, not Python objects already in memory."},
  {"q": "Which statement about `queryset.update()` is true?",
   "options": ["It calls each object's save() method", "It sends post_save signals", "It runs one SQL UPDATE and skips save() and signals", "It updates auto_now fields"],
   "answer": 2,
   "explain": "update is a set-based SQL operation. Per-object hooks do not run."},
  {"q": "What is the risk of `Story.objects.only('headline')` followed by reading `story.body` in a loop?",
   "options": ["A syntax error", "Each access triggers a separate query to load the deferred field", "The body is returned empty", "The headline is lost"],
   "answer": 1,
   "explain": "Deferred fields are fetched lazily per instance, recreating an N+1 pattern."}
]
```

> **Source:** beyond the book (Vincent, *Django for Beginners*, uses the ORM only at the level of ch. 4–5). Docs: https://docs.djangoproject.com/en/5.2/topics/db/queries/ · https://docs.djangoproject.com/en/5.2/ref/models/querysets/ · https://docs.djangoproject.com/en/5.2/ref/models/expressions/ · https://docs.djangoproject.com/en/5.2/topics/db/optimization/
