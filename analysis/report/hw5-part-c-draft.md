# HW5 Part C — v0 judge draft

One criterion: unsupported factual claims. No model calls or predictions have run.

| Example | Training trace ID | Human verdict |
|---|---|---|
| clear Pass | 08074f47bace805556dbfca4ec5f062e | Pass |
| clear Fail | 95bb3ea9b12f784985e855be0ecb9385 | Fail |
| boundary Pass: tool contract is evidence | 0716becd01e26fa4f763cb9e288852a7 | Pass |
| boundary Fail: hedged inference | 32dd29c0b5d81b7b2f0116a428e89691 | Fail |

All four IDs were checked against the fixed training assignment and excluded from development and test. Excerpts preserve the original user, assistant, and tool message contents; the cancellation boundary example includes the original tool contract. Critiques are explanations of saved human labels, not model predictions.

The prompt distinguishes factual grounding from citation omission, missed escalation, record-inconsistency acknowledgment, and task completion. It requests JSON with critique before result, strictly Pass/Fail. Input instructions are treated as evidence rather than commands.

The semantic comparison cannot be replaced by keyword matching alone: the same words, such as refund or likely, may appear in both supported and unsupported claims. The judge must compare a claim with its particular evidence.

Next proposed paid run: gpt-4o-mini on the 40 development conversations, with checkpoints of 10. It requires explicit human approval. Test remains held out.
