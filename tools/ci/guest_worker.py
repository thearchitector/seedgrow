"""Private, bounded codec payload on the admitted VM. No returned executable or network inputs."""
import argparse
import base64
import ctypes as C
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zipfile

HERE = Path(__file__).resolve().parent
FIX = HERE/'fixture'
MANIFEST = 'd56827e16d2419c5a411ac922d8ddef2d1ecb81397886dde8613a901e5fb0507'
MAGIC = b'SG8CIP01'
CLEAR4 = '521852b7418e1f33aa38d7aedadcbbd270158814ae31647c44b00166d99ffe4f'
WIRE4 = '5b123dad59cede493fbde923fc64d59bb3fc999e203ea4051ad316b7f304d7f5'
FSIZE = 14680064000
WORK_AS = 8500000000


def sha(data): return hashlib.sha256(data).hexdigest()


def need(ok, reason):
    if not ok: raise ValueError(reason)


def dump(p, obj):
    t = p.with_suffix('.tmp')
    t.write_text(json.dumps(obj, indent=2)+'\n')
    t.replace(p)


class CapacityError(RuntimeError): pass


def available():
    mem = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                   if line.startswith('MemAvailable:')))*1024
    group = next((l[3:] for l in Path('/proc/self/cgroup').read_text().splitlines() if l.startswith('0::')), None)
    cgroot = Path('/sys/fs/cgroup'); remaining = []
    if group is not None:
        # Cgroup namespaces may expose the guest's group as the mount root.
        rel = Path(group.lstrip('/'))
        c = cgroot/rel if '..' not in rel.parts and (cgroot/rel/'memory.max').is_file() else cgroot
        while c.is_relative_to(cgroot):
            if (c/'memory.max').is_file():
                v = (c/'memory.max').read_text().strip()
                if v != 'max': remaining.append(int(v)-int((c/'memory.current').read_text()))
            if c == cgroot: break
            c = c.parent
    return min([mem]+remaining)


def capacity(path):
    free = shutil.disk_usage(path).free
    if free <= 32 << 30: raise CapacityError('scratch volume lacks >32 GiB free')
    if available() < 8000000000: raise CapacityError('less than 8 GB available to job')
    for limit, want in ((resource.RLIMIT_AS, WORK_AS+FSIZE), (resource.RLIMIT_FSIZE, FSIZE)):
        _, hard = resource.getrlimit(limit)
        if hard != resource.RLIM_INFINITY and hard < want: raise CapacityError('inherited rlimit too low')


def decrypt(blob, key):
    # OpenSSL 3 from the OS: AES-256-GCM, one 96-bit nonce and a 128-bit tag. No pip or key argv.
    need(len(key) == 32 and blob[:8] == MAGIC and 36 < len(blob) < 12 << 20, 'bad encrypted envelope')
    lib = C.CDLL('libcrypto.so.3'); ptr, integer, buf = C.c_void_p, C.c_int, C.c_char_p
    def fn(name, ret, *args):
        f = getattr(lib, name); f.restype = ret; f.argtypes = args; return f
    ctx = fn('EVP_CIPHER_CTX_new', ptr)(); need(ctx, 'cipher allocation failed')
    try:
        init = fn('EVP_DecryptInit_ex', integer, ptr, ptr, ptr, buf, buf)
        update = fn('EVP_DecryptUpdate', integer, ptr, ptr, C.POINTER(integer), buf, integer)
        final = fn('EVP_DecryptFinal_ex', integer, ptr, ptr, C.POINTER(integer))
        alg = fn('EVP_aes_256_gcm', ptr)(); n = integer(); tag = C.create_string_buffer(blob[-16:]); data = blob[20:-16]
        out = C.create_string_buffer(len(data)+16)
        need(init(ctx, alg, None, key, blob[8:20]) == 1 and
             update(ctx, None, C.byref(n), MAGIC, len(MAGIC)) == 1 and
             update(ctx, out, C.byref(n), data, len(data)) == 1 and n.value == len(data), 'decrypt failed')
        ctrl = fn('EVP_CIPHER_CTX_ctrl', integer, ptr, integer, integer, ptr)
        need(ctrl(ctx, 0x11, 16, tag) == 1 and final(ctx, C.byref(out, n.value), C.byref(n)) == 1 and n.value == 0,
             'fixture authentication failed')
        return out.raw[:len(data)]
    finally: fn('EVP_CIPHER_CTX_free', None, ptr)(ctx)


def unpack(assets, key):
    raw = (FIX/'manifest.json').read_bytes(); need(sha(raw) == MANIFEST, 'manifest mismatch'); m = json.loads(raw)
    aes = FIX/'guest.aes'; need(aes.stat().st_size == m['cipher_bytes'] < 12 << 20, 'cipher length')
    ct = aes.read_bytes(); need(sha(ct) == m['cipher_sha256'], 'cipher SHA256')
    with zipfile.ZipFile(io.BytesIO(decrypt(ct, key))) as z:
        need(sorted(z.namelist()) == sorted(m['files']), 'member set')
        for name, spec in m['files'].items():
            need(Path(name).name == name and z.getinfo(name).file_size == spec['bytes'] <= 4000000, 'member extent')
            b = z.read(name); need(sha(b) == spec['sha256'], 'member digest')
            p = assets/name; p.write_bytes(b); p.chmod(0o700 if name.endswith(('.sfx','.unit','.probe')) else 0o600)


