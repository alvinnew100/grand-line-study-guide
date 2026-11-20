# Structured outputs and streaming

Two mechanics separate a demo from an application. Programs need **data they can parse**, not prose;
users need **tokens as they are generated**, not a spinner for twenty seconds. This lesson covers the
ladder of structured-output techniques, how constrained decoding works inside the sampler, and how to
consume streaming events correctly, including streamed tool calls.

## 1. The structured-output ladder

From weakest to strongest guarantee:

1. **Ask nicely.** "Respond with JSON matching this schema" plus an example. Works most of the time
   with strong models; fails with trailing prose, Markdown fences, missing fields, truncated output.
2. **Prefill / stop sequences.** Start the assistant's reply with `{` (prefill) so the model continues
   JSON; stop on a closing tag. Cheap and effective where supported.
3. **JSON mode.** The provider guarantees *syntactically valid JSON*, but not your schema.
4. **Tool calling as a schema carrier.** Define a tool whose input schema is your desired output and
   force it with `tool_choice`. The arguments are your structured result.
5. **Structured outputs with constrained decoding** (strict mode). You supply a JSON Schema; the
   provider compiles it to a grammar and masks invalid tokens at every step, so the output **always
   parses and validates**. Available from OpenAI (`response_format` with `json_schema`, `strict`),
   Anthropic (structured outputs via an output format/schema and strict tools), Gemini
   (`response_schema`), and for open models through vLLM/TGI/llama.cpp guided decoding with Outlines,
   XGrammar or llguidance.

Whatever rung you use, **validate in code** (Pydantic) and have a repair path.

```python
from pydantic import BaseModel, Field
from typing import Literal

class Ticket(BaseModel):
    category: Literal["billing", "bug", "feature_request", "other"]
    urgency: int = Field(ge=1, le=5, description="1 = low, 5 = outage")
    summary: str = Field(max_length=200)
    order_ids: list[str] = []

schema = Ticket.model_json_schema()            # hand this to the API
# OpenAI-style:    client.responses.parse(model=..., input=..., text_format=Ticket)
# Anthropic-style: client.messages.parse(model=..., messages=..., output_format=Ticket)
# Any provider:    force a tool whose input_schema is `schema`, then Ticket.model_validate(tool_input)
ticket = Ticket.model_validate_json(raw_model_output)
```

(Exact method names vary by SDK version; check the current reference. Libraries such as Instructor and
Pydantic AI wrap this pattern, including automatic retries on validation errors.)

## 2. How constrained decoding works

At each step the model produces logits over the whole vocabulary. A **grammar engine** tracks which
strings are still legal given the output so far (as a state machine for regular structure or a
pushdown automaton for nested JSON) and sets the logits of every token that would violate the schema to
$-\infty$ before sampling. Subtleties: tokens span multiple characters, so the engine precomputes, for
each grammar state, the set of allowed tokens; and schemas are restricted to a supported subset
(for instance no arbitrary regex look-arounds, bounded recursion, `additionalProperties: false`
required in strict modes).

```python-run
import numpy as np
rng = np.random.default_rng(0)
vocab = ['{"sentiment": "', 'positive', 'negative', 'neutral', '"}', 'Sure', '!', ' Here', ' is', '\n']
# A tiny grammar as a state machine: state -> allowed token ids -> next state
GRAMMAR = {0: {0: 1}, 1: {1: 2, 2: 2, 3: 2}, 2: {4: 3}}           # 3 = accept

def generate(constrained):
    state, out = 0, []
    for _ in range(6):
        logits = rng.normal(0, 1, len(vocab))
        logits[5] += 3.0                                           # the model "wants" to chat: 'Sure'
        logits[2] += 1.0
        if constrained:
            allowed = GRAMMAR[state]
            mask = np.full(len(vocab), -np.inf); mask[list(allowed)] = 0
            tok = int(np.argmax(logits + mask))                    # greedy over legal tokens only
            state = allowed[tok]
        else:
            tok = int(np.argmax(logits))
        out.append(vocab[tok])
        if constrained and state == 3:
            break
    return "".join(out)

print("unconstrained:", repr(generate(False)))
print("constrained  :", repr(generate(True)))
```

What constrained decoding does **not** do:

- **Semantics**: a valid `"urgency": 5` can still be wrong. Evaluate content, not just shape.
- **Truncation**: if `max_tokens` is hit mid-object the JSON is incomplete. Check the stop reason.
- **Refusals**: a model may refuse; handle that path.
- **Quality for free**: forcing a format can degrade reasoning if the schema leaves no room to think.
  Put a `reasoning` field **first** in the schema (fields are generated in order), or let the model
  think in a separate step/thinking block and then emit the structure.

