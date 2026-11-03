"""Two-pass word-addressed M20 assembler with a restricted expression grammar."""
from dataclasses import dataclass
import ast
import re

from .isa import ROM_WORDS, RAM_OPS, decode, encode, IllegalInstruction


class AssemblyError(ValueError):
    pass


@dataclass(frozen=True)
class AssemblyResult:
    # Empty .org gaps are 0xFFFF (TRAP), and count towards image occupancy.
    words: tuple[int, ...]
    symbols: dict[str, int]
    listing: tuple[dict, ...]
    source_map: dict[int, dict]

    @property
    def binary(self):
        return b"".join(word.to_bytes(2, "little") for word in self.words)

    @property
    def memh(self):
        return "".join(f"{word:04X}\n" for word in self.words)

    @property
    def used_words(self):
        return len(self.source_map)


_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


def _expression(text, resolve):
    try:
        node = ast.parse(text.strip(), mode="eval").body
    except (SyntaxError, ValueError) as exc:
        raise AssemblyError(f"invalid expression {text!r}") from exc

    if sum(1 for _ in ast.walk(node)) > 512:
        raise AssemblyError("expression is too complex")

    def evaluate(n):
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return n.value
        if isinstance(n, ast.Name):
            return resolve(n.id)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub, ast.Invert)):
            value = visit(n.operand)
            return value if isinstance(n.op, ast.UAdd) else -value if isinstance(n.op, ast.USub) else ~value
        if isinstance(n, ast.BinOp):
            a, b = visit(n.left), visit(n.right)
            if isinstance(n.op, ast.Add): return a + b
            if isinstance(n.op, ast.Sub): return a - b
            if isinstance(n.op, ast.Mult): return a * b
            if isinstance(n.op, ast.FloorDiv):
                if b == 0: raise AssemblyError("division by zero")
                return a // b
            if isinstance(n.op, ast.Mod):
                if b == 0: raise AssemblyError("modulo by zero")
                return a % b
            if isinstance(n.op, (ast.LShift, ast.RShift)):
                if not 0 <= b <= 63: raise AssemblyError("shift must be 0..63")
                return a << b if isinstance(n.op, ast.LShift) else a >> b
            if isinstance(n.op, ast.BitAnd): return a & b
            if isinstance(n.op, ast.BitOr): return a | b
            if isinstance(n.op, ast.BitXor): return a ^ b
        raise AssemblyError("expression permits only integer symbols/arithmetic/bitwise operations")

    def visit(n):
        value = evaluate(n)
        if value.bit_length() > 128:
            raise AssemblyError("expression integer too large")
        return value

    return visit(node)


def assemble(text: str, filename="<string>") -> AssemblyResult:
    constants = {}
    labels = {}
    parsed = []
    declared = set()

    def declare(name, line):
        if not _NAME.fullmatch(name):
            raise AssemblyError(f"{filename}:{line}: invalid symbol {name!r}")
        if name in declared:
            raise AssemblyError(f"{filename}:{line}: duplicate symbol {name}")
        declared.add(name)

    for lineno, raw in enumerate(text.splitlines(), 1):
        # A semicolon starts an inline comment; // remains integer division.
        content = raw.split(";", 1)[0].strip()
        if not content or content.startswith("#"):
            continue
        while True:
            match = re.match(r"^([A-Za-z_][A-Za-z_0-9]*)\s*:\s*(.*)$", content)
            if not match: break
            name, content = match.groups(); declare(name, lineno)
            parsed.append((lineno, "label", name, raw))
        if not content:
            continue
        # Tabs are whitespace too.
        fields = content.split(None, 1)
        head = fields[0]; arg = fields[1].strip() if len(fields) == 2 else ""
        if head.lower() == ".equ":
            match = re.match(r"^([A-Za-z_]\w*)\s*(?:,\s*|\s+)(.+)$", arg)
            if not match: raise AssemblyError(f"{filename}:{lineno}: .equ NAME, expression")
            name, expr = match.groups(); declare(name, lineno); constants[name] = (expr, lineno)
        else:
            parsed.append((lineno, head, arg, raw))

    def resolver(name, active=None):
        if name in labels: return labels[name]
        if name not in constants: raise AssemblyError(f"undefined symbol {name}")
        active = set() if active is None else active
        if name in active: raise AssemblyError(f"cyclic constant {name}")
        return _expression(constants[name][0], lambda n: resolver(n, active | {name}))

    pc = 0; emissions = []
    for line, op, arg, raw in parsed:
        try:
            if op == "label":
                if pc >= ROM_WORDS: raise AssemblyError("label outside ROM")
                labels[arg] = pc
            elif op.lower() == ".org":
                pc = _expression(arg, resolver)
                if not 0 <= pc < ROM_WORDS: raise AssemblyError(".org must be 0..4095")
            else:
                if op.startswith(".") and op.lower() != ".word":
                    raise AssemblyError(f"unknown directive {op}")
                if pc >= ROM_WORDS: raise AssemblyError("ROM exceeds 4096 words")
                emissions.append((pc, line, op, arg, raw)); pc += 1
        except (AssemblyError, ValueError) as exc:
            raise AssemblyError(f"{filename}:{line}: {exc}") from exc
    resolved = dict(labels)
    for name in constants:
        try: resolved[name] = resolver(name)
        except AssemblyError as exc: raise AssemblyError(f"{filename}:{constants[name][1]}: {exc}") from exc
    memory = {}; listing = []; source_map = {}
    for addr, line, op, arg, raw in emissions:
        try:
            if addr in memory: raise AssemblyError(f"overlapping ROM address 0x{addr:03X}")
            name = op.upper()
            clean = arg.strip()
            if name == ".WORD":
                word = _expression(clean, lambda n: resolved[n] if n in resolved else resolver(n))
                if not 0 <= word <= 0xFFFF: raise AssemblyError(".word must be 0..65535")
            elif name in ("MOVARL", "MOVARH", "SHL", "SHR", "NOT"):
                if clean.upper() not in ("", "A"): raise AssemblyError(f"{name} accepts only A")
                word = encode(name)
            elif name == "MOVA":
                if clean.upper() not in ("ARL", "ARH"): raise AssemblyError("MOVA expects ARL or ARH")
                word = encode("MOVA_" + clean.upper())
            elif name in RAM_OPS and clean.upper().replace(" ", "") == "[AR]":
                word = encode(name, indirect=True)
            elif clean:
                if clean.startswith("[") and clean.endswith("]"): clean = clean[1:-1].strip()
                if clean.startswith("#"): clean = clean[1:].strip()
                value = _expression(clean, lambda n: resolved[n] if n in resolved else resolver(n))
                word = encode(name, value)
            else:
                word = encode(name)
            memory[addr] = word
            try: decoded = str(decode(word))
            except IllegalInstruction: decoded = ".word (TRAP encoding)"
            row = dict(address=addr, word=word, source=raw, line=line, file=filename, disassembly=decoded)
            listing.append(row); source_map[addr] = dict(file=filename, line=line, source=raw)
        except (AssemblyError, IllegalInstruction, KeyError, TypeError, ValueError) as exc:
            raise AssemblyError(f"{filename}:{line}: {exc}") from exc
    words = tuple(memory.get(i, 0xFFFF) for i in range(max(memory, default=-1) + 1))
    return AssemblyResult(words, resolved, tuple(listing), source_map)
