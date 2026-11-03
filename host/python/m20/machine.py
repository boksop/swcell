"""Independent instruction interpreter, not a microcycle RTL simulator.

cycles counts execution microcycles; reset_cycles=1 is separate. RAM's default
zero fill is an explicit software-test fixture, not a physical power-on promise.
"""
from collections.abc import Mapping
from .isa import ISA_VERSION, RAM_OPS, ROM_WORDS, RAM_NIBBLES, decode, IllegalInstruction


def _bounded(value, maximum, name):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be 0..{maximum}")
    return value


class Machine:
    def __init__(self, words, ram=None, pc=0, keys=0, trace=True):
        self.words = tuple(words)
        if len(self.words) > ROM_WORDS: raise ValueError("ROM exceeds 4096 words")
        for word in self.words: _bounded(word, 0xFFFF, "ROM word")
        self.ram = [0] * RAM_NIBBLES
        self.ram_initialization = "zero_test_fixture" if ram is None else "explicit_test_fixture"
        if ram is not None:
            if isinstance(ram, Mapping):
                for addr, value in ram.items():
                    self.ram[_bounded(addr, 255, "RAM address")] = _bounded(value, 15, "RAM nibble")
            else:
                if len(ram) != RAM_NIBBLES: raise ValueError("RAM requires exactly 256 nibbles")
                self.ram = [_bounded(v, 15, "RAM nibble") for v in ram]
        self.trace_enabled = bool(trace)
        self.trace = []
        self.keys = keys
        self.reset(pc=pc)

    @property
    def keys(self): return self._keys

    @keys.setter
    def keys(self, value): self._keys = _bounded(value, 63, "six-key input")

    @property
    def total_cycles(self): return self.reset_cycles + self.cycles

    @property
    def halted(self): return self.status == "HALTED"

    @property
    def registers(self):
        return dict(pc=self.pc, a=self.a, ar=self.ar, z=self.z, c=self.c, gpo=self.gpo)

    def reset(self, pc=0, clear_ram=False):
        self.pc = _bounded(pc, 4095, "PC word address")
        self.a = self.ar = self.c = 0
        self.z = 1
        self.gpo = 8
        self.status = "RUNNING"
        self.reason = None
        self.stop_reason = None
        self.retired = self.cycles = self.rom_reads = 0
        self.ram_reads = self.ram_writes = self.gpio_writes = 0
        self.reset_cycles = 1
        self.trace.clear()
        if clear_ram: self.ram[:] = [0] * RAM_NIBBLES

    def _record(self, pc, word, event, cost, mnemonic=None, ram=None, gpio=None, input_value=None):
        record = dict(sequence=self.retired, pc=pc, opcode=word, word=word, mnemonic=mnemonic,
                      next_pc=self.pc, a=self.a, ar=self.ar, z=self.z, c=self.c,
                      gpo=self.gpo, gpio=gpio, input=input_value, ram_transaction=ram,
                      event=event, retired=event == "RETIRE", cycles=cost,
                      cumulative_cycles=self.cycles, status=self.status, reason=self.reason)
        if self.trace_enabled: self.trace.append(record)
        return record

    def step(self):
        if self.status != "RUNNING": return None
        pc = self.pc
        self.rom_reads += 1
        if pc >= len(self.words):
            self.cycles += 2; self.status = "FAULT"; self.reason = "UNMAPPED_ROM"
            return self._record(pc, None, "FAULT", 2)
        word = self.words[pc]
        try: ins = decode(word)
        except IllegalInstruction as exc:
            self.cycles += 2; self.status = "TRAP"; self.reason = str(exc)
            return self._record(pc, word, "TRAP", 2)
        name = ins.mnemonic
        next_pc = (pc + 1) & 0xFFF
        cost = ins.cycles
        ram_tx = gpio = input_value = None
        rhs = ins.operand
        if name in RAM_OPS:
            addr = self.ar if ins.indirect else ins.operand
            if name == "ST":
                previous = self.ram[addr]
                self.ram[addr] = self.a; self.ram_writes += 1
                ram_tx = dict(kind="WRITE", address=addr, value=self.a, previous=previous)
            else:
                rhs = self.ram[addr]
                _bounded(rhs, 15, "RAM nibble")
                self.ram_reads += 1
                ram_tx = dict(kind="READ", address=addr, value=rhs)
        if name in ("LDI", "LD"):
            self.a = rhs; self.z = int(self.a == 0)
        elif name in ("ADDI", "ADCI", "ADD", "ADC"):
            value = self.a + rhs + (self.c if name in ("ADCI", "ADC") else 0)
            self.a = value & 15; self.c = int(value >= 16); self.z = int(self.a == 0)
        elif name in ("SUBI", "SBCI", "SUB", "SBC", "CMP"):
            value = self.a - rhs - ((1 - self.c) if name in ("SBCI", "SBC") else 0)
            result = value & 15
            self.c = int(value >= 0); self.z = int(result == 0)
            if name != "CMP": self.a = result
        elif name in ("ANDI", "AND", "XORI", "XOR", "OR", "NOT"):
            if name in ("ANDI", "AND"): self.a &= rhs
            elif name in ("XORI", "XOR"): self.a ^= rhs
            elif name == "OR": self.a |= rhs
            else: self.a ^= 15
            self.z = int(self.a == 0)
        elif name == "SHL":
            self.c = (self.a >> 3) & 1; self.a = (self.a << 1) & 15; self.z = int(self.a == 0)
        elif name == "SHR":
            self.c = self.a & 1; self.a >>= 1; self.z = int(self.a == 0)
        elif name == "ARL": self.ar = (self.ar & 0xF0) | rhs
        elif name == "ARH": self.ar = (self.ar & 0x0F) | (rhs << 4)
        elif name == "MOVARL": self.ar = (self.ar & 0xF0) | self.a
        elif name == "MOVARH": self.ar = (self.ar & 0x0F) | (self.a << 4)
        elif name == "MOVA_ARL": self.a = self.ar & 15
        elif name == "MOVA_ARH": self.a = self.ar >> 4
        elif name == "INCAR": self.ar = (self.ar + 1) & 255
        elif name == "JMP": next_pc = rhs
        elif name == "JZ" and self.z: next_pc = rhs
        elif name == "JC" and self.c: next_pc = rhs
        elif name == "IN0": self.a = self.keys & 15; input_value = self.a
        elif name == "IN1": self.a = (self.keys >> 4) & 3; input_value = self.a
        elif name == "OUT":
            self.gpo = self.a; self.gpio_writes += 1; gpio = self.a
        elif name == "HALT": self.status = "HALTED"
        # ST/NOP and untaken conditionals have no remaining register effects.
        self.pc = next_pc
        self.cycles += cost
        self.retired += 1
        return self._record(pc, word, "RETIRE", cost, name, ram_tx, gpio, input_value)

    def run(self, max_instructions=100000, stop_pc=None):
        if type(max_instructions) is not int or max_instructions < 0:
            raise ValueError("max_instructions must be nonnegative")
        if stop_pc is not None: _bounded(stop_pc, 4095, "stop PC")
        self.stop_reason = None
        for _ in range(max_instructions):
            if self.status != "RUNNING": break
            if stop_pc is not None and self.pc == stop_pc:
                self.stop_reason = "BREAKPOINT"; break
            self.step()
        if self.stop_reason is None:
            self.stop_reason = (self.status if self.status != "RUNNING" else
                                "BREAKPOINT" if stop_pc is not None and self.pc == stop_pc else
                                "INSTRUCTION_LIMIT")
        return self.summary()

    def summary(self):
        return dict(isa_version=ISA_VERSION, status=self.status, reason=self.reason,
                    stop_reason=self.stop_reason, registers=self.registers, retired=self.retired,
                    cycles=self.cycles, reset_cycles=self.reset_cycles, total_cycles=self.total_cycles,
                    rom_reads=self.rom_reads, ram_reads=self.ram_reads, ram_writes=self.ram_writes,
                    gpio_writes=self.gpio_writes, ram_initialization=self.ram_initialization,
                    timing_model="ordinary=2, RAM=5 microcycles; no extra WAIT; not RTL timing")
