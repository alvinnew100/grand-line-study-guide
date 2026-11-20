# Arithmetic, condition codes and control flow

So far machine code moves data. Real programs compute and *decide*: `if`, `while`, `for`, `switch`. This lesson covers the integer arithmetic instructions (including the surprisingly versatile `leaq`), the condition codes that record what the last operation did, and how compilers translate every C control construct into compares, jumps, conditional moves and jump tables.

## 1. Load effective address

`leaq S, D` computes the effective address of memory operand `S` and writes **the address itself** into `D`, **without touching memory**. It is the C `&` operator in machine form, but compilers love it as a fast arithmetic tool because the address form computes `Imm + rb + ri*s` in one instruction.

```c
long scale(long x, long y, long z) {
    long t = x + 4 * y + 12 * z;
    return t;
}
```

```
# x in %rdi, y in %rsi, z in %rdx
scale:
    leaq    (%rdi,%rsi,4), %rax     # x + 4*y
    leaq    (%rdx,%rdx,2), %rdx     # z + 2*z = 3*z
    leaq    (%rax,%rdx,4), %rax     # (x+4y) + 4*(3z) = x + 4y + 12z
    ret
```

With `%rdx = x`, `leaq 7(%rdx,%rdx,4), %rax` sets `%rax = 5x + 7`. `leaq` does not set condition codes.

## 2. Unary, binary and shift operations

| Instruction | Effect | Description |
|---|---|---|
| `INC D` / `DEC D` | D ← D ± 1 | Increment / decrement |
| `NEG D` | D ← −D | Negate |
| `NOT D` | D ← ~D | Complement |
| `ADD S, D` | D ← D + S | Add |
| `SUB S, D` | D ← D − S | Subtract (**note the order**) |
| `IMUL S, D` | D ← D * S | Multiply (low 64 bits) |
| `XOR S, D` | D ← D ^ S | Exclusive-or |
| `OR S, D` | D ← D \| S | Or |
| `AND S, D` | D ← D & S | And |
| `SAL k, D` / `SHL k, D` | D ← D << k | Left shift (identical) |
| `SAR k, D` | D ← D >>_A k | Arithmetic right shift |
| `SHR k, D` | D ← D >>_L k | Logical right shift |

Each has `b/w/l/q` variants. `subq %rax, %rdx` computes `%rdx - %rax` (read as "subtract `%rax` *from* `%rdx`"). The shift amount is an immediate or the single-byte register `%cl` (only that one), and for $w$-bit data only the low $\log_2 w$ bits of `%cl` are used, matching the C undefined-behavior story from Module 2.

```c
long arith(long x, long y, long z) {
    long t1 = x ^ y;
    long t2 = z * 48;
    long t3 = t1 & 0x0F0F0F0F;
    long t4 = t2 - t3;
    return t4;
}
```

```
arith:
    xorq    %rsi, %rdi          # t1 = x ^ y
    leaq    (%rdx,%rdx,2), %rax # 3*z
    salq    $4, %rax            # t2 = 16 * (3*z) = 48*z
    andl    $252645135, %edi    # t3 = t1 & 0x0F0F0F0F
    subq    %rdi, %rax          # return t2 - t3
    ret
```

Note `xorq %rdx, %rdx` (or `xorl %edx, %edx`) is the idiomatic way to set a register to zero: shorter encoding than `movq $0, %rdx`.

### Special arithmetic: 128-bit products and division

Multiplying two 64-bit numbers can need 128 bits. Intel calls a 16-byte quantity an *oct word*.

| Instruction | Effect |
|---|---|
| `imulq S` | Signed full multiply: `R[%rdx]:R[%rax] ← S × R[%rax]` |
| `mulq S` | Unsigned full multiply |
| `cqto` | Sign-extend `%rax` into `%rdx:%rax` |
| `idivq S` | Signed divide `%rdx:%rax` by S: quotient → `%rax`, remainder → `%rdx` |
| `divq S` | Unsigned divide |

For signed 64-bit division, the compiler does `movq %rdi, %rax; cqto; idivq %rsi`. For unsigned, it zeros `%rdx` (`movl $0, %edx`) instead of `cqto`.

## 3. Condition codes

The CPU keeps single-bit **condition code** registers describing the most recent arithmetic or logical operation:

| Flag | Name | Set when |
|---|---|---|
| **CF** | Carry flag | The operation generated a carry out of the MSB: **unsigned** overflow |
| **ZF** | Zero flag | The result is zero |
| **SF** | Sign flag | The result is negative |
| **OF** | Overflow flag | **Two's-complement** overflow, positive or negative |

For `t = a + b` (as C ints): CF = `(unsigned) t < (unsigned) a`; ZF = `t == 0`; SF = `t < 0`; OF = `(a<0 == b<0) && (t<0 != a<0)`.

