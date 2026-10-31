"""
Gait engine robot humanoid NAO.

Membaca file .motion (keyframe sudut sendi tiap 40 ms) lalu mengendalikan SETIAP sendi
secara langsung lewat RotationalMotor.setPosition(), dengan tiga perbaikan dibanding
memutar Motion bawaan Webots:

1. Transisi halus (blend). Motion bawaan langsung melompat ke pose pertama; dari posisi
   berdiri tegak lompatan ini membuat robot jatuh (terukur: Forwards50 jatuh ke depan
   pada detik 1.2). Di sini sudut sendi diinterpolasi smoothstep dari target terakhir
   ke pose pertama klip.
2. Siklus jalan kontinu. Forwards50 dipotong menjadi mulai (frame 0-51), siklus
   (51-102, 2 langkah, 2.04 s) dan berhenti (102-170). Frame 51 dan 102 identik
   (selisih 0 rad), jadi siklus dapat diulang tanpa sambungan kasar.
3. Belok sambil jalan. Sendi HipYawPitch diberi satu pulsa per siklus, meniru pola pada
   TurnLeft/TurnRight.motion: dibuka saat kaki yang sesuai terangkat, ditutup saat kaki
   menapak. Pulsa bernilai nol di batas siklus sehingga klip bisa disambung bebas.

Hasil ukur (rata-rata, lihat laporan):
  jalan_lurus  +0.18 m / 2.04 s        jalan_kiri  +0.16 m, +17 deg / 2.04 s
  jalan_kanan  +0.17 m, -13 deg        putar_kiri40/60  +39/+59 deg
  putar_kanan40/60  -40/-59 deg        putar_kiri10/20, kanan10/20  +-11 / +-20.7 deg
  putar_balik  +196 deg (9.0 s)
  mundur  -0.10 m                      maju_kecil  +0.10 m
"""

import os

# Postur siap: lutut ditekuk (pusat massa rendah), lengan di samping badan.
READY = {
    'LHipYawPitch': 0.0, 'LHipRoll': 0.0, 'LHipPitch': -0.524, 'LKneePitch': 1.047,
    'LAnklePitch': -0.524, 'LAnkleRoll': 0.0,
    'RHipYawPitch': 0.0, 'RHipRoll': 0.0, 'RHipPitch': -0.524, 'RKneePitch': 1.047,
    'RAnklePitch': -0.524, 'RAnkleRoll': 0.0,
    'LShoulderPitch': 1.745, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
    'RShoulderPitch': 1.745, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396,
    'HeadYaw': 0.0, 'HeadPitch': 0.0,
}
JOINTS = list(READY)

LOOP_START, LOOP_END = 51, 102     # frame siklus jalan di Forwards50.motion
TURN_AMP = 0.25                    # rad, amplitudo pulsa HipYawPitch (stabil, terukur)


def _smooth(u):
    return u * u * (3.0 - 2.0 * u)


def load_motion(path, start=0, end=None):
    """Baca file .motion -> (nama sendi, [(waktu_s, [sudut...]), ...])."""
    lines = open(path).read().strip().split('\n')
    joints = lines[0].split(',')[2:]
    frames = []
    for line in lines[1:]:
        parts = line.split(',')
        mm, ss, ms = parts[0].split(':')
        frames.append((int(mm) * 60 + int(ss) + int(ms) / 1000.0, [float(v) for v in parts[2:]]))
    frames = frames[start:end]
    t0 = frames[0][0]
    return joints, [(t - t0, v) for t, v in frames]


class Clip:
    def __init__(self, joints, frames):
        self.joints, self.frames = joints, frames
        self.duration = frames[-1][0]

    def at(self, t):
        f = self.frames
        if t <= 0.0:
            return f[0][1]
        if t >= self.duration:
            return f[-1][1]
        lo, hi = 0, len(f) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if f[mid][0] <= t:
                lo = mid
            else:
                hi = mid
        (ta, a), (tb, b) = f[lo], f[hi]
        u = (t - ta) / (tb - ta)
        return [x + (y - x) * u for x, y in zip(a, b)]


def turn_pulse(clip, direction, amp=TURN_AMP):
    """Siklus jalan + satu pulsa HipYawPitch. direction +1 = kiri, -1 = kanan.
    Kiri: buka pada frame 7-20 (ayunan badan ke sisi +), tutup 20-33.
    Kanan: buka 20-33, tutup 33-46. Di luar itu nol, termasuk di batas siklus."""
    iyl, iyr = clip.joints.index('LHipYawPitch'), clip.joints.index('RHipYawPitch')
    a, b, c = (7, 20, 33) if direction > 0 else (20, 33, 46)
    frames = []
    for k, (t, v) in enumerate(clip.frames):
        if a <= k < b:
            s = (k - a) / (b - a)
        elif b <= k < c:
            s = 1.0 - (k - b) / (c - b)
        else:
            s = 0.0
        v = list(v)
        v[iyl] -= amp * _smooth(s)
        v[iyr] -= amp * _smooth(s)
        frames.append((t, v))
    return Clip(clip.joints, frames)


