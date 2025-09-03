import pandas as pd
import numpy as np
from typing import Iterable, Optional
import matplotlib.pyplot as plt
from .data import get_df_scaled

def radar_dodecagon(
    players: list[str],
    df: pd.DataFrame | None = None,
    player_col: str = "Player",
    title: str | None = None,
    nan_to: float = 0.0,
    max_players: int = 5,
    label_map: dict[str, str] | None = None
):
    """
    Draw a 12-axis radar (dodecagon) for up to 5 players using the global `df_scaled`.
    """
    if df is None:
        df = get_df_scaled()
        
    features_12 = [
        "goal_scoring", "goal_efficacy", "shooting","passing_influence", "passing_accuracy", "goal_creation",
        "possession_influence", "progression", "take_ons",        "aerial_influence", "defensive_influence", "discipline_and_consistency"
    ]

    if len(features_12) != 12:
        raise ValueError("The internal feature list must have exactly 12 items.")
    if not players:
        raise ValueError("Provide at least one player name.")
    if len(players) > max_players:
        raise ValueError(f"Provide at most {max_players} players (got {len(players)}).")

    # Ensure feature columns exist; if not, create as NaN so they show as nan_to
    for c in features_12:
        if c not in df.columns:
            df[c] = np.nan

    # Angles & labels
    labels = [label_map.get(f, f) for f in features_12] if label_map else features_12
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
    angles_closed = np.r_[angles, angles[:1]]

    # --- Figure & axes ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, 16), subplot_kw=dict(polar=True))

    # x/angle labels
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=45)
    ax.tick_params(axis='x', pad=75)

    # radial ticks
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8"], fontsize=34, color="grey")
    ax.set_rlabel_position(0)

    # --- Plot each player ------------------------------------------------------
    plotted = 0
    for p in players:
        idx = df.index[df[player_col].astype(str) == str(p)]
        if len(idx) == 0:
            continue
        row = (
            df.loc[idx[0], features_12]
              .apply(pd.to_numeric, errors="coerce")
              .fillna(nan_to)
        )
        vals = row.values
        vals_closed = np.r_[vals, vals[:1]]

        line, = ax.plot(angles_closed, vals_closed, linewidth=3, label=p)
        ax.fill(angles_closed, vals_closed, alpha=0.20, facecolor=line.get_color(), zorder=0)
        plotted += 1

    if plotted == 0:
        raise ValueError("None of the requested players were found in the database.")

    # --- Legend completely outside on the right --------------------------------
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.45, 0.85),  # stick to the right edge of the axes
        borderaxespad=0.0,
        frameon=True,
        fontsize=50
    )

    # Leave space on the right for legend and on the top for the suptitle
    fig.tight_layout(rect=[0.00, 0.00, 1.50, 1.00])

    return fig