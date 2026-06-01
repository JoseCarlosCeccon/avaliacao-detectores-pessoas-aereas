from __future__ import annotations

import random
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import functional as F


class YoloPersonDetectionDataset(Dataset):
    """Read YOLO person labels and return TorchVision detection targets.

    The YOLO dataset uses class 0 for person. TorchVision detection models reserve
    class 0 for background, so person labels are converted to class 1.
    """

    def __init__(
        self,
        dataset_root: Path | str,
        split: str,
        max_samples: int | None = None,
        seed: int = 42,
        only_with_labels: bool = False,
    ) -> None:
        self.dataset_root = Path(dataset_root)
        self.split = split
        self.image_dir = self.dataset_root / "images" / split
        self.label_dir = self.dataset_root / "labels" / split
        if not self.image_dir.is_dir():
            raise FileNotFoundError(f"Image directory not found: {self.image_dir}")
        if not self.label_dir.is_dir():
            raise FileNotFoundError(f"Label directory not found: {self.label_dir}")

        image_paths = sorted(self.image_dir.glob("*.jpg"))
        if only_with_labels:
            image_paths = [path for path in image_paths if self._has_nonempty_label(path)]
        if max_samples is not None and max_samples > 0:
            rng = random.Random(seed)
            image_paths = image_paths[:]
            rng.shuffle(image_paths)
            image_paths = sorted(image_paths[:max_samples])
        self.image_paths = image_paths
        if not self.image_paths:
            raise ValueError(f"No images found for split '{split}' in {self.image_dir}")

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        image_path = self.image_paths[index]
        with Image.open(image_path).convert("RGB") as image:
            width, height = image.size
            boxes = self._read_boxes(image_path.stem, width, height)
            image_tensor = F.to_tensor(image)

        labels = torch.ones((len(boxes),), dtype=torch.int64)
        boxes_tensor = torch.as_tensor(boxes, dtype=torch.float32)
        if boxes_tensor.numel() == 0:
            boxes_tensor = torch.zeros((0, 4), dtype=torch.float32)
        area = (boxes_tensor[:, 2] - boxes_tensor[:, 0]) * (boxes_tensor[:, 3] - boxes_tensor[:, 1])

        target = {
            "boxes": boxes_tensor,
            "labels": labels,
            "image_id": torch.tensor([index], dtype=torch.int64),
            "image_index": torch.tensor([index], dtype=torch.int64),
            "area": area,
            "iscrowd": torch.zeros((len(boxes),), dtype=torch.int64),
        }
        return image_tensor, target

    def get_image_path(self, index: int) -> Path:
        return self.image_paths[index]

    def _has_nonempty_label(self, image_path: Path) -> bool:
        label_path = self.label_dir / f"{image_path.stem}.txt"
        return label_path.exists() and bool(label_path.read_text(encoding="utf-8").strip())

    def _read_boxes(self, stem: str, image_w: int, image_h: int) -> list[list[float]]:
        label_path = self.label_dir / f"{stem}.txt"
        if not label_path.exists():
            return []

        boxes: list[list[float]] = []
        for line_no, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 5:
                raise ValueError(f"{label_path}:{line_no} expected 5 YOLO columns, got {len(parts)}")
            class_id = int(parts[0])
            if class_id != 0:
                continue
            x_center, y_center, width, height = [float(value) for value in parts[1:]]
            box_w = width * image_w
            box_h = height * image_h
            x1 = (x_center * image_w) - box_w / 2
            y1 = (y_center * image_h) - box_h / 2
            x2 = x1 + box_w
            y2 = y1 + box_h
            x1 = max(0.0, min(float(image_w), x1))
            y1 = max(0.0, min(float(image_h), y1))
            x2 = max(0.0, min(float(image_w), x2))
            y2 = max(0.0, min(float(image_h), y2))
            if x2 <= x1 or y2 <= y1:
                continue
            boxes.append([x1, y1, x2, y2])
        return boxes


def collate_detection_batch(batch: list[tuple[torch.Tensor, dict[str, torch.Tensor]]]):
    images, targets = zip(*batch)
    return list(images), list(targets)

