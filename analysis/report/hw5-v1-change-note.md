# HW5 v1 revision

The human retained all 11 Fail labels after reviewing v0 disagreements. All 11 are recorded as judge errors. No label, split, exact input export, or v0 prompt changed.

Changes: Require every claim and final clause to be checked against evidence, rather than validating only the main action.

Treat notification/update promises as separate claims, distinguish queued review from payment completion.

Require identity mappings and exhaustive evidence for absence/universal summaries.

Explicitly check named date fields, hedged specific guesses, and exceptions in permission statements.

Replace the store-name Fail few-shot with an already-labeled training refund-status/timing Fail.

Four few-shot examples are still training-only: two Pass and two Fail, including the boundary cases. Development disagreements informed general rules; their conversations, identifiers, and replies are not few-shot examples. The fixed test set remains untouched.

Next proposed run: gpt-4o-mini on the same 40 development conversations, requiring new explicit batch approval. This is revision 1 of at most 2. No v1 evaluation has run.
