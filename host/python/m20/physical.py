"""MUX pin-arc topology, max-delay scenarios, short paths and load analysis.
All physical numbers are estimates; no hold/Fmax guarantee or FPGA-STA claim.
"""
import argparse,csv,hashlib,json,random
from collections import Counter
from pathlib import Path
from .v21_audit import audit
ROOT=Path(__file__).resolve().parents[3]

def write_csv(path,rows):
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def paths(net,device,wire=0.0,k=50,allowed_sources=None):
    """Exact k-best pin-arc walks on a DAG, separately for each source class."""
    table={n['id']:n for n in net['nodes']};ff={s for r in net['registers'] for s in r['qbits']}
    inputs={s for name,w in net['inputs'].items() if name!='clk' for s in ([name] if w==1 else [f'{name}[{i}]' for i in range(w)])}
    cache={};busy=set()
    def walk(s,kind):
        key=s,kind
        if key in cache:return cache[key]
        if s not in table:
            ok=(kind=='FF' and s in ff) or (kind=='FPGA' and s in inputs)
            return [(0.0,s,())] if ok and (allowed_sources is None or s in allowed_sources) else []
        if s in busy:raise ValueError('cycle')
        busy.add(s);n=table[s];candidates=[]
        for pin in ('s','i0','i1'):
            delay=device['select_ns' if pin=='s' else 'data_ns']['max']+wire
            for t,src,route in walk(n[pin],kind):candidates.append((t+delay,src,route+((s,pin),)))
        busy.remove(s);cache[key]=sorted(candidates,key=lambda a:(-a[0],a[1],a[2]))[:k];return cache[key]
    endpoints=[(f'{r["name"]}.D[{i}]',s,'FF') for r in net['registers'] for i,s in enumerate(r['dbits'])]
    endpoints += [(f'{p}[{i}]',s,'OUTPUT') for p,v in net['functional_outputs'].items() for i,s in enumerate(v)]
    rows=[]
    for kind in ('FF','FPGA'):
        for endpoint,s,destination in endpoints:
            for t,src,route in walk(s,kind):
                rows.append(dict(path_class=kind+'_TO_'+destination,source=src,endpoint=endpoint,endpoint_net=s,
                    mux_layers=len(route),select_arcs=sum(p=='s' for _,p in route),data_arcs=sum(p!='s' for _,p in route),
                    max_scenario_ns=round(t,6),groups='>'.join(dict.fromkeys(table[n]['group'] for n,_ in route)),
                    route=';'.join(n+':'+p for n,p in route),sensitization='UNPROVEN_STATIC_TOPOLOGY'))
    return sorted(rows,key=lambda r:(-r['max_scenario_ns'],r['source'],r['endpoint'],r['route']))

def shortest_pairs(net):
    """Minimum gate count from each FF-Q to each FF-D; not a tCD bound."""
    table={n['id']:n for n in net['nodes']};ff={s for r in net['registers'] for s in r['qbits']}
    cache={}
    def walk(s):
        if s in cache:return cache[s]
        if s not in table:return {s:()} if s in ff else {}
        result={}
        for pin in ('s','i0','i1'):
            for src,route in walk(table[s][pin]).items():
                r=route+((s,pin),)
                if src not in result or len(r)<len(result[src]):result[src]=r
        cache[s]=result;return result
    rows=[]
    for r in net['registers']:
        for i,d in enumerate(r['dbits']):
            for src,route in walk(d).items():
                rows.append(dict(source=src,destination=r['qbits'][i],mux_layers=len(route),
                    self_feedback=src==r['qbits'][i],route=';'.join(n+':'+p for n,p in route),
                    contamination_min_ns='',hold_status='TBD_NOT_CERTIFIED',sensitization='UNPROVEN_INCLUDES_HOLD_PATHS'))
    return sorted(rows,key=lambda r:(r['mux_layers'],r['self_feedback'],r['source'],r['destination']))

def static_witness(rows,net,attempts=3000):
    """Find stable side-condition vectors; never claims sequential reachability."""
    rng=random.Random(210543);nodes=net['nodes'];table={n['id']:n for n in nodes};unresolved=set(range(len(rows)));found={}
    ff=[s for r in net['registers'] for s in r['qbits']]
    ins=[s for name,w in net['inputs'].items() if name!='clk' for s in ([name] if w==1 else [f'{name}[{i}]' for i in range(w)])]
    for _ in range(attempts):
        values={'0':0,'1':1}|{s:rng.randrange(2) for s in ff+ins};values['rst']=0
        initial=dict(values)
        for n in nodes:values[n['id']]=values[n['i1']] if values[n['s']] else values[n['i0']]
        for idx in list(unresolved):
            row=rows[idx];ok=True
            for item in row['route'].split(';'):
                node,pin=item.split(':');n=table[node]
                if (pin=='s' and values[n['i0']]==values[n['i1']]) or (pin=='i0' and values[n['s']]!=0) or (pin=='i1' and values[n['s']]!=1):ok=False;break
            if ok:
                row['sensitization']='STATIC_SIDE_CONDITIONS_WITNESS_NOT_SEQUENTIAL_PROOF';found[str(idx)]=initial;unresolved.remove(idx)
        if not unresolved:break
    return found

