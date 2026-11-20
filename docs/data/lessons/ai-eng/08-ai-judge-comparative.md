# AI as a judge and comparative evaluation

Most valuable outputs, such as a helpful answer, a faithful summary or a polite tone, cannot be checked with unit tests or exact match. Human evaluation is slow and expensive. The pragmatic answer that took over the industry is **AI as a judge**: use an AI model to evaluate another model's outputs. This lesson covers why it works, how to use it, its limitations and biases, specialized judges, and then **comparative evaluation**, ranking models by pairwise matches with rating systems like Elo.

## 1. Why AI as a judge?

AI judges are **fast, cheap and easy**, and they **do not need reference data**, so they work in production where no ground truth exists. You can ask them to judge almost anything: correctness, repetitiveness, toxicity, hallucination, wholesomeness. They can also **explain** their verdicts, which helps when auditing.

Their judgments correlate well with humans:

- Zheng et al. (2023): on MT-Bench, GPT-4 agreed with humans **85%** of the time, higher than human–human agreement (**81%**).
- AlpacaEval's AI judges had a near-perfect (**0.98**) correlation with LMSYS Chatbot Arena's human-based leaderboard.

## 2. How to use AI as a judge

Three common setups:

1. **Evaluate a response by itself**: "Given this question and answer, score how good the answer is from 1 to 5."
2. **Compare to a reference**: "Given the question, the reference answer and this answer, does this answer match the reference?" This is an alternative to the human-designed similarity metrics in the previous lesson.
3. **Compare two responses**: "Which of these two answers is better?" This is the basis of comparative evaluation and of preference data for post-training.

A judge prompt should specify:

- **The task**, for example evaluating the relevance between a question and an answer.
- **The criteria**, with explicit definitions. Vague criteria give vague scores.
- **The scoring system**: classification (good/bad, relevant/irrelevant), discrete numbers (1–5) or continuous numbers (0–1). Huyen notes that **language models are generally better with text than numbers**, and that classification or small discrete scales work better than wide numeric ranges. Score ranges that are too fine, such as 1–10, make judgments noisier.
- **Examples** of each score with justifications, which improves consistency.

```text
You are evaluating whether an ANSWER is faithful to a CONTEXT.
Faithful = every factual claim in the ANSWER can be inferred from the CONTEXT.
Return exactly one word: FAITHFUL or UNFAITHFUL, then one sentence of justification.

Example:
CONTEXT: The store opens at 9am on weekdays.
ANSWER: The store opens at 8am on Mondays.
VERDICT: UNFAITHFUL - the context says 9am.

CONTEXT: {{context}}
ANSWER: {{answer}}
VERDICT:
```

Many tools ship built-in judge criteria. Huyen lists Azure AI Studio (groundedness, relevance, coherence, fluency, similarity), MLflow (faithfulness, relevance), LangChain criteria (conciseness, relevance, correctness, coherence, harmfulness, maliciousness, helpfulness, controversiality, misogyny, insensitivity, criminality) and Ragas (faithfulness, answer relevance).

## 3. Limitations

### Inconsistency

Judges are probabilistic. The same judge on the same input can give different scores, and a small prompt change can swing results. Zheng et al. raised GPT-4's consistency from **65% to 77.5%** by adding examples to the prompt, but consistency is not accuracy (a judge can be consistently wrong), and the extra examples **quadrupled** their GPT-4 spending.

### Criteria ambiguity

AI judge metrics are not standardized. MLflow, Ragas and LlamaIndex all have a "faithfulness" criterion, scored 1–5, 0/1 and YES/NO respectively, with different prompts. Their scores are not comparable. Worse, **a judge is itself an application that evolves**. If someone changes the judge's model or prompt, your metric changes even though your application did not. Huyen's rule: **treat the judge (model + prompt + sampling settings) as part of the metric and version it.** Do not trust a judge score unless you know exactly which model and prompt produced it.

### Cost and latency

Using GPT-4 to judge each GPT-4 response can triple the number of API calls if you check several criteria. Mitigations: use weaker or specialized judges, judge only a **sample** of traffic (spot-checking), or run judges asynchronously off the request path. Judging in the request path as a guardrail adds latency.

### Biases

- **Self-bias.** Models favor their own outputs. In Zheng et al., GPT-4 favored itself with a 10% higher win rate, and Claude-v1 with 25%.
- **First-position bias.** Many AI judges favor the first answer in a pair or list. This is the **opposite of humans**, who show **recency bias** and favor the last answer seen. Mitigate by running both orders and checking consistency.
- **Verbosity bias.** Judges favor longer answers. Wu and Aji (2023) found GPT-4 and Claude-1 preferred about 100-word answers containing factual errors over about 50-word correct ones. Saito et al. found that when one answer is about twice as long, the judge almost always prefers it. GPT-4 is less prone to this than GPT-3.5, which suggests the bias may fade as models improve.
- **Privacy and IP.** Proprietary judges see your data, and their training data provenance is unknown.

