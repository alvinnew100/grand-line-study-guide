# Unsigned and two's-complement integers

A $w$-bit pattern can be read as an integer in two standard ways: **unsigned** (only nonnegative values) or **two's complement** (the universal encoding for signed values on modern machines). The same bits, two meanings, and C converts between them silently. Many famous bugs, including security holes in real operating systems, come from exactly that silence. This lesson builds the precise mathematical model of both encodings, then studies conversion, extension and truncation.

## 1. Notation

Write a $w$-bit vector as $\vec{x} = [x_{w-1}, x_{w-2}, \dots, x_0]$, with $x_{w-1}$ the most significant bit. We define functions from bit vectors to integers:

- $B2U_w$: binary to unsigned
- $B2T_w$: binary to two's complement
- and their inverses $U2B_w$, $T2B_w$, plus conversions $T2U_w$, $U2T_w$.

## 2. Unsigned encoding

Each bit $x_i$ contributes weight $2^i$:

$$B2U_w(\vec{x}) = \sum_{i=0}^{w-1} x_i 2^i$$

So $B2U_4([1011]) = 8 + 0 + 2 + 1 = 11$. The range is $0$ to $UMax_w = 2^w - 1$ (all ones). $B2U_w$ is a **bijection**: every integer in that range has exactly one $w$-bit encoding.

## 3. Two's-complement encoding

The trick: give the most significant bit a **negative** weight.

$$B2T_w(\vec{x}) = -x_{w-1} 2^{w-1} + \sum_{i=0}^{w-2} x_i 2^i$$

The top bit is the **sign bit**. With it set, the value is negative.

| Bits (w=4) | Unsigned | Two's complement |
|---|---|---|
| 0000 | 0 | 0 |
| 0101 | 5 | 5 |
| 0111 | 7 | 7 (TMax) |
| 1000 | 8 | −8 (TMin) |
| 1011 | 11 | −8 + 3 = −5 |
| 1111 | 15 | −1 |

Key values for width $w$:

| Quantity | Value | Bit pattern |
|---|---|---|
| $TMin_w$ | $-2^{w-1}$ | `100...0` |
| $TMax_w$ | $2^{w-1} - 1$ | `011...1` |
| $-1$ | | `111...1` (same as $UMax_w$) |
| $0$ | | `000...0` |
| $UMax_w$ | $2^w - 1 = 2\,TMax_w + 1$ | `111...1` |

```python-run
def B2U(bits):            # bits is a string like "1011"
    return int(bits, 2)

def B2T(bits):
    w = len(bits)
    return int(bits, 2) - (int(bits[0]) << w)   # subtract 2^w if sign bit set

for b in ("0000", "0101", "0111", "1000", "1011", "1111"):
    print(b, B2U(b), B2T(b))

for w in (8, 16, 32, 64):
    print(f"w={w}: TMin={-(1 << (w-1))}, TMax={(1 << (w-1)) - 1}, UMax={(1 << w) - 1}")
```

Important properties:

- **Asymmetry.** $|TMin| = |TMax| + 1$: there is one more negative number than positive, because 0 takes one of the nonnegative patterns. This makes $-TMin = TMin$ in $w$-bit arithmetic, a perennial source of bugs (`abs(INT_MIN)` is negative!).
- $B2T_w$ is also a bijection onto $[TMin_w, TMax_w]$.
- In C, `<limits.h>` defines `INT_MIN`, `INT_MAX`, `UINT_MAX`, and so on. The C standard historically did not *require* two's complement, but virtually every machine uses it, and C23 finally made it mandatory. Java requires it.

> [!NOTE]
> **Why two's complement?** Because the hardware for addition is the same as for unsigned! Adding the bit patterns as if they were unsigned and dropping the carry out gives the correct two's-complement sum. Older alternatives, **ones' complement** (top bit weight $-(2^{w-1}-1)$) and **sign-magnitude** (top bit just flips the sign), both have two representations of zero (+0 and −0) and need separate adder logic. Sign-magnitude survives today in floating point.

<div class="widget" data-widget="bits"></div>

## 4. Conversions between signed and unsigned

C allows casting between signed and unsigned types of the same size. On two's-complement machines the rule is: **the bit pattern is unchanged; only the interpretation changes**.

