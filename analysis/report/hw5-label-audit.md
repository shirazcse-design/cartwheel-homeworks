# Homework 5 label audit — human quality review pending
Mode: `unsupported_factual_claim`. No labels were changed and no model calls were made.
| Set | Pass | Fail | Total |
|---|---:|---:|---:|
| Original HW4 records (interpreted as HW5 classes) | 82 | 67 | 149 |
| Proposed independent situation representatives | 41 | 59 | 100 |

**Numeric minimum after proposed grouping:** met. This does not establish label quality or final eligibility.
## Independence rule
Group by data-quality fixture ID when present. Otherwise group by scenario tuple after dropping surface style, difficulty and turn-count fields. This merges same-session turns/retries and close metadata variants. Choose the earliest labeled timestamp then trace ID, never by outcome. Metadata can miss semantic duplicates; a final human check is still needed.
## Quality findings
138 labels were flagged for possible evidence/reason problems, reused rubric text, retained proposal language, or unresolved notes. Flags are review leads, not replacement labels.
The audit must be resolved before exporting trusted HW5 labels or splitting. Do not rely on raw class totals alone. Existing HW4 originals and splits were preserved.
## First review items
| Scenario | HW4 value | Issue |
|---|---:|---|
| support-0001 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0004 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0029 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0039 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0055 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0067 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0071 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0094 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0095 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |
| support-0101 | 1 | Identical reason reused on at least three traces; may lack trace-specific evidence. Reason repeats the rubric without identifying the unsupported claim or missing evidence. |

Full membership, trace IDs and reasons: [hw5-label-audit.json](hw5-label-audit.json).
No HW5 labels, inputs, splits, prompts or predictions have been created by this audit.
