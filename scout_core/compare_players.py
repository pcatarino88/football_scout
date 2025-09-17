import pandas as pd
import plotly.graph_objects as go

FEATURES_12 = [
    "Goal Scoring","Goal Efficacy","Shooting",
    "Passing Influence","Passing Accuracy","Goal Creation",
    "Possession Influence","Progression","Dribling",
    "Aerial Influence","Defensive Influence","Discipline and Consistency"
]

def radar_data(df: pd.DataFrame, players, player_col="Player",
               features=FEATURES_12, fillna=0.0) -> pd.DataFrame:
    data = df.copy()

    # choose the MV column name that exists
    mv_col = "Market Value (M€)" if "Market Value (M€)" in data.columns else (
             "Market Value"      if "Market Value"      in data.columns else None)

    # validate + coerce features
    for f in features:
        if f not in data.columns:
            data[f] = pd.NA
    data[features] = data[features].apply(pd.to_numeric, errors="coerce").fillna(fillna)

    # filter requested players
    keep = data[data[player_col].isin(players)]
    if keep.empty:
        raise ValueError("None of the requested players were found.")

    # carry meta columns into df_long ---
    meta_cols = ["Age", "Squad"] + ([mv_col] if mv_col else [])
    meta_cols = [c for c in meta_cols if c in keep.columns]

    id_vars = [player_col] + meta_cols
    df_long = (
        keep[id_vars + features]
        .melt(id_vars=id_vars, var_name="Feature", value_name="Value")
        .rename(columns={player_col: "Player"})
    )
    return df_long

def radar_plotly(df_long: pd.DataFrame, fill=True, label_map=None):
    features = FEATURES_12
    labels = [label_map.get(f, f) for f in features] if label_map else features
    fig = go.Figure()

    for player, sub in df_long.groupby("Player"):
        # values in the correct order
        vals = sub.set_index("Feature").reindex(features)["Value"].tolist()

        # close the loop
        theta_closed = labels + [labels[0]]
        r_closed = vals + [vals[0]]

        # legend text from meta carried in df_long ---
        age   = sub["Age"].iloc[0]   if "Age"   in sub.columns else None
        squad = sub["Squad"].iloc[0] if "Squad" in sub.columns else None
        if "Market Value (M€)" in sub.columns:
            mv_val = sub["Market Value (M€)"].iloc[0]
        elif "Market Value" in sub.columns:
            mv_val = sub["Market Value"].iloc[0]
        else:
            mv_val = None

        mv_txt = f"{float(mv_val):.1f} M€" if mv_val is not None and pd.notna(mv_val) else "N/A"
        legend_name = f"{player}{', ' + str(int(age)) + 'y' if age is not None else ''}"f"<br>{mv_txt}{' - ' + squad or 'N/A'}"

        fig.add_trace(go.Scatterpolar(
            r=r_closed, theta=theta_closed,
            fill="toself" if fill else None,
            fillcolor="rgba(0,100,200,0.2)" if fill else None,           
            name=legend_name,
            connectgaps=True
        ))

    fig.update_layout(
        autosize = True,
        polar=dict(
            angularaxis=dict(
                tickfont=dict(size=10),   # smaller label text
                rotation=90,              # start at top 
                ),
            radialaxis=dict(range=[0, 1], tickvals=[0.2, 0.4, 0.6, 0.8])),
        showlegend=True, 
        template="plotly_white",
        legend=dict(
            orientation="h",       # horizontal legend
            yanchor="bottom",      # anchor at bottom or top
            y=1.1,                 # move above the plot (use -0.2 to put below)
            xanchor="center",      
            x=0.5                  # center it horizontally
        ),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig