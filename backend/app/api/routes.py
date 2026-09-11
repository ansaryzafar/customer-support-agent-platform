"""
TODO: Implement the POST /chat endpoint.

    from fastapi import APIRouter
    router = APIRouter()

    @router.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        return run_agent_turn(request.conversation_id, request.message)

Best practice: keep this route a thin adapter — all real logic lives in
app/agent/agent.py so it's testable without spinning up FastAPI.
"""
