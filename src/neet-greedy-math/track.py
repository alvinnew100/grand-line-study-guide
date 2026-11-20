TRACK = dict(
    id="neet-greedy-math",
    title="Patterns VI — Greedy, Intervals, Math & Bits",
    icon="🌊",
    color="#1f8a9e",
    group="Data Structures & Algorithms",
    blurb="When the locally best move is globally right (and how to prove it), interval sweeps and "
          "meeting-room heaps, matrix and number-theory tricks, and bit manipulation with Python's "
          "unbounded integers.",
    sources=[
        "Goodrich, Tamassia & Goldwasser, Data Structures and Algorithms in Python — §4.4 (repeated squaring), §13.4.2 (the greedy method), ch. 14 (greedy graph algorithms)",
        "Bryant & O'Hallaron, Computer Systems: A Programmer's Perspective — ch. 2 (bit-level operations, two's complement, integer arithmetic)",
        "NeetCode 150",
    ],
    modules=[
        dict(
            id="greedy",
            title="Greedy",
            summary="Make the locally best choice — and learn to prove (or refute) that it is globally best.",
            lessons=[
                dict(id="greedy-method", title="When greedy works: exchange arguments and counterexamples", file="01-greedy-method.md"),
                dict(id="greedy-patterns", title="Greedy patterns: Kadane, frontiers, and running ranges", file="02-greedy-patterns.md"),
            ],
            problems=[
                "maximum-subarray", "jump-game", "jump-game-ii", "gas-station", "hand-of-straights",
                "merge-triplets-to-form-target-triplet", "partition-labels", "valid-parenthesis-string",
                "lemonade-change", "candy", "boats-to-save-people",
            ],
        ),
        dict(
            id="intervals",
            title="Intervals",
            summary="Sort by start or end, sweep left to right, and use a heap when you need to know what is still open.",
            lessons=[
                dict(id="interval-basics", title="Interval fundamentals: overlap, sorting, merging", file="03-interval-basics.md"),
                dict(id="interval-sweep", title="Sweep lines and heaps: meeting rooms and queries", file="04-interval-sweep.md"),
            ],
            problems=[
                "insert-interval", "merge-intervals", "non-overlapping-intervals", "meeting-rooms",
                "meeting-rooms-ii", "minimum-interval-to-include-each-query",
            ],
        ),
        dict(
            id="math-geometry",
            title="Math & Geometry",
            summary="Matrix index gymnastics, digit arithmetic, fast exponentiation, primes and gcd.",
            lessons=[
                dict(id="matrix-tricks", title="Matrix manipulation: rotate, spiral, mark in place", file="05-matrix-tricks.md"),
                dict(id="number-theory", title="Interview number theory: digits, modular arithmetic, fast power, primes, gcd", file="06-number-theory.md"),
            ],
            problems=[
                "rotate-image", "spiral-matrix", "set-matrix-zeroes", "happy-number", "plus-one",
                "powx-n", "multiply-strings", "detect-squares", "count-primes", "math-gcd",
            ],
        ),
        dict(
            id="bit-manipulation",
            title="Bit Manipulation",
            summary="Bitwise operators, two's complement, masks, XOR tricks — and simulating 32-bit integers in Python.",
            lessons=[
                dict(id="bits-python", title="Bits in Python: operators, two's complement, and unbounded ints", file="07-bits-python.md"),
                dict(id="bit-tricks", title="Bit tricks for interviews: x & (x-1), XOR, masks, bit DP", file="08-bit-tricks.md"),
            ],
            problems=[
                "single-number", "number-of-1-bits", "counting-bits", "reverse-bits", "missing-number",
                "sum-of-two-integers", "reverse-integer",
            ],
        ),
    ],
)
