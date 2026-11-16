# Homework 4 review tool

From the repository root:

```bash
.venv/bin/python -m analysis.review_app.server --port 8021
```

Open http://127.0.0.1:8021. The tool reads `.env` locally and loads full final-scenario
traces from live Langfuse. It never exposes credentials to the browser and makes no
agent-model calls. Restart the server to refresh the live trace collection.

For a temporary outage only, explicitly use `--offline traces/support_traces.json`
and document the reason in `analysis/report/interface_comparison.md`. Offline labels
remain pending and must later be saved again in live mode to synchronize.

## Workflow

- **Review:** choose a session in the left column. Each turn retains its own stable
  trace identifier. Read the centered chronological conversation, expand tool
  results, highlight one evidence block, and save a note in the right margin.
  Annotation anchors retain block IDs, text offsets, and quotations. Long model
  requests (including system/history/tool schemas) and scenario grounding remain
  available in disclosures. Related tool inputs/results share a container.
- **No failure observed:** explicit free-text review result for one trace. Merely
  opening a trace does not mark it reviewed. Read until the first failure during
  initial open coding; formal labeling is a separate pass.
- **Map:** deterministic eight-cluster structural/role map, PCA projection. This
  is not a failure classifier. Every point opens its session and original trace.
- **Patterns:** reads human-grounded candidate/final taxonomy from
  `analysis/state/patterns.json`, including source annotation IDs and boundaries.
- **Labels:** unlocked only for modes with `status: "final"`. Present=1, absent=0.
  Saves a local pending record, synchronously upserts a stable Langfuse score ID,
  and marks it synced only after success. A failed sync stays pending; retrying
  reuses the score ID. Uses a separate judgment for each original trace ID.
- **Progress:** sample batches, notes, incomplete taxonomy judgments and separate
  AI suggestions. Explicit accept/reject with a reason; acceptance creates a human
  note, not an automatic formal label.

No sample, mode, failure annotation, or binary judgment is generated on launch.
The five preliminary inspections are usability observations, not failure labels.
Formal sampling is a later human-approved step. The app reads `sample_manifest.json`
(`picks` entries carry `trace_id`, `batch`, `reason`). Repeated trace IDs must never
be counted in more than one batch.

Existing `analysis/state/annotations.json`, `patterns.json`, `suggestions.json`, and
`labels/*.json` are preserved. Saves are atomic and edits/deletions/relabels retain
previous records in `review_history.json`. Free-text drafts are backed up in browser
localStorage; no binary label is silently inferred from a note.

To supply later agent proposals, update the existing state files atomically using
`analysis.helpers._state.write_json`; the app polls changes every five seconds.
Suggestions use `{id, trace_id, mode, quote, reason}`. Taxonomy entries use
`{name, status, definition, requirement_source, annotation_ids, positive_trace_ids,
negative_trace_ids, boundary, evaluator_type}`. The agent must not set a mode to
final without the student's explicit approval and evidence review.

## Verification

```bash
.venv/bin/python -m pytest tests/test_review_app.py -q
```

Tests use temporary files and stub score writers. Never write test annotations or
scores into the student's live review state. The original reference UI and server
remain unchanged. Remaining limitations: scripted offline sync requires retry,
inline selections must stay inside one evidence block, the map describes structure
rather than semantic meaning, and raw model-request disclosures are intentionally
verbose. This local single-user server must stay bound to 127.0.0.1.


## Batch labeling

Use **Batch labels → Load missing-label proposals**. The table covers every human-reviewed trace, including supplemental traces, and excludes existing binary judgments. Confirmed positive/negative taxonomy examples are identified separately from tentative absent proposals based on generic initial no-failure notes; other pairs remain undecided. Initial notes alone are not formal absent labels. Evidence expands to the selected turn and preceding session context; Open conversation provides the full review view.

Filter by category or scenario, review and edit decisions/reasons, select rows (or decided rows on the current 20-row page), explicitly attest review, then approve/save. Uncertain rows cannot be saved. Each approved row uses the existing label endpoint, stable score ID and Langfuse synchronization. Current labels are rechecked before saving to avoid overwriting judgments from another tab. On error, already saved rows remain saved and the user sees a partial-progress warning. Unsaved proposals are in-memory and disappear on reload; do not reload while saving. This feature does not run a model judge or auto-approve proposals.


### Prepared consolidated proposals

`analysis/state/label_proposals.json` stores one **unaccepted** proposal per missing reviewed-trace/final-mode pair. `proposals.py` uses confirmed evidence links plus transparent rules over session messages, policy identifiers, failed/empty lookup results, dates and escalation tickets. It is a triage assistant, not an LLM judge. Semantic support, mismatches beyond dates, and unresolved notes are highlighted for careful review. No initial no-failure note automatically becomes five absent labels.

The proposal endpoint excludes subsequently saved labels. Fingerprints detect changed taxonomy, notes or selected-turn messages; stale proposals require a new human decision. Batch approval rechecks staleness before writing. The UI sorts uncertain rows first, supports uncertainty/confirmed-example/lower-risk filters, and retains trace-specific reasons and session evidence. Generating/loading proposals never writes scores. The current upgraded server is port8023; use one review tab while saving to avoid conflicting edits.
