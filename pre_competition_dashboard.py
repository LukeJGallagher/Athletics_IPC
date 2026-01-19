"""
Pre-Competition Reports Dashboard
Interactive dashboard for pre-competition championship analysis
Team Saudi Para Athletics Program
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

# Try to import azure_db for data access
try:
    from azure_db import query_data, get_connection_mode
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Team Saudi Brand Colors
TEAL_PRIMARY = '#007167'
GOLD_ACCENT = '#a08e66'
TEAL_DARK = '#005a51'
TEAL_LIGHT = '#009688'
GRAY_BLUE = '#78909C'

# Page config
st.set_page_config(
    page_title="Pre-Competition Reports - Team Saudi",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .medal-gold { background-color: #FFD700; padding: 0.5rem; border-radius: 4px; }
    .medal-silver { background-color: #C0C0C0; padding: 0.5rem; border-radius: 4px; }
    .medal-bronze { background-color: #CD7F32; padding: 0.5rem; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%);
            padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
    <h1 style="color: white; margin: 0;">🎯 Pre-Competition Analysis Dashboard</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
        Championship Standards, Competitor Analysis & Strategic Insights
    </p>
</div>
""", unsafe_allow_html=True)


# ============== DATA LOADING ==============

@st.cache_data(ttl=600)
def load_main_data():
    """Load main results data"""
    # Try Azure SQL first
    if AZURE_AVAILABLE:
        try:
            df = query_data("SELECT * FROM Results")
            if len(df) > 0:
                return df
        except:
            pass

    # Fallback to local CSV
    csv_path = Path("data/Tilastoptija/ksaoutputipc3.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding='latin-1', low_memory=False)
        df.columns = df.columns.str.lower()
        return df
    return pd.DataFrame()

@st.cache_data(ttl=600)
def load_championship_standards():
    """Load championship standards CSV"""
    standards_file = Path("championship_standards_gender_separated.csv")
    if standards_file.exists():
        return pd.read_csv(standards_file)

    # Try non-gender-separated version
    alt_file = Path("championship_standards_report.csv")
    if alt_file.exists():
        return pd.read_csv(alt_file)
    return pd.DataFrame()

@st.cache_data(ttl=600)
def load_top8_analysis():
    """Load detailed top 8 analysis"""
    top8_file = Path("detailed_top8_championship_analysis_gender_separated.csv")
    if top8_file.exists():
        return pd.read_csv(top8_file)

    alt_file = Path("detailed_top8_championship_analysis.csv")
    if alt_file.exists():
        return pd.read_csv(alt_file)
    return pd.DataFrame()

@st.cache_data(ttl=600)
def load_rankings():
    """Load rankings data"""
    rankings_path = Path("data/Rankings")
    if not rankings_path.exists():
        return pd.DataFrame()

    all_rankings = []
    for csv_file in rankings_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            parts = csv_file.stem.split("_")
            year = parts[-1] if parts[-1].isdigit() else "Unknown"
            df['ranking_year'] = year
            df['ranking_type'] = "_".join(parts[:-1])
            all_rankings.append(df)
        except:
            continue

    if all_rankings:
        return pd.concat(all_rankings, ignore_index=True)
    return pd.DataFrame()

@st.cache_data(ttl=600)
def load_records():
    """Load records data"""
    records_path = Path("data/Records")
    if not records_path.exists():
        return pd.DataFrame()

    all_records = []
    record_type_map = {
        "World": "World Record",
        "Paralympic": "Paralympic Record",
        "Asian": "Asian Record",
        "European": "European Record",
        "African": "African Record",
        "Americas": "Americas Record",
        "Championship": "Championship Record"
    }

    for csv_file in records_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            filename = csv_file.stem
            for key, value in record_type_map.items():
                if key in filename:
                    df['record_type'] = value
                    break
            else:
                df['record_type'] = 'Other'
            all_records.append(df)
        except:
            continue

    if all_records:
        return pd.concat(all_records, ignore_index=True)
    return pd.DataFrame()


# ============== HELPER FUNCTIONS ==============

def parse_performance(perf_str):
    """Parse performance string to numeric value"""
    if pd.isna(perf_str) or perf_str == '':
        return np.nan

    perf_str = str(perf_str).strip()

    if any(x in perf_str.upper() for x in ['DNS', 'DNF', 'DQ', 'NM', 'NH', '-']):
        return np.nan

    perf_str = perf_str.rstrip('A').strip()

    if ':' in perf_str:
        parts = perf_str.split(':')
        try:
            if len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except:
            return np.nan

    try:
        return float(perf_str)
    except:
        return np.nan

def is_track_event(event_name):
    """Check if event is track (lower is better)"""
    if pd.isna(event_name):
        return False
    event_name = str(event_name).lower()
    track_events = ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m', 'marathon', 'relay']
    return any(t in event_name for t in track_events)

def get_event_unit(event_name):
    """Get unit for event"""
    if is_track_event(event_name):
        return "seconds"
    return "meters"

def extract_classification(event_name):
    """Extract classification from event name"""
    if pd.isna(event_name):
        return None
    import re
    match = re.search(r'[TF]\d{2}', str(event_name))
    return match.group(0) if match else None

def extract_base_event(event_name):
    """Extract base event without classification"""
    if pd.isna(event_name):
        return None
    import re
    # Remove classification
    base = re.sub(r'\s*[TF]\d{2}\s*', ' ', str(event_name))
    # Remove gender markers
    base = re.sub(r'\s*(Men|Women|M|W)\s*', ' ', base, flags=re.IGNORECASE)
    return base.strip()


# ============== LOAD DATA ==============

with st.spinner("Loading data..."):
    main_df = load_main_data()
    standards_df = load_championship_standards()
    top8_df = load_top8_analysis()
    rankings_df = load_rankings()
    records_df = load_records()

# Sidebar - Event Selection
st.sidebar.markdown(f"""
<div style="background: {TEAL_PRIMARY}; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
    <h3 style="color: white; margin: 0;">Event Selection</h3>
</div>
""", unsafe_allow_html=True)

# Get available events from data
if not standards_df.empty and 'event' in standards_df.columns:
    available_events = sorted(standards_df['event'].dropna().unique().tolist())
    available_classifications = sorted(standards_df['classification'].dropna().unique().tolist()) if 'classification' in standards_df.columns else []
else:
    # Extract from main data
    if not main_df.empty:
        event_col = 'eventname' if 'eventname' in main_df.columns else 'event_name'
        if event_col in main_df.columns:
            all_events = main_df[event_col].dropna().unique()
            available_events = sorted(set(extract_base_event(e) for e in all_events if extract_base_event(e)))
            available_classifications = sorted(set(extract_classification(e) for e in all_events if extract_classification(e)))
        else:
            available_events = []
            available_classifications = []
    else:
        available_events = []
        available_classifications = []

# Event selection
selected_event = st.sidebar.selectbox("Select Event", [''] + available_events)
selected_classification = st.sidebar.selectbox("Select Classification", [''] + available_classifications)
selected_gender = st.sidebar.selectbox("Select Gender", ['', 'M', 'W'], format_func=lambda x: {'': 'All', 'M': 'Men', 'W': 'Women'}.get(x, x))

# Show data status
st.sidebar.markdown("---")
st.sidebar.markdown("### Data Status")
st.sidebar.markdown(f"- Main Data: {len(main_df):,} rows" if not main_df.empty else "- Main Data: Not loaded")
st.sidebar.markdown(f"- Standards: {len(standards_df):,} rows" if not standards_df.empty else "- Standards: Not loaded")
st.sidebar.markdown(f"- Rankings: {len(rankings_df):,} rows" if not rankings_df.empty else "- Rankings: Not loaded")
st.sidebar.markdown(f"- Records: {len(records_df):,} rows" if not records_df.empty else "- Records: Not loaded")


# ============== MAIN CONTENT ==============

if selected_event and selected_classification:
    gender_name = "Men" if selected_gender == 'M' else "Women" if selected_gender == 'W' else "All"

    st.markdown(f"## {selected_event} {selected_classification} - {gender_name}")

    # Create tabs for different report pages
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Championship Standards",
        "👥 Competition Field",
        "📈 Historical Analysis",
        "🎯 Performance Analysis",
        "🇸🇦 Saudi Context"
    ])

    # ============== TAB 1: Championship Standards ==============
    with tab1:
        st.markdown("### Championship Medal Standards")

        if not standards_df.empty:
            # Filter standards for selected event
            filter_mask = (standards_df['event'] == selected_event) & (standards_df['classification'] == selected_classification)
            if selected_gender:
                filter_mask &= (standards_df['gender'] == selected_gender)

            event_standards = standards_df[filter_mask]

            if len(event_standards) > 0:
                row = event_standards.iloc[0]
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### World Championships")
                    # Use actual column names from championship_standards_report.csv
                    wc_gold = row.get('wc_gold', None)
                    wc_bronze = row.get('wc_bronze', None)
                    wc_8th = row.get('wc_8th_place', None)
                    wc_semi = row.get('wc_semi_qualifying', None)

                    if pd.notna(wc_gold) or pd.notna(wc_bronze) or pd.notna(wc_8th):
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("Gold", f"{wc_gold:.2f}" if pd.notna(wc_gold) else "N/A")
                        with m2:
                            st.metric("Bronze", f"{wc_bronze:.2f}" if pd.notna(wc_bronze) else "N/A")
                        with m3:
                            st.metric("8th Place", f"{wc_8th:.2f}" if pd.notna(wc_8th) else "N/A")
                        with m4:
                            st.metric("Semi Qual", f"{wc_semi:.2f}" if pd.notna(wc_semi) else "N/A")
                    else:
                        st.info("No World Championships data available")

                with col2:
                    st.markdown("#### Paralympics")
                    # Use actual column names from championship_standards_report.csv
                    para_gold = row.get('paralympics_gold', None)
                    para_bronze = row.get('paralympics_bronze', None)
                    para_8th = row.get('paralympics_8th_place', None)
                    para_semi = row.get('paralympics_semi_qualifying', None)

                    if pd.notna(para_gold) or pd.notna(para_bronze) or pd.notna(para_8th):
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("Gold", f"{para_gold:.2f}" if pd.notna(para_gold) else "N/A")
                        with m2:
                            st.metric("Bronze", f"{para_bronze:.2f}" if pd.notna(para_bronze) else "N/A")
                        with m3:
                            st.metric("8th Place", f"{para_8th:.2f}" if pd.notna(para_8th) else "N/A")
                        with m4:
                            st.metric("Semi Qual", f"{para_semi:.2f}" if pd.notna(para_semi) else "N/A")
                    else:
                        st.info("No Paralympics data available")

                # Comparison chart
                st.markdown("---")
                st.markdown("#### Medal Standards Comparison")

                chart_data = []
                # World Championships data
                for medal, col in [('Gold', 'wc_gold'), ('Bronze', 'wc_bronze'), ('8th', 'wc_8th_place')]:
                    val = row.get(col)
                    if pd.notna(val):
                        chart_data.append({
                            'Competition': 'World Championships',
                            'Standard': medal,
                            'Performance': val
                        })
                # Paralympics data
                for medal, col in [('Gold', 'paralympics_gold'), ('Bronze', 'paralympics_bronze'), ('8th', 'paralympics_8th_place')]:
                    val = row.get(col)
                    if pd.notna(val):
                        chart_data.append({
                            'Competition': 'Paralympics',
                            'Standard': medal,
                            'Performance': val
                        })

                if chart_data:
                    chart_df = pd.DataFrame(chart_data)
                    fig = px.bar(
                        chart_df,
                        x='Competition',
                        y='Performance',
                        color='Standard',
                        barmode='group',
                        color_discrete_map={
                            'Gold': '#FFD700',
                            'Bronze': '#CD7F32',
                            '8th': GRAY_BLUE
                        }
                    )
                    fig.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family='Inter, sans-serif', color='#333'),
                        yaxis_title=f"Performance ({get_event_unit(selected_event)})"
                    )
                    st.plotly_chart(fig, width='stretch')
            else:
                st.warning("No championship standards data for selected event/classification")
        else:
            st.info("Championship standards data not available. Run championship_winning_standards.py to generate.")

    # ============== TAB 2: Competition Field ==============
    with tab2:
        st.markdown("### Top Competitors Analysis")

        if not main_df.empty:
            # Get event data
            event_col = 'eventname' if 'eventname' in main_df.columns else 'event_name'
            perf_col = 'performancestring' if 'performancestring' in main_df.columns else 'performance'
            nat_col = 'nationality' if 'nationality' in main_df.columns else 'Nat'

            # Filter for event
            event_mask = main_df[event_col].str.contains(selected_event, case=False, na=False) & \
                        main_df[event_col].str.contains(selected_classification, case=False, na=False)

            event_data = main_df[event_mask].copy()

            if len(event_data) > 0:
                # Parse performances
                event_data['perf_value'] = event_data[perf_col].apply(parse_performance)
                event_data = event_data.dropna(subset=['perf_value'])

                # Get athlete column
                if 'firstname' in event_data.columns and 'lastname' in event_data.columns:
                    event_data['athlete_name'] = event_data['firstname'].fillna('') + ' ' + event_data['lastname'].fillna('')
                elif 'athlete_name' in event_data.columns:
                    pass
                else:
                    event_data['athlete_name'] = 'Unknown'

                is_track = is_track_event(selected_event)

                # Get top performers
                top_athletes = event_data.groupby('athlete_name').agg({
                    'perf_value': 'min' if is_track else 'max',
                    perf_col: 'first',
                    nat_col: 'first'
                }).reset_index()
                top_athletes.columns = ['Athlete', 'Performance Value', 'Best Performance', 'Nationality']
                top_athletes = top_athletes.sort_values('Performance Value', ascending=is_track).head(20)

                # Display top athletes
                st.markdown(f"#### Top 20 Athletes - {selected_event} {selected_classification}")

                # Create ranking chart
                fig = px.bar(
                    top_athletes.head(10),
                    x='Performance Value',
                    y='Athlete',
                    orientation='h',
                    color='Nationality',
                    text='Best Performance'
                )
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family='Inter, sans-serif', color='#333'),
                    yaxis={'categoryorder': 'total ascending' if is_track else 'total descending'},
                    xaxis_title=f"Performance ({get_event_unit(selected_event)})",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

                # Display table
                st.dataframe(
                    top_athletes[['Athlete', 'Best Performance', 'Nationality']],
                    use_container_width=True,
                    hide_index=True
                )

                # Nationality distribution
                st.markdown("#### Nationality Distribution (Top 20)")
                nat_counts = top_athletes['Nationality'].value_counts()
                fig2 = px.pie(
                    values=nat_counts.values,
                    names=nat_counts.index,
                    color_discrete_sequence=[TEAL_PRIMARY, GOLD_ACCENT, TEAL_LIGHT, GRAY_BLUE, '#E0E0E0']
                )
                fig2.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family='Inter, sans-serif', color='#333')
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No results found for selected event/classification")
        else:
            st.info("Main data not available")

    # ============== TAB 3: Historical Analysis ==============
    with tab3:
        st.markdown("### Historical Championship Performance")

        if not top8_df.empty:
            # Filter top8 data
            filter_mask = (top8_df['event'] == selected_event) & (top8_df['classification'] == selected_classification)
            if selected_gender:
                filter_mask &= (top8_df['gender'] == selected_gender)

            event_top8 = top8_df[filter_mask]

            if len(event_top8) > 0:
                st.markdown("#### Position-by-Position Analysis")

                # Create position analysis chart
                fig = px.line(
                    event_top8,
                    x='position',
                    y='mean_performance',
                    color='competition',
                    markers=True,
                    labels={'position': 'Position', 'mean_performance': 'Mean Performance', 'competition': 'Competition'}
                )
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family='Inter, sans-serif', color='#333'),
                    xaxis=dict(dtick=1)
                )
                st.plotly_chart(fig, use_container_width=True)

                # Display detailed table
                st.markdown("#### Detailed Position Breakdown")
                display_cols = ['competition', 'position', 'mean_performance', 'best_performance', 'worst_performance', 'sample_size']
                available_cols = [c for c in display_cols if c in event_top8.columns]
                st.dataframe(event_top8[available_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No top 8 analysis data for selected event")
        else:
            st.info("Top 8 analysis data not available. Run championship_winning_standards.py to generate.")

    # ============== TAB 4: Performance Analysis ==============
    with tab4:
        st.markdown("### Performance Trends & Analysis")

        if not main_df.empty:
            event_col = 'eventname' if 'eventname' in main_df.columns else 'event_name'
            perf_col = 'performancestring' if 'performancestring' in main_df.columns else 'performance'
            date_col = 'competitiondate' if 'competitiondate' in main_df.columns else 'date'

            event_mask = main_df[event_col].str.contains(selected_event, case=False, na=False) & \
                        main_df[event_col].str.contains(selected_classification, case=False, na=False)

            event_data = main_df[event_mask].copy()

            if len(event_data) > 0:
                event_data['perf_value'] = event_data[perf_col].apply(parse_performance)
                event_data = event_data.dropna(subset=['perf_value'])

                # Try to parse dates
                if date_col in event_data.columns:
                    event_data['date_parsed'] = pd.to_datetime(event_data[date_col], format='%d/%m/%Y', errors='coerce')
                    event_data['year'] = event_data['date_parsed'].dt.year

                is_track = is_track_event(selected_event)

                # Performance distribution
                st.markdown("#### Performance Distribution")
                fig = px.histogram(
                    event_data,
                    x='perf_value',
                    nbins=30,
                    labels={'perf_value': f'Performance ({get_event_unit(selected_event)})'}
                )
                fig.update_traces(marker_color=TEAL_PRIMARY)
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family='Inter, sans-serif', color='#333')
                )
                st.plotly_chart(fig, use_container_width=True)

                # Year-over-year trends
                if 'year' in event_data.columns:
                    st.markdown("#### Year-over-Year Performance Trends")
                    yearly_stats = event_data.groupby('year').agg({
                        'perf_value': ['min' if is_track else 'max', 'mean', 'count']
                    }).reset_index()
                    yearly_stats.columns = ['Year', 'Best', 'Average', 'Count']
                    yearly_stats = yearly_stats[yearly_stats['Year'] >= 2015]

                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        x=yearly_stats['Year'],
                        y=yearly_stats['Best'],
                        mode='lines+markers',
                        name='Best Performance',
                        line=dict(color=GOLD_ACCENT)
                    ))
                    fig2.add_trace(go.Scatter(
                        x=yearly_stats['Year'],
                        y=yearly_stats['Average'],
                        mode='lines+markers',
                        name='Average Performance',
                        line=dict(color=TEAL_PRIMARY)
                    ))
                    fig2.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family='Inter, sans-serif', color='#333'),
                        xaxis_title='Year',
                        yaxis_title=f'Performance ({get_event_unit(selected_event)})'
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # Statistics
                st.markdown("#### Statistical Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Results", f"{len(event_data):,}")
                with col2:
                    best = event_data['perf_value'].min() if is_track else event_data['perf_value'].max()
                    st.metric("Best Ever", f"{best:.2f}")
                with col3:
                    st.metric("Mean", f"{event_data['perf_value'].mean():.2f}")
                with col4:
                    st.metric("Std Dev", f"{event_data['perf_value'].std():.2f}")
            else:
                st.info("No data found for selected event")
        else:
            st.info("Main data not available")

    # ============== TAB 5: Saudi Context ==============
    with tab5:
        st.markdown("### Saudi Arabia Context")

        if not main_df.empty:
            event_col = 'eventname' if 'eventname' in main_df.columns else 'event_name'
            perf_col = 'performancestring' if 'performancestring' in main_df.columns else 'performance'
            nat_col = 'nationality' if 'nationality' in main_df.columns else 'Nat'

            # Get Saudi data for this event
            event_mask = main_df[event_col].str.contains(selected_event, case=False, na=False) & \
                        main_df[event_col].str.contains(selected_classification, case=False, na=False)
            saudi_mask = main_df[nat_col] == 'KSA'

            saudi_event_data = main_df[event_mask & saudi_mask].copy()

            if len(saudi_event_data) > 0:
                saudi_event_data['perf_value'] = saudi_event_data[perf_col].apply(parse_performance)
                saudi_event_data = saudi_event_data.dropna(subset=['perf_value'])

                if 'firstname' in saudi_event_data.columns and 'lastname' in saudi_event_data.columns:
                    saudi_event_data['athlete_name'] = saudi_event_data['firstname'].fillna('') + ' ' + saudi_event_data['lastname'].fillna('')
                elif 'athlete_name' not in saudi_event_data.columns:
                    saudi_event_data['athlete_name'] = 'Unknown'

                is_track = is_track_event(selected_event)

                st.markdown(f"#### Saudi Athletes in {selected_event} {selected_classification}")

                # Saudi athlete summary
                saudi_summary = saudi_event_data.groupby('athlete_name').agg({
                    'perf_value': ['min' if is_track else 'max', 'count'],
                    perf_col: 'first'
                }).reset_index()
                saudi_summary.columns = ['Athlete', 'Best Value', 'Competitions', 'Best Performance']
                saudi_summary = saudi_summary.sort_values('Best Value', ascending=is_track)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Saudi Athletes", len(saudi_summary))
                with col2:
                    st.metric("Total Results", len(saudi_event_data))
                with col3:
                    best_saudi = saudi_summary.iloc[0]['Best Performance'] if len(saudi_summary) > 0 else "N/A"
                    st.metric("Best Saudi Performance", best_saudi)

                st.dataframe(
                    saudi_summary[['Athlete', 'Best Performance', 'Competitions']],
                    use_container_width=True,
                    hide_index=True
                )

                # Gap to medals
                st.markdown("---")
                st.markdown("#### Gap to Championship Standards")

                if not standards_df.empty:
                    filter_mask = (standards_df['event'] == selected_event) & (standards_df['classification'] == selected_classification)
                    event_standards = standards_df[filter_mask]

                    if len(event_standards) > 0 and len(saudi_summary) > 0:
                        best_saudi_val = saudi_summary.iloc[0]['Best Value']

                        for _, std_row in event_standards.iterrows():
                            comp_type = std_row.get('competition_type', 'Unknown')
                            st.markdown(f"**{comp_type}:**")

                            gold = std_row.get('gold_mean')
                            bronze = std_row.get('bronze_mean')
                            eighth = std_row.get('eighth_mean')

                            col1, col2, col3 = st.columns(3)
                            if pd.notna(gold):
                                gap = best_saudi_val - gold if is_track else gold - best_saudi_val
                                status = "behind" if gap > 0 else "ahead"
                                with col1:
                                    st.metric(f"Gap to Gold", f"{abs(gap):.2f} {status}")
                            if pd.notna(bronze):
                                gap = best_saudi_val - bronze if is_track else bronze - best_saudi_val
                                status = "behind" if gap > 0 else "ahead"
                                with col2:
                                    st.metric(f"Gap to Bronze", f"{abs(gap):.2f} {status}")
                            if pd.notna(eighth):
                                gap = best_saudi_val - eighth if is_track else eighth - best_saudi_val
                                status = "behind" if gap > 0 else "ahead"
                                with col3:
                                    st.metric(f"Gap to Finals", f"{abs(gap):.2f} {status}")
            else:
                st.info(f"No Saudi athletes found in {selected_event} {selected_classification}")
        else:
            st.info("Main data not available")

