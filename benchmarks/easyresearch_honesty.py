"""Are the scores EasyResearch reports honest? (regression, forecasting, signals)

The same question as Benchmark 1 of the EasyClassifier paper, asked for the
three EasyResearch cores. Part of each dataset is never touched until the
end and gives the true performance of the model each estimate describes.

Regression and signal classification
    Each dataset is split in half (three random seeds). The first half is
    analysed; the second half is the truth. Estimates:
      naive      (regression only) preprocessing fitted on all development
                 rows before cross-validation, and the best model's
                 cross-validation score reported: common practice;
      comparison the best score in EasyResearch's leakage-free comparison
                 (selection bias only);
      final      EasyResearch's reported final score (nested CV here).

Forecasting
    The first 70% of each series is the development part, the last 30% is
    the untouched future. Estimates, all computed on the development part:
      shuffled   machine-learning models on windows of past values, scored by
                 shuffled 5-fold cross-validation over the windows, best
                 model's score reported: common practice for ML forecasting;
      comparison the best score at EasyResearch's rolling comparison origins;
      final      EasyResearch's final-period score.
    The truth is each selected model's error in the untouched future, with
    rolling origins one horizon apart, retrained before each origin.

Controls: a random target (regression), random labels (signals) and random
walks (forecasting), where nothing can be predicted.

    python easyresearch_honesty.py                 # everything
    python easyresearch_honesty.py --task forecasting
    python easyresearch_honesty.py --report        # tables and figures only

Results: results/easyresearch_honesty/. Finished pieces are cached in
results/easyresearch_honesty/cache/, so an interrupted run continues.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE / "results" / "easyresearch_honesty"
CACHE = OUT / "cache"
SEEDS = (0, 1, 2)                 # signals (ROCKET is slow)
REG_SEEDS = tuple(range(10))      # regression

import easyresearch_benchmarks as eb  # noqa: E402  (dataset loaders)


def cached(key, fn):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / (key + ".json")
    if p.exists():
        return json.loads(p.read_text())
    t = time.perf_counter()
    value = fn()
    value["seconds"] = time.perf_counter() - t
    p.write_text(json.dumps(value))
    return value


# --------------------------------------------------------------------------- #
# Datasets
# --------------------------------------------------------------------------- #

def _random_regression(seed):
    rng = np.random.default_rng(1000 + seed)
    df = pd.DataFrame(rng.normal(size=(300, 10)),
                      columns=[f"x{i}" for i in range(1, 11)])
    df["y"] = rng.normal(size=300)
    return df


def _drop(name, cols):
    return lambda: eb._r(name).drop(columns=cols)


REGRESSION = [(k, name, load, target) for k, name, load, target, _ in
              eb.REGRESSION if k != "mtcars"] + [
    ("salaries", "Professors' salaries (US)", lambda: eb._r("Salaries"),
     "salary"),
    # city mileage and the model name are left out (near-copies of the
    # target and an identifier)
    ("mpg", "Car highway mileage (mpg)", _drop("mpg", ["cty", "model"]),
     "hwy"),
    ("ornstein", "Interlocking directorates (Canada)",
     lambda: eb._r("Ornstein"), "interlocks"),
    # the published estimate of performance is left out (it leaks the target)
    ("cpus", "Computer performance (cpus)", _drop("cpus", ["name", "estperf"]),
     "perf"),
    # 7,425 rows: the development half is above 2,000 rows, so the final
    # score comes from an untouched 20% test set
    ("slid", "Survey of labour and income (wages)", lambda: eb._r("SLID"),
     "wages"),
]
REGRESSION_CONTROL = ("random_target", "Random target (control)")


def _random_signals(seed):
    rng = np.random.default_rng(2000 + seed)
    X = np.cumsum(rng.normal(size=(200, 100)), axis=1)
    df = pd.DataFrame(X, columns=[f"t{i}" for i in range(1, 101)])
    df.insert(0, "label", rng.choice(["a", "b"], size=200))
    return df


SIGNALS = [(k, name, load, target) for k, name, load, target, _ in eb.SIGNALS]
SIGNAL_CONTROL = ("random_labels", "Random labels (control)")


def _random_walk(seed):
    rng = np.random.default_rng(3000 + seed)
    y = 100 + np.cumsum(rng.normal(size=300))
    return pd.DataFrame({"t": np.arange(1, 301), "value": y})


def _ts(name, column, freq=None, start=None):
    def load():
        s = eb._r(name)
        v = s[name].to_numpy(dtype=float)
        if freq is None:
            return pd.DataFrame({column: v})
        idx = pd.period_range(start, periods=len(v), freq=freq)
        idx = idx.to_timestamp() if freq == "Q" else idx
        return pd.DataFrame({"time": idx.strftime("%Y-%m-%d") if freq != "Y"
                             else idx.year, column: v})
    return load


FORECASTING = [(k, name, load, value) for k, name, load, value, _ in
               eb.FORECASTING] + [
    ("ukdriverdeaths", "UK car drivers killed (monthly)",
     _ts("UKDriverDeaths", "deaths", "M", "1969-01"), "deaths"),
    ("usaccdeaths", "US accidental deaths (monthly)",
     _ts("USAccDeaths", "deaths", "M", "1973-01"), "deaths"),
    ("austres", "Australian residents (quarterly)",
     _ts("austres", "residents", "Q", "1971Q2"), "residents"),
    ("johnsonjohnson", "Johnson & Johnson earnings (quarterly)",
     _ts("JohnsonJohnson", "earnings", "Q", "1960Q1"), "earnings"),
    ("lynx", "Canadian lynx trappings (yearly)",
     _ts("lynx", "trappings", "Y", "1821"), "trappings"),
    ("lakehuron", "Lake Huron level (yearly)",
     _ts("LakeHuron", "level", "Y", "1875"), "level"),
    ("discoveries", "Great inventions (yearly)",
     _ts("discoveries", "count", "Y", "1860"), "count"),
    ("bjsales", "Box-Jenkins sales (no dates)", _ts("BJsales", "sales"),
     "sales"),
    ("wwwusage", "Internet users per minute (no dates)",
     _ts("WWWusage", "users"), "users"),
]
FORECAST_CONTROL = ("random_walk", "Random walk (control)")


# --------------------------------------------------------------------------- #
# Regression
# --------------------------------------------------------------------------- #

def regression_run(key, df, target, seed):
    from easyclassifier import preprocessing as pp
    from easyclassifier.logbook import LogBook
    from sklearn.metrics import r2_score
    from sklearn.model_selection import KFold, train_test_split
    from easyresearch.regression import analysis as ra
    from easyresearch.regression import evaluation as ev
    from easyresearch.regression.models import build_registry

    prep = ra.prepare(df, target, LogBook())
    X, y = prep.X, prep.y
    idx = np.arange(len(y))
    dev, ext = train_test_split(idx, test_size=0.5, random_state=seed)
    Xd, yd = X.iloc[dev].reset_index(drop=True), y[dev]
    Xe, ye = X.iloc[ext].reset_index(drop=True), y[ext]
    reg = {k: s for k, s in build_registry().items() if s.available}
    specs = {k: ra._pipeline_spec(s, Xd, prep.cfg) for k, s in reg.items()}

    # naive: preprocessing fitted on all development rows, then CV, best-of
    pre = pp.build_preprocessor(Xd, prep.cfg, scale="standard").fit(Xd)
    Zd, Ze = pre.transform(Xd), pre.transform(Xe)
    naive = {}
    for k, s in reg.items():
        pred = np.empty(len(yd))
        for tr, te in KFold(5, shuffle=True, random_state=seed).split(Zd):
            pred[te] = s.factory().fit(Zd[tr], yd[tr]).predict(Zd[te])
        naive[k] = float(r2_score(yd, pred))
    nw = max(naive, key=naive.get)
    ext_naive = float(r2_score(ye, reg[nw].factory().fit(Zd, yd).predict(Ze)))

    comp = {k: ev.evaluate(s, Xd, yd, "kfold5").selection_score
            for k, s in specs.items()}
    tw = max(comp, key=comp.get)
    method = ev.recommend_selection(len(yd))
    if method == "nested":
        final = ev.nested_cv(list(specs.values()), Xd, yd, "kfold5").metrics["r2"]
    else:
        d2, t2 = ev.split_final_test(len(yd))
        comp = {k: ev.evaluate(s, Xd.iloc[d2], yd[d2], "kfold5").selection_score
                for k, s in specs.items()}
        tw = max(comp, key=comp.get)
        final = ev.evaluate_on_test(specs[tw], Xd, yd, d2, t2).metrics["r2"]
    ext_tool = float(r2_score(ye, specs[tw].factory().fit(Xd, yd).predict(Xe)))
    return dict(dataset=key, seed=seed, n_dev=len(yd), n_ext=len(ye),
                method=method, naive_winner=nw, naive=naive[nw],
                external_naive=ext_naive, tool_winner=tw,
                comparison=comp[tw], final=final, external_tool=ext_tool)


def screening_run(seed, n=100, p=500, k=10):
    """The 'wrong way' to cross-validate (screening on all rows) on pure
    noise, compared with screening inside each fold."""
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    from sklearn.model_selection import KFold
    from sklearn.pipeline import make_pipeline
    rng = np.random.default_rng(4000 + seed)
    X, y = rng.normal(size=(n, p)), rng.normal(size=n)
    Xe, ye = rng.normal(size=(n, p)), rng.normal(size=n)
    cols = SelectKBest(f_regression, k=k).fit(X, y).get_support()
    pred_out, pred_in = np.empty(n), np.empty(n)
    for tr, te in KFold(5, shuffle=True, random_state=seed).split(X):
        pred_out[te] = LinearRegression().fit(X[tr][:, cols], y[tr]) \
            .predict(X[te][:, cols])
        m = make_pipeline(SelectKBest(f_regression, k=k), LinearRegression())
        pred_in[te] = m.fit(X[tr], y[tr]).predict(X[te])
    ext = r2_score(ye, LinearRegression().fit(X[:, cols], y)
                   .predict(Xe[:, cols]))
    return dict(seed=seed, screen_outside=float(r2_score(y, pred_out)),
                screen_inside=float(r2_score(y, pred_in)),
                external=float(ext))


# --------------------------------------------------------------------------- #
# Signals
# --------------------------------------------------------------------------- #

def signal_run(key, df, label, seed):
    from easyclassifier import preprocessing as pp
    from easyclassifier import recommend as rec
    from easyclassifier.evaluation import evaluate, nested_cv, recommend_selection
    from sklearn.metrics import balanced_accuracy_score
    from sklearn.model_selection import train_test_split
    from easyresearch.timeseries import signal_data as sd
    from easyresearch.timeseries.signal_models import build_registry

    recs = sd.prepare(df, label)
    X = recs.X
    y, names, _ = pp.encode_target(recs.labels)
    dev, ext = train_test_split(np.arange(len(y)), test_size=0.5,
                                random_state=seed, stratify=y)
    Xd, yd = X.iloc[dev].reset_index(drop=True), y[dev]
    Xe, ye = X.iloc[ext].reset_index(drop=True), y[ext]
    reg = build_registry()
    keys = [k for k, s in reg.items() if s.default_selected]
    validation = rec.validation_method(yd)
    comp = {k: evaluate(reg[k], Xd, yd, names, validation, []).selection_score
            for k in keys}
    tw = max(comp, key=comp.get)
    method = recommend_selection(yd)
    final = nested_cv([reg[k] for k in keys], Xd, yd, names, validation,
                      []).selection_score
    ext_tool = float(balanced_accuracy_score(
        ye, reg[tw].factory().fit(Xd, yd).predict(Xe)))
    return dict(dataset=key, seed=seed, n_dev=len(yd), n_ext=len(ye),
                method=method, tool_winner=tw, comparison=comp[tw],
                final=final, external_tool=ext_tool, comparison_all=comp)


# --------------------------------------------------------------------------- #
# Forecasting
# --------------------------------------------------------------------------- #

ML_KEYS = ["ridge", "random_forest", "gradient_boosting", "knn"]


def _shuffled_cv(spec_key, y, L, H, m, seed):
    """Shuffled 5-fold CV over windows of the development series (the
    common, leaky practice), scored by MASE with the in-sample scale."""
    from sklearn.model_selection import KFold
    from easyresearch.timeseries import evaluation as tev
    from easyresearch.timeseries import models as tm
    reg = tm.build_registry()
    X, Y = tm.make_windows(y, L, H)
    scale = float(np.std(np.diff(y))) or 1.0
    last = X[:, -1:]
    Xr, Yr = (X - last) / scale, (Y - last) / scale
    proto = reg[spec_key].make(L, H, m)
    errs = []
    for tr, te in KFold(5, shuffle=True, random_state=seed).split(Xr):
        model = proto.regressor().fit(Xr[tr], Yr[tr])
        f = last[te] + np.asarray(model.predict(Xr[te])).reshape(len(te), H) * scale
        errs.append(np.abs(Y[te] - f))
    return float(np.mean(np.concatenate(errs)) / tev.mase_scale(y, m))


def forecast_run(key, df, value, seed=0):
    from easyresearch.timeseries import data as td
    from easyresearch.timeseries import evaluation as tev
    from easyresearch.timeseries import forecast as tf
    from easyresearch.timeseries import models as tm

    series = td.prepare_series(df, value, None)
    y, m = series.values, series.season
    n = len(y)
    n_dev = int(round(0.7 * n))
    dev = td.Series(**{**series.__dict__, "values": y[:n_dev],
                       "index": series.index[:n_dev], "notes": []})
    H = tf.choose_horizon(dev)
    L = tm.window_length(int(0.6 * n_dev), m, H)
    plan = tev.plan_split(n_dev, H, L, m)
    reg = tm.build_registry()
    yd = y[:n_dev]
    future = [o for o in range(n_dev, n - H + 1, H)]

    def truth(k):
        s = reg[k]
        return tev.rolling(s, lambda: s.make(L, H, m), y, future, H, m) \
            .metrics["mase"]

    shuffled = {k: _shuffled_cv(k, yd, L, H, m, seed) for k in ML_KEYS}
    sw = min(shuffled, key=shuffled.get)

    cand = [k for k in tm.REFERENCE_KEYS if not tm.spec_unusable(reg[k], m)] \
        + [k for k, s in reg.items() if s.default_selected]
    comp = {}
    for k in cand:
        s = reg[k]
        try:
            comp[k] = tev.rolling(s, lambda s=s: s.make(L, H, m), yd,
                                  plan.dev_origins, H, m).metrics["mase"]
        except Exception:  # noqa: BLE001
            pass
    tw = min(comp, key=comp.get)
    s = reg[tw]
    final = tev.rolling(s, lambda: s.make(L, H, m), yd, plan.test_origins,
                        H, m).metrics["mase"]
    naive_key = "seasonal_naive" if "seasonal_naive" in comp else "naive"
    return dict(dataset=key, seed=seed, n=n, n_dev=n_dev, horizon=H,
                window=L, season=m, future_origins=len(future),
                shuffled_winner=sw, shuffled=shuffled[sw],
                truth_shuffled=truth(sw), tool_winner=tw,
                comparison=comp[tw], final=final, truth_tool=truth(tw),
                rule=naive_key, truth_rule=truth(naive_key),
                comparison_all=comp, shuffled_all=shuffled)


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def run_task(task):
    rows = []
    if task == "regression":
        for k, name, load, target in REGRESSION:
            df = load()
            for seed in REG_SEEDS:
                r = cached(f"reg__{k}__{seed}",
                           lambda: regression_run(k, df, target, seed))
                rows.append({**r, "name": name})
                print(f"regression {k} seed {seed}: done", flush=True)
        k, name = REGRESSION_CONTROL
        for seed in REG_SEEDS:
            r = cached(f"reg__{k}__{seed}", lambda: regression_run(
                k, _random_regression(seed), "y", seed))
            rows.append({**r, "name": name})
        scr = [cached(f"screen__{seed}", lambda: screening_run(seed))
               for seed in REG_SEEDS]
        pd.DataFrame(scr).to_csv(OUT / "screening_runs.csv", index=False)
    elif task == "signals":
        for k, name, load, target in SIGNALS:
            df = load()
            for seed in SEEDS:
                r = cached(f"sig__{k}__{seed}",
                           lambda: signal_run(k, df, target, seed))
                rows.append({**r, "name": name})
                print(f"signals {k} seed {seed}: done", flush=True)
        k, name = SIGNAL_CONTROL
        for seed in SEEDS:
            r = cached(f"sig__{k}__{seed}", lambda: signal_run(
                k, _random_signals(seed), "label", seed))
            rows.append({**r, "name": name})
    else:
        for k, name, load, value in FORECASTING:
            r = cached(f"fc__{k}", lambda: forecast_run(k, load(), value))
            rows.append({**r, "name": name})
            print(f"forecasting {k}: done", flush=True)
        k, name = FORECAST_CONTROL
        for seed in REG_SEEDS[:5]:
            r = cached(f"fc__{k}__{seed}", lambda: forecast_run(
                f"{k}_{seed}", _random_walk(seed), "value", seed))
            rows.append({**r, "name": f"{name}, seed {seed}"})
    df = pd.DataFrame([{k: v for k, v in r.items()
                        if not isinstance(v, dict)} for r in rows])
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / f"{task}_runs.csv", index=False)
    return df


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["regression", "signals", "forecasting"])
    args = ap.parse_args(argv)
    warnings.filterwarnings("ignore")
    for task in ([args.task] if args.task else
                 ["regression", "forecasting", "signals"]):
        run_task(task)


if __name__ == "__main__":
    main()
