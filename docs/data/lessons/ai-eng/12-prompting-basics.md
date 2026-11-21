# Prompts, in-context learning and context length

> **Before this lesson:** you should know what a token, a prompt and a model's weights are (see [From language models to foundation models](#/lesson/ai-eng/aie-rise)), and that post-training teaches a model to follow instructions (see [Post-training: SFT and preference finetuning](#/lesson/ai-eng/aie-post-training)). It helps to have read [Designing your evaluation pipeline](#/lesson/ai-eng/aie-eval-pipeline), because every prompt change should be checked with evaluation. The Python here builds strings and adds numbers; each line is explained.

## In plain words

A **prompt** is everything you send to a model in one request: your instructions, any examples, any background material, and the user's actual question. **Prompt engineering** is the craft of writing prompts that make a model do what you want, reliably. It is the first way to adapt a model to your task, because it changes nothing inside the model: no training, little data, and results in minutes rather than weeks.

An everyday picture: briefing a talented temp worker on their first morning. You cannot rewire their brain (that would be training), but you can tell them clearly what the job is, show them two or three finished examples, hand them the files they need, and put the most important rule at the top of the note where they will see it. A vague note gets vague work; a clear one with good examples gets good work. A prompt is that note.

Why this matters for a job: prompt work is daily work for an AI engineer, and Huyen warns that it is often dismissed as "fiddling with words" and done carelessly. A prompt is a piece of software: it should be **systematic, versioned and evaluated**. Interviewers ask what in-context learning is, why the system prompt matters, and why you should not stuff an entire knowledge base into a long context window. This lesson covers what a prompt is made of, in-context learning, system and user prompts and the chat templates that join them, and how the length of a prompt, and where things sit inside it, affects what the model uses.

> [!NOTE]
> Context engineering, where you assemble the right information, tools and memory for each call (including protocols such as MCP), is covered in depth in the **LLM Practice** track. This module follows Huyen's treatment of prompts themselves.

## 1. Anatomy of a prompt

A prompt is an instruction given to a model to perform a task. It usually contains one or more of three parts:

1. **Task description**: what the model should do, including the role it should play and the format of the output.
2. **Examples** of the task done well. To detect toxic comments, for instance, you might show a few toxic and non-toxic comments with their labels.
3. **The task itself**: the concrete input, such as the question to answer or the document to summarise.

Here are the three parts in a single short prompt:

```text
You are a support assistant. Classify each message as BILLING, TECHNICAL or OTHER.   <- task description
Message: "I was charged twice this month."  Label: BILLING                           <- example
Message: "The app crashes when I log in."  Label:                                    <- the task
```

For prompting to work, the model must be able to **follow instructions**, a skill added during post-training. How much prompt engineering you need depends on how **robust** the model is: how little its output changes when the prompt changes in ways that should not matter. Such harmless changes are called **perturbations**. If writing "5" instead of "five" changes the answer, the model is fragile. You can measure robustness by perturbing prompts on purpose and checking how much the outputs move. Stronger models are generally more robust, which saves you fiddling time.

> [!TIP]
> Experiment with structure. Huyen notes that most models, GPT-4 included, empirically do better when the task description is at the **beginning** of the prompt, while some (for example Llama 3) seemed to do better with it at the **end**. Test both on your evaluation set rather than assuming.

## 2. In-context learning: zero-shot and few-shot

Teaching a model through its prompt is called **in-context learning** (ICL). The term comes from the GPT-3 paper, "Language Models Are Few-shot Learners" (Brown and colleagues, 2020). GPT-3 had been trained only to predict the next token, yet when shown examples in its prompt it could translate, answer reading-comprehension questions, do simple maths and answer SAT exam questions, all with **no change to its weights**. "Learning" here means the model picked up the pattern from the prompt for this one request; nothing is remembered afterwards.

- Each example in the prompt is called a **shot**. A prompt with five examples is **5-shot**; with none it is **zero-shot**. "Few-shot" means a handful.
- ICL is a form of **continual learning**, learning new things after training has finished. A model trained before a library's latest release can still use its new features if you put the new documentation in its prompt, so it can answer beyond its **training cutoff** (the date its training data stops).
- More examples usually help, but they cost tokens and space in the prompt. For GPT-3, few-shot clearly beat zero-shot. For GPT-4 and models like it, a 2023 analysis by Microsoft found only small gains from few-shot prompting on general tasks, because stronger models follow plain instructions well. **Domain-specific** formats still benefit: if a model has rarely seen a niche tool, such as the Ibis dataframe library, a few examples help a lot.

