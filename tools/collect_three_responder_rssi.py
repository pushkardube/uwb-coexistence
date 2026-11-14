#!/usr/bin/env python3
"""Save three-responder BLE readings and compare peers at each TX setting."""
import argparse
import collections
import csv
import datetime
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

from analyze_checked_variants import analyze


def summarize(directory):
    """Use the latest startup; retain failed attempts and partial settings."""
    summary, records = analyze(directory / 'init.log')
    config = summary.get('configuration', {})
    if (summary['variant'] != 'COMBINED' or config.get('targets') != 3 or
            not summary.get('schedule_matches_configuration')):
        raise ValueError('Expected a COMBINED log with targets=3 and a valid schedule.')
    groups = collections.defaultdict(list)
    for record in records:
        groups[record['cycle'], record['level']].append(record)
    output = []
    for (cycle, level), group in sorted(groups.items()):
        octets = {record['octet'] for record in group}
        if len(octets) != 1:
            raise ValueError(f'Mixed TX settings in cycle {cycle}, level {level}.')
        row = dict(cycle=cycle, level=level,
                   tx_power_hex=f'0x{octets.pop() * 0x01010101:08X}',
                   first_seq=min(r['seq'] for r in group),
                   last_seq=max(r['seq'] for r in group))
        full = True
        all_valid = True
        for peer in range(3):
            attempts = [r for r in group if r['peer'] == peer]
            complete = [r for r in attempts if 'dist_mm' in r]
            valid = [r for r in complete if r.get('diag') == 1 and
                     r.get('rssi_dgc_mdB', -2147483648) != -2147483648]
            distance = [r['dist_mm'] / 1000 for r in complete]
            rssi = [r['rssi_dgc_mdB'] / 1000 for r in valid]
            prefix = f'peer{peer}_'
            row.update({
                prefix + 'attempts': len(attempts),
                prefix + 'completed': len(complete),
                prefix + 'valid_rssi': len(valid),
                prefix + 'distance_m_median': statistics.median(distance) if distance else None,
                prefix + 'rssi_db_median': statistics.median(rssi) if rssi else None,
                prefix + 'rssi_db_min': min(rssi) if rssi else None,
                prefix + 'rssi_db_max': max(rssi) if rssi else None,
                prefix + 'errors': json.dumps(dict(collections.Counter(
                    str(r['error']) for r in attempts if 'error' in r)), sort_keys=True),
            })
            full &= len(attempts) == config['attempts_per_peer']
            all_valid &= bool(valid)
        row['full_attempt_budget'] = full
        row['all_peers_have_valid_rssi'] = all_valid
        output.append(row)
    with (directory / 'rssi_by_tx_setting.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    result = {
        'configuration': config,
        'reported_distance_unit': 'm; UWB-reported, not tape-measured',
        'rssi_unit': 'DGC-corrected dB estimate, not calibrated dBm',
        'comparison': 'same TX setting and cycle; consecutive addressed exchanges',
        'full_attempt_budget_settings': sum(r['full_attempt_budget'] for r in output),
        'settings_with_valid_rssi_from_all_peers': sum(r['all_peers_have_valid_rssi'] for r in output),
        'consecutive_sequences': summary['consecutive_sequences'],
        'fatal': summary['fatal'],
        'log_drops': summary['log_drops'],
        'rows': output,
    }
    if 'sweep_order' in summary:
        result['sweep_order'] = summary['sweep_order']
    (directory / 'rssi_by_tx_setting.json').write_text(json.dumps(result, indent=2) + '\n')
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=720,
                        help='capture duration; default 720 seconds, then pause')
    parser.add_argument('--address', help='BLE initiator address, if selection is needed')
    parser.add_argument('--out', type=Path, help='new output directory; existing data is never overwritten')
    parser.add_argument('--summarize-only', type=Path,
                        help='regenerate comparison files from an existing capture; no radio access')
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error('--seconds must be finite and positive')
    if args.summarize_only and args.out:
        parser.error('--out and --summarize-only cannot be combined')
    directory = args.summarize_only or args.out or Path('build') / (
        'three_responder_rssi_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    status = 0
    if not args.summarize_only:
        if directory.exists():
            parser.error('Choose a new --out directory; existing captures are not overwritten.')
        # The existing collector owns BLE notifications, ACK/replay and safe PAUSE.
        command = [sys.executable, str(Path(__file__).with_name('collect_checked_ble.py')),
                   '--seconds', str(args.seconds), '--out', str(directory), '--quiet']
        if args.address:
            command += ['--address', args.address]
        try:
            status = subprocess.run(command, check=False).returncode
        except KeyboardInterrupt:
            status = 130  # Child also receives Ctrl-C and preserves its capture.
    try:
        result = summarize(directory)
    except (OSError, ValueError) as error:
        print(f'Comparison unavailable: {error}; any raw capture remains in {directory}', file=sys.stderr)
        raise SystemExit(status or 1)
    print(f'READINGS={directory / "measurements.csv"}', flush=True)
    print(f'COMPARISON={directory / "rssi_by_tx_setting.csv"}', flush=True)
    print('Full-budget settings:', result['full_attempt_budget_settings'], flush=True)
    print('Settings with valid RSSI from all three peers:',
          result['settings_with_valid_rssi_from_all_peers'], flush=True)
    raise SystemExit(status)


if __name__ == '__main__':
    main()
