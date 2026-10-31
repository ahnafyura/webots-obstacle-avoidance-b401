"""Membuat worlds/obstacle_avoidance.wbt (arena humanoid). Jalankan: python3 tools/make_world.py"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = 0.8  # tinggi obstacle (lebih tinggi dari Lidar di kepala, ~0.57 m)
# (nama, tipe, x, y, yaw, ukuran, warna)
OBS = [
    ('kotak_1', 'box', -1.2, -1.0, 0.0, (0.6, 0.6), (0.85, 0.25, 0.2)),
    ('dinding_miring', 'box', 0.6, -1.6, 0.5, (1.0, 0.25), (0.95, 0.65, 0.15)),
    ('tabung_1', 'cyl', 1.4, -0.3, 0.0, 0.25, (0.2, 0.5, 0.85)),
    ('tabung_2', 'cyl', -0.35, 0.45, 0.0, 0.2, (0.3, 0.75, 0.35)),
    ('dinding_tengah', 'box', 0.85, 0.85, 0.0, (0.25, 1.1), (0.6, 0.3, 0.75)),
    ('kotak_berlian', 'box', -1.5, 1.1, 0.785, (0.5, 0.5), (0.85, 0.25, 0.55)),
    ('tabung_besar', 'cyl', 1.75, 1.75, 0.0, 0.3, (0.15, 0.65, 0.65)),
    ('dinding_utara', 'box', -0.4, 1.85, 0.0, (1.1, 0.25), (0.95, 0.8, 0.2)),
    ('tiang', 'cyl', -1.95, -0.1, 0.0, 0.15, (0.45, 0.45, 0.5)),
    ('kotak_2', 'box', 1.8, -1.8, 0.3, (0.4, 0.4), (0.9, 0.45, 0.1)),
    ('siku_L_a', 'box', 0.1, -0.5, 0.0, (0.8, 0.2), (0.35, 0.35, 0.8)),
    ('siku_L_b', 'box', 0.4, -0.15, 0.0, (0.2, 0.5), (0.35, 0.35, 0.8)),
]


def solid(i, name, kind, x, y, yaw, size, col):
    geom = (f'Box {{ size {size[0]} {size[1]} {H} }}' if kind == 'box'
            else f'Cylinder {{ height {H} radius {size} }}')
    return f'''    Solid {{
      translation {x} {y} {H / 2}
      rotation 0 0 1 {yaw}
      children [
        DEF OBS{i} Shape {{
          appearance PBRAppearance {{ baseColor {col[0]} {col[1]} {col[2]} roughness 1 metalness 0 }}
          geometry {geom}
        }}
      ]
      name "{name}"
      boundingObject USE OBS{i}
    }}'''


world = f'''#VRML_SIM R2025a utf8

EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackground.proto"
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackgroundLight.proto"
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/floors/protos/RectangleArena.proto"
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/robots/softbank/nao/protos/Nao.proto"

WorldInfo {{
  info [
    "Tugas Pelatihan Lab B401 - Robot Humanoid Obstacle Avoidance"
    "Humanoid NAO (25 DOF) dengan Lidar 360 derajat di atas kepala"
  ]
  title "B401 Humanoid Obstacle Avoidance"
  basicTimeStep 20
  contactProperties [
    ContactProperties {{
      material1 "NAO foot material"
      coulombFriction [
        7
      ]
      bounce 0.3
      bounceVelocity 0.003
    }}
  ]
}}
DEF VIEW Viewpoint {{
  orientation -0.5774 0.5774 0.5774 2.0944
  position 0 0 13.5
}}
TexturedBackground {{
}}
TexturedBackgroundLight {{
}}
DEF ARENA RectangleArena {{
  floorSize 5 5
  floorTileSize 1 1
  wallThickness 0.04
  wallHeight {H}
}}
DEF OBSTACLES Group {{
  children [
{chr(10).join(solid(i + 1, *o) for i, o in enumerate(OBS))}
  ]
}}
DEF ROBOT Nao {{
  translation -2.0 -2.0 0.334
  rotation 0 0 1 0.785
  name "humanoid_b401"
  controller "humanoid_avoidance"
  cameraWidth 320
  cameraHeight 240
  bodySlot [
    InertialUnit {{
      name "imu_body"
    }}
  ]
  headSlot [
    Lidar {{
      translation 0 0 0.085
      name "lidar"
      horizontalResolution 360
      fieldOfView 6.2832
      verticalFieldOfView 0.05
      numberOfLayers 1
      near 0.05
      minRange 0.06
      maxRange 4
      projection "cylindrical"
      noise 0.002
      children [
        Shape {{
          appearance PBRAppearance {{ baseColor 0.9 0.1 0.1 roughness 1 metalness 0 }}
          geometry Cylinder {{ height 0.04 radius 0.03 }}
        }}
      ]
    }}
  ]
}}
DEF EVALUATOR Robot {{
  name "evaluator"
  controller "evaluator"
  supervisor TRUE
}}
'''
open(os.path.join(ROOT, 'worlds', 'obstacle_avoidance.wbt'), 'w').write(world)
print('world ok')
