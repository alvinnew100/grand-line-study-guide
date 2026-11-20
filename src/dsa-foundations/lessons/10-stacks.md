# Stacks and their applications

A **stack** is a collection of objects inserted and removed according to the **last-in, first-out
(LIFO)** principle. You may insert at any time, but you can only access or remove the most recently
inserted object that remains — the "top". Think of a spring-loaded stack of plates in a cafeteria:
you take the top plate, and new plates are pushed onto the top.

Stacks are among the simplest data structures, yet they are everywhere: a browser's back button, an
editor's undo history, the call stack that implements recursion, and the parsers that check whether
your brackets match.

## 1. The stack ADT

An **abstract data type (ADT)** specifies *what* operations do, not *how*. The stack ADT, for a
stack `S`:

| Operation | Meaning |
|---|---|
| `S.push(e)` | add element `e` to the top |
| `S.pop()` | remove and return the top element; error if empty |
| `S.top()` | return (without removing) the top element; error if empty |
| `S.is_empty()` | `True` if the stack has no elements |
| `len(S)` | number of elements |

A sample sequence of operations:

| Operation | Return | Stack contents (bottom → top) |
|---|---|---|
| `push(5)` | – | [5] |
| `push(3)` | – | [5, 3] |
| `len(S)` | 2 | [5, 3] |
| `pop()` | 3 | [5] |
| `is_empty()` | False | [5] |
| `pop()` | 5 | [] |
| `is_empty()` | True | [] |
| `pop()` | error | [] |
| `push(7)` | – | [7] |
| `push(9)` | – | [7, 9] |
| `top()` | 9 | [7, 9] |
| `push(4)` | – | [7, 9, 4] |
| `pop()` | 4 | [7, 9] |

## 2. Array-based implementation: the adapter pattern

A Python list already supports adding and removing at the end in $O(1)$ amortised time, so the end
of the list makes a perfect top. But a list also allows inserting in the middle, indexing, etc. —
operations that would break the stack abstraction. The **adapter design pattern** wraps an existing
class and exposes only a new, restricted interface:

| Stack method | Realised with list `L` |
|---|---|
| `S.push(e)` | `L.append(e)` |
| `S.pop()` | `L.pop()` |
| `S.top()` | `L[-1]` |
| `S.is_empty()` | `len(L) == 0` |
| `len(S)` | `len(L)` |

```python-run
class Empty(Exception):
    """Error attempting to access an element from an empty container."""
    pass

class ArrayStack:
    """LIFO Stack implementation using a Python list as underlying storage."""
    def __init__(self):
        self._data = []                   # nonpublic list instance
    def __len__(self):
        return len(self._data)
    def is_empty(self):
        return len(self._data) == 0
    def push(self, e):
        self._data.append(e)              # new item stored at end of list
    def top(self):
        if self.is_empty():
            raise Empty('Stack is empty')
        return self._data[-1]             # the last item in the list
    def pop(self):
        if self.is_empty():
            raise Empty('Stack is empty')
        return self._data.pop()           # remove last item from list

S = ArrayStack()
S.push(5); S.push(3)
print(len(S), S.pop(), S.is_empty(), S.pop(), S.is_empty())
try:
    S.pop()
except Empty as e:
    print("Empty:", e)
```

Defining our own `Empty` exception is better than letting the list raise `IndexError`, which would
leak an implementation detail ("index") through the abstraction.

### Performance

| Operation | Running time |
|---|---|
| `push` | $O(1)$ amortised |
| `pop` | $O(1)$ amortised |
| `top`, `is_empty`, `len` | $O(1)$ |

Space is $O(n)$. The amortisation comes from the underlying dynamic array resizing occasionally.

> [!TIP]
> If you know the maximum size in advance, you can preallocate (`[None] * maxlen`) and track the
> size yourself, avoiding resizes — the book suggests this as an exercise.

## 3. Application: reversing data

Push every item, then pop them all: they come out in reverse. The book uses this to reverse the
lines of a file:

```python-run
def reverse_lines(lines):
    S = []
    for line in lines:
        S.append(line.rstrip('\n'))       # push
    out = []
    while S:
        out.append(S.pop())               # pop: reverse order
    return out

print(reverse_lines(["first\n", "second\n", "third\n"]))
```

## 4. Application: matching delimiters

Arithmetic expressions use grouping pairs: parentheses `( )`, braces `{ }`, brackets `[ ]`. Every
opening symbol must be matched by the corresponding closing symbol, properly nested:

- correct: `( )(( )){([( )])}`, `((( )(( )){([( )])}))`
- incorrect: `)(( )){([( )])}`, `({[ ])}`, `(`

**Algorithm:** scan left to right. Push each opening symbol. On a closing symbol, the stack must be
non-empty and its top must be the matching opener — pop it. At the end, the stack must be empty.

