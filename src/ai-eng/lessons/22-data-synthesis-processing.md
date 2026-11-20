# Data synthesis, distillation and processing

High-quality data is expensive and slow to get by hand. This lesson covers the two remaining parts of dataset engineering. First, **generating data programmatically**: augmentation, rule-based and AI-powered synthesis, verification, limitations and model distillation. Second, **processing data** so it is ready for training: inspecting, deduplicating, cleaning, filtering and formatting.

## 1. Augmentation vs synthesis

- **Data augmentation** creates new data from existing *real* data. A flipped photo of a cat is still a cat.
- **Data synthesis** generates data that mimics the properties of real data. Simulating mouse movements to build a bot-detection dataset is an example.

The line is blurry, and Huyen often uses "synthesis" for both. Synthetic data rarely replaces human-generated data altogether. Usually it is mixed in.

### Why synthesize?

- **Quantity.** Produce data at scale, especially where real data is scarce: rare weather, deep-sea exploration, self-driving accidents.
- **Coverage.** Generate data with targeted characteristics: very short or very long texts, toxic phrases for a toxicity detector, adversarial examples, rare classes for class imbalance. TrueTeacher used LLMs to generate factually *inconsistent* summaries to train an inconsistency detector. Anthropic generated datasets testing 154 behaviours and found that model-written datasets approached, and sometimes exceeded, human-written quality.
- **Quality.** Sometimes AI data is *better*. Tool-use data is one case, since humans and AI work differently. Complex math problems are another. Preference ratings are a third, because AI ratings can be more consistent than ratings from different people.
- **Privacy.** Use synthetic records where real ones are sensitive. Synthetic patient records and insurance claims let you build and test models without exposing personal information.
- **Distillation.** Train a model to imitate another (section 5).

## 2. Traditional (rule-based and simulation) techniques

### Rule-based synthesis

- **Templates** filled by random generators such as Faker. A credit-card transaction template has fields for ID, date, amount, merchant, location and status. Fraud models are often first trained on such synthetic transactions to prove feasibility before real data is made available. Templates suit structured documents (invoices, resumes, tax forms, contracts, config files) and anything with a grammar (regexes, math equations). DeepMind trained AlphaGeometry on **100 million** synthetic examples.
- **Procedural transformations.** For images: rotate, crop, scale, erase (this goes back to AlexNet). For text: replace a word with a similar one ("fantastic nurse" becomes "great nurse"), found through a synonym dictionary or nearby embeddings.
- **Bias mitigation.** Swap gendered words ("She's a fantastic nurse" becomes "He's a fantastic nurse") or names from different backgrounds.
- **Perturbation.** Add noise to create new examples. Adversarial research showed that slight perturbations can fool models. One study found that changing a single pixel flipped the predictions for 67.97% of natural images in CIFAR-10. Training on perturbed data makes models more **robust**. BERT's training used a version of this: 15% of tokens were selected, and of those 10% were replaced with random words.

```python-run
import random
random.seed(3)
templates = ["How do I {verb} my {obj}?", "I can't {verb} my {obj}, please help.", "Steps to {verb} {obj}?"]
verbs, objs = ["reset", "change", "recover"], ["password", "email address", "2FA device"]
swap = {"she": "he", "her": "his", "mom": "dad", "Ms.": "Mr."}
print("Template synthesis:")
for _ in range(4):
    print("  ", random.choice(templates).format(verb=random.choice(verbs), obj=random.choice(objs)))
s = "Today her mom said she is a fantastic nurse"
print("Counterfactual augmentation:\n  ", s, "\n  ", " ".join(swap.get(w, w) for w in s.split()))
def typo(text, rate=0.08):
    return "".join(c if random.random() > rate or not c.isalpha() else random.choice("abcdefghijklmnopqrstuvwxyz") for c in text)
print("Perturbation (typos):\n  ", typo("How do I reset my password?"))
```

