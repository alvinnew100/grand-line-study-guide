"""DSA in JavaScript: Two Pointers and Sliding Window problems."""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


rng = random.Random(11)
SORTED_BIG = sorted(rng.sample(range(-50000, 50000), 6000))
THREE_RAND = [rng.randint(-40, 40) for _ in range(300)]
HEIGHTS = [rng.randint(0, 10000) for _ in range(20000)]
PRICES = [rng.randint(1, 10000) for _ in range(20000)]
LONG_S = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(20000))
WIN_NUMS = [rng.randint(-10000, 10000) for _ in range(8000)]

PROBLEMS = [
dict(
    id="js-valid-palindrome", title="Valid Palindrome", difficulty="Easy", pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/valid-palindrome/",
    neetcode="https://neetcode.io/problems/is-palindrome",
    kind="js", entry="isPalindrome",
    description=r"""
A phrase is a **palindrome** if, after converting all uppercase letters to lowercase and throwing away every
character that is not a letter or a digit, it reads the same forwards and backwards. Given a string `s`, return
`true` if it is a palindrome.

- `1 <= s.length <= 2 * 10^5`, printable ASCII characters only

**Example 1:** `"Was it a car or a cat I saw?"` → `true`

**Example 2:** `"tab a cat"` → `false`
""",
    starter="function isPalindrome(s) {\n  // your code\n}\n",
    solution=r'''function isAlnum(code) {
  return (code >= 48 && code <= 57) || (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
}
function isPalindrome(s) {
  let i = 0, j = s.length - 1;
  while (i < j) {
    while (i < j && !isAlnum(s.charCodeAt(i))) i++;
    while (i < j && !isAlnum(s.charCodeAt(j))) j--;
    if (s[i].toLowerCase() !== s[j].toLowerCase()) return false;
    i++;
    j--;
  }
  return true;
}
''',
    tests=[["Was it a car or a cat I saw?"], ["tab a cat"], [" "], ["A man, a plan, a canal: Panama"], ["race a car"],
           ["0P"], ["a."], [".,"], ["ab_a"], ["No 'x' in Nixon"], ["12321"], ["1a2"], ["Aa"],
           ["ab" * 5000 + "ba" * 5000]],
    examples=2,
    wrong_solutions=[
        "function isPalindrome(s) {\n  const t = s.toLowerCase().replace(/[^a-z]/g, '');\n  return t === [...t].reverse().join('');\n}\n",
        "function isPalindrome(s) {\n  const t = s.replace(/[^A-Za-z0-9]/g, '');\n  return t === [...t].reverse().join('');\n}\n",
    ],
    guide=G(
        prereqs="Strings: indexing with `s[i]`, `charCodeAt`, `toLowerCase`; two indices moving towards each other (lesson *Pattern map I*).",
        intuition="Put one pointer at each end. Skip anything that is not a letter or digit, compare the two characters case-insensitively, and move both pointers inwards.",
        hints=[
            "Cleaning the string first with a regular expression is a fine O(n) start.",
            "To avoid the extra string, use `i` from the left and `j` from the right.",
            "Skip non-alphanumeric characters inside small `while` loops guarded by `i < j`.",
        ],
        brute_force="`const t = s.toLowerCase().replace(/[^a-z0-9]/g, \"\")` and compare `t` with its reverse: O(n) time but O(n) extra space. Fine as a first answer.",
        approach="1. `i = 0`, `j = s.length - 1`.\n2. While `i < j`: advance `i` past non-alphanumerics, retreat `j` likewise.\n3. Compare lowercase characters; mismatch → `false`.\n4. Move both inwards. Finishing the loop → `true`.\n\n**Dry run** `\"0P\"`: compare `\"0\"` with `\"p\"` → different → `false` (digits count!).",
        complexity="Time O(n), space O(1).",
        pitfalls="- Digits are kept: `\"0P\"` is not a palindrome, and a regex like `/[^a-z]/` that drops digits gets it wrong.\n- Forgetting `i < j` in the skip loops runs past the middle on strings like `\".,\"`.\n- `[...t].reverse().join(\"\")` is the idiomatic way to reverse a string; strings themselves have no `reverse` method.",
        follow_up="Valid Palindrome II allows deleting one character: on the first mismatch, try skipping either side once.",
    ),
),
dict(
    id="js-two-sum-ii-input-array-is-sorted", title="Two Sum II - Input Array Is Sorted", difficulty="Medium", pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/",
    neetcode="https://neetcode.io/problems/two-integer-sum-ii",
    kind="js", entry="twoSum",
    description=r"""
`numbers` is sorted in non-decreasing order. Find the two entries that add up to `target` and return their
positions as a **1-based** pair `[index1, index2]` with `index1 < index2`. Exactly one answer exists, and you
must use only O(1) extra space.

- `2 <= numbers.length <= 3 * 10^4`

**Example 1:** `numbers = [1, 3, 4, 8], target = 7` → `[2, 3]` (3 + 4)

**Example 2:** `numbers = [-5, -1], target = -6` → `[1, 2]`
""",
    starter="function twoSum(numbers, target) {\n  // return 1-based [index1, index2]\n}\n",
    solution=r'''function twoSum(numbers, target) {
  let i = 0, j = numbers.length - 1;
  while (i < j) {
    const sum = numbers[i] + numbers[j];
    if (sum === target) return [i + 1, j + 1];
    if (sum < target) i++;     // need a bigger sum
    else j--;                  // need a smaller sum
  }
  return [];
}
''',
    tests=[[[1, 3, 4, 8], 7], [[-5, -1], -6], [[2, 7, 11, 15], 9], [[2, 3, 4], 6], [[-1, 0], -1], [[1, 1, 2, 9], 2],
           [[0, 0, 3, 4], 0], [[-10, -3, 0, 5, 9], -13], [[1, 2, 3, 4, 4, 9, 56, 90], 8],
           [SORTED_BIG, SORTED_BIG[1234] + SORTED_BIG[5555]]],
    examples=2,
    wrong_solutions=[
        "function twoSum(numbers, target) {\n  let i = 0, j = numbers.length - 1;\n  while (i < j) {\n    const s = numbers[i] + numbers[j];\n    if (s === target) return [i, j];\n    if (s < target) i++; else j--;\n  }\n  return [];\n}\n",
        "function twoSum(numbers, target) {\n  for (let i = 0; i + 1 < numbers.length; i++) if (numbers[i] + numbers[i + 1] === target) return [i + 1, i + 2];\n  return [1, 2];\n}\n",
    ],
    guide=G(
        prereqs="Two pointers from both ends (lesson *Pattern map I*), and the hash-map Two Sum.",
        intuition="Look at the smallest and largest values. If their sum is too small, the smallest value can never be part of the answer (pairing it with the largest is already too small), so discard it. If too big, discard the largest. Each step removes one candidate.",
        hints=[
            "The array is sorted: use that instead of a `Map`.",
            "Start with `i = 0` and `j = n - 1`.",
            "Sum too small → `i++`; too large → `j--`. Return 1-based indices.",
        ],
        brute_force="Nested loops over all pairs: O(n^2). The hash-map method is O(n) but uses O(n) space, which the problem forbids.",
        approach="1. `i = 0`, `j = n - 1`.\n2. Compute `sum`; equal → return `[i + 1, j + 1]`.\n3. Smaller → `i++`; larger → `j--`.\n\n**Dry run** `[1,3,4,8]`, 7: 1+8=9 too big → j=2; 1+4=5 too small → i=1; 3+4=7 → `[2,3]`.",
        complexity="Time O(n), space O(1).",
        pitfalls="- The answer is **1-based**.\n- Use `while (i < j)`, not `<=`: one element cannot be used twice.\n- Numbers are small enough that `numbers[i] + numbers[j]` is exact; with huge values, remember `Number.MAX_SAFE_INTEGER`.",
        follow_up="3Sum fixes one value and runs this exact loop on the rest.",
    ),
),
dict(
    id="js-3sum", title="3Sum", difficulty="Medium", pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/3sum/",
    neetcode="https://neetcode.io/problems/three-integer-sum",
    kind="js", entry="threeSum", compare="unordered_nested",
    description=r"""
Given an integer array `nums`, return every **distinct** triple of values `[a, b, c]` taken from three different
positions such that `a + b + c === 0`. No triple may appear twice (as a set of values). Triples and the values
inside them may be returned in any order.

- `3 <= nums.length <= 3000`, `-10^5 <= nums[i] <= 10^5`

**Example 1:** `[-1, 0, 1, 2, -1, -4]` → `[[-1, -1, 2], [-1, 0, 1]]`

**Example 2:** `[0, 0, 0, 0]` → `[[0, 0, 0]]`
""",
    starter="function threeSum(nums) {\n  const result = [];\n  // your code\n  return result;\n}\n",
    solution=r'''function threeSum(nums) {
  const a = [...nums].sort((x, y) => x - y);   // numeric sort on a copy
  const res = [];
  for (let i = 0; i < a.length - 2; i++) {
    if (a[i] > 0) break;                        // smallest value positive: no more triples
    if (i > 0 && a[i] === a[i - 1]) continue;   // same first value as before
    let lo = i + 1, hi = a.length - 1;
    while (lo < hi) {
      const s = a[i] + a[lo] + a[hi];
      if (s < 0) lo++;
      else if (s > 0) hi--;
      else {
        res.push([a[i], a[lo], a[hi]]);
        lo++;
        hi--;
        while (lo < hi && a[lo] === a[lo - 1]) lo++;   // skip equal second values
      }
    }
  }
  return res;
}
''',
    tests=[[[-1, 0, 1, 2, -1, -4]], [[0, 0, 0, 0]], [[0, 1, 1]], [[0, 0, 0]], [[-2, 0, 1, 1, 2]], [[1, 2, -2, -1]],
           [[-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6]], [[3, -2, 1, 0]], [[-10, 5, 5, 10, -5, 0, -15]],
           [[100000, -100000, 0, 50000, -50000]], [THREE_RAND]],
    examples=2,
    wrong_solutions=[
        "function threeSum(nums) {\n  const a = [...nums].sort((x, y) => x - y), res = [];\n  for (let i = 0; i < a.length - 2; i++) {\n    let lo = i + 1, hi = a.length - 1;\n    while (lo < hi) {\n      const s = a[i] + a[lo] + a[hi];\n      if (s < 0) lo++; else if (s > 0) hi--; else { res.push([a[i], a[lo], a[hi]]); lo++; hi--; }\n    }\n  }\n  return res;\n}\n",
        "function threeSum(nums) {\n  const a = [...nums].sort(), res = [];\n  for (let i = 0; i < a.length - 2; i++) {\n    if (i > 0 && a[i] === a[i - 1]) continue;\n    let lo = i + 1, hi = a.length - 1;\n    while (lo < hi) {\n      const s = a[i] + a[lo] + a[hi];\n      if (s < 0) lo++; else if (s > 0) hi--; else { res.push([a[i], a[lo], a[hi]]); lo++; hi--; while (lo < hi && a[lo] === a[lo - 1]) lo++; }\n    }\n  }\n  return res;\n}\n",
    ],
    guide=G(
        prereqs="Two Sum II (two pointers on a sorted array) and numeric sort comparators (lesson *Numbers and sorting without surprises*).",
        intuition="Sort the values. Fix the first value `a[i]`; the problem becomes Two Sum II on the part to its right with target `-a[i]`. Sorting also makes duplicates adjacent, so skipping repeats is a one-line check.",
        hints=[
            "Sort a copy with `(x, y) => x - y`. Why not plain `sort()`?",
            "For each `i`, run two pointers `lo = i + 1`, `hi = n - 1`.",
            "Skip `i` when `a[i] === a[i - 1]`, and after a hit skip `lo` past equal values.",
        ],
        brute_force="Three nested loops plus a `Set` of sorted-triple strings to remove duplicates: O(n^3), too slow for n = 3000.",
        approach="1. `a = [...nums].sort((x, y) => x - y)`.\n2. For each `i` (stop early once `a[i] > 0`): skip duplicate first values.\n3. Two pointers: sum < 0 → `lo++`; sum > 0 → `hi--`; zero → record, move both, then skip duplicate `lo` values.\n\n**Dry run** sorted `[-4,-1,-1,0,1,2]`: i=0 (-4) finds nothing; i=1 (-1): lo=-1, hi=2 → hit `[-1,-1,2]`; next lo=0, hi=1 → hit `[-1,0,1]`; i=2 is a duplicate -1, skipped.",
        complexity="Time O(n^2) (sorting O(n log n) is dominated). Space O(1) besides the sorted copy and output.",
        pitfalls="- The default `sort()` is lexicographic: `[-1, -4, 2, 10]` sorts as strings into `[-1, -4, 10, 2]`, which breaks the pointer logic.\n- Without duplicate skipping you return `[-1, 0, 1]` several times.\n- `nums.sort` mutates the caller's array; copying with `[...nums]` is polite.",
        follow_up="4Sum adds one more outer loop: O(n^3). k-Sum generalises with recursion down to the two-pointer base case.",
    ),
),
dict(
    id="js-container-with-most-water", title="Container With Most Water", difficulty="Medium", pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/container-with-most-water/",
    neetcode="https://neetcode.io/problems/max-water-container",
    kind="js", entry="maxArea",
    description=r"""
`height[i]` is the height of a vertical wall standing at position `i`. Choose two walls; together with the
ground they form a container whose water level is limited by the **shorter** wall. The amount of water is
`min(height[i], height[j]) * (j - i)`. Return the largest amount any pair can hold.

- `2 <= height.length <= 10^5`, `0 <= height[i] <= 10^4`

**Example 1:** `[1, 7, 2, 5, 4, 7, 3, 6]` → `36` (walls 1 and 7: min(7, 6) * 6)

**Example 2:** `[2, 2]` → `2`
""",
    starter="function maxArea(height) {\n  // your code\n}\n",
    solution=r'''function maxArea(height) {
  let i = 0, j = height.length - 1, best = 0;
  while (i < j) {
    const h = Math.min(height[i], height[j]);
    best = Math.max(best, h * (j - i));
    if (height[i] < height[j]) i++;   // the shorter wall limits every narrower pair
    else j--;
  }
  return best;
}
''',
    tests=[[[1, 7, 2, 5, 4, 7, 3, 6]], [[2, 2]], [[1, 8, 6, 2, 5, 4, 8, 3, 7]], [[1, 1]], [[0, 0, 0]], [[4, 3, 2, 1, 4]],
           [[1, 2, 1]], [[1, 2, 4, 3]], [[10, 1, 1, 1, 1, 1, 10]], [[0, 10000]], [HEIGHTS]],
    examples=2,
    wrong_solutions=[
        "function maxArea(h) {\n  let best = 0;\n  for (let i = 0; i + 1 < h.length; i++) best = Math.max(best, Math.min(h[i], h[i + 1]));\n  return best;\n}\n",
        "function maxArea(h) {\n  let i = 0, j = h.length - 1, best = 0;\n  while (i < j) {\n    best = Math.max(best, Math.min(h[i], h[j]) * (j - i));\n    if (h[i] > h[j]) i++; else j--;\n  }\n  return best;\n}\n",
    ],
    guide=G(
        prereqs="Two pointers from both ends; `Math.min` and `Math.max`.",
        intuition="Start with the widest container. The shorter wall limits the height, and every narrower container that keeps that short wall can only be worse (less width, height no taller). So the short wall is useless from now on: move past it.",
        hints=[
            "Start with `i = 0` and `j = n - 1`: the widest pair.",
            "Which wall can you throw away without losing the best answer?",
            "Always move the pointer at the **shorter** wall.",
        ],
        brute_force="Check every pair: O(n^2), about 5 * 10^9 pairs at the upper limit.",
        approach="1. `i = 0`, `j = n - 1`, `best = 0`.\n2. Area = `Math.min(height[i], height[j]) * (j - i)`; update `best`.\n3. Move the pointer at the shorter wall (either one on a tie).\n\n**Dry run** `[1,8,6,2,5,4,8,3,7]`: (0,8) area 8, move i; (1,8) area 7*7=49; move j ... nothing beats 49.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Moving the taller wall can skip the optimum.\n- Width is `j - i`, not `j - i + 1`.\n- Do not confuse this with Trapping Rain Water, which sums water over every position.",
        follow_up="Trapping Rain Water uses the same two pointers with running maxima from both sides.",
    ),
),
dict(
    id="js-best-time-to-buy-and-sell-stock", title="Best Time to Buy and Sell Stock", difficulty="Easy", pattern="Sliding Window",
    leetcode="https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
    neetcode="https://neetcode.io/problems/buy-and-sell-crypto",
    kind="js", entry="maxProfit",
    description=r"""
`prices[d]` is a stock's price on day `d`. You may buy once and sell once, on a **later** day. Return the
largest profit possible, or `0` if no trade makes money.

- `1 <= prices.length <= 10^5`, `0 <= prices[d] <= 10^4`

**Example 1:** `[10, 1, 5, 6, 7, 1]` → `6` (buy at 1, sell at 7)

**Example 2:** `[10, 8, 7, 5, 2]` → `0`
""",
    starter="function maxProfit(prices) {\n  // your code\n}\n",
    solution=r'''function maxProfit(prices) {
  let minSoFar = Infinity, best = 0;
  for (const p of prices) {
    if (p < minSoFar) minSoFar = p;              // cheapest buy day up to now
    else if (p - minSoFar > best) best = p - minSoFar;
  }
  return best;
}
''',
    tests=[[[10, 1, 5, 6, 7, 1]], [[10, 8, 7, 5, 2]], [[7, 1, 5, 3, 6, 4]], [[5]], [[1, 2]], [[2, 1]], [[3, 3, 3]],
           [[2, 4, 1]], [[3, 2, 6, 5, 0, 3]], [[0, 10000]], [PRICES]],
    examples=2,
    wrong_solutions=[
        "function maxProfit(p) {\n  return Math.max(0, Math.max(...p) - Math.min(...p));\n}\n",
        "function maxProfit(p) {\n  let best = 0;\n  for (let i = 1; i < p.length; i++) best = Math.max(best, p[i] - p[i - 1]);\n  return best;\n}\n",
    ],
    guide=G(
        prereqs="A running minimum; `Infinity` as a starting value.",
        intuition="For each possible sell day, the best buy day is the cheapest day **before** it. Keep that running minimum as you scan, and the profit for selling today is `price - minSoFar`.",
        hints=[
            "Fix the sell day. Which buy day is best for it?",
            "Keep `minSoFar`, the lowest price seen so far.",
            "Update the answer with `p - minSoFar` on every day.",
        ],
        brute_force="All pairs `i < j`: O(n^2).",
        approach="1. `minSoFar = Infinity`, `best = 0`.\n2. For each price: if lower than `minSoFar`, update it; else update `best` with `p - minSoFar`.\n\n**Dry run** `[10,1,5,6,7,1]`: min 10, then 1; profits 4, 5, 6; final day 1 does not help → 6.",
        complexity="Time O(n), space O(1).",
        pitfalls="- `Math.max(...p) - Math.min(...p)` ignores order: the max may come before the min. Spreading 10^5 values into `Math.max` can also throw `RangeError` in some engines.\n- Comparing only adjacent days finds the best single-day jump, not the best trade.",
        follow_up="Unlimited trades: add every positive day-to-day difference. With cooldown or fees, use a small state-machine DP.",
    ),
),
dict(
    id="js-longest-substring-without-repeating-characters", title="Longest Substring Without Repeating Characters", difficulty="Medium", pattern="Sliding Window",
    leetcode="https://leetcode.com/problems/longest-substring-without-repeating-characters/",
    neetcode="https://neetcode.io/problems/longest-substring-without-duplicates",
    kind="js", entry="lengthOfLongestSubstring",
    description=r"""
Given a string `s`, return the length of the longest **substring** (a contiguous run of characters) in which
no character appears twice.

- `0 <= s.length <= 5 * 10^4`; letters, digits, symbols and spaces

**Example 1:** `"zxyzxyz"` → `3` (`"zxy"`)

**Example 2:** `"xxxx"` → `1`
""",
    starter="function lengthOfLongestSubstring(s) {\n  // your code\n}\n",
    solution=r'''function lengthOfLongestSubstring(s) {
  const last = new Map();       // character -> last index where it appeared
  let left = 0, best = 0;
  for (let right = 0; right < s.length; right++) {
    const c = s[right];
    if (last.has(c) && last.get(c) >= left) left = last.get(c) + 1;   // jump past the repeat
    last.set(c, right);
    best = Math.max(best, right - left + 1);
  }
  return best;
}
''',
    tests=[["zxyzxyz"], ["xxxx"], [""], [" "], ["abcabcbb"], ["pwwkew"], ["dvdf"], ["abba"], ["tmmzuxt"], ["au"],
           ["a b c a"], ["abcdefghijklmnopqrstuvwxyz"], [LONG_S]],
    examples=2,
    wrong_solutions=[
        "function lengthOfLongestSubstring(s) {\n  const last = new Map();\n  let left = 0, best = 0;\n  for (let r = 0; r < s.length; r++) {\n    if (last.has(s[r])) left = last.get(s[r]) + 1;\n    last.set(s[r], r);\n    best = Math.max(best, r - left + 1);\n  }\n  return best;\n}\n",
        "function lengthOfLongestSubstring(s) {\n  return new Set(s).size;\n}\n",
    ],
    guide=G(
        prereqs="Sliding window with `left` and `right` indices (lesson *Pattern map I*); `Map` from character to index.",
        intuition="Grow a window to the right one character at a time. When the new character already appears **inside** the window, move the left edge just past its previous occurrence. The window always holds distinct characters, so its largest size is the answer.",
        hints=[
            "Keep a window `[left, right]` that never contains a repeat.",
            "Store the last index of each character in a `Map`.",
            "Only jump `left` when that last index is `>= left`, otherwise it is outside the window.",
        ],
        brute_force="Check every substring for uniqueness with a `Set`: O(n^3), or O(n^2) if you extend each start until the first repeat.",
        approach="1. `last = new Map()`, `left = 0`.\n2. For each `right`: if `s[right]` was seen at index `>= left`, set `left` to that index + 1.\n3. Record `last.set(c, right)` and update `best = right - left + 1`.\n\n**Dry run** `\"abba\"`: a(0) b(1) best 2; b again at 1 >= 0 → left 2; a seen at 0 < 2 → ignore; window \"ba\" length 2.",
        complexity="Time O(n), space O(min(n, alphabet)).",
        pitfalls="- Without the `>= left` check, `left` can move **backwards** (`\"abba\"` then reports 3).\n- Counting distinct characters of the whole string (`new Set(s).size`) answers a different question.\n- Strings are indexed by UTF-16 code units; emoji take two units. Fine for ASCII interview inputs.",
        follow_up="Longest Repeating Character Replacement and Permutation in String use the same window with a count array.",
    ),
),
dict(
    id="js-minimum-window-substring", title="Minimum Window Substring", difficulty="Hard", pattern="Sliding Window",
    leetcode="https://leetcode.com/problems/minimum-window-substring/",
    neetcode="https://neetcode.io/problems/minimum-window-with-characters",
    kind="js", entry="minWindow",
    description=r"""
Given strings `s` and `t`, return the shortest substring of `s` that contains every character of `t`,
**including repeats** (if `t` has two `a`s, the window needs at least two). If no such window exists, return
the empty string `""`. The shortest window is unique whenever one exists.

- `1 <= s.length, t.length <= 10^5`; upper and lower case English letters

**Example 1:** `s = "OUZODYXAZV", t = "XYZ"` → `"YXAZ"`

**Example 2:** `s = "xyz", t = "xyzz"` → `""`
""",
    starter="function minWindow(s, t) {\n  // your code\n}\n",
    solution=r'''function minWindow(s, t) {
  if (t.length > s.length) return "";
  const need = new Map();
  for (const c of t) need.set(c, (need.get(c) || 0) + 1);
  let missing = t.length;           // characters of t not yet covered
  let left = 0, bestStart = 0, bestLen = Infinity;
  for (let right = 0; right < s.length; right++) {
    const c = s[right];
    if (need.has(c)) {
      if (need.get(c) > 0) missing--;
      need.set(c, need.get(c) - 1);   // may go negative: surplus copies
    }
    while (missing === 0) {
      if (right - left + 1 < bestLen) { bestLen = right - left + 1; bestStart = left; }
      const d = s[left++];
      if (need.has(d)) {
        need.set(d, need.get(d) + 1);
        if (need.get(d) > 0) missing++;
      }
    }
  }
  return bestLen === Infinity ? "" : s.slice(bestStart, bestStart + bestLen);
}
''',
    tests=[["OUZODYXAZV", "XYZ"], ["xyz", "xyzz"], ["ADOBECODEBANC", "ABC"], ["a", "a"], ["a", "aa"], ["a", "b"],
           ["ab", "b"], ["aa", "aa"], ["bba", "ab"], ["cabwefgewcwaefgcf", "cae"], ["aAbB", "AB"],
           ["x" * 30000 + "abc" + "y" * 30000, "cba"]],
    examples=2,
    wrong_solutions=[
        "function minWindow(s, t) {\n  const need = new Set(t), have = new Map();\n  let formed = 0, left = 0, best = '';\n  for (let r = 0; r < s.length; r++) {\n    const c = s[r];\n    if (need.has(c)) { have.set(c, (have.get(c) || 0) + 1); if (have.get(c) === 1) formed++; }\n    while (formed === need.size) {\n      if (best === '' || r - left + 1 < best.length) best = s.slice(left, r + 1);\n      const d = s[left++];\n      if (need.has(d)) { have.set(d, have.get(d) - 1); if (have.get(d) === 0) formed--; }\n    }\n  }\n  return best;\n}\n",
        "function minWindow(s, t) {\n  return s.includes(t) ? t : '';\n}\n",
    ],
    guide=G(
        prereqs="The variable-size sliding window (lesson *Pattern map I*) and counting with a `Map`.",
        intuition="Expand the right edge until the window covers everything in `t`, then shrink the left edge as long as it still covers. Every time the window is valid, it is a candidate. A single counter `missing` tells you in O(1) whether the window is valid.",
        hints=[
            "Count what you need from `t` in a `Map`.",
            "Keep `missing`, the number of characters of `t` still uncovered (repeats included).",
            "While `missing === 0`, record the window and move `left` forward, giving characters back.",
        ],
        brute_force="Check every substring and compare counts: O(n^2) substrings times O(n) checks. Way too slow at 10^5.",
        approach="1. `need` counts of `t`; `missing = t.length`.\n2. Add `s[right]`: if its need was positive, `missing--`; decrement its need (negative means surplus).\n3. While `missing === 0`: update best, remove `s[left]` (increment its need; if it became positive, `missing++`), `left++`.\n4. Return the best slice or `\"\"`.",
        complexity="Time O(|s| + |t|): each index enters and leaves the window once. Space O(alphabet).",
        pitfalls="- Using a `Set` for `t` ignores repeats (`t = \"aa\"`).\n- Upper and lower case are different characters.\n- Track the start and length, then slice once at the end; slicing on every candidate makes it O(n^2).",
        follow_up="Find All Anagrams in a String and Permutation in String are the fixed-size versions of this window.",
    ),
),
dict(
    id="js-sliding-window-maximum", title="Sliding Window Maximum", difficulty="Hard", pattern="Sliding Window",
    leetcode="https://leetcode.com/problems/sliding-window-maximum/",
    neetcode="https://neetcode.io/problems/sliding-window-maximum",
    kind="js", entry="maxSlidingWindow",
    description=r"""
A window of size `k` slides over `nums` from left to right, one step at a time. Return an array with the
maximum of each window position (there are `n - k + 1` of them).

- `1 <= k <= nums.length <= 10^5`, `-10^4 <= nums[i] <= 10^4`

**Example 1:** `nums = [1, 2, 1, 0, 4, 2, 6], k = 3` → `[2, 2, 4, 4, 6]`

**Example 2:** `nums = [5], k = 1` → `[5]`

JavaScript has no built-in deque, and `Array.prototype.shift` is O(n). Use an array plus a head index.
""",
    starter="function maxSlidingWindow(nums, k) {\n  // your code\n}\n",
    solution=r'''function maxSlidingWindow(nums, k) {
  const dq = new Array(nums.length);   // indices; values decreasing from head to tail
  let head = 0, tail = 0;              // live part is dq[head..tail-1]
  const out = [];
  for (let i = 0; i < nums.length; i++) {
    while (tail > head && nums[dq[tail - 1]] <= nums[i]) tail--;   // pop smaller from the back
    dq[tail++] = i;
    if (dq[head] <= i - k) head++;                               // front left the window
    if (i >= k - 1) out.push(nums[dq[head]]);
  }
  return out;
}
''',
    tests=[[[1, 2, 1, 0, 4, 2, 6], 3], [[5], 1], [[1, 3, -1, -3, 5, 3, 6, 7], 3], [[1, -1], 1], [[9, 11], 2],
           [[4, -2], 2], [[7, 2, 4], 2], [[1, 3, 1, 2, 0, 5], 3], [[-7, -8, 7, 5, 7, 1, 6, 0], 4], [[2, 2, 2, 2], 2],
           [[5, 4, 3, 2, 1], 5], [WIN_NUMS, 500], [WIN_NUMS, 1]],
    examples=2,
    wrong_solutions=[
        "function maxSlidingWindow(nums, k) {\n  const out = [];\n  for (let i = 0; i + k <= nums.length; i++) out.push(Math.max(nums[i], nums[i + k - 1]));\n  return out;\n}\n",
        "function maxSlidingWindow(nums, k) {\n  const out = [];\n  let m = -Infinity;\n  for (let i = 0; i < nums.length; i++) { m = Math.max(m, nums[i]); if (i >= k - 1) out.push(m); }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="The lesson *Stacks, queues and deques in JavaScript* (head-index deque), and the monotonic deque idea.",
        intuition="Keep the indices of useful candidates in a deque whose values decrease from front to back. A new value kicks out every smaller value at the back (they can never be a maximum again while the new one is in the window). The front is always the current maximum; drop it once it leaves the window.",
        hints=[
            "Store **indices**, not values, so you can tell when the front has left the window.",
            "Before pushing `i`, pop indices from the back whose values are `<= nums[i]`.",
            "Use an array plus a `head` pointer instead of `shift()`.",
        ],
        brute_force="Compute `Math.max` over each window: O(n * k), up to 10^10 operations. A max-heap with lazy deletion gives O(n log n).",
        approach="1. Pre-size an index array `dq`, with `head` and `tail` pointers.\n2. For each `i`: pop back while `nums[dq[tail-1]] <= nums[i]`; push `i`.\n3. If `dq[head] <= i - k`, advance `head`.\n4. Once `i >= k - 1`, output `nums[dq[head]]`.\n\n**Dry run** `[1,2,1,0,4,2,6]`, k 3: deque after i=2 holds values [2,1] → 2; i=3 [2,1,0] → 2; i=4: 4 clears all → 4; i=5 [4,2] → 4; i=6 → 6.",
        complexity="Time O(n): each index is pushed once and removed at most once. Space O(n) for the index array (O(k) live).",
        pitfalls="- `dq.shift()` inside the loop is O(k) per call in the worst case and turns the solution quadratic.\n- Storing values instead of indices makes expiry impossible to detect with duplicates.\n- Spreading a large window into `Math.max(...window)` is O(k) and can overflow the argument limit.",
        follow_up="The same deque gives the minimum, and powers problems like Shortest Subarray with Sum at Least K.",
    ),
),
]
