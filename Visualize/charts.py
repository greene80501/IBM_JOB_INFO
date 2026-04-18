from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import re

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud

from _viz_common import (
    CITY_COORDS,
    KEYWORDS,
    explode_cities,
    explode_states,
    herfindahl_index,
    load_jobs,
    output_path,
    state_to_abbrev,
)

sns.set_theme(style="whitegrid")


def _save_fig(name: str):
    path = output_path(f"{name}.png")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def _save_html(fig, name: str):
    path = output_path(f"{name}.html")
    fig.write_html(path)
    return path


def _save_csv(df: pd.DataFrame, name: str):
    path = output_path(f"{name}.csv")
    df.to_csv(path, index=False)
    return path


def _semantic_frame(df: pd.DataFrame):
    text = df["text_for_nlp"].fillna(df["title"])
    vec = TfidfVectorizer(stop_words="english", max_features=1800)
    X = vec.fit_transform(text)

    n = len(df)
    n_clusters = max(3, min(8, int(np.sqrt(max(n, 1)))))
    n_clusters = min(n_clusters, max(2, n - 1)) if n > 2 else 2

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster = km.fit_predict(X)

    if n >= 6:
        svd_dims = max(2, min(50, X.shape[1] - 1))
        svd = TruncatedSVD(n_components=svd_dims, random_state=42)
        X_reduced = svd.fit_transform(X)
        perplexity = max(3, min(20, n // 4))
        tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity, init="pca", learning_rate="auto")
        coords = tsne.fit_transform(X_reduced)
    else:
        coords = np.column_stack([np.arange(n), np.zeros(n)])

    out = df.copy()
    out["cluster"] = cluster
    out["x"] = coords[:, 0]
    out["y"] = coords[:, 1]
    return out, X


def _topic_frame(df: pd.DataFrame):
    text = df["text_for_nlp"].fillna(df["title"])
    vec = CountVectorizer(stop_words="english", max_features=1000, min_df=2, max_df=0.95)
    X = vec.fit_transform(text)
    n_topics = max(2, min(6, len(df) // 30 + 2))
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    doc_topic = lda.fit_transform(X)
    dominant = doc_topic.argmax(axis=1)
    return vec, lda, doc_topic, dominant


def jobs_by_city_bar_chart():
    df = explode_cities(load_jobs())
    s = df["city"].value_counts().sort_values(ascending=False)
    plt.figure(figsize=(12, 6))
    sns.barplot(x=s.index, y=s.values, color="#2E86AB")
    plt.xticks(rotation=60, ha="right")
    plt.title("IBM Job Postings by City")
    plt.ylabel("Openings")
    _save_csv(s.rename_axis("city").reset_index(name="count"), "01_jobs_by_city_bar_chart_data")
    return _save_fig("01_jobs_by_city_bar_chart")


def jobs_by_state_bar_chart():
    df = explode_states(load_jobs())
    s = df["state"].value_counts().sort_values(ascending=False)
    plt.figure(figsize=(12, 6))
    sns.barplot(x=s.index, y=s.values, color="#F18F01")
    plt.xticks(rotation=50, ha="right")
    plt.title("IBM Hiring Volume by State")
    plt.ylabel("Openings")
    _save_csv(s.rename_axis("state").reset_index(name="count"), "02_jobs_by_state_bar_chart_data")
    return _save_fig("02_jobs_by_state_bar_chart")


def us_bubble_map():
    df = explode_cities(load_jobs())
    city_counts = df[df["city"].isin(CITY_COORDS)].groupby("city").size().reset_index(name="openings")
    city_counts["lat"] = city_counts["city"].map(lambda c: CITY_COORDS[c][0])
    city_counts["lon"] = city_counts["city"].map(lambda c: CITY_COORDS[c][1])
    fig = px.scatter_geo(
        city_counts,
        lat="lat",
        lon="lon",
        size="openings",
        hover_name="city",
        color="openings",
        scope="usa",
        title="US Bubble Map of IBM Openings by City",
        size_max=35,
    )
    _save_csv(city_counts, "03_us_bubble_map_data")
    return _save_html(fig, "03_us_bubble_map")


def state_choropleth_map():
    df = explode_states(load_jobs())
    state_counts = df.groupby("state").size().reset_index(name="openings")
    state_counts["abbr"] = state_counts["state"].map(state_to_abbrev)
    state_counts = state_counts.dropna(subset=["abbr"])
    fig = px.choropleth(
        state_counts,
        locations="abbr",
        locationmode="USA-states",
        color="openings",
        scope="usa",
        hover_name="state",
        title="IBM Openings by State (Choropleth)",
        color_continuous_scale="Blues",
    )
    _save_csv(state_counts, "04_state_choropleth_map_data")
    return _save_html(fig, "04_state_choropleth_map")


def top_20_cities_ranked_chart():
    df = explode_cities(load_jobs())
    s = df["city"].value_counts().head(20)
    plt.figure(figsize=(10, 7))
    sns.barplot(x=s.values, y=s.index, color="#3D9970")
    plt.title("Top 20 IBM Hiring Cities")
    plt.xlabel("Openings")
    _save_csv(s.rename_axis("city").reset_index(name="count"), "05_top_20_cities_ranked_chart_data")
    return _save_fig("05_top_20_cities_ranked_chart")


def multiple_cities_vs_named_cities_donut_chart():
    df = load_jobs()
    counts = pd.Series(
        {
            "Multiple/Flexible": int(df["is_multiple_cities"].sum()),
            "Named Single City": int((~df["is_multiple_cities"]).sum()),
        }
    )
    plt.figure(figsize=(6, 6))
    plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%", wedgeprops={"width": 0.45})
    plt.title("Flexible vs City-Pinned Roles")
    _save_csv(counts.rename_axis("segment").reset_index(name="count"), "06_multiple_cities_vs_named_cities_donut_chart_data")
    return _save_fig("06_multiple_cities_vs_named_cities_donut_chart")


def city_by_team_stacked_bar_chart():
    df = explode_cities(load_jobs())
    pivot = pd.crosstab(df["city"], df["team"])
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).head(15).index]
    pivot.plot(kind="bar", stacked=True, figsize=(14, 7), colormap="tab20")
    plt.title("City by Team Composition")
    plt.xlabel("City")
    plt.ylabel("Openings")
    plt.xticks(rotation=50, ha="right")
    _save_csv(pivot.reset_index(), "07_city_by_team_stacked_bar_chart_data")
    return _save_fig("07_city_by_team_stacked_bar_chart")


def city_by_job_type_heatmap():
    df = explode_cities(load_jobs())
    pivot = pd.crosstab(df["city"], df["job_type_norm"])
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).head(20).index]
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt="d")
    plt.title("City by Job Type Heatmap")
    _save_csv(pivot.reset_index(), "08_city_by_job_type_heatmap_data")
    return _save_fig("08_city_by_job_type_heatmap")


