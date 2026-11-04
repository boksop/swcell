#!/usr/bin/env python3
"""Plot existing XSIM observations only; no interpolation or new simulations."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT/'build/m20_300/v24_ff16/deep_review_r4'
SUMMARY = ROOT/'docs/m20/ff16_review_resources'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))

def generate(output):
    output = output.resolve()
    if output.exists():
        raise FileExistsError('Use a fresh output directory; existing evidence is preserved')
    raw = RUN/'cone_results.csv'
    recorded = next(r for r in rows(SUMMARY/'evidence_sha256.csv') if r['path']=='cone_results.csv')
    assert sha(raw)==recorded['sha256'], 'Raw XSIM results changed'
    sources = json.loads((SUMMARY/'source_sha256.json').read_text())
    tb = 'sim/m20_ff16_review/tb_ff16_cpu_cones.sv'
    assert sha(ROOT/tb)==sources[tb], 'Clock configuration testbench changed'
    margins = rows(SUMMARY/'root_leaf_decomposition.csv')
    case_for_stage = {0.5:'fast_chain_sensitivity', 2.0:'independent_cross'}
    groups = defaultdict(list)
    for row in rows(raw):
        groups[(float(row['chain_stage_ns']), float(row['cell_min_ns']))].append(row)
    assert len(groups)==8
    data = []
    for (stage, delay), group in sorted(groups.items()):
        assert len(group)==79 and {int(r['path_id']) for r in group}==set(range(79))
        assert all(int(r['mismatch'])==int(r['expected_destination']!=r['actual_destination']) for r in group)
        case = case_for_stage[stage]
        values = {int(r['direction']):float(r['leaf_margin_ns']) for r in margins if r['case']==case and r['tap']=='16'}
        assert len(values)==2 and values[1]==values[2]
        data.append(dict(d1_ns=values[1],d2_ns=values[2],chain_stage_assumed_ns=stage,
                         combination_mux_delay_assumed_ns=delay,paths_checked=79,
                         observed_error_paths=sum(int(r['mismatch']) for r in group),
                         source='XSIM_LOCAL_TWO_LATCH_PAIR_EXPERIMENT',
                         physical_status='NOT_VERIFIED'))
    expected={.125:79,.25:52,.5:0,1.:0}
    assert all(r['observed_error_paths']==(expected[r['combination_mux_delay_assumed_ns']] if r['d1_ns']==-2 else 0) for r in data)
    output.mkdir(parents=True)
    with (output/'margin_error_points.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)

    fontfile=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    font=FontProperties(fname=fontfile)
    plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,
                         'svg.fonttype':'path','font.size':11})
    colors=['#c93232','#dc8700','#1678ab','#5e4597']
    markers=['o','s','D','^']
    delays=[.125,.25,.5,1.]
    fig=plt.figure(figsize=(13.2,8.4),facecolor='white')
    ax=fig.add_axes([.085,.40,.87,.38])
    ax.axvspan(-4,0,color='#fff0ee',zorder=0)
    ax.axvspan(0,4,color='#fff9df',zorder=0)
    ax.axvspan(4,24,color='#eef7f2',zorder=0)
    ax.axvline(0,color='#ba2929',linewidth=1.3,linestyle='--')
    ax.axvline(4,color='#8e9875',linewidth=1.2,linestyle='--')
    handles=[]
    for delay,color,marker,size in zip(delays,colors,markers,[210,145,90,45]):
        selected=sorted((r for r in data if r['combination_mux_delay_assumed_ns']==delay),key=lambda r:r['d1_ns'])
        # All shared-zero observations remain at their exact coordinate.
        ax.scatter([r['d1_ns'] for r in selected],[r['observed_error_paths'] for r in selected],
                   s=size,c=color,marker=marker,edgecolors='white',linewidths=.8,zorder=4)
        handles.append(Line2D([],[],linestyle='none',marker=marker,color=color,markersize=8,
                              label=f'{delay:g} ns / 组合MUX'))
    ax.annotate('79 / 79',(-2,79),xytext=(15,-2),textcoords='offset points',weight='bold',color=colors[0])
    ax.annotate('52 / 79',(-2,52),xytext=(15,-2),textcoords='offset points',weight='bold',color=colors[1])
    ax.annotate('0 / 79（0.5、1 ns）',(-2,0),xytext=(15,13),textcoords='offset points',color='#424b60')
    ax.annotate('四种组合延迟均为 0 / 79',(22,0),xytext=(-12,20),ha='right',textcoords='offset points',weight='bold',color='#285d44')
    ax.text(-2,88,'有效透明重叠',ha='center',fontsize=10,color='#a34037')
    ax.text(2,88,'不足4 ns目标',ha='center',fontsize=9,color='#8d742e')
    ax.text(13,88,'达到4 ns间隔目标的区域',ha='center',fontsize=10,color='#397153')
    ax.text(12,45,'现有数据只有 −2 ns、22 ns 两组间隔\n中间区间未开展逐路径XSIM扫描\n图中不插值、不画预测错误曲线',
            ha='center',va='center',fontsize=12,color='#576471',linespacing=1.7,
            bbox=dict(boxstyle='round,pad=.8',facecolor='white',edgecolor='#d7dfe3'))
    ax.set(xlim=(-4,24),ylim=(-7,95),xticks=[-2,0,4,8,12,16,20,22],yticks=[0,20,40,52,60,79],
           xlabel='有效叶端非重叠时间 D1 = D2（ns）',ylabel='出现目的Q错误的短路径数（共79条）')
    ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('有效非重叠时间 D1/D2 与 79 条 CPU 短路径错误数量',fontsize=20,y=.965,weight='bold')
    fig.text(.5,.905,'TAP16 · 冻结477-MUX组合网络 · 每次仅源/目的两位使用活动双MUX存储',ha='center',fontsize=12,color='#52606d')
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.878),ncol=4,frameon=False,fontsize=10.5)
    table_ax=fig.add_axes([.13,.145,.78,.18]);table_ax.axis('off')
    cells=[]
    for delay in delays:
        a=next(r for r in data if r['d1_ns']==-2 and r['combination_mux_delay_assumed_ns']==delay)
        b=next(r for r in data if r['d1_ns']==22 and r['combination_mux_delay_assumed_ns']==delay)
        cells.append([f'{delay:g} ns / MUX',f'{a["observed_error_paths"]} / 79',f'{b["observed_error_paths"]} / 79'])
    table=table_ax.table(cellText=cells,colLabels=['组合延迟假设','D1 = D2 = −2 ns','D1 = D2 = 22 ns'],loc='center',cellLoc='center')
    table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,1.5)
    for (row,col),cell in table.get_celld().items():
        cell.set_edgecolor('#d8e0e5')
        if row==0:cell.set_facecolor('#eaf0f4');cell.set_text_props(weight='bold')
        elif col==0:cell.set_text_props(color=colors[row-1])
    fig.text(.085,.075,'来源：deep_review_r4/cone_results.csv，632次局部XSIM；错误按目的Q与预期值不一致统计。',fontsize=10,color='#52606d')
    fig.text(.085,.043,'范围：D1/D2同步变化，错误针对上升交接；假设延迟、逐路径不利叶端配对。0错误不代表实体时序签核。',fontsize=10,color='#52606d')
    for ext in ('png','svg'):
        fig.savefig(output/f'margin_error_relation.{ext}',dpi=200,facecolor='white')
    plt.close(fig)
    metadata=dict(status='VERIFIED_PLOT_OF_EXISTING_DIGITAL_OBSERVATIONS',source_records=632,
                  points=8,unique_margin_configurations=2,interpolation=False,new_simulation=False,
                  physical_signoff='NOT_VERIFIED',margin_qualification='D1 and D2 covary; errors test rising-handoff paths only',
                  inputs={str(p.relative_to(ROOT)):sha(p) for p in [raw,SUMMARY/'root_leaf_decomposition.csv',ROOT/tb]},
                  plot_script_sha256=sha(Path(__file__)),
                  outputs={p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()})
    (output/'plot_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(f'PLOT_VERIFIED: 632 records -> 8 points, no interpolation; {output}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=SUMMARY/'margin_error_relation')
    generate(p.parse_args().output)
