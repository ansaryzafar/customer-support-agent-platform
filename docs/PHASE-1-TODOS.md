# Phase 1 — Your TODOs (Single-Agent + Tools)

Work through these in order. Each stub file has inline hints — this file
is the map that ties them together. Ask for a review once you've got the
Definition of Done working end-to-end.

## Order of implementation

1. `backend/app/models/schemas.py` — `ChatRequest` / `ChatResponse`.
2. `backend/app/agent/decisions.py` — `AgentDecision` enum.
3. `backend/app/agent/tools/base.py` — `Tool` contract + `ToolResult`.
4. `backend/app/agent/tools/lookup_account.py`,
   `lookup_billing.py`, `create_ticket.py` — concrete tools (fake data is fine).
5. `backend/app/agent/agent.py` — the core loop. This is the big one.
6. `backend/app/api/routes.py` — wire the `/chat` endpoint.
7. `backend/app/main.py` — include the router (one-line TODO already marked).
8. Frontend: wire the chat UI (`frontend/src/App.tsx`) to `POST /api/chat`.

## Definition of Done (copied from EXECUTION-PLAN.md)
You can have a multi-turn conversation where the agent either answers,
asks a clarifying question, calls a tool, or escalates — and you can
point to the exact code path that made that decision.

## Industry best practices to apply here
- **Typed boundary between model output and system action.** The LLM
  proposes; your code disposes. Never directly execute something the
  model wrote — always go through your Pydantic-validated `AgentDecision`
  and tool schemas.
- **Fail closed, not open.** If output doesn't parse, or a tool errors,
  default to `ESCALATE` — never silently proceed as if nothing happened.
- **Bounded loops.** Hard cap on tool-call iterations per turn (e.g. 4).
  Infinite agent loops are a real production incident category.
- **Logging from day one.** Even a basic logger call per decision now
  saves you rebuilding tracing later (Phase 3 builds directly on this).
- **Testability.** Keep `run_agent_turn()` callable without FastAPI/HTTP
  so you can unit test it directly and reuse it in the eval runner later.

## Things to think about (bring these to the review)
- What happens if the same tool is called twice in one turn?
- How do you decide the line between `ANSWER` and `ESCALATE` for an
  ambiguous question?
- Where would you add a timeout around the LLM call itself?

## When you're done
Tell me it's ready — I'll write `docs/code-reviews/phase-1-review.md`
with specific, line-level feedback.
