"""Membuat grafik hasil pengujian humanoid untuk laporan & slide (docs/images/).

Membaca logs/set{1,2}_{kebaruan,acak}/run_*/ hasil tools/stress_test.sh.
    python3 tools/plot_results.py
"""
import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'images')
LOGS = os.path.join(ROOT, 'logs')
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'font.family': 'DejaVu Sans'})
sys.path.insert(0, os.path.join(ROOT, 'controllers', 'humanoid_avoidance'))

ARENA = 2.5
GRID = 0.2
R_ROBOT = 0.18
C_NOV, C_RND = '#0b5cad', '#c8102e'


def load(run_dir):
    with open(os.path.join(run_dir, 'trajectory.csv')) as f:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    return rows, json.load(open(os.path.join(run_dir, 'obstacles.json'))), \
        json.load(open(os.path.join(run_dir, 'summary.json')))


def runs(name):
    d = os.path.join(LOGS, name)
    return [os.path.join(d, f'run_{i}') for i in range(1, 9)]


def obstacle_distance(px, py, o):
    if o['type'] == 'cylinder':
        return math.hypot(px - o['x'], py - o['y']) - o['r']
    c, s = math.cos(-o['yaw']), math.sin(-o['yaw'])
    dx, dy = px - o['x'], py - o['y']
    lx, ly = c * dx - s * dy, s * dx + c * dy
    qx, qy = abs(lx) - o['sx'] / 2, abs(ly) - o['sy'] / 2
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0)


def free_cells(obs):
    n = int(2 * ARENA / GRID)
    out = set()
    for ix in range(n):
        for iy in range(n):
            cx, cy = -ARENA + (ix + 0.5) * GRID, -ARENA + (iy + 0.5) * GRID
            d = min([ARENA - max(abs(cx), abs(cy))] + [obstacle_distance(cx, cy, o) for o in obs])
            if d > R_ROBOT:
                out.add((ix, iy))
    return out


def coverage_curve(rows, cells, step=10.0):
    seen, curve, nxt = set(), [], 0.0
    for r in rows:
        seen.add((int((r['x'] + ARENA) / GRID), int((r['y'] + ARENA) / GRID)))
        if r['t'] >= nxt:
            curve.append((r['t'], 100.0 * len(seen & cells) / len(cells)))
            nxt += step
    return curve


def draw_arena(ax, obs):
    ax.add_patch(Rectangle((-ARENA, -ARENA), 2 * ARENA, 2 * ARENA, fill=False, lw=2.5, ec='#333'))
    for o in obs:
        if o['type'] == 'cylinder':
            ax.add_patch(Circle((o['x'], o['y']), o['r'], fc='#9aa3ad', ec='#444'))
        else:
            c, s = math.cos(o['yaw']), math.sin(o['yaw'])
            pts = [(o['x'] + c * dx * o['sx'] / 2 - s * dy * o['sy'] / 2,
                    o['y'] + s * dx * o['sx'] / 2 + c * dy * o['sy'] / 2)
                   for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
            ax.add_patch(Polygon(pts, fc='#9aa3ad', ec='#444'))
    ax.set_xlim(-2.65, 2.65)
    ax.set_ylim(-2.65, 2.65)
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.grid(alpha=0.2)


sets = {m: runs(f'set1_{m}') + runs(f'set2_{m}') for m in ('kebaruan', 'acak')}
data = {m: [load(d) for d in sets[m]] for m in sets}
obs = data['kebaruan'][0][1]
cells = free_cells(obs)

# 1. Lintasan: kebaruan vs acak (set 1)
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
for ax, m, col, title in ((axes[0], 'acak', C_RND, 'Mode ACAK (pembanding)'),
                          (axes[1], 'kebaruan', C_NOV, 'Mode KEBARUAN (dipakai)')):
    draw_arena(ax, obs)
    cov = []
    for rows, _, s in data[m][:8]:
        ax.plot([r['x'] for r in rows], [r['y'] for r in rows], lw=0.7, alpha=0.6, color=col)
        ax.plot(rows[0]['x'], rows[0]['y'], 'o', ms=5, color='k')
        cov.append(s['coverage_persen'])
    ax.set_title(f'{title}: coverage rata-rata {sum(cov) / len(cov):.1f} %')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'trajectory_compare.png'), dpi=150)
