# Launch instructions

The package is prepared for a Linux NVIDIA GPU machine. The code and analysis have been validated on CPU and synthetic fixtures. Actual BF16 inference, A100 memory and throughput must pass the smoke run before full execution.

## Machine

One A100 40GB, 32GB+ system RAM, 80–100GB disk, network access to PyPI/Hugging Face. Use an NVIDIA driver compatible with the CUDA libraries in the locked PyTorch 2.7.1 Linux wheel. The smoke run is the actual compatibility check. Run only one model process at a time.

Before provisioning, choose a provider and spending limit. Set a provider-level shutdown timer. `RUN_TIMEOUT_HOURS` below only stops the experiment process; it does **not** stop GPU billing or shut down the rented instance. Nothing in this repository purchases compute.

## 1. Unpack and install

Unpack the provided archive and enter `budgeted-research-auditing/`. Install uv from its official instructions if absent, then:

```bash
./scripts/setup.sh gpu
```

This installs Python 3.11 and the locked dependencies, runs the tests, builds the seeded cases and validates them. Models are loaded at immutable revisions from `configs/core.json`. The setup does not download model weights; the first real run does.

For local CPU checks only use `./scripts/setup.sh cpu`. That excludes PyTorch/Transformers. The optional likelihood test is then skipped; it was separately validated with CPU PyTorch during preparation.

## 2. Smoke run

```bash
RUN_TIMEOUT_HOURS=1 ./scripts/launch.sh smoke results/smoke
```

Three development cases, 4B generation, 1.7B auditing, three evidence views: up to 27 scores. Expect explicit skips for unassessable natural reports, never missing controlled reports. The preflight checks token boundaries and context lengths with the pinned tokenizers. Model downloads/loading may dominate this first run.

If the command fails, inspect the terminal and `results/smoke/errors.jsonl`. Fix an engineering defect before proceeding. To resume an interrupted run with unchanged code/config/data, rerun the same command; completed generation and audit records are reused. Modified sources require a new run directory. Never edit a signature merely to force a resume.

## 3. Development pass

```bash
RUN_TIMEOUT_HOURS=2 ./scripts/launch.sh development results/development
.venv/bin/python scripts/estimate_runtime.py results/development
```

This includes both 1.7B and 4B auditors. Review actual prompts, schema failures, CPU labels, GPU memory and timings. Select rental duration from these measured results; the earlier 4–6-hour allowance is not a benchmark. No need to pay for an idle GPU while reading the report: download artifacts and stop the instance if review will take time.

Before freezing, record predictions and implementation decisions. Make prompt/engineering changes only on development cases. If implementation changes, repeat the affected development run under a new directory so the freeze matches the actual code.

## 4. Freeze and run the held-out partition

```bash
.venv/bin/python -m auditbench freeze --development-run results/development
RUN_TIMEOUT_HOURS=4 ./scripts/launch.sh test results/test
```

The test run refuses to start without a matching freeze from a completed real development run. The freeze covers implementation, prompts, protocol, dependency lock, scripts, configuration and dataset. The timeout is an operator-selected process cap, not a runtime prediction.

## 5. Validate, export, analyze

```bash
.venv/bin/python -m auditbench validate-run --out results/test
.venv/bin/python -m auditbench analyze --out results/test
```

Full analysis uses 2,000 clustered bootstrap replicates and 1,000 prevalence draws. It writes seven PNG figures, seven PDF figures and source CSV tables under `results/test/analysis/`. You can copy the complete project and run these CPU-only analysis commands locally after shutting down the GPU. Retain the run's matching code and configuration.

Copy the raw results, dataset, frozen manifest and source code to persistent local storage. Confirm hashes before deleting anything on the rental machine, then terminate the GPU instance through the provider. The experiment does not automatically terminate a provider instance.

## Optional 8B extension

After the core test is complete and archived, extend the same run directory:

```bash
.venv/bin/python -m auditbench run --phase test --mode real --out results/test --freeze data/freeze.json --optional-8b
.venv/bin/python -m auditbench analyze --out results/test
```

This preserves existing generation/core-auditor records and adds only missing 8B scores. It records the extension start time. Keep the archived core results for the original planned analysis. Use a provider stop timer for the extension too.

## Verify the pipeline without a GPU

```bash
.venv/bin/python -m auditbench run --phase test --mode fixture --out outputs/my-fixture-check
.venv/bin/python -m auditbench analyze --out outputs/my-fixture-check --quick-fixture
```

These commands produce **synthetic software-test data only**. All figures carry that label, and fixture runs cannot authorize a real freeze. `--quick-fixture` is rejected for real data.

## Interpret run records

- `manifest.json`: mode, phase, model pins, fingerprints and actual hardware for real runs.
- `generation.jsonl`: prompt, raw model output, tokens, seed, elapsed time and truncation status.
- `reports.json`: independent labels and unassessable outputs; no silent regeneration.
- `scores.jsonl`: both conditional label log likelihoods, relative score, prompt and runtime.
- `errors.jsonl`: failures, preserved even when a later resume succeeds.
- `performance.jsonl`: model loading time, separate from per-record inference.
- `validation.json`: completeness check with exact expected records and explicit skips.

One writer per run directory is enforced by a process lock. A corrupt/truncated JSONL record fails loudly rather than being silently discarded; preserve it and document any repair before continuing.
