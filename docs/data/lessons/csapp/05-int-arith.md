# Integer arithmetic and overflow

> **Before this lesson:** You need unsigned and two's-complement numbers, with their ranges, from [Unsigned and two’s-complement integers](#/lesson/csapp/integers), and shifts from [Bits, bytes, words and bit-level operations](#/lesson/csapp/bits-bytes).

## In plain words

When you add or multiply numbers on paper, the answer can be as long as it needs to be. Inside a computer the answer must fit in the same fixed number of bits as the inputs, and whatever does not fit is thrown away. That event is called **overflow**. A clock is the everyday model: 9 o'clock plus 5 hours is 2 o'clock, not 14, because the dial only goes to 12. Computer arithmetic works the same way with a much bigger dial. The results are entirely predictable once you know the rule, and this lesson gives the rule for addition, negation, multiplication and division by powers of two.

Why this matters at work: overflow has caused real disasters, from crashed rockets to money calculated wrongly, and it is behind many security flaws in which a size calculation wraps round to a small number. Being able to say exactly when an operation overflows, and how to test for it safely, is a practical skill and a frequent interview subject.

## Why look closer

Many beginners are surprised that adding two positive numbers can produce a negative one, or that `x < y` and `x - y < 0` can disagree. These are not bugs in the computer: they follow from the fact that computer arithmetic works on **finite** bit vectors. Integer arithmetic on $w$ bits is really **modular arithmetic**, and once you see it that way, every "weird" result becomes predictable. This lesson derives the rules for addition, negation, multiplication and division by powers of two, for both unsigned and two's-complement numbers.

## 1. Unsigned addition

Two $w$-bit unsigned numbers $0 \le x, y < 2^w$ have a true sum in $[0, 2^{w+1}-2]$, which may need $w+1$ bits. C (and the hardware) **discards the carry out**, i.e., keeps the sum modulo $2^w$:

$$x +^u_w y = \begin{cases} x + y, & x + y < 2^w \quad\text{(normal)}\\ x + y - 2^w, & 2^w \le x + y < 2^{w+1} \quad\text{(overflow)}\end{cases}$$

Example with $w = 4$: $9 + 12 = 21$, and $21 - 16 = 5$. In binary `1001 + 1100 = 1 0101`; drop the leading carry to get `0101`.

**Detecting unsigned overflow.** Let $s = x +^u_w y$. Overflow happened **iff $s < x$** (equivalently $s < y$). Intuition: if we overflowed, $s = x + (y - 2^w)$ and $y - 2^w < 0$, so $s < x$.

```c
/* Returns 1 if x + y can be computed without unsigned overflow */
int uadd_ok(unsigned x, unsigned y) {
    unsigned sum = x + y;
    return sum >= x;
}
```

<!-- walkthrough:c -->
**Reading this C line by line**

- The text between `/*` and `*/` is a comment for the reader.
- `int uadd_ok(unsigned x, unsigned y)` defines a function taking two non-negative whole numbers and returning an `int` used as a yes/no answer (1 for yes, 0 for no).
- `unsigned sum = x + y;` adds them. If the true sum is too large for the type, the stored value has wrapped round and is smaller than expected.
- `return sum >= x;` compares. If no wrap happened, adding `y` cannot have made the result smaller than `x`, so the comparison is true and gives 1. If a wrap happened, the result is smaller than `x`, the comparison is false, and the function gives 0.

**Unsigned negation.** Every element has an additive inverse modulo $2^w$: $-^u_w x$ is $0$ if $x=0$, else $2^w - x$.

## 2. Two's-complement addition

Remarkably, two's-complement addition uses **the very same bit-level operation**: add the patterns as if unsigned and truncate. Reinterpreting gives:

$$x +^t_w y = \begin{cases} x + y - 2^w, & 2^{w-1} \le x + y \quad\text{(positive overflow)}\\ x + y, & -2^{w-1} \le x + y < 2^{w-1} \quad\text{(normal)}\\ x + y + 2^w, & x + y < -2^{w-1} \quad\text{(negative overflow)}\end{cases}$$

Formally $x +^t_w y = U2T_w(T2U_w(x) +^u_w T2U_w(y))$.

Examples with $w = 4$ (range −8..7):

| $x$ | $y$ | $x + y$ | $x +^t_4 y$ | Case |
|---|---|---|---|---|
| −8 [1000] | −5 [1011] | −13 | 3 [0011] | negative overflow |
| −8 [1000] | −8 [1000] | −16 | 0 [0000] | negative overflow |
| −8 [1000] | 5 [0101] | −3 | −3 [1101] | normal |
| 2 [0010] | 5 [0101] | 7 | 7 [0111] | normal |
| 5 [0101] | 5 [0101] | 10 | −6 [1010] | positive overflow |

