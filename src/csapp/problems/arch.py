def _y86_sum_prog():
    return [
        "irmovq $8, %r8",
        "irmovq $1, %r9",
        "xorq %rax, %rax",
        "andq %rsi, %rsi",
        "jmp test",
        "loop:",
        "mrmovq (%rdi), %r10",
        "addq %r10, %rax",
        "addq %r8, %rdi",
        "subq %r9, %rsi",
        "test:",
        "jne loop",
        "halt",
    ]


_Y86_SOLUTION = r'''def run_y86(program, mem):
    MASK = (1 << 64) - 1

    def signed(v):
        v &= MASK
        return v - (1 << 64) if v >> 63 else v

    labels, code = {}, []
    for line in program:
        line = line.strip()
        if line.endswith(":"):
            labels[line[:-1]] = len(code)
        else:
            code.append(line)
    R = collections.defaultdict(int)
    M = {a: signed(v) for a, v in mem}
    ZF, SF, OF = 1, 0, 0
    pc = steps = 0

    def reg(tok):
        return tok.strip().lstrip("%")

    def memop(tok):
        tok = tok.strip()
        d, r = tok.split("(")
        return (int(d) if d else 0), reg(r.rstrip(")"))

    def cond(op):
        if op == "jmp":
            return True
        return {"jle": (SF ^ OF) | ZF, "jl": SF ^ OF, "je": ZF, "jne": 1 - ZF,
                "jge": 1 - (SF ^ OF), "jg": (1 - (SF ^ OF)) & (1 - ZF)}[op] == 1

    while 0 <= pc < len(code) and steps < 100000:
        line = code[pc]
        steps += 1
        parts = line.split(None, 1)
        op = parts[0]
        args = [a.strip() for a in parts[1].split(",")] if len(parts) > 1 else []
        nxt = pc + 1
        if op == "halt":
            break
        elif op == "nop":
            pass
        elif op == "irmovq":
            R[reg(args[1])] = signed(int(args[0].lstrip("$")))
        elif op == "rrmovq":
            R[reg(args[1])] = R[reg(args[0])]
        elif op == "mrmovq":
            d, rb = memop(args[0])
            R[reg(args[1])] = M.get(R[rb] + d, 0)
        elif op == "rmmovq":
            d, rb = memop(args[1])
            M[R[rb] + d] = R[reg(args[0])]
        elif op in ("addq", "subq", "andq", "xorq"):
            a, b = R[reg(args[0])], R[reg(args[1])]
            if op == "addq":
                t = signed(b + a)
                OF = int((a < 0) == (b < 0) and (t < 0) != (a < 0))
            elif op == "subq":
                t = signed(b - a)
                OF = int((a < 0) != (b < 0) and (t < 0) != (b < 0))
            elif op == "andq":
                t, OF = b & a, 0
            else:
                t, OF = b ^ a, 0
            t = signed(t)
            ZF, SF = int(t == 0), int(t < 0)
            R[reg(args[1])] = t
        elif op in ("jmp", "jle", "jl", "je", "jne", "jge", "jg"):
            if cond(op):
                nxt = labels[args[0]]
        elif op == "pushq":
            v = R[reg(args[0])]
            R["rsp"] = signed(R["rsp"] - 8)
            M[R["rsp"]] = v
        elif op == "popq":
            v = M.get(R["rsp"], 0)
            R["rsp"] = signed(R["rsp"] + 8)
            R[reg(args[0])] = v
        elif op == "call":
            R["rsp"] = signed(R["rsp"] - 8)
            M[R["rsp"]] = pc + 1
            nxt = labels[args[0]]
        elif op == "ret":
            nxt = M.get(R["rsp"], 0)
            R["rsp"] = signed(R["rsp"] + 8)
        pc = nxt
    return [R["rax"], steps]
'''

