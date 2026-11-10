"""Historical (pre-match) features for each map.

Leakage rule: a team's history for a map only includes maps from EARLIER stage blocks
(`stage_block`), never the map itself nor other maps of the same stage, because match IDs
do not order matches inside a stage (see notebook 01).
"""
import numpy as np
import pandas as pd

RAW_KEY = ["Tournament", "Stage", "Match Type", "Match Name", "Map", "Year"]
MAPS_KEY = ["tournament", "stage", "match_type", "match_name", "map", "year"]
ORDER = ["stage_block", "match_id", "game_id"]

PLAYER_STATS = {
    "rating": "Rating",
    "acs": "Average Combat Score",
    "adr": "Average Damage Per Round",
    "kast": "Kill, Assist, Trade, Survive %",
    "fkd": "Kills - Deaths (FKD)",
}
# per-map values whose historical mean becomes a feature
MEAN_STATS = ["won", "round_diff", *PLAYER_STATS, "pistol_won"]

DIFF_FEATURES = [
    "diff_winrate", "diff_winrate_recent", "diff_winrate_map", "diff_maps_played",
    "diff_maps_played_map", "diff_round_diff", "diff_rating", "diff_acs", "diff_adr",
    "diff_kast", "diff_fkd", "diff_pistol",
]
FEATURES = DIFF_FEATURES + ["h2h_winrate_a", "h2h_games", "a_picked_map", "min_maps_played"]


def to_number(s: pd.Series) -> pd.Series:
    """'81%' -> 81.0, '' / None -> NaN."""
    return pd.to_numeric(s.astype("string").str.rstrip("%"), errors="coerce").astype(float)


def team_map_stats(maps: pd.DataFrame, overview: pd.DataFrame, eco_stats: pd.DataFrame) -> pd.DataFrame:
    """Long table: two rows per map (one per team) with what each team did in that map."""
    base = maps[["game_id", "match_id", "stage_block", "map", "team_a_win"]]
    score_diff = maps["team_a_score"] - maps["team_b_score"]
    long = pd.concat([
        base.assign(side="a", team=maps["team_a"], opponent=maps["team_b"],
                    won=maps["team_a_win"], round_diff=score_diff),
        base.assign(side="b", team=maps["team_b"], opponent=maps["team_a"],
                    won=1 - maps["team_a_win"], round_diff=-score_diff),
    ]).drop(columns="team_a_win")

    game_ids = maps[MAPS_KEY + ["game_id"]].set_axis(RAW_KEY + ["game_id"], axis=1)

    players = overview[(overview["Side"] == "both") & (overview["Map"] != "All Maps")]
    players = players[RAW_KEY + ["Team"]].assign(
        **{name: to_number(players[col]) for name, col in PLAYER_STATS.items()})
    team_stats = (players.merge(game_ids, on=RAW_KEY)
                  .assign(team=lambda d: d["Team"].str.strip())
                  .groupby(["game_id", "team"])[list(PLAYER_STATS)].mean().reset_index())

    pistols = eco_stats[eco_stats["Type"] == "Pistol Won"]
    pistols = (pistols[RAW_KEY + ["Team"]].assign(pistol_won=to_number(pistols["Won"]))
               .merge(game_ids, on=RAW_KEY)
               .assign(team=lambda d: d["Team"].str.strip())
               .groupby(["game_id", "team"])["pistol_won"].mean().reset_index())

    long = long.merge(team_stats, on=["game_id", "team"], how="left")
    long = long.merge(pistols, on=["game_id", "team"], how="left")
    return long.sort_values(ORDER + ["side"]).reset_index(drop=True)


def _state_before_stage(long: pd.DataFrame, group: list[str], cols: list[str]) -> pd.DataFrame:
    """Value of running columns `cols` at the end of the previous stage block, per `group`."""
    state = long.groupby(group + ["stage_block"], sort=False)[cols].last().reset_index()
    state = state.sort_values("stage_block")
    state[cols] = state.groupby(group)[cols].shift(1)
    return state


def _picked_map(maps: pd.DataFrame, draft: pd.DataFrame) -> pd.Series:
    """1 if team A picked the map, -1 if team B did, 0 if nobody did (decider), NaN without draft."""
    match_key = MAPS_KEY[:4] + ["year"]
    draft = draft.rename(columns=dict(zip(RAW_KEY, MAPS_KEY)))
    picks = (draft[draft["Action"] == "pick"]
             .assign(picker=lambda d: d["Team"].str.strip())
             .drop_duplicates(MAPS_KEY)[MAPS_KEY + ["picker"]])
    has_draft = draft[match_key].drop_duplicates().assign(has_draft=True)
    merged = maps[MAPS_KEY + ["team_a", "team_b"]].merge(picks, on=MAPS_KEY, how="left") \
                                                   .merge(has_draft, on=match_key, how="left")
    picked = np.select([merged["picker"] == merged["team_a"], merged["picker"] == merged["team_b"]],
                       [1.0, -1.0], default=0.0)
    return pd.Series(np.where(merged["has_draft"].isna(), np.nan, picked), index=maps.index)


