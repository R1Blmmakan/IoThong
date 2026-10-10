"""Ambil foto dataset dari webcam laptop.

Kamera: index OpenCV 0 (webcam laptop).
README IoTong memakai 0 untuk webcam laptop. Kode detect_trash.py
juga memakai 0 bila CAMERA_SOURCE tidak diisi. File .env.example
memakai SELECT; untuk laptop ini langkahnya tetap index 0.

Kelas = enam kelas TrashType di data.yaml IoTong:
  1 cardboard, 2 glass, 3 metal, 4 paper, 5 plastic, 6 trash

Foto masuk ke capture/<kelas>/. Belum ada label sampai label_dataset.py dijalankan.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2

from servo_map import CLASS_TO_ANGLE

CLASSES = list(CLASS_TO_ANGLE)
KEYS = {str(i + 1): name for i, name in enumerate(CLASSES)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rekam dataset sampah dari webcam index 0.")
    parser.add_argument("--camera", type=int, default=0, help="Index OpenCV. Laptop: 0.")
    parser.add_argument("--out", default="capture", help="Folder keluaran per kelas.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    for name in CLASSES:
        (out / name).mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(
            f"Webcam index {args.camera} tidak bisa dibuka. "
            "Di laptop Windows ini harusnya kamera bawaan. "
            "Mesin cloud tidak punya webcam, jadi langkah ini dijalankan di laptop."
        )

    print("Webcam terbuka. Satu foto = satu jenis sampah.")
    for key, name in KEYS.items():
        print(f"  tombol {key} -> {name}")
    print("  tombol q -> selesai")

    counts = {name: 0 for name in CLASSES}
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Gagal membaca frame.")
            break
        view = frame.copy()
        label = " | ".join(f"{k}:{n}({counts[n]})" for k, n in KEYS.items())
        cv2.putText(view, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.imshow("IoTong capture (q = selesai)", view)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        choice = chr(key) if key < 128 else ""
        if choice in KEYS:
            name = KEYS[choice]
            path = out / name / f"{name}_{int(time.time() * 1000)}.jpg"
            cv2.imwrite(str(path), frame)
            counts[name] += 1
            print(f"simpan {path}")

    cap.release()
    cv2.destroyAllWindows()
    print("Selesai. Lanjut: python scripts/label_dataset.py")


if __name__ == "__main__":
    main()
