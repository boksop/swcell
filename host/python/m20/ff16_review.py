"""Read-only A/B evidence review and conditional timing exploration.

Writes only to a fresh review output. Does not run a CPU regression, modify the
20-cell structure, or establish physical contamination-delay guarantees.
"""
import argparse, csv, hashlib, json, math, random, re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from .ff16_timing import config, TAPS, ROOT

NET = ROOT/'rtl/m20/v21/generated/m20v21_cpu_core.netlist.json'
OLD = ROOT/'build/m20_300/v24_ff16/small_r4'
PHYS = ROOT/'docs/m20/physical_resources'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def csvread(p):
    with Path(p).open(newline='') as f: return list(csv.DictReader(f))
def csvwrite(p, rows):
    with Path(p).open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def dump(p, v): Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n')

def boundaries(cfg):
    """Full, isolated pulses only. Root is AFTER the two hold cells."""
    g=cfg['gates']; t=cfg['tap']; r=sum(x['dr'] for x in g[:t]); f=sum(x['df'] for x in g[:t])
    h_r=min(g[16]['sr'],r+g[16]['dr'])+g[18]['dr']
    s_r=max(g[17]['sr'],r+g[17]['dr'])+g[19]['dr']
    h_f=max(g[16]['sf'],f+g[16]['df'])+g[18]['df']
    s_f=min(g[17]['sf'],f+g[17]['df'])+g[19]['df']
    leaf=[]
    for i,v in enumerate(cfg['leaves']):
        leaf.append(dict(index=i,branch=i%6,m_close=h_r+v['bmr']+v['mc'],s_open=s_r+v['bsr']+v['so'],
                         m_open=h_f+v['bmf']+v['mo'],s_close=s_f+v['bsf']+v['sc']))
    return dict(chain_r=r,chain_f=f,h_r=h_r,s_r=s_r,h_f=h_f,s_f=s_f,
                root_d1=s_r-h_r,root_d2=h_f-s_f,
                d1=min(v['s_open'] for v in leaf)-max(v['m_close'] for v in leaf),
                d2=min(v['m_open'] for v in leaf)-max(v['s_close'] for v in leaf),leaves=leaf)

def verify_old():
    assert all(sha(ROOT/p)==h for p,h in load(OLD/'source_sha256.json').items())
    assert all(sha(OLD/p)==h for p,h in load(OLD/'input_sha256.json').items())
    for v in csvread(ROOT/'docs/m20/ff16_resources/evidence_sha256.csv'):
        assert sha(OLD/v['path'])==v['sha256'],v['path']
    rows=csvread(OLD/'timing_results.csv'); assert len(rows)==56
    normal={t:sum(v['status']=='CONDITIONAL' for v in rows if int(v['tap'])==t and v['role']=='normal_assumed') for t in TAPS}
    assert normal==dict(zip(TAPS,[3,8,10,11]))
    for t in TAPS:
        log=(OLD/f'xsim/tap{t}.log').read_text()
        assert f'FF16_SMALL_COMPLETE tap={t} cases=14' in log
        for v in rows:
            if int(v['tap'])!=t:continue
            line=next(x for x in log.splitlines() if x.startswith('FF16_CASE case='+v['case']+' '))
            if v['case']!='runt_high':
                for key,col in [('D1','d1_ns'),('D2','d2_ns')]:
                    actual=float(re.search(key+r'=([\d.\-]+)',line)[1]); assert abs(actual-float(v[col]))<.002
                b=boundaries(load(OLD/f'tap{t}/{v["case"]}.json'))
                assert abs(b['d1']-float(v['d1_ns']))<.002 and abs(b['d2']-float(v['d2_ns']))<.002
            for key,col in [('global','global_overlap_events'),('own','own_overlap_events'),('data','data_errors'),('pipe','pipeline_errors'),('penetration','penetration_events'),('missing','missing_windows')]:
                assert int(re.search(key+r'=(\d+)',line)[1])==int(v[col])
    return dict(status='VERIFIED',cases=56,counts=dict(Counter(v['status'] for v in rows)),normal_conditional=normal,
                sources=10,inputs=116,evidence_files=272,summary_sha256=sha(OLD/'small_verification.json'))

