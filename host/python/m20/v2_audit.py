"""Independent, fail-closed audit of emitted MUX SV, connectivity and state.

Does not import the generator, its Circuit.stats(), Vivado LUT reports or ALU.
Only swc_mux157, wires/constants and unconditional native-FF assignments are
accepted. A JSON count alone is never evidence that the SV contains that graph.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
REG_GROUP=dict(a_reg='writeback_a',z_reg='flags',c_reg='flags',pc_reg='pc',
               ar_reg='ar',gpo_reg='gpo',state_reg='control')
STATE_WIDTHS=dict(a_reg=4,z_reg=1,c_reg=1,pc_reg=12,ar_reg=8,gpo_reg=4,state_reg=3)


class AuditError(ValueError):pass


def require(condition,message):
    if not condition:raise AuditError(message)


def clean(text):return re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)


def bit(value):
    value=str(value).strip()
    if value in ("1'b0",'0'):return '0'
    if value in ("1'b1",'1'):return '1'
    require(re.fullmatch(r'[A-Za-z_]\w*(?:\[\d+\])?',value) is not None,f'unsupported signal {value!r}')
    return value


def vector(expression):
    expression=expression.strip()
    if expression.startswith('{'):
        require(expression.endswith('}'),'invalid concatenation')
        return [bit(v) for v in reversed(expression[1:-1].split(','))]
    return [bit(expression)]


def signal_bits(name,width):return [name] if width==1 else [f'{name}[{i}]' for i in range(width)]


def audit_primitive(path):
    source=clean(Path(path).read_text())
    source=re.sub(r'^`default_nettype\s+(?:none|wire)\s*$','',source,flags=re.M)
    expected=r'\s*module\s+swc_mux157\s*\(\s*input\s+wire\s+S\s*,\s*input\s+wire\s+I0\s*,\s*input\s+wire\s+I1\s*,\s*output\s+wire\s+Y\s*\);\s*assign\s+Y\s*=\s*S\s*\?\s*I1\s*:\s*I0\s*;\s*endmodule\s*'
    require(re.fullmatch(expected,source) is not None,'unique primitive is not exactly Y = S ? I1 : I0')
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_module(sv_path,json_path):
    text=sv_path.read_text();source=clean(text)
    net=json.loads(json_path.read_text())
    require(hashlib.sha256(text.encode()).hexdigest()==net['source_sha256'],f'{sv_path}: source hash mismatch')
    source=re.sub(r'^`default_nettype\s+(?:none|wire)\s*$','',source,flags=re.M)
    header=re.fullmatch(r'\s*module\s+(\w+)\s*\((.*?)\);(.*?)endmodule\s*',source,re.S)
    require(header is not None,f'{sv_path}: expected exactly one structural module')
    require(header[1]==net['module'],'SV/JSON module name mismatch')
    inputs={};outputs={}
    for declaration in header[2].split(','):
        p=re.fullmatch(r'\s*(input|output)\s+wire\s*(?:\[(\d+):0\]\s*)?(\w+)\s*',declaration)
        require(p is not None,f'unsupported port {declaration!r}')
        (inputs if p[1]=='input' else outputs)[p[3]]=int(p[2])+1 if p[2] else 1
    require(inputs==net['inputs'] and outputs=={k:len(v) for k,v in net['outputs'].items()},'SV/JSON port mismatch')
    body=header[3];actual_nodes={}
    blocks=list(re.finditer(r'if\s*\(1\)\s*begin\s*:\s*(\w+)(.*?)\bend\b',body,re.S))
    instance_pattern=r'swc_mux157\s+(\w+)\s*\(\s*\.S\(([^()]*)\),\s*\.I0\(([^()]*)\),\s*\.I1\(([^()]*)\),\s*\.Y\(([^()]*)\)\s*\);'
    for block in blocks:
        matches=list(re.finditer(instance_pattern,block[2]))
        leftover=re.sub(instance_pattern,'',block[2])
        require(not leftover.strip(),f'{block[1]}: uncounted construct inside MUX block')
        for m in matches:
            path=f'{block[1]}.{m[1]}'
            require(path not in actual_nodes,f'duplicate instance {path}')
            actual_nodes[path]=dict(s=bit(m[2]),i0=bit(m[3]),i1=bit(m[4]),y=bit(m[5]))
    for block in reversed(blocks):body=body[:block.start()]+body[block.end():]
    body=re.sub(r'\b(?:generate|endgenerate)\b','',body)
    expected_nodes={n['instance']:{p:bit(n[p]) for p in ('s','i0','i1','y')} for n in net['nodes']}
    require(len(expected_nodes)==len(net['nodes']),'duplicate manifest instance')
    require(actual_nodes==expected_nodes,'SV/JSON MUX instance or pin mismatch')
    require(len(actual_nodes)==net['physical_mux_count'],'declared MUX total disagrees with parsed SV')
    wires=re.findall(r'\bwire\s+(\w+)\s*;',body)
    body=re.sub(r'\bwire\s+\w+\s*;','',body)
    require(len(wires)==len(set(wires))==len(actual_nodes),'missing/duplicate output nets')
    require(set(wires)=={n['y'] for n in actual_nodes.values()},'MUX Y nets disagree with wire declarations')
    registers={m[2]:int(m[1])+1 if m[1] else 1
               for m in re.finditer(r'logic\s*(?:\[(\d+):0\]\s*)?(\w+)\s*;',body)}
    body=re.sub(r'logic\s*(?:\[\d+:0\]\s*)?\w+\s*;','',body)
    declared={r['name']:r['width'] for r in net['registers']}
    require(registers==declared,'native FF declarations disagree with manifest')
    observed_assigns={}
    def take_assign(match):
        name=match[1];require(name not in observed_assigns,'multiple output drivers')
        observed_assigns[name]=vector(match[2]);return ''
    body=re.sub(r'assign\s+(\w+)\s*=\s*([^;]+);',take_assign,body)
    require(observed_assigns==net['outputs'],'SV/JSON output wiring mismatch')
    sequential={}
    def take_ff(match):
        statement=re.fullmatch(r'\s*(\w+)\s*<=\s*([^;]+);\s*',match[1])
        require(statement is not None,'native FF has hidden enable/reset/behavior')
        require(statement[1] not in sequential,'multiple FF writers')
        sequential[statement[1]]=vector(statement[2]);return ''
    body=re.sub(r'always_ff\s*@\(posedge\s+clk\)\s*begin(.*?)\bend\b',take_ff,body,flags=re.S)
    require(sequential=={r['name']:r['dbits'] for r in net['registers']},'FF D pins disagree with manifest')
    require(not body.strip(),f'unsupported/unaccounted structural logic: {body.strip()[:160]}')
    table={n['y']:n for n in net['nodes']}
    require(len(table)==len(net['nodes']),'multiple MUX drivers')
    external={b for name,width in inputs.items() for b in signal_bits(name,width)}
    external|={b for name,width in registers.items() for b in signal_bits(name,width)}
    for n in net['nodes']:
        require(n['id']==n['y'],'unexpected net ID')
        require(n['instance'].split('.')[0]=='g_'+re.sub(r'[^A-Za-z_0-9]','_',n['group']),'wrong group ownership')
        for p in ('s','i0','i1'):
            require(n[p] in table or n[p] in external or n[p] in ('0','1'),f'unknown source {n[p]}')
            require(n[p]!='clk','combinational clock gate is unsupported')
    depth={'0':0,'1':0}|{b:0 for b in external};visiting=set()
    def level(signal):
        if signal in depth:return depth[signal]
        require(signal in table,f'unknown sink source {signal}')
        require(signal not in visiting,'combinational cycle')
        visiting.add(signal);n=table[signal]
        depth[signal]=1+max(level(n[p]) for p in ('s','i0','i1'))
        visiting.remove(signal);return depth[signal]
    for signal in table:level(signal)
    roots=[s for r in net['registers'] for s in r['dbits']]
    roots += [s for value in net['functional_outputs'].values() for s in value]
    used=set();todo=list(roots)
    while todo:
        s=todo.pop()
        if s not in table or s in used:continue
        used.add(s);todo.extend(table[s][p] for p in ('s','i0','i1'))
    require(used==set(table),'dead or debug-only gate counted as core hardware')
    for value in net['outputs'].values():
        for s in value:require(s in external or s in used or s in ('0','1'),'observer adds unsupported logic')
    ff_bits=sum(registers.values());require(ff_bits==net['ff_bits'],'state bit count mismatch')
    if net['module']=='m20v2_cpu_core':
        require(registers==STATE_WIDTHS and ff_bits==33,'CPU changed the 33-bit state boundary')
        for r in net['registers']:
            require(r['qbits']==signal_bits(r['name'],r['width']),'wrong FF Q mapping')
            require(r['storage']=='unconditional_native_ff','unsupported storage type')
            for index,d in enumerate(r['dbits']):
                n=table[d]
                require(n['category']=='reset' and n['s']=='rst' and
                        n['i1']==str((r['reset_value']>>index)&1),'missing explicit reset select')
                if r['name']!='state_reg':
                    hold=table[n['i0']]
                    require(hold['category']=='hold_enable' and hold['i0']==r['qbits'][index],
                            'missing explicit CE/hold MUX')
    counts=Counter(n['group'] for n in net['nodes']);categories=Counter(n['category'] for n in net['nodes'])
    require(dict(counts)==net['group_counts'] and dict(categories)==net['category_counts'],'group/category total mismatch')
    reused=Counter();cross=set()
    for request in net['shared_requests']:
        require(request['id'] in table,'shared request refers to nonexistent physical MUX')
        owner=table[request['id']]
        require(all(bit(request[p])==owner[p] for p in ('s','i0','i1')),'shared request has unequal pins')
        reused[request['id']]+=1
        if request['group']!=owner['group']:cross.add(request['id'])
    loads=Counter()
    for n in net['nodes']:
        loads.update(n[p] for p in ('s','i0','i1'))
    for r in net['registers']:loads.update(r['dbits'])
    # Functional port loads only: exclude test/debug sinks from electrical proxy.
    for values in net['functional_outputs'].values():loads.update(values)
    for constant in ('0','1'):loads.pop(constant,None)
    deepest=max(roots,key=level) if roots else '0'
    witness=[];s=deepest
    while s in table:
        witness.append(s);s=max((table[s][p] for p in ('s','i0','i1')),key=level)
    groups=[]
    for group,total in counts.items():
        nodes=[n for n in net['nodes'] if n['group']==group]
        state=sum(w for name,w in registers.items() if REG_GROUP.get(name)==group)
        hold=sum(n['category']=='hold_enable' for n in nodes);reset=sum(n['category']=='reset' for n in nodes)
        groups.append(dict(variant=net['variant'],group=group,combinational_mux=total,
            ce_hold_mux=hold,reset_mux=reset,other_combinational_mux=total-hold-reset,
            state_bits=state,dff_mux_equivalent=2*state,physical_157_equivalent=total+2*state,
            cse_reused_mux_owned=sum(n['y'] in reused for n in nodes),
            cross_group_shared_mux_owned=sum(n['y'] in cross for n in nodes),
            node_max_depth=max(level(n['y']) for n in nodes)))
    return dict(module=net['module'],variant=net['variant'],combinational_mux=len(actual_nodes),
        state_bits=ff_bits,dff_mux_equivalent=2*ff_bits,physical_157_equivalent=len(actual_nodes)+2*ff_bits,
        categories=dict(categories),groups=groups,max_mux_depth=level(deepest),deepest_endpoint=deepest,
        longest_path_root_to_sink=list(reversed(witness)),path_origin=s,
        max_internal_pin_fanout=max(loads.values(),default=0),
        max_fanout_signals=[s for s,n in loads.items() if n==max(loads.values(),default=0)],
        cse_reused_mux=len(reused),cross_group_shared_mux=len(cross),shared_requests=len(net['shared_requests']),
        source_sha256=net['source_sha256'],netlist_sha256=hashlib.sha256(json_path.read_bytes()).hexdigest(),nodes=net['nodes'])


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def report(result):
    base=result['variants']['baseline'];shared=result['variants']['shared']
    text=['# M20-300 V2：精确MUX资源审计','',
      '> 此文件由 `python -m m20.v2_audit` 从实际结构SV/JSON重新生成；不是Vivado LUT估算。日期：2026-10-29。','',
      '## 1. 结论与口径','',
      f'朴素结构版为 **{base["combinational_mux"]} 组合MUX + 66 DFF等价 = {base["physical_157_equivalent"]}颗**；全局共享版为 **{shared["combinational_mux"]} + 66 = {shared["physical_157_equivalent"]}颗**。这是本次具体网表、普通DFF按2颗157/bit的核心逻辑等价数，包含显式CE/保持和复位选择，不是已完成物理PCB的全部BOM。','',
      f'共享优化减少{base["combinational_mux"]-shared["combinational_mux"]}颗组合MUX，未增加状态（仍33位）或改变2/5微周期。当前共享版相对328超出{shared["physical_157_equivalent"]-328}颗，相对300超出{shared["physical_157_equivalent"]-300}颗。','',
      '唯一原语为swc_mux157，每个显式实例一颗；接线/常量tie不计，NOT必须MUX。表中CE和reset是组合列的子集，DFF等价另加；共享MUX已计在唯一归属组，不重复相加。standalone ALU/decoder是单元测试副本，不再加进CPU top。','',
      '## 2. 两版逐组统计','',
      '|版/语义组|组合MUX|CE保持子集|复位子集|其它组合|状态bit|DFF等价|物理157等价|有CSE复用的归属MUX|',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for variant in ('baseline','shared'):
        for r in result['variants'][variant]['groups']:
            text.append('|'+f"{variant}/{r['group']}|"+'|'.join(str(r[k]) for k in ('combinational_mux','ce_hold_mux','reset_mux','other_combinational_mux','state_bits','dff_mux_equivalent','physical_157_equivalent','cse_reused_mux_owned'))+'|')
        r=result['variants'][variant]
        text.append(f"|**{variant}合计**|**{r['combinational_mux']}**|**{r['categories'].get('hold_enable',0)}**|**{r['categories'].get('reset',0)}**|**{r['combinational_mux']-r['categories'].get('hold_enable',0)-r['categories'].get('reset',0)}**|**{r['state_bits']}**|**{r['dff_mux_equivalent']}**|**{r['physical_157_equivalent']}**|**{r['cse_reused_mux']}**|")
    text+=['','## 3. 与原328预算按一致口径比较','',
      '为避免复位双算，本表先从各组移除reset子集，再集中到复位行；控制器与译码合并比较原70，并加原uSTATE存储6。原预算没有真实网表，归属只能按这一公开映射比较，不能声称找到了原估算中的逐门差异。','',
      '|对应模块|原预算|共享版精确数|差额|','|---|---:|---:|---:|']
    by={r['group']:r for r in shared['groups']}
    net=lambda g:sum(r['physical_157_equivalent']-r['reset_mux']
                     for name,r in by.items() if name==g or name.startswith(g+'.'))
    comparisons=[('PC12',82,net('pc')),('AR8',62,net('ar')),('A4写回',20,net('writeback_a')),
      ('Z/C',6,net('flags')),('GPO4',12,net('gpo')),('控制/译码+uSTATE存储',76,net('control')+net('decoder')),
      ('ALU',40,net('alu')),('RAM地址/控制',8,net('bus')),('输入选择',10,net('input_select')),
      ('集中复位选择',12,shared['categories']['reset'])]
    require(sum(r[1] for r in comparisons)==328 and sum(r[2] for r in comparisons)==shared['physical_157_equivalent'],'comparison ledger does not reconcile')
    for label,old,new in comparisons:text.append(f'|{label}|{old}|{new}|{new-old:+d}|')
    text+=['', '## 4. 优化与拓扑代价','',
      '|指标|baseline|shared|','|---|---:|---:|',
      f'|组合MUX拓扑最大层数|{base["max_mux_depth"]}|{shared["max_mux_depth"]}|',
      f'|核心状态bit|{base["state_bits"]}|{shared["state_bits"]}|',
      f'|内部信号最大输入pin负载数（不含常量/调试）|{base["max_internal_pin_fanout"]}|{shared["max_internal_pin_fanout"]}|',
      f'|有跨语义组CSE复用的唯一MUX|{base["cross_group_shared_mux"]}|{shared["cross_group_shared_mux"]}|','',
      'O1只合并完全相同(S,I0,I1)节点，包含重复NOT；两版采用同一逻辑构造/常量简化。拓扑层数不是ns，也未证明所有路径都可被敏化；扇出是内部pin负载代理，不能替代PCB驱动/缓冲/物理时序分析。最大路径节点清单在audit.json中。','',
      '## 5. 300颗目标与外围边界','',
      f'当前共享版必须再减少{shared["physical_157_equivalent"]-300}颗才达到300；这不是已证明不可达的理论下界，也没有证据可保证仅靠继续CSE达到。当前固定存储66、显式保持30和复位33合计129，余下171的目标额度需容纳其它组合；现有其它组合{shared["combinational_mux"]-63}。应另评审局部译码/控制因式分解和数据路径选择，再做每项等价验证。','',
      'PC/AR共用增量器、改微状态/复位策略可能引入选择MUX、扇出或周期代价；本轮没有实施，不能填入假节省。保持冻结ISA和本轮2/5验收配置，不为压数字隐藏状态/运算器。','',
      '六键两级同步12bit按storage至少24颗、复位同步2bit至少4颗另列；其CE/复位/输入整形及真实时钟缓冲仍需各自电路审计。RAM/ROM容量为0颗157但物理器件另列；SRAM方向/三态驱动、PCB负载、供电去耦不包含于核心逻辑数。','',
      '当前仅组合网络已逐MUX构造。nativeFF可继续用于FPGA原型；2-MUX/DFF是用户指定折算，尚未实现/验证真实反馈DFF时序。没有三态157原语或免费反相；电气辅助不能由本表凭空省掉。','',
      '## 6. 独立审计与复现','',
      '审计器不导入生成器/其stats：逐个解析SV的MUX实例和S/I0/I1/Y，核对JSON、端口/输出接线、无条件FF-D、33位边界、显式hold/reset和功能根可达性；拒绝其它单元/行为组合/组合环。共享请求也核对同一live节点/相同pins。','',
      '```bash',
      'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=host/python \\',
      'build/venvs/python312/bin/python -B -m m20.v2_audit \\',
      '  --output docs/m20/v2_resources \\',
      '  --markdown docs/m20/M20_300_V2_MUX_BUDGET.md','```','',
      '逐组module_budget.csv、逐实例gate_instances.csv及audit.json同时生成；SHA关联实际SV和连接清单。独立单元副本统计在audit.json的standalone_units，不与top相加。功能三方验证和已知边界另见M20_300_V2_VERIFICATION.md及M20_300_V2_TEST_REPORT.md。','']
    return '\n'.join(text)


def run(input_directory,output,markdown=None):
    input_directory=Path(input_directory);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    primitive_sha=audit_primitive(input_directory.parent/'swc_mux157.sv')
    variants={};units={};rows=[];gates=[]
    for variant in ('baseline','shared'):
        directory=input_directory/variant;units[variant]={}
        for module in ('m20v2_alu','m20v2_decoder','m20v2_cpu_core'):
            audited=audit_module(directory/f'{module}.sv',directory/f'{module}.netlist.json')
            if module=='m20v2_cpu_core':
                rows.extend(audited['groups'])
                gates.extend(dict(variant=variant,instance=n['instance'],group=n['group'],category=n['category'],
                    selector=n['s'],i0=n['i0'],i1=n['i1'],output=n['y']) for n in audited['nodes'])
                variants[variant]={k:v for k,v in audited.items() if k!='nodes'}
            else:units[variant][module]={k:v for k,v in audited.items() if k not in ('nodes','groups')}
    result=dict(status='PASS',counting_unit='one explicit swc_mux157 instance = one single-channel 157',primitive_sha256=primitive_sha,
                audit_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                generator_sources={name:hashlib.sha256((ROOT/'host/python/m20'/name).read_bytes()).hexdigest()
                                   for name in ('v2_build.py','v2_muxlib.py','v2_alu.py')},
                variants=variants,standalone_units=units,method='Independent SV and JSON connectivity/FF/cone audit; no LUT conversion')
    write_csv(output/'module_budget.csv',rows);write_csv(output/'gate_instances.csv',gates)
    (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    destination=Path(markdown) if markdown else output/'mux_budget.md'
    destination.write_text(report(result))
    print(json.dumps({name:{k:v[k] for k in ('combinational_mux','state_bits','dff_mux_equivalent','physical_157_equivalent','max_mux_depth','max_internal_pin_fanout')} for name,v in variants.items()},indent=2))
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'rtl/m20/v2/generated')
    parser.add_argument('--output',type=Path,default=ROOT/'build/m20_300/v2/audit')
    parser.add_argument('--markdown',type=Path)
    args=parser.parse_args(argv)
    try:run(args.input,args.output,args.markdown);return 0
    except (OSError,ValueError,KeyError,TypeError) as error:parser.exit(1,f'M20V2_AUDIT_FAIL: {error}\n')


if __name__=='__main__':raise SystemExit(main())
