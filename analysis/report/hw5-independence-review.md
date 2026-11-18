# HW5 independence review

Human labels remain unchanged. No dataset splits or paid calls.

Raw approved: {'Fail': 35, 'Pass': 79}. After conservative close-variant grouping: {'Fail': 30, 'Pass': 69}.

Public policy paraphrases are merged across users and roles. Representatives are selected by earliest timestamp then trace ID, without looking at verdicts. Mixed labels can reflect different assistant behavior; they are not automatically annotation conflicts.

| Representative | Verdict | Group members |
|---|---|---|
| support-0192 | Fail | support-0192 (Fail), support-0193 (Pass) |
| support-0080 | Fail | support-0080 (Fail), support-0085 (Fail), support-0090 (Fail), support-0095 (Pass), support-0100 (Pass) |
| support-0077 | Pass | support-0077 (Pass), support-0082 (Fail) |
| support-0081 | Pass | support-0081 (Pass), support-0086 (Pass) |
| support-0232 | Pass | support-0232 (Pass), support-0233 (Pass), support-0235 (Fail) |
| support-0078 | Pass | support-0078 (Pass), support-0083 (Pass), support-0088 (Fail) |
| support-0226 | Pass | support-0226 (Pass), support-0227 (Pass), support-0228 (Pass), support-0229 (Pass), support-0230 (Pass) |
