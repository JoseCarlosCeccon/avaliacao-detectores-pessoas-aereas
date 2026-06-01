from __future__ import annotations

import torch
from torchvision.ops import box_iou


def detection_counts(
    predictions: list[dict[str, torch.Tensor]],
    targets: list[dict[str, torch.Tensor]],
    score_threshold: float = 0.25,
    iou_threshold: float = 0.5,
) -> dict[str, int]:
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for prediction, target in zip(predictions, targets):
        pred_boxes = prediction["boxes"].detach().cpu()
        pred_scores = prediction["scores"].detach().cpu()
        pred_labels = prediction["labels"].detach().cpu()
        keep = (pred_scores >= score_threshold) & (pred_labels == 1)
        pred_boxes = pred_boxes[keep]
        pred_scores = pred_scores[keep]
        if len(pred_scores):
            order = torch.argsort(pred_scores, descending=True)
            pred_boxes = pred_boxes[order]

        gt_boxes = target["boxes"].detach().cpu()
        matched_gt: set[int] = set()
        if len(gt_boxes) == 0:
            false_positives += len(pred_boxes)
            continue
        if len(pred_boxes) == 0:
            false_negatives += len(gt_boxes)
            continue

        ious = box_iou(pred_boxes, gt_boxes)
        for pred_idx in range(len(pred_boxes)):
            best_iou, best_gt = torch.max(ious[pred_idx], dim=0)
            best_gt_idx = int(best_gt.item())
            if float(best_iou.item()) >= iou_threshold and best_gt_idx not in matched_gt:
                true_positives += 1
                matched_gt.add(best_gt_idx)
            else:
                false_positives += 1
        false_negatives += len(gt_boxes) - len(matched_gt)

    return {
        "tp": true_positives,
        "fp": false_positives,
        "fn": false_negatives,
    }


def precision_recall_f1(counts: dict[str, int]) -> dict[str, float]:
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall > 0 else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