def observed_events(trace):
    """Actual first basic-cycle leaf boundaries, after the trace's 1ps settle."""
    events={};previous=None
    for v in csvread(trace):
        if previous and v['checking']=='1' and v['reference_cycle']=='0' and v['measurement_kind'] in ('1','2'):
            kind=int(v['measurement_kind']); tm=float(v['time_ns'])
            if v['clk_ref']!=previous['clk_ref']:events[(kind,'ref',-1)]=tm
            for field,prefix in [('master_effective','m'),('slave_effective','s')]:
                a=int(previous[field],16);b=int(v[field],16)
                for i in range(33):
                    if (a>>i&1)!=(b>>i&1):events[(kind,prefix+str(b>>i&1),i)]=tm
        previous=v
    return events

def decompose(out):
    rows=[];worst=[];pairs=[];net=load(NET);names=[q for r in net['registers'] for q in r['qbits']]
    for row in csvread(OLD/'timing_results.csv'):
        t=int(row['tap']);name=row['case'];cfg=load(OLD/f'tap{t}/{name}.json');b=boundaries(cfg)
        if name=='runt_high':continue
        ev=observed_events(OLD/f'tap{t}/{name}_tap{t}.trace.csv')
        for i,(v,bt) in enumerate(zip(cfg['leaves'],b['leaves'])):
            for kind,edge,k,root,buf,lat in [(1,'m1','m_close',b['h_r'],'bmr','mc'),(1,'s1','s_open',b['s_r'],'bsr','so'),(2,'m0','m_open',b['h_f'],'bmf','mo'),(2,'s0','s_close',b['s_f'],'bsf','sc')]:
                tm=ev.get((kind,edge,i));ref=ev.get((kind,'ref',-1))
                # Late-release cycle0 may intentionally lack this boundary.
                if tm is not None and ref is not None and name!='safe_hold_late_release':assert abs(tm-ref-bt[k])<.003,(name,t,i,k)
                branch=cfg['buffer_branches'][i%6]['base_ns'][buf]
                rows.append(dict(case=name,tap=t,leaf=i,register_index_mapping='ILLUSTRATIVE_NETLIST_ORDER_NOT_PHYSICAL_ASSIGNMENT',register=names[i],branch=i%6,edge=k,
                    ref_absolute_trace_ns=ref,event_absolute_trace_ns=tm,event_relative_trace_ns=None if tm is None or ref is None else round(tm-ref,6),
                    predicted_relative_ns=round(bt[k],6),root_relative_ns=root,buffer_aggregate_ns=v[buf],artificial_branch_base_ns=branch,
                    artificial_within_branch_residual_ns=v[buf]-branch,pcb_separate_ns=None,chip_separate_ns=None,output_skew_separate_ns=None,effective_latch_ns=v[lat],source='actual_trace_plus_assumed_config_decomposition'))
        for kind,closekey,openkey,rootkey,cb,ob,cl,ol in [(1,'m_close','s_open','root_d1','bmr','bsr','mc','so'),(2,'s_close','m_open','root_d2','bsf','bmf','sc','mo')]:
            close=max(b['leaves'],key=lambda x:x[closekey]);opening=min(b['leaves'],key=lambda x:x[openkey]);cv=cfg['leaves'][close['index']];ov=cfg['leaves'][opening['index']]
            bd=ov[ob]-cv[cb];ld=ov[ol]-cv[cl];margin=b[rootkey]+bd+ld
            assert abs(margin-float(row['d1_ns' if kind==1 else 'd2_ns']))<.002
            worst.append(dict(case=name,tap=t,direction=kind,root_ns=b[rootkey],buffer_aggregate_difference_ns=bd,effective_latch_difference_ns=ld,
                pcb_difference_ns=None,cross_chip_difference_ns=None,same_chip_output_skew_ns=None,
                close_leaf=close['index'],close_register=names[close['index']],close_branch=close['branch'],close_relative_ns=close[closekey],
                open_leaf=opening['index'],open_register=names[opening['index']],open_branch=opening['branch'],open_relative_ns=opening[openkey],leaf_margin_ns=margin,
                note='legacy 7ns loss is aggregate buffer3 + effective boundary4; chip/output/PCB not independently identified'))
            for ci in range(33):
                for oi in range(33):
                    pairs.append(dict(case=name,tap=t,direction=kind,closing_leaf=ci,opening_leaf=oi,pair_margin_ns=b['leaves'][oi][openkey]-b['leaves'][ci][closekey],classification='RECOMPUTED_ASSUMED_CONFIG_NOT_PCB_ASSIGNMENT'))
    csvwrite(out/'all_leaf_pairs.csv',pairs)
    csvwrite(out/'leaf_events.csv',rows);csvwrite(out/'root_leaf_decomposition.csv',worst)
    return worst