All arithmetic instructions except `leaq` set flags. Logical operations set CF and OF to 0. Shifts set CF to the last bit shifted out and OF to 0. `INC`/`DEC` set OF and ZF but leave CF alone.

Two instruction families set flags **without** changing any other register:

- `cmpq S1, S2` sets flags as for `S2 - S1` (note order: `cmpq %rsi, %rdi` compares `%rdi` against `%rsi`).
- `testq S1, S2` sets flags as for `S1 & S2`. The idiom `testq %rax, %rax` tests whether `%rax` is zero, negative or positive.

## 4. Accessing the condition codes

Flags are used three ways: (1) set a byte to 0 or 1 from a flag combination (`set`), (2) conditionally jump (`j`), (3) conditionally move (`cmov`).

| `set` / `j` suffix | Condition | Meaning |
|---|---|---|
| `e` / `z` | ZF | Equal / zero |
| `ne` / `nz` | ~ZF | Not equal |
| `s` | SF | Negative |
| `ns` | ~SF | Nonnegative |
| `g` (`nle`) | ~(SF ^ OF) & ~ZF | Greater (signed >) |
| `ge` (`nl`) | ~(SF ^ OF) | Greater or equal (signed >=) |
| `l` (`nge`) | SF ^ OF | Less (signed <) |
| `le` (`ng`) | (SF ^ OF) \| ZF | Less or equal (signed <=) |
| `a` (`nbe`) | ~CF & ~ZF | Above (unsigned >) |
| `ae` (`nb`) | ~CF | Above or equal (unsigned >=) |
| `b` (`nae`) | CF | Below (unsigned <) |
| `be` (`na`) | CF \| ZF | Below or equal (unsigned <=) |

**Why is signed "less" `SF ^ OF`?** After `cmp b, a` the CPU computes `t = a - b`. Without overflow, $a < b$ iff $t < 0$ (SF = 1). With positive overflow (a large, b very negative), the true difference is positive but $t$ appears negative (SF=1, OF=1, and $a > b$). With negative overflow, $t$ appears nonnegative but $a < b$ (SF=0, OF=1). In all cases, $a < b$ iff SF ≠ OF. For unsigned comparisons the carry flag tells you directly whether $a - b$ borrowed, i.e. $a < b$.

```c
int comp(long a, long b) { return a < b; }
```

```
comp:                     # a in %rdi, b in %rsi
    cmpq    %rsi, %rdi    # compare a:b
    setl    %al           # set low byte of %eax to 0 or 1
    movzbl  %al, %eax     # clear the rest of %eax (and %rax)
    ret
```

> [!TIP]
> The machine code does not record whether a value is signed. The **choice of instruction** reveals it: `setl`/`jl`/`jg` for signed, `setb`/`jb`/`ja` for unsigned; `sar` vs. `shr`; `movs` vs. `movz`; `idiv` vs. `div`.

```python-run
def flags_after_cmp(a, b, w=64):
    """cmp b, a  -> computes t = a - b. Returns dict of CF, ZF, SF, OF."""
    mask = (1 << w) - 1
    ua, ub = a & mask, b & mask
    t = (ua - ub) & mask
    st = t - (1 << w) if t >> (w - 1) else t
    CF = int(ua < ub)                              # borrow = unsigned below
    ZF = int(t == 0)
    SF = int(st < 0)
    OF = int((a < 0) != (b < 0) and (st < 0) != (a < 0))
    return dict(CF=CF, ZF=ZF, SF=SF, OF=OF, signed_less=SF ^ OF, unsigned_below=CF)

print(flags_after_cmp(3, 5))
print(flags_after_cmp(-1, 1))                         # signed less, but unsigned above
print(flags_after_cmp(2**63 - 1, -1))                 # overflow case
```

## 5. Jumps

A **jump** transfers control to a new position. In assembly the target is a **label**:

```
    movq $0, %rax
    jmp  .L1          # unconditional
    movq (%rax), %rdx # skipped (would be a null dereference)
.L1:
    popq %rdx
```

- `jmp Label` is a **direct** jump; `jmp *%rax` and `jmp *(%rax)` are **indirect** jumps (target read from a register or memory). Indirect jumps implement `switch` and function pointers.
- Conditional jumps (`je`, `jne`, `jl`, `jbe`, …) can only be direct.

**Jump encodings** are usually **PC-relative**: the instruction stores the difference between the target address and the address of the **instruction immediately following the jump** (because the processor has already advanced the PC when it executes the jump). In this disassembly:

```
   3:  eb 03      jmp  8 <loop+0x8>
   5:  48 d1 f8   sar  %rax
   8:  48 85 c0   test %rax,%rax
   b:  7f f8      jg   5 <loop+0x5>
```

