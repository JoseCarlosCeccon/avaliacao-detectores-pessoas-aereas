from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tcc_detection.torchvision_pilot import add_common_args, run_pilot


def main() -> None:
    parser = add_common_args(argparse.ArgumentParser(description="Run an SSD300 VGG16 pilot on YOLO person labels."))
    parser.set_defaults(output_dir=Path("outputs") / "pilots" / "ssd")
    args = parser.parse_args()
    run_pilot("ssd", args)


if __name__ == "__main__":
    main()

