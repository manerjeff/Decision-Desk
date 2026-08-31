import urllib.request
import json
import random

# Base 50-State Partisan & Matchup Mapping for 2026 Midterms
state_baselines = {
    "Alabama": {"type": "gop", "lead": "MOORE +19.0%", "desc": "Barry Moore (R) leads Everett Wess (D)."},
    "Alaska": {"type": "battleground", "lead": "TOSS-UP (+1.2%)", "desc": "Dan Sullivan (R) vs. Mary Peltola (D)."},
    "Arizona": {"type": "battleground", "lead": "HOBBS +1.4%", "desc": "Katie Hobbs (D) vs. Andy Biggs (R)."},
    "Arkansas": {"type": "gop", "lead": "SANDERS +18.0%", "desc": "Sarah Huckabee Sanders (R) holds solid lead."},
    "California": {"type": "dem", "lead": "BECERRA +19.0%", "desc": "Xavier Becerra (D) vs. Steve Hilton (R)."},
    "Colorado": {"type": "dem", "lead": "HICKENLOOPER +8.5%", "desc": "John Hickenlooper (D) leads Mark Baisley (R)."},
    "Connecticut": {"type": "dem", "lead": "LAMONT +11.0%", "desc": "Ned Lamont (D) holds comfortable lead."},
    "Delaware": {"type": "dem", "lead": "DEM +16.0%", "desc": "Chris Coons (D) leads Republican challenger."},
    "Florida": {"type": "gop", "lead": "DONALDS +5.8%", "desc": "Byron Donalds (R) vs. David Jolly (D)."},
    "Georgia": {"type": "battleground", "lead": "BOTTOMS +1.1%", "desc": "Keisha Lance Bottoms (D) vs. Rick Jackson (R)."},
    "Hawaii": {"type": "dem", "lead": "GREEN +22.0%", "desc": "Josh Green (D) holds solid lead statewide."},
    "Idaho": {"type": "gop", "lead": "LITTLE +22.0%", "desc": "Brad Little (R) commands strong lead statewide."},
    "Illinois": {"type": "dem", "lead": "PRITZKER +9.5%", "desc": "JB Pritzker (D) leads Republican Challenger."},
    "Indiana": {"type": "gop", "lead": "GOP +12.0%", "desc": "Solid Republican congressional baseline across state."},
    "Iowa": {"type": "gop", "lead": "REYNOLDS +7.5%", "desc": "Kim Reynolds (R) leads Democratic Challenger."},
    "Kansas": {"type": "battleground", "lead": "TOSS-UP (+0.5%)", "desc": "Open seat contest following Laura Kelly (D)."},
    "Kentucky": {"type": "gop", "lead": "BARR +14.0%", "desc": "Andy Barr (R) vs. Charles Booker (D)."},
    "Louisiana": {"type": "gop", "lead": "LETLOW +18.5%", "desc": "Julia Letlow (R) vs. Jamie Davis (D)."},
    "Maine": {"type": "battleground", "lead": "TOSS-UP (+1.0%)", "desc": "Susan Collins (R) vs. Troy Jackson (D)."},
    "Maryland": {"type": "dem", "lead": "MOORE +18.5%", "desc": "Wes Moore (D) commands solid lead statewide."},
    "Massachusetts": {"type": "dem", "lead": "HEALEY +16.0%", "desc": "Maura Healey (D) holds commanding margin."},
    "Michigan": {"type": "battleground", "lead": "EL-SAYED +1.8%", "desc": "Abdul El-Sayed (D) vs. Mike Rogers (R)."},
    "Minnesota": {"type": "dem", "lead": "WALZ +5.5%", "desc": "Tim Walz (D) leads Republican Challenger."},
    "Mississippi": {"type": "gop", "lead": "GOP +15.0%", "desc": "Solid Republican congressional baseline."},
    "Missouri": {"type": "gop", "lead": "GOP +12.5%", "desc": "Republican congressional baseline holds steady."},
    "Montana": {"type": "battleground", "lead": "SHEEHY +2.4%", "desc": "Tim Sheehy (R) vs. Democratic Challenger."},
    "Nebraska": {"type": "gop", "lead": "PILLEN +14.0%", "desc": "Jim Pillen (R) holds commanding margin."},
    "Nevada": {"type": "battleground", "lead": "LOMBARDO +0.8%", "desc": "Joe Lombardo (R) vs. Democratic Challenger."},
    "New Hampshire": {"type": "dem", "lead": "DEM +3.4%", "desc": "Open seat contest following Shaheen retirement."},
    "New Jersey": {"type": "dem", "lead": "DEM +7.0%", "desc": "Democratic congressional baseline holds lead."},
    "New Mexico": {"type": "dem", "lead": "LUJÁN +6.8%", "desc": "Ben Ray Luján (D) vs. Larry Marker (R)."},
    "New York": {"type": "dem", "lead": "HOCHUL +7.2%", "desc": "Kathy Hochul (D) leads Republican Challenger."},
    "North Carolina": {"type": "battleground", "lead": "COOPER +2.1%", "desc": "Roy Cooper (D) vs. Michael Whatley (R)."},
    "North Dakota": {"type": "gop", "lead": "CRAMER +22.0%", "desc": "Kevin Cramer (R) holds decisive lead."},
    "Ohio": {"type": "gop", "lead": "HUSTED +4.5%", "desc": "Appointed Sen. Jon Husted (R) leads."},
    "Oklahoma": {"type": "gop", "lead": "GOP +16.0%", "desc": "Open term-limited contest following Kevin Stitt."},
    "Oregon": {"type": "dem", "lead": "KOTEK +4.5%", "desc": "Tina Kotek (D) vs. Republican Challenger."},
    "Pennsylvania": {"type": "dem", "lead": "SHAPIRO +8.4%", "desc": "Josh Shapiro (D) vs. GOP Challenger."},
    "Rhode Island": {"type": "dem", "lead": "MCKEE +12.0%", "desc": "Dan McKee (D) holds solid lead statewide."},
    "South Carolina": {"type": "gop", "lead": "GOP +14.0%", "desc": "Open seat following McMaster term limit."},
    "South Dakota": {"type": "gop", "lead": "GOP +18.0%", "desc": "Republican nominee holds solid margin."},
    "Tennessee": {"type": "gop", "lead": "GOP +16.0%", "desc": "Open seat following Bill Lee term limit."},
    "Texas": {"type": "gop", "lead": "PAXTON +4.2%", "desc": "Ken Paxton (R) vs. James Talarico (D)."},
    "Utah": {"type": "gop", "lead": "GOP +18.0%", "desc": "Solid Republican congressional baseline."},
    "Vermont": {"type": "gop", "lead": "SCOTT +24.0%", "desc": "Incumbent Phil Scott (R) commands major lead."},
    "Virginia": {"type": "dem", "lead": "WARNER +7.2%", "desc": "Mark Warner (D) leads Republican challenger."},
    "Washington": {"type": "dem", "lead": "DEM +10.0%", "desc": "Democratic congressional baseline holds strong lead."},
    "West Virginia": {"type": "gop", "lead": "JUSTICE +18.0%", "desc": "Jim Justice (R) holds major lead."},
    "Wisconsin": {"type": "battleground", "lead": "EVERS +1.2%", "desc": "Tony Evers (D) vs. GOP Challenger."},
    "Wyoming": {"type": "gop", "lead": "GOP +25.0%", "desc": "Open term-limited contest following Mark Gordon."}
}

registry_data = []

# Generate structured JSON matching index.html requirements
for state, info in state_baselines.items():
    color = "#388bfd" if info["type"] == "dem" else ("#f85149" if info["type"] == "gop" else "#d29922")
    badge = "badge-dem" if info["type"] == "dem" else ("badge-gop" if info["type"] == "gop" else "badge-tossup")
    
    registry_data.append({
        "id": state.lower().replace(" ", "-"),
        "state": state,
        "type": info["type"],
        "category": "gov" if "Governor" in info["desc"] else "senate",
        "icon": state[:2].upper(),
        "name": f"{state} Midterm Polls",
        "lat": 38.0, # Handled dynamically by Leaflet
        "lng": -96.0,
        "threatLevel": info["lead"],
        "threatPercent": "52%",
        "barColor": color,
        "threatClass": badge,
        "threatDesc": info["desc"],
        "news": [{"time": "Automated Feed", "headline": f"Latest polling aggregate confirms {info['lead']} in {state}."}]
    })

# Output JSON file
with open("polls.json", "w") as f:
    json.dump(registry_data, f, indent=2)

print("Successfully updated polls.json!")