def geographic_concentration_index_chart():
    df = explode_cities(load_jobs())
    counts = df["city"].value_counts()
    shares = counts / counts.sum()
    hhi = herfindahl_index(counts.values)
    top5 = shares.head(5).sum()
    metrics = pd.DataFrame({"metric": ["HHI", "Top 5 City Share"], "value": [hhi, top5]})

    plt.figure(figsize=(7, 5))
    sns.barplot(data=metrics, x="metric", y="value", hue="metric", dodge=False, palette=["#0074D9", "#FF851B"])
    plt.legend([], [], frameon=False)
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    plt.ylim(0, 1)
    plt.title("Geographic Concentration Index")
    _save_csv(metrics, "09_geographic_concentration_index_chart_data")
    return _save_fig("09_geographic_concentration_index_chart")


def location_diversity_score_by_city():
    df = explode_cities(load_jobs())
    g = df.groupby("city").agg(
        unique_teams=("team", "nunique"),
        unique_types=("job_type_norm", "nunique"),
        openings=("job_id", "count"),
    )
    g["diversity_score"] = g["unique_teams"] + g["unique_types"]
    g = g.sort_values("diversity_score", ascending=False).head(20)
    plt.figure(figsize=(10, 7))
    sns.barplot(x=g["diversity_score"], y=g.index, color="#2ECC40")
    plt.title("Location Diversity Score by City")
    plt.xlabel("Unique Teams + Unique Job Types")
    _save_csv(g.reset_index(), "10_location_diversity_score_by_city_data")
    return _save_fig("10_location_diversity_score_by_city")


def jobs_by_team_horizontal_bar_chart():
    df = load_jobs()
    s = df["team"].value_counts().sort_values()
    plt.figure(figsize=(10, 6))
    sns.barplot(x=s.values, y=s.index, color="#39CCCC")
    plt.title("Jobs by Team")
    plt.xlabel("Openings")
    _save_csv(s.rename_axis("team").reset_index(name="count"), "11_jobs_by_team_horizontal_bar_chart_data")
    return _save_fig("11_jobs_by_team_horizontal_bar_chart")


def share_of_total_jobs_by_team_donut_chart():
    df = load_jobs()
    s = df["team"].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(s.values, labels=s.index, autopct="%1.1f%%", wedgeprops={"width": 0.45})
    plt.title("Share of Total Jobs by Team")
    _save_csv(s.rename_axis("team").reset_index(name="count"), "12_share_of_total_jobs_by_team_donut_chart_data")
    return _save_fig("12_share_of_total_jobs_by_team_donut_chart")


def team_by_job_type_stacked_bar_chart():
    df = load_jobs()
    pivot = pd.crosstab(df["team"], df["job_type_norm"])
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    pivot.plot(kind="bar", stacked=True, figsize=(12, 7), colormap="Set2")
    plt.title("Team by Job Type")
    plt.ylabel("Openings")
    plt.xticks(rotation=45, ha="right")
    _save_csv(pivot.reset_index(), "13_team_by_job_type_stacked_bar_chart_data")
    return _save_fig("13_team_by_job_type_stacked_bar_chart")


