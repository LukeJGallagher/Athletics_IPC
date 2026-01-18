"""
Team Saudi Para Athletics Intelligence Dashboard
Comprehensive performance analysis system for Saudi Arabia Paralympic Program

Features:
- Athlete profiles with detailed performance history
- Championship standards (what it takes to win)
- World/Asian/Championship records
- Competitor intelligence and threat assessment
- Season progression tracking
- Major event performance analysis
- Top 8 analysis by event/classification
- Saudi qualification standards
- Filter by classification, event, gender
- Athlete classification management
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import re
import json

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agents.skills import (
        DataLoadingSkill,
        GenderSeparationSkill,
        PerformanceAnalysisSkill,
        ClassificationSkill,
        VisualizationSkill
    )
    AGENTS_AVAILABLE = True
except:
    AGENTS_AVAILABLE = False

# Import enhanced dashboard module
try:
    from enhanced_dashboard_module import (
        load_all_standards,
        show_championship_standards_complete,
        show_competitor_intelligence_complete,
        compare_to_standards
    )
    ENHANCED_MODULE_AVAILABLE = True
except Exception as e:
    print(f"Enhanced module not available: {e}")
    ENHANCED_MODULE_AVAILABLE = False

# Import ultra-detailed features v2
try:
    from enhanced_features_v2 import (
        show_detailed_athlete_profile,
        show_ultra_detailed_championship_standards
    )
    ULTRA_DETAILED_AVAILABLE = True
except Exception as e:
    print(f"Ultra-detailed features not available: {e}")
    ULTRA_DETAILED_AVAILABLE = False

# Import Parquet data layer for Azure Blob Storage
try:
    from parquet_data_layer import (
        get_data_manager,
        get_connection_mode,
        load_results as parquet_load_results,
        load_rankings as parquet_load_rankings,
        load_records as parquet_load_records,
        load_championship_standards as parquet_load_standards
    )
    PARQUET_AVAILABLE = True
except Exception as e:
    print(f"Parquet data layer not available: {e}")
    PARQUET_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Team Saudi Para Athletics Intelligence",
    page_icon="🇸🇦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Team Saudi branding colors
COLORS = {
    'primary_green': '#1B8B7D',
    'gold': '#D4AF37',
    'teal': '#007167',
    'secondary_gold': '#9D8E65',
    'white': '#FFFFFF',
    'black': '#000000'
}

# Custom CSS with Team Saudi branding
st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(90deg, {COLORS['primary_green']} 0%, {COLORS['teal']} 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    .main-header h1 {{
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    .main-header p {{
        font-size: 1.2rem;
        margin: 10px 0 0 0;
    }}
    .metric-card {{
        background: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {COLORS['primary_green']};
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }}
    .stDataFrame {{
        background-color: #FFFFFF !important;
    }}
    .stDataFrame [data-testid="stDataFrameResizable"] {{
        background-color: #FFFFFF !important;
    }}
    div[data-testid="stExpander"] {{
        background-color: #FFFFFF;
        border-radius: 10px;
    }}
    .element-container {{
        background-color: transparent;
    }}
    section[data-testid="stSidebar"] {{
        background-color: #FAFAFA;
    }}
    .main .block-container {{
        background-color: #FFFFFF;
        padding: 2rem;
        border-radius: 10px;
    }}
    .gold-medal {{
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000;
        font-weight: bold;
    }}
    .silver-medal {{
        background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%);
        color: #000;
        font-weight: bold;
    }}
    .bronze-medal {{
        background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%);
        color: #FFF;
        font-weight: bold;
    }}
    .saudi-athlete {{
        background-color: #E8F5E9;
        border-left: 4px solid {COLORS['primary_green']};
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }}
    .competitor-threat-high {{
        background-color: #FFEBEE;
        border-left: 4px solid #D32F2F;
    }}
    .competitor-threat-medium {{
        background-color: #FFF3E0;
        border-left: 4px solid #F57C00;
    }}
    .competitor-threat-low {{
        background-color: #E3F2FD;
        border-left: 4px solid #1976D2;
    }}
    .world-record {{
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: bold;
    }}
    .asian-record {{
        background: linear-gradient(135deg, #2196F3 0%, #1565C0 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: bold;
    }}
    .stButton>button {{
        background-color: {COLORS['primary_green']};
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {COLORS['teal']};
    }}
    .classification-badge {{
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        background-color: {COLORS['primary_green']};
        color: white;
        font-weight: bold;
        margin: 5px;
    }}
</style>
""", unsafe_allow_html=True)

# Event type determination for correct min/max logic
def get_event_type(event_name):
    """Determine if event is track (lower is better) or field (higher is better)"""
    event_lower = event_name.lower()

    # Field events (higher is better)
    if any(x in event_lower for x in ['shot', 'discus', 'javelin', 'throw', 'jump', 'high jump', 'long jump', 'triple jump']):
        return 'field'

    # Track events (lower is better)
    if any(x in event_lower for x in ['m', 'marathon', 'race', 'run']):
        return 'track'

    return 'track'  # Default to track

def is_better_performance(perf1, perf2, event_type):
    """Compare performances based on event type"""
    try:
        p1 = float(perf1)
        p2 = float(perf2)
        if event_type == 'field':
            return p1 > p2  # Higher is better
        else:
            return p1 < p2  # Lower is better
    except:
        return False

@st.cache_data
def load_data():
    """Load all performance data - uses Parquet from Azure Blob Storage if available"""
    try:
        # Try Parquet data layer first (Azure Blob Storage or local cache)
        if PARQUET_AVAILABLE:
            df = parquet_load_results()
            if not df.empty:
                # Normalize column names to lowercase
                df.columns = df.columns.str.lower()
        else:
            # Fallback to CSV
            df = pd.read_csv('data/Tilastoptija/ksaoutputipc3.csv',
                            encoding='latin-1',
                            low_memory=False)

        if df.empty:
            return pd.DataFrame()

        # Create full name (handle different column names)
        first_col = 'firstname' if 'firstname' in df.columns else 'givenname'
        last_col = 'lastname' if 'lastname' in df.columns else 'familyname'
        if first_col in df.columns and last_col in df.columns:
            df['athlete_name'] = df[first_col].fillna('') + ' ' + df[last_col].fillna('')
            df['athlete_name'] = df['athlete_name'].str.strip()

        # Extract classification from event name
        event_col = 'eventname' if 'eventname' in df.columns else 'event'
        if event_col in df.columns:
            df['classification'] = df[event_col].str.extract(r'([TF]\d{2})')

        # Clean performance values
        perf_col = 'performance' if 'performance' in df.columns else 'result'
        if perf_col in df.columns:
            df['performance_clean'] = pd.to_numeric(df[perf_col], errors='coerce')

        # Parse dates
        date_col = 'competitiondate' if 'competitiondate' in df.columns else 'date'
        if date_col in df.columns:
            df['competition_date'] = pd.to_datetime(df[date_col], errors='coerce')
            df['year'] = df['competition_date'].dt.year
            df['season'] = df['competition_date'].dt.year

        # Identify major championships
        comp_col = 'competitionname' if 'competitionname' in df.columns else 'competition'
        if comp_col in df.columns:
            df['is_major'] = df[comp_col].str.contains(
                'World Championships|Paralympic|Olympics|Asian Para Games',
                case=False,
                na=False
            )

        # Gender from event name
        if event_col in df.columns:
            df['gender'] = df[event_col].apply(lambda x:
                'Men' if any(term in str(x) for term in ["Men's", "Men ", "M "])
                else 'Women' if any(term in str(x) for term in ["Women's", "Women ", "W "])
                else 'Unknown'
            )

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_records():
    """Load world and regional records - uses Parquet from Azure Blob Storage if available"""
    # Try Parquet data layer first
    if PARQUET_AVAILABLE:
        try:
            records = parquet_load_records()
            if not records.empty:
                # Normalize column names
                records.columns = records.columns.str.lower()
                # Standardize column names
                column_mapping = {
                    'event_name': 'event',
                    'athlete_name': 'athlete',
                    'country_code': 'country',
                    'athlete_gender': 'gender',
                    'athlete_class': 'classification'
                }
                for old_col, new_col in column_mapping.items():
                    if old_col in records.columns and new_col not in records.columns:
                        records[new_col] = records[old_col]
                return records
        except Exception as e:
            print(f"Parquet records load failed: {e}")

    # Fallback to CSV
    records_dir = Path('data/Records')
    all_records = []

    if records_dir.exists():
        # First, load world records (has different format with actual data)
        world_records_files = list(records_dir.glob('ipc_world_records*.csv'))
        for file in world_records_files:
            try:
                df = pd.read_csv(file, encoding='latin-1')
                # World records file has 'record_type' column already (WR)
                if 'record_type' not in df.columns:
                    df['record_type'] = 'World Record'
                # Filter out empty/invalid records
                if 'performance' in df.columns:
                    df = df[df['performance'].notna() & (df['performance'] != '')]
                all_records.append(df)
            except Exception as e:
                continue

        # Load other record types (Asian, Paralympic, Championship, etc.)
        for file in records_dir.glob('ipc_records_*.csv'):
            try:
                df = pd.read_csv(file, encoding='latin-1')
                # Extract record type from filename
                record_type = file.stem.replace('ipc_records_', '').split('_2025')[0].replace('_', ' ')
                df['record_type'] = record_type
                # Filter out empty/invalid records (performance is empty or N/A)
                if 'performance' in df.columns:
                    df = df[df['performance'].notna() & (df['performance'] != '') & (df['performance'] != 'N/A')]
                if len(df) > 0:
                    all_records.append(df)
            except Exception as e:
                continue

    if all_records:
        combined = pd.concat(all_records, ignore_index=True)
        # Standardize column names
        column_mapping = {
            'event_name': 'event',
            'athlete_name': 'athlete',
            'country_code': 'country',
            'athlete_gender': 'gender',
            'athlete_class': 'classification'
        }
        for old_col, new_col in column_mapping.items():
            if old_col in combined.columns and new_col not in combined.columns:
                combined[new_col] = combined[old_col]
        return combined
    return pd.DataFrame()

