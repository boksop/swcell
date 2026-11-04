"""Strict IO_STATE decoding and latest-boot coverage. OLED visibility is manual."""
import csv
import json
from pathlib import Path


def parse_record(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    record = json.loads(raw)
    if not isinstance(record, dict) or record.get('type') != 'IO_STATE' or record.get('build') not in ('OLEDKEYS01', 'OLEDKEYS02', 'OLEDKEYS03', 'OLEDKEYS04'):
        raise ValueError('not a supported OLEDKEYS diagnostic image')
    parsed = dict(record)
    widths = dict(keys=9, seen=9, events=32, frame=32, mode=4, patterns=8, up=32, merged=32)
    for key, width in widths.items():
        value = record.get(key)
        if not isinstance(value, str) or not value or any(c not in '0123456789abcdefABCDEF' for c in value):
            raise ValueError('invalid hexadecimal field ' + key)
        value = int(value, 16)
        if value >= 1 << width:
            raise ValueError('field exceeds width ' + key)
        parsed[key] = value
    counts = record.get('presses')
    if not isinstance(counts, list) or len(counts) != 9:
        raise ValueError('expected nine per-key press counters')
    if any(not isinstance(x, str) or len(x) != 8 or any(c not in '0123456789abcdefABCDEF' for c in x) for x in counts):
        raise ValueError('invalid key counter')
    parsed['presses'] = [int(x, 16) for x in counts]
    if any(type(record.get(key)) is not int or record[key] not in (0, 1) for key in ('oled', 'rx')):
        raise ValueError('oled/rx must be bits')
    if parsed['mode'] > 8 or parsed['keys'] & ~parsed['seen']:
        raise ValueError('inconsistent state snapshot')
    return parsed


class StateCollector:
    def __init__(self):
        self.rows = []
        self.last = None
        self.resets = 0
        self.pressed_observed = 0
        self.released_observed = 0

    def add(self, record):
        if self.last and any(record[k] < self.last[k] for k in ('frame', 'up', 'events')):
            self.resets += 1
            self.pressed_observed = self.released_observed = 0
        self.pressed_observed |= record['keys']
        self.released_observed |= (~record['keys']) & 0x1ff
        self.rows.append(record)
        self.last = record

    def summary(self):
        p = self.last
        return dict(build=p['build'] if p else None, valid_records=len(self.rows), resets_observed=self.resets,
                    current_boot_pressed_observed=self.pressed_observed,
                    current_boot_released_observed=self.released_observed,
                    fpga_seen_mask=p['seen'] if p else 0,
                    press_counts=p['presses'] if p else [0]*9,
                    all_inputs_seen_by_fpga=bool(p and p['seen'] == 0x1ff and all(p['presses'])),
                    all_levels_observed_by_host=self.pressed_observed == self.released_observed == 0x1ff,
                    all_patterns_transmitted=bool(p and p['patterns'] == 0xff),
                    oled_initialized=p['oled'] if p else 0,
                    oled_visual_verification='NOT_CONFIRMED', led_visual_verification='NOT_CONFIRMED',
                    note='input observations and SPI transmission do not prove physical labels, LED light or OLED pixels')

    def save(self, directory):
        directory = Path(directory)
        fields = ['frame', 'up', 'keys', 'seen', 'events', 'mode', 'patterns', 'oled', 'rx', 'merged']
        with (directory / 'states.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields+[f'press_{i}' for i in range(9)])
            writer.writeheader()
            for row in self.rows:
                writer.writerow({k: row[k] for k in fields} | {f'press_{i}': n for i, n in enumerate(row['presses'])})
        (directory / 'summary.json').write_text(json.dumps(self.summary(), ensure_ascii=False, indent=2) + '\n')
