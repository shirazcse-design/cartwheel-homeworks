"""Offline checks of immutable evidence and split isolation."""
import json
import shutil
import hashlib

import pytest

from analysis import run_judges as runner
from analysis.helpers.normalization import normalize_trace


@pytest.fixture
def prepared_state(tmp_path, monkeypatch):
    source = runner.STATE
    for name in ("hw5_trace_inputs.json", "hw5_export_manifest.json", "splits.json",
                 "hw5_split_manifest.json"):
        shutil.copy(source / name, tmp_path / name)
    shutil.copytree(source / "hw5_labels", tmp_path / "hw5_labels")
    monkeypatch.setattr(runner, "STATE", tmp_path)
    return tmp_path


def test_saved_split_is_reused_without_writes(prepared_state):
    before = {p.name: p.read_bytes() for p in prepared_state.iterdir() if p.is_file()}
    counts = runner.split_data()
    assert counts == {"train": {"Pass": 14, "Fail": 6},
                      "dev": {"Pass": 28, "Fail": 12},
                      "test": {"Pass": 27, "Fail": 12}}
    assert before == {p.name: p.read_bytes() for p in prepared_state.iterdir() if p.is_file()}


def test_modified_evidence_and_overlapping_split_are_rejected(prepared_state):
    inputs = prepared_state / "hw5_trace_inputs.json"
    original = inputs.read_bytes()
    inputs.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="inputs or labels changed"):
        runner.split_data()
    inputs.write_bytes(original)
    path = prepared_state / "splits.json"
    saved = json.loads(path.read_text())
    mode = saved[runner.MODE]
    mode["dev"].append(mode["train"][0])
    path.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="overlapping"):
        runner.split_data()


def test_export_has_evidence_without_review_fields():
    records = json.loads((runner.STATE / "hw5_trace_inputs.json").read_text())
    forbidden = {"label", "verdict", "reason", "scenario", "metadata", "human_accepted",
                 "proposal_reason", "annotations", "expected"}
    assert len(records) == len({r["trace_id"] for r in records}) == 99
    for record in records:
        assert set(record) == {"trace_id", "trace"}
        for message in record["trace"]:
            assert not forbidden.intersection(message)
        normalized = normalize_trace(record)
        assert normalized["text"]
        assert record["trace"][-1]["role"] == "assistant"
    # The capability judgment needs the original tool contract in judge-visible text.
    capability = next(r for r in records if r["trace_id"] == "fee7c87e365f0332fcd4339364c7d372")
    assert "Search your orders by product name" in normalize_trace(capability)["text"]


def test_prompt_examples_are_human_labeled_training_cases_only():
    manifest = json.loads((runner.STATE / "hw5_prompt_manifest.json").read_text())
    splits = json.loads((runner.STATE / "splits.json").read_text())[runner.MODE]
    labels = {r["trace_id"]: r for r in map(json.loads,
        (runner.STATE / "hw5_labels" / f"{runner.MODE}.jsonl").read_text().splitlines())}
    example_ids = {r["trace_id"] for r in manifest["examples"]}
    assert len(example_ids) == 4
    assert example_ids <= set(splits["train"])
    assert not example_ids.intersection(splits["dev"] + splits["test"])
    for example in manifest["examples"]:
        assert labels[example["trace_id"]]["human_accepted"]
        assert labels[example["trace_id"]]["verdict"] == example["human_verdict"]
    prompt = (runner.ROOT / manifest["prompt_path"]).read_bytes()
    assert hashlib.sha256(prompt).hexdigest() == manifest["prompt_sha256"]
    assert manifest["structured_output_schema"]["properties"]["result"]["enum"] == ["Pass", "Fail"]


def test_development_rejects_unmatched_approval_before_any_model_call(prepared_state):
    (prepared_state / "hw5_development_approval.json").write_text(json.dumps({
        "approved": True, "model": "gpt-4o-mini", "trace_count": 40,
        "trace_ids": [], "prompt_sha256": "wrong", "input_sha256": "wrong"}))
    prompt = runner.ROOT / "analysis/prompts" / f"{runner.MODE}-v0.txt"
    with pytest.raises(ValueError, match="Approval does not match"):
        runner.run_development(runner.MODE, prompt)


@pytest.mark.parametrize("unfreeze", [False, True])
def test_test_run_requires_matching_approval_and_frozen_selection(prepared_state, unfreeze):
    source = runner.ROOT / "analysis/state"
    selection = json.loads((source / "hw5_final_selection.json").read_text())
    judge_id = selection["judge_id"]
    (prepared_state / "hw5_final_selection.json").write_text(json.dumps(selection))
    judges = prepared_state / "judges"
    judges.mkdir()
    judge = json.loads((source / "judges" / f"{judge_id}.json").read_text())
    if unfreeze:
        judge["status"] = "draft"
    (judges / f"{judge_id}.json").write_text(json.dumps(judge))
    (prepared_state / "hw5_test_approval.json").write_text(json.dumps({
        "approved": True, "judge_id": judge_id, "model": "gpt-4o-mini",
        "trace_count": 39, "trace_ids": [], "prompt_sha256": "wrong"}))
    with pytest.raises(ValueError, match="already-frozen|Test approval does not match"):
        runner.run_test(judge_id)
