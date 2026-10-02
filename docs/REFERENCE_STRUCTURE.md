# Structure learned from the previous A100 task

Reviewed read-only: the author’s prior linear-probe replication exercise. Those local reference materials are not included in this repository.
The original task and its code remain unchanged. Its assessment instructions are specific to that exercise; this is a new independent research plan, not a reused assessment submission.

| Existing component | Observed purpose | Adaptation here |
| --- | --- | --- |
| README.md | Seven explicit questions; predictions before experiments; bounded deliverables | Seven questions with a primary endpoint and proposed hypotheses |
| decept/pyproject.toml and environment | Reproducible model/evaluation dependencies | Fresh minimal environment, tested lockfile and immutable model revisions |
| run_q1_scaling.sh | Model queue, per-model logs, smallest-model smoke gate | Sequential generator/auditor queue with resume keys and fail-fast validation |
| run_q6_minimal.sh | Generation, scoring, summaries and a manual label audit | Separate generation, fresh outcome labeling, auditing and analysis stages |
| analysis/*.csv and *.txt | Compact results and limitations | Per-record raw evidence plus deterministic aggregate tables |
| slides_template/slides.md and figures/ | Question-by-question explanation and plotted evidence | Short report with one answer and evidence trail per research question |
| Session logs | Traceability of AI assistance and researcher decisions | Decision log and AI-assistance disclosure; secrets excluded from public artifacts |

Useful lessons from the actual artifacts:

1. Q1 has both fixed-layer and post-hoc best-layer figures. Here the main auditor, budget and comparison are fixed before test inspection; best-looking exploratory settings are labeled exploratory.
2. Q4 used centroid differences because fitted probe weights were unavailable. Here preserve the actual scoring inputs, score components and model metadata needed to reproduce the claimed quantity.
3. Q6's manual audit found generated answers inconsistent with inherited labels. Here every natural report is checked against the artifacts it describes; labels from its prompt are never inherited as observed correctness.
4. The queue checks process exit status, but individual run completion is not enough. Our gate also checks expected record counts, duplicate IDs, non-finite scores, schema failures and hashes.
5. A fixed presentation budget encourages clear claims. The new report separates hypotheses, observed results, failure analysis and the human-study follow-up.

We reuse this workflow structure, not the old dataset, probe implementation, institutional branding, or conclusions. The old source contains no evidence that this new experiment has run on an A100.
