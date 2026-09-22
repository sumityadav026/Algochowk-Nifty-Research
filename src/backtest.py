"""Simple event-driven backtest: loop day by day, one position at a time, causal signals only."""
import numpy as np
import pandas as pd
from .events import event_mask


def backtest(df, ev, H, entry, costs, start=None, end=None, initial=1.0):
    d = df.loc[start:end] if (start or end) else df
    sig = event_mask(df, ev).fillna(False).reindex(d.index)   # signal uses full history causally, then sliced
    o, c = d["Open"].values, d["Close"].values
    slip = costs["slippage_bps_per_side"] / 1e4
    com = costs["commission_bps_per_side"] / 1e4
    n = len(d)
    equity = np.full(n, np.nan)
    eq, pos, trades = initial, None, []
    for i in range(n):
        # 1) mark to market / exit at the close of day exit_idx
        if pos is not None and i >= pos["entry_i"]:
            if i == pos["exit_idx"]:
                exit_eff = c[i] * (1 - slip)
                eq = pos["base"] * exit_eff / pos["entry_eff"] * (1 - 2 * com)
                trades.append({"signal_date": d.index[pos["sig_i"]], "entry_date": d.index[pos["entry_i"]],
                               "exit_date": d.index[i], "entry_px": pos["entry_px"], "exit_px": c[i],
                               "net_ret": eq / pos["base"] - 1})
                pos = None
                equity[i] = eq
            else:
                equity[i] = pos["base"] * c[i] / pos["entry_eff"]
        else:
            equity[i] = eq
        # 2) signal seen at today's close; only act when flat
        if pos is None and sig.iloc[i]:
            ei = i if entry == "close" else i + 1
            xi = i + H
            if xi < n:
                ep = c[i] if entry == "close" else o[ei]
                pos = {"sig_i": i, "entry_i": ei, "exit_idx": xi, "entry_px": ep,
                       "entry_eff": ep * (1 + slip), "base": eq}
    eqs = pd.Series(equity, index=d.index).ffill()
    tr = pd.DataFrame(trades)
    dd = eqs / eqs.cummax() - 1
    bh = d["Close"] / d["Close"].iloc[0]
    years = max((d.index[-1] - d.index[0]).days / 365.25, 1e-9)
    res = {"n_trades": len(tr), "total_return_%": (eqs.iloc[-1] / initial - 1) * 100,
           "CAGR_%": ((eqs.iloc[-1] / initial) ** (1 / years) - 1) * 100,
           "max_drawdown_%": dd.min() * 100,
           "win_rate_%": (tr["net_ret"] > 0).mean() * 100 if len(tr) else np.nan,
           "avg_trade_%": tr["net_ret"].mean() * 100 if len(tr) else np.nan,
           "time_in_market_%": (len(tr) * H / n) * 100,
           "buy_hold_return_%": (bh.iloc[-1] - 1) * 100,
           "buy_hold_max_dd_%": (bh / bh.cummax() - 1).min() * 100}
    return res, eqs, tr, bh
