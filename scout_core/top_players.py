from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union, Dict
import pandas as pd

# --- hardcoded config 
STANDARD_COLS: List[str] = ["Player", "League", "Squad", "Position", "Age", "Nation","Market Value (M€)", "Matches", "Minutes","Goals","Assists"]

FEATURE_MAP: Dict[str, List[str]] = {
        "Goal Scoring": ["Goals_90m", "Goals not Penalty_90m"],
        "Goal Efficacy": ["Goals Minus Expected_90m", "Goals/Shoot","Penalty Efficacy"],     
        "Shooting": ["Shoots_90m","Shoots on Target_90m","Goals/Shoot","FreeKick Tacker"],
        "Passing Influence": ["Short Cmp_90m","Medium Cmp_90m","Long Cmp_90m","Prog Passes_90m","Pass Prog Distance_90m"],
        "Passing Accuracy": ['Cmp Passes%','Short Cmp%','Medium Cmp%','Long Cmp%'],
        "Goal Creation": ['Assists_90m','Key Passes_90m','Goal Creating Actions_90m'],     
        "Possession Influence": ['Touches_90m','Fouls Suffered_90m','Carries_90m'],
        "Progression": ['Prog Carries_90m','Carries PrgDist_90m'],
        "Dribling": ['Take-Ons Succ_90m','Take-Ons Succ%'],
        "Aerial Influence": ['Aerial Duels_90m','Aerial Duels Won%'],     
        "Defensive Influence": ['Tackles Won_90m','Blocks_90m','Interceptions_90m','Clearances_90m','Ball Recoveries_90m'],
        "Discipline and Consistency": ['Own Goals_90m','Errors_90m','Yellow Cards_90m','Red Cards_90m','Fouls Commited_90m','Penalty Commited_90m']
}
# ------------------------------------------------------------------------

@dataclass(frozen=True)
class TopPlayersParams:
    n: int = 10
    pos: Optional[Union[str, List[str]]] = None       
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    min_minutes: Optional[int] = None
    max_minutes: Optional[int] = None
    min_MV: Optional[float] = None                 
    max_MV: Optional[float] = None
    score_name: str = "Score"

def _apply_filters(df: pd.DataFrame, p: TopPlayersParams) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if p.pos is not None:
        mask &= (df["Position"] == p.pos) if isinstance(p.pos, str) else df["Position"].isin(p.pos)
    if p.min_age is not None:      mask &= pd.to_numeric(df["Age"], errors="coerce") >= p.min_age
    if p.max_age is not None:      mask &= pd.to_numeric(df["Age"], errors="coerce") <= p.max_age
    if p.min_minutes is not None:  mask &= pd.to_numeric(df["Minutes"], errors="coerce") >= p.min_minutes
    if p.max_minutes is not None:  mask &= pd.to_numeric(df["Minutes"], errors="coerce") <= p.max_minutes
    if (p.min_MV is not None) or (p.max_MV is not None):
        mv = pd.to_numeric(df["Market Value (M€)"], errors="coerce")
        in_range = pd.Series(True, index=df.index)
        if p.min_MV is not None: in_range &= mv >= p.min_MV
        if p.max_MV is not None: in_range &= mv <= p.max_MV
        mask &= (in_range | mv.isna())  # include NaNs regardless
    return df.loc[mask]

def top_players(
    df: pd.DataFrame,
    selected_features: List[str],
    params: TopPlayersParams = TopPlayersParams(),
) -> pd.DataFrame:
    """Equal-weight ranking over `selected_features`. Returns only configured columns."""
    req = {"Age", "Minutes", "Market Value (M€)", "Position"}
    miss = [c for c in req if c not in df.columns]
    if miss: raise ValueError(f"Missing required columns: {miss}")

    # ensure features numeric
    out = df.copy()
    feat_cols = [c for c in selected_features if c in out.columns]
    if not feat_cols: raise ValueError("None of `selected_features` exist in DataFrame.")
    out[feat_cols] = out[feat_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    # filters
    out = _apply_filters(out, params)

    # score (equal weights)
    out[params.score_name] = out[feat_cols].mean(axis=1)

    all_features = [col for cols in FEATURE_MAP.values() for col in cols]
    for col in all_features:
        if col in out.columns:
            out[col] = out[col].round(1)
    
    # column order: standard + score + selected + extras from FEATURE_MAP
    extras: List[str] = []
    for f in selected_features:
        for c in FEATURE_MAP.get(f, []):
            if c not in extras: extras.append(c)

    order = [c for c in (STANDARD_COLS + [params.score_name] + selected_features + extras) if c in out.columns]
    out = (out
           .sort_values(params.score_name, ascending=False)
           .head(params.n)
           .reset_index(drop=True))
    
    return out.loc[:, order]

__all__ = ["TopPlayersParams", "top_players", "STANDARD_COLS", "FEATURE_MAP"]