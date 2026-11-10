"""Loading raw VCT tables and building the clean base table of maps."""
import pandas as pd

from src.config import RAW_DIR, load_config

MATCH_KEY = ["Tournament", "Stage", "Match Type", "Match Name"]
MAP_KEY = MATCH_KEY + ["Map"]

MAPS_COLUMNS = [
    "game_id", "match_id", "stage_block", "year", "tournament", "stage", "match_type", "match_name",
    "map", "team_a", "team_b", "team_a_score", "team_b_score", "team_a_win",
]


def load_table(relative_path: str, years: list[int] | None = None) -> pd.DataFrame:
    """Read data/raw/vct_<year>/<relative_path> for every year and concatenate, adding `Year`."""
    years = years or load_config()["years"]
    frames = [
        pd.read_csv(RAW_DIR / f"vct_{year}" / relative_path, low_memory=False).assign(Year=year)
        for year in years
    ]
    return pd.concat(frames, ignore_index=True)


def load_ids() -> pd.DataFrame:
    """Match and game IDs for every map of every year."""
    return pd.read_csv(RAW_DIR / "all_ids" / "all_matches_games_ids.csv")


def clean_maps(scores: pd.DataFrame, ids: pd.DataFrame) -> pd.DataFrame:
    """Build the base table: one row per valid map, in chronological (ID) order.

    Drops ambiguous duplicated keys, maps without IDs, ties, unfinished maps (winner < 13)
    and showmatches. `stage_block` is the smallest match_id of the (tournament, stage) the map
    belongs to: IDs order stages reliably, but not matches inside a stage (bracket slots get
    their IDs before being played), so history must only look at earlier stage blocks.
    """
    key = MAP_KEY + ["Year"]
    scores = scores.drop_duplicates(key, keep=False)
    ids = ids.drop_duplicates(key, keep=False)[key + ["Match ID", "Game ID"]]
    df = scores.merge(ids, on=key, how="left")
    df = df.dropna(subset=["Match ID", "Game ID", "Team A Score", "Team B Score"])
    df = df[df["Team A Score"] != df["Team B Score"]]
    df = df[df[["Team A Score", "Team B Score"]].max(axis=1) >= 13]  # unfinished maps / forfeits
    df = df[df["Stage"] != "Showmatch"]
    out = pd.DataFrame({
        "game_id": df["Game ID"].astype(int),
        "match_id": df["Match ID"].astype(int),
        "year": df["Year"].astype(int),
        "tournament": df["Tournament"],
        "stage": df["Stage"],
        "match_type": df["Match Type"],
        "match_name": df["Match Name"],
        "map": df["Map"],
        "team_a": df["Team A"].str.strip(),
        "team_b": df["Team B"].str.strip(),
        "team_a_score": df["Team A Score"].astype(int),
        "team_b_score": df["Team B Score"].astype(int),
    })
    out["team_a_win"] = (out["team_a_score"] > out["team_b_score"]).astype(int)
    out["stage_block"] = out.groupby(["year", "tournament", "stage"])["match_id"].transform("min")
    return out.sort_values(["stage_block", "match_id", "game_id"]).reset_index(drop=True)[MAPS_COLUMNS]


def build_maps_table() -> pd.DataFrame:
    return clean_maps(load_table("matches/maps_scores.csv"), load_ids())
