"""Download, validate and clean NIFTY daily OHLC data. Every check is logged in a report dict."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

COLS = ["Open", "High", "Low", "Close"]


def download_yahoo(ticker, start, end=None):
    import yfinance as yf
    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError("Download returned no data. Use --csv with a file from niftyindices.com instead.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    return df[["Date"] + COLS]


def load_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().title() for c in df.columns]
    return df[["Date"] + COLS]


def validate_and_clean(raw, cfg):
    d = cfg["data"]
    rep = {"raw_rows": int(len(raw))}
    df = raw.copy()

    # 1. dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    rep["unparseable_dates_dropped"] = int(df["Date"].isna().sum())
    df = df.dropna(subset=["Date"])
    if getattr(df["Date"].dt, "tz", None) is not None:
        df["Date"] = df["Date"].dt.tz_localize(None)

    # 2. ordering & duplicates
    rep["was_sorted"] = bool(df["Date"].is_monotonic_increasing)
    rep["duplicate_dates"] = int(df["Date"].duplicated().sum())
    df = df.sort_values("Date").drop_duplicates("Date", keep="last")

    # 3. missing / invalid values
    for c in COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    rep["missing_ohlc_rows"] = int(df[COLS].isna().any(axis=1).sum())
    rep["non_positive_ohlc_rows"] = int((df[COLS] <= 0).any(axis=1).sum())
    df = df.dropna(subset=COLS)
    df = df[(df[COLS] > 0).all(axis=1)]

    # 4. flat bars (O=H=L=C) -> stale placeholders
    flat = (df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"])
    rep["flat_bars"] = int(flat.sum())
    if d.get("drop_flat_bars", True):
        df = df[~flat]

    # 5. OHLC consistency
    rep["high_lt_low_rows_dropped"] = int((df["High"] < df["Low"]).sum())
    df = df[df["High"] >= df["Low"]].copy()
    bad = (df["High"] < df[["Open", "Close"]].max(axis=1)) | (df["Low"] > df[["Open", "Close"]].min(axis=1))
    rep["open_close_outside_range_repaired"] = int(bad.sum())
    df["High"] = df[COLS].max(axis=1)   # repair: widen range to include O and C
    df["Low"] = df[COLS].min(axis=1)
    df = df.set_index("Date")

    # 6. suspicious observations (flagged, NOT auto-removed: real crashes exist, e.g. Oct 2008, Mar 2020)
    ret = df["Close"].pct_change()
    gap = df["Open"] / df["Close"].shift(1) - 1
    big = ret[ret.abs() > d["suspicious_daily_move_pct"] / 100]
    rep["suspicious_daily_moves"] = {str(k.date()): round(float(v) * 100, 2) for k, v in big.items()}
    g = gap[gap.abs() > d["suspicious_gap_pct"] / 100]
    rep["suspicious_open_gaps"] = {str(k.date()): round(float(v) * 100, 2) for k, v in g.items()}
    rep["open_equals_prev_close_share"] = round(float((gap.abs() < 1e-9).mean()), 4)  # high => Open may be stale

    # 7. coverage
    days = df.index.to_series().diff().dt.days
    gaps = days[days > d["max_calendar_gap_days"]]
    rep["calendar_gaps_gt_limit"] = {str(k.date()): int(v) for k, v in gaps.items()}
    rep["first_date"], rep["last_date"] = str(df.index[0].date()), str(df.index[-1].date())
    rep["clean_rows"] = int(len(df))
    per_year = df.groupby(df.index.year).size()
    rep["rows_per_year"] = {int(k): int(v) for k, v in per_year.items()}
    rep["years_with_lt_240_rows"] = [int(y) for y, n in per_year.items() if n < 240]
    return df, rep


def prepare(cfg, csv=None, force_download=False):
    d = cfg["data"]
    raw_path = Path(csv or d["raw_csv"])
    if raw_path.exists() and not force_download:
        raw = load_csv(raw_path)
    else:
        raw = download_yahoo(d["ticker"], d["start"], d["end"])
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(raw_path, index=False)
    clean, rep = validate_and_clean(raw, cfg)
    Path(d["clean_csv"]).parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(d["clean_csv"])
    Path("results").mkdir(exist_ok=True)
    Path("results/data_validation.json").write_text(json.dumps(rep, indent=2))
    return clean, rep
