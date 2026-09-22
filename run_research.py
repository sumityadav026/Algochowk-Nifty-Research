"""Run the full research pipeline:  python run_research.py [--csv path] [--config config.yaml]
Order: data validation -> DEVELOPMENT analysis -> robustness grid (dev only) -> ONE look at out-of-sample
-> backtest -> results/summary.md + figures."""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd, yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.data_loader import prepare
from src.events import run_experiment
from src.stats import compare, summarize, holm
from src.backtest import backtest


def md(df, floatfmt=3):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else f"{v:.{floatfmt}f}")
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in df.values) + "\n"


def analyse(df, cfg, ev, H, entry, start, end):
    s = cfg["stats"]
    events, base, n_raw = run_experiment(df, ev, H, entry, cfg["trade"]["cooldown_days"], cfg["costs"], start, end)
    res = compare(events["gross_ret"], base, s["n_boot"], s["n_perm"], s["ci_level"], s["seed"])
    res["n_raw_events"] = n_raw
    res["net_mean_%"] = events["net_ret"].mean() * 100 if len(events) else np.nan
    res["net_win_%"] = (events["net_ret"] > 0).mean() * 100 if len(events) else np.nan
    return events, base, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--csv", default=None, help="raw OHLC csv (Date,Open,High,Low,Close). Default: download.")
    ap.add_argument("--refresh", action="store_true", help="re-download even if raw csv exists")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    Path("results").mkdir(exist_ok=True)
    out = ["# Results summary (auto-generated)\n"]

    df, rep = prepare(cfg, a.csv, a.refresh)
    out.append(f"## Data\nRows after cleaning: {rep['clean_rows']} | {rep['first_date']} -> {rep['last_date']}\n\n"
               f"Duplicates: {rep['duplicate_dates']}, missing OHLC rows: {rep['missing_ohlc_rows']}, "
               f"flat bars dropped: {rep['flat_bars']}, OC-outside-range repaired: {rep['open_close_outside_range_repaired']}, "
               f"suspicious daily moves: {len(rep['suspicious_daily_moves'])}, calendar gaps: {len(rep['calendar_gaps_gt_limit'])}\n"
               f"Open==prev Close share: {rep['open_equals_prev_close_share']}\n"
               f"Full detail: results/data_validation.json\n")

    ev, tr = cfg["event"], cfg["trade"]
    H, entry = tr["holding_days"], tr["entry"]
    oos = pd.Timestamp(cfg["split"]["oos_start"])
    dev_end = df.index[df.index < oos][-1]
    ev_all = {"method": ev["method"], **ev}

    # ---- 1. DEVELOPMENT: main config
    e_dev, b_dev, r_dev = analyse(df, cfg, ev, H, entry, None, dev_end)
    e_dev.to_csv("results/events_development.csv")
    out.append(f"## Development ({df.index[0].date()} -> {dev_end.date()}) - main config: {ev['method']} "
               f"{ev.get('threshold_pct')}%, H={H}, entry={entry}\n")
    out.append(md(pd.DataFrame([r_dev]).T.reset_index().rename(columns={"index": "metric", 0: "value"}).astype(str)))
    out.append("\nForward-return distribution (gross):\n\n" +
               md(pd.DataFrame({"events": summarize(e_dev["gross_ret"]), "baseline": summarize(b_dev)}).T.reset_index()))

    # ---- 2. ROBUSTNESS GRID (development only)
    rows = []
    rb = cfg["robustness"]
    for thr in rb["thresholds_pct"]:
        for h in rb["holding_days"]:
            for en in rb["entries"]:
                e = {**ev, "method": "fixed", "threshold_pct": thr}
                _, _, r = analyse(df, cfg, e, h, en, None, dev_end)
                rows.append({"threshold_%": thr, "H": h, "entry": en, "n": r["n_events"],
                             "event_mean_%": r["event_mean_%"], "baseline_%": r["baseline_mean_%"],
                             "excess_%": r["excess_mean_%"], "net_mean_%": r["net_mean_%"],
                             "p_random_day": r.get("rd_p_greater", np.nan)})
    for name, e in {"percentile_5": {**ev, "method": "percentile", "percentile": 5.0},
                    "vol_adj_2sigma": {**ev, "method": "vol_adjusted", "k_sigma": 2.0}}.items():
        _, _, r = analyse(df, cfg, e, H, entry, None, dev_end)
        rows.append({"threshold_%": name, "H": H, "entry": entry, "n": r["n_events"],
                     "event_mean_%": r["event_mean_%"], "baseline_%": r["baseline_mean_%"],
                     "excess_%": r["excess_mean_%"], "net_mean_%": r["net_mean_%"],
                     "p_random_day": r.get("rd_p_greater", np.nan)})
    grid = pd.DataFrame(rows)
    grid["p_holm"] = holm(grid["p_random_day"].fillna(1.0).values)
    grid.to_csv("results/robustness_grid_development.csv", index=False)
    m = len(grid)
    out.append(f"\n## Robustness grid (development only; {m} tests -> Holm-adjusted p shown)\n\n" + md(grid) +
               f"\nShare of grid cells with positive excess return: {(grid['excess_%'] > 0).mean():.0%}. "
               f"Cells with Holm p < 0.05: {(grid['p_holm'] < 0.05).sum()} of {m}. "
               f"Expected false positives at raw p<0.05 by chance alone: ~{0.05 * m:.1f}.\n")

    # ---- 3. OUT-OF-SAMPLE: main config, locked, looked at ONCE
    e_oos, b_oos, r_oos = analyse(df, cfg, ev, H, entry, oos, None)
    e_oos.to_csv("results/events_oos.csv")
    out.append(f"\n## Out-of-sample ({oos.date()} -> {df.index[-1].date()}) - LOCKED main config\n\n" +
               md(pd.DataFrame([r_oos]).T.reset_index().rename(columns={"index": "metric", 0: "value"}).astype(str)))
    out.append("\n" + md(pd.DataFrame({"events": summarize(e_oos["gross_ret"]), "baseline": summarize(b_oos)}).T.reset_index()))

    # ---- 4. Robustness of independence: no cooldown at all (overlapping events allowed)
    tr_nc = {**cfg, "trade": {**tr, "cooldown_days": 1}}
    _, _, r_nc = analyse(df, tr_nc, ev, H, entry, None, dev_end)
    out.append(f"\n## Overlap check (development): no cooldown -> n={r_nc['n_events']} events vs {r_dev['n_events']} with cooldown; "
               f"mean {r_nc['event_mean_%']:.3f}% vs {r_dev['event_mean_%']:.3f}%\n")

    # ---- 5. Cost sensitivity
    cs = []
    for bps in [0, 2, 5, 10, 20, 40]:
        c2 = {"commission_bps_per_side": bps / 2, "slippage_bps_per_side": bps / 2}
        ee, _, _ = run_experiment(df, ev, H, entry, tr["cooldown_days"], c2, None, dev_end)
        eo, _, _ = run_experiment(df, ev, H, entry, tr["cooldown_days"], c2, oos, None)
        cs.append({"per_side_bps": bps, "round_trip_%": 2 * bps / 100,
                   "dev_net_mean_%": ee["net_ret"].mean() * 100, "oos_net_mean_%": eo["net_ret"].mean() * 100})
    out.append("\n## Cost sensitivity (net mean return per trade)\n\n" + md(pd.DataFrame(cs)))

    # ---- 6. Backtest
    bt_rows = []
    fig, ax = plt.subplots(figsize=(9, 4))
    for label, s, e in [("Full", None, None), ("Development", None, dev_end), ("Out-of-sample", oos, None)]:
        res, eqs, trades, bh = backtest(df, ev, H, entry, cfg["costs"], s, e)
        bt_rows.append({"period": label, **res})
        if label == "Full":
            ax.plot(eqs, label="Event strategy (net of costs)"); ax.plot(bh, label="NIFTY buy & hold", alpha=.6)
            trades.to_csv("results/backtest_trades_full.csv", index=False)
    ax.axvline(oos, ls="--", c="grey"); ax.set_title("Backtest equity (growth of 1)"); ax.legend()
    plt.tight_layout(); plt.savefig("results/equity_curve.png", dpi=120); plt.close()
    out.append("\n## Simple event-driven backtest (one position at a time, costs + slippage included)\n\n" + md(pd.DataFrame(bt_rows)))

    # ---- figures
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
    for ax, (t, e, b) in zip(axs, [("Development", e_dev, b_dev), ("Out-of-sample", e_oos, b_oos)]):
        ax.hist(b * 100, bins=60, density=True, alpha=.5, label="all other days")
        ax.hist(e["gross_ret"] * 100, bins=20, density=True, alpha=.6, label="post-fall events")
        ax.axvline(0, c="k", lw=.5); ax.set_title(f"{t}: {H}-day forward return (%)"); ax.legend()
    plt.tight_layout(); plt.savefig("results/return_distributions.png", dpi=120); plt.close()

    Path("results/summary.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
