# Expressions, operators and control flow

With objects and names in place, we can combine them. This lesson covers Python's operators (including the ones that behave differently from C and Java), precedence, chained comparisons, short-circuit logic, conditional expressions, and the control-flow statements: `if`, `while`, `for`, `break`/`continue`, the unusual `else` clause on loops, and `match`.

## Arithmetic operators

| Operator | Meaning | Example | Result |
|---|---|---|---|
| `+ - *` | add, subtract, multiply | `7 * 3` | `21` |
| `/` | true division (always float) | `7 / 2` | `3.5` |
| `//` | floor division | `7 // 2`, `-7 // 2` | `3`, `-4` |
| `%` | modulo (sign of divisor) | `-7 % 3` | `2` |
| `**` | power | `2 ** 10`, `2 ** -1` | `1024`, `0.5` |
| `@` | matrix multiply (numpy) | `A @ B` | — |

Two things to remember. First, `/` *always* produces a float in Python 3, even for `6 / 2`. Second, `//` and `%` use **floor** semantics, which makes `%` perfect for wrap-around indexing: `(i - 1) % n` is always in `0..n-1`, even when `i == 0`.

```python-run
n = 5
print([(i - 1) % n for i in range(n)])   # previous index with wrap-around
print(6 / 2, type(6 / 2))
print(2 ** 0.5, pow(2, 10, 1000))        # 3-arg pow = fast modular exponentiation
```

`pow(base, exp, mod)` computes modular exponentiation in O(log exp) multiplications without ever building the huge intermediate number — a common interview helper. Since Python 3.8, `pow(a, -1, m)` returns the modular inverse.

## Comparison operators and chaining

`<`, `<=`, `>`, `>=`, `==`, `!=` compare values; `is`, `is not` compare identity; `in`, `not in` test membership. Python lets you **chain** comparisons, with mathematical meaning:

```python-run
x = 5
print(1 < x < 10)          # same as (1 < x) and (x < 10), x evaluated once
print(1 < x > 3)           # legal but confusing: (1 < x) and (x > 3)
print(0 <= x <= 4)
a = b = c = 7
print(a == b == c)
```

Comparing incompatible types with ordering operators raises `TypeError` in Python 3 (`3 < "a"`), whereas `==` between unrelated types simply returns `False`.

Sequences compare **lexicographically**: element by element, the first difference decides, and a proper prefix is smaller. This is why you can sort tuples to sort by multiple keys.

```python-run
print((1, 2, 3) < (1, 3), [1, 2] < [1, 2, 0], "apple" < "banana", "Zebra" < "apple")
```

The last result is `True` because uppercase letters have smaller code points than lowercase ones. Use `key=str.lower` (or `str.casefold`) when you want case-insensitive ordering.

## Logical operators and short-circuiting

`and`, `or` and `not` work on truthiness, and `and`/`or` **short-circuit**: they stop evaluating as soon as the answer is known. Crucially, they return **one of their operands**, not necessarily a `bool`:

- `a or b` returns `a` if `a` is truthy, else `b`.
- `a and b` returns `a` if `a` is falsy, else `b`.

```python-run
print(0 or "default")        # 'default'
print("given" or "default")  # 'given'
print([] and 1 / 0)          # [] — the division never runs
name = ""
display = name or "anonymous"
print(display)
```

The `x or default` idiom is common but has the same trap as truthiness tests: it replaces *every* falsy value, including a legitimate `0`. When only `None` means "missing", write `x if x is not None else default`.

Short-circuiting is also how you guard expressions: `if i < len(a) and a[i] == target:` never indexes out of range.

## Bitwise operators

`&` (and), `|` (or), `^` (xor), `~` (invert), `<<`, `>>` work on integers. Python ints are conceptually infinite two's complement, so `~5 == -6` and `-1 >> 10 == -1`. On sets, `&`, `|`, `^`, `-` mean intersection, union, symmetric difference and difference; on dicts (3.9+), `|` merges.

```python-run
print(6 & 3, 6 | 3, 6 ^ 3, ~5, 1 << 10)
print(bin(42), (42).bit_count() if hasattr(int, "bit_count") else bin(42).count("1"))
print({1, 2, 3} & {2, 3, 4}, {"a": 1} | {"b": 2})
x = 12
print("power of two?", x > 0 and x & (x - 1) == 0)
```

