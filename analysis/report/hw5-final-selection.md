# HW5 final judge selection

The human retained all nine v2 disagreement labels and selected v1. All nine adjudications are recorded as judge errors. Existing human labels, inputs, and splits remain unchanged.

Selected judge: unsupported_factual_claim-v1, model gpt-4o-mini. The exact evaluated v1 prompt is frozen; its prior 40 development predictions and critiques remain preserved. No test predictions exist.

V1 was selected because it had the strongest development TPR and TNR across the three evaluated versions: TPR 100% and TNR 58.33%. It still missed 5 of 12 human failures. Both permitted revisions were used; the stopping decision does not depend on meeting an arbitrary accuracy threshold. Held-out test results are still needed before the final assessment.

Next proposed paid batch: the frozen v1 judge with gpt-4o-mini on 39 held-out test conversations (27 human Pass, 12 human Fail). Explicit user approval is still required. The final prompt will not be revised based on test predictions.
