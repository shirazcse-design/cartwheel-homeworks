"""Run with: .venv/bin/python -m analysis.review_app.server --port 8021.

Live Langfuse is the default. --offline PATH is explicit, never an automatic
fallback. Run tests against temporary state, never the student's judgments.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
from urllib.parse import parse_qs, urlparse, urlencode
import uuid

from analysis.helpers.normalization import normalize_trace
from analysis.helpers._state import write_json

ROOT = Path(__file__).resolve().parents[2]
UI = Path(__file__).parent


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def fetch_live(scenario_ids):
    from langfuse import Langfuse
    from scenarios.export_langfuse import _attribute_scenario_id, _jsonable, _scenario_id
    client = Langfuse()
    summaries = []
    page = 1
    while True:
        batch = list(client.api.trace.list(page=page, limit=100).data or [])
        summaries.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    # Summary metadata can be absent; full trace metadata is authoritative.
    candidates = [t for t in summaries if not _attribute_scenario_id(t.metadata)
                  or _attribute_scenario_id(t.metadata) in scenario_ids]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda t: _jsonable(client.api.trace.get(t.id)), candidates))
    return [r for r in records if _scenario_id(r) in scenario_ids], client


def prepare(raw, scenarios):
    """Normalize individually: do NOT merge retry sessions by scenario id."""
    traces = {}
    sessions = defaultdict(list)
    for item in raw:
        t = normalize_trace(item)
        sid = t['meta'].get('scenario_id')
        if sid not in scenarios:
            continue
        t['scenario'] = {k: v for k, v in scenarios[sid].items()
                         if k not in ('opening_message', 'followups')}
        t['permalink'] = 'http://localhost:3000/project/cartwheel-dev/traces?' + urlencode(
            {'peek': t['id'], 'timestamp': t['timestamp'], 'peekView': 'expanded'})
        traces[t['id']] = t
        session = t['meta'].get('session_id') or 'trace:' + t['id']
        sessions[session].append(t['id'])
    for ids in sessions.values():
        ids.sort(key=lambda tid: (traces[tid]['timestamp'] or '', tid))
    return traces, dict(sessions)


def make_graph(traces):
    """Structural clusters only: no predicted failures, labels or answer keys."""
    import numpy as np
    ids = sorted(traces)
    if not ids:
        return {'nodes': [], 'clusters': []}
    vectors = []
    roles = ['shopper', 'merchant', 'support']
    for tid in ids:
        t = traces[tid]
        vectors.append([t['features'][k] for k in ('tool_call_count', 'distinct_tools', 'tokens', 'has_retrieval')]
                       + [int(t['meta'].get('role') == r) for r in roles])
    x = np.array(vectors, dtype=float)
    x = (x - x.mean(axis=0)) / np.where(x.std(axis=0) > 0, x.std(axis=0), 1)
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    xy = x @ vt[:2].T
    if xy.shape[1] < 2:
        xy = np.pad(xy, ((0, 0), (0, 2 - xy.shape[1])))
    k = min(8, len(ids))
    rng = np.random.default_rng(20261112)
    centers = x[rng.choice(len(x), k, replace=False)].copy()
    for _ in range(40):
        assignment = ((x[:, None] - centers) ** 2).sum(axis=2).argmin(axis=1)
        updated = np.array([x[assignment == j].mean(axis=0) if (assignment == j).any() else centers[j] for j in range(k)])
        if np.allclose(centers, updated):
            break
        centers = updated
    nodes = [{'id': tid, 'x': float(xy[i, 0]), 'y': float(xy[i, 1]),
              'cluster': int(assignment[i]), 'distance': float(np.linalg.norm(x[i] - centers[assignment[i]]))}
             for i, tid in enumerate(ids)]
    return {'nodes': nodes, 'clusters': [{'id': j, 'count': int((assignment == j).sum())} for j in range(k)],
            'method': 'Standardized structural/role features; deterministic KMeans (8 clusters), PCA projection. No quality labels used.'}


class Store:
    def __init__(self, state, traces, sessions, source, writer=None):
        self.state = Path(state)
        self.traces, self.sessions, self.source = traces, sessions, source
        self.writer = writer
        self.lock = threading.RLock()
        self.graph = make_graph(traces)

    def data(self):
        anns = read(self.state / 'annotations.json', {'annotations': []})
        patterns = read(self.state / 'patterns.json', {'modes': []})
        suggestions = read(self.state / 'suggestions.json', [])
        return {'annotations': anns.get('annotations', []) if isinstance(anns, dict) else anns,
                'patterns': patterns, 'suggestions': suggestions,
                'manifest': read(self.state / 'sample_manifest.json', {'picks': [], 'status': 'Not selected yet'})}

    def label_proposals(self):
        from analysis.review_app.proposals import fingerprint
        doc = read(self.state / 'label_proposals.json', {'rows': []})
        done = {(r['trace_id'], r['mode']) for r in self.labels()}
        data = self.data()
        modes = {m['name']: m for m in self.modes() if m.get('status') == 'final'}
        rows = []
        for proposal in doc.get('rows', []):
            tid, mode = proposal.get('trace_id'), proposal.get('mode')
            if (tid, mode) in done or tid not in self.traces or mode not in modes:
                continue
            row = dict(proposal)
            notes = [a for a in data['annotations'] if a['trace_id'] == tid]
            row['stale'] = (row.get('taxonomy_fingerprint') != fingerprint(modes[mode])
                            or row.get('notes_fingerprint') != fingerprint(notes)
                            or row.get('trace_fingerprint') != fingerprint(self.traces[tid]['trace']))
            rows.append(row)
        return {**doc, 'rows': rows}

    def labels(self):
        return [r for p in sorted((self.state / 'labels').glob('*.json'))
                for r in read(p, []) if isinstance(r, dict) and r.get('trace_id') in self.traces]

    def modes(self):
        p = self.data()['patterns']
        return p.get('modes', []) if isinstance(p, dict) else p

    def summary(self):
        data = self.data()
        data.update({'source': self.source, 'can_sync': self.writer is not None,
                     'labels': self.labels(), 'trace_count': len(self.traces), 'sessions': []})
        for session, ids in self.sessions.items():
            first = self.traces[ids[0]]
            data['sessions'].append({'id': session, 'trace_ids': ids, 'scenario_id': first['meta']['scenario_id'],
                                     'role': first['meta'].get('role'), 'timestamp': first['timestamp'],
                                     'group': first['scenario']['scenario_group'],
                                     'intent': first['scenario']['tuple']['intent']})
        data['sessions'].sort(key=lambda s: (s['scenario_id'], s['timestamp']))
        return data

    def save_note(self, payload):
        tid = payload.get('trace_id')
        if tid not in self.traces:
            raise ValueError('Unknown trace')
        note = str(payload.get('note', '')).strip()
        if not note:
            raise ValueError('Write an observation or choose No failure observed')
        kind = payload.get('kind', 'observation')
        if kind not in ('observation', 'no_failure_observed'):
            raise ValueError('Invalid observation kind')
        anchor = payload.get('anchor') or {}
        if anchor and (not isinstance(anchor, dict) or not isinstance(anchor.get('quote'), str)):
            raise ValueError('Invalid quote anchor')
        anns_doc = read(self.state / 'annotations.json', {'annotations': []})
        anns = anns_doc.get('annotations', []) if isinstance(anns_doc, dict) else anns_doc
        aid = payload.get('id') or str(uuid.uuid4())
        old = next((a for a in anns if a.get('id') == aid), None)
        if old and old['trace_id'] != tid:
            raise ValueError('Cannot move an annotation to a different trace')
        if old:
            history = read(self.state / 'review_history.json', [])
            write_json(self.state / 'review_history.json', history + [{'action': 'edit', 'at': now(), 'previous': old}])
        record = {'id': aid, 'trace_id': tid, 'note': note, 'kind': kind, 'anchor': anchor,
                  'author': 'human', 'created_at': old['created_at'] if old else now(), 'updated_at': now()}
        anns = [a for a in anns if a.get('id') != aid] + [record]
        write_json(self.state / 'annotations.json', {'annotations': anns})
        return record

    def delete_note(self, payload):
        doc = self.data()['annotations']
        old = next((a for a in doc if a.get('id') == payload.get('id')), None)
        if old is None:
            raise ValueError('Unknown annotation')
        history = read(self.state / 'review_history.json', [])
        write_json(self.state / 'review_history.json', history + [{'action': 'delete', 'at': now(), 'previous': old}])
        write_json(self.state / 'annotations.json', {'annotations': [a for a in doc if a['id'] != old['id']]})
        return {'ok': True}

    def suggestion_decision(self, p):
        suggestions = self.data()['suggestions']
        if not isinstance(suggestions, list):
            raise ValueError('Suggestions must be a list')
        s = next((s for s in suggestions if s.get('id') == p.get('id')), None)
        if not s:
            raise ValueError('Unknown suggestion')
        if p.get('decision') not in ('accept', 'reject') or not str(p.get('reason', '')).strip():
            raise ValueError('Choose accept/reject and provide your reason')
        if s.get('decision') in ('accept', 'reject'):
            raise ValueError('Suggestion already decided; preserve the existing review history')
        if p['decision'] == 'accept':
            ann = self.save_note({'trace_id': s['trace_id'], 'note': p['reason'],
                                  'anchor': {'quote': s.get('quote', s.get('text', ''))}})
            s['annotation_id'] = ann['id']
        s.update({'decision': p['decision'], 'reason': p['reason'], 'decided_at': now(), 'decided_by': 'human'})
        write_json(self.state / 'suggestions.json', suggestions)
        return s

    def save_label(self, p):
        tid, mode, label = p.get('trace_id'), p.get('mode'), p.get('label')
        if tid not in self.traces or type(label) is not int or label not in (0, 1):
            raise ValueError('Select a trace and present (1) or absent (0)')
        modes = self.modes()
        if not any(m.get('name') == mode and m.get('status') == 'final' for m in modes):
            raise ValueError('Labels are available only for human-confirmed final modes')
        if not re.fullmatch(r'[a-z][a-z0-9_]*', mode):
            raise ValueError('Invalid mode name')
        if not str(p.get('reason', '')).strip():
            raise ValueError('Provide evidence/reason for this judgment')
        path = self.state / 'labels' / (mode + '.json')
        rows = read(path, [])
        score_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'cartwheel-hw4:' + tid + ':' + mode))
        record = {'trace_id': tid, 'mode': mode, 'label': label, 'reason': p['reason'],
                  'human_accepted': True, 'score_id': score_id, 'updated_at': now(), 'sync_status': 'pending'}
        old = next((r for r in rows if r.get('trace_id') == tid), None)
        if old:
            history = read(self.state / 'review_history.json', [])
            write_json(self.state / 'review_history.json', history + [{'action': 'relabel', 'at': now(), 'previous': old}])
        rows = [r for r in rows if r.get('trace_id') != tid] + [record]
        write_json(path, rows)
        if self.writer is None:
            return {'ok': True, 'sync_status': 'pending', 'message': 'Saved locally; live sync required later'}
        try:
            self.writer(record)
        except Exception:
            raise RuntimeError('Saved locally as pending. Langfuse write failed; retry this judgment to sync.') from None
        record['sync_status'] = 'synced'
        write_json(path, rows)
        return {'ok': True, 'sync_status': 'synced'}


def score_writer(client):
    def write(record):
        from langfuse.api.resources.score.types.create_score_request import CreateScoreRequest
        client.api.score.create(request=CreateScoreRequest(
            id=record['score_id'], traceId=record['trace_id'], name=record['mode'],
            value=record['label'], dataType='NUMERIC', comment=record['reason'],
            metadata={'origin': 'hw4-human-review', 'convention': '1=failure present;0=absent'}))
    return write


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        store = self.server.store
        if u.path in ('/', '/app.js', '/style.css'):
            path = UI / {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[u.path]
            body = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', {'/': 'text/html', '/app.js': 'text/javascript', '/style.css': 'text/css'}[u.path] + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        with store.lock:
            if u.path == '/api/bootstrap':
                return self.send(store.summary())
            if u.path == '/api/label-proposals':
                return self.send(store.label_proposals())
            if u.path == '/api/graph':
                return self.send(store.graph)
            if u.path == '/api/session':
                sid = parse_qs(u.query).get('id', [''])[0]
                return self.send({'traces': [store.traces[t] for t in store.sessions.get(sid, [])]})
            if u.path in ('/api/annotations', '/api/patterns', '/api/suggestions'):
                return self.send(store.data()[u.path.split('/')[-1]])
        self.send({'error': 'Not found'}, 404)

    def do_POST(self):
        # A local tool: reject cross-origin browser writes and non-JSON forms.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            return self.send({'error': 'Cross-origin writes are not allowed'}, 403)
        if 'application/json' not in self.headers.get('Content-Type', ''):
            return self.send({'error': 'Expected JSON'}, 415)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 2_000_000:
                raise ValueError('Invalid request size')
            p = json.loads(self.rfile.read(length))
            if not isinstance(p, dict):
                raise ValueError('Expected an object')
            store = self.server.store
            with store.lock:
                methods = {'/api/note': store.save_note, '/api/note/delete': store.delete_note,
                           '/api/label': store.save_label, '/api/suggestion-decision': store.suggestion_decision}
                if self.path not in methods:
                    return self.send({'error': 'Not found'}, 404)
                result = methods[self.path](p)
            self.send(result)
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self.send({'error': str(e)}, 400)
        except RuntimeError as e:
            self.send({'error': str(e)}, 502)
        except Exception:
            self.send({'error': 'Unexpected save error; your browser draft is retained'}, 500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8021)
    parser.add_argument('--state', type=Path, default=ROOT / 'analysis/state')
    parser.add_argument('--offline', type=Path, help='Explicit offline export; document the reason before using it for review')
    args = parser.parse_args()
    scenarios = {r['id']: r for r in map(json.loads, (ROOT / 'scenarios/support_scenarios.jsonl').read_text().splitlines())}
    from observability.instrument import load_env
    load_env()
    if args.offline:
        payload = json.loads(args.offline.read_text())
        raw = payload['traces'] if isinstance(payload, dict) else payload
        client = None
        source = {'kind': 'offline', 'loaded_at': now(), 'warning': 'Offline: labels remain pending Langfuse synchronization'}
    else:
        print('Loading final scenario traces from live Langfuse…', flush=True)
        raw, client = fetch_live(set(scenarios))
        source = {'kind': 'live Langfuse', 'loaded_at': now()}
    traces, sessions = prepare(raw, scenarios)
    if not traces:
        raise RuntimeError('No final traces found; check Langfuse project and scenario IDs')
    store = Store(args.state, traces, sessions, source, score_writer(client) if client else None)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.store = store
    print(f'Review tool ready: http://127.0.0.1:{args.port} — {len(traces)} traces, {len(sessions)} sessions', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
