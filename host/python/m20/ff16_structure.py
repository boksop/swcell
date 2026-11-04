"""Independent literal-netlist audit/export of the fixed20 MUX feed-forward model.

This tool does not generate RTL, run a timing model, or count FPGA LUTs. It reads
literal SV primitive instances, rejects unaccounted logic/cycles/multiple drivers,
and models the selected solder link separately from the always-present16 chain.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
FOLDER = ROOT / 'rtl/m20/v24_ff16'
TAPS = (4, 8, 12, 16)


class StructureError(ValueError):
    pass


def require(value, message):
    if not value:
        raise StructureError(message)


def clean(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'^\s*`(?:timescale|default_nettype)[^\n]*', '', text, flags=re.M)
    return text


def normalize(text):
    return re.sub(r'\s+', '', text)


def expected_cells():
    result = []
    for i in range(1, 17):
        result.append(dict(instance=f'u_delay{i:02d}', s="1'b0", i0=f'chain[{i-1}]',
                           i1="1'b0", y=f'chain[{i}]', role='fixed_delay_chain'))
    result.extend([
        dict(instance='u_decode_h', s='clk_ref', i0='delayed_ref', i1="1'b1", y='h_raw', role='or_decode'),
        dict(instance='u_decode_s', s='clk_ref', i0="1'b0", i1='delayed_ref', y='s_raw', role='and_decode'),
        dict(instance='u_hold_h', s='safe_hold', i0='h_raw', i1="1'b1", y='master_hold', role='safe_hold'),
        dict(instance='u_hold_s', s='safe_hold', i0='s_raw', i1="1'b0", y='slave_open', role='safe_hold'),
    ])
    return result


def audit(folder=FOLDER, tap_stages=8):
    require(type(tap_stages) is int and tap_stages in TAPS, 'illegal static tap configuration')
    folder = Path(folder)
    primitive = (folder / 'swc_ff16_mux157.sv').read_text()
    expected_primitive = 'module swc_ff16_mux157(input wire s,i0,i1,output wire y); assign y=s?i1:i0; endmodule'
    require(normalize(clean(primitive)) == normalize(expected_primitive), 'primitive truth table or extra logic changed')
    path = folder / 'swc_ff16_phasegen.sv'
    raw = path.read_text()
    text = clean(raw)
    require('`default_nettype none' in raw and '`default_nettype none' in primitive, 'implicit-net protection missing')
    require(not re.search(r'\b(?:reg|logic|always|always_ff|always_comb|always_latch)\b', text), 'state/behavioral logic in structural model')
    header = '''module swc_ff16_phasegen #(parameter integer TAP_STAGES=8)
      (input wire clk_ref,safe_hold,output wire master_hold,slave_open,delayed_ref,
       output wire tap4,tap8,tap12,tap16,h_raw,s_raw);'''
    normalized = normalize(text)
    require(normalized.startswith(normalize(header)), 'top name/ports/parameters changed')
    body = normalized[len(normalize(header)):]
    pattern = (r'swc_ff16_mux157(\w+)\(\.s\(([^()]+)\),\.i0\(([^()]+)\),'
               r'\.i1\(([^()]+)\),\.y\(([^()]+)\)\);')
    cells = [dict(instance=m[1], s=m[2], i0=m[3], i1=m[4], y=m[5])
             for m in re.finditer(pattern, body)]
    expected = [{k: v for k, v in row.items() if k != 'role'} for row in expected_cells()]
    require(cells == expected, 'literal20 cell count, pins or physical16 chain changed')
    require(len(cells) == 20 and len({v['instance'] for v in cells}) == 20, 'duplicate or wrong physical count')
    remainder = re.sub(pattern, '', body)
    allowed = '''wire [16:0] chain; assign chain[0]=clk_ref;
      assign tap4=chain[4]; assign tap8=chain[8]; assign tap12=chain[12]; assign tap16=chain[16];
      generate
       if(TAP_STAGES==4)begin:g_tap4 assign delayed_ref=tap4;
       end else if(TAP_STAGES==8)begin:g_tap8 assign delayed_ref=tap8;
       end else if(TAP_STAGES==12)begin:g_tap12 assign delayed_ref=tap12;
       end else if(TAP_STAGES==16)begin:g_tap16 assign delayed_ref=tap16;
       end else begin:g_invalid assign delayed_ref=1'bx;
        initial $fatal(1,"TAP_STAGES must be 4,8,12,16"); end
      endgenerate endmodule'''
    require(remainder == normalize(allowed), 'extra logic/driver or dynamic tap selector')
    # A separate traversal validates all physical outputs, including unselected tail.
    drivers = {v['y']: v for v in cells}
    require(len(drivers) == 20, 'multiple output drivers')
    aliases = {'chain[0]': 'clk_ref', 'delayed_ref': f'chain[{tap_stages}]'}
    seen, visiting = set(), set()
    def visit(signal):
        signal = aliases.get(signal, signal)
        if signal in ('clk_ref', 'safe_hold', "1'b0", "1'b1"):
            return
        require(signal in drivers, 'undriven net ' + signal)
        require(signal not in visiting, 'combinational cycle ' + signal)
        if signal in seen:
            return
        visiting.add(signal)
        for pin in ('s', 'i0', 'i1'):
            visit(drivers[signal][pin])
        visiting.remove(signal)
        seen.add(signal)
    for signal in drivers:
        visit(signal)
    require(len(seen) == 20, 'not every physical cell audited')
    return dict(status='VERIFIED',verification='static_structure_only_not_deadtime',
                physical_mux_count=20,physical_delay_cells=16,decoder_mux_count=2,
                safe_hold_mux_count=2,selected_tap=tap_stages,effective_delay_cells=tap_stages,
                unselected_tail_cells=16-tap_stages,generator_state_bits=0,feedback_cycles=0,
                extra_tap_mux=0,cpu_mux_count_separate=543,total_excluding_buffers=563,
                selected_tap_immediate_next_stage_inputs=int(tap_stages<16),
                selected_tap_decoder_inputs=2,
                selected_tap_total_direct_mux_input_loads=2+int(tap_stages<16),
                load_note='Only immediate next-stage I0 is directly parallel; all later cells are not lumped in parallel. Test-pad/wiring/probe loads remain unknown.',
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                primitive_sha256=hashlib.sha256(primitive.encode()).hexdigest())


def evaluate(c, cd, hold):
    """Independent Boolean truth table, not a delay simulation."""
    h = bool(c or cd)
    s = bool(c and cd)
    return (True, False) if hold else (h, s)


def reference_review():
    """Bind the retained proposal to its original saved fingerprint and pin mapping."""
    path=ROOT/'rtl/m20/clock_proposals/swc157_phase_feedforward.sv'
    raw=path.read_text();text=normalize(clean(raw))
    expected={
        'u_decode_h': 'swc_phase_mux157decode_h(.s(clk_ref),.i0(delayed_ref),.i1(1\'b1),.y(h_raw));',
        'u_decode_s': 'swc_phase_mux157decode_s(.s(clk_ref),.i0(1\'b0),.i1(delayed_ref),.y(s_raw));',
        'u_hold_h': 'swc_phase_mux157hold_h(.s(safe_hold),.i0(h_raw),.i1(1\'b1),.y(master_hold));',
        'u_hold_s': 'swc_phase_mux157hold_s(.s(safe_hold),.i0(s_raw),.i1(1\'b0),.y(slave_open));',
    }
    require('assigny=s?i1:i0;' in text,'retained proposal truth table changed')
    require(all(value in text for value in expected.values()),'retained proposal decode/hold polarity changed')
    require('swc_phase_mux157buffer157(.s(1\'b0),.i0(delay_tap[i]),.i1(1\'b0),.y(delay_tap[i+1]));' in text,'retained proposal chain direction changed')
    saved=json.loads((ROOT/'docs/m20/compact_clock/proposal.json').read_text())
    actual=hashlib.sha256(raw.encode()).hexdigest()
    require(saved['source_sha256']==actual,'retained proposal no longer matches original saved reference')
    return dict(path=str(path.relative_to(ROOT)),status='VERIFIED_STATIC_REFERENCE',source_sha256=actual,
                original_fingerprint_matches=True,conclusion='Truth table, chain direction, OR/AND/PARK pins reviewed; no correction required. Variable-length reference preserved unchanged.')


def export(output):
    output = Path(output)
    require(not output.exists(), 'refusing existing evidence output')
    output.mkdir(parents=True)
    reports = [audit(tap_stages=t) for t in TAPS]
    cells = expected_cells()
    # NC7SZ157P6X SC-88 pin mapping from the frozen onsemi Rev7 source record.
    connection_rows=[dict(**v,pin_s=6,pin_i0=3,pin_i1=1,pin_y=4,pin_vcc=5,pin_gnd=2,vcc_net='3V3',gnd_net='GND') for v in cells]
    with (output / 'mux_connections.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(connection_rows[0]))
        writer.writeheader(); writer.writerows(connection_rows)
    assembly = [dict(configuration=f'TAP{t}', resistor=f'R_TAP{p}', source=f'tap{p}',
                     destination='delayed_ref', fitted=int(t==p), connection='STATIC_0_OHM_NO_LOGIC_MUX')
                for t in TAPS for p in TAPS]
    with (output / 'tap_assembly.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(assembly[0])); writer.writeheader();writer.writerows(assembly)
    loads = []
    for t in TAPS:
        for stage in range(1,17):
            loads.append(dict(configuration=f'TAP{t}', stage=stage, continuation_inputs=int(stage<16),
                              decoder_inputs=2*int(stage==t), direct_mux_input_loads=int(stage<16)+2*int(stage==t),
                              test_pad=bool(stage in TAPS), pad_wire_probe_capacitance_pf='UNKNOWN',
                              current_load_model='INPUT_COUNTS_ONLY_NOT_PF_NOT_TIMING'))
    with (output / 'tap_loads.csv').open('w', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(loads[0]));writer.writeheader();writer.writerows(loads)
    signals = [
        dict(signal='clk_ref',role='single selected root clock',fpga_relationship='FPGA source or observed external root; static0R source selection',default='defined clean clock'),
        dict(signal='safe_hold',role='active high safety clamp',fpga_relationship='FPGA control output',default='HIGH before FPGA configuration; hardware bias TBD'),
    ]
    for t in TAPS:
        signals.append(dict(signal=f'tap{t}',role='delay-chain probe and optional selected link',fpga_relationship='optional observation only; loading must be counted',default='clock-derived'))
    for signal,role in [('delayed_ref','selected Cd'),('h_raw','unclamped Master decode'),('s_raw','unclamped Slave decode'),('master_hold','Master buffer-root output'),('slave_open','Slave buffer-root output')]:
        signals.append(dict(signal=signal,role=role,fpga_relationship='testpoint/observation as allocated; no invented pin',default='H=1/S=0 when safe_hold=1' if signal in ('master_hold','slave_open') else 'clock-derived'))
    with (output / 'signal_probes.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(signals[0]));writer.writeheader();writer.writerows(signals)
    (output / 'structure_audit.json').write_text(json.dumps(dict(status='VERIFIED',profiles=reports,
        reference_template_review=reference_review(),
        package_mapping_source='https://www.onsemi.com/download/data-sheet/pdf/nc7sz157-d.pdf Rev7 p2 SC-88',
        physical_fixed_count=20,zero_ohm_rule='exactly one link fitted per configuration; never tie tap outputs',
        external_buffers='not included',timing_model='NOT_RUN_BY_STRUCTURE_AUDIT',physical_signoff='NOT_VERIFIED'),indent=2)+'\n')
    print('FF16_STRUCTURE_VERIFIED physical20 effective4/8/12/16 state0 feedback0')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    try: export(args.output)
    except (OSError,ValueError) as exc:parser.exit(1,'FF16_STRUCTURE_FAILED: '+str(exc)+'\n')


if __name__=='__main__':main()
