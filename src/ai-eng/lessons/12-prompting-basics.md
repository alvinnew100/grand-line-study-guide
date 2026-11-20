# Prompts, in-context learning and context length

Prompt engineering is the first adaptation technique anyone should try. It needs no weight updates, little data, and minutes rather than weeks. Huyen also warns that it is often dismissed as "fiddling with words", and that many teams under-invest in doing it rigorously. A prompt is a piece of software: it should be **systematic, versioned and evaluated**. This lesson covers what a prompt is made of, in-context learning, system vs user prompts and chat templates, and how context length and position affect what a model actually uses.

> [!NOTE]
> Context engineering, where you assemble the right information, tools and memory for each call (including protocols such as MCP), is covered in depth in the **LLM Practice** track. This module follows Huyen's treatment of prompts themselves.

## 1. Anatomy of a prompt

A prompt is an instruction given to a model to perform a task. It usually contains one or more of:

1. **Task description**: what the model should do, including the role it should play and the output format.
2. **Examples** of how to do the task. For instance, to detect toxicity you show a few toxic and non-toxic examples.
3. **The task**: the concrete input, such as the question to answer or the document to summarize.

For prompting to work, the model must be able to **follow instructions**. How much prompt engineering you need depends on how **robust** the model is to prompt perturbations. If "5" and "five" give different answers, the model is fragile. Robustness can be measured by perturbing prompts and checking how much outputs change. Stronger models are generally more robust, which saves fiddling time.

> [!TIP]
> Experiment with structure. Huyen notes that most models, GPT-4 included, empirically do better when the task description is at the **beginning** of the prompt, while some (for example Llama 3) seemed to do better with it at the **end**.

## 2. In-context learning: zero-shot and few-shot

Teaching a model through its prompt is **in-context learning (ICL)**, a term introduced in the GPT-3 paper "Language Models Are Few-shot Learners" (Brown et al., 2020). GPT-3 was trained only on next-token prediction, yet from examples in its context it could translate, do reading comprehension and simple math, and answer SAT questions, all with **no weight updates**.

- Each example in the prompt is a **shot**. Five examples is **5-shot**, and none is **zero-shot**.
- ICL is a form of **continual learning**. A model trained on old JavaScript docs can use the new docs if you put them in its context, which lets it answer beyond its cutoff.
- More examples generally help but cost tokens and context space. For GPT-3, few-shot clearly beat zero-shot. For GPT-4 and similar models, Microsoft's 2023 analysis found only limited gains from few-shot on general tasks, because stronger models follow instructions better. **Domain-specific** formats still benefit. If a model has rarely seen the Ibis dataframe API, examples help a lot.

> [!NOTE]
> **Prompt vs context.** Usage varies. In the GPT-3 paper, "context" means the whole input. In other writing, the context is the background information (retrieved documents, conversation history) and the prompt is the whole input. Huyen uses *prompt* for the whole input and *context* for the information supplied to help do the task.

```python-run
# Building a few-shot prompt programmatically: examples are data, not hand-edited text.
examples = [
    ("I loved every minute of it!", "POSITIVE"),
    ("Worst purchase I've ever made.", "NEGATIVE"),
    ("It arrived on Tuesday.", "NEUTRAL"),
]
task = "Classify the sentiment of the review as POSITIVE, NEGATIVE or NEUTRAL. Answer with the label only."
def build(review, k):
    shots = "\n\n".join(f"Review: {r}\nLabel: {l}" for r, l in examples[:k])
    return f"{task}\n\n{shots}\n\nReview: {review}\nLabel:" if k else f"{task}\n\nReview: {review}\nLabel:"
print(build("The battery died after two days.", 0)); print("-" * 50)
print(build("The battery died after two days.", 3))
```

## 3. System prompt and user prompt

Most model APIs split instructions into:

- a **system prompt**: the task description, role, rules and constraints, set by the application developer, and
- a **user prompt**: the task input, usually from the end user.

For example, a real-estate assistant's system prompt might say: "You are an experienced real estate agent. Read each disclosure carefully, assess the condition of the property, and answer concisely." The user prompt contains the disclosure and the question.

### Chat templates

Under the hood, the system and user prompts are **concatenated into one sequence** using the model's **chat template**, which uses special tokens to mark roles. Llama 2 wraps the system message in `<<SYS>>` tags inside `[INST] … [/INST]`, and Llama 3 uses headers such as `<|start_header_id|>system<|end_header_id|>`. Every model family has its own template, and templates can change between versions.

Template mistakes are common and silent. The model still does *something* reasonable, so you may not notice. An extra newline can change behavior noticeably. Huyen's practices:

- Follow the model's chat template **exactly** when building raw prompts.
- If a third-party tool builds prompts for you, **verify it uses the right template**.
- **Print the final prompt** before sending it, at least while debugging.

```python-run
# A simplified chat template renderer (illustrative, not an exact vendor template).
def render(messages, bos="<s>"):
    out = [bos]
    for m in messages:
        out.append(f"<|{m['role']}|>\n{m['content'].strip()}\n<|end|>")
    out.append("<|assistant|>\n")      # generation prompt: the model continues from here
    return "\n".join(out)
msgs = [{"role": "system", "content": "You are a concise real-estate assistant."},
        {"role": "user", "content": "Is a 1962 roof a concern?"}]
print(render(msgs))
```

### Why do system prompts help?

The model sees a single sequence, so why should system instructions matter more? Huyen gives two likely reasons:

