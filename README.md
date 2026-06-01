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
