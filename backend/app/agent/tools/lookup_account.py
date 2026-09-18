"""
Looks up a customer's account details (plan, status, signup date) by
customer_id, from a hardcoded in-memory dataset.
"""

from pydantic import BaseModel, ValidationError
from app.agent.tools.base import ToolResult


class LookupAccountInput(BaseModel):
    customer_id: str


class LookupAccountTool:
    name = "lookup_account"
    description = "Lookup a customer's account information by customer_id."
    requires_approval = False

    def input_schema(self):
        return LookupAccountInput

    def run(self, **kwargs):
        try:
            input_data = LookupAccountInput(**kwargs)
        except ValidationError as e:
            return ToolResult(success=False, error=str(e))

        # Hardcoded in-memory fake dataset
        fake_customers = {
            "cust_001": {"plan_name": "Pro", "status": "active", "signup_date": "2022-01-15"},
            "cust_002": {"plan_name": "Basic", "status": "inactive", "signup_date": "2021-11-20"},
            # Add more fake customers as needed
        }

        customer_info = fake_customers.get(input_data.customer_id)
        if not customer_info:
            return ToolResult(success=False, error="Customer not found.")

        return ToolResult(success=True, data=customer_info)