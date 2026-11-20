TRACK = dict(
    id="ai-eng",
    title="AI Engineering (Chip Huyen)",
    icon="🤖",
    color="#7b5cff",
    group="AI Engineering",
    blurb="Build real applications on top of foundation models: how they work, how to evaluate them, "
          "prompting, RAG and agents, finetuning, data, inference optimization and production architecture.",
    sources=[
        "Chip Huyen, AI Engineering: Building Applications with Foundation Models (O'Reilly, 2025), ch. 1-10",
    ],
    modules=[
        dict(
            id="intro",
            title="1. Building AI Applications with Foundation Models",
            summary="Where foundation models came from, what people build with them, how to plan a product, and the AI engineering stack.",
            lessons=[
                dict(id="aie-rise", title="From language models to foundation models", file="01-rise-of-foundation-models.md"),
                dict(id="aie-planning-stack", title="Planning AI applications and the AI engineering stack", file="02-planning-and-stack.md"),
            ],
            problems=[],
        ),
        dict(
            id="foundation-models",
            title="2. Understanding Foundation Models",
            summary="Training data, the transformer, scale and scaling laws, post-training (SFT, RLHF, DPO) and sampling.",
            lessons=[
                dict(id="aie-data-arch-scale", title="Training data, architecture and scale", file="03-data-architecture-scale.md"),
                dict(id="aie-post-training", title="Post-training: SFT and preference finetuning", file="04-post-training.md"),
                dict(id="aie-sampling", title="Sampling, structured outputs and the probabilistic nature of AI", file="05-sampling.md"),
            ],
            problems=["aie-softmax-temperature", "aie-top-k-top-p", "aie-beam-search"],
        ),
        dict(
            id="eval-methodology",
            title="3. Evaluation Methodology",
            summary="Entropy, cross entropy and perplexity; exact and similarity-based evaluation; AI as a judge; comparative evaluation.",
            lessons=[
                dict(id="aie-lm-metrics", title="Language modeling metrics: entropy to perplexity", file="06-language-modeling-metrics.md"),
                dict(id="aie-exact-similarity", title="Exact evaluation and similarity measures", file="07-exact-and-similarity.md"),
                dict(id="aie-judge-comparative", title="AI as a judge and comparative evaluation", file="08-ai-judge-comparative.md"),
            ],
            problems=["aie-perplexity", "aie-rouge-l", "aie-elo-ratings", "aie-judge-position-bias"],
        ),
        dict(
            id="eval-systems",
            title="4. Evaluating AI Systems",
            summary="Evaluation criteria, model selection, build vs buy, public benchmarks and contamination, and your own eval pipeline.",
            lessons=[
                dict(id="aie-eval-criteria", title="Evaluation criteria", file="09-evaluation-criteria.md"),
                dict(id="aie-model-selection", title="Model selection, build vs buy and public benchmarks", file="10-model-selection.md"),
                dict(id="aie-eval-pipeline", title="Designing your evaluation pipeline", file="11-eval-pipeline.md"),
            ],
            problems=["aie-qa-exact-f1"],
        ),
        dict(
            id="prompt-engineering",
            title="5. Prompt Engineering",
            summary="In-context learning, system prompts, best practices, chain-of-thought, decomposition and defensive prompt engineering.",
            lessons=[
                dict(id="aie-prompt-intro", title="Prompts, in-context learning and context length", file="12-prompting-basics.md"),
                dict(id="aie-prompt-practices", title="Prompt engineering best practices", file="13-prompt-best-practices.md"),
                dict(id="aie-prompt-defense", title="Defensive prompt engineering", file="14-defensive-prompting.md"),
            ],
            problems=["aie-prompt-template", "aie-injection-detector"],
        ),
        dict(
            id="rag-agents",
            title="6. RAG and Agents",
            summary="Retrieval algorithms, hybrid search, chunking, reranking, query rewriting, contextual retrieval, agents, planning and memory.",
            lessons=[
                dict(id="aie-rag-retrieval", title="RAG architecture and retrieval algorithms", file="15-rag-retrieval.md"),
                dict(id="aie-retrieval-opt", title="Retrieval optimization", file="16-retrieval-optimization.md"),
                dict(id="aie-agents", title="Agents: tools, planning, failure modes and memory", file="17-agents-memory.md"),
            ],
            problems=["aie-cosine-topk", "aie-bm25", "aie-text-splitter", "aie-rrf", "aie-mmr", "aie-react-executor"],
        ),
        dict(
            id="finetuning",
            title="7. Finetuning",
            summary="When to finetune, memory math, numerical formats and quantization, PEFT/LoRA/QLoRA, model merging and hyperparameters.",
            lessons=[
                dict(id="aie-when-finetune", title="When (and when not) to finetune", file="18-when-to-finetune.md"),
                dict(id="aie-memory-quant", title="Memory math, numerical formats and quantization", file="19-memory-math-quantization.md"),
                dict(id="aie-peft-lora", title="PEFT, LoRA, model merging and hyperparameters", file="20-peft-lora-merging.md"),
            ],
            problems=["aie-model-memory", "aie-lora-params", "aie-int8-quant"],
        ),
        dict(
            id="dataset-engineering",
            title="8. Dataset Engineering",
            summary="Curating data for quality, coverage and quantity; synthesis and distillation; inspecting, deduplicating, filtering and formatting.",
            lessons=[
                dict(id="aie-data-curation", title="Data curation: quality, coverage, quantity", file="21-data-curation.md"),
                dict(id="aie-data-synthesis", title="Data synthesis, distillation and processing", file="22-data-synthesis-processing.md"),
            ],
            problems=["aie-near-dedup"],
        ),
        dict(
            id="inference-opt",
            title="9. Inference Optimization",
            summary="Bottlenecks and metrics (TTFT, TPOT, MFU, MBU), accelerators, model-level and service-level optimization.",
            lessons=[
                dict(id="aie-inference-metrics", title="Inference bottlenecks, metrics and hardware", file="23-inference-metrics-hardware.md"),
                dict(id="aie-model-opt", title="Model optimization: compression, speculative decoding, KV cache", file="24-model-optimization.md"),
                dict(id="aie-service-opt", title="Service optimization: batching, prompt caching, parallelism", file="25-service-optimization.md"),
            ],
            problems=["aie-kv-cache"],
        ),
        dict(
            id="architecture-feedback",
            title="10. AI Engineering Architecture and User Feedback",
            summary="Context, guardrails, routers, gateways, caching, observability, orchestration and collecting user feedback.",
            lessons=[
                dict(id="aie-architecture", title="Building up an AI application architecture", file="26-ai-architecture.md"),
                dict(id="aie-observability-feedback", title="Observability, orchestration and user feedback", file="27-observability-feedback.md"),
            ],
            problems=["aie-semantic-cache", "aie-token-bucket", "aie-cost-estimator"],
        ),
    ],
)
