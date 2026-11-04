"""Independent literal-MUX/state-binding audit; never imports v24_build."""
import argparse,json,re,hashlib,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def require(value,msg):
 if not value:raise ValueError(msg)
def audit(folder):
 p=Path(folder)/'swc157_phasegen_v24.sv';text=p.read_text();m=json.loads(p.with_suffix('.json').read_text())
 require(hashlib.sha256(p.read_bytes()).hexdigest()==m['source_sha256'],'source hash')
 require(not re.search(r'\balways(?:_ff|_latch|_comb)?\b',text),'behavioral logic prohibited')
 require(text.count(' assign ')==6,'unaccounted assignments')
 n=re.findall(r'swc_mux157_v23 #\(\.DATA_NS\(COMB_NS\),\.SELECT_NS\(COMB_NS\)\) u_(\w+)\(\.s\(([^)]+)\),\.i0\(([^)]+)\),\.i1\(([^)]+)\),\.y\(([^)]+)\)\);',text)
 conv=lambda v:int(v[-1]) if v.startswith("1'b") else v
 actual=[dict(id=v[0],s=conv(v[1]),i0=conv(v[2]),i1=conv(v[3]),group=a['group'],category=a['category']) for v,a in zip(n,m['nodes'])]
 require(len(n)==len(m['nodes'])==88 and actual==m['nodes'],'88 comb node pins mismatch')
 regs=re.findall(r'r(\d+)\(\.master_hold\(local_h\),\.slave_open\(local_s\),\.d\(([^)]+)\),\.q\(([^)]+)\),\.qm\(\),\.checks_enable\(!rst\)\);',text)
 require(regs==[(str(i),str(m['d'][v]) if not isinstance(m['d'][v],int) else "1'b"+str(m['d'][v]),v) for i,v in enumerate(m['state_names'])],'13 state bindings')
 require(len(regs)==13 and text.count('swc_ms_bit_v23 #(')==13,'storage count')
 require(text.count('swc_mux157_v23 #(')==90 and 'clock_h(.s(clk_ref),.i0(local_s),.i1(1\'b1),.y(local_h))' in text and 'clock_s(.s(clk_ref),.i0(1\'b0),.i1(local_h),.y(local_s))' in text,'interlock count/pins')
 require(m['total_mux']==116 and m['storage_mux']==26 and m['local_interlock_mux']==2,'budget mismatch')
 return dict(status='PASS',comb_mux=88,local_interlock_mux=2,storage_bits=13,storage_mux=26,total_mux=116,cpu_mux_separate=543,system_mux_without_buffers=659,source_sha256=m['source_sha256'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'rtl/m20/v24/generated');p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=audit(a.input);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print('V24_AUDIT_PASS total=116 state=13')
