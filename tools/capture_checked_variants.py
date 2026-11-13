#!/usr/bin/env python3
"""Capture selected boards; optional explicit reset of these boards only."""
import argparse
import datetime
import json
from pathlib import Path
import selectors
import subprocess
import time
import serial
from analyze_checked_variants import analyze


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant', choices=['power', 'multi', 'combined'], required=True)
    p.add_argument('--init', required=True, help='initiator probe serial')
    p.add_argument('--responder', action='append', required=True, help='repeat for each selected responder')
    p.add_argument('--seconds', type=float, default=60)
    p.add_argument('--reset', action='store_true')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if args.seconds <= 0:
        p.error('--seconds must be positive')
    ids = [args.init] + args.responder
    if not all(v.isdigit() for v in ids) or len(set(map(int, ids))) != len(ids):
        p.error('use distinct numeric probe IDs')
    root = args.out or Path('build') / (args.variant + '_capture_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    root.mkdir(parents=True, exist_ok=False)
    selector = selectors.DefaultSelector()
    handles = []
    try:
        for index, sn in enumerate(ids):
            role = 'init' if index == 0 else f'resp{index-1}'
            path = Path('/dev/serial/by-id') / f'usb-SEGGER_J-Link_{int(sn):012d}-if00'
            port = serial.Serial(str(path), 115200, timeout=0, exclusive=True)
            handles.append((port, None))
            port.dtr = True
            port.reset_input_buffer()
            file = (root / (role + '.log')).open('wb')
            handles[-1] = (port, file)
            selector.register(port, selectors.EVENT_READ, file)
        print('CAPTURE_DIR=' + str(root), flush=True)
        if args.reset:
            # Reset only the explicitly selected responders, then initiator.
            command = 'source tools/ncs_env.sh; export NRFUTIL_HOME="$PWD/build/.nrfutil"; nrfutil device reset --serial-number "$1"'
            for sn in args.responder + [args.init]:
                subprocess.run(['bash', '-c', command, 'reset', sn], check=True)
        start = last = time.monotonic()
        while time.monotonic() - start < args.seconds:
            for key, _ in selector.select(timeout=0.2):
                data = key.fileobj.read(8192)
                if data:
                    key.data.write(data)
                    key.data.flush()
            if time.monotonic() - last >= 25:
                print(f'CAPTURE_SECONDS={time.monotonic()-start:.1f}', flush=True)
                last = time.monotonic()
        elapsed = time.monotonic() - start
    finally:
        for port, file in handles:
            port.close()
            if file:
                file.close()
        selector.close()
    manifest = {'variant': args.variant, 'seconds': elapsed, 'init': args.init,
                'responders': args.responder, 'reset': args.reset}
    (root / 'capture.json').write_text(json.dumps(manifest, indent=2) + '\n')
    summary, _ = analyze(root / 'init.log')
    (root / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