def apply_loss(cfg,chip=0.,branch=0.,pcb=0.,latch=0.):
    """Explicit new assumed components; each is an adverse closing-opening span."""
    components=[]
    for i,v in enumerate(cfg['leaves']):
        x=i/32; bd=chip*x+branch*x+pcb*x
        v.update(bmr=1+bd,bmf=1+bd,bsr=1+bd,bsf=1+bd,mc=1+latch*x,mo=1+latch*x,so=1+latch*x,sc=1+latch*x)
        components.append(dict(leaf=i,branch=i%6,chip_common_assumed_ns=chip*x,output_branch_assumed_ns=branch*x,pcb_assumed_ns=pcb*x,effective_latch_assumed_ns=1+latch*x))
    return components

def root_for_chain(tau):
    # Balanced delayed opening paths, closing SELECT=4, DATA=1, HOLD DATA=1.
    return max(1.,tau+1.)-min(4.,tau+1.)

def scans(out):
    scan=[];rng=random.Random(240411)
    for tap in TAPS:
        for hundredths in range(50,301,5):
            d=hundredths/100
            for profile in ('uniform','alternating','independent','fall_half'):
                cfg=config('independent_cross',tap)
                for i,g in enumerate(cfg['gates'][:16]):
                    v=d if profile in ('uniform','fall_half') else d*((.75,1.25)[i%2] if profile=='alternating' else rng.uniform(.75,1.25))
                    g.update(dr=v,df=v*(.5 if profile=='fall_half' else 1))
                b=boundaries(cfg)
                scan.append(dict(tap=tap,profile=profile,stage_nominal_ns=d,all16_rise_ns=json.dumps([g['dr'] for g in cfg['gates'][:16]]),all16_fall_ns=json.dumps([g['df'] for g in cfg['gates'][:16]]),chain_r_ns=b['chain_r'],chain_f_ns=b['chain_f'],d1_ns=b['d1'],d2_ns=b['d2'],classification='CONDITIONAL_ASSUMED',meets0=min(b['d1'],b['d2'])>=0,meets4=min(b['d1'],b['d2'])>=4,meets8=min(b['d1'],b['d2'])>=8))
    csvwrite(out/'delay_scan.csv',scan)
    loss=[];parameters=[]
    for axis in ('chip_mismatch','branch_skew','pcb_skew','latch_difference'):
        for t in TAPS:
            for j in range(49):
                value=j/4;cfg=config('independent_cross',t)
                kw=dict(chip=0.,branch=0.,pcb=0.,latch=4.)
                if axis=='chip_mismatch':kw['chip']=value
                elif axis=='branch_skew':kw.update(chip=1.,branch=value)
                elif axis=='pcb_skew':kw.update(chip=1.,branch=.2,pcb=value)
                else:kw.update(chip=1.,branch=.2,latch=value)
                components=apply_loss(cfg,**kw);b=boundaries(cfg)
                loss.append(dict(axis=axis,tap=t,value_ns=value,chip_span_ns=kw['chip'],branch_span_ns=kw['branch'],pcb_span_ns=kw['pcb'],latch_span_ns=kw['latch'],d1_ns=b['d1'],d2_ns=b['d2'],classification='CONDITIONAL_ASSUMED'))
                if t==16 and j==4:parameters.append(dict(axis=axis,gates=cfg['gates'],leaves=cfg['leaves'],separate_components=components))
    dump(out/'explicit_leaf_parameters.json',parameters);csvwrite(out/'leaf_scan.csv',loss)
    envelope=[]
    for d in (.5,.625,.75,.875,1.,1.25,1.5,2.,2.5,3.):
        for guard in (0.,4.,8.,12.):
            for latch in (0.,2.,4.):
                valid=[t for t in TAPS if root_for_chain(t*d)-latch>=guard]
                envelope.append(dict(stage_min_assumed_ns=d,guard_assumed_ns=guard,latch_adverse_span_assumed_ns=latch,
                    tap16_root_ns=root_for_chain(16*d),tap16_allowed_total_distribution_span_ns=root_for_chain(16*d)-latch-guard,
                    minimum_chain_sum_ns=0 if guard+latch==0 else 3+guard+latch,
                    shortest_tap_at_zero_distribution=None if not valid else min(valid),classification='CONDITIONAL_FULL_PULSE_BALANCED_DECODER'))
    csvwrite(out/'safe_envelope.csv',envelope)
    freq=[]
    for t in TAPS:
        for d in (.5,1.,2.,3.):
            cfg=config('independent_cross',t)
            for g in cfg['gates'][:16]:g.update(dr=d,df=d)
            b=boundaries(cfg);ls=b['leaves']
            for hz in (100000,500000,1000000,2000000,5000000,10000000,20000000,50000000,100000000):
                period=1e9/hz
                wm=min(period/2+x['m_close']-x['m_open'] for x in ls);ws=min(period/2+x['s_close']-x['s_open'] for x in ls)
                available=period+min(x['m_close'] for x in ls)-max(x['s_open'] for x in ls)
                valid=period/2>max(b['chain_r'],b['chain_f'])+max(cfg['gates'][16]['sr'],cfg['gates'][17]['sf'])
                freq.append(dict(tap=t,stage_ns=d,frequency_hz=hz,period_ns=period,
                    d1_ns=b['d1'] if valid else None,d2_ns=b['d2'] if valid else None,
                    master_window_ns=wm,slave_window_ns=ws,ff_launch_to_next_close_budget_ns=available,
                    assumed_required_master_window_ns=100.,assumed_ff_settle_ns=29*5.2+5+5,
                    satisfies_illustrative_setup=valid and wm>=100 and available>=29*5.2+10,
                    classification='CONDITIONAL_FULL_PULSE' if valid else 'FULL_PULSE_FORMULA_NOT_APPLICABLE'))
    csvwrite(out/'frequency_scan.csv',freq)
    feasibility=[]
    for f in (100000,500000,1000000,2000000,5000000,10000000,20000000):
        for window in (10.,100.):
            period=1e9/f
            # Exact for the balanced independent_cross family only.
            tau_max=min(period/2+3-window,period-(29*5.2+10)-4,period/2-4)
            for guard in (0.,4.,8.):
                tau_min=3+7+guard
                feasibility.append(dict(frequency_hz=f,master_window_required_assumed_ns=window,guard_assumed_ns=guard,
                    minimum_chain_sum_ns=tau_min,maximum_chain_sum_ns=tau_max,
                    interval_exists=tau_min<=tau_max,assumed_ff_path_plus_cq_setup_ns=29*5.2+10,
                    condition='BALANCED_DECODER_DISTRIBUTION3_LATCH4_NO_SERVICE_BUDGET_NOT_CPU_FMAX'))
    csvwrite(out/'frequency_envelope.csv',feasibility)
    dec=[]
    for t in TAPS:
        for sr in (.5,1.,2.,4.,5.2):
            for holdm,holds in ((.5,5.),(1.,1.),(5.,.5)):
                cfg=config('independent_cross',t);cfg['gates'][16]['sr']=sr;cfg['gates'][17]['sf']=sr
                cfg['gates'][18].update(dr=holdm,df=holds);cfg['gates'][19].update(dr=holds,df=holdm)
                b=boundaries(cfg);dec.append(dict(tap=t,close_select_ns=sr,close_hold_data_ns=holdm,open_hold_data_ns=holds,root_d1=b['root_d1'],root_d2=b['root_d2'],d1=b['d1'],d2=b['d2'],classification='CONDITIONAL_ASSUMED'))
    csvwrite(out/'decode_hold_scan.csv',dec)
    relative=[]
    for t in TAPS:
        for rh in (0.,.5,1.,2.):
            for rs in (0.,.5,1.,2.):
                for datah,datas in ((.5,5.),(1.,1.),(5.,.5)):
                    cfg=config('independent_cross',t)
                    cfg['gates'][16].update(sr=4+rh,sf=1+rh,dr=datah,df=datah)
                    cfg['gates'][17].update(sr=1+rs,sf=4+rs,dr=datas,df=datas)
                    b=boundaries(cfg)
                    relative.append(dict(tap=t,or_select_input_route_assumed_ns=rh,and_select_input_route_assumed_ns=rs,
                        or_data_arc_ns=datah,and_data_arc_ns=datas,d1=b['d1'],d2=b['d2'],
                        note='route folded into SELECT arrival before Boolean evaluation; full pulses only, no analog glitch guarantee'))
    csvwrite(out/'relative_decode_inputs.csv',relative)
    safe=[]
    for lead in (-1.,1.,4.,8.,12.,16.,32.,64.,128.,200.):
        # Raw H is already low, as in the old late-release counterexample.
        # Output low requires BOTH release SELECT and raw low DATA to arrive.
        release_select=-lead+12.;raw_h_rise_data=2.
        root_low=max(-lead+12.,-1000.)
        potential=max(0.,raw_h_rise_data-root_low)
        safe.append(dict(release_lead_before_ref_rise_ns=lead,hold_master_select_fall_assumed_ns=12.,
            raw_h_rise_at_hold_data_ns=raw_h_rise_data,potential_root_master_low_pulse_ns=potential,
            meets_assumed_100ns_window=potential>=100.,
            classification='ANALYTICAL_NECESSARY_WINDOW_ONLY_INERTIAL_FILTER_CAN_REMOVE_SHORT_PULSES',
            old_actual_failure='small_r4 safe_hold_late_release' if lead==1 else '',
            memory_transaction_guarantee='NOT_VERIFIED'))
    csvwrite(out/'safe_hold_release_budget.csv',safe)
    comparisons=[]
    for device in load(ROOT/'config/m20/ff16_buffer_sources.json')['devices']:
        lo=device['tpd_min_ns'];hi=device['tpd_max_ns'];span=None if lo is None else hi-lo
        for guard in (0.,4.,8.):
            comparisons.append(dict(part=device['part'],buffer_path_min_ns=lo,buffer_path_max_ns=hi,independent_cross_package_span_ns=span,
                same_package_same_direction_skew_ns=device['output_skew_max_ns'],part_to_part_same_conditions_ns=device['part_to_part_skew_max_ns'],
                assumed_pcb_span_ns=1.,assumed_effective_latch_span_ns=4.,guard_assumed_ns=guard,
                required_root_gap_ns=None if span is None else span+1+4+guard,
                required_tap16_chain_min_ns=None if span is None else 3+span+1+4+guard,
                classification='PART_SPEC_PLUS_ASSUMED_SYSTEM_BOUND_CONDITIONAL_NOT_BUFFER_RANKING'))
    csvwrite(out/'buffer_comparison.csv',comparisons)

