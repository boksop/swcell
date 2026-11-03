"""Independent fail-closed SV/pin/FF/DAG/cone audit; never imports generator."""
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path
from .v2_audit import clean,bit,vector,signal_bits,require,AuditError
ROOT=Path(__file__).resolve().parents[3]
WIDTHS=dict(pc_reg=12,ar_reg=8,a_reg=4,z_reg=1,c_reg=1,gpo_reg=4,state_reg=3)
BUS=('rom_addr','ram_addr','ram_wdata','ram_ce','ram_oe','ram_we')

def audit(sv_path,json_path,primitive_path):
    sv_path=Path(sv_path);json_path=Path(json_path)
    raw=sv_path.read_text();text=clean(raw);net=json.loads(json_path.read_text())
    primitive=clean(Path(primitive_path).read_text())
    primitive=re.sub(r'^`default_nettype\s+\w+\s*$','',primitive,flags=re.M)
    require(re.fullmatch(r'\s*module swc_mux157\(input wire s, input wire i0, input wire i1, output wire y\);\s*assign y = s \? i1 : i0;\s*endmodule\s*',primitive)!=None,'bad primitive')
    require(net['source_sha256']==hashlib.sha256(raw.encode()).hexdigest(),'source SHA mismatch')
    text=re.sub(r'^`default_nettype\s+\w+\s*$','',text,flags=re.M)
    m=re.fullmatch(r'\s*module\s+(\w+)\s*\((.*?)\);(.*?)endmodule\s*',text,re.S)
    require(m is not None and m[1]==net['module']=='m20v21_cpu_core','module mismatch')
    inputs={};outputs={}
    for d in m[2].split(','):
        p=re.fullmatch(r'\s*(input|output) wire\s*(?:\[(\d+):0\]\s*)?(\w+)\s*',d)
        require(p is not None,'bad port');target=inputs if p[1]=='input' else outputs
        require(p[3] not in target,'duplicate port');target[p[3]]=int(p[2])+1 if p[2] else 1
    require(inputs==dict(clk=1,rst=1,keys=6,rom_data=16,ram_rdata=4),'unexpected CPU inputs')
    require(inputs==net['inputs'] and outputs=={k:len(v) for k,v in net['outputs'].items()},'port mismatch')
    require(net['functional_outputs']=={k:net['outputs'][k] for k in BUS},'physical output roots changed')
    body=m[3];actual={}
    pattern=r'swc_mux157\s+(\w+)\s*\(\s*\.s\(([^()]*)\),\s*\.i0\(([^()]*)\),\s*\.i1\(([^()]*)\),\s*\.y\(([^()]*)\)\s*\);'
    blocks=list(re.finditer(r'if\s*\(1\)\s*begin\s*:\s*(\w+)(.*?)\bend\b',body,re.S))
    for b in blocks:
        require(not re.sub(pattern,'',b[2]).strip(),'opaque combinational logic')
        for p in re.finditer(pattern,b[2]):
            k=b[1]+'.'+p[1];require(k not in actual,'duplicate instance')
            actual[k]={pin:bit(p[i]) for pin,i in [('s',2),('i0',3),('i1',4),('y',5)]}
    for b in reversed(blocks):body=body[:b.start()]+body[b.end():]
    body=re.sub(r'\b(?:generate|endgenerate)\b','',body)
    require(len(net['nodes'])==len({n['instance'] for n in net['nodes']}),'duplicate JSON instance')
    require(actual=={n['instance']:{p:n[p] for p in ('s','i0','i1','y')} for n in net['nodes']},'MUX pin mismatch')
    wires=re.findall(r'\bwire\s+(\w+)\s*;',body);body=re.sub(r'\bwire\s+\w+\s*;','',body)
    require(len(wires)==len(set(wires))==len(actual) and set(wires)=={p['y'] for p in actual.values()},'driver/wire mismatch')
    regs={m[2]:int(m[1])+1 if m[1] else 1 for m in re.finditer(r'logic\s*(?:\[(\d+):0\]\s*)?(\w+)\s*;',body)}
    require(regs==WIDTHS=={r['name']:r['width'] for r in net['registers']},'33-state boundary mismatch')
    body=re.sub(r'logic\s*(?:\[\d+:0\]\s*)?\w+\s*;','',body);assigns={};seq={}
    def take_assign(m):
        require(m[1] not in assigns,'multiple port drivers');assigns[m[1]]=vector(m[2]);return ''
    body=re.sub(r'assign\s+(\w+)\s*=\s*([^;]+);',take_assign,body)
    require(assigns==net['outputs'],'output wiring mismatch')
    def take_ff(m):
        p=re.fullmatch(r'\s*(\w+)\s*<=\s*([^;]+);\s*',m[1]);require(p is not None,'hidden FF control')
        require(p[1] not in seq,'multiple FF drivers');seq[p[1]]=vector(p[2]);return ''
    body=re.sub(r'always_ff\s*@\(posedge\s+clk\)\s*begin(.*?)\bend\b',take_ff,body,flags=re.S)
    require(seq=={r['name']:r['dbits'] for r in net['registers']},'FF-D mismatch')
    require(not body.strip(),'uncounted logic')
    table={n['y']:n for n in net['nodes']};require(len(table)==len(actual),'multiple MUX drivers')
    external={s for k,w in (inputs|regs).items() for s in signal_bits(k,w)}
    require(not external.intersection(table),'MUX drives input/state')
    for n in table.values():
        require(n['id']==n['y'] and n['instance']==f'g_{n["group"]}.u_{n["id"]}','node identity mismatch')
        for p in ('s','i0','i1'):require(n[p] in table or n[p] in external or n[p] in ('0','1'),'floating input')
        require('clk' not in [n[p] for p in ('s','i0','i1')],'fabric clock logic')
    depth={s:0 for s in external}|{'0':0,'1':0};pending=set()
    def level(s):
        if s in depth:return depth[s]
        require(s in table and s not in pending,'unknown source or combinational cycle')
        pending.add(s);depth[s]=1+max(level(table[s][p]) for p in ('s','i0','i1'));pending.remove(s);return depth[s]
    for s in table:level(s)
    def cone(roots):
        used=set();todo=list(roots)
        while todo:
            s=todo.pop()
            if s not in table:require(s in external or s in ('0','1'),'unknown root');continue
            if s not in used:used.add(s);todo.extend(table[s][p] for p in ('s','i0','i1'))
        return used
    d_roots=[s for r in net['registers'] for s in r['dbits']]
    functional=cone(d_roots+[s for v in net['functional_outputs'].values() for s in v])
    all_used=cone(d_roots+[s for v in net['outputs'].values() for s in v]);require(all_used==set(table),'dead logic')
    debug=set(table)-functional
    require(debug<=cone(net['outputs']['trap_event']),'unexpected debug-only gate')
    resets=dict(pc_reg=0,ar_reg=0,a_reg=0,z_reg=1,c_reg=0,gpo_reg=8,state_reg=0)
    for r in net['registers']:
        require(r['reset_value']==resets[r['name']],'reset value changed')
        require(r['qbits']==signal_bits(r['name'],r['width']),'Q mapping mismatch')
        for i,d in enumerate(r['dbits']):
            require(table[d]['s']=='rst' and table[d]['i1']==str((r['reset_value']>>i)&1),'missing reset select')
    groups=dict(sorted(Counter(n['group'] for n in table.values()).items()))
    require(groups==net['group_counts'] and len(table)==net['physical_mux_count'] and net['ff_bits']==33,'generator total mismatch')
    loads=Counter(n[p] for n in table.values() for p in ('s','i0','i1') if n[p] not in ('0','1'))
    return dict(status='VERIFIED',combinational_mux=len(table),functional_mux=len(functional),debug_only_mux=len(debug),
        debug_nodes=sorted(debug),ff_bits=33,dff_equivalent=66,full_equivalent=len(table)+66,functional_equivalent=len(functional)+66,
        reset_mux=33,groups=groups,max_mux_depth=max(depth.values()),max_internal_pin_load=max(loads.values()),
        highest_load_nodes=[s for s,n in loads.items() if n==max(loads.values())],
        max_mux_output_load=max(loads[s] for s in table),load_histogram=dict(sorted(Counter(loads.values()).items())),
        sv_sha256=net['source_sha256'],json_sha256=hashlib.sha256(json_path.read_bytes()).hexdigest(),
        primitive_sha256=hashlib.sha256(Path(primitive_path).read_bytes()).hexdigest(),nodes=list(table.values()),
        fanout=[dict(signal=s,pin_load=loads[s],depth=depth[s],group=table[s]['group'] if s in table else 'primary_or_ff') for s in sorted(loads)])

