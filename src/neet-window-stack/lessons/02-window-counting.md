# Counting windows: frequency maps and "need / have"

## Before this lesson

- [Sliding windows: fixed vs variable](#/lesson/neet-window-stack/window-fundamentals) — you need the two templates (fixed size, and
  grow/shrink) and the idea of a window *invariant*.
- Python dictionaries: creating one, reading `d[key]`, `d.get(key, 0)`, and deleting with `del d[key]`.
- `ord(ch)` — the built-in that turns a character into its number code (`ord('a')` is 97, `ord('A')` is 65).

## In plain words

Suppose you have a bag of letter tiles and want to know whether it contains the letters needed to spell a
word. You would not compare the bag with the word tile by tile, over and over. You would keep a **tally**: a
small table saying "3 × A, 1 × B, 2 × N". Two bags hold the same letters exactly when their tallies are equal.

A **frequency table** (also called a *frequency map* or *counter*) is that tally: for each distinct item, how
many times it occurs. This lesson keeps such a tally for the items currently inside a sliding window. When the
window moves, exactly one count goes up (the item that entered) and one goes down (the item that left) — so the
tally is never recounted from zero.

Why it matters: "does this text contain a rearrangement of that word?", "what is the shortest log excerpt that
mentions all of these error codes?", "how many product types did the customer browse in a row?" are tally
questions. They show up in search features, fraud detection, bioinformatics and, very often, interviews.

New words you will meet:

- **Anagram / permutation** of a word: the same letters in a different order (`"listen"` / `"silent"`).
- **Multiplicity**: how many copies of something are required. `"aab"` needs the letter `a` with multiplicity 2.
- **Alphabet** (written Σ, the Greek letter sigma): the set of characters that may appear — 26 for lowercase
  English letters.

The first lesson treated the window's state as something small — a sum, a set. A large family of string
problems needs a richer state: **how many times each character occurs in the window**. "Is this window an
anagram of `p`?", "does it contain every character of `t`?", "how many distinct values does it hold?", "how
many characters are *not* the majority letter?" — all are questions about a frequency table.

This lesson shows how to keep a frequency table in sync with a sliding window in O(1) per step, how to test
the window condition **without rescanning the table**, and walks through the two hardest window problems in
the NeetCode list: *Permutation in String* and *Minimum Window Substring*.

## 1. Frequency tables in Python

Three common representations:

| Representation | Good for | Notes |
|---|---|---|
| `[0] * 26` with `ord(ch) - ord('a')` | lowercase-only strings | fastest; comparison `a == b` is O(26) |
| `dict` / `collections.Counter` | arbitrary characters or numbers | `Counter` returns 0 for missing keys |
| `defaultdict(int)` | arbitrary keys, explicit deletes | delete keys at 0 if you use `len()` |

```python-run
from collections import Counter
c = Counter("banana")
print(c)                 # Counter({'a': 3, 'n': 2, 'b': 1})
print(c["z"])            # 0 — missing keys count as zero
c["a"] -= 3
print(len(c), +c)        # len still counts 'a' (value 0); unary + drops non-positive entries
```

> [!WARNING]
> `Counter` keeps keys whose count fell to zero. If "number of distinct characters" is part of your window
> condition (e.g. *Fruit Into Baskets*: at most two types), **delete** a key when it reaches zero, or the
> distinct count will be wrong.

## 2. The anagram window (fixed size)

Two strings are anagrams iff their frequency tables are equal. So "does `s2` contain a permutation of `s1`?"
becomes: does some window of length `m = len(s1)` in `s2` have the same table as `s1`?

### 2.1 Straightforward version: compare tables each step

```python-run
def check_inclusion(s1, s2):
    m = len(s1)
    if m > len(s2):
        return False
    need = [0] * 26
    win = [0] * 26
    for ch in s1:
        need[ord(ch) - 97] += 1
    for i, ch in enumerate(s2):
        win[ord(ch) - 97] += 1
        if i >= m:
            win[ord(s2[i - m]) - 97] -= 1
        if i >= m - 1 and win == need:      # O(26) comparison
            return True
    return False

print(check_inclusion("ab", "eidbaooo"), check_inclusion("ab", "eidboaoo"))
```

This is O(26·n) — linear, and perfectly acceptable in an interview. But there is a neat refinement that
interviewers love, because it generalises to large alphabets.

### 2.2 The `matches` counter: O(1) per step

Keep `matches` = the number of slots `c` (out of 26) where `win[c] == need[c]`. A step changes only two slots
(the entering and the leaving character), so `matches` can be updated by looking at only those two slots:

