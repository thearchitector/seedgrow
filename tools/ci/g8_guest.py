"""Bounded G8 guest payload. Caller supplies CPUID admission, private assets and guard.

run(assets, out, mode) creates out/native.json (never overwrites a previous run)
and returns its dict. Scratch is private and under tempfile.gettempdir(), NOT out.
Schema g8-guest-v1: units and pairs are completed rows in execution order; active
is a partial unit/pair on failure. Pair keys: heat, arm, case (s1/s2), C, D.
Each direction has usage, marks=[extent,wall_ns,cpu_ns,misses,holes,writes] rows,
tail_wall_ns, tail_cpu_ns, output_bytes and output_sha256. C also has commits=
[extent,file_bytes,closed_wire_prefix_sha256] rows and boundary=[N,preflush,closed].
scores[heat]={passed, by_direction:{C/D:{pooled_speedup, per_case_speedup}}}.
No bare-metal launcher, timing qualification, retry, unbounded codec or raw logs.
"""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time

MIB = 1 << 20
N, WORK, HOLE = 32768, 8_500_000_000, 14_000 * MIB
MODEL_NAME = 'weights-poc8m_w2048_tf2t3_pruned_v5k_np2.c5'
EXTENTS = (4096, 8192, 16384, N)
# Frozen J1/F3 exposed resets: native logical misses (=holes), C fstat lengths.
CASES = {'s1': ((21, 41, 86, 164), (939, 1929, 3553, 7208)),
         's2': ((23, 44, 80, 164), (1063, 2177, 4302, 7987))}
GUARD = '4789c8d66a2bc86a195d033c97e05d9b1007a9cbd17174bf95a9df941f0c8ced'
PINS = {
    'stock.unit': '94d61af08475e74f137a97977aeb42f1f95f95d6a40124fca5fc1d3fd7112a39',
    'evex.unit': '8ac9aa8bd950abcd0ebcfb404287f8507187a1f109f543557b9613016507bbc2',
    'stock.probe': '72ceb819e3f9691664627dba0596b5961d5a8ab75b11f3415654f67366569305',
    'evex.probe': '02a535827e4dd4deb5c6e49934fe606e5a05185982b27e39d449219613bb0c0a',
    'model.c5': '729694cba4969b7d833686ed3f597ff04d3b226da849d5f8004ec020a0ed9563',
    's1.clear': '397027a83119582503310a9d833dd43d9d9e1df9b1d6bbd35c39203423086751',
    's2.clear': '64adfb019a5dc52708bb02a4d77c3e23ef1e756a317f26470a488418b21d2a19',
    's1.wire': '1a19a961e0cd00f02adf14fd8c6b4579a4af64308d7530991cc5eda735e33053',
    's2.wire': '2b22db112ab511087cc209a79ee0eb5c043b1ea28a17fa218d9bf7ca0ed350b8',
}
HERE = Path(__file__).resolve()
OFFLINE = 'G8 wrapper: limits installed, socket probe ENETDOWN'
UNIT_OK = 'G8 synthetic OK: raw/biased, NC=2/6, single/batch, i32 and f32 bits'


class Stop(Exception):
    """Only fixed, artifact-safe reason codes go here; never child-controlled text."""


class Capacity(Stop):
    pass


def need(test, reason):
    if not test:
        raise Stop(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bounded(path, maximum):
    s = path.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_size <= maximum, 'file-type-or-size')
    with path.open('rb') as f:
        data = f.read(maximum + 1)
    need(len(data) == s.st_size, 'file-changed')
    return data


