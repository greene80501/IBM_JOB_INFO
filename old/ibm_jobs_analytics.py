#!/usr/bin/env python3
"""
IBM early-career job analytics and visualization script.

Reads IBM jobs CSV data, infers U.S. states for each posting, and writes
summary CSVs + charts (including a U.S. state tile map).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Set

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")


STATE_ABBR_TO_NAME: Dict[str, str] = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}

# Fallback map for IBM location_summary city names in this dataset.
CITY_TO_STATE_FALLBACK: Dict[str, str] = {
    "ARMONK": "NY",
    "AUSTIN": "TX",
    "BATON ROUGE": "LA",
    "BELLEVUE": "WA",
    "BUFFALO": "NY",
    "COLUMBIA": "SC",
    "CAMBRIDGE": "MA",
    "CHICAGO": "IL",
    "HOPEWELL JUNCTION": "NY",
    "HERNDON": "VA",
    "LANSING": "MI",
    "MONROE": "LA",
    "NEW YORK": "NY",
    "POUGHKEEPSIE": "NY",
    "RESEARCH TRIANGLE PARK": "NC",
    "ROCHESTER": "MN",
    "ROCKET CENTER": "WV",
    "SAN JOSE": "CA",
    "TUCSON": "AZ",
    "UNIVERSITY PARK": "IL",
    "WASHINGTON": "DC",
    "YORKTOWN HEIGHTS": "NY",
}

# State tile grid coordinates (x, y), compact U.S. cartogram style.
STATE_TILE_POS = {
    "WA": (0, 0), "MT": (1, 0), "ND": (2, 0), "MN": (3, 0), "WI": (4, 0), "MI": (5, 0), "VT": (8, 0), "ME": (9, 0),
    "OR": (0, 1), "ID": (1, 1), "SD": (2, 1), "IA": (3, 1), "IL": (4, 1), "IN": (5, 1), "NY": (7, 1), "NH": (8, 1), "MA": (9, 1),
    "CA": (0, 2), "NV": (1, 2), "WY": (2, 2), "NE": (3, 2), "MO": (4, 2), "KY": (5, 2), "WV": (6, 2), "PA": (7, 2), "NJ": (8, 2), "CT": (9, 2), "RI": (10, 2),
    "AZ": (1, 3), "UT": (2, 3), "CO": (3, 3), "KS": (4, 3), "AR": (5, 3), "TN": (6, 3), "VA": (7, 3), "MD": (8, 3), "DE": (9, 3),
    "NM": (2, 4), "OK": (4, 4), "LA": (5, 4), "MS": (6, 4), "AL": (7, 4), "NC": (8, 4), "SC": (9, 4),
    "TX": (3, 5), "HI": (0, 5), "AK": (1, 5), "FL": (9, 5), "GA": (8, 5),
    "DC": (10, 3),
}

LOCATION_PATTERN = re.compile(r"\b([A-Z][A-Za-z .&\-/]+),\s*([A-Z]{2})\b")


def infer_states_for_row(row: pd.Series) -> List[str]:
    states: Set[str] = set()

    text_cols = [
        "title",
        "official_title",
        "location_summary",
        "intro",
        "responsibilities",
        "extra_content",
    ]
    full_text = "\n".join(str(row.get(c, "") or "") for c in text_cols)

    # 1) Direct City, ST matches from text.
    for _, state in LOCATION_PATTERN.findall(full_text):
        if state in STATE_ABBR_TO_NAME:
            states.add(state)

    # 2) Fallback using location_summary city.
    loc = str(row.get("location_summary", "") or "").strip()
    if loc and loc != "Multiple Cities":
        city = loc.split(",")[0].strip().upper()
        if city in CITY_TO_STATE_FALLBACK:
            states.add(CITY_TO_STATE_FALLBACK[city])

    # 3) Fallback for explicit Washington, DC office phrasing.
    if re.search(r"\bWashington,\s*DC\b", full_text, flags=re.IGNORECASE):
        states.add("DC")

    return sorted(states)


def prepare_dataframe(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["inferred_states"] = df.apply(infer_states_for_row, axis=1)
    df["inferred_state_count"] = df["inferred_states"].apply(len)
    df["inferred_states_str"] = df["inferred_states"].apply(lambda x: ",".join(x))
    return df


def state_counts(df: pd.DataFrame) -> pd.DataFrame:
    exploded = df.explode("inferred_states")
    exploded = exploded[exploded["inferred_states"].notna() & (exploded["inferred_states"] != "")]
    counts = (
        exploded.groupby("inferred_states", as_index=False)
        .agg(job_count=("id", "nunique"))
        .rename(columns={"inferred_states": "state_abbr"})
    )
    counts["state_name"] = counts["state_abbr"].map(STATE_ABBR_TO_NAME)
    return counts.sort_values("job_count", ascending=False).reset_index(drop=True)


def save_summary(df: pd.DataFrame, counts: pd.DataFrame, out_dir: Path) -> None:
    total_jobs = len(df)
    with_states = int((df["inferred_state_count"] > 0).sum())
    multi_state = int((df["inferred_state_count"] > 1).sum())

    lines = [
        "IBM Jobs Analytics Summary",
        "==========================",
        f"Total jobs: {total_jobs}",
        f"Jobs with inferred U.S. states: {with_states}",
        f"Jobs mapped to multiple U.S. states: {multi_state}",
        "",
        "Top states by job count:",
    ]

    for _, r in counts.head(15).iterrows():
        lines.append(f"- {r['state_abbr']} ({r['state_name']}): {int(r['job_count'])}")

    (out_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")


def plot_state_bar(counts: pd.DataFrame, out_dir: Path) -> None:
    top = counts.head(15).copy()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=top, x="state_abbr", y="job_count", hue="state_abbr", palette="Blues_r", legend=False)
    plt.title("IBM Early-Career Jobs by U.S. State (Top 15)")
    plt.xlabel("State")
    plt.ylabel("Job Count")
    plt.tight_layout()
    plt.savefig(out_dir / "jobs_by_state_top15.png", dpi=180)
    plt.close()


def plot_category_bar(df: pd.DataFrame, out_dir: Path) -> None:
    cat = (
        df.groupby("category", as_index=False)
        .agg(job_count=("id", "nunique"))
        .sort_values("job_count", ascending=False)
    )
    plt.figure(figsize=(12, 7))
    plot_df = cat.head(12).copy()
    sns.barplot(data=plot_df, x="job_count", y="category", hue="category", palette="viridis", legend=False)
    plt.title("IBM Early-Career Jobs by Category")
    plt.xlabel("Job Count")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(out_dir / "jobs_by_category.png", dpi=180)
    plt.close()
    cat.to_csv(out_dir / "jobs_by_category.csv", index=False)


def plot_us_tile_map(counts: pd.DataFrame, out_dir: Path) -> None:
    count_map = {r["state_abbr"]: int(r["job_count"]) for _, r in counts.iterrows()}
    vmax = max(count_map.values()) if count_map else 1

    fig, ax = plt.subplots(figsize=(14, 8))
    cmap = plt.cm.Blues

    for st, (x, y) in STATE_TILE_POS.items():
        v = count_map.get(st, 0)
        color = cmap(v / vmax if vmax else 0)
        rect = plt.Rectangle((x, -y), 0.95, 0.95, facecolor=color, edgecolor="white", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 0.12, -y + 0.68, st, fontsize=8, color="black", fontweight="bold")
        ax.text(x + 0.12, -y + 0.22, str(v), fontsize=8, color="black")

    ax.set_xlim(-0.3, 11.2)
    ax.set_ylim(-6.4, 1.2)
    ax.axis("off")
    ax.set_title("IBM Early-Career Jobs by U.S. State (Tile Map)", fontsize=16, pad=12)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=vmax))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.026, pad=0.02)
    cbar.set_label("Job count")

    plt.tight_layout()
    plt.savefig(out_dir / "jobs_us_tile_map.png", dpi=220)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze IBM jobs CSV and produce U.S.-focused visualizations.")
    parser.add_argument("--csv", default="ibm_jobs.csv", help="Input CSV path (default: ibm_jobs.csv)")
    parser.add_argument(
        "--output-dir",
        default="ibm_jobs_current",
        help="Output folder for current analytics artifacts (default: ibm_jobs_current)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")
    df = prepare_dataframe(csv_path)
    counts = state_counts(df)

    df.to_csv(out_dir / "parsed_jobs_with_states.csv", index=False)
    counts.to_csv(out_dir / "jobs_by_state.csv", index=False)
    save_summary(df, counts, out_dir)
    plot_state_bar(counts, out_dir)
    plot_category_bar(df, out_dir)
    plot_us_tile_map(counts, out_dir)

    print(f"Input CSV: {csv_path}")
    print(f"Output folder: {out_dir}")
    print(f"Jobs analyzed: {len(df)}")
    print(f"States with jobs: {counts['state_abbr'].nunique()}")
    if not counts.empty:
        top = counts.head(5)
        print("Top states:")
        for _, r in top.iterrows():
            print(f"  {r['state_abbr']}: {int(r['job_count'])}")


if __name__ == "__main__":
    main()
