# Results summary (auto-generated)

## Data
Rows after cleaning: 4663 | 2007-09-17 -> 2026-09-18

Duplicates: 0, missing OHLC rows: 1, flat bars dropped: 0, OC-outside-range repaired: 0, suspicious daily moves: 6, calendar gaps: 1
Open==prev Close share: 0.0047
Full detail: results/data_validation.json

## Development (2007-09-17 -> 2018-12-31) - main config: fixed 2.0%, H=5, entry=next_open

| metric | value |
|---|---|
| n_events | 95.0 |
| event_mean_% | 0.02173562711822335 |
| baseline_mean_% | 0.1106379527729911 |
| excess_mean_% | -0.08890232565476774 |
| event_mean_CI_lo_% | -0.9149914862339401 |
| event_mean_CI_hi_% | 0.919766875815356 |
| excess_CI_lo_% | -1.0256294390069314 |
| excess_CI_hi_% | 0.8091289230423648 |
| t_vs_zero_p | 0.9638391796264114 |
| welch_p | 0.8539755633436444 |
| mannwhitney_p | 0.7134796014008196 |
| rd_p_greater | 0.617038296170383 |
| rd_p_two_sided | 0.7639236076392361 |
| event_win_% | 48.421052631578945 |
| baseline_win_% | 54.87336914811972 |
| winrate_binom_p | 0.2170037219517866 |
| n_raw_events | 149.0 |
| net_mean_% | -0.07826437288177673 |
| net_win_% | 48.421052631578945 |


Forward-return distribution (gross):

| index | n | mean_% | median_% | std_% | win_rate_% | p5_% | p95_% | worst_% | best_% | skew |
|---|---|---|---|---|---|---|---|---|---|---|
| events | 95.000 | 0.022 | -0.214 | 4.660 | 48.421 | -6.609 | 8.299 | -19.220 | 12.116 | -0.412 |
| baseline | 2606.000 | 0.111 | 0.258 | 2.999 | 54.873 | -4.684 | 4.395 | -19.236 | 21.620 | -0.019 |


## Robustness grid (development only; 26 tests -> Holm-adjusted p shown)

| threshold_% | H | entry | n | event_mean_% | baseline_% | excess_% | net_mean_% | p_random_day | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| 1.5 | 1 | next_open | 255 | -0.101 | -0.038 | -0.062 | -0.201 | 0.785 | 1.000 |
| 1.5 | 1 | close | 255 | -0.078 | 0.054 | -0.132 | -0.178 | 0.947 | 1.000 |
| 1.5 | 3 | next_open | 184 | 0.100 | 0.031 | 0.069 | -0.000 | 0.347 | 1.000 |
| 1.5 | 3 | close | 184 | 0.132 | 0.124 | 0.008 | 0.032 | 0.481 | 1.000 |
| 1.5 | 5 | next_open | 153 | 0.285 | 0.095 | 0.190 | 0.185 | 0.218 | 1.000 |
| 1.5 | 5 | close | 153 | 0.255 | 0.187 | 0.068 | 0.155 | 0.393 | 1.000 |
| 1.5 | 10 | next_open | 108 | 0.119 | 0.300 | -0.181 | 0.019 | 0.679 | 1.000 |
| 1.5 | 10 | close | 108 | 0.088 | 0.393 | -0.305 | -0.012 | 0.776 | 1.000 |
| 2.0 | 1 | next_open | 149 | -0.170 | -0.037 | -0.133 | -0.270 | 0.907 | 1.000 |
| 2.0 | 1 | close | 149 | -0.097 | 0.050 | -0.147 | -0.197 | 0.917 | 1.000 |
| 2.0 | 3 | next_open | 114 | 0.180 | 0.036 | 0.144 | 0.080 | 0.254 | 1.000 |
| 2.0 | 3 | close | 114 | 0.269 | 0.123 | 0.147 | 0.169 | 0.255 | 1.000 |
| 2.0 | 5 | next_open | 95 | 0.022 | 0.111 | -0.089 | -0.078 | 0.617 | 1.000 |
| 2.0 | 5 | close | 95 | 0.040 | 0.197 | -0.158 | -0.060 | 0.697 | 1.000 |
| 2.0 | 10 | next_open | 72 | 0.632 | 0.302 | 0.330 | 0.532 | 0.249 | 1.000 |
| 2.0 | 10 | close | 72 | 0.645 | 0.389 | 0.256 | 0.545 | 0.303 | 1.000 |
| 3.0 | 1 | next_open | 60 | -0.245 | -0.040 | -0.206 | -0.345 | 0.901 | 1.000 |
| 3.0 | 1 | close | 60 | -0.174 | 0.047 | -0.221 | -0.274 | 0.903 | 1.000 |
| 3.0 | 3 | next_open | 46 | 0.019 | 0.037 | -0.018 | -0.081 | 0.517 | 1.000 |
| 3.0 | 3 | close | 46 | 0.075 | 0.124 | -0.048 | -0.025 | 0.551 | 1.000 |
| 3.0 | 5 | next_open | 41 | 0.694 | 0.105 | 0.589 | 0.594 | 0.102 | 1.000 |
| 3.0 | 5 | close | 41 | 0.761 | 0.191 | 0.569 | 0.661 | 0.115 | 1.000 |
| 3.0 | 10 | next_open | 31 | 0.455 | 0.306 | 0.150 | 0.355 | 0.432 | 1.000 |
| 3.0 | 10 | close | 31 | 0.571 | 0.392 | 0.179 | 0.471 | 0.417 | 1.000 |
| percentile_5 | 5 | next_open | 21 | 0.008 | 0.123 | -0.115 | -0.092 | 0.564 | 1.000 |
| vol_adj_2sigma | 5 | next_open | 67 | 0.539 | 0.107 | 0.432 | 0.439 | 0.125 | 1.000 |

