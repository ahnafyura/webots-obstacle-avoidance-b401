#!/usr/bin/env python3
"""Merender slides.html menjadi PDF presentasi.

    python3 slides/buat_slide.py

Angka hasil uji diambil dari docs/stress_results.json, jadi slide selalu sama dengan data.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

R = json.load(open(os.path.join(ROOT, 'docs', 'stress_results.json')))
N, A = R['kebaruan'], R['acak']
rviz_shot = os.path.exists(os.path.join(ROOT, 'docs', 'images', 'rviz2.png'))
values = {
    'runs': str(len(N['runs']) + len(A['runs'])),
    'col': str(N['tabrakan'] + A['tabrakan']),
    'fall': str(N['jatuh'] + A['jatuh']),
    'hours': f"{(N['waktu_total_s'] + A['waktu_total_s']) / 3600:.1f}",
    'dist': f"{N['jarak_total_m'] + A['jarak_total_m']:.0f}",
    'dist_km': f"{(N['jarak_total_m'] + A['jarak_total_m']) / 1000:.1f}",
    'cov_n': f"{N['coverage_rata']:.1f}",
    'cov_a': f"{A['coverage_rata']:.1f}",
    'up': f"{R['peningkatan_persen']:.0f}",
    'rviz_img': 'rviz2.png' if rviz_shot else 'ros_scan_view.png',
    'rviz_cap': ('Tangkapan layar RViz2 saat simulasi berjalan' if rviz_shot
                 else 'Data /scan + /odom yang direkam dari robot'),
}

s = open(os.path.join(HERE, 'slides.html')).read()
for k, v in values.items():
    s = s.replace('{{' + k + '}}', v)
assert '{{' not in s, 'masih ada placeholder yang belum diisi'
tmp = os.path.join(HERE, '_render.html')
open(tmp, 'w').write(s)
pdf = os.path.join(HERE, 'Presentasi_Obstacle_Avoidance_B401.pdf')
subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox',
                '--allow-file-access-from-files', '--no-pdf-header-footer', '--virtual-time-budget=8000',
                '--print-to-pdf=' + pdf, 'file://' + tmp], check=True, stderr=subprocess.DEVNULL)
os.remove(tmp)
print('OK', pdf)
