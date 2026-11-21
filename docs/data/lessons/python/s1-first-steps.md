# First steps: running Python, values, names and text

> **Before this lesson:** nothing at all. This is the very first lesson of the Python track, written for someone who has never programmed. You need only this page: every example runs in your browser, so there is nothing to install yet. The next lesson, [Lists and loops](#/lesson/python/py-start-lists-loops), builds on this one.

## In plain words

Programming means writing instructions that a computer follows. Think of a recipe card: "boil the water, add the tea leaves, wait three minutes, pour". A recipe is a list of steps in order, written precisely enough that someone else can follow it without asking you questions. A program is the same thing for a computer, except that the computer is far more literal than any cook. It follows exactly what is written, never what you meant.

This module is for you if you have never written a program. No prior knowledge is assumed: we start from "what is a program?" and move in small steps, and every idea comes with a box you can run and change right here in the page. Please do change things. Programming is learned with your fingers, in the same way swimming is learned in water; reading alone won't do it.

Why this matters for a job: Python is one of the most widely used programming languages in the world, in web development, data analysis, automation, science and machine learning, and it is a common choice for coding interviews because it is short to write and easy to read. Everything later in this track, up to interview-level topics, rests on the basics in this lesson.

By the end of this lesson you will be able to run Python, store information under names, work with text and numbers, leave notes for human readers, and make sense of your first error messages.

## What a program is

A **program** is a list of instructions, written in a text file, that a computer carries out one after another from top to bottom. The computer is extremely fast and extremely literal: it does exactly what the text says, never what you meant. A **programming language** is the set of rules for writing those instructions. **Python** is a popular language because its rules are few and its code reads almost like careful English.

Here is a complete Python program. Press *Run*:

```python-run
print("Hello! This line was produced by a program.")
print(2 + 3)
```

Two instructions, two lines of output. `print` is a **function** — a named action that Python already knows how to perform. The things inside the parentheses are what we hand to the function to work with. Text must be wrapped in quotation marks so Python can tell it apart from instructions; `2 + 3` has no quotes, so Python calculates it first and prints the result.

Try it: change the text, add a third `print` line, replace `+` with `*` (multiply). You cannot break anything.

## Three ways to run Python

On this site, code runs in your browser. On your own computer you would first install Python from python.org (on Windows, tick the option that adds Python to your PATH during installation; PATH is the list of folders where the system looks for programs you type by name) and then use it in one of these ways. A **terminal** (also called a command prompt or shell) is a window where you type commands as text instead of clicking.

| Way | What it looks like | Good for |
|---|---|---|
| **Interactive prompt** (the REPL, short for Read-Eval-Print Loop: it reads a line, evaluates it, prints the result, and loops) | type `python` (or `python3` on macOS/Linux) in a terminal; a `>>>` prompt appears and each line you type runs immediately | quick experiments, checking how something behaves |
| **Script file** | save code in a file ending in `.py`, then run `python my_program.py` in a terminal opened in that folder | real programs you want to keep |
| **Editor with a Run button** | an editor such as VS Code (Visual Studio Code) with its Python extension: write, press Run, see the output in a panel below | everyday work; it also colours your code and flags mistakes as you type |

All three use the same **interpreter**: the program called `python` that reads your text and performs it. When something does not work on your machine, the usual suspects are: the terminal is open in a different folder than the file; the file was not saved; or the command is `python3` rather than `python` on your system. Typing `python --version` tells you whether Python is reachable at all.

A file name such as `tea_orders.py` — lowercase letters, underscores instead of spaces — will save you trouble later.

## Names for values: variables

Programs need to remember things. A **variable** is a name you attach to a value so you can use the value later:

```python-run
shop = "Lantern Tea House"
cups_sold = 42
print(shop)
print(cups_sold)
print(cups_sold + 8)
```

Read `=` as "now refers to", not as "equals" in the mathematical sense. The line `cups_sold = 42` creates the number 42 and ties the name `cups_sold` to it — picture a luggage tag tied to a suitcase. A name can be re-tied to something else at any moment, and the program always uses whatever it is tied to *at that point*:

```python-run
weather = "foggy"
print(weather)
weather = "clear"          # the tag is moved to a new value
print(weather)

visitors = 10
visitors = visitors + 5    # work out the right side first (15), then re-tie the name
print(visitors)
```

The third assignment looks odd as mathematics but makes perfect sense as an instruction: compute `visitors + 5` using the current value, then make `visitors` refer to the result. It is so common that there is a shorthand, `visitors += 5`.

### Rules and habits for names

The rules (Python enforces these):

- Names may contain letters, digits and underscores, and may not start with a digit: `cup_2` is fine, `2nd_cup` is not.
- No spaces. Use underscores: `opening_hour`.
- Upper and lower case are different: `Total` and `total` are two separate names.
- A few dozen words that Python uses itself — `if`, `for`, `class`, `return`, `True` and so on — cannot be names.

The habits (people expect these):

- Write names in lowercase with underscores — `monthly_rainfall`.
- Prefer a name that says what the value means. `price_per_cup` beats `p`; you will thank yourself next week.
- Values that should never change are written in capitals by convention: `MAX_TABLES = 12`. Python will not stop you from changing it; the capitals are a message to readers.
- Avoid reusing names Python already gives meaning to, such as `print`, `list` or `sum`. It is allowed, and it breaks those tools for the rest of your program.

## Text: strings

A piece of text is called a **string** (think of characters strung together). You write one by putting quotation marks around it. Single and double quotes work the same way; having both lets you put one kind inside the other:

```python-run
sign = "Today's special: ginger tea"
reply = 'She said "two cups, please" and sat down.'
print(sign)
print(reply)
print(len(sign))        # len counts the characters, spaces included
```

### Methods: things a string can do

A **method** is an action that belongs to a value. You call it by writing a dot after the value, then the method's name and parentheses. Strings come with many methods. None of them changes the original string; each one hands back a new string.

```python-run
visitor = "  marta OKONKWO "
print(visitor.title())          # First Letter Of Each Word
print(visitor.upper())
print(visitor.lower())
print(visitor.strip())          # remove spaces at both ends
print(visitor.strip().title())  # methods can be chained, left to right
print("[" + visitor + "]")      # the original is unchanged
```

Stray spaces at the ends of text are a classic source of confusion — two strings that look the same on screen but are not equal. `strip()` removes them from both ends, `lstrip()` only from the left, `rstrip()` only from the right. Use them on anything a person has typed.

To keep a change, tie a name to the result:

```python-run
visitor = "  marta OKONKWO "
visitor = visitor.strip().title()
print(visitor)

link = "https://lantern-tea.example/menu.pdf"
print(link.removeprefix("https://"))
print(link.removesuffix(".pdf"))
print(link.replace("menu", "prices"))
print(link.endswith(".pdf"), link.startswith("ftp"))
```

`removeprefix` and `removesuffix` cut a known beginning or ending off a string (and do nothing if it is not there). `replace` swaps every occurrence of one piece of text for another. `startswith` and `endswith` answer a yes/no question; Python writes yes and no as `True` and `False`.

### Putting values inside text: f-strings

Very often you want to build a sentence out of fixed words and changing values. Put the letter `f` directly before the opening quote, and write names (or any calculation) inside curly braces:

```python-run
first = "marta"
last = "okonkwo"
cups = 3
price = 2.5

full_name = f"{first} {last}".title()
print(f"Welcome back, {full_name}!")
print(f"{cups} cups cost {cups * price} coins.")
print(f"Your name has {len(first) + len(last)} letters.")
```

The `f` stands for *format*. Python replaces each `{...}` with the value of what is inside. Forgetting the `f` is a very common slip — then the braces are printed literally. Try deleting an `f` above and running again.

### Invisible characters: new lines and tabs

Inside a string, a backslash followed by a letter stands for a character you cannot type directly. `\n` starts a new line; `\t` jumps to the next tab stop:

```python-run
print("Menu:\n\tGinger tea\n\tMint tea\n\tHot chocolate")
print("one line\nanother line")
```

### Joining and repeating

```python-run
dash_line = "-" * 24             # repeat a string
title = "Lantern" + " " + "Tea"  # glue strings together
print(dash_line)
print(title)
print(dash_line)
```

`+` between two strings joins them; `*` with a number repeats. Mixing a string and a number with `+` is an error, which we will meet in a moment.

## Numbers

Python has two everyday kinds of number:

- **Integers** (`int`): whole numbers such as `7`, `-3`, `1000000`.
- **Floats** (`float`): numbers with a decimal point such as `2.5` or `0.1`.

```python-run
print(7 + 2, 7 - 2, 7 * 2)    # add, subtract, multiply
print(7 / 2)                  # divide: the answer is always a float
print(7 // 2)                 # whole-number division: how many times 2 fits in 7
print(7 % 2)                  # remainder after that division
print(2 ** 5)                 # power: 2 multiplied by itself 5 times
print(2 + 3 * 4, (2 + 3) * 4) # multiplication first, unless parentheses say otherwise
```

Three details worth knowing early:

1. Ordinary division `/` always gives a float, even when it divides evenly: `8 / 2` is `4.0`.
2. The remainder operator `%` is more useful than it looks: `number % 2` is `0` for even numbers and `1` for odd ones.
3. Floats are stored in binary (a number system that uses only the digits 0 and 1), and many decimal fractions such as 0.1 have no exact binary form, so some results carry a tiny error in the far decimal places. This is true in nearly every programming language, not a Python fault. Round when you display.

```python-run
print(0.1 + 0.2)                 # not exactly 0.3
print(round(0.1 + 0.2, 2))       # rounded to 2 decimal places
total = 3 * 2.35
print(f"Total: {total:.2f} coins")   # :.2f inside an f-string also shows 2 decimals

population = 8_250_000           # underscores make big numbers readable; Python ignores them
print(population + 1)

width, height, depth = 4, 3, 2   # several names in one line
print(width * height * depth)
```

### Numbers and text are different things

`"12"` (with quotes) is a string made of two characters; `12` is a number. They behave differently, and Python will not guess which one you meant:

```python-run
print("12" + "3")        # joining text: 123
print(12 + 3)            # arithmetic: 15
print(int("12") + 3)     # int(...) turns suitable text into a whole number
print(str(12) + "3")     # str(...) turns a number into text
print(float("2.5") * 2)  # float(...) turns text into a decimal number
print(type("12"), type(12), type(2.5))   # type(...) tells you what kind of value you have
```

`int`, `float` and `str` are **conversion** functions. You will need them constantly, because everything a user types arrives as text.

## Comments: notes for people

Anything after a `#` on a line is ignored by Python. Such **comments** are for human readers — including you, a month from now.

```python-run
# Work out the bill for a table, including a tip.
bill = 18.40
tip_rate = 0.10            # ten percent; agreed with the staff in March

total = bill + bill * tip_rate
print(f"Please pay {total:.2f}")
```

A helpful comment explains *why* something is done, or summarises what a whole block is for. A comment that merely repeats the code (`# add 1 to x`) is noise. When in doubt, improve the names first; comment what the names cannot say.

## Your first errors

Everyone makes mistakes when typing code — beginners and professionals at about the same rate. The difference is that experienced programmers read the error message calmly. Python's messages are specific and usually point straight at the problem. When a program fails, Python prints a **traceback**: a report of where it was when things went wrong.

Run this program, which contains a misspelled name:

```python-run
import traceback

try:
    greeting = "Good evening"
    print(greting)
except NameError:
    traceback.print_exc()
```

(The `try`/`except` wrapper is only there so the page can show the report; you will learn it properly in the last lesson of this module.) Read a traceback **from the bottom up**:

1. The **last line** names the kind of error and gives a description: `NameError: name 'greting' is not defined`. Recent Python versions even add *Did you mean: 'greeting'?*
2. The lines above show **where**: the file, the line number, and the offending line itself.

A `NameError` means Python met a name that has not been given a value. Nearly always it is a spelling slip, a different upper/lower case, or using a name before the line that creates it.

Here are the four errors you will meet most in your first week, each caught so you can see its message:

```python-run
experiments = {
    "name not defined":      "print(totl)",
    "mixing text and number": "print('Cups: ' + 4)",
    "unclosed quote":         "print('hello)",
    "text that is not a number": "int('four')",
}
for label, code in experiments.items():
    try:
        exec(code)
    except Exception as error:
        print(f"{label:<28} -> {type(error).__name__}: {error}")
```

You do not need to understand every line of this demo yet. Each experiment is a small piece of Python code stored as text; `exec(code)` runs that text as if it were a program, and the `try`/`except` catches the error so that the next experiment can still run. Each output line shows a label, the error's type and its message.

| Error | What it means | Usual fix |
|---|---|---|
| `NameError` | a name is unknown | check spelling and case; define it earlier |
| `TypeError` | an operation was applied to the wrong kind of value | convert with `str()`, `int()` or `float()`, or use an f-string |
| `SyntaxError` | the text breaks Python's grammar, so nothing ran at all | look at the marked line *and the one before it* for a missing quote, bracket or colon |
| `ValueError` | right kind of value, unacceptable content | check what the value really contains — `print(repr(value))` shows hidden spaces |

A `SyntaxError` is special: Python reads the whole file before running anything, so with a syntax error not even the first line executes. The message shows a little arrow where Python became confused — the real cause is often slightly earlier, such as a bracket opened on the previous line and never closed.

### A routine for when something goes wrong

1. Read the last line of the traceback. What kind of error? What does it say?
2. Go to the line number it mentions. Look at that line and the one above.
3. Still unclear? Add `print(...)` lines immediately before it to display the values involved, and their `type(...)`.
4. Change **one** thing, run again, and observe. Random multiple changes make things worse.
5. Still stuck? Copy the last line of the error into a search engine — thousands of people have met the same message.

## Worked example: a receipt

Let's combine everything into one small program. Read it top to bottom and predict the output before running it.

```python-run
# --- details of the order ---
customer = "  dana whitfield "
item = "jasmine tea"
unit_price = 3.2
quantity = 4
DISCOUNT_RATE = 0.15          # regular customers get 15% off

# --- tidy up and calculate ---
customer = customer.strip().title()
subtotal = unit_price * quantity
discount = subtotal * DISCOUNT_RATE
total = subtotal - discount

# --- print the receipt ---
line = "=" * 30
print(line)
print(f"Customer:\t{customer}")
print(f"Item:\t\t{item.title()} x {quantity}")
print(f"Subtotal:\t{subtotal:.2f}")
print(f"Discount:\t-{discount:.2f}")
print(f"TOTAL:\t\t{total:.2f}")
print(line)
print(f"Thank you, {customer.split()[0]}!")
```

Notice the shape: first the facts, then the calculations, then the output, with blank lines and comments separating the stages. Most small programs have this input → process → output structure. (`split()` cuts a string into its words; `[0]` takes the first one. Lists are the subject of the next lesson.)

Experiments to try: change the quantity; make the discount zero; add a second item with its own price and quantity and include it in the totals; deliberately misspell `subtotal` in one place and read the traceback.

> [!TIP]
> When you are unsure what a line does, do not guess — test it. Type a tiny experiment into a run box or the interactive prompt, look at the result, and adjust. The feedback loop of *change one thing, run, observe* is the single most important habit in programming, and the interpreter never gets tired of answering.

## Practise

Short exercises to do in any run box above (or your own editor):

1. Tie your town's name to a variable and print it in upper case, lower case and title case.
2. Store a temperature in Celsius and print it in Fahrenheit (multiply by 9, divide by 5, add 32) inside a full sentence, with one decimal place.
3. A string holds `"  LEAF-and-bean.txt  "`. Produce `leaf-and-bean` using only methods from this lesson.
4. How many seconds are there in a week? Let Python work it out, with a constant for each factor.
5. Create each of the four errors from the table on purpose, read the message, then repair the line.

## Summary

- A program is text that the Python interpreter carries out line by line. You can run code at the interactive prompt, from a `.py` file, or from an editor.
- A variable is a name tied to a value by `=`; it can be re-tied later. Choose lowercase, descriptive names.
- Strings hold text. Methods such as `title`, `upper`, `lower`, `strip`, `replace`, `removeprefix` return new strings; f-strings insert values into text.
- Integers and floats support `+ - * / // % **`; `/` always produces a float. Convert between text and numbers with `int`, `float` and `str`.
- Comments begin with `#` and explain the *why*.
- Read tracebacks from the bottom: error type, message, then the line. `NameError`, `TypeError`, `SyntaxError` and `ValueError` cover most early mistakes.

## Glossary

- **Program** - a list of instructions, in a text file, that a computer carries out from top to bottom.
- **Programming language** - the set of rules for writing those instructions; Python is one.
- **Interpreter** - the program called `python` that reads your code and carries it out.
- **Terminal** - a window where you type commands as text.
- **REPL** - Read-Eval-Print Loop, the interactive `>>>` prompt that runs each line as you type it.
- **Script** - a program saved in a `.py` file.
- **Function** - a named action, such as `print` or `len`, that you call with parentheses.
- **Variable** - a name tied to a value with `=`, which can be re-tied later.
- **Assignment** - the `=` statement that ties a name to a value.
- **String** - a piece of text, written inside quotation marks.
- **Method** - an action that belongs to a value, called with a dot: `name.upper()`.
- **f-string** - a string with `f` before the quote, whose `{...}` parts are replaced by values.
- **Escape sequence** - a backslash code inside a string, such as `\n` (new line) or `\t` (tab).
- **Integer (`int`) / float** - a whole number / a number with a decimal point.
- **Conversion** - turning a value into another type with `int()`, `float()` or `str()`.
- **Comment** - text after `#` that Python ignores; a note for human readers.
- **Traceback** - the report Python prints when a program fails, showing where and why.
- **NameError, TypeError, SyntaxError, ValueError** - an unknown name; the wrong kind of value; text that breaks Python's grammar; the right kind of value with unacceptable content.

```quiz
[
  {"q": "What does the line `score = score + 1` do?", "options": ["It is an error, because nothing equals itself plus one", "It works out score + 1 and makes the name score refer to the result", "It compares score with score + 1", "It creates a second variable"], "answer": 1,
   "explain": "`=` is assignment: the right-hand side is evaluated first using the current value, then the name is re-tied to the result."},
  {"q": "Which of these is a valid, well-styled variable name?", "options": ["2nd_place", "second place", "second_place", "class"], "answer": 2,
   "explain": "Names cannot start with a digit, contain spaces, or be reserved words such as class. Lowercase with underscores is the convention."},
  {"q": "What does `print(\"7\" + \"2\")` display?", "options": ["9", "72", "7 2", "An error"], "answer": 1,
   "explain": "Both values are strings, so + joins them. Use int(\"7\") + int(\"2\") for arithmetic."},
  {"q": "After `city = \" oslo \"` and `city.strip().title()` on its own line, what does `print(city)` show?", "options": ["Oslo", "oslo", " oslo  (unchanged, with its spaces)", "OSLO"], "answer": 2,
   "explain": "String methods return a new string and never alter the original. To keep the result you must assign it: city = city.strip().title()."},
  {"q": "What is the result of `9 / 3` in Python?", "options": ["3", "3.0", "3.3", "0"], "answer": 1,
   "explain": "The / operator always produces a float. Use // when you want a whole-number result."},
  {"q": "You see `NameError: name 'totl' is not defined`. What is the most likely cause?", "options": ["Python is not installed properly", "A misspelled variable name, or a name used before it was given a value", "A missing quotation mark", "Dividing by zero"], "answer": 1,
   "explain": "NameError means Python met a name it has no value for: usually a typo, a case difference, or use before assignment."},
  {"q": "In which direction should you read a traceback first?", "options": ["Top line first", "Bottom line first: it names the error type and message", "Only the middle matters", "Tracebacks are not meant to be read"], "answer": 1,
   "explain": "The final line states what went wrong; the lines above it show where."},
  {"q": "What is missing in `print(\"You owe {amount} coins\")` if you want the value of amount to appear?", "options": ["Nothing", "The letter f before the opening quote", "A plus sign", "Square brackets"], "answer": 1,
   "explain": "Only f-strings replace {name} with the value. Without the f the braces are printed as ordinary characters."}
]
```

> **Source:** Matthes, *Python Crash Course* (3rd ed.), ch. 1–2 (getting started; variables and simple data types) — topics only, examples and wording are original; Python docs, *Tutorial* ch. 2–3 "Using the Python Interpreter" and "An Informal Introduction to Python".
