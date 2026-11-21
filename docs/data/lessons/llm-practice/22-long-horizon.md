# Long-horizon agents: compaction, notes, memory and sub-agents

> **Before this lesson:** you should know why the context window is a limited budget and how fast an
> agent fills it ([The context window as a budget](#/lesson/llm-practice/context-budget)), how tool
> calls and tool results enter the conversation
> ([Function calling](#/lesson/llm-practice/function-calling)), and what sub-agents are
> ([ReAct, planning, multi-agent systems and frameworks](#/lesson/llm-practice/agent-frameworks)).
> The code uses Python lists, dictionaries and a small class.

## In plain words

Some tasks take an agent hours: moving a large codebase to a new library, writing a deep research
report, playing a long game. Such a task produces far more text than any context window can hold. A
**long-horizon** agent is one built to keep working coherently across that much activity. This lesson
covers the four tools for it: throw away stale tool output, summarise the conversation and start
fresh (**compaction**), keep written notes outside the window (**memory**), and hand pieces of work to
helpers with their own clean windows (**sub-agents**).

An analogy: a detective on a case that lasts months. They cannot carry every page of every interview
in their head. They file old transcripts away (clearing), write a one-page case summary at the end of
each week (compaction), keep a notebook of leads, decisions and open questions (notes), and send
junior officers to check alibis, receiving short reports back (sub-agents). Any morning they can
open the notebook and pick up exactly where they left off.

Why it matters for a job: coding agents, research agents and customer-service agents all hit the
context limit in real use, and the quality of a product often comes down to how gracefully it handles
that moment. "An agent must work for six hours on one task: how do you manage its context?" is a
standard interview question.

## The scale of the problem

A task that takes an agent hours (migrating a codebase, a deep research report) produces far more
tokens than any context window holds. The previous lesson showed that a busy agent fills 200k tokens in
a couple of dozen steps. Three families of techniques let agents keep working coherently past that
limit: **compaction**, **structured note-taking** (memory outside the window) and **sub-agent
architectures**. This lesson implements the first two and analyses the third.

## 1. The cheapest trick first: clear old tool results

Most of a long transcript is **tool output** that mattered once: a file read thirty steps ago, a test
log, a search result. Once the agent has acted on it, the raw output is dead weight. **Tool-result
clearing** replaces old results with a short **placeholder** (a stand-in line that records what used to
be there) while keeping the record that the call happened:

```text
[tool result cleared to save context: read_file("src/api.py"), 6,104 tokens. Re-read if needed.]
```

Anthropic calls this one of the safest, lightest-touch forms of compaction, and the API offers it as
automatic **context editing** (clear tool uses beyond a threshold, keep the most recent N). Rules of
thumb: keep the last few results intact, never clear a result the model has not yet responded to, keep
tool *calls* (so the model knows what it already did), and clear in **batches** rather than one per
turn, because every edit to earlier history invalidates the prompt cache from that point (lesson 23).
(**Invalidating** the cache means the provider can no longer reuse its stored work for the changed part
of the prompt, so that part is processed, and billed, at full price again.)

The demo applies clearing to a short history. Each message records its role and its size in tokens:

```python-run
def clear_old_tool_results(messages, keep_last=2, min_tokens=200):
    """Replace all but the newest `keep_last` large tool results with placeholders."""
    idx = [i for i, m in enumerate(messages) if m["role"] == "tool" and m["tokens"] >= min_tokens]
    out, saved = [dict(m) for m in messages], 0
    for i in idx[:-keep_last] if keep_last else idx:
        placeholder = f"[cleared: {out[i]['name']} result, {out[i]['tokens']} tokens]"
        saved += out[i]["tokens"] - 12
        out[i].update(content=placeholder, tokens=12)
    return out, saved

history = [
    {"role": "user", "content": "Fix the failing auth test", "tokens": 9},
    {"role": "tool", "name": "read_file(auth.py)", "content": "...", "tokens": 4200},
    {"role": "tool", "name": "run_tests", "content": "...", "tokens": 1800},
    {"role": "assistant", "content": "The token check is inverted.", "tokens": 30},
    {"role": "tool", "name": "edit_file(auth.py)", "content": "ok", "tokens": 5},
    {"role": "tool", "name": "read_file(auth.py)", "content": "...", "tokens": 4250},
    {"role": "tool", "name": "run_tests", "content": "...", "tokens": 600},
]
new, saved = clear_old_tool_results(history)
for m in new:
    print(f"{m['role']:9} {m.get('name', ''):20} {m['tokens']:>5}  {m['content'][:48]}")
print("tokens saved:", saved)
```

**Reading this code line by line**

- `idx` lists the positions of tool results large enough to be worth clearing (at least 200 tokens).
  Small results such as `ok` are left alone.
- `[dict(m) for m in messages]` copies every message so the original history is untouched.
- `idx[:-keep_last]` drops the last two positions from the list, so the two most recent large results
  survive.
- Each remaining result has its content replaced by a placeholder naming the tool and its old size;
  its token count becomes 12, and `saved` adds up the difference.
- The output: the first `read_file` and `run_tests` results (4,200 and 1,800 tokens) become 12-token
  placeholders, while the newer file read and test run stay intact. The `edit_file` result, only 5
  tokens, is untouched. Total saved: 5,976 tokens, with the record of every call still visible.

## 2. Compaction

**Compaction** takes a conversation nearing the limit, **summarises** it, and starts a fresh context
seeded with the summary. Claude Code does this automatically ("auto-compact") and on demand; the
Claude API and Agent SDK offer server-side and client-side compaction.

What a good compaction summary preserves (from Anthropic's guidance and what coding harnesses do):

- the user's goal and explicit instructions/constraints, verbatim where they matter,
- architectural decisions made and why,
- the current state: what is done, what is in progress, what is next,
- unresolved bugs, open questions and failed approaches (so they are not retried),
- key identifiers: file paths, function names, ids, commands that worked,
- and then, typically, the **most recently accessed files** are re-attached in full.

What it discards: redundant tool outputs, superseded drafts, pleasantries.

**Tuning advice**: the art is choosing what to keep. Over-aggressive compaction loses subtle context
whose importance only shows later. Start by maximising **recall** (capture everything relevant from
real long **traces**, the recorded transcripts of actual agent runs), then iterate to improve
**precision** by cutting superfluous content. These are the same recall and precision as in retrieval
(lesson 8): first make sure nothing important is missing, then remove what is not needed.

The flowchart shows a typical policy: at 80 percent full, clear stale tool results first; only if that
is not enough, write a summary and rebuild the context around it.

```mermaid
flowchart LR
  A[Context at 80 percent] --> B[Clear stale tool results]
  B --> C{Still above threshold?}
  C -- no --> D[Continue]
  C -- yes --> E[LLM writes structured summary]
  E --> F[New context: system prompt + summary + recent turns + key files]
  F --> D
```

A compaction policy in code, with a mock summariser:

```python-run
def count(msgs):
    return sum(m["tokens"] for m in msgs)

def summarise(msgs):                      # stand-in for an LLM call with a structured summary prompt
    facts = [m["content"] for m in msgs if m.get("important")]
    text = "SUMMARY: " + " | ".join(facts) if facts else "SUMMARY: (earlier small talk)"
    return {"role": "user", "content": text, "tokens": 20 + 8 * len(facts)}

def compact(messages, limit, keep_recent=4, trigger=0.8):
    if count(messages) <= trigger * limit:
        return messages, False
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    old, recent = rest[:-keep_recent], rest[-keep_recent:]
    return system + [summarise(old)] + recent, True

msgs = [{"role": "system", "content": "You are a coding agent.", "tokens": 400},
        {"role": "user", "content": "Goal: migrate auth to OAuth; never touch billing/", "tokens": 30, "important": True},
        {"role": "tool", "content": "<8k tokens of file listing>", "tokens": 8000},
        {"role": "assistant", "content": "Decision: use PKCE flow, tokens in httpOnly cookies", "tokens": 60, "important": True},
        {"role": "tool", "content": "<test log>", "tokens": 5000},
        {"role": "assistant", "content": "Bug: refresh endpoint 500s when cookie missing (open)", "tokens": 40, "important": True},
        {"role": "tool", "content": "<diff>", "tokens": 3000},
        {"role": "assistant", "content": "Edited auth/refresh.py", "tokens": 20},
        {"role": "user", "content": "now add tests", "tokens": 8},
        {"role": "assistant", "content": "Writing tests/test_refresh.py", "tokens": 25}]
out, did = compact(msgs, limit=20_000)
print("compacted:", did, " tokens:", count(msgs), "->", count(out))
for m in out:
    print(f"  {m['role']:9} {m['content'][:95]}")
```

**Reading this code line by line**

- `count` adds up the token sizes of a list of messages.
- `summarise` stands in for an LLM call. It keeps the messages marked `important` (in a real system
  the model decides what matters) and joins them into one summary message whose size grows with the
  number of facts kept.
- `compact` does nothing while the history is at or below 80 percent of the limit. Otherwise it keeps
  the system prompt, summarises everything except the last `keep_recent` messages, and returns system
  prompt + summary + recent messages, plus `True` to say compaction happened.
- The history totals 16,583 tokens against a limit of 20,000; 80 percent is 16,000, so compaction
  fires. The output shows the result shrinking to 3,497 tokens: the system prompt, one summary that
  still carries the goal, the design decision and the open bug, and the last four messages.

Sharp edges:

- **Tool-call pairing**: never cut between an assistant tool call and its result; APIs reject
  **orphaned** tool results (results whose matching call has been removed). Cut on **turn boundaries**
  (between complete exchanges). The toy above keeps the last four messages without checking this; a
  real implementation must move the cut point if it would split a pair.
- **Repeated compaction** is lossy on lossy (**lossy** means some information is lost each time, like
  re-photocopying a photocopy); instructions drift. Keeping the user's original request verbatim and
  re-injecting persistent files helps.
- **Cache**: compaction resets the cached prefix; do it rarely and deliberately.

## 3. Structured note-taking: memory outside the window

Instead of trying to keep everything in context, let the agent **write notes to persistent storage**
(files or a database that survive after the conversation ends) and read them back later. Examples:

- **To-do lists**: Claude Code maintains a task list; ticking items off keeps a long task on track and
  survives compaction.
- **`NOTES.md` / progress files**: the agent records decisions, results and next steps. Anthropic's
  example is Claude playing Pokemon: over thousands of game steps it keeps tallies ("for the last
  1,234 steps I've been training my Pokemon on Route 1..."), maps of explored regions and strategy
  notes, and after a context reset reads its own notes and continues multi-hour plans.
- **Project memory files** (`CLAUDE.md`, `AGENTS.md`): human- or agent-maintained instructions and
  conventions loaded at the start of every session.
- **Memory tools**: the Claude API's memory tool gives the model file operations on a client-side
  memory directory that persists across conversations; frameworks offer similar stores.

Memory **taxonomies** (classification schemes) you will see, borrowed from psychology by the CoALA
paper and others: **working memory** (the context window), **episodic** (what happened: past
interactions and outcomes), **semantic** (facts about the user and world), **procedural** (how to do
things: skills, instructions). Implementation options range from plain files (inspectable,
**versionable** (trackable with git), surprisingly strong) to vector stores (lesson 9) and knowledge
graphs (lesson 12), offered by memory products such as Mem0, Zep and Letta (the successor of the
MemGPT research project, whose agent edits its own memory blocks).

Design questions for any memory system:

1. **What gets written?** Decisions, preferences, verified facts, not raw transcripts. Poisoned or
   wrong memories persist, so validate and allow correction.
2. **When is it read?** Always-loaded (small, high value) versus retrieved on demand.
3. **How is it kept fresh?** Timestamps, dedupe, consolidation, expiry; contradictory memories are
   context clash waiting to happen.
4. **Whose is it?** Per-user isolation, privacy, the ability to inspect and delete.

```python-run
import json

class Notes:
    """A tiny file-like memory: the agent writes structured notes and reloads them after a reset."""
    def __init__(self): self.store = {}
    def write(self, key, value): self.store[key] = value
    def render(self):
        return "\n".join(f"## {k}\n{json.dumps(v, indent=1) if not isinstance(v, str) else v}"
                         for k, v in self.store.items())

notes = Notes()
notes.write("goal", "Migrate auth to OAuth 2.1 with PKCE. Do not modify billing/.")
notes.write("todo", [{"task": "refresh endpoint", "done": True}, {"task": "tests for refresh", "done": False},
                     {"task": "update docs", "done": False}])
notes.write("decisions", ["httpOnly cookies for tokens", "PKCE for all clients"])
notes.write("known issues", ["refresh 500s when cookie missing"])

fresh_context = "SYSTEM: You are a coding agent. Read your notes first.\n\n" + notes.render()
print(fresh_context)
print("\ncontext after reset:", len(fresh_context.split()), "words instead of the full transcript")
```

How it works: `Notes` keeps a dictionary of named sections. `write` stores or replaces a section, and
`render` turns all sections into Markdown, printing strings as they are and lists or dictionaries as
indented JSON. The agent records its goal, its to-do list with done flags, its decisions and a known
bug. The printed "fresh context" is what a new context window would start with after a reset: 71
words that hold everything needed to continue, instead of a transcript of tens of thousands of tokens.

For work spanning **multiple context windows**, Anthropic's guidance for recent models is to treat the
first window differently (set up a framework: tests, setup scripts, a to-do file), have the model track
state in **structured files** (e.g. `tests.json` for test status) plus free-form progress notes, use
**git** as a log and checkpoint mechanism, and note that starting a fresh context that reads those
files can work better than automatic compaction.

## 4. Sub-agent architectures

Rather than one agent holding everything, a **lead agent** delegates focused tasks to **sub-agents**,
each with its **own clean context window**. A sub-agent may burn tens of thousands of tokens exploring
(reading files, running searches), but returns only a **condensed, distilled summary**, often 1,000 to
2,000 tokens. The lead agent's context holds the plan and the distilled results, not the exploration.

```python-run
subtasks = {"search auth code paths": 48_000, "survey OAuth libraries": 61_000, "audit existing tests": 37_000}
summary_tokens = 1_500
single_agent = sum(subtasks.values())
lead_context = len(subtasks) * summary_tokens
print(f"single agent context consumed by exploration: {single_agent:,} tokens")
print(f"lead agent context with sub-agents          : {lead_context:,} tokens")
print(f"total tokens billed with sub-agents          : {single_agent + lead_context:,} (more spend, cleaner contexts)")
```

The arithmetic: three explorations of 37,000 to 61,000 tokens each would put 146,000 tokens into a
single agent's window. With sub-agents, the lead receives three 1,500-token summaries, 4,500 tokens in
all. The bill goes *up* slightly (150,500 tokens in total, because the summaries are extra), but the
lead's window stays almost empty and focused.

This is **separation of concerns** (each part of a system handles one job and hides its details from
the others): detailed search context stays isolated in sub-agents while the lead
focuses on synthesis. Benefits: clean contexts, parallelism, specialisation. Costs: more total tokens,
coordination overhead, and information loss at the hand-off (the sub-agent's summary is all the lead
knows). Good delegation briefs specify the objective, the expected output format, which tools and
sources to use, and clear task boundaries; sub-agents can also write detailed artefacts to files and
return references.

## 5. Choosing among them

| technique | best when |
|---|---|
| tool-result clearing | always on; long tool-heavy sessions |
| compaction | long, conversational back-and-forth that needs continuity |
| structured notes / memory | iterative development with clear milestones; work spanning sessions |
| sub-agents | complex research or analysis where parallel exploration pays off |

They combine: a lead agent with a to-do file, sub-agents for exploration, tool-result clearing
throughout and compaction as the last resort. And keep the meta-advice in mind: as models improve they
need less **scaffolding** (the supporting code and structure built around a model), so "do the simplest
thing that works".

> [!INTERVIEW]
> **"An agent must work for six hours on one task. How do you manage its context?"** Measure usage by
> category; clear stale tool results first; compact near a threshold with a structured summary that
> keeps goals, decisions, state, open bugs and identifiers, cutting only on turn boundaries; keep
> durable state outside the window (to-do list, progress notes, tests status, git commits) so a fresh
> window can resume; delegate exploration to sub-agents that return 1-2k-token summaries; order context
> for prompt caching and batch edits to preserve it.

## Summary

- Clear old tool results first: cheap, safe, large savings.
- Compaction summarises and restarts; tune for recall, then precision; respect tool-call pairing.
- Notes and memory move state outside the window: to-do lists, progress files, memory tools.
- Sub-agents explore in isolated contexts and return condensed summaries; more tokens overall, cleaner
  lead context.
- Combine techniques according to task shape, and prefer the simplest working design.

## Glossary

- **Long-horizon agent**: an agent built to work coherently over many more tokens than its window
  holds.
- **Tool-result clearing**: replacing old tool output with short placeholders while keeping the calls.
- **Placeholder**: a stand-in line recording what used to be in the context.
- **Context editing**: the API feature that clears old tool results automatically.
- **Cache invalidation**: an edit to earlier history that stops the provider reusing cached work.
- **Compaction**: summarising a long conversation and restarting from the summary.
- **Trace**: the recorded transcript of a real agent run.
- **Turn boundary / orphaned tool result**: a point between complete exchanges / a result whose call
  was removed.
- **Lossy**: losing some information each time it is applied.
- **Structured note-taking**: the agent writes notes, to-do lists and progress files to persistent
  storage.
- **Persistent storage**: files or databases that outlive the conversation.
- **Project memory file**: a file such as `CLAUDE.md` loaded at the start of every session.
- **Memory tool**: an API tool giving the model file operations on a memory directory.
- **Working / episodic / semantic / procedural memory**: the context / past events / facts / skills.
- **Sub-agent**: a helper agent with its own clean context that returns a condensed summary.
- **Separation of concerns**: each part handles one job and hides its details from the others.
- **Scaffolding**: the supporting code and structure built around a model.

## Check yourself

```quiz
[
  {"q": "Which is typically the safest first step when context fills up?",
   "options": ["Clearing old tool results while keeping the record of the calls", "Deleting the system prompt", "Dropping the user's original request", "Switching models"], "answer": 0,
   "explain": "Stale raw tool output is the largest and least valuable part of long transcripts."},
  {"q": "What should a compaction summary definitely preserve?",
   "options": ["Goals, decisions, current state, unresolved issues and key identifiers", "Every tool output verbatim", "Only the last message", "Greetings and acknowledgements"], "answer": 0,
   "explain": "Those are what the agent needs to continue coherently; redundant outputs can go."},
  {"q": "When tuning a compaction prompt, what does Anthropic suggest optimising first?",
   "options": ["Recall, then precision", "Precision, then recall", "Latency only", "Summary length only"], "answer": 0,
   "explain": "First make sure nothing important is lost on real traces, then trim the excess."},
  {"q": "Why must compaction not cut between a tool call and its result?",
   "options": ["APIs require each tool result to follow its tool call; orphans are invalid and confusing", "It wastes tokens", "It changes the tokenizer", "It disables caching permanently"], "answer": 0,
   "explain": "Tool use and tool result form a pair; truncate on turn boundaries."},
  {"q": "What do sub-agents typically return to the lead agent?",
   "options": ["A condensed summary, often 1,000 to 2,000 tokens", "Their entire transcript", "Nothing", "Raw embeddings"], "answer": 0,
   "explain": "The lead's context stays clean; the exploration stays in the sub-agent's window."},
  {"q": "Which technique best suits iterative development with clear milestones across sessions?",
   "options": ["Structured note-taking and memory files", "Voting", "Higher temperature", "Larger batch size"], "answer": 0,
   "explain": "Persistent notes let a fresh context pick up the state of the work."},
  {"q": "What is a key risk of persistent agent memory?",
   "options": ["Wrong or malicious entries persist and keep influencing future sessions", "It always exceeds the context window", "It cannot store text", "It disables tools"], "answer": 0,
   "explain": "Memory needs validation, freshness management and the ability to inspect and delete."}
]
```

> **Source:** Anthropic Engineering, "Effective context engineering for AI agents" (2025) and "How we
> built our multi-agent research system" (2025); Anthropic docs on context editing, compaction, the
> memory tool and multi-context-window workflows (https://docs.claude.com); Sumers et al., "Cognitive
> Architectures for Language Agents" (CoALA, 2023); Packer et al., "MemGPT" (2023); Huyen, *AI
> Engineering*, ch. 6 (memory).