def guard_fd():
    # Accept the main checkout's actual guard for a worktree rehearsal, too.
    for fd in Path('/proc/self/fd').iterdir():
        try:
            lock = Path(os.readlink(fd))
        except FileNotFoundError:
            continue
        if lock.name != 'resource.lock' or not lock.is_absolute() or not fd.samefile(lock):
            continue
        info = (Path('/proc/self/fdinfo') / fd.name).read_text()
        owner = re.search(r'^lock:\s+\d+: FLOCK\s+ADVISORY\s+WRITE\s+(\d+) ', info, re.M)
        need(owner and sha(bounded(lock.with_name('resource_guard.py'), MIB)) == GUARD, 'guard-pin')
        proc = Path('/proc') / owner[1]
        args = (proc / 'cmdline').read_bytes().split(b'\0')
        args = args[:args.index(b'--')] if b'--' in args else []
        script = next((os.fsdecode(x) for x in args if Path(os.fsdecode(x)).name == 'resource_guard.py'), None)
        need(script and (proc / 'cwd' / script).samefile(lock.with_name('resource_guard.py')) and
             any(k == b'--wall-seconds=0' or [k, v] == [b'--wall-seconds', b'0']
                 for k, v in zip(args, args[1:] + [b''])), 'guard-command')
        return int(fd.name)
    raise Stop('guard-missing')


def platform_check():
    need(sys.platform == 'linux' and os.uname().machine == 'x86_64', 'platform')
    allowed = os.sched_getaffinity(0)  # observation only; never set affinity
    v3 = set('cx16 lahf_lm popcnt pni ssse3 sse4_1 sse4_2 avx avx2 bmi1 bmi2 f16c fma movbe xsave'.split())
    found = set()
    for cpu in Path('/proc/cpuinfo').read_text().split('\n\n'):
        d = dict((k.strip(), v.strip()) for k, v in (s.split(':', 1) for s in cpu.splitlines() if ':' in s))
        if 'processor' in d and int(d['processor']) in allowed:
            flags = set(d.get('flags', '').split())
            need(v3 <= flags and flags & {'lzcnt', 'abm'}, 'v3-missing')
            found.add(int(d['processor']))
    need(found and found == allowed, 'v3-incomplete')


def memory_headroom():
    # Ubuntu unified cgroup v2. Walk every visible ancestor (including mount root),
    # not just the leaf; no credit for cache reclaim or swap. Refuse unknown layouts.
    mem = Path('/proc/meminfo').read_text()
    host = int(re.search(r'^MemAvailable:\s+(\d+) kB$', mem, re.M)[1]) * 1024
    groups = [row.split(':', 2) for row in Path('/proc/self/cgroup').read_text().splitlines()]
    need(not any('memory' in controllers.split(',') for _, controllers, _ in groups), 'cgroup-v1-memory')
    unified = [Path(g) for index, controllers, g in groups if index == '0' and not controllers]
    mount = Path('/sys/fs/cgroup')
    roots = [Path(line.split()[3]) for line in Path('/proc/self/mountinfo').read_text().splitlines()
             if ' - cgroup2 ' in line and line.split()[4] == str(mount)]
    need(len(unified) == len(roots) == 1, 'cgroup-v2-layout')
    group, root = unified[0], roots[0]
    need(group.is_relative_to(root) and '..' not in group.parts, 'cgroup-path')
    leaf = mount / group.relative_to(root)
    need((leaf / 'cgroup.procs').is_file(), 'cgroup-missing')
    rooms, oom = [], 0
    for scope in (leaf, *leaf.parents):
        events = scope / 'memory.events'
        if events.is_file():
            oom += int(dict(s.split() for s in events.read_text().splitlines()).get('oom_kill', '0'))
        for name in ('memory.max', 'memory.high'):
            f = scope / name
            if f.is_file():
                limit = f.read_text().strip()
                if limit != 'max':
                    rooms.append(max(0, int(limit) - int((scope / 'memory.current').read_text())))
        if scope == mount:
            break
    return {'host_available_bytes': host, 'cgroup_available_bytes': min(rooms, default=None),
            'available_bytes': min([host, *rooms]), 'ancestor_oom_kill_sum': oom}


def limits(native):
    return ((resource.RLIMIT_AS, WORK, WORK + HOLE), (resource.RLIMIT_FSIZE, HOLE, HOLE),
            (resource.RLIMIT_CORE, 0, 0)) if native else (
                (resource.RLIMIT_AS, 512*MIB, 512*MIB), (resource.RLIMIT_FSIZE, 160*MIB, 160*MIB),
                (resource.RLIMIT_CORE, 0, 0))


