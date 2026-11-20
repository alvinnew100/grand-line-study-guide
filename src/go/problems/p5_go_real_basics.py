"""Real Go problems, part 1 (kind="go"): judged on the server by compiling solution.go with a main.go harness.

The learner writes ordinary Go in package main. The harness below runs one closure per test case,
recovers from panics, and prints exactly one line per case: "CASE n OK" or "CASE n FAIL ...".
"""


def harness(checks, imports=(), pre=""):
    """Build main.go. Each check is (got_expr, want_expr) or a string holding a full closure body."""
    imps = sorted(set(["fmt"]) | set(imports))
    lines = ["package main", "", "import ("]
    lines += ['\t"%s"' % i for i in imps]
    lines += [
        ")", "",
        "var caseNo int", "",
        "func check(f func() (any, any)) {",
        "\tcaseNo++",
        "\tdefer func() {",
        "\t\tif r := recover(); r != nil {",
        '\t\t\tfmt.Println("CASE", caseNo, "FAIL", "panic:", r)',
        "\t\t}",
        "\t}()",
        "\tgot, want := f()",
        "\tif fmt.Sprint(got) == fmt.Sprint(want) {",
        '\t\tfmt.Println("CASE", caseNo, "OK")',
        "\t} else {",
        '\t\tfmt.Println("CASE", caseNo, "FAIL", "got", got, "want", want)',
        "\t}",
        "}", "",
    ]
    if pre:
        lines += [pre.strip("\n"), ""]
    lines.append("func main() {")
    for c in checks:
        if isinstance(c, str):
            lines.append("\tcheck(func() (any, any) { %s })" % c)
        else:
            lines.append("\tcheck(func() (any, any) { return %s, %s })" % c)
    lines.append("}")
    return "\n".join(lines) + "\n"


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute,
                approach=approach, complexity=complexity, pitfalls=pitfalls)


LOGIN = "\n\n*This problem is compiled and run as real Go on the judge server, so you need to be logged in to run it.*\n"

