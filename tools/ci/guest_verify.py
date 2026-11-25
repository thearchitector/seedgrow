"""Linux data-only readback of one pinned, sequential six-slot scout dispatch.

Use the trusted checkout, not a script in the download. Run/attempt, commit and
artifact ZIP provenance are pinned by the caller; receipts are not attestations.
Exit: 0 completed native comparison (not necessarily a gain), 3 exhausted,
4 resource refusal, 1 engineering failure/invalid or incomplete evidence.
"""
import argparse
from contextlib import contextmanager, redirect_stdout
import errno
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from types import SimpleNamespace

# -I deliberately omits the script directory. Load ONLY this trusted sibling;
# neither the current directory nor the artifact is an import path.
_spec = importlib.util.spec_from_file_location('trusted_runner_isa', Path(__file__).resolve().with_name('runner_isa.py'))
smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(smoke)

GIB = 1 << 30
MAXINT = (1 << 63) - 1
HOLE = 14680064000
ARCHIVE = '929b6149ab8a45116fe39d785e6145f0a9df76d9c1f70606343c8eb4181c7ad9'
WIRE4 = '5b123dad59cede493fbde923fc64d59bb3fc999e203ea4051ad316b7f304d7f5'
CLEAR4 = '521852b7418e1f33aa38d7aedadcbbd270158814ae31647c44b00166d99ffe4f'
POINTS = (4096, 8192, 16384, 32768)
CASES = {
    1: dict(closed=7209, wire='1a19a961e0cd00f02adf14fd8c6b4579a4af64308d7530991cc5eda735e33053',
            clear='397027a83119582503310a9d833dd43d9d9e1df9b1d6bbd35c39203423086751',
            commits=(939, 1929, 3553, 7208), pages=(21, 41, 86, 164)),
    2: dict(closed=7988, wire='2b22db112ab511087cc209a79ee0eb5c043b1ea28a17fa218d9bf7ca0ed350b8',
            clear='64adfb019a5dc52708bb02a4d77c3e23ef1e756a317f26470a488418b21d2a19',
            commits=(1063, 2177, 4302, 7987), pages=(23, 44, 80, 164)),
}
# SHA-256 of each closed golden wire truncated to its four continuing C fstat
# offsets, computed locally from the original J1 stock controls, not from returns.
PREFIXES = {
    1: ('c413c508f7524d0ad9596d40cb5c449a00382711db88cae93548f6ace1cf7b54',
        '03de63572929777b1d68f09bbb77b769ad5bb9cb3cccfc10624bc2d1e4a4614a',
        '75e8d5cbccd0ea3f651b26618abc611779f90a04bed616efe9beafe90047ff55',
        '1f3ecbf251ee99ae49a5dca4626936f18d5d2510dfb6069afc053e05034bd3b6'),
    2: ('9d9d0beced9c34b30fb8fcca1a0916a23dec5e33ecacf643a15615cf209d56aa',
        '603e2d7da8d3e43fb325e78f362d3cee76d0576edde92a9aa9c36cc3ddfe9f51',
        'b2d1606b37048db400da8d0c80aec627fb71b9d5fc9e080e799c661cb78c0e35',
        'cb372f1c85df9cde49a89637a08dee5a8203388670e32909ca3e07057ab3cfea'),
}
ASSETS = {
    'stock.unit': '94d61af08475e74f137a97977aeb42f1f95f95d6a40124fca5fc1d3fd7112a39',
    'evex.unit': '8ac9aa8bd950abcd0ebcfb404287f8507187a1f109f543557b9613016507bbc2',
    'stock.probe': '72ceb819e3f9691664627dba0596b5961d5a8ab75b11f3415654f67366569305',
    'evex.probe': '02a535827e4dd4deb5c6e49934fe606e5a05185982b27e39d449219613bb0c0a',
    'model.c5': '729694cba4969b7d833686ed3f597ff04d3b226da849d5f8004ec020a0ed9563',
    **{f's{n}.{kind}': case[kind] for n, case in CASES.items() for kind in ('clear', 'wire')},
}
GUARD_SHA = '4789c8d66a2bc86a195d033c97e05d9b1007a9cbd17174bf95a9df941f0c8ced'
SCOUT_LIMITS = {'guard.json': 16384, 'result.json': 8192, 'scalar.u32': 2048, 'evex.u32': 2048}
RESOURCE = {'refused-low-headroom', 'host-ram-emergency', 'host-memory-reserve'}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def integer(v, low=0, high=MAXINT):
    return type(v) is int and low <= v <= high


