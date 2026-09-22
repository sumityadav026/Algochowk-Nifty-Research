"""Statistics: descriptive, bootstrap CI, random-day Monte-Carlo test, Welch / Mann-Whitney, Holm correction."""
import numpy as np
from scipy import stats as st


def summarize(x):
    x = np.asarray(x, float)
    if len(x) == 0:
        return {"n": 0}
    return {"n": len(x), "mean_%": x.mean() * 100, "median_%": np.median(x) * 100,
            "std_%": x.std(ddof=1) * 100 if len(x) > 1 else np.nan,
            "win_rate_%": (x > 0).mean() * 100, "p5_%": np.percentile(x, 5) * 100,
            "p95_%": np.percentile(x, 95) * 100, "worst_%": x.min() * 100, "best_%": x.max() * 100,
            "skew": st.skew(x) if len(x) > 2 else np.nan}


def bootstrap_ci(x, n_boot=10000, level=0.95, seed=42, stat=np.mean):
    x = np.asarray(x, float)
    if len(x) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), (n_boot, len(x)))
    b = stat(x[idx], axis=1)
    a = (1 - level) / 2
    return tuple(np.quantile(b, [a, 1 - a]))


def random_day_test(events, baseline, n_perm=10000, seed=42):
    """Null: event days are just random days. Draw n_events random baseline days many times;
    p_greater = share of draws whose mean >= observed event mean ('higher than a normal day')."""
    ev, bl = np.asarray(events, float), np.asarray(baseline, float)
    if len(ev) < 2 or len(bl) < len(ev):
        return {"p_greater": np.nan, "p_two_sided": np.nan}
    rng = np.random.default_rng(seed)
    means = bl[rng.integers(0, len(bl), (n_perm, len(ev)))].mean(axis=1)
    obs = ev.mean()
    p_g = (np.sum(means >= obs) + 1) / (n_perm + 1)
    p_2 = (np.sum(np.abs(means - bl.mean()) >= abs(obs - bl.mean())) + 1) / (n_perm + 1)
    return {"p_greater": p_g, "p_two_sided": p_2}


def compare(events, baseline, n_boot=10000, n_perm=10000, level=0.95, seed=42):
    ev, bl = np.asarray(events, float), np.asarray(baseline, float)
    out = {"n_events": len(ev), "event_mean_%": ev.mean() * 100 if len(ev) else np.nan,
           "baseline_mean_%": bl.mean() * 100,
           "excess_mean_%": (ev.mean() - bl.mean()) * 100 if len(ev) else np.nan}
    if len(ev) < 3:
        return out
    lo, hi = bootstrap_ci(ev, n_boot, level, seed)
    out["event_mean_CI_lo_%"], out["event_mean_CI_hi_%"] = lo * 100, hi * 100
    out["excess_CI_lo_%"], out["excess_CI_hi_%"] = (lo - bl.mean()) * 100, (hi - bl.mean()) * 100
    out["t_vs_zero_p"] = st.ttest_1samp(ev, 0).pvalue
    out["welch_p"] = st.ttest_ind(ev, bl, equal_var=False).pvalue
    out["mannwhitney_p"] = st.mannwhitneyu(ev, bl, alternative="two-sided").pvalue
    out.update({f"rd_{k}": v for k, v in random_day_test(ev, bl, n_perm, seed).items()})
    out["event_win_%"] = (ev > 0).mean() * 100
    out["baseline_win_%"] = (bl > 0).mean() * 100
    out["winrate_binom_p"] = st.binomtest(int((ev > 0).sum()), len(ev), (bl > 0).mean()).pvalue
    return out


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (controls family-wise error across the robustness grid)."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj
