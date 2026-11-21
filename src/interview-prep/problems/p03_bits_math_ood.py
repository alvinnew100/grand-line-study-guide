import random

R = random.Random(37)
G = ("prereqs", "intuition", "hints", "brute_force", "approach", "complexity", "pitfalls", "follow_up")


def _starter(sol):
    out = []
    for ln in sol.splitlines():
        s = ln.strip()
        if ln.startswith("class "):
            out.append(ln)
        elif s.startswith("def ") and (ln.startswith("    def ") or ln.startswith("def ")) and (
                not s.startswith("def _") or s.startswith("def __init__")):
            out.append(ln)
            out.append(ln[:len(ln) - len(ln.lstrip())] + "    pass")
    return "\n".join(out) + "\n"


def P(id, title, diff, pattern, entry, desc, sol, tests, wrong, guide, **kw):
    if "class Solution" not in sol:
        kw.setdefault("kind", "class")
    return dict(id="ctci-" + id, title=title, difficulty=diff, pattern=pattern, entry=entry,
                description=desc.strip() + "\n", starter=_starter(sol), solution=sol, tests=tests,
                wrong_solutions=wrong, guide=dict(zip(G, guide)), **kw)


def _ops(name, n, makers):
    ops, args = [name[0]], [name[1]]
    for _ in range(n):
        op, fn = R.choice(makers)
        ops.append(op)
        args.append(fn())
    return [ops, args]


def _board(n, fill):
    rows = []
    for _ in range(n):
        rows.append("".join(R.choice(fill) for _ in range(n)))
    return rows


_plates = lambda: "P%d" % R.randint(0, 40)
_paths = ["/a", "/b", "/a/x", "/a/y", "/a/x/k", "/b/z", "/c", "/a/x/k/deep", "/b/z/f1", "/a/f2", "/f3", "/a/x/f4", "/nope/q"]

