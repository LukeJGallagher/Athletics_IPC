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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
            padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
    <h1 style="color: white; margin: 0;">🏃‍♂️ Para Athletics Dashboard</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
        Real-time data from Azure Blob Storage (Parquet)
    </p>
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

def parse_performance(perf_str):
    """Parse performance string to float value"""
    if pd.isna(perf_str) or perf_str == '':
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

# Load data
with st.spinner("Loading data..."):
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏃 Results", "📈 Rankings", "🏆 Records", "🇸🇦 Saudi Arabia", "📊 Championship Analysis", "👤 Athlete Analysis"])

with tab1:
    st.markdown("### Competition Results")

    if len(results_df) > 0:
        col1, col2 = st.columns(2)

        with col1:
            # Filter by nationality
            nationalities = ['All'] + sorted(results_df['nationality'].dropna().unique().tolist())
            selected_nat = st.selectbox("Filter by Nationality", nationalities)

        with col2:
            # Filter by event
            events = ['All'] + sorted(results_df['event_name'].dropna().unique().tolist())
            selected_event = st.selectbox("Filter by Event", events)

        # Apply filters
        filtered_df = results_df.copy()
        if selected_nat != 'All':
            filtered_df = filtered_df[filtered_df['nationality'] == selected_nat]
        if selected_event != 'All':
            filtered_df = filtered_df[filtered_df['event_name'] == selected_event]

        st.dataframe(
            filtered_df[['competition_name', 'event_name', 'athlete_name',
                        'nationality', 'performance', 'date']].head(100),
            use_container_width=True,
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
        st.plotly_chart(fig, use_container_width=True)
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
                selected_year = st.selectbox("Filter by Year", years)
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
            use_container_width=True,
            hide_index=True
        )

        # Saudi athletes in rankings
        nat_col = 'Nat' if 'Nat' in rankings_df.columns else 'nationality' if 'nationality' in rankings_df.columns else None
        if nat_col:
            saudi_rankings = filtered_rankings[filtered_rankings[nat_col] == 'KSA']
            if len(saudi_rankings) > 0:
                st.markdown("#### Saudi Athletes in Rankings")
                st.dataframe(saudi_rankings, use_container_width=True, hide_index=True)
    else:
        st.info("No rankings data available. Check data/Rankings/ folder or run scrapers.")

with tab3:
    st.markdown("### World & Regional Records")

    if len(records_df) > 0:
        # Show record type filter
        if 'record_type' in records_df.columns:
            record_types = ['All'] + sorted(records_df['record_type'].dropna().unique().tolist())
            selected_record_type = st.selectbox("Filter by Record Type", record_types)

            filtered_records = records_df.copy()
            if selected_record_type != 'All':
                filtered_records = filtered_records[filtered_records['record_type'] == selected_record_type]

            # Show metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", f"{len(filtered_records):,}")
            with col2:
                if 'Event' in filtered_records.columns:
                    st.metric("Events", filtered_records['Event'].nunique())
                elif 'event' in filtered_records.columns:
                    st.metric("Events", filtered_records['event'].nunique())
            with col3:
                if 'record_type' in filtered_records.columns:
                    st.metric("Record Types", records_df['record_type'].nunique())

            # Display table
            st.dataframe(
                filtered_records.head(200),
                use_container_width=True,
                hide_index=True
            )

            # Record type distribution chart
            st.markdown("#### Records by Type")
            type_counts = records_df['record_type'].value_counts()
            fig = px.bar(
                x=type_counts.index,
                y=type_counts.values,
                labels={'x': 'Record Type', 'y': 'Count'}
            )
            fig.update_traces(marker_color=GOLD_ACCENT)
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', color='#333'),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(
                records_df.head(100),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No records data available. Check data/Records/ folder or run scrapers.")

with tab4:
    st.markdown("### 🇸🇦 Saudi Arabia Performance")

    if len(results_df) > 0:
        saudi_df = results_df[results_df['nationality'] == 'KSA']

        if len(saudi_df) > 0:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Saudi Results", f"{len(saudi_df):,}")
            with col2:
                saudi_athletes = saudi_df['athlete_name'].nunique()
                st.metric("Saudi Athletes", f"{saudi_athletes:,}")
            with col3:
                saudi_events = saudi_df['event_name'].nunique()
                st.metric("Events Competed", f"{saudi_events:,}")

            st.markdown("#### Recent Saudi Performances")
            st.dataframe(
                saudi_df[['competition_name', 'event_name', 'athlete_name',
                         'performance', 'date']].head(50),
                use_container_width=True,
                hide_index=True
            )

            # Top Saudi events
            st.markdown("#### Top Saudi Events by Participation")
            top_events = saudi_df['event_name'].value_counts().head(10)
            fig = px.bar(
                x=top_events.values,
                y=top_events.index,
                orientation='h',
                labels={'x': 'Number of Results', 'y': 'Event'}
            )
            fig.update_traces(marker_color=TEAL_PRIMARY)
            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', color='#333')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No Saudi Arabia (KSA) results found in database yet.")
    else:
        st.info("No results data available yet. Run the GitHub workflow to populate.")