def evaluate(net,initial):
    v=dict(initial)
    for n in net['nodes']:v[n['id']]=v[n['i1']] if v[n['s']] else v[n['i0']]
    return v

def witnesses(out):
    net=load(NET);table={n['id']:n for n in net['nodes']};regs=[q for r in net['registers'] for q in r['qbits']]
    dm={q:d for r in net['registers'] for q,d in zip(r['qbits'],r['dbits'])};rows=csvread(PHYS/'co_launch_risks.csv');assert len(rows)==79
    manifest=load(PHYS/'trace_manifest.json')
    assert sha(NET)==manifest['netlist_sha256']
    assert all(sha(ROOT/p)==h for p,h in manifest['trace_files'].items())
    traces=Path(manifest['trace_directory']);meta=load(traces/'metadata.json');cache={};vectors=[];analysis=[];routepins=[]
    for idx,row in enumerate(rows):
        w=json.loads(row['witness']);case=w['case']
        if case not in cache:
            entry=next(x for x in meta['cases'] if x['name']==case)
            cache[case]=(entry,csvread(traces/(case+'.rtl.csv')),[int(x) for x in (traces/(case+'.keys.txt')).read_text().split()])
        entry,events,keys=cache[case];seq=w['sequence'];e={k:int(v) for k,v in events[seq].items()};old=entry['initial'] if seq==0 else {k:int(v) for k,v in events[seq-1].items()}
        initial={'0':0,'1':1,'rst':0};fields=dict(pc_reg=(e['pc'],12),ar_reg=(old['ar'],8),a_reg=(old['a'],4),z_reg=(old['z'],1),c_reg=(old['c'],1),gpo_reg=(old['gpo'],4),state_reg=(5 if e['ram_kind'] else 2,3),rom_data=(e['word'],16),keys=(keys[seq],6),ram_rdata=(e['ram_data'] if e['ram_kind']==1 else 0,4))
        for name,(val,width) in fields.items():
            for bit in range(width):initial[name if width==1 else f'{name}[{bit}]']=(val>>bit)&1
        v=evaluate(net,initial);source=row['source'];dest=row['destination'];last=source;conditions=[]
        route=row['route'].split(';');assert len(route)==int(row['mux_layers'])
        for item in route:
            nid,pin=item.split(':');n=table[nid];assert n[pin]==last,(idx,item,last);last=nid
            active=(v[n['i0']]!=v[n['i1']]) if pin=='s' else v[n['s']]==int(pin=='i1');assert active
            condition=f'{nid}:{pin}, S={v[n["s"]]}, I0={v[n["i0"]]}, I1={v[n["i1"]]}'
            conditions.append(condition);routepins.append(dict(path_id=idx,node=nid,group=n['group'],pin=pin,input_net=n[pin],side_conditions=condition))
        assert last==dm[dest] and v[dm[source]]!=v[source]
        flip=dict(initial);flip[source]^=1;after=evaluate(net,flip);assert after[dm[dest]]!=v[dm[dest]]
        vectors.append(dict(path_id=idx,source=source,destination=dest,source_index=regs.index(source),destination_index=regs.index(dest),initial=initial,
                            before_dest_d=v[dm[dest]],after_flip_dest_d=after[dm[dest]],next_source=v[dm[source]],witness=w,conditions=conditions))
        for t in TAPS:
            cfg=config('fast_chain_sensitivity',t);b=boundaries(cfg);si=regs.index(source);di=regs.index(dest)
            for placement in ('illustrative_net_order','adversarial_source0_dest32'):
                sl=b['leaves'][si if placement=='illustrative_net_order' else 0];dl=b['leaves'][di if placement=='illustrative_net_order' else 32]
                for minimum in (0.,.1,.25,.5,1.,2.):
                    cd=len(route)*minimum;arrival=sl['s_open']+cd;gap=arrival-dl['m_close']
                    analysis.append(dict(path_id=idx,source=source,destination=dest,mux_layers=len(route),route=row['route'],witness_case=case,witness_sequence=seq,word=w['word'],microstate=fields['state_reg'][0],same_microcycle='REVERIFIED_TRACE_AND_ISOLATED_BOOLEAN_INFLUENCE',tap=t,placement=placement,
                        data_and_select_min_assumed_ns_per_cell=minimum,path_min_assumed_ns=cd,slave_clock_to_q_min_assumed_ns=0.,data_pcb_min_assumed_ns=0.,destination_capture_guard_assumed_ns=0.,
                        source_slave_open_ns=sl['s_open'],destination_master_close_ns=dl['m_close'],clock_pair_margin_ns=sl['s_open']-dl['m_close'],earliest_assumed_arrival_ns=arrival,path_hold_slack_ns=gap,
                        classification='CONDITIONAL_RISK' if gap<0 else ('BOUNDARY_NOT_QUALIFIED' if gap==0 else 'CONDITIONAL_NO_EARLY_ARRIVAL'),physical_safety='NOT_VERIFIED'))
    dump(out/'cpu_witness_vectors.json',vectors);csvwrite(out/'cpu_short_paths.csv',analysis);csvwrite(out/'cpu_route_pins.csv',routepins)
    return net,regs,vectors

