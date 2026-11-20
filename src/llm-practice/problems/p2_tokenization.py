_WP_VOCAB = ["[UNK]", "un", "##aff", "##able", "play", "##ing", "##ed", "##er", "p", "##l", "##a", "##y",
             "the", "a", "##s", "token", "##ize", "##r", "##ization", "trans", "##form", "##former", "!", "##!"]

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-bpe-train",
    title="Train a Toy BPE Tokenizer",
    difficulty="Medium",
    pattern="Tokenization",
    entry="bpe_train",
    description=r"""
Learn Byte-Pair Encoding merges from a small corpus.

`words` is a list of words (repeats express frequency). Start with every word split into single
characters. Then repeat up to `num_merges` times:

1. Count every **adjacent symbol pair** across all words (a word occurring 5 times contributes 5 to each
   of its pairs; a pair occurring twice inside one word counts twice, including overlaps such as
   `a a a`, which contains `(a, a)` twice).
2. Pick the pair with the **highest count**. Break ties by choosing the **lexicographically smallest**
   pair (compare the tuples `(left, right)` as Python does).
3. Merge that pair into one symbol everywhere, scanning each word **left to right** (so `a a a`
   with merge `(a, a)` becomes `aa a`).

Stop early if no pairs remain. Return the list of merges in order, each as `[left, right]`.

**Example:** `words = ["low", "low", "lower", "newest", "newest", "newest"]`, `num_merges = 3`

Counts start as `(e,s)=3, (e,w)=3, (l,o)=3, (n,e)=3, (o,w)=3, (s,t)=3, (w,e)=4, ...`, so the first merge
is `["w", "e"]`. Now `newest` is `n e we s t`, and five pairs tie at count 3: `(e,we)`, `(l,o)`,
`(n,e)`, `(s,t)`, `(we,s)`; the smallest is `("e", "we")`. The result is
`[["w", "e"], ["e", "we"], ["ewe", "s"]]`.
""",
    starter=r'''def bpe_train(words, num_merges):
    pass
''',
    solution=r'''from collections import Counter

def bpe_train(words, num_merges):
    vocab = Counter(tuple(w) for w in words if w)
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for sym, f in vocab.items():
            for a, b in zip(sym, sym[1:]):
                pairs[(a, b)] += f
        if not pairs:
            break
        best = min(pairs, key=lambda p: (-pairs[p], p))
        merges.append([best[0], best[1]])
        new_vocab = Counter()
        for sym, f in vocab.items():
            out, i = [], 0
            while i < len(sym):
                if i + 1 < len(sym) and sym[i] == best[0] and sym[i + 1] == best[1]:
                    out.append(sym[i] + sym[i + 1])
                    i += 2
                else:
                    out.append(sym[i])
                    i += 1
            new_vocab[tuple(out)] += f
        vocab = new_vocab
    return merges
''',
    tests=[
        [["low", "low", "lower", "newest", "newest", "newest"], 3],
        [["aaa"], 2],
        [["ab", "ab", "ab", "cd", "cd", "cd"], 2],
        [["hug"] * 10 + ["pug"] * 5 + ["pun"] * 12 + ["bun"] * 4 + ["hugs"] * 5, 6],
        [["a", "b", "c"], 5],
        [[], 3],
        [["abab", "abab", "ba"], 4],
        [["zz", "zz", "aa", "aa"], 1],
        [["banana"] * 3 + ["bandana"] * 2, 8],
        [["x"], 2],
        [["the", "then", "there", "the", "they", "other", "the"], 5],
        [["mississippi"], 6],
        [["ba", "ab", "ab", "ba", "cab"], 3],
    ],
    examples=2,
    wrong_solutions=[
        # ignores word frequency (uses the set of words)
        r'''from collections import Counter
def bpe_train(words, num_merges):
    vocab = [list(w) for w in set(words) if w]
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for sym in vocab:
            for a, b in zip(sym, sym[1:]):
                pairs[(a, b)] += 1
        if not pairs:
            break
        best = min(pairs, key=lambda p: (-pairs[p], p))
        merges.append([best[0], best[1]])
        nv = []
        for sym in vocab:
            out, i = [], 0
            while i < len(sym):
                if i + 1 < len(sym) and (sym[i], sym[i + 1]) == best:
                    out.append(sym[i] + sym[i + 1]); i += 2
                else:
                    out.append(sym[i]); i += 1
            nv.append(out)
        vocab = nv
    return merges
''',
        # tie-break by first occurrence instead of lexicographic order
        r'''from collections import Counter
def bpe_train(words, num_merges):
    vocab = [list(w) for w in words if w]
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for sym in vocab:
            for a, b in zip(sym, sym[1:]):
                pairs[(a, b)] += 1
        if not pairs:
            break
        best = max(pairs, key=lambda p: pairs[p])
        merges.append([best[0], best[1]])
        nv = []
        for sym in vocab:
            out, i = [], 0
            while i < len(sym):
                if i + 1 < len(sym) and (sym[i], sym[i + 1]) == best:
                    out.append(sym[i] + sym[i + 1]); i += 2
                else:
                    out.append(sym[i]); i += 1
            nv.append(out)
        vocab = nv
    return merges
''',
        # merges with string replace on a joined word (breaks symbol boundaries)
        r'''from collections import Counter
def bpe_train(words, num_merges):
    vocab = [" ".join(w) for w in words if w]
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for w in vocab:
            s = w.split()
            for a, b in zip(s, s[1:]):
                pairs[(a, b)] += 1
        if not pairs:
            break
        best = min(pairs, key=lambda p: (-pairs[p], p))
        merges.append([best[0], best[1]])
        vocab = [w.replace(best[0] + " " + best[1], best[0] + best[1]) for w in vocab]
    return merges
''',
    ],
    guide=dict(
        prereqs="Lesson *Subword tokenizers*, section on BPE; `collections.Counter`.",
        intuition="BPE is greedy compression: repeatedly glue together the pair of neighbouring symbols that occurs most often. Frequent words end up as single tokens; rare words stay as reusable pieces.",
        hints=[
            "Represent the corpus as a `Counter` mapping a tuple of symbols to the word's frequency. It makes counting weighted and fast.",
            "Count pairs with `zip(sym, sym[1:])`, adding the word frequency each time. Choose with `min(pairs, key=lambda p: (-pairs[p], p))` to get the highest count and the smallest pair on ties.",
            "Apply the merge with an index loop: if `sym[i], sym[i+1]` equals the pair, append the concatenation and skip two; otherwise append one symbol.",
        ],
        brute_force="Recount all pairs from scratch after each merge, as described: $O(\\text{merges} \\times \\text{corpus size})$. That is what this problem expects; production trainers update pair counts incrementally with a priority queue.",
        approach="1. Build the word-frequency table of symbol tuples.\n2. Loop `num_merges` times: count pairs; stop if none; pick the best pair with the tie-break; record it; rewrite every word.\n\n**Dry run** (`['aaa'], 2`): symbols `a a a`, pair `(a,a)` counted twice, merge left-to-right gives `aa a`. Next the only pair is `(aa, a)`, giving `aaa`. Result `[['a','a'], ['aa','a']]`.",
        complexity="Each merge scans the corpus: $O(M \\cdot N)$ time for $M$ merges and $N$ total symbols; $O(N)$ space.",
        pitfalls="- Ignoring word frequencies (de-duplicating the corpus).\n- Tie-breaking by dictionary insertion order, which makes training non-deterministic across implementations.\n- Merging with string `replace` on space-joined symbols: `'a b' -> 'ab'` also matches inside `'ba b'`-style boundaries such as `c a b` vs `ca b`, corrupting multi-character symbols.\n- Merging across word boundaries.",
        follow_up="Write `encode(word, merges)` that replays merges by rank; switch to byte-level by starting from `word.encode('utf-8')`; add an end-of-word marker.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-wordpiece-tokenize",
    title="WordPiece Greedy Longest-Match Tokenizer",
    difficulty="Medium",
    pattern="Tokenization",
    entry="wordpiece",
    description=r"""
Implement BERT-style WordPiece **encoding** (the vocabulary is given).

Split `text` on whitespace. For each word, repeatedly take the **longest** prefix of the remaining
characters that is in `vocab`; pieces that do not start the word must be looked up with a `##` prefix.
If at any position no piece matches, the **entire word** becomes a single `unk` token (no partial
output for that word). Words longer than `max_chars` characters also become `unk`.

Return the flat list of tokens.

**Example:** `vocab = ["un", "##aff", "##able", "play", "##ing"]`

- `"unaffable playing"` gives `["un", "##aff", "##able", "play", "##ing"]`
- `"plays"` gives `["[UNK]"]` (`play` matches, but `##s` is not in the vocabulary)
""",
    starter=r'''def wordpiece(text, vocab, unk="[UNK]", max_chars=100):
    pass
''',
    solution=r'''def wordpiece(text, vocab, unk="[UNK]", max_chars=100):
    vocab = set(vocab)
    out = []
    for word in text.split():
        if len(word) > max_chars:
            out.append(unk)
            continue
        pieces, start, bad = [], 0, False
        while start < len(word):
            end, cur = len(word), None
            while start < end:
                piece = word[start:end]
                if start > 0:
                    piece = "##" + piece
                if piece in vocab:
                    cur = piece
                    break
                end -= 1
            if cur is None:
                bad = True
                break
            pieces.append(cur)
            start = end
        out.extend([unk] if bad else pieces)
    return out
''',
    tests=[
        ["unaffable playing", ["un", "##aff", "##able", "play", "##ing"]],
        ["plays", ["un", "##aff", "##able", "play", "##ing"]],
        ["the tokenizer played", _WP_VOCAB],
        ["", _WP_VOCAB],
        ["transformer transform trans", _WP_VOCAB],
        ["tokenization   tokenize\ttokens", _WP_VOCAB],
        ["play!", _WP_VOCAB],
        ["!play", _WP_VOCAB],
        ["playplay", _WP_VOCAB],
        ["supercalifragilistic", _WP_VOCAB, "[UNK]", 10],
        ["a aa aaa", ["a", "##a"]],
        ["player players xyz", _WP_VOCAB, "<unk>"],
        ["ing ##ing", ["##ing", "ing", "#", "###", "##i", "##n", "##g"]],
        ["unable", ["un", "##able", "u", "##n", "##a", "##b", "##l", "##e", "una", "##ble"]],
    ],
    examples=2,
    wrong_solutions=[
        # emits the matched pieces and then UNK for the rest instead of whole-word UNK
        r'''def wordpiece(text, vocab, unk="[UNK]", max_chars=100):
    vocab = set(vocab); out = []
    for word in text.split():
        if len(word) > max_chars:
            out.append(unk); continue
        start = 0
        while start < len(word):
            end, cur = len(word), None
            while start < end:
                piece = word[start:end] if start == 0 else "##" + word[start:end]
                if piece in vocab:
                    cur = piece; break
                end -= 1
            if cur is None:
                out.append(unk); break
            out.append(cur); start = end
    return out
''',
        # shortest match instead of longest
        r'''def wordpiece(text, vocab, unk="[UNK]", max_chars=100):
    vocab = set(vocab); out = []
    for word in text.split():
        if len(word) > max_chars:
            out.append(unk); continue
        pieces, start, bad = [], 0, False
        while start < len(word):
            cur = None
            for end in range(start + 1, len(word) + 1):
                piece = word[start:end] if start == 0 else "##" + word[start:end]
                if piece in vocab:
                    cur = piece; break
            if cur is None:
                bad = True; break
            pieces.append(cur); start = end
        out.extend([unk] if bad else pieces)
    return out
''',
        # forgets the ## prefix for continuation pieces
        r'''def wordpiece(text, vocab, unk="[UNK]", max_chars=100):
    vocab = set(vocab); out = []
    for word in text.split():
        if len(word) > max_chars:
            out.append(unk); continue
        pieces, start, bad = [], 0, False
        while start < len(word):
            end, cur = len(word), None
            while start < end:
                if word[start:end] in vocab:
                    cur = word[start:end]; break
                end -= 1
            if cur is None:
                bad = True; break
            pieces.append(cur); start = end
        out.extend([unk] if bad else pieces)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Subword tokenizers*, section on WordPiece.",
        intuition="Read the word left to right, always biting off the biggest chunk the vocabulary knows. Chunks after the first are marked with `##` so the original word boundaries can be recovered. One unmatchable position spoils the whole word.",
        hints=[
            "Put the vocabulary in a `set`. For each word keep a `start` index and try `end` from `len(word)` down to `start + 1`.",
            "When `start > 0`, look up `'##' + word[start:end]`.",
            "Collect pieces in a temporary list per word; only extend the output if the whole word was consumed, otherwise append a single `unk`.",
        ],
        brute_force="Try every segmentation of the word and keep one whose pieces are all in the vocabulary: exponential. Greedy longest-match is the defined algorithm and is $O(L^2)$ per word.",
        approach="For each whitespace-separated word:\n1. If it is longer than `max_chars`, emit `unk`.\n2. `start = 0`; while `start < len(word)`: scan `end` downward for the longest matching piece (with `##` if `start > 0`).\n3. No match: mark the word bad and stop. Match: record it and set `start = end`.\n4. Emit the pieces, or one `unk`.\n\n**Dry run** (`unaffable`): longest prefix in vocab is `un`; from index 2 the longest `##`-piece is `##aff`; then `##able`. Output `[un, ##aff, ##able]`.",
        complexity="$O(L^2)$ substring checks per word of length $L$ (each check hashes up to $L$ characters); $O(L)$ extra space.",
        pitfalls="- Emitting partial pieces before the `[UNK]`.\n- Forgetting `##` on continuation pieces, or adding it to the first piece.\n- Shortest-match instead of longest-match.\n- Greedy is not optimal: `unable` with vocab containing `una`, `un`, `##able`, `##ble` tokenises as `una + ##ble`, and that is the specified behaviour.",
        follow_up="Add BERT's basic pre-tokenisation (lower-casing, splitting punctuation); implement decoding by stripping `##`; compare with BPE merge-replay on the same words.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-chat-template",
    title="ChatML Chat-Template Renderer",
    difficulty="Medium",
    pattern="Tokenization",
    entry="render_chat",
    description=r"""
Render a list of chat messages into the flat **ChatML** string a model is trained on (Hermes/Qwen-style
tool calls).

Each message is a dict with `role` (`system`, `user`, `assistant` or `tool`) and `content` (string).
Assistant messages may also have `tool_calls`: a list of `{"name": str, "arguments": dict}`.

Rules:

1. If `default_system` is a non-empty string and the first message is **not** a system message (or
   there are no messages), prepend a system message with that content.
2. `system`, `user` and `assistant` messages render as
   `<|im_start|>{role}\n{body}<|im_end|>\n`.
3. For an assistant message with tool calls, `body` is the content followed by one block per call:
   `<tool_call>\n{json}\n</tool_call>` where `json = json.dumps({"name": ..., "arguments": ...})`
   (default separators, keys in that order). Separate the content and the blocks, and consecutive
   blocks, with a single `\n`. If the content is empty, the body starts directly with the first block.
4. A `tool` message renders as a **user** turn whose body is
   `<tool_response>\n{content}\n</tool_response>`.
5. If `add_generation_prompt` is true, append `<|im_start|>assistant\n` at the end.

**Example:** `messages = [{"role": "user", "content": "Hi"}]`, `add_generation_prompt = True`,
`default_system = "Be brief."` renders

```text
<|im_start|>system
Be brief.<|im_end|>
<|im_start|>user
Hi<|im_end|>
<|im_start|>assistant
```

(followed by a final newline).
""",
    starter=r'''import json

def render_chat(messages, add_generation_prompt=True, default_system=""):
    pass
''',
    solution=r'''import json

def render_chat(messages, add_generation_prompt=True, default_system=""):
    msgs = list(messages)
    if default_system and (not msgs or msgs[0]["role"] != "system"):
        msgs = [{"role": "system", "content": default_system}] + msgs
    out = []
    for m in msgs:
        role, content = m["role"], m.get("content") or ""
        if role == "tool":
            role = "user"
            body = "<tool_response>\n" + content + "\n</tool_response>"
        else:
            parts = [content] if content else []
            if role == "assistant":
                for c in m.get("tool_calls") or []:
                    parts.append("<tool_call>\n" + json.dumps({"name": c["name"], "arguments": c["arguments"]})
                                 + "\n</tool_call>")
            body = "\n".join(parts)
        out.append("<|im_start|>" + role + "\n" + body + "<|im_end|>\n")
    if add_generation_prompt:
        out.append("<|im_start|>assistant\n")
    return "".join(out)
''',
    tests=[
        [[{"role": "user", "content": "Hi"}], True, "Be brief."],
        [[{"role": "system", "content": "You are a pirate."}, {"role": "user", "content": "Hello"},
          {"role": "assistant", "content": "Arr!"}], False, "Be brief."],
        [[{"role": "user", "content": "Hi"}], True, ""],
        [[], True, "You are helpful."],
        [[], False, ""],
        [[{"role": "user", "content": "Weather in Oslo?"},
          {"role": "assistant", "content": "", "tool_calls": [{"name": "get_weather", "arguments": {"city": "Oslo"}}]},
          {"role": "tool", "content": "{\"temp\": 3}"}], True, ""],
        [[{"role": "user", "content": "Compare Oslo and Bergen"},
          {"role": "assistant", "content": "Checking both.",
           "tool_calls": [{"name": "get_weather", "arguments": {"city": "Oslo"}},
                          {"name": "get_weather", "arguments": {"city": "Bergen", "days": 2}}]},
          {"role": "tool", "content": "3C"}, {"role": "tool", "content": "7C"},
          {"role": "assistant", "content": "Bergen is warmer."}], False, "Use tools."],
        [[{"role": "user", "content": "line1\nline2"}, {"role": "assistant", "content": "ok"},
          {"role": "user", "content": ""}], True, ""],
        [[{"role": "user", "content": "a"}, {"role": "system", "content": "late system"}], True, "Default."],
        [[{"role": "assistant", "content": "No tools here", "tool_calls": []}], False, ""],
        [[{"role": "user", "content": "x", "tool_calls": [{"name": "ignored", "arguments": {}}]}], False, ""],
        [[{"role": "assistant", "content": "", "tool_calls": [{"name": "noop", "arguments": {}}]}], True, "S"],
    ],
    examples=2,
    wrong_solutions=[
        # always prepends the default system prompt, even when one exists
        r'''import json
def render_chat(messages, add_generation_prompt=True, default_system=""):
    msgs = list(messages)
    if default_system:
        msgs = [{"role": "system", "content": default_system}] + msgs
    out = []
    for m in msgs:
        role, content = m["role"], m.get("content") or ""
        if role == "tool":
            role = "user"; body = "<tool_response>\n" + content + "\n</tool_response>"
        else:
            parts = [content] if content else []
            if role == "assistant":
                for c in m.get("tool_calls") or []:
                    parts.append("<tool_call>\n" + json.dumps({"name": c["name"], "arguments": c["arguments"]}) + "\n</tool_call>")
            body = "\n".join(parts)
        out.append("<|im_start|>" + role + "\n" + body + "<|im_end|>\n")
    if add_generation_prompt:
        out.append("<|im_start|>assistant\n")
    return "".join(out)
''',
        # ignores tool calls and renders tool messages with role "tool"
        r'''def render_chat(messages, add_generation_prompt=True, default_system=""):
    msgs = list(messages)
    if default_system and (not msgs or msgs[0]["role"] != "system"):
        msgs = [{"role": "system", "content": default_system}] + msgs
    out = ["<|im_start|>" + m["role"] + "\n" + (m.get("content") or "") + "<|im_end|>\n" for m in msgs]
    if add_generation_prompt:
        out.append("<|im_start|>assistant\n")
    return "".join(out)
''',
        # missing newline after the generation prompt header / always adds it
        r'''import json
def render_chat(messages, add_generation_prompt=True, default_system=""):
    msgs = list(messages)
    if default_system and (not msgs or msgs[0]["role"] != "system"):
        msgs = [{"role": "system", "content": default_system}] + msgs
    out = []
    for m in msgs:
        role, content = m["role"], m.get("content") or ""
        if role == "tool":
            role = "user"; body = "<tool_response>\n" + content + "\n</tool_response>"
        else:
            parts = [content] if content else []
            if role == "assistant":
                for c in m.get("tool_calls") or []:
                    parts.append("<tool_call>\n" + json.dumps({"name": c["name"], "arguments": c["arguments"]}) + "\n</tool_call>")
            body = "\n".join(parts)
        out.append("<|im_start|>" + role + "\n" + body + "<|im_end|>\n")
    out.append("<|im_start|>assistant")
    return "".join(out)
''',
    ],
    guide=dict(
        prereqs="Lesson *Special tokens, chat templates and tokenizer pitfalls*; `json.dumps`.",
        intuition="A chat template is a small, exact string-formatting program. The model was trained on byte-identical formatting, so every newline and special token matters. Tool calls and tool results are just more text wrapped in agreed tags.",
        hints=[
            "Handle the default system prompt first by building a new list; do not mutate the input.",
            "Build each message body separately: content, then `<tool_call>` blocks joined with `\\n`; tool messages become user turns with a `<tool_response>` wrapper.",
            "Finish with `<|im_start|>assistant\\n` only when `add_generation_prompt` is true.",
        ],
        brute_force="There is no asymptotically different approach; a single pass over the messages concatenating strings is the solution.",
        approach="1. Prepend the default system message when needed.\n2. For each message compute `(role, body)`.\n3. Emit `<|im_start|>role\\nbody<|im_end|>\\n`.\n4. Optionally append the generation prompt.\n\n**Dry run:** user `Hi` with default system `Be brief.` produces a system turn, a user turn, then the open assistant header.",
        complexity="$O(n)$ in the total length of the messages.",
        pitfalls="- Prepending the default system prompt when the conversation already starts with one.\n- Adding the generation prompt during training-style rendering (`add_generation_prompt=False`).\n- Leaving a leading `\\n` before the first `<tool_call>` when the content is empty.\n- Rendering `tool_calls` on non-assistant messages.\n- Using custom JSON separators: the expected output uses `json.dumps` defaults.",
        follow_up="Render Llama 3's header format instead; add a `tools` parameter that injects JSON schemas into the system turn; return an assistant-token mask for assistant-only loss.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-top-p-filter",
    title="Temperature, Top-k and Top-p Filtering",
    difficulty="Medium",
    pattern="Decoding",
    entry="filter_probs",
    compare="float",
    description=r"""
Implement the logits-processing pipeline behind `generate(do_sample=True, temperature=..., top_k=...,
top_p=...)` and return the final **probability distribution** to sample from.

Steps, in this order:

1. **Temperature:** divide the logits by `temperature` (> 0).
2. **Top-k:** if `top_k > 0`, keep only the `top_k` highest-scoring tokens (if `top_k` exceeds the
   vocabulary size keep everything). Ties are resolved in favour of the **lower index**.
3. **Top-p (nucleus):** if `top_p < 1`, compute the softmax over the tokens that survived step 2, sort
   them by probability descending (ties: lower index first) and keep the smallest prefix whose
   cumulative probability is **at least** `top_p`. Equivalently, keep a token if the cumulative
   probability of the tokens *before* it is `< top_p`. At least one token is always kept.
4. Renormalise: softmax over the remaining tokens; removed tokens get probability `0`.

Return a list of probabilities with the same length as `logits`.

**Example:** `logits = [2.0, 1.0, 0.0]`, `temperature = 1`, `top_k = 0`, `top_p = 0.8`.
Softmax is about `[0.665, 0.245, 0.090]`. Token 0 alone has 0.665 < 0.8, so token 1 is also kept
(0.910 >= 0.8); token 2 is dropped. Result is about `[0.731, 0.269, 0.0]`.
""",
    starter=r'''import numpy as np

def filter_probs(logits, temperature=1.0, top_k=0, top_p=1.0):
    pass
''',
    solution=r'''import numpy as np

def filter_probs(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = np.asarray(logits, dtype=float) / temperature
    n = len(z)
    order = sorted(range(n), key=lambda i: (-z[i], i))
    keep = order[:top_k] if 0 < top_k < n else order
    def softmax(idx):
        v = z[idx] - z[idx].max()
        e = np.exp(v)
        return e / e.sum()
    if top_p < 1.0:
        p = softmax(keep)
        kept, cum = [], 0.0
        for i, pi in zip(keep, p):
            if kept and cum >= top_p:
                break
            kept.append(i)
            cum += pi
        keep = kept
    out = np.zeros(n)
    out[keep] = softmax(keep)
    return out
''',
    tests=[
        [[2.0, 1.0, 0.0], 1.0, 0, 0.8],
        [[2.0, 1.0, 0.0], 1.0, 0, 1.0],
        [[2.0, 1.0, 0.0], 0.5, 0, 1.0],
        [[2.0, 1.0, 0.0], 2.0, 0, 1.0],
        [[1.0, 3.0, 2.0, 0.5], 1.0, 2, 1.0],
        [[1.0, 3.0, 2.0, 0.5], 1.0, 10, 1.0],
        [[4.0, 3.5, 3.0, 1.0, 0.5, -2.0], 1.0, 0, 0.9],
        [[4.0, 3.5, 3.0, 1.0, 0.5, -2.0], 0.7, 4, 0.75],
        [[0.0, 0.0, 0.0, 0.0], 1.0, 2, 1.0],
        [[5.0, 1.0, 1.0], 1.0, 0, 0.5],
        [[1000.0, 999.0, 0.0], 1.0, 0, 0.99],
        [[0.3], 1.0, 0, 0.1],
        [[1.0, 2.0, 3.0, 4.0, 5.0], 1.5, 3, 0.6],
        [[-1.0, -1.0, 2.0, 2.0], 1.0, 3, 0.7],
        [[0.5, 2.5, 2.4, 0.1, 2.3], 1.0, 0, 0.05],
    ],
    examples=2,
    wrong_solutions=[
        # drops the token that crosses the threshold (keeps cum <= top_p only)
        r'''import numpy as np
def filter_probs(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = np.asarray(logits, dtype=float) / temperature
    n = len(z)
    order = sorted(range(n), key=lambda i: (-z[i], i))
    keep = order[:top_k] if 0 < top_k < n else order
    def softmax(idx):
        v = z[idx] - z[idx].max(); e = np.exp(v); return e / e.sum()
    if top_p < 1.0:
        p = softmax(keep); kept, cum = [], 0.0
        for i, pi in zip(keep, p):
            cum += pi
            if kept and cum > top_p:
                break
            kept.append(i)
        keep = kept
    out = np.zeros(n); out[keep] = softmax(keep)
    return out
''',
        # ignores temperature
        r'''import numpy as np
def filter_probs(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = np.asarray(logits, dtype=float)
    n = len(z)
    order = sorted(range(n), key=lambda i: (-z[i], i))
    keep = order[:top_k] if 0 < top_k < n else order
    def softmax(idx):
        v = z[idx] - z[idx].max(); e = np.exp(v); return e / e.sum()
    if top_p < 1.0:
        p = softmax(keep); kept, cum = [], 0.0
        for i, pi in zip(keep, p):
            if kept and cum >= top_p:
                break
            kept.append(i); cum += pi
        keep = kept
    out = np.zeros(n); out[keep] = softmax(keep)
    return out
''',
        # does not renormalise after filtering
        r'''import numpy as np
def filter_probs(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = np.asarray(logits, dtype=float) / temperature
    n = len(z)
    e = np.exp(z - z.max()); full = e / e.sum()
    order = sorted(range(n), key=lambda i: (-z[i], i))
    keep = order[:top_k] if 0 < top_k < n else order
    if top_p < 1.0:
        tot = full[keep].sum(); kept, cum = [], 0.0
        for i in keep:
            if kept and cum >= top_p:
                break
            kept.append(i); cum += full[i] / tot
        keep = kept
    out = np.zeros(n); out[keep] = full[keep]
    return out
''',
        # top-k keeps all tokens tied with the k-th value
        r'''import numpy as np
def filter_probs(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = np.asarray(logits, dtype=float) / temperature
    n = len(z)
    order = sorted(range(n), key=lambda i: (-z[i], i))
    if 0 < top_k < n:
        kth = z[order[top_k - 1]]
        keep = [i for i in order if z[i] >= kth]
    else:
        keep = order
    def softmax(idx):
        v = z[idx] - z[idx].max(); e = np.exp(v); return e / e.sum()
    if top_p < 1.0:
        p = softmax(keep); kept, cum = [], 0.0
        for i, pi in zip(keep, p):
            if kept and cum >= top_p:
                break
            kept.append(i); cum += pi
        keep = kept
    out = np.zeros(n); out[keep] = softmax(keep)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Hub, pipelines, Auto classes and generate()*, section on sampling filters; stable softmax.",
        intuition="Sampling from the raw distribution occasionally picks absurd tokens from the long tail. Temperature reshapes the distribution, top-k cuts the tail at a fixed count, and top-p cuts it at a fixed probability mass that adapts to how confident the model is.",
        hints=[
            "Sort indices once by `(-scaled_logit, index)`; both top-k and top-p then work on prefixes of that order.",
            "For top-p, walk the sorted tokens with a running sum and stop *before* adding a token once the sum so far is already `>= top_p`.",
            "Write a helper that returns the softmax over a list of kept indices, and scatter it into a zero vector at the end.",
        ],
        brute_force="Recompute a softmax for every candidate prefix length and pick the first whose mass reaches `top_p`: $O(V^2)$. The cumulative-sum walk is $O(V \\log V)$ for the sort.",
        approach="1. `z = logits / temperature`.\n2. `order` = indices sorted by descending `z` (ties: lower index).\n3. Top-k: keep `order[:k]` when `0 < k < V`.\n4. Top-p: softmax over the kept tokens, keep the minimal prefix reaching `top_p`.\n5. Softmax over the survivors, zeros elsewhere.\n\n**Dry run** (`[2,1,0]`, p = 0.8): probabilities `[0.665, 0.245, 0.090]`; cumulative before each token `0, 0.665, 0.910`; keep while it is `< 0.8`, so tokens 0 and 1; renormalise to `[0.731, 0.269, 0]`.",
        complexity="$O(V \\log V)$ time for the sort, $O(V)$ space.",
        pitfalls="- Off-by-one in nucleus selection: the token that *crosses* the threshold must be included.\n- Returning unnormalised probabilities.\n- Applying temperature after filtering (top-p's cut depends on the tempered distribution).\n- Overflow in softmax for large logits: subtract the max.\n- Ties in top-k: the specification keeps exactly `k` tokens.",
        follow_up="Add `min_p` (keep tokens with probability at least `min_p * p_max`) and a repetition penalty; implement the sampler with a seeded RNG and check empirical frequencies.",
    ),
),
]
