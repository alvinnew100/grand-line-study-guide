# Data curation: quality, coverage, quantity

Huyen writes that a model is only as good as the data it was trained on, and that the best ML team with unlimited compute cannot finetune a good model without good data. As models become commodities, **data is the differentiator**. This module covers **dataset engineering**: creating a dataset that lets you train the best model within your budget. This lesson covers **data curation**: what data you need, and how to think about its **quality, coverage and quantity**, and how to acquire and annotate it.

## 1. Data-centric AI

There are two ways to improve AI performance:

- **Model-centric AI**: improve the model itself by designing new architectures, making models bigger, or inventing training techniques.
- **Data-centric AI**: improve the data through better processing and higher-quality datasets, so that better models can be trained with fewer resources.

Benchmarks used to be model-centric: given a fixed dataset such as ImageNet, build the best model. Newer efforts are data-centric: given a fixed model, build the best dataset. Andrew Ng's 2021 data-centric AI competition and DataPerf are examples. Huyen stresses that meaningful progress needs **both**, and that dataset engineering is mostly "toil, tears and sweat". It is unglamorous and decisive.

> [!NOTE]
> This module focuses on data for **finetuning**. The same principles apply to pre-training data (Module 2) and evaluation data (Module 4). Much of what you learn annotating evaluation data, especially the guidelines, transfers directly to training data.

## 2. What data do you need?

The data should **exhibit the behaviours you want the model to learn**. The format follows the training method:

| Training method | Data format |
|---|---|
| Self-supervised finetuning | sequences of raw data |
| Instruction (supervised) finetuning | (instruction, response) |
| Preference finetuning | (instruction, winning response, losing response) |
| Reward model training | comparison data, or ((instruction, response), score) |

Some behaviours are especially hard to get data for:

- **Chain-of-thought.** To teach step-by-step reasoning, responses must *contain* the steps. Including CoT responses in finetuning data nearly doubled accuracy on some CoT tasks ("Scaling Instruction-Finetuned Language Models"). Writing step-by-step solutions is tedious, so CoT datasets are less common.
- **Tool use.** Domain experts can write (task, actions) examples. But what is efficient for humans differs from what is efficient for AI. Humans prefer GUIs, and models work better with APIs. A human might do steps sequentially where an AI could run them in parallel. So human demonstrations may be suboptimal. **Simulations** and synthetic data help, and tool-use data often needs special message formats. Llama 3, for instance, designed a multi-message chat format for tool calls.
- **Single-turn vs multi-turn.** Single-turn data is easier to get, but real tasks often need back-and-forth clarification. Multi-turn data is harder to collect and annotate.

Curation also includes **removing** data to make a model unlearn behaviours. If a model is too sassy, removing sassy examples helps.

## 3. Data quality

A small amount of high-quality data can beat a large amount of noisy data. The Yi model developers found that 10K carefully crafted instructions were better than hundreds of thousands of noisy ones. The **LIMA** paper showed that a 65B Llama model finetuned on only **1,000 carefully curated prompts and responses** produced answers equivalent to or preferred over GPT-4's in 43% of cases. The downside is that it was less robust than product-grade models. The Llama 3 team found human-generated data more prone to errors and inconsistencies, especially for nuanced safety policies, and built AI-assisted annotation tools.

Huyen's six characteristics of high-quality data:

1. **Relevant** to the task. A 19th-century legal dataset is not relevant to today's legal questions, unless the task is about 19th-century law.
2. **Aligned with task requirements.** If the task needs factual consistency, annotations must be factually correct. If it needs creativity, they should be creative. If it needs scores with justifications, include both. If it needs conciseness, be concise. Huyen says "aligned" rather than "accurate" because a correct response is not always what the user wants.
3. **Consistent** across examples and annotators. Would two essays with the same score really be the same quality? Inconsistency confuses the model. A good **annotation guideline** is the key.
4. **Correctly formatted.** Follow the model's expected format and remove redundant formatting tokens such as HTML tags from scraped reviews. Watch for trailing whitespace, stray newlines, and inconsistent casing or number formats.
5. **Sufficiently unique.** Duplicates introduce bias and contamination. Use cases differ in how much duplication they tolerate.
6. **Compliant** with internal and external policies, laws and regulations. Remove PII if you are not allowed to train on it.

