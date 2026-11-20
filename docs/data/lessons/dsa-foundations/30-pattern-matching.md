# Pattern matching: brute force, Boyer-Moore, KMP

Text is everywhere: documents, web pages, source code, logs, DNA sequences. The most basic question
about text is **pattern matching**: we hold a long text $T$ ($n$ characters) and a shorter pattern $P$ ($m$ characters), and
want to know if — and where — $P$ occurs inside $T$. Every `Ctrl+F`, every `grep`,
every `str.find` solves this problem. This lesson develops three algorithms from the book: brute
force, **Boyer-Moore** and **Knuth-Morris-Pratt (KMP)**.

## 1. Notation

- Characters come from an **alphabet** $\Sigma$ (ASCII, Unicode, $\{A, C, G, T\}$…) of size
  $|\Sigma|$, assumed fixed and finite.
- $T[i:j]$ is the substring from index $i$ up to but not including $j$ (Python slicing).
- A **prefix** of $P$ is $P[0:k]$; a **suffix** is $P[j:m]$. The empty string is both.
- A *match* is an index $j$ with $T[j:j+m] = P$. We return the lowest such $j$ or $-1$ — like
  Python's `T.find(P)`.

## 2. Brute force

The **brute-force** design pattern enumerates all possible configurations and picks the right one.
Here: try every alignment $i = 0, \ldots, n - m$ of the pattern against the text and compare
character by character.

```python-run
def find_brute(T, P):
    """Return the lowest index of T at which substring P begins (or else -1)."""
    n, m = len(T), len(P)
    for i in range(n - m + 1):               # try every potential starting index within T
        k = 0                                # an index into pattern P
        while k < m and T[i + k] == P[k]:    # kth character of P matches
            k += 1
        if k == m:                           # if we reached the end of pattern,
            return i                         # substring T[i:i+m] matches P
    return -1                                # failed to find a match starting with any i

print(find_brute("abacaabaccabacabaabb", "abacab"))

def count_comparisons(T, P):
    c = 0
    for i in range(len(T) - len(P) + 1):
        k = 0
        while k < len(P):
            c += 1
            if T[i + k] != P[k]: break
            k += 1
    return c
print("worst case comparisons:", count_comparisons("a" * 2000 + "b", "a" * 50 + "b"))
```

**Running time:** there are $n - m + 1$ candidate alignments and each may compare up to $m$
characters: **$O(nm)$** worst case. The worst case occurs for inputs like $T = aaa\ldots ab$,
$P = aaab$: almost the whole pattern matches at every alignment before failing. On typical English
text mismatches happen quickly and brute force is close to linear, which is why it is still
perfectly usable for short searches.

The inefficiency: after a mismatch, brute force **throws away everything it learned** from the
characters it just compared, shifts by one, and starts over. The two classic algorithms differ in
how they exploit that information.

## 3. The Boyer-Moore algorithm

Boyer-Moore can often **skip** large portions of the text without examining them at all. It rests
on two heuristics:

- **Looking-glass heuristic:** when testing an alignment, compare the pattern against the text
  **backwards**, from the last character of $P$ to the first.
- **Character-jump heuristic:** when the text character $c = T[i]$ fails to match $P[k]$:
  - if $c$ does **not occur anywhere in $P$**, shift $P$ completely past $T[i]$ — no alignment
    overlapping this character can match;
  - otherwise, shift $P$ until the **last occurrence** of $c$ in $P$ is aligned with $T[i]$.

Define the **last-occurrence function**: `last(c)` gives the position of the rightmost copy of
$c$ inside $P$, and $-1$ when $P$ does not contain $c$. For $P = $ `abacab`:

| c | a | b | c | d |
|---|---|---|---|---|
| last(c) | 4 | 5 | 3 | -1 |

**The shift rule.** Let $i$ be the text index of the mismatch, $k$ the pattern index, and
$j = \text{last}(T[i])$.

- **Case 1, $j < k$** (the last occurrence is to the left of the mismatch position): shift the
  pattern so that $P[j]$ aligns with $T[i]$. In terms of indices: $i \mathrel{+}= m - (j + 1)$, and the comparison restarts at the end of the pattern.
- **Case 2, $j > k$** (the last occurrence is to the right — aligning it would shift the pattern
  *backwards*): just shift the pattern by one: $i \mathrel{+}= m - k$.