> [!NOTE]
> **Prompt versus context.** Usage varies. In the GPT-3 paper, "context" means the whole input. Elsewhere, the *context* is the background information (retrieved documents, conversation history) and the *prompt* is the whole input. Huyen uses *prompt* for the whole input and *context* for the information supplied to help with the task. This track follows her.

Few-shot prompts should be built by code from a list of examples, not hand-edited as one giant string. Then you can add, remove, reorder and count examples, and every example is guaranteed the same layout.

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

**Reading this Python line by line**

- `examples` is a list of `(review, label)` pairs: the shots, stored as data.
- `task` holds the task description.
- In `build(review, k)`, `examples[:k]` takes the first `k` examples. For each pair, the f-string `f"Review: {r}\nLabel: {l}"` fills in the review and label; `\n` is a line break. `"\n\n".join(...)` glues the formatted examples together with a blank line between them.
- The `return` line uses Python's conditional expression `A if condition else B`: with `k` greater than zero it includes the shots; with `k = 0` it leaves them out.
- The prompt ends with `Label:` and nothing after it, inviting the model to write the label next. A language model completes text, so ending on the exact spot where the answer belongs is a simple, effective trick.
- Output: first the zero-shot prompt (task, then the review, then `Label:`), a line of dashes, then the 3-shot prompt with the three labelled examples in between.

## 3. System prompt and user prompt

Most model APIs split a request into roles:

- a **system prompt**: the task description, role, rules and constraints, written by the application's developer and the same for every user; and
- a **user prompt**: the task input, usually typed by the end user.

For example, a real-estate assistant's system prompt might say: "You are an experienced real estate agent. Read each disclosure carefully, assess the condition of the property, and answer concisely." The user prompt then holds a specific property disclosure and the user's question. In code, the roles are a list of messages, shown here as a static example because it needs an account and a network connection:

```python
messages = [
    {"role": "system", "content": "You are an experienced real estate agent. Answer concisely."},
    {"role": "user",   "content": "Disclosure: roof replaced 1962. Is the roof a concern?"},
]
reply = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
```

### Chat templates

The model itself does not see a list of messages. Under the hood, the system and user prompts are **joined into one sequence of tokens** using the model's **chat template**: a fixed layout that uses **special tokens** (reserved tokens that never occur in normal text) to mark where each role's message starts and ends. Llama 2 wraps the system message in `<<SYS>>` tags inside `[INST] … [/INST]`; Llama 3 uses headers such as `<|start_header_id|>system<|end_header_id|>`. Every model family has its own template, and templates can change between versions of the same family.

Template mistakes are common and silent: the model still does *something* reasonable, so you may never notice that quality dropped. Even an extra line break can change behaviour noticeably. Huyen's practices:

- Follow the model's chat template **exactly** when you build raw prompts yourself.
- If a third-party tool builds prompts for you, **check that it uses the right template**.
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

**Reading this Python line by line**

- `bos="<s>"` is a default argument: a *beginning-of-sequence* token that many models expect at the very start.
- For each message, the f-string writes a role marker such as `<|system|>`, the message text with surrounding spaces removed by `.strip()`, and an `<|end|>` marker.
- The final `<|assistant|>` line with nothing after it is the *generation prompt*: it tells the model that the assistant speaks next, so its continuation becomes the reply.
- Output: `<s>`, then the system block, the user block, and an open `<|assistant|>` line. This is the single string the model really reads. Real templates differ in their exact tokens, which is why you must use each model's own.