For example, `short v = -12345;` has bit pattern `0xCFC7`. `(unsigned short) v` is therefore 53191.

Mathematically, for $TMin_w \le x \le TMax_w$:

$$T2U_w(x) = \begin{cases} x + 2^w, & x < 0 \\ x, & x \ge 0 \end{cases}$$

and for $0 \le u \le UMax_w$:

$$U2T_w(u) = \begin{cases} u, & u \le TMax_w \\ u - 2^w, & u > TMax_w \end{cases}$$

Derivation: $B2U_w(\vec{x}) - B2T_w(\vec{x}) = x_{w-1}(2^{w-1} - (-2^{w-1})) = x_{w-1} 2^w$. The sign bit is worth $+2^{w-1}$ unsigned but $-2^{w-1}$ signed, a difference of $2^w$.

So small positive numbers are unaffected, negative numbers become large positives, and $-1$ becomes $UMax$.

```python-run
def T2U(x, w): return x + (1 << w) if x < 0 else x
def U2T(u, w): return u - (1 << w) if u >= (1 << (w-1)) else u

print(T2U(-12345, 16), hex(T2U(-12345, 16)))   # 53191 0xcfc7
print(T2U(-1, 32))                              # 4294967295
print(U2T(4294967295, 32), U2T(2147483648, 32)) # -1 -2147483648
```

### Implicit conversion in C expressions

Constants like `12345` are signed; add `U` (`12345U`) to make them unsigned. When an operation combines a signed and an unsigned operand of the same size, **C implicitly converts the signed one to unsigned** and operates on nonnegative values. For arithmetic this rarely matters (the bits are the same), but for **relational operators** it is treacherous:

| Expression | Type | Result | Why |
|---|---|---|---|
| `0 == 0U` | unsigned | 1 | |
| `-1 < 0` | signed | 1 | |
| `-1 < 0U` | **unsigned** | **0** | −1 becomes 4294967295 |
| `2147483647 > -2147483647 - 1` | signed | 1 | |
| `2147483647U > -2147483647 - 1` | unsigned | **0** | right side is 2147483648U |
| `2147483647 > (int) 2147483648U` | signed | 1 | cast gives −2147483648 |
| `-1 > -2` | signed | 1 | |
| `(unsigned) -1 > -2` | unsigned | 1 | 4294967295 > 4294967294 |

> [!WARNING]
> **Why is `INT_MIN` written as `(-2147483647 - 1)` in `<limits.h>`?** Because the literal `2147483648` does not fit in `int`, so `-2147483648` is the negation of a value of a *larger* type (`long` on 64-bit, or even unsigned in old C90 rules). Writing it as an expression keeps the type `int`.

## 5. Expanding: zero and sign extension

To convert to a *larger* type while preserving the value:

- **Zero extension** for unsigned: add leading zeros.
- **Sign extension** for two's complement: add copies of the sign bit.

Sign extension works because, going from $w$ to $w+1$ bits with sign bit 1, the new top bit is worth $-2^w$ and the old top bit changes from $-2^{w-1}$ to $+2^{w-1}$: net change $-2^w + 2^{w-1} + 2^{w-1} = 0$. By induction, any number of copies preserves the value.

For `short sx = -12345` (`cf c7`): `int x = sx` is `ff ff cf c7` (−12345). For `unsigned short usx = 53191` (`cf c7`): `unsigned ux = usx` is `00 00 cf c7` (53191).

**Order of conversions.** When converting `short` to `unsigned`, C first changes the *size* (sign-extending, since the source is signed), then the signedness. So `(unsigned) sx` for `sx = -12345` is `0xFFFFCFC7` = 4294954951, not 53191. That is, `(unsigned) sx == (unsigned) (int) sx`.

```python-run
def sign_extend(pattern, from_w, to_w):
    sign = (pattern >> (from_w - 1)) & 1
    if sign:
        pattern |= ((1 << to_w) - 1) ^ ((1 << from_w) - 1)   # set the new high bits
    return pattern

p = 0xCFC7
print(hex(sign_extend(p, 16, 32)))   # 0xffffcfc7
print(hex(p))                        # zero extension leaves 0x0000cfc7
x = sign_extend(p, 16, 32)
print("value preserved:", x - (1 << 32))
```

