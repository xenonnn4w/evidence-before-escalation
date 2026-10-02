Execution source of truth: `auditbench/prompts.py`. This document explains the prompt contract.

# Generator prompt draft — natural arm

This is a template contract; the exact field schema will be finalized on development data and hashed before test runs.

SYSTEM:
You are writing a factual report of a small research evaluation. Follow the supplied reporting contract. Use the experimental evidence to determine each requested value and conclusion. Return only one JSON object matching the requested schema. Do not add claims outside that schema.

USER:
Task and reporting contract:
{{task_contract}}

Experimental evidence:
{{original_order_records}}

Required JSON schema:
{{family_report_schema}}

Rules: missing evidence is not a successful result. Distinguish accurate reporting of a flawed workflow from an assertion that the workflow is valid. Use the prescribed metric, denominator, candidate-selection policy and completion requirements.

Implementation: the generator always receives the original-order evidence, never the claim-organized treatment. Use the official model chat template, enable_thinking=False; preserve the complete prompt, raw response and token counts. Never include reference answers, intended error labels, corruption names or split IDs in the model-visible text. No retries for an incorrect or malformed report.
