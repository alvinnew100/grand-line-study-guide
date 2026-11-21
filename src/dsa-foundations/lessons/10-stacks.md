# Stacks and their applications

> **Before this lesson:** You should know that `append` and `pop()` at the end of a Python list
> take $O(1)$ amortised time, from
> [Dynamic arrays and amortised analysis](#/lesson/dsa-foundations/dynamic-arrays), and be able
> to read a small Python class. The call stack was introduced in
> [Thinking recursively](#/lesson/dsa-foundations/recursion-examples).

## In plain words

A **stack** is a collection with one rule: the only item you can look at or take away is the one
you added most recently. This rule is called **last-in, first-out**, shortened to **LIFO**.

Think of a pile of plates in a canteen. Clean plates are put on top of the pile, and a customer
takes the top plate. Nobody pulls a plate out of the middle. The last plate put down is the
first one picked up. The place where items go on and come off is called the **top**.

Why it matters for a job: stacks are everywhere once you know to look. A browser's Back button
returns to the most recent page; an editor's Undo reverses the most recent change; a programming
language keeps track of unfinished function calls on the call stack; and every tool that checks
whether brackets or tags are balanced uses one. Interview problems that mention "most recent",
"nested" or "matching" are usually stack problems wearing a disguise.

## 1. The stack ADT

An **abstract data type**, abbreviated **ADT**, is a description of *what* operations a
collection offers and what each one does, without saying *how* it is built. It is a contract
between the person who uses the collection and the person who implements it. A vending machine
is a fair comparison: you know the buttons and what each gives you, and you neither know nor
care how the inside is arranged. Separating the two lets the inside change without breaking any
code that uses it.

The stack ADT, for a stack `S`, has five operations. To **push** is to add an item on top, and
to **pop** is to remove the top item and hand it back.

| Operation | Meaning |
|---|---|
| `S.push(e)` | add element `e` to the top |
| `S.pop()` | remove and return the top element; error if empty |
| `S.top()` | return (without removing) the top element; error if empty |
| `S.is_empty()` | `True` if the stack has no elements |
| `len(S)` | number of elements |

Follow this sequence of operations one row at a time, starting from an empty stack. The right
column shows the contents with the bottom on the left and the top on the right.

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

Notice that `pop()` on an empty stack is an error, and that 7 stays buried under 9 until 9 has
gone.

A Python list already adds and removes at its end in $O(1)$ amortised time, so the end of a list
makes a perfect top. But a list also allows inserting in the middle, reading any position, and
more; if code using our stack could do those things, it would no longer be a stack, and we could
not rely on the LIFO rule. The fix is to wrap the list inside a new class that offers only the
five stack operations. Reusing an existing class behind a different, narrower set of methods is
called the **adapter design pattern** (a *design pattern* is a named, reusable way of organising
code). The set of methods a class offers to its users is its **interface**.

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

**Reading this code line by line**

- `class Empty(Exception)` defines a new kind of error. An **exception** is Python's way of
  signalling that something went wrong; `raise` triggers one and `try ... except` catches it.
- `self._data = []` is the hidden list. Everything else is a thin layer over it.
- `push` appends, so the newest item is always at the end.
- `top` returns `self._data[-1]`, the last item, without removing it; `pop` removes it with the
  list's own `pop()`. Both first check for an empty stack and raise `Empty` if so.
- The test pushes 5 then 3. `len(S)` is 2; `pop()` gives 3 (the most recent); the stack is not
  empty; `pop()` gives 5; now it is empty. Output: `2 3 False 5 True`. A third `pop()` raises
  the exception, which the `except` line catches and prints as `Empty: Stack is empty`.

Why define our own `Empty` error instead of letting the list raise its own `IndexError`? Because
"index" is a detail of the list hidden inside. A user of a stack should hear about stacks.

### Performance

| Operation | Running time |
|---|---|
| `push` | $O(1)$ amortised |
| `pop` | $O(1)$ amortised |
| `top`, `is_empty`, `len` | $O(1)$ |

Space is $O(n)$ for $n$ items. The word "amortised" is there because the list underneath
occasionally resizes, as the dynamic-arrays lesson showed.

> [!TIP]
> If you know the largest size the stack will ever reach, you can create the storage at full
> size (`[None] * maxlen`) and keep track of the count yourself. No resize ever happens, so
> every operation is $O(1)$ in the worst case, not only on average.

## 3. Application: reversing data

Push every item, then pop until the stack is empty: the items come out in reverse order, because
the last one in is the first one out. Here the idea reverses the lines of a text. A plain list
plays the role of the stack (`append` is push, `pop()` is pop), and `rstrip('\n')` removes the
end-of-line character from each line.

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

The output is `['third', 'second', 'first']`.

## 4. Application: matching delimiters

Arithmetic expressions and program code use three kinds of grouping pairs, called
**delimiters**: parentheses `( )`, braces `{ }` and brackets `[ ]`. Every opening symbol must be
closed by the matching closing symbol, and pairs must nest properly: whatever was opened last
must be closed first.

- correct: `( )(( )){([( )])}`, `((( )(( )){([( )])}))`
- incorrect: `)(( )){([( )])}`, `({[ ])}`, `(`

"Opened last, closed first" is the LIFO rule, so a stack is the natural tool.

**Algorithm:** read the text from left to right. Push each opening symbol. On a closing symbol,
the stack must not be empty and its top must be the matching opener; pop it. When the text ends,
the stack must be empty.

Trace it on `{[()]}`. Push `{`, push `[`, push `(`. Then `)` arrives: the top is `(`, a match,
pop. Then `]`: the top is `[`, pop. Then `}`: the top is `{`, pop. The stack is empty at the
end, so the text is balanced. Now `({[])}`: after three pushes, `]` matches `[` and pops it;
then `)` arrives but the top is `{`. Mismatch.

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

**Reading this code.** `lefty` and `righty` list the openers and closers in the same order, so a
pair matches when both symbols sit at the same position in their strings; `righty.index(c)` and
`lefty.index(S.pop())` find those positions. `not S` is `True` when the list `S` is empty. The
five test strings print `True`, `True`, `False`, `False`, `False`.

There are three ways to fail, and each has its own exit: a closer arriving when the stack is
empty, a closer that does not match the top, and openers left over at the end (caught by
`return not S`). The time is $O(n)$: each character causes at most one push or one pop.

### Matching HTML tags

HTML, the language of web pages, marks up text with **tags** such as `<body>`, `<h1>` and `<p>`,
each closed later by a tag with a slash: `</body>`, `</h1>`, `</p>`. Tags must nest in the same
way brackets do, so the same algorithm works, comparing tag names instead of single characters.
In the code, `raw.find('<', k)` returns the position of the next `<` at or after position `k`,
or `-1` if there is none.

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

The usual way of writing arithmetic, with the operator between the numbers it works on
(`1 + 2`), is called **infix** notation. In **postfix** notation, also known as reverse Polish
notation, each operator comes *after* its two numbers (its **operands**): `1 2 +`. A longer
example: `5 1 2 + 4 * + 3 -` means $5 + (1 + 2) \cdot 4 - 3 = 14$. Postfix never needs
parentheses, and a stack evaluates it in a single pass: push each number; on an operator, pop
the right operand, then the left one, apply the operator, and push the result.

Trace `5 1 2 + 4 * + 3 -`: push 5, 1, 2. On `+`, pop 2 and 1, push 3; the stack is `[5, 3]`.
Push 4. On `*`, pop 4 and 3, push 12; the stack is `[5, 12]`. On `+`, pop 12 and 5, push 17.
Push 3. On `-`, pop 3 and 17, push 14. The single number left is the answer.

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

The code prints `14.0`. `tokens` is the expression split into pieces at the spaces; a **token**
is one meaningful unit, here a number or an operator. The dictionary in the middle computes all
four possible results and `[t]` picks the one for the operator at hand. The order of the two
pops matters for subtraction and division: the first value popped is the *right* operand.

The trees module will show the same postfix order arising from a tree of the expression.

## 6. Stacks and recursion

Every running Python program uses a stack: the **call stack** of frames from the recursion
lessons. When function `f` calls `g`, the frame for `f` stays underneath the frame for `g`; when
`g` returns, its frame is popped and `f` carries on. Calls finish in the reverse of the order
they started, which is LIFO. This is why any recursive algorithm can be rewritten as a loop with
an explicit stack, and why the depth-first search of the graphs module is naturally written
with one.

> [!INTERVIEW]
> Stack problems in interviews tend to hide behind words like "most recent", "nested",
> "matching", "undo" or "next greater element". Recognise the last-in, first-out structure
> first; the code is then short. Always say what happens when the stack is empty.

## 7. Worked application: from infix to postfix

Section 5 evaluated a postfix expression, but people write infix, such as `3 + 4 * 2`, where two
conventions decide the order of operations. **Precedence** says multiplication and division are
done before addition and subtraction. Parentheses override precedence. Converting infix to
postfix is another classic stack algorithm, known as the *shunting-yard* algorithm and due to
Edsger Dijkstra. Combined with the postfix evaluator it gives a complete calculator.

**Idea.** Numbers go straight to the output. An operator cannot be output yet, because its
right-hand operand has not been read; it waits on a stack until we are sure that nothing of
higher precedence is about to claim that operand:

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

- **Popping operands in the wrong order.** For `-` and `/` the order matters: the first pop is
  the right operand. `8 3 -` is 5, not $-5$.
- **Forgetting the final emptiness check** when matching delimiters. Without it, `"(("` would
  wrongly pass.
- **Using `list.pop(0)` for a stack.** That removes the *bottom*, which breaks LIFO and costs
  $O(n)$ because every other item shifts.
- **Letting `IndexError` escape** from a pop on an empty stack instead of a meaningful error.
- **Reaching inside the stack.** Code that reads `S._data[0]` has abandoned the abstraction; if
  you need access to the middle, a stack is the wrong structure.

## 9. Summary

- A stack is a last-in, first-out collection with operations push, pop, top, is_empty and len.
- Built as an adapter over a Python list, every operation is $O(1)$ (push and pop amortised).
- Applications: reversing, matching delimiters and tags, evaluating postfix, converting infix to
  postfix, undo histories, and the call stack that makes recursion work.
- Programming against the ADT means the implementation can change without touching the code
  that uses it.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 6.1.

## Glossary

- **Stack**: a collection in which the most recently added item is the first one removed.
- **LIFO**: last-in, first-out.
- **Push / pop / top**: add an item on top / remove and return the top item / look at the top
  item without removing it.
- **Abstract data type (ADT)**: a specification of operations and their meaning, independent of
  any implementation.
- **Interface**: the set of methods a class offers to its users.
- **Adapter pattern**: wrapping an existing class to present a different, usually narrower,
  interface.
- **Exception**: an error signal raised with `raise` and handled with `try ... except`.
- **Delimiter**: a symbol that opens or closes a group, such as `(` or `}`.
- **Tag**: an HTML marker such as `<p>` or `</p>`.
- **Infix / postfix notation**: operator between its operands / after its operands.
- **Operand**: a value an operator works on.
- **Token**: one unit of an expression, such as a number, operator or parenthesis.
- **Precedence**: the rule deciding which operator is applied first.
- **Left-associative**: operators of equal precedence are applied from left to right.

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
