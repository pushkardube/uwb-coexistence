#!/usr/bin/env python3
"""Export one complete COMBINED sweep as a measured RSSI table (MD/CSV/JSON)."""
import argparse
import collections
import csv
import json
from pathlib import Path
import statistics

from analyze_checked_variants import analyze


def measured_map(log, peer=0, cycle=0):
    summary, records = analyze(log)
    if summary['variant'] != 'COMBINED':
        raise ValueError('Use a COMBINED initiator log with its startup configuration.')
    config = summary.get('configuration', {})
    if not summary.get('schedule_matches_configuration'):
        raise ValueError('Missing startup configuration or observed schedule mismatch.')
    if not 0 <= peer < config['targets'] or cycle < 0:
        raise ValueError('Peer/cycle outside the selected configuration.')
    groups = collections.defaultdict(list)
    for row in records:
        if row['peer'] == peer and row['cycle'] == cycle:
            groups[row['level']].append(row)
    expected = config['levels']
    budget = config['attempts_per_peer']
    if sorted(groups) != list(range(expected)):
        raise ValueError(f'Incomplete cycle: observed {len(groups)}/{expected} settings.')
    output = []
    distances = []
    for level, group in sorted(groups.items()):
        if len(group) != budget:
            raise ValueError(f'Level {level} has {len(group)}/{budget} attempt records.')
        octets = {r['octet'] for r in group}
        if len(octets) != 1:
            raise ValueError(f'Mixed TX octets within level {level}.')
        octet = octets.pop()
        good = [r for r in group if 'dist_mm' in r]
        valid = [r for r in good if r.get('diag') == 1 and
                 r.get('rssi_dgc_mdB', -2147483648) != -2147483648]
        rssi = [r['rssi_dgc_mdB'] / 1000 for r in valid]
        raw = [r['final_rssi_mdB'] / 1000 for r in valid]
        ranges = [r['dist_mm'] for r in good]
        distances.extend(ranges)
        output.append({
            'level': level, 'tx_power_hex': f'0x{octet * 0x01010101:08X}',
            'octet_hex': f'0x{octet:02X}', 'coarse': octet & 3, 'fine': octet >> 2,
            'attempts': len(group), 'completed': len(good), 'valid_rssi_samples': len(valid),
            'rssi_dgc_db_median': statistics.median(rssi) if rssi else None,
            'rssi_dgc_db_mean': statistics.mean(rssi) if rssi else None,
            'rssi_dgc_db_min': min(rssi) if rssi else None,
            'rssi_dgc_db_max': max(rssi) if rssi else None,
            'rssi_legacy_db_median': statistics.median(raw) if raw else None,
            'distance_mm_median': statistics.median(ranges) if ranges else None,
            'distance_mm_min': min(ranges) if ranges else None,
            'distance_mm_max': max(ranges) if ranges else None,
            'error_codes': json.dumps(dict(collections.Counter(str(r['error'])
                                        for r in group if 'error' in r)), sort_keys=True),
        })
    metadata = {
        'log': str(Path(log).resolve()), 'peer': peer, 'cycle': cycle,
        'configuration': config, 'attempts': sum(r['attempts'] for r in output),
        'completed': sum(r['completed'] for r in output),
        'valid_rssi_samples': sum(r['valid_rssi_samples'] for r in output),
        'reported_distance_mm_median': statistics.median(distances) if distances else None,
        'reported_distance_mm_min_max': [min(distances), max(distances)] if distances else None,
        'full_capture_fatal': summary['fatal'], 'full_capture_log_drops': summary['log_drops'],
        'full_capture_consecutive_sequences': summary['consecutive_sequences'],
    }
    return metadata, output


def fmt(value, digits=2):
    return 'NA' if value is None else f'{value:.{digits}f}'


def markdown(metadata, rows):
    actual = metadata['physical_distance_m']
    physical = ('Not supplied; the distances below are UWB-reported ranges.' if actual is None
                else f'{actual:.4f} m, supplied as the physical antenna separation.')
    text = [
        '# Measured TX register to receiver RSSI mapping', '',
        'One complete sweep at the current two-board setup; this is an empirical',
        'mapping for this geometry, orientation, PHY and hardware, not a universal calibration.', '',
        f"- Source UART log: `{metadata['log']}`",
        f"- Responder ID: {metadata['peer']}; sweep cycle: {metadata['cycle']}.",
        f"- Settings: {metadata['configuration']['levels']}; attempts per setting: {metadata['configuration']['attempts_per_peer']}.",
        f'- Physical separation: {physical}',
        f"- Median reported range across successful exchanges: {fmt(metadata['reported_distance_mm_median'], 1)} mm.",
        f"- Full-cycle completion: {metadata['completed']}/{metadata['attempts']}; valid RSSI samples: {metadata['valid_rssi_samples']}.", '',
        'The initiator sweeps Poll and Final TX power. The responder measures Final',
        'RSSI and returns it with raw diagnostics using fixed FEFEFEFE reply power.',
        'RSSI below is the median DGC-corrected estimate, in dB, not calibrated dBm.',
        'The full register word repeats the listed octet in all four TX_POWER bytes.', '',
        'The initial 01010101 probe uses coarse=1, fine=0. The following 64 entries',
        'use coarse=2, fine=63 down to 0. Do not interpret the initial jump or',
        'adjacent register steps as equal calibrated dB steps. No receiver-position',
        'tracking is available; the operator was asked to hold the boards stationary.', '',
        '| Level | TX_POWER register | Median RSSI (dB) | Median reported range (mm) | Completed / attempts | Valid RSSI |',
        '|---:|---|---:|---:|---:|---:|',
    ]
    for row in rows:
        text.append(f"| {row['level']} | `{row['tx_power_hex']}` | {fmt(row['rssi_dgc_db_median'])} | "
                    f"{fmt(row['distance_mm_median'], 1)} | {row['completed']}/{row['attempts']} | {row['valid_rssi_samples']} |")
    text += ['', 'The companion CSV/JSON retain mean/min/max RSSI, legacy RSSI, coarse/fine',
             'codes, distance spread and error counts. Rows include failed attempts;',
             'RSSI/range distributions are conditional on successful exchanges.',
             'NA means no usable measurement, not minus infinity or zero received power.', '',
             'The same physical position can produce different reported ranges as receive',
             'power and receiver state change. Use a tape measurement for a calibrated',
             'distance label, and repeat at other positions to build a distance-indexed map.', '']
    return '\n'.join(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--peer', type=int, default=0)
    parser.add_argument('--cycle', type=int, default=0)
    parser.add_argument('--out-prefix', type=Path, required=True)
    parser.add_argument('--physical-distance-m', type=float)
    args = parser.parse_args()
    if args.physical_distance_m is not None and args.physical_distance_m <= 0:
        parser.error('--physical-distance-m must be positive')
    metadata, rows = measured_map(args.log, args.peer, args.cycle)
    metadata['physical_distance_m'] = args.physical_distance_m
    destinations = [Path(str(args.out_prefix) + suffix) for suffix in ('.md', '.csv', '.json')]
    if any(p.exists() for p in destinations):
        parser.error('Choose a new output prefix; existing results are not overwritten.')
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    destinations[0].write_text(markdown(metadata, rows))
    with destinations[1].open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    destinations[2].write_text(json.dumps({'metadata': metadata, 'rows': rows}, indent=2) + '\n')
    print(json.dumps(metadata, indent=2))
    for path in destinations:
        print(path)


if __name__ == '__main__':
    main()