The `jmp` at 3 encodes offset `0x03`: $0x5 + 3 = 0x8$. The `jg` encodes `0xf8` = −8: $0xd - 8 = 0x5$. PC-relative code is compact (1-byte offsets) and **position independent**: it keeps working if the linker moves it, which matters for shared libraries (Module 7).

## 6. Conditional branches vs. conditional moves

```c
long absdiff(long x, long y) {
    long result;
    if (x < y) result = y - x;
    else       result = x - y;
    return result;
}
```

**Control-flow version** (the "goto" style the compiler effectively uses):

```
absdiff:
    cmpq    %rsi, %rdi      # compare x:y
    jge     .L2             # if x >= y goto x_ge_y
    movq    %rsi, %rax
    subq    %rdi, %rax      # result = y - x
    ret
.L2:
    movq    %rdi, %rax
    subq    %rsi, %rax      # result = x - y
    ret
```

**Conditional-move version** (what gcc emits at `-O1` and above for this function):

```
absdiff:
    movq    %rsi, %rax
    subq    %rdi, %rax      # rval = y - x
    movq    %rdi, %rdx
    subq    %rsi, %rdx      # eval = x - y
    cmpq    %rsi, %rdi      # compare x:y
    cmovge  %rdx, %rax      # if >=, rval = eval
    ret
```

Why compute *both* outcomes? Pipelined processors (Module 4) guess branch outcomes far ahead. A wrong guess costs a large **misprediction penalty**, about 15–30 cycles. For an unpredictable `x < y`, the book measures about 8 cycles per call when predictable versus about 17.5 when random, a penalty of around 19 cycles. The `cmov` version takes about 8 cycles regardless.

But conditional moves are not always legal or wise. Both branches are always evaluated, so `cmov` cannot be used when:

- a branch could cause an error: `return (xp ? *xp : 0);` must not dereference a null `xp`;
- a branch has side effects (`lcount++`);
- a branch is expensive, making evaluating both slower than a misprediction.

Compilers therefore use `cmov` only for cheap, safe expressions.

## 7. Loops

C's loops compile into conditional tests and jumps. Learning the patterns makes loop assembly instantly readable.

### do-while

```
loop:
    body-statement
    t = test-expr;
    if (t) goto loop;
```

### while

gcc uses one of two translations:

**Jump to middle** (`-Og`):

```
    goto test;
loop:
    body-statement
test:
    t = test-expr;
    if (t) goto loop;
```

**Guarded do** (`-O1` and higher): test once to skip the loop entirely, then run a do-while. This lets the compiler optimize the loop test, e.g., knowing the first test already passed.

```
    t = test-expr;
    if (!t) goto done;
loop:
    body-statement
    t = test-expr;
    if (t) goto loop;
done:
```

Example, factorial with a while loop, jump-to-middle style:

```c
long fact_while(long n) {
    long result = 1;
    while (n > 1) {
        result *= n;
        n = n - 1;
    }
    return result;
}
```

```
fact_while:                 # n in %rdi
    movl    $1, %eax        # result = 1
    jmp     .L5             # goto test
.L6:                        # loop:
    imulq   %rdi, %rax      #   result *= n
    subq    $1, %rdi        #   n--
.L5:                        # test:
    cmpq    $1, %rdi        #   compare n:1
    jg      .L6             #   if > goto loop
    rep; ret
```

(`rep; ret` is a harmless prefix that avoids a branch-predictor quirk on some AMD processors; treat it as `ret`.)

### for

`for (init; test; update) body` is equivalent to

```c
init;
while (test) {
    body;
    update;
}
```

and is translated with either while strategy. The one subtlety is `continue`: in a `for` loop, `continue` must still execute `update`, so a naive rewrite to `while` that places `continue` before the update creates an infinite loop. Compilers jump to the update code instead.

## 8. Switch statements and jump tables

A `switch` with several cases over a small, dense range of values is compiled into a **jump table**: an array where entry *i* is the address of the code for case *i*. Dispatch takes constant time regardless of the number of cases.

```c
void switch_eg(long x, long n, long *dest) {
    long val = x;
    switch (n) {
    case 100: val *= 13; break;
    case 102: val += 10;      /* fall through */
    case 103: val += 11; break;
    case 104:
    case 106: val *= val; break;
    default:  val = 0;
    }
    *dest = val;
}
```

The compiler subtracts the smallest case (100) so the index ranges 0–6, uses an **unsigned** comparison to send everything outside 0–6 (including negative indices, which become huge unsigned numbers) to the default, then performs an indirect jump:

