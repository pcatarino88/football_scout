from __future__ import annotations
import pandas as pd
from typing import Iterable, Optional
import re

from .data import get_df_scaled
from .market_value import cached_market_value

def top_players(
    features: dict,                        
    n: int = 20,
    df: pd.DataFrame | None = None,
    pos: str | list[str] | None = None,      # 'FW' or ['FW','AM']
    pos_col: str = "Pos",
    max_age: int | None = None,
    min_minutes: int | None = None,
    normalize_weights: bool = False,         # set True if you want weights to sum to 1
    round_to: int = 3,
    extra_cols: tuple = ("Player","Nation","Age","League","Squad","Pos","Minutes"),
    fetch_market_value: bool = True,         # By default it scrapes Transfermarkt market value
    market_value_col: str = "Market_Value_TM"
):
    """
    Rank players by a weighted sum of composite features using the global `df_scaled`.
    - Missing feature columns are created as 0 (no reweighting by default).
    - Optional filters: position substring match, max_age, min_minutes.
    - Adds Transfermarkt market value for the top N players (cached) if fetch_market_value=True.
    """
    # ---- 0) Get the data ----
    if df is None:
        df = get_df_scaled()  

    # score column name
    score_name = 'SCORE'

    # -------- filters --------
    mask = pd.Series(True, index=df.index)

    if pos is not None and pos_col in df.columns:
        pos_list = [pos] if isinstance(pos, str) else list(pos)
        pattern = "|".join(map(re.escape, pos_list))          # substring match
        mask &= df[pos_col].astype(str).str.contains(pattern, case=False, na=False)

    if max_age is not None and "Age" in df.columns:
        mask &= pd.to_numeric(df["Age"], errors="coerce").le(max_age)

    if min_minutes is not None and "Minutes" in df.columns:
        mask &= pd.to_numeric(df["Minutes"], errors="coerce").ge(min_minutes)

    data = df.loc[mask].copy()

    # -------- features & score --------
    feat_cols = list(features.keys())
    for c in feat_cols:
        if c not in data.columns:
            data[c] = 0.0  # missing -> 0

    X = data[feat_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    w = pd.Series(features, index=feat_cols, dtype=float)
    if normalize_weights and w.sum() != 0:
        w = w / w.sum()

    data[score_name] = (X * w).sum(axis=1).round(round_to)

    # -------- sort, cut to top N --------
    data = data.sort_values(score_name, ascending=False).head(n).copy()

    # -------- add Transfermarkt market value --------
    if fetch_market_value and "Player" in data.columns:
        unique_names = data["Player"].astype(str).fillna("").unique().tolist()
        mv_map = {name: cached_market_value(name) if name else None for name in unique_names}
        data[market_value_col] = data["Player"].map(mv_map)

    # -------- order: extra_cols → market_value → feature cols → score --------
    base_cols = [c for c in extra_cols if c in data.columns]
    mv_cols   = [market_value_col] if fetch_market_value else []
    feat_cols_present = [c for c in feat_cols if c in data.columns]

    show_cols = list(dict.fromkeys(base_cols + mv_cols + feat_cols_present + [score_name]))
    out = data.loc[:, show_cols].reset_index(drop=True)
    
    return out

