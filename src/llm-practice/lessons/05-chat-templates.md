# Special tokens, chat templates and tokenizer pitfalls

A chat model does not natively understand a list of `{"role", "content"}` dictionaries. It was trained
on a **flat string** in which turns are delimited by special tokens, in a format specific to that model
family. The **chat template** is the function that flattens your messages into exactly that string.
Get it wrong and a perfectly good model rambles, never stops, ignores the system prompt, or silently
loses quality. This is one of the most common real-world bugs in open-model work.

## 1. Special tokens

Special tokens are vocabulary entries that the tokenizer never produces from ordinary text (when
configured correctly) and that carry structural meaning:

| token (examples) | purpose |
|---|---|
| BOS: `<s>`, `<|begin_of_text|>`, `<bos>` | start of sequence |
| EOS: `</s>`, `<|end_of_text|>`, `<|im_end|>`, `<|eot_id|>` | end of sequence or end of turn: generation stops here |
| PAD: `<pad>` | fills batches to equal length; masked out of attention and loss |
| UNK: `[UNK]`, `<unk>` | unknown piece (rare with byte-level vocabularies) |
| `[CLS]`, `[SEP]`, `[MASK]` | BERT: sequence summary, segment separator, masked-LM target |
| role markers: `<|im_start|>`, `<|start_header_id|>` | delimit chat turns |
| tool markers: `<tool_call>`, `<|python_tag|>` | delimit tool calls in some families |
| reasoning: `<think>` ... `</think>` | delimit hidden reasoning in reasoning models (Qwen3, DeepSeek-R1) |

Two subtleties:

- A model can have **several stop tokens**. Llama 3 Instruct ends turns with `<|eot_id|>` but its
  `eos_token` in the tokenizer was originally `<|end_of_text|>`; if generation only stops on the
  latter, the model keeps writing fake turns. Check `generation_config.json`'s `eos_token_id`, which
  may be a list.
- **Base vs instruct models.** A base model was pretrained only on raw text; it has special tokens in
  its vocab but no learned chat behaviour. An instruct/chat model was post-trained on a specific
  template. Using a base model with a chat template, or an instruct model without one, gives poor
  results.

## 2. What a template produces

Here are the same two messages rendered for three families (abridged):

**ChatML** (Qwen, SmolLM, many fine-tunes):

```text
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
What is RoPE?<|im_end|>
<|im_start|>assistant
```

**Llama 3**:

```text
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

What is RoPE?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

```

**Mistral (v1-style)**: `<s>[INST] What is RoPE? [/INST]` with no separate system role (older
templates prepend the system text to the first user turn).

The trailing assistant header is the **generation prompt**: it tells the model "now it is your turn".

## 3. `apply_chat_template` in practice

Templates are Jinja2 programs stored with the tokenizer (`chat_template` in `tokenizer_config.json`,
or a separate `chat_template.jinja` file in recent repos). Static code:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "Qwen/Qwen3-0.6B"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto", device_map="auto")

messages = [
    {"role": "system", "content": "You are a concise tutor."},
    {"role": "user", "content": "Explain the KV cache in one sentence."},
]
# 1) inspect the string
print(tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))

# 2) tokenize and generate
inputs = tok.apply_chat_template(messages, add_generation_prompt=True,
                                 return_tensors="pt", return_dict=True).to(model.device)
