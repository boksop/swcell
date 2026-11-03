"""Independent numeric/encoding oracles for the M20-300 software prototype.

No test uses game algorithms, FPGA hardware, generated expected RTL state, or
the implementation's opcode tables as its golden model.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from m20 import AssemblyError, IllegalInstruction, Machine, assemble, decode, encode


def legal_by_bit_contract(word):
    """Independent masks from the documented word fields, not decode()."""
    top = word >> 12
    if 0 <= top <= 6:
        return (word & 0x0FF0) == 0
    if top == 7:
        return word in (0x7000, 0x7100, 0x7200)
    if top == 8:
        return ((word >> 8) & 15) <= 9
    if top == 9:
        return ((word >> 8) & 15) <= 9 and (word & 255) == 0
    if top == 10:
        return ((word & 0xFFF0) in (0xA000, 0xA100) or
                word in (0xA200, 0xA300, 0xA400, 0xA500, 0xA600))
    if top in (11, 12, 13):
        return True
    if top == 14:
        return word in (0xE000, 0xE100, 0xE200)
    return word in (0xF000, 0xF100)


def arithmetic_oracle(operation, a, b, carry):
    """Unbounded integer arithmetic defines result, carry/no-borrow and Z."""
    if operation in ("ADD", "ADC"):
        value = a + b + (carry if operation == "ADC" else 0)
        expected_c = int(value > 15)
    else:
        value = a - b - ((1 - carry) if operation == "SBC" else 0)
        expected_c = int(value >= 0)
    result = value % 16
    return a if operation == "CMP" else result, int(result == 0), expected_c


class M20EncodingTests(unittest.TestCase):
    def test_all_65536_words_against_independent_reserved_bit_rules(self):
        accepted = 0
        for word in range(65536):
            expected = legal_by_bit_contract(word)
            try:
                instruction = decode(word)
            except IllegalInstruction:
                self.assertFalse(expected, f"legal word rejected: {word:04X}")
            else:
                self.assertTrue(expected, f"reserved word accepted: {word:04X}")
                accepted += 1
                # Roundtrip is additional consistency, not the legality oracle.
                self.assertEqual(encode(instruction.mnemonic, instruction.operand,
                                        indirect=instruction.indirect), word)
        self.assertEqual(accepted, 15015)
        self.assertEqual(65536 - accepted, 50521)

    def test_every_reserved_word_traps_without_architectural_side_effects(self):
        for word in range(65536):
            if legal_by_bit_contract(word):
                continue
            cpu = Machine([word], ram={0x45: 7}, trace=False)
            cpu.a, cpu.ar, cpu.z, cpu.c, cpu.gpo = 9, 0x45, 0, 1, 6
            previous = (cpu.registers, tuple(cpu.ram))
            event = cpu.step()
            self.assertEqual((cpu.registers, tuple(cpu.ram)), previous, f"word {word:04X}")
            self.assertEqual((cpu.status, cpu.retired, cpu.cycles, cpu.total_cycles,
                              cpu.rom_reads, cpu.ram_reads, cpu.ram_writes, cpu.gpio_writes),
                             ("TRAP", 0, 2, 3, 1, 0, 0, 0))
            self.assertEqual((event["event"], event["retired"], event["ram_transaction"]),
                             ("TRAP", False, None))

    def test_input_ranges_are_rejected_without_truncation(self):
        for value in (-1, 65536, True):
            with self.assertRaises(IllegalInstruction): decode(value)
        for name, value in (("LDI", 16), ("ARH", -1), ("LD", 256), ("JMP", 4096)):
            with self.assertRaises(IllegalInstruction): encode(name, value)
        for args in ([65536], [True]):
            with self.assertRaises(ValueError): Machine(args)
        with self.assertRaises(ValueError): Machine([0] * 4097)
        with self.assertRaises(ValueError): Machine([0], ram=[0] * 255)
        with self.assertRaises(ValueError): Machine([0], ram={1: 16})
        with self.assertRaises(ValueError): Machine([0], keys=64)


class M20ExecutionTests(unittest.TestCase):
    def test_exhaustive_arithmetic_immediate_direct_and_indirect(self):
        # Raw numeric opcodes are independent of encode()/implementation tables.
        modes = [
            ("ADD", 0x1000, 0x8200, 0x9200),
            ("ADC", 0x2000, 0x8300, 0x9300),
            ("SUB", 0x3000, 0x8400, 0x9400),
            ("SBC", 0x4000, 0x8500, 0x9500),
            ("CMP", None,   0x8600, 0x9600),
        ]
        for operation, immediate, direct, indirect in modes:
            for a in range(16):
                for b in range(16):
                    for carry in range(2):
                        expected = arithmetic_oracle(operation, a, b, carry)
                        for word, address in [(direct | 0xA5, 0xA5), (indirect, 0xA5)]:
                            cpu = Machine([word], ram={address: b}, trace=False)
                            cpu.a, cpu.ar, cpu.c, cpu.z = a, address, carry, 1
                            cpu.step()
                            self.assertEqual((cpu.a, cpu.z, cpu.c), expected,
                                             (operation, word, a, b, carry))
                            self.assertEqual((cpu.cycles, cpu.ram_reads, cpu.ram_writes), (5, 1, 0))
                        if immediate is not None:
                            cpu = Machine([immediate | b], trace=False)
                            cpu.a, cpu.c, cpu.z = a, carry, 1
                            cpu.step()
                            self.assertEqual((cpu.a, cpu.z, cpu.c), expected)
                            self.assertEqual((cpu.cycles, cpu.ram_reads), (2, 0))

    def test_exhaustive_logic_load_and_shift_flags(self):
        operations = [
            (lambda a,b: a & b, 0x5000, 0x8700, 0x9700),
            (lambda a,b: a ^ b, 0x6000, 0x8800, 0x9800),
            (lambda a,b: a | b, None,   0x8900, 0x9900),
        ]
        for function, immediate, direct, indirect in operations:
            for a in range(16):
                for b in range(16):
                    for carry in (0, 1):
                        expected = function(a, b)
                        words = [direct | 0x23, indirect]
                        if immediate is not None: words.append(immediate | b)
                        for word in words:
                            cpu = Machine([word], ram={0x23: b}, trace=False)
                            cpu.a, cpu.ar, cpu.c, cpu.z = a, 0x23, carry, 1
                            cpu.step()
                            self.assertEqual((cpu.a,cpu.z,cpu.c), (expected,int(expected==0),carry))
        for a in range(16):
            for carry in (0, 1):
                for z in (0, 1):
                    for word, expected, expected_c in [
                        (0x7000, (2*a) % 16, a // 8),
                        (0x7100, a // 2, a % 2),
                        (0x7200, 15-a, carry),
                    ]:
                        cpu = Machine([word], trace=False);cpu.a,cpu.c,cpu.z=a,carry,z
                        cpu.step()
                        self.assertEqual((cpu.a,cpu.z,cpu.c), (expected,int(expected==0),expected_c))
                    for word in (a, 0x8023, 0x9000):
                        cpu = Machine([word], ram={0x23:a}, trace=False)
                        cpu.a,cpu.ar,cpu.c,cpu.z=15-a,0x23,carry,z;cpu.step()
                        self.assertEqual((cpu.a,cpu.z,cpu.c), (a,int(a==0),carry))

    def test_all_256_addresses_direct_and_indirect_read_write(self):
        original = [(i ^ (i >> 4)) & 15 for i in range(256)]
        for address in range(256):
            for indirect in (False, True):
                load = 0x9000 if indirect else 0x8000 | address
                cpu = Machine([load], ram=original, trace=False)
                cpu.ar=address;event=cpu.step()
                self.assertEqual((cpu.a,cpu.ram_reads,cpu.ram_writes,cpu.cycles),
                                 (original[address],1,0,5))
                self.assertEqual(event["ram_transaction"]["address"],address)
                self.assertEqual(cpu.ram,original)
                store = 0x9100 if indirect else 0x8100 | address
                cpu = Machine([store], ram=original, trace=False)
                cpu.a,cpu.ar,cpu.z,cpu.c=15-original[address],address,address&1,(address>>1)&1
                before_flags=cpu.z,cpu.c;cpu.step()
                expected=original.copy();expected[address]=15-original[address]
                self.assertEqual(cpu.ram,expected)
                self.assertEqual((cpu.z,cpu.c),before_flags)
                self.assertEqual((cpu.ram_reads,cpu.ram_writes,cpu.cycles),(0,1,5))

    def test_ar_controls_preserve_flags_and_address_wrap(self):
        for ar in range(256):
            for c in (0,1):
                for z in (0,1):
                    for value in range(16):
                        for word,new_ar in ((0xA000|value,(ar&0xF0)|value),
                                           (0xA100|value,(ar&15)|(value<<4)),
                                           (0xA200,(ar&0xF0)|value),
                                           (0xA300,(ar&15)|(value<<4))):
                            cpu=Machine([word],trace=False);cpu.ar,cpu.a,cpu.c,cpu.z=ar,value,c,z
                            cpu.step();self.assertEqual((cpu.ar,cpu.a,cpu.c,cpu.z,cpu.cycles),
                                                       (new_ar,value,c,z,2))
                    for word,new_a in ((0xA400,ar&15),(0xA500,ar>>4)):
                        cpu=Machine([word],trace=False);cpu.ar,cpu.a,cpu.c,cpu.z=ar,7,c,z
                        cpu.step();self.assertEqual((cpu.ar,cpu.a,cpu.c,cpu.z),(ar,new_a,c,z))
                    cpu=Machine([0xA600],trace=False);cpu.ar,cpu.a,cpu.c,cpu.z=ar,7,c,z
                    cpu.step();self.assertEqual((cpu.ar,cpu.a,cpu.c,cpu.z),((ar+1)%256,7,c,z))

    def test_all_keys_io_flags_and_gpio_write_counts(self):
        for keys in range(64):
            for c in (0,1):
                for z in (0,1):
                    for word,value in ((0xE000,keys&15),(0xE100,keys>>4)):
                        cpu=Machine([word],keys=keys,trace=False);cpu.c,cpu.z=c,z
                        event=cpu.step()
                        self.assertEqual((cpu.a,cpu.c,cpu.z,cpu.gpio_writes),(value,c,z,0))
                        self.assertEqual(event["input"],value)
        for a in range(16):
            for c in (0,1):
                for z in (0,1):
                    cpu=Machine([0xE200],trace=False);cpu.a,cpu.c,cpu.z=a,c,z
                    event=cpu.step()
                    self.assertEqual((cpu.a,cpu.gpo,cpu.c,cpu.z,cpu.gpio_writes),(a,a,c,z,1))
                    self.assertEqual(event["gpio"],a)

    def test_absolute_branches_pc_fff_wrap_and_flags(self):
        for opcode in (0xB000,0xC000,0xD000):
            for pc in (0,4095):
                for c in (0,1):
                    for z in (0,1):
                        words=[0xFFFF]*4096;words[pc]=opcode|0xABC
                        cpu=Machine(words,pc=pc,trace=False);cpu.c,cpu.z=c,z
                        event=cpu.step()
                        taken=(opcode==0xB000 or opcode==0xC000 and z or opcode==0xD000 and c)
                        self.assertEqual(cpu.pc,0xABC if taken else (pc+1)%4096)
                        self.assertEqual((cpu.c,cpu.z,cpu.cycles),(c,z,2))
                        self.assertEqual(event['pc'],pc)
        words=[0xF100]+[0xFFFF]*4094+[0xF000]
        cpu=Machine(words,pc=4095);cpu.step();self.assertEqual(cpu.pc,0)
        cpu.step();self.assertEqual((cpu.pc,cpu.retired,cpu.cycles,cpu.total_cycles),(1,2,4,5))

    def test_halt_fault_reset_and_instruction_limit_are_distinct(self):
        cpu=Machine([0xF100],ram={0x44:13})
        cpu.run(max_instructions=10)
        self.assertEqual((cpu.status,cpu.retired,cpu.cycles,cpu.reset_cycles,cpu.total_cycles),
                         ('HALTED',1,2,1,3))
        self.assertIsNone(cpu.step());self.assertEqual(len(cpu.trace),1)
        cpu.reset();self.assertEqual(cpu.ram[0x44],13)
        self.assertEqual((cpu.a,cpu.ar,cpu.z,cpu.c,cpu.gpo,cpu.retired,cpu.cycles,cpu.total_cycles),
                         (0,0,1,0,8,0,0,1))
        cpu=Machine([0xF000]);cpu.run(max_instructions=5)
        self.assertEqual((cpu.status,cpu.reason,cpu.retired,cpu.cycles,cpu.rom_reads),
                         ('FAULT','UNMAPPED_ROM',1,4,2))
        self.assertIsNone(cpu.step())
        loop=Machine([0xB000]);summary=loop.run(max_instructions=7)
        self.assertEqual((summary['status'],summary['stop_reason'],loop.retired,loop.cycles),
                         ('RUNNING','INSTRUCTION_LIMIT',7,14))
        breakpoint=Machine([0xF000,0xF100]);s=breakpoint.run(max_instructions=1,stop_pc=1)
        self.assertEqual((s['status'],s['stop_reason'],s['retired']),('RUNNING','BREAKPOINT',1))

    def test_exact_mixed_cycles_and_trace_transactions(self):
        # LDI, ST direct, LD indirect, ADD direct, OUT, NOP, HALT.
        cpu=Machine([0x0003,0x8120,0x9000,0x8220,0xE200,0xF000,0xF100])
        cpu.ar=0x20;s=cpu.run()
        self.assertEqual((s['retired'],s['ram_reads'],s['ram_writes'],s['gpio_writes']), (7,2,1,1))
        self.assertEqual((s['cycles'],s['total_cycles'],s['rom_reads']),(23,24,7))
        self.assertEqual(sum(e['cycles'] for e in cpu.trace),23)
        self.assertEqual([e['pc'] for e in cpu.trace],list(range(7)))
        self.assertEqual([e['sequence'] for e in cpu.trace],list(range(1,8)))
        self.assertEqual(cpu.trace[1]['ram_transaction']['kind'],'WRITE')
        self.assertEqual(cpu.trace[2]['ram_transaction']['kind'],'READ')
        quiet=Machine([0xF100],trace=False);event=quiet.step()
        self.assertTrue(event['retired']);self.assertEqual(quiet.trace,[])


class M20AssemblerAndCLITests(unittest.TestCase):
    def test_forward_labels_constants_expressions_and_numeric_encoding(self):
        program=assemble('''
            # Whole-line comment
            .equ VALUE, (8 // 2) | (1 << 3)
            .equ TARGET, finish
            start: LDI VALUE ; inline comment
            JMP TARGET
            .word 0xFFFF
            finish: HALT
        ''')
        self.assertEqual(program.words,(0x000C,0xB003,0xFFFF,0xF100))
        self.assertEqual(program.symbols['finish'],3)
        self.assertEqual(program.binary,b'\x0c\x00\x03\xb0\xff\xff\x00\xf1')
        self.assertEqual(program.memh,'000C\nB003\nFFFF\nF100\n')
        self.assertEqual(assemble('LD [0x20]\nST [AR]\nMOVA ARH\nSHR A').words,
                         (0x8020,0x9100,0xA500,0x7100))

    def test_org_holes_high_water_and_explicit_invalid_word(self):
        program=assemble('JMP finish\n.org 4\nfinish:HALT')
        self.assertEqual(program.words,(0xB004,0xFFFF,0xFFFF,0xFFFF,0xF100))
        self.assertEqual(program.used_words,2)
        self.assertEqual(set(program.source_map),{0,4})
        self.assertEqual(len(assemble('.org 4095\nHALT').words),4096)
        cpu=Machine(assemble('.word 65535').words);cpu.step()
        self.assertEqual((cpu.status,cpu.retired),('TRAP',0))

    def test_invalid_assembly_rejected_instead_of_truncated_or_evaluated(self):
        for source in (
            'LDI 16','LDI -1','LD 256','JMP 4096','ARH 16','.word 65536','.word -1',
            '.org -1\nNOP','.org 4096\nNOP','.org 4095\nNOP\nNOP',
            'a:NOP\na:HALT','.equ A,1\nA:NOP',
            '.org 0\nNOP\n.org 0\nHALT','.equ A,B\n.equ B,A\nNOP','JMP missing',
            'CALL 0','RET','DECAR','SHR B','MOVA OTHER','LD [AR+1]',
            'LDI __import__("os")','LDI (1).__class__','LDI [1][0]',
            'LDI 1 << 64','LDI 1 // 0','LDI 2 ** 3',
        ):
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):assemble(source)

    def test_cli_binary_memh_roundtrip_and_invalid_images(self):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]),
                 PYTHONDONTWRITEBYTECODE='1')
        def cli(*args):
            return subprocess.run([sys.executable,'-B','-m','m20',*map(str,args)],
                                  env=env,text=True,capture_output=True,timeout=30)
        with tempfile.TemporaryDirectory(prefix='m20_cli_test_') as name:
            tmp=Path(name);source=tmp/'smoke.asm';source.write_text('LDI 9\nST 0x20\nLDI 1\nADD 0x20\nHALT\n')
            image=tmp/'image';result=cli('assemble',source,'--output-dir',image)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual((image/'smoke.bin').read_bytes(),b'\x09\x00\x20\x81\x01\x00\x20\x82\x00\xf1')
            stat=json.loads((image/'smoke.assembly.json').read_text())
            self.assertEqual((stat['image_words'],stat['emitted_words'],stat['image_bytes']),(5,5,10))
            for ext in ('bin','memh'):
                summary=tmp/(ext+'.json');trace=tmp/(ext+'.jsonl')
                result=cli('run',image/('smoke.'+ext),'--summary',summary,'--trace',trace)
                self.assertEqual(result.returncode,0,result.stderr)
                values=json.loads(summary.read_text())
                self.assertEqual((values['status'],values['retired'],values['cycles'],values['total_cycles']),
                                 ('HALTED',5,16,17))
                self.assertEqual(values['registers']['a'],10)
                records=[json.loads(line) for line in trace.read_text().splitlines()]
                self.assertEqual(len(records),5)
            for filename,data in [('odd.bin',b'\0'),('long.bin',b'\0\0'*4097),
                                  ('wide.memh',b'10000\n'),('short.memh',b'001\n'),
                                  ('bad.memh',b'XYZ0\n'),('long.memh',b'F000\n'*4097)]:
                path=tmp/filename;path.write_bytes(data)
                result=cli('run',path)
                self.assertEqual(result.returncode,1,(filename,result.stdout,result.stderr))
            trap=tmp/'trap.memh';trap.write_text('FFFF\n')
            self.assertEqual(cli('run',trap).returncode,2)
            loop=tmp/'loop.memh';loop.write_text('B000\n')
            self.assertEqual(cli('run',loop,'--max-instructions','3').returncode,2)


if __name__=='__main__':
    unittest.main()