PROBLEMS = [
dict(
    id="csapp-amdahl",
    title="Amdahl's Law",
    difficulty="Easy",
    pattern="Performance",
    entry="speedup",
    compare="float",
    description=r"""
Generalized Amdahl's law. A program's running time is split into parts. You are given a list
`parts` of `[fraction, k]` pairs: `fraction` is the share of the **original** running time spent in
that part and `k > 0` is the factor by which that part is sped up. The fractions sum to at most 1;
whatever remains is not improved. Return the overall speedup

$$S = \frac{T_{old}}{T_{new}} = \frac{1}{(1 - \sum_i \alpha_i) + \sum_i \alpha_i / k_i}$$

**Example:** `[[0.6, 3]]` → `1.6667` (the book's example)

**Example:** `[[0.5, 2], [0.25, 5]]` → `1 / (0.25 + 0.25 + 0.05) = 1.8182`
""",
    starter='''def speedup(parts: List[List[float]]) -> float:
    pass
''',
    solution='''def speedup(parts):
    rest = 1.0 - sum(a for a, _ in parts)
    return 1.0 / (rest + sum(a / k for a, k in parts))
''',
    tests=[[[[0.6, 3]]], [[[0.5, 2], [0.25, 5]]], [[]], [[[0.9, 6.0]]], [[[1.0, 4]]], [[[0.6, 1e12]]],
           [[[0.0, 100]]], [[[0.5, 1]]], [[[0.2, 0.5]]], [[[0.1, 2], [0.2, 3], [0.3, 4], [0.4, 5]]],
           [[[0.99, 1000]]]],
    wrong_solutions=['''def speedup(parts):
    return 1.0 / sum(a / k for a, k in parts) if parts else 1.0
''', '''def speedup(parts):
    return sum(a * k for a, k in parts) + (1 - sum(a for a, _ in parts))
'''],
    guide=dict(
        prereqs="Lesson *Caches, the OS, and the big themes* (Amdahl's law).",
        intuition="New time = unimproved share + each improved share divided by its factor. Speedup is old time (1) over new time.",
        hints=["Normalize the old time to 1.", "The unimproved share is `1 - sum(fractions)`.", "Return `1 / (rest + sum(a/k))`."],
        brute_force="There is only the formula; a 'brute force' check is to pick T_old = 100 and compute actual times.",
        approach="Compute `rest`, add `a/k` for each part, invert. Dry run `[[0.6,3]]`: rest 0.4, improved 0.2, total 0.6, S = 1.667.",
        complexity="O(n) for n parts.",
        pitfalls="- Weighting speedups by fraction (`sum(a*k)`) is the classic mistake: time adds, speedups do not.\n- `k < 1` is a slowdown and is legal.\n- Empty list → speedup 1.",
        follow_up="Invert the law: given a target S and alpha, find k (and detect when it is impossible because S > 1/(1-alpha)).",
    ),
),
dict(
    id="csapp-struct-layout",
    title="Struct Layout and Alignment",
    difficulty="Medium",
    pattern="Machine-Level Data",
    entry="struct_layout",
    description=r"""
Compute how an x86-64 C compiler lays out a `struct`.

`fields` is a list of type strings in declaration order. Scalar types and their sizes (= alignments):
`char` 1, `short` 2, `int` 4, `float` 4, `long` 8, `double` 8, `ptr` 8. A field may also be an array
written like `"int[3]"`: its size is `n × element size`, its alignment is the element's alignment.

Rules: each field is placed at the lowest offset `>=` the current end that is a multiple of its
alignment; the struct's alignment is the maximum field alignment (1 if empty); the total size is rounded
up to a multiple of the struct's alignment.

Return `[offsets, size, alignment]`.

**Example:** `["int", "char", "int"]` → `[[0, 4, 8], 12, 4]`

**Example:** `["char", "double", "char"]` → `[[0, 8, 16], 24, 8]`
""",
    starter='''def struct_layout(fields: List[str]) -> list:
    pass
''',
    solution='''def struct_layout(fields):
    sizes = {"char": 1, "short": 2, "int": 4, "float": 4, "long": 8, "double": 8, "ptr": 8}
    off, maxa, offsets = 0, 1, []
    for f in fields:
        n = 1
        if "[" in f:
            f, cnt = f.split("[")
            n = int(cnt.rstrip("]"))
        k = sizes[f]
        off = (off + k - 1) // k * k
        offsets.append(off)
        off += k * n
        maxa = max(maxa, k)
    size = (off + maxa - 1) // maxa * maxa
    return [offsets, size, maxa]
''',
    tests=[[["int", "char", "int"]], [["char", "double", "char"]], [[]], [["char"]], [["int", "int", "char"]],
           [["ptr", "short", "double", "char", "float", "char", "long", "int"]],
           [["ptr", "double", "long", "float", "int", "short", "char", "char"]],
           [["char", "short", "char", "int"]], [["char[3]", "short"]], [["int[2]", "ptr"]],
           [["char", "int[3]", "char", "double[2]", "short"]], [["short", "char"]], [["char[5]"]],
           [["double", "char[9]"]]],
    wrong_solutions=['''def struct_layout(fields):
    sizes = {"char": 1, "short": 2, "int": 4, "float": 4, "long": 8, "double": 8, "ptr": 8}
    off, maxa, offsets = 0, 1, []
    for f in fields:
        n = 1
        if "[" in f:
            f, cnt = f.split("[")
            n = int(cnt.rstrip("]"))
        k = sizes[f]
        off = (off + k - 1) // k * k
        offsets.append(off)
        off += k * n
        maxa = max(maxa, k)
    return [offsets, off, maxa]
''', '''def struct_layout(fields):
    sizes = {"char": 1, "short": 2, "int": 4, "float": 4, "long": 8, "double": 8, "ptr": 8}
    off, maxa, offsets = 0, 1, []
    for f in fields:
        n = 1
        if "[" in f:
            f, cnt = f.split("[")
            n = int(cnt.rstrip("]"))
        k = sizes[f] * n
        off = (off + k - 1) // k * k
        offsets.append(off)
        off += k
        maxa = max(maxa, k)
    size = (off + maxa - 1) // maxa * maxa
    return [offsets, size, maxa]
'''],
    guide=dict(
        prereqs="Lesson *Arrays, structs, alignment and buffer overflows*, section on data alignment.",
        intuition="Walk the fields keeping a running offset. Before placing a field, round the offset up to the field's alignment. At the end, round the size up to the largest alignment so arrays of the struct stay aligned.",
        hints=["Rounding `x` up to a multiple of `k`: `(x + k - 1) // k * k`.", "An array aligns like its element, not like its total size.", "Do not forget trailing padding."],
        brute_force="Simulate byte by byte: advance the offset one byte at a time until it is divisible by the alignment. O(total size).",
        approach="For each field: parse optional `[n]`, look up element size k, align, record offset, advance by `k*n`, track max alignment. Finally round up. Dry run `char,double,char`: 0; align to 8 → 8; 16; end 17 → round to 24.",
        complexity="O(number of fields).",
        pitfalls="- Missing trailing padding (`int,int,char` is 12, not 9).\n- Aligning `char[3]` to 3 bytes or `int[3]` to 12.\n- Empty struct: size 0, alignment 1.",
        follow_up="Find the field order that minimizes size (sort by decreasing alignment) and report the bytes saved.",
    ),
),
dict(
    id="csapp-y86-interpreter",
    title="Y86-64 Interpreter",
    difficulty="Hard",
    pattern="Processor Architecture",
    entry="run_y86",
    description=r"""
Write an interpreter for a subset of Y86-64 assembly.

`program` is a list of lines. A line is either a label `name:` or one instruction:

| Instruction | Effect |
|---|---|
| `irmovq $V, %rB` | `rB = V` (V is a decimal integer, possibly negative) |
| `rrmovq %rA, %rB` | `rB = rA` |
| `mrmovq D(%rB), %rA` | `rA = M[rB + D]` (D is an optional decimal displacement) |
| `rmmovq %rA, D(%rB)` | `M[rB + D] = rA` |
| `addq/subq/andq/xorq %rA, %rB` | `rB = rB OP rA`, sets ZF, SF, OF |
| `jmp/jle/jl/je/jne/jge/jg label` | jump (conditionally, on the condition codes) |
| `pushq %rA` | `rsp -= 8; M[rsp] = rA` (pushes the old value if rA is `%rsp`) |
| `popq %rA` | `rA = M[rsp]; rsp += 8` |
| `call label` | push the index of the next instruction, jump |
| `ret` | pop an instruction index and jump to it |
| `nop`, `halt` | |

Details:
- Registers hold 64-bit two's-complement values (wrap on overflow) and start at 0.
- Memory is a map from address to an 8-byte word; `mem` gives its initial contents as `[address, value]` pairs. Unwritten words read as 0.
- The "address" of an instruction is its index among the instructions (labels do not count). Execution starts at instruction 0.
- Condition codes start as `ZF=1, SF=0, OF=0` and are changed only by the four `OPq` instructions. `andq`/`xorq` clear `OF`. Conditions: `jle: (SF^OF)|ZF`, `jl: SF^OF`, `je: ZF`, `jne: ~ZF`, `jge: ~(SF^OF)`, `jg: ~(SF^OF)&~ZF`.
- Execution stops at `halt` (which counts as an executed instruction) or when the PC runs past the last instruction. All test programs finish in far fewer than 100,000 steps; stop there as a safety net against infinite loops.

Return `[rax, steps]`: the signed value of `%rax` and the number of instructions executed.

**Example:** the array-sum program from the lesson with `%rdi`/`%rsi` loaded first returns the sum.
""",
    starter='''def run_y86(program: List[str], mem: List[List[int]]) -> List[int]:
    pass
''',
    solution=_Y86_SOLUTION,
    tests=[
        [["irmovq $5, %rax", "irmovq $7, %rbx", "addq %rbx, %rax", "halt"], []],
        [["irmovq $256, %rdi", "irmovq $4, %rsi"] + _y86_sum_prog(), [[256, 10], [264, 20], [272, 30], [280, -5]]],
        [["irmovq $256, %rdi", "irmovq $0, %rsi"] + _y86_sum_prog(), [[256, 10]]],
        [["irmovq $10, %rcx", "irmovq $1, %rdx", "loop:", "addq %rcx, %rax", "subq %rdx, %rcx", "jg loop", "halt"], []],
        [["irmovq $4096, %rsp", "irmovq $6, %rdi", "call square", "halt",
          "square:", "rrmovq %rdi, %rcx", "irmovq $1, %rdx", "xorq %rax, %rax",
          "sq_loop:", "addq %rdi, %rax", "subq %rdx, %rcx", "jne sq_loop", "ret"], []],
        [["irmovq $4096, %rsp", "irmovq $3, %rax", "irmovq $9, %rbx", "pushq %rax", "pushq %rbx",
          "popq %rax", "popq %rbx", "subq %rbx, %rax", "halt"], []],
        [["irmovq $-9223372036854775808, %rax", "irmovq $1, %rbx", "subq %rbx, %rax", "jl less",
          "irmovq $0, %rax", "halt", "less:", "irmovq $1, %rax", "halt"], []],
        [["irmovq $9223372036854775807, %rax", "irmovq $1, %rbx", "addq %rbx, %rax", "halt"], []],
        [["irmovq $5, %rax", "irmovq $5, %rbx", "subq %rax, %rbx", "je same", "irmovq $111, %rax", "halt",
          "same:", "irmovq $222, %rax"], []],
        [["irmovq $100, %rbx", "irmovq $42, %rcx", "rmmovq %rcx, 16(%rbx)", "mrmovq 16(%rbx), %rax",
          "mrmovq 24(%rbx), %rdx", "addq %rdx, %rax", "nop", "halt"], [[124, 8]]],
        [["jle start", "irmovq $99, %rax", "halt", "start:", "irmovq $12, %rax", "irmovq $10, %rbx",
          "andq %rbx, %rax", "jge done", "irmovq $-1, %rax", "done:", "halt"], []],
        [["irmovq $4096, %rsp", "pushq %rsp", "popq %rax", "halt"], []],
        [["irmovq $4096, %rsp", "irmovq $5, %rdi", "call fact", "halt",
          "fact:", "irmovq $1, %rax", "irmovq $1, %r8", "f_loop:", "andq %rdi, %rdi", "je f_done",
          "rrmovq %rax, %rcx", "rrmovq %rdi, %rdx", "xorq %rax, %rax",
          "m_loop:", "addq %rcx, %rax", "subq %r8, %rdx", "jne m_loop",
          "subq %r8, %rdi", "jmp f_loop", "f_done:", "ret"], []],
        [["irmovq $-3, %rax", "irmovq $5, %rbx", "xorq %rbx, %rax", "jl neg", "halt", "neg:", "irmovq $7, %rcx",
          "addq %rcx, %rax", "halt"], []],
    ],
    examples=2,
    wrong_solutions=[
        _Y86_SOLUTION.replace('"jl": SF ^ OF,', '"jl": SF,').replace('"jle": (SF ^ OF) | ZF', '"jle": SF | ZF'),
        _Y86_SOLUTION.replace("t = signed(b - a)", "t = signed(a - b)"),
        _Y86_SOLUTION.replace("ZF, SF, OF = 1, 0, 0", "ZF, SF, OF = 0, 0, 0"),
    ],
    guide=dict(
        prereqs="Lessons *The Y86-64 ISA and logic design* and *SEQ*; condition codes from Module 3.",
        intuition="An interpreter is the fetch–decode–execute loop in software: keep a PC, a register map, a memory map and three flags; decode each line and update the state exactly as the ISA says.",
        hints=["First pass: strip labels and record `label -> instruction index`.",
               "Wrap every register write to 64-bit signed. For `subq rA, rB` the result is `rB - rA`.",
               "Overflow: add overflows when both operands share a sign that differs from the result's; `b - a` overflows when `a` and `b` have different signs and the result's sign differs from `b`'s."],
        brute_force="No shortcut exists: you must simulate. A simpler first version can ignore OF and the stack, then add them.",
        approach="1. Preprocess labels.\n2. Loop while `0 <= pc < len(code)`: count a step, split the mnemonic from comma-separated operands.\n3. Implement each instruction; for jumps evaluate the condition from ZF/SF/OF.\n4. `call` pushes `pc+1`; `ret` pops the PC.\n5. Return `[R['rax'], steps]`.\n\nDry run of `irmovq $5,%rax; irmovq $7,%rbx; addq %rbx,%rax; halt`: rax = 12 after 4 steps.",
        complexity="O(number of executed instructions); each step is O(1) apart from string parsing (pre-parse to speed up).",
        pitfalls="- Operand order of `subq` (it is `rB - rA`).\n- Using SF alone for `jl`: wrong when the subtraction overflows (TMin - 1).\n- Initial ZF is 1, so a `jle`/`je` before any arithmetic is taken.\n- `pushq %rsp` pushes the old stack pointer.\n- Displacement may be omitted: `(%rdi)`.",
        follow_up="Add `cmovXX`, byte-accurate instruction addresses and encodings, and the status codes ADR/INS.",
    ),
),
dict(
    id="csapp-pipeline-penalties",
    title="Pipeline Cycle Count",
    difficulty="Medium",
    pattern="Processor Architecture",
    entry="pipeline_cycles",
    description=r"""
Count how many clock cycles the five-stage PIPE processor (fetch, decode, execute, memory,
write back, **with forwarding**) needs to run a dynamic instruction trace.

Each trace entry is `[kind, dst, srcs]`:

- `kind` is one of `"op"` (ALU instruction), `"load"` (`mrmovq`/`popq`), `"store"`, `"jmp_ok"`
  (correctly predicted jump), `"jmp_miss"` (mispredicted jump) or `"ret"`;
- `dst` is the register written (or `""` if none);
- `srcs` is the list of registers read.

Bubbles are inserted as in the lesson:

- **Load/use hazard:** if an instruction reads the `dst` of the *immediately preceding* `load`: 1 bubble.
- **Mispredicted jump:** 2 bubbles after it.
- **`ret`:** 3 bubbles after it.

All other dependencies are handled by forwarding at no cost. With `n` instructions and `b` bubbles the
run takes `n + 4 + b` cycles (the last instruction needs 4 more cycles to drain), or 0 cycles if the
trace is empty. Return `[cycles, bubbles]`.

**Example:** `[["load","rax",["rdx"]], ["op","rbx",["rax","rbx"]]]` → `[7, 1]`
""",
    starter='''def pipeline_cycles(trace: List[list]) -> List[int]:
    pass
''',
    solution='''def pipeline_cycles(trace):
    if not trace:
        return [0, 0]
    bubbles = 0
    prev = None
    for kind, dst, srcs in trace:
        if prev and prev[0] == "load" and prev[1] and prev[1] in srcs:
            bubbles += 1
        if kind == "jmp_miss":
            bubbles += 2
        elif kind == "ret":
            bubbles += 3
        prev = (kind, dst)
    return [len(trace) + 4 + bubbles, bubbles]
''',
    tests=[
        [[["load", "rax", ["rdx"]], ["op", "rbx", ["rax", "rbx"]]]],
        [[]],
        [[["op", "rax", []]]],
        [[["op", "rdx", []], ["op", "rax", []], ["op", "rax", ["rdx", "rax"]]]],
        [[["load", "rax", ["rdx"]], ["op", "rcx", ["rcx"]], ["op", "rbx", ["rax", "rbx"]]]],
        [[["op", "rax", ["rax"]], ["jmp_miss", "", []], ["op", "rax", ["rax"]]]],
        [[["load", "rsp", ["rbx"]], ["ret", "rsp", ["rsp"]]]],
        [[["ret", "rsp", ["rsp"]], ["ret", "rsp", ["rsp"]]]],
        [[["load", "rax", ["rax"]], ["load", "rax", ["rax"]], ["load", "rax", ["rax"]]]],
        [[["load", "rax", ["rdi"]], ["store", "", ["rax", "rsi"]], ["jmp_ok", "", []], ["jmp_miss", "", []]]],
        [[["op", "rax", ["rdx"]], ["op", "rbx", ["rax"]]] * 50],
        [[["load", "r10", ["rdi"]], ["op", "rax", ["r10", "rax"]], ["op", "rdi", ["r8", "rdi"]],
          ["op", "rsi", ["r9", "rsi"]], ["jmp_ok", "", []]] * 100 + [["jmp_miss", "", []], ["ret", "rsp", ["rsp"]]]],
        [[["store", "", ["rax"]], ["load", "", ["rbx"]], ["op", "rax", [""]]]],
    ],
    wrong_solutions=['''def pipeline_cycles(trace):
    if not trace:
        return [0, 0]
    bubbles = 0
    written = set()
    for kind, dst, srcs in trace:
        if any(s in written for s in srcs):
            bubbles += 1
        written = {dst} if dst else set()
        if kind == "jmp_miss":
            bubbles += 2
        elif kind == "ret":
            bubbles += 3
    return [len(trace) + 4 + bubbles, bubbles]
''', '''def pipeline_cycles(trace):
    bubbles = 0
    prev = None
    for kind, dst, srcs in trace:
        if prev and prev[0] == "load" and prev[1] and prev[1] in srcs:
            bubbles += 1
        if kind in ("jmp_miss", "ret"):
            bubbles += 2
        prev = (kind, dst)
    return [len(trace) + 4 + bubbles, bubbles]
'''],
    guide=dict(
        prereqs="Lesson *Pipelining, hazards and forwarding*.",
        intuition="With forwarding, only three events cost cycles: load immediately followed by a use (1), mispredicted branch (2), ret (3). Everything else flows at one instruction per cycle after the 4-cycle fill.",
        hints=["Only the *previous* instruction matters for load/use.", "An `op` followed by a dependent `op` costs nothing thanks to forwarding.", "Total = n + 4 + bubbles; empty trace is 0."],
        brute_force="Simulate the five pipeline registers cycle by cycle with stall/bubble control logic. Correct but far more code.",
        approach="Scan once, remembering the previous (kind, dst). Add 1 if prev is a load whose dst is among the current srcs; add 2 for `jmp_miss`, 3 for `ret`. Dry run on the example: n=2, bubbles=1, cycles 7.",
        complexity="O(n) time, O(1) space.",
        pitfalls="- Charging a bubble for op→op dependencies (forwarding handles them).\n- Charging load/use when one instruction intervenes (forwarding from W suffices).\n- A load with no destination (`\"\"`) must not match an empty source name.",
        follow_up="Compute CPI = cycles-per-instruction in the limit (1 + bubbles/n) and compare with the book's 1.27 estimate.",
    ),
),
dict(
    id="csapp-critical-path",
    title="Loop Critical Path (Data-Flow Scheduling)",
    difficulty="Medium",
    pattern="Program Optimization",
    entry="loop_cycles",
    description=r"""
Model an out-of-order processor with **unlimited functional units**: every operation starts as soon as
all of its inputs are ready and takes `latency` cycles.

A loop body is a list `ops` of `[dst, latency, srcs]`: the operation reads the registers in `srcs` and
writes register `dst`. Operations appear in program order; a read sees the most recent earlier write to
that register (from this iteration, or from a previous iteration, or the initial value which is ready
at time 0). Registers that are never written are always ready at time 0.

The body is executed `n` times. Return the time at which the last operation finishes (the maximum
finish time over all operations), i.e. the length of the critical path. `n = 0` → `0`.

For `combine4` with double multiplication the body is
`[["t",4,["p"]], ["acc",5,["acc","t"]], ["p",1,["p"]]]` (load, mul, pointer add):
the multiply chain dominates, so 1000 iterations take about 5000 cycles (CPE 5).

**Example:** `ops = [["acc",5,["acc","t"]]], n = 3` → `15`
""",
    starter='''def loop_cycles(ops: List[list], n: int) -> int:
    pass
''',
    solution='''def loop_cycles(ops, n):
    ready = {}
    finish = 0
    for _ in range(n):
        for dst, lat, srcs in ops:
            t = lat
            for s in srcs:
                t = max(t, ready.get(s, 0) + lat)
            ready[dst] = t
            if t > finish:
                finish = t
    return finish
''',
    tests=[
        [[["acc", 5, ["acc", "t"]]], 3],
        [[["t", 4, ["p"]], ["acc", 5, ["acc", "t"]], ["p", 1, ["p"]]], 1000],
        [[["t", 4, ["p"]], ["acc", 5, ["acc", "t"]], ["p", 1, ["p"]]], 0],
        [[["t0", 4, ["p"]], ["acc0", 5, ["acc0", "t0"]], ["t1", 4, ["p"]], ["acc1", 5, ["acc1", "t1"]], ["p", 1, ["p"]]], 500],
        [[["t0", 4, ["p"]], ["acc", 5, ["acc", "t0"]], ["t1", 4, ["p"]], ["acc", 5, ["acc", "t1"]], ["p", 1, ["p"]]], 500],
        [[["t0", 4, ["p"]], ["t1", 4, ["p"]], ["u", 5, ["t0", "t1"]], ["acc", 5, ["acc", "u"]], ["p", 1, ["p"]]], 500],
        [[["ls", 4, ["ls"]], ["len", 1, ["len"]]], 100],
        [[["x", 3, []]], 10],
        [[["a", 1, ["b"]], ["b", 1, ["a"]]], 50],
        [[["sum", 1, ["sum", "v"]]], 1],
        [[["v", 4, ["dst"]], ["w", 1, ["v"]], ["dst", 0, ["dst"]]], 20],
        [[["m", 4, ["src"]], ["val", 1, ["m"]], ["src", 3, ["val"]]], 200],
    ],
    wrong_solutions=['''def loop_cycles(ops, n):
    return n * sum(lat for _, lat, _ in ops)
''', '''def loop_cycles(ops, n):
    return n * max((lat for _, lat, _ in ops), default=0)
'''],
    guide=dict(
        prereqs="Lesson *Instruction-level parallelism and unrolling* (data-flow graphs, latency bound).",
        intuition="Track, for each register, the time its current value becomes available. An operation finishes at `max(ready of its inputs) + latency`. Loop-carried registers form chains whose length grows with the iteration count; the longest chain is the critical path.",
        hints=["Keep a dict `ready[reg]`.", "Process operations in program order, iteration by iteration, updating `ready[dst]`.", "The answer is the max finish time ever seen, not necessarily that of the last operation."],
        brute_force="Build the full data-flow DAG for all n iterations and run a longest-path computation: same O(n·|ops|) cost, more memory.",
        approach="Simulate directly: for each iteration, for each op compute `t = max(ready[s]) + lat`, store it. Dry run: one multiply (lat 5) on `acc`, 3 iterations → 5, 10, 15.",
        complexity="O(n · total number of sources).",
        pitfalls="- Summing all latencies (assumes no parallelism) or taking only the max latency (ignores chains through several ops).\n- Two operations per iteration on the *same* accumulator double the chain (2×1 unrolling does not help); separate accumulators or reassociation do.",
        follow_up="Add a limit on the number of functional units per operation type to model the throughput bound.",
    ),
),
dict(
    id="csapp-direct-mapped-cache",
    title="Direct-Mapped Cache Simulator",
    difficulty="Medium",
    pattern="Caches",
    entry="direct_mapped",
    description=r"""
Simulate a **direct-mapped** cache with $S = 2^s$ sets (one line each) and $B = 2^b$-byte blocks.

Given `s`, `b` and a `trace` of byte addresses (nonnegative ints, each access touches one byte),
return `[hits, misses]`. The cache starts empty (all valid bits 0).

An address is split as `tag | set index (s bits) | block offset (b bits)`.

**Example:** `s = 2, b = 1, trace = [0, 1, 13, 8, 0]` → `[1, 4]` (the lesson's worked example)
""",
    starter='''def direct_mapped(s: int, b: int, trace: List[int]) -> List[int]:
    pass
''',
    solution='''def direct_mapped(s, b, trace):
    lines = [None] * (1 << s)
    hits = misses = 0
    mask = (1 << s) - 1
    for a in trace:
        idx = (a >> b) & mask
        tag = a >> (s + b)
        if lines[idx] == tag:
            hits += 1
        else:
            misses += 1
            lines[idx] = tag
    return [hits, misses]
''',
    tests=[
        [2, 1, [0, 1, 13, 8, 0]],
        [2, 1, []],
        [0, 0, [5, 5, 6, 5]],
        [4, 4, list(range(0, 64 * 4, 4))],
        [1, 4, [0, 32, 4, 36, 8, 40, 12, 44, 16, 48, 20, 52, 24, 56, 28, 60]],
        [1, 4, [0, 48, 4, 52, 8, 56, 12, 60, 16, 64, 20, 68, 24, 72, 28, 76]],
        [3, 2, [0, 32, 0, 32, 0, 32]],
        [10, 6, [i * 64 for i in range(2048)] * 2],
        [10, 6, [i * 8 for i in range(4096)]],
        [5, 3, [(i * 7919) % 5000 for i in range(20000)]],
        [0, 3, [0, 7, 8, 15, 16, 0]],
        [6, 6, [0x7ffe4c3a1238, 0x7ffe4c3a1240, 0x7ffe4c3a1238, 0x601040, 0x601048]],
    ],
    wrong_solutions=['''def direct_mapped(s, b, trace):
    lines = [None] * (1 << s)
    hits = misses = 0
    for a in trace:
        idx = a & ((1 << s) - 1)
        tag = a >> s
        if lines[idx] == tag:
            hits += 1
        else:
            misses += 1
            lines[idx] = tag
    return [hits, misses]
''', '''def direct_mapped(s, b, trace):
    seen = set()
    hits = misses = 0
    for a in trace:
        blk = a >> b
        if blk in seen:
            hits += 1
        else:
            misses += 1
            seen.add(blk)
    return [hits, misses]
'''],
    guide=dict(
        prereqs="Lesson *Cache memories* (address partitioning, direct-mapped caches).",
        intuition="Each set holds at most one block. Compute the set index and tag for every address: a hit happens iff that set currently stores the same tag; otherwise it is a miss and the line is replaced.",
        hints=["Drop the b offset bits first: `block = addr >> b`.", "`index = block & (2^s - 1)`, `tag = block >> s`.", "Store one tag (or None) per set."],
        brute_force="Keep a dict from set index to the full block number: equivalent.",
        approach="Array of tags, one per set. For each address compute (idx, tag); compare; update. Dry run of the example gives miss, hit, miss, miss, miss.",
        complexity="O(len(trace)) time, O(S) space.",
        pitfalls="- Forgetting to strip the block offset (two bytes in the same block must hit).\n- Modeling an *infinite* cache (a set of seen blocks) misses the evictions and conflict misses.\n- `s = 0` means one set: the mask is 0.",
        follow_up="Classify each miss as cold, conflict or capacity by comparing with a fully associative LRU cache of the same size.",
    ),
),
dict(
    id="csapp-set-assoc-lru",
    title="Set-Associative Cache with LRU",
    difficulty="Medium",
    pattern="Caches",
    entry="cache_sim",
    description=r"""
The heart of CS:APP's *cache lab*. Simulate a cache with $S = 2^s$ sets, `E` lines per set and
$B = 2^b$-byte blocks, using **LRU** (least recently used) replacement.

For each byte address in `trace`:
- **hit** if a valid line in the selected set has the matching tag;
- otherwise a **miss**: load the block into an empty line if there is one, else **evict** the least
  recently used line of that set (count an eviction).

Both hits and loads make the line the most recently used. Return `[hits, misses, evictions]`.

**Example:** `s = 0, E = 4, b = 1, trace = [0, 1, 13, 8, 0]` → `[2, 3, 0]`

**Example:** `s = 0, E = 2, b = 0, trace = [1, 2, 3, 1]` → `[0, 4, 2]`
""",
    starter='''def cache_sim(s: int, E: int, b: int, trace: List[int]) -> List[int]:
    pass
''',
    solution='''def cache_sim(s, E, b, trace):
    sets = [collections.OrderedDict() for _ in range(1 << s)]
    hits = misses = evictions = 0
    mask = (1 << s) - 1
    for a in trace:
        line = sets[(a >> b) & mask]
        tag = a >> (s + b)
        if tag in line:
            hits += 1
            line.move_to_end(tag)
        else:
            misses += 1
            if len(line) == E:
                line.popitem(last=False)
                evictions += 1
            line[tag] = True
    return [hits, misses, evictions]
''',
    tests=[
        [1, 2, 1, [0, 1, 13, 8, 0]],
        [0, 2, 0, [1, 2, 3, 1]],
        [0, 2, 0, [1, 2, 1, 3, 1, 2]],
        [2, 1, 1, [0, 1, 13, 8, 0]],
        [0, 4, 1, [0, 1, 13, 8, 0]],
        [0, 1, 0, []],
        [1, 2, 4, [0, 32, 4, 36, 8, 40, 64, 0, 32]],
        [0, 3, 0, [1, 2, 3, 1, 4, 2, 1, 3, 5, 1]],
        [4, 1, 4, [0x10, 0x20, 0x22, 0x18, 0x110, 0x210, 0x12]],
        [6, 8, 6, [i * 64 for i in range(1024)] * 2],
        [3, 2, 3, [(i * 7919) % 3000 for i in range(20000)]],
        [2, 4, 2, [(i * i) % 997 for i in range(5000)]],
    ],
    wrong_solutions=['''def cache_sim(s, E, b, trace):
    sets = [collections.OrderedDict() for _ in range(1 << s)]
    hits = misses = evictions = 0
    mask = (1 << s) - 1
    for a in trace:
        line = sets[(a >> b) & mask]
        tag = a >> (s + b)
        if tag in line:
            hits += 1
        else:
            misses += 1
            if len(line) == E:
                line.popitem(last=False)
                evictions += 1
            line[tag] = True
    return [hits, misses, evictions]
''', '''def cache_sim(s, E, b, trace):
    sets = [collections.OrderedDict() for _ in range(1 << s)]
    hits = misses = evictions = 0
    mask = (1 << s) - 1
    for a in trace:
        line = sets[(a >> b) & mask]
        tag = a >> (s + b)
        if tag in line:
            hits += 1
            line.move_to_end(tag)
        else:
            misses += 1
            if len(line) == E:
                line.popitem(last=True)
                evictions += 1
            line[tag] = True
    return [hits, misses, evictions]
'''],
    guide=dict(
        prereqs="Lesson *Cache memories* (set associative caches, replacement policies). Related: LeetCode 146 LRU Cache.",
        intuition="Each set is a tiny LRU cache of capacity E keyed by tag. An ordered map (or a per-line timestamp) tracks recency.",
        hints=["Compute set index and tag exactly as in the direct-mapped problem.", "On a hit you must refresh recency, otherwise you have FIFO, not LRU.", "`collections.OrderedDict` gives `move_to_end` and `popitem(last=False)`."],
        brute_force="Store for every line a 'last used' counter and scan the set's E lines for a match or for the minimum counter: O(E) per access, which is how the C cache lab is usually written.",
        approach="For each address: pick the set; if the tag is present → hit, move to MRU position; else miss, evict the LRU entry if the set is full, insert. Dry run `[1,2,1,3,1,2]`, E=2, one set: M, M, H, M (evict 2), H, M (evict 3) → `[2,4,2]`.",
        complexity="O(1) per access with an ordered map; O(S·E) space.",
        pitfalls="- Not updating recency on hits (FIFO).\n- Evicting the most recently used entry.\n- Counting an eviction when an empty line was available.",
        follow_up="Add `L`/`S`/`M` operations as in the cache lab (M = load then store: a second guaranteed hit), or implement LFU.",
    ),
),
dict(
    id="csapp-symbol-resolution",
    title="Linker Symbol Resolution",
    difficulty="Medium",
    pattern="Linking",
    entry="resolve",
    description=r"""
Apply the Linux linker's rules for global symbols.

`modules` is a list of modules; each module is a list of `[name, kind]` where `kind` is `"strong"`
(a function or initialized global definition), `"weak"` (an uninitialized global definition) or
`"ref"` (a reference to a symbol defined elsewhere).

Rules:
1. Multiple strong definitions of the same name are an error.
2. Given a strong and weak definitions, the strong one is chosen.
3. Given only weak definitions, any may be chosen: **choose the one in the lowest-numbered module**.
4. A reference (or nothing but references) to a name with no definition is an error.

Return:
- `"multiple definition of NAME"` if rule 1 is violated (the alphabetically smallest such name); this
  takes priority;
- else `"undefined reference to NAME"` for the alphabetically smallest undefined name;
- else a list of `[name, module_index]` pairs sorted by name, giving the module whose definition every
  reference to `name` resolves to.

**Example:** `[[["main","strong"],["x","strong"],["f","ref"]], [["x","weak"],["f","strong"]]]`
→ `[["f",1],["main",0],["x",0]]`
""",
    starter='''def resolve(modules: List[List[List[str]]]):
    pass
''',
    solution='''def resolve(modules):
    strong, weak, names = {}, {}, set()
    for i, m in enumerate(modules):
        for name, kind in m:
            names.add(name)
            if kind == "strong":
                strong.setdefault(name, []).append(i)
            elif kind == "weak":
                weak.setdefault(name, []).append(i)
    dup = sorted(n for n, lst in strong.items() if len(lst) > 1)
    if dup:
        return "multiple definition of " + dup[0]
    undef = sorted(n for n in names if n not in strong and n not in weak)
    if undef:
        return "undefined reference to " + undef[0]
    return [[n, strong[n][0] if n in strong else min(weak[n])] for n in sorted(names)]
''',
    tests=[
        [[[["main", "strong"], ["x", "strong"], ["f", "ref"]], [["x", "weak"], ["f", "strong"]]]],
        [[[["main", "strong"]], [["main", "strong"]]]],
        [[[["x", "strong"], ["main", "strong"]], [["x", "strong"], ["p1", "strong"]]]],
        [[[["main", "strong"], ["foo", "ref"]]]],
        [[[["x", "weak"]], [["x", "weak"]], [["x", "weak"], ["main", "strong"]]]],
        [[[["x", "weak"], ["main", "strong"]], [["x", "weak"]], [["x", "strong"]]]],
        [[]],
        [[[]]],
        [[[["b", "ref"], ["a", "ref"]], [["z", "strong"], ["z", "strong"]]]],
        [[[["b", "ref"], ["a", "ref"], ["c", "weak"]]]],
        [[[["main", "strong"], ["printf", "ref"], ["buf", "weak"]], [["printf", "strong"], ["buf", "ref"], ["write", "ref"]],
          [["write", "strong"], ["buf", "weak"]]]],
        [[[["y", "weak"], ["y", "ref"]], [["y", "ref"]]]],
    ],
    wrong_solutions=['''def resolve(modules):
    chosen, names = {}, set()
    for i, m in enumerate(modules):
        for name, kind in m:
            names.add(name)
            if kind != "ref" and name not in chosen:
                chosen[name] = i
    undef = sorted(n for n in names if n not in chosen)
    if undef:
        return "undefined reference to " + undef[0]
    return [[n, chosen[n]] for n in sorted(names)]
''', '''def resolve(modules):
    strong, weak, names = {}, {}, set()
    for i, m in enumerate(modules):
        for name, kind in m:
            names.add(name)
            if kind == "strong":
                strong.setdefault(name, []).append(i)
            elif kind == "weak":
                weak.setdefault(name, []).append(i)
    undef = sorted(n for n in names if n not in strong and n not in weak)
    if undef:
        return "undefined reference to " + undef[0]
    dup = sorted(n for n, lst in strong.items() if len(lst) > 1)
    if dup:
        return "multiple definition of " + dup[0]
    return [[n, strong[n][0] if n in strong else min(weak[n])] for n in sorted(names)]
'''],
    guide=dict(
        prereqs="Lesson *Static linking: symbols and relocation* (strong and weak symbols).",
        intuition="Collect, per name, the modules with strong definitions and those with weak ones. Then apply the three rules in order, plus the undefined-reference check.",
        hints=["Two dictionaries: `strong[name] -> [modules]`, `weak[name] -> [modules]`.", "Check duplicates of strong symbols before anything else.", "A name is undefined if it appears only as `ref`."],
        brute_force="For each name scan all modules again: O(names × total entries). Fine for small inputs.",
        approach="One pass to bucket definitions; error checks; then for each name pick `strong[0]` or the smallest weak module. Dry run of the example: x has strong in 0 and weak in 1 → 0.",
        complexity="O(total entries + n log n) for sorting names.",
        pitfalls="- 'First definition wins' is wrong: a later strong symbol overrides an earlier weak one.\n- Error priority: multiple definition before undefined reference.\n- Two weak definitions are legal.",
        follow_up="Extend with static libraries: process archives left to right with the E/U/D algorithm and show that command-line order matters.",
    ),
),
]
