#!/usr/bin/env python3
"""Derive FPGA storage binding without editing the frozen 477-node CPU network."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'host/python'))
from m20 import assemble
from m20.v21_build import construct


def generate(out):
    src = ROOT/'rtl/m20/v21/generated/m20v21_cpu_core.sv'
    text = src.read_text()
    spec = json.loads(src.with_suffix('.netlist.json').read_text())
    assert spec['ff_bits'] == 33 and spec['physical_mux_count'] == 477
    instances = re.findall(r'swc_mux157 (u_n\d+) \(([^;]+)\);', text)
    assert len(instances) == 477
    # Tap existing CPU decode nodes; never create a second instruction decoder
    # in the FPGA input frontend. Identical cached expressions add zero nodes.
    network,_,_=construct();before=len(network.nodes)
    word=[f'rom_data[{i}]' for i in range(16)]
    in0=network.AND(network.eq(word[12:16],14),network.eq(word[8:12],0))
    in1=network.AND(network.eq(word[12:16],14),network.eq(word[8:12],1))
    selected=network.OR(in0,in1)
    assert len(network.nodes)==before
    assert {selected,in1}<={n['id'] for n in spec['nodes']}
    blocks = re.findall(r'    always_ff @\(posedge clk\) begin\n        (\w+) <= ([^;]+);\n    end', text)
    assert len(blocks) == 7
    states = []
    replacement = ['    generate if (STORAGE_MODE == "FUNCTIONAL_STORAGE") begin : g_ff']
    for register, data in blocks:
        replacement.append(f'        always_ff @(posedge clk) if(commit_ce) {register} <= {data};')
    replacement.append('    end else begin : g_strict')
    for register, data in blocks:
        bits = data[1:-1].split(',') if data.startswith('{') else [data]
        for index, node in enumerate(reversed(bits)):
            q = f'{register}[{index}]' if len(bits)>1 else register
            states.append(dict(state=q, next_d=node, master=f'g_strict.u_bit{len(states)}.master', slave=f'g_strict.u_bit{len(states)}.slave'))
            replacement.append(f'        swc_v3_mux_storage u_bit{len(states)-1}(.d({node}),.master_hold(master_hold),.slave_open(slave_open),.q({q}));')
    assert len(states) == 33
    replacement.append('    end endgenerate')
    text = re.sub(r'    always_ff @\(posedge clk\) begin\n        \w+ <= [^;]+;\n    end\n', '', text)
    text = text.replace('endmodule', '\n'.join(replacement)+'\nendmodule')
    text = text.replace('module m20v21_cpu_core (', 'module m20v3_cpu_core #(parameter STORAGE_MODE="FUNCTIONAL_STORAGE") (\n    input wire commit_ce,master_hold,slave_open,\n    output wire debug_input_selected,debug_input_bank,')
    text = text.replace('endmodule',f'    assign debug_input_selected={selected};\n    assign debug_input_bank={in1};\nendmodule')
    text = text.replace('swc_mux157 ', 'swc_v3_mux157 ')
    # Verify complete node connectivity, not only instance count.
    after = re.findall(r'swc_v3_mux157 (u_n\d+) \(([^;]+)\);', text)
    assert after == instances
    out.mkdir(parents=True, exist_ok=True)
    (out/'m20v3_cpu_core.sv').write_text(text)
    manifest = dict(source=str(src.relative_to(ROOT)), source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                    netlist_sha256=hashlib.sha256(src.with_suffix('.netlist.json').read_bytes()).hexdigest(),
                    generated_sha256=hashlib.sha256(text.encode()).hexdigest(), combination_mux_count=477,
                    state_bits=33, strict_storage_mux_count=66, states=states,
                    nodes=[dict(instance=n, connection=c) for n,c in instances],
                    observed_cpu_nodes=dict(input_selected=selected,input_bank=in1))
    (out/'binding_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    games = {}
    for name in ('pong','snake'):
        asm = ROOT/f'software/m20_300/{name}.asm'
        game = assemble(asm.read_text(), str(asm))
        original = ROOT/f'software/m20_300/rom/{name}.memh'
        assert tuple(int(s,16) for s in original.read_text().split()) == game.words
        padded = game.memh + 'FFFF\n'*(4096-len(game.words))
        (out/f'{name}.memh').write_text(padded)
        games[name]=dict(words=len(game.words),tick=game.symbols['tick'],tick_done=game.symbols['tick_done'],original_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
    (out/'games.json').write_text(json.dumps(games,indent=2)+'\n')
    (out/'m20_v3_game_pkg.sv').write_text('package m20_v3_game_pkg;\n'+''.join(f" localparam [11:0] {n.upper()}_DONE=12'd{g['tick_done']};\n" for n,g in games.items())+'endpackage\n')
    print('M20_V3_BINDING_PASS combination=477 states=33 strict=543',json.dumps(games))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    generate(parser.parse_args().output)
