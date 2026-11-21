# QA tools

Checks used to verify the site beyond `tools/build.py` and `tools/overlap.py`. Run Python tools from
`study-guide/`. None of them change lesson content except `quiz_dollar_fix.py`.

| Tool | What it checks | How to run |
|---|---|---|
| `browser_helpers.js` | In the browser: every problem (reference passes, starter fails), every python/js/sql demo, Mermaid parsing, a render pass, a whole-site sweep | Paste into the console of the local preview (`127.0.0.1:8765`), then `await __selftest('python')`, `__fullSweep()` + `__sweepReport()`, etc. Keep the tab in front. |
| `html_demo_monkey.js` | Every `html-run` demo: uses every control, reports script errors and demos whose controls change nothing | Playwright MCP `browser_run_code_unsafe` with `filename` (the file must sit under the Prepare folder; edit `RANGE` per batch of lessons) |
| `lesson_structure.py` | Lessons missing "Before this lesson", "In plain words", "Glossary", or under 2,400 words | `python tools/qa/lesson_structure.py <track>...` |
| `quiz_dollar_scan.py` | Quiz strings whose bare `$` signs would render as KaTeX math | `python tools/qa/quiz_dollar_scan.py src [<track>...]` |
| `quiz_dollar_fix.py` | Escapes those dollars as `\\$` (JSON) | `python tools/qa/quiz_dollar_fix.py src <track>...` |
| `stage_index.py` | Stages `docs/data/index.json` with only the named tracks updated | `python tools/qa/stage_index.py <track>...` |
| `java_examples_judge.py` | Runs every Java lesson example that is followed by its stated output on the judge server | `python tools/qa/java_examples_judge.py [lesson-substring]` (needs `.judge-credentials`) |
| `java_examples_local.py` | The Java examples the judge cannot compare (stderr, args, stdin, files, hangs, fragments) on a local JDK | `python -I tools/qa/java_examples_local.py C:/Users/alvin/.jdks/jdk-21.0.13.1+2` |
| `redis_lua_test.py` | Redis lesson Lua scripts: sharded-list scripts fuzzed on fakeredis against a deque | `pip install "fakeredis[lua]"`, then `python -I tools/qa/redis_lua_test.py .` (syntax is checked with lupa's `load()`; fakeredis `SCRIPT LOAD` does not compile) |
| `anchor_check.py` | External links with `#fragments` point at anchors that exist (static fetch; recheck misses in a real browser, since many docs sites build anchors with JavaScript) | `python -I tools/qa/anchor_check.py` |

Quiz text renders `<` and `>` literally (app.js `quizText()`), but markdown still eats a backslash before
punctuation: put regexes, paths and Vim patterns in quiz options inside backticks.
