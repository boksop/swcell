#!/usr/bin/env python3
"""Capture a new read-only source/index checkpoint for a standalone regression."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def capture(output):
 output=Path(output)
 if output.exists():raise ValueError('refusing existing checkpoint')
 paths=set()
 for folder in ('rtl/m20','sim/m20_v23','sim/m20_ff16','sim/m20_ff16_review','docs/m20/ff16_resources','docs/m20/ff16_review_resources','software/m20_300','host/python/m20'):
  paths.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 paths.update([ROOT/'docs/m20/isa_v0_1.json',ROOT/'docs/reports/m20_phaseV2.3_20261103.md'])
 data=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           tag=subprocess.check_output(['git','rev-parse','m20-v2.3-two-phase-sim-verified^{}'],cwd=ROOT,text=True).strip(),
           index=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).decode(),
           protected={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)})
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(data,indent=2)+'\n')
 print('FFCD_CHECKPOINT_CREATED read_only=1 protected='+str(len(paths)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);capture(p.parse_args().output)