plt.close(fig)

# 2. Lintasan semua 16 run kebaruan
fig, ax = plt.subplots(figsize=(6.4, 6.2))
draw_arena(ax, obs)
cmap = plt.get_cmap('tab20')
for i, (rows, _, s) in enumerate(data['kebaruan']):
    ax.plot([r['x'] for r in rows], [r['y'] for r in rows], lw=0.6, alpha=0.7, color=cmap(i % 20))
    ax.plot(rows[0]['x'], rows[0]['y'], 'o', ms=5, color=cmap(i % 20), mec='k')
ax.set_title('Lintasan 16 uji mode kebaruan (16 posisi awal, 10 menit/uji)')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'trajectory_all.png'), dpi=150)
plt.close(fig)

# 3. Coverage terhadap waktu (rata-rata 16 run tiap mode)
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for m, col in (('kebaruan', C_NOV), ('acak', C_RND)):
    curves = [coverage_curve(rows, cells) for rows, _, _ in data[m]]
    n = min(len(c) for c in curves)
    t = [curves[0][k][0] / 60 for k in range(n)]
    mean = [sum(c[k][1] for c in curves) / len(curves) for k in range(n)]
    lo = [min(c[k][1] for c in curves) for k in range(n)]
    hi = [max(c[k][1] for c in curves) for k in range(n)]
    ax.plot(t, mean, color=col, lw=2.2, label=f'{m} (rata-rata)')
    ax.fill_between(t, lo, hi, color=col, alpha=0.12)
ax.set_xlabel('waktu (menit)')
ax.set_ylabel('coverage arena (%)')
ax.set_title('Coverage terhadap waktu, 16 uji per mode (area = rentang min-maks)')
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'coverage_time.png'), dpi=150)
plt.close(fig)

# 4. Coverage per uji
fig, ax = plt.subplots(figsize=(10, 3.8))
cn = [s['coverage_persen'] for _, _, s in data['kebaruan']]
ca = [s['coverage_persen'] for _, _, s in data['acak']]
xs = range(1, 17)
ax.bar([x - 0.2 for x in xs], ca, width=0.4, color=C_RND, label=f'acak (rata-rata {sum(ca) / 16:.1f} %)')
ax.bar([x + 0.2 for x in xs], cn, width=0.4, color=C_NOV, label=f'kebaruan (rata-rata {sum(cn) / 16:.1f} %)')
ax.set_xticks(list(xs))
ax.set_xlabel('uji ke- (1-8: posisi awal set 1, 9-16: set 2)')
ax.set_ylabel('coverage (%)')
ax.set_title('Coverage tiap uji, 10 menit, posisi awal sama untuk kedua mode')
ax.legend(loc='upper left', fontsize=9)
ax.grid(axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'coverage_bar.png'), dpi=150)
plt.close(fig)

# 5. Clearance
allc = [r['clearance'] for m in data for rows, _, _ in data[m] for r in rows]
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.hist(allc, bins=70, color='#2ca02c', alpha=0.85)
ax.axvline(0, color='r', ls='--', lw=1)
ax.set_xlabel('clearance terhadap lingkaran pembungkus r = 0.18 m (m)')
ax.set_ylabel('jumlah sampel')
ax.set_title('Distribusi jarak aman, seluruh 32 uji (5.3 jam simulasi)')
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'clearance.png'), dpi=150)
plt.close(fig)

