#!/usr/bin/env python3
"""Build snapshot.json for the 2026 Senate desk.

Nightly job:
  1. Start from the curated race table (nominees, coordinates).
  2. Pull Wikipedia section 8 (Predictions) and overlay published ratings.
  3. Compute a median consensus of Cook / Inside Elections / Sabato / Silver.
  4. Write snapshot.json. If Wikipedia is down, the curated ratings still ship.
"""
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

RACES = [
    {"state": "Alabama", "abbr": "AL", "held": "R", "open": True, "special": False, "incumbent": "Tommy Tuberville (retiring)", "dem": "Everett Wess", "gop": "Barry Moore", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Alaska", "abbr": "AK", "held": "R", "open": False, "special": False, "incumbent": "Dan Sullivan", "dem": "Mary Peltola", "gop": "Dan Sullivan", "cook": "Tossup", "ie": "Lean R", "sabato": "Tossup", "silver": "Tossup"},
    {"state": "Arkansas", "abbr": "AR", "held": "R", "open": False, "special": False, "incumbent": "Tom Cotton", "dem": "Hallie Shoffner", "gop": "Tom Cotton", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Colorado", "abbr": "CO", "held": "D", "open": False, "special": False, "incumbent": "John Hickenlooper", "dem": "John Hickenlooper", "gop": "Mark Baisley", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "Delaware", "abbr": "DE", "held": "D", "open": False, "special": False, "incumbent": "Chris Coons", "dem": "Chris Coons", "gop": "Michael Katz", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "Florida", "abbr": "FL", "held": "R", "open": False, "special": True, "incumbent": "Ashley Moody", "dem": "Angie Nixon", "gop": "Ashley Moody", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Likely R"},
    {"state": "Georgia", "abbr": "GA", "held": "D", "open": False, "special": False, "incumbent": "Jon Ossoff", "dem": "Jon Ossoff", "gop": "Mike Collins", "cook": "Lean D", "ie": "Tilt D", "sabato": "Likely D", "silver": "Likely D"},
    {"state": "Idaho", "abbr": "ID", "held": "R", "open": False, "special": False, "incumbent": "Jim Risch", "dem": "\u2014", "gop": "Jim Risch", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Illinois", "abbr": "IL", "held": "D", "open": True, "special": False, "incumbent": "Dick Durbin (retiring)", "dem": "Juliana Stratton", "gop": "Don Tracy", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "Iowa", "abbr": "IA", "held": "R", "open": True, "special": False, "incumbent": "Joni Ernst (retiring)", "dem": "Josh Turek", "gop": "Ashley Hinson", "cook": "Tossup", "ie": "Tilt R", "sabato": "Lean R", "silver": "Tossup"},
    {"state": "Kansas", "abbr": "KS", "held": "R", "open": False, "special": False, "incumbent": "Roger Marshall", "dem": "Adam Hamilton", "gop": "Roger Marshall", "cook": "Likely R", "ie": "Solid R", "sabato": "Likely R", "silver": "Likely R"},
    {"state": "Kentucky", "abbr": "KY", "held": "R", "open": True, "special": False, "incumbent": "Mitch McConnell (retiring)", "dem": "Charles Booker", "gop": "Andy Barr", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Louisiana", "abbr": "LA", "held": "R", "open": True, "special": False, "incumbent": "Bill Cassidy (lost primary)", "dem": "Jamie Davis", "gop": "Julia Letlow", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Maine", "abbr": "ME", "held": "R", "open": False, "special": False, "incumbent": "Susan Collins", "dem": "Troy Jackson", "gop": "Susan Collins", "cook": "Tossup", "ie": "Tilt R", "sabato": "Tossup", "silver": "Lean D"},
    {"state": "Massachusetts", "abbr": "MA", "held": "D", "open": False, "special": False, "incumbent": "Ed Markey", "dem": "Ed Markey", "gop": "John Deaton", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "Michigan", "abbr": "MI", "held": "D", "open": True, "special": False, "incumbent": "Gary Peters (retiring)", "dem": "Abdul El-Sayed", "gop": "Mike Rogers", "cook": "Tossup", "ie": "Tossup", "sabato": "Tossup", "silver": "Lean D"},
    {"state": "Minnesota", "abbr": "MN", "held": "D", "open": True, "special": False, "incumbent": "Tina Smith (retiring)", "dem": "Peggy Flanagan", "gop": "Michele Tafoya", "cook": "Likely D", "ie": "Likely D", "sabato": "Likely D", "silver": "Likely D"},
    {"state": "Mississippi", "abbr": "MS", "held": "R", "open": False, "special": False, "incumbent": "Cindy Hyde-Smith", "dem": "Scott Colom", "gop": "Cindy Hyde-Smith", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Montana", "abbr": "MT", "held": "R", "open": True, "special": False, "incumbent": "Steve Daines (retiring)", "dem": "Alani Bankhead", "gop": "Kurt Alme", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Nebraska", "abbr": "NE", "held": "R", "open": False, "special": False, "incumbent": "Pete Ricketts", "dem": "\u2014", "gop": "Pete Ricketts", "cook": "Likely R", "ie": "Likely R", "sabato": "Likely R", "silver": "Likely R"},
    {"state": "New Hampshire", "abbr": "NH", "held": "D", "open": True, "special": False, "incumbent": "Jeanne Shaheen (retiring)", "dem": "Chris Pappas", "gop": "Scott Brown", "cook": "Lean D", "ie": "Tilt D", "sabato": "Lean D", "silver": "Likely D"},
    {"state": "New Jersey", "abbr": "NJ", "held": "D", "open": False, "special": False, "incumbent": "Cory Booker", "dem": "Cory Booker", "gop": "Justin Murphy", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "New Mexico", "abbr": "NM", "held": "D", "open": False, "special": False, "incumbent": "Ben Ray Luj\u00e1n", "dem": "Ben Ray Luj\u00e1n", "gop": "Larry Marker", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "North Carolina", "abbr": "NC", "held": "R", "open": True, "special": False, "incumbent": "Thom Tillis (retiring)", "dem": "Roy Cooper", "gop": "Michael Whatley", "cook": "Lean D", "ie": "Tilt D", "sabato": "Lean D", "silver": "Likely D"},
    {"state": "Ohio", "abbr": "OH", "held": "R", "open": False, "special": True, "incumbent": "Jon Husted", "dem": "Sherrod Brown", "gop": "Jon Husted", "cook": "Tossup", "ie": "Tilt R", "sabato": "Tossup", "silver": "Lean D"},
    {"state": "Oklahoma", "abbr": "OK", "held": "R", "open": True, "special": False, "incumbent": "Open Republican seat", "dem": "N'Kiyla Jasmine Thomas", "gop": "Kevin Hern", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Oregon", "abbr": "OR", "held": "D", "open": False, "special": False, "incumbent": "Jeff Merkley", "dem": "Jeff Merkley", "gop": "David Brock Smith", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "Rhode Island", "abbr": "RI", "held": "D", "open": False, "special": False, "incumbent": "Jack Reed", "dem": "Jack Reed", "gop": "Raymond McKay", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "South Carolina", "abbr": "SC", "held": "R", "open": False, "special": False, "incumbent": "Lindsey Graham", "dem": "Annie Andrews", "gop": "Lindsey Graham", "cook": "Solid R", "ie": "Likely R", "sabato": "Safe R", "silver": "Likely R"},
    {"state": "South Dakota", "abbr": "SD", "held": "R", "open": False, "special": False, "incumbent": "Mike Rounds", "dem": "\u2014", "gop": "Mike Rounds", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Tennessee", "abbr": "TN", "held": "R", "open": False, "special": False, "incumbent": "Bill Hagerty", "dem": "Marquita Bradshaw", "gop": "Bill Hagerty", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Texas", "abbr": "TX", "held": "R", "open": True, "special": False, "incumbent": "John Cornyn (lost primary)", "dem": "James Talarico", "gop": "Ken Paxton", "cook": "Tossup", "ie": "Lean R", "sabato": "Tossup", "silver": "Lean D"},
    {"state": "Virginia", "abbr": "VA", "held": "D", "open": False, "special": False, "incumbent": "Mark Warner", "dem": "Mark Warner", "gop": "Bert Mizusawa", "cook": "Solid D", "ie": "Solid D", "sabato": "Safe D", "silver": "Solid D"},
    {"state": "West Virginia", "abbr": "WV", "held": "R", "open": False, "special": False, "incumbent": "Shelley Moore Capito", "dem": "Rachel Fetty Anderson", "gop": "Shelley Moore Capito", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
    {"state": "Wyoming", "abbr": "WY", "held": "R", "open": True, "special": False, "incumbent": "Cynthia Lummis (retiring)", "dem": "James W. Byrd", "gop": "Harriet Hageman", "cook": "Solid R", "ie": "Solid R", "sabato": "Safe R", "silver": "Solid R"},
]

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
    parser = WikiTableParser()
    parser.feed(html)
    found = {}
    states = {row["state"].lower(): row["abbr"] for row in RACES}
    for table in parser.tables:
        if len(table) < 8:
            continue
        header = [c.lower() for c in table[0]]
        if not any("cook" in c for c in header):
            if len(table) > 1 and any("cook" in c.lower() for c in table[1]):
                header = [c.lower() for c in table[1]]
            else:
                continue
        col_map = {}
        for i, h in enumerate(header):
            if "cook" in h:
                col_map["cook"] = i
            elif h.startswith("ie") or "inside" in h:
                col_map["ie"] = i
            elif "sabato" in h:
                col_map["sabato"] = i
            elif "silver" in h:
                col_map["silver"] = i
        if "cook" not in col_map:
            continue
        for row in table[1:]:
            if not row:
                continue
            label = re.sub(r"\(special\)", "", row[0].split("[")[0], flags=re.I).strip()
            abbr = states.get(label.lower())
            if not abbr:
                continue
            ratings = {}
            for key, idx in col_map.items():
                if idx < len(row):
                    parsed = norm_rating(row[idx])
                    if parsed:
                        ratings[key] = "Toss-up" if parsed == "tossup" else LABEL[SCALE[parsed]]
            if ratings:
                found[abbr] = ratings
        if found:
            break
    return found

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
    races = []
    buckets = {k: 0 for k in LABEL.values()}
    for raw in RACES:
        race = dict(raw)
        race.update(wiki_overlay.get(race["abbr"], {}))
        score, consensus = consensus_for(race)
        race["score"] = score
        race["consensus"] = consensus
        race["color"] = COLOR[score]
        race["lat"], race["lng"] = CENTROIDS[race["abbr"]]
        race["matchup"] = f"{race['dem']} (D) vs. {race['gop']} (R)"
        buckets[consensus] = buckets.get(consensus, 0) + 1
        races.append(race)
    watch = [r["state"] for r in sorted(races, key=lambda r: (abs(r["score"]), r["state"])) if abs(r["score"]) <= 1]
    now = datetime.now(timezone.utc)
    return {
        "updated": now.strftime("%Y-%m-%dT%H:%MZ"),
        "updatedLabel": now.strftime("%-d %b %Y, %H:%M UTC"),
        "source": source_note,
        "disclaimer": "Independent briefing. Not affiliated with Decision Desk HQ or The Cook Political Report.",
        "license": "Ratings table sourced from Wikipedia, CC BY-SA.",
        "senate": {
            "currentDem": 47, "currentGop": 53, "neededForDemMajority": 4,
            "seatsUp": 35, "demSeatsUp": 13, "gopSeatsUp": 22,
            "buckets": buckets, "watch": watch[:10], "tossUpCount": buckets.get("Toss-up", 0),
        },
        "races": sorted(races, key=lambda r: (abs(r["score"]), r["score"], r["state"])),
    }

def main():
    html = fetch_wiki_html()
    overlay = ratings_from_wiki(html) if html else {}
    source = "Wikipedia predictions table + curated nominees" if html else "Curated snapshot (Wikipedia unreachable)"
    if html:
        print(f"Wikipedia overlay applied to {len(overlay)} states.")
    payload = build(overlay, source)
    Path("snapshot.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote snapshot.json with {len(payload['races'])} Senate races.")

if __name__ == "__main__":
    main()
