#!/usr/bin/env bash
# Separate ascending initiator and compatible protocol-4 responder artifacts.
set -eo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
source tools/ncs_env.sh
export XDG_CACHE_HOME="$repo_dir/build/.host_cache"
export CCACHE_DIR="$repo_dir/build/.ccache"
export CMAKE_BUILD_PARALLEL_LEVEL=4
mkdir -p "$XDG_CACHE_HOME"
west build -b decawave_dwm3001cdk -d build/checked_ascending_init samples/twr_checked_ascending_init -- \
  -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" -DCHECKED_N_RESPONDERS=3 -DSWEEP_ATTEMPTS=20
for peer in 0 1 2; do
  west build -b decawave_dwm3001cdk -d "build/checked_ascending_resp$peer" samples/twr_checked_combined_resp -- \
    -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" -DCHECKED_N_RESPONDERS=3 \
    -DSWEEP_ATTEMPTS=20 -DCHECKED_RESP_ID="$peer"
done
python3 - <<'PY'
from pathlib import Path
import datetime,hashlib,json
images=[]
for name,app,role,peer in [('init','twr_checked_ascending_init',1,0)]+[(f'resp{i}','twr_checked_combined_resp',0,i) for i in range(3)]:
    d=Path('build/checked_ascending_'+name)
    commands=json.loads((d/app/'compile_commands.json').read_text())
    command=next(r['command'] for r in commands if r['file'].endswith('/checked.c'))
    for key,value in [('CHECKED_INITIATOR',role),('CHECKED_RESP_ID',peer),('CHECKED_N_RESPONDERS',3),('SWEEP_ATTEMPTS',20)]:
        assert f'-D{key}={value}' in command.split(),(name,key)
    if role: assert '-DCHECKED_BLE=1' in command.split()
    image=d/'merged.hex'
    images.append({'name':'ascending_'+name,'image':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'compile_command':command})
record={'variant':'ascending','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'responders':3,'attempts_per_peer':20,'levels':65,'order':'ascending',
        'first_tx_power':'0x01010101','last_tx_power':'0xFEFEFEFE',
        'responder_tx_power':'0xFEFEFEFE','protocol':4,'images':images}
Path('build/checked_variants_ascending_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print('Verified ascending 01,02,06,...,FE images and three responder IDs.')
PY
