"""Java track, model problems part 2: overloading, dispatch, initialisation, access, interfaces, objects."""


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls, follow_up=None):
    d = dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute, approach=approach,
             complexity=complexity, pitfalls=pitfalls)
    if follow_up:
        d["follow_up"] = follow_up
    return d


PROBLEMS = [
# ------------------------------------------------------------------ java-overload-resolution
dict(
    id="java-overload-resolution",
    title="Which overload is called?",
    difficulty="Medium",
    pattern="Java methods",
    entry="resolve",
    description=r"""
A class has several one-parameter methods named `m`. Given the **declared type** of the argument (a
primitive), decide which one the compiler picks. Java tries three phases and stops at the first that
finds a candidate.

**Phase 1: no boxing.** A parameter type applies if it is the argument type or reachable by **primitive
widening**:

`byte → short → int → long → float → double` and `char → int → long → float → double`.

Pick the applicable type that is **nearest** along that chain.

**Phase 2: boxing.** Box the argument to its wrapper (`byte`→`Byte`, `short`→`Short`, `char`→`Character`,
`int`→`Integer`, `long`→`Long`, `float`→`Float`, `double`→`Double`). A parameter type applies if it is that
wrapper or one of its supertypes. Numeric wrappers: `wrapper → Number → Object`. `Character → Object`.
Pick the nearest.

**Phase 3: varargs.** A parameter written `"T..."` (for a primitive `T`) applies if the argument type is `T`
or widens to `T`. Pick the nearest `T`.

Write `resolve(overloads, arg)`: `overloads` is a list of parameter types (strings such as `"long"`,
`"Integer"`, `"Object"`, `"int..."`), `arg` a primitive type name. Return the chosen parameter type, or
`"compile error"` if nothing applies.

**Examples** `resolve(["long", "Integer"], "int")` → `"long"`; `resolve(["Object", "int..."], "int")` → `"Object"`;
`resolve(["Long"], "int")` → `"compile error"`.
""",
    starter='''def resolve(overloads, arg):
    pass
''',
    solution='''def resolve(overloads, arg):
    order = ["byte", "short", "int", "long", "float", "double"]

    def widenings(t):
        if t == "char":
            return ["char", "int", "long", "float", "double"]
        return order[order.index(t):]

    chain = widenings(arg)
    for t in chain:
        if t in overloads:
            return t
    wrapper = {"byte": "Byte", "short": "Short", "char": "Character", "int": "Integer",
               "long": "Long", "float": "Float", "double": "Double"}[arg]
    refs = [wrapper, "Object"] if arg == "char" else [wrapper, "Number", "Object"]
    for t in refs:
        if t in overloads:
            return t
    for t in chain:
        if t + "..." in overloads:
            return t + "..."
    return "compile error"
''',
    tests=[
        [["long", "Integer"], "int"],
        [["Object", "int..."], "int"],
        [["Long"], "int"],
        [["int", "long", "double"], "byte"],
        [["int", "long", "double"], "char"],
        [["short", "long"], "char"],
        [["double", "Float"], "float"],
        [["Number", "Object"], "double"],
        [["Number", "Object"], "char"],
        [["long...", "double..."], "int"],
        [["int...", "Integer", "Object"], "int"],
        [["byte", "short"], "int"],
        [["Character", "int..."], "char"],
        [["float", "Long", "long..."], "long"],
        [[], "int"],
        [["char", "int"], "short"],
        [["char", "long"], "byte"],
    ],
    wrong_solutions=[
        '''def resolve(overloads, arg):
    wrapper = {"byte": "Byte", "short": "Short", "char": "Character", "int": "Integer",
               "long": "Long", "float": "Float", "double": "Double"}[arg]
    if arg in overloads: return arg
    if wrapper in overloads: return wrapper
    order = ["byte", "short", "int", "long", "float", "double"]
    chain = ["char", "int", "long", "float", "double"] if arg == "char" else order[order.index(arg):]
    for t in chain:
        if t in overloads: return t
    for t in ["Number", "Object"]:
        if t in overloads: return t
    for t in chain:
        if t + "..." in overloads: return t + "..."
    return "compile error"
''',
        '''def resolve(overloads, arg):
    order = ["byte", "short", "char", "int", "long", "float", "double"]
    chain = order[order.index(arg):]
    for t in chain:
        if t in overloads: return t
    wrapper = {"byte": "Byte", "short": "Short", "char": "Character", "int": "Integer",
               "long": "Long", "float": "Float", "double": "Double"}[arg]
    for t in [wrapper, "Number", "Object"]:
        if t in overloads: return t
    for t in chain:
        if t + "..." in overloads: return t + "..."
    return "compile error"
''',
    ],
    guide=G(
        "Lesson *Polymorphism, overriding and overloading*: the three phases of overload resolution.",
        "The compiler prefers the least 'effort': first a plain widening, then boxing, then varargs. Within a "
        "phase the closest type wins. So build the list of candidates for each phase in order of closeness and "
        "return the first one that exists.",
        ["Write the widening chain starting at the argument type. `char` has its own chain and never widens to `short`.",
         "Only if phase 1 finds nothing, try the wrapper, then `Number` (not for `Character`), then `Object`.",
         "Only if phase 2 finds nothing, try `T...` along the widening chain."],
        "Checking 'exact match, then wrapper, then anything wider' is the intuitive order and it is wrong: "
        "widening `int` to `long` beats boxing to `Integer`.",
        r"""**Dry run** `resolve(["long", "Integer"], "int")`. Phase 1 chain for `int`: `int, long, float, double`.
`int` is not offered; `long` is. Return `"long"` without ever looking at `Integer`.

**Dry run** `resolve(["Long"], "int")`. Phase 1: none. Phase 2: `Integer`, `Number`, `Object`: none (the
compiler never widens and then boxes). Phase 3: none. `"compile error"`.

```java
static void m(long x)    { System.out.println("long"); }
static void m(Integer x) { System.out.println("Integer"); }
static void m(int... x)  { System.out.println("varargs"); }

m(5);            // long: widening beats boxing, which beats varargs
char c = 'x';
m(c);            // long: char widens to int, long, ...; never to short
// static void n(Long x) {}   n(5);   does not compile: no widen-then-box
```""",
        "Time O(1): the candidate lists have fixed length. Space O(1).",
        "- Preferring boxing to widening.\n- Letting `char` widen to `short`, or `short`/`byte` to `char`.\n"
        "- Giving `Character` the supertype `Number`.\n- Trying varargs before boxing.",
        "With two parameters the compiler needs one method that is at least as specific in every position; "
        "otherwise the call is ambiguous.",
    ),
),
# ------------------------------------------------------------------ java-dynamic-dispatch
dict(
    id="java-dynamic-dispatch",
    title="Dynamic dispatch, hiding and fields",
    difficulty="Medium",
    pattern="Java inheritance",
    entry="access",
    description=r"""
Given a class hierarchy and `Declared ref = new Runtime();`, decide which class's member is used by
`ref.member`.

`classes` maps a class name to `{"parent": name or None, "methods": [...], "statics": [...], "fields": [...]}`,
listing the instance methods, static methods and fields **declared in that class**.

Write `access(classes, declared, runtime, kind, member)` where `kind` is `"method"`, `"static"` or `"field"`.

1. **Compile-time check.** Search for the member (of that kind) starting at `declared` and going up through
   parents. If it is not found, return `"compile error"`.
2. **Selection.**
   - `"field"` and `"static"`: the class found in step 1 (the declared type decides).
   - `"method"`: search again starting at `runtime` and going up; return the first class that declares it
     (the runtime type decides).

`runtime` is always `declared` or one of its subclasses.

**Example** with `Animal {methods: [speak], statics: [kind], fields: [name]}` and
`Dog extends Animal {methods: [speak, fetch], statics: [kind], fields: [name]}`:
`access(c, "Animal", "Dog", "method", "speak")` → `"Dog"`; `"static", "kind"` → `"Animal"`;
`"field", "name"` → `"Animal"`; `"method", "fetch"` → `"compile error"`.
""",
    starter='''def access(classes, declared, runtime, kind, member):
    pass
''',
    solution='''def access(classes, declared, runtime, kind, member):
    table = {"method": "methods", "static": "statics", "field": "fields"}[kind]

    def find(start):
        c = start
        while c is not None:
            if member in classes[c][table]:
                return c
            c = classes[c]["parent"]
        return None

    found = find(declared)
    if found is None:
        return "compile error"
    if kind == "method":
        return find(runtime)
    return found
''',
    tests=[
        [{"Animal": {"parent": None, "methods": ["speak"], "statics": ["kind"], "fields": ["name"]},
          "Dog": {"parent": "Animal", "methods": ["speak", "fetch"], "statics": ["kind"], "fields": ["name"]}},
         "Animal", "Dog", "method", "speak"],
        [{"Animal": {"parent": None, "methods": ["speak"], "statics": ["kind"], "fields": ["name"]},
          "Dog": {"parent": "Animal", "methods": ["speak", "fetch"], "statics": ["kind"], "fields": ["name"]}},
         "Animal", "Dog", "static", "kind"],
        [{"Animal": {"parent": None, "methods": ["speak"], "statics": ["kind"], "fields": ["name"]},
          "Dog": {"parent": "Animal", "methods": ["speak", "fetch"], "statics": ["kind"], "fields": ["name"]}},
         "Animal", "Dog", "field", "name"],
        [{"Animal": {"parent": None, "methods": ["speak"], "statics": ["kind"], "fields": ["name"]},
          "Dog": {"parent": "Animal", "methods": ["speak", "fetch"], "statics": ["kind"], "fields": ["name"]}},
         "Animal", "Dog", "method", "fetch"],
        [{"Animal": {"parent": None, "methods": ["speak"], "statics": ["kind"], "fields": ["name"]},
          "Dog": {"parent": "Animal", "methods": ["speak", "fetch"], "statics": ["kind"], "fields": ["name"]}},
         "Dog", "Dog", "method", "fetch"],
        [{"A": {"parent": None, "methods": ["m", "n"], "statics": [], "fields": ["x"]},
          "B": {"parent": "A", "methods": ["m"], "statics": ["s"], "fields": []},
          "C": {"parent": "B", "methods": ["n"], "statics": [], "fields": ["x"]}},
         "A", "C", "method", "m"],
        [{"A": {"parent": None, "methods": ["m", "n"], "statics": [], "fields": ["x"]},
          "B": {"parent": "A", "methods": ["m"], "statics": ["s"], "fields": []},
          "C": {"parent": "B", "methods": ["n"], "statics": [], "fields": ["x"]}},
         "A", "C", "method", "n"],
        [{"A": {"parent": None, "methods": ["m", "n"], "statics": [], "fields": ["x"]},
          "B": {"parent": "A", "methods": ["m"], "statics": ["s"], "fields": []},
          "C": {"parent": "B", "methods": ["n"], "statics": [], "fields": ["x"]}},
         "B", "C", "field", "x"],
        [{"A": {"parent": None, "methods": ["m", "n"], "statics": [], "fields": ["x"]},
          "B": {"parent": "A", "methods": ["m"], "statics": ["s"], "fields": []},
          "C": {"parent": "B", "methods": ["n"], "statics": [], "fields": ["x"]}},
         "C", "C", "field", "x"],
        [{"A": {"parent": None, "methods": ["m", "n"], "statics": [], "fields": ["x"]},
          "B": {"parent": "A", "methods": ["m"], "statics": ["s"], "fields": []},
          "C": {"parent": "B", "methods": ["n"], "statics": [], "fields": ["x"]}},
         "A", "B", "static", "s"],
        [{"A": {"parent": None, "methods": ["m", "n"], "statics": [], "fields": ["x"]},
          "B": {"parent": "A", "methods": ["m"], "statics": ["s"], "fields": []},
          "C": {"parent": "B", "methods": ["n"], "statics": [], "fields": ["x"]}},
         "C", "C", "static", "s"],
        [{"A": {"parent": None, "methods": ["m", "n"], "statics": [], "fields": ["x"]},
          "B": {"parent": "A", "methods": ["m"], "statics": ["s"], "fields": []},
          "C": {"parent": "B", "methods": ["n"], "statics": [], "fields": ["x"]}},
         "B", "B", "method", "n"],
        [{"A": {"parent": None, "methods": ["m"], "statics": ["m"], "fields": ["m"]}},
         "A", "A", "field", "q"],
    ],
    wrong_solutions=[
        '''def access(classes, declared, runtime, kind, member):
    table = {"method": "methods", "static": "statics", "field": "fields"}[kind]
    c = runtime
    while c is not None:
        if member in classes[c][table]:
            return c
        c = classes[c]["parent"]
    return "compile error"
''',
        '''def access(classes, declared, runtime, kind, member):
    table = {"method": "methods", "static": "statics", "field": "fields"}[kind]
    c = declared
    while c is not None:
        if member in classes[c][table]:
            return c
        c = classes[c]["parent"]
    return "compile error"
''',
    ],
    guide=G(
        "Lesson *Polymorphism, overriding and overloading*: declared type versus runtime type; hiding.",
        "Two lookups. The compiler looks from the **declared** type to decide whether the access is legal. "
        "Only instance methods get a second lookup, from the **runtime** type.",
        ["Write one helper that climbs the parent chain from a starting class.",
         "If the helper finds nothing from the declared type, it is a compile error, whatever the object really is.",
         "For methods, call the helper again from the runtime type."],
        "Always starting at the runtime type treats fields and static methods as polymorphic. They are not.",
        r"""**Dry run** `A {m, n; field x}`, `B extends A {m; static s}`, `C extends B {n; field x}` and
`A ref = new C()`.

- `ref.m()`: legal (found in A). Runtime search from C: C has no `m`, B has → **B**.
- `ref.n()`: legal. Runtime search: C has `n` → **C**.
- `ref.x`: found from the declared type A → **A**, although C declares its own `x`.
- `ref.s()`: `s` is declared in B, which is not visible from A → **compile error**.

```java
class A { String x = "A.x"; String m() { return "A.m"; } static String s() { return "A.s"; } }
class B extends A { String x = "B.x"; @Override String m() { return "B.m"; } static String s() { return "B.s"; } }

A ref = new B();
System.out.println(ref.m());            // B.m   instance method: runtime type
System.out.println(ref.x);              // A.x   field: declared type
System.out.println(ref.s());            // A.s   static: declared type (write A.s() instead)
System.out.println(((B) ref).x);        // B.x   a cast changes the declared type of the expression
```""",
        "Time O(depth of the hierarchy), space O(1).",
        "- Dispatching fields or static methods on the runtime type.\n"
        "- Allowing a call that only the runtime class declares.\n"
        "- Returning the declared class for an overridden instance method.",
    ),
),
# ------------------------------------------------------------------ java-init-order
dict(
    id="java-init-order",
    title="Constructor and initialiser order",
    difficulty="Medium",
    pattern="Java objects",
    entry="init_order",
    description=r"""
Work out what a program prints while creating objects.

`classes` maps a class name to
`{"parent": name or None, "static": [labels], "instance": [labels], "ctor": label}`:

- `static`: static initialisers and static field initialisers, in source order;
- `instance`: instance field initialisers and instance initialiser blocks, in source order;
- `ctor`: the constructor body.

`news` is a list of class names: the program executes `new X()` for each, in order. Return the list of
strings printed, each as `"<Class>.<label>"`.

**Rules**

1. A class is **initialised** the first time it is needed: first its superclass (if not yet initialised),
   then its own `static` labels. This happens **once** per class for the whole program.
2. `new X()` initialises `X` (rule 1), then, for each class from the **top** of X's hierarchy **down** to
   `X`: that class's `instance` labels, then its `ctor`.

**Example** `Base {static: [s], instance: [f], ctor: c}`, `Derived extends Base {static: [s], instance: [f], ctor: c}`,
`news = ["Derived", "Derived"]` →
`["Base.s", "Derived.s", "Base.f", "Base.c", "Derived.f", "Derived.c", "Base.f", "Base.c", "Derived.f", "Derived.c"]`
""",
    starter='''def init_order(classes, news):
    pass
''',
    solution='''def init_order(classes, news):
    out = []
    loaded = set()

    def chain(name):
        c, path = name, []
        while c is not None:
            path.append(c)
            c = classes[c]["parent"]
        return path[::-1]

    for name in news:
        path = chain(name)
        for c in path:
            if c not in loaded:
                loaded.add(c)
                out.extend(c + "." + s for s in classes[c]["static"])
        for c in path:
            out.extend(c + "." + s for s in classes[c]["instance"])
            out.append(c + "." + classes[c]["ctor"])
    return out
''',
    tests=[
        [{"Base": {"parent": None, "static": ["s"], "instance": ["f"], "ctor": "c"},
          "Derived": {"parent": "Base", "static": ["s"], "instance": ["f"], "ctor": "c"}}, ["Derived", "Derived"]],
        [{"Base": {"parent": None, "static": ["s"], "instance": ["f"], "ctor": "c"},
          "Derived": {"parent": "Base", "static": ["s"], "instance": ["f"], "ctor": "c"}}, ["Base", "Derived"]],
        [{"Base": {"parent": None, "static": ["s"], "instance": ["f"], "ctor": "c"},
          "Derived": {"parent": "Base", "static": ["s"], "instance": ["f"], "ctor": "c"}}, ["Derived", "Base"]],
        [{"A": {"parent": None, "static": [], "instance": [], "ctor": "ctor"}}, ["A"]],
        [{"A": {"parent": None, "static": ["s1", "s2"], "instance": ["x", "block", "y"], "ctor": "ctor"}}, ["A", "A"]],
        [{"A": {"parent": None, "static": ["s"], "instance": ["i"], "ctor": "c"}}, []],
        [{"A": {"parent": None, "static": ["s"], "instance": ["i"], "ctor": "c"},
          "B": {"parent": "A", "static": ["s"], "instance": [], "ctor": "c"},
          "C": {"parent": "B", "static": [], "instance": ["i"], "ctor": "c"}}, ["C"]],
        [{"A": {"parent": None, "static": ["s"], "instance": ["i"], "ctor": "c"},
          "B": {"parent": "A", "static": ["s"], "instance": [], "ctor": "c"},
          "C": {"parent": "B", "static": [], "instance": ["i"], "ctor": "c"}}, ["B", "C", "A"]],
        [{"A": {"parent": None, "static": ["s"], "instance": ["i"], "ctor": "c"},
          "X": {"parent": "A", "static": ["s"], "instance": ["i"], "ctor": "c"},
          "Y": {"parent": "A", "static": ["s"], "instance": ["i"], "ctor": "c"}}, ["X", "Y", "X"]],
        [{"A": {"parent": None, "static": ["s"], "instance": ["i"], "ctor": "c"},
          "X": {"parent": "A", "static": ["s"], "instance": ["i"], "ctor": "c"},
          "Y": {"parent": "A", "static": ["s"], "instance": ["i"], "ctor": "c"}}, ["A", "A"]],
        [{"P": {"parent": None, "static": ["a", "b"], "instance": [], "ctor": "c"},
          "Q": {"parent": "P", "static": [], "instance": ["m", "n"], "ctor": "c"}}, ["Q", "P", "Q"]],
    ],
    wrong_solutions=[
        '''def init_order(classes, news):
    out = []
    def chain(name):
        c, path = name, []
        while c is not None:
            path.append(c); c = classes[c]["parent"]
        return path[::-1]
    for name in news:
        path = chain(name)
        for c in path:
            out.extend(c + "." + s for s in classes[c]["static"])
        for c in path:
            out.extend(c + "." + s for s in classes[c]["instance"])
            out.append(c + "." + classes[c]["ctor"])
    return out
''',
        '''def init_order(classes, news):
    out, loaded = [], set()
    def chain(name):
        c, path = name, []
        while c is not None:
            path.append(c); c = classes[c]["parent"]
        return path[::-1]
    for name in news:
        path = chain(name)
        for c in path:
            if c not in loaded:
                loaded.add(c)
                out.extend(c + "." + s for s in classes[c]["static"])
        for c in path:
            out.extend(c + "." + s for s in classes[c]["instance"])
        for c in path:
            out.append(c + "." + classes[c]["ctor"])
    return out
''',
    ],
    guide=G(
        "Lesson *Constructors, this and super*: the complete order of initialisation.",
        "Two phases per `new`. The static phase happens once per class, top of the hierarchy first. The instance "
        "phase happens every time, also top first, and within one class the field initialisers come before the "
        "constructor body.",
        ["Build the chain from the root class down to the class being created.",
         "Keep a set of classes whose static part has already run.",
         "For each class in the chain: all instance labels, then that class's constructor, before moving down."],
        "Printing every class's instance initialisers first and all constructors afterwards is a common wrong "
        "model: in reality each class finishes (initialisers, then constructor) before its subclass starts.",
        r"""**Dry run** `news = ["Derived", "Base"]`. First `new Derived()`: statics for Base then Derived;
then `Base.f, Base.c, Derived.f, Derived.c`. Then `new Base()`: Base is already initialised, so no statics;
`Base.f, Base.c`.

```java
class Base {
    static { System.out.println("Base.s"); }
    int f = log("Base.f");
    Base() { System.out.println("Base.c"); }
    static int log(String s) { System.out.println(s); return 0; }
}
class Derived extends Base {
    static { System.out.println("Derived.s"); }
    int g = log("Derived.f");
    Derived() { System.out.println("Derived.c"); }      // an implicit super() runs first
}
// new Derived(); prints Base.s, Derived.s, Base.f, Base.c, Derived.f, Derived.c
```""",
        "Time O(total labels printed), space O(number of classes).",
        "- Running static initialisers for every `new`.\n- Running a subclass's static part before its superclass's.\n"
        "- Running all field initialisers before any constructor body.",
        "This order is why calling an overridable method from a constructor sees the subclass's fields still at "
        "their default values.",
    ),
),
# ------------------------------------------------------------------ java-access-check
dict(
    id="java-access-check",
    title="Can this code see that member?",
    difficulty="Easy",
    pattern="Java classes",
    entry="can_access",
    description=r"""
Apply Java's four access levels.

Write `can_access(modifier, same_class, same_package, is_subclass, via_own_type)` returning a boolean.

- `modifier` is `"private"`, `"package"` (no keyword: package-private), `"protected"` or `"public"`.
- `same_class`: the accessing code is inside the class that declares the member.
- `same_package`: the accessing code is in the same package as the declaring class (always true when
  `same_class` is true).
- `is_subclass`: the accessing class is a subclass of the declaring class.
- `via_own_type`: for an instance member reached through a reference `ref.member`, whether the reference's
  type is the accessing class itself or one of its subclasses (as with `this.member`).

**Rules**

| modifier | accessible when |
|---|---|
| `public` | always |
| `protected` | same package, **or** (`is_subclass` **and** `via_own_type`) |
| `package` | same package |
| `private` | same class |

**Example** `can_access("protected", False, False, True, False)` → `False`: a subclass in another package
cannot use a protected member through a reference typed as the superclass.
""",
    starter='''def can_access(modifier, same_class, same_package, is_subclass, via_own_type):
    pass
''',
    solution='''def can_access(modifier, same_class, same_package, is_subclass, via_own_type):
    if modifier == "public":
        return True
    if modifier == "protected":
        return same_package or (is_subclass and via_own_type)
    if modifier == "package":
        return same_package
    return same_class
''',
    tests=[
        ["protected", False, False, True, False],
        ["protected", False, False, True, True],
        ["protected", False, True, False, False],
        ["protected", False, False, False, True],
        ["private", True, True, False, True],
        ["private", False, True, True, True],
        ["package", False, True, False, False],
        ["package", False, False, True, True],
        ["public", False, False, False, False],
        ["private", False, False, False, False],
        ["package", True, True, False, True],
        ["protected", True, True, False, True],
    ],
    wrong_solutions=[
        '''def can_access(modifier, same_class, same_package, is_subclass, via_own_type):
    if modifier == "public": return True
    if modifier == "protected": return same_package or is_subclass
    if modifier == "package": return same_package
    return same_class
''',
        '''def can_access(modifier, same_class, same_package, is_subclass, via_own_type):
    if modifier == "public": return True
    if modifier == "protected": return is_subclass and via_own_type
    if modifier == "package": return same_package
    return same_class
''',
        '''def can_access(modifier, same_class, same_package, is_subclass, via_own_type):
    if modifier == "public": return True
    if modifier == "protected": return same_package or (is_subclass and via_own_type)
    if modifier == "package": return same_package or is_subclass
    return same_class
''',
    ],
    guide=G(
        "Lessons *Encapsulation* and *Minimal accessibility and immutable classes*.",
        "Each level adds one circle of trust: the class, then the package, then subclasses, then everyone. The one "
        "subtlety is `protected` outside the package, which works only on references of the subclass's own type.",
        ["Handle the four modifiers one at a time.", "`protected` includes everything `package` allows.",
         "Outside the package, protected needs both conditions: a subclass, and a reference of its own type."],
        "A full 4 × 5 lookup table of situations works, and is how the lesson presents it. Four `if` statements are shorter.",
        r"""**Dry run** `("protected", False, False, True, False)`: not the same package; it is a subclass, but the
access is through a superclass-typed reference, so `is_subclass and via_own_type` is False → **False**.

```java
package shop.billing;
public class Invoice {
    private   int a;      // Invoice only
    int       b;          // package shop.billing
    protected int c;      // shop.billing + subclasses (through their own type)
    public    int d;      // everyone
}

package shop.web;
class PremiumInvoice extends shop.billing.Invoice {
    int ok()                         { return c + d; }          // this.c: fine
    int no(shop.billing.Invoice o)   { return o.d; }            // o.c would not compile
}
```""",
        "Time O(1), space O(1).",
        "- Thinking `protected` means 'subclasses only': it also includes the whole package.\n"
        "- Thinking package-private members are visible to subclasses in other packages.\n"
        "- Forgetting the own-type restriction on protected access.",
    ),
),
# ------------------------------------------------------------------ java-default-method-conflict
dict(
    id="java-default-method-conflict",
    title="Default methods: which implementation wins?",
    difficulty="Medium",
    pattern="Java interfaces",
    entry="resolve_default",
    description=r"""
A class inherits a method `m()` from its superclass chain and from interfaces. Decide which body it gets.

`types` maps a type name to
`{"kind": "class" or "interface", "super": superclass name or None, "interfaces": [names], "m": "body", "abstract" or None}`.

- For a class, `super` is its superclass and `interfaces` the interfaces it implements.
- For an interface, `super` is `None` and `interfaces` are the interfaces it extends.
- `m` says whether the type declares `m` with a body (a concrete method or a default method), declares it
  abstract, or does not declare it.

Write `resolve_default(types, cls)` for a class `cls`. Return the **name of the type** whose body is used,
`"abstract"` if the class ends up with no body, or `"conflict"` if it does not compile until it overrides `m`.

**Rules, in order**

1. **Classes win.** Walk from `cls` up its superclass chain. The first class that declares `m` decides:
   `"body"` → that class's name; `"abstract"` → `"abstract"`.
2. Otherwise collect every interface reachable from `cls` or any of its superclasses (through `interfaces`,
   transitively) that **declares** `m` (body or abstract). Discard any that is a super-interface of another
   collected one (**the most specific wins**).
3. If one interface remains: `"body"` → its name; `"abstract"` → `"abstract"`.
   If several remain: `"conflict"` if at least one has a body, otherwise `"abstract"`. If none: `"abstract"`.
""",
    starter='''def resolve_default(types, cls):
    pass
''',
    solution='''def resolve_default(types, cls):
    def supers(i):
        seen, stack = set(), list(types[i]["interfaces"])
        while stack:
            x = stack.pop()
            if x not in seen:
                seen.add(x)
                stack.extend(types[x]["interfaces"])
        return seen

    c = cls
    roots = []
    while c is not None:
        if types[c]["m"] == "body":
            return c
        if types[c]["m"] == "abstract":
            return "abstract"
        roots.extend(types[c]["interfaces"])
        c = types[c]["super"]
    reachable = set()
    for r in roots:
        reachable.add(r)
        reachable |= supers(r)
    declaring = {i for i in reachable if types[i]["m"] is not None}
    maximal = [i for i in declaring if not any(i in supers(j) for j in declaring if j != i)]
    if not maximal:
        return "abstract"
    if len(maximal) == 1:
        return maximal[0] if types[maximal[0]]["m"] == "body" else "abstract"
    return "conflict" if any(types[i]["m"] == "body" for i in maximal) else "abstract"
''',
    tests=[
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "B": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "C": {"kind": "class", "super": None, "interfaces": ["A", "B"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "B": {"kind": "interface", "super": None, "interfaces": ["A"], "m": "body"},
          "C": {"kind": "class", "super": None, "interfaces": ["A", "B"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "Base": {"kind": "class", "super": None, "interfaces": [], "m": "body"},
          "C": {"kind": "class", "super": "Base", "interfaces": ["A"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "C": {"kind": "class", "super": None, "interfaces": ["A"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "abstract"},
          "C": {"kind": "class", "super": None, "interfaces": ["A"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "B": {"kind": "interface", "super": None, "interfaces": ["A"], "m": "abstract"},
          "C": {"kind": "class", "super": None, "interfaces": ["B"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "B": {"kind": "interface", "super": None, "interfaces": [], "m": "abstract"},
          "C": {"kind": "class", "super": None, "interfaces": ["A", "B"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "abstract"},
          "B": {"kind": "interface", "super": None, "interfaces": [], "m": "abstract"},
          "C": {"kind": "class", "super": None, "interfaces": ["A", "B"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "B": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "C": {"kind": "class", "super": None, "interfaces": ["A", "B"], "m": "body"}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "Base": {"kind": "class", "super": None, "interfaces": ["A"], "m": None},
          "B": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "C": {"kind": "class", "super": "Base", "interfaces": ["B"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "B": {"kind": "interface", "super": None, "interfaces": ["A"], "m": None},
          "D": {"kind": "interface", "super": None, "interfaces": ["A"], "m": None},
          "C": {"kind": "class", "super": None, "interfaces": ["B", "D"], "m": None}}, "C"],
        [{"A": {"kind": "interface", "super": None, "interfaces": [], "m": "body"},
          "Base": {"kind": "class", "super": None, "interfaces": [], "m": "abstract"},
          "C": {"kind": "class", "super": "Base", "interfaces": ["A"], "m": None}}, "C"],
        [{"C": {"kind": "class", "super": None, "interfaces": [], "m": None}}, "C"],
    ],
    wrong_solutions=[
        '''def resolve_default(types, cls):
    c = cls
    roots = []
    while c is not None:
        if types[c]["m"] == "body": return c
        if types[c]["m"] == "abstract": return "abstract"
        roots.extend(types[c]["interfaces"])
        c = types[c]["super"]
    bodies = [i for i in roots if types[i]["m"] == "body"]
    if len(bodies) == 1: return bodies[0]
    return "conflict" if bodies else "abstract"
''',
        '''def resolve_default(types, cls):
    def supers(i):
        seen, stack = set(), list(types[i]["interfaces"])
        while stack:
            x = stack.pop()
            if x not in seen:
                seen.add(x); stack.extend(types[x]["interfaces"])
        return seen
    reachable = set()
    c = cls
    while c is not None:
        for r in types[c]["interfaces"]:
            reachable.add(r); reachable |= supers(r)
        c = types[c]["super"]
    declaring = {i for i in reachable if types[i]["m"] is not None}
    maximal = [i for i in declaring if not any(i in supers(j) for j in declaring if j != i)]
    if len(maximal) == 1 and types[maximal[0]]["m"] == "body": return maximal[0]
    if len(maximal) > 1 and any(types[i]["m"] == "body" for i in maximal): return "conflict"
    c = cls
    while c is not None:
        if types[c]["m"] == "body": return c
        c = types[c]["super"]
    return "abstract"
''',
    ],
    guide=G(
        "Lesson *Interfaces, default methods, sealed types and pattern matching*: the three resolution rules.",
        "Java avoids the diamond problem with a strict priority: anything from a class beats anything from an "
        "interface; among interfaces a sub-interface beats its super-interfaces; and a real tie is a compile error "
        "that the programmer must settle.",
        ["Walk the superclass chain first; a declaration in any class there ends the search.",
         "Gather all interfaces, including inherited ones, that mention `m` at all.",
         "Remove any interface that another gathered interface extends; then count what is left."],
        "Looking only at the directly implemented interfaces misses defaults inherited through sub-interfaces and "
        "cannot tell that a sub-interface overrides its parent.",
        r"""**Dry run** `A { default m }`, `B extends A { default m }`, `class C implements A, B`. No class declares
`m`. Declaring interfaces: `{A, B}`. `A` is a super-interface of `B`, so discard `A`. One remains, with a
body → `"B"`.

**Dry run** `A { default m }`, `B { abstract m }`, unrelated, `class C implements A, B`. Both remain, and one
has a body → `"conflict"`: Java will not silently choose the default over an unrelated abstract declaration.

```java
interface Printer { default String status() { return "printer"; } }
interface Scanner { default String status() { return "scanner"; } }

class Copier implements Printer, Scanner {
    @Override
    public String status() {                                   // required: the defaults conflict
        return Printer.super.status() + "+" + Scanner.super.status();
    }
}
```""",
        "Time O(t²) for t types in the worst case (pairwise 'is a super-interface of'); tiny in practice.",
        "- Letting an interface default beat a method inherited from a superclass.\n"
        "- Forgetting that an abstract redeclaration in a sub-interface hides the parent's default.\n"
        "- Reporting a conflict for the diamond where two interfaces merely inherit one default from a common parent.",
    ),
),
# ------------------------------------------------------------------ java-sealed-exhaustive
dict(
    id="java-sealed-exhaustive",
    title="Is the switch over a sealed type exhaustive?",
    difficulty="Medium",
    pattern="Java interfaces",
    entry="missing_cases",
    description=r"""
A `sealed` interface lists every permitted subtype, so the compiler can check that a pattern-matching
`switch` covers all possibilities.

`hierarchy` maps a type name to the list of its **permitted direct subtypes**. A type with an empty list is
a **leaf** (a record or final class). Types with a non-empty list are sealed and abstract: no object is
*directly* of such a type, only of some leaf below it.

Write `missing_cases(hierarchy, root, cases)`:

- `root` is the type of the value being switched on;
- `cases` is the list of type patterns in the switch (`case X x ->`). A pattern covers `X` and everything
  below `X`.

Return the **sorted** list of leaf types under `root` that no pattern covers. An empty list means the
switch is exhaustive and needs no `default`.

**Example** `Shape permits Circle, Polygon; Polygon permits Square, Triangle`:
`missing_cases(h, "Shape", ["Circle", "Square"])` → `["Triangle"]`;
`missing_cases(h, "Shape", ["Circle", "Polygon"])` → `[]`.
""",
    starter='''def missing_cases(hierarchy, root, cases):
    pass
''',
    solution='''def missing_cases(hierarchy, root, cases):
    def leaves(t, acc):
        if not hierarchy[t]:
            acc.add(t)
        for child in hierarchy[t]:
            leaves(child, acc)
        return acc

    covered = set()
    for c in cases:
        leaves(c, covered)
    return sorted(leaves(root, set()) - covered)
''',
    tests=[
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Shape", ["Circle", "Square"]],
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Shape", ["Circle", "Polygon"]],
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Shape", []],
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Shape", ["Shape"]],
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Polygon", ["Square"]],
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Polygon", ["Circle"]],
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Circle", []],
        [{"Shape": ["Circle", "Polygon"], "Polygon": ["Square", "Triangle"], "Circle": [], "Square": [], "Triangle": []},
         "Shape", ["Triangle", "Square", "Circle"]],
        [{"P": ["Card", "Cash", "Voucher"], "Card": [], "Cash": [], "Voucher": []}, "P", ["Cash"]],
        [{"E": ["Lit", "Bin"], "Bin": ["Add", "Mul"], "Lit": [], "Add": [], "Mul": ["Sq", "Cube"], "Sq": [], "Cube": []},
         "E", ["Lit", "Add", "Sq"]],
        [{"E": ["Lit", "Bin"], "Bin": ["Add", "Mul"], "Lit": [], "Add": [], "Mul": ["Sq", "Cube"], "Sq": [], "Cube": []},
         "E", ["Mul", "Lit"]],
        [{"R": ["A", "B"], "A": ["X"], "B": ["X", "Y"], "X": [], "Y": []}, "R", ["A"]],
    ],
    wrong_solutions=[
        '''def missing_cases(hierarchy, root, cases):
    return sorted(t for t in hierarchy[root] if t not in cases)
''',
        '''def missing_cases(hierarchy, root, cases):
    leaves = []
    def walk(t):
        if not hierarchy[t]:
            leaves.append(t)
        for c in hierarchy[t]:
            walk(c)
    walk(root)
    return sorted(set(l for l in leaves if l not in cases))
''',
    ],
    guide=G(
        "Lesson *Interfaces, default methods, sealed types and pattern matching*: sealed types and exhaustive switches.",
        "Only leaves are real values. Each case covers all the leaves at or below its type, so collect the covered "
        "leaves and subtract them from the leaves under the root.",
["Write a helper that collects every leaf at or below a given type.",
         "The covered leaves are the union of that helper over all case types.",
         "Answer: leaves under the root minus the covered ones, sorted. A leaf permitted by two sealed parents is covered if either parent is named."],
        "Listing only the root's direct subtypes that lack a case ignores nested sealed types in both directions: "
        "a parent pattern covering its children, and children patterns covering a parent.",
        r"""**Dry run** `Shape → {Circle, Polygon}`, `Polygon → {Square, Triangle}`, cases `[Circle, Square]`.
Leaves under `Shape`: `{Circle, Square, Triangle}`. Covered by the cases: `{Circle} ∪ {Square}`. The
difference is `["Triangle"]`. With cases `[Circle, Polygon]`, `Polygon` covers `{Square, Triangle}` and
nothing is missing.

```java
sealed interface Shape permits Circle, Polygon { }
record Circle(double r) implements Shape { }
sealed interface Polygon extends Shape permits Square, Triangle { }
record Square(double side) implements Polygon { }
record Triangle(double base, double height) implements Polygon { }

static double area(Shape s) {
    return switch (s) {                       // exhaustive: no default needed
        case Circle c   -> Math.PI * c.r() * c.r();
        case Square q   -> q.side() * q.side();
        case Triangle t -> 0.5 * t.base() * t.height();
    };                                        // remove one case and this stops compiling
}
```""",
        "Time O(number of types under the root), space O(depth) for the recursion.",
        "- Looking only one level down.\n- Not letting a case on a sealed parent cover all its leaves.\n"
        "- Reporting sealed (abstract) parents as missing instead of their leaves.",
    ),
),
# ------------------------------------------------------------------ java-gc-reachability
dict(
    id="java-gc-reachability",
    title="Which objects can be garbage collected?",
    difficulty="Medium",
    pattern="Java memory",
    entry="collectable",
    description=r"""
The garbage collector may reclaim an object when no chain of references from a **GC root** reaches it.
Roots are the live local variables on thread stacks and the static fields.

Write `collectable(objects, roots)`:

- `objects` maps each object's id (a string) to the list of ids its fields refer to;
- `roots` is the list of ids referred to directly by roots (it may contain repeats; every id exists).

Return the **sorted** list of ids that are unreachable.

Objects that refer to each other in a cycle are still garbage if no root reaches the cycle: Java does not
count references.

**Example** `collectable({"a": ["b"], "b": [], "c": ["d"], "d": ["c"], "e": ["a"]}, ["a"])` → `["c", "d", "e"]`
""",
    starter='''def collectable(objects, roots):
    pass
''',
    solution='''def collectable(objects, roots):
    marked = set()
    stack = list(roots)
    while stack:
        o = stack.pop()
        if o in marked:
            continue
        marked.add(o)
        stack.extend(objects[o])
    return sorted(o for o in objects if o not in marked)
''',
    tests=[
        [{"a": ["b"], "b": [], "c": ["d"], "d": ["c"], "e": ["a"]}, ["a"]],
        [{"a": [], "b": []}, []],
        [{"a": [], "b": []}, ["a", "b"]],
        [{}, []],
        [{"x": ["x"]}, []],
        [{"x": ["x"]}, ["x"]],
        [{"order": ["customer", "item"], "customer": [], "item": [], "map": ["customer"], "old": []}, ["map"]],
        [{"n1": ["n2"], "n2": ["n3"], "n3": ["n1"], "n4": ["n1"]}, ["n4"]],
        [{"n1": ["n2"], "n2": ["n3"], "n3": ["n1"], "n4": ["n1"]}, ["n2", "n2"]],
        [{str(i): [str(i + 1)] if i < 499 else [] for i in range(500)}, ["250"]],
        [{"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": [], "e": ["d"], "f": ["e"]}, ["a"]],
        [{str(i): [str((i * 7) % 60), str((i + 1) % 60)] if i % 5 else [] for i in range(60)}, ["3"]],
    ],
    wrong_solutions=[
        '''def collectable(objects, roots):
    referenced = set(roots)
    for refs in objects.values():
        referenced.update(refs)
    return sorted(o for o in objects if o not in referenced)
''',
        '''def collectable(objects, roots):
    reachable = set(roots)
    for r in roots:
        reachable.update(objects[r])
    return sorted(o for o in objects if o not in reachable)
''',
    ],
    guide=G(
        "Lesson *Object lifecycle, scope and garbage collection*: reachability and mark-and-sweep.",
        "This is graph reachability. Mark everything you can reach from the roots; whatever stays unmarked is garbage.",
        ["Use a stack (or queue) of objects still to visit, starting with the roots.",
         "Skip objects already marked, or a cycle will loop for ever.",
         "The answer is the set of all ids minus the marked ones, sorted."],
        "Reference counting ('is anything pointing at me?') is the tempting shortcut. It wrongly keeps cycles "
        "alive, and it keeps an object alive merely because another garbage object refers to it.",
        r"""**Dry run** `{a→b, b, c→d, d→c, e→a}`, roots `[a]`. Visit `a`, then `b`. Marked `{a, b}`.
`c` and `d` point at each other but nothing marked points at them; `e` points at `a`, which does not make
`e` reachable. Garbage: `["c", "d", "e"]`.

```java
class Node { Node next; }

static void demo() {
    Node a = new Node();           // reachable through the local variable a
    Node c = new Node();
    Node d = new Node();
    c.next = d;
    d.next = c;                    // a cycle
    c = null;
    d = null;                      // the cycle is unreachable: both objects are eligible for collection
}                                  // when demo returns, the object a referred to becomes eligible too
```""",
        "Time O(V + E) for V objects and E references, space O(V).",
        "- Counting references instead of tracing from roots.\n- Following only one level of references.\n"
        "- Recursing without a visited set on cyclic data.",
    ),
),
# ------------------------------------------------------------------ java-equals-hashcode-checker
dict(
    id="java-equals-hashcode-checker",
    title="equals / hashCode contract checker",
    difficulty="Medium",
    pattern="Java objects",
    entry="contract_violations",
    description=r"""
You are given how a class's `equals` and `hashCode` behave on `n` sample objects, numbered `0..n-1`:

- `eq[i][j]` is the boolean result of `obj_i.equals(obj_j)`;
- `hashes[i]` is `obj_i.hashCode()`.

Write `contract_violations(eq, hashes)` returning the **sorted** list of contract rules that these samples
violate. Possible entries:

| name | violated when |
|---|---|
| `"reflexive"` | some `eq[i][i]` is false |
| `"symmetric"` | some `eq[i][j] != eq[j][i]` |
| `"transitive"` | some `eq[i][j]` and `eq[j][k]` are true but `eq[i][k]` is false |
| `"hash"` | some `eq[i][j]` is true but `hashes[i] != hashes[j]` |

Unequal objects with equal hash codes are **not** a violation (that is an ordinary collision).
Return `[]` when all four rules hold.

**Example** `contract_violations([[True, True], [False, True]], [1, 1])` → `["symmetric"]`
""",
    starter='''def contract_violations(eq, hashes):
    pass
''',
    solution='''def contract_violations(eq, hashes):
    n = len(eq)
    bad = set()
    for i in range(n):
        if not eq[i][i]:
            bad.add("reflexive")
        for j in range(n):
            if eq[i][j] != eq[j][i]:
                bad.add("symmetric")
            if eq[i][j] and hashes[i] != hashes[j]:
                bad.add("hash")
            if eq[i][j]:
                for k in range(n):
                    if eq[j][k] and not eq[i][k]:
                        bad.add("transitive")
    return sorted(bad)
''',
    tests=[
        [[[True, True], [False, True]], [1, 1]],
        [[[True, False], [False, True]], [1, 1]],
        [[[True, True], [True, True]], [1, 2]],
        [[[True, True, False], [True, True, True], [False, True, True]], [5, 5, 5]],
        [[[False]], [0]],
        [[], []],
        [[[True]], [42]],
        [[[True, True, True], [True, True, True], [True, True, True]], [9, 9, 9]],
        [[[True, True, False], [True, True, True], [False, True, True]], [1, 1, 2]],
        [[[False, True], [False, False]], [1, 2]],
        [[[True, False, False], [False, True, True], [False, True, True]], [3, 4, 4]],
        [[[True, False, False], [False, True, True], [False, True, True]], [3, 4, 5]],
        [[[True, True, False, False], [False, True, True, False], [False, False, True, False], [False, False, False, True]], [1, 1, 1, 1]],
    ],
    wrong_solutions=[
        '''def contract_violations(eq, hashes):
    n = len(eq)
    bad = set()
    for i in range(n):
        if not eq[i][i]: bad.add("reflexive")
        for j in range(n):
            if eq[i][j] != eq[j][i]: bad.add("symmetric")
            if eq[i][j] != (hashes[i] == hashes[j]): bad.add("hash")
            if eq[i][j]:
                for k in range(n):
                    if eq[j][k] and not eq[i][k]: bad.add("transitive")
    return sorted(bad)
''',
        '''def contract_violations(eq, hashes):
    n = len(eq)
    bad = set()
    for i in range(n):
        if not eq[i][i]: bad.add("reflexive")
        for j in range(n):
            if eq[i][j] != eq[j][i]: bad.add("symmetric")
            if eq[i][j] and hashes[i] != hashes[j]: bad.add("hash")
    return sorted(bad)
''',
    ],
    guide=G(
        "Lesson *Writing equals and hashCode correctly*: the five rules of `equals` and the hash rule.",
        "Each rule is a statement about all pairs or triples of objects. With a matrix in hand you can test every "
        "pair and every triple directly.",
        ["Reflexive: look at the diagonal.", "Symmetric and hash: loop over all ordered pairs.",
         "Transitive: for every equal pair (i, j), every k equal to j must be equal to i."],
        "This *is* the brute force: three nested loops over n samples. For the handful of sample objects a test "
        "uses, that is exactly right. Libraries such as EqualsVerifier do the same on generated instances.",
        r"""**Dry run** a `ColourPoint` that ignores colour when compared with a plain point. Objects: 0 = red
point, 1 = plain point, 2 = blue point. `eq = [[T,T,F],[T,T,T],[F,T,T]]`, hashes all 5.
Reflexive: fine. Symmetric: fine. Hash: fine. Transitive: `eq[0][1]` and `eq[1][2]` are true but `eq[0][2]`
is false → `["transitive"]`.

```java
public final class Money {
    private final long cents;
    private final String currency;

    public Money(long cents, String currency) { this.cents = cents; this.currency = currency; }

    @Override public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Money m)) return false;
        return cents == m.cents && currency.equals(m.currency);
    }

    @Override public int hashCode() { return java.util.Objects.hash(cents, currency); }   // same fields as equals
}
// or simply: record Money(long cents, String currency) { }
```""",
        "Time O(n³) for the transitivity check, space O(1).",
        "- Reporting equal hash codes on unequal objects as a violation.\n- Checking only `i < j` and missing asymmetry.\n"
        "- Skipping transitivity.",
    ),
),
# ------------------------------------------------------------------ java-record-equality
dict(
    id="java-record-equality",
    title="Record equality",
    difficulty="Easy",
    pattern="Java objects",
    entry="records_equal",
    description=r"""
A record's generated `equals` returns true when the other object is a record of the **same type** and every
pair of corresponding components is equal, where each component is compared by its own rule.

A record value is `[type_name, components]` and each component is `[kind, value]`:

| kind | value | Java comparison |
|---|---|---|
| `"int"` | integer | `==` |
| `"double"` | a **string** such as `"1.5"`, `"0.0"`, `"-0.0"`, `"NaN"` | `Double.compare(a, b) == 0`: `NaN` equals `NaN`, and `0.0` does **not** equal `-0.0` |
| `"String"` | string, or `None` for `null` | `Objects.equals` (two nulls are equal) |
| `"array"` | an integer **identity** | arrays are compared by **reference**: equal only if the identities are the same |
| `"record"` | a nested record value | that record's `equals`, recursively |

Write `records_equal(a, b)` returning a boolean. Two records of the same type always have the same number
and kinds of components.

**Examples**
`records_equal(["Point", [["int", 1], ["int", 2]]], ["Point", [["int", 1], ["int", 2]]])` → `True`;
`records_equal(["Size", [["int", 1]]], ["Point", [["int", 1]]])` → `False`;
`records_equal(["T", [["double", "NaN"]]], ["T", [["double", "NaN"]]])` → `True`.
""",
    starter='''def records_equal(a, b):
    pass
''',
    solution='''def records_equal(a, b):
    if a[0] != b[0] or len(a[1]) != len(b[1]):
        return False
    for (kind, x), (_, y) in zip(a[1], b[1]):
        if kind == "double":
            if x == "NaN" or y == "NaN":
                if x != y:
                    return False
            elif float(x) != float(y) or x.startswith("-") != y.startswith("-"):
                return False
        elif kind == "record":
            if not records_equal(x, y):
                return False
        elif x != y:
            return False
    return True
''',
    tests=[
        [["Point", [["int", 1], ["int", 2]]], ["Point", [["int", 1], ["int", 2]]]],
        [["Size", [["int", 1]]], ["Point", [["int", 1]]]],
        [["T", [["double", "NaN"]]], ["T", [["double", "NaN"]]]],
        [["T", [["double", "0.0"]]], ["T", [["double", "-0.0"]]]],
        [["T", [["double", "1.50"]]], ["T", [["double", "1.5"]]]],
        [["P", [["String", None]]], ["P", [["String", None]]]],
        [["P", [["String", None]]], ["P", [["String", ""]]]],
        [["A", [["array", 1]]], ["A", [["array", 2]]]],
        [["A", [["array", 7]]], ["A", [["array", 7]]]],
        [["Line", [["record", ["Point", [["int", 0], ["int", 0]]]], ["record", ["Point", [["int", 3], ["int", 4]]]]]],
         ["Line", [["record", ["Point", [["int", 0], ["int", 0]]]], ["record", ["Point", [["int", 3], ["int", 4]]]]]]],
        [["Line", [["record", ["Point", [["int", 0], ["int", 0]]]], ["record", ["Point", [["int", 3], ["int", 4]]]]]],
         ["Line", [["record", ["Point", [["int", 0], ["int", 0]]]], ["record", ["Point", [["int", 3], ["int", 5]]]]]]],
        [["E", []], ["E", []]],
        [["T", [["double", "NaN"]]], ["T", [["double", "1.0"]]]],
        [["W", [["record", ["A", [["array", 1]]]]]], ["W", [["record", ["A", [["array", 1]]]]]]],
    ],
    wrong_solutions=[
        '''def records_equal(a, b):
    return a == b
''',
        '''def records_equal(a, b):
    if a[0] != b[0]:
        return False
    for (kind, x), (_, y) in zip(a[1], b[1]):
        if kind == "double":
            if float(x) != float(y):
                return False
        elif kind == "record":
            if not records_equal(x, y):
                return False
        elif x != y:
            return False
    return True
''',
    ],
    guide=G(
        "Lessons *Classes and objects* (records) and *Writing equals and hashCode correctly*.",
        "A record is equal to another record of the same class when all components match, and each component "
        "kind has its own notion of 'match'. The surprises are `double` (bitwise-style comparison) and arrays "
        "(identity, not contents).",
        ["Different type names are never equal, even with identical components.",
         "For doubles: handle `NaN` first; then compare numerically **and** compare the signs to tell 0.0 from -0.0.",
         "Recurse for nested records."],
        "Python's `==` on the nested lists compares the double strings as text (`\"1.50\"` vs `\"1.5\"`) and so "
        "gets numerically equal doubles wrong.",
        r"""**Dry run** `T(0.0)` vs `T(-0.0)`: neither is NaN; `0.0 == -0.0` numerically, but one text starts with
`-` and the other does not → **False**. Java's `Double.compare(0.0, -0.0)` is not 0, which keeps `equals`
consistent with `hashCode`.

```java
record Point(int x, int y) { }
record Reading(double value) { }
record Blob(int[] data) { }

System.out.println(new Point(1, 2).equals(new Point(1, 2)));                       // true
System.out.println(new Reading(Double.NaN).equals(new Reading(Double.NaN)));      // true
System.out.println(new Reading(0.0).equals(new Reading(-0.0)));                   // false
System.out.println(new Blob(new int[] {1}).equals(new Blob(new int[] {1})));      // false: arrays compare by identity

record SafeBlob(java.util.List<Integer> data) {               // use a List for value equality
    SafeBlob { data = java.util.List.copyOf(data); }          // canonical constructor copies defensively
}
```""",
        "Time O(total number of components, including nested ones), space O(nesting depth).",
        "- Comparing only the components and ignoring the record type.\n- `NaN != NaN` and `0.0 == -0.0`, the primitive `==` rules.\n"
        "- Expecting two arrays with equal contents to make records equal.",
    ),
),
# ------------------------------------------------------------------ java-immutable-audit
dict(
    id="java-immutable-audit",
    title="Immutable class audit",
    difficulty="Medium",
    pattern="Java classes",
    entry="audit",
    description=r"""
Check a class description against the five rules for immutable classes.

`cls` is a dictionary:

```
{"final_class": bool, "private_constructors": bool, "setters": [field names with a setter],
 "fields": [{"name": str, "final": bool, "private": bool, "mutable_type": bool,
             "copied_in": bool, "getter": "none" | "direct" | "copy"}, ...]}
```

`mutable_type` says the field refers to a mutable object (an array, a `List`, a `Date`). `copied_in` says
the constructor stores a defensive copy. `getter` says whether a getter exists and whether it returns the
field itself or a copy.

Write `audit(cls)` returning the **sorted** list of violation codes:

| code | when |
|---|---|
| `"SUBCLASSABLE"` | the class is not final **and** its constructors are not all private |
| `"SETTER:<name>"` | for each name in `setters` |
| `"NONFINAL:<name>"` | the field is not final |
| `"NONPRIVATE:<name>"` | the field is not private |
| `"NOCOPYIN:<name>"` | `mutable_type` and not `copied_in` |
| `"LEAK:<name>"` | `mutable_type` and the getter is `"direct"`; **or** `mutable_type` and the field is not private |

`copied_in` and `getter` are ignored for fields of immutable type. An empty list means the class is immutable.
""",
    starter='''def audit(cls):
    pass
''',
    solution='''def audit(cls):
    out = set()
    if not cls["final_class"] and not cls["private_constructors"]:
        out.add("SUBCLASSABLE")
    for s in cls["setters"]:
        out.add("SETTER:" + s)
    for f in cls["fields"]:
        n = f["name"]
        if not f["final"]:
            out.add("NONFINAL:" + n)
        if not f["private"]:
            out.add("NONPRIVATE:" + n)
        if f["mutable_type"]:
            if not f["copied_in"]:
                out.add("NOCOPYIN:" + n)
            if f["getter"] == "direct" or not f["private"]:
                out.add("LEAK:" + n)
    return sorted(out)
''',
    tests=[
        [{"final_class": True, "private_constructors": False, "setters": [],
          "fields": [{"name": "name", "final": True, "private": True, "mutable_type": False, "copied_in": False, "getter": "direct"},
                     {"name": "tracks", "final": True, "private": True, "mutable_type": True, "copied_in": False, "getter": "direct"}]}],
        [{"final_class": True, "private_constructors": False, "setters": [],
          "fields": [{"name": "name", "final": True, "private": True, "mutable_type": False, "copied_in": False, "getter": "direct"},
                     {"name": "tracks", "final": True, "private": True, "mutable_type": True, "copied_in": True, "getter": "copy"}]}],
        [{"final_class": False, "private_constructors": False, "setters": ["name"],
          "fields": [{"name": "name", "final": False, "private": True, "mutable_type": False, "copied_in": False, "getter": "direct"}]}],
        [{"final_class": False, "private_constructors": True, "setters": [], "fields": []}],
        [{"final_class": False, "private_constructors": False, "setters": [], "fields": []}],
        [{"final_class": True, "private_constructors": False, "setters": [],
          "fields": [{"name": "when", "final": True, "private": False, "mutable_type": True, "copied_in": True, "getter": "none"}]}],
        [{"final_class": True, "private_constructors": False, "setters": [],
          "fields": [{"name": "when", "final": True, "private": True, "mutable_type": True, "copied_in": True, "getter": "none"}]}],
        [{"final_class": True, "private_constructors": False, "setters": [],
          "fields": [{"name": "when", "final": True, "private": True, "mutable_type": True, "copied_in": False, "getter": "copy"}]}],
        [{"final_class": True, "private_constructors": True, "setters": ["b", "a"],
          "fields": [{"name": "a", "final": False, "private": False, "mutable_type": False, "copied_in": False, "getter": "none"},
                     {"name": "b", "final": True, "private": True, "mutable_type": False, "copied_in": False, "getter": "copy"}]}],
        [{"final_class": True, "private_constructors": False, "setters": [],
          "fields": [{"name": "x", "final": True, "private": True, "mutable_type": False, "copied_in": False, "getter": "direct"}]}],
        [{"final_class": False, "private_constructors": False, "setters": ["z"],
          "fields": [{"name": "z", "final": False, "private": False, "mutable_type": True, "copied_in": False, "getter": "direct"}]}],
    ],
    wrong_solutions=[
        '''def audit(cls):
    out = set()
    if not cls["final_class"]:
        out.add("SUBCLASSABLE")
    for s in cls["setters"]:
        out.add("SETTER:" + s)
    for f in cls["fields"]:
        n = f["name"]
        if not f["final"]: out.add("NONFINAL:" + n)
        if not f["private"]: out.add("NONPRIVATE:" + n)
        if f["mutable_type"]:
            if not f["copied_in"]: out.add("NOCOPYIN:" + n)
            if f["getter"] == "direct" or not f["private"]: out.add("LEAK:" + n)
    return sorted(out)
''',
        '''def audit(cls):
    out = set()
    if not cls["final_class"] and not cls["private_constructors"]:
        out.add("SUBCLASSABLE")
    for s in cls["setters"]:
        out.add("SETTER:" + s)
    for f in cls["fields"]:
        n = f["name"]
        if not f["final"]: out.add("NONFINAL:" + n)
        if not f["private"]: out.add("NONPRIVATE:" + n)
        if not f["copied_in"]: out.add("NOCOPYIN:" + n)
        if f["getter"] == "direct": out.add("LEAK:" + n)
    return sorted(out)
''',
    ],
    guide=G(
        "Lesson *Minimal accessibility and immutable classes*: the five rules.",
        "Immutability is a checklist. Translate each rule into one condition and collect the codes for every "
        "condition that fails.",
        ["Start with the class-level rules: subclassing and setters.", "Then loop over the fields for `final` and `private`.",
         "The copy rules apply only to fields of mutable types: copy on the way in, and never hand out the original."],
        "There is nothing to optimise; the risk is misreading a rule, such as applying the defensive-copy "
        "requirement to a `String` field.",
        r"""**Dry run** a `Playlist` with `private final String name` and `private final List<String> tracks`
stored without copying and returned directly. Class is final, no setters, both fields final and private.
`name` is immutable: nothing more to check. `tracks` is mutable: not copied in → `NOCOPYIN:tracks`; getter
direct → `LEAK:tracks`. Result `["LEAK:tracks", "NOCOPYIN:tracks"]`.

```java
public final class Playlist {                                  // 2. no subclasses
    private final String name;                                 // 3. final   4. private
    private final java.util.List<String> tracks;

    public Playlist(String name, java.util.List<String> tracks) {
        this.name = java.util.Objects.requireNonNull(name);
        this.tracks = java.util.List.copyOf(tracks);           // 5. defensive copy in (and unmodifiable)
    }

    public String name()                    { return name; }
    public java.util.List<String> tracks()  { return tracks; } // safe: cannot be modified
    public Playlist withTrack(String t) {                      // 1. no mutators: return a new object
        var copy = new java.util.ArrayList<>(tracks);
        copy.add(t);
        return new Playlist(name, copy);
    }
}
```""",
        "Time O(number of fields), space O(number of violations).",
        "- Flagging a non-final class whose constructors are all private (it cannot be subclassed from outside).\n"
        "- Demanding copies for immutable field types.\n- Forgetting that a non-private mutable field is itself a leak.",
    ),
),
]
