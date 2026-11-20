import random

_r = random.Random(1071)


def _to_roman(n):
    out = []
    for v, s in [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                 (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


_bin_a = "1" + "".join(_r.choice("01") for _ in range(9999))
_bin_b = "1" + "".join(_r.choice("01") for _ in range(7000))
_robot_big = "".join(_r.choice("GLR") for _ in range(100))


def _thrice(n):
    vals = _r.sample(range(-2 ** 31, 2 ** 31), n + 1)
    arr = vals[:n] * 3 + [vals[n]]
    _r.shuffle(arr)
    return arr


def _twice_two(n):
    vals = _r.sample(range(-2 ** 31, 2 ** 31), n + 2)
    arr = vals[:n] * 2 + vals[n:]
    _r.shuffle(arr)
    return arr


_xor_big = [_r.randint(0, 2 ** 31 - 1) for _ in range(5000)]
_utf_ok = []
for _ in range(3000):
    k = _r.choice([1, 2, 3, 4])
    if k == 1:
        _utf_ok.append(_r.randint(0, 127))
    else:
        _utf_ok.append({2: 0b11000000, 3: 0b11100000, 4: 0b11110000}[k] | _r.randint(0, (1 << (7 - k)) - 1))
        _utf_ok.extend(0b10000000 | _r.randint(0, 63) for _ in range(k - 1))

PROBLEMS = [
# ================================================================== MATH
dict(
    id="excel-sheet-column-title",
    title="Excel Sheet Column Title",
    difficulty="Easy",
    pattern="Math / base conversion",
    leetcode="https://leetcode.com/problems/excel-sheet-column-title/",
    entry="convertToTitle",
    description=r"""
Spreadsheet columns are labelled `A, B, …, Z, AA, AB, …, AZ, BA, …, ZZ, AAA, …`. Given a positive
column number (`A` is 1, `Z` is 26, `AA` is 27), return its label.

**Constraints**
- `1 <= columnNumber <= 2^31 - 1`

**Example 1:** `1` → `"A"`, `28` → `"AB"`.

**Example 2:** `701` → `"ZY"`, `2147483647` → `"FXSHRXW"`.
""",
    starter='''class Solution:
    def convertToTitle(self, columnNumber: int) -> str:
        pass
''',
    solution='''class Solution:
    def convertToTitle(self, columnNumber):
        letters = []
        n = columnNumber
        while n > 0:
            n -= 1                         # shift 1..26 down to 0..25
            n, r = divmod(n, 26)
            letters.append(chr(ord("A") + r))
        return "".join(reversed(letters))
''',
    tests=[[1], [28], [701], [2147483647], [26], [27], [52], [53], [702], [703], [18278], [18279], [676], [677]],
    examples=4,
    wrong_solutions=[
        '''class Solution:
    def convertToTitle(self, columnNumber):
        letters, n = [], columnNumber
        while n > 0:
            n, r = divmod(n, 26)           # no "minus one": breaks on multiples of 26
            letters.append(chr(ord("A") + r - 1))
        return "".join(reversed(letters))
''',
        '''class Solution:
    def convertToTitle(self, columnNumber):
        letters, n = [], columnNumber - 1  # subtracts one only once
        while True:
            n, r = divmod(n, 26)
            letters.append(chr(ord("A") + r))
            if n == 0: break
        return "".join(reversed(letters))
''',
    ],
    guide=dict(
        prereqs="Digit peeling with `divmod` (lesson *Interview number theory*).",
        intuition=r"""
This looks like writing a number in base 26, but there is no zero digit: the "digits" run from 1 (A)
to 26 (Z). Such a system is called *bijective base 26*. The fix is small: before extracting each
digit, subtract 1, so that 1..26 becomes 0..25 and ordinary `% 26` and `// 26` work.
""",
        hints=[
            "Try ordinary base-26 conversion on 26 and see what goes wrong.",
            "The letters stand for 1..26, not 0..25.",
            "Each round: n -= 1; n, r = divmod(n, 26); emit chr(65 + r). Reverse at the end.",
        ],
        brute_force="Count up label by label from A — O(n) labels, hopeless for two billion.",
        approach=r"""
**Dry run** `701`: n=700 → divmod = (26, 24) → `Y`; n=26 → 25 → divmod = (0, 25) → `Z`. Reversed: **"ZY"**.

**Dry run** `26`: n=25 → (0, 25) → `Z`. Without the `−1` you would get remainder 0 and no letter for it.
""",
        complexity="Time **O(log₂₆ n)** — at most 7 letters for 32-bit input. Space O(1).",
        pitfalls="Multiples of 26 (`Z`, `AZ`, `ZZ`) are where the off-by-one shows. The subtraction must happen in **every** round.",
        follow_up="*Excel Sheet Column Number* is the inverse: `res = res * 26 + (ord(ch) - 64)`.",
    ),
),
dict(
    id="palindrome-number",
    title="Palindrome Number",
    difficulty="Easy",
    pattern="Math / digit reversal",
    leetcode="https://leetcode.com/problems/palindrome-number/",
    entry="isPalindrome",
    description=r"""
Return `True` if the integer `x` reads the same from left to right and from right to left in
decimal. Negative numbers are never palindromes (the minus sign would have to appear at the end).
Try to do it without converting the number to a string.

**Constraints**
- `-2^31 <= x <= 2^31 - 1`

**Example 1:** `121` → `True`.

**Example 2:** `-121` → `False`, `10` → `False`.
""",
    starter='''class Solution:
    def isPalindrome(self, x: int) -> bool:
        pass
''',
    solution='''class Solution:
    def isPalindrome(self, x):
        if x < 0 or (x % 10 == 0 and x != 0):   # negatives, and numbers ending in 0, cannot be
            return False
        half = 0
        while x > half:                          # move digits from x to half until half catches up
            half = half * 10 + x % 10
            x //= 10
        return x == half or x == half // 10      # even length, or odd length (drop middle digit)
''',
    tests=[[121], [-121], [10], [0], [7], [11], [12], [1221], [12321], [123321], [1000021], [2147447412],
           [2147483647], [-1], [100], [1001]],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def isPalindrome(self, x):
        return str(abs(x)) == str(abs(x))[::-1]        # accepts negatives
''',
        '''class Solution:
    def isPalindrome(self, x):
        if x < 0: return False
        half = 0
        while x > half:
            half = half * 10 + x % 10
            x //= 10
        return x == half or x == half // 10            # 10, 100 slip through
''',
    ],
    guide=dict(
        prereqs="Digit peeling and pushing (`% 10`, `// 10`, `res*10 + d`). *Reverse Integer*.",
        intuition=r"""
You could reverse all the digits and compare, but in a fixed-width language the reversed number can
overflow. Reversing only the **second half** avoids that: pop digits off the end of `x` and push
them onto `half` until `half` is at least as large as what remains of `x`. For a palindrome the two
halves are then equal (even length) or equal after dropping the middle digit from `half` (odd length).
""",
        hints=[
            "Which inputs can you reject immediately?",
            "Reverse only half of the digits.",
            "Stop when x <= half; compare x == half or x == half // 10.",
        ],
        brute_force="`s = str(x); return s == s[::-1]` — fine in practice, O(d) extra space, but it dodges the arithmetic the question is about.",
        approach=r"""
**Dry run** `12321`: (x, half) = (1232, 1) → (123, 12) → (12, 123). Stop. `12 == 123 // 10` → **True**.

**Dry run** `10`: ends in 0 and is not 0 → **False** (otherwise half would become 01 = 1 and match).
""",
        complexity="Time **O(log₁₀ x)** — half the digits. Space O(1).",
        pitfalls="Numbers ending in 0 (`10`, `100`) need the explicit early rejection; `0` itself is a palindrome.",
        follow_up="*Valid Palindrome* (strings), *Palindrome Linked List* (reverse the second half — the same idea).",
    ),
),
dict(
    id="roman-to-integer",
    title="Roman to Integer",
    difficulty="Easy",
    pattern="Math / string scan",
    leetcode="https://leetcode.com/problems/roman-to-integer/",
    neetcode="https://neetcode.io/problems/roman-to-integer",
    entry="romanToInt",
    description=r"""
Roman numerals use seven symbols: `I`=1, `V`=5, `X`=10, `L`=50, `C`=100, `D`=500, `M`=1000.
Symbols are normally written from largest to smallest and added up. When a smaller symbol stands
directly **before** a larger one it is subtracted instead: `IV`=4, `IX`=9, `XL`=40, `XC`=90,
`CD`=400, `CM`=900. Convert a valid numeral `s` to an integer.

**Constraints**
- `1 <= len(s) <= 15`, `s` is a valid numeral for a number in `1..3999`.

**Example 1:** `"III"` → `3`, `"LVIII"` → `58`.

**Example 2:** `"MCMXCIV"` → `1994` (M + CM + XC + IV).
""",
    starter='''class Solution:
    def romanToInt(self, s: str) -> int:
        pass
''',
    solution='''class Solution:
    def romanToInt(self, s):
        value = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        total = 0
        for i, ch in enumerate(s):
            v = value[ch]
            if i + 1 < len(s) and v < value[s[i + 1]]:
                total -= v            # smaller before larger: subtract
            else:
                total += v
        return total
''',
    tests=[["III"], ["LVIII"], ["MCMXCIV"], ["I"], ["IV"], ["IX"], ["XL"], ["XC"], ["CD"], ["CM"],
           ["MMMCMXCIX"], ["MMMDCCCLXXXVIII"], ["XIV"], ["CDXLIV"]] + [[_to_roman(n)] for n in (2024, 1666, 49)],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def romanToInt(self, s):
        value = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        return sum(value[c] for c in s)
''',
        '''class Solution:
    def romanToInt(self, s):
        value = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        total = 0
        for i, ch in enumerate(s):
            if i > 0 and value[s[i - 1]] < value[ch]:
                total += value[ch] - value[s[i - 1]]      # forgets it already added the smaller one
            else:
                total += value[ch]
        return total
''',
    ],
    guide=dict(
        prereqs="Dictionaries; scanning a string with a look-ahead.",
        intuition="Every symbol contributes its value — positively in the normal case, negatively when the symbol right after it is larger. So one pass with a peek at the next character is enough.",
        hints=[
            "Map each symbol to its value with a dict.",
            "When is a symbol subtracted rather than added?",
            "If value[s[i]] < value[s[i+1]], subtract it; otherwise add it.",
        ],
        brute_force="Replace the six subtractive pairs with placeholder symbols first (`IV` → 4 …) and then sum — works, but needs several passes.",
        approach=r"""
**Dry run** `"MCMXCIV"`: M +1000; C (< M) −100; M +1000; X (< C) −10; C +100; I (< V) −1; V +5 →
1000 − 100 + 1000 − 10 + 100 − 1 + 5 = **1994**.
""",
        complexity="Time **O(n)**, space O(1).",
        pitfalls="Index out of range on the last symbol; double counting when you look backwards instead of forwards.",
        follow_up="*Integer to Roman* (the inverse, greedy).",
    ),
),
dict(
    id="integer-to-roman",
    title="Integer to Roman",
    difficulty="Medium",
    pattern="Math / greedy",
    leetcode="https://leetcode.com/problems/integer-to-roman/",
    neetcode="https://neetcode.io/problems/integer-to-roman",
    entry="intToRoman",
    description=r"""
Write the integer `num` as a Roman numeral. Symbols: `I`=1, `V`=5, `X`=10, `L`=50, `C`=100,
`D`=500, `M`=1000. A symbol may be repeated at most three times in a row, so 4 and 9 at each decimal
place use the subtractive forms `IV`, `IX`, `XL`, `XC`, `CD`, `CM`.

**Constraints**
- `1 <= num <= 3999`

**Example 1:** `3749` → `"MMMDCCXLIX"`.

**Example 2:** `58` → `"LVIII"`, `1994` → `"MCMXCIV"`.
""",
    starter='''class Solution:
    def intToRoman(self, num: int) -> str:
        pass
''',
    solution='''class Solution:
    def intToRoman(self, num):
        table = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                 (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        out = []
        for value, symbol in table:          # largest piece first
            count, num = divmod(num, value)
            out.append(symbol * count)
        return "".join(out)
''',
    tests=[[3749], [58], [1994], [1], [4], [9], [14], [40], [90], [400], [900], [3999], [3888], [2024], [444], [1000]],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def intToRoman(self, num):
        table = [(1000, "M"), (500, "D"), (100, "C"), (50, "L"), (10, "X"), (5, "V"), (1, "I")]
        out = []
        for value, symbol in table:          # no subtractive forms: 4 -> IIII
            count, num = divmod(num, value)
            out.append(symbol * count)
        return "".join(out)
''',
        '''class Solution:
    def intToRoman(self, num):
        table = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                 (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        out = []
        for value, symbol in table:
            if num >= value:                 # uses each piece at most once
                out.append(symbol); num -= value
        return "".join(out)
''',
    ],
    guide=dict(
        prereqs="The cashier's algorithm from the lesson *When greedy works*.",
        intuition="Treat the thirteen pieces (seven symbols plus six subtractive pairs) as coin denominations and make change greedily: take the largest piece that fits, as many times as it fits. This coin system is *canonical* — greedy is always right for it.",
        hints=[
            "List the values 1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1 with their symbols.",
            "Take the biggest piece that still fits.",
            "For each (value, symbol): count, num = divmod(num, value); append symbol * count.",
        ],
        brute_force="Handle each decimal digit with a 10-entry lookup table per place (`['', 'I', 'II', …, 'IX']`) — equally fast, more typing.",
        approach=r"""
**Dry run** `1994`: 1000 fits once → `M` (994 left); 900 → `CM` (94); 90 → `XC` (4); 4 → `IV`. → **"MCMXCIV"**.
""",
        complexity="Time and space **O(1)** — the table has 13 entries and the output at most 15 characters.",
        pitfalls="Leaving out the subtractive pairs produces `IIII`; using each piece at most once breaks `III` and `MMM`.",
        follow_up="*Roman to Integer*; *Integer to English Words* (same chunking idea, much fiddlier).",
    ),
),
dict(
    id="add-binary",
    title="Add Binary",
    difficulty="Easy",
    pattern="Math / digit arithmetic",
    leetcode="https://leetcode.com/problems/add-binary/",
    entry="addBinary",
    description=r"""
`a` and `b` are binary numbers written as strings of `'0'` and `'1'` (no leading zeros except the
number `"0"` itself). Return their sum as a binary string. Add them digit by digit with a carry, the
way you add decimal numbers on paper.

**Constraints**
- `1 <= len(a), len(b) <= 10^4`

**Example 1:** `a = "11", b = "1"` → `"100"`.

**Example 2:** `a = "1010", b = "1011"` → `"10101"`.
""",
    starter='''class Solution:
    def addBinary(self, a: str, b: str) -> str:
        pass
''',
    solution='''class Solution:
    def addBinary(self, a, b):
        i, j = len(a) - 1, len(b) - 1
        carry = 0
        out = []
        while i >= 0 or j >= 0 or carry:
            total = carry
            if i >= 0:
                total += ord(a[i]) - 48      # '0' is character code 48
                i -= 1
            if j >= 0:
                total += ord(b[j]) - 48
                j -= 1
            out.append(str(total % 2))       # digit to write
            carry = total // 2               # carry to the next column
        return "".join(reversed(out))
''',
    tests=[
        ["11", "1"], ["1010", "1011"], ["0", "0"], ["1", "1"], ["0", "1"], ["1111", "1"],
        ["1", "111111"], ["100", "110010"], ["101", "0"], ["11111111", "11111111"],
        ["110010", "10111"], [_bin_a, _bin_b], ["1" * 10000, "1"], ["1" * 9000, "1" * 10000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def addBinary(self, a, b):
        i, j, carry, out = len(a) - 1, len(b) - 1, 0, []
        while i >= 0 or j >= 0:                       # drops the final carry
            total = carry
            if i >= 0: total += int(a[i]); i -= 1
            if j >= 0: total += int(b[j]); j -= 1
            out.append(str(total % 2)); carry = total // 2
        return "".join(reversed(out))
''',
        '''class Solution:
    def addBinary(self, a, b):
        i, j, carry, out = len(a) - 1, len(b) - 1, 0, []
        while i >= 0 and j >= 0:                      # stops when the shorter string ends
            total = carry + int(a[i]) + int(b[j]); i -= 1; j -= 1
            out.append(str(total % 2)); carry = total // 2
        if carry: out.append("1")
        return "".join(reversed(out))
''',
    ],
    guide=dict(
        prereqs="Column addition with carries (lesson *Interview number theory* §1); binary notation (lesson *Bits in Python*).",
        intuition="Exactly like decimal addition, but a column overflows at 2 instead of 10: write `total % 2`, carry `total // 2`. Walk both strings from their last character; when one runs out, treat its missing digits as 0; when both run out, a leftover carry becomes one more leading `1`.",
        hints=[
            "Start from the rightmost characters.",
            "Each column: total = carry + digit of a + digit of b.",
            "Loop while i >= 0 or j >= 0 or carry; write total % 2, carry total // 2; reverse at the end.",
        ],
        brute_force="`bin(int(a, 2) + int(b, 2))[2:]` — a Python one-liner that relies on big integers; fine as a check, not as the interview answer.",
        approach=r"""
**Dry run** `"11" + "1"`: column 1+1 = 2 → write 0 carry 1; column 1+0+1 = 2 → write 0 carry 1; carry
1 → write 1. Reversed: **"100"**.
""",
        complexity="Time **O(max(m, n))**, space the same for the output.",
        pitfalls="Forgetting the final carry; stopping when the shorter string ends; building the string by repeated front-insertion (O(n²)).",
        follow_up="*Add Strings* (base 10), *Add Two Numbers* (linked lists), *Sum of Two Integers* (bitwise, no `+`).",
    ),
),
dict(
    id="robot-bounded-in-circle",
    title="Robot Bounded In Circle",
    difficulty="Medium",
    pattern="Math & geometry / simulation",
    leetcode="https://leetcode.com/problems/robot-bounded-in-circle/",
    entry="isRobotBounded",
    description=r"""
A robot starts at `(0, 0)` on an infinite plane, facing north. It executes the string
`instructions` — `'G'` move one unit forward, `'L'` turn 90° left, `'R'` turn 90° right — and then
repeats the whole string forever. Return `True` if the robot stays inside some circle forever (its
path is bounded), `False` if it wanders off to infinity.

**Constraints**
- `1 <= len(instructions) <= 100`

**Example 1:** `"GGLLGG"` → `True` (goes up 2, turns around, comes back).

**Example 2:** `"GG"` → `False`. `"GL"` → `True` (walks a square).
""",
    starter='''class Solution:
    def isRobotBounded(self, instructions: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isRobotBounded(self, instructions):
        x = y = 0
        dx, dy = 0, 1                       # facing north
        for c in instructions:
            if c == "G":
                x, y = x + dx, y + dy
            elif c == "L":
                dx, dy = -dy, dx            # rotate the direction 90 degrees counter-clockwise
            else:
                dx, dy = dy, -dx            # 90 degrees clockwise
        # bounded iff it is back at the start, or it no longer faces north
        return (x, y) == (0, 0) or (dx, dy) != (0, 1)
''',
    tests=[["GGLLGG"], ["GG"], ["GL"], ["L"], ["G"], ["GLGLGLG"], ["GLRLLGLL"], ["LLGRL"], ["RRGRRG"],
           ["GLGRG"], ["LRRRRLLLRL"], ["GRGL"], ["LGR"], [_robot_big], ["G" * 99 + "L"], ["GLGLGLGL" + "G"]],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def isRobotBounded(self, instructions):
        x = y = 0
        dx, dy = 0, 1
        for c in instructions:
            if c == "G": x, y = x + dx, y + dy
            elif c == "L": dx, dy = -dy, dx
            else: dx, dy = dy, -dx
        return (x, y) == (0, 0)             # only accepts returning in one pass
''',
        '''class Solution:
    def isRobotBounded(self, instructions):
        return instructions.count("L") != instructions.count("R")
''',
    ],
    guide=dict(
        prereqs="Direction vectors and 90° rotation (lesson *Matrix manipulation* §5).",
        intuition=r"""
Run the instructions once and look at where the robot is and which way it faces.

- Back at the origin → it repeats the same loop forever: bounded.
- Not at the origin but **still facing north** → every repetition adds the same displacement: it
  drifts away for ever.
- Not at the origin and facing another direction → the displacement itself gets rotated each cycle.
  Facing south, two cycles cancel; facing east or west, four cycles add up to zero. Bounded.
""",
        hints=[
            "Simulate one pass, tracking position and direction.",
            "What happens over several passes if the robot ends facing north but displaced?",
            "Bounded iff final position is the origin OR final direction is not north.",
        ],
        brute_force="Simulate four full passes and check that the robot is back at the origin — also correct and O(n).",
        approach=r"""
Direction as a vector `(dx, dy)`: left turn `(dx, dy) → (−dy, dx)`, right turn `(dx, dy) → (dy, −dx)`.

**Dry run** `"GL"`: move to (0,1), turn left → facing west. Not at origin, not north → **True**
(four passes trace a unit square).

**Dry run** `"GG"`: ends at (0,2) facing north → **False**.
""",
        complexity="Time **O(n)**, space O(1).",
        pitfalls="Checking only the position misses the square-walking cases; comparing counts of L and R ignores that `LLLL` is a full turn and that `G`s may cancel.",
        follow_up="*Walking Robot Simulation* (obstacles), *Spiral Matrix* (same direction-vector idiom).",
    ),
),
# ================================================================== BITS
dict(
    id="power-of-two",
    title="Power of Two",
    difficulty="Easy",
    pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/power-of-two/",
    entry="isPowerOfTwo",
    description=r"""
Return `True` if the integer `n` equals `2^k` for some integer `k >= 0` (so 1, 2, 4, 8, …), and
`False` otherwise. Zero and negative numbers are not powers of two. Aim for a solution without a
loop.

**Constraints**
- `-2^31 <= n <= 2^31 - 1`

**Example 1:** `1` → `True` (2⁰), `16` → `True`.

**Example 2:** `3` → `False`, `0` → `False`.
""",
    starter='''class Solution:
    def isPowerOfTwo(self, n: int) -> bool:
        pass
''',
    solution='''class Solution:
    def isPowerOfTwo(self, n):
        # a power of two has exactly one 1 bit; n & (n - 1) clears the lowest 1 bit
        return n > 0 and (n & (n - 1)) == 0
''',
    tests=[[1], [16], [3], [0], [-1], [-16], [2], [6], [1024], [1073741824], [2147483647], [-2147483648],
           [536870912], [12], [1023]],
    examples=4,
    wrong_solutions=[
        '''class Solution:
    def isPowerOfTwo(self, n):
        return (n & (n - 1)) == 0            # accepts 0
''',
        '''class Solution:
    def isPowerOfTwo(self, n):
        return n > 0 and n % 2 == 0          # "even" is not "power of two", and rejects 1
''',
    ],
    guide=dict(
        prereqs="`x & (x - 1)` (lesson *Bit tricks for interviews* §1).",
        intuition="In binary a power of two is a single 1 followed by zeros (`1000`). Subtracting one turns it into all ones below that position (`0111`). The two share no 1 bits, so their AND is zero — and that only happens when there was a single 1 bit to begin with.",
        hints=[
            "Write 1, 2, 4, 8, 16 in binary. What do they have in common?",
            "What does n & (n - 1) remove?",
            "return n > 0 and (n & (n - 1)) == 0.",
        ],
        brute_force="Keep dividing by 2 while the number is even and check whether you end at 1: O(log n).",
        approach=r"""
`16 = 10000`, `15 = 01111`, AND = 0 → True. `12 = 1100`, `11 = 1011`, AND = `1000` ≠ 0 → False.
`0`: `0 & −1 = 0` would wrongly pass, hence the `n > 0` guard.
""",
        complexity="Time and space **O(1)**.",
        pitfalls="Forgetting `n > 0` (0 and the minimum 32-bit integer in fixed-width languages). `n & -n == n` is an equivalent test.",
        follow_up="*Power of Four* (additionally the single bit must sit at an even position: `n & 0x55555555`), *Power of Three* (no bit trick; use division or the largest power of 3 that fits).",
    ),
),
dict(
    id="bitwise-and-of-numbers-range",
    title="Bitwise AND of Numbers Range",
    difficulty="Medium",
    pattern="Bit Manipulation / common prefix",
    leetcode="https://leetcode.com/problems/bitwise-and-of-numbers-range/",
    neetcode="https://neetcode.io/problems/bitwise-and-of-numbers-range",
    entry="rangeBitwiseAnd",
    description=r"""
Given `left <= right`, return the bitwise AND of **every** integer in the inclusive range
`[left, right]`. The range can contain two billion numbers, so you cannot AND them one by one.

**Constraints**
- `0 <= left <= right <= 2^31 - 1`

**Example 1:** `left = 5, right = 7` → `4` (`101 & 110 & 111 = 100`).

**Example 2:** `left = 0, right = 0` → `0`. `left = 1, right = 2147483647` → `0`.
""",
    starter='''class Solution:
    def rangeBitwiseAnd(self, left: int, right: int) -> int:
        pass
''',
    solution='''class Solution:
    def rangeBitwiseAnd(self, left, right):
        shift = 0
        while left != right:       # strip low bits until only the common prefix is left
            left >>= 1
            right >>= 1
            shift += 1
        return left << shift
''',
    tests=[[5, 7], [0, 0], [1, 2147483647], [1, 1], [6, 7], [8, 15], [10, 11], [12, 15], [2147483646, 2147483647],
           [2147483647, 2147483647], [0, 1], [26, 30], [1073741824, 2147483647], [3, 4], [600000000, 2147483645]],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def rangeBitwiseAnd(self, left, right):
        return left & right
''',
        '''class Solution:
    def rangeBitwiseAnd(self, left, right):
        shift = 0
        while left != right:
            left >>= 1; right >>= 1; shift += 1
        return left                    # forgets to shift the prefix back
''',
    ],
    guide=dict(
        prereqs="Shifts; binary counting. Lesson *Bits in Python*.",
        intuition=r"""
A bit of the answer is 1 only if **every** number in the range has it set. Write `left` and `right`
in binary and find their longest common prefix. Just below that prefix `left` has a 0 and `right`
has a 1 — and while counting up from `left` to `right`, every lower bit takes both values at some
point. So all bits below the common prefix are 0 in the AND, and the prefix itself survives.
""",
        hints=[
            "If left < right, can the lowest bit of the answer be 1?",
            "Which bits are identical in every number from left to right?",
            "Shift both right until they are equal, then shift the result back.",
        ],
        brute_force="AND every number from `left` to `right`: O(right − left), up to 2³¹ steps.",
        approach=r"""
**Dry run** `left = 26 (11010)`, `right = 30 (11110)`: shift → 1101 / 1111 → 110 / 111 → 11 / 11.
Three shifts; `11 << 3 = 11000₂ =` **24**.

Alternative: repeatedly clear the lowest set bit of `right` (`right &= right − 1`) while
`right > left`; the result is `right`.
""",
        complexity="Time **O(log n)** — at most 31 shifts. Space O(1).",
        pitfalls="`left & right` alone is wrong (3 & 4 = 0 is right by luck; 5 & 7 = 5 but the answer is 4).",
        follow_up="Bitwise OR of a range (common prefix followed by all ones). XOR of a range via the period-4 formula.",
    ),
),
dict(
    id="single-number-ii",
    title="Single Number II",
    difficulty="Medium",
    pattern="Bit Manipulation / counting bits mod 3",
    leetcode="https://leetcode.com/problems/single-number-ii/",
    entry="singleNumber",
    description=r"""
In `nums` every value appears exactly **three** times, except one value that appears once. Return
that value. Aim for linear time and constant extra space. Values may be negative.

**Constraints**
- `1 <= len(nums) <= 3·10^4`, `-2^31 <= nums[i] <= 2^31 - 1`

**Example 1:** `[2,2,3,2]` → `3`.

**Example 2:** `[0,1,0,1,0,1,99]` → `99`.
""",
    starter='''class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def singleNumber(self, nums):
        result = 0
        for k in range(32):
            ones = sum((x >> k) & 1 for x in nums)   # how many numbers have bit k set
            if ones % 3:
                result |= 1 << k
        if result >= 1 << 31:                        # bit 31 set: negative in 32-bit two's complement
            result -= 1 << 32
        return result
''',
    tests=[
        [[2, 2, 3, 2]],
        [[0, 1, 0, 1, 0, 1, 99]],
        [[7]],
        [[-2, -2, 1, 1, 4, 1, 4, 4, -4, -2]],
        [[-1, -1, -1, -5]],
        [[0, 5, 5, 5]],
        [[2147483647, 1, 1, 1]],
        [[-2147483648, 3, 3, 3]],
        [[30000, 500, 100, 30000, 100, 30000, 100]],
        [[-7, 4, 4, 4]],
        [[1, 1, 1, 0]],
        [_thrice(300)],
        [_thrice(2000)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def singleNumber(self, nums):
        acc = 0
        for x in nums: acc ^= x              # XOR only cancels pairs
        return acc
''',
        '''class Solution:
    def singleNumber(self, nums):
        result = 0
        for k in range(32):
            if sum((x >> k) & 1 for x in nums) % 3:
                result |= 1 << k
        return result                        # never converts back to a signed value
''',
    ],
    guide=dict(
        prereqs="*Single Number*; lesson *Bit tricks* §5 (counting per bit position) and *Bits in Python* §5 (32-bit simulation).",
        intuition=r"""
XOR cancels values that appear twice, not three times. Go one level lower: look at one bit position
at a time. Among the tripled values, the number of 1s in that position is a multiple of 3. So the
total count of 1s, modulo 3, is exactly the lone value's bit.
""",
        hints=[
            "Why does plain XOR fail here?",
            "Count how many numbers have bit k set. What is that count modulo 3?",
            "Rebuild the answer bit by bit over 32 positions, then convert to signed if bit 31 is set.",
        ],
        brute_force="`Counter(nums)` and pick the value with count 1 — O(n) time but O(n) space. Or `(3*sum(set(nums)) - sum(nums)) // 2`, also O(n) space.",
        approach=r"""
**Dry run** `[2,2,3,2]` = `10, 10, 11, 10`: bit 0 has one 1 → 1 % 3 = 1 → set; bit 1 has four 1s →
4 % 3 = 1 → set. Result `11₂ =` **3**.

Negative inputs: `(x >> k) & 1` reads bit `k` of the two's-complement pattern (Python's shift keeps
the sign bits). The rebuilt pattern is unsigned, so subtract `2^32` when bit 31 is set.

There is also a famous O(1)-state version with two masks: `ones = (ones ^ x) & ~twos;
twos = (twos ^ x) & ~ones`.
""",
        complexity="Time **O(32·n) = O(n)**, space O(1).",
        pitfalls="Forgetting the signed conversion returns huge positive numbers for negative answers.",
        follow_up="Generalise to 'every value appears k times except one' (count mod k). *Single Number III*.",
    ),
),
dict(
    id="single-number-iii",
    title="Single Number III",
    difficulty="Medium",
    pattern="Bit Manipulation / XOR partition",
    leetcode="https://leetcode.com/problems/single-number-iii/",
    entry="singleNumber",
    compare="unordered",
    description=r"""
In `nums` exactly **two** values appear once and every other value appears exactly twice. Return
the two lone values, in any order. Aim for linear time and constant extra space.

**Constraints**
- `2 <= len(nums) <= 3·10^4`, `-2^31 <= nums[i] <= 2^31 - 1`

**Example 1:** `[1,2,1,3,2,5]` → `[3,5]`.

**Example 2:** `[-1,0]` → `[-1,0]`.
""",
    starter='''class Solution:
    def singleNumber(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def singleNumber(self, nums):
        both = 0
        for x in nums:
            both ^= x                 # both == a ^ b
        low = both & -both            # one bit position where a and b differ
        a = 0
        for x in nums:
            if x & low:               # the group that has this bit set contains exactly one of them
                a ^= x
        return [a, a ^ both]
''',
    tests=[
        [[1, 2, 1, 3, 2, 5]],
        [[-1, 0]],
        [[0, 1]],
        [[1, 2]],
        [[2, 1, 2, 3, 4, 1]],
        [[-2147483648, 2147483647]],
        [[-2147483648, 0]],
        [[1, 1, 0, -2147483648]],
        [[5, 5, -3, 7, 7, -8]],
        [[4, 6, 9, 9]],
        [[1, 3, 3, 1, 1024, 1025]],
        [_twice_two(500)],
        [_twice_two(10000)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def singleNumber(self, nums):
        both = 0
        for x in nums: both ^= x
        return [both, 0]
''',
        '''class Solution:
    def singleNumber(self, nums):
        both = 0
        for x in nums: both ^= x
        a = 0
        for x in nums:
            if x & 1: a ^= x          # always splits on bit 0, which may not differ
        return [a, a ^ both]
''',
    ],
    guide=dict(
        prereqs="*Single Number*; `x & -x` isolates the lowest set bit (lesson *Bit tricks* §1–2).",
        intuition=r"""
XOR-ing everything gives `a ^ b`, which is not zero because `a ≠ b`. Any 1 bit in it marks a
position where `a` and `b` **differ**. Split the array into two groups by that bit: `a` lands in one
group, `b` in the other, and each pair of duplicates stays together (equal numbers have equal bits).
Each group is now an ordinary *Single Number* problem.
""",
        hints=[
            "What do you get when you XOR the whole array?",
            "Pick any set bit of that XOR. What does it tell you about the two answers?",
            "XOR only the numbers that have that bit set to get one answer; XOR with a^b for the other.",
        ],
        brute_force="A `Counter` or a set that toggles membership — O(n) space.",
        approach=r"""
**Dry run** `[1,2,1,3,2,5]`: XOR of all = `3 ^ 5 = 110₂`. Lowest set bit = `010`. Numbers with that
bit: 2, 3, 2 → XOR = 3. Other answer: `3 ^ 6 = 5`. → **[3, 5]**.

`both & -both` works for negatives too (Python integers behave like infinite two's complement).
""",
        complexity="Time **O(n)** (two passes), space O(1).",
        pitfalls="Splitting on a fixed bit such as bit 0 fails when the two answers agree there. In C/Java, negating the minimum integer overflows — Python is immune.",
        follow_up="*Missing and repeated number* problems use the same split-by-a-differing-bit idea.",
    ),
),
dict(
    id="hamming-distance",
    title="Hamming Distance",
    difficulty="Easy",
    pattern="Bit Manipulation / XOR + popcount",
    leetcode="https://leetcode.com/problems/hamming-distance/",
    entry="hammingDistance",
    description=r"""
The **Hamming distance** between two integers is the number of bit positions in which their binary
representations differ. Given non-negative `x` and `y`, return it.

**Constraints**
- `0 <= x, y <= 2^31 - 1`

**Example 1:** `x = 1, y = 4` → `2` (`001` vs `100`).

**Example 2:** `x = 3, y = 1` → `1`.
""",
    starter='''class Solution:
    def hammingDistance(self, x: int, y: int) -> int:
        pass
''',
    solution='''class Solution:
    def hammingDistance(self, x, y):
        diff = x ^ y              # 1 exactly where the two numbers differ
        count = 0
        while diff:
            diff &= diff - 1      # remove one differing bit
            count += 1
        return count
''',
    tests=[[1, 4], [3, 1], [0, 0], [0, 2147483647], [7, 7], [1, 0], [2147483647, 2147483646], [93, 73],
           [1073741824, 1], [255, 256], [680, 40], [5, 10], [123456789, 987654321]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def hammingDistance(self, x, y):
        return bin(x & y).count("1")        # counts shared bits instead of differing bits
''',
        '''class Solution:
    def hammingDistance(self, x, y):
        return abs(bin(x).count("1") - bin(y).count("1"))
''',
    ],
    guide=dict(
        prereqs="XOR; *Number of 1 Bits*.",
        intuition="XOR compares two numbers bit by bit and outputs 1 where they differ. So the distance is the number of 1 bits in `x ^ y` — a popcount.",
        hints=[
            "Which operator outputs 1 exactly when two bits differ?",
            "Count the 1 bits of x ^ y.",
            "Use diff &= diff - 1 in a loop (or bin(diff).count('1')).",
        ],
        brute_force="Compare the two numbers one bit position at a time for 31 positions.",
        approach="**Dry run** `1 ^ 4 = 001 ^ 100 = 101` → two 1 bits → **2**.",
        complexity="Time **O(number of differing bits)** ≤ 31, space O(1).",
        pitfalls="Comparing popcounts of x and y separately says nothing about *positions* (5 = 101 and 2 = 010 differ in 3 places).",
        follow_up="*Total Hamming Distance*: for each bit position, pairs differing = (count of ones) × (count of zeros) — O(32·n) instead of O(n²).",
    ),
),
dict(
    id="gray-code",
    title="Gray Code",
    difficulty="Medium",
    pattern="Bit Manipulation / construction",
    leetcode="https://leetcode.com/problems/gray-code/",
    entry="grayCode",
    checker=r'''
def check(args, got, expected):
    n = args[0]
    size = 1 << n
    if not isinstance(got, list) or len(got) != size:
        return False
    if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 or v >= size for v in got):
        return False
    if got[0] != 0 or len(set(got)) != size:
        return False
    for i in range(size):
        d = got[i] ^ got[(i + 1) % size]
        if d == 0 or d & (d - 1):
            return False
    return True
''',
    description=r"""
An `n`-bit **Gray code** is an ordering of all `2^n` integers from `0` to `2^n − 1` such that

- it starts with `0`,
- each integer appears exactly once,
- neighbouring entries differ in **exactly one bit**, and so do the last and the first entry.

Return any such ordering for the given `n` (the judge checks the properties, so every valid sequence
is accepted).

**Constraints**
- `1 <= n <= 16`

**Example 1:** `n = 2` → `[0,1,3,2]` (`00, 01, 11, 10`); `[0,2,3,1]` is also valid.

**Example 2:** `n = 1` → `[0,1]`.
""",
    starter='''class Solution:
    def grayCode(self, n: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def grayCode(self, n):
        return [i ^ (i >> 1) for i in range(1 << n)]
''',
    tests=[[2], [1], [3], [4], [5], [6], [7], [8], [10], [12], [14]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def grayCode(self, n):
        return list(range(1 << n))               # plain counting: 1 -> 2 flips two bits
''',
        '''class Solution:
    def grayCode(self, n):
        res = [0]
        for k in range(n):
            res += [x | (1 << k) for x in res]   # appended without reversing
        return res
''',
    ],
    guide=dict(
        prereqs="XOR and shifts; power-of-two test for 'exactly one bit differs'.",
        intuition=r"""
**Reflect and prefix.** Suppose you already have a Gray code for `k` bits. Write it down, then write
it again **in reverse** with an extra leading 1 on each entry. Inside each half neighbours differ in
one bit (they did before); at the seam the two middle entries are the same number except for the new
leading bit. Starting from `[0]` and repeating `n` times builds the whole code.

The closed form `i ^ (i >> 1)` produces exactly this sequence.
""",
        hints=[
            "Solve n = 1 and n = 2 by hand, then build n = 3 from n = 2.",
            "Mirror the list and set a new top bit on the mirrored half.",
            "Or use the formula gray(i) = i ^ (i >> 1).",
        ],
        brute_force="Backtracking: extend the sequence by any unused number one bit away — works for small n but can explore a lot.",
        approach=r"""
**Reflect-and-prefix for n = 3**: `[0,1]` → `[0,1,3,2]` → `[0,1,3,2, 6,7,5,4]`
(`000 001 011 010 110 111 101 100`).

```
res = [0]
for k in range(n):
    res += [x | (1 << k) for x in reversed(res)]
```

**Why `i ^ (i >> 1)` works.** Going from `i` to `i + 1` flips a run of trailing 1s to 0 and the next
0 to 1 (`0111 → 1000`). XOR-ing a number with itself shifted makes each output bit the "difference"
of adjacent input bits; within the flipped run those differences are unchanged, and only one
boundary changes — exactly one output bit flips.
""",
        complexity="Time and space **O(2ⁿ)** — the size of the output.",
        pitfalls="Appending the second half without reversing breaks the seam. Remember the wrap-around requirement (last vs first).",
        follow_up="Inverse Gray code (prefix XOR), *Circular Permutation in Binary Representation* (start at a given value: XOR the whole sequence with `start`).",
    ),
),
dict(
    id="utf-8-validation",
    title="UTF-8 Validation",
    difficulty="Medium",
    pattern="Bit Manipulation / masks",
    leetcode="https://leetcode.com/problems/utf-8-validation/",
    entry="validUtf8",
    description=r"""
UTF-8 stores each character in 1 to 4 bytes:

| bytes | pattern |
|---|---|
| 1 | `0xxxxxxx` |
| 2 | `110xxxxx 10xxxxxx` |
| 3 | `1110xxxx 10xxxxxx 10xxxxxx` |
| 4 | `11110xxx 10xxxxxx 10xxxxxx 10xxxxxx` |

The first byte announces the length by its number of leading 1s; every following byte of that
character (a *continuation byte*) starts with `10`. `data` is a list of integers; only the lowest 8
bits of each matter. Return `True` if the byte sequence is a valid series of such characters.

**Constraints**
- `1 <= len(data) <= 2·10^4`, `0 <= data[i] <= 255`

**Example 1:** `[197,130,1]` → `True` (`11000101 10000010 00000001`: a 2-byte character then a 1-byte one).

**Example 2:** `[235,140,4]` → `False` (`11101011` promises 3 bytes but the third is `00000100`).
""",
    starter='''class Solution:
    def validUtf8(self, data: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def validUtf8(self, data):
        need = 0                              # continuation bytes still expected
        for byte in data:
            byte &= 0xFF
            if need:
                if byte >> 6 != 0b10:         # must look like 10xxxxxx
                    return False
                need -= 1
            elif byte >> 7 == 0:              # 0xxxxxxx
                need = 0
            elif byte >> 5 == 0b110:
                need = 1
            elif byte >> 4 == 0b1110:
                need = 2
            elif byte >> 3 == 0b11110:
                need = 3
            else:                             # 10xxxxxx as a first byte, or 11111xxx
                return False
        return need == 0
''',
    tests=[
        [[197, 130, 1]],
        [[235, 140, 4]],
        [[0]],
        [[255]],
        [[145]],
        [[240, 162, 138, 147]],
        [[240, 162, 138]],
        [[248, 130, 130, 130, 130]],
        [[237]],
        [[228, 189, 160, 229, 165, 189, 13, 10]],
        [[250, 145, 145, 145, 145]],
        [[115, 100, 102, 231, 154, 132, 13, 10]],
        [[194, 155, 231, 184, 185, 246, 176, 131, 147]],
        [[127, 128]],
        [_utf_ok],
        [_utf_ok + [225, 136]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def validUtf8(self, data):
        need = 0
        for byte in data:
            if need:
                if byte >> 6 != 0b10: return False
                need -= 1
            elif byte >> 7 == 0: need = 0
            elif byte >> 5 == 0b110: need = 1
            elif byte >> 4 == 0b1110: need = 2
            elif byte >> 3 == 0b11110: need = 3
            else: return False
        return True                           # accepts a truncated final character
''',
        '''class Solution:
    def validUtf8(self, data):
        need = 0
        for byte in data:
            if need:
                if byte >> 6 != 0b10: return False
                need -= 1
            else:
                ones = 0
                while ones < 8 and (byte >> (7 - ones)) & 1: ones += 1
                if ones == 1: return False
                need = max(ones - 1, 0)       # allows 5+ byte characters
        return need == 0
''',
    ],
    guide=dict(
        prereqs="Shifts and masks to read the top bits of a byte (lesson *Bits in Python* §2).",
        intuition="It is a tiny state machine with one piece of state: how many continuation bytes are still owed. If none are owed, the current byte starts a character and its leading bits say how many follow. If some are owed, the current byte must start with `10`.",
        hints=[
            "How do you read the top k bits of an 8-bit value?",
            "Keep a counter of continuation bytes still expected.",
            "byte >> 7 == 0, byte >> 5 == 0b110, byte >> 4 == 0b1110, byte >> 3 == 0b11110; continuation: byte >> 6 == 0b10. End with counter == 0.",
        ],
        brute_force="Convert each byte to an 8-character binary string and compare prefixes with `startswith` — same logic, slower and wordier.",
        approach=r"""
**Dry run** `[197,130,1]`: `11000101` → top three bits `110` → need 1. `10000010` → continuation,
need 0. `00000001` → single byte. End with need 0 → **True**.

**Dry run** `[235,140,4]`: `11101011` → need 2. `10001100` ok, need 1. `00000100` is not `10…` → **False**.
""",
        complexity="Time **O(n)**, space O(1).",
        pitfalls="Data ending in the middle of a character; a first byte of the form `10xxxxxx`; first bytes with five or more leading 1s (`11111xxx`) are invalid.",
        follow_up="Real UTF-8 validation also rejects overlong encodings and code points above U+10FFFF — a good discussion point.",
    ),
),
dict(
    id="maximum-xor-of-two-numbers-in-an-array",
    title="Maximum XOR of Two Numbers in an Array",
    difficulty="Medium",
    pattern="Bit Manipulation / greedy on prefixes",
    leetcode="https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/",
    entry="findMaximumXOR",
    description=r"""
Given non-negative integers `nums`, return the largest value of `nums[i] XOR nums[j]` over all
pairs `i <= j` (a number paired with itself gives 0). With up to 2·10⁵ numbers on LeetCode, checking
every pair is too slow.

**Constraints**
- `1 <= len(nums) <= 2·10^5` (tests here go to 5000), `0 <= nums[i] <= 2^31 - 1`

**Example 1:** `[3,10,5,25,2,8]` → `28` (5 XOR 25).

**Example 2:** `[14,70,53,83,49,91,36,80,92,51,66,70]` → `127`.
""",
    starter='''class Solution:
    def findMaximumXOR(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def findMaximumXOR(self, nums):
        best = 0
        mask = 0
        for k in range(30, -1, -1):          # decide the answer's bits from the top down
            mask |= 1 << k
            prefixes = {x & mask for x in nums}      # top bits of every number
            candidate = best | (1 << k)              # can bit k of the answer be 1?
            # a ^ b == candidate  <=>  a ^ candidate == b
            if any((p ^ candidate) in prefixes for p in prefixes):
                best = candidate
        return best
''',
    tests=[
        [[3, 10, 5, 25, 2, 8]],
        [[14, 70, 53, 83, 49, 91, 36, 80, 92, 51, 66, 70]],
        [[0]],
        [[5]],
        [[1, 2]],
        [[7, 7, 7]],
        [[0, 2147483647]],
        [[8, 10, 2]],
        [[4, 6, 7]],
        [[2147483647, 2147483646]],
        [[1, 2, 4, 8, 16, 32]],
        [[1073741824, 1]],
        [_xor_big],
        [list(range(3000))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findMaximumXOR(self, nums):
        return max(nums) ^ min(nums)
''',
        '''class Solution:
    def findMaximumXOR(self, nums):
        nums = sorted(nums)
        return max((nums[i] ^ nums[i + 1] for i in range(len(nums) - 1)), default=0)
''',
    ],
    guide=dict(
        prereqs="XOR identity `a ^ b = c ⇔ a ^ c = b`; hash sets; greedy from the most significant bit.",
        intuition=r"""
A 1 in a higher bit is worth more than all lower bits together, so build the answer **greedily from
the top bit down**: for each bit ask "can this bit be 1, given the higher bits already decided?".
To answer, keep only the top bits (a *prefix*) of every number in a set. We want two prefixes `a`,
`b` with `a ^ b == candidate`. Since XOR is its own inverse, that is the same as asking whether
`a ^ candidate` is in the set — the *Two Sum* trick with XOR instead of minus.
""",
        hints=[
            "Which bit of the answer matters most?",
            "Fix the answer's bits from high to low; tentatively set the next bit to 1.",
            "With prefixes in a set, candidate is achievable iff some p has (p ^ candidate) in the set.",
        ],
        brute_force="Try all pairs: O(n²) — 2·10¹⁰ operations at the limit.",
        approach=r"""
**Dry run** `[3,10,5,25,2,8]` (5 bits: 00011, 01010, 00101, 11001, 00010, 01000):
- bit 4: prefixes {0, 16}; candidate 16: 0 ^ 16 = 16 ✓ → best = 16.
- bit 3: prefixes {0, 8, 24}; candidate 24: 0 ^ 24 = 24 ✓ → best = 24.
- bit 2: prefixes {0, 8, 4, 24}; candidate 28: 4 ^ 28 = 24 ✓ → best = 28.
- bit 1: candidate 30: no pair → stays 28. bit 0: candidate 29: no pair. Answer **28** (5 ^ 25).

The alternative is a **binary trie**: insert every number bit by bit from the top; for each number
walk the trie preferring the opposite bit at every level.
""",
        complexity="Time **O(31·n)**, space O(n).",
        pitfalls="`max ^ min` and 'XOR of sorted neighbours' are tempting but wrong (neighbours give the *minimum* XOR). Start from bit 30 for 31-bit inputs.",
        follow_up="*Maximum XOR With an Element From Array* (offline queries + trie), *Count Pairs With XOR in a Range*.",
    ),
),
]
