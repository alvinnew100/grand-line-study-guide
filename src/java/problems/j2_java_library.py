"""Java track, REAL Java problems part 2 (judged on the server): collections, generics, streams, records,
equals/hashCode, immutability, builders, and classic interview problems.
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

    static String arr(int[] got, int[] want) {
        return Arrays.equals(got, want) ? null : "got " + Arrays.toString(got) + " want " + Arrays.toString(want);
    }

    static String deep(int[][] got, int[][] want) {
        return Arrays.deepEquals(got, want) ? null : "got " + Arrays.deepToString(got) + " want " + Arrays.deepToString(want);
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
    return PRE + "".join("        t(() -> %s);\n" % c for c in checks) + "    }\n}\n"


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls, follow_up=None, leetcode=None):
    d = dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute, approach=approach,
             complexity=complexity, pitfalls=pitfalls)
    if follow_up:
        d["follow_up"] = follow_up
    if leetcode:
        d["_leetcode"] = leetcode
    return d


def J(id, title, difficulty, pattern, description, starter, solution, checks, wrong, guide, **extra):
    d = dict(id=id, title=title, difficulty=difficulty, pattern=pattern, kind="java", cases=len(checks),
             description=description, starter=starter, solution=solution, harness=H(*checks),
             wrong_solutions=wrong, guide=guide)
    link = guide.pop("_leetcode", None)
    if link:
        d["leetcode"] = link
    d.update(extra)
    return d


PROBLEMS = [
# ------------------------------------------------------------------ java-code-dedupe-list
J("java-code-dedupe-list", "Remove duplicates, keep the order", "Easy", "Java collections",
  r"""
In class `Solution`, write

```java
static List<Integer> dedupe(List<Integer> values)
```

Return a **new** list containing each distinct value once, in the order of its **first** appearance. Do not
modify the list you were given (it may be unmodifiable).

**Examples** `dedupe(List.of(3, 1, 3, 2, 1))` → `[3, 1, 2]`; `dedupe(List.of())` → `[]`.

The values may be large (such as 1000), so compare them by value, never with `==` on `Integer` objects.
""",
  '''import java.util.*;

class Solution {
    static List<Integer> dedupe(List<Integer> values) {
        // your code
        return values;
    }
}
''',
  '''import java.util.*;

class Solution {
    static List<Integer> dedupe(List<Integer> values) {
        return new ArrayList<>(new LinkedHashSet<>(values));
    }
}
''',
  ["eq(Solution.dedupe(List.of(3, 1, 3, 2, 1)), List.of(3, 1, 2))", "eq(Solution.dedupe(List.of()), List.of())", "eq(Solution.dedupe(List.of(7)), List.of(7))",
   "eq(Solution.dedupe(List.of(5, 5, 5, 5)), List.of(5))", "eq(Solution.dedupe(List.of(1, 2, 3)), List.of(1, 2, 3))",
   "eq(Solution.dedupe(List.of(1000, 2000, 1000, 3000, 2000)), List.of(1000, 2000, 3000))", "eq(Solution.dedupe(List.of(-1, 0, -1, 0, 1)), List.of(-1, 0, 1))",
   "{ List<Integer> in = new ArrayList<>(List.of(2, 2, 1)); Solution.dedupe(in); return eq(in, List.of(2, 2, 1)); }",
   "{ List<Integer> in = new ArrayList<>(List.of(2, 1)); return yes(Solution.dedupe(in) != in, \"must return a new list\"); }",
   "eq(Solution.dedupe(List.of(9, 8, 9, 7, 8, 6)), List.of(9, 8, 7, 6))"],
  ['''import java.util.*;

class Solution {
    static List<Integer> dedupe(List<Integer> values) {
        return new ArrayList<>(new TreeSet<>(values));
    }
}
''', '''import java.util.*;

class Solution {
    static List<Integer> dedupe(List<Integer> values) {
        List<Integer> out = new ArrayList<>();
        for (Integer v : values) {
            boolean seen = false;
            for (Integer o : out) if (o == v) seen = true;
            if (!seen) out.add(v);
        }
        return out;
    }
}
'''],
  G("Lessons *ArrayList and reading the API documentation* and *Collections: List, Set, Map and Queue*.",
    "A set rejects duplicates; a `LinkedHashSet` also remembers insertion order. Pour the list into one and pour it back out.",
    ["Which `Set` implementation keeps insertion order?", "`new LinkedHashSet<>(values)` copies and removes duplicates in one step.", "Wrap the set in `new ArrayList<>(...)` to return a list."],
    "For each value, scan the output list built so far and add the value only if it is absent: O(n²), and correct if you compare with `equals`.",
    r"""**Dry run** `[3, 1, 3, 2, 1]`: the set receives 3, 1, (3 ignored), 2, (1 ignored) → `[3, 1, 2]`.

```java
import java.util.*;

class Solution {
    static List<Integer> dedupe(List<Integer> values) {
        return new ArrayList<>(new LinkedHashSet<>(values));
    }
}
// with streams: values.stream().distinct().toList()
```""",
    "Time O(n) on average, space O(n).",
    "- `HashSet` loses the order; `TreeSet` sorts.\n- `o == v` on `Integer` objects compares references and fails above 127.\n- Removing from the input list, which may be unmodifiable."),
  ),
# ------------------------------------------------------------------ java-code-word-count
J("java-code-word-count", "Word frequencies with a HashMap", "Easy", "Java collections",
  r"""
In class `Solution`, write

```java
static Map<String, Integer> wordCount(String text)
```

Split `text` into words at runs of spaces, convert each word to lower case, and return a map from each word
to the number of times it occurs. Leading and trailing spaces are ignored. An empty or all-space text gives
an empty map.

**Example** `wordCount("To be or not to be")` → `{to=2, be=2, or=1, not=1}` (the order of a map's entries
does not matter).
""",
  '''import java.util.*;

class Solution {
    static Map<String, Integer> wordCount(String text) {
        // your code
        return new HashMap<>();
    }
}
''',
  '''import java.util.*;

class Solution {
    static Map<String, Integer> wordCount(String text) {
        Map<String, Integer> counts = new HashMap<>();
        for (String word : text.trim().split(" +")) {
            if (!word.isEmpty()) {
                counts.merge(word.toLowerCase(), 1, Integer::sum);
            }
        }
        return counts;
    }
}
''',
  ['eq(Solution.wordCount("To be or not to be"), Map.of("to", 2, "be", 2, "or", 1, "not", 1))', 'eq(Solution.wordCount(""), Map.of())', 'eq(Solution.wordCount("    "), Map.of())',
   'eq(Solution.wordCount("tea"), Map.of("tea", 1))', 'eq(Solution.wordCount("Tea TEA tea"), Map.of("tea", 3))', 'eq(Solution.wordCount("  a   b  a "), Map.of("a", 2, "b", 1))',
   'eq(Solution.wordCount("x y z"), Map.of("x", 1, "y", 1, "z", 1))', 'eq(Solution.wordCount("one, one one"), Map.of("one,", 1, "one", 2))',
   'eq(Solution.wordCount("a a a a a a a a a a").get("a"), 10)', 'eq(Solution.wordCount("b a").size(), 2)'],
  ['''import java.util.*;

class Solution {
    static Map<String, Integer> wordCount(String text) {
        Map<String, Integer> counts = new HashMap<>();
        for (String word : text.split(" ")) {
            counts.put(word.toLowerCase(), 1);
        }
        return counts;
    }
}
''', '''import java.util.*;

class Solution {
    static Map<String, Integer> wordCount(String text) {
        Map<String, Integer> counts = new HashMap<>();
        for (String word : text.trim().split(" +")) {
            if (!word.isEmpty()) counts.merge(word, 1, Integer::sum);
        }
        return counts;
    }
}
'''],
  G("Lesson *Collections: List, Set, Map and Queue*: the counting idiom with `merge`.",
    "A map from word to count. For each word: if it is new, store 1; otherwise add 1 to what is there. `merge` does both in one call.",
    ["`text.trim().split(\" +\")` gives the words; skip an empty string.", "`counts.merge(word, 1, Integer::sum)` inserts 1 or adds 1.", "Lower-case the word before using it as the key."],
    "`if (counts.containsKey(w)) counts.put(w, counts.get(w) + 1); else counts.put(w, 1);` is the long form of the same thing, with two lookups.",
    r"""**Dry run** `"To be or not to be"` → words `to, be, or, not, to, be` → `{to=1}`, `{to=1, be=1}`, …, the second `to` merges to 2, the second `be` to 2.

```java
import java.util.*;

class Solution {
    static Map<String, Integer> wordCount(String text) {
        Map<String, Integer> counts = new HashMap<>();
        for (String word : text.trim().split(" +")) {
            if (!word.isEmpty()) {
                counts.merge(word.toLowerCase(), 1, Integer::sum);
            }
        }
        return counts;
    }
}
// streams: Arrays.stream(words).collect(Collectors.groupingBy(String::toLowerCase, Collectors.counting()))  (values are Long)
```""",
    "Time O(n) in the length of the text, space O(distinct words).",
    "- `put(word, 1)` overwrites instead of counting.\n- Forgetting to lower-case.\n- `split(\" \")` produces empty words for double spaces, and `\"\".split(...)` yields one empty string."),
  ),
# ------------------------------------------------------------------ java-code-common-elements
J("java-code-common-elements", "Common elements with a HashSet", "Easy", "Java collections",
  r"""
In class `Solution`, write

```java
static List<Integer> common(int[] a, int[] b)
```

Return the values that occur in **both** arrays, each once, in **ascending** order.

**Examples** `common({4, 9, 5, 4}, {9, 4, 9, 8})` → `[4, 9]`; `common({1, 2}, {3})` → `[]`.

Aim for time proportional to the total length (plus sorting the answer), not `a.length × b.length`.
""",
  '''import java.util.*;

class Solution {
    static List<Integer> common(int[] a, int[] b) {
        // your code
        return new ArrayList<>();
    }
}
''',
  '''import java.util.*;

class Solution {
    static List<Integer> common(int[] a, int[] b) {
        Set<Integer> inA = new HashSet<>();
        for (int x : a) {
            inA.add(x);
        }
        Set<Integer> both = new TreeSet<>();
        for (int x : b) {
            if (inA.contains(x)) {
                both.add(x);
            }
        }
        return new ArrayList<>(both);
    }
}
''',
  ["eq(Solution.common(new int[] {4, 9, 5, 4}, new int[] {9, 4, 9, 8}), List.of(4, 9))", "eq(Solution.common(new int[] {1, 2}, new int[] {3}), List.of())",
   "eq(Solution.common(new int[] {}, new int[] {1}), List.of())", "eq(Solution.common(new int[] {}, new int[] {}), List.of())",
   "eq(Solution.common(new int[] {7, 7, 7}, new int[] {7}), List.of(7))", "eq(Solution.common(new int[] {3, 2, 1}, new int[] {1, 2, 3}), List.of(1, 2, 3))",
   "eq(Solution.common(new int[] {-5, 1000, 0}, new int[] {1000, -5}), List.of(-5, 1000))", "eq(Solution.common(new int[] {1, 3, 5}, new int[] {2, 4, 6}), List.of())",
   "{ int[] a = new int[20000], b = new int[20000]; for (int i = 0; i < 20000; i++) { a[i] = i; b[i] = i + 19990; } return eq(Solution.common(a, b).size(), 10); }",
   "eq(Solution.common(new int[] {2, 2}, new int[] {2, 2}), List.of(2))"],
  ['''import java.util.*;

class Solution {
    static List<Integer> common(int[] a, int[] b) {
        List<Integer> out = new ArrayList<>();
        for (int x : a) for (int y : b) if (x == y) out.add(x);
        return out;
    }
}
''', '''import java.util.*;

class Solution {
    static List<Integer> common(int[] a, int[] b) {
        Set<Integer> inA = new HashSet<>();
        for (int x : a) inA.add(x);
        List<Integer> out = new ArrayList<>();
        for (int x : b) if (inA.contains(x) && !out.contains(x)) out.add(x);
        return out;
    }
}
'''],
  G("Lesson *Collections: List, Set, Map and Queue*: `HashSet` for fast membership tests, `TreeSet` for sorted results.",
    "Put one array into a hash set so that 'is this value in it?' takes constant time. Walk the other array and keep the hits in a set that sorts.",
    ["Fill a `HashSet<Integer>` from `a`.", "For each element of `b` that the set contains, add it to a `TreeSet`.", "Return `new ArrayList<>(treeSet)`."],
    "Compare every element of `a` with every element of `b`: O(a × b), and you must still remove duplicates and sort.",
    r"""**Dry run** `a = {4, 9, 5, 4}` → set `{4, 5, 9}`. `b = {9, 4, 9, 8}`: 9 yes, 4 yes, 9 already there, 8 no → `TreeSet {4, 9}` → `[4, 9]`.