**Detecting two's-complement overflow.** Let $s = x +^t_w y$. Positive overflow iff $x > 0$, $y > 0$ and $s \le 0$. Negative overflow iff $x < 0$, $y < 0$ and $s \ge 0$. In words: **overflow occurs only when both operands have the same sign and the result has the opposite sign.** Adding numbers of opposite signs can never overflow.

```c
int tadd_ok(int x, int y) {
    int sum = x + y;          /* (technically UB in ISO C; wraps on gcc -fwrapv and on the hardware) */
    int neg_over = x < 0 && y < 0 && sum >= 0;
    int pos_over = x >= 0 && y >= 0 && sum < 0;
    return !neg_over && !pos_over;
}
```

> [!WARNING]
> A tempting but **wrong** test is `(sum - x == y) && (sum - y == x)`. Because two's-complement addition forms an abelian group, `(x + y) - x` evaluates to `y` *whether or not* the addition overflowed, so this check always returns 1.

> [!WARNING]
> In ISO C, **signed** overflow is *undefined behavior*, unlike unsigned wraparound, which is defined. Optimizing compilers exploit this: `if (x + 1 > x)` may be folded to `true`. The hardware wraps, but the compiler may assume overflow never happens. Check *before* adding, or use `__builtin_add_overflow`.

```python-run
def tadd(x, y, w):
    s = (x + y) & ((1 << w) - 1)
    if s >> (w - 1):
        s -= 1 << w
    if x >= 0 and y >= 0 and s < 0:   kind = "positive overflow"
    elif x < 0 and y < 0 and s >= 0:  kind = "negative overflow"
    else:                             kind = "ok"
    return s, kind

for x, y in [(-8, -5), (-8, -8), (-8, 5), (2, 5), (5, 5)]:
    print(f"{x:3} + {y:3} ->", tadd(x, y, 4))
print("INT_MAX + 1 =", tadd(2**31 - 1, 1, 32))
```

<!-- walkthrough:python-run -->
**Reading this Python line by line**

- `def tadd(x, y, w):` models adding two signed numbers that are stored in `w` bits.
- `(x + y) & ((1 << w) - 1)` adds exactly, then keeps only the lowest `w` bits. `(1 << w) - 1` is a row of `w` ones, used as a mask.
- `if s >> (w - 1):` checks the top bit of the result. If it is 1 the pattern stands for a negative number, so `s -= 1 << w` subtracts 2ʷ to get its signed value.
- The `if / elif / else` chain names the outcome: two non-negative inputs with a negative result is positive overflow; two negative inputs with a non-negative result is negative overflow; anything else is fine.
- The loop tries several pairs with `w = 4`, where the range is −8 to 7. For instance 5 + 5 prints −6 with "positive overflow".

## 3. Two's-complement negation

Every value except $TMin$ has a proper negation. For $TMin$, $-TMin$ would be $2^{w-1}$, which overflows back to $TMin$:

$$-^t_w x = \begin{cases} TMin_w, & x = TMin_w\\ -x, & x > TMin_w\end{cases}$$

**Bit-level recipes** (worth memorizing):

1. **Complement and increment**: $-x$ = `~x + 1`. For $x = 5$ = `0101`: `~x` = `1010` (−6), plus 1 = `1011` (−5).
2. **Flip everything left of the rightmost 1**: find the rightmost 1 bit; keep it and everything to its right, complement everything to its left. `0101` → rightmost 1 at bit 0 → complement bits 3..1 → `1011`. `1100` (−4) → rightmost 1 at bit 2 → `0100` (4).

Note `~x + 1 == -x` implies `~x == -x - 1`, a handy identity.

## 4. Multiplication

**Unsigned.** The true product of two $w$-bit numbers can need $2w$ bits. C truncates to the low $w$ bits: $x *^u_w y = (x \cdot y) \bmod 2^w$.

**Two's complement.** Also truncate to $w$ bits, then interpret as signed: $x *^t_w y = U2T_w((x \cdot y) \bmod 2^w)$. The key theorem: **the low $w$ bits of the product are identical for unsigned and two's-complement multiplication**, even though the full $2w$-bit products differ. So the same instruction serves both (x86-64 has separate instructions only for the *full* 128-bit product, `mulq` and `imulq` with one operand).

| Mode | $x$ | $y$ | $x\cdot y$ | truncated (3 bits) |
|---|---|---|---|---|
| Unsigned | 5 [101] | 3 [011] | 15 [001111] | 7 [111] |
| Two's comp. | −3 [101] | 3 [011] | −9 [110111] | −1 [111] |
| Unsigned | 4 [100] | 7 [111] | 28 [011100] | 4 [100] |
| Two's comp. | −4 [100] | −1 [111] | 4 [000100] | −4 [100] |

