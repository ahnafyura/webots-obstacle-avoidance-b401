"""
Controller : evaluator (Supervisor)

Pengamat pasif untuk MENGUJI robot obstacle avoidance. Tidak mengendalikan robot.
  - Mendeteksi tabrakan memakai contact points milik robot (kontak selain lantai).
  - Mendeteksi robot jatuh (ketinggian torso turun di bawah FALL_Z).
  - Menghitung jarak minimum (clearance) robot ke obstacle & dinding secara analitik.
  - Menghitung cakupan (coverage) arena dalam grid 20 cm.
  - Mencetak ringkasan setiap 10 detik ke console.

Variabel lingkungan opsional (dipakai oleh tools/run_test.sh):
  EVAL_LOG_DIR   : folder untuk trajectory.csv, obstacles.json, summary.json
  EVAL_DURATION  : durasi uji (detik simulasi), lalu simulasi dihentikan
  EVAL_SNAPSHOTS : daftar waktu (detik) screenshot 3D view, contoh "1,30,60"
"""

import json
import math
import os

from controller import Supervisor

ARENA_HALF = 2.5
ROBOT_RADIUS = 0.18        # radius lingkaran pembungkus humanoid dari atas (m)
GRID = 0.2
CONTACT_Z = 0.03           # kontak di atas ketinggian ini = tabrakan (telapak kaki di z ~ 0)
FALL_Z = 0.22              # torso lebih rendah dari ini = jatuh (berdiri ~0.30 m)
SUMMARY_PERIOD = 10.0

sup = Supervisor()
dt_ms = int(sup.getBasicTimeStep())
dt = dt_ms / 1000.0

robot = sup.getFromDef('ROBOT')
robot.enableContactPointsTracking(dt_ms, True)

# posisi awal kustom untuk pengujian, format "x,y,yaw"
start = os.environ.get('EVAL_START')
if start:
    sx0, sy0, syaw0 = (float(v) for v in start.split(','))
    robot.getField('translation').setSFVec3f([sx0, sy0, 0.334])
    robot.getField('rotation').setSFRotation([0, 0, 1, syaw0])
    robot.resetPhysics()

log_dir = os.environ.get('EVAL_LOG_DIR')
duration = float(os.environ.get('EVAL_DURATION', '0') or 0)
view_mode = os.environ.get('EVAL_VIEW', 'top')   # 'top', 'follow', 'chase', atau 'oblique'
snapshots = sorted(float(s) for s in os.environ.get('EVAL_SNAPSHOTS', '').split(',') if s.strip())

# ---------------------------------------------------------------------------
# Ambil geometri obstacle dari Scene Tree
# ---------------------------------------------------------------------------
obstacles = []
group = sup.getFromDef('OBSTACLES').getField('children')
for i in range(group.getCount()):
    node = group.getMFNode(i)
    pos = node.getField('translation').getSFVec3f()
    rot = node.getField('rotation').getSFRotation()
    yaw = rot[3] * (1 if rot[2] >= 0 else -1)
    shape = node.getField('boundingObject').getSFNode()
    geom = shape.getField('geometry').getSFNode()
    name = node.getField('name').getSFString()
    if geom.getTypeName() == 'Box':
        sx, sy, _ = geom.getField('size').getSFVec3f()
        obstacles.append({'name': name, 'type': 'box', 'x': pos[0], 'y': pos[1],
                          'yaw': yaw, 'sx': sx, 'sy': sy})
    else:
        r = geom.getField('radius').getSFFloat()
        obstacles.append({'name': name, 'type': 'cylinder', 'x': pos[0], 'y': pos[1], 'r': r})


def obstacle_distance(px, py, o):
    if o['type'] == 'cylinder':
        return math.hypot(px - o['x'], py - o['y']) - o['r']
    c, s = math.cos(-o['yaw']), math.sin(-o['yaw'])
    dx, dy = px - o['x'], py - o['y']
    lx, ly = c * dx - s * dy, s * dx + c * dy
    qx = abs(lx) - o['sx'] / 2
    qy = abs(ly) - o['sy'] / 2
    outside = math.hypot(max(qx, 0), max(qy, 0))
    return outside + min(max(qx, qy), 0)


def clearance(px, py):
    walls = ARENA_HALF - max(abs(px), abs(py))
    return min([walls] + [obstacle_distance(px, py, o) for o in obstacles])


free_cells = set()
n = int(2 * ARENA_HALF / GRID)
for ix in range(n):
    for iy in range(n):
        cx = -ARENA_HALF + (ix + 0.5) * GRID
        cy = -ARENA_HALF + (iy + 0.5) * GRID
        if clearance(cx, cy) > ROBOT_RADIUS:
            free_cells.add((ix, iy))

visited = set()
collisions = 0
falls = 0
fallen = False
contact_steps = 0
in_contact = False
min_clear = 1e9
distance = 0.0
last_pos = None
t = 0.0
summary_timer = 0.0
log_timer = 0.0
rows = []

if log_dir:
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, 'obstacles.json'), 'w') as f:
        json.dump(obstacles, f, indent=2)