def run(directory,output):
    directory=Path(directory);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    result=audit(directory/'m20v21_cpu_core.sv',directory/'m20v21_cpu_core.netlist.json',directory.parent/'swc_mux157.sv')
    result['audit_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for name,rows in [('nodes',result.pop('nodes')),('fanout',result.pop('fanout'))]:
        with (output/f'{name}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    text=['# M20 V2.1 独立资源审计','', '状态 VERIFIED；从SV逐pin/无条件FF-D解析，与生成器JSON交叉核对。','',
          '|口径|组合MUX|存储折算|总数|','|---|---:|---:|---:|',
          f'|完整验证接口|{result["combinational_mux"]}|66|{result["full_equivalent"]}|',
          f'|纯功能核心|{result["functional_mux"]}|66|{result["functional_equivalent"]}|','',
          f'33功能状态，33个显式reset选择已包含组合；debug-only {result["debug_only_mux"]}颗用于trap_event。',
          f'最大拓扑{result["max_mux_depth"]}，最大输入pin负载{result["max_internal_pin_load"]}；不是实物时序证明。','',
          '|组|组合MUX|','|---|---:|']+[f'|{k}|{v}|' for k,v in result['groups'].items()]
    text += ['', '检查：实例/端口/每pin、33状态/FF-D/reset、已驱动源/多驱动/环路、功能与debug锥/死网；所有数值可重生成。',
             '详见v21_resources/audit.json、nodes.csv、fanout.csv；nativeFF仍须真实双MUX DFF另验证。','']
    (output/'audit.md').write_text('\n'.join(text));print(f'M20V21_AUDIT_PASS full={result["full_equivalent"]} functional={result["functional_equivalent"]}');return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'rtl/m20/v21/generated');p.add_argument('--output',type=Path,default=ROOT/'build/m20_300/v21/audit');a=p.parse_args();run(a.input,a.output)
if __name__=='__main__':main()
