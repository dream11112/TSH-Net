"""Create a small synthetic volume for the preprocessing example."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--height", type=int, default=64)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--depth", type=int, default=100)
    args = parser.parse_args()
    if min(args.height, args.width, args.depth) <= 0:
        raise ValueError("Volume dimensions must be positive")
    rng = np.random.default_rng(42)
    volume = rng.normal(100.0, 20.0, (args.height, args.width, args.depth)).astype(
        np.float32
    )
    volume[:8, :, :] = 0.0
    volume[-8:, :, :] = 0.0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.output, volume)
    print(f"saved synthetic volume with shape {volume.shape} to {args.output}")


if __name__ == "__main__":
    main()
