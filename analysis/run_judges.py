"""Homework 5 runner. Part B is offline; later judge calls require approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path

from analysis.helpers import split_labels

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "analysis/state"
MODE = "unsupported_factual_claim"
SOURCE = ROOT.parent / "work/hw4/live-review-corpus.json"


def _bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _save_once(path, data):
    """Permit identical reruns, but never silently replace prepared evidence."""
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Existing artifact differs; refusing replacement: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _original_prefix(record):
    """Recover original system, tool contracts, and history before this turn."""
    generations = sorted(
        (o for o in record["observations"] if o.get("type") == "GENERATION"),
        key=lambda o: o.get("start_time", ""),
    )
    if not generations or not isinstance(generations[0].get("input"), dict):
        raise ValueError(f"Missing original request: {record['trace_id']}")
    request = generations[0]["input"]
    messages = request.get("messages", [])
    user_text = next(m["text"] for m in record["trace"] if m["role"] == "user")
    matches = [i for i, m in enumerate(messages) if m.get("role") == "user"
               and "\n".join(p.get("content", "") for p in m.get("parts", [])
                              if p.get("type") == "text") == user_text]
    if not matches:
        raise ValueError(f"Cannot locate current turn in original request: {record['trace_id']}")
    prefix = []
    # The last matching user message is the current turn, even if a user repeats text.
    for message in messages[:matches[-1]]:
        for part in message.get("parts", []):
            if part.get("type") == "text" and part.get("content"):
                prefix.append({"role": message["role"], "text": part["content"]})
            elif part.get("type") == "tool_call":
                prefix.append({"role": "tool_call", "name": part["name"],
                               "arguments": part.get("arguments", {})})
            elif part.get("type") == "tool_call_response":
                prefix.append({"role": "tool_result", "content": part.get("response"),
                               "text": "Original prior tool response: " + str(part.get("response"))})
            else:
                raise ValueError(f"Unhandled original message part: {part.get('type')}")
    definitions = request.get("tools", [])
    if definitions:
        prefix.insert(1 if prefix and prefix[0]["role"] == "system" else 0,
                      {"role": "tool_definition", "text": json.dumps(definitions, ensure_ascii=False)})
    return prefix


def prepare_inputs():
    """Export only approved independent representatives and their observed evidence."""
    corpus = json.loads(SOURCE.read_text())
    audit = json.loads((ROOT / "analysis/report/hw5-independence-review.json").read_text())
    decisions = json.loads((STATE / "hw5_review_decisions.json").read_text())
    by_id = {d["trace_id"]: d for d in decisions["decisions"]}
    records, labels, sessions = [], [], set()
    for group in audit["groups"]:
        tid = group["representative_trace_id"]
        decision, original = by_id[tid], corpus[tid]
        if not decision.get("human_accepted") or decision["verdict"] not in {"Pass", "Fail"}:
            raise ValueError(f"Unapproved or unresolved label: {tid}")
        if decision["verdict"] != group["verdict"]:
            raise ValueError(f"Independence audit is stale for {tid}")
        session = original["meta"]["session_id"]
        if session in sessions:
            raise ValueError(f"More than one representative from conversation {session}")
        sessions.add(session)
        trace = _original_prefix(original)
        for message in original["trace"]:
            # Explicit allowlist: never copy scenario metadata or review annotations.
            clean = {k: message[k] for k in ("role", "text", "name", "arguments", "content")
                     if k in message}
            if clean["role"] == "tool_result":
                clean["text"] = clean.get("name", "tool") + ": " + json.dumps(clean.get("content"), ensure_ascii=False)
            trace.append(clean)
        if not trace or trace[-1].get("role") != "assistant":
            raise ValueError(f"Missing final assistant answer: {tid}")
        records.append({"trace_id": tid, "trace": trace})
        labels.append({"trace_id": tid, "mode": MODE,
                       "label": int(decision["verdict"] == "Pass"),
                       "verdict": decision["verdict"], "human_accepted": True,
                       "reason": decision.get("reason", decision.get("proposal_reason", ""))})
    records.sort(key=lambda r: r["trace_id"])
    labels.sort(key=lambda r: r["trace_id"])
    counts = Counter(r["verdict"] for r in labels)
    if min(counts["Pass"], counts["Fail"]) < 30:
        raise ValueError(f"Need at least 30 approved cases per class: {counts}")
    inputs_path = STATE / "hw5_trace_inputs.json"
    label_path = STATE / "hw5_labels" / f"{MODE}.jsonl"
    input_data = _bytes(records)
    label_data = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in labels)
    # Check both before writing either, including on interrupted reruns.
    for path, data in [(inputs_path, input_data), (label_path, label_data)]:
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"Existing artifact differs; refusing replacement: {path}")
    _save_once(inputs_path, input_data)
    _save_once(label_path, label_data)
    manifest = {"mode": MODE, "input_path": str(inputs_path.relative_to(ROOT)),
                "input_sha256": _hash(input_data), "labels_sha256": _hash(label_data),
                "source_sha256": _hash(SOURCE.read_bytes()), "counts": dict(counts),
                "conversation_count": len(sessions), "labels_in_inputs": False}
    _save_once(STATE / "hw5_export_manifest.json", _bytes(manifest))
    os.environ["CARTWHEEL_JUDGE_TRACE_SOURCE"] = str(inputs_path)
    return manifest


def split_data(mode=MODE):
    """Create one stratified split; subsequent invocations only verify and reuse it."""
    if mode != MODE:
        raise ValueError("This runner prepares only the human-approved mode")
    manifest = json.loads((STATE / "hw5_export_manifest.json").read_text())
    inputs = STATE / "hw5_trace_inputs.json"
    labels_path = STATE / "hw5_labels" / f"{mode}.jsonl"
    if _hash(inputs.read_bytes()) != manifest["input_sha256"] or _hash(labels_path.read_bytes()) != manifest["labels_sha256"]:
        raise ValueError("Prepared inputs or labels changed; refusing to split")
    labels = {r["trace_id"]: r for r in map(json.loads, labels_path.read_text().splitlines())}
    records = json.loads(inputs.read_text())
    ids = {r["trace_id"] for r in records}
    if ids != set(labels):
        raise ValueError("Input and label IDs differ")
    path = STATE / "splits.json"
    before = json.loads(path.read_text()) if path.exists() else {}
    if mode in before:
        saved = before[mode]
        assignment = {name: saved[name] for name in ("train", "dev", "test")}
        if saved.get("seed") != 7 or saved.get("fractions") != [.2, .4, .4]:
            raise ValueError("Existing mode has a different split configuration")
    else:
        _save_once(STATE / "hw5_before_splits.json", _bytes(before))
        from analysis.helpers import _state
        if _state.state_root().resolve() != STATE.resolve():
            raise ValueError("Analysis state override does not match this runner")
        assignment = split_labels(mode, fractions=(.2, .4, .4), seed=7,
                                  min_per_class=10, eligible_trace_ids=sorted(ids))
    combined = [tid for values in assignment.values() for tid in values]
    if len(combined) != len(set(combined)) or set(combined) != ids:
        raise ValueError("Split is overlapping or does not cover exactly the exported dataset")
    after = json.loads(path.read_text())
    if any(after[k] != v for k, v in before.items() if k != mode):
        raise ValueError("An existing unrelated mode was changed")
    counts = {name: dict(Counter(labels[tid]["verdict"] for tid in values))
              for name, values in assignment.items()}
    for name in ("dev", "test"):
        if min(counts[name].get("Pass", 0), counts[name].get("Fail", 0)) < 10:
            raise ValueError(f"Insufficient {name} class counts")
    _save_once(STATE / "hw5_split_manifest.json", _bytes({
        "mode": mode, "seed": 7, "fractions": [.2, .4, .4], "counts": counts,
        "input_sha256": manifest["input_sha256"], "labels_sha256": manifest["labels_sha256"],
        "mode_split_sha256": _hash(_bytes(after[mode])), "disjoint": True,
    }))
    return counts


def run_development(mode, prompt_path):
    """Run only an explicitly approved dev batch, resuming its saved judge ID."""
    if mode != MODE:
        raise ValueError("Unapproved mode")
    split_data(mode)  # Verify immutable evidence and reuse the saved split.
    prompt_path = Path(prompt_path).resolve()
    prompt = prompt_path.read_text()
    approval_path = STATE / "hw5_development_approval.json"
    approval = json.loads(approval_path.read_text())
    ids = json.loads((STATE / "splits.json").read_text())[mode]["dev"]
    export = json.loads((STATE / "hw5_export_manifest.json").read_text())
    if (approval.get("approved") is not True or approval.get("model") != "gpt-4o-mini"
            or approval.get("trace_ids") != ids or approval.get("trace_count") != len(ids)
            or approval.get("prompt_sha256") != _hash(prompt.encode())
            or approval.get("input_sha256") != export["input_sha256"]):
        raise ValueError("Approval does not match this model, prompt, input export, and dev batch")
    from observability.instrument import load_env
    load_env()
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not configured locally")
    os.environ["CARTWHEEL_JUDGE_TRACE_SOURCE"] = str(STATE / "hw5_trace_inputs.json")
    # Keep runtime caches in a writable temp directory; never change HOME.
    os.environ.setdefault("DOCETL_HOME_DIR", "/private/tmp/cartwheel-hw5-runtime")
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/cartwheel-hw5-runtime/matplotlib")
    from analysis.helpers import register_judge, run_judge, judge_alignment
    import docetl  # Validate runtime availability before registering a version.
    if approval.get("judge_id"):
        judge_id = approval["judge_id"]
        judge = json.loads((STATE / "judges" / f"{judge_id}.json").read_text())
        if judge["prompt_text"] != prompt or judge["model"] != approval["model"]:
            raise ValueError("Saved judge differs from approved prompt/model")
    else:
        record = register_judge(mode, prompt, judge_model=approval["model"])
        judge_id = record["judge_id"]
        approval["judge_id"] = judge_id
        approval["started_at"] = datetime.now(timezone.utc).isoformat()
        approval_path.write_bytes(_bytes(approval))
    print(f"Running approved development judge {judge_id}: {len(ids)} traces, checkpoints of 10", flush=True)
    run_judge(judge_id, split="dev", batch_size=10)
    report_path = ROOT / "analysis/report" / f"dev-{judge_id}.json"
    # Avoid appending a duplicate helper iteration row on a completed rerun.
    metrics = json.loads(report_path.read_text()) if report_path.exists() else judge_alignment(judge_id, split="dev")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(_bytes(metrics))
    approval.update({"status": "complete", "completed_at": datetime.now(timezone.utc).isoformat()})
    approval_path.write_bytes(_bytes(approval))
    return metrics


def run_test(judge_id):
    """Evaluate the already-frozen final judge once; interruptions reuse its cache."""
    split_data(MODE)
    selection = json.loads((STATE / "hw5_final_selection.json").read_text())
    approval_path = STATE / "hw5_test_approval.json"
    approval = json.loads(approval_path.read_text())
    judge = json.loads((STATE / "judges" / f"{judge_id}.json").read_text())
    ids = json.loads((STATE / "splits.json").read_text())[MODE]["test"]
    export = json.loads((STATE / "hw5_export_manifest.json").read_text())
    if (selection["judge_id"] != judge_id or judge["status"] != "frozen"
            or selection["status"] != "frozen"):
        raise ValueError("Only the human-selected, already-frozen judge can run test")
    if (approval.get("approved") is not True or approval.get("judge_id") != judge_id
            or approval.get("model") != judge["model"] or judge["model"] != "gpt-4o-mini"
            or approval.get("trace_ids") != ids or approval.get("trace_count") != len(ids)
            or approval.get("prompt_sha256") != _hash(judge["prompt_text"].encode())
            or approval.get("prompt_sha256") != selection["prompt_sha256"]
            or approval.get("input_sha256") != export["input_sha256"]):
        raise ValueError("Test approval does not match frozen prompt, model, inputs, and test IDs")
    from analysis.helpers import run_judge, judge_alignment
    report_path = ROOT / "analysis/report" / f"test-{judge_id}.json"
    if report_path.exists() and approval.get("status") == "complete":
        return judge_alignment(judge_id, split="test")
    from observability.instrument import load_env
    load_env()
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not configured locally")
    os.environ["CARTWHEEL_JUDGE_TRACE_SOURCE"] = str(STATE / "hw5_trace_inputs.json")
    os.environ.setdefault("DOCETL_HOME_DIR", "/private/tmp/cartwheel-hw5-runtime")
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/cartwheel-hw5-runtime/matplotlib")
    approval["status"] = "running"
    approval.setdefault("started_at", datetime.now(timezone.utc).isoformat())
    approval_path.write_bytes(_bytes(approval))
    print(f"Running approved frozen judge {judge_id}: {len(ids)} test traces, checkpoints of 10", flush=True)
    # No registration, reshuffling, refreezing, or prompt changes on a resume.
    run_judge(judge_id, split="test", batch_size=10)
    metrics = judge_alignment(judge_id, split="test")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(_bytes(metrics))
    approval.update({"status": "complete", "completed_at": datetime.now(timezone.utc).isoformat()})
    approval_path.write_bytes(_bytes(approval))
    return metrics


def recalculate_test_metrics(judge_id):
    """Recompute metrics from saved labels/predictions only; no model calls."""
    from analysis.helpers import judge_alignment
    selection = json.loads((STATE / "hw5_final_selection.json").read_text())
    if selection["judge_id"] != judge_id:
        raise ValueError("Use the selected final judge")
    return judge_alignment(judge_id, split="test")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "split", "part-b", "dev", "test", "test-metrics"])
    parser.add_argument("--prompt", type=Path, default=ROOT / "analysis/prompts" / f"{MODE}-v0.txt")
    parser.add_argument("--judge-id", default=f"{MODE}-v1")
    args = parser.parse_args()
    if args.action in {"prepare", "part-b"}:
        print(json.dumps(prepare_inputs(), indent=2))
    if args.action in {"split", "part-b"}:
        print(json.dumps(split_data(), indent=2))
    if args.action == "dev":
        print(json.dumps(run_development(MODE, args.prompt), indent=2))
    if args.action == "test":
        print(json.dumps(run_test(args.judge_id), indent=2))
    if args.action == "test-metrics":
        print(json.dumps(recalculate_test_metrics(args.judge_id), indent=2))