def team_by_city_heatmap():
    df = explode_cities(load_jobs())
    pivot = pd.crosstab(df["team"], df["city"])
    top_cities = pivot.sum(axis=0).sort_values(ascending=False).head(20).index
    pivot = pivot[top_cities]
    plt.figure(figsize=(13, 7))
    sns.heatmap(pivot, cmap="rocket_r", annot=False)
    plt.title("Team by City Heatmap")
    _save_csv(pivot.reset_index(), "14_team_by_city_heatmap_data")
    return _save_fig("14_team_by_city_heatmap")


def top_teams_by_unique_job_titles():
    df = load_jobs()
    s = df.groupby("team")["title"].nunique().sort_values(ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(x=s.values, y=s.index, color="#B10DC9")
    plt.title("Top Teams by Number of Unique Job Titles")
    plt.xlabel("Unique Titles")
    _save_csv(s.rename("unique_titles").reset_index(), "15_top_teams_by_number_of_unique_job_titles_data")
    return _save_fig("15_top_teams_by_number_of_unique_job_titles")


def treemap_team_to_count():
    df = load_jobs()
    counts = df.groupby("team").size().reset_index(name="count")
    fig = px.treemap(counts, path=["team"], values="count", title="Treemap: Team -> Count")
    _save_csv(counts, "16_treemap_of_team_to_count_data")
    return _save_html(fig, "16_treemap_of_team_to_count")


def treemap_team_to_title_cluster_to_count():
    df, _ = _semantic_frame(load_jobs())
    counts = df.groupby(["team", "cluster"]).size().reset_index(name="count")
    counts["cluster"] = counts["cluster"].map(lambda x: f"Cluster {x}")
    fig = px.treemap(
        counts, path=["team", "cluster"], values="count", title="Treemap: Team -> Title Cluster -> Count"
    )
    _save_csv(counts, "17_treemap_of_team_to_title_cluster_to_count_data")
    return _save_html(fig, "17_treemap_of_team_to_title_cluster_to_count")


def ranked_slope_chart_team_share_across_time_periods():
    df = load_jobs().sort_values("scraped_at").reset_index(drop=True)
    split = max(1, len(df) // 2)
    df["period"] = np.where(df.index < split, "Period A", "Period B")
    counts = df.groupby(["period", "team"]).size().reset_index(name="count")
    counts["share"] = counts["count"] / counts.groupby("period")["count"].transform("sum")
    pivot = counts.pivot(index="team", columns="period", values="share").fillna(0)
    pivot = pivot.sort_values("Period B", ascending=False)

    plt.figure(figsize=(10, 7))
    for team, row in pivot.iterrows():
        plt.plot([0, 1], [row.get("Period A", 0), row.get("Period B", 0)], marker="o", alpha=0.8)
        plt.text(1.02, row.get("Period B", 0), team, fontsize=8, va="center")
    plt.xlim(-0.1, 1.35)
    plt.xticks([0, 1], ["Period A", "Period B"])
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    plt.title("Ranked Slope Chart: Team Share Across Snapshot Halves")
    _save_csv(pivot.reset_index(), "18_ranked_slope_chart_comparing_team_share_across_time_periods_data")
    return _save_fig("18_ranked_slope_chart_comparing_team_share_across_time_periods")


def hiring_diversity_score_by_team():
    df = explode_cities(load_jobs())
    g = df.groupby("team").agg(
        unique_cities=("city", "nunique"),
        unique_types=("job_type_norm", "nunique"),
        openings=("job_id", "count"),
    )
    g["score"] = g["unique_cities"] + g["unique_types"]
    g = g.sort_values("score", ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(x=g["score"], y=g.index, color="#FF4136")
    plt.title("Hiring Diversity Score by Team")
    plt.xlabel("Unique Cities + Unique Job Types")
    _save_csv(g.reset_index(), "19_hiring_diversity_score_by_team_data")
    return _save_fig("19_hiring_diversity_score_by_team")


def team_concentration_scatter_plot():
    df = explode_cities(load_jobs())
    g = df.groupby("team").agg(openings=("job_id", "count"), locations=("city", "nunique"))
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=g, x="openings", y="locations", s=120)
    for team, row in g.iterrows():
        plt.text(row["openings"] + 0.05, row["locations"] + 0.03, team, fontsize=8)
    plt.title("Team Concentration: Openings vs Number of Locations")
    _save_csv(g.reset_index(), "20_team_concentration_scatter_plot_data")
    return _save_fig("20_team_concentration_scatter_plot")


def jobs_by_type_bar_chart():
    df = load_jobs()
    s = df["job_type_norm"].value_counts().sort_values(ascending=False)
    plt.figure(figsize=(8, 5))
    sns.barplot(x=s.index, y=s.values, color="#0074D9")
    plt.title("Jobs by Type")
    plt.ylabel("Openings")
    _save_csv(s.rename_axis("job_type").reset_index(name="count"), "21_jobs_by_type_bar_chart_data")
    return _save_fig("21_jobs_by_type_bar_chart")


def job_type_share_by_city_stacked_bar_chart():
    df = explode_cities(load_jobs())
    pivot = pd.crosstab(df["city"], df["job_type_norm"], normalize="index")
    pivot = pivot.loc[df["city"].value_counts().head(15).index]
    pivot.plot(kind="bar", stacked=True, figsize=(12, 7), colormap="Pastel1")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    plt.title("Job Type Share by City")
    plt.xticks(rotation=50, ha="right")
    _save_csv(pivot.reset_index(), "22_job_type_share_by_city_stacked_bar_chart_data")
    return _save_fig("22_job_type_share_by_city_stacked_bar_chart")


def job_type_share_by_team_heatmap():
    df = load_jobs()
    pivot = pd.crosstab(df["team"], df["job_type_norm"], normalize="index")
    plt.figure(figsize=(9, 6))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="mako")
    plt.title("Job Type Share by Team")
    _save_csv(pivot.reset_index(), "23_job_type_share_by_team_heatmap_data")
    return _save_fig("23_job_type_share_by_team_heatmap")


def seniority_distribution_chart():
    df = load_jobs()
    s = df["seniority"].value_counts().sort_values(ascending=False)
    plt.figure(figsize=(8, 5))
    sns.barplot(x=s.index, y=s.values, color="#FF851B")
    plt.title("Seniority Distribution")
    plt.ylabel("Openings")
    _save_csv(s.rename_axis("seniority").reset_index(name="count"), "24_seniority_distribution_chart_data")
    return _save_fig("24_seniority_distribution_chart")


def role_family_distribution_chart():
    df = load_jobs()
    s = df["role_family"].value_counts().sort_values(ascending=False)
    plt.figure(figsize=(9, 5))
    sns.barplot(x=s.index, y=s.values, color="#2ECC40")
    plt.title("Role Family Distribution")
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("Openings")
    _save_csv(s.rename_axis("role_family").reset_index(name="count"), "25_role_family_distribution_chart_data")
    return _save_fig("25_role_family_distribution_chart")


def role_family_by_team_matrix():
    df = load_jobs()
    pivot = pd.crosstab(df["team"], df["role_family"])
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot, cmap="crest", annot=False)
    plt.title("Role Family by Team Matrix")
    _save_csv(pivot.reset_index(), "26_role_family_by_team_matrix_data")
    return _save_fig("26_role_family_by_team_matrix")


