# The dot command: one key that replays your last change

> **Before this lesson:** nothing. This is the first lesson of the track and starts from zero. You only need to be able to type and to open this site's code editor.

## In plain words

**Vim** is a text editor: a program for writing and changing text, most often program code and configuration files. It runs in a terminal window (the text-only window where you type commands), it is installed on almost every server and developer machine, and its way of editing is offered as an option inside most other editors too.

What makes Vim different is that it is **modal**. A *mode* is a state in which the keys have a particular job.

- In **Insert mode** the keys type text, as in any editor.
- In **Normal mode** the keys are *commands*: `x` deletes a character, `dd` deletes a line, `w` jumps to the next word. Vim starts in Normal mode, and you return to it by pressing the Escape key, written `<Esc>`.

An everyday comparison: a pocket calculator has digit keys and operation keys. Vim uses the same keyboard for both by switching between "typing" and "commanding". A second comparison explains this lesson's subject. A washing machine has a button that repeats the last programme you ran; you set it up once and afterwards press one button. Vim has such a button for editing. It is the full stop key, `.`, known as the **dot command**: it repeats the last change you made.

Why it matters for a job: most editing is repetitive. Add the same thing to ten lines, rename a word in six places, remove a prefix from a list. If repeating costs one key press, tedious work becomes quick and, more important, consistent, because line ten is treated exactly like line one.

### A survival kit, before anything else

| You want to | Press |
|---|---|
| start typing text | `i` (you are now in Insert mode) |
| stop typing and give commands again | `<Esc>` (back in Normal mode) |
| undo the last change | `u` |
| move left, down, up, right | `h`, `j`, `k`, `l` |
| save the file (in a real Vim) | `:w` and then Enter |
| quit (in a real Vim) | `:q` and then Enter; `:q!` to quit without saving |

Two more words used throughout the track. The **cursor** is the marker showing where you are in the text. The **buffer** is the text you are editing, as held in the editor's memory.

Most editors make you choose between doing a small edit by hand and reaching for heavy machinery such as find-and-replace or multiple cursors. Vim has something in between that turns out to cover a surprising share of everyday editing: the `.` key in Normal mode. It replays **the last change you made**, whatever that change was, at wherever the cursor is now.

That single sentence is the foundation of the whole Vim style. People who are fast in Vim are rarely fast typists; they are people who have learnt to shape each edit so that it can be replayed, and to shape each movement so that getting to the next place costs one key. This lesson is about the first half of that habit: what a "change" is, how to make changes that are worth repeating, and how to read the before/after tables used throughout this track.

> [!TIP]
> This site's code editor has a **Vim mode** switch in the ⚙ settings menu. Turn it on now. Every table in these lessons can be typed into any editor pane on the site, and typing them is worth ten readings.

## How to read the examples

Every worked example in this track has three columns:

- **Before**: the buffer, with the cursor shown as a bracket around one character, like `to[t]al`.
- **Keys**: exactly what to type. `<Esc>` is the Escape key, `<CR>` is Enter, `<C-r>` is Ctrl-R, and `␣` stands for a space where a space would otherwise be invisible.
- **After**: the buffer and cursor once the keys have been typed.

In Normal mode the cursor always sits *on* a character, never between two. That is why a bracket around a character is an honest picture.

## What counts as "the last change"

Vim keeps a small record of the most recent command that modified the buffer. The record is replaced each time you make a new change, and `.` re-executes it. The unit is larger than a keystroke and smaller than a script:

| You typed | What Vim stored as one change |
|---|---|
| `x` | delete the character under the cursor |
| `dd` | delete one line |
| `dw` | delete from the cursor to the start of the next word |
| `>G` | indent from this line to the end of the file |
| `ciwcount<Esc>` | replace the word under the cursor with `count` |
| `A;<Esc>` | append a semicolon at the end of the line |
| `otry:<Esc>` | open a line below and type `try:` |
| `3J` | join three lines |

Two rules explain the whole table.

