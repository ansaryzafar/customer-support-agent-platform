# Nimbus — Scope (Draft)

> Refine this yourself as part of Phase 0 — this is a starting draft, not
> a final spec. Edit freely.

## Who is the user?
A telecom/subscription company's customers, chatting via a support widget.

## What can the agent do?
- Answer questions about plans, pricing, and policies (grounded in a
  knowledge base — Phase 2).
- Look up a customer's account and billing status.
- Create a support ticket.
- Troubleshoot common device/connectivity issues via a decision tree.

## What is explicitly out of scope (v1)?
- Processing payments.
- Cancelling a subscription without human approval (Phase 4: this becomes
  a `requires_approval` tool).
- Any action affecting a different customer than the one in conversation.

## What does "escalate to human" mean?
The conversation is flagged in the operator console with full context;
the customer is told a human will follow up. No tool with side effects
runs after an escalation without approval.

## Definition of "done" for v1
A customer can ask a policy question and get a grounded answer, look up
their own billing status, and create a ticket — all without a human,
while every sensitive action requires approval and every decision is
logged for evals.
