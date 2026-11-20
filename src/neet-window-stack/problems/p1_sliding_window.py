import random
import string

R = random.Random(20261119)

LC = "https://leetcode.com/problems/{}/"
NC = "https://neetcode.io/problems/{}"


def rand_str(n, alphabet, rng=R):
    return "".join(rng.choice(alphabet) for _ in range(n))


# ---------- big inputs ----------
_prices_big = [R.randint(0, 10000) for _ in range(25000)]
_prices_desc = list(range(15000, 0, -1))

_lsub_big = rand_str(50000, string.ascii_letters + string.digits + " !?")
_lsub_distinct = "".join(chr(c) for c in range(33, 127)) * 300  # 94 distinct chars repeated

_rep_big = rand_str(50000, "ABC")
_rep_big2 = rand_str(40000, string.ascii_uppercase)

_perm_s1 = rand_str(1000, "abcdefghij")
_perm_tail = list(_perm_s1)
R.shuffle(_perm_tail)
_perm_s2_yes = rand_str(29000, "abcdefghij") + "".join(_perm_tail)
_perm_s2_no = rand_str(30000, "klmnopqrstuvwxyz") + "a"

_mw_s = rand_str(50000, string.ascii_letters)
_mw_t = rand_str(60, string.ascii_letters)
_mw_s2 = "a" * 30000 + "b" + "a" * 20000 + "c"

_swm_big = [R.randint(-1000, 1000) for _ in range(15000)]

_cd_big = list(range(15000))
_cd_big_yes = list(range(10000)) + [9999 - 7000] + list(range(10000, 15000))

_mss_big = [R.randint(1, 100) for _ in range(30000)]

_ana_s = rand_str(50000, "abc")
_ana_p = "abcabcabcabcaab"

_fruit_big = []
while len(_fruit_big) < 50000:
    _fruit_big.extend([R.randint(0, 6)] * R.randint(1, 30))
_fruit_big = _fruit_big[:50000]