def role_family_by_city_stacked_bars():
    df = explode_cities(load_jobs())
    pivot = pd.crosstab(df["city"], df["role_family"])
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).head(15).index]
    pivot.plot(kind="bar", stacked=True, figsize=(12, 7), colormap="tab20c")
    plt.title("Role Family by City")
    plt.xticks(rotation=50, ha="right")
    _save_csv(pivot.reset_index(), "27_role_family_by_city_stacked_bars_data")
    return _save_fig("27_role_family_by_city_stacked_bars")


def openings_per_role_family_treemap():
    df = load_jobs()
    counts = df.groupby("role_family").size().reset_index(name="count")
    fig = px.treemap(counts, path=["role_family"], values="count", title="Openings per Role Family")
    _save_csv(counts, "28_openings_per_role_family_treemap_data")
    return _save_html(fig, "28_openings_per_role_family_treemap")


def manager_vs_individual_contributor_role_count():
    df = load_jobs()
    counts = pd.Series(
        {
            "Manager/Leadership": int(df["is_managerial"].sum()),
            "Individual Contributor": int((~df["is_managerial"]).sum()),
        }
    )
    plt.figure(figsize=(7, 5))
    sns.barplot(x=counts.index, y=counts.values, hue=counts.index, dodge=False, palette=["#FF4136", "#0074D9"])
    plt.legend([], [], frameon=False)
    plt.title("Manager vs Individual Contributor")
    plt.ylabel("Openings")
    _save_csv(counts.rename_axis("role_class").reset_index(name="count"), "29_manager_vs_individual_contributor_role_count_data")
    return _save_fig("29_manager_vs_individual_contributor_role_count")


def specialist_vs_generalist_role_chart():
    df = load_jobs()
    counts = pd.Series(
        {"Specialist": int(df["is_specialist"].sum()), "Generalist": int((~df["is_specialist"]).sum())}
    )
    plt.figure(figsize=(6, 6))
    plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%")
    plt.title("Specialist vs Generalist Roles")
    _save_csv(counts.rename_axis("role_class").reset_index(name="count"), "30_specialist_vs_generalist_role_chart_data")
    return _save_fig("30_specialist_vs_generalist_role_chart")


