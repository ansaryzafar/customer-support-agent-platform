"""
Tool contract shared by every agent tool.

Each tool implements this Protocol so the agent loop can validate input,
invoke the tool safely, and receive a typed result without needing to know
the tool's internal implementation.
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