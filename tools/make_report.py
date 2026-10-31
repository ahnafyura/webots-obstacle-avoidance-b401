"""Membuat laporan PDF: docs/Laporan_Obstacle_Avoidance_B401.pdf"""
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'docs', 'images')
OUT = os.path.join(ROOT, 'docs', 'Laporan_Obstacle_Avoidance_B401.pdf')
REPO = 'https://github.com/ahnafyura/webots-obstacle-avoidance-b401'

FONT_DIR = '/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DV', f'{FONT_DIR}/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-B', f'{FONT_DIR}/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DV-I', f'{FONT_DIR}/DejaVuSans-Oblique.ttf'))
pdfmetrics.registerFont(TTFont('DVM', f'{FONT_DIR}/DejaVuSansMono.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('DV', normal='DV', bold='DV-B', italic='DV-I', boldItalic='DV-B')

ss = getSampleStyleSheet()
BLUE = colors.HexColor('#1f3f8f')
body = ParagraphStyle('body', parent=ss['Normal'], fontName='DV', fontSize=10, leading=14.5,
                      alignment=TA_JUSTIFY, spaceAfter=6)
h1 = ParagraphStyle('h1', parent=body, fontName='DV-B', fontSize=15, leading=20, textColor=BLUE,
                    spaceBefore=10, spaceAfter=8, alignment=0)
h2 = ParagraphStyle('h2', parent=body, fontName='DV-B', fontSize=11.5, leading=16, textColor=BLUE,
                    spaceBefore=8, spaceAfter=4, alignment=0)
cap = ParagraphStyle('cap', parent=body, fontName='DV-I', fontSize=8.5, leading=11,
                     alignment=TA_CENTER, textColor=colors.HexColor('#444'), spaceAfter=10)
bullet = ParagraphStyle('bullet', parent=body, leftIndent=14, bulletIndent=4, spaceAfter=3)
code = ParagraphStyle('code', fontName='DVM', fontSize=7.4, leading=9.2,
                      backColor=colors.HexColor('#f4f5f7'), borderColor=colors.HexColor('#d0d4da'),
                      borderWidth=0.5, borderPadding=5, spaceBefore=4, spaceAfter=10)
formula = ParagraphStyle('formula', parent=body, alignment=TA_CENTER, fontName='DV', fontSize=10.5)
cell = ParagraphStyle('cell', parent=body, fontSize=8.8, leading=11.5, alignment=0, spaceAfter=0)
cellb = ParagraphStyle('cellb', parent=cell, fontName='DV-B', textColor=colors.white)

W = A4[0] - 4 * cm
story = []
fig_no = [0]
tab_no = [0]


def P(t, s=body):
    story.append(Paragraph(t, s))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, bullet, bulletText='•'))


def fig(name, caption, width=W * 0.85):
    from PIL import Image as PI
    path = os.path.join(IMG, name)
    w, h = PI.open(path).size
    fig_no[0] += 1
    story.append(KeepTogether([Image(path, width=width, height=width * h / w),
                               Paragraph(f'Gambar {fig_no[0]}. {caption}', cap)]))


