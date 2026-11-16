from analysis.review_app.proposals import propose, fingerprint
from analysis.review_app.server import Store, write_json


def case(messages):
    return {'id':'a'*32,'trace':messages,'meta':{'scenario_id':'support-test'}}


def test_citation_proposal_flags_uncited_retrieved_policy():
    t=case([{'role':'tool_result','name':'get_policy','content':{'ok':True,'policy_id':'cw-returns'}}, {'role':'assistant','text':'The policy allows returns within 30 days.'}])
    r=propose(t,[t],{'name':'missing_policy_citation'},[])
    assert r['proposed_label']==1 and r['uncertain'] and not r['human_accepted']
    assert 'cw-returns' in str(r['evidence'])


def test_dispute_without_escalation_needs_review_but_no_dispute_is_separate():
    t=case([{'role':'user','text':'Help with a delivery dispute'},{'role':'assistant','text':'Please give the order ID.'}])
    r=propose(t,[t],{'name':'missed_dispute_escalation'},[])
    assert r['proposed_label']==1 and r['uncertain']
    t=case([{'role':'user','text':'Find my mug order.'},{'role':'assistant','text':'Please give the order ID.'}])
    r=propose(t,[t],{'name':'missed_dispute_escalation'},[])
    assert r['proposed_label']==0 and not r['uncertain']


def test_generic_note_does_not_override_reversed_dates_or_unresolved_flag():
    t=case([{'role':'tool_result','name':'find_order','content':{'ok':True,'orders':[{'shipped_at':'2026-06-25','delivered_at':'2026-06-23'}]}},{'role':'assistant','text':'Shipped June 25 and delivered June 23.'}])
    r=propose(t,[t],{'name':'unacknowledged_record_inconsistency'},[{'note':'No failure observed.'}])
    assert r['proposed_label']==1 and r['uncertain']
    r=propose(t,[t],{'name':'missed_dispute_escalation'},[{'note':'UNRESOLVED — unsure'}])
    assert r['uncertain']


def test_proposals_are_stale_after_notes_change_and_exclude_saved(tmp_path):
    t=case([{'role':'assistant','text':'Hello'}]);mode={'name':'missed_dispute_escalation','status':'final'}
    write_json(tmp_path/'patterns.json',{'modes':[mode]})
    write_json(tmp_path/'label_proposals.json',{'rows':[propose(t,[t],mode,[])]})
    store=Store.__new__(Store);store.state=tmp_path;store.traces={t['id']:t}
    assert store.label_proposals()['rows'][0]['stale'] is False
    write_json(tmp_path/'annotations.json',{'annotations':[{'trace_id':t['id'],'note':'Changed'}]})
    assert store.label_proposals()['rows'][0]['stale'] is True
    write_json(tmp_path/'labels'/'missed_dispute_escalation.json',[{'trace_id':t['id'],'mode':mode['name']}])
    assert store.label_proposals()['rows']==[]