## Precedence (highest to lowest)

| Level | Operators |
|---|---|
| 1 | `(...)`, `[...]`, `{...}` displays; attribute, subscript, call |
| 2 | `**` (right-associative; binds tighter than unary minus on its left) |
| 3 | unary `+x`, `-x`, `~x` |
| 4 | `*`, `@`, `/`, `//`, `%` |
| 5 | `+`, `-` |
| 6 | `<<`, `>>` |
| 7 | `&` |
| 8 | `^` |
| 9 | `|` |
| 10 | comparisons, `in`, `is` (chained) |
| 11 | `not` |
| 12 | `and` |
| 13 | `or` |
| 14 | `x if c else y` |
| 15 | `lambda` |
| 16 | `:=` (walrus) |

Surprises worth memorising: `-2 ** 2 == -4` (power binds tighter than unary minus), `2 ** 3 ** 2 == 512` (right-associative), and `x & 1 == 0` parses as `(x & 1) == 0` because comparisons rank *below* the bitwise operators — the opposite of C, where `==` binds tighter than `&` and the same expression means `x & (1 == 0)`. When in doubt, add parentheses; readers will thank you.

```python-run
print(-2 ** 2, (-2) ** 2, 2 ** 3 ** 2)
x = 6
print(x & 1 == 0)     # (x & 1) == 0 in Python
print(not 1 == 2)     # not (1 == 2)
```

## Conditional expressions and the walrus operator

The ternary form is `value_if_true if condition else value_if_false`:

```python-run
n = -3
abs_n = n if n >= 0 else -n
parity = "even" if n % 2 == 0 else "odd"
print(abs_n, parity)
```

The **assignment expression** `:=` (Python 3.8+) binds a name *inside* an expression. It shines in loops that read until a sentinel and in comprehensions that need a computed value twice:

```python-run
import io
stream = io.StringIO("alpha\nbeta\n\ngamma\n")
while (line := stream.readline().strip()):
    print("got", line)          # stops at the first blank line

nums = [3, 8, 1, 10]
print([y for x in nums if (y := x * x) > 10])
```

## The `if` statement

```python
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"
```

Blocks are delimited by **indentation** (PEP 8: four spaces), not braces. There is no `switch` in classic Python; long `if/elif` chains or a dict of handlers are the traditional substitutes, and Python 3.10 added `match` (below).

## `while` loops

```python-run
# Euclid's algorithm
a, b = 252, 105
while b:
    a, b = b, a % b
print("gcd =", a)
```

Note the **tuple assignment** `a, b = b, a % b`: the whole right side is evaluated first, then unpacked, so no temporary variable is needed. This simultaneous assignment is also how you swap: `x, y = y, x`.

## `for` loops iterate over iterables

A Python `for` loop is a *for-each*: it walks any iterable (list, string, dict, file, generator...). There's no C-style `for (i = 0; i < n; i++)`. Use the helper built-ins:

```python-run
names = ["ana", "ben", "cy"]
ages = [31, 25, 40]

for i in range(len(names)):          # works, but un-Pythonic
    pass

for i, name in enumerate(names, start=1):     # index + value
    print(i, name)

for name, age in zip(names, ages):            # parallel iteration
    print(f"{name} is {age}")

for i in range(10, 0, -3):                    # start, stop (exclusive), step
    print(i, end=" ")
print()
for name in reversed(names):
    print(name, end=" ")
print()
```

`range(start, stop, step)` is lazy: `range(10**12)` costs no memory, supports `len`, indexing and an O(1) `in` test for integers. `zip` stops at the shortest input; pass `strict=True` (3.10+) to raise if lengths differ.

> [!WARNING]
> Don't add or remove items from a list (or keys from a dict) while iterating over it. For lists you'll silently skip elements; for dicts you get `RuntimeError: dictionary changed size during iteration`. Iterate over a copy (`for k in list(d):`) or build a new collection.

```python-run
nums = [1, 2, 2, 3, 2]
for x in nums:
    if x == 2:
        nums.remove(x)
print("buggy:", nums)      # a 2 survives because indices shift

nums = [1, 2, 2, 3, 2]
nums = [x for x in nums if x != 2]
print("fixed:", nums)
```

