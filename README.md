# Does NIFTY Recover After a Big One-Day Fall? An Event Study (2007–2026)

**Question:** After a significant one-day fall in NIFTY 50, does the market tend to recover over the next few trading days?

**Answer:** No. Post-fall 5-day returns are statistically indistinguishable from NIFTY's normal drift, both in-sample and out-of-sample. Full evidence below.

**Research Note:** [docs/research_note.pdf](docs/research_note.pdf) · **AI Usage Note:** [docs/ai_usage_note.pdf](docs/ai_usage_note.pdf) · **Video walkthrough:** [add link once recorded]

## Quick start
```bash
pip install -r requirements.txt
python run_research.py                    # downloads ^NSEI from Yahoo Finance, runs everything
# offline / alternative source: python run_research.py --csv path/to/nifty.csv   (columns Date,Open,High,Low,Close)
python -m pytest -q tests                 # unit tests (look-ahead, cooldown, event detection)
python tests/cross_check.py               # independent re-derivation of all core statistics
```
Outputs: `results/summary.md`, `results/data_validation.json`, `results/*.csv`, `results/*.png`.
Every parameter (threshold, holding period, entry rule, costs, split date, event method) is in `config.yaml` — changing the experiment never requires touching the code.

## Data
- **Source:** Yahoo Finance, ticker `^NSEI` (NIFTY 50 index level, daily), via the `yfinance` Python library.
- **Fields:** Date, Open, High, Low, Close. Price index level, not total return (dividends excluded — immaterial for a 1–10 day holding horizon).
- **Range:** 2007-09-17 to 2026-09-18 — 4,663 trading days after cleaning.
- **Validation checks:** unparseable/duplicate/unsorted dates, missing or non-positive OHLC, High<Low, Open/Close outside [Low, High], flat O=H=L=C rows (stale placeholders), moves >8%, open gaps >4%, calendar gaps >5 days, rows per year, share of days where Open equals the previous Close. Full detail in `results/data_validation.json`.
- **What was actually found:** 0 duplicate dates, 1 missing-OHLC row (dropped), 0 flat bars, 0 High/Low repairs needed, 6 flagged "suspicious" daily moves, and 1 calendar gap exceeding 5 days. All 6 suspicious moves correspond to the 2008 financial crisis and the 2020 COVID crash — genuine crisis-period volatility, not data errors. Open equals the previous Close on only 0.47% of days, indicating Open is a real opening print rather than a stale carry-forward.
- **Independent verification:** three of the largest single-day falls in the dataset — 2020-03-23 (−12.98%, close 7610.25), 2008-10-24 (−12.20%, close 2584.00), and 2008-01-21 (−8.70%, close 5208.80) — were manually cross-checked against an independent public source (niftyindices.com / Google Finance) and matched exactly.

## Method (fixed before looking at results)
| Item | Choice | Why |
|---|---|---|
| Event | Close-to-close return ≤ −2.0% | Roughly twice NIFTY's typical daily volatility — a clear outlier without being so rare that too few events remain. Percentile and volatility-adjusted versions are robustness checks, not alternatives searched over. |
| Entry | **Open of the next trading day** | The −2% return is only known at the close, so buying that close would use information not yet available (look-ahead bias). Verified by a unit test. |
| Exit | Close of event day + 5 trading days | ≈ one trading week; fixed a priori. 1/3/10-day holds are robustness checks. |
| Independence | Cooldown = holding period (non-overlapping trades) | Crashes cluster in time (e.g., Oct 2008, Mar 2020); overlapping windows are not independent observations. |
| Baseline | Same entry/exit rule applied to every non-event day in the same period | NIFTY drifts upward over time; "positive after a fall" means nothing without this comparison. |
| Costs | 3 bps commission + 2 bps slippage per side = 0.10% round trip; sensitivity tested 0–0.8% | Approximate cost for an index futures/ETF proxy. |
| Split | Development: 2007-09-17 to 2018-12-31. Out-of-sample: 2019-01-01 to 2026-09-18 | Chronological, never random. Trades whose exit crosses the split boundary are excluded from both windows to prevent leakage. |

**Statistics used and why:** n (small n = weak evidence); mean and median (mean is fragile to one large rebound); win rate; std and 5th/95th percentiles (risk); bootstrap 95% CI of the mean (no normality assumption, valid for skewed small samples); a random-day Monte-Carlo test (draw n random non-event days 10,000 times — how often does a random set do as well as the event set? This directly answers "is this better than normal?"); Welch t-test and Mann-Whitney as cross-checks; Holm correction across the robustness grid to control for testing 26 configurations.

