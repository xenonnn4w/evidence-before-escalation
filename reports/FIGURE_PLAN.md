# Figure plan — seven main figures

Prepared 23 October 2026. **No figures have been generated; no experimental data exist yet.**

Produce seven main figures after real runs. Each figure may have multiple panels, and each is exported as PNG and vector PDF: seven scientific figures, fourteen image files. Save an adjacent CSV containing the plotted values. Additional 8B results use the same figure families, clearly marked as an optional extension. Do not increase the figure count merely to make the project look larger.

## 1. Errors prioritized versus review budget

Filename: `fig01_review_budget`

- Question: how many errors reach the queue as review capacity increases?
- X: actual fraction of assessable test reports selected, at nominal 10%, 20%, 40%.
- Y: erroneous reports selected / all erroneous reports.
- Panels: core auditor size and natural/controlled arm. Use clear line styles for original-order risk, organized-evidence risk and organized-evidence uncertainty; report-only risk can be a lighter diagnostic line.
- References: random selection, benchmark oracle, executable checker when it has full coverage. Report checker abstentions separately if coverage is incomplete rather than silently imputing correctness.
- Uncertainty: base-case clustered bootstrap intervals; distinguish random-ranking spread from inferential intervals.
- Data: scored records joined to independent labels and policy selections. Natural-arm plots with insufficient positives/negatives carry a descriptive-only label; zero errors means recall is undefined, not zero.

## 2. Primary effect of evidence organization

Filename: `fig02_organization_effect`

- Forest plot of S-minus-U error recall at 20% review, with a zero reference line.
- Primary point: 4B, controlled arm, fixed pooled test mixture. Secondary 1.7B and natural-arm contrasts are visually separated and labeled exploratory.
- Display raw additional erroneous reports selected alongside percentage-point differences, denominator and clustered 95% interval.
- Keep illustrative success/failure case excerpts in the report, not invented plot annotations.

## 3. Transfer to held-out task variants

Filename: `fig03_variant_transfer`

- Compare new-instance and held-out-variant test strata at 20% review for U and S, separately by auditor and arm where sample permits.
- For this diagnostic, build queues within each stratum; label this distinctly from the pooled primary queue in Figure 2. Use floor(budget*N) and show actual queue sizes.
- Show raw counts and clustered intervals, conditional on the deliberately chosen task variants.
- Avoid claiming new-domain generalization or attributing differences solely to novelty: the variants can differ in difficulty.

## 4. Errors left outside the review queue

Filename: `fig04_residual_errors`

- Heatmap: family/error subtype rows; model/condition columns at 20% review.
- Cell: fraction of that subtype's erroneous reports missed by the global risk-ranked queue, annotated with missed/total counts. Natural reports with several errors may contribute to multiple subtype rows; disclose this non-exclusivity. Controlled corruptions have one subtype.
- Separate controlled and natural panels. Empty subtypes are NA, never zero failure.
- This reveals shared failures without suggesting each cell is a separately powered comparison.

## 5. Natural reports versus controlled corruptions

Filename: `fig05_natural_controlled`

- Panel A: natural-report correct, incorrect and unassessable counts by task family. Controlled reports have a separately labeled designed 50:50 composition.
- Panel B: queue precision and recall at 20% review for U/S, with natural and controlled arms separated and counts printed.
- Natural/controlled differences are descriptive because content and error distributions differ. The designed arm is not an estimate of model reliability.
- Unassessable natural reports remain in Panel A, although excluded from assessable-report queue metrics in Panel B.

## 6. Sensitivity to error prevalence

Filename: `fig06_prevalence_sensitivity`

- Display queue precision and recall at 20% review under nominal 10% and 25% controlled-error prevalence; show actual prevalence after rounding.
- Use the prespecified 1,000 queue draws with one controlled variant per case; U/S share the same chosen records in each draw.
- Show median and 5th–95th percentile simulation ranges. These are conditional simulation ranges, not confidence intervals from new experiments.
- Include random/oracle references appropriate to each queue; the original paired 50:50 arm can appear as a separately marked reference point.
- No new model inference is needed.

## 7. Inference cost and memory

Filename: `fig07_compute_cost`

- Panel A: measured audit wall time per report, by model and condition, on the recorded hardware and batch configuration; include measured variability.
- Panel B: measured peak allocated GPU memory for each model/configuration.
- Show deterministic-checker CPU latency and hardware in a separate panel/table: do not pretend it ran on the GPU or has comparable GPU-memory usage.
- Separate initial downloads/model loading from steady-state inference; generation and audit workloads are recorded separately.
- Do not label error recall as actual human errors caught, or infer human time saved from model latency.

## Shared quality gates

- All values trace to a run ID, immutable config and machine-readable source table.
- Plot paired differences from paired bootstrap samples, not by subtracting independent confidence interval endpoints.
- Use fixed condition colors, readable units, visible sample sizes and legends that define R/U/S.
- Main figures use held-out data; development and smoke runs never silently enter them.
- Undefined or insufficient-data outcomes stay visible as such. Do not manufacture a curve to fill a panel.
- A clean-environment regeneration must reproduce the source tables and all seven figures from saved records. Numerical reproduction matters; byte-identical PDFs are not required.
