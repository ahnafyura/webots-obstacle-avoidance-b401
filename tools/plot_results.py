"""Membuat grafik hasil pengujian untuk dokumentasi (docs/images/)."""
import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'images')
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'font.family': 'DejaVu Sans'})


def load(run_dir):
    with open(os.path.join(run_dir, 'trajectory.csv')) as f:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    obs = json.load(open(os.path.join(run_dir, 'obstacles.json')))
    summ = json.load(open(os.path.join(run_dir, 'summary.json')))
    return rows, obs, summ


def draw_arena(ax, obs):
    ax.add_patch(Rectangle((-1.5, -1.5), 3, 3, fill=False, lw=2.5, ec='#333'))
    for o in obs:
        if o['type'] == 'cylinder':
            ax.add_patch(Circle((o['x'], o['y']), o['r'], fc='#9aa3ad', ec='#444'))
        else:
            c, s = math.cos(o['yaw']), math.sin(o['yaw'])
            pts = []
            for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                lx, ly = dx * o['sx'] / 2, dy * o['sy'] / 2
                pts.append((o['x'] + c * lx - s * ly, o['y'] + s * lx + c * ly))
            ax.add_patch(Polygon(pts, fc='#9aa3ad', ec='#444'))
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.grid(alpha=0.25)


stress = os.path.join(ROOT, 'logs', 'stress')
runs = sorted([d for d in os.listdir(stress) if os.path.isdir(os.path.join(stress, d))],
              key=lambda d: int(d.split('_')[1]))

# 1. Lintasan satu run (warna = waktu)
rows, obs, summ = load(os.path.join(stress, runs[0]))
fig, ax = plt.subplots(figsize=(6.2, 6))
draw_arena(ax, obs)
sc = ax.scatter([r['x'] for r in rows], [r['y'] for r in rows], c=[r['t'] for r in rows],
                s=2, cmap='viridis')
ax.plot(rows[0]['x'], rows[0]['y'], 'go', ms=9, label='start')
ax.plot(rows[-1]['x'], rows[-1]['y'], 'rs', ms=8, label='akhir')
fig.colorbar(sc, ax=ax, label='waktu (s)', shrink=0.8)
ax.legend(loc='upper left', fontsize=8)
ax.set_title(f"Lintasan robot {summ['waktu_s']:.0f} s - {summ['tabrakan']} tabrakan, "
             f"{summ['jarak_tempuh_m']:.0f} m")
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'trajectory_run1.png'), dpi=160)
plt.close(fig)

# 2. Semua run (8 posisi awal)
fig, ax = plt.subplots(figsize=(6.2, 6))
draw_arena(ax, obs)
cmap = plt.get_cmap('tab10')
for i, d in enumerate(runs):
    rows, _, s = load(os.path.join(stress, d))
    ax.plot([r['x'] for r in rows], [r['y'] for r in rows], lw=0.6, alpha=0.75, color=cmap(i),
            label=f"run {i + 1}")
    ax.plot(rows[0]['x'], rows[0]['y'], 'o', color=cmap(i), ms=6, mec='k')
ax.legend(loc='upper left', fontsize=7, ncol=2)
ax.set_title('Lintasan 8 pengujian (posisi awal berbeda, 300 s/run)')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'trajectory_all.png'), dpi=160)
plt.close(fig)

# 3. Clearance terhadap waktu (run 1) + histogram semua run
rows, _, _ = load(os.path.join(stress, runs[0]))
allc = []
for d in runs:
    allc += [r['clearance'] for r in load(os.path.join(stress, d))[0]]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
a1.plot([r['t'] for r in rows], [r['clearance'] for r in rows], lw=0.8, color='#1f77b4')
a1.axhline(0, color='r', ls='--', lw=1, label='batas tabrakan')
a1.set_xlabel('waktu (s)')
a1.set_ylabel('clearance (m)')
a1.set_title('Jarak aman robot ke obstacle terdekat (run 1)')
a1.legend(fontsize=8)
a1.grid(alpha=0.3)
a2.hist(allc, bins=60, color='#2ca02c', alpha=0.85)
a2.axvline(0, color='r', ls='--', lw=1)
a2.set_xlabel('clearance (m)')
a2.set_ylabel('jumlah sampel')
a2.set_title('Distribusi clearance - seluruh 8 run')
a2.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'clearance.png'), dpi=160)
plt.close(fig)

