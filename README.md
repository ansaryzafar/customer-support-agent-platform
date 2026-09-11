# Nimbus

### Enterprise Customer Support AI Agent

Nimbus is a production-oriented conversational AI agent designed
to resolve complex customer-support tasks while maintaining
bounded autonomy, grounded responses, observable execution,
human approval controls and reliable failure recovery.

[Architecture] [Demo] [Evaluation] [Security] [API]

Portfolio project built alongside `../EXECUTION-PLAN.md`. A bounded,
tool-using customer support agent for a telecom/subscription domain, with
an operator console, evals, and guardrails layered in over successive
phases.

## Stack
- Backend: FastAPI + Postgres + Redis (Python)
- Frontend: React + TypeScript (Vite)
- Infra: Docker Compose (local Postgres + Redis)

## Getting started

1. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`.
2. Start infra: `docker compose up -d`
3. Backend:
   ```
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
4. Frontend:
   ```
   cd frontend
   npm install
   npm run dev
   ```

## Project layout
- `backend/` — FastAPI app, agent loop, tools, DB.
- `frontend/` — chat UI + (later) operator console.
- `evals/` — golden test cases + eval runner (Phase 3+).
- `docs/` — scope doc, phase TODOs, code review files.

## Where you are
Check `docs/PHASE-1-TODOS.md` for the current phase's tasks.
