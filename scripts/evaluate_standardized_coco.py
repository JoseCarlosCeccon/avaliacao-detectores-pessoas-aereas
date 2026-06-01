from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from torchvision.ops import box_iou
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tcc_detection.data import YoloPersonDetectionDataset
from tcc_detection.torchvision_pilot import build_faster_rcnn, build_ssd
from tcc_detection.visualization import draw_prediction_image


MODEL_NAMES = ("yolo11s", "faster_rcnn", "ssd")


def xyxy_to_xywh(box: list[float]) -> list[float]:
    x1, y1, x2, y2 = box
    return [float(x1), float(y1), float(max(0.0, x2 - x1)), float(max(0.0, y2 - y1))]


def xywh_to_xyxy(box: list[float]) -> list[float]:
    x, y, width, height = box
    return [float(x), float(y), float(x + width), float(y + height)]


def build_coco_ground_truth(dataset: YoloPersonDetectionDataset) -> dict[str, Any]:
    images: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    annotation_id = 1

    for index in range(len(dataset)):
        image_path = dataset.get_image_path(index)
        with Image.open(image_path) as image:
            width, height = image.size

        _, target = dataset[index]
        image_id = index + 1
        images.append(
            {
                "id": image_id,
                "file_name": image_path.name,
                "width": width,
                "height": height,
            }
        )
        for box in target["boxes"].tolist():
            bbox = xyxy_to_xywh(box)
            annotations.append(
                {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": 1,
                    "bbox": bbox,
                    "area": bbox[2] * bbox[3],
                    "iscrowd": 0,
                }
            )
            annotation_id += 1

    return {
        "info": {
            "description": "VisDrone person detection subset converted from YOLO labels",
            "version": "1.0",
        },
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": [{"id": 1, "name": "person", "supercategory": "person"}],
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def group_ground_truth(coco_gt: dict[str, Any]) -> dict[int, list[list[float]]]:
    grouped: dict[int, list[list[float]]] = defaultdict(list)
    for annotation in coco_gt["annotations"]:
        grouped[int(annotation["image_id"])].append(xywh_to_xyxy(annotation["bbox"]))
    return grouped


def detection_counts_from_coco(
    coco_gt: dict[str, Any],
    detections: list[dict[str, Any]],
    score_threshold: float,
    iou_threshold: float,
) -> dict[str, int]:
    gt_by_image = group_ground_truth(coco_gt)
    detections_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for detection in detections:
        if detection["category_id"] != 1 or float(detection["score"]) < score_threshold:
            continue
        detections_by_image[int(detection["image_id"])].append(detection)

    counts = {"tp": 0, "fp": 0, "fn": 0}
    image_ids = [int(image["id"]) for image in coco_gt["images"]]

    for image_id in image_ids:
        gt_boxes = torch.tensor(gt_by_image.get(image_id, []), dtype=torch.float32)
        image_detections = sorted(
            detections_by_image.get(image_id, []),
            key=lambda item: float(item["score"]),
            reverse=True,
        )
        pred_boxes = torch.tensor([xywh_to_xyxy(item["bbox"]) for item in image_detections], dtype=torch.float32)

        if gt_boxes.numel() == 0:
            counts["fp"] += len(pred_boxes)
            continue
        if pred_boxes.numel() == 0:
            counts["fn"] += len(gt_boxes)
            continue

        ious = box_iou(pred_boxes, gt_boxes)
        matched_gt: set[int] = set()
        for pred_idx in range(len(pred_boxes)):
            best_iou, best_gt = torch.max(ious[pred_idx], dim=0)
            best_gt_idx = int(best_gt.item())
            if float(best_iou.item()) >= iou_threshold and best_gt_idx not in matched_gt:
                counts["tp"] += 1
                matched_gt.add(best_gt_idx)
            else:
                counts["fp"] += 1
        counts["fn"] += len(gt_boxes) - len(matched_gt)

    return counts


def precision_recall_f1(counts: dict[str, int]) -> dict[str, float]:
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def coco_map_metrics(gt_path: Path, pred_path: Path, image_ids: list[int]) -> dict[str, float]:
    detections = json.loads(pred_path.read_text(encoding="utf-8"))
    if not detections:
        return {"map_50_95": 0.0, "map_50": 0.0}

    coco_gt = COCO(str(gt_path))
    coco_dt = coco_gt.loadRes(str(pred_path))
    evaluator = COCOeval(coco_gt, coco_dt, "bbox")
    evaluator.params.imgIds = image_ids
    evaluator.params.catIds = [1]
    evaluator.evaluate()
    evaluator.accumulate()
    evaluator.summarize()
    return {
        "map_50_95": float(evaluator.stats[0]),
        "map_50": float(evaluator.stats[1]),
    }


def prediction_to_tensor_dict(detections: list[dict[str, Any]], image_id: int) -> dict[str, torch.Tensor]:
    filtered = [item for item in detections if int(item["image_id"]) == image_id]
    return {
        "boxes": torch.tensor([xywh_to_xyxy(item["bbox"]) for item in filtered], dtype=torch.float32),
        "scores": torch.tensor([float(item["score"]) for item in filtered], dtype=torch.float32),
        "labels": torch.ones((len(filtered),), dtype=torch.int64),
    }


def load_torchvision_model(model_name: str, weights_path: Path, device: torch.device, args: argparse.Namespace):
    if model_name == "faster_rcnn":
        model = build_faster_rcnn(num_classes=2, pretrained=False)
        model.roi_heads.score_thresh = args.min_score_for_map
        model.roi_heads.nms_thresh = args.nms_iou
        model.roi_heads.detections_per_img = args.max_det
    elif model_name == "ssd":
        model = build_ssd(num_classes=2, pretrained=False)
        if hasattr(model, "score_thresh"):
            model.score_thresh = args.min_score_for_map
        if hasattr(model, "nms_thresh"):
            model.nms_thresh = args.nms_iou
        if hasattr(model, "detections_per_img"):
            model.detections_per_img = args.max_det
    else:
        raise ValueError(f"Unsupported TorchVision model: {model_name}")

    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


@torch.no_grad()
def evaluate_torchvision_model(
    model_name: str,
    weights_path: Path,
    dataset: YoloPersonDetectionDataset,
    output_dir: Path,
    device: torch.device,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    model = load_torchvision_model(model_name, weights_path, device, args)

    for warmup_index in range(min(args.warmup_samples, len(dataset))):
        image_tensor, _ = dataset[warmup_index]
        _ = model([image_tensor.to(device)])

    detections: list[dict[str, Any]] = []
    inference_times: list[float] = []
    saved_images = 0

    for index in range(len(dataset)):
        image_tensor, target = dataset[index]
        image_id = index + 1
        started = time.perf_counter()
        prediction = model([image_tensor.to(device)])[0]
        elapsed = time.perf_counter() - started
        inference_times.append(elapsed)

        boxes = prediction["boxes"].detach().cpu().tolist()
        scores = prediction["scores"].detach().cpu().tolist()
        labels = prediction["labels"].detach().cpu().tolist()
        for box, score, label in zip(boxes, scores, labels):
            if int(label) != 1:
                continue
            detections.append(
                {
                    "image_id": image_id,
                    "category_id": 1,
                    "bbox": xyxy_to_xywh(box),
                    "score": float(score),
                }
            )

        if saved_images < args.max_prediction_images:
            image_path = dataset.get_image_path(index)
            prediction_for_draw = prediction_to_tensor_dict(detections, image_id)
            draw_prediction_image(
                image_path,
                target,
                prediction_for_draw,
                output_dir / "prediction_images" / model_name / f"{image_path.stem}.jpg",
                score_threshold=args.score_threshold,
            )
            saved_images += 1

    mean_time = sum(inference_times) / max(1, len(inference_times))
    timing = {
        "total_inference_time_s": sum(inference_times),
        "mean_inference_time_s": mean_time,
        "fps": 1.0 / mean_time if mean_time > 0 else 0.0,
    }
    return detections, timing


def evaluate_yolo_model(
    weights_path: Path,
    dataset: YoloPersonDetectionDataset,
    output_dir: Path,
    device: torch.device,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    model = YOLO(str(weights_path))
    device_arg = str(device)

    for warmup_index in range(min(args.warmup_samples, len(dataset))):
        image_path = dataset.get_image_path(warmup_index)
        model.predict(
            source=str(image_path),
            imgsz=args.imgsz,
            conf=args.min_score_for_map,
            iou=args.nms_iou,
            max_det=args.max_det,
            device=device_arg,
            verbose=False,
        )

    detections: list[dict[str, Any]] = []
    inference_times: list[float] = []
    saved_images = 0

    for index in range(len(dataset)):
        image_path = dataset.get_image_path(index)
        _, target = dataset[index]
        image_id = index + 1
        started = time.perf_counter()
        results = model.predict(
            source=str(image_path),
            imgsz=args.imgsz,
            conf=args.min_score_for_map,
            iou=args.nms_iou,
            max_det=args.max_det,
            device=device_arg,
            verbose=False,
        )
        elapsed = time.perf_counter() - started
        inference_times.append(elapsed)

        result = results[0]
        if result.boxes is not None:
            boxes = result.boxes.xyxy.detach().cpu().tolist()
            scores = result.boxes.conf.detach().cpu().tolist()
            classes = result.boxes.cls.detach().cpu().tolist()
            for box, score, class_id in zip(boxes, scores, classes):
                if int(class_id) != 0:
                    continue
                detections.append(
                    {
                        "image_id": image_id,
                        "category_id": 1,
                        "bbox": xyxy_to_xywh(box),
                        "score": float(score),
                    }
                )

        if saved_images < args.max_prediction_images:
            prediction_for_draw = prediction_to_tensor_dict(detections, image_id)
            draw_prediction_image(
                image_path,
                target,
                prediction_for_draw,
                output_dir / "prediction_images" / "yolo11s" / f"{image_path.stem}.jpg",
                score_threshold=args.score_threshold,
            )
            saved_images += 1

    mean_time = sum(inference_times) / max(1, len(inference_times))
    timing = {
        "total_inference_time_s": sum(inference_times),
        "mean_inference_time_s": mean_time,
        "fps": 1.0 / mean_time if mean_time > 0 else 0.0,
    }
    return detections, timing


def build_metrics_row(
    model_name: str,
    coco_gt: dict[str, Any],
    gt_path: Path,
    pred_path: Path,
    detections: list[dict[str, Any]],
    timing: dict[str, float],
    args: argparse.Namespace,
) -> dict[str, Any]:
    image_ids = [int(image["id"]) for image in coco_gt["images"]]
    counts = detection_counts_from_coco(coco_gt, detections, args.score_threshold, args.iou_threshold)
    prf = precision_recall_f1(counts)
    map_metrics = coco_map_metrics(gt_path, pred_path, image_ids)
    return {
        "model": model_name,
        "split": args.split,
        "images": len(coco_gt["images"]),
        "gt_annotations": len(coco_gt["annotations"]),
        "detections": len(detections),
        "score_threshold": args.score_threshold,
        "iou_threshold": args.iou_threshold,
        "precision": prf["precision"],
        "recall": prf["recall"],
        "f1": prf["f1"],
        "map_50": map_metrics["map_50"],
        "map_50_95": map_metrics["map_50_95"],
        "tp": counts["tp"],
        "fp": counts["fp"],
        "fn": counts["fn"],
        "mean_inference_time_s": timing["mean_inference_time_s"],
        "fps": timing["fps"],
        "total_inference_time_s": timing["total_inference_time_s"],
        "predictions_json": str(pred_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate YOLO, Faster R-CNN, and SSD with a shared COCO protocol.")
    parser.add_argument("--dataset-root", type=Path, default=Path("datasets") / "visdrone_person_yolo_pilot")
    parser.add_argument("--split", choices=["val", "test"], default="val")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "evaluations" / "standardized_coco")
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=list(MODEL_NAMES))
    parser.add_argument("--yolo-weights", type=Path, default=Path("runs") / "detect" / "train2" / "weights" / "best.pt")
    parser.add_argument(
        "--faster-rcnn-weights",
        type=Path,
        default=Path("outputs") / "pilots" / "faster_rcnn" / "faster_rcnn_pilot_last.pt",
    )
    parser.add_argument("--ssd-weights", type=Path, default=Path("outputs") / "pilots" / "ssd" / "ssd_pilot_last.pt")
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--only-with-labels", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--score-threshold", type=float, default=0.25)
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument("--min-score-for-map", type=float, default=0.001)
    parser.add_argument("--nms-iou", type=float, default=0.7)
    parser.add_argument("--max-det", type=int, default=300)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--warmup-samples", type=int, default=1)
    parser.add_argument("--max-prediction-images", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device if args.device else ("cuda" if torch.cuda.is_available() else "cpu"))
    torch.manual_seed(args.seed)

    output_dir = args.output_dir / args.split
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = YoloPersonDetectionDataset(
        args.dataset_root,
        args.split,
        max_samples=args.max_samples if args.max_samples > 0 else None,
        seed=args.seed,
        only_with_labels=args.only_with_labels,
    )
    coco_gt = build_coco_ground_truth(dataset)
    gt_path = output_dir / "ground_truth_coco.json"
    write_json(gt_path, coco_gt)

    metrics_rows: list[dict[str, Any]] = []
    for model_name in args.models:
        print(f"Evaluating {model_name} on split={args.split} images={len(dataset)} device={device}")
        if model_name == "yolo11s":
            detections, timing = evaluate_yolo_model(args.yolo_weights, dataset, output_dir, device, args)
        elif model_name == "faster_rcnn":
            detections, timing = evaluate_torchvision_model(
                "faster_rcnn",
                args.faster_rcnn_weights,
                dataset,
                output_dir,
                device,
                args,
            )
        elif model_name == "ssd":
            detections, timing = evaluate_torchvision_model("ssd", args.ssd_weights, dataset, output_dir, device, args)
        else:
            raise ValueError(f"Unsupported model: {model_name}")

        pred_path = output_dir / f"{model_name}_predictions_coco.json"
        write_json(pred_path, detections)
        row = build_metrics_row(model_name, coco_gt, gt_path, pred_path, detections, timing, args)
        metrics_rows.append(row)
        print(f"{model_name}: precision={row['precision']:.4f} recall={row['recall']:.4f} "
              f"f1={row['f1']:.4f} map50={row['map_50']:.4f} map5095={row['map_50_95']:.4f} "
              f"fps={row['fps']:.4f}")

    write_csv(output_dir / "metrics_standardized.csv", metrics_rows)
    summary = {
        "dataset_root": str(args.dataset_root),
        "split": args.split,
        "images": len(dataset),
        "device": str(device),
        "score_threshold": args.score_threshold,
        "iou_threshold": args.iou_threshold,
        "min_score_for_map": args.min_score_for_map,
        "models": metrics_rows,
    }
    write_json(output_dir / "summary.json", summary)
    print(f"Saved standardized COCO evaluation outputs to {output_dir}")


if __name__ == "__main__":
    main()
