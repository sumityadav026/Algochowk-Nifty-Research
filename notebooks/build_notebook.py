import nbformat as nbf
nb = nbf.v4.new_notebook()
c = lambda s: nbf.v4.new_code_cell(s); m = lambda s: nbf.v4.new_markdown_cell(s)
nb.cells = [
 m("# NIFTY: does a big one-day fall lead to a recovery?\nThin notebook over `src/`. All parameters live in `config.yaml`."),
 c("import sys, yaml, pandas as pd; sys.path.insert(0, '..')\nfrom src.data_loader import prepare\nfrom run_research import analyse, md\ncfg = yaml.safe_load(open('../config.yaml'))\n%cd ..\ndf, rep = prepare(cfg)\nrep"),
 m("## Data checks (see results/data_validation.json)"),
 c("df.describe()"),
 m("## Development-period result for the locked main configuration"),
 c("ev, tr = cfg['event'], cfg['trade']\ndev_end = df.index[df.index < pd.Timestamp(cfg['split']['oos_start'])][-1]\nevents, base, res = analyse(df, cfg, ev, tr['holding_days'], tr['entry'], None, dev_end)\npd.Series(res)"),
 c("events"),
 m("## Change the experiment without touching the engine\nEdit `ev`/`H` below or `config.yaml`."),
 c("for thr in [1.5, 2, 3]:\n    e = {**ev, 'threshold_pct': thr}\n    print(thr, {k: round(v,3) for k,v in analyse(df, cfg, e, 5, 'next_open', None, dev_end)[2].items() if k in ['n_events','event_mean_%','baseline_mean_%','excess_mean_%','rd_p_greater']})"),
 m("For out-of-sample, robustness grid, costs and backtest run `python run_research.py` and read `results/summary.md`."),
]
nbf.write(nb, "notebooks/research.ipynb")
