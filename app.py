import streamlit as st
import pandas as pd
import numpy as np
import io
from pathlib import Path
import base64
import plotly.io as pio
from scout_core import radar_data, radar_plotly
from scout_core import top_players, TopPlayersParams, FEATURE_MAP, STANDARD_COLS

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
BANNER_PATH = BASE_DIR / "assets" / "cover2.png"

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
            background-image: url("data:image/png;base64,{b64}");
            background-size: cover;          /* fill */
            background-position: center;     /* center crop */
            background-repeat: no-repeat;
      }}
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
 
POSITION_ORDER = ["CB","RB","LB","DM","CM","AM","RW","LW","CF"]

LEAGUE_NAMES = {
    "GB 1": "England - Premier League",
    "ES 1": "Spain - La Liga",
    "DE 1": "Germany - Bundesliga",
    "IT 1": "Italy - Serie A",
    "FR 1": "France - Ligue 1",  
    "NL 1": "Netherlands - Eredivisie",
    "PT 1": "Portugal - Primeira Liga",
    "BE 1": "Belgium - Pro League",
    "BR 1": "Brazil - Série A",
    "AR 1": "Argentina - Liga Profesional",
    "GB 2": "England - Championship",
    "IT 2": "Italy - Serie B"
}

POSITION_NAMES = {
    "CB": "Centre Back (CB)",
    "RB": "Right Back (RB)",
    "LB": "Left Back (LB)",
    "DM": "Defensive Midfielder (DM)",
    "CM": "Center Midfielder (CM)",
    "AM": "Attacking Midfielder (AM)",    
    "RW": "Rigth Winger (RW)",
    "LW": "Left Winger (LW)",
    "CF": "Center Forward (CF)"
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
        # Unique position codes from the DF
        position_codes = [code for code in POSITION_NAMES if code in df_tab1["Position"].unique()]
        # Build display options and reverse map (display -> code)
        display_options = ["All"] + [POSITION_NAMES[code] for code in position_codes]
        reverse_map = {POSITION_NAMES[code]: code for code in position_codes}
        reverse_map["All"] = "All"
        # UI select (default = All)
        position_display_choice = st.selectbox(
            "Position",
            display_options,
            index=0,
            help="Optional filter by position."
        )
        # Convert back to codes for filtering
        position = None if position_display_choice == "All" else [reverse_map[position_display_choice]]
    
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
                pos=position,
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
            # store results + features for later reruns
            st.session_state.tp_res = res
            st.session_state.tp_features = selected_features
        except ValueError as e:
            st.error(str(e))

    # ---------- render results (persists across reruns) ----------
    res = st.session_state.get("tp_res")
    selected_features_for_view = st.session_state.get("tp_features", [])
    
    if res is not None:            
        # -- TABLE FORMATING --
        def highlight_subset(df, cols1, color1, cols2=None, color2=None):
            cols1 = [c for c in (cols1 or []) if c in df.columns]
            cols2 = [c for c in (cols2 or []) if c in df.columns]
            styler = df.style
            if cols2 and color2: styler = styler.set_properties(subset=cols2, **{"background-color": color2})
            if cols1 and color1: styler = styler.set_properties(subset=cols1, **{"background-color": color1})
            return styler
        
        # decide columns
        core_cols = [c for c in (STANDARD_COLS + ["Score"] + selected_features_for_view) if c in res.columns]
        extras_raw = [c for f in selected_features_for_view for c in FEATURE_MAP.get(f, []) if c in res.columns]
        seen = set(); extra_cols = [c for c in extras_raw if not (c in seen or seen.add(c))]
    
        show_extras = st.toggle("Show extra stats (per-feature details)", value=False, key="show_extras")
        cols_to_show = core_cols + (extra_cols if show_extras else [])
        df_show = res.loc[:, cols_to_show].copy()
    
        # style
        score_props = {
            "background-color": "rgba(0,95,95,0.65)",  # darker + more opaque
            "color": "white",
            "font-weight": "bold",
            "text-align": "center",
        }
       
        styled = (
            highlight_subset(
                df_show,
                cols1=["Score"],                 color1="rgba(0,95,95,0.65)",
                cols2=list(FEATURE_MAP.keys()), color2="rgba(175,175,175,0.25)",
            )
            .set_properties(subset=['Score'], **score_props)
        )
    
        # column config (only for visible columns)
        BASE_CFG = {
            "Market Value (M€)": st.column_config.NumberColumn("Market Value", format="€ %.1f M"),
            "Score": st.column_config.NumberColumn("Score", format="%.2f"),
            "Goal Scoring": st.column_config.NumberColumn("Scoring", format="%.2f"),
            "Goal Efficacy": st.column_config.NumberColumn("Efficacy", format="%.2f"),
            "Goal Creation": st.column_config.NumberColumn("Goal Creation", format="%.2f"),
            "Shooting": st.column_config.NumberColumn("Shooting", format="%.2f"),
            "Passing Influence": st.column_config.NumberColumn("Pass Inf.", format="%.2f"),
            "Passing Accuracy": st.column_config.NumberColumn("Pass Acc.", format="%.2f"),
            "Possession Influence": st.column_config.NumberColumn("Possession", format="%.2f"),  # note spelling
            "Progression": st.column_config.NumberColumn("Progression", format="%.2f"),
            "Dribling": st.column_config.NumberColumn("Dribling", format="%.2f"),
            "Aerial Influence": st.column_config.NumberColumn("Aerial", format="%.2f"),
            "Defensive Influence": st.column_config.NumberColumn("Defense", format="%.2f"),
            "Discipline and Consistency": st.column_config.NumberColumn("Disc. & Consist.", format="%.2f"),
            "Goals_90m": st.column_config.NumberColumn("Gls/90", help="Goals per 90 minutes", format="%.2f", width="small"),
            "Goals not Penalty_90m": st.column_config.NumberColumn("Gls NP/90", help="Goals not Penalty per 90 minutes", format="%.2f", width="small"),
            "Goals Minus Expected_90m": st.column_config.NumberColumn("Gls-Exp/90m", help="Goals Minus Expected Goals per 90 minutes", format="%.2f", width="small"),
            "Goals/Shoot": st.column_config.NumberColumn("Gls/Shoot", help="Goals per Shoots", format="%.2f", width="small"),
            "Penalty Efficacy": st.column_config.NumberColumn("Pen Eff%", help="Penalty Scored / Penalty Attempts", format="%.2f", width="small"),
            "Shoots_90m": st.column_config.NumberColumn("Sht/90m", help="Shoots per 90 minutes", format="%.2f", width="small"),
            "Shoots on Target_90m": st.column_config.NumberColumn("SoT/90m", help="Shoots on Target per 90 minutes", format="%.2f", width="small"),
            "FreeKick Tacker": st.column_config.NumberColumn("FK Tacker", help="FreeKick Tacker (1 if yes)", format="%.0f", width="small"),
            "Short Cmp_90m": st.column_config.NumberColumn("Sht Pass/90m", help="Short distance passes completed per 90 minutes", format="%.1f", width="small"),
            "Medium Cmp_90m": st.column_config.NumberColumn("Med Pass/90m", help="Medium distance passes completed per 90 minutes", format="%.1f", width="small"),
            "Long Cmp_90m": st.column_config.NumberColumn("Long Pass/90m", help="Long distance passes completed per 90 minutes", format="%.1f", width="small"),
            "Prog Passes_90m": st.column_config.NumberColumn("Prog Pass/90m", help="Progressive passes completed per 90 minutes", format="%.1f", width="small"),
            "Pass Prog Distance_90m": st.column_config.NumberColumn("Pass Dist/90m", help="Progressive passes distance per 90 minutes", format="%.1f", width="small"),
            "Cmp Passes%": st.column_config.NumberColumn("Pass Acc%", help="Completed Passes / Attempted Passes", format="%.1f", width="small"),
            "Short Cmp%": st.column_config.NumberColumn("Pass Short%", help="Completed Short Passes / Attempted Short Passes", format="%.1f", width="small"),
            "Medium Cmp%": st.column_config.NumberColumn("Pass Med%", help="Completed Medium Passes / Attempted Medium Passes", format="%.1f", width="small"),
            "Long Cmp%": st.column_config.NumberColumn("Pass Long%", help="Completed Long Passes / Attempted Long Passes", format="%.1f", width="small"), 
            "Assists_90m": st.column_config.NumberColumn("Ast/90m", help="Assists per 90 minutes", format="%.2f", width="small"),            
            "Key Passes_90m": st.column_config.NumberColumn("Key Pass/90m", help="Key Passes per 90 minutes", format="%.2f", width="small"),    
            "Goal Creating Actions_90m": st.column_config.NumberColumn("GCA/90m", help="Goal Creating Actions per 90 minutes", format="%.2f", width="small"),
            "Touches_90m": st.column_config.NumberColumn("Touch/90m", help="Touches on the ball per 90 minutes", format="%.1f", width="small"),
            "Fouls Suffered_90m": st.column_config.NumberColumn("Fls Suf/90m", help="Fouls suffered per 90 minutes", format="%.1f", width="small"),
            "Carries_90m": st.column_config.NumberColumn("Carr/90m", help="Carries per 90 minutes", format="%.1f", width="small"),      
            "Prog Carries_90m": st.column_config.NumberColumn("PCarr/90m", help="Progressive Carries per 90 minutes", format="%.1f", width="small"),    
            "Carries PrgDist_90m": st.column_config.NumberColumn("PCarr Dis/90m", help="Progressive Carries Distance per 90 minutes", format="%.1f", width="small"),  
            "Take-Ons Succ_90m": st.column_config.NumberColumn("Drb/90m", help="Successfull dribles per 90 minutes", format="%.1f", width="small"),
            "Take-Ons Succ%": st.column_config.NumberColumn("Drb%", help="Successfull dribles / Attempted", format="%.1f", width="small"),
            "Aerial Duels_90m": st.column_config.NumberColumn("Aerial/90m", help="Aerials duels per 90 minutes", format="%.1f", width="small"),
            "Aerial Duels Won%": st.column_config.NumberColumn("Aerial %", help="Aerials Duels Won / Aerial Duels Total", format="%.1f", width="small"),
            "Tackles Won_90m": st.column_config.NumberColumn("Tkl/90m", help="Tackles won per 90 minutes", format="%.1f", width="small"),
            "Blocks_90m": st.column_config.NumberColumn("Blk/90m", help="Blocks per 90 minutes", format="%.1f", width="small"),
            "Interceptions_90m": st.column_config.NumberColumn("Int/90m", help="Interceptions per 90 minutes", format="%.1f", width="small"),
            "Clearances_90m": st.column_config.NumberColumn("Clr/90m", help="Clearances per 90 minutes", format="%.1f", width="small"),
            "Ball Recoveries_90m": st.column_config.NumberColumn("Rec/90m", help="Ball Recoveries per 90 minutes", format="%.1f", width="small"),
            "Own Goals_90m": st.column_config.NumberColumn("OG/90m", help="Own Goals per 90 minutes", format="%.2f", width="small"),
            "Errors_90m": st.column_config.NumberColumn("Err/90m", help="Errors leading to a shot or goal per 90 minutes", format="%.2f", width="small"),
            "Yellow Cards_90m": st.column_config.NumberColumn("YC/90m", help="Yellow Cards per 90 minutes", format="%.2f", width="small"),
            "Red Cards_90m": st.column_config.NumberColumn("RC/90m", help="Red Cards per 90 minutes", format="%.2f", width="small"),
            "Fouls Commited_90m": st.column_config.NumberColumn("FlsCom/90m", help="Fouls committed per 90 minutes", format="%.1f", width="small"),
            "Penalty Commited_90m": st.column_config.NumberColumn("PKCom/90m", help="Penalty committed per 90 minutes", format="%.2f", width="small")
        }
        cfg = {k: v for k, v in BASE_CFG.items() if k in df_show.columns}
    
        st.dataframe(styled, use_container_width=True, column_config=cfg)
    else:
        st.info("Set filters and click Search.")

    if run:
       # Tab 1 Footer
        st.write("")
        st.markdown(
            """
        <div style="text-align:left; color: gray; font-size: 10px; margin-left:10px; margin-top:5px;">
            Skills were weighted according to related statistics as detailed below.  All metrics were scaled before weighting. <br>
            1. <b>Goal Scoring</b>: Goals scored per 90m (60%), Goals scored excluding penalties per 90m (40%).
            2. <b>Goal Efficacy</b>: Goals scored minus expected goals scored per 90m (40%), 
            Goals divided by total shoots (40%), Penalties scored versus penalties attempted (20%).
            3. <b>Shooting</b>: Total shoots per 90m (30%), Shoots on Target per 90m (40%), 
            Goals versus total shoots (20%), FreeKick Tacker - yes or no (10%)
            4. <b>Passing Influence</b>: Short passes completed per 90min (17.5%), 
            Medium passes completed per 90m (17.5%), Long passes completed per 90m (17.5%), 
            Progressive passes completed per 90m (35%), Progressive passes distance per 90m (12.5%).
            5. <b>Passing Accuracy</b>: Total passes accuracy (55%), short passes accuracy (15%), 
            medium passes accuracy (15%), long passes accuracy (15%).
            6. <b>Goal Creation</b>: Assists per 90m (40%), Key Passes per 90m (30%), 
            Goal Creating Actions per 90m (20%), Penalty won per 90m (10%).
            7. <b>Possession Influence</b>: Ball touches per 90m (40%), Carries per 90m (40%), 
            Fouls Suffered per 90m (20%).
            8. <b>Progression</b>: Progressive Carries per 90m (60%), Carries progressive distance per 90m (40%).
            9. <b>Dribling</b>: Successfull dribles per 90m (50%), Percentage of successfull dribles (50%).
            10. <b>Aerial Influence</b>: Total aerial duels per 90m (40%), Percentage of aerial duels won (60%).
            11. <b>Defensive Influence</b>: Tackles won per 90m (17.5%), Blocks per 90m (17.5%), 
            Interceptions per 90m (17.5%), Clearances per 90m, Ball (17.5%) Recoveries per 90m (17.5%).
            12. <b>Discipline and Consistency</b>: Own Goals per 90m (17.5%), Errors commited per 90m (17.5%), 
            Yellow cards per 90m (15%), Red cards per 90m (17.5%), Fouls commited per 90m (15%), 
            Penalties commited per 90m (17.5%).
            </a><br>
        </div>
            """,
            unsafe_allow_html=True
        )    

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
        positions = [
            p for p in POSITION_ORDER
            if p in df_s["Position"].dropna().unique().tolist()
        ] if squad_choice else []
    
        # Add "All" option at the beginning
        position_options = ["All"] + positions
    
        # Selectbox with friendly labels from POSITION_NAMES
        position = st.selectbox(
            "Position",
            position_options,
            index=0,
            key="t2_pos",
            help="Optional filter by position.",
            format_func=lambda x: POSITION_NAMES.get(x, x)  # fallback to code if not in dict
        )

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
    st.markdown("""
    <style>
    @media (max-width: 900px){
    /* Old & new Streamlit selectors */
    .main .block-container{ padding-left:12px !important; padding-right:12px !important; }
    [data-testid="stAppViewContainer"] .main .block-container{ padding-left:12px !important; padding-right:12px !important; }

    /* Plotly wrapper tweaks so the iframe doesn't add its own outer gaps */
    .stPlotlyChart, .stPlotlyChart > div { margin-left:0 !important; margin-right:0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    players = st.session_state.selected_players_tab2
    fill = st.checkbox("Fill areas", value=True)
    draw = st.button("Draw radar")

    if draw:
        if players:
            df_long = radar_data(df_tab2, players)
            fig = radar_plotly(df_long, fill=fill)
            fig.update_layout(
                margin=dict(l=24, r=24, t=24, b=24),   # tweak values to taste
                autosize=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select at least one player.")

# APPLICATION FOOTER

# Add spacer
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <hr style="margin: 5px 0 0 0; border: none; border-top: 1px solid #ddd;">
    """,
    unsafe_allow_html=True
)

# Footer
st.markdown(
    """
<div style="text-align:left; color: gray; font-size: 12px; margin-left:10px; margin-top:0px;">
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