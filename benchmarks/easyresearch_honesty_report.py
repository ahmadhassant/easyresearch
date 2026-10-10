"""Tables, figures and summary numbers for easyresearch_honesty.py.

    python easyresearch_honesty_report.py [--tex-dir DIR]

Reads results/easyresearch_honesty/*_runs.csv and writes RESULTS.md, figures
(PNG and PDF) and summary.json there; with --tex-dir it also writes the LaTeX
macros (results.tex) and tables (tab_*.tex) used by the paper.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "easyresearch_honesty"
BLUE, ORANGE, GREEN = "#0072B2", "#E69F00", "#009E73"


def p_one_sided(a, b):
    """One-sided Wilcoxon signed-rank test that a > b."""
    d = np.asarray(a) - np.asarray(b)
    if np.allclose(d, 0):
        return 1.0
    return float(wilcoxon(d, alternative="greater").pvalue)


def fmt_p(p):
    return f"{p:.2g}" if p >= 0.001 else f"{p:.1e}".replace("e-0", "e-")


def tex_p(p):
    if p >= 0.001:
        return f"{p:.2g}"
    m, e = f"{p:.1e}".split("e")
    return f"{m}\\times10^{{{int(e)}}}"


# --------------------------------------------------------------------------- #

def regression():
    r = pd.read_csv(OUT / "regression_runs.csv")
    r["bias_naive"] = (r.naive - r.external_naive) * 100
    r["bias_comp"] = (r.comparison - r.external_tool) * 100
    r["bias_final"] = (r.final - r.external_tool) * 100
    real = r[r.dataset != "random_target"]
    ctrl = r[r.dataset == "random_target"]
    by = real.groupby("dataset", sort=False)
    s = dict(
        n_data=real.dataset.nunique(), runs=len(real),
        seeds=int(r.seed.nunique()),
        bias=real[["bias_naive", "bias_comp", "bias_final"]].mean().to_dict(),
        mae=real[["bias_naive", "bias_comp", "bias_final"]].abs().mean()
        .to_dict(),
        p=p_one_sided(real.bias_naive, real.bias_final),
        p_ds=p_one_sided(by.bias_naive.mean(), by.bias_final.mean()),
        ctrl=dict(comp=float(ctrl.comparison.mean() * 100),
                  final=float(ctrl.final.mean() * 100),
                  naive=float(ctrl.naive.mean() * 100),
                  truth=float(ctrl.external_tool.mean() * 100),
                  bias_comp=float(ctrl.bias_comp.mean()),
                  bias_final=float(ctrl.bias_final.mean())),
        methods=r.groupby("dataset", sort=False).method.first().to_dict())
    table = r.groupby(["dataset", "name"], sort=False)[
        ["n_dev", "naive", "comparison", "final", "external_tool",
         "bias_naive", "bias_comp", "bias_final"]].mean().reset_index()
    return r, s, table


def screening():
    d = pd.read_csv(OUT / "screening_runs.csv")
    return {k: float(d[k].mean()) for k in
            ("screen_outside", "screen_inside", "external")}


def forecasting():
    f = pd.read_csv(OUT / "forecasting_runs.csv")
    # ratio estimate / truth of MASE: below 1 = the estimate promised a
    # smaller error than was achieved (optimistic). Ratios are summarised on
    # the log scale, because relative errors are asymmetric.
    f["ratio_shuf"] = f.shuffled / f.truth_shuffled
    f["ratio_comp"] = f.comparison / f.truth_tool
    f["ratio_final"] = f.final / f.truth_tool
    f["opt_shuf"] = (1 - f.ratio_shuf) * 100
    f["opt_comp"] = (1 - f.ratio_comp) * 100
    f["opt_final"] = (1 - f.ratio_final) * 100
    rw = f[f.dataset.str.startswith("random_walk")]
    real = f[~f.dataset.str.startswith("random_walk")]
    ml = {"ridge", "random_forest", "gradient_boosting", "knn"}

    def geo(x):
        return float(np.exp(np.mean(np.log(x))))

    def typical(x):
        return float(np.exp(np.mean(np.abs(np.log(x)))))
    lt = np.log(real.truth_tool / real.truth_shuffled)
    s = dict(
        n_data=len(real),
        geo={k: geo(real[f"ratio_{k}"]) for k in ("shuf", "comp", "final")},
        median={k: float(real[f"ratio_{k}"].median())
                for k in ("shuf", "comp", "final")},
        typical={k: typical(real[f"ratio_{k}"])
                 for k in ("shuf", "comp", "final")},
        below_one={k: int((real[f"ratio_{k}"] < 1).sum())
                   for k in ("shuf", "comp", "final")},
        p=float(wilcoxon(np.log(real.ratio_shuf), np.log(real.ratio_final),
                         alternative="less").pvalue),
        tool_better=int((lt < -1e-9).sum()),
        same=int((np.abs(lt) <= 1e-9).sum()),
        tool_worse=int((lt > 1e-9).sum()),
        truth_gain=float((1 - np.exp(lt.mean())) * 100),
        beats_rule=int((real.truth_tool < real.truth_rule).sum()),
        beats_rule_shuf=int((real.truth_shuffled < real.truth_rule).sum()),
        rw_n=len(rw),
        rw_shuf_ml=int(rw.shuffled_winner.isin(ml).sum()),
        rw_shuf_worse=int((rw.truth_shuffled > rw.truth_rule).sum()),
        rw_shuf_gain=float((1 - geo(rw.ratio_shuf)) * 100),
        rw_tool_naive=int((rw.tool_winner == "naive").sum()),
        rw_truth_shuf=float(rw.truth_shuffled.mean()),
        rw_truth_rule=float(rw.truth_rule.mean()),
        rw_truth_tool=float(rw.truth_tool.mean()))
    return f, s


def signals():
    g = pd.read_csv(OUT / "signals_runs.csv")
    g["bias_comp"] = (g.comparison - g.external_tool) * 100
    g["bias_final"] = (g.final - g.external_tool) * 100
    real = g[g.dataset != "random_labels"]
    ctrl = g[g.dataset == "random_labels"]
    by = real.groupby("dataset", sort=False)
    s = dict(
        n_data=real.dataset.nunique(), runs=len(real),
        seeds=int(g.seed.nunique()),
        bias=real[["bias_comp", "bias_final"]].mean().to_dict(),
        mae=real[["bias_comp", "bias_final"]].abs().mean().to_dict(),
        p=p_one_sided(real.bias_comp, real.bias_final),
        p_ds=p_one_sided(by.bias_comp.mean(), by.bias_final.mean()),
        rocket_wins=int((real.tool_winner == "rocket").sum()),
        ctrl=dict(comp=float(ctrl.comparison.mean() * 100),
                  final=float(ctrl.final.mean() * 100),
                  truth=float(ctrl.external_tool.mean() * 100)))
    table = g.groupby(["dataset", "name"], sort=False)[
        ["n_dev", "comparison", "final", "external_tool", "bias_comp",
         "bias_final"]].mean().reset_index()
    return g, s, table


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #

STYLE = {"common": ("o", BLUE), "comparison": ("s", ORANGE),
         "final": ("D", GREEN)}


def _dotplot(ax, names, series, xlabel):
    """series: list of (style key, label, values)."""
    y = np.arange(len(names))[::-1]
    for i, (key, label, vals) in enumerate(series):
        marker, color = STYLE[key]
        off = (i - (len(series) - 1) / 2) * 0.22
        ax.scatter(vals, y + off, marker=marker, color=color, s=34,
                   label=label, zorder=3)
    ax.axvline(0, color="black", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color="#dddddd")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=1,
              frameon=False, fontsize=8)


def figures(reg_t, fc, sig_t):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9})
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.2), layout="constrained",
                             gridspec_kw={"width_ratios": [1, 1, 0.75]})
    _dotplot(axes[0], list(reg_t.name),
             [("common", "Common practice (preprocessing on all rows, "
               "best model's CV score)", reg_t.bias_naive),
              ("comparison", "Comparison best (EasyResearch)", reg_t.bias_comp),
              ("final", "EasyResearch final score", reg_t.bias_final)],
             "Estimate minus truth ($R^2$ points)")
    axes[0].set_title("Regression")
    _dotplot(axes[1], list(fc.name),
             [("common", "Common practice (shuffled CV over windows)",
               np.log2(1 / fc.ratio_shuf)),
              ("comparison", "Comparison best (rolling origins)",
               np.log2(1 / fc.ratio_comp)),
              ("final", "EasyResearch final-period score",
               np.log2(1 / fc.ratio_final))],
             "log$_2$(true MASE / estimated MASE)")
    axes[1].set_title("Forecasting")
    _dotplot(axes[2], list(sig_t.name),
             [("comparison", "Comparison best (EasyResearch)", sig_t.bias_comp),
              ("final", "EasyResearch final score", sig_t.bias_final)],
             "Estimate minus truth (pp)")
    axes[2].set_title("Signal classification")
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"honesty_easyresearch.{ext}", dpi=300,
                    bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# LaTeX
# --------------------------------------------------------------------------- #

def _f(x, d=1, sign=True):
    if round(x, d) == 0:
        x = 0.0
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    if s in ("+0." + "0" * d, "+0"):
        s = s[1:]
    return s.replace("-", "$-$") if s.startswith("-") else s


def _esc(text):
    return str(text).replace("&", "\\&").replace("#", "\\#").replace("%", "\\%")


def write_tex(d, s_reg, scr, s_fc, s_sig, reg_t, fc, sig_t):
    d.mkdir(parents=True, exist_ok=True)
    m = {
        "RegNData": s_reg["n_data"], "RegRuns": s_reg["runs"],
        "RegSeeds": s_reg["seeds"],
        "RegBiasNaive": _f(s_reg["bias"]["bias_naive"]),
        "RegBiasComp": _f(s_reg["bias"]["bias_comp"]),
        "RegBiasFinal": _f(s_reg["bias"]["bias_final"]),
        "RegMAENaive": _f(s_reg["mae"]["bias_naive"], sign=False),
        "RegMAEComp": _f(s_reg["mae"]["bias_comp"], sign=False),
        "RegMAEFinal": _f(s_reg["mae"]["bias_final"], sign=False),
        "RegP": tex_p(s_reg["p"]), "RegPds": tex_p(s_reg["p_ds"]),
        "RegCtrlComp": _f(s_reg["ctrl"]["bias_comp"]),
        "RegCtrlFinal": _f(s_reg["ctrl"]["bias_final"]),
        "RegCtrlCompVal": f"{s_reg['ctrl']['comp'] / 100:.3f}".replace("-", "$-$"),
        "RegCtrlFinalVal": f"{s_reg['ctrl']['final'] / 100:.3f}".replace("-", "$-$"),
        "RegCtrlTruthVal": f"{s_reg['ctrl']['truth'] / 100:.3f}".replace("-", "$-$"),
        "ScrOut": f"{scr['screen_outside']:.2f}".replace("-", "$-$"),
        "ScrIn": f"{scr['screen_inside']:.2f}".replace("-", "$-$"),
        "ScrExt": f"{scr['external']:.2f}".replace("-", "$-$"),
        "FcNData": s_fc["n_data"],
        "FcShufGeo": f"{(1 - s_fc['geo']['shuf']) * 100:.0f}",
        "FcShufMedian": f"{(1 - s_fc['median']['shuf']) * 100:.0f}",
        "FcCompGeo": f"{abs(1 - s_fc['geo']['comp']) * 100:.0f}",
        "FcFinalGeo": f"{abs(1 - s_fc['geo']['final']) * 100:.1f}",
        "FcShufTyp": f"{s_fc['typical']['shuf']:.2f}",
        "FcCompTyp": f"{s_fc['typical']['comp']:.2f}",
        "FcFinalTyp": f"{s_fc['typical']['final']:.2f}",
        "FcShufBelow": s_fc["below_one"]["shuf"],
        "FcFinalBelow": s_fc["below_one"]["final"],
        "FcP": tex_p(s_fc["p"]),
        "FcToolBetter": s_fc["tool_better"], "FcSame": s_fc["same"],
        "FcToolWorse": s_fc["tool_worse"],
        "FcTruthGain": f"{s_fc['truth_gain']:.0f}",
        "FcBeatsRule": s_fc["beats_rule"],
        "FcBeatsRuleShuf": s_fc["beats_rule_shuf"],
        "FcRWn": s_fc["rw_n"], "FcRWShufML": s_fc["rw_shuf_ml"],
        "FcRWShufWorse": s_fc["rw_shuf_worse"],
        "FcRWShufGain": f"{s_fc['rw_shuf_gain']:.0f}",
        "FcRWToolNaive": s_fc["rw_tool_naive"],
        "SigNData": s_sig["n_data"], "SigRuns": s_sig["runs"],
        "SigSeeds": s_sig["seeds"],
        "SigBiasComp": _f(s_sig["bias"]["bias_comp"], 2),
        "SigBiasFinal": _f(s_sig["bias"]["bias_final"], 2),
        "SigMAEComp": _f(s_sig["mae"]["bias_comp"], sign=False),
        "SigMAEFinal": _f(s_sig["mae"]["bias_final"], sign=False),
        "SigRocketWins": s_sig["rocket_wins"],
        "SigCtrlComp": f"{s_sig['ctrl']['comp']:.1f}",
        "SigCtrlFinal": f"{s_sig['ctrl']['final']:.1f}",
        "SigCtrlTruth": f"{s_sig['ctrl']['truth']:.1f}",
    }
    lines = ["% generated by benchmarks/easyresearch_honesty_report.py"]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    (d / "results.tex").write_text("\n".join(lines) + "\n")

    def num(x, scale=100, dd=1):
        v = x * scale
        return f"{v:.{dd}f}".replace("-", "$-$")

    rows = []
    for _, t in reg_t.iterrows():
        rows.append(f"{_esc(t['name'])} & {int(t.n_dev)} & {num(t.naive)} & "
                    f"{num(t.comparison)} & {num(t.final)} & "
                    f"{num(t.external_tool)} \\\\")
    ctrl_i = [i for i, t in enumerate(reg_t.itertuples()) if t.dataset == "random_target"]
    if ctrl_i:
        rows.insert(ctrl_i[0], "\\midrule")
    (d / "tab_regression.tex").write_text(
        "\\begin{table}[t]\n\\centering\\small\n"
        "\\caption{Regression: $R^2$ ($\\times 100$) estimated on the first "
        f"half and measured on the untouched second half (mean of "
        f"{s_reg['seeds']} random splits). The truth is that of "
        "\\ER's selected model; the common-practice estimate is compared with "
        "its own winner's truth when its bias is computed.}\n"
        "\\label{tab:regression}\n\\resizebox{\\linewidth}{!}{%\n"
        "\\begin{tabular}{@{}lrrrrr@{}}\n\\toprule\n"
        "Dataset & Rows & Common practice & Comparison best & \\ER{} final "
        "& Truth \\\\\n\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n")

    def mase(x):
        return f"{x:.3f}"
    names = {"naive": "naive", "seasonal_naive": "seas.\\ naive",
             "ets": "ETS", "theta": "Theta", "ridge": "Ridge",
             "random_forest": "RF", "gradient_boosting": "GB", "knn": "KNN"}
    rows = []
    for i, t in fc.iterrows():
        if t.dataset.startswith("random_walk") and (i == 0 or not fc.iloc[i - 1].dataset.startswith("random_walk")):
            rows.append("\\midrule")
        rows.append(
            f"{_esc(t['name'])} & {int(t.horizon)} & {mase(t.shuffled)} "
            f"({names[t.shuffled_winner]}) & {mase(t.truth_shuffled)} & "
            f"{mase(t.final)} ({names[t.tool_winner]}) & "
            f"{mase(t.truth_tool)} & {mase(t.truth_rule)} \\\\")
    (d / "tab_forecasting.tex").write_text(
        "\\begin{table}[t]\n\\centering\\footnotesize\n"
        "\\caption{Forecasting: MASE estimated on the development part (first "
        "70\\%) and achieved in the untouched future (last 30\\%) by the "
        "model each procedure selected; lower is better. $H$ is the "
        "horizon. The last column is the naive or seasonal naive rule in the "
        "future.}\n\\label{tab:forecasting}\n"
        "\\resizebox{\\linewidth}{!}{%\n"
        "\\begin{tabular}{@{}lrrrrrr@{}}\n\\toprule\n"
        " & & \\multicolumn{2}{c}{Shuffled CV} & \\multicolumn{2}{c}{\\ER} & "
        "Rule \\\\\n\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\n"
        "Series & $H$ & estimate (model) & truth & final (model) & truth & "
        "truth \\\\\n\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n")

    rows = []
    for _, t in sig_t.iterrows():
        if t.dataset == "random_labels":
            rows.append("\\midrule")
        rows.append(f"{_esc(t['name'])} & {int(t.n_dev)} & {num(t.comparison)} & "
                    f"{num(t.final)} & {num(t.external_tool)} \\\\")
    (d / "tab_signals.tex").write_text(
        "\\begin{table}[t]\n\\centering\\small\n"
        "\\caption{Signal classification: balanced accuracy (\\%) estimated "
        "on the first half and measured on the untouched second half (mean "
        f"of {s_sig['seeds']} random stratified splits), default model set.}}\n"
        "\\label{tab:signals}\n\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n"
        "Dataset & Recordings & Comparison best & \\ER{} final & Truth "
        "\\\\\n\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex-dir")
    args = ap.parse_args(argv)
    r, s_reg, reg_t = regression()
    scr = screening()
    fc, s_fc = forecasting()
    g, s_sig, sig_t = signals()
    figures(reg_t, fc, sig_t)
    summary = dict(regression=s_reg, screening=scr, forecasting=s_fc,
                   signals=s_sig)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2,
                                                 default=float))
    md = ["# EasyResearch honesty benchmark", "",
          "Produced by `easyresearch_honesty.py` and "
          "`easyresearch_honesty_report.py`.", "",
          "## Regression (R² × 100; bias = estimate − truth)", "",
          reg_t.round(2).to_markdown(index=False), "",
          f"Real data, {s_reg['runs']} runs: mean bias common practice "
          f"{s_reg['bias']['bias_naive']:.2f}, comparison best "
          f"{s_reg['bias']['bias_comp']:.2f}, final "
          f"{s_reg['bias']['bias_final']:.2f}; mean absolute "
          f"{s_reg['mae']['bias_naive']:.2f} / {s_reg['mae']['bias_comp']:.2f}"
          f" / {s_reg['mae']['bias_final']:.2f}. One-sided Wilcoxon (common "
          f"practice > final): p = {fmt_p(s_reg['p'])}; dataset means: "
          f"p = {fmt_p(s_reg['p_ds'])}.", "",
          "Screening on all rows (pure noise, 100 rows, 500 predictors): "
          f"CV R² {scr['screen_outside']:.3f}; screening inside the folds "
          f"{scr['screen_inside']:.3f}; new data {scr['external']:.3f}.", "",
          "## Forecasting (MASE; optimism = (truth − estimate) / truth, %)", "",
          fc.drop(columns=[c for c in fc.columns if c in ("seconds",)])
          .round(3).to_markdown(index=False), "",
          json.dumps(s_fc, indent=1, default=float), "",
          "## Signals (balanced accuracy × 100)", "",
          sig_t.round(2).to_markdown(index=False), "",
          json.dumps(s_sig, indent=1, default=float), ""]
    (OUT / "RESULTS.md").write_text("\n".join(md))
    if args.tex_dir:
        write_tex(Path(args.tex_dir), s_reg, scr, s_fc, s_sig, reg_t, fc,
                  sig_t)
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main()
