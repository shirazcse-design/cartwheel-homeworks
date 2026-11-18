# Homework 5 — unsupported factual claim judge

## Task and human labels

The selected failure is a factual claim that the supplied conversation, original system context, tool contracts, and observed results do not establish. Pass means the failure is absent; Fail means at least one unsupported factual claim occurs. Missing citation alone, missed escalation alone, and faithful repetition of inconsistent records are separate issues. The human selected the definition and approved the labels and disagreement adjudications.

The dataset contains 99 conservatively grouped conversation representatives: 69 Pass and 30 Fail. Grouping merges public-policy paraphrases across caller identities/roles, repeated fixtures, and related public product/store queries; private cases retain order and authorization context. These rules reduce close-variant leakage but do not prove statistical independence. The label-collection sample is enriched for failures and is not an estimate of natural agent-failure prevalence. Original HW4 labels remain preserved.

## Preparation and split

Inputs contain observed user/assistant messages, relevant history, tool calls/results, policy passages, and original instructions/tool contracts. Review labels, reasons, scenario expectations, and annotations are excluded from judge inputs. Inputs were hashed and held fixed before any prompt run. Human labels use 1=Pass and 0=Fail.

| Split | Pass | Fail | Total |
|---|---:|---:|---:|
| Training | 14 | 6 | 20 |
| Development | 28 | 12 | 40 |
| Test | 27 | 12 | 39 |

Split seed 7; proportions 20/40/40; no overlap. Representatives were chosen by earliest timestamp then trace ID, without selecting on verdict. Only training cases were used as prompt examples. Existing unrelated split entries were preserved.

## Development and stopping

Each version used gpt-4o-mini through DocETL on the same 40 development conversations. Predictions and critiques were saved in batches of 10.

| Version | TPR | TNR | Disagreements |
|---|---:|---:|---:|
| v0 | 100.00% | 8.33% | 11 |
| v1 | 100.00% | 58.33% | 5 |
| v2 | 96.43% | 33.33% | 9 |

The human reviewed all 11 v0 disagreements, all 5 v1 disagreements, and all 9 v2 disagreements, retaining the existing labels and recording judge errors. V1 strengthened claim-by-claim checking and added a training example of unsupported refund completion/timing. V2 required a structured audit but performed worse. The human selected v1 because it had the strongest observed development TPR and TNR. Both allowed revisions were used; no numerical acceptance threshold was imposed. V1 was frozen before test predictions were generated.

### Development disagreement example

Trace `423448f3fbaf1a9636aacdd84aa004e6`: the assistant correctly reported a queued $282 refund request but also promised a notification once processed. The tool result established human review, not a notification mechanism. The human labeled Fail. V0 judged Pass because it focused on the supported refund facts and ignored the extra promise. The human retained Fail; the v1 prompt explicitly separated notifications from queued review, using training-only examples. V1 judged this development case Fail. This is a development lesson, not evidence of test performance.

## Held-out test

The human explicitly approved the frozen v1 test batch using gpt-4o-mini. All 39 held-out conversations were evaluated once as the final test, with checkpointed predictions and critiques. No prompt changes followed the test.

| | Human Pass | Human Fail |
|---|---:|---:|
| Judge Pass | TP = 25 | FP = 9 |
| Judge Fail | FN = 2 | TN = 3 |

Pass is the positive class.

| Metric | Calculation | Result | 95% Wilson interval |
|---|---|---:|---|
| TPR | 25 / (25 + 2) | 92.59% | 76.63–97.94% |
| TNR | 3 / (3 + 9) | 25.00% | 8.89–53.23% |
| Agreement | (25 + 3) / 39 | 71.79% | — |

Confusion counts and Wilson intervals were independently recomputed from saved public labels and predictions and checked against the course helper output. Agreement alone masks the poor failure detection: the judge missed 9 of 12 human Fail cases. The intervals are wide, especially for TNR, because there are only 12 held-out human failures. These estimates apply to this sampled synthetic evaluation set, not automatically to production.

## Use recommendation and human decision

**Assistant recommendation:** do not use this judge for unattended failure detection. It detected only 25% of human failures in the held-out sample. If retained as an experimental reviewer aid, it requires human oversight; a Pass verdict should not be treated as reliable clearance. This recommendation follows the observed rates and uncertainty rather than a predeclared score threshold.

**Human use decision:** confirmed. The human agrees not to use this judge for unattended failure detection, based on its low held-out failure detection rate and uncertainty. Approval is saved in `analysis/state/hw5_use_decision.json`. No additional prompt revision or paid run is authorized.

## Recalculate saved test metrics live

From the repository root, run:

```sh
.venv/bin/python -m analysis.run_judges test-metrics --judge-id unsupported_factual_claim-v1
```

This reads the saved labels and cached predictions and recalculates metrics; it makes no model calls. Do not register a new judge, split again, refreeze, or revise the prompt after inspecting test results.

## Artifacts and verification

- Labels: `analysis/state/hw5_labels/unsupported_factual_claim.jsonl`
- Exact inputs: `analysis/state/hw5_trace_inputs.json`
- Fixed split: `analysis/state/splits.json`
- Prompts: `analysis/prompts/unsupported_factual_claim-v0.txt`, `-v1.txt`, `-v2.txt`
- Judge records, predictions, critiques: `analysis/state/judges/unsupported_factual_claim-v*.json`
- Development metrics: `analysis/report/dev-unsupported_factual_claim-v*.json`
- Final metrics: `analysis/report/test-unsupported_factual_claim-v1.json`
- Runner: `analysis/run_judges.py`
- Selection and approvals: `analysis/state/hw5_final_selection.json`, versioned development approvals, and `analysis/state/hw5_test_approval.json`

23 focused offline checks passed before the final test. Live work comprised three explicitly approved 40-conversation development batches and one explicitly approved 39-conversation test batch. Prompts, labels, input hashes, and split hashes were checked for preservation.

## Submission and video

The submission artifacts are committed together; secrets, runtime caches, session databases, and unrelated files are excluded.

The human records a continuous screen video of up to five minutes: failure definition, one development disagreement, version choice, held-out TPR/TNR and intervals, live cached-metric recalculation, and the use decision.
