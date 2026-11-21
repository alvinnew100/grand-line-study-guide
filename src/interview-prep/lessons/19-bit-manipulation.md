# Bit manipulation: approach and cheat sheet

## Before this lesson

You need ordinary arithmetic and Python integers. Knowing what a hash set is helps for one comparison ([Arrays and strings](#/lesson/interview-prep/arrays-strings-approach)). For slower teaching of the same material see [Bits in Python](#/lesson/neet-greedy-math/bits-python) and [Bit tricks](#/lesson/neet-greedy-math/bit-tricks); for how computers store numbers in depth, see [Bits and bytes](#/lesson/csapp/bits-bytes) in the Computer Systems track.

## In plain words

Inside a computer every number is stored as a row of switches, each either off (0) or on (1). One switch is a **bit**. The number 13 is stored as `1101`: one eight, one four, no two, one one.

**Bit manipulation** means working on those switches directly instead of on the number as a whole. Picture a row of light switches on a wall. You can ask "is the third switch on?", turn the third switch on or off without touching the others, flip every switch at once, or slide the whole pattern one position along. Processors do these things in a single step, which makes them the fastest operations available.

This matters for a job in specific places: packing several yes/no flags into one integer, network and file formats, permissions, graphics, compression, cryptography, embedded devices. It matters for interviews because a small set of bit questions appears regularly, and they are nearly impossible to improvise but easy once you know six operators and four standard recipes.

## Reading binary

In decimal, each position is worth ten times the one to its right: 1, 10, 100. In **binary** each position is worth twice the one to its right: 1, 2, 4, 8, 16. Positions are numbered from the right starting at 0, and bit i is worth 2ⁱ.

| Decimal | Binary | Sum |
|---|---|---|
| 5 | `0101` | 4 + 1 |
| 6 | `0110` | 4 + 2 |
| 13 | `1101` | 8 + 4 + 1 |
| 16 | `10000` | 16 |

In Python, write a binary literal as `0b1101` and print one with `bin(13)` or `format(13, "08b")` (eight digits, padded with zeros). The widget lets you click bits and see the value change.

<div class="widget" data-widget="bits"></div>

## The six operators

| Operator | Name | Rule for each bit position | Example (4 bits) |
|---|---|---|---|
| `a & b` | AND | 1 only if both are 1 | `1100 & 1010 = 1000` |
| `a \| b` | OR | 1 if at least one is 1 | `1100 \| 1010 = 1110` |
| `a ^ b` | XOR (exclusive or) | 1 if the two differ | `1100 ^ 1010 = 0110` |
| `~a` | NOT | flips every bit | `~1100 = 0011` (in 4 bits) |
| `a << k` | left shift | moves bits k places left, filling with 0 | `0011 << 2 = 1100` |
| `a >> k` | right shift | moves bits k places right, dropping the lowest | `1100 >> 2 = 0011` |

Shifting left by k multiplies by 2ᵏ; shifting right by k divides by 2ᵏ and discards the remainder.

```python-run
a, b = 0b1100, 0b1010
def show(label, value):
    print(f"{label:10s} {value & 0b1111:04b}   (decimal {value & 0b1111})")

show("a", a); show("b", b)
show("a & b", a & b)
show("a | b", a | b)
show("a ^ b", a ^ b)
show("~a", ~a)            # masked to 4 bits by show()
show("a << 1", a << 1)    # the top bit falls outside 4 bits
show("a >> 2", a >> 2)
```

`show` prints the lowest four bits of a value using `value & 0b1111`, a mask that keeps four positions and clears the rest, and the format `04b`, which means "binary, four digits, zero-padded". Read each output line against the table above.

### Facts worth memorising

For any bit pattern `x` (with "all 1s" meaning every bit set):

| Expression | Result | Expression | Result |
|---|---|---|---|
| `x ^ 0` | `x` | `x & 0` | `0` |
| `x ^ all 1s` | `~x` | `x & all 1s` | `x` |
| `x ^ x` | `0` | `x & x` | `x` |
| `x \| 0` | `x` | `x \| all 1s` | all 1s |

You do not need to memorise the table as text: check any row by thinking about one bit. The XOR rows are the source of many tricks: XOR-ing a value twice with the same thing cancels out.

## Negative numbers: two's complement

Computers with fixed-width integers (8, 32 or 64 bits) store negative numbers in **two's complement**. In an N-bit number the leftmost bit has a *negative* weight: −2^(N−1). So in 4 bits, `1011` is −8 + 2 + 1 = −5.

Two handy consequences:

- To negate a number, flip all bits and add 1. In 4 bits: 5 is `0101`; flipped is `1010`; plus one is `1011` = −5.
- −1 is all 1s (`1111`), and the most negative value (`1000` = −8) has no positive counterpart.

There are also two kinds of right shift on fixed-width integers. A **logical** right shift fills the vacated top bits with 0. An **arithmetic** right shift fills them with copies of the sign bit, so a negative number stays negative and the result is division by two rounded down. Java has both (`>>>` and `>>`); C leaves the choice for signed values to the compiler, though it is almost always arithmetic.

> [!WARNING]
> Python integers are not fixed-width: they grow as needed, and negative numbers behave as if they had infinitely many leading 1s. So `~5` is `-6`, not a large positive number, and there is no overflow. When a problem says "32-bit", mask your results with `& 0xFFFFFFFF` to imitate fixed width.

## The four standard recipes

A **mask** is a number whose bits are chosen so that combining it with another number affects only the positions you want. `1 << i` is the mask with a single 1 at position i.

| Task | Recipe | Why it works |
|---|---|---|
| **Get** bit i | `(x >> i) & 1`, or test `x & (1 << i) != 0` | AND with a single 1 keeps that bit and clears the rest |
| **Set** bit i (make it 1) | `x \| (1 << i)` | OR with 1 forces a 1; OR with 0 leaves bits alone |
| **Clear** bit i (make it 0) | `x & ~(1 << i)` | The mask has a 0 only at i; AND with 0 forces a 0 |
| **Update** bit i to value v | `(x & ~(1 << i)) \| (v << i)` | Clear the bit, then OR in the new value |

Wider versions clear or write a whole field: a block of `w` ones is `(1 << w) - 1`; shift it into place and use it as the mask.

```python-run
def get_bit(x, i):      return (x >> i) & 1
def set_bit(x, i):      return x | (1 << i)
def clear_bit(x, i):    return x & ~(1 << i)
def update_bit(x, i, v): return (x & ~(1 << i)) | (v << i)

x = 0b10110
print("x              ", format(x, "05b"))
print("bit 2 is       ", get_bit(x, 2), "  bit 3 is", get_bit(x, 3))
print("set bit 0      ", format(set_bit(x, 0), "05b"))
print("clear bit 4    ", format(clear_bit(x, 4), "05b"))
print("update bit 1->0", format(update_bit(x, 1, 0), "05b"))

# permissions packed in one integer
READ, WRITE, EXECUTE = 1 << 0, 1 << 1, 1 << 2
rights = READ | EXECUTE
print("can write?", bool(rights & WRITE), "| after granting:", bool((rights | WRITE) & WRITE))
```

The last three lines show the everyday use: each permission is one bit, a set of permissions is one integer, granting is OR, checking is AND, and revoking would be AND with the inverted mask.

## Tricks that come up again and again

### `x & (x - 1)` removes the lowest 1 bit

Subtracting 1 turns the lowest 1 into 0 and all the 0s below it into 1s; AND-ing with the original wipes all of those out. `101100 & 101011 = 101000`.

- **Count the 1 bits**: repeat until x is 0, counting the repetitions. The loop runs once per 1 bit, not once per position.
- **Power of two test**: a positive x is a power of two exactly when `x & (x - 1) == 0` (it has a single 1 bit).

### `x & -x` isolates the lowest 1 bit

Because −x is "flip and add one", every bit above the lowest 1 is inverted and the lowest 1 itself survives. `101100 & -101100 = 000100`. Used in binary indexed trees and in the "next number with the same number of 1 bits" problem ([Next Number With the Same Weight](#/problem/ctci-next-same-weight)).

### XOR finds differences and cancels pairs

- The number of positions in which a and b differ is the number of 1 bits in `a ^ b` ([Bit Flips Between Two Numbers](#/problem/ctci-bit-flips-between)).
- XOR-ing a list in which every value appears twice except one leaves that one value, because equal values cancel.

### Whole-word masks

Hexadecimal digits correspond to four bits each, which makes patterns easy to write: `0xAAAAAAAA` is `1010…` (the odd positions), `0x55555555` is `0101…` (the even positions). Selecting each group and shifting swaps neighbouring bits in a handful of operations ([Swap Neighbouring Bits](#/problem/ctci-swap-neighbor-bits)).

### An integer as a small set

If items are numbered 0 to 63, a single integer can be a set: bit i is 1 when item i is present. Union is OR, intersection is AND, membership is a get-bit. Compared with a hash set this uses a fraction of the memory and is faster, at the price of a limited range of items.

```python-run
def count_ones(x):
    count = 0
    while x:
        x &= x - 1          # remove the lowest 1 bit
        count += 1
    return count

def is_power_of_two(x):
    return x > 0 and x & (x - 1) == 0

def lone_value(values):
    result = 0
    for v in values:
        result ^= v         # pairs cancel
    return result

print("ones in 0b101101:", count_ones(0b101101))
print("powers of two among 1..20:", [n for n in range(1, 21) if is_power_of_two(n)])
print("value without a partner:", lone_value([7, 3, 9, 3, 7]))
print("bits differing between 29 and 15:", count_ones(29 ^ 15))
```

`count_ones` loops four times for `101101`, which has four 1 bits: once per 1 bit, not once per position. `lone_value` starts from 0 (the value that leaves XOR unchanged) and folds every element in; the pairs 7, 7 and 3, 3 cancel and 9 remains. The last line combines two tricks: XOR to mark the differing positions, then a count of the marks.

## A worked example with full reasoning

*Problem: a 32-bit register must have the bits from position `lo` to position `hi` replaced by a given field, leaving all other bits untouched.* ([Splice Bits](#/problem/ctci-splice-bits).)

**Listen.** Positions are inclusive and counted from 0 at the right. The field fits in `hi − lo + 1` bits.

**Example.** `reg = 11111111`, `field = 010`, `lo = 3`, `hi = 5`. Expected: bits 5, 4, 3 become 0, 1, 0 → `11010111`.

**Brute force.** Loop over the positions and update one bit at a time with the update recipe: correct, up to 32 steps.

**Optimise.** Do all positions at once with one mask. Two steps: make a hole, then fill it.

1. Mask of the hole: a block of `width = hi − lo + 1` ones, shifted left by `lo`. For the example: `111 << 3 = 00111000`.
2. Clear: `reg & ~mask` = `11111111 & 11000111 = 11000111`.
3. Fill: `field << lo` = `010 << 3 = 00010000`; OR it in → `11010111`.

**Implement.**

```python
def splice(reg, field, lo, hi):
    width = hi - lo + 1
    mask = ((1 << width) - 1) << lo
    return (reg & ~mask & 0xFFFFFFFF) | (field << lo)
```

The extra `& 0xFFFFFFFF` keeps the result within 32 bits in Python, where `~mask` is a negative number with endless leading 1s.

**Test.** A one-bit field (`lo == hi`); the whole word (`lo = 0`, `hi = 31`); a field of zeros into a register of ones (checks clearing); a field of ones into zeros (checks filling); a field touching bit 31.

**Complexity.** O(1) time and space.

**What usually goes wrong.** Skipping the clearing step (OR alone cannot turn a 1 into a 0), and an off-by-one in the width.

## Cheat sheet

| Goal | Expression |
|---|---|
| Mask with bit i set | `1 << i` |
| Mask with the low w bits set | `(1 << w) - 1` |
| Get bit i | `(x >> i) & 1` |
| Set bit i | `x \| (1 << i)` |
| Clear bit i | `x & ~(1 << i)` |
| Toggle bit i | `x ^ (1 << i)` |
| Clear bits i and above | `x & ((1 << i) - 1)` |
| Clear bits 0 through i | `x & ~((1 << (i + 1)) - 1)` |
| Remove lowest 1 bit | `x & (x - 1)` |
| Isolate lowest 1 bit | `x & -x` |
| Is x a power of two? | `x > 0 and x & (x - 1) == 0` |
| Positions where a and b differ | `a ^ b` |
| Multiply / divide by 2ᵏ | `x << k` / `x >> k` |
| Is x odd? | `x & 1` |
| Imitate 32-bit unsigned in Python | `x & 0xFFFFFFFF` |

All of these are O(1). Counting 1 bits with `x & (x - 1)` is O(number of 1 bits).

## Problems in this module and what each trains

| Problem | Skill |
|---|---|
| [Splice Bits](#/problem/ctci-splice-bits) | Field masks: clear, then OR |
| [Bit Flips Between Two Numbers](#/problem/ctci-bit-flips-between) | XOR plus counting 1 bits |
| [Swap Neighbouring Bits](#/problem/ctci-swap-neighbor-bits) | Whole-word masks in hexadecimal |
| [Longest Run After One Flip](#/problem/ctci-longest-ones-one-flip) | Scanning bits with a small amount of state |
| [Next Number With the Same Weight](#/problem/ctci-next-same-weight) | Reasoning about carries and trailing blocks |
| [Binary Fraction Printer](#/problem/ctci-binary-fraction) | Binary place value after the point |

## Pitfalls

- **Operator precedence.** In Python and C, `==` binds tighter than `&`, so `x & 1 == 0` means `x & (1 == 0)`. Use parentheses: `(x & 1) == 0`.
- **Forgetting Python's unlimited integers** when a problem assumes 32 bits: mask after `~` and after left shifts.
- **Confusing bit positions with values.** Bit 3 has value 8.
- **Off-by-one in field widths and shift amounts.**
- **Shifting negative numbers** without knowing whether the shift is arithmetic or logical in the language at hand.
- **Using OR to write a field without clearing it first.**
- **Counting from the wrong end.** Position 0 is the rightmost (least significant) bit.

> [!INTERVIEW]
> Work bit problems on paper with a small width, four or eight bits, and write the patterns in aligned columns. Interviewers follow the columns easily, and most bit bugs are visible as soon as the masks are written out.

> [!TIP]
> When a solution loops over all 32 positions, ask whether a whole-word operation exists. Conversely, when you cannot find the clever expression, the 32-step loop is a perfectly acceptable first answer: it is O(1) for a fixed word size.

## Summary

- Numbers are rows of bits; bit i is worth 2ⁱ, counted from 0 at the right.
- Six operators: AND, OR, XOR, NOT, left shift, right shift. A mask selects the positions an operation affects.
- Negative fixed-width numbers use two's complement; right shifts are arithmetic or logical; Python integers are unbounded, so mask to imitate a fixed width.
- Four recipes cover most needs: get, set, clear and update a bit, and their multi-bit field versions.
- Reusable tricks: `x & (x - 1)`, `x & -x`, XOR for differences and cancellation, hexadecimal masks, an integer as a set.
- Write examples in aligned binary columns and watch operator precedence.

## Glossary

- **Bit**: a binary digit, 0 or 1.
- **Binary**: the base-two number system.
- **Least / most significant bit**: the rightmost bit (worth 1) / the leftmost bit.
- **Mask**: a bit pattern used with AND, OR or XOR to select, set, clear or flip chosen positions.
- **AND, OR, XOR, NOT**: the bitwise logical operators.
- **Shift**: moving all bits left or right by a number of positions.
- **Two's complement**: the standard representation of signed integers, in which the top bit has negative weight.
- **Arithmetic / logical right shift**: a right shift that copies the sign bit into vacated positions / fills them with zeros.
- **Hexadecimal**: base sixteen; each digit represents four bits.
- **Bit set (bitmask set)**: an integer whose bits record which items of a small numbered range are present.
- **Population count**: the number of 1 bits in a number, also called its weight.

```quiz
[
  {"q": "What is 0b1100 & 0b1010?",
   "options": ["0b1110", "0b1000", "0b0110", "0b0000"],
   "answer": 1,
   "explain": "AND keeps a 1 only where both numbers have a 1: only the leftmost position."},
  {"q": "Which expression sets bit i of x to 1 and leaves the other bits unchanged?",
   "options": ["x & (1 << i)", "x | (1 << i)", "x ^ x", "x >> i"],
   "answer": 1,
   "explain": "OR with a single-1 mask forces that bit on; OR with 0 changes nothing elsewhere."},
  {"q": "What does x & (x - 1) do?",
   "options": ["Doubles x", "Removes the lowest 1 bit of x", "Isolates the lowest 1 bit", "Negates x"],
   "answer": 1,
   "explain": "Subtracting 1 flips the lowest 1 and the zeros below it; AND-ing clears them."},
  {"q": "How many bit positions differ between a and b?",
   "options": ["The number of 1 bits in a & b", "The number of 1 bits in a | b", "The number of 1 bits in a ^ b", "a - b"],
   "answer": 2,
   "explain": "XOR gives 1 exactly where the two numbers disagree."},
  {"q": "In 4-bit two's complement, what value does 1011 represent?",
   "options": ["11", "-5", "-3", "5"],
   "answer": 1,
   "explain": "−8 + 2 + 1 = −5: the top bit has weight −8."},
  {"q": "Why must a field be cleared before OR-ing in its new value?",
   "options": ["OR is slow", "OR can turn 0 into 1 but can never turn 1 into 0, so old 1s would remain", "Clearing changes the other bits", "It is not necessary"],
   "answer": 1,
   "explain": "AND with the inverted mask makes the hole; OR then writes exactly the new bits."},
  {"q": "In Python, what is the value of ~5, and why?",
   "options": ["10, because bits are reversed", "-6, because integers are unbounded and NOT acts like −x − 1", "4294967290 always", "0"],
   "answer": 1,
   "explain": "Python integers behave as if they had infinitely many sign bits; mask with 0xFFFFFFFF to imitate 32-bit behaviour."},
  {"q": "What is wrong with the test `x & 1 == 0` in Python?",
   "options": ["Nothing", "== binds tighter than &, so it computes x & (1 == 0)", "& cannot be used on integers", "It always raises an error"],
   "answer": 1,
   "explain": "Write (x & 1) == 0. The unparenthesised form evaluates x & False, which is 0."}
]
```

> **Source:** McDowell, Cracking the Coding Interview 6e, ch. 5 (Bit Manipulation). Explanations, code and examples are original.
