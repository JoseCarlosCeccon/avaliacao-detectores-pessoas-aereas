from __future__ import annotations

import argparse
import os
import random
import shutil
from pathlib import Path


def has_labels(label_path: Path) -> bool:
    return label_path.exists() and bool(label_path.read_text(encoding="utf-8").strip())


def link_or_copy(src: Path, dst: Path, mode: str) -> None:
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(src, dst)
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def make_split(
    source_root: Path,
    output_root: Path,
    split: str,
    limit: int,
    seed: int,
    only_with_labels: bool,
    image_mode: str,
) -> int:
    image_dir = source_root / "images" / split
    label_dir = source_root / "labels" / split
    images = sorted(image_dir.glob("*.jpg"))
    if only_with_labels:
        images = [p for p in images if has_labels(label_dir / f"{p.stem}.txt")]
    random.Random(seed).shuffle(images)
    selected = images[:limit]

    for image_path in selected:
        label_path = label_dir / f"{image_path.stem}.txt"
        out_image = output_root / "images" / split / image_path.name
        out_label = output_root / "labels" / split / label_path.name
        if image_mode == "copy":
            shutil.copy2(image_path, out_image)
        else:
            link_or_copy(image_path, out_image, image_mode)
        out_label.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(label_path, out_label)

    return len(selected)


def write_yaml(output_root: Path) -> None:
    text = (
        f"path: {output_root.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: person\n"
    )
    (output_root / "visdrone_person_pilot.yaml").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a small YOLO subset for pilot experiments.")
    parser.add_argument("--source-root", type=Path, default=Path("datasets") / "visdrone_person_yolo")
    parser.add_argument("--output-root", type=Path, default=Path("datasets") / "visdrone_person_yolo_pilot")
    parser.add_argument("--train", type=int, default=300)
    parser.add_argument("--val", type=int, default=100)
    parser.add_argument("--test", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--include-empty-labels", action="store_true")
    parser.add_argument("--image-mode", choices=("hardlink", "copy"), default="hardlink")
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)
    only_with_labels = not args.include_empty_labels
    counts = {
        "train": make_split(args.source_root, args.output_root, "train", args.train, args.seed, only_with_labels, args.image_mode),
        "val": make_split(args.source_root, args.output_root, "val", args.val, args.seed, only_with_labels, args.image_mode),
        "test": make_split(args.source_root, args.output_root, "test", args.test, args.seed, only_with_labels, args.image_mode),
    }
    write_yaml(args.output_root)
    for split, count in counts.items():
        print(f"{split}: {count}")
    print(f"Dataset YAML: {args.output_root / 'visdrone_person_pilot.yaml'}")


if __name__ == "__main__":
    main()