With the open source Hugging Face `transformers` library, the correct template is applied for you from the model's configuration (static example; it downloads a tokenizer):

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
print(text)        # always look at the real string before trusting it
```

### Why do system prompts help?

If the model sees one sequence anyway, why should instructions in the system part carry more weight? Huyen gives two likely reasons:

1. The system prompt comes **first**, and models may be better at following instructions that appear first.
2. Models may be **post-trained to prioritise** system prompts. OpenAI's "Instruction Hierarchy" paper (Wallace and colleagues, 2024) trains models to rank system instructions above user instructions, and user instructions above text returned by tools. This also helps defend against prompt attacks, covered in [Defensive prompt engineering](#/lesson/ai-eng/aie-prompt-defense).

## 4. Context length and context efficiency

The **context length** (or **context window**) is the maximum number of tokens a model can take in one request, prompt and output together. Context lengths have exploded. The first three GPT generations had 1K, 2K and 4K tokens (K means thousand). Within about five years the range went from GPT-2's 1K to Gemini 1.5 Pro's **2M** (two million), a 2,000-fold increase. For scale: 100K tokens holds a moderate book (Huyen's book is about 120,000 words, roughly 160,000 tokens), and 2M tokens holds about 2,000 Wikipedia pages or a codebase the size of PyTorch.

### Not all positions are equal

A long window does not mean the model uses every part of it equally well. Models are much better at using information near the **beginning and end** of the prompt than in the **middle**. This is the "lost in the middle" finding (Liu and colleagues, 2023). Two common ways to test it:

- **Needle in a haystack (NIAH)**: insert a random fact (the needle) at different positions in a long prompt (the haystack) and ask the model to retrieve it. Plot accuracy against position and context length.
- **RULER** (Hsieh and colleagues, 2024): a broader set of long-context tasks. It found that a model's *effective* context length, the length at which it still performs well, is often far shorter than its advertised maximum.

Huyen recommends running NIAH-style tests with **your own data**. For a medical assistant, for example, put a fact from a patient's visit notes at different positions in a long medical record and ask the model about it.

```python-run
# Simulated 'lost in the middle': retrieval accuracy as a U-shape over needle position.
import numpy as np
positions = np.linspace(0, 1, 11)
acc = 0.95 - 0.35 * np.sin(np.pi * positions)          # toy U-curve
for p, a in zip(positions, acc):
    print(f"needle at {p:4.0%} of context  -> recall {a:.2f}  " + "#" * int(a * 30))
print("\nPractical rule: put instructions and the most important context at the start or end.")
```

This demo draws an invented curve rather than calling a model. `np.linspace(0, 1, 11)` makes 11 evenly spaced positions from 0 (start) to 1 (end). `np.sin(np.pi * positions)` is 0 at both ends and 1 in the middle, so subtracting it from 0.95 creates a dip in the middle. `"#" * int(a * 30)` repeats the `#` character to draw a crude bar chart. Output: recall 0.95 at the start and end, falling to 0.60 at the middle. Real curves from NIAH tests often look like this, and the dip deepens as the context gets longer.

### Context efficiency

Longer prompts cost more money (you pay for every input token), add latency (the model must process the whole prompt before writing its first token, a phase called **prefill**), and can distract the model. **Context efficiency** means fitting the needed information in with the fewest tokens:

- Retrieve only what is relevant (RAG, Module 6) rather than pasting everything.
- Put critical instructions at the start or end.
- Prefer compact formats, such as YAML or terse bullet lists, over verbose prose.
- Use **prompt caching**, where the provider stores the processed form of a long, repeated beginning of the prompt (a system prompt, a shared document) so it is not recomputed on every call (Module 9).

> [!INTERVIEW]
> **"Our model has a 128K context window. Why not put the whole knowledge base in the prompt instead of building RAG?"** Effective context is shorter than advertised (lost in the middle, RULER). Cost and latency grow with input tokens on every call. Most knowledge bases are larger than any context window and keep changing. Irrelevant context can distract the model and increase hallucination. Long context and RAG are complementary: use retrieval to choose what goes in, and long context to fit more of what matters. Validate with NIAH-style tests on your own data.

## 5. Few-shot prompting: what goes wrong and how to fix it

Few-shot examples are powerful because the model imitates them closely. That is also how they cause trouble. The patterns below are well documented in the prompting literature and are worth testing whenever you add examples.

| Failure | What it looks like | Mitigation |
|---|---|---|
| **Majority label bias** | Four of five examples are POSITIVE, and the model over-predicts POSITIVE | Balance the labels across examples |
| **Recency bias** | The model favours the label of the last example | Shuffle example order, or test several orders and keep the most stable |
| **Surface copying** | Every example answer is one sentence, so the model never writes two, even when needed | Vary length and format across examples in the ways you want the output to vary |
| **Unrepresentative examples** | Examples are clean and short, but real inputs are long and messy | Draw examples from production data, including typos and edge cases |
| **Format drift** | The examples use `Label:` and the final line uses `Answer:` | Build the prompt from one template so every shot has an identical structure |
| **Leaking the answer** | An example is nearly identical to the test input | Remove examples that duplicate items in your evaluation set |

Example order and balance are cheap to test, because you only change the prompt. The demo below uses a stand-in "model" (a *stub*: a fake that imitates one behaviour) which copies the most recent example's label when it is unsure, to show how you would measure sensitivity to order.

