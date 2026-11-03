"""Command line assembler and interpreter. Run with PYTHONPATH=host/python."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from .assembler import AssemblyError, assemble
from .machine import Machine


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ass = commands.add_parser("assemble", help="assemble text to little-endian .bin, .memh and listing")
    ass.add_argument("source", type=Path)
    ass.add_argument("--output-dir", required=True, type=Path)
    run = commands.add_parser("run", help="run a word-ROM image, without hardware")
    run.add_argument("binary", type=Path)
    run.add_argument("--format", choices=("auto", "binary", "memh"), default="auto")
    run.add_argument("--max-instructions", type=int, default=100000)
    run.add_argument("--entry", type=lambda s: int(s, 0), default=0)
    run.add_argument("--keys", type=lambda s: int(s, 0), default=0)
    run.add_argument("--trace", type=Path)
    run.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "assemble":
            source = args.source.read_text()
            result = assemble(source, str(args.source))
            out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
            stem = args.source.stem
            binary = result.binary
            (out / (stem + ".bin")).write_bytes(binary)
            (out / (stem + ".memh")).write_text(result.memh)
            (out / (stem + ".symbols.json")).write_text(json.dumps(result.symbols, indent=2, sort_keys=True) + "\n")
            (out / (stem + ".source_map.json")).write_text(json.dumps(result.source_map, indent=2) + "\n")
            listing = ["WORD  CODE  DISASSEMBLY             SOURCE"]
            listing += [f"{r['address']:03X}   {r['word']:04X}  {r['disassembly']:<23} {r['line']:4}: {r['source']}" for r in result.listing]
            (out / (stem + ".lst")).write_text("\n".join(listing) + "\n")
            stats = dict(image_words=len(result.words), emitted_words=result.used_words,
                         image_bytes=len(binary), capacity_words=4096,
                         holes=len(result.words) - result.used_words, hole_word="0xFFFF",
                         binary_word_order="little-endian", sha256=hashlib.sha256(binary).hexdigest())
            (out / (stem + ".assembly.json")).write_text(json.dumps(stats, indent=2) + "\n")
            print(json.dumps(stats))
            return 0
        data = args.binary.read_bytes()
        image_format = args.format
        if image_format == "auto":
            image_format = "memh" if args.binary.suffix.lower() == ".memh" else "binary"
        if image_format == "memh":
            words = []
            for line_no, line in enumerate(data.decode("ascii").splitlines(), 1):
                token = line.strip()
                if not token: continue
                if not re.fullmatch(r"[0-9a-fA-F]{4}", token):
                    raise ValueError(f"memh line {line_no}: expected exactly four hex digits")
                words.append(int(token, 16))
        else:
            if len(data) % 2: raise ValueError("binary image must contain complete 16-bit words")
            words = [int.from_bytes(data[i:i+2], "little") for i in range(0, len(data), 2)]
        machine = Machine(words, pc=args.entry, keys=args.keys, trace=args.trace is not None)
        summary = machine.run(args.max_instructions)
        summary["program_sha256"] = hashlib.sha256(data).hexdigest()
        summary["image_format"] = image_format
        if args.trace:
            args.trace.parent.mkdir(parents=True, exist_ok=True)
            args.trace.write_text("".join(json.dumps(r) + "\n" for r in machine.trace))
        if args.summary:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary))
        return 0 if machine.halted else 2
    except (OSError, AssemblyError, ValueError) as exc:
        print(f"M20_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
