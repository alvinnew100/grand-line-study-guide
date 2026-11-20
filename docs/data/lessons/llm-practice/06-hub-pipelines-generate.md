# Hub, pipelines, Auto classes and generate()

The Hugging Face stack is the de facto standard toolkit for open models: the **Hub** hosts weights,
datasets and demos; **Transformers** loads and runs models; **Tokenizers**, **Datasets**, **PEFT**,
**TRL** and **Accelerate** cover the rest of the lifecycle. This lesson is a guided tour of the
inference side, with the code you will actually type. Code blocks here are static (they need a GPU or
network), but every concept is backed by a runnable numpy demo.

> [!NOTE]
> Versions move fast. This lesson follows **Transformers v5** (released late 2025): PyTorch-only,
> `dtype=` instead of the older `torch_dtype=`, and `dtype="auto"` by default when loading. If you
> read older tutorials, translate `torch_dtype` to `dtype`.

## 1. The Hub: repos, revisions, model cards

Every model, dataset and Space is a **git repository** (with large files in Xet/LFS storage):

- `meta-llama/Llama-3.1-8B-Instruct` is `<namespace>/<repo>`. Pin a **revision** (branch, tag or
  commit sha) in production so an upstream push cannot change your model: `from_pretrained(id,
  revision="a1b2c3d")`.
- **Model cards** (`README.md` with YAML metadata) document intended use, training data, evaluation,
  limitations, license and the `library_name` / `pipeline_tag` that drive the Hub widgets. Read the
  license (gated models such as Llama require accepting terms) before shipping.
- **Formats**: `safetensors` (safe, memory-mapped; prefer it over pickle-based `.bin`, which can run
  arbitrary code on load), GGUF (llama.cpp/Ollama), ONNX, MLX.
- `trust_remote_code=True` executes Python shipped in the repo. Treat it like installing a package
  from a stranger: pin a revision and review the code.

The `huggingface_hub` library is the programmatic interface:

```python
from huggingface_hub import snapshot_download, hf_hub_download, HfApi

path = snapshot_download("Qwen/Qwen3-0.6B", revision="main", allow_patterns=["*.json", "*.safetensors"])
cfg = hf_hub_download("Qwen/Qwen3-0.6B", "config.json")
api = HfApi()
for m in api.list_models(search="embedding", sort="downloads", limit=5):
    print(m.id)
api.upload_folder(folder_path="out/", repo_id="me/my-model", repo_type="model")   # needs `hf auth login`
```

Files are cached under `~/.cache/huggingface/hub` (override with `HF_HOME`); set
`HF_HUB_OFFLINE=1` for air-gapped servers.

## 2. Pipelines: the one-liner

`pipeline()` bundles tokenizer, model, pre- and post-processing for a task:

```python
from transformers import pipeline

clf = pipeline("sentiment-analysis")                              # default small model
print(clf(["I love this course!", "The KV cache ate my GPU."]))

gen = pipeline("text-generation", model="Qwen/Qwen3-0.6B", device_map="auto")
chat = [{"role": "user", "content": "Name three uses of RoPE scaling."}]
print(gen(chat, max_new_tokens=100)[0]["generated_text"][-1]["content"])

ner = pipeline("token-classification", model="dslim/bert-base-NER", aggregation_strategy="simple")
zs = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
print(zs("Refund my order", candidate_labels=["billing", "shipping", "tech support"]))
```

Pipelines are perfect for prototypes and for encoders (classification, NER, embeddings). For serious
LLM serving use a dedicated engine (TGI, vLLM, SGLang: next lesson).

## 3. Auto classes: what pipelines do underneath

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

model_id = "Qwen/Qwen3-0.6B"
config = AutoConfig.from_pretrained(model_id)          # architecture hyperparameters
print(config.num_hidden_layers, config.hidden_size, config.num_attention_heads, config.num_key_value_heads)

tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.bfloat16,          # or "auto": use the checkpoint's dtype
    device_map="auto",             # place layers across available GPUs / CPU (Accelerate)
    attn_implementation="sdpa",    # or "flash_attention_2", "eager"
)
batch = tok(["Hello world", "Attention is"], return_tensors="pt", padding=True).to(model.device)
with torch.no_grad():
    out = model(**batch)
print(out.logits.shape)            # (batch, seq_len, vocab_size)
```

The `Auto*` classes read `config.json`'s `architectures` / `model_type` and instantiate the right
class. Pick the **head** for your task:

| class | head | output |
|---|---|---|
| `AutoModel` | none | hidden states (use for embeddings) |
| `AutoModelForCausalLM` | LM head | next-token logits, `generate()` |
| `AutoModelForSeq2SeqLM` | encoder-decoder LM | `generate()` for T5/BART |
| `AutoModelForSequenceClassification` | pooled linear | class logits (also cross-encoder rerankers) |
| `AutoModelForTokenClassification` | per-token linear | NER tags |
| `AutoModelForMaskedLM` | MLM head | fill-mask |

Loading a checkpoint with a head that it was not trained with (e.g. classification on a base model)
prints a warning that the head is newly initialised; that is expected before fine-tuning.

**Quantised loading** for limited GPUs:

```python
from transformers import BitsAndBytesConfig
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct",
                                             quantization_config=bnb, device_map="auto")
```

A rule of thumb for memory: parameters x bytes per parameter (2 for bf16, about 0.5 for 4-bit), plus
KV cache and activations. An 8B model is about 16 GB in bf16 and about 5 GB in 4-bit.

## 4. generate(): the decoding loop

`model.generate()` runs prefill, then the decode loop with a KV cache, applying **logits processors**
(temperature, top-k, top-p, repetition penalty...) and **stopping criteria** at every step.

```python
inputs = tok.apply_chat_template(chat, add_generation_prompt=True, return_tensors="pt",
                                 return_dict=True).to(model.device)