```java
import java.util.*;

class Solution {
    static List<Integer> common(int[] a, int[] b) {
        Set<Integer> inA = new HashSet<>();
        for (int x : a) inA.add(x);
        Set<Integer> both = new TreeSet<>();
        for (int x : b) if (inA.contains(x)) both.add(x);
        return new ArrayList<>(both);
    }
}
// with set algebra: Set<Integer> s = new TreeSet<>(listA); s.retainAll(new HashSet<>(listB));
```""",
    "Time O(a + b + k log k) for k common values, space O(a + k).",
    "- Nested loops produce duplicates and quadratic time.\n- Forgetting to sort the result.\n- `list.contains` inside the loop makes it quadratic again."),
  ),
# ------------------------------------------------------------------ java-code-valid-parentheses
J("java-code-valid-parentheses", "Valid parentheses", "Easy", "Stack",
  r"""
In class `Solution`, write

```java
static boolean isValid(String s)
```

`s` contains only the characters `( ) [ ] { }`. It is valid when every opening bracket is closed by the same
kind of bracket, and brackets close in the correct order. The empty string is valid.

**Examples** `isValid("()[]{}")` → `true`; `isValid("([)]")` → `false`; `isValid("{[]}")` → `true`;
`isValid("(")` → `false`.

Use a `Deque` as a stack (`ArrayDeque`), not the legacy `Stack` class.
""",
  '''import java.util.*;

class Solution {
    static boolean isValid(String s) {
        // your code
        return false;
    }
}
''',
  '''import java.util.*;

class Solution {
    static boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') {
                stack.push(c);
            } else {
                if (stack.isEmpty()) {
                    return false;
                }
                char open = stack.pop();
                if ((c == ')' && open != '(') || (c == ']' && open != '[') || (c == '}' && open != '{')) {
                    return false;
                }
            }
        }
        return stack.isEmpty();
    }
}
''',
  ['eq(Solution.isValid("()[]{}"), true)', 'eq(Solution.isValid("([)]"), false)', 'eq(Solution.isValid("{[]}"), true)', 'eq(Solution.isValid("("), false)',
   'eq(Solution.isValid(""), true)', 'eq(Solution.isValid(")"), false)', 'eq(Solution.isValid("(("), false)', 'eq(Solution.isValid("())"), false)',
   'eq(Solution.isValid("(]"), false)', 'eq(Solution.isValid("{[()()]}[]"), true)', 'eq(Solution.isValid("(".repeat(5000) + ")".repeat(5000)), true)',
   'eq(Solution.isValid("][" ), false)'],
  ['''class Solution {
    static boolean isValid(String s) {
        int round = 0, square = 0, curly = 0;
        for (char c : s.toCharArray()) {
            if (c == '(') round++; else if (c == ')') round--;
            else if (c == '[') square++; else if (c == ']') square--;
            else if (c == '{') curly++; else curly--;
            if (round < 0 || square < 0 || curly < 0) return false;
        }
        return round == 0 && square == 0 && curly == 0;
    }
}
''', '''import java.util.*;

class Solution {
    static boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') stack.push(c);
            else {
                if (stack.isEmpty()) return false;
                char open = stack.pop();
                if ((c == ')' && open != '(') || (c == ']' && open != '[') || (c == '}' && open != '{')) return false;
            }
        }
        return true;
    }
}
'''],
  G("Lesson *Collections: List, Set, Map and Queue*: `Deque` used as a stack (`push`, `pop`, `isEmpty`).",
    "The most recently opened bracket must be the first one closed. 'Last in, first out' is a stack.",
    ["Push every opening bracket.", "On a closing bracket: an empty stack means there is nothing to close; otherwise pop and check that the kinds match.", "At the end the stack must be empty."],
    "Repeatedly delete the substrings `()`, `[]` and `{}` until nothing changes; the string is valid if it becomes empty. Correct, and O(n²).",
    r"""**Dry run** `"([)]"`: push `(`, push `[`; `)` arrives, pop gives `[`, which does not match → `false`.
Counting brackets of each kind would wrongly accept this string; only a stack sees the order.

```java
import java.util.*;

class Solution {
    static boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            switch (c) {
                case '(' -> stack.push(')');           // push the closer we expect
                case '[' -> stack.push(']');
                case '{' -> stack.push('}');
                default -> {
                    if (stack.isEmpty() || stack.pop() != c) return false;
                }
            }
        }
        return stack.isEmpty();
    }
}
```""",
    "Time O(n), space O(n).",
    "- Counting instead of stacking.\n- Popping an empty stack (`NoSuchElementException`).\n- Returning `true` without checking that the stack is empty.",
    leetcode="https://leetcode.com/problems/valid-parentheses/"),
  ),
# ------------------------------------------------------------------ java-code-top-k
J("java-code-top-k", "K largest with a PriorityQueue", "Medium", "Heap",
  r"""
In class `Solution`, write

```java
static List<Integer> topK(int[] values, int k)
```

Return the `k` largest elements in **descending** order. Duplicates count separately. If `k` is larger than
the array, return all elements (still descending). `k >= 0`.

**Examples** `topK({5, 1, 9, 3, 9}, 3)` → `[9, 9, 5]`; `topK({4, 2}, 5)` → `[4, 2]`; `topK({1}, 0)` → `[]`.

Solve it with a `PriorityQueue` that never holds more than `k` elements, so the work is proportional to
n log k and not n log n.
""",
  '''import java.util.*;

class Solution {
    static List<Integer> topK(int[] values, int k) {
        // your code
        return new ArrayList<>();
    }
}
''',
  '''import java.util.*;

class Solution {
    static List<Integer> topK(int[] values, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();        // smallest on top
        for (int v : values) {
            heap.offer(v);
            if (heap.size() > k) {
                heap.poll();                                        // drop the smallest
            }
        }
        List<Integer> out = new ArrayList<>(heap);
        out.sort(Comparator.reverseOrder());
        return out;
    }
}
''',
  ["eq(Solution.topK(new int[] {5, 1, 9, 3, 9}, 3), List.of(9, 9, 5))", "eq(Solution.topK(new int[] {4, 2}, 5), List.of(4, 2))", "eq(Solution.topK(new int[] {1}, 0), List.of())",
   "eq(Solution.topK(new int[] {}, 3), List.of())", "eq(Solution.topK(new int[] {7}, 1), List.of(7))", "eq(Solution.topK(new int[] {1, 2, 3, 4, 5}, 2), List.of(5, 4))",
   "eq(Solution.topK(new int[] {-1, -5, -3}, 2), List.of(-1, -3))", "eq(Solution.topK(new int[] {2, 2, 2}, 2), List.of(2, 2))",
   "eq(Solution.topK(new int[] {3, 1, 2}, 3), List.of(3, 2, 1))",
   "{ int[] a = new int[50000]; for (int i = 0; i < a.length; i++) a[i] = (i * 7919) % 50021; return eq(Solution.topK(a, 3), List.of(50020, 50019, 50018)); }"],
  ['''import java.util.*;

class Solution {
    static List<Integer> topK(int[] values, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int v : values) {
            heap.offer(v);
            if (heap.size() > k) heap.poll();
        }
        return new ArrayList<>(heap);
    }
}
''', '''import java.util.*;

class Solution {
    static List<Integer> topK(int[] values, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>(Comparator.reverseOrder());
        for (int v : values) {
            heap.offer(v);
            if (heap.size() > k) heap.poll();
        }
        List<Integer> out = new ArrayList<>(heap);
        out.sort(Comparator.reverseOrder());
        return out;
    }
}
'''],
  G("Lessons *Collections: List, Set, Map and Queue* (`PriorityQueue`) and *Sorting with Comparable and Comparator*.",
    "Keep a small 'leader board' of the k best values seen so far. The value you most often need from it is the **weakest** leader, to compare with a newcomer, so the board is a **min**-heap.",
    ["A default `PriorityQueue<Integer>` hands out the smallest element first.", "After each insertion, if the heap holds more than `k` elements, remove the smallest.", "Iterating over a heap is not sorted: sort the survivors in reverse order at the end."],
    "Sort the whole array in descending order and take the first k: O(n log n). Fine for small inputs; the heap wins when k is much smaller than n.",
    r"""**Dry run** `{5, 1, 9, 3, 9}`, k = 3. Heap after each step (smallest first): `[5]`, `[1, 5]`, `[1, 5, 9]`, add 3 → four elements, drop 1 → `[3, 5, 9]`, add 9 → drop 3 → `[5, 9, 9]`. Sorted descending: `[9, 9, 5]`.

```java
import java.util.*;

class Solution {
    static List<Integer> topK(int[] values, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();     // min-heap of the k largest so far
        for (int v : values) {
            heap.offer(v);
            if (heap.size() > k) heap.poll();
        }
        List<Integer> out = new ArrayList<>(heap);
        out.sort(Comparator.reverseOrder());
        return out;
    }
}
```""",
    "Time O(n log k + k log k), space O(k).",
    "- A max-heap capped at k keeps the k **smallest**.\n- Returning the heap's iteration order, which is not sorted.\n- Forgetting `k = 0`."),
  ),
# ------------------------------------------------------------------ java-code-generic-largest
J("java-code-generic-largest", "A generic method with a bound", "Medium", "Java generics",
  r"""
In class `Solution`, write a **generic** method that works for any type with a natural ordering:

```java
static <T extends Comparable<? super T>> T largest(List<? extends T> items)
```

Return the largest element according to `compareTo`. If several elements are equally large, return the
first of them. For an empty list throw `java.util.NoSuchElementException`.

It must work for `List<Integer>`, `List<String>`, `List<java.time.LocalDate>` and so on, with no casts in
the calling code.