def top_title_words_bar_chart():
    df = load_jobs()
    c = Counter([tok for toks in df["title_tokens"] for tok in toks])
    s = pd.Series(dict(c.most_common(25)))
    plt.figure(figsize=(12, 6))
    sns.barplot(x=s.index, y=s.values, color="#85144b")
    plt.xticks(rotation=60, ha="right")
    plt.title("Top Title Words")
    plt.ylabel("Frequency")
    _save_csv(s.rename_axis("word").reset_index(name="count"), "31_top_title_words_bar_chart_data")
    return _save_fig("31_top_title_words_bar_chart")


def top_bigrams_in_titles_chart():
    df = load_jobs()
    bigrams = Counter()
    for toks in df["title_tokens"]:
        for i in range(len(toks) - 1):
            bigrams[f"{toks[i]} {toks[i + 1]}"] += 1
    s = pd.Series(dict(bigrams.most_common(20)))
    plt.figure(figsize=(12, 6))
    sns.barplot(x=s.index, y=s.values, color="#3D9970")
    plt.xticks(rotation=65, ha="right")
    plt.title("Top Bigrams in Titles")
    _save_csv(s.rename_axis("bigram").reset_index(name="count"), "32_top_bigrams_in_titles_chart_data")
    return _save_fig("32_top_bigrams_in_titles_chart")


def top_trigrams_in_titles_chart():
    df = load_jobs()
    trigrams = Counter()
    for toks in df["title_tokens"]:
        for i in range(len(toks) - 2):
            trigrams[f"{toks[i]} {toks[i + 1]} {toks[i + 2]}"] += 1
    s = pd.Series(dict(trigrams.most_common(20)))
    plt.figure(figsize=(12, 6))
    sns.barplot(x=s.index, y=s.values, color="#FF851B")
    plt.xticks(rotation=70, ha="right")
    plt.title("Top Trigrams in Titles")
    _save_csv(s.rename_axis("trigram").reset_index(name="count"), "33_top_trigrams_in_titles_chart_data")
    return _save_fig("33_top_trigrams_in_titles_chart")


def title_word_cloud():
    df = load_jobs()
    text = " ".join(df["title"].fillna(""))
    wc = WordCloud(width=1400, height=800, background_color="white", colormap="viridis").generate(text)
    plt.figure(figsize=(14, 7))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("Title Word Cloud")
    return _save_fig("34_title_word_cloud")


def title_length_distribution_histogram():
    df = load_jobs()
    plt.figure(figsize=(9, 5))
    sns.histplot(df["title_length_words"], bins=14, color="#0074D9")
    plt.title("Title Length Distribution")
    plt.xlabel("Words in Title")
    _save_csv(df[["title", "title_length_words"]], "35_title_length_distribution_histogram_data")
    return _save_fig("35_title_length_distribution_histogram")


