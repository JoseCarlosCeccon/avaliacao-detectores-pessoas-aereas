# Standardized COCO Pilot Evaluation

Date: 2026-06-01

This file records the standardized pilot evaluation executed with a shared COCO-style protocol for YOLO11s, Faster R-CNN ResNet-50 FPN, and SSD300 VGG16. The full outputs are stored locally under `outputs/evaluations/pilot_standardized/` and are ignored by Git because they include prediction JSON files and rendered prediction images.

## Protocol

| Item | Value |
| --- | --- |
| Dataset | `datasets/visdrone_person_yolo_pilot` |
| Splits evaluated | `val` and `test` |
| Images per split | 100 |
| Class | `person` |
| Ground truth format | COCO JSON |
| Prediction format | COCO detection JSON |
| Score threshold for precision/recall/F1 | 0.25 |
| IoU threshold for precision/recall/F1 | 0.50 |
| mAP protocol | COCO bbox AP |
| Device | CPU |

## Commands

```powershell
python .\scripts\evaluate_standardized_coco.py --dataset-root .\datasets\visdrone_person_yolo_pilot --split val --output-dir .\outputs\evaluations\pilot_standardized --device cpu --max-prediction-images 4
```

```powershell
python .\scripts\evaluate_standardized_coco.py --dataset-root .\datasets\visdrone_person_yolo_pilot --split test --output-dir .\outputs\evaluations\pilot_standardized --device cpu --max-prediction-images 4
```

## Test Split Results

| Model | Precision | Recall | F1-score | mAP@0.5 | mAP@0.5:0.95 | Mean inference (s/img) | FPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| YOLO11s | 0.7950 | 0.0585 | 0.1089 | 0.1301 | 0.0478 | 0.1103 | 9.0668 |
| Faster R-CNN ResNet-50 FPN | 0.2118 | 0.1617 | 0.1834 | 0.0895 | 0.0339 | 2.2035 | 0.4538 |
| SSD300 VGG16 | 0.0002 | 0.0027 | 0.0004 | 0.0000 | 0.0000 | 0.5345 | 1.8709 |

## Validation Split Results

| Model | Precision | Recall | F1-score | mAP@0.5 | mAP@0.5:0.95 | Mean inference (s/img) | FPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| YOLO11s | 0.8155 | 0.0665 | 0.1230 | 0.1951 | 0.0692 | 0.1132 | 8.8336 |
| Faster R-CNN ResNet-50 FPN | 0.2307 | 0.2681 | 0.2480 | 0.1465 | 0.0523 | 2.2190 | 0.4507 |
| SSD300 VGG16 | 0.0001 | 0.0014 | 0.0002 | 0.0000 | 0.0000 | 0.2939 | 3.4023 |

## Interpretation

The standardized test split results show that YOLO11s achieved the highest precision, mAP@0.5, mAP@0.5:0.95, and FPS among the pilot models. Faster R-CNN achieved higher recall and F1-score than YOLO11s on the test split, but it was substantially slower on CPU. SSD300 VGG16 remained unstable in this pilot setup, with near-zero detection quality and many false positives.

These values are still preliminary because the models were trained with very small pilot configurations. They are useful for validating the evaluation protocol, but they should not be treated as final TCC results.
