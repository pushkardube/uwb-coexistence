#!/usr/bin/env bash
# BLE aggregator initiator + plain checked responders; no hardware is flashed.
set -eo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
peer_count="${1:-1}"
attempt_budget="${2:-20}"
python3 - "$peer_count" "$attempt_budget" <<'PY'
import sys
n,b=map(int,sys.argv[1:])
if not (1<=n<=16 and 1<=b<=10000):raise SystemExit('Use 1..16 responders and 1..10000 attempts per peer per level.')
PY
source tools/ncs_env.sh
export XDG_CACHE_HOME="$repo_dir/build/.host_cache"
export CCACHE_DIR="$repo_dir/build/.ccache"
export CMAKE_BUILD_PARALLEL_LEVEL=4
mkdir -p "$XDG_CACHE_HOME"
west build -b decawave_dwm3001cdk -d build/checked_ble_init samples/twr_checked_ble_init -- \
  -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" -DCHECKED_N_RESPONDERS="$peer_count" \
  -DSWEEP_ATTEMPTS="$attempt_budget"
for ((peer=0; peer<peer_count; ++peer)); do
  west build -b decawave_dwm3001cdk -d "build/checked_ble_resp$peer" samples/twr_checked_combined_resp -- \
    -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" -DCHECKED_N_RESPONDERS="$peer_count" \
    -DSWEEP_ATTEMPTS="$attempt_budget" -DCHECKED_RESP_ID="$peer"
done
python3 - "$peer_count" "$attempt_budget" <<'PY'
from pathlib import Path
import sys,json,hashlib,datetime
n,b=map(int,sys.argv[1:]);images=[]
for name,app,role,peer in [('init','twr_checked_ble_init',1,0)]+[(f'resp{i}','twr_checked_combined_resp',0,i) for i in range(n)]:
    directory=Path('build/checked_ble_'+name)
    commands=json.loads((directory/app/'compile_commands.json').read_text())
    command=next(r['command'] for r in commands if r['file'].endswith('/checked.c'))
    for key,value in [('CHECKED_INITIATOR',role),('CHECKED_RESP_ID',peer),('CHECKED_N_RESPONDERS',n),('SWEEP_ATTEMPTS',b)]:
        assert f'-D{key}={value}' in command.split(),(name,key)
    if role:assert '-DCHECKED_BLE=1' in command.split()
    image=directory/'merged.hex'
    images.append({'name':'ble_'+name,'image':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'compile_command':command})
record={'variant':'ble','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'responders':n,'attempts_per_peer':b,'levels':65,'ble_name':'UWB-COEX-INIT','images':images}
Path('build/checked_variants_ble_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print('Verified BLE initiator and addressed responder images; manifest saved.')
PY