### Simulation

Instead of running costly or dangerous real experiments, simulate them. Self-driving companies generate rare scenarios in virtual environments (CARLA, Waymo's SimulationCity, Tesla's simulator). Robotics simulates joint movements and keeps the successful ones. Simulation is also good for **tool-use data**: simulate different action sequences for a query, execute them, check the results, and keep the most efficient sequence as the label. It suits rare events too: IPOs or bankruptcies in finance, manufacturing defects, extreme climate scenarios.

## 3. AI-powered data synthesis

- **Simulating programs and people.** A model can simulate API responses without calling the APIs (StableToolBench). **Self-play** has AIs play against each other. OpenAI's Dota 2 bot played about 180 years' worth of games per day, and AlphaGo used millions of self-play games. The same idea works for negotiation, or for customer and support-agent roleplay.
- **Paraphrasing and translation.** "How to reset my password?" becomes "I forgot my password", "How can I change my password?" and so on. Translation augments low-resource languages and programming languages alike. **Back-translation** translates to another language and back, and keeps the example only if the round trip preserves it. This serves as both augmentation and verification.
- **Pre-training data.** Even pre-training corpora can be synthesized. Models have been trained on AI-generated short stories and synthetic textbooks.

### Instruction data synthesis

For instruction finetuning you can synthesize instructions, responses, or both.

- **Generate instructions** from a list of topics, keywords or instruction types, or from templates. **UltraChat** asked ChatGPT for 30 topics, then 30–50 subtopics each, then instructions and responses.
- **Seed and expand.** **Alpaca** started from 175 human-written (instruction, response) seeds from Self-Instruct and used text-davinci-003 to generate **52,000** pairs.
- **Reverse instruction.** Long, high-quality responses are hard for AI to write without hallucinating. Take existing high-quality human content such as books or Wikipedia and have AI write the *prompt* that would elicit it. The responses stay human quality. Repeating this lets a weak model bootstrap better instruction data and improve.
- **Long-context finetuning data.** Split long documents into short chunks, generate (question, answer) pairs per chunk, then pair each QA with the **whole long document** as context, so the model learns to use extended context.

**Llama 3's coding data** is a good case study:

1. Generate a large, diverse set of programming problem descriptions.
2. For each description and programming language, generate a solution. General rules of good programming and CoT reasoning improved quality.
3. Verify. Run the code through parsers and linters to catch syntax errors, uninitialized variables and type errors. Generate unit tests and execute them.
4. When a solution fails, feed the error back and ask the model to revise. Only examples that pass every check are kept. About 20% of solutions were initially wrong and then self-corrected.

They also used **code translation** (into less common languages) and **code back-translation**: generate explanations or documentation, regenerate code from them, and keep the example if the regenerated code is faithful. The pipeline produced more than 2.7 million synthetic coding examples.

### Data verification

People tend to synthesize data they can verify, which is one reason coding data is so commonly synthesized.

- **Functional correctness** where possible: execution, unit tests, back-translation.
- **AI verifiers**: a general AI judge or a specialized scorer rates each example 1–5 or good/bad, or checks stated quality requirements. Use the factual-consistency techniques from Module 4 to filter hallucinated examples.
- **Creative checks.** If synthetic data should resemble real data, train a detector. If telling them apart is easy, the synthetic data is not good.
- **Heuristics.** Filter examples by keywords, user or author, creation date, metadata or source. Remove empty or too-short examples, instructions that appear with many different responses and vice versa, and outputs that merely repeat the input. Anomaly detection can flag outliers.

Verifying synthetic data is as hard as evaluating any AI output, and it needs the same combination of methods.

## 4. Limitations of AI-generated data

