# Using arrays: insertion sort, ciphers and 2-D data

Having seen how arrays work, we now put them to use in four classic case studies from the book:
maintaining a high-score table, sorting with insertion sort, the Caesar cipher, and two-dimensional
data such as game boards.

## 1. Storing high scores

A game keeps the top 10 scores in descending order. Each entry has a name and a score. The book's
`Scoreboard` stores entries in a fixed-capacity list and maintains them sorted.

**Adding an entry** — a new score qualifies if the board is not full or it beats the lowest score.
Starting at the end, shift every entry with a lower score one cell to the right, then drop the new
entry into the gap.

```python-run
class GameEntry:
    def __init__(self, name, score):
        self._name, self._score = name, score
    def get_score(self): return self._score
    def __str__(self): return f"({self._name}, {self._score})"

class Scoreboard:
    def __init__(self, capacity=5):
        self._board = [None] * capacity
        self._n = 0
    def __str__(self):
        return '\n'.join(str(self._board[j]) for j in range(self._n))
    def add(self, entry):
        score = entry.get_score()
        good = self._n < len(self._board) or score > self._board[-1].get_score()
        if good:
            if self._n < len(self._board):
                self._n += 1                       # no score drops off
            j = self._n - 1
            while j > 0 and self._board[j - 1].get_score() < score:
                self._board[j] = self._board[j - 1]   # shift entry right
                j -= 1
            self._board[j] = entry

board = Scoreboard(5)
for name, s in [("Mike", 1105), ("Rob", 750), ("Paul", 720), ("Anna", 660),
                ("Rose", 590), ("Jack", 510), ("Jill", 740), ("Ruffy", 1200)]:
    board.add(GameEntry(name, s))
print(board)
```

Adding costs $O(c)$ for capacity $c$ — the shifting. Note "Jack" never makes the board, and when
"Jill" arrives the lowest entry drops off the end. This shifting step is exactly the inner loop of
insertion sort.

## 2. Insertion sort

**Problem:** rearrange a sequence so its elements are in nondecreasing order.

**Idea:** grow a sorted prefix one element at a time. The first element alone is sorted. Take the
next element (the *current* element) and slide it left past every larger element until it is in
place. Repeat for each element.

```
Algorithm InsertionSort(A):
  for k from 1 to n-1:
    insert A[k] at its proper location within A[0], ..., A[k]
```

```python-run
def insertion_sort(A):
    """Sort list of comparable elements into nondecreasing order, in place."""
    for k in range(1, len(A)):
        cur = A[k]                         # current element to be inserted
        j = k                              # find correct index j for current
        while j > 0 and A[j - 1] > cur:    # element A[j-1] must be after current
            A[j] = A[j - 1]
            j -= 1
        A[j] = cur                         # cur is now in the right place
        print(f"after k={k}: {A}")
    return A

insertion_sort(['B', 'C', 'D', 'A', 'E', 'H', 'G', 'F'])
```

### Dry run

Sorting `[5, 2, 4, 6, 1, 3]`:

| k | cur | sorted prefix after insertion |
|---|---|---|
| 1 | 2 | 2 5 \| 4 6 1 3 |
| 2 | 4 | 2 4 5 \| 6 1 3 |
| 3 | 6 | 2 4 5 6 \| 1 3 |
| 4 | 1 | 1 2 4 5 6 \| 3 |
| 5 | 3 | 1 2 3 4 5 6 |

### Analysis

- **Worst case** (reverse-sorted input): the inner loop runs $k$ times for each $k$, so
  $1 + 2 + \cdots + (n-1) = n(n-1)/2 = \Theta(n^2)$.
- **Best case** (already sorted): the inner loop exits immediately: $\Theta(n)$.
- More precisely the running time is $O(n + I)$ where $I$ is the number of **inversions** — pairs
  $(i, j)$ with $i < j$ but $A[i] > A[j]$ — because each shift fixes exactly one inversion. So
  insertion sort is excellent for *nearly sorted* data.
- It is **in place** ($O(1)$ extra space) and **stable** (equal elements keep their order, since we
  shift only strictly greater elements).

> [!INTERVIEW]
> Why do production sorts (Timsort, introsort) use insertion sort for small runs? For $n$ below
> roughly 16–64, its tiny constant factor and cache-friendly shifting beat $O(n \log n)$ algorithms,
> and it is adaptive to existing order.

### Loop invariant

At the start of iteration $k$, `A[0:k]` holds the original first $k$ elements in sorted order.
Initially true ($k = 1$); each iteration inserts `A[k]` in place, maintaining it; at termination
$k = n$, so the whole list is sorted.

## 3. Simple cryptography: the Caesar cipher

