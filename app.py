import streamlit as st
import pandas as pd
import io
from pathlib import Path
import base64
from scout_core import set_df_scaled, top_players, FEATURES_ALLOWED, FEATURES_DEFAULT, radar_dodecagon

BASE_DIR = Path(__file__).resolve().parent
DF_PATH = BASE_DIR / "assets" / "df_scaled.parquet"
FALLBACK_PATH = BASE_DIR / "assets" / "sample_df_scaled.parquet"

# Load dataset
if DF_PATH.exists():
    df_scaled = pd.read_parquet(DF_PATH)
elif FALLBACK_PATH.exists():
    st.warning("Using fallback sample dataset.")
    df_scaled = pd.read_parquet(FALLBACK_PATH)
else:
    st.error("No dataset found.")
    st.stop()
    
def save_df_scaled(df: pd.DataFrame):
    df.to_parquet(DF_PATH, index=False)

def load_saved_df_scaled():
    if DF_PATH.exists():
        return pd.read_parquet(DF_PATH)
    return None

st.set_page_config(page_title="Football Scout", layout="wide")

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
            position: absolute; left: 40px; top: 50%;
            transform: translateY(-50%);
            color: #fff; text-align: left;
            padding: 0 12px;
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
                <h1>Football Scout by Pedro Catarino</h1>
                <p>Find and compare players from 14 different leagues with interactive charts</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
# ---------------------------
# Data loading (one-time)
# ---------------------------
@st.cache_data(show_spinner=True)
def load_df(file) -> pd.DataFrame:
    if file.name.endswith(".parquet"):
        return pd.read_parquet(file)
    elif file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        # default to excel
        return pd.read_excel(file)

if 0 == 1: # Sidebar unavailable. When needed adjust to: 0 == 0
    with st.sidebar:
        st.header("Data")
        # 1) Try auto-load from disk
        df_scaled = None
        if DF_PATH.exists():
            df_scaled = pd.read_parquet(DF_PATH)

        # 2) If not found, ask for upload
        if df_scaled is None:
            df_file = st.file_uploader(
                "Upload your df_scaled file",
                type=["parquet", "csv", "xlsx", "xls"]
            )
            if df_file:
                df_scaled = load_df(df_file)        
                df_scaled.to_parquet(DF_PATH, index=False)  
                set_df_scaled(df_scaled)
                st.success("File uploaded and saved. It will auto-load next time.")
                st.rerun()
            else:
                st.info("Please upload your preprocessed df_scaled to begin.")
                st.stop()
        else:
            set_df_scaled(df_scaled)
            st.success("Loaded stored df_scaled.parquet")

            if st.button("Forget stored dataset"):
                DF_PATH.unlink(missing_ok=True)
                st.rerun()

# Safety guard (use df_scaled, not df_file)
if df_scaled is None:
    st.stop()

# Some light helpers
INFO_COLS = {"Player","Nation","Age","League","Squad","Pos","Minutes","Market_Value_TM"}
numeric_cols = sorted([c for c in df_scaled.columns if pd.api.types.is_numeric_dtype(df_scaled[c])])
feature_candidates = [c for c in numeric_cols if c not in INFO_COLS]

# ---------------------------
# UI Tabs
# ---------------------------
tab1, tab2 = st.tabs(["🏆 Find Top Players", "📊 Compare Players"])

# ===========================
# Tab 1: Top Players
# ===========================
with tab1:
    st.subheader("Find Top Players")

    # ----- Top filters row (single line) -----
    # options from data
    pos_opts     = sorted(df_scaled["Pos"].dropna().unique().tolist()) if "Pos"    in df_scaled.columns else []
    league_opts  = sorted(df_scaled["League"].dropna().unique().tolist()) if "League" in df_scaled.columns else []

    # 5 columns across that row (League | Position | Age | Minutes | Top N)
    c_league, c_pos, c_age, c_min, c_topn = st.columns([1.2, 1.2, 1.4, 1.4, 1])

    # League (left-most). "All" means no filter.
    league_choice = c_league.selectbox(
        "League",
        options=(["All"] + league_opts) if league_opts else ["All"],
        index=0,
    )
    # Position Selectbox
    position = c_pos.selectbox(
        "Position",
        options=([""] + pos_opts),
        index=0,
    )
    # Age Slider
    age_min = int(df_scaled["Age"].min()) if "Age" in df_scaled.columns else 16
    age_max = int(df_scaled["Age"].max()) if "Age" in df_scaled.columns else 40
    age_cap = c_age.slider("Maximum Age", min_value=age_min, max_value=age_max, value=min(age_max, 27), step=1)
    # Minutes Slider
    min_minutes = int(df_scaled["Minutes"].min()) if "Minutes" in df_scaled.columns else 0
    max_minutes = int(df_scaled["Minutes"].max()) if "Minutes" in df_scaled.columns else 3000
    minutes_thr = c_min.slider("Minimum Minutes", min_value=min_minutes, max_value=max_minutes, value=min(900, max_minutes), step=30)
    # Top n
    top_n = c_topn.number_input("Number of Players to Find", min_value=5, max_value=50, value=10, step=5)

    feature_candidates = FEATURES_ALLOWED  # defined in ranking.py

    feat_cols = st.multiselect(
        "Select the skills you want to consider when evaluating top players",
        options=feature_candidates,
        default=FEATURES_DEFAULT,   
        max_selections=12,
    )
    
    leagues = None if league_choice == "All" else [league_choice]
    
    run = st.button("Search")

    if run:
        df_out = top_players(
            features={c:1.0 for c in feat_cols}, 
            top_n=int(top_n),
            pos=position if position else None,
            max_age=age_cap,
            min_minutes=minutes_thr,
            leagues=leagues,           
            df=df_scaled, 
        )
        st.dataframe(df_out, use_container_width=True)
        st.caption(f"{len(df_out)} players shown.")

# ===========================
# Tab 2: Compare (Radar)
# ===========================
with tab2:
    st.subheader("Compare Players")

    player_options = sorted(df_scaled["Player"].dropna().unique().tolist()) if "Player" in df_scaled.columns else []
    selected_players = st.multiselect("Players to compare (supports up to 5 players)", options=player_options, max_selections=6)

    draw = st.button("Draw radar")

    if draw:
        if len(selected_players) < 2:
            st.warning("Pick at least two players.")
        else:
            fig = radar_dodecagon(
                players=selected_players,
            )
           
            # Save fig to an in-memory PNG and control its display size
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
            buf.seek(0)

            # Center the plot and control its display width
            left, mid, right = st.columns([1, 3, 1])
            with mid:
                st.image(buf, width=520)  # adjust width (e.g. 480–600) to tast