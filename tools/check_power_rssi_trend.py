#!/usr/bin/env python3
"""Sort an exported power/RSSI map by nominal gain and check its RSSI trend."""
import argparse
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path


def ranks(values):
    groups = collections.defaultdict(list)
    for index, value in enumerate(values):
        groups[value].append(index)
    output = [0.0] * len(values)
    offset = 0
    for value, indices in sorted(groups.items()):
        rank = offset + (len(indices) + 1) / 2
        for index in indices:
            output[index] = rank
        offset += len(indices)
    return output


def spearman(values):
    if len(values) < 2:
        return None
    x = list(range(1, len(values) + 1))
    y = ranks(values)
    mx, my = sum(x) / len(x), sum(y) / len(y)
    numerator = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return numerator / denominator if denominator else None


def increasing_power(rows):
    # This ordering is valid for this measured ladder, not arbitrary mixed
    # coarse/fine words. A coarse increase alone cannot order every gain code.
    output = [dict(row) for row in rows]
    octets = set()
    for row in output:
        octet = int(row['octet_hex'], 16)
        if not 0 <= octet <= 255 or not (row['coarse'] == 2 or (row['coarse'] == 1 and row['fine'] == 0)):
            raise ValueError('Unsupported mixed-coarse map; supply a calibrated order instead.')
        if row['coarse'] != octet & 3 or row['fine'] != octet >> 2:
            raise ValueError('Coarse/fine fields disagree with octet.')
        if int(row['tx_power_hex'], 16) != octet * 0x01010101 or octet in octets:
            raise ValueError('Invalid repeated-byte word or duplicate setting.')
        octets.add(octet)
    output.sort(key=lambda row: (row['coarse'], row['fine']))
    for index, row in enumerate(output, 1):
        row['power_rank'] = index
        previous = output[index - 2]['rssi_dgc_db_median'] if index > 1 else None
        current = row['rssi_dgc_db_median']
        row['rssi_delta_from_previous_db'] = (current - previous
            if previous is not None and current is not None else None)
    return output


def trend(rows, field):
    pairs = [(a, b) for a, b in zip(rows, rows[1:])
             if a[field] is not None and b[field] is not None]
    deltas = [b[field] - a[field] for a, b in pairs]
    values = [row[field] for row in rows if row[field] is not None]
    reversals = [{'from_tx_power': a['tx_power_hex'], 'to_tx_power': b['tx_power_hex'],
                  'from_rssi_db': a[field], 'to_rssi_db': b[field], 'delta_db': b[field] - a[field]}
                 for a, b in pairs if b[field] - a[field] < -1e-12]
    return {'valid_settings': len(values), 'compared_adjacent_steps': len(pairs),
            'increasing_steps': sum(d > 1e-12 for d in deltas),
            'flat_steps': sum(abs(d) <= 1e-12 for d in deltas),
            'decreasing_steps': len(reversals),
            'strictly_increasing': bool(pairs) and all(d > 1e-12 for d in deltas),
            'nondecreasing': bool(pairs) and all(d >= -1e-12 for d in deltas),
            'spearman_rank_correlation': spearman(values),
            'endpoint_rssi_increase_db': rows[-1][field] - rows[0][field]
                if rows and rows[-1][field] is not None and rows[0][field] is not None else None,
            'largest_reversal_db': max((-r['delta_db'] for r in reversals), default=0),
            'reversals': reversals}


def number(value, digits=3):
    return 'NA' if value is None else f'{value:.{digits}f}'