1. **Quality control.** Garbage in, garbage out. Without reliable verification, people will not trust synthetic data.
2. **Superficial imitation.** "The False Promise of Imitating Proprietary LLMs" (Gudibande et al., 2023) found that imitation models copy the teacher's **style** but struggle with factual accuracy and generalization. Imitation can also force hallucination. A student trained on a teacher's correct math solutions learns to produce answers that *look like* solutions even when it cannot solve the problem.
3. **Potential model collapse.** Training recursively on AI-generated data can cause irreversible defects ("The Curse of Recursion", Shumailov et al., 2023). Probable events get over-represented and rare events are forgotten. "Is Model Collapse Inevitable?" (Gerstgrasser et al., 2024) argues that collapse is inevitable if *all* training data is synthetic but avoidable by **mixing synthetic with real data**. Nobody has a definitive ratio. Some studies report large gains from mostly synthetic data. The same mechanism can also amplify biases over iterations.
4. **Obscure data lineage.** If model X was trained on copyrighted or contaminated data and you train on X's outputs, your model inherits the problem invisibly. If X saw benchmark B, your model's score on B is contaminated too.

```python-run
import numpy as np
# Toy model collapse: each generation is trained only on samples from the previous one.
# Rare events (the tails) vanish; mixing in real data slows the loss of diversity.
rng = np.random.default_rng(0)
real = rng.normal(0, 1, 20000)
def generation(prev, mix_real=0.0, n=20):
    k = int(n * mix_real)
    train = np.concatenate([rng.choice(prev, n - k), rng.choice(real, k)])
    return rng.normal(train.mean(), train.std(), 2000)       # "model" = fitted Gaussian, then sampled
for mix in [0.0, 0.5]:
    data = real
    for g in range(200): data = generation(data, mix)
    print(f"real-data mix {mix:.0%}: std after 200 generations = {data.std():.3f} (original 1.0), share beyond |x|>2: {np.mean(np.abs(data) > 2):.2%}")
```

## 5. Model distillation

**Model distillation** (knowledge distillation, Hinton et al., 2015) trains a small **student** to mimic a larger **teacher**.

- Traditionally the goal is a smaller, faster model for deployment. **DistilBERT** is 40% smaller than BERT, keeps 97% of its language understanding, and runs 60% faster.
- The student can be trained from scratch (DistilBERT) or finetuned from a pre-trained model. **Alpaca** finetuned Llama-7B on examples generated by the 175B text-davinci-003 and behaved similarly at 4% of the teacher's size.
- Synthetic instruction data is often combined with adapters. BuzzFeed finetuned Flan-T5 with LoRA on OpenAI-generated examples and reported cutting inference cost by 80%.

> [!WARNING]
> Not all models can be distilled. Many licenses **prohibit using a model's outputs to train other models**, especially competing ones. Check before you build a pipeline on it.

Not all training on synthetic data is distillation. Distillation implies that the teacher is the gold standard. A student can end up *stronger* than the model that generated its data. Reverse-instruction bootstrapping is one case. NVIDIA's **Nemotron-4 340B**, finetuned on data generated by Mixtral-8x7B, outperformed its "teacher" on several tasks.

## 6. Data processing

The right order of processing steps can save a lot of time. Huyen's tips: if cleaning each example is slow, **deduplicate first**. If deduplication is the expensive part, filter out low-quality data first. Do **trial runs** on a sample before processing everything. **Avoid changing data in place**, and keep the original, because you or another team may need it processed differently, and bugs happen.

### Inspect data

Get statistics. Where does the data come from, and how has it been processed? Plot distributions of tokens, input and response lengths, topics and languages. Microsoft researchers compared GPT-3 and GPT-4 generations using the distribution of (verb, direct-object noun) pairs and response lengths. Plot by source, time and annotator, and look for outliers. Do some annotators give much shorter responses or consistently higher scores? Where examples have several annotations, compute **inter-annotator disagreement** and resolve conflicts. If the same query has different responses, find out why.

**Manually inspect your data.** Huyen emphasizes this more than any tool. OpenAI co-founder Greg Brockman has made the same point: manual inspection of data probably has the highest value-to-prestige ratio of any activity in machine learning. Fifteen minutes of looking at data can save hours.

