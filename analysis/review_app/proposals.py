"""Evidence-guided proposals, never accepted labels. No LLM or score writes.

Rules identify explicit examples and review signals; semantic or incomplete cases
remain flagged for human review. A proposed 0 is not an automatic pass.
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import date


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def propose(trace, context, mode, notes):
    tid=trace['id']; name=mode['name']; msgs=trace['trace']
    answer=next((m.get('text',m.get('content','')) for m in reversed(msgs) if m['role']=='assistant'),'')
    user='\n'.join(m.get('text','') for t in context for m in t['trace'] if m['role']=='user')
    events=[m for t in context for m in t['trace'] if m['role']=='tool_result']
    current=[m for m in msgs if m['role']=='tool_result']
    quote=answer[:1400]; label=0; uncertain=False; level='review signal'; evidence=[]
    pos=tid in mode.get('positive_trace_ids',[]);neg=tid in mode.get('negative_trace_ids',[])
    unresolved=any(re.search(r'UNRESOLVED|unsure',n['note'],re.I) for n in notes)
    if pos or neg:
        label=int(pos);level='previously confirmed example'
        evidence=[n['note'] for n in notes]
        reason=f'This trace is an explicitly human-confirmed {"positive" if pos else "close negative"} example for this category. Recheck the definition before accepting the binary judgment.'
    elif name=='missed_dispute_escalation':
        dispute=bool(re.search(r'\bdisput\w*',user,re.I))
        tickets=[e['content'] for e in events if e.get('name')=='escalate_to_human' and isinstance(e.get('content'),dict) and e['content'].get('ok')]
        if not dispute:
            reason='No explicit dispute request appears in the selected turn or preceding session user messages; this dispute-specific trigger was not found.'
        elif tickets:
            reason='A dispute is mentioned and a successful escalation ticket exists in the session. Verify that the ticket covers this dispute, especially after a topic change.';uncertain=True
            evidence=[json.dumps(v) for v in tickets]
        else:
            label=1;uncertain=True;reason='The user mentions a dispute, but no successful human-escalation result appears through this turn. Check whether the dispute trigger applies here.'
    elif name=='missing_policy_citation':
        policies=[e['content'] for e in events if e.get('name') in ('get_policy','search_help_center') and isinstance(e.get('content'),dict) and e['content'].get('ok')]
        ids=set()
        for p in policies:
            if p.get('policy_id'):ids.add(p['policy_id'])
            ids.update(r['policy_id'] for r in p.get('results',[]) if r.get('policy_id'))
        cited=sorted(i for i in ids if i in answer)
        claims=bool(re.search(r'\bpolicy\b|\breturns? within\b|\b\d+ (?:business )?days\b|auto.approv',answer,re.I))
        if policies and claims and not cited:
            label=1;uncertain=True;reason='The answer contains possible policy-derived claims and no retrieved policy identifier in this reply. Check earlier citations and whether the claims actually derive from policy rather than order/tool facts.'
        elif cited:
            reason='The reply contains retrieved identifier(s): '+', '.join(cited)+'. Verify that they support every policy-derived claim; identifier presence alone does not establish full coverage.';uncertain=True
        elif claims:
            reason='Possible policy language appears without policy retrieval. Check whether this is uncited policy advice, unsupported content, or reporting an order/write-tool fact.';uncertain=True
        else:reason='No policy-derived claim signal was found in the reply. The selected answer should still be checked for paraphrased policy advice.'
        evidence=['Retrieved policy IDs: '+(', '.join(sorted(ids)) or 'none'),'IDs in selected reply: '+(', '.join(cited) or 'none')]
    elif name=='unacknowledged_record_inconsistency':
        bad=[]
        def walk(v):
            if isinstance(v,dict):
                dates={k:v.get(k) for k in ('ordered_at','shipped_at','delivered_at')}
                for left,right in [('ordered_at','shipped_at'),('shipped_at','delivered_at'),('ordered_at','delivered_at')]:
                    try:
                        if dates[left] and dates[right] and date.fromisoformat(str(dates[left])[:10])>date.fromisoformat(str(dates[right])[:10]):bad.append(f'{left}={dates[left]} occurs after {right}={dates[right]}')
                    except ValueError:pass
                for z in v.values():walk(z)
            elif isinstance(v,list):
                for z in v:walk(z)
        for e in current:walk(e.get('content'))
        acknowledges=bool(re.search(r'inconsisten|contradic|mismatch|before.*ship|does.n.t match|conflict|error',answer,re.I))
        if bad:
            label=int(not acknowledges);uncertain=True;reason='Tool records contain chronology contradictions. Check whether the reply reports the affected record and explicitly acknowledges the inconsistency.';evidence=bad
        elif not current:
            reason='No new tool record appears in this turn; earlier session evidence may still be contradictory. Compare the selected reply against prior records.';uncertain=True
        else:
            reason='No mechanically reversed order/shipment/delivery dates found in this turn. Store, product, and request-versus-result mismatches require semantic inspection.';uncertain=True
    elif name=='unresolved_lookup_recovery':
        failures=[e for e in current if isinstance(e.get('content'),dict) and (e['content'].get('ok') is False or ('orders' in e['content'] and not e['content']['orders']) or ('products' in e['content'] and not e['content']['products']))]
        if not failures:reason='The selected turn has no explicit failed or empty lookup result. Check for a previously unresolved lookup carried into this turn.'
        else:
            last=msgs.index(failures[-1]);later=[m for m in msgs[last+1:] if m['role']=='tool_result' and isinstance(m.get('content'),dict) and m['content'].get('ok')]
            label=int(not later);uncertain=True
            reason='A failed or empty lookup occurs. '+('A later successful tool result may recover the request; verify relevance.' if later else 'No later successful result occurs in this turn. Decide whether clarification was genuinely necessary or recovery/escalation was required.')
            evidence=[json.dumps(e,ensure_ascii=False)[:1200] for e in failures]
    else:
        facts=json.dumps([e.get('content') for e in events],ensure_ascii=False)
        speculative=bool(re.search(r'likely|typically|usually|generally|may have|might|possibly|common for|specific form|material quality|size, design',answer,re.I))
        substantive=bool(re.search(r'\d|\bis\b|\bare\b|\bwas\b|\bwill\b',answer))
        if not answer.strip():reason='No assistant answer is recorded; there is no reply claim to evaluate for this category.'
        elif not events and substantive:
            uncertain=True;reason='The reply contains possible factual claims without tool evidence in the available session. Check whether the conversation itself supports them or they are merely requests for clarification.'
        else:
            uncertain=True;reason=('Potential speculation or generalized process language appears. ' if speculative else ('Tool evidence is available; claim support requires semantic comparison. ' if events else 'No explicit unsupported-claim signal was found by the phrase rules. '))+'Check each factual claim against the displayed conversation and results. Proposed absent is conservative triage, not a verified pass.'
        evidence=['Tool results available through selected turn: '+str(len(events)), 'Potential speculation/generalization signal: '+str(speculative)]
    if unresolved:uncertain=True;reason+=' A saved human note is unresolved; this proposal must not resolve it implicitly.'
    return {'trace_id':tid,'mode':name,'proposed_label':label,'uncertain':uncertain,'confidence':level if pos or neg else ('needs careful review' if uncertain else 'lower-risk rule signal'),
            'reason':reason,'evidence':evidence,'answer_excerpt':quote,'context_trace_ids':[t['id'] for t in context],
            'method':'confirmed examples plus transparent evidence rules; not a model judge or ground truth',
            'human_accepted':False,'taxonomy_fingerprint':fingerprint(mode),'notes_fingerprint':fingerprint(notes),
            'trace_fingerprint':fingerprint(trace['trace'])}
