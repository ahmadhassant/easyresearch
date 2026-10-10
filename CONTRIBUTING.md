# Contributing to EasyResearch

Thank you for helping. EasyResearch is for researchers who do not
program, so the most valuable contributions are often **not code**:

* **Report a problem.** Open an issue on GitHub and describe what you did,
  what you expected, and what happened. Attach `log.txt` from the results
  folder – it lists every step. Please do **not** attach your data unless it
  is public.
* **Tell us what was confusing.** If a question in the wizard or a sentence
  in the report was unclear, that is a bug too.
* **Suggest an improvement** by opening an issue.

## Working on the code

```bash
git clone https://github.com/ahmadhassant/easyresearch.git
cd easyresearch
python -m pip install -e ".[test]"
python -m pytest tests
```

Guidelines (see also `docs/DEVELOPMENT.md`):

* Keep the user's side free of jargon; every new choice needs a
  plain-language explanation and a sensible default.
* Anything that learns from data must be fitted on training rows only,
  inside the model pipeline; forecasts are never evaluated on shuffled data
  (see `tests/test_evaluation_integrity.py`).
* Models use their default parameters with a fixed random seed; there is
  deliberately no hyperparameter tuning.
* Every method a report uses is cited (`src/easyresearch/common/references.py`).
* Add a test for every fix or feature, and describe user-visible changes in
  `CHANGELOG.md` (the desktop application has its own,
  `desktop/CHANGELOG.md`).

## Adding a model or a task

* Model: add it to the registry of its core (`regression/models.py`,
  `timeseries/models.py` or `timeseries/signal_models.py`) with its
  reference.
* Task for the desktop application: see "Add another analysis module" in
  `desktop/README.md`.

## Code of conduct

Be kind and constructive. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/),
version 2.1. Problems can be reported to ahmad.hassanat@gmail.com.