- after incrementing `win[c]`: if it now **equals** `need[c]`, `matches += 1`; if it was equal **just before**
  (i.e. now equals `need[c] + 1`), `matches -= 1`;
- after decrementing: symmetric (`== need[c]` → +1; `== need[c] - 1` → −1).

The window is an anagram exactly when `matches == 26`.

```python-run
def check_inclusion_fast(s1, s2):
    m, n = len(s1), len(s2)
    if m > n:
        return False
    need, win = [0] * 26, [0] * 26
    for ch in s1: need[ord(ch) - 97] += 1
    for ch in s2[:m]: win[ord(ch) - 97] += 1
    matches = sum(need[i] == win[i] for i in range(26))
    for r in range(m, n):
        if matches == 26:
            return True
        i = ord(s2[r]) - 97                 # entering
        win[i] += 1
        if win[i] == need[i]: matches += 1
        elif win[i] == need[i] + 1: matches -= 1
        j = ord(s2[r - m]) - 97             # leaving
        win[j] -= 1
        if win[j] == need[j]: matches += 1
        elif win[j] == need[j] - 1: matches -= 1
    return matches == 26

print(check_inclusion_fast("adc", "dcda"), check_inclusion_fast("hello", "ooolleoooleh"))
```

Notice the final `return matches == 26` — the loop checks a window **before** sliding, so the last window
needs a separate check. Forgetting it is a classic off-by-one.

*Find All Anagrams in a String* is the same code that collects every start index `r - m + 1` instead of
returning early.

## 3. The "need / missing" window (variable size)

*Minimum Window Substring*: find the shortest substring of `s` containing every character of `t` **with
multiplicity**. The window is variable — the answer's length is unknown — and we want the *shortest* valid
window, so we use the "shrink while valid" template from lesson 1.

Validity check: "for every character `c`, `window[c] >= need[c]`". Testing that over the whole alphabet each
step costs O(Σ). Instead maintain a single integer:

> **`missing`** = the number of characters of `t` (counted with multiplicity) that the window still lacks.

Initially `missing = len(t)`. Implement with one dict `need` that starts as `Counter(t)` and is
**decremented** when a character enters the window:

- if `need[ch] > 0` before decrementing, this character was genuinely needed → `missing -= 1`;
- if `need[ch] <= 0`, it was surplus (or not in `t` at all) → `missing` unchanged.

So `need[ch] < 0` means "the window holds more `ch` than `t` requires" — the surplus. When the window is
valid (`missing == 0`), we can drop characters from the left **as long as they are surplus**, i.e. while
`need[s[left]] < 0`.

```python-run
def min_window(s, t):
    need = {}
    for ch in t:
        need[ch] = need.get(ch, 0) + 1
    missing = len(t)
    left = 0
    best = (float("inf"), 0)                # (length, start)
    for right, ch in enumerate(s):
        if need.get(ch, 0) > 0:
            missing -= 1
        need[ch] = need.get(ch, 0) - 1
        if missing == 0:                    # valid: shrink as far as possible
            while need[s[left]] < 0:
                need[s[left]] += 1
                left += 1
            best = min(best, (right - left + 1, left))
            need[s[left]] += 1              # give up one required char on purpose
            missing += 1
            left += 1
    length, start = best
    return "" if length == float("inf") else s[start:start + length]

for s, t in [("ADOBECODEBANC", "ABC"), ("a", "a"), ("a", "aa"), ("bba", "ab")]:
    print(s, t, "->", repr(min_window(s, t)))
```

### 3.1 Dry run

`s = "ADOBECODEBANC"`, `t = "ABC"`. Start: `need = {A:1, B:1, C:1}`, `missing = 3`.

| right | ch | missing after | action |
|---|---|---|---|
| 0 | A | 2 | A was needed |
| 1–2 | D, O | 2 | not in `t` → need goes negative (surplus) |
| 3 | B | 1 | B was needed |
| 4 | E | 1 | |
| 5 | C | **0** | valid. `s[0] = A` is not surplus, so no shrink → record `ADOBEC` (len 6). Release A: `missing = 1`, `left = 1` |
| 6–9 | O, D, E, B | 1 | the second B makes `need[B] = −1` (surplus) |
| 10 | A | **0** | valid. Shrink past D, O, B, E (indices 1–4, all surplus) → `left = 5`, record `CODEBA` (6, not better). Release C: `left = 6` |
| 11 | N | 1 | |
| 12 | C | **0** | valid. Shrink past O, D, E (6–8) → `left = 9`, record `BANC` (len **4**) ✓ |

