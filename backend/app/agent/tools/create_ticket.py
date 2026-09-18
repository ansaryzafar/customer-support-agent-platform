"""
Creates a support ticket for a customer.
"""
class CreateTicketTool:
    name: str = "create_ticket"
    description: str = "Create a support ticket for a customer."
    requires_approval: bool = False  # Low risk, reversible action.
    
    def input_schema(self):
        from pydantic import BaseModel
        
        class CreateTicketInput(BaseModel):
            customer_id: str
            subject: str
        return CreateTicketInput
    
    def run(self, **kwargs):
        from pydantic import ValidationError
        from app.agent.tools.base import ToolResult
        
        CreateTicketInput = self.input_schema()
        
        try:
            input_data = CreateTicketInput(**kwargs)
        except ValidationError as e:
            return ToolResult(success=False, error=str(e))
        
        # In-memory list to store tickets (for demonstration purposes)
        if not hasattr(self, "_tickets"):
            self._tickets = []
            
        # Create a new ticket
        new_ticket = {
            "id": len(self._tickets) + 1, # Simple auto-incrementing ID
            "customer_id": input_data.customer_id,
            "subject": input_data.subject,
            "status": "open"
        }
        self._tickets.append(new_ticket)
        return ToolResult(success=True, data=new_ticket)
        