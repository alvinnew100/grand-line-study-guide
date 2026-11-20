# Datasets, Trainer, Accelerate and serving (TGI, vLLM, Spaces)

The previous lesson ran models. This one covers the rest of the loop: loading and transforming data at
scale with `datasets`, training with `Trainer`, scaling across devices with `Accelerate`, and putting
a model behind an endpoint with Text Generation Inference, vLLM, Inference Providers or a Space.

## 1. The `datasets` library

`datasets` stores tables as **Apache Arrow** files that are memory-mapped from disk, so a 100 GB
dataset does not need 100 GB of RAM, and transformations are cached by fingerprint.

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

The core operations are functional and chainable:

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

- `map(batched=True)` passes dicts of lists (fast, especially with fast tokenizers).
- `num_proc` parallelises; results are cached so re-running a notebook is instant.
- `remove_columns` drops raw text after tokenising, which matters for collators.
- `with_format("torch")` / `"numpy"` / `"pandas"` controls what indexing returns.
- Streaming (`IterableDataset`) is for corpora too big to download; you lose random access and `len`.

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

## 2. Trainer: the batteries-included loop

`Trainer` wraps the PyTorch training loop: batching, mixed precision, gradient accumulation,
checkpointing, evaluation, logging and multi-GPU, configured through `TrainingArguments`.
Fine-tuning an encoder classifier (the classic HF course example):

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

Things to know:

- **Effective batch size** = per-device batch x gradient accumulation steps x number of GPUs.
- `processing_class=` replaced the older `tokenizer=` argument.
- **Dynamic padding** via a data collator pads each batch to its own longest sequence, not to a
  global maximum, which saves a lot of compute.
- `gradient_checkpointing=True` trades about 30 percent more compute for much lower activation memory.
- TRL's trainers (`SFTTrainer`, `DPOTrainer`, `GRPOTrainer`) subclass `Trainer`, so everything here
  carries over to LLM fine-tuning in module 6.

### The learning-rate schedule

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

Warm-up avoids huge early updates while Adam's moment estimates are still noisy; decay lets the model
settle into a minimum.

## 3. Accelerate: one script, any hardware

If you write your own loop (custom losses, RL, multi-model setups), **Accelerate** makes the same code
run on CPU, one GPU, many GPUs, TPUs, with DDP, FSDP or DeepSpeed, and mixed precision:

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

Launch with `accelerate config` once, then `accelerate launch train.py`. Distributed strategies in one
sentence each:

- **DDP**: full model copy per GPU, gradients all-reduced; fits when the model plus optimizer state fits
  on one GPU.
- **FSDP / DeepSpeed ZeRO**: shard parameters, gradients and optimizer states across GPUs, gathering
  layers just in time; needed for full fine-tuning of big models.
- **Tensor / pipeline parallelism**: split individual matrices or layer ranges across GPUs; mostly for
  pretraining and very large inference.

Memory for full fine-tuning with Adam in mixed precision is roughly 16 bytes per parameter (weights,
gradients, two Adam moments, master fp32 copy), so a 7B model needs about 112 GB before activations.
That number is the main motivation for LoRA (module 6).

## 4. Serving: from notebook to endpoint

`model.generate()` processes one batch at a time and wastes the GPU between requests. Production
engines add **continuous batching** (new requests join the running batch at every decode step),
**PagedAttention** KV memory, prefix caching, tensor parallelism, quantisation kernels, speculative
decoding and an **OpenAI-compatible HTTP API**.

**vLLM**:

```bash
pip install vllm
vllm serve Qwen/Qwen3-8B --max-model-len 32768 --tensor-parallel-size 2 \
     --enable-prefix-caching --enable-auto-tool-choice --tool-call-parser hermes
```

**Text Generation Inference (TGI)**, Hugging Face's server (now in maintenance mode, with HF
recommending vLLM or SGLang for new deployments, but still widely deployed):

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

Other deployment options on the HF platform:

- **Inference Providers**: a single client (`huggingface_hub.InferenceClient`) routing to many
  serverless providers (Together, Fireworks, Groq, Cerebras, HF's own...) with your HF token.
- **Inference Endpoints**: dedicated, autoscaling managed deployments of any Hub model (vLLM, TGI,
  SGLang or custom containers), with scale-to-zero.
- **Spaces**: git repos that run a Gradio, Streamlit, Docker or static app; ideal for demos and
  internal tools, with ZeroGPU for shared GPU bursts.

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

### Local options

Ollama and llama.cpp (GGUF, CPU/Apple Silicon friendly), LM Studio, and MLX on Macs. Great for
development and privacy-sensitive prototypes; not for high-throughput serving.

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

The division by the number of accumulation steps is what `Trainer` and `accelerator.accumulate` do
internally. Two caveats: layers that use batch statistics (BatchNorm) are not equivalent, and
accumulation gives you the memory of a small batch but none of the speed of a large one.

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

The single most useful habit: **overfit one small batch first**. If the model cannot drive the loss to
near zero on 16 examples, there is a bug in the data pipeline, labels or template, and no amount of
compute will fix it.

## 6. Why continuous batching wins: a simulation

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

The throughput-versus-latency trade-off is the knob behind all of them: larger batches raise tokens per
second per GPU (lower cost per token) but increase each user's time to first token. Decide which you are
optimising, set a latency objective (for example p95 TTFT under one second), and load-test with a
realistic distribution of prompt and output lengths rather than a single fixed prompt.

> [!INTERVIEW]
> **"Why is vLLM faster than calling model.generate() in a loop?"** Continuous batching keeps the GPU
> full by adding and retiring sequences at every step; PagedAttention stores the KV cache in
> fixed-size blocks so memory is not fragmented or over-reserved, allowing larger batches; prefix
> caching skips recomputing shared prompts; optimised kernels, CUDA graphs and speculative decoding
> cut per-token latency.

## Summary

- `datasets`: Arrow-backed, memory-mapped, cached `map`/`filter`, streaming for huge corpora.
- `Trainer` + `TrainingArguments` handle the loop; TRL trainers build on it.
- Accelerate makes custom loops hardware-agnostic; FSDP/ZeRO shard state for big models.
- Serve with vLLM/SGLang/TGI (continuous batching, PagedAttention, OpenAI-compatible API) or via
  Inference Providers/Endpoints; demo with Spaces.

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
