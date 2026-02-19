"""
Para Athletics Azure Database Dashboard
Connects to Azure Blob Storage (Parquet) for real-time data
Includes Championship Analysis, Records, Rankings, and Pre-Competition Analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from glob import glob
from functools import lru_cache
import base64

# Import Parquet data layer for Azure Blob Storage
try:
    from parquet_data_layer import (
        get_data_manager,
        get_connection_mode,
        load_results as parquet_load_results,
        load_rankings as parquet_load_rankings,
        load_records as parquet_load_records
    )
    PARQUET_AVAILABLE = True
except Exception as e:
    print(f"Parquet data layer not available: {e}")
    PARQUET_AVAILABLE = False
    def get_connection_mode():
        return "local_csv"

# Team Saudi Brand Colors
TEAL_PRIMARY = '#007167'
GOLD_ACCENT = '#a08e66'
TEAL_DARK = '#005a51'
TEAL_LIGHT = '#009688'
GRAY_BLUE = '#78909C'

# Page config
st.set_page_config(
    page_title="Para Athletics - Azure Database",
    page_icon="🏃‍♂️",
    layout="wide"
)

# Custom CSS - Professional sports theme, completely hide default spinner animations
st.markdown(f"""
<style>
    .main {{
        background-color: #f8f9fa;
    }}
    .stMetric {{
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}

    /* COMPLETELY HIDE all Streamlit spinner animations (donuts, cakes, cookies, etc.) */
    .stSpinner > div > div,
    .stSpinner svg,
    .stSpinner [data-testid="stSpinner"],
    [data-testid="stSpinner"] > div,
    [data-testid="stSpinner"] svg,
    .stSpinner > div:first-child,
    div[data-testid="stSpinnerAnimation"],
    .stSpinner div[class*="Animation"],
    .stSpinner div[class*="spinner"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }}

    /* Hide Streamlit's "App is running/cooking" startup animations */
    [data-testid="stAppViewBlockContainer"] .stMarkdown img[src*="cooking"],
    [data-testid="stAppViewBlockContainer"] .stMarkdown img[src*="baking"],
    [data-testid="stAppViewBlockContainer"] .stMarkdown img[src*="oven"],
    .stApp [data-testid="stImage"] img[alt*="cooking"],
    .element-container img[src*="giphy"],
    .stMarkdown img[src*="tenor"],
    div[class*="loading"] img,
    div[class*="Loading"] img {{
        display: none !important;
    }}

    /* Hide default Streamlit status messages about cooking/baking */
    .stStatusWidget,
    [data-testid="stStatusWidget"] {{
        display: none !important;
    }}

    /* Style the spinner container with Team Saudi branding */
    .stSpinner,
    [data-testid="stSpinnerContainer"] {{
        background: linear-gradient(135deg, {TEAL_PRIMARY}10 0%, {TEAL_DARK}10 100%);
        border-radius: 8px;
        padding: 1.5rem;
        border-left: 4px solid {TEAL_PRIMARY};
        min-height: 60px;
    }}

    /* Style the spinner text (the message we pass to st.spinner) */
    .stSpinner > div:last-child,
    [data-testid="stSpinnerContainer"] > div:last-child {{
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: {TEAL_PRIMARY};
        font-weight: 600;
        font-size: 1rem;
        text-align: center;
        animation: pulse 1.5s ease-in-out infinite;
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.6; }}
    }}

    /* Progress bar styling */
    .stProgress > div > div {{
        background-color: {TEAL_PRIMARY};
    }}

    /* Team Saudi Sidebar Styling - Green like banner */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: white !important;
    }}
    [data-testid="stSidebar"] [data-testid="stAlert"] {{
        background-color: rgba(255,255,255,0.15);
        color: white;
        border: none;
    }}
    [data-testid="stSidebar"] [data-testid="stAlert"] p {{
        color: white !important;
    }}
</style>
""", unsafe_allow_html=True)

# Helper function to encode images to base64
def get_image_base64(image_path):
    """Encode image to base64 for embedding in HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Theme paths
theme_dir = Path(r"C:\Users\l.gallagher\OneDrive - Team Saudi\Documents\Performance Analysis\Theme")
banner_path = theme_dir / "team_saudi_banner.jpg"
logo_path = theme_dir / "team_saudi_logo.jpg"
saudi_logo_path = Path("Saudilogo.png")

# Header with Banner Image
banner_b64 = get_image_base64(banner_path) if banner_path.exists() else None

if banner_b64:
    st.markdown(f'''
    <div style="position: relative; border-radius: 12px; overflow: hidden; margin-bottom: 1.5rem;
         box-shadow: 0 8px 25px rgba(0, 113, 103, 0.25);">
        <img src="data:image/jpeg;base64,{banner_b64}" style="width: 100%; height: 180px; object-fit: cover; filter: brightness(0.7);">
        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center;">
            <div style="text-align: center;">
                <h1 style="color: white; font-size: 2.2rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
                    Para Athletics Dashboard
                </h1>
                <p style="color: {GOLD_ACCENT}; font-size: 1.1rem; margin: 0.5rem 0 0 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
                    Real-time Championship Analysis & Performance Tracking
                </p>
            </div>
        </div>
        <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, {TEAL_PRIMARY} 0%, {GOLD_ACCENT} 50%, {TEAL_DARK} 100%);"></div>
    </div>
    ''', unsafe_allow_html=True)
else:
    # Fallback header without banner image
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
                padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">Para Athletics Dashboard</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Real-time data from Azure Blob Storage (Parquet)
        </p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar Logo
logo_b64 = get_image_base64(logo_path) if logo_path.exists() else None
saudi_logo_b64 = get_image_base64(saudi_logo_path) if saudi_logo_path.exists() else None

if logo_b64:
    st.sidebar.markdown(f'''
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
        <img src="data:image/jpeg;base64,{logo_b64}" style="width: 180px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    </div>
    ''', unsafe_allow_html=True)