PROBLEMS = [
# ------------------------------------------------------------------ 1
dict(
    id="go-real-c-to-f", title="Celsius to Fahrenheit", difficulty="Easy", pattern="Go basics", kind="go", cases=8,
    description=r"""
Write `func CToF(c float64) float64` in `solution.go` that converts a temperature from degrees Celsius to
degrees Fahrenheit using `F = C × 9 / 5 + 32`.

**Examples:** `CToF(0)` → `32`, `CToF(100)` → `212`, `CToF(-40)` → `-40`.

The tests compare results rounded to two decimals, so tiny floating-point differences do not matter.
""" + LOGIN,
    starter="package main\n\n// CToF converts degrees Celsius to degrees Fahrenheit.\nfunc CToF(c float64) float64 {\n\t// your code\n\treturn 0\n}\n",
    solution="package main\n\n// CToF converts degrees Celsius to degrees Fahrenheit.\nfunc CToF(c float64) float64 {\n\treturn c*9/5 + 32\n}\n",
    wrong_solutions=[
        "package main\n\nfunc CToF(c float64) float64 {\n\treturn float64(int(c)*9/5 + 32)\n}\n",
        "package main\n\nfunc CToF(c float64) float64 {\n\treturn (c + 32) * 9 / 5\n}\n",
    ],
    harness=harness([
        ("r2(CToF(0))", "32.0"), ("r2(CToF(100))", "212.0"), ("r2(CToF(-40))", "-40.0"), ("r2(CToF(37))", "98.6"),
        ("r2(CToF(36.6))", "97.88"), ("r2(CToF(-273.15))", "-459.67"), ("r2(CToF(0.5))", "32.9"), ("r2(CToF(1000))", "1832.0"),
    ], imports=["math"], pre="func r2(x float64) float64 { return math.Round(x*100) / 100 }"),
    guide=G(
        "Variables, `float64` and arithmetic: [Predeclared types, zero values and conversions](#/lesson/go/go-predeclared-types).",
        "A formula is a one-line function. The only thing to watch is the type: with `float64` operands, `/` keeps the fraction.",
        ["The parameter `c` is already a `float64`, so `c*9/5` is floating-point arithmetic.",
         "Do not convert to `int` anywhere; integer division throws the fraction away.",
         "Return `c*9/5 + 32`."],
        "There is nothing slower to compare with; the task is a direct formula.",
        "Multiply by 9, divide by 5, add 32.\n\n**Dry run:** `CToF(37)` → `37*9 = 333`, `333/5 = 66.6`, `66.6 + 32 = 98.6`.\n\n"
        "```go\nfunc CToF(c float64) float64 {\n\treturn c*9/5 + 32\n}\n```",
        "O(1) time and space.",
        "Converting to `int` first (36.6 would become 36). Writing `9/5` with integer constants inside a typed integer "
        "expression. Applying the offset before the scaling.",
    ),
),
# ------------------------------------------------------------------ 2
dict(
    id="go-real-split-seconds", title="Hours, minutes, seconds (multiple returns)", difficulty="Easy", pattern="Go functions", kind="go", cases=8,
    description=r"""
Write `func SplitSeconds(total int) (hours, minutes, seconds int)` that splits a non-negative number of
seconds into whole hours, remaining minutes (0–59) and remaining seconds (0–59).

**Example:** `SplitSeconds(3725)` → `1, 2, 5` (1 hour, 2 minutes, 5 seconds).

This exercises a Go feature Python does differently: a function with **three return values**.
""" + LOGIN,
    starter="package main\n\n// SplitSeconds splits total seconds into hours, minutes and seconds.\nfunc SplitSeconds(total int) (hours, minutes, seconds int) {\n\t// your code\n\treturn 0, 0, 0\n}\n",
    solution="package main\n\n// SplitSeconds splits total seconds into hours, minutes and seconds.\nfunc SplitSeconds(total int) (hours, minutes, seconds int) {\n\thours = total / 3600\n\tminutes = total % 3600 / 60\n\tseconds = total % 60\n\treturn hours, minutes, seconds\n}\n",
    wrong_solutions=[
        "package main\n\nfunc SplitSeconds(total int) (int, int, int) {\n\treturn total / 3600, total / 60, total % 60\n}\n",
    ],
    harness=harness([
        ("fmt.Sprint(SplitSeconds(3725))", '"1 2 5"'), ("fmt.Sprint(SplitSeconds(0))", '"0 0 0"'),
        ("fmt.Sprint(SplitSeconds(59))", '"0 0 59"'), ("fmt.Sprint(SplitSeconds(60))", '"0 1 0"'),
        ("fmt.Sprint(SplitSeconds(3599))", '"0 59 59"'), ("fmt.Sprint(SplitSeconds(3600))", '"1 0 0"'),
        ("fmt.Sprint(SplitSeconds(86399))", '"23 59 59"'), ("fmt.Sprint(SplitSeconds(360000))", '"100 0 0"'),
    ]),
    guide=G(
        "Integer division and remainder, multiple return values: [Declaring and calling functions](#/lesson/go/go-functions-basics).",
        "Integer division `/` answers 'how many whole groups fit' and `%` answers 'what is left over'. Peel off hours, then minutes from the remainder.",
        ["There are 3600 seconds in an hour and 60 in a minute.", "`total % 3600` is what remains after removing whole hours.",
         "Minutes are `total % 3600 / 60`; seconds are `total % 60`."],
        "A loop that subtracts 3600 while possible, then 60, works and takes time proportional to the answer; division does it in one step.",
        "Three expressions, returned together.\n\n**Dry run:** 3725 → `3725/3600 = 1`; `3725%3600 = 125`, `125/60 = 2`; `3725%60 = 5`.\n\n"
        "```go\nfunc SplitSeconds(total int) (hours, minutes, seconds int) {\n\thours = total / 3600\n\tminutes = total % 3600 / 60\n\tseconds = total % 60\n\treturn hours, minutes, seconds\n}\n```\n\n"
        "The caller writes `h, m, s := SplitSeconds(3725)`.",
        "O(1).",
        "Returning total minutes (`total/60`) instead of the minutes within the hour. Mixing up the order of the results.",
    ),
),
# ------------------------------------------------------------------ 3
dict(
    id="go-real-fizzbuzz", title="FizzBuzz into a slice", difficulty="Easy", pattern="Go control flow", kind="go", cases=8,
    description=r"""
Write `func FizzBuzz(n int) []string` returning the FizzBuzz sequence for 1 to `n`:

- `"FizzBuzz"` for multiples of both 3 and 5,
- `"Fizz"` for other multiples of 3,
- `"Buzz"` for other multiples of 5,
- otherwise the number itself as text (use `strconv.Itoa`).

For `n <= 0` return an empty slice.

**Example:** `FizzBuzz(5)` → `["1", "2", "Fizz", "4", "Buzz"]`
""" + LOGIN,
    starter="package main\n\n// FizzBuzz returns the FizzBuzz sequence from 1 to n.\nfunc FizzBuzz(n int) []string {\n\t// your code\n\treturn nil\n}\n",
    solution='package main\n\nimport "strconv"\n\n// FizzBuzz returns the FizzBuzz sequence from 1 to n.\nfunc FizzBuzz(n int) []string {\n\tout := []string{}\n\tfor i := 1; i <= n; i++ {\n\t\tswitch {\n\t\tcase i%15 == 0:\n\t\t\tout = append(out, "FizzBuzz")\n\t\tcase i%3 == 0:\n\t\t\tout = append(out, "Fizz")\n\t\tcase i%5 == 0:\n\t\t\tout = append(out, "Buzz")\n\t\tdefault:\n\t\t\tout = append(out, strconv.Itoa(i))\n\t\t}\n\t}\n\treturn out\n}\n',
    wrong_solutions=[
        'package main\n\nimport "strconv"\n\nfunc FizzBuzz(n int) []string {\n\tvar out []string\n\tfor i := 1; i <= n; i++ {\n\t\tswitch {\n\t\tcase i%3 == 0:\n\t\t\tout = append(out, "Fizz")\n\t\tcase i%5 == 0:\n\t\t\tout = append(out, "Buzz")\n\t\tcase i%15 == 0:\n\t\t\tout = append(out, "FizzBuzz")\n\t\tdefault:\n\t\t\tout = append(out, strconv.Itoa(i))\n\t\t}\n\t}\n\treturn out\n}\n',
        'package main\n\nimport "strconv"\n\nfunc FizzBuzz(n int) []string {\n\tout := make([]string, n)\n\tfor i := 1; i < n; i++ {\n\t\tout[i] = strconv.Itoa(i)\n\t}\n\treturn out\n}\n',
    ],
    harness=harness([
        ("FizzBuzz(5)", '[]string{"1", "2", "Fizz", "4", "Buzz"}'), ("len(FizzBuzz(0))", "0"), ("len(FizzBuzz(-3))", "0"),
        ("FizzBuzz(1)", '[]string{"1"}'), ("FizzBuzz(15)[14]", '"FizzBuzz"'), ("FizzBuzz(15)[9]", '"Buzz"'),
        ("len(FizzBuzz(100))", "100"), ('strings.Join(FizzBuzz(30)[26:], ",")', '"Fizz,28,29,FizzBuzz"'),
    ], imports=["strings"]),
    guide=G(
        "`for` loops, tagless `switch`, `append`: [for, switch and goto](#/lesson/go/go-for-switch), [Arrays and slices](#/lesson/go/go-arrays-slices).",
        "Check the most specific condition first. A number divisible by 15 is also divisible by 3, so the 15 test must come before the 3 test.",
        ["Loop `for i := 1; i <= n; i++`.", "A `switch` with no value lets each `case` be a condition; the first true one wins.",
         "Put `i%15 == 0` first, then `i%3`, then `i%5`, then `default` with `strconv.Itoa(i)`."],
        "Building one long string and splitting it afterwards works but adds needless steps.",
        "Create a slice with capacity `n`, loop, and `append` one string per number.\n\n**Dry run:** `i=3` → `3%15 != 0`, `3%3 == 0` → `Fizz`. `i=15` → first case → `FizzBuzz`.\n\n"
        '```go\nfor i := 1; i <= n; i++ {\n\tswitch {\n\tcase i%15 == 0:\n\t\tout = append(out, "FizzBuzz")\n\tcase i%3 == 0:\n\t\tout = append(out, "Fizz")\n\tcase i%5 == 0:\n\t\tout = append(out, "Buzz")\n\tdefault:\n\t\tout = append(out, strconv.Itoa(i))\n\t}\n}\n```',
        "O(n) time and space.",
        "Testing 3 before 15. `make([]string, n)` followed by `append` (leaves n empty strings in front). Using `string(i)`, which gives a character, not digits. `make` with a negative length panics.",
    ),
),
# ------------------------------------------------------------------ 4
dict(
    id="go-real-is-prime", title="Is it prime?", difficulty="Easy", pattern="Go control flow", kind="go", cases=10,
    description=r"""
Write `func IsPrime(n int) bool` that reports whether `n` is a prime number: an integer greater than 1 whose
only divisors are 1 and itself. Numbers below 2, including negatives, are not prime.

**Examples:** `IsPrime(2)` → `true`, `IsPrime(9)` → `false`, `IsPrime(97)` → `true`.

The tests include numbers around a billion, so trying every divisor up to `n` is too slow.
""" + LOGIN,
    starter="package main\n\n// IsPrime reports whether n is prime.\nfunc IsPrime(n int) bool {\n\t// your code\n\treturn false\n}\n",
    solution="package main\n\n// IsPrime reports whether n is prime.\nfunc IsPrime(n int) bool {\n\tif n < 2 {\n\t\treturn false\n\t}\n\tfor d := 2; d*d <= n; d++ {\n\t\tif n%d == 0 {\n\t\t\treturn false\n\t\t}\n\t}\n\treturn true\n}\n",
    wrong_solutions=[
        "package main\n\nfunc IsPrime(n int) bool {\n\tfor d := 2; d*d < n; d++ {\n\t\tif n%d == 0 {\n\t\t\treturn false\n\t\t}\n\t}\n\treturn n >= 2\n}\n",
        "package main\n\nfunc IsPrime(n int) bool {\n\tif n%2 == 0 {\n\t\treturn false\n\t}\n\tfor d := 3; d*d <= n; d += 2 {\n\t\tif n%d == 0 {\n\t\t\treturn false\n\t\t}\n\t}\n\treturn true\n}\n",
    ],
    harness=harness([
        ("IsPrime(2)", "true"), ("IsPrime(3)", "true"), ("IsPrime(4)", "false"), ("IsPrime(1)", "false"), ("IsPrime(0)", "false"),
        ("IsPrime(-7)", "false"), ("IsPrime(97)", "true"), ("IsPrime(49)", "false"), ("IsPrime(1000000007)", "true"),
        ("IsPrime(999999999)", "false"),
    ]),
    guide=G(
        "Loops and the remainder operator: [for, switch and goto](#/lesson/go/go-for-switch).",
        "Divisors come in pairs: if `d` divides `n`, so does `n/d`, and one of the two is at most the square root of `n`. So it is enough to test divisors up to √n.",
        ["Handle `n < 2` first.", "Loop while `d*d <= n`; that avoids computing a square root.", "Return `false` at the first divisor found, `true` after the loop."],
        "Testing every `d` from 2 to `n-1` is O(n): about a billion steps for the largest test.",
        "Trial division up to the square root.\n\n**Dry run:** `n = 49`: d=2..6 do not divide; d=7: `7*7 <= 49` and `49%7 == 0` → false. A loop with `d*d < n` would stop before 7 and wrongly say prime.\n\n"
        "```go\nfunc IsPrime(n int) bool {\n\tif n < 2 {\n\t\treturn false\n\t}\n\tfor d := 2; d*d <= n; d++ {\n\t\tif n%d == 0 {\n\t\t\treturn false\n\t\t}\n\t}\n\treturn true\n}\n```",
        "O(√n) time, O(1) space.",
        "Using `<` instead of `<=` in the loop condition (squares of primes slip through). Forgetting 0, 1 and negatives. Special-casing even numbers and then calling 2 composite.",
    ),
),
# ------------------------------------------------------------------ 5
dict(
    id="go-real-grade", title="Letter grade with switch", difficulty="Easy", pattern="Go control flow", kind="go", cases=10,
    description=r"""
Write `func Grade(score int) string`:

| score | result |
|---|---|
| 90–100 | `"A"` |
| 80–89 | `"B"` |
| 70–79 | `"C"` |
| 60–69 | `"D"` |
| 0–59 | `"F"` |
| below 0 or above 100 | `"invalid"` |

Use a `switch` with no tag value (each `case` is a condition).
""" + LOGIN,
    starter="package main\n\n// Grade converts a score from 0 to 100 into a letter.\nfunc Grade(score int) string {\n\t// your code\n\treturn \"\"\n}\n",
    solution='package main\n\n// Grade converts a score from 0 to 100 into a letter.\nfunc Grade(score int) string {\n\tswitch {\n\tcase score < 0 || score > 100:\n\t\treturn "invalid"\n\tcase score >= 90:\n\t\treturn "A"\n\tcase score >= 80:\n\t\treturn "B"\n\tcase score >= 70:\n\t\treturn "C"\n\tcase score >= 60:\n\t\treturn "D"\n\tdefault:\n\t\treturn "F"\n\t}\n}\n',
    wrong_solutions=[
        'package main\n\nfunc Grade(score int) string {\n\tswitch {\n\tcase score >= 60:\n\t\treturn "D"\n\tcase score >= 70:\n\t\treturn "C"\n\tcase score >= 80:\n\t\treturn "B"\n\tcase score >= 90:\n\t\treturn "A"\n\tcase score < 0 || score > 100:\n\t\treturn "invalid"\n\tdefault:\n\t\treturn "F"\n\t}\n}\n',
        'package main\n\nfunc Grade(score int) string {\n\tswitch {\n\tcase score > 90:\n\t\treturn "A"\n\tcase score > 80:\n\t\treturn "B"\n\tcase score > 70:\n\t\treturn "C"\n\tcase score > 60:\n\t\treturn "D"\n\tcase score < 0 || score > 100:\n\t\treturn "invalid"\n\tdefault:\n\t\treturn "F"\n\t}\n}\n',
    ],
    harness=harness([
        ("Grade(95)", '"A"'), ("Grade(90)", '"A"'), ("Grade(89)", '"B"'), ("Grade(80)", '"B"'), ("Grade(70)", '"C"'),
        ("Grade(60)", '"D"'), ("Grade(59)", '"F"'), ("Grade(0)", '"F"'), ("Grade(101)", '"invalid"'), ("Grade(-1)", '"invalid"'),
    ]),
    guide=G(
        "Tagless `switch`: [for, switch and goto](#/lesson/go/go-for-switch).",
        "Cases are tried top to bottom and the first true one wins, so order them from the most restrictive to the least, with the invalid range first.",
        ["Start with the invalid check.", "Then `>= 90`, `>= 80`, and so on downwards.", "`default` covers everything left: 0 to 59."],
        "A chain of `if score >= 90 && score <= 100` conditions works; the switch says the same with less repetition.",
        "**Dry run:** 80 → not invalid, not `>= 90`, `>= 80` is true → `B`. No `break` is needed: Go leaves the switch after a case.\n\n"
        '```go\nswitch {\ncase score < 0 || score > 100:\n\treturn "invalid"\ncase score >= 90:\n\treturn "A"\ncase score >= 80:\n\treturn "B"\ncase score >= 70:\n\treturn "C"\ncase score >= 60:\n\treturn "D"\ndefault:\n\treturn "F"\n}\n```',
        "O(1).",
        "Wrong order of cases. `>` where `>=` is needed (boundary values 90, 80, 70, 60). Checking validity last, after 101 has already matched `>= 90`.",
    ),
),
# ------------------------------------------------------------------ 6
dict(
    id="go-real-safe-div", title="Division that returns an error", difficulty="Easy", pattern="Go errors", kind="go", cases=8,
    description=r"""
In Go, a function that can fail returns an `error` as its last result.

In `solution.go` declare a package-level sentinel error

```go
var ErrDivByZero = errors.New("division by zero")
```

and write `func SafeDiv(a, b int) (int, error)`:

- if `b` is 0, return `0` and `ErrDivByZero`;
- otherwise return `a / b` (Go's integer division, which truncates toward zero) and `nil`.
""" + LOGIN,
    starter='package main\n\nimport "errors"\n\n// ErrDivByZero is returned when the divisor is zero.\nvar ErrDivByZero = errors.New("division by zero")\n\n// SafeDiv divides a by b.\nfunc SafeDiv(a, b int) (int, error) {\n\t// your code\n\treturn 0, nil\n}\n',
    solution='package main\n\nimport "errors"\n\n// ErrDivByZero is returned when the divisor is zero.\nvar ErrDivByZero = errors.New("division by zero")\n\n// SafeDiv divides a by b.\nfunc SafeDiv(a, b int) (int, error) {\n\tif b == 0 {\n\t\treturn 0, ErrDivByZero\n\t}\n\treturn a / b, nil\n}\n',
    wrong_solutions=[
        'package main\n\nimport "errors"\n\nvar ErrDivByZero = errors.New("division by zero")\n\nfunc SafeDiv(a, b int) (int, error) {\n\tif b == 0 {\n\t\treturn 0, errors.New("division by zero")\n\t}\n\treturn a / b, nil\n}\n',
        'package main\n\nimport "errors"\n\nvar ErrDivByZero = errors.New("division by zero")\n\nfunc SafeDiv(a, b int) (int, error) {\n\tif a == 0 {\n\t\treturn 0, ErrDivByZero\n\t}\n\treturn a / b, nil\n}\n',
    ],
    harness=harness([
        ("div(10, 2)", '"5"'), ("div(7, 2)", '"3"'), ("div(-7, 2)", '"-3"'), ("div(1, 0)", '"ErrDivByZero"'),
        ("div(0, 0)", '"ErrDivByZero"'), ("div(0, 5)", '"0"'), ("div(9, -3)", '"-3"'), ("ErrDivByZero.Error()", '"division by zero"'),
    ], imports=["errors"], pre='''func div(a, b int) string {
	q, err := SafeDiv(a, b)
	if err != nil {
		if errors.Is(err, ErrDivByZero) {
			return "ErrDivByZero"
		}
		return "some other error"
	}
	return fmt.Sprint(q)
}'''),
    guide=G(
        "[Errors are values](#/lesson/go/go-errors-values): the `error` type, sentinel errors, `nil` for success.",
        "Go has no exceptions for ordinary failures. Check the bad case first, return the zero value plus the error; otherwise return the result plus `nil`.",
        ["Compare `b` with 0 before dividing; dividing by zero would panic.", "Return the **same** `ErrDivByZero` variable each time so callers can compare against it.",
         "The success path is `return a / b, nil`."],
        "Not applicable.",
        "**Dry run:** `SafeDiv(1, 0)` → `b == 0` → `0, ErrDivByZero`. `SafeDiv(-7, 2)` → `-3, nil` (truncation toward zero).\n\n"
        '```go\nvar ErrDivByZero = errors.New("division by zero")\n\nfunc SafeDiv(a, b int) (int, error) {\n\tif b == 0 {\n\t\treturn 0, ErrDivByZero\n\t}\n\treturn a / b, nil\n}\n```\n\n'
        "A caller writes `q, err := SafeDiv(x, y); if err != nil { ... }`.",
        "O(1).",
        "Creating a new error with `errors.New` inside the function: it has the same text but is a different value, so `errors.Is(err, ErrDivByZero)` is false. Checking `a` instead of `b`.",
    ),
),
# ------------------------------------------------------------------ 7
dict(
    id="go-real-reverse-runes", title="Reverse a string by characters", difficulty="Easy", pattern="Go strings", kind="go", cases=9,
    description=r"""
Write `func ReverseString(s string) string` that returns the characters of `s` in reverse order.

A Go string is a sequence of **bytes**, and characters outside plain English take more than one byte. Reversing
bytes would break them. Reverse **runes** (Unicode code points) instead.

**Examples:** `ReverseString("hello")` → `"olleh"`, `ReverseString("héllo")` → `"olléh"`, `ReverseString("世界")` → `"界世"`.
""" + LOGIN,
    starter="package main\n\n// ReverseString returns s with its characters in reverse order.\nfunc ReverseString(s string) string {\n\t// your code\n\treturn s\n}\n",
    solution="package main\n\n// ReverseString returns s with its characters in reverse order.\nfunc ReverseString(s string) string {\n\tr := []rune(s)\n\tfor i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {\n\t\tr[i], r[j] = r[j], r[i]\n\t}\n\treturn string(r)\n}\n",
    wrong_solutions=[
        "package main\n\nfunc ReverseString(s string) string {\n\tb := []byte(s)\n\tfor i, j := 0, len(b)-1; i < j; i, j = i+1, j-1 {\n\t\tb[i], b[j] = b[j], b[i]\n\t}\n\treturn string(b)\n}\n",
        "package main\n\nfunc ReverseString(s string) string {\n\tr := []rune(s)\n\tfor i := 0; i < len(r); i++ {\n\t\tr[i], r[len(r)-1-i] = r[len(r)-1-i], r[i]\n\t}\n\treturn string(r)\n}\n",
    ],
    harness=harness([
        ('ReverseString("hello")', '"olleh"'), ('ReverseString("")', '""'), ('ReverseString("a")', '"a"'),
        ('ReverseString("ab")', '"ba"'), ('ReverseString("héllo")', '"olléh"'), ('ReverseString("世界")', '"界世"'),
        ('ReverseString("Go 🙂!")', '"!🙂 oG"'), ('ReverseString("racecar")', '"racecar"'), ('ReverseString(ReverseString("añb"))', '"añb"'),
    ]),
    guide=G(
        "[Strings, runes and bytes](#/lesson/go/go-strings-runes).",
        "Convert to `[]rune` so that each element is one whole character, swap from both ends toward the middle, convert back.",
        ["`[]rune(s)` decodes the UTF-8 bytes into code points.", "Use two indexes `i` and `j` moving toward each other.", "Stop when `i >= j`; going further swaps everything back."],
        "Appending characters one by one to a new string from the end is O(n²), because each `+=` copies the string.",
        "**Dry run:** `héllo` → runes `[h é l l o]`; swap ends → `[o é l l h]`; swap inner → `[o l l é h]`; middle stays.\n\n"
        "```go\nfunc ReverseString(s string) string {\n\tr := []rune(s)\n\tfor i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {\n\t\tr[i], r[j] = r[j], r[i]\n\t}\n\treturn string(r)\n}\n```",
        "O(n) time and space.",
        "Reversing bytes (breaks `é`, `世`, emoji). Looping `i` over the whole slice, which swaps each pair twice and returns the original.",
    ),
),
# ------------------------------------------------------------------ 8
dict(
    id="go-real-word-freq", title="Word frequencies with a map", difficulty="Easy", pattern="Go maps", kind="go", cases=8,
    description=r"""
Write `func WordFreq(text string) map[string]int` that counts how often each word occurs.

- Words are separated by any whitespace (use `strings.Fields`).
- Counting ignores case: convert each word to lower case with `strings.ToLower`.
- An empty text gives an empty (non-nil) map.

**Example:** `WordFreq("the cat The hat")` → `map[cat:1 hat:1 the:2]`
""" + LOGIN,
    starter="package main\n\n// WordFreq counts the words of text, ignoring case.\nfunc WordFreq(text string) map[string]int {\n\t// your code\n\treturn nil\n}\n",
    solution='package main\n\nimport "strings"\n\n// WordFreq counts the words of text, ignoring case.\nfunc WordFreq(text string) map[string]int {\n\tcounts := make(map[string]int)\n\tfor _, w := range strings.Fields(text) {\n\t\tcounts[strings.ToLower(w)]++\n\t}\n\treturn counts\n}\n',
    wrong_solutions=[
        'package main\n\nimport "strings"\n\nfunc WordFreq(text string) map[string]int {\n\tcounts := make(map[string]int)\n\tfor _, w := range strings.Split(text, " ") {\n\t\tcounts[w]++\n\t}\n\treturn counts\n}\n',
        'package main\n\nimport "strings"\n\nfunc WordFreq(text string) map[string]int {\n\tcounts := make(map[string]int)\n\tfor _, w := range strings.Fields(text) {\n\t\tcounts[strings.ToLower(w)] = 1\n\t}\n\treturn counts\n}\n',
    ],
    harness=harness([
        ('WordFreq("the cat The hat")', 'map[string]int{"cat": 1, "hat": 1, "the": 2}'), ('len(WordFreq(""))', "0"),
        ('WordFreq("") != nil', "true"), ('WordFreq("go")', 'map[string]int{"go": 1}'),
        ('WordFreq("a  a\\ta\\na")', 'map[string]int{"a": 4}'), ('WordFreq("Go GO go gO")["go"]', "4"),
        ('WordFreq("   ")', "map[string]int{}"), ('len(WordFreq("one two three two three three"))', "3"),
    ]),
    guide=G(
        "[Maps and structs](#/lesson/go/go-maps-structs): creating maps, zero values for missing keys.",
        "A missing key reads as 0, so `counts[word]++` works for the first occurrence and for all later ones with no special case.",
        ["Create the map with `make`; writing to a nil map panics.", "`strings.Fields` splits on any run of spaces, tabs and newlines and never yields empty strings.", "Lower-case the word before using it as the key."],
        "For each word, scanning the whole list to count it is O(n²).",
        "**Dry run:** `the cat The hat` → fields `[the cat The hat]` → keys `the, cat, the, hat` → `{the:2, cat:1, hat:1}`.\n\n"
        '```go\nfunc WordFreq(text string) map[string]int {\n\tcounts := make(map[string]int)\n\tfor _, w := range strings.Fields(text) {\n\t\tcounts[strings.ToLower(w)]++\n\t}\n\treturn counts\n}\n```',
        "O(n) in the length of the text.",
        "`strings.Split(text, \" \")` produces empty strings for double spaces and does not split on tabs or newlines. Returning a nil map. Forgetting to fold case.",
    ),
),
# ------------------------------------------------------------------ 9
dict(
    id="go-real-dedupe", title="Remove duplicates, keep order", difficulty="Easy", pattern="Go slices", kind="go", cases=8,
    description=r"""
Write `func Dedupe(xs []int) []int` that returns the distinct values of `xs` in the order of their first
appearance. **The input slice must not be modified.**

**Example:** `Dedupe([]int{3, 1, 3, 2, 1})` → `[3 1 2]`
""" + LOGIN,
    starter="package main\n\n// Dedupe returns the distinct values of xs in first-seen order.\nfunc Dedupe(xs []int) []int {\n\t// your code\n\treturn nil\n}\n",
    solution="package main\n\n// Dedupe returns the distinct values of xs in first-seen order.\nfunc Dedupe(xs []int) []int {\n\tseen := make(map[int]bool, len(xs))\n\tout := make([]int, 0, len(xs))\n\tfor _, x := range xs {\n\t\tif !seen[x] {\n\t\t\tseen[x] = true\n\t\t\tout = append(out, x)\n\t\t}\n\t}\n\treturn out\n}\n",
    wrong_solutions=[
        'package main\n\nimport "sort"\n\nfunc Dedupe(xs []int) []int {\n\tsort.Ints(xs)\n\tvar out []int\n\tfor i, x := range xs {\n\t\tif i == 0 || x != xs[i-1] {\n\t\t\tout = append(out, x)\n\t\t}\n\t}\n\treturn out\n}\n',
        "package main\n\nfunc Dedupe(xs []int) []int {\n\tout := xs[:0]\n\tseen := map[int]bool{}\n\tfor _, x := range xs {\n\t\tif !seen[x] {\n\t\t\tseen[x] = true\n\t\t\tout = append(out, x)\n\t\t}\n\t}\n\treturn out\n}\n",
    ],
    harness=harness([
        ("Dedupe([]int{3, 1, 3, 2, 1})", "[]int{3, 1, 2}"), ("len(Dedupe(nil))", "0"), ("Dedupe([]int{7})", "[]int{7}"),
        ("Dedupe([]int{5, 5, 5, 5})", "[]int{5}"), ("Dedupe([]int{1, 2, 3})", "[]int{1, 2, 3}"),
        ("Dedupe([]int{0, -1, 0, -1, 2})", "[]int{0, -1, 2}"),
        "in := []int{4, 4, 9, 4, 1}; _ = Dedupe(in); return in, []int{4, 4, 9, 4, 1}",
        "in := []int{2, 1, 2}; out := Dedupe(in); out[0] = 99; return in, []int{2, 1, 2}",
    ]),
    guide=G(
        "[Maps and structs](#/lesson/go/go-maps-structs) for a set; [Slicing, aliasing and copy](#/lesson/go/go-slicing-aliasing) for why the result must be a new slice.",
        "Walk the input once. A map remembers which values were already emitted; a new slice collects the first occurrences.",
        ["A `map[int]bool` is a set: missing keys read as `false`.", "Append to a **new** slice, not to `xs[:0]`, which shares the input's memory.", "Pre-size with `make([]int, 0, len(xs))`."],
        "For each element, search the output so far: O(n²).",
        "**Dry run:** `[3 1 3 2 1]` → 3 new, 1 new, 3 seen, 2 new, 1 seen → `[3 1 2]`.\n\n"
        "```go\nseen := make(map[int]bool, len(xs))\nout := make([]int, 0, len(xs))\nfor _, x := range xs {\n\tif !seen[x] {\n\t\tseen[x] = true\n\t\tout = append(out, x)\n\t}\n}\nreturn out\n```",
        "O(n) time, O(n) extra space.",
        "Sorting first (changes the order and the caller's slice). Reusing the input's backing array with `xs[:0]`, which overwrites the caller's data.",
    ),
),
# ------------------------------------------------------------------ 10
dict(
    id="go-real-rotate-left", title="Rotate a slice without aliasing", difficulty="Medium", pattern="Go slices", kind="go", cases=9,
    description=r"""
Write `func RotateLeft(xs []int, k int) []int` that returns a **new** slice with the elements of `xs` rotated
left by `k` positions (`k >= 0`, and `k` may be larger than the length). The input must stay unchanged, and
changing the result must not change the input.

**Example:** `RotateLeft([]int{1, 2, 3, 4, 5}, 2)` → `[3 4 5 1 2]`
""" + LOGIN,
    starter="package main\n\n// RotateLeft returns a rotated copy of xs.\nfunc RotateLeft(xs []int, k int) []int {\n\t// your code\n\treturn nil\n}\n",
    solution="package main\n\n// RotateLeft returns a rotated copy of xs.\nfunc RotateLeft(xs []int, k int) []int {\n\tn := len(xs)\n\tout := make([]int, 0, n)\n\tif n == 0 {\n\t\treturn out\n\t}\n\tk %= n\n\tout = append(out, xs[k:]...)\n\tout = append(out, xs[:k]...)\n\treturn out\n}\n",
    wrong_solutions=[
        "package main\n\nfunc RotateLeft(xs []int, k int) []int {\n\tif len(xs) == 0 {\n\t\treturn xs\n\t}\n\tk %= len(xs)\n\treturn append(xs[k:], xs[:k]...)\n}\n",
        "package main\n\nfunc RotateLeft(xs []int, k int) []int {\n\tout := make([]int, 0, len(xs))\n\tif k > len(xs) {\n\t\tk = len(xs)\n\t}\n\tout = append(out, xs[k:]...)\n\treturn append(out, xs[:k]...)\n}\n",
    ],
    harness=harness([
        ("RotateLeft([]int{1, 2, 3, 4, 5}, 2)", "[]int{3, 4, 5, 1, 2}"), ("RotateLeft([]int{1, 2, 3}, 0)", "[]int{1, 2, 3}"),
        ("RotateLeft([]int{1, 2, 3}, 3)", "[]int{1, 2, 3}"), ("RotateLeft([]int{1, 2, 3}, 4)", "[]int{2, 3, 1}"),
        ("len(RotateLeft(nil, 5))", "0"), ("RotateLeft([]int{9}, 100)", "[]int{9}"),
        "in := []int{1, 2, 3, 4}; _ = RotateLeft(in, 1); return in, []int{1, 2, 3, 4}",
        "in := []int{1, 2, 3, 4}; out := RotateLeft(in, 3); out[0] = 77; return in, []int{1, 2, 3, 4}",
        "in := make([]int, 3, 10); in[0], in[1], in[2] = 1, 2, 3; _ = RotateLeft(in, 1); return in[:4], []int{1, 2, 3, 0}",
    ]),
    guide=G(
        "[Slicing, aliasing and copy](#/lesson/go/go-slicing-aliasing): slice expressions share memory, `append` may write into spare capacity.",
        "A left rotation by `k` is 'the tail `xs[k:]` followed by the head `xs[:k]`'. Build that in a fresh slice so nothing is shared.",
        ["Reduce `k` with `k %= len(xs)`, after handling the empty slice (modulo by zero panics).", "Allocate the result with `make([]int, 0, n)`.", "`append(out, xs[k:]...)` then `append(out, xs[:k]...)`."],
        "Rotating by one position `k` times in a loop is O(n·k).",
        "**Dry run:** `[1 2 3 4 5]`, k=2 → tail `[3 4 5]` + head `[1 2]`.\n\n"
        "```go\nn := len(xs)\nout := make([]int, 0, n)\nif n == 0 {\n\treturn out\n}\nk %= n\nout = append(out, xs[k:]...)\nout = append(out, xs[:k]...)\nreturn out\n```",
        "O(n) time and space.",
        "`append(xs[k:], xs[:k]...)` appends into the input's backing array when there is spare capacity, or returns a slice sharing it: the caller's data changes. Forgetting `k %= n`. Modulo on an empty slice.",
    ),
),
# ------------------------------------------------------------------ 11
dict(
    id="go-real-rect-methods", title="Methods: value and pointer receivers", difficulty="Easy", pattern="Go methods", kind="go", cases=8,
    description=r"""
Define a type

```go
type Rect struct {
    W, H float64
}
```

with three methods:

- `Area() float64` returns width × height;
- `Perimeter() float64` returns 2 × (width + height);
- `Scale(f float64)` multiplies both sides by `f`, **changing the rectangle it is called on**.

`Scale` needs a pointer receiver; the other two may use value receivers.
""" + LOGIN,
    starter="package main\n\n// Rect is a rectangle.\ntype Rect struct {\n\tW, H float64\n}\n\n// Area returns the area of r.\nfunc (r Rect) Area() float64 {\n\treturn 0\n}\n\n// add Perimeter and Scale\n",
    solution="package main\n\n// Rect is a rectangle.\ntype Rect struct {\n\tW, H float64\n}\n\n// Area returns the area of r.\nfunc (r Rect) Area() float64 { return r.W * r.H }\n\n// Perimeter returns the perimeter of r.\nfunc (r Rect) Perimeter() float64 { return 2 * (r.W + r.H) }\n\n// Scale multiplies both sides by f.\nfunc (r *Rect) Scale(f float64) {\n\tr.W *= f\n\tr.H *= f\n}\n",
    wrong_solutions=[
        "package main\n\ntype Rect struct {\n\tW, H float64\n}\n\nfunc (r Rect) Area() float64      { return r.W * r.H }\nfunc (r Rect) Perimeter() float64 { return 2 * (r.W + r.H) }\nfunc (r Rect) Scale(f float64) {\n\tr.W *= f\n\tr.H *= f\n}\n",
        "package main\n\ntype Rect struct {\n\tW, H float64\n}\n\nfunc (r Rect) Area() float64      { return r.W * r.H }\nfunc (r Rect) Perimeter() float64 { return 2*r.W + r.H }\nfunc (r *Rect) Scale(f float64) {\n\tr.W *= f\n\tr.H *= f\n}\n",
    ],
    harness=harness([
        ("Rect{3, 4}.Area()", "12.0"), ("Rect{3, 4}.Perimeter()", "14.0"), ("Rect{}.Area()", "0.0"), ("Rect{2.5, 2}.Area()", "5.0"),
        "r := Rect{2, 3}; r.Scale(2); return r.Area(), 24.0",
        "r := Rect{2, 3}; r.Scale(2); return r, Rect{4, 6}",
        "r := &Rect{1, 5}; r.Scale(3); return r.Perimeter(), 36.0",
        "r := Rect{4, 4}; r.Scale(0.5); r.Scale(0.5); return r.W, 1.0",
    ]),
    guide=G(
        "[Defined types, methods and embedding](#/lesson/go/go-types-methods).",
        "A method's receiver is a parameter. A value receiver gets a copy, so changes are lost; a pointer receiver gets the address and changes the original.",
        ["`func (r Rect) Area() float64` reads the fields.", "For `Scale`, write the receiver as `(r *Rect)`.", "Calling `r.Scale(2)` on a variable works: Go takes the address for you."],
        "Not applicable.",
        "**Dry run:** `r := Rect{2, 3}; r.Scale(2)` → with a pointer receiver `r` becomes `{4 6}` and the area 24; with a value receiver `r` stays `{2 3}`.\n\n"
        "```go\nfunc (r Rect) Area() float64      { return r.W * r.H }\nfunc (r Rect) Perimeter() float64 { return 2 * (r.W + r.H) }\nfunc (r *Rect) Scale(f float64) {\n\tr.W *= f\n\tr.H *= f\n}\n```",
        "O(1) each.",
        "A value receiver on `Scale` compiles and silently does nothing. In real code, once one method has a pointer receiver, give all methods pointer receivers for consistency.",
    ),
),
# ------------------------------------------------------------------ 12
dict(
    id="go-real-stack", title="A stack type with a useful zero value", difficulty="Easy", pattern="Go methods", kind="go", cases=9,
    description=r"""
Define a type `Stack` holding integers, with methods:

- `Push(v int)` adds a value on top;
- `Pop() (int, bool)` removes and returns the top value and `true`, or returns `0, false` when the stack is empty;
- `Peek() (int, bool)` returns the top value without removing it;
- `Len() int` returns the number of stored values.

A stack is last in, first out. The **zero value** must be ready to use: `var s Stack; s.Push(1)` must work.
""" + LOGIN,
    starter="package main\n\n// Stack is a last-in, first-out collection of ints.\ntype Stack struct {\n\titems []int\n}\n\n// Push adds v on top.\nfunc (s *Stack) Push(v int) {\n\t// your code\n}\n\n// add Pop, Peek and Len\n",
    solution="package main\n\n// Stack is a last-in, first-out collection of ints.\ntype Stack struct {\n\titems []int\n}\n\n// Push adds v on top.\nfunc (s *Stack) Push(v int) { s.items = append(s.items, v) }\n\n// Pop removes and returns the top value.\nfunc (s *Stack) Pop() (int, bool) {\n\tif len(s.items) == 0 {\n\t\treturn 0, false\n\t}\n\tv := s.items[len(s.items)-1]\n\ts.items = s.items[:len(s.items)-1]\n\treturn v, true\n}\n\n// Peek returns the top value without removing it.\nfunc (s *Stack) Peek() (int, bool) {\n\tif len(s.items) == 0 {\n\t\treturn 0, false\n\t}\n\treturn s.items[len(s.items)-1], true\n}\n\n// Len returns the number of values.\nfunc (s *Stack) Len() int { return len(s.items) }\n",
    wrong_solutions=[
        "package main\n\ntype Stack struct {\n\titems []int\n}\n\nfunc (s *Stack) Push(v int) { s.items = append(s.items, v) }\n\nfunc (s *Stack) Pop() (int, bool) {\n\tif len(s.items) == 0 {\n\t\treturn 0, false\n\t}\n\tv := s.items[0]\n\ts.items = s.items[1:]\n\treturn v, true\n}\n\nfunc (s *Stack) Peek() (int, bool) {\n\tif len(s.items) == 0 {\n\t\treturn 0, false\n\t}\n\treturn s.items[0], true\n}\n\nfunc (s *Stack) Len() int { return len(s.items) }\n",
        "package main\n\ntype Stack struct {\n\titems []int\n}\n\nfunc (s *Stack) Push(v int) { s.items = append(s.items, v) }\n\nfunc (s *Stack) Pop() (int, bool) {\n\tv := s.items[len(s.items)-1]\n\ts.items = s.items[:len(s.items)-1]\n\treturn v, true\n}\n\nfunc (s *Stack) Peek() (int, bool) {\n\treturn s.items[len(s.items)-1], true\n}\n\nfunc (s *Stack) Len() int { return len(s.items) }\n",
    ],
    harness=harness([
        "var s Stack; return s.Len(), 0",
        "var s Stack; return fmt.Sprint(s.Pop()), \"0 false\"",
        "var s Stack; s.Push(5); return fmt.Sprint(s.Peek()), \"5 true\"",
        "var s Stack; s.Push(1); s.Push(2); s.Push(3); return fmt.Sprint(s.Pop()), \"3 true\"",
        "var s Stack; s.Push(1); s.Push(2); s.Pop(); return fmt.Sprint(s.Pop()), \"1 true\"",
        "var s Stack; s.Push(1); s.Pop(); return fmt.Sprint(s.Pop()), \"0 false\"",
        "var s Stack; s.Push(9); s.Peek(); s.Peek(); return s.Len(), 1",
        "var s Stack; for i := 0; i < 100; i++ { s.Push(i) }; s.Pop(); return s.Len(), 99",
        "var a, b Stack; a.Push(1); b.Push(2); b.Push(3); return fmt.Sprint(a.Len(), b.Len()), \"1 2\"",
    ]),
    guide=G(
        "[Arrays and slices](#/lesson/go/go-arrays-slices), [Defined types, methods and embedding](#/lesson/go/go-types-methods).",
        "A slice already grows at its end. Push is `append`; pop reads the last element and re-slices one shorter. A nil slice accepts `append`, which gives the useful zero value for free.",
        ["All methods need pointer receivers because they change `s.items`.", "The top is `s.items[len(s.items)-1]`.", "Check for the empty stack before indexing."],
        "Pushing and popping at index 0 makes every operation shift all elements: O(n) each.",
        "**Dry run:** push 1, 2, 3 → `[1 2 3]`; pop → returns 3, slice `[1 2]`; pop → 2; pop → 1; pop → `0, false`.\n\n"
        "```go\nfunc (s *Stack) Push(v int) { s.items = append(s.items, v) }\n\nfunc (s *Stack) Pop() (int, bool) {\n\tif len(s.items) == 0 {\n\t\treturn 0, false\n\t}\n\tv := s.items[len(s.items)-1]\n\ts.items = s.items[:len(s.items)-1]\n\treturn v, true\n}\n```",
        "O(1) amortised per operation.",
        "Taking from the front (that is a queue). Indexing an empty slice, which panics. Value receivers, which modify a copy.",
    ),
),
# ------------------------------------------------------------------ 13
dict(
    id="go-real-shapes", title="An interface and two implementations", difficulty="Medium", pattern="Go interfaces", kind="go", cases=9,
    description=r"""
Declare

```go
type Shape interface {
    Area() float64
    Name() string
}
```

and two types that satisfy it:

- `Circle` with field `R float64`: area `math.Pi * R * R`, name `"circle"`;
- `Square` with field `S float64`: area `S * S`, name `"square"`.

Then write:

- `func TotalArea(shapes []Shape) float64` returning the sum of the areas (0 for none);
- `func Largest(shapes []Shape) Shape` returning the shape with the largest area (the first one on ties), or `nil` for an empty slice.
""" + LOGIN,
    starter='package main\n\n// Shape is anything with an area and a name.\ntype Shape interface {\n\tArea() float64\n\tName() string\n}\n\n// Circle is a circle of radius R.\ntype Circle struct{ R float64 }\n\n// Square is a square of side S.\ntype Square struct{ S float64 }\n\n// add the methods, TotalArea and Largest\n',
    solution='package main\n\nimport "math"\n\n// Shape is anything with an area and a name.\ntype Shape interface {\n\tArea() float64\n\tName() string\n}\n\n// Circle is a circle of radius R.\ntype Circle struct{ R float64 }\n\n// Square is a square of side S.\ntype Square struct{ S float64 }\n\nfunc (c Circle) Area() float64 { return math.Pi * c.R * c.R }\nfunc (c Circle) Name() string  { return "circle" }\nfunc (s Square) Area() float64 { return s.S * s.S }\nfunc (s Square) Name() string  { return "square" }\n\n// TotalArea sums the areas.\nfunc TotalArea(shapes []Shape) float64 {\n\ttotal := 0.0\n\tfor _, s := range shapes {\n\t\ttotal += s.Area()\n\t}\n\treturn total\n}\n\n// Largest returns the shape with the largest area, or nil.\nfunc Largest(shapes []Shape) Shape {\n\tvar best Shape\n\tfor _, s := range shapes {\n\t\tif best == nil || s.Area() > best.Area() {\n\t\t\tbest = s\n\t\t}\n\t}\n\treturn best\n}\n',
    wrong_solutions=[
        'package main\n\nimport "math"\n\ntype Shape interface {\n\tArea() float64\n\tName() string\n}\n\ntype Circle struct{ R float64 }\ntype Square struct{ S float64 }\n\nfunc (c Circle) Area() float64 { return 2 * math.Pi * c.R }\nfunc (c Circle) Name() string  { return "circle" }\nfunc (s Square) Area() float64 { return s.S * s.S }\nfunc (s Square) Name() string  { return "square" }\n\nfunc TotalArea(shapes []Shape) float64 {\n\ttotal := 0.0\n\tfor _, s := range shapes {\n\t\ttotal += s.Area()\n\t}\n\treturn total\n}\n\nfunc Largest(shapes []Shape) Shape {\n\tvar best Shape\n\tfor _, s := range shapes {\n\t\tif best == nil || s.Area() > best.Area() {\n\t\t\tbest = s\n\t\t}\n\t}\n\treturn best\n}\n',
        'package main\n\nimport "math"\n\ntype Shape interface {\n\tArea() float64\n\tName() string\n}\n\ntype Circle struct{ R float64 }\ntype Square struct{ S float64 }\n\nfunc (c Circle) Area() float64 { return math.Pi * c.R * c.R }\nfunc (c Circle) Name() string  { return "circle" }\nfunc (s Square) Area() float64 { return s.S * s.S }\nfunc (s Square) Name() string  { return "square" }\n\nfunc TotalArea(shapes []Shape) float64 {\n\ttotal := 0.0\n\tfor _, s := range shapes {\n\t\ttotal += s.Area()\n\t}\n\treturn total\n}\n\nfunc Largest(shapes []Shape) Shape {\n\tvar best Shape\n\tfor _, s := range shapes {\n\t\tif best == nil || s.Area() >= best.Area() {\n\t\t\tbest = s\n\t\t}\n\t}\n\treturn best\n}\n',
    ],
    harness=harness([
        ("r2(Circle{1}.Area())", "3.14"), ("Square{3}.Area()", "9.0"), ('Circle{2}.Name() + "," + Square{2}.Name()', '"circle,square"'),
        ("TotalArea(nil)", "0.0"), ("r2(TotalArea([]Shape{Square{2}, Circle{1}, Square{1}}))", "8.14"),
        ("Largest(nil) == nil", "true"), ("Largest([]Shape{Square{2}, Circle{2}, Square{3}}).Name()", '"circle"'),
        ("Largest([]Shape{Square{2}, Square{5}, Circle{1}})", "Square{5}"),
        ('Largest([]Shape{tagged{4, "first"}, tagged{4, "second"}, tagged{1, "small"}}).Name()', '"first"'),
    ], imports=["math"], pre="""func r2(x float64) float64 { return math.Round(x*100) / 100 }

type tagged struct {
	area float64
	name string
}

func (t tagged) Area() float64 { return t.area }
func (t tagged) Name() string  { return t.name }"""),
    guide=G(
        "[Interfaces, any, assertions and the nil trap](#/lesson/go/go-interfaces).",
        "A type satisfies an interface by having its methods; no `implements` keyword. Functions written against `Shape` work for every such type, present and future.",
        ["Give both types the two methods with value receivers.", "`TotalArea` is a loop adding `s.Area()`.", "For `Largest`, keep a `best` variable of type `Shape` that starts as nil; replace it only when the new area is strictly greater."],
        "A type switch inside `TotalArea` listing every concrete type works until someone adds a triangle; calling the interface method needs no change.",
        "**Dry run:** `[Square{2}, Circle{2}, Square{3}]` → areas 4, 12.57, 9 → best becomes the square, then the circle, and stays.\n\n"
        "```go\nfunc Largest(shapes []Shape) Shape {\n\tvar best Shape\n\tfor _, s := range shapes {\n\t\tif best == nil || s.Area() > best.Area() {\n\t\t\tbest = s\n\t\t}\n\t}\n\treturn best\n}\n```",
        "O(n) for both functions.",
        "`>=` returns the last of equal shapes instead of the first. Circumference formula instead of area. Calling a method on a nil `best` before checking.",
    ),
),
# ------------------------------------------------------------------ 14
dict(
    id="go-real-stringer", title="A String method for money", difficulty="Medium", pattern="Go interfaces", kind="go", cases=9,
    description=r"""
Define `type Money int64`, an amount in **cents**, and give it a method `String() string` so that `fmt`
prints it nicely (this is the `fmt.Stringer` interface):

- `Money(1234)` → `"$12.34"`
- `Money(5)` → `"$0.05"`
- `Money(0)` → `"$0.00"`
- `Money(-250)` → `"-$2.50"`

Also write `func Total(items []Money) Money` returning the sum.
""" + LOGIN,
    starter="package main\n\n// Money is an amount in cents.\ntype Money int64\n\n// String formats m as dollars and cents.\nfunc (m Money) String() string {\n\t// your code\n\treturn \"\"\n}\n\n// Total sums the items.\nfunc Total(items []Money) Money {\n\treturn 0\n}\n",
    solution='package main\n\nimport "fmt"\n\n// Money is an amount in cents.\ntype Money int64\n\n// String formats m as dollars and cents.\nfunc (m Money) String() string {\n\tsign := ""\n\tv := int64(m)\n\tif v < 0 {\n\t\tsign = "-"\n\t\tv = -v\n\t}\n\treturn fmt.Sprintf("%s$%d.%02d", sign, v/100, v%100)\n}\n\n// Total sums the items.\nfunc Total(items []Money) Money {\n\tvar sum Money\n\tfor _, it := range items {\n\t\tsum += it\n\t}\n\treturn sum\n}\n',
    wrong_solutions=[
        'package main\n\nimport "fmt"\n\ntype Money int64\n\nfunc (m Money) String() string {\n\treturn fmt.Sprintf("$%d.%d", int64(m)/100, int64(m)%100)\n}\n\nfunc Total(items []Money) Money {\n\tvar sum Money\n\tfor _, it := range items {\n\t\tsum += it\n\t}\n\treturn sum\n}\n',
        'package main\n\nimport "fmt"\n\ntype Money int64\n\nfunc (m Money) String() string {\n\treturn fmt.Sprintf("$%.2f", float64(m)/100)\n}\n\nfunc Total(items []Money) Money {\n\tvar sum Money\n\tfor _, it := range items {\n\t\tsum += it\n\t}\n\treturn sum\n}\n',
    ],
    harness=harness([
        ("Money(1234).String()", '"$12.34"'), ("Money(5).String()", '"$0.05"'), ("Money(0).String()", '"$0.00"'),
        ("Money(-250).String()", '"-$2.50"'), ("Money(100000).String()", '"$1000.00"'), ("Money(-7).String()", '"-$0.07"'),
        ("fmt.Sprint(Money(990))", '"$9.90"'), ("Total([]Money{150, 250, 5}).String()", '"$4.05"'), ("int64(Total(nil))", "0"),
    ]),
    guide=G(
        "[Defined types, methods and embedding](#/lesson/go/go-types-methods) (methods on non-struct types), `fmt.Sprintf`.",
        "Any type with `String() string` is printed through it by `fmt`. Work in whole cents: dollars are `v / 100`, the cents part is `v % 100` padded to two digits.",
        ["Handle the sign separately: remember it, then format the absolute value.", "`%02d` pads a number with a leading zero to width 2.", "Inside `String`, convert to `int64` before formatting, or `fmt` would call `String` again and recurse for ever."],
        "Converting to `float64` and formatting with `%.2f` looks fine for small values but puts the minus sign after the dollar sign and loses exactness for large amounts.",
        "**Dry run:** `-250` → sign `-`, v = 250 → `250/100 = 2`, `250%100 = 50` → `-$2.50`. `5` → `0` and `05` → `$0.05`.\n\n"
        '```go\nfunc (m Money) String() string {\n\tsign := ""\n\tv := int64(m)\n\tif v < 0 {\n\t\tsign = "-"\n\t\tv = -v\n\t}\n\treturn fmt.Sprintf("%s$%d.%02d", sign, v/100, v%100)\n}\n```',
        "O(1) for `String`, O(n) for `Total`.",
        "`%d` without padding prints `$0.5`. Formatting `m` itself with `%v` inside `String` causes infinite recursion. Negative amounts: `-250 % 100` is `-50` in Go.",
    ),
),
# ------------------------------------------------------------------ 15
dict(
    id="go-real-error-wrap", title="Wrap errors and keep the cause", difficulty="Medium", pattern="Go errors", kind="go", cases=9,
    description=r"""
Declare two sentinel errors:

```go
var ErrNotFound  = errors.New("not found")
var ErrInvalidID = errors.New("invalid id")
```

Write `func FindUser(id int) (string, error)` over this fixed data: user 1 is `"ana"`, user 2 is `"ben"`, user 3 is `"cy"`.

- `id <= 0` → return `""` and an error that **wraps** `ErrInvalidID`, with the message `find user <id>: invalid id`;
- unknown id → return `""` and an error that wraps `ErrNotFound`, with the message `find user <id>: not found`;
- otherwise return the name and `nil`.

Wrap with `fmt.Errorf("find user %d: %w", id, ErrNotFound)`. The tests use `errors.Is`.
""" + LOGIN,
    starter='package main\n\nimport "errors"\n\nvar ErrNotFound = errors.New("not found")\nvar ErrInvalidID = errors.New("invalid id")\n\n// FindUser returns the name of the user with the given id.\nfunc FindUser(id int) (string, error) {\n\t// your code\n\treturn "", nil\n}\n',
    solution='package main\n\nimport (\n\t"errors"\n\t"fmt"\n)\n\nvar ErrNotFound = errors.New("not found")\nvar ErrInvalidID = errors.New("invalid id")\n\nvar users = map[int]string{1: "ana", 2: "ben", 3: "cy"}\n\n// FindUser returns the name of the user with the given id.\nfunc FindUser(id int) (string, error) {\n\tif id <= 0 {\n\t\treturn "", fmt.Errorf("find user %d: %w", id, ErrInvalidID)\n\t}\n\tname, ok := users[id]\n\tif !ok {\n\t\treturn "", fmt.Errorf("find user %d: %w", id, ErrNotFound)\n\t}\n\treturn name, nil\n}\n',
    wrong_solutions=[
        'package main\n\nimport (\n\t"errors"\n\t"fmt"\n)\n\nvar ErrNotFound = errors.New("not found")\nvar ErrInvalidID = errors.New("invalid id")\n\nvar users = map[int]string{1: "ana", 2: "ben", 3: "cy"}\n\nfunc FindUser(id int) (string, error) {\n\tif id <= 0 {\n\t\treturn "", fmt.Errorf("find user %d: %v", id, ErrInvalidID)\n\t}\n\tname, ok := users[id]\n\tif !ok {\n\t\treturn "", fmt.Errorf("find user %d: %v", id, ErrNotFound)\n\t}\n\treturn name, nil\n}\n',
        'package main\n\nimport "errors"\n\nvar ErrNotFound = errors.New("not found")\nvar ErrInvalidID = errors.New("invalid id")\n\nvar users = map[int]string{1: "ana", 2: "ben", 3: "cy"}\n\nfunc FindUser(id int) (string, error) {\n\tname, ok := users[id]\n\tif !ok {\n\t\treturn "", ErrNotFound\n\t}\n\treturn name, nil\n}\n',
    ],
    harness=harness([
        "name, err := FindUser(1); return fmt.Sprintf(\"%s %v\", name, err), \"ana <nil>\"",
        "name, err := FindUser(3); return fmt.Sprintf(\"%s %v\", name, err), \"cy <nil>\"",
        "_, err := FindUser(7); return errors.Is(err, ErrNotFound), true",
        "_, err := FindUser(7); return err.Error(), \"find user 7: not found\"",
        "_, err := FindUser(0); return errors.Is(err, ErrInvalidID), true",
        "_, err := FindUser(-4); return err.Error(), \"find user -4: invalid id\"",
        "_, err := FindUser(-4); return errors.Is(err, ErrNotFound), false",
        "name, _ := FindUser(99); return name, \"\"",
        "_, err := FindUser(7); return err == ErrNotFound, false",
    ], imports=["errors"]),
    guide=G(
        "[Errors are values](#/lesson/go/go-errors-values) and [errors.Is, errors.As, panic and recover](#/lesson/go/go-errors-is-as-panic).",
        "Wrapping adds context ('which user?') while keeping the original sentinel inside, so callers can still recognise the cause with `errors.Is`.",
        ["Check the invalid id first.", "Use the comma-ok form on the map: `name, ok := users[id]`.", "The verb must be `%w`. With `%v` the message is the same and the cause is lost."],
        "Returning the bare sentinel works for `errors.Is` and loses the id from the message; returning `errors.New(text)` keeps the message and loses the identity.",
        "**Dry run:** `FindUser(7)` → not `<= 0`, not in the map → `fmt.Errorf(\"find user %d: %w\", 7, ErrNotFound)` → message `find user 7: not found`, and `errors.Is(err, ErrNotFound)` is true.\n\n"
        '```go\nif id <= 0 {\n\treturn "", fmt.Errorf("find user %d: %w", id, ErrInvalidID)\n}\nname, ok := users[id]\nif !ok {\n\treturn "", fmt.Errorf("find user %d: %w", id, ErrNotFound)\n}\nreturn name, nil\n```',
        "O(1).",
        "`%v` instead of `%w`. Comparing with `==` in callers (a wrapped error is a different value). Forgetting the invalid-id branch, which then reports 'not found'.",
    ),
),
# ------------------------------------------------------------------ 16
dict(
    id="go-real-error-as", title="A custom error type and errors.As", difficulty="Medium", pattern="Go errors", kind="go", cases=9,
    description=r"""
Define an error type that carries details:

```go
type ValidationError struct {
    Field  string
    Reason string
}
```

with a method `func (e *ValidationError) Error() string` returning `"<Field>: <Reason>"`.

Write `func ValidateUser(name string, age int) error`:

- empty `name` → field `"name"`, reason `"is required"`;
- `age < 0` → field `"age"`, reason `"must not be negative"`;
- `age > 150` → field `"age"`, reason `"is unrealistic"`;
- otherwise `nil`.

Check the name first. Return the error **wrapped**: `fmt.Errorf("validate user: %w", &ValidationError{...})`, so the
full message is e.g. `validate user: age: is unrealistic`. On success return a plain `nil`.
""" + LOGIN,
    starter='package main\n\n// ValidationError describes one invalid field.\ntype ValidationError struct {\n\tField  string\n\tReason string\n}\n\n// add the Error method and ValidateUser\n',
    solution='package main\n\nimport "fmt"\n\n// ValidationError describes one invalid field.\ntype ValidationError struct {\n\tField  string\n\tReason string\n}\n\nfunc (e *ValidationError) Error() string { return e.Field + ": " + e.Reason }\n\nfunc invalid(field, reason string) error {\n\treturn fmt.Errorf("validate user: %w", &ValidationError{Field: field, Reason: reason})\n}\n\n// ValidateUser checks a name and an age.\nfunc ValidateUser(name string, age int) error {\n\tswitch {\n\tcase name == "":\n\t\treturn invalid("name", "is required")\n\tcase age < 0:\n\t\treturn invalid("age", "must not be negative")\n\tcase age > 150:\n\t\treturn invalid("age", "is unrealistic")\n\t}\n\treturn nil\n}\n',
    wrong_solutions=[
        'package main\n\nimport "fmt"\n\ntype ValidationError struct {\n\tField  string\n\tReason string\n}\n\nfunc (e *ValidationError) Error() string { return e.Field + ": " + e.Reason }\n\nfunc ValidateUser(name string, age int) error {\n\tswitch {\n\tcase name == "":\n\t\treturn fmt.Errorf("validate user: name: is required")\n\tcase age < 0:\n\t\treturn fmt.Errorf("validate user: age: must not be negative")\n\tcase age > 150:\n\t\treturn fmt.Errorf("validate user: age: is unrealistic")\n\t}\n\treturn nil\n}\n',
        'package main\n\ntype ValidationError struct {\n\tField  string\n\tReason string\n}\n\nfunc (e *ValidationError) Error() string { return e.Field + ": " + e.Reason }\n\nfunc ValidateUser(name string, age int) error {\n\tvar e *ValidationError\n\tif name == "" {\n\t\te = &ValidationError{"name", "is required"}\n\t} else if age < 0 {\n\t\te = &ValidationError{"age", "must not be negative"}\n\t} else if age > 150 {\n\t\te = &ValidationError{"age", "is unrealistic"}\n\t}\n\treturn e\n}\n',
    ],
    harness=harness([
        ('ValidateUser("ana", 30) == nil', "true"), ('ValidateUser("ana", 0) == nil', "true"), ('ValidateUser("ana", 150) == nil', "true"),
        ('field(ValidateUser("", 30))', '"name"'), ('field(ValidateUser("ana", -1))', '"age"'),
        ('ValidateUser("ana", 200).Error()', '"validate user: age: is unrealistic"'),
        ('ValidateUser("", -5).Error()', '"validate user: name: is required"'),
        ('reason(ValidateUser("bo", -1))', '"must not be negative"'),
        ('(&ValidationError{"x", "y"}).Error()', '"x: y"'),
    ], imports=["errors"], pre='''func field(err error) string {
	var ve *ValidationError
	if errors.As(err, &ve) {
		return ve.Field
	}
	return "errors.As found no *ValidationError"
}

func reason(err error) string {
	var ve *ValidationError
	if errors.As(err, &ve) {
		return ve.Reason
	}
	return "errors.As found no *ValidationError"
}'''),
    guide=G(
        "[errors.Is, errors.As, panic and recover](#/lesson/go/go-errors-is-as-panic); the nil-interface trap from [Interfaces](#/lesson/go/go-interfaces).",
        "A custom error type lets callers read details as data. Wrapping it with `%w` adds context and keeps it discoverable through `errors.As`.",
        ["Give `*ValidationError` (pointer receiver) the `Error` method.", "Build the error with `&ValidationError{Field: ..., Reason: ...}` and wrap it with `fmt.Errorf(\"validate user: %w\", ...)`.", "Return the literal `nil` on success, never a nil `*ValidationError` variable."],
        "Returning formatted strings gives the right message and no way for a caller to ask which field failed.",
        "**Dry run:** `ValidateUser(\"\", -5)` → the name check comes first → wraps `{name, is required}` → message `validate user: name: is required`; `errors.As` finds the inner value and its `Field` is `name`.\n\n"
        '```go\nfunc (e *ValidationError) Error() string { return e.Field + ": " + e.Reason }\n\nfunc ValidateUser(name string, age int) error {\n\tif name == "" {\n\t\treturn fmt.Errorf("validate user: %w", &ValidationError{"name", "is required"})\n\t}\n\t// ... age checks ...\n\treturn nil\n}\n```',
        "O(1).",
        "Declaring `var e *ValidationError` and returning it: on success the caller receives a non-nil interface holding a nil pointer, so `err == nil` is false. Building the message with plain text, leaving nothing for `errors.As`.",
    ),
),
# ------------------------------------------------------------------ 17
dict(
    id="go-real-generic-map-filter", title="Generic Map and Filter", difficulty="Medium", pattern="Go generics", kind="go", cases=9,
    description=r"""
Write two generic functions:

```go
func Map[T, U any](xs []T, f func(T) U) []U
func Filter[T any](xs []T, keep func(T) bool) []T
```

- `Map` returns a new slice containing `f(x)` for every element, in order.
- `Filter` returns a new slice with the elements for which `keep` returns true, in order.

Both return an empty slice for empty input and must not modify `xs`.

**Example:** `Map([]int{1, 2, 3}, func(n int) string { return strconv.Itoa(n * n) })` → `["1", "4", "9"]`
""" + LOGIN,
    starter="package main\n\n// Map applies f to every element.\nfunc Map[T, U any](xs []T, f func(T) U) []U {\n\t// your code\n\treturn nil\n}\n\n// Filter keeps the elements for which keep returns true.\nfunc Filter[T any](xs []T, keep func(T) bool) []T {\n\t// your code\n\treturn nil\n}\n",
    solution="package main\n\n// Map applies f to every element.\nfunc Map[T, U any](xs []T, f func(T) U) []U {\n\tout := make([]U, 0, len(xs))\n\tfor _, x := range xs {\n\t\tout = append(out, f(x))\n\t}\n\treturn out\n}\n\n// Filter keeps the elements for which keep returns true.\nfunc Filter[T any](xs []T, keep func(T) bool) []T {\n\tout := make([]T, 0, len(xs))\n\tfor _, x := range xs {\n\t\tif keep(x) {\n\t\t\tout = append(out, x)\n\t\t}\n\t}\n\treturn out\n}\n",
    wrong_solutions=[
        "package main\n\nfunc Map[T, U any](xs []T, f func(T) U) []U {\n\tout := make([]U, len(xs))\n\tfor _, x := range xs {\n\t\tout = append(out, f(x))\n\t}\n\treturn out\n}\n\nfunc Filter[T any](xs []T, keep func(T) bool) []T {\n\tout := make([]T, 0, len(xs))\n\tfor _, x := range xs {\n\t\tif keep(x) {\n\t\t\tout = append(out, x)\n\t\t}\n\t}\n\treturn out\n}\n",
        "package main\n\nfunc Map[T, U any](xs []T, f func(T) U) []U {\n\tout := make([]U, 0, len(xs))\n\tfor _, x := range xs {\n\t\tout = append(out, f(x))\n\t}\n\treturn out\n}\n\nfunc Filter[T any](xs []T, keep func(T) bool) []T {\n\tout := xs[:0]\n\tfor _, x := range xs {\n\t\tif keep(x) {\n\t\t\tout = append(out, x)\n\t\t}\n\t}\n\treturn out\n}\n",
    ],
    harness=harness([
        ("Map([]int{1, 2, 3}, func(n int) string { return strconv.Itoa(n * n) })", '[]string{"1", "4", "9"}'),
        ('Map([]string{"go", "rust"}, func(s string) int { return len(s) })', "[]int{2, 4}"),
        ("len(Map([]int{}, func(n int) int { return n }))", "0"),
        ("Map([]float64{1.5}, func(f float64) bool { return f > 1 })", "[]bool{true}"),
        ("Filter([]int{1, 2, 3, 4, 5, 6}, func(n int) bool { return n%2 == 0 })", "[]int{2, 4, 6}"),
        ('Filter([]string{"a", "", "b", ""}, func(s string) bool { return s != "" })', '[]string{"a", "b"}'),
        ("len(Filter([]int{1, 3}, func(n int) bool { return n > 10 }))", "0"),
        "in := []int{1, 2, 3, 4}; _ = Filter(in, func(n int) bool { return n > 2 }); return in, []int{1, 2, 3, 4}",
        ("Map(Filter([]int{1, 2, 3, 4}, func(n int) bool { return n%2 == 1 }), func(n int) int { return n * 10 })", "[]int{10, 30}"),
    ], imports=["strconv"]),
    guide=G(
        "[Type parameters and generic functions](#/lesson/go/go-generics-basics).",
        "The loop is identical for every element type; only the types change. Type parameters let you write it once: `T` for the input element, `U` for the output element.",
        ["Declare the type parameters in square brackets after the function name.", "Create the result with `make([]U, 0, len(xs))` and `append`.", "`Filter` needs one type parameter because the element type does not change."],
        "Writing `MapIntToString`, `MapStringToInt` and so on for every pair of types duplicates the same loop endlessly.",
        "**Dry run:** `Filter([1 2 3 4 5 6], even)` → keeps 2, 4, 6. `Map` over `[1 2 3]` with squaring-to-text → `[\"1\" \"4\" \"9\"]`; `T` is inferred as `int` and `U` as `string`.\n\n"
        "```go\nfunc Map[T, U any](xs []T, f func(T) U) []U {\n\tout := make([]U, 0, len(xs))\n\tfor _, x := range xs {\n\t\tout = append(out, f(x))\n\t}\n\treturn out\n}\n```",
        "O(n) time and space.",
        "`make([]U, len(xs))` followed by `append` leaves `len(xs)` zero values in front. `xs[:0]` in `Filter` overwrites the caller's slice.",
    ),
),
# ------------------------------------------------------------------ 18
dict(
    id="go-real-generic-max", title="Generic maximum with a constraint", difficulty="Medium", pattern="Go generics", kind="go", cases=9,
    description=r"""
Write

```go
func MaxOf[T cmp.Ordered](xs []T) (T, bool)
```

It returns the largest element of `xs` and `true`. For an empty slice it returns the zero value of `T` and `false`.

`cmp.Ordered` (import `"cmp"`) is the constraint for types that support `<` and `>`: integers, floats and strings.

**Examples:** `MaxOf([]int{3, 9, 2})` → `9, true`; `MaxOf([]string{"go", "rust", "c"})` → `"rust", true`; `MaxOf([]float64{})` → `0, false`.
""" + LOGIN,
    starter='package main\n\nimport "cmp"\n\n// MaxOf returns the largest element of xs.\nfunc MaxOf[T cmp.Ordered](xs []T) (T, bool) {\n\tvar zero T\n\t// your code\n\treturn zero, false\n}\n',
    solution='package main\n\nimport "cmp"\n\n// MaxOf returns the largest element of xs.\nfunc MaxOf[T cmp.Ordered](xs []T) (T, bool) {\n\tvar zero T\n\tif len(xs) == 0 {\n\t\treturn zero, false\n\t}\n\tbest := xs[0]\n\tfor _, x := range xs[1:] {\n\t\tif x > best {\n\t\t\tbest = x\n\t\t}\n\t}\n\treturn best, true\n}\n',
    wrong_solutions=[
        'package main\n\nimport "cmp"\n\nfunc MaxOf[T cmp.Ordered](xs []T) (T, bool) {\n\tvar best T\n\tfor _, x := range xs {\n\t\tif x > best {\n\t\t\tbest = x\n\t\t}\n\t}\n\treturn best, len(xs) > 0\n}\n',
        'package main\n\nimport "cmp"\n\nfunc MaxOf[T cmp.Ordered](xs []T) (T, bool) {\n\tvar zero T\n\tif len(xs) == 0 {\n\t\treturn zero, false\n\t}\n\treturn xs[len(xs)-1], true\n}\n',
    ],
    harness=harness([
        ("fmt.Sprint(MaxOf([]int{3, 9, 2}))", '"9 true"'), ("fmt.Sprint(MaxOf([]int{}))", '"0 false"'),
        ("fmt.Sprint(MaxOf([]int{-5, -2, -9}))", '"-2 true"'), ('pair(MaxOf([]string{"go", "rust", "c"}))', '"rust true"'),
        ("fmt.Sprint(MaxOf([]float64{1.5, 2.25, 2.0}))", '"2.25 true"'), ("fmt.Sprint(MaxOf([]float64(nil)))", '"0 false"'),
        ("fmt.Sprint(MaxOf([]int{7}))", '"7 true"'), ('fmt.Sprintf("%q", first(MaxOf([]string{})))', '`""`'),
        ("fmt.Sprint(MaxOf([]uint8{200, 13, 255, 0}))", '"255 true"'),
    ], pre="""func first[T any](v T, ok bool) T { return v }

func pair[T any](v T, ok bool) string { return fmt.Sprintf("%v %v", v, ok) }"""),
    guide=G(
        "[Type parameters and generic functions](#/lesson/go/go-generics-basics), [Constraints, type sets and idiomatic generics](#/lesson/go/go-generics-constraints).",
        "The constraint is what makes `x > best` legal. Start from the first element, not from the zero value, so that all-negative inputs work.",
        ["`var zero T` is the zero value of whatever type is used.", "Return early for an empty slice.", "Initialise `best := xs[0]` and compare the rest."],
        "Sorting a copy and taking the last element is O(n log n) and allocates; one pass is O(n).",
        "**Dry run:** `[-5 -2 -9]` → best -5, then -2 (greater), then -9 (not) → `-2, true`. Starting `best` at zero would give `0`, which is not even in the slice.\n\n"
        "```go\nfunc MaxOf[T cmp.Ordered](xs []T) (T, bool) {\n\tvar zero T\n\tif len(xs) == 0 {\n\t\treturn zero, false\n\t}\n\tbest := xs[0]\n\tfor _, x := range xs[1:] {\n\t\tif x > best {\n\t\t\tbest = x\n\t\t}\n\t}\n\treturn best, true\n}\n```",
        "O(n) time, O(1) space.",
        "Initialising with the zero value. Using `any` as the constraint (then `>` does not compile). Returning `nil` for a `T`.",
    ),
),
# ------------------------------------------------------------------ 19
dict(
    id="go-real-closure-counter", title="Closures that remember", difficulty="Easy", pattern="Go functions", kind="go", cases=8,
    description=r"""
Write `func NewCounter(start, step int) func() int`.

It returns a function. The first call of that function returns `start`, the second `start + step`, the third
`start + 2*step`, and so on. Every counter created by `NewCounter` keeps its own state.

**Example:**

```go
next := NewCounter(10, 5)
next() // 10
next() // 15
next() // 20
```
""" + LOGIN,
    starter="package main\n\n// NewCounter returns a function that yields start, start+step, start+2*step, ...\nfunc NewCounter(start, step int) func() int {\n\t// your code\n\treturn nil\n}\n",
    solution="package main\n\n// NewCounter returns a function that yields start, start+step, start+2*step, ...\nfunc NewCounter(start, step int) func() int {\n\tnext := start\n\treturn func() int {\n\t\tv := next\n\t\tnext += step\n\t\treturn v\n\t}\n}\n",
    wrong_solutions=[
        "package main\n\nfunc NewCounter(start, step int) func() int {\n\treturn func() int {\n\t\tstart += step\n\t\treturn start\n\t}\n}\n",
        "package main\n\nvar shared int\n\nfunc NewCounter(start, step int) func() int {\n\tshared = start\n\treturn func() int {\n\t\tv := shared\n\t\tshared += step\n\t\treturn v\n\t}\n}\n",
    ],
    harness=harness([
        "c := NewCounter(10, 5); return c(), 10",
        "c := NewCounter(10, 5); c(); return c(), 15",
        "c := NewCounter(10, 5); c(); c(); return c(), 20",
        "c := NewCounter(0, 1); for i := 0; i < 99; i++ { c() }; return c(), 99",
        "c := NewCounter(3, 0); c(); return c(), 3",
        "c := NewCounter(5, -2); c(); c(); return c(), 1",
        "a := NewCounter(0, 1); b := NewCounter(100, 10); a(); a(); b(); return fmt.Sprint(a(), b()), \"2 110\"",
        "a := NewCounter(1, 1); _ = NewCounter(50, 50); return a(), 1",
    ]),
    guide=G(
        "[Closures, defer and call by value](#/lesson/go/go-closures-defer).",
        "The returned function captures a variable of `NewCounter` and keeps it alive. Each call to `NewCounter` creates a fresh variable, so counters are independent.",
        ["Declare a local variable holding the next value to return.", "The returned function reads it, advances it by `step`, and returns the old value.", "Return the value *before* adding the step."],
        "A package-level variable would be shared by all counters, so creating a second counter would disturb the first.",
        "**Dry run:** `NewCounter(10, 5)` → `next = 10`. Call 1: v=10, next=15, return 10. Call 2: v=15, next=20, return 15.\n\n"
        "```go\nfunc NewCounter(start, step int) func() int {\n\tnext := start\n\treturn func() int {\n\t\tv := next\n\t\tnext += step\n\t\treturn v\n\t}\n}\n```",
        "O(1) per call.",
        "Advancing before returning (the first call would give `start + step`). Keeping state in a global variable.",
    ),
),
# ------------------------------------------------------------------ 20
dict(
    id="go-real-safe-call", title="defer and recover: turn a panic into an error", difficulty="Medium", pattern="Go errors", kind="go", cases=8,
    description=r"""
Write `func SafeCall(f func()) (err error)`.

It calls `f`. If `f` returns normally, `SafeCall` returns `nil`. If `f` **panics**, `SafeCall` must not crash:
it recovers and returns an error whose message is `recovered: ` followed by the panic value formatted with `%v`.

**Examples:**

- `SafeCall(func() {})` → `nil`
- `SafeCall(func() { panic("boom") })` → error `recovered: boom`

You need a deferred function that calls `recover()` and assigns to the **named result** `err`.
""" + LOGIN,
    starter="package main\n\n// SafeCall runs f and converts a panic into an error.\nfunc SafeCall(f func()) (err error) {\n\t// your code\n\tf()\n\treturn nil\n}\n",
    solution='package main\n\nimport "fmt"\n\n// SafeCall runs f and converts a panic into an error.\nfunc SafeCall(f func()) (err error) {\n\tdefer func() {\n\t\tif r := recover(); r != nil {\n\t\t\terr = fmt.Errorf("recovered: %v", r)\n\t\t}\n\t}()\n\tf()\n\treturn nil\n}\n',
    wrong_solutions=[
        'package main\n\nimport "fmt"\n\nfunc SafeCall(f func()) error {\n\tvar err error\n\tdefer func() {\n\t\tif r := recover(); r != nil {\n\t\t\terr = fmt.Errorf("recovered: %v", r)\n\t\t}\n\t}()\n\tf()\n\treturn err\n}\n',
        'package main\n\nimport "errors"\n\nfunc SafeCall(f func()) (err error) {\n\tdefer func() {\n\t\trecover()\n\t\terr = errors.New("recovered: panic")\n\t}()\n\tf()\n\treturn nil\n}\n',
    ],
    harness=harness([
        ("SafeCall(func() {}) == nil", "true"),
        ('SafeCall(func() { panic("boom") }).Error()', '"recovered: boom"'),
        ("SafeCall(func() { panic(42) }).Error()", '"recovered: 42"'),
        ('SafeCall(func() { var m map[string]int; m["a"] = 1 }).Error()', '"recovered: assignment to entry in nil map"'),
        ("SafeCall(func() { var s []int; _ = s[3] }) != nil", "true"),
        "n := 0; _ = SafeCall(func() { n = 7 }); return n, 7",
        'ran := false; _ = SafeCall(func() { defer func() { ran = true }(); panic("x") }); return ran, true',
        '_ = SafeCall(func() { panic("first") }); return SafeCall(func() {}) == nil, true',
    ]),
    guide=G(
        "[Closures, defer and call by value](#/lesson/go/go-closures-defer) (named results), [errors.Is, errors.As, panic and recover](#/lesson/go/go-errors-is-as-panic).",
        "`recover` only works inside a deferred function, and a deferred closure can assign to a named result after the function body has stopped. Together they convert a panic into a returned error.",
        ["Name the result: `(err error)`.", "Defer a closure whose first statement is `if r := recover(); r != nil`.", "Inside it, set `err = fmt.Errorf(\"recovered: %v\", r)`."],
        "Not applicable.",
        "**Dry run:** `f` panics with `\"boom\"` → `SafeCall` stops at the call → the deferred closure runs → `recover()` returns `\"boom\"` → `err` is set → `SafeCall` returns that error to its caller.\n\n"
        '```go\nfunc SafeCall(f func()) (err error) {\n\tdefer func() {\n\t\tif r := recover(); r != nil {\n\t\t\terr = fmt.Errorf("recovered: %v", r)\n\t\t}\n\t}()\n\tf()\n\treturn nil\n}\n```',
        "O(1) plus the cost of `f`.",
        "An unnamed result: the deferred closure changes a local variable after the return value was already decided (when `f` panics, `return err` never runs, so the function returns the zero value `nil`). Setting an error even when nothing panicked.",
    ),
),
]
