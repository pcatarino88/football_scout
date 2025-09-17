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

st.set_page_config(
    page_title="Football Scout", 
    page_icon="⚽",
    layout="wide")

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
            height: 150px;                 /* reduce banner height */
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
            position: absolute; left: 20px; top: 40%;            
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
                    Scout players from +10 leagues with interactive charts<br> 
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

LEAGUE_NAMES = {
    "eng1": "England - Premier League",
    "spa1": "Spain - La Liga",
    "ger1": "Germany - Bundesliga",
    "ita1": "Italy - Serie A",
    "fra1": "France - Ligue 1",  
    "net1": "Netherlands - Eredivisie",
    "por1": "Portugal - Primeira Liga",
    "bel1": "Belgium - Pro League",
    "bra1": "Brazil - Série A",
    "arg1": "Argentina - Liga Profesional",
    "eng2": "England - Championship",
    "ita2": "Italy - Serie B"
}


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
    c1, c2, c3, c4, c5 = st.columns(5)

    # League filter
    with c1:
        # Unique league codes from the DF
        league_codes = [code for code in LEAGUE_NAMES if code in df_tab1["League"].unique()]
        # Build display options and reverse map (display -> code)
        display_options = ["All"] + [LEAGUE_NAMES[code] for code in league_codes]
        reverse_map = {LEAGUE_NAMES[code]: code for code in league_codes}
        reverse_map["All"] = "All"
        # UI select (default = All)
        league_display_choice = st.selectbox(
            "League",
            display_options,
            index=0,
            help="Optional filter by league."
        )
        # Convert back to codes for filtering
        leagues = None if league_display_choice == "All" else [reverse_map[league_display_choice]]

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
    
    # Market Value slider
    with c4:
        mv_max_possible = float(pd.to_numeric(df_tab1["Market Value (M€)"], errors="coerce").max() or 200.0)
        mv_max_possible = int(round(mv_max_possible))
    
        max_MV = st.number_input(
            "Maximum Market Value (M€)",
            min_value=0,
            max_value=mv_max_possible,
            value=50,   # default value
            step=5,
            key="mv_max",
            help="Define maximum Market Value to be filtered."
        )
    
    # Top N players
    with c5:
        top_n = st.number_input("Number of Players", min_value=5, max_value=25, value=10, step=5, help="Select number of top players you want to list.")

    # ---------- Skills selector (full width below other filters) ----------
    MAX_SKILLS = 5
    skills = list(FEATURE_MAP.keys())
    
    st.write("Select desired skills for the player search (max 5)")
    
    # map skill -> unique toggle key
    toggle_keys = {skill: f"skill_toggle_{i}" for i, skill in enumerate(skills)}
    
    # callback to enforce the limit
    def _enforce_skill_limit(changed_key: str):
        # gather current selection (after the user action)
        selected_now = [s for s, k in toggle_keys.items() if st.session_state.get(k, False)]
        if len(selected_now) > MAX_SKILLS:
            # revert the last change
            st.session_state[changed_key] = False
            st.session_state["_skill_limit_msg"] = f"You can select up to {MAX_SKILLS} skills."
    
    # layout (2 rows x 6 cols)
    cols = st.columns(6, gap="small")
    
    for i, skill in enumerate(skills):
        with cols[i % 6]:
            st.toggle(
                skill,
                key=toggle_keys[skill],
                value=st.session_state.get(toggle_keys[skill], False),
                on_change=_enforce_skill_limit,
                args=(toggle_keys[skill],),
            )
    
    # toast message if limit was exceeded
    if st.session_state.get("_skill_limit_msg"):
        st.toast(st.session_state["_skill_limit_msg"], icon="⚠️")
        del st.session_state["_skill_limit_msg"]
    
    # final list for downstream use
    selected_features = [s for s, k in toggle_keys.items() if st.session_state.get(k, False)]

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
                max_MV=max_MV,
            )

            res = top_players(
                df=df_work,
                selected_features=selected_features,
                params=params,
            )

            res.index = res.index + 1       # shift index to start at 1
            res.index.name = "Rank"         # rename index
            
            st.dataframe(
                res, 
                use_container_width=True,
                column_config={
                    "Market Value (M€)": st.column_config.NumberColumn(
                        "Market Value (€)",
                        format="€ %.1f M",  # one decimal, in millions
                    )
                }
            )

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
        # Unique league codes from df_tab2
        league_codes_tab2 = [code for code in LEAGUE_NAMES if code in df_tab2["League"].unique()]
        # Build display options (simpler league names)
        display_options_tab2 = ["All"] + [LEAGUE_NAMES[code] for code in league_codes_tab2]
        reverse_map_tab2 = {LEAGUE_NAMES[code]: code for code in league_codes_tab2}
        reverse_map_tab2["All"] = "All"
        # UI select (default = All)
        league_display_choice_tab2 = st.selectbox(
            "League",
            display_options_tab2,
            index=0,
            key="t2_league",
            help="Optional filter by league."
        )
        # Convert back to codes for filtering
        league_code_tab2 = None if league_display_choice_tab2 == "All" else reverse_map_tab2[league_display_choice_tab2]
        # Apply filter
        df_l = df_tab2 if league_code_tab2 is None else df_tab2[df_tab2["League"] == league_code_tab2]

    with c2:
        squads = (sorted(df_l["Squad"].dropna().astype(str).unique().tolist()))
        squad_options = ["All"] + squads
        squad_choice = st.selectbox(
            "Squad",
            squad_options,
            index=0,
            key="t2_squad",
            disabled=(league_code_tab2 is None),  # disabled when League = All
            help="Optional filter by squad."
        )
        # Apply squad filter (keep df_l if 'All' or league not selected)
        df_s = df_l if (league_code_tab2 is None or squad_choice == "All") else df_l[df_l["Squad"] == squad_choice]

    with c3:
        positions = (
            sorted(
                df_s["Position"].dropna().unique().tolist(),
                key=lambda x: POSITION_ORDER.index(x) if x in POSITION_ORDER else len(POSITION_ORDER)
            )
            if squad_choice else []
        )
        position_options = ["All"] + positions

        position = st.selectbox("Position", position_options, index=0, key="t2_pos",
                                help="Optional filter by position.")

        df_p = df_s if position == "All" else df_s[df_s["Position"] == position]

    with c4:
        # Player picker in the cascade path (enabled once Squad chosen)
        player_opts = sorted(df_p["Player"].dropna().unique().tolist()) if squad_choice else []
        picked_chain = st.multiselect("Player", player_opts, default=[],
                                      key="t2_chain_players", disabled=(squad_choice == ""),
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

# APPLICATION FOOTER

# Add spacer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")

# Footer
st.markdown(
    """
<div style="text-align:left; color: gray; font-size: 12px; margin-left:10px; margin-top:5px;">
    Developed by 
    <a href="https://www.linkedin.com/in/pedrofcatarino/" target="_blank"
       style="color:#0a66c2; text-decoration:underline;">
       Pedro Catarino
    </a><br>
    Data sourced from FBref & Transfermarkt.
</div>
    """,
    unsafe_allow_html=True
)