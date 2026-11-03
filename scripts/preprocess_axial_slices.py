"""Minimal path-independent axial-slice preprocessing example.

Input is a NumPy volume with shape (height, width, axial_slices). The script
is intended for synthetic data or an approved local export; it does not read
ADNI files or write participant metadata.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def normalize_slice(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image, dtype=np.float32)
    positive = image[image > 0]
    if positive.size == 0:
        return np.zeros(image.shape, dtype=np.uint8)
    low, high = np.percentile(positive, [1, 99])
    if high <= low:
        return np.zeros(image.shape, dtype=np.uint8)
    scaled = np.clip((image - low) / (high - low), 0.0, 1.0)
    return np.rint(scaled * 255.0).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--slice-start", type=int, default=79)
    parser.add_argument("--slice-end", type=int, default=99)
    parser.add_argument("--image-size", type=int, default=225)
    args = parser.parse_args()
    if args.slice_start < 0 or args.slice_end < args.slice_start:
        raise ValueError("Invalid inclusive slice range")

    volume = np.load(args.input)
    if volume.ndim != 3:
        raise ValueError("Input volume must have shape (height, width, axial_slices)")
    if args.slice_end >= volume.shape[2]:
        raise ValueError(
            f"slice-end={args.slice_end} exceeds volume depth {volume.shape[2]}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index in range(args.slice_start, args.slice_end + 1):
        image = Image.fromarray(normalize_slice(volume[:, :, index]), mode="L")
        image = image.resize((args.image_size, args.image_size), Image.Resampling.BILINEAR)
        image.save(args.output_dir / f"output-slice{index:03d}.png")
    print(
        f"saved {args.slice_end - args.slice_start + 1} slices "
        f"({args.slice_start}-{args.slice_end}, inclusive) to {args.output_dir}"
    )


if __name__ == "__main__":
    main()