elif saudi_logo_b64:
    st.sidebar.markdown(f'''
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
        <img src="data:image/png;base64,{saudi_logo_b64}" style="width: 180px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    </div>
    ''', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
                padding: 1rem; border-radius: 8px; text-align: center; margin-bottom: 1rem;">
        <h3 style="color: white; margin: 0;">Team Saudi</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.8rem;">Para Athletics</p>
    </div>
    """, unsafe_allow_html=True)

# Show connection mode in sidebar
mode = get_connection_mode()
mode_display = {
    'azure_blob': 'Azure Blob Storage',
    'local_parquet': 'Local Parquet',
    'local_csv': 'Local CSV'
}.get(mode, mode)
st.sidebar.info(f"📊 Data: {mode_display}")

def create_athlete_name_column(df):
    """Create athlete_name column from firstname/lastname or givenname/familyname"""
    if df.empty:
        return df

    # Check for different column naming conventions
    first_col = None
    last_col = None

    if 'firstname' in df.columns:
        first_col = 'firstname'
    elif 'givenname' in df.columns:
        first_col = 'givenname'

    if 'lastname' in df.columns:
        last_col = 'lastname'
    elif 'familyname' in df.columns:
        last_col = 'familyname'

    if first_col and last_col:
        df['athlete_name'] = df[first_col].fillna('').astype(str) + ' ' + df[last_col].fillna('').astype(str)
        df['athlete_name'] = df['athlete_name'].str.strip()
    elif 'athlete_name' not in df.columns:
        # If no name columns, create empty athlete_name
        df['athlete_name'] = 'Unknown'

    return df

def normalize_column_names(df):
    """Normalize column names to expected format"""
    if df.empty:
        return df

    # Column mapping from Tilastopaja format to expected format
    column_mapping = {
        'eventname': 'event_name',
        'competitionname': 'competition_name',
        'performancevalue': 'performance',
        'mark': 'performance',
        'nat': 'nationality',
        'country': 'nationality',
        'compdate': 'date',
        'competitiondate': 'date'
    }

    # Apply mapping for columns that exist
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df[new_name] = df[old_name]

    return df

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_results():
    """Load results from Parquet (Azure Blob Storage or local cache)"""
    try:
        if PARQUET_AVAILABLE:
            df = parquet_load_results()
            if not df.empty:
                # Normalize column names to lowercase
                df.columns = df.columns.str.lower()
                # Create athlete_name from firstname/lastname
                df = create_athlete_name_column(df)
                # Normalize other column names
                df = normalize_column_names(df)
                return df
        # Fallback to local CSV
        return load_local_results()
    except Exception as e:
        st.error(f"❌ Failed to load results: {e}")
        return pd.DataFrame()

def load_local_results():
    """Load results from local CSV file"""
    csv_path = Path("data/Tilastoptija/ksaoutputipc3.csv")
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path, encoding='latin-1', low_memory=False)
            df.columns = df.columns.str.lower()
            df = create_athlete_name_column(df)
            df = normalize_column_names(df)
            return df
        except Exception as e:
            st.error(f"Failed to load local CSV: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_rankings():
    """Load rankings from Parquet (Azure Blob Storage or local cache)"""
    try:
        if PARQUET_AVAILABLE:
            df = parquet_load_rankings()
            if not df.empty:
                df.columns = df.columns.str.lower()
                return df
        # Fallback to local CSV files
        return load_local_rankings()
    except Exception as e:
        st.warning(f"Rankings load issue: {e}")
        return load_local_rankings()

@st.cache_data(ttl=300)
def load_records():
    """Load records from Parquet (Azure Blob Storage or local cache)"""
    try:
        if PARQUET_AVAILABLE:
            df = parquet_load_records()
            if not df.empty:
                df.columns = df.columns.str.lower()
                return df
        # Fallback to local CSV files
        return load_local_records()
    except Exception as e:
        st.warning(f"Records load issue: {e}")
        return load_local_records()

@st.cache_data(ttl=600)
def load_local_records():
    """Load records from local CSV files in data/Records/"""
    records_path = Path("data/Records")
    if not records_path.exists():
        return pd.DataFrame()

    all_records = []
    for csv_file in records_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            # Extract record type from filename
            filename = csv_file.stem
            if "World" in filename:
                df['record_type'] = 'World Record'
            elif "Paralympic" in filename:
                df['record_type'] = 'Paralympic Record'
            elif "Asian" in filename:
                df['record_type'] = 'Asian Record'
            elif "European" in filename:
                df['record_type'] = 'European Record'
            elif "African" in filename:
                df['record_type'] = 'African Record'
            elif "Americas" in filename:
                df['record_type'] = 'Americas Record'
            elif "Championship" in filename:
                df['record_type'] = 'Championship Record'
            elif "Oceanian" in filename:
                df['record_type'] = 'Oceanian Record'
            else:
                df['record_type'] = 'Other'
            all_records.append(df)
        except Exception as e:
            continue

    if all_records:
        return pd.concat(all_records, ignore_index=True)
    return pd.DataFrame()

@st.cache_data(ttl=600)
def load_local_rankings():
    """Load rankings from local CSV files in data/Rankings/"""
    rankings_path = Path("data/Rankings")
    if not rankings_path.exists():
        return pd.DataFrame()

    all_rankings = []
    for csv_file in rankings_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            # Extract year from filename
            parts = csv_file.stem.split("_")
            if parts:
                year = parts[-1] if parts[-1].isdigit() else "Unknown"
                df['ranking_year'] = year
            all_rankings.append(df)
        except Exception as e:
            continue

    if all_rankings:
        return pd.concat(all_rankings, ignore_index=True)
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_major_championships(results_df):
    """Filter results to major championships only"""
    if results_df.empty:
        return pd.DataFrame()

    # Filter for major championships
    major_mask = results_df['competition_name'].astype(str).str.contains(
        'World Championships|Paralympic|Asian|Para Athletics',
        case=False, na=False
    )
    major_df = results_df[major_mask].copy()

    # Add competition type classification
    major_df['competition_type'] = 'Other'
    major_df.loc[
        major_df['competition_name'].str.contains('Paralympic', case=False, na=False),
        'competition_type'
    ] = 'Paralympics'
    major_df.loc[
        major_df['competition_name'].str.contains('World Championships', case=False, na=False),
        'competition_type'
    ] = 'World Championships'
    major_df.loc[
        major_df['competition_name'].str.contains('Asian', case=False, na=False),
        'competition_type'
    ] = 'Asian Championships'

    return major_df

@lru_cache(maxsize=50000)
def parse_performance(perf_str):
    """Parse performance string to float value - cached for speed"""
    if perf_str is None or perf_str == '' or (isinstance(perf_str, float) and np.isnan(perf_str)):
        return np.nan

    perf_str = str(perf_str).strip()

    # Handle DNS, DNF, DQ, etc.
    if any(x in perf_str.upper() for x in ['DNS', 'DNF', 'DQ', 'NM', 'NH', '-']):
        return np.nan

    # Remove 'A' suffix for altitude marks
    perf_str = perf_str.rstrip('A').strip()

    # Handle time format (mm:ss.xx or hh:mm:ss.xx)
    if ':' in perf_str:
        parts = perf_str.split(':')
        try:
            if len(parts) == 2:  # mm:ss.xx
                return float(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:  # hh:mm:ss.xx
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except:
            return np.nan

    # Handle standard numeric values
    try:
        return float(perf_str)
    except:
        return np.nan

@st.cache_data(ttl=600)
def precompute_performance_values(df):
    """Pre-compute performance values for entire dataframe - cached"""
    if df.empty or 'performance' not in df.columns:
        return df
    result = df.copy()
    result['perf_value'] = result['performance'].apply(parse_performance)
    return result

def ensure_perf_value(df):
    """Ensure dataframe has perf_value column - avoids redundant computation"""
    if df.empty:
        return df
    if 'perf_value' not in df.columns and 'performance' in df.columns:
        df = df.copy()
        df['perf_value'] = df['performance'].apply(parse_performance)
    return df

def is_track_event(event_name):
    """Check if event is track (lower is better) or field (higher is better)"""
    if pd.isna(event_name):
        return False
    event_name = str(event_name).lower()
    track_events = ['100m', '200m', '400m', '800m', '1500m', '5000m', 'marathon', 'relay']
    return any(t in event_name for t in track_events)

def analyze_championship_standards(major_df, event_filter=None, classification_filter=None):
    """Analyze championship winning standards"""
    if major_df.empty:
        return pd.DataFrame()

    df = major_df.copy()

    # Apply filters
    if event_filter and event_filter != 'All':
        df = df[df['event_name'].str.contains(event_filter, case=False, na=False)]

    # Parse performance values
    df['perf_value'] = df['performance'].apply(parse_performance)
    df = df.dropna(subset=['perf_value'])

    if df.empty:
        return pd.DataFrame()

    # Group by event and competition
    standards = []
    for (event, comp), group in df.groupby(['event_name', 'competition_name']):
        if len(group) < 3:
            continue

        is_track = is_track_event(event)
        sorted_perfs = group.sort_values('perf_value', ascending=is_track)

        gold = sorted_perfs.iloc[0] if len(sorted_perfs) > 0 else None
        silver = sorted_perfs.iloc[1] if len(sorted_perfs) > 1 else None
        bronze = sorted_perfs.iloc[2] if len(sorted_perfs) > 2 else None
        final_8th = sorted_perfs.iloc[7] if len(sorted_perfs) > 7 else None

        standards.append({
            'Event': event,
            'Competition': comp,
            'Gold': gold['performance'] if gold is not None else None,
            'Gold_Athlete': gold['athlete_name'] if gold is not None else None,
            'Gold_Nation': gold['nationality'] if gold is not None else None,
            'Silver': silver['performance'] if silver is not None else None,
            'Bronze': bronze['performance'] if bronze is not None else None,
            'Final_8th': final_8th['performance'] if final_8th is not None else None,
            'Entries': len(group)
        })

    return pd.DataFrame(standards)

# Load data (cached - subsequent loads are fast)
results_df = load_results()
rankings_df = load_rankings()
records_df = load_records()

# Overview metrics
st.markdown("### 📊 Database Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Results", f"{len(results_df):,}")
with col2:
    st.metric("Rankings", f"{len(rankings_df):,}")
with col3:
    st.metric("Records", f"{len(records_df):,}")
with col4:
    unique_athletes = results_df['athlete_name'].nunique() if len(results_df) > 0 else 0
    st.metric("Unique Athletes", f"{unique_athletes:,}")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🏃 Results", "📈 Rankings", "🏆 Records", "🇸🇦 Saudi Arabia", "📊 Championship Analysis", "👤 Athlete Analysis", "📄 Event Reports"])

with tab1:
    st.markdown("### Competition Results")

    if len(results_df) > 0:
        col1, col2 = st.columns(2)

        with col1:
            # Filter by nationality
            nationalities = ['All'] + sorted(results_df['nationality'].dropna().unique().tolist())
            selected_nat = st.selectbox("Filter by Nationality", nationalities, key="results_nationality")

        with col2:
            # Filter by event
            events = ['All'] + sorted(results_df['event_name'].dropna().unique().tolist())
            selected_event = st.selectbox("Filter by Event", events, key="results_event")

        # Apply filters
        filtered_df = results_df.copy()
        if selected_nat != 'All':
            filtered_df = filtered_df[filtered_df['nationality'] == selected_nat]
        if selected_event != 'All':
            filtered_df = filtered_df[filtered_df['event_name'] == selected_event]

        st.dataframe(
            filtered_df[['competition_name', 'event_name', 'athlete_name',
                        'nationality', 'performance', 'date']].head(100),
            width='stretch',
            hide_index=True
        )

        # Top competitions chart
        st.markdown("#### Top Competitions by Results Count")
        top_comps = results_df['competition_name'].value_counts().head(10)
        fig = px.bar(
            x=top_comps.values,
            y=top_comps.index,
            orientation='h',
            labels={'x': 'Number of Results', 'y': 'Competition'}
        )
        fig.update_traces(marker_color=TEAL_PRIMARY)
        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Inter, sans-serif', color='#333')
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No results data available yet. Run the GitHub workflow to populate.")

with tab2:
    st.markdown("### IPC Rankings")

    if len(rankings_df) > 0:
        # Show year filter if available
        col1, col2 = st.columns(2)

        with col1:
            if 'ranking_year' in rankings_df.columns:
                years = ['All'] + sorted(rankings_df['ranking_year'].dropna().unique().tolist(), reverse=True)
                selected_year = st.selectbox("Filter by Year", years, key="rankings_year")
            else:
                selected_year = 'All'

        with col2:
            # Event filter
            event_col = 'Event' if 'Event' in rankings_df.columns else 'event' if 'event' in rankings_df.columns else None
            if event_col:
                events = ['All'] + sorted(rankings_df[event_col].dropna().unique().tolist())
                selected_rank_event = st.selectbox("Filter by Event", events, key="ranking_event")
            else:
                selected_rank_event = 'All'

        # Apply filters
        filtered_rankings = rankings_df.copy()
        if selected_year != 'All' and 'ranking_year' in filtered_rankings.columns:
            filtered_rankings = filtered_rankings[filtered_rankings['ranking_year'] == selected_year]
        if selected_rank_event != 'All' and event_col:
            filtered_rankings = filtered_rankings[filtered_rankings[event_col] == selected_rank_event]

        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rankings", f"{len(filtered_rankings):,}")
        with col2:
            if event_col:
                st.metric("Events", filtered_rankings[event_col].nunique())
        with col3:
            if 'ranking_year' in filtered_rankings.columns:
                st.metric("Years", rankings_df['ranking_year'].nunique())

        st.dataframe(
            filtered_rankings.head(200),
            width='stretch',
            hide_index=True
        )

        # Saudi athletes in rankings
        nat_col = 'Nat' if 'Nat' in rankings_df.columns else 'nationality' if 'nationality' in rankings_df.columns else None
        if nat_col:
            saudi_rankings = filtered_rankings[filtered_rankings[nat_col] == 'KSA']
            if len(saudi_rankings) > 0:
                st.markdown("#### Saudi Athletes in Rankings")
                st.dataframe(saudi_rankings, width='stretch', hide_index=True)
    else:
        st.info("No rankings data available. Check data/Rankings/ folder or run scrapers.")

with tab3:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0;">🏆 World Records</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Current IPC World Records by Event and Classification</p>
    </div>
    """, unsafe_allow_html=True)

    if len(records_df) > 0:
        # Filter to World Records only
        if 'record_type' in records_df.columns:
            world_records = records_df[records_df['record_type'] == 'World Record'].copy()
        else:
            world_records = records_df.copy()

        # Determine event column name
        event_col = 'Event' if 'Event' in world_records.columns else 'event' if 'event' in world_records.columns else 'event_name'

        # Event filter only
        if event_col in world_records.columns:
            events = ['All Events'] + sorted(world_records[event_col].dropna().unique().tolist())
            selected_event = st.selectbox("Filter by Event", events, key="records_event")
        else:
            selected_event = 'All Events'

        # Apply filter
        if selected_event != 'All Events' and event_col in world_records.columns:
            filtered_records = world_records[world_records[event_col] == selected_event]
        else:
            filtered_records = world_records

        # Show metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("World Records", f"{len(filtered_records):,}")
        with col2:
            if event_col in filtered_records.columns:
                st.metric("Events", filtered_records[event_col].nunique())

        # Display table
        st.dataframe(
            filtered_records.head(500),
            width='stretch',
            hide_index=True
        )

        # Download button
        csv = filtered_records.to_csv(index=False)
        st.download_button(
            label="Download World Records",
            data=csv,
            file_name="world_records.csv",
            mime="text/csv",
            key="records_download"
        )
    else:
        st.info("No records data available. Check data/Records/ folder or run scrapers.")