**Examples** `largest(List.of(4, 19, 7))` → `19`; `largest(List.of("pear", "fig", "plum"))` → `"plum"`.
""",
  '''import java.util.*;

class Solution {
    static <T extends Comparable<? super T>> T largest(List<? extends T> items) {
        // your code
        return null;
    }
}
''',
  '''import java.util.*;

class Solution {
    static <T extends Comparable<? super T>> T largest(List<? extends T> items) {
        if (items.isEmpty()) {
            throw new NoSuchElementException("empty list");
        }
        T best = items.get(0);
        for (T item : items) {
            if (item.compareTo(best) > 0) {
                best = item;
            }
        }
        return best;
    }
}
''',
  ["{ Integer r = Solution.largest(List.of(4, 19, 7)); return eq(r, 19); }", '{ String r = Solution.largest(List.of("pear", "fig", "plum")); return eq(r, "plum"); }',
   "{ Integer r = Solution.largest(List.of(-3)); return eq(r, -3); }", "thrown(NoSuchElementException.class, () -> { Solution.largest(new ArrayList<Integer>()); return null; })",
   '{ java.time.LocalDate r = Solution.largest(List.of(java.time.LocalDate.of(2024, 5, 1), java.time.LocalDate.of(2026, 1, 1), java.time.LocalDate.of(2025, 12, 31))); return eq(r, java.time.LocalDate.of(2026, 1, 1)); }',
   "{ Double r = Solution.largest(List.of(1.5, -2.0, 1.25)); return eq(r, 1.5); }", '{ String r = Solution.largest(List.of("b", "B", "a")); return eq(r, "b"); }',
   '{ String a = new String("zz"), b = new String("zz"); List<String> xs = List.of("a", a, b); return yes(Solution.largest(xs) == a, "on a tie, return the FIRST largest element"); }',
   "{ Integer r = Solution.largest(List.of(1000, 2000, 1500)); return eq(r, 2000); }",
   "{ Long r = Solution.largest(List.of(5L, 9000000000L, 7L)); return eq(r, 9000000000L); }"],
  ['''import java.util.*;

class Solution {
    static <T extends Comparable<? super T>> T largest(List<? extends T> items) {
        T best = null;
        for (T item : items) {
            if (best == null || item.compareTo(best) >= 0) best = item;
        }
        return best;
    }
}
''', '''import java.util.*;

class Solution {
    static <T extends Comparable<? super T>> T largest(List<? extends T> items) {
        if (items.isEmpty()) throw new NoSuchElementException();
        T best = items.get(0);
        for (T item : items) {
            if (item.compareTo(best) < 0) best = item;
        }
        return best;
    }
}
'''],
  G("Lessons *Generics, wildcards and bounds* and *Bounded wildcards, PECS, varargs and heterogeneous containers*.",
    "The type parameter `T` stands for whatever the caller's list holds. The bound `Comparable<? super T>` is what entitles the method body to call `compareTo` on a `T`.",
    ["Read the signature aloud: any `T` that can be compared with `T` or a supertype of `T`.", "The list is a producer of `T`s, hence `List<? extends T>`.", "Keep the first element as `best` and replace it only when `item.compareTo(best) > 0`."],
    "`Collections.max(items)` does exactly this in the library, with the same signature shape. Writing it by hand shows why the bound is needed.",
    r"""**Dry run** `["pear", "fig", "plum"]`: best `pear`; `fig.compareTo(pear)` is negative; `plum.compareTo(pear)` is positive (`l` > `e`) → best `plum`.

```java
import java.util.*;

class Solution {
    static <T extends Comparable<? super T>> T largest(List<? extends T> items) {
        if (items.isEmpty()) throw new NoSuchElementException("empty list");
        T best = items.get(0);
        for (T item : items) {
            if (item.compareTo(best) > 0) best = item;        // strictly greater: ties keep the first
        }
        return best;
    }
}
```

Why `? super T`? A class such as `java.sql.Date` is comparable to its superclass `java.util.Date`, not to itself; the wildcard lets a list of such objects be used.""",
    "Time O(n), space O(1).",
    "- Returning `null` for an empty list instead of throwing.\n- `>=`, which returns the last of several equal elements.\n- Declaring the parameter as `List<Object>` and casting."),
  ),
# ------------------------------------------------------------------ java-code-stream-names
J("java-code-stream-names", "A stream pipeline: filter, map, distinct, sorted", "Easy", "Java streams",
  r"""
In class `Solution`, write

```java
static List<String> longNames(List<String> names, int minLength)
```

Using a **stream pipeline**, return the names whose length (after trimming spaces at both ends) is at least
`minLength`, converted to upper case, without duplicates, sorted alphabetically.

**Example** `longNames(List.of("ada", " Grace ", "bo", "grace", "Linus"), 4)` → `["GRACE", "LINUS"]`.
""",
  '''import java.util.*;
import java.util.stream.*;

class Solution {
    static List<String> longNames(List<String> names, int minLength) {
        // your code
        return List.of();
    }
}
''',
  '''import java.util.*;
import java.util.stream.*;

class Solution {
    static List<String> longNames(List<String> names, int minLength) {
        return names.stream()
                .map(String::trim)
                .filter(n -> n.length() >= minLength)
                .map(String::toUpperCase)
                .distinct()
                .sorted()
                .toList();
    }
}
''',
  ['eq(Solution.longNames(List.of("ada", " Grace ", "bo", "grace", "Linus"), 4), List.of("GRACE", "LINUS"))', 'eq(Solution.longNames(List.of(), 1), List.of())',
   'eq(Solution.longNames(List.of("a", "bb", "ccc"), 2), List.of("BB", "CCC"))', 'eq(Solution.longNames(List.of("a", "bb", "ccc"), 9), List.of())',
   'eq(Solution.longNames(List.of("zed", "amy", "Bob"), 0), List.of("AMY", "BOB", "ZED"))', 'eq(Solution.longNames(List.of("  x  "), 2), List.of())',
   'eq(Solution.longNames(List.of("  xy  "), 2), List.of("XY"))', 'eq(Solution.longNames(List.of("Tea", "tea", "TEA"), 3), List.of("TEA"))',
   'eq(Solution.longNames(List.of("delta", "alpha", "charlie", "bravo"), 5), List.of("ALPHA", "BRAVO", "CHARLIE", "DELTA"))',
   '{ List<String> in = new ArrayList<>(List.of("bb", "a")); Solution.longNames(in, 1); return eq(in, List.of("bb", "a")); }'],
  ['''import java.util.*;
import java.util.stream.*;

class Solution {
    static List<String> longNames(List<String> names, int minLength) {
        return names.stream().filter(n -> n.length() >= minLength).map(String::trim).map(String::toUpperCase).sorted().toList();
    }
}
''', '''import java.util.*;
import java.util.stream.*;

class Solution {
    static List<String> longNames(List<String> names, int minLength) {
        return names.stream().map(String::trim).filter(n -> n.length() > minLength).distinct().map(String::toUpperCase).sorted().toList();
    }
}
'''],
  G("Lessons *Lambdas, functional interfaces and method references* and *The Stream API, collectors and Optional*.",
    "Describe the result as a series of stations: trim, keep the long ones, upper-case, drop duplicates, sort, collect.",
    ["Start with `names.stream()`.", "Order matters: trim before measuring the length, and upper-case before `distinct()` so that `grace` and `Grace` merge.", "Finish with `.toList()`."],
    "A loop with a `TreeSet<String>`: trim, test, upper-case, add; then copy the set to a list. The same result in more lines.",
    r"""**Dry run** `["ada", " Grace ", "bo", "grace", "Linus"]`, min 4: trim → `ada, Grace, bo, grace, Linus`; filter → `Grace, grace, Linus`; upper → `GRACE, GRACE, LINUS`; distinct → `GRACE, LINUS`; sorted → the same.

```java
import java.util.*;

class Solution {
    static List<String> longNames(List<String> names, int minLength) {
        return names.stream()
                .map(String::trim)
                .filter(n -> n.length() >= minLength)
                .map(String::toUpperCase)
                .distinct()
                .sorted()
                .toList();
    }
}
```""",
    "Time O(n log n) because of the sort, space O(n).",
    "- Filtering before trimming.\n- `distinct()` before upper-casing leaves `Tea` and `tea` as two entries.\n- `>` instead of `>=`.\n- Forgetting the terminal operation: nothing runs."),
  ),
# ------------------------------------------------------------------ java-code-count-by-length
J("java-code-count-by-length", "Grouping with collectors", "Medium", "Java streams",
  r"""
In class `Solution`, write

```java
static Map<Integer, Long> countByLength(List<String> words)
static Map<Boolean, List<String>> splitByVowelStart(List<String> words)
```

- `countByLength` returns, for each word length that occurs, how many words have that length.
- `splitByVowelStart` returns a map with exactly the two keys `true` and `false`: `true` → the words that
  start with a vowel (`a e i o u`, either case), `false` → the others; each list keeps the original order.
  Words are never empty.

Use `Collectors.groupingBy` with `Collectors.counting()`, and `Collectors.partitioningBy`.

**Examples** `countByLength(List.of("tea", "jam", "scone"))` → `{3=2, 5=1}`;
`splitByVowelStart(List.of("apple", "tea", "Oat"))` → `{true=[apple, Oat], false=[tea]}`.
""",
  '''import java.util.*;
import java.util.stream.*;

class Solution {
    static Map<Integer, Long> countByLength(List<String> words) {
        return new HashMap<>();
    }

    static Map<Boolean, List<String>> splitByVowelStart(List<String> words) {
        return new HashMap<>();
    }
}
''',
  '''import java.util.*;
import java.util.stream.*;

class Solution {
    static Map<Integer, Long> countByLength(List<String> words) {
        return words.stream().collect(Collectors.groupingBy(String::length, Collectors.counting()));
    }

    static Map<Boolean, List<String>> splitByVowelStart(List<String> words) {
        return words.stream().collect(Collectors.partitioningBy(
                w -> "aeiou".indexOf(Character.toLowerCase(w.charAt(0))) >= 0));
    }
}
''',
  ['eq(Solution.countByLength(List.of("tea", "jam", "scone")), Map.of(3, 2L, 5, 1L))', 'eq(Solution.countByLength(List.of()), Map.of())',
   'eq(Solution.countByLength(List.of("a", "b", "c")), Map.of(1, 3L))', 'eq(Solution.countByLength(List.of("", "x", "")), Map.of(0, 2L, 1, 1L))',
   'eq(Solution.countByLength(List.of("aa", "bbb", "cc", "dddd", "ee")), Map.of(2, 3L, 3, 1L, 4, 1L))',
   'eq(Solution.splitByVowelStart(List.of("apple", "tea", "Oat")), Map.of(true, List.of("apple", "Oat"), false, List.of("tea")))',
   'eq(Solution.splitByVowelStart(List.of()), Map.of(true, List.of(), false, List.of()))',
   'eq(Solution.splitByVowelStart(List.of("x", "y")), Map.of(true, List.of(), false, List.of("x", "y")))',
   'eq(Solution.splitByVowelStart(List.of("Ice", "egg", "Up")).get(true), List.of("Ice", "egg", "Up"))',
   'eq(Solution.splitByVowelStart(List.of("yes", "under", "over", "no")), Map.of(true, List.of("under", "over"), false, List.of("yes", "no")))'],
  ['''import java.util.*;
import java.util.stream.*;

class Solution {
    static Map<Integer, Long> countByLength(List<String> words) {
        return words.stream().collect(Collectors.groupingBy(String::length, Collectors.counting()));
    }
    static Map<Boolean, List<String>> splitByVowelStart(List<String> words) {
        return words.stream().collect(Collectors.groupingBy(w -> "aeiou".indexOf(Character.toLowerCase(w.charAt(0))) >= 0));
    }
}
''', '''import java.util.*;
import java.util.stream.*;

class Solution {
    static Map<Integer, Long> countByLength(List<String> words) {
        return words.stream().distinct().collect(Collectors.groupingBy(String::length, Collectors.counting()));
    }
    static Map<Boolean, List<String>> splitByVowelStart(List<String> words) {
        return words.stream().collect(Collectors.partitioningBy(w -> "aeiou".indexOf(w.charAt(0)) >= 0));
    }
}
'''],
  G("Lesson *The Stream API, collectors and Optional*: `groupingBy`, downstream collectors and `partitioningBy`.",
    "`groupingBy(key, counting())` is the stream form of the counting loop. `partitioningBy(test)` is a grouping with a boolean key that always produces both keys.",
    ["The classifier for the first method is `String::length`.", "`Collectors.counting()` yields `Long` values.", "Use `partitioningBy`, not `groupingBy`, when both `true` and `false` must be present even if one list is empty."],
    "Two ordinary loops with `merge` and `computeIfAbsent` do the same and are perfectly good Java. The collectors say it in one expression.",
    r"""**Dry run** `["tea", "jam", "scone"]`: keys 3, 3, 5 → `{3=2, 5=1}`.

```java
import java.util.*;
import java.util.stream.*;

class Solution {
    static Map<Integer, Long> countByLength(List<String> words) {
        return words.stream().collect(Collectors.groupingBy(String::length, Collectors.counting()));
    }

    static Map<Boolean, List<String>> splitByVowelStart(List<String> words) {
        return words.stream().collect(Collectors.partitioningBy(
                w -> "aeiou".indexOf(Character.toLowerCase(w.charAt(0))) >= 0));
    }
}
```""",
    "Time O(n), space O(n).",
    "- `groupingBy` with a boolean classifier omits a key that has no elements.\n- Forgetting upper-case vowels.\n- Expecting `Integer` counts: `counting()` produces `Long`."),
  ),
# ------------------------------------------------------------------ java-code-compose-functions
J("java-code-compose-functions", "Lambdas: build a pipeline of functions", "Medium", "Java lambdas",
  r"""
