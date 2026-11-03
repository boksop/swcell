"""Generate explicit one-bit MUX networks for the frozen M20 CPU.

The Python construction graph is the source of the structural RTL. Every
retained combination node is one swc_mux157 instance; register D paths include
the holding and synchronous-reset MUXes. No behavioral arithmetic is emitted.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .v2_muxlib import Circuit, bits_const
from .v2_alu import build_alu

ROOT = Path(__file__).resolve().parents[3]
OP = dict(LOAD=0, ADD=1, ADC=2, SUB=3, SBC=4, CMP=5, AND=6, XOR=7,
          OR=8, NOT=9, SHL=10, SHR=11, ST=12, ARL=13, ARH=14,
          MOVARL=15, MOVARH=16, MOVA_ARL=17, MOVA_ARH=18, INCAR=19,
          JMP=20, JZ=21, JC=22, IN0=23, IN1=24, OUT=25, NOP=26,
          HALT=27, INVALID=63)


def bits(name, width):
    return [name if width == 1 else f'{name}[{i}]' for i in range(width)]


def muxv(c, select, low, high, *, group, category='comb'):
    assert len(low) == len(high)
    return [c.mux(select, a, b, group=group, category=category)
            for a,b in zip(low,high)]


def build_decoder(c, instruction, *, encoded=True):
    """Strict shared predecode. Returned one-hots feed the core directly.

    Core control does not encode a six-bit internal operation and immediately
    decode it again. The standalone decoder still exposes V1-compatible op6.
    Both variants use this identical construction; only DAG hash-consing differs.
    """
    group='decoder'
    eq=lambda xs,v:c.eq_const(xs,v,group=group)
    both=lambda a,b:c.and_(a,b,group=group)
    either=lambda a,b:c.or_(a,b,group=group)
    anyof=lambda xs:c.reduce_or(xs,group=group)
    major=[eq(instruction[12:16],n) for n in range(16)]
    sub=[eq(instruction[8:12],n) for n in range(10)]
    low_zero=eq(instruction[:8],0)
    middle_zero=eq(instruction[4:8],0)
    imm_reserved_zero=eq(instruction[4:12],0)
    hits={value:0 for name,value in OP.items() if name!='INVALID'}
    immediate=(OP['LOAD'],OP['ADD'],OP['ADC'],OP['SUB'],OP['SBC'],OP['AND'],OP['XOR'])
    for n,operation in enumerate(immediate):
        hits[operation]=both(major[n],imm_reserved_zero)
    aux_base=both(major[7],low_zero)
    for n,name in enumerate(('SHL','SHR','NOT')):
        hits[OP[name]]=both(aux_base,sub[n])
    family=either(major[8],major[9])
    allowed_address=either(major[8],low_zero)
    memory=both(both(family,allowed_address),anyof(sub))
    memory_ops=('LOAD','ST','ADD','ADC','SUB','SBC','CMP','AND','XOR','OR')
    mem_hits={}
    for n,name in enumerate(memory_ops):
        h=both(memory,sub[n]);mem_hits[name]=h
        hits[OP[name]]=either(hits[OP[name]],h)
    ar_base=both(major[10],middle_zero)
    for n,name in enumerate(('ARL','ARH','MOVARL','MOVARH','MOVA_ARL','MOVA_ARH','INCAR')):
        h=both(ar_base,sub[n])
        if n>=2:h=both(h,low_zero)
        hits[OP[name]]=h
    for n,name in enumerate(('JMP','JZ','JC'),11):hits[OP[name]]=major[n]
    for n,name in enumerate(('IN0','IN1','OUT')):
        hits[OP[name]]=both(both(major[14],low_zero),sub[n])
    for n,name in enumerate(('NOP','HALT')):
        hits[OP[name]]=both(both(major[15],low_zero),sub[n])
    legal=anyof(list(hits.values()))
    result=dict(legal=legal,is_memory=memory,memory_write=mem_hits['ST'],
                indirect=both(memory,major[9]),hits=hits)
    if encoded:
        illegal=c.inv(legal,group=group)
        result['op']=[either(illegal,anyof([h for value,h in hits.items() if (value>>bit)&1]))
                      for bit in range(6)]
    return result


def register(c, name, width, candidate, enable, reset, reset_value, group):
    """One CE/hold and one reset decision per bit, implemented with real MUXes."""
    q=bits(name,width)
    held=muxv(c,enable,q,candidate,group=group,category='hold_enable')
    d=muxv(c,reset,held,bits_const(reset_value,width),group=group,category='reset')
    return dict(name=name,width=width,qbits=q,dbits=d,reset_value=reset_value,
                storage='unconditional_native_ff',physical_storage_mux_per_bit=2)


def build_core(c):
    instruction=bits('rom_data',16);keys=bits('keys',6);rdata=bits('ram_rdata',4)
    pc=bits('pc_reg',12);ar=bits('ar_reg',8);a=bits('a_reg',4)
    z='z_reg';carry='c_reg';gpo=bits('gpo_reg',4);state=bits('state_reg',3)
    dec=build_decoder(c,instruction,encoded=False);hit=dec['hits']
    legal=dec['legal'];memory=dec['is_memory'];write=dec['memory_write']
    st=[c.eq_const(state,n,group='control') for n in range(8)]
    nrst=c.inv('rst',group='control')
    not_memory=c.inv(memory,group='control')
    normal=c.and_(c.and_(st[2],not_memory,group='control'),legal,group='control')
    mem_commit=c.and_(c.and_(st[5],memory,group='control'),legal,group='control')
    commit=c.and_(nrst,c.or_(normal,mem_commit,group='control'),group='control')
    operand=muxv(c,memory,instruction[:4],rdata,group='input_select')
    for name,choice in [('MOVA_ARL',ar[:4]),('MOVA_ARH',ar[4:]),
                        ('IN0',keys[:4]),('IN1',keys[4:]+[0,0])]:
        operand=muxv(c,hit[OP[name]],operand,choice,group='input_select')
    alu=build_alu(c,bits_const(0,6),a,operand,carry,group='alu',selects=hit)
    registers=[]
    for name,width,qcandidate,enable,reset_value,group in [
            ('a_reg',4,alu['result'],alu['a_we'],0,'writeback_a'),
            ('z_reg',1,[alu['z']],alu['z_we'],1,'flags'),
            ('c_reg',1,[alu['c']],alu['c_we'],0,'flags')]:
        active=c.and_(commit,enable,group=group,category='enable')
        registers.append(register(c,name,width,qcandidate,active,'rst',reset_value,group))
    pc_increment=c.inc_bits(pc,group='pc',category='increment')
    jump=c.or_(hit[OP['JMP']],c.or_(c.and_(hit[OP['JZ']],z,group='pc'),
                  c.and_(hit[OP['JC']],carry,group='pc'),group='pc'),group='pc')
    next_pc=muxv(c,jump,pc_increment,instruction[:12],group='pc',category='write_source')
    registers.append(register(c,'pc_reg',12,next_pc,commit,'rst',0,'pc'))
    ar_increment=c.inc_bits(ar,group='ar',category='increment')
    next_ar=ar
    for name,choice in [('ARL',instruction[:4]+ar[4:]),('ARH',ar[:4]+instruction[:4]),
                        ('MOVARL',a+ar[4:]),('MOVARH',ar[:4]+a),('INCAR',ar_increment)]:
        next_ar=muxv(c,hit[OP[name]],next_ar,choice,group='ar',category='write_source')
    ar_enable=c.and_(commit,c.reduce_or([hit[OP[name]] for name in ('ARL','ARH','MOVARL','MOVARH','INCAR')],
                                     group='ar'),group='ar',category='enable')
    registers.append(register(c,'ar_reg',8,next_ar,ar_enable,'rst',0,'ar'))
    gpo_enable=c.and_(commit,hit[OP['OUT']],group='gpo',category='enable')
    registers.append(register(c,'gpo_reg',4,a,gpo_enable,'rst',8,'gpo'))
    # Explicit eight-state transition truth table. No additional state bit.
    exec_next=muxv(c,hit[OP['HALT']],bits_const(1,3),bits_const(6,3),group='control')
    exec_next=muxv(c,memory,exec_next,bits_const(3,3),group='control')
    exec_next=muxv(c,legal,bits_const(7,3),exec_next,group='control')
    destinations=[bits_const(1,3),bits_const(2,3),exec_next,bits_const(4,3),
                  bits_const(5,3),bits_const(1,3),bits_const(6,3),bits_const(7,3)]
    next_state=[]
    for bit in range(3):
        next_state.append(c.reduce_or([c.and_(st[n],destinations[n][bit],group='control')
                                      for n in range(8)],group='control'))
    registers.append(register(c,'state_reg',3,next_state,1,'rst',0,'control'))
    by_name={r['name']:r for r in registers}
    in_memory=c.reduce_or([st[3],st[4],st[5]],group='bus')
    ce=c.and_(c.and_(nrst,legal,group='bus'),c.and_(memory,in_memory,group='bus'),group='bus')
    oe=c.and_(ce,c.inv(write,group='bus'),group='bus')
    we=c.and_(c.and_(ce,write,group='bus'),st[4],group='bus')
    address=muxv(c,dec['indirect'],instruction[:8],ar,group='bus',category='address_select')
    outputs=dict(rom_addr=pc,ram_addr=address,ram_wdata=a,ram_ce=[ce],ram_oe=[oe],ram_we=[we],
        dbg_pc=pc,dbg_a=a,dbg_ar=ar,dbg_z=[z],dbg_c=[carry],dbg_gpo=gpo,dbg_state=state,
        halted=[st[6]],trapped=[st[7]],retire_valid=[commit],retire_pc=pc,
        retire_instruction=instruction,retire_next_pc=by_name['pc_reg']['dbits'],
        retire_a=by_name['a_reg']['dbits'],retire_ar=by_name['ar_reg']['dbits'],
        retire_z=by_name['z_reg']['dbits'],retire_c=by_name['c_reg']['dbits'],
        retire_gpo=by_name['gpo_reg']['dbits'],
        # Only observed when retire_valid=1. These aliases add no debug gate.
        retire_ram_valid=[memory],retire_ram_write=[write],retire_ram_addr=address,
        retire_ram_wdata=a,retire_ram_rdata=rdata,retire_is_memory=[memory],
        retire_instruction_cycles=[memory,not_memory,memory])
    functional_outputs={name:outputs[name] for name in ('rom_addr','ram_addr','ram_wdata','ram_ce','ram_oe','ram_we')}
    return dict(inputs=dict(clk=1,rst=1,keys=6,rom_data=16,ram_rdata=4),
                outputs=outputs,functional_outputs=functional_outputs,registers=registers,
                observation_validity='Retire projections are specified only when retire_valid=1; debug state and buses always valid after reset.')


def build_alu_module(c):
    result=build_alu(c,bits('op',6),bits('a',4),bits('operand',4),'c_in',group='alu')
    outputs={'result':result['result'],'z_out':[result['z']],'c_out':[result['c']],
             'a_we':[result['a_we']],'z_we':[result['z_we']],'c_we':[result['c_we']]}
    return dict(inputs=dict(op=6,a=4,operand=4,c_in=1),outputs=outputs,
                functional_outputs=outputs,registers=[])


def build_decoder_module(c):
    dec=build_decoder(c,bits('instruction',16))
    outputs={name:[dec[name]] for name in ('legal','is_memory','memory_write','indirect')}
    outputs['op']=dec['op']
    return dict(inputs=dict(instruction=16),outputs=outputs,functional_outputs=outputs,registers=[])


def retained_nodes(c, design):
    """Keep only nodes required by functional D/bus roots or observation wires."""
    table={n['id']:n for n in c.nodes}
    functional_roots=[b for r in design['registers'] for b in r['dbits']]
    functional_roots += [b for value in design['functional_outputs'].values() for b in value]
    roots=functional_roots+[b for value in design['outputs'].values() for b in value]
    def cone(values):
        used=set();todo=list(values)
        while todo:
            signal=todo.pop()
            if signal not in table or signal in used:continue
            used.add(signal);node=table[signal]
            todo.extend((node['s'],node['i0'],node['i1']))
        return used
    functional=cone(functional_roots);all_used=cone(roots)
    debug_only=all_used-functional
    if design['registers'] and debug_only:
        raise AssertionError(f'Core observer generated physical gates: {sorted(debug_only)}')
    return [n for n in c.nodes if n['id'] in all_used],len(c.nodes)-len(all_used)


def sv_signal(signal):
    return f"1'b{signal}" if type(signal) is int else signal


def sv_vector(values):
    return sv_signal(values[0]) if len(values)==1 else '{'+', '.join(sv_signal(v) for v in reversed(values))+'}'


def group_label(group):
    return 'g_'+re.sub(r'[^A-Za-z_0-9]','_',group)


def emit_module(module, variant, directory, builder):
    c=Circuit(optimize=variant=='shared');design=builder(c)
    nodes,pruned=retained_nodes(c,design)
    ports=[]
    for direction,table in [('input',design['inputs']),('output',{k:len(v) for k,v in design['outputs'].items()})]:
        for name,width in table.items():
            ports.append(f'    {direction} wire '+(f'[{width-1}:0] ' if width>1 else '')+name)
    source=['`default_nettype none',f'// Generated by m20.v2_build; variant={variant}. Do not hand edit.',
            '// Every combinational instance below is one physical single-bit 157 MUX.',
            f'module {module} (',',\n'.join(ports),');']
    for reg in design['registers']:
        source.append('    logic '+(f'[{reg["width"]-1}:0] ' if reg['width']>1 else '')+reg['name']+';')
    source.extend(f'    wire {n["id"]};' for n in nodes)
    groups=list(dict.fromkeys(n['group'] for n in nodes))
    source.append('    generate')
    for group in groups:
        source.append(f'        if (1) begin : {group_label(group)}')
        for n in nodes:
            if n['group']!=group:continue
            source.append(f'            swc_mux157 u_{n["id"]} (.S({sv_signal(n["s"])}), .I0({sv_signal(n["i0"])}), .I1({sv_signal(n["i1"])}), .Y({n["id"]}));')
        source.append('        end')
    source.append('    endgenerate')
    for name,value in design['outputs'].items():source.append(f'    assign {name} = {sv_vector(value)};')
    for reg in design['registers']:
        source.extend(['    always_ff @(posedge clk) begin',
                       f'        {reg["name"]} <= {sv_vector(reg["dbits"])};',
                       '    end'])
    source += ['endmodule','`default_nettype wire','']
    text='\n'.join(source);path=directory/f'{module}.sv';path.write_text(text)
    def serial(value):return str(value) if type(value) is int else value
    manifest=dict(schema_version=1,module=module,variant=variant,
        inputs=design['inputs'],outputs={k:[serial(v) for v in values] for k,values in design['outputs'].items()},
        functional_outputs={k:[serial(v) for v in values] for k,values in design['functional_outputs'].items()},
        registers=[dict(r,qbits=[serial(v) for v in r['qbits']],dbits=[serial(v) for v in r['dbits']]) for r in design['registers']],
        nodes=[dict(n,y=n['id'],s=serial(n['s']),i0=serial(n['i0']),i1=serial(n['i1']),
                    instance=f'{group_label(n["group"])}.u_{n["id"]}') for n in nodes],
        physical_mux_count=len(nodes),pruned_nodes=pruned,
        ff_bits=sum(r['width'] for r in design['registers']),
        source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        group_counts=dict(Counter(n['group'] for n in nodes)),
        category_counts=dict(Counter(n['category'] for n in nodes)),
        shared_requests=[request for request in c.shared_requests if request['id'] in {node['id'] for node in nodes}],
        pruned_shared_requests=sum(request['id'] not in {node['id'] for node in nodes} for request in c.shared_requests),
        simplifications=c.simplifications,
        observation_validity=design.get('observation_validity','All outputs combinationally specified.'))
    (directory/f'{module}.netlist.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def generate(output):
    output=Path(output);result={}
    for variant in ('baseline','shared'):
        directory=output/variant;directory.mkdir(parents=True,exist_ok=True)
        result[variant]={}
        for name,builder in [('m20v2_alu',build_alu_module),('m20v2_decoder',build_decoder_module),('m20v2_cpu_core',build_core)]:
            manifest=emit_module(name,variant,directory,builder)
            result[variant][name]=dict(muxes=manifest['physical_mux_count'],ff_bits=manifest['ff_bits'])
    print(json.dumps(result,indent=2));return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'rtl/m20/v2/generated')
    args=parser.parse_args(argv);generate(args.output);return 0


if __name__=='__main__':raise SystemExit(main())