Both are captured by $i \mathrel{+}= m - \min(k, j + 1)$, with $k$ reset to $m - 1$.

```python-run
def find_boyer_moore(T, P, trace=False):
    """Return the lowest index of T at which substring P begins (or else -1)."""
    n, m = len(T), len(P)
    if m == 0: return 0
    last = {}                                # build 'last' dictionary
    for k in range(m):
        last[P[k]] = k                       # later occurrence overwrites
    # align end of pattern at index m-1 of text
    i = m - 1                                # an index into T
    k = m - 1                                # an index into P
    comparisons = 0
    while i < n:
        comparisons += 1
        if T[i] == P[k]:                     # a matching character
            if k == 0:
                if trace: print("comparisons:", comparisons)
                return i                     # pattern begins at index i of text
            i -= 1                           # examine previous character
            k -= 1                           # of both T and P
        else:
            j = last.get(T[i], -1)           # last(T[i]) is -1 if not found
            i += m - min(k, j + 1)           # case analysis for jump step
            k = m - 1                        # restart at end of pattern
    if trace: print("comparisons:", comparisons)
    return -1

print(find_boyer_moore("abacaabadcabacabaabb", "abacab", trace=True))
print(find_boyer_moore("the quick brown fox jumps over the lazy dog " * 20 + "needle", "needle", trace=True))
```

In the book's example ($T = $ `abacaabadcabacabaabb`, $P = $ `abacab`) the match at index 10 is
found with only 13 character comparisons; note the second run above, where a 6-character pattern is
found in a text of about 900 characters using only a fraction of $n$ comparisons — many text
characters are **never examined**.

### Dry run (first steps)

```
T: a b a c a a b a d c a b a c a b a a b b
P: a b a c a b                              compare T[5]='a' vs P[5]='b': mismatch; last('a')=4 -> shift 1
P:   a b a c a b                            T[6]='b' ok, T[5]='a' ok, T[4]='a' vs P[3]='c': mismatch;
                                            last('a')=4 > k=3 -> case 2, shift by 1
P:     a b a c a b                          T[7]='a' vs 'b': mismatch; shift 1
P:       a b a c a b                        T[8]='d' vs 'b': 'd' not in P -> jump past it (shift 6)
P:                   a b a c a b            T[14]='a' vs 'b': mismatch, shift 1
P:                     a b a c a b          six matches right to left: found at index 10
```

### Performance

- Building `last`: $O(m + |\Sigma|)$ with an array, or $O(m)$ with a dict.
- **Worst case:** $O(nm + |\Sigma|)$ — e.g. $T = aaa\ldots a$, $P = baa\ldots a$. This simplified
  version (bad-character rule only) is no better than brute force in the worst case.
- **In practice:** excellent on natural-language text with a reasonably large alphabet. The larger
  the pattern, the bigger the jumps: often about $n/m$ comparisons — **sublinear**.

The original Boyer-Moore algorithm adds a second rule, the *good-suffix heuristic* (shift so that the
matched suffix aligns with another occurrence of itself, in the spirit of KMP), and with refinements
achieves $O(n + m + |\Sigma|)$. GNU `grep` and many editors use Boyer-Moore variants (e.g. Horspool).

## 4. The Knuth-Morris-Pratt algorithm

Brute force and simple Boyer-Moore both have bad worst cases because they may re-examine text
characters. **KMP** never moves backwards in the text. When a mismatch occurs after matching
$P[0:k]$, we *know* the last $k$ text characters — they are $P[0:k]$. So we can precompute, from the
pattern alone, the best way to continue.

### 4.1 The failure function

The **failure function** $f(k)$ is the length of the **longest proper prefix of $P[0:k+1]$ that is
also a suffix of $P[0:k+1]$** ("proper" = not the whole string). For $P = $ `abracadabra`:

| k | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P[k] | a | b | r | a | c | a | d | a | b | r | a |
| f(k) | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 2 | 3 | 4 |

E.g. $f(10) = 4$: the whole word both starts and ends with `abra`; and $f(7) = 1$, because
`abracada` starts and ends with `a` but with nothing longer.

