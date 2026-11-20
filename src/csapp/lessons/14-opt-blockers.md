# CPE and optimization blockers

The primary objective of programming is to make code **work correctly** under all conditions; a fast program that gives wrong answers is useless. Programmers must also write clear, maintainable code. But there are many occasions where speed matters: real-time video processing, network packet handling, or a computation that would otherwise take weeks. Writing efficient programs requires three things: (1) choosing appropriate **algorithms and data structures**; (2) writing source code the **compiler can optimize effectively**; and (3) for heavy computations, exploiting **parallelism**. This lesson and the next focus on (2): understanding what optimizing compilers can and cannot do, and how to eliminate the "optimization blockers" that prevent them from producing efficient code.

## 1. Capabilities and limitations of optimizing compilers

Modern compilers perform sophisticated analysis: they determine what values expressions compute and how they are used, then simplify expressions, reuse a single computation in several places, reduce how often a computation runs, and so on. GCC's optimization levels (`-Og`, `-O1`, `-O2`, `-O3`) enable progressively more transformations.

But compilers apply only **safe** optimizations: the optimized program must behave identically to the unoptimized one **for every possible case** the program may encounter, up to the guarantees of the C standard. When in doubt, the compiler must be conservative. Two aspects of C are major **optimization blockers**.

### Blocker 1: memory aliasing

```c
void twiddle1(long *xp, long *yp) {
    *xp += *yp;
    *xp += *yp;
}
void twiddle2(long *xp, long *yp) {
    *xp += 2 * *yp;
}
```

`twiddle2` needs three memory references (read `*xp`, read `*yp`, write `*xp`); `twiddle1` needs six. They look equivalent, but they are **not** if `xp == yp`: `twiddle1` then quadruples `*xp` (double it twice), while `twiddle2` triples it. Since the compiler cannot know how the function will be called, it must assume the two pointers might be **aliases** (point to the same location) and cannot turn `twiddle1` into `twiddle2`.

```python-run
def twiddle1(mem, xp, yp):
    mem[xp] += mem[yp]; mem[xp] += mem[yp]
def twiddle2(mem, xp, yp):
    mem[xp] += 2 * mem[yp]
for xp, yp in [(0, 1), (0, 0)]:
    a, b = [5, 7], [5, 7]
    twiddle1(a, xp, yp); twiddle2(b, xp, yp)
    print(f"xp={xp}, yp={yp}: twiddle1 -> {a[xp]}, twiddle2 -> {b[xp]}")
```

Another example: after `x = 1000; y = 3000; *q = y; *p = x; t1 = *q;` the value of `t1` is 3000 if `p` and `q` differ, but 1000 if they alias. The compiler must reload from memory rather than reuse `y`.

### Blocker 2: function calls

```c
long f();
long func1() { return f() + f() + f() + f(); }
long func2() { return 4 * f(); }
```

Can `func1` be rewritten as `func2`? Not if `f` has **side effects**:

```c
long counter = 0;
long f() { return counter++; }
```

Then `func1` returns $0+1+2+3 = 6$ but `func2` returns 0. Most compilers do not try to determine whether a function is side-effect free, so they treat any call as a potential modifier of global state and leave calls intact. (**Inlining**, substituting the function body at the call site, both removes call overhead and exposes the code to further optimization; GCC inlines within a single file at `-O1` and above in some cases, more aggressively at `-O2`/`-O3`.)

> [!TIP]
> GCC is considered adequate, but not exceptional, in its optimization capabilities; it does not do the most aggressive transformations. That means programmers who write code in a compiler-friendly style get real gains.

## 2. Expressing program performance: CPE

For code that iterates over data, the book uses **cycles per element (CPE)**: the slope of the line relating run time (in clock cycles) to the number of elements $n$. Using cycles rather than nanoseconds ties the measure to the processor's work rather than to its clock rate. A 4 GHz processor has a 0.25 ns clock period.

Example: two prefix-sum implementations, one computing a single element per iteration (`psum1`) and one unrolled to compute two (`psum2`), measured as approximately $368 + 9.0n$ and $368 + 6.0n$ cycles. Their CPEs are 9.0 and 6.0. For large $n$ the constant term is irrelevant; the CPE *is* the performance.

## 3. The running example

A simple vector abstraction:

```c
typedef struct {
    long len;
    data_t *data;
} vec_rec, *vec_ptr;

/* Retrieve element with bounds check; returns 0 on failure */
int get_vec_element(vec_ptr v, long index, data_t *dest);
long vec_length(vec_ptr v);
```

and a function combining all elements with an operation `OP` and identity `IDENT` (`+` and 0 for sum, `*` and 1 for product), where `data_t` can be `long` or `double`:

```c
void combine1(vec_ptr v, data_t *dest) {
    long i;
    *dest = IDENT;
    for (i = 0; i < vec_length(v); i++) {
        data_t val;
        get_vec_element(v, i, &val);
        *dest = *dest OP val;
    }
}
```

Measured CPEs on the book's reference machine (Intel Core i7 Haswell):

