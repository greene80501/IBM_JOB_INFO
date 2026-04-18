from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "ibm_jobs.json"
OUTPUT_DIR = BASE_DIR / "visualize_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

US_STATES = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}

CITY_COORDS = {
    "Armonk": (41.1265, -73.7140),
    "Atlanta": (33.7490, -84.3880),
    "Austin": (30.2672, -97.7431),
    "Baton Rouge": (30.4515, -91.1871),
    "Bellevue": (47.6101, -122.2015),
    "Boston": (42.3601, -71.0589),
    "Brookhaven": (33.8651, -84.3366),
    "Buffalo": (42.8864, -78.8784),
    "Cambridge": (42.3736, -71.1097),
    "Chicago": (41.8781, -87.6298),
    "Columbia": (39.2037, -76.8610),
    "Dallas": (32.7767, -96.7970),
    "Durham": (35.9940, -78.8986),
    "Herndon": (38.9696, -77.3861),
    "Hopewell Junction": (41.5620, -73.7949),
    "Houston": (29.7604, -95.3698),
    "Lansing": (42.7325, -84.5555),
    "Lowell": (42.6334, -71.3162),
    "Monroe": (32.5093, -92.1193),
    "New York": (40.7128, -74.0060),
    "Phoenix": (33.4484, -112.0740),
    "Poughkeepsie": (41.7004, -73.9210),
    "Raleigh": (35.7796, -78.6382),
    "Research Triangle Park": (35.9120, -78.7880),
    "Reston": (38.9586, -77.3570),
    "Rochester": (43.1566, -77.6088),
    "Rocket Center": (39.6093, -78.8073),
    "San Francisco": (37.7749, -122.4194),
    "San Jose": (37.3382, -121.8863),
    "Tucson": (32.2226, -110.9747),
    "University Park": (40.8077, -77.8606),
    "Washington": (38.9072, -77.0369),
    "Yorktown Heights": (41.2709, -73.7774),
}

STOP_WORDS = {
    "and",
    "or",
    "for",
    "to",
    "of",
    "the",
    "in",
    "with",
    "a",
    "an",
    "on",
    "at",
    "by",
    "ibm",
    "2026",
    "level",
    "entry",
    "intern",
    "internship",
    "associate",
    "co",
    "op",
}

KEYWORDS = [
    "cloud",
    "data",
    "ai",
    "security",
    "consulting",
    "client",
    "software",
    "infrastructure",
    "sales",
]