**Use:** if we have matched $P[0:k]$ (so $k$ characters) and $P[k]$ mismatches the current text
character, the longest prefix of $P$ that could still be "in progress" has length $f(k-1)$. So set
$k \leftarrow f(k - 1)$ and compare the *same* text character again — sliding the pattern forward by
$k - f(k-1)$ positions without losing any potential match. If $k = 0$, just advance in the text.

```python-run
def compute_kmp_fail(P):
    """Utility that computes and returns KMP 'fail' list."""
    m = len(P)
    fail = [0] * m                    # by default, presume overlap of 0 everywhere
    j = 1
    k = 0
    while j < m:                      # compute f(j) during this pass, if nonzero
        if P[j] == P[k]:              # k + 1 characters match thus far
            fail[j] = k + 1
            j += 1
            k += 1
        elif k > 0:                   # k follows a matching prefix
            k = fail[k - 1]
        else:                         # no match found starting at j
            j += 1
    return fail

def find_kmp(T, P):
    """Return the lowest index of T at which substring P begins (or else -1)."""
    n, m = len(T), len(P)
    if m == 0: return 0
    fail = compute_kmp_fail(P)        # rely on utility to precompute
    j = 0                             # index into text
    k = 0                             # index into pattern
    while j < n:
        if T[j] == P[k]:              # P[0:1+k] matched thus far
            if k == m - 1:            # match is complete
                return j - m + 1
            j += 1                    # try to extend match
            k += 1
        elif k > 0:
            k = fail[k - 1]           # reuse suffix of P[0:k]
        else:
            j += 1
    return -1                         # reached end without match

print(compute_kmp_fail("abracadabra"))
print(compute_kmp_fail("abacab"), find_kmp("abacaabaccabacabaabb", "abacab"))
```

### 4.2 Dry run

$T = $ `abacaabaccabacabaabb`, $P = $ `abacab`, fail = `[0, 0, 1, 0, 1, 2]`.

| text index j | k before | compare | action |
|---|---|---|---|
| 0–4 | 0→5 | `abaca` matches | k = 5 |
| 5 | 5 | T[5]='a' vs P[5]='b' ✗ | k = fail[4] = 1 |
| 5 | 1 | 'a' vs P[1]='b' ✗ | k = fail[0] = 0 |
| 5 | 0 | 'a' vs 'a' ✓ | j = 6, k = 1 |
| 6–8 | 1→4 | `bac` matches | k = 4 |
| 9 | 4 | T[9]='c' vs P[4]='a' ✗ | k = fail[3] = 0 |
| 9 | 0 | 'c' vs 'a' ✗ | j = 10 |
| 10–15 | 0→5 | `abacab` matches | return 15 − 6 + 1 = **10** |

The text index $j$ never decreases.

### 4.3 Computing the failure function

The construction is KMP matching the pattern **against itself**: $j$ scans the pattern, $k$ is the
length of the current prefix-suffix overlap. On a match, $f(j) = k + 1$; on a mismatch with $k > 0$,
fall back to $k = f(k - 1)$ (the next-longest border); otherwise $f(j) = 0$.

### 4.4 Performance

Consider the quantity $s = j - k$ (the shift of the pattern against the text). Each iteration of the
loop either:

- matches: $j$ increases by 1, $s$ unchanged;
- mismatches with $k > 0$: $j$ unchanged, $s$ increases by at least 1 (since $f(k-1) < k$);
- mismatches with $k = 0$: both $j$ and $s$ increase by 1.

So every iteration increases $j$ or $s$ (or both), and both are at most $n$: at most $2n$
iterations. The same argument bounds the failure-function computation by $2m$.

> **Proposition.** KMP locates a length-$m$ pattern inside a length-$n$ text using **$O(n + m)$**
> time in the worst case.

This is worst-case optimal — any algorithm must read the input.

```python-run
def find_all_kmp(T, P):
    """All (possibly overlapping) match positions, in O(n + m)."""
    fail, k, out = [0] * len(P), 0, []
    for j in range(1, len(P)):
        while k > 0 and P[j] != P[k]: k = fail[k - 1]
        if P[j] == P[k]: k += 1
        fail[j] = k
    k = 0
    for j, c in enumerate(T):
        while k > 0 and c != P[k]: k = fail[k - 1]
        if c == P[k]: k += 1
        if k == len(P):
            out.append(j - k + 1)
            k = fail[k - 1]            # keep going: allow overlapping matches
    return out
print(find_all_kmp("aaaaa", "aa"), find_all_kmp("abababab", "abab"))
```

