PROBLEMS = [
dict(
    id="csapp-show-bytes",
    title="Show Bytes (Endianness)",
    difficulty="Easy",
    pattern="Bits & Bytes",
    entry="show_bytes",
    description=r"""
CS:APP's `show_bytes` prints the bytes of an object **in address order**. Simulate it.

Given an integer `x`, a size `nbytes` (1, 2, 4 or 8) and a flag `little`, return the list of the
object's bytes as two-digit lowercase hex strings, in the order they would appear in memory from the
lowest address upward. `x` may be negative: store its `nbytes`-byte two's-complement pattern
(i.e. truncate `x` modulo $2^{8 \cdot nbytes}$).

- `little = True`: least significant byte first.
- `little = False`: most significant byte first (big endian).

**Example:** `x = 0x01234567, nbytes = 4, little = True` → `["67","45","23","01"]`

**Example:** `x = -1, nbytes = 2, little = False` → `["ff","ff"]`
""",
    starter='''def show_bytes(x: int, nbytes: int, little: bool) -> List[str]:
    pass
''',
    solution='''def show_bytes(x, nbytes, little):
    u = x & ((1 << (8 * nbytes)) - 1)
    out = [f"{(u >> (8 * i)) & 0xFF:02x}" for i in range(nbytes)]
    return out if little else out[::-1]
''',
    tests=[
        [0x01234567, 4, True],
        [0x01234567, 4, False],
        [-1, 2, False],
        [12345, 4, True],
        [12345, 8, False],
        [-12345, 2, True],
        [0, 1, True],
        [255, 1, False],
        [-2**63, 8, True],
        [2**64 - 2, 8, False],
        [0x1122334455667788, 8, True],
        [300, 1, True],
    ],
    wrong_solutions=['''def show_bytes(x, nbytes, little):
    u = x & ((1 << (8 * nbytes)) - 1)
    out = [f"{(u >> (8 * i)) & 0xFF:02x}" for i in range(nbytes)]
    return out[::-1] if little else out
''', '''def show_bytes(x, nbytes, little):
    out = [f"{(abs(x) >> (8 * i)) & 0xFF:02x}" for i in range(nbytes)]
    return out if little else out[::-1]
'''],
    guide=dict(
        prereqs="Lesson *Bits, bytes, words and bit-level operations* (byte ordering).",
        intuition="A multi-byte value is just a number; *endianness* only decides which byte goes at the lowest address. Extract bytes by shifting and masking, from least significant to most, then reverse for big endian.",
        hints=["Byte i (from the least significant end) is `(u >> (8*i)) & 0xFF`.",
               "Handle negatives by first masking: `u = x & ((1 << 8*nbytes) - 1)` gives the two's-complement pattern.",
               "Little endian lists byte 0 first; big endian is the reverse."],
        brute_force="Format the masked value as a zero-padded hex string of length `2*nbytes` and slice it into pairs (that is big endian), reversing for little endian. Same complexity.",
        approach="1. Mask `x` to `8*nbytes` bits so negatives become their two's-complement pattern.\n2. For `i` in `0..nbytes-1`, extract byte `i` with a shift and mask; format with `:02x`.\n3. That list is little-endian order; reverse it for big endian.\n\nDry run `0x01234567`, 4 bytes: bytes from LSB are 67, 45, 23, 01, so little endian gives `[67,45,23,01]`.",
        complexity="O(nbytes) time and space.",
        pitfalls="- Forgetting to mask negatives (Python ints are unbounded, `-1 >> 8` is still -1, so bytes come out right by luck, but `abs` is wrong).\n- Values larger than the width must be **truncated**, e.g. 300 in 1 byte is `2c`.\n- Reversing the wrong case.",
        follow_up="Write `is_little_endian()` in C by storing `int x = 1` and reading `*(char *)&x`.",
    ),
),
dict(
    id="csapp-bit-and",
    title="bitAnd with only ~ and |",
    difficulty="Easy",
    pattern="Bit Manipulation",
    entry="bit_and",
    description=r"""
A classic CS:APP *data lab* puzzle: compute `x & y` using **only** the operators `~` and `|`.

Inputs are 32-bit patterns given as Python ints in `[0, 2^32)`. Return the 32-bit result as an int in
`[0, 2^32)`. (Python's `~` produces negative numbers, so mask your final answer with `0xFFFFFFFF`.
Using `&` only for that final mask is allowed; the grader cannot check operators, so hold yourself
to the rules!)

**Example:** `x = 6 (0b0110), y = 12 (0b1100)` → `4 (0b0100)`
""",
    starter='''def bit_and(x: int, y: int) -> int:
    pass
''',
    solution='''def bit_and(x, y):
    return (~(~x | ~y)) & 0xFFFFFFFF
''',
    tests=[[6, 12], [0, 0], [0xFFFFFFFF, 0xFFFFFFFF], [0xFFFFFFFF, 0], [0x12345678, 0xF0F0F0F0],
           [0x80000000, 0x80000001], [1, 3], [0xAAAAAAAA, 0x55555555], [0xDEADBEEF, 0xFFFF0000], [7, 7]],
    wrong_solutions=['''def bit_and(x, y):
    return (~x | ~y) & 0xFFFFFFFF
''', '''def bit_and(x, y):
    return (x | y) & 0xFFFFFFFF
'''],
    guide=dict(
        prereqs="Boolean algebra and De Morgan's laws (lesson *Bits, bytes...*).",
        intuition="De Morgan: `~(a & b) == ~a | ~b`. Complement both sides: `a & b == ~(~a | ~b)`.",
        hints=["What is the complement of `x & y`?", "De Morgan turns NOT-of-AND into OR-of-NOTs.", "`x & y = ~(~x | ~y)`; then mask to 32 bits."],
        brute_force="Loop over 32 bit positions and set bit i when both inputs have it: O(32), but it violates the operator rules.",
        approach="Apply De Morgan's law once: `~(~x | ~y)`. In Python, `~` of a nonnegative int is negative, so finish with `& 0xFFFFFFFF` to get the 32-bit pattern.",
        complexity="O(1): three bitwise operations.",
        pitfalls="Forgetting the final mask (results come out negative in Python); forgetting the outer `~`.",
        follow_up="Also from the data lab: `bitXor` using only `~` and `&`: `~(~(x & ~y) & ~(~x & y))`.",
    ),
),
dict(
    id="csapp-is-power-of-two",
    title="Is Power of Two (bit trick)",
    difficulty="Easy",
    pattern="Bit Manipulation",
    entry="is_power_of_two",
    description=r"""
Given a **32-bit two's-complement** integer `x` (a Python int in `[-2^31, 2^31)`), return `True`
iff `x` is a positive power of two (1, 2, 4, ..., 2^30). Use the identity that `x & (x - 1)` clears the
lowest set bit. Zero, negative numbers (including `TMin = -2^31`, whose bit pattern has a single 1)
are **not** powers of two.

**Example:** `64` → `True`; `96` → `False`; `-2147483648` → `False`
""",
    starter='''def is_power_of_two(x: int) -> bool:
    pass
''',
    solution='''def is_power_of_two(x):
    return x > 0 and (x & (x - 1)) == 0
''',
    tests=[[64], [96], [-2147483648], [0], [1], [2], [3], [-1], [2**30], [2**30 + 1], [2147483647], [-64]],
    wrong_solutions=['''def is_power_of_two(x):
    return (x & (x - 1)) == 0
''', '''def is_power_of_two(x):
    m = x & 0xFFFFFFFF
    return m != 0 and (m & (m - 1)) == 0
'''],
    guide=dict(
        prereqs="Masks and two's complement (Module 2).",
        intuition="A power of two has exactly one 1 bit. Subtracting 1 turns that bit off and turns on all bits below it, so `x & (x-1)` becomes 0. Any number with two or more 1s keeps its higher 1s.",
        hints=["How many 1 bits does a power of two have?", "What does `x - 1` look like in binary when x = 0b1000?", "Handle 0 and negatives separately: as a bit pattern, TMin has one 1 bit but is negative."],
        brute_force="Repeatedly divide by 2 while even; O(log x).",
        approach="Return `x > 0 and (x & (x-1)) == 0`. Dry run x=96 (0b1100000): x-1 = 0b1011111, AND = 0b1000000 != 0, so False.",
        complexity="O(1).",
        pitfalls="- `0 & -1 == 0` would claim 0 is a power of two: test `x > 0`.\n- Viewing TMin as an unsigned pattern `0x80000000` would say yes; as a signed value it is negative.",
        follow_up="Round up to the next power of two by smearing bits: `x-=1; x|=x>>1; x|=x>>2; ...; x+1`.",
    ),
),
dict(
    id="csapp-popcount",
    title="Population Count (32-bit)",
    difficulty="Easy",
    pattern="Bit Manipulation",
    entry="popcount",
    description=r"""
Return the number of 1 bits in the **32-bit two's-complement pattern** of `x`, where `x` is a Python
int in `[-2^31, 2^31)`. For example `-1` has all 32 bits set.

**Example:** `11 (0b1011)` → `3`; `-1` → `32`; `-2147483648` → `1`
""",
    starter='''def popcount(x: int) -> int:
    pass
''',
    solution='''def popcount(x):
    x &= 0xFFFFFFFF
    n = 0
    while x:
        x &= x - 1
        n += 1
    return n
''',
    tests=[[11], [-1], [-2147483648], [0], [1], [2147483647], [0x55555555], [-2], [256], [-256], [0x0F0F0F0F], [123456789]],
    wrong_solutions=['''def popcount(x):
    return bin(x).count("1")
'''],
    guide=dict(
        prereqs="Two's-complement patterns and `x & (x-1)`.",
        intuition="Convert to the 32-bit pattern first, then count. Kernighan's trick clears one set bit per iteration, so the loop runs once per 1 bit.",
        hints=["Python ints are unbounded: `bin(-1)` is `-0b1`. Mask with `0xFFFFFFFF` first.", "`x &= x - 1` removes the lowest 1.", "Count iterations until x is 0."],
        brute_force="Test each of the 32 bits with `(x >> i) & 1`: O(32).",
        approach="Mask, then loop `while x: x &= x-1; n += 1`. The data-lab version uses a divide-and-conquer sum: add adjacent bits in pairs (mask 0x55555555), then nibbles (0x33333333), bytes (0x0F0F0F0F), and so on, in O(log w) operations with no loop.",
        complexity="O(number of set bits) <= 32.",
        pitfalls="Not masking negatives (`bin(-1).count('1')` is 1, not 32).",
        follow_up="Hardware has a single instruction (`popcnt`). Try the branch-free SWAR version.",
    ),
),
dict(
    id="csapp-twos-decode",
    title="Two's-Complement Decode (B2T)",
    difficulty="Easy",
    pattern="Integer Representation",
    entry="b2t",
    description=r"""
Implement $B2T_w$: given a bit string `bits` of length $w \ge 1$ (most significant bit first),
return the integer it encodes in **two's complement**:

$$B2T_w(\vec{x}) = -x_{w-1}2^{w-1} + \sum_{i=0}^{w-2} x_i 2^i$$

**Example:** `"1011"` → `-5`; `"0111"` → `7`; `"1"` → `-1`
""",
    starter='''def b2t(bits: str) -> int:
    pass
''',
    solution='''def b2t(bits):
    w = len(bits)
    v = int(bits, 2)
    return v - (1 << w) if bits[0] == "1" else v
''',
    tests=[["1011"], ["0111"], ["1"], ["0"], ["1000"], ["1111"], ["0000"], ["10000000"], ["01111111"],
           ["11111111111111111111111111111111"], ["10000000000000000000000000000000"], ["1100111111000111"]],
    wrong_solutions=['''def b2t(bits):
    return int(bits, 2)
''', '''def b2t(bits):
    v = int(bits[1:] or "0", 2)
    return -v if bits[0] == "1" else v
'''],
    guide=dict(
        prereqs="Lesson *Unsigned and two's-complement integers*.",
        intuition="Read the bits as unsigned, then correct for the sign bit: it was counted as $+2^{w-1}$ but should weigh $-2^{w-1}$, a difference of $2^w$.",
        hints=["Compute the unsigned value first.", "If the top bit is 1, subtract 2^w.", "Note \"1\" alone is -1 in 1-bit two's complement."],
        brute_force="Sum weights bit by bit, giving the top bit a negative weight. O(w).",
        approach="`v = int(bits, 2)`; if `bits[0] == '1'`, return `v - 2**w`. Dry run `1011`: v = 11, w = 4, 11 - 16 = -5.",
        complexity="O(w).",
        pitfalls="Treating the sign bit as sign-magnitude (`1011` → -3) is wrong; that is a different encoding.",
        follow_up="Implement $B2U$, $T2U$ and $U2T$ as well.",
    ),
),
dict(
    id="csapp-twos-encode",
    title="Two's-Complement Encode (T2B)",
    difficulty="Easy",
    pattern="Integer Representation",
    entry="t2b",
    description=r"""
Implement $T2B_w$: given an integer `x` and a width `w`, return the `w`-character bit string
(MSB first) of `x` in two's complement. If `x` is outside $[-2^{w-1}, 2^{w-1}-1]$, return
the string `"overflow"`.

**Example:** `x = -5, w = 4` → `"1011"`; `x = 8, w = 4` → `"overflow"`
""",
    starter='''def t2b(x: int, w: int) -> str:
    pass
''',
    solution='''def t2b(x, w):
    if not (-(1 << (w - 1)) <= x <= (1 << (w - 1)) - 1):
        return "overflow"
    return format(x & ((1 << w) - 1), "0%db" % w)
''',
    tests=[[-5, 4], [8, 4], [7, 4], [-8, 4], [-9, 4], [0, 1], [-1, 1], [1, 1], [-12345, 16],
           [2147483647, 32], [-2147483648, 32], [2147483648, 32], [100, 8]],
    wrong_solutions=['''def t2b(x, w):
    return format(x & ((1 << w) - 1), "0%db" % w)
''', '''def t2b(x, w):
    if not (-(1 << (w - 1)) < x < (1 << (w - 1))):
        return "overflow"
    return format(x & ((1 << w) - 1), "0%db" % w)
'''],
    guide=dict(
        prereqs="Two's-complement ranges and $T2U_w(x) = x + 2^w$ for negative x.",
        intuition="The two's-complement pattern of x equals the unsigned pattern of $x \\bmod 2^w$. Masking with $2^w - 1$ does exactly that in Python.",
        hints=["Check the range $[TMin_w, TMax_w]$ first: note it is asymmetric.", "`x & ((1<<w)-1)` gives $T2U_w(x)$.", "Format with zero padding to width w."],
        brute_force="For negative x compute `x + 2**w`, then repeatedly take bits with `% 2`.",
        approach="Range check, then `format(x & mask, '0{w}b')`. Dry run x=-5, w=4: -5 & 15 = 11 = `1011`.",
        complexity="O(w).",
        pitfalls="- Off-by-one on the range: TMin is valid, TMax+1 is not.\n- `bin()` of a negative number gives `-0b101`, not the pattern.",
        follow_up="Use it together with `b2t` to verify a round trip for all 8-bit values.",
    ),
),
dict(
    id="csapp-sign-extend",
    title="Sign Extension",
    difficulty="Easy",
    pattern="Integer Representation",
    entry="sign_extend",
    description=r"""
Given an unsigned **bit pattern** `p` (an int in $[0, 2^{from\_w})$) that holds a `from_w`-bit
two's-complement number, return the `to_w`-bit pattern (an int in $[0, 2^{to\_w})$) obtained by
**sign extension** ($to\_w \ge from\_w$). The represented value must be unchanged.

**Example:** `p = 0xCFC7, from_w = 16, to_w = 32` → `0xFFFFCFC7` (= 4294954951)

**Example:** `p = 0x7F, from_w = 8, to_w = 16` → `0x007F` (= 127)
""",
    starter='''def sign_extend(p: int, from_w: int, to_w: int) -> int:
    pass
''',
    solution='''def sign_extend(p, from_w, to_w):
    if (p >> (from_w - 1)) & 1:
        p |= ((1 << to_w) - 1) ^ ((1 << from_w) - 1)
    return p
''',
    tests=[[0xCFC7, 16, 32], [0x7F, 8, 16], [0x80, 8, 16], [0xFF, 8, 64], [0, 8, 32], [1, 1, 8], [0, 1, 8],
           [0x9C, 8, 8], [0x8000, 16, 64], [0x7FFF, 16, 64], [0b101, 3, 5], [0xABCDEF, 24, 32]],
    wrong_solutions=['''def sign_extend(p, from_w, to_w):
    return p
''', '''def sign_extend(p, from_w, to_w):
    if p >> (from_w - 1):
        return p | (((1 << to_w) - 1) << from_w)
    return p
'''],
    guide=dict(
        prereqs="Lesson *Unsigned and two's-complement integers*, section on expansion.",
        intuition="Copy the sign bit into every new high position. If the sign is 0 nothing changes (zero extension); if 1, set bits `from_w .. to_w-1`.",
        hints=["Read the sign bit with `(p >> (from_w-1)) & 1`.", "The mask of the new bits is `(2^to_w - 1) XOR (2^from_w - 1)`.", "Make sure the result never exceeds to_w bits."],
        brute_force="Convert to the signed value with B2T, then re-encode with `& (2^to_w - 1)`. Equally valid.",
        approach="If the sign bit is set, OR in the mask of high bits. Dry run 0x80 (8→16): sign 1, mask = 0xFFFF ^ 0xFF = 0xFF00, result 0xFF80 = -128 in 16 bits.",
        complexity="O(1) big-int operations.",
        pitfalls="Shifting an all-ones mask left by from_w without bounding it to to_w bits produces too many bits; `from_w == to_w` must return p unchanged.",
        follow_up="Why does sign extension preserve the value? The new top bit weighs $-2^{w}$ and the old one flips from $-2^{w-1}$ to $+2^{w-1}$: net zero.",
    ),
),
dict(
    id="csapp-tadd-overflow",
    title="Two's-Complement Add with Overflow Detection",
    difficulty="Medium",
    pattern="Integer Arithmetic",
    entry="tadd",
    description=r"""
Simulate $w$-bit two's-complement addition. Given `x`, `y` (both in $[-2^{w-1}, 2^{w-1})$) and `w`,
return `[s, kind]` where `s` is the $w$-bit two's-complement sum (what the hardware produces) and
`kind` is `"positive"` (positive overflow), `"negative"` (negative overflow) or `"none"`.

**Example:** `x = 5, y = 5, w = 4` → `[-6, "positive"]`

**Example:** `x = -8, y = -5, w = 4` → `[3, "negative"]`
""",
    starter='''def tadd(x: int, y: int, w: int) -> list:
    pass
''',
    solution='''def tadd(x, y, w):
    true = x + y
    s = true & ((1 << w) - 1)
    if s >> (w - 1):
        s -= 1 << w
    if true > (1 << (w - 1)) - 1:
        kind = "positive"
    elif true < -(1 << (w - 1)):
        kind = "negative"
    else:
        kind = "none"
    return [s, kind]
''',
    tests=[[5, 5, 4], [-8, -5, 4], [-8, 5, 4], [2, 5, 4], [-8, -8, 4], [7, -8, 4], [0, 0, 1], [-1, -1, 1],
           [2147483647, 1, 32], [-2147483648, -1, 32], [-2147483648, 2147483647, 32], [100, 27, 8], [100, 28, 8],
           [-100, -29, 8]],
    wrong_solutions=['''def tadd(x, y, w):
    s = (x + y) & ((1 << w) - 1)
    if s >> (w - 1):
        s -= 1 << w
    return [s, "none" if s == x + y else "positive"]
''', '''def tadd(x, y, w):
    s = (x + y) & ((1 << w) - 1)
    return [s, "none"]
'''],
    guide=dict(
        prereqs="Lesson *Integer arithmetic and overflow*.",
        intuition="Compute the true sum, then wrap it into $[-2^{w-1}, 2^{w-1})$ by keeping the low w bits and reinterpreting. Overflow kind depends on whether the true sum was above TMax or below TMin. Equivalent hardware rule: same-sign operands, different-sign result.",
        hints=["Python has big ints, so the true sum is free.", "Wrap: `s = (x+y) & mask`, then subtract 2^w if the top bit is set.", "Positive overflow iff true sum > TMax; negative iff < TMin."],
        brute_force="The same: there is nothing to brute force here, but you could also simulate a ripple-carry adder bit by bit.",
        approach="1. `true = x + y`. 2. `s = U2T(true mod 2^w)`. 3. Classify. Dry run 5+5 in 4 bits: true 10 > 7, s = 10 - 16 = -6, positive.",
        complexity="O(1).",
        pitfalls="- w = 1: the range is [-1, 0], so -1 + -1 = -2 overflows to 0.\n- Opposite-sign operands never overflow.\n- The C check `sum - x == y` is useless (always true).",
        follow_up="Write `tsub_ok(x, y)`: careful, `y = TMin` makes `-y` overflow.",
    ),
),
dict(
    id="csapp-float-decode",
    title="Decode an IEEE-754 Single",
    difficulty="Medium",
    pattern="Floating Point",
    entry="decode_float",
    description=r"""
Given a 32-bit pattern `u` (int in $[0, 2^{32})$), return the value it encodes as an IEEE-754
single-precision float (sign 1 bit, exponent 8 bits with bias 127, fraction 23 bits).

- Normalized: $(-1)^s \times (1 + f/2^{23}) \times 2^{e-127}$
- Denormalized (`e == 0`): $(-1)^s \times (f/2^{23}) \times 2^{-126}$
- `e == 255`: return the **string** `"inf"`, `"-inf"` or `"nan"`.

Return a Python float otherwise (every single-precision value is exactly representable as a double,
so results are exact). Zero with the sign bit set returns `-0.0` (compares equal to 0.0).

**Example:** `0x3F800000` → `1.0`; `0x4640E400` → `12345.0`; `0x7F800000` → `"inf"`
""",
    starter='''def decode_float(u: int):
    pass
''',
    solution='''def decode_float(u):
    s = u >> 31
    e = (u >> 23) & 0xFF
    f = u & 0x7FFFFF
    if e == 0xFF:
        if f:
            return "nan"
        return "-inf" if s else "inf"
    if e == 0:
        v = f * 2.0 ** (-149)
    else:
        v = (f + (1 << 23)) * 2.0 ** (e - 150)
    return -v if s else v
''',
    tests=[[0x3F800000], [0x4640E400], [0x7F800000], [0xFF800000], [0x7FC00000], [0x00000000], [0x80000000],
           [0x00000001], [0x007FFFFF], [0x00800000], [0x7F7FFFFF], [0xBF400000], [0x40490FDB], [0xC2F6E979]],
    wrong_solutions=['''def decode_float(u):
    s = u >> 31
    e = (u >> 23) & 0xFF
    f = u & 0x7FFFFF
    if e == 0xFF:
        return "nan" if f else ("-inf" if s else "inf")
    v = (1 + f / 2**23) * 2.0 ** (e - 127)
    return -v if s else v
''', '''def decode_float(u):
    s = u >> 31
    e = (u >> 23) & 0xFF
    f = u & 0x7FFFFF
    if e == 0xFF:
        return "nan" if f else ("-inf" if s else "inf")
    if e == 0:
        v = f / 2**23 * 2.0 ** (-127)
    else:
        v = (1 + f / 2**23) * 2.0 ** (e - 127)
    return -v if s else v
'''],
    guide=dict(
        prereqs="Lesson *IEEE-754 floating point*.",
        intuition="Split the word into s, exp and frac with shifts and masks, then apply one of the three cases. Denormals have no implied 1 and use E = 1 - 127 = -126, not -127.",
        hints=["`s = u >> 31`, `e = (u >> 23) & 0xFF`, `f = u & 0x7FFFFF`.", "Check e == 255 first (special), then e == 0 (denormal).", "Using integer significands avoids rounding: normal value = (2^23 + f) * 2^(e - 150)."],
        brute_force="`struct.unpack('>f', u.to_bytes(4, 'big'))` does it in one line, but the point is to implement the cases yourself.",
        approach="Extract fields; special case; denormal $f\\cdot 2^{-149}$; normal $(2^{23}+f)\\cdot 2^{e-150}$; apply sign. Dry run 0x3F800000: s=0, e=127, f=0, value $2^{23}\\cdot 2^{-23} = 1$.",
        complexity="O(1).",
        pitfalls="- Using E = -127 for denormals (off by a factor of 2).\n- Adding the implied 1 to denormals.\n- Forgetting negative zero and negative infinity.",
        follow_up="Write the reverse: encode a Python float into the nearest single with round-to-even.",
    ),
),
dict(
    id="csapp-float-round-even",
    title="Round Binary Fraction to Even",
    difficulty="Medium",
    pattern="Floating Point",
    entry="round_even",
    description=r"""
Given a nonnegative binary number as a string with a binary point (e.g. `"10.00110"`) and an integer
`k >= 0`, round it to `k` bits after the binary point using IEEE **round-to-even**:

- below halfway: round down; above halfway: round up;
- exactly halfway (the dropped bits are `1` followed only by `0`s): choose the result whose last
  kept bit is `0`.

Return the result as a string with exactly `k` bits after the point (no point at all when `k == 0`),
with the integer part written without leading zeros (but at least `"0"`). The input always contains
a `"."` and at least one digit on each side; it may have fewer than `k` fraction bits (pad with zeros).

**Examples** (rounding to quarters, `k = 2`): `"10.00011"` → `"10.00"`, `"10.00110"` → `"10.01"`,
`"10.11100"` → `"11.00"`, `"10.10100"` → `"10.10"`
""",
    starter='''def round_even(num: str, k: int) -> str:
    pass
''',
    solution='''def round_even(num, k):
    ip, fp = num.split(".")
    fp = fp + "0" * max(0, k - len(fp))
    kept = int(ip + fp[:k], 2)
    rest = fp[k:]
    if rest and rest[0] == "1":
        if "1" in rest[1:] or (kept & 1):
            kept += 1
    s = bin(kept)[2:]
    if k == 0:
        return s
    s = s.rjust(k + 1, "0")
    return s[:-k] + "." + s[-k:]
''',
    tests=[["10.00011", 2], ["10.00110", 2], ["10.11100", 2], ["10.10100", 2], ["0.1", 0], ["1.1", 0],
           ["10.1", 0], ["11.1", 0], ["0.0101", 3], ["1.111", 2], ["0.01", 4], ["111.1111", 3],
           ["0.011", 2], ["0.0011", 2], ["1001.1000", 0]],
    wrong_solutions=['''def round_even(num, k):
    ip, fp = num.split(".")
    fp = fp + "0" * max(0, k - len(fp))
    kept = int(ip + fp[:k], 2)
    rest = fp[k:]
    if rest and rest[0] == "1":
        kept += 1
    s = bin(kept)[2:]
    if k == 0:
        return s
    s = s.rjust(k + 1, "0")
    return s[:-k] + "." + s[-k:]
''', '''def round_even(num, k):
    ip, fp = num.split(".")
    fp = fp + "0" * max(0, k - len(fp))
    kept = int(ip + fp[:k], 2)
    s = bin(kept)[2:]
    if k == 0:
        return s
    s = s.rjust(k + 1, "0")
    return s[:-k] + "." + s[-k:]
'''],
    guide=dict(
        prereqs="Lesson *IEEE-754 floating point*, section on rounding.",
        intuition="Treat the kept bits as an integer. Look at the dropped bits: first dropped bit 0 means below half; first bit 1 with any later 1 means above half; exactly `100...0` is a tie, broken toward an even kept integer.",
        hints=["Concatenate integer and kept fraction bits into one integer `kept`.", "Classify the dropped tail: `rest[0]` and whether any 1 follows.", "On a tie, add 1 only if `kept` is odd. Re-insert the point k places from the right."],
        brute_force="Use `fractions.Fraction` to compute the exact value, multiply by 2^k, and apply round-half-even with Python's `round` (which uses banker's rounding on Fractions). Also O(n).",
        approach="1. Split at the point, pad the fraction to k bits.\n2. `kept = int(ip + fp[:k], 2)`, `rest = fp[k:]`.\n3. If `rest` starts with 1 and (has another 1 or kept is odd): kept += 1.\n4. Format back, padding so there are at least k+1 digits.\n\nDry run `10.11100`, k=2: kept = `1011` = 11, rest = `100` is a tie, 11 is odd, so 12 = `1100` → `11.00`.",
        complexity="O(n) in the length of the string.",
        pitfalls="- Rounding up carries into the integer part (`1.111` → `10.00`).\n- Ties when the kept value is already even must round *down*.\n- Formatting when the result is smaller than 2^k (`0.01` style): pad with leading zeros.",
        follow_up="Implement round-toward-zero, round-up and round-down too, and compare on negative inputs.",
    ),
),
]
