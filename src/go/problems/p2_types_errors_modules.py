"""Go track problems, part 2: embedding, method sets, nil interfaces, generic constraints, error chains,
module versions, build constraints and struct tags."""

PROBLEMS = [
# ------------------------------------------------------------------ go-embed-promotion
dict(
    id="go-embed-promotion",
    title="Struct embedding: which field or method is selected?",
    difficulty="Medium",
    pattern="Go types",
    entry="resolve",
    description=r"""
Go has no inheritance. Instead a struct can **embed** another type: you write the type name with no
field name, and the inner type's fields and methods become reachable directly on the outer value.
This is called **promotion**.

```go
type Engine struct{ Power int }
func (Engine) Start() {}
type Car struct {
    Engine      // embedded
    Name string
}
// car.Power and car.Start() work: they are promoted from Engine
```

You are given `types`, a dictionary `name -> {"fields": [...], "methods": [...], "embeds": [...]}`
(any key may be missing). An entry of `embeds` is a type name, optionally written `"*T"` for an
embedded pointer; it behaves like `T` here.

For each query `[type, selector]` decide what `value.selector` means, using Go's rule:

- **Depth 0** is the type itself. Its names are its fields, its methods, and each embedded type's
  name (embedding `Engine` or `*Engine` creates a field called `Engine`).
- **Depth 1** holds the names of the types embedded at depth 0, depth 2 the types they embed, and so on.
  A type reached along two different paths counts twice.
- Find the **shallowest** depth where the selector appears. If it appears exactly **once** there, the
  answer is `[owner_type, depth]`. If it appears more than once at that depth, the answer is
  `"ambiguous"` (a compile error in Go). If it appears nowhere, the answer is `"undefined"`.

Embedding never forms a cycle. Return the list of answers.

**Example:** with
`types = {"Engine": {"fields": ["Power"], "methods": ["Start"]}, "Car": {"fields": ["Name"], "embeds": ["Engine"]}}`

`resolve(types, [["Car","Name"], ["Car","Power"], ["Car","Engine"], ["Car","Stop"]])`
→ `[["Car", 0], ["Engine", 1], ["Car", 0], "undefined"]`
""",
    starter='''def resolve(types, queries):
    pass
''',
    solution='''def resolve(types, queries):
    def names(t):
        d = types.get(t, {})
        own = list(d.get("fields", [])) + list(d.get("methods", []))
        return own + [e.lstrip("*") for e in d.get("embeds", [])]

    out = []
    for start, sel in queries:
        level = [start]
        depth = 0
        ans = "undefined"
        while level:
            hits = [t for t in level for n in names(t) if n == sel]
            if len(hits) == 1:
                ans = [hits[0], depth]
                break
            if len(hits) > 1:
                ans = "ambiguous"
                break
            level = [e.lstrip("*") for t in level for e in types.get(t, {}).get("embeds", [])]
            depth += 1
        out.append(ans)
    return out
''',
    tests=[
        [{"Engine": {"fields": ["Power"], "methods": ["Start"]}, "Car": {"fields": ["Name"], "embeds": ["Engine"]}},
         [["Car", "Name"], ["Car", "Power"], ["Car", "Engine"], ["Car", "Stop"]]],
        [{"A": {"methods": ["Hello"]}, "B": {"methods": ["Hello"]}, "C": {"embeds": ["A", "B"]}},
         [["C", "Hello"], ["C", "A"], ["A", "Hello"]]],
        [{"A": {"methods": ["Hello"]}, "B": {"methods": ["Hello"]}, "C": {"embeds": ["A", "B"], "methods": ["Hello"]}},
         [["C", "Hello"]]],
        [{"Base": {"fields": ["ID"]}, "Mid": {"embeds": ["Base"], "fields": ["ID"]}, "Top": {"embeds": ["Mid"]}},
         [["Top", "ID"], ["Mid", "ID"], ["Top", "Base"], ["Top", "Mid"]]],
        [{"Base": {"fields": ["ID"]}, "L": {"embeds": ["Base"]}, "R": {"embeds": ["Base"]}, "D": {"embeds": ["L", "R"]}},
         [["D", "ID"], ["D", "Base"], ["L", "ID"], ["D", "L"]]],
        [{"Deep": {"fields": ["X"]}, "A": {"embeds": ["Deep"]}, "B": {"fields": ["X"]}, "C": {"embeds": ["A", "B"]}},
         [["C", "X"], ["C", "Deep"]]],
        [{"Logger": {"methods": ["Log"]}, "Svc": {"embeds": ["*Logger"], "fields": ["name"]}},
         [["Svc", "Log"], ["Svc", "Logger"], ["Svc", "name"], ["Svc", "*Logger"]]],
        [{"Empty": {}}, [["Empty", "x"]]],
        [{"A": {"fields": ["v"]}}, []],
        [{"T0": {"fields": ["bottom"]}, "T1": {"embeds": ["T0"]}, "T2": {"embeds": ["T1"]}, "T3": {"embeds": ["T2"]},
          "T4": {"embeds": ["T3"]}}, [["T4", "bottom"], ["T4", "T0"], ["T4", "T3"], ["T2", "bottom"]]],
        [{"X": {"methods": ["M"]}, "Y": {"methods": ["M"]}, "P": {"embeds": ["X"]}, "Q": {"embeds": ["Y"]},
          "Z": {"embeds": ["P", "Q"], "fields": ["own"]}}, [["Z", "M"], ["P", "M"], ["Z", "own"], ["Z", "X"]]],
        [{"Reader": {"methods": ["Read", "Close"]}, "Writer": {"methods": ["Write", "Close"]},
          "RW": {"embeds": ["Reader", "Writer"]}}, [["RW", "Read"], ["RW", "Write"], ["RW", "Close"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def resolve(types, queries):
    def search(t, sel, depth):
        d = types.get(t, {})
        if sel in d.get("fields", []) or sel in d.get("methods", []) or sel in [e.lstrip("*") for e in d.get("embeds", [])]:
            return [t, depth]
        for e in d.get("embeds", []):
            r = search(e.lstrip("*"), sel, depth + 1)
            if r != "undefined":
                return r
        return "undefined"
    return [search(t, s, 0) for t, s in queries]
''',
        '''def resolve(types, queries):
    out = []
    for start, sel in queries:
        level = [start]; depth = 0; ans = "undefined"
        while level:
            hits = {t for t in level if sel in types.get(t, {}).get("fields", []) + types.get(t, {}).get("methods", [])
                    + [e.lstrip("*") for e in types.get(t, {}).get("embeds", [])]}
            if len(hits) == 1:
                ans = [hits.pop(), depth]; break
            if len(hits) > 1:
                ans = "ambiguous"; break
            level = [e.lstrip("*") for t in level for e in types.get(t, {}).get("embeds", [])]
            depth += 1
        out.append(ans)
    return out
''',
    ],
    guide=dict(
        prereqs="Breadth-first search. Lesson: [Defined types, methods and embedding](#/lesson/go/go-types-methods).",
        intuition="Think of the embedded types as floors of a building below the outer type. Go walks down one "
                  "floor at a time and takes the name on the first floor where it appears, provided it appears "
                  "only once on that floor. Depth beats everything; there is no left-to-right priority.",
        hints=[
            "Process a whole level at once (a list of type names), not one branch at a time.",
            "Count occurrences, not distinct owner types: the same `Base` reached through `L` and through `R` is ambiguous.",
            "The embedded type's own name is a field of the type that embeds it.",
        ],
        brute_force="Depth-first search that returns the first hit is short to write and wrong twice over: it "
                    "can prefer a deep name on the left branch over a shallow one on the right, and it never "
                    "reports ambiguity.",
        approach=r"""
Breadth-first search by levels. At each level collect every `(type, name)` hit for the selector. One hit:
done. Several: ambiguous. None: replace the level with all the types embedded by the current level.

**Dry run** (diamond): `D` embeds `L` and `R`, both embed `Base{ID}`. Query `D.ID`. Level 0 `[D]`: names are
`L, R`, no hit. Level 1 `[L, R]`: names `Base, Base`, no `ID`. Level 2 `[Base, Base]`: two hits → `"ambiguous"`.
Query `D.Base` is ambiguous too (two fields named `Base` at depth 1).

**The same behaviour in Go:**

```go
package main

import "fmt"

type Engine struct{ Power int }

func (e Engine) Start() string { return "vroom" }

type Radio struct{ Power int } // same field name as Engine.Power

type Car struct {
	Engine
	Radio
	Name string
}

func main() {
	c := Car{Engine{150}, Radio{5}, "Mini"}
	fmt.Println(c.Start())      // promoted method: vroom
	fmt.Println(c.Engine.Power) // 150: spell out the path
	// fmt.Println(c.Power)     // compile error: ambiguous selector c.Power
}
```
""",
        complexity="O(total embedded paths) per query; tiny for realistic type graphs.",
        pitfalls="Depth-first search. De-duplicating owners with a set. Forgetting the embedded type name "
                 "itself. Thinking the outer type's method 'overrides' in the class sense: it only *shadows* by "
                 "being shallower; the inner method never calls back to the outer one.",
    ),
),

# ------------------------------------------------------------------ go-method-sets
dict(
    id="go-method-sets",
    title="Method sets and interface satisfaction",
    difficulty="Medium",
    pattern="Go interfaces",
    entry="missing_methods",
    description=r"""
A Go type satisfies an interface when its **method set** contains every method the interface lists.
No `implements` keyword exists; the compiler checks the method set.

A method is declared with a **receiver**: `func (t T) Name()` has a *value receiver*,
`func (t *T) Name()` has a *pointer receiver*. The method sets are:

- the method set of `T` contains only the value-receiver methods;
- the method set of `*T` contains the value-receiver **and** the pointer-receiver methods.

Embedding adds promoted methods:

- if a struct `S` embeds `T` (by value): `S` gets the method set of `T`, and `*S` gets the method set of `*T`;
- if `S` embeds `*T`: both `S` and `*S` get the method set of `*T`.

Input:

- `types`: `name -> {"value": [methods], "pointer": [methods], "embeds": [names or "*names"]}` (keys may be missing);
- `interfaces`: `name -> [entries]`, where an entry is a method name **or the name of another
  interface** whose methods are included (interface embedding);
- `queries`: `[expr, interface]` with `expr` either `"T"` or `"*T"`.

For each query return the **sorted list of methods that are missing** (an empty list means the
type satisfies the interface).

**Example:** `types = {"File": {"value": ["Name"], "pointer": ["Write"]}}`,
`interfaces = {"Writer": ["Write"], "Named": ["Name"], "NamedWriter": ["Named", "Writer"]}`

`[["File","Named"], ["File","Writer"], ["*File","NamedWriter"]]` → `[[], ["Write"], []]`
""",
    starter='''def missing_methods(types, interfaces, queries):
    pass
''',
    solution='''def missing_methods(types, interfaces, queries):
    def mset(name, ptr):
        t = types.get(name, {})
        s = set(t.get("value", []))
        if ptr:
            s |= set(t.get("pointer", []))
        for e in t.get("embeds", []):
            if e.startswith("*"):
                s |= mset(e[1:], True)
            else:
                s |= mset(e, ptr)
        return s

    def wanted(iface, seen=()):
        need = set()
        for entry in interfaces.get(iface, []):
            if entry in interfaces and entry not in seen:
                need |= wanted(entry, seen + (iface,))
            else:
                need.add(entry)
        return need

    out = []
    for expr, iface in queries:
        ptr = expr.startswith("*")
        out.append(sorted(wanted(iface) - mset(expr.lstrip("*"), ptr)))
    return out
''',
    tests=[
        [{"File": {"value": ["Name"], "pointer": ["Write"]}},
         {"Writer": ["Write"], "Named": ["Name"], "NamedWriter": ["Named", "Writer"]},
         [["File", "Named"], ["File", "Writer"], ["*File", "NamedWriter"]]],
        [{"T": {}}, {"Empty": []}, [["T", "Empty"], ["*T", "Empty"]]],
        [{"T": {"pointer": ["A", "B"]}}, {"I": ["B", "A", "C"]}, [["T", "I"], ["*T", "I"]]],
        [{"Inner": {"value": ["V"], "pointer": ["P"]}, "Outer": {"embeds": ["Inner"]}},
         {"IV": ["V"], "IP": ["P"], "Both": ["V", "P"]},
         [["Outer", "IV"], ["Outer", "IP"], ["*Outer", "IP"], ["Outer", "Both"], ["*Outer", "Both"]]],
        [{"Inner": {"value": ["V"], "pointer": ["P"]}, "Outer": {"embeds": ["*Inner"]}},
         {"Both": ["V", "P"]}, [["Outer", "Both"], ["*Outer", "Both"]]],
        [{"A": {"pointer": ["M"]}, "B": {"embeds": ["A"]}, "C": {"embeds": ["B"]}},
         {"I": ["M"]}, [["C", "I"], ["*C", "I"], ["B", "I"], ["*B", "I"]]],
        [{"A": {"pointer": ["M"]}, "B": {"embeds": ["*A"]}, "C": {"embeds": ["B"]}},
         {"I": ["M"]}, [["C", "I"], ["*C", "I"]]],
        [{"Buf": {"pointer": ["Read", "Write"], "value": ["Len"]}},
         {"Reader": ["Read"], "Writer": ["Write"], "ReadWriter": ["Reader", "Writer"],
          "Sized": ["Len"], "All": ["ReadWriter", "Sized", "Close"]},
         [["Buf", "All"], ["*Buf", "All"], ["Buf", "Sized"], ["*Buf", "ReadWriter"]]],
        [{"S": {"value": ["String"]}}, {"Stringer": ["String"], "error": ["Error"]},
         [["S", "Stringer"], ["*S", "Stringer"], ["S", "error"]]],
        [{"S": {"value": ["x"]}}, {"I": ["x"]}, []],
        [{"Lock": {"pointer": ["Lock", "Unlock"]}, "Counter": {"embeds": ["Lock"], "pointer": ["Inc"], "value": ["Get"]}},
         {"Locker": ["Lock", "Unlock"], "IncGetter": ["Inc", "Get"]},
         [["Counter", "Locker"], ["*Counter", "Locker"], ["Counter", "IncGetter"], ["*Counter", "IncGetter"]]],
        [{"T": {"value": ["A"]}}, {"I": ["Missing2", "Missing1", "A"]}, [["Unknown", "I"], ["T", "I"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def missing_methods(types, interfaces, queries):
    def mset(name):
        t = types.get(name, {})
        s = set(t.get("value", [])) | set(t.get("pointer", []))
        for e in t.get("embeds", []):
            s |= mset(e.lstrip("*"))
        return s
    def wanted(i):
        need = set()
        for e in interfaces.get(i, []):
            need |= wanted(e) if e in interfaces else {e}
        return need
    return [sorted(wanted(i) - mset(x.lstrip("*"))) for x, i in queries]
''',
        '''def missing_methods(types, interfaces, queries):
    def mset(name, ptr):
        t = types.get(name, {})
        s = set(t.get("value", []))
        if ptr:
            s |= set(t.get("pointer", []))
        for e in t.get("embeds", []):
            s |= mset(e.lstrip("*"), ptr)
        return s
    def wanted(i):
        need = set()
        for e in interfaces.get(i, []):
            need |= wanted(e) if e in interfaces else {e}
        return need
    return [sorted(wanted(i) - mset(x.lstrip("*"), x.startswith("*"))) for x, i in queries]
''',
    ],
    guide=dict(
        prereqs="Sets and recursion. Lessons: [Defined types, methods and embedding](#/lesson/go/go-types-methods) "
                "and [Interfaces](#/lesson/go/go-interfaces).",
        intuition="A pointer-receiver method needs an address to work on. If all you have is a plain value "
                  "stored inside an interface, Go cannot take its address, so those methods are not available. "
                  "That is the entire reason `T` has the smaller method set and `*T` the larger.",
        hints=[
            "Write `mset(name, is_pointer)` returning a set, and `wanted(interface)` that flattens embedded interfaces.",
            "For an embedded `*T`, always ask for the pointer method set. For an embedded `T`, pass along the "
            "outer `is_pointer` flag.",
            "The answer is a set difference, sorted.",
        ],
        brute_force="Treating all methods as available on both `T` and `*T` is the common mental shortcut, and "
                    "it is exactly what the compiler error `X does not implement Y (method M has pointer "
                    "receiver)` is telling you is wrong.",
        approach=r"""
`mset(T, ptr)` = value methods, plus pointer methods if `ptr`, plus for each embedded entry either
`mset(E, True)` (embedded pointer) or `mset(E, ptr)` (embedded value).

**Dry run:** `Inner{value:[V], pointer:[P]}`, `Outer` embeds `Inner`. `mset(Outer, False)` = `mset(Inner, False)` = `{V}`,
so `Outer` is missing `P` for interface `Both`. `mset(Outer, True)` = `{V, P}`. If `Outer` embedded `*Inner`
instead, both would be `{V, P}`.

**The same behaviour in Go:**

```go
package main

import "fmt"

type Shape interface{ Area() float64 }
type Scaler interface{ Scale(f float64) }

type Square struct{ side float64 }

func (s Square) Area() float64   { return s.side * s.side } // value receiver
func (s *Square) Scale(f float64) { s.side *= f }            // pointer receiver

func main() {
	var a Shape = Square{2}  // ok: Area is in the method set of Square
	var b Scaler = &Square{2} // ok: *Square has Scale
	// var c Scaler = Square{2}
	// compile error: Square does not implement Scaler (method Scale has pointer receiver)
	b.Scale(3)
	fmt.Println(a.Area(), b.(*Square).Area()) // 4 36
}
```
""",
        complexity="O(size of the embedding tree + size of the interface) per query.",
        pitfalls="Giving `T` the pointer-receiver methods. Mishandling embedded pointers (they always "
                 "contribute the full set). Forgetting to expand embedded interfaces. Note that calling "
                 "`v.Scale(3)` on an *addressable variable* `v` of type `Square` compiles because Go rewrites it "
                 "to `(&v).Scale(3)`; that convenience does not change the method set.",
    ),
),

# ------------------------------------------------------------------ go-nil-interface
dict(
    id="go-nil-interface",
    title="The nil interface puzzle",
    difficulty="Medium",
    pattern="Go interfaces",
    entry="eval_nil",
    description=r"""
An interface value in Go is a pair: **(dynamic type, value)**. It equals `nil` only when **both**
parts are empty. If you store a nil pointer of type `*T` in an interface, the pair is `(*T, nil)`:
the type part is filled in, so the interface is **not** nil. This surprises almost everyone once.

Simulate these statements and collect the outputs. Variable kinds are fixed at declaration.

| statement | Go | effect / output |
|---|---|---|
| `["iface", x]` | `var x any` | interface variable holding `(none, none)` |
| `["nilptr", p, T]` | `var p *T` | pointer variable of type `*T` holding nil |
| `["newptr", p, T]` | `p := &T{}` | pointer variable of type `*T` pointing to a fresh object |
| `["assign", dst, src]` | `dst = src` | `src` is a variable name or the literal `"nil"` (see below) |
| `["isnil", x]` | `x == nil` | outputs `true`/`false` |
| `["eq", a, b]` | `a == b` | outputs `true`/`false` |
| `["type", x]` | `fmt.Sprintf("%T", x)` | outputs the dynamic type such as `"*T"`, or `"<nil>"` for a nil interface |
| `["call", x, kind]` | `x.Method()` | outputs `"ok"` or `"panic"` (the simulation continues) |

**assign.** Into an interface variable: `"nil"` stores `(none, none)`; a pointer variable `p` of type
`*T` stores `(*T, p's value)`; another interface is copied as it is. Into a pointer variable:
`"nil"` clears the value; another pointer variable copies its value (types always match in the tests).

**isnil.** Interface: true only for `(none, none)`. Pointer: true when the value is nil.

**eq.** Convert both sides to pairs (a pointer variable of type `*T` becomes `(*T, value)`) and
compare both parts. Two pointers are equal when they point to the same object.

**call.** `kind` is `"safe"` (the method never touches its receiver's fields) or `"deref"` (it reads a field).
A nil interface panics for both kinds. A nil pointer (direct, or inside an interface) is `"ok"` for
`"safe"` and `"panic"` for `"deref"`. A non-nil pointer is always `"ok"`.

**Example:** `[["nilptr","p","MyErr"], ["iface","err"], ["isnil","err"], ["assign","err","p"], ["isnil","p"], ["isnil","err"], ["type","err"]]`
→ `[true, true, false, "*MyErr"]`
""",
    starter='''def eval_nil(stmts):
    pass
''',
    solution='''def eval_nil(stmts):
    kinds = {}
    vals = {}
    out = []
    counter = [0]

    def pair(name):
        return vals[name]

    for st in stmts:
        op = st[0]
        if op == "iface":
            kinds[st[1]] = "iface"
            vals[st[1]] = (None, None)
        elif op == "nilptr":
            kinds[st[1]] = "ptr"
            vals[st[1]] = ("*" + st[2], None)
        elif op == "newptr":
            counter[0] += 1
            kinds[st[1]] = "ptr"
            vals[st[1]] = ("*" + st[2], counter[0])
        elif op == "assign":
            dst, src = st[1], st[2]
            if kinds[dst] == "iface":
                vals[dst] = (None, None) if src == "nil" else vals[src]
            else:
                vals[dst] = (vals[dst][0], None if src == "nil" else vals[src][1])
        elif op == "isnil":
            t, v = vals[st[1]]
            out.append((t is None) if kinds[st[1]] == "iface" else (v is None))
        elif op == "eq":
            out.append(pair(st[1]) == pair(st[2]))
        elif op == "type":
            t, v = vals[st[1]]
            out.append("<nil>" if t is None else t)
        elif op == "call":
            t, v = vals[st[1]]
            if t is None:
                out.append("panic")
            elif v is None:
                out.append("ok" if st[2] == "safe" else "panic")
            else:
                out.append("ok")
    return out
''',
    tests=[
        [[["nilptr", "p", "MyErr"], ["iface", "err"], ["isnil", "err"], ["assign", "err", "p"], ["isnil", "p"],
          ["isnil", "err"], ["type", "err"]]],
        [[["iface", "x"], ["type", "x"], ["call", "x", "safe"], ["call", "x", "deref"]]],
        [[["nilptr", "p", "T"], ["call", "p", "safe"], ["call", "p", "deref"], ["iface", "x"], ["assign", "x", "p"],
          ["call", "x", "safe"], ["call", "x", "deref"]]],
        [[["newptr", "p", "T"], ["iface", "x"], ["assign", "x", "p"], ["isnil", "x"], ["call", "x", "deref"],
          ["assign", "x", "nil"], ["isnil", "x"], ["type", "x"]]],
        [[["newptr", "p", "T"], ["newptr", "q", "T"], ["eq", "p", "q"], ["assign", "q", "p"], ["eq", "p", "q"]]],
        [[["nilptr", "p", "A"], ["nilptr", "q", "B"], ["iface", "x"], ["iface", "y"], ["assign", "x", "p"],
          ["assign", "y", "q"], ["eq", "x", "y"], ["isnil", "x"], ["isnil", "y"]]],
        [[["nilptr", "p", "A"], ["iface", "x"], ["iface", "y"], ["eq", "x", "y"], ["assign", "x", "p"],
          ["eq", "x", "y"], ["eq", "x", "p"], ["assign", "y", "x"], ["eq", "x", "y"]]],
        [[["newptr", "p", "T"], ["iface", "x"], ["assign", "x", "p"], ["assign", "p", "nil"], ["isnil", "p"],
          ["isnil", "x"], ["call", "x", "deref"], ["eq", "x", "p"]]],
        [[]],
        [[["newptr", "a", "T"], ["newptr", "b", "T"], ["iface", "x"], ["iface", "y"], ["assign", "x", "a"],
          ["assign", "y", "b"], ["eq", "x", "y"], ["assign", "b", "a"], ["assign", "y", "b"], ["eq", "x", "y"], ["type", "y"]]],
        [[["nilptr", "p", "bytes.Buffer"], ["iface", "w"], ["assign", "w", "p"], ["isnil", "w"], ["type", "w"],
          ["assign", "w", "nil"], ["isnil", "w"], ["call", "w", "safe"]]],
        [[["iface", "x"], ["iface", "y"], ["newptr", "p", "T"], ["assign", "x", "p"], ["assign", "y", "x"],
          ["assign", "x", "nil"], ["isnil", "y"], ["isnil", "x"], ["call", "y", "deref"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def eval_nil(stmts):
    kinds = {}; vals = {}; out = []; c = [0]
    for st in stmts:
        op = st[0]
        if op == "iface": kinds[st[1]] = "iface"; vals[st[1]] = (None, None)
        elif op == "nilptr": kinds[st[1]] = "ptr"; vals[st[1]] = ("*" + st[2], None)
        elif op == "newptr": c[0] += 1; kinds[st[1]] = "ptr"; vals[st[1]] = ("*" + st[2], c[0])
        elif op == "assign":
            d, s = st[1], st[2]
            if kinds[d] == "iface": vals[d] = (None, None) if s == "nil" else vals[s]
            else: vals[d] = (vals[d][0], None if s == "nil" else vals[s][1])
        elif op == "isnil": out.append(vals[st[1]][1] is None)
        elif op == "eq": out.append(vals[st[1]][1] == vals[st[2]][1])
        elif op == "type":
            t, v = vals[st[1]]; out.append("<nil>" if v is None else t)
        elif op == "call":
            t, v = vals[st[1]]
            out.append("ok" if v is not None or (t is not None and st[2] == "safe") else "panic")
    return out
''',
        '''def eval_nil(stmts):
    kinds = {}; vals = {}; out = []; c = [0]
    for st in stmts:
        op = st[0]
        if op == "iface": kinds[st[1]] = "iface"; vals[st[1]] = (None, None)
        elif op == "nilptr": kinds[st[1]] = "ptr"; vals[st[1]] = ("*" + st[2], None)
        elif op == "newptr": c[0] += 1; kinds[st[1]] = "ptr"; vals[st[1]] = ("*" + st[2], c[0])
        elif op == "assign":
            d, s = st[1], st[2]
            if kinds[d] == "iface": vals[d] = (None, None) if s == "nil" else vals[s]
            else: vals[d] = (vals[d][0], None if s == "nil" else vals[s][1])
        elif op == "isnil":
            t, v = vals[st[1]]; out.append((t is None) if kinds[st[1]] == "iface" else (v is None))
        elif op == "eq": out.append(vals[st[1]] == vals[st[2]])
        elif op == "type":
            t, v = vals[st[1]]; out.append("<nil>" if t is None else t)
        elif op == "call":
            t, v = vals[st[1]]
            out.append("panic" if v is None else "ok")
    return out
''',
    ],
    guide=dict(
        prereqs="Tuples. Lesson: [Interfaces, any, assertions and the nil trap](#/lesson/go/go-interfaces).",
        intuition="Picture an interface as a labelled box. An empty box with no label is nil. A box with the "
                  "label `*MyErr` and nothing inside is *not* an empty unlabelled box, so `== nil` says false, "
                  "even though what is inside is a nil pointer.",
        hints=[
            "Store every variable as a `(type, value)` tuple, even pointers.",
            "`isnil` asks a different question depending on the variable kind: interface → is the *type* empty; "
            "pointer → is the *value* empty.",
            "Copying a pointer into an interface copies the pointer's value at that moment. Later changes to the "
            "pointer variable do not reach the interface.",
        ],
        brute_force="Tracking only the value part (one slot per variable) is the natural first model. It gives "
                    "the wrong answer for the central question of the problem.",
        approach=r"""
Use tuples. Pointer variable: `("*T", id-or-None)`. Interface: `(None, None)` or a copy of a pointer's tuple.
Equality is tuple equality.

**Dry run** of the example: `p = ("*MyErr", None)`, `err = (None, None)` → `isnil err` true. `err = p` copies the
tuple: `("*MyErr", None)`. `isnil p` → value is None → true. `isnil err` → type is not None → **false**.

**The same behaviour in Go:**

```go
package main

import "fmt"

type MyErr struct{ msg string }

func (e *MyErr) Error() string { return "boom" } // "safe": never touches e.msg

func find(fail bool) error {
	var p *MyErr // nil pointer
	if fail {
		p = &MyErr{"bad"}
	}
	return p // BUG: wraps a possibly-nil *MyErr in a non-nil error
}

func main() {
	err := find(false)
	fmt.Println(err == nil)        // false
	fmt.Printf("%T %v\n", err, err) // *main.MyErr boom
}
```

The fix is to return the literal `nil` on the success path, and to declare variables as `error`, not as
a concrete pointer type.
""",
        complexity="O(n) for n statements.",
        pitfalls="Deciding `isnil` from the value for interfaces. Comparing only values in `eq` (two nil "
                 "pointers of different types are different interface values). Believing a nil receiver always "
                 "panics: a method that never dereferences it runs fine.",
    ),
),

# ------------------------------------------------------------------ go-constraint-check
dict(
    id="go-constraint-check",
    title="Does this type satisfy the constraint?",
    difficulty="Medium",
    pattern="Go generics",
    entry="satisfies",
    description=r"""
A generic Go function has **type parameters**, and each one has a **constraint**: an interface that
says which types may be plugged in. A constraint can list methods, and it can list a **type set**:

```go
type Number interface { ~int | ~float64 }   // any type whose underlying type is int or float64
type Exact  interface { int | string }      // exactly int or exactly string
```

`~int` (with the tilde) means "any type whose **underlying type** is `int`", which includes
`type Celsius int`. Plain `int` means only the type `int` itself.

Input:

- `types`: user-defined types, `name -> {"underlying": "int", "methods": ["String"]}`. Any type name
  not in this dictionary is a built-in or literal type: its underlying type is its own name and it has no methods.
- `constraints`: `name -> {"types": [terms], "methods": [names], "embeds": [constraint names]}` (keys may be missing).
- `queries`: `[type_name, constraint_name]`.

A type satisfies a constraint when **all** of these hold:

1. every constraint in `embeds` is satisfied;
2. if `types` is non-empty, at least one term matches: `"~U"` matches when the type's underlying type
   is `U`; a term without tilde matches only when it equals the type's own name;
3. every name in `methods` is one of the type's methods.

Two built-in constraints exist: `"any"` (always satisfied) and `"comparable"` (satisfied unless the
underlying type starts with `[]`, `map[` or `func`, since slices, maps and functions cannot be compared with `==`).

Return a list of booleans.

**Example:** `types = {"Celsius": {"underlying": "float64", "methods": ["String"]}}`,
`constraints = {"Number": {"types": ["~int", "~float64"]}, "Exact": {"types": ["int", "float64"]}}`

`[["Celsius","Number"], ["Celsius","Exact"], ["int","Exact"], ["string","Number"]]` → `[true, false, true, false]`
""",
    starter='''def satisfies(types, constraints, queries):
    pass
''',
    solution='''def satisfies(types, constraints, queries):
    def ok(t, c):
        info = types.get(t, {})
        under = info.get("underlying", t)
        methods = info.get("methods", [])
        if c == "any":
            return True
        if c == "comparable":
            return not (under.startswith("[]") or under.startswith("map[") or under.startswith("func"))
        d = constraints[c]
        for e in d.get("embeds", []):
            if not ok(t, e):
                return False
        terms = d.get("types", [])
        if terms:
            for term in terms:
                if term.startswith("~"):
                    if term[1:] == under:
                        break
                elif term == t:
                    break
            else:
                return False
        return all(m in methods for m in d.get("methods", []))

    return [ok(t, c) for t, c in queries]
''',
    tests=[
        [{"Celsius": {"underlying": "float64", "methods": ["String"]}},
         {"Number": {"types": ["~int", "~float64"]}, "Exact": {"types": ["int", "float64"]}},
         [["Celsius", "Number"], ["Celsius", "Exact"], ["int", "Exact"], ["string", "Number"]]],
        [{}, {}, [["int", "any"], ["[]int", "any"], ["int", "comparable"], ["[]int", "comparable"],
                  ["map[string]int", "comparable"], ["func()", "comparable"], ["string", "comparable"]]],
        [{"IDs": {"underlying": "[]int"}, "Name": {"underlying": "string"}}, {},
         [["IDs", "comparable"], ["Name", "comparable"], ["IDs", "any"]]],
        [{"Celsius": {"underlying": "float64", "methods": ["String"]}, "Plain": {"underlying": "float64"}},
         {"StringNum": {"types": ["~float64"], "methods": ["String"]}},
         [["Celsius", "StringNum"], ["Plain", "StringNum"], ["float64", "StringNum"]]],
        [{"MyInt": {"underlying": "int"}},
         {"Signed": {"types": ["~int", "~int8", "~int16", "~int32", "~int64"]},
          "Unsigned": {"types": ["~uint", "~uint8"]},
          "Integer": {"types": ["~int", "~int8", "~int16", "~int32", "~int64", "~uint", "~uint8"]},
          "Ordered": {"types": ["~int", "~uint", "~float64", "~string"]}},
         [["MyInt", "Signed"], ["MyInt", "Unsigned"], ["uint8", "Integer"], ["string", "Ordered"],
          ["bool", "Ordered"], ["int32", "Ordered"]]],
        [{"MyInt": {"underlying": "int"}}, {"OnlyMyInt": {"types": ["MyInt"]}},
         [["MyInt", "OnlyMyInt"], ["int", "OnlyMyInt"]]],
        [{"Key": {"underlying": "string", "methods": ["Hash"]}, "Bad": {"underlying": "[]byte", "methods": ["Hash"]}},
         {"Hasher": {"methods": ["Hash"]}, "MapKey": {"embeds": ["comparable", "Hasher"]}},
         [["Key", "MapKey"], ["Bad", "MapKey"], ["string", "MapKey"], ["Bad", "Hasher"]]],
        [{"T": {"underlying": "int", "methods": ["A", "B"]}},
         {"NeedsA": {"methods": ["A"]}, "NeedsAB": {"embeds": ["NeedsA"], "methods": ["B"]},
          "NeedsABC": {"embeds": ["NeedsAB"], "methods": ["C"]}, "IntAB": {"embeds": ["NeedsAB"], "types": ["~int"]},
          "StrAB": {"embeds": ["NeedsAB"], "types": ["~string"]}},
         [["T", "NeedsAB"], ["T", "NeedsABC"], ["T", "IntAB"], ["T", "StrAB"]]],
        [{}, {"Empty": {}}, [["int", "Empty"], ["[]string", "Empty"]]],
        [{"A": {"underlying": "int"}}, {"C": {"types": ["~int"]}}, []],
        [{"Seconds": {"underlying": "int64"}}, {"C1": {"types": ["~int"]}, "C2": {"types": ["int64"]}, "C3": {"types": ["~int64"]}},
         [["Seconds", "C1"], ["Seconds", "C2"], ["Seconds", "C3"], ["int64", "C2"], ["int64", "C3"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def satisfies(types, constraints, queries):
    def ok(t, c):
        info = types.get(t, {}); under = info.get("underlying", t); methods = info.get("methods", [])
        if c == "any": return True
        if c == "comparable": return not (under.startswith("[]") or under.startswith("map[") or under.startswith("func"))
        d = constraints[c]
        if not all(ok(t, e) for e in d.get("embeds", [])): return False
        terms = d.get("types", [])
        if terms and not any(term.lstrip("~") == under for term in terms): return False
        return all(m in methods for m in d.get("methods", []))
    return [ok(t, c) for t, c in queries]
''',
        '''def satisfies(types, constraints, queries):
    def ok(t, c):
        info = types.get(t, {}); under = info.get("underlying", t); methods = info.get("methods", [])
        if c == "any": return True
        if c == "comparable": return not (t.startswith("[]") or t.startswith("map[") or t.startswith("func"))
        d = constraints[c]
        terms = d.get("types", [])
        if terms and not any((term[1:] == under) if term.startswith("~") else term == t for term in terms): return False
        return all(m in methods for m in d.get("methods", []))
    return [ok(t, c) for t, c in queries]
''',
    ],
    guide=dict(
        prereqs="Lessons: [Type parameters and generic functions](#/lesson/go/go-generics-basics) and "
                "[Constraints, type sets and idiomatic generics](#/lesson/go/go-generics-constraints).",
        intuition="A constraint is a filter with up to three stacked sieves: embedded constraints, a list of "
                  "allowed type shapes, and required methods. A type gets through only if it passes every sieve.",
        hints=[
            "Look up the type first: underlying type and methods, with sensible defaults for built-ins.",
            "The tilde changes *what you compare against*: underlying type with `~`, the type's own name without.",
            "Recursion handles `embeds`; `any` and `comparable` are the base cases.",
        ],
        brute_force="Stripping the tilde and always comparing underlying types is the usual simplification. It "
                    "wrongly lets `type Celsius float64` through a constraint that says exactly `float64`.",
        approach=r"""
`ok(type, constraint)`: handle the two built-ins, then check embeds (recursively), terms, methods.

**Dry run:** `Celsius` (underlying `float64`) against `Exact = int | float64`. Terms have no tilde, so compare the
name `Celsius` with `int` and with `float64`: no match → false. Against `Number = ~int | ~float64`: compare the
underlying type `float64` with `int` (no), with `float64` (yes) → true.

**The same behaviour in Go:**

```go
package main

import "fmt"

type Number interface{ ~int | ~float64 }
type Exact interface{ int | float64 }

type Celsius float64

func Sum[T Number](xs []T) T {
	var total T
	for _, x := range xs {
		total += x
	}
	return total
}

func Double[T Exact](x T) T { return x * 2 }

func main() {
	fmt.Println(Sum([]Celsius{20.5, 1.5})) // 22: Celsius has underlying type float64
	fmt.Println(Double(21))                // 42
	// Double(Celsius(1))
	// compile error: Celsius does not satisfy Exact (possibly missing ~ for float64 in Exact)
}
```
""",
        complexity="O(size of the constraint, including embedded ones) per query.",
        pitfalls="Ignoring the tilde. Testing `comparable` on the type name instead of the underlying type. "
                 "Skipping embedded constraints. Treating an empty `types` list as 'matches nothing' (it means "
                 "'no restriction').",
    ),
),

# ------------------------------------------------------------------ go-error-chain
dict(
    id="go-error-chain",
    title="Error wrapping: Is, As, Unwrap and messages",
    difficulty="Medium",
    pattern="Go errors",
    entry="error_queries",
    description=r"""
In Go an error is an ordinary value. One error can **wrap** another to add context, forming a chain
(or, with `errors.Join`, a tree). The standard library gives three tools to inspect it:

- `errors.Unwrap(err)` returns the error directly inside, or nil;
- `errors.Is(err, target)` reports whether `target` appears anywhere in the tree (compared by identity);
- `errors.As(err, &target)` finds the first error in the tree that has a given **type**.

`errors` maps an id to `{"type": ..., "msg": ..., "wraps": ...}` where `wraps` is:

- missing or `None`: a leaf error;
- one id: created like `fmt.Errorf("msg: %w", inner)`;
- a list of ids: created by `errors.Join(a, b, ...)` (its own `msg` is ignored).

Answer each query:

| query | answer |
|---|---|
| `["msg", e]` | the text of `e.Error()`: a leaf gives its `msg`; a single wrap gives `msg + ": " + inner text`; a join gives the children's texts joined with `"\n"` |
| `["unwrap", e]` | the wrapped id for a single wrap, otherwise `None` (also `None` for a join, as in Go) |
| `["is", e, target]` | `true` if `target` is found walking the tree from `e` |
| `["as", e, type]` | the id of the first error whose `type` equals `type`, or `None` |

The walk for `is` and `as` is **depth-first, pre-order**: check the error itself, then its children
from left to right, each one completely before the next.

**Example:** `errors = {"nf": {"type":"Sentinel","msg":"not found"}, "q": {"type":"QueryError","msg":"query users","wraps":"nf"}, "h": {"type":"Wrap","msg":"handler","wraps":"q"}}`

`[["msg","h"], ["is","h","nf"], ["as","h","QueryError"], ["unwrap","h"], ["is","nf","h"]]`
→ `["handler: query users: not found", true, "q", "q", false]`
""",
    starter='''def error_queries(errors, queries):
    pass
''',
    solution='''def error_queries(errors, queries):
    def children(e):
        w = errors[e].get("wraps")
        if w is None:
            return []
        return list(w) if isinstance(w, list) else [w]

    def walk(e):
        yield e
        for c in children(e):
            yield from walk(c)

    def msg(e):
        w = errors[e].get("wraps")
        if w is None:
            return errors[e]["msg"]
        if isinstance(w, list):
            return "\\n".join(msg(c) for c in w)
        return errors[e]["msg"] + ": " + msg(w)

    out = []
    for q in queries:
        kind, e = q[0], q[1]
        if kind == "msg":
            out.append(msg(e))
        elif kind == "unwrap":
            w = errors[e].get("wraps")
            out.append(None if w is None or isinstance(w, list) else w)
        elif kind == "is":
            out.append(any(x == q[2] for x in walk(e)))
        elif kind == "as":
            out.append(next((x for x in walk(e) if errors[x]["type"] == q[2]), None))
    return out
''',
    tests=[
        [{"nf": {"type": "Sentinel", "msg": "not found"}, "q": {"type": "QueryError", "msg": "query users", "wraps": "nf"},
          "h": {"type": "Wrap", "msg": "handler", "wraps": "q"}},
         [["msg", "h"], ["is", "h", "nf"], ["as", "h", "QueryError"], ["unwrap", "h"], ["is", "nf", "h"]]],
        [{"e": {"type": "Sentinel", "msg": "eof"}}, [["msg", "e"], ["unwrap", "e"], ["is", "e", "e"], ["as", "e", "Sentinel"], ["as", "e", "Other"]]],
        [{"a": {"type": "A", "msg": "a failed"}, "b": {"type": "B", "msg": "b failed"},
          "j": {"type": "Join", "msg": "ignored", "wraps": ["a", "b"]}, "top": {"type": "Wrap", "msg": "batch", "wraps": "j"}},
         [["msg", "j"], ["msg", "top"], ["unwrap", "j"], ["unwrap", "top"], ["is", "top", "b"], ["as", "top", "B"], ["as", "top", "Join"]]],
        [{"t1": {"type": "Timeout", "msg": "db timeout"}, "t2": {"type": "Timeout", "msg": "cache timeout"},
          "w1": {"type": "Wrap", "msg": "load", "wraps": "t1"}, "j": {"type": "Join", "msg": "", "wraps": ["w1", "t2"]}},
         [["as", "j", "Timeout"], ["is", "j", "t2"], ["is", "j", "t1"], ["msg", "j"], ["as", "w1", "Timeout"]]],
        [{"t1": {"type": "Timeout", "msg": "db timeout"}, "t2": {"type": "Timeout", "msg": "cache timeout"},
          "w1": {"type": "Wrap", "msg": "load", "wraps": "t1"}, "j": {"type": "Join", "msg": "", "wraps": ["t2", "w1"]}},
         [["as", "j", "Timeout"], ["msg", "j"]]],
        [{"x": {"type": "Sentinel", "msg": "same text"}, "y": {"type": "Sentinel", "msg": "same text"},
          "w": {"type": "Wrap", "msg": "ctx", "wraps": "x"}}, [["is", "w", "x"], ["is", "w", "y"], ["msg", "w"]]],
        [{"x": {"type": "A", "msg": "x"}}, []],
        [{"e0": {"type": "Root", "msg": "m0"}, "e1": {"type": "W", "msg": "m1", "wraps": "e0"},
          "e2": {"type": "W", "msg": "m2", "wraps": "e1"}, "e3": {"type": "W", "msg": "m3", "wraps": "e2"},
          "e4": {"type": "Top", "msg": "m4", "wraps": "e3"}},
         [["msg", "e4"], ["as", "e4", "W"], ["as", "e4", "Root"], ["is", "e4", "e0"], ["is", "e2", "e3"], ["unwrap", "e1"]]],
        [{"a": {"type": "A", "msg": "a"}, "b": {"type": "B", "msg": "b"}, "c": {"type": "C", "msg": "c"},
          "j1": {"type": "Join", "msg": "", "wraps": ["a", "b"]}, "j2": {"type": "Join", "msg": "", "wraps": ["j1", "c"]},
          "top": {"type": "T", "msg": "all", "wraps": "j2"}},
         [["msg", "j2"], ["msg", "top"], ["is", "top", "c"], ["as", "top", "B"], ["as", "top", "Z"]]],
        [{"a": {"type": "A", "msg": "only"}, "j": {"type": "Join", "msg": "", "wraps": ["a"]}},
         [["msg", "j"], ["unwrap", "j"], ["is", "j", "a"], ["is", "j", "j"]]],
        [{"leaf": {"type": "PathError", "msg": "open cfg.yaml", "wraps": None},
          "w": {"type": "ConfigError", "msg": "load config", "wraps": "leaf"}},
         [["as", "w", "ConfigError"], ["as", "w", "PathError"], ["msg", "w"], ["unwrap", "leaf"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def error_queries(errors, queries):
    def msg(e):
        w = errors[e].get("wraps")
        if w is None: return errors[e]["msg"]
        if isinstance(w, list): return "\\n".join(msg(c) for c in w)
        return errors[e]["msg"] + ": " + msg(w)
    def chain(e):
        res = []
        while e is not None:
            res.append(e)
            w = errors[e].get("wraps")
            e = None if w is None or isinstance(w, list) else w
        return res
    out = []
    for q in queries:
        k, e = q[0], q[1]
        if k == "msg": out.append(msg(e))
        elif k == "unwrap":
            w = errors[e].get("wraps"); out.append(None if w is None or isinstance(w, list) else w)
        elif k == "is": out.append(q[2] in chain(e))
        elif k == "as": out.append(next((x for x in chain(e) if errors[x]["type"] == q[2]), None))
    return out
''',
        '''def error_queries(errors, queries):
    def kids(e):
        w = errors[e].get("wraps")
        return [] if w is None else (list(w) if isinstance(w, list) else [w])
    def walk(e):
        yield e
        for c in kids(e): yield from walk(c)
    def msg(e):
        w = errors[e].get("wraps")
        if w is None: return errors[e]["msg"]
        if isinstance(w, list): return "\\n".join(msg(c) for c in w)
        return errors[e]["msg"] + ": " + msg(w)
    out = []
    for q in queries:
        k, e = q[0], q[1]
        if k == "msg": out.append(msg(e))
        elif k == "unwrap":
            w = errors[e].get("wraps"); out.append(None if w is None or isinstance(w, list) else w)
        elif k == "is": out.append(any(errors[x]["msg"] == errors[q[2]]["msg"] for x in walk(e)))
        elif k == "as": out.append(next((x for x in walk(e) if errors[x]["type"] == q[2]), None))
    return out
''',
        '''def error_queries(errors, queries):
    def kids(e):
        w = errors[e].get("wraps")
        return [] if w is None else (list(w) if isinstance(w, list) else [w])
    def bfs(e):
        order = [e]; i = 0
        while i < len(order):
            order.extend(kids(order[i])); i += 1
        return order
    def msg(e):
        w = errors[e].get("wraps")
        if w is None: return errors[e]["msg"]
        if isinstance(w, list): return "\\n".join(msg(c) for c in w)
        return errors[e]["msg"] + ": " + msg(w)
    out = []
    for q in queries:
        k, e = q[0], q[1]
        if k == "msg": out.append(msg(e))
        elif k == "unwrap":
            w = errors[e].get("wraps"); out.append(None if w is None or isinstance(w, list) else w)
        elif k == "is": out.append(q[2] in bfs(e))
        elif k == "as": out.append(next((x for x in bfs(e) if errors[x]["type"] == q[2]), None))
    return out
''',
    ],
    guide=dict(
        prereqs="Trees and recursion. Lessons: [Errors are values](#/lesson/go/go-errors-values) and "
                "[errors.Is, errors.As, panic and recover](#/lesson/go/go-errors-is-as-panic).",
        intuition="Wrapping is a set of nested envelopes. `Is` asks 'is *this exact* letter somewhere inside?'. "
                  "`As` asks 'is there a letter of *this kind* inside, and hand me the first one'. Both open "
                  "envelopes in the same order: outside first, then each inner envelope fully, left to right.",
        hints=[
            "Write one generator `walk(e)` that yields ids in pre-order; `is` and `as` are one-liners on top of it.",
            "`is` compares ids (identity), never message text.",
            "`unwrap` on a join returns `None` even though the join has children.",
        ],
        brute_force="Following only single `wraps` links with a `while` loop handles chains but silently stops "
                    "at the first `errors.Join`, so anything inside a join is never found.",
        approach=r"""
Recursive pre-order walk plus a recursive message builder.

**Dry run:** `j = Join(w1, t2)` where `w1` wraps `t1`. Walk order: `j, w1, t1, t2`. `as j Timeout` → `t1` (found
inside `w1` before `t2` is visited). Swap the join's children and the answer becomes `t2`.

**The same behaviour in Go:**

```go
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("not found") // sentinel: compared by identity

type QueryError struct {
	Table string
	Err   error
}

func (q *QueryError) Error() string { return "query " + q.Table + ": " + q.Err.Error() }
func (q *QueryError) Unwrap() error { return q.Err }

func main() {
	err := fmt.Errorf("handler: %w", &QueryError{"users", ErrNotFound})
	fmt.Println(err)                         // handler: query users: not found
	fmt.Println(errors.Is(err, ErrNotFound)) // true

	var qe *QueryError
	if errors.As(err, &qe) {
		fmt.Println(qe.Table) // users
	}
	both := errors.Join(err, errors.New("also failed"))
	fmt.Println(errors.Unwrap(both) == nil) // true: Join exposes Unwrap() []error instead
}
```
""",
        complexity="O(size of the error tree) per query.",
        pitfalls="Comparing message text for `Is`. Stopping at joins. Breadth-first order for `As`. Returning "
                 "the first child for `unwrap` of a join.",
    ),
),

# ------------------------------------------------------------------ go-import-path-version
dict(
    id="go-import-path-version",
    title="Semantic versions and import paths",
    difficulty="Easy",
    pattern="Go modules",
    entry="release",
    description=r"""
Go modules use **semantic versioning**: a version is `vMAJOR.MINOR.PATCH`, for example `v1.4.2`.

- PATCH goes up for bug fixes.
- MINOR goes up for new features that do not break existing users (PATCH resets to 0).
- MAJOR goes up for breaking changes (MINOR and PATCH reset to 0).

Go adds one rule of its own, **semantic import versioning**: from major version 2 on, the major
version is part of the module path. `example.com/lib` at `v2.x.y` must be imported as
`example.com/lib/v2`. Versions `v0` and `v1` use the plain path. Major version 0 means "still
unstable", so by convention a breaking change there only bumps MINOR.

Write `release(base, version, changes)`:

- If `version` is not exactly `v<number>.<number>.<number>` (digits only, no leading zeros except the
  single digit `0`), return `"invalid"`.
- Apply each change in order:
  - `"fix"` → PATCH + 1
  - `"feature"` → MINOR + 1, PATCH = 0
  - `"breaking"` → if MAJOR is 0: MINOR + 1, PATCH = 0; otherwise MAJOR + 1, MINOR = 0, PATCH = 0
  - `"stable"` → if MAJOR is 0: the version becomes `v1.0.0`; otherwise nothing changes
- Return `[new_version, import_path]` where the path is `base` for major 0 or 1 and `base + "/vN"` for major `N >= 2`.

**Example 1:** `release("example.com/lib", "v1.4.2", ["fix"])` → `["v1.4.3", "example.com/lib"]`

**Example 2:** `release("example.com/lib", "v1.4.2", ["breaking", "feature"])` → `["v2.1.0", "example.com/lib/v2"]`

**Example 3:** `release("example.com/lib", "1.4.2", [])` → `"invalid"`
""",
    starter='''def release(base, version, changes):
    pass
''',
    solution='''import re

def release(base, version, changes):
    m = re.fullmatch(r"v(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)", version)
    if not m:
        return "invalid"
    major, minor, patch = (int(g) for g in m.groups())
    for c in changes:
        if c == "fix":
            patch += 1
        elif c == "feature":
            minor, patch = minor + 1, 0
        elif c == "breaking":
            if major == 0:
                minor, patch = minor + 1, 0
            else:
                major, minor, patch = major + 1, 0, 0
        elif c == "stable":
            if major == 0:
                major, minor, patch = 1, 0, 0
    path = base if major < 2 else "%s/v%d" % (base, major)
    return ["v%d.%d.%d" % (major, minor, patch), path]
''',
    tests=[
        ["example.com/lib", "v1.4.2", ["fix"]],
        ["example.com/lib", "v1.4.2", ["breaking", "feature"]],
        ["example.com/lib", "1.4.2", []],
        ["example.com/lib", "v0.3.9", ["breaking"]],
        ["example.com/lib", "v0.3.9", ["stable", "breaking"]],
        ["example.com/lib", "v2.0.0", []],
        ["example.com/lib", "v1.9.9", ["feature", "fix", "fix"]],
        ["github.com/acme/db", "v9.9.9", ["breaking"]],
        ["github.com/acme/db", "v1.2", ["fix"]],
        ["github.com/acme/db", "v01.2.3", ["fix"]],
        ["github.com/acme/db", "v1.2.3-beta", []],
        ["github.com/acme/db", "v0.0.0", []],
        ["github.com/acme/db", "v3.1.4", ["stable", "fix", "breaking", "breaking", "feature"]],
        ["m", "v1.0.0", ["breaking"] * 12],
        ["m", "v1.2.x", []],
    ],
    examples=3,
    wrong_solutions=[
        '''def release(base, version, changes):
    if not version.startswith("v") or version.count(".") != 2:
        return "invalid"
    try:
        major, minor, patch = (int(x) for x in version[1:].split("."))
    except ValueError:
        return "invalid"
    for c in changes:
        if c == "fix": patch += 1
        elif c == "feature": minor, patch = minor + 1, 0
        elif c == "breaking": major, minor, patch = major + 1, 0, 0
        elif c == "stable" and major == 0: major, minor, patch = 1, 0, 0
    return ["v%d.%d.%d" % (major, minor, patch), base if major < 2 else "%s/v%d" % (base, major)]
''',
        '''import re
def release(base, version, changes):
    m = re.fullmatch(r"v(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)", version)
    if not m: return "invalid"
    major, minor, patch = (int(g) for g in m.groups())
    for c in changes:
        if c == "fix": patch += 1
        elif c == "feature": minor += 1
        elif c == "breaking":
            if major == 0: minor += 1
            else: major += 1
        elif c == "stable" and major == 0: major, minor, patch = 1, 0, 0
    return ["v%d.%d.%d" % (major, minor, patch), base if major < 1 else "%s/v%d" % (base, major)]
''',
    ],
    guide=dict(
        prereqs="String parsing. Lesson: [Modules, versions and minimal version selection](#/lesson/go/go-modules-versioning).",
        intuition="Three counters with a reset rule (bumping one zeroes everything to its right), plus one "
                  "formatting rule for the path. The path rule exists so that `lib` v1 and `lib/v2` can both be "
                  "in the same program: to Go they are different modules.",
        hints=[
            "Validate with a regular expression or by splitting on dots and checking each piece.",
            "Handle major 0 as a special case for both `breaking` and `stable`.",
            "Only majors 2 and above get the `/vN` suffix.",
        ],
        brute_force="Not applicable: the task is direct simulation.",
        approach=r"""
Parse → loop over changes → format.

**Dry run** of example 2: `v1.4.2` + `breaking` → `v2.0.0`; + `feature` → `v2.1.0`. Major is 2, so the path is
`example.com/lib/v2`.

**What this looks like in a Go project:**

```go
// go.mod of the library after the breaking release
module example.com/lib/v2

go 1.22
```

```go
// a program that uses both major versions at once
package main

import (
	"fmt"

	lib "example.com/lib"      // v1.x
	libv2 "example.com/lib/v2" // v2.x: a different import path, so a different module
)

func main() {
	fmt.Println(lib.Version(), libv2.Version())
}
```

The tag pushed to the repository is `v2.1.0`; the path inside `go.mod` and in every `import` ends in `/v2`.
""",
        complexity="O(len(changes)).",
        pitfalls="Bumping MAJOR for a breaking change in `v0`. Forgetting the resets. Adding `/v1`. Accepting "
                 "versions without the leading `v`, with only two parts, or with leading zeros.",
    ),
),

# ------------------------------------------------------------------ go-mvs
dict(
    id="go-mvs",
    title="Minimal version selection",
    difficulty="Medium",
    pattern="Go modules",
    entry="build_list",
    description=r"""
When several parts of a Go program ask for different versions of the same dependency, Go must pick
one. Its algorithm is called **minimal version selection (MVS)**:

> For every module, use the **highest version that anybody in the dependency graph asks for**, and
> nothing newer than that.

It is "minimal" because Go never jumps to the latest published release on its own; it only goes as
high as some `go.mod` file explicitly requires.

Input:

- `root_reqs`: the requirements of the main module, e.g. `["a@v1.2.0", "b@v1.0.0"]`;
- `graph`: for each `module@version`, the list of requirements written in *its* `go.mod`
  (missing key = no requirements).

Algorithm: starting from `root_reqs`, visit every `module@version` reachable by following
requirements (including versions that end up not being selected). For each module name keep the
highest version seen. Versions are `vMAJOR.MINOR.PATCH` and compare **numerically** part by part
(`v1.10.0` is higher than `v1.9.0`).

Return the selected `module@version` strings sorted alphabetically (plain string sort).

**Example:** `root_reqs = ["a@v1.2.0", "b@v1.0.0"]`,
`graph = {"a@v1.2.0": ["c@v1.1.0"], "b@v1.0.0": ["c@v1.3.0"], "c@v1.3.0": ["d@v0.9.0"]}`
→ `["a@v1.2.0", "b@v1.0.0", "c@v1.3.0", "d@v0.9.0"]`
""",
    starter='''def build_list(root_reqs, graph):
    pass
''',
    solution='''def build_list(root_reqs, graph):
    def key(v):
        return tuple(int(x) for x in v[1:].split("."))

    best = {}
    seen = set()
    stack = list(root_reqs)
    while stack:
        mv = stack.pop()
        if mv in seen:
            continue
        seen.add(mv)
        mod, ver = mv.rsplit("@", 1)
        if mod not in best or key(ver) > key(best[mod]):
            best[mod] = ver
        stack.extend(graph.get(mv, []))
    return sorted("%s@%s" % (m, v) for m, v in best.items())
''',
    tests=[
        [["a@v1.2.0", "b@v1.0.0"], {"a@v1.2.0": ["c@v1.1.0"], "b@v1.0.0": ["c@v1.3.0"], "c@v1.3.0": ["d@v0.9.0"]}],
        [[], {}],
        [["a@v1.0.0"], {}],
        [["a@v1.9.0", "b@v1.0.0"], {"b@v1.0.0": ["a@v1.10.0"]}],
        [["a@v1.0.0"], {"a@v1.0.0": ["b@v1.1.0"], "old@v0.1.0": ["b@v1.5.0", "unused@v1.0.0"]}],
        [["a@v1.0.0", "a@v1.0.1"], {"a@v1.0.0": ["x@v1.0.0"], "a@v1.0.1": []}],
        [["a@v1.0.0"], {"a@v1.0.0": ["b@v1.0.0"], "b@v1.0.0": ["c@v1.0.0"], "c@v1.0.0": ["a@v1.1.0"], "a@v1.1.0": ["b@v1.0.0"]}],
        [["app/db@v2.3.4", "app/log@v0.1.0"], {"app/db@v2.3.4": ["app/log@v0.2.0", "app/pool@v1.0.0"],
          "app/log@v0.2.0": ["app/fmt@v1.0.0"], "app/pool@v1.0.0": ["app/log@v0.1.5"], "app/log@v0.1.5": ["app/fmt@v1.2.0"]}],
        [["lib@v1.2.3", "lib/v2@v2.0.1"], {"lib/v2@v2.0.1": ["lib@v1.5.0"]}],
        [["a@v0.0.9", "b@v1.0.0"], {"b@v1.0.0": ["a@v0.0.10"], "a@v0.0.10": ["c@v10.0.0"], "a@v0.0.9": ["c@v9.99.99"]}],
        [["a@v1.0.0", "b@v1.0.0", "c@v1.0.0"], {"a@v1.0.0": ["d@v1.1.0"], "b@v1.0.0": ["d@v1.2.0"], "c@v1.0.0": ["d@v1.0.5"],
          "d@v1.0.5": ["e@v3.0.0"], "d@v1.1.0": ["e@v1.0.0"], "d@v1.2.0": ["e@v2.0.0"]}],
        [["m0@v1.0.0"], {("m%d@v1.0.0" % i): ["m%d@v1.0.0" % (i + 1), "m%d@v1.%d.0" % (i + 1, i)] for i in range(40)}],
    ],
    examples=1,
    wrong_solutions=[
        '''def build_list(root_reqs, graph):
    best = {}; seen = set(); stack = list(root_reqs)
    while stack:
        mv = stack.pop()
        if mv in seen: continue
        seen.add(mv)
        mod, ver = mv.rsplit("@", 1)
        if mod not in best or ver > best[mod]:
            best[mod] = ver
        stack.extend(graph.get(mv, []))
    return sorted("%s@%s" % (m, v) for m, v in best.items())
''',
        '''def build_list(root_reqs, graph):
    key = lambda v: tuple(int(x) for x in v[1:].split("."))
    best = {}
    def visit(mv):
        mod, ver = mv.rsplit("@", 1)
        if mod in best:
            return
        best[mod] = ver
        for d in graph.get(mv, []):
            visit(d)
    for r in root_reqs:
        visit(r)
    return sorted("%s@%s" % (m, v) for m, v in best.items())
''',
        '''def build_list(root_reqs, graph):
    key = lambda v: tuple(int(x) for x in v[1:].split("."))
    best = {}
    for mv in list(root_reqs) + [d for ds in graph.values() for d in ds]:
        mod, ver = mv.rsplit("@", 1)
        if mod not in best or key(ver) > key(best[mod]):
            best[mod] = ver
    return sorted("%s@%s" % (m, v) for m, v in best.items())
''',
    ],
    guide=dict(
        prereqs="Graph traversal. Lesson: [Modules, versions and minimal version selection](#/lesson/go/go-modules-versioning).",
        intuition="Every `go.mod` line is a vote that says 'at least this version'. Collect all the votes you "
                  "can reach from the main module, then for each module honour the largest 'at least'. No "
                  "solver, no backtracking: a graph walk and a max.",
        hints=[
            "Traverse `module@version` nodes with a stack and a `seen` set (the graph can contain cycles).",
            "Turn `v1.10.0` into the tuple `(1, 10, 0)` before comparing.",
            "Visit a node even if a higher version of the same module was already seen: its requirements still count.",
        ],
        brute_force="Taking the max over *every* requirement in the whole graph dictionary ignores "
                    "reachability and can select modules the program never depends on.",
        approach=r"""
Depth-first search from the root requirements. For each visited node update `best[module]` with a numeric
comparison and push the node's requirements.

**Dry run** of the example: visit `a@v1.2.0` → best a=1.2.0, push `c@v1.1.0`. Visit `c@v1.1.0` → c=1.1.0.
Visit `b@v1.0.0` → push `c@v1.3.0`. Visit `c@v1.3.0` → c=1.3.0, push `d@v0.9.0`. Visit it → d=0.9.0.

**What the go command shows for the same idea:**

```go
// go.mod of the main module
module example.com/app

go 1.22

require (
	example.com/a v1.2.0
	example.com/b v1.0.0
	example.com/c v1.3.0 // indirect
	example.com/d v0.9.0 // indirect
)
```

```text
$ go list -m all          # the build list chosen by MVS
example.com/app
example.com/a v1.2.0
example.com/b v1.0.0
example.com/c v1.3.0
example.com/d v0.9.0
$ go mod graph            # the edges the algorithm walks
$ go mod why -m example.com/d
```
""",
        complexity="O(V + E) over reachable `module@version` nodes and requirement edges.",
        pitfalls="Comparing versions as strings. Stopping at the first version seen for a module. Not guarding "
                 "against cycles. Note that `lib` and `lib/v2` are different module names, so both can be selected.",
        follow_up="Real Go prunes the graph (since Go 1.17 `go.mod` lists indirect dependencies so that most "
                  "of the graph need not be loaded) and honours `replace` and `exclude` directives.",
    ),
),

# ------------------------------------------------------------------ go-build-constraint
dict(
    id="go-build-constraint",
    title="Build constraints: is this file compiled?",
    difficulty="Medium",
    pattern="Go tooling",
    entry="file_included",
    description=r"""
Go decides per file whether to compile it for the target platform. `GOOS` names the operating
system (`linux`, `windows`, `darwin` for macOS, ...) and `GOARCH` the processor architecture
(`amd64`, `arm64`, ...). Two mechanisms filter files.

**1. File name suffixes.** Remove the `.go` extension, then a trailing `_test` if present. If the
name contains no underscore, there is no constraint. Otherwise drop everything before the first
underscore, split the rest on `_`, and look at the last pieces:

- if the last two pieces are a known OS followed by a known architecture, both must match;
- else if the last piece is a known OS, it must equal `GOOS`;
- else if the last piece is a known architecture, it must equal `GOARCH`;
- otherwise there is no constraint.

Known OS names: `linux`, `windows`, `darwin`, `freebsd`, `android`, `ios`, `js`, `wasip1`.
Known architectures: `amd64`, `arm64`, `386`, `arm`, `wasm`, `riscv64`.

**2. A `//go:build` line.** `expr` is the expression after `//go:build`, or `None` if the file has
none. It is built from tags, `!` (not), `&&` (and), `||` (or) and parentheses, with the usual
precedence: `!` binds tightest, then `&&`, then `||`. A tag is true when it is:

- equal to `goos` or `goarch`;
- `"unix"` and `goos` is one of `linux`, `darwin`, `freebsd`, `android`, `ios`;
- one of the extra `tags` (as given with `go build -tags`).

Write `file_included(filename, expr, goos, goarch, tags)` returning `true` only if **both**
mechanisms accept the file.

**Example 1:** `file_included("net_linux.go", None, "linux", "amd64", [])` → `true`

**Example 2:** `file_included("net_linux.go", None, "windows", "amd64", [])` → `false`

**Example 3:** `file_included("fast.go", "(linux || darwin) && !purego", "darwin", "arm64", ["purego"])` → `false`
""",
    starter='''def file_included(filename, expr, goos, goarch, tags):
    pass
''',
    solution='''import re

KNOWN_OS = {"linux", "windows", "darwin", "freebsd", "android", "ios", "js", "wasip1"}
KNOWN_ARCH = {"amd64", "arm64", "386", "arm", "wasm", "riscv64"}
UNIX = {"linux", "darwin", "freebsd", "android", "ios"}


def file_included(filename, expr, goos, goarch, tags):
    name = filename[:-3] if filename.endswith(".go") else filename
    if name.endswith("_test"):
        name = name[:-5]
    if "_" in name:
        parts = name.split("_")[1:]
        n = len(parts)
        if n >= 2 and parts[-2] in KNOWN_OS and parts[-1] in KNOWN_ARCH:
            if parts[-2] != goos or parts[-1] != goarch:
                return False
        elif parts[-1] in KNOWN_OS:
            if parts[-1] != goos:
                return False
        elif parts[-1] in KNOWN_ARCH:
            if parts[-1] != goarch:
                return False
    if expr is None:
        return True

    true_tags = set(tags) | {goos, goarch}
    if goos in UNIX:
        true_tags.add("unix")
    toks = re.findall(r"[(]|[)]|&&|[|][|]|!|[A-Za-z0-9_.]+", expr)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        pos[0] += 1
        return toks[pos[0] - 1]

    def parse_or():
        v = parse_and()
        while peek() == "||":
            take()
            r = parse_and()
            v = v or r
        return v

    def parse_and():
        v = parse_not()
        while peek() == "&&":
            take()
            r = parse_not()
            v = v and r
        return v

    def parse_not():
        if peek() == "!":
            take()
            return not parse_not()
        if peek() == "(":
            take()
            v = parse_or()
            take()
            return v
        return take() in true_tags

    return parse_or()
''',
    tests=[
        ["net_linux.go", None, "linux", "amd64", []],
        ["net_linux.go", None, "windows", "amd64", []],
        ["fast.go", "(linux || darwin) && !purego", "darwin", "arm64", ["purego"]],
        ["fast.go", "(linux || darwin) && !purego", "darwin", "arm64", []],
        ["main.go", None, "linux", "amd64", []],
        ["linux.go", None, "windows", "amd64", []],
        ["sys_windows_arm64.go", None, "windows", "arm64", []],
        ["sys_windows_arm64.go", None, "windows", "amd64", []],
        ["sys_windows_arm64_test.go", None, "linux", "arm64", []],
        ["mem_arm64.go", None, "darwin", "arm64", []],
        ["mem_arm64.go", None, "darwin", "amd64", []],
        ["my_linux_helper.go", None, "windows", "amd64", []],
        ["x.go", "unix", "freebsd", "amd64", []],
        ["x.go", "unix", "windows", "amd64", []],
        ["x.go", "linux || windows && arm64", "linux", "amd64", []],
        ["x.go", "(linux || windows) && arm64", "linux", "amd64", []],
        ["x.go", "!windows && !(darwin && amd64)", "darwin", "amd64", []],
        ["x.go", "!!integration", "linux", "amd64", ["integration"]],
        ["db_linux.go", "integration && !race", "linux", "amd64", ["integration"]],
        ["db_linux.go", "integration", "darwin", "amd64", ["integration"]],
        ["a_b_js_wasm.go", "go1.21 || tinygo", "js", "wasm", ["go1.21"]],
        ["x.go", "a || b && c || d", "linux", "amd64", ["c", "b"]],
        ["x.go", "!a && b || a && !b", "linux", "amd64", ["a", "b"]],
    ],
    examples=3,
    wrong_solutions=[
        '''import re
def file_included(filename, expr, goos, goarch, tags):
    OS = {"linux", "windows", "darwin", "freebsd", "android", "ios", "js", "wasip1"}
    AR = {"amd64", "arm64", "386", "arm", "wasm", "riscv64"}
    name = filename[:-3]
    if name.endswith("_test"): name = name[:-5]
    for part in name.split("_"):
        if part in OS and part != goos: return False
        if part in AR and part != goarch: return False
    if expr is None: return True
    t = set(tags) | {goos, goarch}
    if goos in {"linux", "darwin", "freebsd", "android", "ios"}: t.add("unix")
    py = re.sub(r"[A-Za-z0-9_.]+", lambda m: str(m.group(0) in t), expr)
    py = py.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    return eval(py)
''',
        '''import re
def file_included(filename, expr, goos, goarch, tags):
    OS = {"linux", "windows", "darwin", "freebsd", "android", "ios", "js", "wasip1"}
    AR = {"amd64", "arm64", "386", "arm", "wasm", "riscv64"}
    name = filename[:-3]
    if name.endswith("_test"): name = name[:-5]
    if "_" in name:
        p = name.split("_")[1:]
        if len(p) >= 2 and p[-2] in OS and p[-1] in AR:
            if p[-2] != goos or p[-1] != goarch: return False
        elif p[-1] in OS:
            if p[-1] != goos: return False
        elif p[-1] in AR:
            if p[-1] != goarch: return False
    if expr is None: return True
    t = set(tags) | {goos, goarch}
    toks = re.findall(r"[(]|[)]|&&|[|][|]|!|[A-Za-z0-9_.]+", expr)
    val = None; op = None; neg = False
    for tk in toks:
        if tk in ("(", ")"): continue
        if tk == "!": neg = not neg; continue
        if tk in ("&&", "||"): op = tk; continue
        v = (tk in t) != neg; neg = False
        val = v if val is None else (val and v if op == "&&" else val or v)
    return val
''',
    ],
    guide=dict(
        prereqs="Recursive-descent parsing of boolean expressions. Lesson: "
                "[embed, go generate and cross-compilation](#/lesson/go/go-embed-generate-cross).",
        intuition="Two independent gates in a row. The file-name gate is a small table lookup on the last one "
                  "or two underscore-separated words. The `//go:build` gate is a boolean formula where each "
                  "variable is 'is this tag switched on?'.",
        hints=[
            "Strip `.go`, then `_test`, then ignore everything before the first underscore.",
            "Check the two-piece OS_ARCH form before the one-piece forms.",
            "Write three mutually recursive functions: `or` calls `and`, `and` calls `not`, `not` handles `!`, "
            "parentheses and a single tag.",
        ],
        brute_force="Rewriting the expression into Python (`&&` → `and`, ...) and calling `eval` works for the "
                    "expression part but is unsafe on untrusted input; and scanning *every* underscore piece for "
                    "an OS name wrongly excludes files such as `my_linux_helper.go`.",
        approach=r"""
Name gate first, then tokenise the expression with one regular expression and parse:

```
or   := and ( "||" and )*
and  := not ( "&&" not )*
not  := "!" not | "(" or ")" | TAG
```

**Dry run:** `linux || windows && arm64` on linux/amd64. `and` binds tighter, so it is `linux || (windows && arm64)`
= `true || (false && false)` = true. With explicit parentheses `(linux || windows) && arm64` = `true && false` = false.

**What this looks like in Go source:**

```go
//go:build (linux || darwin) && !purego

// Package fastsum picks an optimised implementation on Unix-like systems
// unless the build is run with:  go build -tags purego
package fastsum

func Sum(b []byte) uint32 { return sumAsm(b) }
```

```text
$ GOOS=windows GOARCH=arm64 go build ./...   # cross-compile: this file is skipped
$ go list -f '{{.GoFiles}} ignored: {{.IgnoredGoFiles}}' ./fastsum
```
""",
        complexity="O(length of the file name + number of tokens).",
        pitfalls="Treating a file called `linux.go` as constrained (no underscore, so it is not). Forgetting "
                 "`_test`. Wrong precedence between `&&` and `||`. Forgetting the implied `unix` tag.",
    ),
),

# ------------------------------------------------------------------ go-struct-tag-parse
dict(
    id="go-struct-tag-parse",
    title="Parse a struct tag like reflect.StructTag",
    difficulty="Medium",
    pattern="Go reflection",
    entry="tag_lookup",
    description=r"""
A Go struct field can carry a **tag**: a string of metadata that libraries read at run time through
reflection. By convention the tag is a list of `key:"value"` pairs separated by spaces:

```go
type User struct {
    Name string `json:"name,omitempty" db:"user_name"`
}
```

Write `tag_lookup(tag, keys)` which behaves like calling `reflect.StructTag(tag).Lookup(key)` for
each key: return a list of `[value, found]` pairs (`["", false]` when the key is not found).

Parse from left to right, repeating:

1. Skip spaces. If the string is finished, stop.
2. Read the **key**: the longest run of characters that are not a space, not `:`, not `"` and not a
   control character (code below 32 or equal to 127).
3. The key must be non-empty and be followed immediately by `:"`. If not, **stop parsing** (everything
   from here on is ignored; pairs found earlier still count).
4. Read the **value** up to the next unescaped `"`. Inside the value a backslash escapes the next
   character. If the closing quote is missing, stop parsing.
5. Unescape the value: `\"` becomes `"`, `\\` becomes `\`, `\n` a newline, `\t` a tab; any other
   escaped character stands for itself.

If a key appears twice, the **first** one wins.

**Example 1:** tag `json:"name,omitempty" db:"user_name"`, keys `["db", "json", "xml"]`
→ `[["user_name", true], ["name,omitempty", true], ["", false]]`

**Example 2:** tag `json: "name"` (space after the colon), keys `["json"]` → `[["", false]]`
""",
    starter='''def tag_lookup(tag, keys):
    pass
''',
    solution='''def tag_lookup(tag, keys):
    found = {}
    i, n = 0, len(tag)
    while i < n:
        while i < n and tag[i] == " ":
            i += 1
        if i >= n:
            break
        j = i
        while j < n and tag[j] > " " and tag[j] not in ':"' and tag[j] != "\\x7f":
            j += 1
        if j == i or j + 1 >= n or tag[j] != ":" or tag[j + 1] != '"':
            break
        name = tag[i:j]
        k = j + 2
        buf = []
        closed = False
        while k < n:
            ch = tag[k]
            if ch == '"':
                closed = True
                break
            if ch == "\\\\":
                k += 1
                if k >= n:
                    break
                esc = tag[k]
                buf.append({"n": "\\n", "t": "\\t"}.get(esc, esc))
            else:
                buf.append(ch)
            k += 1
        if not closed:
            break
        if name not in found:
            found[name] = "".join(buf)
        i = k + 1
    return [[found[k], True] if k in found else ["", False] for k in keys]
''',
    tests=[
        ['json:"name,omitempty" db:"user_name"', ["db", "json", "xml"]],
        ['json: "name"', ["json"]],
        ["", ["json"]],
        ['json:"id"', []],
        ['   json:"id"    yaml:"ident"  ', ["json", "yaml"]],
        ['json:"a" json:"b"', ["json"]],
        ['json:"" db:"x"', ["json", "db"]],
        ['json:"say \\"hi\\"" db:"c:\\\\tmp"', ["json", "db"]],
        ['a:"1" broken b:"2"', ["a", "b"]],
        ['a:"1" b:"unterminated', ["a", "b"]],
        ['a:"1" :"nokey" c:"3"', ["a", "c"]],
        ['validate:"min=1,max=10" json:"n"', ["validate", "json", "min"]],
        ['a:"x y z" b:"p:q"', ["a", "b"]],
        ['json:"name"db:"col"', ["json", "db"]],
        ['k:"line\\nbreak\\tand\\qother"', ["k"]],
        ['a:"1"\tb:"2"', ["a", "b"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def tag_lookup(tag, keys):
    found = {}
    for part in tag.split():
        if ':"' in part and part.endswith('"'):
            k, v = part.split(":", 1)
            found.setdefault(k, v[1:-1])
    return [[found[k], True] if k in found else ["", False] for k in keys]
''',
        '''import re
def tag_lookup(tag, keys):
    found = {}
    for k, v in re.findall(r'([^\\s:"]+):"((?:[^"\\\\]|\\\\.)*)"', tag):
        if k not in found:
            found[k] = re.sub(r"\\\\(.)", lambda m: {"n": "\\n", "t": "\\t"}.get(m.group(1), m.group(1)), v)
    return [[found[k], True] if k in found else ["", False] for k in keys]
''',
    ],
    guide=dict(
        prereqs="Character-by-character string scanning. Lesson: [Reflection](#/lesson/go/go-reflection).",
        intuition="It is a tiny hand-written scanner with one index walking the string. The important design "
                  "decision in Go's version is that it does not try to recover: the first malformed pair ends "
                  "the scan, which is why a stray space after the colon makes a tag silently useless.",
        hints=[
            "Use a `while` loop with an index, not `split()`: values may contain spaces.",
            "After the key, test the two characters `:` and `\"` together before going on.",
            "When you see a backslash inside the value, consume the next character unconditionally.",
        ],
        brute_force="`tag.split()` followed by `split(':')` passes the simplest case and fails on values with "
                    "spaces, escaped quotes, pairs with no space between them, and the stop-at-first-error rule.",
        approach=r"""
Loop: skip spaces → scan key → require `:"` → scan value with escapes → store if the key is new → continue
after the closing quote.

**Dry run:** `a:"1" broken b:"2"`. Pair `a` = `1`. Skip the space. Key scan reads `broken` and stops at the space;
the next characters are not `:"`, so parsing stops. `b` is never seen: answer `[["1", true], ["", false]]`.

**The same behaviour in Go:**

```go
package main

import (
	"fmt"
	"reflect"
)

type User struct {
	Name  string `json:"name,omitempty" db:"user_name"`
	Email string `json: "email"` // BUG: space after the colon
}

func main() {
	t := reflect.TypeOf(User{})
	f, _ := t.FieldByName("Name")
	fmt.Println(f.Tag.Get("db")) // user_name
	v, ok := f.Tag.Lookup("xml")
	fmt.Printf("%q %v\n", v, ok) // "" false

	g, _ := t.FieldByName("Email")
	v, ok = g.Tag.Lookup("json")
	fmt.Printf("%q %v\n", v, ok) // "" false   (go vet reports this tag as malformed)
}
```
""",
        complexity="O(length of the tag) to parse, O(1) per key afterwards.",
        pitfalls="Splitting on spaces. Continuing after a malformed pair. Letting the last duplicate win. "
                 "Treating `\\\"` as the end of the value.",
    ),
),
]
