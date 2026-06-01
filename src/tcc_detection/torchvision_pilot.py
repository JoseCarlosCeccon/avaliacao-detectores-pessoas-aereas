from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision.models.detection import (
    FasterRCNN_ResNet50_FPN_Weights,
    SSD300_VGG16_Weights,
    fasterrcnn_resnet50_fpn,
    ssd300_vgg16,
)
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.ssd import SSDClassificationHead

from tcc_detection.data import YoloPersonDetectionDataset, collate_detection_batch
from tcc_detection.metrics import detection_counts, precision_recall_f1
from tcc_detection.visualization import draw_prediction_image


def build_faster_rcnn(num_classes: int, pretrained: bool = True) -> torch.nn.Module:
    weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT if pretrained else None
    weights_backbone = None if pretrained else None
    model = fasterrcnn_resnet50_fpn(weights=weights, weights_backbone=weights_backbone)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


def build_ssd(num_classes: int, pretrained: bool = True) -> torch.nn.Module:
    weights = SSD300_VGG16_Weights.DEFAULT if pretrained else None
    weights_backbone = None if pretrained else None
    model = ssd300_vgg16(weights=weights, weights_backbone=weights_backbone, num_classes=None if pretrained else num_classes)
    if pretrained:
        in_channels = [module.in_channels for module in model.head.classification_head.module_list]
        num_anchors = model.anchor_generator.num_anchors_per_location()
        model.head.classification_head = SSDClassificationHead(in_channels, num_anchors, num_classes)
    return model


def move_targets_to_device(targets: list[dict[str, torch.Tensor]], device: torch.device):
    return [{key: value.to(device) for key, value in target.items()} for target in targets]


def train_one_epoch(model, loader, optimizer, device: torch.device) -> dict[str, float]:
    model.train()
    totals: dict[str, float] = {}
    batches = 0
    for images, targets in loader:
        images = [image.to(device) for image in images]
        targets = move_targets_to_device(targets, device)
        loss_dict = model(images, targets)
        loss = sum(loss_value for loss_value in loss_dict.values())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        for key, value in loss_dict.items():
            totals[key] = totals.get(key, 0.0) + float(value.detach().cpu().item())
        totals["total_loss"] = totals.get("total_loss", 0.0) + float(loss.detach().cpu().item())
        batches += 1
    return {key: value / max(1, batches) for key, value in totals.items()}


@torch.no_grad()
def evaluate(model, loader, dataset, device: torch.device, output_dir: Path, score_threshold: float, max_prediction_images: int):
    model.eval()
    counts = {"tp": 0, "fp": 0, "fn": 0}
    saved_images = 0
    inference_times: list[float] = []

    for images, targets in loader:
        images_on_device = [image.to(device) for image in images]
        start = time.perf_counter()
        predictions = model(images_on_device)
        elapsed = time.perf_counter() - start
        inference_times.extend([elapsed / max(1, len(images))] * len(images))

        batch_counts = detection_counts(predictions, targets, score_threshold=score_threshold)
        for key in counts:
            counts[key] += batch_counts[key]

        if saved_images < max_prediction_images:
            for target, prediction in zip(targets, predictions):
                image_index = int(target["image_index"].item())
                image_path = dataset.get_image_path(image_index)
                output_path = output_dir / "predictions" / f"{image_path.stem}.jpg"
                draw_prediction_image(image_path, target, prediction, output_path, score_threshold=score_threshold)
                saved_images += 1
                if saved_images >= max_prediction_images:
                    break

    metrics = precision_recall_f1(counts)
    mean_inference_time = sum(inference_times) / max(1, len(inference_times))
    metrics.update(
        {
            "tp": counts["tp"],
            "fp": counts["fp"],
            "fn": counts["fn"],
            "mean_inference_time_s": mean_inference_time,
            "fps": 1.0 / mean_inference_time if mean_inference_time > 0 else 0.0,
        }
    )
    return metrics


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_pilot(model_name: str, args: argparse.Namespace) -> None:
    device = torch.device(args.device if args.device else ("cuda" if torch.cuda.is_available() else "cpu"))
    torch.manual_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_dataset = YoloPersonDetectionDataset(
        args.dataset_root,
        "train",
        max_samples=args.max_train_samples,
        seed=args.seed,
        only_with_labels=True,
    )
    val_dataset = YoloPersonDetectionDataset(
        args.dataset_root,
        "val",
        max_samples=args.max_val_samples,
        seed=args.seed,
        only_with_labels=True,
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.workers,
        collate_fn=collate_detection_batch,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        collate_fn=collate_detection_batch,
    )

    if model_name == "faster_rcnn":
        model = build_faster_rcnn(num_classes=2, pretrained=not args.no_pretrained)
    elif model_name == "ssd":
        model = build_ssd(num_classes=2, pretrained=not args.no_pretrained)
    else:
        raise ValueError(f"Unsupported model name: {model_name}")
    model.to(device)

    optimizer = torch.optim.SGD(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=args.lr,
        momentum=args.momentum,
        weight_decay=args.weight_decay,
    )

    losses: list[dict[str, object]] = []
    metrics_rows: list[dict[str, object]] = []
    started = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        epoch_started = time.perf_counter()
        loss_row = train_one_epoch(model, train_loader, optimizer, device)
        loss_row = {"epoch": epoch, "time_s": time.perf_counter() - epoch_started, **loss_row}
        losses.append(loss_row)
        metrics = evaluate(
            model,
            val_loader,
            val_dataset,
            device,
            output_dir,
            score_threshold=args.score_threshold,
            max_prediction_images=args.max_prediction_images if epoch == args.epochs else 0,
        )
        metrics_rows.append({"epoch": epoch, **metrics})
        print(f"epoch={epoch} losses={loss_row} metrics={metrics}")

    torch.save(model.state_dict(), output_dir / f"{model_name}_pilot_last.pt")
    write_csv(output_dir / "losses.csv", losses)
    write_csv(output_dir / "metrics.csv", metrics_rows)
    summary = {
        "model": model_name,
        "dataset_root": str(args.dataset_root),
        "train_images": len(train_dataset),
        "val_images": len(val_dataset),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "device": str(device),
        "pretrained": not args.no_pretrained,
        "score_threshold": args.score_threshold,
        "total_time_s": time.perf_counter() - started,
        "final_metrics": metrics_rows[-1] if metrics_rows else {},
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved pilot outputs to {output_dir}")


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--dataset-root", type=Path, default=Path("datasets") / "visdrone_person_yolo_pilot")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "pilots" / "torchvision")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=0.002)
    parser.add_argument("--momentum", type=float, default=0.9)
    parser.add_argument("--weight-decay", type=float, default=0.0005)
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-train-samples", type=int, default=50)
    parser.add_argument("--max-val-samples", type=int, default=20)
    parser.add_argument("--score-threshold", type=float, default=0.25)
    parser.add_argument("--max-prediction-images", type=int, default=8)
    parser.add_argument("--no-pretrained", action="store_true")
    return parser
