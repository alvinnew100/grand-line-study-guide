"""Go track problems, part 1: fixed-width integers, slices, strings, maps, scopes, switch, defer, escape analysis.

Go cannot run in the browser, so every problem is solved in Python and models one precisely
defined piece of Go behaviour. Each guide ends with the idiomatic Go that shows the same behaviour.
"""

PROBLEMS = [
# ------------------------------------------------------------------ go-int-overflow
dict(
    id="go-int-overflow",
    title="Fixed-width integers: wrap-around and conversions",
    difficulty="Medium",
    pattern="Go types",
    entry="fixed_width",
    description=r"""
Go integers have a fixed number of bits. When a result does not fit, the extra high bits are thrown
away and the value **wraps around** silently (no error, unlike Python's unlimited integers).

Write `fixed_width(kind, start, ops)` that simulates a Go variable of type `kind`.

- `kind` is one of `"int8"`, `"int16"`, `"int32"`, `"int64"`, `"uint8"`, `"uint16"`, `"uint32"`, `"uint64"`.
- `start` is any Python integer. It is first wrapped into `kind`.
- `ops` is a list of `[op, operand]` pairs applied in order:

| op | meaning in Go |
|---|---|
| `"+"`, `"-"`, `"*"` | arithmetic, result wrapped to the current type |
| `"/"` | integer division that **truncates toward zero** (`-7 / 2` is `-3`) |
| `"%"` | remainder with the **sign of the left operand** (`-7 % 2` is `-1`) |
| `"<<"` | shift left by `operand` bits, result wrapped |
| `">>"` | shift right by `operand` bits (keeps the sign for signed types) |
| `"conv"` | `operand` is a type name: convert the current value to that type (keep the low bits, reinterpret) |

For `+ - * / %` the operand is first wrapped into the current type (as if it were a variable of that
type). For shifts the operand is a non-negative bit count and is used as it is.

**Wrapping rule.** For a type with `b` bits keep `v mod 2^b`. For a signed type, if that is
`>= 2^(b-1)`, subtract `2^b`.

Dividing (`/` or `%`) by zero stops everything: return the string
`"panic: runtime error: integer divide by zero"`.

Otherwise return `[final_type, final_value]`.

**Example 1:** `fixed_width("uint8", 250, [["+", 10]])` → `["uint8", 4]` (260 does not fit in 8 bits; 260 − 256 = 4)

**Example 2:** `fixed_width("int8", 127, [["+", 1]])` → `["int8", -128]`

**Example 3:** `fixed_width("int32", -7, [["/", 2]])` → `["int32", -3]`
""",
    starter='''def fixed_width(kind, start, ops):
    # return [final_type, final_value] or the panic string
    pass
''',
    solution='''def fixed_width(kind, start, ops):
    def info(k):
        if k.startswith("u"):
            return False, int(k[4:])
        return True, int(k[3:])

    def wrap(v, k):
        signed, bits = info(k)
        v &= (1 << bits) - 1
        if signed and v >= 1 << (bits - 1):
            v -= 1 << bits
        return v

    cur = wrap(start, kind)
    for op, x in ops:
        if op == "conv":
            kind = x
            cur = wrap(cur, kind)
            continue
        if op == "<<":
            cur = wrap(cur << x, kind)
            continue
        if op == ">>":
            cur = cur >> x
            continue
        y = wrap(x, kind)
        if op in ("/", "%") and y == 0:
            return "panic: runtime error: integer divide by zero"
        if op == "+":
            r = cur + y
        elif op == "-":
            r = cur - y
        elif op == "*":
            r = cur * y
        elif op == "/":
            r = abs(cur) // abs(y)
            if (cur < 0) != (y < 0):
                r = -r
        else:
            r = abs(cur) % abs(y)
            if cur < 0:
                r = -r
        cur = wrap(r, kind)
    return [kind, cur]
''',
    tests=[
        ["uint8", 250, [["+", 10]]],
        ["int8", 127, [["+", 1]]],
        ["int32", -7, [["/", 2]]],
        ["int32", -7, [["%", 2]]],
        ["int64", 7, [["%", -2]]],
        ["uint8", 0, [["-", 1]]],
        ["int8", -128, [["/", -1]]],
        ["int8", -128, [["%", -1]]],
        ["int16", 300, [["conv", "uint8"]]],
        ["int8", -1, [["conv", "uint8"], ["conv", "int16"]]],
        ["uint32", 1, [["<<", 31], ["<<", 1]]],
        ["int8", -128, [[">>", 3]]],
        ["uint8", 128, [[">>", 3], ["*", 100]]],
        ["int64", 9223372036854775807, [["+", 1]]],
        ["uint16", 9, [["/", 0]]],
        ["int32", 5, [["%", 4294967296]]],
        ["uint64", -1, []],
        ["int16", 200, [["*", 200], ["conv", "int8"], ["-", 100]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def fixed_width(kind, start, ops):
    signed = not kind.startswith("u")
    def wrap(v, k):
        s = not k.startswith("u"); bits = int(k[3:] if s else k[4:])
        v &= (1 << bits) - 1
        if s and v >= 1 << (bits - 1):
            v -= 1 << bits
        return v
    cur = wrap(start, kind)
    for op, x in ops:
        if op == "conv":
            kind = x; cur = wrap(cur, kind); continue
        if op == "<<":
            cur = wrap(cur << x, kind); continue
        if op == ">>":
            cur >>= x; continue
        y = wrap(x, kind)
        if op in "/%" and y == 0:
            return "panic: runtime error: integer divide by zero"
        cur = wrap({"+": cur + y, "-": cur - y, "*": cur * y,
                    "/": cur // y if y else 0, "%": cur % y if y else 0}[op], kind)
    return [kind, cur]
''',
        '''def fixed_width(kind, start, ops):
    cur = start
    for op, x in ops:
        if op == "conv":
            kind = x
        elif op == "+":
            cur += x
        elif op == "-":
            cur -= x
        elif op == "*":
            cur *= x
        elif op == "<<":
            cur <<= x
        elif op == ">>":
            cur >>= x
        elif x == 0:
            return "panic: runtime error: integer divide by zero"
        elif op == "/":
            cur = int(cur / x)
        else:
            cur = cur - x * int(cur / x)
    return [kind, cur]
''',
    ],
    guide=dict(
        prereqs="Binary numbers and two's complement (the way computers store negative integers). "
                "Lesson: [Predeclared types, zero values and conversions](#/lesson/go/go-predeclared-types).",
        intuition="A fixed-width integer is a car odometer with a fixed number of digits: after the largest "
                  "value it rolls over to the smallest. Do the arithmetic with Python's unlimited integers, then "
                  "apply one `wrap` step that keeps only the low `b` bits and reinterprets the top bit as the sign.",
        hints=[
            "Write a helper `wrap(v, kind)` first. Everything else calls it.",
            "Python's `//` and `%` round toward negative infinity. Go rounds toward zero. Compute with absolute "
            "values and fix the sign afterwards.",
            "A conversion is nothing more than `wrap(current, new_type)`. A right shift of a negative Python "
            "integer already keeps the sign, which is what Go does for signed types.",
        ],
        brute_force="You could store the value as a list of bits and implement adders and shifters by hand. "
                    "It works, but it is slow and long. Masking does the same job in one line.",
        approach=r"""
1. Parse the type name: signed or unsigned, and the bit count `b`.
2. `wrap(v)`: `v &= 2^b - 1` keeps the low `b` bits (Python's `&` works on negative numbers as if they had
   infinitely many sign bits, which is exactly two's complement). If the type is signed and the result is
   at least `2^(b-1)`, subtract `2^b`.
3. For each operation compute the exact mathematical result, then wrap.
4. Division: `q = |a| // |b|`, negate if the signs differ. Remainder: `r = |a| % |b|`, negate if `a < 0`.

**Dry run:** `fixed_width("int8", -128, [["/", -1]])`. The exact quotient is `128`. `128 & 255 = 128`, which
is `>= 128`, so subtract 256: `-128`. Go really does give `-128` here: the one case where dividing by -1
does not change the sign.

**The same behaviour in Go:**

```go
package main

import "fmt"

func main() {
	var a uint8 = 250
	a += 10
	fmt.Println(a) // 4

	var b int8 = 127
	b++
	fmt.Println(b) // -128

	var c int32 = -7
	fmt.Println(c/2, c%2) // -3 -1

	var d int16 = 300
	fmt.Println(uint8(d)) // 44: only the low 8 bits survive
}
```
""",
        complexity="Time O(len(ops)), space O(1). Each step is a constant number of integer operations.",
        pitfalls="Using Python's `//` and `%` directly (wrong for negative operands). Forgetting to wrap the "
                 "operand as well as the result. Forgetting that the type changes after `conv`, so later "
                 "operations wrap to the new width.",
        follow_up="Add a `checked` mode that reports overflow instead of wrapping, like the helper functions "
                  "people write around `math.MaxInt64`.",
    ),
),

# ------------------------------------------------------------------ go-slice-append-sim
dict(
    id="go-slice-append-sim",
    title="Simulate slices: append growth and aliasing",
    difficulty="Hard",
    pattern="Go slices",
    entry="simulate",
    description=r"""
A Go slice is a small record with three parts: a pointer into a **backing array**, a **length**
(how many elements you can see) and a **capacity** (how many elements exist from the slice's start
to the end of the backing array). Two slices can point into the same backing array, so a write
through one can show up in the other. This is called **aliasing**.

Write `simulate(ops)` that executes these operations in order. All elements are integers.

| op | Go equivalent | rule |
|---|---|---|
| `["make", s, n, c]` | `s := make([]int, n, c)` | new backing array of `c` zeros; `s` has length `n`, capacity `c` |
| `["append", d, s, v1, v2, ...]` | `d = append(s, v1, v2, ...)` | see below |
| `["slice", d, s, lo, hi]` | `d = s[lo:hi]` | `d` shares `s`'s array; length `hi-lo`, capacity `cap(s)-lo` |
| `["set", s, i, v]` | `s[i] = v` | writes into the backing array |
| `["copy", d, s]` | `copy(d, s)` | copies `min(len(d), len(s))` elements, correct even if they overlap |

A name that was never assigned is the nil slice: length 0, capacity 0.

**append rule.** Let `k` be the number of values and `need = len(s) + k`.

- If `need <= cap(s)`: the values are written into `s`'s backing array right after its last visible
  element (overwriting whatever was there), and `d` shares that array with length `need` and the same capacity.
- Otherwise a **new** backing array is allocated, the visible elements of `s` are copied into it, then the
  values. The new capacity is:
  - `need` if `need > 2 * cap(s)`;
  - else `2 * cap(s)` if `cap(s) < 256`;
  - else start from `cap(s)` and repeat `newcap += (newcap + 768) // 4` until `newcap >= need`.

(Real Go then rounds up to a memory size class. This problem leaves that step out.)

All indexes in the tests are valid. Return, for every name that was ever assigned, in alphabetical
order: `[name, len, cap, visible_elements]`.

**Example 1:** `[["make","a",2,4], ["append","b","a",7], ["set","b",0,9]]`
→ `[["a",2,4,[9,0]], ["b",3,4,[9,0,7]]]` (b shares a's array, so the write to `b[0]` is visible in `a`)

**Example 2:** `[["append","s","s",1], ["append","s","s",2], ["append","s","s",3]]`
→ `[["s",3,4,[1,2,3]]]` (capacity goes 1, 2, 4)
""",
    starter='''def simulate(ops):
    # return [[name, len, cap, elements], ...] sorted by name
    pass
''',
    solution='''def simulate(ops):
    s = {}
    nil = lambda: [[], 0, 0, 0]
    for op in ops:
        kind = op[0]
        if kind == "make":
            _, name, ln, cp = op
            s[name] = [[0] * cp, 0, ln, cp]
        elif kind == "append":
            dst, src, vals = op[1], op[2], list(op[3:])
            arr, off, ln, cp = s.get(src) or nil()
            need = ln + len(vals)
            if need <= cp:
                for i, v in enumerate(vals):
                    arr[off + ln + i] = v
                s[dst] = [arr, off, need, cp]
            else:
                if need > 2 * cp:
                    nc = need
                elif cp < 256:
                    nc = 2 * cp
                else:
                    nc = cp
                    while nc < need:
                        nc += (nc + 768) // 4
                new = arr[off:off + ln] + vals + [0] * (nc - need)
                s[dst] = [new, 0, need, nc]
        elif kind == "slice":
            _, dst, src, lo, hi = op
            arr, off, ln, cp = s.get(src) or nil()
            s[dst] = [arr, off + lo, hi - lo, cp - lo]
        elif kind == "set":
            _, name, i, v = op
            arr, off, ln, cp = s[name]
            arr[off + i] = v
        elif kind == "copy":
            d = s.get(op[1]) or nil()
            r = s.get(op[2]) or nil()
            n = min(d[2], r[2])
            tmp = r[0][r[1]:r[1] + n]
            d[0][d[1]:d[1] + n] = tmp
    return [[name, v[2], v[3], v[0][v[1]:v[1] + v[2]]] for name, v in sorted(s.items())]
''',
    tests=[
        [[["make", "a", 2, 4], ["append", "b", "a", 7], ["set", "b", 0, 9]]],
        [[["append", "s", "s", 1], ["append", "s", "s", 2], ["append", "s", "s", 3]]],
        [[["make", "a", 3, 3], ["append", "b", "a", 4], ["set", "b", 0, 99]]],
        [[["make", "a", 5, 5], ["set", "a", 0, 1], ["set", "a", 1, 2], ["set", "a", 2, 3], ["set", "a", 3, 4],
          ["set", "a", 4, 5], ["slice", "b", "a", 1, 3], ["append", "b", "b", 100]]],
        [[["make", "a", 1, 4], ["append", "x", "a", 1], ["append", "y", "a", 2]]],
        [[["append", "s", "s", 1, 2, 3, 4, 5]]],
        [[["make", "a", 2, 2], ["append", "a", "a", 1, 2, 3]]],
        [[["make", "a", 4, 4], ["set", "a", 0, 1], ["set", "a", 1, 2], ["set", "a", 2, 3], ["set", "a", 3, 4],
          ["slice", "b", "a", 1, 4], ["copy", "b", "a"]]],
        [[["make", "a", 4, 4], ["set", "a", 0, 1], ["set", "a", 1, 2], ["set", "a", 2, 3], ["set", "a", 3, 4],
          ["slice", "b", "a", 1, 4], ["copy", "a", "b"]]],
        [[["make", "big", 256, 256], ["append", "big", "big", 1]]],
        [[["make", "big", 300, 300], ["append", "big2", "big", 1], ["slice", "tail", "big2", 299, 301]]],
        [[["make", "a", 0, 3], ["slice", "b", "a", 0, 3], ["set", "b", 2, 5], ["append", "a", "a", 1],
          ["append", "c", "a", 2, 3], ["append", "d", "c", 4]]],
        [[["make", "a", 3, 6], ["slice", "b", "a", 2, 2], ["append", "b", "b", 1, 2, 3, 4], ["append", "b", "b", 5]]],
        [[["make", "x", 0, 0], ["copy", "x", "y"], ["append", "z", "x"]]],
        [[["make", "a", 2, 8], ["slice", "b", "a", 1, 2], ["slice", "c", "b", 0, 5], ["set", "c", 4, 7],
          ["slice", "d", "a", 0, 6]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def simulate(ops):
    s = {}
    for op in ops:
        k = op[0]
        if k == "make":
            s[op[1]] = [[0] * op[2], op[3]]
        elif k == "append":
            cur = s.get(op[2], [[], 0])
            vals = list(cur[0]) + list(op[3:])
            cp = cur[1]
            if len(vals) > cp:
                cp = len(vals) if len(vals) > 2 * cp else 2 * cp
            s[op[1]] = [vals, cp]
        elif k == "slice":
            cur = s.get(op[2], [[], 0])
            s[op[1]] = [cur[0][op[3]:op[4]], cur[1] - op[3]]
        elif k == "set":
            s[op[1]][0][op[2]] = op[3]
        elif k == "copy":
            d = s.get(op[1], [[], 0]); r = s.get(op[2], [[], 0])
            n = min(len(d[0]), len(r[0]))
            d[0][:n] = r[0][:n]
    return [[n, len(v[0]), v[1], v[0]] for n, v in sorted(s.items())]
''',
        '''def simulate(ops):
    s = {}
    nil = lambda: [[], 0, 0, 0]
    for op in ops:
        kind = op[0]
        if kind == "make":
            s[op[1]] = [[0] * op[3], 0, op[2], op[3]]
        elif kind == "append":
            dst, src, vals = op[1], op[2], list(op[3:])
            arr, off, ln, cp = s.get(src) or nil()
            need = ln + len(vals)
            if need <= cp:
                for i, v in enumerate(vals):
                    arr[off + ln + i] = v
                s[dst] = [arr, off, need, cp]
            else:
                nc = max(need, 2 * cp)
                s[dst] = [arr[off:off + ln] + vals + [0] * (nc - need), 0, need, nc]
        elif kind == "slice":
            arr, off, ln, cp = s.get(op[2]) or nil()
            s[op[1]] = [arr, off + op[3], op[4] - op[3], cp - op[3]]
        elif kind == "set":
            arr, off, ln, cp = s[op[1]]
            arr[off + op[2]] = op[3]
        elif kind == "copy":
            d = s.get(op[1]) or nil(); r = s.get(op[2]) or nil()
            n = min(d[2], r[2])
            d[0][d[1]:d[1] + n] = r[0][r[1]:r[1] + n]
    return [[name, v[2], v[3], v[0][v[1]:v[1] + v[2]]] for name, v in sorted(s.items())]
''',
    ],
    guide=dict(
        prereqs="Lists and dictionaries in Python. Lessons: [Arrays and slices](#/lesson/go/go-arrays-slices) and "
                "[Slicing, aliasing and copy](#/lesson/go/go-slicing-aliasing).",
        intuition="Model exactly what Go stores. A slice value is `(array, offset, length, capacity)`. The array "
                  "is a shared Python list, so two slice records holding the *same list object* alias each other "
                  "for free. `append` either writes into the shared list (room left) or builds a fresh list (no room).",
        hints=[
            "Keep a dictionary `name -> [array, offset, len, cap]`. Never copy the Python list unless Go would "
            "allocate a new backing array.",
            "`s[lo:hi]` does not copy: same list, offset `+lo`, length `hi-lo`, capacity `cap-lo`.",
            "In `append`, when `need <= cap` write at positions `offset+len ...` of the shared list. That is the "
            "line that makes two appends to the same slice overwrite each other.",
        ],
        brute_force="Storing each slice as its own Python list of visible elements is the natural first try, and "
                    "it gets every aliasing test wrong, because writes no longer travel between slices.",
        approach=r"""
1. `make`: allocate a list of `c` zeros, record `[list, 0, n, c]`.
2. `slice`: reuse the list, shift the offset, shrink length and capacity.
3. `set`: write `list[offset + i]`.
4. `append`: compute `need`. In-place branch writes into the shared list. Growth branch computes the new
   capacity with the three-way rule, builds `visible + values + zero padding` and resets the offset to 0.
5. `copy`: take a snapshot of the source elements first, then write them, so overlapping ranges behave
   like Go's `copy` (which works like C's `memmove`).

**Dry run** of example 1. `make a 2 4` gives list `L=[0,0,0,0]`, `a=(L,0,2,4)`. `append b a 7`: need 3 <= 4, so
`L[2]=7` and `b=(L,0,3,4)`. `set b 0 9` writes `L[0]=9`. Reading `a` shows `[9,0]`: it never asked for the
change, but it shares `L`.

**The same behaviour in Go:**

```go
package main

import "fmt"

func main() {
	a := make([]int, 2, 4)
	b := append(a, 7) // room left: b shares a's backing array
	b[0] = 9
	fmt.Println(a, len(a), cap(a)) // [9 0] 2 4
	fmt.Println(b, len(b), cap(b)) // [9 0 7] 3 4

	c := append(b, 1, 2) // no room: new array, c is independent
	c[0] = -1
	fmt.Println(b[0], c[0]) // 9 -1
}
```
""",
        complexity="Each `append` that grows copies the visible elements, O(len). Everything else is O(1) or "
                   "O(number of values). Space is the total size of the backing arrays.",
        pitfalls="Copying on `slice`. Using `max(need, 2*cap)` for every size (wrong from capacity 256 upward). "
                 "Copying overlapping ranges front-to-back without a snapshot. Forgetting that `d = append(s, ...)` "
                 "can leave `s` and `d` sharing memory.",
        follow_up="Add the three-index slice `s[lo:hi:max]` (see the next problem) and check that it prevents "
                  "the overwrite in the test where `x` and `y` are both appended from `a`.",
    ),
),

# ------------------------------------------------------------------ go-slice-expr
dict(
    id="go-slice-expr",
    title="Slice expressions with capacity",
    difficulty="Medium",
    pattern="Go slices",
    entry="slice_expr",
    description=r"""
Start with a Go slice `s` of length `length` and capacity `capacity` whose backing array holds the
numbers `0, 1, 2, ..., capacity-1` (so element `i` of the array is `i`, and `s` shows the first `length` of them).

Apply a chain of slice expressions. Each one is `[lo, hi, max]`, where any entry may be `None`:

- `s[lo:hi]` is `[lo, hi, None]`. A missing `lo` means `0`. A missing `hi` means `len(s)`.
- `s[lo:hi:max]` (the *full slice expression*) also limits the capacity. When `max` is given, `hi` is given too.

Each expression is applied to the result of the previous one. Rules, where `len` and `cap` belong to
the slice being sliced:

- It is valid only if `0 <= lo <= hi <= max <= cap`, with `max = cap` when it is missing.
  Notice that `hi` may be **larger than `len`** as long as it is at most `cap`: re-slicing can reveal
  elements that were hidden.
- The result has length `hi - lo` and capacity `max - lo`, and starts `lo` elements further into the array.

If expression number `i` (0-based) is invalid, Go panics: return `["panic", i]`.
Otherwise return `[len, cap, visible_elements]` of the final slice.

**Example 1:** `slice_expr(5, 8, [[1, 3, None]])` → `[2, 7, [1, 2]]`

**Example 2:** `slice_expr(5, 8, [[1, 3, None], [0, 6, None]])` → `[6, 7, [1, 2, 3, 4, 5, 6]]` (grew back past its length)

**Example 3:** `slice_expr(5, 8, [[1, 3, 3], [0, 3, None]])` → `["panic", 1]` (capacity was capped at 2)
""",
    starter='''def slice_expr(length, capacity, exprs):
    pass
''',
    solution='''def slice_expr(length, capacity, exprs):
    off, ln, cp = 0, length, capacity
    for i, (lo, hi, mx) in enumerate(exprs):
        lo = 0 if lo is None else lo
        hi = ln if hi is None else hi
        m = cp if mx is None else mx
        if not (0 <= lo <= hi <= m <= cp):
            return ["panic", i]
        off += lo
        ln = hi - lo
        cp = m - lo
    return [ln, cp, list(range(off, off + ln))]
''',
    tests=[
        [5, 8, [[1, 3, None]]],
        [5, 8, [[1, 3, None], [0, 6, None]]],
        [5, 8, [[1, 3, 3], [0, 3, None]]],
        [5, 8, []],
        [5, 8, [[None, None, None]]],
        [5, 8, [[2, None, None], [None, 1, None]]],
        [5, 8, [[None, 0, None], [None, 8, None]]],
        [5, 8, [[6, None, None]]],
        [5, 8, [[5, None, None], [0, 3, None], [1, 2, 2]]],
        [0, 0, [[None, None, None], [0, 0, 0]]],
        [3, 3, [[0, 4, None]]],
        [10, 10, [[2, 8, 9], [1, 3, 5], [None, None, None], [0, 4, None]]],
        [10, 10, [[2, 8, 9], [1, 3, 5], [0, 5, None]]],
        [4, 6, [[3, 2, None]]],
        [4, 6, [[1, 1, 1], [0, 0, None], [0, 1, None]]],
        [6, 6, [[-1, 2, None]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def slice_expr(length, capacity, exprs):
    off, ln, cp = 0, length, capacity
    for i, (lo, hi, mx) in enumerate(exprs):
        lo = 0 if lo is None else lo
        hi = ln if hi is None else hi
        m = cp if mx is None else mx
        if not (0 <= lo <= hi <= ln and m <= cp):
            return ["panic", i]
        off += lo; ln = hi - lo; cp = m - lo
    return [ln, cp, list(range(off, off + ln))]
''',
        '''def slice_expr(length, capacity, exprs):
    off, ln, cp = 0, length, capacity
    for i, (lo, hi, mx) in enumerate(exprs):
        lo = 0 if lo is None else lo
        hi = ln if hi is None else hi
        m = cp if mx is None else mx
        if not (0 <= lo <= hi <= m <= cp):
            return ["panic", i]
        off += lo; ln = hi - lo; cp = m
    return [ln, cp, list(range(off, off + ln))]
''',
    ],
    guide=dict(
        prereqs="Lesson: [Slicing, aliasing and copy](#/lesson/go/go-slicing-aliasing).",
        intuition="A slice is a window on an array. Slicing never moves data; it only moves the left edge "
                  "(`lo`), sets the visible width (`hi - lo`) and optionally pulls in the right wall (`max`). The "
                  "bounds check is against the wall (capacity), not against what is currently visible.",
        hints=[
            "Track three numbers: offset into the original array, length and capacity.",
            "Fill in the defaults first (`lo=0`, `hi=len`, `max=cap`), then one chained comparison validates everything.",
            "Because the array holds `0..capacity-1`, the visible elements are `range(offset, offset + len)`.",
        ],
        brute_force="Build the real list and slice it with Python's `[lo:hi]`. That loses the capacity, so you "
                    "cannot grow a slice back, and Python silently clamps out-of-range bounds where Go panics.",
        approach=r"""
For each expression: default the missing parts, check `0 <= lo <= hi <= max <= cap`, then update
`offset += lo`, `len = hi - lo`, `cap = max - lo`.

**Dry run** of example 2 (`len 5, cap 8`): `[1:3]` gives offset 1, len 2, cap 7. Then `[0:6]`: `hi = 6 <= cap 7`
is fine even though the length is only 2. Result: offset 1, len 6, elements `1..6`.

**The same behaviour in Go:**

```go
package main

import "fmt"

func main() {
	base := make([]int, 5, 8)
	base = base[:8]
	for i := range base {
		base[i] = i
	}
	s := base[:5]

	t := s[1:3]
	fmt.Println(t, len(t), cap(t)) // [1 2] 2 7
	u := t[0:6]                    // legal: 6 <= cap(t)
	fmt.Println(u)                 // [1 2 3 4 5 6]

	v := s[1:3:3] // full slice expression: cap = 3-1 = 2
	fmt.Println(len(v), cap(v)) // 2 2
	_ = v[0:3]                  // panic: slice bounds out of range [:3] with capacity 2
}
```
""",
        complexity="O(number of expressions) plus O(final length) to list the elements.",
        pitfalls="Checking `hi <= len` instead of `hi <= cap`. Setting the new capacity to `max` instead of "
                 "`max - lo`. Forgetting that a missing `hi` defaults to the *length*, not the capacity.",
    ),
),

# ------------------------------------------------------------------ go-rune-byte-iter
dict(
    id="go-rune-byte-iter",
    title="Bytes, runes and range over a string",
    difficulty="Medium",
    pattern="Go strings",
    entry="string_report",
    description=r"""
A Go string is a read-only sequence of **bytes**. `len(s)` counts bytes. Text is normally stored in
UTF-8, an encoding where one character (Go calls a Unicode code point a **rune**) takes 1 to 4 bytes.
`for i, r := range s` decodes UTF-8 as it goes: `i` is the byte index where the rune starts and `r`
is the rune's number.

You are given the bytes of a string as a list of integers `0..255` (this lets the tests include
broken UTF-8). Write `string_report(data)` returning `[byte_length, rune_count, pairs]` where `pairs`
is the list of `[i, r]` that the `range` loop would produce.

**Decoding rule at byte index `i`** (`b0 = data[i]`; a *continuation byte* is in `0x80..0xBF`):

| first byte `b0` | total width | extra condition |
|---|---|---|
| `0x00..0x7F` | 1 | |
| `0xC2..0xDF` | 2 | next byte is a continuation byte |
| `0xE0..0xEF` | 3 | next 2 are continuation bytes; if `b0 == 0xE0` the second byte is `>= 0xA0`; if `b0 == 0xED` the second byte is `<= 0x9F` |
| `0xF0..0xF4` | 4 | next 3 are continuation bytes; if `b0 == 0xF0` the second byte is `>= 0x90`; if `b0 == 0xF4` the second byte is `<= 0x8F` |

If the bytes are there and the conditions hold, the rune is built from the payload bits (the low
5, 4 or 3 bits of `b0`, then the low 6 bits of every continuation byte) and the loop advances by the width.
In **every other case** (stray continuation byte, `0xC0`, `0xC1`, `0xF5..0xFF`, missing bytes, failed
condition) Go yields the replacement rune `65533` (written U+FFFD) and advances by **one** byte.

**Example 1:** `[104, 105]` (`"hi"`) → `[2, 2, [[0, 104], [1, 105]]]`

**Example 2:** `[99, 195, 169]` (`"cé"`) → `[3, 2, [[0, 99], [1, 233]]]`

**Example 3:** `[255, 65]` → `[2, 2, [[0, 65533], [1, 65]]]`
""",
    starter='''def string_report(data):
    # return [byte_length, rune_count, [[byte_index, rune], ...]]
    pass
''',
    solution='''def string_report(data):
    n = len(data)
    pairs = []
    i = 0

    def cont(j):
        return j < n and 0x80 <= data[j] <= 0xBF

    while i < n:
        b0 = data[i]
        width, r = 1, 0xFFFD
        if b0 < 0x80:
            r = b0
        elif 0xC2 <= b0 <= 0xDF:
            if cont(i + 1):
                width, r = 2, ((b0 & 0x1F) << 6) | (data[i + 1] & 0x3F)
        elif 0xE0 <= b0 <= 0xEF:
            if cont(i + 1) and cont(i + 2):
                b1 = data[i + 1]
                if not (b0 == 0xE0 and b1 < 0xA0) and not (b0 == 0xED and b1 > 0x9F):
                    width = 3
                    r = ((b0 & 0x0F) << 12) | ((b1 & 0x3F) << 6) | (data[i + 2] & 0x3F)
        elif 0xF0 <= b0 <= 0xF4:
            if cont(i + 1) and cont(i + 2) and cont(i + 3):
                b1 = data[i + 1]
                if not (b0 == 0xF0 and b1 < 0x90) and not (b0 == 0xF4 and b1 > 0x8F):
                    width = 4
                    r = (((b0 & 0x07) << 18) | ((b1 & 0x3F) << 12)
                         | ((data[i + 2] & 0x3F) << 6) | (data[i + 3] & 0x3F))
        pairs.append([i, r])
        i += width
    return [n, len(pairs), pairs]
''',
    tests=[
        [[104, 105]],
        [[99, 195, 169]],
        [[255, 65]],
        [[]],
        [list("héllo, 世界".encode("utf-8"))],
        [list("🙂a".encode("utf-8"))],
        [[226, 130]],
        [[226, 130, 172, 226, 130]],
        [[128, 191, 65]],
        [[192, 128]],
        [[224, 128, 128]],
        [[237, 160, 128]],
        [[240, 128, 128, 128]],
        [[244, 144, 128, 128]],
        [[244, 143, 191, 191]],
        [list(("naïve café " * 40).encode("utf-8"))],
        [[195, 40, 195, 169]],
    ],
    examples=3,
    wrong_solutions=[
        '''def string_report(data):
    s = bytes(data).decode("utf-8", errors="replace")
    pairs = []
    i = 0
    for ch in s:
        pairs.append([i, ord(ch)])
        i += len(ch.encode("utf-8")) if ord(ch) != 65533 else 1
    return [len(data), len(pairs), pairs]
''',
        '''def string_report(data):
    return [len(data), len(data), [[i, b] for i, b in enumerate(data)]]
''',
    ],
    guide=dict(
        prereqs="Bits and bytes, hexadecimal. Lesson: [Strings, runes and bytes](#/lesson/go/go-strings-runes).",
        intuition="UTF-8 puts the length of a character into its first byte. Read the first byte, decide how "
                  "many bytes should follow, verify them, and either accept the whole group or give up on this "
                  "single byte and move one step. Go never skips more than one byte on bad input.",
        hints=[
            "Write `cont(j)`: is index `j` inside the data and is the byte between 0x80 and 0xBF?",
            "Default to `(width 1, rune 65533)` and overwrite only when a full valid sequence is found. That "
            "handles all the error cases with no extra code.",
            "Payload bits: mask the first byte with 0x1F / 0x0F / 0x07 and each continuation byte with 0x3F, "
            "shifting left by 6 for every byte that follows.",
        ],
        brute_force="`bytes(data).decode('utf-8', errors='replace')` looks tempting, but Python may replace a "
                    "whole broken group with one U+FFFD where Go emits one per byte, and you lose the byte indexes.",
        approach=r"""
Loop with an index `i`. Classify `data[i]` with the table, check the continuation bytes and the
extra range condition, build the rune, append `[i, rune]`, advance by the width (or by 1 on error).

**Dry run** on `[226, 130, 172, 226, 130]`: at 0, `226 = 0xE2` wants two continuation bytes; 130 and 172
qualify; rune = `(2<<12) | (2<<6) | 44 = 8364` (the euro sign); advance 3. At 3, `0xE2` again but only one
byte follows, so emit `[3, 65533]` and advance 1. At 4, `130` is a stray continuation byte: `[4, 65533]`.
Result: 5 bytes, 3 runes.

**The same behaviour in Go:**

```go
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	s := "cé"
	fmt.Println(len(s), utf8.RuneCountInString(s)) // 3 2
	for i, r := range s {
		fmt.Println(i, r, string(r))
	}
	// 0 99 c
	// 1 233 é

	bad := string([]byte{0xff, 'A'})
	for i, r := range bad {
		fmt.Println(i, r) // 0 65533, then 1 65
	}
}
```
""",
        complexity="O(n) time: every byte is looked at a constant number of times. O(runes) output space.",
        pitfalls="Advancing by the *expected* width on a broken sequence (Go advances by 1). Accepting 0xC0/0xC1 "
                 "or over-long forms such as `E0 80 80`. Accepting surrogates (`ED A0 80`). Reading past the end.",
        follow_up="Write the encoder (rune to bytes) and check that decoding its output gives the rune back.",
    ),
),

# ------------------------------------------------------------------ go-map-comma-ok
dict(
    id="go-map-comma-ok",
    title="Map zero values, comma-ok and the nil map",
    difficulty="Easy",
    pattern="Go maps",
    entry="run_map_ops",
    description=r"""
Simulate a Go variable declared as `var m map[string]int`. Declared like this, `m` is a **nil map**:
it has no storage yet. Reading from a nil map is allowed, writing to it crashes the program.

Process `ops` in order and collect outputs:

| op | Go | output |
|---|---|---|
| `["make"]` | `m = make(map[string]int)` | none (replaces `m` with a new empty map) |
| `["set", k, v]` | `m[k] = v` | none |
| `["inc", k]` | `m[k]++` | none (a missing key counts as 0, so it becomes 1) |
| `["get", k]` | `m[k]` | the value, or `0` (the zero value of `int`) when the key is missing |
| `["lookup", k]` | `v, ok := m[k]` | `[v, ok]`: `[0, false]` when missing |
| `["delete", k]` | `delete(m, k)` | none (deleting a missing key is fine) |
| `["len"]` | `len(m)` | number of keys |
| `["clear"]` | `clear(m)` | none (removes every key, the map stays usable) |

On a nil map: `get`, `lookup`, `len`, `delete` and `clear` behave as on an empty map. `set` and `inc`
panic: append the string `"panic: assignment to entry in nil map"` to the outputs and stop.

Return the list of outputs.

**Example 1:** `[["make"], ["inc", "go"], ["inc", "go"], ["get", "go"], ["get", "rust"]]` → `[2, 0]`

**Example 2:** `[["make"], ["set", "a", 0], ["lookup", "a"], ["lookup", "b"]]` → `[[0, true], [0, false]]`

**Example 3:** `[["len"], ["get", "x"], ["set", "x", 1], ["len"]]` → `[0, 0, "panic: assignment to entry in nil map"]`
""",
    starter='''def run_map_ops(ops):
    pass
''',
    solution='''def run_map_ops(ops):
    m = None
    out = []
    for op in ops:
        kind = op[0]
        if kind == "make":
            m = {}
        elif kind in ("set", "inc"):
            if m is None:
                out.append("panic: assignment to entry in nil map")
                break
            if kind == "set":
                m[op[1]] = op[2]
            else:
                m[op[1]] = m.get(op[1], 0) + 1
        elif kind == "get":
            out.append((m or {}).get(op[1], 0))
        elif kind == "lookup":
            d = m or {}
            out.append([d.get(op[1], 0), op[1] in d])
        elif kind == "delete":
            if m is not None:
                m.pop(op[1], None)
        elif kind == "len":
            out.append(len(m or {}))
        elif kind == "clear":
            if m is not None:
                m.clear()
    return out
''',
    tests=[
        [[["make"], ["inc", "go"], ["inc", "go"], ["get", "go"], ["get", "rust"]]],
        [[["make"], ["set", "a", 0], ["lookup", "a"], ["lookup", "b"]]],
        [[["len"], ["get", "x"], ["set", "x", 1], ["len"]]],
        [[]],
        [[["lookup", "x"], ["delete", "x"], ["clear"], ["len"]]],
        [[["inc", "x"], ["get", "x"]]],
        [[["make"], ["set", "a", 1], ["set", "b", 2], ["delete", "a"], ["delete", "zzz"], ["len"], ["lookup", "a"]]],
        [[["make"], ["set", "a", 5], ["clear"], ["len"], ["inc", "a"], ["get", "a"]]],
        [[["make"], ["set", "a", 5], ["make"], ["get", "a"], ["len"]]],
        [[["make"], ["set", "k", -3], ["inc", "k"], ["inc", "k"], ["inc", "k"], ["lookup", "k"]]],
        [[["make"], ["get", "a"], ["len"], ["lookup", "a"], ["len"]]],
        [[["make"], ["set", "", 7], ["lookup", ""], ["len"]]],
        [[["make"]] + [["inc", "w%d" % (i % 7)] for i in range(100)] + [["get", "w0"], ["get", "w6"], ["len"]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def run_map_ops(ops):
    m = {}
    out = []
    for op in ops:
        k = op[0]
        if k == "make": m = {}
        elif k == "set": m[op[1]] = op[2]
        elif k == "inc": m[op[1]] = m.get(op[1], 0) + 1
        elif k == "get": out.append(m.get(op[1], 0))
        elif k == "lookup": out.append([m.get(op[1], 0), op[1] in m])
        elif k == "delete": m.pop(op[1], None)
        elif k == "len": out.append(len(m))
        elif k == "clear": m.clear()
    return out
''',
        '''def run_map_ops(ops):
    m = None
    out = []
    for op in ops:
        k = op[0]
        if k == "make": m = {}
        elif k in ("set", "inc"):
            if m is None:
                out.append("panic: assignment to entry in nil map"); break
            m[op[1]] = op[2] if k == "set" else m.get(op[1], 0) + 1
        elif k == "get": out.append((m or {}).get(op[1], 0))
        elif k == "lookup":
            v = (m or {}).get(op[1], 0)
            out.append([v, v != 0])
        elif k == "delete":
            if m: m.pop(op[1], None)
        elif k == "len": out.append(len(m or {}))
        elif k == "clear":
            if m: m.clear()
    return out
''',
    ],
    guide=dict(
        prereqs="Python dictionaries. Lesson: [Maps and structs](#/lesson/go/go-maps-structs).",
        intuition="Two ideas. First, a Go map never raises on a missing key; it hands back the zero value, and "
                  "the second result `ok` tells a real zero from a missing key. Second, a nil map is a map-shaped "
                  "hole: you can look into it, but there is nowhere to put anything.",
        hints=[
            "Use `None` for the nil map and a `dict` for a real one.",
            "`ok` is about the *key being present*, not about the value being non-zero.",
            "Only `set` and `inc` need storage. Everything else treats nil like an empty map.",
        ],
        brute_force="There is nothing slower to compare with; the task is a direct simulation. The work is in "
                    "getting each rule exactly right.",
        approach=r"""
Walk the operations with an `m` that is `None` or a dict. Reads use `(m or {})`. Writes check for
`None` first and stop with the panic text.

**Dry run** of example 3: `len` on nil gives 0. `get x` gives 0. `set x 1` on nil: append the panic text and
stop, so the last `len` never runs.

**The same behaviour in Go:**

```go
package main

import "fmt"

func main() {
	var m map[string]int   // nil map
	fmt.Println(len(m), m["x"]) // 0 0

	m = make(map[string]int)
	m["go"]++
	m["go"]++
	fmt.Println(m["go"], m["rust"]) // 2 0

	m["zero"] = 0
	v, ok := m["zero"]
	fmt.Println(v, ok) // 0 true
	v, ok = m["missing"]
	fmt.Println(v, ok) // 0 false

	var n map[string]int
	n["x"] = 1 // panic: assignment to entry in nil map
}
```
""",
        complexity="O(1) average per operation, like any hash map.",
        pitfalls="Starting with an empty dict instead of nil. Deciding `ok` from the value (`[0, true]` is a "
                 "legal answer). Treating `clear` on a map as making it nil: it stays a usable empty map.",
    ),
),

# ------------------------------------------------------------------ go-shadowing-scopes
dict(
    id="go-shadowing-scopes",
    title="Blocks and shadowing",
    difficulty="Medium",
    pattern="Go scope",
    entry="run_blocks",
    description=r"""
In Go every pair of braces `{ }` opens a **block**. A variable lives in the block where it was
declared and in the blocks nested inside it. Declaring a variable with a name that already exists
in an *outer* block creates a second, separate variable that hides the outer one until the inner
block ends. This is called **shadowing**.

Simulate a tiny program made of these statements (all values are integers):

| statement | Go | rule |
|---|---|---|
| `["var", x, v]` | `var x = v` | declares `x` in the current block; an error if `x` is already declared **in this same block** |
| `["short", [names], [values]]` | `a, b := 1, 2` | for each name: if it is already declared **in the current block**, assign to it; otherwise declare a new variable in the current block (shadowing any outer one). An error if **no** name is new |
| `["assign", x, v]` | `x = v` | assigns to the nearest enclosing `x`; an error if there is none |
| `["add", x, d]` | `x += d` | same lookup as assign |
| `["print", x]` | `fmt.Println(x)` | outputs the nearest enclosing `x`; an error if there is none |
| `["block", [statements]]` | `{ ... }` | runs the statements in a new nested block |

The program itself is the outermost block. Any error is a compile error in Go, so nothing would run:
return the string `"compile error"`. Otherwise return the list of printed values.
(Real Go also rejects unused variables. Ignore that rule here.)

**Example 1:** `[["var","x",1], ["block",[["short",["x"],[2]], ["print","x"]]], ["print","x"]]` → `[2, 1]`

**Example 2:** `[["var","x",1], ["block",[["assign","x",2]]], ["print","x"]]` → `[2]`

**Example 3:** `[["var","x",1], ["short",["x"],[2]]]` → `"compile error"` (no new variable on the left of `:=`)
""",
    starter='''def run_blocks(program):
    pass
''',
    solution='''def run_blocks(program):
    out = []

    class CompileError(Exception):
        pass

    def find(scopes, name):
        for sc in reversed(scopes):
            if name in sc:
                return sc
        raise CompileError()

    def run(stmts, outer):
        cur = {}
        scopes = outer + [cur]
        for st in stmts:
            kind = st[0]
            if kind == "var":
                if st[1] in cur:
                    raise CompileError()
                cur[st[1]] = st[2]
            elif kind == "short":
                names, vals = st[1], st[2]
                if all(n in cur for n in names):
                    raise CompileError()
                for n, v in zip(names, vals):
                    cur[n] = v
            elif kind == "assign":
                find(scopes, st[1])[st[1]] = st[2]
            elif kind == "add":
                find(scopes, st[1])[st[1]] += st[2]
            elif kind == "print":
                out.append(find(scopes, st[1])[st[1]])
            elif kind == "block":
                run(st[1], scopes)

    try:
        run(program, [])
    except CompileError:
        return "compile error"
    return out
''',
    tests=[
        [[["var", "x", 1], ["block", [["short", ["x"], [2]], ["print", "x"]]], ["print", "x"]]],
        [[["var", "x", 1], ["block", [["assign", "x", 2]]], ["print", "x"]]],
        [[["var", "x", 1], ["short", ["x"], [2]]]],
        [[]],
        [[["print", "x"]]],
        [[["block", [["var", "y", 5]]], ["print", "y"]]],
        [[["var", "x", 1], ["var", "x", 2]]],
        [[["var", "x", 1], ["short", ["x", "err"], [5, 0]], ["print", "x"], ["print", "err"]]],
        [[["var", "x", 1], ["block", [["short", ["x", "err"], [5, 0]], ["add", "x", 10], ["print", "x"]]], ["print", "x"]]],
        [[["var", "n", 0], ["block", [["add", "n", 1], ["block", [["add", "n", 1], ["var", "n", 100],
          ["add", "n", 1], ["print", "n"]]], ["print", "n"]]], ["print", "n"]]],
        [[["short", ["a", "b"], [1, 2]], ["short", ["b", "c"], [3, 4]], ["print", "a"], ["print", "b"], ["print", "c"]]],
        [[["var", "x", 1], ["block", [["var", "x", 2], ["block", [["var", "x", 3], ["print", "x"]]], ["print", "x"]]],
          ["print", "x"], ["block", [["print", "x"], ["assign", "x", 9]]], ["print", "x"]]],
        [[["var", "x", 1], ["print", "x"], ["block", [["assign", "z", 1]]]]],
        [[["block", [["short", ["v"], [1]], ["short", ["v"], [2]]]]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def run_blocks(program):
    out = []
    env = {}
    def run(stmts):
        for st in stmts:
            k = st[0]
            if k == "var": env[st[1]] = st[2]
            elif k == "short":
                for n, v in zip(st[1], st[2]): env[n] = v
            elif k == "assign": env[st[1]] = st[2]
            elif k == "add": env[st[1]] = env.get(st[1], 0) + st[2]
            elif k == "print": out.append(env.get(st[1]))
            elif k == "block": run(st[1])
    run(program)
    return out
''',
        '''def run_blocks(program):
    out = []
    class E(Exception): pass
    def find(scopes, name):
        for sc in reversed(scopes):
            if name in sc: return sc
        raise E()
    def run(stmts, outer):
        cur = {}; scopes = outer + [cur]
        for st in stmts:
            k = st[0]
            if k == "var":
                if st[1] in cur: raise E()
                cur[st[1]] = st[2]
            elif k == "short":
                new = False
                for n, v in zip(st[1], st[2]):
                    try:
                        find(scopes, n)[n] = v
                    except E:
                        cur[n] = v; new = True
                if not new: raise E()
            elif k == "assign": find(scopes, st[1])[st[1]] = st[2]
            elif k == "add": find(scopes, st[1])[st[1]] += st[2]
            elif k == "print": out.append(find(scopes, st[1])[st[1]])
            elif k == "block": run(st[1], scopes)
    try: run(program, [])
    except E: return "compile error"
    return out
''',
    ],
    guide=dict(
        prereqs="Recursion and dictionaries. Lesson: [Blocks, shadowing and if](#/lesson/go/go-blocks-shadowing).",
        intuition="Picture a stack of transparent sheets, one per open block. A lookup looks down through the "
                  "stack from the top and stops at the first sheet that has the name. `var` and `:=` only ever "
                  "write on the top sheet. `=` writes on whichever sheet the lookup found.",
        hints=[
            "Represent the scopes as a list of dictionaries; a nested block appends one and drops it at the end.",
            "`:=` checks only the *current* dictionary to decide between declare and assign. That one detail is "
            "the whole shadowing trap.",
            "Raise an exception for errors and catch it at the top so you can discard partial output.",
        ],
        brute_force="A single flat dictionary of variables is the tempting shortcut. It cannot represent two "
                    "variables with the same name, so every shadowing test fails.",
        approach=r"""
Recursive `run(statements, outer_scopes)` creates a fresh dictionary, pushes it and executes.

**Dry run** of the test `x := 1; { x, err := 5, 0; x += 10; print x }; print x`. Outer sheet `{x:1}`. Inside the
block, neither `x` nor `err` is on the *inner* sheet, so both are declared there: inner `{x:5, err:0}`.
`x += 10` finds the inner `x`: 15. Print 15. The block ends, the inner sheet is thrown away, and the outer
`x` is still 1. Output `[15, 1]`. This is the classic bug where the programmer meant to update the outer `x`.

**The same behaviour in Go:**

```go
package main

import (
	"fmt"
	"strconv"
)

func main() {
	x := 1
	{
		x, err := strconv.Atoi("5") // new x: shadows the outer one
		if err != nil {
			return
		}
		x += 10
		fmt.Println(x) // 15
	}
	fmt.Println(x) // 1: the outer x never changed
}
```
""",
        complexity="O(total statements × nesting depth) time, O(variables) space.",
        pitfalls="Letting `:=` assign to an outer variable. Forgetting that `:=` needs at least one new name in "
                 "the current block. Printing partial output before discovering a later compile error.",
    ),
),

# ------------------------------------------------------------------ go-switch-fallthrough
dict(
    id="go-switch-fallthrough",
    title="switch: matching, default and fallthrough",
    difficulty="Easy",
    pattern="Go control flow",
    entry="run_switch",
    description=r"""
Go's `switch` differs from the one in C or Java: after a matching case runs, control leaves the
switch **automatically**. You only continue into the next case if you write the keyword `fallthrough`.

You are given the clauses of one `switch tag { ... }` statement, in source order. Each clause is
`[values, label, fallthrough]`:

- `values` is a list of integers (`case 1, 2, 3:`), or `None` for the `default:` clause (at most one, anywhere).
- `label` is a string that the clause prints.
- `fallthrough` is `true` when the clause ends with the `fallthrough` keyword (never on the last clause).

Rules:

1. Cases are tested top to bottom; the first clause whose `values` contain the tag is chosen.
2. If no case matches, the `default` clause is chosen, wherever it sits. If there is none, nothing runs.
3. The chosen clause prints its label. If it ends in `fallthrough`, the **next clause in source order**
   runs too, without testing its values (even if it is `default`), and so on.

Write `run_switch(tags, clauses)` that runs the switch once for every tag and returns the list of
label lists.

**Example 1:** tags `[1, 3, 9]`, clauses `[[[1], "one", false], [[2, 3], "few", false], [None, "many", false]]`
→ `[["one"], ["few"], ["many"]]`

**Example 2:** tags `[1]`, clauses `[[[1], "a", true], [[2], "b", true], [[3], "c", false], [[4], "d", false]]`
→ `[["a", "b", "c"]]`
""",
    starter='''def run_switch(tags, clauses):
    pass
''',
    solution='''def run_switch(tags, clauses):
    result = []
    for tag in tags:
        start = None
        default = None
        for i, (vals, _label, _ft) in enumerate(clauses):
            if vals is None:
                default = i
            elif start is None and tag in vals:
                start = i
        if start is None:
            start = default
        out = []
        i = start
        while i is not None:
            out.append(clauses[i][1])
            i = i + 1 if clauses[i][2] and i + 1 < len(clauses) else None
        result.append(out)
    return result
''',
    tests=[
        [[1, 3, 9], [[[1], "one", False], [[2, 3], "few", False], [None, "many", False]]],
        [[1], [[[1], "a", True], [[2], "b", True], [[3], "c", False], [[4], "d", False]]],
        [[5], [[[1], "a", False]]],
        [[], [[[1], "a", False]]],
        [[1, 2], []],
        [[7, 1], [[None, "dflt", False], [[1], "one", False]]],
        [[7, 1], [[None, "dflt", True], [[1], "one", False]]],
        [[2, 9], [[[1], "a", False], [[2], "b", True], [None, "d", True], [[3], "c", False]]],
        [[2], [[[1, 2], "first", False], [[2], "second", False]]],
        [[3, 4, 5], [[[3], "x", True], [[4], "y", False], [[5], "z", False]]],
        [[0, -1], [[[-1, 0], "neg-or-zero", True], [[100], "hundred", False]]],
        [list(range(6)), [[[0, 2, 4], "even", False], [[1, 3], "odd", True], [None, "other", False]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def run_switch(tags, clauses):
    res = []
    for tag in tags:
        out = []
        started = False
        for vals, label, ft in clauses:
            if started or vals is None or tag in vals:
                out.append(label)
                started = True
                if not ft:
                    break
        res.append(out)
    return res
''',
        '''def run_switch(tags, clauses):
    res = []
    for tag in tags:
        out = []
        for vals, label, ft in clauses:
            if vals is not None and tag in vals:
                out.append(label)
                break
        else:
            for vals, label, ft in clauses:
                if vals is None:
                    out.append(label)
        res.append(out)
    return res
''',
    ],
    guide=dict(
        prereqs="Loops and lists. Lesson: [for, switch and goto](#/lesson/go/go-for-switch).",
        intuition="Two separate phases: *pick* the starting clause (first match, else default), then *run* "
                  "forward while clauses end in `fallthrough`.",
        hints=[
            "Find the index of the first matching case and, separately, the index of `default`.",
            "`default` is a fallback, not a position: a default written first still loses to a later match.",
            "After the start is chosen, the values of later clauses no longer matter.",
        ],
        brute_force="A single pass that treats `default` as 'always matches' breaks when `default` is written "
                    "before a matching case.",
        approach=r"""
For each tag: scan once to find `start` (first case containing the tag) and `default`. Use `default` if
`start` is missing. Then loop: print, and move to `i + 1` only when the clause has `fallthrough`.

**Dry run:** tag 9 on `case 1: a` / `case 2: b; fallthrough` / `default: d; fallthrough` / `case 3: c`.
No case matches, so start at `default` (index 2). Print `d`, fall through to index 3, print `c`. Result `["d", "c"]`.

**The same behaviour in Go:**

```go
package main

import "fmt"

func describe(n int) {
	switch n {
	case 1:
		fmt.Println("a")
		fallthrough
	case 2:
		fmt.Println("b")
	default:
		fmt.Println("other")
	case 3:
		fmt.Println("c")
	}
}

func main() {
	describe(1) // a, then b (fallthrough), then stop
	describe(3) // c: default written earlier does not win
	describe(8) // other
}
```
""",
        complexity="O(clauses) per tag.",
        pitfalls="Treating `default` as a match during the top-to-bottom scan. Re-testing values after a "
                 "`fallthrough`. Assuming C-style automatic fall-through.",
    ),
),

# ------------------------------------------------------------------ go-defer-order
dict(
    id="go-defer-order",
    title="defer: order and argument timing",
    difficulty="Medium",
    pattern="Go functions",
    entry="run_defers",
    description=r"""
`defer` schedules a function call to run when the surrounding function returns. Three rules decide
what you see:

1. Deferred calls run in **last-in, first-out** order (the most recently deferred runs first).
2. The **arguments** of a deferred call are evaluated at the `defer` statement, not when it runs.
3. A deferred **closure** (a function literal that uses outer variables) reads those variables when
   it finally runs, and it can even change a *named result* after the `return` statement set it.

Simulate one Go function `func f() (result int)`. All variables are integers and start at 0;
`result` is the named result. Statements:

| statement | Go | effect |
|---|---|---|
| `["set", x, v]` | `x = v` | |
| `["add", x, d]` | `x += d` | |
| `["print", x]` | `fmt.Println(x)` | prints now |
| `["defer_print", x]` | `defer fmt.Println(x)` | the value of `x` is captured **now**, printed at exit |
| `["defer_closure", x]` | `defer func() { fmt.Println(x) }()` | prints the value `x` has **at exit** |
| `["defer_add", x, d]` | `defer func() { x += d }()` | runs `x += d` at exit |
| `["return", x]` | `return x` | copies `x` into `result`, then runs the deferred calls; later statements are ignored |

If there is no `return` statement the function ends after the last statement (like a bare `return`),
and the deferred calls run then.

Return `[printed_values, returned_value]` where the returned value is `result` after all deferred calls ran.

**Example 1:** `[["defer_print","x"], ["set","x",5], ["print","x"]]` → `[[5, 0], 0]`

**Example 2:** `[["set","x",1], ["defer_print","x"], ["defer_closure","x"], ["set","x",2]]` → `[[2, 1], 0]`

**Example 3:** `[["set","x",10], ["defer_add","result",1], ["return","x"]]` → `[[], 11]`
""",
    starter='''def run_defers(stmts):
    # return [printed, returned]
    pass
''',
    solution='''def run_defers(stmts):
    env = {}
    out = []
    stack = []
    for st in stmts:
        kind = st[0]
        if kind == "set":
            env[st[1]] = st[2]
        elif kind == "add":
            env[st[1]] = env.get(st[1], 0) + st[2]
        elif kind == "print":
            out.append(env.get(st[1], 0))
        elif kind == "defer_print":
            stack.append(("value", env.get(st[1], 0)))
        elif kind == "defer_closure":
            stack.append(("read", st[1]))
        elif kind == "defer_add":
            stack.append(("add", st[1], st[2]))
        elif kind == "return":
            env["result"] = env.get(st[1], 0)
            break
    while stack:
        d = stack.pop()
        if d[0] == "value":
            out.append(d[1])
        elif d[0] == "read":
            out.append(env.get(d[1], 0))
        else:
            env[d[1]] = env.get(d[1], 0) + d[2]
    return [out, env.get("result", 0)]
''',
    tests=[
        [[["defer_print", "x"], ["set", "x", 5], ["print", "x"]]],
        [[["set", "x", 1], ["defer_print", "x"], ["defer_closure", "x"], ["set", "x", 2]]],
        [[["set", "x", 10], ["defer_add", "result", 1], ["return", "x"]]],
        [[]],
        [[["set", "i", 0], ["defer_print", "i"], ["add", "i", 1], ["defer_print", "i"], ["add", "i", 1], ["defer_print", "i"]]],
        [[["set", "i", 0], ["defer_closure", "i"], ["add", "i", 1], ["defer_closure", "i"], ["add", "i", 1], ["defer_closure", "i"]]],
        [[["set", "x", 3], ["return", "x"], ["print", "x"], ["defer_print", "x"]]],
        [[["set", "x", 4], ["defer_add", "x", 100], ["return", "x"]]],
        [[["set", "result", 7], ["defer_add", "result", 1], ["defer_add", "result", 10]]],
        [[["defer_closure", "result"], ["defer_add", "result", 5], ["set", "x", 1], ["return", "x"]]],
        [[["defer_add", "result", 5], ["defer_closure", "result"], ["set", "x", 1], ["return", "x"]]],
        [[["defer_closure", "x"], ["defer_add", "x", 2], ["defer_print", "x"], ["set", "x", 40], ["print", "x"], ["return", "x"]]],
        [[["set", "a", 1], ["set", "b", 2], ["defer_print", "a"], ["defer_closure", "b"], ["add", "a", 10],
          ["add", "b", 10], ["return", "result"]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def run_defers(stmts):
    env = {}; out = []; stack = []
    for st in stmts:
        k = st[0]
        if k == "set": env[st[1]] = st[2]
        elif k == "add": env[st[1]] = env.get(st[1], 0) + st[2]
        elif k == "print": out.append(env.get(st[1], 0))
        elif k in ("defer_print", "defer_closure"): stack.append(("read", st[1]))
        elif k == "defer_add": stack.append(("add", st[1], st[2]))
        elif k == "return":
            env["result"] = env.get(st[1], 0); break
    while stack:
        d = stack.pop()
        if d[0] == "read": out.append(env.get(d[1], 0))
        else: env[d[1]] = env.get(d[1], 0) + d[2]
    return [out, env.get("result", 0)]
''',
        '''def run_defers(stmts):
    env = {}; out = []; stack = []
    for st in stmts:
        k = st[0]
        if k == "set": env[st[1]] = st[2]
        elif k == "add": env[st[1]] = env.get(st[1], 0) + st[2]
        elif k == "print": out.append(env.get(st[1], 0))
        elif k == "defer_print": stack.append(("value", env.get(st[1], 0)))
        elif k == "defer_closure": stack.append(("read", st[1]))
        elif k == "defer_add": stack.append(("add", st[1], st[2]))
        elif k == "return":
            env["result"] = env.get(st[1], 0); break
    for d in stack:
        if d[0] == "value": out.append(d[1])
        elif d[0] == "read": out.append(env.get(d[1], 0))
        else: env[d[1]] = env.get(d[1], 0) + d[2]
    return [out, env.get("result", 0)]
''',
        '''def run_defers(stmts):
    env = {}; out = []; stack = []; ret = None
    for st in stmts:
        k = st[0]
        if k == "set": env[st[1]] = st[2]
        elif k == "add": env[st[1]] = env.get(st[1], 0) + st[2]
        elif k == "print": out.append(env.get(st[1], 0))
        elif k == "defer_print": stack.append(("value", env.get(st[1], 0)))
        elif k == "defer_closure": stack.append(("read", st[1]))
        elif k == "defer_add": stack.append(("add", st[1], st[2]))
        elif k == "return":
            ret = env.get(st[1], 0); break
    while stack:
        d = stack.pop()
        if d[0] == "value": out.append(d[1])
        elif d[0] == "read": out.append(env.get(d[1], 0))
        else: env[d[1]] = env.get(d[1], 0) + d[2]
    return [out, env.get("result", 0) if ret is None else ret]
''',
    ],
    guide=dict(
        prereqs="Stacks (last in, first out). Lesson: [Closures, defer and call by value](#/lesson/go/go-closures-defer).",
        intuition="`defer` pushes a note onto a stack. What is written on the note matters: `defer f(x)` writes "
                  "the *current value* of `x` on it; `defer func(){ ... x ... }()` writes only the *name* `x`, to "
                  "be looked up later. At exit the notes are read from the top of the stack down.",
        hints=[
            "Keep a list used as a stack; store either a captured value or a variable name.",
            "`return x` is two steps in Go: `result = x`, then run the deferred calls. Model them separately.",
            "Stop reading statements after `return`, but still run the stack.",
        ],
        brute_force="No shortcut exists; simulate. The usual wrong idea is to treat `defer` as 'run this line "
                    "at the end' and re-read every variable at exit.",
        approach=r"""
One pass over the statements building `env`, `out` and `stack`; then pop the stack until empty.

**Dry run** of example 2: `x=1`; push `("value", 1)`; push `("read", "x")`; `x=2`. Exit: pop `read x` → prints 2,
pop `value 1` → prints 1. Output `[2, 1]`.

**Dry run** of example 3: `x=10`, push `add result 1`, `return x` sets `result=10`. Exit: `result += 1` → 11.
The caller receives 11 even though the code says `return x` with `x == 10`.

**The same behaviour in Go:**

```go
package main

import "fmt"

func f() (result int) {
	x := 1
	defer fmt.Println("argument captured:", x) // x evaluated now: 1
	defer func() {
		fmt.Println("closure sees:", x) // x read at exit: 2
		result++                        // changes the value the caller gets
	}()
	x = 2
	return x // result = 2, then the deferred calls run
}

func main() {
	fmt.Println("returned:", f())
}
```

```text
closure sees: 2
argument captured: 1
returned: 3
```
""",
        complexity="O(n) time and space for n statements.",
        pitfalls="Running deferred calls first-in first-out. Reading the variable at exit for `defer_print`. "
                 "Returning the value from the `return` statement instead of the final `result`. Continuing to "
                 "execute statements after `return`.",
    ),
),

# ------------------------------------------------------------------ go-escape-analysis
dict(
    id="go-escape-analysis",
    title="Escape analysis by rules",
    difficulty="Hard",
    pattern="Go memory",
    entry="escaping",
    description=r"""
A Go function's local variables normally live on the **stack**, a region of memory that is released
the moment the function returns. If something might still point at a variable after the function
returns, the compiler must put that variable on the **heap** instead (memory managed by the garbage
collector). Deciding this is called **escape analysis**; a variable moved to the heap "escapes".

Implement a simplified version. You are given the statements of one function and a list `big` of
variables that are too large for the stack. Pointer variables and ordinary variables share one namespace.

| statement | Go | meaning for the analysis |
|---|---|---|
| `["addr", p, x]` | `p = &x` | `p` may point to `x` |
| `["assign", a, b]` | `a = b` | `a` may point to everything `b` may point to |
| `["store_field", q, p]` | `q.f = p` | every variable `q` may point to now **holds** everything `p` may point to |
| `["load_field", a, q]` | `a = q.f` | `a` may point to everything held by the variables `q` may point to |
| `["return", p]` | `return p` | everything `p` may point to escapes |
| `["store_global", p]` | `global = p` | same |
| `["send", p]` | `ch <- p` | same |
| `["go", p]` | `go func() { use(p) }()` | same |
| `["call_iface", p]` | `fmt.Println(p)` | same (the value is passed through an interface) |
| `["call", p]` | `helper(p)` | nothing escapes (the helper does not keep the pointer) |

Rules:

1. The analysis is **flow-insensitive**: the order of statements does not matter. Repeat the
   "may point to" and "holds" rules until nothing changes.
2. Every variable in `big` escapes.
3. If a variable escapes, everything it **holds** escapes too (a heap object must not point into a
   stack frame). Apply this until nothing changes.

Return the sorted list of escaping variables.

**Example 1:** `escaping([["addr","p","x"], ["return","p"]], [])` → `["x"]`

**Example 2:** `escaping([["addr","p","x"], ["call","p"]], [])` → `[]`

**Example 3:** `escaping([["addr","p","x"], ["addr","q","node"], ["store_field","q","p"], ["store_global","q"]], [])` → `["node", "x"]`
""",
    starter='''def escaping(stmts, big):
    pass
''',
    solution='''def escaping(stmts, big):
    pts = {}
    holds = {}

    def grow(table, key, items):
        cur = table.setdefault(key, set())
        before = len(cur)
        cur |= items
        return len(cur) != before

    changed = True
    while changed:
        changed = False
        for st in stmts:
            kind = st[0]
            if kind == "addr":
                changed |= grow(pts, st[1], {st[2]})
            elif kind == "assign":
                changed |= grow(pts, st[1], set(pts.get(st[2], ())))
            elif kind == "store_field":
                src = set(pts.get(st[2], ()))
                for t in list(pts.get(st[1], ())):
                    changed |= grow(holds, t, src)
            elif kind == "load_field":
                for t in list(pts.get(st[2], ())):
                    changed |= grow(pts, st[1], set(holds.get(t, ())))
    esc = set(big)
    for st in stmts:
        if st[0] in ("return", "store_global", "send", "go", "call_iface"):
            esc |= pts.get(st[1], set())
    stack = list(esc)
    while stack:
        t = stack.pop()
        for u in holds.get(t, ()):
            if u not in esc:
                esc.add(u)
                stack.append(u)
    return sorted(esc)
''',
    tests=[
        [[["addr", "p", "x"], ["return", "p"]], []],
        [[["addr", "p", "x"], ["call", "p"]], []],
        [[["addr", "p", "x"], ["addr", "q", "node"], ["store_field", "q", "p"], ["store_global", "q"]], []],
        [[], []],
        [[], ["buf"]],
        [[["return", "p"], ["assign", "p", "q"], ["addr", "q", "x"]], []],
        [[["addr", "p", "x"], ["assign", "q", "p"], ["assign", "r", "q"], ["send", "r"]], []],
        [[["addr", "p", "x"], ["addr", "p", "y"], ["addr", "q", "z"], ["call_iface", "p"], ["call", "q"]], []],
        [[["addr", "p", "x"], ["addr", "q", "buf"], ["store_field", "q", "p"]], ["buf"]],
        [[["addr", "a", "n1"], ["addr", "b", "n2"], ["addr", "c", "n3"], ["store_field", "a", "b"],
          ["store_field", "b", "c"], ["go", "a"]], []],
        [[["addr", "a", "n1"], ["addr", "b", "n2"], ["store_field", "a", "b"], ["load_field", "c", "a"], ["return", "c"]], []],
        [[["load_field", "c", "a"], ["return", "c"], ["store_field", "a", "b"], ["addr", "b", "n2"], ["addr", "a", "n1"]], []],
        [[["addr", "a", "n1"], ["addr", "b", "n2"], ["store_field", "a", "b"], ["store_field", "b", "a"], ["return", "b"]], []],
        [[["addr", "p", "x"], ["addr", "q", "y"], ["store_field", "q", "p"], ["call", "q"], ["return", "v"]], ["w"]],
        [[["addr", "p%d" % i, "x%d" % i] for i in range(30)] + [["assign", "p%d" % (i + 1), "p%d" % i] for i in range(29)]
         + [["return", "p29"]], []],
    ],
    examples=3,
    wrong_solutions=[
        '''def escaping(stmts, big):
    pts = {}; holds = {}
    for st in stmts:
        k = st[0]
        if k == "addr": pts.setdefault(st[1], set()).add(st[2])
        elif k == "assign": pts.setdefault(st[1], set()).update(pts.get(st[2], ()))
        elif k == "store_field":
            for t in pts.get(st[1], ()): holds.setdefault(t, set()).update(pts.get(st[2], ()))
        elif k == "load_field":
            for t in list(pts.get(st[2], ())): pts.setdefault(st[1], set()).update(holds.get(t, ()))
    esc = set(big)
    for st in stmts:
        if st[0] in ("return", "store_global", "send", "go", "call_iface"):
            esc |= pts.get(st[1], set())
    stack = list(esc)
    while stack:
        t = stack.pop()
        for u in holds.get(t, ()):
            if u not in esc:
                esc.add(u); stack.append(u)
    return sorted(esc)
''',
        '''def escaping(stmts, big):
    pts = {}; holds = {}
    changed = True
    while changed:
        changed = False
        for st in stmts:
            k = st[0]
            def grow(tb, key, items):
                cur = tb.setdefault(key, set()); n = len(cur); cur |= items; return len(cur) != n
            if k == "addr": changed |= grow(pts, st[1], {st[2]})
            elif k == "assign": changed |= grow(pts, st[1], set(pts.get(st[2], ())))
            elif k == "store_field":
                for t in list(pts.get(st[1], ())): changed |= grow(holds, t, set(pts.get(st[2], ())))
            elif k == "load_field":
                for t in list(pts.get(st[2], ())): changed |= grow(pts, st[1], set(holds.get(t, ())))
    esc = set(big)
    for st in stmts:
        if st[0] in ("return", "store_global", "send", "go", "call_iface", "call"):
            esc |= pts.get(st[1], set())
    return sorted(esc)
''',
        '''def escaping(stmts, big):
    pts = {}; holds = {}
    changed = True
    while changed:
        changed = False
        for st in stmts:
            k = st[0]
            def grow(tb, key, items):
                cur = tb.setdefault(key, set()); n = len(cur); cur |= items; return len(cur) != n
            if k == "addr": changed |= grow(pts, st[1], {st[2]})
            elif k == "assign": changed |= grow(pts, st[1], set(pts.get(st[2], ())))
            elif k == "store_field":
                for t in list(pts.get(st[1], ())): changed |= grow(holds, t, set(pts.get(st[2], ())))
            elif k == "load_field":
                for t in list(pts.get(st[2], ())): changed |= grow(pts, st[1], set(holds.get(t, ())))
    esc = set(big)
    for st in stmts:
        if st[0] in ("return", "store_global", "send", "go", "call_iface"):
            esc |= pts.get(st[1], set())
    return sorted(esc)
''',
    ],
    guide=dict(
        prereqs="Sets, graphs and reachability. Lesson: "
                "[Pointers, performance and the garbage collector](#/lesson/go/go-pointers-gc).",
        intuition="Escaping is reachability. Some places outlive the function (the caller, a global, a channel, "
                  "another goroutine). Anything those places can reach by following pointers must outlive the "
                  "function too. So: work out who may point to whom, mark the direct leaks, then follow `holds` edges.",
        hints=[
            "Build two tables: `pts[p]` (variables `p` may point to) and `holds[x]` (variables that `x`'s fields may point to).",
            "Statement order does not matter, so one pass is not enough. Loop until a full pass adds nothing.",
            "After marking the direct escapes, do a graph search over `holds` to pull in everything reachable.",
        ],
        brute_force="Processing the statements once, top to bottom, misses facts that are written 'later' in "
                    "the source (see the tests with reversed statement order). The fixpoint loop repairs that.",
        approach=r"""
1. **Points-to fixpoint.** Apply the four data-flow rules for every statement, again and again, until
   no set grows. Sets only grow and are bounded by the number of variables, so this terminates.
2. **Roots.** Start with `big`, add `pts[p]` for every leaking statement.
3. **Closure.** Depth-first search along `holds`.

**Dry run** of example 3: `pts[p]={x}`, `pts[q]={node}`, `holds[node]={x}`. Root: `store_global q` leaks `node`.
Closure: `node` holds `x`, so `x` escapes. Answer `["node", "x"]`.

**See the real compiler's decisions** with `go build -gcflags=-m`:

```go
package main

type node struct{ next *int }

var global *node

func leak() {
	x := 42       // moved to heap: x
	n := node{}   // moved to heap: n
	n.next = &x
	global = &n
}

func stay() int {
	y := 7
	p := &y // p does not leave the function: y stays on the stack
	return *p
}

func main() { leak(); _ = stay() }
```

```text
$ go build -gcflags=-m .
./main.go:8:2: moved to heap: x
./main.go:9:2: moved to heap: n
```
""",
        complexity="With V variables and S statements each pass is O(S·V) and there are at most O(V²) growth "
                   "steps, so the fixpoint is polynomial; tiny for function-sized inputs.",
        pitfalls="A single pass. Counting `call` as an escape. Forgetting the transitive `holds` step. "
                 "Forgetting that `big` variables drag along whatever they hold.",
        follow_up="The real compiler is smarter: it tracks whether callees leak their parameters, and inlining "
                  "changes the answer. Try `-gcflags='-m -m'` for the reasoning.",
    ),
),
]