PROBLEMS = [
# ---------------------------------------------------------------- 121
dict(
    id="best-time-to-buy-and-sell-stock",
    title="Best Time to Buy and Sell Stock",
    difficulty="Easy",
    pattern="Sliding Window",
    leetcode=LC.format("best-time-to-buy-and-sell-stock"),
    neetcode=NC.format("buy-and-sell-crypto"),
    entry="maxProfit",
    description=r"""
You are given a list `prices` where `prices[i]` is the price of a single stock on day `i`.
You may make **at most one trade**: pick one day to buy and a **strictly later** day to sell.

Return the largest profit you can lock in. If every possible trade loses money (or there is only one
day), return `0` — you are allowed to simply not trade.

**Constraints**

- `1 <= len(prices) <= 10^5`
- `0 <= prices[i] <= 10^4`

**Example 1:** `prices = [7,1,5,3,6,4]` → `5` (buy at 1 on day 1, sell at 6 on day 4).

**Example 2:** `prices = [7,6,4,3,1]` → `0` (prices only fall, so do not trade).
""",
    starter='''class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def maxProfit(self, prices):
        best = 0
        lowest = prices[0]
        for p in prices[1:]:
            if p < lowest:
                lowest = p
            elif p - lowest > best:
                best = p - lowest
        return best
''',
    tests=[
        [[7, 1, 5, 3, 6, 4]],
        [[7, 6, 4, 3, 1]],
        [[1]],
        [[1, 2]],
        [[2, 1]],
        [[3, 3, 3, 3]],
        [[2, 4, 1]],
        [[2, 1, 2, 1, 0, 1, 2]],
        [[3, 2, 6, 5, 0, 3]],
        [[1, 10000, 0, 9999]],
        [_prices_big],
        [_prices_desc],
    ],
    wrong_solutions=[
        '''class Solution:
    def maxProfit(self, prices):
        return max(0, max(prices) - min(prices))
''',
        '''class Solution:
    def maxProfit(self, prices):
        best = 0
        for i in range(1, len(prices)):
            best = max(best, prices[i] - prices[i - 1])
        return best
''',
    ],
    guide=dict(
        prereqs="Single pass over an array; the idea of a *window* `[buy, sell]` from the Sliding Window lessons.",
        intuition="""
If you sell on day `j`, the best buy day is simply the **cheapest day before `j`**. So as you sweep left to
right you only need to remember one number: the minimum price seen so far. Every day you ask *"what if I
sold today?"* and compare against the best answer so far.

In window language: the left edge is the cheapest day so far and the right edge walks forward. When you meet
a price lower than the left edge, no future sale can prefer the old left edge, so the window jumps.
""",
        hints=[
            "Fix the selling day. Which buying day is optimal for it?",
            "The optimal buy day for a sale on day j is the minimum of prices[0..j-1]. Can you maintain that minimum incrementally?",
            "Keep `lowest` and `best`. For each price p: best = max(best, p - lowest); lowest = min(lowest, p).",
        ],
        brute_force="""
Try every pair `i < j` and keep the largest `prices[j] - prices[i]`. That is $\\binom{n}{2}$ pairs —
**O(n²)** time, O(1) space. With `n = 10^5` that is 5·10⁹ subtractions: far too slow (the large tests here
will visibly time out in the browser).
""",
        approach="""
1. `lowest = prices[0]`, `best = 0`.
2. For each later price `p`:
   - if `p < lowest`, it becomes the new cheapest buy day (it cannot be a profitable sale anyway);
   - otherwise try selling: `best = max(best, p - lowest)`.
3. Return `best`.

**Dry run** on `[7,1,5,3,6,4]`:

| day | p | lowest (before) | p − lowest | best |
|---|---|---|---|---|
| 1 | 1 | 7 | — new low | 0 |
| 2 | 5 | 1 | 4 | 4 |
| 3 | 3 | 1 | 2 | 4 |
| 4 | 6 | 1 | 5 | **5** |
| 5 | 4 | 1 | 3 | 5 |
""",
        complexity="Time **O(n)** — one pass. Space **O(1)** — two integers.",
        pitfalls="""
- `max(prices) - min(prices)` is wrong: the maximum might come *before* the minimum (`[7,1,5,3,6,4]` would give 6).
- Comparing only adjacent days finds the best one-day jump, not the best overall trade.
- Return `0`, never a negative number, when prices only fall.
- Initialise `lowest` with `prices[0]` (or `inf`), not `0`.
""",
        follow_up="""
- *Unlimited trades* (LeetCode 122): add every positive day-to-day difference.
- *At most k trades* (123/188) and *cooldown* (309) are dynamic-programming problems built on the same
  "best state so far" idea.
- This is **Kadane's algorithm** in disguise: the profit is the maximum subarray sum of the daily differences.
""",
    ),
),
# ---------------------------------------------------------------- 3
dict(
    id="longest-substring-without-repeating-characters",
    title="Longest Substring Without Repeating Characters",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("longest-substring-without-repeating-characters"),
    neetcode=NC.format("longest-substring-without-duplicates"),
    entry="lengthOfLongestSubstring",
    description=r"""
Given a string `s`, find the length of the longest **contiguous** block of characters in which no character
appears twice.

A *substring* is contiguous: `"pwke"` is a subsequence of `"pwwkew"` but not a substring.

**Constraints**

- `0 <= len(s) <= 5·10^4`
- `s` contains English letters, digits, symbols and spaces.

**Example 1:** `s = "abcabcbb"` → `3` (`"abc"`).

**Example 2:** `s = "bbbbb"` → `1`.

**Example 3:** `s = "pwwkew"` → `3` (`"wke"`).
""",
    starter='''class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        pass
''',
    solution='''class Solution:
    def lengthOfLongestSubstring(self, s):
        last = {}
        left = best = 0
        for right, ch in enumerate(s):
            if ch in last and last[ch] >= left:
                left = last[ch] + 1
            last[ch] = right
            if right - left + 1 > best:
                best = right - left + 1
        return best
''',
    tests=[
        ["abcabcbb"],
        ["bbbbb"],
        ["pwwkew"],
        [""],
        [" "],
        ["au"],
        ["dvdf"],
        ["abba"],
        ["tmmzuxt"],
        ["aab"],
        ["abcdefghijklmnopqrstuvwxyz"],
        [_lsub_big],
        [_lsub_distinct],
    ],
    wrong_solutions=[
        '''class Solution:
    def lengthOfLongestSubstring(self, s):
        last = {}
        left = best = 0
        for right, ch in enumerate(s):
            if ch in last:
                left = last[ch] + 1   # bug: can move left backwards
            last[ch] = right
            best = max(best, right - left + 1)
        return best
''',
        '''class Solution:
    def lengthOfLongestSubstring(self, s):
        return len(set(s))
''',
    ],
    guide=dict(
        prereqs="Variable-size sliding window; hash sets / dicts.",
        intuition="""
Keep a window `s[left..right]` that **never contains a duplicate** (that is the invariant). Push `right`
forward one character at a time. If the new character already lives inside the window, the window is broken
— and the only way to repair it is to move `left` just past the earlier copy. Every window we ever hold is
valid, so the answer is the largest one we saw.
""",
        hints=[
            "If s[i..j] has a duplicate, so does every longer substring that contains it. What does that tell you about moving the left edge back?",
            "Grow the window on the right; when the new character is already inside, shrink from the left until it is not.",
            "Store the last index of every character so you can jump `left` to `last[ch] + 1` in one step — but only if that index is inside the current window.",
        ],
        brute_force="""
Check every substring for uniqueness: O(n²) substrings × O(n) check = **O(n³)**, or O(n²) if you extend each
start with a set until you hit a duplicate. With `n = 5·10^4` even O(n²) is 2.5·10⁹ steps.
""",
        approach="""
Maintain `last[ch]` = most recent index of `ch`.

```
for right, ch in enumerate(s):
    if ch in last and last[ch] >= left:   # duplicate inside the window
        left = last[ch] + 1
    last[ch] = right
    best = max(best, right - left + 1)
```

**Dry run** on `"abba"`:

| right | ch | last before | left | window | best |
|---|---|---|---|---|---|
| 0 | a | {} | 0 | a | 1 |
| 1 | b | {a:0} | 0 | ab | 2 |
| 2 | b | {a:0,b:1} | 2 | b | 2 |
| 3 | a | {a:0,b:2} | **2** (a's last index 0 < left, ignore) | ba | 2 |

The `last[ch] >= left` check is what stops `left` from jumping *backwards* to 1 at step 3.
""",
        complexity="Time **O(n)**: each index is visited once by `right`, and `left` only moves forward. Space **O(min(n, Σ))** for the dict, where Σ is the alphabet size.",
        pitfalls="""
- Moving `left` backwards (`"abba"` → wrong answer 3). Use `left = max(left, last[ch] + 1)` or the `>= left` guard.
- Empty string must return `0`.
- Spaces and symbols are characters too.
- Off-by-one: window length is `right - left + 1`.
""",
        follow_up="""
- *Longest substring with at most K distinct characters* — same skeleton, with a counter instead of a set.
- *Fruit Into Baskets* in this module is the K = 2 case.
""",
    ),
),
# ---------------------------------------------------------------- 424
dict(
    id="longest-repeating-character-replacement",
    title="Longest Repeating Character Replacement",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("longest-repeating-character-replacement"),
    neetcode=NC.format("longest-repeating-substring-with-replacement"),
    entry="characterReplacement",
    description=r"""
You get a string `s` of uppercase letters and an integer `k`. You may overwrite **at most `k`** characters of
`s`, each with any uppercase letter you like.

Return the length of the longest substring that can be made to consist of **one repeated letter**.

**Constraints**

- `1 <= len(s) <= 10^5`
- `s` contains only `'A'`–`'Z'`
- `0 <= k <= len(s)`

**Example 1:** `s = "ABAB", k = 2` → `4` (rewrite both `B`s, or both `A`s).

**Example 2:** `s = "AABABBA", k = 1` → `4` (rewrite the `A` inside `"BABB"` to get `"BBBB"`).
""",
    starter='''class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        pass
''',
    solution='''class Solution:
    def characterReplacement(self, s, k):
        count = [0] * 26
        left = maxf = 0
        for right, ch in enumerate(s):
            c = ord(ch) - 65
            count[c] += 1
            if count[c] > maxf:
                maxf = count[c]
            if right - left + 1 - maxf > k:
                count[ord(s[left]) - 65] -= 1
                left += 1
        return len(s) - left
''',
    tests=[
        ["ABAB", 2],
        ["AABABBA", 1],
        ["A", 0],
        ["AAAA", 0],
        ["ABCDE", 1],
        ["ABCDE", 0],
        ["ABBB", 2],
        ["BAAAB", 2],
        ["ABAA", 0],
        ["ABCABC", 6],
        ["AAABBBCCCAAA", 3],
        [_rep_big, 100],
        [_rep_big2, 1000],
    ],
    wrong_solutions=[
        '''class Solution:
    def characterReplacement(self, s, k):
        from collections import Counter
        return min(len(s), max(Counter(s).values()) + k)
''',
        '''class Solution:
    def characterReplacement(self, s, k):
        best = 0
        run = 1
        for i in range(1, len(s) + 1):
            if i < len(s) and s[i] == s[i - 1]:
                run += 1
            else:
                best = max(best, run)
                run = 1
        return min(len(s), best + k)
''',
    ],
    guide=dict(
        prereqs="Variable sliding window; frequency counting with an array of 26.",
        intuition="""
A window can be turned into one letter if the number of characters that are **not** its most common letter
is at most `k`:

$$\\text{len(window)} - \\text{maxFreq(window)} \\le k$$

So: grow the window to the right, and whenever this condition fails, slide the left edge forward by one.
The clever bit is that `maxf` never needs to *decrease*: we only care about windows **longer** than the best
found so far, and a longer valid window needs a larger `maxf` than any we have already seen.
""",
        hints=[
            "For a fixed window, how many replacements are needed to make it uniform?",
            "replacements = window length − count of the most frequent letter in it. Keep a 26-slot count array.",
            "When the window becomes invalid, move left by one (not a while loop). The window size then never shrinks, so the final size is the answer.",
        ],
        brute_force="""
For each start `i`, extend `j` while keeping counts, and check `len - max(count) <= k`. That is **O(26·n²)**,
hopeless for `n = 10^5`.
""",
        approach="""
```
for right, ch in enumerate(s):
    count[ch] += 1
    maxf = max(maxf, count[ch])
    if (right - left + 1) - maxf > k:   # window invalid
        count[s[left]] -= 1
        left += 1                        # slide, keeping the size
return len(s) - left
```

Because we shift `left` by at most one per step, the window size never decreases: it is a "high-water mark".
When the loop ends the window size `n - left` is the longest valid length ever reached.

**Dry run** `s = "AABABBA", k = 1`:

| r | ch | counts A/B | maxf | size | size−maxf | action | left |
|---|---|---|---|---|---|---|---|
| 0 | A | 1/0 | 1 | 1 | 0 | ok | 0 |
| 1 | A | 2/0 | 2 | 2 | 0 | ok | 0 |
| 2 | B | 2/1 | 2 | 3 | 1 | ok | 0 |
| 3 | A | 3/1 | 3 | 4 | 1 | ok | 0 |
| 4 | B | 3/2 | 3 | 5 | 2 | slide | 1 |
| 5 | B | 2/3 | 3 | 5 | 2 | slide | 2 |
| 6 | A | 2/3 | 3 | 5 | 2 | slide | 3 |

Answer `7 - 3 = 4`.
""",
        complexity="Time **O(n)** (O(26·n) if you recompute the max each time — still linear). Space **O(26)**.",
        pitfalls="""
- Forgetting that `maxf` may be *stale* is fine — but then you must not report `right-left+1` only when the window is truly valid; returning the final window size (or tracking the max size) is correct.
- `max(count) + k` over the whole string ignores contiguity.
- `k` can be as large as `len(s)` — cap the answer at `len(s)`.
""",
        follow_up="""
- *Max Consecutive Ones III* (1004): binary array, flip at most k zeros — same template.
- If you are uneasy with the stale `maxf` trick, recompute `max(count)` (26 work) each step; it is still O(n).
""",
    ),
),
# ---------------------------------------------------------------- 567
dict(
    id="permutation-in-string",
    title="Permutation in String",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("permutation-in-string"),
    neetcode=NC.format("permutation-string"),
    entry="checkInclusion",
    description=r"""
Given two lowercase strings `s1` and `s2`, decide whether some **rearrangement of `s1`** appears as a
contiguous block inside `s2`. In other words: does `s2` have a substring of length `len(s1)` with exactly
the same letter counts as `s1`?

**Constraints**

- `1 <= len(s1), len(s2) <= 10^4` (the big tests here go a little further)
- lowercase English letters only

**Example 1:** `s1 = "ab", s2 = "eidbaooo"` → `True` (`"ba"` starts at index 3).

**Example 2:** `s1 = "ab", s2 = "eidboaoo"` → `False`.
""",
    starter='''class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        pass
''',
    solution='''class Solution:
    def checkInclusion(self, s1, s2):
        m, n = len(s1), len(s2)
        if m > n:
            return False
        need = [0] * 26
        win = [0] * 26
        for ch in s1:
            need[ord(ch) - 97] += 1
        for ch in s2[:m]:
            win[ord(ch) - 97] += 1
        matches = sum(1 for i in range(26) if need[i] == win[i])
        for r in range(m, n):
            if matches == 26:
                return True
            i = ord(s2[r]) - 97
            win[i] += 1
            if win[i] == need[i]:
                matches += 1
            elif win[i] == need[i] + 1:
                matches -= 1
            j = ord(s2[r - m]) - 97
            win[j] -= 1
            if win[j] == need[j]:
                matches += 1
            elif win[j] == need[j] - 1:
                matches -= 1
        return matches == 26
''',
    tests=[
        ["ab", "eidbaooo"],
        ["ab", "eidboaoo"],
        ["a", "a"],
        ["abc", "ab"],
        ["adc", "dcda"],
        ["hello", "ooolleoooleh"],
        ["aab", "bbaaa"],
        ["aab", "bbab"],
        ["abc", "cba"],
        ["xyz", "abcdefxzy"],
        ["a", "bbbbbbb"],
        [_perm_s1, _perm_s2_yes],
        [_perm_s1, _perm_s2_no],
    ],
    wrong_solutions=[
        '''class Solution:
    def checkInclusion(self, s1, s2):
        m = len(s1)
        t = set(s1)
        return any(set(s2[i:i + m]) == t for i in range(len(s2) - m + 1))
''',
        '''class Solution:
    def checkInclusion(self, s1, s2):
        from collections import Counter
        m, need = len(s1), Counter(s1)
        for i in range(len(s2) - m):          # off by one: misses the last window
            if Counter(s2[i:i + m]) == need:
                return True
        return False
''',
    ],
    guide=dict(
        prereqs="Fixed-size sliding window; frequency arrays (lesson: Counting windows).",
        intuition="""
"Some permutation of `s1` is a substring of `s2`" is a fancy way of saying "some window of length `m = len(s1)`
in `s2` has the same letter counts as `s1`". The window size is **fixed**, so we slide it one step at a time:
add the new right character, drop the old left one, and compare counts.

Comparing two 26-slot arrays is O(26) — fine. The extra polish is to track `matches` = how many of the 26
letters currently agree, so each slide costs O(1).
""",
        hints=[
            "Two strings are permutations of each other iff their letter counts are equal.",
            "Only windows of length len(s1) matter. Slide one across s2, updating counts in O(1).",
            "Maintain how many of the 26 letters have equal counts in `need` and `win`; the answer is True as soon as that number hits 26.",
        ],
        brute_force="""
Generating all permutations of `s1` is O(m!) — absurd. A saner brute force sorts (or counts) every window
from scratch: **O(n · m)** or O(n · m log m). With `m = 1000, n = 30 000` that is 3·10⁷ character
operations and visibly slow.
""",
        approach="""
1. If `m > n` return False.
2. Build `need` from `s1` and `win` from the first `m` chars of `s2`; set `matches` = number of equal slots.
3. For each new index `r` from `m` to `n-1`: if `matches == 26` return True; add `s2[r]`, remove `s2[r-m]`,
   adjusting `matches` whenever a slot becomes equal (+1) or stops being equal (−1).
4. Return `matches == 26` (checks the last window).

**Dry run** `s1="ab"`, `s2="eidbaooo"`: windows `ei`, `id`, `db`, `ba` → at `ba` counts are a:1, b:1, all 26
slots match → True.
""",
        complexity="Time **O(n + m)** (plus O(26) set-up). Space **O(26)** = O(1).",
        pitfalls="""
- Comparing **sets** instead of counts: `"aab"` vs window `"abb"` look equal as sets.
- Forgetting to test the final window (loop bounds `range(n - m + 1)`, not `n - m`).
- `s1` longer than `s2` → immediately False.
- When updating `matches`, a slot can move from equal→unequal: decrement only in that exact case.
""",
        follow_up="*Find All Anagrams in a String* (438, in this module) returns every start index instead of a boolean — same window.",
    ),
),
# ---------------------------------------------------------------- 76
dict(
    id="minimum-window-substring",
    title="Minimum Window Substring",
    difficulty="Hard",
    pattern="Sliding Window",
    leetcode=LC.format("minimum-window-substring"),
    neetcode=NC.format("minimum-window-with-characters"),
    entry="minWindow",
    description=r"""
Given strings `s` and `t`, return the **shortest substring of `s`** that contains every character of `t`,
**counting multiplicity** (if `t` has two `'a'`s the window needs at least two `'a'`s). Return `""` if no such
window exists.

If several shortest windows exist, return the **leftmost** one.

**Constraints**

- `1 <= len(s), len(t) <= 10^5`
- upper- and lowercase English letters (case-sensitive)

**Example 1:** `s = "ADOBECODEBANC", t = "ABC"` → `"BANC"`.

**Example 2:** `s = "a", t = "aa"` → `""` (only one `'a'` available).
""",
    starter='''class Solution:
    def minWindow(self, s: str, t: str) -> str:
        pass
''',
    solution='''class Solution:
    def minWindow(self, s, t):
        need = {}
        for ch in t:
            need[ch] = need.get(ch, 0) + 1
        missing = len(t)
        left = 0
        best_len, best_l = float("inf"), 0
        for right, ch in enumerate(s):
            if need.get(ch, 0) > 0:
                missing -= 1
            need[ch] = need.get(ch, 0) - 1
            if missing == 0:
                while need[s[left]] < 0:
                    need[s[left]] += 1
                    left += 1
                if right - left + 1 < best_len:
                    best_len, best_l = right - left + 1, left
                need[s[left]] += 1
                missing += 1
                left += 1
        return "" if best_len == float("inf") else s[best_l:best_l + best_len]
''',
    tests=[
        ["ADOBECODEBANC", "ABC"],
        ["a", "a"],
        ["a", "aa"],
        ["ab", "b"],
        ["aa", "aa"],
        ["bba", "ab"],
        ["cabwefgewcwaefgcf", "cae"],
        ["abc", "d"],
        ["aAbB", "AB"],
        ["acbbaca", "aba"],
        ["abcabdebac", "cda"],
        [_mw_s, _mw_t],
        [_mw_s2, "abc"],
        [_mw_s2, "aab"],
    ],
    wrong_solutions=[
        '''class Solution:
    def minWindow(self, s, t):
        need = set(t)
        best = ""
        left = 0
        from collections import Counter
        have = Counter()
        for right, ch in enumerate(s):
            have[ch] += 1
            while all(have[c] > 0 for c in need):
                if not best or right - left + 1 < len(best):
                    best = s[left:right + 1]
                have[s[left]] -= 1
                left += 1
        return best
''',
        '''class Solution:
    def minWindow(self, s, t):
        from collections import Counter
        need = Counter(t)
        have = Counter()
        best = ""
        left = 0
        for right, ch in enumerate(s):
            have[ch] += 1
            if all(have[c] >= need[c] for c in need):
                while have[s[left]] > need[s[left]]:
                    have[s[left]] -= 1
                    left += 1
                if not best or right - left + 1 <= len(best):   # bug: prefers the rightmost tie
                    best = s[left:right + 1]
        return best
''',
    ],
    guide=dict(
        prereqs="Variable sliding window with a frequency map; the *need/have* technique (lesson 2).",
        intuition="""
This is the canonical "**expand to become valid, shrink while still valid**" window.

- Move `right` until the window covers `t` (it is *valid*).
- Then move `left` as far as possible while it stays valid — every step yields a shorter candidate.
- One more step breaks validity; go back to expanding.

The trick for speed is to avoid re-checking all of `t` every time: keep `missing` = how many characters of
`t` (with multiplicity) are still not covered. The window is valid exactly when `missing == 0`.
""",
        hints=[
            "If s[l..r] contains t, so does every superset window. So for each right edge you want the largest left that still works.",
            "Keep a count of what you still need. Decrement when a needed character enters; the window is valid when the total still-needed is 0.",
            "When valid, pop from the left while the leftmost char is surplus (its need count is negative). Record the window, then drop one needed char to keep searching.",
        ],
        brute_force="""
Check every substring `s[i..j]` against `Counter(t)`: O(n²) windows × O(|Σ|) check = **O(n²·52)**.
With `n = 5·10^4` that is ~10¹¹ operations.
""",
        approach="""
`need[c]` starts as the count of `c` in `t` and is decremented when `c` enters the window, so negative values
mean *surplus*.

```
for right, ch in enumerate(s):
    if need[ch] > 0: missing -= 1   # ch was genuinely needed
    need[ch] -= 1
    if missing == 0:                 # valid
        while need[s[left]] < 0:     # left char is surplus -> drop it
            need[s[left]] += 1; left += 1
        record s[left..right]
        need[s[left]] += 1; missing += 1; left += 1   # break validity on purpose
```

**Dry run** `s = "ADOBECODEBANC", t = "ABC"`: first valid at `right=5` (`ADOBEC`, length 6). Dropping `A`
breaks it. Next valid at `right=10` (`DOBECODEBA` → shrink to `CODEBA`, length 6, not shorter). Drop `C`.
Valid again at `right=12`: window shrinks to `BANC`, length 4 → answer.
""",
        complexity="Time **O(|s| + |t|)** — each index enters and leaves the window once. Space **O(|Σ|)**.",
        pitfalls="""
- Ignoring multiplicity (using a set of `t`) — `t = "aa"` must need two `a`s.
- Updating the best answer with `<=` instead of `<` returns the rightmost tie; the task asks for the leftmost.
- Slicing a new string on every update is O(n) each — store `(start, length)` and slice once at the end.
- Case-sensitive: `'a' != 'A'`.
""",
        follow_up="""
- *Minimum Window Subsequence* (727) — order matters; DP or two-pointer scan.
- *Smallest Range Covering Elements from K Lists* (632) — same window idea after merging lists.
""",
    ),
),
# ---------------------------------------------------------------- 239
dict(
    id="sliding-window-maximum",
    title="Sliding Window Maximum",
    difficulty="Hard",
    pattern="Sliding Window",
    leetcode=LC.format("sliding-window-maximum"),
    neetcode=NC.format("sliding-window-maximum"),
    entry="maxSlidingWindow",
    description=r"""
A window of width `k` starts at the left end of `nums` and moves right one position at a time until it reaches
the right end. Return a list containing the **largest value inside the window at each position** (there are
`len(nums) - k + 1` positions).

**Constraints**

- `1 <= len(nums) <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
- `1 <= k <= len(nums)`

**Example 1:** `nums = [1,3,-1,-3,5,3,6,7], k = 3` → `[3,3,5,5,6,7]`.

**Example 2:** `nums = [1], k = 1` → `[1]`.
""",
    starter='''class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        pass
''',
    solution='''from collections import deque

class Solution:
    def maxSlidingWindow(self, nums, k):
        dq = deque()          # indices, values strictly decreasing
        out = []
        for i, x in enumerate(nums):
            while dq and nums[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                out.append(nums[dq[0]])
        return out
''',
    tests=[
        [[1, 3, -1, -3, 5, 3, 6, 7], 3],
        [[1], 1],
        [[1, -1], 1],
        [[9, 11], 2],
        [[4, -2], 2],
        [[7, 2, 4], 2],
        [[1, 3, 1, 2, 0, 5], 3],
        [[5, 4, 3, 2, 1], 2],
        [[1, 2, 3, 4, 5], 5],
        [[2, 2, 2, 2], 2],
        [[-7, -8, 7, 5, 7, 1, 6, 0], 4],
        [_swm_big, 1000],
        [list(range(12000, 0, -1)), 4000],
    ],
    wrong_solutions=[
        '''class Solution:
    def maxSlidingWindow(self, nums, k):
        out = [max(nums[:k])]
        for i in range(k, len(nums)):
            out.append(max(out[-1], nums[i]))   # never forgets an expired maximum
        return out
''',
        '''from collections import deque
class Solution:
    def maxSlidingWindow(self, nums, k):
        dq, out = deque(), []
        for i, x in enumerate(nums):
            while dq and nums[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] < i - k:        # off by one: keeps an expired index
                dq.popleft()
            if i >= k - 1:
                out.append(nums[dq[0]])
        return out
''',
    ],
    guide=dict(
        prereqs="Fixed-size windows; `collections.deque`; the monotonic deque lesson.",
        intuition="""
When a new value `x` arrives, any older value `≤ x` can **never** be a window maximum again: `x` is at least
as large *and* will stay in the window longer. So throw those values away. What remains is a deque of
indices whose values are **strictly decreasing** from front to back — the front is always the current
maximum. We also pop the front once it slides out of the window.
""",
        hints=[
            "Recomputing max(window) costs O(k) per step. Which elements could possibly be a future maximum?",
            "An element is useless once a larger-or-equal element arrives after it. Keep only the useful ones, in order.",
            "Store indices in a deque with decreasing values: pop from the back while nums[back] <= x, append i, pop the front if it is i-k or older; the front is the answer.",
        ],
        brute_force="""
For each of the `n-k+1` windows compute `max(nums[i:i+k])`: **O(n·k)**. With `n = 25 000, k = 1000` that is
2.5·10⁷ comparisons — sluggish in the browser; on LeetCode's limits (10⁵ × 5·10⁴) it times out.
A heap with lazy deletion gives O(n log n).
""",
        approach="""
```
for i, x in enumerate(nums):
    while dq and nums[dq[-1]] <= x: dq.pop()   # remove dominated
    dq.append(i)
    if dq[0] <= i - k: dq.popleft()            # remove expired
    if i >= k - 1: out.append(nums[dq[0]])
```

**Dry run** `[1,3,-1,-3,5,3,6,7], k = 3` (deque shows values):

| i | x | deque after | output |
|---|---|---|---|
| 0 | 1 | [1] | |
| 1 | 3 | [3] | |
| 2 | -1 | [3,-1] | 3 |
| 3 | -3 | [3,-1,-3] | 3 |
| 4 | 5 | [5] | 5 |
| 5 | 3 | [5,3] | 5 |
| 6 | 6 | [6] | 6 |
| 7 | 7 | [7] | 7 |
""",
        complexity="""
Time **O(n)** amortized: every index is appended once and popped at most once (from either end), so the
total work of all `while` loops is ≤ n. Space **O(k)** for the deque.
""",
        pitfalls="""
- Store **indices**, not values — you need them to detect expiry.
- Expiry test is `dq[0] <= i - k` (window is `i-k+1..i`).
- Using `<` vs `<=` when popping the back both work for maxima; `<=` keeps the deque smaller.
- `list.pop(0)` is O(k); use `deque.popleft()`.
""",
        follow_up="""
- Window **minimum**: flip the comparison.
- *Shortest Subarray with Sum at Least K* (862) and *Constrained Subsequence Sum* (1425) use the same deque on prefix sums / DP values.
""",
    ),
),
# ---------------------------------------------------------------- 219
dict(
    id="contains-duplicate-ii",
    title="Contains Duplicate II",
    difficulty="Easy",
    pattern="Sliding Window",
    leetcode=LC.format("contains-duplicate-ii"),
    entry="containsNearbyDuplicate",
    description=r"""
Given an integer list `nums` and an integer `k`, return `True` if there are two **different** indices `i` and
`j` with `nums[i] == nums[j]` and `|i - j| <= k`. Otherwise return `False`.

**Constraints**

- `1 <= len(nums) <= 10^5`
- `-10^9 <= nums[i] <= 10^9`
- `0 <= k <= 10^5`

**Example 1:** `nums = [1,2,3,1], k = 3` → `True` (indices 0 and 3).

**Example 2:** `nums = [1,2,3,1,2,3], k = 2` → `False` (equal values are 3 apart).
""",
    starter='''class Solution:
    def containsNearbyDuplicate(self, nums: List[int], k: int) -> bool:
        pass
''',
    solution='''class Solution:
    def containsNearbyDuplicate(self, nums, k):
        window = set()
        for i, x in enumerate(nums):
            if x in window:
                return True
            window.add(x)
            if len(window) > k:
                window.remove(nums[i - k])
        return False
''',
    tests=[
        [[1, 2, 3, 1], 3],
        [[1, 0, 1, 1], 1],
        [[1, 2, 3, 1, 2, 3], 2],
        [[1], 0],
        [[1, 1], 0],
        [[99, 99], 2],
        [[1, 2, 1], 1],
        [[1, 2, 1], 2],
        [[-5, 3, -5], 2],
        [[4, 1, 2, 3, 1, 5], 3],
        [_cd_big, 10000],
        [_cd_big_yes, 7001],
        [_cd_big_yes, 7000],
    ],
    wrong_solutions=[
        '''class Solution:
    def containsNearbyDuplicate(self, nums, k):
        window = set()
        for i, x in enumerate(nums):
            if x in window:
                return True
            window.add(x)
            if len(window) >= k:          # window one too small
                window.remove(nums[i - k + 1])
        return False
''',
        '''class Solution:
    def containsNearbyDuplicate(self, nums, k):
        return len(set(nums)) < len(nums)
''',
    ],
    guide=dict(
        prereqs="Hash sets; fixed-size windows.",
        intuition="""
"Two equal values at most `k` apart" means: when you stand at index `i`, is `nums[i]` among the previous `k`
values? Keep exactly those `k` values in a set — a window of size `k` that slides with you.
""",
        hints=[
            "For index i, which earlier indices are allowed partners?",
            "Only indices i-k..i-1. Keep their values in a set.",
            "Check membership, add nums[i], and when the set holds more than k values remove nums[i-k].",
        ],
        brute_force="Compare each `i` with the next `k` indices: **O(n·k)** — 10¹⁰ in the worst case.",
        approach="""
```
window = set()
for i, x in enumerate(nums):
    if x in window: return True
    window.add(x)
    if len(window) > k: window.remove(nums[i - k])
return False
```
The set never contains duplicates (we would have returned), so `len(window)` equals the number of indices in
it. **Dry run** `[1,0,1,1], k=1`: i=0 {1}; i=1 {0} after eviction of 1? Let us see: add 0 → {1,0}, size 2 > 1 →
remove nums[0]=1 → {0}; i=2: 1 not in {0}, add → {0,1}, remove nums[1]=0 → {1}; i=3: 1 in {1} → True.

An equally good alternative stores `last[x] = i` in a dict and checks `i - last[x] <= k`.
""",
        complexity="Time **O(n)**, space **O(min(n, k))**.",
        pitfalls="""
- `k = 0` can never succeed (indices must differ).
- Evict `nums[i-k]` *after* adding, when the window exceeds `k`.
- Plain "any duplicate" ignores the distance requirement.
""",
        follow_up="*Contains Duplicate III* (220) asks for values within `t` of each other — use buckets of width `t+1` or a sorted container.",
    ),
),
# ---------------------------------------------------------------- 209
dict(
    id="minimum-size-subarray-sum",
    title="Minimum Size Subarray Sum",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("minimum-size-subarray-sum"),
    entry="minSubArrayLen",
    description=r"""
Given a positive integer `target` and a list of **positive** integers `nums`, return the length of the shortest
contiguous subarray whose sum is **at least** `target`. If no such subarray exists, return `0`.

**Constraints**

- `1 <= target <= 10^9`
- `1 <= len(nums) <= 10^5`
- `1 <= nums[i] <= 10^4`

**Example 1:** `target = 7, nums = [2,3,1,2,4,3]` → `2` (`[4,3]`).

**Example 2:** `target = 11, nums = [1,1,1,1,1,1,1,1]` → `0`.
""",
    starter='''class Solution:
    def minSubArrayLen(self, target: int, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def minSubArrayLen(self, target, nums):
        best = len(nums) + 1
        total = left = 0
        for right, x in enumerate(nums):
            total += x
            while total >= target:
                if right - left + 1 < best:
                    best = right - left + 1
                total -= nums[left]
                left += 1
        return 0 if best > len(nums) else best
''',
    tests=[
        [7, [2, 3, 1, 2, 4, 3]],
        [4, [1, 4, 4]],
        [11, [1, 1, 1, 1, 1, 1, 1, 1]],
        [15, [1, 2, 3, 4, 5]],
        [1, [1]],
        [2, [1]],
        [11, [1, 2, 3, 4, 5]],
        [6, [10, 2, 3]],
        [100, [1, 99, 1, 1, 100]],
        [213, [12, 28, 83, 4, 25, 26, 25, 2, 25, 25, 25, 12]],
        [50000, _mss_big],
        [10 ** 9, _mss_big],
        [1500000, _mss_big],
    ],
    wrong_solutions=[
        '''class Solution:
    def minSubArrayLen(self, target, nums):
        best = len(nums) + 1
        total = left = 0
        for right, x in enumerate(nums):
            total += x
            if total >= target:            # bug: shrinks at most once per step
                best = min(best, right - left + 1)
                total -= nums[left]
                left += 1
        return 0 if best > len(nums) else best
''',
        '''class Solution:
    def minSubArrayLen(self, target, nums):
        best = len(nums) + 1
        total = left = 0
        for right, x in enumerate(nums):
            total += x
            while total > target:          # bug: strict >
                best = min(best, right - left + 1)
                total -= nums[left]
                left += 1
        return 0 if best > len(nums) else best
''',
    ],
    guide=dict(
        prereqs="Variable sliding window; why positivity matters (lesson 1).",
        intuition="""
All numbers are positive, so extending a window **increases** its sum and shrinking **decreases** it. That
monotonicity is what makes a two-pointer window correct: once `nums[left..right]` reaches the target, there is
no point keeping `left` where it is — shrink until the sum drops below the target, recording lengths as you go.
""",
        hints=[
            "Because all values are positive, the sum of a window grows when you move right and shrinks when you move left.",
            "Grow right; while the sum is >= target, record the length and move left.",
            "Use a while loop (not if) for the shrinking step, and return 0 if you never recorded anything.",
        ],
        brute_force="All O(n²) subarrays with running sums: **O(n²)** — 4.5·10⁸ for n = 30 000. A prefix-sum + binary-search variant gives O(n log n).",
        approach="""
```
for right, x in enumerate(nums):
    total += x
    while total >= target:
        best = min(best, right - left + 1)
        total -= nums[left]; left += 1
```

**Dry run** `target=7, [2,3,1,2,4,3]`: totals 2,5,6,8 → record 4, drop 2 → 6; add 4 → 10 → record 4, drop 3 →
7 → record 3, drop 1 → 6; add 3 → 9 → record 3, drop 2 → 7 → record **2**, drop 4 → 3. Answer 2.
""",
        complexity="Time **O(n)** — `left` and `right` each move at most n times. Space **O(1)**.",
        pitfalls="""
- `if` instead of `while` when shrinking misses shorter windows.
- "At least" means `>=`.
- Return `0`, not `inf` or `n+1`, when impossible.
- This window **breaks** with negative numbers — then you need prefix sums + a monotonic deque (LeetCode 862).
""",
        follow_up="O(n log n) follow-up: prefix sums are increasing, so for each `i` binary-search the smallest `j` with `prefix[j] - prefix[i] >= target`.",
    ),
),
# ---------------------------------------------------------------- 438
dict(
    id="find-all-anagrams-in-a-string",
    title="Find All Anagrams in a String",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("find-all-anagrams-in-a-string"),
    entry="findAnagrams",
    description=r"""
Given lowercase strings `s` and `p`, return the list of every start index `i` such that `s[i : i+len(p)]` is a
rearrangement of `p` (same letters, same counts). Return the indices in **increasing order**.

**Constraints**

- `1 <= len(s), len(p) <= 3·10^4` (big tests go to 5·10^4)
- lowercase English letters

**Example 1:** `s = "cbaebabacd", p = "abc"` → `[0, 6]` (`"cba"` and `"bac"`).

**Example 2:** `s = "abab", p = "ab"` → `[0, 1, 2]`.
""",
    starter='''class Solution:
    def findAnagrams(self, s: str, p: str) -> List[int]:
        pass
''',
    solution='''class Solution:
    def findAnagrams(self, s, p):
        m, n = len(p), len(s)
        if m > n:
            return []
        need = [0] * 26
        for ch in p:
            need[ord(ch) - 97] += 1
        win = [0] * 26
        out = []
        for i, ch in enumerate(s):
            win[ord(ch) - 97] += 1
            if i >= m:
                win[ord(s[i - m]) - 97] -= 1
            if i >= m - 1 and win == need:
                out.append(i - m + 1)
        return out
''',
    tests=[
        ["cbaebabacd", "abc"],
        ["abab", "ab"],
        ["a", "ab"],
        ["aaaaa", "a"],
        ["baa", "aa"],
        ["abc", "abc"],
        ["aab", "abb"],
        ["abacbabc", "abc"],
        ["zzzz", "zz"],
        ["af", "be"],
        [_ana_s, _ana_p],
        [_ana_s, "ab"],
    ],
    wrong_solutions=[
        '''class Solution:
    def findAnagrams(self, s, p):
        m, t = len(p), set(p)
        return [i for i in range(len(s) - m + 1) if set(s[i:i + m]) == t]
''',
        '''class Solution:
    def findAnagrams(self, s, p):
        m = len(p)
        sp = sorted(p)
        return [i for i in range(len(s) - m) if sorted(s[i:i + m]) == sp]
''',
    ],
    guide=dict(
        prereqs="Fixed-size window with a 26-slot count array; *Permutation in String*.",
        intuition="Slide a window of length `len(p)` across `s`, keeping letter counts. Whenever the window's counts equal `p`'s counts, record the window's start.",
        hints=[
            "An anagram of p has length len(p) — so the window size is fixed.",
            "Maintain counts incrementally: +1 for the entering char, −1 for the leaving one.",
            "Comparing two 26-length lists is O(26), which is constant. Record i-m+1 whenever they are equal.",
        ],
        brute_force="Sort every window and compare with `sorted(p)`: **O(n · m log m)**. With `m = 15`, `n = 5·10^4` it is acceptable; with long `p` it dies.",
        approach="""
```
for i, ch in enumerate(s):
    win[ch] += 1
    if i >= m: win[s[i-m]] -= 1
    if i >= m - 1 and win == need: out.append(i - m + 1)
```
**Dry run** `s="abab", p="ab"`: windows `ab`(0) ✓, `ba`(1) ✓, `ab`(2) ✓ → `[0,1,2]`.
""",
        complexity="Time **O(26·n)** = O(n) (or strict O(n) with the `matches` counter). Space O(26).",
        pitfalls="""
- Set comparison ignores counts.
- Loop bound must include the last window.
- `len(p) > len(s)` → `[]`.
""",
        follow_up="Same window powers *Permutation in String* (boolean version) and *Substring with Concatenation of All Words* (30), where tokens are words instead of letters.",
    ),
),
# ---------------------------------------------------------------- 904
dict(
    id="fruit-into-baskets",
    title="Fruit Into Baskets",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("fruit-into-baskets"),
    entry="totalFruit",
    description=r"""
A row of trees is described by `fruits`, where `fruits[i]` is the fruit **type** of tree `i`. You carry two
baskets; each basket holds any amount but only **one type** of fruit.

Pick any starting tree, then walk right picking exactly one fruit from every tree, and stop as soon as you
meet a tree whose type fits in neither basket. Return the maximum number of fruits you can collect.

Equivalently: the length of the longest contiguous subarray containing **at most two distinct values**.

**Constraints**

- `1 <= len(fruits) <= 10^5`
- `0 <= fruits[i] < len(fruits)`

**Example 1:** `fruits = [1,2,1]` → `3`.

**Example 2:** `fruits = [1,2,3,2,2]` → `4` (`[2,3,2,2]`).
""",
    starter='''class Solution:
    def totalFruit(self, fruits: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def totalFruit(self, fruits):
        count = {}
        left = best = 0
        for right, f in enumerate(fruits):
            count[f] = count.get(f, 0) + 1
            while len(count) > 2:
                g = fruits[left]
                count[g] -= 1
                if count[g] == 0:
                    del count[g]
                left += 1
            if right - left + 1 > best:
                best = right - left + 1
        return best
''',
    tests=[
        [[1, 2, 1]],
        [[0, 1, 2, 2]],
        [[1, 2, 3, 2, 2]],
        [[3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4]],
        [[0]],
        [[1, 1]],
        [[1, 2, 2, 3]],
        [[1, 0, 1, 4, 1, 4, 1, 2, 3]],
        [[0, 1, 6, 6, 4, 4, 6]],
        [[5, 5, 5, 5, 5]],
        [_fruit_big],
        [[i % 3 for i in range(30000)]],
    ],
    wrong_solutions=[
        '''class Solution:
    def totalFruit(self, fruits):
        best, start = 0, 0
        for i in range(len(fruits)):
            if len(set(fruits[start:i + 1])) > 2:
                start = i - 1            # bug: forgets the longer run before i-1
            best = max(best, i - start + 1)
        return best
''',
        '''class Solution:
    def totalFruit(self, fruits):
        from collections import Counter
        return sum(c for _, c in Counter(fruits).most_common(2))
''',
    ],
    guide=dict(
        prereqs="Variable sliding window with a counter; *Longest Substring Without Repeating Characters*.",
        intuition="Strip away the story: find the longest window with **at most 2 distinct values**. Grow on the right; while there are 3 distinct types, shrink from the left, deleting a type when its count reaches zero.",
        hints=[
            "Rephrase the problem in terms of distinct values in a subarray.",
            "Keep a dict type → count for the current window. Its size is the number of distinct types.",
            "While len(count) > 2, decrement fruits[left] (deleting zeros) and advance left. Track the max width.",
        ],
        brute_force="For every start, extend until a third type appears: **O(n²)** — 4.5·10⁸ steps for n = 30 000.",
        approach="""
```
for right, f in enumerate(fruits):
    count[f] += 1
    while len(count) > 2:
        count[fruits[left]] -= 1
        if count[fruits[left]] == 0: del count[fruits[left]]
        left += 1
    best = max(best, right - left + 1)
```
**Dry run** `[1,2,3,2,2]`: windows `[1]`, `[1,2]`, `[1,2,3]`→shrink→`[2,3]`, `[2,3,2]`, `[2,3,2,2]` → 4.
""",
        complexity="Time **O(n)**, space **O(1)** (the dict has at most 3 keys).",
        pitfalls="""
- Delete keys whose count hits 0, or `len(count)` overstates the distinct count.
- Resetting the window to start at `i-1` forgets that the previous type may have a longer run (`[1,2,2,3]`).
- Counting the two most common types globally ignores contiguity.
""",
        follow_up="Generalise to *at most K distinct* (LeetCode 340). *Subarrays with K Different Integers* (992) uses `atMost(K) - atMost(K-1)`.",
    ),
),
]
