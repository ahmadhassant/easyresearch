# EasyResearch honesty benchmark

Produced by `easyresearch_honesty.py` and `easyresearch_honesty_report.py`.

## Regression (R² × 100; bias = estimate − truth)

| dataset       | name                                |   n_dev |   naive |   comparison |   final |   external_tool |   bias_naive |   bias_comp |   bias_final |
|:--------------|:------------------------------------|--------:|--------:|-------------:|--------:|----------------:|-------------:|------------:|-------------:|
| diabetes      | Diabetes progression                |     221 |    0.49 |         0.49 |    0.46 |            0.47 |         2.85 |        2.62 |        -0.68 |
| prestige      | Occupational prestige (Canada)      |      51 |    0.82 |         0.81 |    0.77 |            0.74 |         7.54 |        7.89 |         3.23 |
| airquality    | New York air quality (ozone)        |      58 |    0.64 |         0.65 |    0.6  |            0.6  |         3.26 |        5.42 |         0.84 |
| friedman1     | Friedman #1 (synthetic, noise sd 1) |     250 |    0.81 |         0.81 |    0.81 |            0.82 |        -1.05 |       -1.27 |        -1.42 |
| salaries      | Professors' salaries (US)           |     196 |    0.43 |         0.44 |    0.41 |            0.4  |         1.59 |        3.87 |         1.28 |
| mpg           | Car highway mileage (mpg)           |     109 |    0.87 |         0.86 |    0.84 |            0.83 |         5.34 |        2.93 |         0.56 |
| ornstein      | Interlocking directorates (Canada)  |     124 |    0.53 |         0.55 |    0.47 |            0.56 |        -2.39 |       -1.5  |        -9.75 |
| cpus          | Computer performance (cpus)         |     104 |    0.87 |         0.88 |    0.81 |            0.83 |         3.18 |        4.18 |        -2.8  |
| slid          | Survey of labour and income (wages) |    2055 |    0.34 |         0.34 |    0.35 |            0.35 |        -0.7  |       -1.59 |        -0.12 |
| random_target | Random target (control)             |     150 |   -0.06 |        -0.04 |   -0.09 |           -0.16 |         6.18 |       11.44 |         6.82 |

Real data, 90 runs: mean bias common practice 2.18, comparison best 2.51, final -0.99; mean absolute 8.21 / 7.93 / 9.13. One-sided Wilcoxon (common practice > final): p = 1.3e-4; dataset means: p = 0.0098.

Screening on all rows (pure noise, 100 rows, 500 predictors): CV R² 0.273; screening inside the folds -0.331; new data -0.439.

## Forecasting (MASE; optimism = (truth − estimate) / truth, %)