### A security case study: calloc-style overflow

The book recounts a 2002 vulnerability in Sun's XDR library. Code computed `ele_cnt * ele_size` to size a buffer for `malloc`. A malicious caller chose values whose product overflowed 32 bits to something small, so `malloc` returned a tiny buffer and the subsequent copy loop wrote far past it. The fix: check that the product does not overflow, e.g. `if (ele_size != 0 && ele_cnt > SIZE_MAX / ele_size) fail;`, or let `calloc` do it.

```python-run
def umul32(x, y): return (x * y) & 0xFFFFFFFF
cnt, size = 1 << 20, 4097           # pretend 32-bit size_t
print("true product     :", cnt * size)
print("32-bit product   :", umul32(cnt, size), "<- malloc gets a tiny buffer!")
```

## 5. Multiplying by constants

Integer multiply used to cost 10+ cycles (about 3 on the book's Core i7 Haswell), while shifts and adds take 1. So compilers replace multiplication by a constant with shifts and adds.

- $x \cdot 2^k$ = `x << k`, for both unsigned and two's complement, even with overflow (the bits are the same).
- $x \cdot 14$: since $14 = 2^3 + 2^2 + 2^1$, compute `(x<<3) + (x<<2) + (x<<1)`, or better, since $14 = 2^4 - 2^1$, `(x<<4) - (x<<1)`.

General rule: for a run of ones from bit $m$ down to bit $n$ in $K$, use either $\sum_{i=n}^{m} (x \ll i)$ or $(x \ll (m+1)) - (x \ll n)$, whichever needs fewer operations. On x86-64 the compiler also uses `leaq` (Module 3) to compute things like $x + 4x$ in one instruction.

## 6. Dividing by powers of two

Division is even slower (30+ cycles). Division by $2^k$ uses a right shift, but carefully, because C integer division **rounds toward zero**.

**Unsigned:** `x >> k` (logical) equals $\lfloor x / 2^k \rfloor$. Correct.

**Two's complement, nonnegative $x$:** arithmetic shift gives $\lfloor x/2^k \rfloor$, which equals rounding toward zero. Correct.

**Two's complement, negative $x$:** arithmetic shift gives $\lfloor x/2^k \rfloor$, which rounds toward $-\infty$. For $x = -12340$, `x >> 4` gives −772 but $-12340/16 = -771.25$, and C wants −771. Fix with a **bias**: add $2^k - 1$ before shifting:

$$\left\lceil x/2^k \right\rceil = (x + 2^k - 1) \gg k \quad\text{for } x < 0$$

So the compiler emits

```c
int div16(int x) {
    int bias = (x >> 31) & 0xF;   /* 15 if x < 0, else 0 */
    return (x + bias) >> 4;
}
```

```python-run
def c_div(x, d):                # C semantics: truncate toward zero
    q = abs(x) // abs(d)
    return q if (x >= 0) == (d > 0) else -q

for x in (12340, -12340, -1, -16, -17):
    shift = x >> 4                          # Python >> is arithmetic
    biased = (x + (15 if x < 0 else 0)) >> 4
    print(f"x={x:7}: x>>4={shift:6}  biased={biased:6}  C x/16={c_div(x,16):6}")
```

> [!NOTE]
> Division by a power of two *cannot* be generalized to arbitrary constants the way multiplication can. Compilers instead use "magic number" multiplication (multiply by a precomputed reciprocal and take the high half), which is beyond this lesson.

## 7. Final thoughts on integer arithmetic

- Unsigned and two's-complement arithmetic share the same bit-level implementations of add, subtract, multiply (low half) and left shift. They differ in division and right shift, and in how you *interpret* results and detect overflow.
- $w$-bit arithmetic is arithmetic in the ring $\mathbb{Z}/2^w\mathbb{Z}$. Commutativity, associativity and distributivity all hold! That is why compilers can freely reassociate integer expressions. (Floating point, by contrast, is *not* associative.)
- Overflow is silent. Defensive code checks *before* the operation.

> [!INTERVIEW]
> **"How do you detect overflow when adding two ints?"** Answer: overflow iff the operands have the same sign and the sum's sign differs; in C, avoid the UB by checking first: `if (y > 0 && x > INT_MAX - y) overflow; if (y < 0 && x < INT_MIN - y) overflow;`. **"Midpoint of two indices?"** Use `lo + (hi - lo) / 2`, not `(lo + hi) / 2`, which overflows for large indices (the bug famously lived in Java's binary search for years).

## 8. Practice puzzles