## `break`, `continue` and the loop `else`

`break` exits the innermost loop; `continue` jumps to the next iteration. Python loops also accept an `else` clause that runs **only if the loop finished without `break`**. It's the cleanest way to express "search, and do something if not found":

```python-run
def find_first_negative(xs):
    for i, x in enumerate(xs):
        if x < 0:
            print("first negative at index", i)
            break
    else:
        print("no negatives")

find_first_negative([3, 1, -4, 1])
find_first_negative([2, 7])
```

Read the `else` as "no break". It is rarely used, which is exactly why interviewers like to ask what it does.

To break out of *nested* loops, Python has no labelled break. Options: move the loops into a function and `return`; use a flag; or use `itertools.product` to flatten the nesting into a single loop.

## `pass`, `...` and empty blocks

A block cannot be empty. `pass` is the do-nothing statement; `...` (the `Ellipsis` object) is also commonly used as a placeholder body in stubs.

## Structural pattern matching: `match` (3.10+)

`match` is not just a switch: it destructures sequences, mappings and objects while testing their shape.

```python-run
def describe(cmd):
    match cmd:
        case ["go", direction]:
            return f"moving {direction}"
        case ["pick", "up", *items] if items:
            return f"picking up {', '.join(items)}"
        case {"action": "say", "text": str(text)}:
            return f"saying {text!r}"
        case int() | float() as n if n < 0:
            return "negative number"
        case _:
            return "unknown"

for c in [["go", "north"], ["pick", "up", "key", "map"], {"action": "say", "text": "hi"}, -2.5, 42]:
    print(c, "->", describe(c))
```

Key rules: a bare name in a pattern (`direction`) is a **capture**, binding whatever is there; to compare against a constant stored in a variable, use a dotted name (`Color.RED`); `_` is the wildcard; `|` combines alternatives; `if` adds a guard. A plain `str` value does *not* match a sequence pattern, which avoids a classic bug.

## Worked example: FizzBuzz three ways

```python-run
# 1. classic
out = []
for i in range(1, 16):
    if i % 15 == 0:
        out.append("FizzBuzz")
    elif i % 3 == 0:
        out.append("Fizz")
    elif i % 5 == 0:
        out.append("Buzz")
    else:
        out.append(str(i))
print(" ".join(out))

# 2. string concatenation + or-default
print(" ".join(("Fizz" * (i % 3 == 0) + "Buzz" * (i % 5 == 0)) or str(i) for i in range(1, 16)))

# 3. match on a tuple
def fb(i):
    match (i % 3, i % 5):
        case (0, 0): return "FizzBuzz"
        case (0, _): return "Fizz"
        case (_, 0): return "Buzz"
        case _: return str(i)
print(" ".join(map(fb, range(1, 16))))
```

Version 2 leans on `bool * str` (True is 1) and the `or` default — cute, but version 1 is what you'd write in production.

## Input and output basics

`print(*objects, sep=" ", end="\n", file=sys.stdout, flush=False)` writes text; `input(prompt)` reads a line as a string (always a string — convert with `int()`/`float()`). For formatting, use **f-strings**:

```python-run
name, total, ratio = "Brook", 1234567.891, 0.4567
print(f"{name:>8}|{total:,.2f}|{ratio:.1%}|{42:08b}|{255:#x}")
print(f"{total=}")   # self-documenting expression (3.8+)
```

Format spec mini-language: `[[fill]align][sign][width][,][.precision][type]` where align is `<`, `>`, `^`, and type is `d`, `f`, `e`, `%`, `b`, `x`, etc.

> [!INTERVIEW]
> Expect quick-fire questions: What does `else` on a `for` loop do? (Runs if no `break`.) What's `a or b` when `a` is `0`? (`b`.) Why is `-7 % 3 == 2`? (Floor semantics, result takes the divisor's sign.) How do you swap two variables? (`a, b = b, a`.) What's the cost of `x in range(n)`? (O(1) for ints.)

## Interactive loops: input, sentinels and flags

Console programs combine `input()` with a `while` loop. Two points cause most of the trouble: `input` always returns a **string** (convert it, and expect the conversion to fail), and the loop needs a clear exit — a **sentinel** value such as `"q"`, a Boolean **flag** that any branch can switch off, or `while True` with `break` placed exactly where the decision is made.