```python-run
import itertools
examples = [("great battery", "POSITIVE"), ("screen cracked on day one", "NEGATIVE"),
            ("fast delivery", "POSITIVE"), ("stopped charging", "NEGATIVE")]
tests = [("love it", "POSITIVE"), ("broke quickly", "NEGATIVE"), ("works fine", "POSITIVE"), ("terrible support", "NEGATIVE"),
         ("okay I guess", "POSITIVE"), ("does the job", "POSITIVE")]
def stub_model(shots, text):
    clear = {"love it": "POSITIVE", "broke quickly": "NEGATIVE", "works fine": "POSITIVE", "terrible support": "NEGATIVE"}
    return clear.get(text, shots[-1][1])          # on ambiguous inputs it copies the label of the LAST example
accs = [sum(stub_model(order, t) == y for t, y in tests) / len(tests) for order in itertools.permutations(examples)]
print(f"accuracy over {len(accs)} example orders: min {min(accs):.2f}  max {max(accs):.2f}  mean {sum(accs)/len(accs):.2f}")
print("Report the mean and the spread. A large spread means the prompt (or model) is order-sensitive.")
```

**Reading this Python line by line**

- `itertools.permutations(examples)` produces every possible ordering of the four examples: $4 \times 3 \times 2 \times 1 = 24$ orders.
- `stub_model` answers the four clear-cut test inputs correctly from a lookup table. For anything else, `clear.get(text, shots[-1][1])` falls back to the label of the last example (`shots[-1]` is the last pair, `[1]` its label).
- The list comprehension scores each order on the six tests: `stub_model(order, t) == y` is `True` when the prediction matches the correct label.
- Output: across 24 orders, accuracy ranges from 0.67 to 1.00, mean 0.83. Nothing changed except the order of the same four examples. With a real model you would run the same loop with real API calls on your evaluation set.

### How many examples?

There is no fixed number. Start with zero-shot, add examples for the cases the model gets wrong, and stop when the evaluation score stops improving. Each example has a recurring cost, because it is sent with every request. If you need dozens of examples to hold a format or style, the behaviour may be better taught by finetuning (Module 7), where the examples are paid for once during training.

## 6. Budgeting the context window

The context window is shared by everything in the request: the system prompt, examples, retrieved documents, conversation history, the user's message, *and the output*, which must also fit. Running out is a common production failure: either the request is rejected, or the oldest history is silently cut off and the model "forgets" its instructions. A **token budget** is a plan for how many tokens each part may use.

In words: the spare room (*slack*) is the window size minus everything you put in, minus the room reserved for the answer.

```python-run
def slack(limit, system, examples, history, retrieved, user, max_output):
    return limit - (system + examples + history + retrieved + user) - max_output
limit = 8000
parts = dict(system=900, examples=1200, history=1000, retrieved=2400, user=300, max_output=800)
print(f"turn 0: slack {slack(limit, **parts)} tokens")
for turn in range(1, 6):                          # each turn adds about 450 tokens of history
    parts["history"] += 450
    s = slack(limit, **parts)
    print(f"turn {turn}: slack {s:5d}" + ("   <- over budget: summarize or drop old history" if s < 0 else ""))
```

**Reading this Python line by line**

- `slack(...)` is the formula above as a function with one argument per part.
- `parts = dict(...)` stores the token count of each part in a dictionary. `slack(limit, **parts)` unpacks the dictionary so that each key becomes the matching named argument.
- Each loop pass simulates one more conversation turn adding 450 tokens of history, then recomputes the slack.
- Output: 1,400 tokens spare at the start, then 950, 500 and 50, then −400 at turn 4: the request no longer fits. Worked by hand for turn 0: $8000 - (900 + 1200 + 1000 + 2400 + 300) - 800 = 8000 - 5800 - 800 = 1400$.

Practical rules that follow:

- **Reserve the output budget first.** A response cut off at the token limit often breaks structured output such as JSON.
- **Give each part a cap.** Decide how many tokens retrieval and history may use, and enforce it in code.
- **Trim the least valuable content first.** Old conversation turns can be summarised (Module 6 covers memory strategies). The system prompt and the current question should never be what gets cut.
- **Count tokens with the target model's tokenizer.** Word counts are off by a quarter or more, and by far more for code and non-English text.
- **Remember the cost.** Everything in the window is paid for on every call. A 2,000-token block of examples at one million calls a day is two billion input tokens a day.

## Pitfalls

- Hand-editing few-shot examples inside a giant string instead of keeping them as data.
- Using the wrong chat template, or trusting a framework's default without inspecting the final prompt.
- Assuming the maximum context length equals the usable context length.
- Burying key instructions in the middle of a long prompt.
- Forgetting to leave room for the output in the context budget.

## Summary

