"""Java track, REAL Java problems part 1 (judged on the server): basics, classes, inheritance, exceptions.

The learner edits Solution.java (a class named Solution). Each harness is a Main.java that prints one
CASE line per test.
"""

PRE = r'''import java.util.*;
import java.util.function.*;

public class Main {
    interface Check { String run() throws Throwable; }
    static int n = 0;

    static void t(Check c) {
        n++;
        String r;
        try { r = c.run(); } catch (Throwable e) { r = "threw " + e; }
        if (r != null) r = r.replace('\n', ' ').replace('\r', ' ');
        System.out.println("CASE " + n + (r == null ? " OK" : " FAIL " + r));
    }

    static String eq(Object got, Object want) {
        return Objects.equals(got, want) ? null : "got " + got + " want " + want;
    }

    static String near(double got, double want) {
        return Math.abs(got - want) < 1e-9 ? null : "got " + got + " want " + want;
    }

    static String arr(int[] got, int[] want) {
        return Arrays.equals(got, want) ? null : "got " + Arrays.toString(got) + " want " + Arrays.toString(want);
    }

    static String yes(boolean cond, String why) {
        return cond ? null : why;
    }

    static String thrown(Class<? extends Throwable> type, Check c) {
        try { c.run(); } catch (Throwable e) {
            return type.isInstance(e) ? null : "threw " + e + " but wanted " + type.getSimpleName();
        }
        return "no exception, wanted " + type.getSimpleName();
    }

    public static void main(String[] args) {
'''


def H(*checks):
    """Build Main.java from lambda bodies. A check starting with '{' is a block lambda, otherwise an expression."""
    return PRE + "".join("        t(() -> %s);\n" % c for c in checks) + "    }\n}\n"


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls, follow_up=None):
    d = dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute, approach=approach,
             complexity=complexity, pitfalls=pitfalls)
    if follow_up:
        d["follow_up"] = follow_up
    return d


def J(id, title, difficulty, pattern, description, starter, solution, checks, wrong, guide):
    return dict(id=id, title=title, difficulty=difficulty, pattern=pattern, kind="java", cases=len(checks),
                description=description, starter=starter, solution=solution, harness=H(*checks),
                wrong_solutions=wrong, guide=guide)


