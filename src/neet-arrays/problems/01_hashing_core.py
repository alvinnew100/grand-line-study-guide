import random

_r = random.Random(150)


def _shuffled(xs, seed):
    xs = list(xs)
    random.Random(seed).shuffle(xs)
    return xs


# ---------- big inputs (built once, deterministic) ----------
_dup_free = _shuffled(range(-10000, 10000), 1)            # 20,000 distinct ints
_dup_late = _shuffled(range(15000), 2) + [7]                # duplicate only at the very end

_letters = "abcdefghijklmnopqrstuvwxyz"
_anagram_s = "".join(_r.choice(_letters) for _ in range(50000))
_anagram_t = "".join(_shuffled(_anagram_s, 3))
_anagram_t_bad = _anagram_t[:-1] + ("a" if _anagram_t[-1] != "a" else "b")

_two_sum_big = _shuffled(range(0, 40000, 2), 4)            # even numbers only
_two_sum_big[12345] = 33333                                  # the only odd number
_two_sum_target = 33333 + _two_sum_big[777]

_words = []
for _ in range(8000):
    base = "".join(_r.choice("abcde") for _ in range(_r.randint(1, 5)))
    _words.append("".join(_shuffled(base, _r.randint(0, 10**6))))

_topk_big = []
for v in range(1, 201):
    _topk_big += [v * 7 - 1000] * v                          # value v*7-1000 appears v times
_topk_big = _shuffled(_topk_big, 5)

_codec_big = ["".join(_r.choice("ab#3,:4 ") for _ in range(_r.randint(0, 25))) for _ in range(3000)]

_prod_big = [_r.choice([1, -1, 1, 1, -1]) for _ in range(20000)]
for i in range(0, 20000, 2000):
    _prod_big[i] = 2

_lcs_big = _shuffled(list(range(0, 9000)) + list(range(20000, 21500)) + [_r.randint(-10**9, 10**9) for _ in range(6000)], 6)


_SUDOKU_VALID = [
    ["5", "3", ".", ".", "7", ".", ".", ".", "."],
    ["6", ".", ".", "1", "9", "5", ".", ".", "."],
    [".", "9", "8", ".", ".", ".", ".", "6", "."],
    ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
    ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
    ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
    [".", "6", ".", ".", ".", ".", "2", "8", "."],
    [".", ".", ".", "4", "1", "9", ".", ".", "5"],
    [".", ".", ".", ".", "8", ".", ".", "7", "9"],
]
_SUDOKU_SOLVED = [
    list("534678912"), list("672195348"), list("198342567"),
    list("859761423"), list("426853791"), list("713924856"),
    list("961537284"), list("287419635"), list("345286179"),
]


def _board_with(base, changes):
    b = [row[:] for row in base]
    for (r, c, v) in changes:
        b[r][c] = v
    return b


_EMPTY = [["."] * 9 for _ in range(9)]


