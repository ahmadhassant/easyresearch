# EasyResearch changelog

## Unreleased

* Signal classification: one model with a single 80/20 validation split no longer crashes while saving `predictions.csv` (the file now lists the 20% validation recordings, with their rows in the data file).
* Forecasting: a date column in which some dates appear more than once is no longer refused as "not evenly spaced"; the spacing is read from the distinct dates, and repeated time points are averaged as before (with a note).
* ROCKET works on recordings of 10 values, the shortest accepted: a kernel longer than the recording is padded so it fits.

## 0.1.1 – 2026-10-14

Fixes for the Windows setup program of EasyResearch Desktop 0.1.1; the analyses and their results are unchanged.

* `versions.txt` also records the `xgboost-cpu` package, the XGBoost build bundled with the desktop application.
* The software citation (in every report, `citations.txt` and `CITATION.cff`) uses the Zenodo DOI for all versions, 10.5281/zenodo.23305077, and the README shows its badge.

## 0.1.0 – 2026-10-11

First version: the regression, forecasting and signal classification cores used by EasyResearch Desktop 0.1.0 and the `easyresearch` command line.

* Regression: nine models with the Hassanat KNN, R², RMSE, MAE, median absolute error, MAPE and MHSP, honest final score (nested cross-validation up to 2,000 rows, otherwise an untouched 20% test set).
* Forecasting: reference rules, statistical, machine-learning and deep models; rolling-origin comparison and a final period that plays no part in choosing the model; MASE, MAE, RMSE, sMAPE and MHSP; an automatic horizon that always fits the series.
* Signal classification: KNN with the Hassanat distance, ROCKET, features with Random Forest and four deep networks; EasyClassifier's evaluation.
* Every run writes a report, comparison table, predictions or forecasts, figures, the trained model, `settings.json`, `versions.txt`, citations and a log. A model that cannot be saved no longer stops the analysis.
* Deep models are optional (not in the default set); the forecasting evaluation accepts shorter series (comparison forecasts may overlap, with a note).
* The Hassanat distance is cited with the IEEE ETCEA 2022 paper and the arXiv preprint.
* Figure choices in all three cores: `figure_theme` (colorblind, greyscale, high_contrast), `figure_format` (png, png+pdf, png+svg) and `figure_keys` (which figures; `None` keeps the usual set). Unknown choices are refused before any training.
* Every method used is cited in each report and in `citations.txt`: every regression, forecasting and signal model (including XGBoost and LightGBM), the multi-step forecasting strategy, rolling-origin evaluation, nested cross-validation or the final test, the measures (MASE, sMAPE, MHSP, balanced accuracy, MCC, ROC AUC), STL and the software (scikit-learn, statsmodels, PyTorch, NumPy, pandas, Matplotlib). The reference list is generated from the citations in the report (`common/references.py`).
* Regression cites the sign-symmetric reformulation of the Hassanat distance when its signed form is applied. Forecasting reports describe only the settings of the statistical models actually used (before, exponential-smoothing settings were described even when only Theta was selected).
* Command line: `--figures`, `--figure-theme` and `--figure-format` for every task; `pip install -e ".[full]"` adds XGBoost and LightGBM to regression.
* Own repository (split from the EasyClassifier repository, together with EasyResearch Desktop, now numbered 0.1.0 like the package); requires EasyClassifier 0.8.2 or later (0.8.x).
* EasyResearch Desktop is distributed as a Windows setup program (`EasyResearchDesktop-0.1.0-setup.exe`, attached to the GitHub release), built and tested by the `desktop release` workflow.
* Honesty benchmark (`benchmarks/easyresearch_honesty.py`): reported scores compared with data never touched, for regression, forecasting and signals, with random-target controls.
* Tests for leakage-free preparation, final-test isolation (scores unchanged when held-out rows are replaced by noise), time order, reproducibility and model saving.