def main():
    """Main dashboard application"""

    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🇸🇦 Team Saudi Para Athletics Intelligence System</h1>
        <p>Performance Analysis & Competitor Intelligence for Saudi Arabia Paralympic Program</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    with st.spinner('Loading worldwide athlete database...'):
        df = load_data()
        records_df = load_records()

        # Load standards data
        if ENHANCED_MODULE_AVAILABLE:
            standards_data = load_all_standards()
        else:
            standards_data = {}

    if df.empty:
        st.error("Unable to load data. Please check data files.")
        return

    # Sidebar - Main Navigation
    st.sidebar.image("https://via.placeholder.com/300x100/1B8B7D/FFFFFF?text=Team+Saudi", use_column_width=True)

    # Show data connection mode
    if PARQUET_AVAILABLE:
        mode = get_connection_mode()
        mode_display = {
            'azure_blob': 'Azure Blob Storage',
            'local_parquet': 'Local Parquet',
            'local_csv': 'Local CSV'
        }.get(mode, mode)
        st.sidebar.caption(f"Data: {mode_display}")

    # Competition Mode Toggle - Key strategic selector
    st.sidebar.markdown("""
    <div style="background: linear-gradient(135deg, #007167 0%, #005a51 100%);
                padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;">
        <h4 style="color: white; margin: 0; text-align: center;">Target Competition</h4>
    </div>
    """, unsafe_allow_html=True)

    competition_mode = st.sidebar.radio(
        "Select Target",
        ["Asian Games 2026", "LA Paralympics 2028"],
        index=0,
        key="competition_mode_selector",
        label_visibility="collapsed"
    )

    # Store in session state for global access
    st.session_state['competition_mode'] = competition_mode

    # Show target indicator
    if competition_mode == "Asian Games 2026":
        st.sidebar.success("Targeting: Asian Games 2026")
    else:
        st.sidebar.info("Targeting: LA Paralympics 2028")

    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard Overview",
            "👤 Athlete Profiles",
            "🏆 Championship Standards",
            "🌍 World & Asian Records",
            "📊 Top 8 Analysis",
            "🎯 Competitor Intelligence",
            "📈 Season Progression",
            "🇸🇦 Saudi Athletes",
            "⚙️ Data Management"
        ]
    )

    # Manual Refresh Section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Data Updates")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔍 Check Updates", help="Check for new data without downloading"):
            with st.spinner("Checking for updates..."):
                try:
                    import subprocess
                    result = subprocess.run(
                        ['python', 'tilastopaja_updater.py', '--check'],
                        capture_output=True, text=True, timeout=60
                    )
                    st.sidebar.info(result.stdout if result.stdout else "Check complete")
                except Exception as e:
                    st.sidebar.error(f"Check failed: {e}")

    with col2:
        if st.button("⬇️ Update Data", help="Download latest data if available"):
            with st.spinner("Updating database..."):
                try:
                    import subprocess
                    result = subprocess.run(
                        ['python', 'tilastopaja_updater.py', '--check-and-update'],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode == 0:
                        st.sidebar.success("Update complete! Refresh page to see changes.")
                        st.cache_data.clear()
                    else:
                        st.sidebar.warning(result.stdout if result.stdout else "No updates available")
                except Exception as e:
                    st.sidebar.error(f"Update failed: {e}")

    # Show last update time
    metadata_path = Path("data/tilastopaja_metadata.json")
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                meta = json.load(f)
            last_update = meta.get('last_download', 'Unknown')
            if last_update != 'Unknown':
                last_update = last_update[:19].replace('T', ' ')
            st.sidebar.caption(f"Last update: {last_update}")
        except:
            pass

    # Global filters in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Global Filters")

    # Classification filter
    all_classifications = sorted(df['classification'].dropna().unique())
    selected_classifications = st.sidebar.multiselect(
        "Classifications",
        all_classifications,
        default=None,
        help="Filter by disability classification (T/F11-64)"
    )

    # Event filter
    all_events = sorted(df['eventname'].unique())
    selected_events = st.sidebar.multiselect(
        "Events",
        all_events,
        default=None
    )

    # Gender filter
    selected_gender = st.sidebar.selectbox(
        "Gender",
        ["All", "Men", "Women"]
    )

    # Year filter
    min_year = int(df['year'].min()) if not df['year'].isna().all() else 2012
    max_year = int(df['year'].max()) if not df['year'].isna().all() else datetime.now().year
    selected_years = st.sidebar.slider(
        "Years",
        min_year,
        max_year,
        (min_year, max_year)
    )

    # Apply filters
    filtered_df = df.copy()

    if selected_classifications:
        filtered_df = filtered_df[filtered_df['classification'].isin(selected_classifications)]

    if selected_events:
        filtered_df = filtered_df[filtered_df['eventname'].isin(selected_events)]

    if selected_gender != "All":
        filtered_df = filtered_df[filtered_df['gender'] == selected_gender]

    filtered_df = filtered_df[
        (filtered_df['year'] >= selected_years[0]) &
        (filtered_df['year'] <= selected_years[1])
    ]

    # Route to selected page
    if page == "🏠 Dashboard Overview":
        show_dashboard_overview(filtered_df, df)

    elif page == "👤 Athlete Profiles":
        if ULTRA_DETAILED_AVAILABLE:
            show_athlete_profiles_enhanced(filtered_df, df, standards_data)
        else:
            show_athlete_profiles(filtered_df, df)

    elif page == "🏆 Championship Standards":
        if ULTRA_DETAILED_AVAILABLE:
            show_ultra_detailed_championship_standards(filtered_df, standards_data)
        elif ENHANCED_MODULE_AVAILABLE:
            show_championship_standards_complete(filtered_df, standards_data)
        else:
            show_championship_standards(filtered_df, df)

    elif page == "🌍 World & Asian Records":
        show_records(records_df, filtered_df)

    elif page == "📊 Top 8 Analysis":
        show_top8_analysis(filtered_df, df)

    elif page == "🎯 Competitor Intelligence":
        if ENHANCED_MODULE_AVAILABLE:
            show_competitor_intelligence_complete(filtered_df, df, standards_data)
        else:
            show_competitor_intelligence(filtered_df, df)

    elif page == "📈 Season Progression":
        show_season_progression(filtered_df, df)

    elif page == "🇸🇦 Saudi Athletes":
        show_saudi_athletes(filtered_df, df)

    elif page == "⚙️ Data Management":
        show_data_management(df)

def show_dashboard_overview(filtered_df, full_df):
    """Dashboard overview with key metrics"""

    st.markdown("## 📊 System Overview")

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Athletes",
            f"{full_df['athleteid'].nunique():,}",
            help="Worldwide athlete database"
        )

    with col2:
        st.metric(
            "Total Performances",
            f"{len(full_df):,}",
            help="All recorded performances (2012-2024)"
        )

    with col3:
        st.metric(
            "Countries",
            f"{full_df['nationality'].nunique()}",
            help="Countries represented"
        )

    with col4:
        saudi_count = len(full_df[full_df['nationality'] == 'KSA'])
        st.metric(
            "Saudi Performances",
            f"{saudi_count:,}",
            help="Team Saudi recorded performances"
        )

    with col5:
        saudi_athletes = full_df[full_df['nationality'] == 'KSA']['athleteid'].nunique()
        st.metric(
            "Saudi Athletes",
            f"{saudi_athletes}",
            help="Team Saudi athlete count"
        )

    # Coverage map
    st.markdown("### 🌍 Global Coverage")

    country_stats = full_df.groupby('nationality').agg({
        'athleteid': 'nunique',
        'performance_clean': 'count'
    }).reset_index()
    country_stats.columns = ['Country', 'Athletes', 'Performances']
    country_stats = country_stats.sort_values('Performances', ascending=False).head(20)

    fig = px.bar(
        country_stats,
        x='Country',
        y='Performances',
        title="Top 20 Countries by Performance Count",
        color='Performances',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Event distribution
    st.markdown("### 🏃 Event Distribution")

    col1, col2 = st.columns(2)

    with col1:
        event_counts = full_df['eventname'].value_counts().head(15)
        event_df = pd.DataFrame({'Event': event_counts.index, 'Performances': event_counts.values})
        fig = px.bar(
            event_df,
            x='Performances',
            y='Event',
            orientation='h',
            title="Top 15 Events by Performance Count",
            color='Performances',
            color_continuous_scale='Teal'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        class_counts = full_df['classification'].value_counts().head(15)
        class_df = pd.DataFrame({'Classification': class_counts.index, 'Performances': class_counts.values})
        fig = px.bar(
            class_df,
            x='Performances',
            y='Classification',
            orientation='h',
            title="Top 15 Classifications by Performance Count",
            color='Performances',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Recent major championships
    st.markdown("### 🏆 Major Championships Coverage")

    major_comps = full_df[full_df['is_major']].groupby('competitionname').agg({
        'athleteid': 'nunique',
        'performance_clean': 'count',
        'competition_date': 'max'
    }).reset_index()
    major_comps.columns = ['Championship', 'Athletes', 'Performances', 'Latest Date']
    major_comps = major_comps.sort_values('Latest Date', ascending=False).head(10)

    st.dataframe(major_comps, use_container_width=True, hide_index=True)

    # Medal Contender Summary based on Competition Mode
    st.markdown("---")
    competition_mode = st.session_state.get('competition_mode', 'Asian Games 2026')
    st.markdown(f"### 🎯 Medal Contender Summary - {competition_mode}")

    saudi_df = full_df[full_df['nationality'] == 'KSA']

    if len(saudi_df) > 0:
        # Get best performance per athlete per event
        saudi_summary = saudi_df.groupby(['athlete_name', 'eventname']).agg({
            'performance_clean': 'min',  # Best performance (works for track events)
            'classification': 'first'
        }).reset_index()

        # Count unique athlete-event combinations
        total_combinations = len(saudi_summary)
        unique_athletes = saudi_df['athlete_name'].nunique()
        unique_events = saudi_df['eventname'].nunique()

        # Medal contender status cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div style="background: {COLORS['teal']}; padding: 1rem; border-radius: 8px; text-align: center;">
                <h2 style="color: white; margin: 0;">{unique_athletes}</h2>
                <p style="color: rgba(255,255,255,0.9); margin: 0;">Saudi Athletes</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background: {COLORS['gold']}; padding: 1rem; border-radius: 8px; text-align: center;">
                <h2 style="color: #333; margin: 0;">{unique_events}</h2>
                <p style="color: rgba(0,0,0,0.7); margin: 0;">Events</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background: {COLORS['primary_green']}; padding: 1rem; border-radius: 8px; text-align: center;">
                <h2 style="color: white; margin: 0;">{total_combinations}</h2>
                <p style="color: rgba(255,255,255,0.9); margin: 0;">Athlete-Event Combos</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            # Count athletes with championship-level performances
            major_perf_count = len(saudi_df[saudi_df['is_major']]['athlete_name'].unique())
            st.markdown(f"""
            <div style="background: #78909C; padding: 1rem; border-radius: 8px; text-align: center;">
                <h2 style="color: white; margin: 0;">{major_perf_count}</h2>
                <p style="color: rgba(255,255,255,0.9); margin: 0;">Championship Experience</p>
            </div>
            """, unsafe_allow_html=True)

        # Target competition message
        if competition_mode == "Asian Games 2026":
            st.info("🎯 **Asian Games Focus**: Analysis prioritizes regional competition standards and Asian rankings data")
        else:
            st.info("🎯 **LA Paralympics Focus**: Analysis uses Paralympic standards and world rankings for medal targeting")
    else:
        st.warning("No Saudi athletes found in the dataset.")

def show_athlete_profiles_enhanced(filtered_df, full_df, standards_data):
    """Ultra-detailed athlete profile view with standards comparison"""

    st.markdown("## 👤 Athlete Profiles - Comprehensive Analysis")

    # Country filter first
    col1, col2 = st.columns([1, 3])

    with col1:
        all_countries = ['All Countries'] + sorted(filtered_df['nationality'].dropna().unique().tolist())
        selected_country = st.selectbox(
            "Filter by Country",
            all_countries,
            key="athlete_profile_country",
            help="Filter athletes by nationality"
        )

    # Apply country filter
    if selected_country != 'All Countries':
        country_filtered_df = filtered_df[filtered_df['nationality'] == selected_country]
        athlete_count = len(country_filtered_df['athlete_name'].unique())
        st.info(f"Showing {athlete_count} athletes from {selected_country}")
    else:
        country_filtered_df = filtered_df
        athlete_count = len(country_filtered_df['athlete_name'].unique())

    # Athlete search
    all_athletes = sorted(country_filtered_df['athlete_name'].unique())

    with col2:
        selected_athlete = st.selectbox(
            f"Search Athlete ({athlete_count:,} athletes)",
            all_athletes,
            help="Select an athlete to view ultra-detailed profile with standards comparison"
        )

    if not selected_athlete:
        st.info("Select an athlete to view their comprehensive profile")
        return

    # Use ultra-detailed profile from enhanced_features_v2
    show_detailed_athlete_profile(selected_athlete, filtered_df, full_df, standards_data)

def show_athlete_profiles(filtered_df, full_df):
    """Detailed athlete profile view"""

    st.markdown("## 👤 Athlete Profiles")

    # Country filter first
    col1, col2 = st.columns([1, 3])

    with col1:
        all_countries = ['All Countries'] + sorted(filtered_df['nationality'].dropna().unique().tolist())
        selected_country = st.selectbox(
            "Filter by Country",
            all_countries,
            key="athlete_profile_country_basic",
            help="Filter athletes by nationality"
        )

    # Apply country filter
    if selected_country != 'All Countries':
        country_filtered_df = filtered_df[filtered_df['nationality'] == selected_country]
        athlete_count = len(country_filtered_df['athlete_name'].unique())
        st.info(f"Showing {athlete_count} athletes from {selected_country}")
    else:
        country_filtered_df = filtered_df
        athlete_count = len(country_filtered_df['athlete_name'].unique())

    # Athlete search
    all_athletes = sorted(country_filtered_df['athlete_name'].unique())

    with col2:
        selected_athlete = st.selectbox(
            f"Search Athlete ({athlete_count:,} athletes)",
            all_athletes,
            help="Select an athlete to view detailed profile"
        )

    if not selected_athlete:
        st.info("Select an athlete to view their profile")
        return

    # Get athlete data (use full_df to get all their performances, not just filtered)
    athlete_data = full_df[full_df['athlete_name'] == selected_athlete]

    if athlete_data.empty:
        st.warning("No data found for selected athlete")
        return

    # Athlete header
    nationality = athlete_data['nationality'].iloc[0]
    classifications = athlete_data['classification'].dropna().unique()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{selected_athlete}</h3>
            <p><strong>Country:</strong> {nationality}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("Total Competitions", athlete_data['competitionname'].nunique())

    with col3:
        st.metric("Total Events", athlete_data['eventname'].nunique())

    with col4:
        st.metric("Total Performances", len(athlete_data))

    # Classifications
    if len(classifications) > 0:
        st.markdown("**Classifications:** " + " ".join([
            f'<span class="classification-badge">{c}</span>'
            for c in classifications
        ]), unsafe_allow_html=True)

    # Performance timeline
    st.markdown("### 📈 Performance Timeline")

    for event in athlete_data['eventname'].unique()[:5]:  # Top 5 events
        event_data = athlete_data[athlete_data['eventname'] == event].copy()
        event_data = event_data.sort_values('competition_date')

        if len(event_data) > 0:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=event_data['competition_date'],
                y=event_data['performance_clean'],
                mode='lines+markers',
                name=event,
                line=dict(color=COLORS['primary_green'], width=2),
                marker=dict(size=10)
            ))

            fig.update_layout(
                title=f"{event} - Performance Progression",
                xaxis_title="Date",
                yaxis_title="Performance",
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

    # Season bests
    st.markdown("### 🌟 Season Bests")

    season_bests = athlete_data.groupby(['season', 'eventname']).agg({
        'performance_clean': lambda x: x.dropna().iloc[0] if len(x.dropna()) > 0 else None,
        'competitionname': 'first',
        'competition_date': 'first'
    }).reset_index()

    season_bests = season_bests.dropna(subset=['performance_clean'])
    season_bests = season_bests.sort_values(['season', 'eventname'], ascending=[False, True])

    st.dataframe(season_bests, use_container_width=True, hide_index=True)

    # Major championships performance
    st.markdown("### 🏆 Major Championships Performance")

    major_perfs = athlete_data[athlete_data['is_major']].sort_values('competition_date', ascending=False)

    if len(major_perfs) > 0:
        major_display = major_perfs[['competition_date', 'competitionname', 'eventname',
                                     'round', 'position', 'performance_clean']].head(20)
        st.dataframe(major_display, use_container_width=True, hide_index=True)
    else:
        st.info("No major championship performances recorded")

# Continue with other page functions...
# (Due to length, showing core structure. Would continue with remaining functions)

def show_championship_standards(filtered_df, full_df):
    """Championship winning standards analysis"""
    st.markdown("## 🏆 Championship Standards - What It Takes to Win")
    st.info("Under development - will show gold/silver/bronze standards by event/classification")

def show_records(records_df, filtered_df):
    """World and Asian records"""
    st.markdown("## 🌍 World & Asian Records")

    if records_df.empty:
        st.info("Records data not available. Run the records scraper to update.")
        return

    # Show record count
    st.success(f"Loaded {len(records_df)} world records")

    # Get event column
    event_col = 'event' if 'event' in records_df.columns else 'event_name'

    # Extract base events (without gender prefix) for event filter
    def extract_base_event(event_name):
        """Extract base event name like '100 m', 'Shot Put' etc."""
        if pd.isna(event_name):
            return None
        # Remove gender prefix
        base = str(event_name).replace("Men's ", "").replace("Women's ", "")
        # Remove classification suffix (e.g., T11, F20)
        base = re.sub(r'\s+[TF]\d{2}.*$', '', base)
        return base.strip()

    if event_col in records_df.columns:
        records_df['base_event'] = records_df[event_col].apply(extract_base_event)
        base_events = sorted(records_df['base_event'].dropna().unique().tolist())
    else:
        base_events = []

    # Get classifications
    class_col = 'classification' if 'classification' in records_df.columns else 'athlete_class'
    if class_col in records_df.columns:
        classifications = sorted(records_df[class_col].dropna().unique().tolist())
    else:
        classifications = []

    # Filters - Row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Gender filter
        genders = ['All', 'Men', 'Women']
        selected_gender = st.selectbox("Gender", genders, key="records_gender")

    with col2:
        # Event type filter (category)
        event_types = ['All Categories', 'Track (Sprints)', 'Track (Distance)', 'Field (Throws)', 'Field (Jumps)', 'Relays']
        selected_event_type = st.selectbox("Event Category", event_types, key="records_event_type")

    with col3:
        # Specific event filter
        event_options = ['All Events'] + base_events
        selected_event = st.selectbox("Specific Event", event_options, key="records_specific_event")

    with col4:
        # Classification filter
        class_options = ['All Classifications'] + classifications
        selected_class = st.selectbox("Classification", class_options, key="records_class")

    # Apply filters
    display_df = records_df.copy()

    # Gender filter
    if selected_gender != 'All':
        gender_pattern = "Men's" if selected_gender == 'Men' else "Women's"
        if event_col in display_df.columns:
            display_df = display_df[display_df[event_col].str.contains(gender_pattern, case=False, na=False)]

    # Event category filter
    if selected_event_type != 'All Categories':
        if event_col in display_df.columns:
            if selected_event_type == 'Track (Sprints)':
                display_df = display_df[display_df[event_col].str.contains(r'100 m|200 m|400 m', regex=True, na=False)]
            elif selected_event_type == 'Track (Distance)':
                display_df = display_df[display_df[event_col].str.contains(r'800 m|1500 m|5000 m|10,000 m|Marathon', regex=True, na=False)]
            elif selected_event_type == 'Field (Throws)':
                display_df = display_df[display_df[event_col].str.contains(r'Shot Put|Discus|Javelin|Club Throw', regex=True, na=False)]
            elif selected_event_type == 'Field (Jumps)':
                display_df = display_df[display_df[event_col].str.contains(r'Long Jump|High Jump|Triple Jump', regex=True, na=False)]
            elif selected_event_type == 'Relays':
                display_df = display_df[display_df[event_col].str.contains(r'Relay|4x', regex=True, na=False)]

    # Specific event filter
    if selected_event != 'All Events':
        display_df = display_df[display_df['base_event'] == selected_event]

    # Classification filter
    if selected_class != 'All Classifications':
        if class_col in display_df.columns:
            display_df = display_df[display_df[class_col] == selected_class]

    # Display columns
    display_columns = []
    for col in ['event', 'event_name', 'performance', 'athlete', 'athlete_name', 'country', 'country_code',
                'country_name', 'date', 'competition', 'location', 'record_type']:
        if col in display_df.columns:
            display_columns.append(col)

    # Remove duplicates (prefer shorter names)
    if 'event' in display_columns and 'event_name' in display_columns:
        display_columns.remove('event_name')
    if 'athlete' in display_columns and 'athlete_name' in display_columns:
        display_columns.remove('athlete_name')
    if 'country' in display_columns and 'country_code' in display_columns:
        display_columns.remove('country_code')
    if 'country' in display_columns and 'country_name' in display_columns:
        display_columns.remove('country_name')

    if display_columns and not display_df.empty:
        st.markdown(f"### Showing {len(display_df)} records")

        # Sort by event name
        sort_col = 'event' if 'event' in display_df.columns else 'event_name'
        if sort_col in display_df.columns:
            display_df = display_df.sort_values(sort_col)

        st.dataframe(
            display_df[display_columns].reset_index(drop=True),
            use_container_width=True,
            height=500
        )

        # Summary stats
        st.markdown("### Record Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            country_col = 'country' if 'country' in display_df.columns else 'country_code'
            if country_col in display_df.columns:
                top_countries = display_df[country_col].value_counts().head(5)
                st.markdown("**Top Countries by Records:**")
                for country, count in top_countries.items():
                    st.write(f"- {country}: {count}")

        with col2:
            if 'date' in display_df.columns:
                recent = display_df.nlargest(5, 'date') if display_df['date'].dtype == 'datetime64[ns]' else display_df.head(5)
                st.markdown("**Recent Records Set:**")
                for _, row in recent.iterrows():
                    event = row.get('event', row.get('event_name', 'Unknown'))
                    date = row.get('date', 'Unknown')
                    st.write(f"- {event}: {date}")

        with col3:
            # Record type breakdown
            if 'record_type' in display_df.columns:
                type_counts = display_df['record_type'].value_counts()
                st.markdown("**Record Types:**")
                for rtype, count in type_counts.items():
                    st.write(f"- {rtype}: {count}")
    else:
        st.warning("No records match your filters")

def show_top8_analysis(filtered_df, full_df):
    """Top 8 finishers analysis by event and classification"""
    st.markdown("## 📊 Top 8 Analysis - Championship Standards")

    if filtered_df.empty:
        st.warning("No data available with current filters")
        return

    # Extract base event names for filtering
    def extract_base_event(event_name):
        """Extract base event like '100 m', 'Shot Put' without gender/classification"""
        if pd.isna(event_name):
            return None
        base = str(event_name).replace("Men's ", "").replace("Women's ", "")
        base = re.sub(r'\s+[TF]\d{2}.*$', '', base)
        return base.strip()

    filtered_df = filtered_df.copy()
    filtered_df['base_event'] = filtered_df['eventname'].apply(extract_base_event)

    # Get unique values for filters
    base_events = sorted(filtered_df['base_event'].dropna().unique().tolist())
    classifications = sorted(filtered_df['classification'].dropna().unique().tolist())

    # Filter row
    st.markdown("### Select Event")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Gender filter
        genders = ['All', 'Men', 'Women']
        selected_gender = st.selectbox("Gender", genders, key="top8_gender")

    with col2:
        # Base event filter
        event_options = ['Select Event...'] + base_events
        selected_base_event = st.selectbox("Event", event_options, key="top8_base_event")

    with col3:
        # Classification filter
        class_options = ['All Classifications'] + classifications
        selected_class = st.selectbox("Classification", class_options, key="top8_class")

    # Apply filters
    analysis_df = filtered_df.copy()

    # Gender filter
    if selected_gender != 'All':
        gender_pattern = "Men's" if selected_gender == 'Men' else "Women's"
        analysis_df = analysis_df[analysis_df['eventname'].str.contains(gender_pattern, case=False, na=False)]

    # Base event filter
    if selected_base_event != 'Select Event...':
        analysis_df = analysis_df[analysis_df['base_event'] == selected_base_event]
    else:
        st.info("Please select an event to see Top 8 analysis")
        return

    # Classification filter
    if selected_class != 'All Classifications':
        analysis_df = analysis_df[analysis_df['classification'] == selected_class]

    if analysis_df.empty:
        st.warning("No data matches your filters")
        return

    # Determine if track or field event
    is_field = any(x in selected_base_event.lower() for x in ['throw', 'put', 'javelin', 'discus', 'jump', 'vault', 'club'])

    # Get performance column
    if 'performance_numeric' in analysis_df.columns:
        perf_col = 'performance_numeric'
    elif 'performance_clean' in analysis_df.columns:
        perf_col = 'performance_clean'
    else:
        st.warning("Performance data not available")
        return

    # Remove NaN performances
    valid_df = analysis_df[analysis_df[perf_col].notna()].copy()

    if valid_df.empty:
        st.warning("No valid performance data for this selection")
        return

    # Build event title
    gender_str = f"{selected_gender}'s " if selected_gender != 'All' else ""
    class_str = f" {selected_class}" if selected_class != 'All Classifications' else " (All Classes)"
    event_title = f"{gender_str}{selected_base_event}{class_str}"

    st.markdown(f"### Top 8 Performances: {event_title}")
    st.caption(f"{'Higher is better (field event)' if is_field else 'Lower is better (track event)'}")

    # Get top 8 (or top 12 for more context)
    col1, col2 = st.columns([3, 1])
    with col2:
        num_results = st.selectbox("Show Top", [8, 10, 12, 20], key="top8_num")

    # Sort and get top performers
    if is_field:
        top_df = valid_df.nlargest(num_results, perf_col)
    else:
        top_df = valid_df.nsmallest(num_results, perf_col)

    # Display table
    display_cols = ['athlete_name', 'nationality', 'classification', 'performance', 'competitionname', 'competitiondate']
    available_cols = [c for c in display_cols if c in top_df.columns]

    if available_cols:
        display_df = top_df[available_cols].copy()
        display_df = display_df.reset_index(drop=True)
        display_df.index = display_df.index + 1
        display_df.index.name = 'Rank'

        # Add medal indicators
        def add_medal(rank):
            if rank == 1: return "🥇"
            if rank == 2: return "🥈"
            if rank == 3: return "🥉"
            return ""

        display_df.insert(0, '', [add_medal(i) for i in range(1, len(display_df) + 1)])

        st.dataframe(display_df, use_container_width=True)

    # Visualization
    if len(top_df) > 0:
        # Create bar chart
        chart_df = top_df.head(num_results).copy()
        chart_df['rank'] = range(1, len(chart_df) + 1)
        chart_df['display_name'] = chart_df['athlete_name'] + ' (' + chart_df['nationality'].fillna('') + ')'

        fig = px.bar(
            chart_df,
            x='display_name',
            y=perf_col,
            color='classification' if selected_class == 'All Classifications' else 'nationality',
            title=f"Top {num_results} - {event_title}",
            labels={perf_col: 'Performance', 'display_name': 'Athlete'},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_tickangle=-45,
            showlegend=True,
            legend_title='Classification' if selected_class == 'All Classifications' else 'Country'
        )

        # Add horizontal lines for medal positions
        if is_field:
            for i, (idx, row) in enumerate(chart_df.head(3).iterrows()):
                color = ['gold', 'silver', '#CD7F32'][i]
                fig.add_hline(y=row[perf_col], line_dash="dash", line_color=color, opacity=0.5)
        else:
            for i, (idx, row) in enumerate(chart_df.head(3).iterrows()):
                color = ['gold', 'silver', '#CD7F32'][i]
                fig.add_hline(y=row[perf_col], line_dash="dash", line_color=color, opacity=0.5)

        st.plotly_chart(fig, use_container_width=True)

    # Statistics summary
    st.markdown("### Performance Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Gold Standard", f"{top_df[perf_col].iloc[0]:.2f}" if len(top_df) > 0 else "N/A")

    with col2:
        if len(top_df) >= 3:
            st.metric("Bronze Standard", f"{top_df[perf_col].iloc[2]:.2f}")
        else:
            st.metric("Bronze Standard", "N/A")

    with col3:
        if len(top_df) >= 8:
            st.metric("Finals Standard (8th)", f"{top_df[perf_col].iloc[7]:.2f}")
        else:
            st.metric("Finals Standard", "N/A")

    with col4:
        st.metric("Athletes in Event", len(valid_df['athlete_name'].unique()))

    # By classification breakdown (if showing all classifications)
    if selected_class == 'All Classifications':
        st.markdown("### Top 3 by Classification")

        class_breakdown = valid_df.groupby('classification').apply(
            lambda x: x.nlargest(3, perf_col) if is_field else x.nsmallest(3, perf_col)
        ).reset_index(drop=True)

        for classification in sorted(valid_df['classification'].dropna().unique())[:8]:
            class_df = valid_df[valid_df['classification'] == classification]
            if len(class_df) > 0:
                class_top = class_df.nlargest(3, perf_col) if is_field else class_df.nsmallest(3, perf_col)

                with st.expander(f"{classification} - Top 3 ({len(class_df)} athletes)"):
                    disp_cols = ['athlete_name', 'nationality', 'performance', 'competitionname', 'competitiondate']
                    avail_cols = [c for c in disp_cols if c in class_top.columns]
                    if avail_cols:
                        st.dataframe(class_top[avail_cols], use_container_width=True, hide_index=True)

def show_competitor_intelligence(filtered_df, full_df):
    """Competitor threat analysis - mode-aware"""
    competition_mode = st.session_state.get('competition_mode', 'Asian Games 2026')
    st.markdown(f"## 🎯 Competitor Intelligence - {competition_mode}")

    # Load rankings based on competition mode
    if competition_mode == "Asian Games 2026":
        st.markdown("### Asian Region Focus")

        # Asian countries list
        asian_countries = ['CHN', 'JPN', 'KOR', 'IND', 'THA', 'MAS', 'SIN', 'INA', 'PHI', 'VIE',
                          'IRN', 'IRQ', 'KSA', 'UAE', 'QAT', 'KUW', 'BRN', 'OMA', 'JOR', 'LBN',
                          'PAK', 'AFG', 'UZB', 'KAZ', 'TKM', 'KGZ', 'TJK', 'MGL', 'TPE', 'HKG']

        # Filter to Asian competitors
        asian_df = full_df[full_df['nationality'].isin(asian_countries)]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Asian Athletes", asian_df['athleteid'].nunique())
        with col2:
            st.metric("Asian Countries", asian_df['nationality'].nunique())
        with col3:
            saudi_rank = len(asian_df[asian_df['nationality'] == 'KSA']['athleteid'].unique())
            st.metric("Saudi Athletes", saudi_rank)

        # Load Asian rankings if available
        rankings_path = Path("data/Rankings")
        asian_rankings = []

        if rankings_path.exists():
            for csv_file in rankings_path.glob("*Asian*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    parts = csv_file.stem.split("_")
                    year = parts[-1] if parts and parts[-1].isdigit() else "Unknown"
                    df['ranking_year'] = year
                    asian_rankings.append(df)
                except:
                    continue

        if asian_rankings:
            rankings_df = pd.concat(asian_rankings, ignore_index=True)
            st.markdown("### Asian Rankings Data")
            st.caption(f"Loaded {len(rankings_df)} ranking entries")

            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                if 'ranking_year' in rankings_df.columns:
                    years = ['All'] + sorted(rankings_df['ranking_year'].unique(), reverse=True)
                    selected_year = st.selectbox("Year", years, key="intel_year")
                else:
                    selected_year = 'All'

            with col2:
                event_col = 'Event' if 'Event' in rankings_df.columns else 'event'
                if event_col in rankings_df.columns:
                    events = ['All'] + sorted(rankings_df[event_col].dropna().unique().tolist())
                    selected_event = st.selectbox("Event", events, key="intel_event")
                else:
                    selected_event = 'All'

            # Apply filters
            display_rankings = rankings_df.copy()
            if selected_year != 'All' and 'ranking_year' in display_rankings.columns:
                display_rankings = display_rankings[display_rankings['ranking_year'] == selected_year]
            if selected_event != 'All' and event_col in display_rankings.columns:
                display_rankings = display_rankings[display_rankings[event_col] == selected_event]

            st.dataframe(display_rankings.head(100), use_container_width=True, hide_index=True)

            # Country distribution
            nat_col = 'Country' if 'Country' in display_rankings.columns else 'Nat'
            if nat_col in display_rankings.columns:
                st.markdown("#### Rankings by Country")
                country_counts = display_rankings[nat_col].value_counts().head(15)

                fig = px.bar(
                    x=country_counts.index,
                    y=country_counts.values,
                    labels={'x': 'Country', 'y': 'Ranked Athletes'},
                    color_discrete_sequence=[COLORS['teal']]
                )
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Asian rankings not loaded. Check data/Rankings/ folder.")

        # Top Asian competitors by event (from results data)
        st.markdown("### Top Asian Competitors by Event")

        base_events = sorted(asian_df['eventname'].unique())
        selected_event_comp = st.selectbox("Select Event", ['Select...'] + list(base_events), key="asian_comp_event")

        if selected_event_comp != 'Select...':
            event_df = asian_df[asian_df['eventname'] == selected_event_comp].copy()

            if 'performance_clean' in event_df.columns:
                perf_col = 'performance_clean'
            elif 'performance_numeric' in event_df.columns:
                perf_col = 'performance_numeric'
            else:
                st.warning("Performance data not available")
                return

            # Determine if track or field
            is_field = any(x in selected_event_comp.lower() for x in ['throw', 'put', 'javelin', 'discus', 'jump', 'vault'])

            # Get top performers
            valid_df = event_df[event_df[perf_col].notna()]
            if is_field:
                top_perfs = valid_df.groupby(['athlete_name', 'nationality'])[perf_col].max().reset_index()
                top_perfs = top_perfs.nlargest(20, perf_col)
            else:
                top_perfs = valid_df.groupby(['athlete_name', 'nationality'])[perf_col].min().reset_index()
                top_perfs = top_perfs.nsmallest(20, perf_col)

            top_perfs.columns = ['Athlete', 'Country', 'Best Performance']
            top_perfs['Rank'] = range(1, len(top_perfs) + 1)
            top_perfs = top_perfs[['Rank', 'Athlete', 'Country', 'Best Performance']]

            # Highlight Saudi athletes
            st.dataframe(top_perfs, use_container_width=True, hide_index=True)

            # Saudi position
            saudi_athletes = top_perfs[top_perfs['Country'] == 'KSA']
            if len(saudi_athletes) > 0:
                st.success(f"**Saudi Position**: {len(saudi_athletes)} Saudi athlete(s) in top 20")
            else:
                st.warning("No Saudi athletes in top 20 for this event")

    else:
        # LA Paralympics mode - global focus
        st.markdown("### Global Competition Focus")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Athletes", full_df['athleteid'].nunique())
        with col2:
            st.metric("Countries", full_df['nationality'].nunique())
        with col3:
            saudi_count = len(full_df[full_df['nationality'] == 'KSA']['athleteid'].unique())
            st.metric("Saudi Athletes", saudi_count)

        # Top performers globally
        st.markdown("### Top Global Competitors by Event")

        base_events = sorted(filtered_df['eventname'].unique())
        selected_event_global = st.selectbox("Select Event", ['Select...'] + list(base_events), key="global_comp_event")

        if selected_event_global != 'Select...':
            event_df = full_df[full_df['eventname'] == selected_event_global].copy()

            if 'performance_clean' in event_df.columns:
                perf_col = 'performance_clean'
            elif 'performance_numeric' in event_df.columns:
                perf_col = 'performance_numeric'
            else:
                st.warning("Performance data not available")
                return

            is_field = any(x in selected_event_global.lower() for x in ['throw', 'put', 'javelin', 'discus', 'jump', 'vault'])

            valid_df = event_df[event_df[perf_col].notna()]
            if is_field:
                top_perfs = valid_df.groupby(['athlete_name', 'nationality'])[perf_col].max().reset_index()
                top_perfs = top_perfs.nlargest(30, perf_col)
            else:
                top_perfs = valid_df.groupby(['athlete_name', 'nationality'])[perf_col].min().reset_index()
                top_perfs = top_perfs.nsmallest(30, perf_col)

            top_perfs.columns = ['Athlete', 'Country', 'Best Performance']
            top_perfs['Rank'] = range(1, len(top_perfs) + 1)
            top_perfs = top_perfs[['Rank', 'Athlete', 'Country', 'Best Performance']]

            st.dataframe(top_perfs, use_container_width=True, hide_index=True)

            saudi_athletes = top_perfs[top_perfs['Country'] == 'KSA']
            if len(saudi_athletes) > 0:
                st.success(f"**Saudi Position**: {len(saudi_athletes)} Saudi athlete(s) in top 30")
            else:
                st.warning("No Saudi athletes in top 30 for this event")

def show_season_progression(filtered_df, full_df):
    """Season progression tracking"""
    st.markdown("## 📈 Season Progression")

    if filtered_df.empty:
        st.warning("No data available with current filters")
        return

    # Athlete selection
    athletes = sorted(filtered_df['athlete_name'].unique())
    selected_athlete = st.selectbox("Select Athlete", athletes, key="progression_athlete")

    if not selected_athlete:
        return

    athlete_df = filtered_df[filtered_df['athlete_name'] == selected_athlete].copy()

    if athlete_df.empty:
        st.warning("No data for selected athlete")
        return

    # Event selection for this athlete
    athlete_events = sorted(athlete_df['eventname'].unique())
    selected_event = st.selectbox("Select Event", athlete_events, key="progression_event")

    if not selected_event:
        return

    event_df = athlete_df[athlete_df['eventname'] == selected_event].copy()

    # Get performance column
    if 'performance_numeric' in event_df.columns:
        perf_col = 'performance_numeric'
    elif 'performance_clean' in event_df.columns:
        perf_col = 'performance_clean'
    else:
        st.warning("Performance data not available")
        return

    # Parse dates and sort
    if 'competitiondate' in event_df.columns:
        event_df['date_parsed'] = pd.to_datetime(event_df['competitiondate'], format='%d/%m/%Y', errors='coerce')
        event_df = event_df.sort_values('date_parsed')

    # Determine if track or field
    is_field = any(x in selected_event.lower() for x in ['throw', 'put', 'javelin', 'discus', 'jump', 'vault'])

    # Display athlete info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Performances", len(event_df))
    with col2:
        nationality = event_df['nationality'].iloc[0] if 'nationality' in event_df.columns else 'Unknown'
        st.metric("Nationality", nationality)
    with col3:
        classification = event_df['classification'].iloc[0] if 'classification' in event_df.columns else 'Unknown'
        st.metric("Classification", classification)

    # Season bests
    st.markdown("### 📅 Season Bests")

    if 'year' in event_df.columns:
        valid_df = event_df[event_df[perf_col].notna()]

        if is_field:
            season_bests = valid_df.groupby('year')[perf_col].max().reset_index()
        else:
            season_bests = valid_df.groupby('year')[perf_col].min().reset_index()

        season_bests.columns = ['Season', 'Best Performance']
        season_bests = season_bests.sort_values('Season')

        if len(season_bests) > 0:
            # Progression chart
            fig = px.line(
                season_bests,
                x='Season',
                y='Best Performance',
                markers=True,
                title=f"Season Progression - {selected_athlete} - {selected_event}"
            )

            # Invert y-axis for track events (lower is better)
            if not is_field:
                fig.update_yaxes(autorange="reversed")

            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis_title="Season",
                yaxis_title="Performance"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show table
            st.dataframe(season_bests, use_container_width=True, hide_index=True)

            # Calculate improvement
            if len(season_bests) >= 2:
                first = season_bests['Best Performance'].iloc[0]
                last = season_bests['Best Performance'].iloc[-1]
                improvement = last - first if is_field else first - last

                if improvement > 0:
                    st.success(f"Overall improvement: {improvement:.2f}")
                elif improvement < 0:
                    st.warning(f"Overall regression: {abs(improvement):.2f}")
                else:
                    st.info("No change in performance")

    # All performances timeline
    st.markdown("### 📊 All Performances")

    if 'date_parsed' in event_df.columns and not event_df['date_parsed'].isna().all():
        valid_perfs = event_df[event_df[perf_col].notna()]

        fig = px.scatter(
            valid_perfs,
            x='date_parsed',
            y=perf_col,
            color='competitionname' if 'competitionname' in valid_perfs.columns else None,
            title="Performance Timeline"
        )

        if not is_field:
            fig.update_yaxes(autorange="reversed")

        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    # Performance history table
    display_cols = ['competitiondate', 'competitionname', 'performance', 'classification']
    available_cols = [c for c in display_cols if c in event_df.columns]
    if available_cols:
        st.dataframe(event_df[available_cols], use_container_width=True, hide_index=True)

def show_saudi_athletes(filtered_df, full_df):
    """Saudi athletes specific view"""
    st.markdown("## 🇸🇦 Saudi Athletes")

    saudi_df = full_df[full_df['nationality'] == 'KSA']

    if saudi_df.empty:
        st.warning("No Saudi athlete data found")
        return

    # Saudi statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Performances", len(saudi_df))

    with col2:
        st.metric("Unique Athletes", saudi_df['athleteid'].nunique())

    with col3:
        st.metric("Events", saudi_df['eventname'].nunique())

    with col4:
        st.metric("Competitions", saudi_df['competitionname'].nunique())

    # Saudi athletes list
    st.markdown("### 👥 Saudi Athletes")

    # Get performance column
    perf_col = 'performance_clean' if 'performance_clean' in saudi_df.columns else 'performance'

    saudi_summary = saudi_df.groupby('athlete_name').agg({
        'eventname': 'nunique',
        'competitionname': 'nunique',
        'competitiondate': ['min', 'max'],
        perf_col: 'count'
    }).reset_index()

    saudi_summary.columns = ['Athlete', 'Events', 'Competitions', 'First_Comp', 'Last_Comp', 'Total_Perfs']
    saudi_summary = saudi_summary.sort_values('Total_Perfs', ascending=False)

    st.dataframe(saudi_summary, use_container_width=True, hide_index=True)

    # Individual athlete details
    st.markdown("### 🔍 Athlete Details")

    selected_saudi = st.selectbox(
        "Select Saudi Athlete",
        saudi_summary['Athlete'].tolist(),
        key="saudi_athlete_detail"
    )

    if selected_saudi:
        athlete_data = saudi_df[saudi_df['athlete_name'] == selected_saudi]

        # Events breakdown
        st.markdown(f"#### Events for {selected_saudi}")

        event_summary = athlete_data.groupby('eventname').agg({
            perf_col: 'count',
            'competitiondate': 'max'
        }).reset_index()
        event_summary.columns = ['Event', 'Performances', 'Last Performance']
        event_summary = event_summary.sort_values('Performances', ascending=False)

        st.dataframe(event_summary, use_container_width=True, hide_index=True)

        # Recent performances
        st.markdown("#### Recent Performances")
        recent = athlete_data.sort_values('competitiondate', ascending=False).head(10)
        display_cols = ['eventname', 'performance', 'competitionname', 'competitiondate', 'classification']
        available_cols = [c for c in display_cols if c in recent.columns]
        if available_cols:
            st.dataframe(recent[available_cols], use_container_width=True, hide_index=True)

def load_classification_overrides():
    """Load athlete classification overrides from JSON file"""
    override_file = Path('data/classification_overrides.json')
    if override_file.exists():
        try:
            with open(override_file, 'r') as f:
                return json.load(f)
        except:
            return {'overrides': [], 'excluded_athletes': []}
    return {'overrides': [], 'excluded_athletes': []}

def save_classification_overrides(overrides_data):
    """Save athlete classification overrides to JSON file"""
    override_file = Path('data/classification_overrides.json')
    override_file.parent.mkdir(parents=True, exist_ok=True)
    with open(override_file, 'w') as f:
        json.dump(overrides_data, f, indent=2)

def show_data_management(df):
    """Data management and athlete classification updates"""
    st.markdown("## ⚙️ Data Management")

    # Load existing overrides
    overrides_data = load_classification_overrides()

    # Tabs for different management functions
    tab1, tab2, tab3 = st.tabs(["🔄 Classification Overrides", "🚫 Exclude Athletes", "📊 Data Summary"])

    with tab1:
        st.markdown("### 🔄 Athlete Classification Override")
        st.caption("Override an athlete's classification when they've been reclassified. This affects how they appear in analysis.")

        # Search for athlete to override
        col1, col2 = st.columns([2, 1])

        with col1:
            # Country filter to narrow down search
            countries = ['All Countries'] + sorted(df['nationality'].dropna().unique().tolist())
            selected_country = st.selectbox("Filter by Country", countries, key="override_country")

        # Filter athletes
        if selected_country != 'All Countries':
            athlete_df = df[df['nationality'] == selected_country]
        else:
            athlete_df = df

        athletes = sorted(athlete_df['athlete_name'].unique().tolist())

        with col2:
            st.metric("Athletes", len(athletes))

        # Select athlete
        selected_athlete = st.selectbox(
            "Select Athlete to Override",
            ['Select athlete...'] + athletes,
            key="override_athlete"
        )

        if selected_athlete != 'Select athlete...':
            # Show current classifications for this athlete
            athlete_data = df[df['athlete_name'] == selected_athlete]
            current_classes = athlete_data['classification'].dropna().unique().tolist()

            st.markdown(f"**Current classifications in database:** {', '.join(current_classes)}")

            # Show recent performances
            st.markdown("**Recent Performances:**")
            recent = athlete_data.nlargest(5, 'competitiondate') if 'competitiondate' in athlete_data.columns else athlete_data.head(5)
            display_cols = ['competitiondate', 'eventname', 'classification', 'performance', 'competitionname']
            avail_cols = [c for c in display_cols if c in recent.columns]
            st.dataframe(recent[avail_cols], use_container_width=True, hide_index=True)

            # Override form
            st.markdown("---")
            st.markdown("**Set Classification Override:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                # All possible classifications
                all_classifications = sorted(df['classification'].dropna().unique().tolist())
                new_class = st.selectbox("New Classification", all_classifications, key="new_classification")

            with col2:
                # Effective date
                effective_date = st.date_input("Effective From", key="effective_date")

            with col3:
                reason = st.text_input("Reason (optional)", placeholder="e.g., IPC reclassification", key="override_reason")

            if st.button("Add Classification Override", type="primary", key="add_override"):
                # Add to overrides
                new_override = {
                    'athlete_name': selected_athlete,
                    'old_classifications': current_classes,
                    'new_classification': new_class,
                    'effective_date': str(effective_date),
                    'reason': reason,
                    'added_date': str(datetime.now().date())
                }
                overrides_data['overrides'].append(new_override)
                save_classification_overrides(overrides_data)
                st.success(f"Override added: {selected_athlete} → {new_class} from {effective_date}")
                st.rerun()

        # Show existing overrides
        st.markdown("---")
        st.markdown("### Current Classification Overrides")

        if overrides_data['overrides']:
            override_df = pd.DataFrame(overrides_data['overrides'])
            st.dataframe(override_df, use_container_width=True, hide_index=True)

            # Remove override
            st.markdown("**Remove Override:**")
            override_athletes = [o['athlete_name'] for o in overrides_data['overrides']]
            remove_athlete = st.selectbox("Select to remove", ['Select...'] + override_athletes, key="remove_override")

            if remove_athlete != 'Select...' and st.button("Remove Override", type="secondary"):
                overrides_data['overrides'] = [o for o in overrides_data['overrides'] if o['athlete_name'] != remove_athlete]
                save_classification_overrides(overrides_data)
                st.success(f"Removed override for {remove_athlete}")
                st.rerun()
        else:
            st.info("No classification overrides configured")

    with tab2:
        st.markdown("### 🚫 Exclude Athletes from Analysis")
        st.caption("Exclude athletes entirely from analysis (e.g., retired, suspended, or classification protests)")

        # Search for athlete to exclude
        col1, col2 = st.columns([2, 1])

        with col1:
            countries_excl = ['All Countries'] + sorted(df['nationality'].dropna().unique().tolist())
            selected_country_excl = st.selectbox("Filter by Country", countries_excl, key="exclude_country")

        if selected_country_excl != 'All Countries':
            athlete_df_excl = df[df['nationality'] == selected_country_excl]
        else:
            athlete_df_excl = df

        athletes_excl = sorted(athlete_df_excl['athlete_name'].unique().tolist())

        exclude_athlete = st.selectbox(
            "Select Athlete to Exclude",
            ['Select athlete...'] + athletes_excl,
            key="exclude_athlete"
        )

        if exclude_athlete != 'Select athlete...':
            athlete_info = df[df['athlete_name'] == exclude_athlete].iloc[0]
            st.markdown(f"**Nationality:** {athlete_info.get('nationality', 'Unknown')}")
            st.markdown(f"**Classifications:** {', '.join(df[df['athlete_name'] == exclude_athlete]['classification'].dropna().unique())}")

            exclude_reason = st.text_input("Reason for exclusion", placeholder="e.g., Classification under protest", key="exclude_reason")

            if st.button("Exclude Athlete", type="primary", key="add_exclusion"):
                if exclude_athlete not in overrides_data['excluded_athletes']:
                    exclusion = {
                        'athlete_name': exclude_athlete,
                        'nationality': athlete_info.get('nationality', 'Unknown'),
                        'reason': exclude_reason,
                        'excluded_date': str(datetime.now().date())
                    }
                    if 'excluded_athletes' not in overrides_data:
                        overrides_data['excluded_athletes'] = []
                    overrides_data['excluded_athletes'].append(exclusion)
                    save_classification_overrides(overrides_data)
                    st.success(f"Excluded {exclude_athlete} from analysis")
                    st.rerun()
                else:
                    st.warning("Athlete already excluded")

        # Show excluded athletes
        st.markdown("---")
        st.markdown("### Currently Excluded Athletes")

        if overrides_data.get('excluded_athletes'):
            excluded_df = pd.DataFrame(overrides_data['excluded_athletes'])
            st.dataframe(excluded_df, use_container_width=True, hide_index=True)

            # Reinstate athlete
            st.markdown("**Reinstate Athlete:**")
            excluded_names = [e['athlete_name'] if isinstance(e, dict) else e for e in overrides_data['excluded_athletes']]
            reinstate_athlete = st.selectbox("Select to reinstate", ['Select...'] + excluded_names, key="reinstate_athlete")

            if reinstate_athlete != 'Select...' and st.button("Reinstate Athlete", type="secondary"):
                overrides_data['excluded_athletes'] = [
                    e for e in overrides_data['excluded_athletes']
                    if (e['athlete_name'] if isinstance(e, dict) else e) != reinstate_athlete
                ]
                save_classification_overrides(overrides_data)
                st.success(f"Reinstated {reinstate_athlete}")
                st.rerun()
        else:
            st.info("No athletes currently excluded")

    with tab3:
        st.markdown("### 📊 Data Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Athletes", f"{df['athlete_name'].nunique():,}")

        with col2:
            st.metric("Total Results", f"{len(df):,}")

        with col3:
            st.metric("Classifications", df['classification'].nunique())

        with col4:
            st.metric("Countries", df['nationality'].nunique())

        # Classification distribution
        st.markdown("### Classification Distribution")
        class_counts = df['classification'].value_counts().head(20)
        fig = px.bar(
            x=class_counts.index,
            y=class_counts.values,
            labels={'x': 'Classification', 'y': 'Result Count'},
            title="Top 20 Classifications by Result Count"
        )
        fig.update_layout(plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

        # Athletes with multiple classifications (potential reclassifications)
        st.markdown("### Athletes with Multiple Classifications")
        st.caption("These athletes may have been reclassified over time")

        multi_class = df.groupby('athlete_name')['classification'].nunique()
        multi_class = multi_class[multi_class > 1].sort_values(ascending=False).head(20)

        if len(multi_class) > 0:
            multi_class_details = []
            for athlete in multi_class.index:
                athlete_df = df[df['athlete_name'] == athlete]
                classes = athlete_df['classification'].dropna().unique()
                nationality = athlete_df['nationality'].iloc[0] if 'nationality' in athlete_df.columns else 'Unknown'
                multi_class_details.append({
                    'Athlete': athlete,
                    'Nationality': nationality,
                    'Classifications': ', '.join(sorted(classes)),
                    'Num Classes': len(classes)
                })

            multi_df = pd.DataFrame(multi_class_details)
            st.dataframe(multi_df, use_container_width=True, hide_index=True)
        else:
            st.info("No athletes with multiple classifications found")

if __name__ == "__main__":
    main()
