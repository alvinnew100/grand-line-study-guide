# Java essentials

## Before this lesson

> **Before this lesson:** You should know what a class, an object and inheritance are ([Object-oriented design questions](#/lesson/interview-prep/object-oriented-design)) and be able to read short Python programs. You do not need to have written Java. The previous lesson, [C and C++ essentials](#/lesson/interview-prep/c-cpp-essentials), introduced knowledge-based questions and the difference between static and dynamic types; this lesson uses both ideas. To learn Java properly from zero, the Java track starts at [From source to JVM](#/lesson/java/java-source-to-jvm).

## In plain words

**Java** is a programming language in which every variable has a declared type, the code is checked by a **compiler** (a program that translates source code and rejects mistakes before anything runs), and the result runs on the **Java Virtual Machine** or **JVM** (a program that executes compiled Java on any operating system and manages memory for you).

Picture two ways of sending a parcel. In the first, you scribble an address on any box and hand it over; if the address is wrong you find out days later when the parcel comes back. That is Python: flexible, quick to write, and mistakes with types show up while the program is running. In the second, a clerk checks the form at the counter: postcode present, weight declared, customs box ticked. Filling in the form takes longer, but most mistakes are caught before the parcel leaves. That is Java. The clerk is the compiler, and the form is the type declarations.

Why it matters for a job: Java runs a large share of back-end systems at banks, e-commerce firms, logistics platforms and government agencies, so many roles list it. If Java is on your resume, interviewers ask **knowledge-based questions** about it: short questions on how the language behaves, such as "what is the difference between overloading and overriding?". They are checking that the word on your resume is backed by understanding. This lesson covers the questions asked most often, shows the Java, and explains each piece for someone who thinks in Python.

Java code here is shown in static blocks (not runnable in the browser). Each idea is followed by a runnable Python demo that reproduces the behaviour.

## Reading Java when you know Python

Here is one small class in both languages.

```java
public class Parcel {
    private final int grams;              // a field: every Parcel has its own grams

    public Parcel(int grams) {            // constructor: same name as the class
        this.grams = grams;
    }

    public boolean isHeavy() {            // method returning true or false
        return grams > 2000;
    }
}
```

Line by line:

- `public class Parcel {` starts a class that any other code may use. Curly braces mark where blocks begin and end; indentation is for humans only.
- `private final int grams;` declares a **field** (Python: an attribute). `int` is its type: a 32-bit whole number. `private` means only code inside `Parcel` may touch it. `final` means it can be assigned once.
- `public Parcel(int grams)` is the **constructor**, the code that runs when an object is created. Python spells it `__init__`.
- `this.grams = grams;` copies the parameter into the field. `this` plays the role of Python's `self`, but is not listed as a parameter. Statements end with a semicolon.
- `public boolean isHeavy()` declares a method whose result type is `boolean` (`true` or `false`, lower case).

Creating and using an object: `Parcel p = new Parcel(450);` then `p.isHeavy()`. The variable `p` has the **declared type** (also called static type) `Parcel`; the compiler refuses `p.fly()` because `Parcel` has no such method. Python would let that line run and fail at that moment.

| Python | Java | Note |
|---|---|---|
| `x = 5` | `int x = 5;` | The type is declared and cannot change |
| `self` | `this` | Implicit in Java |
| `__init__` | constructor named after the class | |
| `None` | `null` | Only for object types, not for `int` |
| `list` | `ArrayList<T>` | `T` is the element type |
| `dict` | `HashMap<K, V>` | |
| `a == b` on strings | `a.equals(b)` | In Java `==` on objects asks "same object?" |
| `class B(A)` | `class B extends A` | One parent class only |
| duck typing | `interface` + `implements` | A named promise of methods |

Java has two families of types. **Primitive types** (`int`, `long`, `double`, `boolean`, `char` and a few more) hold a plain value. **Reference types** (every class, including `String`, `Integer` and all collections) hold a reference to an object, or `null`. Python has only the second family.

## How to answer a knowledge question

The shape from the previous lesson applies unchanged: **define it in one sentence, say how it works underneath, say when it matters**. If you do not know, say so and reason aloud from what you do know. A wrong answer delivered confidently costs more than "I have not used that; here is how I would expect it to behave, and why".

## Overloading and overriding

The names are similar and the mechanisms are different.

**Overloading** means several methods in one class share a name and differ in their parameter lists. The compiler picks one by looking at the declared types of the arguments. The choice is fixed at **compile time**.

**Overriding** means a subclass supplies its own body for a method that it inherits, with the same name and the same parameters. The JVM picks the body by looking at the real class of the object. The choice is made at **run time**.

```java
class Parcel {}
class FragileParcel extends Parcel {}

class Courier {
    String handle(Parcel p)        { return "Courier handles a parcel"; }
    String handle(FragileParcel p) { return "Courier handles a FRAGILE parcel"; }   // overload
}

class BikeCourier extends Courier {
    @Override
    String handle(Parcel p)        { return "BikeCourier straps a parcel to the rack"; }  // override
}
```

`Courier` has two methods called `handle`: that is overloading. `BikeCourier` replaces one of them: that is overriding. The marker `@Override` is an **annotation**, a label for the compiler; it asks the compiler to complain if the method does not in fact override anything, which catches spelling mistakes.

Now the question interviewers love:

```java
Courier c = new BikeCourier();
Parcel p = new FragileParcel();
c.handle(p);        // which of the three bodies runs?
```

Work in two steps. Step 1, compile time: the argument's declared type is `Parcel`, so the compiler commits to the signature `handle(Parcel)`. The fact that the object is really fragile is invisible to it. Step 2, run time: the receiver object is really a `BikeCourier`, which overrides `handle(Parcel)`, so the bike version runs. The fragile overload is never considered.

Python has overriding and no overloading: a second `def handle` in the same class replaces the first. So the demo below models both steps explicitly.

```python-run
PARCEL_PARENT = {"Parcel": None, "FragileParcel": "Parcel"}
COURIER_PARENT = {"Courier": None, "BikeCourier": "Courier"}

# class -> {signature: what that body prints}
METHODS = {
    "Courier": {
        ("handle", "Parcel"): "Courier handles a parcel",
        ("handle", "FragileParcel"): "Courier handles a FRAGILE parcel",
    },
    "BikeCourier": {
        ("handle", "Parcel"): "BikeCourier straps a parcel to the rack",
    },
}

def pick_overload(receiver_declared, name, arg_declared):
    """Compile time: the most specific signature that accepts the argument's DECLARED type."""
    arg_type = arg_declared
    while arg_type is not None:
        cls = receiver_declared
        while cls is not None:
            if (name, arg_type) in METHODS[cls]:
                return (name, arg_type)
            cls = COURIER_PARENT[cls]
        arg_type = PARCEL_PARENT[arg_type]
    raise TypeError("does not compile")

def pick_override(receiver_real, signature):
    """Run time: the nearest body for that signature, starting at the receiver's REAL class."""
    cls = receiver_real
    while signature not in METHODS[cls]:
        cls = COURIER_PARENT[cls]
    return METHODS[cls][signature]

def call(receiver_declared, receiver_real, arg_declared, arg_real):
    signature = pick_overload(receiver_declared, "handle", arg_declared)
    body = pick_override(receiver_real, signature)
    print(f"{receiver_declared} c = new {receiver_real}();  {arg_declared} p = new {arg_real}();")
    print(f"    c.handle(p) -> handle({signature[1]}) -> {body}")

call("Courier", "Courier", "FragileParcel", "FragileParcel")
call("Courier", "Courier", "Parcel", "FragileParcel")
call("Courier", "BikeCourier", "Parcel", "FragileParcel")
call("Courier", "BikeCourier", "FragileParcel", "FragileParcel")
```

`pick_overload` starts from the argument's declared type and climbs to its parent until some class in the receiver's declared hierarchy has a matching signature. `pick_override` starts from the receiver's real class and climbs until it finds a body. The second line of output is the surprise: a fragile parcel held in a `Parcel` variable is treated as an ordinary parcel. The fourth shows the other half: `BikeCourier` did not override the fragile signature, so the inherited `Courier` body runs.

| | Overloading | Overriding |
|---|---|---|
| Where | Same class (or inherited), same name, different parameters | Subclass, same name, same parameters |
| Decided | At compile time, from declared argument types | At run time, from the object's real class |
| Purpose | Convenience: one name for related operations | Polymorphism: subclasses change behaviour |
| Return type alone can differ? | No, that does not compile | Must be the same type or a subtype |

Two details that come up as follow-ups: `static` methods and `private` methods cannot be overridden (a subclass method with the same name is a separate method), and fields are never chosen by the real class, only methods are.

## The collections framework

The **collections framework** is Java's standard library of data structures. Each structure is an **interface** (a named list of operations, such as `List`, `Map`, `Set`, `Queue`) with one or more implementations that make different trade-offs. Knowing which implementation to pick, and its costs, is the most useful Java knowledge for coding rounds.

| Java class | What it is underneath | Python counterpart | Costs to remember |
|---|---|---|---|
| `ArrayList` | Resizable array | `list` | Index O(1); append O(1) amortised; insert at front O(n) |
| `LinkedList` | Doubly linked list | `collections.deque` (roughly) | Add or remove at either end O(1); index O(n) |
| `ArrayDeque` | Circular array | `collections.deque` | Stack and queue operations O(1); the preferred stack |
| `HashMap` | Hash table | `dict` (without the ordering) | Get and put O(1) on average |
| `LinkedHashMap` | Hash table plus a linked list through the entries | `dict` | As `HashMap`; iterates in insertion order |
| `TreeMap` | Red-black tree, a self-balancing search tree | no built-in; `bisect` on a sorted list | Get and put O(log n); keys always sorted |
| `HashSet`, `TreeSet` | A `HashMap` or `TreeMap` that keeps only keys | `set` | As the matching map |
| `PriorityQueue` | Binary heap, smallest first | `heapq` | Add and remove-smallest O(log n) |

A frequent question is the difference between the three maps. All three store key-value pairs; they differ in the order in which a loop over the keys visits them, and in cost.

- `HashMap`: no promised order. The order comes from which **bucket** (slot of the internal array) each key's hash code lands in, and can change when the table grows.
- `LinkedHashMap`: the order in which keys were first inserted. It can also be switched to "least recently accessed first", which makes a least-recently-used cache a few lines long.
- `TreeMap`: ascending key order, always. Because the keys are in a search tree it can also answer neighbour questions: `floorKey(x)` is the largest key not above `x`, `ceilingKey(x)` the smallest key not below it.

```python-run
entries = [("mango", 3), ("apple", 7), ("kiwi", 2), ("banana", 5), ("cherry", 1)]

# LinkedHashMap keeps insertion order. A Python dict behaves the same way.
linked = {}
for key, value in entries:
    linked[key] = value
print("LinkedHashMap order:", list(linked))

# TreeMap hands the keys out in sorted order.
print("TreeMap order:      ", sorted(linked))

# HashMap order follows the buckets. This reproduces Java's own arithmetic.
def java_string_hash(s):
    h = 0
    for ch in s:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF      # keep 32 bits, as a Java int does
    return h

def bucket_of(s, table_size=16):
    h = java_string_hash(s)
    h ^= h >> 16                                  # HashMap folds the high bits into the low bits
    return h & (table_size - 1)

buckets = {}
for key, _ in entries:
    buckets.setdefault(bucket_of(key), []).append(key)
print("HashMap buckets:    ", dict(sorted(buckets.items())))
print("HashMap order:      ", [key for b in sorted(buckets) for key in buckets[b]])
```

`java_string_hash` is the formula Java uses for strings: multiply the running value by 31 and add the next character's code, keeping 32 bits. `bucket_of` applies the extra mixing step `HashMap` performs and keeps the lowest four bits, because a new `HashMap` has 16 buckets. Looping over a `HashMap` walks the buckets from 0 upward, which is the last line printed. It matches neither insertion order nor alphabetical order, and that is the point: never write code that depends on it.

**The `equals` and `hashCode` contract.** A `HashMap` finds a key in two moves: `hashCode()` selects the bucket, then `equals()` compares against the keys in that bucket. So two objects that are equal must return the same hash code, otherwise the map looks in the wrong bucket and reports a key missing while it is sitting in the table. If you override one of the two methods in your own class, override the other. Python has the same rule for `__eq__` and `__hash__`. The Java track covers it in depth in [equals and hashCode](#/lesson/java/java-ej-equals-hashcode).

The practice problem [Ordered Ledger](#/problem/ctci-ordered-ledger) asks you to build the neighbour queries of a `TreeMap` in Python.

## Ordering objects: Comparable and Comparator

Sorting needs one fact: given two items, which comes first? For numbers and strings Java already knows. For your own class, such as a `Parcel` with a weight and a destination, you must say. Java gives you two ways, and interviewers like asking for the difference.

**`Comparable<T>`: the class knows its own natural order.** The class implements one method, `compareTo`. It returns a negative number if `this` comes first, zero if they are tied, and a positive number if `this` comes later. Once a class does this, `Collections.sort(list)`, `Arrays.sort(array)`, `TreeSet` and `TreeMap` can order it with no further instructions. A class can have only one `compareTo`, so there is only one "natural" order.

**`Comparator<T>`: a separate judge.** A comparator is a different object (often a lambda) with the method `compare(a, b)`, returning a number by the same rules. You hand it to the sorting call, so you can sort the same class many ways without touching it, and you can sort classes you cannot edit.

```java
class Parcel implements Comparable<Parcel> {
    final String city;
    final int grams;
    Parcel(String city, int grams) { this.city = city; this.grams = grams; }

    @Override
    public int compareTo(Parcel other) {          // natural order: lightest first
        return Integer.compare(this.grams, other.grams);
    }
}

List<Parcel> parcels = loadParcels();
Collections.sort(parcels);                         // uses compareTo

// Other orders, chosen at the call site:
parcels.sort(Comparator.comparing((Parcel p) -> p.city)
                       .thenComparing(p -> p.grams, Comparator.reverseOrder()));
```

- `Integer.compare(x, y)` is used instead of `x - y`. Subtraction can overflow for large values and then flip the sign, giving a silently wrong order.
- `Comparator.comparing(...)` builds a comparator from a "sort key" function; `thenComparing` breaks ties; `.reversed()` flips the order.
- Python parallel: `compareTo` is like defining `__lt__` on a class, and a `Comparator` is like the `key=` function given to `sorted`. Python's tools compare keys; Java's compare pairs directly.

```python-run
from functools import cmp_to_key

parcels = [("Oslo", 900), ("Bern", 300), ("Oslo", 150), ("Bern", 700)]

def by_city_then_heavy_first(a, b):
    # a comparator: negative = a first, zero = tie, positive = b first
    if a[0] != b[0]:
        return -1 if a[0] < b[0] else 1
    return b[1] - a[1]

print(sorted(parcels, key=cmp_to_key(by_city_then_heavy_first)))
print(sorted(parcels, key=lambda p: (p[0], -p[1])))      # same order, written as a key
```

Both lines print the same order. `cmp_to_key` shows that Java's comparator style and Python's key style describe the same thing.

**The consistency trap.** `TreeSet` and `TreeMap` treat `compareTo` returning zero as "same element", ignoring `equals`. Java's `BigDecimal("1.0")` and `BigDecimal("1.00")` are not `equals` but compare as zero, so a `HashSet` keeps both while a `TreeSet` keeps one. The advice is to keep `compareTo` consistent with `equals`, and to say so when you know it is not.

> [!INTERVIEW]
> "Comparable or Comparator?" Answer: Comparable is the one built-in order inside the class; Comparator is an external order passed in, so there can be many and the class need not change. Mention `Integer.compare` over subtraction.

## Iterators, Iterable and the fail-fast rule

An **iterator** is an object that walks through a collection one item at a time. It has three methods: `hasNext()` ("is there another item?"), `next()` ("give me the next item and move on") and an optional `remove()` ("delete the item you just gave me"). An **`Iterable`** is anything that can hand out a fresh iterator through a method `iterator()`. Every collection is `Iterable`, and the `for (X x : things)` loop works on exactly the things that are. Write your own `Iterable` class and the enhanced `for` works on it too.

In Python terms: an `Iterable` is an object with `__iter__`, an `Iterator` is the object with `__next__`, and Java's for-each is Python's `for` loop. The difference is the ending: Python's `next` raises `StopIteration`, whereas Java asks `hasNext()` first.

```java
List<String> names = new ArrayList<>(List.of("ana", "bo", "cy", "di"));

Iterator<String> it = names.iterator();
while (it.hasNext()) {
    String n = it.next();
    if (n.length() == 2) it.remove();        // safe: removal done by the iterator itself
}
```

**Fail-fast iterators.** Now suppose you remove an item with `names.remove(n)` inside a for-each loop. The loop's hidden iterator did not know about that change, so it could skip items or return stale ones. To catch this class of bug, collections such as `ArrayList` and `HashMap` keep a **modification count**, a counter that goes up each time the collection's structure changes (an item added or removed; replacing an item's value does not count). Each iterator remembers the count when it was created and checks it on every `next()`. If the numbers differ, the iterator throws **`ConcurrentModificationException`**. Such an iterator is called **fail-fast**: it fails immediately and loudly rather than carrying on with doubtful data.

The name misleads. You do not need two threads to trigger it: the single-threaded loop above is the usual cause. Equally, fail-fast is only a best-effort bug detector, not a thread-safety tool; with real concurrent modification it may not fire. A well-known quirk: removing the second-to-last item of an `ArrayList` inside a for-each loop happens not to throw, because `hasNext()` then reports "no more" before the check is reached.

```python-run
class TinyList:
    """A toy list that mimics Java's fail-fast behaviour with a modification count."""
    def __init__(self, items):
        self.items = list(items)
        self.mod_count = 0

    def remove(self, value):
        self.items.remove(value)
        self.mod_count += 1                       # a structural change

    def iterator(self):
        expected = self.mod_count                 # the iterator remembers the count
        pos = 0
        while pos < len(self.items):
            if self.mod_count != expected:
                raise RuntimeError("ConcurrentModificationException")
            yield self.items[pos]
            pos += 1

names = TinyList(["ana", "bo", "cy", "di"])
try:
    for n in names.iterator():
        if len(n) == 2:
            names.remove(n)                       # changes the list behind the iterator's back
except RuntimeError as e:
    print("caught:", e)

safe = [n for n in ["ana", "bo", "cy", "di"] if len(n) != 2]   # build a new list instead
print(safe)
```

**How to avoid it:** use the iterator's own `remove()`, or `list.removeIf(predicate)`, or build a new list of the survivors, or loop over a copy. For collections truly shared between threads use `CopyOnWriteArrayList` or `ConcurrentHashMap`, whose iterators never throw this exception; they are *weakly consistent*, meaning they may or may not show changes made after they were created.

## Generics

A **generic** class or method is written with a placeholder for a type, filled in where it is used. `ArrayList<String>` is a list that holds strings; `HashMap<String, Integer>` maps strings to whole numbers.

```java
List<String> names = new ArrayList<>();
names.add("Wei");
names.add(42);                 // compile error: 42 is not a String
String first = names.get(0);   // no cast needed: the compiler knows the element type
```

The benefit is that a wrong element type is rejected by the compiler instead of blowing up later. The `<>` on the right is shorthand: the compiler fills in `String` from the left-hand side.

How it works underneath is the part interviewers probe. Java implements generics by **type erasure**: the compiler checks the types, inserts the casts for you, and then removes the type arguments. At run time `ArrayList<String>` and `ArrayList<Integer>` are the same class, `ArrayList`. Consequences:

- You cannot ask `if (x instanceof List<String>)`; the information is gone.
- You cannot write `new T()` or `new T[10]` inside a generic class.
- Type arguments must be reference types: `List<int>` is illegal, `List<Integer>` is used instead. `Integer` is the **wrapper class** for `int`, and Java converts between them automatically (**autoboxing**).
- A `static` field of a generic class is shared by all its uses, because there is only one class.

**Compared with C++ templates.** A C++ template is a recipe from which the compiler generates a separate copy of the code for each type used, so `Stack<int>` and `Stack<string>` are two unrelated classes, primitives work, and each has its own static members. Java has one compiled class and a compile-time check. If asked "are Java generics the same as C++ templates?", the answer is "similar syntax, different mechanism: erasure versus code generation", followed by two of the consequences above.

**Wildcards**, briefly. `List<? extends Number>` means "a list of some unknown subtype of `Number`": you can read numbers from it and cannot add to it. `List<? super Integer>` means "a list of some supertype of `Integer`": you can add integers to it. The details are in [Generics](#/lesson/java/java-generics).

Python's type hints (`list[int]`) are close cousins of erased generics: a separate checker reads them, and the running program ignores them.

```python-run
def compile_check(element_type, operations):
    """Play the Java compiler: reject a wrong element type before anything runs."""
    for op, value in operations:
        if op == "add" and type(value).__name__ != element_type:
            return f"compile error: cannot add {type(value).__name__} to List<{element_type}>"
    return "compiles"

program_a = [("add", 4), ("add", 9)]
program_b = [("add", 4), ("add", "nine")]
print("program A as List<int>:", compile_check("int", program_a))
print("program B as List<int>:", compile_check("int", program_b))

# After the check, the type argument is erased: at run time both are plain lists.
numbers = [4, 9]             # think List<Integer>
words = ["four", "nine"]     # think List<String>
print("same class at run time?", type(numbers) is type(words))
```

`compile_check` inspects a program before running it and refuses the one that adds a string to a list of integers. The last line shows what "erased" means: once checking is done, nothing in the running objects records the element type.

## final, finally and finalize

Three words that look related and are not. This is a classic warm-up question.

**`final`** is a keyword meaning "cannot be changed", and what cannot change depends on where it is written.

- On a variable or field: it can be assigned once. For a reference type, the *reference* is fixed, not the object: `final List<String> xs = new ArrayList<>();` forbids `xs = otherList;` and allows `xs.add("a")`.
- On a method: subclasses cannot override it.
- On a class: nobody can extend it. `String` is a final class.

**`finally`** is a block attached to `try`. It runs when the `try` block is left, however it is left: normally, by an exception, or by `return`. It is where cleanup goes (closing a file, releasing a lock).

```java
static String readSetting() {
    try {
        return "from try";
    } finally {
        System.out.println("cleanup runs before the method really returns");
    }
}
```

The follow-up question is "does `finally` run if `try` contains a `return`?" Yes: the return value is computed, then `finally` runs, then the method returns. It does not run only when the whole JVM stops first (for example `System.exit()` is called, the machine loses power, or the thread is stuck forever inside `try`). Python's `try`/`finally` has the same rules, so this demo is the real thing, not a simulation:

```python-run
def read_setting():
    try:
        print("  try: about to return")
        return "from try"
    finally:
        print("  finally: runs although try already said return")

print("result:", read_setting())

def overridden():
    try:
        return "from try"
    finally:
        return "from finally"       # legal, and a bad idea: it replaces the earlier value

print("result:", overridden())

def swallowed():
    try:
        raise ValueError("disk full")
    finally:
        return "the exception vanished"   # a return here also discards the exception

print("result:", swallowed())
```

The first function prints its `finally` message before the caller receives the value. The second and third show why a `return` inside `finally` is discouraged in both languages: it silently replaces the value from `try`, and it even throws away an exception that was on its way out. (Recent Python versions print a warning for those two functions for exactly that reason.)

**`finalize`** is a method that the garbage collector could call on an object before reclaiming its memory. The **garbage collector** is the part of the JVM that finds objects no longer reachable from the program and frees them. `finalize` gives no promise about when it runs, or whether it runs at all, so it was never a safe place for cleanup; it has been deprecated since Java 9 and marked for removal since Java 18. The modern tool is **try-with-resources**: `try (Scanner in = new Scanner(file)) { ... }` closes `in` automatically at the end of the block, like Python's `with`.

| Word | Kind of thing | One-line meaning |
|---|---|---|
| `final` | Keyword on a variable, method or class | Assign once / cannot override / cannot extend |
| `finally` | Block after `try` | Runs whenever `try` is left |
| `finalize` | Method called by the garbage collector | Deprecated; do not rely on it |

## Access modifiers and the private constructor

| Modifier | Who may use the member |
|---|---|
| `private` | Code in the same class only |
| *(none)*, called package-private | Classes in the same package (folder of related classes) |
| `protected` | The same package, plus subclasses anywhere |
| `public` | Everyone |

"What does it mean to make a constructor private?" Nobody outside the class can write `new Thing()`. That has two effects: outside code cannot create instances directly, and outside classes cannot extend the class, because a subclass constructor must call a parent constructor. People do it for three reasons: to route creation through a `static` factory method that can validate or reuse objects; to guarantee one instance only (the singleton pattern from the design lesson); or to mark a class that holds only `static` helper methods and should never be instantiated.

`static` itself means "belongs to the class, not to any one object": a static field is shared by all instances, and a static method is called on the class (`Math.max(a, b)`) and has no `this`.

## Reflection

**Reflection** is a program's ability to examine and use its own classes at run time: list the methods of a class whose name arrived as a string, create an object without writing `new`, call a method chosen by name, even read a private field.

```java
Class<?> cls = Class.forName("shop.Parcel");                 // look a class up by name
Object obj = cls.getDeclaredConstructor(int.class).newInstance(450);
Method m = cls.getDeclaredMethod("isHeavy");                 // look a method up by name
Object answer = m.invoke(obj);                               // call it
```

Who uses this? Mostly frameworks: a test runner finds every method marked `@Test`; a web framework creates your controller objects and wires them together; a library converts objects to and from JSON by walking their fields. The costs are the answer to "why not use it everywhere?": the compiler can no longer check the names (a typo fails at run time), calls are slower, and `setAccessible(true)` breaks the privacy that `private` was meant to give.

Python is reflective by nature, so the same moves are short:

```python-run
class Parcel:
    def __init__(self, grams):
        self.grams = grams
    def weigh(self):
        return f"{self.grams} g"
    def _secret_route(self):
        return "via depot 7"

p = Parcel(450)
cls = type(p)                                     # Java: p.getClass()
print("class name:", cls.__name__)                # Java: cls.getName()
methods = [n for n in dir(cls) if callable(getattr(cls, n)) and not n.startswith("__")]
print("methods:", methods)                        # Java: cls.getDeclaredMethods()
wanted = "weigh"                                  # the method name arrives as text
print("call by name:", getattr(p, wanted)())      # Java: cls.getMethod(wanted).invoke(p)
print("reach a private one:", getattr(p, "_secret_route")())    # Java: setAccessible(true)
q = cls(120)                                      # Java: getDeclaredConstructor(...).newInstance(120)
print("built from the class object:", q.weigh())
```

`type(p)` returns the class object; `dir` lists its attribute names; `getattr` fetches one by name, and the trailing `()` calls it. The last two lines create a second parcel from the class object alone, with the word `Parcel` appearing nowhere on that line.

## Lambda expressions

A **lambda expression** is a small function written in place, without a name, so that behaviour can be passed as an argument. Java gained them in version 8.

```java
List<Order> orders = loadOrders();

int paidTotal = orders.stream()                       // view the list as a stream of items
        .filter(o -> o.status.equals("paid"))         // keep the paid ones
        .mapToInt(o -> o.cents)                       // turn each order into its amount
        .sum();

orders.sort((a, b) -> Integer.compare(b.cents, a.cents));   // largest first
```

`o -> o.status.equals("paid")` reads "given `o`, return whether its status is paid". A lambda with two parameters puts them in brackets: `(a, b) -> ...`. A **stream** is a pipeline that passes each element through the steps in turn.

Underneath, a Java lambda is an object that implements a **functional interface**: an interface with exactly one abstract method, such as `Predicate<T>` (takes a `T`, returns a boolean), `Function<T, R>` or `Comparator<T>`. The compiler works out which interface is wanted from the context. One rule to remember: a lambda may read local variables from the surrounding method only if they are **effectively final**, meaning never reassigned after their first value.

```python-run
orders = [("A17", "paid", 1250), ("A18", "open", 300), ("A19", "paid", 4999), ("A20", "paid", 80)]

# filter, then map, then sum: the same pipeline as the Java stream
paid_total = sum(map(lambda o: o[2], filter(lambda o: o[1] == "paid", orders)))
print("paid total in cents:", paid_total)

# a lambda as the sort rule, like the Java comparator
largest_first = sorted(orders, key=lambda o: o[2], reverse=True)
print("largest first:", [o[0] for o in largest_first])

# a lambda is a value: it can be stored in a variable and passed around
is_large = lambda o: o[2] >= 1000
print("large orders:", [o[0] for o in orders if is_large(o)])
```

Each `lambda o: ...` is a function of one order. `filter` keeps the orders for which the first lambda is true, `map` replaces each by its amount, and `sum` adds them: 1250 + 4999 + 80 = 6329.

## Building strings: StringBuilder versus StringBuffer

Because `String` is immutable (see the traps below), code that assembles text piece by piece uses a **mutable character buffer**: an object holding a growing array of characters that can be changed in place. Java has two with the same methods (`append`, `insert`, `reverse`, `deleteCharAt`, `toString`):

| | `StringBuffer` | `StringBuilder` |
|---|---|---|
| Since | Java 1.0 | Java 5 |
| Thread-safe | Yes: its methods are `synchronized` | No |
| Speed | Slower, because every call takes a lock | Faster |
| Use it | Rarely; legacy code or a buffer genuinely shared by threads | Almost always |

**Synchronized** means a lock is taken around the method so only one thread runs it at a time. Locking costs time even when only one thread exists, and most string building happens inside one method on one thread, so the lock buys nothing. That is why `StringBuilder` was added. Even when you do share a buffer, `StringBuffer` makes each call safe, not a sequence of calls: "check the length, then append" can still be interleaved by another thread, so you often need your own lock anyway.

```java
StringBuilder sb = new StringBuilder();
for (String word : words) {
    sb.append(word).append(' ');          // appends in place, amortised O(1) per character
}
String sentence = sb.toString().trim();
```

Compared with `s = s + word` in a loop (O(n²) overall, since each step copies everything so far), a builder is O(n) overall. The buffer grows by reallocating a larger array when full, which is the same trick as `ArrayList`'s resizing.

## Four short traps

**`==` and `equals`.** On primitives `==` compares values. On objects it asks whether two references point to the same object. `new String("hi") == new String("hi")` is `false`; `.equals` is `true`. Compare strings and wrapper objects with `equals`.

**The small-integer cache.** `Integer a = 127, b = 127;` gives `a == b` true, while the same lines with 128 give false, because Java reuses one object for each small value from −128 to 127 and creates fresh objects beyond that. The lesson is the previous trap again: use `equals`.

**Strings are immutable.** Every `s = s + x` in a loop builds a new string and copies the old one, which is O(n²) overall. `StringBuilder` appends in place; Python's equivalent habit is collecting pieces in a list and calling `"".join`.

**Checked and unchecked exceptions.** A **checked exception** (such as `IOException`) must be either caught or declared in the method's `throws` list, and the compiler enforces it. An **unchecked exception** (such as `NullPointerException`, any subclass of `RuntimeException`) needs no declaration. Python has only the unchecked kind.

## A worked question, start to finish

*"You need to store the prices of products and often ask for the cheapest product at or above a given budget floor. Which Java map would you use, and why not the others?"*

**Define.** "All three standard maps store key-value pairs. They differ in ordering and cost."

**Reason.** "The question is a neighbour query: the smallest key greater than or equal to a value. A `HashMap` cannot answer that without scanning every key, O(n), because hashing scatters keys with no regard to their size. A `LinkedHashMap` remembers insertion order, which is unrelated to price. A `TreeMap` keeps keys in a balanced search tree, so `ceilingKey(floor)` walks one path from the root: O(log n)."

**Trade-off.** "The price is that every insert and lookup is O(log n) instead of O(1) on average, and keys must be comparable. If we only ever looked prices up by exact product name, `HashMap` would be the better choice."

**Edge cases.** "`ceilingKey` returns `null` when no key is large enough, so the caller must check. Two products with the same price need a map from price to a list of products."

That answer names the structure, the reason, the cost and the edge cases in under a minute.

## Problems in this module and what each trains

| Problem | Skill |
|---|---|
| [Ordered Ledger](#/problem/ctci-ordered-ledger) | What a sorted map offers that a hash map cannot: floor and ceiling queries with binary search |

## Pitfalls

- **Mixing up overloading and overriding.** Overloading: same name, different parameters, compile time. Overriding: same signature in a subclass, run time.
- **Expecting an overload to be chosen by the real type of the argument.** It is chosen by the declared type.
- **Believing `final` makes an object unchangeable.** It fixes the reference; the object can still be modified unless its class forbids it.
- **Relying on `HashMap` iteration order**, or on `finalize` ever running.
- **Comparing strings or `Integer` objects with `==`.**
- **Overriding `equals` without `hashCode`.** Hash-based collections then lose your objects.
- **Saying generics exist at run time.** The type arguments are erased after compilation.
- **Reciting without reasoning.** A memorised definition followed by silence reads as shallow. Add how it works and when it matters.

> [!INTERVIEW]
> For any "difference between X and Y" question, give one sentence per item and then the axis on which they differ. "Overloading and overriding both reuse a method name. Overloading is resolved by the compiler from the argument types; overriding is resolved at run time from the object's class." Then offer a two-line example. Stop there and let the interviewer choose where to dig.

> [!TIP]
> If your Java is rusty, translate from what you know: "In Python a dict keeps insertion order; Java's `HashMap` does not promise that, and `LinkedHashMap` is the one that does." Showing that you can map concepts between languages is worth more than a memorised list.

> [!WARNING]
> Do not list Java on a resume as a strength unless you can answer everything in this lesson. "Familiar with" is an honest label and sets the right expectations.

## Summary

- Java is statically typed and compiled; the JVM runs the result and manages memory. Declared types let the compiler reject many mistakes early.
- Overloading is chosen at compile time from declared argument types; overriding is chosen at run time from the receiver's real class.
- Pick collections by need: `ArrayList` for indexed sequences, `ArrayDeque` for stacks and queues, `HashMap` for fast exact lookup, `LinkedHashMap` for insertion order, `TreeMap` for sorted keys and neighbour queries, `PriorityQueue` for repeated smallest-first removal.
- Generics give compile-time type checking and are erased afterwards; C++ templates generate separate code per type.
- `final` restricts change, `finally` always runs after `try`, `finalize` is obsolete.
- Reflection inspects and calls code by name at run time, at a cost in safety and speed. Lambdas are compact implementations of one-method interfaces.

## Glossary

- **Compiler**: a program that translates source code and reports errors before the program runs.
- **JVM (Java Virtual Machine)**: the program that executes compiled Java and manages its memory.
- **Declared (static) type**: the type written in a variable's declaration, which is what the compiler sees.
- **Primitive type**: a plain value type such as `int` or `boolean`, not an object.
- **Reference type**: a type whose variables hold a reference to an object, or `null`.
- **Overloading**: several methods with one name and different parameter lists; resolved at compile time.
- **Overriding**: a subclass replacing an inherited method's body; resolved at run time.
- **Annotation**: a label beginning with `@` that gives information to the compiler or to tools.
- **Collections framework**: Java's standard interfaces and classes for lists, sets, maps and queues.
- **Interface**: a named set of method signatures that a class promises to implement.
- **Bucket**: one slot of a hash table's internal array.
- **Generic**: a class or method written with a type placeholder.
- **Type erasure**: removal of generic type arguments after compile-time checking.
- **Wrapper class / autoboxing**: an object version of a primitive (`Integer` for `int`) / automatic conversion between the two.
- **Garbage collector**: the JVM component that frees objects the program can no longer reach.
- **Try-with-resources**: a `try` form that closes its resources automatically.
- **Reflection**: examining and using classes, methods and fields by name at run time.
- **Lambda expression**: an unnamed function written in place.
- **Functional interface**: an interface with exactly one abstract method, the target type of a lambda.
- **Effectively final**: a local variable that is never reassigned.
- **Checked exception**: an exception the compiler forces you to catch or declare.
- **`Comparable`**: an interface whose `compareTo` method gives a class its single natural order.
- **`Comparator`**: a separate object whose `compare` method orders two items; many can exist for one class.
- **Iterator / `Iterable`**: an object that walks a collection with `hasNext` and `next` / anything that can produce an iterator, and so works in for-each.
- **Modification count**: a counter a collection raises on each structural change, used by iterators to detect interference.
- **Fail-fast**: throwing `ConcurrentModificationException` at once when the collection changed behind an iterator's back.
- **Weakly consistent iterator**: an iterator of a concurrent collection that never throws that exception but may not show recent changes.
- **Mutable buffer**: an object holding characters that can be changed in place, such as `StringBuilder`.
- **Synchronized**: guarded by a lock so only one thread at a time runs the method.

```quiz
[
  {"q": "A class has methods handle(Parcel) and handle(FragileParcel). You write: Parcel p = new FragileParcel(); courier.handle(p); Which overload does the compiler choose?",
   "options": ["handle(FragileParcel), because the object is fragile", "handle(Parcel), because the declared type of p is Parcel", "Both run", "It does not compile"],
   "answer": 1,
   "explain": "Overloads are selected at compile time from the declared type of the argument. The real class of the object matters only for overriding."},
  {"q": "Which statement about overriding is correct?",
   "options": ["It is resolved at compile time", "It needs a different parameter list", "The body that runs is chosen at run time from the object's real class", "Static methods can be overridden"],
   "answer": 2,
   "explain": "Overriding keeps the signature and replaces the body in a subclass; the JVM dispatches on the real class. Static methods are hidden, not overridden."},
  {"q": "You need the keys of a map to come out in ascending order and to find the largest key not above a given value. Which class fits?",
   "options": ["HashMap", "LinkedHashMap", "TreeMap", "ArrayList"],
   "answer": 2,
   "explain": "TreeMap keeps keys in a balanced search tree: sorted iteration and floorKey/ceilingKey in O(log n)."},
  {"q": "What does type erasure mean for List<String> and List<Integer> at run time?",
   "options": ["They are two different classes", "They are the same class; the type arguments were removed after compile-time checking", "List<Integer> is faster", "Neither can hold null"],
   "answer": 1,
   "explain": "The compiler checks element types and inserts casts, then discards the type arguments, so only one class exists."},
  {"q": "A try block executes a return statement and has a finally block. What happens?",
   "options": ["finally is skipped", "finally runs, then the method returns", "The program crashes", "finally runs only if an exception was thrown"],
   "answer": 1,
   "explain": "finally runs whenever the try block is left, including by return. Only stopping the whole JVM first prevents it."},
  {"q": "final List<String> xs = new ArrayList<>(); Which line is rejected by the compiler?",
   "options": ["xs.add(\"a\");", "xs.clear();", "xs = new ArrayList<>();", "xs.size();"],
   "answer": 2,
   "explain": "final fixes the reference, so xs cannot be pointed at another list. The list object itself can still be modified."},
  {"q": "Why is reflection used sparingly in application code?",
   "options": ["It cannot call methods", "Names are checked only at run time, calls are slower, and it can bypass private", "It only works on primitives", "It is removed from modern Java"],
   "answer": 1,
   "explain": "Reflection trades compile-time safety and speed for flexibility, which suits frameworks more than everyday code."},
  {"q": "What is a functional interface?",
   "options": ["An interface with no methods", "An interface with exactly one abstract method, which a lambda can implement", "Any interface in java.util", "A class with only static methods"],
   "answer": 1,
   "explain": "A lambda supplies the body of that single method; Predicate, Function and Comparator are common examples."},
  {"q": "What is the difference between StringBuilder and StringBuffer?", "options": ["StringBuffer is immutable", "They are identical in every way", "StringBuffer is synchronized, so thread-safe but slower; StringBuilder is not synchronized and is the usual choice", "StringBuilder is older"], "answer": 2, "explain": "Both are mutable buffers with the same methods. StringBuffer (Java 1.0) locks on each call; StringBuilder (Java 5) does not, which is faster when only one thread uses it."},
  {"q": "You need to sort Parcel objects by weight in one place and by city in another, and you cannot edit the Parcel class. What do you use?", "options": ["Implement Comparable twice", "A Comparator for each order, passed to the sort call", "Override equals", "Use a HashMap"], "answer": 1, "explain": "Comparable gives only one natural order inside the class. A Comparator is supplied from outside, so any number of orders work without changing the class."},
  {"q": "Why prefer Integer.compare(a, b) to returning a - b from a comparator?", "options": ["It is shorter", "Subtraction can overflow for large values and give a wrong sign", "Subtraction is not allowed", "compare is faster by a factor of ten"], "answer": 1, "explain": "If a is very large and b very negative, a - b wraps around and the sign flips, giving an inconsistent order. Integer.compare never overflows."},
  {"q": "A for-each loop over an ArrayList calls list.remove(x) on a matching element. What is the most likely result?", "options": ["Silent success", "ConcurrentModificationException on a later step, because the list's modification count changed behind the iterator", "A compile error", "The list is copied automatically"], "answer": 1, "explain": "The hidden iterator checks the count on each next(). Use the iterator's own remove(), removeIf, or build a new list."},
  {"q": "Which statement about fail-fast iterators is true?", "options": ["They only throw when two threads are running", "They are a best-effort bug detector, not a guarantee of thread safety", "They never throw in single-threaded code", "They lock the collection"], "answer": 1, "explain": "The exception most often comes from single-threaded code that modifies a collection while looping. It is not guaranteed even with threads, so it is not a synchronisation mechanism."}
]
```

> **Source:** McDowell, Cracking the Coding Interview 6e, ch. 13 (Java: how to approach, overloading vs. overriding, collection framework, and the chapter's knowledge topics). Explanations, Java samples and Python demos are original.
