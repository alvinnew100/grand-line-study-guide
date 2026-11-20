# Bits, bytes, words and bit-level operations

Modern computers store and process information as two-valued signals: **bits**. Two-valued signals are easy to store and transmit reliably (high vs. low voltage, a magnetized domain pointing one way or the other), and when we group bits together and apply an *interpretation*, we can represent anything: unsigned integers, signed integers, real numbers, characters, instructions. This lesson covers the plumbing that everything else rests on: bytes, hexadecimal, word sizes, byte ordering, and the bit-level operations C gives you.

## 1. Bytes, addresses and hexadecimal

Rather than individual bits, most computers use blocks of 8 bits, **bytes**, as the smallest addressable unit of memory. A machine-level program views memory as a very large array of bytes called **virtual memory**; every byte has a unique **address**, and the set of all possible addresses is the **virtual address space**. A C pointer's value is just the virtual address of the first byte of some block of storage. The C compiler associates *type information* with each pointer so it can generate the right machine code, but the machine code itself has no notion of types: it sees only bytes.

Writing bytes in binary is verbose (00000000 to 11111111) and decimal is awkward to convert, so we use **hexadecimal**: base 16, digits `0–9` and `A–F`. One hex digit is exactly 4 bits, so a byte is two hex digits, ranging `00` to `FF`. In C, hex constants start with `0x`.

| Hex | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | A | B | C | D | E | F |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dec | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| Bin | 0000 | 0001 | 0010 | 0011 | 0100 | 0101 | 0110 | 0111 | 1000 | 1001 | 1010 | 1011 | 1100 | 1101 | 1110 | 1111 |

**Converting.** Hex→binary: expand each digit to 4 bits (`0x173A4C` → `0001 0111 0011 1010 0100 1100`). Binary→hex: group into 4-bit chunks *from the right*, padding the leftmost chunk with zeros. A handy fact: $2^n$ with $n = i + 4j$ ($0 \le i \le 3$) is written as hex digit $2^i$ followed by $j$ zeros. So $2^{11} = 2^{3+4\cdot 2}$ is `0x800`.

```python-run
for x in (0x173A4C, 2**11, 314156, 0xFF):
    print(f"{x:>8} = 0x{x:X} = 0b{x:b}")
# group a binary string into hex digits from the right
b = "1111001010110110110011"
pad = (-len(b)) % 4
b4 = "0"*pad + b
print(" ".join(b4[i:i+4] for i in range(0, len(b4), 4)), "->", hex(int(b, 2)))
```

## 2. Data sizes

Every computer has a **word size**, the nominal size of pointer data. Because a virtual address is encoded by one word, the word size $w$ determines the virtual address space: $0$ to $2^w - 1$. A 32-bit machine can address 4 GB; a 64-bit machine, in principle, 16 exabytes. Most 64-bit machines can also run 32-bit programs (compiled with `gcc -m32`).

Typical sizes in bytes of C data types:

| C declaration (signed) | Unsigned | 32-bit | 64-bit |
|---|---|---|---|
| `char` | `unsigned char` | 1 | 1 |
| `short` | `unsigned short` | 2 | 2 |
| `int` | `unsigned` | 4 | 4 |
| `long` | `unsigned long` | 4 | **8** |
| `int32_t` | `uint32_t` | 4 | 4 |
| `int64_t` | `uint64_t` | 8 | 8 |
| `char *` | | 4 | **8** |
| `float` | | 4 | 4 |
| `double` | | 8 | 8 |

> [!WARNING]
> Code that assumes `sizeof(int) == sizeof(void *)` or that a `long` is 4 bytes breaks when moved between 32- and 64-bit machines. Use the fixed-size types `int32_t`, `int64_t` (from `<stdint.h>`) when the exact width matters. Also note the C standard does not even guarantee that plain `char` is signed.

## 3. Addressing and byte ordering

A multi-byte object is stored as a **contiguous sequence of bytes**, and its address is the *smallest* address of those bytes. If an `int x` is at address `0x100`, its 4 bytes occupy `0x100`–`0x103`. But in which order?