### Deduplicate data

Duplicates skew the distribution and bias the model. In Huyen's toy pricing table, repeated "red pencil → \$20" rows could teach the model that red items are expensive. Duplicates can also contaminate test sets, when an example lands in train and its duplicate in test. An Anthropic study found that repeating just **0.1% of the data 100 times** degraded an 800M-parameter model to the level of a 400M one, even though 90% of the training tokens remained unique.

Duplication takes several forms: whole-document, intra-document (a repeated paragraph) and cross-document (a popular quote). You define what counts: the level (document, paragraph, sentence), exact match versus, say, 80% overlap, and whether order matters.

Techniques, which are the same ones used for similarity measurement:

- **Pairwise comparison** with exact, n-gram, fuzzy or semantic similarity. This is expensive for large datasets.
- **Hashing.** Hash examples into buckets and compare only within a bucket: **MinHash**, **Bloom filters**.
- **Dimensionality reduction** followed by pairwise comparison, using vector-search techniques.

Libraries include dupeGuru, Dedupe, datasketch, TextDistance, TheFuzz and deduplicate-text-datasets.

```python-run
import re, zlib
def shingles(t, n=2):
    w = re.findall(r"[a-z0-9]+", t.lower()); return {" ".join(w[i:i+n]) for i in range(max(1, len(w)-n+1))}
def minhash(sh, k=64):       # k hash functions simulated by salting; the signature is each one's minimum
    return [min(zlib.crc32(f"{i}|{s}".encode()) for s in sh) for i in range(k)]
docs = ["The quick brown fox jumps over the lazy dog near the river bank",
        "the quick brown fox jumps over the lazy dog near the river bank!!",
        "The quick brown fox leaps over the lazy dog near the river bank",
        "Completely different sentence about quantization of neural networks"]
sig = [minhash(shingles(d)) for d in docs]
for i in range(len(docs)):
    for j in range(i+1, len(docs)):
        a, b = shingles(docs[i]), shingles(docs[j])
        est = sum(x == y for x, y in zip(sig[i], sig[j])) / 64
        print(f"docs {i},{j}: true Jaccard {len(a&b)/len(a|b):.2f}   MinHash estimate {est:.2f}")
```

MinHash signatures are short and their agreement rate estimates Jaccard similarity, so near-duplicates can be found without comparing full texts.

### Clean and filter data

- **Remove extraneous formatting.** Databricks found that removing extra Markdown and HTML tokens improved accuracy by **20%** and cut input length by **60%**.
- **Remove non-compliant data**: PII, sensitive, copyrighted or toxic content, and fields you may not use (zip code, name, gender).
- **Remove low-quality data** using the verification techniques above. Manual inspection reveals non-obvious heuristics. Kern et al. (2024) found that annotations made in the **second half of an annotation session** are lower quality, probably from fatigue.
- **Filter down** if you have more data than you can afford to use. **Active learning** selects the most helpful examples, and **importance sampling** selects those most important to the task. Good data-pruning metrics can cut training cost substantially (Sorscher et al., 2022).

### Format data

Put the data into the format the model expects: the right **tokenizer** and **chat template**. Wrong templates cause strange bugs (Module 5).

For supervised finetuning, the data is (instruction, response), with instructions optionally split into (system prompt, user prompt). Moving from prompt engineering to finetuning changes the instructions. Finetuning instructions usually do **not need task descriptions or examples**, because the model learns the task from the training data. A 3-shot prompt such as "Label the following item as edible or inedible. Item: burger Label: edible …" becomes plain training pairs, such as prompt `burger -->` and completion `edible`. The **prompts you use at inference must then match the finetuning format** exactly. If you trained on `burger -->`, do not prompt with `burger` or `Item: burger -->`.

