# Homework 4 interface comparison

## Preliminary human inspection

The student inspected five Homework 3 examples in Langfuse before building the
custom interface. These were usability inspections, not open-coding labels:

| Scenario | Content inspected | Student observation |
| --- | --- | --- |
| support-0048 | Cancellation, lookup and cancellation result | Nothing was difficult |
| support-0107 | Product-search input and result | Straightforward |
| support-0078 | Help-center retrieval and policy response | Policy results were easy to read |
| support-0136 | Two-turn account-change conversation | Straightforward |
| support-0185 | Three-turn purchase timeline and earlier evidence | Straightforward |

These five examples comprise eight individual trace IDs. No usability problem,
failure category, or binary judgment is inferred from the student's observations.
The student approved conversations in the center, notes on the right, tool calls
paired with results, and separate map/pattern/label/progress views.

## Retained design

Retained the reference's role-specific text blocks, paired tool-call/result
containers, expandable long structured results, and evidence-linked margin notes.
These make the actual model and tool evidence available without replacing it with
an AI summary. The original reference server and HTML remain unchanged.

## Changed design after inspecting the trace structure

The custom app groups original traces by `cartwheel.session_id` and orders turns by
timestamp. It preserves each original trace ID for annotations and labels rather
than merging a whole scenario into its first trace. The final collection contains
305 traces across 252 sessions: two scenarios were retried, so grouping only by
scenario ID would mix different attempts. The changed design also adds a session
navigator, explicit no-failure observations per trace, and a separate structured
labeling screen. This is an adaptation to observed trace structure and assignment
needs, not a claim that the student found Langfuse difficult.

## Source and persistence

The normal interface loads full records live from Langfuse, restricted to the final
scenario IDs. There was no offline fallback in the student's review workspace.
An explicitly offline, isolated test workspace was used solely to smoke-test a
disposable UI note; it is outside `analysis/state/` and is not a student annotation.

Human notes are mirrored under `analysis/state/annotations.json`. Binary judgments
are stored one per original trace and mode under `analysis/state/labels/`, then
synchronously upserted to Langfuse using stable score IDs. Failed writes remain
pending locally and are not counted as synchronized. Test score writes use stubs;
no fabricated test score or judgment was sent to live Langfuse.

## Remaining limitations

- A text-selection anchor must stay inside a single evidence block. Whole-turn
  notes are available when evidence spans several blocks.
- Browser drafts are backed up locally, but notes require the explicit Save
  observation action before they count as human review.
- The structural cluster map describes tools, length, retrieval and role, not
  semantic similarity or failure probability.
- Offline label synchronization requires retrying the saved judgment in live
  mode. A server restart refreshes the live trace collection.
- Narrow screens stack the notes beneath the conversation; a wide browser window
  is preferable for the approved side-by-side layout.

## Batch labeling extension

A batch-label table was added after the human reported repetitive manual effort. It excludes saved judgments, separates confirmed examples from rule-assisted proposals, highlights uncertain rows and allows explicit per-page review/approval. Evidence includes preceding session turns. Generation and loading do not write scores. Changed notes, definitions or selected-turn messages invalidate stale proposals. Human decisions are saved through the original synchronized label endpoint.

## Batch labeling extension

A batch-label table was added after the human reported repetitive manual effort. It excludes saved judgments, separates confirmed examples from rule-assisted proposals, highlights uncertain rows and allows explicit per-page review/approval. Evidence includes preceding session turns. Generation and loading do not write scores. Changed notes, definitions or selected-turn messages invalidate stale proposals. Human decisions are saved through the original synchronized label endpoint.

## Verification status

Fourteen isolated tests cover session/retry separation, persistence/history, suggestion decisions, final-mode gating, score identity, local HTTP checks, batch approval gates, preservation of existing judgments, evidence-rule signals and stale proposals. Browser checks verified batch loading, uncertainty filtering and the review-attestation gate without creating test scores. Normal live loading returned 305 traces across 252 sessions. The actual review is complete for 100 required selections plus 49 supplemental traces, with 745 synchronized structured judgments. Five detected contradictions between saved labels and confirmed close-negative evidence were corrected with explicit human approval and resynchronized; previous values remain in review history.