def table(rows, widths, caption=None, header=True):
    data = [[Paragraph(str(c), cellb if (header and i == 0) else cell) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#b8bec8')),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
    if header:
        st += [('BACKGROUND', (0, 0), (-1, 0), BLUE)]
        st += [('BACKGROUND', (0, i), (-1, i), colors.HexColor('#eef1f7'))
               for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    items = [t]
    if caption:
        tab_no[0] += 1
        items.insert(0, Paragraph(f'Tabel {tab_no[0]}. {caption}', cap))
    story.append(KeepTogether(items))
    story.append(Spacer(1, 6))


def codeblock(text):
    story.append(Preformatted(text.rstrip('\n'), code))


# ---------------------------------------------------------------------------
# Data hasil
# ---------------------------------------------------------------------------
stress = json.load(open(os.path.join(ROOT, 'docs', 'stress_results.json')))
starts = ["(-1.2, -1.2, 45°)", "(1.2, 1.2, -132°)", "(0.0, 0.7, 0°)", "(1.2, -0.5, 180°)",
          "(-1.2, 1.2, -29°)", "(0.6, -0.5, 90°)", "(-0.3, -1.2, 0°)", "(0.9, 0.3, 115°)"]
tot_dist = sum(r['jarak_tempuh_m'] for r in stress)
tot_col = sum(r['tabrakan'] for r in stress)
tot_time = sum(r['waktu_s'] for r in stress)
min_clear = min(r['clearance_min_m'] for r in stress)
avg_cov = sum(r['coverage_persen'] for r in stress) / len(stress)

# ---------------------------------------------------------------------------
# Halaman judul
# ---------------------------------------------------------------------------
title = ParagraphStyle('title', parent=body, fontName='DV-B', fontSize=22, leading=28,
                       alignment=TA_CENTER, textColor=BLUE)
sub = ParagraphStyle('sub', parent=body, fontSize=12, leading=17, alignment=TA_CENTER)
story += [Spacer(1, 2.2 * cm),
          Paragraph('LAPORAN TUGAS PELATIHAN LAB B401', sub), Spacer(1, 0.4 * cm),
          Paragraph('Robot Obstacle Avoidance<br/>Berbasis Lidar 360° di Webots', title),
          Spacer(1, 0.4 * cm),
          Paragraph('Navigasi reaktif <i>Corridor Gap Selection</i> dengan state machine '
                    'dan lapisan safety ultrasonik', sub),
          Spacer(1, 0.9 * cm)]
fig('overview.jpg', 'Arena 3 × 3 m dengan 12 obstacle dan robot differential drive kustom.', W)
story += [Spacer(1, 0.5 * cm),
          Paragraph('Disusun oleh: <b>Ahnaf</b>', sub),
          Paragraph(f'Repositori: <font color="#1f3f8f"><link href="{REPO}">{REPO}</link></font>', sub),
          Paragraph('Simulator: Cyberbotics Webots R2025a · Bahasa: Python 3', sub),
          Paragraph('Oktober 2026', sub),
          PageBreak()]

# ---------------------------------------------------------------------------
# 1. Pendahuluan
# ---------------------------------------------------------------------------
P('1. Pendahuluan', h1)
P('1.1 Latar Belakang', h2)
P('Pada modul pelatihan sebelumnya robot dirakit sebagai <i>line tracer</i>: robot differential drive '
  'yang mengikuti garis hitam dengan dua sensor inframerah dan kontrol <i>bang-bang</i>. Tugas ini '
  'mengembangkan robot yang sama menjadi robot <b>obstacle avoidance</b>. Robot harus bergerak secara '
  'otonom di arena berisi rintangan tanpa menabraknya. Rintangannya tidak hanya dinding pinggir arena, '
  'tetapi juga obstacle yang diletakkan di tengah arena.')
P('1.2 Spesifikasi Tugas dan Pemenuhannya', h2)
table([
    ['Ketentuan tugas', 'Implementasi pada proyek ini', 'Status'],
    ['Membuat robot obstacle avoidance', 'Robot bergerak otonom dan menghindari semua rintangan. '
     f'Diuji 8 × 300 detik dengan total {tot_col} tabrakan.', '✔'],
    ['Bentuk robot bebas (boleh sama dengan modul)', 'Robot kustom dengan struktur seperti modul: body '
     '<i>Box</i>, 2 roda <i>HingeJoint</i> + <i>RotationalMotor</i>, dan roda kastor <i>BallJoint</i>. '
     'Ditambah encoder, Lidar, dan sonar.', '✔'],
    ['Menaruh obstacle di arena, tidak hanya menghindari pinggiran arena', '12 obstacle di tengah arena: '
     'kotak, kotak miring, tabung berbagai ukuran, dinding, dan siku-L (perangkap cekung).', '✔'],
    ['Sensor bebas (Lidar, Ultrasonic, dll.)', 'Lidar 360° (360 sinar, jangkauan 2.5 m) sebagai sensor '
     'utama, 3 sensor ultrasonik (sonar) di depan sebagai lapisan safety, dan 2 encoder roda untuk odometri.', '✔'],
], [4.0 * cm, 10.2 * cm, 2.0 * cm], 'Pemenuhan ketentuan tugas')

P('1.3 Tujuan', h2)
bullets(['Merancang robot differential drive beserta sensor jarak di Webots.',
         'Mengimplementasikan algoritma navigasi reaktif yang menghindari obstacle dengan aman dan tetap '
         'menjelajahi arena.',
         'Menguji robot secara kuantitatif, yaitu jumlah tabrakan, jarak aman (clearance), dan cakupan '
         'arena, dari beberapa posisi awal.'])

# ---------------------------------------------------------------------------
# 2. Dasar teori
# ---------------------------------------------------------------------------
P('2. Dasar Teori', h1)
P('2.1 Kinematika Differential Drive', h2)
P('Robot digerakkan oleh dua roda independen. Kecepatan linear <i>v</i> dan kecepatan sudut <i>ω</i> '
  'diperoleh dari kecepatan roda kanan <i>V<sub>R</sub></i> dan kiri <i>V<sub>L</sub></i> dengan jarak '
  'antar roda <i>L</i>:')
P('v = (V<sub>R</sub> + V<sub>L</sub>) / 2        ω = (V<sub>R</sub> − V<sub>L</sub>) / L', formula)
P('Controller menghitung <i>v</i> dan <i>ω</i> yang diinginkan, lalu mengubahnya menjadi kecepatan '
  'sudut roda (rad/s) dengan jari-jari roda <i>r</i>. Jika salah satu roda melebihi batas motor, kedua '
  'nilai diskalakan bersama sehingga arah belok tetap terjaga:')
P('ω<sub>L</sub> = (v − ω·L/2) / r        ω<sub>R</sub> = (v + ω·L/2) / r', formula)
P('2.2 Lidar', h2)
P('Lidar (<i>Light Detection and Ranging</i>) memancarkan berkas cahaya dan mengukur jarak dari waktu '
  'pantulnya. Lidar putar 2D menghasilkan <i>range image</i>, yaitu deretan jarak untuk setiap sudut. '
  'Pada proyek ini Lidar memiliki 360 sinar dengan resolusi 1° dan FOV 360°. Hasil uji kalibrasi di '
  'Webots: indeks 0 mengarah ke belakang robot (+180°), kemudian urutannya searah jarum jam. Indeks 90 '
  'mengarah ke kiri, 180 ke depan, dan 270 ke kanan. Jadi sudut sinar ke-<i>i</i> adalah '
  'θ<sub>i</sub> = π − i·(2π/360).')
P('2.3 Sensor Ultrasonik', h2)
P('Sensor ultrasonik (sonar) mengukur jarak dari pantulan gelombang suara. Di Webots, sensor ini '
  'dimodelkan sebagai <i>DistanceSensor</i> bertipe <i>sonar</i>. Sensor ini dipakai sebagai lapisan '
  'safety kedua di depan robot: jika Lidar gagal melihat obstacle (misalnya obstacle yang lebih rendah '
  'dari bidang scan), sonar tetap dapat memicu manuver darurat.')
P('2.4 Navigasi Reaktif', h2)
P('Navigasi reaktif menentukan aksi langsung dari pembacaan sensor saat itu, tanpa peta global. '
  'Beberapa pendekatan yang umum adalah <i>Braitenberg</i>, <i>potential field</i>, <i>Vector Field '
  'Histogram</i>, dan <i>Follow-the-Gap</i>. Proyek ini memakai varian <i>gap selection</i> berbasis '
  'koridor. Lebar fisik robot diperhitungkan secara eksplisit, sehingga celah yang lebih sempit dari '
  'robot tidak akan dipilih.')

# ---------------------------------------------------------------------------
# 3. Desain robot dan arena
# ---------------------------------------------------------------------------
P('3. Perancangan Robot', h1)
P('Robot dirakit dari node dasar Webots dengan langkah yang sama seperti modul Line Tracer, yaitu '
  '<i>Robot → Shape (DEF BODY_SHAPE) → HingeJoint</i> untuk roda dan <i>BallJoint</i> untuk kastor. '
  'Sensor IR lantai pada modul diganti dengan sensor jarak horizontal.')
fig('robot_closeup.jpg', 'Robot B401: body biru, Lidar merah di atas, dua roda penggerak, dan roda '
    'kastor di belakang. Tiga sensor ultrasonik terpasang di sisi depan.', W * 0.8)
table([
    ['Komponen', 'Node Webots', 'Nama device / parameter'],
    ['Body (chassis)', 'Shape + Box', '0.16 × 0.12 × 0.04 m, massa 0.6 kg, center of mass digeser ke belakang'],
    ['Roda kiri / kanan', 'HingeJoint + RotationalMotor', 'motor_kiri / motor_kanan; r = 0.03 m, L = 0.14 m, '
     'v<sub>maks</sub> 15 rad/s'],
    ['Encoder roda', 'PositionSensor', 'encoder_kiri / encoder_kanan, untuk odometri heading'],
    ['Roda kastor', 'BallJoint + Sphere', 'r = 0.015 m, di x = −0.06 m'],
    ['Lidar 360°', 'Lidar (cylindrical)', 'lidar; 360 sinar, 1 layer, 0.03–2.5 m, noise 0.2%, tinggi 9.5 cm'],
    ['Ultrasonik ×3', 'DistanceSensor type "sonar"', 'us_kiri (+34°), us_depan (0°), us_kanan (−34°); '
     'keluaran dalam meter (0–1 m)'],
], [3.3 * cm, 4.4 * cm, 8.5 * cm], 'Spesifikasi robot')

P('4. Perancangan Arena', h1)
P('Arena berupa <i>RectangleArena</i> 3 × 3 m dengan dinding setinggi 0.2 m. Di dalamnya diletakkan '
  '<b>12 obstacle</b> dengan bentuk dan orientasi beragam. Tujuannya agar algoritma diuji pada kasus '
  'yang sulit: celah sempit, permukaan melengkung (tabung), permukaan miring, dan sudut cekung (siku-L). '
  'Sudut cekung adalah kasus klasik yang membuat robot reaktif sederhana terjebak.')
fig('top_view.jpg', 'Tampak atas arena. Seluruh obstacle berada di dalam arena, bukan hanya dinding pinggir.',
    W * 0.62)
table([
    ['#', 'Nama', 'Bentuk', 'Posisi (x, y)', 'Ukuran'],
    ['1', 'kotak_1', 'Box', '(−0.60, −0.50)', '0.30 × 0.30 m'],
    ['2', 'dinding_miring', 'Box, rotasi 29°', '(0.30, −0.90)', '0.50 × 0.15 m'],
    ['3', 'tabung_1', 'Cylinder', '(0.80, −0.20)', 'r = 0.12 m'],
    ['4', 'tabung_2', 'Cylinder', '(−0.15, 0.25)', 'r = 0.10 m'],
    ['5', 'dinding_tengah', 'Box', '(0.45, 0.45)', '0.15 × 0.60 m'],
    ['6', 'kotak_berlian', 'Box, rotasi 45°', '(−0.90, 0.65)', '0.25 × 0.25 m'],
    ['7', 'tabung_besar', 'Cylinder', '(1.00, 0.95)', 'r = 0.15 m'],
    ['8', 'dinding_utara', 'Box', '(−0.25, 1.05)', '0.60 × 0.12 m'],
    ['9', 'tiang', 'Cylinder', '(−1.10, −0.05)', 'r = 0.08 m'],
    ['10', 'kotak_2', 'Box, rotasi 17°', '(1.05, −1.00)', '0.20 × 0.20 m'],
    ['11–12', 'siku_L_a / siku_L_b', 'Box (bentuk L)', '(0.10, −0.30) / (0.25, −0.15)', '0.40 × 0.10 / 0.10 × 0.20 m'],
], [1.1 * cm, 3.4 * cm, 3.0 * cm, 4.4 * cm, 4.3 * cm], 'Daftar obstacle (tinggi semua 0.2 m)')

# ---------------------------------------------------------------------------
# 5. Algoritma
# ---------------------------------------------------------------------------
P('5. Algoritma Navigasi', h1)
P('5.1 Corridor Gap Selection', h2)
P('Setiap langkah simulasi (16 ms), scan Lidar diubah ke titik-titik (x, y) dalam frame robot. Untuk '
  '61 kandidat arah θ dari −150° sampai +150° (kelipatan 5°), controller menghitung <b>jarak bebas '
  'koridor</b>. Koridor adalah persegi panjang selebar robot ditambah margin (2 × 0.13 m) yang memanjang '
  'ke arah θ. Setiap titik Lidar diproyeksikan ke arah θ:')
P('longitudinal = x·cos θ + y·sin θ        lateral = −x·sin θ + y·cos θ', formula)
P('Titik dengan nilai longitudinal positif dan |lateral| lebih kecil dari setengah lebar koridor berarti '
  'memblokir koridor. Jarak bebas adalah nilai longitudinal terkecil dari titik-titik tersebut, dengan '
  'batas maksimum 1 m. Cara ini lebih aman daripada hanya melihat satu sinar, karena celah yang terlihat '
  'lebar tetapi sebenarnya lebih sempit dari badan robot tidak akan lolos seleksi.')
fig('corridor_concept.png', 'Konsep koridor. Koridor θ = 0 terblokir obstacle, sedangkan koridor '
    'θ = 35° bebas sehingga dipilih.', W * 0.62)
P('Setiap kandidat diberi skor sebagai berikut, lalu kandidat dengan skor terbesar dipilih:')
P('skor(θ) = min(bebas(θ), 1 m) − 0.15·|θ − θ<sub>jelajah</sub>| − 0.08·|θ − θ<sub>sebelumnya</sub>|',
  formula)
bullets(['<b>Suku pertama</b> mengutamakan arah yang paling lapang.',
         '<b>Suku kedua</b> (bias jelajah) membuat robot menjelajah. Setiap 5–10 detik robot memilih '
         'arah global acak, lalu arah itu dikonversi ke frame robot memakai heading dari odometri '
         'encoder. Tanpa suku ini, robot cenderung berputar di satu lintasan yang sama (limit cycle).',
         '<b>Suku ketiga</b> (smoothing) mencegah robot zig-zag karena arah tujuan berubah-ubah.'])
P('Kecepatan dihitung dengan kontrol proporsional:')
P('ω = clamp(2.8·θ*, ±3 rad/s)        v = 0.28 · clamp((d<sub>depan</sub> − 0.17)/(0.60 − 0.17), 0, 1) · cos²θ*',
  formula)
P('Robot melaju penuh di area lapang, melambat ketika mendekati obstacle, dan hampir berputar di tempat '
  'ketika arah yang dipilih jauh ke samping.')

P('5.2 State Machine dan Penanganan Kondisi Khusus', h2)
fig('state_machine.png', 'State machine controller.', W * 0.95)
bullets(['<b>JELAJAH</b>: navigasi normal dengan Corridor Gap Selection.',
         '<b>MUNDUR</b>: aktif jika titik Lidar terdekat di sektor depan ±60° kurang dari 13 cm, '
         'sonar membaca kurang dari 5 cm, atau robot terdeteksi macet. Robot mundur 0.10 m/s sambil '
         'memutar ke sisi yang lebih lapang, dengan syarat bagian belakang masih kosong.',
         '<b>PUTAR</b>: berputar di tempat sampai koridor depan bebas lebih dari 45 cm. Jika jarak ke '
         'segala arah kurang dari 11.5 cm, robot terlalu sempit untuk berputar, sehingga robot bergeser '
         'menjauh dari titik terdekat terlebih dahulu.',
         '<b>Watchdog macet</b>: rata-rata perubahan scan Lidar dibandingkan dengan 2 detik sebelumnya. '
         'Jika perubahannya kurang dari 4 mm padahal robot sedang diperintah maju, robot dianggap '
         'tersangkut dan masuk state MUNDUR.'])

P('5.3 Potongan Kode Inti', h2)
codeblock('''def corridor_free(self, scan, theta, half_width):
    """Jarak bebas sepanjang koridor selebar 2*half_width ke arah theta."""
    ct, st = math.cos(theta), math.sin(theta)
    free = LOOKAHEAD
    for i, r in enumerate(scan):
        if r >= LOOKAHEAD + half_width:
            continue
        x = r * self.ray_cos[i]
        y = r * self.ray_sin[i]
        longi = x * ct + y * st          # komponen searah theta
        if longi <= 0.0:
            continue
        lat = -x * st + y * ct           # komponen menyamping
        if abs(lat) < half_width and longi < free:
            free = longi
    return free

# --- pemilihan arah pada state JELAJAH ---
for th in CANDIDATES:
    free = self.corridor_free(scan, th, hw)
    score = (min(free, LOOKAHEAD)
             - K_BIAS * abs(th - self.bias)
             - K_SMOOTH * abs(th - self.prev_theta))
    if score > best_score:
        best, best_score, best_free = th, score, free''')

# ---------------------------------------------------------------------------
# 6. Pengujian
# ---------------------------------------------------------------------------
P('6. Pengujian dan Hasil', h1)
P('6.1 Metode Pengujian', h2)
P('Supaya hasilnya objektif dan tidak hanya berdasarkan pengamatan visual, world dilengkapi robot '
  '<b>evaluator</b> (Supervisor). Evaluator hanya mengamati dan tidak memengaruhi robot. '
  'Tugas-tugasnya:')
bullets(['<b>Deteksi tabrakan</b>: memakai <i>contact points</i> robot dari physics engine. Setiap kontak '
         'di atas permukaan lantai (z > 8 mm) dihitung sebagai tabrakan. Metode ini sudah divalidasi '
         'dengan controller "buta" yang hanya maju lurus. Controller tersebut tercatat menabrak '
         '68 kali dalam 20 detik.',
         '<b>Clearance</b>: jarak analitik dari pusat robot ke permukaan obstacle atau dinding terdekat, '
         'dikurangi radius pembungkus robot (0.10 m). Nilai ini konservatif karena body robot berbentuk '
         'persegi panjang dan lebih kecil dari lingkaran pembungkusnya.',
         '<b>Coverage</b>: persentase sel grid 10 × 10 cm yang dapat dilalui robot dan sudah dikunjungi.'])
P('Pengujian dijalankan secara otomatis dan headless (<font face="DVM">tools/stress_test.sh</font>) dari '
  '8 posisi dan orientasi awal yang berbeda, masing-masing selama 300 detik simulasi dengan seed acak '
  'yang berbeda.')

P('6.2 Hasil', h2)
rows = [['Run', 'Posisi awal (x, y, heading)', 'Jarak tempuh', 'Tabrakan', 'Clearance min*', 'Coverage']]
for i, r in enumerate(stress):
    rows.append([str(i + 1), starts[i], f"{r['jarak_tempuh_m']:.1f} m", str(r['tabrakan']),
                 f"{r['clearance_min_m'] * 100:.1f} cm", f"{r['coverage_persen']:.1f} %"])
rows.append(['<b>Total</b>', f'<b>{tot_time / 60:.0f} menit simulasi</b>', f'<b>{tot_dist:.0f} m</b>',
             f'<b>{tot_col}</b>', f'<b>{min_clear * 100:.1f} cm</b>', f'<b>{avg_cov:.1f} %</b> (rata-rata)'])
table(rows, [1.6 * cm, 4.4 * cm, 2.4 * cm, 1.9 * cm, 2.6 * cm, 3.3 * cm],
      'Hasil uji ketahanan (8 run × 300 detik)')
P('<font size="8">*Clearance diukur dari lingkaran pembungkus robot berjari-jari 10 cm, sehingga jarak '
  'sebenarnya antara body robot dan obstacle lebih besar dari nilai ini.</font>')
P(f'Selama {tot_time / 60:.0f} menit simulasi dengan total jarak tempuh {tot_dist:.0f} m, robot '
  f'<b>tidak pernah menabrak</b> obstacle maupun dinding ({tot_col} tabrakan). Nilai clearance terkecil '
  f'adalah {min_clear * 100:.1f} cm terhadap lingkaran pembungkus, dan tidak pernah mendekati nol. '
  f'Dalam 5 menit robot rata-rata menjangkau {avg_cov:.0f} % area yang dapat dilalui. Robot melewati '
  f'celah di antara obstacle dan tidak hanya mengelilingi pinggir arena.')
fig('trajectory_all.png', 'Lintasan 8 run. Titik bulat menandai posisi awal. Robot menjelajahi '
    'hampir seluruh arena dan melewati celah di antara obstacle.', W * 0.78)
fig('trajectory_run1.png', 'Lintasan run 1, warna menunjukkan waktu.', W * 0.7)
fig('clearance.png', 'Kiri: clearance terhadap waktu pada run 1. Kanan: distribusi clearance dari '
    'seluruh run. Tidak ada sampel di bawah nol.', W)
fig('robot_avoid.jpg', 'Robot melewati celah di antara tabung dan dinding_tengah.', W * 0.8)

P('6.3 Evolusi Desain', h2)
P('Versi awal memakai bias jelajah acak dalam frame robot. Robot memang tidak menabrak, tetapi lintasannya '
  'menyatu menjadi satu lingkaran besar di sekitar kelompok obstacle tengah, dengan coverage sekitar '
  '38 %. Penyebabnya, bias yang konstan dalam frame robot membuat robot terus berbelok ke arah yang sama. '
  'Setelah bias diubah menjadi arah global (memakai odometri encoder), coverage naik menjadi sekitar '
  f'{avg_cov:.0f} % dan jumlah tabrakan tetap 0.')

# ---------------------------------------------------------------------------
# 7. Cara menjalankan
# ---------------------------------------------------------------------------
P('7. Cara Menjalankan', h1)
bullets(['Instal Webots R2025a (atau versi yang lebih baru) dan Python 3.',
         f'Clone repositori: <font face="DVM">git clone {REPO}.git</font>',
         'Di Webots, buka <font face="DVM">File → Open World…</font> lalu pilih '
         '<font face="DVM">worlds/obstacle_avoidance.wbt</font>, kemudian tekan Play.',
         'Console menampilkan state, jarak bebas, dan kecepatan setiap detik. Evaluator mencetak jumlah '
         'tabrakan, clearance, dan coverage setiap 10 detik.',
         'Aktifkan <font face="DVM">View → Optional Rendering → Show Lidar Ray Paths</font> untuk melihat '
         'sinar Lidar.',
         'Uji otomatis headless: <font face="DVM">tools/run_test.sh 180</font> (satu run) atau '
         '<font face="DVM">tools/stress_test.sh 300</font> (8 run). Grafik dibuat ulang dengan '
         '<font face="DVM">python3 tools/plot_results.py</font>.'])
P('Struktur repositori:', body)
codeblock('''webots-obstacle-avoidance-b401/
├── worlds/obstacle_avoidance.wbt          # arena + 12 obstacle + robot + evaluator
├── controllers/obstacle_avoidance/        # controller robot (Lidar + sonar)
├── controllers/evaluator/                 # supervisor pengukur tabrakan/clearance/coverage
├── tools/run_test.sh, stress_test.sh      # pengujian otomatis headless
├── tools/plot_results.py, make_report.py  # grafik & laporan PDF
└── docs/                                  # laporan PDF, gambar, hasil uji''')

# ---------------------------------------------------------------------------
# 8. Kesimpulan
# ---------------------------------------------------------------------------
P('8. Kesimpulan', h1)
bullets(['Robot differential drive kustom dengan Lidar 360° dan tiga sensor ultrasonik berhasil dibuat di '
         'Webots dengan struktur node yang sama seperti modul pelatihan.',
         'Algoritma Corridor Gap Selection memperhitungkan lebar robot secara eksplisit, sehingga robot '
         'hanya memilih celah yang benar-benar dapat dilalui. Ditambah state machine (JELAJAH, MUNDUR, '
         'PUTAR) dan watchdog macet, robot dapat keluar dari sudut cekung.',
         f'Pengujian kuantitatif selama {tot_time / 60:.0f} menit simulasi dari 8 posisi awal menghasilkan '
         f'<b>{tot_col} tabrakan</b> dengan total jarak tempuh {tot_dist:.0f} m dan coverage rata-rata '
         f'{avg_cov:.0f} % dalam 5 menit.',
         'Pengembangan selanjutnya: SLAM/occupancy grid untuk eksplorasi yang lebih sistematis, navigasi '
         'menuju titik tujuan (goal seeking), atau obstacle bergerak.'])

# ---------------------------------------------------------------------------
# Lampiran
# ---------------------------------------------------------------------------
story.append(PageBreak())
P('Lampiran A. Kode Lengkap Controller obstacle_avoidance.py', h1)
codeblock(open(os.path.join(ROOT, 'controllers', 'obstacle_avoidance', 'obstacle_avoidance.py')).read())


def on_page(c, doc):
    c.saveState()
    c.setFont('DV', 8)
    c.setFillColor(colors.HexColor('#666'))
    if doc.page > 1:
        c.drawString(2 * cm, 1.2 * cm, 'Tugas Pelatihan Lab B401 - Robot Obstacle Avoidance')
        c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f'Halaman {doc.page}')
        c.setStrokeColor(colors.HexColor('#c8ccd4'))
        c.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=2 * cm, title='Laporan Robot Obstacle Avoidance - Lab B401',
                        author='Ahnaf')
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print('PDF:', OUT)