def offline():
    lib = ctypes.CDLL('libseccomp.so.2')
    ptr, u32, ci = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int
    lib.seccomp_init.argtypes = [u32]
    lib.seccomp_init.restype = ptr
    lib.seccomp_rule_add.argtypes = [ptr, u32, ci, ctypes.c_uint]
    lib.seccomp_load.argtypes = lib.seccomp_release.argtypes = [ptr]
    lib.seccomp_release.restype = None
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    ctx = lib.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW; fail closed on any setup error
    need(ctx, 'seccomp-init')
    try:
        for name in (b'socket', b'socketpair', b'io_uring_setup'):
            nr = lib.seccomp_syscall_resolve_name(name)
            need(nr >= 0 and lib.seccomp_rule_add(ctx, 0x50000 | errno.ENETDOWN, nr, 0) == 0, 'seccomp-rule')
        need(lib.seccomp_load(ctx) == 0, 'seccomp-load')
    finally:
        lib.seccomp_release(ctx)
    try:
        socket.socket().close()
    except OSError as e:
        need(e.errno == errno.ENETDOWN, 'seccomp-probe')
    else:
        raise Stop('seccomp-probe')


def clean_env(cwd):
    return {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'HOME': str(cwd), 'TMPDIR': str(cwd)}


def child(arm, op, case):
    """Clean -IB helper, no inherited fd but guard; no arbitrary command/codec argv."""
    os.close(guard_fd())
    need(arm in ('stock', 'evex') and ((op == 'unit' and case == '-') or
         (op in ('C', 'D') and case in CASES)), 'child-args')
    filename = arm + ('.unit' if op == 'unit' else '.probe')
    exe = Path.cwd().parent / filename
    need(sha(bounded(exe, 8*MIB)) == PINS[filename], 'executable-pin')
    for kind, soft, hard in limits(op != 'unit'):
        resource.setrlimit(kind, (soft, hard))
        need(resource.getrlimit(kind) == (soft, hard), 'rlimit-readback')
    offline()
    os.write(2, OFFLINE.encode() + b'\n')
    args = [] if op == 'unit' else [op, 'input', 'output', str(N), str(2*N if op == 'C' else 0), 'text' + case[-1]]
    os.execve(exe, [str(exe), *args], clean_env(Path.cwd()))


def witness(pid, cwd):
    """Independent live kernel witness in addition to pinned native self-check/log."""
    try:
        page = (cwd / 'ppm.page').lstat()
        if page.st_size == 0:  # between O_CREAT and ftruncate
            return None
        maps = (Path('/proc') / str(pid) / 'maps').read_text().splitlines()
    except FileNotFoundError:  # before construction or after exit
        return None
    holes = []
    for row in maps:
        address, perm, _, dev, ino, *name = row.split()
        if perm == '---p' and dev == '00:00' and ino == '0' and not name:
            lo, hi = address.split('-')
            holes.append(int(hi, 16) - int(lo, 16))
    need(stat.S_ISREG(page.st_mode) and page.st_size == HOLE and page.st_blocks*512 < HOLE and
         max(holes, default=0) >= HOLE, 'pager-kernel-witness')
    need(resource.prlimit(pid, resource.RLIMIT_AS) == (WORK + HOLE, WORK + HOLE), 'pager-as-limit')
    return {'none_private_anon_bytes': max(holes), 'as_live_bytes': WORK + HOLE, 'pagefile_bytes': page.st_size,
            'pagefile_allocated_bytes': page.st_blocks * 512}


