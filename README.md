# 2026 Senate Desk

Independent briefing of the 35 U.S. Senate seats on the 2026 ballot.

Live site: https://manerjeff.github.io/Decision-Desk/

## What updates automatically

GitHub Actions runs twice a day and on demand. `fetch_snapshot.py` reads the Predictions table on [Wikipedia’s 2026 Senate elections page](https://en.wikipedia.org/wiki/2026_United_States_Senate_elections) and writes `snapshot.json`. Consensus is the median of Cook, Inside Elections, Sabato, and Silver. Nominees stay in the curated table until you edit them.

This is not an AP or Decision Desk HQ feed. Ratings belong to their publishers. Wikipedia text is CC BY-SA.

## Edit a nominee

Change the race row in `fetch_snapshot.py`, run `python3 fetch_snapshot.py`, commit `snapshot.json`.
