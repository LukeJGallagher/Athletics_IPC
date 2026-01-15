"""
Para Athletics Azure Database Dashboard
Connects to Azure SQL and displays real-time data
Includes Championship Analysis capabilities
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import unified database connection module
from azure_db import query_data, get_connection_mode, test_connection

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

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
            padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
    <h1 style="color: white; margin: 0;">🏃‍♂️ Para Athletics Dashboard</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
        Real-time data from Azure SQL Database
    </p>
</div>
""", unsafe_allow_html=True)

# Show connection mode in sidebar
st.sidebar.info(f"📊 Database: {get_connection_mode().upper()}")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_results():
    """Load results from database (Azure SQL or SQLite)"""
    query = """
    SELECT
        competition_name,
        event_name,
        athlete_name,
        nationality,
        performance,
        date,
        scraped_at
    FROM Results
    ORDER BY scraped_at DESC
    """
    try:
        return query_data(query)
    except Exception as e:
        st.error(f"❌ Failed to load results: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_rankings():
    """Load rankings from database (Azure SQL or SQLite)"""
    query = "SELECT * FROM Rankings ORDER BY scraped_at DESC"
    try:
        return query_data(query)
    except Exception as e:
        # Rankings table might not exist, return empty dataframe
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_records():
    """Load records from database (Azure SQL or SQLite)"""
    query = "SELECT * FROM Records ORDER BY scraped_at DESC"
    try:
        return query_data(query)
    except Exception as e:
        # Records table might not exist, return empty dataframe
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏃 Results", "📈 Rankings", "🏆 Records", "🇸🇦 Saudi Arabia", "📊 Championship Analysis"])

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
        st.dataframe(
            rankings_df.head(100),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No rankings data available yet. Run the GitHub workflow to populate.")

with tab3:
    st.markdown("### World Records")

    if len(records_df) > 0:
        st.dataframe(
            records_df.head(100),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No records data available yet. Run the GitHub workflow to populate.")

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

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if len(results_df) > 0:
        last_update = results_df['scraped_at'].max()
        st.caption(f"Last updated: {last_update}")
with col2:
    st.caption(f"Database: {get_connection_mode().upper()} (REDACTED_DB)")
with col3:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