def report(source, destination, metadata, rows, stats, has_plot):
    main = stats['corrected_median']
    raw = stats['legacy_median']
    relative = os.path.relpath(source, destination.parent)
    text = [
        '# TX power sorted low to high: measured RSSI check', '',
        '**Result: RSSI follows increasing nominal TX gain strongly overall, but the',
        'measured medians are not strictly monotonic at every adjacent setting.**', '',
        f"Source dataset: [{source.name}]({relative}), peer {metadata['peer']}, cycle {metadata['cycle']}.",
        f"Median UWB-reported distance: {metadata['reported_distance_mm_median']:.1f} mm; physical tape separation was "
        + ('not supplied.' if metadata.get('physical_distance_m') is None else f"{metadata['physical_distance_m']} m."),
        f"The same {metadata['attempts']} attempted exchanges are reused; this analysis does not reflash or recapture hardware.", '',
        '## Ordering used', '',
        'Rows are sorted by **nominal transmitter gain**, not by the measured RSSI.',
        '01010101 is coarse=1/fine=0; 02020202 is coarse=2/fine=0;',
        'then coarse stays 2 while fine increases from 1 through 63, ending at FEFEFEFE.',
        'This ordering applies to this specific ladder. Arbitrary mixed-coarse register',
        'values cannot be ordered by hex value alone. No absolute emitted-power',
        'calibration or equal-dB spacing is inferred.', '',
        'The local vendor reference `dw3000_device.c` defines positive coarse-1 to',
        'coarse-2 gain and a nonnegative channel-9 fine-gain increment table.',
        'Those support the nominal ordering, not an absolute calibration of this pair.',
        'The earlier acquisition order was 01, FE, FA, ... 02; the data was not',
        'collected as a new low-to-high sweep. Original acquisition level is retained.', '',
        '## Trend check', '',
        f"- Lowest setting median: {number(rows[0]['rssi_dgc_db_median'])} dB.",
        f"- Highest setting median: {number(rows[-1]['rssi_dgc_db_median'])} dB.",
        f"- Endpoint RSSI increase: **{number(main['endpoint_rssi_increase_db'])} dB**.",
        f"- Adjacent steps: **{main['increasing_steps']} increases, {main['flat_steps']} flat, {main['decreasing_steps']} decreases** out of {main['compared_adjacent_steps']} compared pairs.",
        f"- Largest local decrease: **{number(main['largest_reversal_db'])} dB**.",
        f"- Spearman rank correlation, nominal order versus corrected median RSSI: **{number(main['spearman_rank_correlation'], 6)}**.",
        f"- Uncorrected legacy median comparison: {number(raw['spearman_rank_correlation'], 6)} rank correlation, {raw['decreasing_steps']} decreasing adjacent steps.", '',
        'Less-negative RSSI means a stronger received signal. Corrected RSSI is the',
        'DGC-adjusted estimate at the responder, not calibrated dBm. Raw sample',
        'spread, fading, receiver gain state and time/order drift can contribute to',
        'local reversals; this single capture cannot uniquely identify their cause.',
        'Rank correlation is descriptive, not a statistical independence test or',
        'proof of a calibrated transmitter transfer function. No smoothing, isotonic',
        'fit or sorting by RSSI has been used to manufacture monotonicity.', '',
    ]
    if has_plot:
        text += [f'![Measured RSSI and adjacent changes]({destination.with_suffix(".png").name})', '']
    text += ['## All settings in increasing nominal power order', '',
             'Delta is this row minus the preceding weaker setting. Negative deltas',
             'are reversals. Original level identifies the row in the acquisition-order table.', '',
             '| Power rank | Original level | TX_POWER | Coarse / fine | Median RSSI (dB) | Delta (dB) | Median range (mm) | Valid RSSI |',
             '|---:|---:|---|---|---:|---:|---:|---:|']
    for row in rows:
        delta = row['rssi_delta_from_previous_db']
        delta_text = '—' if delta is None else f'{delta:+.3f}'
        if delta is not None and delta < -1e-12:
            delta_text = f'**{delta_text}**'
        text.append(f"| {row['power_rank']} | {row['level']} | `{row['tx_power_hex']}` | "
                    f"{row['coarse']} / {row['fine']} | {number(row['rssi_dgc_db_median'])} | {delta_text} | "
                    f"{number(row['distance_mm_median'], 1)} | {row['valid_rssi_samples']} |")
    text += ['', '## Adjacent reversals', '',
             '| Lower nominal setting | Next higher setting | Lower-setting RSSI | Higher-setting RSSI | Change (dB) |',
             '|---|---|---:|---:|---:|']
    for row in main['reversals']:
        text.append(f"| `{row['from_tx_power']}` | `{row['to_tx_power']}` | "
                    f"{number(row['from_rssi_db'])} | {number(row['to_rssi_db'])} | {row['delta_db']:+.3f} |")
    text += ['', 'To distinguish repeatable hardware/estimator effects from variability,',
             'collect fresh repeated sweeps in ascending and descending or randomized',
             'order at the same measured physical geometry.',
             f"Across the selected settings, {sum(r['completed'] for r in rows)}/{sum(r['attempts'] for r in rows)} exchanges completed.",
             'RSSI is conditional on received frames; inspect the per-setting counts',
             'when evaluating reception rather than inferring PRR from RSSI alone.', '']
    return '\n'.join(text)