Schema design tips: descriptive field names and descriptions (they are prompt text), enums instead of
free strings, flat over deeply nested, required fields with explicit null options rather than optional
ambiguity, and keep schemas small.

### A repair loop

```python-run
import json, re

FENCE = "`" * 3      # a Markdown code fence

def extract_json(text):
    """Tolerant extraction: strip code fences, find the outermost braces, then parse."""
    text = text.strip().replace(FENCE + "json", "").replace(FENCE, "")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])

def validate(obj):
    errs = []
    if obj.get("category") not in ("billing", "bug", "other"): errs.append("category must be billing|bug|other")
    if not isinstance(obj.get("urgency"), int) or not 1 <= obj["urgency"] <= 5: errs.append("urgency must be int 1-5")
    return errs

attempts = iter(['Sure! Here is the JSON:\n' + FENCE + 'json\n{"category": "payment", "urgency": "high"}\n' + FENCE,
                 '{"category": "billing", "urgency": 4}'])
def model(prompt): return next(attempts)

prompt = "Classify the ticket as JSON."
for attempt in range(3):
    raw = model(prompt)
    try:
        obj = extract_json(raw); errs = validate(obj)
    except (ValueError, json.JSONDecodeError) as e:
        obj, errs = None, [str(e)]
    print(f"attempt {attempt + 1}: {errs or 'valid ' + json.dumps(obj)}")
    if not errs: break
    prompt += f"\nYour previous output was invalid: {'; '.join(errs)}. Return only corrected JSON."
```

Feeding the validation errors back usually fixes the output in one retry. Cap retries, and log failures
as eval cases.

## 3. Streaming

LLM APIs stream over **Server-Sent Events (SSE)**: a long-lived HTTP response of `event:` / `data:`
lines. Streaming does not make generation faster, but it slashes *perceived* latency:
**time to first token (TTFT)** becomes the number users feel, followed by a steady tokens-per-second
rate.

Anthropic's Messages stream has this event grammar:

```text
message_start                    (message metadata, input token usage)
  content_block_start  index=0   (type: text | tool_use | thinking)
    content_block_delta          (text_delta | input_json_delta | thinking_delta)  ... repeated
  content_block_stop   index=0
  content_block_start  index=1 ...
message_delta                    (stop_reason, cumulative output usage)
message_stop
ping / error                     (may appear at any time)
```

OpenAI's Chat Completions stream sends `chat.completion.chunk` objects with `choices[0].delta`
(content fragments, or `tool_calls` fragments keyed by `index`), ending with `data: [DONE]`; the newer
Responses API uses typed semantic events (`response.output_text.delta`, ...).

```python
with client.messages.stream(model="claude-sonnet-4-5", max_tokens=1024, messages=msgs) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    final = stream.get_final_message()          # fully assembled message with usage and stop_reason
```

### Accumulating a stream by hand

Tool-call arguments arrive as **partial JSON strings** (`input_json_delta.partial_json`) that are only
parseable once the block stops. You concatenate fragments per content-block index and parse at
`content_block_stop`. This module's `llm-stream-accumulate` problem is exactly this routine.

```python-run
import json
events = [
  {"type": "message_start"},
  {"type": "content_block_start", "index": 0, "content_block": {"type": "text"}},
  {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Let me check "}},
  {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "the weather."}},
  {"type": "content_block_stop", "index": 0},
  {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "toolu_1", "name": "get_weather"}},
  {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": '{"city": "Os'}},
  {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": 'lo", "days": 3}'}},
  {"type": "content_block_stop", "index": 1},
  {"type": "message_delta", "delta": {"stop_reason": "tool_use"}},
  {"type": "message_stop"},
]
blocks, buf, stop = {}, {}, None
for e in events:
    t = e["type"]
    if t == "content_block_start":
        blocks[e["index"]] = dict(e["content_block"]); buf[e["index"]] = ""
    elif t == "content_block_delta":
        d = e["delta"]; buf[e["index"]] += d.get("text", "") + d.get("partial_json", "")
    elif t == "content_block_stop":
        b = blocks[e["index"]]
        if b["type"] == "text": b["text"] = buf[e["index"]]
        else: b["input"] = json.loads(buf[e["index"]] or "{}")
    elif t == "message_delta":
        stop = e["delta"].get("stop_reason")