def analyze(net_path,models_path,output):
    net_path=Path(net_path);net=json.loads(net_path.read_text());models=json.loads(Path(models_path).read_text())
    output=Path(output);output.mkdir(parents=True,exist_ok=True);cfg=models['scenario'];device=models['devices'][cfg['device']]
    audited=audit(net_path.with_suffix('').with_suffix('.sv'),net_path,net_path.parent.parent/'swc_mux157.sv')
    allpaths=paths(net,device,cfg['wire_delay_ns_per_gate']);top=allpaths[:50]
    witnesses=static_witness(top,net)
    write_csv(output/'top50_paths.csv',top);write_csv(output/'shortest_ff_paths.csv',shortest_pairs(net))
    # Keep worst for each origin/destination class and each requested sink module.
    classes={}
    for row in allpaths:classes.setdefault(row['path_class'],row)
    write_csv(output/'path_classes.csv',list(classes.values()))
    endpoints={}
    for row in allpaths:endpoints.setdefault(row['endpoint'].split('.')[0].split('[')[0],row)
    write_csv(output/'endpoint_paths.csv',list(endpoints.values()))
    categories=[]
    filters={
      'PC_INCREMENT_OR_JUMP_FF_LOOP':lambda r:r['source'].startswith('pc_reg') and r['endpoint'].startswith('pc_reg'),
      'AR_INCREMENT_FF_LOOP':lambda r:r['source'].startswith('ar_reg') and r['endpoint'].startswith('ar_reg'),
      'ALU_FLAGS_FF_LOOP':lambda r:r['path_class']=='FF_TO_FF' and r['endpoint'].split('.')[0] in ('a_reg','z_reg','c_reg'),
      'ROM_TO_STATE':lambda r:r['source'].startswith('rom_data') and r['endpoint'].startswith('state_reg'),
      'RAM_DATA_TO_A':lambda r:r['source'].startswith('ram_rdata') and r['endpoint'].startswith('a_reg'),
      'STATE_TO_RAM_WE':lambda r:r['source'].startswith('state_reg') and r['endpoint']=='ram_we[0]',
      'RESET_TO_D':lambda r:r['source']=='rst' and r['path_class']=='FPGA_TO_FF'}
    # Re-run DAG search with each source family, so top-k ROM paths cannot hide RAM/reset paths.
    ff_sources={q for r in net['registers'] for q in r['qbits']}
    families={
      'PC_INCREMENT_OR_JUMP_FF_LOOP':{q for q in ff_sources if q.startswith('pc_reg')},
      'AR_INCREMENT_FF_LOOP':{q for q in ff_sources if q.startswith('ar_reg')},
      'ALU_FLAGS_FF_LOOP':ff_sources,
      'ROM_TO_STATE':{f'rom_data[{i}]' for i in range(16)},
      'RAM_DATA_TO_A':{f'ram_rdata[{i}]' for i in range(4)},
      'STATE_TO_RAM_WE':{q for q in ff_sources if q.startswith('state_reg')},
      'RESET_TO_D':{'rst'}}
    for label,predicate in filters.items():
        matching=[r for r in paths(net,device,cfg['wire_delay_ns_per_gate'],allowed_sources=families[label]) if predicate(r)]
        if matching:categories.append(dict(category=label,**matching[0]))
    write_csv(output/'critical_categories.csv',categories)
    (output/'sensitization_witnesses.json').write_text(json.dumps(witnesses,indent=2)+'\n')
    fan=audited['fanout'];pin_loads={r['signal']:r['pin_load'] for r in fan}
    # For real DFFs the native FF-D load becomes one master input, Q feedback adds one slave input.
    for r in net['registers']:
        for d,q in zip(r['dbits'],r['qbits']):pin_loads[d]=pin_loads.get(d,0)+1;pin_loads[q]=pin_loads.get(q,0)+1
    for r in net['registers']:
        for i in range(r['width']):pin_loads[f'QM_{r["name"]}_{i}']=2
    fpga_loads=Counter(s for p in ('rom_addr','ram_addr','ram_wdata','ram_ce','ram_oe','ram_we','dbg_gpo') for s in net['outputs'][p])
    loads=[]
    for s,count in sorted(pin_loads.items()):
        cap=count*device['cin_typ_pf']+cfg['wire_cap_pf_per_net']+fpga_loads[s]*cfg['fpga_input_cap_assumed_pf']
        loads.append(dict(signal=s,pin_load=count,cin_typ_based_pf=round(cap,3),wire_cap_assumed_pf=cfg['wire_cap_pf_per_net'],fpga_input_load_pf=fpga_loads[s]*cfg['fpga_input_cap_assumed_pf'],
                          exceeds_timing_test_load=cap>device['load_pf'],cap_bound_status='ESTIMATED_CIN_MAX_NOT_SPECIFIED'))
    write_csv(output/'loads.csv',loads)
    clock=dict(state_bits=33,clock_select_pins=66,clock_pin_cap_typ_pf=66*device['cin_typ_pf'],clock_route_cap_pf=None,
               two_phase_pins_per_phase=33,status='ESTIMATED_TYP_CAP_TBD_SKEW')
    result=dict(status='ESTIMATED_PHYSICAL_NOT_STA',topology_status='VERIFIED',mux=audited['combinational_mux'],
                full_equivalent=audited['full_equivalent'],functional_equivalent=audited['functional_equivalent'],
                max_topology_layers=audited['max_mux_depth'],worst=top[0],path_classes=classes,
                shortest_nonself=next(r for r in shortest_pairs(net) if not r['self_feedback']),
                static_witness_count=len(witnesses),witness_attempts=3000,
                unproven_paths=50-len(witnesses),clock=clock,
                overloaded_model_nets=[r['signal'] for r in loads if r['exceeds_timing_test_load']],
                topology_warning='All paths unproven as worst sensitizable dynamic paths; static witnesses are not reachable-state proof',
                hold_status='TBD_FOR_ALL_FREQUENCIES',source_sha256=net['source_sha256'],
                model_sha256=hashlib.sha256(Path(models_path).read_bytes()).hexdigest(),scenario=cfg,analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    freqs=[];powers=[]
    fixed=sum(cfg[k] for k in ('clock_to_q_assumed_ns','setup_assumed_ns','skew_assumed_ns','board_fixed_delay_assumed_ns','margin_assumed_ns'))
    worst_ff=classes['FF_TO_FF']['max_scenario_ns'];rom_delay=classes['FPGA_TO_FF']['max_scenario_ns']+cfg['fpga_rom_service_assumed_ns']
    for hz in cfg['frequencies_hz']:
        period=1e9/hz;budget=max(worst_ff,rom_delay)+fixed
        freqs.append(dict(frequency_hz=hz,period_ns=period,assumed_required_ns=round(budget,3),
            setup_scenario_slack_ns=round(period-budget,3),setup_scenario='POSITIVE_ESTIMATE' if period>=budget else 'NEGATIVE_ESTIMATE',
            qualification='TBD_HOLD_DFF_LOAD_BOARD_UNQUALIFIED',pong_tick_max_observed_ms=308*1000/hz,
            snake_tick_max_observed_ms=13419*1000/hz,snake_boot_ms=4531*1000/hz))
        for alpha in cfg['activity_factors']:
            internal=(477*alpha*cfg['internal_input_switch_factor']+66)*device['cpd_typ_pf']*1e-12*3.3**2*hz
            load_switch_w=sum(r['cin_typ_based_pf'] for r in loads)*1e-12*3.3**2*hz*alpha
            # Add the unconditionally switching external clock capacitive load separately.
            clock_w=clock['clock_pin_cap_typ_pf']*1e-12*3.3**2*hz
            static=543*device['icc_max_ua']*1e-6*3.3
            powers.append(dict(hz=hz,activity=alpha,internal_w=round(internal,6),switched_output_w=round(load_switch_w,6),external_clock_driver_w=round(clock_w,6),static_icc_w=round(static,6),
                total_illustrative_w=round(internal+load_switch_w+clock_w+static,6),status='ESTIMATED_NOT_PSU_RATING_EXCLUDES_GLITCHES_AND_SLOW_INPUT_CURRENT'))
    write_csv(output/'frequency_scenarios.csv',freqs);write_csv(output/'power_scenarios.csv',powers)
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    write_csv(output/'device_parameters.csv',[dict(part=k,source=d['source'],revision=d['revision'],vcc_range=str(d['vcc_range_v']),temperature=str(d['temperature_c']),
        cl_pf=d['load_pf'],data_min_ns=d['data_ns']['min'],data_typ_ns=d['data_ns']['typ'],data_max_ns=d['data_ns']['max'],select_min_ns=d['select_ns']['min'],select_typ_ns=d['select_ns']['typ'],select_max_ns=d['select_ns']['max'],
        cin_typ_pf=d['cin_typ_pf'],icc_max_ua=d['icc_max_ua'],cpd_typ_pf=d['cpd_typ_pf'],package=d['package']) for k,d in models['devices'].items()])
    print(f'M20_PHYSICAL_ANALYSIS layers={result["max_topology_layers"]} hold=TBD witnesses={len(witnesses)}/50');return result

def trace_short_paths(net_path,trace_directory,output):
    """Cross-check short paths with actual boot/continuous RTL retirement data.
    Co-launch is a logical risk witness, not a transistor-level race proof.
    """
    net=json.loads(Path(net_path).read_text());root=Path(trace_directory);out=Path(output)
    rows=shortest_pairs(net);wanted=[r for r in rows if not r['self_feedback'] and r['mux_layers']<=8]
    table={n['id']:n for n in net['nodes']};dmap={q:d for r in net['registers'] for q,d in zip(r['qbits'],r['dbits'])}
    found={};metadata=json.loads((root/'metadata.json').read_text());trace_files=[root/'metadata.json']
    def evaluate(initial):
        v=dict(initial)
        for n in net['nodes']:v[n['id']]=v[n['i1']] if v[n['s']] else v[n['i0']]
        return v
    for case in metadata['cases']:
        if case['name'] not in ('pong_boot','snake_boot','pong_continuous_64','snake_continuous_64'):continue
        trace_files += [root/(case['name']+'.keys.txt'),root/(case['name']+'.rtl.csv')]
        old=dict(case['initial']);schedule=[int(x) for x in (root/(case['name']+'.keys.txt')).read_text().split()]
        with (root/(case['name']+'.rtl.csv')).open() as f:
            for event in csv.DictReader(f):
                e={k:int(v) for k,v in event.items()};seq=e['sequence'];initial={'0':0,'1':1,'rst':0}
                fields=dict(pc_reg=(e['pc'],12),ar_reg=(old['ar'],8),a_reg=(old['a'],4),z_reg=(old['z'],1),c_reg=(old['c'],1),
                    gpo_reg=(old['gpo'],4),state_reg=(5 if e['ram_kind'] else 2,3),rom_data=(e['word'],16),keys=(schedule[seq],6),ram_rdata=(e['ram_data'] if e['ram_kind']==1 else 0,4))
                for name,(value,width) in fields.items():
                    for i in range(width):initial[name if width==1 else f'{name}[{i}]']=(value>>i)&1
                v=evaluate(initial)
                for reg,key in [('a_reg','a'),('ar_reg','ar'),('z_reg','z'),('c_reg','c'),('gpo_reg','gpo'),('pc_reg','next_pc')]:
                    r=next(x for x in net['registers'] if x['name']==reg)
                    actual=sum(v[d]<<i for i,d in enumerate(r['dbits']))
                    if actual!=e[key]:raise ValueError('RTL trace is not aligned with analyzed graph')
                for row in wanted:
                    pair=row['source'],row['destination']
                    if pair in found or v[dmap[pair[0]]]==v[pair[0]]:continue
                    ok=True
                    for item in row['route'].split(';'):
                        name,pin=item.split(':');n=table[name]
                        if (pin=='s' and v[n['i0']]==v[n['i1']]) or (pin=='i0' and v[n['s']]!=0) or (pin=='i1' and v[n['s']]!=1):ok=False;break
                    if not ok:continue
                    flip=dict(initial);flip[pair[0]]^=1;after=evaluate(flip)
                    if after[dmap[pair[1]]]!=v[dmap[pair[1]]]:
                        found[pair]=dict(case=case['name'],sequence=seq,pc=e['pc'],word=f"{e['word']:04X}")
                old={k:e[k] for k in ('a','ar','z','c','gpo')}
    for row in rows:
        witness=found.get((row['source'],row['destination']))
        row.update(co_launch='WITNESS_ON_ACTUAL_RTL_TRACE' if witness else 'NOT_OBSERVED_NOT_PROOF',witness=json.dumps(witness) if witness else '')
    write_csv(out/'shortest_ff_paths.csv',rows)
    write_csv(out/'co_launch_risks.csv',[r for r in rows if r['co_launch']=='WITNESS_ON_ACTUAL_RTL_TRACE'])
    (out/'trace_manifest.json').write_text(json.dumps(dict(trace_directory=str(root.resolve()),trace_files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in trace_files},netlist_sha256=hashlib.sha256(Path(net_path).read_bytes()).hexdigest(),co_launch_witness_count=len(found)),indent=2)+'\n')
    return len(found)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--netlist',type=Path,default=ROOT/'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json');p.add_argument('--traces',type=Path);p.add_argument('--models',type=Path,default=ROOT/'config/m20/157_timing_models.json');p.add_argument('--output',type=Path,default=ROOT/'docs/m20/physical_resources');a=p.parse_args();analyze(a.netlist,a.models,a.output)
    if a.traces:print("CO_LAUNCH_RISKS",trace_short_paths(a.netlist,a.traces,a.output))
if __name__=='__main__':main()
