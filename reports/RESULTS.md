# Evidence Before Escalation

## Does organizing identical evidence improve error prioritization?

**Completed open-model experiment.** GPU inference completed on 24 October 2026; report assembled on 25 October 2026. The test comprises 150 base cases, 450 reports, and 2,700 auditor scores. Inputs are synthetic; report generation and auditing used real released model weights.

At a 20% review budget, organizing evidence by claim **did not improve the primary endpoint**. Qwen3-4B selected 41 of 150 controlled errors under either layout (27.3% error recall). The paired change was **0.0 percentage points**, with a 95% clustered bootstrap interval of **−4.0 to +3.3 points**. This is inconclusive about small effects, rather than evidence that the layouts are equivalent. Exploratory effects differed by auditor and report arm.

![Paired organization effects](../results/test/analysis/fig02_organization_effect.png)

## Question and scope

The study tests the routing step before hypothetical human review: which reports should receive limited attention? It compares the same evidence in original order (U) and deterministically sorted by claim field/source identifier (S). Both contain the same records; S adds no summaries, answers, or gold labels. Report-only scoring (R) is an information-availability diagnostic.

This is adjacent to human-centered oversight research because it examines allocation of scarce review capacity. It does not test human decision-making, cognitive load, review time, autonomous research agents, or a complete oversight system. A useful follow-up would measure how real reviewers use the selected reports and evidence.

## Design

The seeded dataset has three bounded families: metric reporting from classification confusion counts, checking logged candidate selection against a validation-only policy, and checking completeness/support in an evaluation ledger. No classifiers were trained: their labels, predictions, selection events, and ledger values are synthetic.

There are 180 base cases: 30 development and 150 test. The test has 90 new instances and 60 held-out variants within the same three families. Every test case has one generated natural report, one canonical correct report, and one canonical report with one controlled corruption. The controlled arm therefore has 300 reports and exactly 150 errors by design. The natural arm has 150 reports; its errors were determined after generation. The 450 report records are not 450 independent tasks.

Qwen3-4B generated reports with thinking disabled, BF16, temperature 0.7, top-p 0.8, top-k 20, a 384-token output limit, and one seeded draw per case. Auditors were Qwen3-1.7B and Qwen3-4B, also nonthinking BF16. The score normalizes conditional likelihoods of the complete `ERROR` and `OK` continuations, including termination. It is a ranking score, not a calibrated probability of error.

Risk queues rank descending error score; uncertainty queues rank by proximity to 0.5. Queue sizes are floor(budget × reports), with deterministic hash tie-breaking. Budgets are 10%, 20%, and 40%. The primary contrast was fixed as S-minus-U risk-queue error recall at 20% for the 4B controlled arm. Intervals use 2,000 paired base-case bootstrap replicates stratified by family and test stratum. All report variants and conditions stay together. Exploratory intervals are not adjusted for multiple comparisons.

An independent checker derives expectations from visible artifacts without accessing saved gold fields. Numerical fields use absolute tolerance 0.005; any incorrect required assertion makes a report incorrect. Schema failures remain a separate unassessable category. No unassessable outputs occurred.

## Results at 20% review

| Auditor | Arm | Queue size | Errors available | U errors selected | S errors selected | U recall | S recall | S−U recall, percentage points (95% interval) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 1.7B | Controlled | 60 | 150 | 31 | 28 | 20.7% | 18.7% | −2.0 [−4.0, +2.0] |
| 1.7B | Natural | 30 | 113 | 23 | 27 | 20.4% | 23.9% | +3.5 [+0.8, +7.3] |
| **4B** | **Controlled, primary** | **60** | **150** | **41** | **41** | **27.3%** | **27.3%** | **0.0 [−4.0, +3.3]** |
| 4B | Natural | 30 | 113 | 30 | 28 | 26.5% | 24.8% | −1.8 [−5.5, 0.0] |

For the primary comparison, both queues contain 19 correct reports and leave 109 errors outside the queue. Equal total recall does not mean they select identical reports. The 4B auditor prioritizes more controlled errors than 1.7B at this budget, but this does not establish a general scaling trend from two sizes in one model family.

