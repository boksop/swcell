"""Execute real assembled words against separate mathematical game rules."""
from pathlib import Path
from contextlib import redirect_stdout
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from m20 import Machine, assemble
from m20.benchmarks import (programs, pong_cases, snake_cases, run_case,
                            boot_case, replay, drive, compare_ram, main as benchmark_main, ROOT)
from m20.game_reference import (get8, pong_initial, snake_initial,
    snake_fixture, snake_tick, snake_invariants)


class M20GameProgramsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.programs=programs()

    def test_pong_all_directed_keys_and_seeded_states(self):
        for label,ram,keys in pong_cases(128):
            with self.subTest(case=label):
                row,cpu,_=run_case('pong',self.programs['pong'],label,ram,keys)
                self.assertEqual(row['gpio_writes'],0)

    def test_snake_all_directed_keys_and_seeded_states(self):
        for label,ram,keys in snake_cases(128):
            with self.subTest(case=label):
                run_case('snake',self.programs['snake'],label,ram,keys)

    def test_boot_initializes_dirty_ram_by_machine_instructions(self):
        for name,program in self.programs.items():
            result=boot_case(name,program)
            self.assertGreater(result['ram_writes'],0)
        program=self.programs['snake']
        cpu=Machine(program.words,ram=[10]*256,trace=True)
        drive(cpu,program.symbols['tick_done'])
        writes={e['ram_transaction']['address'] for e in cpu.trace
                if e['ram_transaction'] and e['ram_transaction']['kind']=='WRITE'}
        self.assertEqual(writes,set(range(256)))

    def test_continuous_program_loops_without_host_ram_updates(self):
        for name,program in self.programs.items():
            result=replay(name,program,ticks=256)
            self.assertEqual(result['ticks'],256)
            self.assertEqual(result['host_RAM_writes_after_boot'],0)

    def test_food_search_63_is_a_reachable_connected_body_fixture(self):
        label,ram,keys=next(c for c in snake_cases(0) if c[0]=='food_search_63')
        self.assertEqual(len(snake_invariants(ram)),62)
        row,cpu,_=run_case('snake',self.programs['snake'],label,ram,keys)
        self.assertEqual(get8(cpu.ram,15),63)
        self.assertEqual(get8(cpu.ram,4),63)
        self.assertEqual(cpu.ram[7:9],[0,4])
        self.assertEqual(get8(cpu.ram,9),0)  # FF + growth -> 00

    def test_corrupt_bitmap_search_has_bounded_software_diagnostic(self):
        ram=snake_fixture([(2,3),(3,3),(4,3)],food=(5,3))
        ram[0xC0:0xE0]=[15]*32
        ram[0xCD]&=13  # food(5,3) temporarily clear; growth fills last bit
        program=self.programs['snake']
        cpu=Machine(program.words,ram=ram,pc=program.symbols['tick'],trace=False)
        drive(cpu,program.symbols['tick_done'],limit=20000)
        self.assertEqual((cpu.ram[11],cpu.ram[14],get8(cpu.ram,15)),(3,5,65))
        self.assertEqual(cpu.status,'RUNNING')  # software status, not CPU TRAP

    def test_growing_into_tail_is_rejected_even_for_invalid_food_fixture(self):
        ram=snake_fixture([(3,3),(3,4),(4,4),(4,3)],direction=3,food=(3,3))
        # Deliberately invalid food placement verifies the growth collision rule.
        program=self.programs['snake']
        cpu=Machine(program.words,ram=ram,pc=program.symbols['tick'],keys=4,trace=False)
        drive(cpu,program.symbols['tick_done'])
        self.assertEqual((cpu.ram[11],cpu.ram[14]),(1,2))
        self.assertEqual(cpu.ram[0x40:0xE0],ram[0x40:0xE0])

    def test_independent_oracle_rejects_mutated_input_instruction(self):
        for name,program in self.programs.items():
            words=list(program.words)
            words[program.symbols['tick']]=0xE100  # IN0 incorrectly changed to IN1
            initial=pong_initial() if name=='pong' else snake_initial()
            cpu=Machine(words,ram=initial,pc=program.symbols['tick'],keys=1,trace=False)
            drive(cpu,program.symbols['tick_done'])
            expected=__import__('m20.game_reference',fromlist=[name+'_tick'])
            expected=getattr(expected,name+'_tick')(initial,1)
            with self.assertRaises(AssertionError):compare_ram(name,cpu.ram,expected,'mutated')

    def test_software_bad_return_id_halts_instead_of_magic_return(self):
        program=self.programs['pong'];ram=pong_initial();ram[0xF0]=15;ram[0x20]=0
        cpu=Machine(program.words,ram=ram,pc=program.symbols['update_paddle'],trace=False)
        cpu.ar=4
        result=cpu.run(max_instructions=100)
        self.assertEqual(result['status'],'HALTED')
        self.assertNotIn('lr',cpu.registers)
        self.assertNotIn('b',cpu.registers)

    def test_exported_budgets_images_fingerprints_and_retire_traces_agree(self):
        # Exactly reaching a breakpoint at the instruction limit is successful.
        cpu=Machine(assemble('NOP').words,trace=False)
        self.assertEqual(drive(cpu,1,limit=1)['NOP'],1)
        self.assertEqual(drive(cpu,1,limit=0),{})
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(io.StringIO()):
            out=Path(temporary)
            self.assertEqual(benchmark_main(['--output',str(out),'--random-cases','0']),0)
            summary=json.loads((out/'summary.json').read_text())
            rows=list(csv.DictReader(io.StringIO((out/'case_metrics.csv').read_text())))
            self.assertEqual(len(rows),sum(p['cases'] for p in summary['programs'].values()))
            fixtures=[json.loads(line) for line in (out/'fixtures.jsonl').read_text().splitlines()]
            self.assertEqual(len(fixtures),len(rows))
            self.assertEqual(summary['status'],'PASS')
            for relative,digest in summary['source_fingerprints'].items():
                self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),digest)
            for name,program in self.programs.items():
                group=summary['programs'][name]
                binary=(out/name/f'{name}.bin').read_bytes()
                self.assertEqual(binary,program.binary)
                self.assertEqual(hashlib.sha256(binary).hexdigest(),group['binary_sha256'])
                self.assertEqual((out/name/f'{name}.memh').read_text(),program.memh)
                trace=[json.loads(line) for line in (out/name/'max_case_trace.jsonl').read_text().splitlines()]
                maximum=group['maximum_case_metrics']
                self.assertTrue(all(e['event']=='RETIRE' for e in trace))
                self.assertEqual(len(trace),maximum['retired'])
                self.assertEqual(sum(e['cycles'] for e in trace),maximum['cycles'])
                self.assertEqual(trace[-1]['cumulative_cycles'],maximum['cycles'])
                for kind,field in [('READ','ram_reads'),('WRITE','ram_writes')]:
                    count=sum(bool(e['ram_transaction'] and e['ram_transaction']['kind']==kind) for e in trace)
                    self.assertEqual(count,maximum[field])
            budget=list(csv.DictReader(io.StringIO((out/'clock_budget.csv').read_text())))
            self.assertEqual(len(budget),4*sum(len(p['selected_cases']) for p in summary['programs'].values()))
            for row in budget:
                self.assertEqual(row['clock_source'],'ASSUMED_NOT_MEASURED')
                hz=int(row['microclock_hz']);cycles=int(row['execution_cycles'])
                self.assertAlmostEqual(float(row['execution_seconds'])*hz,cycles)
                self.assertAlmostEqual(float(row['continuous_loop_seconds'])*hz,cycles+4)


if __name__=='__main__':unittest.main()
