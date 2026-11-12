from pathlib import Path

import pytest

from src import eda

DATA = Path(__file__).resolve().parents[1] / "data" / "parking_occupancy.csv"


@pytest.fixture(scope="module")
def df():
    return eda.load(DATA)


def test_dataset_covers_nine_lots_and_four_weeks(df):
    assert df["lot_code"].nunique() == 9
    assert (df["timestamp"].max() - df["timestamp"].min()).days == 27


def test_capacity_is_constant_per_lot(df):
    assert (df.groupby("lot_code")["lot_capacity"].nunique() == 1).all()


def test_rate_matches_occupancy_over_capacity(df):
    calc = 100 * df["lot_occupancy"] / df["lot_capacity"]
    assert (calc - df["occupancy_rate"]).abs().max() < 0.01


def test_lot_summary_ranks_lot02_busiest_and_lot04_quietest(df):
    summary = eda.lot_summary(df)
    assert summary.index[0] == "Lot02"
    assert summary.index[-1] == "Lot04"


def test_weekdays_busier_than_weekends(df):
    days = eda.day_summary(df)["median"]
    assert days[["Tuesday", "Wednesday", "Thursday"]].min() > days[["Saturday", "Sunday"]].max()


def test_run_writes_figures(tmp_path):
    summary = eda.run(DATA, tmp_path)
    assert summary["lots"] == 9
    assert (tmp_path / "figures" / "lot_hour_heatmap.png").exists()