out = model.generate(
    **inputs,
    max_new_tokens=256,        # ALWAYS set this; max_length counts the prompt too
    do_sample=True,            # False = greedy (or beam search if num_beams > 1)
    temperature=0.7,
    top_p=0.9,
    top_k=50,
    min_p=0.05,                # keep tokens with p >= min_p * p_max
    repetition_penalty=1.1,
    eos_token_id=[tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>")],
    pad_token_id=tok.pad_token_id,
)
print(tok.decode(out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

Defaults come from the repo's `generation_config.json`, which often sets sampling parameters
recommended by the model authors; your kwargs override them. Other useful knobs:

- `num_beams` (beam search; good for translation/ASR, rarely for chat),
- `no_repeat_ngram_size`, `stop_strings=["\n\n"]` (with `tokenizer=tok`),
- `assistant_model=draft_model` or `prompt_lookup_num_tokens=10` for **speculative / assisted
  decoding** (same output distribution, fewer large-model steps),
- `streamer=TextIteratorStreamer(tok)` to stream tokens from a background thread,
- `output_scores=True, return_dict_in_generate=True` to get per-step logits (for confidence or
  log-prob based evals).

### Sampling filters, from scratch

All sampling methods reshape the next-token distribution before drawing. The order in Transformers is
roughly: repetition penalty, temperature, top-k, top-p (each optional). Here they are in numpy;
this module's problem asks you to implement the top-k + top-p filter exactly.

```python-run
import numpy as np
np.set_printoptions(precision=3, suppress=True)

def softmax(z):
    z = z - z.max(); e = np.exp(z); return e / e.sum()

def filter_logits(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = np.asarray(logits, float) / temperature
    if top_k > 0:
        kth = np.sort(z)[-top_k]
        z = np.where(z < kth, -np.inf, z)
    if top_p < 1.0:
        order = np.argsort(-z, kind="stable")
        p = softmax(z)[order]
        cum = np.cumsum(p)
        keep_sorted = cum - p < top_p          # keep tokens until the mass BEFORE them reaches top_p
        keep = np.zeros_like(keep_sorted); keep[order] = keep_sorted
        z = np.where(keep, z, -np.inf)
    return softmax(z)

logits = np.array([4.0, 3.5, 3.0, 1.0, 0.5, -2.0])
print("plain      ", softmax(logits))
print("T=0.5      ", filter_logits(logits, temperature=0.5))
print("T=1.5      ", filter_logits(logits, temperature=1.5))
print("top_k=2    ", filter_logits(logits, top_k=2))
print("top_p=0.8  ", filter_logits(logits, top_p=0.8))

rng = np.random.default_rng(0)
p = filter_logits(logits, temperature=0.8, top_p=0.9)
draws = rng.choice(len(p), size=2000, p=p).astype(np.intp)   # intp = the integer type NumPy uses for indexes
print("sample frequencies:", np.bincount(draws, minlength=len(p)) / 2000)
```

How to choose:

- **Greedy / temperature 0**: extraction, classification, code with tests, anything you want
  reproducible (though GPU non-determinism and batching can still change results slightly).
- **Temperature 0.6 to 1.0 with top-p 0.9 to 0.95**: chat and creative writing. Reasoning models often
  ship recommended values (e.g. temperature 0.6, top-p 0.95) and degrade with greedy decoding.
- **min-p** scales the cut-off with the model's confidence, so it stays coherent at higher temperatures.

## 5. Batched generation correctly

```python
tok.padding_side = "left"                               # decoder-only: pad on the left
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
prompts = [tok.apply_chat_template([{"role": "user", "content": q}], tokenize=False,
                                   add_generation_prompt=True) for q in questions]
batch = tok(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
out = model.generate(**batch, max_new_tokens=128, do_sample=False)
answers = tok.batch_decode(out[:, batch["input_ids"].shape[1]:], skip_special_tokens=True)
```

Slice off the prompt tokens before decoding (a frequent "why does the output repeat my question?"
bug), and remember that right padding in a decoder-only batch makes the model continue from pad tokens.

## 6. Embeddings with AutoModel (preview of module 4)

```python
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F

tok = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
enc_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
b = tok(["a cat sits", "a kitten rests"], padding=True, return_tensors="pt")
h = enc_model(**b).last_hidden_state                       # (B, T, d)
mask = b["attention_mask"].unsqueeze(-1).float()
emb = (h * mask).sum(1) / mask.sum(1)                      # mean pooling over real tokens
emb = F.normalize(emb, dim=-1)
print((emb[0] @ emb[1]).item())                            # cosine similarity
```

Mean pooling must respect the attention mask, or padding tokens dilute the embedding.

## 7. Greedy versus beam search, traced by hand

Greedy decoding commits to the single best token at every step, which can miss a sequence whose first
token is slightly less likely but whose continuation is much better. **Beam search** keeps the
`num_beams` best partial sequences by total log-probability. The toy model below has a vocabulary of
three tokens and hand-written conditional probabilities so you can follow every step.

```python-run
import math
# P(next | prefix) for a tiny "language model": after token A the future is uncertain, after B it is confident.
def next_probs(prefix):
    if prefix == ():        return {"A": 0.5, "B": 0.4, "C": 0.1}
    if prefix[-1] == "A":   return {"A": 0.4, "B": 0.3, "C": 0.3}
    if prefix[-1] == "B":   return {"A": 0.05, "B": 0.05, "C": 0.9}
    return {"A": 0.34, "B": 0.33, "C": 0.33}

def greedy(steps):
    seq, lp = (), 0.0
    for _ in range(steps):
        tok, p = max(next_probs(seq).items(), key=lambda kv: kv[1])
        seq, lp = seq + (tok,), lp + math.log(p)
    return seq, lp

def beam_search(steps, num_beams):
    beams = [((), 0.0)]
    for step in range(steps):
        cand = [(seq + (t,), lp + math.log(p)) for seq, lp in beams for t, p in next_probs(seq).items()]
        beams = sorted(cand, key=lambda x: -x[1])[:num_beams]
        print(f"  step {step + 1}:", [("".join(s), round(math.exp(lp), 3)) for s, lp in beams])
    return beams[0]

g = greedy(2); print("greedy:", "".join(g[0]), "p =", round(math.exp(g[1]), 3))
b = beam_search(2, num_beams=2); print("beam  :", "".join(b[0]), "p =", round(math.exp(b[1]), 3))
```

Greedy picks `A` (0.5) and ends with probability 0.20; beam search keeps `B` alive and finds `BC` with
probability 0.36. Three practical notes:

- Beam search optimises **likelihood**, which is the right target for translation, summarisation and
  speech recognition, where there is one faithful output. For open-ended chat, the most likely text is
  often bland and repetitive, which is why sampling is the default there.
- Longer sequences accumulate more negative log-probability, so beam search favours short outputs;
  `length_penalty` rescales scores by length to compensate.
- Cost grows linearly with `num_beams` (each step runs the model on every beam), and the KV cache must
  be reordered when beams are pruned.

## 8. Repetition controls and how they work

Low-temperature decoding can loop ("the the the" or repeating a whole paragraph). Three knobs act on
the logits before sampling:

- `repetition_penalty` $\rho > 1$: for every token already present, divide its logit by $\rho$ if
  positive, or multiply by $\rho$ if negative, making it less likely either way.
- `no_repeat_ngram_size = n`: hard-ban any token that would complete an n-gram already generated.
- OpenAI-style `frequency_penalty` and `presence_penalty` subtract an amount proportional to (or
  independent of) how often a token has appeared.

```python-run
import numpy as np
def softmax(z): z = z - z.max(); e = np.exp(z); return e / e.sum()

def repetition_penalty(logits, generated, rho):
    out = logits.copy()
    for t in set(generated):
        out[t] = out[t] / rho if out[t] > 0 else out[t] * rho
    return out

logits = np.array([3.0, 2.5, -1.0, 0.5])
np.set_printoptions(precision=3, suppress=True)
print("before          :", softmax(logits))
print("penalise 0 and 2:", softmax(repetition_penalty(logits, [0, 2, 0], rho=1.3)))
```

Use these sparingly: a strong penalty breaks legitimate repetition (code, JSON keys, names, numbers in a
table), and penalising tokens from the *prompt* can stop a model quoting its sources. If a model loops at
sensible settings, suspect the chat template or a missing stop token first.

## 9. Streaming tokens to a user

```python
from threading import Thread
from transformers import TextIteratorStreamer

streamer = TextIteratorStreamer(tok, skip_prompt=True, skip_special_tokens=True)
thread = Thread(target=model.generate, kwargs=dict(**inputs, max_new_tokens=256, streamer=streamer))
thread.start()
for piece in streamer:            # yields decoded text as soon as whole words are available
    print(piece, end="", flush=True)
thread.join()
```

The streamer buffers until a complete word (or a complete multi-byte character) can be decoded, which is
why text appears in small chunks rather than one token at a time. Module 10 covers streaming over HTTP.

## 10. A debugging table for generate()

| symptom | likely cause | fix |
|---|---|---|
| output repeats the prompt | decoded the full sequence | slice off `input_ids.shape[1]` tokens before decoding |
| output stops after about 20 tokens | default `max_length` of 20 | set `max_new_tokens` |
| never stops, invents new user turns | end-of-turn token not in `eos_token_id` | add it; check `generation_config.json` |
| gibberish from a batched call only | right padding on a decoder-only model, or missing `attention_mask` | `padding_side="left"`, pass the mask |
| warning "Setting pad_token_id to eos_token_id" | tokenizer has no pad token | set `pad_token` explicitly and pass `pad_token_id` |
| different outputs for the same prompt at temperature 0 | sampling still enabled by the repo's generation config, or batch-dependent numerics | pass `do_sample=False`; expect tiny GPU nondeterminism |
| out of memory on long prompts | KV cache and activations grow with length and batch | lower batch size, quantise, enable a static or offloaded cache |
| very slow first call | weights loading, kernels compiling, cache warm-up | benchmark from the second call onwards |

> [!INTERVIEW]
> **"Walk me through loading and running an 8B model on a 24 GB GPU."** bf16 weights need about 16 GB,
> leaving room for KV cache; use `device_map="auto"`, `dtype=torch.bfloat16`, SDPA or FlashAttention;
> if memory is tight, 4-bit NF4 via bitsandbytes (about 5 GB). Apply the chat template with
> `add_generation_prompt=True`, set `max_new_tokens`, the right EOS ids and sampling parameters, left-pad
> for batches, and slice the prompt off before decoding. For production throughput, move to vLLM/TGI.

## Summary

- The Hub is git for models; pin revisions, prefer safetensors, read cards and licenses, be careful with
  `trust_remote_code`.
- `pipeline()` for quick tasks; `AutoTokenizer` + `AutoModelFor<Task>` for control.
- `generate()` = prefill + KV-cached decode + logits processors + stopping criteria; always set
  `max_new_tokens`.
- Temperature, top-k, top-p and min-p reshape the distribution; greedy for determinism.
- Left-pad decoder-only batches and decode only the new tokens.

```quiz
[
  {"q": "Why prefer .safetensors over pickle-based .bin weights?",
   "options": ["Loading pickles can execute arbitrary code; safetensors is pure data and memory-mappable", "safetensors are smaller", "Only safetensors work on GPU", ".bin cannot store bf16"], "answer": 0,
   "explain": "Pickle deserialisation can run code. safetensors is a simple header plus raw tensors, safe and fast."},
  {"q": "Which Auto class gives you raw hidden states for building embeddings?",
   "options": ["AutoModel", "AutoModelForCausalLM", "AutoModelForMaskedLM", "AutoModelForSequenceClassification"], "answer": 0,
   "explain": "AutoModel loads the base transformer without a task head."},
  {"q": "What is the difference between max_length and max_new_tokens?",
   "options": ["max_length includes the prompt tokens; max_new_tokens counts only generated ones", "They are identical", "max_new_tokens includes the prompt", "max_length is in characters"], "answer": 0,
   "explain": "With long prompts, max_length can leave no room for output; prefer max_new_tokens."},
  {"q": "Logits [4, 3.5, 3, 1] and top_p = 0.8: which describes the nucleus?",
   "options": ["The smallest set of top tokens whose cumulative probability reaches 0.8", "Tokens with probability above 0.8", "The top 80 percent of tokens by count", "Tokens whose logit is above 0.8"], "answer": 0,
   "explain": "Nucleus sampling keeps tokens in descending order until the cumulative mass reaches p."},
  {"q": "Batched outputs from a decoder-only model look broken for shorter prompts. Likely cause?",
   "options": ["Right padding; switch to padding_side='left'", "Temperature too high", "Wrong vocabulary", "Missing top_k"], "answer": 0,
   "explain": "With right padding the model continues generation after pad tokens."},
  {"q": "What does passing assistant_model=draft to generate() enable?",
   "options": ["Assisted (speculative) decoding with a small draft model", "Ensembling two models", "Chat templates", "Beam search"], "answer": 0,
   "explain": "The draft proposes tokens that the main model verifies in one pass, speeding decode without changing the output distribution."},
  {"q": "Why must mean pooling use the attention mask?",
   "options": ["Otherwise padding tokens are averaged into the embedding", "To make it causal", "To apply RoPE", "To normalise length to 1"], "answer": 0,
   "explain": "Pad positions carry meaningless hidden states and must be excluded from the average."}
]
```

> **Source:** Transformers docs: Pipelines, Auto classes, "Generation strategies", "Text generation"
> (https://huggingface.co/docs/transformers/generation_strategies), quantization with bitsandbytes;
> Hub docs: repositories, model cards, security/pickle (https://huggingface.co/docs/hub);
> HF LLM Course ch. 2 "Using Transformers" (https://huggingface.co/learn/llm-course/chapter2);
> Huyen, *AI Engineering*, ch. 2 (sampling: temperature, top-k, top-p) and ch. 9.
