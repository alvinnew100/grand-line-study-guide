# Hub, pipelines, Auto classes and generate()

> **Before this lesson:** you should know what logits, softmax, temperature and greedy decoding are
> ([From embeddings to scaled dot-product attention](#/lesson/llm-practice/attention-from-scratch)),
> what attention heads are
> ([The transformer block](#/lesson/llm-practice/transformer-block)), what the KV cache is
> ([Positional encodings, RoPE, KV cache and architecture families](#/lesson/llm-practice/positions-and-architectures)),
> and how a chat template turns messages into a prompt
> ([Special tokens, chat templates and tokenizer pitfalls](#/lesson/llm-practice/special-tokens-chat-templates)).
> The runnable demos need only Python and numpy.

## In plain words

Training a large model costs millions; using one that somebody else trained costs a download.
**Hugging Face** is the company whose website, the **Hub**, hosts hundreds of thousands of such
downloadable models, and whose Python libraries load and run them in a few lines. This lesson is the
"how do I actually run a model" lesson: find a model, download it, feed it text, and control how it
writes its answer.

An analogy: the Hub is a huge public library of pre-built engines. Each engine comes in a labelled
crate (the repository) with a manual (the model card). The `pipeline` function is the showroom test
drive: turn the key and go. The `Auto` classes are the mechanic's toolkit, giving access to every
part. And `generate()` is the driving itself, where settings such as temperature and top-p decide
whether the car drives cautiously or adventurously.

Why it matters for a job: nearly every applied machine-learning role touches this stack, and
interviewers expect you to know how to load a model within a memory budget, why its output repeats
the question, or why batched output is garbage. The decoding settings (temperature, top-k, top-p,
beam search) are classic interview material because they decide the quality, variety and cost of
every response a product sends.

## The Hugging Face stack in one paragraph

The Hugging Face stack is the most widely used toolkit for open models. The **Hub** hosts weights,
datasets and demos; **Transformers** loads and runs models; **Tokenizers** turns text into ids
(lesson 4); **Datasets** loads and processes training data; **PEFT** (parameter-efficient
fine-tuning) trains small add-on weights instead of the whole model (lesson 13); **TRL**
(Transformer Reinforcement Learning) runs fine-tuning recipes (lesson 14); and **Accelerate** spreads
work across several chips. This lesson is a guided tour of the **inference** side, meaning using a
trained model to produce outputs, with the code you will actually type. Code blocks here are static
(they need a GPU or a network connection), but every concept is backed by a runnable numpy demo.

> [!NOTE]
> Versions move fast. This lesson follows **Transformers v5** (released late 2025): PyTorch-only,
> `dtype=` instead of the older `torch_dtype=`, and `dtype="auto"` by default when loading. If you
> read older tutorials, translate `torch_dtype` to `dtype`.

## 1. The Hub: repos, revisions, model cards

A model on disk is a set of files: a configuration file describing its shape, a tokenizer, and the
**weights** (the learned numbers, often billions of them). A saved set of weights is called a
**checkpoint**. On the Hub, every model, dataset and **Space** (a small hosted demo app) lives in a
**git repository**, the same version-control system programmers use for code, with large files kept
in special storage (Xet, or the older LFS, "large file storage"). Some consequences:

- `meta-llama/Llama-3.1-8B-Instruct` is `<namespace>/<repo>`: the owner, then the repository name.
- Every change to a repository creates a new **commit**, identified by a long hexadecimal code called
  its **sha**. A **revision** is any name for one version: a branch (`main`), a tag, or a commit sha.
  Pin a revision in production so an upstream push cannot change your model under your feet:
  `from_pretrained(id, revision="a1b2c3d")`.
- **Model cards** (`README.md` with YAML metadata) document intended use, training data, evaluation,
  limitations, license and the `library_name` / `pipeline_tag` that drive the Hub widgets. (YAML is
  a simple "key: value" text format placed at the top of the file.) Read the license before
  shipping; **gated** models such as Llama require you to accept terms on the website before you can
  download them.
- **Formats**: `safetensors` stores raw arrays plus a small header. It is safe and can be
  **memory-mapped** (read straight from disk into memory without an extra copy). Prefer it over
  older `.bin` files, which use Python's **pickle** format; unpickling can run arbitrary code, so a
  malicious `.bin` file can execute a program on your machine as it loads. Other formats you will
  meet: GGUF (llama.cpp and Ollama), ONNX (a cross-framework format for deployment) and MLX (Apple's
  framework for its own chips).
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

Line by line: `snapshot_download` fetches a whole repository at a given revision and returns the
local folder path; `allow_patterns` limits it to the listed file types, so you skip files you do not
need. `hf_hub_download` fetches one named file. `HfApi()` is a client for the Hub's web interface:
`list_models` searches it (here, the five most downloaded models matching "embedding") and
`upload_folder` publishes a local folder as a repository. Uploading needs you to be signed in, which
the `hf auth login` command does once per machine.

Downloaded files are **cached** (kept on disk so the next load is instant) under
`~/.cache/huggingface/hub`. An **environment variable** is a setting the operating system passes to
every program; `HF_HOME` moves the cache elsewhere, and `HF_HUB_OFFLINE=1` forbids network access,
which is what you want on **air-gapped** servers (machines deliberately cut off from the internet).

## 2. Pipelines: the one-liner

`pipeline()` bundles the tokenizer, the model, and the pre- and post-processing for a named **task**
(a kind of job, such as "sentiment-analysis" or "text-generation"). Pre-processing turns your input
into ids; post-processing turns the model's numbers into a friendly answer such as a label and a
score.

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

What each pipeline does:

- `pipeline("sentiment-analysis")` with no model name picks a small default English model. Called on
  a list of two sentences, it returns one dictionary per sentence, along the lines of
  `{'label': 'POSITIVE', 'score': 0.99}` for the first and a negative label for the second.
- The `text-generation` pipeline accepts a chat (a list of messages), applies the model's chat
  template for you, and returns the conversation with the new assistant message appended. The
  expression `[0]["generated_text"][-1]["content"]` digs out that last message's text: first result,
  its conversation, last message, its content.
- `token-classification` labels individual words. With the `dslim/bert-base-NER` model it performs
  **NER** (named-entity recognition: finding names of people, organisations and places).
  `aggregation_strategy="simple"` merges word pieces back into whole names.
- `zero-shot-classification` sorts text into labels you invent on the spot, with no training: "zero
  shot" means zero labelled examples. It returns the labels ranked by score, so "Refund my order"
  should come back with "billing" first.

Pipelines are perfect for prototypes and for **encoders** (models that read text and produce a
representation of it, such as BERT, used for classification, NER and embeddings). For serious LLM
serving use a dedicated engine (TGI, vLLM, SGLang: next lesson), which can serve many users at once
efficiently.

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

**Reading this code line by line**

- `AutoConfig.from_pretrained` downloads only `config.json`, the model's shape description. The
  printed numbers are the count of transformer blocks (`num_hidden_layers`), the width $d$ of each
  token's vector (`hidden_size`), the number of query heads and the number of key/value heads. When
  the last number is smaller than the query-head count, the model uses grouped-query attention
  (lesson 2) to shrink its KV cache.
- `dtype=torch.bfloat16` stores each weight in **bfloat16**, a 16-bit (2-byte) number format with the
  same range as 32-bit floats but less precision; it halves memory compared with float32.
- `device_map="auto"` lets Accelerate place the model's layers on the available GPUs, spilling to the
  CPU if they do not fit.
- `attn_implementation` chooses the attention code: `"sdpa"` is PyTorch's built-in fast
  `scaled_dot_product_attention`, `"flash_attention_2"` needs an extra package and a recent GPU, and
  `"eager"` is the plain, slow reference version.
- `tok([...], return_tensors="pt", padding=True)` tokenizes two texts of different lengths into one
  padded batch, with an attention mask marking the real tokens.
- `torch.no_grad()` tells PyTorch not to record the bookkeeping needed for training, which saves
  memory when you only want outputs.
- `model(**batch)` runs one forward pass (input to output, no generation). `out.logits.shape` prints
  three numbers: the batch size (2), the padded sequence length, and the vocabulary size. That is one
  row of next-token scores for *every* position of *every* sequence.

The `Auto*` classes read the `architectures` and `model_type` entries in `config.json` and create
the right Python class for you, so the same three lines load a Llama, a Qwen or a Mistral. Pick the
**head** for your task. A head is the final small layer that turns the transformer's hidden states
into the output a task needs: vocabulary logits for text generation, a handful of class scores for
classification, one label per token for NER.

| class | head | output |
|---|---|---|
| `AutoModel` | none | hidden states (use for embeddings) |
| `AutoModelForCausalLM` | LM head | next-token logits, `generate()` |
| `AutoModelForSeq2SeqLM` | encoder-decoder LM | `generate()` for T5/BART |
| `AutoModelForSequenceClassification` | pooled linear | class logits (also cross-encoder rerankers) |
| `AutoModelForTokenClassification` | per-token linear | NER tags |
| `AutoModelForMaskedLM` | MLM head | fill-mask |

In the table, "hidden states" are the vectors coming out of the last block, one per token; "pooled
linear" means the hidden states are summarised into one vector and passed through one small matrix;
"MLM" is masked language modelling, BERT's fill-in-the-blank training task; and T5 and BART are
**encoder-decoder** models (one half reads, the other half writes) used for translation and
summarisation.

Loading a checkpoint with a head that it was not trained with (e.g. classification on a base model)
prints a warning that the head is newly initialised, meaning filled with random numbers. That is
expected before fine-tuning, and a bug if you meant to load a finished classifier.

**Quantised loading** for limited GPUs. **Quantisation** stores each weight in fewer bits than
usual, for example 4 bits instead of 16, trading a little accuracy for a large memory saving. The
bitsandbytes library does this as the model loads:

```python
from transformers import BitsAndBytesConfig
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct",
                                             quantization_config=bnb, device_map="auto")
```

The arguments: `load_in_4bit=True` turns quantisation on; `bnb_4bit_quant_type="nf4"` picks
**NF4** ("4-bit NormalFloat"), a 4-bit format whose 16 levels are spaced to suit the bell-shaped
spread of real weights; `bnb_4bit_compute_dtype=torch.bfloat16` means the weights are expanded back
to bfloat16 for each multiplication; and `bnb_4bit_use_double_quant=True` also compresses the small
scaling constants that quantisation needs, saving a little more memory. Lesson 13 explains these
ideas in depth for QLoRA.

A rule of thumb for memory: parameters x bytes per parameter (2 for bf16, about 0.5 for 4-bit), plus
the KV cache and **activations** (the intermediate results computed during a forward pass). An 8B
model (8 billion parameters) is about 16 GB in bf16 and about 5 GB in 4-bit.

## 4. generate(): the decoding loop

Recall from lesson 3 how a model writes. In the **prefill** step it reads the whole prompt in one
pass and stores every token's keys and values in the **KV cache**. In the **decode** loop it then
produces one token per step, reusing the cache so that it only computes the newest position.
`model.generate()` runs exactly that, and at every step it applies **logits processors** (small
functions that edit the next-token scores: temperature, top-k, top-p, repetition penalty and so on)
and checks **stopping criteria** (rules that decide when to finish).

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

What each argument means:

- `max_new_tokens=256` caps the reply length. Always set it: the older `max_length` counts the prompt
  too, so a long prompt can leave no room at all.
- `do_sample=True` means "draw the next token at random according to the probabilities".
  **Sampling** is that random draw; `do_sample=False` instead takes the single most likely token
  every time (greedy decoding).
- `temperature=0.7` divides the logits by 0.7 before softmax, sharpening the distribution a little
  (lesson 1).
- `top_p`, `top_k` and `min_p` remove unlikely tokens before the draw; the next subsection builds
  them from scratch.
- `repetition_penalty=1.1` makes tokens that already appeared slightly less likely (section 8).
- `eos_token_id=[...]` lists every token that should end generation: here the tokenizer's EOS and
  ChatML's end-of-turn marker, the double-stop-token lesson from lesson 5.
- `pad_token_id` tells `generate` which id to use when one sequence in a batch finishes early.

Defaults come from the repo's `generation_config.json`, which often sets sampling parameters
recommended by the model authors; your keyword arguments override them. Other useful knobs:

- `num_beams` (beam search, section 7; good for translation and **ASR**, automatic speech
  recognition, rarely for chat),
- `no_repeat_ngram_size`, `stop_strings=["\n\n"]` (with `tokenizer=tok`, which it needs to decode
  text while watching for the string),
- `assistant_model=draft_model` or `prompt_lookup_num_tokens=10` for **speculative / assisted
  decoding**: a cheap guesser (a small **draft model**, or a lookup of text already in the prompt)
  proposes several tokens, and the big model checks them all in one pass, keeping those it agrees
  with. The output distribution is unchanged, but the big model runs fewer steps.
- `streamer=TextIteratorStreamer(tok)` to stream tokens from a background thread (section 9),
- `output_scores=True, return_dict_in_generate=True` to get per-step logits (for confidence or
  log-prob based evals).

### Sampling filters, from scratch

All sampling methods reshape the next-token distribution before drawing. Three filters are common:

- **Top-k** keeps only the $k$ highest-scoring tokens and discards the rest.
- **Top-p**, also called **nucleus sampling**, sorts tokens from most to least likely and keeps the
  smallest group whose probabilities add up to at least $p$. When the model is confident the group
  is tiny; when it is unsure the group is large. That adaptivity is why top-p is more popular than
  top-k.
- **Min-p** keeps every token whose probability is at least `min_p` times the top token's
  probability.

After filtering, the surviving probabilities are rescaled to add up to 1 and one token is drawn. The
order in Transformers is roughly: repetition penalty, temperature, top-k, top-p (each optional). Here
they are in numpy; this module's problem asks you to implement the top-k + top-p filter exactly.

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

**Reading this code line by line**

- `filter_logits` first divides by the temperature. Top-k finds the $k$-th largest score with
  `np.sort(z)[-top_k]` and sets every smaller score to $-\infty$, which softmax turns into a
  probability of exactly 0.
- For top-p, `np.argsort(-z, kind="stable")` lists the token positions from highest to lowest score,
  `p` holds their probabilities in that order and `np.cumsum` gives running totals. The test
  `cum - p < top_p` asks, for each token, "had the tokens before this one already reached `top_p`?"
  If not, the token is kept. This guarantees the top token always survives.
- `keep[order] = keep_sorted` writes the decisions back to the original token positions.
- The five printed rows use six logits. Plain softmax gives about `[0.486 0.295 0.179 0.024 0.015
  0.001]`. Temperature 0.5 sharpens it (the leader rises to 0.664); temperature 1.5 flattens it (the
  leader drops to 0.403 and the tail grows). Top-k 2 keeps two tokens, rescaled to `0.622` and
  `0.378`. Top-p 0.8 keeps three: the first two add up to only 0.781, which is short of 0.8, so the
  third is needed.
- The last lines draw 2,000 samples with `rng.choice(..., p=p)` and count them with `np.bincount`.
  The frequencies (about `0.54 0.30 0.16 0 0 0`) match the filtered probabilities, and the three
  filtered-out tokens are never drawn.

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

Step by step: left padding is switched on; a pad token is borrowed from EOS if the tokenizer has
none; each question is rendered with the chat template as a string; the strings are tokenized
together with `padding=True` and `add_special_tokens=False` (the template already added BOS, so this
avoids the double-BOS bug of lesson 5); `generate` runs greedily; and `batch_decode` decodes every
row at once after slicing off the prompt columns.

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

A **sentence embedding** is one vector that stands for a whole sentence, so that similar sentences
get nearby vectors (lesson 8). `AutoModel` returns `last_hidden_state`, one vector per token with
shape (batch, tokens, width). **Mean pooling** averages those token vectors into one: the mask
(1 for real tokens, 0 for padding) is multiplied in so padding contributes nothing, and the sum is
divided by the number of real tokens. `F.normalize` scales each vector to length 1, after which the
dot product `emb[0] @ emb[1]` equals the **cosine similarity**, a score near 1 for sentences with
nearly the same meaning. "a cat sits" and "a kitten rests" should score high.

Mean pooling must respect the attention mask, or padding tokens dilute the embedding.

## 7. Greedy versus beam search, traced by hand

Greedy decoding commits to the single best token at every step, which can miss a sequence whose first
token is slightly less likely but whose continuation is much better.

The probability of a whole sequence is the product of its step probabilities (lesson 1). Multiplying
many small numbers quickly underflows, so programs add their **log-probabilities** instead: the
logarithm turns a product into a sum, and a higher (less negative) total still means a more likely
sequence. **Beam search** keeps the `num_beams` best partial sequences by total log-probability at
every step, extends each by every possible token, and again keeps only the best few. The toy model
below has a vocabulary of three tokens and hand-written conditional probabilities so you can follow
every step.

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

How the code works: `next_probs(prefix)` plays the role of the model, returning a probability for
each next token given the tokens so far. `greedy` takes the `max` at each step and adds up the logs.
`beam_search` builds every one-token extension of every surviving beam (`cand`), sorts them by
log-probability, keeps the top `num_beams`, and prints the survivors with their probabilities
(`math.exp` undoes the log).

Greedy picks `A` (0.5) and ends with probability 0.20; beam search keeps `B` alive and finds `BC` with
probability 0.36. The printed trace shows why: after step 1 the beams are `A` (0.5) and `B` (0.4);
after step 2, `BC` (0.4 x 0.9 = 0.36) beats the best continuation of `A`, which is `AA`
(0.5 x 0.4 = 0.20). Three practical notes:

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
- `no_repeat_ngram_size = n`: hard-ban any token that would complete an **n-gram** (a run of $n$
  consecutive tokens) already generated.
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

Why the rule has two branches: dividing a *positive* logit by 1.3 makes it smaller, but dividing a
*negative* one would move it towards zero, which is *larger*. Multiplying a negative logit by 1.3
pushes it further down instead, so both branches make the token less likely. In the output, token 0
(already generated twice) falls from 0.586 to 0.416 and token 1, never generated, overtakes it at
0.504. Token 2's logit goes from -1.0 to -1.3, yet its printed probability stays at 0.011, because
the other tokens moved too; only the relative order of the scores matters to softmax.

Use these sparingly: a strong penalty breaks legitimate repetition (code, JSON keys, names, numbers in a
table), and penalising tokens from the *prompt* can stop a model quoting its sources. If a model loops at
sensible settings, suspect the chat template or a missing stop token first.

## 9. Streaming tokens to a user

**Streaming** means showing the reply as it is written instead of waiting for the whole of it, which
is why chat interfaces appear to type. `generate` does not return until it has finished, so the
standard recipe runs it in a **thread** (a second line of execution inside the same program) while
the main thread reads text pieces from a streamer object as they arrive:

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

## Glossary

- **Hub**: Hugging Face's website hosting models, datasets and demo apps as git repositories.
- **Checkpoint / weights**: a saved set of a model's learned numbers.
- **Revision**: one version of a repository, named by a branch, tag or commit sha.
- **Model card**: the README that documents a model's use, data, limits and license.
- **safetensors / pickle**: a safe raw-array file format / Python's object format, which can run code
  when loaded.
- **Pipeline**: a one-line wrapper that bundles tokenizer, model and post-processing for a task.
- **Auto class**: a loader that reads `config.json` and builds the matching model class.
- **Head**: the final layer that turns hidden states into a task's output.
- **bfloat16**: a 2-byte number format with float32's range and less precision.
- **Quantisation / NF4**: storing weights in fewer bits / a 4-bit format shaped for typical weights.
- **Prefill / decode**: reading the whole prompt in one pass / producing one token per step.
- **Logits processor**: a function that edits next-token scores before the choice is made.
- **Sampling**: drawing the next token at random according to its probability.
- **Top-k / top-p (nucleus) / min-p**: keep the $k$ best tokens / the smallest group reaching
  probability $p$ / tokens at least `min_p` times as likely as the best.
- **Beam search**: keeping several best partial sequences at each step.
- **Log-probability**: the logarithm of a probability; sums of logs replace products.
- **Speculative (assisted) decoding**: a cheap guesser proposes tokens that the big model verifies.
- **Mean pooling**: averaging token vectors, ignoring padding, to get one sentence vector.
- **Streaming**: sending text to the user piece by piece while it is generated.

## Check yourself

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
