# Homework 4 — human trace review and failure taxonomy

## Status and scope

The review contains **149 distinct traces**, including the required **100-trace four-stage sample** and **49 supplemental traces** read during session-context exploration, guided review and taxonomy checks. Each trace has all five final binary judgments: **745 total**, with no missing or duplicate trace/mode pairs. All local records are human-accepted and record successful Langfuse synchronization. This summarizes the write acknowledgments recorded by the app; it is not an independent re-fetch of all remote scores.

**Consistency check resolved:** five labels initially conflicted with their saved absence explanations and approved close-negative examples. The human explicitly approved correcting all five to Absent (0). Corrections synchronized to Langfuse, previous values remain in review_history.json, and all counts below were regenerated from the corrected records.

## Sampling and composition

The live collection has 305 traces across 252 sessions. Original trace IDs are retained; session grouping supplies context without replacing turn-level identities. Initial selection combines structural clustering with uniform sampling; the role dimension was approved before looking at outcomes. Depth searches include possible failures and similar negative cases.

| Selection stage | Distinct selected traces | Method |
|---|---:|---|
| Initial random | 15 | Uniform random |
| Cluster representatives | 15 | Deterministic standardized structural/role KMeans; centroid representatives excluding overlap |
| Role breadth | 30 | Uniform random within authenticated role: 10 shopper, 10 merchant, 10 support; seed 20261113 |
| Depth search | 25 | Six citation comparisons and 19 focused candidates; no overlap with earlier stages |
| Final stability batch | 15 | Uniform random after five supported draft definitions; seed 20261115; excludes all earlier selected or reviewed IDs |
| Total required sample | **100** | Every selected trace has an initial human observation |

Required sample roles: merchant: 35, shopper: 33, support: 32. Required scenario groups: challenge: 43, coverage: 57.

All 149 reviewed traces: merchant: 52, shopper: 53, support: 44; scenario groups: challenge: 67, coverage: 82. Selection seeds, reasons and trace identities are in `analysis/state/sample_manifest.json`; the final outcome-blind plan is included there. Supplemental traces do not replace required-stage selections.

The initial record contains 153 observations across 149 traces because some traces have more than one note. Notes with unresolved judgments remain unresolved; they are not independently counted as positive examples. Structured labels are a separate later pass.

## Review and labeling workflow

The human first read conversations with tool activity and recorded free-text observations at the first observed failure, or explicitly recorded no failure. Guided comparisons checked behavior against SPEC.md. Human corrections supersede earlier judgments while preserving edit history. Category names, grouping and definitions were approved in chat and saved with supporting annotation IDs.

Structured labeling then applied every final mode separately, allowing multiple modes per trace. Convention: **1 = failure present; 0 = failure absent**. The custom app writes stable score IDs to Langfuse and matching local label files. Saved judgments were not automatically replaced by AI proposals.

To reduce repetitive entry, prepared proposals used confirmed example links and transparent evidence rules over policy IDs, dates, failed lookup results and escalation tickets. They were not an LLM judge. Uncertain cases were highlighted, evidence and preceding session context were available, and the human could edit then explicitly approve selected rows. Proposal loading never wrote scores. Prior generic no-failure notes alone were not converted into final absent labels.

## Final taxonomy

Five modes are final. Evaluator types below are implementation recommendations, not evaluated judges; no judge performance is claimed. The out-of-scope candidate remains provisional and is excluded from final-mode counts.

### unsupported_factual_claim

The reply makes a factual claim that the available conversation and tool results do not establish. Qualifying it with likely does not excuse inventing missing attributes.

**Requirement:** SPEC.md RESP-3. **Likely evaluator:** LLM judge.

**Boundary:** Unsupported information, rather than a supported policy claim with a missing citation or a failure to acknowledge contradictory records. Those remain separate drafts. Judge the particular factual claim, not the entire answer.

