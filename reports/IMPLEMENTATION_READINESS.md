# Implementation readiness — 23 October 2026

**Status: prepared for the first A100 smoke run. Full experiment readiness remains conditional on that GPU check and the development freeze.**

Implemented: deterministic case suite; independent artifact-derived checker; correct/corrupted controls; original/organized evidence renderers; pinned model loading; conditional likelihood scoring; per-case seeded generation; resumable logs; failure recording; single-writer lock; real/fixture separation; freeze gate; optional 8B extension; clustered analysis and seven figure families.

## Verified locally

**20 tests passed**, including independent likelihood-reference verification, malformed JSON handling, data/label consistency, oracle limits, optional-extension reuse, rejection of changed signatures, and tampered-record detection. Full test output is in `verification/tests.txt`.

- 180 cases validate: 30 development, 90 new-instance test, 60 held-out-variant test.
- All 180 pairs preserve the same evidence records and actually change their order.
- Every canonical/corrupted control agrees with the independent checker.
- Raw prediction arrays agree with the confusion counts supplied as evidence.
- Core model/tokenizer revisions resolved and pinned to immutable Hugging Face hashes.
- Pinned 1.7B and 4B tokenizers checked across all controlled reports/views: maximum 712 input tokens; verdict boundaries preserved; each verdict is one answer token plus EOS.
- CPU model test: production likelihood calculation matches a full-logits reference on a tiny randomly initialized Qwen3. This verifies scoring mechanics, not pretrained-model performance.
- Synthetic test-partition pipeline generates all seven figures in PNG and PDF with source tables; fixture mode is prominent on every figure.
- Hypothetical precision simulation completed, explicitly separate from model results.
- Locked CPU environment installed and tested; CUDA dependency resolution is included in `uv.lock`.

## Still requires the rented GPU

- Installing CUDA inference dependencies on the actual host and loading the pinned pretrained models.
- BF16 inference correctness/compatibility, peak VRAM and measured throughput.
- Real smoke run, development run, operator review and freeze before held-out inference.
- Provider price/spending cap, shutdown timer and verified artifact export.

No pretrained model results, real research effects or A100 usage are claimed yet. The local machine has a 6GB RTX 4050, while the model mechanics test used CPU PyTorch. No compute rental or spending occurred during preparation.

See [LAUNCH.md](../docs/LAUNCH.md) for commands and [FIGURE_PLAN.md](FIGURE_PLAN.md) for figure definitions. Historical planning/readiness notes are retained as history; this file describes implementation status.

The final synthetic test run contains 150 cases, 450 report slots, 2,670 audit records and 5 explicitly unassessable fixture reports. Its full analysis used 2,000 bootstrap replicates and 1,000 prevalence draws; all seven figure families were emitted. These counts describe software verification, not scientific findings.

Export verification passed: the archive was extracted to a separate directory, its fixture records validated, and all seven figures regenerated. All 11 CSV tables matched the original byte for byte. See `verification/export-reproduction.json`.