## 6. Truncating

Converting to a *smaller* type drops high-order bits. Truncating to $k$ bits:

- Unsigned: $x' = x \bmod 2^k$.
- Two's complement: $x' = U2T_k(x \bmod 2^k)$: take the low $k$ bits, then reinterpret.

Example: `int x = 53191; short sx = (short) x;` gives −12345 (the low 16 bits `0xCFC7` read as signed). Converting back with `int y = sx;` gives −12345, so a round trip through a narrower type can change the value.

| Bits $(w=4)$ | Unsigned | → 3 bits | Signed | → 3 bits |
|---|---|---|---|---|
| 1011 | 11 | 3 (011) | −5 | 3 |
| 1001 | 9 | 1 (001) | −7 | 1 |
| 1111 | 15 | 7 (111) | −1 | −1 |

Note that −1 truncates to −1 (all ones stays all ones), and $11 \bmod 8 = 3$.

## 7. Advice on signed vs. unsigned

The implicit casting has caused real bugs. Two from the book:

**Loop that never ends.**

```c
float sum_elements(float a[], unsigned length) {
    float result = 0;
    for (int i = 0; i <= length - 1; i++)   // BUG when length == 0
        result += a[i];
    return result;
}
```

With `length = 0`, `length - 1` is computed with unsigned arithmetic and becomes $UMax$. Every `i` satisfies the test (the comparison is unsigned), so the loop runs off the array and crashes. Fix: `i < length`.

**`strlen` subtraction.**

```c
/* Determine whether string s is longer than string t */
int strlonger(char *s, char *t) {
    return strlen(s) - strlen(t) > 0;       // BUG
}
```

`strlen` returns `size_t`, an unsigned type. The difference is never negative, so the function returns 1 whenever the lengths differ, even when `s` is shorter. Fix: `return strlen(s) > strlen(t);`.

**A real security hole.** A version of FreeBSD's `getpeername` code passed a signed length, after taking the minimum with a buffer size, into `memcpy`, whose `size_t` parameter is unsigned. A malicious negative `maxlen` became a huge unsigned count, letting a user read arbitrary kernel memory. The fix was to declare the length `size_t`.

> [!TIP]
> Unsigned types are great when you treat words as **collections of bits** (flags, masks, addresses, modular arithmetic, multiprecision math). Avoid them for quantities you subtract or compare against expressions that might go negative. Java, notably, has no unsigned integers at all.

> [!INTERVIEW]
> Classic question: **"What does `for (unsigned i = n; i >= 0; i--)` do?"** It loops forever: `i >= 0` is always true for unsigned, and decrementing 0 wraps to $UMax$. Similarly `if (sizeof(int) > -1)` is false, because `-1` is converted to an unsigned `size_t`.

## 8. Worked example: reading a hex dump

You see `ff ff ff 9c` in a debugger watching a 32-bit `int` on a little-endian machine, listed in address order. What is the value? Address order is least significant first, so the value is `0x9cffffff`. Its sign bit is set, so it is $\text{0x9cffffff} - 2^{32} = 2634022911 - 4294967296 = -1660944385$. If instead the debugger already printed the *value* `0xffffff9c`, it is $-100$ (because `0x9c` = 156, $156 - 256 = -100$, sign-extended). Always ask: is this a value, or a sequence of bytes in memory order?

```python-run
import struct
print(struct.unpack("<i", bytes([0xff, 0xff, 0xff, 0x9c]))[0])
print(struct.unpack(">i", bytes([0xff, 0xff, 0xff, 0x9c]))[0])
```

## 9. A mental model: the number wheel

A useful picture for everything in this lesson is a **wheel** with $2^w$ positions, one per bit pattern, arranged in counting order: `000...0`, `000...1`, and so on, wrapping from `111...1` back to `000...0`. Adding 1 always moves one step clockwise, whatever the interpretation.

- The **unsigned** reading labels the positions $0, 1, \dots, 2^w - 1$. The "seam", where the label jumps, lies between `111...1` ($UMax$) and `000...0`.
- The **two's-complement** reading uses the *same wheel* but relabels the half starting at `100...0` with $-2^{w-1}, \dots, -1$. Its seam lies between `011...1` ($TMax$) and `100...0` ($TMin$).

