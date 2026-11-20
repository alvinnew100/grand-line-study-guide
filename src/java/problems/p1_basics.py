"""Java track, model problems part 1: numbers, text, control flow, arrays, references, growth, boxing, try/finally.

Java cannot run in the browser, so each of these is solved in Python and models one precisely
defined piece of Java behaviour. Every guide ends with the idiomatic Java that shows the same thing.
"""


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls, follow_up=None):
    d = dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute, approach=approach,
             complexity=complexity, pitfalls=pitfalls)
    if follow_up:
        d["follow_up"] = follow_up
    return d


PROBLEMS = [
# ------------------------------------------------------------------ java-int-arithmetic
dict(
    id="java-int-arithmetic",
    title="int and long arithmetic: overflow and integer division",
    difficulty="Easy",
    pattern="Java numbers",
    entry="java_arith",
    description=r"""
Java's `int` has 32 bits and `long` has 64. Results that do not fit **wrap around** silently, division of
whole numbers **truncates toward zero**, and `%` takes the **sign of the left operand**. Python's integers
do none of these things, so you must model them.

Write `java_arith(kind, a, op, b)`.

- `kind` is `"int"` or `"long"`. `a` and `b` are already valid values of that type.
- `op` is one of `"+"`, `"-"`, `"*"`, `"/"`, `"%"`.
- Return the value Java would compute, as a Python integer.
- For `"/"` or `"%"` with `b == 0`, return the string `"ArithmeticException"`.

**Wrapping rule** for a type with `n` bits: keep the true result modulo `2^n`; if that is `>= 2^(n-1)`,
subtract `2^n`.

**Examples**

- `java_arith("int", 2147483647, "+", 1)` → `-2147483648`
- `java_arith("int", -7, "/", 2)` → `-3` (Python's `//` would give `-4`)
- `java_arith("int", -7, "%", 2)` → `-1` (Python's `%` would give `1`)
""",
    starter='''def java_arith(kind, a, op, b):
    # kind is "int" or "long"; op is one of + - * / %
    pass
''',
    solution='''def java_arith(kind, a, op, b):
    bits = 32 if kind == "int" else 64

    def wrap(v):
        v &= (1 << bits) - 1
        return v - (1 << bits) if v >= 1 << (bits - 1) else v

    if op in "/%" and b == 0:
        return "ArithmeticException"
    if op == "+":
        r = a + b
    elif op == "-":
        r = a - b
    elif op == "*":
        r = a * b
    else:
        q = abs(a) // abs(b)
        if (a < 0) != (b < 0):
            q = -q
        r = q if op == "/" else a - q * b
    return wrap(r)
''',
    tests=[
        ["int", 2147483647, "+", 1],
        ["int", -7, "/", 2],
        ["int", -7, "%", 2],
        ["int", 7, "/", -2],
        ["int", 7, "%", -2],
        ["int", 86400000, "*", 30],
        ["long", 86400000, "*", 30],
        ["int", -2147483648, "/", -1],
        ["int", -2147483648, "-", 1],
        ["int", 10, "/", 0],
        ["long", 5, "%", 0],
        ["long", 9223372036854775807, "+", 1],
        ["int", 46341, "*", 46341],
        ["int", 17, "%", 5],
        ["int", 0, "-", 0],
    ],
    wrong_solutions=[
        '''def java_arith(kind, a, op, b):
    if op in "/%" and b == 0:
        return "ArithmeticException"
    return {"+": a + b, "-": a - b, "*": a * b, "/": a // b, "%": a % b}[op]
''',
        '''def java_arith(kind, a, op, b):
    bits = 32 if kind == "int" else 64
    def wrap(v):
        v &= (1 << bits) - 1
        return v - (1 << bits) if v >= 1 << (bits - 1) else v
    if op in "/%" and b == 0:
        return "ArithmeticException"
    return wrap({"+": a + b, "-": a - b, "*": a * b, "/": a // b, "%": a % b}[op])
''',
    ],
    guide=G(
        "Lesson *Primitive types and how numbers are stored*: bits, ranges, integer division, overflow.",
        "Python never overflows and rounds division downward. Compute the exact mathematical result first, "
        "fix division so it rounds toward zero, then squeeze the result back into 32 or 64 bits.",
        ["Handle division by zero before anything else.",
         "Truncating division: divide the absolute values, then put the sign back. The remainder is `a - q * b`.",
         "To wrap: `v & (2**bits - 1)` keeps the low bits; if the top bit is set, subtract `2**bits`."],
        "You could special-case every overflow direction with `if` statements. It works for `+` and `-` and "
        "becomes hopeless for `*`. Masking handles all three with one line.",
        r"""1. If the operator is `/` or `%` and `b` is 0, return `"ArithmeticException"`.
2. Compute the exact result with Python's unlimited integers. For `/`, use `q = abs(a) // abs(b)` and negate
   `q` if the signs differ. For `%`, use `a - q * b`.
3. Wrap: mask to the low `bits` bits, and reinterpret the top bit as the sign.

**Dry run** `java_arith("int", 86400000, "*", 30)`: exact product `2592000000`. It is below `2^32`, so the
mask leaves it alone. It is `>= 2^31` (2147483648), so subtract `2^32`: `2592000000 - 4294967296 = -1702967296`.

**Dry run** `java_arith("int", -2147483648, "/", -1)`: `q = 2147483648`, signs equal so it stays positive;
that does not fit, and wrapping gives `-2147483648`. Java really does print that.

```java
int big = Integer.MAX_VALUE + 1;            // -2147483648: wraps silently
int q = -7 / 2;                             // -3: truncates toward zero
int r = -7 % 2;                             // -1: sign of the left operand
long ok = 86_400_000L * 30;                 // 2592000000: one long operand makes it 64-bit
int safe = Math.addExact(big, 1);           // throws ArithmeticException on overflow instead of wrapping
```""",
        "Time O(1), space O(1): a fixed number of arithmetic steps.",
        "- Using Python's `//` and `%`, which round toward negative infinity.\n"
        "- Forgetting that `Integer.MIN_VALUE / -1` overflows.\n"
        "- Wrapping with `% 2**bits` only: that gives a value from 0 upward and never a negative one.",
        "Add the shifts `<<`, `>>` and `>>>`. In Java the shift distance is itself masked to 5 bits for `int` and 6 for `long`.",
    ),
),
# ------------------------------------------------------------------ java-char-string-concat
dict(
    id="java-char-string-concat",
    title="What does + mean? char, int and String",
    difficulty="Easy",
    pattern="Java numbers",
    entry="plus_chain",
    description=r"""
In Java `+` is evaluated **left to right**, and its meaning depends on the two operands at each step:

- if **either** operand is a `String`, it is concatenation and the result is a `String`
  (an `int` is appended as decimal digits, a `char` as the character itself);
- otherwise it is numeric addition and the result is an `int` (a `char` contributes its character code).

Write `plus_chain(terms)`. Each term is a pair `[type, value]`:

- `["int", 5]`
- `["char", "a"]` (a one-character string)
- `["String", "hi"]`

Evaluate `term0 + term1 + term2 + ...` and return the result as `[type, value]`: either `["int", n]` or
`["String", text]`. A single `char` term with nothing added stays a `char`: return it unchanged.
`terms` is never empty. Ignore overflow.

**Examples**

- `'a' + 'b'` → `["int", 195]`
- `1 + 2 + "3"` → `["String", "33"]`
- `"" + 'a' + 1` → `["String", "a1"]`
""",
    starter='''def plus_chain(terms):
    # terms: list of [type, value]; type is "int", "char" or "String"
    pass
''',
    solution='''def plus_chain(terms):
    kind, value = terms[0]
    for t, v in terms[1:]:
        if kind == "String" or t == "String":
            left = value if kind != "int" else str(value)
            right = v if t != "int" else str(v)
            kind, value = "String", left + right
        else:
            a = ord(value) if kind == "char" else value
            b = ord(v) if t == "char" else v
            kind, value = "int", a + b
    return [kind, value]
''',
    tests=[
        [[["char", "a"], ["char", "b"]]],
        [[["int", 1], ["int", 2], ["String", "3"]]],
        [[["String", ""], ["char", "a"], ["int", 1]]],
        [[["String", "1"], ["int", 2], ["int", 3]]],
        [[["char", "a"], ["int", 1], ["String", "z"]]],
        [[["char", "x"]]],
        [[["int", 7]]],
        [[["String", "only"]]],
        [[["char", "a"], ["char", "b"], ["String", "c"], ["char", "d"], ["int", 1]]],
        [[["int", -5], ["char", "0"]]],
        [[["String", "a"], ["String", "b"], ["char", "c"]]],
        [[["int", 1], ["char", "1"], ["String", ""], ["int", 1], ["char", "1"]]],
    ],
    wrong_solutions=[
        '''def plus_chain(terms):
    if any(t == "String" for t, _ in terms):
        return ["String", "".join(str(v) for _, v in terms)]
    if len(terms) == 1:
        return terms[0]
    return ["int", sum(ord(v) if t == "char" else v for t, v in terms)]
''',
        '''def plus_chain(terms):
    kind, value = terms[0]
    for t, v in terms[1:]:
        if kind == "String" or t == "String":
            kind, value = "String", str(value) + str(v)
        else:
            kind, value = "String", str(value) + str(v)
    return [kind, value]
''',
    ],
    guide=G(
        "Lesson *Primitive types and how numbers are stored*: `char` is a number, and the left-to-right rule for `+`.",
        "Keep one running result with its type. Each new term either gets added as a number or glued on as text, "
        "and the decision depends only on the running type and the new term's type.",
        ["Start with the first term as the running value.",
         "At each step ask: is the running value a String, or is the new term a String? Then concatenate.",
         "Otherwise convert any `char` to its code with `ord` and add; the result type is `int`."],
        "Checking 'is there a String anywhere?' and concatenating everything is the common wrong idea: it ignores "
        "that the terms **before** the first String are added as numbers.",
        r"""Fold from the left.

**Dry run** `'a' + 'b' + "c" + 'd' + 1`:

| step | running | next | rule | result |
|---|---|---|---|---|
| 1 | char `a` | char `b` | no String: numeric | int 195 |
| 2 | int 195 | String `c` | String: append | String `195c` |
| 3 | String `195c` | char `d` | String: append the character | String `195cd` |
| 4 | String `195cd` | int 1 | String: append digits | String `195cd1` |

```java
System.out.println('a' + 'b');             // 195
System.out.println(1 + 2 + "3");           // 33
System.out.println("" + 'a' + 1);          // a1
System.out.println('a' + 'b' + "c" + 'd' + 1);   // 195cd1
char next = (char) ('a' + 1);              // 'b': cast the int back to a char
```""",
        "Time O(total length of the result), space the same: one pass over the terms.",
        "- Treating the whole expression as concatenation because a String appears somewhere.\n"
        "- Appending a `char`'s numeric code to a String; Java appends the character.\n"
        "- Returning `[\"int\", 120]` for a lone `char`: with nothing added there is no promotion.",
    ),
),
# ------------------------------------------------------------------ java-switch-fallthrough
dict(
    id="java-switch-fallthrough",
    title="Classic switch: fall-through",
    difficulty="Easy",
    pattern="Java control flow",
    entry="run_switch",
    description=r"""
A classic Java `switch` (the form with colons) jumps to the matching `case` label and then keeps running
**downward through the following cases** until it meets a `break` or the end of the switch.

Write `run_switch(value, cases)` that returns the list of texts printed.

- `cases` is a list, in source order, of `[label, text, has_break]`.
- `label` is an integer, or `None` for the `default` label (at most one, anywhere in the list).
- Entry point: the case whose label equals `value`; if there is none, the `default` case; if there is no
  default either, nothing is printed.
- From the entry point, print each case's `text` in order, stopping after the first case whose `has_break`
  is true.

**Example**

```
switch (2) { case 3: print("three"); case 2: print("two"); case 1: print("one"); break; default: print("other"); }
```
`run_switch(2, [[3, "three", False], [2, "two", False], [1, "one", True], [None, "other", False]])` → `["two", "one"]`
""",
    starter='''def run_switch(value, cases):
    pass
''',
    solution='''def run_switch(value, cases):
    start = None
    for i, (label, _, _) in enumerate(cases):
        if label is not None and label == value:
            start = i
            break
    if start is None:
        for i, (label, _, _) in enumerate(cases):
            if label is None:
                start = i
                break
    if start is None:
        return []
    out = []
    for _, text, has_break in cases[start:]:
        out.append(text)
        if has_break:
            break
    return out
''',
    tests=[
        [2, [[3, "three", False], [2, "two", False], [1, "one", True], [None, "other", False]]],
        [3, [[3, "three", False], [2, "two", False], [1, "one", True], [None, "other", False]]],
        [9, [[3, "three", False], [2, "two", False], [1, "one", True], [None, "other", False]]],
        [9, [[None, "other", False], [1, "one", False], [2, "two", True]]],
        [5, [[1, "a", True], [2, "b", True]]],
        [1, [[1, "a", True], [2, "b", True]]],
        [2, [[1, "a", False], [2, "b", False]]],
        [0, []],
        [7, [[None, "d", True], [7, "seven", False], [8, "eight", False]]],
        [8, [[1, "a", False], [None, "d", False], [8, "h", True], [9, "i", False]]],
        [4, [[1, "a", False], [None, "d", False], [8, "h", True], [9, "i", False]]],
        [0, [[0, "zero", False], [None, "d", False]]],
    ],
    wrong_solutions=[
        '''def run_switch(value, cases):
    for label, text, _ in cases:
        if label == value:
            return [text]
    for label, text, _ in cases:
        if label is None:
            return [text]
    return []
''',
        '''def run_switch(value, cases):
    out, started = [], False
    for label, text, has_break in cases:
        if label == value or label is None:
            started = True
        if started:
            out.append(text)
            if has_break:
                break
    return out
''',
    ],
    guide=G(
        "Lesson *Anatomy of a class, main, and your first statements*: the classic and the arrow form of `switch`.",
        "Two separate questions: **where do I enter**, and **where do I stop**. Entry is decided once. After that "
        "the labels no longer matter; only `break` does.",
        ["First search for a label equal to the value.", "Only if that fails, search for the default.",
         "From the entry index, collect texts until you have collected one that has a break."],
        "Returning only the matching case's text is how an arrow switch behaves. For the classic form it is wrong "
        "whenever a `break` is missing.",
        r"""1. Find the entry index: exact match first, default second, otherwise return `[]`.
2. Walk forward from there, appending each text, and stop after a case with `has_break`.

**Dry run** value 9, cases `default: other` (no break), `case 1: one` (no break), `case 2: two; break`.
No label equals 9, so enter at the default (index 0). Print `other`, fall into case 1 and print `one`,
fall into case 2 and print `two`, then break. Result `["other", "one", "two"]`. A default placed first
still falls through.

```java
static String size(int cups) {
    return switch (cups) {              // arrow form: no fall-through, and it yields a value
        case 1 -> "single";
        case 2, 3 -> "medium";
        default -> "large";
    };
}
```""",
        "Time O(n) in the number of cases, space O(n) for the output.",
        "- Entering at the default because it appears before the matching case in the source.\n"
        "- Stopping at the default.\n- Forgetting the switch with no match and no default.",
    ),
),
# ------------------------------------------------------------------ java-array-defaults-bounds
dict(
    id="java-array-defaults-bounds",
    title="Arrays: default values and bounds checks",
    difficulty="Easy",
    pattern="Java arrays",
    entry="array_ops",
    description=r"""
`new int[4]` creates four slots that already hold a **default value**, and every access is **bounds-checked**.

Write `array_ops(elem_type, length, ops)` simulating `new elem_type[length]` followed by operations.

- `elem_type` is `"int"`, `"double"`, `"boolean"`, `"char"` or `"String"`.
- Defaults: `0`, `0.0`, `False`, `"\u0000"` (the character with code 0) and `None` (Java's `null`).
- If `length` is negative, return `["NegativeArraySizeException: " + str(length)]` and do nothing else.
- `ops` is a list of:
  - `["get", i]` → append the element at index `i` to the output;
  - `["set", i, v]` → store `v` (append nothing);
  - `["length"]` → append the length.
- An index below 0 or at or above the length ends the run: append
  `"ArrayIndexOutOfBoundsException: Index <i> out of bounds for length <n>"` and stop.

Return the output list.

**Example** `array_ops("int", 3, [["get", 1], ["set", 1, 9], ["get", 1], ["get", 3], ["length"]])`
→ `[0, 9, "ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3"]`
""",
    starter='''def array_ops(elem_type, length, ops):
    pass
''',
    solution='''def array_ops(elem_type, length, ops):
    if length < 0:
        return ["NegativeArraySizeException: " + str(length)]
    default = {"int": 0, "double": 0.0, "boolean": False, "char": "\\u0000", "String": None}[elem_type]
    arr = [default] * length
    out = []
    for op in ops:
        if op[0] == "length":
            out.append(length)
            continue
        i = op[1]
        if i < 0 or i >= length:
            out.append("ArrayIndexOutOfBoundsException: Index %d out of bounds for length %d" % (i, length))
            break
        if op[0] == "get":
            out.append(arr[i])
        else:
            arr[i] = op[2]
    return out
''',
    tests=[
        ["int", 3, [["get", 1], ["set", 1, 9], ["get", 1], ["get", 3], ["length"]]],
        ["String", 2, [["get", 0], ["set", 0, "tea"], ["get", 0], ["get", 1]]],
        ["boolean", 1, [["get", 0], ["length"]]],
        ["double", 2, [["get", 1], ["set", 0, 2.5], ["get", 0]]],
        ["char", 1, [["get", 0]]],
        ["int", 0, [["length"], ["get", 0]]],
        ["int", -1, [["length"]]],
        ["int", 4, [["set", -1, 5], ["get", 0]]],
        ["int", 4, [["set", 4, 5], ["get", 0]]],
        ["int", 4, [["set", 3, 5], ["get", 3], ["get", 2], ["length"]]],
        ["String", 3, []],
        ["int", 2, [["get", 0], ["get", 1], ["get", 2], ["get", 0]]],
    ],
    wrong_solutions=[
        '''def array_ops(elem_type, length, ops):
    if length < 0:
        return ["NegativeArraySizeException: " + str(length)]
    arr = [None] * length
    out = []
    for op in ops:
        if op[0] == "length":
            out.append(length); continue
        i = op[1]
        if i < 0 or i >= length:
            out.append("ArrayIndexOutOfBoundsException: Index %d out of bounds for length %d" % (i, length)); break
        if op[0] == "get": out.append(arr[i])
        else: arr[i] = op[2]
    return out
''',
        '''def array_ops(elem_type, length, ops):
    if length < 0:
        return ["NegativeArraySizeException: " + str(length)]
    default = {"int": 0, "double": 0.0, "boolean": False, "char": "\\u0000", "String": None}[elem_type]
    arr = [default] * length
    out = []
    for op in ops:
        if op[0] == "length":
            out.append(length); continue
        i = op[1]
        if i >= length:
            out.append("ArrayIndexOutOfBoundsException: Index %d out of bounds for length %d" % (i, length)); break
        if op[0] == "get": out.append(arr[i])
        else: arr[i] = op[2]
    return out
''',
    ],
    guide=G(
        "Lesson *References, arrays, the stack and the heap*: arrays are objects with zero-based indices.",
        "A Java array is a fixed row of slots pre-filled with the type's zero value. Python lists accept negative "
        "indices, so the bounds check has to be written by hand.",
        ["Deal with a negative length first.", "Build the array as `[default] * length` using a table of defaults.",
         "Check `0 <= i < length` before every get and set; on failure append the message and stop."],
        "Without the explicit check, `arr[-1]` in Python quietly reads the last element. Java would throw.",
        r"""**Dry run** `("int", 3, [get 1, set 1 9, get 1, get 3, length])`: array `[0, 0, 0]`. `get 1` → 0.
`set 1 9` → `[0, 9, 0]`. `get 1` → 9. `get 3`: 3 is not below 3, so append the exception text and stop.
The final `length` never runs.

```java
int[] counts = new int[3];                 // {0, 0, 0}
String[] names = new String[2];            // {null, null}
boolean[] flags = new boolean[1];          // {false}
counts[1] = 9;
System.out.println(counts.length);         // 3: a field, no parentheses
counts[3] = 1;   // ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3
```""",
        "Time O(length + number of operations), space O(length).",
        "- `None` as the default for every type.\n- Allowing Python's negative indices.\n"
        "- Continuing after an exception.\n- `i > length` instead of `i >= length`.",
    ),
),
# ------------------------------------------------------------------ java-reference-model
dict(
    id="java-reference-model",
    title="References, aliases and pass-by-value",
    difficulty="Medium",
    pattern="Java references",
    entry="run_program",
    description=r"""
Model a tiny Java program working with `class Box { int v; }`. Variables hold **references** to boxes
(or `null`). Assignment copies the reference. Arguments are passed **by value**: a method gets a copy of
the reference.

Write `run_program(ops)`; each op is one statement:

| op | Java | effect |
|---|---|---|
| `["new", x, n]` | `Box x = new Box(); x.v = n;` | `x` refers to a new box |
| `["assign", x, y]` | `x = y;` | `x` refers to whatever `y` refers to (maybe `null`) |
| `["null", x]` | `x = null;` | |
| `["set", x, n]` | `x.v = n;` | |
| `["mutate", x, n]` | `mutate(x, n)` where `static void mutate(Box b, int n) { b.v = n; }` | changes the caller's box |
| `["reassign", x, n]` | `reassign(x, n)` where `static void reassign(Box b, int n) { b = new Box(); b.v = n; }` | **no effect on the caller** |
| `["swap", x, y]` | `swap(x, y)` where the method exchanges its two parameters | **no effect on the caller** |
| `["print", x]` | `System.out.println(x.v);` | append the value to the output |
| `["same", x, y]` | `System.out.println(x == y);` | append `True` or `False` |

`set`, `mutate` and `print` on a variable holding `null` throw: append `"NullPointerException"` and stop.
(`reassign`, `swap` and `same` work with `null`.) Every variable used has been created earlier by `new`,
`assign` or `null`. Return the output list.

**Example** `[["new","a",1], ["assign","b","a"], ["set","b",5], ["print","a"], ["reassign","a",9], ["print","a"], ["same","a","b"]]`
→ `[5, 5, True]`
""",
    starter='''def run_program(ops):
    pass
''',
    solution='''def run_program(ops):
    heap = {}
    frame = {}
    out = []
    next_id = [1]

    def new_box(n):
        oid = next_id[0]
        next_id[0] += 1
        heap[oid] = n
        return oid

    for op in ops:
        kind = op[0]
        if kind == "new":
            frame[op[1]] = new_box(op[2])
        elif kind == "assign":
            frame[op[1]] = frame[op[2]]
        elif kind == "null":
            frame[op[1]] = None
        elif kind in ("set", "mutate"):
            ref = frame[op[1]]
            if ref is None:
                out.append("NullPointerException")
                break
            heap[ref] = op[2]
        elif kind == "reassign":
            new_box(op[2])
        elif kind == "swap":
            pass
        elif kind == "print":
            ref = frame[op[1]]
            if ref is None:
                out.append("NullPointerException")
                break
            out.append(heap[ref])
        elif kind == "same":
            out.append(frame[op[1]] == frame[op[2]])
    return out
''',
    tests=[
        [[["new", "a", 1], ["assign", "b", "a"], ["set", "b", 5], ["print", "a"], ["reassign", "a", 9], ["print", "a"], ["same", "a", "b"]]],
        [[["new", "a", 1], ["new", "b", 1], ["same", "a", "b"], ["print", "a"], ["print", "b"]]],
        [[["new", "a", 1], ["mutate", "a", 7], ["print", "a"]]],
        [[["new", "a", 1], ["new", "b", 2], ["swap", "a", "b"], ["print", "a"], ["print", "b"]]],
        [[["new", "a", 1], ["null", "a"], ["print", "a"], ["new", "b", 3], ["print", "b"]]],
        [[["null", "a"], ["null", "b"], ["same", "a", "b"], ["reassign", "a", 4], ["same", "a", "b"]]],
        [[["new", "a", 1], ["assign", "b", "a"], ["new", "a", 2], ["print", "b"], ["print", "a"], ["same", "a", "b"]]],
        [[["new", "a", 1], ["assign", "b", "a"], ["null", "a"], ["set", "b", 8], ["print", "b"], ["set", "a", 1], ["print", "b"]]],
        [[]],
        [[["new", "a", 1], ["assign", "b", "a"], ["assign", "c", "b"], ["mutate", "c", 42], ["print", "a"], ["null", "b"], ["print", "c"], ["same", "a", "c"]]],
        [[["null", "x"], ["mutate", "x", 1], ["new", "y", 2], ["print", "y"]]],
        [[["new", "a", 3], ["reassign", "a", 3], ["new", "b", 3], ["same", "a", "b"], ["assign", "b", "a"], ["same", "a", "b"]]],
    ],
    wrong_solutions=[
        '''def run_program(ops):
    frame, out = {}, []
    for op in ops:
        k = op[0]
        if k == "new": frame[op[1]] = op[2]
        elif k == "assign": frame[op[1]] = frame[op[2]]
        elif k == "null": frame[op[1]] = None
        elif k in ("set", "mutate"):
            if frame[op[1]] is None:
                out.append("NullPointerException"); break
            frame[op[1]] = op[2]
        elif k == "print":
            if frame[op[1]] is None:
                out.append("NullPointerException"); break
            out.append(frame[op[1]])
        elif k == "same": out.append(frame[op[1]] == frame[op[2]])
    return out
''',
        '''def run_program(ops):
    heap, frame, out, n = {}, {}, [], [0]
    def nb(v):
        n[0] += 1; heap[n[0]] = v; return n[0]
    for op in ops:
        k = op[0]
        if k == "new": frame[op[1]] = nb(op[2])
        elif k == "assign": frame[op[1]] = frame[op[2]]
        elif k == "null": frame[op[1]] = None
        elif k in ("set", "mutate"):
            if frame[op[1]] is None:
                out.append("NullPointerException"); break
            heap[frame[op[1]]] = op[2]
        elif k == "reassign": frame[op[1]] = nb(op[2])
        elif k == "swap": frame[op[1]], frame[op[2]] = frame[op[2]], frame[op[1]]
        elif k == "print":
            if frame[op[1]] is None:
                out.append("NullPointerException"); break
            out.append(heap[frame[op[1]]])
        elif k == "same": out.append(frame[op[1]] == frame[op[2]])
    return out
''',
    ],
    guide=G(
        "Lessons *References, arrays, the stack and the heap* and *Methods, parameters, return values and pass-by-value*.",
        "Keep two tables: a **frame** mapping variable names to object ids (or `None`), and a **heap** mapping "
        "object ids to the box's value. Assignment copies an id. A method receives copies of ids, so it can change "
        "the heap but never the caller's frame.",
        ["Give every `new` a fresh object id.", "`same` compares ids, not values.",
         "`reassign` and `swap` change only the method's own copies: the caller's frame is untouched."],
        "Storing the number directly in the variable (no heap) cannot represent two variables sharing one box, "
        "so aliasing is lost.",
        r"""**Dry run** of the example. `new a 1`: heap `{#1: 1}`, frame `{a: #1}`. `assign b a`: frame
`{a: #1, b: #1}`. `set b 5`: heap `{#1: 5}`. `print a` → 5 (same box). `reassign a 9`: the method's local
copy points at a new box #2, which becomes garbage; frame unchanged. `print a` → 5. `same a b` → True.

```java
class Box { int v; }

static void mutate(Box b, int n)   { b.v = n; }                    // follows the copied reference
static void reassign(Box b, int n) { b = new Box(); b.v = n; }     // re-points only the local copy
static void swap(Box x, Box y)     { Box t = x; x = y; y = t; }    // swaps only the local copies

Box a = new Box();  a.v = 1;
Box b = a;                       // alias
b.v = 5;                         // a.v is 5 too
reassign(a, 9);                  // a.v is still 5
System.out.println(a == b);      // true: same object
```""",
        "Time O(number of statements), space O(number of boxes created).",
        "- Comparing values for `==`.\n- Letting `reassign` or `swap` change the caller's variables.\n"
        "- Throwing for `same` on `null`: comparing references with `==` never throws.",
    ),
),
# ------------------------------------------------------------------ java-casting-narrowing
dict(
    id="java-casting-narrowing",
    title="Narrowing casts",
    difficulty="Easy",
    pattern="Java numbers",
    entry="narrow",
    description=r"""
A cast such as `(byte) x` or `(int) d` may lose information. Model the two rules.

Write `narrow(value, target)` where `target` is `"byte"`, `"short"`, `"char"`, `"int"` or `"long"`.

**Whole-number source** (`value` is a Python `int` that fits in a Java `long`): keep the low
8 / 16 / 16 / 32 / 64 bits. `byte`, `short`, `int` and `long` are signed (reinterpret the top bit as a sign);
`char` is **unsigned** (0 to 65535).

**Fractional source** (`value` is a Python `float`, standing for a Java `double`):

1. Drop the fraction (round toward zero).
2. If the target is `long`: clamp to the `long` range. Otherwise clamp to the **`int`** range first, and then
   apply the whole-number rule to reach `byte`, `short` or `char`.

Return a Python `int`.

**Examples** `narrow(300, "byte")` → `44`; `narrow(-1, "char")` → `65535`; `narrow(3.99, "int")` → `3`;
`narrow(-3.99, "int")` → `-3`; `narrow(1e20, "int")` → `2147483647`.
""",
    starter='''def narrow(value, target):
    pass
''',
    solution='''def narrow(value, target):
    bits = {"byte": 8, "short": 16, "char": 16, "int": 32, "long": 64}[target]

    def clamp(v, b):
        lo, hi = -(1 << (b - 1)), (1 << (b - 1)) - 1
        return max(lo, min(hi, v))

    if isinstance(value, float):
        v = int(value)
        v = clamp(v, 64) if target == "long" else clamp(v, 32)
    else:
        v = value
    v &= (1 << bits) - 1
    if target != "char" and v >= 1 << (bits - 1):
        v -= 1 << bits
    return v
''',
    tests=[
        [300, "byte"],
        [-1, "char"],
        [3.99, "int"],
        [-3.99, "int"],
        [1e20, "int"],
        [-1e20, "long"],
        [200, "byte"],
        [5000000000, "int"],
        [70000, "short"],
        [65, "char"],
        [1e10, "byte"],
        [-129, "byte"],
        [127, "byte"],
        [0.5, "long"],
        [-70000.9, "short"],
    ],
    wrong_solutions=[
        '''def narrow(value, target):
    bits = {"byte": 8, "short": 16, "char": 16, "int": 32, "long": 64}[target]
    v = round(value)
    v &= (1 << bits) - 1
    if target != "char" and v >= 1 << (bits - 1):
        v -= 1 << bits
    return v
''',
        '''def narrow(value, target):
    bits = {"byte": 8, "short": 16, "char": 16, "int": 32, "long": 64}[target]
    v = int(value)
    v &= (1 << bits) - 1
    if v >= 1 << (bits - 1):
        v -= 1 << bits
    return v
''',
    ],
    guide=G(
        "Lessons *Primitive types and how numbers are stored* and *Loops, operators and casting*.",
        "Integer narrowing throws away high bits. Floating-point narrowing first becomes a clamped `int` or `long`, "
        "then, for small targets, throws away high bits as well.",
        ["`int(x)` on a Python float truncates toward zero, which is what Java does.",
         "Clamp a truncated float to the int range (or the long range when the target is long).",
         "Mask to the target's bit count; subtract `2**bits` if the top bit is set, except for `char`."],
        "Rounding with `round()` is the usual mistake: `(int) 3.99` is 3, not 4.",
        r"""**Dry run** `narrow(1e10, "byte")`: truncate → 10000000000. Target is not long, so clamp to the int
range → 2147483647, which is `0x7FFFFFFF`. Low 8 bits are `0xFF` = 255; the top bit is set, so 255 - 256 = `-1`.
Java prints `-1` for `(byte) 1e10`.

```java
System.out.println((byte) 300);          // 44
System.out.println((int) (char) -1);     // 65535
System.out.println((int) 3.99);          // 3
System.out.println((int) -3.99);         // -3
System.out.println((int) 1e20);          // 2147483647
System.out.println((byte) 1e10);         // -1
System.out.println(Math.round(3.99));    // 4: use round when you want rounding
```""",
        "Time O(1), space O(1).",
        "- Rounding instead of truncating.\n- Treating `char` as signed.\n"
        "- Masking a huge float directly to 8 bits without first clamping to the int range.",
    ),
),
# ------------------------------------------------------------------ java-vault-feedback
dict(
    id="java-vault-feedback",
    title="Vault Dial feedback",
    difficulty="Easy",
    pattern="Arrays",
    entry="feedback",
    description=r"""
The game from the lesson *Building a small game: the Vault Dial*. The vault holds a secret list of digits;
the player guesses a list of the same length. Return `[exact, near]`:

- `exact`: positions where the guess digit equals the secret digit;
- `near`: guess digits that are **not** exact but match a secret digit elsewhere. Each secret digit can be
  matched by **at most one** guess digit, and a secret digit used for an exact match cannot also be used
  for a near match.

Digits may repeat in either list. Lengths are equal (possibly zero).

**Examples** secret `[4, 7, 2]`:
`feedback([4,7,2], [2,7,9])` → `[1, 1]`; `feedback([4,7,2], [7,7,7])` → `[1, 0]`; `feedback([4,7,2], [2,4,7])` → `[0, 3]`.
""",
    starter='''def feedback(secret, guess):
    pass
''',
    solution='''def feedback(secret, guess):
    exact = sum(1 for s, g in zip(secret, guess) if s == g)
    left_s, left_g = {}, {}
    for s, g in zip(secret, guess):
        if s != g:
            left_s[s] = left_s.get(s, 0) + 1
            left_g[g] = left_g.get(g, 0) + 1
    near = sum(min(c, left_s.get(d, 0)) for d, c in left_g.items())
    return [exact, near]
''',
    tests=[
        [[4, 7, 2], [2, 7, 9]],
        [[4, 7, 2], [7, 7, 7]],
        [[4, 7, 2], [2, 4, 7]],
        [[4, 7, 2], [4, 7, 2]],
        [[4, 7, 2], [1, 3, 5]],
        [[4, 7, 2], [2, 2, 4]],
        [[], []],
        [[5], [5]],
        [[5], [6]],
        [[1, 1, 2, 2], [2, 2, 1, 1]],
        [[1, 1, 2, 2], [1, 2, 1, 2]],
        [[1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]],
        [[3, 3, 3], [3, 1, 3]],
    ],
    wrong_solutions=[
        '''def feedback(secret, guess):
    exact = near = 0
    for i, g in enumerate(guess):
        if g == secret[i]:
            exact += 1
        elif g in secret:
            near += 1
    return [exact, near]
''',
        '''def feedback(secret, guess):
    exact = sum(1 for s, g in zip(secret, guess) if s == g)
    common = sum(min(secret.count(d), guess.count(d)) for d in set(guess))
    return [exact, common]
''',
    ],
    guide=G(
        "Lesson *Building a small game: the Vault Dial*, where a test exposed the repeated-digit bug.",
        "Count exact matches first and set those positions aside. Among what is left, a digit can pair up as "
        "many times as it appears on **both** sides: the minimum of the two counts.",
        ["Do the exact pass separately.", "Tally the leftover secret digits and the leftover guess digits.",
         "For each digit, near matches = `min(leftover in guess, leftover in secret)`."],
        "For each non-exact guess digit, search the secret for an unused equal digit and mark it used: "
        "O(n²), and it is what the lesson's Java code does. Fine for three digits.",
        r"""**Dry run** secret `[4,7,2]`, guess `[7,7,7]`. Exact: position 1 → 1. Leftover secret `{4:1, 2:1}`,
leftover guess `{7:2}`. `min(2, 0) = 0` near. Result `[1, 0]`. The naive "appears anywhere in the secret"
rule would report two near matches for a secret containing a single 7.

```java
record Feedback(int exact, int near) { }

static Feedback check(int[] secret, int[] guess) {
    int exact = 0;
    int[] leftSecret = new int[10], leftGuess = new int[10];     // counts per digit 0..9
    for (int i = 0; i < secret.length; i++) {
        if (secret[i] == guess[i]) {
            exact++;
        } else {
            leftSecret[secret[i]]++;
            leftGuess[guess[i]]++;
        }
    }
    int near = 0;
    for (int d = 0; d < 10; d++) {
        near += Math.min(leftSecret[d], leftGuess[d]);
    }
    return new Feedback(exact, near);
}
```""",
        "Time O(n), space O(k) for k distinct digits.",
        "- Counting a guess digit as near because the digit exists somewhere in the secret.\n"
        "- Counting exact matches again in the near total.",
        "This is the scoring rule of the classic game Bulls and Cows.",
    ),
),
# ------------------------------------------------------------------ java-arraylist-growth
dict(
    id="java-arraylist-growth",
    title="How ArrayList grows",
    difficulty="Easy",
    pattern="Java collections",
    entry="grow",
    description=r"""
`java.util.ArrayList` stores its elements in an internal array. When an `add` finds the array full, it
allocates a bigger array and copies the elements across.

Model `n` calls to `add` on a new list. Write `grow(n, initial)`:

- `initial == -1` means `new ArrayList<>()`: the capacity starts at 0 and the **first** growth goes to **10**.
- otherwise `new ArrayList<>(initial)` with `initial >= 0`: the capacity starts at `initial`.
- Every other growth, when the list is full: `new = old + old // 2`, but at least `old + 1`.
- Growing copies every element currently stored.

Return `[final_capacity, number_of_growths, total_elements_copied]`.

**Examples** `grow(11, -1)` → `[15, 2, 10]` (0 → 10 copying 0 elements, then 10 → 15 copying 10);
`grow(3, 0)` → `[3, 3, 3]` (0 → 1 → 2 → 3).
""",
    starter='''def grow(n, initial):
    pass
''',
    solution='''def grow(n, initial):
    default = initial == -1
    cap = 0 if default else initial
    size = growths = copied = 0
    for _ in range(n):
        if size == cap:
            if default and cap == 0:
                new_cap = 10
            else:
                new_cap = max(cap + cap // 2, cap + 1)
            copied += size
            cap = new_cap
            growths += 1
        size += 1
    return [cap, growths, copied]
''',
    tests=[
        [11, -1],
        [3, 0],
        [0, -1],
        [10, -1],
        [1, -1],
        [100, -1],
        [5, 5],
        [6, 5],
        [1000, -1],
        [7, 1],
        [0, 0],
        [16, 2],
        [23, -1],
    ],
    wrong_solutions=[
        '''def grow(n, initial):
    cap = 10 if initial == -1 else initial
    size = growths = copied = 0
    for _ in range(n):
        if size == cap:
            copied += size
            cap = cap * 2
            growths += 1
        size += 1
    return [cap, growths, copied]
''',
        '''def grow(n, initial):
    default = initial == -1
    cap = 0 if default else initial
    size = growths = copied = 0
    for _ in range(n):
        if size == cap:
            new_cap = 10 if default and cap == 0 else cap + cap // 2
            copied += size
            cap = new_cap
            growths += 1
        size += 1
    return [cap, growths, copied]
''',
    ],
    guide=G(
        "Lesson *ArrayList and reading the API documentation*: size versus capacity, and growth by half.",
        "Simulate it literally: a size, a capacity, and a rule for what the capacity becomes when the two meet.",
        ["Grow only when `size == capacity`, immediately before the add.",
         "The default constructor allocates nothing until the first add.",
         "`old // 2` is 0 for capacities 0 and 1, so the 'at least old + 1' rule matters."],
        "A closed formula exists but is fiddly because of the integer division. Simulation is clear and fast.",
        r"""**Dry run** `grow(11, -1)`. Add 1: size 0 = cap 0, default → cap 10, copied 0, growths 1. Adds 2 to 10
fit. Add 11: size 10 = cap 10 → cap 15, copied 10, growths 2. Result `[15, 2, 10]`.

Capacities for the default list: 10, 15, 22, 33, 49, 73, 109, 163, 244, 366, 549, 823, 1234. A thousand adds
copy about 2,500 elements in total: a small constant amount per add, which is why `add` is called
**amortised constant time**.

```java
List<String> names = new ArrayList<>();          // capacity 0 until the first add, then 10
List<String> sized = new ArrayList<>(1_000);     // reserve up front: no growth for 1,000 adds
((ArrayList<String>) names).ensureCapacity(500); // grow once, now
((ArrayList<String>) names).trimToSize();        // shrink the array to the current size
```""",
        "Time O(n), space O(1).",
        "- Doubling: Java grows by half.\n- Starting the default list at capacity 10 and missing the first growth.\n"
        "- Forgetting `max(..., old + 1)`, which leaves a list created with capacity 0 or 1 stuck.",
    ),
),
# ------------------------------------------------------------------ java-integer-cache
dict(
    id="java-integer-cache",
    title="Integer cache puzzles: == and equals",
    difficulty="Easy",
    pattern="Java boxing",
    entry="evaluate",
    description=r"""
`==` on two `Integer` references compares **identity**. Autoboxing calls `Integer.valueOf`, which returns
**cached** objects for values from -128 to 127 and a new object otherwise. That makes `==` true for small
numbers and false for large ones.

Write `evaluate(decls, queries)`.

`decls` is a list of declarations, in order:

| declaration | Java |
|---|---|
| `[name, "int", n]` | `int name = n;` |
| `[name, "Integer", n]` | `Integer name = n;` (autoboxed) |
| `[name, "new", n]` | `Integer name = new Integer(n);` (always a new object) |
| `[name, "alias", other]` | `Integer name = other;` where `other` is an earlier `Integer` variable |

`queries` is a list of `["==", a, b]` or `["equals", a, b]`. Return a list of booleans.

- `==`: if **either** side is an `int`, the other is unboxed and the numbers are compared. If both are
  `Integer` references, the result is true only when they refer to the same object.
- `equals` (the left side is always an `Integer` variable): true when the values are equal. An `int` on
  the right is boxed first.

**Example** `evaluate([["a","Integer",127],["b","Integer",127],["c","Integer",128],["d","Integer",128]], [["==","a","b"],["==","c","d"],["equals","c","d"]])` → `[True, False, True]`
""",
    starter='''def evaluate(decls, queries):
    pass
''',
    solution='''def evaluate(decls, queries):
    cache = {}
    value = {}      # name -> number
    ident = {}      # name -> object id, or None for a primitive int
    counter = [0]

    def fresh():
        counter[0] += 1
        return ("obj", counter[0])

    for name, kind, arg in decls:
        if kind == "int":
            value[name], ident[name] = arg, None
        elif kind == "Integer":
            value[name] = arg
            if -128 <= arg <= 127:
                ident[name] = cache.setdefault(arg, ("cache", arg))
            else:
                ident[name] = fresh()
        elif kind == "new":
            value[name], ident[name] = arg, fresh()
        else:
            value[name], ident[name] = value[arg], ident[arg]
    out = []
    for op, a, b in queries:
        if op == "equals" or ident[a] is None or ident[b] is None:
            out.append(value[a] == value[b])
        else:
            out.append(ident[a] == ident[b])
    return out
''',
    tests=[
        [[["a", "Integer", 127], ["b", "Integer", 127], ["c", "Integer", 128], ["d", "Integer", 128]],
         [["==", "a", "b"], ["==", "c", "d"], ["equals", "c", "d"]]],
        [[["a", "Integer", 1000], ["b", "int", 1000]], [["==", "a", "b"], ["==", "b", "a"], ["equals", "a", "b"]]],
        [[["a", "new", 5], ["b", "new", 5], ["c", "Integer", 5]], [["==", "a", "b"], ["==", "a", "c"], ["equals", "a", "b"], ["==", "a", "a"]]],
        [[["a", "Integer", 500], ["b", "alias", "a"]], [["==", "a", "b"], ["equals", "b", "a"]]],
        [[["a", "Integer", -128], ["b", "Integer", -128], ["c", "Integer", -129], ["d", "Integer", -129]],
         [["==", "a", "b"], ["==", "c", "d"]]],
        [[["x", "int", 7], ["y", "int", 7]], [["==", "x", "y"]]],
        [[["a", "Integer", 0], ["b", "Integer", 1]], [["==", "a", "b"], ["equals", "a", "b"]]],
        [[["a", "Integer", 128], ["b", "new", 128], ["c", "alias", "b"]], [["==", "a", "b"], ["==", "b", "c"], ["equals", "a", "c"], ["==", "a", "c"]]],
        [[["a", "Integer", 127], ["b", "new", 127], ["c", "int", 127]], [["==", "a", "b"], ["==", "b", "c"], ["==", "a", "c"]]],
        [[["a", "Integer", 200]], [["==", "a", "a"], ["equals", "a", "a"]]],
        [[], []],
        [[["a", "Integer", 127], ["b", "Integer", 128]], [["==", "a", "b"], ["equals", "a", "b"]]],
    ],
    wrong_solutions=[
        '''def evaluate(decls, queries):
    value = {}
    for name, kind, arg in decls:
        value[name] = value[arg] if kind == "alias" else arg
    return [value[a] == value[b] for _, a, b in queries]
''',
        '''def evaluate(decls, queries):
    value, boxed = {}, {}
    for name, kind, arg in decls:
        if kind == "alias":
            value[name], boxed[name] = value[arg], True
        else:
            value[name], boxed[name] = arg, kind != "int"
    out = []
    for op, a, b in queries:
        if op == "equals" or not boxed[a] or not boxed[b]:
            out.append(value[a] == value[b])
        else:
            out.append(value[a] == value[b] and -128 <= value[a] <= 127)
    return out
''',
    ],
    guide=G(
        "Lesson *Wrapper classes, autoboxing and formatting*: the three traps of autoboxing.",
        "Give each `Integer` variable an **identity** as well as a value. Autoboxed small values share one "
        "identity per value; everything else gets a fresh one; an alias copies the identity.",
        ["Track `value[name]` and `ident[name]`; use `None` as the identity of a primitive.",
         "If either side of `==` is primitive, compare values.",
         "Otherwise compare identities. A variable compared with itself is always the same object."],
        "Comparing values everywhere answers `equals` correctly and gets `==` wrong for large numbers and for `new`.",
        r"""**Dry run** `a = 128` (autoboxed, fresh object #1), `b = new Integer(128)` (#2), `c = b` (alias, #2).
`a == b`: #1 vs #2 → False. `b == c`: #2 vs #2 → True. `a.equals(c)`: 128 = 128 → True. `a == c` → False.

The tempting shortcut "both boxed: equal values and in the cache range" fails for `new Integer(5) == new Integer(5)`
(two objects) and for `a == a` with a large value (one object).

```java
Integer a = 127, b = 127, c = 128, d = 128;
System.out.println(a == b);          // true: same cached object
System.out.println(c == d);          // false: two objects
System.out.println(c.equals(d));     // true: compare values with equals
System.out.println(c == 128);        // true: c is unboxed
System.out.println(Integer.compare(c, d) == 0);   // true, and null-safe alternatives exist in Objects
```""",
        "Time O(declarations + queries), space O(declarations).",
        "- Forgetting that `new Integer` never uses the cache.\n- Treating an alias as a new object.\n"
        "- Applying the cache rule when one side is a primitive.",
    ),
),
# ------------------------------------------------------------------ java-try-finally-flow
dict(
    id="java-try-finally-flow",
    title="try / catch / finally: what comes out?",
    difficulty="Medium",
    pattern="Java exceptions",
    entry="flow",
    description=r"""
Predict the outcome of one `try` statement inside a method.

Write `flow(try_block, catches, fin, tail)`.

An **outcome** is one of `["ok"]` (the block finishes normally), `["return", value]` or `["throw", type]`.

- `try_block` is an outcome.
- `catches` is a list of `[caught_type, outcome]`, in source order. If the try block throws `T`, the **first**
  catch whose `caught_type` is `T` or a supertype of `T` runs; its outcome replaces the pending one.
- `fin` is an outcome, or `None` when there is no `finally`. If present it **always runs**. If it returns or
  throws, that **replaces** whatever was pending (a pending return value or exception is discarded).
- If nothing returned or threw, the method goes on and returns `tail`.

Use this fixed hierarchy (child → parent):
`FileNotFoundException → IOException → Exception → Throwable`, `NullPointerException → RuntimeException → Exception`,
`IllegalStateException → RuntimeException`, `OutOfMemoryError → Error → Throwable`.

Return `[kind, value, trace]`: `kind` is `"return"` or `"throw"`, `value` the returned value or the exception
type, and `trace` the blocks executed in order, from `"try"`, `"catch:<caught_type>"`, `"finally"`.

**Example** `flow(["throw", "FileNotFoundException"], [["IOException", ["return", 2]]], ["ok"], 0)`
→ `["return", 2, ["try", "catch:IOException", "finally"]]`
""",
    starter='''def flow(try_block, catches, fin, tail):
    pass
''',
    solution='''def flow(try_block, catches, fin, tail):
    parent = {"FileNotFoundException": "IOException", "IOException": "Exception", "Exception": "Throwable",
              "NullPointerException": "RuntimeException", "IllegalStateException": "RuntimeException",
              "RuntimeException": "Exception", "OutOfMemoryError": "Error", "Error": "Throwable",
              "Throwable": None}

    def is_a(t, anc):
        while t is not None:
            if t == anc:
                return True
            t = parent[t]
        return False

    trace = ["try"]
    pending = list(try_block)
    if pending[0] == "throw":
        for caught, outcome in catches:
            if is_a(pending[1], caught):
                trace.append("catch:" + caught)
                pending = list(outcome)
                break
    if fin is not None:
        trace.append("finally")
        if fin[0] != "ok":
            pending = list(fin)
    if pending[0] == "ok":
        return ["return", tail, trace]
    return [pending[0], pending[1], trace]
''',
    tests=[
        [["throw", "FileNotFoundException"], [["IOException", ["return", 2]]], ["ok"], 0],
        [["return", 1], [], ["ok"], 0],
        [["return", 1], [], ["return", 2], 0],
        [["throw", "IllegalStateException"], [], ["return", 9], 0],
        [["throw", "NullPointerException"], [["IOException", ["return", 1]], ["RuntimeException", ["ok"]]], None, 7],
        [["throw", "OutOfMemoryError"], [["Exception", ["return", 1]]], ["ok"], 0],
        [["ok"], [["Exception", ["return", 1]]], None, 5],
        [["throw", "IOException"], [["FileNotFoundException", ["return", 1]], ["Exception", ["throw", "IllegalStateException"]]], ["ok"], 0],
        [["throw", "IOException"], [["Exception", ["throw", "IllegalStateException"]]], ["throw", "NullPointerException"], 0],
        [["throw", "FileNotFoundException"], [["FileNotFoundException", ["ok"]], ["IOException", ["return", 3]]], ["ok"], 4],
        [["ok"], [], ["ok"], 8],
        [["throw", "Exception"], [["RuntimeException", ["return", 1]]], None, 0],
        [["throw", "OutOfMemoryError"], [["Throwable", ["return", 6]]], None, 0],
    ],
    wrong_solutions=[
        '''def flow(try_block, catches, fin, tail):
    trace = ["try"]
    pending = list(try_block)
    if pending[0] == "throw":
        for caught, outcome in catches:
            if caught == pending[1]:
                trace.append("catch:" + caught)
                pending = list(outcome)
                break
    if fin is not None:
        trace.append("finally")
        if fin[0] != "ok":
            pending = list(fin)
    if pending[0] == "ok":
        return ["return", tail, trace]
    return [pending[0], pending[1], trace]
''',
        '''def flow(try_block, catches, fin, tail):
    parent = {"FileNotFoundException": "IOException", "IOException": "Exception", "Exception": "Throwable",
              "NullPointerException": "RuntimeException", "IllegalStateException": "RuntimeException",
              "RuntimeException": "Exception", "OutOfMemoryError": "Error", "Error": "Throwable", "Throwable": None}
    def is_a(t, anc):
        while t is not None:
            if t == anc: return True
            t = parent[t]
        return False
    trace = ["try"]
    pending = list(try_block)
    if pending[0] == "return":
        return ["return", pending[1], trace]
    if pending[0] == "throw":
        for caught, outcome in catches:
            if is_a(pending[1], caught):
                trace.append("catch:" + caught)
                pending = list(outcome)
                break
    if fin is not None:
        trace.append("finally")
        if fin[0] != "ok":
            pending = list(fin)
    if pending[0] == "ok":
        return ["return", tail, trace]
    return [pending[0], pending[1], trace]
''',
    ],
    guide=G(
        "Lesson *Exceptions: try, catch, finally, checked and unchecked*.",
        "Carry one **pending outcome** through three stations: the try block sets it, a matching catch may "
        "replace it, and `finally` runs last and replaces it only if `finally` itself returns or throws.",
        ["A catch matches the thrown type or any of its supertypes; take the first match only.",
         "`finally` runs even when the try block returned, and even when no catch matched.",
         "After `finally`: a pending `ok` means the method continues to `tail`."],
        "Returning as soon as the try block returns skips `finally`, which is exactly the misunderstanding "
        "interviewers test.",
        r"""**Dry run** try throws `IOException`; catches `FileNotFoundException` (no: an `IOException` is not a
`FileNotFoundException`) then `Exception` (yes) whose body throws `IllegalStateException`; `finally` is `ok`.
Pending becomes `throw IllegalStateException`; `finally` runs and changes nothing. Result
`["throw", "IllegalStateException", ["try", "catch:Exception", "finally"]]`.

```java
static int demo() {
    try {
        throw new java.io.FileNotFoundException("x");
    } catch (java.io.IOException e) {      // matches: FileNotFoundException is an IOException
        return 2;                          // the value 2 is saved...
    } finally {
        System.out.println("finally");     // ...this runs, then 2 is returned
    }
}

static int bad() {
    try { throw new IllegalStateException(); }
    finally { return 9; }                  // swallows the exception: never do this
}
```""",
        "Time O(number of catch blocks × hierarchy depth), space O(1) besides the trace.",
        "- Matching catch types by exact name only.\n- Trying later catch blocks after one has run.\n"
        "- Forgetting that an `Error` is not caught by `catch (Exception e)`.\n"
        "- Letting a pending return skip `finally`.",
    ),
),
]
