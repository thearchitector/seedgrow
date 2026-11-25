"""GitHub-hosted runner smoke test, not a benchmark. Verify downloads as data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CPP = Path(__file__).with_name('isa_smoke.cpp')
SHA = lambda data: hashlib.sha256(data).hexdigest()


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def vectors():
    # Deliberately cross the signed accumulator boundaries: saturating is wrong.
    frames, answers = bytearray(), bytearray()
    for width in (64, 192):
        for case in range(32):
            seeds = [(0, 0x7ffffffe, 0x80000001, 0xfffffffe)[(case+i) % 4] for i in range(8)]
            a = bytes(255 if case < 2 else (k*29 + (k//4)*13 + case*17) % 256 for k in range(width))
            w = [7 if case == 0 else -7 if case == 1 else (k*7 + k//32 + case*3) % 15 - 7 for k in range(width)]
            frames += struct.pack('<B8I', width//32, *seeds) + a + bytes(v & 255 for v in w)
            for lane, seed in enumerate(seeds):
                exact = seed + sum(a[j]*w[j] for block in range(0, width, 32)
                                   for j in range(block+4*lane, block+4*lane+4))
                answers += struct.pack('<I', exact & 0xffffffff)
    return bytes(frames), bytes(answers)


def run(out):
    # Expect one fresh, resource-guarded x64 Linux job. Never set affinity or a thread/time limit.
    require(platform.machine() == 'x86_64' and platform.system() == 'Linux', 'requires Linux x86-64')
    require(any(p.resolve().name == 'resource.lock' for p in Path('/proc/self/fd').iterdir()), 'missing guard fd')
    out.mkdir(parents=True, exist_ok=True)
    require(not any((out/n).exists() for n in ('result.json', 'scalar.u32', 'evex.u32')), 'stale receipt')
    src, expected = vectors()
    commit = subprocess.check_output(['git', '-C', ROOT, 'rev-parse', 'HEAD'], text=True).strip()
    require(os.environ.get('GITHUB_SHA', commit) == commit, 'checkout SHA differs from event SHA')
    paths = ['tools/ci', 'tools/resource_guard.py', '.github/workflows/scratchpad.yml']
    dirty = subprocess.run(['git', '-C', ROOT, 'diff', '--quiet', 'HEAD', '--', *paths]).returncode
    require(dirty in (0, 1) and (not os.getenv('GITHUB_RUN_ID') or dirty == 0), 'dirty hosted checkout')
    metadata = {'commit': commit, 'test_paths_clean': not dirty,
                'image': os.getenv('ImageOS'), 'image_version': os.getenv('ImageVersion'),
                'run_id': os.getenv('GITHUB_RUN_ID'), 'attempt': os.getenv('GITHUB_RUN_ATTEMPT'),
                'kernel': platform.release(), 'model': next((v.split(':', 1)[1].strip() for v in
                    Path('/proc/cpuinfo').read_text().splitlines() if v.startswith('model name')), None),
                'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
                'fixture_sha256': SHA(src), 'scalar_oracle_sha256': SHA(expected), 'source_sha256': SHA(CPP.read_bytes()),
                'rows': len(expected)//32, 'scope': 'synthetic 256-bit dot correctness; no codec or timing claim'}
    # Keep compiler intermediates on the same authorized scratch volume as the receipt.
    with tempfile.TemporaryDirectory(dir=out.resolve()) as tmp:
        exe = Path(tmp)/'smoke'
        def compile_limits():
            lim = resource.getrlimit(resource.RLIMIT_AS)[0]
            cap = 512 << 20 if lim == resource.RLIM_INFINITY else min(lim, 512 << 20)
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        subprocess.run(['g++', '-O2', '-std=c++17', '-march=x86-64', '-fno-tree-vectorize', '-Wall', '-Wextra',
                        '-Werror', CPP, '-o', exe], env={**os.environ, 'TMPDIR': tmp},
                       preexec_fn=compile_limits, check=True)
        dis = subprocess.check_output(['objdump', '-d', '-M', 'intel', '--disassemble=dot_evex', exe], text=True)
        dot = next((s.strip() for s in dis.splitlines() if re.search(r':\s+62\s.*\bvpdpbusd\s+ymm', s)), None)
        require(dot is not None, 'no non-saturating 256-bit EVEX dot instruction in target routine')
        metadata['opcode'] = dot
        for arm in ('scalar', 'evex'):
            p = subprocess.run([exe, arm], input=src, capture_output=True)
            if arm == 'evex':
                metadata.update(cpu_gate=p.stderr.decode().strip(), evex_exit=p.returncode)
                if p.returncode == 77:
                    require(not p.stdout, 'refusal emitted results')
                    metadata['outcome'] = 'unsupported'
                    break
                metadata['outcome'] = 'executed-match'
            require(p.returncode == 0 and p.stdout == expected, f'{arm}: exit {p.returncode} or wrong lane values')
            (out/(arm+'.u32')).write_bytes(p.stdout)
    (out/'result.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(f"Scalar matched {len(expected)//4} lanes; EVEX: {metadata['outcome']}. {metadata['model']}")


def verify(out, commit):
    # Flat allowlisted files only. Bound sizes and never execute a downloaded program or command.
    def data(name, limit):
        p = out/name
        require(not p.is_symlink() and p.is_file() and p.stat().st_size <= limit, 'invalid receipt: '+name)
        return p.read_bytes()
    r = json.loads(data('result.json', 8192)); guard = json.loads(data('guard.json', 16384))
    require(guard['status'] == 'completed' and guard['exit_code'] == guard['wall_limit_seconds'] == 0,
            'guard did not complete')
    require(re.fullmatch(r'[0-9a-f]{40}', commit) and r['commit'] == commit, 'wrong commit')
    require(not r['run_id'] or r['test_paths_clean'] is True, 'dirty hosted checkout')
    src, expected = vectors()
    require(r['rows'] == len(expected)//32 and r['fixture_sha256'] == SHA(src) and
            r['source_sha256'] == SHA(CPP.read_bytes()) and r['scalar_oracle_sha256'] == SHA(expected) and
            data('scalar.u32', len(expected)) == expected, 'wrong scalar result or source')
    cp = re.fullmatch(r'cpuid_1_ecx=([0-9a-f]{8}) cpuid_7_ebx=([0-9a-f]{8}) cpuid_7_ecx=([0-9a-f]{8}) xcr0=([0-9a-f]{16})', r['cpu_gate'])
    require(cp and re.search(r':\s+62\s.*\bvpdpbusd\s+ymm', r['opcode']), 'missing CPUID/XCR0/opcode evidence')
    c1, b7, c7, xcr = (int(v, 16) for v in cp.groups())
    admitted = (c1 & (7 << 26) == 7 << 26 and b7 & 0x80010000 == 0x80010000 and
                bool(c7 & (1 << 11)) and xcr & 0xe6 == 0xe6)
    if admitted:
        require(r['outcome'] == 'executed-match' and r['evex_exit'] == 0 and
                data('evex.u32', len(expected)) == expected, 'wrong EVEX result')
    else:
        require(r['outcome'] == 'unsupported' and r['evex_exit'] == 77 and not os.path.lexists(out/'evex.u32'),
                'missing CPU support is a refusal, not a pass')
    print(f"Verified {commit}: scalar exact; EVEX {r['outcome']}. Not a codec timing.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for mode in ('run', 'verify'):
        p = sub.add_parser(mode); p.add_argument('out', type=Path)
        if mode == 'verify': p.add_argument('--commit', required=True)
    args = parser.parse_args()
    if args.mode == 'run': run(args.out)
    else: verify(args.out, args.commit)
