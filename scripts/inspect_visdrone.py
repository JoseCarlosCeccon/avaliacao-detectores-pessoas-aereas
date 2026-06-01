from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from PIL import Image


CLASS_NAMES = {
    0: "ignored_regions",
    1: "pedestrian",
    2: "people",
    3: "bicycle",
    4: "car",
    5: "van",
    6: "truck",
    7: "tricycle",
    8: "awning_tricycle",
    9: "bus",
    10: "motor",
    11: "others",
}

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


def find_split_dir(source_root: Path, split: str) -> Path:
    for candidate in SPLIT_CANDIDATES[split]:
        path = source_root / candidate
        if (path / "images").is_dir() and (path / "annotations").is_dir():
            return path
    searched = ", ".join(str(source_root / p) for p in SPLIT_CANDIDATES[split])
    raise FileNotFoundError(f"Could not find split {split}. Searched: {searched}")


def parse_annotation(path: Path) -> list[list[int]]:
    rows: list[list[int]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.rstrip(",").split(",")
        if len(parts) < 8:
            raise ValueError(f"{path}:{line_no} expected 8 columns, got {len(parts)}")
        rows.append([int(float(value)) for value in parts[:8]])
    return rows


def inspect_split(split_dir: Path) -> dict[str, object]:
    image_dir = split_dir / "images"
    annotation_dir = split_dir / "annotations"
    images = sorted(image_dir.glob("*.jpg"))
    annotations = sorted(annotation_dir.glob("*.txt"))
    image_stems = {p.stem for p in images}
    annotation_stems = {p.stem for p in annotations}

    class_counts: Counter[int] = Counter()
    size_counts: Counter[str] = Counter()
    total_boxes = 0
    invalid_boxes = 0
    person_boxes = 0

    for annotation in annotations:
        for x, y, w, h, score, category, truncation, occlusion in parse_annotation(annotation):
            class_counts[category] += 1
            total_boxes += 1
            if category in (1, 2):
                person_boxes += 1
            if w <= 0 or h <= 0:
                invalid_boxes += 1

    for image in images[:100]:
        with Image.open(image) as im:
            size_counts[f"{im.width}x{im.height}"] += 1

    return {
        "path": str(split_dir),
        "images": len(images),
        "annotations": len(annotations),
        "missing_annotations": sorted(image_stems - annotation_stems)[:20],
        "missing_images": sorted(annotation_stems - image_stems)[:20],
        "total_boxes": total_boxes,
        "person_boxes_pedestrian_plus_people": person_boxes,
        "invalid_boxes": invalid_boxes,
        "class_counts": {
            CLASS_NAMES.get(class_id, str(class_id)): count
            for class_id, count in sorted(class_counts.items())
        },
        "sample_image_sizes_first_100": dict(size_counts.most_common()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect VisDrone DET folders and annotations.")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("VisDrone"),
        help="Path to the folder containing VisDrone2019-DET-* directories.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to save the inspection report as JSON.",
    )
    args = parser.parse_args()

    report = {
        split: inspect_split(find_split_dir(args.source_root, split))
        for split in ("train", "val", "test")
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
