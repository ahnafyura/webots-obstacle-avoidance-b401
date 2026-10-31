#!/usr/bin/env python3
"""Merender slides.html menjadi PDF presentasi (gaya deck magang Barunastra).

    python3 slides/buat_slide.py

Angka hasil uji diambil dari docs/stress_results.json, jadi slide selalu sama dengan data.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STARTS = ["(-1.2, -1.2)", "(1.2, 1.2)", "(0.0, 0.7)", "(1.2, -0.5)",
          "(-1.2, 1.2)", "(0.6, -0.5)", "(-0.3, -1.2)", "(0.9, 0.3)"]

res = json.load(open(os.path.join(ROOT, 'docs', 'stress_results.json')))
rows = ''.join(
    f"<tr><td>{i + 1}</td><td>{STARTS[i]}</td><td>{r['jarak_tempuh_m']:.1f} m</td>"
    f"<td><b style=\"color:#1f9d55\">{r['tabrakan']}</b></td><td>{r['coverage_persen']:.1f} %</td></tr>"
    for i, r in enumerate(res))
values = {'run_rows': rows,
          'min_clear': f"{min(r['clearance_min_m'] for r in res) * 100:.1f}"}

s = open(os.path.join(HERE, 'slides.html')).read()
for k, v in values.items():
    s = s.replace('{{' + k + '}}', v)
tmp = os.path.join(HERE, '_render.html')
open(tmp, 'w').write(s)
pdf = os.path.join(HERE, 'Presentasi_Obstacle_Avoidance_B401.pdf')
subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox',
                '--allow-file-access-from-files', '--no-pdf-header-footer', '--virtual-time-budget=8000',
                '--print-to-pdf=' + pdf, 'file://' + tmp], check=True, stderr=subprocess.DEVNULL)
os.remove(tmp)
print('OK', pdf)