```python-run
# Position-bias check: ask the judge about (A,B) and (B,A). A consistent judge flips its label.
# Here we simulate a biased judge that prefers position 1 with probability 0.3 regardless of quality.
import random
random.seed(1)
def judge(first_quality, second_quality, bias=0.3):
    if random.random() < bias: return "first"
    return "first" if first_quality >= second_quality else "second"
pairs = [(random.random(), random.random()) for _ in range(1000)]
consistent = 0
for qa, qb in pairs:
    v1 = judge(qa, qb)            # A shown first
    v2 = judge(qb, qa)            # B shown first
    winner1 = "A" if v1 == "first" else "B"
    winner2 = "B" if v2 == "first" else "A"
    consistent += (winner1 == winner2)
print(f"swap-consistency: {consistent/len(pairs):.1%}  (a bias-free judge would score 100%)")
```

## 4. Which model should judge?

- **A stronger judge** is intuitive, like an examiner who knows more than the student. It is useful when you generate with a cheap model and evaluate a sample (say 1%) with a stronger one, or evaluate in the background and replace bad responses. Problems: the strongest model has no stronger judge, and you need some other way to know which model is strongest.
- **Self-evaluation (self-critique).** It sounds like cheating because of self-bias, but it is useful as a sanity check and nudges models to revise. Huyen's example: asked "What's 10+3?", a model answers 30, then is asked to check itself and corrects to 13.
- **A weaker judge.** Judging may be easier than generating (anyone can tell whether a song is good, but few can write one). Zheng et al. found stronger judges correlate better with humans, so people often pick the strongest judge they can afford.

### Specialized judges

Small, finetuned judges can be cheaper and more consistent than general models:

- **Reward models** score a (prompt, response) pair, as in RLHF. Google's Cappy (360M parameters) scores how correct a response is.
- **Reference-based judges** score against references. BLEURT outputs a similarity score, and Prometheus scores against a reference and a rubric.
- **Preference models** take (prompt, response 1, response 2) and output which is better. PandaLM and JudgeLM also explain their reasoning.

> [!INTERVIEW]
> **"How would you make an LLM-as-judge evaluation trustworthy?"** Version the judge (model, prompt, sampling) as part of the metric. Use clear criteria with rubric examples and small discrete or classification outputs. Set temperature to 0. Calibrate against a human-labeled set and report agreement. Mitigate position bias by swapping order and counting only swap-consistent verdicts, and control for length. Avoid using a model to judge its own family. Combine with exact metrics where possible, and spot-check with humans.

## 5. Comparative evaluation

Often you do not care about a model's absolute score. You want to know **which model is best for you**. You can rank by **pointwise** evaluation (score each model independently) or by **comparative** evaluation (compare models against each other). For subjective quality, comparison is easier. Picking the better of two songs is easier than scoring a song.

Anthropic first used comparative evaluation for AI models in 2021. LMSYS **Chatbot Arena** made it famous: users enter a prompt, two anonymous models respond, and the user votes. Each comparison is a **match**, and the probability that A beats B is A's **win rate** over B.

Comparative evaluation is **not A/B testing**. In A/B tests a user sees one variant. In comparative evaluation a user sees several side by side.

> [!WARNING]
> Not every question should be settled by preference. "Is there a link between cell phone radiation and brain tumors?" should be settled by correctness, not votes. Preference voting only works when voters know the subject, for example when AI acts as an assistant for tasks users already understand.

### From matches to ratings: Elo and Bradley–Terry

Ratings are computed from match outcomes, then models are ranked by rating. Algorithms borrowed from games and sports include **Elo**, **Bradley–Terry** and **TrueSkill**. Chatbot Arena started with Elo and later switched to Bradley–Terry, which is less sensitive to the order of matches.

Elo models the expected score of A against B as:

$$
E_A = \frac{1}{1 + 10^{(R_B - R_A)/400}}
$$

and after a match with actual score $S_A$ (1 for a win, 0.5 for a tie, 0 for a loss) it updates:

$$
R_A' = R_A + K\,(S_A - E_A), \qquad R_B' = R_B + K\,\big((1-S_A) - (1-E_A)\big)
$$

$K$ controls how fast ratings move. A 400-point gap means the stronger side is expected to win about 10:1. An upset (low expected score, actual win) moves ratings a lot, and an expected win moves them a little.

```python-run
def expected(ra, rb): return 1 / (1 + 10 ** ((rb - ra) / 400))
def elo(ratings, matches, k=32):
    r = dict(ratings)
    for a, b, s in matches:                # s = 1 (a wins), 0.5 tie, 0 (b wins)
        ea = expected(r[a], r[b])
        r[a] += k * (s - ea)
        r[b] += k * ((1 - s) - (1 - ea))
    return r
start = {"model-1": 1000, "model-2": 1000, "model-3": 1000}
matches = [("model-1","model-2",1), ("model-2","model-3",1), ("model-1","model-3",1),
           ("model-3","model-1",0.5), ("model-2","model-1",1)]
for m, v in sorted(elo(start, matches).items(), key=lambda x: -x[1]):
    print(f"{m}: {v:.1f}")
print("P(1400 beats 1000) =", round(expected(1400, 1000), 3))
```