- **Little endian**: least significant byte first (at the lowest address). Most Intel-compatible machines.
- **Big endian**: most significant byte first. Many IBM and Oracle (Sun) machines; also "network byte order".
- **Bi-endian**: many recent chips (ARM, for example) can be configured either way, though in practice the OS usually fixes one (Android and iOS run little endian).

For `x = 0x01234567` at address `0x100`:

| Address | 0x100 | 0x101 | 0x102 | 0x103 |
|---|---|---|---|---|
| Big endian | 01 | 23 | 45 | 67 |
| Little endian | 67 | 45 | 23 | 01 |

The terms come from *Gulliver's Travels*, where two factions fought over which end of a boiled egg to crack. The choice is arbitrary, and most of the time invisible. It matters in three situations:

1. **Networking.** Binary data sent between machines of different endianness arrives reversed unless both sides convert to an agreed network standard (`htonl`, `ntohl`; see Module 11).
2. **Reading machine code.** A disassembler line such as `01 05 43 0b 20 00  add %eax,0x200b43(%rip)` shows the constant `0x00200b43` stored as bytes `43 0b 20 00`: little endian.
3. **Circumventing the type system.** Casts and unions that view an object through a different type expose the byte order.

The book's `show_bytes` routine prints an object's bytes in address order by casting its address to `unsigned char *`:

```c
typedef unsigned char *byte_pointer;

void show_bytes(byte_pointer start, size_t len) {
    for (size_t i = 0; i < len; i++)
        printf(" %.2x", start[i]);
    printf("\n");
}
void show_int(int x) { show_bytes((byte_pointer) &x, sizeof(int)); }
```

We can mimic it in Python with `struct`:

```python-run
import struct
def show_bytes(fmt, x):
    return " ".join(f"{b:02x}" for b in struct.pack(fmt, x))

x = 12345          # 0x00003039
print("int    little:", show_bytes("<i", x))
print("int    big   :", show_bytes(">i", x))
print("float  little:", show_bytes("<f", float(x)))  # 0x4640E400
print("long   little:", show_bytes("<q", x))
```

Notice that the integer 12345 (`0x00003039`) and the float 12345.0 (`0x4640E400`) have completely different byte patterns, yet if you line up their binary representations you will find a run of 13 matching bits: the float's fraction field holds the integer's bits after the leading 1. You will see why in the floating-point lesson.

### Strings and code

A C string is an array of characters terminated by a null byte (0). Since each ASCII character is one byte, **strings are independent of byte order and word size**: `"12345"` is `31 32 33 34 35 00` everywhere. Text data is therefore more portable than binary data. Machine code, by contrast, is *not* portable: different machine types use different instructions and encodings, and even the same processor running different OSes uses different coding conventions.

## 4. Boolean algebra

George Boole's algebra on {0, 1} gives us four basic operations:

| `~` (NOT) | `&` (AND) | `\|` (OR) | `^` (XOR) |
|---|---|---|---|
| ~0 = 1, ~1 = 0 | 1 only if both are 1 | 1 if either is 1 | 1 if exactly one is 1 |

Extended to **bit vectors** of length $w$, the operations apply bit by bit. For example, with `a = 0110` and `b = 1100`: `a & b = 0100`, `a | b = 1110`, `a ^ b = 1010`, `~b = 0011`.

Useful algebraic facts:

- `&` distributes over `|` *and* `|` distributes over `&` (unlike integer arithmetic, where $a + (b \cdot c) \ne (a+b)(a+c)$).
- With `^`, `&` and `~`, bit vectors form a **Boolean ring**: every element is its own additive inverse, `a ^ a = 0`. Hence `(a ^ b) ^ a = b`, the basis of the classic in-place swap trick.
- **De Morgan's laws**: `~(a & b) == ~a | ~b` and `~(a | b) == ~a & ~b`. These let you build `&` from `~` and `|` alone, a favorite "data lab" puzzle.

**Bit vectors as sets.** A $w$-bit vector encodes a subset of $\{0, \dots, w-1\}$: bit $i$ is 1 iff $i$ is in the set. Then `|` is union, `&` is intersection, `~` is complement. The vector `01101001` (bits 0, 3, 5, 6 set) represents $\{0, 3, 5, 6\}$. Real systems use exactly this: the signal masks in Module 8 are bit vectors selecting which signals are blocked.

