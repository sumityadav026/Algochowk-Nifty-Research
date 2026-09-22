"""INDEPENDENT cross-check. Re-implements the core calculations with plain loops (different code path
from src/) and compares. Run from the project root AFTER run_research.py:  python tests/cross_check.py"""
import sys, yaml, numpy as np, pandas as pd
sys.path.insert(0, ".")
from scipy import stats as st
from src.events import run_experiment
from src.backtest import backtest

cfg = yaml.safe_load(open("config.yaml"))
df = pd.read_csv(cfg["data"]["clean_csv"], index_col=0, parse_dates=True)
O, C, D = df["Open"].values, df["Close"].values, df.index
n, H = len(df), cfg["trade"]["holding_days"]
thr = cfg["event"]["threshold_pct"] / 100
oos = pd.Timestamp(cfg["split"]["oos_start"])
dev_last = int(np.where(D < oos)[0][-1])
ok = lambda cond: "PASS" if cond else "*** FAIL ***"


def naive(lo, hi, thr, H, method="fixed"):
    """Plain-loop version. Window = index lo..hi inclusive; exit must also be <= hi."""
    r = np.r_[np.nan, C[1:] / C[:-1] - 1]
    raw, ev, last = [], [], -10**9
    for i in range(lo, hi - H + 1):
        if method == "fixed":
            hit = (not np.isnan(r[i])) and r[i] <= -thr
        else:  # expanding 5th percentile of returns up to yesterday, >=250 obs
            hit = i >= 251 and r[i] <= np.quantile(r[1:i], 0.05)
        if hit:
            raw.append(i)
            if i - last >= H:
                ev.append(i); last = i
    rets = [C[i + H] / O[i + 1] - 1 for i in ev]
    rawset = set(raw)
    base = [C[i + H] / O[i + 1] - 1 for i in range(lo, hi - H + 1) if i not in rawset]
    return ev, np.array(rets), np.array(base), len(raw)


print("=" * 70, "\nA. EVENT ENGINE vs NAIVE LOOP")
for name, lo, hi, s, e in [("development", 0, dev_last, None, D[dev_last]), ("out-of-sample", dev_last + 1, n - 1, oos, None)]:
    ev_i, rets, base, nraw = naive(lo, hi, thr, H)
    events, b, nraw_e = run_experiment(df, cfg["event"], H, cfg["trade"]["entry"], cfg["trade"]["cooldown_days"], cfg["costs"], s, e)
    same_n = len(ev_i) == len(events)
    same_dates = same_n and all(D[i] == d for i, d in zip(ev_i, events.index))
    same_ret = same_n and np.allclose(rets, events["gross_ret"].values)
    same_base = np.isclose(base.mean(), b.mean()) and len(base) == len(b)
    print(f"{name:14s} events naive={len(ev_i)} engine={len(events)} | dates {ok(same_dates)} | returns {ok(same_ret)} | "
          f"baseline n {len(base)}/{len(b)} mean {base.mean()*100:.4f}%/{b.mean()*100:.4f}% {ok(same_base)} | raw {nraw}/{nraw_e}")

print("\nB. PERCENTILE-EVENT count (the suspiciously low n=21 in the grid)")
ev_i, _, _, nraw = naive(0, dev_last, thr, H, "percentile")
e2, _, nr2 = run_experiment(df, {**cfg["event"], "method": "percentile", "percentile": 5.0}, H, "next_open", "auto", cfg["costs"], None, D[dev_last])
print(f"naive kept={len(ev_i)} raw={nraw} | engine kept={len(e2)} raw={nr2} {ok(len(ev_i)==len(e2))}")
r = pd.Series(C).pct_change()
print("final expanding 5th-pct threshold at end of dev period: %.2f%%  (fixed rule uses -2.00%%)" % (np.quantile(r.values[1:dev_last], .05) * 100))

print("\nC. STATISTICS cross-check (development, main config)")
ev_i, rets, base, _ = naive(0, dev_last, thr, H)
m, s = rets.mean(), rets.std(ddof=1)
tci = st.t.interval(0.95, len(rets) - 1, loc=m, scale=s / np.sqrt(len(rets)))
rng = np.random.default_rng(999)
bs = np.array([rng.choice(rets, len(rets)).mean() for _ in range(20000)])
print(f"mean {m*100:.3f}% | t-interval [{tci[0]*100:.2f}, {tci[1]*100:.2f}] | bootstrap(loop, other seed) [{np.quantile(bs,.025)*100:.2f}, {np.quantile(bs,.975)*100:.2f}]")
z = (m - base.mean()) / (base.std(ddof=1) / np.sqrt(len(rets)))
print(f"analytic z for 'event mean vs baseline mean' = {z:.2f}, one-sided p = {1-st.norm.cdf(z):.3f}  (engine random-day p was similar if not tiny)")
mw = st.mannwhitneyu(rets, base).pvalue
print(f"independent Mann-Whitney p = {mw:.3f}")

print("\nD. BACKTEST vs hand-compounded trades (development)")
events, _, _ = run_experiment(df, cfg["event"], H, cfg["trade"]["entry"], cfg["trade"]["cooldown_days"], cfg["costs"], None, D[dev_last])
res, eqs, tr, _ = backtest(df, cfg["event"], H, cfg["trade"]["entry"], cfg["costs"], None, D[dev_last])
hand = np.prod(1 + events["net_ret"].values) - 1
diff = np.abs(tr["net_ret"].values - events["net_ret"].values).max() if len(tr) == len(events) else np.nan
print(f"trades {res['n_trades']} vs events {len(events)} | compounded engine net returns {hand*100:.2f}% vs backtest {res['total_return_%']:.2f}% | max per-trade diff {diff:.5f} {ok(diff < 5e-4)}")

print("\nE. IS ONE CRASH CLUSTER DRIVING IT?  (drop 2008-09..2009-12 and 2020-02..2020-06)")
events, base_all, _ = run_experiment(df, cfg["event"], H, cfg["trade"]["entry"], cfg["trade"]["cooldown_days"], cfg["costs"])
def excl(idx):
    return ~(((idx >= "2008-09-01") & (idx <= "2009-12-31")) | ((idx >= "2020-02-01") & (idx <= "2020-06-30")))
evx = events[excl(events.index)]["gross_ret"]
t = pd.DataFrame({"g": (df["Close"].shift(-H) / df["Open"].shift(-1) - 1)}).dropna()
bx = t[excl(t.index)]["g"]
lo, hi = np.quantile(np.random.default_rng(1).choice(evx.values, (10000, len(evx))).mean(1), [.025, .975])
print(f"full sample : n={len(events)} event mean {events['gross_ret'].mean()*100:.3f}% vs baseline {base_all.mean()*100:.3f}%")
print(f"ex-clusters : n={len(evx)} event mean {evx.mean()*100:.3f}% vs baseline {bx.mean()*100:.3f}% | excess CI [{(lo-bx.mean())*100:.2f}, {(hi-bx.mean())*100:.2f}]")

print("\nF. STATISTICAL POWER (what effect could this sample even detect?)")
sd, k = events["gross_ret"].std(ddof=1), len(events)
print(f"n={k}, std={sd*100:.2f}% -> minimum detectable mean excess (80% power, 5% test) ~ {2.8*sd/np.sqrt(k)*100:.2f}%")

print("\nG. MANUAL DATA SPOT-CHECK: 10 worst days. Verify 3-4 against niftyindices.com / NSE / Google Finance")
w = df["Close"].pct_change().nsmallest(10)
for d, v in w.items():
    print(f"  {d.date()}  return {v*100:6.2f}%  close {df.loc[d,'Close']:.2f}")
