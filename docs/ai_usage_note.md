# AI Usage Note (max 1 page)

> **DRAFT: edit this so it is true for YOU.** The company wants your reasoning; the parts marked [YOU] must be your own honest words. Do not submit claims you did not actually do or understand.

**Tools used:** Claude (code scaffold, module structure, boilerplate for bootstrap/tests/plots, explaining concepts). [YOU: add anything else.]

**How I used it:** to draft the data-loader, event engine, stats and backtest modules and a config-driven runner; I then read every function, ran the tests, and ran the pipeline on real data. [YOU: describe what you actually reviewed/modified.]

**My own decisions:** [YOU: explain in your words why you chose -2%, H=5, next-open entry, cooldown = H, split at 2019, 10 bps costs, and what you would change.]

**Points where AI output needed checking (the design deliberately avoids these; verify you understand each):**
1. *Entry at the event-day close* is a common suggestion but is look-ahead: -2% is only known once the day has closed. Used next-day Open. Unit test `test_entry_uses_next_open_not_event_close`.
2. *Full-sample percentile thresholds* leak future volatility. Used an expanding quantile shifted by one day.
3. *Random train/test split* leaks the future. Used a chronological split and dropped trades whose exit crosses the boundary.
4. *Treating every crash day as independent* inflates n. Added a cooldown equal to the holding period and an overlap sensitivity check.
5. *Comparing to zero instead of a baseline* would credit NIFTY's normal upward drift to the event.
6. *Grid search then pick the best cell* is data snooping; the grid is reported in full with Holm correction and not used to choose the main parameters.
[YOU: add any real mistakes the AI made that you personally caught, e.g. bugs, wrong API usage, over-claims, and what you changed.]

**What I learned:** [YOU: e.g. why baseline matters, what a bootstrap CI means, why significance is not tradability, how clustering breaks independence.]