Functions are values. In class `Solution`, write

```java
static Function<Integer, Integer> pipeline(List<Function<Integer, Integer>> steps)
static Predicate<Integer> allOf(List<Predicate<Integer>> tests)
```

- `pipeline` returns one function that applies the steps **in list order**: for steps `[f, g, h]` the result
  computes `h(g(f(x)))`. An empty list gives the identity function.
- `allOf` returns a predicate that is true when **every** test in the list is true. An empty list gives a
  predicate that is always true. It should stop at the first failing test.

**Example**

```java
Function<Integer, Integer> p = Solution.pipeline(List.of(x -> x + 1, x -> x * 10));
p.apply(4);     // 50
```
""",
  '''import java.util.*;
import java.util.function.*;

class Solution {
    static Function<Integer, Integer> pipeline(List<Function<Integer, Integer>> steps) {
        return null;
    }

    static Predicate<Integer> allOf(List<Predicate<Integer>> tests) {
        return null;
    }
}
''',
  '''import java.util.*;
import java.util.function.*;

class Solution {
    static Function<Integer, Integer> pipeline(List<Function<Integer, Integer>> steps) {
        Function<Integer, Integer> result = Function.identity();
        for (Function<Integer, Integer> step : steps) {
            result = result.andThen(step);
        }
        return result;
    }

    static Predicate<Integer> allOf(List<Predicate<Integer>> tests) {
        Predicate<Integer> result = x -> true;
        for (Predicate<Integer> test : tests) {
            result = result.and(test);
        }
        return result;
    }
}
''',
  ["{ Function<Integer, Integer> p = Solution.pipeline(List.of(x -> x + 1, x -> x * 10)); return eq(p.apply(4), 50); }",
   "{ Function<Integer, Integer> p = Solution.pipeline(List.of(x -> x * 10, x -> x + 1)); return eq(p.apply(4), 41); }",
   "{ Function<Integer, Integer> p = Solution.pipeline(List.of()); return eq(p.apply(7), 7); }",
   "{ Function<Integer, Integer> p = Solution.pipeline(List.of(x -> x - 3)); return eq(p.apply(3), 0); }",
   "{ Function<Integer, Integer> p = Solution.pipeline(List.of(x -> x + 1, x -> x * 2, x -> x - 5, x -> x * x)); return eq(p.apply(2), 1); }",
   "{ Function<Integer, Integer> p = Solution.pipeline(List.of(x -> x + 1)); return eq(p.apply(1) + p.apply(10), 13); }",
   "{ Predicate<Integer> a = Solution.allOf(List.of(x -> x > 0, x -> x % 2 == 0)); return eq(a.test(4), true); }",
   "{ Predicate<Integer> a = Solution.allOf(List.of(x -> x > 0, x -> x % 2 == 0)); return eq(a.test(3), false); }",
   "{ Predicate<Integer> a = Solution.allOf(List.of(x -> x > 0, x -> x % 2 == 0)); return eq(a.test(-4), false); }",
   "{ Predicate<Integer> a = Solution.allOf(List.of()); return eq(a.test(123), true); }",
   "{ int[] calls = {0}; Predicate<Integer> a = Solution.allOf(List.of(x -> false, x -> { calls[0]++; return true; })); a.test(1); return eq(calls[0], 0); }"],
  ['''import java.util.*;
import java.util.function.*;

class Solution {
    static Function<Integer, Integer> pipeline(List<Function<Integer, Integer>> steps) {
        Function<Integer, Integer> result = Function.identity();
        for (Function<Integer, Integer> step : steps) result = result.compose(step);
        return result;
    }
    static Predicate<Integer> allOf(List<Predicate<Integer>> tests) {
        Predicate<Integer> result = x -> true;
        for (Predicate<Integer> test : tests) result = result.and(test);
        return result;
    }
}
''', '''import java.util.*;
import java.util.function.*;

class Solution {
    static Function<Integer, Integer> pipeline(List<Function<Integer, Integer>> steps) {
        Function<Integer, Integer> result = Function.identity();
        for (Function<Integer, Integer> step : steps) result = result.andThen(step);
        return result;
    }
    static Predicate<Integer> allOf(List<Predicate<Integer>> tests) {
        return x -> {
            boolean ok = false;
            for (Predicate<Integer> test : tests) ok = ok | test.test(x);
            return ok;
        };
    }
}
'''],
  G("Lessons *Lambdas, functional interfaces and method references* and *Choosing between lambdas, method references and classes*.",
    "Start from a function that does nothing and chain each step onto the end with `andThen`. The same folding idea works for predicates with `and`.",
    ["`Function.identity()` returns its argument unchanged.", "`f.andThen(g)` runs `f` first and then `g`; `compose` is the reverse order.", "`Predicate.and` short-circuits: if the left side is false, the right side is not evaluated."],
    "Return a lambda that loops over the list each time it is called: `x -> { for (var s : steps) x = s.apply(x); return x; }`. Just as valid, and arguably clearer; note that it captures the list, so later changes to the list would show through.",
    r"""**Dry run** steps `[x + 1, x * 10]`, input 4. `identity.andThen(+1).andThen(*10)`: 4 → 4 → 5 → 50.

```java
import java.util.*;
import java.util.function.*;

class Solution {
    static Function<Integer, Integer> pipeline(List<Function<Integer, Integer>> steps) {
        Function<Integer, Integer> result = Function.identity();
        for (Function<Integer, Integer> step : steps) {
            result = result.andThen(step);
        }
        return result;
    }

    static Predicate<Integer> allOf(List<Predicate<Integer>> tests) {
        return x -> tests.stream().allMatch(t -> t.test(x));      // allMatch short-circuits
    }
}
// with streams: steps.stream().reduce(Function.identity(), Function::andThen)
```""",
    "Building is O(k) for k steps; each call of the result is O(k).",
    "- `compose` applies the steps in reverse.\n- `allOf` of an empty list must be true, not false.\n- Using `|` or evaluating every test defeats short-circuiting."),
  ),
# ------------------------------------------------------------------ java-code-record-range
J("java-code-record-range", "A record with validation", "Easy", "Java records",
  r"""
Inside `Solution`, write a **record** for a closed range of whole numbers.

```java
record Range(int lo, int hi) {
    // compact constructor: throw IllegalArgumentException if lo > hi
    int length()                     // number of integers in the range: hi - lo + 1
    boolean contains(int value)      // lo <= value <= hi
    boolean overlaps(Range other)    // do the two ranges share at least one integer?
    static Range of(int a, int b)    // factory that accepts the bounds in either order
}
```

A record gives you the accessors `lo()` and `hi()`, `equals`, `hashCode` and `toString` automatically:
`new Range(1, 5).toString()` is `"Range[lo=1, hi=5]"`.

**Examples** `new Range(3, 7).length()` → `5`; `Range.of(9, 2)` equals `new Range(2, 9)`;
`new Range(5, 1)` throws `IllegalArgumentException`.
""",
  '''class Solution {
    record Range(int lo, int hi) {
        // your code
    }
}
''',
  '''class Solution {
    record Range(int lo, int hi) {
        Range {
            if (lo > hi) {
                throw new IllegalArgumentException("lo " + lo + " is greater than hi " + hi);
            }
        }

        int length() {
            return hi - lo + 1;
        }

        boolean contains(int value) {
            return lo <= value && value <= hi;
        }

        boolean overlaps(Range other) {
            return lo <= other.hi && other.lo <= hi;
        }

        static Range of(int a, int b) {
            return new Range(Math.min(a, b), Math.max(a, b));
        }
    }
}
''',
  ["eq(new Solution.Range(3, 7).length(), 5)", "eq(new Solution.Range(4, 4).length(), 1)", "thrown(IllegalArgumentException.class, () -> { new Solution.Range(5, 1); return null; })",
   "eq(new Solution.Range(1, 5), new Solution.Range(1, 5))", "eq(new Solution.Range(1, 5).hashCode(), new Solution.Range(1, 5).hashCode())",
   'eq(new Solution.Range(1, 5).toString(), "Range[lo=1, hi=5]")', "eq(Solution.Range.of(9, 2), new Solution.Range(2, 9))",
   "{ Solution.Range r = new Solution.Range(-2, 2); return yes(r.contains(-2) && r.contains(0) && r.contains(2) && !r.contains(3) && !r.contains(-3), \"contains is wrong at a boundary\"); }",
   "eq(new Solution.Range(1, 5).overlaps(new Solution.Range(5, 9)), true)", "eq(new Solution.Range(1, 4).overlaps(new Solution.Range(5, 9)), false)",
   "eq(new Solution.Range(1, 10).overlaps(new Solution.Range(3, 4)), true)", "eq(new Solution.Range(6, 8).overlaps(new Solution.Range(1, 5)), false)",
   "{ Object r = new Solution.Range(0, 1); return yes(r.getClass().isRecord(), \"Range must be a record\"); }"],
  ['''class Solution {
    record Range(int lo, int hi) {
        int length() { return hi - lo; }
        boolean contains(int value) { return lo <= value && value <= hi; }
        boolean overlaps(Range other) { return lo <= other.hi && other.lo <= hi; }
        static Range of(int a, int b) { return new Range(Math.min(a, b), Math.max(a, b)); }
    }
}
''', '''class Solution {
    record Range(int lo, int hi) {
        Range {
            if (lo > hi) throw new IllegalArgumentException();
        }
        int length() { return hi - lo + 1; }
        boolean contains(int value) { return lo < value && value < hi; }
        boolean overlaps(Range other) { return lo < other.hi && other.lo < hi; }
        static Range of(int a, int b) { return new Range(Math.min(a, b), Math.max(a, b)); }
    }
}
'''],
  G("Lessons *Classes and objects: blueprint and building* (records), *Constructors, this and super* (compact constructors).",
    "A record is a class whose state is exactly its components. You add the rule (lo ≤ hi) in the compact constructor, and behaviour as ordinary methods; equality and printing come for free.",
    ["A compact constructor has no parameter list: `Range { ... }`. The fields are assigned automatically after your checks.", "Two closed ranges overlap when each starts no later than the other ends.", "`of` normalises the order with `Math.min` and `Math.max`."],
    "A hand-written class needs a constructor, two private final fields, two accessors, `equals`, `hashCode` and `toString`: about thirty lines to say what `record Range(int lo, int hi)` says.",
    r"""**Dry run** `new Range(1, 5).overlaps(new Range(5, 9))`: `1 <= 9` and `5 <= 5` → `true`; the ranges share the number 5.

```java
class Solution {
    record Range(int lo, int hi) {
        Range {                                               // compact canonical constructor
            if (lo > hi) throw new IllegalArgumentException("lo " + lo + " is greater than hi " + hi);
        }

        int length()                  { return hi - lo + 1; }
        boolean contains(int value)   { return lo <= value && value <= hi; }
        boolean overlaps(Range other) { return lo <= other.hi && other.lo <= hi; }

        static Range of(int a, int b) { return new Range(Math.min(a, b), Math.max(a, b)); }
    }
}
```""",
    "Every operation is O(1).",
    "- No validation: an invalid `Range(5, 1)` can then exist.\n- `hi - lo` for the length (off by one).\n- Strict `<` in `contains` or `overlaps` excludes the end points of a closed range."),
  ),
# ------------------------------------------------------------------ java-code-money-equals
J("java-code-money-equals", "equals and hashCode by hand", "Medium", "Java objects",
  r"""
Inside `Solution`, complete the ordinary class (not a record) `Money` so that two objects with the same
amount and currency are **equal** and work correctly in `HashSet` and `HashMap`.

