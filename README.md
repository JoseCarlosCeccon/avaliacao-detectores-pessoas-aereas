# TCC - VisDrone Person Detection

This folder contains the code and data preparation utilities for the TCC experiments.

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

## Commands

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

## Next experiment

Create a small pilot subset before training all final models:

```powershell
python .\scripts\make_yolo_subset.py --source-root .\datasets\visdrone_person_yolo --output-root .\datasets\visdrone_person_yolo_pilot --train 300 --val 100 --test 100
```

Start with a small pilot training run:

```powershell
yolo detect train model=yolo11s.pt data=.\datasets\visdrone_person_yolo_pilot\visdrone_person_pilot.yaml epochs=3 imgsz=640 batch=4 device=cpu
```

If a CUDA GPU is available, replace `device=cpu` with the GPU device, for example `device=0`.

## TorchVision pilots

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
├── losses.csv
├── metrics.csv
├── summary.json
├── predictions/
└── *_pilot_last.pt
```

These pilots are intended to validate the experimental pipeline. They are not final TCC results.
