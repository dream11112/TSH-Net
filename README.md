# TSH-Net public reproducibility package v0.1.0

This is the **revision-stage** reproducibility package. It contains the
slice-selection convention, a self-contained preprocessing example, a
subject-level split-generation example, and a minimal experiment
configuration. It does not contain ADNI images, subject-level metadata,
subject-identifying feature files, per-slice predictions, or trained weights.

The package is designed for an approved ADNI user to run against a local,
controlled-access export.

## Revision and acceptance releases

### v0.1.0 - revision reproducibility package

The revision package contains:

```text
TSH-Net-public/
├── README.md
├── LICENSE.txt
├── requirements.txt
├── configs/
│   └── revision_example.yaml
├── examples/
│   ├── synthetic_manifest.csv
│   └── synthetic_output_expected.json
└── scripts/
    ├── make_synthetic_volume.py
    ├── preprocess_axial_slices.py
    └── rebuild_subject_split.py
```

### v1.0.0 - acceptance release

After formal acceptance, the remaining model, training, and evaluation code
and the weights used for the reported results are planned for release, subject
to ADNI and institutional restrictions. Every weight will be accompanied by
its task, fold number, configuration file, data-version identifier, validation
selection metric, and loading instructions.

## Data-use and privacy boundary

Raw ADNI data are controlled-access and are not redistributed here. The two
site/scanner manifests, MRI files, participant-level feature files, any index
file containing participant identifiers, and per-slice predictions remain in
the controlled local environment. Do not copy them into this package or a
public repository.

The split script accepts a local manifest supplied by an approved user. The
manifest is not included in the public package. It must preserve the original
row order used to build the feature file.

## Required local manifest

The authorized user's CSV must contain these columns:

```text
row_index,image_id,label
```

Requirements:

1. `row_index` is zero-based and unique.
2. Rows are in the same order as the local feature file.
3. `image_id` starts with a synthetic or locally authorized subject identifier,
   such as `SYNTH_0001`.
4. `label` uses the raw MAT convention: `0=AD`, `1=CN`, `2=MCI`.
5. Every row has one valid label and one parseable subject identifier.

The script does not read MRI images or publish the manifest. It only writes
the split indices and a summary in the user's chosen local output directory.

## Slice selection and preprocessing

For each MRI volume, the preprocessing protocol prespecifies **21 axial slice
positions**, indices **79 through 99 inclusive** (`output-slice079` ...
`output-slice099`). The actual input rows are included only after matching
those positions to the available records. No slice is selected using the
diagnosis, model prediction, confidence, or anatomical ranking.

Each matched slice is represented by a 225 x 225 image and decomposed into
25 overlapping 56 x 56 patches with stride 42. The public preprocessing
example implements slice extraction, percentile normalization, and
deterministic resizing for synthetic or user-authorized image arrays. It is a
**preprocessing example**, not a complete reproduction of the paper's
foreground extraction, morphological processing, or largest-connected-
component workflow. It is intentionally independent of any local absolute
path.

Create a synthetic volume and run the example:

```bash
python scripts/make_synthetic_volume.py \
  --output examples/synthetic_volume.npy

python scripts/preprocess_axial_slices.py \
  --input examples/synthetic_volume.npy \
  --output-dir examples/preprocessed \
  --slice-start 79 \
  --slice-end 99
```

For a real export, first create a local volume array from approved NIfTI data.
The example does not replace the controlled ADNI NIfTI conversion,
registration, or the paper's foreground extraction workflow.

## Subject-level split example

`rebuild_subject_split.py` is a **split-generation example**. It generates a
new stratified subject-level split from an approved local manifest; it does not
read or validate the formal split indices used for the reported experiment,
and it does not generate the internal five folds. The example always
generates a new split.

Run it against an approved local manifest:

```bash
python scripts/rebuild_subject_split.py \
  --manifest /controlled/path/authorized_manifest.csv \
  --output /controlled/path/subject_split_.npz \
  --summary /controlled/path/subject_split_.json \
  --seed 42 \
  --val-size 0.15 \
  --test-size 0.15
```

The script creates a stratified subject-level split and verifies that slices
from one subject are not divided across partitions. To reproduce the formal
reported indices, a separate local verification script must compare the
approved user's row-ordered manifest with the formally archived indices; this
public example does not claim to perform that verification.

For the reported data version, the expected partition sizes are:

| Partition | Subjects | Slice rows |
|---|---:|---:|
| Train | 557 | 33,096 |
| Validation | 120 | 6,909 |
| Test | 120 | 7,092 |
| Total | 797 | 47,097 |

These counts describe the reported data version. The script reports the
counts of whatever local manifest is supplied and should not be used to
silently assume that another ADNI export has the same composition.

The expected raw-label mapping is:

```text
0 -> AD
1 -> CN
2 -> MCI
```

Reporting order in tables and figures is `CN, MCI, AD`.

## Five-fold training protocol

The internal five folds are formed **only among the 557 development
subjects** in the fixed training/development partition, using:

```text
StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
```

The group is the subject identifier. The outer validation and test partitions
are not merged into these internal folds. Each fold-best model is selected on
that fold's validation subjects only, using the configured validation monitor
and early stopping. The independent 7,092-slice test partition is not used
for checkpoint selection, early stopping, hyperparameter selection, or model
ranking. Test evaluation is performed only after fold-best weights have been
fixed.

## Synthetic example

The included synthetic manifest has no real participant identifiers and is
provided only to test parsing and split validation:

```bash
python scripts/rebuild_subject_split.py \
  --manifest examples/synthetic_manifest.csv \
  --output /tmp/synthetic_subject_split.npz \
  --summary /tmp/synthetic_subject_split.json \
  --seed 42 \
  --val-size 0.20 \
  --test-size 0.20
```

The expected summary is recorded in
`examples/synthetic_output_expected.json`.

## Suggested Data/Code Availability statement

> We provide a revision-stage reproducibility package (TSH-Net v0.1.0)
> containing the slice-selection convention, preprocessing example, split
> generation example, configuration template, and synthetic test data. The
> split-generation example creates subject-disjoint partitions from the
> row-ordered manifest of an approved user's local ADNI export; it is not the
> formal split-index verification script. No participant-level manifest, MRI
> image, or prediction file is redistributed. The reported protocol
> prespecifies axial slice positions 79--99 inclusive and includes positions
> only after record matching. Internal five-fold training is restricted to the
> 557 development subjects. Complete model, training, evaluation,
> feature-extraction, hypergraph construction code, and the reported fold
> weights are planned for the post-acceptance v1.0.0 release, subject to ADNI
> and institutional restrictions. Fold-best weights are selected using
> validation data only and never using the independent test set.