```java
static final class Money {
    Money(long cents, String currency)      // currency is never null
    long cents()
    String currency()
    @Override public boolean equals(Object o)
    @Override public int hashCode()
    @Override public String toString()      // "<cents> <currency>", e.g. "500 GBP"
}
```

Rules to respect: `equals` takes an `Object`; it returns `false` for `null` and for objects of other types;
equal objects have equal hash codes.

**Example** `new HashSet<>(List.of(new Money(500, "GBP"), new Money(500, "GBP"))).size()` → `1`.
""",
  '''class Solution {
    static final class Money {
        private final long cents;
        private final String currency;

        Money(long cents, String currency) {
            this.cents = cents;
            this.currency = currency;
        }

        long cents() { return cents; }

        String currency() { return currency; }

        // equals, hashCode, toString
    }
}
''',
  '''class Solution {
    static final class Money {
        private final long cents;
        private final String currency;

        Money(long cents, String currency) {
            this.cents = cents;
            this.currency = currency;
        }

        long cents() { return cents; }

        String currency() { return currency; }

        @Override
        public boolean equals(Object o) {
            if (this == o) {
                return true;
            }
            if (!(o instanceof Money other)) {
                return false;
            }
            return cents == other.cents && currency.equals(other.currency);
        }

        @Override
        public int hashCode() {
            return 31 * Long.hashCode(cents) + currency.hashCode();
        }

        @Override
        public String toString() {
            return cents + " " + currency;
        }
    }
}
''',
  ['eq(new Solution.Money(500, "GBP"), new Solution.Money(500, "GBP"))', 'eq(new Solution.Money(500, "GBP").hashCode(), new Solution.Money(500, "GBP").hashCode())',
   'yes(!new Solution.Money(500, "GBP").equals(new Solution.Money(501, "GBP")), "different amounts must not be equal")',
   'yes(!new Solution.Money(500, "GBP").equals(new Solution.Money(500, "EUR")), "different currencies must not be equal")',
   'yes(!new Solution.Money(500, "GBP").equals(null), "equals(null) must be false")', 'yes(!new Solution.Money(500, "GBP").equals("500 GBP"), "a Money is never equal to a String")',
   '{ Solution.Money m = new Solution.Money(1, "USD"); return yes(m.equals(m), "must be reflexive"); }',
   'eq(new HashSet<>(List.of(new Solution.Money(500, "GBP"), new Solution.Money(500, new String("GBP")), new Solution.Money(7, "GBP"))).size(), 2)',
   '{ Map<Solution.Money, String> m = new HashMap<>(); m.put(new Solution.Money(9000000000L, "JPY"), "big"); return eq(m.get(new Solution.Money(9000000000L, "JPY")), "big"); }',
   'eq(new Solution.Money(500, "GBP").toString(), "500 GBP")',
   'eq(List.of(new Solution.Money(1, "A"), new Solution.Money(2, "B")).contains(new Solution.Money(2, "B")), true)',
   '{ Set<Integer> hashes = new HashSet<>(); for (int i = 0; i < 200; i++) hashes.add(new Solution.Money(i, "GBP").hashCode()); return yes(hashes.size() > 100, "hashCode should spread values, not return a constant"); }'],
  ['''class Solution {
    static final class Money {
        private final long cents;
        private final String currency;
        Money(long cents, String currency) { this.cents = cents; this.currency = currency; }
        long cents() { return cents; }
        String currency() { return currency; }
        public boolean equals(Money other) {
            return other != null && cents == other.cents && currency.equals(other.currency);
        }
        @Override public int hashCode() { return 31 * Long.hashCode(cents) + currency.hashCode(); }
        @Override public String toString() { return cents + " " + currency; }
    }
}
''', '''class Solution {
    static final class Money {
        private final long cents;
        private final String currency;
        Money(long cents, String currency) { this.cents = cents; this.currency = currency; }
        long cents() { return cents; }
        String currency() { return currency; }
        @Override public boolean equals(Object o) {
            if (!(o instanceof Money other)) return false;
            return cents == other.cents && currency.equals(other.currency);
        }
        @Override public String toString() { return cents + " " + currency; }
    }
}
''', '''class Solution {
    static final class Money {
        private final long cents;
        private final String currency;
        Money(long cents, String currency) { this.cents = cents; this.currency = currency; }
        long cents() { return cents; }
        String currency() { return currency; }
        @Override public boolean equals(Object o) {
            if (!(o instanceof Money other)) return false;
            return cents == other.cents && currency == other.currency;
        }
        @Override public int hashCode() { return 31 * Long.hashCode(cents) + currency.hashCode(); }
        @Override public String toString() { return cents + " " + currency; }
    }
}
'''],
  G("Lesson *Writing equals and hashCode correctly*.",
    "`equals` answers 'same value?' field by field; `hashCode` must be computed from the same fields so that equal objects land in the same bucket.",
    ["The parameter of `equals` must be `Object`; `@Override` makes the compiler check it.", "`o instanceof Money other` handles both the type test and `null`.", "Compare the `long` with `==` and the `String` with `equals`; combine their hashes with the multiplier 31."],
    "A record generates all three methods: `record Money(long cents, String currency) { }`. Writing them by hand once shows what the record is doing for you.",
    r"""**Dry run** a set receiving `Money(500, "GBP")` twice: both objects have the same `hashCode`, so they go to the same bucket; `equals` then returns `true`, and the second is rejected. Size 1.

```java
@Override
public boolean equals(Object o) {
    if (this == o) return true;                              // same object
    if (!(o instanceof Money other)) return false;           // wrong type or null
    return cents == other.cents && currency.equals(other.currency);
}

@Override
public int hashCode() {
    return 31 * Long.hashCode(cents) + currency.hashCode();  // or Objects.hash(cents, currency)
}
```""",
    "Both methods are O(length of the currency string); effectively O(1).",
    "- `equals(Money other)` overloads instead of overriding: collections never call it.\n- Overriding `equals` without `hashCode`: hash collections treat equal objects as different.\n- Comparing the `String` field with `==`.\n- A constant `hashCode` is legal and makes every hash table a linked list."),
  ),
# ------------------------------------------------------------------ java-code-immutable-playlist
J("java-code-immutable-playlist", "An immutable class with defensive copies", "Medium", "Java classes",
  r"""
Inside `Solution`, write an **immutable** class.

```java
static final class Playlist {
    Playlist(String name, List<String> tracks)      // NullPointerException if name or tracks is null
    String name()
    List<String> tracks()                           // the tracks, in order
    int size()
    Playlist withTrack(String track)                // a NEW playlist with the track added at the end; this one is unchanged
}
```

Nothing outside the class may be able to change a playlist after it is created:

- changing the list passed to the constructor afterwards must not affect the playlist;
- changing the list returned by `tracks()` must not affect the playlist. (It is fine for that list to throw
  `UnsupportedOperationException` on modification, or to be a copy.)
""",
  '''import java.util.*;

class Solution {
    static final class Playlist {
        Playlist(String name, List<String> tracks) {
        }

        String name() { return null; }

        List<String> tracks() { return null; }

        int size() { return 0; }

        Playlist withTrack(String track) { return this; }
    }
}
''',
  '''import java.util.*;

class Solution {
    static final class Playlist {
        private final String name;
        private final List<String> tracks;

        Playlist(String name, List<String> tracks) {
            this.name = Objects.requireNonNull(name, "name");
            this.tracks = List.copyOf(tracks);
        }

        String name() { return name; }

        List<String> tracks() { return tracks; }

        int size() { return tracks.size(); }

        Playlist withTrack(String track) {
            List<String> extended = new ArrayList<>(tracks);
            extended.add(track);
            return new Playlist(name, extended);
        }
    }
}
''',
  ['{ Solution.Playlist p = new Solution.Playlist("Morning", List.of("Tides", "Harbour")); return eq(p.tracks(), List.of("Tides", "Harbour")); }',
   '{ Solution.Playlist p = new Solution.Playlist("Morning", List.of("Tides")); return eq(p.name() + p.size(), "Morning1"); }',
   '{ List<String> src = new ArrayList<>(List.of("Tides")); Solution.Playlist p = new Solution.Playlist("M", src); src.add("sneaky"); return eq(p.tracks(), List.of("Tides")); }',
   '{ List<String> src = new ArrayList<>(List.of("Tides")); Solution.Playlist p = new Solution.Playlist("M", src); src.clear(); return eq(p.size(), 1); }',
   '{ Solution.Playlist p = new Solution.Playlist("M", new ArrayList<>(List.of("Tides"))); try { p.tracks().add("sneaky"); } catch (UnsupportedOperationException ok) { } return eq(p.tracks(), List.of("Tides")); }',
   '{ Solution.Playlist p = new Solution.Playlist("M", new ArrayList<>(List.of("a", "b"))); try { p.tracks().clear(); } catch (UnsupportedOperationException ok) { } return eq(p.size(), 2); }',
   '{ Solution.Playlist a = new Solution.Playlist("M", List.of("Tides")); Solution.Playlist b = a.withTrack("Harbour"); return eq(b.tracks(), List.of("Tides", "Harbour")); }',
   '{ Solution.Playlist a = new Solution.Playlist("M", List.of("Tides")); a.withTrack("Harbour"); return eq(a.tracks(), List.of("Tides")); }',
   '{ Solution.Playlist a = new Solution.Playlist("M", List.of()); Solution.Playlist b = a.withTrack("x").withTrack("y"); return eq(a.size() + "," + b.size() + "," + b.name(), "0,2,M"); }',
   'thrown(NullPointerException.class, () -> { new Solution.Playlist(null, List.of()); return null; })',
   'thrown(NullPointerException.class, () -> { new Solution.Playlist("M", null); return null; })',
   '{ Solution.Playlist a = new Solution.Playlist("M", List.of("t")); return yes(a.withTrack("u") != a, "withTrack must return a new object"); }'],
  ['''import java.util.*;

class Solution {
    static final class Playlist {
        private final String name;
        private final List<String> tracks;
        Playlist(String name, List<String> tracks) {
            this.name = Objects.requireNonNull(name);
            this.tracks = Objects.requireNonNull(tracks);
        }
        String name() { return name; }
        List<String> tracks() { return Collections.unmodifiableList(tracks); }
        int size() { return tracks.size(); }
        Playlist withTrack(String track) {
            List<String> extended = new ArrayList<>(tracks);
            extended.add(track);
            return new Playlist(name, extended);
        }
    }
}
''', '''import java.util.*;

class Solution {
    static final class Playlist {
        private final String name;
        private final List<String> tracks;
        Playlist(String name, List<String> tracks) {
            this.name = Objects.requireNonNull(name);
            this.tracks = new ArrayList<>(tracks);
        }
        String name() { return name; }
        List<String> tracks() { return tracks; }
        int size() { return tracks.size(); }
        Playlist withTrack(String track) {
            tracks.add(track);
            return this;
        }
    }
}
'''],
  G("Lessons *Minimal accessibility and immutable classes* and *Parameter checks, defensive copies, signatures and overloading*.",
    "`private final` fields are not enough when a field refers to a mutable list: the caller still holds the list they passed in, and a getter hands the list out again. Copy on the way in, and return something that cannot be modified.",
    ["`List.copyOf(tracks)` makes an independent, unmodifiable copy and throws `NullPointerException` for a null list.", "An unmodifiable list can be returned directly from `tracks()`.", "`withTrack` builds a new list and a new `Playlist`; it never touches `this`."],
    "`Collections.unmodifiableList(tracks)` around the caller's own list protects the getter and still leaves the constructor's back door open: the view shows every later change to the original.",
    r"""**Dry run** `src = [Tides]`; `p = new Playlist("M", src)` stores a copy `[Tides]`. `src.add("sneaky")` changes only `src`. `p.tracks()` is still `[Tides]`.

