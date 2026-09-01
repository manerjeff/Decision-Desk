#!/usr/bin/env python3
"""Build polls.json from a curated 2026 midterm table.

This is an editorial snapshot, not a live poll scrape. Coordinates and
postal codes are fixed so the map cannot collapse onto Kansas.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

CENTROIDS = {
    "AL": (32.8067, -86.7911), "AK": (63.5888, -154.4933), "AZ": (34.0489, -111.0937),
    "AR": (34.9697, -92.3731), "CA": (36.7783, -119.4179), "CO": (39.0598, -105.3111),
    "CT": (41.5978, -72.7554), "DE": (38.9108, -75.5277), "FL": (27.7663, -81.6868),
    "GA": (32.6782, -83.2230), "HI": (19.8968, -155.5828), "ID": (44.2405, -114.4788),
    "IL": (40.3495, -88.9861), "IN": (39.8494, -86.2583), "IA": (42.0115, -93.2105),
    "KS": (38.5266, -96.7265), "KY": (37.6681, -84.6701), "LA": (31.1695, -91.8678),
    "ME": (44.6939, -69.3819), "MD": (39.0639, -76.8021), "MA": (42.2302, -71.5301),
    "MI": (43.3266, -84.5361), "MN": (45.6945, -93.9002), "MS": (32.7416, -89.6787),
    "MO": (38.4561, -92.2884), "MT": (46.9219, -110.4544), "NE": (41.1254, -98.2681),
    "NV": (38.4199, -117.1219), "NH": (43.4525, -71.5639), "NJ": (40.2989, -74.5210),
    "NM": (34.8405, -106.2485), "NY": (42.1657, -74.9481), "NC": (35.6301, -79.8064),
    "ND": (47.5289, -99.7840), "OH": (40.3888, -82.7649), "OK": (35.5653, -96.9289),
    "OR": (44.5720, -122.0709), "PA": (40.5908, -77.2098), "RI": (41.6809, -71.5118),
    "SC": (33.8569, -80.9450), "SD": (44.2998, -99.4388), "TN": (35.7478, -86.6923),
    "TX": (31.0545, -97.5635), "UT": (40.1500, -111.8624), "VT": (44.0459, -72.7107),
    "VA": (37.7693, -78.1700), "WA": (47.4009, -121.4905), "WV": (38.4912, -80.9545),
    "WI": (44.2685, -89.6165), "WY": (42.7559, -107.3025),
}

SENATE_UP = {
    "AL", "AK", "AR", "CO", "DE", "FL", "GA", "ID", "IL", "IA", "KS", "KY", "LA",
    "ME", "MA", "MI", "MN", "MS", "MT", "NE", "NH", "NJ", "NM", "NC", "OH", "OK",
    "OR", "RI", "SC", "SD", "TN", "TX", "VA", "WV", "WY",
}

DEM, GOP, TOSS = "dem", "gop", "battleground"
COLORS = {DEM: "#388bfd", GOP: "#f85149", TOSS: "#d29922"}
BADGES = {DEM: "badge-dem", GOP: "badge-gop", TOSS: "badge-tossup"}


def pct_from_lead(lead: str, lean: str) -> str:
    digits = "".join(ch for ch in lead if ch.isdigit() or ch == ".")
    try:
        margin = float(digits) if digits else 0.0
    except ValueError:
        margin = 0.0
    if lean == TOSS:
        return "50%"
    share = min(78.0, max(51.0, 50.0 + margin / 2.0))
    return f"{share:.0f}%"


def race(state, abbr, category, lean, lead, desc, featured=False, source="Editorial snapshot"):
    lat, lng = CENTROIDS[abbr]
    return {
        "id": f"{state.lower().replace(' ', '-')}-{category}",
        "state": state,
        "abbr": abbr,
        "type": lean,
        "category": category,
        "featured": featured,
        "senateUp": abbr in SENATE_UP,
        "icon": abbr,
        "name": f"{state} {category.title()}",
        "lat": lat,
        "lng": lng,
        "lead": lead,
        "leadPct": pct_from_lead(lead, lean),
        "barColor": COLORS[lean],
        "leadClass": BADGES[lean],
        "desc": desc,
        "source": source,
        "news": [{"time": source, "headline": f"{lead} — {desc}"}],
    }


RACES = [
    race("Alabama", "AL", "senate", GOP, "MOORE +19.0%", "Barry Moore (R) leads Everett Wess (D) for the open Sessions seat.", True),
    race("Alaska", "AK", "senate", TOSS, "TOSS-UP +1.2%", "Dan Sullivan (R) vs. Mary Peltola (D). Ranked-choice final four.", True),
    race("Arizona", "AZ", "gov", TOSS, "HOBBS +1.4%", "Katie Hobbs (D) vs. Andy Biggs (R). No Senate seat on the 2026 ballot.", True),
    race("Arkansas", "AR", "senate", GOP, "BOOZMAN +18.0%", "John Boozman (R) is heavily favored in this Class 2 seat.", True),
    race("Arkansas", "AR", "gov", GOP, "SANDERS +18.0%", "Sarah Huckabee Sanders (R) remains the clear favorite."),
    race("California", "CA", "gov", DEM, "BECERRA +19.0%", "Xavier Becerra (D) vs. Steve Hilton (R). No Senate seat on the 2026 ballot.", True),
    race("Colorado", "CO", "senate", DEM, "HICKENLOOPER +8.5%", "John Hickenlooper (D) leads Mark Baisley (R).", True),
    race("Connecticut", "CT", "gov", DEM, "LAMONT +11.0%", "Ned Lamont (D) holds a comfortable lead. No Senate seat on the 2026 ballot.", True),
    race("Delaware", "DE", "senate", DEM, "COONS +16.0%", "Chris Coons (D) is a strong favorite for a third term.", True),
    race("Florida", "FL", "senate", GOP, "MOODY +8.0%", "Special election: Ashley Moody (R) defends the Rubio seat.", True),
    race("Florida", "FL", "gov", GOP, "DONALDS +5.8%", "Byron Donalds (R) vs. David Jolly (D) for open governor."),
    race("Georgia", "GA", "senate", TOSS, "OSSOFF +1.0%", "Jon Ossoff (D) defends a Trump-won state.", True),
    race("Georgia", "GA", "gov", TOSS, "BOTTOMS +1.1%", "Keisha Lance Bottoms (D) vs. Rick Jackson (R) for open governor."),
    race("Hawaii", "HI", "gov", DEM, "GREEN +22.0%", "Josh Green (D) is strongly favored. No Senate seat on the 2026 ballot.", True),
    race("Idaho", "ID", "senate", GOP, "RISH +22.0%", "Jim Risch (R) is a heavy favorite.", True),
    race("Idaho", "ID", "gov", GOP, "LITTLE +22.0%", "Brad Little (R) remains strongly favored."),
    race("Illinois", "IL", "senate", DEM, "DURBIN OPEN +9.0%", "Open Class 2 seat after Dick Durbin retirement; Democratic baseline is strong.", True),
    race("Illinois", "IL", "gov", DEM, "PRITZKER +9.5%", "JB Pritzker (D) leads the Republican field."),
    race("Indiana", "IN", "house", GOP, "GOP +12.0%", "No Senate seat on the 2026 ballot. House baseline remains Republican.", True),
    race("Iowa", "IA", "senate", GOP, "OPEN +3.5%", "Open seat after Joni Ernst retirement. Competitive but still GOP-leaning.", True),
    race("Iowa", "IA", "gov", GOP, "OPEN +4.0%", "Open governor race after Kim Reynolds declined another term."),
    race("Kansas", "KS", "senate", GOP, "MARSHALL +7.0%", "Roger Marshall (R) starts with a Republican lean.", True),
    race("Kansas", "KS", "gov", TOSS, "TOSS-UP +0.5%", "Open governor race after Laura Kelly is term-limited."),
    race("Kentucky", "KY", "senate", GOP, "BARR +14.0%", "Andy Barr (R) vs. Charles Booker (D) for the McConnell seat.", True),
    race("Louisiana", "LA", "senate", GOP, "CASSIDY +12.0%", "Bill Cassidy (R) is favored in the jungle primary / runoff system.", True),
    race("Maine", "ME", "senate", TOSS, "TOSS-UP +1.0%", "Susan Collins (R) in a state Democrats usually carry statewide.", True),
    race("Maryland", "MD", "gov", DEM, "MOORE +18.5%", "Wes Moore (D) is strongly favored. No Senate seat on the 2026 ballot.", True),
    race("Massachusetts", "MA", "senate", DEM, "MARKEY +16.0%", "Ed Markey (D) is a strong favorite for the Class 2 seat.", True),
    race("Massachusetts", "MA", "gov", DEM, "HEALEY +16.0%", "Maura Healey (D) holds a commanding margin."),
    race("Michigan", "MI", "senate", TOSS, "EL-SAYED +1.8%", "Open seat after Gary Peters retired. Abdul El-Sayed (D) vs. Mike Rogers (R).", True),
    race("Minnesota", "MN", "senate", DEM, "SMITH +6.0%", "Tina Smith (D) is favored in this Class 2 seat.", True),
    race("Minnesota", "MN", "gov", DEM, "WALZ +5.5%", "Tim Walz (D) leads the Republican field."),
    race("Mississippi", "MS", "senate", GOP, "HYDE-SMITH +15.0%", "Cindy Hyde-Smith (R) is a heavy favorite.", True),
    race("Missouri", "MO", "house", GOP, "GOP +12.5%", "No Senate seat on the 2026 ballot. House baseline remains Republican.", True),
    race("Montana", "MT", "senate", GOP, "DAINES +6.0%", "Steve Daines (R) defends the Class 2 seat. Sheehy holds the other seat until 2030.", True),
    race("Nebraska", "NE", "senate", GOP, "RICKETTS +14.0%", "Pete Ricketts (R) is strongly favored.", True),
    race("Nebraska", "NE", "gov", GOP, "PILLEN +14.0%", "Jim Pillen (R) holds a wide lead."),
    race("Nevada", "NV", "gov", TOSS, "LOMBARDO +0.8%", "Joe Lombardo (R) vs. the Democratic nominee. No Senate seat on the 2026 ballot.", True),
    race("New Hampshire", "NH", "senate", DEM, "OPEN +3.4%", "Open seat after Jeanne Shaheen retired. Democratic nominee starts narrowly ahead.", True),
    race("New Jersey", "NJ", "senate", DEM, "BOOKER +7.0%", "Cory Booker (D) is favored in this Class 2 seat.", True),
    race("New Mexico", "NM", "senate", DEM, "LUJAN +6.8%", "Ben Ray Lujan (D) vs. Larry Marker (R).", True),
    race("New York", "NY", "gov", DEM, "HOCHUL +7.2%", "Kathy Hochul (D) leads. No Senate seat on the 2026 ballot.", True),
    race("North Carolina", "NC", "senate", TOSS, "COOPER +2.1%", "Open GOP seat: Roy Cooper (D) vs. Michael Whatley (R).", True),
    race("North Dakota", "ND", "house", GOP, "GOP +20.0%", "No Senate seat on the 2026 ballot (Cramer is Class 1, next up in 2030).", True),
    race("Ohio", "OH", "senate", GOP, "HUSTED +4.5%", "Special election: appointed Sen. Jon Husted (R) vs. the Democratic nominee.", True),
    race("Oklahoma", "OK", "senate", GOP, "LANKFORD +16.0%", "James Lankford (R) is a heavy favorite.", True),
    race("Oklahoma", "OK", "gov", GOP, "OPEN +16.0%", "Open governor race after Kevin Stitt is term-limited."),
    race("Oregon", "OR", "senate", DEM, "MERKLEY +8.0%", "Jeff Merkley (D) is favored in this Class 2 seat.", True),
    race("Oregon", "OR", "gov", DEM, "KOTEK +4.5%", "Tina Kotek (D) vs. the Republican nominee."),
    race("Pennsylvania", "PA", "gov", DEM, "SHAPIRO +8.4%", "Josh Shapiro (D) is favored. No Senate seat on the 2026 ballot.", True),
    race("Rhode Island", "RI", "senate", DEM, "REED +12.0%", "Jack Reed (D) is a strong favorite.", True),
    race("Rhode Island", "RI", "gov", DEM, "MCKEE +12.0%", "Dan McKee (D) holds a solid lead."),
    race("South Carolina", "SC", "senate", GOP, "GRAHAM +10.0%", "Lindsey Graham (R) is favored in this Class 2 seat.", True),
    race("South Carolina", "SC", "gov", GOP, "OPEN +14.0%", "Open governor race after Henry McMaster is term-limited."),
    race("South Dakota", "SD", "senate", GOP, "ROUNDS +18.0%", "Mike Rounds (R) is a heavy favorite.", True),
    race("Tennessee", "TN", "senate", GOP, "HAGERTY +16.0%", "Bill Hagerty (R) is a heavy favorite.", True),
    race("Tennessee", "TN", "gov", GOP, "OPEN +16.0%", "Open governor race after Bill Lee is term-limited."),
    race("Texas", "TX", "senate", GOP, "PAXTON +4.2%", "Ken Paxton (R) vs. James Talarico (D) after the GOP primary.", True),
    race("Utah", "UT", "house", GOP, "GOP +18.0%", "No Senate seat on the 2026 ballot. House baseline remains Republican.", True),
    race("Vermont", "VT", "gov", GOP, "SCOTT +24.0%", "Phil Scott (R) remains broadly popular. No Senate seat on the 2026 ballot.", True),
    race("Virginia", "VA", "senate", DEM, "WARNER +7.2%", "Mark Warner (D) leads the Republican challenger.", True),
    race("Washington", "WA", "house", DEM, "DEM +10.0%", "No Senate seat on the 2026 ballot. House baseline remains Democratic.", True),
    race("West Virginia", "WV", "senate", GOP, "CAPITO +18.0%", "Shelley Moore Capito (R) defends the Class 2 seat. Justice holds the other seat until 2030.", True),
    race("Wisconsin", "WI", "gov", TOSS, "EVERS +1.2%", "Tony Evers (D) vs. the GOP nominee. No Senate seat on the 2026 ballot.", True),
    race("Wyoming", "WY", "senate", GOP, "LUMMIS +25.0%", "Cynthia Lummis (R) is a heavy favorite.", True),
    race("Wyoming", "WY", "gov", GOP, "OPEN +25.0%", "Open governor race after Mark Gordon is term-limited."),
]


def main():
    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "updatedLabel": "Editorial snapshot · 1 Sep 2026",
        "disclaimer": "Independent project. Not affiliated with Decision Desk HQ.",
        "senate": {
            "currentDem": 47,
            "currentGop": 53,
            "neededForDemMajority": 4,
            "seatsUp": 35,
            "gopSeatsUp": 22,
            "demSeatsUp": 13,
            "watch": ["Alaska", "Maine", "Michigan", "Georgia", "North Carolina", "Ohio", "Texas", "Iowa"],
        },
        "house": {
            "dem": 48.2,
            "gop": 41.8,
            "note": "Generic ballot snapshot, not a seat projection. ~D+6.",
        },
        "races": RACES,
    }
    with open("polls.json", "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(f"Wrote polls.json with {len(RACES)} races.")


if __name__ == "__main__":
    main()
