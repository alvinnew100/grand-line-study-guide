# Designing tools for agents and prompt caching

Two levers decide whether an agent is effective *and* affordable. **Tools** define what the agent can
perceive and do, and every tool definition and tool result is context. **Prompt caching** decides
whether you pay full price to re-read that context on every one of the hundreds of requests in an
agent loop. Both reward the same discipline: stable, compact, well-structured context.

## 1. Tools are a contract with a non-deterministic caller

A traditional API is a contract between deterministic programs. A tool is a contract between a
deterministic system and an agent that may call it in unexpected ways, misunderstand it, or never call
it. Anthropic's post *Writing effective tools for agents* recommends a loop: prototype, **evaluate with
real agents on realistic tasks**, read the transcripts, and refine (even letting an agent help rewrite
the tools from those transcripts). Its principles:

### Choose the right tools (fewer, higher-level)

More tools do not mean better outcomes. Do not wrap each API endpoint; build tools around **tasks**:

| instead of | build |
|---|---|
| `list_users`, `list_events`, `create_event` | `schedule_event` (finds availability and books) |
| `read_logs` (returns everything) | `search_logs` (returns relevant lines with context) |
| `get_customer_by_id`, `list_transactions`, `list_notes` | `get_customer_context` (compiles the relevant recent info) |

An agent that must page through `list_contacts` wastes context reading token by token what a
`search_contacts` tool would have filtered in code. Each tool should have a clear, distinct purpose; if
a human engineer cannot say which tool applies, the agent cannot either.

### Namespace

With many servers and tools, group by prefix (`asana_search`, `jira_search`; or by resource:
`asana_projects_search`, `asana_users_search`). Prefix versus suffix naming measurably affects tool
selection, so test it.

### Return meaningful context

- Prefer **natural-language names and semantic identifiers** over cryptic ones: `name`, `image_url`,
  `file_type` are more useful to a model than `uuid`, `256px_image_url`, `mime_type`. Resolving opaque
  UUIDs into meaningful labels reduces hallucinated ids.
- Offer a **`response_format`** parameter (`"concise"` or `"detailed"`) so the agent can ask for ids
  only when it needs them for follow-up calls; in Anthropic's Slack example the concise form used about
  a third of the tokens.
- Choose the output structure (JSON, XML, Markdown) by evaluation; it affects performance.

### Optimise for token efficiency

Implement **pagination, range selection, filtering and truncation** with sensible defaults (Claude
Code caps tool responses at 25,000 tokens by default). When truncating, **say so and say how to get
more** ("showing 50 of 1,240 matches; narrow the query or pass `page=2`"). Make **error messages
actionable**: state what was wrong and what a valid call looks like, rather than an opaque code and
traceback.

```python-run
import json

RECORDS = [{"uuid": f"c9f1-{i:04d}", "name": f"Customer {i}", "plan": ["free", "pro", "team"][i % 3],
            "mrr": 0 if i % 3 == 0 else 49 * (i % 3), "notes": "lorem ipsum " * 30} for i in range(400)]

def search_customers(query="", plan=None, limit=5, response_format="concise"):
    """Task-level tool: filtering, truncation notice, concise vs detailed output, actionable errors."""
    if response_format not in ("concise", "detailed"):
        return "Error: response_format must be 'concise' or 'detailed'. Example: search_customers(plan='pro', limit=5)"
    if plan not in (None, "free", "pro", "team"):
        return f"Error: unknown plan {plan!r}. Valid plans: free, pro, team."
    hits = [r for r in RECORDS if query.lower() in r["name"].lower() and (plan is None or r["plan"] == plan)]
    shown = hits[:limit]
    if response_format == "concise":
        rows = [{"name": r["name"], "plan": r["plan"], "mrr": r["mrr"]} for r in shown]
    else:
        rows = shown
    note = f"Showing {len(shown)} of {len(hits)} matches." + (" Narrow the query or raise limit (max 50)." if len(hits) > len(shown) else "")
    return json.dumps({"results": rows, "note": note})

naive = json.dumps(RECORDS)                       # what a list_customers endpoint wrapper would return
good = search_customers(plan="pro", limit=5)
print("naive list_customers:", len(naive) // 4, "tokens (approx)")
print("search_customers    :", len(good) // 4, "tokens (approx)")
print(good[:230], "...")
print(search_customers(plan="enterprise"))
```

### Prompt-engineer the descriptions

Tool descriptions are loaded into context and steer behaviour. Write them as for a new teammate: make
implicit conventions explicit (query syntax, id formats, units, time zones), name parameters
unambiguously (`user_id`, not `user`), define terms, and include a short example where formats are
tricky. Small description edits can yield large gains; Anthropic credits precise description
refinements for a big part of Claude's SWE-bench Verified improvements.

### When there are too many tools

- **Deferred loading / tool search**: keep only names (or nothing) in context and let the agent search
  a tool catalogue and load schemas on demand.