| Function | Method | int + | int * | FP + | FP * |
|---|---|---|---|---|---|
| combine1 | Abstract, unoptimized (`-O0`) | 22.68 | 20.02 | 19.98 | 20.18 |
| combine1 | Abstract, `-O1` | 10.12 | 10.12 | 10.17 | 11.14 |

Just enabling `-O1` halves the time. Now we improve the code by hand.

## 4. Eliminating loop inefficiencies (code motion)

`combine1` calls `vec_length` in the loop test, **every iteration**, though the length never changes. Moving it out is called **code motion**: identify a computation performed repeatedly that always produces the same result, and move it to where it is evaluated once.

```c
void combine2(vec_ptr v, data_t *dest) {
    long i;
    long length = vec_length(v);
    *dest = IDENT;
    for (i = 0; i < length; i++) {
        data_t val;
        get_vec_element(v, i, &val);
        *dest = *dest OP val;
    }
}
```

CPE drops to 7.02 / 9.03 / 9.02 / 11.03. The compiler cannot do this itself: it cannot prove `vec_length` has no side effects or always returns the same value.

### The strlen disaster

This looks innocent:

```c
void lower1(char *s) {
    for (long i = 0; i < strlen(s); i++)
        if (s[i] >= 'A' && s[i] <= 'Z')
            s[i] -= ('A' - 'a');
}
```

But `strlen` walks the whole string, costing $O(n)$, and it is called on each of $n$ iterations: the loop is **quadratic**. The book measures a 1,048,576-character string at about **17 minutes** for `lower1` versus about **2.0 milliseconds** for `lower2`, which hoists `strlen` out of the loop: over 500,000× faster. The compiler will not hoist it for you, because the loop modifies the string, and proving that the modifications never create or remove a null terminator is beyond it.

```python-run
import time
def clen(s):                      # emulate C strlen: O(n) scan for the terminator
    n = 0
    while s[n] != 0: n += 1
    return n
def lower1(s):
    i = 0
    while i < clen(s):            # strlen in the loop test: quadratic
        if 65 <= s[i] <= 90: s[i] += 32
        i += 1
def lower2(s):
    n = clen(s)                   # hoisted: linear
    for i in range(n):
        if 65 <= s[i] <= 90: s[i] += 32
for n in (500, 1000, 2000):
    a = [65] * n + [0]; b = list(a)
    t = time.perf_counter(); lower1(a); t1 = time.perf_counter() - t
    t = time.perf_counter(); lower2(b); t2 = time.perf_counter() - t
    print(f"n={n:5}: lower1 {t1*1e3:8.2f} ms   lower2 {t2*1e3:6.2f} ms   ratio {t1/t2:7.1f}")
```

Doubling $n$ roughly quadruples `lower1`'s time. Such "insignificant" inefficiencies lurk in real code until the day the input is large.

## 5. Reducing procedure calls

`get_vec_element` performs a bounds check on every access, yet the loop already guarantees valid indices. Fetch the underlying array once and index it directly:

```c
data_t *get_vec_start(vec_ptr v) { return v->data; }

void combine3(vec_ptr v, data_t *dest) {
    long i;
    long length = vec_length(v);
    data_t *data = get_vec_start(v);
    *dest = IDENT;
    for (i = 0; i < length; i++)
        *dest = *dest OP data[i];
}
```

