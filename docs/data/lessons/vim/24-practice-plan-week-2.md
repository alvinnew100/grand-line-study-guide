# A 14-day practice plan, week 2: registers, search, Ex commands and macros

> **Before this lesson:** complete [week 1 of the practice plan](#/lesson/vim/vim-practice-week1), or be confident with operators, motions, text objects and the dot command. Each day below links to the lesson that teaches its topic.

## In plain words

Week 1 trained the hands on single edits: change this word, delete up to that comma, repeat on the next line. Week 2 is about **scale**: doing an edit in many places, across many lines, with one instruction.

Compare a cook preparing one plate with a cook running a kitchen. The knife skills are the same. What changes is organisation: ingredients set out in labelled containers, one instruction that covers forty plates, a recipe written down so that anyone can repeat it. This week's tools are those organisational skills for text:

- **registers**: labelled containers for copied text;
- **search and substitution**: "find every place that looks like this, and change it";
- **Ex commands**: instructions that apply to a whole range of lines at once;
- **macros**: a recorded recipe of keystrokes, replayed on demand;
- **the global command and multiple files**: "do this to every line, or every file, that qualifies".

Why it matters for a job: these are the edits that would otherwise take half an hour of careful, boring, error-prone hand work, such as reformatting a data file, renaming something throughout a module, or cleaning up a log. Done with the right command they take a minute, and the result is consistent.

### Where to practise this week

Days 8, 9 and 12 work in **this site's code editor** with Vim mode switched on (**⚙ settings menu**, then **Vim mode**). Days 10, 11, 13 and 14 use Vim's own pattern language and Ex commands in ways that a browser editor only partly supports, so do those in a real **Vim or Neovim** on your computer. To start a scratch session in a terminal, type `vim` and press Enter; paste the drill text in Insert mode; and when you are finished type `:q!` and Enter to leave without saving.

Notation is the same as in week 1: `[x]` marks the character under the cursor, `<Esc>` is Escape, `<CR>` is Enter, `<C-r>` is Ctrl with `r`, and `␣` is a space. The rules also stand: three repetitions, predict before pressing, undo with `u` when the result differs, twenty minutes a day.

```mermaid
flowchart LR
    D8["Day 8: registers"] --> D9["Day 9: search and cgn"]
    D9 --> D10["Day 10: substitution"]
    D10 --> D11["Day 11: Ex ranges, copy, move, normal"]
    D11 --> D12["Day 12: macros"]
    D12 --> D13["Day 13: global command, buffers, windows"]
    D13 --> D14["Day 14: capstone"]
    D14 --> M["Afterwards: spaced review"]
```

## Day 8: registers

**Read first:** [registers](#/lesson/vim/vim-registers).

**The idea.** A **register** is a named storage slot for text. When you copy (Vim says *yank*, key `y`) or delete without naming a slot, the text goes to the *unnamed* register, and `p` (*put*, Vim's word for paste) reads from there. That is why a deletion can overwrite what you copied. Three registers fix nearly every such problem:

| Register | Typed as | Holds |
|---|---|---|
| yank register | `"0` | your most recent yank; deletions never touch it |
| named registers | `"a` to `"z` | whatever you put there; a capital letter (`"A`) adds to the end |
| black hole | `"_` | nothing: text sent there disappears and no other register changes |

A register name is typed **before** the command: `"ayy` yanks a line into `a`; `"ap` puts from `a`.

**Drill A: copy a value into another string**

```text
primary = "blue"
accent = "red"
```

| # | Before | Keys | After | Why |
|---|---|---|---|---|
| 1 | cursor at the start of line 1 | `yi"` | unchanged; cursor on the `b` of `blue` | yank inside the quotes (the command looks ahead along the line for them) |
| 2 | | `j` | cursor inside `red` on line 2 | |
| 3 | | `ci"<C-r>0<Esc>` | `accent = "blu[e]"` | change inside the quotes; `<C-r>0` types the contents of the yank register |

**Drill B: delete without losing what you copied**

```text
good_name = 1
print(bad)
```

| # | Before | Keys | After |
|---|---|---|---|
| 1 | cursor at the start of line 1 | `yiw` | `good_name` is yanked |
| 2 | | `jfb` | cursor on the `b` of `bad` |
| 3 | | `"_diw` | `print([)]` ; the deleted word went to the black hole |
| 4 | | `P` | `print(good_nam[e])` |

Repeat drill B with plain `diw` in step 3 and watch `P` put `bad` straight back. Then fix it a different way: `diw` followed by `"0P`.

**Drill C: collect lines**

With any three-line text and the cursor on line 1: `"ayy` (yank line 1 into `a`), `j"Ayy` (append line 2), `G"ap` (go to the last line and put both collected lines below it).

**Check:** after `yiw` on one word and `dd` on some other line, which keys put the yanked word? (`"0p`.) Which register holds the deleted line? (`"1`, and the unnamed register.)

## Day 9: search, and changing every match

**Read first:** [patterns and search](#/lesson/vim/vim-patterns-search) and [the dot formula](#/lesson/vim/vim-dot-formula).

**The idea.** `/text<CR>` jumps to the next place `text` appears; `n` goes to the following one and `N` to the previous. `*` searches for the whole word under the cursor without your typing it. And `gn` is a text object meaning "the next match of the last search", so `cgn` followed by new text and `<Esc>` makes a change that finds its own target: after it, each press of `.` changes one more match.

**Drill text:**

```text
count = 0
for item in items:
    count += item.size
print("count", count)
```

**A. Change every match**

| # | Before | Keys | After |
|---|---|---|---|
| 1 | cursor on `count` in line 1 | `*` | cursor on `count` in line 3 |
| 2 | | `cgntotal<Esc>` | line 3: `    tota[l] += item.size` |
| 3 | | `.` | line 4: `print("total", count)` |
| 4 | | `.` | line 4: `print("total", total)` |
| 5 | | `.` | line 1: `total = 0` (the search wrapped round to the top) |

**B. Change some matches and skip others.** Press `u` four times to restore the text, then `gg` to return to line 1. Suppose the word inside the quotes must stay.

| # | Before | Keys | After |
|---|---|---|---|
| 1 | cursor on `count` in line 1 | `*` | line 3 |
| 2 | | `cwtotal<Esc>` | line 3 changed |
| 3 | | `n` | cursor on `count` inside the quotes: look, decide to skip |
| 4 | | `n` | cursor on the second `count` of line 4 |
| 5 | | `.` | `print("count", total)` |
| 6 | | `n.` | line 1: `total = 0` |

Drill A is quickest; drill B gives you a look at each match before you commit. Knowing both and choosing between them is the skill.

**Check:** what does `N` do after a search started with `/`? (Goes to the previous match, toward the top of the file.) After `*` on the word `id`, will the search stop on `width`? (No: `*` searches for the whole word only.)

## Day 10: substitution

**Read first:** [substitution](#/lesson/vim/vim-substitute). Use real Vim or Neovim today.

**The idea.** The substitute command replaces text that matches a pattern. Its shape is `:[range]s/pattern/replacement/flags`. With no range it works on the current line; `%` means every line. With no flags it replaces the first match on each line; the flag `g` means every match and `c` asks you to confirm each one. In the replacement, `\1`, `\2` … stand for the parts of the match that the pattern wrapped in parentheses.

**Drill text:**

```text
2026-01-15 login ok
2026-01-16 login failed
2026-01-17 logout ok
```

| # | Command | Result | Why |
|---|---|---|---|
| 1 | `:%s/login/sign-in/` | lines 1 and 2 now say `sign-in`; line 3 still says `logout` | `logout` does not contain the letters `login` in that order |
| 2 | `:%s/ok$/OK/` | lines 1 and 3 end in `OK` | `$` means "at the end of the line" |
| 3 | `:%s/\v(\d+)-(\d+)-(\d+)/\3.\2.\1/` | dates become `15.01.2026`, `16.01.2026`, `17.01.2026` | three groups of digits are captured and written back in reverse order with dots |
| 4 | `:%s/OK$//n` | the message `2 matches on 2 lines`, and no change | flag `n` only counts |
| 5 | `u` three times | the original text is back | each substitution is a single undo step |

Step 3 piece by piece: `\v` switches on "very magic" mode, in which parentheses and `+` need no backslash. `(\d+)` is "one or more digits, remembered". There are three such groups separated by hyphens. The replacement `\3.\2.\1` writes the third group, a dot, the second, a dot, and the first.

**One more, with confirmation.** Run `:%s/o/0/gc` and answer `y` (yes) and `n` (no) to a few prompts, then `q` to stop. Undo with `u`.

**Check:** why did step 1 not need the `g` flag? (Each line contains `login` at most once.) What would `:s/login/sign-in/` without the `%` have changed? (Only the line the cursor was on.)

## Day 11: Ex commands on ranges of lines

**Read first:** [command-line mode](#/lesson/vim/vim-command-line). Use real Vim or Neovim.

**The idea.** An **Ex command** is typed after a colon and acts on a **range** of lines, wherever the cursor happens to be. A range is one line (`3`), a span (`2,4`), the current line (`.`), the last line (`$`) or everything (`%`). Three commands to learn today: `:t` copies lines to below a given line, `:m` moves them, and `:normal` types Normal-mode keys on every line of a range.

**Drill text** (put the cursor on the last line before you start):

```text
one
two
three
four
five
```

| # | Command | Buffer afterwards | Explanation |
|---|---|---|---|
| 1 | `:2t.` | `one` `two` `three` `four` `five` `two` | copy line 2 to below the current line (`.`); the cursor moves to the copy |
| 2 | `:m0` | `two` `one` `two` `three` `four` `five` | move the current line to below line 0, that is, to the top |
| 3 | `:2,4normal A;` | `two` `one;` `two;` `three;` `four` `five` | on lines 2 to 4, type `A;` (append a semicolon) |
| 4 | `:$d` | `two` `one;` `two;` `three;` `four` | delete the last line |
| 5 | `:2,3m$` | `two` `three;` `four` `one;` `two;` | move lines 2 and 3 to the end |
| 6 | `@:` | `two` `one;` `two;` `three;` `four` | repeat the last Ex command: the *new* lines 2 and 3 move to the end |

Step 6 shows `@:`, the "do it again" key for Ex commands. Notice that it repeats the instruction ("move lines 2 and 3 to the end"), applied to whatever is on those lines now.

**The selection shortcut.** Select a few lines with `V` and `j`, then press `:`. Vim fills in `:'<,'>`, which means "the selected lines". Type `normal I#␣` and press Enter to put `# ` in front of each.

**Check:** which command duplicates the current line directly below itself? (`:t.`) Which single command appends `!` to every line of the file? (`:%normal A!`)

## Day 12: macros

**Read first:** [macros](#/lesson/vim/vim-macros).

**The idea.** A **macro** is a recording of keystrokes. `qa` starts recording into register `a`, a second `q` stops, `@a` replays, `@@` replays again, and a number in front (`5@a`) replays that many times. A reliable macro starts by putting the cursor in a known place (`0`), moves with commands that name their target (`w`, `f`, `A`), and ends by moving to the next line (`j`).

**Drill text:** names that should become `Surname, Forename` with capital letters.

```text
ada lovelace
alan turing
grace hopper
```

Record on the first line. The table shows that line after each piece.

| Keys | Meaning | Line 1 afterwards |
|---|---|---|
| `qa` | start recording into `a` | `[a]da lovelace` |
| `0` | first column | `[a]da lovelace` |
| `~` | toggle the case of the character and step right | `A[d]a lovelace` |
| `w` | next word | `Ada [l]ovelace` |
| `~` | capitalise it | `Ada L[o]velace` |
| `0` | back to the first column | `[A]da Lovelace` |
| `dw` | delete the forename and its space (they go to the unnamed register) | `[L]ovelace` |
| `A,␣<Esc>` | append a comma and a space | `Lovelace,[ ]` |
| `p` | put the forename after the cursor | `Lovelace, Ada[ ]` |
| `x` | delete the trailing space that came along with it | `Lovelace, Ad[a]` |
| `j` | down to the next line | |
| `q` | stop recording | |

In one piece: `qa0~w~0dwA, <Esc>pxjq`.

| # | Keys | Result |
|---|---|---|
| 1 | `@a` | line 2 becomes `Turing, Alan` |
| 2 | `@@` | line 3 becomes `Hopper, Grace` |

**Then try the other style.** Undo back to the original three lines (`u` repeatedly), record the same macro **without** the final `j`, select all three lines with `ggVG`, and type `:normal @a<CR>` (the command line will read `:'<,'>normal @a`). All three lines are converted in one step, and one `u` undoes the lot. This form needs real Vim.

**Check:** why does the macro begin with `0`? (So that every replay starts from the same position, wherever the previous one left the cursor.) What happens if you play it on an empty line? (`w` or `dw` cannot do what was recorded, the macro stops, and nothing is damaged.)

## Day 13: the global command, buffers and windows

**Read first:** [the global command](#/lesson/vim/vim-global), [buffers](#/lesson/vim/vim-buffers) and [windows](#/lesson/vim/vim-windows-tabs). Use real Vim or Neovim.

**The idea, part 1.** `:g/pattern/command` runs an Ex command on every line that contains a match for the pattern. `:v/pattern/command` runs it on every line that does **not**. With no command, the matching lines are only shown.

**Drill text:**

```text
INFO boot
DEBUG cache warm
ERROR disk full
DEBUG retry 1
INFO done
ERROR timeout
```

| # | Command | Buffer afterwards |
|---|---|---|
| 1 | `:g/ERROR/` | unchanged; the two `ERROR` lines are listed at the bottom of the screen |
| 2 | `:g/DEBUG/d` | the two `DEBUG` lines are gone; four lines remain |
| 3 | `:g/ERROR/t$` | six lines: the four, followed by copies of `ERROR disk full` and `ERROR timeout` |
| 4 | `u` | back to four lines |
| 5 | `:v/ERROR/d` | only `ERROR disk full` and `ERROR timeout` remain |
| 6 | `u` then `:g/^/m0` | the four lines in reverse order |

**The idea, part 2.** A **buffer** is a file loaded into Vim's memory; a **window** is a view onto a buffer. You can have many buffers and show one, two or more of them at a time.

Create two scratch files to play with: in a terminal, start Vim with two names, `vim notes.txt todo.txt` (they do not need to exist).

| # | Keys or command | What happens |
|---|---|---|
| 1 | `:ls` | lists both buffers; `%` marks the one you are looking at |
| 2 | `:bnext` | switches to `todo.txt` (if you have typed anything unsaved, first run `:set hidden`) |
| 3 | `<C-^>` | back to `notes.txt`: this chord toggles between the last two buffers |
| 4 | `:vsplit` | the window divides into two side-by-side views of the same buffer |
| 5 | `<C-w>l` then `<C-^>` | move to the right-hand window and show the other buffer there |
| 6 | `<C-w>h`, `<C-w>l` | move between the two windows |
| 7 | `<C-w>o` | keep only the current window |
| 8 | `:qa!` | quit, discarding the scratch text |

**Check:** which command keeps only the lines containing `WARN`? (`:v/WARN/d`) Does closing a window with `<C-w>c` remove the buffer? (No; the buffer stays loaded and `:ls` still lists it.)

## Day 14: capstone

No new commands today. One realistic task, solved twice.

**Task.** Turn this settings file

```text
# settings
host = localhost
port = 8080
debug = true
# database
db_host = localhost
db_port = 5432
```

into this shell script:

```text
export HOST="localhost"
export PORT="8080"
export DEBUG="true"
export DB_HOST="localhost"
export DB_PORT="5432"
```

Try it yourself first, in real Vim. Then compare with the two routes below.

### Route 1: global command, substitution and a macro

| # | Keys or command | Buffer afterwards (first line shown) | Tool used |
|---|---|---|---|
| 1 | `:g/^#/d` | `host = localhost` (both comment lines are gone) | global command |
| 2 | `:%s/ = /=/` | `host=localhost` | substitution |
| 3 | `gg` | cursor on line 1 | motion |
| 4 | `qa0gUt=f=a"<Esc>A"<Esc>Iexport <Esc>jq` | `export HOST="localhost"`; cursor on line 2 | macro, recorded while editing line 1 |
| 5 | `4@a` | all five lines converted | macro with a count |

The macro in step 4, read aloud: go to the first column; upper-case up to the equals sign; move onto the equals sign and append a quote; append a quote at the end of the line; insert `export ` at the start; go down a line.

### Route 2: one substitution

| # | Command | Result |
|---|---|---|
| 1 | `:g/^#/d` | comment lines removed |
| 2 | `:%s/\v^(\w+) \= (.*)$/export \U\1\E="\2"/` | all five lines converted |

Piece by piece: `\v` very magic mode; `^(\w+)` the name at the start of the line, remembered as group 1; a space, a literal equals sign (written `\=` in this mode) and a space; `(.*)$` the rest of the line, remembered as group 2. In the replacement, `\U` switches to upper case, `\1` is the name, `\E` ends the upper-casing, and `"\2"` is the value in quotes.

### Which route is better?

Neither is "the" answer. Route 1 is built from small steps you can watch and correct, and it works even when you cannot think of the pattern. Route 2 is shorter and is a single undo step, but it has to be right in one go. An experienced user picks by feel: a pattern for regular data, a macro when each line needs several different touches, and the dot command when there are only three lines. After two weeks you have all three.

## Afterwards: keeping the skill

Skills fade without use and stick with **spaced repetition**: reviewing something after one day, then three, then a week, then two weeks, with the gaps growing each time. The small program below prints a review calendar for the fourteen drills. Change the start date to your own.

```python-run
from datetime import date, timedelta

start = date(2026, 11, 23)                 # the day you did (or will do) day 1
gaps = [1, 3, 7, 14]                       # review this many days after first doing a drill
topics = ["modes", "operators + word motions", "dot command", "f / t and change", "text objects",
          "Visual and block", "review + golf", "registers", "search + cgn", "substitution",
          "Ex ranges", "macros", "global + buffers", "capstone"]

calendar = {}
for day_number, topic in enumerate(topics, start=1):
    first = start + timedelta(days=day_number - 1)
    for gap in gaps:
        calendar.setdefault(first + timedelta(days=gap), []).append(f"day {day_number} ({topic})")

for when in sorted(calendar)[:12]:         # show the first twelve review dates
    print(when.strftime("%a %d %b"), "- redo:", "; ".join(calendar[when]))
```

Each output line is a date and the drills to repeat on it. A review takes two or three minutes per drill, because you are only confirming that the keys are still in your fingers. The first lines show week 1's drills coming round while you are still working through week 2, which is the point: old material is refreshed while new material is added.

Beyond the calendar, three habits keep you improving:

| Habit | How |
|---|---|
| notice friction | when an edit feels clumsy, finish the work, then spend two minutes finding the better command (`:help` and the cheat sheets in this track) |
| one new thing a week | pick a single command you do not use yet and use it deliberately for a week |
| use Vim mode everywhere | on this site, in your IDE, at the shell prompt: see [Vim keys everywhere](#/lesson/vim/vim-everywhere) |

> [!TIP]
> The practice problems of this track double as review. After day 8 solve `vim-registers`; after day 10, `vim-substitute` and `vim-ex-range`; after day 12, `vim-macro-expand`; after day 13, `vim-global-command` and `vim-buffer-list`. Writing a small program that predicts what a command does is the firmest test that you understand it.

> [!TIP]
> When a drill goes wrong in a way you cannot explain, do it again one key at a time and look at the screen after each key. Nearly every surprise comes from the cursor not being where you assumed.

> [!INTERVIEW]
> A favourite practical exercise in interviews for operations and data roles is "here is a messy text file; get it into this shape". The capstone is that exercise. Talk through your plan before typing ("remove the comment lines, normalise the spacing, then transform each line"), choose a tool for each step, and check the result. The interviewer is assessing the plan and the checking at least as much as the keystrokes.

## Pitfalls

- **Recording a macro with counted moves** such as `5l`. It works on the line you recorded on and fails on the others. Name the target instead: `f=`, `w`, `$`.
- **Forgetting the range.** `:s/a/b/` changes one line; `:%s/a/b/` changes the file. With `:g` it is the other way round: no range means the whole file.
- **Running a destructive command without a preview.** `:g/pattern/` on its own, or `:%s/pattern//gn`, shows what would be affected.
- **Overwriting a register that holds a macro.** `"ayy` replaces the macro stored in `a`. Keep one or two letters for macros and others for text.
- **Typing Ex commands in the browser editor and getting an error.** Some commands of real Vim are not available there. Move to real Vim for days 10, 11, 13 and 14.
- **Leaving unsaved scratch buffers and being unable to quit.** `:qa!` quits everything and discards changes. Use it only on scratch work.
- **Skipping the reviews.** Two weeks of drills without review fade in a month. The calendar takes minutes a day.
- **Measuring yourself against speed videos.** Fluency is the absence of hesitation, not a high typing rate.

## Cheat sheet: week 2

| Day | Keys to own |
|---|---|
| 8 | `"0p`, `"ay` / `"Ay` / `"ap`, `"_d`, `<C-r>0` in Insert mode, `yi"`, `ci"` |
| 9 | `/text<CR>`, `n`, `N`, `*`, `cgn…<Esc>` then `.`, the pair `n.` |
| 10 | `:s/a/b/`, `:%s/a/b/g`, flags `g` `c` `n`, groups `\1`, `\v` |
| 11 | ranges `.` `$` `%` `2,4` `'<,'>`; `:t`, `:m`, `:d`, `:normal`, `@:` |
| 12 | `qa` … `q`, `@a`, `@@`, `5@a`, `:'<,'>normal @a` |
| 13 | `:g/pat/d`, `:v/pat/d`, `:g/pat/t$`, `:ls`, `:bnext`, `<C-^>`, `:vsplit`, `<C-w>` + `h` `l` `o` |
| 14 | choosing between the dot command, a macro and a substitution |

## Summary

- Week 2 scales your editing up: registers for holding text, search and `cgn` for scattered matches, substitution and Ex commands for ranges of lines, macros for multi-step edits, and the global command for lines chosen by content.
- Registers `"0`, `"a`–`"z` and `"_` solve the "my paste was overwritten" problem.
- `*` followed by `cgn` and `.` changes every match; `n` followed by `.` lets you inspect each one first.
- `:%s/pattern/replacement/g` replaces throughout a file; groups rearrange parts of a match.
- `:t`, `:m` and `:normal` act on ranges; `@:` repeats the last Ex command.
- A macro is recorded with `q`, replayed with `@`, and made reliable by starting from a known position and moving by named targets.
- `:g` and `:v` act on lines that match or do not match a pattern.
- Keep the skill with a few minutes of spaced review and by using Vim keys in every tool.

## Glossary

| Term | Meaning |
|---|---|
| register | a named storage slot for text |
| yank | Vim's word for copy |
| put | Vim's word for paste |
| unnamed register | where text goes when no register is named; what `p` uses by default |
| black hole register | the register `_`, which discards text sent to it |
| pattern | a description of text to search for |
| match | a piece of text that fits a pattern |
| substitution | replacing matches of a pattern with other text, using `:s` |
| group | a parenthesised part of a pattern, whose text can be reused as `\1`, `\2` … |
| Ex command | a command typed after a colon |
| range | the lines an Ex command applies to |
| macro | a recorded sequence of keystrokes that can be replayed |
| global command | `:g`, which runs a command on every line matching a pattern |
| buffer | a file loaded into Vim's memory |
| window | a view onto a buffer; several can be open at once |
| spaced repetition | reviewing material at increasing intervals so that it stays in memory |
| capstone | a final exercise that combines everything learnt |

## Check yourself

```quiz
[
  {"q": "You yanked a word with yiw, then deleted a different word with diw. Which keys put the yanked word before the cursor?",
   "options": ["P", "\"0P", "\"_P", "\"1P"],
   "answer": 1,
   "explain": "The deletion replaced the unnamed register, so plain P would put the deleted word. Register 0 still holds the last yank."},
  {"q": "The cursor is on the word rate, which occurs five times in the file. Which keystrokes change every occurrence to speed with the fewest presses?",
   "options": ["*cgnspeed<Esc>....", "*cwspeed<Esc>....", "cwspeed<Esc>....", "/rate<CR>cgnspeed<Esc>"],
   "answer": 0,
   "explain": "* sets the search to the whole word, cgn changes the next match, and each dot finds and changes one more: four dots for the remaining four. With cw, dot would not move to the next match by itself."},
  {"q": "Lines look like '2026-03-09'. Which command rewrites every line as '09/03/2026'?",
   "options": ["`:%s/\\v(\\d+)-(\\d+)-(\\d+)/\\3\\/\\2\\/\\1/`", "`:%s/\\v(\\d+)-(\\d+)-(\\d+)/\\1\\/\\2\\/\\3/`", "`:s/-/\\//g`", "`:%s/\\v\\d+-\\d+-\\d+/\\3\\/\\2\\/\\1/`"],
   "answer": 0,
   "explain": "Three groups capture year, month and day; the replacement writes them in reverse with escaped slashes. The second keeps the original order, the third only swaps the separators on one line, and the fourth has no groups to refer to."},
  {"q": "Buffer lines: 'a', 'b', 'c', 'd' with the cursor on 'a'. What is the buffer after :3m0 ?",
   "options": ["c a b d", "a b d c", "a c b d", "b c a d"],
   "answer": 0,
   "explain": ":3m0 moves line 3 to below line 0, which is the top of the file."},
  {"q": "Which command puts '# ' in front of every line in the last Visual selection?",
   "options": [":'<,'>normal I# ", ":'<,'>s/#/ /", ":normal I# ", ":%normal A# "],
   "answer": 0,
   "explain": ":normal types the given keys on each line of the range; I inserts at the start of the line. Without a range only the current line is affected, and A would append at the end."},
  {"q": "A macro in register a ends with j. The file has about 60 lines to convert. What does 500@a do?",
   "options": ["Converts 500 lines and corrupts the file", "Converts lines until a command in the macro fails, typically j on the last line, then stops", "Reports an error and does nothing", "Runs for ever"],
   "answer": 1,
   "explain": "A failing command aborts the macro and cancels the remaining repeats, so an over-large count is harmless."},
  {"q": "Which command deletes every line that does NOT contain the text 'keep'?",
   "options": [":g/keep/d", ":v/keep/d", ":%s/keep//", ":g!/keep/"],
   "answer": 1,
   "explain": ":v is the inverse global command: it acts on lines without a match. :g!/keep/ with no command would only list those lines."},
  {"q": "For the capstone, when is a single substitution a better choice than a macro?",
   "options": ["Always", "When every line has the same regular shape that one pattern can describe", "When there are fewer than three lines", "When the file is read-only"],
   "answer": 1,
   "explain": "A substitution needs one pattern to fit all lines. When lines need several different touches, or you cannot think of the pattern, a macro built from small visible steps is the safer tool."}
]
```

> **Source:** practice material written for this guide. The skills drilled follow Neil, Practical Vim 2e, tips 27–41 (ch. 5–6), 60–72 (ch. 10–11) and 80–101 (ch. 13–15). Drill texts and wording are original.
