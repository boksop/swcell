#!/usr/bin/env python3
"""Local read-only release checks. No commit, cleanup, network or source writes.
Only a new report directory and a private temporary generation directory are written.
"""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def git(root,*args):
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
    p=subprocess.run(['git','-C',str(root),'-c','core.fsmonitor=false','-c','core.untrackedCache=false',*args],env=env,text=True,capture_output=True)
    if p.returncode:raise ValueError('local git check failed: '+' '.join(args)+' '+p.stderr.strip())
    return p.stdout.strip()

def inspect(root,manifest):
    root=Path(root).resolve();manifest=Path(manifest).resolve()
    metadata=dict(commit=git(root,'rev-parse','HEAD'),branch=git(root,'rev-parse','--abbrev-ref','HEAD'),
                  tags_at_head=git(root,'tag','--points-at','HEAD').splitlines(),
                  tag_objects=git(root,'for-each-ref','--format=%(refname:short)|%(objecttype)|%(objectname)|%(*objectname)','refs/tags').splitlines(),
                  remotes=git(root,'remote','-v').splitlines(),
                  tracked_count=len(git(root,'ls-files').splitlines()),
                  worktree_changes=git(root,'status','--porcelain=v1','-uall').splitlines())
    result=dict(status='FAIL',git=metadata,checks={},errors=[],hashes={},limits='Digital/source restoration only; no real 157 timing or FPGA hardware qualification')
    if metadata['remotes']:result['errors'].append('unexpected remote configuration')
    definition=json.loads(manifest.read_text());files=definition['files']
    if manifest.is_relative_to(root) and str(manifest.relative_to(root)) in files:raise ValueError('manifest must not include itself')
    for relative,expected in files.items():
        p=Path(relative)
        if p.is_absolute() or '..' in p.parts or not (root/p).resolve().is_relative_to(root):raise ValueError('unsafe manifest path')
        if not (root/p).is_file():result['errors'].append('missing '+relative);continue
        digest=sha(root/p);result['hashes'][relative]=digest
        if digest!=expected:result['errors'].append('SHA mismatch '+relative)
    result['checks']['manifest_files']=len(files)
    # Imports come from the selected local tree; generated outputs never touch that tree.
    sys.path.insert(0,str(root/'host/python'))
    from m20.v21_build import generate
    from m20.v21_audit import audit
    from m20.v2_build import generate as generate_v2
    from m20.v2_audit import audit_module
    from m20.benchmarks import programs
    from m20.isa import decode,IllegalInstruction
    scratch=Path(tempfile.mkdtemp(prefix='swcell-release-audit-'))
    result['scratch_directory']=str(scratch)
    generate(scratch/'v21');generate_v2(scratch/'v2')
    regenerated={}
    for p in (scratch/'v21').iterdir():
        original=root/'rtl/m20/v21/generated'/p.name
        regenerated[str(original.relative_to(root))]=p.read_bytes()==original.read_bytes()
    for p in (scratch/'v2').rglob('*'):
        if p.is_file():
            original=root/'rtl/m20/v2/generated'/p.relative_to(scratch/'v2')
            regenerated[str(original.relative_to(root))]=p.read_bytes()==original.read_bytes()
    result['checks']['regenerated_files']=regenerated
    if not all(regenerated.values()):result['errors'].append('generated SV/JSON byte mismatch')
    a=audit(root/'rtl/m20/v21/generated/m20v21_cpu_core.sv',root/'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json',root/'rtl/m20/v21/swc_mux157.sv')
    count={k:a[k] for k in ('combinational_mux','ff_bits','full_equivalent','functional_equivalent','debug_only_mux')}
    result['checks']['v21']=count
    if count!=dict(combinational_mux=477,ff_bits=33,full_equivalent=543,functional_equivalent=542,debug_only_mux=1):result['errors'].append('V2.1 resource contract mismatch')
    p=root/'rtl/m20/v2/generated/shared/m20v2_cpu_core.sv';a2=audit_module(p,p.with_suffix('.netlist.json'))
    result['checks']['v2_shared_equivalent']=a2['physical_157_equivalent']
    if a2['physical_157_equivalent']!=603:result['errors'].append('603 reference mismatch')
    legal=0
    for w in range(65536):
        try:decode(w);legal+=1
        except IllegalInstruction:pass
    result['checks']['isa_codes']=dict(legal=legal,illegal=65536-legal)
    if legal!=15015:result['errors'].append('ISA legality mismatch')
    result['checks']['roms']={}
    for name,program in programs().items():
        data=b''.join(w.to_bytes(2,'little') for w in program.words)
        memh=''.join(f'{w:04X}\n' for w in program.words).encode()
        frozen=definition['frozen_roms'][name]
        okay=(hashlib.sha256(data).hexdigest()==frozen['binary_sha256'] and
              data==(root/f'software/m20_300/rom/{name}.bin').read_bytes() and
              memh==(root/f'software/m20_300/rom/{name}.memh').read_bytes() and len(program.words)==frozen['words'])
        result['checks']['roms'][name]=dict(pass_check=okay,words=len(program.words),sha256=hashlib.sha256(data).hexdigest())
        if not okay:result['errors'].append('ROM mismatch '+name)
    result['status']='PASS' if not result['errors'] else 'FAIL'
    result['worktree_clean']=not metadata['worktree_changes']
    result['manifest_sha256']=sha(manifest)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();dest=a.output.resolve()
    if dest==root or (root in dest.parents and root/'build' not in dest.parents):p.error('reports must be outside source tree or in its build/ directory')
    if (dest/'release_audit.json').exists():p.error('choose fresh report directory; previous reports are preserved')
    try:result=inspect(root,a.manifest or root/'docs/m20/M20_SOURCE_MANIFEST.json')
    except Exception as e:result=dict(status='FAIL',errors=[str(e)])
    dest.mkdir(parents=True,exist_ok=True);(dest/'release_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# SwCell 本地版本只读审计','',f'结果：{result["status"]}；不是硬件时序验收。','']
    if 'git' in result:
        m=result['git'];lines += [f'Commit：`{m["commit"]}`',f'分支：{m["branch"]}',f'Tags：{", ".join(m["tags_at_head"]) or "无"}',
            f'跟踪文件：{m["tracked_count"]}；工作区干净：{result["worktree_clean"]}；remote数：{len(m["remotes"])}。','',
            '检查：来源SHA、冻结ISA/ROM、14份生成文件字节比较、独立477/33/543及603计数。','',
            '本工具不执行单元测试或XSIM，测试日志须另外关联；不把旧PASS报告当恢复成功。']
    lines += ['', '错误：'+('; '.join(result['errors']) or '无'),'']
    (dest/'release_audit.md').write_text('\n'.join(lines));print('LOCAL_RELEASE_AUDIT_'+result['status'])
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