def look_at(cam, target):
    """Orientasi axis-angle Viewpoint agar menghadap target (kamera melihat ke +x)."""
    dx, dy, dz = (target[k] - cam[k] for k in range(3))
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(-dz, math.hypot(dx, dy))
    # q = qz(yaw) * qy(pitch)
    cz, sz = math.cos(yaw / 2), math.sin(yaw / 2)
    cy, sy = math.cos(pitch / 2), math.sin(pitch / 2)
    w, x, y, z = cz * cy, -sz * sy, cz * sy, sz * cy
    angle = 2 * math.acos(max(-1.0, min(1.0, w)))
    norm = math.sqrt(x * x + y * y + z * z) or 1.0
    return [x / norm, y / norm, z / norm, angle]


def summary():
    return {
        'waktu_s': round(t, 1),
        'jarak_tempuh_m': round(distance, 2),
        'tabrakan': collisions,
        'jatuh': falls,
        'langkah_kontak': contact_steps,
        'clearance_min_m': round(min_clear, 3),
        'coverage_persen': round(100.0 * len(visited & free_cells) / max(1, len(free_cells)), 1),
        'jumlah_obstacle': len(obstacles),
    }


print(f"[evaluator] {len(obstacles)} obstacle terdeteksi di arena.", flush=True)

while sup.step(dt_ms) != -1:
    t += dt
    p = robot.getPosition()
    x, y = p[0], p[1]
    R = robot.getOrientation()
    yaw = math.atan2(R[3], R[0])

    if last_pos is not None:
        distance += math.hypot(x - last_pos[0], y - last_pos[1])
    last_pos = (x, y)

    # body robot berbentuk persegi panjang; clearance dihitung dari pusat - radius
    c = clearance(x, y) - ROBOT_RADIUS
    min_clear = min(min_clear, c)
    visited.add((int((x + ARENA_HALF) / GRID), int((y + ARENA_HALF) / GRID)))

    # kontak non-lantai = tabrakan (lantai ada di z ~ 0)
    contact = any(cp.getPoint()[2] > CONTACT_Z for cp in robot.getContactPoints(True))
    is_fallen = p[2] < FALL_Z
    if is_fallen and not fallen:
        falls += 1
        print(f"[evaluator] JATUH pada t={t:.1f}s di ({x:.2f}, {y:.2f})", flush=True)
    fallen = is_fallen
    if contact:
        contact_steps += 1
        if not in_contact:
            collisions += 1
            print(f"[evaluator] TABRAKAN pada t={t:.1f}s di ({x:.2f}, {y:.2f})", flush=True)
    in_contact = contact

    log_timer += dt
    if log_dir and log_timer >= 0.1:
        log_timer = 0.0
        rows.append(f"{t:.2f},{x:.4f},{y:.4f},{yaw:.4f},{c:.4f},{int(contact)},{p[2]:.3f}")

    while snapshots and t >= snapshots[0]:
        snap_t = snapshots.pop(0)
        if log_dir:
            if view_mode == 'follow':
                view = sup.getFromDef('VIEW')
                cam = [x - 1.4 * math.cos(yaw), y - 1.4 * math.sin(yaw), 0.95]
                view.getField('position').setSFVec3f(cam)
                view.getField('orientation').setSFRotation(look_at(cam, [x + 0.3 * math.cos(yaw), y + 0.3 * math.sin(yaw), 0.3]))
                sup.step(dt_ms)
            elif view_mode == 'chase':
                view = sup.getFromDef('VIEW')
                cam = [x - 2.0 * math.cos(yaw + 0.35), y - 2.0 * math.sin(yaw + 0.35), 1.35]
                view.getField('position').setSFVec3f(cam)
                view.getField('orientation').setSFRotation(look_at(cam, [x + 0.6 * math.cos(yaw), y + 0.6 * math.sin(yaw), 0.25]))
                sup.step(dt_ms)
            elif view_mode == 'oblique':
                view = sup.getFromDef('VIEW')
                cam = [0.0, -6.0, 5.6]
                view.getField('position').setSFVec3f(cam)
                view.getField('orientation').setSFRotation(look_at(cam, [0.0, -0.1, 0.0]))
                sup.step(dt_ms)
            sup.exportImage(os.path.join(log_dir, f'snapshot_{int(snap_t):03d}s.jpg'), 90)

    summary_timer += dt
    if summary_timer >= SUMMARY_PERIOD:
        summary_timer = 0.0
        print(f"[evaluator] {summary()}", flush=True)

    if duration and t >= duration:
        break

result = summary()
print(f"[evaluator] HASIL AKHIR: {result}", flush=True)
if log_dir:
    with open(os.path.join(log_dir, 'trajectory.csv'), 'w') as f:
        f.write('t,x,y,yaw,clearance,contact,z\n')
        f.write('\n'.join(rows) + '\n')
    with open(os.path.join(log_dir, 'summary.json'), 'w') as f:
        json.dump(result, f, indent=2)
if duration:
    sup.simulationQuit(0)
