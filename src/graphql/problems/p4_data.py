"""GraphQL track problems, part 4: pagination, filtering, sorting and mutations."""

ITEMS = [{"id": "r%d" % i, "title": "Recipe %d" % i} for i in range(1, 8)]
BIG = [{"id": i, "t": "x%d" % i} for i in range(500)]

RECIPES = [
    {"id": 1, "title": "Lentil soup", "category": "SOUP", "minutes": 35, "rating": 4.5, "tags": ["vegan", "winter"]},
    {"id": 2, "title": "flatbread", "category": "BREAD", "minutes": 20, "rating": 4.5, "tags": ["vegan", "quick"]},
    {"id": 3, "title": "Plum cake", "category": "DESSERT", "minutes": 70, "rating": 4.9, "tags": ["baking"]},
    {"id": 4, "title": "Tomato Soup", "category": "SOUP", "minutes": 20, "rating": 3.8, "tags": ["quick"]},
    {"id": 5, "title": "Sourdough", "category": "BREAD", "minutes": 240, "rating": 4.7, "tags": []},
    {"id": 6, "title": "apple crumble", "category": "DESSERT", "minutes": 35, "rating": 4.5, "tags": ["baking", "winter"]},
    {"id": 7, "title": "Miso soup", "category": "SOUP", "minutes": 10, "rating": 4.1, "tags": ["quick", "vegan"]},
]

STATE = {"recipes": [{"id": "r1", "title": "Lentil soup", "minutes": 35, "category": "SOUP", "servings": 4}], "nextId": 2}

