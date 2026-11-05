#!/usr/bin/env python3
"""Read-only source/evidence binding verification; works without ignored build data."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(root,name):
    relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe path '+name)
    p=root/relative
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root):raise ValueError('missing/unsafe '+name)
    return p


def inspect(root,manifest_path,assets=None):
    manifest=json.loads(manifest_path.read_text())
    for name,digest in manifest['files'].items():
        assert sha(local_file(root,name))==digest,'SHA mismatch '+name
    # Build inputs are the actual source_sha256.txt from the hardware image.
    for name,digest in manifest['build_sources'].items():
        assert sha(local_file(root,name))==digest,'build SHA mismatch '+name
    frozen=json.loads(local_file(root,'docs/m20/v31_resources/baseline_sha256.json').read_text())
    for name,digest in frozen.items():assert sha(local_file(root,name))==digest,'frozen V3 changed '+name
    sys.dont_write_bytecode=True;sys.path.insert(0,str(root/'host/python'))
    spec=importlib.util.spec_from_file_location('v31_release_firmware',root/'tools/m20/v31/build_firmware.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source,image,meta=module.firmware()
    for name,expected in (('m20_v31.asm',source),('m20_v31.memh',image.memh),('manifest.json',json.dumps(meta,indent=2)+'\n')):
        assert (root/'software/m20_300/v31'/name).read_bytes()==expected.encode(),'regeneration '+name
    assert meta['version']=='M20-V31-0.2' and len(image.words)==4052
    binding=manifest['artifact_binding']
    assert sha(root/'software/m20_300/v31/m20_v31.memh')==binding['rom_sha256']
    assert sha(root/'fpga/projects/m20/autonomous/scripts/build.tcl')==binding['build_tcl_sha256']
    from m20.v21_audit import audit
    counts=audit(root/'rtl/m20/v21/generated/m20v21_cpu_core.sv',root/'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json',root/'rtl/m20/v21/swc_mux157.sv')
    assert (counts['combinational_mux'],counts['ff_bits'],counts['full_equivalent'])==(477,33,543)
    archive=root/manifest['evidence_directory'];evidence=json.loads((archive/'manifest.json').read_text())
    for row in evidence['files']:
        p=local_file(archive,row['copy']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['copy']
    route=json.loads((archive/'fpga/route_audit/counts.json').read_text())
    assert (route['mux_lut3'],route['cpu_native_ff'],route['oled_cpu_gpo_direct_drivers'])==(477,33,4)
    status=json.loads((root/'docs/m20/v31_resources/acceptance_summary.json').read_text())
    assert status['status']=='COMPLETED' and status['firmware']=='M20-V31-0.2'
    acceptance=json.loads((root/status['human_confirmation']).read_text())
    assert acceptance['status']=='USER_CONFIRMED_PASS' and acceptance['bitstream_sha256']==binding['bitstream_sha256']
    artifact_status='NOT_REQUESTED'
    if assets is not None:
        for key in ('bitstream','evidence_archive'):
            row=manifest['release_assets'][key];p=local_file(assets,row['name'])
            assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['name']
        artifact_status='PASS'
    commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    return dict(status='PASS',commit=commit,source_files=len(manifest['files']),build_sources=len(manifest['build_sources']),
                regenerated_files=3,rom_words=4052,free_rom_words=44,combination_mux=477,cpu_native_ff=33,
                physical_cpu_equivalent=543,archived_evidence_files=len(evidence['files']),release_assets=artifact_status,
                git_status=subprocess.check_output(['git','-C',str(root),'status','--porcelain=v1','-uall'],text=True).splitlines(),
                scope='Sources, deterministic firmware, independent CPU audit, archived historical evidence and manual acceptance; not a new hardware or XSIM test')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--manifest',type=Path);p.add_argument('--assets',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve()
    if a.output.exists():p.error('Use a fresh output file')
    try:result=inspect(root,a.manifest or root/'docs/m20/v31_release_resources/source_manifest.json',a.assets.resolve() if a.assets else None)
    except (AssertionError,ValueError,KeyError,OSError) as exc:result=dict(status='FAIL',error=str(exc))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result|{'git_status':'omitted; see JSON'} if 'git_status' in result else result))
    raise SystemExit(0 if result['status']=='PASS' else 1)
