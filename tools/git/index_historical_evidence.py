#!/usr/bin/env python3
"""Read-only historical file hashing; writes only explicitly requested index files."""
import argparse,csv,hashlib,json,os,stat
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def index(root,output):
    root=Path(root).resolve();output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    rows=[];skipped=Counter()
    for scope in ('results','build','docs','software'):
        for base,dirs,files in os.walk(root/scope,followlinks=False):
            relbase=Path(base).relative_to(root)
            for d in list(dirs):
                p=Path(base)/d
                if d in ('venvs','.venv','__pycache__','.Xil','xsim.dir','.git') or (scope=='build' and d=='local_git_20261103'):
                    dirs.remove(d);skipped[d]+=1
            for name in sorted(files):
                p=Path(base)/name;rel=p.relative_to(root)
                if scope in ('docs','software') and p.suffix.lower()!='.zip':continue
                before=p.lstat()
                if stat.S_ISLNK(before.st_mode):
                    target=os.readlink(p);digest=hashlib.sha256(target.encode()).hexdigest();kind='SYMLINK_TARGET_STRING';size=len(target.encode())
                elif stat.S_ISREG(before.st_mode):
                    target='';h=hashlib.sha256()
                    with p.open('rb') as f:
                        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
                    after=p.stat()
                    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError(f'file changed while reading: {rel}')
                    digest=h.hexdigest();size=before.st_size;kind='FILE'
                else:continue
                category='HISTORICAL_RESULT' if scope=='results' else 'HISTORICAL_BUILD_EVIDENCE'
                if scope in ('docs','software'):category='LOCAL_INPUT_ARCHIVE'
                if p.suffix.lower() in ('.bit','.ltx'):category='FPGA_IMAGE_OR_DEBUG_ASSOCIATION'
                if p.suffix.lower() in ('.wdb','.vcd','.fst','.fsdb'):category='WAVEFORM_EVIDENCE'
                rows.append(dict(path=str(rel),category=category,kind=kind,bytes=size,sha256=digest,link_target=target))
    rows.sort(key=lambda r:r['path'])
    with output.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report=dict(date='2026-11-03',scope='Local historical build/results and original ZIP archives; not proof of PASS',files=len(rows),
        total_bytes=sum(r['bytes'] for r in rows),categories=dict(Counter(r['category'] for r in rows)),
        skipped_cache_directories=dict(skipped),index_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        restoration='Files remain at original relative paths. Index is not an off-machine backup. No evidence regenerated.')
    output.with_suffix('.summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);a=p.parse_args();index(a.root,a.output)
