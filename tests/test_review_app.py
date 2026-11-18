"""Review-tool regression checks. Never use live Langfuse or student state."""
import json
from pathlib import Path
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest
from analysis.review_app.server import Store, Handler, ThreadingHTTPServer, prepare, write_json, score_writer


def trace(tid, session='session-a', timestamp='2026-11-03T03:00:00Z'):
    return {'id': tid, 'timestamp': timestamp,
            'metadata': {'attributes': {'cartwheel.scenario_id': 'support-test',
                         'cartwheel.session_id': session, 'cartwheel.user_role': 'shopper'}},
            'input': [{'role': 'user', 'parts': [{'type': 'text', 'content': 'Help with my order'}]}],
            'output': [{'role': 'assistant', 'parts': [{'type': 'text', 'content': 'Please clarify'}]}],
            'observations': []}


@pytest.fixture
def store(tmp_path):
    scenarios = {'support-test': {'id': 'support-test', 'scenario_group': 'coverage', 'tuple': {'intent': 'order_status'}}}
    traces, sessions = prepare([trace('a'*32)], scenarios)
    return Store(tmp_path, traces, sessions, {'kind': 'test'})


def test_session_grouping_keeps_turn_ids_and_retry_sessions_separate():
    raw = [trace('b'*32, timestamp='2026-11-03T03:00:02Z'), trace('a'*32), trace('c'*32, session='retry')]
    ts, sessions = prepare(raw, {'support-test': {}})
    assert sessions == {'session-a': ['a'*32, 'b'*32], 'retry': ['c'*32]}
    assert len(ts) == 3
    assert 'scenario_id' in ts['a'*32]['meta']


def test_note_edit_and_delete_preserve_history(store):
    anchor = {'quote': 'Help', 'block_id': 'a'*32+'-0', 'start': 0, 'end': 4}
    first = store.save_note({'trace_id': 'a'*32, 'note': 'Needs clarification', 'anchor': anchor})
    updated = store.save_note({**first, 'note': 'Clarification requested'})
    assert updated['id'] == first['id'] and updated['anchor'] == anchor
    assert store.data()['annotations'][0]['note'] == 'Clarification requested'
    store.delete_note({'id': first['id']})
    assert store.data()['annotations'] == []
    history = json.loads((store.state/'review_history.json').read_text())
    assert [h['action'] for h in history] == ['edit', 'delete']


def test_browsing_does_not_create_annotations_or_samples(store):
    summary = store.summary()
    assert summary['annotations'] == [] and summary['manifest']['picks'] == []
    assert not list(store.state.glob('*.json'))


def test_judge_review_exposes_development_only_without_changing_labels(store):
    tid = 'a' * 32
    write_json(store.state / 'splits.json', {'example': {'dev': [tid], 'test': ['held-out']}})
    doc = {'mode': 'example', 'split': 'dev', 'rows': [
        {'trace_id': tid, 'human_verdict': 'Fail', 'judge_verdict': 'Pass'}]}
    write_json(store.state / 'hw5_development_review.json', doc)
    assert store.judge_review() == doc
    assert store.labels() == []
    doc['rows'].append({'trace_id': 'held-out'})
    write_json(store.state / 'hw5_development_review.json', doc)
    with pytest.raises(ValueError, match='non-development'):
        store.judge_review()


def test_judge_review_rejects_test_snapshot(store):
    write_json(store.state / 'hw5_development_review.json', {'split': 'test'})
    with pytest.raises(ValueError, match='Only development'):
        store.judge_review()


def test_suggestion_rejection_does_not_create_human_note(store):
    write_json(store.state/'suggestions.json', [{'id': 's', 'trace_id': 'a'*32, 'quote': 'Help'}])
    decision = store.suggestion_decision({'id': 's', 'decision': 'reject', 'reason': 'No evidence of this failure'})
    assert decision['decided_by'] == 'human'
    assert not store.data()['annotations']
    with pytest.raises(ValueError):
        store.suggestion_decision({'id': 's', 'decision': 'accept', 'reason': 'Changed'})


def test_suggestion_acceptance_creates_note_but_no_binary_label(store):
    write_json(store.state/'suggestions.json', [{'id': 's', 'trace_id': 'a'*32, 'quote': 'Help'}])
    store.suggestion_decision({'id': 's', 'decision': 'accept', 'reason': 'My observation'})
    assert len(store.data()['annotations']) == 1 and store.labels() == []


def make_final(store):
    write_json(store.state/'patterns.json', {'modes': [{'name': 'example_mode', 'status': 'final', 'definition': 'Test only'}]})


def test_labels_require_final_mode_and_explicit_binary_judgment(store):
    with pytest.raises(ValueError):
        store.save_label({'trace_id': 'a'*32, 'mode': 'example_mode', 'label': 1, 'reason': 'Evidence'})
    make_final(store)
    with pytest.raises(ValueError):
        store.save_label({'trace_id': 'a'*32, 'mode': 'example_mode', 'label': True, 'reason': 'Evidence'})


def test_failed_sync_stays_pending_and_retry_reuses_score_id(store):
    make_final(store)
    seen = []
    def fail(r):
        seen.append(r['score_id'])
        raise OSError('Offline')
    store.writer = fail
    payload = {'trace_id': 'a'*32, 'mode': 'example_mode', 'label': 1, 'reason': 'Evidence'}
    with pytest.raises(RuntimeError):
        store.save_label(payload)
    assert store.labels()[0]['sync_status'] == 'pending'
    store.writer = lambda r: seen.append(r['score_id'])
    assert store.save_label(payload)['sync_status'] == 'synced'
    assert len(store.labels()) == 1 and seen[0] == seen[1]


def test_score_writer_uses_synchronous_api_and_exact_trace_id(store):
    from types import SimpleNamespace
    captured = []
    client = SimpleNamespace(api=SimpleNamespace(score=SimpleNamespace(create=lambda **kw: captured.append(kw['request']))))
    make_final(store)
    store.writer = score_writer(client)
    store.save_label({'trace_id': 'a'*32, 'mode': 'example_mode', 'label': 0, 'reason': 'Absent'})
    assert captured[0].trace_id == 'a'*32 and captured[0].value == 0
    assert captured[0].id == store.labels()[0]['score_id']


def test_http_origin_rejection_and_save_roundtrip(store):
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.store = store
    thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
    base = 'http://127.0.0.1:'+str(server.server_port)
    try:
        assert json.load(urlopen(base+'/api/bootstrap'))['trace_count'] == 1
        payload = json.dumps({'trace_id': 'a'*32, 'kind': 'no_failure_observed', 'note': 'No failure observed.'}).encode()
        req = Request(base+'/api/note', data=payload, headers={'Content-Type':'application/json','Origin':'https://external.example'})
        with pytest.raises(HTTPError) as error:
            urlopen(req)
        assert error.value.code == 403
        assert store.data()['annotations'] == []
        req = Request(base+'/api/note', data=payload, headers={'Content-Type':'application/json','Origin':base})
        saved = json.load(urlopen(req))
        assert saved['kind'] == 'no_failure_observed'
        assert len(store.data()['annotations']) == 1
    finally:
        server.shutdown();server.server_close();thread.join()