## 5. Comparison

| Algorithm | Preprocessing | Worst case | Typical behaviour |
|---|---|---|---|
| Brute force | none | $O(nm)$ | near-linear on natural text |
| Boyer-Moore (simplified) | $O(m + \lvert\Sigma\rvert)$ | $O(nm + \lvert\Sigma\rvert)$ | sublinear: skips text; best for long patterns, large alphabets |
| KMP | $O(m)$ | $O(n + m)$ | linear; never backs up in the text (good for streams) |

Other important approaches: **Rabin-Karp** (rolling hash; expected $O(n + m)$; great for multiple
patterns and plagiarism detection), and **suffix structures** (tries / suffix arrays) when the
*text* is fixed and many patterns are searched — see the tries lesson.

> [!INTERVIEW]
> You are most often asked to implement `strStr`. Start with the $O(nm)$ brute force, then offer
> KMP and explain the failure function as "longest proper prefix that is also a suffix". Common
> follow-ups built on the failure function: shortest period of a string ($m - f(m-1)$ if it divides
> $m$), longest prefix that is a palindrome, repeated-substring pattern.

## 6. Pitfalls

- KMP: using `fail[k]` instead of `fail[k - 1]` on mismatch; forgetting the `k == 0` case (infinite
  loop).
- Counting the whole string as a "proper" prefix: $f(k) \le k$ always.
- Boyer-Moore: shifting by a negative amount when the last occurrence is to the right of the
  mismatch — the `min(k, j + 1)` guards against it.
- Empty pattern: by convention found at index 0.
- Overlapping matches: after a full match continue with `k = fail[m - 1]`, not `k = 0`.

## 7. Summary

- Brute force: every alignment, $O(nm)$.
- Boyer-Moore: compare right-to-left, jump using the last-occurrence table; can skip text.
- KMP: failure function = longest proper prefix-suffix; never re-reads text; $O(n + m)$.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 13.1–13.2.

## Check yourself

```quiz
[
  {"q": "Worst-case running time of brute-force pattern matching?",
   "options": ["O(n + m)", "O(nm)", "O(n log m)", "O(m^2)"], "answer": 1,
   "explain": "Up to n - m + 1 alignments, each comparing up to m characters, e.g. T = aaaa...ab, P = aaab."},
  {"q": "For P = 'abacab', what is last('a') in Boyer-Moore?",
   "options": ["0", "2", "4", "5"], "answer": 2,
   "explain": "The rightmost 'a' is at index 4."},
  {"q": "In Boyer-Moore, a mismatch occurs on a text character that does not appear in P. The pattern is...",
   "options": ["shifted by one", "shifted entirely past that text character", "reversed", "not shifted"], "answer": 1,
   "explain": "No alignment covering that character can match, so the whole pattern moves beyond it."},
  {"q": "The KMP failure function f(k) is...",
   "options": ["the number of mismatches so far", "the length of the longest proper prefix of P[0:k+1] that is also its suffix", "the last occurrence of P[k]", "k minus the pattern length"], "answer": 1,
   "explain": "It tells how much of the pattern is still matched after a mismatch."},
  {"q": "What is the failure function of 'abacab'?",
   "options": ["[0,0,1,0,1,2]", "[0,1,2,0,1,2]", "[0,0,0,0,1,2]", "[0,0,1,2,1,2]"], "answer": 0,
   "explain": "aba -> 1 (a); abac -> 0; abaca -> 1 (a); abacab -> 2 (ab)."},
  {"q": "Why is KMP O(n + m)?",
   "options": ["Each iteration advances the text index or the pattern shift, and both are bounded by n", "It uses hashing", "It skips characters like Boyer-Moore", "It sorts the text"], "answer": 0,
   "explain": "j and j - k never decrease and at least one increases each iteration: at most 2n iterations."},
  {"q": "Which algorithm can examine fewer than n text characters?",
   "options": ["Brute force", "KMP", "Boyer-Moore", "None"], "answer": 2,
   "explain": "Right-to-left comparison plus character jumps lets it skip parts of the text entirely."}
]
```