**Encryption** turns *plaintext* into *ciphertext*; **decryption** reverses it. The Caesar cipher,
reportedly used by Julius Caesar, replaces each letter with the letter $r$ positions later in the
alphabet, wrapping from Z back to A. With $r = 3$: A→D, B→E, …, X→A, Y→B, Z→C.

Treat letters as numbers $A = 0, \ldots, Z = 25$. Then

$$\text{encrypt}(x) = (x + r) \bmod 26, \qquad \text{decrypt}(y) = (y - r) \bmod 26.$$

Python's `ord` and `chr` convert between characters and code points: `ord('C') - ord('A')` is 2. The
book builds two 26-character lookup strings (an *encoder* and a *decoder*) and translates using a
**list of characters**, because strings are immutable:

```python-run
class CaesarCipher:
    """Class for doing encryption and decryption using a Caesar cipher."""
    def __init__(self, shift):
        encoder = [None] * 26
        decoder = [None] * 26
        for k in range(26):
            encoder[k] = chr((k + shift) % 26 + ord('A'))
            decoder[k] = chr((k - shift) % 26 + ord('A'))
        self._forward = ''.join(encoder)
        self._backward = ''.join(decoder)

    def encrypt(self, message):
        return self._transform(message, self._forward)

    def decrypt(self, secret):
        return self._transform(secret, self._backward)

    def _transform(self, original, code):
        msg = list(original)                        # mutable copy
        for k in range(len(msg)):
            if msg[k].isupper():
                j = ord(msg[k]) - ord('A')          # index from 0 to 25
                msg[k] = code[j]
        return ''.join(msg)

cipher = CaesarCipher(3)
message = "THE EAGLE IS IN PLAY; MEET AT JOE'S."
coded = cipher.encrypt(message)
print('Secret: ', coded)
print('Message:', cipher.decrypt(coded))
```

Each message of length $n$ is transformed in $O(n)$. Note that Python's `%` returns a non-negative
result for a positive modulus even when the left side is negative — `(-3) % 26 == 23` — which makes
decryption painless.

> [!WARNING]
> The Caesar cipher is trivially breakable: there are only 25 possible shifts, so try them all
> (brute force), or use letter-frequency analysis — "E" is the most common English letter. It is a
> teaching example, not security.

```python-run
# Breaking a Caesar cipher by brute force: print all 26 candidates
secret = "WKLV LV QRW VHFXUH"
for r in range(26):
    print(r, ''.join(chr((ord(c) - 65 - r) % 26 + 65) if c.isupper() else c for c in secret))
```

## 4. Multidimensional data sets

Many data sets are naturally two-dimensional: a game board, an image (rows × columns of pixels), a
spreadsheet, a matrix. Python has no built-in 2-D array, so we use a **list of lists**: a list of
rows, each row a list of cells. `data[i][j]` is row $i$, column $j$.

### 4.1 Constructing a 2-D list correctly

```python
data = ([0] * c) * r          # WRONG: a flat list of r*c zeros
data = [[0] * c] * r          # WRONG: r references to the SAME row
data = [[0] * c for j in range(r)]   # RIGHT: r independent rows
```

The second form is a notorious bug: changing `data[2][0]` changes column 0 of *every* row, because
all rows are the same list object.

```python-run
bad = [[0] * 3] * 2
bad[0][0] = 99
good = [[0] * 3 for _ in range(2)]
good[0][0] = 99
print("bad: ", bad)
print("good:", good)
```

### 4.2 Case study: tic-tac-toe

The book represents the board as a 3×3 list of lists of characters (`'X'`, `'O'` or a space) and
checks for a winner by examining all rows, columns and both diagonals.

```python-run
class TicTacToe:
    def __init__(self):
        self._board = [[' '] * 3 for j in range(3)]
        self._player = 'X'
    def mark(self, i, j):
        if not (0 <= i <= 2 and 0 <= j <= 2): raise ValueError('Invalid board position')
        if self._board[i][j] != ' ': raise ValueError('Board position occupied')
        if self.winner() is not None: raise ValueError('Game is already complete')
        self._board[i][j] = self._player
        self._player = 'O' if self._player == 'X' else 'X'
    def _is_win(self, mark):
        b = self._board
        return (mark == b[0][0] == b[0][1] == b[0][2] or mark == b[1][0] == b[1][1] == b[1][2] or
                mark == b[2][0] == b[2][1] == b[2][2] or mark == b[0][0] == b[1][0] == b[2][0] or
                mark == b[0][1] == b[1][1] == b[2][1] or mark == b[0][2] == b[1][2] == b[2][2] or
                mark == b[0][0] == b[1][1] == b[2][2] or mark == b[0][2] == b[1][1] == b[2][0])
    def winner(self):
        for mark in 'XO':
            if self._is_win(mark):
                return mark
        return None
    def __str__(self):
        rows = ['|'.join(self._board[r]) for r in range(3)]
        return '\n-----\n'.join(rows)

game = TicTacToe()
for i, j in [(1, 1), (0, 2), (2, 2), (0, 0), (0, 1), (2, 1), (1, 2), (1, 0), (2, 0)]:
    game.mark(i, j)
print(game)
print('Winner:', game.winner() or 'tie')
```