print([blocks[i] for i in sorted(blocks)], stop)
```

### Streaming engineering checklist

- **Always read the stop reason**: `end_turn`, `max_tokens` (truncated: continue or raise the limit),
  `tool_use`, `stop_sequence`, `refusal`, or a pause that expects you to continue the turn.
- **Errors can arrive mid-stream** after a 200 status (e.g. overload). Decide whether to show partial
  text, retry from scratch, or resume by prefilling what you have.
- **Timeouts**: use streaming for long generations so idle-connection timeouts do not kill a request;
  set a first-byte timeout and an inter-chunk timeout.
- **Backpressure and cancellation**: if the user navigates away, abort the request to stop paying for
  tokens.
- **Proxies** buffer SSE unless told not to (`X-Accel-Buffering: no`, disable gzip buffering).
- **Rendering**: partial Markdown and partial JSON need tolerant renderers; for structured streaming
  use a partial-JSON parser (or stream a list of objects, one per line).
- **Guardrails and streaming conflict**: you cannot un-send a token. Options: buffer a sentence or
  chunk and scan before release, run a parallel checker that can abort the stream, or post-hoc retract
  in the UI (next lesson).
- **Unicode**: byte-level tokens can split a multi-byte character across chunks; decode incrementally.

## 4. Latency vocabulary

- **TTFT**: queueing + prefill of the prompt (grows with input length; prompt caching cuts it).
- **TPOT / tokens per second**: decode speed.
- **Total latency** $\approx$ TTFT + output tokens $\times$ TPOT: for long answers, **output length
  dominates**, so asking for concise output is a latency optimisation.

> [!INTERVIEW]
> **"How do you get reliable JSON from an LLM?"** Use schema-constrained structured outputs or a forced
> tool call where available (explain logit masking against a grammar), keep schemas simple with enums
> and descriptions, put reasoning before conclusions, validate with Pydantic, retry with the validation
> error, check stop reasons for truncation and refusals, and evaluate semantic correctness separately
> because constrained decoding only guarantees shape.

## Summary

- Structured output options range from prompting to schema-constrained decoding; always validate and
  keep a repair loop.
- Constrained decoding masks illegal tokens per grammar state: guaranteed shape, not guaranteed truth.
- Streaming is SSE events; assemble text and partial-JSON tool arguments per block index.
- Handle stop reasons, mid-stream errors, cancellation and guardrail timing.
- TTFT depends on input and queueing; total latency is dominated by output length.

```quiz
[
  {"q": "What does schema-constrained decoding guarantee?",
   "options": ["The output parses and conforms to the schema", "The values are factually correct", "The model never refuses", "Output is never truncated"], "answer": 0,
   "explain": "Masking enforces shape only; semantics, refusals and max_tokens truncation remain your problem."},
  {"q": "How does constrained decoding enforce a grammar?",
   "options": ["It sets logits of tokens that would violate the grammar to -infinity before sampling", "It retries until valid", "It post-edits the text", "It fine-tunes the model on the schema"], "answer": 0,
   "explain": "A state machine tracks legal continuations and masks the rest at each step."},
  {"q": "Why put a reasoning field before the answer field in a schema?",
   "options": ["Fields are generated in order, so the model can think before committing", "It reduces tokens", "JSON requires alphabetical order", "It disables streaming"], "answer": 0,
   "explain": "Autoregressive generation means earlier fields condition later ones."},
  {"q": "In a streamed tool call, when can you parse the tool's JSON arguments?",
   "options": ["After the content block stops, once all partial_json fragments are concatenated", "After the first delta", "Before message_start", "Never; arguments are not streamed"], "answer": 0,
   "explain": "Fragments are arbitrary string pieces and are only valid JSON once complete."},
  {"q": "A response ends with stop_reason = max_tokens. What does that mean?",
   "options": ["The output was cut off by the token limit and may be incomplete", "The model finished naturally", "A tool must be run", "The prompt was too long"], "answer": 0,
   "explain": "Truncated JSON or answers must be continued or regenerated with a higher limit."},
  {"q": "Which metric does streaming mainly improve for the user?",
   "options": ["Perceived latency via time to first token", "Total tokens generated", "Model accuracy", "Input cost"], "answer": 0,
   "explain": "Generation is not faster, but the user sees output immediately."},
  {"q": "Why do output guardrails conflict with streaming?",
   "options": ["Tokens already sent cannot be unsent, so checks must buffer or run alongside", "Guardrails need GPUs", "SSE cannot carry JSON", "Streaming disables tool use"], "answer": 0,
   "explain": "You must choose between buffering chunks for scanning and risking exposure of content before a check completes."}
]
```

> **Source:** Anthropic docs: "Streaming Messages", "Structured outputs", tool use
> (https://docs.claude.com/en/docs/build-with-claude/streaming); OpenAI docs: Structured Outputs and
> streaming; Willard & Louf, "Efficient Guided Generation for LLMs" (Outlines, 2023); vLLM structured
> outputs docs; Hugging Face TGI guidance docs
> (https://huggingface.co/docs/text-generation-inference/conceptual/guidance); Huyen, *AI Engineering*,
> ch. 2 (structured outputs, constrained sampling) and ch. 9 (latency metrics: TTFT, TPOT).