Now the conversion rules are visible at a glance. Casting never moves you on the wheel; it only swaps the labels, and the labels of the upper half differ by exactly $2^w$. Positions in the lower half (`0xxx`) carry the same label in both readings, which is why small nonnegative numbers are unaffected by casts. And a comparison such as `-1 < 0U` goes wrong because the unsigned labels place `111...1` at the *far end* of the wheel from `000...0`, not just before it.

Try it with $w = 3$: the patterns `000`–`111` read 0, 1, 2, 3, 4, 5, 6, 7 unsigned and 0, 1, 2, 3, −4, −3, −2, −1 signed. Pattern `110` is 6 or −2, and $6 - (-2) = 8 = 2^3$. The same wheel will explain overflow in the next lesson: crossing a seam is exactly what overflow means.

```python-run
w = 3
for u in range(1 << w):
    t = u - (1 << w) if u >> (w - 1) else u
    print(f"{u:03b}  unsigned={u}  signed={t:2}  difference={u - t}")
```

## 10. Summary

- $B2U_w(\vec x) = \sum x_i 2^i$; $B2T_w$ gives the top bit weight $-2^{w-1}$.
- Ranges: unsigned $[0, 2^w-1]$; two's complement $[-2^{w-1}, 2^{w-1}-1]$, asymmetric.
- Casting between signed and unsigned keeps the bits: $T2U_w(x) = x + 2^w$ for $x<0$.
- Mixed signed/unsigned expressions are evaluated as unsigned, which breaks comparisons.
- Widen with zero extension (unsigned) or sign extension (signed); narrow by truncating high bits.

## Check yourself

```quiz
[
  {"q": "What is B2T_4([1011])?", "options": ["11", "-3", "-5", "-11"], "answer": 2,
   "explain": "-8 + 0 + 2 + 1 = -5."},
  {"q": "What is (unsigned) -1 for a 32-bit int?", "options": ["1", "2147483647", "4294967295", "-1"], "answer": 2,
   "explain": "The bits are all ones; read as unsigned that is UMax = 2^32 - 1."},
  {"q": "In C on a 32-bit int machine, what is the value of the expression -1 < 0U?", "options": ["1", "0", "Undefined", "Compile error"], "answer": 1,
   "explain": "The signed -1 is converted to unsigned 4294967295, which is not less than 0."},
  {"q": "short sx = -12345 (0xCFC7). What is (unsigned) sx?", "options": ["53191", "0x0000CFC7", "0xFFFFCFC7", "12345"], "answer": 2,
   "explain": "C first sign-extends to int (0xFFFFCFC7), then reinterprets as unsigned."},
  {"q": "Truncating the 4-bit two's-complement value 1001 (-7) to 3 bits gives:", "options": ["-7", "1", "-1", "-3"], "answer": 1,
   "explain": "Keep the low 3 bits 001, which is 1 in 3-bit two's complement."},
  {"q": "Why is -TMin equal to TMin in w-bit two's complement?", "options": ["Because of sign extension", "Because the range is asymmetric: +2^(w-1) is not representable and wraps", "Because negation is undefined", "It is not; -TMin = TMax"], "answer": 1,
   "explain": "The true result 2^(w-1) exceeds TMax and wraps around to -2^(w-1)."},
  {"q": "A function returns strlen(s) - strlen(t) > 0. When is it wrong?", "options": ["Never", "When s is shorter than t: the unsigned difference wraps to a huge positive", "When both are empty", "When s is longer than t"], "answer": 1,
   "explain": "size_t arithmetic cannot go negative; a 'negative' difference becomes a large positive and the test returns 1."},
  {"q": "Sign-extending the 8-bit pattern 0x9C to 16 bits gives:", "options": ["0x009C", "0xFF9C", "0x9C00", "0x9CFF"], "answer": 1,
   "explain": "The sign bit of 0x9C is 1, so the new high byte is all ones. Both represent -100."}
]
```

> **Source:** CS:APP 3e, §2.2 (Integer representations: integral data types, unsigned and two's-complement encodings, conversions, signed vs. unsigned in C, expanding and truncating, advice on signed vs. unsigned).