```python
total = 0
while True:
    text = input("Amount (blank to finish): ").strip()
    if not text:                  # sentinel: an empty line ends the loop
        break
    try:
        total += float(text)
    except ValueError:
        print(f"{text!r} is not a number")
        continue                  # ask again
print(f"Total: {total:.2f}")
```

The same loop shape drives menu programs and games: read a command, dispatch on it, repeat until told to stop. Because this page cannot pause for typing, here it is with the answers supplied by an iterator — the technique to use in tests as well, since logic that receives its "input" as an argument can be checked automatically:

```python-run
def add_amounts(read):
    """read is any zero-argument function returning the next line of input."""
    total, rejected = 0.0, []
    while True:
        text = read().strip()
        if not text:
            break
        try:
            total += float(text)
        except ValueError:
            rejected.append(text)
    return total, rejected

answers = iter(["12.5", "abc", " 7 ", "1e2", ""])
print(add_amounts(lambda: next(answers)))
```

For a gentler, step-by-step introduction to `input`, `while`, flags, `break` and `continue`, see the lesson *User input, while loops and functions* in the "Start here" module.

## Pitfalls recap

- `/` returns float; use `//` for integer division.
- `-2 ** 2 == -4`.
- `x or default` swallows valid falsy values.
- Mutating a collection while iterating over it.
- Capture patterns in `match` silently bind instead of comparing: `case RED:` matches everything; use `case Color.RED:`.
- Expecting `zip` to complain about different lengths (it truncates unless `strict=True`).

## Summary

Python operators mostly look like C's, but division, modulo, comparison chaining, short-circuit operators that return operands, and precedence of `**` and bitwise ops have their own rules. Loops iterate over iterables, helped by `range`, `enumerate`, `zip` and `reversed`; `else` on a loop means "completed without break"; and `match` brings structural destructuring.

```quiz
[
  {"q": "What does `[] or \"x\"` evaluate to?", "options": ["True", "[]", "\"x\"", "False"], "answer": 2,
   "explain": "`or` returns the first truthy operand, or the last operand if none is truthy. `[]` is falsy, so the result is \"x\"."},
  {"q": "When does the `else` block of a `for` loop run?", "options": ["When the loop body raises", "When the loop never executes", "When the loop ends without hitting `break`", "Always, after the loop"], "answer": 2,
   "explain": "Loop `else` means 'no break'. It also runs for an empty iterable, because no break happened."},
  {"q": "What is `-2 ** 2`?", "options": ["4", "-4", "0.25", "SyntaxError"], "answer": 1,
   "explain": "`**` binds tighter than unary minus, so this is `-(2 ** 2)`."},
  {"q": "`1 < x < 10` is equivalent to:", "options": ["(1 < x) < 10", "1 < x and x < 10 (x evaluated once)", "1 < (x < 10)", "A TypeError"], "answer": 1,
   "explain": "Python chains comparisons mathematically, evaluating the middle operand only once."},
  {"q": "In a `match` statement, what does `case value:` (a bare name) do?", "options": ["Compares to the variable `value`", "Always matches and binds the subject to `value`", "Raises SyntaxError", "Matches only None"], "answer": 1,
   "explain": "Bare names are capture patterns. Use a dotted name like `Config.VALUE` to compare with a constant."},
  {"q": "What does `zip([1, 2, 3], \"ab\")` produce when listed?", "options": ["[(1,'a'),(2,'b'),(3,None)]", "[(1,'a'),(2,'b')]", "ValueError", "[(1,'a'),(2,'b'),(3,'')]"], "answer": 1,
   "explain": "zip stops at the shortest iterable unless strict=True is passed (then it raises ValueError)."},
  {"q": "Which statement swaps a and b?", "options": ["a = b; b = a", "a, b = b, a", "swap(a, b)", "a ^= b"], "answer": 1,
   "explain": "Tuple packing/unpacking evaluates the whole right side before assigning, so no temporary is needed."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.3 (Expressions, Operators, and Precedence), §1.4 (Control Flow) and §1.6 (Simple I/O); Python docs, *Tutorial* ch. 4 "More Control Flow Tools" and *Language Reference* §6.17 "Operator precedence".