with tab4:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0;">🇸🇦 Saudi Arabia Athlete Profiles</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Individual athlete analysis, performance history, and championship readiness</p>
    </div>
    """, unsafe_allow_html=True)

    if len(results_df) > 0:
        saudi_df = results_df[results_df['nationality'] == 'KSA'].copy()

        if len(saudi_df) > 0:
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Results", f"{len(saudi_df):,}")
            with col2:
                saudi_athletes = saudi_df['athlete_name'].nunique()
                st.metric("Athletes", f"{saudi_athletes:,}")
            with col3:
                saudi_events = saudi_df['event_name'].nunique()
                st.metric("Events", f"{saudi_events:,}")
            with col4:
                if 'date' in saudi_df.columns:
                    try:
                        saudi_df['date_parsed'] = pd.to_datetime(saudi_df['date'], errors='coerce')
                        recent_year = saudi_df['date_parsed'].dt.year.max()
                        st.metric("Latest Year", int(recent_year) if pd.notna(recent_year) else "N/A")
                    except:
                        st.metric("Latest Year", "N/A")

            # Create subtabs for different views
            ksa_tab1, ksa_tab2, ksa_tab3, ksa_tab4 = st.tabs(["👤 Athlete Profile", "📊 Squad Overview", "📈 Performance Trends", "🏆 Top Performers"])

            with ksa_tab1:
                st.markdown("#### Individual Athlete Profile")

                # Athlete selector
                all_ksa_athletes = sorted(saudi_df['athlete_name'].dropna().unique().tolist())
                selected_athlete = st.selectbox("Select Athlete", all_ksa_athletes, key="ksa_athlete_select")

                if selected_athlete:
                    athlete_df = saudi_df[saudi_df['athlete_name'] == selected_athlete].copy()

                    # Parse performance for sorting
                    def parse_perf_value(perf, event):
                        """Parse performance string to numeric value"""
                        try:
                            perf_str = str(perf)
                            if ':' in perf_str:
                                parts = perf_str.split(':')
                                if len(parts) == 2:
                                    return float(parts[0]) * 60 + float(parts[1])
                                elif len(parts) == 3:
                                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                            return float(perf_str)
                        except:
                            return None

                    athlete_df['perf_numeric'] = athlete_df.apply(
                        lambda row: parse_perf_value(row.get('performance', ''), row.get('event_name', '')), axis=1
                    )

                    # Athlete header card
                    events_competed = athlete_df['event_name'].nunique()
                    total_results = len(athlete_df)
                    competitions = athlete_df['competition_name'].nunique() if 'competition_name' in athlete_df.columns else 0

                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                        <h2 style="color: white; margin: 0;">{selected_athlete}</h2>
                        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">
                            🇸🇦 Saudi Arabia | {events_competed} Events | {total_results} Results | {competitions} Competitions
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Personal Bests by Event
                    st.markdown("##### Personal Bests by Event")

                    # Group by event and find best performance
                    pb_data = []
                    for event in athlete_df['event_name'].unique():
                        event_results = athlete_df[athlete_df['event_name'] == event]
                        event_results = event_results[event_results['perf_numeric'].notna()]

                        if len(event_results) > 0:
                            # Determine if lower is better (time events)
                            is_time_event = any(x in str(event).lower() for x in ['m', 'metre', 'meter', 'marathon']) and \
                                           not any(x in str(event).lower() for x in ['throw', 'put', 'jump', 'discus', 'javelin', 'shot'])

                            if is_time_event:
                                best_row = event_results.loc[event_results['perf_numeric'].idxmin()]
                            else:
                                best_row = event_results.loc[event_results['perf_numeric'].idxmax()]

                            pb_data.append({
                                'Event': event,
                                'PB': best_row.get('performance', ''),
                                'Date': best_row.get('date', ''),
                                'Competition': best_row.get('competition_name', ''),
                                'Results': len(event_results)
                            })

                    if pb_data:
                        pb_df = pd.DataFrame(pb_data)
                        # Display as styled cards
                        cols = st.columns(min(3, len(pb_data)))
                        for i, row in enumerate(pb_data[:6]):  # Show top 6 events
                            with cols[i % 3]:
                                st.markdown(f"""
                                <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {GOLD_ACCENT}; margin-bottom: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <p style="color: {TEAL_PRIMARY}; font-weight: bold; margin: 0; font-size: 0.9rem;">{row['Event']}</p>
                                    <p style="color: #333; font-size: 1.5rem; font-weight: bold; margin: 0.25rem 0;">{row['PB']}</p>
                                    <p style="color: #666; font-size: 0.75rem; margin: 0;">{row['Results']} results</p>
                                </div>
                                """, unsafe_allow_html=True)

                    # Competition History
                    st.markdown("##### Competition History")

                    # Sort by date descending
                    if 'date_parsed' in athlete_df.columns:
                        history_df = athlete_df.sort_values('date_parsed', ascending=False)
                    else:
                        history_df = athlete_df

                    display_cols = ['date', 'event_name', 'performance', 'competition_name']
                    if 'position' in history_df.columns:
                        display_cols.insert(3, 'position')

                    display_cols = [c for c in display_cols if c in history_df.columns]
                    st.dataframe(
                        history_df[display_cols].head(20),
                        width='stretch',
                        hide_index=True,
                        column_config={
                            'date': 'Date',
                            'event_name': 'Event',
                            'performance': 'Performance',
                            'position': 'Position',
                            'competition_name': 'Competition'
                        }
                    )

                    # Performance Progression Chart
                    st.markdown("##### Performance Progression")

                    # Event filter for chart
                    chart_events = sorted(athlete_df['event_name'].dropna().unique().tolist())
                    if chart_events:
                        chart_event = st.selectbox("Select Event for Progression", chart_events, key="athlete_chart_event")

                        event_data = athlete_df[
                            (athlete_df['event_name'] == chart_event) &
                            (athlete_df['perf_numeric'].notna())
                        ].copy()

                        if len(event_data) > 1 and 'date_parsed' in event_data.columns:
                            event_data = event_data.sort_values('date_parsed')

                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=event_data['date_parsed'],
                                y=event_data['perf_numeric'],
                                mode='lines+markers',
                                name='Performance',
                                line=dict(color=TEAL_PRIMARY, width=2),
                                marker=dict(size=8, color=TEAL_PRIMARY),
                                text=event_data['performance'],
                                hovertemplate='%{x}<br>Performance: %{text}<extra></extra>'
                            ))

                            # Add PB line
                            is_time_event = any(x in str(chart_event).lower() for x in ['m', 'metre', 'meter', 'marathon']) and \
                                           not any(x in str(chart_event).lower() for x in ['throw', 'put', 'jump', 'discus', 'javelin', 'shot'])
                            pb_value = event_data['perf_numeric'].min() if is_time_event else event_data['perf_numeric'].max()

                            fig.add_hline(y=pb_value, line_dash="dash", line_color=GOLD_ACCENT,
                                         annotation_text="PB", annotation_position="right")

                            fig.update_layout(
                                title=f'{chart_event} Progression',
                                xaxis_title='Date',
                                yaxis_title='Performance',
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                font=dict(family='Inter, sans-serif', color='#333'),
                                height=400
                            )
                            st.plotly_chart(fig, width='stretch')
                        elif len(event_data) <= 1:
                            st.info(f"Need more results for {chart_event} to show progression")

            with ksa_tab2:
                st.markdown("#### Saudi Squad Overview")

                # Group athletes by event
                athlete_events = saudi_df.groupby(['athlete_name', 'event_name']).agg({
                    'performance': 'count',
                    'competition_name': 'nunique'
                }).reset_index()
                athlete_events.columns = ['Athlete', 'Event', 'Results', 'Competitions']

                # Filter by event
                all_events = ['All'] + sorted(saudi_df['event_name'].dropna().unique().tolist())
                squad_event = st.selectbox("Filter by Event", all_events, key="squad_event_filter")

                if squad_event != 'All':
                    squad_df = athlete_events[athlete_events['Event'] == squad_event]
                else:
                    squad_df = athlete_events

                st.dataframe(
                    squad_df.sort_values(['Event', 'Results'], ascending=[True, False]),
                    width='stretch',
                    hide_index=True
                )

                # Event coverage chart
                st.markdown("#### Event Coverage")
                event_counts = saudi_df.groupby('event_name')['athlete_name'].nunique().sort_values(ascending=True).tail(15)

                fig = px.bar(
                    x=event_counts.values,
                    y=event_counts.index,
                    orientation='h',
                    labels={'x': 'Number of Athletes', 'y': 'Event'}
                )
                fig.update_traces(marker_color=TEAL_PRIMARY)
                fig.update_layout(
                    title='Athletes per Event',
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family='Inter, sans-serif', color='#333'),
                    height=500
                )
                st.plotly_chart(fig, width='stretch')

            with ksa_tab3:
                st.markdown("#### Performance Trends")

                # Year-over-year analysis
                if 'date_parsed' in saudi_df.columns:
                    saudi_df['year'] = saudi_df['date_parsed'].dt.year

                    yearly_stats = saudi_df.groupby('year').agg({
                        'athlete_name': 'nunique',
                        'event_name': 'nunique',
                        'competition_name': 'nunique'
                    }).reset_index()
                    yearly_stats.columns = ['Year', 'Athletes', 'Events', 'Competitions']
                    yearly_stats = yearly_stats[yearly_stats['Year'] > 2010]

                    if not yearly_stats.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=yearly_stats['Year'],
                            y=yearly_stats['Athletes'],
                            name='Athletes',
                            marker_color=TEAL_PRIMARY
                        ))
                        fig.add_trace(go.Scatter(
                            x=yearly_stats['Year'],
                            y=yearly_stats['Competitions'],
                            name='Competitions',
                            mode='lines+markers',
                            line=dict(color=GOLD_ACCENT, width=2),
                            yaxis='y2'
                        ))

                        fig.update_layout(
                            title='Saudi Para Athletics Growth',
                            xaxis_title='Year',
                            yaxis=dict(title='Athletes', side='left'),
                            yaxis2=dict(title='Competitions', side='right', overlaying='y'),
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            font=dict(family='Inter, sans-serif', color='#333'),
                            height=400,
                            legend=dict(x=0.01, y=0.99)
                        )
                        st.plotly_chart(fig, width='stretch')

                        # Yearly breakdown table
                        st.dataframe(yearly_stats.sort_values('Year', ascending=False), width='stretch', hide_index=True)

            with ksa_tab4:
                st.markdown("#### Top Saudi Performers")

                # Load championship standards for comparison
                standards_path = Path("championship_standards_report.csv")
                if standards_path.exists():
                    standards_df_local = pd.read_csv(standards_path)
                    saudi_standards = standards_df_local[standards_df_local['saudi_best'].notna()]

                    if not saudi_standards.empty:
                        # Show athletes closest to medals
                        st.markdown("##### Medal Contenders (Closest to Gold)")

                        # Filter for those with gap data
                        contenders = saudi_standards[saudi_standards['gap_to_para_gold'].notna()].copy()
                        contenders = contenders.sort_values('gap_to_para_gold')

                        # Display top contenders
                        for i, row in contenders.head(10).iterrows():
                            gap = row['gap_to_para_gold']
                            gap_color = GOLD_ACCENT if gap <= 0 else (TEAL_PRIMARY if gap <= 0.5 else GRAY_BLUE)
                            status = "🥇 GOLD LEVEL" if gap <= 0 else ("🎯 CLOSE" if gap <= 0.5 else "📈 DEVELOPING")

                            st.markdown(f"""
                            <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {gap_color}; margin-bottom: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <p style="color: {TEAL_PRIMARY}; font-weight: bold; margin: 0;">{row['saudi_best_athlete']}</p>
                                        <p style="color: #666; font-size: 0.85rem; margin: 0;">{row['event']} {row['classification']} ({row['gender']})</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <p style="color: #333; font-weight: bold; margin: 0;">{row['saudi_best']:.2f}</p>
                                        <p style="color: {gap_color}; font-size: 0.85rem; margin: 0;">Gap: {gap:+.2f} | {status}</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Run `python championship_winning_standards.py` to generate medal contender analysis")

                # Most active athletes
                st.markdown("##### Most Active Athletes")
                active_athletes = saudi_df.groupby('athlete_name').agg({
                    'event_name': 'count',
                    'competition_name': 'nunique'
                }).reset_index()
                active_athletes.columns = ['Athlete', 'Total Results', 'Competitions']
                active_athletes = active_athletes.sort_values('Total Results', ascending=False).head(15)

                fig = px.bar(
                    active_athletes,
                    x='Total Results',
                    y='Athlete',
                    orientation='h',
                    color='Competitions',
                    color_continuous_scale=[TEAL_LIGHT, TEAL_PRIMARY, TEAL_DARK]
                )
                fig.update_layout(
                    title='Most Active Saudi Athletes',
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family='Inter, sans-serif', color='#333'),
                    height=500
                )
                st.plotly_chart(fig, width='stretch')

        else:
            st.warning("No Saudi Arabia (KSA) results found in database yet.")
    else:
        st.info("No results data available yet. Run the GitHub workflow to populate.")

