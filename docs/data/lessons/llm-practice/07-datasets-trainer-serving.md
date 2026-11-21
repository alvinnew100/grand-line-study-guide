# Datasets, Trainer, Accelerate and serving (TGI, vLLM, Spaces)

> **Before this lesson:** you should be comfortable loading a model and tokenizer with the `Auto`
> classes and calling `generate()`, from
> [Hub, pipelines, Auto classes and generate()](#/lesson/llm-practice/hub-pipelines-generate). The
> ideas of a loss, a gradient and training by small nudges come from
> [From embeddings to scaled dot-product attention](#/lesson/llm-practice/attention-from-scratch),
> and the KV cache from
> [Positional encodings, RoPE, KV cache and architecture families](#/lesson/llm-practice/positions-and-architectures).

## In plain words

Running a model is only one stage of its life. Before it, you collect and clean data and train or
adapt the model; after it, you put the model on a server so that real users can reach it. This
lesson covers those stages with the Hugging Face tools built for each: `datasets` for data,
`Trainer` for the training loop, `Accelerate` for using several chips, and serving engines (vLLM,
TGI) and hosted services for the last mile.

Think of a restaurant. `datasets` is the pantry and the prep station: ingredients arrive in bulk,
are washed and chopped once, and are kept ready. `Trainer` is the head chef's routine that turns
practice into skill, one service at a time. `Accelerate` is opening several kitchens that follow the
same recipe. A serving engine is the front of house: it seats many diners at once, takes new orders
while others are still eating, and never lets a table wait for the slowest diner.

Why it matters for a job: an engineer who can fine-tune a model but cannot estimate its memory,
explain the effective batch size, or say why vLLM is faster than a loop of `generate()` calls will
struggle in a machine-learning interview. These are also the places where money is spent: GPU hours
for training and per-token costs for serving.

## 1. The `datasets` library

A **dataset** here is a table: each **row** is one example (a question and its answer, a document)
and each **column** is one field. A dataset is usually divided into **splits**: `train` for learning,
`validation` for choosing settings and `test` for the final score.

`datasets` stores tables as **Apache Arrow** files. Arrow is a column-by-column binary layout that
programs can read without converting it first. The files are memory-mapped from disk (the operating
system loads only the parts you touch), so a 100 GB dataset does not need 100 GB of **RAM** (the
computer's working memory). Every transformation is also cached under a **fingerprint**, a short code
computed from the input and the function applied, so running the same step twice reuses the saved
result.

```python
from datasets import load_dataset, Dataset, DatasetDict

ds = load_dataset("rajpurkar/squad")                         # DatasetDict with 'train' and 'validation'
print(ds)
print(ds["train"][0])
print(ds["train"].features)                                   # typed schema

local = load_dataset("json", data_files={"train": "train.jsonl", "test": "test.jsonl"})
csv = load_dataset("csv", data_files="faq.csv", split="train")
tiny = Dataset.from_list([{"q": "What is BPE?", "a": "A subword algorithm."}])

stream = load_dataset("HuggingFaceFW/fineweb-edu", split="train", streaming=True)   # IterableDataset
for row in stream.take(3):
    print(row["text"][:80])
```

Line by line: `load_dataset("rajpurkar/squad")` downloads SQuAD, a question-answering dataset, and
returns a `DatasetDict` (a dictionary of splits). `print(ds)` shows each split's row count and
columns, `ds["train"][0]` returns the first row as a dictionary, and `features` lists each column's
type. The next three lines build datasets from your own files: **JSONL** ("JSON lines", one JSON
object per line) and **CSV** (comma-separated values, the spreadsheet export format), or from a
Python list. The last block opens a huge web corpus with `streaming=True`: nothing is downloaded up
front, and `stream.take(3)` fetches only the first three rows.

The core operations are **functional and chainable**: each one returns a new dataset rather than
changing the old one, so you can write them one after another like a recipe:

```python
def tokenize(batch):
    return tok(batch["text"], truncation=True, max_length=512)

ds = (ds["train"]
      .filter(lambda r: len(r["text"]) > 200)              # drop short rows
      .shuffle(seed=42)
      .select(range(50_000))
      .map(tokenize, batched=True, num_proc=8, remove_columns=["text"]))
splits = ds.train_test_split(test_size=0.05, seed=42)
splits.push_to_hub("me/my-clean-corpus", private=True)
```

Read the chain top to bottom: `filter` keeps rows for which the function returns `True` (texts
longer than 200 characters); `shuffle(seed=42)` mixes the order reproducibly (the **seed** fixes the
random generator so every run gives the same order); `select(range(50_000))` keeps the first 50,000
rows; `map(tokenize, ...)` adds token columns, with `truncation=True, max_length=512` cutting any
text longer than 512 tokens. `train_test_split` carves off 5 percent as a test split, and
`push_to_hub(..., private=True)` uploads the result as a private dataset repository.

- `map(batched=True)` passes the function a **dict of lists** (one list per column, covering many
  rows) instead of one row at a time. That is faster, especially with fast tokenizers, which process
  a whole list in one call.
- `num_proc` runs the work in several processes in parallel; results are cached so re-running a
  notebook is instant.
- `remove_columns` drops raw text after tokenising, which matters for collators (the batch builders
  from lesson 5), since they cannot pad a column of strings.
- `with_format("torch")` / `"numpy"` / `"pandas"` controls what indexing returns.
- Streaming (`IterableDataset`) is for corpora too big to download; you lose random access and `len`.

The runnable block below imitates what a batched `map` does, using a fake tokenizer that lowercases,
splits on spaces and turns each word into a number below 1000:

```python-run
# What a batched map does, in plain Python: dict-of-lists in, dict-of-lists out
rows = {"text": ["Attention is all you need", "RoPE rotates queries", "BPE merges pairs"]}
def fake_tokenize(batch):
    toks = [t.lower().split() for t in batch["text"]]
    return {"input_ids": [[hash(w) % 1000 for w in ws] for ws in toks],
            "length": [len(ws) for ws in toks]}
out = {**rows, **fake_tokenize(rows)}
for i in range(3):
    print({k: v[i] for k, v in out.items()})
```

`fake_tokenize` receives the whole column `batch["text"]` and returns two new columns, `input_ids`
and `length`, each a list with one entry per row. `{**rows, **fake_tokenize(rows)}` merges the old
and new columns into one dictionary, and the loop prints row by row: for example
`{'text': 'RoPE rotates queries', 'input_ids': [...], 'length': 3}`. The id numbers differ on every
run because Python deliberately randomises string hashes per process; a real tokenizer's ids are
fixed.

## 2. Trainer: the batteries-included loop

A **training loop** repeats four steps: take a **batch** of examples, run the model to get the loss,
compute the gradients, and let the **optimizer** (the rule that turns gradients into weight updates;
**Adam** and its variant AdamW are the usual choice) nudge the weights. One full pass over the
training data is an **epoch**. The **learning rate** is the size of each nudge.

`Trainer` wraps that PyTorch loop together with everything around it: batching, mixed precision,
gradient accumulation, checkpointing, evaluation, logging and multi-GPU, configured through
`TrainingArguments`. **Mixed precision** does most arithmetic in a 16-bit format such as bfloat16 for
speed while keeping sensitive values in 32 bits. **Gradient accumulation** adds up the gradients of
several small batches before one update (section 5 proves it equals a big batch). **Checkpointing**
saves the model to disk at intervals so a crash does not lose the run.

The example below fine-tunes an encoder classifier (the classic Hugging Face course example) on
MRPC, a task that asks whether two sentences are paraphrases of each other:

```python
import numpy as np, evaluate
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          TrainingArguments, Trainer, DataCollatorWithPadding)
from datasets import load_dataset

ckpt = "answerdotai/ModernBERT-base"
raw = load_dataset("glue", "mrpc")
tok = AutoTokenizer.from_pretrained(ckpt)
data = raw.map(lambda b: tok(b["sentence1"], b["sentence2"], truncation=True), batched=True)
model = AutoModelForSequenceClassification.from_pretrained(ckpt, num_labels=2)

metric = evaluate.load("glue", "mrpc")
def compute_metrics(p):
    preds = np.argmax(p.predictions, axis=-1)
    return metric.compute(predictions=preds, references=p.label_ids)

args = TrainingArguments(
    output_dir="mrpc-modernbert",
    learning_rate=2e-5, per_device_train_batch_size=16, gradient_accumulation_steps=2,
    num_train_epochs=3, weight_decay=0.01, warmup_ratio=0.1, lr_scheduler_type="cosine",
    bf16=True, eval_strategy="epoch", save_strategy="epoch",
    load_best_model_at_end=True, metric_for_best_model="f1", report_to="none",
)
trainer = Trainer(model=model, args=args, train_dataset=data["train"], eval_dataset=data["validation"],
                  processing_class=tok, data_collator=DataCollatorWithPadding(tok),
                  compute_metrics=compute_metrics)
trainer.train()
trainer.push_to_hub()
```

**Reading this code line by line**

- `raw.map(lambda b: tok(b["sentence1"], b["sentence2"], truncation=True), batched=True)` tokenizes
  each sentence pair into one input, the way BERT-style models expect pairs.
- `AutoModelForSequenceClassification.from_pretrained(ckpt, num_labels=2)` adds a fresh two-class
  head (paraphrase or not) on top of ModernBERT.
- `evaluate.load("glue", "mrpc")` loads the official scoring code for this task, which reports
  accuracy and **F1** (a single score that balances how many predicted positives were right against
  how many real positives were found). `compute_metrics` turns the model's logits into predicted
  classes with `argmax` (the index of the largest score) and scores them.
- In `TrainingArguments`: `learning_rate=2e-5` is a small step size, normal for fine-tuning;
  `per_device_train_batch_size=16` with `gradient_accumulation_steps=2` gives 32 examples per
  update; `num_train_epochs=3` reads the data three times; `weight_decay=0.01` gently pulls weights
  towards zero to reduce overfitting; `warmup_ratio=0.1` and `lr_scheduler_type="cosine"` shape the
  learning rate over time (demo below); `bf16=True` turns on mixed precision;
  `eval_strategy="epoch"` and `save_strategy="epoch"` evaluate and save after every epoch;
  `load_best_model_at_end=True` with `metric_for_best_model="f1"` restores the best-scoring
  checkpoint at the end; `report_to="none"` turns off logging to outside services.
- `Trainer(...)` receives the model, the settings, both splits, the tokenizer, a collator that pads
  each batch, and the metric function. `train()` runs everything; `push_to_hub()` uploads the result.

Things to know:

- **Effective batch size** = per-device batch x gradient accumulation steps x number of GPUs.
- `processing_class=` replaced the older `tokenizer=` argument.
- **Dynamic padding** via a data collator pads each batch to its own longest sequence, not to a
  global maximum, which saves a lot of compute.
- `gradient_checkpointing=True` trades about 30 percent more compute for much lower activation memory:
  instead of storing every layer's intermediate results for the backward pass, it stores a few and
  recomputes the rest when needed. (Despite the shared word, this has nothing to do with saving
  checkpoints to disk.)
- TRL's trainers (`SFTTrainer`, `DPOTrainer`, `GRPOTrainer`) **subclass** `Trainer` (they are built
  on it and inherit its behaviour), so everything here carries over to LLM fine-tuning in module 6.

### The learning-rate schedule

A **learning-rate schedule** changes the learning rate during training. The usual shape has two
parts. **Warm-up** raises it from zero to its peak over the first few percent of steps. **Decay**
then lowers it towards zero, either in a straight line (linear) or along half a cosine wave (cosine,
which stays high a little longer and then falls faster). The demo prints both shapes for a run of
1,000 steps with 100 warm-up steps and a peak of $2 \times 10^{-5}$:

```python-run
import numpy as np
total, warm, peak = 1000, 100, 2e-5
steps = np.arange(total)
lin = np.where(steps < warm, peak * steps / warm, peak * (total - steps) / (total - warm))
cos = np.where(steps < warm, peak * steps / warm,
               peak * 0.5 * (1 + np.cos(np.pi * (steps - warm) / (total - warm))))
for s in [0, 50, 100, 300, 550, 800, 999]:
    print(f"step {s:4d}  linear {lin[s]:.2e}  cosine {cos[s]:.2e}")
```

`np.where(condition, a, b)` picks `a` where the condition holds and `b` elsewhere, so each line
computes the warm-up ramp for the first 100 steps and the decay afterwards. In the output both
schedules climb to `2.00e-05` at step 100, agree again at the halfway point of the decay (step 550,
`1.00e-05`), and differ in between: at step 300 cosine is still higher (`1.77e-05` against
`1.56e-05`), while at step 800 it is lower (`2.34e-06` against `4.44e-06`).

Why bother? Warm-up avoids huge early updates while Adam's **moment estimates** (its running
averages of each gradient and of its square, which it uses to scale every step) are still based on
too few batches to be trustworthy. Decay lets the model settle into a **minimum** of the loss, a
low point it would otherwise keep overshooting.

## 3. Accelerate: one script, any hardware

If you write your own loop (custom losses, **RL** meaning reinforcement learning, multi-model setups),
**Accelerate** makes the same code run on a CPU, one GPU, many GPUs, or **TPUs** (Google's AI chips),
with DDP, FSDP or DeepSpeed (explained below), and mixed precision:

```python
from accelerate import Accelerator

accelerator = Accelerator(mixed_precision="bf16", gradient_accumulation_steps=4)
model, optimizer, train_dl, scheduler = accelerator.prepare(model, optimizer, train_dl, scheduler)
model.train()
for batch in train_dl:
    with accelerator.accumulate(model):
        loss = model(**batch).loss
        accelerator.backward(loss)          # replaces loss.backward()
        optimizer.step(); scheduler.step(); optimizer.zero_grad()
accelerator.wait_for_everyone()
accelerator.save_model(model, "out/")
```

What changes compared with a plain PyTorch loop: `accelerator.prepare(...)` wraps the model,
optimizer, data loader and scheduler so they work on whatever hardware the script was launched on;
`accelerator.accumulate(model)` handles gradient accumulation (it only lets the optimizer really
step every fourth batch); `accelerator.backward(loss)` replaces `loss.backward()` so mixed precision
and multi-GPU gradient syncing happen correctly; `wait_for_everyone()` pauses until every GPU has
finished; and `save_model` writes one clean copy of the weights.

Launch with `accelerate config` once, then `accelerate launch train.py`. **Distributed training**
means one training run spread over several GPUs, and there are several strategies, in one sentence
each:

- **DDP** (Distributed Data Parallel): full model copy per GPU, each GPU gets different batches, and
  the gradients are **all-reduced** (summed across GPUs so every copy applies the same update); fits
  when the model plus optimizer state fits on one GPU.
- **FSDP** (Fully Sharded Data Parallel) / **DeepSpeed ZeRO**: **shard** (cut into pieces and spread)
  parameters, gradients and optimizer states across GPUs, gathering each layer's pieces only at the
  moment it is needed; required for full fine-tuning of big models.
- **Tensor / pipeline parallelism**: split individual matrices (tensor) or ranges of layers
  (pipeline) across GPUs; mostly for pretraining and very large inference.

Memory for full fine-tuning with Adam in mixed precision is roughly 16 bytes per parameter: 2 for
the bf16 weights, 2 for the bf16 gradients, 8 for Adam's two moments in 32-bit, and 4 for a "master"
32-bit copy of the weights that receives the precise updates. So a 7B model needs about
7 x 16 = 112 GB before activations, more than any single common GPU holds. That number is the main
motivation for LoRA (module 6), which trains a tiny fraction of the parameters.

## 4. Serving: from notebook to endpoint

**Serving** means running a model as a service: a program that waits for requests over the network
and answers them. The address that clients send requests to is an **endpoint**, and the requests
usually travel over **HTTP**, the protocol of the web.

`model.generate()` processes one batch at a time and wastes the GPU between requests. Production
engines add **continuous batching** (new requests join the running batch at every decode step),
**PagedAttention** (the KV cache is stored in small fixed-size blocks, like pages of memory, so no
space is reserved in advance for text that may never be written), **prefix caching** (the KV cache of
a shared prompt start, such as a long system prompt, is computed once and reused), tensor
parallelism, quantisation **kernels** (hand-optimised GPU routines), speculative decoding and an
**OpenAI-compatible HTTP API**, meaning the same request format as OpenAI's service so existing
client code works unchanged.

**vLLM**:

```bash
pip install vllm
vllm serve Qwen/Qwen3-8B --max-model-len 32768 --tensor-parallel-size 2 \
     --enable-prefix-caching --enable-auto-tool-choice --tool-call-parser hermes
```

The command starts a server for Qwen3-8B. `--max-model-len 32768` caps the context length (and so
the KV-cache memory per request), `--tensor-parallel-size 2` splits the model across two GPUs,
`--enable-prefix-caching` turns on reuse of shared prompt starts, and the two tool flags let the
server recognise tool calls in the model's output and return them in the structured OpenAI format
(lesson 15). The trailing `\` continues the command on the next line.

**Text Generation Inference (TGI)**, Hugging Face's server (now in maintenance mode, with HF
recommending vLLM or SGLang for new deployments, but still widely deployed). It ships as a
**Docker** image, a packaged program that runs the same way on any machine with Docker installed:

```bash
docker run --gpus all -p 8080:80 -v $PWD/data:/data \
  ghcr.io/huggingface/text-generation-inference:latest --model-id Qwen/Qwen3-8B
```

Either way, any OpenAI-style client can talk to it:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")
r = client.chat.completions.create(model="Qwen/Qwen3-8B",
                                   messages=[{"role": "user", "content": "Hi"}], max_tokens=50)
print(r.choices[0].message.content)
```

The client is OpenAI's own Python package pointed at your server: `base_url` is the server's address
(vLLM listens on port 8000 by default), and `api_key` can be any text because a local server does
not check it. `chat.completions.create` sends the messages; the reply text sits in
`r.choices[0].message.content`.

Other deployment options on the HF platform:

- **Inference Providers**: a single client (`huggingface_hub.InferenceClient`) routing to many
  **serverless** providers (you send requests and pay per use, with no servers of your own to run:
  Together, Fireworks, Groq, Cerebras, HF's own...) with your HF **token** (a secret string that
  identifies your account).
- **Inference Endpoints**: dedicated, **autoscaling** (adding or removing machines as traffic
  changes) managed deployments of any Hub model (vLLM, TGI, SGLang or custom containers), with
  **scale-to-zero** (no machines, and no bill, while idle).
- **Spaces**: git repos that run a Gradio, Streamlit, Docker or static app; ideal for demos and
  internal tools, with ZeroGPU for shared GPU bursts. Gradio and Streamlit are Python libraries that
  build a web interface from a few lines of code.

```python
from huggingface_hub import InferenceClient
client = InferenceClient(provider="auto")      # uses HF_TOKEN
resp = client.chat_completion(model="meta-llama/Llama-3.1-8B-Instruct",
                              messages=[{"role": "user", "content": "One fact about BPE"}], max_tokens=60)
print(resp.choices[0].message.content)
```

A minimal Gradio Space (`app.py`):

```python
import gradio as gr
from huggingface_hub import InferenceClient
client = InferenceClient()
def respond(message, history):
    msgs = history + [{"role": "user", "content": message}]
    out = ""
    for chunk in client.chat_completion(msgs, model="Qwen/Qwen3-8B", stream=True, max_tokens=300):
        out += chunk.choices[0].delta.content or ""
        yield out
gr.ChatInterface(respond, type="messages").launch()
```

How the Gradio app works: `respond` receives the new message and the chat `history` (a list of
earlier messages), sends them to the model with `stream=True`, and adds each arriving piece
(`chunk.choices[0].delta.content`, which can be `None`, hence `or ""`) to `out`. Because it uses
`yield` instead of `return`, the function is a **generator**: each `yield` hands the text so far to
Gradio, which redraws the reply, so the user watches it being typed. `gr.ChatInterface(...).launch()`
builds the chat page around that function.

### Local options

Ollama and llama.cpp (GGUF, CPU/Apple Silicon friendly), LM Studio, and MLX on Macs. Great for
development and privacy-sensitive prototypes; not for **high-throughput** serving (serving many
tokens per second to many users).

## 5. What the Trainer does for you, demonstrated

### Gradient accumulation is exactly a bigger batch

When a batch of 32 does not fit in memory, run 4 micro-batches of 8, **sum their gradients**, and step
once. For a loss that is a mean over examples this is mathematically identical to the large batch, as
the demo verifies on a linear model:

```python-run
import numpy as np
rng = np.random.default_rng(0)
X, y = rng.standard_normal((32, 5)), rng.standard_normal(32)
w = np.zeros(5)

def grad(Xb, yb, w):                       # gradient of mean squared error on a batch
    return 2 * Xb.T @ (Xb @ w - yb) / len(yb)

full = grad(X, y, w)
accum = np.zeros(5)
for i in range(0, 32, 8):                  # 4 micro-batches of 8
    accum += grad(X[i:i + 8], y[i:i + 8], w) / 4     # divide by the number of accumulation steps
print("max difference:", float(np.abs(full - accum).max()))
```

The demo uses the simplest possible model, a **linear model** whose prediction is `X @ w`, and the
**mean squared error** loss (the average of the squared prediction errors). `grad` is the textbook
formula for that loss's gradient. `full` is the gradient over all 32 rows at once; the loop computes
it on four slices of 8 rows, divides each by 4 and adds them up. The printed maximum difference is
about `1e-16`, which is rounding noise: the two are the same number.

The division by the number of accumulation steps is what `Trainer` and `accelerator.accumulate` do
internally. Two caveats: layers that use batch statistics (**BatchNorm**, a normalisation layer
common in image models that averages over the batch) are not equivalent, and accumulation gives you
the memory of a small batch but none of the speed of a large one.

### Dynamic padding and length bucketing

Padding every example to the longest in the *dataset* wastes most of the compute on pad tokens. Padding
to the longest in each *batch* helps, and grouping similar lengths together (`group_by_length=True`, or a
length-sorted sampler) helps more:

```python-run
import numpy as np
rng = np.random.default_rng(1)
lengths = np.clip(rng.lognormal(4.0, 0.7, 4096).astype(int), 5, 512)      # realistic skew: many short, few long
B = 32
def padded_tokens(order):
    return sum(lengths[order[i:i + B]].max() * len(order[i:i + B]) for i in range(0, len(order), B))

real = lengths.sum()
shuffled = rng.permutation(len(lengths))
print(f"real tokens                  : {real:>9,}")
print(f"pad to global max (512)      : {512 * len(lengths):>9,}  ({512 * len(lengths) / real:.1f}x)")
print(f"dynamic padding, random order: {padded_tokens(shuffled):>9,}  ({padded_tokens(shuffled) / real:.2f}x)")
print(f"dynamic + length bucketing   : {padded_tokens(np.argsort(lengths)):>9,}  ({padded_tokens(np.argsort(lengths)) / real:.2f}x)")
```

The demo draws 4,096 example lengths from a skewed distribution (`lognormal`: most short, a few
long), capped between 5 and 512 tokens. `padded_tokens(order)` walks through the examples in batches
of 32 and counts what the GPU actually processes: the longest length in each batch times the batch
size. The output compares four numbers. The real content is about 283,000 tokens. Padding everything
to 512 processes 7.4 times that. Padding each random batch to its own longest example still costs
3.66 times. Sorting by length first, so each batch holds similar lengths, brings it to 1.03 times,
nearly no waste.

(Real bucketing shuffles *among* buckets so batches are still random; fully sorted order is shown only
to make the upper bound visible.)

### A debugging table for training runs

| symptom | likely cause | what to check |
|---|---|---|
| loss is `nan` after a few steps | learning rate too high, fp16 overflow, bad labels | lower LR, use bf16, add `max_grad_norm`, inspect a batch |
| loss does not move | LR too low or frozen parameters; labels all `-100` | `print_trainable_parameters()`, decode one batch's labels |
| eval loss rises while train loss falls | overfitting | fewer epochs, more data, lower rank, early stopping |
| out of memory at the first step | batch or sequence too large | smaller batch plus accumulation, gradient checkpointing, shorter `max_length`, 4-bit base |
| out of memory at evaluation only | logits accumulated for every eval example | `eval_accumulation_steps`, `prediction_loss_only=True` |
| training is slow, GPU utilisation low | data loading or tokenisation in the loop | pre-tokenise with `map`, raise `dataloader_num_workers` |
| metrics worse after resuming | scheduler or optimizer state not restored | `resume_from_checkpoint=True` rather than reloading weights |

Terms in the table: **fp16** is an older 16-bit format with a small range, so large values overflow
to infinity, which bf16 avoids; `max_grad_norm` caps the size of each gradient (**gradient
clipping**); **overfitting** is memorising the training examples instead of learning the general
pattern, which shows up as training loss falling while loss on unseen data rises; **early stopping**
ends training when the validation score stops improving.

The single most useful habit: **overfit one small batch first**. If the model cannot drive the loss to
near zero on 16 examples, there is a bug in the data pipeline, labels or template, and no amount of
compute will fix it.

## 6. Why continuous batching wins: a simulation

**Latency** is how long one user waits for an answer; **throughput** is how much work the server
finishes per second. **p95** (95th percentile) latency is the wait that 95 percent of requests beat:
it describes the unlucky users that an average hides.

Static batching waits to fill a batch, then every request in it waits for the **longest** one to finish.
Continuous batching admits a waiting request into a free slot at every decode step. The simulation below
serves the same arrival trace both ways (one unit of time is one decode step; a request needs as many
steps as it has output tokens).

```python-run
import numpy as np
rng = np.random.default_rng(0)
N, SLOTS = 200, 8
arrive = np.cumsum(rng.exponential(1.2, N)).astype(int)          # arrival step of each request
need = np.clip(rng.lognormal(3.0, 0.8, N).astype(int), 2, 300)   # output tokens each request needs

def static_batching():
    t, done, i = 0, np.zeros(N), 0
    while i < N:
        t = max(t, arrive[i])
        batch = [j for j in range(i, min(i + SLOTS, N)) if arrive[j] <= t] or [i]
        t += need[batch].max()                                    # everyone waits for the longest
        done[batch] = t
        i += len(batch)
    return done

def continuous_batching():
    t, done, queue, active, nxt = 0, np.zeros(N), [], {}, 0
    while nxt < N or queue or active:
        while nxt < N and arrive[nxt] <= t:
            queue.append(nxt); nxt += 1
        while queue and len(active) < SLOTS:                      # fill free slots every step
            j = queue.pop(0); active[j] = need[j]
        for j in list(active):
            active[j] -= 1
            if active[j] == 0:
                done[j] = t + 1; del active[j]
        t += 1
    return done

for name, fn in [("static", static_batching), ("continuous", continuous_batching)]:
    lat = fn() - arrive
    print(f"{name:10} mean latency {lat.mean():7.1f} steps   p95 {np.percentile(lat, 95):7.1f}   finished at step {int(fn().max())}")
```

How the simulation works: 200 requests arrive at random times (`arrive`), each needing a random number
of output tokens (`need`), and the server has 8 slots. `static_batching` takes up to 8 waiting
requests, advances the clock by the *longest* of their needs, marks them all done at that moment, and
moves on. `continuous_batching` runs one decode step at a time: it queues new arrivals, fills any
free slot from the queue, subtracts one token from every active request, and retires those that
reach zero. The output shows mean latency falling from about 1,069 to 214 steps, p95 from 1,676 to
378, and the whole trace finishing at step 749 instead of 2,043.

Short requests no longer queue behind long ones, so both mean and tail latency drop sharply and the GPU
stays busy. Real engines add one more constraint that this toy ignores: admitting a request requires
**KV-cache memory**, which is what PagedAttention manages.

## 7. Choosing a deployment option

| option | you manage | best for | watch out for |
|---|---|---|---|
| Inference Providers / serverless APIs | nothing | prototypes, spiky or low volume, many models | per-token price, rate limits, model availability |
| Inference Endpoints (dedicated) | scaling policy | steady traffic, private models, compliance | cold starts with scale-to-zero, GPU hourly cost |
| self-hosted vLLM / SGLang / TGI | everything | high steady volume, custom models, data residency | ops burden, capacity planning, upgrades |
| llama.cpp / Ollama / MLX | a laptop | local development, offline, privacy | throughput, feature gaps versus servers |
| Spaces | an app repo | demos and internal tools | not a production API tier |

A **cold start** is the delay when a scaled-to-zero service must start a machine and load the
weights before it can answer the first request; **data residency** is a legal requirement that data
stay in a given country or region.

The throughput-versus-latency trade-off is the knob behind all of them: larger batches raise tokens per
second per GPU (lower cost per token) but increase each user's **time to first token** (TTFT, the
wait before the first word appears). Decide which you are optimising, set a latency objective (for
example p95 TTFT under one second), and **load-test** (send realistic traffic at the system and
measure) with a realistic distribution of prompt and output lengths rather than a single fixed prompt.

> [!INTERVIEW]
> **"Why is vLLM faster than calling model.generate() in a loop?"** Continuous batching keeps the GPU
> full by adding and retiring sequences at every step; PagedAttention stores the KV cache in
> fixed-size blocks so memory is not fragmented or over-reserved, allowing larger batches; prefix
> caching skips recomputing shared prompts; optimised kernels, CUDA graphs (a recorded sequence of GPU
> operations replayed with little overhead) and speculative decoding cut per-token latency.

## Summary

- `datasets`: Arrow-backed, memory-mapped, cached `map`/`filter`, streaming for huge corpora.
- `Trainer` + `TrainingArguments` handle the loop; TRL trainers build on it.
- Accelerate makes custom loops hardware-agnostic; FSDP/ZeRO shard state for big models.
- Serve with vLLM/SGLang/TGI (continuous batching, PagedAttention, OpenAI-compatible API) or via
  Inference Providers/Endpoints; demo with Spaces.

## Glossary

- **Split**: a named part of a dataset, such as train, validation or test.
- **Apache Arrow**: a column-based binary table format that can be read straight from disk.
- **Fingerprint**: a code computed from data and a transformation, used to cache results.
- **Streaming dataset**: rows fetched on demand instead of downloading the whole dataset.
- **Batch / epoch**: a group of examples processed together / one full pass over the training data.
- **Optimizer / Adam**: the rule that turns gradients into weight updates / the most common such rule.
- **Learning rate / schedule / warm-up**: the update step size / how it changes over training / the
  initial ramp up from zero.
- **Mixed precision**: computing mostly in 16-bit numbers while keeping key values in 32-bit.
- **Gradient accumulation**: summing gradients from several small batches before one update.
- **Effective batch size**: per-device batch x accumulation steps x number of GPUs.
- **Dynamic padding / length bucketing**: padding to the longest in each batch / grouping similar
  lengths into the same batch.
- **Gradient checkpointing**: storing fewer activations and recomputing them to save memory.
- **DDP / FSDP / ZeRO**: copy the whole model on every GPU / shard the model and its training state
  across GPUs (two implementations).
- **Serving / endpoint**: running a model as a network service / the address clients call.
- **Continuous batching**: letting requests join and leave the running batch at every decode step.
- **PagedAttention / prefix caching**: storing the KV cache in small blocks / reusing the cache of a
  shared prompt start.
- **Latency / throughput / p95 / TTFT**: one user's wait / work done per second / the wait 95% of
  requests beat / time to first token.
- **Serverless / scale-to-zero / cold start**: pay-per-use with no servers to run / no machines while
  idle / the delay to start one again.

## Check yourself

```quiz
[
  {"q": "Why can datasets handle corpora larger than RAM?",
   "options": ["Arrow tables are memory-mapped from disk", "It compresses everything into GPU memory", "It samples randomly", "It deletes old rows"], "answer": 0,
   "explain": "Memory mapping lets the OS page data in on demand; streaming mode avoids even the download."},
  {"q": "per_device_train_batch_size=8, gradient_accumulation_steps=4, 2 GPUs. Effective batch size?",
   "options": ["64", "32", "16", "8"], "answer": 0,
   "explain": "8 x 4 x 2 = 64 examples contribute to each optimizer step."},
  {"q": "What does a padding data collator such as DataCollatorWithPadding provide?",
   "options": ["Dynamic padding to the longest sequence in each batch", "Fixed padding to 512 tokens", "Tokenization", "Label smoothing"], "answer": 0,
   "explain": "Padding per batch avoids wasting compute on padding up to a global maximum."},
  {"q": "Roughly how much memory does full fine-tuning with Adam in mixed precision need per parameter?",
   "options": ["About 16 bytes", "About 2 bytes", "About 4 bytes", "About 64 bytes"], "answer": 0,
   "explain": "bf16 weights and grads plus fp32 master weights and two fp32 Adam moments add up to about 16 bytes."},
  {"q": "Which serving technique lets new requests join a running batch at every decode step?",
   "options": ["Continuous batching", "Static batching", "Beam search", "Gradient accumulation"], "answer": 0,
   "explain": "Iteration-level scheduling keeps GPU utilisation high with variable-length requests."},
  {"q": "What is a Hugging Face Space?",
   "options": ["A git repo that hosts a running app such as Gradio or Docker", "A dataset format", "A tokenizer type", "A GPU instance type"], "answer": 0,
   "explain": "Spaces host demos and apps; pushes redeploy them."}
]
```

> **Source:** Datasets docs (https://huggingface.co/docs/datasets), Transformers Trainer docs
> (https://huggingface.co/docs/transformers/main_classes/trainer), Accelerate docs
> (https://huggingface.co/docs/accelerate), TGI docs (https://huggingface.co/docs/text-generation-inference),
> Inference Providers docs (https://huggingface.co/docs/inference-providers), Hub Spaces docs; HF LLM
> Course ch. 3 "Fine-tuning a pretrained model" and ch. 5 "The Datasets library"; Huyen, *AI
> Engineering*, ch. 7 (memory math) and ch. 9 (batching, serving).
