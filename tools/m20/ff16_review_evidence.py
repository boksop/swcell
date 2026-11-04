#!/usr/bin/env python3
"""Preserve compact review summaries while indexing all actual raw artifacts."""
import argparse,csv,hashlib,json,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def save(p,r):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
def archive(run,dest):
 run=run.resolve();dest=dest.resolve()
 if dest.exists():raise ValueError('fresh output required')
 dest.mkdir(parents=True)
 for name in ('baseline_review.json','analysis_summary.json','root_leaf_decomposition.csv','safe_envelope.csv','frequency_envelope.csv','frequency_scan.csv','leaf_scan.csv','decode_hold_scan.csv','relative_decode_inputs.csv','safe_hold_release_budget.csv','buffer_comparison.csv','cone_verification.json','cone_provenance.json'):
  shutil.copyfile(run/name,dest/name)
 for p in run.glob('*.svg'):shutil.copyfile(p,dest/p.name)
 leaves=[r for r in rows(run/'leaf_events.csv') if r['tap']=='16' and r['case'] in ('nominal','fast_chain_sensitivity')]
 save(dest/'tap16_leaf_events.csv',leaves)
 scan=rows(run/'delay_scan.csv')
 for r in scan:
  del r['all16_rise_ns'];del r['all16_fall_ns']
 save(dest/'delay_scan_summary.csv',scan)
 vectors=json.loads((run/'cpu_witness_vectors.json').read_text());risks=rows(run/'cpu_short_paths.csv');actual=rows(run/'cone_results.csv');summary=[]
 for v in vectors:
  pathid=v['path_id'];r=next(r for r in risks if int(r['path_id'])==pathid and r['tap']=='16' and r['placement']=='adversarial_source0_dest32' and r['data_and_select_min_assumed_ns_per_cell']=='0.25')
  result={k:r[k] for k in ('path_id','source','destination','mux_layers','route','witness_case','witness_sequence','word','microstate','source_slave_open_ns','destination_master_close_ns','clock_pair_margin_ns')}
  result['conditions']='; '.join(v['conditions'])
  result['source_and_destination_pcb_assignment']='UNKNOWN_ADVERSARIAL_PAIRING_PER_EXPERIMENT'
  for delay in ('0.125','0.250','0.500','1.000'):
   hit=next(a for a in actual if int(a['path_id'])==pathid and a['chain_stage_ns']=='0.500' and a['cell_min_ns']==delay)
   result['xsim_error_at_cell_'+delay+'_ns']=int(hit['mismatch'])
  result['minimum_physical_path_ns']=None;summary.append(result)
 save(dest/'cpu79_summary.csv',summary)
 index=[]
 for p in sorted(run.rglob('*')):
  if p.is_file() and 'xsim.dir' not in p.parts and p.suffix in ('.csv','.json','.txt','.sv','.log','.vcd'):
   index.append(dict(path=str(p.relative_to(run)),bytes=p.stat().st_size,sha256=sha(p)))
 save(dest/'evidence_sha256.csv',index)
 srcpaths=['host/python/m20/ff16_review.py','config/m20/ff16_buffer_sources.json','tools/m20/ff16_review_xsim.py','tools/m20/ff16_review_evidence.py','sim/m20_ff16_review/tb_ff16_cpu_cones.sv','sim/m20_ff16_review/run_cones.tcl','sim/scripts/run_m20_ff16_review.sh','sim/m20_ff16/swc_ff16_timing.sv','rtl/m20/v21/generated/m20v21_cpu_core.netlist.json']
 (dest/'source_sha256.json').write_text(json.dumps({p:sha(ROOT/p) for p in srcpaths},indent=2)+'\n')
 (dest/'origin.json').write_text(json.dumps(dict(run=str(run),indexed_files=len(index),indexed_bytes=sum(v['bytes'] for v in index),cpu_full_regression='NOT_RUN',gate='RETAIN_20_DO_NOT_ADMIT_C_D_YET',physical_signoff='NOT_VERIFIED',old_AB_evidence='preserved under docs/m20/ff16_resources and small_r4'),indent=2)+'\n')
 bundle=run.with_name(run.name+'_evidence.tar.gz')
 if bundle.exists():raise ValueError('refusing bundle overwrite')
 with tarfile.open(bundle,'w:gz') as f:
  for v in index:f.add(run/v['path'],arcname='raw/'+v['path'],recursive=False)
  for p in sorted(dest.iterdir()):f.add(p,arcname='summary/'+p.name,recursive=False)
 (dest/'bundle.json').write_text(json.dumps(dict(path=str(bundle),bytes=bundle.stat().st_size,sha256=sha(bundle),uploaded=False),indent=2)+'\n')
 print('FF16_REVIEW_ARCHIVED',len(index),'raw files; no source or old evidence overwritten')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();archive(a.run,a.output)
