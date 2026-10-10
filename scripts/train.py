"""Latih YOLO11 pada dataset TrashType yang sudah disiapkan.

Bobot awal resmi: yolo11n.pt (diunduh Ultralytics pada run pertama).
Tidak ada bobot custom di repo ini. Jangan menganggap hasil smoke
beberapa gambar sebagai model pemilah yang siap pakai.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Training YOLO11 untuk kelas sampah IoTong.")
    parser.add_argument("--model", default="yolo11n.pt", help="Bobot awal. Default YOLO11n resmi.")
    parser.add_argument("--data", default="dataset/data.yaml")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--project", default="runs/detect")
    parser.add_argument("--name", default="train")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = Path(args.data)
    if not data.is_file():
        raise SystemExit(f"data.yaml tidak ada: {data}")
    train_dir = data.parent / "images" / "train"
    images = [p for p in train_dir.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    if not images:
        raise SystemExit(
            "Folder dataset/images/train kosong. "
            "Jalankan scripts/prepare_dataset.py --iotong /path/ke/IoTong dulu."
        )
    model = YOLO(args.model)
    model.train(
        data=str(data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        exist_ok=True,
        plots=False,
    )
    print("Bobot: runs/detect/train/weights/best.pt")
    print("Lalu inferensi: python scripts/infer.py --model runs/detect/train/weights/best.pt --source <gambar>")


if __name__ == "__main__":
    main()