1. The system prompt comes **first**, and models may be better at following instructions that appear first.
2. Models may be **post-trained to prioritize** system prompts. OpenAI's "Instruction Hierarchy" (Wallace et al., 2024) trains models to rank system above user above tool outputs. This also helps defend against prompt attacks (lesson 3 of this module).

## 4. Context length and context efficiency

Maximum context lengths have exploded. The first three GPT generations had 1K, 2K and 4K. Within about five years the range went from GPT-2's 1K to Gemini 1.5 Pro's **2M**, a 2,000× increase. For scale: 100K tokens fits a moderate book (Huyen's book is about 120,000 words, roughly 160,000 tokens), and 2M tokens fits about 2,000 Wikipedia pages or a codebase like PyTorch.

### Not all positions are equal

Models are much better at using information at the **beginning and end** of the prompt than in the **middle**. This is the "lost in the middle" finding (Liu et al., 2023). Two common tests:

- **Needle in a haystack (NIAH)**: insert a random fact (the needle) at different positions in a long prompt and ask the model to retrieve it. Plot accuracy by position and context length.
- **RULER** (Hsieh et al., 2024): a broader set of long-context tasks. It found that a model's *effective* context length is often far shorter than its advertised maximum.

Huyen recommends running NIAH-style tests with **your own data**. For example, put a fact from a patient's visit transcript at different positions in a medical record and ask the model about it.

```python-run
# Simulated 'lost in the middle': retrieval accuracy as a U-shape over needle position.
import numpy as np
positions = np.linspace(0, 1, 11)
acc = 0.95 - 0.35 * np.sin(np.pi * positions)          # toy U-curve
for p, a in zip(positions, acc):
    print(f"needle at {p:4.0%} of context  -> recall {a:.2f}  " + "#" * int(a * 30))
print("\nPractical rule: put instructions and the most important context at the start or end.")
```

### Context efficiency

Longer prompts cost more money (input tokens), more latency (prefill time) and possibly more distraction. Context efficiency means getting the needed information in with the fewest tokens:

- Retrieve only what is relevant (RAG, Module 6) rather than pasting everything.
- Put critical instructions at the start or end.
- Prefer compact formats (YAML or terse bullet lists over verbose prose).
- Use **prompt caching** for long, repeated prefixes such as system prompts and shared documents (Module 9).

> [!INTERVIEW]
> **"Our model has a 128K context window. Why not just put the whole knowledge base in the prompt instead of building RAG?"** Effective context is shorter than advertised (lost in the middle, RULER). Cost and latency grow with input tokens on every call. Most knowledge bases are larger than any context window and keep changing. Irrelevant context can distract the model and increase hallucination. Long context and RAG are complementary: use retrieval to choose what goes in, and long context to fit more of what matters. Validate with NIAH-style tests on your own data.

## Pitfalls

- Hand-editing few-shot examples inside a giant string instead of keeping them as data.
- Using the wrong chat template, or trusting a framework's default without inspecting the final prompt.
- Assuming the maximum context length equals the usable context length.
- Burying key instructions in the middle of a long prompt.

## Summary

- A prompt combines a task description, examples and the concrete task. Robust models need less prompt fiddling.
- **In-context learning** teaches through context without weight updates (zero-shot vs few-shot). Stronger models need fewer shots, but domain-specific formats still benefit.
- System and user prompts are concatenated with the model's **chat template**. Template mistakes fail silently. System prompts help because they come first and because models are trained on an instruction hierarchy.
- Context windows have grown from 1K to 2M tokens, but models use the **start and end** best. Test with NIAH or RULER on your own data and keep context efficient.

```quiz
[
  {"q": "What does 'in-context learning' mean?", "options": ["Finetuning on context documents", "Learning the desired behavior from instructions/examples in the prompt, with no weight updates", "Training a retriever", "Pre-training on long contexts"], "answer": 1, "explain": "Introduced with GPT-3: the model learns from its prompt without changing weights."},
  {"q": "A prompt with 5 examples of the task is…", "options": ["Zero-shot", "5-shot (few-shot)", "Chain-of-thought", "RAG"], "answer": 1, "explain": "Each example is a shot."},
  {"q": "Why did Microsoft's 2023 analysis find limited gains from few-shot prompting on GPT-4?", "options": ["GPT-4 can't read examples", "Stronger models follow instructions well enough that examples add less", "Examples are banned", "Context was too short"], "answer": 1, "explain": "As models get stronger they need fewer examples, though domain-specific formats can still benefit."},
  {"q": "From the model's perspective, the system prompt and user prompt are…", "options": ["Processed by different networks", "Concatenated into a single sequence via the chat template", "Ignored", "Encrypted separately"], "answer": 1, "explain": "They are joined into one prompt with special role tokens."},
  {"q": "Why are chat-template errors dangerous?", "options": ["They crash the API", "They fail silently: the model still responds reasonably but performance drops", "They increase context length", "They are impossible"], "answer": 1, "explain": "Huyen advises following templates exactly and printing the final prompt to check."},
  {"q": "The 'lost in the middle' finding says models…", "options": ["Use information in the middle best", "Use information at the beginning and end of the prompt better than in the middle", "Ignore the system prompt", "Can't handle 4K tokens"], "answer": 1, "explain": "Recall is U-shaped over position. Put important content at the start or end."},
  {"q": "A needle-in-a-haystack test measures…", "options": ["Tokenizer speed", "Whether the model can retrieve a fact inserted at various positions of a long context", "Hallucination rate on trivia", "Prompt injection robustness"], "answer": 1, "explain": "NIAH inserts a fact at different depths and checks retrieval, revealing effective context length."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 5 ("Introduction to Prompting": in-context learning, system prompt and user prompt, context length and context efficiency).
