# EasyVision paper – plan

Draft skeleton: `main.tex` (red text = to be filled once the code runs).
Design source: `docs/EASYVISION_DESIGN.md`.

## Claim the paper will test

Common evaluation shortcuts in image classification inflate the reported
result, and an honest default removes the inflation. Measured, not argued:
the same models and data under five evaluation regimes (R1 honest, R2
augmentation before splitting, R3 image-level split, R4 near-duplicates
left in, R5 flipped/rotated copies added as new images), each also with
random labels, against an untouched subject-wise external set.

## What must exist before the experiments

1. EasyVision phase 1 (image classification): data layout with a subject
   column, the copy check, subject-wise nested CV / final test, the five
   models of the design, report with "What was checked".
2. A switch for each shortcut (R2–R5), used only by the benchmark script,
   never offered in the interface.
3. A synthetic copy set (exact, flipped/rotated, resized/recoloured, crops)
   to measure the copy check's recall and false alarms (Table 4).

## Datasets to decide (open decision in the design)

Public, with subject identifiers, from several fields. Check licence,
size and identifiers for each candidate:

* dermoscopy with lesion identifiers (several images per lesion);
* histopathology with patient identifiers in file names (patches per patient);
* chest radiographs with patient identifiers;
* a plant or animal set with individual identifiers;
* one non-medical set with known near-duplicates.

Aim for 4–6 datasets, a few thousand images each, so that the linear probe
runs on a laptop CPU and fine-tuning on one GPU.

## Experiments and statistics

* 3–5 seeds per dataset and regime; balanced accuracy per image and per
  subject; inflation = reported − truth.
* Paired Wilcoxon tests between regimes over dataset × seed, with a
  dataset-level sensitivity analysis (as in the EasyResearch paper).
* Random-label control for every regime.

## Figures

1. Inflation per regime and dataset (dot plot, as in the earlier papers).
2. Examples of copies the check found (side by side).
3. One shortcut case with occlusion maps.

## Order of work

1. Implement phase 1 and the benchmark switches.
2. Copy-check validation on synthetic copies.
3. Pick the datasets (licences), run the five regimes.
4. Fill the red parts of `main.tex`; related work on augmentation-before-
   split and patch-level leakage; check the claim that no existing tool
   enforces all of the rules by default.

## Notes for the text

* Barz & Denzler (2020): the abstract reports duplicates for 3.3% (CIFAR-10)
  and 10% (CIFAR-100) of test images and an accuracy drop of 9–14%
  *relative to the original performance*. The design draft's "error rates
  rising by up to 2.7 points" is not in the abstract; check the paper's
  tables before using a number.
* Yagis et al. (2021): slice-level splitting inflated slice-level accuracy
  by 29–55% across four datasets; about 96% accuracy on random labels with
  the leaky split against about 50% with the subject-level split.