with tab5:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0;">Championship Standards & Gap Analysis</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Medal standards, world records, and Saudi athlete gap analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # Load enhanced championship standards report
    @st.cache_data(ttl=300)
    def load_championship_standards():
        """Load the enhanced championship standards report"""
        standards_path = Path("championship_standards_report.csv")
        if standards_path.exists():
            return pd.read_csv(standards_path)
        return pd.DataFrame()

    standards_df = load_championship_standards()

    if not standards_df.empty:
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Event/Class Combinations", f"{len(standards_df):,}")
        with col2:
            unique_events = standards_df['event'].nunique()
            st.metric("Events", f"{unique_events:,}")
        with col3:
            unique_classes = standards_df['classification'].nunique()
            st.metric("Classifications", f"{unique_classes:,}")
        with col4:
            saudi_with_data = standards_df[standards_df['saudi_best'].notna()]
            st.metric("Saudi Athletes Tracked", f"{len(saudi_with_data):,}")

        # Filters
        st.markdown("#### Filters")
        col1, col2, col3 = st.columns(3)
        with col1:
            events = ['All'] + sorted(standards_df['event'].dropna().unique().tolist())
            selected_event = st.selectbox("Event", events, key="std_event")
        with col2:
            classes = ['All'] + sorted(standards_df['classification'].dropna().unique().tolist())
            selected_class = st.selectbox("Classification", classes, key="std_class")
        with col3:
            genders = ['All', 'M', 'W']
            selected_gender = st.selectbox("Gender", genders, key="std_gender")

        # Apply filters
        filtered_df = standards_df.copy()
        if selected_event != 'All':
            filtered_df = filtered_df[filtered_df['event'] == selected_event]
        if selected_class != 'All':
            filtered_df = filtered_df[filtered_df['classification'] == selected_class]
        if selected_gender != 'All':
            filtered_df = filtered_df[filtered_df['gender'] == selected_gender]

        st.markdown(f"**Showing {len(filtered_df)} of {len(standards_df)} combinations**")

        # Create subtabs for different views
        subtab1, subtab2, subtab3, subtab4 = st.tabs(["📊 Standards Table", "🇸🇦 Saudi Gap Analysis", "📈 Comparisons", "🏅 Medal Targets"])

        with subtab1:
            st.markdown("#### Championship Standards Table")

            # Select columns to display
            display_cols = ['event', 'classification', 'gender', 'world_record_display',
                          'paralympics_gold', 'paralympics_bronze', 'paralympics_8th_place',
                          'wc_gold', 'wc_bronze', 'wc_8th_place',
                          'asian_gold', 'asian_bronze', 'total_results']

            # Only include columns that exist
            display_cols = [c for c in display_cols if c in filtered_df.columns]
            display_df = filtered_df[display_cols].copy()

            # Rename for display
            rename_map = {
                'world_record_display': 'World Record',
                'paralympics_gold': 'Para Gold',
                'paralympics_bronze': 'Para Bronze',
                'paralympics_8th_place': 'Para 8th',
                'wc_gold': 'WC Gold',
                'wc_bronze': 'WC Bronze',
                'wc_8th_place': 'WC 8th',
                'asian_gold': 'Asian Gold',
                'asian_bronze': 'Asian Bronze',
                'total_results': 'Results'
            }
            display_df = display_df.rename(columns=rename_map)

            st.dataframe(display_df, width='stretch', hide_index=True)

            # Download
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download Full Standards Data",
                data=csv,
                file_name="championship_standards_full.csv",
                mime="text/csv",
                key="standards_download"
            )

        with subtab2:
            st.markdown("#### Saudi Athlete Gap Analysis")

            # Filter to Saudi data only
            saudi_df = filtered_df[filtered_df['saudi_best'].notna()].copy()

            if not saudi_df.empty:
                # Gap analysis metrics
                col1, col2, col3 = st.columns(3)

                # Count medal-ready athletes (gap <= 0 means they can medal)
                can_gold = len(saudi_df[saudi_df['gap_to_para_gold'] <= 0]) if 'gap_to_para_gold' in saudi_df.columns else 0
                can_bronze = len(saudi_df[saudi_df['gap_to_para_bronze'] <= 0]) if 'gap_to_para_bronze' in saudi_df.columns else 0
                can_finals = len(saudi_df[saudi_df['gap_to_para_8th'] <= 0]) if 'gap_to_para_8th' in saudi_df.columns else 0

                with col1:
                    st.markdown(f"""
                    <div style="background: {GOLD_ACCENT}; padding: 1rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.85rem;">Medal Contenders (Gold)</p>
                        <p style="color: white; margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: bold;">{can_gold}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style="background: {TEAL_PRIMARY}; padding: 1rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.85rem;">Medal Contenders (Bronze)</p>
                        <p style="color: white; margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: bold;">{can_bronze}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div style="background: {TEAL_LIGHT}; padding: 1rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.85rem;">Finals Contenders (8th)</p>
                        <p style="color: white; margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: bold;">{can_finals}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("#### Saudi Athlete Performance vs Standards")

                # Display Saudi gap analysis table
                gap_cols = ['event', 'classification', 'gender', 'saudi_best', 'saudi_best_athlete',
                           'paralympics_gold', 'gap_to_para_gold', 'gap_to_para_bronze', 'gap_to_para_8th',
                           'saudi_world_rank']
                gap_cols = [c for c in gap_cols if c in saudi_df.columns]
                gap_df = saudi_df[gap_cols].copy()

                # Rename for display
                gap_rename = {
                    'saudi_best': 'Saudi Best',
                    'saudi_best_athlete': 'Athlete',
                    'paralympics_gold': 'Gold Std',
                    'gap_to_para_gold': 'Gap to Gold',
                    'gap_to_para_bronze': 'Gap to Bronze',
                    'gap_to_para_8th': 'Gap to 8th',
                    'saudi_world_rank': 'World Rank'
                }
                gap_df = gap_df.rename(columns=gap_rename)

                # Style the dataframe - highlight athletes close to medals
                st.dataframe(gap_df, width='stretch', hide_index=True)

                # Gap visualization with championship type selector
                if len(saudi_df) > 0:
                    st.markdown("#### Gap to Gold Standard (by Event)")

                    # Championship type selector
                    champ_type = st.radio(
                        "Select Championship Type",
                        ["Paralympics", "World Championships", "Asian Championships"],
                        horizontal=True,
                        key="gap_champ_type"
                    )

                    # Map selection to column names
                    gap_col_map = {
                        "Paralympics": "gap_to_para_gold",
                        "World Championships": "gap_to_wc_gold",
                        "Asian Championships": "gap_to_asian_gold"
                    }
                    gold_col_map = {
                        "Paralympics": "paralympics_gold",
                        "World Championships": "wc_gold",
                        "Asian Championships": "asian_gold"
                    }

                    # Calculate gaps for WC and Asian if not present
                    gap_col = gap_col_map[champ_type]
                    gold_col = gold_col_map[champ_type]

                    # Create gap column if needed
                    if gap_col not in saudi_df.columns and gold_col in saudi_df.columns:
                        # Determine if time event for gap calculation
                        def calc_gap(row):
                            if pd.isna(row['saudi_best']) or pd.isna(row.get(gold_col)):
                                return None
                            return row['saudi_best'] - row[gold_col]
                        saudi_df[gap_col] = saudi_df.apply(calc_gap, axis=1)

                    if gap_col in saudi_df.columns:
                        cols_needed = ['event', 'classification', 'gender', gap_col, 'saudi_best_athlete']
                        cols_available = [c for c in cols_needed if c in saudi_df.columns]
                        chart_df = saudi_df[cols_available].dropna()
                        chart_df['event_class'] = chart_df['event'] + ' ' + chart_df['classification'] + ' (' + chart_df['gender'] + ')'

                        if not chart_df.empty:
                            # Sort by gap
                            chart_df = chart_df.sort_values(gap_col)

                            # Color based on gap
                            chart_df['color'] = chart_df[gap_col].apply(
                                lambda x: GOLD_ACCENT if x <= 0 else (TEAL_PRIMARY if x <= 0.5 else GRAY_BLUE)
                            )

                            fig = go.Figure()
                            fig.add_trace(go.Bar(
                                y=chart_df['event_class'],
                                x=chart_df[gap_col],
                                orientation='h',
                                marker_color=chart_df['color'],
                                text=chart_df['saudi_best_athlete'],
                                textposition='auto',
                                hovertemplate='%{y}<br>Gap: %{x:.2f}s<br>Athlete: %{text}<extra></extra>'
                            ))
                            fig.add_vline(x=0, line_dash="dash", line_color=GOLD_ACCENT, annotation_text="Gold Standard")
                            fig.update_layout(
                                title=f'Gap to {champ_type} Gold (negative = faster than gold)',
                                xaxis_title='Gap (seconds - negative is better for track events)',
                                yaxis_title='',
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                font=dict(family='Inter, sans-serif', color='#333'),
                                height=max(400, len(chart_df) * 30)
                            )
                            st.plotly_chart(fig, width='stretch')
                        else:
                            st.info(f"No gap data available for {champ_type}")
                    else:
                        st.info(f"No {champ_type} gold standards available for comparison")
            else:
                st.info("No Saudi athlete data found for the selected filters.")

        with subtab3:
            st.markdown("#### Championships Comparison")

            if not filtered_df.empty:
                # Compare Paralympics vs World Championships vs Asian - Grid Layout
                available_cols = ['event', 'classification', 'gender']
                for col in ['paralympics_gold', 'paralympics_bronze', 'wc_gold', 'wc_bronze', 'asian_gold', 'asian_bronze']:
                    if col in filtered_df.columns:
                        available_cols.append(col)

                compare_df = filtered_df[available_cols].head(20)

                if not compare_df.empty:
                    compare_df['Event'] = compare_df['event'] + ' ' + compare_df['classification']

                    # Create comparison metrics grid - 3 columns
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                        <div style="background: {TEAL_PRIMARY}; padding: 0.75rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;">
                            <p style="color: white; margin: 0; font-weight: bold;">Paralympics</p>
                        </div>
                        """, unsafe_allow_html=True)
                        para_cols = ['Event'] + [c for c in ['paralympics_gold', 'paralympics_bronze'] if c in compare_df.columns]
                        para_data = compare_df[para_cols].dropna(subset=[c for c in para_cols if c != 'Event'])
                        para_data.columns = ['Event'] + ['Gold' if 'gold' in c else 'Bronze' for c in para_cols[1:]]
                        if len(para_data) > 0:
                            st.dataframe(para_data, width='stretch', hide_index=True, height=350)
                        else:
                            st.info("No data")

                    with col2:
                        st.markdown(f"""
                        <div style="background: {GOLD_ACCENT}; padding: 0.75rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;">
                            <p style="color: white; margin: 0; font-weight: bold;">World Championships</p>
                        </div>
                        """, unsafe_allow_html=True)
                        wc_cols = ['Event'] + [c for c in ['wc_gold', 'wc_bronze'] if c in compare_df.columns]
                        wc_data = compare_df[wc_cols].dropna(subset=[c for c in wc_cols if c != 'Event'])
                        wc_data.columns = ['Event'] + ['Gold' if 'gold' in c else 'Bronze' for c in wc_cols[1:]]
                        if len(wc_data) > 0:
                            st.dataframe(wc_data, width='stretch', hide_index=True, height=350)
                        else:
                            st.info("No data")

                    with col3:
                        st.markdown(f"""
                        <div style="background: {TEAL_LIGHT}; padding: 0.75rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;">
                            <p style="color: white; margin: 0; font-weight: bold;">Asian Championships</p>
                        </div>
                        """, unsafe_allow_html=True)
                        asian_cols = ['Event'] + [c for c in ['asian_gold', 'asian_bronze'] if c in compare_df.columns]
                        asian_data = compare_df[asian_cols].dropna(subset=[c for c in asian_cols if c != 'Event'])
                        asian_data.columns = ['Event'] + ['Gold' if 'gold' in c else 'Bronze' for c in asian_cols[1:]]
                        if len(asian_data) > 0:
                            st.dataframe(asian_data, width='stretch', hide_index=True, height=350)
                        else:
                            st.info("No data")

        with subtab4:
            st.markdown("#### Medal Target Calculator")

            # Dynamic cascading filters - each selection filters the next dropdown
            col1, col2, col3 = st.columns(3)

            with col1:
                # Event selection
                all_events = sorted(standards_df['event'].unique().tolist())
                target_event = st.selectbox("Target Event", all_events, key="target_event")

            with col2:
                # Classification - filtered by selected event
                event_filtered = standards_df[standards_df['event'] == target_event]
                available_classes = sorted(event_filtered['classification'].unique().tolist())
                target_class = st.selectbox("Target Classification", available_classes, key="target_class")

            with col3:
                # Gender - filtered by selected event AND classification
                event_class_filtered = standards_df[
                    (standards_df['event'] == target_event) &
                    (standards_df['classification'] == target_class)
                ]
                available_genders = sorted(event_class_filtered['gender'].unique().tolist())
                # Map to display names
                gender_display = {'M': 'Men', 'W': 'Women'}
                gender_options = [gender_display.get(g, g) for g in available_genders]

                if gender_options:
                    selected_gender_display = st.selectbox("Gender", gender_options, key="target_gender")
                    # Map back to M/W
                    target_gender = 'M' if selected_gender_display == 'Men' else 'W'
                else:
                    st.warning("No gender data available")
                    target_gender = None

            # Only proceed if we have a valid gender selection
            if target_gender:
                target_row = standards_df[
                    (standards_df['event'] == target_event) &
                    (standards_df['classification'] == target_class) &
                    (standards_df['gender'] == target_gender)
                ]
            else:
                target_row = pd.DataFrame()

            if not target_row.empty:
                row = target_row.iloc[0]

                st.markdown(f"### {target_event} {target_class} ({'Men' if target_gender == 'M' else 'Women'})")

                # Display targets
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    wr = row.get('world_record_display', 'N/A')
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {GOLD_ACCENT} 0%, #c9a227 100%); padding: 1.5rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.8rem;">WORLD RECORD</p>
                        <p style="color: white; margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: bold;">{wr if wr else 'N/A'}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    gold = row.get('paralympics_gold')
                    gold_display = f"{gold:.2f}" if pd.notna(gold) else 'N/A'
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%); padding: 1.5rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.8rem;">GOLD TARGET</p>
                        <p style="color: white; margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: bold;">{gold_display}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    bronze = row.get('paralympics_bronze')
                    bronze_display = f"{bronze:.2f}" if pd.notna(bronze) else 'N/A'
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #CD7F32 0%, #a86b28 100%); padding: 1.5rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.8rem;">BRONZE TARGET</p>
                        <p style="color: white; margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: bold;">{bronze_display}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    eighth = row.get('paralympics_8th_place')
                    eighth_display = f"{eighth:.2f}" if pd.notna(eighth) else 'N/A'
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {GRAY_BLUE} 0%, #5f7682 100%); padding: 1.5rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.8rem;">FINALS TARGET</p>
                        <p style="color: white; margin: 0.5rem 0 0 0; font-size: 1.8rem; font-weight: bold;">{eighth_display}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Saudi athlete status
                st.markdown("---")
                saudi_best = row.get('saudi_best')
                saudi_athlete = row.get('saudi_best_athlete')

                if pd.notna(saudi_best):
                    st.markdown(f"#### Saudi Athlete Status: **{saudi_athlete}**")

                    gap_gold = row.get('gap_to_para_gold')
                    gap_bronze = row.get('gap_to_para_bronze')
                    gap_8th = row.get('gap_to_para_8th')

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Saudi Best", f"{saudi_best:.2f}")
                    with col2:
                        if pd.notna(gap_gold):
                            delta_color = "normal" if gap_gold <= 0 else "inverse"
                            st.metric("Gap to Gold", f"{gap_gold:+.2f}", delta_color=delta_color)
                    with col3:
                        if pd.notna(gap_bronze):
                            delta_color = "normal" if gap_bronze <= 0 else "inverse"
                            st.metric("Gap to Bronze", f"{gap_bronze:+.2f}", delta_color=delta_color)
                    with col4:
                        if pd.notna(gap_8th):
                            delta_color = "normal" if gap_8th <= 0 else "inverse"
                            st.metric("Gap to Finals", f"{gap_8th:+.2f}", delta_color=delta_color)

                    # Medal probability indicator
                    if pd.notna(gap_gold) and gap_gold <= 0:
                        st.success(f"**{saudi_athlete}** is performing at GOLD medal level!")
                    elif pd.notna(gap_bronze) and gap_bronze <= 0:
                        st.info(f"**{saudi_athlete}** is performing at MEDAL level (Bronze or better possible)")
                    elif pd.notna(gap_8th) and gap_8th <= 0:
                        st.warning(f"**{saudi_athlete}** can make FINALS - needs {abs(gap_bronze):.2f} improvement for medal")
                    else:
                        if pd.notna(gap_8th):
                            st.error(f"**{saudi_athlete}** needs {abs(gap_8th):.2f} improvement to reach finals")
                else:
                    st.info(f"No Saudi athlete data for {target_event} {target_class}")
            else:
                st.warning("No data found for selected event/classification/gender combination")
    else:
        st.warning("Championship standards report not found. Run `python championship_winning_standards.py` to generate.")