### 4.3 Row-major order and cost

For an $r \times c$ grid, visiting every cell is $\Theta(rc)$. In compact array libraries (NumPy, C),
a 2-D array is stored in **row-major order** — row 0, then row 1, … — as one contiguous block, and
`A[i][j]` lives at offset $i \cdot c + j$. Iterating row by row walks memory sequentially (cache
friendly); iterating column by column jumps by $c$ each step. A Python list of lists is not
contiguous, but the same "iterate rows in the outer loop" habit is still the idiomatic choice.

## 5. Completing the scoreboard: removal, and the cost of keeping an array sorted

The book's scoreboard discussion also covers **removing** the entry at a given rank (say, a
disqualified cheater). It is the mirror image of insertion: every entry *below* the removed one
shifts one cell **left** to close the gap, and the vacated last cell is reset to `None`.

```python-run
board = [("Mike", 1105), ("Rob", 750), ("Paul", 720), ("Anna", 660), ("Rose", 590), None, None]
n = 5                                             # number of real entries

def remove(i):
    """Remove and return the entry at rank i (0 = highest), shifting lower entries up."""
    global n
    entry = board[i]
    for j in range(i, n - 1):                     # left to right: each cell takes its right neighbour
        board[j] = board[j + 1]
    board[n - 1] = None                           # clear the duplicate left in the last used cell
    n -= 1
    return entry

def add(entry):
    global n
    if n < len(board): n += 1
    elif entry[1] <= board[-1][1]: return
    j = n - 1
    while j > 0 and board[j - 1][1] < entry[1]:   # right to left: each cell takes its left neighbour
        board[j] = board[j - 1]; j -= 1
    board[j] = entry

print("removed:", remove(1)); print(board)
add(("Jill", 740)); print(board)
```

### Dry run of `remove(1)`

| step | array (5 entries, then unused cells) |
|---|---|
| before | Mike, **Rob**, Paul, Anna, Rose, –, – |
| j = 1: `board[1] = board[2]` | Mike, Paul, Paul, Anna, Rose, –, – |
| j = 2: `board[2] = board[3]` | Mike, Paul, Anna, Anna, Rose, –, – |
| j = 3: `board[3] = board[4]` | Mike, Paul, Anna, Rose, Rose, –, – |
| clear `board[4]` | Mike, Paul, Anna, Rose, –, –, – |

**Direction matters.** Removal copies **left to right** (`board[j] = board[j+1]` for increasing
`j`), insertion copies **right to left**. Do either in the opposite direction and one value is
smeared across the whole range. The rule: always copy *into the cell you no longer need*.

**Cost.** Removing at rank $i$ shifts $n - i - 1$ entries; inserting at rank $i$ shifts $n - i$.
Both are $O(n)$ in the worst case (the front) and $O(1)$ at the back — the same asymmetry as
`list.pop(k)` and `list.insert(k, v)`. Keeping an array sorted under updates therefore costs
$O(n)$ per update even though *finding* the right position takes only $O(\log n)$ with binary
search. That tension — fast search, slow update — is what the linked structures and search trees of
later modules are designed to resolve.

## 6. Working with matrices as lists of lists

A table of numbers with $r$ rows and $c$ columns is the workhorse of scientific computing. Three
operations show how to reason about cost on 2-D data.

```python-run
def transpose(A):
    r, c = len(A), len(A[0])
    return [[A[i][j] for i in range(r)] for j in range(c)]          # c rows of length r

def mat_mul(A, B):
    """Product of an r x m matrix and an m x c matrix: r * m * c scalar multiplications."""
    r, m, c = len(A), len(B), len(B[0])
    assert len(A[0]) == m, "inner dimensions must agree"
    C = [[0] * c for _ in range(r)]                                 # independent rows!
    for i in range(r):
        for j in range(c):
            total = 0
            for k in range(m):
                total += A[i][k] * B[k][j]
            C[i][j] = total
    return C

def spiral(A):
    """Visit every cell once, clockwise from the outside in."""
    out, top, bottom, left, right = [], 0, len(A) - 1, 0, len(A[0]) - 1
    while top <= bottom and left <= right:
        out += [A[top][j] for j in range(left, right + 1)]
        out += [A[i][right] for i in range(top + 1, bottom + 1)]
        if top < bottom:
            out += [A[bottom][j] for j in range(right - 1, left - 1, -1)]
        if left < right:
            out += [A[i][left] for i in range(bottom - 1, top, -1)]
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return out

A = [[1, 2, 3], [4, 5, 6]]
B = [[7, 8], [9, 10], [11, 12]]
print("transpose:", transpose(A), "==", [list(col) for col in zip(*A)])
print("product:  ", mat_mul(A, B))
print("spiral:   ", spiral([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]))
```

