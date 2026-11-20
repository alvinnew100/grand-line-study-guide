"""Python Mastery problems: the "Start here" on-ramp (py-start-*) and the Projects module (py-proj-*)."""
import random


def _csv_rain(seed, n):
    rnd = random.Random(seed)
    cities = ["Porto", "Faro", "Braga", "Evora"]
    lines = ["date,city,rain_mm"]
    for i in range(n):
        r = rnd.random()
        day = f"2026-{rnd.randrange(1, 13):02d}-{rnd.randrange(1, 29):02d}"
        city = rnd.choice(cities)
        if r < 0.08:
            lines.append(f"{day},{city},n/a")
        elif r < 0.12:
            lines.append(f"{day},{city}")
        elif r < 0.15:
            lines.append("")
        else:
            lines.append(f"{day}, {city} ,{rnd.randrange(0, 400) / 10}")
    return "\n".join(lines) + "\n"


_ROUTES = [
    ["", "home"],
    ["plants/", "plant_list"],
    ["plants/new/", "plant_create"],
    ["plants/<int:plant_id>/", "plant_detail"],
    ["plants/<int:plant_id>/water/", "water"],
    ["rooms/<str:room>/", "room_detail"],
    ["rooms/<str:room>/plants/<int:plant_id>/", "room_plant"],
    ["plants/<str:slug>/", "plant_by_slug"],
]

_PAYLOAD = {
    "total_count": 5,
    "items": [
        {"id": "PRT-01", "name": "Foz Lighthouse", "latest": {"height_m": 2.31}, "sensors": ["tide", "wind"]},
        {"id": "PRT-02", "name": "Ribeira Quay", "latest": {"height_m": 1.87}, "sensors": ["tide"]},
        {"id": "PRT-03", "name": "Afurada Pier", "latest": None, "sensors": []},
        {"id": "PRT-04", "name": "Cantareira", "sensors": ["tide"]},
        {"name": "no id here", "latest": {"height_m": 9.99}},
        {"id": "PRT-06", "name": "Douro Mouth", "latest": {"height_m": 2.31}},
        {"id": "PRT-07", "latest": {"height_m": 0.4}},
        {"id": "PRT-08", "name": "Leixoes", "latest": {"height_m": 3.05, "taken_at": "2026-07-04"}},
    ],
}