def restrict_archive():
    resource.setrlimit(resource.RLIMIT_CORE, (0,0)); resource.setrlimit(resource.RLIMIT_FSIZE, (FSIZE,FSIZE))
    resource.setrlimit(resource.RLIMIT_AS, (96 << 20, WORK_AS+FSIZE))
    sec = C.CDLL('libseccomp.so.2'); sec.seccomp_init.argtypes = [C.c_uint32]; sec.seccomp_init.restype = C.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes = [C.c_char_p]; sec.seccomp_rule_add.argtypes = [C.c_void_p,C.c_uint32,C.c_int,C.c_uint]
    sec.seccomp_load.argtypes = sec.seccomp_release.argtypes = [C.c_void_p]
    ctx = sec.seccomp_init(0x7fff0000); need(ctx, 'seccomp init')
    for name in (b'socket', b'socketpair', b'io_uring_setup'):
        nr = sec.seccomp_syscall_resolve_name(name); need(nr >= 0 and sec.seccomp_rule_add(ctx,0x50000|errno.ENETDOWN,nr,0) == 0, 'seccomp rule')
    need(sec.seccomp_load(ctx) == 0, 'seccomp load'); sec.seccomp_release(ctx)


def archive4(assets, scratch, out):
    img = (assets/'archive4.sfx').read_bytes(); magic, i, w, n, h = struct.unpack('<8sQQQ64s',img[-96:])
    need((magic,i,w,n,h.decode()) == (b'NEIFSFX1',3308272,1002,4096,WIRE4) and len(img)==96+i+w and
         sha(img[i:-96])==WIRE4, 'archive envelope')
    rec = {'archive_sha256':sha(img), 'wire_sha256':WIRE4}
    for bad in (False, True):
        capacity(scratch)
        with tempfile.TemporaryDirectory(dir=scratch) as t:
            d=Path(t); a=d/'archive'; data=bytearray(img)
            if bad: data[i+8]^=1
            a.write_bytes(data); a.chmod(0o700); need(list(d.iterdir())==[a], 'archive not alone')
            before=time.monotonic_ns(); p=subprocess.run(['./archive'],cwd=d,env={'LC_ALL':'C','TMPDIR':'.','PATH':'/usr/bin:/bin'},
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,preexec_fn=restrict_archive); ns=time.monotonic_ns()-before
            if not bad:
                need(p.returncode==0 and {q.name for q in d.iterdir()}=={'archive','stream.prefix'}, 'archive-only D failed')
                wire=(d/'stream.prefix').read_bytes(); need(len(wire)==4096 and sha(wire)==CLEAR4 and p.stderr.count(b'PQ hole 14680064000 verified')==1,'archive-only output or hole')
                rec.update(decoded_sha256=CLEAR4,decoded_bytes=4096,exit=0,isolated=True,wall_ns=ns,pager_hole_bytes=FSIZE)
            else:
                need(p.returncode>0 and list(d.iterdir())==[a] and b'archive payload stamp' in p.stderr,'corrupt archive not rejected as expected')
                rec.update(damage_rejected=True,damaged_exit=p.returncode)
    dump(out/'archive.json', rec)


def run(out, mode):
    os.umask(0o077); need(any(d.resolve().name=='resource.lock' for d in Path('/proc/self/fd').iterdir()), 'not guarded')
    need(mode=='guest' or not os.getenv('GITHUB_ACTIONS'), 'no rehearsal on Actions'); need(platform.machine()=='x86_64','wrong architecture')
    need(not (out/'state.json').exists(), 'stale codec state'); out.mkdir(exist_ok=True,parents=True)
    encoded = os.environ.pop('SG_GUEST_KEY',''); key = base64.b64decode(encoded.strip(),validate=True); del encoded
    scratch=Path(os.environ['TMPDIR']).resolve(); capacity(scratch)
    need('x86-64-v3 (supported, searched)' in subprocess.check_output(['/lib64/ld-linux-x86-64.so.2','--help'],text=True,env={'LC_ALL':'C'}),'v3 not available')
    with tempfile.TemporaryDirectory(dir=scratch,prefix='sg8-') as t:
        work=Path(t); tempfile.tempdir=str(work); os.environ['TMPDIR']=str(work); assets=work/'private';assets.mkdir()
        with (work/'sparse-test').open('xb') as f:
            f.seek((8 << 20)-1); f.write(b'\0'); f.flush(); need(os.fstat(f.fileno()).st_blocks*512 < 1 << 20,'not sparse')
        (work/'sparse-test').unlink(); unpack(assets,key); del key
        archive4(assets,work,out)
        if mode!='archive-rehearsal':
            sys.path.insert(0,str(HERE)); import g8_guest
            native = g8_guest.run(assets, out, mode)
            if native['status'] == 'skipped-capacity': raise CapacityError('native preflight: '+native['reason'])
            need(native['status']=='completed' and native['mode']==mode and native['pairs'], 'native correctness/engineering failure')
    dump(out/'state.json',{'status':'completed','mode':mode}); print(f'{mode}: bounded fixtures complete; no qualification claim')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('out',type=Path);p.add_argument('--mode',choices=('guest','stock-rehearsal','archive-rehearsal'),default='guest');args=p.parse_args();out=args.out.resolve()
    try: run(out,args.mode)
    except Exception as e:
        # Public artifact/console never contain private payload bytes, native output, keys or environment dumps.
        refused=isinstance(e,CapacityError); status='resource-refused' if refused else 'failed'; reason=str(e) if refused else f'{type(e).__name__} at {Path(__file__).name if e.__traceback__ is None else "bounded workload"}'
        import traceback
        site=traceback.extract_tb(e.__traceback__)[-1]; print(f'{status}: {reason} [{Path(site.filename).name}:{site.lineno}]',file=sys.stderr)
        out.mkdir(exist_ok=True,parents=True);dump(out/'state.json',{'status':status,'site':f'{Path(site.filename).name}:{site.lineno}','reason':reason});sys.exit(75 if refused else 1)
