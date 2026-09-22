"""Event detection and forward returns. Every rule uses only information available at the event close."""
import numpy as np
import pandas as pd


def event_mask(df, ev):
    r = df["Close"].pct_change()
    m = ev["method"]
    if m == "fixed":
        return r <= -ev["threshold_pct"] / 100
    if m == "percentile":  # expanding quantile, shifted 1 day => no look-ahead
        q = r.expanding(min_periods=ev.get("min_history", 250)).quantile(ev["percentile"] / 100).shift(1)
        return r <= q
    if m == "vol_adjusted":
        sd = r.rolling(ev["vol_window"]).std().shift(1)
        return r <= -ev["k_sigma"] * sd
    raise ValueError(f"unknown event method {m}")


def apply_cooldown(mask, cooldown):
    """Keep an event only if >= `cooldown` trading days passed since the last KEPT event."""
    vals, out, last = mask.values, np.zeros(len(mask), bool), -10**9
    for i in range(len(vals)):
        if vals[i] and i - last >= cooldown:
            out[i], last = True, i
    return pd.Series(out, index=mask.index)


def trade_frame(df, H, entry):
    """Gross return of a trade for EVERY day t, assuming the signal is seen at close of day t.
    next_open: buy Open[t+1]. close: buy Close[t] (optimistic). Exit: Close[t+H]."""
    ep = df["Open"].shift(-1) if entry == "next_open" else df["Close"]
    xp = df["Close"].shift(-H)
    return pd.DataFrame({
        "event_ret": df["Close"].pct_change(),
        "entry_px": ep, "exit_px": xp,
        "exit_date": df.index.to_series().shift(-H),
        "gross_ret": xp / ep - 1,
    })


def run_experiment(df, ev, H, entry, cooldown, costs, start=None, end=None):
    """Returns (events_df, baseline_returns, n_raw_events). Trades whose exit falls after `end` are
    excluded, so nothing from the out-of-sample window leaks into the development window."""
    start = pd.Timestamp(start) if start else df.index[0]
    end = pd.Timestamp(end) if end else df.index[-1]
    t = trade_frame(df, H, entry)
    valid = (df.index >= start) & (df.index <= end) & t["gross_ret"].notna() & (t["exit_date"] <= end)
    raw = event_mask(df, ev).fillna(False) & valid
    cd = H if cooldown == "auto" else int(cooldown)
    kept = apply_cooldown(raw, cd)
    rt_cost = 2 * (costs["commission_bps_per_side"] + costs["slippage_bps_per_side"]) / 1e4
    events = t[kept].copy()
    events["net_ret"] = events["gross_ret"] - rt_cost
    baseline = t.loc[valid & ~raw, "gross_ret"]
    return events, baseline, int(raw.sum())
