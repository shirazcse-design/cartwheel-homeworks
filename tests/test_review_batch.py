"""Exercise batch approval gates with fake DOM/API; no student state or network."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_batch_requires_review_preserves_existing_and_only_saves_selected():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser approval-logic check')
    source = Path('analysis/review_app/app.js').read_text()
    batch = source.split('// Explicit human approval workflow for missing trace/category pairs.\n')[1].rsplit('init();', 1)[0]
    harness = r'''
const vm=require('node:vm'),assert=require('node:assert');
const elements={},writes=[],saved=[];
const box={console, data:{labels:[]}, $:s=>elements[s]??=( {checked:false,disabled:false,value:'',textContent:''} ), $$:()=>[],say:()=>{},pretty:JSON.stringify,esc:String,finalModes:()=>[],notes:()=>[],bindOpen:()=>{},
api:async(path,payload)=>{if(path==='/api/bootstrap')return {labels:[{trace_id:'old',mode:'m'}]};if(path==='/api/label'){writes.push(payload);saved.push(payload);return {sync_status:'synced'};}throw Error(path);},refresh:async()=>{box.data.labels=[{trace_id:'old',mode:'m'},...saved];}};
vm.createContext(box);
vm.runInContext(BATCH,box);
(async()=>{
 await vm.runInContext(`renderBatchRows=()=>{};batchRows=[{trace_id:'new',mode:'m',choice:'0',reason:'Reviewed evidence',selected:true}];saveBatchRows()`,box);
 assert.equal(writes.length,0,'unchecked review attestation must block writes');
 box.$('#batch-attest').checked=true;
 await vm.runInContext(`batchRows[0].choice='';saveBatchRows()`,box);
 assert.equal(writes.length,0,'uncertain selected rows must block writes');
 await vm.runInContext(`batchRows=[{trace_id:'old',mode:'m',choice:'1',reason:'Do not overwrite',selected:true},{trace_id:'new',mode:'m',choice:'0',reason:'Reviewed evidence',selected:true},{trace_id:'untouched',mode:'m',choice:'0',reason:'Not approved',selected:false}];saveBatchRows()`,box);
 assert.equal(writes.length,1);assert.equal(writes[0].trace_id,'new');assert.equal(writes[0].label,0);
 assert(writes[0].reason.includes('Human reviewed and approved in batch'));
 console.log('approval gates and preservation checks passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
'''.replace('BATCH', __import__('json').dumps(batch))
    result = subprocess.run([node, '-e', harness], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'checks passed' in result.stdout
