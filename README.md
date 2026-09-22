# Does NIFTY recover after a big one-day fall? An event study

**Question:** After a significant one-day fall in NIFTY 50, does the market tend to recover over the next few trading days?
**Answer:** see `results/summary.md` after running the pipeline (fill the "Results" section below from it).

## Quick start
```bash
pip install -r requirements.txt
python run_research.py                    # downloads ^NSEI from Yahoo Finance, runs everything
# offline / alternative source: python run_research.py --csv path/to/nifty.csv   (columns Date,Open,High,Low,Close)
python -m pytest -q tests                 # unit tests (look-ahead, cooldown, event detection)
```
Outputs: `results/summary.md`, `results/data_validation.json`, `results/*.csv`, `results/*.png`.
Every parameter (threshold, holding period, entry rule, costs, split date, event method) is in `config.yaml`.

## Data
- **Source:** Yahoo Finance ticker `^NSEI` (NIFTY 50 index level, daily) via `yfinance`. Cross-check a handful of dates against niftyindices.com and note the result here: `[TODO]`.
- **Fields:** Date, Open, High, Low, Close. Index level, not total return (dividends excluded).
- **Range:** from 2007-09-17 (start of Yahoo's history) to the latest close. Actual coverage is written to `results/data_validation.json`.
- **Checks:** unparseable/duplicate/unsorted dates, missing or non-positive OHLC, High<Low, Open/Close outside [Low,High], flat O=H=L=C rows (stale placeholders, dropped), moves >8%, open gaps >4%, calendar gaps >5 days, rows per year, share of days where Open equals previous Close (a sign Open is not a genuine opening print).
- **Cleaning:** drop invalid rows; keep last of duplicate dates; repair High/Low to include Open/Close; **suspicious big moves are flagged, not deleted** (real crashes such as Oct 2008 and Mar 2020 look "suspicious" but are genuine and are exactly the events under study). `[TODO: list anything you actually found]`

## Method (fixed before looking at results)
| Item | Choice | Why |
|---|---|---|
| Event | Close-to-close return <= -2.0% | Simple, reproducible; roughly the worst few % of days. Percentile and vol-adjusted versions are robustness checks. |
| Entry | **Open of the next trading day** | The -2% is only known at the close, so buying that close is look-ahead. |
| Exit | Close of event day + 5 trading days | 5 days ~ one trading week; fixed a priori. 1/3/10 are robustness. |
| Independence | Cooldown = holding period (non-overlapping trades) | Crashes cluster; overlapping windows are not independent samples. |
| Baseline | Same entry/exit rule applied to every non-event day in the same period | NIFTY drifts upward; "positive after a fall" means nothing without this. |
| Costs | 3 bps commission + 2 bps slippage per side = 0.10% round trip; sensitivity 0-0.8% | Approximate for index futures/ETF. |
| Split | Development up to 2018-12-31, out-of-sample from 2019-01-01 | Time split, never random. Trades whose exit crosses the boundary are excluded. |

**Statistics and why:** n (small n = weak evidence); mean and median (mean is fragile to one big rebound); win rate; std and 5th/95th percentiles (risk); bootstrap 95% CI of the mean (no normality assumption, valid for skewed small samples); **random-day Monte-Carlo test** (draw n random non-event days 10,000 times: how often is a random set of days as good as the event set? this directly answers "is this better than normal?"); Welch t and Mann-Whitney as cross-checks; Holm correction over the robustness grid.

**Statistical vs economic significance:** even a significant excess of a few bps is not tradable after 10 bps costs; costs and the backtest address that.

## Repo layout
```
config.yaml          all research parameters
run_research.py      end-to-end pipeline
src/data_loader.py   download + validation + cleaning
src/events.py        event detection, forward returns, cooldown
src/stats.py         summaries, bootstrap, random-day test, Holm
src/backtest.py      simple event-driven backtest
tests/               look-ahead and logic tests, synthetic data generator (pipeline testing only)
notebooks/           thin notebook over src/
docs/                research_note.md, ai_usage_note.md
```

## Results  `[TODO: fill from results/summary.md, one short paragraph each]`
- Development: n = , mean = , baseline = , CI = , random-day p = 
- Robustness: share of cells with positive excess, Holm-significant cells
- Out-of-sample: n = , mean = , baseline = , persisted? what changed?
- Backtest: trades, net return, max drawdown vs buy & hold

## Limitations
- Few events at a -2% threshold, especially per sub-period; confidence intervals will be wide.
- Post-fall returns are dominated by a few episodes (2008, 2020); regime dependence is likely.
- Index level ignores dividends; the index itself is not directly tradable (futures/ETF add basis/tracking error).
- Yahoo is a credible but unofficial source; Open prices for an index can be derived rather than a true auction print.
- The robustness grid is multiple testing on one dataset; Holm correction helps but the grid also reuses the same data.
- Overlapping windows in the baseline are autocorrelated, so baseline "n" overstates its independent information (the random-day test is less sensitive to this than a naive t-test, but the p-values are still approximate).

## What would make me reject the hypothesis
Excess return CI includes zero (or negative) in development; effect not present out-of-sample; effect vanishes after 10 bps costs; effect exists only in 2008/2020 and disappears when those clusters are removed; Holm-adjusted p >= 0.05; results flip sign across reasonable thresholds/holding periods.