def execute(cwd, arm, op, case, row, lock, save):
    native = op != 'unit'
    u = row['usage'] = {'started': False}
    room = u['preflight'] = memory_headroom()
    room['disk_free_bytes'] = shutil.disk_usage(cwd).free
    if room['available_bytes'] < 8_000_000_000:
        raise Capacity('memory-headroom')
    if native and room['disk_free_bytes'] <= 32 * (1 << 30):
        raise Capacity('scratch-space')
    for kind, _, hard in limits(native):
        ceiling = resource.getrlimit(kind)[1]
        if ceiling != resource.RLIM_INFINITY and ceiling < hard:
            raise Capacity('inherited-hard-limit')
    with tempfile.TemporaryFile(dir=cwd.parent) as log:
        u['start_wall_ns'] = time.monotonic_ns()
        p = subprocess.Popen([sys.executable, '-IB', cwd.parent / 'child.py', '--child', arm, op, case], cwd=cwd, env=clean_env(cwd),
                             stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, pass_fds=(lock,))
        try:
            u['started'] = True
            save()
            live = None
            while True:
                # Only poll until the one /proc witness; the outer guard samples the entire tree.
                pid, status, ru = os.wait4(p.pid, os.WNOHANG if native and live is None else 0)
                if pid:
                    p.returncode = os.waitstatus_to_exitcode(status)
                    break
                live = witness(p.pid, cwd)
                if live is None:
                    time.sleep(.05)
        finally:
            if p.returncode is None:
                p.kill()
                p.wait()
        u.update(exit=p.returncode, whole_wall_ns=time.monotonic_ns()-u['start_wall_ns'],
                 whole_cpu_ns=round((ru.ru_utime + ru.ru_stime)*1e9), peak_rss_bytes=ru.ru_maxrss*1024)
        if p.returncode == -signal.SIGKILL and memory_headroom()['ancestor_oom_kill_sum'] > room['ancestor_oom_kill_sum']:
            raise Capacity('cgroup-oom-kill-observed')
        rc_reason = {-signal.SIGILL: 'illegal-instruction', -signal.SIGXFSZ: 'fsize-limit', 74: 'native-address-budget',
                     75: 'pager-write-cap', 77: 'evex-refused', 118: 'wrapper-setup', 119: 'wrapper-os-error'}
        need(p.returncode == 0, rc_reason.get(p.returncode, 'child-exit'))
        log.seek(0)
        data = log.read(65537)
        need(len(data) <= 65536, 'log-overflow')
    lines = data.decode('ascii').splitlines()
    need(lines.count(OFFLINE) == 1, 'missing-offline-probe')
    u['socket_enetdown'] = True
    u['rlimits'] = {key: [soft, hard] for key, (_, soft, hard) in zip(('as', 'fsize', 'core'), limits(native))}
    if native:
        need(live is not None, 'pager-unobserved')
        row['pager'] = live
    admissions = [line for line in lines if line.startswith('F3-G8')]
    need(len(admissions) == int(arm == 'evex'), 'arm-marker')
    if admissions:
        m = re.fullmatch(r'F3-G8 evex admitted CPUID\.1\.ecx=([0-9a-f]{8}) 7\.0\.ebx=([0-9a-f]{8}) '
                         r'7\.0\.ecx=([0-9a-f]{8}) XCR0=([0-9a-f]{16})', admissions[0])
        need(m, 'evex-marker')
        ecx1, ebx7, ecx7, xcr = row['evex_cpuid'] = [int(x, 16) for x in m.groups()]
        need(ecx1 & 0x1c000000 == 0x1c000000 and ebx7 & 0x80010000 == 0x80010000 and
             ecx7 & (1 << 11) and xcr & 0xe6 == 0xe6, 'evex-xstate')
    return lines