For natural reports, U/S queue precision is 76.7%/90.0% for 1.7B and 100.0%/93.3% for 4B. The natural arm's high 75.3% error prevalence makes these precisions easier to attain than in a low-error deployment. The 4B organized uncertainty queue selects 36 controlled and 25 natural errors, compared with 41 and 28 for organized risk ranking. The corresponding 1.7B queues tie at this budget. Other budgets and all conditions are in `metrics.csv`.

The 4B natural-arm AUROC increases from 0.454 (U) to 0.541 (S), even though the top-20% queue loses two errors. Overall ranking and usefulness at a particular queue budget are different measurements.

### Natural error distribution and label audit

Natural reports contain 113 errors, 37 correct reports, and zero schema failures. Error counts by family are metrics 50/50, selection 26/50, and evidence sufficiency 37/50. These are rates for this particular synthetic task generator, prompt, and model setting, not general Qwen reliability estimates.

The unexpectedly poor metric reporting was checked independently from raw labels/predictions for **all 50 test metric cases**, without using the checker or its batch counts. Recomputed expectations and error fields matched every saved label. For example, case `0-010` has 96/128 correct A predictions and 95/128 correct B predictions: accuracy 0.7500 and 0.7422. The natural report instead asserts 0.9444 and 0.9333. See `independent_metric_check.json` for all checks.

Natural reports can have several errors: score_A and score_B are each wrong in 49 reports, and the winner in 14. Error-subtype rows therefore overlap. At 20% global review the 4B auditor leaves every erroneous natural metric report outside the queue under U and S, despite selecting many evidence-sufficiency errors. A pooled result can hide strong family-specific blind spots.

### Traceable queue changes

Illustrations below use the lexicographically first erroneous report entering/leaving each model-arm queue when moving U→S; they are not estimates of prevalence. Selection uses the same score/hash ranking as the main analysis. Complete examples are in `queue_examples.json`.

- `1-012:controlled_incorrect`: added from the review queue under S; erroneous field(s) `policy_compliant`. Error score U=0.060088, S=0.993306.
- `1-011:controlled_incorrect`: lost from the review queue under S; erroneous field(s) `policy_compliant`. Error score U=0.562170, S=0.320795.

### Robustness and baselines

Held-out-variant comparisons build separate queues within each stratum, unlike the pooled primary queue. They test transfer within families, not unseen research domains; the strata also differ in difficulty. Their selected-error counts must not be added and compared directly with the pooled queue.

Prevalence sensitivity reuses controlled scores in 1,000 paired queue draws at nominal 10% and 25% errors, choosing one canonical variant per case. Rounding within strata makes the higher actual prevalence 26%. The plotted 5th–95th percentile ranges are conditional simulation ranges, not confidence intervals from new model experiments. They do not simulate changed natural error content.

The executable checker covers all 300 controlled and all 150 natural reports without abstention. These tasks are fully checkable, so the checker already supplies the ground-truth ranking/oracle ceiling. Its agreement with benchmark labels is an implementation-consistency check, not evidence that an LLM outperforms a practical checker. This benchmark does not justify deploying an LLM instead of available deterministic checks.

## Additional descriptive analyses — 25 October

Three post-hoc diagnostics were added after the primary analysis. They reuse saved scores, preserve the original queues and hash tie-breaking, and introduce no new model inference or confirmatory tests.

- **Figure 8, family prioritization:** At 20% controlled review, the 4B auditor selects 0/50 metric errors, 10/50 selection errors, and 31/50 evidence errors under either layout. This is the composition of the global queue, not separate family budgets. In the natural arm, its queue selects 0/50 metric errors under either layout. The 1.7B auditor instead misses almost all evidence-sufficiency errors.
- **Figure 9, queue overlap:** The 4B controlled queues retain 39 reports and exchange 21 each. Each exchanged set contains eight errors, so their total recall is identical despite different membership. The natural 4B queues retain 21 reports and exchange nine each: nine outgoing errors versus seven incoming errors, explaining the loss of two.
- **Figure 10, score discrimination:** ROC curves show overall ranking across thresholds. The natural 4B AUROC improvement coexists with worse top-20% recall. Curves are descriptive point estimates without uncertainty bands.

