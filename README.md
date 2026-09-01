# 2026 Midterm Election Polling Desk

Independent snapshot of 2026 Senate, governor, and House-generic races.

Live site: https://manerjeff.github.io/Decision-Desk/

This project is **not affiliated with Decision Desk HQ**.

## What the desk shows

- Current Senate: 47 Democratic / 53 Republican
- 35 Senate seats on the 2026 ballot (Class 2 plus Florida and Ohio specials)
- Democrats need a net gain of 4 for a majority
- Featured race per state, with a Senate-only map that leaves non-ballot states gray
- House generic ballot as vote share, not a seat projection

Numbers are an editorial snapshot in `fetch_polls.py`. The GitHub Action rebuilds `polls.json` from that table; it does not scrape pollsters yet.

## Update the snapshot

1. Edit the race table in `fetch_polls.py`
2. Run `python3 fetch_polls.py`
3. Commit `fetch_polls.py` and `polls.json`
