"""
Looks up a customer's billing details (recent invoices, balance, due date)
by customer_id, from a hardcoded in-memory dataset.
"""
class LookupBillingTool:
    name: str = "lookup_billing"
    description: str = "Look up a customer's billing information by customer_id."
    requires_approval: bool = False
    
    def input_schema(self):
        from pydantic import BaseModel
        
        class LookupBillingInput(BaseModel):
            customer_id: str
            
        return LookupBillingInput
    
    def run(self, **kwargs):
        from pydantic import ValidationError
        from app.agent.tools.base import ToolResult
        
        LookupBillingInput = self.input_schema()
        
        try:
            input_data = LookupBillingInput(**kwargs)
        except ValidationError as e:
            return ToolResult(success=False, error=str(e))

        # Hardcoded in-memory fake dataset
        fake_billing = {
            "cust_001": {"recent_invoices": ["inv_001", "inv_002"], "balance": 100.0, "due_date": "2024-06-30"},
            "cust_002": {"recent_invoices": ["inv_003"], "balance": 50.0, "due_date": "2024-07-15"},
            # Add more fake billing records as needed
        }

        billing_info = fake_billing.get(input_data.customer_id)
        if not billing_info:
            return ToolResult(success=False, error="Customer not found.")

        return ToolResult(success=True, data=billing_info)