PROBLEMS = [
# ===================================================================================== START HERE
dict(
    id="py-start-greeting",
    title="Tidy Greeting",
    difficulty="Easy",
    pattern="Strings",
    entry="make_greeting",
    description=r"""
People type their names carelessly. Write `make_greeting(name)` that returns a greeting with the
name tidied up:

- remove spaces from both ends of `name`;
- write it in title case (each word starting with a capital letter);
- return `"Hello, <Name>!"`.

If nothing is left after removing the spaces, return `"Hello, stranger!"`.

**Example:** `"  marta OKONKWO "` → `"Hello, Marta Okonkwo!"`

**Example:** `"   "` → `"Hello, stranger!"`
""",
    starter='''def make_greeting(name: str) -> str:
    pass
''',
    solution='''def make_greeting(name):
    tidy = name.strip().title()
    if not tidy:
        return "Hello, stranger!"
    return f"Hello, {tidy}!"
''',
    tests=[["  marta OKONKWO "], ["   "], ["dana"], [""], ["LI WEI"], ["  o'neill  "], ["anna-maria de la cruz"],
           ["\tsam\n"], ["x"], ["  two  spaces inside  "]],
    examples=2,
    wrong_solutions=['''def make_greeting(name):
    return f"Hello, {name.title()}!"
''', '''def make_greeting(name):
    tidy = name.strip().capitalize()
    return f"Hello, {tidy}!" if tidy else "Hello, stranger!"
'''],
    guide=dict(
        prereqs="Lesson *First steps*: string methods and f-strings.",
        intuition="Clean the text first, decide whether anything is left, then build the sentence.",
        hints=["`strip()` removes spaces (and tabs/newlines) at both ends.",
               "`title()` capitalises each word; chain it: `name.strip().title()`.",
               "An empty string counts as false: `if not tidy:`."],
        brute_force="Loop over the characters and remove leading/trailing spaces by hand — possible, but the methods already do it.",
        approach="1. `tidy = name.strip().title()`  2. if `tidy` is empty return the stranger greeting  3. otherwise return `f\"Hello, {tidy}!\"`.",
        complexity="O(n) in the length of the name.",
        pitfalls="- String methods return new strings; assign the result.\n- `capitalize()` only capitalises the first letter of the whole string.\n- Forgetting the `f` prints the braces literally.",
        follow_up="Greet with only the first name: `tidy.split()[0]`.",
    ),
),
dict(
    id="py-start-weather-advice",
    title="What Should I Wear?",
    difficulty="Easy",
    pattern="if / elif / else",
    entry="advice",
    description=r"""
Write `advice(temperature, raining)` that returns a string telling someone what to wear.

Based on `temperature` (a number, in °C):

| temperature | text |
|---|---|
| below 5 | `"coat and gloves"` |
| from 5 up to (not including) 15 | `"jacket"` |
| from 15 up to (not including) 25 | `"sweater"` |
| 25 or more | `"t-shirt"` |

If `raining` is `True`, add `" and an umbrella"` to the end.

**Example:** `advice(17, False)` → `"sweater"`

**Example:** `advice(3, True)` → `"coat and gloves and an umbrella"`
""",
    starter='''def advice(temperature: float, raining: bool) -> str:
    pass
''',
    solution='''def advice(temperature, raining):
    if temperature < 5:
        text = "coat and gloves"
    elif temperature < 15:
        text = "jacket"
    elif temperature < 25:
        text = "sweater"
    else:
        text = "t-shirt"
    if raining:
        text += " and an umbrella"
    return text
''',
    tests=[[17, False], [3, True], [5, False], [15, True], [25, False], [24.9, False], [4.99, True],
           [-20, False], [40, True], [14.5, False], [0, False]],
    examples=2,
    wrong_solutions=['''def advice(temperature, raining):
    if temperature <= 5:
        text = "coat and gloves"
    elif temperature <= 15:
        text = "jacket"
    elif temperature <= 25:
        text = "sweater"
    else:
        text = "t-shirt"
    if raining:
        text += " and an umbrella"
    return text
''', '''def advice(temperature, raining):
    if temperature < 25:
        text = "sweater"
    elif temperature < 15:
        text = "jacket"
    elif temperature < 5:
        text = "coat and gloves"
    else:
        text = "t-shirt"
    return text + (" and an umbrella" if raining else "")
'''],
    guide=dict(
        prereqs="Lesson *Decisions and dictionaries*: `if` / `elif` / `else`.",
        intuition="Test the ranges from coldest to warmest. Because the first true branch wins, each `elif` already knows the earlier tests failed, so one comparison per line is enough.",
        hints=["Start with `if temperature < 5:`.", "The umbrella is an *independent* question — use a separate `if` after the chain.",
               "Check the boundary values 5, 15 and 25 by hand."],
        brute_force="Four separate `if`s with both bounds written out (`5 <= t < 15`) also work; the chain is shorter.",
        approach="An `if/elif/else` chain picks the base text; a separate `if raining:` appends the umbrella; return the text.",
        complexity="O(1).",
        pitfalls="- `<=` instead of `<` puts exactly 5, 15 and 25 in the wrong group.\n- Testing the widest range first swallows the narrower ones.\n- Putting the umbrella inside the chain as an `elif` means it is skipped.",
        follow_up="Add wind: above 40 km/h append \" and a windbreaker\".",
    ),
),
dict(
    id="py-start-list-summary",
    title="Summarise a List of Numbers",
    difficulty="Easy",
    pattern="Lists",
    entry="summarise",
    compare="float",
    description=r"""
Write `summarise(numbers)` that takes a list of numbers and returns a list of four values:
`[smallest, largest, total, average]`.

For an empty list return `[None, None, 0, None]` (there is no smallest, largest or average of nothing).

**Example:** `[4, 8, 15, 16, 23, 42]` → `[4, 42, 108, 18.0]`

**Example:** `[]` → `[None, None, 0, None]`
""",
    starter='''def summarise(numbers: list) -> list:
    pass
''',
    solution='''def summarise(numbers):
    if not numbers:
        return [None, None, 0, None]
    total = sum(numbers)
    return [min(numbers), max(numbers), total, total / len(numbers)]
''',
    tests=[[[4, 8, 15, 16, 23, 42]], [[]], [[7]], [[-3, -1, -2]], [[2.5, 3.5]], [[0, 0, 0]], [[10, -10]],
           [list(range(1, 101))], [[1, 2]], [[5, 5, 5, 6]]],
    examples=2,
    wrong_solutions=['''def summarise(numbers):
    total = sum(numbers)
    return [min(numbers), max(numbers), total, total / len(numbers)]
''', '''def summarise(numbers):
    if not numbers:
        return [None, None, 0, None]
    return [numbers[0], numbers[-1], sum(numbers), sum(numbers) / len(numbers)]
'''],
    guide=dict(
        prereqs="Lesson *Lists and loops*: `min`, `max`, `sum`, `len`.",
        intuition="Python's built-in functions do the summarising; your job is the special case of the empty list, where `min`, `max` and the division would all fail.",
        hints=["`if not numbers:` is true for an empty list.", "`sum(numbers) / len(numbers)` is the average.", "Return the four values inside square brackets."],
        brute_force="A loop that keeps a running smallest, largest and total — good practice, same result.",
        approach="Guard the empty case first with an early `return`; otherwise compute with the built-ins.",
        complexity="O(n).",
        pitfalls="- `min([])` raises `ValueError`; dividing by `len([])` raises `ZeroDivisionError`.\n- The first/last items are not the smallest/largest unless the list is sorted.",
        follow_up="Also return the median (sort a copy and take the middle).",
    ),
),
dict(
    id="py-start-count-vowels",
    title="Count the Vowels",
    difficulty="Easy",
    pattern="Loops & Strings",
    entry="count_vowels",
    description=r"""
Write `count_vowels(text)` that returns how many letters in `text` are vowels — `a`, `e`, `i`, `o`
or `u`, in either upper or lower case. Every occurrence counts.

**Example:** `"Lantern Tea House"` → `7`

**Example:** `"rhythm"` → `0`
""",
    starter='''def count_vowels(text: str) -> int:
    pass
''',
    solution='''def count_vowels(text):
    count = 0
    for letter in text.lower():
        if letter in "aeiou":
            count += 1
    return count
''',
    tests=[["Lantern Tea House"], ["rhythm"], [""], ["AEIOU"], ["aeiouAEIOU"], ["Python 3.12!"], ["queueing"],
           ["y"], ["The quick brown fox jumps over the lazy dog"], ["a" * 500 + "b" * 500]],
    examples=2,
    wrong_solutions=['''def count_vowels(text):
    count = 0
    for letter in text:
        if letter in "aeiou":
            count += 1
    return count
''', '''def count_vowels(text):
    return len(set(text.lower()) & set("aeiou"))
'''],
    guide=dict(
        prereqs="Lesson *Lists and loops* (for loops) and *Decisions and dictionaries* (`in`).",
        intuition="Look at each character in turn and keep a tally of those that are vowels. Lower-casing first means you only have to check five letters.",
        hints=["A `for` loop over a string visits its characters one at a time.", "`letter in \"aeiou\"` asks whether the letter is one of those five.", "Start a counter at 0 and add 1 for each vowel."],
        brute_force="Five separate `text.count(...)` calls added together — fine, and also O(n).",
        approach="`count = 0`; loop over `text.lower()`; if the letter is in `\"aeiou\"` add one; return `count`.",
        complexity="O(n).",
        pitfalls="- Forgetting upper-case vowels.\n- Returning inside the loop (which stops after the first character).\n- Counting *distinct* vowels with a set instead of occurrences.",
        follow_up="Return a dictionary with a separate count for each vowel.",
    ),
),
dict(
    id="py-start-basket-total",
    title="Basket Total",
    difficulty="Easy",
    pattern="Dictionaries",
    entry="basket_total",
    compare="float",
    description=r"""
A shop keeps its prices in a dictionary such as `{"tea": 3.5, "lemons": 1.2}`. A customer's basket is a
list of item names, where an item appears once for each unit bought.

Write `basket_total(prices, basket)` that returns `[total, unknown]`:

- `total` — the sum of the prices of all basket items that the shop sells, rounded to 2 decimals;
- `unknown` — a list of the item names that are **not** in `prices`, in the order they first appear,
  each listed once.

**Example:** `prices = {"tea": 3.5, "lemons": 1.2}`, `basket = ["tea", "caviar", "lemons", "tea", "caviar"]`
→ `[8.2, ["caviar"]]`
""",
    starter='''def basket_total(prices: dict, basket: list) -> list:
    pass
''',
    solution='''def basket_total(prices, basket):
    total = 0
    unknown = []
    for item in basket:
        if item in prices:
            total += prices[item]
        elif item not in unknown:
            unknown.append(item)
    return [round(total, 2), unknown]
''',
    tests=[
        [{"tea": 3.5, "lemons": 1.2}, ["tea", "caviar", "lemons", "tea", "caviar"]],
        [{"tea": 3.5}, []],
        [{}, ["a", "b", "a"]],
        [{"a": 0.1, "b": 0.2}, ["a", "b"]],
        [{"pen": 1.25, "ink": 4.0, "pad": 2.5}, ["pad", "pen", "pen", "ink", "pad"]],
        [{"x": 2}, ["y", "z", "y", "x", "w"]],
        [{"free": 0}, ["free", "free"]],
        [{"a": 1.005, "b": 2.675}, ["a", "b", "b"]],
        [{f"item{i}": i * 0.5 for i in range(50)}, [f"item{i % 60}" for i in range(300)]],
    ],
    examples=1,
    wrong_solutions=['''def basket_total(prices, basket):
    total = 0
    unknown = []
    for item in basket:
        if item in prices:
            total += prices[item]
        else:
            unknown.append(item)
    return [round(total, 2), unknown]
''', '''def basket_total(prices, basket):
    return [round(sum(prices[i] for i in set(basket) if i in prices), 2), [i for i in dict.fromkeys(basket) if i not in prices]]
'''],
    guide=dict(
        prereqs="Lesson *Decisions and dictionaries*: lookups, `in`, building a list.",
        intuition="Walk through the basket once. Each item is either known (add its price) or unknown (remember its name, but only the first time).",
        hints=["`if item in prices:` checks the keys of the dictionary.", "Keep two things as you loop: a running total and a list of unknown names.", "Before appending to `unknown`, check `item not in unknown`."],
        brute_force="Two separate passes — one for the total, one for the unknowns — is equally fine.",
        approach="Loop; known → `total += prices[item]`; unknown and not yet recorded → append; finally `round(total, 2)`.",
        complexity="O(n) for the basket (plus the small cost of checking the unknown list).",
        pitfalls="- `prices[item]` on a missing key raises `KeyError`.\n- Recording an unknown item every time it appears.\n- Counting an item only once when it is in the basket several times.\n- Floating-point noise such as 0.30000000000000004 — round at the end.",
        follow_up="Return the unknown items sorted, or count how many of each were requested.",
    ),
),
dict(
    id="py-start-multiples",
    title="Multiples in a Range",
    difficulty="Easy",
    pattern="range & Comprehensions",
    entry="multiples",
    description=r"""
Write `multiples(limit, a, b)` that returns a list, in increasing order, of every whole number from
`1` to `limit` (inclusive) that is divisible by `a` or by `b` (or both). `a` and `b` are positive.
A number divisible by both appears only once.

**Example:** `multiples(20, 3, 5)` → `[3, 5, 6, 9, 10, 12, 15, 18, 20]`

**Example:** `multiples(4, 5, 7)` → `[]`
""",
    starter='''def multiples(limit: int, a: int, b: int) -> list:
    pass
''',
    solution='''def multiples(limit, a, b):
    return [n for n in range(1, limit + 1) if n % a == 0 or n % b == 0]
''',
    tests=[[20, 3, 5], [4, 5, 7], [0, 2, 3], [10, 1, 7], [15, 15, 15], [30, 4, 6], [1, 1, 1], [12, 12, 5],
           [100, 7, 11], [1000, 13, 17], [9, 3, 9]],
    examples=2,
    wrong_solutions=['''def multiples(limit, a, b):
    return [n for n in range(1, limit) if n % a == 0 or n % b == 0]
''', '''def multiples(limit, a, b):
    return [n for n in range(1, limit + 1) if n % a == 0] + [n for n in range(1, limit + 1) if n % b == 0]
'''],
    guide=dict(
        prereqs="Lesson *Lists and loops*: `range`, the remainder operator `%`, list comprehensions.",
        intuition="Go through the numbers 1 to limit and keep those that leave no remainder when divided by `a` or by `b`.",
        hints=["`range(1, limit + 1)` includes `limit` itself.", "`n % a == 0` means n is divisible by a.", "Combine the two tests with `or`."],
        brute_force="An explicit loop with `append` — exactly what the comprehension abbreviates.",
        approach="`[n for n in range(1, limit + 1) if n % a == 0 or n % b == 0]`. Checking each number once keeps the order and avoids duplicates automatically.",
        complexity="O(limit).",
        pitfalls="- `range(1, limit)` stops one short.\n- Building two lists and joining them gives duplicates and breaks the order.",
        follow_up="Return their sum instead (a classic warm-up puzzle).",
    ),
),
dict(
    id="py-start-word-lengths",
    title="Word Lengths Dictionary",
    difficulty="Easy",
    pattern="Dictionaries & Loops",
    entry="word_lengths",
    description=r"""
Write `word_lengths(sentence)` that returns a dictionary mapping each word of the sentence to its
length. Words are separated by spaces. Treat words case-insensitively: store every word in
**lowercase**, so `"The"` and `"the"` become the single key `"the"`.

**Example:** `"The cat saw the Bird"` → `{"the": 3, "cat": 3, "saw": 3, "bird": 4}`

**Example:** `""` → `{}`
""",
    starter='''def word_lengths(sentence: str) -> dict:
    pass
''',
    solution='''def word_lengths(sentence):
    lengths = {}
    for word in sentence.lower().split():
        lengths[word] = len(word)
    return lengths
''',
    tests=[["The cat saw the Bird"], [""], ["one"], ["  spaced   out  words "], ["A a A a"], ["I am what I am"],
           ["Mississippi river RIVER"], ["x yy zzz yy x"], [" ".join(f"w{i % 40}" for i in range(400))]],
    examples=2,
    wrong_solutions=['''def word_lengths(sentence):
    return {word: len(word) for word in sentence.split(" ")}
''', '''def word_lengths(sentence):
    return {word: len(word) for word in sentence.split()}
'''],
    guide=dict(
        prereqs="Lesson *Decisions and dictionaries*: adding key-value pairs in a loop.",
        intuition="Split the sentence into words, and for each one store `word → len(word)`. Assigning to a key that already exists simply overwrites it with the same value, so repeats take care of themselves.",
        hints=["`sentence.lower().split()` gives a list of lowercase words and ignores extra spaces.", "Start with `lengths = {}` and assign `lengths[word] = len(word)`."],
        brute_force="Not applicable — one pass is the natural solution.",
        approach="Lowercase, split, loop, assign. As a comprehension: `{w: len(w) for w in sentence.lower().split()}`.",
        complexity="O(n) in the length of the sentence.",
        pitfalls="- `split(\" \")` produces empty strings when there are repeated spaces; `split()` does not.\n- Forgetting `lower()` creates separate keys for `The` and `the`.",
        follow_up="Group words by length instead: `{3: [\"the\", \"cat\"], 4: [\"bird\"]}`.",
    ),
),
dict(
    id="py-start-halving-steps",
    title="Steps to Reach One",
    difficulty="Easy",
    pattern="while Loops",
    entry="steps_to_one",
    description=r"""
Start with a positive whole number `n` and repeat this rule until the number becomes 1:

- if the number is even, halve it;
- if it is odd, multiply it by 3 and add 1.

Write `steps_to_one(n)` that returns how many times the rule had to be applied. (For every starting
value anyone has tried, the sequence does reach 1.)

**Example:** `n = 6` → the sequence is 6, 3, 10, 5, 16, 8, 4, 2, 1 → `8` steps

**Example:** `n = 1` → `0`
""",
    starter='''def steps_to_one(n: int) -> int:
    pass
''',
    solution='''def steps_to_one(n):
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps
''',
    tests=[[6], [1], [2], [7], [27], [16], [97], [1000], [871], [9999], [3]],
    examples=2,
    wrong_solutions=['''def steps_to_one(n):
    steps = 0
    while n > 1:
        n = n // 2
        steps += 1
    return steps
''', '''def steps_to_one(n):
    steps = 1
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps
'''],
    guide=dict(
        prereqs="Lesson *User input, while loops and functions*: `while`, counters, `%`.",
        intuition="You cannot know in advance how many rounds are needed, so this is a job for `while`: keep applying the rule until the number is 1, counting as you go.",
        hints=["The loop condition is `n != 1`.", "`n % 2 == 0` tests for even; use `n // 2` so the result stays a whole number.", "Add one to a counter each time round and return it after the loop."],
        brute_force="This *is* the direct simulation; there is no known formula.",
        approach="`steps = 0`; `while n != 1:` apply the rule, `steps += 1`; `return steps`. Dry run for 6: 3, 10, 5, 16, 8, 4, 2, 1 → eight updates.",
        complexity="Unknown in general (this is the famous Collatz problem); small in practice.",
        pitfalls="- `/` instead of `//` turns the number into a float.\n- Starting the counter at 1 (off by one).\n- Forgetting to change `n` inside the loop — an infinite loop.",
        follow_up="Return the whole sequence as a list, or find the start value below 1000 with the most steps.",
    ),
),
dict(
    id="py-start-safe-divide",
    title="A Calculator That Does Not Crash",
    difficulty="Easy",
    pattern="Exceptions",
    entry="safe_divide",
    compare="float",
    description=r"""
A user types two values as **text**. Write `safe_divide(a_text, b_text)` that tries to divide the
first number by the second and never crashes:

- if both texts are valid numbers (e.g. `"7"`, `" 2.5 "`, `"-3"`) and the second is not zero, return
  the result of the division as a float;
- if either text is not a number, return the string `"not a number"`;
- if both are numbers but the second is zero, return the string `"cannot divide by zero"`.

Use `try` / `except` with `float(...)`.

**Example:** `safe_divide("7", "2")` → `3.5`

**Example:** `safe_divide("seven", "2")` → `"not a number"`; `safe_divide("7", "0")` → `"cannot divide by zero"`
""",
    starter='''def safe_divide(a_text: str, b_text: str):
    pass
''',
    solution='''def safe_divide(a_text, b_text):
    try:
        a = float(a_text)
        b = float(b_text)
    except ValueError:
        return "not a number"
    try:
        return a / b
    except ZeroDivisionError:
        return "cannot divide by zero"
''',
    tests=[["7", "2"], ["seven", "2"], ["7", "0"], [" 2.5 ", "0.5"], ["-3", "4"], ["", "1"], ["1", ""],
           ["0", "5"], ["abc", "0"], ["1e3", "10"], ["10", "0.0"], ["3", "three"]],
    examples=3,
    wrong_solutions=['''def safe_divide(a_text, b_text):
    try:
        return float(a_text) / float(b_text)
    except Exception:
        return "not a number"
''', '''def safe_divide(a_text, b_text):
    if float(b_text) == 0:
        return "cannot divide by zero"
    try:
        return float(a_text) / float(b_text)
    except ValueError:
        return "not a number"
'''],
    guide=dict(
        prereqs="Lesson *Files, errors and tests*: `try` / `except`, `ValueError`, `ZeroDivisionError`.",
        intuition="Two different things can go wrong, and each has its own exception type: converting text (`ValueError`) and dividing (`ZeroDivisionError`). Catch each one specifically and answer with the matching message.",
        hints=["`float(\"seven\")` raises `ValueError`.", "Convert both texts inside one `try`; return \"not a number\" in its `except ValueError`.", "Then divide inside a second `try` (or check `b == 0` with an `if`)."],
        brute_force="Checking the text by hand with `isdigit()` fails on negatives, decimals and spaces — letting `float` decide is both simpler and more correct.",
        approach="```\ntry: a = float(a_text); b = float(b_text)\nexcept ValueError: return \"not a number\"\ntry: return a / b\nexcept ZeroDivisionError: return \"cannot divide by zero\"\n```",
        complexity="O(1).",
        pitfalls="- A single `except Exception` cannot tell the two problems apart.\n- Converting outside the `try` lets the error escape.\n- When *both* problems are present (`\"abc\"`, `\"0\"`), \"not a number\" comes first.",
        follow_up="Wrap it in a loop that keeps asking until the input is valid.",
    ),
),
dict(
    id="py-start-inventory",
    title="Stockroom Class",
    difficulty="Easy",
    pattern="Classes",
    kind="class",
    entry="Stockroom",
    description=r"""
Write a class `Stockroom` that keeps track of how many units of each product are in stock.

- `Stockroom()` starts empty.
- `add(name, quantity)` adds `quantity` units of the product (creating it if necessary). Returns nothing.
- `remove(name, quantity)` takes units out **only if** at least `quantity` are in stock: then it
  reduces the stock and returns `True`. Otherwise it changes nothing and returns `False`.
- `count(name)` returns the units in stock for that product (`0` if it was never added).
- `total()` returns the total number of units across all products.

Quantities are positive whole numbers.

**Example:** `add("tea", 5)`, `remove("tea", 2)` → `True`, `remove("tea", 9)` → `False`,
`count("tea")` → `3`, `count("ink")` → `0`, `total()` → `3`
""",
    starter='''class Stockroom:
    def __init__(self):
        pass

    def add(self, name, quantity):
        pass

    def remove(self, name, quantity):
        pass

    def count(self, name):
        pass

    def total(self):
        pass
''',
    solution='''class Stockroom:
    def __init__(self):
        self.stock = {}

    def add(self, name, quantity):
        self.stock[name] = self.stock.get(name, 0) + quantity

    def remove(self, name, quantity):
        if self.stock.get(name, 0) < quantity:
            return False
        self.stock[name] -= quantity
        return True

    def count(self, name):
        return self.stock.get(name, 0)

    def total(self):
        return sum(self.stock.values())
''',
    tests=[
        [["Stockroom", "add", "remove", "remove", "count", "count", "total"],
         [[], ["tea", 5], ["tea", 2], ["tea", 9], ["tea"], ["ink"], []]],
        [["Stockroom", "total", "count", "remove"], [[], [], ["x"], ["x", 1]]],
        [["Stockroom", "add", "add", "count", "total"], [[], ["pen", 3], ["pen", 4], ["pen"], []]],
        [["Stockroom", "add", "remove", "count", "remove", "total"], [[], ["pad", 2], ["pad", 2], ["pad"], ["pad", 1], []]],
        [["Stockroom", "add", "add", "add", "remove", "total", "count", "count"],
         [[], ["a", 1], ["b", 2], ["c", 3], ["b", 1], [], ["b"], ["c"]]],
        [["Stockroom", "remove", "add", "remove", "remove", "count"], [[], ["tea", 1], ["tea", 1], ["tea", 1], ["tea", 1], ["tea"]]],
        [["Stockroom", "add", "remove", "total", "add", "total"], [[], ["x", 10], ["y", 1], [], ["y", 5], []]],
        [["Stockroom"] + ["add"] * 30 + ["total", "count", "remove", "total"],
         [[]] + [[f"p{i % 7}", i + 1] for i in range(30)] + [[], ["p3"], ["p3", 50], []]],
    ],
    examples=1,
    wrong_solutions=['''class Stockroom:
    def __init__(self):
        self.stock = {}
    def add(self, name, quantity):
        self.stock[name] = quantity
    def remove(self, name, quantity):
        if self.stock.get(name, 0) < quantity:
            return False
        self.stock[name] -= quantity
        return True
    def count(self, name):
        return self.stock.get(name, 0)
    def total(self):
        return sum(self.stock.values())
''', '''class Stockroom:
    def __init__(self):
        self.stock = {}
    def add(self, name, quantity):
        self.stock[name] = self.stock.get(name, 0) + quantity
    def remove(self, name, quantity):
        self.stock[name] = self.stock.get(name, 0) - quantity
        return self.stock[name] >= 0
    def count(self, name):
        return self.stock.get(name, 0)
    def total(self):
        return sum(self.stock.values())
'''],
    guide=dict(
        prereqs="Lesson *Classes: modelling things with objects*; dictionaries with `get`.",
        intuition="The object needs one piece of data — a dictionary from product name to quantity, created in `__init__` — and four small methods that read or update it.",
        hints=["`self.stock = {}` in `__init__`.", "`self.stock.get(name, 0)` gives 0 for an unknown product.", "In `remove`, check first and return `False` *before* changing anything."],
        brute_force="A list of `[name, quantity]` pairs searched with a loop works but every operation becomes O(n).",
        approach="- `add`: `self.stock[name] = self.stock.get(name, 0) + quantity`\n- `remove`: if stock < quantity → `False`; else subtract → `True`\n- `count`: `get(name, 0)`\n- `total`: `sum(self.stock.values())`",
        complexity="O(1) per add/remove/count; O(products) for total.",
        pitfalls="- Forgetting `self.` makes a local variable that vanishes.\n- `add` that overwrites instead of adding.\n- `remove` that subtracts first and leaves the stock negative.\n- `self.stock[name]` on an unknown product raises `KeyError`.",
        follow_up="Add `low_stock(threshold)` returning the sorted names of products below a level.",
    ),
),
# ===================================================================================== PROJECTS
dict(
    id="py-proj-rect-collision",
    title="Do Two Rectangles Collide?",
    difficulty="Easy",
    pattern="Game Logic",
    entry="rects_collide",
    description=r"""
In a 2D game every object has a bounding rectangle given as `[x, y, width, height]`, where `(x, y)`
is its top-left corner and `width`, `height` are positive. (Screen coordinates: `x` grows to the
right, `y` grows downwards.)

Write `rects_collide(a, b)` that returns `True` if the two rectangles **overlap** — that is, share
some area. Rectangles that merely touch along an edge or at a corner do **not** collide.

**Example:** `a = [0, 0, 10, 10], b = [5, 5, 10, 10]` → `True`

**Example:** `a = [0, 0, 10, 10], b = [10, 0, 5, 5]` → `False` (they only touch)
""",
    starter='''def rects_collide(a: list, b: list) -> bool:
    pass
''',
    solution='''def rects_collide(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah
''',
    tests=[
        [[0, 0, 10, 10], [5, 5, 10, 10]],
        [[0, 0, 10, 10], [10, 0, 5, 5]],
        [[0, 0, 10, 10], [0, 10, 10, 10]],
        [[0, 0, 10, 10], [2, 2, 3, 3]],
        [[2, 2, 3, 3], [0, 0, 10, 10]],
        [[0, 0, 10, 10], [20, 20, 5, 5]],
        [[0, 0, 10, 10], [-5, 3, 6, 2]],
        [[0, 0, 10, 10], [-5, 3, 5, 2]],
        [[0, 0, 4, 100], [2, 99, 50, 50]],
        [[0, 0, 4, 100], [2, 100, 50, 50]],
        [[5, 5, 1, 1], [5, 5, 1, 1]],
        [[0, 0, 10, 2], [3, -4, 2, 20]],
        [[0.5, 0.5, 1, 1], [1.4, 1.4, 1, 1]],
        [[10, 10, 5, 5], [15, 15, 5, 5]],
        [[0, 0, 100, 1], [50, 2, 1, 1]],
    ],
    examples=2,
    wrong_solutions=['''def rects_collide(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax <= bx + bw and bx <= ax + aw and ay <= by + bh and by <= ay + ah
''', '''def rects_collide(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    corners = [(bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)]
    return any(ax < x < ax + aw and ay < y < ay + ah for x, y in corners)
'''],
    guide=dict(
        prereqs="Lesson *A game: the loop, state, events and collisions*.",
        intuition="It is easier to say when rectangles do **not** overlap: one is entirely left of, right of, above or below the other. They collide exactly when none of those is true — i.e. their x-ranges overlap **and** their y-ranges overlap.",
        hints=["Unpack: `ax, ay, aw, ah = a`.", "The x-ranges overlap when `ax < bx + bw and bx < ax + aw`.", "Use strict `<` so that touching edges do not count."],
        brute_force="Testing whether any corner of one rectangle lies inside the other misses crossing shapes (a tall thin bar through a wide flat one) and containment in the other direction.",
        approach="Return the conjunction of four comparisons: left edge of each is left of the right edge of the other, top edge of each is above the bottom edge of the other.",
        complexity="O(1).",
        pitfalls="- `<=` counts touching rectangles as colliding.\n- Corner-inside tests fail for plus-shaped crossings.\n- Remember y grows downward: `y + height` is the bottom edge.",
        follow_up="Return the overlapping rectangle; or test a circle against a rectangle.",
    ),
),
dict(
    id="py-proj-game-step",
    title="One Step of a Grid Game",
    difficulty="Medium",
    pattern="Game Logic & State",
    entry="step",
    description=r"""
A treasure hunter moves on a grid that is `width` columns wide and `height` rows high. The game
state is a dictionary:

```
{"width": 5, "height": 4, "player": [x, y], "coins": [[x, y], ...], "score": 0, "moves": 0}
```

Columns are numbered `0 .. width-1` from the left and rows `0 .. height-1` from the top.

Write `step(state, command)` that returns the **new state** after one command, without modifying
the state it was given:

- `command` is `"left"`, `"right"`, `"up"`, `"down"` or `"wait"`. Up decreases `y`, down increases it.
- A move that would leave the grid is ignored (the player stays put) — but it still counts as a move.
- `moves` increases by 1 for **every** command, including `"wait"` and blocked moves.
- If the player ends the step on a square containing a coin, that coin is removed and `score`
  increases by 10. The remaining coins keep their order.
- Any other command string leaves the state completely unchanged (not even `moves`).

**Example:** player `[1, 1]`, coins `[[2, 1], [4, 3]]`, command `"right"` → player `[2, 1]`,
coins `[[4, 3]]`, score `10`, moves `1`.
""",
    starter='''def step(state: dict, command: str) -> dict:
    pass
''',
    solution='''MOVES = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1), "wait": (0, 0)}

def step(state, command):
    if command not in MOVES:
        return {**state, "player": list(state["player"]), "coins": [list(c) for c in state["coins"]]}
    dx, dy = MOVES[command]
    x, y = state["player"]
    nx, ny = x + dx, y + dy
    if not (0 <= nx < state["width"] and 0 <= ny < state["height"]):
        nx, ny = x, y
    coins = [list(c) for c in state["coins"] if list(c) != [nx, ny]]
    gained = 10 * (len(state["coins"]) - len(coins))
    return {
        "width": state["width"],
        "height": state["height"],
        "player": [nx, ny],
        "coins": coins,
        "score": state["score"] + gained,
        "moves": state["moves"] + 1,
    }
''',
    tests=[
        [{"width": 5, "height": 4, "player": [1, 1], "coins": [[2, 1], [4, 3]], "score": 0, "moves": 0}, "right"],
        [{"width": 5, "height": 4, "player": [0, 0], "coins": [[2, 1]], "score": 0, "moves": 3}, "left"],
        [{"width": 5, "height": 4, "player": [0, 0], "coins": [[2, 1]], "score": 0, "moves": 3}, "up"],
        [{"width": 5, "height": 4, "player": [4, 3], "coins": [], "score": 50, "moves": 9}, "down"],
        [{"width": 5, "height": 4, "player": [4, 3], "coins": [], "score": 50, "moves": 9}, "right"],
        [{"width": 5, "height": 4, "player": [2, 2], "coins": [[2, 3], [2, 1], [1, 2]], "score": 20, "moves": 1}, "down"],
        [{"width": 5, "height": 4, "player": [2, 2], "coins": [[2, 3], [2, 1], [1, 2]], "score": 20, "moves": 1}, "up"],
        [{"width": 5, "height": 4, "player": [2, 2], "coins": [[2, 2]], "score": 0, "moves": 0}, "wait"],
        [{"width": 5, "height": 4, "player": [2, 2], "coins": [[3, 2]], "score": 0, "moves": 7}, "jump"],
        [{"width": 1, "height": 1, "player": [0, 0], "coins": [], "score": 0, "moves": 0}, "down"],
        [{"width": 3, "height": 3, "player": [1, 0], "coins": [[0, 0], [2, 0], [1, 1]], "score": 0, "moves": 0}, "left"],
        [{"width": 3, "height": 3, "player": [0, 0], "coins": [[0, 0]], "score": 0, "moves": 0}, "up"],
    ],
    examples=1,
    wrong_solutions=['''MOVES = {"left": (-1, 0), "right": (1, 0), "up": (0, 1), "down": (0, -1), "wait": (0, 0)}
def step(state, command):
    if command not in MOVES:
        return dict(state)
    dx, dy = MOVES[command]
    x, y = state["player"]
    nx, ny = x + dx, y + dy
    if not (0 <= nx < state["width"] and 0 <= ny < state["height"]):
        nx, ny = x, y
    coins = [c for c in state["coins"] if c != [nx, ny]]
    return {**state, "player": [nx, ny], "coins": coins,
            "score": state["score"] + 10 * (len(state["coins"]) - len(coins)), "moves": state["moves"] + 1}
''', '''MOVES = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1), "wait": (0, 0)}
def step(state, command):
    if command not in MOVES:
        return dict(state)
    dx, dy = MOVES[command]
    x, y = state["player"]
    nx, ny = x + dx, y + dy
    if not (0 <= nx < state["width"] and 0 <= ny < state["height"]):
        return dict(state)
    coins = [c for c in state["coins"] if c != [nx, ny]]
    return {**state, "player": [nx, ny], "coins": coins,
            "score": state["score"] + 10 * (len(state["coins"]) - len(coins)), "moves": state["moves"] + 1}
'''],
    guide=dict(
        prereqs="Lesson *A game: the loop, state, events and collisions* — state and the update phase.",
        intuition="This is the *update* phase of a game loop written as a pure function: new state = f(old state, input). Translate the command into a change of position, clamp to the grid, then resolve what the player is standing on.",
        hints=["A dictionary from command to `(dx, dy)` replaces a chain of `if`s.", "Check `0 <= nx < width and 0 <= ny < height`; if it fails, keep the old position.", "Build a new coins list without the coin at the player's square; the score grows by 10 per coin removed.", "Return a new dictionary rather than changing `state`."],
        brute_force="Five nearly identical `if` branches, one per command — works, but every rule change must be made five times.",
        approach="1. Unknown command → return an unchanged copy.\n2. Look up `(dx, dy)`, compute the target, fall back to the current square if off-grid.\n3. Filter the coins; add 10 to the score if one disappeared.\n4. Return a fresh dict with `moves + 1`.",
        complexity="O(number of coins) per step.",
        pitfalls="- `up` must *decrease* y (screen coordinates).\n- A blocked move still counts as a move.\n- A coin on the square where a blocked or waiting player already stands is collected.\n- Mutating the input state makes the function untestable and breaks undo/replay.",
        follow_up="Add walls (a list of blocked squares) and a win condition when no coins remain.",
    ),
),
dict(
    id="py-proj-bounce",
    title="Bouncing Ball Simulation",
    difficulty="Medium",
    pattern="Simulation",
    entry="simulate",
    description=r"""
A ball moves in a box that spans `0 .. width` horizontally and `0 .. height` vertically. Its
position is `(x, y)` and its velocity `(vx, vy)` in units per tick; all values are whole numbers.

Each **tick**, the ball moves by its velocity. If that carries it past a wall, it is reflected: the
distance it overshot is folded back inside the box and the corresponding velocity component changes
sign. For example, with `width = 10`, a ball at `x = 8` with `vx = 5` would reach 13 — three past the
wall — so it ends the tick at `x = 7` with `vx = -5`. The same rule applies at `0` and on the
vertical axis. You may assume `|vx| <= width` and `|vy| <= height`, so at most one bounce per axis
happens in a tick.

Write `simulate(x, y, vx, vy, width, height, ticks)` returning `[x, y, vx, vy]` after `ticks` ticks.

**Example:** `simulate(8, 0, 5, 0, 10, 10, 1)` → `[7, 0, -5, 0]`

**Example:** `simulate(1, 1, -3, 2, 10, 10, 2)` → `[5, 5, 3, 2]` (tick 1: x would be −2, reflected to 2 with `vx = 3`, and y becomes 3; tick 2: x = 5, y = 5)
""",
    starter='''def simulate(x, y, vx, vy, width, height, ticks):
    pass
''',
    solution='''def _move(pos, vel, limit):
    pos += vel
    if pos < 0:
        pos, vel = -pos, -vel
    elif pos > limit:
        pos, vel = 2 * limit - pos, -vel
    return pos, vel

def simulate(x, y, vx, vy, width, height, ticks):
    for _ in range(ticks):
        x, vx = _move(x, vx, width)
        y, vy = _move(y, vy, height)
    return [x, y, vx, vy]
''',
    tests=[[8, 0, 5, 0, 10, 10, 1], [1, 1, -3, 2, 10, 10, 2], [0, 0, 0, 0, 5, 5, 10], [5, 5, 1, 1, 10, 10, 0],
           [0, 0, 1, 1, 4, 4, 9], [3, 2, 4, -2, 6, 3, 7], [10, 10, 10, 10, 10, 10, 3], [2, 7, -2, 3, 9, 8, 25],
           [0, 5, 7, 0, 7, 9, 100], [4, 4, -1, -1, 8, 8, 1000], [6, 1, 5, 9, 6, 9, 13]],
    examples=1,
    wrong_solutions=['''def simulate(x, y, vx, vy, width, height, ticks):
    for _ in range(ticks):
        x += vx; y += vy
        if x < 0 or x > width: vx = -vx
        if y < 0 or y > height: vy = -vy
    return [x, y, vx, vy]
''', '''def simulate(x, y, vx, vy, width, height, ticks):
    for _ in range(ticks):
        x += vx; y += vy
        if x < 0: x, vx = 0, -vx
        if x > width: x, vx = width, -vx
        if y < 0: y, vy = 0, -vy
        if y > height: y, vy = height, -vy
    return [x, y, vx, vy]
'''],
    guide=dict(
        prereqs="Lesson *A game: the loop, state, events and collisions* — movement as position plus velocity.",
        intuition="The two axes are independent, so solve one axis in a helper and use it twice. Reflection means: whatever distance the ball travelled beyond the wall, it travels back inside instead, and its direction flips.",
        hints=["Write `move(pos, vel, limit)` returning the new `(pos, vel)`.", "Past the low wall: `pos = -pos`. Past the high wall: `pos = 2 * limit - pos`.", "Flip the sign of the velocity whenever a reflection happens.", "Loop `ticks` times, updating x then y."],
        brute_force="Moving one unit at a time and checking the walls after each unit also works, at |v| times the cost.",
        approach="Per tick and per axis: add the velocity; if below 0 mirror around 0; if above the limit mirror around the limit; flip velocity in either case.",
        complexity="O(ticks).",
        pitfalls="- Flipping the velocity without correcting the position leaves the ball outside the box.\n- Clamping to the wall (instead of reflecting the overshoot) loses distance.\n- Landing exactly on a wall is not a bounce yet; the bounce happens on the following tick if the ball keeps going.",
        follow_up="Allow speeds larger than the box (several bounces per tick) using the modulo of `2 * limit`.",
    ),
),
dict(
    id="py-proj-high-scores",
    title="High-Score Table",
    difficulty="Easy",
    pattern="Lists & Sorting",
    entry="add_score",
    description=r"""
A game keeps its best results in a table: a list of `[name, score]` pairs ordered from the highest
score to the lowest. When scores are equal, the entry that was added **earlier** stays higher.

Write `add_score(table, name, score, limit)` that returns a **new** table with the entry
`[name, score]` inserted in the right place and cut down to at most `limit` entries. The original
table must not be modified. (`limit` is at least 1; the given table is already ordered and no longer
than `limit`.)

**Example:** `table = [["ana", 90], ["ben", 70]]`, `add_score(table, "cy", 80, 3)` →
`[["ana", 90], ["cy", 80], ["ben", 70]]`

**Example:** `add_score([["ana", 90], ["ben", 70]], "dee", 70, 3)` → `[["ana", 90], ["ben", 70], ["dee", 70]]`
""",
    starter='''def add_score(table: list, name: str, score: int, limit: int) -> list:
    pass
''',
    solution='''def add_score(table, name, score, limit):
    position = len(table)
    for i, entry in enumerate(table):
        if score > entry[1]:
            position = i
            break
    new_table = [list(e) for e in table[:position]] + [[name, score]] + [list(e) for e in table[position:]]
    return new_table[:limit]
''',
    tests=[
        [[["ana", 90], ["ben", 70]], "cy", 80, 3],
        [[["ana", 90], ["ben", 70]], "dee", 70, 3],
        [[], "first", 10, 5],
        [[["ana", 90], ["ben", 70]], "low", 5, 2],
        [[["ana", 90], ["ben", 70]], "top", 100, 2],
        [[["a", 50], ["b", 50], ["c", 50]], "d", 50, 4],
        [[["a", 50], ["b", 50], ["c", 50]], "d", 50, 3],
        [[["a", 50], ["b", 40], ["c", 30]], "d", 40, 4],
        [[["solo", 1]], "new", 1, 1],
        [[["solo", 1]], "new", 2, 1],
        [[[f"p{i}", 100 - i] for i in range(20)], "mid", 90, 20],
        [[["x", 0], ["y", -5]], "z", -1, 5],
    ],
    examples=2,
    wrong_solutions=['''def add_score(table, name, score, limit):
    new_table = table + [[name, score]]
    new_table.sort(key=lambda e: e[1])
    return new_table[:limit]
''', '''def add_score(table, name, score, limit):
    position = len(table)
    for i, entry in enumerate(table):
        if score >= entry[1]:
            position = i
            break
    return (table[:position] + [[name, score]] + table[position:])[:limit]
'''],
    guide=dict(
        prereqs="Lists, slicing and sorting; the scoring section of the game lesson.",
        intuition="Find the first entry whose score is strictly lower than the new one and insert just before it; if there is none, the new entry goes at the end. Then keep only the first `limit` entries.",
        hints=["Use `>` (not `>=`) when comparing, so that equal scores stay behind earlier entries.", "Build the result from slices: `table[:i] + [[name, score]] + table[i:]`.", "Alternatively append and use `sorted(..., key=lambda e: -e[1])` — Python's sort is *stable*, so ties keep their order.", "Finish with `[:limit]`."],
        brute_force="Append and re-sort the whole table: O(n log n) instead of O(n), perfectly acceptable for a ten-line leaderboard — as long as you sort by descending score and rely on stability for ties.",
        approach="Scan for the insertion index, assemble a new list with slices, truncate. Equivalent one-liner: `sorted(table + [[name, score]], key=lambda e: -e[1])[:limit]`.",
        complexity="O(n).",
        pitfalls="- Sorting ascending puts the worst score first.\n- `>=` lets a newcomer jump ahead of an equal, earlier score.\n- `table.append(...)` or `table.sort()` changes the caller's list.",
        follow_up="Save and load the table as JSON so it survives between games.",
    ),
),
dict(
    id="py-proj-api-stations",
    title="Summarise an API Response",
    difficulty="Medium",
    pattern="JSON & Defensive Parsing",
    entry="summarise_stations",
    compare="float",
    description=r"""
A tide-monitoring API returns a JSON object (already parsed into Python for you) shaped like this:

```
{"total_count": 5,
 "items": [
   {"id": "PRT-01", "name": "Foz Lighthouse", "latest": {"height_m": 2.31}, "sensors": ["tide", "wind"]},
   {"id": "PRT-03", "name": "Afurada Pier", "latest": null, "sensors": []},
   ...
 ]}
```

Real payloads are messy: `"items"` may be missing; a record may lack `"id"` or `"name"`; `"latest"`
may be missing or `null`; `"height_m"` may be missing.

Write `summarise_stations(payload, min_height)` returning a dictionary with:

- `"usable"` — the number of records that have both an `"id"` and a `"name"`;
- `"without_reading"` — the sorted list of ids of usable records that have no height reading;
- `"high"` — a list of `[name, height]` for usable records whose height is at least `min_height`,
  ordered by height descending, ties by name ascending.

**Example:** with the sample payload of test 1 and `min_height = 2.0` →
`{"usable": 6, "without_reading": ["PRT-03", "PRT-04"], "high": [["Leixoes", 3.05], ["Douro Mouth", 2.31], ["Foz Lighthouse", 2.31]]}`
""",
    starter='''def summarise_stations(payload: dict, min_height: float) -> dict:
    pass
''',
    solution='''def summarise_stations(payload, min_height):
    usable = 0
    without_reading = []
    high = []
    for item in payload.get("items") or []:
        if "id" not in item or "name" not in item:
            continue
        usable += 1
        height = (item.get("latest") or {}).get("height_m")
        if height is None:
            without_reading.append(item["id"])
        elif height >= min_height:
            high.append([item["name"], height])
    high.sort(key=lambda pair: (-pair[1], pair[0]))
    return {"usable": usable, "without_reading": sorted(without_reading), "high": high}
''',
    tests=[
        [_PAYLOAD, 2.0],
        [_PAYLOAD, 0],
        [_PAYLOAD, 99],
        [{}, 1.0],
        [{"items": []}, 1.0],
        [{"items": None}, 1.0],
        [{"items": [{"id": "A", "name": "Alpha"}]}, 0],
        [{"items": [{"id": "A", "name": "Alpha", "latest": {}}, {"id": "B", "name": "Beta", "latest": {"height_m": 0}}]}, 0],
        [{"items": [{"id": "B", "name": "Beta", "latest": {"height_m": 1.5}}, {"id": "A", "name": "Alpha", "latest": {"height_m": 1.5}},
                    {"id": "C", "name": "Gamma", "latest": {"height_m": 1.5}}]}, 1.5],
        [{"items": [{"id": f"S{i:02d}", "name": f"Station {i:02d}", "latest": ({"height_m": (i * 7) % 10 / 2} if i % 4 else None)}
                    for i in range(60)]}, 3.0],
    ],
    examples=1,
    wrong_solutions=['''def summarise_stations(payload, min_height):
    usable, without, high = 0, [], []
    for item in payload.get("items", []):
        if "id" not in item or "name" not in item:
            continue
        usable += 1
        latest = item.get("latest", {})
        if "height_m" not in latest:
            without.append(item["id"])
        elif latest["height_m"] >= min_height:
            high.append([item["name"], latest["height_m"]])
    high.sort(key=lambda p: (-p[1], p[0]))
    return {"usable": usable, "without_reading": sorted(without), "high": high}
''', '''def summarise_stations(payload, min_height):
    usable, without, high = 0, [], []
    for item in payload.get("items") or []:
        if "id" not in item or "name" not in item:
            continue
        usable += 1
        height = (item.get("latest") or {}).get("height_m")
        if not height:
            without.append(item["id"])
        elif height >= min_height:
            high.append([item["name"], height])
    high.sort(key=lambda p: -p[1])
    return {"usable": usable, "without_reading": sorted(without), "high": high}
'''],
    guide=dict(
        prereqs="Lesson *Working with web APIs*: exploring payloads, optional and null fields.",
        intuition="Walk the records once, normalising each into 'unusable', 'usable without a reading' or 'usable with a height'. The whole difficulty is that a key can be absent *or* present with the value `None`.",
        hints=["`payload.get(\"items\") or []` survives both a missing key and `null`.", "`(item.get(\"latest\") or {}).get(\"height_m\")` yields the height or `None`.", "Test `height is None` — a height of `0` is a real reading.", "Sort with the key `(-height, name)`."],
        brute_force="Wrapping each lookup in its own try/except works but hides which case you are handling; `.get` with `or {}` is clearer.",
        approach="Loop; skip records lacking id or name; count the rest; extract the height tolerantly; route to the right list; sort and return.",
        complexity="O(n log n) for the final sort.",
        pitfalls="- `item.get(\"latest\", {})` returns `None` when the value is `null` — the default only applies to a *missing* key.\n- `if not height` treats 0 as missing.\n- Forgetting the tie-break on name.\n- Indexing `item[\"latest\"][\"height_m\"]` directly crashes on the first incomplete record.",
        follow_up="Fetch every page of a paginated endpoint first (pass the page-fetching function in as an argument).",
    ),
),
dict(
    id="py-proj-rain-by-city",
    title="Aggregate CSV Rows",
    difficulty="Medium",
    pattern="CSV & Grouping",
    entry="rain_by_city",
    compare="float",
    description=r"""
You are given the **text** of a CSV file with the header `date,city,rain_mm` and one measurement per
line, for example:

```
date,city,rain_mm
2026-01-03,Porto,12.5
2026-01-03,Faro,0
2026-01-04, Porto ,7.5
2026-01-05,Faro,n/a
```

Write `rain_by_city(text)` that returns a dictionary with:

- `"cities"` — a dictionary mapping each city to
  `{"days": number of valid rows, "total": total rain rounded to 1 decimal, "wettest": [date, rain_mm]}`
  where `wettest` is the row with the most rain (the earliest such row in the file if tied);
- `"skipped"` — how many data lines were skipped.

Rules: strip spaces around every field. A data line is **skipped** if it does not have exactly three
fields, if `rain_mm` is not a number, or if the city is empty. Completely blank lines are ignored and
not counted as skipped. The header line is not data.

**Example:** the text above → `{"cities": {"Porto": {"days": 2, "total": 20.0, "wettest": ["2026-01-03", 12.5]}, "Faro": {"days": 1, "total": 0.0, "wettest": ["2026-01-03", 0.0]}}, "skipped": 1}`
""",
    starter='''import csv
import io

def rain_by_city(text: str) -> dict:
    pass
''',
    solution='''import csv
import io

def rain_by_city(text):
    cities = {}
    skipped = 0
    reader = csv.reader(io.StringIO(text))
    next(reader, None)                      # header
    for row in reader:
        if not row:
            continue
        fields = [field.strip() for field in row]
        if len(fields) != 3 or not fields[1]:
            skipped += 1
            continue
        day, city, rain_text = fields
        try:
            rain = float(rain_text)
        except ValueError:
            skipped += 1
            continue
        info = cities.setdefault(city, {"days": 0, "total": 0.0, "wettest": [day, rain]})
        info["days"] += 1
        info["total"] += rain
        if rain > info["wettest"][1]:
            info["wettest"] = [day, rain]
    for info in cities.values():
        info["total"] = round(info["total"], 1)
    return {"cities": cities, "skipped": skipped}
''',
    tests=[
        ["date,city,rain_mm\n2026-01-03,Porto,12.5\n2026-01-03,Faro,0\n2026-01-04, Porto ,7.5\n2026-01-05,Faro,n/a\n"],
        ["date,city,rain_mm\n"],
        [""],
        ["date,city,rain_mm\n\n\n2026-02-01,Braga,3\n\n"],
        ["date,city,rain_mm\n2026-02-01,Braga\n2026-02-02,Braga,1,extra\n2026-02-03,,4\n2026-02-04,Braga,2\n"],
        ["date,city,rain_mm\n2026-03-01,Evora,5\n2026-03-02,Evora,5\n2026-03-03,Evora,4.9\n"],
        ["date,city,rain_mm\n2026-03-01,Evora,0.1\n2026-03-02,Evora,0.2\n2026-03-03,Faro,0.3\n"],
        ["date,city,rain_mm\n2026-04-01,Faro,-1\n2026-04-02,Faro,1e1\n2026-04-03,Faro,\n"],
        [_csv_rain(1, 60)],
        [_csv_rain(2, 600)],
        [_csv_rain(3, 2500)],
    ],
    examples=1,
    wrong_solutions=['''def rain_by_city(text):
    cities, skipped = {}, 0
    for line in text.splitlines()[1:]:
        parts = line.split(",")
        try:
            day, city, rain = parts[0], parts[1], float(parts[2])
        except (ValueError, IndexError):
            skipped += 1
            continue
        info = cities.setdefault(city, {"days": 0, "total": 0.0, "wettest": [day, rain]})
        info["days"] += 1
        info["total"] += rain
        if rain > info["wettest"][1]:
            info["wettest"] = [day, rain]
    for info in cities.values():
        info["total"] = round(info["total"], 1)
    return {"cities": cities, "skipped": skipped}
''', '''import csv, io
def rain_by_city(text):
    cities, skipped = {}, 0
    reader = csv.reader(io.StringIO(text)); next(reader, None)
    for row in reader:
        if not row: continue
        f = [x.strip() for x in row]
        if len(f) != 3 or not f[1]:
            skipped += 1; continue
        try: rain = float(f[2])
        except ValueError:
            skipped += 1; continue
        info = cities.setdefault(f[1], {"days": 0, "total": 0.0, "wettest": [f[0], rain]})
        info["days"] += 1; info["total"] += rain
        if rain >= info["wettest"][1]:
            info["wettest"] = [f[0], rain]
    for info in cities.values():
        info["total"] = round(info["total"], 1)
    return {"cities": cities, "skipped": skipped}
'''],
    guide=dict(
        prereqs="Lesson *Data visualisation*: load, clean, group, aggregate.",
        intuition="This is the whole data pipeline in one function: read rows, reject the bad ones (counting them), group by city, and keep three running summaries per group.",
        hints=["`csv.reader(io.StringIO(text))` yields a list per line; `next(reader, None)` skips the header.", "A blank line arrives as an empty list.", "Convert the rain with `float` inside `try/except ValueError`.", "`cities.setdefault(city, {...})` creates the group the first time it is seen.", "Use strict `>` when updating the wettest day so earlier rows win ties."],
        brute_force="Collect all valid rows per city in lists, then compute `len`, `sum` and `max` for each — clear, and only slightly more memory.",
        approach="1. Iterate rows, ignoring blank ones.\n2. Strip fields; validate count, city and number; otherwise `skipped += 1`.\n3. Update `days`, `total` and `wettest` for that city.\n4. Round totals once at the end.",
        complexity="O(number of rows).",
        pitfalls="- Forgetting to strip spaces creates separate cities `\"Porto\"` and `\" Porto \"`.\n- Counting blank lines as skipped.\n- Rounding inside the loop accumulates error; round once at the end.\n- `>=` makes the *latest* tied day the wettest.\n- A row with two or four fields must be rejected, not half-read.",
        follow_up="Return the cities sorted by total rain, and draw a text bar chart of the result.",
    ),
),
dict(
    id="py-proj-route-match",
    title="URL Routing Table",
    difficulty="Medium",
    pattern="Parsing & Dispatch",
    entry="resolve",
    description=r"""
Web frameworks decide which function handles a request by matching the request path against a table
of patterns. Implement that lookup.

`routes` is a list of `[pattern, name]` pairs. A pattern is a path made of segments separated by
`/`; a segment is either fixed text (`plants`) or a **converter** written `<int:param>` or
`<str:param>`:

- `<int:param>` matches a segment consisting only of digits and captures it as an **integer**;
- `<str:param>` matches any non-empty segment and captures it as a string.

Write `resolve(routes, path)` that returns `[name, params]` for the **first** pattern in the table
that matches the whole path, where `params` is a dictionary of captured values, or `None` if nothing
matches. Leading and trailing slashes are ignored on both sides (so `"/plants/7/"` and `"plants/7"`
are the same path), and the empty pattern `""` matches the root path `"/"`.

**Example:** with the table of test 1, `resolve(routes, "/plants/7/")` → `["plant_detail", {"plant_id": 7}]`

**Example:** `resolve(routes, "/rooms/kitchen/plants/12/")` → `["room_plant", {"room": "kitchen", "plant_id": 12}]`
""",
    starter='''def resolve(routes: list, path: str):
    pass
''',
    solution='''def _segments(text):
    text = text.strip("/")
    return text.split("/") if text else []

def _match(pattern, path):
    expected, actual = _segments(pattern), _segments(path)
    if len(expected) != len(actual):
        return None
    params = {}
    for want, got in zip(expected, actual):
        if want.startswith("<") and want.endswith(">"):
            kind, _, name = want[1:-1].partition(":")
            if kind == "int":
                if not (got.isascii() and got.isdigit()):
                    return None
                params[name] = int(got)
            else:
                if not got:
                    return None
                params[name] = got
        elif want != got:
            return None
    return params

def resolve(routes, path):
    for pattern, name in routes:
        params = _match(pattern, path)
        if params is not None:
            return [name, params]
    return None
''',
    tests=[
        [_ROUTES, "/plants/7/"],
        [_ROUTES, "/rooms/kitchen/plants/12/"],
        [_ROUTES, "/"],
        [_ROUTES, ""],
        [_ROUTES, "/plants/"],
        [_ROUTES, "plants"],
        [_ROUTES, "/plants/new/"],
        [_ROUTES, "/plants/7/water/"],
        [_ROUTES, "/plants/fern/"],
        [_ROUTES, "/plants/7/prune/"],
        [_ROUTES, "/rooms/"],
        [_ROUTES, "/rooms/kitchen/plants/twelve/"],
        [_ROUTES, "/plants/007/"],
        [_ROUTES, "/plants/-7/"],
        [_ROUTES, "/nope/"],
        [[["<str:a>/<str:b>/", "two"], ["<str:a>/", "one"]], "/x/y/"],
        [[["<str:a>/<str:b>/", "two"], ["<str:a>/", "one"]], "/x/"],
        [[["items/<int:id>/", "first"], ["items/<int:id>/", "second"]], "/items/3/"],
        [[], "/anything/"],
    ],
    examples=2,
    wrong_solutions=['''def resolve(routes, path):
    actual = [p for p in path.split("/") if p]
    for pattern, name in routes:
        expected = [p for p in pattern.split("/") if p]
        if len(expected) != len(actual):
            continue
        params, ok = {}, True
        for want, got in zip(expected, actual):
            if want.startswith("<"):
                kind, _, key = want[1:-1].partition(":")
                params[key] = int(got) if kind == "int" and got.isdigit() else got
            elif want != got:
                ok = False
        if ok:
            return [name, params]
    return None
''', '''def resolve(routes, path):
    actual = [p for p in path.split("/") if p]
    best = None
    for pattern, name in routes:
        expected = [p for p in pattern.split("/") if p]
        if len(expected) != len(actual):
            continue
        params, ok = {}, True
        for want, got in zip(expected, actual):
            if want.startswith("<"):
                kind, _, key = want[1:-1].partition(":")
                if kind == "int":
                    if not got.isdigit():
                        ok = False
                        break
                    params[key] = int(got)
                else:
                    params[key] = got
            elif want != got:
                ok = False
                break
        if ok:
            best = [name, params]
    return best
'''],
    guide=dict(
        prereqs="Lesson *A web application with Django* — URL patterns and path converters.",
        intuition="Split both the pattern and the path into segments and compare them pairwise. A fixed segment must be equal; a converter segment must be acceptable to its type and contributes a captured value. Try the patterns in order and stop at the first success.",
        hints=["`text.strip(\"/\").split(\"/\")` gives the segments — but handle the empty path, where `\"\".split(\"/\")` is `[\"\"]`.", "Different numbers of segments can never match.", "For `<int:name>`, require `segment.isdigit()` and store `int(segment)`; otherwise this *pattern* fails and you move on to the next one.", "Return as soon as one pattern matches."],
        brute_force="Translating each pattern into a regular expression (`<int:id>` → `(?P<id>\\d+)`) and using `re.fullmatch` is what real frameworks do; segment comparison is simpler to get right here.",
        approach="1. Helper `segments(text)`.\n2. Helper `match(pattern, path)` → dict of params or `None`.\n3. `resolve` loops over the table and returns `[name, params]` for the first non-`None` match.",
        complexity="O(routes × segments).",
        pitfalls="- A failed `int` conversion must reject the pattern, not fall back to a string.\n- Returning the *last* match instead of the first.\n- The root path: both `\"/\"` and `\"\"` have zero segments.\n- `/plants/new/` vs `/plants/<int:plant_id>/`: order in the table decides when patterns overlap.\n- `-7` is not all digits, so it is not an int segment.",
        follow_up="Add a `<slug:...>` converter (letters, digits, hyphens) and `reverse(name, params)` to build a path from a route name.",
    ),
),
dict(
    id="py-proj-text-chart",
    title="Text Bar Chart",
    difficulty="Easy",
    pattern="Formatting & Scaling",
    entry="bar_chart",
    description=r"""
Write `bar_chart(data, width)` that turns a list of `[label, value]` pairs (values are non-negative
whole numbers) into a list of text lines forming a horizontal bar chart, one line per pair, in the
given order.

Each line has the form

```
<label padded on the right to the longest label> | <bar> <value>
```

- The bar is made of `#` characters. The largest value gets a bar of exactly `width` characters;
  every other bar is scaled proportionally and **rounded to the nearest whole number, halves rounding
  up**: `length = (value * width * 2 + largest) // (2 * largest)`.
- If the largest value is 0, every bar is empty.
- When the bar is empty the line is `<label> |  <value>` (note the two spaces: an empty bar between them).
- For an empty `data` list return `[]`.

**Example:** `bar_chart([["ana", 30], ["ben", 15], ["cy", 0]], 10)` →
`["ana | ########## 30", "ben | ##### 15", "cy  |  0"]`
""",
    starter='''def bar_chart(data: list, width: int) -> list:
    pass
''',
    solution='''def bar_chart(data, width):
    if not data:
        return []
    largest = max(value for _, value in data)
    label_width = max(len(label) for label, _ in data)
    lines = []
    for label, value in data:
        length = (value * width * 2 + largest) // (2 * largest) if largest else 0
        lines.append(f"{label:<{label_width}} | {'#' * length} {value}")
    return lines
''',
    tests=[
        [[["ana", 30], ["ben", 15], ["cy", 0]], 10],
        [[], 10],
        [[["only", 7]], 5],
        [[["a", 0], ["bb", 0]], 8],
        [[["x", 1], ["y", 2], ["z", 3]], 3],
        [[["x", 1], ["y", 3]], 10],
        [[["x", 1], ["y", 4]], 10],
        [[["long label", 5], ["s", 10]], 4],
        [[["a", 1], ["b", 1000]], 20],
        [[["a", 499], ["b", 1000]], 2],
        [[["a", 500], ["b", 1000]], 1],
        [[[f"row{i}", (i * 37) % 23] for i in range(25)], 30],
    ],
    examples=1,
    wrong_solutions=['''def bar_chart(data, width):
    if not data:
        return []
    largest = max(v for _, v in data)
    lw = max(len(l) for l, _ in data)
    return [f"{l:<{lw}} | {'#' * (v * width // largest if largest else 0)} {v}" for l, v in data]
''', '''def bar_chart(data, width):
    if not data:
        return []
    largest = max(v for _, v in data)
    return [f"{l} | {'#' * ((v * width * 2 + largest) // (2 * largest) if largest else 0)} {v}" for l, v in data]
'''],
    guide=dict(
        prereqs="Lesson *Data visualisation* — scaling values to the available space; f-string padding.",
        intuition="Every chart does the same two things: **scale** a value into the drawing space (value ÷ largest × width) and **draw** a mark of that size. Aligning the labels just needs the length of the longest one.",
        hints=["Find `largest` and the longest label length first.", "Use the given integer formula for the bar length — it avoids floating-point rounding surprises.", "`f\"{label:<{label_width}}\"` pads the label on the right.", "Guard against `largest == 0` before dividing."],
        brute_force="`round(value / largest * width)` looks equivalent but Python's `round` sends halves to the nearest *even* number (banker's rounding), so some bars come out one character short.",
        approach="1. Empty input → `[]`.\n2. Compute `largest` and `label_width`.\n3. For each pair compute the length and build `f\"{label:<{label_width}} | {'#' * length} {value}\"`.",
        complexity="O(n + total characters produced).",
        pitfalls="- Division by zero when all values are 0.\n- Floor division alone rounds down instead of to nearest.\n- Forgetting to pad labels misaligns the bars.\n- `round()` uses round-half-to-even.",
        follow_up="Add a `sort` flag, or draw vertical bars by building the chart row by row from the top.",
    ),
),
]