def build_dataset(maps: pd.DataFrame, overview: pd.DataFrame, eco_stats: pd.DataFrame,
                  draft: pd.DataFrame, window: int, seed: int) -> pd.DataFrame:
    """One row per map with pre-match features (team A minus team B) and the target."""
    maps = maps.sort_values(ORDER).reset_index(drop=True)
    long = team_map_stats(maps, overview, eco_stats)

    # ponytail: history is keyed by team name and ignores roster changes;
    # upgrade path is building history per player and aggregating the current lineup.
    by_team = long.groupby("team")
    running = pd.DataFrame({"team": long["team"], "stage_block": long["stage_block"]})
    running["n"] = by_team.cumcount() + 1
    for stat in MEAN_STATS:
        running[f"{stat}_sum"] = long[stat].fillna(0).groupby(long["team"]).cumsum()
        running[f"{stat}_n"] = long[stat].notna().groupby(long["team"]).cumsum()
    running["recent"] = by_team["won"].transform(lambda s: s.rolling(window, min_periods=1).mean())
    state_cols = [c for c in running.columns if c not in ("team", "stage_block")]
    team_state = _state_before_stage(running, ["team"], state_cols)

    prior = long[["game_id", "side", "team", "opponent", "map", "stage_block"]].merge(
        team_state, on=["team", "stage_block"], how="left")
    feats = prior[["game_id", "side"]].copy()
    feats["maps_played"] = prior["n"].fillna(0)
    for stat in MEAN_STATS:
        feats[stat] = prior[f"{stat}_sum"] / prior[f"{stat}_n"].where(prior[f"{stat}_n"] > 0)
    feats["recent"] = prior["recent"]

    # same idea, restricted to this map and to this opponent
    for name, group in [("map", ["team", "map"]), ("h2h", ["team", "opponent"])]:
        run = long[group + ["stage_block"]].copy()
        run["n"] = long.groupby(group).cumcount() + 1
        run["wins"] = long.groupby(group)["won"].cumsum()
        state = _state_before_stage(run, group, ["n", "wins"])
        merged = long[group + ["stage_block"]].merge(state, on=group + ["stage_block"], how="left")
        feats[f"{name}_n"] = merged["n"].fillna(0).to_numpy()
        feats[f"{name}_winrate"] = (merged["wins"] / merged["n"]).to_numpy()

    a = feats[feats["side"] == "a"].set_index("game_id")
    b = feats[feats["side"] == "b"].set_index("game_id")
    out = maps[["game_id", "match_id", "stage_block", "year", "map", "team_a", "team_b", "team_a_win"]].copy()
    ids = out["game_id"]

    def diff(col):
        return (a[col] - b[col]).reindex(ids).to_numpy()

    out["diff_winrate"] = diff("won")
    out["diff_winrate_recent"] = diff("recent")
    out["diff_winrate_map"] = diff("map_winrate")
    out["diff_maps_played"] = diff("maps_played")
    out["diff_maps_played_map"] = diff("map_n")
    out["diff_round_diff"] = diff("round_diff")
    for stat in PLAYER_STATS:
        out[f"diff_{stat}"] = diff(stat)
    out["diff_pistol"] = diff("pistol_won")
    out["h2h_winrate_a"] = a["h2h_winrate"].reindex(ids).to_numpy()
    out["h2h_games"] = a["h2h_n"].reindex(ids).to_numpy()
    out["a_picked_map"] = _picked_map(maps, draft).to_numpy()
    out["min_maps_played"] = np.minimum(a["maps_played"].reindex(ids).to_numpy(),
                                        b["maps_played"].reindex(ids).to_numpy())

    # Team A is usually the favourite (notebook 02): swap A and B in a random half of the rows
    swap = np.random.default_rng(seed).random(len(out)) < 0.5
    out.loc[swap, ["team_a", "team_b"]] = out.loc[swap, ["team_b", "team_a"]].to_numpy()
    out.loc[swap, DIFF_FEATURES + ["a_picked_map"]] *= -1
    out["a_picked_map"] += 0.0  # turn -0.0 into 0.0
    out.loc[swap, "h2h_winrate_a"] = 1 - out.loc[swap, "h2h_winrate_a"]
    out.loc[swap, "team_a_win"] = 1 - out.loc[swap, "team_a_win"]
    return out
