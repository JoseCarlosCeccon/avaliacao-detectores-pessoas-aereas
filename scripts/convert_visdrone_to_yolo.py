from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from PIL import Image


SPLIT_CANDIDATES = {
    "train": [
        Path("VisDrone2019-DET-train") / "VisDrone2019-DET-train",
        Path("VisDrone2019-DET-train"),
    ],
    "val": [
        Path("VisDrone2019-DET-val") / "VisDrone2019-DET-val",
        Path("VisDrone2019-DET-val"),
    ],
    "test": [
        Path("VisDrone2019-DET-test-dev (1)"),
        Path("VisDrone2019-DET-test-dev"),
    ],
}

# VisDrone DET category ids:
# 0 ignored, 1 pedestrian, 2 people, 3 bicycle, 4 car, 5 van, 6 truck,
# 7 tricycle, 8 awning-tricycle, 9 bus, 10 motor, 11 others.
PERSON_CLASS_IDS = {1, 2}


def find_split_dir(source_root: Path, split: str) -> Path:
    for candidate in SPLIT_CANDIDATES[split]:
        path = source_root / candidate
        if (path / "images").is_dir() and (path / "annotations").is_dir():
            return path
    searched = ", ".join(str(source_root / p) for p in SPLIT_CANDIDATES[split])
    raise FileNotFoundError(f"Could not find split {split}. Searched: {searched}")


def parse_annotation(path: Path) -> list[tuple[int, int, int, int, int]]:
    boxes: list[tuple[int, int, int, int, int]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.rstrip(",").split(",")
        if len(parts) < 8:
            raise ValueError(f"{path}:{line_no} expected 8 columns, got {len(parts)}")
        x, y, w, h, score, category, truncation, occlusion = [int(float(value)) for value in parts[:8]]
        boxes.append((x, y, w, h, category))
    return boxes


def to_yolo_line(x: int, y: int, w: int, h: int, image_w: int, image_h: int) -> str | None:
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(image_w, x + w)
    y2 = min(image_h, y + h)
    clipped_w = x2 - x1
    clipped_h = y2 - y1
    if clipped_w <= 0 or clipped_h <= 0:
        return None

    x_center = (x1 + clipped_w / 2) / image_w
    y_center = (y1 + clipped_h / 2) / image_h
    norm_w = clipped_w / image_w
    norm_h = clipped_h / image_h
    return f"0 {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}"


def link_or_copy_image(src: Path, dst: Path, mode: str) -> None:
    if dst.exists():
        return
    if mode == "none":
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(src, dst)
        return
    if mode == "symlink":
        try:
            dst.symlink_to(src)
            return
        except OSError:
            shutil.copy2(src, dst)
            return
    if mode == "hardlink":
        try:
            os.link(src, dst)
            return
        except OSError:
            shutil.copy2(src, dst)
            return
    raise ValueError(f"Unsupported image mode: {mode}")


def convert_split(source_root: Path, output_root: Path, split: str, image_mode: str) -> dict[str, int]:
    split_dir = find_split_dir(source_root, split)
    image_dir = split_dir / "images"
    annotation_dir = split_dir / "annotations"
    output_image_dir = output_root / "images" / split
    output_label_dir = output_root / "labels" / split
    output_label_dir.mkdir(parents=True, exist_ok=True)
    if image_mode != "none":
        output_image_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "images": 0,
        "labels_with_person": 0,
        "empty_labels": 0,
        "person_boxes": 0,
        "skipped_non_person_boxes": 0,
        "skipped_invalid_boxes": 0,
    }

    for image_path in sorted(image_dir.glob("*.jpg")):
        annotation_path = annotation_dir / f"{image_path.stem}.txt"
        if not annotation_path.exists():
            continue
        stats["images"] += 1
        with Image.open(image_path) as image:
            image_w, image_h = image.size

        yolo_lines: list[str] = []
        for x, y, w, h, category in parse_annotation(annotation_path):
            if category not in PERSON_CLASS_IDS:
                stats["skipped_non_person_boxes"] += 1
                continue
            line = to_yolo_line(x, y, w, h, image_w, image_h)
            if line is None:
                stats["skipped_invalid_boxes"] += 1
                continue
            yolo_lines.append(line)
            stats["person_boxes"] += 1

        label_path = output_label_dir / f"{image_path.stem}.txt"
        label_path.write_text("\n".join(yolo_lines) + ("\n" if yolo_lines else ""), encoding="utf-8")
        if yolo_lines:
            stats["labels_with_person"] += 1
        else:
            stats["empty_labels"] += 1

        link_or_copy_image(image_path, output_image_dir / image_path.name, image_mode)

    return stats


def write_dataset_yaml(output_root: Path) -> None:
    yaml_text = (
        f"path: {output_root.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: person\n"
    )
    (output_root / "visdrone_person.yaml").write_text(yaml_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert VisDrone DET annotations to YOLO person labels.")
    parser.add_argument("--source-root", type=Path, default=Path("VisDrone"))
    parser.add_argument("--output-root", type=Path, default=Path("datasets") / "visdrone_person_yolo")
    parser.add_argument(
        "--image-mode",
        choices=("hardlink", "copy", "symlink", "none"),
        default="hardlink",
        help="How to place images in the converted YOLO dataset.",
    )
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)
    all_stats = {}
    for split in ("train", "val", "test"):
        all_stats[split] = convert_split(args.source_root, args.output_root, split, args.image_mode)
    write_dataset_yaml(args.output_root)

    for split, stats in all_stats.items():
        print(split)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    print(f"\nDataset YAML: {args.output_root / 'visdrone_person.yaml'}")


if __name__ == "__main__":
    main()