```python-run
def is_matched(expr):
    """Return True if all delimiters are properly matched; False otherwise."""
    lefty = '({['                          # opening delimiters
    righty = ')}]'                         # respective closing delims
    S = []
    for c in expr:
        if c in lefty:
            S.append(c)                    # push left delimiter on stack
        elif c in righty:
            if not S:
                return False               # nothing to match with
            if righty.index(c) != lefty.index(S.pop()):
                return False               # mismatched
    return not S                           # were all symbols matched?

for e in ["()(()){([()])}", "((()(()){([()])}))", ")(()){([()])}", "({[])}", "("]:
    print(f"{e:22s} {is_matched(e)}")
```

$O(n)$ time: one push or pop per character. Each of the three failure modes — closing with empty
stack, mismatched pair, leftover openers — corresponds to one `return False` (the last via
`return not S`).

### Matching HTML tags

HTML documents nest tags like `<body>`, `<h1>`, `<p>` with closing tags `</body>`, `</h1>`,
`</p>`. Exactly the same algorithm works with tag names instead of single characters:

```python-run
def is_matched_html(raw):
    S = []
    j = raw.find('<')                      # find first '<' character (if any)
    while j != -1:
        k = raw.find('>', j + 1)           # find next '>' character
        if k == -1:
            return False                   # invalid tag
        tag = raw[j + 1:k]                 # strip away < >
        if not tag.startswith('/'):        # this is opening tag
            S.append(tag)
        else:                              # this is closing tag
            if not S:
                return False
            if tag[1:] != S.pop():
                return False               # mismatched tag
        j = raw.find('<', k + 1)           # find next '<' character (if any)
    return not S

print(is_matched_html("<body><center><h1>The Little Boat</h1></center><p>The storm tossed.</p></body>"))
print(is_matched_html("<body><p>unclosed</body>"))
```

## 5. Application: evaluating postfix expressions

In **postfix** (reverse Polish) notation operators follow their operands: `5 1 2 + 4 * + 3 -`
means $5 + (1 + 2) \cdot 4 - 3 = 14$. No parentheses are needed. A stack evaluates it in one pass:
push numbers; on an operator, pop the right operand, then the left, apply, and push the result.

```python-run
def eval_postfix(tokens):
    S = []
    for t in tokens:
        if t in '+-*/':
            right = S.pop(); left = S.pop()      # order matters for - and /
            S.append({'+': left + right, '-': left - right,
                      '*': left * right, '/': left / right}[t])
        else:
            S.append(float(t))
    return S.pop()

print(eval_postfix("5 1 2 + 4 * + 3 -".split()))
```

The same postfix form is produced by a **postorder traversal of an expression tree** (trees module),
and the implicit stack is the recursion stack.

## 6. Stacks and recursion

Every running Python program uses a stack: the **call stack** of activation records. When function
`f` calls `g`, `f`'s frame stays below `g`'s on the stack; when `g` returns, its frame is popped and
`f` continues. This is why any recursive algorithm can be converted to an iterative one with an
explicit stack (recursion lesson), and why depth-first search is naturally implemented with a stack
(graphs module).

> [!INTERVIEW]
> Stack problems in interviews usually hide behind phrases like "most recent", "nested",
> "matching", "undo", or "next greater element" (monotonic stack). Recognise LIFO structure first;
> the code is then short. Always handle the empty-stack case explicitly.

## 7. Worked application: from infix to postfix

