#!/usr/bin/env bash
# Semak sama ada pakej wujud di registry awam dan lihat metadata asas (umur, muat turun).
# Berguna sebelum menambah pakej yang dicadangkan oleh asisten AI atau artikel yang anda tidak kenal.
#
# Guna:
#   ./semak-pakej.sh nuget Newtonsoft.Json
#   ./semak-pakej.sh packagist phpmailer/phpmailer
# Perlu: curl dan python3.
set -uo pipefail

eko="${1:-}"; nama="${2:-}"
[ -n "$eko" ] && [ -n "$nama" ] || { echo "Guna: $0 nuget|packagist NAMA"; exit 2; }
tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT

case "$eko" in
  nuget)
    id="$(echo "$nama" | tr 'A-Z' 'a-z')"
    kod="$(curl -s -o "$tmp" -w '%{http_code}' "https://api.nuget.org/v3-flatcontainer/$id/index.json")"
    if [ "$kod" != "200" ]; then echo "TIDAK WUJUD di NuGet: $nama (HTTP $kod). Mungkin direka oleh AI."; exit 1; fi
    python3 - "$tmp" "$nama" <<'EOF'
import json, sys, urllib.request
v = json.load(open(sys.argv[1]))["versions"]
q = f"https://azuresearch-usnc.nuget.org/query?q=packageid:{sys.argv[2]}&take=1&prerelease=true"
d = json.load(urllib.request.urlopen(q))["data"]
m = d[0] if d else {}
print(f"WUJUD di NuGet: {sys.argv[2]}")
stabil = [x for x in v if "-" not in x]
print(f"  versi        : {len(v)} (stabil terkini {stabil[-1] if stabil else v[-1]})")
print(f"  jumlah unduh : {m.get('totalDownloads', 'tidak diketahui')}")
print(f"  pemilik      : {', '.join(m.get('owners', [])) or 'tidak diketahui'}")
print(f"  disahkan     : {m.get('verified', 'tidak diketahui')} (awalan ID dipegang oleh pemilik yang disahkan)")
EOF
    ;;
  packagist)
    kod="$(curl -s -o "$tmp" -w '%{http_code}' "https://packagist.org/packages/$nama.json")"
    if [ "$kod" != "200" ]; then echo "TIDAK WUJUD di Packagist: $nama (HTTP $kod). Mungkin direka oleh AI."; exit 1; fi
    python3 - "$tmp" <<'EOF'
import json, sys
p = json.load(open(sys.argv[1]))["package"]
print(f"WUJUD di Packagist: {p['name']}")
print(f"  keterangan   : {p.get('description', '')[:80]}")
print(f"  dicipta      : {p.get('time', 'tidak diketahui')[:10]}")
print(f"  jumlah unduh : {p.get('downloads', {}).get('total', 'tidak diketahui')}")
print(f"  bintang      : {p.get('favers', 'tidak diketahui')}")
print(f"  versi        : {len(p.get('versions', {}))}")
print(f"  ditinggalkan : {p.get('abandoned') or 'tidak'}")
EOF
    ;;
  *) echo "Ekosistem tidak disokong: $eko (guna nuget atau packagist)"; exit 2 ;;
esac
