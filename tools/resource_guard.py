"""Monitor serialized experiments for RAM/swap pressure and counted archive size."""
import argparse,fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;MIB=1024*1024

def memory():
    with open('/proc/meminfo') as f:
        return {line.split(':')[0]:int(line.split()[1])*1024 for line in f if line.startswith(('MemAvailable:','SwapTotal:','SwapFree:'))}

def pressure_reason(free,swap_free,reserve,min_ram):
    if free<min_ram:return 'host-ram-emergency'
    if free+swap_free<reserve:return 'host-memory-reserve'
    return None

def tree(root):
    pending=[root];found={}
    while pending:
        pid=pending.pop()
        if pid in found:continue
        try:
            fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
            pages=int(Path(f'/proc/{pid}/statm').read_text().split()[1])
            with open(f'/proc/{pid}/status') as f:
                swap=next((int(line.split()[1])*1024 for line in f if line.startswith('VmSwap:')),0)
            found[pid]=(fields[19],pages*os.sysconf('SC_PAGE_SIZE'),swap)
            for children in Path(f'/proc/{pid}/task').glob('*/children'):
                try:pending.extend(map(int,children.read_text().split()))
                except FileNotFoundError:pass
        except (FileNotFoundError,ProcessLookupError):pass
    return found

def stop(process,known):
    # Descendants may start separate sessions; kill tracked processes, not just a PGID.
    for sig in [signal.SIGTERM,signal.SIGKILL]:
        for pid,(started,_,_) in reversed(list(known.items())):
            try:
                current=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
                if current==started:os.kill(pid,sig)
            except (FileNotFoundError,ProcessLookupError):pass
        if sig==signal.SIGTERM:time.sleep(.2)
    process.wait()

def main():
    p=argparse.ArgumentParser();p.add_argument('--log',type=Path,required=True);p.add_argument('--reserve-mib',type=int,default=2048,help='combined available RAM and free swap reserve');p.add_argument('--min-ram-mib',type=int,default=512,help='emergency available RAM floor, even with free swap');p.add_argument('--start-free-mib',type=int,default=3072);p.add_argument('--wall-seconds',type=float,default=0);p.add_argument('--archive',type=Path,help='final append-only archive; never a temporary or shrinkable file');p.add_argument('--counted-limit-bytes',type=int,default=0);p.add_argument('--counted-overhead-bytes',type=int,default=0,help='known mandatory counted bytes outside the archive');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    if a.command[:1]==['--']:a.command=a.command[1:]
    if a.wall_seconds<0:p.error('wall seconds must be nonnegative')
    if a.counted_overhead_bytes<0 or a.counted_limit_bytes<0 or bool(a.archive)!=(a.counted_limit_bytes>0) or (a.counted_overhead_bytes and not a.archive):p.error('archive and positive counted limit required together; overhead must be nonnegative')
    if not a.command or a.reserve_mib<2048 or a.min_ram_mib<512 or a.start_free_mib<3072:p.error('command required; minimum2048MiB combined reserve/512MiB RAM floor/3072MiB startup RAM')
    a.log.parent.mkdir(parents=True,exist_ok=True);lock=(R/'resource.lock').open('a+')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        print('Experiment refused: another guarded experiment owns the lock.',file=sys.stderr);return 125
    mem=memory();free=mem['MemAvailable'];record=dict(command=a.command,status='starting',wall_limit_seconds=a.wall_seconds,reserve_bytes=a.reserve_mib*MIB,min_ram_bytes=a.min_ram_mib*MIB,start_available_bytes=free,start_swap_total_bytes=mem['SwapTotal'],start_swap_free_bytes=mem['SwapFree'],peak_tree_rss_bytes=0,peak_tree_swap_bytes=0,min_available_bytes=free,min_swap_free_bytes=mem['SwapFree'],peak_processes=0)
    if a.archive:record.update(archive=str(a.archive),counted_limit_bytes=a.counted_limit_bytes,counted_overhead_bytes=a.counted_overhead_bytes,observed_archive_bytes=0)
    def oversized():
        if not a.archive:return False
        try:size=a.archive.stat().st_size
        except FileNotFoundError:size=0
        record['observed_archive_bytes']=size
        record['counted_lower_bound_bytes']=size+a.counted_overhead_bytes
        return record['counted_lower_bound_bytes']>a.counted_limit_bytes
    def save():
        temp=a.log.with_suffix(a.log.suffix+'.tmp');temp.write_text(json.dumps(record,indent=2)+'\n');temp.replace(a.log)
    if free<a.start_free_mib*MIB:
        record.update(status='refused-low-headroom');save();print('Experiment refused: available memory below startup reserve.',file=sys.stderr);return 125
    record['cpu_affinity']=sorted(os.sched_getaffinity(0))
    env=dict(os.environ)
    for name in ['OMP_NUM_THREADS','OMP_THREAD_LIMIT','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMEXPR_MAX_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS','GOTO_NUM_THREADS']:env.pop(name,None)
    process=subprocess.Popen(a.command,env=env,start_new_session=True,pass_fds=(lock.fileno(),));record.update(pid=process.pid,status='running');save();start=time.monotonic();last=0
    interrupted=[]
    for sig in [signal.SIGTERM,signal.SIGINT,signal.SIGHUP]:signal.signal(sig,lambda number,frame:interrupted.append(number))
    try:
        while process.poll() is None:
            known=tree(process.pid);rss=sum(value[1] for value in known.values());swap=sum(value[2] for value in known.values());mem=memory();free=mem['MemAvailable'];record['peak_tree_rss_bytes']=max(record['peak_tree_rss_bytes'],rss);record['peak_tree_swap_bytes']=max(record['peak_tree_swap_bytes'],swap);record['min_available_bytes']=min(record['min_available_bytes'],free);record['min_swap_free_bytes']=min(record['min_swap_free_bytes'],mem['SwapFree']);record['peak_processes']=max(record['peak_processes'],len(known))
            reason='interrupted' if interrupted else 'counted-size-limit' if oversized() else 'wall-time-limit' if a.wall_seconds and time.monotonic()-start>=a.wall_seconds else pressure_reason(free,mem['SwapFree'],a.reserve_mib*MIB,a.min_ram_mib*MIB)
            if reason:record['status']=reason;stop(process,known);break
            if time.monotonic()-last>=1:save();last=time.monotonic()
            time.sleep(.05)
        if record['status']=='running':record['status']='counted-size-limit' if oversized() else 'completed' if process.returncode==0 else 'child-failed'
    finally:
        if process.poll() is None:stop(process,tree(process.pid))
        record.update(exit_code=process.returncode,wall_seconds=time.monotonic()-start);save()
    print(json.dumps({k:v for k,v in record.items() if k!='command'}),file=sys.stderr,flush=True)
    return 125 if record['status']!='completed' else 0

if __name__=='__main__':sys.exit(main())