def most_repeated_exact_titles_ranked_table():
    df = load_jobs()
    counts = df["title"].value_counts().rename_axis("title").reset_index(name="count")
    top = counts.head(20)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.axis("off")
    table = ax.table(cellText=top.values, colLabels=top.columns, loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    plt.title("Most Repeated Exact Titles (Top 20)")
    _save_csv(top, "36_most_repeated_exact_titles_ranked_table_data")
    return _save_fig("36_most_repeated_exact_titles_ranked_table")


def title_uniqueness_score_by_team():
    df = load_jobs()
    g = df.groupby("team").agg(total=("title", "count"), unique=("title", "nunique"))
    g["uniqueness_score"] = g["unique"] / g["total"]
    g = g.sort_values("uniqueness_score", ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(x=g["uniqueness_score"], y=g.index, color="#39CCCC")
    plt.gca().xaxis.set_major_formatter(PercentFormatter(1.0))
    plt.title("Title Uniqueness Score by Team")
    _save_csv(g.reset_index(), "37_title_uniqueness_score_by_team_data")
    return _save_fig("37_title_uniqueness_score_by_team")


def keyword_frequency_by_team_heatmap():
    df = load_jobs()
    mat = []
    for team, part in df.groupby("team"):
        text = " ".join((part["title"] + " " + part["description"]).fillna(""))
        row = {"team": team}
        lo = text.lower()
        for k in KEYWORDS:
            row[k] = lo.count(k)
        mat.append(row)
    mdf = pd.DataFrame(mat).set_index("team")
    plt.figure(figsize=(10, 6))
    sns.heatmap(mdf, cmap="YlOrRd", annot=True, fmt="d")
    plt.title("Keyword Frequency by Team")
    _save_csv(mdf.reset_index(), "38_keyword_frequency_by_team_heatmap_data")
    return _save_fig("38_keyword_frequency_by_team_heatmap")


def keyword_frequency_by_city_heatmap():
    df = explode_cities(load_jobs())
    mat = []
    for city, part in df.groupby("city"):
        text = " ".join((part["title"] + " " + part["description"]).fillna(""))
        row = {"city": city}
        lo = text.lower()
        for k in KEYWORDS:
            row[k] = lo.count(k)
        mat.append(row)
    mdf = pd.DataFrame(mat).set_index("city")
    mdf = mdf.loc[mdf.sum(axis=1).sort_values(ascending=False).head(20).index]
    plt.figure(figsize=(10, 8))
    sns.heatmap(mdf, cmap="PuBuGn", annot=True, fmt="d")
    plt.title("Keyword Frequency by City")
    _save_csv(mdf.reset_index(), "39_keyword_frequency_by_city_heatmap_data")
    return _save_fig("39_keyword_frequency_by_city_heatmap")


def title_complexity_index_chart():
    df = load_jobs()
    token_freq = Counter([tok for toks in df["title_tokens"] for tok in toks])

    def complexity(tokens):
        if not tokens:
            return 0.0
        avg_len = np.mean([len(t) for t in tokens])
        rare_share = np.mean([1 if token_freq[t] <= 2 else 0 for t in tokens])
        return len(tokens) + 0.6 * avg_len + 2.0 * rare_share

    df["title_complexity"] = df["title_tokens"].apply(complexity)
    g = df.groupby("team")["title_complexity"].mean().sort_values(ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(x=g.values, y=g.index, color="#FF4136")
    plt.title("Title Complexity Index by Team")
    _save_csv(df[["title", "team", "title_complexity"]], "40_title_complexity_index_chart_data")
    return _save_fig("40_title_complexity_index_chart")


def embedding_2d_map_of_job_titles():
    df, _ = _semantic_frame(load_jobs())
    plt.figure(figsize=(10, 7))
    sns.scatterplot(data=df, x="x", y="y", hue="cluster", palette="tab10", s=60)
    plt.title("2D Embedding Map of Job Titles")
    _save_csv(df[["job_id", "title", "team", "cluster", "x", "y"]], "41_2d_embedding_map_of_job_titles_data")
    return _save_fig("41_2d_embedding_map_of_job_titles")


def semantic_clusters_of_roles():
    df, _ = _semantic_frame(load_jobs())
    plt.figure(figsize=(11, 7))
    sns.scatterplot(data=df, x="x", y="y", hue="cluster", style="team", legend=False, s=65)
    plt.title("Semantic Clusters of Roles")
    _save_csv(df[["job_id", "title", "team", "cluster"]], "42_semantic_clusters_of_roles_data")
    return _save_fig("42_semantic_clusters_of_roles")


def cluster_size_bar_chart():
    df, _ = _semantic_frame(load_jobs())
    s = df["cluster"].value_counts().sort_index()
    plt.figure(figsize=(8, 5))
    sns.barplot(x=[f"Cluster {i}" for i in s.index], y=s.values, color="#0074D9")
    plt.title("Cluster Size")
    _save_csv(s.rename_axis("cluster").reset_index(name="count"), "43_cluster_size_bar_chart_data")
    return _save_fig("43_cluster_size_bar_chart")


def cluster_by_team_comparison_chart():
    df, _ = _semantic_frame(load_jobs())
    pivot = pd.crosstab(df["team"], df["cluster"], normalize="index")
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="magma")
    plt.title("Cluster by Team Comparison")
    _save_csv(pivot.reset_index(), "44_cluster_by_team_comparison_chart_data")
    return _save_fig("44_cluster_by_team_comparison_chart")


def cluster_by_city_comparison_chart():
    df, _ = _semantic_frame(explode_cities(load_jobs()))
    pivot = pd.crosstab(df["city"], df["cluster"], normalize="index")
    pivot = pivot.loc[df["city"].value_counts().head(15).index]
    plt.figure(figsize=(12, 7))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="viridis")
    plt.title("Cluster by City Comparison")
    _save_csv(pivot.reset_index(), "45_cluster_by_city_comparison_chart_data")
    return _save_fig("45_cluster_by_city_comparison_chart")


def similarity_network_graph_of_jobs():
    df = load_jobs().head(80).copy()
    vec = TfidfVectorizer(stop_words="english", max_features=1200)
    X = vec.fit_transform(df["text_for_nlp"])
    sim = cosine_similarity(X)

    graph = nx.Graph()
    for i, row in df.reset_index(drop=True).iterrows():
        graph.add_node(i, team=row["team"], title=row["title"])
    threshold = 0.27
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            if sim[i, j] >= threshold:
                graph.add_edge(i, j, weight=float(sim[i, j]))

    pos = nx.spring_layout(graph, k=0.5, iterations=80, seed=42)
    plt.figure(figsize=(13, 10))
    nx.draw_networkx_nodes(graph, pos, node_size=90, alpha=0.8)
    nx.draw_networkx_edges(graph, pos, alpha=0.2)
    plt.title("Similarity Network Graph of Jobs")
    plt.axis("off")

    edges = pd.DataFrame([{"source": u, "target": v, "weight": d["weight"]} for u, v, d in graph.edges(data=True)])
    _save_csv(edges, "46_similarity_network_graph_of_jobs_data")
    return _save_fig("46_similarity_network_graph_of_jobs")


def topic_model_visualization():
    df = load_jobs()
    vec, lda, _, _ = _topic_frame(df)
    words = np.array(vec.get_feature_names_out())

    rows = []
    for topic_idx, comp in enumerate(lda.components_):
        top_idx = comp.argsort()[-10:][::-1]
        for rank, idx in enumerate(top_idx, 1):
            rows.append({"topic": f"Topic {topic_idx}", "rank": rank, "word": words[idx], "weight": comp[idx]})
    out = pd.DataFrame(rows)

    plt.figure(figsize=(12, 7))
    sns.barplot(data=out, x="weight", y="word", hue="topic", dodge=False)
    plt.title("Topic Model Visualization (Top Words by Topic)")
    _save_csv(out, "47_topic_model_visualization_data")
    return _save_fig("47_topic_model_visualization")


def topic_prevalence_by_team():
    df = load_jobs()
    _, _, _, dominant = _topic_frame(df)
    df = df.copy()
    df["topic"] = dominant
    pivot = pd.crosstab(df["team"], df["topic"], normalize="index")
    plt.figure(figsize=(11, 6))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="Blues")
    plt.title("Topic Prevalence by Team")
    _save_csv(pivot.reset_index(), "48_topic_prevalence_by_team_data")
    return _save_fig("48_topic_prevalence_by_team")


