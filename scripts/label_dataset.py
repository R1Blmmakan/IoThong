"""Beri label YOLO pada foto webcam, mengikuti kebiasaan dataset IoTong.

Asumsi, satu baris: setiap foto di capture/<kelas>/ adalah satu objek kelas itu,
dan kotaknya sama dengan seluruh 2527 label TrashType, yaitu `0.5 0.5 0.85 0.85`.

Kalau objek tidak memenuhi frame, jangan pakai skrip ini. Gambar kotak
di LabelImg (format YOLO) lalu taruh .txt di samping gambar sebelum split.
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

from servo_map import CLASS_TO_ANGLE

CLASSES = list(CLASS_TO_ANGLE)
REPO_BOX = "0.5 0.5 0.85 0.85"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Label foto capture/ menjadi dataset YOLO.")
    parser.add_argument("--capture", default="capture")
    parser.add_argument("--out", default="dataset")
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=11)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    capture = Path(args.capture)
    out = Path(args.out)
    random.seed(args.seed)
    train_n = 0
    val_n = 0

    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    for cls_id, name in enumerate(CLASSES):
        folder = capture / name
        images = sorted(
            p for p in folder.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ) if folder.is_dir() else []
        if not images:
            print(f"{name}: 0 foto")
            continue
        random.shuffle(images)
        cut = int(len(images) * (1.0 - args.val_ratio))
        if len(images) > 1:
            cut = min(max(cut, 1), len(images) - 1)
        else:
            cut = 1
        for index, image in enumerate(images):
            split = "train" if index < cut else "val"
            dest_img = out / "images" / split / image.name
            dest_lbl = out / "labels" / split / f"{image.stem}.txt"
            shutil.copy2(image, dest_img)
            sidecar = image.with_suffix(".txt")
            if sidecar.is_file():
                dest_lbl.write_text(sidecar.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                dest_lbl.write_text(f"{cls_id} {REPO_BOX}\n", encoding="utf-8")
            if split == "train":
                train_n += 1
            else:
                val_n += 1
        print(f"{name}: {len(images)} foto, id {cls_id}")

    if train_n == 0:
        raise SystemExit(
            f"Tidak ada foto di {capture}/<kelas>/. "
            "Jalankan capture_webcam.py di laptop dulu."
        )
    print(f"Train {train_n}, val {val_n}. Config tetap {out / 'data.yaml'}.")


if __name__ == "__main__":
    main()
