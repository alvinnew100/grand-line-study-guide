# Using arrays: insertion sort, ciphers and 2-D data

> **Before this lesson:** You should know that a list is an array of cells, that inserting into
> the middle means shifting items along, and what a reference is. All of that is in
> [Low-level arrays and Python's sequence types](#/lesson/dsa-foundations/low-level-arrays).
> Python classes were introduced in
> [Dynamic arrays and amortised analysis](#/lesson/dsa-foundations/dynamic-arrays).

## In plain words

The last two lessons explained what an array *is*. This one is four small projects that use
arrays the way working programs do: a leaderboard that stays in order, a method for sorting, a
secret code, and grids such as game boards and tables of numbers.

One picture ties the first two together. When you are dealt playing cards one at a time, you
keep the cards in your hand in order. Each new card is slid leftwards past every card that is
bigger than it, until it sits in the right place. A leaderboard does this with each new score,
and doing it for every item of a list is a sorting method called insertion sort.

Why it matters for a job: insertion sort is the first sorting algorithm interviewers expect you
to write from memory, and real sorting libraries still use it for short lists. Grids built from
lists of lists appear in a large share of interview problems (boards, images, mazes), and the
"all my rows changed at once" bug in section 4 catches almost everyone once.

## 1. Storing high scores

A game keeps its best few scores in order, highest first. Each entry has a player's name and a
score. The `Scoreboard` class below stores entries in a list of fixed capacity and keeps them
sorted at all times.

**Adding an entry.** A new score earns a place if the board still has room or if it beats the
lowest score on the board. To place it, start at the bottom of the board and move every entry
with a lower score one cell to the right, then put the new entry into the gap that opens up.

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

**Reading this code.**

- `GameEntry` is a small class holding a name and a score. `__str__` is the hook Python calls
  when an object is printed.
- `Scoreboard.__init__` creates `capacity` empty cells (`None`) and sets the count `_n` to 0.
- In `add`, the variable `good` is `True` when the board has room, or when the new score beats
  the last entry (`self._board[-1]`; index `-1` means "last cell").
- If the board is not full, `_n` grows by one. If it is full, `_n` stays put, and the lowest
  entry is about to be overwritten.
- `j` starts at the last used cell. The `while` loop copies the entry on the left into cell `j`
  as long as that entry has a lower score, moving `j` leftwards. When it stops, cell `j` is the
  right home for the new entry.

The board printed at the end is Ruffy 1200, Mike 1105, Rob 750, Jill 740, Paul 720. Jack (510)
arrived when the board was full and did not beat the lowest score, so he never appears. Jill's
arrival pushed Rose off the bottom, and Ruffy's pushed Anna off.

Adding costs $O(c)$ for a board of capacity $c$, all of it shifting. That shifting loop is
exactly the inner loop of insertion sort.

## 2. Insertion sort

**Problem:** rearrange a list so that its items are in *nondecreasing* order, meaning each item
is at least as large as the one before it. (We say "nondecreasing" and not "increasing" because
equal items are allowed.)

**Idea:** grow a sorted stretch at the front of the list, one item at a time. A single item is
sorted by definition. Take the next item (the *current* one) and slide it left past every larger
item until it is in place; now the sorted stretch is one longer. Repeat until the stretch is the
whole list.

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

**Reading this code.** The outer loop takes `k = 1, 2, ..., n - 1`; item 0 needs no work. `cur`
keeps a copy of the item being inserted, because its cell is about to be overwritten. The
`while` loop runs as long as there is an item to the left (`j > 0`) and that item is larger than
`cur`; each pass copies the larger item one cell right and steps `j` left. When the loop ends,
`A[j] = cur` drops the saved item into the gap. The `print` shows the list after each insertion:
the letters `B C D` stay put, then `A` travels all the way to the front, and so on until the
list reads `A B C D E F G H`.

### Dry run

A **dry run** means carrying out an algorithm by hand on a small input. Sorting
`[5, 2, 4, 6, 1, 3]`, with a bar marking the end of the sorted stretch:

| k | cur | sorted prefix after insertion |
|---|---|---|
| 1 | 2 | 2 5 \| 4 6 1 3 |
| 2 | 4 | 2 4 5 \| 6 1 3 |
| 3 | 6 | 2 4 5 6 \| 1 3 |
| 4 | 1 | 1 2 4 5 6 \| 3 |
| 5 | 3 | 1 2 3 4 5 6 |

### Analysis

- **Worst case** (the input is in reverse order): every new item must travel to the front, so
  the inner loop runs $k$ times for each $k$, and
  $1 + 2 + \cdots + (n-1) = n(n-1)/2 = \Theta(n^2)$.
- **Best case** (the input is already sorted): the inner loop's test fails at once every time:
  $\Theta(n)$.
- **In between.** An **inversion** is a pair of items that are in the wrong order relative to
  each other: positions $i < j$ with $A[i] > A[j]$. The list `[2, 3, 1]` has two inversions,
  (2, 1) and (3, 1). Each shift in insertion sort repairs exactly one inversion, so the running
  time is $O(n + I)$, where $I$ is the number of inversions. A nearly sorted list has few
  inversions, which makes insertion sort excellent for nearly sorted data.
- It is **in place**: it rearranges the list using only $O(1)$ extra memory (the variables
  `cur`, `j`, `k`).
- It is **stable**: items that compare equal stay in their original relative order, because the
  loop shifts only items that are *strictly* greater. Stability matters when records are sorted
  by one field after another (by name, then by date, for instance).

> [!INTERVIEW]
> Why do the sorting routines inside real languages (Python's Timsort, C++'s introsort) switch
> to insertion sort for short stretches? For $n$ below roughly 16 to 64, its tiny overhead and
> its habit of touching neighbouring memory cells beat the $O(n \log n)$ algorithms, and it
> speeds up automatically when the data is already partly ordered (it is *adaptive*).

### Loop invariant

Using the tool from the analysis lesson: at the start of iteration $k$, `A[0:k]` holds the
original first $k$ items in sorted order. This is true at the start ($k = 1$, a single item).
Each iteration inserts `A[k]` into its place, so the statement holds for $k + 1$. When the loop
finishes, $k = n$, and the statement says the whole list is sorted.

## 3. Simple cryptography: the Caesar cipher

**Encryption** turns a readable message, the *plaintext*, into a scrambled one, the
*ciphertext*; **decryption** reverses it. The Caesar cipher, said to have been used by Julius
Caesar, replaces each letter by the letter $r$ places later in the alphabet, wrapping round from
Z back to A. With $r = 3$: A becomes D, B becomes E, and at the end X becomes A, Y becomes B and
Z becomes C.

To compute with letters, number them $A = 0, \ldots, Z = 25$. The wrap-around is handled by the
**modulo** operation, written `mod` in mathematics and `%` in Python: $a \bmod 26$ is the
remainder when $a$ is divided by 26. So $(23 + 3) \bmod 26 = 0$, which turns X into A. It is
clock arithmetic with 26 hours. The two rules are

$$\text{encrypt}(x) = (x + r) \bmod 26, \qquad \text{decrypt}(y) = (y - r) \bmod 26.$$

Python's `ord` gives the number that stands for a character and `chr` goes the other way; since
the capital letters have consecutive numbers, `ord('C') - ord('A')` is 2. The class below
prepares two 26-character lookup strings (an *encoder* and a *decoder*) once, and then
translates a message by replacing its letters in a **list of characters**, because a string
cannot be modified in place:

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

The demo prints `Secret:  WKH HDJOH LV LQ SODB; PHHW DW MRH'V.` and then the original message
again. In `_transform`, `isupper()` is true only for capital letters, so spaces and punctuation
pass through unchanged. Each character is handled in constant time, so a message of length $n$
takes $O(n)$.

One detail makes decryption painless in Python: `%` with a positive number on the right never
gives a negative result, even when the left side is negative. `(-3) % 26` is `23`, so
decrypting A with shift 3 gives X as it should. In several other languages (C, Java,
JavaScript) the same expression gives $-3$ and you must add 26 yourself.

> [!WARNING]
> The Caesar cipher offers no real secrecy. There are only 25 useful shifts, so an attacker can
> try them all, an approach called **brute force**. Or they can count letters: E is the most
> common letter in English, so the most common letter in the ciphertext probably stands for E.
> It is a teaching example, not security.

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

Here `r` is the number of rows and `c` the number of columns. The second form is a notorious
bug, and the referential-array model explains it: `[[0] * c]` is a list with one cell that
refers to one row, and `* r` copies that *reference* `r` times. Every "row" is the same list
object, so changing `data[2][0]` changes column 0 of *every* row. The third form runs
`[0] * c` afresh for each row and so creates `r` separate lists.

```python-run
bad = [[0] * 3] * 2
bad[0][0] = 99
good = [[0] * 3 for _ in range(2)]
good[0][0] = 99
print("bad: ", bad)
print("good:", good)
```

### 4.2 Case study: tic-tac-toe

The output is `bad:  [[99, 0, 0], [99, 0, 0]]` and `good: [[99, 0, 0], [0, 0, 0]]`.

A noughts-and-crosses board is a 3×3 list of lists of characters (`'X'`, `'O'` or a space). The
class below places marks, refuses illegal moves by raising `ValueError`, and checks for a winner
by testing all three rows, all three columns and both diagonals. The expression
`mark == b[0][0] == b[0][1] == b[0][2]` is true when all three cells of the top row hold `mark`.

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

For a grid with $r$ rows and $c$ columns, visiting every cell takes $\Theta(rc)$ time. In
libraries that store grids compactly (NumPy, or arrays in C), a two-dimensional array is laid
out in memory as one unbroken block: all of row 0, then all of row 1, and so on. This layout is
called **row-major order**, and cell `A[i][j]` sits $i \cdot c + j$ cells from the start. Going
through such a grid row by row walks straight through memory, which processors handle quickly;
going column by column jumps $c$ cells at every step. A Python list of lists is not one block,
but "rows in the outer loop, columns in the inner loop" is still the customary way to write it.

## 5. Completing the scoreboard: removal, and the cost of keeping an array sorted

A scoreboard also needs to **remove** the entry at a given rank, for instance a player caught
cheating. Removal is the mirror image of insertion: every entry *below* the removed one moves
one cell **left** to close the gap, and the last used cell is reset to `None`. This demo uses
plain tuples `(name, score)` and module-level functions; `global n` lets a function change the
variable `n` defined outside it.

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

A rectangular table of numbers with $r$ rows and $c$ columns is called a **matrix**, and it is
the workhorse of scientific computing and machine learning. Three operations show how to reason
about cost on two-dimensional data:

- The **transpose** of a matrix swaps rows and columns: row $i$ becomes column $i$.
- The **product** of an $r \times m$ matrix $A$ and an $m \times c$ matrix $B$ is an
  $r \times c$ matrix whose entry in row $i$, column $j$ is found by going along row $i$ of $A$
  and down column $j$ of $B$ together, multiplying matching entries and adding the results.
- **Spiral order** lists the cells starting along the top row and winding inwards clockwise.

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

- **Rows that are all the same list.** `[[0]*c]*r` makes `r` references to one row.
- **Breaking stability.** In insertion sort, shifting while `A[j-1] >= cur` (instead of `>`)
  moves equal items past each other, and the sort is no longer stable.
- **Forgetting the wrap-around.** Leave out `% 26` in a cipher and Z turns into a symbol beyond
  the alphabet. And in languages whose `%` can return a negative number, add 26 before taking
  the remainder when decrypting.
- **Trying to change a string in place.** It cannot be done; convert to a list, change the list,
  then `join`.
- **Shifting in the wrong direction.** Insertion copies right to left, removal left to right.

## 8. Summary

- A sorted array accepts a new item by shifting larger items along: $O(n)$ per insertion.
- Insertion sort repeats that step for each item: $O(n^2)$ in the worst case, $O(n)$ in the
  best, $O(n + \text{inversions})$ in general; it is in place and stable.
- The Caesar cipher is modular arithmetic on letter numbers, $O(n)$ per message, and easy to
  break.
- Two-dimensional data is a list of lists, built with a comprehension so that the rows are
  separate objects.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 5.5–5.6.

## Glossary

- **Nondecreasing order**: each item is greater than or equal to the one before it.
- **Insertion sort**: sorting by inserting each item into a growing sorted stretch at the front.
- **Dry run**: executing an algorithm by hand on a small example.
- **Inversion**: a pair of items that appear in the wrong order relative to each other.
- **In place**: using only a constant amount of memory beyond the input itself.
- **Stable sort**: a sort that keeps equal items in their original relative order.
- **Adaptive**: faster on inputs that are already partly sorted.
- **Encryption / decryption**: scrambling a message / recovering the original.
- **Plaintext / ciphertext**: the readable message / its scrambled form.
- **Modulo (`%`)**: the remainder after division; arithmetic that wraps round.
- **Brute force**: solving a problem by trying every possibility.
- **Matrix**: a rectangular table of numbers.
- **Transpose**: a matrix with its rows and columns swapped.
- **Row-major order**: storing a grid row after row in one block of memory.

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