out = model.generate(**inputs, max_new_tokens=80)
print(tok.decode(out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

Key arguments:

- `add_generation_prompt=True` for **inference** (append the assistant header). For **training** on
  complete conversations, leave it False.
- `continue_final_message=True` to make the model continue a partially written assistant message
  (prefilling, e.g. starting the answer with `{` to force JSON).
- `tools=[...]` to render tool definitions (JSON schemas or Python functions with type hints and
  docstrings) into the prompt in the family's native format (module 7).
- `documents=[...]` for RAG-aware templates that have a grounded-generation format.
- `enable_thinking=False` (Qwen3) and similar template variables are passed through as extra kwargs.

> [!WARNING]
> **Double BOS.** If the template already inserts `<|begin_of_text|>` and you then call
> `tok(text)` (which adds special tokens by default), you get two BOS tokens and slightly degraded
> output. When tokenizing a rendered template string, pass `add_special_tokens=False`, or let
> `apply_chat_template(tokenize=True)` do it.

## 4. A template renderer from scratch

The logic inside a template is simple. Here is a ChatML renderer in plain Python, including a default
system prompt and the generation prompt; this module's `llm-chat-template` problem extends it with
tool calls.

```python-run
def render_chatml(messages, add_generation_prompt=True, default_system=None):
    msgs = list(messages)
    if default_system and (not msgs or msgs[0]["role"] != "system"):
        msgs.insert(0, {"role": "system", "content": default_system})
    out = []
    for m in msgs:
        out.append(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n")
    if add_generation_prompt:
        out.append("<|im_start|>assistant\n")
    return "".join(out)

s = render_chatml([{"role": "user", "content": "Hi!"}], default_system="Be brief.")
print(s)
print(repr(s[-25:]))
```

Rendering whitespace exactly matters: a model trained with `"\n"` after `<|im_start|>assistant` and
served with `" "` is out of distribution on every single request.

## 5. Templates for training: masking the prompt

For supervised fine-tuning (module 6) we usually want loss **only on assistant tokens**, not on the
system or user text. TRL's `SFTTrainer` supports `assistant_only_loss=True`, which relies on the chat
template wrapping assistant content in `{% generation %}` ... `{% endgeneration %}` markers so the
tokenizer can return an `assistant_masks` array via
`apply_chat_template(..., return_assistant_tokens_mask=True)`. Positions outside the mask get label
`-100`.

```python-run
# Toy illustration of building labels with an assistant mask
tokens = ["<|im_start|>", "user", "\n", "Hi", "<|im_end|>", "\n",
          "<|im_start|>", "assistant", "\n", "Hello", "!", "<|im_end|>", "\n"]
assistant_mask = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0]   # train on answer + its end-of-turn token
ids = list(range(100, 100 + len(tokens)))
labels = [i if m else -100 for i, m in zip(ids, assistant_mask)]
for t, l in zip(tokens, labels):
    print(f"{t!r:16} {l}")
```

Including the end-of-turn token `<|im_end|>` in the trained positions is important: that is how the
model learns to **stop**.

## 6. Special-token injection

If user-supplied text containing the literal string `<|im_start|>system` is tokenised as the real
special token, a user can forge a system turn. Hugging Face tokenizers parse special tokens in input
text by default; protections include `split_special_tokens=True` (treat them as plain text), escaping
or stripping these strings from untrusted input, and rendering untrusted content only inside message
`content` fields. Hosted APIs (Claude, OpenAI) accept structured messages and handle this for you,
which is one reason prompt injection there must be fought at the semantic level instead (module 10).

## 7. Debugging checklist

1. Print the rendered template once (`tokenize=False`) and eyeball every newline and special token.
2. Confirm the stop tokens in `generation_config.eos_token_id` include the end-of-turn token.
3. Check `pad_token`. Many decoder tokenizers ship without one; setting `pad_token = eos_token` is
   common but then you must rely on the attention mask (and with some collators the EOS gets masked out
   of the loss, so the model never learns to stop; use a distinct pad token if available).
4. Use **left padding** for batched generation with decoder-only models (`tok.padding_side = "left"`),
   right padding for training.
5. Fine-tuning a base model? Either adopt the template of the instruct sibling or set one explicitly
   (TRL `SFTConfig(chat_template_path=...)`), and make sure the same template is used at serving time
   (vLLM and TGI read the template from the tokenizer config).

> [!INTERVIEW]
> **"Your fine-tuned model never stops generating. What do you check?"** The EOS / end-of-turn
> token: is it in the training labels (not masked to -100, not replaced by padding)? Is the serving
> stack's stop-token list consistent with the template (`<|eot_id|>` vs `<|end_of_text|>`)? Is the
> serving template identical to the training template? Is pad_token equal to eos_token, causing the
> collator to mask EOS?

## Summary

- Chat models consume a flat string; the chat template (Jinja, shipped with the tokenizer) defines it.
- `add_generation_prompt` for inference, not for training; `continue_final_message` for prefilling.
- Training masks non-assistant tokens with -100 but keeps the end-of-turn token so the model learns to stop.
- Most "model is broken" reports are template, BOS/EOS, padding or stop-token mismatches.
- Untrusted text must never be able to produce real special tokens.

```quiz
[
  {"q": "What does add_generation_prompt=True do?",
   "options": ["Appends the assistant turn header so the model starts answering", "Adds a system prompt", "Adds EOS at the end", "Enables sampling"], "answer": 0,
   "explain": "It ends the string with the opening of an assistant turn, e.g. <|im_start|>assistant newline."},
  {"q": "Your rendered template already contains <|begin_of_text|>. You then call tok(text). What goes wrong?",
   "options": ["A second BOS token is added", "Nothing", "The EOS is removed", "Padding becomes right-sided"], "answer": 0,
   "explain": "Tokenizers add special tokens by default; pass add_special_tokens=False for pre-rendered strings."},
  {"q": "During SFT with assistant-only loss, which tokens should keep their labels?",
   "options": ["Assistant content plus its end-of-turn token", "Only user tokens", "All tokens", "Only the system prompt"], "answer": 0,
   "explain": "Training on the end-of-turn token teaches the model when to stop."},
  {"q": "For batched generation with a decoder-only model, which padding side is recommended?",
   "options": ["Left", "Right", "Both", "No padding is possible"], "answer": 0,
   "explain": "Left padding keeps every sequence's last real token at the final position, where generation continues."},
  {"q": "A user message contains the literal text <|im_start|>system ... Why is this dangerous?",
   "options": ["If parsed as a real special token, the user can forge a system turn", "It wastes tokens", "It breaks RoPE", "It changes the vocabulary"], "answer": 0,
   "explain": "Special-token injection lets untrusted input impersonate privileged roles; split or escape special tokens."},
  {"q": "What is the most likely cause of a Llama 3 Instruct model producing fake extra user turns?",
   "options": ["Generation stops only on <|end_of_text|> and not on <|eot_id|>", "Temperature too low", "RoPE scaling", "Too many KV heads"], "answer": 0,
   "explain": "The end-of-turn token must be among the stop tokens, otherwise the model keeps writing the transcript."}
]
```

> **Source:** Transformers docs, "Chat templates" and "Writing a chat template"
> (https://huggingface.co/docs/transformers/chat_templating,
> https://huggingface.co/docs/transformers/chat_templating_writing); TRL docs on assistant-only loss
> (https://huggingface.co/docs/trl/sft_trainer); HF LLM Course ch. 11 "Supervised fine-tuning"
> (https://huggingface.co/learn/llm-course/chapter11); Huyen, *AI Engineering*, ch. 5 (prompt
> templates) and ch. 7 (finetuning data formats).