## 4. Data coverage (diversity)

Training data should cover the range of problems the model will face. Users write long detailed instructions and short ones, with typos and without, in different languages and formats. If the model will see typos, include typos.

The dimensions of diversity depend on the application. Examples are task type (summarization, QA, classification), topic (fashion, finance, tech), language, expected output format (JSON, yes/no), output length, number of turns, and tool use. A French-to-English translator needs topic, length and style diversity but not language diversity. A global support bot needs linguistic and cultural diversity.

Llama 3's developers reported that their gains came mostly from **data quality and diversity** rather than architecture. Their data mix by training phase:

| Domain | Pre-training | Supervised finetuning | Preference finetuning |
|---|---|---|---|
| General knowledge (English) | 50% | 52.66% | 81.99% |
| Math and reasoning | 25% | 21.19% | 5.89% |
| Coding | 17% | 14.89% | 6.93% |
| Multilingual | 8% | 3.01% | 5.19% |
| Exam-like | — | 8.14% | — |
| Long context | — | 0.11% | — |

Math, reasoning and code together are roughly 40% of pre-training and SFT data, far more than their share of the internet. That means **high-quality code and math data boosts reasoning more than natural language text does**. Preference data has much less math and code, because preference finetuning aims at the real distribution of user preferences.

How do you find the right mix? Experiment. "Ask Me Anything" (Chen et al., 2023) found that diversity along some dimensions helped more than others. Experiments also show that with the same number of examples, more diverse data performs better.

## 5. Data quantity

Asking how much data you need is like asking how much money you need. It varies widely. Jeremy Howard and Jonathan Whitaker showed that LLMs can learn from a *single* example, and some teams finetune on millions.

> [!NOTE]
> With millions of examples, should you train from scratch? Evaluate it. Finetuning is usually more efficient, but **ossification** can occur: pre-training can freeze weights so they adapt less well to finetuning data (Hernandez et al., 2021). Smaller models are more susceptible.

Three factors besides quality and diversity:

- **Finetuning technique.** Full finetuning needs orders of magnitude more data than PEFT. With tens of thousands to millions of pairs, try full finetuning. With a few hundred to a few thousand, PEFT such as LoRA.
- **Task complexity.** Sentiment classification needs far less data than QA over financial filings.
- **Base model performance.** The closer the base model is to the target, the fewer examples you need. OpenAI's finetuning guide shows that with 100 examples the more advanced models finetune much better, while after 550,000 examples all five models performed similarly.

So: **little data → PEFT on stronger models; lots of data → full finetuning on smaller models.**

### Start small and plot the curve

Before investing in a large dataset, try a small, well-crafted one, around **50 examples**, to see whether finetuning helps at all. Clear improvement suggests that more data will help more. No improvement with small data rarely gets fixed by more data. First rule out other causes such as hyperparameters, data quality and prompts. In the vast majority of cases you should see improvement after 50–100 examples.

Then finetune on **25%, 50% and 100%** of your data and plot performance against dataset size. A steep slope means that doubling the data will pay off. A plateau means it will not.

```python-run
import numpy as np
# Performance-vs-data curve: fit a simple saturating model to decide whether more data is worth it.
sizes = np.array([250, 500, 1000])
scores = np.array([0.62, 0.70, 0.75])            # eval metric at 25%, 50%, 100% of data
a, b = np.polyfit(np.log(sizes), scores, 1)      # score ~ a*ln(n) + b  (diminishing returns)
for n in [1000, 2000, 4000, 8000]:
    print(f"n={n:5d}  predicted score ~ {min(1.0, a*np.log(n)+b):.3f}")
print(f"\nEach doubling adds about {a*np.log(2):.3f}. Compare that with the cost of annotating that many more examples.")
```