with tab5:
    st.markdown("### Championship Winning Standards Analysis")

    if len(results_df) > 0:
        # Get major championships
        major_df = get_major_championships(results_df)

        if len(major_df) > 0:
            # Overview metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Major Championship Results", f"{len(major_df):,}")
            with col2:
                unique_comps = major_df['competition_name'].nunique()
                st.metric("Championships", f"{unique_comps:,}")
            with col3:
                unique_events = major_df['event_name'].nunique()
                st.metric("Events", f"{unique_events:,}")

            # Championship type distribution
            st.markdown("#### Championship Type Distribution")
            comp_counts = major_df['competition_type'].value_counts()
            fig = px.pie(
                values=comp_counts.values,
                names=comp_counts.index,
                color_discrete_sequence=[TEAL_PRIMARY, GOLD_ACCENT, TEAL_LIGHT, GRAY_BLUE]
            )
            fig.update_layout(
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', color='#333')
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.markdown("#### Medal Standards by Event")

            # Event filter
            events = ['All'] + sorted(major_df['event_name'].dropna().unique().tolist())
            selected_event = st.selectbox("Select Event to Analyze", events, key="championship_event")

            # Analyze standards
            with st.spinner("Analyzing championship standards..."):
                standards_df = analyze_championship_standards(major_df, selected_event)

            if not standards_df.empty:
                st.markdown(f"**Found {len(standards_df)} event/competition combinations**")

                # Display standards table
                st.dataframe(
                    standards_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Gold': st.column_config.TextColumn('Gold', help='Gold medal performance'),
                        'Silver': st.column_config.TextColumn('Silver', help='Silver medal performance'),
                        'Bronze': st.column_config.TextColumn('Bronze', help='Bronze medal performance'),
                        'Final_8th': st.column_config.TextColumn('8th Place', help='8th place performance (finals cutoff)')
                    }
                )

                # Download button
                csv = standards_df.to_csv(index=False)
                st.download_button(
                    label="Download Championship Standards CSV",
                    data=csv,
                    file_name="championship_standards.csv",
                    mime="text/csv"
                )

                # Chart: Gold standards by competition
                if selected_event != 'All' and len(standards_df) > 1:
                    st.markdown("#### Gold Medal Performance Trends")

                    chart_df = standards_df[standards_df['Gold'].notna()].copy()
                    chart_df['Gold_Value'] = chart_df['Gold'].apply(parse_performance)
                    chart_df = chart_df.dropna(subset=['Gold_Value'])

                    if not chart_df.empty:
                        fig = px.bar(
                            chart_df,
                            x='Competition',
                            y='Gold_Value',
                            text='Gold',
                            color_discrete_sequence=[GOLD_ACCENT]
                        )
                        fig.update_layout(
                            xaxis_title='Competition',
                            yaxis_title='Performance',
                            showlegend=False,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            font=dict(family='Inter, sans-serif', color='#333'),
                            xaxis_tickangle=-45
                        )
                        fig.update_traces(textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Select an event or adjust filters to see championship standards.")

            # Saudi Athletes at Major Championships
            st.markdown("---")
            st.markdown("#### Saudi Athletes at Major Championships")

            saudi_major = major_df[major_df['nationality'] == 'KSA']
            if len(saudi_major) > 0:
                st.markdown(f"**{len(saudi_major)} Saudi performances at major championships**")

                # Saudi athlete summary
                saudi_summary = saudi_major.groupby(['athlete_name', 'event_name']).agg({
                    'competition_name': 'count',
                    'performance': 'first'
                }).reset_index()
                saudi_summary.columns = ['Athlete', 'Event', 'Championships', 'Best Performance']

                st.dataframe(saudi_summary, use_container_width=True, hide_index=True)

                # Download Saudi championship data
                csv_saudi = saudi_major.to_csv(index=False)
                st.download_button(
                    label="Download Saudi Championship Results",
                    data=csv_saudi,
                    file_name="saudi_championship_results.csv",
                    mime="text/csv",
                    key="saudi_download"
                )
            else:
                st.info("No Saudi athletes found in major championship results.")
        else:
            st.warning("No major championship data found in results. Data may need event classification.")
    else:
        st.info("No results data available yet. Run the GitHub workflow to populate.")

with tab6:
    st.markdown("### Athlete Analysis & Event Comparison")

    if len(results_df) > 0:
        # Athlete search
        col1, col2 = st.columns(2)

        with col1:
            all_athletes = sorted(results_df['athlete_name'].dropna().unique().tolist())
            selected_athlete = st.selectbox("Select Athlete", [''] + all_athletes, key="athlete_search")

        with col2:
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
            st.plotly_chart(fig, use_container_width=True)

            # Performance history
            st.markdown("#### Performance History")
            st.dataframe(
                athlete_data[['competition_name', 'event_name', 'performance', 'date']].sort_values('date', ascending=False),
                use_container_width=True,
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
                use_container_width=True,
                hide_index=True
            )
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