PROBLEMS = [
dict(
    id="gql-offset-pagination",
    title="Offset pagination",
    difficulty="Easy",
    pattern="Pagination",
    entry="page",
    description=r"""
The oldest way to split a long list into pages is **limit and offset**: "skip `offset` items, then give me `limit` items".

`page(items, limit, offset)` returns

```
{"items": [...], "total": <length of the full list>, "hasMore": bool, "nextOffset": int or None}
```

Rules (a public API must defend itself from bad input, so the server normalises the arguments first):

- `limit` of `None` means the default **10**. A limit above **50** is reduced to 50. A negative limit becomes 0.
- `offset` of `None` or a negative number becomes 0.
- `items` in the result are the items at positions `offset` … `offset + limit - 1` that exist.
- `hasMore` is `True` when at least one item exists after the last position covered by this page.
- `nextOffset` is the offset to send for the following page (`offset +` the number of items returned), or `None` when `hasMore` is `False`.

**Example:** 7 items, `page(items, 3, 0)` → the first 3 items, `total` 7, `hasMore` `True`, `nextOffset` 3.

**Example:** `page(items, 3, 6)` → the last item, `hasMore` `False`, `nextOffset` `None`.
""",
    starter='''def page(items, limit, offset):
    pass
''',
    solution='''def page(items, limit, offset):
    limit = 10 if limit is None else max(0, min(limit, 50))
    offset = 0 if offset is None else max(0, offset)
    chunk = items[offset:offset + limit]
    end = offset + len(chunk)
    has_more = end < len(items)
    return {"items": chunk, "total": len(items), "hasMore": has_more, "nextOffset": end if has_more else None}
''',
    tests=[
        [ITEMS, 3, 0],
        [ITEMS, 3, 6],
        [ITEMS, 3, 3],
        [ITEMS, None, None],
        [BIG, None, 20],
        [BIG, 1000, 0],
        [BIG, 50, 450],
        [ITEMS, 7, 0],
        [ITEMS, 5, 99],
        [ITEMS, 0, 2],
        [ITEMS, -4, -2],
        [[], 5, 0],
        [ITEMS, 2, 7],
        [BIG, 50, 451],
    ],
    examples=2,
    wrong_solutions=[
        '''def page(items, limit, offset):
    limit = limit or 10
    offset = offset or 0
    chunk = items[offset:offset + limit]
    return {"items": chunk, "total": len(items), "hasMore": len(chunk) == limit, "nextOffset": offset + limit if len(chunk) == limit else None}
''',
        '''def page(items, limit, offset):
    limit = 10 if limit is None else max(0, min(limit, 50))
    offset = offset or 0
    chunk = items[offset:offset + limit]
    end = offset + len(chunk)
    has_more = end < len(items)
    return {"items": chunk, "total": len(items), "hasMore": has_more, "nextOffset": end if has_more else None}
''',
    ],
    guide=dict(
        prereqs="Python list slicing (`items[a:b]` never raises, even when `b` is past the end). The lesson *Arguments, filtering, pagination and sorting*.",
        intuition="Offset pagination is a ruler laid over the list: start at mark `offset`, measure `limit` items. Everything else is defence: clamp the arguments into a sane range before using them, and compute 'is there more?' from where the page actually ended, not from where it was supposed to end.",
        hints=[
            "Normalise `limit` and `offset` first, in two lines, before touching the list.",
            "A slice past the end of a list returns fewer items (or none). Use `len(chunk)` to learn how many you really got.",
            "`hasMore` is `offset + len(chunk) < len(items)`.",
        ],
        brute_force="Loop with a counter, skipping `offset` items and appending until `limit` are collected. Same O(offset + limit) work as the slice but more code and more places for off-by-one mistakes.",
        approach="""1. Clamp: `limit = 10 if None else max(0, min(limit, 50))`; `offset = 0 if None else max(0, offset)`.
2. `chunk = items[offset:offset + limit]`.
3. `end = offset + len(chunk)`; `hasMore = end < len(items)`; `nextOffset = end if hasMore else None`.

**Dry run** 7 items, `limit=3`, `offset=6`: chunk has 1 item (index 6); `end = 7`; `7 < 7` is false → `hasMore False`, `nextOffset None`.""",
        complexity="Time O(limit) for the slice (in a database, O(offset + limit): the skipped rows are still read, which is the main weakness of this style). Space O(limit).",
        pitfalls="- `limit or 10` turns a deliberate `0` into 10.\n- Guessing `hasMore` from `len(chunk) == limit` is wrong when the list ends exactly on a page boundary.\n- No upper bound on `limit` lets one request fetch the whole table.\n- A negative offset in a Python slice counts from the end and silently returns the wrong rows.",
        follow_up="If a new item is inserted at the front between two requests, which item does the client see twice? `gql-cursor-pagination` fixes that.",
    ),
),
dict(
    id="gql-cursor-pagination",
    title="Relay-style cursor connection",
    difficulty="Medium",
    pattern="Pagination",
    entry="paginate",
    description=r"""
Most production GraphQL APIs page through lists with a **connection**: every item is wrapped in an **edge** that carries a
**cursor** (a bookmark for that item), and a `pageInfo` object says whether more pages exist.

`paginate(items, first, after)`

- `items`: the full ordered list of dictionaries, each with a unique `"id"`.
- `first`: how many items to return (an integer ≥ 0).
- `after`: a cursor string or `None`. The cursor of an item is the text `"cur:"` followed by its id (`"cur:r3"`).

Return

```
{
  "edges": [{"cursor": "cur:r1", "node": {...item...}}, ...],
  "pageInfo": {"hasNextPage": bool, "hasPreviousPage": bool, "startCursor": str or None, "endCursor": str or None},
  "totalCount": <length of the full list>
}
```

Rules:

1. If `after` matches an item's cursor, the page starts with the item **after** it. If `after` is `None` or matches nothing, start from the beginning.
2. Take at most `first` items from there.
3. `hasNextPage`: there is at least one item after the last returned position (when no items are returned: after the start position).
4. `hasPreviousPage`: there is at least one item before the start position.
5. `startCursor` / `endCursor`: cursors of the first and last returned edges, or `None` when there are no edges.

**Example:** ids `r1…r7`, `paginate(items, 2, "cur:r2")` → edges for `r3`, `r4`; `hasNextPage` `True`; `hasPreviousPage` `True`; `endCursor` `"cur:r4"`.
""",
    starter='''def paginate(items, first, after):
    pass
''',
    solution='''def paginate(items, first, after):
    start = 0
    if after is not None:
        for i, item in enumerate(items):
            if "cur:" + str(item["id"]) == after:
                start = i + 1
                break
    chunk = items[start:start + first]
    edges = [{"cursor": "cur:" + str(item["id"]), "node": item} for item in chunk]
    return {
        "edges": edges,
        "pageInfo": {
            "hasNextPage": start + len(chunk) < len(items),
            "hasPreviousPage": start > 0,
            "startCursor": edges[0]["cursor"] if edges else None,
            "endCursor": edges[-1]["cursor"] if edges else None,
        },
        "totalCount": len(items),
    }
''',
    tests=[
        [ITEMS, 2, "cur:r2"],
        [ITEMS, 3, None],
        [ITEMS, 3, "cur:r4"],
        [ITEMS, 3, "cur:r5"],
        [ITEMS, 10, "cur:r7"],
        [ITEMS, 0, "cur:r3"],
        [ITEMS, 0, None],
        [ITEMS, 2, "cur:zzz"],
        [ITEMS, 2, "r2"],
        [[], 5, None],
        [ITEMS, 7, None],
        [ITEMS, 1, "cur:r6"],
        [BIG, 25, "cur:473"],
        [[{"id": 1}, {"id": 11}, {"id": 111}], 5, "cur:11"],
    ],
    examples=2,
    wrong_solutions=[
        '''def paginate(items, first, after):
    start = 0
    if after is not None:
        for i, item in enumerate(items):
            if "cur:" + str(item["id"]) == after:
                start = i
                break
    chunk = items[start:start + first]
    edges = [{"cursor": "cur:" + str(item["id"]), "node": item} for item in chunk]
    return {"edges": edges, "pageInfo": {"hasNextPage": start + len(chunk) < len(items), "hasPreviousPage": start > 0,
            "startCursor": edges[0]["cursor"] if edges else None, "endCursor": edges[-1]["cursor"] if edges else None},
            "totalCount": len(items)}
''',
        '''def paginate(items, first, after):
    start = 0
    if after is not None:
        for i, item in enumerate(items):
            if "cur:" + str(item["id"]) == after:
                start = i + 1
                break
    chunk = items[start:start + first]
    edges = [{"cursor": "cur:" + str(item["id"]), "node": item} for item in chunk]
    return {"edges": edges, "pageInfo": {"hasNextPage": len(chunk) == first, "hasPreviousPage": after is not None,
            "startCursor": edges[0]["cursor"] if edges else None, "endCursor": edges[-1]["cursor"] if edges else None},
            "totalCount": len(items)}
''',
        '''def paginate(items, first, after):
    start = 0
    if after is not None:
        for i, item in enumerate(items):
            if str(item["id"]) in after:
                start = i + 1
                break
    chunk = items[start:start + first]
    edges = [{"cursor": "cur:" + str(item["id"]), "node": item} for item in chunk]
    return {"edges": edges, "pageInfo": {"hasNextPage": start + len(chunk) < len(items), "hasPreviousPage": start > 0,
            "startCursor": edges[0]["cursor"] if edges else None, "endCursor": edges[-1]["cursor"] if edges else None},
            "totalCount": len(items)}
''',
    ],
    guide=dict(
        prereqs="`gql-offset-pagination`; the pagination section of *Arguments, filtering, pagination and sorting*; the vocabulary *edge* and *node* from the graph theory module.",
        intuition="An offset says 'skip 20 items', which points at a different item whenever the list changes. A cursor says 'continue after *this* item', like a bookmark stuck on a page instead of a page number. The server turns the bookmark back into a position, then does the same slicing as before. The extra wrapper (`edges`, `pageInfo`) exists so the client always knows the bookmark for every item and whether to show a 'load more' button.",
        hints=[
            "First convert `after` into a start index. Unknown or missing cursor → index 0.",
            "The item *after* the cursor is at index `i + 1`, not `i`.",
            "Compute both booleans from `start` and the number of items returned; do not derive them from `first` or from whether `after` was supplied.",
        ],
        brute_force="Loop through all items with a flag `seen_cursor`, collecting items once the flag is set. It is the same O(n) scan, but mixing the search and the collecting makes the unknown-cursor case (start from the beginning) awkward.",
        approach="""1. Find `start`.
2. `chunk = items[start:start + first]`; wrap each item in an edge.
3. `hasNextPage = start + len(chunk) < len(items)`; `hasPreviousPage = start > 0`.

**Dry run** ids r1…r7, `first=2`, `after="cur:r2"`:

| step | value |
|---|---|
| cursor matches index | 1 → `start = 2` |
| chunk | r3, r4 |
| hasNextPage | `2 + 2 < 7` → True |
| hasPreviousPage | `2 > 0` → True |
| startCursor / endCursor | `cur:r3` / `cur:r4` |""",
        complexity="Time O(n) to locate the cursor in a plain list plus O(first) to build the page. A database does the lookup with an index (`WHERE id > ? ORDER BY id LIMIT ?`) in O(log n + first). Space O(first).",
        pitfalls="- Starting *at* the cursor repeats the last item of the previous page.\n- `hasNextPage = len(chunk) == first` is wrong when the list ends exactly at the page boundary, and wrong for `first = 0`.\n- Substring matching: the cursor `cur:11` must not match id `1`.\n- Indexing `edges[0]` on an empty page raises `IndexError`.",
        follow_up="Add backward paging with `last` and `before`. Make the cursor opaque by base64-encoding it so clients cannot build cursors by hand.",
    ),
),
dict(
    id="gql-filter-sort",
    title="Filtering and sorting arguments",
    difficulty="Medium",
    pattern="Arguments",
    entry="query_recipes",
    description=r"""
Implement the resolver behind this field:

```graphql
recipes(filter: RecipeFilter, sort: RecipeSort): [Recipe!]!
```

`query_recipes(recipes, filter, sort)` returns the **list of ids** of the matching recipes, in order.

Each recipe is `{"id": int, "title": str, "category": str, "minutes": int, "rating": float, "tags": [str]}`.

**`filter`** is `None` or a dictionary; every key is optional, and a key whose value is `None` is ignored.
A recipe must satisfy **all** conditions that are present (logical AND):

| key | condition |
|---|---|
| `category` | recipe's category equals it |
| `maxMinutes` | recipe's minutes ≤ it |
| `titleContains` | the text occurs in the title, ignoring upper/lower case |
| `tagsAny` | the recipe has at least one of the listed tags (an empty list matches nothing) |

**`sort`** is `None` (keep the incoming order) or `{"field": ..., "direction": ...}` with field `"title"`, `"minutes"` or
`"rating"` and direction `"ASC"` or `"DESC"` (default `"ASC"` when the key is missing). Titles compare ignoring case.
Recipes with equal sort values are ordered by **ascending id in both directions**.

Do not modify the input list.

**Example:** `filter = {"category": "SOUP"}`, `sort = {"field": "minutes", "direction": "ASC"}` → `[7, 4, 1]`
""",
    starter='''def query_recipes(recipes, filter, sort):
    pass
''',
    solution='''def query_recipes(recipes, filter, sort):
    f = filter or {}

    def keep(r):
        if f.get("category") is not None and r["category"] != f["category"]:
            return False
        if f.get("maxMinutes") is not None and r["minutes"] > f["maxMinutes"]:
            return False
        if f.get("titleContains") is not None and f["titleContains"].lower() not in r["title"].lower():
            return False
        if f.get("tagsAny") is not None and not (set(f["tagsAny"]) & set(r["tags"])):
            return False
        return True

    rows = [r for r in recipes if keep(r)]
    if sort:
        field = sort["field"]
        key = (lambda r: r["title"].lower()) if field == "title" else (lambda r: r[field])
        rows.sort(key=lambda r: r["id"])
        rows.sort(key=key, reverse=sort.get("direction") == "DESC")
    return [r["id"] for r in rows]
''',
    tests=[
        [RECIPES, {"category": "SOUP"}, {"field": "minutes", "direction": "ASC"}],
        [RECIPES, None, None],
        [RECIPES, {"maxMinutes": 35}, {"field": "rating", "direction": "DESC"}],
        [RECIPES, {"titleContains": "SOUP"}, None],
        [RECIPES, {"tagsAny": ["quick", "baking"]}, {"field": "title"}],
        [RECIPES, {"tagsAny": []}, None],
        [RECIPES, {"category": None, "maxMinutes": None, "titleContains": None, "tagsAny": None}, {"field": "title", "direction": "DESC"}],
        [RECIPES, {"category": "SOUP", "maxMinutes": 20, "tagsAny": ["vegan"]}, None],
        [RECIPES, {}, {"field": "rating", "direction": "ASC"}],
        [RECIPES, {}, {"field": "minutes", "direction": "DESC"}],
        [list(reversed(RECIPES)), {}, {"field": "rating", "direction": "DESC"}],
        [list(reversed(RECIPES)), {"maxMinutes": 0}, {"field": "title"}],
        [[], {"category": "SOUP"}, {"field": "title"}],
        [RECIPES, {"titleContains": ""}, {"field": "minutes"}],
        [[{"id": i, "title": "T", "category": "MAIN", "minutes": i % 3, "rating": 4.0, "tags": ["a"]} for i in range(60, 0, -1)], {"tagsAny": ["a", "b"]}, {"field": "minutes", "direction": "DESC"}],
    ],
    examples=2,
    wrong_solutions=[
        '''def query_recipes(recipes, filter, sort):
    f = filter or {}
    def keep(r):
        if f.get("category") is not None and r["category"] != f["category"]: return False
        if f.get("maxMinutes") is not None and r["minutes"] > f["maxMinutes"]: return False
        if f.get("titleContains") is not None and f["titleContains"].lower() not in r["title"].lower(): return False
        if f.get("tagsAny") is not None and not (set(f["tagsAny"]) & set(r["tags"])): return False
        return True
    rows = [r for r in recipes if keep(r)]
    if sort:
        field = sort["field"]
        key = (lambda r: (r["title"].lower(), r["id"])) if field == "title" else (lambda r: (r[field], r["id"]))
        rows.sort(key=key, reverse=sort.get("direction") == "DESC")
    return [r["id"] for r in rows]
''',
        '''def query_recipes(recipes, filter, sort):
    f = filter or {}
    def keep(r):
        if f.get("category") and r["category"] != f["category"]: return False
        if f.get("maxMinutes") and r["minutes"] > f["maxMinutes"]: return False
        if f.get("titleContains") and f["titleContains"] not in r["title"]: return False
        if f.get("tagsAny") and not (set(f["tagsAny"]) & set(r["tags"])): return False
        return True
    rows = [r for r in recipes if keep(r)]
    if sort:
        field = sort["field"]
        rows.sort(key=lambda r: r["id"])
        rows.sort(key=lambda r: r[field], reverse=sort.get("direction") == "DESC")
    return [r["id"] for r in rows]
''',
    ],
    guide=dict(
        prereqs="List comprehensions, `sorted` / `list.sort` with a `key`, and the fact that Python's sort is *stable* (items that compare equal keep their previous relative order). The lesson *Arguments, filtering, pagination and sorting*.",
        intuition="A filter object is a stack of optional sieves. A sieve that was not supplied lets everything through. Sorting needs a tie-breaker to be repeatable: without one, two recipes with the same rating could swap places between requests and pagination would show duplicates.",
        hints=[
            "Write a helper `keep(recipe)` that returns `False` as soon as one present condition fails.",
            "Use `is not None` to decide whether a condition is present. `0`, `\"\"` and `[]` are real values.",
            "To get 'ties by ascending id' in both directions, sort by id first, then do a second stable sort by the chosen field (with `reverse=True` for DESC, which still keeps ties in their existing order).",
        ],
        brute_force="Write one branch per combination of filters. With 4 optional filters that is 16 branches; with 10 filters it is 1,024. Independent checks combined with AND scale linearly instead.",
        approach="""1. Filter with `keep`.
2. If `sort` is given: stable sort by id, then stable sort by the field.
3. Return ids.

**Dry run** `{"category": "SOUP"}` sorted by minutes ASC: SOUP recipes are 1 (35 min), 4 (20), 7 (10). Sorted by id: 1, 4, 7. Sorted by minutes: 7 (10), 4 (20), 1 (35) → `[7, 4, 1]`.""",
        complexity="Time O(n·t) to filter n recipes with t tags each, plus O(m log m) to sort the m survivors. Space O(m).",
        pitfalls="- Sorting DESC with a key of `(value, id)` and `reverse=True` reverses the ids too.\n- `if f.get(\"maxMinutes\"):` skips the filter when the value is `0`; `if f.get(\"tagsAny\"):` skips an empty list that should match nothing.\n- Case-sensitive title matching and sorting (`\"apple\"` sorts after `\"Sourdough\"` in plain string order).\n- Calling `recipes.sort()` mutates the caller's list.",
        follow_up="In a real resolver these arguments become a SQL `WHERE ... ORDER BY ..., id` clause. Which columns need an index?",
    ),
),
dict(
    id="gql-mutation-input",
    title="A mutation with an input object and validation errors",
    difficulty="Medium",
    pattern="Mutations",
    entry="create_recipe",
    description=r"""
Implement the resolver for

```graphql
createRecipe(input: CreateRecipeInput!): CreateRecipePayload!
```

`create_recipe(state, input)` where `state = {"recipes": [...], "nextId": int}` and `input` is a dictionary.
Return the payload `{"recipe": ..., "errors": [...], "state": ...}`.

**Validation.** Collect *every* problem, as `{"field": name, "message": text}`, in this field order:

| field | rule | message |
|---|---|---|
| `title` | must be a string that is not empty after trimming spaces | `Title is required.` |
| `title` | trimmed length ≤ 60 | `Title must be at most 60 characters.` |
| `title` | no existing recipe has the same trimmed title, ignoring case | `Title is already taken.` |
| `minutes` | an integer (not a boolean) from 1 to 1440 | `Minutes must be between 1 and 1440.` |
| `category` | one of `SOUP`, `BREAD`, `MAIN`, `DESSERT` | `Category must be one of SOUP, BREAD, MAIN, DESSERT.` |
| `servings` | optional; missing or `None` means 4; otherwise an integer (not a boolean) ≥ 1 | `Servings must be at least 1.` |

At most one error per field: the title rules are checked top to bottom and the first failure wins.

**Outcome.**

- Any error → `recipe` is `None`, `errors` is the list, `state` is returned unchanged.
- No error → the new recipe is `{"id": "r<nextId>", "title": <trimmed>, "minutes", "category", "servings"}`; `errors` is `[]`;
  the returned `state` has the recipe appended and `nextId` increased by 1.

Never modify the `state` or `input` objects you were given; build new ones.

**Example:** `input = {"title": " Flatbread ", "minutes": 20, "category": "BREAD"}` on a state with `nextId` 2 →
recipe `{"id": "r2", "title": "Flatbread", "minutes": 20, "category": "BREAD", "servings": 4}`.
""",
    starter='''def create_recipe(state, input):
    pass
''',
    solution='''CATEGORIES = ["SOUP", "BREAD", "MAIN", "DESSERT"]

def create_recipe(state, input):
    errors = []

    def is_int(v):
        return isinstance(v, int) and not isinstance(v, bool)

    title = input.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append({"field": "title", "message": "Title is required."})
    else:
        title = title.strip()
        if len(title) > 60:
            errors.append({"field": "title", "message": "Title must be at most 60 characters."})
        elif any(r["title"].lower() == title.lower() for r in state["recipes"]):
            errors.append({"field": "title", "message": "Title is already taken."})
    minutes = input.get("minutes")
    if not is_int(minutes) or not 1 <= minutes <= 1440:
        errors.append({"field": "minutes", "message": "Minutes must be between 1 and 1440."})
    category = input.get("category")
    if category not in CATEGORIES:
        errors.append({"field": "category", "message": "Category must be one of SOUP, BREAD, MAIN, DESSERT."})
    servings = input.get("servings")
    if servings is None:
        servings = 4
    elif not is_int(servings) or servings < 1:
        errors.append({"field": "servings", "message": "Servings must be at least 1."})
    if errors:
        return {"recipe": None, "errors": errors, "state": state}
    recipe = {"id": "r%d" % state["nextId"], "title": title, "minutes": minutes, "category": category, "servings": servings}
    new_state = {"recipes": state["recipes"] + [recipe], "nextId": state["nextId"] + 1}
    return {"recipe": recipe, "errors": [], "state": new_state}
''',
    tests=[
        [STATE, {"title": " Flatbread ", "minutes": 20, "category": "BREAD"}],
        [STATE, {"title": "", "minutes": 0, "category": "SNACK"}],
        [STATE, {"title": "lentil SOUP", "minutes": 30, "category": "SOUP", "servings": 2}],
        [STATE, {"title": "   ", "minutes": 30, "category": "SOUP"}],
        [STATE, {"minutes": 30, "category": "SOUP"}],
        [STATE, {"title": "x" * 61, "minutes": 1440, "category": "MAIN"}],
        [STATE, {"title": "  " + "x" * 60 + "  ", "minutes": 1, "category": "MAIN", "servings": None}],
        [STATE, {"title": "Stew", "minutes": 1441, "category": "MAIN", "servings": 0}],
        [STATE, {"title": "Stew", "minutes": True, "category": "MAIN", "servings": True}],
        [STATE, {"title": "Stew", "minutes": "20", "category": "main", "servings": 1}],
        [STATE, {"title": 42, "minutes": 12.5, "category": None, "servings": -3}],
        [{"recipes": [], "nextId": 10}, {"title": "Plum cake", "minutes": 70, "category": "DESSERT", "servings": 8, "ignored": "yes"}],
        [STATE, {}],
    ],
    examples=2,
    wrong_solutions=[
        '''CATEGORIES = ["SOUP", "BREAD", "MAIN", "DESSERT"]
def create_recipe(state, input):
    title = input.get("title")
    if not isinstance(title, str) or not title.strip():
        return {"recipe": None, "errors": [{"field": "title", "message": "Title is required."}], "state": state}
    title = title.strip()
    if len(title) > 60:
        return {"recipe": None, "errors": [{"field": "title", "message": "Title must be at most 60 characters."}], "state": state}
    if any(r["title"].lower() == title.lower() for r in state["recipes"]):
        return {"recipe": None, "errors": [{"field": "title", "message": "Title is already taken."}], "state": state}
    minutes = input.get("minutes")
    if not isinstance(minutes, int) or isinstance(minutes, bool) or not 1 <= minutes <= 1440:
        return {"recipe": None, "errors": [{"field": "minutes", "message": "Minutes must be between 1 and 1440."}], "state": state}
    category = input.get("category")
    if category not in CATEGORIES:
        return {"recipe": None, "errors": [{"field": "category", "message": "Category must be one of SOUP, BREAD, MAIN, DESSERT."}], "state": state}
    servings = input.get("servings")
    if servings is None:
        servings = 4
    elif not isinstance(servings, int) or isinstance(servings, bool) or servings < 1:
        return {"recipe": None, "errors": [{"field": "servings", "message": "Servings must be at least 1."}], "state": state}
    recipe = {"id": "r%d" % state["nextId"], "title": title, "minutes": minutes, "category": category, "servings": servings}
    return {"recipe": recipe, "errors": [], "state": {"recipes": state["recipes"] + [recipe], "nextId": state["nextId"] + 1}}
''',
        '''CATEGORIES = ["SOUP", "BREAD", "MAIN", "DESSERT"]
def create_recipe(state, input):
    errors = []
    title = input.get("title")
    if not title:
        errors.append({"field": "title", "message": "Title is required."})
    elif len(title) > 60:
        errors.append({"field": "title", "message": "Title must be at most 60 characters."})
    elif any(r["title"] == title for r in state["recipes"]):
        errors.append({"field": "title", "message": "Title is already taken."})
    minutes = input.get("minutes")
    if not isinstance(minutes, int) or not 1 <= minutes <= 1440:
        errors.append({"field": "minutes", "message": "Minutes must be between 1 and 1440."})
    category = input.get("category")
    if category not in CATEGORIES:
        errors.append({"field": "category", "message": "Category must be one of SOUP, BREAD, MAIN, DESSERT."})
    servings = input.get("servings") or 4
    if not isinstance(servings, int) or servings < 1:
        errors.append({"field": "servings", "message": "Servings must be at least 1."})
    if errors:
        return {"recipe": None, "errors": errors, "state": state}
    recipe = {"id": "r%d" % state["nextId"], "title": title, "minutes": minutes, "category": category, "servings": servings}
    return {"recipe": recipe, "errors": [], "state": {"recipes": state["recipes"] + [recipe], "nextId": state["nextId"] + 1}}
''',
    ],
    guide=dict(
        prereqs="The lesson *Mutations, input types, return types and subscriptions*; `isinstance`; string methods `strip` and `lower`.",
        intuition="A good mutation answers with a **payload**: either the thing that was created, or a list of everything that was wrong, so a form can highlight all the bad fields in one go. Mistakes the user can fix (a title that is too long) are data, not exceptions. The resolver has three stages: validate everything, stop if anything failed, otherwise build new state.",
        hints=[
            "Create an empty `errors` list and append to it; do not `return` at the first problem.",
            "For the title, the three rules form an `if / elif / elif` chain so only the first failure is reported.",
            "Build the new state with `state[\"recipes\"] + [recipe]` (a new list) instead of `append` (which changes the caller's list).",
        ],
        brute_force="Return as soon as one rule fails. The user fixes the title, submits, learns the minutes are wrong, fixes them, submits, learns the category is wrong. Three round trips instead of one.",
        approach="""1. Validate `title` (chain), `minutes`, `category`, `servings` in that order, appending errors.
2. If `errors` is non-empty: `{"recipe": None, "errors": errors, "state": state}`.
3. Otherwise build the recipe with id `"r" + nextId` and a new state.

**Dry run** `{"title": "", "minutes": 0, "category": "SNACK"}`:

| field | check | error |
|---|---|---|
| title | empty after trim | Title is required. |
| minutes | 0 not in 1..1440 | Minutes must be between 1 and 1440. |
| category | not in the enum | Category must be one of ... |
| servings | missing → 4 | none |

Three errors, recipe `None`, state unchanged.""",
        complexity="Time O(n) for the duplicate-title scan over n existing recipes (a database would use a unique index), O(1) for the other checks. Space O(n) for the new list.",
        pitfalls="- `True` passes `isinstance(x, int)`.\n- Comparing the untrimmed title for uniqueness, or forgetting to ignore case.\n- `servings or 4` turns an invalid `0` into a valid 4.\n- Mutating `state` in place: a failed validation later in the function would leave half-applied changes behind.",
        follow_up="Add an `updateRecipe(id, input)` mutation where every input field is optional, and decide how 'field not sent' differs from 'field sent as null'.",
    ),
),
]
