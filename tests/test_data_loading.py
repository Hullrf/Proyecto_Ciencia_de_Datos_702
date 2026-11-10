"""Run with: python tests/test_data_loading.py"""
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.data_loading import MAPS_COLUMNS, clean_maps  # noqa: E402


def _row(match, map_, a, b, year=2021):
    return {"Tournament": "T", "Stage": "S", "Match Type": "M", "Match Name": match, "Map": map_,
            "Team A": "X ", "Team A Score": a, "Team B": "Y", "Team B Score": b, "Year": year}


def test_clean_maps():
    scores = pd.DataFrame([
        _row("late", "Bind", 13, 5),      # valid, higher id
        _row("early", "Haven", 7, 13),    # valid, lower id
        _row("dup", "Split", 13, 1),      # duplicated key -> ambiguous, dropped
        _row("dup", "Split", 2, 13),
        _row("tie", "Ascent", 12, 12),    # tie -> dropped
        _row("noid", "Icebox", 13, 3),    # no id -> dropped
        _row("short", "Breeze", 5, 2),    # unfinished (winner < 13) -> dropped
    ])
    ids = pd.DataFrame([
        {**{k: r[k] for k in ["Tournament", "Stage", "Match Type", "Match Name", "Map", "Year"]},
         "Match ID": m, "Game ID": g}
        for r, m, g in [(scores.iloc[0], 20, 200), (scores.iloc[1], 10, 100),
                        (scores.iloc[2], 30, 300), (scores.iloc[4], 40, 400),
                        (scores.iloc[6], 50, 500)]
    ])
    out = clean_maps(scores, ids)
    assert list(out.columns) == MAPS_COLUMNS
    assert out["game_id"].tolist() == [100, 200], out
    assert out["team_a_win"].tolist() == [0, 1]
    assert out["team_a"].tolist() == ["X", "X"]  # stripped
    assert out["game_id"].is_unique
    assert out["stage_block"].tolist() == [10, 10]  # same stage -> block = smallest match_id


if __name__ == "__main__":
    test_clean_maps()
    print("OK test_data_loading")
