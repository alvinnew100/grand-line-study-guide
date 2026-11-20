TRACK = dict(
    id="llm-practice",
    title="LLMs Hands-On: Transformers, Hugging Face, RAG, MCP & Context Engineering",
    icon="🔮",
    color="#7b5cff",
    group="AI Engineering",
    blurb=(
        "The hands-on and internals companion to the AI Engineering track: build attention and BPE in numpy, "
        "drive the Hugging Face stack, ship RAG and LoRA fine-tunes, write MCP servers, and engineer "
        "context for long-running agents."
    ),
    sources=[
        "Hugging Face LLM Course & Agents Course (huggingface.co/learn)",
        "Hugging Face docs: Transformers v5, Tokenizers, Datasets, PEFT, TRL, Hub, TGI",
        "Model Context Protocol specification 2026-07-28 and 2025-11-25 (modelcontextprotocol.io)",
        "Anthropic Engineering: Building effective agents; Effective context engineering for AI agents; Writing tools for agents",
        "Chip Huyen, AI Engineering (O'Reilly, 2025), ch. 2, 5, 6, 7, 9, 10",
        "Vaswani et al. 2017; Su et al. 2021 (RoPE); Hu et al. 2021 (LoRA); Dettmers et al. 2023 (QLoRA); Rafailov et al. 2023 (DPO)",
    ],
    modules=[
        dict(
            id="transformers",
            title="Transformers from Scratch",
            summary="Embeddings, attention, masking, normalisation, positional encodings (sinusoidal and RoPE), FFN/MoE and the architecture families, built up in numpy.",
            lessons=[
                dict(id="attention-from-scratch", title="From embeddings to scaled dot-product attention", file="01-attention-from-scratch.md"),
                dict(id="transformer-block", title="The transformer block: multi-head, norms, residuals, FFN and MoE", file="02-transformer-block.md"),
                dict(id="positions-and-architectures", title="Positional encodings, RoPE, KV cache and architecture families", file="03-positions-and-architectures.md"),
            ],
            problems=["llm-scaled-dot-attention", "llm-causal-attention", "llm-multihead-split-merge",
                      "llm-layer-norm", "llm-sinusoidal-pe", "llm-rope-rotate"],
        ),
        dict(
            id="tokenization",
            title="Tokenization",
            summary="BPE, WordPiece, Unigram/SentencePiece and byte-level tokenizers; special tokens and chat templates.",
            lessons=[
                dict(id="subword-tokenizers", title="Subword tokenizers: BPE, WordPiece, Unigram, byte-level", file="04-subword-tokenizers.md"),
                dict(id="special-tokens-chat-templates", title="Special tokens, chat templates and tokenizer pitfalls", file="05-chat-templates.md"),
            ],
            problems=["llm-bpe-train", "llm-wordpiece-tokenize", "llm-chat-template"],
        ),
        dict(
            id="huggingface",
            title="The Hugging Face Ecosystem, Hands-On",
            summary="Hub, model cards, pipelines, Auto classes, generate() and decoding, datasets, Trainer, Accelerate, TGI/vLLM, Inference Providers and Spaces.",
            lessons=[
                dict(id="hub-pipelines-generate", title="Hub, pipelines, Auto classes and generate()", file="06-hub-pipelines-generate.md"),
                dict(id="datasets-trainer-serving", title="Datasets, Trainer, Accelerate and serving (TGI, vLLM, Spaces)", file="07-datasets-trainer-serving.md"),
            ],
            problems=["llm-top-p-filter"],
        ),
        dict(
            id="vector-search",
            title="Embeddings & Vector Search",
            summary="Sentence embeddings, similarity metrics, exact vs approximate search (HNSW, IVF, PQ) and the vector database landscape.",
            lessons=[
                dict(id="embeddings-similarity", title="Embeddings and similarity: from sentence-transformers to Matryoshka", file="08-embeddings-similarity.md"),
                dict(id="ann-indexes", title="ANN indexes (HNSW, IVF, PQ) and vector databases", file="09-ann-indexes.md"),
            ],
            problems=["llm-cosine-topk", "llm-ivf-search", "llm-greedy-graph-search"],
        ),
        dict(
            id="rag",
            title="Building RAG End-to-End",
            summary="Ingestion, chunking, metadata, hybrid search with RRF, cross-encoder reranking, citations, RAG evaluation, GraphRAG and agentic RAG.",
            lessons=[
                dict(id="ingestion-chunking", title="Ingestion, parsing and chunking strategies", file="10-ingestion-chunking.md"),
                dict(id="hybrid-retrieval-reranking", title="Hybrid retrieval, fusion, reranking and grounded generation", file="11-hybrid-retrieval-reranking.md"),
                dict(id="rag-eval-advanced", title="Evaluating RAG; GraphRAG and agentic RAG", file="12-rag-eval-advanced.md"),
            ],
            problems=["llm-chunk-overlap", "llm-rrf"],
        ),
        dict(
            id="finetuning",
            title="Finetuning Hands-On",
            summary="LoRA and QLoRA maths and code with peft, SFT with TRL, preference tuning with DPO, data formatting and evaluation.",
            lessons=[
                dict(id="lora-qlora", title="PEFT: LoRA, QLoRA and friends", file="13-lora-qlora.md"),
                dict(id="sft-dpo-trl", title="SFT and DPO with TRL: data, training loop, evaluation", file="14-sft-dpo-trl.md"),
            ],
            problems=["llm-lora-params", "llm-dpo-loss"],
        ),
        dict(
            id="agents",
            title="Agents & Tool Use",
            summary="Function calling with JSON Schema, the agent loop, ReAct, Anthropic's workflow patterns, multi-agent systems and frameworks such as smolagents.",
            lessons=[
                dict(id="function-calling", title="Function calling: schemas, the tool loop and parsing", file="15-function-calling.md"),
                dict(id="workflow-patterns", title="Workflows vs agents: the five patterns", file="16-workflow-patterns.md"),
                dict(id="agent-frameworks", title="ReAct, planning, multi-agent systems and frameworks", file="17-agent-frameworks.md"),
            ],
            problems=["llm-tool-call-parser", "llm-json-schema-validate"],
        ),
        dict(
            id="mcp",
            title="Model Context Protocol",
            summary="Why MCP exists, hosts/clients/servers, JSON-RPC messages, legacy handshake vs the 2026 stateless protocol, transports, primitives, building servers and securing them.",
            lessons=[
                dict(id="mcp-architecture", title="Why MCP: architecture and primitives", file="18-mcp-architecture.md"),
                dict(id="mcp-protocol", title="The wire protocol: JSON-RPC, lifecycle, transports", file="19-mcp-protocol.md"),
                dict(id="mcp-building", title="Building, connecting and securing MCP servers", file="20-mcp-building.md"),
            ],
            problems=["llm-mcp-jsonrpc", "llm-mcp-dispatcher"],
        ),
        dict(
            id="context-engineering",
            title="Context Engineering",
            summary="Attention budgets and context rot, system prompt altitude, just-in-time retrieval, compaction, memory, sub-agents, tool design and prompt caching.",
            lessons=[
                dict(id="context-budget", title="The context window as a budget: rot, altitude and retrieval", file="21-context-budget.md"),
                dict(id="long-horizon", title="Long-horizon agents: compaction, notes, memory and sub-agents", file="22-long-horizon.md"),
                dict(id="tools-and-caching", title="Designing tools for agents and prompt caching", file="23-tools-and-caching.md"),
            ],
            problems=["llm-context-packer", "llm-compaction-policy"],
        ),
        dict(
            id="app-engineering",
            title="LLM Application Engineering",
            summary="Structured outputs, streaming, guardrails and prompt-injection defence, observability and tracing, evals in CI, and cost/latency engineering.",
            lessons=[
                dict(id="structured-streaming", title="Structured outputs and streaming", file="24-structured-streaming.md"),
                dict(id="guardrails-security", title="Guardrails and prompt-injection defence", file="25-guardrails-security.md"),
                dict(id="observability-cost", title="Observability, evals in CI, cost and latency", file="26-observability-cost.md"),
            ],
            problems=["llm-stream-accumulate"],
        ),
    ],
)