def ident(value, expected):
    # GitHub env vars are strings; some dispatch metadata is serialized as ints.
    return type(value) in (str, int) and str(value) == str(expected)


def equal(a, b):
    """JSON equality, without silently accepting booleans/floats as byte counts."""
    if type(a) is not type(b):
        return False
    if type(b) is dict:
        return a.keys() == b.keys() and all(equal(a[k], v) for k, v in b.items())
    if type(b) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def fields(obj, **want):
    for key, val in want.items():
        need(key in obj and equal(obj[key], val), 'wrong field: ' + key)


def document(data):
    def unique(items):
        obj = {}
        for k, v in items:
            need(k not in obj, 'duplicate JSON key')
            obj[k] = v
        return obj

    def integral(s):
        need(len(s) <= 20, 'oversize integer')
        return int(s)

    def real(s):
        need(len(s) <= 40 and math.isfinite(float(s)), 'invalid floating point value')
        return float(s)

    obj = json.loads(data.decode('utf-8'), object_pairs_hook=unique, parse_int=integral,
                     parse_float=real, parse_constant=real)
    need(type(obj) is dict, 'expected JSON object')
    return obj


DIR_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY | os.O_CLOEXEC


@contextmanager
def directory(path, parent=None):
    # Traverse even ROOTDIR's components without following links. After opening
    # a directory, only look up checked single names relative to its pinned fd.
    if parent is None:
        parts = Path(os.path.abspath(path)).parts
        need(len(parts) > 1, 'expected an artifact directory, not /')
        # Ancestors need traversal only, never directory-read permission.
        anchor = os.O_PATH | os.O_NOFOLLOW | os.O_DIRECTORY | os.O_CLOEXEC
        fd = os.open(parts[0], anchor)
        try:
            for index, name in enumerate(parts[1:], start=1):
                new = os.open(name, DIR_FLAGS if index == len(parts)-1 else anchor, dir_fd=fd)
                os.close(fd)
                fd = new
            yield fd
        finally:
            os.close(fd)
    else:
        fd = os.open(path, DIR_FLAGS, dir_fd=parent)
        try:
            yield fd
        finally:
            os.close(fd)


def entries(fd, limit):
    out = set()
    with os.scandir(fd) as it:
        for ent in it:
            need(len(out) < limit and re.fullmatch(r'[a-zA-Z0-9_-][a-zA-Z0-9_.-]{0,95}', ent.name),
                 'too many entries or non-receipt name')
            mode = ent.stat(follow_symlinks=False).st_mode
            need(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'link or special file in receipt')
            out.add(ent.name)
    return out


def data(fd, name, limit):
    # O_PATH pins the inode without opening a device or blocking on a FIFO. The
    # only symlink we resolve is the kernel's own descriptor, after fstat.
    p = os.open(name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
    try:
        st = os.fstat(p)
        need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_size <= limit, 'invalid file: ' + name)
        with open('/proc/self/fd/' + str(p), 'rb') as f:
            raw = f.read(st.st_size + 1)
        need(len(raw) == st.st_size, 'changed file: ' + name)
        return raw
    finally:
        os.close(p)


class ScoutSnapshot:
    """Path-like view expected by runner_isa.verify; reads use validated bytes.

    The upstream verifier calls os.path.lexists only for the *absence* of the
    refused EVEX file. That lstat is relative to our still-open directory fd.
    """
    def __init__(self, fd, blobs):
        self.fd, self.blobs = fd, blobs

    def __truediv__(self, name):
        need(name in SCOUT_LIMITS, 'unexpected scout file')
        blob = self.blobs.get(name)
        class Leaf:
            def __fspath__(leaf): return f'/proc/self/fd/{self.fd}/{name}'
            def is_symlink(leaf): return False  # all blobs have passed no-follow fstat
            def is_file(leaf): return blob is not None
            def stat(leaf): return SimpleNamespace(st_size=len(blob))
            def read_bytes(leaf): return blob
        return Leaf()