A useful trick: you can reduce the amount of **high-quality** data needed by first finetuning on **lower-quality or less relevant data**: self-supervised on raw domain text, then supervised; less relevant data, then relevant (for example tweets before product reviews); or synthetic data, then real data. Mixing data carelessly can hurt, so evaluate.

Quantity is not only about the number of examples. **Tokens per example** matter too. Very long examples may exceed context limits, and very short ones may teach little.

## 6. Data acquisition and annotation

The most valuable source is usually **your own application data**. It matches your distribution exactly, and it enables the **data flywheel**: user data improves the product, which attracts more users, which gives more data (Module 10 covers feedback collection). Check user privacy and consent.

Other sources:

- **Public datasets.** Hugging Face and Kaggle host hundreds of thousands. Others are Google Dataset Search, government portals (Data.gov), ICPSR, the UCI ML Repository, OpenML, the Open Data Network, cloud providers' open data, and datasets bundled with ML frameworks and evaluation harnesses. **Never fully trust public data.** Inspect and validate it, and always check the **license**, since parts of a commercially licensed dataset may come from sources that do not allow commercial use.
- **Purchased or proprietary data** from vendors.
- **Annotation**, in-house or outsourced.
- **Synthesis** (next lesson).

Real pipelines mix sources. Huyen's illustration: start with a public dataset of 10,000 examples, remove low-quality instructions to leave 9,000, set aside 3,000 with low-quality responses to leave 6,000, hand-write responses for those 3,000 to reach 9,000, notice a gap on topic X, write 100 templates and synthesize 2,000 instructions, and annotate them to reach 11,000. Along the way you may find your guidelines were wrong and need to re-annotate.

### Annotation guidelines

Annotation is hard because **writing clear guidelines is hard**. You must decide what a good response is, what makes one better than another, and whether a correct but unhelpful answer counts. LinkedIn reported that creating guidelines was one of the hardest parts of its pipeline, and annotation is often abandoned halfway because of the effort. Guidelines you wrote for **evaluation** data (rubrics with examples) can be reused for training data, and evaluation examples can be augmented into training examples.

```python-run
# A tiny data-quality report: format, duplicates, coverage by task type, token-length distribution.
import re, collections, statistics
data = [
  {"task": "summarize", "instruction": "Summarize: <p>Sales rose 3%.</p>", "response": "Sales rose 3%."},
  {"task": "summarize", "instruction": "Summarize: <p>Sales rose 3%.</p>", "response": "Sales rose 3%."},
  {"task": "classify",  "instruction": "Sentiment of 'great!'?", "response": "POSITIVE"},
  {"task": "classify",  "instruction": "Sentiment of 'meh'?", "response": "neutral "},
  {"task": "qa",        "instruction": "Capital of Vietnam?", "response": ""},
]
issues = collections.Counter()
seen = set()
for ex in data:
    key = (ex["instruction"].strip().lower(), ex["response"].strip().lower())
    if key in seen: issues["duplicate"] += 1
    seen.add(key)
    if re.search(r"<[^>]+>", ex["instruction"]): issues["html tags"] += 1
    if ex["response"] != ex["response"].strip(): issues["trailing whitespace"] += 1
    if not ex["response"].strip(): issues["empty response"] += 1
print("issues:", dict(issues))
print("coverage by task:", dict(collections.Counter(ex["task"] for ex in data)))
lens = [len(ex["instruction"].split()) + len(ex["response"].split()) for ex in data]
print("words per example: min", min(lens), "median", statistics.median(lens), "max", max(lens))
labels = collections.Counter(ex["response"].strip() for ex in data if ex["task"] == "classify")
print("label spellings (inconsistent casing is a consistency problem):", dict(labels))
```