def scale_hip_yaw(clip, k):
    """Putar di tempat dengan sudut lebih kecil: hanya sendi HipYawPitch yang diskalakan.
    TurnLeft40/TurnRight40 x 0.25 -> +-11 deg, x 0.5 -> +-20.7 deg (terukur, stabil)."""
    iyl, iyr = clip.joints.index('LHipYawPitch'), clip.joints.index('RHipYawPitch')
    frames = []
    for t, v in clip.frames:
        v = list(v)
        v[iyl] *= k
        v[iyr] *= k
        frames.append((t, v))
    return Clip(clip.joints, frames)


class Gait:
    # klip yang disambung tanpa blend (bagian dari siklus jalan)
    CHAIN = {'jalan_lurus', 'jalan_kiri', 'jalan_kanan', 'jalan_berhenti'}

    def __init__(self, robot, dt, motion_dir):
        self.dt = dt
        self.motors, self.sensors = {}, {}
        for j in JOINTS:
            self.motors[j] = robot.getDevice(j)
            s = robot.getDevice(j + 'S')
            s.enable(int(round(dt * 1000)))
            self.sensors[j] = s
        p = lambda name: os.path.join(motion_dir, name + '.motion')
        fw = p('Forwards50')
        loop = Clip(*load_motion(fw, LOOP_START, LOOP_END + 1))
        self.clips = {
            'jalan_mulai': Clip(*load_motion(fw, 0, LOOP_START + 1)),
            'jalan_lurus': loop,
            'jalan_kiri': turn_pulse(loop, +1),
            'jalan_kanan': turn_pulse(loop, -1),
            'jalan_berhenti': Clip(*load_motion(fw, LOOP_END)),
            'putar_kiri10': scale_hip_yaw(Clip(*load_motion(p('TurnLeft40'))), 0.25),
            'putar_kanan10': scale_hip_yaw(Clip(*load_motion(p('TurnRight40'))), 0.25),
            'putar_kiri20': scale_hip_yaw(Clip(*load_motion(p('TurnLeft40'))), 0.5),
            'putar_kanan20': scale_hip_yaw(Clip(*load_motion(p('TurnRight40'))), 0.5),
            'putar_kiri40': Clip(*load_motion(p('TurnLeft40'))),
            'putar_kiri60': Clip(*load_motion(p('TurnLeft60'))),
            'putar_kanan40': Clip(*load_motion(p('TurnRight40'))),
            'putar_kanan60': Clip(*load_motion(p('TurnRight60'))),
            'putar_balik': Clip(*load_motion(p('TurnLeft180'))),
            'mundur': Clip(*load_motion(p('Backwards'))),
            'maju_kecil': Clip(*load_motion(p('Forwards'))),
            'bangun': Clip(*load_motion(p('StandUpFromFront'))),
        }
        self.target = dict(READY)
        self.name, self.clip, self.t, self.blend, self.blend_from = None, None, 0.0, 0.0, None

    def joint_positions(self):
        return {j: s.getValue() for j, s in self.sensors.items()}

    def play(self, name, blend=None):
        if blend is None:
            blend = 0.0 if name in self.CHAIN else 0.4
        self.name, self.clip, self.t = name, self.clips[name], 0.0
        self.blend, self.blend_from = blend, dict(self.target)

    def go_ready(self, seconds=1.2):
        """Transisi dari posisi sendi saat ini (berdiri tegak) ke postur siap."""
        cur = self.joint_positions()
        self.clips['siap'] = Clip(JOINTS, [(0.0, [cur[j] for j in JOINTS]),
                                           (seconds, [READY[j] for j in JOINTS])])
        self.target = cur
        self.play('siap', 0.0)

    def busy(self):
        return self.clip is not None

    def step(self):
        c = self.clip
        if c is not None:
            if self.t < self.blend:
                u = _smooth(self.t / self.blend)
                for j, v in zip(c.joints, c.frames[0][1]):
                    self.target[j] = self.blend_from[j] + (v - self.blend_from[j]) * u
            else:
                for j, v in zip(c.joints, c.at(self.t - self.blend)):
                    self.target[j] = v
                if self.t - self.blend >= c.duration:
                    self.clip = None
            self.t += self.dt
        for j, m in self.motors.items():
            m.setPosition(self.target[j])