```
switch_eg:                      # x in %rdi, n in %rsi, dest in %rdx
    subq    $100, %rsi          # index = n - 100
    cmpq    $6, %rsi
    ja      .L8                 # if index > 6 (unsigned) goto default
    jmp     *.L4(,%rsi,8)       # goto *jt[index]
.L3: leaq (%rdi,%rdi,2), %rax   # case 100: 3*x
     leaq (%rdi,%rax,4), %rdi   #   val = 13*x
     jmp  .L2
.L5: addq $10, %rdi             # case 102: val += 10, fall through
.L6: addq $11, %rdi             # case 103
     jmp  .L2
.L7: imulq %rdi, %rdi           # cases 104, 106
     jmp  .L2
.L8: movl $0, %edi              # default
.L2: movq %rdi, (%rdx)          # *dest = val
     ret

    .section .rodata
    .align 8
.L4:
    .quad .L3   # case 100
    .quad .L8   # case 101: missing -> default
    .quad .L5   # case 102
    .quad .L6   # case 103
    .quad .L7   # case 104
    .quad .L8   # case 105: missing -> default
    .quad .L7   # case 106
```

Missing cases point at the default; duplicate cases (104, 106) share a label; fall-through is simply the absence of a jump. When the case values are sparse (e.g., 1, 1000, 1000000), the compiler instead emits a tree of comparisons.

> [!INTERVIEW]
> **"Is a switch faster than if-else?"** For many dense cases, usually yes: a jump table gives O(1) dispatch with one indirect jump, while an if-else chain needs up to n compares. For sparse cases compilers use a binary decision tree, O(log n). Also mention that unpredictable branches cost ~15–30 cycles, which is why branchless code (`cmov`, or arithmetic tricks) can win in hot loops on random data.

## 9. Summary

- `leaq` computes addresses (and cheap arithmetic like `5x+7`) without memory access or flag changes.
- `SUB S,D` is `D - S`; `cmp S1,S2` sets flags from `S2 - S1`; `test` from `AND`.
- CF = unsigned overflow, OF = signed overflow, ZF zero, SF sign. Signed less = `SF ^ OF`; unsigned below = `CF`.
- Jumps are usually PC-relative to the *next* instruction. Indirect jumps use `*`.
- `cmov` avoids misprediction penalties but evaluates both sides.
- while loops compile to jump-to-middle or guarded-do; switches with dense cases compile to jump tables guarded by an unsigned range check.

## Check yourself

```quiz
[
  {"q": "With x in %rdx, what does leaq 7(%rdx,%rdx,4), %rax compute?", "options": ["4x + 7", "5x + 7", "M[5x + 7]", "x + 28"], "answer": 1,
   "explain": "7 + x + 4x = 5x + 7; leaq never reads memory."},
  {"q": "After cmpq %rsi, %rdi, the jl instruction jumps when...", "options": ["%rsi < %rdi signed", "%rdi < %rsi signed", "%rdi < %rsi unsigned", "they are equal"], "answer": 1,
   "explain": "cmp S1,S2 compares S2 with S1, i.e. %rdi against %rsi; jl tests SF ^ OF for signed less."},
  {"q": "Which flag indicates unsigned overflow?", "options": ["ZF", "SF", "OF", "CF"], "answer": 3,
   "explain": "The carry flag records a carry (or borrow) out of the most significant bit."},
  {"q": "A jump instruction at address 0x3 is 2 bytes long and encodes offset 0x03. Its target is:", "options": ["0x6", "0x8", "0x5", "0x3"], "answer": 1,
   "explain": "PC-relative targets are measured from the next instruction: 0x5 + 0x3 = 0x8."},
  {"q": "Why can't the compiler use a conditional move for return xp ? *xp : 0;?", "options": ["cmov only works on bytes", "Both operands are evaluated, so *xp would be dereferenced even when xp is null", "cmov cannot use memory", "It is slower"], "answer": 1,
   "explain": "Conditional moves compute both values first; dereferencing a null pointer would fault."},
  {"q": "How does a jump-table switch handle negative indices after subtracting the minimum case?", "options": ["A separate signed test", "An unsigned comparison (ja) treats negatives as huge values and sends them to default", "It crashes", "The table has negative entries"], "answer": 1,
   "explain": "One unsigned compare catches both index < 0 and index > max."},
  {"q": "What does the guarded-do translation of a while loop do first?", "options": ["Jumps to the test at the bottom", "Tests the condition once and skips the loop if false, then runs a do-while", "Executes the body once unconditionally", "Builds a jump table"], "answer": 1,
   "explain": "Guarded-do = initial test plus do-while, used at -O1 and above."},
  {"q": "Which instruction sets condition codes like SUB but discards the result?", "options": ["test", "cmp", "lea", "set"], "answer": 1,
   "explain": "cmp performs the subtraction only for its effect on the flags; test does the same for AND."}
]
```

> **Source:** CS:APP 3e, §3.5–3.6 (Arithmetic and logical operations; Control: condition codes, accessing them, jumps and their encodings, conditional branches and moves, loops, switch statements).