PROBLEMS = [
# ---------------------------------------------------------------------------
dict(
    id="contains-duplicate",
    title="Contains Duplicate",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/contains-duplicate/",
    neetcode="https://neetcode.io/problems/duplicate-integer",
    entry="containsDuplicate",
    description=r"""
You are handed a list of integers `nums`. Report whether **any value shows up two or more times**.
Return `True` if some value repeats, and `False` if every element is unique.

**Constraints**

- `1 <= len(nums) <= 10^5`
- `-10^9 <= nums[i] <= 10^9`

**Example 1:** `nums = [1, 2, 3, 1]` → `True` (the value `1` appears at index 0 and index 3)

**Example 2:** `nums = [1, 2, 3, 4]` → `False`

**Example 3:** `nums = [1, 1, 1, 3, 3, 4, 3, 2, 4, 2]` → `True`
""",
    starter='''class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def containsDuplicate(self, nums):
        seen = set()
        for x in nums:
            if x in seen:
                return True
            seen.add(x)
        return False
''',
    tests=[
        [[1, 2, 3, 1]],
        [[1, 2, 3, 4]],
        [[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]],
        [[7]],
        [[-1, -1]],
        [[0, -0]],
        [[10**9, -10**9, 0, 10**9 - 1]],
        [[3, 1, 2, 3]],
        [[2, 14, 18, 22, 22]],
        [[5, 4, 3, 2, 1, 5]],
        [_dup_free],
        [_dup_late],
    ],
    wrong_solutions=[
        '''class Solution:
    def containsDuplicate(self, nums):
        # only compares neighbours without sorting first
        return any(nums[i] == nums[i + 1] for i in range(len(nums) - 1))
''',
        '''class Solution:
    def containsDuplicate(self, nums):
        # off-by-one: never looks at the last element
        return len(set(nums[:-1])) != len(nums) - 1
''',
    ],
    guide=dict(
        prereqs="Python `set` membership (see *The Arrays & Hashing pattern*). Big-O of nested loops.",
        intuition="""
The question is really *"have I seen this value before?"*, asked once per element. A set answers that
question in O(1) on average, so one pass that remembers everything it has seen is enough.
""",
        hints=[
            "What is the cost of comparing every pair of elements? Can you avoid re-scanning the past?",
            "If you sort the array first, where must duplicates end up?",
            "Keep a set of values you've already visited; check membership before inserting.",
        ],
        brute_force="""
Compare every pair `(i, j)` with `i < j`: two nested loops, **O(n²) time, O(1) space**. With `n = 10^5`
that is ~5·10⁹ comparisons — far too slow.

A better non-hash option: **sort, then check neighbours** — O(n log n) time, O(1) extra space if you may
sort in place. This is a good answer when memory is the constraint.
""",
        approach="""
1. Create an empty set `seen`.
2. For each `x` in `nums`: if `x` is already in `seen`, return `True` (early exit). Otherwise add it.
3. If the loop finishes, every value was new → return `False`.

**Dry run** on `[1, 2, 3, 1]`:

| step | x | seen before | action |
|---|---|---|---|
| 1 | 1 | {} | add → {1} |
| 2 | 2 | {1} | add → {1,2} |
| 3 | 3 | {1,2} | add → {1,2,3} |
| 4 | 1 | {1,2,3} | **1 in seen → return True** |

One-liner alternative: `return len(set(nums)) < len(nums)` — same complexity, but no early exit.
""",
        complexity="Time **O(n)** average (each set lookup/insert is O(1) expected). Space **O(n)** for the set in the worst case (all distinct).",
        pitfalls="""
- Comparing only adjacent elements **without sorting** misses `[1, 2, 3, 1]`.
- `0` and `-0` are the same integer in Python — no special case needed.
- The one-liner always builds the full set; the loop can stop early, which matters when a duplicate appears near the start.
""",
        follow_up="""
- *Contains Duplicate II* (LC 219): duplicates within distance `k` → keep a dict `value → last index` or a sliding-window set of size `k`.
- *Contains Duplicate III* (LC 220): values within `t` and indices within `k` → bucket by `x // (t+1)`.
""",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="valid-anagram",
    title="Valid Anagram",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/valid-anagram/",
    neetcode="https://neetcode.io/problems/is-anagram",
    entry="isAnagram",
    description=r"""
Two strings are **anagrams** when one can be turned into the other just by rearranging its letters —
every character must be used exactly as many times as it appears.

Given strings `s` and `t`, return `True` if `t` is an anagram of `s`, otherwise `False`.

**Constraints**

- `1 <= len(s), len(t) <= 5 * 10^4`
- both strings contain only lowercase English letters

**Example 1:** `s = "anagram", t = "nagaram"` → `True`

**Example 2:** `s = "rat", t = "car"` → `False`

**Follow-up:** what changes if the strings may contain arbitrary Unicode characters?
""",
    starter='''class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isAnagram(self, s, t):
        if len(s) != len(t):
            return False
        count = [0] * 26
        for a, b in zip(s, t):
            count[ord(a) - 97] += 1
            count[ord(b) - 97] -= 1
        return all(c == 0 for c in count)
''',
    tests=[
        ["anagram", "nagaram"],
        ["rat", "car"],
        ["a", "a"],
        ["a", "b"],
        ["ab", "a"],
        ["aacc", "ccac"],
        ["ac", "bb"],
        ["listen", "silent"],
        ["abc", "abcd"],
        ["zzzzzz", "zzzzzz"],
        [_anagram_s, _anagram_t],
        [_anagram_s, _anagram_t_bad],
    ],
    wrong_solutions=[
        '''class Solution:
    def isAnagram(self, s, t):
        return set(s) == set(t)      # ignores how many times each letter appears
''',
        '''class Solution:
    def isAnagram(self, s, t):
        return sum(map(ord, s)) == sum(map(ord, t))   # "ac" and "bb" collide
''',
    ],
    guide=dict(
        prereqs="Counting with a dict / `collections.Counter`; fixed-size count arrays (see *Prefix sums, counting and bucket tricks*).",
        intuition="""
Two strings are anagrams exactly when they have the **same multiset of characters** — the same letters
with the same counts. So build a "fingerprint" of letter counts for each and compare.
""",
        hints=[
            "If the lengths differ, can they possibly be anagrams?",
            "Sorting both strings gives a canonical form — but can you beat O(n log n)?",
            "Use 26 counters: add 1 for each char of s, subtract 1 for each char of t, then check all are zero.",
        ],
        brute_force="""
For each char of `s`, search `t` for an unused copy and mark it — O(n²). Or compare `sorted(s) == sorted(t)`:
**O(n log n)** time and O(n) space for the sorted copies. Sorting is perfectly acceptable in an interview
as a first answer; then improve to counting.
""",
        approach="""
1. If `len(s) != len(t)` return `False`.
2. Make `count = [0] * 26`.
3. Walk both strings together: `count[s[i]] += 1`, `count[t[i]] -= 1`.
4. They are anagrams iff every counter ended at 0.

**Dry run** `s = "aacc"`, `t = "ccac"`:

- after i=0: a:+1, c:-1 → a=1, c=-1
- after i=1: a:+1, c:-1 → a=2, c=-2
- after i=2: c:+1, a:-1 → a=1, c=-1
- after i=3: c:+1, c:-1 → a=1, c=-1 → **not all zero → False** (`s` has two a's, `t` only one).

Pythonic version: `return Counter(s) == Counter(t)`.
""",
        complexity="Time **O(n)**. Space **O(1)** — the array has 26 slots no matter how long the strings are (O(k) for an alphabet of size k).",
        pitfalls="""
- Comparing **sets** forgets multiplicities (`"aacc"` vs `"ccac"`).
- Summing character codes is a terrible hash: different multisets collide.
- For Unicode, a fixed 26-slot array breaks — use a dict/`Counter` instead (that's the follow-up).
""",
        follow_up="*Group Anagrams* uses the same fingerprint as a dict key. *Find All Anagrams in a String* (LC 438) slides this count array over a window.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="two-sum",
    title="Two Sum",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/two-sum/",
    neetcode="https://neetcode.io/problems/two-integer-sum",
    entry="twoSum",
    compare="unordered",
    description=r"""
Given an integer list `nums` and an integer `target`, find the **two different positions** `i` and `j`
whose values add up to `target`, and return them as `[i, j]`.

Every input is guaranteed to have **exactly one** such pair, and you may not use the same position twice
(though two different positions may hold the same value). The two indices may be returned in either order.

**Constraints**

- `2 <= len(nums) <= 10^4`
- `-10^9 <= nums[i], target <= 10^9`
- exactly one valid answer exists

**Example 1:** `nums = [2, 7, 11, 15], target = 9` → `[0, 1]` because `2 + 7 = 9`

**Example 2:** `nums = [3, 2, 4], target = 6` → `[1, 2]` (not `[0, 0]` — position 0 can't be reused)

**Example 3:** `nums = [3, 3], target = 6` → `[0, 1]`
""",
    starter='''class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def twoSum(self, nums, target):
        seen = {}                      # value -> index
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
''',
    tests=[
        [[2, 7, 11, 15], 9],
        [[3, 2, 4], 6],
        [[3, 3], 6],
        [[1, 5, 1, 5], 10],
        [[-3, 4, 3, 90], 0],
        [[0, 4, 3, 0], 0],
        [[-1, -2, -3, -4, -5], -8],
        [[10**9, -10**9, 5], 5],
        [[5, 75, 25], 100],
        [[2, 5, 5, 11], 10],
        [list(range(10000)), 19997],
        [_two_sum_big, _two_sum_target],
    ],
    wrong_solutions=[
        '''class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, x in enumerate(nums):
            seen[x] = i                # inserted BEFORE the lookup: may pair x with itself
            if target - x in seen:
                return [seen[target - x], i]
''',
        '''class Solution:
    def twoSum(self, nums, target):
        nums = sorted(nums)            # sorting loses the original indices
        l, r = 0, len(nums) - 1
        while l < r:
            s = nums[l] + nums[r]
            if s == target:
                return [l, r]
            if s < target:
                l += 1
            else:
                r -= 1
''',
    ],
    guide=dict(
        prereqs="Dict lookup by key; the *complement* idea (see *The Arrays & Hashing pattern*).",
        intuition="""
For each number `x`, the partner you need is fully determined: `target - x`. Instead of searching the
array for it, remember every number you've passed **in a dict from value to index** and ask the dict.
""",
        hints=[
            "For a fixed x, which exact value would complete the pair?",
            "Can you look that value up in O(1) instead of scanning?",
            "Iterate once; before storing x, check whether target - x is already stored.",
        ],
        brute_force="""
Try all pairs `i < j` and check `nums[i] + nums[j] == target`: **O(n²) time, O(1) space**. On the large
test (10⁴ elements, answer at the very end) that is ~5·10⁷ additions — noticeably slow in Python.
""",
        approach="""
1. `seen = {}` maps a value to the index where it was seen.
2. For each index `i` with value `x`:
   - `need = target - x`. If `need` is in `seen`, return `[seen[need], i]`.
   - Otherwise store `seen[x] = i`.

Checking **before** inserting guarantees we never pair an element with itself.

**Dry run** `nums = [3, 2, 4]`, `target = 6`:

| i | x | need | seen before | result |
|---|---|---|---|---|
| 0 | 3 | 3 | {} | store {3:0} |
| 1 | 2 | 4 | {3:0} | store {3:0, 2:1} |
| 2 | 4 | 2 | {3:0, 2:1} | **2 found → [1, 2]** |

With duplicates `[3, 3]`: at i=1, need=3 is already stored as index 0 → `[0, 1]`.
""",
        complexity="Time **O(n)** average — one pass, O(1) dict operations. Space **O(n)** for the dict.",
        pitfalls="""
- Inserting before checking lets `x + x = target` match **the same index** (`[3,2,4], 6 → [0,0]`).
- Sorting + two pointers is O(n log n) but **destroys indices** unless you sort `(value, index)` pairs.
- If a value repeats, overwriting `seen[x]` is fine: we only need *some* earlier index.
""",
        follow_up="""
- Sorted input → *Two Sum II* with two pointers and O(1) space.
- All unique pairs / triples → *3Sum*, *4Sum*.
- Count pairs instead of finding one → store counts instead of indices.
""",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="group-anagrams",
    title="Group Anagrams",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/group-anagrams/",
    neetcode="https://neetcode.io/problems/anagram-groups",
    entry="groupAnagrams",
    compare="unordered_nested",
    description=r"""
You get a list of lowercase words `strs`. Partition them into groups so that two words are in the same
group **if and only if** they are anagrams of each other (same letters, same counts). Return the list of
groups. Neither the order of the groups nor the order of words inside a group matters.

**Constraints**

- `1 <= len(strs) <= 10^4`
- `0 <= len(strs[i]) <= 100`
- words contain only lowercase English letters

**Example 1:** `strs = ["eat","tea","tan","ate","nat","bat"]` → `[["bat"],["nat","tan"],["ate","eat","tea"]]`

**Example 2:** `strs = [""]` → `[[""]]`

**Example 3:** `strs = ["a"]` → `[["a"]]`
""",
    starter='''class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        pass
''',
    solution='''class Solution:
    def groupAnagrams(self, strs):
        groups = {}
        for w in strs:
            count = [0] * 26
            for ch in w:
                count[ord(ch) - 97] += 1
            groups.setdefault(tuple(count), []).append(w)
        return list(groups.values())
''',
    tests=[
        [["eat", "tea", "tan", "ate", "nat", "bat"]],
        [[""]],
        [["a"]],
        [["", ""]],
        [["", "b", ""]],
        [["aab", "abb", "bab", "aba"]],
        [["abc", "bca", "cab", "xyz", "zyx", "yxz", "q"]],
        [["ac", "bb", "ca"]],
        [["ab", "ba", "ab"]],
        [["listen", "silent", "enlist", "google", "gogole", "cat"]],
        [_words],
    ],
    wrong_solutions=[
        '''class Solution:
    def groupAnagrams(self, strs):
        groups = {}
        for w in strs:
            key = "".join(sorted(set(w)))      # set() drops repeated letters
            groups.setdefault(key, []).append(w)
        return list(groups.values())
''',
        '''class Solution:
    def groupAnagrams(self, strs):
        groups = {}
        for w in strs:
            key = sum(ord(c) for c in w)       # "ac" and "bb" collide
            groups.setdefault(key, []).append(w)
        return list(groups.values())
''',
    ],
    guide=dict(
        prereqs="*Valid Anagram*; tuples as dict keys (hashable, see *Inside dict and set*).",
        intuition="""
Give every word a **canonical key** that is identical for all its anagrams and different otherwise —
either its sorted letters or its 26-letter count vector. Then a dict from key → list of words does the
grouping in one pass.
""",
        hints=[
            "How would you test whether two words are anagrams? Now make that test a *key*.",
            "Sorted letters work as a key. Count vectors also work — but lists aren't hashable; what is?",
            "Use `dict.setdefault(key, []).append(word)` (or `defaultdict(list)`) and return the values.",
        ],
        brute_force="""
Compare every word with every existing group's representative using an anagram test: O(n² · k) where
`k` is word length. Fine for 10 words, hopeless for 10⁴.
""",
        approach="""
1. `groups = {}`.
2. For each word `w`: build `count = [0]*26`, increment per letter, convert to `tuple(count)` (hashable).
3. Append `w` to `groups[key]`.
4. Return `list(groups.values())`.

**Dry run** on `["eat","tea","tan","ate","nat","bat"]` (showing keys as sorted strings for readability):

| word | key | groups after |
|---|---|---|
| eat | aet | {aet:[eat]} |
| tea | aet | {aet:[eat,tea]} |
| tan | ant | + {ant:[tan]} |
| ate | aet | aet:[eat,tea,ate] |
| nat | ant | ant:[tan,nat] |
| bat | abt | + {abt:[bat]} |

Sorted-key version: `key = "".join(sorted(w))` — simpler to write, O(k log k) per word.
""",
        complexity="Count-key: time **O(n · k)** (plus 26 per word for the tuple), space **O(n · k)** for the output. Sorted-key: O(n · k log k).",
        pitfalls="""
- Lists can't be dict keys — convert the count to a `tuple` (or a string like `"1#0#2#..."`).
- Keys built from `set(w)` or sums of character codes merge non-anagrams.
- Empty string is a valid word; its key is all zeros and it groups with other empty strings.
""",
        follow_up="Group Shifted Strings (LC 249) uses the same 'canonical key' trick with letter differences as the key.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="top-k-frequent-elements",
    title="Top K Frequent Elements",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/top-k-frequent-elements/",
    neetcode="https://neetcode.io/problems/top-k-elements-in-list",
    entry="topKFrequent",
    compare="unordered",
    description=r"""
Given an integer list `nums` and an integer `k`, return the `k` values that occur **most often**. You may
return them in any order. The inputs are chosen so that the answer is **unique** (there is never a tie at
the k-th place).

**Constraints**

- `1 <= len(nums) <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
- `1 <= k <=` number of distinct values

**Example 1:** `nums = [1,1,1,2,2,3], k = 2` → `[1, 2]`

**Example 2:** `nums = [1], k = 1` → `[1]`

**Follow-up:** beat O(n log n) — the obvious "sort by frequency" approach.
""",
    starter='''class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def topKFrequent(self, nums, k):
        count = {}
        for x in nums:
            count[x] = count.get(x, 0) + 1
        buckets = [[] for _ in range(len(nums) + 1)]   # buckets[f] = values seen f times
        for x, f in count.items():
            buckets[f].append(x)
        res = []
        for f in range(len(buckets) - 1, 0, -1):
            for x in buckets[f]:
                res.append(x)
                if len(res) == k:
                    return res
        return res
''',
    tests=[
        [[1, 1, 1, 2, 2, 3], 2],
        [[1], 1],
        [[4, 1, -1, 2, -1, 2, 3], 2],
        [[5, 5, 5, 5], 1],
        [[1, 2, 3, 4, 5, 5], 1],
        [[3, 0, 1, 0], 1],
        [[-10000, -10000, 10000], 1],
        [[1, 2], 2],
        [[6, 6, 6, 7, 7, 8, 8, 8, 8, 9], 3],
        [[2, 2, 3, 3, 3, 1, 4, 4, 4, 4], 4],
        [_topk_big, 10],
        [_topk_big[:3000] + [42] * 400, 1],
    ],
    wrong_solutions=[
        '''class Solution:
    def topKFrequent(self, nums, k):
        seen = []
        for x in nums:                    # first k distinct values, ignoring frequency
            if x not in seen:
                seen.append(x)
            if len(seen) == k:
                break
        return seen
''',
        '''class Solution:
    def topKFrequent(self, nums, k):
        count = {}
        for x in nums:
            count[x] = count.get(x, 0) + 1
        order = sorted(count, key=lambda x: count[x])   # ascending: returns the LEAST frequent
        return order[:k]
''',
    ],
    guide=dict(
        prereqs="Frequency counting with a dict; bucket sort (see *Prefix sums, counting and bucket tricks*); heaps optional.",
        intuition="""
First count frequencies. A frequency can never exceed `n`, so instead of *sorting* by frequency you can
drop each value into **bucket number = its frequency** and read the buckets from the top down.
""",
        hints=[
            "Start by counting how many times each value occurs.",
            "Sorting the (value, count) pairs is O(n log n). A heap of size k gives O(n log k). Can you do O(n)?",
            "Frequencies are integers between 1 and n — make an array of n+1 lists indexed by frequency.",
        ],
        brute_force="""
Count with a dict, then `sorted(count, key=count.get, reverse=True)[:k]` — **O(n log n)**. A min-heap of
size `k` (`heapq.nlargest(k, count, key=count.get)`) gives **O(n log k)**. Both are fine answers to say
out loud before reaching the linear one.
""",
        approach="""
1. `count[x]` = occurrences of `x` (one pass).
2. `buckets = [[] for _ in range(n + 1)]`; for every `(x, f)` append `x` to `buckets[f]`.
3. Walk `f` from `n` down to `1`, collecting values until you have `k`.

**Dry run** `nums = [1,1,1,2,2,3]`, `k = 2`:

- count = {1:3, 2:2, 3:1}
- buckets: `[[], [3], [2], [1], [], [], []]` (index = frequency)
- f=6,5,4 empty → f=3 take 1 → f=2 take 2 → have k=2 → **[1, 2]**.
""",
        complexity="Time **O(n)**: counting is O(n), there are n+1 buckets, and each distinct value is placed once. Space **O(n)**.",
        pitfalls="""
- Buckets must have size `n + 1` (a value may appear `n` times).
- Stop as soon as you have `k` items — otherwise you return too many.
- Sorting ascending by count returns the *least* frequent values.
""",
        follow_up="*Top K Frequent Words* (LC 692) adds a lexicographic tie-break → heap with `(-count, word)`. *Kth Largest Element* uses quickselect for average O(n).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="encode-and-decode-strings",
    title="Encode and Decode Strings",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/encode-and-decode-strings/",
    neetcode="https://neetcode.io/problems/string-encode-and-decode",
    entry="roundtrip",
    description=r"""
Design a way to pack a **list of strings into one string** and unpack it again. Implement:

- `encode(strs)` → a single `str`
- `decode(s)` → the original list, exactly

The strings may contain **any characters** — including digits, `#`, commas, colons and spaces — and may
be empty. The list itself may be empty. You may not use language serialisers such as `json` or `pickle`
(the point is to design the format yourself).

The judge calls `roundtrip(strs)`, which is already written for you and simply returns
`decode(encode(strs))`; it must equal `strs`.

**Constraints**

- `0 <= len(strs) <= 3000`
- `0 <= len(strs[i]) <= 200`

**Example 1:** `["neet","code","love","you"]` → round-trips to `["neet","code","love","you"]`

**Example 2:** `["we","say",":","yes"]` → round-trips unchanged

**Example 3:** `[]` → `[]` and `[""]` → `[""]` (these two must stay different!)
""",
    starter='''class Solution:
    def encode(self, strs: List[str]) -> str:
        pass

    def decode(self, s: str) -> List[str]:
        pass

    # The judge calls this method. Leave it as it is.
    def roundtrip(self, strs: List[str]) -> List[str]:
        encoded = self.encode(strs)
        assert isinstance(encoded, str), "encode must return a single str"
        return self.decode(encoded)
''',
    solution='''class Solution:
    def encode(self, strs):
        return "".join(f"{len(w)}#{w}" for w in strs)

    def decode(self, s):
        res, i = [], 0
        while i < len(s):
            j = s.index("#", i)          # the first '#' after i ends the length field
            n = int(s[i:j])
            res.append(s[j + 1:j + 1 + n])
            i = j + 1 + n
        return res

    def roundtrip(self, strs):
        encoded = self.encode(strs)
        assert isinstance(encoded, str), "encode must return a single str"
        return self.decode(encoded)
''',
    tests=[
        [["neet", "code", "love", "you"]],
        [["we", "say", ":", "yes"]],
        [[]],
        [[""]],
        [["", ""]],
        [["#", "##", "3#abc"]],
        [["a,b", ",", ""]],
        [["12#", "0#", "#0"]],
        [["hello world", "  ", "tab\tchar", "new\nline"]],
        [["x" * 150, "y" * 10, "z"]],
        [["héllo", "日本語", "😀"]],
        [_codec_big],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def encode(self, strs):
        return ",".join(strs)              # breaks on commas and can't tell [] from [""]

    def decode(self, s):
        return s.split(",")

    def roundtrip(self, strs):
        return self.decode(self.encode(strs))
''',
        '''class Solution:
    def encode(self, strs):
        return "".join(str(len(w)) + w for w in strs)   # one-digit length assumed

    def decode(self, s):
        res, i = [], 0
        while i < len(s):
            n = int(s[i])
            res.append(s[i + 1:i + 1 + n])
            i += 1 + n
        return res

    def roundtrip(self, strs):
        return self.decode(self.encode(strs))
''',
    ],
    guide=dict(
        prereqs="String slicing and `str.index`; the idea of a *length-prefixed* format (how network protocols frame messages).",
        intuition="""
Any delimiter character might also appear *inside* a string, so a plain separator is ambiguous. Instead,
put the **length** of each string in front of it, followed by a marker: `4#neet`. The decoder reads the
number, then copies exactly that many characters — whatever they are — so the content can never confuse it.
""",
        hints=[
            "Why does `','.join` fail? Try a string that contains a comma, and the inputs `[]` vs `['']`.",
            "If the decoder knew how long the next string is, would it care what characters are in it?",
            "Encode each word as `len(word) + '#' + word`. Decode by reading digits up to the first '#', then slicing.",
        ],
        brute_force="""
Escaping: replace every `#` inside a word with `##` and use a lone `#` as separator (like CSV quoting).
It works but is fiddly to get right. The length-prefix scheme is O(total length) and much simpler.
""",
        approach="""
**Encode**: for each word append `f"{len(w)}#{w}"`.

**Decode**: keep an index `i`.
1. Find `j`, the first `#` at or after `i` — the characters `s[i:j]` are all digits (we wrote them).
2. `n = int(s[i:j])`; the word is `s[j+1 : j+1+n]`.
3. Jump `i = j + 1 + n` and repeat until the end.

**Dry run** `["we", "3#a"]` → encoded `"2#we3#3#a"`.

- i=0: first `#` at 1 → n=2 → word `s[2:4] = "we"` → i=4
- i=4: first `#` at 5 → n=3 → word `s[6:9] = "3#a"` (the inner `#` is just content) → i=9 = end.

Result `["we", "3#a"]`. Note `[]` encodes to `""` and `[""]` to `"0#"`, so they stay distinct.
""",
        complexity="Time **O(L)** for both directions, where L = total characters. Space **O(L)** for the output.",
        pitfalls="""
- Searching for `#` from the **current** index, not from the start (`s.index('#', i)`).
- Lengths can have several digits — don't assume one digit.
- `split` on a separator turns `""` into `[""]`, so empty list vs list-of-empty-string is lost.
""",
        follow_up="Real protocols use fixed-width binary length headers (e.g. 4 bytes, big-endian) — the same idea without the `#`. *Serialize and Deserialize Binary Tree* is the tree version of this design question.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="product-of-array-except-self",
    title="Product of Array Except Self",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/product-of-array-except-self/",
    neetcode="https://neetcode.io/problems/products-of-array-discluding-self",
    entry="productExceptSelf",
    description=r"""
For an integer list `nums`, build a list `answer` where `answer[i]` is the **product of every element
except** `nums[i]`.

You must run in **O(n)** time and you must **not use division** (division also breaks when the input
contains zeros).

**Constraints**

- `2 <= len(nums) <= 10^5`
- `-30 <= nums[i] <= 30`
- every prefix/suffix product fits in a 32-bit integer

**Example 1:** `nums = [1, 2, 3, 4]` → `[24, 12, 8, 6]`

**Example 2:** `nums = [-1, 1, 0, -3, 3]` → `[0, 0, 9, 0, 0]`

**Follow-up:** use O(1) extra space (the output list does not count).
""",
    starter='''class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def productExceptSelf(self, nums):
        n = len(nums)
        res = [1] * n
        prefix = 1
        for i in range(n):              # res[i] = product of everything left of i
            res[i] = prefix
            prefix *= nums[i]
        suffix = 1
        for i in range(n - 1, -1, -1):  # multiply in everything right of i
            res[i] *= suffix
            suffix *= nums[i]
        return res
''',
    tests=[
        [[1, 2, 3, 4]],
        [[-1, 1, 0, -3, 3]],
        [[2, 3]],
        [[0, 0]],
        [[0, 4]],
        [[1, 0, 2, 0]],
        [[-2, -3, -4]],
        [[5, 1, 1, 1, 1]],
        [[30, -30, 1, 2]],
        [[1, 1, 1, 1, 1, 1, 1, 1]],
        [_prod_big],
        [_prod_big[:9999] + [0] + _prod_big[10000:]],
    ],
    wrong_solutions=[
        '''class Solution:
    def productExceptSelf(self, nums):
        total = 1
        for x in nums:
            total *= x
        return [total // x for x in nums]     # division: crashes on zeros
''',
        '''class Solution:
    def productExceptSelf(self, nums):
        n = len(nums)
        res = [1] * n
        prefix = 1
        for i in range(n):
            prefix *= nums[i]                 # off by one: includes nums[i] itself
            res[i] = prefix
        suffix = 1
        for i in range(n - 1, -1, -1):
            res[i] *= suffix
            suffix *= nums[i]
        return res
''',
    ],
    guide=dict(
        prereqs="Prefix sums (same idea with multiplication) — see *Prefix sums, counting and bucket tricks*.",
        intuition="""
`answer[i]` = (product of everything **left** of i) × (product of everything **right** of i). Both halves
are running products you can sweep in one pass each: left-to-right for prefixes, right-to-left for suffixes.
""",
        hints=[
            "Split 'everything except i' into two contiguous pieces.",
            "Could you precompute the product of all elements before i, for every i, in one pass?",
            "Store prefix products in the output array, then sweep from the right with a single running suffix variable.",
        ],
        brute_force="""
For each `i`, multiply all other elements: **O(n²)**. The division trick (`total // nums[i]`) is O(n) but
forbidden, and it needs special cases for one zero vs. two or more zeros.
""",
        approach="""
1. `res = [1]*n`, `prefix = 1`. For `i = 0..n-1`: `res[i] = prefix`, then `prefix *= nums[i]`.
   Now `res[i]` holds the product of `nums[0..i-1]`.
2. `suffix = 1`. For `i = n-1..0`: `res[i] *= suffix`, then `suffix *= nums[i]`.

Order matters inside each loop: **write first, then include `nums[i]`**, so element i is never in its own product.

**Dry run** `[1, 2, 3, 4]`:

| i | prefix before | res after pass 1 |
|---|---|---|
| 0 | 1 | [1,_,_,_] |
| 1 | 1 | [1,1,_,_] |
| 2 | 2 | [1,1,2,_] |
| 3 | 6 | [1,1,2,6] |

Pass 2 (suffix): i=3: ×1 → 6, suffix=4; i=2: ×4 → 8, suffix=12; i=1: ×12 → 12, suffix=24; i=0: ×24 → 24.
Result **[24, 12, 8, 6]**.
""",
        complexity="Time **O(n)** (two passes). Extra space **O(1)** besides the output.",
        pitfalls="""
- Updating `prefix` *before* writing `res[i]` includes the element itself (off-by-one).
- Division fails on zeros; with exactly one zero, only that position is non-zero.
- Don't allocate separate prefix and suffix arrays if the follow-up asks for O(1) extra space.
""",
        follow_up="The same prefix/suffix decomposition solves *Trapping Rain Water* (max instead of product) and *Candy* (LC 135).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="valid-sudoku",
    title="Valid Sudoku",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/valid-sudoku/",
    neetcode="https://neetcode.io/problems/valid-sudoku",
    entry="isValidSudoku",
    description=r"""
A 9×9 Sudoku board is given as a list of 9 rows, each a list of 9 one-character strings: a digit
`"1"`–`"9"` or `"."` for an empty cell. Decide whether the **filled-in cells so far** break any rule:

1. no digit repeats within a row,
2. no digit repeats within a column,
3. no digit repeats within any of the nine 3×3 boxes.

You only check the current state — the board does **not** have to be solvable.

**Constraints**

- `board` is 9×9; each cell is `"1"`–`"9"` or `"."`

**Example 1:** the classic puzzle with `5 3 . . 7 . . . .` as the first row → `True`

**Example 2:** the same puzzle with the top-left `5` replaced by `8` → `False` (two 8s in the first box and first column)
""",
    starter='''class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        pass
''',
    solution='''class Solution:
    def isValidSudoku(self, board):
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]
        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":
                    continue
                b = (r // 3) * 3 + c // 3
                if v in rows[r] or v in cols[c] or v in boxes[b]:
                    return False
                rows[r].add(v)
                cols[c].add(v)
                boxes[b].add(v)
        return True
''',
    tests=[
        [_SUDOKU_VALID],
        [_board_with(_SUDOKU_VALID, [(0, 0, "8")])],
        [_EMPTY],
        [_SUDOKU_SOLVED],
        [_board_with(_EMPTY, [(4, 0, "7"), (4, 8, "7")])],               # row clash
        [_board_with(_EMPTY, [(0, 5, "2"), (8, 5, "2")])],               # column clash
        [_board_with(_EMPTY, [(3, 3, "9"), (5, 5, "9")])],               # box clash only
        [_board_with(_EMPTY, [(0, 3, "4"), (3, 0, "4")])],               # different boxes - fine
        [_board_with(_EMPTY, [(0, 3, "4"), (4, 1, "4"), (8, 8, "4")])],
        [_board_with(_SUDOKU_SOLVED, [(8, 8, "8")])],
        [_board_with(_EMPTY, [(6, 6, "1"), (8, 7, "1")])],
        [_board_with(_EMPTY, [(2, 2, "5"), (3, 3, "5"), (6, 6, "5")])],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isValidSudoku(self, board):
        for i in range(9):                       # forgets the 3x3 boxes
            row = [v for v in board[i] if v != "."]
            col = [board[r][i] for r in range(9) if board[r][i] != "."]
            if len(row) != len(set(row)) or len(col) != len(set(col)):
                return False
        return True
''',
        '''class Solution:
    def isValidSudoku(self, board):
        seen = set()
        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":
                    continue
                keys = [("r", r, v), ("c", c, v), ("b", r // 3 + c // 3, v)]   # wrong box id
                if any(k in seen for k in keys):
                    return False
                seen.update(keys)
        return True
''',
    ],
    guide=dict(
        prereqs="Sets; mapping 2-D coordinates to a block index with integer division.",
        intuition="""
There are 27 "groups" (9 rows, 9 columns, 9 boxes) and each must contain no repeated digit. Keep one set
per group and visit every cell once, checking and updating the three sets it belongs to.
""",
        hints=[
            "Check rows, columns and boxes — can you do all three in a single scan of the board?",
            "Which box does cell (r, c) belong to? Try (r // 3, c // 3).",
            "Flatten the box coordinate to one index: `(r // 3) * 3 + c // 3`, and keep 9 sets for each kind of group.",
        ],
        brute_force="""
Three separate passes — validate each row, each column, then each box, building a fresh set every time.
Still O(81) = O(1) for a fixed board, so this is fine; the one-pass version is just tidier and
generalises to n×n boards in O(n²).
""",
        approach="""
1. Create `rows`, `cols`, `boxes`: 9 sets each.
2. For every non-empty cell `(r, c)` with digit `v`:
   - `b = (r // 3) * 3 + c // 3`
   - if `v` is already in `rows[r]`, `cols[c]` or `boxes[b]` → return `False`
   - otherwise add `v` to all three.
3. Return `True`.

**Box index table:**

| r \\ c | 0–2 | 3–5 | 6–8 |
|---|---|---|---|
| 0–2 | 0 | 1 | 2 |
| 3–5 | 3 | 4 | 5 |
| 6–8 | 6 | 7 | 8 |

**Dry run** on Example 2: (0,0)='8' is added to row 0, col 0, box 0. Later (3,0)='8' → col 0 already has
'8' → **False**. (It would also be caught at (2,2)='8' via box 0.)
""",
        complexity="Time **O(81) = O(1)** for a 9×9 board (O(n²) for an n×n board). Space O(1) likewise (at most 81 entries per kind).",
        pitfalls="""
- `r // 3 + c // 3` is **not** a unique box id — box (0,1) and (1,0) both give 1.
- Remember to skip `"."` cells.
- The task is validity of the *current* board — don't try to solve it.
""",
        follow_up="*Sudoku Solver* (LC 37) uses the same three set-arrays inside a backtracking search. A bitmask per group (9 bits) replaces each set with an int.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="longest-consecutive-sequence",
    title="Longest Consecutive Sequence",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/longest-consecutive-sequence/",
    neetcode="https://neetcode.io/problems/longest-consecutive-sequence",
    entry="longestConsecutive",
    description=r"""
Given an unsorted list of integers `nums`, return the length of the longest run of **consecutive
integer values** that all appear in `nums` (like `4, 5, 6, 7`). The values can appear anywhere in the list
and in any order; repeated values count once.

Your algorithm must run in **O(n)** time.

**Constraints**

- `0 <= len(nums) <= 10^5`
- `-10^9 <= nums[i] <= 10^9`

**Example 1:** `nums = [100, 4, 200, 1, 3, 2]` → `4` (the run `1, 2, 3, 4`)

**Example 2:** `nums = [0, 3, 7, 2, 5, 8, 4, 6, 0, 1]` → `9`

**Example 3:** `nums = [1, 0, 1, 2]` → `3`
""",
    starter='''class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def longestConsecutive(self, nums):
        s = set(nums)
        best = 0
        for x in s:
            if x - 1 not in s:              # x starts a run
                y = x
                while y + 1 in s:
                    y += 1
                best = max(best, y - x + 1)
        return best
''',
    tests=[
        [[100, 4, 200, 1, 3, 2]],
        [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]],
        [[1, 0, 1, 2]],
        [[]],
        [[5]],
        [[7, 7, 7]],
        [[1, 3, 5, 7]],
        [[-1, -2, -3, 10, 11]],
        [[9, 1, 4, 7, 3, -1, 0, 5, 8, -1, 6]],
        [[10**9, -10**9, 10**9 - 1]],
        [[1, 2, 2, 3, 3, 4, 10, 11, 12, 13, 14]],
        [_lcs_big],
        [list(range(20000, 0, -1))],
    ],
    wrong_solutions=[
        '''class Solution:
    def longestConsecutive(self, nums):
        if not nums:
            return 0
        nums = sorted(nums)
        best = cur = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i - 1] + 1:
                cur += 1
            else:
                cur = 1                    # duplicates wrongly reset the run
            best = max(best, cur)
        return best
''',
        '''class Solution:
    def longestConsecutive(self, nums):
        s = set(nums)
        best = 0
        for x in s:
            if x - 1 not in s:
                y = x
                while y + 1 in s:
                    y += 1
                best = max(best, y - x)    # off by one
        return best
''',
    ],
    guide=dict(
        prereqs="Sets for O(1) membership; amortised counting arguments.",
        intuition="""
Put everything in a set. A number `x` is the **start** of a run exactly when `x - 1` is missing. Only from
starts do you walk upward (`x+1`, `x+2`, …). Each number is walked over at most once, so the total work is
linear even though there's a loop inside a loop.
""",
        hints=[
            "Sorting gives O(n log n). What data structure answers 'is x+1 present?' in O(1)?",
            "If you start counting from every element, you redo work. Which elements should you start from?",
            "Only start a run at x if x-1 is not in the set; then extend while y+1 is in the set.",
        ],
        brute_force="""
For every element, keep checking whether the next value exists by scanning the list: O(n³) / O(n²).
Sorting then scanning is **O(n log n)** — a good stepping stone, but careful with duplicates.
""",
        approach="""
1. `s = set(nums)` (also removes duplicates).
2. For each `x` in `s` with `x - 1 not in s`: walk `y` up while `y + 1 in s`; the run length is `y - x + 1`.
3. Track the maximum.

**Why O(n)?** The inner `while` only runs from run starts, and each element belongs to exactly one run,
so across the whole loop the `while` advances at most n times in total.

**Dry run** `[100, 4, 200, 1, 3, 2]` → s = {1,2,3,4,100,200}

| x | x-1 in s? | walk | length |
|---|---|---|---|
| 1 | no (start) | 1→2→3→4 | 4 |
| 2,3,4 | yes | skip | – |
| 100 | no | 100 | 1 |
| 200 | no | 200 | 1 |

Answer **4**.
""",
        complexity="Time **O(n)** average (each element is inserted, checked as a start, and walked over at most once). Space **O(n)** for the set.",
        pitfalls="""
- Iterate over the **set**, not the list: with many duplicates of a run start, iterating the list repeats the walk.
- In the sorting version, equal neighbours must be *skipped*, not reset the streak (`[1,2,2,3]` → 3).
- Empty input → 0.
""",
        follow_up="Union-Find also solves it (union x with x+1). *Binary Tree Longest Consecutive Sequence* is the tree variant.",
    ),
),
]
