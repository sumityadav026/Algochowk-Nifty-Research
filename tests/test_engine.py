import numpy as np, pandas as pd
from src.events import trade_frame, apply_cooldown, event_mask

def _df():
    idx = pd.bdate_range("2020-01-01", periods=8)
    return pd.DataFrame({"Open": [10, 11, 12, 13, 14, 15, 16, 17.],
                         "High": 20., "Low": 5.,
                         "Close": [10, 9.7, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5]}, index=idx)

def test_entry_uses_next_open_not_event_close():
    t = trade_frame(_df(), 2, "next_open")
    assert t["entry_px"].iloc[1] == 12          # event at t=1 -> buy Open[2]
    assert t["exit_px"].iloc[1] == 13.5         # exit Close[3] = t+2
    assert np.isclose(t["gross_ret"].iloc[1], 13.5 / 12 - 1)

def test_event_detected_at_close_only():
    m = event_mask(_df(), {"method": "fixed", "threshold_pct": 2.0})
    assert m.iloc[1] and m.sum() == 1

def test_cooldown_blocks_overlap():
    m = pd.Series([True, True, False, True, False, False, True])
    assert apply_cooldown(m, 3).tolist() == [True, False, False, True, False, False, True]