with tab6:
    st.markdown("### Athlete Analysis & Event Comparison")

    if len(results_df) > 0:
        # Filters row
        col1, col2, col3 = st.columns(3)

        with col1:
            # Country filter
            all_countries = sorted(results_df['nationality'].dropna().unique().tolist())
            selected_country = st.selectbox("Filter by Country", ['All'] + all_countries, key="athlete_country")

        # Filter athletes by country
        if selected_country != 'All':
            filtered_for_athletes = results_df[results_df['nationality'] == selected_country]
        else:
            filtered_for_athletes = results_df

        with col2:
            all_athletes = sorted(filtered_for_athletes['athlete_name'].dropna().unique().tolist())
            selected_athlete = st.selectbox("Select Athlete", [''] + all_athletes, key="athlete_search")

        with col3:
            # Event comparison selector
            all_events = sorted(results_df['event_name'].dropna().unique().tolist())
            compare_event = st.selectbox("Compare Event Standards", [''] + all_events, key="compare_event")

        if selected_athlete:
            st.markdown(f"## {selected_athlete}")

            athlete_data = results_df[results_df['athlete_name'] == selected_athlete].copy()

            # Athlete overview
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Performances", len(athlete_data))
            with col2:
                st.metric("Competitions", athlete_data['competition_name'].nunique())
            with col3:
                st.metric("Events", athlete_data['event_name'].nunique())
            with col4:
                nationality = athlete_data['nationality'].iloc[0] if len(athlete_data) > 0 else "Unknown"
                st.metric("Nationality", nationality)

            # Events competed
            st.markdown("#### Events Competed")
            event_counts = athlete_data['event_name'].value_counts()
            fig = px.bar(
                x=event_counts.index,
                y=event_counts.values,
                labels={'x': 'Event', 'y': 'Performances'}
            )
            fig.update_traces(marker_color=TEAL_PRIMARY)
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', color='#333'),
                xaxis_tickangle=-45,
                height=300
            )
            st.plotly_chart(fig, width='stretch')

            # Performance history
            st.markdown("#### Performance History")
            st.dataframe(
                athlete_data[['competition_name', 'event_name', 'performance', 'date']].sort_values('date', ascending=False),
                width='stretch',
                hide_index=True
            )

            # Compare to championship standards
            if compare_event:
                st.markdown(f"#### {selected_athlete} vs Championship Standards - {compare_event}")

                athlete_event_data = athlete_data[athlete_data['event_name'].str.contains(compare_event, case=False, na=False)]

                if len(athlete_event_data) > 0:
                    athlete_best = athlete_event_data['performance'].iloc[0]
                    athlete_perf_val = parse_performance(athlete_best)

                    # Get championship standards for this event
                    major_df = get_major_championships(results_df)
                    event_standards = analyze_championship_standards(major_df, compare_event)

                    if not event_standards.empty and athlete_perf_val:
                        st.markdown(f"**Athlete's Best: {athlete_best}**")

                        # Show gap to medal standards
                        for _, row in event_standards.iterrows():
                            gold_val = parse_performance(row['Gold']) if pd.notna(row['Gold']) else None
                            bronze_val = parse_performance(row['Bronze']) if pd.notna(row['Bronze']) else None

                            if gold_val and bronze_val:
                                is_track = is_track_event(compare_event)

                                if is_track:
                                    gold_gap = athlete_perf_val - gold_val
                                    bronze_gap = athlete_perf_val - bronze_val
                                    gold_status = "ahead" if gold_gap < 0 else "behind"
                                    bronze_status = "ahead" if bronze_gap < 0 else "behind"
                                else:
                                    gold_gap = gold_val - athlete_perf_val
                                    bronze_gap = bronze_val - athlete_perf_val
                                    gold_status = "behind" if gold_gap > 0 else "ahead"
                                    bronze_status = "behind" if bronze_gap > 0 else "ahead"

                                st.markdown(f"**{row['Competition']}**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"Gold: {row['Gold']} ({abs(gold_gap):.2f} {gold_status})")
                                with col2:
                                    st.markdown(f"Bronze: {row['Bronze']} ({abs(bronze_gap):.2f} {bronze_status})")
                else:
                    st.info(f"No performances found for {selected_athlete} in {compare_event}")

        # Event leaderboard
        st.markdown("---")
        st.markdown("#### Event Leaderboard")

        leaderboard_event = st.selectbox("Select Event for Leaderboard", [''] + all_events, key="leaderboard_event")

        if leaderboard_event:
            event_results = results_df[results_df['event_name'].str.contains(leaderboard_event, case=False, na=False)].copy()
            event_results['perf_value'] = event_results['performance'].apply(parse_performance)
            event_results = event_results.dropna(subset=['perf_value'])

            is_track = is_track_event(leaderboard_event)
            event_results = event_results.sort_values('perf_value', ascending=is_track)

            # Top performers
            top_performers = event_results.groupby('athlete_name').agg({
                'performance': 'first',
                'perf_value': 'min' if is_track else 'max',
                'nationality': 'first',
                'competition_name': 'count'
            }).reset_index()
            top_performers.columns = ['Athlete', 'Best Performance', 'Performance Value', 'Nationality', 'Total Results']
            top_performers = top_performers.sort_values('Performance Value', ascending=is_track).head(20)

            st.dataframe(
                top_performers[['Athlete', 'Best Performance', 'Nationality', 'Total Results']],
                width='stretch',
                hide_index=True
            )
    else:
        st.info("No results data available yet. Run the GitHub workflow to populate.")

# Tab 7: Event Reports (Pre-Competition Analysis)
with tab7:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0;">Event Reports</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Pre-Competition Championship Analysis - Similar to PDF Reports</p>
    </div>
    """, unsafe_allow_html=True)

    if len(results_df) > 0:
        # Event selection filters - simplified
        col1, col2, col3 = st.columns(3)

        with col1:
            # Get unique events
            report_events = sorted(results_df['event_name'].dropna().unique().tolist())
            selected_report_event = st.selectbox("Select Event", ['-- Select Event --'] + report_events, key="tab7_event")

        with col2:
            # Get classifications for selected event
            if selected_report_event and selected_report_event != '-- Select Event --':
                event_data = results_df[results_df['event_name'] == selected_report_event]
                if 'classification' in event_data.columns:
                    report_classes = sorted(event_data['classification'].dropna().unique().tolist())
                else:
                    report_classes = []
            else:
                report_classes = []

            selected_report_class = st.selectbox("Select Classification", ['-- Select Class --'] + report_classes, key="tab7_class")

        with col3:
            selected_report_gender = st.selectbox("Select Gender", ['-- Select Gender --', 'M', 'W'], key="tab7_gender",
                                                   format_func=lambda x: {'-- Select Gender --': 'Select Gender...', 'M': 'Men', 'W': 'Women'}.get(x, x))

        # Check if all filters are selected
        filters_complete = (selected_report_event and selected_report_event != '-- Select Event --' and
                           selected_report_class and selected_report_class != '-- Select Class --' and
                           selected_report_gender and selected_report_gender != '-- Select Gender --')

        if filters_complete:
            gender_name = "Men" if selected_report_gender == 'M' else "Women"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {GOLD_ACCENT} 0%, #c9a227 100%); padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center;">
                <h3 style="color: white; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">{selected_report_event} {selected_report_class} - {gender_name}</h3>
            </div>
            """, unsafe_allow_html=True)

            # Create report sections as expandable panels
            report_tab1, report_tab2, report_tab3, report_tab4, report_tab5 = st.tabs([
                "🏅 Championship Standards",
                "👥 Competition Field",
                "📊 Historical Data",
                "📈 Performance Analysis",
                "🇸🇦 Saudi Context"
            ])

            # Filter data for this event-class-gender (exact match, no regex)
            event_filter = results_df['event_name'] == selected_report_event
            class_filter = results_df['classification'] == selected_report_class if 'classification' in results_df.columns else pd.Series([True] * len(results_df))

            # Gender filter - check multiple possible gender columns/formats
            gender_filter = pd.Series([True] * len(results_df))
            if 'gender' in results_df.columns:
                gender_filter = results_df['gender'] == selected_report_gender
            elif 'sex' in results_df.columns:
                gender_filter = results_df['sex'] == selected_report_gender

            filtered_event_df = results_df[event_filter & class_filter & gender_filter].copy()
            major_event_df = get_major_championships(filtered_event_df)

            # Section 1: Championship Standards
            with report_tab1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
                     padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {GOLD_ACCENT};">
                    <h3 style="color: white; margin: 0;">Championship Medal Standards</h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">World Championships vs Paralympics Comparison</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                # World Championships Standards
                with col1:
                    st.markdown("#### World Championships")
                    wc_df = major_event_df[major_event_df['competition_name'].str.contains('World Championships|World Champ', case=False, na=False)].copy()

                    if len(wc_df) > 0:
                        wc_df['perf_value'] = wc_df['performance'].apply(parse_performance)
                        wc_df = wc_df.dropna(subset=['perf_value'])

                        is_track = is_track_event(selected_report_event)
                        wc_df = wc_df.sort_values('perf_value', ascending=is_track)

                        # Get medal standards
                        wc_standards = []
                        if len(wc_df) >= 1:
                            wc_standards.append({"Position": "Gold (1st)", "Performance": wc_df.iloc[0]['performance'], "Athlete": wc_df.iloc[0]['athlete_name']})
                        if len(wc_df) >= 2:
                            wc_standards.append({"Position": "Silver (2nd)", "Performance": wc_df.iloc[1]['performance'], "Athlete": wc_df.iloc[1]['athlete_name']})
                        if len(wc_df) >= 3:
                            wc_standards.append({"Position": "Bronze (3rd)", "Performance": wc_df.iloc[2]['performance'], "Athlete": wc_df.iloc[2]['athlete_name']})
                        if len(wc_df) >= 8:
                            wc_standards.append({"Position": "8th Place", "Performance": wc_df.iloc[7]['performance'], "Athlete": wc_df.iloc[7]['athlete_name']})

                        if wc_standards:
                            wc_standards_df = pd.DataFrame(wc_standards)
                            st.dataframe(wc_standards_df, width='stretch', hide_index=True)
                        else:
                            st.info("Insufficient World Championships data")
                    else:
                        st.info("No World Championships data available for this event")

                # Paralympics Standards
                with col2:
                    st.markdown("#### Paralympics")
                    para_df = major_event_df[major_event_df['competition_name'].str.contains('Paralympic|Paralympics', case=False, na=False)].copy()

                    if len(para_df) > 0:
                        para_df['perf_value'] = para_df['performance'].apply(parse_performance)
                        para_df = para_df.dropna(subset=['perf_value'])

                        is_track = is_track_event(selected_report_event)
                        para_df = para_df.sort_values('perf_value', ascending=is_track)

                        # Get medal standards
                        para_standards = []
                        if len(para_df) >= 1:
                            para_standards.append({"Position": "Gold (1st)", "Performance": para_df.iloc[0]['performance'], "Athlete": para_df.iloc[0]['athlete_name']})
                        if len(para_df) >= 2:
                            para_standards.append({"Position": "Silver (2nd)", "Performance": para_df.iloc[1]['performance'], "Athlete": para_df.iloc[1]['athlete_name']})
                        if len(para_df) >= 3:
                            para_standards.append({"Position": "Bronze (3rd)", "Performance": para_df.iloc[2]['performance'], "Athlete": para_df.iloc[2]['athlete_name']})
                        if len(para_df) >= 8:
                            para_standards.append({"Position": "8th Place", "Performance": para_df.iloc[7]['performance'], "Athlete": para_df.iloc[7]['athlete_name']})

                        if para_standards:
                            para_standards_df = pd.DataFrame(para_standards)
                            st.dataframe(para_standards_df, width='stretch', hide_index=True)
                        else:
                            st.info("Insufficient Paralympics data")
                    else:
                        st.info("No Paralympics data available for this event")

                # Medal Standards Comparison Chart
                st.markdown("#### Medal Standards Comparison")

                comparison_data = []

                # WC data
                if len(wc_df) > 0:
                    wc_df_sorted = wc_df.sort_values('perf_value', ascending=is_track_event(selected_report_event))
                    if len(wc_df_sorted) >= 1:
                        comparison_data.append({"Competition": "World Championships", "Medal": "Gold", "Performance": wc_df_sorted.iloc[0]['perf_value']})
                    if len(wc_df_sorted) >= 3:
                        comparison_data.append({"Competition": "World Championships", "Medal": "Bronze", "Performance": wc_df_sorted.iloc[2]['perf_value']})

                # Paralympics data
                if len(para_df) > 0:
                    para_df_sorted = para_df.sort_values('perf_value', ascending=is_track_event(selected_report_event))
                    if len(para_df_sorted) >= 1:
                        comparison_data.append({"Competition": "Paralympics", "Medal": "Gold", "Performance": para_df_sorted.iloc[0]['perf_value']})
                    if len(para_df_sorted) >= 3:
                        comparison_data.append({"Competition": "Paralympics", "Medal": "Bronze", "Performance": para_df_sorted.iloc[2]['perf_value']})

                if comparison_data:
                    comp_df = pd.DataFrame(comparison_data)
                    fig = px.bar(comp_df, x='Competition', y='Performance', color='Medal',
                                barmode='group',
                                color_discrete_map={'Gold': '#FFD700', 'Bronze': '#CD7F32'})
                    fig.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family='Inter, sans-serif', color='#333'),
                        height=350
                    )
                    st.plotly_chart(fig, width='stretch')

            # Section 2: Competition Field
            with report_tab2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
                     padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {GOLD_ACCENT};">
                    <h3 style="color: white; margin: 0;">Competition Field Analysis</h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Top athletes and their best performances</p>
                </div>
                """, unsafe_allow_html=True)

                if len(filtered_event_df) > 0:
                    # Get top performers
                    filtered_event_df['perf_value'] = filtered_event_df['performance'].apply(parse_performance)
                    clean_df = filtered_event_df.dropna(subset=['perf_value'])

                    is_track = is_track_event(selected_report_event)

                    # Group by athlete and get best performance
                    athlete_bests = clean_df.groupby('athlete_name').agg({
                        'performance': 'first',
                        'perf_value': 'min' if is_track else 'max',
                        'nationality': 'first',
                        'competition_name': 'count',
                        'date': 'max'
                    }).reset_index()
                    athlete_bests.columns = ['Athlete', 'Best Performance', 'Performance Value', 'Country', 'Total Results', 'Last Competed']
                    athlete_bests = athlete_bests.sort_values('Performance Value', ascending=is_track).head(20)

                    st.markdown("#### Top 20 Athletes - All Time")
                    st.dataframe(
                        athlete_bests[['Athlete', 'Best Performance', 'Country', 'Total Results']],
                        width='stretch',
                        hide_index=True
                    )

                    # Performance distribution chart
                    st.markdown("#### Performance Distribution")
                    fig = px.histogram(clean_df, x='perf_value', nbins=30,
                                      labels={'perf_value': 'Performance'})
                    fig.update_traces(marker_color=TEAL_PRIMARY)
                    fig.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family='Inter, sans-serif', color='#333'),
                        height=300,
                        showlegend=False
                    )
                    st.plotly_chart(fig, width='stretch')

                    # Country breakdown
                    st.markdown("#### Athletes by Country")
                    country_counts = clean_df.groupby('nationality')['athlete_name'].nunique().sort_values(ascending=False).head(15)
                    fig = px.bar(x=country_counts.values, y=country_counts.index, orientation='h',
                                labels={'x': 'Number of Athletes', 'y': 'Country'})
                    fig.update_traces(marker_color=TEAL_PRIMARY)
                    fig.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family='Inter, sans-serif', color='#333'),
                        height=400
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("No data available for this event combination")

            # Section 3: Historical Championship Data
            with report_tab3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
                     padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {GOLD_ACCENT};">
                    <h3 style="color: white; margin: 0;">Historical Championship Data</h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Performance trends across major championships</p>
                </div>
                """, unsafe_allow_html=True)

                if len(major_event_df) > 0:
                    # Championship results table
                    st.markdown("#### Major Championship Results")

                    major_event_df = major_event_df.copy()
                    major_event_df['perf_value'] = major_event_df['performance'].apply(parse_performance)
                    major_clean = major_event_df.dropna(subset=['perf_value'])

                    is_track = is_track_event(selected_report_event)
                    major_clean = major_clean.sort_values('perf_value', ascending=is_track)

                    display_cols = ['competition_name', 'athlete_name', 'nationality', 'performance', 'date']
                    available_cols = [c for c in display_cols if c in major_clean.columns]

                    st.dataframe(
                        major_clean[available_cols].head(50),
                        width='stretch',
                        hide_index=True
                    )

                    # Performance trends by year - improved visualization
                    st.markdown("#### Performance Trends by Year")
                    if 'date' in major_clean.columns:
                        major_clean['year'] = pd.to_datetime(major_clean['date'], errors='coerce').dt.year
                        yearly_stats = major_clean.groupby('year').agg({
                            'perf_value': ['min' if is_track else 'max', 'mean', 'count']
                        }).reset_index()
                        yearly_stats.columns = ['Year', 'Best', 'Average', 'Count']
                        yearly_stats = yearly_stats.dropna()
                        yearly_stats = yearly_stats.sort_values('Year')

                        if len(yearly_stats) > 1:
                            # Summary metrics
                            first_year = yearly_stats.iloc[0]
                            last_year = yearly_stats.iloc[-1]
                            improvement = first_year['Best'] - last_year['Best'] if is_track else last_year['Best'] - first_year['Best']

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("First Year Best", f"{first_year['Best']:.2f}", f"{int(first_year['Year'])}")
                            with col2:
                                st.metric("Latest Year Best", f"{last_year['Best']:.2f}", f"{int(last_year['Year'])}")
                            with col3:
                                delta_label = "improvement" if improvement > 0 else "slower"
                                st.metric("Change", f"{abs(improvement):.2f}", delta_label)

                            # Area chart showing trend
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=yearly_stats['Year'], y=yearly_stats['Best'],
                                mode='lines+markers+text',
                                name='Best Performance',
                                fill='tozeroy',
                                fillcolor=f'rgba(0, 113, 103, 0.2)',
                                line=dict(color=TEAL_PRIMARY, width=3),
                                marker=dict(size=10, color=GOLD_ACCENT),
                                text=[f"{v:.2f}" for v in yearly_stats['Best']],
                                textposition='top center'
                            ))
                            fig.update_layout(
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                font=dict(family='Inter, sans-serif', color='#333'),
                                height=300,
                                xaxis_title='Year',
                                yaxis_title='Performance',
                                showlegend=False,
                                margin=dict(t=20, b=40)
                            )
                            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', dtick=1)
                            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                            st.plotly_chart(fig, width='stretch')

                            # Data table
                            st.dataframe(yearly_stats, width='stretch', hide_index=True)
                else:
                    st.info("No major championship data available for this event")

            # Section 4: Performance Analysis
            with report_tab4:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
                     padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {GOLD_ACCENT};">
                    <h3 style="color: white; margin: 0;">Performance Analysis</h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Statistical breakdown and benchmarks</p>
                </div>
                """, unsafe_allow_html=True)

                if len(filtered_event_df) > 0:
                    filtered_event_df['perf_value'] = filtered_event_df['performance'].apply(parse_performance)
                    clean_df = filtered_event_df.dropna(subset=['perf_value'])

                    is_track = is_track_event(selected_report_event)

                    # Statistical summary
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        best_val = clean_df['perf_value'].min() if is_track else clean_df['perf_value'].max()
                        st.markdown(f"""
                        <div style="background: {TEAL_PRIMARY}; padding: 1rem; border-radius: 8px; text-align: center;">
                            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Best Performance</p>
                            <p style="color: white; margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;">{best_val:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        avg_val = clean_df['perf_value'].mean()
                        st.markdown(f"""
                        <div style="background: {TEAL_LIGHT}; padding: 1rem; border-radius: 8px; text-align: center;">
                            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Average</p>
                            <p style="color: white; margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;">{avg_val:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        std_val = clean_df['perf_value'].std()
                        st.markdown(f"""
                        <div style="background: {GRAY_BLUE}; padding: 1rem; border-radius: 8px; text-align: center;">
                            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Std Deviation</p>
                            <p style="color: white; margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;">{std_val:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col4:
                        total_results = len(clean_df)
                        st.markdown(f"""
                        <div style="background: {GOLD_ACCENT}; padding: 1rem; border-radius: 8px; text-align: center;">
                            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Total Results</p>
                            <p style="color: white; margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;">{total_results:,}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Percentile breakdown
                    st.markdown("#### Performance Percentiles")
                    percentiles = [10, 25, 50, 75, 90, 95, 99]
                    perc_values = np.percentile(clean_df['perf_value'], percentiles)
                    perc_df = pd.DataFrame({
                        'Percentile': [f'{p}th' for p in percentiles],
                        'Performance': [f'{v:.2f}' for v in perc_values],
                        'Description': ['Elite', 'Very Good', 'Median', 'Above Average', 'Good', 'Competitive', 'Top Level']
                    })
                    st.dataframe(perc_df, width='stretch', hide_index=True)

                    # Box plot
                    st.markdown("#### Performance Distribution")
                    fig = px.box(clean_df, y='perf_value', points='outliers',
                                labels={'perf_value': 'Performance'})
                    fig.update_traces(marker_color=TEAL_PRIMARY, line_color=TEAL_DARK)
                    fig.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family='Inter, sans-serif', color='#333'),
                        height=300
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("No performance data available for analysis")

            # Section 5: Saudi Context
            with report_tab5:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
                     padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {GOLD_ACCENT};">
                    <h3 style="color: white; margin: 0;">Saudi Arabia Context</h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">KSA athlete performance and gap analysis</p>
                </div>
                """, unsafe_allow_html=True)

                # Get Saudi athletes in this event
                saudi_event_df = filtered_event_df[filtered_event_df['nationality'] == 'KSA'].copy()

                if len(saudi_event_df) > 0:
                    saudi_event_df['perf_value'] = saudi_event_df['performance'].apply(parse_performance)
                    saudi_clean = saudi_event_df.dropna(subset=['perf_value'])

                    is_track = is_track_event(selected_report_event)

                    st.markdown("#### Saudi Athletes in this Event")

                    # Saudi athlete summary
                    saudi_athletes = saudi_clean.groupby('athlete_name').agg({
                        'performance': 'first',
                        'perf_value': 'min' if is_track else 'max',
                        'competition_name': 'count',
                        'date': 'max'
                    }).reset_index()
                    saudi_athletes.columns = ['Athlete', 'Best Performance', 'Performance Value', 'Total Results', 'Last Competed']
                    saudi_athletes = saudi_athletes.sort_values('Performance Value', ascending=is_track)

                    st.dataframe(
                        saudi_athletes[['Athlete', 'Best Performance', 'Total Results', 'Last Competed']],
                        width='stretch',
                        hide_index=True
                    )

                    # Gap to medal standards
                    st.markdown("#### Gap to Championship Standards")

                    if len(saudi_athletes) > 0:
                        saudi_best = saudi_athletes.iloc[0]['Performance Value']
                        saudi_best_athlete = saudi_athletes.iloc[0]['Athlete']

                        # Get world best from filtered data
                        all_clean = filtered_event_df.dropna(subset=['perf_value'])
                        if len(all_clean) > 0:
                            world_best = all_clean['perf_value'].min() if is_track else all_clean['perf_value'].max()

                            # Calculate gaps
                            if is_track:
                                gap_to_gold = saudi_best - world_best
                                gap_text = f"+{gap_to_gold:.2f}s behind" if gap_to_gold > 0 else f"{abs(gap_to_gold):.2f}s ahead"
                            else:
                                gap_to_gold = world_best - saudi_best
                                gap_text = f"{gap_to_gold:.2f}m behind" if gap_to_gold > 0 else f"{abs(gap_to_gold):.2f}m ahead"

                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown(f"""
                                <div style="background: {GOLD_ACCENT}; padding: 1.5rem; border-radius: 8px; text-align: center;">
                                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">Saudi Best ({saudi_best_athlete})</p>
                                    <p style="color: white; margin: 0.5rem 0; font-size: 2rem; font-weight: bold;">{saudi_best:.2f}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            with col2:
                                gap_color = TEAL_PRIMARY if gap_to_gold <= 0 else '#dc3545'
                                st.markdown(f"""
                                <div style="background: {gap_color}; padding: 1.5rem; border-radius: 8px; text-align: center;">
                                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">Gap to Gold Standard</p>
                                    <p style="color: white; margin: 0.5rem 0; font-size: 2rem; font-weight: bold;">{gap_text}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            # Saudi performance history
                            st.markdown("#### Saudi Performance History")
                            st.dataframe(
                                saudi_clean[['athlete_name', 'competition_name', 'performance', 'date']].sort_values('date', ascending=False),
                                width='stretch',
                                hide_index=True
                            )
                else:
                    st.info("No Saudi athletes found in this event/classification/gender combination")

                    # Show what it would take
                    st.markdown("#### Target Standards for Saudi Athletes")

                    all_clean = filtered_event_df.dropna(subset=['perf_value'])
                    if len(all_clean) > 0:
                        is_track = is_track_event(selected_report_event)
                        all_clean = all_clean.sort_values('perf_value', ascending=is_track)

                        targets = []
                        if len(all_clean) >= 1:
                            targets.append({"Target": "Gold Medal", "Performance": all_clean.iloc[0]['performance']})
                        if len(all_clean) >= 3:
                            targets.append({"Target": "Bronze Medal", "Performance": all_clean.iloc[2]['performance']})
                        if len(all_clean) >= 8:
                            targets.append({"Target": "Finals (8th)", "Performance": all_clean.iloc[7]['performance']})

                        if targets:
                            st.dataframe(pd.DataFrame(targets), width='stretch', hide_index=True)
        else:
            st.info("Please select an event, classification, and gender to generate the report")
    else:
        st.info("No results data available yet. Run the GitHub workflow to populate.")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if len(results_df) > 0:
        # Try to get last update from available date columns
        if 'scraped_at' in results_df.columns:
            last_update = results_df['scraped_at'].max()
        elif 'date' in results_df.columns:
            last_update = results_df['date'].max()
        elif 'competitiondate' in results_df.columns:
            last_update = results_df['competitiondate'].max()
        else:
            last_update = "Unknown"
        st.caption(f"Data from: {last_update}")
with col2:
    st.caption(f"Source: {get_connection_mode().upper()}")
with col3:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
