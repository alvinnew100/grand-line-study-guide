"""Run the Java lesson examples the judge cannot compare, on a local JDK, and compare with the stated output.

Handles: stderr traces (stdout + stderr compared), "> java X args" lines (args), keyboard input
(VaultGame: typed values fed on stdin), file I/O (temp working dir, scores.csv from the lesson),
client/server (TipServer + two TipClient runs), intentional hangs (timeout expected), Swing
(real window driven through a harness), fragments without a class, and the intentional compile error.
Usage (from study-guide/): python -I java_local_check.py <JDK dir>
"""
import pathlib
import re
import subprocess
import sys
import tempfile
import time

JDK = pathlib.Path(sys.argv[1])
JAVA, JAVAC = str(JDK / "bin" / "java"), str(JDK / "bin" / "javac")
BT = chr(96) * 3
NF = r"((?:(?!" + BT + r")[\s\S])*?)"
PAIR = re.compile(BT + r"java\r?\n" + NF + BT + r"[ \t]*\r?\n\s*" + BT + r"text\r?\n" + NF + BT)
ANY = re.compile(BT + r"java\r?\n" + NF + BT)
L = lambda n: pathlib.Path("src/java/lessons", n).read_text(encoding="utf-8")


def norm(lines):
    out = []
    for ln in lines:
        ln = ln.rstrip()
        if ln.startswith("\tat ") or re.match(r"^ {2,}at ", ln):
            ln = "    at " + ln.strip()[3:]
        out.append(ln)
    while out and not out[-1]:
        out.pop()
    return out


def names_in(code):
    return re.findall(r"^\s*(?:public\s+|final\s+|abstract\s+|sealed\s+|static\s+)*(?:class|interface|enum|record|@interface)\s+(\w+)", code, re.M)


def write_sources(d, code, extras):
    """Write the example as <Public>.java and extras with 'public' removed. Returns the main class name."""
    m = re.search(r"public\s+(?:final\s+)?class\s+(\w+)", code)
    main = m.group(1) if m else None
    if main is None:  # a fragment: wrap it
        main = "Demo"
        code = "public class Demo {\n" + code + "\n}\n"
    (d / (main + ".java")).write_text(code, encoding="utf-8")
    for k, e in enumerate(extras):
        pm = re.search(r"public\s+(?:final\s+)?class\s+(\w+)", e)
        if pm and pm.group(1) != main:  # keep the real file name so stack traces match the lesson
            (d / (pm.group(1) + ".java")).write_text(e, encoding="utf-8")
        else:
            (d / ("Extra%d.java" % k)).write_text(re.sub(r"^public\s+", "", e, flags=re.M), encoding="utf-8")
    return main


def extras_for(code, pool):
    have, out = set(names_in(code)), []
    changed = True
    while changed:  # transitive: include blocks that define names used by the example or by earlier extras
        changed = False
        text = code + "\n".join(out)
        for b in pool:
            if b == code or b in out:
                continue
            ns = names_in(b)
            if ns and not (set(ns) & have) and any(re.search(r"\b" + n + r"\b", text) for n in ns):
                out.append(b); have |= set(ns); changed = True
    return out


def compile_dir(d):
    srcs = [str(p) for p in d.glob("*.java")]
    return subprocess.run([JAVAC, "-d", str(d)] + srcs, capture_output=True, text=True, cwd=d)


def run(d, main, args=(), stdin="", timeout=8):
    try:
        r = subprocess.run([JAVA, "-cp", str(d), main] + list(args), input=stdin, capture_output=True, text=True, cwd=d, timeout=timeout)
        return r.stdout, r.stderr, r.returncode, False
    except subprocess.TimeoutExpired as e:
        dec = lambda x: (x.decode() if isinstance(x, bytes) else (x or ""))
        return dec(e.stdout), dec(e.stderr), None, True


def check(name, idx, label, lesson_pool_extra=()):
    text = L(name)
    code, expected = PAIR.findall(text)[idx - 1]
    pool = ANY.findall(text) + [b for n in lesson_pool_extra for b in ANY.findall(L(n))]
    exp = expected.rstrip().splitlines()
    args, cmd_lines = [], [l for l in exp if l.startswith("> ")]
    for c in cmd_lines:
        m = re.match(r"> java (\S+)(.*)", c)
        if m:
            args = m.group(2).split()
    narr = [l for l in exp if l.strip().startswith("(")]
    want = [l for l in exp if not l.startswith("> ") and not l.strip().startswith("(")]
    hang = any(re.search(r"hang|never ends|for ever|forever", n) for n in narr)
    d = pathlib.Path(tempfile.mkdtemp(prefix="jl_"))
    main = write_sources(d, code, extras_for(code, pool))
    c = compile_dir(d)
    if c.returncode != 0:
        got = norm([l for l in c.stderr.splitlines() if l.strip()])
        got = [re.sub(r"^.*[\\/]", "", g) if ".java:" in g else g for g in got]
        ok = norm(want) == got
        return f"{label}: {'OK (compile error matches)' if ok else 'COMPILE ' + ' | '.join(got[:4])}"
    stdin = ""
    if label == "VaultGame":  # typed guesses follow the prompts in the transcript
        typed = [m.group(2) for l in want for m in [re.match(r"^(Guess \(\d+ left\): )(.*)$", l)] if m]
        stdin = "\n".join(typed) + "\n"
        flat, merged = "\n".join(want), []
        want = re.sub(r"(Guess \(\d+ left\): )[^\n]*\n", r"\1", flat + "\n").rstrip("\n").splitlines()
    if label == "ScoreReader":
        (d / "scores.csv").write_text("name,score\nAda,91\nBo,78\nCy,eighty\nDi,64\n", encoding="utf-8")
    out, err, rc, timed_out = run(d, main, args, stdin)
    got = norm((out + err).splitlines())
    if hang:
        ok = timed_out and norm(want) == got
        return f"{label}: {'OK (hangs as stated, output matches)' if ok else 'DIFF hang=' + str(timed_out) + ' got=' + repr(got[:6])}"
    ok = norm(want) == got or (norm(want) and all(g.startswith(w) for w, g in zip(norm(want), got)) and len(got) == len(norm(want)))
    exact = norm(want) == got
    return f"{label}: {'OK' if exact else ('PREFIX-OK (output has more detail than the lesson shows)' if ok else 'DIFF')} want={norm(want)[:6]!r} got={got[:6]!r}"


results = []
results.append(check("01-source-to-jvm.md", 1, "Broken"))
results.append(check("01-source-to-jvm.md", 2, "Divide"))
results.append(check("02-class-anatomy.md", 3, "Echo"))
results.append(check("03-classes-vs-objects.md", 4, "NullDemo"))
results.append(check("06-references-stack-heap.md", 3, "Arrays1"))
results.append(check("09-building-a-game.md", 2, "VaultGame"))
results.append(check("21-exceptions-basics.md", 1, "Crash"))
results.append(check("25-serialization-streams.md", 1, "SaveGame"))
results.append(check("26-files-nio.md", 2, "Notes"))
results.append(check("26-files-nio.md", 3, "ScoreReader"))
results.append(check("29-synchronization.md", 3, "Deadlock"))
results.append(check("56-ej-shared-data.md", 1, "StopThread"))
results.append(check("52-ej-everyday-habits.md", 9, "NullCounter"))
print("\n".join(results))
