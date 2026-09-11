"""
TODO: Implement the core single-agent loop.

This is the heart of Phase 1. Pseudocode to guide you:

    def run_agent_turn(conversation_id: str, message: str) -> ChatResponse:
        1. Load recent conversation history (start with in-memory/dict,
           swap to Redis/Postgres once it works).
        2. Build the prompt: system policy + history + new message +
           tool definitions (name, description, JSON schema per tool).
        3. Call the LLM asking for a structured response that includes:
             - decision: one of AgentDecision
             - either a direct answer, a clarifying question, or a
               tool_name + tool_arguments to call
        4. Validate the model's output against your Pydantic schema.
             - If it doesn't validate: retry once with an error message
               fed back to the model. If it still fails: force ESCALATE.
        5. If decision == EXECUTE_SAFE_TOOL:
             - look up the tool by name in a registry (see tools/base.py)
             - validate arguments against the tool's own input schema
             - call it with a timeout + try/except -> on failure, ESCALATE
             - feed the tool result back to the model for a final answer
        6. Persist the turn (message, decision, tool calls, latency) —
           you'll reuse this in Phase 3 for tracing/evals.
        7. Return the ChatResponse.

Industry best-practice tips:
    - The model NEVER calls a tool directly. Your code parses structured
      output, then YOUR code decides whether/how to call the tool. This is
      the core safety boundary — keep it that way even under pressure to
      "just let the model call the function directly."
    - Put a hard step limit (e.g. max 4 tool calls per turn) to prevent
      infinite loops from a confused agent.
    - Treat every LLM call as something that can time out, return garbage,
      or fail — this loop should never raise an unhandled exception up to
      the API layer.
"""
