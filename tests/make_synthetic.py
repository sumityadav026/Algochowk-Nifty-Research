"""Synthetic index with volatility clustering and NO mean reversion. Used ONLY to test the code path.
Never use its output as a research result."""
import numpy as np, pandas as pd

def make(path="data/synthetic_test.csv", seed=1):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2007-09-17", "2025-12-31")
    n = len(dates); vol = np.empty(n); vol[0] = 0.01
    for i in range(1, n):
        vol[i] = np.sqrt(1e-6 + 0.08 * (vol[i-1] * rng.standard_normal()) ** 2 + 0.9 * vol[i-1] ** 2)
    r = 0.0004 + vol * rng.standard_t(6, n) * 0.8
    close = 4000 * np.exp(np.cumsum(r))
    op = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.003, n))
    hi = np.maximum(op, close) * (1 + np.abs(rng.normal(0, 0.003, n)))
    lo = np.minimum(op, close) * (1 - np.abs(rng.normal(0, 0.003, n)))
    df = pd.DataFrame({"Date": dates, "Open": op, "High": hi, "Low": lo, "Close": close})
    # inject dirt so the validator has something to catch
    df = pd.concat([df, df.iloc[[100, 200]]]).sample(frac=1, random_state=0)
    df.loc[df.index[5], "Close"] = np.nan
    df.to_csv(path, index=False)

if __name__ == "__main__":
    make()
