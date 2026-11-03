"""Generate a subject-disjoint split example from a local CSV manifest."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split


ADNI_SUBJECT_RE = re.compile(
    r"^(\d{3}_S_\d{4})(?=\d{4}-\d{2}-\d{2}|\d{8}|_|$)"
)
SYNTHETIC_SUBJECT_RE = re.compile(
    r"^([A-Za-z][A-Za-z0-9]*_[A-Za-z0-9]+)(?=_\d{4}-\d{2}-\d{2}|_|$)"
)
LABEL_NAMES = {0: "AD", 1: "CN", 2: "MCI"}


def load_manifest(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"row_index", "image_id", "label"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Manifest must contain columns {sorted(required)}")
    indices = np.asarray([int(row["row_index"]) for row in rows], dtype=np.int64)
    if not np.array_equal(indices, np.arange(len(rows), dtype=np.int64)):
        raise ValueError("row_index must be unique, zero-based, and contiguous")
    image_ids = np.asarray([row["image_id"] for row in rows], dtype=str)
    labels = np.asarray([int(row["label"]) for row in rows], dtype=np.int64)
    if np.any(~np.isin(labels, list(LABEL_NAMES))):
        raise ValueError("Labels must use raw MAT mapping 0=AD, 1=CN, 2=MCI")
    subjects = []
    for image_id in image_ids:
        match = ADNI_SUBJECT_RE.match(image_id)
        if match is None:
            match = SYNTHETIC_SUBJECT_RE.match(image_id)
        if not match:
            raise ValueError(f"Cannot parse subject ID from image_id={image_id!r}")
        subjects.append(match.group(1))
    return np.asarray(subjects), labels


def expand(subjects: np.ndarray, selected: np.ndarray) -> np.ndarray:
    selected_set = set(selected.tolist())
    return np.flatnonzero(np.isin(subjects, list(selected_set))).astype(np.int64)


def make_split(subjects: np.ndarray, labels: np.ndarray, seed: int,
               val_size: float, test_size: float) -> dict[str, np.ndarray]:
    unique = np.asarray(sorted(set(subjects.tolist())), dtype=str)
    subject_labels = np.asarray([
        np.bincount(labels[subjects == subject], minlength=3).argmax()
        for subject in unique
    ])
    development, test, development_y, _ = train_test_split(
        unique, subject_labels, test_size=test_size, stratify=subject_labels,
        random_state=seed,
    )
    relative_val = val_size / (1.0 - test_size)
    train, val = train_test_split(
        development, test_size=relative_val, stratify=development_y,
        random_state=seed,
    )
    return {
        "train_idx": expand(subjects, train),
        "val_idx": expand(subjects, val),
        "test_idx": expand(subjects, test),
        "train_subject_ids": np.sort(train),
        "val_subject_ids": np.sort(val),
        "test_subject_ids": np.sort(test),
    }


def overlap_report(subjects: np.ndarray, split: dict[str, np.ndarray]) -> dict[str, int]:
    groups = {
        name.removesuffix("_idx"): set(subjects[indices].tolist())
        for name, indices in split.items() if name.endswith("_idx")
    }
    return {
        "train_subjects": len(groups["train"]),
        "val_subjects": len(groups["val"]),
        "test_subjects": len(groups["test"]),
        "train_val_overlap": len(groups["train"] & groups["val"]),
        "train_test_overlap": len(groups["train"] & groups["test"]),
        "val_test_overlap": len(groups["val"] & groups["test"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-size", type=float, default=0.15)
    parser.add_argument("--test-size", type=float, default=0.15)
    args = parser.parse_args()
    if not 0 < args.val_size < 1 or not 0 < args.test_size < 1:
        raise ValueError("val-size and test-size must be between 0 and 1")
    if args.val_size + args.test_size >= 1:
        raise ValueError("val-size + test-size must be less than 1")

    subjects, labels = load_manifest(args.manifest)
    split = make_split(subjects, labels, args.seed, args.val_size, args.test_size)
    report = overlap_report(subjects, split)
    if any(report[key] for key in ("train_val_overlap", "train_test_overlap", "val_test_overlap")):
        raise RuntimeError(f"Subject overlap detected: {report}")
    if sum(len(split[f"{name}_idx"]) for name in ("train", "val", "test")) != len(subjects):
        raise RuntimeError("Split indices do not cover every manifest row")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, **split, seed=np.asarray(args.seed))
    result = {
        "manifest": str(args.manifest),
        "output": str(args.output),
        "n_rows": int(len(subjects)),
        "n_subjects": int(len(set(subjects.tolist()))),
        "seed": args.seed,
        "val_size": args.val_size,
        "test_size": args.test_size,
        "raw_label_mapping": LABEL_NAMES,
        "subject_disjoint": True,
        "split": {
            name: {
                "rows": int(len(split[f"{name}_idx"])),
                "subjects": int(len(split[f"{name}_subject_ids"])),
            }
            for name in ("train", "val", "test")
        },
        "overlap": report,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