**Human-confirmed origin/positive examples (7):** [support-0190](http://localhost:3000/project/cartwheel-dev/traces?peek=110c8024456751cb2b22d2380f0ce9df&timestamp=2026-11-03T03%3A21%3A26.063000Z&peekView=expanded) (`110c8024456751cb2b22d2380f0ce9df`); [support-0192](http://localhost:3000/project/cartwheel-dev/traces?peek=6e4e8e75c65ecb82e7d8aedd86dc6d14&timestamp=2026-11-03T03%3A21%3A42.504000Z&peekView=expanded) (`6e4e8e75c65ecb82e7d8aedd86dc6d14`); [support-0140](http://localhost:3000/project/cartwheel-dev/traces?peek=b27ec0cec03fbb0efe9f99eef5624759&timestamp=2026-11-03T03%3A18%3A15.531000Z&peekView=expanded) (`b27ec0cec03fbb0efe9f99eef5624759`); [support-0080](http://localhost:3000/project/cartwheel-dev/traces?peek=de5bf55226fc084f82f69c2bd97a3258&timestamp=2026-11-03T03%3A14%3A15.627000Z&peekView=expanded) (`de5bf55226fc084f82f69c2bd97a3258`); [support-0090](http://localhost:3000/project/cartwheel-dev/traces?peek=62a2e31b81081d8c3fdb2847cb323fb2&timestamp=2026-11-03T03%3A14%3A50.664000Z&peekView=expanded) (`62a2e31b81081d8c3fdb2847cb323fb2`); [support-0080](http://localhost:3000/project/cartwheel-dev/traces?peek=8e2b3cdabd7fa73f8df37d0351546229&timestamp=2026-11-03T03%3A14%3A19.928000Z&peekView=expanded) (`8e2b3cdabd7fa73f8df37d0351546229`); [support-0204](http://localhost:3000/project/cartwheel-dev/traces?peek=b5ff2108193d1a79ef033cc5b5f210c3&timestamp=2026-11-03T03%3A22%3A32.815000Z&peekView=expanded) (`b5ff2108193d1a79ef033cc5b5f210c3`)

**Confirmed close negatives (3):** [support-0186](http://localhost:3000/project/cartwheel-dev/traces?peek=2e4c04589f3f8a06d3b5815e85f13645&timestamp=2026-11-03T03%3A21%3A05.228000Z&peekView=expanded) (`2e4c04589f3f8a06d3b5815e85f13645`); [support-0193](http://localhost:3000/project/cartwheel-dev/traces?peek=606e79ad1442914725f5ae56a0a262ab&timestamp=2026-11-03T03%3A21%3A45.987000Z&peekView=expanded) (`606e79ad1442914725f5ae56a0a262ab`); [support-0246](http://localhost:3000/project/cartwheel-dev/traces?peek=f3c00694c2e670cbffbbf88bd054d175&timestamp=2026-11-03T03%3A25%3A52.111000Z&peekView=expanded) (`f3c00694c2e670cbffbbf88bd054d175`)

Supporting human annotation IDs are saved alongside these trace IDs in `analysis/state/patterns.json`. These origin-example counts are not substitutes for the full structured-label totals.

### missing_policy_citation

The reply makes a policy-derived claim without citing a supporting policy identifier.

**Requirement:** SPEC.md RESP-1. **Likely evaluator:** LLM judge.

**Boundary:** One relevant identifier may support several claims; the reply need not cite every retrieved document. Unsupported information remains a separate category.

**Human-confirmed origin/positive examples (3):** [support-0229](http://localhost:3000/project/cartwheel-dev/traces?peek=c254aed9eafbc5b503c5cee13d09f90a&timestamp=2026-11-03T03%3A24%3A16.395000Z&peekView=expanded) (`c254aed9eafbc5b503c5cee13d09f90a`); [support-0233](http://localhost:3000/project/cartwheel-dev/traces?peek=cd956419a87cf2326fc16f77edec360c&timestamp=2026-11-03T03%3A24%3A29.574000Z&peekView=expanded) (`cd956419a87cf2326fc16f77edec360c`); [support-0235](http://localhost:3000/project/cartwheel-dev/traces?peek=72e042943ee0970f80ecc89ef386a9c2&timestamp=2026-11-03T03%3A24%3A35.358000Z&peekView=expanded) (`72e042943ee0970f80ecc89ef386a9c2`)

**Confirmed close negatives (3):** [support-0081](http://localhost:3000/project/cartwheel-dev/traces?peek=7ac072bebbc53e65d9f9b17d8c0d3f0d&timestamp=2026-11-03T03%3A14%3A20.962000Z&peekView=expanded) (`7ac072bebbc53e65d9f9b17d8c0d3f0d`); [support-0077](http://localhost:3000/project/cartwheel-dev/traces?peek=0a9cb2002b18dca933c7f960116d26d3&timestamp=2026-11-03T03%3A14%3A07.642000Z&peekView=expanded) (`0a9cb2002b18dca933c7f960116d26d3`); [support-0078](http://localhost:3000/project/cartwheel-dev/traces?peek=99335b972c22988662cde0458672f9cc&timestamp=2026-11-03T03%3A14%3A11.380000Z&peekView=expanded) (`99335b972c22988662cde0458672f9cc`)

Supporting human annotation IDs are saved alongside these trace IDs in `analysis/state/patterns.json`. These origin-example counts are not substitutes for the full structured-label totals.

### unacknowledged_record_inconsistency

The reply reports conflicting information from the request or records without acknowledging the mismatch.

**Requirement:** SPEC.md RESP-3. **Likely evaluator:** LLM judge.

**Boundary:** Record inconsistency concerns handling conflicting evidence; lookup recovery concerns continuing after a failed lookup. Asking for genuinely necessary missing information is not automatically a failure.

**Human-confirmed origin/positive examples (3):** [support-0181](http://localhost:3000/project/cartwheel-dev/traces?peek=d318ec829780871df4f89faad0618b2f&timestamp=2026-11-03T03%3A20%3A34.570000Z&peekView=expanded) (`d318ec829780871df4f89faad0618b2f`); [support-0184](http://localhost:3000/project/cartwheel-dev/traces?peek=6de1497dfca68ab76882d95cd0682312&timestamp=2026-11-03T03%3A20%3A48.459000Z&peekView=expanded) (`6de1497dfca68ab76882d95cd0682312`); [support-0133](http://localhost:3000/project/cartwheel-dev/traces?peek=95bb3ea9b12f784985e855be0ecb9385&timestamp=2026-11-03T03%3A17%3A54.113000Z&peekView=expanded) (`95bb3ea9b12f784985e855be0ecb9385`)

**Confirmed close negatives (3):** [support-0182](http://localhost:3000/project/cartwheel-dev/traces?peek=e2295d79db96887bc5d3d32c685b3914&timestamp=2026-11-03T03%3A20%3A37.075000Z&peekView=expanded) (`e2295d79db96887bc5d3d32c685b3914`); [support-0186](http://localhost:3000/project/cartwheel-dev/traces?peek=2e4c04589f3f8a06d3b5815e85f13645&timestamp=2026-11-03T03%3A21%3A05.228000Z&peekView=expanded) (`2e4c04589f3f8a06d3b5815e85f13645`); [support-0183](http://localhost:3000/project/cartwheel-dev/traces?peek=a684f5142a81c33610974715c18938ae&timestamp=2026-11-03T03%3A20%3A40.145000Z&peekView=expanded) (`a684f5142a81c33610974715c18938ae`)

Supporting human annotation IDs are saved alongside these trace IDs in `analysis/state/patterns.json`. These origin-example counts are not substitutes for the full structured-label totals.

### unresolved_lookup_recovery

After an unsuccessful lookup, the agent stops without an appropriate recovery step or required escalation.

**Requirement:** SPEC.md SCOPE-1; ESC-3. **Likely evaluator:** LLM judge.

**Boundary:** Record inconsistency concerns handling conflicting evidence; lookup recovery concerns continuing after a failed lookup. Asking for genuinely necessary missing information is not automatically a failure.

**Human-confirmed origin/positive examples (4):** [support-0228](http://localhost:3000/project/cartwheel-dev/traces?peek=9182a3b19f36c45f85d936634ecf7dd5&timestamp=2026-11-03T03%3A24%3A14.721000Z&peekView=expanded) (`9182a3b19f36c45f85d936634ecf7dd5`); [support-0129](http://localhost:3000/project/cartwheel-dev/traces?peek=56b081308257554342e8d191df2ec1a8&timestamp=2026-11-03T03%3A17%3A43.326000Z&peekView=expanded) (`56b081308257554342e8d191df2ec1a8`); [support-0126](http://localhost:3000/project/cartwheel-dev/traces?peek=b034c71109228b0d99bca35e22562302&timestamp=2026-11-03T03%3A17%3A30.675000Z&peekView=expanded) (`b034c71109228b0d99bca35e22562302`); [support-0134](http://localhost:3000/project/cartwheel-dev/traces?peek=3cb93012c516b633f83de9b984411733&timestamp=2026-11-03T03%3A17%3A55.783000Z&peekView=expanded) (`3cb93012c516b633f83de9b984411733`)

**Confirmed close negatives (3):** [support-0186](http://localhost:3000/project/cartwheel-dev/traces?peek=2e4c04589f3f8a06d3b5815e85f13645&timestamp=2026-11-03T03%3A21%3A05.228000Z&peekView=expanded) (`2e4c04589f3f8a06d3b5815e85f13645`); [support-0135](http://localhost:3000/project/cartwheel-dev/traces?peek=498691ce49aeb35b3f5f388fc9ad54e5&timestamp=2026-11-03T03%3A17%3A57.835000Z&peekView=expanded) (`498691ce49aeb35b3f5f388fc9ad54e5`); [support-0128](http://localhost:3000/project/cartwheel-dev/traces?peek=e0bf34b2d3e4c1e401329e407bd6bfdf&timestamp=2026-11-03T03%3A17%3A35.320000Z&peekView=expanded) (`e0bf34b2d3e4c1e401329e407bd6bfdf`)

Supporting human annotation IDs are saved alongside these trace IDs in `analysis/state/patterns.json`. These origin-example counts are not substitutes for the full structured-label totals.

### missed_dispute_escalation

The user presents a dispute, but the agent does not escalate it to a human as required by ESC-3.

**Requirement:** SPEC.md ESC-3. **Likely evaluator:** LLM judge with tool-call check.

**Boundary:** A dispute itself requires human escalation, regardless of whether a lookup might help. This differs from failed lookup recovery, where the issue is stopping after an unsuccessful lookup. A successful escalation ticket and corresponding reply form a close negative.

**Human-confirmed origin/positive examples (3):** [support-0153](http://localhost:3000/project/cartwheel-dev/traces?peek=c611367f80ba05a4c3eff8ac730ac0fd&timestamp=2026-11-03T03%3A18%3A56.959000Z&peekView=expanded) (`c611367f80ba05a4c3eff8ac730ac0fd`); [support-0154](http://localhost:3000/project/cartwheel-dev/traces?peek=85174c01feaea42431cf81d815c0c0e3&timestamp=2026-11-03T03%3A18%3A58.488000Z&peekView=expanded) (`85174c01feaea42431cf81d815c0c0e3`); [support-0155](http://localhost:3000/project/cartwheel-dev/traces?peek=68c5c8a47d91117bd757d3a8f066f1e9&timestamp=2026-11-03T03%3A18%3A59.895000Z&peekView=expanded) (`68c5c8a47d91117bd757d3a8f066f1e9`)

**Confirmed close negatives (3):** [support-0146](http://localhost:3000/project/cartwheel-dev/traces?peek=fc655cd523d0b5c9986237126a1f821b&timestamp=2026-11-03T03%3A18%3A35.876000Z&peekView=expanded) (`fc655cd523d0b5c9986237126a1f821b`); [support-0149](http://localhost:3000/project/cartwheel-dev/traces?peek=b2eee584b9481c14a92a8c73d033faa0&timestamp=2026-11-03T03%3A18%3A44.509000Z&peekView=expanded) (`b2eee584b9481c14a92a8c73d033faa0`); [support-0150](http://localhost:3000/project/cartwheel-dev/traces?peek=3dc080f62f53d25a77b31d8a58ba4869&timestamp=2026-11-03T03%3A18%3A47.522000Z&peekView=expanded) (`3dc080f62f53d25a77b31d8a58ba4869`)

Supporting human annotation IDs are saved alongside these trace IDs in `analysis/state/patterns.json`. These origin-example counts are not substitutes for the full structured-label totals.

## Counts and sample fractions

These are **sample fractions**, not population prevalence estimates. Clustering, focused searches, role balancing and supplemental review deliberately change sample composition. Category fractions overlap because one trace can have multiple modes. The five detected label/reason conflicts were corrected with explicit human approval before these totals were computed.

| Mode | Present / required 100 | Required-sample fraction | Present / all 149 | All-reviewed fraction |
|---|---:|---:|---:|---:|
| unsupported_factual_claim | 46/100 | 46.0% | 67/149 | 45.0% |
| missing_policy_citation | 44/100 | 44.0% | 68/149 | 45.6% |
| unacknowledged_record_inconsistency | 43/100 | 43.0% | 63/149 | 42.3% |
| unresolved_lookup_recovery | 44/100 | 44.0% | 62/149 | 41.6% |
| missed_dispute_escalation | 40/100 | 40.0% | 57/149 | 38.3% |

## Final 15 traces and stability

All 15 final random selections have human-saved initial “No failure observed” notes. **Zero previously unseen consequential modes were recorded in this batch.** This reports observed discovery, not proof that failures or omitted categories cannot exist. Structured labeling can subsequently assign existing modes without discovering a new category. The exact notes and IDs are linked in `analysis/state/final_batch_assessment.json`; taxonomy and selection snapshots precede this batch.

## Taxonomy revision

The human approved expanding `unsupported_factual_claim` from its initial three-positive grouping to include unsupported policy advice and unsupported item identification, giving seven confirmed origin examples. The common corrective change is claim-to-evidence checking. The earlier grouping and the added example IDs are retained in `analysis/state/taxonomy_history.json`. Rather than creating separate categories solely to meet a quota, these related observations were merged under one definition.

## Rejected search suggestions and boundary

The human rejected the proposed scope failures in **support-0164** and **support-0165**, explicitly explaining: **“The agent refused the unrelated request and did not actually fulfill it.”** A general offer after refusal was insufficient to count as fulfilling an unrelated request. The original hypotheses, decisions and explanation are saved as `scope-boundary-*` entries in `analysis/state/suggestions.json`. The scope group remains provisional, with only one confirmed positive. Earlier dispute-escalation rejections were later corrected to failures and are not counted as current rejections.

## Comparison with AgentDebug

See [agentdebug_comparison.md](agentdebug_comparison.md), based on [AgentErrorTaxonomy Appendix A.2, Table 2](https://arxiv.org/html/2509.25370v1#A2). The comparison checks for omissions and naming ambiguities; mappings are interpretive rather than exact equivalences. No final mode was added solely because it appears in the published taxonomy. An expected not_found result after a guessed identifier was not treated as an infrastructure crash.

## Label consistency checks

Completeness, uniqueness and recorded synchronization checks pass: 149 reviewed traces × five final modes = 745 judgments, with no missing pairs. All approved origin-positive and close-negative example labels now match their confirmed status.

Five detected conflicts were corrected to Absent (0) with explicit human approval: lookup recovery for support-0128 and support-0135, and missed dispute escalation for support-0146, support-0149 and support-0150. Previous Present labels and their reasons remain in review_history.json. The corrected counts are used throughout this report.

This consistency check is not an exhaustive independent semantic audit of all 745 judgments. Initial open codes and later structured labels may differ because of re-review; saved binary judgments remain human-owned.

## Interface and reproducibility

See [interface_comparison.md](interface_comparison.md) for retained/changed design and limitations. The custom code is under `analysis/review_app/`; the supplied reference server and UI were not submitted unchanged. Normal review used live Langfuse. Isolated offline test fixtures were used only for testing, not as fallback production evidence.

Required local artifacts include the sample manifest, annotations, patterns, suggestions and five mode files under `analysis/state/labels/`. Additional histories, proposal records and final-batch assessment preserve provenance. No SPEC.md revision was made for these five modes; they refer to existing requirements.

## Verification and submission status

Fourteen isolated review-app/proposal/batch tests passed during this report preparation. They exercise approval gates, saved-label preservation, session grouping, persistence, score identity, stale-proposal handling and evidence-rule signals. These tests do not establish semantic correctness of every human judgment.

Workshop was skipped; its optional report/video segment is omitted. **Commit/push and the human-recorded continuous video of at most five minutes remain submission steps.** The report is populated from corrected saved state. No detected example/label conflicts remain.
