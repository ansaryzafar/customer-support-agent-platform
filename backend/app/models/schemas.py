"""
Pydantic request/response schemas for the chat API and agent decisions.

This file is intentionally left for you to implement — structured output
design is one of the core skills this phase is meant to build.

TODO 1: Define `ChatRequest`
    - conversation_id: str
    - message: str
    - customer_id: str | None = None

TODO 2: Define `ChatResponse`
    - conversation_id: str
    - decision: <the AgentDecision enum from app/agent/decisions.py>
    - message: str                # what to show the user
    - tool_calls: list[str] = []  # names of tools invoked this turn
    - citations: list[str] = []  # doc/chunk ids used to ground the answer (Phase 2)

Hint / industry practice:
    - Never let the agent return a raw free-text "action" — always validate
      into a typed enum/schema before the backend acts on it. If the model's
      output doesn't parse, treat that as a failure case (retry once, then
      escalate) rather than guessing what it meant.
    - Keep these schemas the single source of truth for the API contract —
      the frontend TS types should mirror this shape.
"""

# TODO: from enum import Enum
# TODO: from pydantic import BaseModel
# TODO: implement ChatRequest, ChatResponse here
from enum import Enum
from pydantic import BaseModel  
from app.agent.decisions import AgentDecision

class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    customer_id: str | None = None

class ChatResponse(BaseModel):
    conversation_id: str
    decision: AgentDecision
    message: str
    tool_calls: list[str] = []
    citations: list[str] = []