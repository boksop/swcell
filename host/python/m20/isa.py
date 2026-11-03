"""Frozen M20-300 ISA v0.1: 16-bit words, 12-bit word-addressed PC.

Encoding and semantics match the validated v0.1-software prototype. The formal
contract is docs/m20/M20_300_ISA_FROZEN.md; timing is a separate versioned
profile, not a gate-count or physical timing implementation.
"""
from dataclasses import dataclass

LEGACY_ISA_VERSION = "M20-300-ISA-0.1-software"
ISA_VERSION = "M20-300-ISA-0.1"
ROM_WORDS = 4096
RAM_NIBBLES = 256
IMMEDIATE = ("LDI", "ADDI", "ADCI", "SUBI", "SBCI", "ANDI", "XORI")
AUX = ("SHL", "SHR", "NOT")
RAM_OPS = ("LD", "ST", "ADD", "ADC", "SUB", "SBC", "CMP", "AND", "XOR", "OR")
AR_OPS = ("ARL", "ARH", "MOVARL", "MOVARH", "MOVA_ARL", "MOVA_ARH", "INCAR")
IO_OPS = ("IN0", "IN1", "OUT")
SYS_OPS = ("NOP", "HALT")
BRANCHES = ("JMP", "JZ", "JC")


class IllegalInstruction(ValueError):
    """The word is outside 16 bits or has an illegal/reserved encoding."""


@dataclass(frozen=True)
class Instruction:
    mnemonic: str
    operand: int | None = None
    indirect: bool = False
    word: int = 0

    @property
    def name(self):
        return self.mnemonic

    @property
    def cycles(self):
        return 5 if self.mnemonic in RAM_OPS else 2

    @property
    def is_memory(self):
        return self.mnemonic in RAM_OPS

    def __str__(self):
        if self.indirect:
            return f"{self.mnemonic} [AR]"
        if self.mnemonic == "MOVA_ARL":
            return "MOVA ARL"
        if self.mnemonic == "MOVA_ARH":
            return "MOVA ARH"
        if self.operand is None:
            return self.mnemonic
        width = 3 if self.mnemonic in BRANCHES else 2 if self.is_memory else 1
        return f"{self.mnemonic} 0x{self.operand:0{width}X}"


def _uint(value, width, what):
    if type(value) is not int or not 0 <= value < (1 << width):
        raise IllegalInstruction(f"{what} must be an unsigned {width}-bit integer")
    return value


def decode(word: int) -> Instruction:
    """Strict decode: no ignored nonzero reserved fields."""
    _uint(word, 16, "instruction")
    major = word >> 12
    sub = (word >> 8) & 15
    low = word & 255
    operand = None
    indirect = False
    if major < 7:
        if word & 0xFF0:
            raise IllegalInstruction(f"reserved immediate bits in 0x{word:04X}")
        name, operand = IMMEDIATE[major], word & 15
    elif major == 7:
        if sub >= len(AUX) or low:
            raise IllegalInstruction(f"reserved AUX encoding 0x{word:04X}")
        name = AUX[sub]
    elif major in (8, 9):
        if sub >= len(RAM_OPS) or (major == 9 and low):
            raise IllegalInstruction(f"reserved RAM encoding 0x{word:04X}")
        name = RAM_OPS[sub]
        indirect = major == 9
        operand = None if indirect else low
    elif major == 10:
        if sub >= len(AR_OPS) or (word & 0xF0) or (sub >= 2 and low):
            raise IllegalInstruction(f"reserved AR encoding 0x{word:04X}")
        name = AR_OPS[sub]
        operand = word & 15 if sub < 2 else None
    elif major in (11, 12, 13):
        name, operand = BRANCHES[major - 11], word & 0xFFF
    elif major == 14:
        if sub >= len(IO_OPS) or low:
            raise IllegalInstruction(f"reserved IO encoding 0x{word:04X}")
        name = IO_OPS[sub]
    else:
        if sub >= len(SYS_OPS) or low:
            raise IllegalInstruction(f"reserved SYS encoding 0x{word:04X}")
        name = SYS_OPS[sub]
    return Instruction(name, operand, indirect, word)


def encode(mnemonic: str, operand: int | None = None, *, indirect=False) -> int:
    """Encode one canonical instruction; expressions belong to the assembler."""
    if not isinstance(mnemonic, str):
        raise IllegalInstruction("mnemonic must be a string")
    name = mnemonic.upper()
    if name in IMMEDIATE:
        word = IMMEDIATE.index(name) << 12 | _uint(operand, 4, "immediate")
    elif name in AUX:
        if operand is not None:
            raise IllegalInstruction(f"{name} has no numeric operand")
        word = 0x7000 | AUX.index(name) << 8
    elif name in RAM_OPS:
        if indirect:
            if operand is not None:
                raise IllegalInstruction("[AR] does not take a direct address")
            word = 0x9000 | RAM_OPS.index(name) << 8
        else:
            word = 0x8000 | RAM_OPS.index(name) << 8 | _uint(operand, 8, "RAM address")
    elif name in AR_OPS:
        sub = AR_OPS.index(name)
        if sub < 2:
            value = _uint(operand, 4, "AR immediate")
        else:
            if operand is not None:
                raise IllegalInstruction(f"{name} has no numeric operand")
            value = 0
        word = 0xA000 | sub << 8 | value
    elif name in BRANCHES:
        word = (0xB000 + BRANCHES.index(name) * 0x1000) | _uint(operand, 12, "word target")
    elif name in IO_OPS:
        if operand is not None:
            raise IllegalInstruction(f"{name} has no numeric operand")
        word = 0xE000 | IO_OPS.index(name) << 8
    elif name in SYS_OPS:
        if operand is not None:
            raise IllegalInstruction(f"{name} has no numeric operand")
        word = 0xF000 | SYS_OPS.index(name) << 8
    else:
        raise IllegalInstruction(f"unknown mnemonic {mnemonic!r}")
    if indirect and name not in RAM_OPS:
        raise IllegalInstruction("only RAM instructions accept [AR]")
    decode(word)
    return word