PROBLEMS = [
# ------------------------------------------------------------------ java-code-total-seconds
J("java-code-total-seconds", "Total seconds", "Easy", "Java basics",
  r"""
Your first real Java method. In class `Solution`, write

```java
static int totalSeconds(int hours, int minutes, int seconds)
```

that returns the length of a time span in seconds. One hour is 3600 seconds and one minute is 60.

**Examples** `totalSeconds(0, 1, 30)` → `90`; `totalSeconds(2, 0, 5)` → `7205`.

All arguments are between 0 and 1000, so the result fits in an `int`.

*Java problems are compiled and run on a judge server: you need to be logged in to submit.*
""",
  '''class Solution {
    static int totalSeconds(int hours, int minutes, int seconds) {
        // your code
        return 0;
    }
}
''',
  '''class Solution {
    static int totalSeconds(int hours, int minutes, int seconds) {
        return hours * 3600 + minutes * 60 + seconds;
    }
}
''',
  ["eq(Solution.totalSeconds(0, 1, 30), 90)", "eq(Solution.totalSeconds(2, 0, 5), 7205)", "eq(Solution.totalSeconds(0, 0, 0), 0)",
   "eq(Solution.totalSeconds(0, 0, 59), 59)", "eq(Solution.totalSeconds(1, 0, 0), 3600)", "eq(Solution.totalSeconds(0, 60, 0), 3600)",
   "eq(Solution.totalSeconds(1, 1, 1), 3661)", "eq(Solution.totalSeconds(24, 0, 0), 86400)", "eq(Solution.totalSeconds(1000, 1000, 1000), 3661000)"],
  ['''class Solution {
    static int totalSeconds(int hours, int minutes, int seconds) {
        return hours * 60 + minutes * 60 + seconds;
    }
}
''', '''class Solution {
    static int totalSeconds(int hours, int minutes, int seconds) {
        return (hours + minutes) * 60 + seconds;
    }
}
'''],
  G("Lessons *From source code to a running program* and *Anatomy of a class, main, and your first statements*.",
    "Convert each part to seconds and add them up.",
    ["An hour is 60 minutes of 60 seconds each.", "`*` is done before `+`, so no parentheses are needed.", "`return hours * 3600 + minutes * 60 + seconds;`"],
    "You could loop, adding 3600 once per hour and 60 once per minute. It works and does needless work; multiplication says it directly.",
    r"""Multiply, then add.

**Dry run** `totalSeconds(1, 1, 1)`: `1 * 3600 = 3600`, `1 * 60 = 60`, sum with 1 → `3661`.

```java
class Solution {
    static int totalSeconds(int hours, int minutes, int seconds) {
        return hours * 3600 + minutes * 60 + seconds;
    }
}
```

`static` lets the test call the method as `Solution.totalSeconds(...)` without creating an object. `int` before
the name is the return type.""",
    "Time O(1), space O(1).",
    "- Multiplying hours by 60 instead of 3600.\n- Forgetting the `return`.\n- For much larger inputs an `int` would overflow; `long` would be needed."),
  ),
# ------------------------------------------------------------------ java-code-average
J("java-code-average", "Average of three", "Easy", "Java basics",
  r"""
In class `Solution`, write

```java
static double average(int a, int b, int c)
```

returning the exact arithmetic mean of three whole numbers.

**Examples** `average(1, 2, 4)` → `2.3333333333333335`; `average(3, 3, 3)` → `3.0`.

The trap: `(a + b + c) / 3` divides two `int` values, so Java throws the fraction away. Make sure the
division happens in `double`. The arguments may be as large as `Integer.MAX_VALUE`, so their sum may not fit
in an `int`.
""",
  '''class Solution {
    static double average(int a, int b, int c) {
        // your code
        return 0;
    }
}
''',
  '''class Solution {
    static double average(int a, int b, int c) {
        return ((long) a + b + c) / 3.0;
    }
}
''',
  ["near(Solution.average(1, 2, 4), 7 / 3.0)", "near(Solution.average(3, 3, 3), 3.0)", "near(Solution.average(0, 0, 1), 1 / 3.0)",
   "near(Solution.average(-1, -2, -4), -7 / 3.0)", "near(Solution.average(1, 1, 0), 2 / 3.0)", "near(Solution.average(0, 0, 0), 0.0)",
   "near(Solution.average(Integer.MAX_VALUE, Integer.MAX_VALUE, Integer.MAX_VALUE), 2147483647.0)",
   "near(Solution.average(Integer.MIN_VALUE, Integer.MIN_VALUE, 0), -4294967296.0 / 3)", "near(Solution.average(10, 20, 31), 61 / 3.0)"],
  ['''class Solution {
    static double average(int a, int b, int c) {
        return (a + b + c) / 3;
    }
}
''', '''class Solution {
    static double average(int a, int b, int c) {
        return (a + b + c) / 3.0;
    }
}
'''],
  G("Lesson *Primitive types and how numbers are stored*: integer division, overflow, widening.",
    "Two separate dangers: the sum can overflow `int`, and the division can lose its fraction. Widen to `long` before adding and divide by a `double`.",
    ["`3.0` is a `double` literal; dividing by it gives a `double` result.", "Cast one operand to `long` before the additions so that they are done in 64 bits.",
     "`((long) a + b + c) / 3.0`"],
    "Writing `(a + b + c) / 3` is the natural first attempt. It returns `2.0` for (1, 2, 4).",
    r"""**Dry run** `average(1, 2, 4)`: `(long) 1 + 2 + 4` is the `long` 7; `7 / 3.0` promotes 7 to `double` → `2.3333333333333335`.

**Dry run** with three copies of `Integer.MAX_VALUE`: in `int` the sum would wrap to a negative number. In `long` it is 6442450941, and dividing by 3.0 gives 2147483647.0.

```java
class Solution {
    static double average(int a, int b, int c) {
        return ((long) a + b + c) / 3.0;
    }
}
```""",
    "Time O(1), space O(1).",
    "- Integer division.\n- `(double) (a + b + c) / 3`: the cast is applied after the `int` sum has already overflowed.\n- Casting the result instead of an operand."),
  ),
# ------------------------------------------------------------------ java-code-initials
J("java-code-initials", "Initials", "Easy", "Java strings",
  r"""
In class `Solution`, write

```java
static String initials(String fullName)
```

Return the first letter of each word in upper case, each followed by a dot.

- Words are separated by one or more spaces; there may be spaces at the start or end.
- An empty or all-space name gives the empty string `""`.

**Examples** `initials("ada lovelace")` → `"A.L."`; `initials("  Grace   Brewster Hopper ")` → `"G.B.H."`;
`initials("")` → `""`.
""",
  '''class Solution {
    static String initials(String fullName) {
        // your code
        return "";
    }
}
''',
  '''class Solution {
    static String initials(String fullName) {
        StringBuilder sb = new StringBuilder();
        for (String word : fullName.trim().split(" +")) {
            if (!word.isEmpty()) {
                sb.append(Character.toUpperCase(word.charAt(0))).append('.');
            }
        }
        return sb.toString();
    }
}
''',
  ['eq(Solution.initials("ada lovelace"), "A.L.")', 'eq(Solution.initials("  Grace   Brewster Hopper "), "G.B.H.")', 'eq(Solution.initials(""), "")',
   'eq(Solution.initials("   "), "")', 'eq(Solution.initials("Cher"), "C.")', 'eq(Solution.initials("x y z"), "X.Y.Z.")',
   'eq(Solution.initials("Alan Mathison Turing"), "A.M.T.")', 'eq(Solution.initials(" q"), "Q.")', 'eq(Solution.initials("mary  ann"), "M.A.")'],
  ['''class Solution {
    static String initials(String fullName) {
        StringBuilder sb = new StringBuilder();
        for (String word : fullName.split(" ")) {
            sb.append(Character.toUpperCase(word.charAt(0))).append('.');
        }
        return sb.toString();
    }
}
''', '''class Solution {
    static String initials(String fullName) {
        StringBuilder sb = new StringBuilder();
        for (String word : fullName.trim().split(" +")) {
            if (!word.isEmpty()) sb.append(word.charAt(0)).append('.');
        }
        return sb.toString();
    }
}
'''],
  G("Lesson *Packages, imports and the String toolbox*: `trim`, `split`, `charAt`, `StringBuilder`.",
    "Cut the name into words, take each word's first character, upper-case it, and build the answer piece by piece.",
    ["`trim()` removes the spaces at both ends.", "`split(\" +\")` splits on runs of one or more spaces (the argument is a regular expression).",
     "`\"\".split(\" +\")` returns one empty string, so skip empty words."],
    "Walk the characters with a flag 'previous character was a space'; whenever a non-space follows a space (or the start), it is an initial. Equally fast, and it avoids regular expressions.",
    r"""**Dry run** `"  Grace   Brewster Hopper "`: after `trim` → `"Grace   Brewster Hopper"`; split → `["Grace", "Brewster", "Hopper"]`; initials `G`, `B`, `H` → `"G.B.H."`.

```java
class Solution {
    static String initials(String fullName) {
        StringBuilder sb = new StringBuilder();
        for (String word : fullName.trim().split(" +")) {
            if (!word.isEmpty()) {
                sb.append(Character.toUpperCase(word.charAt(0))).append('.');
            }
        }
        return sb.toString();
    }
}
```""",
    "Time O(n) in the length of the name, space O(n).",
    "- `split(\" \")` produces empty strings for double spaces, and `charAt(0)` on an empty string throws `StringIndexOutOfBoundsException`.\n- Forgetting to upper-case.\n- Building with `+=` in a loop works here but is the habit `StringBuilder` replaces."),
  ),
# ------------------------------------------------------------------ java-code-leap-year
J("java-code-leap-year", "Leap year", "Easy", "Java basics",
  r"""
In class `Solution`, write

```java
static boolean isLeapYear(int year)
```

A year is a leap year if it is divisible by 4, **except** years divisible by 100, which are leap years only
if they are also divisible by 400.

**Examples** `isLeapYear(2024)` → `true`; `isLeapYear(1900)` → `false`; `isLeapYear(2000)` → `true`;
`isLeapYear(2023)` → `false`. `year` is at least 1.
""",
  '''class Solution {
    static boolean isLeapYear(int year) {
        // your code
        return false;
    }
}
''',
  '''class Solution {
    static boolean isLeapYear(int year) {
        return year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    }
}
''',
  ["eq(Solution.isLeapYear(2024), true)", "eq(Solution.isLeapYear(1900), false)", "eq(Solution.isLeapYear(2000), true)", "eq(Solution.isLeapYear(2023), false)",
   "eq(Solution.isLeapYear(2100), false)", "eq(Solution.isLeapYear(2400), true)", "eq(Solution.isLeapYear(4), true)", "eq(Solution.isLeapYear(1), false)",
   "eq(Solution.isLeapYear(100), false)", "eq(Solution.isLeapYear(1996), true)"],
  ['''class Solution {
    static boolean isLeapYear(int year) {
        return year % 4 == 0;
    }
}
''', '''class Solution {
    static boolean isLeapYear(int year) {
        return year % 4 == 0 && year % 100 != 0;
    }
}
'''],
  G("Lesson *Anatomy of a class, main, and your first statements*: `if`, comparison and the logical operators `&&`, `||`.",
    "Translate the sentence into a boolean expression: divisible by 4 AND (not divisible by 100 OR divisible by 400).",
    ["`year % 4 == 0` tests divisibility by 4.", "The exception has its own exception, so parentheses are needed.", "A boolean expression can be returned directly; no `if` is required."],
    "Three nested `if` statements, from the most specific rule (400) to the least (4), give the same answer and are easier to read for some people.",
    r"""**Dry run** 1900: `1900 % 4 == 0` true; `1900 % 100 != 0` false; `1900 % 400 == 0` false (remainder 300) → `true && (false || false)` → `false`.

```java
class Solution {
    static boolean isLeapYear(int year) {
        return year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    }
}
```

In real code use the library: `java.time.Year.isLeap(year)`.""",
    "Time O(1), space O(1).",
    "- Stopping at 'divisible by 4'.\n- Forgetting the 400 rule.\n- Missing parentheses: `&&` binds tighter than `||`."),
  ),
# ------------------------------------------------------------------ java-code-fizzbuzz
J("java-code-fizzbuzz", "FizzBuzz", "Easy", "Java loops",
  r"""
In class `Solution`, write

```java
static String fizzBuzz(int n)
```

For the numbers 1 to `n`, produce one token each, separated by single spaces (no space at the end):

- `"FizzBuzz"` if the number is divisible by both 3 and 5;
- `"Fizz"` if divisible by 3;
- `"Buzz"` if divisible by 5;
- otherwise the number itself.

For `n <= 0` return `""`.

**Example** `fizzBuzz(5)` → `"1 2 Fizz 4 Buzz"`.
""",
  '''class Solution {
    static String fizzBuzz(int n) {
        // your code
        return "";
    }
}
''',
  '''class Solution {
    static String fizzBuzz(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 1; i <= n; i++) {
            if (i > 1) {
                sb.append(' ');
            }
            if (i % 15 == 0) {
                sb.append("FizzBuzz");
            } else if (i % 3 == 0) {
                sb.append("Fizz");
            } else if (i % 5 == 0) {
                sb.append("Buzz");
            } else {
                sb.append(i);
            }
        }
        return sb.toString();
    }
}
''',
  ['eq(Solution.fizzBuzz(5), "1 2 Fizz 4 Buzz")', 'eq(Solution.fizzBuzz(1), "1")', 'eq(Solution.fizzBuzz(0), "")', 'eq(Solution.fizzBuzz(-3), "")',
   'eq(Solution.fizzBuzz(3), "1 2 Fizz")', 'eq(Solution.fizzBuzz(15), "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz")',
   'yes(Solution.fizzBuzz(30).endsWith("29 FizzBuzz"), "the end of fizzBuzz(30) is wrong")',
   'eq(Solution.fizzBuzz(100).split(" ").length, 100)', 'yes(!Solution.fizzBuzz(20).endsWith(" "), "trailing space")'],
  ['''class Solution {
    static String fizzBuzz(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 1; i <= n; i++) {
            if (i > 1) sb.append(' ');
            if (i % 3 == 0) sb.append("Fizz");
            else if (i % 5 == 0) sb.append("Buzz");
            else if (i % 15 == 0) sb.append("FizzBuzz");
            else sb.append(i);
        }
        return sb.toString();
    }
}
''', '''class Solution {
    static String fizzBuzz(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 1; i < n; i++) {
            if (i > 1) sb.append(' ');
            if (i % 15 == 0) sb.append("FizzBuzz");
            else if (i % 3 == 0) sb.append("Fizz");
            else if (i % 5 == 0) sb.append("Buzz");
            else sb.append(i);
        }
        return sb.toString();
    }
}
'''],
  G("Lesson *Loops, operators and casting*: the counting `for` loop and `%`.",
    "Loop from 1 to n, decide the token for each number, and join the tokens with spaces. The only subtlety is testing the most specific condition first.",
    ["Test divisibility by 15 before 3 and 5.", "Append a space before every token except the first.", "Use a `StringBuilder` and return `sb.toString()`."],
    "Collect the tokens in a `List<String>` and call `String.join(\" \", tokens)`: slightly more memory, and no separator bookkeeping.",
    r"""**Dry run** `fizzBuzz(5)`: 1 → `1`; 2 → ` 2`; 3 → ` Fizz`; 4 → ` 4`; 5 → ` Buzz`. Result `"1 2 Fizz 4 Buzz"`.

```java
class Solution {
    static String fizzBuzz(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 1; i <= n; i++) {
            if (i > 1) sb.append(' ');
            if (i % 15 == 0)     sb.append("FizzBuzz");
            else if (i % 3 == 0) sb.append("Fizz");
            else if (i % 5 == 0) sb.append("Buzz");
            else                 sb.append(i);
        }
        return sb.toString();
    }
}
```""",
    "Time O(n), space O(n) for the result.",
    "- Testing 3 before 15, so 15 prints `Fizz`.\n- `i < n` instead of `i <= n`.\n- A trailing space."),
  ),
# ------------------------------------------------------------------ java-code-count-vowels
J("java-code-count-vowels", "Count vowels", "Easy", "Java loops",
  r"""
In class `Solution`, write

```java
static int countVowels(String text)
```

returning how many characters of `text` are vowels: `a`, `e`, `i`, `o`, `u`, in either upper or lower case.

**Examples** `countVowels("Education")` → `5`; `countVowels("rhythm")` → `0`; `countVowels("")` → `0`.
""",
  '''class Solution {
    static int countVowels(String text) {
        // your code
        return 0;
    }
}
''',
  '''class Solution {
    static int countVowels(String text) {
        int count = 0;
        for (int i = 0; i < text.length(); i++) {
            char c = Character.toLowerCase(text.charAt(i));
            if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') {
                count++;
            }
        }
        return count;
    }
}
''',
  ['eq(Solution.countVowels("Education"), 5)', 'eq(Solution.countVowels("rhythm"), 0)', 'eq(Solution.countVowels(""), 0)', 'eq(Solution.countVowels("AEIOU"), 5)',
   'eq(Solution.countVowels("aaa"), 3)', 'eq(Solution.countVowels("Hello, World!"), 3)', 'eq(Solution.countVowels("xyz XYZ 123"), 0)',
   'eq(Solution.countVowels("queue"), 4)', 'eq(Solution.countVowels("U"), 1)'],
  ['''class Solution {
    static int countVowels(String text) {
        int count = 0;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') count++;
        }
        return count;
    }
}
''', '''class Solution {
    static int countVowels(String text) {
        int count = 0;
        for (int i = 1; i < text.length(); i++) {
            char c = Character.toLowerCase(text.charAt(i));
            if ("aeiou".indexOf(c) >= 0) count++;
        }
        return count;
    }
}
'''],
  G("Lessons *Loops, operators and casting* and *Packages, imports and the String toolbox*.",
    "Visit every character once and count those that belong to a small set.",
    ["Loop with an index from 0 to `text.length() - 1` and read `text.charAt(i)`.", "Convert each character to lower case first, so one comparison handles both cases.",
     "`\"aeiou\".indexOf(c) >= 0` is a compact membership test."],
    "Count each vowel separately with five passes over the text. Correct, and five times the work.",
    r"""**Dry run** `"Education"`: E, u, a, i, o are vowels → 5; d, c, t, n are not.

```java
class Solution {
    static int countVowels(String text) {
        int count = 0;
        for (char c : text.toLowerCase().toCharArray()) {      // for-each over the characters
            if ("aeiou".indexOf(c) >= 0) {
                count++;
            }
        }
        return count;
    }
}
```""",
    "Time O(n), space O(1) (O(n) if you copy to a char array).",
    "- Counting only lower-case vowels.\n- Starting the index at 1.\n- Comparing a `char` with a `String` such as `\"a\"`: use single quotes for characters."),
  ),
# ------------------------------------------------------------------ java-code-index-of-max
J("java-code-index-of-max", "Index of the largest element", "Easy", "Java arrays",
  r"""
In class `Solution`, write

```java
static int indexOfMax(int[] values)
```

Return the index of the largest element. If the largest value occurs several times, return the **first**
such index. For an empty array return `-1`.

**Examples** `indexOfMax(new int[] {3, 9, 2, 9})` → `1`; `indexOfMax(new int[] {})` → `-1`;
`indexOfMax(new int[] {-5, -2, -8})` → `1`.
""",
  '''class Solution {
    static int indexOfMax(int[] values) {
        // your code
        return -1;
    }
}
''',
  '''class Solution {
    static int indexOfMax(int[] values) {
        if (values.length == 0) {
            return -1;
        }
        int best = 0;
        for (int i = 1; i < values.length; i++) {
            if (values[i] > values[best]) {
                best = i;
            }
        }
        return best;
    }
}
''',
  ["eq(Solution.indexOfMax(new int[] {3, 9, 2, 9}), 1)", "eq(Solution.indexOfMax(new int[] {}), -1)", "eq(Solution.indexOfMax(new int[] {-5, -2, -8}), 1)",
   "eq(Solution.indexOfMax(new int[] {7}), 0)", "eq(Solution.indexOfMax(new int[] {1, 2, 3, 4}), 3)", "eq(Solution.indexOfMax(new int[] {4, 3, 2, 1}), 0)",
   "eq(Solution.indexOfMax(new int[] {5, 5, 5}), 0)", "eq(Solution.indexOfMax(new int[] {Integer.MIN_VALUE, Integer.MIN_VALUE}), 0)",
   "eq(Solution.indexOfMax(new int[] {0, -1, Integer.MAX_VALUE, 3}), 2)"],
  ['''class Solution {
    static int indexOfMax(int[] values) {
        int best = -1, max = 0;
        for (int i = 0; i < values.length; i++) {
            if (values[i] > max) { max = values[i]; best = i; }
        }
        return best;
    }
}
''', '''class Solution {
    static int indexOfMax(int[] values) {
        if (values.length == 0) return -1;
        int best = 0;
        for (int i = 1; i < values.length; i++) {
            if (values[i] >= values[best]) best = i;
        }
        return best;
    }
}
'''],
  G("Lesson *References, arrays, the stack and the heap*: arrays, indices and `length`.",
    "Keep the index of the best element seen so far, starting with the first element, and replace it only when a strictly larger one appears.",
    ["Handle the empty array before the loop.", "Start with `best = 0` and loop from index 1.", "Use `>` and not `>=`, so that ties keep the earlier index."],
    "Find the maximum value in one pass and its first position in a second pass. Two passes, same result.",
    r"""**Dry run** `{3, 9, 2, 9}`: best 0 (3). i=1: 9 > 3 → best 1. i=2: 2 > 9? no. i=3: 9 > 9? no. Return 1.

```java
class Solution {
    static int indexOfMax(int[] values) {
        if (values.length == 0) return -1;
        int best = 0;
        for (int i = 1; i < values.length; i++) {
            if (values[i] > values[best]) best = i;
        }
        return best;
    }
}
```""",
    "Time O(n), space O(1).",
    "- Initialising the running maximum to 0, which fails for arrays of negative numbers.\n- `>=`, which returns the last maximum.\n- Reading `values[0]` of an empty array."),
  ),
# ------------------------------------------------------------------ java-code-reverse-array
J("java-code-reverse-array", "Reversed copy of an array", "Easy", "Java arrays",
  r"""
In class `Solution`, write

```java
static int[] reversed(int[] values)
```

Return a **new** array holding the elements of `values` in reverse order. The array passed in must be left
unchanged.

**Examples** `reversed(new int[] {1, 2, 3})` → `{3, 2, 1}`; `reversed(new int[] {})` → `{}`.
""",
  '''class Solution {
    static int[] reversed(int[] values) {
        // your code
        return values;
    }
}
''',
  '''class Solution {
    static int[] reversed(int[] values) {
        int n = values.length;
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            out[i] = values[n - 1 - i];
        }
        return out;
    }
}
''',
  ["arr(Solution.reversed(new int[] {1, 2, 3}), new int[] {3, 2, 1})", "arr(Solution.reversed(new int[] {}), new int[] {})",
   "arr(Solution.reversed(new int[] {7}), new int[] {7})", "arr(Solution.reversed(new int[] {1, 2}), new int[] {2, 1})",
   "arr(Solution.reversed(new int[] {1, 2, 3, 4}), new int[] {4, 3, 2, 1})", "arr(Solution.reversed(new int[] {5, 5, 9}), new int[] {9, 5, 5})",
   "{ int[] in = {1, 2, 3}; Solution.reversed(in); return arr(in, new int[] {1, 2, 3}); }",
   "{ int[] in = {1, 2, 3}; return yes(Solution.reversed(in) != in, \"must return a new array\"); }",
   "{ int[] in = {4, 5}; int[] out = Solution.reversed(in); out[0] = 99; return arr(in, new int[] {4, 5}); }"],
  ['''class Solution {
    static int[] reversed(int[] values) {
        for (int i = 0, j = values.length - 1; i < j; i++, j--) {
            int t = values[i]; values[i] = values[j]; values[j] = t;
        }
        return values;
    }
}
''', '''class Solution {
    static int[] reversed(int[] values) {
        int n = values.length;
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            out[i] = values[n - i];
        }
        return out;
    }
}
'''],
  G("Lesson *References, arrays, the stack and the heap*: arrays are objects; a method receives a copy of the reference.",
    "Because the caller's array is the same object the method sees, reversing 'in place' would change the caller's data. Allocate a second array and fill it from the far end.",
    ["`new int[n]` creates the result.", "Element `i` of the result is element `n - 1 - i` of the input.", "Return the new array, never `values`."],
    "Copy with `values.clone()` and then swap pairs inside the copy from both ends: also fine, and it uses the swap idiom.",
    r"""**Dry run** `{1, 2, 3}`, n = 3: `out[0] = values[2] = 3`, `out[1] = values[1] = 2`, `out[2] = values[0] = 1`.

```java
class Solution {
    static int[] reversed(int[] values) {
        int n = values.length;
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            out[i] = values[n - 1 - i];
        }
        return out;
    }
}
```""",
    "Time O(n), space O(n) for the new array.",
    "- Reversing the caller's array.\n- `values[n - i]`, an off-by-one that throws `ArrayIndexOutOfBoundsException` at `i = 0`.\n- Returning the input for the empty case is tempting; a new empty array keeps the contract simple."),
  ),
# ------------------------------------------------------------------ java-code-is-palindrome
J("java-code-is-palindrome", "Palindrome, ignoring punctuation", "Easy", "Java methods",
  r"""
In class `Solution`, write

```java
static boolean isPalindrome(String text)
```

Return `true` if `text` reads the same forwards and backwards when you consider **only letters and digits**
and ignore case. A text with no letters or digits counts as a palindrome.

**Examples** `isPalindrome("A man, a plan, a canal: Panama")` → `true`; `isPalindrome("race a car")` → `false`;
`isPalindrome("")` → `true`.

Useful library methods: `Character.isLetterOrDigit(c)` and `Character.toLowerCase(c)`.
""",
  '''class Solution {
    static boolean isPalindrome(String text) {
        // your code
        return false;
    }
}
''',
  '''class Solution {
    static boolean isPalindrome(String text) {
        int i = 0, j = text.length() - 1;
        while (i < j) {
            if (!Character.isLetterOrDigit(text.charAt(i))) {
                i++;
            } else if (!Character.isLetterOrDigit(text.charAt(j))) {
                j--;
            } else {
                if (Character.toLowerCase(text.charAt(i)) != Character.toLowerCase(text.charAt(j))) {
                    return false;
                }
                i++;
                j--;
            }
        }
        return true;
    }
}
''',
  ['eq(Solution.isPalindrome("A man, a plan, a canal: Panama"), true)', 'eq(Solution.isPalindrome("race a car"), false)', 'eq(Solution.isPalindrome(""), true)',
   'eq(Solution.isPalindrome("x"), true)', 'eq(Solution.isPalindrome(".,!"), true)', 'eq(Solution.isPalindrome("ab"), false)',
   'eq(Solution.isPalindrome("No lemon, no melon"), true)', 'eq(Solution.isPalindrome("0P"), false)', 'eq(Solution.isPalindrome("12321"), true)',
   'eq(Solution.isPalindrome("a.b"), false)'],
  ['''class Solution {
    static boolean isPalindrome(String text) {
        return new StringBuilder(text).reverse().toString().equals(text);
    }
}
''', '''class Solution {
    static boolean isPalindrome(String text) {
        int i = 0, j = text.length() - 1;
        while (i < j) {
            if (!Character.isLetter(text.charAt(i))) i++;
            else if (!Character.isLetter(text.charAt(j))) j--;
            else {
                if (Character.toLowerCase(text.charAt(i)) != Character.toLowerCase(text.charAt(j))) return false;
                i++; j--;
            }
        }
        return true;
    }
}
'''],
  G("Lessons *Methods, parameters, return values and pass-by-value* and *Loops, operators and casting*.",
    "Two fingers, one at each end, walking toward each other. Skip anything that is not a letter or digit; compare what remains.",
    ["Use two indices `i` and `j`.", "If the character at `i` should be ignored, move `i`; likewise for `j`.", "When both are significant, compare in lower case; on a mismatch return `false` at once."],
    "Build a cleaned string (letters and digits only, lower-cased) with a `StringBuilder`, then compare it with its reverse. Simple and correct, with O(n) extra memory.",
    r"""**Dry run** `"0P"`: i=0 (`0`), j=1 (`P`). Both significant; `'0'` vs `'p'` differ → `false`.

```java
class Solution {
    static boolean isPalindrome(String text) {
        int i = 0, j = text.length() - 1;
        while (i < j) {
            char a = text.charAt(i), b = text.charAt(j);
            if (!Character.isLetterOrDigit(a))      i++;
            else if (!Character.isLetterOrDigit(b)) j--;
            else {
                if (Character.toLowerCase(a) != Character.toLowerCase(b)) return false;
                i++;
                j--;
            }
        }
        return true;
    }
}
```""",
    "Time O(n), space O(1).",
    "- Comparing the raw string with its reverse, which respects case and punctuation.\n- Ignoring digits.\n- Letting the indices cross and read out of bounds."),
  ),
# ------------------------------------------------------------------ java-code-bank-account
J("java-code-bank-account", "A class with state: Account", "Easy", "Java classes",
  r"""
Write your first class with **encapsulated state**. Inside `Solution`, complete the nested class `Account`:

```java
static class Account {
    Account(String owner)           // balance starts at 0
    String owner()
    long balance()                  // in pence
    void deposit(long pence)        // throws IllegalArgumentException if pence <= 0
    boolean withdraw(long pence)    // if pence <= 0 or pence > balance: change nothing, return false; else subtract, return true
}
```

Keep the fields `private`. Each `Account` object must have its own balance.

**Example**

```java
Solution.Account a = new Solution.Account("Noor");
a.deposit(500);
a.withdraw(200);     // true
a.withdraw(900);     // false
a.balance();         // 300
```
""",
  '''class Solution {
    static class Account {
        // fields

        Account(String owner) {
        }

        String owner() { return null; }

        long balance() { return 0; }

        void deposit(long pence) {
        }

        boolean withdraw(long pence) { return false; }
    }
}
''',
  '''class Solution {
    static class Account {
        private final String owner;
        private long balance;

        Account(String owner) {
            this.owner = owner;
        }

        String owner() { return owner; }

        long balance() { return balance; }

        void deposit(long pence) {
            if (pence <= 0) {
                throw new IllegalArgumentException("deposit must be positive: " + pence);
            }
            balance += pence;
        }

        boolean withdraw(long pence) {
            if (pence <= 0 || pence > balance) {
                return false;
            }
            balance -= pence;
            return true;
        }
    }
}
''',
  ['{ Solution.Account a = new Solution.Account("Noor"); return eq(a.balance(), 0L); }',
   '{ Solution.Account a = new Solution.Account("Noor"); return eq(a.owner(), "Noor"); }',
   '{ Solution.Account a = new Solution.Account("Noor"); a.deposit(500); a.deposit(1); return eq(a.balance(), 501L); }',
   '{ Solution.Account a = new Solution.Account("Noor"); a.deposit(500); boolean ok = a.withdraw(200); return ok ? eq(a.balance(), 300L) : "withdraw returned false"; }',
   '{ Solution.Account a = new Solution.Account("Noor"); a.deposit(500); boolean ok = a.withdraw(900); return ok ? "withdraw should fail" : eq(a.balance(), 500L); }',
   '{ Solution.Account a = new Solution.Account("Noor"); a.deposit(500); return eq(a.withdraw(500), true); }',
   '{ Solution.Account a = new Solution.Account("Noor"); a.deposit(500); boolean ok = a.withdraw(-5); return ok ? "negative withdraw accepted" : eq(a.balance(), 500L); }',
   '{ Solution.Account a = new Solution.Account("Noor"); return thrown(IllegalArgumentException.class, () -> { a.deposit(0); return null; }); }',
   '{ Solution.Account a = new Solution.Account("Noor"); return thrown(IllegalArgumentException.class, () -> { a.deposit(-10); return null; }); }',
   '{ Solution.Account a = new Solution.Account("A"); Solution.Account b = new Solution.Account("B"); a.deposit(100); return eq(b.balance(), 0L); }',
   '{ Solution.Account a = new Solution.Account("A"); a.deposit(100); return eq(a.withdraw(0), false); }'],
  ['''class Solution {
    static class Account {
        private final String owner;
        private static long balance;
        Account(String owner) { this.owner = owner; }
        String owner() { return owner; }
        long balance() { return balance; }
        void deposit(long pence) {
            if (pence <= 0) throw new IllegalArgumentException();
            balance += pence;
        }
        boolean withdraw(long pence) {
            if (pence <= 0 || pence > balance) return false;
            balance -= pence;
            return true;
        }
    }
}
''', '''class Solution {
    static class Account {
        private final String owner;
        private long balance;
        Account(String owner) { this.owner = owner; }
        String owner() { return owner; }
        long balance() { return balance; }
        void deposit(long pence) { balance += pence; }
        boolean withdraw(long pence) {
            balance -= pence;
            return balance >= 0;
        }
    }
}
'''],
  G("Lessons *Classes and objects: blueprint and building* and *Encapsulation: private fields, getters and setters*.",
    "The class guards one rule (an invariant): the balance never goes below zero. Because the field is private, only `deposit` and `withdraw` can change it, so the rule is checked in exactly two places.",
    ["Two fields: `private final String owner` and `private long balance`.", "`this.owner = owner;` in the constructor distinguishes the field from the parameter.",
     "In `withdraw`, test the failing conditions first and return `false` before changing anything."],
    "Public fields would 'work' and would let any code set a negative balance. The point of the exercise is that the class, not its callers, enforces the rule.",
    r"""**Dry run** of the example: balance 0 → deposit 500 → 500 → withdraw 200: 200 ≤ 500, so 300 and `true` → withdraw 900: 900 > 300, nothing changes, `false` → balance 300.

```java
class Solution {
    static class Account {
        private final String owner;
        private long balance;                      // instance field: one per Account

        Account(String owner) { this.owner = owner; }

        String owner()  { return owner; }
        long balance()  { return balance; }

        void deposit(long pence) {
            if (pence <= 0) throw new IllegalArgumentException("deposit must be positive: " + pence);
            balance += pence;
        }

        boolean withdraw(long pence) {
            if (pence <= 0 || pence > balance) return false;
            balance -= pence;
            return true;
        }
    }
}
```""",
    "Every method is O(1); each object uses O(1) space.",
    "- Declaring `balance` as `static`, so that all accounts share one balance.\n- Subtracting first and checking afterwards, which leaves the account overdrawn.\n- Forgetting to validate `deposit`."),
  ),
# ------------------------------------------------------------------ java-code-ticket-counter
J("java-code-ticket-counter", "static versus instance: Ticket", "Easy", "Java classes",
  r"""
Inside `Solution`, complete the nested class `Ticket` so that every new ticket receives the next number.

```java
static class Ticket {
    Ticket()                 // takes the next number
    int number()             // this ticket's number
    static int issued()      // how many tickets have been created so far
    static void reset()      // start again: issued() becomes 0 and the next ticket gets number 1
}
```

The first ticket after a reset has number 1, the second 2, and so on. `issued()` must work even when no
ticket exists. A ticket keeps its number for ever, even after later tickets are created or `reset` is called.
""",
  '''class Solution {
    static class Ticket {
        // fields

        Ticket() {
        }

        int number() { return 0; }

        static int issued() { return 0; }

        static void reset() {
        }
    }
}
''',
  '''class Solution {
    static class Ticket {
        private static int issued = 0;
        private final int number;

        Ticket() {
            issued++;
            number = issued;
        }

        int number() { return number; }

        static int issued() { return issued; }

        static void reset() {
            issued = 0;
        }
    }
}
''',
  ['{ Solution.Ticket.reset(); return eq(Solution.Ticket.issued(), 0); }',
   '{ Solution.Ticket.reset(); Solution.Ticket a = new Solution.Ticket(); return eq(a.number(), 1); }',
   '{ Solution.Ticket.reset(); new Solution.Ticket(); Solution.Ticket b = new Solution.Ticket(); return eq(b.number(), 2); }',
   '{ Solution.Ticket.reset(); new Solution.Ticket(); new Solution.Ticket(); new Solution.Ticket(); return eq(Solution.Ticket.issued(), 3); }',
   '{ Solution.Ticket.reset(); Solution.Ticket a = new Solution.Ticket(); new Solution.Ticket(); new Solution.Ticket(); return eq(a.number(), 1); }',
   '{ Solution.Ticket.reset(); Solution.Ticket a = new Solution.Ticket(); Solution.Ticket b = new Solution.Ticket(); return eq(a.number() + b.number(), 3); }',
   '{ Solution.Ticket.reset(); Solution.Ticket a = new Solution.Ticket(); new Solution.Ticket(); Solution.Ticket.reset(); return eq(a.number(), 1); }',
   '{ Solution.Ticket.reset(); new Solution.Ticket(); new Solution.Ticket(); Solution.Ticket.reset(); Solution.Ticket c = new Solution.Ticket(); return eq(c.number(), 1); }',
   '{ Solution.Ticket.reset(); for (int i = 0; i < 50; i++) new Solution.Ticket(); return eq(new Solution.Ticket().number(), 51); }'],
  ['''class Solution {
    static class Ticket {
        private static int issued = 0;
        Ticket() { issued++; }
        int number() { return issued; }
        static int issued() { return issued; }
        static void reset() { issued = 0; }
    }
}
''', '''class Solution {
    static class Ticket {
        private int issued = 0;
        private final int number;
        private static int total = 0;
        Ticket() { issued++; number = issued; total++; }
        int number() { return number; }
        static int issued() { return total; }
        static void reset() { total = 0; }
    }
}
'''],
  G("Lesson *static, final, constants and the Math class*: one copy per class versus one copy per object.",
    "The running count belongs to the class as a whole, so it is `static`. Each ticket's own number belongs to that ticket, so it is an instance field, copied from the counter at construction.",
    ["`private static int issued` is shared by all tickets.", "In the constructor: increment the shared counter, then store its value in `private final int number`.", "`number()` returns the instance field, not the counter."],
    "Returning the static counter from `number()` is the usual first mistake: every ticket would then report the latest number.",
    r"""**Dry run** after `reset()`: `new Ticket()` → issued 1, number 1. `new Ticket()` → issued 2, number 2. The first ticket still answers 1, because it stored its own copy.

```java
class Solution {
    static class Ticket {
        private static int issued = 0;       // one for the class
        private final int number;            // one per ticket

        Ticket() {
            issued++;
            number = issued;
        }

        int number()          { return number; }
        static int issued()   { return issued; }
        static void reset()   { issued = 0; }
    }
}
```""",
    "All operations O(1).",
    "- Making the per-ticket number static.\n- Making the counter an instance field: every ticket would be number 1.\n- Calling an instance method from a static one without an object."),
  ),
# ------------------------------------------------------------------ java-code-shapes
J("java-code-shapes", "An interface and two implementations", "Medium", "Java interfaces",
  r"""
Inside `Solution` you are given the interface

```java
interface Shape {
    double area();
    String name();
}
```

Write two nested classes that implement it, and one method that works with **any** shape:

```java
static class Circle implements Shape     // Circle(double radius);         area = Math.PI * r * r;  name() returns "circle"
static class Rect implements Shape       // Rect(double width, double height);  area = w * h;       name() returns "rect"
static double totalArea(java.util.List<Shape> shapes)                 // sum of the areas; 0 for an empty list
static String largest(java.util.List<Shape> shapes)                   // name() of the shape with the largest area; "" for an empty list
```

`totalArea` and `largest` must not test which class a shape is; they call `area()` and `name()` and let
dynamic dispatch do the rest. If two shapes tie for largest, return the name of the one that comes first.
""",
  '''class Solution {
    interface Shape {
        double area();
        String name();
    }

    // write Circle and Rect here

    static double totalArea(java.util.List<Shape> shapes) {
        return 0;
    }

    static String largest(java.util.List<Shape> shapes) {
        return "";
    }
}
''',
  '''class Solution {
    interface Shape {
        double area();
        String name();
    }

    static class Circle implements Shape {
        private final double radius;
        Circle(double radius) { this.radius = radius; }
        @Override public double area() { return Math.PI * radius * radius; }
        @Override public String name() { return "circle"; }
    }

    static class Rect implements Shape {
        private final double width, height;
        Rect(double width, double height) { this.width = width; this.height = height; }
        @Override public double area() { return width * height; }
        @Override public String name() { return "rect"; }
    }

    static double totalArea(java.util.List<Shape> shapes) {
        double sum = 0;
        for (Shape s : shapes) {
            sum += s.area();
        }
        return sum;
    }

    static String largest(java.util.List<Shape> shapes) {
        Shape best = null;
        for (Shape s : shapes) {
            if (best == null || s.area() > best.area()) {
                best = s;
            }
        }
        return best == null ? "" : best.name();
    }
}
''',
  ["near(new Solution.Circle(1).area(), Math.PI)", "near(new Solution.Rect(2, 3).area(), 6.0)", 'eq(new Solution.Circle(2).name(), "circle")', 'eq(new Solution.Rect(1, 1).name(), "rect")',
   "near(Solution.totalArea(List.of()), 0.0)", "near(Solution.totalArea(List.of(new Solution.Rect(2, 3), new Solution.Circle(1), new Solution.Rect(1, 1))), 7.0 + Math.PI)",
   'eq(Solution.largest(List.of(new Solution.Rect(2, 3), new Solution.Circle(1))), "rect")', 'eq(Solution.largest(List.of(new Solution.Rect(1, 1), new Solution.Circle(3))), "circle")',
   'eq(Solution.largest(List.of()), "")',
   '{ Solution.Shape tri = new Solution.Shape() { public double area() { return 100; } public String name() { return "triangle"; } }; return eq(Solution.largest(List.of(new Solution.Circle(1), tri)), "triangle"); }',
   '{ Solution.Shape tri = new Solution.Shape() { public double area() { return 2.5; } public String name() { return "triangle"; } }; return near(Solution.totalArea(List.of(tri, tri)), 5.0); }'],
  ['''class Solution {
    interface Shape { double area(); String name(); }
    static class Circle implements Shape {
        private final double radius;
        Circle(double radius) { this.radius = radius; }
        public double area() { return Math.PI * radius * radius; }
        public String name() { return "circle"; }
    }
    static class Rect implements Shape {
        private final double width, height;
        Rect(double width, double height) { this.width = width; this.height = height; }
        public double area() { return width * height; }
        public String name() { return "rect"; }
    }
    static double totalArea(java.util.List<Shape> shapes) {
        double sum = 0;
        for (Shape s : shapes) {
            if (s instanceof Circle c) sum += c.area();
            else if (s instanceof Rect r) sum += r.area();
        }
        return sum;
    }
    static String largest(java.util.List<Shape> shapes) {
        Shape best = null;
        for (Shape s : shapes) if (best == null || s.area() > best.area()) best = s;
        return best == null ? "" : best.name();
    }
}
''', '''class Solution {
    interface Shape { double area(); String name(); }
    static class Circle implements Shape {
        private final double radius;
        Circle(double radius) { this.radius = radius; }
        public double area() { return 2 * Math.PI * radius; }
        public String name() { return "circle"; }
    }
    static class Rect implements Shape {
        private final double width, height;
        Rect(double width, double height) { this.width = width; this.height = height; }
        public double area() { return width * height; }
        public String name() { return "rect"; }
    }
    static double totalArea(java.util.List<Shape> shapes) {
        double sum = 0;
        for (Shape s : shapes) sum += s.area();
        return sum;
    }
    static String largest(java.util.List<Shape> shapes) {
        Shape best = null;
        for (Shape s : shapes) if (best == null || s.area() > best.area()) best = s;
        return best == null ? "" : best.name();
    }
}
'''],
  G("Lessons *Interfaces, default methods, sealed types and pattern matching* and *Polymorphism, overriding and overloading*.",
    "The interface is the contract; `totalArea` and `largest` are written against the contract alone. The tests pass in a shape class your code has never seen, which only works if you call `area()` and do not ask what kind of shape it is.",
    ["Implementing methods must be `public`.", "Loop over `List<Shape>` and call `s.area()`; the object's own class decides which code runs.", "For `largest`, keep the best shape so far and replace it only on a strictly larger area."],
    "A chain of `instanceof` tests handles the two known shapes and silently ignores every other implementation. It is exactly the design the open/closed principle warns about.",
    r"""**Dry run** `largest([Rect 2×3, Circle r=1])`: best = rect (6.0). Circle area 3.14… > 6? No. Answer `"rect"`.

```java
static class Circle implements Shape {
    private final double radius;
    Circle(double radius) { this.radius = radius; }
    @Override public double area() { return Math.PI * radius * radius; }
    @Override public String name() { return "circle"; }
}

static double totalArea(java.util.List<Shape> shapes) {
    double sum = 0;
    for (Shape s : shapes) sum += s.area();          // dynamic dispatch
    return sum;
}
// with streams: shapes.stream().mapToDouble(Shape::area).sum()
```""",
    "Time O(n) for both methods, space O(1).",
    "- Forgetting `public` on the implementing methods (a compile error).\n- Type-testing inside `totalArea`.\n- Circumference `2πr` instead of area `πr²`.\n- `>=` in `largest`, which returns the last of several equal shapes."),
  ),
# ------------------------------------------------------------------ java-code-employee-pay
J("java-code-employee-pay", "Abstract class and overriding: payroll", "Medium", "Java inheritance",
  r"""
Inside `Solution`, build a small hierarchy.

```java
static abstract class Employee {
    Employee(String name)
    String name()
    abstract int weeklyPay();                    // in pounds
    String payslip()                             // returns name() + ": " + weeklyPay()   (written ONCE, here)
}

static class Salaried extends Employee          // Salaried(String name, int annualSalary);  weeklyPay = annualSalary / 52 (integer division)
static class Hourly extends Employee            // Hourly(String name, int ratePerHour, int hours)
                                                //   first 40 hours at the rate, hours beyond 40 at DOUBLE the rate
static class Manager extends Salaried           // Manager(String name, int annualSalary, int weeklyBonus)
                                                //   weeklyPay = the Salaried weekly pay + weeklyBonus  (reuse it with super)

static int payroll(java.util.List<Employee> staff)     // sum of weeklyPay()
```

**Example** `new Hourly("Bo", 10, 45).weeklyPay()` → `500` (40 × 10 + 5 × 20);
`new Manager("Cy", 52000, 150).payslip()` → `"Cy: 1150"`.
""",
  '''class Solution {
    static abstract class Employee {
        Employee(String name) {
        }

        String name() { return null; }

        abstract int weeklyPay();

        String payslip() { return null; }
    }

    // write Salaried, Hourly and Manager here

    static int payroll(java.util.List<Employee> staff) {
        return 0;
    }
}
''',
  '''class Solution {
    static abstract class Employee {
        private final String name;

        Employee(String name) {
            this.name = name;
        }

        String name() { return name; }

        abstract int weeklyPay();

        String payslip() { return name() + ": " + weeklyPay(); }
    }

    static class Salaried extends Employee {
        private final int annualSalary;

        Salaried(String name, int annualSalary) {
            super(name);
            this.annualSalary = annualSalary;
        }

        @Override int weeklyPay() { return annualSalary / 52; }
    }

    static class Hourly extends Employee {
        private final int rate, hours;

        Hourly(String name, int ratePerHour, int hours) {
            super(name);
            this.rate = ratePerHour;
            this.hours = hours;
        }

        @Override int weeklyPay() {
            int normal = Math.min(hours, 40);
            int overtime = Math.max(hours - 40, 0);
            return normal * rate + overtime * rate * 2;
        }
    }

    static class Manager extends Salaried {
        private final int weeklyBonus;

        Manager(String name, int annualSalary, int weeklyBonus) {
            super(name, annualSalary);
            this.weeklyBonus = weeklyBonus;
        }

        @Override int weeklyPay() { return super.weeklyPay() + weeklyBonus; }
    }

    static int payroll(java.util.List<Employee> staff) {
        int total = 0;
        for (Employee e : staff) {
            total += e.weeklyPay();
        }
        return total;
    }
}
''',
  ['eq(new Solution.Salaried("Ada", 52000).weeklyPay(), 1000)', 'eq(new Solution.Salaried("Ada", 30000).weeklyPay(), 576)',
   'eq(new Solution.Hourly("Bo", 10, 45).weeklyPay(), 500)', 'eq(new Solution.Hourly("Bo", 10, 40).weeklyPay(), 400)', 'eq(new Solution.Hourly("Bo", 12, 0).weeklyPay(), 0)',
   'eq(new Solution.Manager("Cy", 52000, 150).weeklyPay(), 1150)', 'eq(new Solution.Manager("Cy", 52000, 150).payslip(), "Cy: 1150")',
   'eq(new Solution.Hourly("Di", 8, 10).payslip(), "Di: 80")', 'eq(new Solution.Salaried("Eve", 5200).name(), "Eve")',
   'eq(Solution.payroll(List.of(new Solution.Salaried("A", 52000), new Solution.Hourly("B", 10, 45), new Solution.Manager("C", 52000, 150))), 2650)',
   'eq(Solution.payroll(List.of()), 0)',
   '{ Solution.Employee m = new Solution.Manager("M", 104000, 1); return yes(m instanceof Solution.Salaried, "Manager must extend Salaried"); }'],
  ['''class Solution {
    static abstract class Employee {
        private final String name;
        Employee(String name) { this.name = name; }
        String name() { return name; }
        abstract int weeklyPay();
        String payslip() { return name() + ": " + weeklyPay(); }
    }
    static class Salaried extends Employee {
        private final int annualSalary;
        Salaried(String name, int annualSalary) { super(name); this.annualSalary = annualSalary; }
        @Override int weeklyPay() { return annualSalary / 52; }
    }
    static class Hourly extends Employee {
        private final int rate, hours;
        Hourly(String name, int ratePerHour, int hours) { super(name); this.rate = ratePerHour; this.hours = hours; }
        @Override int weeklyPay() { return hours * rate; }
    }
    static class Manager extends Salaried {
        private final int weeklyBonus;
        Manager(String name, int annualSalary, int weeklyBonus) { super(name, annualSalary); this.weeklyBonus = weeklyBonus; }
        @Override int weeklyPay() { return super.weeklyPay() + weeklyBonus; }
    }
    static int payroll(java.util.List<Employee> staff) {
        int total = 0;
        for (Employee e : staff) total += e.weeklyPay();
        return total;
    }
}
''', '''class Solution {
    static abstract class Employee {
        private final String name;
        Employee(String name) { this.name = name; }
        String name() { return name; }
        abstract int weeklyPay();
        String payslip() { return name() + ": " + weeklyPay(); }
    }
    static class Salaried extends Employee {
        final int annualSalary;
        Salaried(String name, int annualSalary) { super(name); this.annualSalary = annualSalary; }
        @Override int weeklyPay() { return annualSalary / 52; }
    }
    static class Hourly extends Employee {
        private final int rate, hours;
        Hourly(String name, int ratePerHour, int hours) { super(name); this.rate = ratePerHour; this.hours = hours; }
        @Override int weeklyPay() { return Math.min(hours, 40) * rate + Math.max(hours - 40, 0) * rate * 2; }
    }
    static class Manager extends Salaried {
        private final int weeklyBonus;
        Manager(String name, int annualSalary, int weeklyBonus) { super(name, annualSalary); this.weeklyBonus = weeklyBonus; }
        @Override int weeklyPay() { return (annualSalary + weeklyBonus) / 52; }
    }
    static int payroll(java.util.List<Employee> staff) {
        int total = 0;
        for (Employee e : staff) total += e.weeklyPay();
        return total;
    }
}
'''],
  G("Lessons *Inheritance: sharing code through a family tree*, *Abstract classes and the Object class* and *Constructors, this and super*.",
    "`Employee` fixes what every employee has (a name, a payslip format) and leaves one question open: how is the pay computed? Each subclass answers that single question. `payslip()` calls `weeklyPay()` and dynamic dispatch picks the right answer.",
    ["Each subclass constructor must call `super(...)` first, because `Employee` has no no-argument constructor.", "`Hourly`: split the hours into the first 40 and the rest.",
     "`Manager` should not recompute the salary: `super.weeklyPay() + weeklyBonus`."],
    "A single `Employee` class with a `type` field and a `switch` in `weeklyPay` works for three kinds and has to be edited for every new kind: the tagged-class design the hierarchy replaces.",
    r"""**Dry run** `new Manager("Cy", 52000, 150).payslip()`: `payslip` (written in `Employee`) calls `weeklyPay()`; the object is a `Manager`, so `Manager.weeklyPay` runs: `super.weeklyPay()` is `52000 / 52 = 1000`, plus 150 → `"Cy: 1150"`.

```java
static class Hourly extends Employee {
    private final int rate, hours;

    Hourly(String name, int ratePerHour, int hours) {
        super(name);                                   // initialise the Employee part first
        this.rate = ratePerHour;
        this.hours = hours;
    }

    @Override
    int weeklyPay() {
        int normal = Math.min(hours, 40);
        int overtime = Math.max(hours - 40, 0);
        return normal * rate + overtime * rate * 2;
    }
}

static class Manager extends Salaried {
    private final int weeklyBonus;
    Manager(String name, int annualSalary, int weeklyBonus) { super(name, annualSalary); this.weeklyBonus = weeklyBonus; }
    @Override int weeklyPay() { return super.weeklyPay() + weeklyBonus; }
}
```""",
    "Each `weeklyPay` is O(1); `payroll` is O(n).",
    "- Forgetting `super(name)`: 'constructor Employee cannot be applied to given types'.\n- Paying overtime at the normal rate.\n- Adding the weekly bonus to the annual salary before dividing.\n- Duplicating `payslip` in every subclass."),
  ),
# ------------------------------------------------------------------ java-code-safe-divide
J("java-code-safe-divide", "Catching exceptions: parse and divide", "Easy", "Java exceptions",
  r"""
In class `Solution`, write

```java
static String divide(String a, String b)
```

`a` and `b` are text typed by a user. Parse both with `Integer.parseInt` and return the result of the
integer division `a / b` as text. Handle the two things that can go wrong:

- if either text is not a valid whole number, return `"not a number"`;
- if the divisor is zero, return `"division by zero"`.

Use `try` and `catch`; do not test for zero or validate the digits yourself.

**Examples** `divide("17", "5")` → `"3"`; `divide("17", "five")` → `"not a number"`;
`divide("17", "0")` → `"division by zero"`; `divide("-7", "2")` → `"-3"`.
""",
  '''class Solution {
    static String divide(String a, String b) {
        // your code
        return "";
    }
}
''',
  '''class Solution {
    static String divide(String a, String b) {
        try {
            int x = Integer.parseInt(a);
            int y = Integer.parseInt(b);
            return String.valueOf(x / y);
        } catch (NumberFormatException e) {
            return "not a number";
        } catch (ArithmeticException e) {
            return "division by zero";
        }
    }
}
''',
  ['eq(Solution.divide("17", "5"), "3")', 'eq(Solution.divide("17", "five"), "not a number")', 'eq(Solution.divide("17", "0"), "division by zero")',
   'eq(Solution.divide("-7", "2"), "-3")', 'eq(Solution.divide("", "2"), "not a number")', 'eq(Solution.divide("x", "0"), "not a number")',
   'eq(Solution.divide("0", "9"), "0")', 'eq(Solution.divide("3.5", "1"), "not a number")', 'eq(Solution.divide("0", "0"), "division by zero")',
   'eq(Solution.divide(" 4", "2"), "not a number")', 'eq(Solution.divide("2147483647", "1"), "2147483647")'],
  ['''class Solution {
    static String divide(String a, String b) {
        try {
            int x = Integer.parseInt(a);
            int y = Integer.parseInt(b);
            return String.valueOf(x / y);
        } catch (Exception e) {
            return "not a number";
        }
    }
}
''', '''class Solution {
    static String divide(String a, String b) {
        try {
            int x = Integer.parseInt(a.trim());
            int y = Integer.parseInt(b.trim());
            return String.valueOf((double) x / y);
        } catch (NumberFormatException e) {
            return "not a number";
        } catch (ArithmeticException e) {
            return "division by zero";
        }
    }
}
'''],
  G("Lesson *Exceptions: try, catch, finally, checked and unchecked*.",
    "Write the happy path as if nothing could go wrong, inside `try`. Then add one `catch` for each kind of failure, each returning its own message.",
    ["`Integer.parseInt` throws `NumberFormatException` for bad text.", "Integer division by zero throws `ArithmeticException`.", "Two separate catch blocks; each exception type selects its block."],
    "Checking the text with a regular expression and testing `b == 0` by hand also works. Here the aim is to practise the mechanism the library already gives you.",
    r"""**Dry run** `divide("17", "0")`: both parse. `17 / 0` throws `ArithmeticException`. The first catch (`NumberFormatException`) does not match; the second does → `"division by zero"`.

**Dry run** `divide("x", "0")`: parsing `"x"` throws first, so the answer is `"not a number"`; the division is never attempted.

```java
class Solution {
    static String divide(String a, String b) {
        try {
            int x = Integer.parseInt(a);
            int y = Integer.parseInt(b);
            return String.valueOf(x / y);
        } catch (NumberFormatException e) {
            return "not a number";
        } catch (ArithmeticException e) {
            return "division by zero";
        }
    }
}
```""",
    "Time O(length of the inputs), space O(1).",
    "- One broad `catch (Exception e)`, which cannot tell the two failures apart.\n- Casting to `double`: floating-point division by zero does not throw, it gives `Infinity`.\n- Trimming the input changes which texts are accepted."),
  ),
# ------------------------------------------------------------------ java-code-wallet-exception
J("java-code-wallet-exception", "A custom checked exception", "Medium", "Java exceptions",
  r"""
Inside `Solution`, write a custom **checked** exception and a class that throws it.

```java
static class InsufficientFundsException extends Exception {
    InsufficientFundsException(long shortfall)       // message: "short by <shortfall>"
    long shortfall()
}

static class Wallet {
    Wallet(long pence)                               // starting balance; IllegalArgumentException if negative
    long balance()
    void pay(long price) throws InsufficientFundsException
        // price < 0  -> IllegalArgumentException, balance unchanged
        // price > balance -> throw new InsufficientFundsException(price - balance), balance unchanged
        // otherwise subtract
}

static String tryToPay(Wallet w, long price)
    // returns "paid" on success, or "short by <n>" when InsufficientFundsException is thrown
    // (use the exception's shortfall() or getMessage())
```

**Example** `Wallet w = new Wallet(500); tryToPay(w, 200)` → `"paid"`; then `tryToPay(w, 450)` → `"short by 150"`
and the balance is still 300.
""",
  '''class Solution {
    // write InsufficientFundsException here

    static class Wallet {
        Wallet(long pence) {
        }

        long balance() { return 0; }

        void pay(long price) {
        }
    }

    static String tryToPay(Wallet w, long price) {
        return "";
    }
}
''',
  '''class Solution {
    static class InsufficientFundsException extends Exception {
        private final long shortfall;

        InsufficientFundsException(long shortfall) {
            super("short by " + shortfall);
            this.shortfall = shortfall;
        }

        long shortfall() { return shortfall; }
    }

    static class Wallet {
        private long balance;

        Wallet(long pence) {
            if (pence < 0) {
                throw new IllegalArgumentException("negative balance: " + pence);
            }
            balance = pence;
        }

        long balance() { return balance; }

        void pay(long price) throws InsufficientFundsException {
            if (price < 0) {
                throw new IllegalArgumentException("negative price: " + price);
            }
            if (price > balance) {
                throw new InsufficientFundsException(price - balance);
            }
            balance -= price;
        }
    }

    static String tryToPay(Wallet w, long price) {
        try {
            w.pay(price);
            return "paid";
        } catch (InsufficientFundsException e) {
            return "short by " + e.shortfall();
        }
    }
}
''',
  ['{ Solution.Wallet w = new Solution.Wallet(500); w.pay(200); return eq(w.balance(), 300L); }',
   '{ Solution.Wallet w = new Solution.Wallet(500); return thrown(Solution.InsufficientFundsException.class, () -> { w.pay(501); return null; }); }',
   '{ Solution.Wallet w = new Solution.Wallet(500); try { w.pay(650); return "no exception"; } catch (Solution.InsufficientFundsException e) { return eq(e.shortfall(), 150L); } }',
   '{ Solution.Wallet w = new Solution.Wallet(500); try { w.pay(650); return "no exception"; } catch (Solution.InsufficientFundsException e) { return eq(e.getMessage(), "short by 150"); } }',
   '{ Solution.Wallet w = new Solution.Wallet(500); try { w.pay(650); } catch (Solution.InsufficientFundsException e) { } return eq(w.balance(), 500L); }',
   '{ Solution.Wallet w = new Solution.Wallet(500); w.pay(500); return eq(w.balance(), 0L); }',
   '{ Solution.Wallet w = new Solution.Wallet(500); return thrown(IllegalArgumentException.class, () -> { w.pay(-1); return null; }); }',
   'thrown(IllegalArgumentException.class, () -> { new Solution.Wallet(-1); return null; })',
   '{ Solution.Wallet w = new Solution.Wallet(500); return eq(Solution.tryToPay(w, 200), "paid"); }',
   '{ Solution.Wallet w = new Solution.Wallet(500); Solution.tryToPay(w, 200); return eq(Solution.tryToPay(w, 450), "short by 150"); }',
   '{ Object e = new Solution.InsufficientFundsException(1); return yes(e instanceof Exception && !(e instanceof RuntimeException), "must be a CHECKED exception: extend Exception, not RuntimeException"); }',
   '{ Solution.Wallet w = new Solution.Wallet(0); Solution.tryToPay(w, 0); return eq(Solution.tryToPay(w, 1), "short by 1"); }'],
  ['''class Solution {
    static class InsufficientFundsException extends RuntimeException {
        private final long shortfall;
        InsufficientFundsException(long shortfall) { super("short by " + shortfall); this.shortfall = shortfall; }
        long shortfall() { return shortfall; }
    }
    static class Wallet {
        private long balance;
        Wallet(long pence) { if (pence < 0) throw new IllegalArgumentException(); balance = pence; }
        long balance() { return balance; }
        void pay(long price) {
            if (price < 0) throw new IllegalArgumentException();
            if (price > balance) throw new InsufficientFundsException(price - balance);
            balance -= price;
        }
    }
    static String tryToPay(Wallet w, long price) {
        try { w.pay(price); return "paid"; } catch (InsufficientFundsException e) { return "short by " + e.shortfall(); }
    }
}
''', '''class Solution {
    static class InsufficientFundsException extends Exception {
        private final long shortfall;
        InsufficientFundsException(long shortfall) { super("short by " + shortfall); this.shortfall = shortfall; }
        long shortfall() { return shortfall; }
    }
    static class Wallet {
        private long balance;
        Wallet(long pence) { if (pence < 0) throw new IllegalArgumentException(); balance = pence; }
        long balance() { return balance; }
        void pay(long price) throws InsufficientFundsException {
            if (price < 0) throw new IllegalArgumentException();
            balance -= price;
            if (balance < 0) throw new InsufficientFundsException(-balance);
        }
    }
    static String tryToPay(Wallet w, long price) {
        try { w.pay(price); return "paid"; } catch (InsufficientFundsException e) { return "short by " + e.shortfall(); }
    }
}
'''],
  G("Lessons *try-with-resources, multi-catch and custom exceptions*, *Choosing exceptions* and *Documenting, detailing and recovering from failures*.",
    "A declined payment is something a caller can recover from, so it is a checked exception carrying the data needed for recovery (the shortfall). A negative price is a bug in the caller, so it is an unchecked `IllegalArgumentException`. Check everything before changing the balance, so a failed call changes nothing.",
    ["`extends Exception` makes it checked; pass the message to `super(...)`.", "`pay` must declare `throws InsufficientFundsException`.", "Validate first, mutate last: that gives failure atomicity."],
    "Returning `false` or `-1` from `pay` avoids exceptions but loses the shortfall and lets callers ignore the failure. The exception carries the detail and cannot be skipped by accident.",
    r"""**Dry run** wallet 300, `pay(450)`: not negative; `450 > 300` → throw `InsufficientFundsException(150)` before touching the balance. `tryToPay` catches it and returns `"short by 150"`; the balance is still 300.

```java
static class InsufficientFundsException extends Exception {          // checked
    private final long shortfall;

    InsufficientFundsException(long shortfall) {
        super("short by " + shortfall);                              // detail message with the value
        this.shortfall = shortfall;
    }

    long shortfall() { return shortfall; }                           // accessor: no need to parse the message
}

void pay(long price) throws InsufficientFundsException {
    if (price < 0) throw new IllegalArgumentException("negative price: " + price);
    if (price > balance) throw new InsufficientFundsException(price - balance);
    balance -= price;                                                // only after every check has passed
}
```""",
    "All operations O(1).",
    "- Extending `RuntimeException`: the exception becomes unchecked and callers are no longer forced to handle it.\n- Subtracting before checking, leaving a negative balance after a failed payment.\n- No `throws` clause on `pay`: the compiler rejects throwing a checked exception without it."),
  ),
]
