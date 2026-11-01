# Log Pengerjaan

Catatan kronologis sesi pengerjaan bersama Claude Code. Waktu dalam WIB.
Detail teknis lengkap ada di [AGENTS.md](AGENTS.md).

---

## Sesi 1: Sabtu 31 Okt 21.27 – Minggu 1 Nov 05.51

Sesi ini dijalankan dari folder `~/Documents/Barunastra`, jadi transkripnya tersimpan di
`~/.claude/projects/-home-ahnaf-Documents-Barunastra/`.

| Waktu | Permintaan | Hasil |
|---|---|---|
| 21.27 | Kerjakan tugas Lab B401 (robot obstacle avoidance di Webots) end-to-end, repo publik, dokumentasi PDF | Robot **beroda** differential drive dengan Lidar 360° + ultrasonik, arena berobstacle, evaluator, laporan PDF. Commit `9230c3c` |
| 23.45 | Slide presentasi bergaya deck magang di `/barunastra/c16` | Slide HTML → PDF. Commit `c87fef8` |
| 23.52–00.04 | Cara menjalankan, objektif, lokasi program, peta Lidar, RViz2 | ROS 2 bridge + RViz2 (`f7f2e8b`), fix crash RViz di Wayland lewat XWayland (`c6f884f`) |
| 00.34 | Hapus Barunastra/ITS dari slide, ganti ke **humanoid** dengan Lidar di atas, rumus benar, RViz semua sensor, tingkatkan coverage | Humanoid NAO + gait engine sendiri, navigasi kebaruan, watchdog, RViz2 semua sensor, slide tanpa logo, laporan ditulis ulang |
| 02.53 | (stress test) | 32 uji × 10 menit: 0 tabrakan, 0 jatuh, coverage 42.9 % vs acak 30.3 % (+42 %) |
| 03.06 | | Commit `c32f97d` (mulai tanpa trailer Claude) |
| 05.33 | Simpan semua cara kerja dan objektif ke `.md` | `AGENTS.md` + `CLAUDE.md`. Commit `460ef55` |
| 05.50 | Tutup semua simulasi | Webots, RViz2, robot_state_publisher ditutup |

---

## Sesi 2: Minggu 1 Nov (sore)

| Permintaan | Hasil |
|---|---|
| Rekap sesi kemarin | Kronologi dari transkrip sesi 1 |
| Buka slide paparan, buat **PDF naskah presentasi** lengkap dengan penjelasan teknis, buka Webots + RViz | `docs/Naskah_Presentasi_B401.pdf` dari generator baru `tools/make_naskah.py`: panduan durasi, cerita pengerjaan, naskah per slide (thumbnail, yang diucapkan, rumus, detail teknis cadangan), persiapan tanya jawab, tabel angka penting. Webots + RViz2 dijalankan lewat `tools/rviz.sh` |
| Sampul slide jangan "Lidar 360° di kepala", tulis daftar sensor; nama lengkap | Sampul: "Sensor: Lidar 360° · Sonar · IMU · Gyro · Accelerometer · GPS · FSR Kaki · Kamera". Nama **Ahnaf Al Ghiffarri Ahtasyafi** di slide, naskah, dan laporan |
| Ganti "Kenapa sulit" (slide 5) dengan tantangan membuat humanoid; naskah ikut | Kotak "Tantangan membuat humanoid": Jatuh, Belok, Berhenti, Lengan. Naskah slide 5 menjelaskan keempatnya |
| "Pulsa" diganti bahasa yang familiar di slide dan naskah | "Pinggul diputar sedikit saat kaki terangkat, lalu dikembalikan saat menapak"; "per siklus" → "tiap 2 langkah". Label grafik gait ikut diganti (`tools/plot_results.py`) |
| Perbaiki diagram state machine | Digambar ulang sesuai `decide()`: SIAP sebagai pusat; JALAN (siklus berulang), BERHENTI → SIAP, PUTAR, MUNDUR/maju kecil, BANGUN, watchdog. Naskah slide 15 mengikuti alur diagram |
| Penjelasan beda coverage acak vs kebaruan | Dijelaskan di chat (memori sel 1/(1+n) vs arah acak tiap 20 s) |
| Hapus kotak `tools/rviz.sh` dari slide 22, cukup di naskah | Kotak dihapus dari slide; perintah tetap ada di naskah |
| Asal model NAO dan cara engsel dibuat/digerakkan/dihubungkan; tambahkan ke tanya jawab | 4 pertanyaan baru di naskah: asal model NAO (PROTO Webots/Cyberbotics, robot asli Aldebaran/SoftBank), struktur engsel (HingeJoint + motor + sensor), cara menggerakkan (gait engine → `setPosition`), alur keterhubungan (sensor → decide → gait → motor → fisika; ROS 2 → RViz2) |

Angka hasil uji tidak berubah (`docs/stress_results.json` sama); hanya gambar dan dokumen yang dibangun ulang.