def load_jobs() -> pd.DataFrame:
    rows = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(rows)

    for col in ["title", "team", "type", "location_raw", "description"]:
        if col not in df.columns:
            df[col] = ""
    if "cities" not in df.columns:
        df["cities"] = [[] for _ in range(len(df))]

    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["team"] = df["team"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    df["type"] = df["type"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    df["location_raw"] = df["location_raw"].fillna("").astype(str).str.strip()
    df["description"] = df["description"].fillna("").astype(str)
    df["scraped_at"] = pd.to_datetime(df.get("scraped_at"), errors="coerce", utc=True)

    def norm_city_list(value):
        if isinstance(value, list):
            clean = [str(x).strip().title() for x in value if str(x).strip()]
            return clean
        return []

    df["city_list"] = df["cities"].apply(norm_city_list)
    empty_city_mask = df["city_list"].map(len) == 0
    df.loc[empty_city_mask, "city_list"] = df.loc[empty_city_mask, "location_raw"].apply(parse_location)
    empty_city_mask = df["city_list"].map(len) == 0
    df.loc[empty_city_mask, "city_list"] = [["No City"] for _ in range(empty_city_mask.sum())]

    df["state_list"] = df["location_raw"].apply(parse_states)
    df["is_multiple_cities"] = df["location_raw"].str.lower().eq("multiple cities") | (
        df["city_list"].map(len) > 1
    )
    df["job_type_norm"] = df["type"].apply(normalize_job_type)
    df["role_family"] = df["title"].apply(infer_role_family)
    df["seniority"] = df.apply(lambda r: infer_seniority(r["title"], r["job_type_norm"]), axis=1)
    df["is_managerial"] = df["title"].str.contains(
        r"\b(?:manager|director|lead|head|vp|chief)\b", case=False, regex=True
    )
    df["is_specialist"] = df["title"].str.contains(
        r"\b(?:ai|ml|sap|oracle|security|sre|site reliability|cloud|devops|quantum|cyber|hacker|middleware)\b",
        case=False,
        regex=True,
    )
    df["title_length_words"] = df["title"].str.split().str.len().fillna(0).astype(int)
    df["title_tokens"] = df["title"].apply(tokenize)
    df["text_for_nlp"] = df["title"].fillna("") + " " + df["description"].fillna("")
    return df


def parse_location(raw: str) -> list[str]:
    if not raw or raw.lower() == "multiple cities":
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return []

    if len(parts) >= 3 and parts[-1].lower() == "united states":
        candidates = parts[:-2]
        cities = [c.title() for c in candidates if c.lower() not in US_STATES]
        return cities or [candidates[0].title()]
    return [parts[0].title()]


def parse_states(raw: str) -> list[str]:
    if not raw:
        return []
    states = []
    for part in [p.strip().lower() for p in raw.split(",") if p.strip()]:
        if part in US_STATES:
            states.append(part.title())
    return sorted(set(states))


def normalize_job_type(value: str) -> str:
    txt = (value or "").lower()
    if "intern" in txt:
        return "Internship"
    if "co-op" in txt or "co op" in txt:
        return "Co-op"
    if "entry" in txt or "associate" in txt or "apprentice" in txt:
        return "Entry Level"
    if "experienced" in txt:
        return "Experienced"
    return value or "Unknown"


def infer_seniority(title: str, job_type: str) -> str:
    text = f"{title} {job_type}".lower()
    if any(k in text for k in ["intern", "co-op", "apprentice"]):
        return "Junior"
    if any(k in text for k in ["entry", "associate", "analyst"]):
        return "Junior"
    if any(k in text for k in ["senior", "sr", "principal", "staff"]):
        return "Senior"
    if any(k in text for k in ["manager", "director", "lead", "head", "vp", "chief"]):
        return "Leadership"
    return "Mid"


def infer_role_family(title: str) -> str:
    t = (title or "").lower()
    mapping = [
        (
            "Engineer",
            [
                "engineer",
                "developer",
                "sre",
                "devops",
                "full stack",
                "backend",
                "front end",
                "hardware",
            ],
        ),
        ("Data/AI", ["data", "ai", "ml", "analytics", "scientist"]),
        ("Consultant", ["consult", "package specialist"]),
        ("Sales", ["sales", "account", "client executive"]),
        ("Security", ["security", "hacker", "cyber"]),
        ("Product/PM", ["product", "project manager", "program manager", "technical project manager"]),
        ("Support/Operations", ["support", "operations", "technician", "admin"]),
        ("Research", ["research", "quantum"]),
        ("Design", ["design", "ux", "ui"]),
    ]
    for family, words in mapping:
        if any(w in t for w in words):
            return family
    return "Other"


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-/+]*", (text or "").lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


def explode_cities(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().explode("city_list", ignore_index=True).rename(columns={"city_list": "city"})
    out["city"] = out["city"].fillna("No City")
    return out


def explode_states(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().explode("state_list", ignore_index=True).rename(columns={"state_list": "state"})
    out = out.dropna(subset=["state"])
    return out


def state_to_abbrev(state_name: str) -> str | None:
    if not state_name:
        return None
    return US_STATES.get(state_name.lower())


def output_path(*parts: str) -> Path:
    path = OUTPUT_DIR.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def herfindahl_index(counts: Iterable[int]) -> float:
    arr = np.asarray(list(counts), dtype=float)
    if arr.sum() == 0:
        return 0.0
    shares = arr / arr.sum()
    return float(np.square(shares).sum())
