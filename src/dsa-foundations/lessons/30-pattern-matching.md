# Pattern matching: brute force, Boyer-Moore, KMP

> **Before this lesson:** You should be comfortable with Python strings, indexing and slicing,
> and with big-O analysis of loops
> ([Analysing real code and proving it correct](#/lesson/dsa-foundations/analysis-examples)). The
> "a quantity that only moves forward" argument from that lesson is used again here. No earlier
> text-processing lesson is assumed; this is the first one.

## In plain words

**Pattern matching** is the problem behind the Find box in every editor and browser: given a
long piece of text and a shorter piece to look for, report where the shorter piece occurs, if
it does.

Imagine checking whether a phrase appears on a printed page by sliding a strip of card with
the phrase written on it along each line. The plain method slides the strip one letter at a
time and compares letter by letter at every position. It works, but it wastes effort: after
comparing five letters and failing on the sixth, it forgets what it saw, moves one place, and
compares many of the same letters again. The two famous algorithms in this lesson both remember
what they have seen. One uses it to jump the strip forward several places at once; the other
uses it to guarantee that it never looks at a letter of the page twice.

Why it matters for a job: searching text is among the most common things software does (find
in files, log analysis, spam filters, matching DNA sequences). In interviews, "implement
`strStr`" (find a substring) is a standard question, and the algorithm called KMP, with its
"failure function", is the classic answer once the plain method has been given.

## 1. Notation

The long string is the **text** $T$, with $n$ characters. The short string is the **pattern**
$P$, with $m$ characters. A few more terms:

- The set of characters that may appear is the **alphabet**, written with the Greek letter
  $\Sigma$ (sigma). It might be the 26 letters, all of Unicode, or the four letters
  $\{A, C, G, T\}$ of DNA. Its size is written $|\Sigma|$ and is treated as a fixed number.
- A **substring** is a run of consecutive characters. $T[i:j]$ is the substring from index $i$
  up to but not including $j$, as in Python slicing.
- A **prefix** of $P$ is a substring that starts at its beginning, $P[0:k]$; a **suffix** is
  one that ends at its end, $P[j:m]$. For `abc` the prefixes are the empty string, `a`, `ab`
  and `abc`.
- A *match* is an index $j$ such that $T[j:j+m] = P$. The functions below return the lowest
  such $j$, or $-1$ if there is none, the same convention as Python's `T.find(P)`.

## 2. Brute force

A **brute-force** algorithm tries every possibility and checks each one. Here the
possibilities are the positions at which the pattern could start, called **alignments**:
$i = 0, 1, \ldots, n - m$. For each one, compare the pattern with the text character by
character.

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

**Reading this code.** The outer loop tries each starting index `i`. The inner `while` loop
advances `k` along the pattern for as long as the characters agree. If `k` reaches `m`, every
character matched and `i` is returned. Otherwise the loop moves on to the next `i`. The first
call prints 10: the pattern `abacab` begins at index 10 of the text. The second function counts
character comparisons on a deliberately nasty input, a text of 2,000 `a`s followed by a `b`,
searched for 50 `a`s followed by a `b`; it reports 99,501 comparisons.

**Running time.** There are $n - m + 1$ alignments and each may compare up to $m$ characters:
**$O(nm)$** in the worst case. The worst case arises for inputs like the one above, where
almost the entire pattern matches at every alignment before the last character fails. On
ordinary English text a mismatch usually turns up within the first character or two, and brute
force runs in nearly linear time, which is why it is still perfectly usable for short searches.

**Where the waste is.** After a mismatch, brute force **forgets everything it learned** from
the characters it compared, shifts the pattern by one, and starts again. The two classic
algorithms differ in how they put that knowledge to use.

## 3. The Boyer-Moore algorithm

Boyer-Moore can often **skip** stretches of the text without looking at them at all. It rests
on two ideas (called heuristics because they usually help but are not guaranteed to):

- **Compare backwards.** When testing an alignment, compare the pattern with the text from the
  **last** character of $P$ back to the first.
- **Jump on a mismatch.** Suppose the text character $c = T[i]$ fails to match $P[k]$. Then:
  - if $c$ does **not occur anywhere in $P$**, no alignment that covers $T[i]$ can possibly
    match, so move the whole pattern past $T[i]$;
  - otherwise, move $P$ forward until the **last occurrence** of $c$ in $P$ sits under $T[i]$.

Why compare backwards? Because a mismatch at the *end* of the pattern, found after a single
comparison, can justify a jump of up to $m$ places. Searching for `needle` in a page, if the
sixth letter of the current alignment is `x`, which is not in `needle` at all, the pattern can
jump six places having looked at one letter.

To do this quickly, precompute the **last-occurrence function**: `last(c)` is the index of the
rightmost copy of the character $c$ in $P$, or $-1$ if $P$ does not contain $c$. For
$P = $ `abacab`:

| c | a | b | c | d |
|---|---|---|---|---|
| last(c) | 4 | 5 | 3 | -1 |

**The shift rule.** Let $i$ be the text index of the mismatch, $k$ the pattern index, and
$j = \text{last}(T[i])$.

- **Case 1, $j < k$** (the last occurrence is to the left of the mismatch position): shift the
  pattern so that $P[j]$ aligns with $T[i]$. In terms of indices: $i \mathrel{+}= m - (j + 1)$, and the comparison restarts at the end of the pattern.
- **Case 2, $j > k$** (the last occurrence is to the right of the mismatch, so lining it up
  would move the pattern *backwards*): move the pattern forward by one place instead:
  $i \mathrel{+}= m - k$.

Both cases are covered by the single update $i \mathrel{+}= m - \min(k, j + 1)$, after which
$k$ is reset to $m - 1$, the end of the pattern. (The notation $i \mathrel{+}= x$ means
"increase $i$ by $x$", as in Python.)

In the code, the dictionary `last` is built by one pass over the pattern; a later occurrence
of a character overwrites an earlier one, leaving the rightmost. `last.get(T[i], -1)` returns
$-1$ for characters that are not in the pattern.

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

In the first run ($T = $ `abacaabadcabacabaabb`, $P = $ `abacab`) the match at index 10 is
found with only 13 character comparisons. In the second, a 6-character pattern is found at the
end of a text of nearly 900 characters using a number of comparisons that is a small fraction
of $n$: most characters of the text are **never looked at**.

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

- Building `last` takes $O(m + |\Sigma|)$ with an array indexed by character, or $O(m)$ with a
  dictionary.
- **Worst case:** $O(nm + |\Sigma|)$, for instance with a text of all `a`s and a pattern that
  is a `b` followed by `a`s. This simplified version, which uses only the character jump, is no
  better than brute force in the worst case.
- **In practice:** excellent on natural-language text with a reasonably large alphabet. The
  longer the pattern, the longer the jumps: often only about $n/m$ comparisons, which is
  **sublinear**, fewer steps than there are characters in the text.

The full Boyer-Moore algorithm adds a second rule, which looks at the part of the pattern that
*did* match and shifts so that it lines up with another copy of itself (an idea in the spirit
of KMP, below). With refinements it achieves $O(n + m + |\Sigma|)$. The Unix search tool `grep`
and many editors use variants of Boyer-Moore.

## 4. The Knuth-Morris-Pratt algorithm

Brute force and simplified Boyer-Moore both have poor worst cases because they may examine the
same text character many times. The **Knuth-Morris-Pratt** algorithm, **KMP** for short and
named after its three inventors, never moves backwards in the text. Its insight is this: when
a mismatch occurs after $k$ characters of the pattern have matched, we already *know* what the
last $k$ characters of the text were. They were $P[0:k]$, the first $k$ characters of the
pattern. So the best way to continue depends only on the pattern, and can be worked out in
advance, before the text is ever seen.

### 4.1 The failure function

That advance knowledge is stored in the **failure function**. $f(k)$ is the length of the
**longest proper prefix of $P[0:k+1]$ that is also a suffix of $P[0:k+1]$**. ("Proper" means
"not the whole string".) In words: take the first $k + 1$ characters of the pattern, and ask
how long a piece at its start is repeated exactly at its end. For $P = $ `abracadabra`:

| k | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P[k] | a | b | r | a | c | a | d | a | b | r | a |
| f(k) | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 2 | 3 | 4 |

E.g. $f(10) = 4$: the whole word both starts and ends with `abra`; and $f(7) = 1$, because
`abracada` starts and ends with `a` but with nothing longer.

**How it is used.** Suppose $k$ characters have matched, $P[0:k]$, and then $P[k]$ disagrees
with the current text character. The pattern must slide forward. How far? Far enough that the
start of the pattern lines up again with the end of what was matched, and the longest overlap
of that kind has length $f(k-1)$. So set $k$ to $f(k - 1)$ and compare the *same* text
character again. The pattern has slid forward by $k - f(k-1)$ places, no possible match has
been skipped, and the characters known to agree are not compared again. If $k = 0$ there is
nothing matched to reuse, so move on to the next text character.

For instance, with `abracadabra`, suppose the first 10 characters `abracadabr` have matched
and the 11th fails. $f(9) = 3$: the matched part ends with `abr`, which is also how the
pattern begins. So the pattern slides forward 7 places and matching resumes at its 4th
character.

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

The failure function is computed by running the same matching idea on the pattern **against
itself**. The index $j$ scans along the pattern, and $k$ is the length of the overlap found so
far between the start of the pattern and the part ending immediately before $j$. If $P[j] = P[k]$, the
overlap grows: $f(j) = k + 1$. If they differ and $k > 0$, fall back to the next-longest
overlap, $k = f(k - 1)$, and try again. If they differ and $k = 0$, then $f(j) = 0$. This is
`compute_kmp_fail` in the code above.

### 4.4 Performance

The matching loop can go round without advancing in the text (when it falls back), so it is
not obvious that it is linear. The proof finds a second quantity that only increases. Let
$s = j - k$; it is the position in the text where the pattern currently starts, the "shift".
Each pass of the loop does one of three things:

- a match: $j$ increases by 1 and $s$ is unchanged;
- a mismatch with $k > 0$: $j$ is unchanged and $s$ increases by at least 1, because $k$
  decreases ($f(k-1) < k$);
- a mismatch with $k = 0$: both $j$ and $s$ increase by 1.

So every pass increases $j$ or $s$ (or both), neither ever decreases, and both are at most $n$.
There can be at most $2n$ passes. The same argument bounds the computation of the failure
function by $2m$.

> **Theorem.** KMP finds a pattern of length $m$ in a text of length $n$ in **$O(n + m)$** time
> in the worst case.

No algorithm can do better in the worst case, since reading the input alone takes that long.

The function below is a compact variant that reports **every** match, including overlapping
ones. After a complete match it does not start again from scratch; it continues with
`k = fail[k - 1]`, as if a mismatch had occurred. For `aaaaa` and `aa` it reports
`[0, 1, 2, 3]`.

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

Two other approaches are worth knowing by name. **Rabin-Karp** compares hash values of the
pattern and of each window of the text, updating the window's hash in constant time as it
slides; it runs in expected $O(n + m)$ and is well suited to searching for many patterns at
once. And when the *text* is fixed and many different patterns will be searched for, the text
itself can be preprocessed into a tree of its suffixes; see the tries lesson.

> [!INTERVIEW]
> The usual request is to implement `strStr`, substring search. Start with the $O(nm)$ brute
> force, then offer KMP, and explain the failure function as "the longest proper prefix that
> is also a suffix". Common follow-up questions build on the failure function: the shortest
> repeating unit of a string (its length is $m - f(m-1)$, provided that divides $m$), and
> whether a string consists of one block repeated several times.

## 6. Pitfalls

- **Falling back with the wrong index in KMP.** On a mismatch use `fail[k - 1]`, not `fail[k]`.
  And handle `k == 0` separately by advancing in the text, or the loop never ends.
- **Counting the whole string as a "proper" prefix.** The failure value satisfies $f(k) \le k$
  always.
- **Shifting backwards in Boyer-Moore.** When the last occurrence is to the right of the
  mismatch, lining it up would move the pattern backwards; the `min(k, j + 1)` in the update
  prevents this.
- **The empty pattern.** By convention it is found at index 0.
- **Missing overlapping matches.** After a complete match continue with `k = fail[m - 1]`, not
  with `k = 0`.

## 7. Summary

- Brute force tries every alignment: $O(nm)$ in the worst case, near-linear on ordinary text.
- Boyer-Moore compares from right to left and jumps using the last-occurrence table, so it can
  skip parts of the text; the simplified version is still $O(nm)$ in the worst case.
- KMP precomputes the failure function, the longest proper prefix that is also a suffix, and
  never re-reads a text character: $O(n + m)$ in the worst case.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 13.1–13.2.

## Glossary

- **Pattern matching**: finding where a pattern string occurs inside a text string.
- **Text / pattern**: the long string searched in / the short string searched for.
- **Alphabet ($\Sigma$)**: the set of characters that may occur.
- **Substring**: a run of consecutive characters of a string.
- **Prefix / suffix**: a substring at the start / at the end of a string.
- **Proper prefix**: a prefix that is not the whole string.
- **Alignment**: a position of the pattern relative to the text.
- **Brute force**: trying every possibility in turn.
- **Last-occurrence function**: for each character, the index of its rightmost occurrence in
  the pattern.
- **Boyer-Moore**: matching right to left and jumping forward on a mismatch.
- **Sublinear**: taking fewer steps than the length of the input.
- **Failure function**: for each position of the pattern, the length of the longest proper
  prefix that is also a suffix of the pattern up to there.
- **KMP (Knuth-Morris-Pratt)**: linear-time matching that never moves backwards in the text.
- **Rabin-Karp**: matching by comparing hash values of sliding windows.

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