def guard(g, step):
    status = g['status']
    cmd = g['command']
    script = ['tools/ci/runner_isa.py', 'run'] if step == 'isa' else ['tools/ci/guest_worker.py']
    need(type(cmd) is list and len(cmd) == len(script)+3 and cmd[0] in ('python3', '/usr/bin/python3') and
         cmd[1:-1] == ['-IB', *script] and type(cmd[-1]) is str and cmd[-1].startswith('/'),
         'unexpected guarded command or mode')
    nonnegative = ('reserve_bytes', 'min_ram_bytes', 'start_available_bytes', 'start_swap_total_bytes',
                   'start_swap_free_bytes', 'min_available_bytes', 'min_swap_free_bytes', 'peak_tree_rss_bytes',
                   'peak_tree_swap_bytes', 'peak_processes')
    need(all(integer(g[k]) for k in nonnegative) and g['reserve_bytes'] >= 2*GIB and g['min_ram_bytes'] >= GIB//2
         and type(g['wall_limit_seconds']) in (int, float) and g['wall_limit_seconds'] == 0,
         'missing guard observations or safeguards')
    start = g['start_available_bytes']
    need(g['min_available_bytes'] <= start and g['min_swap_free_bytes'] <= g['start_swap_free_bytes']
         <= g['start_swap_total_bytes'], 'contradictory guard headroom')
    if status == 'refused-low-headroom':
        need(start < 3*GIB and 'exit_code' not in g and g['peak_processes'] == 0, 'unsubstantiated startup refusal')
    else:
        need(start >= 3*GIB and integer(g['exit_code'], -255, 255) and type(g['wall_seconds']) in (int, float)
             and g['wall_seconds'] > 0, 'invalid guard termination')
        affinity = g['cpu_affinity']
        need(type(affinity) is list and 0 < len(affinity) <= 4096 and all(integer(cpu) for cpu in affinity)
             and sorted(set(affinity)) == affinity, 'missing guard CPU observations')
        if status == 'completed':
            need(g['exit_code'] == 0 and g['min_available_bytes'] >= g['min_ram_bytes'] and
                 g['peak_processes'] > 0 and g['peak_tree_rss_bytes'] > 0, 'guard did not complete normally')
        elif status == 'host-ram-emergency':
            need(g['min_available_bytes'] < g['min_ram_bytes'], 'unsubstantiated RAM floor refusal')
        elif status == 'host-memory-reserve':
            need(g['min_available_bytes'] + g['min_swap_free_bytes'] < g['reserve_bytes'],
                 'unsubstantiated combined-memory refusal')
        else:
            need(status == 'child-failed' and g['exit_code'] != 0, 'nonterminal or failed guard: ' + str(status)[:80])
    return {k: g[k] for k in (*nonnegative, 'status', 'cpu_affinity', 'exit_code', 'wall_seconds') if k in g}


def scout(fd, commit, run_id, attempt):
    names = entries(fd, len(SCOUT_LIMITS))
    need(names <= SCOUT_LIMITS.keys(), 'unknown ISA evidence')
    blobs = {n: data(fd, n, SCOUT_LIMITS[n]) for n in names}
    g = guard(document(blobs['guard.json']), 'isa')
    result = {'guard': g}
    if g['status'] != 'completed':
        return result
    r = document(blobs['result.json'])
    fields(r, commit=commit, run_id=run_id, attempt=attempt, test_paths_clean=True,
           scope='synthetic 256-bit dot correctness; no codec or timing claim')
    need(all(type(r[k]) is str and 0 < len(r[k]) < 512 for k in ('model', 'kernel', 'compiler', 'image', 'image_version')),
         'incomplete hosted VM identity')
    need(integer(r['evex_exit']) and integer(r['rows']), 'bad scout result types')
    # Independent, trusted checker regenerates all 512 lanes and checks the
    # instruction, CPUID/XCR0 predicate, exit, source/fixture hashes and output.
    with redirect_stdout(io.StringIO()):
        smoke.verify(ScoutSnapshot(fd, blobs), commit)
    op = re.fullmatch(r'[0-9a-f]+:[ \t]+((?:[0-9a-f]{2}[ \t]+){6,15})(?:\{evex\}[ \t]+)?'
                      r'vpdpbusd[ \t]+ymm\d+,[^\r\n]+', r['opcode'])
    need(op, 'malformed scout disassembly')
    raw = bytes.fromhex(op[1])
    need(raw[0] == 0x62 and raw[1] & 7 == 2 and raw[2] & 0x87 == 5 and raw[3] & 0x60 == 0x20
         and raw[4] == 0x50, 'scout bytes are not EVEX.256.66.0F38.W0 50')
    supported = r['outcome'] == 'executed-match'
    need(names == (set(SCOUT_LIMITS) if supported else set(SCOUT_LIMITS) - {'evex.u32'}), 'inconsistent ISA files')
    lanes = r['rows'] * 8
    result.update(scalar_lanes=lanes, evex_lanes=lanes if supported else 0, evex_exit=r['evex_exit'])
    result.update({k: r[k] for k in ('outcome', 'model', 'image', 'image_version', 'kernel', 'cpu_gate', 'opcode')})
    return result


