# Primitive types and how numbers are stored

> **Before this lesson:** you can declare variables such as `int crates = 12;` and write `if` and `while` ([Anatomy of a class, main, and your first statements](#/lesson/java/java-class-anatomy)). No knowledge of binary is assumed.

## In plain words

Think of the cups in a coffee shop: espresso, small, medium, large. Each size holds a fixed amount. Pour a large coffee into an espresso cup and most of it spills. Pour an espresso into a large cup and it fits with room to spare.

Java variables are cups. For plain values such as numbers, single characters and true/false, Java offers eight cup sizes called the **primitive types**. Each has a fixed size in memory and therefore a fixed range of values. The compiler stops you pouring a big cup into a small one unless you say explicitly "I accept the spill".

Why this matters for a job: money totals that silently wrap round to negative numbers, averages that lose their fraction, and loops that never end because a counter overflowed are real production bugs. "What does this arithmetic print?" is one of the most common Java screening questions.

## Bits and bytes in sixty seconds

Computer memory is a long row of switches that are either off or on, written 0 and 1. One switch is a **bit**. Eight bits form a **byte**. With 8 bits there are $2^8 = 256$ different on/off patterns, so one byte can stand for 256 different values. With 32 bits there are $2^{32}$, a little over four billion.

A type's size in bits decides how many different values it can hold. That is the entire reason the ranges below look the way they do.

## The eight primitive types

| Type | Size | Holds | Range | Example literal |
|---|---|---|---|---|
| `byte` | 8 bits | whole number | -128 to 127 | `byte b = 100;` |
| `short` | 16 bits | whole number | -32,768 to 32,767 | `short s = 3000;` |
| `int` | 32 bits | whole number | about -2.1 billion to 2.1 billion | `int i = 250000;` |
| `long` | 64 bits | whole number | about ±9.2 quintillion | `long n = 9000000000L;` |
| `float` | 32 bits | fractional number | about 7 significant digits | `float f = 2.5f;` |
| `double` | 64 bits | fractional number | about 15 significant digits | `double d = 2.5;` |
| `char` | 16 bits | one character | 0 to 65,535 (a character code) | `char c = 'K';` |
| `boolean` | not specified | truth value | `true` or `false` | `boolean ok = true;` |

A **literal** is a value written directly in the code, such as `42` or `'K'`.

Everyday guidance:

- Use `int` for whole numbers unless you have a reason not to.
- Use `long` when values can pass two billion: timestamps in milliseconds, file sizes, database ids.
- Use `double` for measurements and scientific values. Do **not** use it for money; see below.
- `byte`, `short` and `float` are for special situations such as large arrays of raw data.

Literal rules that trip people up:

- A whole-number literal is an `int`. To write a `long` literal add `L`: `9000000000L`. Without the `L` that number does not compile, because it is too large for an `int`.
- A literal with a decimal point is a `double`. To write a `float` literal add `f`: `2.5f`.
- Underscores may be used to make long numbers readable: `1_000_000`.
- A `char` uses **single** quotes and holds exactly one character: `'K'`. Double quotes make a `String`, which is an object, not a primitive.

## Integer division and remainder

When both sides of `/` are whole-number types, Java does **integer division**: the fractional part is discarded (the result moves toward zero).

```java
public class Division {
    public static void main(String[] args) {
        System.out.println(17 / 5);      // int / int
        System.out.println(17 % 5);      // remainder
        System.out.println(-17 / 5);     // truncates toward zero
        System.out.println(-17 % 5);     // sign follows the left operand
        System.out.println(17 / 5.0);    // one double makes it double division
        System.out.println(1 / 2 * 10);  // left to right: (1 / 2) is 0
    }
}
```

```text
3
2
-3
-2
3.4
0
```

- `17 / 5` is 3 because 5 goes into 17 three whole times.
- `%` is the **remainder** operator: what is left after integer division. `17 % 5` is 2.
- With negative numbers Java rounds the quotient toward zero, so `-17 / 5` is `-3`, and the remainder takes the sign of the left-hand value: `-2`. (Python gives `-4` and `3` for the same inputs. This difference is a classic trap.)
- If either side is a `double`, the other is converted to `double` and you get ordinary division.
- The last line shows order: `1 / 2` is computed first, giving `0`, and `0 * 10` is `0`.

A handy identity always holds for whole numbers: `(a / b) * b + (a % b) == a`.

## Overflow: when the cup is full

An `int` has exactly 32 bits. If a result needs more, the extra bits are dropped and the value **wraps around** with no error and no warning.

```java
public class Overflow {
    public static void main(String[] args) {
        int big = Integer.MAX_VALUE;          // 2147483647
        System.out.println(big);
        System.out.println(big + 1);          // wraps to the most negative int

        int msPerDay = 24 * 60 * 60 * 1000;   // 86,400,000 fits
        int msPer30Days = msPerDay * 30;      // 2,592,000,000 does not fit
        System.out.println(msPer30Days);

        long correct = msPerDay * 30L;        // 30L forces long arithmetic
        System.out.println(correct);
    }
}
```

```text
2147483647
-2147483648
-1702967296
2592000000
```

`Integer.MAX_VALUE` is a named constant holding the largest `int`. Adding 1 gives the smallest. Think of a car's mileage counter rolling from 999999 to 000000, except that the roll-over lands on the most negative number.

The line `long wrong = msPerDay * 30;` would **still** be wrong: the multiplication happens in `int` (both operands are `int`), overflows, and only then is the wrapped result widened to `long`. Making one operand a `long` (`30L`) makes the whole multiplication happen in 64 bits.

> [!WARNING]
> The type of an arithmetic result is decided by the operand types, never by the variable you store it in. `long x = intA * intB;` overflows first and widens afterwards.

If you want an error instead of silent wrap-around, use `Math.addExact`, `Math.multiplyExact` and friends; they throw `ArithmeticException` on overflow.

### A wrap-around model you can run

Python integers never overflow, so we can model Java's rule exactly: keep the low 32 (or 64) bits and reinterpret the top bit as the sign.

```python-run
def wrap(v, bits):
    """What Java stores when the true result is v, for an int (32) or long (64)."""
    v &= (1 << bits) - 1                 # keep only the low bits
    return v - (1 << bits) if v >= 1 << (bits - 1) else v

def jdiv(a, b):                          # Java integer division: toward zero
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q

def jmod(a, b):                          # Java remainder: sign of the left operand
    return a - jdiv(a, b) * b

print("MAX + 1        :", wrap(2147483647 + 1, 32))
print("ms in 30 days  :", wrap(86_400_000 * 30, 32), "(int)   ", wrap(86_400_000 * 30, 64), "(long)")
print("-17 / 5, -17 % 5:", jdiv(-17, 5), jmod(-17, 5), "  (Python gives", -17 // 5, -17 % 5, ")")
print("MIN * -1       :", wrap(-2147483648 * -1, 32))
```

The last line is a famous oddity: negating the smallest `int` gives the same number back, because +2,147,483,648 does not exist in 32 bits. For the same reason `Math.abs(Integer.MIN_VALUE)` is negative.

You can also explore bit patterns with the widget:

<div class="widget" data-widget="bits"></div>

## Widening and narrowing

Moving a value into a bigger cup is always safe, so Java does it automatically. This is **widening**. The allowed automatic direction is:

```mermaid
flowchart LR
  byte --> short --> int --> long --> float --> double
  char --> int
```

Moving into a smaller cup might lose information, so the compiler demands a **cast**: the target type in parentheses, which is your written promise that you accept the loss. This is **narrowing**.

```java
public class Casting {
    public static void main(String[] args) {
        int crates = 42;
        long big = crates;               // widening: automatic
        double d = crates;               // widening: 42.0

        double price = 9.99;
        // int bad = price;              // does not compile: possible lossy conversion
        int whole = (int) price;         // narrowing cast: fraction is cut off
        System.out.println(whole);

        int large = 300;
        byte small = (byte) large;       // keeps the low 8 bits
        System.out.println(small);

        System.out.println((int) -3.7);  // toward zero, not rounding
        System.out.println(Math.round(-3.7));
    }
}
```

```text
9
44
-3
-4
```

- `(int) 9.99` is `9`. A cast from fractional to whole **truncates**; it does not round. Use `Math.round` to round.
- `(byte) 300` keeps the low 8 bits. 300 is 256 + 44, so the result is 44.
- Widening `long` to `float` or `double` is automatic even though very large `long` values lose their last digits. It is allowed because the magnitude survives.

### The small-type promotion rule

In arithmetic, `byte`, `short` and `char` are first converted to `int`. The result is therefore an `int`:

```java
byte a = 10;
byte b = 20;
// byte c = a + b;        // does not compile: a + b is an int
byte c = (byte) (a + b);   // fine
a += b;                    // also fine: compound assignment contains a hidden cast
```

The **compound assignment** operators (`+=`, `-=`, `*=`, `/=`) cast the result back to the variable's type for you. That is convenient, and it also means `a += 1000;` on a `byte` compiles and silently wraps.

## char is a number in disguise

A `char` stores a character's numeric code from the **Unicode** table, the international list that assigns a number to every character. `'A'` is 65, `'a'` is 97, `'0'` is 48.

```java
public class Chars {
    public static void main(String[] args) {
        char letter = 'A';
        System.out.println(letter);          // prints the character
        System.out.println(letter + 1);      // char + int is an int
        System.out.println((char) (letter + 1));
        System.out.println('7' - '0');       // digit character to its value
        letter++;                            // ++ keeps the type char
        System.out.println(letter);
    }
}
```

```text
A
66
B
7
B
```

`letter + 1` is an `int` (the promotion rule), so `println` shows the number 66. Casting back to `char` shows `B`. Subtracting `'0'` from a digit character is the standard trick for turning `'7'` into the number 7.

## Text plus numbers: the left-to-right rule

`+` means addition for numbers and concatenation when either side is a `String`. Java evaluates `+` from left to right, and that decides which meaning applies at each step.

```java
System.out.println(1 + 2 + "3");     // 3 then "33"
System.out.println("1" + 2 + 3);     // "12" then "123"
System.out.println('a' + 'b');       // two chars: numeric addition
System.out.println("" + 'a' + 'b');  // starts as text
System.out.println('a' + 1 + "z");   // 98 then "98z"
```

```text
33
123
195
ab
98z
```

Read each from the left. `1 + 2` is numeric: 3. Then `3 + "3"` involves a `String`, so it concatenates: `"33"`. In the third line no `String` appears at all, so the two `char` values are added as numbers: 97 + 98.

## Fractional numbers are approximate

`float` and `double` store numbers in binary **floating point**, a format that cannot represent most decimal fractions exactly, in the same way that one third cannot be written exactly in decimal.

```java
System.out.println(0.1 + 0.2);
System.out.println(0.1 + 0.2 == 0.3);
System.out.println(1.0 / 0);          // no exception for doubles
System.out.println(0.0 / 0);
```

```text
0.30000000000000004
false
Infinity
NaN
```

Consequences:

- Never compare `double` values with `==`. Check that their difference is tiny: `Math.abs(a - b) < 1e-9`.
- Never store money in `double`. Use whole numbers of the smallest unit (`long` cents) or `BigDecimal`, covered in [Everyday habits: scope, for-each, libraries, money and boxing](#/lesson/java/java-ej-everyday-habits).
- Dividing a `double` by zero gives `Infinity` or `NaN` ("not a number") instead of throwing. `NaN` is not equal to anything, including itself.

<div class="widget" data-widget="float"></div>

## Increment, decrement and their two forms

`i++` and `++i` both add one to `i`. They differ in the **value of the expression**:

```java
int i = 5;
int a = i++;   // a gets the OLD value 5, then i becomes 6
int b = ++i;   // i becomes 7 first, then b gets 7
System.out.println(i + " " + a + " " + b);
```

```text
7 5 7
```

Used on a line alone (`i++;`) the two forms are identical. Avoid mixing them into larger expressions; interviewers do it to test you, and good code does not.

> [!INTERVIEW]
> Expect: "What is the output of `int x = 5; x = x++ + ++x;`?" Work left to right. `x++` yields 5 and makes x 6. `++x` makes x 7 and yields 7. The sum 12 is then assigned to x. Answer: 12. Add that you would never write this in production.

## Pitfalls

- **Integer division where a fraction was wanted.** `double avg = sum / count;` with two `int`s loses the fraction. Write `(double) sum / count`.
- **Overflow in `int` multiplication** before widening to `long`.
- **Missing `L` on a large literal**: "integer number too large".
- **Missing `f` on a float literal**: `float f = 2.5;` does not compile because `2.5` is a `double`.
- **Casting instead of rounding**: `(int) 2.99` is 2.
- **`==` on doubles**, and money in doubles.
- **Assuming Python's rules** for negative division and remainder.
- **`char` arithmetic printing numbers** when a letter was expected.

## Cheat sheet

| Expression | Value | Why |
|---|---|---|
| `7 / 2` | `3` | integer division |
| `7 / 2.0` | `3.5` | one operand is double |
| `-7 / 2`, `-7 % 2` | `-3`, `-1` | truncation toward zero; sign of left operand |
| `Integer.MAX_VALUE + 1` | `-2147483648` | 32-bit wrap-around |
| `(int) 3.99` | `3` | cast truncates |
| `(byte) 200` | `-56` | keeps low 8 bits |
| `'A' + 1` | `66` | char promoted to int |
| `(char) ('A' + 1)` | `'B'` | cast back |
| `1 + 2 + "x"` | `"3x"` | left to right |
| `"x" + 1 + 2` | `"x12"` | left to right |
| `0.1 + 0.2 == 0.3` | `false` | binary floating point |

## Summary

- Java has eight primitives: `byte`, `short`, `int`, `long`, `float`, `double`, `char`, `boolean`.
- Sizes are fixed, so ranges are fixed; exceeding a range wraps silently.
- Integer division truncates toward zero; `%` takes the sign of the left operand.
- Widening is automatic; narrowing needs a cast and may lose data.
- `byte`, `short` and `char` are promoted to `int` in arithmetic; compound assignment hides a cast.
- `+` concatenates as soon as a `String` is involved, reading left to right.
- Floating-point numbers are approximations: no `==`, no money.

## Glossary

- **Primitive type**: one of the eight built-in value types that are not objects.
- **Bit / byte**: a single 0-or-1 switch; a group of eight bits.
- **Literal**: a value written directly in source code.
- **Integer division**: division of whole numbers that discards the fraction.
- **Remainder (`%`)**: what is left over after integer division.
- **Overflow**: a result too large for its type, which wraps around.
- **Widening**: automatic conversion to a larger type.
- **Narrowing**: conversion to a smaller type, requiring a cast.
- **Cast**: a type in parentheses that forces a conversion, e.g. `(int) x`.
- **Promotion**: automatic conversion of small types to `int` in arithmetic.
- **Unicode**: the standard that assigns a number to every character.
- **Floating point**: the approximate binary format used by `float` and `double`.
- **NaN**: "not a number", the result of undefined floating-point operations.

## Check yourself

```quiz
[
  {"q": "What does `System.out.println(10 / 4 * 4);` print?", "options": ["10", "8", "10.0", "2"], "answer": 1,
   "explain": "10 / 4 is integer division giving 2; 2 * 4 is 8."},
  {"q": "What does `System.out.println(-9 % 4);` print?", "options": ["3", "-1", "1", "-3"], "answer": 1,
   "explain": "-9 / 4 truncates to -2; the remainder is -9 - (-2 * 4) = -1. The sign follows the left operand."},
  {"q": "Does this compile? `byte a = 5; byte b = 6; byte c = a + b;`", "options": ["Yes, c is 11", "No: a + b has type int", "No: byte cannot hold 11", "Yes, but it overflows"], "answer": 1,
   "explain": "byte operands are promoted to int, so the sum is an int and needs a cast: (byte) (a + b)."},
  {"q": "What does `System.out.println(1 + 2 + \"a\" + 1 + 2);` print?", "options": ["3a3", "12a12", "3a12", "12a3"], "answer": 2,
   "explain": "Left to right: 1 + 2 = 3 (numeric), then \"3a\", then \"3a1\", then \"3a12\"."},
  {"q": "What is the value of `long t = 1000000 * 3000;` ?", "options": ["3000000000", "-1294967296", "It does not compile", "0"], "answer": 1,
   "explain": "Both literals are int, so the multiplication overflows in 32 bits before being widened. Writing 3000L fixes it."},
  {"q": "What does `System.out.println((int) 7.9 + (int) -7.9);` print?", "options": ["0", "1", "-1", "0.0"], "answer": 0,
   "explain": "Casting truncates toward zero: 7 and -7, which sum to 0."},
  {"q": "What does `char c = 'C'; c += 2; System.out.println(c);` print?", "options": ["69", "E", "C2", "It does not compile"], "answer": 1,
   "explain": "Compound assignment includes a hidden cast back to char, so c becomes the character with code 69, which is E."},
  {"q": "Does this compile? `float rate = 0.5;`", "options": ["Yes", "No: 0.5 is a double literal; write 0.5f", "No: float cannot hold fractions", "Yes, with a warning"], "answer": 1,
   "explain": "A literal with a decimal point is a double. Narrowing double to float needs the f suffix or a cast."}
]
```

> **Source:** Head First Java, ch. 3 (primitive variables) and ch. 10 (numbers). Checked against the Java Language Specification, ch. 4 and 5 (types and conversions): https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html and https://dev.java/learn/language-basics/primitive-types/ .
