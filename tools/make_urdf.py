"""
Membuat rviz/humanoid_b401.urdf untuk RViz2.

Webots dapat mengekspor URDF (Robot.getUrdf), tetapi Hinge2Joint (bahu dan leher NAO)
belum didukung, sehingga hasil ekspor hanya berisi torso dan kaki. Skrip ini:
  1. merapikan nama link/joint (tanpa '/' dan spasi) agar aman sebagai frame TF,
  2. menambahkan lengan (ShoulderPitch/Roll, ElbowYaw/Roll), kepala (HeadYaw/Pitch),
     serta frame lidar, kamera, sonar, dan telapak kaki,
memakai dimensi kinematika NAO H25 V5 (ShoulderOffsetY 0.098, ShoulderOffsetZ 0.100,
UpperArmLength 0.105, ElbowOffsetY 0.015, LowerArmLength 0.056, HandOffsetX 0.058,
NeckOffsetZ 0.1265).

    python3 tools/make_urdf.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'rviz', 'nao_webots_export.urdf')
DST = os.path.join(ROOT, 'rviz', 'humanoid_b401.urdf')

RENAME = {'Sonar/Left': 'sonar_left', 'Sonar/Right': 'sonar_right', 'LFsr': 'l_sole',
          'RFsr': 'r_sole', 'inertial unit': 'inertial_unit'}

GREY = '<material name="abu"><color rgba="0.85 0.85 0.88 1"/></material>'
DARK = '<material name="gelap"><color rgba="0.25 0.27 0.3 1"/></material>'
RED = '<material name="merah"><color rgba="0.9 0.1 0.1 1"/></material>'


def link(name, visual=''):
    return f'  <link name="{name}">{visual}</link>\n'


def cyl(length, radius, xyz, rpy, mat=GREY):
    return (f'<visual><origin xyz="{xyz}" rpy="{rpy}"/><geometry><cylinder length="{length}" '
            f'radius="{radius}"/></geometry>{mat}</visual>')


def sphere(r, xyz, mat=GREY):
    return f'<visual><origin xyz="{xyz}" rpy="0 0 0"/><geometry><sphere radius="{r}"/></geometry>{mat}</visual>'


def box(size, xyz, mat=GREY):
    return f'<visual><origin xyz="{xyz}" rpy="0 0 0"/><geometry><box size="{size}"/></geometry>{mat}</visual>'


def joint(name, parent, child, xyz, axis=None, lo=-2.0, hi=2.0, rpy='0 0 0'):
    if axis is None:
        return (f'  <joint name="{name}" type="fixed"><parent link="{parent}"/><child link="{child}"/>'
                f'<origin xyz="{xyz}" rpy="{rpy}"/></joint>\n')
    return (f'  <joint name="{name}" type="revolute"><parent link="{parent}"/><child link="{child}"/>'
            f'<origin xyz="{xyz}" rpy="{rpy}"/><axis xyz="{axis}"/>'
            f'<limit lower="{lo}" upper="{hi}" effort="5" velocity="8"/></joint>\n')


def arm(side, s):
    """side 'L'/'R', s = +1 kiri / -1 kanan."""
    p = side
    out = link(f'{p}Shoulder', sphere(0.03, '0 0 0'))
    out += joint(f'{p}ShoulderPitch', 'base_link', f'{p}Shoulder', f'0 {0.098 * s} 0.100', '0 1 0', -2.09, 2.09)
    out += link(f'{p}Bicep', cyl(0.105, 0.028, '0.05 0 0', '0 1.5708 0'))
    out += joint(f'{p}ShoulderRoll', f'{p}Shoulder', f'{p}Bicep', '0 0 0', '0 0 1',
                 -0.31 if s > 0 else -1.33, 1.33 if s > 0 else 0.31)
    out += link(f'{p}Elbow', sphere(0.026, '0 0 0', DARK))
    out += joint(f'{p}ElbowYaw', f'{p}Bicep', f'{p}Elbow', f'0.105 {0.015 * s} 0', '1 0 0', -2.09, 2.09)
    out += link(f'{p}ForeArm', cyl(0.11, 0.024, '0.055 0 0', '0 1.5708 0') + sphere(0.028, '0.125 0 0', DARK))
    out += joint(f'{p}ElbowRoll', f'{p}Elbow', f'{p}ForeArm', '0 0 0', '0 0 1',
                 -1.54 if s > 0 else 0.03, -0.03 if s > 0 else 1.54)
    return out


def main():
    u = open(SRC).read()
    for a, b in RENAME.items():
        u = u.replace(f'"{a}"', f'"{b}"')
    # sisa nama dengan '/' atau spasi di atribut name/link
    u = re.sub(r'(name|link)="([^"]*)"', lambda m: f'{m.group(1)}="{m.group(2).replace("/", "_").replace(" ", "_")}"', u)
    u = u.replace('<robot name="NAO"', '<robot name="humanoid_b401"')

    extra = '\n  <!-- ditambahkan oleh tools/make_urdf.py: lengan, kepala, sensor -->\n'
    extra += link('torso_visual', box('0.09 0.14 0.17', '-0.005 0 0.04'))
    extra += joint('torso_visual_joint', 'base_link', 'torso_visual', '0 0 0')
    extra += arm('L', +1) + arm('R', -1)
    extra += link('Neck', cyl(0.03, 0.02, '0 0 -0.01', '0 0 0', DARK))
    extra += joint('HeadYaw', 'base_link', 'Neck', '0 0 0.1265', '0 0 1', -2.08, 2.08)
    extra += link('Head', sphere(0.068, '0 0 0.055'))
    extra += joint('HeadPitch', 'Neck', 'Head', '0 0 0', '0 1 0', -0.67, 0.51)
    extra += link('lidar', cyl(0.04, 0.03, '0 0 0', '0 0 0', RED))
    extra += joint('lidar_joint', 'Head', 'lidar', '0 0 0.13853')
    extra += link('camera_top')
    extra += joint('camera_top_joint', 'Head', 'camera_top', '0.0539 0 0.0679')
    u = u.replace('</robot>', extra + '</robot>')
    open(DST, 'w').write(u)
    # file parameter untuk robot_state_publisher (URDF multi-baris tidak bisa lewat -p)
    yaml = 'robot_state_publisher:\n  ros__parameters:\n    robot_description: |\n'
    yaml += ''.join('      ' + line + '\n' for line in u.splitlines())
    open(os.path.join(ROOT, 'rviz', 'rsp_params.yaml'), 'w').write(yaml)
    print('URDF ->', DST)


if __name__ == '__main__':
    main()
