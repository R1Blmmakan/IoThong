# YOLO11 untuk servo IoTong

Latihan deteksi sampah YOLO11 yang menyambung ke firmware ESP32 di [IoTong](https://github.com/R1Blmmakan/IoTong). Repo IoTong tidak disalin ke sini. Yang ada di sini: layout dataset, skrip latih, deteksi webcam, dan pengirim serial dengan perintah yang sama seperti firmware.

Kamera di laptop Windows: index OpenCV `0`.
Pratinjau browser, hanya di laptop yang menjalankan skrip: `http://127.0.0.1:43123`.
Servo: serial `COM3`, 19200 8N1 (DTR dan RTS hidup, tanpa flow control). `43123` bukan port servo.

## Pasang

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Lima langkah di laptop

Kelas diambil dari `dataset_raw/TrashType_Image_Dataset/data.yaml` di IoTong: `cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash`.

### 1. Rekam dari webcam

```bat
python scripts/capture_webcam.py --camera 0
```

Tombol `1` cardboard, `2` glass, `3` metal, `4` paper, `5` plastic, `6` trash, `q` selesai.
Foto masuk ke `capture/<kelas>/`. Satu foto satu jenis, objek mengisi sebagian besar frame.
Dataset repo punya 137–594 foto per kelas. Di bawah puluhan foto per kelas, model masih lemah.

### 2. Beri label

Asumsi: satu foto di `capture/<kelas>/` adalah satu objek kelas itu, dan kotaknya mengikuti seluruh label TrashType (`0.5 0.5 0.85 0.85`).

```bat
python scripts/label_dataset.py
```

Hasilnya mengisi `dataset/images` dan `dataset/labels`. `dataset/data.yaml` sudah berisi enam kelas.

Kalau objek kecil di dalam frame, jangan pakai skrip itu. Gambar kotak di [LabelImg](https://github.com/HumanSignal/labelImg) (format YOLO), simpan `.txt` di samping foto, lalu jalankan skrip yang sama. File `.txt` yang sudah ada tidak ditimpa rumus kotak repo.

Dataset TrashType yang sudah berlabel bisa dipakai tanpa webcam:

```bat
python scripts/prepare_dataset.py --iotong C:\path\ke\IoTong
```

### 3. Latih YOLO11

```bat
python scripts/prepare_dataset.py --iotong C:\path\ke\IoTong --fraction 0.5 --seed 11
python scripts/train.py --model yolo11n.pt --data dataset/data.yaml --epochs 3 --imgsz 640 --batch 8 --device cpu
```

Tiga epoch pada separuh TrashType (seed 11, tiap kelas tetap ada). `yolo11n.pt` diunduh pada run pertama. GPU NVIDIA: ganti `--device 0`.
Bobot keluar di `runs/detect/train/weights/best.pt`. Folder `runs/` dan `*.pt` tidak di-commit.

### 4. Buka deteksi kamera (Native 30 FPS / Browser)

Perintah ini di laptop. Default membuka jendela Native OpenCV (latensi <5ms, 30 FPS).
Gunakan `--web` bila ingin menyalakan pratinjau browser paralel di `http://127.0.0.1:43123`.

```bat
# Mode Native OpenCV (Default):
python scripts/live_webcam.py --camera 0 --model runs/detect/train/weights/best.pt

# Mode Dual (Native + Pratinjau Web Browser):
python scripts/live_webcam.py --camera 0 --model runs/detect/train/weights/best.pt --web
```

Tekan **Q** atau **ESC** di jendela untuk keluar. Servo belum dikirim pada perintah ini.

### 5. Kirim ke servo lewat COM3, 19200 8N1

`mode COM3` di laptop: baud 19200, parity None, data 8, stop 1, timeout OFF, XON/XOFF OFF, CTS OFF, DSR OFF, DTR ON, RTS ON.

Firmware `src/main.cpp` memakai `Serial.begin(115200)`. `platformio.ini` dan `detect_trash.py` juga 115200. Framing 8N1 sama dengan bawaan Arduino. Baud tidak sama. Pengirim tetap 19200, tidak diubah diam-diam menjadi 115200.

Perintah deteksi di commit `8625083`: `sort <derajat>\n`, misalnya `b"sort 135\n"`. Wadah di GPIO 19 berputar, lalu trapdoor GPIO 18 membuka ke 0 dan menutup ke 180.

```bat
python scripts/send_servo.py --dry-run --port COM3 --class cardboard
python scripts/live_webcam.py --camera 0 --model runs/detect/train/weights/best.pt --port COM3
```

`--port COM3` membuka serial. Angka 43123 tetap hanya halaman pratinjau.

| Kelas | Perintah | Sudut wadah |
| --- | --- | --- |
| cardboard | `sort 135` | 135 |
| paper | `sort 135` | 135 |
| glass | `sort 90` | 90 |
| metal | `sort 90` | 90 |
| plastic | `sort 90` | 90 |
| trash | `sort 90` | 90 |

`organic` (45 derajat) dan B3 seperti `cable` / `battery` (180) ada di peta baru, tidak ada di dataset TrashType.

## Yang tidak bisa dijalankan di mesin cloud

Tidak ada webcam laptop di mesin cloud. Halaman `127.0.0.1:43123` di mesin itu bukan siaran kamera pengguna.
COM3 ada di laptop. `send_servo.py` di mesin ini tidak membuka port itu.

Uji yang bisa di sini: `--dry-run`, inferensi satu gambar dengan `yolo11n.pt`, dan latih singkat pada TrashType yang sudah berlabel.

```bash
python scripts/servo_map.py
python scripts/send_servo.py --dry-run --port COM3 --class plastic
python scripts/infer.py --model yolo11n.pt --source /path/gambar.jpg
```

Hasil perintah yang benar-benar dijalankan dicatat di `docs` studi IoTong pada store proyek, dan diperbarui di bagian bawah README setelah uji selesai.
