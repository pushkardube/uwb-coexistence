#!/usr/bin/env bash
# Experimental forks stay independent of the checked baseline and of each other.
set -eo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
source tools/ncs_env.sh
export XDG_CACHE_HOME="$repo_dir/build/.host_cache"
export CCACHE_DIR="$repo_dir/build/.ccache"
export CMAKE_BUILD_PARALLEL_LEVEL=4
mkdir -p "$XDG_CACHE_HOME"
variant="${1:-all}"
if [[ "$variant" != all && "$variant" != power && "$variant" != multi ]]; then
  echo 'Usage: bash tools/build_checked_variants.sh [all|power|multi]' >&2
  exit 1
fi
build_one() {
  local app="$1" output="$2"
  shift 2
  west build -b decawave_dwm3001cdk -d "build/$output" "samples/$app" -- \
    -DUSER_CACHE_DIR="$XDG_CACHE_HOME/zephyr" "$@"
}
if [[ "$variant" == power || "$variant" == all ]]; then
  build_one twr_checked_power_init checked_power_init
  build_one twr_checked_power_resp checked_power_resp
fi
if [[ "$variant" == multi || "$variant" == all ]]; then
  build_one twr_checked_multi_init checked_multi_init -DCHECKED_N_RESPONDERS=2
  build_one twr_checked_multi_resp checked_multi_resp0 -DCHECKED_RESP_ID=0
  build_one twr_checked_multi_resp checked_multi_resp1 -DCHECKED_RESP_ID=1
fi
python3 - "$variant" <<'PY'
from pathlib import Path
import hashlib,json,datetime,sys
which=sys.argv[1]
images=[]
for name,app in [('power_init','power_init'),('power_resp','power_resp'),('multi_init','multi_init'),('multi_resp0','multi_resp'),('multi_resp1','multi_resp')]:
    if which!='all' and not name.startswith(which):continue
    directory=Path('build/checked_'+name)
    image=directory/'merged.hex'
    rows=json.loads((directory/('twr_checked_'+app)/'compile_commands.json').read_text())
    command=next(row['command'] for row in rows if row['file'].endswith('/checked.c'))
    role=int(name.endswith('init'))
    assert '-DCHECKED_INITIATOR='+str(role) in command.split()
    if name.startswith('multi_resp'):
        assert '-DCHECKED_RESP_ID='+name[-1] in command.split()
    images.append({'name':name,'image':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'compile_command':command})
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variant':which,'images':images}
Path('build/checked_variants_'+which+'_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Verified images and compiled role/ID settings; saved manifest.')
PY