def plots(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    def save(fig,name):
        fig.savefig(out/name);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    for t in TAPS:
        a=[r for r in csvread(out/'delay_scan.csv') if int(r['tap'])==t and r['profile']=='uniform']
        ax.plot([float(r['stage_nominal_ns']) for r in a],[float(r['d1_ns']) for r in a],label=f'TAP{t}, D1=D2')
    ax.axhline(0,color='r');ax.axhline(4,color='gray',linestyle='--');ax.set(xlabel='Assumed DATA delay per stage (ns)',ylabel='Global effective margin (ns)',title='Balanced decoder; aggregate buffer span3 + latch span4ns');ax.legend();ax.grid(alpha=.2);save(fig,'delay_sensitivity.svg')
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for ax,axis in zip(axes,('chip_mismatch','branch_skew','latch_difference')):
        for t in TAPS:
            a=[r for r in csvread(out/'leaf_scan.csv') if int(r['tap'])==t and r['axis']==axis]
            ax.plot([float(r['value_ns']) for r in a],[float(r['d1_ns']) for r in a],label=f'TAP{t}')
        ax.axhline(0,color='r');ax.axhline(4,color='gray',linestyle='--');ax.set(xlabel=axis+' (assumed ns)',ylabel='D1=D2 (ns)');ax.grid(alpha=.2)
    axes[-1].legend();save(fig,'leaf_sensitivity.svg')
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for t in TAPS:
        a=[r for r in csvread(out/'frequency_scan.csv') if int(r['tap'])==t and float(r['stage_ns'])==2.]
        axes[0].semilogx([float(r['frequency_hz'])/1e6 for r in a if r['d1_ns']],[float(r['d1_ns']) for r in a if r['d1_ns']],marker='o',label=f'TAP{t}')
        axes[1].semilogx([float(r['frequency_hz'])/1e6 for r in a],[float(r['master_window_ns']) for r in a],marker='o',label=f'TAP{t}')
    axes[0].set(xlabel='Reference frequency (MHz)',ylabel='D1=D2 (ns)',title='Valid full-pulse domain only; same-edge margin stays fixed')
    axes[1].set(xlabel='Reference frequency (MHz)',ylabel='Master transparent window (ns)',ylim=(-50,1100),title='Higher frequency shortens computation window')
    for ax in axes:ax.legend();ax.grid(alpha=.2)
    save(fig,'frequency_sensitivity.svg')
    import numpy as np
    stage=np.linspace(.5,3,101);loss=np.linspace(0,16,81);z=16*stage[None,:]-3-loss[:,None]
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained');im=ax.pcolormesh(stage,loss,z,shading='auto',cmap='coolwarm');fig.colorbar(im,ax=ax,label='D1=D2 (assumed ns)')
    contours=ax.contour(stage,loss,z,levels=[0,4,8],colors=['red','black','green']);ax.clabel(contours,fmt='%g ns')
    ax.set(xlabel='Assumed minimum delay per stage (ns)',ylabel='Total adverse distribution + latch span (ns)',title='TAP16 conditional envelope; fixed balanced decoder');save(fig,'tap16_envelope.svg')

def analyze(out):
    out=Path(out).resolve()
    if out.exists() or ROOT/'build/m20_300/v24_ff16' not in out.parents:raise ValueError('requires fresh review output under build/m20_300/v24_ff16')
    out.mkdir(parents=True);dump(out/'baseline_review.json',verify_old());decompose(out);scans(out);net,regs,vectors=witnesses(out);plots(out)
    dump(out/'analysis_summary.json',dict(status='VERIFIED_ANALYSIS_EXECUTION_NOT_PHYSICAL_SIGNOFF',real_paths=len(vectors),delay_points=4*51*4,leaf_points=4*4*49,project_gate='NO_C_D_FULL_REGRESSION',buffer_sources_sha256=sha(ROOT/'config/m20/ff16_buffer_sources.json'),script_sha256=sha(__file__)))
    print('FF16_REVIEW_ANALYZED old56=verified real79=reverified no_CPU_regression=1')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.output)