> [!INTERVIEW]
> **"You have budget to label 2,000 examples for finetuning. How do you spend it?"** Clarify the target behaviour and write the annotation guideline first, reusing the eval rubric. Define the coverage dimensions (task types, topics, lengths, languages, edge cases such as typos and out-of-scope) and allocate examples across them, weighting toward known failure modes. Label about 50–100 first, finetune and confirm improvement. Then scale, plotting performance at 25/50/100% to decide whether more data pays off. Enforce quality: relevance, alignment with task requirements, consistency (double-annotate a subset and measure agreement), correct formatting, deduplication and compliance. Prefer production data, and use PEFT on a strong base model given the small data size.

## Pitfalls

- Treating quantity as the goal. A thousand curated examples can beat a hundred thousand noisy ones.
- No annotation guideline, so labels are inconsistent.
- Training data that does not match production: no typos, no multi-turn, one language.
- Trusting public datasets without inspecting them or checking licenses.
- Building a huge dataset before checking that 50 examples help at all.

## Summary

- **Data-centric AI** improves models by improving data. As models commoditize, data is the differentiator.
- Data must show the behaviours you want. Formats follow the training method. CoT, tool-use and multi-turn data are hard to get.
- **Quality**: relevant, aligned with task requirements, consistent, correctly formatted, sufficiently unique, compliant.
- **Coverage**: diversity along the dimensions your users vary on. Llama 3's mix shows heavy use of math and code for reasoning.
- **Quantity**: depends on technique (PEFT vs full), task complexity and base model. Start with about 50 examples and plot the curve at 25/50/100%.
- **Acquisition**: your application data (the data flywheel), public and purchased data (verify and check licenses), annotation with clear guidelines, and synthesis.

```quiz
[
  {"q": "Data-centric AI means…", "options": ["Designing new architectures", "Improving performance by improving the data rather than the model", "Using only synthetic data", "Avoiding evaluation"], "answer": 1, "explain": "Given a model, build the best dataset. This complements model-centric work."},
  {"q": "What did the LIMA paper show?", "options": ["More data always wins", "A 65B model finetuned on only 1,000 carefully curated examples can be competitive with far stronger models in many cases", "Synthetic data fails", "Finetuning needs millions of examples"], "answer": 1, "explain": "A small amount of high-quality data can go a long way, though the result was less robust than product-grade models."},
  {"q": "Why does Huyen say data should be 'aligned with task requirements' rather than 'accurate'?", "options": ["Accuracy is impossible", "Depending on the task, a correct response may not be what's wanted (e.g., it must be creative, concise or justified)", "Alignment is cheaper", "Accuracy only applies to images"], "answer": 1, "explain": "Annotations should reflect what the task actually requires."},
  {"q": "In Llama 3's data mix, math/reasoning and code together made up roughly what share of pre-training data?", "options": ["5%", "15%", "40%", "90%"], "answer": 2, "explain": "25% math and reasoning plus 17% code: far above their share of the internet, because they boost reasoning."},
  {"q": "You have 300 labeled examples. Which approach generally fits best?", "options": ["Full finetuning of a small model", "PEFT (e.g., LoRA) on a stronger base model", "Train from scratch", "No evaluation needed"], "answer": 1, "explain": "Little data → PEFT on advanced models. Lots of data → full finetuning on smaller models."},
  {"q": "Finetuning on 50 well-crafted examples shows no improvement. What should you conclude first?", "options": ["Buy 1M examples", "Check other causes (hyperparameters, data quality, prompts); more data rarely fixes zero improvement", "Finetuning never works", "Switch to pre-training"], "answer": 1, "explain": "In most cases 50-100 examples should show gains. If not, look for other problems before scaling data."},
  {"q": "Why plot performance at 25%, 50% and 100% of your data?", "options": ["To reduce training time", "To see the slope and estimate whether more data will pay off", "To detect contamination", "To pick the tokenizer"], "answer": 1, "explain": "A steep curve suggests more data helps, and a plateau suggests diminishing returns."},
  {"q": "What is the data flywheel?", "options": ["A vector database", "Using data from users to improve the product, which attracts more users and more data", "A deduplication algorithm", "A GPU scheduler"], "answer": 1, "explain": "Application data is the most relevant source and compounds over time."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 8 ("Data Curation": data quality, data coverage, data quantity, data acquisition and annotation).