def audit(lines, row, op, case, output):
    misses, positions = CASES[case]
    need([s for s in lines if s.startswith('PQ hole')] == [f'PQ hole {HOLE} verified'] and
         [s for s in lines if s.startswith('ppmd:')] ==
         [f'ppmd: heap={HOLE} max_pool={256*MIB} misses=164 holes=164 writes=0'], 'pager-summary')
    need([s for s in lines if s.startswith('host:')] ==
         ['host: stream=0 declared=501062281 metadata_rows=0/0 slot_bytes=0 dictionary=0'], 'reset-state')
    marks = row['marks'] = []
    events = [s for s in lines if s.startswith(('MARK', 'commit', 'boundary:'))]
    want = []
    for i, n in enumerate(EXTENTS):
        match = re.fullmatch('MARK ' + ' '.join([r'(\d+)']*6), events[len(want)] if len(events) > len(want) else '')
        need(match, 'mark-format')
        mark = [int(x) for x in match.groups()]
        start = row['usage']['start_wall_ns']
        need(mark[0] == n and mark[3:] == [misses[i], misses[i], 0] and mark[2] > 0 and
             start <= mark[1] <= start + row['usage']['whole_wall_ns'] and
             (not marks or (mark[1] > marks[-1][1] and mark[2] > marks[-1][2])), 'mark-values')
        marks.append(mark)
        want.append(match[0])
        if op == 'C':
            want.append(f'commit stream={n} file={positions[i]} meta_end=0 table_end=0 slot_end=0 slot=0 text_next=0')
    if op == 'C':
        pre = positions[-1]
        need(len(output) == pre + 1, 'wire-length')
        want.append(f'boundary: stream={N} preflush={pre} closed_size={len(output)}')
    need(events == want, 'commit-boundary-order')
    if op == 'C':
        row['boundary'] = [N, pre, len(output)]
        row['commits'] = [[n, size, sha(output[:size])] for n, size in zip(EXTENTS, positions)]
    row.update(tail_wall_ns=marks[3][1]-marks[2][1], tail_cpu_ns=marks[3][2]-marks[2][2])


def score(pairs):
    by = {}
    passed = True
    for op in ('C', 'D'):
        t = {(p['case'], p['arm']): p[op]['tail_wall_ns'] for p in pairs}
        stock = [t[k, 'stock'] for k in CASES]
        evex = [t[k, 'evex'] for k in CASES]
        by[op] = {'pooled_speedup': sum(stock)/sum(evex),
                  'per_case_speedup': {k: s/e for k, s, e in zip(CASES, stock, evex)}}
        # Exact comparisons on integer nanoseconds, no rounding at either threshold.
        passed &= 10*sum(stock) >= 11*sum(evex) and all(100*e <= 105*s for s, e in zip(stock, evex))
    return {'passed': passed, 'by_direction': by}