else:
    # No event selected - show overview
    st.markdown("### Select an Event and Classification to View Pre-Competition Analysis")

    if not standards_df.empty:
        st.markdown("#### Available Events in Championship Standards")

        # Show summary of available data
        if 'event' in standards_df.columns and 'classification' in standards_df.columns:
            summary = standards_df.groupby(['event', 'classification']).size().reset_index(name='Records')
            summary = summary.sort_values('Records', ascending=False)
            st.dataframe(summary.head(30), use_container_width=True, hide_index=True)

    # Show existing PDF reports
    st.markdown("---")
    st.markdown("#### Existing Pre-Competition Reports")

    reports_dir = Path("pre_competition_reports")
    if reports_dir.exists():
        report_folders = [f.name for f in reports_dir.iterdir() if f.is_dir()]
        if report_folders:
            st.markdown(f"Found **{len(report_folders)}** pre-generated reports:")

            # Parse report names
            report_data = []
            for folder in report_folders:
                parts = folder.replace("_PreComp", "").split("_")
                if len(parts) >= 3:
                    report_data.append({
                        'Event': parts[0],
                        'Classification': parts[1],
                        'Gender': parts[2],
                        'Folder': folder
                    })

            if report_data:
                report_df = pd.DataFrame(report_data)
                st.dataframe(report_df[['Event', 'Classification', 'Gender']], use_container_width=True, hide_index=True)
        else:
            st.info("No pre-generated reports found")
    else:
        st.info("Pre-competition reports folder not found")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {GRAY_BLUE};">
    <p>Pre-Competition Analysis Dashboard | Team Saudi Para Athletics</p>
</div>
""", unsafe_allow_html=True)
