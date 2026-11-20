# "Review this code": a method for code-review questions

> **Before this lesson:** you should be able to read short Python functions. [Slow or flaky test suites, and designing code review rules](#/lesson/thinking/flaky-tests-review-rules) covers how teams organise review; this lesson is about what *you* say when a snippet is put in front of you.

## In plain words

Before a newspaper prints an article, an editor reads it. The editor is not there to rewrite it in their own style or to show off. They check, roughly in this order: is it true? is anything missing? could a reader misunderstand it? could it get the paper sued? — and only then: is this sentence clumsy? A good editor also says what is good, and explains each change so that the writer improves.

**Code review** is that editing, for programs: one engineer reads another's change before it joins the shared codebase. In an interview you are handed twenty or thirty lines and asked *"what do you think of this?"* The exercise is popular because it is close to daily work — most engineers read far more code than they write — and because it shows, in ten minutes, whether you notice what matters, can tell a serious problem from a matter of taste, and can say it in a way a colleague would accept.

The trap is to start at line one and comment on everything in the order you see it. That produces "this variable name could be better" before "this loses customers' money". The fix is a method with a fixed order of priorities.

## The method: six passes, most important first

| Pass | Question | Typical findings |
|---|---|---|
| 1. **Purpose** | What is this meant to do? Do I understand it? | Unclear intent; missing description |
| 2. **Correctness** | Does it do that, for *every* input? | Wrong results, edge cases, crashes |
| 3. **Safety** | Could it harm data, security or other users? | Injection, leaked secrets, missing permission checks, races |
| 4. **Robustness** | What happens when something outside fails? | Unhandled errors, no timeout, half-finished work |
| 5. **Readability and design** | Could a colleague change this safely in six months? | Confusing names, duplication, functions doing five things |
| 6. **Tests and performance** | How do we know it works, and will it cope at scale? | No tests; a query inside a loop |

Then **prioritise** what you found and **phrase** it well. The list of what reviewers should look at in Google's public engineering-practices guide covers the same ground — design, functionality, complexity, tests, naming, comments, style, documentation — and adds a point worth remembering: say what is *good* as well.

A one-line reminder for the order: **does it work, is it safe, will it survive, can I read it, can we trust it.**

### Pass 2 in detail: hunting edge cases

Most bugs hide where inputs are unusual. Run this list against every function — it is the error-guessing list from the testing lessons, pointed at code.

- **Empty**: empty list, empty string, zero, `None`.
- **One**: a single element.
- **Boundaries**: first and last index, exactly at a limit, one past it.
- **Duplicates** and **negative numbers**.
- **Very large** input.
- **Wrong type or format**: text where a number was expected.
- **Twice**: what if this is called again with the same data?
- **At the same time**: what if two callers run it concurrently?

## A first example, step by step

Here is a small function of the kind used to open a review interview. Read it and note your thoughts before continuing.

```python
def avg(l):
    t = 0
    for i in range(len(l)):
        t = t + l[i]
    return t / len(l)
```

**Pass 1 — purpose.** It returns the average of a list of numbers. Clear enough, though the names say nothing.

**Pass 2 — correctness.** Try the edge cases. Empty list: `len(l)` is 0, so the last line divides by zero and the program crashes. That is a real bug. One element: fine. Negative numbers: fine. A list containing a string: crashes with a type error — acceptable if the function is only ever given numbers, worth a question.

**Pass 3 — safety.** Nothing here touches data or users.

**Pass 4 — robustness.** Covered by the empty-list case.

**Pass 5 — readability.** `l` is a poor name — it looks like the digit 1 — and `t` and `i` carry no meaning. The loop walks indexes where Python can sum directly.

**Pass 6 — tests.** None shown.

Now **prioritise**. One bug that crashes the program; a handful of style points. And decide what the *right behaviour* for an empty list is — return 0? return nothing? raise a clear error? That is a question for the author, because it depends on who calls it: an "average order value" of 0 for a day with no orders may mislead a report.

A rewritten version, with the decision made explicit:

```python-run
def average(values):
    """Return the mean of a non-empty list of numbers."""
    if not values:                         # empty list: fail with a clear message
        raise ValueError("average() needs at least one value")
    return sum(values) / len(values)

print(average([2, 4, 9]))
try:
    average([])
except ValueError as e:
    print("refused:", e)
```

The `if not values` line catches the empty case and stops with an explanation, instead of the confusing "division by zero" three calls away from the cause. `sum(values)` replaces the manual loop. The printed output shows the normal result and the refusal.

What you would **say**, in order: "It works for normal lists. The one thing I'd block on is the empty list, which crashes with a division by zero — what should happen there? After that, smaller suggestions: clearer names, and `sum()` would replace the loop. And I'd add tests for empty, one element and negatives."

## A realistic example

This is closer to what a mid-level interview uses: a function from a web application. Take ten minutes to review it with the six passes before opening the answer.

```python
def transfer(db, from_id, to_id, amount):
    # move money
    q = "SELECT balance FROM accounts WHERE id = " + from_id
    bal = db.execute(q).fetchone()[0]
    if bal > amount:
        db.execute("UPDATE accounts SET balance = balance - " + str(amount) + " WHERE id = " + from_id)
        db.execute("UPDATE accounts SET balance = balance + " + str(amount) + " WHERE id = " + to_id)
        print("transfer ok " + from_id + " " + to_id + " " + str(amount))
        return True
    else:
        return False
```

<details><summary>Model review</summary>

**Purpose.** Moves `amount` from one account to another if the sender has enough. Understood.

**Findings, most serious first.**

**1. SQL injection — blocking.** The query text is built by gluing the account id into a string. If `from_id` comes from a user and contains `1 OR 1=1` or something worse, the user's text becomes part of the command and the database will run it. This is one of the oldest and most damaging security flaws. Fix: **parameterised queries** — the command and the values are sent separately, so a value can never be treated as a command: `db.execute("SELECT balance FROM accounts WHERE id = ?", (from_id,))`.

**2. Not atomic — blocking.** The two updates are separate. If the program crashes, or the second update fails, after the first has run, money has left one account and arrived nowhere. Fix: wrap both in one **transaction** — a group of changes that either all happen or none do.

**3. Race condition — blocking.** The balance is read, then later reduced. Two transfers from the same account at the same moment can both read 100, both decide 80 is affordable, and both subtract: the balance ends at −60. Fix: do the check and the subtraction in one statement — `UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?` — and see whether a row was changed; or lock the row for the duration of the transaction.

**4. Wrong comparison — bug.** `bal > amount` refuses a transfer of the *entire* balance. It should be `>=`. A classic boundary slip.

**5. Missing validation — bug.** A negative `amount` passes the check (any balance exceeds a negative number) and then *moves money the other way*: a way to take from another account. Zero, and `from_id == to_id`, also deserve a decision. An unknown `from_id` makes `fetchone()` return nothing and the `[0]` crash; an unknown `to_id` silently destroys money, since the second update changes no rows.

**6. Authorisation — question.** Nothing here checks that the caller owns `from_id`. It may be checked before this function is called; I would ask, because if not, this is the most serious problem of all.

**7. Money type — question.** Are amounts whole cents or fractional numbers? Fractions stored as floating-point values accumulate rounding errors; money should be integer minor units or a decimal type.

**8. Logging — improvement.** `print` is not a log: it has no level, no timestamp, and goes nowhere useful in production. Use the logging system; and for transfers there should be a durable audit record in the database, written in the same transaction.

**9. Return value — improvement.** `False` covers "insufficient funds" only by accident of the structure; other failures crash. Callers cannot tell why a transfer was refused. Raise specific errors or return a result that says which.

**10. Readability — minor.** The comment "move money" adds nothing; `q` and `bal` could be spelled out; the `else` after a `return` is unnecessary.

**11. Tests — missing.** I would want: normal transfer; exact balance; insufficient funds; negative and zero amounts; unknown accounts; same account; and a concurrency test with two simultaneous transfers.

**What is good.** It checks the balance before debiting, which shows the right intent, and the function is short and does one thing.

**How I would summarise it to the author.** "The idea is right and it's nicely small. Four things need to change before this is safe for real money: parameterised queries, a transaction around both updates, making the balance check and debit one atomic step, and validating the amount — a negative one currently reverses the transfer. I also have a question about where ownership of `from_id` is checked. The rest — logging, names — are suggestions. Happy to pair on the transaction part if useful."

</details>

A corrected sketch, to show the shape (using SQLite, a small database built into Python, so that it runs):

```python-run
import sqlite3

class TransferError(Exception):
    pass

def transfer(db, from_id, to_id, amount_cents):
    if amount_cents <= 0:
        raise TransferError("amount must be positive")
    if from_id == to_id:
        raise TransferError("accounts must differ")
    with db:                                          # one transaction: commit on success, roll back on error
        debited = db.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?",
            (amount_cents, from_id, amount_cents)).rowcount      # values sent separately: no injection
        if debited != 1:
            raise TransferError("insufficient funds or unknown sender")
        credited = db.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount_cents, to_id)).rowcount
        if credited != 1:
            raise TransferError("unknown recipient")  # raising here undoes the debit too

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER NOT NULL)")
db.executemany("INSERT INTO accounts VALUES (?, ?)", [(1, 10_000), (2, 500)])
db.commit()

transfer(db, 1, 2, 10_000)                            # the whole balance: allowed
print(db.execute("SELECT id, balance FROM accounts").fetchall())
for bad in [(1, 2, 1), (2, 1, -50), (2, 99, 100)]:
    try:
        transfer(db, *bad)
    except TransferError as e:
        print(bad, "->", e)
print(db.execute("SELECT id, balance FROM accounts").fetchall())
```

Things to notice. The `?` marks are placeholders; the values travel beside the command. `with db:` starts a transaction and undoes everything inside it if an error is raised — so the third bad case, which debits account 2 and then finds no recipient 99, leaves account 2 untouched, as the final line shows. The check and the debit are one statement, so no other transfer can slip between them.

## How to phrase review comments

Finding problems is half the task. The other half is saying them so that the author listens. Interviewers often ask directly: *"how would you give this feedback to a colleague?"*

| Principle | Instead of | Say |
|---|---|---|
| Comment on the code, not the person | "You forgot to handle empty lists." | "This crashes on an empty list — what should it return there?" |
| Explain why | "Use parameters." | "Building the query by concatenation lets input be run as SQL; parameters prevent that." |
| Ask when unsure | "This is wrong." | "Is ownership of the account checked before this is called?" |
| Mark severity | (twenty comments of equal weight) | "Blocking: …", "Suggestion: …", "Nit: …" |
| Offer a way forward | "Rewrite this." | "One option: a single UPDATE with the balance condition. Happy to pair." |
| Acknowledge what is good | (silence) | "Nice that this is one small function." |

"**Nit**" is short for nit-pick: a minor preference the author may ignore. Labelling small points this way — a convention recommended in Google's review guide — tells the author what truly needs to change.

Also know the **standard for approval**: a change does not need to be perfect; it needs to leave the codebase better than it found it, with the blocking problems fixed. Holding a change hostage over taste slows everyone and teaches people to avoid review.

> [!INTERVIEW]
> Structure your spoken review as: **one sentence on what the code does → the blocking issues, with why → questions → suggestions → what is good.** If you find a security problem or a data-loss problem, lead with it. Candidates who spend the first three minutes on naming rarely recover the impression.

## A checklist of common findings

Keep this in mind as a scanning aid; each line is a pattern worth recognising on sight.

| Category | Look for |
|---|---|
| **Correctness** | Off-by-one in loops and ranges; `<` versus `<=`; empty input; division; mutable default arguments; modifying a list while looping over it |
| **Security** | Query or shell command built from strings; user input shown without escaping; passwords, keys or tokens in the code or logs; missing permission check; file paths from user input |
| **Errors** | An `except` that swallows everything silently; no timeout on a network call; resources opened and never closed; a failure halfway leaving things inconsistent |
| **Concurrency** | Read-then-write without protection; shared variables changed by several threads; "check then act" |
| **Performance** | A database query or network call inside a loop (the "N+1" problem: one query to get a list, then one more per item); reading a whole large file into memory; nested loops over large collections |
| **Design** | A function doing several unrelated things; copy-pasted blocks; unexplained "magic" numbers; deep nesting |
| **Tests** | No tests for the change; tests that cannot fail; only the happy path |

## Practice

**Prompt:** *"Review this function."* Use the six passes, then compare.

```python
def get_user_orders(db, user_ids):
    result = []
    for uid in user_ids:
        user = db.query("SELECT * FROM users WHERE id = %s" % uid)
        orders = db.query("SELECT * FROM orders WHERE user_id = %s" % uid)
        try:
            result.append({"name": user[0]["name"], "orders": orders, "password": user[0]["password"]})
        except:
            pass
    return result
```

<details><summary>Model review</summary>

**Purpose.** For each user id, return the user's name and orders.

**Blocking.**

1. **SQL injection.** `%` formatting pastes the id into the query text. Use parameters.
2. **The password is returned.** The result includes each user's password field. Whatever this is used for, sensitive fields must not travel in a general-purpose result; select only the columns needed. (And if that column holds readable passwords instead of salted hashes, that is a larger problem to raise.)
3. **The bare `except: pass`.** Any error — a missing user, a typo, a database failure — is silently discarded, and the caller receives a shorter list with no sign that anything went wrong. Catch the specific expected case (user not found), decide what it means, and let everything else surface.

**Performance.**

4. **Queries in a loop.** Two queries per user: 1,000 users means 2,000 round trips. Fetch all users in one query with `WHERE id IN (…)` and all their orders in a second, then group in memory.

**Questions.**

5. May the caller see every one of these users' orders? Where is that checked?
6. Can `user_ids` be very large or contain duplicates? Is a limit or pagination needed?
7. What should happen for an id that does not exist — skip, or report?

**Suggestions.** `SELECT *` fetches every column and breaks when the table changes; name the columns. The function name says "orders" but it returns users with orders. Add tests: empty list, unknown id, user with no orders, duplicates.

**Good.** The returned structure is simple and the function has a single job.

**Summary to the author.** "Three things to fix first: the queries need parameters, the password must not be in the result, and the silent `except` hides real failures. Then I'd batch the queries. A couple of questions about permissions and list size."

</details>

## Summary

- Review in a fixed order of importance: purpose, correctness, safety, robustness, readability, tests and performance.
- Hunt edge cases with a list: empty, one, boundaries, duplicates, negative, huge, wrong type, twice, concurrent.
- Recognise the high-value patterns on sight: queries built from strings, missing transactions, read-then-write races, swallowed errors, secrets in output, queries inside loops.
- Prioritise: lead with what could lose data, money or security; label minor points as nits.
- Phrase comments about the code, with reasons and questions, and note what is good.
- Approve when the change is a net improvement with blocking issues fixed, not when it is perfect.

## Glossary

| Term | Meaning |
|---|---|
| Code review | Reading a colleague's change before it is merged |
| Edge case | An unusual input at the extremes of what is allowed |
| SQL injection | An attack in which user input is executed as part of a database command |
| Parameterised query | A query whose values are supplied separately from its text |
| Transaction | A group of changes that all succeed or all fail |
| Race condition | A bug whose appearance depends on the timing of concurrent actions |
| Validation | Checking that input is acceptable before using it |
| Authorisation | Checking that the caller may act on this particular item |
| Swallowed exception | An error caught and ignored without trace |
| N+1 queries | One query for a list followed by one more for each item |
| Magic number | An unexplained literal value in code |
| Nit | A minor, optional review comment |
| Blocking comment | A problem that must be fixed before the change is accepted |

## Check yourself

```quiz
[
  {"q": "You are handed a snippet with a security flaw and several poorly named variables. What do you mention first?",
   "options": ["The variable names, since they appear first", "The security flaw, because it can cause real harm", "The indentation", "Nothing until asked"],
   "answer": 1,
   "explain": "Lead with what could damage data, money or security; taste comes last."},
  {"q": "What is wrong with db.execute(\"SELECT * FROM users WHERE name = '\" + name + \"'\")?",
   "options": ["It is too short", "User-supplied text becomes part of the command, allowing SQL injection", "SELECT cannot be used with WHERE", "Nothing"],
   "answer": 1,
   "explain": "Concatenation lets input change the meaning of the query; parameterised queries keep data separate from the command."},
  {"q": "A function reads a balance, checks it, and then subtracts in a later statement. Which problem does this invite?",
   "options": ["A syntax error", "A race condition: two concurrent calls can both pass the check", "Slow typing", "A memory leak"],
   "answer": 1,
   "explain": "Check-then-act without atomicity allows another operation to change the value in between."},
  {"q": "What is the harm of 'except: pass'?",
   "options": ["It is slow", "Every error is silently discarded, hiding real failures from callers and operators", "It uses too much memory", "It prevents imports"],
   "answer": 1,
   "explain": "Catch specific expected errors and handle them; let unexpected ones surface."},
  {"q": "A loop over 500 customers runs one database query per customer. What is this pattern and its fix?",
   "options": ["Recursion; add a base case", "N+1 queries; fetch the needed rows in one batched query", "A deadlock; add a lock", "A typo; rename the variable"],
   "answer": 1,
   "explain": "Hundreds of round trips are replaced by one or two queries followed by grouping in memory."},
  {"q": "Which comment is phrased best?",
   "options": ["You always forget edge cases.", "This crashes when the list is empty — what should it return in that case?", "Wrong.", "I would never write it like this."],
   "answer": 1,
   "explain": "It addresses the code, states the observable problem and asks about the intended behaviour."},
  {"q": "When should a reviewer approve a change?",
   "options": ["Only when it is perfect", "When it improves the codebase overall and blocking issues are resolved", "When the author is senior", "Immediately, to be friendly"],
   "answer": 1,
   "explain": "Perfection is not the bar; net improvement is, with optional points marked as such."}
]
```

> **Source:** Google Engineering Practices, "What to look for in a code review" and "The standard of code review" (https://google.github.io/eng-practices/review/reviewer/looking-for.html, https://google.github.io/eng-practices/review/reviewer/standard.html); *Software Engineering at Google*, ch. 9 "Code Review" (https://abseil.io/resources/swe-book/html/ch09.html); OWASP, "SQL Injection Prevention Cheat Sheet" (https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html). Snippets, reviews and wording are original.
