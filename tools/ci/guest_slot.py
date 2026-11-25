"""Emit explicit slot outcomes; never interpret a failed step as a hardware refusal."""
import json
import os
import sys
from pathlib import Path


def read(p): return json.loads(p.read_bytes())


def result(step, value):
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as f: print(f'{step}={value}',file=f)


def main():
    mode, loc, slot = sys.argv[1:]; d=Path(loc); slot=int(slot); assert 1<=slot<=6
    assert os.environ['GITHUB_REPOSITORY']=='thearchitector/seedgrow' and os.environ['GITHUB_REF']=='refs/heads/ci/runner-isa-smoke'
    commit=os.environ['GITHUB_SHA']; run=os.environ['GITHUB_RUN_ID']; attempt=os.environ['GITHUB_RUN_ATTEMPT']
    if mode=='select':
        q=read(d/'isa/result.json'); g=read(d/'isa/guard.json'); assert (q['commit'],q['run_id'],q['attempt'])==(commit,run,attempt) and g['status']=='completed' and g['exit_code']==0
        assert (q['outcome'],q['evex_exit']) in (('unsupported',77),('executed-match',0)); result('eligible','true' if q['outcome']=='executed-match' else 'false'); return
    assert mode=='finish'; outcome='failed'; isa=os.environ['ISA_STEP']; codec=os.environ['CODEC_STEP']; space=os.environ['SPACE_STEP']; raw=d/'codec/state.json'
    resource={'refused-low-headroom','host-ram-emergency','host-memory-reserve'}
    if isa=='failure' and (d/'isa/guard.json').is_file() and read(d/'isa/guard.json')['status'] in resource and space==codec=='skipped':
        outcome='resource-refused'
    if isa=='success':
        q=read(d/'isa/result.json'); assert q['commit']==commit and q['run_id']==run and q['attempt']==attempt
        if (q['outcome'],q['evex_exit'])==('unsupported',77) and codec==space=='skipped' and not raw.exists(): outcome='unsupported'
        elif q['outcome']=='executed-match' and space=='success' and (d/'codec/guard.json').is_file():
            state=read(raw) if raw.is_file() else {}; guard=read(d/'codec/guard.json')
            if state=={'mode':'guest','status':'completed'} and codec=='success' and guard['exit_code']==0 and guard['status']=='completed': outcome='completed'
            elif codec=='failure' and (state.get('status')=='resource-refused' or guard['status'] in resource): outcome='resource-refused'
    d.mkdir(exist_ok=True,parents=True); record={'commit':commit,'run_id':run,'run_attempt':attempt,'slot':slot,'outcome':outcome,
                       'steps':{'isa':isa,'space':space,'codec':codec},'scope':'guest engineering; no judge timing'}
    (d/'dispatch.json').write_text(json.dumps(record,indent=2)+'\n');result('outcome',outcome)
    with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a') as f:
        print(f'**VM {slot}/6: {outcome}.** Only an unsupported ISA can allocate the next VM. Native timings, if present, describe only this guest.',file=f)
    print(f'VM {slot}/6: {outcome}')
    if outcome=='failed': sys.exit(1)

if __name__=='__main__': main()