Run the code above with a `print` inside the `if missing == 0` block to watch the pointers yourself.

### 3.2 Why "release one required char on purpose"?

After recording the shortest window for this `right`, the window is valid but cannot be shortened further
without becoming invalid. Any shorter answer must therefore **end later**. Removing the leftmost required
character makes the window invalid and lets the outer loop look for the next point where it becomes valid
again. Some solutions keep the window valid and instead shrink at the top of the next iteration — both are
fine; this version keeps the invariant "after processing `right`, `missing > 0`" which makes reasoning easy.

### 3.3 Complexity

Every index enters the window once (`right`) and leaves once (`left`), and each move is O(1) dict work:
**O(|s| + |t|)** time, O(Σ) extra space. Slicing the answer once at the end avoids O(n) copies per update.

## 4. Counting distinct values: "at most K"

*Fruit Into Baskets* is "longest subarray with at most 2 distinct values". State: a dict value → count;
condition: `len(count) <= 2`. It is the *longest* template — shrink while invalid:

```python-run
def total_fruit(fruits, K=2):
    count = {}
    left = best = 0
    for right, f in enumerate(fruits):
        count[f] = count.get(f, 0) + 1
        while len(count) > K:
            g = fruits[left]
            count[g] -= 1
            if count[g] == 0:
                del count[g]                 # keep len(count) == number of distinct values
            left += 1
        best = max(best, right - left + 1)
    return best

print(total_fruit([1, 2, 1]), total_fruit([0, 1, 2, 2]), total_fruit([3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4]))
```

### 4.1 "Exactly K" via "at most K"

A beautiful trick for **counting** subarrays (not finding the longest): the number of subarrays with
*exactly* K distinct values equals `atMost(K) - atMost(K - 1)`. Counting "at most K" subarrays is easy with
a window: for each `right`, every start in `[left, right]` is valid, which contributes `right - left + 1`
subarrays.

```python-run
def at_most(nums, K):
    count, left, total = {}, 0, 0
    for right, x in enumerate(nums):
        count[x] = count.get(x, 0) + 1
        while len(count) > K:
            count[nums[left]] -= 1
            if count[nums[left]] == 0:
                del count[nums[left]]
            left += 1
        total += right - left + 1           # all subarrays ending at right with start >= left
    return total

def exactly(nums, K):
    return at_most(nums, K) - at_most(nums, K - 1)

print(exactly([1, 2, 1, 2, 3], 2))   # 7  (LeetCode 992 example)
```

Why not count "exactly K" directly? Because "exactly K distinct" is **not monotone** in the window size —
adding an element can turn a valid window invalid *or* an invalid one valid — so a single window cannot
track it. "At most K" is monotone. Converting a non-monotone condition into a difference of monotone ones
is a recurring idea.

## 5. The majority-letter window

*Longest Repeating Character Replacement*: longest window that becomes a single repeated letter after at
most `k` replacements. With counts `count[26]` and `maxf` = the largest count in the window:

$$\text{replacements needed} = (\text{right} - \text{left} + 1) - \text{maxf}.$$

```python-run
def character_replacement(s, k):
    count = [0] * 26
    left = maxf = 0
    best = 0
    for right, ch in enumerate(s):
        count[ord(ch) - 65] += 1
        maxf = max(maxf, count[ord(ch) - 65])
        while (right - left + 1) - maxf > k:
            count[ord(s[left]) - 65] -= 1
            left += 1
            # maxf is NOT recomputed — see below
        best = max(best, right - left + 1)
    return best

print(character_replacement("ABAB", 2), character_replacement("AABABBA", 1))
```

**Why may `maxf` be stale?** After shrinking, the true maximum count may be smaller than `maxf`. Then
`len - maxf` *underestimates* the replacements needed, and we may accept a window that is actually invalid.
But any window we accept has length at most `maxf + k`, and `maxf` is a count that some letter
*really reached* inside an earlier window — so a valid window of length `maxf + k` (or the whole string, if
shorter) really existed at that moment. In other words, the reported `best` only grows when `maxf` grows, and
every value it takes is genuinely achievable. So the final answer is still correct. If this argument
feels slippery in an interview, recompute `maxf = max(count)` — 26 operations per step, still O(n).

## 6. A catalogue of window states

| Question about the window | State | O(1) validity test |
|---|---|---|
| Same letters as `p`? | `win[26]`, `need[26]` | `matches == 26` |
| Contains all of `t` (multiset)? | `need` dict (decremented) | `missing == 0` |
| At most K distinct? | dict with deletes | `len(d) <= K` |
| No repeated character? | set or `last` index | membership check on entry |
| Uniform after k edits? | `count[26]`, `maxf` | `len - maxf <= k` |
| Sum ≥ target (positives)? | running sum | `total >= target` |

