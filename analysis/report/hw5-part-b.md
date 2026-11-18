# Homework 5 Part B complete

99 approved conversation representatives exported with original system instructions, tool definitions, relevant earlier messages, user requests, assistant replies, tool calls, tool results, and retrieved policy passages. Review labels, reasons, annotations, and scenario metadata are stored separately.

| Split | Pass (1) | Fail (0) | Total |
|---|---:|---:|---:|
| train | 14 | 6 | 20 |
| dev | 28 | 12 | 40 |
| test | 27 | 12 | 39 |

Seed: 7. Fractions: 20% / 40% / 40%. No overlap; all 99 inputs have one approved label and one split assignment. The existing unrelated mode was preserved. Rerunning Part B verifies and reuses the saved artifacts; it does not reshuffle.

Offline verification: 3 preparation tests passed; rerun produced identical evidence, labels, and split manifests. No model calls, prompt-example selection, or test predictions.

To select the fixed input source from the repository root:

```sh
export CARTWHEEL_JUDGE_TRACE_SOURCE="$PWD/analysis/state/hw5_trace_inputs.json"
```

Next: choose examples from training only and draft the judge prompt. Keep development and test examples out of the prompt.
