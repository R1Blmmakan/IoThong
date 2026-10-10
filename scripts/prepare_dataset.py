"""Salin atau tautkan TrashType IoTong ke layout Ultralytics.

Dataset sumber (ada di clone IoTong, tidak di-commit ke repo ini):

    dataset_raw/TrashType_Image_Dataset/
      cardboard/ glass/ metal/ paper/ plastic/ trash/
      train.txt  val.txt  data.yaml

Gambar dan label .txt berada di folder yang sama. train.txt / val.txt
berisi path relatif seperti ./cardboard/cardboard_152.jpg.
Setiap label adalah satu kotak: `<kelas> 0.5 0.5 0.85 0.85`.
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

CLASS_FROM_FOLDER = {
    "cardboard": 0,
    "glass": 1,
    "metal": 2,
    "paper": 3,
    "plastic": 4,
    "trash": 5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Siapkan dataset YOLO dari clone IoTong.")
    parser.add_argument(
        "--iotong",
        default=os.environ.get("IOTONG_ROOT", ""),
        help="Root clone https://github.com/R1Blmmakan/IoTong",
    )
    parser.add_argument(
        "--out",
        default="dataset",
        help="Folder keluaran (berisi data.yaml, images/, labels/)",
    )
    parser.add_argument(
        "--max-per-class-train",
        type=int,
        default=0,
        help="Batas gambar train per kelas. 0 = semua.",
    )
    parser.add_argument(
        "--max-per-class-val",
        type=int,
        default=0,
        help="Batas gambar val per kelas. 0 = semua.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Salin file. Default: symlink agar tidak menduplikasi 57 MB.",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=1.0,
        help="Ambil pecahan ini per kelas, di train dan di val. 0.5 = separuh.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=11,
        help="Seed acak tetap supaya pilihan separuh bisa diulang.",
    )
    return parser.parse_args()


def link_or_copy(src: Path, dst: Path, copy: bool) -> None:
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copy2(src, dst)
    else:
        dst.symlink_to(src.resolve())


def take_split(list_file: Path, root: Path, limit: int) -> list[Path]:
    chosen: list[Path] = []
    seen: Counter[str] = Counter()
    for raw in list_file.read_text(encoding="utf-8").splitlines():
        rel = raw.strip()
        if not rel:
            continue
        img = (root / rel.lstrip("./")).resolve()
        folder = img.parent.name
        if folder not in CLASS_FROM_FOLDER:
            raise SystemExit(f"Folder kelas tidak dikenal: {img}")
        if limit and seen[folder] >= limit:
            continue
        if not img.is_file():
            raise SystemExit(f"Gambar hilang: {img}")
        label = img.with_suffix(".txt")
        if not label.is_file():
            raise SystemExit(f"Label hilang: {label}")
        chosen.append(img)
        seen[folder] += 1
    return chosen


def stratify(images: list[Path], fraction: float, seed: int) -> list[Path]:
    """Ambil pecahan tiap kelas. Kelas tidak dibuang. Seed tetap."""
    if fraction >= 1:
        return images
    if fraction <= 0:
        raise SystemExit("--fraction harus di atas 0.")
    groups: dict[str, list[Path]] = defaultdict(list)
    for img in images:
        groups[img.parent.name].append(img)
    rng = random.Random(seed)
    chosen: list[Path] = []
    for name in sorted(groups):
        items = groups[name]
        rng.shuffle(items)
        keep = max(1, int(len(items) * fraction))
        chosen.extend(items[:keep])
        print(f"  {name:12} {keep}/{len(items)}")
    return chosen


def clear_split(out: Path, split: str) -> None:
    for kind in ("images", "labels"):
        folder = out / kind / split
        folder.mkdir(parents=True, exist_ok=True)
        for path in folder.iterdir():
            if path.name == ".gitkeep":
                continue
            if path.is_symlink() or path.is_file():
                path.unlink()


def place(images: list[Path], split: str, out: Path, copy: bool) -> None:
    img_dir = out / "images" / split
    lbl_dir = out / "labels" / split
    clear_split(out, split)
    for img in images:
        # Nama file unik antar kelas (cardboard_001.jpg, dst).
        link_or_copy(img, img_dir / img.name, copy)
        link_or_copy(img.with_suffix(".txt"), lbl_dir / f"{img.stem}.txt", copy)


def main() -> None:
    args = parse_args()
    if not args.iotong:
        raise SystemExit("Isi --iotong atau env IOTONG_ROOT ke root clone IoTong.")
    root = Path(args.iotong).expanduser().resolve() / "dataset_raw" / "TrashType_Image_Dataset"
    if not (root / "data.yaml").is_file():
        raise SystemExit(f"TrashType tidak ditemukan di {root}")

    out = Path(args.out).resolve()
    train = take_split(root / "train.txt", root, args.max_per_class_train)
    val = take_split(root / "val.txt", root, args.max_per_class_val)
    if args.fraction < 1:
        print(f"Train, fraction {args.fraction}, seed {args.seed}:")
        train = stratify(train, args.fraction, args.seed)
        print(f"Val, fraction {args.fraction}, seed {args.seed}:")
        val = stratify(val, args.fraction, args.seed)
    place(train, "train", out, args.copy)
    place(val, "val", out, args.copy)
    print(f"Train: {len(train)} gambar -> {out / 'images' / 'train'}")
    print(f"Val:   {len(val)} gambar -> {out / 'images' / 'val'}")
    print(f"Config: {out / 'data.yaml'}")


if __name__ == "__main__":
    main()