PROBLEMS = [
P("splice-bits", "Splice Bits", "Easy", "Bit Manipulation", "splice",
"""
A device register is a 32-bit unsigned number `reg`. You must overwrite the bit positions `lo … hi` (inclusive, position 0 is the least significant bit) with the value `field`, leaving all other bits untouched. `field` is guaranteed to fit in `hi - lo + 1` bits.

Return the new register value.

**Constraints:** `0 <= lo <= hi <= 31`; `0 <= reg < 2^32`.

**Example:** `reg = 0b11111111` (255), `field = 0b010` (2), `lo = 3, hi = 5` → `0b11010111` (215)
""",
'''class Solution:
    def splice(self, reg: int, field: int, lo: int, hi: int) -> int:
        width = hi - lo + 1
        mask = ((1 << width) - 1) << lo
        return (reg & ~mask & 0xFFFFFFFF) | (field << lo)
''',
[[255, 2, 3, 5], [1024, 19, 2, 6], [0, 0, 0, 0], [0xFFFFFFFF, 0, 0, 31], [0xFFFFFFFF, 0, 4, 7], [0, 0xFFFFFFFF, 0, 31], [0b1111, 0b00, 1, 2],
 [0b1010, 1, 0, 0], [0x80000000, 1, 31, 31], [0x7FFFFFFF, 1, 31, 31], [0xDEADBEEF, 0xA, 12, 15], [0xDEADBEEF, 0, 0, 15],
 [12345678, 5, 20, 22], [0xFFFFFFFF, 0b101, 29, 31]],
['''class Solution:
    def splice(self, reg, field, lo, hi):
        return reg | (field << lo)
''', '''class Solution:
    def splice(self, reg, field, lo, hi):
        mask = ((1 << (hi - lo)) - 1) << lo
        return (reg & ~mask & 0xFFFFFFFF) | (field << lo)
'''],
("Binary numbers and the operators `&`, `|`, `~`, `<<`: see [Bits in Python](#/lesson/neet-greedy-math/bits-python).",
 "Writing a field is two steps: first make a hole (force the target bits to 0), then drop the new bits into the hole with OR. A hole is made by AND-ing with a mask that has 0s exactly where the hole should be.",
 ["OR alone can turn 0s into 1s but can never turn a 1 into a 0.",
  "Build a block of `width` ones with `(1 << width) - 1`, then shift it to position `lo`.",
  "Clear with `reg & ~mask`, then OR in `field << lo`."],
 "Loop over the positions `lo … hi`, clearing or setting one bit at a time with single-bit masks: correct, O(width), more code.",
 "`width = hi - lo + 1`; `mask = ((1 << width) - 1) << lo`; answer `(reg & ~mask) | (field << lo)`.\n\nDry run: width 3, mask `0b00111000`. `reg & ~mask` = `0b11000111`. `field << 3` = `0b00010000`. OR → `0b11010111` = 215.",
 "O(1) time and space.",
 "Skipping the clearing step. An off-by-one width (`hi - lo`) leaves the top bit of the field's range dirty. In Python `~mask` is negative; AND-ing with `0xFFFFFFFF` keeps the result in 32 bits.",
 "Write `extract(reg, lo, hi)` that reads a field back. These two helpers are how network headers and file formats are packed: see [Bit tricks](#/lesson/neet-greedy-math/bit-tricks).")),

P("bit-flips-between", "Bit Flips Between Two Numbers", "Easy", "Bit Manipulation", "flipsNeeded",
"""
Two machines hold the non-negative integers `a` and `b`. How many individual bits of `a` would you have to flip (0 → 1 or 1 → 0) to make it equal to `b`?

**Constraints:** `0 <= a, b < 2^62`. Do not convert the numbers to strings.

**Example 1:** `a = 44 (101100), b = 37 (100101)` → `2`

**Example 2:** `a = 8, b = 8` → `0`
""",
'''class Solution:
    def flipsNeeded(self, a: int, b: int) -> int:
        diff = a ^ b
        count = 0
        while diff:
            diff &= diff - 1
            count += 1
        return count
''',
[[44, 37], [8, 8], [0, 0], [0, 1], [1, 0], [0, 2 ** 62 - 1], [2 ** 61, 2 ** 61 - 1], [5, 10], [255, 0], [1023, 1024],
 [R.getrandbits(62), R.getrandbits(62)], [R.getrandbits(62), R.getrandbits(62)], [7, 4]],
['''class Solution:
    def flipsNeeded(self, a, b):
        return abs(bin(a).count("1") - bin(b).count("1"))
'''],
("XOR and counting set bits: see [Bit tricks](#/lesson/neet-greedy-math/bit-tricks).",
 "XOR writes a 1 exactly in the positions where two numbers disagree. So the question becomes: how many 1 bits does `a ^ b` have?",
 ["Which operator gives 1 when two bits differ and 0 when they agree?",
  "Now count the 1 bits of that result.",
  "`x & (x - 1)` removes the lowest 1 bit of `x`; repeat until `x` is 0 and count the repetitions."],
 "Compare the two numbers bit by bit for 62 positions with shifts: fine, but always 62 steps.",
 "`diff = a ^ b`. While `diff` is non-zero: `diff &= diff - 1`, `count += 1`.\n\nDry run 44 ^ 37 = `001001`. `1001 & 1000 = 1000` (count 1). `1000 & 0111 = 0` (count 2). Answer 2.",
 "Time O(number of differing bits), at most 62 iterations. Space O(1).",
 "Comparing the *counts* of ones (5 and 10 both have two ones yet differ in four positions).",
 "Same building block as [Hamming Distance](#/problem/hamming-distance) and [Number of 1 Bits](#/problem/number-of-1-bits).")),

P("swap-neighbor-bits", "Swap Neighbouring Bits", "Easy", "Bit Manipulation", "swapPairs",
"""
In a 32-bit unsigned number, number the bit positions from 0 (least significant). Swap every even-position bit with the odd-position bit directly above it: bit 0 with bit 1, bit 2 with bit 3, and so on. Return the result.

Use as few operations as you can; a loop over the 16 pairs is not needed.

**Constraints:** `0 <= x < 2^32`.

**Example:** `x = 0b0110_1001` (105) → `0b1001_0110` (150)
""",
'''class Solution:
    def swapPairs(self, x: int) -> int:
        return ((x & 0xAAAAAAAA) >> 1) | ((x & 0x55555555) << 1)
''',
[[105], [0], [1], [2], [3], [0xFFFFFFFF], [0x80000000], [0x40000000], [0xAAAAAAAA], [0x55555555], [0xDEADBEEF],
 [R.getrandbits(32)], [R.getrandbits(32)], [6]],
['''class Solution:
    def swapPairs(self, x):
        return ((x & 0x55555555) >> 1) | ((x & 0xAAAAAAAA) << 1)
''', '''class Solution:
    def swapPairs(self, x):
        return ((x >> 1) | (x << 1)) & 0xFFFFFFFF
'''],
("Masks written in hexadecimal: see [Bits in Python](#/lesson/neet-greedy-math/bits-python).",
 "Treat all 16 pairs at once. Pick out the odd-position bits with one mask and slide them down; pick out the even-position bits with another mask and slide them up; merge.",
 ["What does the hexadecimal digit `A` look like in binary? And `5`?",
  "`0xAAAAAAAA` selects the odd positions, `0x55555555` the even ones.",
  "Shift the odd group right by one, the even group left by one, and OR them."],
 "For each of the 16 pairs, read both bits and, if they differ, flip both: 16 iterations instead of 5 operations.",
 "`((x & 0xAAAAAAAA) >> 1) | ((x & 0x55555555) << 1)`.\n\nDry run `01101001`: odd bits `00101000` → shifted right `00010100`. Even bits `01000001` → shifted left `10000010`. OR → `10010110`.",
 "O(1) time and space.",
 "Swapping the two masks moves bits the wrong way and loses information. Shifting without masking first smears neighbours together.",
 "Reverse all 32 bits by repeating the idea with groups of 2, 4, 8 and 16: see [Reverse Bits](#/problem/reverse-bits).")),

P("longest-ones-one-flip", "Longest Run After One Flip", "Medium", "Bit Manipulation", "bestRun",
"""
A 32-bit unsigned number `x` is shown as a row of 32 lamps (1 = on). You may switch **exactly one** lamp from off to on. What is the length of the longest unbroken stretch of lit lamps you can obtain?

If all 32 lamps are already on, the answer is 32.

**Constraints:** `0 <= x < 2^32`. Aim for O(1) extra memory (no list of run lengths).

**Example:** `x = 0b1110110111` (951) → `6` (turn on one of the 0s: it joins a run of three with the run of two)
""",
'''class Solution:
    def bestRun(self, x: int) -> int:
        if x == 0xFFFFFFFF:
            return 32
        current = previous = 0
        best = 1
        for _ in range(32):
            if x & 1:
                current += 1
            else:
                previous = current if (x & 2) else 0
                current = 0
            best = max(best, previous + current + 1)
            x >>= 1
        return best
''',
[[951], [0], [0xFFFFFFFF], [1], [0b101], [0b1001], [0b110011], [0x7FFFFFFF], [0xFFFFFFFE], [0xFFFF7FFF], [0b111],
 [0xF0F0F0F0], [0x80000001], [1775], [R.getrandbits(32)], [R.getrandbits(32)]],
['''class Solution:
    def bestRun(self, x):
        best = cur = 0
        for i in range(32):
            if (x >> i) & 1:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return min(32, best + 1)
'''],
("Reading bits one at a time with `x & 1` and `x >>= 1`: see [Bit tricks](#/lesson/neet-greedy-math/bit-tricks).",
 "Flipping a 0 joins the run of 1s on its right with the run of 1s on its left. Scan the bits once, remembering the length of the current run and the length of the run that came just before the most recent 0.",
 ["Write the number as alternating run lengths, e.g. `111 0 1111 0 11`. A flip merges two neighbouring runs of 1s only if a *single* 0 separates them.",
  "Keep `current` (ones since the last 0) and `previous` (the run before that 0, or 0 if that 0 was followed by another 0).",
  "Candidate answer at each step: `previous + 1 + current`."],
 "Try each of the 32 positions: set the bit, measure the longest run. 32 × 32 steps; perfectly reasonable to mention as the first idea.",
 "Scan from the low bit. On a 1: `current += 1`. On a 0: if the next bit is 1 the left run can still be joined, so `previous = current`, else `previous = 0`; then `current = 0`. Track `previous + current + 1`.\n\nDry run `1110110111` from the right: three 1s (current 3, candidate 4); a 0 followed by a 1 → previous 3, current 0; two 1s → candidate 3+2+1 = 6; next 0 → previous 2; three 1s → 2+3+1 = 6. Best 6.",
 "Time O(32) = O(1), space O(1).",
 "Adding 1 to the longest existing run ignores the merge (the wrong solution gives 4 for the example). Returning 33 when every bit is set. Returning 0 for `x = 0` (the answer is 1).",
 "The array form is [Max Consecutive Ones III](#/problem/max-consecutive-ones-iii) with k = 1: a sliding window that tolerates one zero.")),

P("next-same-weight", "Next Number With the Same Weight", "Medium", "Bit Manipulation", "nextSameWeight",
"""
The **weight** of a positive integer is the number of 1 bits in its binary form. Given `x`, return the **smallest integer greater than `x`** that has the same weight.

**Constraints:** `1 <= x < 2^60`.

**Example 1:** `x = 6 (110)` → `9 (1001)`

**Example 2:** `x = 22 (10110)` → `25 (11001)`
""",
'''class Solution:
    def nextSameWeight(self, x: int) -> int:
        lowest = x & -x
        ripple = x + lowest
        ones = ((x ^ ripple) >> 2) // lowest
        return ripple | ones
''',
[[6], [22], [1], [2], [3], [5], [7], [8], [0b1011], [0b111000], [2 ** 59], [2 ** 60 - 2 ** 20], [R.getrandbits(50) | 1],
 [R.getrandbits(55) | 2], [13948]],
['''class Solution:
    def nextSameWeight(self, x):
        lowest = x & -x
        return x + lowest
''', '''class Solution:
    def nextSameWeight(self, x):
        return x << 1
'''],
("Lowest set bit `x & -x` and how addition carries: see [Bit tricks](#/lesson/neet-greedy-math/bit-tricks).",
 "To get a bigger number you must turn some 0 into a 1; to keep the weight you must turn a 1 into a 0 somewhere *below* it. Choose the lowest 0 that has a 1 to its right (so the increase is as small as possible), flip it, then push all the lower 1s as far right as they can go (so the tail is as small as possible).",
 ["Write a few examples in binary: 0110 → 1001, 1011 → 1101, 111000 → 1000011.",
  "Find the rightmost block of 1s. Its top neighbour (a 0) becomes 1; one 1 from the block is used up for that.",
  "The remaining 1s of the block move to the very bottom."],
 "Count the weight, then test `x+1`, `x+2`, … until the weight matches. For `x = 2^59` that is about 2^59 tests.",
 "`lowest = x & -x` isolates the lowest 1. `ripple = x + lowest` clears the rightmost block and sets the 0 above it. `x ^ ripple` is that whole changed region; dividing by `lowest` and shifting right by 2 leaves the block's remaining ones (block length minus one) right-aligned. OR them in.\n\nDry run `x = 0110`: lowest `0010`, ripple `1000`, `x ^ ripple = 1110`, `>> 2 = 11`, `// 2 = 1`. Result `1001` = 9.",
 "O(1) arithmetic operations.",
 "Stopping after the ripple (gives 8 for 6, weight 1). Doubling keeps the weight but is rarely the *next* one.",
 "Write `prevSameWeight` (mirror image: flip the lowest 1 that has a 0 below it). This is the standard way to enumerate all k-element subsets as bit masks, known as Gosper's hack.")),

P("binary-fraction", "Binary Fraction Printer", "Medium", "Bit Manipulation", "fractionBits",
"""
A fraction strictly between 0 and 1 is given exactly as `num / den`. Print its binary expansion as a string that starts with `"0."`, for example `5/8 = 0.101` in binary (one half plus one eighth).

If the expansion needs **more than 32 binary digits** after the point (or never ends), return `"ERROR"`.

**Constraints:** `1 <= num < den <= 2^40`.

**Example 1:** `num = 5, den = 8` → `"0.101"`

**Example 2:** `num = 1, den = 3` → `"ERROR"` (0.010101… never terminates)
""",
'''class Solution:
    def fractionBits(self, num: int, den: int) -> str:
        digits = []
        while num:
            if len(digits) == 32:
                return "ERROR"
            num *= 2
            if num >= den:
                digits.append("1")
                num -= den
            else:
                digits.append("0")
        return "0." + "".join(digits)
''',
[[5, 8], [1, 3], [1, 2], [1, 4], [3, 4], [1, 10], [2, 4], [1, 2 ** 32], [1, 2 ** 33], [2 ** 32 - 1, 2 ** 32], [3, 2 ** 33],
 [2, 2 ** 33], [7, 16], [5, 10], [3, 6], [1023, 1024]],
['''class Solution:
    def fractionBits(self, num, den):
        digits = []
        while num:
            if len(digits) == 31:
                return "ERROR"
            num *= 2
            if num >= den:
                digits.append("1")
                num -= den
            else:
                digits.append("0")
        return "0." + "".join(digits)
''', '''class Solution:
    def fractionBits(self, num, den):
        if den & (den - 1):
            return "ERROR"
        digits = []
        while num:
            num *= 2
            digits.append("1" if num >= den else "0")
            if num >= den:
                num -= den
        return "0." + "".join(digits) if len(digits) <= 32 else "ERROR"
'''],
("Place value after the binary point (halves, quarters, eighths): see [Bits and bytes](#/lesson/csapp/bits-bytes).",
 "In decimal, multiplying 0.37 by 10 pushes the first digit (3) in front of the point. Binary works the same with 2: double the fraction; if the result reaches 1 the next digit is 1 (and you subtract 1), otherwise it is 0.",
 ["What does doubling do to 0.101 in binary? It becomes 1.01.",
  "Work with the exact pair (num, den) rather than a float: doubling is `num *= 2`, \"reached 1\" is `num >= den`.",
  "Stop when `num` becomes 0. If you are about to produce a 33rd digit, give up."],
 "Subtract 1/2, 1/4, 1/8, … greedily using floating point. It works for short cases but floats themselves have only 53 bits and cannot represent 1/10 exactly, so the output depends on rounding.",
 "Loop while `num != 0`: if 32 digits already exist return `ERROR`; double; emit 1 and subtract `den` if `num >= den`, else emit 0.\n\nDry run 5/8: double → 10/8 ≥ 1 → digit 1, left 2/8; double → 4/8 → 0; double → 8/8 → 1, left 0. Result `0.101`.",
 "At most 32 iterations: O(1) time and space.",
 "Allowing only 31 digits. Rejecting every denominator that is not a power of two: `5/10` is `1/2` and prints fine, so reduce first or let the loop decide.",
 "Detect a repeating expansion and print it as `0.0(01)` by remembering which remainders you have seen: see LeetCode's *Fraction to Recurring Decimal*.")),

P("smooth-number-k", "K-th Number From Chosen Primes", "Medium", "Math & Logic", "kthSmooth",
"""
You are given a short list of distinct prime numbers, `primes`. Call a positive integer **buildable** when it can be written as a product that uses only those primes, each as many times as you like (including zero times). The number 1, the empty product, is buildable.

For `primes = [2, 7, 11]` the buildable numbers in increasing order begin `1, 2, 4, 7, 8, 11, 14, 16, 22, 28, …` (6 is missing because it needs the factor 3).

Return the `k`-th buildable number (1-based).

**Constraints:** `1 <= k <= 5000`; between 1 and 6 distinct primes, each below 50, in any order.

**Example 1:** `k = 1, primes = [2, 7, 11]` → `1`

**Example 2:** `k = 9, primes = [2, 7, 11]` → `22`
""",
'''class Solution:
    def kthSmooth(self, k: int, primes: List[int]) -> int:
        seq = [1]
        at = [0] * len(primes)
        while len(seq) < k:
            heads = [seq[at[j]] * p for j, p in enumerate(primes)]
            nxt = min(heads)
            seq.append(nxt)
            for j, value in enumerate(heads):
                if value == nxt:
                    at[j] += 1
        return seq[k - 1]
''',
[[1, [2, 7, 11]], [9, [2, 7, 11]], [2, [2, 7, 11]], [6, [3]], [10, [2]], [7, [5, 3]], [13, [3, 11, 13]], [50, [2, 3, 5, 7]],
 [500, [2, 7, 11]], [5000, [2, 7, 11]], [1234, [13, 3, 11]], [300, [2, 3, 5, 7, 11, 13]], [10, [47]], [45, [43, 47]]],
['''class Solution:
    def kthSmooth(self, k, primes):
        seq = [1]
        at = [0] * len(primes)
        while len(seq) < k:
            heads = [seq[at[j]] * p for j, p in enumerate(primes)]
            nxt = min(heads)
            seq.append(nxt)
            at[heads.index(nxt)] += 1
        return seq[k - 1]
''', '''class Solution:
    def kthSmooth(self, k, primes):
        out, x = [1], 2
        while len(out) < k:
            if any(x % p == 0 for p in primes):
                out.append(x)
            x += 1
        return out[k - 1]
'''],
("Prime factorisation and merging sorted sequences: see [Number theory](#/lesson/neet-greedy-math/number-theory).",
 "Every buildable number except 1 is an earlier buildable number multiplied by one of the primes. So the sequence is the merge of several sorted streams, one per prime: (sequence × p). Keep one pointer per stream and always take the smallest head.",
 ["With primes 2, 7, 11, how is 14 produced? 7 × 2 or 2 × 7. Notice the same value can come from two streams.",
  "Keep one index into the answer list for each prime.",
  "After choosing the minimum, advance **every** pointer whose head equals it, so duplicates are skipped."],
 "Test every integer by dividing out the primes. The buildable numbers thin out so quickly that the 5000-th can be far beyond anything a counting loop reaches. A min-heap with a visited set works in O(k log k).",
 "`seq = [1]`, `at = [0, 0, 0]`. Heads: `seq[at[j]] * primes[j]`. Append the minimum and advance the matching pointer(s).\n\nDry run with 2, 7, 11: heads 2, 7, 11 → 2. Heads 4, 7, 11 → 4. Heads 8, 7, 11 → 7. Heads 8, 14, 11 → 8. Heads 14, 14, 11 → 11. Heads 14, 14, 22 → 14, and both the 2-pointer and the 7-pointer advance.",
 "Time O(k · p) for p primes, space O(k).",
 "Advancing only the first pointer that matches leaves a duplicate in the list (14 would appear twice; first wrong solution). Accepting every multiple of a listed prime (second wrong solution) lets in numbers such as 6, which also needs the factor 3.",
 "With the fixed primes 2, 3, 5 this is [Ugly Number II](#/problem/ugly-number-ii). With many primes, replace the scan for the minimum by a heap: LeetCode's *Super Ugly Number*.")),

P("dice-sum-probability", "Chance of a Dice Total", "Medium", "Math & Logic", "diceChance",
"""
You roll `n` fair six-sided dice. What is the probability that the faces add up to exactly `total`?

Return the exact answer as a fraction in lowest terms, `[numerator, denominator]`. Return `[0, 1]` when the total is impossible.

**Constraints:** `1 <= n <= 30`; `0 <= total <= 200`.

**Example 1:** `n = 2, total = 7` → `[1, 6]` (6 of the 36 outcomes)

**Example 2:** `n = 1, total = 9` → `[0, 1]`
""",
'''class Solution:
    def diceChance(self, n: int, total: int) -> List[int]:
        ways = [1] + [0] * total
        for _ in range(n):
            nxt = [0] * (total + 1)
            for s in range(total + 1):
                if ways[s]:
                    for face in range(1, 7):
                        if s + face <= total:
                            nxt[s + face] += ways[s]
            ways = nxt
        num, den = ways[total], 6 ** n
        if num == 0:
            return [0, 1]
        g = math.gcd(num, den)
        return [num // g, den // g]
''',
[[2, 7], [1, 9], [1, 1], [1, 6], [2, 2], [2, 12], [2, 13], [3, 10], [1, 0], [3, 2], [10, 35], [30, 105], [30, 30], [30, 180],
 [30, 181], [5, 17]],
['''class Solution:
    def diceChance(self, n, total):
        if total < n or total > 6 * n:
            return [0, 1]
        g = math.gcd(1, 5 * n + 1)
        return [1, 5 * n + 1]
''', '''class Solution:
    def diceChance(self, n, total):
        ways = [1] + [0] * total
        for _ in range(n):
            nxt = [0] * (total + 1)
            for s in range(total + 1):
                for face in range(1, 7):
                    if s + face <= total:
                        nxt[s + face] += ways[s]
            ways = nxt
        return [ways[total], 6 ** n] if ways[total] else [0, 1]
'''],
("Probability as favourable outcomes divided by all outcomes, and counting with dynamic programming: see [DP for counting](#/lesson/neet-dp/dp-counting-states).",
 "All `6^n` sequences of faces are equally likely, so the probability is (number of sequences with the right sum) / `6^n`. Count the sequences one die at a time: the ways to reach sum `s` with `d` dice come from the ways to reach `s-1 … s-6` with `d-1` dice.",
 ["The totals are not equally likely (there are 11 possible totals for two dice but 7 has probability 1/6).",
  "Let `ways[s]` = number of ordered rolls of the dice so far that add to `s`. Start with zero dice: `ways[0] = 1`.",
  "After the table is filled, reduce `ways[total] / 6^n` with `math.gcd`."],
 "Enumerate all `6^n` outcomes with recursion: fine for n ≤ 8, hopeless for n = 30 (about 2·10²³ outcomes).",
 "Repeat n times: build `nxt` from `ways` by adding each face 1…6. Then reduce the fraction.\n\nDry run n = 2: after one die `ways[1..6] = 1`. After two dice `ways[7] = ways[1]+…+ways[6] = 6`. Fraction 6/36 → `[1, 6]`.",
 "Time O(n · total · 6), space O(total). Python's big integers keep the count exact.",
 "Assuming every total from n to 6n is equally likely. Returning an unreduced fraction. Using floats: 6³⁰ exceeds the 53 bits a float holds exactly.",
 "The counting core is LeetCode's *Number of Dice Rolls With Target Sum*. Try answering \"at least `total`\" with a suffix sum.")),

P("lamp-toggle", "Pier Lamps", "Easy", "Math & Logic", "lampsOn",
"""
A long pier is lit by `n` lamps numbered `1 … n`, all switched off at dusk. During the night a maintenance routine makes `n` passes along the pier: on pass `k` it presses the switch of every lamp whose number is a multiple of `k`, and each press flips that lamp (off ↔ on).

When the last pass is over, how many lamps are on?

**Constraints:** `0 <= n <= 10^18`. A simulation is far too slow; find the pattern.

**Example 1:** `n = 10` → `3` (lamps 1, 4 and 9)

**Example 2:** `n = 3` → `1`
""",
'''class Solution:
    def lampsOn(self, n: int) -> int:
        return math.isqrt(n)
''',
[[10], [3], [0], [1], [2], [4], [15], [16], [100], [99], [10 ** 18], [10 ** 18 - 1], [999999999999999999 - 2 * 10 ** 9], [2 ** 53 + 1],
 [(10 ** 8 + 7) ** 2 - 1]],
['''class Solution:
    def lampsOn(self, n):
        return int(n ** 0.5)
''', '''class Solution:
    def lampsOn(self, n):
        return n // 3
'''],
("Divisors of a number: see [Number theory](#/lesson/neet-greedy-math/number-theory).",
 "Lamp `L` is flipped once for every divisor of `L`. It ends on when it is flipped an odd number of times. Divisors come in pairs (`d` and `L/d`), so the count is even unless some divisor is paired with itself, which happens exactly when `L` is a perfect square.",
 ["Simulate n = 10 by hand and write down which lamps end on.",
  "How many times is lamp 12 flipped? List its divisors and pair them up.",
  "Count the perfect squares up to `n`: that is the integer square root of `n`."],
 "Simulate with an array: pass k flips n/k lamps, total about n ln n operations. Fine for n = 10⁵, impossible for 10¹⁸.",
 "Return `math.isqrt(n)`.\n\nDry run n = 10: squares ≤ 10 are 1, 4, 9 → 3. Lamp 4 has divisors 1, 2, 4 (three flips: on, off, on).",
 "O(1) arithmetic (isqrt is O(log n) bit operations).",
 "`int(n ** 0.5)` uses floating point and is off by one for large `n`: for `n = 10^18 - 1` the float square root rounds up to exactly 10⁹. Use `math.isqrt`.",
 "Follow-ups: which lamps are flipped exactly twice (the primes)? Which are flipped exactly three times (squares of primes)? The same divisor-pairing argument appears in LeetCode's *Bulb Switcher* and in the lockers puzzle of the lesson.")),

P("two-phone-drop", "Two Phones, One Tower", "Medium", "Math & Logic", "minTrials",
"""
A lab has **two identical prototype phones** and a tower with `floors` floors. There is an unknown threshold floor: a phone dropped from that floor or above breaks, and a phone dropped from below survives and can be reused. The threshold may also be "above the top" (the phone never breaks).

What is the smallest number of drops that is **guaranteed** to identify the threshold, whatever it is?

**Constraints:** `0 <= floors <= 10^18`.

**Example 1:** `floors = 10` → `4`

**Example 2:** `floors = 100` → `14`
""",
'''class Solution:
    def minTrials(self, floors: int) -> int:
        t = (math.isqrt(8 * floors + 1) - 1) // 2
        while t * (t + 1) // 2 < floors:
            t += 1
        return t
''',
[[10], [100], [0], [1], [2], [3], [4], [6], [7], [105], [106], [10 ** 18], [10 ** 12], [5050], [5051]],
['''class Solution:
    def minTrials(self, floors):
        return math.ceil(math.log2(floors + 1))
''', '''class Solution:
    def minTrials(self, floors):
        root = math.isqrt(floors)
        return 2 * root - 1 if root * root == floors else 2 * root
'''],
("Worst-case reasoning and the sum 1 + 2 + … + t = t(t+1)/2: see [Useful maths](#/lesson/interview-prep/review-math-graphs).",
 "Once the first phone breaks you are left with one phone and must climb one floor at a time through the gap below. To keep the worst case level, each jump of the first phone should be one floor shorter than the previous jump: if the first drop is at floor t, a break costs 1 + (t−1) drops; the next jump of t−1 floors costs 2 + (t−2); always t in total.",
 ["With one phone you have no choice but floor 1, 2, 3, …",
  "Fixed jumps of 10 on 100 floors give a worst case of 19. Why is the worst case at the top worse than at the bottom?",
  "With t drops you can cover t + (t−1) + … + 1 floors. Find the smallest t with t(t+1)/2 ≥ floors."],
 "Dynamic programming over floors: best[f] = 1 + min over first drop x of max(x − 1, best[f − x]). O(f²), unusable for 10¹⁸ but excellent for checking small cases.",
 "Solve t(t+1)/2 ≥ floors. Start from the integer estimate `(isqrt(8f+1) − 1) // 2` and adjust upward.\n\nDry run 100: t = 13 covers 91 floors, t = 14 covers 105 ≥ 100 → 14. First drop at 14, then 27, 39, 50, 60, 69, 77, 84, 90, 95, 99, 100.",
 "O(1) arithmetic.",
 "Binary search needs up to log₂(n) phones, not two. Equal jumps of √n give about 2√n, which is not optimal.",
 "The general k-phone version is LeetCode's *Super Egg Drop*: count how many floors t drops and k phones can cover.")),

P("jug-pour", "Two Jugs", "Medium", "Math & Logic", "minPours",
"""
You have a tap, a drain and two unmarked jugs holding exactly `a` and `b` litres when full. One **move** is any of:

- fill one jug completely from the tap,
- empty one jug into the drain,
- pour one jug into the other until the first is empty or the second is full.

Both jugs start empty. Return the minimum number of moves after which **either jug contains exactly `goal` litres**, or `-1` if that can never happen.

**Constraints:** `1 <= a, b <= 300`; `0 <= goal <= 300`.

**Example 1:** `a = 4, b = 7, goal = 6` → `6`

**Example 2:** `a = 2, b = 6, goal = 5` → `-1`
""",
'''class Solution:
    def minPours(self, a: int, b: int, goal: int) -> int:
        start = (0, 0)
        dist = {start: 0}
        queue = collections.deque([start])
        while queue:
            x, y = queue.popleft()
            if x == goal or y == goal:
                return dist[(x, y)]
            to_b = min(x, b - y)
            to_a = min(y, a - x)
            for state in ((a, y), (x, b), (0, y), (x, 0), (x - to_b, y + to_b), (x + to_a, y - to_a)):
                if state not in dist:
                    dist[state] = dist[(x, y)] + 1
                    queue.append(state)
        return -1
''',
[[4, 7, 6], [2, 6, 5], [4, 7, 0], [3, 5, 3], [3, 5, 5], [3, 5, 2], [3, 5, 1], [4, 4, 2], [1, 300, 150], [7, 11, 300], [299, 300, 150],
 [6, 9, 3], [6, 9, 4], [300, 300, 300], [5, 7, 6]],
['''class Solution:
    def minPours(self, a, b, goal):
        if goal > max(a, b) or goal % math.gcd(a, b):
            return -1
        return 0 if goal == 0 else 2
''', '''class Solution:
    def minPours(self, a, b, goal):
        def run(p, q):
            x = y = steps = 0
            while x != goal and y != goal and steps < 4 * (p + q):
                if x == 0:
                    x = p
                elif y == q:
                    y = 0
                else:
                    t = min(x, q - y)
                    x, y = x - t, y + t
                steps += 1
            return steps if x == goal or y == goal else 10 ** 9
        best = min(run(a, b), run(b, a))
        return -1 if best >= 10 ** 9 else best + 1
'''],
("Breadth-first search over *states* rather than places: see [DFS and BFS](#/lesson/neet-heap-graphs/dfs-bfs).",
 "The puzzle is a graph in disguise. A node is a pair (litres in jug A, litres in jug B); each move is an edge. The fewest moves is the shortest path from (0, 0), and breadth-first search finds shortest paths when every edge costs one.",
 ["What information fully describes the situation at any moment?",
  "From one state there are at most six next states. List them.",
  "BFS with a dictionary of distances; stop at the first state that contains `goal`."],
 "Depth-first search without a visited set loops forever (fill, empty, fill, …). With a visited set it terminates but does not give the minimum.",
 "Queue starts with (0,0). For each state generate: fill A, fill B, empty A, empty B, pour A→B, pour B→A. Record unseen states with distance + 1.\n\nDry run 4, 7, goal 6: (0,0) → (0,7) → (4,3) → (0,3) → (3,0) → (3,7) → (4,6): six moves.",
 "At most (a+1)(b+1) states with six edges each: O(a·b) time and space, about 90,000 states at the limits.",
 "A goal is reachable only if it is a multiple of gcd(a, b) and not larger than the bigger jug, but that test alone does not give the *number* of moves. Checking the goal only after pouring misses `goal = 0`, which needs zero moves.",
 "The yes/no version is LeetCode's *Water and Jug Problem*. There is also a number-theory solution: simulate the two \"always pour the same direction\" strategies and take the shorter.")),

P("coin-weighings", "Counterfeit Coin Weighings", "Easy", "Math & Logic", "minWeighings",
"""
Among `n` coins that look identical, exactly one is counterfeit and **slightly heavier**. You have a two-pan balance: each weighing compares two groups of coins and tells you "left heavier", "right heavier" or "equal".

Return the minimum number of weighings that guarantees you can identify the heavy coin.

**Constraints:** `1 <= n <= 10^18`.

**Example 1:** `n = 9` → `2`

**Example 2:** `n = 10` → `3`
""",
'''class Solution:
    def minWeighings(self, n: int) -> int:
        count, reach = 0, 1
        while reach < n:
            reach *= 3
            count += 1
        return count
''',
[[9], [10], [1], [2], [3], [4], [8], [27], [28], [81], [3 ** 30], [3 ** 30 + 1], [10 ** 18], [3 ** 37], [3 ** 37 - 1]],
['''class Solution:
    def minWeighings(self, n):
        count, reach = 0, 1
        while reach < n:
            reach *= 2
            count += 1
        return count
'''],
("Logarithms as \"how many times can I divide by 3?\": see [The seven functions](#/lesson/dsa-foundations/seven-functions).",
 "A weighing has **three** possible results, not two. Split the coins into three piles as equal as possible and weigh two of them: whichever way the scale answers, only one pile can still contain the heavy coin. Each weighing divides the suspects by three.",
 ["Halving (weigh half against half) wastes the \"equal\" outcome.",
  "With 9 coins: weigh 3 against 3. Every answer leaves 3 suspects. One more weighing finishes.",
  "The answer is the smallest w with 3^w ≥ n. Compute it with integer multiplication."],
 "Weigh coins in pairs: up to n/2 weighings.",
 "Start with `reach = 1` (zero weighings distinguish one coin). Multiply by 3 until `reach ≥ n`, counting.\n\nDry run n = 10: 1 → 3 → 9 → 27, three multiplications → 3. It cannot be fewer: two weighings have only 9 distinct result patterns, too few to tell 10 coins apart.",
 "O(log n) time, O(1) space.",
 "Using base 2. Using floating-point `math.log(n, 3)`: for exact powers of 3 it can return 29.000000000000004 and the ceiling becomes 30.",
 "Harder classic: 12 coins, one is different but you do not know whether heavier or lighter, three weighings. The counting argument (3³ = 27 ≥ 24 cases) shows it is just possible.")),

P("two-of-three", "One Shot or Best of Three", "Easy", "Math & Logic", "betterGame",
"""
A fairground stall offers two games with the same prize. You hit the target with probability `p = num / den` on every throw, independently.

- **Game 1:** one throw; you win if it hits.
- **Game 2:** three throws; you win if **at least two** hit.

Return `1` if Game 1 gives the better chance, `2` if Game 2 does, and `0` if the chances are exactly equal. Use exact integer arithmetic.

**Constraints:** `0 <= num <= den <= 10^9`, `den >= 1`.

**Example 1:** `num = 1, den = 4` → `1`

**Example 2:** `num = 3, den = 4` → `2`
""",
'''class Solution:
    def betterGame(self, num: int, den: int) -> int:
        one = num * den * den
        three = 3 * num * num * den - 2 * num ** 3
        if one == three:
            return 0
        return 1 if one > three else 2
''',
[[1, 4], [3, 4], [1, 2], [0, 1], [1, 1], [0, 7], [5, 5], [499999999, 10 ** 9], [500000001, 10 ** 9], [5 * 10 ** 8, 10 ** 9],
 [1, 10 ** 9], [10 ** 9 - 1, 10 ** 9], [2, 4], [3, 7], [4, 7]],
['''class Solution:
    def betterGame(self, num, den):
        return 1 if 2 * num < den else 2
''', '''class Solution:
    def betterGame(self, num, den):
        return 2 if num > 0 else 0
'''],
("Independent events multiply; mutually exclusive events add. See the lesson [Maths and logic puzzles](#/lesson/interview-prep/math-logic-puzzles).",
 "Write both winning chances as formulas in p and compare them. Game 2 is won by exactly two hits (three arrangements, each p²(1−p)) or by three hits (p³): 3p²(1−p) + p³ = 3p² − 2p³.",
 ["List the eight hit/miss patterns of three throws and mark the winning ones.",
  "Compare p with 3p² − 2p³. Divide by p (for p > 0) and you get a quadratic.",
  "Game 1 is better exactly when (2p − 1)(p − 1) > 0, i.e. p < 1/2. To avoid floats, multiply both sides by den³."],
 "Simulate a million games with a random number generator: gives an estimate, never an exact answer, and cannot detect equality.",
 "Scale both probabilities by den³: Game 1 → num·den², Game 2 → 3·num²·den − 2·num³. Compare the integers.\n\nDry run 1/4: 1·16 = 16 versus 3·1·4 − 2 = 10 → Game 1. For 3/4: 3·16 = 48 versus 3·9·4 − 54 = 54 → Game 2.",
 "O(1).",
 "Floating point reports p = 0.5 correctly here but can misjudge equality in general; exact integers cannot. Forgetting the three boundary cases p = 0, p = 1/2, p = 1 where the games tie.",
 "Generalise: best of 5, or \"at least k of n\" with the binomial formula $\\sum_{i \\ge k} \\binom{n}{i} p^i (1-p)^{n-i}$.")),

P("parking-garage", "Parking Garage", "Medium", "Object-Oriented Design", "Garage",
"""
Model a small parking garage with three kinds of space: `compact`, `regular` and `large`.

- A `"bike"` fits in any space and takes the smallest kind that is free (compact, then regular, then large).
- A `"car"` fits in a regular or a large space (regular preferred).
- A `"bus"` needs a large space.

Implement class `Garage(compact, regular, large)` (the numbers of spaces of each kind):

- `park(plate, vehicle)` parks the vehicle and returns the kind of space used (`"compact"`, `"regular"` or `"large"`). Returns `""` if nothing suitable is free **or** a vehicle with this plate is already inside.
- `leave(plate)` frees that vehicle's space and returns `True`; returns `False` if the plate is not inside.
- `free()` returns `[free compact, free regular, free large]`.

**Example:** `Garage(1,1,1)`: `park("B1","bike") → "compact"`, `park("B2","bike") → "regular"`, `park("C1","car") → "large"`, `park("C2","car") → ""`, `leave("B2") → True`, `park("C2","car") → "regular"`, `free() → [0,0,0]`
""",
'''class Garage:
    ORDER = ["compact", "regular", "large"]
    FITS = {"bike": 0, "car": 1, "bus": 2}

    def __init__(self, compact: int, regular: int, large: int):
        self.spaces = [compact, regular, large]
        self.where = {}

    def park(self, plate: str, vehicle: str) -> str:
        if plate in self.where:
            return ""
        for kind in range(self.FITS[vehicle], 3):
            if self.spaces[kind] > 0:
                self.spaces[kind] -= 1
                self.where[plate] = kind
                return self.ORDER[kind]
        return ""

    def leave(self, plate: str) -> bool:
        if plate not in self.where:
            return False
        self.spaces[self.where.pop(plate)] += 1
        return True

    def free(self) -> List[int]:
        return list(self.spaces)
''',
[[["Garage", "park", "park", "park", "park", "leave", "park", "free"],
  [[1, 1, 1], ["B1", "bike"], ["B2", "bike"], ["C1", "car"], ["C2", "car"], ["B2"], ["C2", "car"], []]],
 [["Garage", "park", "leave", "free"], [[0, 0, 0], ["X", "bike"], ["X"], []]],
 [["Garage", "park", "park", "free"], [[2, 2, 2], ["X", "car"], ["X", "car"], []]],
 [["Garage", "park", "park", "leave", "leave", "free"], [[0, 0, 1], ["A", "bus"], ["B", "bus"], ["A"], ["A"], []]],
 [["Garage", "park", "park", "park", "free"], [[5, 0, 1], ["A", "car"], ["B", "car"], ["C", "bus"], []]],
 [["Garage", "park", "leave", "park", "free"], [[1, 0, 0], ["A", "bike"], ["A"], ["A", "bike"], []]],
 [["Garage", "park", "park", "leave", "park", "free"], [[0, 1, 1], ["A", "bike"], ["B", "bus"], ["A"], ["C", "car"], []]],
 _ops(("Garage", [3, 4, 2]), 3000, [("park", lambda: [_plates(), R.choice(["bike", "car", "bus"])]), ("leave", lambda: [_plates()]), ("free", lambda: [])]),
 _ops(("Garage", [10, 10, 10]), 3000, [("park", lambda: [_plates(), R.choice(["bike", "car", "bus"])]), ("park", lambda: [_plates(), "bus"]), ("leave", lambda: [_plates()]), ("free", lambda: [])]),
 _ops(("Garage", [1, 0, 3]), 2000, [("park", lambda: [_plates(), R.choice(["bike", "car"])]), ("leave", lambda: [_plates()]), ("free", lambda: [])])],
['''class Garage:
    ORDER = ["compact", "regular", "large"]
    FITS = {"bike": 0, "car": 1, "bus": 2}

    def __init__(self, compact, regular, large):
        self.spaces = [compact, regular, large]
        self.where = {}

    def park(self, plate, vehicle):
        kind = self.FITS[vehicle]
        if plate in self.where or self.spaces[kind] == 0:
            return ""
        self.spaces[kind] -= 1
        self.where[plate] = kind
        return self.ORDER[kind]

    def leave(self, plate):
        if plate not in self.where:
            return False
        self.spaces[self.where.pop(plate)] += 1
        return True

    def free(self):
        return list(self.spaces)
''', '''class Garage:
    ORDER = ["compact", "regular", "large"]
    FITS = {"bike": 0, "car": 1, "bus": 2}

    def __init__(self, compact, regular, large):
        self.spaces = [compact, regular, large]
        self.where = {}

    def park(self, plate, vehicle):
        for kind in range(self.FITS[vehicle], 3):
            if self.spaces[kind] > 0:
                self.spaces[kind] -= 1
                self.where[plate] = kind
                return self.ORDER[kind]
        return ""

    def leave(self, plate):
        if plate not in self.where:
            return False
        self.spaces[self.where.pop(plate)] += 1
        return True

    def free(self):
        return list(self.spaces)
'''],
("Classes, dictionaries and the design steps in [Object-oriented design](#/lesson/interview-prep/object-oriented-design).",
 "The whole design rests on two pieces of state: how many spaces of each kind are free, and which kind each parked plate occupies. The fitting rule becomes simple once the kinds are *ordered*: a vehicle with minimum kind k may use kind k, k+1, …",
 ["Number the kinds 0, 1, 2 so that \"fits in this or anything bigger\" is a loop from the vehicle's minimum upward.",
  "`leave` must know which kind of space to give back, so remember it per plate in a dictionary.",
  "Reject a duplicate plate before touching any counter."],
 "Keep a list of individual space objects and scan it on every call: O(spaces) per operation. Reasonable when spaces have identities (level, row) but unnecessary here.",
 "`park`: plate present → \"\". Otherwise loop kinds from `FITS[vehicle]` to 2, take the first with a free space, record `where[plate]`.\n\nDry run Garage(1,1,1): B1 bike → compact. B2 bike → compact full → regular. C1 car → regular full → large. C2 car → none → \"\". B2 leaves → regular free. C2 car → regular.",
 "O(1) per operation (the loop has at most three steps); O(number of parked vehicles) space.",
 "Letting a vehicle use only its exact kind. Not remembering the kind per plate and returning the space to the wrong counter. Allowing the same plate twice, which later frees only one of two occupied spaces.",
 "In an interview, extend aloud: several levels, a bus that needs five consecutive large spots, payment by duration, a display of free spaces per level. Decide which class owns each responsibility.")),

P("hand-value", "Card Hand Value", "Easy", "Object-Oriented Design", "handValue",
"""
In the game twenty-one, number cards `"2"` … `"10"` count their face value, `"J"`, `"Q"` and `"K"` count 10, and an ace `"A"` counts **either 1 or 11**, whichever is better for the player.

Given the list of cards in a hand, return the best total: the **largest total that does not exceed 21**. If every way of counting the aces exceeds 21, return the smallest possible total (all aces as 1).

**Constraints:** `0 <= len(cards) <= 30`.

**Example 1:** `["A", "K"]` → `21`

**Example 2:** `["A", "A", "9"]` → `21` (11 + 1 + 9)

**Example 3:** `["K", "Q", "5"]` → `25`
""",
'''class Solution:
    def handValue(self, cards: List[str]) -> int:
        total = aces = 0
        for card in cards:
            if card == "A":
                aces += 1
                total += 1
            elif card in ("J", "Q", "K"):
                total += 10
            else:
                total += int(card)
        if aces and total + 10 <= 21:
            total += 10
        return total
''',
[[["A", "K"]], [["A", "A", "9"]], [["K", "Q", "5"]], [[]], [["A"]], [["A", "A"]], [["10", "A"]], [["9", "A", "A", "A"]],
 [["5", "6", "A"]], [["5", "5", "A"]], [["2", "3", "4"]], [["A"] * 21], [["A"] * 30], [["K", "A", "A"]], [["7", "7", "7"]], [["J", "10", "A"]]],
['''class Solution:
    def handValue(self, cards):
        total = 0
        for card in cards:
            total += 11 if card == "A" else 10 if card in "JQK" else int(card)
        return total
''', '''class Solution:
    def handValue(self, cards):
        total = aces = 0
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ("J", "Q", "K"):
                total += 10
            else:
                total += int(card)
        for _ in range(aces):
            total += 11 if total + 11 <= 21 else 1
        return total
'''],
("Loops and conditionals; the card-game design in [Object-oriented design](#/lesson/interview-prep/object-oriented-design).",
 "At most one ace can ever count as 11, because two of them already make 22. So count every ace as 1, then upgrade a single ace by 10 if that keeps the total within 21.",
 ["Could two aces both be worth 11 in a good hand?",
  "Add everything with aces as 1 and remember whether you saw an ace.",
  "If there is an ace and `total + 10 <= 21`, add 10."],
 "Try all 2^aces assignments and keep the best one: correct, exponential, unnecessary.",
 "One pass to compute `total` (aces as 1) and `aces`. Final adjustment `+10` when allowed.\n\nDry run `A, A, 9`: total 11, aces 2. 11 + 10 = 21 ≤ 21 → 21.",
 "O(n) time, O(1) space.",
 "Counting every ace as 11. Deciding each ace greedily, one at a time, breaks on `9, A, A, A`: the greedy version reaches 22 although 12 is available.",
 "Design the surrounding classes: `Card`, `Deck` with `shuffle` and `deal`, `Hand` with this method, and a `BlackjackHand` subclass versus a strategy object. Which game rules belong where?")),

P("translation-bureau", "Translation Bureau", "Hard", "Object-Oriented Design", "Bureau",
"""
A translation bureau employs three grades of staff: **juniors** (grade 0), **seniors** (grade 1) and **editors** (grade 2). Every incoming job carries a *level* `0`, `1` or `2`: it may only be worked on by someone of that grade **or a higher one**, and it always goes to the lowest suitable grade that has a person free.

Implement class `Bureau(juniors, seniors, editors)` (the head-count of each grade):

- `submit(job, level)`: a new job comes in (`job` is a unique integer id). If a suitable person is free, work starts and the method returns the **grade** that took it. Otherwise the job joins the backlog and the method returns `-1`.
- `finish(job)`: if this job is being worked on, it is completed and its worker becomes free. That person at once picks up the **longest-waiting** backlog job they are allowed to do (level ≤ their grade), if there is one; return that job's id, or `-1` if nothing was picked up. If `job` is still in the backlog, the client has withdrawn it: remove it and return `-1`. Unknown ids return `-1`.
- `waiting()`: number of jobs in the backlog.

**Example:** `Bureau(1,1,0)`: `submit(10,0) → 0`, `submit(11,0) → 1`, `submit(12,1) → -1`, `submit(13,0) → -1`, `finish(10) → 13` (the junior may not take job 12), `finish(11) → 12`, `waiting() → 0`
""",
'''class Bureau:
    def __init__(self, juniors: int, seniors: int, editors: int):
        self.free = [juniors, seniors, editors]
        self.active = {}
        self.backlog = {}

    def submit(self, job: int, level: int) -> int:
        for grade in range(level, 3):
            if self.free[grade] > 0:
                self.free[grade] -= 1
                self.active[job] = grade
                return grade
        self.backlog[job] = level
        return -1

    def finish(self, job: int) -> int:
        if job in self.backlog:
            del self.backlog[job]
            return -1
        if job not in self.active:
            return -1
        grade = self.active.pop(job)
        for waiting_job, level in self.backlog.items():
            if level <= grade:
                del self.backlog[waiting_job]
                self.active[waiting_job] = grade
                return waiting_job
        self.free[grade] += 1
        return -1

    def waiting(self) -> int:
        return len(self.backlog)
''',
[[["Bureau", "submit", "submit", "submit", "submit", "finish", "finish", "waiting"], [[1, 1, 0], [10, 0], [11, 0], [12, 1], [13, 0], [10], [11], []]],
 [["Bureau", "submit", "finish", "finish", "waiting"], [[0, 0, 0], [1, 0], [1], [1], []]],
 [["Bureau", "submit", "submit", "finish", "submit"], [[1, 0, 0], [1, 0], [2, 2], [1], [3, 0]]],
 [["Bureau", "submit", "submit", "submit", "finish", "finish", "finish"], [[0, 0, 1], [1, 0], [2, 2], [3, 1], [1], [2], [3]]],
 [["Bureau", "finish", "waiting"], [[2, 2, 2], [99], []]],
 [["Bureau", "submit", "submit", "submit", "finish", "waiting", "finish", "submit"], [[1, 0, 0], [1, 0], [2, 0], [3, 0], [2], [], [1], [4, 0]]],
 [["Bureau", "submit", "submit", "submit", "submit", "finish", "finish", "finish"], [[1, 1, 1], [1, 2], [2, 2], [3, 0], [4, 1], [1], [3], [4]]],
 _ops(("Bureau", [2, 1, 1]), 10, [("waiting", lambda: [])]),
 (lambda ids: [["Bureau"] + [o for o, _ in ids], [[3, 2, 1]] + [a for _, a in ids]])(
     [(("submit", [i, R.randint(0, 2)]) if R.random() < 0.55 else ("finish", [R.randint(0, i)])) for i in range(3000)]),
 (lambda ids: [["Bureau"] + [o for o, _ in ids], [[1, 1, 1]] + [a for _, a in ids]])(
     [(("submit", [i, R.randint(0, 2)]) if R.random() < 0.5 else (("finish", [R.randint(0, i)]) if R.random() < 0.9 else ("waiting", []))) for i in range(3000)]),
 (lambda ids: [["Bureau"] + [o for o, _ in ids], [[5, 0, 2]] + [a for _, a in ids]])(
     [(("submit", [i, R.choice([0, 0, 1, 2])]) if R.random() < 0.6 else ("finish", [R.randint(max(0, i - 30), i)])) for i in range(2500)])],
['''class Bureau:
    def __init__(self, juniors, seniors, editors):
        self.free = [juniors, seniors, editors]
        self.active = {}
        self.line = {}

    def submit(self, call, difficulty):
        for rank in range(difficulty, 3):
            if self.free[rank] > 0:
                self.free[rank] -= 1
                self.active[call] = rank
                return rank
        self.line[call] = difficulty
        return -1

    def finish(self, call):
        if call in self.line:
            del self.line[call]
            return -1
        if call not in self.active:
            return -1
        rank = self.active.pop(call)
        if self.line:
            waiting_call = next(iter(self.line))
            del self.line[waiting_call]
            self.active[waiting_call] = rank
            return waiting_call
        self.free[rank] += 1
        return -1

    def waiting(self):
        return len(self.line)
''', '''class Bureau:
    def __init__(self, juniors, seniors, editors):
        self.free = [juniors, seniors, editors]
        self.active = {}
        self.line = {}

    def submit(self, call, difficulty):
        if self.free[difficulty] > 0:
            self.free[difficulty] -= 1
            self.active[call] = difficulty
            return difficulty
        self.line[call] = difficulty
        return -1

    def finish(self, call):
        if call in self.line:
            del self.line[call]
            return -1
        if call not in self.active:
            return -1
        rank = self.active.pop(call)
        for waiting_call, difficulty in self.line.items():
            if difficulty <= rank:
                del self.line[waiting_call]
                self.active[waiting_call] = rank
                return waiting_call
        self.free[rank] += 1
        return -1

    def waiting(self):
        return len(self.line)
'''],
("Dictionaries that keep insertion order (Python 3.7+), and the design process in [Object-oriented design](#/lesson/interview-prep/object-oriented-design).",
 "Three facts describe the bureau: the free head-count per grade, which grade is working on each active job, and the backlog in arrival order with each job's level. Every method is a small update of those three.",
 ["Write the state down before any method. What must `finish` know about a job?",
  "A backlog job can be picked up only by a grade at least its level. The freed person scans the backlog from the oldest job.",
  "When the freed person takes a backlog job, the free count does not change at all: they go straight from one job to the next."],
 "Model every employee as an object and scan all employees for a free one on each job: O(staff) per operation and a lot of code, though it is the natural starting point when employees have names and individual queues.",
 "`submit`: first grade ≥ level with a free person, else append to `backlog`. `finish`: in the backlog → delete; active → pop its grade, scan `backlog` in order for the first level ≤ grade, hand it over; otherwise increment `free[grade]`.\n\nDry run Bureau(1,1,0): 10 → junior. 11 (level 0) → junior busy → the senior takes it (returns 1). 12 (level 1) → backlog. 13 → backlog. finish(10): the junior scans 12 (level too high), then 13 → returns 13. finish(11): the senior takes 12.",
 "`submit` O(1); `finish` O(length of the backlog) in the worst case because of the scan; space O(jobs).",
 "Giving the freed person the first backlog job regardless of level. Routing only to the exact grade instead of passing the job upward. Incrementing the free count *and* assigning a new job.",
 "Make `finish` O(1) by keeping one queue per level and comparing arrival tickets at the fronts (as in [Repair Counter](#/problem/ctci-repair-counter)). Then discuss the object model: `Employee` subclasses, a `Dispatcher`, and where the pass-upward logic should live.")),

P("flip-discs", "Flip the Discs", "Medium", "Object-Oriented Design", "placeDisc",
"""
In a disc-flipping board game, two players (`"B"` and `"W"`) place discs on a square board. Empty cells are `"."`.

When a player places a disc, look in each of the eight directions (horizontal, vertical, diagonal). If, starting next to the new disc, there is an unbroken line of **one or more opponent discs followed immediately by one of the player's own discs**, every opponent disc in that line is flipped to the player's colour.

A move is **legal** only if the cell is empty and at least one disc is flipped.

Write `placeDisc(board, row, col, colour)` where `board` is a list of equal-length strings. Return the new board (list of strings) after a legal move, or the board unchanged if the move is illegal.

**Constraints:** board side between 1 and 30.

**Example:** `board = ["....", ".WB.", ".BW.", "...."]`, `row = 0, col = 1, colour = "B"` → `[".B..", ".BB.", ".BW.", "...."]`
""",
'''class Solution:
    def placeDisc(self, board: List[str], row: int, col: int, colour: str) -> List[str]:
        n = len(board)
        grid = [list(line) for line in board]
        if grid[row][col] != ".":
            return board
        other = "W" if colour == "B" else "B"
        flips = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                line = []
                while 0 <= r < n and 0 <= c < n and grid[r][c] == other:
                    line.append((r, c))
                    r += dr
                    c += dc
                if line and 0 <= r < n and 0 <= c < n and grid[r][c] == colour:
                    flips.extend(line)
        if not flips:
            return board
        grid[row][col] = colour
        for r, c in flips:
            grid[r][c] = colour
        return ["".join(line) for line in grid]
''',
[[["....", ".WB.", ".BW.", "...."], 0, 1, "B"], [["....", ".WB.", ".BW.", "...."], 0, 0, "B"], [["....", ".WB.", ".BW.", "...."], 1, 1, "B"],
 [["."], 0, 0, "W"], [["BW.", "...", "..."], 0, 2, "B"], [["BW.", "...", "..."], 0, 2, "W"],
 [["BWW.", "....", "....", "...."], 0, 3, "B"], [["WWW.", "....", "....", "...."], 0, 3, "B"],
 [["B...", ".W..", "..W.", "...."], 3, 3, "B"], [["B.B.B", ".WWW.", "BW.WB", ".WWW.", "B.B.B"], 2, 2, "B"],
 [["B.B.B", ".WWW.", "BW.WB", ".WWW.", "B.B.B"], 2, 2, "W"], [["BW.WB", ".....", ".....", ".....", "....."], 0, 2, "B"],
 [["B.W.", "....", "....", "...."], 0, 1, "B"], [_board(30, "BW.."), 15, 15, "B"], [_board(30, "BWW."), 3, 20, "W"],
 [["W" * 29 + "."] + ["." * 30] * 28 + ["B" + "." * 29], 0, 29, "B"]],
['''class Solution:
    def placeDisc(self, board, row, col, colour):
        n = len(board)
        grid = [list(line) for line in board]
        if grid[row][col] != ".":
            return board
        other = "W" if colour == "B" else "B"
        flips = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                while 0 <= r < n and 0 <= c < n and grid[r][c] == other:
                    flips.append((r, c))
                    r += dr
                    c += dc
        if not flips:
            return board
        grid[row][col] = colour
        for r, c in flips:
            grid[r][c] = colour
        return ["".join(line) for line in grid]
''', '''class Solution:
    def placeDisc(self, board, row, col, colour):
        n = len(board)
        grid = [list(line) for line in board]
        if grid[row][col] != ".":
            return board
        other = "W" if colour == "B" else "B"
        flips = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c = row + dr, col + dc
            line = []
            while 0 <= r < n and 0 <= c < n and grid[r][c] == other:
                line.append((r, c))
                r += dr
                c += dc
            if line and 0 <= r < n and 0 <= c < n and grid[r][c] == colour:
                flips.extend(line)
        if not flips:
            return board
        grid[row][col] = colour
        for r, c in flips:
            grid[r][c] = colour
        return ["".join(line) for line in grid]
'''],
("Walking a grid in a direction `(dr, dc)`: see [Matrix tricks](#/lesson/neet-greedy-math/matrix-tricks).",
 "One rule applied eight times. Write a single piece of code that walks from the new disc in direction `(dr, dc)`, collects opponent discs, and keeps them only if the walk ends on one of your own discs. Then run it for the eight directions.",
 ["Represent a direction as a pair of steps, each −1, 0 or 1 (excluding 0, 0).",
  "Collect the cells of the current line in a temporary list; commit them only when the line is closed by your own colour.",
  "Decide legality after examining all eight directions, and only then modify the board."],
 "Eight separate blocks of copy-pasted loops, one per direction: works until one of them has a sign error that the others do not.",
 "For each direction: step while the cell holds the opponent's colour, storing coordinates. If at least one was stored and the next cell is inside the board and has your colour, add them to `flips`. No flips → illegal.\n\nDry run example: placing B at (0,1). Direction down: (1,1) is W → stored; (2,1) is B → closed → flip (1,1). Other directions collect nothing. Board becomes `.B.. / .BB. / .BW. / ....`.",
 "Each direction walks at most n cells: O(n) per move, O(n²) to copy the board.",
 "Flipping lines that run off the board or end in an empty cell. Handling only four directions. Mutating the board before knowing the move is legal.",
 "List all legal moves for a colour; decide when the game ends; design the classes (`Board`, `Piece`, `Player`, `Game`) and decide which one owns `placeDisc` and the score.")),

P("mini-fs", "Miniature File System", "Medium", "Object-Oriented Design", "MiniFS",
"""
Design an in-memory file system. Paths look like `"/docs/2024/plan.txt"`; the root directory is `"/"`. Names contain no slashes.

Implement class `MiniFS`:

- `mkdir(path)` creates one new directory. Returns `True` on success; `False` if the parent directory does not exist, the parent is a file, or something already exists at `path`.
- `addFile(path, size)` creates a file of `size` bytes under the same rules; returns `True`/`False`.
- `du(path)` returns the total size in bytes of the file at `path`, or of **everything inside** the directory at `path` (recursively). Returns `-1` if nothing exists there.
- `rm(path)` deletes the file or the directory with all its contents; returns `True`, or `False` if the path does not exist or is the root.

**Example:** `mkdir("/a") → True`, `addFile("/a/x", 5) → True`, `addFile("/b/y", 1) → False`, `mkdir("/a/s") → True`, `addFile("/a/s/z", 7) → True`, `du("/a") → 12`, `rm("/a/s") → True`, `du("/") → 5`
""",
'''class MiniFS:
    def __init__(self):
        self.root = {}

    def _walk(self, parts):
        node = self.root
        for name in parts:
            if not isinstance(node, dict) or name not in node:
                return None
            node = node[name]
        return node

    def _create(self, path, value):
        parts = [p for p in path.split("/") if p]
        if not parts:
            return False
        parent = self._walk(parts[:-1])
        if not isinstance(parent, dict) or parts[-1] in parent:
            return False
        parent[parts[-1]] = value
        return True

    def mkdir(self, path: str) -> bool:
        return self._create(path, {})

    def addFile(self, path: str, size: int) -> bool:
        return self._create(path, size)

    def du(self, path: str) -> int:
        node = self._walk([p for p in path.split("/") if p])
        if node is None:
            return -1
        total, stack = 0, [node]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                stack.extend(cur.values())
            else:
                total += cur
        return total

    def rm(self, path: str) -> bool:
        parts = [p for p in path.split("/") if p]
        if not parts:
            return False
        parent = self._walk(parts[:-1])
        if not isinstance(parent, dict) or parts[-1] not in parent:
            return False
        del parent[parts[-1]]
        return True
''',
[[["MiniFS", "mkdir", "addFile", "addFile", "mkdir", "addFile", "du", "rm", "du"],
  [[], ["/a"], ["/a/x", 5], ["/b/y", 1], ["/a/s"], ["/a/s/z", 7], ["/a"], ["/a/s"], ["/"]]],
 [["MiniFS", "du", "rm", "mkdir", "du"], [[], ["/"], ["/"], ["/"], ["/zzz"]]],
 [["MiniFS", "mkdir", "mkdir", "addFile", "addFile", "du"], [[], ["/a"], ["/a"], ["/a", 3], ["/a/f", 3], ["/a/f"]]],
 [["MiniFS", "addFile", "mkdir", "addFile", "du"], [[], ["/f", 9], ["/f/sub"], ["/f/g", 1], ["/"]]],
 [["MiniFS", "mkdir", "mkdir", "mkdir", "addFile", "rm", "du", "du", "rm"], [[], ["/a"], ["/a/b"], ["/a/b/c"], ["/a/b/c/f", 4], ["/a/b"], ["/a/b/c"], ["/a"], ["/a/b"]]],
 [["MiniFS", "addFile", "rm", "addFile", "du"], [[], ["/f", 2], ["/f"], ["/f", 6], ["/f"]]],
 [["MiniFS", "mkdir", "addFile", "addFile", "addFile", "du", "du"], [[], ["/d"], ["/d/a", 0], ["/d/b", 10], ["/c", 100], ["/d"], ["/"]]],
 _ops(("MiniFS", []), 3000, [("mkdir", lambda: [R.choice(_paths)]), ("addFile", lambda: [R.choice(_paths), R.randint(0, 50)]),
                             ("du", lambda: [R.choice(_paths + ["/"])]), ("rm", lambda: [R.choice(_paths)])]),
 _ops(("MiniFS", []), 3000, [("mkdir", lambda: [R.choice(_paths)]), ("mkdir", lambda: [R.choice(_paths)]), ("addFile", lambda: [R.choice(_paths), R.randint(0, 50)]),
                             ("addFile", lambda: [R.choice(_paths) + "/f%d" % R.randint(0, 5), 3]), ("du", lambda: [R.choice(_paths + ["/"])]), ("rm", lambda: [R.choice(_paths)])]),
 [["MiniFS"] + ["mkdir"] * 200 + ["addFile", "du", "du"], [[]] + [["/d" * (i + 1)] for i in range(200)] + [["/d" * 200 + "/f", 42], ["/d"], ["/" + "d/" * 199 + "d"]]]],
['''class MiniFS:
    def __init__(self):
        self.items = {"/": None}

    def _parent(self, path):
        return path.rsplit("/", 1)[0] or "/"

    def mkdir(self, path):
        if path in self.items or self._parent(path) not in self.items:
            return False
        self.items[path] = None
        return True

    def addFile(self, path, size):
        if path in self.items or self._parent(path) not in self.items:
            return False
        self.items[path] = size
        return True

    def du(self, path):
        if path not in self.items:
            return -1
        if self.items[path] is not None:
            return self.items[path]
        return sum(v for k, v in self.items.items() if v is not None and k.startswith(path))

    def rm(self, path):
        if path == "/" or path not in self.items:
            return False
        del self.items[path]
        return True
'''],
("Nested dictionaries as a tree, and the composite idea from [Object-oriented design](#/lesson/interview-prep/object-oriented-design).",
 "A file system is a tree: directories are inner nodes, files are leaves. Almost every operation is \"walk down the path to the parent, then do one small thing there\", so write the walk once and reuse it.",
 ["Represent a directory as a dictionary from name to child and a file as its size.",
  "Split the path on `/` and drop empty pieces; the last piece is the new name, the rest leads to the parent.",
  "`du` on a directory is a tree traversal that adds up the leaves."],
 "A flat dictionary from full path to size. Creation is easy, but `rm` and `du` on a directory must scan every path, and prefix matching confuses `/a` with `/ab`.",
 "`_walk(parts)` returns the node or `None`. `_create` validates the parent (must be a dictionary, name must be new). `du` uses an explicit stack. `rm` deletes one key from the parent, which drops the whole subtree.\n\nDry run: mkdir /a → root {a: {}}. addFile /a/x 5 → {a: {x: 5}}. addFile /b/y → parent missing → False. du /a after adding /a/s/z = 7 → 5 + 7 = 12. rm /a/s → du / = 5.",
 "`mkdir`, `addFile`, `rm`: O(path depth). `du`: O(size of the subtree).",
 "Treating a file as a possible parent. Leaving the children behind when a directory is removed (the flat wrong solution does this, and also matches `/a` as a prefix of `/a2`). Removing the root.",
 "Make `du` O(depth) by caching a size in each directory and updating ancestors on every change. In an interview, name the classes: an abstract `Entry` with `File` and `Directory` subclasses is the composite pattern.")),
]
