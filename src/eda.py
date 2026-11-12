"""Exploratory analysis of parking occupancy across nine lots.

Usage:
    python src/eda.py --data data/parking_occupancy.csv --out reports
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
NAVY, GOLD, TEAL = "#1f4e79", "#c9a227", "#2a9d8f"


def load(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = pd.Categorical(df["day"], categories=DAY_ORDER, ordered=True)
    df["over_capacity"] = df["lot_occupancy"] > df["lot_capacity"]
    return df


def lot_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("lot_code")
    out = pd.DataFrame(
        {
            "capacity": g["lot_capacity"].first(),
            "readings": g.size(),
            "mean_rate": g["occupancy_rate"].mean(),
            "median_rate": g["occupancy_rate"].median(),
            "p90_rate": g["occupancy_rate"].quantile(0.9),
            "share_of_readings_over_90pct": g["occupancy_rate"].apply(lambda s: (s >= 90).mean() * 100),
        }
    )
    return out.round(1).sort_values("mean_rate", ascending=False)


def day_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("day", observed=True)["occupancy_rate"]
        .agg(["mean", "median", "std"])
        .round(1)
    )


def peak_hours(df: pd.DataFrame) -> pd.Series:
    """Mean occupancy rate by hour across all lots."""
    return df.groupby("hour")["occupancy_rate"].mean().round(1)


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_day_boxplot(df: pd.DataFrame, out: Path) -> Path:
    data = [df.loc[df["day"] == d, "occupancy_rate"] for d in DAY_ORDER]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot(data, tick_labels=DAY_ORDER, patch_artist=True,
               boxprops={"facecolor": "#d6e4f0"}, medianprops={"color": NAVY, "lw": 2})
    ax.set(title="Occupancy rate by day of week (all lots)", ylabel="Occupancy rate (%)")
    return _save(fig, out / "occupancy_by_day_boxplot.png")


def plot_lot_boxplot(df: pd.DataFrame, out: Path) -> Path:
    lots = sorted(df["lot_code"].unique())
    data = [df.loc[df["lot_code"] == lot, "occupancy_rate"] for lot in lots]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot(data, tick_labels=lots, patch_artist=True,
               boxprops={"facecolor": "#d6e4f0"}, medianprops={"color": NAVY, "lw": 2})
    ax.axhline(90, color=GOLD, ls="--", lw=1.5, label="90% (effectively full)")
    ax.set(title="Occupancy rate by lot", ylabel="Occupancy rate (%)")
    ax.legend()
    return _save(fig, out / "occupancy_by_lot_boxplot.png")


def plot_lot_scatter(df: pd.DataFrame, lot: str, out: Path) -> Path:
    sub = df[df["lot_code"] == lot]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.scatter(sub["timestamp"], sub["occupancy_rate"], s=10, color=NAVY, alpha=0.7)
    ax.axhline(sub["occupancy_rate"].mean(), color=GOLD, lw=2, label=f"Mean {sub['occupancy_rate'].mean():.0f}%")
    cap = int(sub["lot_capacity"].iloc[0])
    ax.set(title=f"{lot} occupancy over the study period (capacity {cap})", ylabel="Occupancy rate (%)")
    ax.legend()
    fig.autofmt_xdate()
    return _save(fig, out / f"{lot.lower()}_scatter.png")


def plot_heatmap(df: pd.DataFrame, out: Path) -> Path:
    pivot = df.pivot_table(index="lot_code", columns="hour", values="occupancy_rate", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(range(pivot.shape[1]), [f"{h}:00" for h in pivot.columns], rotation=45)
    ax.set_yticks(range(pivot.shape[0]), pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label="Mean occupancy rate (%)")
    ax.set_title("Mean occupancy by lot and hour")
    return _save(fig, out / "lot_hour_heatmap.png")


def run(data: str | Path, out: str | Path) -> dict:
    out = Path(out)
    figs = out / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    df = load(data)

    lots = lot_summary(df)
    days = day_summary(df)
    hours = peak_hours(df)
    lots.to_csv(out / "lot_summary.csv")
    days.to_csv(out / "day_summary.csv")
    hours.to_csv(out / "hourly_profile.csv")

    plot_day_boxplot(df, figs)
    plot_lot_boxplot(df, figs)
    plot_heatmap(df, figs)
    for lot in ("Lot02", "Lot04"):
        plot_lot_scatter(df, lot, figs)

    return {
        "readings": len(df),
        "lots": df["lot_code"].nunique(),
        "start": str(df["timestamp"].min()),
        "end": str(df["timestamp"].max()),
        "busiest_lot": lots.index[0],
        "quietest_lot": lots.index[-1],
        "peak_hour": int(hours.idxmax()),
        "over_capacity_readings": int(df["over_capacity"].sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", default="data/parking_occupancy.csv")
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()
    for key, value in run(args.data, args.out).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
