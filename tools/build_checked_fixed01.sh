#!/usr/bin/env bash
# Separate BLE initiator and two responders; fixed 01010101 in both directions.
set -eo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
source tools/ncs_env.sh
export XDG_CACHE_HOME="$repo_dir/build/.host_cache"
export CCACHE_DIR="$repo_dir/build/.ccache"
export CMAKE_BUILD_PARALLEL_LEVEL=4
mkdir -p "$XDG_CACHE_HOME"
west build -b decawave_dwm3001cdk -d build/checked_fixed01_init samples/twr_checked_fixed01_init -- \
  -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" -DCHECKED_N_RESPONDERS=2 -DSWEEP_ATTEMPTS=20
for peer in 0 1; do
  west build -b decawave_dwm3001cdk -d "build/checked_fixed01_resp$peer" samples/twr_checked_fixed01_resp -- \
    -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" -DCHECKED_N_RESPONDERS=2 \
    -DSWEEP_ATTEMPTS=20 -DCHECKED_RESP_ID="$peer"
done
python3 - <<'PY'
from pathlib import Path
import datetime,hashlib,json
images=[]
for name,app,role,peer in [('init','init',1,0),('resp0','resp',0,0),('resp1','resp',0,1)]:
    directory=Path('build/checked_fixed01_'+name)
    commands=json.loads((directory/('twr_checked_fixed01_'+app)/'compile_commands.json').read_text())
    command=next(r['command'] for r in commands if r['file'].endswith('/checked.c'))
    for key,value in [('CHECKED_INITIATOR',role),('CHECKED_RESP_ID',peer),('CHECKED_N_RESPONDERS',2),('SWEEP_ATTEMPTS',20),('CHECKED_RSSI',1)]:
        assert f'-D{key}={value}' in command.split(),(name,key)
    if role: assert '-DCHECKED_BLE=1' in command.split()
    image=directory/'merged.hex'
    images.append({'name':'fixed01_'+name,'image':str(image),
                   'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'compile_command':command})
record={'variant':'fixed01','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'responders':2,'attempts_per_peer':20,'levels':1,'protocol':5,
        'initiator_tx_power':'0x01010101','responder_tx_power':'0x01010101',
        'ble_name':'UWB-COEX-INIT','images':images}
Path('build/checked_variants_fixed01_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print('Verified fixed01 BLE initiator and responders 0/1; independent protocol 5.')
PY