- **Transpose** touches each of the $rc$ cells once: $\Theta(rc)$. The idiom `zip(*A)` does the same
  thing by unpacking the rows as arguments.
- **Matrix multiplication** has three nested loops with bounds $r$, $c$ and $m$: $\Theta(rmc)$ scalar
  multiplications, i.e. $\Theta(n^3)$ for two $n \times n$ matrices — the standard example of the
  cubic function from the first lesson, and the cost model behind the matrix-chain problem in the
  dynamic-programming lesson.
- **Spiral order** is a pure index-management exercise: four boundaries shrink towards the centre,
  with the two `if` guards preventing a single remaining row or column from being emitted twice.
  $\Theta(rc)$.

**Input size.** For 2-D data be explicit about what $n$ means. An algorithm that is "quadratic in
the side length" of a square grid is **linear in the number of cells** — the actual size of the
input. Flood fill on an $r \times c$ image is $O(rc)$, which is optimal, not "quadratic".

**Space.** A list of lists costs one outer array of $r$ references plus $r$ separate row arrays of
$c$ references each, scattered in memory. For large numeric tables use NumPy, which stores all
$rc$ numbers in one contiguous compact array (row-major order) and performs these loops in compiled
code — typically 10 to 100 times faster than the pure-Python versions above.

## 7. Pitfalls

- `[[0]*c]*r` aliasing.
- In insertion sort, comparing with `>=` instead of `>` breaks stability.
- Forgetting to wrap with `% 26` in ciphers (or using `-` with a language whose `%` can be negative).
- Mutating a string in place — impossible; convert to a list, then `join`.

## 8. Summary

- Sorted arrays support insertion by shifting: $O(n)$ per insert.
- Insertion sort: $O(n^2)$ worst, $O(n)$ best, $O(n + \text{inversions})$ in general; in place and
  stable.
- Caesar cipher: modular arithmetic on letter indices, $O(n)$ per message.
- 2-D data: list of lists built with a comprehension.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 5.5–5.6.

## Check yourself

```quiz
[
  {"q": "Insertion sort's running time on an already-sorted list of n items is...",
   "options": ["Theta(n^2)", "Theta(n)", "Theta(n log n)", "Theta(1)"], "answer": 1,
   "explain": "Each new element is compared once with its left neighbour and stays put."},
  {"q": "Insertion sort's running time in terms of inversions I is...",
   "options": ["O(I)", "O(n + I)", "O(n I)", "O(n log I)"], "answer": 1,
   "explain": "Each shift removes exactly one inversion, plus O(1) work per element."},
  {"q": "With a Caesar shift of 3, what does 'XYZ' encrypt to?",
   "options": ["ABC", "UVW", "XYZ", "BCD"], "answer": 0,
   "explain": "X(23)+3 = 26 mod 26 = 0 = A; Y -> B; Z -> C."},
  {"q": "How many distinct non-trivial Caesar keys exist for the 26-letter alphabet?",
   "options": ["26!", "25", "13", "2^26"], "answer": 1,
   "explain": "Shifts 1 through 25; shift 0 (or 26) leaves the text unchanged. Brute force is instant."},
  {"q": "Which expression correctly builds a 3x4 grid of zeros with independent rows?",
   "options": ["[[0]*4]*3", "[[0]*4 for _ in range(3)]", "[0]*12", "([0]*4)*3"], "answer": 1,
   "explain": "The comprehension evaluates [0]*4 three times, creating three distinct lists."},
  {"q": "Why does the CaesarCipher._transform convert the message to a list first?",
   "options": ["Lists are faster to print", "Strings are immutable, so characters cannot be replaced in place", "To sort the characters", "To remove punctuation"], "answer": 1,
   "explain": "Build a mutable list of characters, modify it, then join once: O(n)."},
  {"q": "Is insertion sort (as written, shifting only while A[j-1] > cur) stable?",
   "options": ["Yes", "No", "Only for integers", "Only when n is even"], "answer": 0,
   "explain": "Equal elements are never moved past each other, so their relative order is preserved."}
]
```