1. **A Normal-mode command that edits text is one change.** That includes an operator together with its motion (`dw`, `>G`, `gUiw`), so the motion is replayed relative to the new cursor position.
2. **An Insert-mode session is one change.** Everything from the key that entered Insert mode (`i`, `a`, `A`, `o`, `c{motion}`, `s` …) through the `<Esc>` that left it is recorded together: the entry command *and* the text typed.

What is **not** a change: moving the cursor, searching, scrolling, yanking with `y` (in Vim's default configuration), switching windows, and Ex commands typed after a colon. Those leave the record untouched, which is exactly what makes the dot command useful: you can move as much as you like between repeats.

```mermaid
flowchart LR
    A[Make a change] --> B[Vim stores it]
    B --> C[Move the cursor]
    C --> D[Press dot]
    D --> E[Same change at the new place]
    E --> C
```

## Worked examples

### 1. Deleting characters

| Before | Keys | After |
|---|---|---|
| `[#]## Release notes` | `x` | `[#]# Release notes` |
| `[#]# Release notes` | `.` | `[#] Release notes` |
| `[#] Release notes` | `.` | `[ ]Release notes` |

Nothing clever yet: `.` replays `x`. Note that the cursor did not have to move, because deleting pulls the next character under it.

### 2. Deleting lines

| Before | Keys | After |
|---|---|---|
| `[d]ebug = true`<br>`trace = true`<br>`port = 8080` | `dd` | `[t]race = true`<br>`port = 8080` |
| `[t]race = true`<br>`port = 8080` | `.` | `[p]ort = 8080` |

### 3. Indenting a block, then nudging it again

Suppose the cursor is on the first of four lines that should be nested one level deeper, and those four lines run to the end of the file.

| Before | Keys | After |
|---|---|---|
| `[n]ame: api`<br>`image: api:2`<br>`ports:`<br>`- 8080` | `>G` | `    [n]ame: api`<br>`    image: api:2`<br>`    ports:`<br>`    - 8080` |
| (same, cursor on line 3) | `jj.` | lines 3 and 4 gain another level |

`>G` means "shift right from here to the last line". When it is replayed from line 3, `G` is evaluated again from line 3, so only the last two lines move. The stored change is the *command*, not the list of lines it touched the first time.

### 4. Appending to many lines

Three statements are missing their terminators.

| Before | Keys | After |
|---|---|---|
| `[l]et host = "db"`<br>`let port = 5432`<br>`let pool = 8` | `A;<Esc>` | `let host = "db"[;]`<br>`let port = 5432`<br>`let pool = 8` |
| | `j.` | `let host = "db";`<br>`let port = 5432[;]`<br>`let pool = 8` |
| | `j.` | `let host = "db";`<br>`let port = 5432;`<br>`let pool = 8[;]` |

The first line costs three keystrokes (`A`, `;`, `<Esc>`). Every further line costs two: `j` to move and `.` to act. It does not matter that the lines have different lengths, because `A` means "go to the end of the line, then append": the movement is *inside* the change.

Compare the alternative `$a;<Esc>`. It produces the same text on the first line, but now the stored change is only `a;<Esc>`, "append here". On the next line you would have to type `j$.`, three keys instead of two, forever. Choosing `A` over `$a` is the smallest possible example of **composing a change so that it carries its own positioning**.

### 5. Spacing out punctuation

A colour is written without spaces after the commas and the style guide wants them.

| Before | Keys | After |
|---|---|---|
| `[r]gb(12,200,7)` | `f,` | `rgb(12[,]200,7)` |
| `rgb(12[,]200,7)` | `a␣<Esc>` | `rgb(12,[ ]200,7)` |
| `rgb(12,[ ]200,7)` | `;` | `rgb(12, 200[,]7)` |
| `rgb(12, 200[,]7)` | `.` | `rgb(12, 200,[ ]7)` |

`f,` looks along the line for a comma; `;` repeats that look-up. So after the set-up, each further comma is `;.`: one key to travel, one key to act.

### 6. Replacing a word in several places

A variable called `tmp` should be called `row` in three assignments.

| Before | Keys | After |
|---|---|---|
| `[t]mp = fetch()`<br>`tmp.validate()`<br>`save(tmp)` | `cwrow<Esc>` | `ro[w] = fetch()`<br>`tmp.validate()`<br>`save(tmp)` |
| | `+` | cursor on the `t` of line 2 |
| | `.` | `row = fetch()`<br>`ro[w].validate()`<br>`save(tmp)` |
| | `+ft.` | `row = fetch()`<br>`row.validate()`<br>`save(ro[w])` |

`+` moves to the first non-blank character of the next line, so it is a one-key way to reach the word when it starts the line. On the third line the word is further in, so a small extra motion (`ft`) is needed. The change itself, `cwrow<Esc>`, is identical every time.

### 7. Deleting a whole word from the middle of it

| Before | Keys | After |
|---|---|---|
| `retry the the reque[s]t now` | `daw` | `retry the the [n]ow` |
| `retry the [t]he now` (after moving back) | `.` | `retry the [n]ow` |

`daw` is "delete a word": it removes the word under the cursor *and* one neighbouring space, from any starting position inside the word. Because it does not depend on where in the word you are, it replays cleanly wherever you land.

## The compound commands exist for the dot command

Several single keys are shorthand for two-step sequences. They look like minor conveniences until you notice what they do to the stored change.

| Shorthand | Long form | What it means |
|---|---|---|
| `A` | `$a` | append at end of line |
| `I` | `^i` | insert at first non-blank |
| `C` | `c$` | change to end of line |
| `D` | `d$` | delete to end of line |
| `s` | `cl` | replace one character and stay in Insert mode |
| `S` | `^C` (or `cc`) | replace the whole line's text |
| `o` | `A<CR>` | open a line below |
| `O` | `ko` | open a line above |
| `x` | `dl` | delete the character under the cursor |
| `X` | `dh` | delete the character before the cursor |

With the long forms, the leading motion (`$`, `^`, `k`) happens *before* the change begins and is not recorded. With the shorthand it is part of the change. So the shorthand is not only shorter to type once: it is the version that survives repetition.

## A mental model in code

The record behaves like a stored function that takes the current cursor as its argument. The toy model below keeps a line of text and a cursor column, and supports three changes. Run it, then change the sequence of calls.

```python-run
class Editor:
    def __init__(self, text):
        self.text, self.col, self.last = text, 0, None

    def show(self, label):
        t, c = self.text, self.col
        print(f"{label:<14}", t[:c] + "[" + t[c:c+1] + "]" + t[c+1:])

    def do(self, change):          # run a change and remember it
        self.last = change
        change(self)

    def dot(self):                 # replay whatever was remembered
        if self.last:
            self.last(self)

def x(ed):                         # delete character under cursor
    ed.text = ed.text[:ed.col] + ed.text[ed.col+1:]

def append_at_end(s):              # A{s}<Esc>
    def change(ed):
        ed.text += s
        ed.col = len(ed.text) - 1
    return change

def find(ed, ch):                  # f{ch}: a motion, NOT remembered
    i = ed.text.find(ch, ed.col + 1)
    if i >= 0:
        ed.col = i

ed = Editor("a,b,c")
ed.show("start")
find(ed, ","); ed.do(x); ed.show("f, then x")
find(ed, ","); ed.dot(); ed.show("f, then .")
ed.do(append_at_end(";")); ed.show("A;<Esc>")
ed.dot(); ed.show(".")
```

Notice that `find` never touches `ed.last`. Motions are free: you can make as many as you need between repeats.

## Why it works: the grammar underneath

A Normal-mode edit is a small sentence, **operator + motion** (or operator + text object): `d` + `w`, `c` + `iw`, `>` + `G`. Vim stores the sentence, not its effect. Replaying the sentence at a new cursor position re-evaluates the motion from there. That is why `dw` deletes a *different* word each time, and why `>G` covers a different number of lines when replayed further down.

Insert-mode sessions fit the same scheme. `cwrow<Esc>` is the operator `c`, the motion `w`, and an argument: the typed text. All three are stored.

The practical consequence is a design rule you can apply to every edit:

> Prefer the form of a command whose meaning does not depend on exactly where the cursor is.

`daw` beats `bdw`. `A` beats `$a`. `ciw` beats `bcw`. `C` beats `d$a`. In each pair the first form makes one change that is complete in itself; the second makes a motion (lost) followed by a smaller change (kept).

> [!INTERVIEW]
> A common pairing-interview observation: candidates who use Vim well narrate edits as phrases, "change inner word", "delete around parentheses", rather than as key sequences. If you are asked why you use Vim keys, "edits are composable and repeatable" plus a ten-second demo of `ciw` followed by `.` on another word is a stronger answer than anything about speed.

## Counts and the dot command

A count before `.` **replaces** the count of the stored change rather than multiplying it.

| Stored change | You type | Result |
|---|---|---|
| `dd` | `3.` | deletes 3 lines |
| `2dd` | `.` | deletes 2 lines |
| `2dd` | `3.` | deletes 3 lines (not 6), and the stored count is now 3 |
| `x` | `5.` | deletes 5 characters |

For an Insert-mode change, a count repeats the typed text: after `a-<Esc>`, typing `10.` appends ten more dashes at the cursor.

## Pitfalls

**Motions made with arrow keys inside Insert mode split the change.** If you type `Aone`, press the left arrow, then type `X<Esc>`, the dot command replays only the portion typed after the arrow key. Leave Insert mode to move. This is one of several reasons experienced users stay off the arrow keys.

**The cursor's resting place matters.** After `cwrow<Esc>` the cursor is on the last typed letter, not at the start of the word. If your next target is "the same column on the next line", `j` alone will not put you at the start of the word; `+`, `j0` or `j^` will.

**`cw` is position dependent; `ciw` is not.** `cw` changes from the cursor to the end of the word. If you land in the middle of the next target, `.` will replace only its tail. When you cannot guarantee landing on the first letter, build the change with `ciw`.

**`.` does not repeat Ex commands or macros.** After `:s/a/b/`, use `&` to repeat the substitution on another line, or `@:` to repeat the last Ex command of any kind. After `@q`, use `@@`.

**`u` and `.` are partners.** If a repeat lands on the wrong text, `u` undoes only that repetition and leaves the stored change intact, so you can move and press `.` again.

**Yank is not a change.** After `yiw` the dot command still replays whatever edit came before. (Vim has an option flag that makes yanks repeatable, but it is off by default and best left off.)

## Cheat sheet

| Goal | Keys | Repeat with |
|---|---|---|
| Append text at end of line | `A{text}<Esc>` | `j.` |
| Insert text at start of line | `I{text}<Esc>` | `j.` |
| Replace word under cursor | `ciw{text}<Esc>` | move, then `.` |
| Delete word under cursor with its space | `daw` | move, then `.` |
| Delete to end of line | `D` | `j.` (after positioning) |
| Replace rest of line | `C{text}<Esc>` | move, then `.` |
| Indent line | `>>` | `j.` |
| Delete a line | `dd` | `.` |
| Toggle case of a word | `g~iw` | move, then `.` |
| Repeat with a new count | `{n}.` | |
| Undo a bad repeat | `u` | |

## Summary

- `.` replays the last change: one Normal-mode editing command, or one complete Insert-mode session from entry key to `<Esc>`.
- Motions, searches and yanks do not disturb the stored change, so you can travel freely between repeats.
- The stored thing is a command, re-evaluated at the new cursor position, not a recording of what was affected.
- Compound keys such as `A`, `I`, `C`, `o` fold a movement into the change. Prefer them, and prefer text objects such as `iw` and `aw`, because they make changes that are independent of the exact cursor position.
- A count typed before `.` replaces the original count.
- When a repeat goes wrong, `u` reverses it without forgetting the change.

## Glossary

| Term | Meaning |
|---|---|
| Vim | a modal text editor found on nearly every developer machine and server |
| mode | a state of the editor in which keys have a particular meaning |
| Normal mode | the mode in which keys are commands; Vim's starting and resting state |
| Insert mode | the mode in which keys type text |
| cursor | the marker showing your position in the text |
| buffer | the text being edited, as held in the editor's memory |
| change | one editing action: a Normal-mode editing command, or everything typed between entering and leaving Insert mode |
| dot command | the `.` key, which repeats the last change |
| motion | a command that moves the cursor, such as `w` (next word) or `j` (down) |
| operator | a command that acts on text, such as `d` (delete) or `c` (change) |
| count | a number typed before a command to repeat or extend it |
| undo | reversing the last change, with `u` |
| Ex command | a command typed after pressing `:` |

## Check yourself

```quiz
[
  {"q": "The buffer has three lines that each need a trailing comma. The cursor is on line 1. Which sequence does the job in the fewest keystrokes?",
   "options": ["$a,<Esc> then j. twice", "A,<Esc> then j. twice", "A,<Esc> then j$. twice", "i,<Esc> then j. twice"],
   "answer": 1,
   "explain": "A folds 'go to end of line' into the change, so j. is enough on the following lines. With $a the motion $ is not stored and would have to be retyped each time."},
  {"q": "You type dw and then move down a line and press dot. What happens?",
   "options": ["The same word that was deleted before is pasted back", "The text from the new cursor position to the start of the next word is deleted", "Nothing, because the cursor moved", "The whole line is deleted"],
   "answer": 1,
   "explain": "The stored change is the command dw. Replaying it evaluates the w motion from the current cursor position."},
  {"q": "Which of these does NOT replace the stored change?",
   "options": ["x", "ciwnew<Esc>", "f, followed by ;", ">>"],
   "answer": 2,
   "explain": "f and ; are motions. Only commands that modify the buffer update what dot will replay."},
  {"q": "The stored change is 2dd. What does 3. do?",
   "options": ["Deletes 6 lines", "Deletes 5 lines", "Deletes 3 lines", "Deletes 2 lines three times"],
   "answer": 2,
   "explain": "A count given to dot replaces the original count; it does not multiply it."},
  {"q": "Line: 'max(a,b,c)' with the cursor on m. Which keystrokes produce 'max(a, b, c)'?",
   "options": ["f,a <Esc>;.", "f,i <Esc>;.", "f,a <Esc>..", "t,a <Esc>;."],
   "answer": 0,
   "explain": "f, lands on the first comma, 'a space Esc' appends a space after it, ; jumps to the next comma and dot repeats the append. With i the space would go before the comma; with t the cursor stops before the comma, so the space also lands before it."},
  {"q": "Why is daw usually a better repeatable change than bdw?",
   "options": ["It is fewer keystrokes in every case", "b is not allowed before an operator", "The whole deletion is one stored change that works from anywhere inside a word; with bdw the b is a separate motion that dot does not replay", "daw does not use a register"],
   "answer": 2,
   "explain": "Dot would replay only dw, which deletes from the cursor forward. daw carries its own positioning."},
  {"q": "You typed :s/foo/bar/ on one line and want to repeat that substitution on the line below. Which works?",
   "options": ["j.", "j&", "ju", "j;"],
   "answer": 1,
   "explain": "Dot does not repeat Ex commands. & repeats the last substitution on the current line (and @: repeats the last Ex command in general)."},
  {"q": "After cwrow<Esc> on the first word of a line, which single key best positions the cursor for dot on the first word of the next line?",
   "options": ["j", "+", "w", "$"],
   "answer": 1,
   "explain": "After Esc the cursor rests on the last typed letter, so j would land mid-word. + goes to the first non-blank of the next line."}
]
```

> **Source:** Neil, Practical Vim 2e, tips 1–3 (ch. 1, "The Vim Way"). Examples and wording are original.
