#!/usr/bin/env python3
"""Ringkaskan laporan JSON ZAP: senarai isyarat mengikut risiko, dengan URL yang terjejas.

Guna: python3 ringkas-zap.py zap-hasil/pelan.json
"""
import json
import sys

RISIKO = {"3": "TINGGI", "2": "SEDERHANA", "1": "RENDAH", "0": "MAKLUMAT"}

d = json.load(open(sys.argv[1]))
baris = []
for tapak in d["site"]:
    for a in tapak["alerts"]:
        url = sorted({i["uri"].split("?")[0].replace(tapak["@name"], "") or "/" for i in a["instances"]})
        baris.append((a["riskcode"], a["name"], len(a["instances"]), url[:4]))
for kod, nama, n, url in sorted(baris, key=lambda b: (-int(b[0]), b[1])):
    print(f"{RISIKO[kod]:<10} {nama}  (x{n})  {', '.join(url)}")
print(f"\nJumlah: {len(baris)} jenis isyarat; tinggi {sum(1 for b in baris if b[0] == '3')}, "
      f"sederhana {sum(1 for b in baris if b[0] == '2')}")
