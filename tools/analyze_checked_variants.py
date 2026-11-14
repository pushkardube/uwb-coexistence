#!/usr/bin/env python3
"""Summarize POWER/MULTI/COMBINED initiator UART logs; stdlib only."""
import argparse
import collections
import csv
import json
from pathlib import Path
import re
import statistics


def combined_group(group):
    ok = [r for r in group if 'dist_mm' in r]
    values = [r['rssi_dgc_mdB'] / 1000 for r in ok
              if r.get('diag') == 1 and r.get('rssi_dgc_mdB', -2147483648) != -2147483648]
    distances = [r['dist_mm'] for r in ok]
    return {'attempt_records': len(group), 'completed': len(ok), 'valid_rssi': len(values),
            'rssi_db_median': statistics.median(values) if values else None,
            'rssi_db_mean': statistics.mean(values) if values else None,
            'distance_mm_median': statistics.median(distances) if distances else None,
            'distance_mm_min_max': [min(distances), max(distances)] if distances else None}


def analyze_combined(rows, text, result):
    ready = re.search(r'COMBINED ready:[^\r\n]+', text)
    config = dict(re.findall(r'(targets|levels|attempts_per_peer)=(\d+)', ready[0])) if ready else {}
    level_count = int(config.get('levels', 64))
    initial_probe = level_count == 65
    fixed_word = None
    if ready and re.search(r'\bmode=fixed\b', ready[0]):
        power = re.search(r'\btx_power=(0x[0-9a-fA-F]+)', ready[0])
        if power:
            word = int(power[1], 16)
            if 0 <= word <= 0xffffffff and word == (word & 255) * 0x01010101:
                fixed_word = word
    groups = collections.defaultdict(list)
    peers = collections.defaultdict(list)
    for row in rows:
        groups[(row['peer'], row['level'])].append(row)
        peers[row['peer']].append(row)
    entries = []
    for (peer, level), group in sorted(groups.items()):
        entry = {'peer': peer, 'level': level, 'octet': hex(group[0]['octet']),
                 'cycles_seen': sorted({r['cycle'] for r in group})}
        entry.update(combined_group(group))
        entries.append(entry)
    result['by_peer_level'] = entries
    result['by_peer'] = [dict(peer=peer, **combined_group(group)) for peer, group in sorted(peers.items())]
    result['per_peer_sweep'] = []
    for peer in sorted(peers):
        levels = [r for r in entries if r['peer'] == peer]
        # The 01 probe changes coarse gain; compare the descending FE..02
        # ladder separately rather than pretending 01 is its highest setting.
        ladder = [r for r in levels if not initial_probe or r['level'] != 0]
        complete = [r['level'] for r in ladder] == list(range(1, 65) if initial_probe else range(64))
        medians = [r['rssi_db_median'] for r in ladder]
        sweep = {
            'peer': peer, 'all_64_levels_observed': complete,
            'full_to_low_rssi_drop_db': medians[0] - medians[-1]
                if complete and medians[0] is not None and medians[-1] is not None else None,
            'observed_nonincreasing_level_medians': all(
                a is not None and b is not None and a >= b for a, b in zip(medians, medians[1:]))
                if complete else None}
        if initial_probe:
            sweep['all_65_levels_observed'] = [r['level'] for r in levels] == list(range(65))
        result['per_peer_sweep'].append(sweep)
    if initial_probe:
        result['probe_01010101'] = [r for r in entries if r['level'] == 0]
    result['firmware_level_summaries'] = len(re.findall(r'COMBINED_LEVEL cycle=', text))
    if fixed_word is not None:
        result['mode'] = 'fixed'
        result['fixed_tx_power'] = f'0x{fixed_word:08X}'
        result['per_peer_sweep'] = []
    result['configuration'] = {k: int(v) for k, v in config.items()}
    result['schedule_matches_configuration'] = None
    if len(config) == 3:
        n, attempts, levels = (int(config[k]) for k in ('targets', 'attempts_per_peer', 'levels'))
        if n > 0 and attempts > 0 and (levels in (64, 65) or (levels == 1 and fixed_word is not None)):
            result['schedule_matches_configuration'] = all(
                r['peer'] == ((r['seq'] - 1) & 0xffffffff) % n and
                r['level'] == (((r['seq'] - 1) & 0xffffffff) // (n * attempts)) % levels and
                r['cycle'] == ((r['seq'] - 1) & 0xffffffff) // (n * attempts * levels) and
                r['octet'] == (fixed_word & 255 if fixed_word is not None else
                    1 if levels == 65 and r['level'] == 0 else
                    ((levels - 1 - r['level']) << 2 | 2)) for r in rows)


def analyze(path):
    text = Path(path).read_text(errors='replace')
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    # If capture includes a reset, analyze the latest application startup only.
    starts = list(re.finditer(r'(?:POWER|MULTI|COMBINED) ready:', text))
    if starts:
        text = text[starts[-1].start():]
    rows = []
    # Captures can stop halfway through the next UART record. Only parse
    # terminated lines; a fragment is neither an attempt nor a radio failure.
    for match in re.finditer(r'(POWER|MULTI|COMBINED) seq=[^\r\n]+(?=[\r\n])', text):
        record = {'variant': match[1]}
        for key, value in re.findall(r'(\w+)=([^\s]+)', match[0]):
            try:
                record[key] = int(value, 16 if value.lower().startswith('0x') else 10)
            except ValueError:
                record[key] = value
        if 'seq' in record and 'peer' in record:
            rows.append(record)
    if not rows:
        raise ValueError('No complete POWER/MULTI/COMBINED measurement or error records found')
    variant = rows[-1]['variant']
    rows = [r for r in rows if r['variant'] == variant]
    seq = [r['seq'] for r in rows]
    successful = [r for r in rows if 'dist_mm' in r]
    result = {
        'variant': variant, 'attempt_records': len(rows), 'completed': len(successful),
        'sequences': [seq[0], seq[-1]],
        'consecutive_sequences': all(b == ((a + 1) & 0xffffffff) for a, b in zip(seq, seq[1:])),
        'error_codes': dict(collections.Counter(str(r['error']) for r in rows if 'error' in r)),
        'fatal': bool(re.search(r'FATAL|ASSERTION|panic|Halting system', text)),
        'log_drops': 'messages dropped' in text,
    }
    if variant == 'COMBINED':
        analyze_combined(rows, text, result)
        return result, rows
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row['level'] if variant == 'POWER' else row['peer']].append(row)
    summaries = []
    for key, group in sorted(groups.items()):
        ok = [r for r in group if 'dist_mm' in r]
        valid = [r for r in ok if r.get('diag') == 1]
        field = 'rssi_dgc_mdB' if variant == 'POWER' else 'final_rssi_mdB'
        values = [r[field] / 1000 for r in valid if field in r and r[field] != -2147483648]
        distances = [r['dist_mm'] for r in ok]
        entry = {'level' if variant == 'POWER' else 'peer': key,
                 'attempt_records': len(group), 'completed': len(ok), 'valid_rssi': len(values),
                 'rssi_db_median': statistics.median(values) if values else None,
                 'rssi_db_mean': statistics.mean(values) if values else None,
                 'distance_mm_median': statistics.median(distances) if distances else None,
                 'distance_mm_min_max': [min(distances), max(distances)] if distances else None}
        if variant == 'POWER':
            entry['octet'] = hex(group[0]['octet'])
            entry['cycles_seen'] = sorted({r['cycle'] for r in group})
        summaries.append(entry)
    result['by_level' if variant == 'POWER' else 'by_peer'] = summaries
    if variant == 'POWER':
        medians = [r['rssi_db_median'] for r in summaries]
        complete_ladder = sorted(groups) == list(range(9))
        result['all_nine_levels_observed'] = complete_ladder
        result['firmware_level_summaries'] = len(re.findall(r'POWER_LEVEL cycle=', text))
        result['full_to_low_rssi_drop_db'] = (medians[0] - medians[-1]
            if complete_ladder and medians[0] is not None and medians[-1] is not None else None)
        result['observed_nonincreasing_level_medians'] = (all(
            a is not None and b is not None and a >= b for a, b in zip(medians, medians[1:]))
            if complete_ladder else None)
    else:
        peers = [r['peer'] for r in rows]
        result['adjacent_targets_differ'] = all(a != b for a, b in zip(peers, peers[1:]))
    return result, rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('log', type=Path)
    p.add_argument('--json', type=Path)
    p.add_argument('--csv', type=Path)
    args = p.parse_args()
    result, rows = analyze(args.log)
    print(json.dumps(result, indent=2))
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + '\n')
    if args.csv:
        fields = sorted(set().union(*(r.keys() for r in rows)))
        with args.csv.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == '__main__':
    main()
