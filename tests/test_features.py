"""Anti-leakage checks. Run with: python tests/test_features.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.features import DIFF_FEATURES, FEATURES, build_dataset, to_number  # noqa: E402

RAW_KEY = ["Tournament", "Stage", "Match Type", "Match Name", "Map", "Year"]
# (game_id, match_id, stage, team_a, team_b, map, score_a, score_b) - three stages, three teams
GAMES = [
    (1, 1, "S1", "X", "Y", "Bind", 13, 5), (2, 1, "S1", "X", "Y", "Haven", 9, 13),
    (3, 2, "S1", "Y", "Z", "Bind", 13, 11),
    (4, 3, "S2", "X", "Z", "Bind", 13, 2), (5, 3, "S2", "X", "Z", "Haven", 13, 10),
    (6, 4, "S2", "Y", "X", "Split", 6, 13),
    (7, 5, "S3", "X", "Y", "Bind", 13, 7), (8, 6, "S3", "Z", "Y", "Haven", 4, 13),
]
BLOCK = {"S1": 1, "S2": 3, "S3": 5}


def make_inputs(games=GAMES, flip_ab=False):
    maps = pd.DataFrame([{
        "game_id": g, "match_id": m, "stage_block": BLOCK[s], "year": 2021, "tournament": "T",
        "stage": s, "match_type": "R", "match_name": f"m{m}", "map": mp,
        "team_a": b if flip_ab else a, "team_b": a if flip_ab else b,
        "team_a_score": sb if flip_ab else sa, "team_b_score": sa if flip_ab else sb,
    } for g, m, s, a, b, mp, sa, sb in games])
    maps["team_a_win"] = (maps["team_a_score"] > maps["team_b_score"]).astype(int)

    def raw_key(row):
        return {"Tournament": "T", "Stage": row["stage"], "Match Type": "R",
                "Match Name": row["match_name"], "Map": row["map"], "Year": 2021}

    overview, eco, draft = [], [], []
    for _, row in maps.iterrows():
        if row["game_id"] == 3:      # one map without overview / eco / draft rows
            continue
        for team, score in [(row["team_a"], row["team_a_score"]), (row["team_b"], row["team_b_score"])]:
            for side in ["both", "attack"]:
                overview.append({**raw_key(row), "Team": team, "Side": side, "Rating": score / 10,
                                 "Average Combat Score": score * 15,
                                 "Average Damage Per Round": score * 10,
                                 "Kill, Assist, Trade, Survive %": f"{60 + score}%",
                                 "Kills - Deaths (FKD)": score - 8})
            eco.append({**raw_key(row), "Team": team, "Type": "Pistol Won", "Won": int(score >= 13)})
        draft.append({**{k: v for k, v in raw_key(row).items() if k != "Map"}, "Map": row["map"],
                      "Team": row["team_b"] if flip_ab else row["team_a"], "Action": "pick"})
    return maps, pd.DataFrame(overview), pd.DataFrame(eco), pd.DataFrame(draft)


def build(games=GAMES, flip_ab=False):
    return build_dataset(*make_inputs(games, flip_ab), window=3, seed=42).set_index("game_id")


def same(a, b):
    return np.allclose(a.to_numpy(float), b.to_numpy(float), equal_nan=True)


def test_no_leakage_from_own_stage():
    """Flipping every result of the last stage must not change any feature of that stage."""
    flipped = [g if g[2] != "S3" else (*g[:6], g[7], g[6]) for g in GAMES]
    base, changed = build(), build(flipped)
    assert same(base.loc[[7, 8], FEATURES], changed.loc[[7, 8], FEATURES])
    assert (base.loc[[7, 8], "team_a_win"] != changed.loc[[7, 8], "team_a_win"]).all()


def test_future_does_not_affect_past():
    base, truncated = build(), build(GAMES[:6])
    assert same(base.loc[truncated.index, FEATURES], truncated[FEATURES])


def test_first_stage_has_no_history():
    first = build().loc[[1, 2, 3]]
    assert (first["min_maps_played"] == 0).all()   # even maps 2 and 3: same stage is not history
    assert first["diff_winrate"].isna().all()
    assert (first["h2h_games"] == 0).all()


def test_known_values():
    """Game 7 (X vs Y, stage 3). Before S3: X won 4 of 5 maps, Y won 2 of 4."""
    row = build().loc[7]
    sign = 1 if row["team_a"] == "X" else -1
    assert np.isclose(row["diff_winrate"], sign * (4 / 5 - 2 / 4))
    assert row["diff_maps_played"] == sign * 1
    assert row["min_maps_played"] == 4
    assert row["h2h_games"] == 3                    # games 1, 2, 6
    x_h2h = 2 / 3                                   # X beat Y in games 1 and 6
    assert np.isclose(row["h2h_winrate_a"], x_h2h if sign == 1 else 1 - x_h2h)
    assert np.isclose(row["diff_winrate_map"], sign * (2 / 2 - 1 / 2))   # Bind: X 2/2, Y 1/2
    assert row["team_a_win"] == (1 if sign == 1 else 0)


def test_swap_symmetry():
    base, flipped = build(), build(flip_ab=True)
    assert same(base[DIFF_FEATURES + ["a_picked_map"]], -flipped[DIFF_FEATURES + ["a_picked_map"]])
    assert same(base["h2h_winrate_a"], 1 - flipped["h2h_winrate_a"])
    assert (base["team_a_win"] == 1 - flipped["team_a_win"]).all()
    assert same(base["min_maps_played"], flipped["min_maps_played"])


def test_missing_side_tables_keep_row():
    data = build()
    assert len(data) == len(GAMES)
    assert np.isnan(data.loc[3, "a_picked_map"])    # no draft for that match
    assert data.loc[8, FEATURES].notna().any()      # Z and Y still get history despite game 3 gap


def test_to_number():
    out = to_number(pd.Series(["81%", "", None, "1.5"]))
    assert out[0] == 81.0 and out[3] == 1.5 and out[1:3].isna().all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK", name)
