#!/usr/bin/env bash
# Explicit targets only: no discovery-based assignment and no rebuilding.
set -eo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
if [[ $# -lt 3 ]]; then
  echo 'Usage: bash tools/flash_checked_variant.sh power INIT_SERIAL RESP_SERIAL' >&2
  echo '   or: bash tools/flash_checked_variant.sh multi INIT_SERIAL RESP0_SERIAL [RESP1_SERIAL]' >&2
  echo '   or: bash tools/flash_checked_variant.sh combined INIT_SERIAL RESP0_SERIAL [RESP1_SERIAL ...]' >&2
  echo '   or: bash tools/flash_checked_variant.sh ble INIT_SERIAL RESP0_SERIAL [RESP1_SERIAL ...]' >&2
  echo '   or: bash tools/flash_checked_variant.sh fixed01 INIT_SERIAL RESP0_SERIAL RESP1_SERIAL' >&2
  exit 1
fi
variant="$1"; shift
if [[ "$variant" == power && $# != 2 ]] || [[ "$variant" == multi && $# != 2 && $# != 3 ]] || [[ "$variant" == fixed01 && $# != 3 ]] || [[ ( "$variant" == combined || "$variant" == ble ) && ( $# -lt 2 || $# -gt 17 ) ]] || [[ "$variant" != power && "$variant" != multi && "$variant" != combined && "$variant" != ble && "$variant" != fixed01 ]]; then
  echo 'Invalid variant/target count.' >&2
  exit 1
fi
source tools/ncs_env.sh
if [[ -d "$repo_dir/build/.nrfutil/installed" ]]; then
  export NRFUTIL_HOME="$repo_dir/build/.nrfutil"
fi
init_probe="$1"; resp0_probe="$2"; resp1_probe="${3:-}"
python3 - "$variant" "$@" <<'PY'
from pathlib import Path
import hashlib,json,sys
variant=sys.argv[1]
try:ids=[str(int(x)) for x in sys.argv[2:]]
except ValueError:raise SystemExit('Use numeric probe IDs.')
if len(ids)!=len(set(ids)):raise SystemExit('Select distinct probes.')
present=set()
for p in Path('/sys/bus/usb/devices').iterdir():
    try:
        if (p/'idVendor').read_text().strip()=='1366':present.add(str(int((p/'serial').read_text().strip())))
    except (OSError,ValueError):pass
if not set(ids)<=present:raise SystemExit('Some selected probes are not currently enumerated.')
paths=[Path('build/checked_variants_'+variant+'_manifest.json')]
if variant not in ('combined','ble','fixed01'):paths.append(Path('build/checked_variants_all_manifest.json'))
manifests=[p for p in paths if p.exists()]
if not manifests:
    builder='build_checked_fixed01.sh' if variant=='fixed01' else 'build_checked_ble.sh' if variant=='ble' else 'build_checked_combined.sh' if variant=='combined' else 'build_checked_variants.sh'
    raise SystemExit('Run tools/'+builder+' first.')
manifest=json.loads(max(manifests,key=lambda p:p.stat().st_mtime).read_text())
needed={variant+'_init',variant+('_resp' if variant=='power' else '_resp0')}
if variant in ('multi','combined','ble','fixed01'):
    needed.update(f'{variant}_resp{i}' for i in range(len(ids)-1))
records={r['name']:r for r in manifest['images']}
if not needed<=records.keys():raise SystemExit('Build the selected responder IDs before flashing.')
for name in needed:
    r=records[name]
    if hashlib.sha256(Path(r['image']).read_bytes()).hexdigest()!=r['sha256']:
        raise SystemExit('Image changed; run the build script to refresh manifest: '+name)
print('Artifact hashes and selected probe IDs checked.')
PY
log_dir="$(mktemp -d "$repo_dir/build/${variant}_flash.XXXXXXXX")"
printf 'variant=%s\ninitiator=%s\n' "$variant" "$init_probe" | tee "$log_dir/targets.txt"
peer_index=0
for probe_id in "${@:2}"; do
  printf 'responder%s=%s\n' "$peer_index" "$probe_id" | tee -a "$log_dir/targets.txt"
  peer_index=$((peer_index+1))
done
if [[ "$variant" == power ]]; then
  west flash --skip-rebuild -d build/checked_power_resp -r nrfutil --dev-id "$resp0_probe" 2>&1 | tee "$log_dir/resp0.log"
else
  peer_index=0
  for probe_id in "${@:2}"; do
    west flash --skip-rebuild -d "build/checked_${variant}_resp${peer_index}" -r nrfutil --dev-id "$probe_id" 2>&1 | tee "$log_dir/resp${peer_index}.log"
    peer_index=$((peer_index+1))
  done
fi
west flash --skip-rebuild -d "build/checked_${variant}_init" -r nrfutil --dev-id "$init_probe" 2>&1 | tee "$log_dir/init.log"
echo "Flash commands succeeded; logs: $log_dir"
