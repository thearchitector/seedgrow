"""Find the pushed commit's one Actions run, wait, authenticate its receipts and verify them as data."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import zipfile

REPO = 'thearchitector/seedgrow'; BRANCH = 'ci/runner-isa-smoke'; WORKFLOW = 'scratchpad.yml'
HERE = Path(__file__).resolve().parent
LIMITS = {'dispatch.json':8192, 'isa/guard.json':16384,'isa/result.json':8192,'isa/scalar.u32':2048,'isa/evex.u32':2048,
          'codec/guard.json':16384,'codec/archive.json':8192,'codec/native.json':524288,'codec/state.json':8192}


def need(ok, message):
    if not ok: raise ValueError(message)


def gh(*args):
    return subprocess.check_output(['gh',*args],env={**os.environ,'GH_PROMPT_DISABLED':'1','GH_NO_UPDATE_NOTIFIER':'1'})


def api(path): return json.loads(gh('api',f'repos/{REPO}/'+path))


def collect(args):
    git=['git','-C',HERE.parents[1]]; commit=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
    need(re.fullmatch(r'[0-9a-f]{40}',commit) and subprocess.run(git+['diff','--quiet','HEAD','--','tools/ci','.github/workflows']).returncode==0,
         'use the clean, reviewed workflow checkout at the tested commit')
    if args.run_id: rid=args.run_id
    else:
        # Only wait for a pushed commit; never trigger, race two dispatches, or request a rerun.
        rid=None
        for trial in range(30 if args.wait else 1):
            rows=api(f'actions/workflows/{WORKFLOW}/runs?branch=ci%2Frunner-isa-smoke&head_sha={commit}&per_page=25')['workflow_runs'];rows=[q for q in rows if q['head_sha']==commit and q['event']=='push']
            need(len(rows)<=1,'ambiguous push: specify --run-id');
            if rows: rid=rows[0]['id']; break
            if args.wait and trial<29: time.sleep(5)
        need(rid is not None,'no matching push run; check branch and push')
    endpoint=f'actions/runs/{rid}';r=api(endpoint)
    def same():
        return (r['id']==rid and r['head_sha']==commit and r['head_branch']==BRANCH and r['head_repository']['full_name']==REPO and
                r['path']=='.github/workflows/'+WORKFLOW and r['event'] in ('push','workflow_dispatch') and r['run_attempt']==1)
    need(same(),'run/commit/ref/event mismatch, or manually rerun attempt');print(r['html_url'],flush=True)
    while args.wait and r['status']!='completed': time.sleep(15);r=api(endpoint);need(same(),'run changed')
    need(r['status']=='completed','still running; use --wait'); attempt=r['run_attempt'];out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False); slots=out/'slots';slots.mkdir();idx=api(endpoint+'/artifacts?per_page=100'); artifacts=idx['artifacts'];need(idx['total_count']==len(artifacts)<=6 and artifacts,'missing or excess artifacts')
    def fetch(a):
        match=re.fullmatch(fr'guest-g8-{rid}-{attempt}-slot-([1-6])',a['name']);need(match and not a['expired'] and 0<a['size_in_bytes']<=800000,'unexpected or expired artifact');n=int(match[1]);w=a['workflow_run'];need((w['id'],w['head_sha'],w['head_branch'])==(rid,commit,BRANCH),'artifact belongs to another run');dest=slots/f'slot-{n}';dest.mkdir()
        raw=gh('api','--allow-escape-sequences',f"repos/{REPO}/actions/artifacts/{a['id']}/zip");need(len(raw)==a['size_in_bytes'] and 'sha256:'+hashlib.sha256(raw).hexdigest()==a['digest'],'artifact digest');(out/f'slot-{n}.zip').write_bytes(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=z.namelist();need('dispatch.json' in names and len(names)==len(set(names)) and all(name in LIMITS or name in ('isa/','codec/') for name in names),'unexpected ZIP paths')
            for info in z.infolist():
                name=info.filename;need(not stat.S_ISLNK(info.external_attr>>16),'ZIP symlink');
                if name.endswith('/'):need(info.is_dir() and info.file_size==0,'bad directory');continue
                need(0<info.file_size<=LIMITS[name],'ZIP member extent');p=dest/name;p.parent.mkdir(exist_ok=True);p.write_bytes(z.read(info))
        return {'slot':n,'id':a['id'],'sha256':a['digest'],'bytes':len(raw)}
    entries=sorted((fetch(a) for a in artifacts),key=lambda e:e['slot']);receipt=dict(run_id=rid,run_attempt=attempt,url=r['html_url'],host_conclusion=r['conclusion'],commit=commit,artifacts=entries)
    (out/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n');v=subprocess.run([sys.executable,'-IB',HERE/'guest_verify.py',slots,'--commit',commit,'--run-id',str(rid),'--attempt',str(attempt)],capture_output=True,text=True)
    (out/'verification.txt').write_text(v.stdout+v.stderr); report=json.loads(v.stdout)
    if v.returncode==0:need(r['conclusion']=='success','completed codec evidence but unsuccessful hosted run')
    if v.returncode in (3,4):need(r['conclusion']=='failure','terminal refusal/exhaustion should not be green')
    print(f"Verified return: {report['status']} ({out})")
    for s in report.get('slots',[]):
        print(f"VM {s['slot']}: {s.get('isa',{}).get('model','unknown CPU')} — {s['outcome']}")
        codec=s.get('codec',{})
        if 'fixture_verdict' in codec:
            print(f"Archive-only D: 4096 B; {codec['checked_C_fresh_D_pairs']} matched C/fresh-D pairs, wires {codec['closed_bytes']} B.")
            for ph,gate in codec['gates'].items():print(f"{ph}: guest tail speedups C {gate['C']['speedup']:.3f}x / D {gate['D']['speedup']:.3f}x")
            print(codec['fixture_verdict']+'; guest only, not a qualifying timing')
    if 'error' in report:print(report['error'],file=sys.stderr)
    return v.returncode


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out',type=Path,help='new local output directory');ap.add_argument('--wait',action='store_true');ap.add_argument('--run-id',type=int);sys.exit(collect(ap.parse_args()))
