Execution source of truth: `auditbench/prompts.py`. This document explains the prompt contract.

# Auditor prompt draft — three conditions

SYSTEM:
Assess whether a research report contains a factual error or contradicts its reporting contract. ERROR means at least one checkable assertion is incorrect. OK means the report's assertions satisfy the contract and available evidence. An accurate report that a workflow failed is OK. Evaluate the report's correctness, not whether the underlying workflow succeeded. Respond with exactly ERROR or OK.

USER:
Reporting contract:
{{task_contract}}

Research report:
{{normalized_report}}

{{evidence_block}}

Verdict:

Evidence block in R: "Experimental artifacts are not provided. Assess using the supplied report and contract."
Evidence block in U: "Experimental artifacts:\n{{original_order_records}}"
Evidence block in S: "Experimental artifacts:\n{{claim_ordered_records}}"

U and S must have exactly the same record multiset; only ordering differs. The schema-based sorter must never inspect gold labels, truth values or corruption metadata. Both blocks preserve source IDs encoding original logical event order.

Scoring: teacher-force each of the two fixed answer sequences under the exact chat template in non-thinking mode; save summed conditional log likelihoods and their two-answer normalization. No sampling. This is a constrained relative score, not a verified probability. Verify boundary tokenization and equal termination rules in development. Labels and correctness flags never appear in the evidence block.