def run(assets: Path, out: Path, mode: str):
    """Only entry point for the guarded caller. A capacity refusal is not a codec loss."""
    out.mkdir(parents=True, exist_ok=True)
    dst = out / 'native.json'
    result = {'schema': 'g8-guest-v1', 'mode': mode if mode in ('guest', 'stock-rehearsal') else 'invalid',
              'status': 'running', 'reason': None, 'timing_qualified': False, 'units': [], 'pairs': [],
              'scores': {}, 'active': None}
    with dst.open('x', encoding='ascii') as f:  # no adaptive reruns into existing evidence
        json.dump(result, f)

    def save():
        tmp = dst.with_name('.native.tmp')
        f = tmp.open('x', encoding='ascii')
        try:
            with f:
                json.dump(result, f, separators=(',', ':'), allow_nan=False)
                f.write('\n')
            tmp.replace(dst)
        finally:
            tmp.unlink(missing_ok=True)

    def interrupt(_signum, _frame):
        raise Stop('interrupted')

    # Unwind private directories even on the guard's TERM; preserve caller handlers.
    handlers = {}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGHUP):
            if signal.getsignal(sig) == signal.SIG_DFL:
                handlers[sig] = signal.signal(sig, interrupt)
    try:
        need(result['mode'] != 'invalid', 'mode')
        lock = guard_fd()
        platform_check()
        arms = ('evex', 'stock') if mode == 'guest' else ('stock',)
        blobs = {}
        for name, pin in PINS.items():
            if mode == 'stock-rehearsal' and name.startswith('evex.'):
                continue
            data = bounded(assets / name, 8*MIB)
            need(sha(data) == pin, 'asset-pin-' + name)
            blobs[name] = data
        for k, (_, pos) in CASES.items():
            need(len(blobs[k + '.clear']) == N and len(blobs[k + '.wire']) == pos[-1]+1, 'fixture-length')
        driver = HERE.read_bytes()
        result.update(asset_sha256={k: PINS[k] for k in blobs}, guard_sha256=GUARD, driver_sha256=sha(driver))
        base = Path(tempfile.gettempdir()).resolve(strict=True)
        need(not base.is_relative_to(out.resolve()), 'scratch-inside-receipts')
        need(not os.statvfs(base).f_flag & os.ST_NOEXEC, 'scratch-noexec')
        with tempfile.TemporaryDirectory(prefix='g8-', dir=base) as scratch:
            root = Path(scratch).resolve()
            (root / 'child.py').write_bytes(driver)
            for name in blobs.keys() & {arm + ext for arm in arms for ext in ('.unit', '.probe')}:
                (root / name).write_bytes(blobs[name])
                (root / name).chmod(0o500)
            for arm in arms:
                row = result['active'] = {'arm': arm, 'op': 'unit'}
                with tempfile.TemporaryDirectory(dir=root) as wd:
                    lines = execute(Path(wd), arm, 'unit', '-', row, lock, save)
                    need(lines.count(UNIT_OK) == 1 and not list(Path(wd).iterdir()), 'unit-check')
                row['synthetic_ok'] = True
                result['units'].append(row)
                result['active'] = None
                save()
            order = [(k, a) for k in CASES for a in ('stock', 'evex')]
            heats = [('forward', order), ('reverse', order[::-1])] if mode == 'guest' else [
                ('stock-rehearsal', [(k, 'stock') for k in CASES])]
            for heat, sequence in heats:
                for case, arm in sequence:
                    pair = result['active'] = {'heat': heat, 'arm': arm, 'case': case}
                    source = blobs[case + '.clear']
                    for op in ('C', 'D'):
                        row = pair[op] = {}
                        # Previous C workspace (clear, pagefile AND all side state) is gone before D.
                        with tempfile.TemporaryDirectory(dir=root) as wd:
                            cwd = Path(wd)
                            (cwd / MODEL_NAME).write_bytes(blobs['model.c5'])
                            (cwd / 'input').write_bytes(source)
                            need({p.name for p in cwd.iterdir()} == {MODEL_NAME, 'input'}, 'cwd-not-fresh')
                            need(bounded(cwd / 'input', 2*N) == source, 'staged-input')
                            row.update(input_bytes=len(source), input_sha256=sha(source))
                            lines = execute(cwd, arm, op, case, row, lock, save)
                            output = bounded(cwd / 'output', 2*N)
                            row.update(output_bytes=len(output), output_sha256=sha(output))
                            audit(lines, row, op, case, output)
                            expected = blobs[case + ('.wire' if op == 'C' else '.clear')]
                            need(output == expected, 'wire-mismatch' if op == 'C' else 'clear-mismatch')
                            source = output  # D actually receives this arm's closed wire, not the golden file.
                        save()
                    result['pairs'].append(pair)
                    result['active'] = None
                    save()
                if mode == 'guest':
                    scored = result['scores'][heat] = score([p for p in result['pairs'] if p['heat'] == heat])
                    save()
                    if not scored['passed']:
                        break
        result['status'] = 'completed'
    except (Exception, KeyboardInterrupt) as e:
        # Never transmit a raw exception, path, stderr, unexpected output or array contents.
        cap = isinstance(e, Capacity) or isinstance(e, OSError) and e.errno in (errno.ENOSPC, errno.ENOMEM, errno.EDQUOT)
        active = result['active'] or {}
        started = bool(result['pairs']) or any(active.get(op, {}).get('usage', {}).get('started') for op in ('C', 'D'))
        result['status'] = ('failed-capacity' if started else 'skipped-capacity') if cap else 'failed'
        result['reason'] = str(e) if isinstance(e, Stop) else 'os-error' if isinstance(e, OSError) else 'controller-error'
        if isinstance(e, OSError):
            result['errno'] = e.errno
        if isinstance(e, KeyboardInterrupt):
            result['reason'] = 'interrupted'
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    save()
    return result


if __name__ == '__main__':
    if len(sys.argv) != 5 or sys.argv[1] != '--child':
        sys.exit('Use run(assets, out, mode) from the guarded controller.')
    try:
        child(*sys.argv[2:])
    except OSError:
        sys.exit(119)
    except Exception:
        sys.exit(118)
