# AI Engineering Best Practices (for Nimbus)

Source: synthesized from Chip Huyen's publicly published writing that is
directly adapted from her book **"AI Engineering: Building Applications
with Foundation Models"** (O'Reilly, 2025). This is not a copy of the
book — it's my own summary/notes distilled from her public blog posts,
written so we can apply the ideas concretely to Nimbus. Read the
originals for full depth:

- [Agents](https://huyenchip.com/2025/01/07/agents.html) — adapted directly from the book's Agents chapter
- [Common pitfalls when building generative AI applications](https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html)
- [Building A Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html) — precursor to the book's architecture chapter
- [Generation configurations: temperature, top-k, top-p, and test time compute](https://huyenchip.com/2024/01/16/sampling.html)
- [Predictive Human Preference: From Model Ranking to Model Routing](https://huyenchip.com/2024/02/28/predictive-human-preference.html)
- [Building LLM applications for production](https://huyenchip.com/2023/04/11/llm-engineering.html) — earlier precursor material

Each section below ends with **"For Nimbus"** — a concrete note on how
this applies to our codebase, tying back to specific files/phases in
[EXECUTION-PLAN.md](../../EXECUTION-PLAN.md) and the `docs/PHASE-N-TODOS.md` files.

---

## 1. Agents: environment, tools, planning

An agent is defined by two things: the **environment** it operates in and
the **set of actions/tools** it has access to. The model itself is just
the "brain" that plans a sequence of actions and decides when a task is
done.

### Why agents need stronger models / fail more
Agents typically require more capable models than single-shot tasks
because of two compounding factors:
- **Compound mistakes** — accuracy drops multiplicatively per step. At
  95% accuracy/step, 10 steps → ~60% overall; 100 steps → ~0.6%. This is
  a strong argument for keeping Nimbus's tool-call chains short.
- **Higher stakes** — tool access means failures have real consequences,
  not just a bad text response.

### Tool categories
1. **Knowledge augmentation** (read-only) — retrievers, SQL executors,
   web search. These fight staleness and hallucination by grounding
   responses in real data.
2. **Capability extension** — calculators, unit converters, code
   interpreters — cheap ways to patch a model's known weaknesses (e.g.
   arithmetic) instead of trying to train/prompt the weakness away.
3. **Write actions** — anything that changes state (send email, update a
   record, issue a refund). Vastly more powerful, vastly more dangerous.
   Treat write actions like giving an intern prod database access:
   default to requiring human approval for anything hard to reverse.

### Planning should be decoupled from execution
Don't let a model plan-and-execute in one breath. Instead:
1. Generate a plan.
2. **Validate** the plan (heuristics: reject plans using tools not in the
   inventory, reject plans over N steps; or an AI judge that scores plan
   sanity) *before* executing anything.
3. Only execute validated plans.

This alone prevents an agent from silently burning API budget on a
1,000-step plan that goes nowhere.

### Reflection improves outcomes, at a cost
Interleaving "think → act → observe → reflect" (the ReAct pattern) or a
separate evaluator+self-reflection step (Reflexion) meaningfully improves
task success, at the cost of extra latency/tokens per turn. Reflection
matters most: after receiving a query (is it feasible?), after plan
generation (is it sane?), after each step (on track?), and after the
full plan (actually done — watch out for an agent that *thinks* it
succeeded when it didn't).

### Control flow
Plans aren't always sequential. Real agent systems need **sequential,
parallel, if/branch (routing), and for-loop (repeat-until)** control
flow. Parallel tool calls materially reduce user-perceived latency (e.g.
looking up account + billing at the same time instead of one after the
other).

### Tool selection is an empirical exercise, not a guess
- More tools = more capability but harder for the model to use them well.
- Do ablations: remove a tool, see if performance actually drops.
- Track the distribution of tool calls — rarely-used or frequently-misused
  tools are candidates for simplification or removal.
- Different tasks and different models prefer different tools — this
  isn't universal, it's empirical per-app.

### Agent failure modes (this is your evaluation checklist)
- **Planning failures**: invalid tool referenced, valid tool/invalid
  parameters, valid tool/wrong parameter values, goal not met, false
  "I'm done" reflection.
- **Tool failures**: right tool called, wrong output returned (or a
  translation-layer bug if you use natural-language plans + a translator).
- **Efficiency failures**: too many steps, too slow, too expensive per
  completed task, relative to a human/baseline.

**Tip carried over directly:** always log what parameter values the
agent used for each tool call and inspect them — most silent failures
hide in wrong parameter values, not wrong tool choice.

**For Nimbus:** this maps almost one-to-one onto `backend/app/agent/agent.py`
and `backend/app/agent/tools/`. Phase 1's `AgentDecision` enum is exactly
the "validated plan before execution" boundary described above. Phase 3's
eval suite should explicitly score the three failure-mode categories
above (planning / tool / efficiency), not just "did it answer correctly."

---

## 2. Context construction (RAG)

- **Chunking** is required once documents exceed manageable size; chunk
  size is a function of model context limit + your latency budget.
- **Term-based retrieval** (BM25/Elasticsearch) is cheap, fast, and a
  legitimately strong baseline — don't skip straight to embeddings.
- **Embedding-based (vector) retrieval** is more expensive but improves
  more over time with tuning. Compare ANN algorithms on recall, queries/sec,
  build time, and index size — there's always a tradeoff.
- **Hybrid search**: cheap term-based retrieval fetches candidates, then a
  more precise step (vector similarity or a reranker) narrows to the best
  few. This "retrieve cheap, rerank precise" pattern is the industry
  default, not an exotic optimization.
- **Document order in context still matters** — models attend better to
  the beginning/end of context ("lost in the middle"), so put your most
  important grounding chunks first or last, not buried in the middle.
- **Query rewriting**: conversational follow-ups ("How about Emily Doe?")
  are ambiguous out of context — rewrite them into standalone queries
  before retrieval, using the conversation history. If the rewrite can't
  be resolved (e.g. needs info you don't have), the rewriter should say so
  rather than hallucinate a value.
- **RAG with tabular/SQL data** is a distinct pipeline: text-to-SQL →
  execute → generate response from the result, not a vector search.

**For Nimbus:** this is Phase 2 exactly. Start with term-based/keyword
retrieval over the knowledge base as the baseline before adding a vector
store — it's a legitimate, citable production pattern, not a shortcut.
Implement query rewriting before retrieval once multi-turn conversations
are common (e.g. "what about my other line?").

---

## 3. Guardrails

### Input guardrails
- **PII/secret leakage to third-party model APIs** is a real, documented
  incident category (e.g. Samsung/ChatGPT 2023). Detect and mask
  sensitive data before it leaves your system; keep a reversible mapping
  if you need to unmask it in the final response.
- **Jailbreaking / prompt injection**: never let a model's output
  directly trigger a write action without a policy check. Define
  out-of-scope topics explicitly (e.g. a support agent shouldn't answer
  political questions) and filter/classify for them.

### Output guardrails
Concrete failure modes to detect and handle: empty responses,
malformatted responses (validate against your schema — this is exactly
why Nimbus's typed `ChatResponse` matters), toxic responses, factually
inconsistent/hallucinated responses, leaked sensitive data, and
brand-risk responses (mischaracterizing your own product/company).

### Failure management
- Cheap first line of defense: **retry logic** (empty/malformed → retry
  N times). Retrying in parallel (fire 2 requests at once, take the
  better one) trades cost for latency instead of cost for cost+latency.
- **Escalate to a human** on specific triggers: keyword match, sentiment
  detection (user getting angry), or turn-count limits (prevent
  infinite-loop conversations).

### Tradeoffs to consciously accept, not ignore
- Guardrails add latency — most teams find this worth it, but it's a
  real, measurable cost you should track, not hand-wave away.
- Streaming responses makes output guardrails harder — by the time you'd
  block an unsafe response, part of it may already be on the user's
  screen.

**For Nimbus:** this is Phase 4, but the *output* guardrail (schema
validation, retry-then-escalate) should exist from Phase 1 — it's the
same mechanism as the "fail closed" principle already in
`docs/PHASE-1-TODOS.md`. Tool `requires_approval` flags are exactly the
"no write action without policy check" rule.

---

## 4. Routing and the model gateway

- A **router** (usually a small, fast intent classifier — doesn't need to
  be a full LLM call) decides which specialized path/model handles a
  query, can reject out-of-scope queries cheaply (without wasting a full
  model call), and can trigger clarification questions for ambiguous
  input.
- A **model gateway** is a thin, unified interface over multiple model
  providers. Real, concrete benefits: centralized API-key management
  (keys never touch app code directly), per-user/app access control,
  usage monitoring/cost caps, and automatic **fallback** to a secondary
  model/provider on rate-limit or outage — this is a resilience pattern,
  not just convenience.
- Routing/scoring models are typically small and cheap relative to the
  generation model — you can afford to run several of them per request.

**For Nimbus:** not urgent for Phase 1, but the intent-classification
idea is directly relevant to the `AgentDecision` split — "is this in
scope at all" is logically a routing decision that happens *before* the
main agent loop, and is worth separating out once Nimbus has more than
one specialized flow (e.g. billing vs. troubleshooting).

---

## 5. Caching

Three distinct caching layers, don't conflate them:
1. **Prompt cache** — reuse processed tokens for repeated prompt
   prefixes (e.g. your system prompt). Usually provided by the model API
   itself; huge cost savings at scale, but you don't implement it
   yourself.
2. **Exact cache** — cache full outputs for byte-identical repeated
   inputs (e.g. "summarize product X" asked by multiple users). Needs an
   eviction policy (LRU/LFU/FIFO) and shouldn't cache
   user-specific or time-sensitive queries ("what's the status of *my*
   order").
3. **Semantic cache** — reuse answers for *similar* (not identical)
   queries via embedding similarity. Explicitly flagged as higher-risk:
   depends on embedding quality + a well-tuned similarity threshold, and
   a wrong match silently returns a wrong answer. Don't reach for this
   until exact cache + retrieval are solid.

**For Nimbus:** low priority until Phase 5+/scale concerns. Worth an
exact-cache layer around expensive tool calls (e.g. repeated billing
lookups) before ever considering semantic cache.

---

## 6. Observability

Three pillars — build all three in from the start, not as an
afterthought:
- **Metrics**: system metrics (throughput, uptime) + model metrics
  (accuracy/hallucination/toxicity rate) + per-step pipeline metrics
  (e.g. retrieval precision). Track latency granularly: **TTFT** (time to
  first token), **TBT** (time between tokens), **TPS**, **total
  latency** — these are the standard LLM-specific latency metrics.
  Break every metric down by user/version/prompt-type/time, not just
  a single aggregate number.
- **Logs**: log everything — config, query, output, intermediate steps,
  component start/end/crash — with tags/IDs so you can trace a log line
  back to its request. Manual daily inspection of a small sample of
  production logs (even 15 minutes) reliably surfaces issues automated
  metrics miss.
- **Traces**: the full path of one request through every component
  (retrieval → prompt construction → model call → tool calls → final
  response), with per-step timing/cost, so a failed request can be
  pinpointed to the exact step that went wrong.

**For Nimbus:** this is Phase 3, and it's meant to be built on top of
whatever logging you already added in Phase 1 per the TODOs ("logging
from day one"). The trace viewer in the operator console should show
exactly this per-request breakdown.

---

## 7. Orchestration

An orchestrator does two things: lets you declare your components
(models, DBs, tools) and lets you **chain** them (the sequence of steps
from query to final response). Advice that's easy to skip and shouldn't
be:

> **Start without an orchestration framework.** Build your first pipeline
> by hand. Frameworks abstract away details you need to understand and
> debug early on, and framework bugs (e.g. a typo in a default prompt) can
> silently change your app's behavior on an update you didn't ask for.

When you do evaluate an orchestrator later, judge it on: integration with
components you already use, support for complex control flow (branching,
parallelism, error handling), and whether it hides API calls or adds
latency you didn't ask for.

**For Nimbus:** directly validates the current plan — Phase 1-3 use a
hand-rolled agent loop; LangGraph (or similar) is explicitly deferred to
Phase 5 in [EXECUTION-PLAN.md](../../EXECUTION-PLAN.md), which matches this advice exactly.

---

## 8. Prompt engineering realities

- Natural-language prompts are ambiguous on both ends: how users phrase
  input, and how the model interprets/responds. This is a root cause,
  not a minor annoyance — expect silent behavior changes from small
  prompt edits.
- **Version your prompts** like code — track what changed and correlate
  with eval score changes. Treat prompts as versioned assets, not
  throwaway strings in code.
- **Evaluate few-shot examples two ways**: does the model get the
  examples *in* the prompt right, and does it generalize to *new*
  examples not in the prompt (overfitting to the few-shot set is real).
- **Cost/latency asymmetry**: input tokens can process in parallel
  (cheap-ish), output tokens generate sequentially one at a time — output
  length is what actually drives latency up.
- **Prompting vs. finetuning** is a data-availability decision, not a
  taste decision: prompting is fast to start and roughly "worth ~100
  examples"; finetuning pays off once you have hundreds+ of examples and
  need either better performance or lower per-call cost (less
  instruction needed in every prompt).
- **Backward/forward compatibility risk**: swapping to a newer model does
  not guarantee your prompts still work the same way. Unit-test all
  prompts against eval examples before/after any model swap.

**For Nimbus:** directly informs how we should treat the system prompt
and few-shot examples in `agent.py` — track them as versioned strings,
and Phase 3's eval suite doubles as the regression test for any prompt
or model change.

---

## 9. Sampling / generation configuration

- **Temperature** rescales logits before softmax — lower = more
  deterministic/boring, higher = more creative/less coherent.
  `temperature=0` (effectively argmax) is standard for tasks needing
  consistency (e.g. Nimbus's decision-making calls); ~0.7 is a common
  default for more creative/free-text generation.
- **Top-k / top-p (nucleus)** limit the sampling pool to the k most
  likely tokens, or the smallest set whose cumulative probability exceeds
  p — top-p adapts pool size to context, which is usually preferable to
  a fixed k.
- **Test-time compute (best-of-N)**: sample multiple outputs, pick the
  best by average log-probability, a reward/verifier model, or a
  task-specific heuristic (e.g. "shortest valid SQL query"). Effective
  but roughly linear in cost — 2 samples ≈ 2x cost.
- **Structured outputs**: prompting for JSON is the easiest but least
  reliable method; constrained/grammar-based sampling and finetuning are
  progressively more reliable but more engineering effort. Always
  validate structured output against a real schema before trusting it —
  "the API says JSON mode" is not a correctness guarantee (it guarantees
  valid JSON, not valid *content*).

**For Nimbus:** the agent's decision-making call (which `AgentDecision` to
take) should run at low/zero temperature for consistency; any
user-facing free-text generation can run warmer. This is a concrete
config choice to make explicit in `agent.py`, not leave at a library
default.

---

## 10. Common pitfalls (a checklist to run Nimbus against)

1. **Don't use gen AI where a simpler solution works.** Before adding an
   LLM step, ask: would a rule, a lookup table, or basic logic solve this
   as well or better? (e.g. Nimbus's plan-lookup doesn't need an LLM at
   all — it's a straight DB read.)
2. **"Bad AI" vs "bad product"** — most of Nimbus's early friction will
   likely be UX (does the user know what to type/ask?), not model
   quality. Don't reflexively blame the model for a product problem.
3. **Don't start complex.** Don't reach for an agent framework, a vector
   DB, finetuning, or semantic caching before proving the simpler version
   doesn't work. This directly validates Nimbus's phase ordering.
4. **Don't over-index on early demo success.** Real case studies: 1
   month to 80% good, 4+ more months to 95%; "0 to 80% took as long as 80
   to 90%." Budget for this curve explicitly instead of assuming demo
   velocity continues.
5. **Never rely solely on an AI judge for evals.** Human eval (even just
   30–1000 examples/day) is necessary to validate that your AI judges
   are still correlated with real quality — AI judges drift and need
   their own evaluation.
6. **Have a strategy for what use cases to build, don't crowdsource
   them.** Directly validates Nimbus's single bounded use case (telecom
   support) instead of a grab-bag of unrelated demos.

**For Nimbus:** re-check this list at the start of every phase kickoff —
it's cheap insurance against the most commonly repeated mistakes in the
industry, per the source material.

---

---
---

# Part 2 — LLM Engineer's Handbook (Iusztin & Labonne)

Source: synthesized from the publicly available companion material for
**"LLM Engineer's Handbook"** by Paul Iusztin and Maxime Labonne (Packt,
2024) — again, my own summary, not copied text. The book's authors
maintain a fully open-source reference implementation and a free
12-lesson course ("LLM Twin") that mirrors the book's architecture
chapter-for-chapter, which is what this section is grounded in:

- [LLM-Engineers-Handbook GitHub repo](https://github.com/PacktPublishing/LLM-Engineers-Handbook) — the book's official, actively-maintained code
- [LLM Twin course, Lesson 1: An End-to-End Framework for Production-Ready LLM Systems](https://medium.com/decodingai/an-end-to-end-framework-for-production-ready-llm-systems-by-building-your-llm-twin-2cc6bb01141f) — the 3-pipeline/FTI architecture explained in depth
- [LLM Twin course, Lesson 8: The Engineer's Framework for LLM & RAG Evaluation](https://medium.com/decodingai/the-engineers-framework-for-llm-rag-evaluation-59897381c326)
- [Maxime Labonne — A Beginner's Guide to LLM Fine-Tuning](https://mlabonne.github.io/blog/posts/A_Beginners_Guide_to_LLM_Finetuning.html)
- [Maxime Labonne — Decoding Strategies in Large Language Models](https://mlabonne.github.io/blog/posts/2023-06-07-Decoding_strategies.html)

Where this section overlaps with Part 1 (Chip Huyen), treat them as two
independent industry sources converging on the same conclusion — that's
a signal the practice is genuinely load-bearing, not just one author's
opinion.

## 1. The 3-pipeline (FTI) architecture

The book's central architectural pattern, credited to Jim Dowling
(Hopsworks): split any ML/LLM system into three independently
deployable, independently scalable components with a strict, one-way
data contract between them:

1. **Feature pipeline** — turns raw data into processed features (for
   Nimbus: cleaned/chunked/embedded knowledge-base content), writes to a
   **feature store** (for Nimbus: the vector DB / Postgres tables). Only
   this pipeline is allowed to write there.
2. **Training pipeline** — reads a specific *version* of features from
   the feature store, produces model weights, writes to a **model
   registry**. Only this pipeline writes there.
3. **Inference pipeline** — reads a specific version of features *and* a
   specific version of the model, serves predictions to a client. It
   never writes to either store.

The value isn't the diagram — it's the enforced boundary: every
component can be deployed, scaled, and owned independently, and swapping
an implementation behind any one of the three boundaries can't break the
other two. This is explicitly presented as the fix for the common
failure mode where a prototype becomes "a massive monolith that is
extremely hard to refactor from offline to online."

**For Nimbus:** Nimbus doesn't fine-tune a model (no training pipeline
needed yet), but the feature/inference split still applies directly:
anything that populates the knowledge base or account/billing lookup
data (Phase 2) is a "feature pipeline" concern and should never be
mixed into `agent.py`'s request-handling code path (the "inference
pipeline"). Keep that boundary even though today both might run in the
same FastAPI process — it's what makes it possible to later move
ingestion to a real background job without touching request handling.

## 2. Domain-Driven Design layering

The reference repo enforces a strict import direction across four
layers: `infrastructure -> model -> application -> domain`. In practice:
- `domain/`: plain data structures and core business rules, no
  framework/library imports allowed.
- `application/`: business logic, orchestration, RAG implementation —
  depends on domain, not the other way around.
- `model/`: training/inference-specific code.
- `infrastructure/`: all external service integration (DB clients, cloud
  SDKs, the web framework itself) — the only layer allowed to know about
  Postgres, Qdrant, AWS, FastAPI, etc.

The rule of thumb: your core decision logic should never import a
database driver or an HTTP framework directly.

**For Nimbus:** this directly validates the existing `app/agent/`,
`app/models/`, `app/db/` separation. Concretely: `agent.py`'s decision
logic should depend on `Tool`/`ToolResult` interfaces (domain-ish) rather
than importing `psycopg2`/SQLAlchemy sessions directly — the actual DB
access belongs inside the individual tool implementations
(`tools/lookup_account.py` etc.), which act as the "infrastructure" layer
for the agent.

## 3. Data pipelines: CDC and streaming for freshness

For keeping a source database and a derived store (e.g. a vector DB) in
sync, the recommended pattern is **Change Data Capture (CDC)**: a
watcher listens for CRUD events on the source DB and pushes a message to
a queue; a separate streaming pipeline consumes that queue and updates
the derived store. This avoids periodic full-diff batch jobs (slow,
doesn't scale) and keeps the two stores continuously synchronized rather
than "as of the last batch run."

**For Nimbus:** overkill for Phase 1-2 at our scale (a single knowledge
base, low write frequency). Worth revisiting only if/when the knowledge
base gets edited frequently enough that "stale until the next batch job"
becomes a real user-facing problem — note it here so we don't reach for
it prematurely (this echoes the "don't start complex" pitfall from Part
1, section 10).

## 4. Fine-tuning: practical mechanics (for when/if Nimbus needs it)

Nimbus's current plan uses a general-purpose hosted model, not a
fine-tuned one — but if a future phase needs a cheaper or more
specialized model, this is the concrete toolbox described:

- **QLoRA** is the default cost-effective fine-tuning method: load the
  base model in 4-bit precision, train small low-rank adapter matrices
  instead of the full weight matrices. Key hyperparameters to know, not
  just copy: `lora_r` (adapter rank — bigger = more capacity/more VRAM),
  `lora_alpha` (scaling factor, commonly ~2x `lora_r`), `lora_dropout`.
- **Gradient checkpointing** trades ~20% more training time for
  significantly lower VRAM use — recompute activations during the
  backward pass instead of storing them.
- **Sample packing** batches multiple short training examples together
  to minimize padding waste — meaningfully reduces training steps needed
  for the same dataset.
- **Dataset format matters and should be picked deliberately**: Alpaca-style
  (`{"instruction", "input", "output"}`) for single-turn instruction
  tuning vs. ShareGPT-style (`{"conversations": [...]}`) for multi-turn
  chat — Nimbus's `ChatRequest`/`ChatResponse` schema is effectively
  choosing a format for this same reason, just for inference rather than
  training.
- Tooling landscape: Axolotl and Unsloth are the two dominant
  config-driven fine-tuning wrappers (YAML config in, trained
  adapter out) — prefer them over hand-rolled training loops unless you
  have a specific reason not to, same "don't reinvent infra" logic as
  Part 1's orchestration advice.

**For Nimbus:** not actionable now (no training pipeline planned), but
keep this section as the reference for if/when a phase requires
specializing a model on our own support-ticket data.

## 5. The MLOps trio: experiment tracker, model registry, prompt monitor

The reference architecture treats these as three distinct, mandatory
tools rather than one blob of "logging":
- **Experiment tracker** (e.g. Comet ML) — records every training run's
  hyperparameters/metrics so runs are comparable.
- **Model registry** (e.g. Hugging Face Hub) — versions trained model
  artifacts with an explicit staging flag (e.g. tag a version
  `accepted` only after both automated eval *and* manual inspection
  pass) before it can reach the inference pipeline. This "gate before
  promote" step is deliberate, not bureaucracy — it's the same principle
  as requiring code review before merge.
- **Prompt monitor** (e.g. Opik) — logs every inference-time
  prompt/response/context tuple in production, separate from the
  training-time experiment tracker, because production traffic has
  different failure modes than training data.

**For Nimbus:** we don't have training runs, but the "gate before
promote" idea applies directly to prompt/config changes — Part 1 already
recommended versioning prompts; this adds the concrete mechanism: track
eval scores per prompt version, and only promote a new system prompt
after it beats the current one on the Phase 3 eval suite, not just on
manual spot-checks.

## 6. Evaluation framework: the concrete metric taxonomy

This is the most directly reusable material for Nimbus's Phase 3. The
book's evaluation framework layers four distinct kinds of signal —
don't rely on just one:

1. **Heuristics** (Levenshtein distance, BLEU, ROUGE) — cheap, fast,
   exact-match-oriented. Explicitly flagged as **usually insufficient
   alone** for GenAI output, since they penalize valid paraphrases and
   reward literal overlap with a reference answer.
2. **Similarity scores** (e.g. BERTScore/embedding similarity) — softer
   than heuristics, tolerant of paraphrasing, still automatic.
3. **LLM-as-judge metrics** for specific, well-defined failure modes,
   each scored 0.0-1.0 with a required written reason (not just a bare
   number — force the judge to justify itself):
   - **Hallucination** — is the answer consistent with the input (and
     context, if provided)?
   - **Moderation** — is the content safe (explicit category checklist:
     violence, hate speech, PII/privacy violations, harassment, etc.)?
   - **Custom business metrics** — e.g. a "Style" judge scored on a
     defined rubric (their example: 1=too formal/academic,
     2=good-but-still-formal, 3=excellent-and-accessible). The lesson
     here: don't just use generic judges — write one custom judge per
     property your product actually needs to get right.
4. **RAG-specific metrics**, which need the *retrieved context* as a
   fourth input alongside (query, output, expected output):
   - **ContextRecall** — does the answer correctly reflect everything
     relevant in the retrieved context?
   - **ContextPrecision** — is the answer free of context-irrelevant
     content, and aligned with what was actually retrieved?

Practical implementation notes worth keeping:
- LLM-judge prompts should use **chain-of-thought** ("analyze, then
  score") and **few-shot examples** (a low/medium/high scoring example
  each) — bare "give me a score" prompts are measurably less reliable.
- Structure the judge's output as strict JSON (`{"score": ..., "reason":
  ...}`) and validate it — same "never trust raw model output, validate
  into a schema" principle already in Nimbus's `docs/PHASE-1-TODOS.md`.
- Run comparisons, not just absolute scores: evaluate "with RAG" vs
  "without RAG", or "new prompt" vs "old prompt", side by side on the
  same eval set — an isolated score is much less actionable than a
  before/after delta.

**For Nimbus:** this is a ready-made checklist for `nimbus/evals/`.
Concretely, Phase 3's golden-case suite should score at minimum:
Hallucination (does the agent's answer match the account/billing data
the tools actually returned?), Moderation, a custom "Escalation
correctness" judge (did it choose ESCALATE/REQUEST_APPROVAL when it
should have?), and — once Phase 2's RAG is in place — ContextRecall/
ContextPrecision against the retrieved knowledge-base chunks.

## 7. Decoding strategies (mechanics behind Part 1's sampling section)

Complements Part 1 section 9 with the underlying mechanics:
- **Greedy search** — always take the single most probable next token.
  Fast, deterministic, but "short-sighted": a locally-best token can lead
  to a globally worse sentence (their concrete example: greedy search
  picks a token sequence with a worse overall score than beam search
  finds).
- **Beam search** — track the top-`n` candidate sequences at each step
  (not just the top token), normalize by sequence length to avoid biasing
  toward shorter outputs, and keep the best-scoring full sequence at the
  end. Strictly better sequence quality than greedy, at higher compute
  cost (roughly `n`x).
- **Top-k / nucleus (top-p) sampling** — introduce controlled randomness
  by sampling from a restricted candidate pool instead of always taking
  the argmax; this is what makes output feel natural/varied instead of
  repetitive, at the cost of determinism.
- **Temperature** divides logits before the softmax — this is the lever
  that controls how "sharp" (low temp, close to greedy) vs. "flat" (high
  temp, close to uniform-random) that candidate pool's probabilities are.

**For Nimbus:** reinforces the existing decision — decision-making calls
(`AgentDecision` selection) should be low/zero temperature and
effectively greedy for reproducibility, while any user-facing free-text
generation can use nucleus sampling at a moderate temperature for
naturalness. If we ever add multi-candidate response generation (e.g.
generate 2 candidate replies and pick the better one), beam search /
best-of-N is the mechanism, at a roughly linear cost multiplier.

## 8. Engineering hygiene from the reference repo

Independent of the LLM-specific content, the companion repo's own setup
is a good checklist for any production-track repo:
- **Pre-commit hooks** running linting/formatting (ruff) on every
  commit, not just in CI — catches issues before they're even pushed.
- **Credential leak scanning** (gitleaks) as a dedicated, separate check
  from linting — treat "did we commit a secret" as its own category of
  bug, not a subset of code style.
- **Pinned, reproducible environments** (exact Python version via
  `.python-version`/pyenv, locked dependencies via Poetry's lockfile) —
  the same motivation as Nimbus's isolated per-project venv.
- **CI/CD gated by tests**, deploying only after the test suite and
  linting both pass.

**For Nimbus:** we already have the isolated venv and a passing test
suite; worth adding a pre-commit hook (ruff/black + a basic secret
scanner) before Phase 2, rather than relying purely on manual review to
catch a leaked `OPENAI_API_KEY` or similar.

---

## How to use this file

- Reference this doc during code review — `docs/code-reviews/phase-N-review.md`
  should call out where Nimbus does/doesn't follow a relevant section here.
- If a new blog post or edition update from the same source adds
  something relevant (e.g. memory systems — explicitly flagged by the
  author as a "future post" beyond what's summarized here), append a new
  section rather than starting a new file.
- Part 1 (Chip Huyen) and Part 2 (Iusztin & Labonne) are independent
  sources — when they agree (e.g. "start simple before reaching for an
  orchestration framework/vector DB/fine-tuning"), treat that as a
  stronger signal than either alone.
