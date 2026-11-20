# Knapsack: 0/1 and unbounded, derived from scratch

> **Before this lesson:** read [The DP framework](#/lesson/neet-dp/dp-framework) and
> [Linear DP: stairs, robbers and decoders](#/lesson/neet-dp/dp-linear) — especially the "take or skip" idea from
> House Robber.

## In plain words

A **knapsack problem** is any problem where you pick things under a limit. The name comes from
packing a rucksack (a knapsack): each item has a weight and a value, the bag can only carry so much,
and you want the most valuable load.

Many problems are the same thing in disguise. Paying an amount with coins: the "bag" is the amount
and the "items" are coins. Splitting a list into two equal halves: the "bag" is half the total.
Recognising the disguise is the skill.

Two versions matter:

- **0/1 knapsack** — each item is used **zero or one** time (that is what "0/1" means).
- **Unbounded knapsack** — each kind of item can be used **as many times as you like** (like coins).

The stored answers form a table with one row per item and one column per possible limit
(0, 1, 2, … up to the bag's capacity). That is why limits must be reasonably small whole numbers.

Why it matters for a job: Coin Change and Partition Equal Subset Sum are among the most frequently
asked interview questions, and budget-limited selection appears in real work — choosing features for
a release under a time budget, or packing files onto disks.

Words used below:

- **Capacity** — the limit (maximum weight, or the amount to pay).
- **Fractional** — allowed to take part of an item. Our items are never fractional.
- **Feasibility** — a yes/no question: "is it possible at all?"

"Knapsack" is less a single problem than a **family** that shows up whenever you choose items subject
to a budget: coins that must sum to an amount, numbers that must hit a target, jobs that must fit in a
time limit. NeetCode's Coin Change, Partition Equal Subset Sum, Coin Change II and Target Sum are all
knapsacks in disguise. This lesson derives the two core variants slowly — including *why* the inner
loop direction matters — so you can adapt them confidently.

## The classic 0/1 knapsack

You have `n` items; item `i` has weight `w_i` and value `v_i`. The bag holds total weight at most
`C`. Each item is taken **at most once**. Maximise total value.

### Why greedy fails

Sorting by value per unit weight is optimal for the *fractional* knapsack (where you can take half an
item), but not here. Items `(w, v)` = `(10, 60)`, `(20, 100)`, `(30, 120)` with `C = 50`: greedy by
ratio takes 60 then 100 (weight 30), can't fit the 30-weight item, total 160. The optimum skips the
best-ratio item: 100 + 120 = **220**.

### The state

A brute-force search decides items one by one: "take item `i` or not?" The arguments it needs are the
**index of the next item** and the **remaining capacity**. That's the state:

> `best(i, c)` = maximum value achievable using only the first `i` items with capacity `c`.

### The recurrence

Decide about item `i` (1-based for prefix length):

- skip it → `best(i-1, c)`
- take it (only if `w_i ≤ c`) → `v_i + best(i-1, c - w_i)`

$$best(i, c) = \max\big(best(i-1, c),\; v_i + best(i-1, c - w_i)\big)$$

Base: `best(0, c) = 0`. Answer: `best(n, C)`. States: $(n+1)(C+1)$; work per state O(1). Total
**O(nC)**.

### The table

Items `(1,1) (3,4) (4,5) (5,7)`, capacity 7:

| items \ c | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| none | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| + (1,1) | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| + (3,4) | 0 | 1 | 1 | 4 | 5 | 5 | 5 | 5 |
| + (4,5) | 0 | 1 | 1 | 4 | 5 | 6 | 6 | 9 |
| + (5,7) | 0 | 1 | 1 | 4 | 5 | 7 | 8 | **9** |

Cell `(+(4,5), 7)`: skip gives 5; take gives `5 + best(row above, 3) = 5 + 4 = 9`.

How to read the code that follows: `best` is a list of lists — `best[i][c]` is the cell in row `i`,
column `c`. The outer loop goes through the items one at a time (row by row); the inner loop goes
through every capacity `c` from 0 to `C`. Inside, `best[i][c] = best[i - 1][c]` copies the "skip"
answer from the row above, and the `if w <= c` block replaces it with the "take" answer when the item
fits and gives more value.

```python-run
def knapsack_2d(weights, values, C):
    n = len(weights)
    best = [[0] * (C + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(C + 1):
            best[i][c] = best[i - 1][c]
            if w <= c:
                best[i][c] = max(best[i][c], v + best[i - 1][c - w])
    return best

t = knapsack_2d([1, 3, 4, 5], [1, 4, 5, 7], 7)
for row in t:
    print(row)
```

### Squeezing to one row — and why the loop runs backwards

Row `i` reads only row `i-1`, at columns `c` and `c - w` (to the **left**). If we keep a single array
and overwrite it in place, we need `best[c - w]` to still hold the *old* (row `i-1`) value when we
compute `best[c]`. Iterating `c` from **high to low** guarantees that: the cells to the left haven't
been overwritten yet in this pass.

```python-run
def knapsack_01(weights, values, C):
    best = [0] * (C + 1)
    for w, v in zip(weights, values):
        for c in range(C, w - 1, -1):          # downward!
            best[c] = max(best[c], best[c - w] + v)
    return best[C]

print(knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7))
print(knapsack_01([10, 20, 30], [60, 100, 120], 50))
```

If you iterate upward instead, `best[c - w]` may already include the current item, so the item can be
added again — that's a *different* problem.

## The unbounded knapsack

Now each item can be taken any number of times. The take option no longer moves to the previous item:
after taking item `i`, you can take it **again**.

$$best(i, c) = \max\big(best(i-1, c),\; v_i + best(i, c - w_i)\big)$$

Note the second term reads row `i` (the current row), not `i-1`. In one array, that means iterating
`c` **upward**, so `best[c - w]` already reflects the current item.

```python-run
def knapsack_unbounded(weights, values, C):
    best = [0] * (C + 1)
    for w, v in zip(weights, values):
        for c in range(w, C + 1):              # upward!
            best[c] = max(best[c], best[c - w] + v)
    return best[C]

print(knapsack_unbounded([1, 3, 4, 5], [1, 4, 5, 7], 7))   # can reuse items now
```

| Variant | Recurrence's "take" reads | 1-D loop over capacity |
|---|---|---|
| 0/1 | previous row `best(i-1, c-w)` | **downward** |
| Unbounded | current row `best(i, c-w)` | **upward** |

> [!TIP]
> Memorise the *reason*, not the direction: "Do I want `best[c - w]` to include this item already?"
> No → go down. Yes → go up.

## Changing the objective

The knapsack skeleton stays fixed while the combine operator and base case change:

| Question | Base `dp[0]` | Others initially | Combine | Example |
|---|---|---|---|---|
| Max value | 0 | 0 | `max(dp[c], dp[c-w] + v)` | 0/1 Knapsack |
| Min number of items to hit exactly `c` | 0 | ∞ | `min(dp[c], dp[c-w] + 1)` | Coin Change |
| Is `c` reachable exactly? | True | False | `dp[c] or dp[c-w]` | Partition Equal Subset Sum |
| Number of ways to hit `c` | 1 | 0 | `dp[c] + dp[c-w]` | Coin Change II, Target Sum |

"Exactly `c`" vs "at most `c`" is controlled by the initial values: initialising every cell to 0 for
max-value means "at most `c`"; initialising non-zero cells to −∞/∞/False/0 means "exactly `c`".

### Coin Change (unbounded, min count)

Coins are reusable → upward. Because the count doesn't depend on which order coins are added, we can
also loop amounts outside and coins inside:

```python-run
def coin_change(coins, amount):
    INF = amount + 1
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                dp[a] = min(dp[a], dp[a - c] + 1)
    return dp[amount] if dp[amount] < INF else -1

print(coin_change([1, 2, 5], 11), coin_change([2], 3), coin_change([1, 3, 4], 6))
```

Table for `coins = [1, 3, 4]`:

| a | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| dp | 0 | 1 | 2 | 1 | 1 | 2 | **2** |

Greedy would pick 4 + 1 + 1 = 3 coins for amount 6; the DP finds 3 + 3.

### Partition Equal Subset Sum (0/1, feasibility)

Split `nums` into two equal-sum halves ⇔ some subset sums to `total / 2`. Each number is used once →
downward.

```python-run
def can_partition(nums):
    total = sum(nums)
    if total % 2:
        return False
    T = total // 2
    reach = [True] + [False] * T
    for x in nums:
        for s in range(T, x - 1, -1):
            reach[s] = reach[s] or reach[s - x]
    return reach[T]

print(can_partition([1, 5, 11, 5]), can_partition([1, 2, 3, 5]))
```

A neat Python trick: represent the reachable set as bits of one big integer. `bits |= bits << x` is
the whole downward loop in a single operation (the shift reads the *old* bits).

```python-run
def can_partition_bits(nums):
    total = sum(nums)
    if total % 2:
        return False
    bits = 1
    for x in nums:
        bits |= bits << x
    return bool(bits >> (total // 2) & 1)

print(can_partition_bits([1, 5, 11, 5]), can_partition_bits([1, 2, 3, 5]))
```

### Counting: the loop-order trap

For **counting** with an unbounded supply, the loop order changes the meaning:

- coins **outer**, amounts inner → each multiset counted once (**combinations**, Coin Change II);
- amounts **outer**, coins inner → each ordered sequence counted (**permutations**, Combination
  Sum IV).

```python-run
def combos(amount, coins):
    ways = [1] + [0] * amount
    for c in coins:
        for a in range(c, amount + 1):
            ways[a] += ways[a - c]
    return ways[amount]

def perms(amount, coins):
    ways = [1] + [0] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                ways[a] += ways[a - c]
    return ways[amount]

print("combinations:", combos(5, [1, 2, 5]), " permutations:", perms(5, [1, 2, 5]))
```

With coins outer, by the time we process coin `c` the table only contains combinations of earlier
coins, so every multiset is built in one canonical order. Min/max problems don't care (a sequence and
its reordering have the same count/value), which is why Coin Change works either way.

## Reconstructing chosen items

Keep the 2-D table and walk back from `(n, C)`: if `best[i][c] != best[i-1][c]`, item `i` was taken
and capacity drops by `w_i`.

```python-run
def knapsack_items(weights, values, C):
    n = len(weights)
    best = [[0] * (C + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(C + 1):
            best[i][c] = best[i - 1][c]
            if w <= c and best[i - 1][c - w] + v > best[i][c]:
                best[i][c] = best[i - 1][c - w] + v
    chosen, c = [], C
    for i in range(n, 0, -1):
        if best[i][c] != best[i - 1][c]:
            chosen.append(i - 1)
            c -= weights[i - 1]
    return best[n][C], chosen[::-1]

print(knapsack_items([10, 20, 30], [60, 100, 120], 50))
```

## Pseudo-polynomial time

O(nC) looks polynomial, but `C` is a *number*, and its input size is only about $\log_2 C$ bits. With
`C = 10^{18}` the table is impossible. Knapsack is NP-hard in general; the DP is efficient only when
capacities are modest. In interviews, constraints like `amount ≤ 10^4` are your cue that an O(n·amount)
table is intended.

## Pitfalls

- Wrong loop direction (0/1 vs unbounded) — the most common knapsack bug.
- Wrong loop nesting for counting (combinations vs permutations).
- `float('inf')` sentinel never converted back to −1.
- For subset-sum reductions (Target Sum): forgetting parity and range checks on `(total + target)/2`.
- Greedy by ratio or by largest coin.

## Summary

- State: (items considered, capacity). Decision: take or skip.
- 0/1 reads the previous row → 1-D loop **downward**; unbounded reads the current row → **upward**.
- The objective (max, min, feasibility, count) only changes the base values and combine operator.
- Counting combinations: items outer. Counting permutations: amounts outer.

## Glossary

| Term | Meaning in plain words |
|---|---|
| **Knapsack problem** | Choose items under a capacity limit to optimise or count something. |
| **0/1 knapsack** | Each item may be used at most once. |
| **Unbounded knapsack** | Each kind of item may be used any number of times. |
| **Capacity** | The limit: maximum weight, target amount or target sum. |
| **Subset sum** | Does some group of the numbers add up exactly to a target? |
| **Combination** | A selection where order does not matter (1+2 is the same as 2+1). |
| **Permutation** | An arrangement where order matters (1+2 differs from 2+1). |
| **Pseudo-polynomial** | Fast only when the capacity is a small number, because the table has one column per unit of capacity. |
| **Bitset** | A whole number used as a row of yes/no bits. |
| **Sentinel (infinity)** | A stand-in value meaning 'not possible'. |

## Check yourself

```quiz
[
  {"q": "In the 1-D 0/1 knapsack, why must capacity be iterated downward?", "options": ["It's faster", "So best[c-w] still holds the value from before this item was considered", "To handle negative weights", "Python lists require it"], "answer": 1, "explain": "Downward iteration leaves smaller capacities untouched in this pass, so each item contributes at most once."},
  {"q": "Which problem is an unbounded knapsack?", "options": ["Partition Equal Subset Sum", "Coin Change", "Target Sum", "0/1 Knapsack"], "answer": 1, "explain": "Each coin denomination can be used any number of times."},
  {"q": "Looping amounts in the outer loop and coins in the inner loop while counting ways computes…", "options": ["Combinations", "Permutations (ordered sequences)", "The minimum coins", "Nothing meaningful"], "answer": 1, "explain": "For each amount every coin may be last, so 1+2 and 2+1 are counted separately."},
  {"q": "Greedy by value/weight ratio is optimal for which variant?", "options": ["0/1 knapsack", "Unbounded knapsack", "Fractional knapsack", "None"], "answer": 2, "explain": "When items can be split, filling with the best ratio first is optimal; with indivisible items it can fail."},
  {"q": "Why is O(n·C) called pseudo-polynomial?", "options": ["Because it uses recursion", "It's polynomial in the numeric value of C, which is exponential in the number of bits used to write C", "Because n is small", "It's actually exponential in n"], "answer": 1, "explain": "C can be huge while its encoding is short; the table size grows with C's value."},
  {"q": "For 'can a subset sum to T', how should dp be initialised?", "options": ["All True", "dp[0] = True, others False", "dp[T] = True", "All 0"], "answer": 1, "explain": "Only the empty sum is reachable before considering any items."},
  {"q": "With coins [1, 3, 4] and amount 6, what's the minimum number of coins?", "options": ["1", "2", "3", "4"], "answer": 1, "explain": "3 + 3. Greedy's 4 + 1 + 1 uses three coins."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §13.3
> (subproblem optimality); NeetCode 150 roadmap (Coin Change, Partition Equal Subset Sum, Coin Change
> II, Target Sum).