Surprisingly, performance barely changes (7.17 / 9.02 / 9.02 / 11.03). The bounds checks were highly predictable branches that the processor handled almost for free; something else is the bottleneck. (This costs modularity, too: the function now depends on the vector's representation. Such trade-offs are common in performance work and should be documented.)

## 6. Eliminating unneeded memory references

Look at combine3's inner loop for `double` multiplication:

```
.L17:                               # loop:
    vmovsd  (%rbx), %xmm0           #   read product from dest
    vmulsd  (%rdx), %xmm0, %xmm0    #   multiply by data[i]
    vmovsd  %xmm0, (%rbx)           #   store product at dest
    addq    $8, %rdx                #   data+i
    cmpq    %rax, %rdx
    jne     .L17
```

The accumulated value is **read from and written to memory on every iteration**, although the value read is just the value written a moment before. Accumulate in a local variable (which the compiler keeps in a register) and store once at the end:

```c
void combine4(vec_ptr v, data_t *dest) {
    long i;
    long length = vec_length(v);
    data_t *data = get_vec_start(v);
    data_t acc = IDENT;
    for (i = 0; i < length; i++)
        acc = acc OP data[i];
    *dest = acc;
}
```

```
.L25:
    vmulsd  (%rdx), %xmm0, %xmm0    #   acc *= data[i]
    addq    $8, %rdx
    cmpq    %rax, %rdx
    jne     .L25
```

| Function | Method | int + | int * | FP + | FP * |
|---|---|---|---|---|---|
| combine3 | Direct data access | 7.17 | 9.02 | 9.02 | 11.03 |
| combine4 | Accumulate in temporary | **1.27** | **3.01** | **3.01** | **5.01** |

Improvements of 2.2× to 5.7×. Why didn't the compiler do it? **Aliasing** again. If `dest` points into the vector itself, the two versions differ. With `v = [2, 3, 5]` and `dest` pointing at the last element, computing a product: combine3 writes `IDENT` to `v[2]` first, giving `[2,3,1]`, then `[2,3,2]`, `[2,3,6]`, and finally `[2,3,36]`. combine4 leaves the vector untouched until the end and produces `[2,3,30]`. The compiler must preserve combine3's behavior, so it cannot transform it.

```python-run
def combine3(v, dest):          # dest is an index into v (aliasing!)
    v[dest] = 1
    for i in range(len(v)):
        v[dest] = v[dest] * v[i]
def combine4(v, dest):
    acc = 1
    for i in range(len(v)):
        acc *= v[i]
    v[dest] = acc
a, b = [2, 3, 5], [2, 3, 5]
combine3(a, 2); combine4(b, 2)
print(a, b)
```

> [!NOTE]
> C99's `restrict` qualifier lets you promise the compiler that a pointer is not aliased, enabling such optimizations. Fortran's no-aliasing rule for arguments is one reason numeric Fortran code historically optimized well.

## 7. Summary so far

| Version | Change | int + CPE |
|---|---|---|
| combine1 `-O0` | baseline | 22.68 |
| combine1 `-O1` | compiler optimization | 10.12 |
| combine2 | hoist `vec_length` | 7.02 |
| combine3 | remove bounds-checked calls | 7.17 |
| combine4 | accumulate in a register | 1.27 |

An 18× speedup, with no change of algorithm. The numbers 1.27, 3.01, 3.01, 5.01 are suspiciously close to 1, 3, 3, 5. The next lesson explains why: they are the **latencies** of the processor's add and multiply units, and it shows how to break through that barrier.

> [!INTERVIEW]
> **"How would you speed up a hot loop?"** A structured answer: (1) *measure* first with a profiler (Amdahl's law: optimize what dominates); (2) fix the algorithm and data structures; (3) hoist loop-invariant work, including hidden O(n) calls such as `strlen` or `.size()` on a linked structure; (4) avoid calls and abstraction overhead in the inner loop; (5) keep accumulators in locals, not behind pointers (aliasing); (6) then consider unrolling, multiple accumulators, SIMD and cache behavior.

> [!WARNING]
> Do not sacrifice readability everywhere. Apply these transformations to the measured hot spots, and keep the clean version in comments or tests.

## Check yourself

```quiz
[
  {"q": "Why can't the compiler rewrite twiddle1 (*xp += *yp twice) as twiddle2 (*xp += 2 * *yp)?", "options": ["Multiplication is slower", "If xp and yp alias, the two functions compute different results", "It would overflow", "It can and does"], "answer": 1,
   "explain": "With xp == yp, twiddle1 quadruples the value and twiddle2 triples it."},
  {"q": "What does CPE measure?", "options": ["Cache misses per element", "Clock cycles per element processed, the slope of run time vs n", "Calls per execution", "Cost per expression"], "answer": 1,
   "explain": "CPE is the per-element cost in cycles, ignoring constant overhead."},
  {"q": "Why is a loop with strlen(s) in its test, over a string being modified, quadratic?", "options": ["strlen is O(n) and is re-evaluated on each of n iterations", "Because of cache misses", "Because of branch mispredictions", "It is linear"], "answer": 0,
   "explain": "n iterations times an O(n) scan each; the compiler cannot hoist the call safely."},
  {"q": "Why can't the compiler replace f() + f() + f() + f() by 4 * f()?", "options": ["Multiplication may overflow", "f may have side effects, so the number of calls matters", "Addition is not commutative", "It violates the ABI"], "answer": 1,
   "explain": "If f modifies global state, calling it once changes the program's behavior."},
  {"q": "Going from combine3 to combine4 gave the largest speedup. What changed?", "options": ["Bounds checks were removed", "The accumulated value is kept in a register instead of being read and written through dest each iteration", "The loop was unrolled", "vec_length was hoisted"], "answer": 1,
   "explain": "Eliminating the load and store of *dest on every iteration removed a memory dependency from the critical path."},
  {"q": "With v = [2,3,5] and dest pointing at v[2], what does combine3 (product) leave in the vector?", "options": ["[2,3,30]", "[2,3,36]", "[2,3,6]", "[2,3,1]"], "answer": 1,
   "explain": "It writes 1, then 2, 6, and finally 6*6 = 36 because the last element read is the running product itself."},
  {"q": "Removing the bounds-checking function call (combine2 to combine3) barely helped because...", "options": ["The compiler had already inlined everything", "The checks were well-predicted branches not on the critical path", "Bounds checks are free in C", "The measurement was wrong"], "answer": 1,
   "explain": "Predictable branches cost little; the real bottleneck was the memory read/write of the accumulator."}
]
```

> **Source:** CS:APP 3e, §5.1–5.6 (Capabilities and limitations of optimizing compilers; Expressing program performance; Program example; Eliminating loop inefficiencies; Reducing procedure calls; Eliminating unneeded memory references).