**Statistical vs. economic significance:** even a marginally significant excess of a few basis points is not tradable once 10 bps round-trip costs are applied — the cost sensitivity table and backtest address this directly.

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
## Results

**Development (2007–2018), main configuration (−2.0%, H=5, next-open entry):**
n = 95 events (149 raw, before the independence cooldown). Mean 5-day return +0.02% vs. baseline +0.11% → **excess −0.09%**, 95% bootstrap CI **[−1.03%, +0.81%]** (includes zero). Random-day Monte-Carlo test p = 0.62. Win rate 48.4% vs. 54.9% baseline. **No evidence of an effect beyond normal market drift.**

**Robustness (development only, 26 configurations — thresholds ±1.5/2/3%, holding periods 1/3/5/10 days, two entry rules, percentile and volatility-adjusted event definitions):**
50% of configurations showed positive excess return, 50% negative — the sign was unstable across neighbouring parameter choices. **0 of 26 remained significant after Holm correction** (expected false positives from chance alone at raw p<0.05: ~1.3). No configuration was selected as "best" and reused; the grid exists only to test stability of the main result.

**Out-of-sample (2019–2026), same locked configuration, evaluated once:**
n = 36 events (51 raw). Mean +0.00% vs. baseline +0.13% → **excess −0.13%**, 95% CI **[−1.84%, +1.31%]** (includes zero). Random-day p = 0.65. Win rate 52.8% vs. 52.8% baseline. **The "no effect" finding persisted unchanged from development** — not an artifact of the earlier period.

**Overlap / independence check:** without the cooldown rule, 149 overlapping "events" are found instead of 95, and the mean return rises to +0.24% purely from double-counting clustered crash days — confirming that treating overlapping falls as independent observations inflates the apparent effect.

**Crisis-cluster check:** excluding the 2008-09/2009-12 and 2020-02/2020-06 crisis windows (n drops from 131 to 92 on the full sample) **flips the sign of the excess return from −0.10% to +0.10%** — but the CI still includes zero **[−0.65%, +0.80%]**. A changed sign is not a confirmed effect; the overall result is not being driven by, nor rescued by, these two episodes alone.

**Cost sensitivity:** net mean return per trade falls monotonically as costs rise — from +0.02% (development) / +0.00% (OOS) at zero cost, to −0.18% / −0.20% at a 20 bps round trip. Any theoretical edge is well within the range that realistic trading costs eliminate.

**Simple event-driven backtest (one position at a time, net of 10 bps round-trip costs):**
| Period | Trades | Total return | CAGR | Max drawdown | Buy & hold return | Buy & hold max DD |
|---|---|---|---|---|---|---|
| Full (2007–2026) | 131 | −22.7% | −1.3% | −52.6% | +419.4% | −59.9% |
| Development | 95 | −16.3% | −1.6% | −52.6% | +141.7% | −59.9% |
| Out-of-sample | 36 | −7.6% | −1.0% | −35.5% | +116.3% | −38.4% |

Trading this rule loses money net of costs in every period tested, while simply holding NIFTY throughout would have substantially outperformed it.

## Limitations
- With ~95 development events, the design has statistical power to reliably detect only an excess return of roughly **1.1% or larger** — a smaller true effect cannot be ruled out, so "no evidence of an effect" is the correct conclusion, not "proof no effect exists."
- Post-fall returns are influenced by a small number of extreme episodes (2008, 2020); regime dependence is plausible even though the headline result does not hinge on these clusters alone.
- The index level excludes dividends and is not directly tradable; a futures/ETF proxy would add basis or tracking error beyond the assumed costs.
- Yahoo Finance is a credible but unofficial source; three of the largest moves were independently verified, but the full series was not cross-checked date-by-date against NSE's own data.
- The 26-cell robustness grid is multiple testing on a single dataset; Holm correction reduces but does not eliminate the risk that any single "good-looking" cell is a false positive.
- Overlapping return windows in the baseline sample are autocorrelated, so the baseline "n" overstates its independent information content; the random-day test is less sensitive to this than a naive t-test, but reported p-values should be read as approximate.

## What would make me reject the hypothesis
The evidence already leans this way, but concretely: the excess-return confidence interval including zero in development; the effect being absent out-of-sample; the effect vanishing after realistic transaction costs; the effect existing only inside the 2008/2020 crisis clusters and disappearing once they are excluded; Holm-adjusted p-values ≥ 0.05 across the robustness grid; and the sign of the effect flipping across neighbouring, equally reasonable thresholds and holding periods. All of these conditions were observed in this study.