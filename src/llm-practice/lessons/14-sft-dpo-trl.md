# SFT and DPO with TRL: data, training loop, evaluation

Post-training turns a base model into an assistant in (at least) two stages: **supervised fine-tuning
(SFT)** on demonstrations, then **preference optimisation** (RLHF, DPO and relatives, or RL with
verifiable rewards). Hugging Face's **TRL** library implements all of them on top of `Trainer`. This
lesson walks through data formats, the losses, working training scripts, and how to evaluate the
result. The AI Engineering track covers the strategy (when to fine-tune, data quantity and quality);
here we write the code and derive the losses.

## 1. Data formats TRL understands

TRL accepts four shapes for SFT (current TRL v1 docs):

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

And for preference methods (DPO, ORPO, KTO-paired, reward modelling):

```python
{"prompt": [{"role": "user", "content": "Explain RoPE in one line."}],
 "chosen": [{"role": "assistant", "content": "RoPE rotates Q and K by position-dependent angles..."}],
 "rejected": [{"role": "assistant", "content": "RoPE is a kind of rope used in sailing."}]}
```

Tool-calling SFT adds a `tools` column (JSON schemas) and `tool_calls` / `tool` role messages.

**Data work dominates outcomes**: dedupe, filter low quality (LLM-judge scoring, heuristics), balance
task types, remove eval-set contamination, and look at samples. A few thousand excellent, diverse
examples routinely beat hundreds of thousands of mediocre ones for style and format adaptation.

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

## 2. SFT: the loss

SFT is ordinary next-token cross-entropy, but usually **only on the completion / assistant tokens**:

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

Notes:

- Passing a model id string lets TRL load it (with `model_init_kwargs` for dtype etc.).
- **Packing** concatenates examples to fill `max_length`, avoiding padding waste; modern TRL uses
  position-id resets / padding-free attention so packed examples do not attend to each other.
- Watch `mean_token_accuracy`, train/eval loss and, above all, **sampled generations** at checkpoints.
- **Overfitting signs**: eval loss rising while train loss falls; outputs copying training phrases;
  degraded general ability. 1 to 3 epochs is typical for SFT.
- Fine-tuning a base model? Set the chat template (`chat_template_path`) and EOS token correctly
  (module 2), or the result will not stop generating.

## 4. Preference optimisation: from RLHF to DPO

Classic **RLHF** (InstructGPT): train a reward model $r_\phi(x, y)$ on human comparisons with a
Bradley-Terry loss, then optimise the policy with PPO to maximise reward minus a KL penalty to a
reference model $\pi_{ref}$ (the SFT model):

$$
\max_\theta\; \mathbb{E}_{y \sim \pi_\theta}\left[r_\phi(x, y)\right] - \beta\,\mathrm{KL}\left(\pi_\theta(\cdot|x)\,\|\,\pi_{ref}(\cdot|x)\right)
$$

PPO needs four models in memory (policy, reference, reward, value) and is finicky.

**DPO** (Rafailov et al. 2023) shows that this objective has a closed-form optimal policy, so the
reward can be expressed through the policy itself: $r(x, y) = \beta \log \frac{\pi_\theta(y|x)}{\pi_{ref}(y|x)} + \text{const}$.
Plugging into Bradley-Terry gives a simple classification-style loss on preference pairs
$(x, y_w, y_l)$:

$$
\mathcal{L}_{DPO} = -\log \sigma\!\left(\beta\left[\log\frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \log\frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\right]\right)
$$

- $\log \pi(y|x)$ is the **sum of token log-probs of the response** given the prompt.
- The bracket is the difference of **implicit rewards** $\beta \log \frac{\pi_\theta}{\pi_{ref}}$ for the
  chosen and rejected responses. TRL logs them as `rewards/chosen`, `rewards/rejected`,
  `rewards/margins` and `rewards/accuracies` (fraction of pairs where chosen beats rejected).
- $\beta$ (0.1 typical) controls how far the policy may drift from the reference.
- Only two models (policy and frozen reference); with LoRA the reference is just the base with adapters
  disabled, so one copy of weights suffices.

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

Use a much lower learning rate than SFT (5e-7 to 5e-6 for full fine-tuning; somewhat higher with LoRA).
Where do preference pairs come from? Human raters, LLM-as-judge ranking of several samples (RLAIF),
"on-policy" pairs sampled from your own SFT model (better than off-policy pairs from other models), or
implicit product feedback (thumbs, edits, regenerations).

### The preference-method zoo

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

1. **Task evals on a held-out set** built *before* training: exact match / F1 for extraction, unit
   tests for code, schema validity for JSON, LLM-judge with a rubric for open-ended answers, pairwise
   win rate versus the base model or the previous version.
2. **Regression evals** for general ability and safety: a few standard benchmarks (e.g. via
   `lighteval` or `lm-evaluation-harness`: IFEval for instruction following, MMLU-Pro, GSM8K), plus
   your refusal and safety prompts. Fine-tunes often quietly lose safety behaviour.
3. **Vibe checks** on real prompts, side by side.
4. **Compare to strong baselines**: the base model with a good prompt and few-shot examples, and RAG.
   If the fine-tune does not beat them clearly, do not ship it.

```bash
lighteval accelerate "model_name=./qwen3-support-sft" "leaderboard|ifeval|0" --output-dir evals/
```

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
