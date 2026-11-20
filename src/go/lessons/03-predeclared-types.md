# Predeclared types, zero values and conversions

> **Before this lesson:** you can create a module and run a program ([The toolchain and your first program](#/lesson/go/go-toolchain)). You have seen `fmt.Println` and `:=`. No knowledge of binary numbers is assumed; the parts you need are explained here.

## In plain words

Think of a paper form with boxes: a box with room for two digits for your age, a tick-box for "yes or no", a long line for your name. Each box has a **kind** (digits, tick, letters) and a **size**. You cannot write your name in the tick-box, and you cannot fit the number 1,000 into two digit boxes.

Variables in Go are boxes of this sort. The kind and size of a box is its **type**. Go comes with a small set of ready-made types, called the **predeclared types**, for the basic kinds of data: true/false values, whole numbers of several sizes, numbers with a fractional part, and text. Three rules make Go's boxes different from Python's:

1. **The type is fixed** when the variable is created and never changes. A box for whole numbers holds whole numbers for its entire life.
2. **A box is never empty.** If you do not put a value in, Go fills it with a well-defined default called the **zero value**.
3. **Go never changes a value's type behind your back.** To move a value into a box of another type you must write the conversion yourself.

Why this matters for a job: bugs caused by numbers that silently overflow, or by mixing units of different sizes, are real and expensive. Go's rules push those decisions into the open. Interviewers like to ask "what is the zero value of X?" and "what does this arithmetic print?" because the answers show whether you know the rules or guess.

## Zero values: there is no "uninitialised"

Start with the smallest example. `var` followed by a name and a type creates a variable without giving it a value:

```go
package main

import "fmt"

func main() {
	var count int
	var price float64
	var name string
	var ready bool

	fmt.Println(count, price, name, ready)
	fmt.Printf("%q\n", name)
}
```

```text
0 0  false
""
```

Line by line: `var count int` declares a whole-number variable; `float64` is a number that can have a fractional part; `string` is text; `bool` is a true/false value. `Println` prints the four values separated by spaces. The name is empty text, so there appear to be two spaces in a row. The last line uses `Printf` with the verb `%q`, which prints a string inside quotes so that you can see it is empty.

Each type has its own zero value:

| Type family | Zero value |
|---|---|
| whole numbers and floating-point numbers | `0` |
| `bool` | `false` |
| `string` | `""` (empty text) |
| pointers, slices, maps, channels, functions, interfaces (later lessons) | `nil`, meaning "refers to nothing" |

**How Python differs.** In Python a name does not exist until you assign to it, and reading it early raises `NameError`. In C a new variable may contain leftover garbage. Go took a third path: a declared variable always exists and always holds its type's zero. Well-designed Go types are built so that the zero value is immediately useful; you will see this idea again with counters, buffers and locks.

## bool: only true and false

A `bool` holds `true` or `false`. It is produced by comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`) and combined with `&&` (and), `||` (or) and `!` (not).

```go
age := 20
hasTicket := true
canEnter := age >= 18 && hasTicket
fmt.Println(canEnter, !canEnter)
```

```text
true false
```

One difference from Python trips people for a week: **Go has no "truthiness"**. Python lets you write `if items:` or `if count:` and treats empty or zero as false. In Go the condition of an `if` must be a `bool` and nothing else. `if count { ... }` with an `int` is a compile error; you write `if count != 0 { ... }`. It is more typing and removes a family of bugs where zero, empty and missing were confused.

## Whole numbers: several sizes

Computers store numbers in **bits**, digits that are each 0 or 1. Eight bits make a **byte**. With `n` bits you can write $2^n$ different patterns, so a type with more bits can hold larger numbers. Go offers whole-number (**integer**) types in four sizes, each in two flavours: **signed** (may be negative) and **unsigned** (zero or positive only).

| Type | Bits | Smallest | Largest |
|---|---|---|---|
| `int8` | 8 | −128 | 127 |
| `int16` | 16 | −32,768 | 32,767 |
| `int32` | 32 | −2,147,483,648 | 2,147,483,647 |
| `int64` | 64 | about −9.2 × 10¹⁸ | about 9.2 × 10¹⁸ |
| `uint8` | 8 | 0 | 255 |
| `uint16` | 16 | 0 | 65,535 |
| `uint32` | 32 | 0 | 4,294,967,295 |
| `uint64` | 64 | 0 | about 1.8 × 10¹⁹ |

Three more names exist:

- `int` and `uint` have the natural size of the machine: 64 bits on every laptop and server you are likely to use, 32 bits on some small devices.
- `byte` is another name for `uint8`. Use it when the value is a raw byte of data.
- `rune` is another name for `int32`. Use it when the value is one character ([Strings, runes and bytes](#/lesson/go/go-strings-runes) explains why a character needs 32 bits).

**Which one should you pick?** Use `int` unless you have a reason not to. Reasons: a file format or network protocol dictates an exact size; a library you call wants a specific type; or you hold millions of values and memory matters. The explicit sizes are tools for those cases, not the default.

The widget below lets you type a number and see its bits, and how the same bits read as signed or unsigned.

<div class="widget" data-widget="bits"></div>

### Writing integer values

A number written directly in code is an **integer literal**. Besides ordinary decimal you can write:

```go
million := 1_000_000 // underscores are ignored; they are for readability
mask := 0b1010       // binary (base 2): 10
perm := 0o755        // octal (base 8): 493
color := 0xFF        // hexadecimal (base 16): 255
fmt.Println(million, mask, perm, color)
```

```text
1000000 10 493 255
```

### Arithmetic, and the surprise in division

The operators are `+`, `-`, `*`, `/` and `%` (remainder). Each has a shortcut form (`x += 2`, `x *= 3`), and `x++` / `x--` add or subtract one.

```go
fmt.Println(7/2, -7/2)   // integer division
fmt.Println(7%3, -7%3)   // remainder
fmt.Println(7.0 / 2)     // one side is not a whole number
```

```text
3 -3
1 -1
3.5
```

When both sides are integers, `/` throws away the fractional part, rounding **toward zero**. Python's `//` rounds toward negative infinity, so `-7 // 2` is `-4` in Python and `-7 / 2` is `-3` in Go. The remainder `%` takes the sign of the left operand in Go (`-7 % 3` is `-1`); in Python it takes the sign of the right operand (`2`). Dividing an integer by zero stops the program with `panic: runtime error: integer divide by zero`.

### Overflow wraps around silently

Python integers grow as large as memory allows. Go integers do not: when a result needs more bits than the type has, the extra bits are discarded and the value **wraps around**, like a car odometer rolling from 999,999 to 000,000.

```go
var small int8 = 127
small++
fmt.Println(small)

var u uint8 = 0
u--
fmt.Println(u)
```

```text
-128
255
```

`int8` tops out at 127; adding one lands on the lowest value. `uint8` cannot be negative; subtracting one from zero lands on the highest value. There is **no error and no warning** at run time. The compiler does catch the case it can see in advance: `var x int8 = 200` fails with `cannot use 200 (untyped int constant) as int8 value in variable declaration (overflows)`.

Try the rule yourself. The simulation keeps only the low `bits` of the result, which is exactly what the processor does.

```python-run
def wrap(value, bits, signed):
    value &= (1 << bits) - 1              # keep only the low bits
    if signed and value >= 1 << (bits - 1):
        value -= 1 << bits                # top bit set means negative
    return value

print("int8 :", [wrap(n, 8, True) for n in (126, 127, 128, 129, 255, 256)])
print("uint8:", [wrap(n, 8, False) for n in (254, 255, 256, 257, -1)])

# A classic bug: averaging two large int32 values
a, b = 2_000_000_000, 2_000_000_000
print("true average      :", (a + b) // 2)
print("int32 a+b wraps to:", wrap(a + b, 32, True))
print("so (a+b)/2 gives  :", wrap(a + b, 32, True) // 2)
print("safe form a+(b-a)/2:", a + (b - a) // 2)
```

The last four lines show a famous mistake: the midpoint `(a + b) / 2` of two large numbers overflows, while `a + (b-a)/2` does not. Practise the rule in the problem [Fixed-width integers](#/problem/go-int-overflow).

## Floating-point numbers

A **floating-point** number can have a fractional part. Go has `float64` (64 bits, about 15 to 17 significant decimal digits) and `float32` (32 bits, about 7 digits). Use `float64` unless a library or a memory budget says otherwise; a literal such as `3.14` becomes `float64` by default.

Floating-point numbers store an approximation in binary, and most decimal fractions have no exact binary form. This is the same in Python:

```go
a, b := 0.1, 0.2
fmt.Println(a + b)
fmt.Println(a+b == 0.3)
```

```text
0.30000000000000004
false
```

Two rules follow. **Never compare floats with `==`**; check that the difference is smaller than a tolerance. And **never use floats for money**; use whole numbers of the smallest unit (cents) or a decimal library.

Dividing a float by zero does not stop the program. It yields the special values `+Inf`, `-Inf` or `NaN` ("not a number"), and `NaN` is not equal to anything, itself included.

Go also has `complex64` and `complex128` for complex numbers. They are rarely needed outside numerical code.

## Strings and runes, briefly

A `string` is text written between double quotes (`"hello\n"`, where `\n` means a new line) or between backquotes (`` `C:\temp` ``), in which backslashes are taken literally and the text may span lines. A single character between single quotes, `'a'`, is a **rune literal**: its value is the character's number in the Unicode table (97 for `a`).

```go
greeting := "Hello" + ", " + "Go"
fmt.Println(greeting, len(greeting))
fmt.Println('a', string('a'))
```

```text
Hello, Go 9
97 a
```

`+` joins strings and `len` gives the length **in bytes**. Strings are **immutable**: once created, their content cannot be changed; operations build new strings. Printing a rune shows its number unless you convert it back with `string(r)`. Strings have their own lesson later; this is enough for now.

## Conversions are explicit

Many languages quietly widen a small number when you mix it with a bigger one. Go does not. **Two variables of different types cannot be combined, even if both are numbers.**

```go
var items int = 3
var unitPrice float64 = 2.5
total := items * unitPrice
```

```text
invalid operation: items * unitPrice (mismatched types int and float64)
```

You state the conversion by using the type's name like a function: `T(value)`.

```go
package main

import "fmt"

func main() {
	var items int = 3
	var unitPrice float64 = 2.5
	total := float64(items) * unitPrice
	fmt.Println(total)

	f := 3.99
	fmt.Println(int(f), int(-f))

	big := 300
	fmt.Println(uint8(big))

	var a int32 = 10
	var b int64 = 20
	fmt.Println(int64(a) + b)
}
```

```text
7.5
3 -3
44
30
```

What each conversion did:

- `float64(items)` turned 3 into 3.0, making the multiplication legal.
- `int(f)` **cuts off** the fraction; it does not round. 3.99 becomes 3 and −3.99 becomes −3. Use `math.Round` first if you want rounding.
- `uint8(big)` kept the low 8 bits of 300. 300 − 256 = 44. Narrowing conversions lose information without any complaint.
- Even `int32` and `int64` need a conversion to be added together.

### Numbers and text

Converting between numbers and their text form is a different job, done by the standard-library package `strconv` (string conversion):

```go
package main

import (
	"fmt"
	"strconv"
)

func main() {
	s := strconv.Itoa(65) // int to text
	fmt.Println(s + "!")

	n, err := strconv.Atoi("42") // text to int; may fail
	fmt.Println(n+1, err)

	_, err = strconv.Atoi("4x2")
	fmt.Println(err)

	fmt.Println(string(rune(65)))
}
```

```text
65!
43 <nil>
strconv.Atoi: parsing "4x2": invalid syntax
A
```

`Itoa` means "integer to ASCII". `Atoi` goes the other way and returns **two** results: the number and an error value that is `nil` (nothing) on success. Returning errors as ordinary values is Go's standard approach and has [its own module](#/lesson/go/go-errors-values). The underscore `_` discards a result you do not need.

> [!WARNING]
> `string(65)` does not give `"65"`. Converting an integer to a string treats the number as a character code and yields `"A"`. `go vet` flags this. Use `strconv.Itoa(65)` or `fmt.Sprint(65)` for the digits.

## Why so strict? A comparison

| Situation | Python | Go |
|---|---|---|
| Variable used before assignment | `NameError` at run time | impossible: zero value |
| `3 * 2.5` with variables of different numeric types | converts automatically | compile error until you convert |
| Integer too large | integer grows | wraps around silently |
| `if count:` | allowed (0 is false) | compile error; write `count != 0` |
| `-7 // 2` vs `-7 / 2` | `-4` | `-3` |
| Variable changes type | allowed | never |

Neither set of choices is "right". Python optimises for getting started; Go optimises for programs that many people maintain for years, where you want the compiler to tell you about a unit mix-up before a customer does.

## Pitfalls

- **Overflow in intermediate results.** `a * b / c` can overflow in `a * b` even when the final answer fits.
- **Unsigned subtraction.** `var n uint = 0; n - 1` is a huge positive number. Loops that count down with an unsigned variable (`for i := n; i >= 0; i--`) never end, because `i >= 0` is always true.
- **`int` is not `int64`.** They are distinct types even when both are 64 bits; assigning one to the other needs a conversion.
- **Integer division where you wanted a fraction.** `1 / 3` is `0`. Write `1.0 / 3` or convert an operand.
- **Comparing floats with `==`.**
- **`string(n)` for digits.**
- **Truncation, not rounding,** when converting float to int.

> [!INTERVIEW]
> **"What happens when a Go integer overflows?"** For values computed at run time, signed and unsigned integers wrap around using two's-complement arithmetic; there is no panic. Constant expressions are evaluated exactly at compile time, so an overflowing constant assignment is a compile error. If overflow matters, check before the operation (for example compare against `math.MaxInt64 - x`) or use `math/bits` helpers; Go has no built-in checked arithmetic.

## Cheat sheet

| Need | Use |
|---|---|
| Whole number, no special reason | `int` |
| Raw data byte | `byte` (= `uint8`) |
| One character | `rune` (= `int32`) |
| Number with fraction | `float64` |
| True/false | `bool` |
| Text | `string` |
| Convert number types | `float64(i)`, `int(f)`, `int64(x)` |
| Number → text | `strconv.Itoa(n)`, `fmt.Sprint(n)` |
| Text → number | `strconv.Atoi(s)`, `strconv.ParseFloat(s, 64)` |
| Limits | `math.MaxInt64`, `math.MinInt8`, `math.MaxUint32`, ... |
| Zero values | `0`, `false`, `""`, `nil` |

## Summary

- Every variable has a fixed type and starts at that type's **zero value**.
- `bool` conditions must be real booleans; numbers and strings are never treated as true or false.
- Integers come in fixed sizes. Use `int` by default. Overflow wraps silently; integer division truncates toward zero.
- `float64` is the default for fractional numbers and is approximate; avoid `==` and avoid it for money.
- Go performs **no automatic conversions** between types. Write `T(value)`, and use `strconv` between numbers and text.

## Glossary

- **Bit / byte**: a binary digit (0 or 1) / a group of eight bits.
- **Conversion**: explicitly producing a value of another type, written `T(value)`.
- **Floating-point number**: an approximate number with a fractional part.
- **Immutable**: cannot be changed after creation.
- **Integer**: a whole number.
- **Literal**: a value written directly in source code.
- **Overflow**: a result too large (or too small) for the type; in Go it wraps around.
- **Predeclared type**: a type built into the language, such as `int` or `string`.
- **Rune**: Go's name for one Unicode character number; an alias of `int32`.
- **Signed / unsigned**: able to hold negative numbers / zero and positive only.
- **Zero value**: the default value a variable has when none is given.

```quiz
[
  {"q": "What does this print? `var s string; var n int; var ok bool; fmt.Printf(\"%q %d %t\\n\", s, n, ok)`",
   "options": ["`nil 0 false`", "`\"\" 0 false`", "It does not compile: the variables are uninitialised", "`<empty> <nil> false`"],
   "answer": 1,
   "explain": "Declared variables hold their zero values: empty string, 0 and false. `%q` prints the string in quotes, `%d` an integer, `%t` a bool."},
  {"q": "What does this print? `var x uint8 = 250; x += 10; fmt.Println(x)`",
   "options": ["`260`", "`255`", "`4`", "The program panics"],
   "answer": 2,
   "explain": "uint8 holds 0..255. 260 needs nine bits; only the low eight are kept: 260 - 256 = 4. Run-time overflow wraps silently."},
  {"q": "What is the value of `-7 / 2` in Go when both operands are integers?",
   "options": ["`-3.5`", "`-4`", "`-3`", "`3`"],
   "answer": 2,
   "explain": "Integer division truncates toward zero, giving -3. Python's `//` would give -4 because it rounds toward negative infinity."},
  {"q": "Given `var a int = 3` and `var b float64 = 1.5`, which line compiles?",
   "options": ["`c := a * b`", "`c := float64(a) * b`", "`c := a * int`", "`c := (float64)a * b`"],
   "answer": 1,
   "explain": "Go never converts between numeric types automatically. The conversion syntax is `T(value)`, so `float64(a) * b` is correct."},
  {"q": "What does `fmt.Println(string(rune(66)))` print?",
   "options": ["`66`", "`B`", "`\"66\"`", "An error"],
   "answer": 1,
   "explain": "Converting an integer (rune) to a string yields the character with that code point; 66 is `B`. To get the digits use `strconv.Itoa(66)`."},
  {"q": "Why is `if count { ... }` a compile error when `count` is an `int`?",
   "options": ["`if` needs parentheses", "Conditions must be of type bool; Go has no truthiness", "`count` must be unsigned", "It is not an error"],
   "answer": 1,
   "explain": "Only bool values may be conditions. Write `if count != 0`. Parentheses around the condition are not required in Go."},
  {"q": "What does this print? `f := 2.99; fmt.Println(int(f))`",
   "options": ["`3`", "`2`", "`2.99`", "`2.0`"],
   "answer": 1,
   "explain": "Converting a float to an integer discards the fractional part (truncation). Use `math.Round` before converting if you want 3."},
  {"q": "Which integer type should you use by default for counts and indexes?",
   "options": ["`int64`, because it is the largest", "`uint`, because counts are never negative", "`int`", "`int32`, to save memory"],
   "answer": 2,
   "explain": "`int` is the conventional default; standard-library functions such as `len` return it. Unsigned types invite wrap-around bugs in subtraction, and explicit sizes are for external formats or memory-critical data."}
]
```

> **Source:** Bodner, *Learning Go* 2e, ch. 2 (topic coverage; wording and examples are original). Official references: https://go.dev/ref/spec#Types, https://go.dev/ref/spec#The_zero_value, https://go.dev/ref/spec#Arithmetic_operators, https://go.dev/ref/spec#Conversions, https://pkg.go.dev/strconv
