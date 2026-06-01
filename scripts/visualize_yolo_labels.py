from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def read_yolo_labels(label_path: Path) -> list[tuple[float, float, float, float]]:
    boxes: list[tuple[float, float, float, float]] = []
    if not label_path.exists():
        return boxes
    for line in label_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        class_id, x_center, y_center, width, height = line.split()
        if class_id != "0":
            continue
        boxes.append((float(x_center), float(y_center), float(width), float(height)))
    return boxes


def draw_sample(image_path: Path, label_path: Path, output_path: Path) -> int:
    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        count = 0
        for x_center, y_center, width, height in read_yolo_labels(label_path):
            img_w, img_h = image.size
            box_w = width * img_w
            box_h = height * img_h
            x1 = (x_center * img_w) - box_w / 2
            y1 = (y_center * img_h) - box_h / 2
            x2 = x1 + box_w
            y2 = y1 + box_h
            draw.rectangle((x1, y1, x2, y2), outline="red", width=2)
            draw.text((x1, max(0, y1 - 10)), "person", fill="red", font=font)
            count += 1
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw YOLO labels on VisDrone person samples.")
    parser.add_argument("--dataset-root", type=Path, default=Path("datasets") / "visdrone_person_yolo")
    parser.add_argument("--split", choices=("train", "val", "test"), default="val")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "sanity_checks" / "yolo_labels")
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--only-with-labels", action="store_true")
    args = parser.parse_args()

    image_dir = args.dataset_root / "images" / args.split
    label_dir = args.dataset_root / "labels" / args.split
    images = sorted(image_dir.glob("*.jpg"))
    if args.only_with_labels:
        images = [p for p in images if read_yolo_labels(label_dir / f"{p.stem}.txt")]
    random.Random(args.seed).shuffle(images)

    selected = images[: args.samples]
    for image_path in selected:
        label_path = label_dir / f"{image_path.stem}.txt"
        output_path = args.output_dir / args.split / image_path.name
        count = draw_sample(image_path, label_path, output_path)
        print(f"{output_path} boxes={count}")


if __name__ == "__main__":
    main()