## 7. Pitfalls

1. **Set vs multiset.** Sets forget multiplicity: `"aab"` and `"abb"` have the same set. Use counts.
2. **Stale zero keys** in dicts when `len()` matters.
3. **The last window** in fixed-size loops that check before sliding.
4. **Tie-breaking.** If the problem wants the leftmost shortest window, update only on a strictly smaller
   length (`<`).
5. **Case sensitivity.** `'A'` and `'a'` are different keys; a 26-slot array silently breaks on mixed case —
   use 52/128 slots or a dict.
6. **Building strings repeatedly.** Store `(start, length)`; slice once.

## 8. Summary

- A frequency table is the state for most string windows; update it in O(1) per pointer move.
- Avoid O(Σ) rescans with an aggregate: `matches` (fixed windows) or `missing` (variable windows).
- Use the *shortest* template for "contains everything" and the *longest* template for "at most K".
- Non-monotone conditions ("exactly K") can often be written as a difference of monotone ones.

## Glossary

- **Frequency table / frequency map** — for each distinct item, how many times it occurs.
- **`Counter`** — Python's ready-made frequency table (`collections.Counter`); missing keys count as 0.
- **Anagram / permutation (of a string)** — the same characters in a different order.
- **Multiplicity** — the number of copies of an item.
- **Multiset** — a collection where copies matter (unlike a set, which ignores repeats).
- **Alphabet (Σ)** — the set of characters that can occur.
- **`need`** — the table of counts still required by the target string.
- **`missing`** — one integer: how many required characters the window still lacks.
- **`matches`** — one integer: how many alphabet slots have equal counts in the window and the target.
- **Surplus** — copies of a character beyond what is required.
- **At most K / exactly K** — two counting conditions; the first works with a window directly, the second is obtained by subtraction.

```quiz
[
  {"q": "In Minimum Window Substring with a single `need` dict that is decremented as characters enter, what does `need[c] < 0` mean?",
   "options": ["c is not in t", "The window lacks c", "The window holds more c than t requires", "The window is invalid"], "answer": 2,
   "explain": "need starts at the count in t; each occurrence in the window decrements it. Below zero means surplus copies that can be dropped."},
  {"q": "When is `missing` decremented in the need/missing technique?",
   "options": ["Every time a character enters", "Only when the entering character had need[c] > 0 before decrementing", "When a character leaves", "When need[c] becomes negative"], "answer": 1,
   "explain": "Only characters that were still required reduce the number of missing characters; surplus ones do not."},
  {"q": "Why does comparing `set(window) == set(p)` fail for anagram detection?",
   "options": ["Sets are slow", "Sets ignore multiplicity", "Sets are unordered", "Sets cannot hold characters"], "answer": 1,
   "explain": "'aab' and 'abb' have the same set {a, b} but different counts."},
  {"q": "Number of subarrays with exactly K distinct values equals:",
   "options": ["atMost(K) + atMost(K-1)", "atMost(K) - atMost(K-1)", "atMost(K+1) - atMost(K)", "atMost(K) * K"], "answer": 1,
   "explain": "Subarrays with at most K distinct values, minus those with at most K-1, leaves exactly K."},
  {"q": "In the `matches` technique for Permutation in String, after `win[c] += 1` the count now equals `need[c] + 1`. What happens to `matches`?",
   "options": ["+1", "-1", "unchanged", "reset to 0"], "answer": 1,
   "explain": "Slot c was equal just before the increment and is now unequal, so one fewer slot matches."},
  {"q": "Using a Counter for Fruit Into Baskets, what bug appears if you never delete keys whose count reached 0?",
   "options": ["Nothing — Counter handles it", "len(count) overstates the number of distinct fruits, so the window shrinks too much", "KeyError", "The answer is always 2"], "answer": 1,
   "explain": "Zero-count keys still count toward len(), so the 'at most two types' check fires too early."},
  {"q": "What is the time complexity of Minimum Window Substring with the missing counter?",
   "options": ["O(|s| * |t|)", "O(|s|^2)", "O(|s| + |t|)", "O(|s| log |s|)"], "answer": 2,
   "explain": "Building need is O(|t|); each index of s enters and leaves the window once with O(1) work."}
]
```

> **Source:** Original exposition; dictionary/Counter behaviour per the Python `collections` documentation and
> Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 10 (maps and hash tables).
> Problem ordering follows the NeetCode 150 roadmap.
