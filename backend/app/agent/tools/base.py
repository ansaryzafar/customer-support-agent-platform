"""
TODO: Define the Tool contract every tool must implement.

Hint (Protocol-based, easy to test/mock):

    from typing import Protocol
    from pydantic import BaseModel

    class ToolResult(BaseModel):
        success: bool
        data: dict | None = None
        error: str | None = None

    class Tool(Protocol):
        name: str
        description: str          # shown to the LLM so it knows when to use it
        requires_approval: bool   # Phase 4 will read this flag

        def input_schema(self) -> type[BaseModel]: ...
        def run(self, **kwargs) -> ToolResult: ...

Best practice:
    - Validate `kwargs` against `input_schema()` BEFORE running any logic.
    - A tool should never throw — catch internally and return
      ToolResult(success=False, error=...). The agent loop should only ever
      deal with a well-formed ToolResult.
    - `requires_approval` belongs on the tool, not scattered in if/else
      logic in the agent loop — Phase 4 (guardrails) depends on this.
"""
from typing import Protocol
from pydantic import BaseModel

class ToolResult(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
    
class Tool(Protocol):
    name: str
    description: str         # shown to the LLM so it knows when to use it
    requires_approval: bool # Phase 4 will read this flag
    
    def input_schema(self) -> type[BaseModel]:
        ...
    def run(self, **kwargs) -> ToolResult:
        ... 