```java
import java.util.*;

class Solution {
    static final class Playlist {
        private final String name;
        private final List<String> tracks;

        Playlist(String name, List<String> tracks) {
            this.name = Objects.requireNonNull(name, "name");
            this.tracks = List.copyOf(tracks);                 // defensive copy, unmodifiable
        }

        String name()          { return name; }
        List<String> tracks()  { return tracks; }              // safe to share
        int size()             { return tracks.size(); }

        Playlist withTrack(String track) {                     // functional update
            List<String> extended = new ArrayList<>(tracks);
            extended.add(track);
            return new Playlist(name, extended);
        }
    }
}
```""",
    "Construction and `withTrack` are O(n) for n tracks; the accessors are O(1).",
    "- Storing the caller's list.\n- Returning the internal mutable list.\n- `withTrack` that modifies `this`.\n- Wrapping without copying."),
  ),
# ------------------------------------------------------------------ java-code-builder
J("java-code-builder", "The builder pattern", "Medium", "Java objects",
  r"""
Inside `Solution`, implement a class with a **builder**.

```java
static final class Pizza {
    static Builder builder(int sizeCm)          // the size is required
    int sizeCm()
    String crust()                              // default "classic"
    boolean extraCheese()                       // default false
    List<String> toppings()                     // default empty; in the order added

    static final class Builder {
        Builder crust(String crust)             // returns this
        Builder extraCheese()                   // returns this
        Builder topping(String topping)         // returns this
        Pizza build()                           // validates, then creates the Pizza
    }
}
```

`build()` throws `IllegalStateException` if the size is not between 15 and 50 (inclusive) or if there are
more than 5 toppings. The built `Pizza` must not change if the builder is used again afterwards.

**Example**

```java
Pizza p = Pizza.builder(30).crust("thin").topping("olive").extraCheese().build();
p.crust();        // "thin"
p.toppings();     // [olive]
```
""",
  '''import java.util.*;

class Solution {
    static final class Pizza {
        static Builder builder(int sizeCm) {
            return new Builder();
        }

        int sizeCm() { return 0; }

        String crust() { return null; }

        boolean extraCheese() { return false; }

        List<String> toppings() { return null; }

        static final class Builder {
            Builder crust(String crust) { return this; }

            Builder extraCheese() { return this; }

            Builder topping(String topping) { return this; }

            Pizza build() { return null; }
        }
    }
}
''',
  '''import java.util.*;

class Solution {
    static final class Pizza {
        private final int sizeCm;
        private final String crust;
        private final boolean extraCheese;
        private final List<String> toppings;

        private Pizza(Builder b) {
            this.sizeCm = b.sizeCm;
            this.crust = b.crust;
            this.extraCheese = b.extraCheese;
            this.toppings = List.copyOf(b.toppings);
        }

        static Builder builder(int sizeCm) {
            return new Builder(sizeCm);
        }

        int sizeCm() { return sizeCm; }

        String crust() { return crust; }

        boolean extraCheese() { return extraCheese; }

        List<String> toppings() { return toppings; }

        static final class Builder {
            private final int sizeCm;
            private String crust = "classic";
            private boolean extraCheese = false;
            private final List<String> toppings = new ArrayList<>();

            private Builder(int sizeCm) {
                this.sizeCm = sizeCm;
            }

            Builder crust(String crust) {
                this.crust = crust;
                return this;
            }

            Builder extraCheese() {
                this.extraCheese = true;
                return this;
            }

            Builder topping(String topping) {
                toppings.add(topping);
                return this;
            }

            Pizza build() {
                if (sizeCm < 15 || sizeCm > 50) {
                    throw new IllegalStateException("size must be 15..50 but was " + sizeCm);
                }
                if (toppings.size() > 5) {
                    throw new IllegalStateException("at most 5 toppings but got " + toppings.size());
                }
                return new Pizza(this);
            }
        }
    }
}
''',
  ['{ Solution.Pizza p = Solution.Pizza.builder(30).crust("thin").topping("olive").extraCheese().build(); return eq(p.sizeCm() + p.crust() + p.extraCheese() + p.toppings(), "30thintrue[olive]"); }',
   '{ Solution.Pizza p = Solution.Pizza.builder(20).build(); return eq(p.crust() + p.extraCheese() + p.toppings(), "classicfalse[]"); }',
   'thrown(IllegalStateException.class, () -> { Solution.Pizza.builder(14).build(); return null; })',
   'thrown(IllegalStateException.class, () -> { Solution.Pizza.builder(51).build(); return null; })',
   '{ Solution.Pizza p = Solution.Pizza.builder(15).build(); Solution.Pizza q = Solution.Pizza.builder(50).build(); return eq(p.sizeCm() + q.sizeCm(), 65); }',
   'thrown(IllegalStateException.class, () -> { Solution.Pizza.builder(30).topping("a").topping("b").topping("c").topping("d").topping("e").topping("f").build(); return null; })',
   '{ Solution.Pizza p = Solution.Pizza.builder(30).topping("a").topping("b").topping("c").topping("d").topping("e").build(); return eq(p.toppings(), List.of("a", "b", "c", "d", "e")); }',
   '{ Solution.Pizza.Builder b = Solution.Pizza.builder(30).topping("a"); Solution.Pizza p = b.build(); b.topping("later").crust("deep"); return eq(p.toppings() + p.crust(), "[a]classic"); }',
   '{ Solution.Pizza.Builder b = Solution.Pizza.builder(30); return yes(b.crust("thin") == b && b.extraCheese() == b && b.topping("x") == b, "builder methods must return this"); }',
   '{ Solution.Pizza p = Solution.Pizza.builder(30).topping("a").build(); try { p.toppings().add("hack"); } catch (UnsupportedOperationException ok) { } return eq(p.toppings(), List.of("a")); }',
   '{ Solution.Pizza p = Solution.Pizza.builder(40).crust("deep").crust("thin").build(); return eq(p.crust(), "thin"); }'],
  ['''import java.util.*;

class Solution {
    static final class Pizza {
        private final int sizeCm; private final String crust; private final boolean extraCheese; private final List<String> toppings;
        private Pizza(Builder b) { sizeCm = b.sizeCm; crust = b.crust; extraCheese = b.extraCheese; toppings = b.toppings; }
        static Builder builder(int sizeCm) { return new Builder(sizeCm); }
        int sizeCm() { return sizeCm; }
        String crust() { return crust; }
        boolean extraCheese() { return extraCheese; }
        List<String> toppings() { return toppings; }
        static final class Builder {
            private final int sizeCm; private String crust = "classic"; private boolean extraCheese; private final List<String> toppings = new ArrayList<>();
            private Builder(int sizeCm) { this.sizeCm = sizeCm; }
            Builder crust(String crust) { this.crust = crust; return this; }
            Builder extraCheese() { this.extraCheese = true; return this; }
            Builder topping(String topping) { toppings.add(topping); return this; }
            Pizza build() {
                if (sizeCm < 15 || sizeCm > 50) throw new IllegalStateException();
                if (toppings.size() > 5) throw new IllegalStateException();
                return new Pizza(this);
            }
        }
    }
}
''', '''import java.util.*;

class Solution {
    static final class Pizza {
        private final int sizeCm; private final String crust; private final boolean extraCheese; private final List<String> toppings;
        private Pizza(Builder b) { sizeCm = b.sizeCm; crust = b.crust; extraCheese = b.extraCheese; toppings = List.copyOf(b.toppings); }
        static Builder builder(int sizeCm) { return new Builder(sizeCm); }
        int sizeCm() { return sizeCm; }
        String crust() { return crust; }
        boolean extraCheese() { return extraCheese; }
        List<String> toppings() { return toppings; }
        static final class Builder {
            private final int sizeCm; private String crust = "classic"; private boolean extraCheese; private final List<String> toppings = new ArrayList<>();
            private Builder(int sizeCm) { this.sizeCm = sizeCm; }
            Builder crust(String crust) { this.crust = crust; return this; }
            Builder extraCheese() { this.extraCheese = true; return this; }
            Builder topping(String topping) { toppings.add(topping); return this; }
            Pizza build() {
                if (sizeCm <= 15 || sizeCm >= 50) throw new IllegalStateException();
                return new Pizza(this);
            }
        }
    }
}
'''],
  G("Lesson *Static factories, builders, singletons and dependency injection*.",
    "Two classes share the work. The builder is a mutable scratch pad whose methods return `this` so calls can be chained. `build()` checks the rules once and hands the values to a private constructor of the immutable product.",
    ["Give the builder its own fields with default values.", "Every configuration method ends with `return this;`.", "In the `Pizza` constructor copy the toppings (`List.copyOf`) so the builder and the pizza no longer share a list."],
    "A constructor `Pizza(int, String, boolean, List<String>)` works for four parameters and becomes unreadable at eight: `new Pizza(30, \"thin\", true, false, true, null)`.",
    r"""**Dry run** `builder(30).topping("a")`, `build()` → pizza with `[a]`. Then `b.topping("later")`: the builder's list is now `[a, later]`, but the pizza holds its own copy `[a]`.

```java
static final class Pizza {
    private final int sizeCm; private final String crust; private final boolean extraCheese; private final List<String> toppings;

    private Pizza(Builder b) {                                  // only the builder can call this
        sizeCm = b.sizeCm; crust = b.crust; extraCheese = b.extraCheese;
        toppings = List.copyOf(b.toppings);                     // snapshot
    }

    static Builder builder(int sizeCm) { return new Builder(sizeCm); }

    static final class Builder {
        private final int sizeCm;
        private String crust = "classic";
        private boolean extraCheese;
        private final List<String> toppings = new ArrayList<>();

        private Builder(int sizeCm) { this.sizeCm = sizeCm; }

        Builder crust(String c)   { this.crust = c; return this; }
        Builder extraCheese()     { this.extraCheese = true; return this; }
        Builder topping(String t) { toppings.add(t); return this; }

        Pizza build() {
            if (sizeCm < 15 || sizeCm > 50) throw new IllegalStateException("size must be 15..50 but was " + sizeCm);
            if (toppings.size() > 5) throw new IllegalStateException("at most 5 toppings but got " + toppings.size());
            return new Pizza(this);
        }
    }
}
```""",
    "Each builder call is O(1); `build()` is O(number of toppings).",
    "- Sharing the builder's list with the built object.\n- Forgetting `return this`.\n- Validating with the wrong boundaries (15 and 50 are allowed).\n- No validation of the topping count."),
  ),
# ------------------------------------------------------------------ java-code-two-sum
J("java-code-two-sum", "Two Sum in Java", "Easy", "Arrays & Hashing",
  r"""
In class `Solution`, write

```java
static int[] twoSum(int[] nums, int target)
```

Return the indices `{i, j}` with `i < j` of the two different positions whose values add up to `target`.
Exactly one such pair exists.

**Examples** `twoSum({2, 7, 11, 15}, 9)` → `{0, 1}`; `twoSum({3, 2, 4}, 6)` → `{1, 2}`; `twoSum({3, 3}, 6)` → `{0, 1}`.