def archive(r):
    fields(r, archive_sha256=ARCHIVE, wire_sha256=WIRE4, decoded_sha256=CLEAR4, decoded_bytes=4096,
           exit=0, isolated=True, damage_rejected=True, damaged_exit=1, pager_hole_bytes=HOLE)
    need(integer(r['wall_ns'], 1), 'incomplete archive-only D time')
    return {k: r[k] for k in ('archive_sha256', 'wire_sha256', 'decoded_sha256', 'decoded_bytes',
                               'damaged_exit', 'wall_ns', 'pager_hole_bytes')}


def schedule(phase):
    pairs = [(s, arm) for s in (1, 2) for arm in ('stock', 'evex')]
    if phase == 'reverse':
        pairs.reverse()
    return [(phase, s, arm, way) for s, arm in pairs for way in ('C', 'D')]


def score(tails, phase):
    by_direction = {}
    for way in ('C', 'D'):
        s, e = ([tails[phase, case, arm, way] for case in (1, 2)] for arm in ('stock', 'evex'))
        # Exact integer boundary tests on wall time, never average ratios, mix
        # C/D, use CPU time, or pool the two orders for the admission decision.
        windows = [100*b <= 105*a for a, b in zip(s, e)]
        pooled = 10*sum(s) >= 11*sum(e)
        by_direction[way] = dict(stock_tail_ns=s, evex_tail_ns=e, speedup=sum(s)/sum(e),
                                 per_case_speedup=[a/b for a, b in zip(s, e)], window_pass=windows,
                                 pooled=pooled, passed=pooled and all(windows))
    return by_direction


def preflight(room):
    host, cg = room['host_available_bytes'], room['cgroup_available_bytes']
    need(integer(host) and (cg is None or integer(cg)) and integer(room['disk_free_bytes']) and
         integer(room['ancestor_oom_kill_sum']), 'invalid memory/disk/OOM preflight')
    fields(room, available_bytes=host if cg is None else min(cg, host))


def usage(row, arm, cpuid, after, measured):
    u = row['usage']
    rlimits = {'as': [8_500_000_000, 8_500_000_000+HOLE] if measured else [512 << 20]*2,
               'fsize': [HOLE]*2 if measured else [160 << 20]*2, 'core': [0, 0]}
    fields(u, started=True, exit=0, socket_enetdown=True, rlimits=rlimits)
    for key in ('start_wall_ns', 'whole_wall_ns', 'whole_cpu_ns', 'peak_rss_bytes'):
        need(integer(u[key], 1), 'missing native usage: ' + key)
    room = u['preflight']
    preflight(room)
    need(room['available_bytes'] >= 8_000_000_000 and (not measured or room['disk_free_bytes'] > 32*GIB),
         'insufficient preflight for completed child')
    need(u['start_wall_ns'] >= after, 'out-of-order or overlapping native children')
    if arm == 'evex':
        fields(row, evex_cpuid=cpuid)  # the actual unit/probe's admission, not just the first smoke
    else:
        need('evex_cpuid' not in row, 'unexpected EVEX admission on stock arm')
    return u['start_wall_ns'] + u['whole_wall_ns']