# 6. Siklus jalan: sudut sendi per siklus (lurus vs belok kiri)
from gait import LOOP_END, LOOP_START, Clip, load_motion, turn_pulse  # noqa: E402
mdir = os.path.join(ROOT, 'controllers', 'humanoid_avoidance', 'motions')
loop = Clip(*load_motion(os.path.join(mdir, 'Forwards50.motion'), LOOP_START, LOOP_END + 1))
left = turn_pulse(loop, +1)
fig, axes = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True)
t = [f[0] for f in loop.frames]
for jname, col in (('LHipPitch', '#0b5cad'), ('LKneePitch', '#1f9d55'), ('LAnklePitch', '#e08a00'),
                   ('LHipRoll', '#7a3fb0')):
    i = loop.joints.index(jname)
    axes[0].plot(t, [f[1][i] for f in loop.frames], color=col, lw=1.8, label=jname)
axes[0].set_ylabel('sudut (rad)')
axes[0].set_title('Satu siklus jalan (2 langkah, 2.04 s): sendi kaki kiri', pad=26)
axes[0].legend(fontsize=8, ncol=4, loc='lower center', bbox_to_anchor=(0.5, 1.0), frameon=False)
axes[0].grid(alpha=0.3)
i = loop.joints.index('LHipYawPitch')
axes[1].plot(t, [f[1][i] for f in loop.frames], color='#555', lw=2, label='jalan lurus')
axes[1].plot(t, [f[1][i] for f in left.frames], color=C_NOV, lw=2, label='belok kiri (pulsa 0.25 rad)')
axes[1].set_ylabel('HipYawPitch (rad)')
axes[1].set_xlabel('waktu dalam siklus (s)')
axes[1].legend(fontsize=8)
axes[1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'gait_cycle.png'), dpi=150)
plt.close(fig)

# 7. Konsep koridor (dimensi humanoid)
fig, ax = plt.subplots(figsize=(6, 4.6))
ax.set_aspect('equal')
ax.add_patch(Circle((0, 0), 0.16, fc='#2b5fd9', ec='k', zorder=3, alpha=0.9))
ax.add_patch(Circle((0, 0), 0.03, fc='r', zorder=4))
hw = 0.25
for th, col, lab in ((0.0, '#d62728', 'theta = 0 (terhalang)'),
                     (math.radians(35), '#2ca02c', 'theta = 35 deg (dipilih)')):
    c, s = math.cos(th), math.sin(th)
    L = 2.0
    pts = [(-s * hw, c * hw), (L * c - s * hw, L * s + c * hw), (L * c + s * hw, L * s - c * hw),
           (s * hw, -c * hw)]
    ax.add_patch(Polygon(pts, fc=col, alpha=0.18, ec=col, label=lab))
    ax.annotate('', xy=(L * c, L * s), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color=col, lw=2))
ax.add_patch(Rectangle((0.9, -0.45), 0.4, 0.65, fc='#9aa3ad', ec='#444', label='obstacle'))
for k in range(26):
    ax.plot(0.9, -0.45 + k * 0.026, 'k.', ms=3)
ax.text(0.3, -0.33, 'titik Lidar', fontsize=8)
ax.set_xlim(-0.4, 2.2)
ax.set_ylim(-0.9, 1.6)
ax.legend(loc='upper left', fontsize=8)
ax.set_title('Koridor selebar 2 x 0.25 m untuk tiap kandidat arah')
ax.set_xlabel('x robot (m)')
ax.set_ylabel('y robot (m)')
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'corridor_concept.png'), dpi=150)
plt.close(fig)

# 8. State machine humanoid
fig, ax = plt.subplots(figsize=(9.5, 4.3))
ax.axis('off')
ax.set_xlim(0, 11)
ax.set_ylim(0, 5)
nodes = {'SIAP': (1.4, 2.5, '#e3e7ee'), 'JALAN': (5.5, 4.1, '#cfe8cf'), 'BERHENTI': (9.6, 4.1, '#ffe2b8'),
         'PUTAR': (9.6, 0.9, '#cfdcf6'), 'MUNDUR': (5.5, 0.9, '#f6d0cf')}