Solve it in one pass with a `HashMap`; arrays may have 100,000 elements.
""",
  '''import java.util.*;

class Solution {
    static int[] twoSum(int[] nums, int target) {
        // your code
        return new int[0];
    }
}
''',
  '''import java.util.*;

class Solution {
    static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int j = 0; j < nums.length; j++) {
            Integer i = seen.get(target - nums[j]);
            if (i != null) {
                return new int[] {i, j};
            }
            seen.put(nums[j], j);
        }
        return new int[0];
    }
}
''',
  ["arr(Solution.twoSum(new int[] {2, 7, 11, 15}, 9), new int[] {0, 1})", "arr(Solution.twoSum(new int[] {3, 2, 4}, 6), new int[] {1, 2})", "arr(Solution.twoSum(new int[] {3, 3}, 6), new int[] {0, 1})",
   "arr(Solution.twoSum(new int[] {-1, -2, -3, -4, -5}, -8), new int[] {2, 4})", "arr(Solution.twoSum(new int[] {0, 4, 3, 0}, 0), new int[] {0, 3})",
   "arr(Solution.twoSum(new int[] {1, 5, 9, 14}, 23), new int[] {2, 3})", "arr(Solution.twoSum(new int[] {1000000000, 5, 1000000000}, 2000000000), new int[] {0, 2})",
   "arr(Solution.twoSum(new int[] {5, 75, 25}, 100), new int[] {1, 2})",
   "{ int[] a = new int[100000]; for (int i = 0; i < a.length; i++) a[i] = i * 2; return arr(Solution.twoSum(a, 399994), new int[] {99998, 99999}); }",
   "arr(Solution.twoSum(new int[] {1, 2}, 3), new int[] {0, 1})"],
  ['''class Solution {
    static int[] twoSum(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++)
            for (int j = 0; j < nums.length; j++)
                if (nums[i] + nums[j] == target) return new int[] {i, j};
        return new int[0];
    }
}
''', '''import java.util.*;

class Solution {
    static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int j = 0; j < nums.length; j++) seen.put(nums[j], j);
        for (int i = 0; i < nums.length; i++) {
            Integer j = seen.get(target - nums[i]);
            if (j != null) return new int[] {i, j};
        }
        return new int[0];
    }
}
'''],
  G("Lesson *Collections: List, Set, Map and Queue*: `HashMap` lookups in constant time.",
    "For each number, the partner it needs is `target - number`. Remember every number already seen, with its index, and ask the map whether the partner has appeared.",
    ["Map from value to index.", "Look up the partner **before** storing the current number, so an element is never paired with itself.", "The stored index is the smaller one: return `{stored, current}`."],
    "Two nested loops over all pairs `i < j`: O(n²). With 100,000 elements that is five billion additions.",
    r"""**Dry run** `{3, 2, 4}`, target 6. j=0: need 3, map empty; store 3→0. j=1: need 4, absent; store 2→1. j=2: need 2, found at 1 → `{1, 2}`.

```java
import java.util.*;

class Solution {
    static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int j = 0; j < nums.length; j++) {
            Integer i = seen.get(target - nums[j]);        // boxed: null means "not seen"
            if (i != null) return new int[] {i, j};
            seen.put(nums[j], j);
        }
        return new int[0];
    }
}
```""",
    "Time O(n) on average, space O(n).",
    "- Pairing an element with itself (`{0, 0}` for `{3, 2, 4}` and target 6).\n- Unboxing a `null` from `map.get`.\n- Filling the whole map first and then finding the same index twice.",
    leetcode="https://leetcode.com/problems/two-sum/"),
  ),
# ------------------------------------------------------------------ java-code-binary-search
J("java-code-binary-search", "Binary search in Java", "Easy", "Binary Search",
  r"""
In class `Solution`, write

```java
static int search(int[] sorted, int target)
```

`sorted` is in ascending order with no duplicates. Return the index of `target`, or `-1` if it is absent.
The method must run in logarithmic time: arrays may hold a million elements and the test checks many
lookups.

**Examples** `search({-1, 0, 3, 5, 9, 12}, 9)` → `4`; `search({-1, 0, 3, 5, 9, 12}, 2)` → `-1`.

Take care with the middle index: `(lo + hi) / 2` can overflow an `int` for very large arrays.
""",
  '''class Solution {
    static int search(int[] sorted, int target) {
        // your code
        return -1;
    }
}
''',
  '''class Solution {
    static int search(int[] sorted, int target) {
        int lo = 0, hi = sorted.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (sorted[mid] == target) {
                return mid;
            } else if (sorted[mid] < target) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return -1;
    }
}
''',
  ["eq(Solution.search(new int[] {-1, 0, 3, 5, 9, 12}, 9), 4)", "eq(Solution.search(new int[] {-1, 0, 3, 5, 9, 12}, 2), -1)", "eq(Solution.search(new int[] {}, 5), -1)",
   "eq(Solution.search(new int[] {5}, 5), 0)", "eq(Solution.search(new int[] {5}, 4), -1)", "eq(Solution.search(new int[] {1, 3}, 1), 0)", "eq(Solution.search(new int[] {1, 3}, 3), 1)",
   "eq(Solution.search(new int[] {1, 3, 5, 7, 9}, 10), -1)", "eq(Solution.search(new int[] {1, 3, 5, 7, 9}, 0), -1)",
   "{ int[] a = new int[1000000]; for (int i = 0; i < a.length; i++) a[i] = i * 3; long s = 0; for (int q = 0; q < 300000; q++) s += Solution.search(a, q * 9); return eq(s, 134999550000L); }",
   "eq(Solution.search(new int[] {Integer.MIN_VALUE, -7, 0, 7, Integer.MAX_VALUE}, Integer.MAX_VALUE), 4)",
   "eq(Solution.search(new int[] {Integer.MIN_VALUE, Integer.MAX_VALUE}, Integer.MAX_VALUE), 1)"],
  ['''class Solution {
    static int search(int[] sorted, int target) {
        int lo = 0, hi = sorted.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (sorted[mid] == target) return mid;
            else if (sorted[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }
}
''', '''class Solution {
    static int search(int[] sorted, int target) {
        int lo = 0, hi = sorted.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (sorted[mid] == target) return mid;
            else if (sorted[mid] - target < 0) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }
}
'''],
  G("Lessons *Loops, operators and casting* and *Primitive types and how numbers are stored* (overflow).",
    "Because the array is sorted, one comparison with the middle element rules out half of what is left. Keep the bounds of the part still under suspicion and halve it until it is empty.",
    ["`lo` and `hi` are inclusive bounds of the remaining range.", "The loop runs while `lo <= hi`; with `<` a single remaining element is never examined.", "Compute `mid = lo + (hi - lo) / 2` and compare with `<`, never by subtracting."],
    "Scan from the left until you meet the target: O(n). The million-element test with 300,000 lookups would take far too long.",
    r"""**Dry run** `{-1, 0, 3, 5, 9, 12}`, target 9. lo=0, hi=5, mid=2 (3 < 9) → lo=3. mid=4 (9) → return 4.

```java
class Solution {
    static int search(int[] sorted, int target) {
        int lo = 0, hi = sorted.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;          // (lo + hi) / 2 may overflow
            if (sorted[mid] == target)      return mid;
            else if (sorted[mid] < target)  lo = mid + 1;
            else                            hi = mid - 1;
        }
        return -1;
    }
}
// library: java.util.Arrays.binarySearch(sorted, target)  (returns a negative number when absent)
```""",
    "Time O(log n), space O(1).",
    "- `while (lo < hi)` skips the last candidate.\n- Not moving past `mid` (`lo = mid`) can loop for ever.\n- Comparing with `sorted[mid] - target < 0` overflows for values of opposite sign.",
    leetcode="https://leetcode.com/problems/binary-search/"),
  ),
# ------------------------------------------------------------------ java-code-reverse-linked-list
J("java-code-reverse-linked-list", "Reverse a linked list in Java", "Easy", "Linked List",
  r"""
`Solution` contains a node class for a singly linked list:

```java
static class Node {
    int val;
    Node next;
    Node(int val) { this.val = val; }
}
```

Write

```java
static Node reverse(Node head)
```

Reverse the list **in place** by re-pointing the `next` references, and return the new head. Do not create
new nodes. `reverse(null)` returns `null`.

**Example** `1 → 2 → 3 → null` becomes `3 → 2 → 1 → null`.
""",
  '''class Solution {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }

    static Node reverse(Node head) {
        // your code
        return head;
    }
}
''',
  '''class Solution {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }

    static Node reverse(Node head) {
        Node previous = null;
        Node current = head;
        while (current != null) {
            Node next = current.next;
            current.next = previous;
            previous = current;
            current = next;
        }
        return previous;
    }
}
''',
  ["eq(show(Solution.reverse(build(1, 2, 3))), \"3 2 1\")", "eq(show(Solution.reverse(build())), \"\")", "eq(show(Solution.reverse(build(7))), \"7\")",
   "eq(show(Solution.reverse(build(1, 2))), \"2 1\")", "eq(show(Solution.reverse(build(5, 5, 9))), \"9 5 5\")",
   "eq(show(Solution.reverse(Solution.reverse(build(1, 2, 3, 4)))), \"1 2 3 4\")",
   "{ Solution.Node h = build(1, 2, 3); Solution.Node last = h.next.next; return yes(Solution.reverse(h) == last, \"must reuse the existing nodes: the old last node becomes the head\"); }",
   "{ Solution.Node h = build(1, 2, 3); Solution.reverse(h); return yes(h.next == null, \"the old head must become the tail\"); }",
   "{ int[] v = new int[20000]; for (int i = 0; i < v.length; i++) v[i] = i; Solution.Node r = Solution.reverse(build(v)); return eq(r.val + \" \" + r.next.val, \"19999 19998\"); }",
   "eq(show(Solution.reverse(build(-1, 0, 1, 0, -1))), \"-1 0 1 0 -1\")"],
  ['''class Solution {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }
    static Node reverse(Node head) {
        Node result = null;
        for (Node n = head; n != null; n = n.next) {
            Node copy = new Node(n.val);
            copy.next = result;
            result = copy;
        }
        return result;
    }
}
''', '''class Solution {
    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }
    static Node reverse(Node head) {
        Node previous = null, current = head;
        while (current != null && current.next != null) {
            Node next = current.next;
            current.next = previous;
            previous = current;
            current = next;
        }
        return previous;
    }
}
'''],
  G("Lesson *References, arrays, the stack and the heap*: objects that refer to each other; re-pointing references.",
    "Walk along the list turning each arrow round. Before overwriting a node's `next`, save it, or the rest of the list is lost.",
    ["Three references: `previous` (starts `null`), `current` (starts at the head) and a saved `next`.", "Inside the loop: save, re-point, advance both.", "When `current` becomes `null`, `previous` is the new head."],
    "Copy the values into an `ArrayList`, then build a new list backwards. O(n) extra memory and new nodes, which the task forbids.",
    r"""**Dry run** `1 → 2 → 3`:

| step | previous | current | action |
|---|---|---|---|
| start | null | 1 | |
| 1 | 1 | 2 | 1.next = null |
| 2 | 2 | 3 | 2.next = 1 |
| 3 | 3 | null | 3.next = 2 |

Return `previous` = 3: `3 → 2 → 1 → null`.

```java
static Node reverse(Node head) {
    Node previous = null;
    Node current = head;
    while (current != null) {
        Node next = current.next;      // save
        current.next = previous;       // re-point
        previous = current;            // advance
        current = next;
    }
    return previous;
}
```""",
    "Time O(n), space O(1).",
    "- Overwriting `current.next` before saving it.\n- Stopping one node early and returning the wrong head.\n- A recursive version overflows the stack on a list of 20,000 nodes.",
    leetcode="https://leetcode.com/problems/reverse-linked-list/"),
  ),
# ------------------------------------------------------------------ java-code-merge-intervals
J("java-code-merge-intervals", "Merge intervals in Java", "Medium", "Intervals",
  r"""
In class `Solution`, write

```java
static int[][] merge(int[][] intervals)
```

Each element of `intervals` is `{start, end}` with `start <= end`. Merge all intervals that overlap or
touch (`{1, 4}` and `{4, 5}` merge) and return the result sorted by start. The input is in no particular
order. Do not modify the arrays you were given.

