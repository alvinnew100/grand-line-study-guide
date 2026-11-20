"""Java track, model problems part 3: strings, HashMap, sorting, wildcards, resources, exceptions, streams, Optional, builders."""


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls, follow_up=None):
    d = dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute, approach=approach,
             complexity=complexity, pitfalls=pitfalls)
    if follow_up:
        d["follow_up"] = follow_up
    return d


PROBLEMS = [
# ------------------------------------------------------------------ java-string-pool
dict(
    id="java-string-pool",
    title="String pool: == versus equals",
    difficulty="Medium",
    pattern="Java strings",
    entry="string_identity",
    description=r"""
Model which `String` variables refer to the **same object**.

`decls` is a list of declarations, in order. Each creates a variable:

| declaration | Java | object |
|---|---|---|
| `[name, "lit", text]` | `String name = "text";` | the pooled string with that text |
| `[name, "new", text]` | `String name = new String("text");` | a brand-new object |
| `[name, "const", t1, t2]` | `String name = "t1" + "t2";` | a compile-time constant: the **pooled** string `t1 + t2` |
| `[name, "concat", var, text]` | `String name = var + "text";` | computed at run time: a **new** object |
| `[name, "intern", var]` | `String name = var.intern();` | the pooled string with `var`'s text |
| `[name, "alias", var]` | `String name = var;` | the same object as `var` |

The pool holds exactly one object per distinct text. `intern` adds the text to the pool if it is not there
yet (as a separate pooled object).

`queries` is a list of `["==", a, b]` or `["equals", a, b]`. Return a list of booleans: `==` is true when
both variables refer to the same object; `equals` when the texts are the same.

**Example** `decls = [["a","lit","java"], ["b","new","java"], ["c","intern","b"], ["p","lit","ja"], ["d","concat","p","va"], ["e","const","ja","va"]]`,
`queries = [["==","a","b"], ["==","a","c"], ["==","a","d"], ["==","a","e"], ["equals","a","d"]]` → `[False, True, False, True, True]`
""",
    starter='''def string_identity(decls, queries):
    pass
''',
    solution='''def string_identity(decls, queries):
    pool = {}
    text = {}
    ident = {}
    counter = [0]

    def pooled(t):
        if t not in pool:
            pool[t] = ("pool", t)
        return pool[t]

    def fresh():
        counter[0] += 1
        return ("heap", counter[0])

    for d in decls:
        name, kind = d[0], d[1]
        if kind == "lit":
            text[name], ident[name] = d[2], pooled(d[2])
        elif kind == "new":
            pooled(d[2])
            text[name], ident[name] = d[2], fresh()
        elif kind == "const":
            t = d[2] + d[3]
            text[name], ident[name] = t, pooled(t)
        elif kind == "concat":
            t = text[d[2]] + d[3]
            text[name], ident[name] = t, fresh()
        elif kind == "intern":
            t = text[d[2]]
            text[name], ident[name] = t, pooled(t)
        else:
            text[name], ident[name] = text[d[2]], ident[d[2]]
    out = []
    for op, a, b in queries:
        out.append(ident[a] == ident[b] if op == "==" else text[a] == text[b])
    return out
''',
    tests=[
        [[["a", "lit", "java"], ["b", "new", "java"], ["c", "intern", "b"], ["p", "lit", "ja"], ["d", "concat", "p", "va"], ["e", "const", "ja", "va"]],
         [["==", "a", "b"], ["==", "a", "c"], ["==", "a", "d"], ["==", "a", "e"], ["equals", "a", "d"]]],
        [[["a", "lit", "x"], ["b", "lit", "x"]], [["==", "a", "b"], ["equals", "a", "b"]]],
        [[["a", "new", "x"], ["b", "new", "x"]], [["==", "a", "b"], ["equals", "a", "b"], ["==", "a", "a"]]],
        [[["a", "new", "x"], ["b", "alias", "a"], ["c", "intern", "a"]], [["==", "a", "b"], ["==", "a", "c"], ["==", "b", "c"]]],
        [[["a", "lit", "ab"], ["b", "lit", "a"], ["c", "concat", "b", "b"], ["d", "intern", "c"]], [["==", "a", "c"], ["==", "a", "d"], ["equals", "a", "c"]]],
        [[["p", "lit", "a"], ["q", "concat", "p", "b"], ["r", "intern", "q"], ["s", "lit", "ab"]], [["==", "q", "r"], ["==", "r", "s"], ["==", "q", "s"]]],
        [[["a", "lit", "hello"], ["b", "lit", "Hello"]], [["==", "a", "b"], ["equals", "a", "b"]]],
        [[["a", "const", "", "x"], ["b", "lit", "x"], ["c", "concat", "b", ""]], [["==", "a", "b"], ["==", "b", "c"], ["equals", "b", "c"]]],
        [[], []],
        [[["a", "lit", "k"], ["b", "concat", "a", ""], ["c", "concat", "a", ""], ["d", "alias", "c"]], [["==", "b", "c"], ["==", "c", "d"], ["equals", "b", "d"]]],
        [[["a", "new", "z"], ["b", "intern", "a"], ["c", "lit", "z"], ["d", "new", "z"], ["e", "intern", "d"]], [["==", "b", "c"], ["==", "b", "e"], ["==", "a", "d"]]],
    ],
    wrong_solutions=[
        '''def string_identity(decls, queries):
    text = {}
    for d in decls:
        name, kind = d[0], d[1]
        if kind in ("lit", "new"): text[name] = d[2]
        elif kind == "const": text[name] = d[2] + d[3]
        elif kind == "concat": text[name] = text[d[2]] + d[3]
        else: text[name] = text[d[2]]
    return [text[a] == text[b] for _, a, b in queries]
''',
        '''def string_identity(decls, queries):
    text, pooled = {}, {}
    for d in decls:
        name, kind = d[0], d[1]
        if kind == "lit": text[name], pooled[name] = d[2], True
        elif kind == "new": text[name], pooled[name] = d[2], False
        elif kind == "const": text[name], pooled[name] = d[2] + d[3], True
        elif kind == "concat": text[name], pooled[name] = text[d[2]] + d[3], False
        elif kind == "intern": text[name], pooled[name] = text[d[2]], True
        else: text[name], pooled[name] = text[d[2]], pooled[d[2]]
    out = []
    for op, a, b in queries:
        if op == "==": out.append(text[a] == text[b] and pooled[a] and pooled[b])
        else: out.append(text[a] == text[b])
    return out
''',
    ],
    guide=G(
        "Lesson *Strings, equals/hashCode, HashMap and ConcurrentHashMap internals*: the string pool.",
        "Every variable has a text **and** an identity. The pool hands out one identity per text; `new` and "
        "run-time concatenation mint fresh identities; an alias copies an identity.",
        ["Keep a dictionary from text to the pooled identity.", "Literals, constant expressions and `intern()` use the pool.",
         "`==` compares identities; a variable is always `==` to itself and to its aliases, pooled or not."],
        "Tracking only 'is this variable pooled?' fails for aliases: two aliases of one `new String` are the "
        "same object even though neither is pooled.",
        r"""**Dry run** of the example. `a` → pool["java"]. `b` → heap #1. `c = b.intern()` → pool["java"], the
object `a` refers to. `p` → pool["ja"]. `d = p + "va"` → heap #2 with text "java". `e = "ja" + "va"` is
folded by the compiler → pool["java"]. So `a == b` False, `a == c` True, `a == d` False, `a == e` True,
`a.equals(d)` True.

```java
String a = "java";
String b = new String("java");
String c = b.intern();
String p = "ja";
String d = p + "va";             // run-time concatenation: new object
String e = "ja" + "va";          // compile-time constant: pooled
System.out.println((a == b) + " " + (a == c) + " " + (a == d) + " " + (a == e) + " " + a.equals(d));
// false true false true true
```""",
        "Time O(declarations + queries), space O(distinct texts + objects).",
        "- Treating run-time concatenation as pooled.\n- Forgetting that `intern()` returns the pooled object, not the receiver.\n"
        "- Returning False for `x == x` when `x` is a heap string.",
        "If `p` were declared `final`, `p + \"va\"` would become a constant expression and `d` would be pooled.",
    ),
),
# ------------------------------------------------------------------ java-hashmap-sim
dict(
    id="java-hashmap-sim",
    title="Simulate HashMap: buckets, load factor and resize",
    difficulty="Hard",
    pattern="Java collections",
    entry="hashmap_sim",
    description=r"""
Simulate `java.util.HashMap<Integer, Integer>` with linked-list buckets (no tree bins).

Write `hashmap_sim(capacity, load_factor, ops)`.

- The table starts with `capacity` buckets (a power of two). Keys are Java `int` values; an `Integer`'s
  `hashCode` is the number itself.
- **Spread**: treat the key as an unsigned 32-bit pattern `h` (for a negative key use `key + 2**32`), then
  `hash = h ^ (h >>> 16)` (unsigned shift).
- **Index**: `hash & (n - 1)` where `n` is the current number of buckets.
- `["put", k, v]`: if the bucket already holds key `k`, replace its value. Otherwise append a new entry at the
  **end** of the bucket and increase the size. Then, if `size > n * load_factor`, **resize**.
- **Resize**: double `n`. Each old bucket `i` is split, keeping the entries' relative order: an entry stays at
  index `i` if `hash & old_n` is 0 and otherwise moves to index `i + old_n`.
- `["get", k]`: append the value to the results, or `None` if absent.
- `["remove", k]`: remove the entry if present (size decreases; the table never shrinks). Appends nothing.

Return `[results, table]` where `table` is the final list of buckets, each a list of keys in bucket order.

**Example** `hashmap_sim(4, 0.75, [["put",1,10],["put",5,50],["put",9,90],["put",2,20],["get",5],["get",3]])`
→ `[[50, None], [[], [1, 9], [2], [], [], [5], [], []]]`
""",
    starter='''def hashmap_sim(capacity, load_factor, ops):
    pass
''',
    solution='''def hashmap_sim(capacity, load_factor, ops):
    def spread(k):
        h = k & 0xFFFFFFFF
        return h ^ (h >> 16)

    table = [[] for _ in range(capacity)]
    size = 0
    results = []
    for op in ops:
        k = op[1]
        h = spread(k)
        bucket = table[h & (len(table) - 1)]
        if op[0] == "put":
            for e in bucket:
                if e[0] == k:
                    e[1] = op[2]
                    break
            else:
                bucket.append([k, op[2]])
                size += 1
                if size > len(table) * load_factor:
                    old_n = len(table)
                    new_table = [[] for _ in range(2 * old_n)]
                    for i, b in enumerate(table):
                        for e in b:
                            new_table[i + old_n if spread(e[0]) & old_n else i].append(e)
                    table = new_table
        elif op[0] == "get":
            for e in bucket:
                if e[0] == k:
                    results.append(e[1])
                    break
            else:
                results.append(None)
        else:
            for idx, e in enumerate(bucket):
                if e[0] == k:
                    del bucket[idx]
                    size -= 1
                    break
    return [results, [[e[0] for e in b] for b in table]]
''',
    tests=[
        [4, 0.75, [["put", 1, 10], ["put", 5, 50], ["put", 9, 90], ["put", 2, 20], ["get", 5], ["get", 3]]],
        [4, 0.75, [["put", 1, 10], ["put", 5, 50], ["put", 9, 90]]],
        [4, 0.75, [["put", 1, 10], ["put", 1, 11], ["put", 1, 12], ["get", 1]]],
        [2, 0.75, []],
        [2, 0.75, [["get", 0]]],
        [2, 1.0, [["put", 0, 0], ["put", 2, 2], ["put", 4, 4], ["put", 6, 6], ["put", 8, 8]]],
        [4, 0.75, [["put", -1, 1], ["put", -2, 2], ["get", -1], ["get", -3]]],
        [4, 0.75, [["put", 65536, 1], ["put", 131072, 2], ["put", 0, 3], ["get", 65536], ["get", 131072]]],
        [4, 0.75, [["put", 1, 1], ["put", 5, 5], ["remove", 1], ["put", 9, 9], ["put", 13, 13], ["get", 1], ["get", 13]]],
        [16, 0.75, [["put", i, i * i] for i in range(13)] + [["get", 12], ["get", 13]]],
        [16, 0.75, [["put", i * 16, i] for i in range(12)] + [["remove", 32], ["remove", 999], ["get", 48]]],
        [4, 0.5, [["put", 3, 1], ["put", 7, 2], ["put", 11, 3], ["put", 15, 4], ["put", 19, 5], ["get", 19]]],
        [8, 0.75, [["put", (i * 2654435761) % 4294967296 - 2147483648, i] for i in range(40)] + [["get", 0]]],
    ],
    wrong_solutions=[
        '''def hashmap_sim(capacity, load_factor, ops):
    table = [[] for _ in range(capacity)]
    size, results = 0, []
    for op in ops:
        k = op[1]
        bucket = table[k % len(table)]
        if op[0] == "put":
            for e in bucket:
                if e[0] == k:
                    e[1] = op[2]; break
            else:
                bucket.append([k, op[2]]); size += 1
                if size > len(table) * load_factor:
                    entries = [e for b in table for e in b]
                    table = [[] for _ in range(2 * len(table))]
                    for e in entries:
                        table[e[0] % len(table)].append(e)
        elif op[0] == "get":
            for e in bucket:
                if e[0] == k:
                    results.append(e[1]); break
            else:
                results.append(None)
        else:
            for idx, e in enumerate(bucket):
                if e[0] == k:
                    del bucket[idx]; size -= 1; break
    return [results, [[e[0] for e in b] for b in table]]
''',
        '''def hashmap_sim(capacity, load_factor, ops):
    def spread(k):
        h = k & 0xFFFFFFFF
        return h ^ (h >> 16)
    table = [[] for _ in range(capacity)]
    size, results = 0, []
    for op in ops:
        k = op[1]
        bucket = table[spread(k) & (len(table) - 1)]
        if op[0] == "put":
            for e in bucket:
                if e[0] == k:
                    e[1] = op[2]; break
            else:
                bucket.append([k, op[2]]); size += 1
                if size >= len(table) * load_factor:
                    old_n = len(table)
                    nt = [[] for _ in range(2 * old_n)]
                    for i, b in enumerate(table):
                        for e in b:
                            nt[i + old_n if spread(e[0]) & old_n else i].append(e)
                    table = nt
        elif op[0] == "get":
            for e in bucket:
                if e[0] == k:
                    results.append(e[1]); break
            else:
                results.append(None)
        else:
            for idx, e in enumerate(bucket):
                if e[0] == k:
                    del bucket[idx]; size -= 1; break
    return [results, [[e[0] for e in b] for b in table]]
''',
    ],
    guide=G(
        "Lessons *Collections: List, Set, Map and Queue* and *Strings, equals/hashCode, HashMap and ConcurrentHashMap internals*.",
        "A hash map is an array of small lists. The key's hash picks the list; within the list you compare keys. "
        "Growing doubles the array, and because the length is a power of two each entry either stays put or moves "
        "up by exactly the old length.",
        ["Write `spread(k)` first: mask to 32 bits, then XOR with itself shifted right by 16.",
         "For `put`, search the bucket; replace, or append and bump the size, then test `size > n * load_factor`.",
         "On resize, walk old buckets in order and append each entry to bucket `i` or `i + old_n` depending on `hash & old_n`."],
        "Rehashing every entry from scratch with `hash & (new_n - 1)` gives the same buckets. The split form shows "
        "why a resize is cheap and order-preserving. An unordered rebuild (collect all, re-insert) also happens to "
        "preserve order here because old buckets are visited in index order.",
        r"""**Dry run** of the example, capacity 4, threshold 3. `put 1` → bucket 1. `put 5` → 5 & 3 = 1 → bucket
1: `[1, 5]`. `put 9` → bucket 1: `[1, 5, 9]`, size 3, not > 3. `put 2` → bucket 2, size 4 > 3 → resize to 8.
Bucket 1 splits on `hash & 4`: 1 → 0 stays, 5 → 4 moves to 5, 9 → 0 stays. Bucket 2: 2 stays.
Table `[[], [1, 9], [2], [], [], [5], [], []]`. `get 5` → 50; `get 3` → None.

```java
Map<Integer, Integer> m = new HashMap<>(4, 0.75f);
m.put(1, 10);  m.put(5, 50);  m.put(9, 90);
m.put(2, 20);                                   // 4th entry exceeds 4 * 0.75: table doubles to 8
System.out.println(m.get(5) + " " + m.get(3));  // 50 null

// the real index computation inside HashMap:
static int index(Object key, int n) {
    int h = key.hashCode();
    return (h ^ (h >>> 16)) & (n - 1);
}
```""",
        "Average O(1) per operation; a resize costs O(size) but happens only when the size doubles, so the "
        "amortised cost stays constant. Space O(size + buckets).",
        "- Using `%`, which differs for negative keys and skips the spreading step.\n"
        "- Resizing at `size >= threshold` instead of `>`.\n- Resizing on a `put` that only replaced a value.\n"
        "- Forgetting to mask negative keys to 32 bits before shifting.",
        "Real `HashMap` converts a bucket to a red-black tree once it holds 8 entries and the table has at least 64 buckets.",
    ),
),
# ------------------------------------------------------------------ java-multikey-sort
dict(
    id="java-multikey-sort",
    title="Multi-key sort with a Comparator",
    difficulty="Easy",
    pattern="Java collections",
    entry="sort_staff",
    description=r"""
Sort employee rows the way this Java comparator would:

```java
Comparator.comparing(Employee::dept)
          .thenComparing(Employee::salary, Comparator.reverseOrder())
          .thenComparing(Employee::name)
```

Each row is `[dept, name, salary]` (two strings and an integer). Return a **new** list sorted by:

1. `dept` ascending;
2. then `salary` **descending**;
3. then `name` ascending.

Strings compare as Java's `String.compareTo` does for plain ASCII text: by character code, so every capital
letter sorts before every lower-case letter (Python's string comparison agrees). Do not modify the input.

**Example** `sort_staff([["ops","Bo",30],["dev","Ada",50],["dev","Cy",70],["dev","Al",50]])`
→ `[["dev","Cy",70],["dev","Ada",50],["dev","Al",50],["ops","Bo",30]]`
""",
    starter='''def sort_staff(rows):
    pass
''',
    solution='''def sort_staff(rows):
    return sorted(rows, key=lambda r: (r[0], -r[2], r[1]))
''',
    tests=[
        [[["ops", "Bo", 30], ["dev", "Ada", 50], ["dev", "Cy", 70], ["dev", "Al", 50]]],
        [[]],
        [[["x", "solo", 1]]],
        [[["a", "z", 5], ["a", "y", 5], ["a", "x", 5]]],
        [[["b", "n", 1], ["a", "n", 1], ["c", "n", 1]]],
        [[["a", "n", 1], ["a", "n", 3], ["a", "n", 2]]],
        [[["dev", "bo", 10], ["Dev", "ada", 10], ["dev", "Bo", 10]]],
        [[["a", "p", -5], ["a", "q", 0], ["a", "r", -10]]],
        [[["hr", "Zed", 40], ["hr", "amy", 40], ["hr", "Amy", 40], ["dev", "Zed", 40]]],
        [[["d%d" % (i % 3), "n%02d" % (i * 7 % 20), (i * 13) % 5] for i in range(20)]],
        [[["a", "x", 1], ["a", "x", 1]]],
    ],
    wrong_solutions=[
        '''def sort_staff(rows):
    return sorted(rows, key=lambda r: (r[0], r[2], r[1]))
''',
        '''def sort_staff(rows):
    return sorted(rows, key=lambda r: (r[0], r[1], -r[2]))
''',
        '''def sort_staff(rows):
    return sorted(rows, reverse=True, key=lambda r: (r[0], r[2], r[1]))
''',
    ],
    guide=G(
        "Lesson *Sorting with Comparable and Comparator*: `thenComparing` and reversing one key.",
        "A multi-key comparison looks at the second key only when the first is a tie. In Python that is a tuple "
        "key; a descending numeric key is its negation.",
        ["Build a key tuple in order of importance.", "Negate the salary to reverse only that key.",
         "`sorted` returns a new list and leaves the input alone."],
        "Sort three times with a stable sort, least important key first: by name, then by salary descending, "
        "then by department. It gives the same result and costs three passes.",
        r"""**Dry run** of the example. Keys: `("ops", -30, "Bo")`, `("dev", -50, "Ada")`, `("dev", -70, "Cy")`,
`("dev", -50, "Al")`. Sorted: `("dev", -70, "Cy")`, `("dev", -50, "Ada")`, `("dev", -50, "Al")`,
`("ops", -30, "Bo")`. "Ada" precedes "Al" because `d` < `l`.

```java
record Employee(String dept, String name, int salary) { }

static List<Employee> sortStaff(List<Employee> staff) {
    List<Employee> copy = new ArrayList<>(staff);
    copy.sort(Comparator.comparing(Employee::dept)
            .thenComparing(Employee::salary, Comparator.reverseOrder())
            .thenComparing(Employee::name));
    return copy;
}
// Do not write .thenComparing(Employee::salary).reversed(): reversed() flips the WHOLE chain so far.
```""",
        "Time O(n log n), space O(n) for the copy.",
        "- Sorting the salary ascending.\n- Putting the keys in the wrong order.\n- Reversing the whole sort instead of one key.\n"
        "- Sorting in place when a new list was asked for.",
    ),
),
# ------------------------------------------------------------------ java-wildcard-assignable
dict(
    id="java-wildcard-assignable",
    title="Wildcards and PECS",
    difficulty="Medium",
    pattern="Java generics",
    entry="wildcard",
    description=r"""
Answer three questions about a parameter of type `List<...>` with a wildcard.

`parents` maps each class to its superclass (`None` for `Object`). A type is a subtype of itself and of all
its ancestors.

`param` is `[kind, T]` describing the parameter's type argument:

| `kind` | Java |
|---|---|
| `"exact"` | `List<T>` |
| `"extends"` | `List<? extends T>` |
| `"super"` | `List<? super T>` |
| `"any"` | `List<?>` (T is ignored; it will be `"Object"`) |

Write `wildcard(parents, param, arg, element)` returning `[assignable, can_add, read_type]`:

1. `assignable`: may a `List<arg>` be passed for this parameter?
   exact: `arg == T`; extends: `arg` is a subtype of `T`; super: `T` is a subtype of `arg`; any: always.
2. `can_add`: inside the method, does `list.add(x)` compile for an `x` of static type `element`?
   exact and super: `element` is a subtype of `T`; extends and any: never.
3. `read_type`: the static type of `list.get(0)`: exact and extends: `T`; super and any: `"Object"`.

**Example** with `Integer → Number → Object`:
`wildcard(p, ["extends", "Number"], "Integer", "Integer")` → `[True, False, "Number"]`;
`wildcard(p, ["super", "Integer"], "Number", "Integer")` → `[True, True, "Object"]`.
""",
    starter='''def wildcard(parents, param, arg, element):
    pass
''',
    solution='''def wildcard(parents, param, arg, element):
    def sub(a, b):
        while a is not None:
            if a == b:
                return True
            a = parents[a]
        return False

    kind, t = param
    if kind == "exact":
        return [arg == t, sub(element, t), t]
    if kind == "extends":
        return [sub(arg, t), False, t]
    if kind == "super":
        return [sub(t, arg), sub(element, t), "Object"]
    return [True, False, "Object"]
''',
    tests=[
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["extends", "Number"], "Integer", "Integer"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["super", "Integer"], "Number", "Integer"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["exact", "Number"], "Integer", "Integer"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["exact", "Number"], "Number", "Double"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["extends", "Number"], "String", "Number"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["super", "Integer"], "Double", "Integer"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["super", "Integer"], "Object", "Number"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["any", "Object"], "String", "String"],
        [{"Object": None, "Number": "Object", "Integer": "Number", "Double": "Number", "String": "Object"}, ["exact", "Object"], "Object", "String"],
        [{"Object": None, "Animal": "Object", "Dog": "Animal", "Puppy": "Dog", "Cat": "Animal"}, ["super", "Dog"], "Animal", "Puppy"],
        [{"Object": None, "Animal": "Object", "Dog": "Animal", "Puppy": "Dog", "Cat": "Animal"}, ["super", "Dog"], "Puppy", "Dog"],
        [{"Object": None, "Animal": "Object", "Dog": "Animal", "Puppy": "Dog", "Cat": "Animal"}, ["extends", "Animal"], "Puppy", "Animal"],
        [{"Object": None, "Animal": "Object", "Dog": "Animal", "Puppy": "Dog", "Cat": "Animal"}, ["super", "Dog"], "Dog", "Animal"],
        [{"Object": None, "Animal": "Object", "Dog": "Animal", "Puppy": "Dog", "Cat": "Animal"}, ["extends", "Dog"], "Dog", "Cat"],
    ],
    wrong_solutions=[
        '''def wildcard(parents, param, arg, element):
    def sub(a, b):
        while a is not None:
            if a == b: return True
            a = parents[a]
        return False
    kind, t = param
    if kind == "exact": return [sub(arg, t), sub(element, t), t]
    if kind == "extends": return [sub(arg, t), False, t]
    if kind == "super": return [sub(t, arg), sub(element, t), "Object"]
    return [True, False, "Object"]
''',
        '''def wildcard(parents, param, arg, element):
    def sub(a, b):
        while a is not None:
            if a == b: return True
            a = parents[a]
        return False
    kind, t = param
    if kind == "exact": return [arg == t, sub(element, t), t]
    if kind == "extends": return [sub(arg, t), sub(element, t), t]
    if kind == "super": return [sub(arg, t), sub(element, t), t]
    return [True, False, "Object"]
''',
    ],
    guide=G(
        "Lessons *Generics, wildcards and bounds* and *Bounded wildcards, PECS, varargs and heterogeneous containers*.",
        "The wildcard says what the compiler knows about the list's element type. `? extends T`: 'some subtype of "
        "T', so reading gives a T and adding is forbidden. `? super T`: 'some supertype of T', so adding a T is safe "
        "and reading gives only Object.",
        ["Write `sub(a, b)`: climb from `a` through `parents` looking for `b`.",
         "Generics are invariant: for `exact`, only the identical type argument is accepted.",
         "For `super`, the subtype test is reversed: `T` must be a subtype of `arg`."],
        "There is no cheaper approach; the difficulty is keeping the directions straight. PECS: producer extends, consumer super.",
        r"""**Dry run** `param = ["super", "Dog"]`, `arg = "Animal"`, `element = "Puppy"`. Is `List<Animal>`
acceptable for `List<? super Dog>`? `Dog` is a subtype of `Animal` → yes. Can a `Puppy` be added? The unknown
element type is at least `Dog`, and a `Puppy` is a `Dog` → yes. Reading gives `Object`. → `[True, True, "Object"]`.

```java
static double sum(List<? extends Number> src) {          // producer: read as Number, cannot add
    double s = 0;
    for (Number n : src) s += n.doubleValue();
    return s;
}

static void fill(List<? super Integer> dst) {            // consumer: can add Integer, reads give Object
    dst.add(1);
    Object first = dst.get(0);
}

sum(List.of(1, 2));                    // List<Integer> is a List<? extends Number>
fill(new ArrayList<Number>());         // List<Number> is a List<? super Integer>
// List<Number> bad = new ArrayList<Integer>();   // does not compile: invariance
```""",
        "Time O(depth of the hierarchy), space O(1).",
        "- Treating `List<Integer>` as a `List<Number>`.\n- Allowing `add` through `? extends`.\n"
        "- Reversing the test for `? super`, or returning `T` as its read type.",
    ),
),
# ------------------------------------------------------------------ java-twr-close-order
dict(
    id="java-twr-close-order",
    title="try-with-resources: close order and suppressed exceptions",
    difficulty="Medium",
    pattern="Java exceptions",
    entry="try_with_resources",
    description=r"""
Simulate one try-with-resources statement.

`resources` is a list, in declaration order, of `[name, open_fails, close_fails]` (two booleans).
`body_throws` says whether the body throws.

**Rules**

1. Open the resources in order. Log `"open <name>"`. If an open fails, log `"open <name> FAILS"` instead:
   that resource and all later ones are **not** opened, the body does **not** run, and the **primary**
   exception is `"open <name>"`.
2. If every resource opened, log `"body"`. If `body_throws`, the primary exception is `"body"`.
3. Close every resource that was successfully opened, in **reverse** order, logging `"close <name>"`.
   If a close fails: when there is no primary exception yet it becomes the primary, `"close <name>"`;
   otherwise it is added to the **suppressed** list, in the order the closes happened.

Return `[log, primary, suppressed]` with `primary` equal to `None` if nothing was thrown.

**Example** `try_with_resources([["A", False, True], ["B", False, True]], True)`
→ `[["open A", "open B", "body", "close B", "close A"], "body", ["close B", "close A"]]`
""",
    starter='''def try_with_resources(resources, body_throws):
    pass
''',
    solution='''def try_with_resources(resources, body_throws):
    log, opened = [], []
    primary, suppressed = None, []
    for name, open_fails, close_fails in resources:
        if open_fails:
            log.append("open " + name + " FAILS")
            primary = "open " + name
            break
        log.append("open " + name)
        opened.append((name, close_fails))
    else:
        log.append("body")
        if body_throws:
            primary = "body"
    for name, close_fails in reversed(opened):
        log.append("close " + name)
        if close_fails:
            if primary is None:
                primary = "close " + name
            else:
                suppressed.append("close " + name)
    return [log, primary, suppressed]
''',
    tests=[
        [[["A", False, True], ["B", False, True]], True],
        [[["A", False, False], ["B", False, False]], False],
        [[["A", False, False], ["B", True, False], ["C", False, False]], False],
        [[["A", False, True], ["B", False, False]], False],
        [[["A", False, True], ["B", False, True]], False],
        [[], False],
        [[], True],
        [[["A", True, True]], True],
        [[["A", False, True], ["B", True, True], ["C", False, True]], True],
        [[["A", False, False], ["B", False, False], ["C", False, False]], True],
        [[["X", False, True]], True],
        [[["A", False, True], ["B", False, True], ["C", True, False]], False],
    ],
    wrong_solutions=[
        '''def try_with_resources(resources, body_throws):
    log, opened, primary, suppressed = [], [], None, []
    for name, open_fails, close_fails in resources:
        if open_fails:
            log.append("open " + name + " FAILS"); primary = "open " + name; break
        log.append("open " + name); opened.append((name, close_fails))
    else:
        log.append("body")
        if body_throws: primary = "body"
    for name, close_fails in opened:
        log.append("close " + name)
        if close_fails:
            if primary is None: primary = "close " + name
            else: suppressed.append("close " + name)
    return [log, primary, suppressed]
''',
        '''def try_with_resources(resources, body_throws):
    log, opened, primary, suppressed = [], [], None, []
    for name, open_fails, close_fails in resources:
        if open_fails:
            log.append("open " + name + " FAILS"); primary = "open " + name; break
        log.append("open " + name); opened.append((name, close_fails))
    else:
        log.append("body")
        if body_throws: primary = "body"
    for name, close_fails in reversed(opened):
        log.append("close " + name)
        if close_fails:
            primary = "close " + name
    return [log, primary, suppressed]
''',
    ],
    guide=G(
        "Lesson *try-with-resources, multi-catch and custom exceptions*.",
        "Resources are a stack: opened in order, closed in reverse. The first exception thrown is the one the "
        "caller sees; later ones from `close` ride along as suppressed.",
        ["Remember which resources were opened successfully.", "The body runs only if the opening loop finished without a failure.",
         "Close in reverse; a failing close becomes primary only if nothing has been thrown yet."],
        "A hand-written `try`/`finally` with nested blocks does the closing but lets a failure in `close` replace "
        "the original exception. Try-with-resources was introduced to fix exactly that.",
        r"""**Dry run** `[A ok/close ok, B open FAILS, C]`, body does not throw. Open A. Open B fails: primary
`"open B"`; C is never opened; no body. Close A. Result
`[["open A", "open B FAILS", "close A"], "open B", []]`. A is still closed although the statement failed
while opening B.

```java
class Res implements AutoCloseable {
    private final String name;
    Res(String name) { this.name = name; System.out.println("open " + name); }
    @Override public void close() { System.out.println("close " + name); throw new IllegalStateException("close " + name); }
}

try (Res a = new Res("A"); Res b = new Res("B")) {
    throw new IllegalArgumentException("body");
} catch (Exception e) {
    System.out.println(e.getMessage());                     // body
    for (Throwable s : e.getSuppressed()) {
        System.out.println("suppressed: " + s.getMessage());   // close B, then close A
    }
}
```""",
        "Time O(number of resources), space O(number of resources).",
        "- Closing in declaration order.\n- Closing resources that were never opened.\n"
        "- Letting a close failure replace the body's exception.\n- Running the body after a failed open.",
    ),
),
# ------------------------------------------------------------------ java-checked-analyser
dict(
    id="java-checked-analyser",
    title="Checked exceptions: must declare or catch",
    difficulty="Medium",
    pattern="Java exceptions",
    entry="unreported",
    description=r"""
The compiler rejects a method whose body can throw a **checked** exception that is neither caught nor
declared. Write the check.

`parents` maps each exception type to its superclass; `"Throwable"` maps to `None`. It always contains
`Throwable`, `Exception`, `RuntimeException` and `Error`.

An exception type is **unchecked** if it is `RuntimeException`, `Error`, or a subtype of either. Every other
type (including `Exception` and `Throwable` themselves) is **checked**.

Write `unreported(parents, thrown, caught, declared)`:

- `thrown`: types the body may throw;
- `caught`: types named in `catch` blocks around that code;
- `declared`: types in the method's `throws` clause.

A thrown type is **handled** if it is a subtype of (or equal to) some caught type or some declared type.
Return the **sorted** list (without duplicates) of thrown **checked** types that are not handled. An empty
list means the method compiles.

**Example** with `FileNotFoundException → IOException → Exception`:
`unreported(p, ["FileNotFoundException", "SQLException"], ["IOException"], [])` → `["SQLException"]`
""",
    starter='''def unreported(parents, thrown, caught, declared):
    pass
''',
    solution='''def unreported(parents, thrown, caught, declared):
    def is_a(t, anc):
        while t is not None:
            if t == anc:
                return True
            t = parents[t]
        return False

    out = set()
    for t in thrown:
        if is_a(t, "RuntimeException") or is_a(t, "Error"):
            continue
        if any(is_a(t, h) for h in caught) or any(is_a(t, h) for h in declared):
            continue
        out.add(t)
    return sorted(out)
''',
    tests=[
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["FileNotFoundException", "SQLException"], ["IOException"], []],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["FileNotFoundException"], [], []],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["NullPointerException", "OutOfMemoryError", "RuntimeException", "Error"], [], []],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["IOException"], ["FileNotFoundException"], []],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["IOException", "SQLException"], [], ["Exception"]],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["Exception"], ["RuntimeException"], []],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["Throwable"], ["Exception"], ["Error"]],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         [], [], []],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["SQLException", "IOException", "SQLException", "FileNotFoundException"], [], ["FileNotFoundException"]],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception", "IOException": "Exception",
          "FileNotFoundException": "IOException", "SQLException": "Exception", "NullPointerException": "RuntimeException", "OutOfMemoryError": "Error"},
         ["FileNotFoundException", "SQLException"], ["SQLException"], ["IOException"]],
        [{"Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception",
          "AppException": "Exception", "PaymentException": "AppException", "BugException": "RuntimeException"},
         ["PaymentException", "BugException", "AppException"], ["PaymentException"], []],
    ],
    wrong_solutions=[
        '''def unreported(parents, thrown, caught, declared):
    handled = set(caught) | set(declared)
    unchecked = {"RuntimeException", "Error"}
    return sorted({t for t in thrown if t not in handled and t not in unchecked})
''',
        '''def unreported(parents, thrown, caught, declared):
    def is_a(t, anc):
        while t is not None:
            if t == anc: return True
            t = parents[t]
        return False
    out = set()
    for t in thrown:
        if is_a(t, "RuntimeException"):
            continue
        if any(is_a(h, t) for h in caught) or any(is_a(h, t) for h in declared):
            continue
        out.add(t)
    return sorted(out)
''',
    ],
    guide=G(
        "Lessons *Exceptions: try, catch, finally, checked and unchecked* and *Choosing exceptions*.",
        "Two filters. First drop everything unchecked. Then, for each remaining type, ask whether some catch or "
        "throws entry is the same type **or an ancestor**.",
        ["Write `is_a(t, ancestor)` by climbing the `parents` map.", "Unchecked means `is_a(t, \"RuntimeException\")` or `is_a(t, \"Error\")`.",
         "A handler covers its subtypes, not its supertypes: `catch (FileNotFoundException e)` does not handle an `IOException`."],
        "Comparing names for equality ignores the hierarchy both for 'is it unchecked?' and for 'is it handled?'.",
        r"""**Dry run** thrown `[IOException]`, caught `[FileNotFoundException]`. `IOException` is checked. Is it a
subtype of `FileNotFoundException`? No: the relation runs the other way. Not declared → `["IOException"]`.

```java
// does not compile: unreported exception java.sql.SQLException; must be caught or declared to be thrown
static void load(String path) {
    try {
        new java.io.FileReader(path).close();        // FileNotFoundException, IOException
        java.sql.DriverManager.getConnection("x");   // SQLException
    } catch (java.io.IOException e) {                // covers FileNotFoundException too
        throw new java.io.UncheckedIOException(e);
    }
}

// fixed: declare it (or catch it)
static void load2(String path) throws java.sql.SQLException { /* same body */ }
```""",
        "Time O(thrown × (caught + declared) × depth), space O(thrown).",
        "- Treating `Exception` itself as unchecked.\n- Thinking a subclass handler covers its superclass.\n"
        "- Forgetting that `Error` and its subclasses are unchecked.\n- Returning duplicates.",
    ),
),
# ------------------------------------------------------------------ java-stream-pipeline
dict(
    id="java-stream-pipeline",
    title="Evaluate a stream pipeline",
    difficulty="Medium",
    pattern="Java streams",
    entry="run_pipeline",
    description=r"""
Evaluate a Java stream pipeline over a list of integers.

`run_pipeline(data, ops)`: `data` is a list of ints; `ops` is a list of intermediate operations followed by
exactly one terminal operation.

**Intermediate operations**

| op | Java | meaning |
|---|---|---|
| `["filter", "even"]` / `"odd"` / `"positive"` | `.filter(...)` | keep matching elements (positive means `> 0`) |
| `["filter", ["gt", k]]` | `.filter(x -> x > k)` | |
| `["map", ["mul", k]]`, `["map", ["add", k]]`, `["map", "square"]`, `["map", "abs"]` | `.map(...)` | transform each element |
| `["flatMap", "digits"]` | `.flatMap(...)` | replace each element by the decimal digits of its absolute value, most significant first (0 gives `[0]`) |
| `["distinct"]` | `.distinct()` | keep the first occurrence of each value |
| `["sorted"]` | `.sorted()` | ascending |
| `["limit", n]`, `["skip", n]` | `.limit(n)`, `.skip(n)` | |

**Terminal operations**

| op | result |
|---|---|
| `["toList"]` | the list |
| `["count"]` | the number of elements |
| `["sum"]` | `reduce(0, Integer::sum)` |
| `["groupingByCount", "parity"]` | a dict `{"even": n, "odd": m}` containing only the keys that occur |
| `["groupingByCount", ["mod", k]]` | a dict whose keys are `str(x % k)` using Java's remainder (sign of the left operand) |

Ignore overflow. **Example** `run_pipeline([5, 3, 8, 3, 10], [["filter", ["gt", 2]], ["distinct"], ["sorted"], ["limit", 3], ["map", ["mul", 2]], ["toList"]])`
→ `[6, 10, 16]`
""",
    starter='''def run_pipeline(data, ops):
    pass
''',
    solution='''def run_pipeline(data, ops):
    def jmod(a, b):
        r = abs(a) % abs(b)
        return -r if a < 0 else r

    xs = list(data)
    for op in ops:
        name = op[0]
        arg = op[1] if len(op) > 1 else None
        if name == "filter":
            if arg == "even":
                xs = [x for x in xs if x % 2 == 0]
            elif arg == "odd":
                xs = [x for x in xs if x % 2 != 0]
            elif arg == "positive":
                xs = [x for x in xs if x > 0]
            else:
                xs = [x for x in xs if x > arg[1]]
        elif name == "map":
            if arg == "square":
                xs = [x * x for x in xs]
            elif arg == "abs":
                xs = [abs(x) for x in xs]
            elif arg[0] == "mul":
                xs = [x * arg[1] for x in xs]
            else:
                xs = [x + arg[1] for x in xs]
        elif name == "flatMap":
            xs = [int(ch) for x in xs for ch in str(abs(x))]
        elif name == "distinct":
            seen, out = set(), []
            for x in xs:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
            xs = out
        elif name == "sorted":
            xs = sorted(xs)
        elif name == "limit":
            xs = xs[:arg]
        elif name == "skip":
            xs = xs[arg:]
        elif name == "toList":
            return xs
        elif name == "count":
            return len(xs)
        elif name == "sum":
            return sum(xs)
        elif name == "groupingByCount":
            groups = {}
            for x in xs:
                if arg == "parity":
                    key = "even" if x % 2 == 0 else "odd"
                else:
                    key = str(jmod(x, arg[1]))
                groups[key] = groups.get(key, 0) + 1
            return groups
''',
    tests=[
        [[5, 3, 8, 3, 10], [["filter", ["gt", 2]], ["distinct"], ["sorted"], ["limit", 3], ["map", ["mul", 2]], ["toList"]]],
        [[1, 2, 3, 4, 5], [["filter", "odd"], ["map", "square"], ["sum"]]],
        [[], [["map", "square"], ["toList"]]],
        [[], [["sum"]]],
        [[12, 305, 0, -47], [["flatMap", "digits"], ["toList"]]],
        [[12, 305, 0, -47], [["flatMap", "digits"], ["distinct"], ["count"]]],
        [[1, 2, 3, 4, 5, 6, 7], [["groupingByCount", "parity"]]],
        [[-7, -3, 0, 4, 8], [["groupingByCount", ["mod", 3]]]],
        [[4, 4, 4], [["distinct"], ["toList"]]],
        [[9, 1, 5, 3, 7], [["sorted"], ["skip", 1], ["limit", 3], ["toList"]]],
        [[9, 1, 5, 3, 7], [["limit", 3], ["sorted"], ["toList"]]],
        [[-2, -1, 0, 1, 2], [["filter", "positive"], ["count"]]],
        [[-2, -1, 0, 1, 2], [["map", "abs"], ["distinct"], ["map", ["add", 10]], ["toList"]]],
        [[2, 4, 6], [["filter", "odd"], ["groupingByCount", "parity"]]],
        [[3, 1, 2], [["skip", 5], ["toList"]]],
    ],
    wrong_solutions=[
        '''def run_pipeline(data, ops):
    xs = list(data)
    for op in ops:
        name = op[0]; arg = op[1] if len(op) > 1 else None
        if name == "filter":
            if arg == "even": xs = [x for x in xs if x % 2 == 0]
            elif arg == "odd": xs = [x for x in xs if x % 2 != 0]
            elif arg == "positive": xs = [x for x in xs if x > 0]
            else: xs = [x for x in xs if x > arg[1]]
        elif name == "map":
            if arg == "square": xs = [x * x for x in xs]
            elif arg == "abs": xs = [abs(x) for x in xs]
            elif arg[0] == "mul": xs = [x * arg[1] for x in xs]
            else: xs = [x + arg[1] for x in xs]
        elif name == "flatMap": xs = [int(ch) for x in xs for ch in str(abs(x))]
        elif name == "distinct": xs = sorted(set(xs))
        elif name == "sorted": xs = sorted(xs)
        elif name == "limit": xs = xs[:arg]
        elif name == "skip": xs = xs[arg:]
        elif name == "toList": return xs
        elif name == "count": return len(xs)
        elif name == "sum": return sum(xs)
        elif name == "groupingByCount":
            g = {}
            for x in xs:
                key = ("even" if x % 2 == 0 else "odd") if arg == "parity" else str(x % arg[1])
                g[key] = g.get(key, 0) + 1
            return g
''',
        '''def run_pipeline(data, ops):
    xs = list(data)
    order = {"filter": 0, "map": 1, "flatMap": 1, "distinct": 2, "sorted": 3, "skip": 4, "limit": 5}
    inter = sorted(ops[:-1], key=lambda o: order[o[0]])
    def jmod(a, b):
        r = abs(a) % abs(b)
        return -r if a < 0 else r
    for op in inter + [ops[-1]]:
        name = op[0]; arg = op[1] if len(op) > 1 else None
        if name == "filter":
            if arg == "even": xs = [x for x in xs if x % 2 == 0]
            elif arg == "odd": xs = [x for x in xs if x % 2 != 0]
            elif arg == "positive": xs = [x for x in xs if x > 0]
            else: xs = [x for x in xs if x > arg[1]]
        elif name == "map":
            if arg == "square": xs = [x * x for x in xs]
            elif arg == "abs": xs = [abs(x) for x in xs]
            elif arg[0] == "mul": xs = [x * arg[1] for x in xs]
            else: xs = [x + arg[1] for x in xs]
        elif name == "flatMap": xs = [int(ch) for x in xs for ch in str(abs(x))]
        elif name == "distinct":
            seen, out = set(), []
            for x in xs:
                if x not in seen:
                    seen.add(x); out.append(x)
            xs = out
        elif name == "sorted": xs = sorted(xs)
        elif name == "limit": xs = xs[:arg]
        elif name == "skip": xs = xs[arg:]
        elif name == "toList": return xs
        elif name == "count": return len(xs)
        elif name == "sum": return sum(xs)
        elif name == "groupingByCount":
            g = {}
            for x in xs:
                key = ("even" if x % 2 == 0 else "odd") if arg == "parity" else str(jmod(x, arg[1]))
                g[key] = g.get(key, 0) + 1
            return g
''',
    ],
    guide=G(
        "Lesson *The Stream API, collectors and Optional*.",
        "Although Java runs a pipeline lazily, one element at a time, the **result** is the same as applying "
        "each stage to the whole sequence in the order written. So transform a list stage by stage and finish "
        "with the terminal operation.",
        ["Keep a current list and replace it at every intermediate stage.",
         "`distinct` must keep first occurrences in encounter order: a plain `set` loses the order.",
         "`groupingBy(..., counting())` is a dictionary of counts; for the `mod` key use Java's remainder."],
        "Writing a special-case loop for one fixed pipeline works for that pipeline only. A small interpreter "
        "over the op list handles every combination.",
        r"""**Dry run** `[5, 3, 8, 3, 10]`: `filter > 2` → `[5, 3, 8, 3, 10]`; `distinct` → `[5, 3, 8, 10]`;
`sorted` → `[3, 5, 8, 10]`; `limit 3` → `[3, 5, 8]`; `map ×2` → `[6, 10, 16]`.

Order matters: `limit(3)` **before** `sorted()` would take `[5, 3, 8]` and then sort those three.

```java
List<Integer> result = Stream.of(5, 3, 8, 3, 10)
        .filter(x -> x > 2)
        .distinct()
        .sorted()
        .limit(3)
        .map(x -> x * 2)
        .toList();                                           // [6, 10, 16]

Map<String, Long> byParity = Stream.of(1, 2, 3, 4, 5, 6, 7)
        .collect(Collectors.groupingBy(x -> x % 2 == 0 ? "even" : "odd", Collectors.counting()));
// {even=3, odd=4}
```""",
        "Time O(n log n) when `sorted` is present, otherwise O(n) per stage; space O(n).",
        "- Implementing `distinct` with a set and losing encounter order.\n- Reordering stages.\n"
        "- Using Python's `%` for negative numbers in the `mod` key (Java: `-7 % 3 == -1`).\n"
        "- Returning a key with count 0 in the grouping result.",
    ),
),
# ------------------------------------------------------------------ java-optional-chain
dict(
    id="java-optional-chain",
    title="Optional chaining",
    difficulty="Easy",
    pattern="Java streams",
    entry="optional_chain",
    description=r"""
Evaluate `Optional.ofNullable(value).<ops>.orElse(default)`.

`value` is an integer or `None` (Java `null`). `ops` is a list of:

| op | Java | effect on a present value `x` |
|---|---|---|
| `["map", ["add", k]]` | `.map(x -> x + k)` | becomes `x + k` |
| `["map", ["mul", k]]` | `.map(x -> x * k)` | becomes `x * k` |
| `["map", "halfIfEven"]` | `.map(x -> x % 2 == 0 ? x / 2 : null)` | `x / 2` if even; a function returning `null` makes the Optional **empty** |
| `["filter", "positive"]` | `.filter(x -> x > 0)` | empty unless `x > 0` |
| `["filter", ["lt", k]]` | `.filter(x -> x < k)` | empty unless `x < k` |
| `["flatMap", table]` | `.flatMap(x -> lookup(x))` | `table` is a dict with string keys; present with `table[str(x)]` if that key exists, otherwise empty |

Once the Optional is empty, every later operation leaves it empty. Return the final value, or `default` if
the Optional is empty at the end.

**Example** `optional_chain(8, [["map", "halfIfEven"], ["filter", "positive"], ["map", ["add", 1]]], -1)` → `5`;
`optional_chain(7, [["map", "halfIfEven"], ["map", ["add", 1]]], -1)` → `-1`.
""",
    starter='''def optional_chain(value, ops, default):
    pass
''',
    solution='''def optional_chain(value, ops, default):
    present = value is not None
    x = value
    for op in ops:
        if not present:
            break
        kind, arg = op
        if kind == "map":
            if arg == "halfIfEven":
                if x % 2 == 0:
                    x = x // 2
                else:
                    present = False
            elif arg[0] == "add":
                x = x + arg[1]
            else:
                x = x * arg[1]
        elif kind == "filter":
            if arg == "positive":
                present = x > 0
            else:
                present = x < arg[1]
        else:
            if str(x) in arg:
                x = arg[str(x)]
            else:
                present = False
    return x if present else default
''',
    tests=[
        [8, [["map", "halfIfEven"], ["filter", "positive"], ["map", ["add", 1]]], -1],
        [7, [["map", "halfIfEven"], ["map", ["add", 1]]], -1],
        [None, [["map", ["add", 1]]], 99],
        [5, [], 0],
        [None, [], 0],
        [5, [["filter", ["lt", 5]]], 0],
        [4, [["filter", ["lt", 5]], ["map", ["mul", 3]]], 0],
        [2, [["flatMap", {"2": 20, "3": 30}], ["map", ["add", 1]]], -1],
        [4, [["flatMap", {"2": 20, "3": 30}], ["map", ["add", 1]]], -1],
        [-6, [["map", "halfIfEven"], ["filter", "positive"]], 0],
        [0, [["filter", "positive"]], 123],
        [0, [["map", "halfIfEven"], ["map", ["add", 5]]], -1],
        [3, [["map", ["mul", 2]], ["map", "halfIfEven"], ["flatMap", {"3": 0}], ["filter", "positive"]], 77],        [5, [["map", ["add", -5]]], 9],
        [0, [], 123],
    ],
    wrong_solutions=[
        '''def optional_chain(value, ops, default):
    x = value
    for kind, arg in ops:
        if x is None:
            return default
        if kind == "map":
            if arg == "halfIfEven": x = x // 2 if x % 2 == 0 else None
            elif arg[0] == "add": x = x + arg[1]
            else: x = x * arg[1]
        elif kind == "filter":
            ok = x > 0 if arg == "positive" else x < arg[1]
            if not ok: x = None
        else:
            x = arg.get(str(x))
    return x or default
''',
        '''def optional_chain(value, ops, default):
    if value is None:
        return default
    x = value
    for kind, arg in ops:
        if kind == "map":
            if arg == "halfIfEven": x = x // 2
            elif arg[0] == "add": x = x + arg[1]
            else: x = x * arg[1]
        elif kind == "filter":
            if not (x > 0 if arg == "positive" else x < arg[1]):
                return default
        else:
            if str(x) not in arg:
                return default
            x = arg[str(x)]
    return x
''',
    ],
    guide=G(
        "Lessons *The Stream API, collectors and Optional* and *Varargs, empty collections, Optional returns and documentation*.",
        "An Optional is a box that is either full or empty. Each operation looks inside only if the box is full; "
        "an empty box passes through everything untouched until `orElse` supplies the default.",
        ["Track two things: whether a value is present, and the value.",
         "`map` with a function that returns null empties the box.",
         "A present value of 0 is still present: do not test the value's truthiness."],
        "Nested `if (x != null)` checks do the same job in Java and grow one level deeper per step. That nesting is "
        "what Optional's `map`, `filter` and `flatMap` replace.",
        r"""**Dry run** `optional_chain(8, [halfIfEven, positive, add 1], -1)`: present 8 → 4 → still positive →
5. Return 5.

**Dry run** `optional_chain(0, [filter positive], 123)`: 0 is not `> 0`, so the box empties → 123. And
`optional_chain(0, [], 123)` returns 0, not 123: zero is a perfectly good value.

```java
static int compute(Integer value) {
    return Optional.ofNullable(value)
            .map(x -> x % 2 == 0 ? x / 2 : null)     // a null result makes the Optional empty
            .filter(x -> x > 0)
            .map(x -> x + 1)
            .orElse(-1);
}
// compute(8) == 5, compute(7) == -1, compute(null) == -1
```""",
        "Time O(number of operations), space O(1).",
        "- Using `x or default`, which replaces a legitimate 0.\n- Continuing to apply functions after the Optional became empty.\n"
        "- Forgetting that `map` to null yields empty.",
    ),
),
# ------------------------------------------------------------------ java-builder-validation
dict(
    id="java-builder-validation",
    title="Builder with validation",
    difficulty="Medium",
    pattern="Java objects",
    entry="build_pizza",
    description=r"""
Simulate a fluent builder: `Pizza.builder().size(30).crust("thin").topping("olive").extraCheese().build()`.

`build_pizza(calls)` receives the method calls in order, each `[method, arg]` or `[method]`:

| call | effect |
|---|---|
| `["size", n]` | set the size in cm (a later call overwrites an earlier one) |
| `["crust", name]` | must be `"classic"`, `"thin"` or `"deep"`; anything else throws **immediately** |
| `["topping", name]` | add a topping (duplicates are kept) |
| `["extraCheese"]` | set the flag |
| `["build"]` | validate and create; calls after `build` are ignored |

Defaults: crust `"classic"`, no toppings, no extra cheese, size unset.

**Return**

- an invalid crust: `"IllegalArgumentException: unknown crust <name>"` (stop at that call);
- at `build`, check in this order and return the first failure:
  1. size never set → `"IllegalStateException: size is required"`
  2. size not in 15..50 → `"IllegalStateException: size must be 15..50 but was <n>"`
  3. more than 5 toppings → `"IllegalStateException: at most 5 toppings but got <k>"`
- on success: `{"size": n, "crust": c, "extraCheese": bool, "toppings": [...]}` (toppings in the order added);
- if `build` is never called: `"not built"`.
""",
    starter='''def build_pizza(calls):
    pass
''',
    solution='''def build_pizza(calls):
    size, crust, cheese, toppings = None, "classic", False, []
    for call in calls:
        m = call[0]
        if m == "size":
            size = call[1]
        elif m == "crust":
            if call[1] not in ("classic", "thin", "deep"):
                return "IllegalArgumentException: unknown crust " + call[1]
            crust = call[1]
        elif m == "topping":
            toppings.append(call[1])
        elif m == "extraCheese":
            cheese = True
        elif m == "build":
            if size is None:
                return "IllegalStateException: size is required"
            if size < 15 or size > 50:
                return "IllegalStateException: size must be 15..50 but was " + str(size)
            if len(toppings) > 5:
                return "IllegalStateException: at most 5 toppings but got " + str(len(toppings))
            return {"size": size, "crust": crust, "extraCheese": cheese, "toppings": list(toppings)}
    return "not built"
''',
    tests=[
        [[["size", 30], ["crust", "thin"], ["topping", "olive"], ["extraCheese"], ["build"]]],
        [[["build"]]],
        [[["size", 10], ["build"]]],
        [[["size", 10], ["size", 20], ["build"]]],
        [[["size", 30], ["crust", "stuffed"], ["build"]]],
        [[["crust", "stuffed"]]],
        [[["size", 30]]],
        [[]],
        [[["size", 50], ["topping", "a"], ["topping", "b"], ["topping", "c"], ["topping", "d"], ["topping", "e"], ["build"]]],
        [[["size", 50], ["topping", "a"], ["topping", "a"], ["topping", "a"], ["topping", "a"], ["topping", "a"], ["topping", "a"], ["build"]]],
        [[["size", 15], ["build"], ["size", 99], ["crust", "nope"]]],
        [[["topping", "x"], ["topping", "y"], ["topping", "z"], ["topping", "p"], ["topping", "q"], ["topping", "r"], ["size", 51], ["build"]]],
        [[["crust", "deep"], ["crust", "thin"], ["extraCheese"], ["extraCheese"], ["size", 22], ["build"]]],
    ],
    wrong_solutions=[
        '''def build_pizza(calls):
    size, crust, cheese, toppings = None, "classic", False, []
    for call in calls:
        m = call[0]
        if m == "size":
            if call[1] < 15 or call[1] > 50:
                return "IllegalStateException: size must be 15..50 but was " + str(call[1])
            size = call[1]
        elif m == "crust":
            if call[1] not in ("classic", "thin", "deep"):
                return "IllegalArgumentException: unknown crust " + call[1]
            crust = call[1]
        elif m == "topping":
            toppings.append(call[1])
            if len(toppings) > 5:
                return "IllegalStateException: at most 5 toppings but got " + str(len(toppings))
        elif m == "extraCheese": cheese = True
        elif m == "build":
            if size is None: return "IllegalStateException: size is required"
            return {"size": size, "crust": crust, "extraCheese": cheese, "toppings": list(toppings)}
    return "not built"
''',
        '''def build_pizza(calls):
    size, crust, cheese, toppings = None, "classic", False, []
    for call in calls:
        m = call[0]
        if m == "size": size = call[1]
        elif m == "crust":
            if call[1] not in ("classic", "thin", "deep"):
                return "IllegalArgumentException: unknown crust " + call[1]
            crust = call[1]
        elif m == "topping": toppings.append(call[1])
        elif m == "extraCheese": cheese = True
    if size is None: return "IllegalStateException: size is required"
    if size < 15 or size > 50: return "IllegalStateException: size must be 15..50 but was " + str(size)
    if len(toppings) > 5: return "IllegalStateException: at most 5 toppings but got " + str(len(toppings))
    return {"size": size, "crust": crust, "extraCheese": cheese, "toppings": list(toppings)}
''',
    ],
    guide=G(
        "Lesson *Static factories, builders, singletons and dependency injection*: the builder pattern.",
        "The builder is a mutable scratch pad. Setter-like calls only record values; **`build` is the single gate** "
        "where rules involving the finished object are checked. A value that is invalid in isolation (an unknown "
        "crust) can be rejected at once.",
        ["Keep four variables for the builder's state.", "Reject a bad crust immediately; record everything else without judging.",
         "At `build`, check in the stated order and return; anything after `build` is ignored."],
        "Validating the size inside `size(...)` looks tidy and changes the behaviour: `size(10)` followed by "
        "`size(20)` would fail although the pizza finally asked for is valid.",
        r"""**Dry run** `[size 10, size 20, build]`: size becomes 10, then 20. At build: set, within 15..50, zero
toppings → `{"size": 20, "crust": "classic", "extraCheese": False, "toppings": []}`.

```java
public final class Pizza {
    private final int size; private final String crust; private final boolean extraCheese; private final List<String> toppings;

    private Pizza(Builder b) { size = b.size; crust = b.crust; extraCheese = b.extraCheese; toppings = List.copyOf(b.toppings); }
    public static Builder builder() { return new Builder(); }

    public static final class Builder {
        private Integer size; private String crust = "classic"; private boolean extraCheese; private final List<String> toppings = new ArrayList<>();

        public Builder size(int cm)          { this.size = cm; return this; }
        public Builder crust(String c) {
            if (!Set.of("classic", "thin", "deep").contains(c)) throw new IllegalArgumentException("unknown crust " + c);
            this.crust = c; return this;
        }
        public Builder topping(String t)     { toppings.add(t); return this; }
        public Builder extraCheese()         { this.extraCheese = true; return this; }

        public Pizza build() {
            if (size == null) throw new IllegalStateException("size is required");
            if (size < 15 || size > 50) throw new IllegalStateException("size must be 15..50 but was " + size);
            if (toppings.size() > 5) throw new IllegalStateException("at most 5 toppings but got " + toppings.size());
            return new Pizza(this);
        }
    }
}
```""",
        "Time O(number of calls), space O(number of toppings).",
        "- Validating cross-field rules before `build`.\n- Processing calls after `build`.\n"
        "- Returning the builder's own toppings list instead of a copy.\n- Checking the rules in a different order.",
    ),
),
# ------------------------------------------------------------------ java-defensive-copy
dict(
    id="java-defensive-copy",
    title="Defensive copies: does the object leak?",
    difficulty="Medium",
    pattern="Java classes",
    entry="playlist_states",
    description=r"""
A class `Playlist` holds a list of track numbers. Depending on how carefully it was written, outside code
may be able to change its contents.

`playlist_states(copy_in, copy_out, initial, actions)` simulates:

```java
List<Integer> source = new ArrayList<>(initial);
Playlist p = new Playlist(source);      // stores source itself, or a copy if copy_in
```

then performs `actions`:

| action | Java | effect |
|---|---|---|
| `["mutate_source", v]` | `source.add(v);` | changes the playlist too, **unless** the constructor copied |
| `["mutate_returned", v]` | `p.tracks().add(v);` | `tracks()` returns the internal list, or a fresh copy if `copy_out`; the add goes to whatever was returned |
| `["read"]` | `p.tracks()` | append a **snapshot** of the playlist's internal list to the output |

Return the list of snapshots.

Note the combined case: with `copy_in` false and `copy_out` false, the list returned by `tracks()` **is**
`source`, so `mutate_returned` changes both.

**Example** `playlist_states(False, True, [1], [["mutate_source", 2], ["mutate_returned", 3], ["read"]])` → `[[1, 2]]`
""",
    starter='''def playlist_states(copy_in, copy_out, initial, actions):
    pass
''',
    solution='''def playlist_states(copy_in, copy_out, initial, actions):
    source = list(initial)
    internal = list(source) if copy_in else source
    out = []
    for a in actions:
        if a[0] == "mutate_source":
            source.append(a[1])
        elif a[0] == "mutate_returned":
            returned = list(internal) if copy_out else internal
            returned.append(a[1])
        else:
            out.append(list(internal))
    return out
''',
    tests=[
        [False, True, [1], [["mutate_source", 2], ["mutate_returned", 3], ["read"]]],
        [True, True, [1], [["mutate_source", 2], ["mutate_returned", 3], ["read"]]],
        [False, False, [1], [["mutate_source", 2], ["mutate_returned", 3], ["read"]]],
        [True, False, [1], [["mutate_source", 2], ["mutate_returned", 3], ["read"]]],
        [True, True, [], [["read"]]],
        [False, False, [], []],
        [False, False, [5], [["read"], ["mutate_returned", 6], ["read"], ["mutate_source", 7], ["read"]]],
        [True, False, [5], [["read"], ["mutate_returned", 6], ["read"], ["mutate_source", 7], ["read"]]],
        [False, True, [5], [["read"], ["mutate_returned", 6], ["read"], ["mutate_source", 7], ["read"]]],
        [True, True, [1, 2, 3], [["mutate_source", 9], ["mutate_source", 9], ["read"], ["mutate_returned", 0], ["read"]]],
        [False, False, [1, 2, 3], [["mutate_returned", 4], ["mutate_source", 5], ["mutate_returned", 6], ["read"]]],
    ],
    wrong_solutions=[
        '''def playlist_states(copy_in, copy_out, initial, actions):
    internal = list(initial)
    out = []
    for a in actions:
        if a[0] == "mutate_source" and not copy_in: internal.append(a[1])
        elif a[0] == "mutate_returned" and not copy_out: internal.append(a[1])
        elif a[0] == "read": out.append(internal)
    return out
''',
        '''def playlist_states(copy_in, copy_out, initial, actions):
    source = list(initial)
    internal = list(source)
    out = []
    for a in actions:
        if a[0] == "mutate_source": source.append(a[1])
        elif a[0] == "mutate_returned":
            returned = list(internal) if copy_out else internal
            returned.append(a[1])
        else: out.append(list(internal))
    return out
''',
    ],
    guide=G(
        "Lessons *Minimal accessibility and immutable classes* and *Parameter checks, defensive copies, signatures and overloading*.",
        "Model the objects, not the outcomes. There is a `source` list and an `internal` list; they are the same "
        "Python object when the constructor did not copy. `tracks()` hands back either `internal` itself or a copy.",
        ["Create `internal` as an alias of `source` or as a copy, depending on `copy_in`.",
         "For `mutate_returned`, pick the object that `tracks()` returns and append to that.",
         "A `read` must append a snapshot (`list(internal)`), or later changes will alter earlier output."],
        "Tracking only 'does this action reach the playlist?' with flags works until you forget to snapshot: "
        "appending the same list object several times makes every earlier snapshot show the final state.",
        r"""**Dry run** `copy_in=False, copy_out=True, initial=[1]`. `internal` **is** `source`. `mutate_source 2` →
both are `[1, 2]`. `mutate_returned 3`: `tracks()` returns a copy `[1, 2]`; the 3 goes into that copy and is
lost. `read` → `[1, 2]`. One leak (the constructor) out of two.

```java
public final class Playlist {
    private final List<Integer> tracks;

    public Playlist(List<Integer> tracks) {
        this.tracks = List.copyOf(tracks);        // copy in: later changes to the caller's list do not reach us
    }

    public List<Integer> tracks() {
        return tracks;                            // List.copyOf is unmodifiable, so handing it out is safe
    }
}

List<Integer> source = new ArrayList<>(List.of(1));
Playlist p = new Playlist(source);
source.add(2);                                    // no effect on p
// p.tracks().add(3);                             // UnsupportedOperationException
```""",
        "Time O(actions × list length) because of the snapshots, space O(output).",
        "- Appending `internal` itself for `read` instead of a snapshot.\n- Always copying in the constructor.\n"
        "- Forgetting that an uncopied `internal` and `source` are one object.",
    ),
),
]
