# TCC - VisDrone Person Detection

This repository contains the code and data preparation utilities for the TCC experiments on person detection in aerial drone images.

## Dataset

Raw VisDrone DET data is expected at:

```text
VisDrone/
```

The local dataset currently contains:

| Split | Images | Original annotations | Person boxes |
| --- | ---: | ---: | ---: |
| train | 6471 | 6471 | 106396 |
| val | 548 | 548 | 13969 |
| test | 1610 | 1610 | 27382 |

The converted YOLO dataset merges VisDrone categories `pedestrian` and `people` into a single class:

```text
0 person
```

## Dataset Commands

Inspect the original VisDrone folders:

```powershell
python .\scripts\inspect_visdrone.py --source-root .\VisDrone --output-json .\outputs\dataset_reports\visdrone_inspection.json
```

Convert VisDrone DET annotations to YOLO format:

```powershell
python .\scripts\convert_visdrone_to_yolo.py --source-root .\VisDrone --output-root .\datasets\visdrone_person_yolo --image-mode hardlink
```

Generate visual sanity-check images:

```powershell
python .\scripts\visualize_yolo_labels.py --dataset-root .\datasets\visdrone_person_yolo --split val --samples 12 --only-with-labels
```

YOLO dataset configuration:

```text
datasets/visdrone_person_yolo/visdrone_person.yaml
```

Create a small pilot subset before training all final models:

```powershell
python .\scripts\make_yolo_subset.py --source-root .\datasets\visdrone_person_yolo --output-root .\datasets\visdrone_person_yolo_pilot --train 300 --val 100 --test 100
```

## YOLO Pilot

Start with a small YOLO pilot training run:

```powershell
yolo detect train model=yolo11s.pt data=.\datasets\visdrone_person_yolo_pilot\visdrone_person_pilot.yaml epochs=3 imgsz=640 batch=4 device=cpu
```

If a CUDA GPU is available, replace `device=cpu` with the GPU device, for example `device=0`.

## TorchVision Pilots

Faster R-CNN and SSD use the same converted YOLO dataset through a PyTorch `Dataset` class in:

```text
src/tcc_detection/data.py
```

The loader converts YOLO labels from:

```text
0 x_center y_center width height
```

to TorchVision targets:

```python
{
    "boxes": Tensor[[x1, y1, x2, y2]],
    "labels": Tensor[1, 1, ...]
}
```

Class `0` in YOLO means `person`, but class `0` in TorchVision detection models is background. For this reason, the dataset maps `person` to class `1` for Faster R-CNN and SSD.

Run a Faster R-CNN pilot:

```powershell
python .\scripts\train_faster_rcnn_pilot.py --dataset-root .\datasets\visdrone_person_yolo_pilot --epochs 1 --batch-size 1 --max-train-samples 50 --max-val-samples 20 --device cpu
```

Run an SSD300 VGG16 pilot:

```powershell
python .\scripts\train_ssd_pilot.py --dataset-root .\datasets\visdrone_person_yolo_pilot --epochs 1 --batch-size 1 --max-train-samples 50 --max-val-samples 20 --device cpu
```

Each pilot saves:

```text
outputs/pilots/<model>/
  losses.csv
  metrics.csv
  summary.json
  predictions/
  *_pilot_last.pt
```

A lightweight summary of the pilot runs is tracked in:

```text
experiments/pilot_results.md
```

These pilots are intended to validate the experimental pipeline. They are not final TCC results.

## Standardized COCO Evaluation

After the pilot trainings, evaluate all models with the same COCO-style protocol:

```powershell
python .\scripts\evaluate_standardized_coco.py --dataset-root .\datasets\visdrone_person_yolo_pilot --split test --output-dir .\outputs\evaluations\pilot_standardized --device cpu
```

The script evaluates YOLO11s, Faster R-CNN, and SSD on the same split and saves:

```text
outputs/evaluations/pilot_standardized/<split>/
  ground_truth_coco.json
  yolo11s_predictions_coco.json
  faster_rcnn_predictions_coco.json
  ssd_predictions_coco.json
  metrics_standardized.csv
  summary.json
  prediction_images/
```

The standardized metrics include precision, recall, F1-score, mAP@0.5, mAP@0.5:0.95, mean inference time, and FPS.

A lightweight summary of the standardized pilot evaluation is tracked in:

```text
experiments/standardized_coco_pilot_results.md
```