| dataset        |   seed |   n |   n_dev |   horizon |   window |   season |   future_origins | shuffled_winner   |   shuffled |   truth_shuffled | tool_winner    |   comparison |   final |   truth_tool | rule           |   truth_rule | name                                   |   ratio_shuf |   ratio_comp |   ratio_final |   opt_shuf |   opt_comp |   opt_final |
|:---------------|-------:|----:|--------:|----------:|---------:|---------:|-----------------:|:------------------|-----------:|-----------------:|:---------------|-------------:|--------:|-------------:|:---------------|-------------:|:---------------------------------------|-------------:|-------------:|--------------:|-----------:|-----------:|------------:|
| co2            |      0 | 526 |     368 |        12 |       24 |       12 |               13 | knn               |      0.361 |            0.444 | ridge          |        0.382 |   0.447 |        0.371 | seasonal_naive |        1.204 | Mauna Loa CO2 (monthly)                |        0.812 |        1.028 |         1.204 |     18.787 |     -2.808 |     -20.355 |
| airpassengers  |      0 | 144 |     101 |        10 |       15 |       12 |                4 | ridge             |      0.396 |            0.527 | ridge          |        0.612 |   0.462 |        0.527 | seasonal_naive |        1.275 | Airline passengers (monthly)           |        0.751 |        1.159 |         0.877 |     24.904 |    -15.95  |      12.322 |
| nottem         |      0 | 240 |     168 |        12 |       24 |       12 |                6 | ridge             |      0.792 |            0.591 | ets            |        0.657 |   0.757 |        0.609 | seasonal_naive |        0.877 | Nottingham temperature (monthly)       |        1.34  |        1.08  |         1.244 |    -33.962 |     -7.998 |     -24.432 |
| ukgas          |      0 | 108 |      76 |         4 |       10 |        4 |                8 | ridge             |      0.927 |            1.622 | ridge          |        3.194 |   1.443 |        1.622 | seasonal_naive |        1.74  | UK gas consumption (quarterly)         |        0.572 |        1.97  |         0.89  |     42.844 |    -96.955 |      11.036 |
| sunspots       |      0 | 309 |     216 |         5 |       10 |        1 |               18 | random_forest     |      1.075 |            1.069 | random_forest  |        1.051 |   1.022 |        1.069 | naive          |        3.432 | Sunspot activity (yearly)              |        1.006 |        0.983 |         0.956 |     -0.572 |      1.683 |       4.353 |
| nile           |      0 | 100 |      70 |         5 |       10 |        1 |                6 | random_forest     |      1.008 |            0.993 | ridge          |        1.12  |   0.889 |        0.915 | naive          |        0.861 | Nile river flow (yearly)               |        1.014 |        1.224 |         0.973 |     -1.43  |    -22.418 |       2.741 |
| ukdriverdeaths |      0 | 192 |     134 |        12 |       20 |       12 |                4 | random_forest     |      1.1   |            0.603 | ets            |        0.84  |   0.458 |        0.904 | seasonal_naive |        1.216 | UK car drivers killed (monthly)        |        1.825 |        0.929 |         0.506 |    -82.463 |      7.148 |      49.393 |
| usaccdeaths    |      0 |  72 |      50 |         5 |        7 |       12 |                4 | random_forest     |      1.169 |            1.729 | seasonal_naive |        0.464 |   0.607 |        0.512 | seasonal_naive |        0.512 | US accidental deaths (monthly)         |        0.676 |        0.907 |         1.186 |     32.393 |      9.283 |     -18.575 |
| austres        |      0 |  89 |      62 |         4 |        9 |        4 |                6 | ridge             |      0.072 |            0.129 | ets            |        0.075 |   0.052 |        0.121 | seasonal_naive |        1.211 | Australian residents (quarterly)       |        0.557 |        0.622 |         0.434 |     44.284 |     37.78  |      56.628 |
| johnsonjohnson |      0 |  84 |      59 |         4 |        8 |        4 |                6 | ridge             |      0.587 |            1.237 | ets            |        1.312 |   0.994 |        1.314 | seasonal_naive |        2.627 | Johnson & Johnson earnings (quarterly) |        0.474 |        0.999 |         0.756 |     52.551 |      0.135 |      24.38  |
| lynx           |      0 | 114 |      80 |         8 |       12 |        1 |                4 | random_forest     |      0.891 |            1.623 | random_forest  |        1.09  |   0.879 |        1.623 | naive          |        2.759 | Canadian lynx trappings (yearly)       |        0.549 |        0.672 |         0.542 |     45.075 |     32.822 |      45.837 |
| lakehuron      |      0 |  98 |      69 |         6 |       10 |        1 |                4 | random_forest     |      1.451 |            2.593 | random_forest  |        1.734 |   2.086 |        2.593 | naive          |        2.243 | Lake Huron level (yearly)              |        0.56  |        0.669 |         0.805 |     44.025 |     33.139 |      19.528 |
| discoveries    |      0 | 100 |      70 |         7 |       10 |        1 |                4 | random_forest     |      0.999 |            0.678 | theta          |        0.841 |   0.708 |        0.659 | naive          |        0.912 | Great inventions (yearly)              |        1.474 |        1.275 |         1.074 |    -47.37  |    -27.547 |      -7.432 |
| bjsales        |      0 | 150 |     105 |        10 |       15 |        1 |                4 | knn               |      3.428 |            3.048 | ets            |        2.415 |   7.35  |        1.387 | naive          |        1.851 | Box-Jenkins sales (no dates)           |        1.125 |        1.742 |         5.301 |    -12.493 |    -74.171 |    -430.106 |
| wwwusage       |      0 | 100 |      70 |         7 |       10 |        1 |                4 | random_forest     |      2.969 |            5.149 | ets            |        2.413 |   5.057 |        3.381 | naive          |        4.819 | Internet users per minute (no dates)   |        0.577 |        0.714 |         1.496 |     42.332 |     28.618 |     -49.577 |
| random_walk_0  |      0 | 300 |     210 |        10 |       20 |        1 |                9 | knn               |      1.879 |            2.349 | naive          |        1.627 |   2.378 |        1.823 | naive          |        1.823 | Random walk (control), seed 0          |        0.8   |        0.893 |         1.304 |     19.999 |     10.723 |     -30.448 |
| random_walk_1  |      1 | 300 |     210 |        10 |       20 |        1 |                9 | knn               |      2.28  |            2.536 | naive          |        2.278 |   2.574 |        2.125 | naive          |        2.125 | Random walk (control), seed 1          |        0.899 |        1.072 |         1.211 |     10.101 |     -7.215 |     -21.131 |
| random_walk_2  |      2 | 300 |     210 |        10 |       20 |        1 |                9 | random_forest     |      1.983 |            2.572 | naive          |        2.911 |   2.654 |        2.527 | naive          |        2.527 | Random walk (control), seed 2          |        0.771 |        1.152 |         1.05  |     22.888 |    -15.193 |      -5.02  |
| random_walk_3  |      3 | 300 |     210 |        10 |       20 |        1 |                9 | random_forest     |      2.306 |            2.686 | naive          |        2.075 |   2.742 |        2.341 | naive          |        2.341 | Random walk (control), seed 3          |        0.859 |        0.886 |         1.171 |     14.127 |     11.372 |     -17.143 |
| random_walk_4  |      4 | 300 |     210 |        10 |       20 |        1 |                9 | random_forest     |      2.15  |            3.162 | ets            |        2.548 |   1.543 |        2.711 | naive          |        2.65  | Random walk (control), seed 4          |        0.68  |        0.94  |         0.569 |     32.004 |      6.041 |      43.076 |