Regenerate with `python analysis/supplementary.py`. These figures and CSVs are in the same analysis directory as the seven prespecified figures.

## Figures and source tables

All figures use held-out test records, excluding smoke/development data. Each has PNG, vector PDF, and adjacent CSV under `results/test/analysis/`.

1. [Review budget curves](../results/test/analysis/fig01_review_budget.png): queue recall, oracle/checker ceiling, and random references.
2. [Paired organization effects](../results/test/analysis/fig02_organization_effect.png): primary and exploratory contrasts.
3. [Within-family variant transfer](../results/test/analysis/fig03_variant_transfer.png): separate queues per stratum.
4. [Residual errors](../results/test/analysis/fig04_residual_errors.png): percentages missed by subtype; exact missed/total counts are in the adjacent CSV. Natural rows overlap.
5. [Natural and controlled results](../results/test/analysis/fig05_natural_controlled.png): natural outcomes and queue composition.
6. [Prevalence sensitivity](../results/test/analysis/fig06_prevalence_sensitivity.png): conditional simulation ranges.
7. [Measured compute](../results/test/analysis/fig07_compute_cost.png): audit latency, allocated GPU memory, and separate CPU checker time.

## Hardware and execution

Test inference used **one RTX 3090 24GB**, batch size 1, BF16, Python 3.11.17, torch 2.7.1+cu126, CUDA 12.6, driver 590.48.01, and transformers 4.51.3. This project did not run on an A100. The 8B extension was not run.

Saved per-record generation and audit times total 421.0 seconds (about 7.0 minutes): 142.9 seconds generation, 96.4 seconds 1.7B auditing, and 181.7 seconds 4B auditing. These exclude model loading, downloads, provisioning, and troubleshooting, and are not total rental time or cost. Peak allocated auditor memory was approximately 3.25 GiB (1.7B) and 7.61 GiB (4B), rather than whole-process device usage. Exact total billed cost was not verified.

Smoke and development ran on an earlier rented instance. A CUDA device failure required moving the saved frozen experiment to a replacement instance, on which the test completed. Backup integrity and local run validation passed before the replacement was stopped and subsequently destroyed by the user. No additional GPU is required to reproduce the analysis from saved scores.

Frozen config retains historical draft/A100 planning strings. They are preserved to maintain its signature; the actual run status and hardware are recorded in `results/test/manifest.json` and validation files. Historical readiness documents describe preparation, not current completion.

Model revisions:

- Qwen3-1.7B: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Qwen3-4B generator/auditor: `1cfa9a7208912126459214e8b04321603b3df60c`

Frozen signatures:

- Code: `42da698bd85d730fc5a1bd77ec3f629febb4c06e3efa8f1872c46e8854297958`
- Config: `b79778518d34da45e9e247dc987b03fd2b56dcce40a44d98e7ca7ef03855983e`
- Dataset: `cbdb8c6d02c1acf7f848c902b8f6ab1930fb8f800bc8e7d9f6833be5423109a8`

From the project directory, use the locked environment and run:

```bash
python -m auditbench validate-run --out results/test
python -m auditbench analyze --out results/test
```

The local reproduction used the pinned CPU analysis environment, regenerated all seven figures, and validated 150 cases / 450 reports / 2,700 scores with zero unassessable reports. Original remote-download archive SHA256: `d2d3abc522361ea1642f861e9c746277234302296ae543b62b4f89377647ca5a`.


## Interpretation and next experiment

The result supports a narrow conclusion: sorting identical evidence by claim did not reliably improve error prioritization in this bounded setup. Larger-auditor and natural-error findings do not provide a consistent benefit across conditions. The primary interval allows both modest harm and benefit.

Limitations include synthetic constrained tasks, small family/variant coverage, one generator draw, one model family, shared generator/auditor family, induced 50% error prevalence in the controlled arm, noncalibrated scores, fully executable checks, and an oracle assumption about eventual review. No human performance or real-world safety outcome was measured.

A next experiment should retain paired identical-evidence layouts while using more realistic research artifacts and testing how human reviewers use them. Measure error detection, false alarms, decision time, and reviewer understanding, with a prespecified protocol. This remains proposed; no participant study has been conducted.