Try predicting each, then run the cell.

1. Is `(x < y) == (-x > -y)` always true for `int`? (No: $x = TMin$, $y = 0$ makes `-x` still TMin.)
2. Is `((x + y) << 4) + y - x == 17*y + 15*x`? (Yes: ring identities hold modulo $2^w$.)
3. Is `~x + ~y + 1 == ~(x + y)`? (Yes: $\sim a = -a - 1$.)

```python-run
import random
W = 32
def wrap(v):
    v &= (1 << W) - 1
    return v - (1 << W) if v >> (W - 1) else v
TMIN = -(1 << 31)
def check(f, trials=20000):
    vals = [TMIN, -1, 0, 1, (1 << 31) - 1]
    for _ in range(trials):
        x = random.choice(vals + [random.randint(TMIN, -TMIN - 1)])
        y = random.choice(vals + [random.randint(TMIN, -TMIN - 1)])
        if not f(x, y):
            return f"counterexample x={x}, y={y}"
    return "always true (on samples)"
print("1:", check(lambda x, y: (x < y) == (wrap(-x) > wrap(-y))))
print("2:", check(lambda x, y: wrap(wrap((x + y) << 4) + y - x) == wrap(17*y + 15*x)))
print("3:", check(lambda x, y: wrap(~x + ~y + 1) == wrap(~(x + y))))
```

## Glossary

- **Overflow**: what happens when a result needs more bits than are available and the extra bits are lost.
- **Modular arithmetic**: arithmetic that wraps round at a fixed value, like hours on a clock.
- **Unsigned addition**: addition of non-negative numbers in which a result too large wraps round to a small one.
- **Two's-complement addition**: addition of signed numbers; it can overflow in the positive or the negative direction.
- **Positive / negative overflow**: a sum of two positive numbers appearing negative / a sum of two negative numbers appearing non-negative.
- **Additive inverse**: the value that gives zero when added to a number; the machine's version of negation.
- **Truncation**: keeping only the low bits of a result.
- **Arithmetic right shift**: a shift to the right that copies the sign bit, used to divide signed numbers by powers of two.
- **Bias**: a small amount added before a shift so that division of a negative number rounds toward zero.
- **Undefined behaviour**: a situation for which the C language makes no promise about what the program does.

## Check yourself

```quiz
[
  {"q": "In 4-bit two's complement, what is 5 + 5?", "options": ["10", "-6", "-5", "2"], "answer": 1,
   "explain": "10 exceeds TMax=7; 10 - 16 = -6 (bits 1010)."},
  {"q": "Unsigned s = x + y overflowed if and only if...", "options": ["s > x", "s < x", "s == 0", "x and y have the same sign"], "answer": 1,
   "explain": "On overflow s = x + y - 2^w, which is less than x because y < 2^w."},
  {"q": "Which pair of operand signs can produce two's-complement addition overflow?", "options": ["Opposite signs", "Both positive or both negative", "Only both negative", "Any pair"], "answer": 1,
   "explain": "If signs differ the true sum lies between the operands, so it is representable."},
  {"q": "Why does the check (sum - x == y) fail to detect overflow?", "options": ["Subtraction is undefined", "Two's-complement addition is a group, so (x+y)-x always equals y", "It detects only negative overflow", "It is correct"], "answer": 1,
   "explain": "Modular arithmetic undoes the wraparound, so the equality always holds."},
  {"q": "For int x = -12340, what does C's x / 16 return, and does x >> 4 match?", "options": ["-771; no, x>>4 is -772", "-772; yes", "-771; yes", "-772; no"], "answer": 0,
   "explain": "C rounds toward zero (-771.25 -> -771); the arithmetic shift rounds down to -772, hence the bias of 15."},
  {"q": "How might a compiler compute x * 14 with shifts?", "options": ["(x<<4) - (x<<1)", "(x<<3) + 6", "x<<14", "(x<<4) + (x<<1)"], "answer": 0,
   "explain": "14 = 16 - 2, so x*14 = (x<<4) - (x<<1)."},
  {"q": "What is -TMin in w-bit two's complement?", "options": ["TMax", "TMin", "0", "Undefined in hardware"], "answer": 1,
   "explain": "The true value 2^(w-1) wraps to -2^(w-1) = TMin."},
  {"q": "The low w bits of x*y are the same for unsigned and two's-complement multiplication. True?", "options": ["True", "False"], "answer": 0,
   "explain": "Both are the full product modulo 2^w; only the interpretation of those bits differs."}
]
```

> **Source:** CS:APP 3e, §2.3 (Integer arithmetic: unsigned and two's-complement addition, negation, multiplication, multiplying by constants, dividing by powers of 2).