{
 "n_data": 15,
 "geo": {
  "shuf": 0.8140218868898014,
  "comp": 1.0086350811380564,
  "final": 0.9847464165638552
 },
 "median": {
  "shuf": 0.7509598567922896,
  "comp": 0.9986495685502066,
  "final": 0.9564732165238873
 },
 "typical": {
  "shuf": 1.4843677630967032,
  "comp": 1.2825526117134576,
  "final": 1.458732768794296
 },
 "below_one": {
  "shuf": 9,
  "comp": 8,
  "final": 9
 },
 "p": 0.1038818359375,
 "tool_better": 7,
 "same": 5,
 "tool_worse": 3,
 "truth_gain": 14.14511776091093,
 "beats_rule": 12,
 "beats_rule_shuf": 10,
 "rw_n": 5,
 "rw_shuf_ml": 5,
 "rw_shuf_worse": 5,
 "rw_shuf_gain": 20.18895386245726,
 "rw_tool_naive": 4,
 "rw_truth_shuf": 2.6609095915823926,
 "rw_truth_rule": 2.2930135569853167,
 "rw_truth_tool": 2.305327620053928
}

## Signals (balanced accuracy × 100)

| dataset       | name                               |   n_dev |   comparison |   final |   external_tool |   bias_comp |   bias_final |
|:--------------|:-----------------------------------|--------:|-------------:|--------:|----------------:|------------:|-------------:|
| gunpoint      | GunPoint (motion)                  |     100 |         1    |    1    |            1    |        0.33 |         0.33 |
| italypower    | ItalyPowerDemand (electricity)     |     548 |         0.97 |    0.97 |            0.97 |        0.43 |         0.36 |
| arrowhead     | ArrowHead (shape outlines)         |     105 |         0.93 |    0.93 |            0.95 |       -1.7  |        -1.7  |
| osuleaf       | OSULeaf (leaf outlines, 6 classes) |     221 |         0.94 |    0.94 |            0.93 |        0.93 |         0.93 |
| random_labels | Random labels (control)            |     100 |         0.47 |    0.43 |            0.53 |       -6.03 |       -10.28 |

{
 "n_data": 4,
 "runs": 12,
 "seeds": 3,
 "bias": {
  "bias_comp": -0.001954683895025141,
  "bias_final": -0.017216794047647494
 },
 "mae": {
  "bias_comp": 1.8716836885272512,
  "bias_final": 1.8261185480716
 },
 "p": 0.5,
 "p_ds": 0.5,
 "rocket_wins": 12,
 "ctrl": {
  "comp": 46.91417378917379,
  "final": 42.664303289303284,
  "truth": 52.93996535262192
 }
}
