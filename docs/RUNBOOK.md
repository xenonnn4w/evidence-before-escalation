# Runbook: prepare locally, execute on one GPU

**Implementation update:** The CPU-validated pipeline now exists. Follow [LAUNCH.md](LAUNCH.md) for exact executable commands; the phase descriptions below retain the design rationale. Real GPU validation remains pending.

## A. CPU preparation — before rental

1. Implement case generators, independent reference checkers and corruption operators under `auditbench/`.
2. Implement schema validation, label-blind renderers, split manifest and analysis on clearly marked fixture scores. Fixtures never enter results as model data.
3. Test hand-computed metrics, evaluation-provenance rules, unsupported-claim rules, deliberate corruptions, split/variant isolation, bootstrap clustering, ranking ties and oracle ceilings. Assert identical record multisets for U/S; inspect prompt leakage and token lengths. Implement the executable checker baseline separately from saved gold labels.
4. Implement generator, binary likelihood scorer and append-only run records. Implemented entry point: `python -m auditbench`; `run` performs resumable generation, labeling and auditing. Other commands are `build-cases`, `verify-data`, `preflight`, `validate-run`, `freeze` and `analyze`.
5. Resolve model revisions to immutable commit hashes. Build a tested Python environment and lockfile from official package sources; do not copy unverified old version pins. Add an exact setup script after validating it.
6. Create dataset/config/prompt hashes, an expected-record manifest and a dry-run job count. Confirm no oracle fields reach the auditor.

## B. Machine selection and budget

Target one A100 40GB, at least 32GB host RAM and 60GB free persistent disk, sequential BF16 inference. Weight-memory lower bounds are about 3.4GB (1.7B), 8GB (4B), 16GB (8B), before activations, caches and runtime overhead. Actual peak memory must be measured. Load only one model at a time; begin batch size 1 and tune only on development data. Do not mix quantization across the primary comparison.

Before renting: confirm provider, hourly price, maximum spend, shutdown mechanism and export destination with the user. Budget is currently unset. No rental is authorized by this document alone. Record GPU model, VRAM, driver, CUDA, Python, package versions and region in a run manifest. No credentials in logs or repository.

## C. Smoke run and timing

Use 3 development cases (one per family), 9 reports, one 1.7B auditor, three views: 27 audit scores plus 3 generator completions. Each audit score requires two label likelihoods. Exercise all stages, including archive/reload and CPU analysis.

Abort progression for bad token masking, NaN scores, leaked labels, invalid mutation labels, duplicate IDs, missing records, unexpected truncation or inability to reproduce a table from saved records. Model mistakes are observations, not infrastructure failures.

Measure generator seconds per report, audit seconds per score at each relevant input length, download/setup time and peak memory. Forecast cost from measured throughput and actual remaining counts. Include export and shutdown time plus a stated contingency. An initial 4B timing slice is needed before extrapolating 1.7B timing to it. Do not infer this experiment's duration from a different project's runtime.

## D. Development and freeze

Complete the 30-case development partition: 30 generator completions, 90 reports, 540 audit score records across the two auditors and three views. Smoke records can be reused only if all final hashes/settings match; otherwise mark them superseded.

Fix engineering and ambiguity using development cases only. Record decisions and qualitative predictions. Keep the chosen primary contrast fixed; changes require explicit protocol versioning. Freeze all artifacts before test inference. Sign off the checklist.

## E. Main run

1. Qwen3-4B generates 150 held-out natural reports (one per case). Preserve raw output and generation metadata.
2. CPU checker independently labels these and builds controlled reports. Do not inspect held-out outcome aggregates to tune prompts. Unassessable natural reports retain status and evidence.
3. Sequentially run 1.7B then 4B auditors across all three views, all 450 test report slots. Audit only assessable natural records; record skipped slots explicitly. Controlled reports must all be assessable. Expected maximum: 2,700 audit score records.
4. Resume by case ID, report ID, arm, model revision, prompt/config hash and condition; never overwrite an incompatible record. Save after each batch and capture failures.
5. Run analysis with frozen settings. Persist counts before plotting; check oracle and random baselines. Export all artifacts before shutdown and verify archive hashes locally.

No improvement is required to call the experiment complete. Required evidence is execution, label validity, faithful analysis and reproducibility.

## F. Optional extension

Only after core results are archived and budget remains: Qwen3-8B auditor on the same 540 report slots (up to 1,620 extra scores), unchanged protocol. Label this extension and disclose if selected after inspecting core outcomes. It is not required for the minimum deliverable. Cross-family replication and actual human participants belong to future work.

## G. Deliverables

- `data/cases/`: specs, raw artifact files, compact evidence and independent labels.
- `data/splits.json`: immutable base-case split mapping.
- `results/<run_id>/`: manifest, raw generation records, all audit scores, errors and performance measurements.
- `analysis/`: reproducible CPU analysis; tables and plots in the run directory.
- `reports/`: completed report, explicit limitations, provenance and assistance disclosure.
- Archive contains code, configs, prompts, manifests, raw records, tables and figures. Exclude model weights, environments and credentials. Rebuild one table and figure from the archive in a clean environment before delivery.

Scientific result figures: recall versus review budget; paired S-minus-U evidence-organization effect; new-instance versus held-out-variant results; errors missed by family; natural versus controlled results; prevalence sensitivity; inference-cost comparison including the deterministic checker. Distinguish bootstrap intervals from random-policy spread.