def direction(row, case, way, end):
    g = CASES[case]
    if way == 'C':
        fields(row, input_bytes=32768, input_sha256=g['clear'], output_bytes=g['closed'], output_sha256=g['wire'],
               commits=[list(x) for x in zip(POINTS, g['commits'], PREFIXES[case])],
               boundary=[32768, g['closed']-1, g['closed']])
    else:
        fields(row, input_bytes=g['closed'], input_sha256=g['wire'], output_bytes=32768, output_sha256=g['clear'])
        need('commits' not in row and 'boundary' not in row, 'C accounting on fresh D')
    page = row['pager']
    fields(page, pagefile_bytes=HOLE, as_live_bytes=8_500_000_000+HOLE)
    need(integer(page['none_private_anon_bytes'], HOLE, 8_500_000_000 + HOLE) and
         integer(page['pagefile_allocated_bytes'], 0, HOLE-1) and page['pagefile_allocated_bytes'] % 512 == 0,
         'missing live sparse pager/mapping witness')
    marks = row['marks']
    need(type(marks) is list and len(marks) == 4, 'missing native marks')
    start = row['usage']['start_wall_ns']
    wall, cpu = start-1, 0
    for mark, pos, misses in zip(marks, POINTS, g['pages']):
        need(type(mark) is list and len(mark) == 6 and all(integer(v) for v in mark) and
             mark[0] == pos and mark[3:] == [misses, misses, 0], 'wrong logical mark')
        # wait4 rusage is quantized to microseconds; absolute MARK CPU is the
        # child's process clock. Wall MARKs use the same monotonic clock as usage.
        need(wall < mark[1] <= end and cpu < mark[2] <= row['usage']['whole_cpu_ns'] + 2000,
             'nonmonotonic/out-of-process MARK')
        wall, cpu = mark[1:3]
    tail = marks[-1][1] - marks[-2][1]
    fields(row, tail_wall_ns=tail, tail_cpu_ns=marks[-1][2]-marks[-2][2])
    return tail


def native(blobs, sc):
    r = document(blobs['native.json'])
    # Never import the producer to score its own return. Hash the TRUSTED
    # checkout's driver bytes and compare independent, fixed release/guard pins.
    driver = Path(__file__).resolve().with_name('g8_guest.py')
    fields(r, schema='g8-guest-v1', mode='guest', status='completed', active=None, reason=None,
           timing_qualified=False, asset_sha256=ASSETS, guard_sha256=GUARD_SHA,
           driver_sha256=hashlib.sha256(driver.read_bytes()).hexdigest())
    cpuid = [int(term.split('=')[1], 16) for term in sc['cpu_gate'].split()]
    units, pairs = r['units'], r['pairs']
    need(type(units) is list and len(units) == 2 and type(pairs) is list and len(pairs) in (4, 8),
         'expected both production units and one or two complete heats')
    end, oom = 0, []
    for arm, row in zip(('evex', 'stock'), units):
        fields(row, op='unit', arm=arm, synthetic_ok=True)
        end = usage(row, arm, cpuid, end, False)
        oom.append(row['usage']['preflight']['ancestor_oom_kill_sum'])
    tails = {}
    order = schedule('forward') + schedule('reverse')
    for i, pair in enumerate(pairs):
        ph, n, arm, _ = order[2*i]
        fields(pair, heat=ph, arm=arm, case=f's{n}')
        for way in ('C', 'D'):
            row = pair[way]
            end = usage(row, arm, cpuid, end, True)
            tails[ph, n, arm, way] = direction(row, n, way, end)
            oom.append(row['usage']['preflight']['ancestor_oom_kill_sum'])
    need(oom == sorted(oom), 'decreasing ancestor OOM counter across serial children')
    gates, scores = {}, {}
    for ph in ('forward', 'reverse'):
        if ph == 'reverse' and not scores['forward']['passed']:
            need(len(pairs) == 4, 'reverse measured after a forward loss')
            break
        if ph == 'reverse':
            need(len(pairs) == 8, 'missing required reverse after forward pass')
        g = gates[ph] = score(tails, ph)
        by = {}
        for way, v in g.items():
            by[way] = {'pooled_speedup': v['speedup'],
                       'per_case_speedup': dict(zip(('s1', 's2'), v['per_case_speedup']))}
        scores[ph] = {'passed': all(v['passed'] for v in g.values()), 'by_direction': by}
    fields(r, scores=scores)
    verdict = ('no-gain-forward' if not scores['forward']['passed'] else
               'conditional-two-order-pass' if scores['reverse']['passed'] else 'no-gain-reverse')
    return dict(fixture_verdict=verdict, gates=gates, checked_C_fresh_D_pairs=len(pairs),
                closed_bytes=[CASES[n]['closed'] for n in (1, 2)], fresh_D_bytes_per_pair=32768,
                ancestor_oom_kill_sum_first_last=[oom[0], oom[-1]])


