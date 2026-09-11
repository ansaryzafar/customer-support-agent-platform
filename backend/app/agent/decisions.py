"""
TODO: Define the AgentDecision enum.

This is the single most important type in the system: it is the *only*
vocabulary the agent is allowed to use to take action. Every response the
agent produces must resolve to exactly one of these values.

Required members (see ../../../EXECUTION-PLAN.md Phase 1):
    ANSWER              - agent answers directly, no tool/escalation needed
    ASK_CLARIFICATION   - agent needs more info from the user first
    ESCALATE            - hand off to a human agent
    REQUEST_APPROVAL    - agent wants to take a sensitive action, needs sign-off
    EXECUTE_SAFE_TOOL   - agent calls a tool that doesn't need approval

Hint:
    from enum import Enum

    class AgentDecision(str, Enum):
        ANSWER = "answer"
        ...

Why str, Enum? So it serializes cleanly to JSON and compares equal to
plain strings in tests, while still being a real enum everywhere else.
"""
from enum import Enum

class AgentDecision(str, Enum):
    ANSWER = "answer"
    ASK_CLARIFICATION = "ask_clarification"
    ESCALATE = "escalate"
    REQUEST_APPROVAL = "request_approval"
    EXECUTE_SAFE_TOOL = "execute_safe_tool"
