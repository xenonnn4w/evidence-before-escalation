# Design review — why v0.2 is stronger

23 October 2026. This is a critique and revision of the plan, not evidence from completed experiments. v0.2 supersedes the earlier two-condition design.

## Central claim we could actually test

On a fixed set of bounded research-report tasks, changing the organization of identical evidence changes which errors an open model prioritizes for review at a fixed review-count budget.

This is narrower and more interpretable than “evidence improves oversight.” Neither a large model nor a positive result automatically establishes useful human oversight. An unchanged or worse queue is an informative finding.

## Changes and their purpose

| Weakness in v0.1 | Revision | What it enables |
| --- | --- | --- |
| Evidence versus no evidence may have an obvious answer | Primary comparison gives both conditions identical evidence records | Tests organization, with evidence availability retained as a secondary diagnostic |
| Test cases use the same task variants as development | Reserve one variant per family; show two test strata | Tests a limited, explicit form of transfer |
| LLM compared mainly against random ranking | Add executable checking, uncertainty and oracle references | Shows when a simpler method is sufficient and where the model falls short |
| Artificial 50% errors can make review precision misleading | Prespecified 10% and 25% error-prevalence simulations | Shows dependence on prevalence without inventing natural error rates |
| A single favorable number could dominate the write-up | Fix primary comparison; report natural errors, holdouts and failures separately | Prevents the largest attractive result from replacing the planned question |
| More models could expand cost before design improves | Keep 1.7B/4B core; optional 8B only after core archive | Prioritizes controls and interpretable results over a large model list |

## Example of the manipulation

Suppose a report asserts that candidate B was selected using validation scores and that its test accuracy was 0.89. Records include the candidate validation scores, candidate test scores, actual selection event and task policy. The selection event says test scores were used.

U presents the original ledger. S presents those exact records grouped by the report schema: candidate selection records together, then reported test-metric records. Neither version inserts “leakage,” “wrong,” a computed verdict or a highlighted decisive line. Both preserve source IDs encoding logical event order. An independent checker evaluates whether the report accurately describes the selection process.

The report may accurately admit that selection violated policy; that report must be labeled correct. This prevents conflating bad research practice with inaccurate reporting.

## Strongest objections and required responses

**“The deterministic checker can solve the whole benchmark.”** Correct: these intentionally checkable tasks may require no LLM in production. The scientific purpose is to diagnose evidence use under controlled conditions and build a verified substrate for later oversight research. Report the checker's accuracy, abstentions and runtime. Do not market this as a superior replacement for executable checks. Generalization to ambiguous research claims remains untested.

**“Ordering is just a prompt engineering trick.”** It is a deliberately narrow intervention, motivated by whether a review system exposes relevant evidence accessibly. Its value is a paired measurement across task variants and error types, not inventing a new algorithm. Do not infer cognitive or interface effects on humans from an LLM experiment.

**“You are collecting synthetic mistakes, not authentic research failures.”** Keep controlled errors and one-shot natural model reports separate. Describe both honestly. Natural errors are still from constrained reporting tasks and do not establish the behavior of autonomous research agents.

**“The same model family generates and audits the reports.”** Yes. Shared failure modes are a limitation; compare self-model auditing with another size, but do not call this independent cross-family replication. A separate-family replication is a future extension, not necessary for the initial claim.

**“The sample is too small.”** Report intervals and denominators, plus illustrative pre-test precision simulations. No powered-study guarantee. If natural errors are rare, report the rare-error observation and descriptive examples; do not increase sampling selectively to find a publishable effect.

**“The two evidence views might accidentally disclose different facts.”** Require exact record-multiset equality, label-blind sorting, and stored prompt hashes. Record how many examples actually change order. Original ledgers should be plausible logs, not adversarially shuffled to manufacture an improvement. If most U/S cases are identical on development data, redesign the representation before freeze and document why; do not select test cases based on observed treatment effects.

## What changes our conclusion?

- S helps on controlled and natural reports, including held-out variants: evidence for robustness within this bounded setting; next test the queues with human reviewers.
- S helps only on planted errors: construction-dependent result; weaken transfer claims.
- S helps only 4B: possible capability interaction; report uncertainty rather than infer a universal threshold.
- S has no benefit: ordering alone may be insufficient; larger claims about “evidence-first oversight” are unsupported.
- S hurts: grouping may disrupt useful chronology or promote superficial matching; inspect paired failures.
- Checker dominates all LLM policies: recommend executable checks for these tasks and study where ambiguity actually requires models or people next.

## Connection to prior research

This personal project investigates queue construction and evidence presentation using cases whose outcomes can be checked independently. It studies one part of allocating scarce review attention; it does not establish human complementarity or the effectiveness of an end-to-end oversight system.

[Xu et al.](https://arxiv.org/abs/2605.04070) identify routing and correction of wrong AI suggestions as bottlenecks in their studied tasks. That motivates testing uncertainty rather than assuming it works. [Bowkis et al.](https://arxiv.org/abs/2605.06390) emphasize difficulties supervising fuzzy research tasks. Our checkable benchmark is a preliminary diagnostic and does not resolve that broader problem.

## Completion boundary

A strong first deliverable is a reproducible, honestly scoped experiment with checked labels, a justified control, negative examples, uncertainty, and a clear next hypothesis. It need not show improvement or use the largest available model. The implementation is now CPU-validated. Pretrained-model inference and scientific reporting remain pending.
