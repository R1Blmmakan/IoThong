"""Inferensi YOLO11 dan cetak perintah serial yang akan dikirim ke ESP32.

Perintah mengikuti detect_trash.py -> send_servo_command():
    pos <sudut>\\n
Firmware src/main.cpp menerapkan sudut itu ke servo GPIO 18 dan GPIO 19.
Kelas di luar enam kelas TrashType tidak menghasilkan perintah di skrip ini.
Di detect_trash.py, kelas tak dikenal jatuh ke fallback `pos 90`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.servo_map import CLASS_TO_ANGLE, serial_line


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inferensi YOLO11 dan peta perintah servo IoTong.")
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--source", required=True, help="Gambar, folder, atau URL.")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)
    results = model.predict(source=args.source, conf=args.conf, imgsz=args.imgsz, verbose=False)
    any_box = False
    for result in results:
        print(f"Sumber: {result.path}")
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            print("  tidak ada deteksi")
            continue
        for box in boxes:
            any_box = True
            cls_id = int(box.cls[0])
            name = str(model.names[cls_id])
            conf = float(box.conf[0])
            line = serial_line(name)
            if line is None:
                print(
                    f"  {name} {conf:.3f} -> bukan kelas TrashType; "
                    "tidak mengirim serial (detect_trash.py akan fallback ke 'pos 90')"
                )
            else:
                print(
                    f"  {name} {conf:.3f} -> sudut {CLASS_TO_ANGLE[name.lower()]} -> serial: {line.strip()}"
                )
    if not any_box:
        print("Tidak ada kotak. Servo tidak diperintah.")


if __name__ == "__main__":
    main()
