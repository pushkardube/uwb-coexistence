#!/usr/bin/env bash
# Build initiator and uniquely addressed responders with verified sysbuild settings.
set -eo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
responder_count="${1:-2}"
attempts_per_peer="${2:-10}"
python3 - "$responder_count" "$attempts_per_peer" <<'PY'
import sys
try:n,attempts=map(int,sys.argv[1:])
except ValueError:raise SystemExit('Usage: bash tools/build_checked_combined.sh [responders:1..16 [attempts:1..10000]]')
if not (1<=n<=16 and 1<=attempts<=10000):raise SystemExit('Invalid responder count or attempt budget.')
PY
source tools/ncs_env.sh
export XDG_CACHE_HOME="$repo_dir/build/.host_cache"
export CCACHE_DIR="$repo_dir/build/.ccache"
export CMAKE_BUILD_PARALLEL_LEVEL=4
mkdir -p "$XDG_CACHE_HOME"
build_one() {
  local role="$1" output="$2" peer_id="$3"
  west build -b decawave_dwm3001cdk -d "build/checked_combined_$output" \
    "samples/twr_checked_combined_$role" -- \
    -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" \
    -DCHECKED_N_RESPONDERS="$responder_count" -DCHECKED_RESP_ID="$peer_id" \
    -DSWEEP_ATTEMPTS="$attempts_per_peer"
}
build_one init init 0
for ((peer_id=0; peer_id<responder_count; ++peer_id)); do
  build_one resp "resp$peer_id" "$peer_id"
done
python3 - "$responder_count" "$attempts_per_peer" <<'PY'
from pathlib import Path
import datetime,hashlib,json,re,sys
n,attempts=map(int,sys.argv[1:])
images=[]
for name,app,role,peer in [('init','init',1,0)]+[(f'resp{i}','resp',0,i) for i in range(n)]:
    directory=Path('build/checked_combined_'+name)
    rows=json.loads((directory/('twr_checked_combined_'+app)/'compile_commands.json').read_text())
    command=next(row['command'] for row in rows if row['file'].endswith('/checked.c'))
    for key,value in [('CHECKED_INITIATOR',role),('CHECKED_RESP_ID',peer),
                      ('CHECKED_N_RESPONDERS',n),('SWEEP_ATTEMPTS',attempts)]:
        assert f'-D{key}={value}' in command.split(),(name,key,command)
    image=directory/'merged.hex'
    images.append({'name':'combined_'+name,'image':str(image),
                   'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                   'compile_command':command})
levels=int(re.search(r'#define SWEEP_LEVELS (\d+)u',Path('samples/twr_checked_combined_common/combined_plan.h').read_text())[1])
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'variant':'combined','responders':n,'attempts_per_peer':attempts,'levels':levels,
          'first_tx_power':'0x01010101','responder_tx_power':'0xFEFEFEFE','images':images}
Path('build/checked_variants_combined_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Verified {n+1} images: {levels} settings, starting at 01010101; {attempts} attempts per peer per setting.')
PY