Share of grid cells with positive excess return: 50%. Cells with Holm p < 0.05: 0 of 26. Expected false positives at raw p<0.05 by chance alone: ~1.3.


## Out-of-sample (2019-01-01 -> 2026-09-18) - LOCKED main config

| metric | value |
|---|---|
| n_events | 36.0 |
| event_mean_% | 0.004220070208549309 |
| baseline_mean_% | 0.13403999599423005 |
| excess_mean_% | -0.12981992578568075 |
| event_mean_CI_lo_% | -1.7103729680956425 |
| event_mean_CI_hi_% | 1.4412483755112984 |
| excess_CI_lo_% | -1.8444129640898725 |
| excess_CI_hi_% | 1.3072083795170684 |
| t_vs_zero_p | 0.9958929646670952 |
| welch_p | 0.8744276679986923 |
| mannwhitney_p | 0.32310870916470014 |
| rd_p_greater | 0.6481351864813518 |
| rd_p_two_sided | 0.7011298870112989 |
| event_win_% | 52.77777777777778 |
| baseline_win_% | 52.84244721169464 |
| winrate_binom_p | 1.0 |
| n_raw_events | 51.0 |
| net_mean_% | -0.09577992979145078 |
| net_win_% | 52.77777777777778 |


| index | n | mean_% | median_% | std_% | win_rate_% | p5_% | p95_% | worst_% | best_% | skew |
|---|---|---|---|---|---|---|---|---|---|---|
| events | 36.000 | 0.004 | 0.559 | 4.884 | 52.778 | -8.298 | 5.568 | -18.041 | 7.135 | -1.997 |
| baseline | 1847.000 | 0.134 | 0.155 | 2.123 | 52.842 | -3.147 | 3.271 | -15.649 | 11.152 | -0.310 |


## Overlap check (development): no cooldown -> n=149 events vs 95 with cooldown; mean 0.242% vs 0.022%


## Cost sensitivity (net mean return per trade)

| per_side_bps | round_trip_% | dev_net_mean_% | oos_net_mean_% |
|---|---|---|---|
| 0 | 0.000 | 0.022 | 0.004 |
| 2 | 0.040 | -0.018 | -0.036 |
| 5 | 0.100 | -0.078 | -0.096 |
| 10 | 0.200 | -0.178 | -0.196 |
| 20 | 0.400 | -0.378 | -0.396 |
| 40 | 0.800 | -0.778 | -0.796 |


## Simple event-driven backtest (one position at a time, costs + slippage included)

| period | n_trades | total_return_% | CAGR_% | max_drawdown_% | win_rate_% | avg_trade_% | time_in_market_% | buy_hold_return_% | buy_hold_max_dd_% |
|---|---|---|---|---|---|---|---|---|---|
| Full | 131 | -22.719 | -1.347 | -52.644 | 49.618 | -0.083 | 14.047 | 419.426 | -59.856 |
| Development | 95 | -16.336 | -1.568 | -52.644 | 48.421 | -0.078 | 17.210 | 141.677 | -59.856 |
| Out-of-sample | 36 | -7.629 | -1.024 | -35.454 | 52.778 | -0.096 | 9.459 | 116.321 | -38.440 |
