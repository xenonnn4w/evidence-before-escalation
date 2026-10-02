**Historical audit, before implementation.** See [IMPLEMENTATION_READINESS.md](IMPLEMENTATION_READINESS.md) for current status.

# Launch-readiness verification

Date: 23 October 2026. Scope: inspect existing preparation files and verify launch readiness, without implementing the experiment.

**Verdict: NOT READY FOR GPU RENTAL.** The design pack exists, but executable implementation and scientific validation are pending. “Plan ready” must not be interpreted as “experiment runnable.”

## Checks actually performed

| Check | Outcome | Evidence |
| --- | --- | --- |
| Planning inventory | PASS | Protocol, prompts, configuration, runbook, checklist and report outline exist |
| Workload arithmetic | PASS | 180 cases; 30 development + 150 test; 540 report slots; 3,240 core audit scores; 1,620 optional 8B scores |
| Split arithmetic | PASS | Per family: 10 development + 30 new-instance + 20 held-out-variant = 60 |
| Local Markdown link resolution | PASS | No missing link targets in the inspected pack |
| Executable CLI | FAIL | From the project root, `python -m auditbench --help` exits 1: no `auditbench.__main__` |
| Implementation files | NOT IMPLEMENTED | No `.py` files or `.sh` launch/setup scripts in this project |
| Cases and split manifest | NOT CREATED | `data/` empty |
| Tests | UNAVAILABLE | `tests/` empty; no meaningful test suite exists to execute |
| Dependency environment | NOT READY | No pyproject/requirements/lockfile; active Python has no torch or transformers |
| Model revision pins | NOT SET | Generator, auditor and optional auditor revisions are null |
| Resume / failure recovery | UNVERIFIED | No implementation or persisted run records |
| GPU smoke test / throughput | NOT RUN | `results/` empty; no measured timing or memory results |
| Rental cost control | NOT SET | No provider, price or maximum spend configured |
| Figures | SPECIFIED, NOT GENERATED | Seven main figures in FIGURE_PLAN.md; no plotting implementation yet |

The local machine reports RTX 4050 Laptop GPU, 6,141 MiB VRAM. Home filesystem has about 5.6 GB free. This is not the planned A100 environment and is not a suitable place to download all full-precision checkpoints with the current free space. Local CPU implementation and fixture validation can proceed without downloading models. No files were deleted or GPU rented during this audit.

## Required before renting

1. Implement case generators, explicit report schemas, independent labels and corruption checks.
2. Implement U/S evidence views and prove identical record content with label-blind ordering; validate variant isolation.
3. Implement generation, likelihood scoring, resume keys, failure records and run validation.
4. Implement checker baseline, budget policies, clustered analysis and seven figure outputs; test with explicitly synthetic fixtures.
5. Resolve model revisions and validate dependency setup/lock; prepare a working launch script.
6. Confirm rental provider, cost ceiling, storage/export and shutdown plan.

Then run a small GPU smoke test and development pass before freezing and launching the held-out run. CPU checks cannot establish actual A100 memory use or throughput.

## Runtime statement

The earlier 4–6-hour core / 6–8-hour extended estimates are unmeasured planning allowances, not verified execution forecasts. No rental-duration guarantee is supported yet. Timing must include two candidate-answer likelihoods per audit score; batching/prompt reuse, sequence lengths, downloads and actual hardware determine the total. Replace the estimate after a valid pilot using both core model sizes.

## Figure count

Seven main scientific figures, exported as PNG and PDF with source tables. Multi-panel figures still count as one figure. Missing natural-error samples or incomplete runs may leave explicitly marked unavailable panels; no results may be invented to complete the layout.
