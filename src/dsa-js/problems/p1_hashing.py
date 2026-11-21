"""DSA in JavaScript: Arrays & Hashing problems (JavaScript versions of the neet-arrays problems)."""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


rng = random.Random(7)
BIG_UNIQUE = rng.sample(range(-10**9, 10**9), 8000)
BIG_DUP = BIG_UNIQUE[:7999] + [BIG_UNIQUE[4321]]
TWO_SUM_BIG = list(range(1, 20001))

PROBLEMS = [
dict(
    id="js-contains-duplicate", title="Contains Duplicate", difficulty="Easy", pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/contains-duplicate/",
    neetcode="https://neetcode.io/problems/duplicate-integer",
    kind="js", entry="containsDuplicate",
    description=r"""
You receive an array of integers `nums`. Return `true` when at least one value occurs two or more times,
and `false` when every value is distinct.

- `0 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`

**Example 1:** `nums = [4, 9, 2, 4]` → `true` (4 appears twice)

**Example 2:** `nums = [7, 1, 3]` → `false`
""",
    starter="function containsDuplicate(nums) {\n  // your code\n}\n",
    solution=r'''function containsDuplicate(nums) {
  const seen = new Set();
  for (const x of nums) {
    if (seen.has(x)) return true;
    seen.add(x);
  }
  return false;
}
''',
    tests=[[[4, 9, 2, 4]], [[7, 1, 3]], [[]], [[5]], [[0, 0]], [[-1, 1, -1]], [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
           [[3, 1, 3, 1]], [[10**9, -10**9, 10**9]], [BIG_UNIQUE], [BIG_DUP]],
    wrong_solutions=[
        "function containsDuplicate(nums) {\n  for (let i = 1; i < nums.length; i++) if (nums[i] === nums[i - 1]) return true;\n  return false;\n}\n",
        "function containsDuplicate(nums) {\n  const s = [...nums].sort();\n  for (let i = 1; i < s.length; i++) if (s[i] === s[i - 1]) return false;\n  return true;\n}\n",
    ],
    guide=G(
        prereqs="The lesson *JavaScript for coding interviews*: `Set` with `has` and `add`, and `for...of` loops.",
        intuition="Walk the array once and remember every value you have already met. A `Set` answers \"have I met this before?\" in constant time on average, so the first repeat ends the search.",
        hints=[
            "What data structure answers membership questions in O(1)?",
            "Create `const seen = new Set()` before the loop.",
            "Inside the loop: if `seen.has(x)` return `true`, otherwise `seen.add(x)`.",
        ],
        brute_force="Compare every pair `i < j`: two nested loops, O(n^2) time and O(1) extra space. With 10^5 values that is about 5 billion comparisons, far too slow.",
        approach="1. Create an empty `Set`.\n2. For each value `x`: if the set already holds `x`, return `true`; otherwise add it.\n3. After the loop, return `false`.\n\n**Dry run** on `[4, 9, 2, 4]`: add 4, add 9, add 2, then 4 is already present → `true`.\n\nA one-liner also works: `return new Set(nums).size !== nums.length;` but it always builds the whole set even when the duplicate is at the start.",
        complexity="Time O(n) on average (each `has`/`add` is O(1)); space O(n) for the set.",
        pitfalls="- Using an object `{}` as the set turns keys into strings; it still works for integers here but breaks for mixed types (`1` and `\"1\"` collide).\n- Sorting with the default `sort()` compares values as **strings**; adjacent-equal checks still happen to work, but the habit causes bugs elsewhere. Pass `(a, b) => a - b`.\n- Checking only `nums[i] === nums[i - 1]` without sorting misses duplicates that are far apart.",
        follow_up="Contains Duplicate II asks whether two equal values are at most `k` indices apart: keep a `Map` from value to its last index, or a sliding-window `Set` of size `k`.",
    ),
),
dict(
    id="js-two-sum", title="Two Sum", difficulty="Easy", pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/two-sum/",
    neetcode="https://neetcode.io/problems/two-integer-sum",
    kind="js", entry="twoSum", compare="unordered",
    description=r"""
Given an integer array `nums` and an integer `target`, return the indices `[i, j]` of the **two different
positions** whose values add up to `target`. Exactly one such pair exists. The order of the two indices in
your answer does not matter.

- `2 <= nums.length <= 10^4`
- `-10^9 <= nums[i], target <= 10^9`

**Example 1:** `nums = [3, 8, 11, 5], target = 13` → `[1, 3]` (8 + 5)

**Example 2:** `nums = [6, 6], target = 12` → `[0, 1]`
""",
    starter="function twoSum(nums, target) {\n  // return [i, j]\n}\n",
    solution=r'''function twoSum(nums, target) {
  const indexOf = new Map();          // value -> index where we saw it
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    if (indexOf.has(need)) return [indexOf.get(need), i];
    indexOf.set(nums[i], i);
  }
  return [];
}
''',
    tests=[[[3, 8, 11, 5], 13], [[6, 6], 12], [[2, 7, 11, 15], 9], [[3, 2, 4], 6], [[-3, 4, 3, 90], 0],
           [[0, 4, 3, 0], 0], [[1, 5, 1, 5], 10], [[-1, -2, -3, -4, -5], -8], [[10**9, -10**9, 7], 7],
           [[5, 75, 25], 100], [TWO_SUM_BIG, 39999]],
    examples=2,
    wrong_solutions=[
        "function twoSum(nums, target) {\n  const m = new Map();\n  nums.forEach((x, i) => m.set(x, i));\n  for (let i = 0; i < nums.length; i++) if (m.has(target - nums[i])) return [i, m.get(target - nums[i])];\n  return [];\n}\n",
        "function twoSum(nums, target) {\n  const m = {};\n  for (let i = 0; i < nums.length; i++) {\n    const need = target - nums[i];\n    if (m[need]) return [m[need], i];\n    m[nums[i]] = i;\n  }\n  return [];\n}\n",
    ],
    guide=G(
        prereqs="`Map` with `has`, `get` and `set` (lesson *JavaScript for coding interviews*).",
        intuition="For each number you know exactly which partner you need: `target - x`. Keep a `Map` from every value seen so far to its index, and ask it whether the partner has already appeared.",
        hints=[
            "If the current value is `x`, which single value would complete the pair?",
            "Store values you have passed in a `Map` from value to index.",
            "Check the map **before** inserting the current value, so a value never pairs with itself.",
        ],
        brute_force="Try every pair with two nested loops and return the first pair that sums to `target`: O(n^2) time, O(1) space.",
        approach="1. `const indexOf = new Map()`.\n2. For `i` from 0: compute `need = target - nums[i]`. If the map has `need`, return `[indexOf.get(need), i]`.\n3. Otherwise `indexOf.set(nums[i], i)`.\n\n**Dry run** `[3, 8, 11, 5]`, target 13: i=0 need 10 (absent, store 3); i=1 need 5 (absent, store 8); i=2 need 2 (absent); i=3 need 8 → present at 1 → `[1, 3]`.",
        complexity="Time O(n): one pass with O(1) average map operations. Space O(n) for the map.",
        pitfalls="- Filling the map first and then searching can pair an element with itself (`[3, 2, 4]`, target 6 would find index 0 twice).\n- With a plain object, `if (m[need])` is falsy when the stored index is `0`: use `Map.has` or `need in m`.\n- Return indices, not values.",
        follow_up="If the array were sorted, two pointers solve it in O(1) extra space (see *Two Sum II*).",
    ),
),
dict(
    id="js-group-anagrams", title="Group Anagrams", difficulty="Medium", pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/group-anagrams/",
    neetcode="https://neetcode.io/problems/anagram-groups",
    kind="js", entry="groupAnagrams", compare="unordered_nested",
    description=r"""
Two words are **anagrams** when one can be made by rearranging the letters of the other (`"listen"` and
`"silent"`). Given an array of lowercase words `strs`, put the anagrams together: return an array of groups,
where each group is an array of words. Groups and the words inside them may come in any order.

- `1 <= strs.length <= 10^4`, `0 <= strs[i].length <= 100`, only `a`-`z`

**Example:** `["eat","tea","tan","ate","nat","bat"]` → `[["bat"],["nat","tan"],["ate","eat","tea"]]`
""",
    starter="function groupAnagrams(strs) {\n  // your code\n}\n",
    solution=r'''function groupAnagrams(strs) {
  const groups = new Map();                 // signature -> array of words
  for (const word of strs) {
    const counts = new Array(26).fill(0);
    for (let i = 0; i < word.length; i++) counts[word.charCodeAt(i) - 97]++;
    const key = counts.join(",");          // e.g. "1,0,0,...": unambiguous
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(word);
  }
  return [...groups.values()];
}
''',
    tests=[[["eat", "tea", "tan", "ate", "nat", "bat"]], [[""]], [["a"]], [["", ""]], [["abc", "bca", "cab", "xyz"]],
           [["ab", "ba", "abb", "bab", "bba", "aab"]], [["bdddddddddd", "bbbbbbbbbbc"]], [["aa", "a", "aaa"]],
           [["listen", "silent", "enlist", "google", "gogole", "cat"]],
           [["".join(chr(97 + (i * 7 + j) % 26) for j in range(8)) for i in range(400)]]],
    wrong_solutions=[
        "function groupAnagrams(strs) {\n  const g = new Map();\n  for (const w of strs) {\n    const counts = new Array(26).fill(0);\n    for (const c of w) counts[c.charCodeAt(0) - 97]++;\n    const key = counts.join('');\n    if (!g.has(key)) g.set(key, []);\n    g.get(key).push(w);\n  }\n  return [...g.values()];\n}\n",
        "function groupAnagrams(strs) {\n  const g = new Map();\n  for (const w of strs) {\n    const key = new Set(w).size + ':' + [...new Set(w)].sort().join('');\n    if (!g.has(key)) g.set(key, []);\n    g.get(key).push(w);\n  }\n  return [...g.values()];\n}\n",
    ],
    guide=G(
        prereqs="`Map` with array values, `charCodeAt`, spreading `map.values()` into an array.",
        intuition="Anagrams share a **signature** that ignores letter order: either the sorted letters, or the 26 letter counts. Use that signature as a `Map` key and collect words under it.",
        hints=[
            "What stays the same when you shuffle the letters of a word?",
            "`[...word].sort().join(\"\")` gives a signature in O(k log k).",
            "A 26-slot count array joined with a separator gives an O(k) signature.",
        ],
        brute_force="Compare every pair of words by sorting both: O(n^2 * k log k). Fine for 10 words, hopeless for 10^4.",
        approach="1. `const groups = new Map()`.\n2. For each word, count letters into a 26-slot array using `charCodeAt(i) - 97`.\n3. Build `key = counts.join(\",\")`. The comma matters: without it, counts `[1, 11]` and `[11, 1]` would both become `\"111\"`.\n4. Push the word into `groups.get(key)` (create the array first if needed).\n5. Return `[...groups.values()]`.",
        complexity="Time O(n * k) for n words of length up to k (plus O(26) per key). Space O(n * k) for the groups.",
        pitfalls="- Arrays cannot be `Map` keys by value: `map.get([1,2])` never finds a different array `[1,2]`. Convert the signature to a string.\n- `counts.join(\"\")` without a separator is ambiguous once a count reaches 10.\n- A `Set` of letters loses multiplicity: `\"aab\"` and `\"abb\"` are not anagrams.",
        follow_up="For Unicode input, sort the code points (`[...word].sort()`) instead of using 26 slots.",
    ),
),
dict(
    id="js-top-k-frequent-elements", title="Top K Frequent Elements", difficulty="Medium", pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/top-k-frequent-elements/",
    neetcode="https://neetcode.io/problems/top-k-elements-in-list",
    kind="js", entry="topKFrequent", compare="unordered",
    description=r"""
Given an integer array `nums` and an integer `k`, return the `k` values that occur most often. The answer is
guaranteed to be unique (no ties at the cut-off), and you may return the values in any order.

- `1 <= nums.length <= 10^5`, `1 <= k <=` number of distinct values

**Example 1:** `nums = [5,5,5,2,2,9], k = 2` → `[5, 2]`

**Example 2:** `nums = [4], k = 1` → `[4]`

Aim for better than O(n log n).
""",
    starter="function topKFrequent(nums, k) {\n  // your code\n}\n",
    solution=r'''function topKFrequent(nums, k) {
  const freq = new Map();
  for (const x of nums) freq.set(x, (freq.get(x) || 0) + 1);
  // bucket[c] holds the values that occur exactly c times
  const bucket = Array.from({ length: nums.length + 1 }, () => []);
  for (const [value, c] of freq) bucket[c].push(value);
  const out = [];
  for (let c = nums.length; c >= 1 && out.length < k; c--) {
    for (const v of bucket[c]) {
      out.push(v);
      if (out.length === k) break;
    }
  }
  return out;
}
''',
    tests=[[[5, 5, 5, 2, 2, 9], 2], [[4], 1], [[1, 1, 1, 2, 2, 3], 2], [[-1, -1, 7], 1], [[3, 0, 1, 0], 1],
           [[1, 2, 3, 4], 4], [[10, 10, 9, 9, 9, 100, 100, 100, 100], 3], [[2, 2, 10, 10, 10], 1],
           [[7] * 50 + [8] * 40 + [9] * 30 + list(range(100, 120)), 3],
           [[i % 1000 for i in range(30000)] + [5] * 10 + [6] * 5, 2]],
    examples=2,
    wrong_solutions=[
        "function topKFrequent(nums, k) {\n  const f = new Map();\n  for (const x of nums) f.set(x, (f.get(x) || 0) + 1);\n  return [...f.keys()].sort().slice(0, k);\n}\n",
        "function topKFrequent(nums, k) {\n  const f = new Map();\n  for (const x of nums) f.set(x, (f.get(x) || 0) + 1);\n  return [...f.entries()].sort((a, b) => a[1] - b[1]).slice(0, k).map(e => e[0]);\n}\n",
    ],
    guide=G(
        prereqs="Counting with a `Map`; iterating a `Map` with `for (const [key, value] of map)`; `Array.from` with a factory.",
        intuition="First count, then pick the biggest counts. A count can never exceed `n`, so instead of sorting you can drop each value into a bucket indexed by its count and read the buckets from high to low.",
        hints=[
            "Start with a frequency `Map`.",
            "Sorting the entries by count descending gives an O(n log n) answer.",
            "For O(n): an array of `n + 1` buckets where `bucket[c]` lists values seen `c` times.",
        ],
        brute_force="Count with a `Map`, then `[...freq].sort((a, b) => b[1] - a[1]).slice(0, k)`: O(n log n). Perfectly acceptable to say first in an interview.",
        approach="1. Count: `freq.set(x, (freq.get(x) || 0) + 1)`.\n2. Make `n + 1` empty buckets with `Array.from({ length: n + 1 }, () => [])` (not `new Array(n + 1).fill([])`, which shares ONE array).\n3. Put each value in `bucket[count]`.\n4. Walk counts from `n` down to 1, collecting values until you have `k`.",
        complexity="Time O(n), space O(n). A size-k min-heap gives O(n log k), useful when values stream in.",
        pitfalls="- `new Array(n).fill([])` fills every slot with the **same** array: pushing to one bucket pushes to all.\n- Sorting entries ascending instead of descending returns the *least* frequent values.\n- Default `sort()` on numbers sorts as strings.",
        follow_up="Top K Frequent Words adds a tie-break (alphabetical): sort with a two-key comparator.",
    ),
),
dict(
    id="js-product-of-array-except-self", title="Product of Array Except Self", difficulty="Medium", pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/product-of-array-except-self/",
    neetcode="https://neetcode.io/problems/products-of-array-discluding-self",
    kind="js", entry="productExceptSelf",
    description=r"""
Given an integer array `nums`, return an array `answer` where `answer[i]` is the product of every element
**except** `nums[i]`. Do it in O(n) time **without using division**. All products fit in a 32-bit integer.

- `2 <= nums.length <= 10^5`, `-30 <= nums[i] <= 30`

**Example 1:** `[1, 2, 3, 4]` → `[24, 12, 8, 6]`

**Example 2:** `[-1, 1, 0, -3, 3]` → `[0, 0, 9, 0, 0]`

Note: JavaScript has a negative zero. Products such as `0 * -3` give `-0`, which serialises to JSON as `0`, so
it will not hurt you here, but the lesson on numbers explains where `-0` does matter.
""",
    starter="function productExceptSelf(nums) {\n  // your code\n}\n",
    solution=r'''function productExceptSelf(nums) {
  const n = nums.length;
  const out = new Array(n).fill(1);
  let prefix = 1;
  for (let i = 0; i < n; i++) {   // out[i] = product of everything to the left
    out[i] = prefix;
    prefix *= nums[i];
  }
  let suffix = 1;
  for (let i = n - 1; i >= 0; i--) { // multiply in everything to the right
    out[i] *= suffix;
    suffix *= nums[i];
  }
  return out;
}
''',
    tests=[[[1, 2, 3, 4]], [[-1, 1, 0, -3, 3]], [[2, 3]], [[0, 0]], [[0, 4, 5]], [[-2, -3, -4]], [[1, 1, 1, 1, 1]],
           [[5, 0, 2, 0]], [[3, -1, 2, 1, -2, 1]], [[(i % 3) - 1 if i % 3 else 1 for i in range(2000)]]],
    wrong_solutions=[
        "function productExceptSelf(nums) {\n  const total = nums.reduce((a, b) => a * b, 1);\n  return nums.map(x => total / x);\n}\n",
        "function productExceptSelf(nums) {\n  const out = [];\n  let p = 1;\n  for (let i = 0; i < nums.length; i++) { out.push(p); p *= nums[i]; }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="Prefix products (the same idea as prefix sums in the lesson *Pattern map I*); `new Array(n).fill(1)`.",
        intuition="The answer at `i` is (product of everything left of `i`) times (product of everything right of `i`). Sweep left-to-right to fill the left part, then right-to-left multiplying in the right part.",
        hints=[
            "Why does dividing the total product fail? Think about zeros.",
            "Write `answer[i] = left[i] * right[i]` where `left[i]` is the product of `nums[0..i-1]`.",
            "You can store `left` in the output array and keep `right` as a single running number.",
        ],
        brute_force="For each `i`, multiply all other elements: O(n^2). Dividing the total product is O(n) but breaks on zeros (division by zero gives `Infinity` or `NaN` in JS, not an error).",
        approach="1. `out = new Array(n).fill(1)`, `prefix = 1`.\n2. Left pass: `out[i] = prefix; prefix *= nums[i]`.\n3. Right pass with `suffix = 1`: `out[i] *= suffix; suffix *= nums[i]`.\n\n**Dry run** `[1,2,3,4]`: after the left pass `out = [1,1,2,6]`; the right pass visits indices 3, 2, 1, 0 with suffix 1, 4, 12, 24, giving `[24,12,8,6]`.",
        complexity="Time O(n), space O(1) extra besides the output array.",
        pitfalls="- Division-based code returns `NaN` (`0/0`) or `Infinity` silently: JavaScript does not throw on division by zero.\n- Forgetting the right pass returns only prefix products.\n- `-0` appears for products like `-3 * 0`; `Object.is(-0, 0)` is false, but `===` and JSON treat it as 0.",
        follow_up="Range-product queries on a changing array need a segment tree; prefix products only work for static data.",
    ),
),
dict(
    id="js-longest-consecutive-sequence", title="Longest Consecutive Sequence", difficulty="Medium", pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/longest-consecutive-sequence/",
    neetcode="https://neetcode.io/problems/longest-consecutive-sequence",
    kind="js", entry="longestConsecutive",
    description=r"""
Given an unsorted integer array `nums`, return the length of the longest run of **consecutive integers**
(such as 4, 5, 6, 7) that can be formed from its values. The values do not have to be adjacent in the array.
Duplicates count once. Solve it in O(n).

- `0 <= nums.length <= 10^5`, `-10^9 <= nums[i] <= 10^9`

**Example 1:** `[100, 4, 200, 1, 3, 2]` → `4` (1, 2, 3, 4)

**Example 2:** `[]` → `0`
""",
    starter="function longestConsecutive(nums) {\n  // your code\n}\n",
    solution=r'''function longestConsecutive(nums) {
  const set = new Set(nums);
  let best = 0;
  for (const x of set) {
    if (set.has(x - 1)) continue;     // x is not the start of a run
    let len = 1;
    while (set.has(x + len)) len++;
    if (len > best) best = len;
  }
  return best;
}
''',
    tests=[[[100, 4, 200, 1, 3, 2]], [[]], [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]], [[1, 2, 0, 1]], [[5]], [[9, 1, -3, 2, 4, 8, 3, -1, 6, -2, -4, 7]],
           [[1, 1, 1]], [[-1, -2, -3, 10, 11]], [[10**9, -10**9, 10**9 - 1]], [list(range(20000, 0, -1))],
           [[i * 2 for i in range(10000)]]],
    examples=2,
    wrong_solutions=[
        "function longestConsecutive(nums) {\n  const s = [...nums].sort();\n  let best = s.length ? 1 : 0, cur = 1;\n  for (let i = 1; i < s.length; i++) {\n    if (s[i] === s[i - 1]) continue;\n    cur = s[i] === s[i - 1] + 1 ? cur + 1 : 1;\n    best = Math.max(best, cur);\n  }\n  return best;\n}\n",
        "function longestConsecutive(nums) {\n  const s = [...nums].sort((a, b) => a - b);\n  let best = s.length ? 1 : 0, cur = 1;\n  for (let i = 1; i < s.length; i++) {\n    cur = s[i] === s[i - 1] + 1 ? cur + 1 : 1;\n    best = Math.max(best, cur);\n  }\n  return best;\n}\n",
    ],
    guide=G(
        prereqs="`Set` construction from an array, `has`, and iterating a `Set` with `for...of`.",
        intuition="Only start counting at the **beginning** of a run, that is, at a value `x` whose predecessor `x - 1` is missing. Each run is then walked exactly once, so the total work is linear.",
        hints=[
            "Put all values into a `Set` for O(1) lookups.",
            "How can you tell that `x` is the smallest number of its run?",
            "From each run start, count upward while `set.has(x + len)`.",
        ],
        brute_force="Sort numerically and scan, resetting the count on gaps and skipping duplicates: O(n log n). Starting a count from **every** value without the start check is O(n^2) on an input like 1..n.",
        approach="1. `const set = new Set(nums)` (this also removes duplicates).\n2. For each `x` in the set: skip it if `set.has(x - 1)`.\n3. Otherwise count `len` while `set.has(x + len)`; update `best`.\n\n**Dry run** `[100,4,200,1,3,2]`: 100 is a start (len 1), 4 is not (3 exists), 200 start (1), 1 start: 2,3,4 present → len 4.",
        complexity="Time O(n): every value is visited by at most one inner while-loop. Space O(n).",
        pitfalls="- Default `sort()` puts `10` before `9`: the sorted-scan version must use `(a, b) => a - b`.\n- In the sorted version, duplicates must be skipped rather than resetting the run.\n- Iterate over the **set**, not `nums`: with many duplicates of a run start, iterating `nums` repeats the inner walk.",
        follow_up="Union-find over values also solves it in near-linear time and generalises to merging ranges online.",
    ),
),
]