def codec_files(fd):
    limits = {'guard.json': 16384, 'archive.json': 8192, 'state.json': 8192, 'native.json': 1 << 20}
    names = entries(fd, len(limits))
    need(names <= limits.keys(), 'unknown codec evidence')
    return {name: data(fd, name, limits[name]) for name in names}


def worker_refusal(blobs):
    state = document(blobs['state.json'])
    fields(state, status='resource-refused')
    reason = state['reason']
    need(re.fullmatch(r'guest_worker\.py:[0-9]{1,6}', state['site']), 'missing capacity refusal site')
    if 'native.json' not in blobs:
        need(reason in ('scratch volume lacks >32 GiB free', 'less than 8 GB available to job',
                        'inherited rlimit too low'), 'unrecognized archive preflight refusal')
    else:
        n = document(blobs['native.json'])
        fields(n, schema='g8-guest-v1', mode='guest', status='skipped-capacity', timing_qualified=False, pairs=[])
        why = n['reason']
        need(reason == 'native preflight: ' + why, 'inconsistent native refusal')
        if why in ('memory-headroom', 'scratch-space', 'inherited-hard-limit'):
            a = n['active']
            need(type(a) is dict, 'missing refused preflight')
            row = a if a.get('op') == 'unit' else a.get('D', a.get('C'))
            fields(row['usage'], started=False)
            room = row['usage']['preflight']
            preflight(room)
            if why == 'memory-headroom':
                need(room['available_bytes'] < 8_000_000_000, 'unsupported memory refusal')
            if why == 'scratch-space':
                need(room['disk_free_bytes'] <= 32*GIB, 'unsupported scratch refusal')
        elif why == 'cgroup-oom-kill-observed':
            # A SIGKILL of a unit before any codec timing. The producer observed
            # an ancestor-counter increase; it does not expose a post-kill count.
            a = n['active']
            fields(a, op='unit')
            fields(a['usage'], started=True, exit=-9)
            preflight(a['usage']['preflight'])
        else:
            need(why == 'os-error' and integer(n['errno']) and n['errno'] in (errno.ENOMEM, errno.ENOSPC, errno.EDQUOT),
                 'not a capacity errno')
    return reason


def codec(fd, outcome, sc):
    blobs = codec_files(fd)
    g = guard(document(blobs['guard.json']), 'codec')
    summary = {'guard': g}
    if 'archive.json' in blobs:
        summary['archive'] = archive(document(blobs['archive.json']))
    if outcome == 'resource-refused':
        if g['status'] in RESOURCE:
            summary['reason'] = g['status']
        else:
            fields(g, status='child-failed', exit_code=75)
            summary['reason'] = worker_refusal(blobs)
        return summary
    if outcome == 'failed':
        need(g['status'] not in RESOURCE, 'resource refusal mislabelled as engineering failure')
        if 'native.json' in blobs:
            n = document(blobs['native.json'])
            if n.get('status') in ('failed', 'failed-capacity', 'running'):
                summary['native_status'] = n['status']
        return summary  # No speed decision on partial records, even if some pairs finished.
    fields(g, status='completed', exit_code=0)
    need(document(blobs['state.json']) == {'mode': 'guest', 'status': 'completed'} and 'archive' in summary,
         'not the completed archive + guest workload')
    summary.update(native(blobs, sc))
    return summary


