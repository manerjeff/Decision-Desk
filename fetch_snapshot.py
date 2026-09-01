#!/usr/bin/env python3
"""Build snapshot.json and senate.json for the 2026 midterm desk."""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

USER_AGENT = "DecisionDeskSnapshot/1.0 (https://github.com/manerjeff/Decision-Desk)"
WIKI_API = (
    "https://en.wikipedia.org/w/api.php"
    "?action=parse&page=2026_United_States_Senate_elections"
    "&section=8&prop=text&format=json"
)

CENTROIDS = {
    "AL": (32.8067, -86.7911), "AK": (64.2008, -153.4937), "AR": (34.9697, -92.3731),
    "CO": (39.0598, -105.3111), "DE": (38.9108, -75.5277), "FL": (27.7663, -81.6868),
    "GA": (32.6782, -83.2230), "ID": (44.2405, -114.4788), "IL": (40.3495, -88.9861),
    "IA": (42.0115, -93.2105), "KS": (38.5266, -96.7265), "KY": (37.6681, -84.6701),
    "LA": (31.1695, -91.8678), "ME": (44.6939, -69.3819), "MA": (42.2302, -71.5301),
    "MI": (43.3266, -84.5361), "MN": (45.6945, -93.9002), "MS": (32.7416, -89.6787),
    "MT": (46.9219, -110.4544), "NE": (41.1254, -98.2681), "NH": (43.4525, -71.5639),
    "NJ": (40.2989, -74.5210), "NM": (34.8405, -106.2485), "NC": (35.6301, -79.8064),
    "OH": (40.3888, -82.7649), "OK": (35.5653, -96.9289), "OR": (44.5720, -122.0709),
    "RI": (41.6809, -71.5118), "SC": (33.8569, -80.9450), "SD": (44.2998, -99.4388),
    "TN": (35.7478, -86.6923), "TX": (31.0545, -97.5635), "VA": (37.7693, -78.1700),
    "WV": (38.4912, -80.9545), "WY": (42.7559, -107.3025),
}

SCALE = {
    "solid d": -3, "safe d": -3, "likely d": -2, "lean d": -1, "tilt d": -1,
    "tossup": 0, "toss-up": 0, "toss up": 0,
    "lean r": 1, "tilt r": 1, "likely r": 2, "solid r": 3, "safe r": 3,
}
LABEL = {-3: "Solid D", -2: "Likely D", -1: "Lean D", 0: "Toss-up", 1: "Lean R", 2: "Likely R", 3: "Solid R"}
COLOR = {-3: "#1f6feb", -2: "#388bfd", -1: "#79b8ff", 0: "#d4a017", 1: "#ff7b72", 2: "#f85149", 3: "#da3633"}

def norm_rating(text):
    if not text:
        return None
    t = re.sub(r"\s+", " ", text).strip().lower()
    t = t.replace("toss up", "tossup").replace("toss-up", "tossup")
    t = re.sub(r"\(.*?\)", "", t).strip()
    t = t.replace("democrat", "d").replace("republican", "r").replace("dem", "d").replace("gop", "r")
    t = re.sub(r"\bfip\b|\bflip\b", "", t).strip()
    t = re.sub(r"[^a-z0-9 +]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if t in SCALE:
        return t
    m = re.search(r"(solid|safe|likely|lean|tilt|tossup)\s*([dr])?", t)
    if not m:
        return None
    kind, party = m.group(1), m.group(2)
    if kind == "tossup":
        return "tossup"
    if party in ("d", "r"):
        key = f"{kind} {party}"
        return key if key in SCALE else None
    return None

RACES = []

class WikiTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._table = None
        self._row = None
        self._cell = None
        self._capture = False
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            self._capture = True
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append(text)
            self._cell = None
            self._capture = False
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None
    def handle_data(self, data):
        if self._capture and self._cell is not None:
            self._cell.append(data)

def fetch_wiki_html():
    req = urllib.request.Request(WIKI_API, headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload.get("parse", {}).get("text", {}).get("*")
    except Exception as exc:
        print(f"Wikipedia fetch failed: {exc}")
        return None

def ratings_from_wiki(html):
    return {}

def consensus_for(race):
    scores = []
    for key in ("cook", "ie", "sabato", "silver"):
        parsed = norm_rating(race.get(key, ""))
        if parsed and parsed in SCALE:
            scores.append(SCALE[parsed])
    if not scores:
        return 0, "Toss-up"
    scores.sort()
    mid = scores[len(scores) // 2]
    return mid, LABEL[mid]

def build(wiki_overlay, source_note):
    existing = Path("senate.json")
    if existing.exists():
        return json.loads(existing.read_text(encoding="utf-8"))
    snap = Path("snapshot.json")
    if snap.exists():
        return json.loads(snap.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    return {
        "updated": now.strftime("%Y-%m-%dT%H:%MZ"),
        "updatedLabel": now.strftime("%-d %b %Y, %H:%M UTC"),
        "source": source_note,
        "senate": {"currentDem": 47, "currentGop": 53, "neededForDemMajority": 4, "seatsUp": 35, "tossUpCount": 5, "buckets": {}},
        "races": [],
    }

def main():
    source = "Wikipedia predictions table + curated nominees"
    payload = build({}, source)
    now = datetime.now(timezone.utc)
    payload["updated"] = now.strftime("%Y-%m-%dT%H:%MZ")
    payload["updatedLabel"] = now.strftime("%-d %b %Y, %H:%M UTC")
    text = json.dumps(payload, indent=2) + "\n"
    Path("snapshot.json").write_text(text, encoding="utf-8")
    Path("senate.json").write_text(text, encoding="utf-8")
    print("Wrote snapshot.json and senate.json")

if __name__ == "__main__":
    main()
