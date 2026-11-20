import random

_r = random.Random(191)


def _single(n, lo=-30000, hi=30000):
    vals = _r.sample(range(lo, hi + 1), n + 1)
    arr = vals[:n] * 2 + [vals[n]]
    _r.shuffle(arr)
    return arr


def _missing(n):
    arr = list(range(n + 1))
    arr.remove(_r.randint(0, n))
    _r.shuffle(arr)
    return arr


PROBLEMS = [
# ------------------------------------------------------------------ Single Number
dict(
    id="single-number",
    title="Single Number",
    difficulty="Easy",
    pattern="Bit Manipulation / XOR",
    leetcode="https://leetcode.com/problems/single-number/",
    neetcode="https://neetcode.io/problems/single-number",
    entry="singleNumber",
    description=r"""
In the non-empty array `nums` every value appears **exactly twice**, except for one value that
appears once. Return that value. Aim for linear time and constant extra space.

**Constraints**
- `1 <= len(nums) <= 3·10^4` (always odd), `-3·10^4 <= nums[i] <= 3·10^4`

**Example 1:** `nums = [4,1,2,1,2]` → `4`.

**Example 2:** `nums = [7]` → `7`.
""",
    starter='''class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def singleNumber(self, nums):
        acc = 0
        for x in nums:
            acc ^= x          # pairs cancel: a ^ a == 0
        return acc
''',
    tests=[
        [[4, 1, 2, 1, 2]],
        [[7]],
        [[2, 2, 1]],
        [[-1, -1, -2]],
        [[0, 5, 5]],
        [[30000, -30000, 30000]],
        [[1, 0, 1]],
        [[-4, 3, 3]],
        [[9, 8, 7, 8, 9]],
        [[6, 6, 0, 1, 1]],
        [_single(10000)],
        [_single(14999)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def singleNumber(self, nums):
        return sum(set(nums)) - sum(nums)
''',
        '''class Solution:
    def singleNumber(self, nums):
        nums = sorted(nums)
        for i in range(0, len(nums) - 1, 2):
            if nums[i] != nums[i + 1]:
                return nums[i + 1]        # should be nums[i]
        return nums[-1]
''',
    ],
    guide=dict(
        prereqs="The XOR operator `^` and its algebra (lesson *Bit tricks for interviews*).",
        intuition=r"""
XOR is addition without carries, bit by bit. It is commutative and associative, `a ^ a = 0` and
`a ^ 0 = a`. So XOR-ing the whole array lets you mentally reorder it so every pair sits together and
cancels to 0; what survives is the lone value.
""",
        hints=[
            "A hash set solves it in O(n) space. What operation makes equal values cancel?",
            "x ^ x == 0 and x ^ 0 == x, in any order.",
            "XOR everything together and return the result.",
        ],
        brute_force="Count occurrences with a dict / `Counter` (O(n) space), or sort and compare neighbours (O(n log n)). `2*sum(set(nums)) - sum(nums)` also works with O(n) space.",
        approach=r"""
**Dry run** `[4,1,2,1,2]` in binary: `100 ^ 001 = 101`, `^ 010 = 111`, `^ 001 = 110`, `^ 010 = 100` → **4**.

Negative numbers are fine: Python's `^` behaves as if ints were infinitely sign-extended two's
complement, and the cancellation argument does not depend on the sign.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="Using `+`/`-` tricks with a set costs O(n) space. Remember `^` is XOR in Python, not power.",
        follow_up="*Single Number II* (others appear three times — count bits mod 3), *Single Number III* (two singles — split by a set bit of the XOR), *Missing Number*.",
    ),
),
# ------------------------------------------------------------------ Number of 1 Bits
dict(
    id="number-of-1-bits",
    title="Number of 1 Bits",
    difficulty="Easy",
    pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/number-of-1-bits/",
    neetcode="https://neetcode.io/problems/number-of-one-bits",
    entry="hammingWeight",
    description=r"""
Given a non-negative integer `n` that fits in 32 bits (unsigned), return how many bits of its
binary representation are `1` (its *Hamming weight* or *popcount*). Try not to lean on
`bin(n).count("1")` / `int.bit_count()` — the point is the bit manipulation.

**Constraints**
- `0 <= n <= 2^32 - 1`

**Example 1:** `n = 11` (binary `1011`) → `3`.

**Example 2:** `n = 128` (binary `10000000`) → `1`.
""",
    starter='''class Solution:
    def hammingWeight(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def hammingWeight(self, n):
        count = 0
        while n:
            n &= n - 1        # clears the lowest set bit
            count += 1
        return count
''',
    tests=[
        [11], [128], [0], [1], [2147483645], [4294967295], [2147483648], [255], [256],
        [1431655765], [2863311530], [4294967294], [3],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def hammingWeight(self, n):
        return len(bin(n)) - 2            # counts all bits, not the ones
''',
        '''class Solution:
    def hammingWeight(self, n):
        count = 0
        for i in range(31):               # misses bit 31
            count += (n >> i) & 1
        return count
''',
    ],
    guide=dict(
        prereqs="`&`, `>>`, and the `x & (x - 1)` identity (lesson *Bit tricks for interviews*).",
        intuition=r"""
Subtracting 1 flips the lowest set bit to 0 and all the zeros below it to 1. AND-ing with the original
therefore erases exactly that lowest set bit and nothing else. Repeat until the number is 0 and count
the iterations — one per set bit.
""",
        hints=[
            "Simple: check n & 1, then shift right, 32 times.",
            "What does n - 1 look like in binary compared to n?",
            "n &= n - 1 removes one set bit per iteration; count the iterations.",
        ],
        brute_force="Loop over all 32 positions: `count += (n >> i) & 1`. That is already O(32); the trick below runs once per **set** bit instead.",
        approach=r"""
**Dry run** `n = 1011₂` (11):
- `1011 & 1010 = 1010` (count 1)
- `1010 & 1001 = 1000` (count 2)
- `1000 & 0111 = 0000` (count 3) → **3**.

This is Brian Kernighan's method.
""",
        complexity="Time **O(k)** where k = number of set bits (≤ 32); space O(1).",
        pitfalls=r"""
- Looping `range(31)` forgets the top bit.
- In languages with signed 32-bit ints, `n >> 1` on a negative value is an arithmetic shift and may
  never reach 0; Python's input here is non-negative so both loops terminate.
""",
        follow_up="*Counting Bits* (popcount for all 0..n via DP), *Hamming Distance* (`popcount(x ^ y)`), *Power of Two* (`n > 0 and n & (n-1) == 0`).",
    ),
),
# ------------------------------------------------------------------ Counting Bits
dict(
    id="counting-bits",
    title="Counting Bits",
    difficulty="Easy",
    pattern="Bit Manipulation / DP",
    leetcode="https://leetcode.com/problems/counting-bits/",
    neetcode="https://neetcode.io/problems/counting-bits",
    entry="countBits",
    description=r"""
Given `n`, return a list `ans` of length `n + 1` where `ans[i]` is the number of `1` bits in the
binary form of `i`, for every `0 <= i <= n`. Aim for `O(n)` total — not `O(n log n)`.

**Constraints**
- `0 <= n <= 10^5`

**Example 1:** `n = 2` → `[0,1,1]`.

**Example 2:** `n = 5` → `[0,1,1,2,1,2]`.
""",
    starter='''class Solution:
    def countBits(self, n: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def countBits(self, n):
        ans = [0] * (n + 1)
        for i in range(1, n + 1):
            ans[i] = ans[i >> 1] + (i & 1)     # drop the last bit, add it back
        return ans
''',
    tests=[[2], [5], [0], [1], [8], [15], [16], [31], [100], [1023], [1024], [20000], [100000]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def countBits(self, n):
        ans = [0] * (n + 1)
        for i in range(1, n + 1):
            ans[i] = ans[i - 1] + (i & 1)       # wrong recurrence
        return ans
''',
        '''class Solution:
    def countBits(self, n):
        return [bin(i).count("1") for i in range(n)]   # off by one: misses n
''',
    ],
    guide=dict(
        prereqs="*Number of 1 Bits*; one-dimensional DP.",
        intuition=r"""
Every number is a smaller number with one more bit attached. `i >> 1` is `i` without its last bit —
and it is smaller than `i`, so its answer is already known. Hence
`bits(i) = bits(i >> 1) + (i & 1)`. Another equally good recurrence: `bits(i) = bits(i & (i-1)) + 1`
(remove the lowest set bit).
""",
        hints=[
            "Calling popcount for every i costs O(n log n). Can ans[i] reuse an earlier answer?",
            "How are the bits of i related to the bits of i // 2?",
            "ans[i] = ans[i >> 1] + (i & 1).",
        ],
        brute_force="Run *Number of 1 Bits* on every `i`: O(n log n).",
        approach=r"""
**Dry run** to 5:

| i | binary | i>>1 | ans[i>>1] | i&1 | ans[i] |
|---|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 1 | 1 |
| 2 | 10 | 1 | 1 | 0 | 1 |
| 3 | 11 | 1 | 1 | 1 | 2 |
| 4 | 100 | 2 | 1 | 0 | 1 |
| 5 | 101 | 2 | 1 | 1 | 2 |
""",
        complexity="Time **O(n)**, space O(n) for the output.",
        pitfalls="`range(n)` instead of `range(n + 1)`; using `ans[i-1]` (not a valid relation).",
        follow_up="Third recurrence via the highest power of two: `ans[i] = 1 + ans[i - offset]`. Total number of set bits from 0..n in O(log n) by counting per bit position.",
    ),
),
# ------------------------------------------------------------------ Reverse Bits
dict(
    id="reverse-bits",
    title="Reverse Bits",
    difficulty="Easy",
    pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/reverse-bits/",
    neetcode="https://neetcode.io/problems/reverse-bits",
    entry="reverseBits",
    description=r"""
Treat the non-negative integer `n` as a **32-bit unsigned** word (pad with leading zeros to 32
bits). Return the integer obtained by reversing the order of those 32 bits: bit 0 becomes bit 31,
bit 1 becomes bit 30, and so on.

**Constraints**
- `0 <= n <= 2^32 - 1`

**Example 1:** `n = 43261596` (`00000010100101000001111010011100`) → `964176192`
(`00111001011110000010100101000000`).

**Example 2:** `n = 1` → `2147483648` (the single 1 moves to the top bit).
""",
    starter='''class Solution:
    def reverseBits(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def reverseBits(self, n):
        res = 0
        for _ in range(32):
            res = (res << 1) | (n & 1)    # append n's lowest bit to res
            n >>= 1
        return res
''',
    tests=[
        [43261596], [1], [0], [4294967293], [4294967295], [2147483648], [2], [65535], [4294901760],
        [2863311530], [305419896], [3], [16777216],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def reverseBits(self, n):
        return int(bin(n)[2:][::-1], 2)       # forgets to pad to 32 bits
''',
        '''class Solution:
    def reverseBits(self, n):
        res = 0
        while n:                              # stops early: leading zeros never shifted in
            res = (res << 1) | (n & 1)
            n >>= 1
        return res
''',
    ],
    guide=dict(
        prereqs="Shifts and masks (lesson *Bits in Python*).",
        intuition="Pop bits off the low end of `n` and push them onto the low end of `res`. The first bit popped is pushed first and ends up shifted furthest left. The loop must run exactly 32 times so that leading zeros of `n` become trailing zeros of the result.",
        hints=[
            "Extract the lowest bit with n & 1.",
            "Build the answer by shifting it left and OR-ing in each extracted bit.",
            "Run exactly 32 iterations, even after n becomes 0.",
        ],
        brute_force="`int(format(n, '032b')[::-1], 2)` — string conversion; fine in Python but not what the interviewer wants.",
        approach=r"""
**Dry run** with 4-bit words, `n = 0011`: res `0` → `1` → `11` → `110` → `1100`. Reversed ✔.

**Divide-and-conquer mask version** (constant number of operations):
```
n = (n >> 16) | (n << 16) & 0xFFFFFFFF
n = ((n & 0xFF00FF00) >> 8) | ((n & 0x00FF00FF) << 8)
n = ((n & 0xF0F0F0F0) >> 4) | ((n & 0x0F0F0F0F) << 4)
n = ((n & 0xCCCCCCCC) >> 2) | ((n & 0x33333333) << 2)
n = ((n & 0xAAAAAAAA) >> 1) | ((n & 0x55555555) << 1)
```
Swap halves, then bytes, nibbles, pairs, single bits.
""",
        complexity="Time **O(32) = O(1)**, space O(1).",
        pitfalls="Looping `while n` loses leading zeros. In Python, left shifts never drop bits, so mask with `0xFFFFFFFF` in the swap version.",
        follow_up="If called many times: cache reversed bytes in a 256-entry table and combine four lookups.",
    ),
),
# ------------------------------------------------------------------ Missing Number
dict(
    id="missing-number",
    title="Missing Number",
    difficulty="Easy",
    pattern="Bit Manipulation / math",
    leetcode="https://leetcode.com/problems/missing-number/",
    neetcode="https://neetcode.io/problems/missing-number",
    entry="missingNumber",
    description=r"""
`nums` holds `n` **distinct** integers taken from the range `0..n` inclusive, so exactly one number
of that range is absent. Return it, using `O(1)` extra space and `O(n)` time.

**Constraints**
- `1 <= n <= 10^4` (tests go a bit larger)

**Example 1:** `nums = [3,0,1]` → `2`.

**Example 2:** `nums = [0,1]` → `2`. `nums = [1]` → `0`.
""",
    starter='''class Solution:
    def missingNumber(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def missingNumber(self, nums):
        acc = len(nums)                 # start with n, the index that never appears in the loop
        for i, x in enumerate(nums):
            acc ^= i ^ x                # every present value cancels against its own index
        return acc
''',
    tests=[
        [[3, 0, 1]],
        [[0, 1]],
        [[1]],
        [[0]],
        [[9, 6, 4, 2, 3, 5, 7, 0, 1]],
        [[1, 2]],
        [[0, 2]],
        [[2, 0, 3, 4]],
        [[1, 2, 3, 4, 5]],
        [_missing(10000)],
        [_missing(20000)],
        [list(range(10000))],
        [list(range(1, 10001))],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def missingNumber(self, nums):
        for i, x in enumerate(sorted(nums)):
            if i != x:
                return i
        return 0                          # should be n when nothing mismatches
''',
        '''class Solution:
    def missingNumber(self, nums):
        acc = 0
        for i, x in enumerate(nums):
            acc ^= i ^ x                  # forgets to include n itself
        return acc
''',
    ],
    guide=dict(
        prereqs="*Single Number* (XOR cancellation); the sum formula `n(n+1)/2`.",
        intuition=r"""
Put the indices `0..n` and the values side by side. Every number except the missing one appears twice
(once as an index, once as a value); the missing one appears once. That is exactly *Single Number* —
XOR everything. Alternatively, the missing value is `n(n+1)/2 − sum(nums)`.
""",
        hints=[
            "What would the sum be if nothing were missing?",
            "XOR of 0..n combined with XOR of the array leaves only the missing value.",
            "acc = n; for i, x: acc ^= i ^ x.",
        ],
        brute_force="Put values in a set and test `0..n` — O(n) space; or sort — O(n log n).",
        approach=r"""
**Dry run** `[3,0,1]`, n = 3: acc = 3; i=0: `3 ^ 0 ^ 3 = 0`; i=1: `0 ^ 1 ^ 0 = 1`; i=2: `1 ^ 2 ^ 1 = 2` → **2**.

Sum version: `3·4/2 − (3+0+1) = 6 − 4 = 2`. In fixed-width languages the XOR version cannot overflow;
in Python both are safe.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="Forgetting to fold in `n` itself (indices only go to n−1). Returning 0 as a default when the missing number is actually `n`.",
        follow_up="*Find the Duplicate Number*, *First Missing Positive* (index-as-hash), *Find All Numbers Disappeared in an Array*.",
    ),
),
# ------------------------------------------------------------------ Sum of Two Integers
dict(
    id="sum-of-two-integers",
    title="Sum of Two Integers",
    difficulty="Medium",
    pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/sum-of-two-integers/",
    neetcode="https://neetcode.io/problems/sum-of-two-integers",
    entry="getSum",
    description=r"""
Return `a + b` **without using the operators `+` or `-`** (nor `sum`, `sub`, etc.). Either
argument may be negative.

Python note: ints are unbounded, so the classic "XOR plus shifted carry" loop never terminates for
some negative inputs unless you **mask to 32 bits** and convert the result back to a signed value.

**Constraints**
- `-1000 <= a, b <= 1000` (tests also include values near the 32-bit limits whose sum still fits
  in a signed 32-bit integer)

**Example 1:** `a = 1, b = 2` → `3`.

**Example 2:** `a = -2, b = 3` → `1`.
""",
    starter='''class Solution:
    def getSum(self, a: int, b: int) -> int:
        pass
''',
    solution='''class Solution:
    def getSum(self, a, b):
        MASK = 0xFFFFFFFF            # keep only 32 bits
        MAX = 0x7FFFFFFF             # largest positive signed 32-bit value
        a &= MASK
        b &= MASK
        while b:
            carry = (a & b) << 1     # positions that generate a carry
            a = (a ^ b) & MASK       # sum without carries
            b = carry & MASK
        return a if a <= MAX else ~(a ^ MASK)   # reinterpret as signed
''',
    tests=[
        [1, 2], [-2, 3], [0, 0], [-1, 1], [-1, -1], [1000, 1000], [-1000, -1000], [-1000, 1000],
        [999, -1000], [5, -9], [0, -7], [2147483647, -1], [-2147483648, 2147483647], [-12, -8],
        [1, -2147483648], [123456, 654321],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def getSum(self, a, b):
        MASK = 0xFFFFFFFF
        a &= MASK; b &= MASK
        while b:
            a, b = (a ^ b) & MASK, ((a & b) << 1) & MASK
        return a                      # never converts back to signed
''',
        '''class Solution:
    def getSum(self, a, b):
        return a | b
''',
        '''class Solution:
    def getSum(self, a, b):
        return a ^ b                  # drops every carry
''',
    ],
    guide=dict(
        prereqs="Lesson *Bits in Python*: two's complement, masks, and why Python ints behave as infinitely sign-extended.",
        intuition=r"""
Add two bits: the **sum bit** is `a ^ b` and the **carry** is `a & b`, which belongs one position to
the left. So `a + b = (a ^ b) + ((a & b) << 1)`. That still contains a `+`, but the new second operand
has at least one more trailing zero each round, so repeating the step eventually makes the carry 0 —
*in a fixed-width word*. Hardware adders work exactly this way.

In Python a negative number has infinitely many leading 1s, so the carry can keep travelling left
forever. Fix: work modulo 2³² (`& 0xFFFFFFFF`), then if bit 31 of the result is set, map the unsigned
pattern back to its negative value.
""",
        hints=[
            "What are the sum bit and the carry bit when you add two single bits?",
            "Loop: a, b = a ^ b, (a & b) << 1 until b == 0.",
            "In Python mask both to 32 bits each round, and at the end convert: if a > 0x7FFFFFFF, return ~(a ^ 0xFFFFFFFF).",
        ],
        brute_force="There is no meaningful brute force — the naive answer `a + b` is forbidden. (Looping `b` times with an increment built from bit ops would be O(|b|).)",
        approach=r"""
**Dry run** `a = 5 (0101)`, `b = 3 (0011)`:

| a | b | a ^ b | (a & b) << 1 |
|---|---|---|---|
| 0101 | 0011 | 0110 | 0010 |
| 0110 | 0010 | 0100 | 0100 |
| 0100 | 0100 | 0000 | 1000 |
| 0000 | 1000 | 1000 | 0000 |

Result `1000₂ = 8` ✔.

**Negative example** `a = -1, b = 1`: masked, `a = 0xFFFFFFFF`. The carry ripples through all 32 bits
and is finally cut off by the mask, leaving `a = 0`.

**Sign conversion.** If `a > 0x7FFFFFFF`, the 32-bit pattern represents `a − 2³²`. The expression
`~(a ^ MASK)` computes exactly that: `a ^ MASK` flips the low 32 bits (giving `2³² − 1 − a`), and `~x`
is `−x − 1`, so the result is `a − 2³²`.
""",
        complexity="Time **O(32) = O(1)** — the carry moves left at least one position per round. Space O(1).",
        pitfalls=r"""
- Without the mask, `getSum(-1, 1)` loops forever in Python.
- Returning the unsigned pattern (e.g. 4294967295 instead of −1).
- `a - 2**32` uses a forbidden `-`; use `~(a ^ MASK)`.
""",
        follow_up="Subtraction: `a + (~b + 1)` using the same adder. *Add Binary* (strings), *Divide Two Integers* (no `*` `/` `%`).",
    ),
),
# ------------------------------------------------------------------ Reverse Integer
dict(
    id="reverse-integer",
    title="Reverse Integer",
    difficulty="Medium",
    pattern="Math / overflow simulation",
    leetcode="https://leetcode.com/problems/reverse-integer/",
    neetcode="https://neetcode.io/problems/reverse-integer",
    entry="reverse",
    description=r"""
Given a signed 32-bit integer `x`, return the integer whose decimal digits are those of `x` in
reverse order, keeping the sign. If the reversed value falls outside the signed 32-bit range
`[-2^31, 2^31 - 1]`, return `0`. Pretend you may not store 64-bit values: detect overflow **before**
it happens.

**Constraints**
- `-2^31 <= x <= 2^31 - 1`

**Example 1:** `x = 123` → `321`. `x = -123` → `-321`.

**Example 2:** `x = 120` → `21`. `x = 1534236469` → `0` (9646324351 does not fit).
""",
    starter='''class Solution:
    def reverse(self, x: int) -> int:
        pass
''',
    solution='''class Solution:
    def reverse(self, x):
        INT_MAX = 2 ** 31 - 1
        sign = -1 if x < 0 else 1
        x = abs(x)
        res = 0
        while x:
            x, d = divmod(x, 10)
            # would res * 10 + d exceed the limit?  (limit is INT_MAX, or INT_MAX + 1 for negatives)
            limit = INT_MAX if sign == 1 else INT_MAX + 1
            if res > (limit - d) // 10:
                return 0
            res = res * 10 + d
        return sign * res
''',
    tests=[
        [123], [-123], [120], [1534236469], [0], [-2147483648], [2147483647], [1463847412],
        [-1463847412], [1563847412], [7], [-10], [1000000003], [-2147483412],
        [2147483641], [-1563847412],
    ],
    examples=4,
    wrong_solutions=[
        '''class Solution:
    def reverse(self, x):
        s = str(abs(x))[::-1]
        return int(s) if x >= 0 else -int(s)       # no overflow check
''',
        '''class Solution:
    def reverse(self, x):
        res = 0
        while x:
            x, d = divmod(x, 10)                   # Python floors: wrong for negatives
            res = res * 10 + d
            if res > 2 ** 31 - 1: return 0
        return res
''',
    ],
    guide=dict(
        prereqs="Digit extraction with `% 10` and `// 10`; signed 32-bit range (lesson *Bits in Python*).",
        intuition=r"""
Pop the last digit of `x` and push it onto `res` (`res = res*10 + d`). The only subtlety is overflow:
before pushing, check whether `res*10 + d` would exceed the limit, i.e. whether
`res > (limit − d) // 10`. Working on `abs(x)` and restoring the sign sidesteps Python's floor
division on negatives.
""",
        hints=[
            "Peel digits with divmod(x, 10) and build the result with res = res*10 + d.",
            "Python's // and % round toward negative infinity — handle the sign separately.",
            "Check res > (limit - d) // 10 before multiplying; return 0 on overflow.",
        ],
        brute_force="Convert to string, reverse, convert back, then range-check — simple and accepted in Python, but it relies on big ints, which the problem asks you to pretend you do not have.",
        approach=r"""
**Dry run** `x = 1534236469`: digits popped 9,6,4,6,3,2,4,3,5,1. After nine pushes
`res = 964632435`; pushing `1` would need `res ≤ (2147483647 − 1)//10 = 214748364` — it is not → **0**.

`x = -123`: sign −1, work on 123 → 321 → **−321**.

In Python, `-123 % 10 == 7` and `-123 // 10 == -13`, unlike C/Java where they are `-3` and `-12`.
""",
        complexity="Time **O(log₁₀ |x|)** (≤ 10 digits), space O(1).",
        pitfalls=r"""
- Floor division/modulo on negatives in Python.
- Checking overflow *after* the multiplication defeats the "32-bit only" premise.
- Trailing zeros vanish naturally (`120 → 21`); no special case needed.
- The negative range is one larger than the positive one (−2³¹ is allowed, 2³¹ is not).
""",
        follow_up="*String to Integer (atoi)* (same overflow guard), *Palindrome Number* (reverse half the digits).",
    ),
),
]