Section 5 evaluated a postfix expression. But people write **infix** — `3 + 4 * 2` — where
precedence and parentheses decide the order. Converting infix to postfix is another classic stack
algorithm (Dijkstra's *shunting-yard* algorithm), and together with the postfix evaluator it gives a
complete calculator.

**Idea.** Operands go straight to the output. Operators wait on a stack until we know that nothing
of higher precedence is coming to claim their right operand:

1. **Operand:** append it to the output.
2. **Operator `op`:** while the stack top is an operator whose precedence is **greater than or equal
   to** `op`'s (for left-associative operators), pop it to the output. Then push `op`.
3. **`(`:** push it. It acts as a wall: nothing below it may be popped until it is closed.
4. **`)`:** pop operators to the output until the matching `(` is on top; discard the `(`.
5. **End of input:** pop every remaining operator to the output.

```python-run
PREC = {'+': 1, '-': 1, '*': 2, '/': 2}

def to_postfix(tokens, trace=False):
    out, ops = [], []
    for t in tokens:
        if t in PREC:
            while ops and ops[-1] != '(' and PREC[ops[-1]] >= PREC[t]:
                out.append(ops.pop())            # the waiting operator binds at least as tightly
            ops.append(t)
        elif t == '(':
            ops.append(t)
        elif t == ')':
            while ops[-1] != '(':
                out.append(ops.pop())
            ops.pop()                            # discard the '('
        else:
            out.append(t)                        # operand
        if trace:
            print(f"read {t:>2}   stack: {' '.join(ops):<8} output: {' '.join(out)}")
    while ops:
        out.append(ops.pop())
    return out

def eval_postfix(tokens):
    S = []
    for t in tokens:
        if t in PREC:
            right, left = S.pop(), S.pop()
            S.append({'+': left + right, '-': left - right, '*': left * right, '/': left / right}[t])
        else:
            S.append(float(t))
    return S.pop()

expr = "3 + 4 * ( 2 - 1 ) / 5".split()
post = to_postfix(expr, trace=True)
print("postfix:", " ".join(post), "=", eval_postfix(post))
for e in ["8 - 3 - 2", "2 * 3 + 4", "2 * ( 3 + 4 )", "( 1 + 2 ) * ( 3 + 4 ) - 5"]:
    p = to_postfix(e.split())
    print(f"{e:28s} -> {' '.join(p):22s} = {eval_postfix(p)}")
```

### Dry run: `3 + 4 * ( 2 - 1 ) / 5`

| token | action | operator stack | output |
|---|---|---|---|
| 3 | operand → output | | 3 |
| + | stack empty → push | + | 3 |
| 4 | output | + | 3 4 |
| * | `+` has lower precedence → push | + * | 3 4 |
| ( | push | + * ( | 3 4 |
| 2 | output | + * ( | 3 4 2 |
| - | top is `(` → push | + * ( - | 3 4 2 |
| 1 | output | + * ( - | 3 4 2 1 |
| ) | pop until `(` | + * | 3 4 2 1 - |
| / | `*` has equal precedence → pop it, then push `/` | + / | 3 4 2 1 - * |
| 5 | output | + / | 3 4 2 1 - * 5 |
| end | pop everything | | 3 4 2 1 - * 5 / + |

Value: $3 + (4 \cdot (2 - 1)) / 5 = 3.8$.

**Why `>=` and not `>`?** Subtraction and division are **left-associative**: `8 - 3 - 2` means
`(8 - 3) - 2 = 3`. When the second `-` arrives, the first one — of *equal* precedence — must be
output first, giving `8 3 - 2 -`. With `>` you would produce `8 3 2 - -`, which is
`8 - (3 - 2) = 7`. (A right-associative operator such as exponentiation uses the strict test.)

**Complexity.** Every token is pushed at most once and popped at most once, so both conversion and
evaluation are $O(n)$ time with $O(n)$ extra space. This two-stack-pass design is essentially how
simple interpreters work, and CPython's own evaluation loop is a stack machine executing postfix-like
bytecode.

### 7.1 Three implementations of the stack, compared

| | Python list adapter (`ArrayStack`) | preallocated array of capacity $N$ | singly linked list (next module) |
|---|---|---|---|
| `push` / `pop` | $O(1)$ amortised | $O(1)$ worst case; `push` fails when full | $O(1)$ worst case |
| memory | up to about $2n$ references after a resize | exactly $N$ cells, used or not | one node object per element (element + next) |
| best when | default choice in Python | hard real-time, known bound | worst-case guarantees without a size bound |

The interface — and therefore every application in this lesson — is identical for all three; that
is the practical payoff of programming against an ADT.

## 8. Pitfalls

- Popping the operands in the wrong order for non-commutative operators.
- Forgetting the final emptiness check in delimiter matching (`"(("` would wrongly pass).
- Using `list.pop(0)` for a stack — that is the bottom, and it costs $O(n)$.
- Letting `IndexError` escape from an empty pop instead of a meaningful exception.

## 9. Summary

- Stack = LIFO; operations push, pop, top, is_empty, len — all $O(1)$ (push/pop amortised) with an
  array-based adapter over a Python list.
- Applications: reversal, delimiter and tag matching, postfix evaluation, undo, recursion.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 6.1.

## Check yourself

```quiz
[
  {"q": "Starting empty: push(5), push(3), pop(), push(2), push(8), pop(), pop(). What does the last pop return?",
   "options": ["5", "3", "2", "8"], "answer": 2,
   "explain": "After pop() of 3 we have [5]; push 2, 8 -> [5,2,8]; pop -> 8; pop -> 2."},
  {"q": "The ArrayStack class is an example of which design pattern?",
   "options": ["Iterator", "Adapter", "Composite", "Template method"], "answer": 1,
   "explain": "It adapts a Python list to the narrower stack interface."},
  {"q": "Why should the top of an array-based stack be at the END of the list?",
   "options": ["append/pop at the end are O(1) amortised; at the front they are O(n)", "It is easier to print", "Python lists only allow access at the end", "No reason"], "answer": 0,
   "explain": "Inserting/removing at index 0 shifts every element."},
  {"q": "is_matched('(()') returns...",
   "options": ["True", "False, because a '(' remains on the stack at the end", "False, because of a mismatch", "an exception"], "answer": 1,
   "explain": "All closers matched, but the final check `return not S` fails with one leftover opener."},
  {"q": "Evaluate the postfix expression `6 2 / 3 -`.",
   "options": ["0", "3", "-3", "1"], "answer": 0,
   "explain": "6 / 2 = 3, then 3 - 3 = 0. Pop right operand first, then left."},
  {"q": "Which is NOT a natural stack application?",
   "options": ["Undo in a text editor", "Matching HTML tags", "Serving customers in arrival order", "Implementing recursion"], "answer": 2,
   "explain": "Arrival-order service is FIFO: a queue."}
]
```
