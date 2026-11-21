# SFT and DPO with TRL: data, training loop, evaluation

> **Before this lesson:** you should know how chat templates render conversations and how training
> labels use `-100` to skip prompt tokens
> ([Special tokens, chat templates and tokenizer pitfalls](#/lesson/llm-practice/special-tokens-chat-templates)),
> how `Trainer` runs a training loop
> ([Datasets, Trainer, Accelerate and serving](#/lesson/llm-practice/datasets-trainer-serving)), and
> what a LoRA adapter is ([PEFT: LoRA, QLoRA and friends](#/lesson/llm-practice/lora-qlora)).
> Softmax, logits and cross-entropy come from
> [lesson 1](#/lesson/llm-practice/attention-from-scratch).

## In plain words

A freshly pretrained model can continue any text but does not know how to be a helpful assistant.
Two kinds of training fix that. **Supervised fine-tuning (SFT)** shows the model thousands of example
conversations and trains it to imitate the assistant's side. **Preference tuning** then shows it pairs
of answers to the same question, one better and one worse, and trains it to prefer the better kind.
**DPO** (direct preference optimisation) is the most popular way to do the second step because it is
as simple to run as SFT.

An analogy: training a new call-centre agent. First they read transcripts of model calls and copy
how good agents speak (SFT). Then a supervisor plays back pairs of their own calls and says "this one
was better than that one", and they adjust (preference tuning). Copying teaches the format; the
comparisons teach judgement about tone, helpfulness and what to avoid.

Why it matters for a job: these two steps are how open models are customised in practice, and the
libraries make them a few dozen lines of code, which means the real skill is in the data and the
evaluation. Interviewers ask candidates to explain or derive the DPO loss, to say why SFT masks the
prompt, and to debug a fine-tune that never stops talking.

## Post-training in two stages

**Post-training** turns a base model into an assistant in (at least) two stages: **supervised
fine-tuning (SFT)** on **demonstrations** (example conversations showing the desired behaviour), then
**preference optimisation**. The second stage has several flavours: **RLHF** (reinforcement learning
from human feedback), DPO and relatives, or RL with **verifiable rewards** (rewards computed by a
program, such as "did the code pass its tests?"). **Reinforcement learning (RL)** in general means
improving behaviour by trial and error guided by a numerical reward. Hugging Face's **TRL** library
implements all of them on top of `Trainer`. This lesson walks through data formats, the losses,
working training scripts, and how to evaluate the result. The AI Engineering track covers the
strategy (when to fine-tune, data quantity and quality); here we write the code and derive the losses.

## 1. Data formats TRL understands

TRL accepts four shapes for SFT (current TRL v1 docs). Each row of the dataset is one dictionary.
"Standard" rows hold plain text; "conversational" rows hold lists of chat messages, which TRL renders
with the model's chat template. "Language modelling" rows train on the whole text; "prompt-completion"
rows separate the input from the part to be learned:

```python
# 1. Standard language modelling
{"text": "The sky is blue."}
# 2. Conversational language modelling (chat template applied automatically)
{"messages": [{"role": "user", "content": "What color is the sky?"},
              {"role": "assistant", "content": "It is blue."}]}
# 3. Standard prompt-completion
{"prompt": "The sky is", "completion": " blue."}
# 4. Conversational prompt-completion
{"prompt": [{"role": "user", "content": "What color is the sky?"}],
 "completion": [{"role": "assistant", "content": "It is blue."}]}
```

And for preference methods (DPO, ORPO, KTO-paired, reward modelling), each row holds one prompt and
two answers, the **chosen** (preferred) one and the **rejected** one:

```python
{"prompt": [{"role": "user", "content": "Explain RoPE in one line."}],
 "chosen": [{"role": "assistant", "content": "RoPE rotates Q and K by position-dependent angles..."}],
 "rejected": [{"role": "assistant", "content": "RoPE is a kind of rope used in sailing."}]}
```

Tool-calling SFT adds a `tools` column (JSON schemas) and `tool_calls` / `tool` role messages.

**Data work dominates outcomes**: dedupe, filter low quality (LLM-judge scoring, heuristics), balance
task types, remove eval-set **contamination** (test questions, or near-copies of them, that slipped
into the training data and would inflate your scores), and look at samples. A few thousand excellent,
diverse examples routinely beat hundreds of thousands of mediocre ones for style and format
adaptation.

The demo turns raw support tickets into prompt-completion rows, applying a quality filter and exact
deduplication on the way:

```python-run
import json
# Converting raw support tickets into conversational prompt-completion SFT rows
raw = [
  {"q": "How do I reset my API key?", "a": "Go to Settings > API keys and click Rotate.", "quality": 5},
  {"q": "asdf", "a": "??", "quality": 1},
  {"q": "Can I export invoices as CSV?", "a": "Yes: Billing > Invoices > Export > CSV.", "quality": 4},
  {"q": "How do I reset my API key?", "a": "Go to Settings > API keys and click Rotate.", "quality": 5},
]
SYSTEM = "You are ACME's support assistant. Answer in one or two sentences."
seen, rows = set(), []
for r in raw:
    key = r["q"].strip().lower()
    if r["quality"] < 3 or key in seen:          # quality filter + exact dedupe
        continue
    seen.add(key)
    rows.append({"prompt": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": r["q"]}],
                 "completion": [{"role": "assistant", "content": r["a"]}]})
print(len(rows), "rows kept")
print(json.dumps(rows[0], indent=1)[:400])
```

Line by line: `seen` remembers the normalised questions already kept (`strip().lower()` ignores
spacing and capital letters). The `if` skips rows with a quality score below 3 and repeats. Each
surviving ticket becomes a row whose `prompt` is a system message plus the user's question and whose
`completion` is the assistant's answer. Out of four tickets, the gibberish one and the duplicate are
dropped, so the output reports `2 rows kept` and prints the first row as indented JSON.

## 2. SFT: the loss

SFT is ordinary next-token cross-entropy (lesson 1: minus the log of the probability the model gave
the correct next token), but usually **only on the completion / assistant tokens**. In the formula,
$\theta$ (theta) stands for all the model's parameters, $p_\theta(y_t \mid y_{<t})$ is the probability
the model assigns to the true token $y_t$ given everything before it, and the sum is averaged over the
completion positions:

$$
\mathcal{L}_{SFT}(\theta) = -\frac{1}{|C|}\sum_{t \in C} \log p_\theta(y_t \mid y_{<t})
$$

where $C$ is the set of completion positions; prompt positions get label $-100$. In TRL v1:
prompt-completion datasets use completion-only loss by default (`completion_only_loss`), and
conversational datasets can use `assistant_only_loss=True` (requires a chat template with generation
markers, which TRL patches in automatically for known families).

```python-run
import numpy as np
rng = np.random.default_rng(0)
T, V = 8, 12
logits = rng.standard_normal((T, V))
targets = rng.integers(0, V, T)
labels = targets.copy(); labels[:5] = -100          # first 5 positions are prompt
lp = logits - logits.max(1, keepdims=True); lp -= np.log(np.exp(lp).sum(1, keepdims=True))
mask = labels != -100
loss_masked = -lp[np.arange(T)[mask], labels[mask]].mean()
loss_all = -lp[np.arange(T), targets].mean()
print("loss on completion only:", round(float(loss_masked), 3), " loss on everything:", round(float(loss_all), 3))
```

What the demo does: `logits` are random scores for 8 positions over a 12-token vocabulary, and
`targets` are random correct tokens. Setting the first five labels to `-100` marks them as prompt. The
line computing `lp` is a stable log-softmax, `mask` is `True` where the label is real, and
`lp[np.arange(T)[mask], labels[mask]]` picks out the log-probability of the correct token at each
unmasked position. The two printed numbers (about 3.50 and 3.32) differ because one averages over 3
positions and the other over all 8: masking changes which positions the model is graded on.

## 3. SFT with TRL (static)

```python
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

ds = load_dataset("json", data_files="support_sft.jsonl", split="train").train_test_split(test_size=0.05, seed=0)

config = SFTConfig(
    output_dir="qwen3-support-sft",
    num_train_epochs=2,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    learning_rate=1e-4,                # adapters: ~10x full-FT LR
    lr_scheduler_type="cosine", warmup_ratio=0.05,
    max_length=2048,
    packing=True,                       # pack short examples into full sequences (bfd strategy)
    assistant_only_loss=False,          # prompt-completion data -> completion-only loss by default
    bf16=True, gradient_checkpointing=True,
    eval_strategy="steps", eval_steps=200, logging_steps=10,
    report_to="trackio",                # or "wandb", "tensorboard", "none"
)
trainer = SFTTrainer(
    model="Qwen/Qwen3-1.7B",
    args=config,
    train_dataset=ds["train"], eval_dataset=ds["test"],
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"),
)
trainer.train()
trainer.save_model()
```

Most settings in `SFTConfig` are `TrainingArguments` you met in lesson 7: epochs, batch size and
accumulation (4 x 8 = 32 examples per update), learning rate and schedule, bf16, gradient
checkpointing, and evaluation every 200 steps. Three are specific to SFT: `max_length=2048` truncates
longer examples, `packing=True` fills each sequence with several short examples (section 7), and
`assistant_only_loss` chooses which tokens are trained. `report_to="trackio"` sends the training
curves to Trackio, Hugging Face's lightweight experiment tracker. `SFTTrainer` receives the model name,
the config, the two splits and a `LoraConfig`, so it trains a LoRA adapter rather than the full model.

Notes:

- Passing a model id string lets TRL load it (with `model_init_kwargs` for dtype etc.).
- **Packing** concatenates examples to fill `max_length`, avoiding padding waste; modern TRL uses
  position-id resets / padding-free attention so packed examples do not attend to each other.
- Watch `mean_token_accuracy` (how often the model's top guess equals the true next token), train/eval
  loss and, above all, **sampled generations** at checkpoints: read what the model actually writes.
- **Overfitting signs**: eval loss rising while train loss falls; outputs copying training phrases;
  degraded general ability. 1 to 3 epochs is typical for SFT.
- Fine-tuning a base model? Set the chat template (`chat_template_path`) and EOS token correctly
  (module 2), or the result will not stop generating.

## 4. Preference optimisation: from RLHF to DPO

Some vocabulary first. In RL language the model being trained is the **policy**, written $\pi_\theta$
(pi): given a prompt $x$, it produces a response $y$ with probability $\pi_\theta(y|x)$. A **reward
model** is a separate network trained to output a score saying how good a response is. The
**Bradley-Terry** model is a classic way to turn scores into comparison probabilities: the chance that
$y_w$ (the winner) beats $y_l$ (the loser) is $\sigma(r(y_w) - r(y_l))$, where $\sigma$ is the
**sigmoid** function $\sigma(z) = 1/(1 + e^{-z})$, which squashes any number into the range 0 to 1.
**KL divergence** measures how different two probability distributions are; it is 0 when they are
identical.

Classic **RLHF** (as used for InstructGPT, the model behind the first ChatGPT): train a reward model
$r_\phi(x, y)$ on human comparisons with a Bradley-Terry loss, then optimise the policy with **PPO**
(proximal policy optimisation, a standard RL algorithm) to maximise reward minus a KL penalty to a
**reference model** $\pi_{ref}$ (the SFT model, kept frozen). The penalty stops the policy drifting
into strange text that happens to fool the reward model:

$$
\max_\theta\; \mathbb{E}_{y \sim \pi_\theta}\left[r_\phi(x, y)\right] - \beta\,\mathrm{KL}\left(\pi_\theta(\cdot|x)\,\|\,\pi_{ref}(\cdot|x)\right)
$$

Read it as: "make the expected reward of the model's own answers ($\mathbb{E}$ means average over
answers drawn from the policy) as high as possible, minus $\beta$ times how far the policy has moved
from the reference". PPO needs four models in memory (policy, reference, reward, and a **value model**
that predicts future reward to reduce noise) and is finicky to tune.

**DPO** (Rafailov et al. 2023) shows that this objective has a **closed-form** optimal policy (an exact
formula rather than something found by search), so the reward can be expressed through the policy
itself: $r(x, y) = \beta \log \frac{\pi_\theta(y|x)}{\pi_{ref}(y|x)} + \text{const}$. Plugging into
Bradley-Terry gives a simple classification-style loss on preference pairs $(x, y_w, y_l)$:

$$
\mathcal{L}_{DPO} = -\log \sigma\!\left(\beta\left[\log\frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \log\frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\right]\right)
$$

- $\log \pi(y|x)$ is the **sum of token log-probs of the response** given the prompt.
- The bracket is the difference of **implicit rewards** $\beta \log \frac{\pi_\theta}{\pi_{ref}}$ for the
  chosen and rejected responses. TRL logs them as `rewards/chosen`, `rewards/rejected`,
  `rewards/margins` and `rewards/accuracies` (fraction of pairs where chosen beats rejected).
- $\beta$ (0.1 typical) controls how far the policy may drift from the reference.
- Only two models (policy and frozen reference); with LoRA the reference is the base with adapters
  disabled, so one copy of weights suffices.

In plain words: the loss is small when the policy has raised the chosen answer's probability (relative
to the reference) by more than it raised the rejected answer's. The demo computes it for two pairs.
`np.logaddexp(0, -m)` equals $\log(1 + e^{-m})$, which is exactly $-\log\sigma(m)$, written in a form
that cannot overflow:

```python-run
import numpy as np

def dpo_loss(pc, pr, rc, rr, beta=0.1):
    """pc/pr: policy log-probs of chosen/rejected; rc/rr: reference log-probs."""
    pc, pr, rc, rr = map(np.asarray, (pc, pr, rc, rr))
    margin = beta * ((pc - rc) - (pr - rr))
    loss = np.logaddexp(0, -margin)                 # -log sigmoid(margin), numerically stable
    acc = (margin > 0).mean()
    return float(loss.mean()), float(acc), beta * (pc - rc), beta * (pr - rr)

# At initialisation policy == reference: margin 0, loss = log 2
print("init loss:", round(dpo_loss([-12, -30], [-15, -28], [-12, -30], [-15, -28])[0], 4), " log2 =", round(np.log(2), 4))
# After some training the policy raises chosen and lowers rejected log-probs
loss, acc, r_c, r_r = dpo_loss([-10, -27], [-18, -33], [-12, -30], [-15, -28])
print("trained loss:", round(loss, 4), " reward accuracy:", acc)
print("implicit rewards chosen:", r_c, " rejected:", r_r)
```

The inputs are summed log-probabilities of whole responses (negative numbers; closer to zero means
more likely). In the first call the policy equals the reference, so every log-ratio is 0, the margin
is 0, and the loss is $\log 2 \approx 0.6931$: the model has no preference yet. In the second call the
policy has made both chosen answers more likely (-12 to -10, -30 to -27) and both rejected answers
less likely. The implicit rewards are $0.1 \times 2 = 0.2$ and $0.1 \times 3 = 0.3$ for the chosen
answers and $-0.3$ and $-0.5$ for the rejected ones, so the margins are 0.5 and 0.8, the loss falls to
about 0.42, and the reward accuracy is 1.0 (the chosen answer wins in both pairs).

## 5. DPO with TRL (static)

```python
from datasets import load_dataset
from trl import DPOConfig, DPOTrainer
from peft import LoraConfig

prefs = load_dataset("trl-lib/ultrafeedback_binarized", split="train")
config = DPOConfig(output_dir="qwen3-support-dpo", beta=0.1, learning_rate=5e-6,
                   per_device_train_batch_size=2, gradient_accumulation_steps=16,
                   max_length=2048, bf16=True, num_train_epochs=1)
trainer = DPOTrainer(model="qwen3-support-sft",          # start from the SFT checkpoint
                     args=config, train_dataset=prefs,
                     peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear"))
trainer.train()
```

The script loads a public preference dataset (UltraFeedback, already split into chosen and rejected
pairs), sets `beta=0.1` and a small learning rate, and starts from the SFT checkpoint saved in the
previous section. When the model is given with a LoRA config, TRL uses the base with adapters switched
off as the reference, so no second copy is loaded.

Use a much lower learning rate than SFT (5e-7 to 5e-6 for full fine-tuning; somewhat higher with LoRA).
Where do preference pairs come from? Human raters, LLM-as-judge ranking of several samples (**RLAIF**,
reinforcement learning from AI feedback), **on-policy** pairs sampled from your own SFT model (better
than **off-policy** pairs written by other models, because they show your model's own typical
mistakes), or implicit product feedback (thumbs, edits, regenerations).

### The preference-method zoo

Many DPO relatives exist. Two terms in the table: **prospect theory** is a model from behavioural
economics of how people weigh gains and losses, which KTO borrows; an **advantage** is how much better
one answer scored than the average answer for the same prompt.

| method | idea |
|---|---|
| **IPO** | adds a regulariser so DPO does not overfit deterministic preferences |
| **KTO** | learns from unpaired thumbs-up / thumbs-down signals (prospect theory) |
| **ORPO** | folds an odds-ratio preference term into SFT: one stage, no reference model |
| **SimPO** | length-normalised, reference-free implicit reward with a margin |
| **GRPO** | online RL (DeepSeek-R1): sample a group of answers, score them with a reward function (e.g. a verifier for maths/code), use group-relative advantages; no value model. TRL's `GRPOTrainer` |

RL with **verifiable rewards** (unit tests, exact-match answers, format checkers) via GRPO and similar
algorithms is how modern reasoning models are trained; DPO remains the workhorse for style, tone and
helpfulness preferences.

## 6. Evaluating a fine-tune

1. **Task evals on a held-out set** (examples never used in training) built *before* training: exact
   match / F1 for extraction, unit tests for code, schema validity for JSON, LLM-judge with a rubric
   for open-ended answers, pairwise **win rate** (how often judges prefer the new model's answer)
   versus the base model or the previous version.
2. **Regression evals** for general ability and safety: a few standard **benchmarks** (public test
   sets, e.g. via `lighteval` or `lm-evaluation-harness`: IFEval for instruction following, MMLU-Pro
   for broad knowledge, GSM8K for grade-school maths), plus your refusal and safety prompts. Fine-tunes
   often quietly lose safety behaviour.
3. **Vibe checks** on real prompts, side by side: informal reading by people, which catches problems
   numbers miss.
4. **Compare to strong baselines**: the base model with a good prompt and **few-shot** examples (a
   handful of worked examples in the prompt), and RAG. If the fine-tune does not beat them clearly, do
   not ship it.

The command below runs the IFEval benchmark on the fine-tuned model with zero few-shot examples
(`|0`) and writes the results to `evals/`:

```bash
lighteval accelerate "model_name=./qwen3-support-sft" "leaderboard|ifeval|0" --output-dir evals/
```

## 7. Packing, traced: why short examples waste compute

With padding, a batch costs as much as its longest example times the batch size. **Packing** fits several
examples into each fixed-length sequence instead. TRL's default strategy is best-fit decreasing (`bfd`):
sort examples by length, and place each into the fullest bin that still has room.

```python-run
import numpy as np
rng = np.random.default_rng(0)
MAX_LEN = 1024
lengths = np.clip(rng.lognormal(5.0, 0.8, 2000).astype(int), 10, MAX_LEN)   # token length of each example

def best_fit_decreasing(lengths, cap):
    bins = []                                   # remaining space in each bin
    for L in sorted(lengths, reverse=True):
        fits = [i for i, free in enumerate(bins) if free >= L]
        if fits:
            i = min(fits, key=lambda i: bins[i])    # the tightest bin that still fits
            bins[i] -= L
        else:
            bins.append(cap - L)
    return bins

bins = best_fit_decreasing(lengths, MAX_LEN)
real = int(lengths.sum())
B = 8
padded = sum(int(lengths[i:i + B].max()) * len(lengths[i:i + B]) for i in range(0, len(lengths), B))
print(f"examples: {len(lengths)}   real tokens: {real:,}")
print(f"padded batches of {B}: {padded:,} token slots  ({100 * real / padded:.0f}% useful)")
print(f"packed sequences  : {len(bins)} x {MAX_LEN} = {len(bins) * MAX_LEN:,} token slots  ({100 * real / (len(bins) * MAX_LEN):.0f}% useful)")
```

How the code works: `bins` holds the free space left in each packed sequence. Examples are taken
longest first; each goes into the bin with the *least* free space that still fits it (the "best
fit"), and a new bin is opened only when none fits. The padded baseline groups examples in eights and
pads each group to its longest member. The output: 2,000 examples with about 394,000 real tokens need
about 962,000 token slots when padded (41 percent useful) but only 385 packed sequences of 1,024 slots
(nearly 100 percent useful).

Roughly doubling the useful fraction of every forward pass is typical on chat datasets with many short
turns. The subtlety is isolation: examples packed into one sequence must not attend to each other, and
position ids must restart for each example. TRL's `bfd` strategy handles this with padding-free
attention; the older `wrapped` strategy concatenates and cuts, letting examples bleed into one
another, which is acceptable for raw-text pretraining but not for instruction data.

## 8. A debugging table for SFT and DPO

| symptom | likely cause | fix |
|---|---|---|
| fine-tuned model never stops | end-of-turn token masked from labels, wrong `eos_token`, pad token equal to EOS | check labels of one batch; set `eos_token` to the template's end-of-turn token; use a distinct pad token |
| model echoes or continues the user's text | loss computed on prompt tokens | prompt-completion format or `assistant_only_loss=True` |
| great training loss, poor real answers | template at serving differs from training | assert the rendered strings are identical |
| loss starts very high (above about 5) for an instruct model | wrong template or double BOS | print the rendered text and token ids |
| replies become short and generic | too many epochs on a narrow dataset | fewer epochs, lower LR, more diverse data |
| DPO loss stays at 0.693 | policy is not moving: LR too low or adapters not attached | check trainable parameters and `rewards/margins` |
| DPO loss collapses to 0 quickly and outputs degrade | LR too high or beta too low; the policy runs away from the reference | lower LR, raise beta, fewer steps |
| DPO `rewards/accuracies` high from step 0 | pairs are trivially separable, e.g. rejected answers are much shorter or malformed | build harder, on-policy pairs |
| eval metric better, users unhappy | eval set does not reflect real traffic | rebuild the eval set from production samples |

Before any long run, do the two cheap checks from the previous module: decode one collated batch
(inputs *and* labels, with special tokens visible), and overfit a handful of examples.

## 9. How much data, and what kind?

Rough guidance that holds up across reports from practitioners:

- **Format and style adaptation** (always answer in this JSON shape, in this voice): hundreds to a few
  thousand examples.
- **A narrow task** (classify, extract, route): a few thousand; here a fine-tuned small model often
  matches a much larger prompted one at a fraction of the cost and latency, which is the classic
  business case for fine-tuning.
- **New domain behaviour or multi-step skills**: tens of thousands, with careful coverage of edge cases.
- **Injecting facts**: prefer retrieval. Fine-tuning stores facts unreliably and they go stale.

Diversity matters more than count: 1,000 examples covering the full range of inputs beat 10,000
near-duplicates. Hold out the evaluation set **before** generating synthetic data or augmentations, so
paraphrases of test items cannot leak into training, and include examples of what the model should
*decline* or escalate, or it will learn that every input deserves a confident answer.

**Distillation** is the common way to get such data: have a strong **teacher** model answer real inputs
(optionally with reasoning), filter the outputs with automatic checks or a judge, and fine-tune the small
**student** model on the survivors. Check the teacher's licence terms; some providers restrict using outputs to
train competing models.

> [!INTERVIEW]
> **"Derive or explain DPO."** Start from the KL-regularised reward maximisation of RLHF; its optimal
> policy is $\pi^*(y|x) \propto \pi_{ref}(y|x)\exp(r(x,y)/\beta)$, so $r = \beta\log(\pi^*/\pi_{ref})$
> plus a prompt-only constant that cancels in Bradley-Terry comparisons. Substituting gives a logistic
> loss on the difference of log-ratio "implicit rewards" of chosen versus rejected. No reward model, no
> sampling, two models in memory; $\beta$ controls drift from the reference.

## Summary

- TRL SFT accepts text, messages, prompt-completion and conversational prompt-completion datasets; it
  trains on completions/assistant turns when configured.
- SFT = masked next-token cross-entropy; packing and LoRA make it cheap.
- DPO turns preference pairs into a logistic loss on implicit rewards relative to a frozen reference.
- KTO, ORPO, SimPO and GRPO cover unpaired feedback, single-stage training and verifiable-reward RL.
- Evaluate task performance, regressions and safety against strong prompt/RAG baselines.

## Glossary

- **Post-training**: training after pretraining that turns a base model into an assistant.
- **SFT (supervised fine-tuning)**: training on demonstration conversations with next-token loss.
- **Demonstration**: an example conversation showing the desired behaviour.
- **Prompt-completion format**: rows that separate the input from the part to be learned.
- **Completion-only / assistant-only loss**: training only on the answer tokens.
- **Contamination**: test items leaking into training data.
- **Packing (best-fit decreasing)**: filling each sequence with several short examples.
- **Preference pair (chosen / rejected)**: two answers to one prompt, one preferred.
- **Policy / reference model**: the model being trained / a frozen copy it is kept close to.
- **Reward model / Bradley-Terry**: a network that scores answers / the sigmoid-of-difference model of
  comparisons.
- **Sigmoid**: $\sigma(z) = 1/(1 + e^{-z})$, squashing any number into 0 to 1.
- **KL divergence**: a measure of how different two probability distributions are.
- **RLHF / PPO**: reinforcement learning from human feedback / the RL algorithm classically used for it.
- **DPO**: a logistic loss on preference pairs using implicit rewards; no reward model or sampling.
- **Implicit reward**: $\beta \log(\pi_\theta / \pi_{ref})$ for a response.
- **$\beta$ (beta)**: how strongly the policy is held close to the reference.
- **On-policy / off-policy data**: answers written by your own model / by other models.
- **KTO / ORPO / SimPO / GRPO**: preference or RL methods for unpaired feedback, single-stage training,
  reference-free rewards, and group-relative RL.
- **Verifiable reward**: a reward computed by a program, such as passing unit tests.
- **Held-out set / benchmark / win rate**: data never trained on / a public test set / how often
  judges prefer one model's answers.
- **Distillation (teacher / student)**: training a small model on a strong model's filtered outputs.

## Check yourself

```quiz
[
  {"q": "In a TRL prompt-completion dataset, what does SFT train on by default?",
   "options": ["Only the completion tokens", "Only the prompt tokens", "Prompt and completion equally", "Nothing until DPO"], "answer": 0,
   "explain": "completion_only_loss defaults to completion-only for prompt-completion data; prompt labels become -100."},
  {"q": "What is the DPO loss for a pair when the policy equals the reference model?",
   "options": ["log 2", "0", "1", "Infinite"], "answer": 0,
   "explain": "The margin is zero and -log sigmoid(0) = log 2, about 0.693."},
  {"q": "What does the beta parameter control in DPO?",
   "options": ["How strongly the policy is kept close to the reference", "The learning rate", "The LoRA rank", "Sampling temperature"], "answer": 0,
   "explain": "beta scales the implicit reward and corresponds to the KL penalty strength in RLHF."},
  {"q": "Which models must be held during DPO training?",
   "options": ["Policy and a frozen reference", "Policy, reference, reward model and value model", "Only a reward model", "Policy and value model"], "answer": 0,
   "explain": "DPO removes the separate reward and value models of PPO-based RLHF."},
  {"q": "Which method learns from unpaired thumbs-up/down feedback?",
   "options": ["KTO", "DPO", "SFT", "PPO with Bradley-Terry"], "answer": 0,
   "explain": "KTO uses binary desirable/undesirable labels rather than chosen/rejected pairs."},
  {"q": "GRPO differs from PPO mainly by...",
   "options": ["Using group-relative advantages from several samples instead of a value model", "Not using rewards", "Using human pairs only", "Being offline"], "answer": 0,
   "explain": "Sampling a group per prompt and normalising rewards within the group replaces the critic."},
  {"q": "Your fine-tune beats the base model on your eval set. What else must you check before shipping?",
   "options": ["Regression and safety evals, and comparison with a well-prompted or RAG baseline", "Nothing", "Only training loss", "Only perplexity"], "answer": 0,
   "explain": "Fine-tunes can lose general and safety behaviour and may not beat cheaper alternatives."}
]
```

> **Source:** TRL docs: SFT Trainer, Dataset formats, DPO Trainer, GRPO Trainer
> (https://huggingface.co/docs/trl); Rafailov et al., "Direct Preference Optimization" (2023); Ouyang et
> al., "InstructGPT" (2022); Shao et al., "DeepSeekMath" (GRPO, 2024); HF LLM Course ch. 11 and 12
> (fine-tuning and reasoning models, https://huggingface.co/learn/llm-course); Huyen, *AI Engineering*,
> ch. 2 (post-training, RLHF, DPO), ch. 7 (finetuning) and ch. 8 (dataset engineering).
