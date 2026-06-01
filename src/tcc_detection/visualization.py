from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont


def draw_prediction_image(
    image_path: Path,
    target: dict[str, torch.Tensor],
    prediction: dict[str, torch.Tensor],
    output_path: Path,
    score_threshold: float = 0.25,
) -> None:
    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        for box in target["boxes"].detach().cpu().tolist():
            draw.rectangle(box, outline="red", width=2)
            draw.text((box[0], max(0, box[1] - 10)), "gt person", fill="red", font=font)

        boxes = prediction["boxes"].detach().cpu()
        scores = prediction["scores"].detach().cpu()
        labels = prediction["labels"].detach().cpu()
        for box, score, label in zip(boxes.tolist(), scores.tolist(), labels.tolist()):
            if label != 1 or score < score_threshold:
                continue
            draw.rectangle(box, outline="lime", width=2)
            draw.text((box[0], box[1]), f"pred {score:.2f}", fill="lime", font=font)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