## 5. Bit-level operations in C

C supports `|`, `&`, `~`, `^` on any integral type. A key idiom is **masking**: a mask is a bit pattern selecting a set of bits.

| Expression | Effect |
|---|---|
| `x & 0xFF` | the least significant byte of `x`, all else zeroed |
| `x \| 0xFF` | set the low byte to all ones |
| `x ^ ~0xFF` | complement all but the low byte |
| `~0` | all ones, *portably*, whatever the word size (better than writing `0xFFFFFFFF`) |
| `x & (x - 1)` | clear the lowest set bit |
| `x & -x` | isolate the lowest set bit |

```python-run
M32 = 0xFFFFFFFF
x = 0x87654321
print(hex(x & 0xFF))                    # 0x21
print(hex((x ^ ~0xFF) & M32))            # 0x789abc21
print(hex((x | 0xFF) & M32))             # 0x876543ff
# bitAnd using only ~ and | (De Morgan)
a, b = 0b0110, 0b1100
print(bin((~(~a | ~b)) & 0xF))           # 0b100
# x & (x-1) clears the lowest set bit -> power-of-two test
for v in (1, 2, 3, 64, 96, 0):
    print(v, "power of two?", v != 0 and (v & (v - 1)) == 0)
```

<div class="widget" data-widget="bits"></div>

Use the explorer above: type a number, flip bits, and watch the unsigned and two's-complement readings change. Try setting only the top bit.

## 6. Logical operations are different

C also has **logical** operators `||`, `&&`, `!`. They treat any nonzero argument as true and 0 as false, and always return 0 or 1. Two important differences from the bitwise ones:

1. `!0x41` is `0x00` but `~0x41` is `0xBE`. `0x69 && 0x55` is `0x01` but `0x69 & 0x55` is `0x41`.
2. **Short-circuit evaluation**: if the first argument determines the result, the second is not evaluated. So `a && 5/a` never divides by zero, and `p && *p++` never dereferences a null pointer.

A classic puzzle: `!(x ^ y)` is 1 exactly when `x == y`, using only bit-level and logical operations.

## 7. Shift operations

`x << k` shifts the bit vector left by $k$, dropping the $k$ most significant bits and filling the right with zeros. Right shift `x >> k` comes in two flavors:

- **Logical** right shift fills the left with zeros.
- **Arithmetic** right shift fills the left with $k$ copies of the *most significant bit*. This is what you want for signed integers (it divides by $2^k$, rounding toward $-\infty$, as the next lessons show).

For an 8-bit `x = 10010101`: `x << 4` = `01010000`, logical `x >> 4` = `00001001`, arithmetic `x >> 4` = `11111001`.

The C standard does not say which right shift signed data uses, but almost every compiler/machine combination uses **arithmetic** shifts for signed values. For unsigned values, right shifts **must** be logical. Java avoids the ambiguity with two operators, `>>` (arithmetic) and `>>>` (logical).

> [!WARNING]
> **Shifting by $k \ge w$ is undefined in C.** On many machines only the low $\log_2 w$ bits of the shift amount are used, so a 32-bit `int` shifted by 36 behaves like a shift by 4. Never rely on it. (Java defines exactly this mod-$w$ behavior.)

> [!WARNING]
> **Precedence trap.** `1<<2 + 3<<4` parses as `1 << (2+3) << 4` because `+` binds tighter than `<<`. The result is 512, not 52. When in doubt, parenthesize.

```python-run
def shr_logical(x, k, w=8):
    return (x & ((1 << w) - 1)) >> k

def shr_arith(x, k, w=8):
    x &= (1 << w) - 1
    if x >> (w - 1):              # negative in two's complement
        x -= 1 << w
    return (x >> k) & ((1 << w) - 1)   # Python >> on ints is arithmetic

x = 0b10010101
print(f"{(x << 4) & 0xFF:08b}  << 4")
print(f"{shr_logical(x, 4):08b}  logical >> 4")
print(f"{shr_arith(x, 4):08b}  arithmetic >> 4")
print("precedence:", 1<<2 + 3<<4)
```

## 8. Worked example: byte extraction and replacement

