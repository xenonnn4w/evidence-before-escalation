# Evidence Before Escalation

Status: experiment not run. All result sections below are placeholders.

## Summary
Question; actual models and cases; primary result with counts and uncertainty; main limitation.

## Motivation and relation to prior work
Explain scarce review capacity and the motivation for testing evidence organization. Connect the question to cited prior research, and state the narrow scope and provisional novelty.

## Method
Record task families, label definitions, splits, generator settings, immutable revisions, score calculation, review policies, primary contrast and actual hardware. Report unassessable outputs and protocol deviations.

## Q1 — Error prioritization
Table: arm, model, condition, policy, N, errors, review count, errors selected, recall, correct escalations. Figure: recall/budget with oracle ceiling and random spread.

## Q2 — Evidence organization
Primary paired difference at 20% review with bootstrap interval. Show one success and one failure with traceable case IDs. Verify identical evidence records across U/S. Keep the secondary U/R information-availability comparison separate.

## Q3 — Auditor size
Paired comparison on identical reports. Include latency/memory and separate any optional 8B extension.

## Q4 — Risk versus uncertainty
Compare policies on the same scored examples; discuss confident misses without describing the relative score as calibrated probability.

## Q5 — Residual errors
Counts by family, subtype and held-out-variant/new-instance stratum, including errors outside the review queue. No cherry-picked examples as prevalence estimates.

## Q6 — Natural versus controlled errors
Natural correctness/schema counts; transfer comparison; explain if the natural-error sample is too small for more than descriptive evidence.

## Baselines and robustness
Report executable-checker coverage, accuracy, runtime and abstentions. Include the 10%/25% prevalence simulations and actual queue counts. State clearly if deterministic checking already solves the task.

## Q7 — Human follow-up
Propose testing queue usefulness with real reviewers. Do not claim reduced cognitive load, reviewer time saved or improved human decisions from this experiment.

## Limitations
Synthetic constrained tasks; limited within-family task-variant holdout; one model family and one generator; induced-error prevalence; shared generator/auditor family; single generator draw; unavailable evidence in R; finite sample; oracle review assumption.

## Reproduction
Exact run ID, code/config/data hashes, lockfile, commands, artifact paths, actual GPU, runtime and cost. Distinguish preparation date from execution date.

## Personal interpretation
The user's own explanation: what surprised me, which belief changed, what I would test next, what I cannot conclude.
