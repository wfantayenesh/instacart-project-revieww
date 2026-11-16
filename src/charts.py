"""
src/charts.py
=============
PURPOSE
-------
Generate 3 PNG charts from REAL cleaned data and save them to reports/.

Charts:
  1. Orders per Day of Week
  2. Orders per Hour of Day
  3. Distribution of days_since_prior_order  (excludes first orders / NaN)

Uses matplotlib with the 'Agg' backend so NO display window is needed.
This means it works on servers, Replit, and headless environments.

IMPORTANT: Never plot invented numbers.
           If the data is missing, a clear message is printed.
"""

import logging
import pathlib

# ── Set non-interactive backend BEFORE importing pyplot ───────────────────────
import matplotlib
matplotlib.use("Agg")   # must be called before pyplot import
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

REPORTS_DIR = pathlib.Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# Day-of-week labels (Instacart: 0 = Saturday or Sunday depending on dataset)
DOW_LABELS = ["Day 0", "Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6"]


def chart_orders_per_dow(orders_df) -> pathlib.Path:
    """
    Bar chart: how many orders were placed on each day of the week.
    X-axis = order_dow (0-6), Y-axis = order count.
    """
    import pandas as pd
    col = "order_dow"
    if col not in orders_df.columns:
        logger.warning("Column '%s' not found – skipping chart.", col)
        print(f"[charts] Column '{col}' not available – chart skipped.")
        return None

    counts = orders_df[col].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(counts.index, counts.values, color="steelblue", edgecolor="white")
    ax.bar_label(bars, fmt="{:,.0f}", fontsize=8, padding=3)
    ax.set_title("Orders per Day of Week", fontsize=14, fontweight="bold")
    ax.set_xlabel("Day of Week (0 = Saturday, 1 = Sunday, …)")
    ax.set_ylabel("Number of Orders")
    ax.set_xticks(counts.index)
    ax.set_xticklabels([f"Day {i}" for i in counts.index])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    plt.tight_layout()

    out = REPORTS_DIR / "chart_orders_per_dow.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Chart saved: %s", out)
    print(f"[charts] Saved: {out}")
    return out


def chart_orders_per_hour(orders_df) -> pathlib.Path:
    """
    Bar chart: how many orders were placed at each hour of the day.
    """
    col = "order_hour_of_day"
    if col not in orders_df.columns:
        logger.warning("Column '%s' not found – skipping chart.", col)
        print(f"[charts] Column '{col}' not available – chart skipped.")
        return None

    counts = orders_df[col].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(counts.index, counts.values, color="coral", edgecolor="white")
    ax.set_title("Orders per Hour of Day", fontsize=14, fontweight="bold")
    ax.set_xlabel("Hour of Day (0 = midnight, 23 = 11 PM)")
    ax.set_ylabel("Number of Orders")
    ax.set_xticks(range(0, 24))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    plt.tight_layout()

    out = REPORTS_DIR / "chart_orders_per_hour.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Chart saved: %s", out)
    print(f"[charts] Saved: {out}")
    return out


def chart_days_since_prior(orders_df) -> pathlib.Path:
    """
    Histogram: distribution of days_since_prior_order.
    NaN rows (first orders) are excluded because they have no prior order.
    """
    col = "days_since_prior_order"
    if col not in orders_df.columns:
        logger.warning("Column '%s' not found – skipping chart.", col)
        print(f"[charts] Column '{col}' not available – chart skipped.")
        return None

    valid = orders_df[col].dropna()

    if valid.empty:
        print("[charts] No valid days_since_prior_order data – chart skipped.")
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(valid, bins=31, range=(0, 30), color="mediumseagreen",
            edgecolor="white", rwidth=0.85)
    ax.set_title("Distribution of Days Since Prior Order\n(first orders excluded)",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Days Since Prior Order")
    ax.set_ylabel("Number of Orders")
    ax.set_xticks(range(0, 31))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    plt.tight_layout()

    out = REPORTS_DIR / "chart_days_since_prior.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Chart saved: %s", out)
    print(f"[charts] Saved: {out}")
    return out


def generate_all_charts(orders_df) -> list[pathlib.Path]:
    """
    Generate all three charts from the cleaned orders DataFrame.

    Parameters
    ----------
    orders_df : the cleaned orders DataFrame (from clean.clean_all()).

    Returns
    -------
    List of Path objects for the charts that were created.
    """
    if orders_df is None or orders_df.empty:
        print("[charts] orders DataFrame is empty – no charts generated.")
        return []

    results = []
    for fn in [chart_orders_per_dow, chart_orders_per_hour, chart_days_since_prior]:
        path = fn(orders_df)
        if path:
            results.append(path)

    print(f"\n[charts] {len(results)} chart(s) saved to reports/")
    return results
