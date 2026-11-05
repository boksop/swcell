#!/usr/bin/env python3
"""Prepare byte-exact V3.1 evidence and Release assets, without Git/network writes."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[2]
TAG='m20-v3.1-autonomous-fpga-verified'
BIT_NAME='swcell_m20_v3_1_fw0_2_xc7k325tffg900-2_FUNCTIONAL_STORAGE.bit'
FPGA='build/fpga/m20/autonomous/restart_plus_r2'
SIM='build/sim/m20_v31/restart_plus_joint_r2'
BIT_SHA='181fb8844407a69f405594440245dc5ed1e50a24e81e103d194aa531835cfd0f'
ROM_SHA='ae5be5055052c8ea9c8a5e4d00de5dcaf2dfe531e84a57fb9dec0b4feef71619'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def selection():
    chosen={}
    def add(source,target=None):
        target=target or source
        if target.endswith('.log'):target=target[:-4]+'.txt'
        if target in chosen:raise ValueError('duplicate evidence target '+target)
        path=ROOT/source
        if not path.is_file() or path.is_symlink():raise ValueError('missing/nonregular '+source)
        if path.stat().st_size>512*1024:raise ValueError('not small evidence '+source)
        chosen[target]=dict(source=source,copy=target,bytes=path.stat().st_size,sha256=digest(path))
    for name in ('timing.rpt','utilization.rpt','synth_utilization.rpt','synth_timing.rpt',
                 'drc.rpt','cdc.rpt','check_timing.rpt','ram.rpt','io.rpt','source_sha256.txt',
                 'software_profile.txt','cpu_mux_cells.txt','route_audit/counts.json',
                 'route_audit/mux_mapping.csv','route_audit/oled_drivers.csv','route_audit/clocks.rpt'):
        add(FPGA+'/'+name,'fpga/'+name)
    for name in ('xsim/compile.log','xsim/elaborate.log','xsim/simulation.log','verification.json',
                 'final_ram.memh','spi_bytes.csv','drawing_cycles.csv','gddram_screens.json',
                 'parsed_uart/summary.json'):
        add(SIM+'/'+name,'simulation/joint/'+name)
    for name in ('compile.log','gpio.log','memory.log','control.log','probe.memh'):
        add('build/sim/m20_v31/units_r4/'+name,'simulation/units/'+name)
    for name in ('isa','illegal','datapath','memory','instructions','games'):
        add('build/sim/m20_v31/v3_core_baseline_r1/xsim/'+name+'.log','simulation/core/'+name+'.txt')
    for suite in ('instructions','games'):
        for name in ('comparison.json','three_way_comparison.json'):
            add('build/sim/m20_v31/v3_core_baseline_r1/'+suite+'/'+name,'simulation/core/'+suite+'/'+name)
    for name in ('restart_plus_python_r2.txt','restart_plus_relocation.json','restart_plus_program_r2.txt',
                 'restart_plus_build_r2.txt','restart_plus_route_audit_r2.txt','restart_plus_capture_r2.txt'):
        add('build/m20_v31/'+name,'final/'+name)
    for name in ('pong_restart_before_fix.txt','plus_first_encoding.json',
                 'restart_plus_python_r1.txt','restart_plus_joint_r1.txt','restart_plus_build_r1.txt'):
        add('build/m20_v31/'+name,'negative/'+name)
    for run in ('20261105_first_download_r1','20261105_debug_controls_r1','20261105_restart_plus_r2'):
        base=ROOT/'results/M20_V31'/run
        for p in sorted(base.iterdir()):
            if p.suffix in ('.json','.jsonl','.csv') and p.is_file():
                add(str(p.relative_to(ROOT)),'hardware/'+run+'/'+p.name)
    old=ROOT/'build/m20_v31/pre_fix_20261105'
    for p in sorted(old.rglob('*')):
        if p.is_file():
            target='initial_r5_source/'+str(p.relative_to(old))
            if p.suffix=='.py':target+='.txt'
            add(str(p.relative_to(ROOT)),target)
    return list(chosen.values())


def prepare(out):
    if out.exists():raise ValueError('Use fresh archive output')
    rows=selection()
    bit=ROOT/FPGA/'swcell_m20_v31_top.bit'
    rom=ROOT/'software/m20_300/v31/m20_v31.memh'
    assert digest(bit)==BIT_SHA and digest(rom)==ROM_SHA
    for line in (ROOT/FPGA/'source_sha256.txt').read_text().splitlines():
        sha,name=line.split(None,1);assert digest(ROOT/name)==sha,name
    out.mkdir(parents=True);small=out/'git_evidence';small.mkdir();assets=out/'assets';assets.mkdir()
    for row in rows:
        destination=small/row['copy'];destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/row['source'],destination)
        assert digest(destination)==row['sha256'] and digest(ROOT/row['source'])==row['sha256']
    manifest=dict(schema_version=1,date='2026-11-05',firmware='M20-V31-0.2',mode='FUNCTIONAL_STORAGE',
                  tag=TAG,count=len(rows),bytes=sum(r['bytes'] for r in rows),files=rows,
                  policy='Exact contents, .log copies explicitly renamed .txt; old failures remain failures. No cache/bit/waves in Git. Manifest excludes itself.')
    (small/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copyfile(bit,assets/BIT_NAME);assert digest(assets/BIT_NAME)==BIT_SHA
    # Full final digital trace plus all selected evidence, including failures.
    full={row['source']:row for row in rows}
    for p in sorted((ROOT/SIM).rglob('*')):
        if not p.is_file() or p.is_symlink():continue
        relative=p.relative_to(ROOT/SIM)
        if relative.parts[0]=='xsim':continue  # Explicit positive logs already selected.
        source=str(p.relative_to(ROOT))
        full[source]=dict(source=source,bytes=p.stat().st_size,sha256=digest(p))
    archive_manifest=dict(schema_version=1,date='2026-11-05',tag=TAG,firmware='M20-V31-0.2',
                          mode='FUNCTIONAL_STORAGE',files=[full[k] for k in sorted(full)],
                          excluded='compiled caches, xsim databases, WDB/VCD, DCP, virtual environments; original files retained',
                          self_hash_excluded=True)
    archive=assets/'m20-v3.1-verification-evidence.tar.gz'
    with archive.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as tar:
        metadata=json.dumps(archive_manifest,indent=2).encode()+b'\n'
        item=tarfile.TarInfo('ARCHIVE_MANIFEST.json');item.size=len(metadata);item.mtime=0;tar.addfile(item,io.BytesIO(metadata))
        for row in archive_manifest['files']:
            p=ROOT/row['source'];item=tar.gettarinfo(str(p),'evidence/'+row['source'])
            item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
            with p.open('rb') as f:tar.addfile(item,f)
            assert digest(p)==row['sha256'],row['source']
    (out/'archive_manifest.json').write_text(json.dumps(archive_manifest,indent=2)+'\n')
    result=dict(status='PREPARED_NOT_PUBLISHED',tag=TAG,mode='FUNCTIONAL_STORAGE',firmware='M20-V31-0.2',
                small_count=len(rows),small_bytes=manifest['bytes'],release_evidence_count=len(full),
                release_evidence_uncompressed_bytes=sum(r['bytes'] for r in full.values()),
                bitstream=dict(name=BIT_NAME,source=str(bit.relative_to(ROOT)),sha256=BIT_SHA,bytes=bit.stat().st_size),
                evidence_archive=dict(name=archive.name,sha256=digest(archive),bytes=archive.stat().st_size))
    (out/'preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    prepare(p.parse_args().output.resolve())