> [!INTERVIEW]
> **"What are the risks of training on LLM-generated data, and how do you mitigate them?"** Quality (verify with execution, back-translation, AI judges and heuristics). Superficial imitation and inherited hallucination (keep human-quality responses through reverse instruction, and evaluate reasoning, not style). Model collapse and loss of rare cases (mix in real data and track diversity). Obscure lineage, licensing and benchmark contamination (check the teacher's license and data lineage, and hold out private evaluation sets). Add deduplication, a compliance filter and manual inspection of samples.

## Summary

- **Synthesis** increases quantity, coverage and sometimes quality, mitigates privacy concerns and enables distillation. Techniques: templates and rules, transformations and perturbation, simulation, and AI-powered generation (self-play, paraphrase, translation and back-translation, instruction synthesis, reverse instruction).
- **Verify** synthetic data with functional checks, AI verifiers and heuristics. Llama 3's coding pipeline is a model example.
- **Limits**: quality control, superficial imitation, potential model collapse (mix in real data) and obscure lineage.
- **Distillation** trains a student to mimic a teacher (DistilBERT, Alpaca). Check licenses. Not all synthetic-data training is distillation.
- **Processing**: inspect (manually too), deduplicate (pairwise, hashing or MinHash, dimensionality reduction), clean and filter (formatting, compliance, quality, active learning), and format for the model's chat template. Keep the original data.

```quiz
[
  {"q": "What is 'reverse instruction' synthesis?", "options": ["Generating responses for human prompts", "Taking existing high-quality content and having AI generate the prompts that would elicit it", "Translating instructions backwards", "Deleting instructions"], "answer": 1, "explain": "Responses stay human quality, which avoids AI hallucinations in long answers."},
  {"q": "Why is coding data among the most commonly synthesized?", "options": ["Code is short", "It can be verified programmatically (execution, tests, back-translation)", "It has no licenses", "Models can't hallucinate code"], "answer": 1, "explain": "People synthesize what they can verify. Llama 3's synthetic data was mostly verifiable code."},
  {"q": "Model collapse refers to…", "options": ["Running out of GPU memory", "Degradation from recursively training on AI-generated data, where rare events are forgotten", "A model refusing to answer", "Quantization error"], "answer": 1, "explain": "Probable events get over-represented across generations. Mixing in real data mitigates it."},
  {"q": "What did 'The False Promise of Imitating Proprietary LLMs' find?", "options": ["Imitation models match teachers in everything", "Imitation models mimic style well but struggle with factual accuracy and generalization", "Distillation is illegal", "Students are always larger"], "answer": 1, "explain": "Superficial imitation: the student sounds like the teacher without having its capabilities."},
  {"q": "DistilBERT compared with BERT is…", "options": ["40% smaller, retains 97% of language comprehension, 60% faster", "Twice as large", "Less accurate by 50%", "Trained with RLHF"], "answer": 0, "explain": "These are the figures from Sanh et al. (2019) cited in the book."},
  {"q": "An Anthropic study found that repeating 0.1% of data 100 times…", "options": ["Improved the model", "Degraded an 800M-parameter model to roughly 400M-level performance", "Had no effect", "Doubled training speed"], "answer": 1, "explain": "Duplicates can be surprisingly harmful, which is why deduplication matters."},
  {"q": "When should you deduplicate before cleaning?", "options": ["Never", "When cleaning each example is expensive, so duplicates aren't cleaned needlessly", "Only for images", "Only after formatting"], "answer": 1, "explain": "Order processing steps to minimise wasted work."},
  {"q": "You finetuned on prompts formatted as 'burger -->'. At inference you should prompt with…", "options": ["'Item: burger -->'", "'burger'", "'burger -->' (the same format as in finetuning)", "A long task description"], "answer": 2, "explain": "Inference prompts must match the finetuning format, or performance drops."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 8 ("Data Augmentation and Synthesis", "Model Distillation", "Data Processing").