def inspect_slot(fd, slot, count, commit, run_id, attempt):
    names = entries(fd, 3)
    need('dispatch.json' in names and names <= {'dispatch.json', 'isa', 'codec'}, 'invalid slot contents')
    d = document(data(fd, 'dispatch.json', 8192))
    fields(d, commit=commit)
    if 'scope' in d:
        fields(d, scope='guest engineering; no judge timing')
    need(ident(d['run_id'], run_id) and ident(d['run_attempt'], attempt) and ident(d['slot'], slot), 'wrong slot/run identity')
    outcome = d['outcome']
    need(outcome in ('failed', 'unsupported', 'resource-refused', 'completed'), 'unknown dispatch outcome')
    need(slot == count or outcome == 'unsupported', 'additional VM after a non-refusal')
    summary = {'slot': slot, 'outcome': outcome}
    if 'isa' not in names:
        need(outcome == 'failed' and 'codec' not in names, 'no ISA evidence')
        return summary
    with directory('isa', fd) as i:
        sc = summary['isa'] = scout(i, commit, run_id, attempt)
    if sc['guard']['status'] != 'completed':
        need('codec' not in names and outcome == ('resource-refused' if sc['guard']['status'] in RESOURCE else 'failed'),
             'codec or wrong dispatch result after scout guard refusal/failure')
    elif sc['outcome'] == 'unsupported':
        need(outcome == 'unsupported' and 'codec' not in names, 'a CPUID refusal must not run the codec')
    else:
        need(outcome != 'unsupported', 'retry on a supported VM')
        if 'codec' in names:
            with directory('codec', fd) as c:
                summary['codec'] = codec(c, outcome, sc)
        else:
            need(outcome == 'failed', 'eligible VM without codec evidence')
    # The original mandatory identity is above. Also cross-check activity step
    # outcomes when present; a skipped or cancelled workload isn't a comparison.
    if 'steps' in d and outcome != 'failed':
        if outcome == 'resource-refused':
            steps = ('success', 'success', 'failure') if 'codec' in names else ('failure', 'skipped', 'skipped')
        else:
            step = 'skipped' if outcome == 'unsupported' else 'success'
            steps = ('success', step, step)
        fields(d['steps'], **dict(zip(('isa', 'space', 'codec'), steps)))
    return summary


def inspect(root, commit, run_id, attempt):
    need(re.fullmatch(r'[0-9a-f]{40}', commit) and re.fullmatch(r'[1-9][0-9]{0,18}', run_id) and
         re.fullmatch(r'[1-9][0-9]{0,8}', attempt), 'expected full commit SHA and positive run ID/attempt')
    slots = []
    report = dict(commit=commit, run_id=run_id, run_attempt=attempt, slots=slots,
                  scope='Guest engineering only; not bare metal, prize eligibility, full-corpus size or judge timing.')
    with directory(root) as fd:
        names = entries(fd, 6)
        count = len(names)
        need(count and names == {f'slot-{n}' for n in range(1, count + 1)}, 'slots must be a contiguous prefix of 1..6')
        for n in range(1, count + 1):
            try:
                with directory(f'slot-{n}', fd) as s:
                    slots.append(inspect_slot(s, n, count, commit, run_id, attempt))
            except (ValueError, KeyError, TypeError, IndexError, RecursionError, OSError) as e:
                raise ValueError(f'slot-{n}: {str(e)[:300]}') from e
    last = slots[-1]['outcome']
    if last == 'unsupported':
        need(count == 6, 'incomplete scout chain; fewer than six verified refusals')
        code, status = 3, 'exhausted-unsupported'
    elif last == 'resource-refused':
        code, status = 4, 'insufficient-resources'
    elif last == 'failed':
        code, status = 1, 'engineering-failure'
    else:
        code, status = 0, 'completed-native-conditional'
    return code, {'status': status, **report}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    for flag in ('--commit', '--run-id', '--attempt'):
        p.add_argument(flag, required=True)
    a = p.parse_args()
    try:
        code, report = inspect(a.root, a.commit, a.run_id, a.attempt)
    except (ValueError, KeyError, TypeError, IndexError, RecursionError, OSError) as e:
        code, report = 1, dict(status='engineering-failure', error=str(e)[:500])
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
