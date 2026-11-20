# Declarations, constants and typed versus untyped

> **Before this lesson:** read [Predeclared types, zero values and conversions](#/lesson/go/go-predeclared-types). You should know what `int`, `float64`, `string` and `bool` are, what a zero value is, and that Go refuses to mix types without an explicit conversion.

## In plain words

To **declare** something is to introduce a new name to the program and say what it stands for. Go gives you two kinds of named values:

- a **variable** is a labelled box whose content can be replaced while the program runs;
- a **constant** is a label permanently attached to one value that is known before the program starts, like the number of minutes in an hour printed on a reference card.

An everyday picture: in a kitchen, the jar labelled "sugar" is a variable, because you refill it and its level changes. The line "1 cup = 240 ml" on the conversion chart taped to the wall is a constant. Nobody edits that chart while cooking, and you may use the fact with any measuring tool you own.

That last point is the interesting part of this lesson. A Go constant written without a type behaves like the fact on the chart: it is a pure number that adapts to whatever type needs it. This is how Go stays strict about types without forcing you to write conversions around every literal `2` or `0.5`.

Why this matters for a job: choosing between `var`, `:=` and `const` is something you do on almost every line, and reviewers notice when it is done carelessly. "What is an untyped constant?" and "What does `iota` do?" are standard interview questions.

## Three ways to create a variable

### The full form

```go
var age int = 30
```

Read it as: create a variable (`var`) named `age`, of type `int`, starting at `30`. This form says everything and is the longest.

### Letting the compiler infer the type

When the starting value makes the type clear, leave the type out:

```go
var age = 30        // int
var price = 9.5     // float64
var name = "Robin"  // string
```

The compiler works out the type from the value. This is called **type inference**. The variable is still statically typed; you saved typing, nothing else.

### Leaving the value out

When you want the zero value, leave the value out and keep the type:

```go
var total int      // 0
var message string // ""
```

### Several at once

```go
var x, y int = 10, 20
var width, label = 3.5, "wide" // different types, both inferred

var (
	host    string
	port    = 8080
	retries int = 3
)
```

The parenthesised form is a **declaration list**; it groups related variables and is common at the top of a file.

### The short form: `:=`

Inside a function there is a fourth, shorter spelling:

```go
age := 30
x, y := 10, 20
```

`age := 30` means the same as `var age = 30`. The symbol `:=` is the **short variable declaration**. It both creates the variable and gives it a value, with the type inferred.

A complete program that uses all of the forms:

```go
package main

import "fmt"

var version = "1.0" // package level: var is the only choice here

func main() {
	var total int
	var ratio float64 = 0.5
	count := 3
	name, ok := "Chopper", true

	total = count * 2
	fmt.Println(version, total, ratio, count, name, ok)
}
```

```text
1.0 6 0.5 3 Chopper true
```

Line by line: `version` is declared outside any function, at **package level**, which makes it visible to every function in the package. `total` starts at its zero value. `ratio` has both a type and a value. `count` and the pair `name, ok` use the short form. `total = count * 2` uses a plain `=` because `total` already exists; **`=` assigns, `:=` declares**.

## Which form when

| Situation | Preferred form | Why |
|---|---|---|
| Inside a function, with a starting value | `x := value` | shortest and clearest |
| You want the zero value | `var x int` | says "starts at zero on purpose" |
| The literal's default type is not the one you want | `var x byte = 20` or `x := byte(20)` | `x := 20` would give `int` |
| Outside any function | `var x = value` | `:=` is not allowed at package level |

**How Python differs.** Python has one form, `x = 30`, which creates the name if it is new and rebinds it if it exists. A typo in a name (`totl = 5`) quietly creates a second variable. Go separates the two acts. Declaring with `:=` or `var` and assigning with `=` are different statements, so `totl = 5` is a compile error (`undefined: totl`) when no such variable was declared.

### Three rules for `:=`

1. **Only inside functions.** At package level every declaration starts with a keyword (`var`, `const`, `func`, `type`).
2. **At least one name on the left must be new.** `x := 1` followed by `x := 2` in the same block fails with `no new variables on left side of :=`.
3. **With several names, existing ones are reused and new ones are created**, provided the existing ones were declared in the *same* block:

```go
x := 10
x, y := 20, 30 // x is assigned, y is created
fmt.Println(x, y)
```

```text
20 30
```

Rule 3 is convenient and also the source of a classic bug called shadowing, where an inner block accidentally creates a second `x`. That gets a full lesson: [Blocks, shadowing and if](#/lesson/go/go-blocks-shadowing).

### Unused variables are errors

A variable declared inside a function and never read stops the build with `declared and not used`. This applies to local variables only; package-level variables and constants may go unused. When a function returns a value you do not need, assign it to the **blank identifier** `_`, a write-only name that discards whatever it receives:

```go
n, _ := strconv.Atoi("42") // keep the number, ignore the error (do this only in throwaway code)
```

### Avoid mutable package-level variables

A variable at package level can be changed by any function in the package, at any time. That makes it hard to reason about where a value came from. Keep package-level variables for values that are set once and then only read; pass everything else as function parameters. This advice is the same in Python, where module-level mutable state causes the same trouble.

## Constants

A constant is declared with `const`:

```go
const secondsPerMinute = 60
const greeting = "hello"

const (
	maxRetries = 3
	pi         = 3.14159
)
```

Two properties define a Go constant:

- its value is computed by the **compiler**, before the program runs;
- it can never be assigned to afterwards. `secondsPerMinute = 61` fails with `cannot assign to secondsPerMinute`.

Because the compiler must be able to compute the value, the right-hand side may contain only literals, other constants, operators, and a few built-in functions such as `len` of a constant string. A constant can be a number, a string, a rune or a boolean. **It cannot be a list, a map, a struct or the result of calling an ordinary function.**

```go
const start = time.Now() // compile error: time.Now() is not constant
```

So `const` in Go is narrower than `final` in Java or `const` in JavaScript. Those keywords mean "this variable is assigned once". Go's `const` means "this is a compile-time value". Go has no way to mark a run-time variable as read-only.

## Typed and untyped constants

Recall the strictness from the previous lesson: an `int` variable cannot be assigned to a `float64` variable without a conversion. If literals obeyed the same rule, `var f float64 = 2` would be illegal, since `2` looks like an integer. It is legal, and the reason is that the literal `2` has no fixed type yet. It is an **untyped constant**.

An untyped constant has a **kind** (integer, floating-point, rune, string or boolean) but not a type. It takes on a type at the moment it is used, as long as the value fits:

```go
package main

import "fmt"

const ten = 10 // untyped integer constant

func main() {
	var i int = ten
	var f float64 = ten
	var b byte = ten
	fmt.Println(i, f, b)
	fmt.Println(f / 4)
}
```

```text
10 10 10
2.5
```

The one constant `ten` served as an `int`, a `float64` and a `byte`. In `f / 4`, the literal `4` also became a `float64`, which is why the result is `2.5` and not `2`.

A **typed constant** is declared with an explicit type and from then on behaves like a variable of that type:

```go
const typedTen int = 10
var f float64 = typedTen
```

```text
cannot use typedTen (constant 10 of type int) as float64 value in variable declaration
```

Prefer untyped constants unless you need the type enforced, for example for a set of related values that should not be mixed with ordinary integers.

### Default types

Sometimes nothing in the context dictates a type, as in `x := 10`. Then each kind has a **default type**:

| Literal | Kind | Default type |
|---|---|---|
| `10` | integer | `int` |
| `2.5` | floating-point | `float64` |
| `'a'` | rune | `rune` (`int32`) |
| `"hi"` | string | `string` |
| `true` | boolean | `bool` |

That is why `x := 10` gives an `int` and `y := 2.5` a `float64`.

### Constants are exact

The compiler calculates with untyped numeric constants at very high precision, far beyond 64 bits. Limits apply only when the result is stored in a typed place.

```go
package main

import "fmt"

const huge = 1 << 100 // 2 to the power 100: does not fit in any integer type

func main() {
	fmt.Println(huge >> 98) // shifted back down at compile time: 4
	const sum = 0.1 + 0.2
	fmt.Println(sum == 0.3)
}
```

```text
4
true
```

`1 << 100` means "1 shifted left by 100 bits", a 31-digit number. It exists only inside the compiler; `huge >> 98` is evaluated there too, leaving `4`. Trying `fmt.Println(huge)` fails to compile with a message ending in `(overflows)`, because the value would have to become an `int`. The second result is a neat contrast with the previous lesson: with *variables*, `0.1 + 0.2 == 0.3` is false; with *constants* the arithmetic is exact, so it is true.

### Try it: which assignments does the compiler accept?

This simulation applies the rules above to pairs of (constant, target type).

```python-run
RANGES = {"int8": (-128, 127), "uint8": (0, 255), "int": (-2**63, 2**63 - 1)}

def assign(const_value, const_type, target):
    """const_type is None for an untyped constant."""
    if const_type is not None:                       # typed: must match exactly
        return "ok" if const_type == target else f"error: constant of type {const_type} is not {target}"
    if target == "float64":
        return "ok" if isinstance(const_value, (int, float)) else "error: not a number"
    if target == "string":
        return "ok" if isinstance(const_value, str) else "error: not a string"
    if isinstance(const_value, float) and const_value != int(const_value):
        return f"error: {const_value} truncated (not a whole number)"
    lo, hi = RANGES[target]
    return "ok" if lo <= const_value <= hi else f"error: {const_value} overflows {target}"

cases = [
    (10, None, "float64"), (10, None, "uint8"), (300, None, "uint8"),
    (2.0, None, "int"), (2.5, None, "int"), (10, "int", "float64"),
    (-1, None, "uint8"), ("hi", None, "string"), (2**70, None, "int"), (2**70, None, "float64"),
]
for value, ctype, target in cases:
    label = f"{'untyped' if ctype is None else ctype} {value!r}"
    print(f"{label:<32} -> {target:<8} {assign(value, ctype, target)}")
```

Notice three rows: untyped `2.0` may become an `int` because it is a whole number; untyped `2.5` may not; and the typed `int` constant is rejected for `float64` even though the value 10 would fit.

## iota: numbered constants

Programs often need a set of distinct labels: days of the week, states of an order, log levels. Go's tool for this is **`iota`**, a counter that exists only inside a `const` block. It is 0 on the first line of the block and increases by one on each following line. A line with no expression repeats the previous line's expression.

```go
package main

import "fmt"

const (
	Pending = iota // 0
	Paid           // 1  (repeats "= iota")
	Shipped        // 2
	Delivered      // 3
)

const (
	_  = iota             // skip 0
	KB = 1 << (10 * iota) // 1 << 10
	MB                    // 1 << 20
	GB                    // 1 << 30
)

func main() {
	fmt.Println(Pending, Paid, Shipped, Delivered)
	fmt.Println(KB, MB, GB)
}
```

```text
0 1 2 3
1024 1048576 1073741824
```

In the second block the first line assigns `iota` (0) to the blank identifier to skip it. On the next line `iota` is 1, so `KB` is `1 << 10`. The following lines reuse the same expression with `iota` equal to 2 and 3.

Python programmers would reach for `enum.Enum` here. Go has no enum type; a `const` block with `iota`, usually combined with a named type, is the idiom. That combination is shown in [Defined types, methods and embedding](#/lesson/go/go-types-methods).

> [!WARNING]
> Use `iota` only when the numbers themselves do not matter outside the program. If the values are stored in a database or sent over a network, write them out explicitly (`Pending = 0`, `Paid = 1`). Otherwise inserting a new line in the middle of the block silently renumbers everything after it.

## Naming

Go's naming customs are part of writing declarations well.

- Names start with a letter or underscore and continue with letters, digits and underscores. Names are case-sensitive.
- Use **camelCase** (`maxRetries`, `userName`), not snake_case. Constants are written the same way: `maxRetries`, not `MAX_RETRIES`.
- **The first letter controls visibility.** A package-level name starting with an upper-case letter (`MaxRetries`) is **exported**: other packages can use it. Lower-case names are private to the package. This is why constant names cannot follow an ALL_CAPS convention.
- **Short names for short lives.** A loop counter is `i`; a variable used across fifty lines deserves a full word. The smaller the region where a name is visible, the shorter it may be.
- Keep acronyms in one case: `userID`, `httpServer`, `ServeHTTP`.

## Pitfalls

- **`:=` at package level.** Not allowed; use `var`.
- **`:=` when you meant `=`.** Inside a nested block this creates a new variable that hides the outer one (shadowing).
- **Expecting `x := 10` to be something other than `int`**, or `x := 2.0` to be an `int`. Check the default-type table.
- **Trying to make a constant list or map.** Only numbers, strings, runes and booleans can be constants.
- **Typed constant in mixed arithmetic.** `const n int = 2; f * n` with a float `f` fails; untyped `const n = 2` works.
- **Relying on `iota` values in stored data.**
- **Unused local variables.** Remove them or use `_`.

> [!TIP]
> When you see `var x T` with no value in good Go code, read it as a signal: "the zero value is intended here". When you see `x := value`, read: "this starts with a specific value". Following that convention yourself makes your code tell the reader something for free.

> [!INTERVIEW]
> **"What is an untyped constant and why does Go have them?"** A constant declared without a type (or a bare literal) has a kind but no fixed type; the compiler keeps its exact value and gives it a type only where it is used, checking that it fits. Without this, Go's ban on implicit conversions would force conversions around every literal: `var f float64 = float64(2)`. Untyped constants give the convenience of flexible literals while variables stay strictly typed. Mention default types (`int`, `float64`, `rune`, `string`, `bool`) and that constant arithmetic is exact.

## Cheat sheet

| Goal | Code |
|---|---|
| Declare with value inside a function | `x := 10` |
| Declare at zero value | `var x int` |
| Declare with a specific type | `var x byte = 10` |
| Declare several | `a, b := 1, "two"` or `var ( ... )` |
| Assign to an existing variable | `x = 20` |
| Discard a value | `_ = value` or `n, _ := f()` |
| Constant | `const limit = 100` |
| Typed constant | `const limit int = 100` |
| Numbered constants | `const ( A = iota; B; C )` |
| Exported name | starts with a capital letter |

## Summary

- `var` works everywhere and can omit either the type or the value; `:=` is the short form for use inside functions.
- `:=` declares (at least one new name); `=` assigns. Unused local variables do not compile.
- `const` values are computed at compile time and limited to numbers, strings, runes and booleans.
- **Untyped constants** have a kind and an exact value; they take a type when used. **Typed constants** behave like variables of their type.
- With no other information, literals default to `int`, `float64`, `rune`, `string` or `bool`.
- `iota` numbers the lines of a `const` block starting from 0.
- Names use camelCase, and a capital first letter exports a name from its package.

## Glossary

- **Assignment**: giving a new value to an existing variable with `=`.
- **Blank identifier**: the name `_`, which discards whatever is assigned to it.
- **Constant**: a named compile-time value that cannot change.
- **Declaration**: a statement that introduces a new name.
- **Default type**: the type an untyped constant gets when the context does not demand one.
- **Exported**: visible from other packages; in Go, a name starting with an upper-case letter.
- **iota**: a counter usable in `const` blocks, starting at 0 and increasing per line.
- **Package level**: outside any function.
- **Short variable declaration**: the `:=` statement.
- **Type inference**: the compiler deducing a variable's type from its initial value.
- **Typed / untyped constant**: a constant with a fixed type / with only a kind.

```quiz
[
  {"q": "Which declaration is NOT allowed at package level (outside all functions)?",
   "options": ["`var count = 10`", "`const limit = 5`", "`count := 10`", "`var name string`"],
   "answer": 2,
   "explain": "The short form `:=` exists only inside functions. Every package-level declaration starts with a keyword such as `var` or `const`."},
  {"q": "What does this print? `x := 10; x, y := 20, 30; fmt.Println(x, y)`",
   "options": ["`10 30`", "`20 30`", "Compile error: x already declared", "`20 0`"],
   "answer": 1,
   "explain": "With several names on the left, `:=` needs only one new name (y). The existing x in the same block is assigned 20."},
  {"q": "Given `const ten = 10`, which statement fails to compile?",
   "options": ["`var f float64 = ten`", "`var b byte = ten`", "`var s string = ten`", "`var i int64 = ten`"],
   "answer": 2,
   "explain": "An untyped integer constant can become any numeric type in which the value fits, but its kind is integer, so it cannot become a string."},
  {"q": "What is the type of `x` after `x := 'a'`?",
   "options": ["`string`", "`byte`", "`rune` (int32)", "`char`"],
   "answer": 2,
   "explain": "A character in single quotes is a rune literal, and the default type of an untyped rune constant is `rune`, an alias for `int32`. Go has no `char` type."},
  {"q": "What does this print? `const ( A = iota; B; C ); fmt.Println(A, B, C)` (each constant on its own line)",
   "options": ["`1 2 3`", "`0 0 0`", "`0 1 2`", "`iota iota iota`"],
   "answer": 2,
   "explain": "`iota` is 0 on the first line of the block and grows by one per line; lines without an expression repeat the previous one, here `= iota`."},
  {"q": "Why does `const now = time.Now()` fail to compile?",
   "options": ["`time` cannot be imported in a file with constants", "A constant's value must be computable at compile time; a function call is evaluated at run time", "Constants must be typed", "`now` is a reserved word"],
   "answer": 1,
   "explain": "Go constants are compile-time values built from literals, other constants and operators. Anything that needs the program to run cannot be a constant; use `var`."},
  {"q": "`const typed int = 2` and `var f float64 = 1.5`. What happens with `fmt.Println(f * typed)`?",
   "options": ["Prints `3`", "Prints `3.0`", "Compile error: mismatched types float64 and int", "Prints `2`"],
   "answer": 2,
   "explain": "A typed constant behaves like a variable of its type, so no automatic conversion happens. With the untyped `const typed = 2` it would compile and print 3."},
  {"q": "A function contains `result := compute()` and never uses `result`. What happens?",
   "options": ["Nothing; unused variables are fine", "`go vet` warns but the build passes", "The build fails: declared and not used", "The variable is silently removed"],
   "answer": 2,
   "explain": "An unused local variable is a compile error. Use the value, delete the variable, or assign to `_` to discard the result on purpose."}
]
```

> **Source:** Bodner, *Learning Go* 2e, ch. 2 (topic coverage; wording and examples are original). Official references: https://go.dev/ref/spec#Variable_declarations, https://go.dev/ref/spec#Short_variable_declarations, https://go.dev/ref/spec#Constants, https://go.dev/ref/spec#Iota, https://go.dev/blog/constants
