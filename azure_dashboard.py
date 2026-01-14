"""
Para Athletics Azure Database Dashboard
Connects to Azure SQL and displays real-time data
"""

import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

@st.cache_resource
def get_connection():
    """Connect to Azure SQL Database"""
    conn_str = os.getenv('AZURE_SQL_CONN')
    if not conn_str:
        st.error("⚠️ AZURE_SQL_CONN not found in .env file")
        st.stop()

    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        st.error(f"❌ Failed to connect to Azure SQL: {e}")
        st.stop()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_results(_conn):
    """Load results from Azure SQL"""
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
    return pd.read_sql(query, _conn)

@st.cache_data(ttl=300)
def load_rankings(_conn):
    """Load rankings from Azure SQL"""
    query = "SELECT * FROM Rankings ORDER BY scraped_at DESC"
    return pd.read_sql(query, _conn)

@st.cache_data(ttl=300)
def load_records(_conn):
    """Load records from Azure SQL"""
    query = "SELECT * FROM Records ORDER BY scraped_at DESC"
    return pd.read_sql(query, _conn)

# Connect to database
with st.spinner("Connecting to Azure SQL..."):
    conn = get_connection()

# Load data
with st.spinner("Loading data..."):
    results_df = load_results(conn)
    rankings_df = load_rankings(conn)
    records_df = load_records(conn)

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
tab1, tab2, tab3, tab4 = st.tabs(["🏃 Results", "📈 Rankings", "🏆 Records", "🇸🇦 Saudi Arabia"])

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

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if len(results_df) > 0:
        last_update = results_df['scraped_at'].max()
        st.caption(f"Last updated: {last_update}")
with col2:
    st.caption(f"Database: Azure SQL (REDACTED_DB)")
with col3:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