# 4. Diagram konsep koridor (penjelasan algoritma)
fig, ax = plt.subplots(figsize=(6, 4.6))
ax.set_aspect('equal')
ax.add_patch(Rectangle((-0.08, -0.06), 0.16, 0.12, fc='#2b5fd9', ec='k', zorder=3))
ax.add_patch(Circle((0, 0), 0.02, fc='r', zorder=4))
hw = 0.13
for th, col, lab in [(0.0, '#d62728', 'theta = 0 (terblokir)'),
                     (math.radians(35), '#2ca02c', 'theta = 35 deg (dipilih)')]:
    c, s = math.cos(th), math.sin(th)
    L = 1.0
    pts = [(-s * hw, c * hw), (L * c - s * hw, L * s + c * hw), (L * c + s * hw, L * s - c * hw), (s * hw, -c * hw)]
    ax.add_patch(Polygon(pts, fc=col, alpha=0.18, ec=col, label=lab))
    ax.annotate('', xy=(L * c, L * s), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color=col, lw=2))
ax.add_patch(Rectangle((0.45, -0.25), 0.25, 0.35, fc='#9aa3ad', ec='#444', label='obstacle'))
import random
random.seed(1)
for _ in range(25):
    y = random.uniform(-0.25, 0.10)
    ax.plot(0.45, y, 'k.', ms=3)
ax.plot([0, 0.45], [0, -0.05], 'k:', lw=0.8)
ax.text(0.2, -0.1, 'sinar lidar', fontsize=8)
ax.set_xlim(-0.2, 1.1)
ax.set_ylim(-0.45, 0.8)
ax.legend(loc='upper left', fontsize=8)
ax.set_title('Corridor Gap Selection: jarak bebas dihitung per koridor')
ax.set_xlabel('x robot (m)')
ax.set_ylabel('y robot (m)')
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'corridor_concept.png'), dpi=160)
plt.close(fig)

# 5. Tabel ringkasan sebagai JSON (dibaca oleh generator PDF)
table = []
for i, d in enumerate(runs):
    s = json.load(open(os.path.join(stress, d, 'summary.json')))
    table.append(s)
json.dump(table, open(os.path.join(ROOT, 'docs', 'stress_results.json'), 'w'), indent=2)
print('grafik tersimpan di', OUT)

# 6. Diagram state machine
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.axis('off')
ax.set_xlim(0, 10)
ax.set_ylim(0, 4.4)
nodes = {'JELAJAH': (1.6, 2.2, '#cfe8cf'), 'MUNDUR': (5.0, 3.4, '#f6d0cf'), 'PUTAR': (8.4, 2.2, '#cfdcf6')}
for k, (x, y, c) in nodes.items():
    ax.add_patch(FancyBboxPatch((x - 1.05, y - 0.42), 2.1, 0.84, boxstyle='round,pad=0.08', fc=c, ec='k', lw=1.4))
    ax.text(x, y, k, ha='center', va='center', fontsize=12, weight='bold')


def arrow(p, q, text, tx, ty, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=16, lw=1.3,
                                 connectionstyle=f'arc3,rad={rad}', color='#333'))
    ax.text(tx, ty, text, ha='center', va='center', fontsize=8.2,
            bbox=dict(fc='white', ec='none', alpha=0.9))


arrow((2.3, 2.65), (3.95, 3.4), 'obstacle < 13 cm\natau robot macet', 2.6, 3.55)
arrow((6.05, 3.4), (7.7, 2.65), 'setelah 0.6 s\n(atau belakang sempit)', 7.4, 3.55)
arrow((2.65, 2.05), (7.35, 2.05), 'tidak ada koridor bebas > 22 cm', 5.0, 2.3)
arrow((7.35, 1.8), (2.65, 1.8), 'koridor depan bebas > 45 cm  (atau timeout 4 s)', 5.0, 1.05, rad=-0.3)
ax.text(1.6, 0.35, 'JELAJAH: pilih heading terbaik (Corridor Gap Selection),\nkecepatan diskalakan jarak bebas depan',
        ha='center', fontsize=8)
ax.text(8.4, 0.35, 'PUTAR: rotasi di tempat ke sisi\nyang lebih lapang', ha='center', fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'state_machine.png'), dpi=160)
plt.close(fig)
