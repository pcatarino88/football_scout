from __future__ import annotations
import pandas as pd
from typing import Iterable, Optional
import re
from .data import get_df_scaled
from .market_value import cached_market_value

DEFAULT_EXTRA_COLS = ["Player","Nation","Age","League","Squad","Pos","Minutes"]

FEATURES_ALLOWED = [
    "goal_scoring",
    "goal_efficacy",
    "shooting",
    "passing_influence",
    "passing_accuracy",
    "goal_creation",
    "possession_influence",
    "progression",
    "take_ons",
    "aerial_influence",
    "defensive_influence",
    "discipline_and_consistency",
]

FEATURES_DEFAULT = ["goal_scoring","goal_efficacy","shooting"]

def top_players(
    df,
    *,
    pos=None,
    max_age=None,
    min_minutes=None,
    top_n=15,
    leagues=None,
    features=None,           # can be a list or dict
    extra_cols=None,         # if None we’ll use EXTRA_COLS_DEFAULT
    fetch_market_value=True,
    round_to=2,
):
    """
    Rank players with optional filters and feature-based scoring. Adds Transfermarkt market value for the top N players (cached) if fetch_market_value=True.
    """
    # ---- a) Get the data ----
    data = df.copy()

    # ---- filters ----
    mask = pd.Series(True, index=data.index)

    # Optional league filter
    if leagues:
        mask &= data["League"].isin(leagues)
    
    if pos is not None and "Pos" in data.columns:
        pos_list = [pos] if isinstance(pos, str) else list(pos)
        pattern = "|".join(map(re.escape, pos_list))          # substring match
        mask &= data["Pos"].astype(str).str.contains(pattern, case=False, na=False)

    if max_age is not None and "Age" in df.columns:
        mask &= pd.to_numeric(df["Age"], errors="coerce").le(max_age)

    if min_minutes is not None and "Minutes" in df.columns:
        mask &= pd.to_numeric(df["Minutes"], errors="coerce").ge(min_minutes)

    data = df.loc[mask].copy()

    # -------- features & score --------
    if features is None:
        feat_cols = FEATURES_DEFAULT[:]                
        weights = {c: 1.0 for c in feat_cols}
    elif isinstance(features, dict):
        weights = {c: float(w) for c, w in features.items()}
        feat_cols = list(weights.keys())
    else:  # list / tuple / set
        feat_cols = list(features)
        weights = {c: 1.0 for c in feat_cols}

    # keep only allowed + present columns, and cap to 12
    feat_cols = [c for c in feat_cols if c in FEATURES_ALLOWED and c in data.columns][:12]
    weights = {c: weights[c] for c in feat_cols}

    if not feat_cols:
        raise ValueError("No valid scoring features selected/found in dataset.")   
    
    X = data[feat_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    w = pd.Series(weights, index=feat_cols, dtype=float)
    if w.sum() != 0:
        w = w / w.sum()

    score_name = "SCORE"
    data[score_name] = (X * w).sum(axis=1).round(round_to)

    # ---- sort, cut to top N ----
    out = (
        data.sort_values(score_name, ascending=False)
            .head(top_n)
            .copy()
    )

    # ---- add Transfermarkt market value ----
    mv_col = "Market Value"
    if fetch_market_value and "Player" in out.columns:
        unique_names = out["Player"].astype(str).fillna("").unique().tolist()
        mv_map = {name: cached_market_value(name) if name else None for name in unique_names}
        out[mv_col] = out["Player"].map(mv_map)
        
    # ---- columns to show: defaults for extra cols + features + score ----
    if extra_cols is None:
        extra_cols = DEFAULT_EXTRA_COLS

    base_cols = [c for c in extra_cols if c in out.columns]
    feat_cols_present = [c for c in feat_cols if c in out.columns]
    
    # Ensure market value column is visible if we created it
    if mv_col in out.columns and mv_col not in base_cols:
        base_cols = base_cols + [mv_col]

    show_cols = ["Player"] + base_cols + feat_cols_present + [score_name]
    show_cols = list(dict.fromkeys(show_cols))  

    out = out.loc[:, show_cols].reset_index(drop=True)

    return out