def plot(rows, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x = [r['power_rank'] for r in rows]
    def values(field):
        return [float('nan') if r[field] is None else r[field] for r in rows]
    fig, (top, bottom) = plt.subplots(2, 1, sharex=True, figsize=(13, 8),
                                      gridspec_kw={'height_ratios': [3, 1.4]})
    top.fill_between(x, values('rssi_dgc_db_min'), values('rssi_dgc_db_max'),
                     alpha=.18, color='#2463a6', label='Observed sample min–max (not CI)')
    top.plot(x, values('rssi_dgc_db_median'), '.-', color='#165a9e', label='Median corrected RSSI')
    dips = [r for r in rows if r['rssi_delta_from_previous_db'] is not None and r['rssi_delta_from_previous_db'] < -1e-12]
    top.scatter([r['power_rank'] for r in dips], [r['rssi_dgc_db_median'] for r in dips],
                color='#c94a24', zorder=4, label='Local reversal')
    top.set(ylabel='Responder RSSI estimate (dB)', title='Same captured sweep, sorted by increasing nominal TX gain')
    top.legend(loc='lower right', fontsize=9)
    delta = [r['rssi_delta_from_previous_db'] for r in rows[1:]]
    bottom.bar(x[1:], [float('nan') if d is None else d for d in delta],
               color=['#c94a24' if d is not None and d < -1e-12 else '#27816e' for d in delta])
    bottom.axhline(0, color='black', linewidth=.8)
    bottom.set(ylabel='Adjacent change (dB)', xlabel='Nominal TX-power rank / repeated octet (not calibrated dBm)')
    ticks = sorted(set([0, len(rows)-1] + list(range(9, len(rows), 8))))
    bottom.set_xticks([x[i] for i in ticks], [f"{x[i]}\n{rows[i]['octet_hex']}" for i in ticks])
    for axis in (top, bottom):
        axis.grid(alpha=.2)
        axis.set_xlim(.3, len(rows)+.7)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='JSON from export_power_rssi_map.py')
    parser.add_argument('--out-prefix', type=Path, required=True)
    parser.add_argument('--plot', action='store_true', help='also save PNG; requires matplotlib')
    args = parser.parse_args()
    data = json.loads(args.source.read_text())
    rows = increasing_power(data['rows'])
    stats = {'corrected_median': trend(rows, 'rssi_dgc_db_median'),
             'legacy_median': trend(rows, 'rssi_legacy_db_median')}
    paths = [Path(str(args.out_prefix) + suffix) for suffix in ('.md', '.csv', '.json')]
    png = Path(str(args.out_prefix) + '.png')
    if any(p.exists() for p in paths + ([png] if args.plot else [])):
        parser.error('Choose a new prefix; existing results are not overwritten.')
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    if args.plot:
        plot(rows, png)
    paths[0].write_text(report(args.source, paths[0], data['metadata'], rows, stats, args.plot))
    with paths[1].open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    paths[2].write_text(json.dumps({'source': str(args.source),
        'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'metadata': data['metadata'], 'statistics': stats, 'rows': rows}, indent=2) + '\n')
    print(json.dumps(stats, indent=2))
    print('Saved: ' + ', '.join(str(p) for p in paths + ([png] if args.plot else [])))


if __name__ == '__main__':
    main()
