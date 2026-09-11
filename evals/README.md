# Evals

Golden test conversations live in `golden_cases/` as JSON files. Each case
should define: input messages, expected `decision`, and expected tool
calls (if any). `run_evals.py` (TODO, Phase 3) will replay these against
the live agent and score tool-selection accuracy + groundedness.

Not needed until Phase 3 — safe to ignore for now.