**Examples** `merge({{1,3},{2,6},{8,10},{15,18}})` → `{{1,6},{8,10},{15,18}}`; `merge({{1,4},{4,5}})` → `{{1,5}}`.
""",
  '''import java.util.*;

class Solution {
    static int[][] merge(int[][] intervals) {
        // your code
        return intervals;
    }
}
''',
  '''import java.util.*;

class Solution {
    static int[][] merge(int[][] intervals) {
        int[][] sorted = new int[intervals.length][];
        for (int i = 0; i < intervals.length; i++) {
            sorted[i] = intervals[i].clone();
        }
        Arrays.sort(sorted, Comparator.comparingInt(a -> a[0]));
        List<int[]> out = new ArrayList<>();
        for (int[] cur : sorted) {
            if (out.isEmpty() || out.get(out.size() - 1)[1] < cur[0]) {
                out.add(cur);
            } else {
                int[] last = out.get(out.size() - 1);
                last[1] = Math.max(last[1], cur[1]);
            }
        }
        return out.toArray(new int[0][]);
    }
}
''',
  ["deep(Solution.merge(new int[][] {{1, 3}, {2, 6}, {8, 10}, {15, 18}}), new int[][] {{1, 6}, {8, 10}, {15, 18}})", "deep(Solution.merge(new int[][] {{1, 4}, {4, 5}}), new int[][] {{1, 5}})",
   "deep(Solution.merge(new int[][] {}), new int[][] {})", "deep(Solution.merge(new int[][] {{5, 7}}), new int[][] {{5, 7}})",
   "deep(Solution.merge(new int[][] {{8, 10}, {1, 3}, {2, 6}}), new int[][] {{1, 6}, {8, 10}})", "deep(Solution.merge(new int[][] {{1, 10}, {2, 3}, {4, 5}}), new int[][] {{1, 10}})",
   "deep(Solution.merge(new int[][] {{1, 2}, {3, 4}, {5, 6}}), new int[][] {{1, 2}, {3, 4}, {5, 6}})", "deep(Solution.merge(new int[][] {{2, 2}, {2, 2}, {1, 1}}), new int[][] {{1, 1}, {2, 2}})",
   "deep(Solution.merge(new int[][] {{-5, -1}, {-2, 3}, {4, 4}}), new int[][] {{-5, 3}, {4, 4}})",
   "{ int[][] in = {{3, 4}, {1, 5}}; Solution.merge(in); return deep(in, new int[][] {{3, 4}, {1, 5}}); }",
   "{ int[][] in = new int[20000][]; for (int i = 0; i < in.length; i++) in[i] = new int[] {i, i + 1}; return eq(Solution.merge(in).length, 1); }"],
  ['''import java.util.*;

class Solution {
    static int[][] merge(int[][] intervals) {
        List<int[]> out = new ArrayList<>();
        for (int[] cur : intervals) {
            if (out.isEmpty() || out.get(out.size() - 1)[1] < cur[0]) out.add(cur.clone());
            else out.get(out.size() - 1)[1] = Math.max(out.get(out.size() - 1)[1], cur[1]);
        }
        return out.toArray(new int[0][]);
    }
}
''', '''import java.util.*;

class Solution {
    static int[][] merge(int[][] intervals) {
        int[][] sorted = new int[intervals.length][];
        for (int i = 0; i < intervals.length; i++) sorted[i] = intervals[i].clone();
        Arrays.sort(sorted, Comparator.comparingInt(a -> a[0]));
        List<int[]> out = new ArrayList<>();
        for (int[] cur : sorted) {
            if (out.isEmpty() || out.get(out.size() - 1)[1] < cur[0]) out.add(cur);
            else out.get(out.size() - 1)[1] = cur[1];
        }
        return out.toArray(new int[0][]);
    }
}
'''],
  G("Lessons *Sorting with Comparable and Comparator* and *Collections: List, Set, Map and Queue*.",
    "Once the intervals are sorted by start, anything that overlaps the interval you are building must come next. So one pass suffices: extend the last result, or start a new one.",
    ["Copy, then sort by `a[0]` with `Comparator.comparingInt`.", "The current interval overlaps the last result when `last[1] >= cur[0]`.", "When merging, the new end is the **maximum** of the two ends."],
    "Compare every pair and merge until nothing changes: O(n²) or worse.",
    r"""**Dry run** sorted `{1,3}, {2,6}, {8,10}, {15,18}`: out `[{1,3}]`; `{2,6}`: 3 ≥ 2 → `{1,6}`; `{8,10}`: 6 < 8 → append; `{15,18}`: append.

```java
import java.util.*;

class Solution {
    static int[][] merge(int[][] intervals) {
        int[][] sorted = new int[intervals.length][];
        for (int i = 0; i < intervals.length; i++) sorted[i] = intervals[i].clone();   // leave the input alone
        Arrays.sort(sorted, Comparator.comparingInt(a -> a[0]));
        List<int[]> out = new ArrayList<>();
        for (int[] cur : sorted) {
            if (out.isEmpty() || out.get(out.size() - 1)[1] < cur[0]) {
                out.add(cur);
            } else {
                int[] last = out.get(out.size() - 1);
                last[1] = Math.max(last[1], cur[1]);
            }
        }
        return out.toArray(new int[0][]);
    }
}
```""",
    "Time O(n log n) for the sort, space O(n).",
    "- Forgetting to sort.\n- Setting the end to `cur[1]` when the current interval lies inside the last one.\n- `<=` versus `<`: touching intervals merge.\n- Sorting or editing the caller's arrays.",
    leetcode="https://leetcode.com/problems/merge-intervals/"),
  ),
# ------------------------------------------------------------------ java-code-lru-cache
J("java-code-lru-cache", "LRU cache in Java", "Hard", "Design",
  r"""
Inside `Solution`, implement a least-recently-used cache.

```java
static class LRUCache {
    LRUCache(int capacity)          // capacity >= 1
    int get(int key)                // the value, or -1 if absent; a hit makes the key the most recently used
    void put(int key, int value)    // insert or update; makes the key the most recently used;
                                    // if the cache then holds more than capacity entries, evict the least recently used
}
```

Both operations must take constant time on average.

**Example**

```java
LRUCache c = new LRUCache(2);
c.put(1, 1); c.put(2, 2);
c.get(1);          // 1   (key 1 is now the most recent)
c.put(3, 3);       // evicts key 2
c.get(2);          // -1
```

Two good solutions: extend `LinkedHashMap` with access order and `removeEldestEntry`, or build a `HashMap`
plus a doubly linked list yourself.
""",
  '''import java.util.*;

class Solution {
    static class LRUCache {
        LRUCache(int capacity) {
        }

        int get(int key) {
            return -1;
        }

        void put(int key, int value) {
        }
    }
}
''',
  '''import java.util.*;

class Solution {
    static class LRUCache {
        private final int capacity;
        private final LinkedHashMap<Integer, Integer> map;

        LRUCache(int capacity) {
            this.capacity = capacity;
            this.map = new LinkedHashMap<>(16, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
                    return size() > LRUCache.this.capacity;
                }
            };
        }

        int get(int key) {
            Integer v = map.get(key);
            return v == null ? -1 : v;
        }

        void put(int key, int value) {
            map.put(key, value);
        }
    }
}
''',
  ["{ Solution.LRUCache c = new Solution.LRUCache(2); c.put(1, 1); c.put(2, 2); return eq(c.get(1), 1); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(2); c.put(1, 1); c.put(2, 2); c.get(1); c.put(3, 3); return eq(c.get(2), -1); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(2); c.put(1, 1); c.put(2, 2); c.get(1); c.put(3, 3); return eq(c.get(1) + \",\" + c.get(3), \"1,3\"); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(2); c.put(1, 1); c.put(2, 2); c.put(3, 3); return eq(c.get(1) + \",\" + c.get(2) + \",\" + c.get(3), \"-1,2,3\"); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(1); c.put(1, 10); c.put(2, 20); return eq(c.get(1) + \",\" + c.get(2), \"-1,20\"); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(2); return eq(c.get(5), -1); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(2); c.put(1, 1); c.put(1, 100); return eq(c.get(1), 100); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(2); c.put(1, 1); c.put(2, 2); c.put(1, 100); c.put(3, 3); return eq(c.get(1) + \",\" + c.get(2), \"100,-1\"); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(3); c.put(1, 1); c.put(2, 2); c.put(3, 3); c.get(1); c.get(2); c.put(4, 4); return eq(c.get(3) + \",\" + c.get(1) + \",\" + c.get(4), \"-1,1,4\"); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(2); c.put(2, 1); c.put(2, 2); c.get(2); c.put(1, 1); c.put(4, 1); return eq(c.get(2), -1); }",
   "{ Solution.LRUCache c = new Solution.LRUCache(1000); long s = 0; for (int i = 0; i < 200000; i++) { c.put(i, i); s += c.get(i - 999); s += c.get(i - 1500); } return eq(s, 25951822L); }"],
  ['''import java.util.*;

class Solution {
    static class LRUCache {
        private final int capacity;
        private final LinkedHashMap<Integer, Integer> map = new LinkedHashMap<>();
        LRUCache(int capacity) { this.capacity = capacity; }
        int get(int key) {
            Integer v = map.get(key);
            return v == null ? -1 : v;
        }
        void put(int key, int value) {
            map.put(key, value);
            if (map.size() > capacity) {
                Integer eldest = map.keySet().iterator().next();
                map.remove(eldest);
            }
        }
    }
}
''', '''import java.util.*;

class Solution {
    static class LRUCache {
        private final int capacity;
        private final Map<Integer, Integer> map = new HashMap<>();
        LRUCache(int capacity) { this.capacity = capacity; }
        int get(int key) {
            Integer v = map.get(key);
            return v == null ? -1 : v;
        }
        void put(int key, int value) {
            if (!map.containsKey(key) && map.size() == capacity) return;
            map.put(key, value);
        }
    }
}
'''],
  G("Lessons *Collections: List, Set, Map and Queue* (`LinkedHashMap`), *Needless objects, memory leaks and resource clean-up* (bounded caches), *Nested, inner, local and anonymous classes*.",
    "Two needs at once: find a key instantly (a hash map) and know which key was used longest ago (an ordering by recency). `LinkedHashMap` in **access order** maintains exactly that ordering, and calls `removeEldestEntry` after every insertion.",
    ["`new LinkedHashMap<>(16, 0.75f, true)`: the third argument switches from insertion order to access order.", "Override `removeEldestEntry` to return `size() > capacity`.", "`get` must go through the map's own `get` so that the access is recorded; translate `null` to -1."],
    "A plain `LinkedHashMap` in insertion order evicts the oldest **inserted** key, which is FIFO, not LRU: a `get` does not refresh a key. Tracking recency in an `ArrayList` works and makes every operation O(n).",
    r"""**Dry run** capacity 2: `put(1,1)`, `put(2,2)` → order `[1, 2]`. `get(1)` → order `[2, 1]`. `put(3,3)` → `[2, 1, 3]`, size 3 > 2, evict the eldest, 2 → `[1, 3]`. `get(2)` → -1.

```java
import java.util.*;

class Solution {
    static class LRUCache {
        private final int capacity;
        private final LinkedHashMap<Integer, Integer> map;

        LRUCache(int capacity) {
            this.capacity = capacity;
            this.map = new LinkedHashMap<>(16, 0.75f, true) {            // access order
                @Override
                protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
                    return size() > LRUCache.this.capacity;
                }
            };
        }

        int get(int key)             { Integer v = map.get(key); return v == null ? -1 : v; }
        void put(int key, int value) { map.put(key, value); }
    }
}
```

The interview follow-up is to build it without `LinkedHashMap`: a `HashMap<Integer, Node>` plus a doubly linked list with sentinel head and tail nodes; on every access unlink the node and re-insert it at the tail; evict from the head.""",
    "Time O(1) average for both operations, space O(capacity).",
    "- Insertion order instead of access order.\n- Refusing new keys when full, instead of evicting.\n- Forgetting that updating an existing key also refreshes it.\n- Unboxing a `null` result.",
    leetcode="https://leetcode.com/problems/lru-cache/"),
  ),
]

# The linked-list problem needs two helper methods in its harness.
_LL_HELPERS = r'''    static Solution.Node build(int... vals) {
        Solution.Node head = null, tail = null;
        for (int v : vals) {
            Solution.Node n = new Solution.Node(v);
            if (head == null) { head = n; tail = n; } else { tail.next = n; tail = n; }
        }
        return head;
    }

    static String show(Solution.Node head) {
        StringBuilder sb = new StringBuilder();
        int guard = 0;
        for (Solution.Node n = head; n != null; n = n.next) {
            if (sb.length() > 0) sb.append(' ');
            sb.append(n.val);
            if (++guard > 100000) return "cycle detected";
        }
        return sb.toString();
    }

    public static void main(String[] args) {
'''
for _p in PROBLEMS:
    if _p["id"] == "java-code-reverse-linked-list":
        _p["harness"] = _p["harness"].replace("    public static void main(String[] args) {\n", _LL_HELPERS, 1)