Problems like "replace byte $i$ of $x$ with $b$" combine masking and shifting:

```c
unsigned replace_byte(unsigned x, int i, unsigned char b) {
    unsigned mask = 0xFFu << (i << 3);         // i*8 via shift
    return (x & ~mask) | ((unsigned) b << (i << 3));
}
// replace_byte(0x12345678, 2, 0xAB) == 0x12AB5678
// replace_byte(0x12345678, 0, 0xAB) == 0x123456AB
```

Byte $i$ (counting from the least significant) occupies bits $8i$ to $8i+7$. The mask isolates those bits; `& ~mask` clears them; shifting `b` into position and OR-ing installs the new value. Note that "byte 0" here means the *least significant* byte, independent of byte order in memory: shifts and masks operate on *values*, not on memory layout.

> [!INTERVIEW]
> Bit-manipulation questions are common. Know: `x & (x-1)` (clear lowest set bit; power-of-two test), `x & -x` (lowest set bit), XOR swap and "find the element appearing once", population count (Kernighan's loop runs once per set bit), and how to test endianness at run time (store `int x = 1` and look at the first byte through a `char *`: 1 means little endian).

## 9. Summary

- Memory is a byte array; addresses name bytes; pointers are addresses plus a compile-time type.
- Hex is shorthand for 4-bit groups. Word size bounds the address space; `long` and pointers are 8 bytes on x86-64.
- Multi-byte objects are stored contiguously; **little endian** stores the least significant byte at the lowest address.
- Bitwise `& | ^ ~` act per bit and support masking; logical `&& || !` return 0/1 and short-circuit.
- Left shift fills with zeros; right shift is logical (unsigned) or arithmetic (signed, in practice). Shifts by $\ge w$ are undefined.

## Check yourself

```quiz
[
  {"q": "The int 0x01234567 is stored at address 0x100 on a little-endian machine. What byte is at 0x100?", "options": ["0x01", "0x23", "0x45", "0x67"], "answer": 3,
   "explain": "Little endian puts the least significant byte, 0x67, at the lowest address."},
  {"q": "What is 0x69 && 0x55 in C?", "options": ["0x41", "0x7D", "0x01", "0x00"], "answer": 2,
   "explain": "Logical AND of two nonzero values yields 1. The bitwise AND would be 0x41."},
  {"q": "For the 8-bit value 10010101, what does an arithmetic right shift by 4 give?", "options": ["00001001", "11111001", "01010000", "10011001"], "answer": 1,
   "explain": "Arithmetic shift copies the sign bit (1) into the four vacated positions."},
  {"q": "What does x & (x - 1) compute?", "options": ["x with its lowest set bit cleared", "x with its highest bit cleared", "Always 0", "x rounded to a power of two"], "answer": 0,
   "explain": "Subtracting 1 flips the lowest 1 and all zeros below it; ANDing clears exactly that lowest 1."},
  {"q": "Which expression yields all ones regardless of word size?", "options": ["0xFFFFFFFF", "~0", "!0", "-0"], "answer": 1,
   "explain": "~0 complements every bit of 0 at whatever width the type has; !0 is just 1."},
  {"q": "Why are ASCII strings portable across byte orders?", "options": ["Compilers reverse them", "Each character is one byte and strings are arrays, so there is no multi-byte ordering", "Strings are stored big endian", "They are not portable"], "answer": 1,
   "explain": "Endianness concerns the order of bytes within a multi-byte scalar; a char array has no such ordering issue."},
  {"q": "What is 1<<2 + 3<<4 in C?", "options": ["52", "512", "28", "Undefined"], "answer": 1,
   "explain": "Addition binds tighter: 1 << (2+3) << 4 = 1 << 5 << 4 = 512."},
  {"q": "On x86-64 Linux, sizeof(long) and sizeof(char *) are:", "options": ["4 and 4", "4 and 8", "8 and 8", "8 and 4"], "answer": 2,
   "explain": "Both are 8 bytes in the LP64 model used by 64-bit Linux."}
]
```

> **Source:** CS:APP 3e, §2.1 (Information storage: hexadecimal, data sizes, addressing and byte ordering, strings, code, Boolean algebra, bit-level, logical and shift operations in C).