- **Code execution over tool calls**: expose tools as code APIs in a sandbox so the agent writes a
  script that chains them and returns only the final result; intermediate data never enters context.
- **Skills**: instructions and scripts loaded progressively by relevance.

## 2. Prompt caching: how it works

Every request in an agent loop resends the same long prefix: system prompt, tool definitions, history.
**Prompt caching** lets the provider reuse the computation for a prefix it has already processed
(conceptually, the KV cache from module 1 persisted across requests), charging much less and
responding faster.

Mechanics (Anthropic's implementation; others are similar in spirit):

- You mark **cache breakpoints** with `cache_control: {"type": "ephemeral"}` on content blocks (up to
  four), or use automatic caching where offered. Everything **up to and including** the marked block,
  in the order **tools, then system, then messages**, forms the cached prefix.
- A later request gets a **cache hit** only if its prefix is **byte-for-byte identical** up to a
  breakpoint. One changed character early in the prompt invalidates everything after it.
- Cache entries have a short **TTL** (5 minutes by default, refreshed on each hit; a 1-hour option
  costs more to write).
- Pricing shape: **cache writes cost a premium** over normal input (about 1.25x for the 5-minute TTL),
  **cache reads cost a small fraction** (about 0.1x). Prompts below a minimum length (on the order of a
  thousand tokens, model dependent) are not cached. Check current pricing pages; the ratios are what
  matter for design.
- The response's `usage` reports `cache_creation_input_tokens`, `cache_read_input_tokens` and uncached
  `input_tokens`: monitor them.

OpenAI and Google Gemini apply caching automatically for sufficiently long prompts with matching
prefixes (Gemini also offers explicit cache objects); the design rules below apply to all of them.

```python
resp = client.messages.create(
    model="claude-sonnet-4-5", max_tokens=1024,
    tools=tools,                                                    # stable, deterministic order
    system=[{"type": "text", "text": LONG_SYSTEM_PROMPT,
             "cache_control": {"type": "ephemeral"}}],              # breakpoint 1: tools + system
    messages=history_with_breakpoint_on_last_block,                 # breakpoint 2: moves forward each turn
)
print(resp.usage.cache_read_input_tokens, resp.usage.cache_creation_input_tokens, resp.usage.input_tokens)
```

## 3. The economics

```python-run
def cost(prefix, turns, new_per_turn, price_in=3.0, write_mult=1.25, read_mult=0.10, cached=True):
    """Input cost in dollars for an agent loop; price_in = $ per million input tokens."""
    total, cached_len = 0.0, 0
    for t in range(turns):
        context = prefix + t * new_per_turn            # history grows every turn
        if not cached:
            total += context * price_in
        else:
            read = cached_len                           # everything cached so far is read cheaply
            write = context - cached_len                # the new suffix is written to the cache
            total += read * price_in * read_mult + write * price_in * write_mult
            cached_len = context
    return total / 1e6

for turns in [1, 10, 50, 200]:
    a = cost(20_000, turns, 1_500, cached=False); b = cost(20_000, turns, 1_500)
    print(f"{turns:4d} turns: uncached ${a:8.2f}   cached ${b:7.2f}   saving {100*(1-b/a):5.1f}%")
```

A single request is slightly *more* expensive with caching (the write premium); break-even comes at the
second request, and long loops save the large majority of input cost. Uncached, an agent loop's input
cost grows **quadratically** with the number of turns (each turn re-reads everything); caching makes it
close to linear.

## 4. Designing for cache hits

1. **Order by volatility**: static first (tool definitions, system prompt, reference documents,
   few-shot examples), then slowly changing (project memory), then the conversation, with the newest
   message last.
2. **Never put volatile values in the prefix**: timestamps, request ids, random seeds, user-specific
   strings in a shared system prompt. Put the current date in a later message or round it to the day.
3. **Keep tool definitions byte-stable**: same set, same order, same serialisation (sort keys). This is
   exactly why the MCP spec asks servers to return tools in deterministic order. Adding or removing a
   tool mid-session invalidates the whole cache: prefer to keep tools constant and constrain behaviour
   by other means.
4. **Append-only history**: editing or deleting earlier messages invalidates everything after the edit.
   So batch context edits (tool-result clearing, compaction) into infrequent events rather than
   trimming a little every turn, and weigh each edit's context savings against the cache miss.
5. **Mind the TTL**: keep requests flowing within the window (or use the longer TTL for bursty
   workloads); a cold cache costs a write.
6. **Share prefixes across users** where possible (common system prompt and tools first, per-user
   context after) to raise hit rates.

```python-run
import hashlib, json

def prefix_key(tools, system):
    blob = json.dumps({"tools": tools, "system": system}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]

tools = [{"name": "search", "description": "Search docs"}, {"name": "read", "description": "Read a doc"}]
base = prefix_key(tools, "You are a support agent.")
print("same content                  :", prefix_key(tools, "You are a support agent.") == base)
print("tools reordered               :", prefix_key(tools[::-1], "You are a support agent.") == base)
print("timestamp in system prompt    :", prefix_key(tools, "You are a support agent. Now: 2026-11-20T10:31:07") == base)
print("date moved to a later message :", prefix_key(tools, "You are a support agent.") == base)
```

## 5. Caching beyond the provider

- **Engine-level prefix caching** (vLLM `--enable-prefix-caching`, SGLang's radix cache, llama.cpp slot
  cache) does the same for self-hosted models.
- **Exact response caching**: memoise identical requests (deterministic settings) in Redis; great for
  repeated classification or FAQ prompts.
- **Semantic caching**: return a stored answer when a new query is embedding-similar to an old one.
  Risky: similar questions can need different answers, and personalised or time-sensitive responses
  must not be shared. Use conservative thresholds and scope keys by user/tenant.
- **Batch APIs** are the other big discount lever for offline workloads, and combine with caching.

> [!INTERVIEW]
> **"How would you cut the cost of a 100-turn agent session?"** Prompt caching: stable prefix (tools
> then system then history), breakpoints on the system prompt and the latest turn, no volatile values
> early, append-only history, deterministic tool order; monitor cache read/write tokens. Then shrink
> what is sent at all: task-level tools with concise outputs, tool-result clearing in batches,
> compaction, sub-agents, deferred tool loading; route easy steps to a cheaper model. Explain that
> uncached loops cost quadratically in turns and that one early change invalidates the cache.

## Summary

- Build few, task-level, namespaced tools that return meaningful, bounded, optionally concise output
  with actionable errors; treat descriptions as prompts and evaluate with real agents.
- Prompt caching reuses identical prefixes: premium to write, about a tenth to read, short TTL.
- Order context by volatility, keep tools and system prompt byte-stable, keep history append-only.
- Context edits trade tokens for cache misses: batch them.
- Add engine prefix caches, exact or semantic response caches and batch APIs where they fit.

```quiz
[
  {"q": "Which tool design does Anthropic's guidance prefer?",
   "options": ["A search_contacts tool that filters server-side", "A list_contacts tool returning every contact", "One tool per database table", "A single run_sql tool with no description"], "answer": 0,
   "explain": "Task-level tools avoid pushing bulk data through the context window."},
  {"q": "What should a tool do when it truncates its output?",
   "options": ["Say that it truncated and how to get the rest", "Silently cut off", "Raise an exception", "Return an empty result"], "answer": 0,
   "explain": "Helpful truncation notes steer the agent towards narrower queries or pagination."},
  {"q": "In what order is the cacheable prefix assembled in Anthropic's prompt caching?",
   "options": ["tools, then system, then messages", "messages, system, tools", "system, messages, tools", "Any order; it is content-addressed per block"], "answer": 0,
   "explain": "A change in tools invalidates system and message caches that come after it."},
  {"q": "You add the current timestamp to the top of the system prompt on every request. Effect?",
   "options": ["Every request misses the cache", "No effect", "Caching improves", "Only tool definitions are re-cached"], "answer": 0,
   "explain": "Cache hits require an identical prefix; a changing early value invalidates everything after it."},
  {"q": "With typical pricing (write about 1.25x, read about 0.1x), when does caching start saving money?",
   "options": ["From the second request that reuses the prefix within the TTL", "Only after 100 requests", "On the first request", "Never for agents"], "answer": 0,
   "explain": "The first request pays the write premium; subsequent reads are about a tenth of the price."},
  {"q": "Why should tool-result clearing be done in batches rather than every turn?",
   "options": ["Each edit to earlier history invalidates the cached prefix after that point", "Batches are required by JSON", "It improves recall", "It changes the model's temperature"], "answer": 0,
   "explain": "Frequent small edits cause constant cache misses that can outweigh the token savings."},
  {"q": "What is the main risk of semantic response caching?",
   "options": ["Serving a stored answer to a similar-looking query that needs a different answer", "It uses too much GPU", "It breaks tokenization", "It requires fine-tuning"], "answer": 0,
   "explain": "Similarity is not equivalence; personalised or time-sensitive answers are especially dangerous."}
]
```

> **Source:** Anthropic Engineering, "Writing effective tools for agents — with agents" (2025,
> https://www.anthropic.com/engineering/writing-tools-for-agents), "Code execution with MCP" (2025),
> "Effective context engineering for AI agents" (2025); Anthropic docs, "Prompt caching"
> (https://docs.claude.com/en/docs/build-with-claude/prompt-caching); OpenAI and Gemini caching docs;
> vLLM automatic prefix caching docs; Huyen, *AI Engineering*, ch. 9 (prompt cache, KV cache) and
> ch. 10 (caching in the application architecture: exact and semantic caches).