- A prompt combines a task description, examples and the concrete task. Robust models need less prompt fiddling.
- **In-context learning** teaches through the prompt without weight updates (zero-shot versus few-shot). Stronger models need fewer shots, but domain-specific formats still benefit.
- System and user prompts are joined into one sequence by the model's **chat template**. Template mistakes fail silently. System prompts help because they come first and because models are trained on an instruction hierarchy.
- Context windows grew from 1K to 2M tokens, but models use the **start and end** best. Test with NIAH or RULER on your own data, keep context efficient, and budget the window with room for the output.

## Glossary

- **Prompt**: everything sent to the model in one request.
- **Prompt engineering**: writing prompts that make a model behave as wanted, without changing its weights.
- **Task description**: the part of a prompt that says what to do, in what role and format.
- **Robustness / perturbation**: how little output changes under harmless prompt changes / such a change.
- **In-context learning (ICL)**: picking up a task from instructions and examples in the prompt, for that request only.
- **Shot / zero-shot / few-shot**: one example in the prompt / no examples / a handful.
- **Continual learning**: learning new information after training has ended.
- **Training cutoff**: the date the model's training data stops.
- **Context**: here, the supporting information supplied in the prompt.
- **System prompt / user prompt**: developer-written instructions shared by every request / the end user's input.
- **Chat template**: the model-specific layout that joins role messages into one token sequence.
- **Special token**: a reserved token used for structure, such as marking a role or the start of a sequence.
- **Generation prompt**: the open assistant marker at the end of a rendered chat, where the model starts writing.
- **Instruction hierarchy**: training a model to rank system over user over tool instructions.
- **Context length (context window)**: the maximum tokens a model handles in one request, input and output together.
- **Lost in the middle**: models use information at the start and end of a prompt better than in the middle.
- **Needle in a haystack (NIAH) / RULER**: tests of whether a model can find facts placed deep in long prompts.
- **Effective context length**: the length at which a model still performs well.
- **Prefill**: the model processing the whole prompt before producing the first output token.
- **Context efficiency**: fitting the needed information into as few tokens as possible.
- **Prompt caching**: reusing the processed form of a repeated prompt prefix.
- **Token budget**: a plan for how many tokens each part of a request may use.
- **Stub**: a simple fake component that imitates one behaviour for testing.

```quiz
[
  {"q": "What does 'in-context learning' mean?", "options": ["Finetuning on context documents", "Learning the desired behaviour from instructions/examples in the prompt, with no weight updates", "Training a retriever", "Pre-training on long contexts"], "answer": 1, "explain": "Introduced with GPT-3: the model picks up the task from its prompt without changing weights."},
  {"q": "A prompt with 5 examples of the task is…", "options": ["Zero-shot", "5-shot (few-shot)", "Chain-of-thought", "RAG"], "answer": 1, "explain": "Each example is a shot."},
  {"q": "Why did Microsoft's 2023 analysis find limited gains from few-shot prompting on GPT-4?", "options": ["GPT-4 can't read examples", "Stronger models follow instructions well enough that examples add less", "Examples are banned", "Context was too short"], "answer": 1, "explain": "As models get stronger they need fewer examples, though domain-specific formats can still benefit."},
  {"q": "From the model's perspective, the system prompt and user prompt are…", "options": ["Processed by different networks", "Joined into a single sequence via the chat template", "Ignored", "Encrypted separately"], "answer": 1, "explain": "They are concatenated into one prompt with special role tokens."},
  {"q": "Why are chat-template errors dangerous?", "options": ["They crash the API", "They fail silently: the model still responds reasonably but performance drops", "They increase context length", "They are impossible"], "answer": 1, "explain": "Huyen advises following templates exactly and printing the final prompt to check."},
  {"q": "The 'lost in the middle' finding says models…", "options": ["Use information in the middle best", "Use information at the beginning and end of the prompt better than in the middle", "Ignore the system prompt", "Can't handle 4K tokens"], "answer": 1, "explain": "Recall is U-shaped over position. Put important content at the start or end."},
  {"q": "A needle-in-a-haystack test measures…", "options": ["Tokenizer speed", "Whether the model can retrieve a fact inserted at various positions of a long context", "Hallucination rate on trivia", "Prompt injection robustness"], "answer": 1, "explain": "NIAH inserts a fact at different depths and checks retrieval, revealing effective context length."},
  {"q": "An 8,000-token window holds 5,800 tokens of prompt and you reserve 800 for output. How much slack is left?", "options": ["2,200", "1,400", "800", "0"], "answer": 1, "explain": "8,000 − 5,800 − 800 = 1,400 tokens of spare room."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 5 ("Introduction to Prompting": in-context learning, system prompt and user prompt, context length and context efficiency).
