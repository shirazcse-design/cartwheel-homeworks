# AgentDebug comparison

Source: [AgentErrorTaxonomy, Appendix A.2 Table 2](https://arxiv.org/html/2509.25370v1#A2), inspected November 15, 2026.

The paper distinguishes memory, reflection, planning, action, and system failures. The following are interpretive similarities, not claims of exact equivalence:

| Cartwheel mode | Nearest published concept |
|---|---|
| unsupported_factual_claim | Hallucination / filling gaps with fabricated information |
| missing_policy_citation | Constraint ignorance; Cartwheel-specific attribution requirement |
| unacknowledged_record_inconsistency | Outcome misinterpretation / insufficient evidence checking |
| unresolved_lookup_recovery | Retrieval failure or unreasonable parameters followed by inadequate recovery |
| missed_dispute_escalation | Constraint ignorance / required action omitted |

The comparison prompts a check for infrastructure failures. A not_found response to an invented identifier is expected tool behavior, not proof of a system crash. Do not introduce a system-error mode without human-confirmed evidence. Likewise, the sports-trivia example remains a provisional scope group with insufficient positive examples. No new final mode was added solely because it appears in AgentDebug.

The Cartwheel names remain tied to human observations and SPEC requirements. Proposed evaluator types remain subject to final taxonomy review. This comparison does not establish hidden model reasoning or causal mechanisms.