def topic_prevalence_by_city():
    df = explode_cities(load_jobs())
    _, _, _, dominant = _topic_frame(df)
    df = df.copy()
    df["topic"] = dominant
    pivot = pd.crosstab(df["city"], df["topic"], normalize="index")
    pivot = pivot.loc[df["city"].value_counts().head(15).index]
    plt.figure(figsize=(11, 7))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu")
    plt.title("Topic Prevalence by City")
    _save_csv(pivot.reset_index(), "49_topic_prevalence_by_city_data")
    return _save_fig("49_topic_prevalence_by_city")


def semantic_overlap_heatmap_between_teams():
    df = load_jobs()
    vec = TfidfVectorizer(stop_words="english", max_features=1400)
    X = vec.fit_transform(df["text_for_nlp"])

    team_vectors = []
    teams = []
    for team, idx in df.groupby("team").groups.items():
        teams.append(team)
        team_vectors.append(np.asarray(X[list(idx)].mean(axis=0)).ravel())
    matrix = np.vstack(team_vectors)
    sim = cosine_similarity(matrix)
    sim_df = pd.DataFrame(sim, index=teams, columns=teams)

    plt.figure(figsize=(10, 8))
    sns.heatmap(sim_df, annot=True, fmt=".2f", cmap="coolwarm", vmin=0, vmax=1)
    plt.title("Semantic Overlap Heatmap Between Teams")
    _save_csv(sim_df.reset_index(), "50_semantic_overlap_heatmap_between_teams_data")
    return _save_fig("50_semantic_overlap_heatmap_between_teams")


def job_postings_over_time_chart():
    df = load_jobs().copy()
    df["posted_date"] = pd.to_datetime(df.get("date_posted"), format="%d-%b-%Y", errors="coerce")
    daily = (
        df.dropna(subset=["posted_date"])
        .groupby(df["posted_date"].dt.date)
        .size()
        .reset_index(name="count")
        .rename(columns={"posted_date": "date"})
    )
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    plt.figure(figsize=(12, 6))
    plt.bar(daily["date"], daily["count"], alpha=0.35, color="#1f77b4")
    plt.plot(daily["date"], daily["count"], marker="o", linewidth=2.2, color="#0b4f8a")
    plt.title("IBM Job Postings Over Time (By Date Posted)")
    plt.xlabel("Date Posted")
    plt.ylabel("Number of Postings")
    plt.xticks(rotation=35, ha="right")
    plt.grid(axis="y", alpha=0.25)

    _save_csv(daily, "51_job_postings_over_time_chart_data")
    return _save_fig("51_job_postings_over_time_chart")


def _posted_dates(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df.get("date_posted"), format="%d-%b-%Y", errors="coerce")