for k, (x, y, c) in nodes.items():
    ax.add_patch(FancyBboxPatch((x - 0.95, y - 0.38), 1.9, 0.76, boxstyle='round,pad=0.08', fc=c, ec='k', lw=1.3))
    ax.text(x, y, k, ha='center', va='center', fontsize=11.5, weight='bold')


def arrow(p, q, text, tx, ty, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=15, lw=1.2,
                                 connectionstyle=f'arc3,rad={rad}', color='#333'))
    if text:
        ax.text(tx, ty, text, ha='center', va='center', fontsize=7.8,
                bbox=dict(fc='white', ec='none', alpha=0.9))


arrow((2.2, 2.85), (4.55, 4.0), 'arah |theta| <= 35 deg\nkoridor bebas', 2.9, 3.8)
arrow((6.45, 4.15), (8.65, 4.15), 'depan < 0.85 m\natau |theta| > 75 deg', 7.55, 4.7)
arrow((9.6, 3.7), (9.6, 1.3), 'perlu belok', 10.35, 2.5)
arrow((8.65, 0.95), (2.3, 2.25), 'selesai putar', 5.6, 1.85, rad=-0.12)
arrow((2.0, 2.1), (4.55, 0.85), 'obstacle < 0.30 m', 2.75, 1.15)
arrow((4.55, 0.65), (1.2, 2.1), 'selesai mundur', 2.2, 0.55, rad=-0.35)
ax.text(5.5, 3.1, 'siklus lurus / belok kiri / belok kanan (2.04 s),\nkoridor diperiksa tiap siklus',
        ha='center', fontsize=7.8, color='#1f6d3d')
ax.text(5.5, 0.12, 'watchdog: tidak berpindah 30 s -> putar 60 deg; terjebak radius 0.5 m selama 60 s -> '
        'mode lolos 25 s; jatuh -> BANGUN', ha='center', fontsize=7.6, color='#444')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'state_machine.png'), dpi=150)
plt.close(fig)

# 9. Ringkasan angka untuk laporan & slide
def path_length(rows, every=10):
    """Panjang lintasan dari posisi tiap 1 s (10 sampel x 0.1 s), menghapus ayunan badan."""
    pts = rows[::every]
    return sum(math.hypot(b['x'] - a['x'], b['y'] - a['y']) for a, b in zip(pts, pts[1:]))


summary = {}
for m in data:
    rs = []
    for rows, _, s in data[m]:
        s = dict(s)
        s['jarak_tempuh_m'] = round(path_length(rows), 1)   # tanpa ayunan badan
        rs.append(s)
    summary[m] = {
        'runs': rs,
        'coverage_rata': round(sum(r['coverage_persen'] for r in rs) / len(rs), 1),
        'coverage_min': min(r['coverage_persen'] for r in rs),
        'coverage_max': max(r['coverage_persen'] for r in rs),
        'tabrakan': sum(r['tabrakan'] for r in rs),
        'jatuh': sum(r['jatuh'] for r in rs),
        'jarak_total_m': round(sum(r['jarak_tempuh_m'] for r in rs), 1),
        'clearance_min_m': min(r['clearance_min_m'] for r in rs),
        'waktu_total_s': sum(r['waktu_s'] for r in rs),
    }
summary['peningkatan_persen'] = round(100 * (summary['kebaruan']['coverage_rata']
                                             / summary['acak']['coverage_rata'] - 1))
json.dump(summary, open(os.path.join(ROOT, 'docs', 'stress_results.json'), 'w'), indent=2)
print('grafik tersimpan di', OUT)
print({m: {k: v for k, v in summary[m].items() if k != 'runs'} for m in ('kebaruan', 'acak')},
      'peningkatan', summary['peningkatan_persen'], '%')
