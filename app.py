import streamlit as st
import pandas as pd
import io
from pathlib import Path
import base64

import plotly.io as pio
from scout_core import radar_data, radar_plotly
from scout_core import top_players, TopPlayersParams, FEATURE_MAP

BASE_DIR = Path(__file__).resolve().parent

# -------------------------------
# I. Page config
# -------------------------------

st.set_page_config(page_title="Football Scout", layout="wide")

st.markdown(
    """
    <style>
    /* reduce the big top padding Streamlit applies */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Banner ---
# --- Paths ---
BANNER_PATH = BASE_DIR / "assets" / "cover.png"

if not BANNER_PATH.exists():
    st.warning(f"Banner not found at {BANNER_PATH}")
else:
    # Convert to base64 string
    b64 = base64.b64encode(BANNER_PATH.read_bytes()).decode()

    st.markdown(
         f"""
        <style>
        .banner-wrap {{
            position: relative;
            margin: 12px 0 18px 0;
            border-radius: 12px;
            overflow: hidden;
            height: 220px;                 /* reduce banner height */
        }}
        .banner-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .banner-overlay {{
            position: absolute; inset: 0;            
            background: rgba(0,0,0,0.28);   /* transparency */
        }}
        .banner-text {{
            position: absolute; left: 20px; top: 50%;            
            transform: translateY(-50%);
            color: #fff; text-align: left;
            padding: 0;
        }}
        .banner-text h1 {{
            margin: 0 0 6px 0;
            font-size: 44px;
        }}    
        .banner-text p {{
            margin: 0; font-size: 18px; opacity: .95;
        }}
        /* Responsive tweaks */
        @media (max-width: 900px) {{
            .banner-wrap {{ height: 200px; }}
            .banner-text h1 {{ font-size: 34px; }}
            .banner-text p {{ font-size: 16px; }}
        }}
        @media (max-width: 600px) {{
            .banner-wrap {{ height: 170px; }}
            .banner-text h1 {{ font-size: 26px; }}
            .banner-text p {{ font-size: 14px; }}
        }}
        .stTabs [role="tab"] {{
            font-size: 1.5rem;      /* bigger text */
            font-weight: 800;       /* bolder */
            padding: 1.0rem 1,4rem;   /* roomier */
        }}
        .stTabs [aria-selected="true"] {{
            color: #d32f2f;
            border-bottom: 3px solid #d32f2f; /* thicker underline */
        }}
        </style>
    
        <div class="banner-wrap">
            <img class="banner-img" src="data:image/png;base64,{b64}" alt="banner"/>
            <div class="banner-overlay"></div>
            <div class="banner-text">
                <h1>Football Scout</h1>
                <p>
                    Scout players from +10 leagues with interactive charts.<br> 
                    Developed by 
                    <a href="https://www.linkedin.com/in/pedrofcatarino/" target="_blank" style="color:#fff; text-decoration:underline; display:inline-flex; align-items:center; gap:6px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style="display:inline-block; vertical-align:middle;">
                          <path d="M20.447 20.452h-3.554v-5.569c0-1.329-.027-3.039-1.852-3.039-1.853 0-2.136 1.448-2.136 2.945v5.663H9.351V9h3.414v1.561h.049c.476-.9 1.637-1.852 3.366-1.852 3.599 0 4.264 2.37 4.264 5.455v6.288zM5.337 7.433a2.062 2.062 0 1 1 0-4.124 2.062 2.062 0 0 1 0 4.124zM6.999 20.452H3.671V9h3.328v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.226.792 24 1.771 24h20.454C23.2 24 24 23.226 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
                        </svg>
                        Pedro Catarino
                    </a>.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------
# III. Helpers
# -------------------------------

@st.cache_data
def load_df(path) -> pd.DataFrame:
    return pd.read_parquet(path)

POSITION_ORDER = ["Centre Back (CB)","Right Back (RB)","Left Back (LB)","Defensive Midfielder (DM)","Center Midfielder (CM)",
                  "Attacking Midfielder (AM)","Rigth Winger (RW)","Left Winger (LW)","Center Forward (CF)"]


# ---------------------------
# Tabs
# ---------------------------

tab1, tab2 = st.tabs(["🏆 Find Top Players", "📊 Compare Players"])

# ===========================
# Tab 1: Top Players
# ===========================
with tab1:
    st.subheader("Find Top Players")

    df_tab1 = load_df("assets/df_tab1.parquet")

    # ---------- Filters in 5 columns ----------
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    # League filter
    with c1:
        league_opts = ["All"] + sorted(df_tab1["League"].dropna().unique().tolist())
        league_choice = st.selectbox("League", league_opts, index=0, help="Optional filter by league.")
        leagues = None if league_choice == "All" else [league_choice]

    # Position filter
    with c2:
        present = set(df_tab1["Position"].dropna().unique().tolist())
        pos_opts = ["All"] + [p for p in POSITION_ORDER if p in present]
        position = st.selectbox("Position", pos_opts, index=0, help="Optional filter by position")
        pos_filter = None if position == "All" else position
    
    # Age Slider
    with c3:
        min_age, max_age = st.slider(
            "Age", 
            min_value=16, 
            max_value=40, 
            value=(16,27),
            step=1,
            help="Define desired age interval to be filtered.")
    
    # Minutes Slider
    with c4:
        min_minutes, max_minutes = st.slider(
            "Minutes", 
            min_value=300, 
            max_value=int(df_tab1["Minutes"].max()), 
            value=(1200,int(df_tab1["Minutes"].max())), 
            step=50,
            help="Define minimum minutes the player must have in last season to be filtered."
        )

    # Market Value slider
    with c5:
        mv_max_possible = float(pd.to_numeric(df_tab1["Market Value (M€)"], errors="coerce").max() or 0.0)
        min_MV, max_MV = st.slider(
            "Market Value (M€)",
            min_value=0.0,
            max_value=max(0.1, mv_max_possible),
            value=(0.0, max(0.1, mv_max_possible)),
            step=0.1,
            help="Filter by market value. Players with unknown value are kept."
        )
    
    # Top N players
    with c6:
        top_n = st.number_input("Number of Players", min_value=5, max_value=25, value=10, step=5, help="Select number of top players you want to list.")

    # ---------- Skills selector (full width below other filters) ----------
    selected_features = st.multiselect(
        "Select desired skills for the player search",
        options=list(FEATURE_MAP.keys()),
        default=None,
        max_selections=5,
    )

    # ---------- Run ----------
    run = st.button("Search")

    if run:
        # keep your league filter outside top_players (function doesn't filter by league)
        df_work = df_tab1 if leagues is None else df_tab1[df_tab1["League"].isin(leagues)]

        try:
            params = TopPlayersParams(
                n=top_n,
                pos=pos_filter,
                min_age=min_age,
                max_age=max_age,
                min_minutes=min_minutes,
                max_minutes=max_minutes,
                min_MV=min_MV,
                max_MV=max_MV,
            )

            res = top_players(
                df=df_work,
                selected_features=selected_features,
                params=params,
            )

            res.index = res.index + 1       # shift index to start at 1
            res.index.name = "Rank"         # rename index
            
            st.dataframe(res, use_container_width=True)

        except ValueError as e:
            st.error(str(e))

# ===========================
# Tab 2: Compare (Radar)
# ===========================

with tab2:  
    df_tab2 = load_df("assets/df_tab2.parquet")
    
    st.subheader("Compare Players")

    # --- keep accumulated selections in session ---
    if "selected_players_tab2" not in st.session_state:
        st.session_state.selected_players_tab2 = []

    def dedupe_keep_order(seq):
        seen, out = set(), []
        for x in seq:
            if x not in seen:
                seen.add(x); out.append(x)
        return out

    def add_players(picks):
        if picks:
            st.session_state.selected_players_tab2 = dedupe_keep_order(
                st.session_state.selected_players_tab2 + list(picks)
            )

    # ---------- Top row: League | Squad | Position | Player ----------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        leagues = [""] + sorted(df_tab2["League"].dropna().unique().tolist())
        league = st.selectbox("League", leagues, index=0, key="t2_league")

    df_l = df_tab2 if league == "" else df_tab2[df_tab2["League"] == league]

    with c2:
        squads = [""] + (sorted(df_l["Squad"].dropna().unique().tolist()) if league else [])
        squad = st.selectbox("Squad", squads, index=0, key="t2_squad",
                             disabled=(league == ""))

    df_s = df_l if (squad == "" or league == "") else df_l[df_l["Squad"] == squad]

    with c3:
        positions = [""] + (sorted(df_s["Position"].dropna().unique().tolist()) if squad else [])
        position = st.selectbox("Position", positions, index=0, key="t2_pos",
                                disabled=(squad == ""))

    df_p = df_s if (position == "" or squad == "") else df_s[df_s["Position"] == position]

    with c4:
        # Player picker in the cascade path (enabled once Squad chosen)
        player_opts = sorted(df_p["Player"].dropna().unique().tolist()) if squad else []
        picked_chain = st.multiselect("Player", player_opts, default=[],
                                      key="t2_chain_players", disabled=(squad == ""),
                                      placeholder="Select one or more…")
        add_players(picked_chain)

    # ---------- Players to compare ----------
    search_pool = df_p if position != "" else (df_s if squad != "" else (df_l if league != "" else df_tab2))
    pool_names = sorted(search_pool["Player"].dropna().unique().tolist())
    current = st.session_state.selected_players_tab2

    # union = current selections + filtered pool (to keep selections visible)
    options_for_box = dedupe_keep_order(current + pool_names)

    st.markdown("**Players to compare**")
    st.session_state.selected_players_tab2 = st.multiselect(
        "Type to search and manage your list",
        options=options_for_box,
        default=current,
        key="t2_selected_players_box",
        placeholder="Start typing a name…",
        help="Suggestions respect the filters above. Unselect to remove."
    )

    # ---------- Draw  ----------
    players = st.session_state.selected_players_tab2
    fill = st.checkbox("Fill areas", value=True)
    draw = st.button("Draw radar")

    if draw:
        if players:
            df_long = radar_data(df_tab2, players)
            fig = radar_plotly(df_long, fill=fill)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select at least one player.")