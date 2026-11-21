# Expressions, operators and control flow

> **Before this lesson:** you should know that names are labels tied to objects and what "truthy" and "falsy" mean, both from [Objects, names, types and mutability](#/lesson/python/py-objects-names). You should also have written a first `if`, `for` and `while`, as in [Decisions and dictionaries](#/lesson/python/py-start-decisions-dicts) and [User input, while loops and functions](#/lesson/python/py-start-input-functions).

## In plain words

A program does two kinds of work. It *calculates* (add these, compare those) and it *decides what to do next* (if this is true do that, repeat this ten times). The symbols that calculate, such as `+`, `<` and `and`, are called **operators**. A piece of code that produces a value, such as `price * 2`, is an **expression**. The statements that choose which lines run and how often, such as `if`, `for` and `while`, are called **control flow**, because they control the path that execution "flows" along.

Think of a recipe. "200 g of flour times two" is an expression: it works out to a quantity. "If the dough is sticky, add flour" and "stir until smooth" are control flow: they decide which steps happen and how many times. A cook who misreads either kind of sentence ruins the dish, and a programmer who misreads either kind of line writes a bug.

Python's operators look like the ones on a calculator, but several of them behave differently from what you would guess, and differently from other languages: division, the remainder of a negative number, `and` and `or` returning things that are not `True` or `False`, and the order in which operators are applied. Interviewers enjoy exactly these corners, and so do bugs. This lesson goes through the operators first and the control-flow statements second, each from its simplest form.

## Arithmetic operators

An **operand** is a value an operator works on: in `7 * 3`, the operator is `*` and the operands are 7 and 3.

| Operator | Meaning | Example | Result |
|---|---|---|---|
| `+ - *` | add, subtract, multiply | `7 * 3` | `21` |
| `/` | true division (the result is always a float) | `7 / 2` | `3.5` |
| `//` | floor division (divide, then round down) | `7 // 2`, `-7 // 2` | `3`, `-4` |
| `%` | remainder, also called modulo (takes the sign of the right operand) | `-7 % 3` | `2` |
| `**` | power | `2 ** 10`, `2 ** -1` | `1024`, `0.5` |
| `@` | matrix multiplication (used by the numpy library) | `A @ B` | — |

Two things to remember. First, `/` *always* produces a float, a number with a decimal point, even when the division comes out even: `6 / 2` is `3.0`, not `3`. Second, `//` and `%` round **down** (toward negative infinity), which makes `%` ideal for "wrap-around" positions. If you have `n` seats in a circle numbered 0 to `n-1`, the seat before seat `i` is `(i - 1) % n`, and that formula gives `n-1` for seat 0 with no special case.

```python-run
n = 5
print([(i - 1) % n for i in range(n)])   # previous index with wrap-around
print(6 / 2, type(6 / 2))
print(2 ** 0.5, pow(2, 10, 1000))        # 3-arg pow = fast modular exponentiation
```

**Reading this code line by line**

- The first `print` builds a list by computing `(i - 1) % n` for `i` = 0, 1, 2, 3, 4. The output is `[4, 0, 1, 2, 3]`: the seat before 0 is 4.
- `6 / 2` prints `3.0` and its type prints `<class 'float'>`.
- `2 ** 0.5` is the square root of 2, about 1.414.
- `pow(2, 10, 1000)` means "2 to the power 10, then the remainder after dividing by 1000", which is 24 because 2¹⁰ is 1024.

The three-argument `pow(base, exp, mod)` never builds the enormous intermediate power. It uses a number of multiplications proportional to the number of digits of the exponent (written O(log exp) in the notation for running time), which makes it a common interview helper. Since Python 3.8, `pow(a, -1, m)` returns the modular inverse: the number that multiplies with `a` to give remainder 1.

## Comparison operators and chaining

A **comparison** produces `True` or `False`. `<`, `<=`, `>`, `>=`, `==` (equal) and `!=` (not equal) compare values; `is` and `is not` compare identity (same object or not); `in` and `not in` test membership (is this item inside that collection?).

Python lets you **chain** comparisons the way mathematics does:

```python-run
x = 5
print(1 < x < 10)          # same as (1 < x) and (x < 10), x evaluated once
print(1 < x > 3)           # legal but confusing: (1 < x) and (x > 3)
print(0 <= x <= 4)
a = b = c = 7
print(a == b == c)
```

`1 < x < 10` reads as "x is between 1 and 10" and prints `True`. Python treats it as `1 < x and x < 10`, with the middle value looked up only once. The second line shows that any chain is allowed, even an unhelpful one; it also prints `True`. `0 <= x <= 4` is `False` because 5 is too large. `a = b = c = 7` ties three names to one object, and `a == b == c` checks that all three are equal: `True`.

Asking whether two values of unrelated types are in order raises an error: `3 < "a"` stops the program with a `TypeError`, because Python refuses to guess whether a number comes before a word. Asking whether they are *equal* is allowed and answers `False`.

Sequences (lists, tuples, strings) compare the way a dictionary orders words, which is called **lexicographic** order: compare the first items; if they differ, that decides; if they are equal, move on to the next pair; if one sequence runs out first, the shorter one is smaller.

```python-run
print((1, 2, 3) < (1, 3), [1, 2] < [1, 2, 0], "apple" < "banana", "Zebra" < "apple")
```

All four are `True`. In the first, the second items decide (2 < 3). In the second, `[1, 2]` is a beginning of `[1, 2, 0]` and therefore smaller. The last one surprises people: `"Zebra" < "apple"` because every character has a number (its **code point**) and capital letters have smaller numbers than lowercase ones. For ordering that ignores case, compare lowercase copies, for example `sorted(words, key=str.lower)`. Tuple comparison is also the reason sorting a list of tuples sorts by the first field, then the second, and so on.

## Logical operators and short-circuiting

`and`, `or` and `not` combine conditions. They work on truthiness, so any object may appear next to them. Two facts about `and` and `or` are easy to miss:

1. They **short-circuit**: Python evaluates the left side first and skips the right side entirely when the left side already settles the answer.
2. They return **one of their operands**, not necessarily `True` or `False`.

The exact rules:

- `a or b` gives `a` if `a` is truthy, otherwise `b`.
- `a and b` gives `a` if `a` is falsy, otherwise `b`.

```python-run
print(0 or "default")        # 'default'
print("given" or "default")  # 'given'
print([] and 1 / 0)          # [] — the division never runs
name = ""
display = name or "anonymous"
print(display)
```

**Reading this code line by line**

- `0 or "default"`: 0 is falsy, so the result is the right operand, the text `default`.
- `"given" or "default"`: the left side is a non-empty string, so it is truthy and is returned as it is; the right side is never looked at.
- `[] and 1 / 0`: an empty list is falsy, so `and` returns it immediately. `1 / 0` would crash the program, but it is never evaluated. That is short-circuiting at work.
- `name or "anonymous"` is the common "use this, or a fallback if it is empty" pattern; it prints `anonymous`.

The `x or default` pattern has the same trap as every truthiness test: it replaces *every* falsy value, including a legitimate `0`. When only `None` means "missing", write `x if x is not None else default`.

Short-circuiting is also how you protect an expression that might fail. In `if i < len(a) and a[i] == target:`, the item `a[i]` is fetched only when the position `i` is known to exist.

## Bitwise operators

Inside the computer an integer is a row of **bits**, binary digits that are each 0 or 1. The **bitwise** operators work on those rows position by position: `&` (and: 1 where both bits are 1), `|` (or: 1 where at least one is 1), `^` (xor, "exclusive or": 1 where the bits differ), `~` (invert every bit), `<<` and `>>` (shift the row left or right, which multiplies or divides by a power of two).

Python integers behave as if they had endlessly many bits in **two's complement**, the standard way of writing negative numbers in binary, which is why `~5 == -6` and `-1 >> 10 == -1`. The same symbols have other meanings on other types: on sets, `&`, `|`, `^` and `-` mean intersection, union, symmetric difference and difference, and on dictionaries (Python 3.9 and later) `|` merges.

```python-run
print(6 & 3, 6 | 3, 6 ^ 3, ~5, 1 << 10)
print(bin(42), (42).bit_count() if hasattr(int, "bit_count") else bin(42).count("1"))
print({1, 2, 3} & {2, 3, 4}, {"a": 1} | {"b": 2})
x = 12
print("power of two?", x > 0 and x & (x - 1) == 0)
```

6 is `110` in binary and 3 is `011`, so the first line prints `2 7 5 -6 1024`. `bin(42)` shows the binary form `0b101010`, and the expression after it counts the 1 bits (three). The third line shows the set and dictionary meanings: `{2, 3}` and `{'a': 1, 'b': 2}`. The last line is a classic trick: a power of two has exactly one 1 bit, and `x & (x - 1)` clears the lowest 1 bit, so the result is zero only for powers of two. 12 is `1100`, not a power of two, so it prints `False`.

## Precedence (highest to lowest)

**Precedence** is the rule for which operator is applied first when an expression has several, the way multiplication comes before addition in school arithmetic. Operators higher in this table bind more tightly.

| Level | Operators |
|---|---|
| 1 | `(...)`, `[...]`, `{...}`; attribute access `x.y`, indexing `x[i]`, calls `f(x)` |
| 2 | `**` (groups from the right; binds tighter than a minus sign on its left) |
| 3 | unary `+x`, `-x`, `~x` (unary means "taking one operand") |
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

Three surprises are worth memorising. `-2 ** 2` is `-4`, because the power is computed before the minus sign is applied. `2 ** 3 ** 2` is 512, because powers group from the right: it means `2 ** (3 ** 2)`. And `x & 1 == 0` means `(x & 1) == 0`, because comparisons rank *below* the bitwise operators. That is the opposite of C, where the same text means `x & (1 == 0)`. When in doubt, add parentheses; they cost nothing and readers will thank you.

```python-run
print(-2 ** 2, (-2) ** 2, 2 ** 3 ** 2)
x = 6
print(x & 1 == 0)     # (x & 1) == 0 in Python
print(not 1 == 2)     # not (1 == 2)
```

The output is `-4 4 512`, then `True` (6 is even, so its lowest bit is 0), then `True` (`not` applies to the whole comparison).

## Conditional expressions and the walrus operator

An `if` statement chooses between blocks of lines. A **conditional expression** chooses between two values inside a single line. Its shape is `value_if_true if condition else value_if_false`:

```python-run
n = -3
abs_n = n if n >= 0 else -n
parity = "even" if n % 2 == 0 else "odd"
print(abs_n, parity)
```

Read the second line as "`abs_n` is `n` if `n` is at least zero, otherwise `-n`". With `n = -3` the program prints `3 odd`. (`-3 % 2` is 1 in Python, so the test for odd works for negative numbers too.)

The **assignment expression** `:=`, nicknamed the walrus operator because it looks like a walrus on its side, was added in Python 3.8. It ties a name to a value *in the middle of* an expression, so that you can test a value and keep it in one step.

```python-run
import io
stream = io.StringIO("alpha\nbeta\n\ngamma\n")
while (line := stream.readline().strip()):
    print("got", line)          # stops at the first blank line

nums = [3, 8, 1, 10]
print([y for x in nums if (y := x * x) > 10])
```

`io.StringIO` gives an object that behaves like an open text file. Each time round the `while`, `stream.readline().strip()` reads the next line and removes the line break; `:=` stores that text in `line`; and the loop continues only while the text is non-empty. The loop prints `got alpha` and `got beta`, then meets the empty third line and stops, never reaching `gamma`. In the last line, each square is computed once, stored in `y`, tested, and reused: `[64, 100]`.

## The `if` statement

```python
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"
```

Python checks the conditions from top to bottom and runs the block under the first one that is true; `elif` is short for "else if", and `else` catches everything left over. The lines that belong to each branch are marked by **indentation**: they are shifted right by the same amount (the official style guide, PEP 8, says four spaces). There are no curly braces as in C or Java; the shape of the text *is* the structure. Classic Python has no `switch` statement. Long `if`/`elif` chains or a dictionary that maps each case to a function are the traditional substitutes, and Python 3.10 added `match`, shown below.

## `while` loops

A `while` loop repeats its block as long as its condition is truthy.

```python-run
# Euclid's algorithm
a, b = 252, 105
while b:
    a, b = b, a % b
print("gcd =", a)
```

This is Euclid's method for the greatest common divisor, the largest number that divides both inputs. `while b:` means "while `b` is not zero". The line inside the loop is a **tuple assignment**: Python first works out the whole right-hand side (`b` and `a % b`, using the *old* values), then ties the two names on the left to the two results. No temporary variable is needed. The pairs go (252, 105), (105, 42), (42, 21), (21, 0), and the program prints `gcd = 21`. The same feature swaps two variables in one line: `x, y = y, x`.

## `for` loops iterate over iterables

An **iterable** is any object that can hand out its items one at a time: a list, a string (letter by letter), a dictionary (key by key), an open file (line by line). A Python `for` loop is a "for each" loop: it takes the items of an iterable one after another. There is no counting form like C's `for (i = 0; i < n; i++)`. When you need positions or several lists at once, use these built-in helpers:

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

**Reading this code line by line**

- `range(len(names))` produces the positions 0, 1, 2. Looping over positions and then indexing works but is clumsy; the next two forms are preferred.
- `enumerate(names, start=1)` hands out pairs: a counter and the item. The loop unpacks each pair into `i` and `name`, printing `1 ana`, `2 ben`, `3 cy`.
- `zip(names, ages)` walks two lists side by side and hands out pairs of matching items: `ana is 31`, and so on.
- `range(10, 0, -3)` starts at 10, stops *before* 0, and steps by −3, printing `10 7 4 1`. `end=" "` tells `print` to finish with a space and not a new line.
- `reversed(names)` walks the list backwards: `cy ben ana`.

`range` is **lazy**: it computes each number when asked and never stores them all, so `range(10**12)` uses almost no memory. It still supports `len`, indexing, and a fast `in` test for integers that takes the same time however long the range is (O(1), "constant time"). `zip` stops when its shortest input runs out; pass `strict=True` (Python 3.10+) to get an error when the lengths differ.

> [!WARNING]
> Do not add or remove items from a list (or keys from a dictionary) while a loop is walking over it. With a list you silently skip items; with a dictionary Python raises `RuntimeError: dictionary changed size during iteration`. Loop over a copy (`for k in list(d):`) or build a new collection.

```python-run
nums = [1, 2, 2, 3, 2]
for x in nums:
    if x == 2:
        nums.remove(x)
print("buggy:", nums)      # a 2 survives because indices shift
```

The loop keeps an internal position. When it removes the 2 at position 1, everything after it slides one place left, so the second 2 moves into position 1 and the loop, now moving on to position 2, never looks at it. The output is `buggy: [1, 3, 2]`. The fix is to build a new list that keeps what you want:

```python-run
nums = [1, 2, 2, 3, 2]
nums = [x for x in nums if x != 2]
print("fixed:", nums)
```

## `break`, `continue` and the loop `else`

`break` leaves the innermost loop at once. `continue` skips the rest of the current pass and moves to the next item. Python loops also accept an `else` block, which runs **only if the loop finished without `break`**. It is the tidiest way to say "search, and do something if nothing was found":

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

In the first call the loop meets −4 at position 2, prints the message and breaks, so the `else` block is skipped. In the second call the loop runs out of items with no `break`, so `no negatives` is printed. Read the loop's `else` as "no break". It is rarely used, which is exactly why interviewers like to ask what it does.

Python has no way to break out of several nested loops at once. The usual answers are to move the loops into a function and `return`, to set a flag variable that the outer loop checks, or to flatten the nesting into one loop with `itertools.product` (covered in the itertools lesson).

## `pass`, `...` and empty blocks

A block may not be empty: Python needs at least one statement after the colon. `pass` is the statement that does nothing, for a branch you intend to fill in later. `...` (three dots, an object named `Ellipsis`) is also commonly used as a placeholder body.

## Structural pattern matching: `match` (3.10+)

`match` compares one value against a list of **patterns**, descriptions of a shape the value might have. It is more than a list of equality tests: a pattern can check the shape of a list or dictionary and pull pieces out of it in the same step.

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

**Reading the patterns one by one**

- `case ["go", direction]` matches a two-item sequence whose first item equals `"go"`. The second item, whatever it is, is tied to the name `direction`.
- `case ["pick", "up", *items] if items` matches a sequence starting with those two words; `*items` collects all remaining items into a list. The `if items` part is a **guard**, an extra condition: the case applies only when the list is non-empty.
- `case {"action": "say", "text": str(text)}` matches a dictionary that has those two keys, where `"text"` holds a string; the string is tied to `text`.
- `case int() | float() as n if n < 0` matches an integer or a float (`|` means "or"), names it `n`, and requires it to be negative.
- `case _` is the wildcard: it matches anything, so it acts as the "otherwise" branch.

The five inputs print `moving north`, `picking up key, map`, `saying 'hi'`, `negative number` and `unknown`.

The rule that catches people: a bare name in a pattern, such as `direction`, is a **capture**. It matches anything and ties the name to it; it does *not* compare against a variable of that name. To compare against a constant stored elsewhere, use a dotted name such as `Color.RED`. One more helpful detail: a plain string never matches a sequence pattern, so `"go"` is not mistaken for the list of letters `["g", "o"]`.

## Worked example: FizzBuzz three ways

FizzBuzz is the best-known warm-up question: print the numbers 1 to 15, but write "Fizz" for multiples of 3, "Buzz" for multiples of 5, and "FizzBuzz" for multiples of both.

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

All three print the same line. Version 1 tests "multiple of 15" first; if it tested 3 first, 15 would be labelled "Fizz" and never reach the combined case. The order of `elif` branches matters. Version 2 uses two facts from this lesson: a string times `True` is the string and times `False` is the empty string (because `True` is 1 and `False` is 0), and `or` supplies the number when both pieces are empty. It is clever, and version 1 is what you would write in real code. Version 3 matches the pair of remainders against patterns.

## Input and output basics

`print(*objects, sep=" ", end="\n")` writes its arguments separated by `sep` and finished with `end` (by default a space and a line break). `input(prompt)` shows the prompt, waits for the user to type a line, and returns it **as a string, always**; convert it with `int()` or `float()` if you need a number.

For building text out of values, use **f-strings**: a string with an `f` before the opening quote, in which anything inside curly braces is computed and inserted. After a colon you can say how the value should be laid out:

```python-run
name, total, ratio = "Brook", 1234567.891, 0.4567
print(f"{name:>8}|{total:,.2f}|{ratio:.1%}|{42:08b}|{255:#x}")
print(f"{total=}")   # self-documenting expression (3.8+)
```

The first line prints `   Brook|1,234,567.89|45.7%|00101010|0xff`. `:>8` right-aligns in a field 8 characters wide; `:,.2f` adds thousands separators and keeps two decimals; `:.1%` shows a fraction as a percentage; `:08b` is binary padded with zeros to 8 digits; `:#x` is hexadecimal with the `0x` prefix. The second line prints `total=1234567.891`: an `=` before the closing brace shows the expression as well as its value, handy when debugging.

The general layout of a format specification is `[[fill]align][sign][width][,][.precision][type]`, where align is `<`, `>` or `^` (left, right, centre) and type is a letter such as `d` (integer), `f` (fixed decimals), `e` (scientific), `%`, `b` or `x`.

> [!INTERVIEW]
> Expect quick-fire questions: What does `else` on a `for` loop do? (Runs if no `break`.) What's `a or b` when `a` is `0`? (`b`.) Why is `-7 % 3 == 2`? (Floor rounding; the result takes the sign of the divisor.) How do you swap two variables? (`a, b = b, a`.) What's the cost of `x in range(n)`? (O(1) for integers.)

## Interactive loops: input, sentinels and flags

Console programs combine `input()` with a `while` loop. Two points cause most of the trouble: `input` returns a string that must be converted (and the conversion can fail), and the loop needs a clear way out. The three usual exits are a **sentinel** (a special value such as `"q"` or an empty line that means "stop"), a Boolean **flag** (a variable that any branch can switch to `False`), or `while True` with a `break` placed exactly where the decision is made.

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

`while True` loops forever unless something breaks out. Each pass reads a line; an empty line breaks; otherwise the `try` block attempts the conversion, and if `float` raises a `ValueError` (its way of saying "this text is not a number") the `except` block reports it and `continue` starts the next pass.

The same shape drives menu programs and games: read a command, act on it, repeat until told to stop. This page cannot pause for typing, so here is the same logic with the answers supplied by a function. That is also the technique to use in tests, since logic that receives its "input" as an argument can be checked automatically:

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

`iter(...)` makes an object that hands out the prepared answers one at a time, and `lambda: next(answers)` is a tiny nameless function that fetches the next one. The output is `(119.5, ['abc'])`: 12.5 + 7 + 100 (`"1e2"` is scientific notation for 100), with `abc` rejected.

## Pitfalls recap

- `/` returns a float; use `//` for whole-number division.
- `-2 ** 2 == -4`.
- `x or default` swallows valid falsy values such as `0`.
- Changing a collection while looping over it.
- Capture patterns in `match` bind a name; they do not compare: `case RED:` matches everything. Use `case Color.RED:`.
- Expecting `zip` to complain about different lengths (it truncates unless `strict=True`).

## Summary

Python's operators mostly look like a calculator's, but division, remainder, chained comparisons, `and`/`or` returning operands, and the precedence of `**` and the bitwise operators have their own rules. Loops walk over iterables, helped by `range`, `enumerate`, `zip` and `reversed`; `else` on a loop means "completed without break"; and `match` tests the shape of a value and takes it apart in one step.

## Glossary

- **Expression** - code that produces a value, such as `a + 1`.
- **Operator / operand** - a symbol that computes, such as `+` / a value it works on.
- **Floor division** - `//`: divide and round down toward negative infinity.
- **Modulo (remainder)** - `%`: what is left over after floor division.
- **Chained comparison** - `a < b < c`, meaning `a < b and b < c`.
- **Lexicographic order** - dictionary-style ordering of sequences, item by item.
- **Short-circuit** - skipping the right side of `and`/`or` when the left side decides the answer.
- **Bit / bitwise operator** - a binary digit / an operator that works on integers bit by bit.
- **Precedence** - the rule that says which operator is applied first.
- **Conditional expression** - `x if cond else y`, a choice between two values.
- **Walrus operator** - `:=`, assignment inside an expression.
- **Control flow** - the statements that decide which lines run and how often.
- **Indentation** - leading spaces that mark which lines belong to a block.
- **Iterable** - an object that can give out its items one at a time.
- **Lazy** - computing values only when they are asked for.
- **Sentinel** - a special value that signals "stop".
- **Flag** - a Boolean variable used to remember a yes/no state.
- **Pattern / capture / guard** - in `match`: a shape to test / a bare name that binds a piece / an extra `if` condition.
- **f-string** - a string prefixed with `f` whose `{...}` parts are computed and inserted.

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
   "explain": "Tuple packing/unpacking evaluates the whole right side before assigning, so no temporary is needed."},
  {"q": "What does `6 / 2` evaluate to in Python 3?", "options": ["3", "3.0", "3.5", "It depends on the platform"], "answer": 1,
   "explain": "`/` is true division and always returns a float, even when the result is a whole number. Use `//` to get the int 3."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.3 (Expressions, Operators, and Precedence), §1.4 (Control Flow) and §1.6 (Simple I/O), restated in original wording with new examples; Python docs, *Tutorial* ch. 4 "More Control Flow Tools" and *Language Reference* §6.17 "Operator precedence".