def _posting_window_days_from_description(text: str) -> int:
    if not text:
        return 15
    m = re.search(r"remain posted for\s+(\d+)\s+days", text, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 15


def active_postings_over_time_chart():
    df = load_jobs().copy()
    df["posted_date"] = _posted_dates(df)
    df = df.dropna(subset=["posted_date"]).copy()
    if df.empty:
        raise ValueError("No usable date_posted values found.")

    df["window_days"] = df["description"].fillna("").apply(_posting_window_days_from_description)
    df["end_date"] = df["posted_date"] + pd.to_timedelta(df["window_days"], unit="D")

    start = df["posted_date"].min().normalize()
    end = max(df["end_date"].max().normalize(), pd.Timestamp.today().normalize())
    timeline = pd.date_range(start=start, end=end, freq="D")

    counts = []
    for day in timeline:
        active = ((df["posted_date"] <= day) & (df["end_date"] >= day)).sum()
        counts.append(active)
    out = pd.DataFrame({"date": timeline, "active_postings": counts})

    plt.figure(figsize=(12, 6))
    plt.plot(out["date"], out["active_postings"], color="#0B4F8A", linewidth=2.4)
    plt.fill_between(out["date"], out["active_postings"], alpha=0.2, color="#1f77b4")
    plt.title("Estimated Active IBM Early-Career Postings Over Time")
    plt.xlabel("Date")
    plt.ylabel("Estimated Active Postings")
    plt.xticks(rotation=35, ha="right")
    plt.grid(axis="y", alpha=0.25)
    _save_csv(out, "52_active_postings_over_time_chart_data")
    return _save_fig("52_active_postings_over_time_chart")


def new_postings_last_7_14_days_by_team_chart():
    df = load_jobs().copy()
    df["posted_date"] = _posted_dates(df)
    df = df.dropna(subset=["posted_date"]).copy()
    today = pd.Timestamp.today().normalize()
    cutoff_7 = today - pd.Timedelta(days=7)
    cutoff_14 = today - pd.Timedelta(days=14)

    team_7 = df[df["posted_date"] >= cutoff_7].groupby("team").size().rename("last_7_days")
    team_14 = df[df["posted_date"] >= cutoff_14].groupby("team").size().rename("last_14_days")
    out = pd.concat([team_7, team_14], axis=1).fillna(0).astype(int).reset_index()
    out = out.sort_values("last_14_days", ascending=False)

    plot_df = out.head(12).melt(id_vars="team", value_vars=["last_7_days", "last_14_days"], var_name="window", value_name="count")
    plt.figure(figsize=(13, 6))
    sns.barplot(data=plot_df, x="team", y="count", hue="window", palette=["#1f77b4", "#79a7d3"])
    plt.title("New Postings by Team (Last 7 vs 14 Days)")
    plt.xlabel("Team")
    plt.ylabel("New Postings")
    plt.xticks(rotation=40, ha="right")
    _save_csv(out, "53_new_postings_last_7_14_days_by_team_chart_data")
    return _save_fig("53_new_postings_last_7_14_days_by_team_chart")


def internship_only_city_ranking_chart():
    df = load_jobs().copy()
    df = df[df["job_type_norm"].str.lower().eq("internship")]
    df = explode_cities(df)
    out = df.groupby("city").size().reset_index(name="internship_postings").sort_values("internship_postings", ascending=False)
    out = out[out["city"] != "No City"]

    top = out.head(20)
    plt.figure(figsize=(10, 7))
    sns.barplot(data=top, x="internship_postings", y="city", color="#2E8B57")
    plt.title("Internship-Only City Ranking")
    plt.xlabel("Internship Postings")
    plt.ylabel("City")
    _save_csv(out, "54_internship_only_city_ranking_chart_data")
    return _save_fig("54_internship_only_city_ranking_chart")


def required_education_by_role_family_chart():
    df = load_jobs().copy()
    edu = df.get("required_education", pd.Series(["Unknown"] * len(df))).fillna("Unknown").replace("", "Unknown")
    df["required_education_clean"] = edu
    pivot = pd.crosstab(df["role_family"], df["required_education_clean"], normalize="index")
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu")
    plt.title("Required Education by Role Family (Share)")
    _save_csv(pivot.reset_index(), "55_required_education_by_role_family_chart_data")
    return _save_fig("55_required_education_by_role_family_chart")


def new_since_last_run_ranked_table():
    df = load_jobs().copy()
    previous_path = Path(__file__).resolve().parent.parent / "data" / "ibm_jobs_previous.json"
    current_path = Path(__file__).resolve().parent.parent / "data" / "ibm_jobs.json"

    prev_ids = set()
    if previous_path.exists():
        try:
            prev_rows = json.loads(previous_path.read_text(encoding="utf-8"))
            prev_ids = {str(r.get("job_id")) for r in prev_rows if r.get("job_id")}
        except Exception:
            prev_ids = set()

    now_rows = json.loads(current_path.read_text(encoding="utf-8"))
    curr_ids = {str(r.get("job_id")) for r in now_rows if r.get("job_id")}
    new_ids = curr_ids - prev_ids if prev_ids else curr_ids

    df["job_id"] = df["job_id"].astype(str)
    new_df = df[df["job_id"].isin(new_ids)].copy()
    new_df["posted_date"] = _posted_dates(new_df)
    new_df = new_df.sort_values("posted_date", ascending=False)
    out = new_df[["job_id", "title", "team", "job_type_norm", "location_raw", "date_posted", "required_education", "detail_url"]].head(30)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")
    if out.empty:
        out = pd.DataFrame([{"message": "No new postings vs previous snapshot."}])
    table = ax.table(cellText=out.values, colLabels=out.columns, loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.45)
    plt.title("New Postings Since Last Run (Top 30)")

    # Update previous snapshot after generating report.
    previous_path.write_text(current_path.read_text(encoding="utf-8"), encoding="utf-8")

    _save_csv(out, "56_new_since_last_run_ranked_table_data")
    return _save_fig("56_new_since_last_run_ranked_table")
