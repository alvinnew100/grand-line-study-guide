# Data curation: quality, coverage, quantity

> **Before this lesson:** read [When (and when not) to finetune](#/lesson/ai-eng/aie-when-finetune) and [PEFT, LoRA, model merging and hyperparameters](#/lesson/ai-eng/aie-peft-lora), which explain supervised and preference finetuning, LoRA and full finetuning. Rubrics and annotation guidelines first appear in [Designing your evaluation pipeline](#/lesson/ai-eng/aie-eval-pipeline). The demos use basic Python and a little NumPy, explained line by line.

## In plain words

A model learns from examples, so the examples decide what it becomes. **Data curation** is the work of choosing, collecting, cleaning and labelling the examples you train on: deciding what data you need, judging its **quality**, making sure it **covers** the situations the model will face, and working out **how much** you need. Huyen writes that a model is only as good as the data it was trained on, and that even the best team with unlimited compute cannot finetune a good model without good data. As models become commodities that anyone can download or rent, **data is what sets products apart**.

An everyday picture: teaching a new cook from a binder of example recipes. If the recipes have typos in the quantities (low quality), the cook learns the typos. If every recipe is for pasta (low coverage), the cook is lost when asked for soup. If there are three recipes, the cook cannot generalise; if there are ten thousand near-identical ones, most of the binder is wasted. And if different authors wrote "a pinch" to mean different amounts (inconsistent labelling), the cook ends up confused. Curating training data is assembling a good binder.

Why this matters for a job: **dataset engineering**, creating a dataset that lets you train the best model within your budget, is where much of the real work in finetuning happens. Interviewers ask "You have budget to label 2,000 examples, how do you spend it?" and expect you to talk about guidelines, coverage, quality checks and learning curves. This lesson covers what data you need, quality, coverage, quantity, and how to acquire and **annotate** (label) data.

## 1. Data-centric AI

There are two broad ways to improve an AI system:

- **Model-centric AI**: improve the model itself, by designing new architectures, making models bigger, or inventing training techniques.
- **Data-centric AI**: improve the data, through better processing and higher-quality datasets, so that better models can be trained with fewer resources.

Benchmarks used to be model-centric: given a fixed dataset such as ImageNet, build the best model. Newer efforts are data-centric: given a fixed model, build the best dataset. Andrew Ng's 2021 data-centric AI competition and the DataPerf benchmark are examples. Huyen stresses that real progress needs **both**, and describes dataset engineering as mostly toil: unglamorous, slow, and decisive.

> [!NOTE]
> This module focuses on data for **finetuning**. The same principles apply to pre-training data (Module 2) and evaluation data (Module 4). Much of what you learn annotating evaluation data, especially the guidelines, carries over directly to training data.

## 2. What data do you need?

The data should **show the behaviours you want the model to learn**. Its format follows the training method:

| Training method | Data format |
|---|---|
| Self-supervised finetuning | sequences of raw text |
| Instruction (supervised) finetuning | (instruction, response) |
| Preference finetuning | (instruction, winning response, losing response) |
| Reward model training | comparison data, or ((instruction, response), score) |

A **reward model** is a model trained to score responses, used in preference finetuning (see the post-training lesson). Some behaviours are especially hard to find data for:

- **Chain-of-thought (CoT).** To teach step-by-step reasoning, the responses in the data must *contain* the steps. Adding CoT responses to finetuning data nearly doubled accuracy on some reasoning tasks (reported in "Scaling Instruction-Finetuned Language Models"). Writing step-by-step solutions is tedious, so CoT datasets are less common.
- **Tool use.** Domain experts can write (task, actions) examples, but what is efficient for people differs from what is efficient for AI. People prefer **GUIs** (graphical user interfaces: buttons and menus); models work better with **APIs** (programmatic interfaces). A person may do steps one after another where an AI could run them in parallel. So human demonstrations can teach inefficient habits. **Simulations** and synthetic data help, and tool-use data often needs special message formats; Llama 3, for instance, designed a multi-message chat format for tool calls.
- **Single-turn versus multi-turn.** Single-turn data (one question, one answer) is easier to get, but real tasks often need back-and-forth clarification. Multi-turn data is harder to collect and to label.

Curation also includes **removing** data to make a model *unlearn* a behaviour. If a model is too sassy, removing sassy examples helps.

## 3. Data quality

A small amount of high-quality data can beat a large amount of noisy data. The developers of the Yi models found 10,000 carefully crafted instructions worked better than hundreds of thousands of noisy ones. The **LIMA** paper showed that a 65B Llama model finetuned on only **1,000 carefully curated prompts and responses** gave answers judged equivalent to or better than GPT-4's in 43% of cases, though it was less robust than production models. The Llama 3 team found that human-written data was more prone to errors and inconsistencies than expected, especially for subtle safety policies, and built AI-assisted annotation tools.

Huyen lists six characteristics of high-quality data:

1. **Relevant** to the task. A 19th-century legal dataset is not relevant to today's legal questions, unless the task is about 19th-century law.
2. **Aligned with task requirements.** If the task needs factual consistency, the annotations must be factually correct. If it needs creativity, they should be creative. If it needs scores with justifications, include both. If it needs conciseness, be concise. Huyen says "aligned" rather than "accurate" because a correct response is not always what the user wants.
3. **Consistent** across examples and annotators. Would two essays given the same score really be of the same quality? Inconsistent labels confuse the model. A good **annotation guideline**, the written instructions that tell labellers exactly how to label, is the key.
4. **Correctly formatted.** Follow the format the model expects, and remove leftover formatting such as HTML tags from scraped reviews. Watch for trailing spaces, stray line breaks, and inconsistent capitalisation or number formats.
5. **Sufficiently unique.** Duplicates introduce bias (the model over-learns what is repeated) and can contaminate evaluation. Use cases differ in how much repetition they tolerate.
6. **Compliant** with internal and external policies, laws and regulations. Remove **PII** (personally identifiable information, such as names, emails and phone numbers) if you are not allowed to train on it.

Many of these checks can be automated. Here is a small data-quality report:

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

**Reading this Python line by line**

- `data` is a list of five training examples, each a dictionary with a task type, an instruction and a response. Several have planted problems.
- `issues = collections.Counter()` starts an empty tally; `issues["duplicate"] += 1` adds one to a named count (a `Counter` starts every key at 0).
- `seen` is a set of (instruction, response) pairs already met, lowercased and with spaces trimmed, so exact repeats are caught.
- `re.search(r"<[^>]+>", ...)` looks for anything shaped like an HTML tag: a `<`, one or more characters that are not `>`, then `>`.
- `ex["response"] != ex["response"].strip()` is true when the response has spaces at either end; `not ex["response"].strip()` is true when it is empty.
- The coverage line counts examples per task type; the lengths line counts words per example; `statistics.median` gives the middle value.
- The last check collects the labels used for the classification task.
- Output: `issues: {'html tags': 2, 'duplicate': 1, 'trailing whitespace': 1, 'empty response': 1}`, coverage of 2 summarise, 2 classify and 1 QA example, word counts from 3 to 7 (median 4), and label spellings `POSITIVE` and `neutral`: the labels use inconsistent capitalisation, a consistency problem that would confuse a classifier.

## 4. Data coverage (diversity)

**Coverage**, also called diversity, means the training data spans the range of situations the model will meet. Users write long detailed instructions and short vague ones, with typos and without, in different languages and formats. If the model will see typos in production, include typos in training.

The dimensions that matter depend on the application: task type (summarisation, question answering, classification), topic (fashion, finance, technology), language, expected output format (JSON, yes/no), output length, number of turns, and tool use. A French-to-English translator needs variety in topic, length and style but not in language. A global support bot needs linguistic and cultural variety.

Llama 3's developers reported that their improvements came mostly from **data quality and diversity** rather than from architecture changes. Their **data mix** (the share of each kind of data) by training phase:

| Domain | Pre-training | Supervised finetuning | Preference finetuning |
|---|---|---|---|
| General knowledge (English) | 50% | 52.66% | 81.99% |
| Math and reasoning | 25% | 21.19% | 5.89% |
| Coding | 17% | 14.89% | 6.93% |
| Multilingual | 8% | 3.01% | 5.19% |
| Exam-like | — | 8.14% | — |
| Long context | — | 0.11% | — |

Maths, reasoning and code together are roughly 40% of the pre-training and SFT data, far more than their share of the internet. The lesson drawn is that **high-quality code and maths data improves reasoning more than ordinary text does**. Preference data has much less maths and code because preference finetuning aims to match what real users ask about and prefer.

How do you find the right mix for your own model? Experiment. "Ask Me Anything" (Chen and colleagues, 2023) found that variety along some dimensions helped more than along others. Experiments also show that, for the same number of examples, more diverse data performs better.

## 5. Data quantity

Asking how much data you need is like asking how much money you need: it varies enormously. Jeremy Howard and Jonathan Whitaker showed that language models can learn from a *single* example in some settings, while some teams finetune on millions.

> [!NOTE]
> With millions of examples, should you train a model from scratch instead of finetuning? Evaluate it. Finetuning is usually more efficient, but **ossification** can occur: pre-training can set the weights so firmly that they adapt less well to new finetuning data (Hernandez and colleagues, 2021). Smaller models are more prone to this.

Besides quality and diversity, three factors decide how much you need:

- **Finetuning technique.** Full finetuning needs orders of magnitude more data than PEFT methods such as LoRA. With tens of thousands to millions of pairs, try full finetuning; with a few hundred to a few thousand, use PEFT.
- **Task complexity.** Sentiment classification needs far less data than answering questions about financial filings.
- **Base model performance.** The closer the base model already is to what you want, the fewer examples you need. OpenAI's finetuning guide shows that with 100 examples the more advanced models finetuned much better, while after 550,000 examples all five models performed similarly.

So: **little data → PEFT on a stronger model; lots of data → full finetuning on a smaller model.**

### Start small and plot the curve

Before investing in a large dataset, try a small, well-crafted one of around **50 examples** to see whether finetuning helps at all. Clear improvement suggests more data will help more. No improvement with a small set is rarely fixed by adding more data: first rule out other causes, such as hyperparameters, data quality and prompts. In the vast majority of cases you should see improvement after 50–100 examples.

Then finetune on **25%, 50% and 100%** of your data and plot performance against dataset size. This plot is a **learning curve**. A steep slope means doubling the data will pay off; a plateau means it will not. A simple way to extrapolate is to assume each doubling of data adds roughly the same improvement, which means the score grows with the logarithm of the dataset size:

$$\text{score} \approx a \cdot \ln(n) + b$$

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

**Reading this Python line by line**

- `sizes` and `scores` are the three points of the learning curve: evaluation scores after finetuning on 250, 500 and 1,000 examples.
- `np.polyfit(x, y, 1)` fits a straight line $y = a x + b$ to the points and returns `a` and `b`. Fitting against `np.log(sizes)` instead of `sizes` means we fit the logarithmic curve above.
- The loop predicts scores for larger datasets; `min(1.0, ...)` stops predictions passing a perfect score.
- `a*np.log(2)` is the predicted gain per doubling, because $\ln(2n) - \ln(n) = \ln 2$.
- Output: about 0.755 at 1,000 examples (close to the observed 0.75), 0.820 at 2,000, 0.885 at 4,000 and 0.950 at 8,000, with each doubling adding about 0.065. Treat the far predictions with caution: real curves usually flatten faster than a logarithm, so measure again after each doubling rather than trusting an eight-fold extrapolation.

A useful trick: you can reduce the amount of **high-quality** data you need by first finetuning on **lower-quality or less relevant data**: self-supervised on raw domain text, then supervised; less relevant data first, then relevant (for example tweets before product reviews); or synthetic data first, then real data. Mixing data carelessly can hurt, so evaluate each step.

Quantity is not only the number of examples: **tokens per example** matter too. Very long examples may exceed the context limit, and very short ones may teach little.

## 6. Data acquisition and annotation

The most valuable source is usually **your own application data**. It matches your real users exactly, and it enables the **data flywheel**: user data improves the product, which attracts more users, who produce more data (Module 10 covers collecting feedback). Check user privacy and consent first.

Other sources:

- **Public datasets.** Hugging Face and Kaggle host hundreds of thousands. Others include Google Dataset Search, government portals such as Data.gov, ICPSR, the UCI Machine Learning Repository, OpenML, the Open Data Network, cloud providers' open data, and datasets bundled with ML frameworks and evaluation harnesses. **Never fully trust public data.** Inspect and validate it, and always check the **license** (the legal terms of use): parts of a dataset released for commercial use may come from sources that do not allow it.
- **Purchased or proprietary data** from vendors.
- **Annotation**, done in-house or outsourced to labelling companies.
- **Synthesis**, generating data with AI (next lesson).

Real pipelines mix sources. Huyen's illustration: start with a public dataset of 10,000 examples; remove low-quality instructions, leaving 9,000; set aside 3,000 whose responses are poor, leaving 6,000; hand-write new responses for those 3,000, back to 9,000; notice a gap on topic X, write 100 templates and synthesise 2,000 instructions; annotate them, reaching 11,000. Along the way you may discover your guidelines were wrong and have to re-annotate.

### Annotation guidelines

Annotation is hard because **writing clear guidelines is hard**. You must decide what a good response is, what makes one response better than another, and whether a correct but unhelpful answer counts. LinkedIn reported that creating guidelines was one of the hardest parts of its pipeline, and annotation projects are often abandoned halfway because of the effort. The guidelines you wrote for **evaluation** data (rubrics with examples) can be reused for training data, and evaluation examples can be extended into training examples (as long as you keep the test set separate). To check consistency, have two annotators label the same subset and measure how often they agree (the Cohen's kappa idea from the evaluation pipeline lesson).

> [!INTERVIEW]
> **"You have budget to label 2,000 examples for finetuning. How do you spend it?"** Clarify the target behaviour and write the annotation guideline first, reusing the evaluation rubric. Define the coverage dimensions (task types, topics, lengths, languages, edge cases such as typos and out-of-scope requests) and spread examples across them, weighting toward known failure modes. Label about 50–100 first, finetune and confirm improvement. Then scale, plotting performance at 25/50/100% to decide whether more data pays off. Enforce quality: relevance, alignment with task requirements, consistency (double-annotate a subset and measure agreement), correct formatting, deduplication and compliance. Prefer production data, and use PEFT on a strong base model given the small data size.

## Pitfalls

- Treating quantity as the goal. A thousand curated examples can beat a hundred thousand noisy ones.
- No annotation guideline, so labels are inconsistent.
- Training data that does not look like production: no typos, no multi-turn, one language.
- Trusting public datasets without inspecting them or checking licenses.
- Building a huge dataset before checking that 50 examples help at all.

## Summary

- **Data-centric AI** improves models by improving data. As models become commodities, data is what differentiates.
- Data must show the behaviours you want, in the format of the training method. CoT, tool-use and multi-turn data are hard to get.
- **Quality**: relevant, aligned with task requirements, consistent, correctly formatted, sufficiently unique, compliant.
- **Coverage**: variety along the dimensions your users vary on. Llama 3's mix uses a lot of maths and code to build reasoning.
- **Quantity**: depends on technique (PEFT versus full), task complexity and base model. Start with about 50 examples and plot the learning curve at 25/50/100%.
- **Acquisition**: your application data (the data flywheel), public and purchased data (verify and check licenses), annotation with clear guidelines, and synthesis.

## Glossary

- **Data curation**: choosing, collecting, cleaning and labelling training data.
- **Dataset engineering**: building the dataset that gives the best model within a budget.
- **Model-centric / data-centric AI**: improving the model / improving the data.
- **Annotate / annotator**: attach labels to examples / the person (or model) doing it.
- **Annotation guideline**: written instructions telling annotators exactly how to label.
- **Reward model**: a model that scores responses, used in preference finetuning.
- **GUI / API**: interfaces for people (buttons, menus) / for programs.
- **Single-turn / multi-turn data**: one exchange / a conversation with several exchanges.
- **Data quality**: relevance, alignment with task needs, consistency, formatting, uniqueness and compliance.
- **PII**: personally identifiable information.
- **Coverage (diversity)**: how well data spans the situations the model will face.
- **Data mix**: the proportions of different kinds of data in a training set.
- **Ossification**: pre-trained weights becoming resistant to adaptation by finetuning.
- **Learning curve**: performance plotted against the amount of training data.
- **Data flywheel**: user data improving the product, which brings more users and more data.
- **License**: the legal terms for using a dataset or model.
- **Synthetic data**: data generated by AI rather than collected from people.

```quiz
[
  {"q": "Data-centric AI means…", "options": ["Designing new architectures", "Improving performance by improving the data rather than the model", "Using only synthetic data", "Avoiding evaluation"], "answer": 1, "explain": "Given a model, build the best dataset. This complements model-centric work."},
  {"q": "What did the LIMA paper show?", "options": ["More data always wins", "A 65B model finetuned on only 1,000 carefully curated examples can be competitive with far stronger models in many cases", "Synthetic data fails", "Finetuning needs millions of examples"], "answer": 1, "explain": "A small amount of high-quality data can go a long way, though the result was less robust than production models."},
  {"q": "Why does Huyen say data should be 'aligned with task requirements' rather than 'accurate'?", "options": ["Accuracy is impossible", "Depending on the task, a correct response may not be what's wanted (e.g., it must be creative, concise or justified)", "Alignment is cheaper", "Accuracy only applies to images"], "answer": 1, "explain": "Annotations should reflect what the task actually requires."},
  {"q": "In Llama 3's data mix, math/reasoning and code together made up roughly what share of pre-training data?", "options": ["5%", "15%", "40%", "90%"], "answer": 2, "explain": "25% maths and reasoning plus 17% code: far above their share of the internet, because they build reasoning."},
  {"q": "You have 300 labelled examples. Which approach generally fits best?", "options": ["Full finetuning of a small model", "PEFT (e.g., LoRA) on a stronger base model", "Train from scratch", "No evaluation needed"], "answer": 1, "explain": "Little data → PEFT on advanced models. Lots of data → full finetuning on smaller models."},
  {"q": "Finetuning on 50 well-crafted examples shows no improvement. What should you conclude first?", "options": ["Buy 1M examples", "Check other causes (hyperparameters, data quality, prompts); more data rarely fixes zero improvement", "Finetuning never works", "Switch to pre-training"], "answer": 1, "explain": "In most cases 50-100 examples should show gains. If not, look for other problems before scaling data."},
  {"q": "Why plot performance at 25%, 50% and 100% of your data?", "options": ["To reduce training time", "To see the slope and estimate whether more data will pay off", "To detect contamination", "To pick the tokenizer"], "answer": 1, "explain": "A steep curve suggests more data helps, and a plateau suggests diminishing returns."},
  {"q": "What is the data flywheel?", "options": ["A vector database", "Using data from users to improve the product, which attracts more users and more data", "A deduplication algorithm", "A GPU scheduler"], "answer": 1, "explain": "Application data is the most relevant source and compounds over time."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 8 ("Data Curation": data quality, data coverage, data quantity, data acquisition and annotation).