Bradley–Terry fits all ratings jointly so that $P(A \succ B) = \sigma(s_A - s_B)$ (in log-odds) best explains every observed match. It is the same model as the RLHF reward loss in Module 2. Because it fits all matches at once, the result does not depend on match order, unlike Elo's sequential updates.

### Challenges of comparative evaluation

- **Scalability.** The number of pairs grows quadratically. In January 2024 LMSYS had 244,000 comparisons over 57 models, which is 1,596 pairs, or only about 153 comparisons per pair. Algorithms assume **transitivity** (A > B and B > C imply A > C), but human preference may not be transitive. Each new model also has to be matched against existing ones, which can reshuffle the ranking. Smarter matchmaking samples the pairs that reduce uncertainty most.
- **Standardization and quality control.** Crowdsourced voters use arbitrary prompts, rarely fact-check, may prefer unfiltered answers your product would refuse, and some vote maliciously. Many Arena prompts are simple ("hello"), so they do not separate strong models. Huyen notes that a large share of Arena prompts are trivial.
- **From comparative to absolute.** Knowing B beats A 51% of the time does not tell you whether B is *good enough*, or whether the gain is worth B's cost.

Despite these challenges, comparative evaluation captures what users care about, is hard to game, and avoids the saturation of static benchmarks. Huyen expects it to grow, especially combined with other methods.

## Summary

- **AI judges** are fast, flexible, reference-free and well correlated with humans (GPT-4 at 85% agreement on MT-Bench). Specify the task, the criteria, a small discrete or classification scoring system and examples.
- Limitations: **inconsistency**, **criteria ambiguity** (version your judge), **cost and latency**, and **biases** (self, first-position, verbosity).
- Judges can be stronger, weaker or the same model. **Specialized judges** include reward models, reference-based judges and preference models.
- **Comparative evaluation** ranks models from pairwise matches using Elo, Bradley–Terry or TrueSkill. Watch for quadratic scaling, non-transitivity, crowd quality and the gap between relative and absolute quality.

```quiz
[
  {"q": "On MT-Bench, how did GPT-4-human agreement compare with human-human agreement (Zheng et al., 2023)?", "options": ["65% vs 90%", "85% vs 81%", "50% vs 50%", "99% vs 70%"], "answer": 1, "explain": "GPT-4 agreed with humans 85% of the time, slightly above the 81% agreement among humans."},
  {"q": "MLflow, Ragas and LlamaIndex each give a 'faithfulness' score for the same output. What's the main problem?", "options": ["They are all identical", "Different prompts and scales (1-5, 0/1, YES/NO) make the scores incomparable", "None support RAG", "They require references"], "answer": 1, "explain": "AI-judge metrics aren't standardized. The judge's model and prompt define the metric."},
  {"q": "AI judges' position bias typically favors…", "options": ["The last answer (recency), like humans", "The first answer, the opposite of humans", "The shorter answer", "Neither"], "answer": 1, "explain": "Many AI judges show first-position bias, while humans tend to show recency bias."},
  {"q": "A cheap, robust mitigation for position bias in pairwise judging is…", "options": ["Increase temperature", "Evaluate both orderings and keep only consistent verdicts (or average)", "Use longer answers", "Remove the system prompt"], "answer": 1, "explain": "Swapping order exposes position effects, and agreement across both orders signals a real preference."},
  {"q": "Two models have Elo ratings 1500 and 1100. The expected score of the 1500 model is about…", "options": ["0.50", "0.76", "0.91", "0.99"], "answer": 2, "explain": "A 400-point gap gives E = 1/(1+10^-1) ≈ 0.909."},
  {"q": "Why did Chatbot Arena move from Elo to Bradley-Terry?", "options": ["Bradley-Terry is faster to compute on GPUs", "Elo's sequential updates make results depend on match order; Bradley-Terry fits all matches jointly", "Elo can't handle ties", "Bradley-Terry needs no data"], "answer": 1, "explain": "Bradley-Terry estimates ratings from all comparisons at once, so the result is order-independent."},
  {"q": "Which question should NOT be resolved by preference voting?", "options": ["Which of two poems is more fun?", "Is there a link between cell phone radiation and brain tumors?", "Which email draft sounds friendlier?", "Which logo do you like?"], "answer": 1, "explain": "Factual questions should be decided by correctness, not popularity."},
  {"q": "Comparative evaluation differs from A/B testing because…", "options": ["A/B tests show users multiple outputs at once", "In comparative evaluation users see outputs from multiple models side by side", "Comparative evaluation never uses humans", "They are the same"], "answer": 1, "explain": "A/B testing shows one variant per user, while comparative evaluation shows candidates side by side."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 3 ("AI as a Judge", "Ranking Models with Comparative Evaluation").
