"""Frozen ISA rules are checked against independent bit and flag contracts.

The JSON is declaration-only: neither Machine arithmetic nor an RTL ALU is
used to generate the legal-word oracle or expected flag write controls.
"""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "host/python"))
from m20 import Machine, assemble, decode, IllegalInstruction
from m20.isa import ISA_VERSION, LEGACY_ISA_VERSION


def independent_legal_word(word):
    """Literal field rules from the frozen contract, independent of decode()."""
    major, sub, low8 = word >> 12, (word >> 8) & 15, word & 255
    if major < 7:
        return (word & 0x0FF0) == 0
    if major == 7:
        return sub < 3 and low8 == 0
    if major == 8:
        return sub < 10
    if major == 9:
        return sub < 10 and low8 == 0
    if major == 10:
        return (sub in (0, 1) and (low8 & 0xF0) == 0) or (
            2 <= sub <= 6 and low8 == 0)
    if major in (11, 12, 13):
        return True
    if major == 14:
        return sub < 3 and low8 == 0
    return sub < 2 and low8 == 0


class M20FrozenISATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT / "docs/m20/isa_v0_1.json").read_text())
        cls.rules = cls.spec["encoding_rules"]

    def test_formal_id_legacy_and_core_state_boundary(self):
        self.assertEqual(ISA_VERSION, "M20-300-ISA-0.1")
        self.assertEqual(LEGACY_ISA_VERSION, "M20-300-ISA-0.1-software")
        self.assertEqual(self.spec["isa_id"], ISA_VERSION)
        self.assertEqual(self.spec["legacy_isa_id"], LEGACY_ISA_VERSION)
        self.assertEqual(self.spec["schema_version"], 1)
        self.assertFalse(self.spec["provenance"]["semantics_changed"])
        registers = {r["name"]: (r["bits"], r["reset"]) for r in self.spec["registers"]}
        self.assertEqual(registers, {"pc": (12, 0), "ar": (8, 0),
                                    "a": (4, 0), "z": (1, 1),
                                    "c": (1, 0), "gpo": (4, 8)})
        self.assertEqual(sum(bits for bits, _ in registers.values()), 30)
        boundary = self.spec["implementation_boundary"]
        self.assertEqual(boundary["current_core_state_bits"], 33)
        self.assertEqual(boundary["current_control_state_bits"], 3)
        self.assertFalse(boundary["control_encoding_part_of_isa"])
        self.assertEqual(Machine([0xF100]).registers,
                         {name: reset for name, (_, reset) in registers.items()})
        self.assertFalse(self.spec["reset"]["clears_external_ram"])

    def test_all_65536_words_rule_uniqueness_and_independent_legality(self):
        self.assertEqual(len(self.rules), 45)
        self.assertEqual(len({r["id"] for r in self.rules}), 45)
        compiled = [(int(r["mask"], 16), int(r["value"], 16), r) for r in self.rules]
        for mask, value, rule in compiled:
            self.assertEqual(value & ~mask, 0, rule["id"])
            self.assertEqual(rule["operand_shift"], 0)
            self.assertEqual(mask | int(rule["operand_mask"], 16), 65535)
        legal = 0
        for word in range(65536):
            matches = [r for mask, value, r in compiled if word & mask == value]
            expected = independent_legal_word(word)
            self.assertEqual(len(matches), int(expected), f"word={word:04X}")
            if not expected:
                with self.assertRaises(IllegalInstruction):
                    decode(word)
                continue
            legal += 1
            rule, instruction = matches[0], decode(word)
            self.assertEqual(instruction.mnemonic, rule["mnemonic"], f"word={word:04X}")
            self.assertEqual(instruction.indirect, rule["indirect"])
            operand = (word & int(rule["operand_mask"], 16)) >> rule["operand_shift"]
            expected_operand = None if rule["operand_kind"] in ("none", "ar_indirect") else operand
            self.assertEqual(instruction.operand, expected_operand)
            self.assertEqual(instruction.cycles, rule["v1_cycles"])
        self.assertEqual(legal, 15015)
        self.assertEqual(65536 - legal, 50521)
        self.assertEqual(self.spec["encoding_match"]["legal_word_count"], legal)
        self.assertEqual(self.spec["encoding_match"]["illegal_word_count"], 65536 - legal)

    def test_declared_write_controls_flags_and_transactions(self):
        # These expected sets are an explicit contract, not imported decode data.
        z_updates = {"LDI", "ADDI", "ADCI", "SUBI", "SBCI", "ANDI", "XORI",
                     "SHL", "SHR", "NOT", "LD", "ADD", "ADC", "SUB", "SBC",
                     "CMP", "AND", "XOR", "OR"}
        preserve_a = {"ST", "CMP", "ARL", "ARH", "MOVARL", "MOVARH", "INCAR",
                      "JMP", "JZ", "JC", "OUT", "NOP", "HALT"}
        expected_operations = {
            "LDI": "load_operand", "LD": "load_operand", "ST": "store_a",
            "ADDI": "add", "ADD": "add", "ADCI": "adc", "ADC": "adc",
            "SUBI": "sub", "SUB": "sub", "SBCI": "sbc", "SBC": "sbc",
            "CMP": "compare", "ANDI": "and", "AND": "and", "XORI": "xor",
            "XOR": "xor", "OR": "or", "NOT": "not", "SHL": "shl", "SHR": "shr",
            "ARL": "ar_low_operand", "ARH": "ar_high_operand", "MOVARL": "ar_low_a",
            "MOVARH": "ar_high_a", "MOVA_ARL": "a_from_ar_low", "MOVA_ARH": "a_from_ar_high",
            "INCAR": "ar_increment", "JMP": "branch", "JZ": "branch", "JC": "branch",
            "IN0": "input_low4", "IN1": "input_high2", "OUT": "gpo_from_a",
            "NOP": "none", "HALT": "halt"}
        for rule in self.rules:
            name = rule["mnemonic"]
            self.assertEqual(rule["operation"], expected_operations[name])
            self.assertEqual(rule["a_write"], name not in preserve_a, rule["id"])
            self.assertEqual(rule["z_rule"], "result_zero" if name in z_updates else "preserve")
            expected_c = ("addition_carry" if name in {"ADDI", "ADCI", "ADD", "ADC"} else
                          "no_borrow" if name in {"SUBI", "SBCI", "SUB", "SBC", "CMP"} else
                          "old_a_bit3" if name == "SHL" else
                          "old_a_bit0" if name == "SHR" else "preserve")
            self.assertEqual(rule["c_rule"], expected_c)
            memory = rule["operand_kind"] in ("ram_addr8", "ar_indirect")
            expected_ram = ("WRITE" if name == "ST" else "READ") if memory else "NONE"
            self.assertEqual(rule["ram_access"], expected_ram)
            self.assertEqual(rule["v1_cycles"], 5 if memory else 2)
            self.assertEqual(rule["pc_rule"], {"JMP": "absolute", "JZ": "if_z", "JC": "if_c"}.get(name, "increment"))
            self.assertTrue(rule["retires"])

    def test_v0_machine_programs_and_reference_implementation_unchanged(self):
        expected = {
            "pong": (168, "1b43020e4cdebac150041796e3898aeaac489efaf911496b39fc0dc5fe66933c",
                     "e1029928d763ab5b0d21fe347687f52b326f545e9072f4c04365597439eead8c"),
            "snake": (368, "9d905bd0b8d567ae8d6f54250e220f85bdb72734324ba6025b3259e07b08dd13",
                      "466cb149c8e5d6914d0b78dc8a3ec5074c77020edf880cedbd520b41b3376b98")}
        for name, (words, source_sha, binary_sha) in expected.items():
            source = (ROOT / "software/m20_300" / (name + ".asm")).read_bytes()
            image = assemble(source.decode())
            self.assertEqual(hashlib.sha256(source).hexdigest(), source_sha)
            self.assertEqual(len(image.words), words)
            self.assertEqual(hashlib.sha256(image.binary).hexdigest(), binary_sha)
            self.assertEqual(self.spec["provenance"][name + "_binary_sha256"], binary_sha)
        reference_sha = hashlib.sha256((ROOT / "host/python/m20/machine.py").read_bytes()).hexdigest()
        self.assertEqual(reference_sha, "421aa1526a21ad063de40a951eb9544e7f85f67f4163f30953013dcc997172e4")
        self.assertEqual(self.spec["provenance"]["machine_py_sha256"], reference_sha)
        self.assertEqual(hashlib.sha256((ROOT / self.spec["provenance"]["reference_doc"]).read_bytes()).hexdigest(),
                         self.spec["provenance"]["reference_doc_sha256"])

    def test_fault_is_mapping_metadata_and_ffff_is_trap(self):
        self.assertEqual(self.spec["fault"]["scope"], "software_and_simulation_metadata_only")
        self.assertFalse(self.spec["fault"]["core_state"])
        self.assertFalse(self.spec["fault"]["core_port"])
        for words, status in (([], "FAULT"), ([0xFFFF], "TRAP")):
            cpu = Machine(words, ram={0x23: 9})
            before = (cpu.registers, list(cpu.ram))
            event = cpu.step()
            self.assertEqual(cpu.status, status)
            self.assertEqual(event["event"], status)
            self.assertEqual((cpu.registers, cpu.ram), before)
            self.assertEqual((cpu.retired, cpu.cycles, cpu.rom_reads,
                              cpu.ram_reads, cpu.ram_writes), (0, 2, 1, 0, 0))
            self.assertIsNone(cpu.step())
        ram = [7] * 256
        cpu = Machine([0x0005, 0xE200, 0xF100], ram=ram)
        cpu.run()
        self.assertEqual((cpu.status, cpu.retired, cpu.pc, cpu.gpo), ("HALTED", 3, 3, 5))
        self.assertIsNone(cpu.step())
        cpu.reset()
        self.assertEqual(cpu.ram, ram)
        self.assertEqual((cpu.pc, cpu.ar, cpu.a, cpu.z, cpu.c, cpu.gpo), (0, 0, 0, 1, 0, 8))

    def test_timing_profile_is_separate_and_preserves_v0_costs(self):
        profile = self.spec["timing_profile"]
        self.assertEqual(profile["id"], "M20-300-V1-TIMING-0.1")
        self.assertFalse(profile["part_of_frozen_isa"])
        self.assertFalse(profile["microarchitecture_frozen"])
        self.assertTrue(profile["version_change_required_for_cycle_or_wait_changes"])
        self.assertTrue(profile["candidate_state_encodings_not_frozen"])
        self.assertEqual((profile["ordinary_cycles"], profile["ram_cycles"],
                          profile["trap_cycles"], profile["software_unmapped_fault_cycles"],
                          profile["reset_cycles_separate"]), (2, 5, 2, 2, 1))
        cpu = Machine([0x0007, 0x8123, 0x8023, 0xF100])
        self.assertEqual((cpu.cycles, cpu.reset_cycles, cpu.total_cycles), (0, 1, 1))
        cpu.run()
        self.assertEqual((cpu.retired, cpu.ram_reads, cpu.ram_writes), (4, 1, 1))
        self.assertEqual(cpu.cycles, 2 * cpu.retired + 3 * (cpu.ram_reads + cpu.ram_writes))
        self.assertEqual((cpu.cycles, cpu.total_cycles), (14, 15))
        self.assertEqual(cpu.summary()["isa_version"], ISA_VERSION)


if __name__ == "__main__":
    unittest.main()
