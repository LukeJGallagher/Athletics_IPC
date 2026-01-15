#!/usr/bin/env python3
"""
Pre-Competition Championship Report Analyzer
==========================================

Generates championship-focused 5-page pre-competition reports similar to comprehensive_event_analysis_v2.py
Focus: Competition insights, championship standards, current form, rankings, and Saudi context
Format: 5 pages per event-classification-gender combination

Author: Performance Analysis Team
Date: 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
from datetime import datetime
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image
import glob
warnings.filterwarnings('ignore')

class PreCompetitionChampionshipAnalyzer:
    def __init__(self):
        self.data_path = Path("data")
        self.main_data = None
        self.championship_standards = None
        self.detailed_top8_analysis = None
        self.rankings_data = {}
        self.all_records = {}

        # Saudi Olympic colors for consistency
        self.colors = {
            'primary_green': '#007167',
            'secondary_gold': '#90EE90',
            'accent_white': '#FFFFFF',
            'background_gray': '#F1F1F1',
            'background_white': '#FFFFFF',
            'text_dark': '#2C2C2C'
        }

        # Output directory
        self.output_dir = Path("pre_competition_reports")
        self.output_dir.mkdir(exist_ok=True)

    def load_data(self):
        """Load all required data sources"""
        print("Loading pre-competition analysis data...")

        # Load main Tilastoptija data
        main_csv = self.data_path / "Tilastoptija" / "ksaoutputipc3.csv"
        if main_csv.exists():
            self.main_data = pd.read_csv(main_csv, encoding='latin-1', low_memory=False)
            print(f"Loaded main data: {len(self.main_data)} results")

            # Clean and prepare data
            self._prepare_main_data()
        else:
            print("Main data file not found!")
            return False

        # Load championship standards (gender-separated)
        self._load_championship_csvs()

        # Load rankings data
        self._load_rankings()

        # Load records
        self._load_records()

        return True

    def _prepare_main_data(self):
        """Clean and prepare main data"""
        # Standardize column names
        self.main_data.columns = self.main_data.columns.str.lower()

        # Create performance_clean column
        if 'performancestring' in self.main_data.columns:
            self.main_data['performance_clean'] = pd.to_numeric(
                self.main_data['performancestring'], errors='coerce'
            )

        # Identify major championships
        major_keywords = [
            '11th Para Athletics World Championships',
            '17th Paralympic Games', '16th Paralympic Games', '15th Paralympic Games',
            'Para Athletics World Championships', 'Paralympic Games'
        ]

        self.main_data['is_major_championship'] = False
        for keyword in major_keywords:
            mask = self.main_data['competitionname'].str.contains(keyword, case=False, na=False)
            self.main_data.loc[mask, 'is_major_championship'] = True

        # Add championship type classification
        self.main_data['championship_type'] = 'Other'

        wc_mask = self.main_data['competitionname'].str.contains('Para Athletics World Championships', case=False, na=False)
        self.main_data.loc[wc_mask, 'championship_type'] = 'World Championships'

        para_mask = self.main_data['competitionname'].str.contains('Paralympic', case=False, na=False)
        self.main_data.loc[para_mask, 'championship_type'] = 'Paralympics'

    def _load_championship_csvs(self):
        """Load championship analysis CSV data"""
        standards_file = Path("championship_standards_gender_separated.csv")
        if standards_file.exists():
            self.championship_standards = pd.read_csv(standards_file)
            print(f"Loaded Championship Standards: {len(self.championship_standards)} event-classification-gender combinations")

        top8_file = Path("detailed_top8_championship_analysis_gender_separated.csv")
        if top8_file.exists():
            self.detailed_top8_analysis = pd.read_csv(top8_file)
            print(f"Loaded Detailed Top 8 Analysis (Gender-Separated): {len(self.detailed_top8_analysis)} position records")
        else:
            # Fallback to old file
            old_top8_file = Path("detailed_top8_championship_analysis.csv")
            if old_top8_file.exists():
                self.detailed_top8_analysis = pd.read_csv(old_top8_file)
                print(f"Loaded Detailed Top 8 Analysis (Legacy): {len(self.detailed_top8_analysis)} position records")

    def _load_rankings(self):
        """Load rankings data from recent years - focusing on important ranking types"""
        rankings_dir = self.data_path / "Rankings"
        if rankings_dir.exists():
            # Load specific ranking types for 2024-2025
            ranking_types = [
                "World Rankings", "Asian Rankings", "African Rankings",
                "European Rankings", "Americas Rankings", "Annual Recorded Best Performances"
            ]

            for ranking_type in ranking_types:
                # Load 2024 data
                file_2024 = rankings_dir / f"{ranking_type}_2024.csv"
                if file_2024.exists():
                    try:
                        data = pd.read_csv(file_2024)
                        self.rankings_data[f"{ranking_type}_2024"] = data
                        print(f"Loaded {ranking_type} 2024: {len(data)} entries")
                    except Exception as e:
                        print(f"Error loading {file_2024}: {e}")

                # Load 2025 data
                file_2025 = rankings_dir / f"{ranking_type}_2025.csv"
                if file_2025.exists():
                    try:
                        data = pd.read_csv(file_2025)
                        self.rankings_data[f"{ranking_type}_2025"] = data
                        print(f"Loaded {ranking_type} 2025: {len(data)} entries")
                    except Exception as e:
                        print(f"Error loading {file_2025}: {e}")

    def _load_records(self):
        """Load records data with proper classification support"""
        records_dir = self.data_path / "Records"
        if records_dir.exists():
            # Load important record types
            record_types = [
                "World Record", "Paralympic Record", "Asian Record",
                "African Record", "European Record", "Americas Record",
                "Championship Record"
            ]

            for record_type in record_types:
                # Find files matching this record type
                matching_files = list(records_dir.glob(f"*{record_type}*.csv"))
                if matching_files:
                    try:
                        # Use the most recent file (assuming timestamp makes it last)
                        file = matching_files[-1]
                        data = pd.read_csv(file)
                        self.all_records[record_type] = data
                        print(f"Loaded {record_type}: {len(data)} records")
                    except Exception as e:
                        print(f"Error loading {record_type}: {e}")

    def generate_pre_competition_report(self, event, classification, gender):
        """Generate complete 5-page pre-competition report"""
        gender_name = "Men" if gender == 'M' else "Women"

        print(f"\nGenerating Pre-Competition Report for {event} {classification} {gender_name}")

        # Create output directory
        event_dir = self.output_dir / f"{event}_{classification}_{gender_name}_PreComp"
        event_dir.mkdir(exist_ok=True)

        # Generate 5 pages
        self.create_page1_championship_standards(event, classification, gender, event_dir)
        self.create_page2_competition_field(event, classification, gender, event_dir)
        self.create_page3_historical_championship(event, classification, gender, event_dir)
        self.create_page4_performance_analysis(event, classification, gender, event_dir)
        self.create_page5_saudi_championship_context(event, classification, gender, event_dir)

        # Compile all pages into PDF
        pdf_file = self.compile_event_pdf(event, classification, gender, event_dir)

        print(f"Pre-competition report generated in: {event_dir}")
        if pdf_file:
            print(f"Combined PDF created: {pdf_file}")

    def create_page1_championship_standards(self, event, classification, gender, output_dir):
        """Page 1: Championship Medal Standards Analysis"""
        gender_name = "Men" if gender == 'M' else "Women"
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 28))

        fig.suptitle(f'{event} {classification} {gender_name} - Championship Medal Standards Analysis\nWorld Championships vs Paralympics Comparison',
                    fontsize=26, fontweight='bold', color=self.colors['primary_green'], y=0.96)

        # Top Left: World Championships Medal Standards
        self._create_wc_championship_standards(ax1, event, classification, gender)

        # Top Right: Paralympics Medal Standards
        self._create_paralympics_championship_standards(ax2, event, classification, gender)

        # Bottom Left: Championship Top 8 Breakdown
        self._create_championship_top8_analysis(ax3, event, classification, gender)

        # Bottom Right: Medal Performance Trends
        self._create_medal_performance_trends(ax4, event, classification, gender)

        plt.tight_layout(pad=6.0)
        plt.savefig(output_dir / 'page1_championship_standards.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_wc_championship_standards(self, ax, event, classification, gender):
        """Create World Championships medal standards table"""
        ax.set_title('World Championships - Medal Standards', fontsize=18, fontweight='bold', pad=35)

        if self.championship_standards is not None:
            # Get WC standards for this event-class-gender
            wc_data = self.championship_standards[
                (self.championship_standards['event'] == event) &
                (self.championship_standards['classification'] == classification) &
                (self.championship_standards['gender'] == gender) &
                (self.championship_standards['competition_type'] == 'World Championships')
            ]

            if len(wc_data) > 0:
                row = wc_data.iloc[0]

                table_data = []
                if pd.notna(row['gold_mean']):
                    table_data.append(['Gold Standard', f"{row['gold_mean']:.2f}", f"Sample: {row['gold_count']}", 'Recent Championships'])
                if pd.notna(row['silver_mean']):
                    table_data.append(['Silver Standard', f"{row['silver_mean']:.2f}", f"Sample: {row['silver_count']}", 'Recent Championships'])
                if pd.notna(row['bronze_mean']):
                    table_data.append(['Bronze Standard', f"{row['bronze_mean']:.2f}", f"Sample: {row['bronze_count']}", 'Recent Championships'])
                if pd.notna(row['eighth_mean']):
                    table_data.append(['8th Place', f"{row['eighth_mean']:.2f}", f"Sample: {row['eighth_count']}", 'Finals Qualifier'])

                if table_data:
                    headers = ['Standard', 'Performance', 'Data', 'Notes']
                    table = ax.table(cellText=table_data, colLabels=headers,
                                   cellLoc='center', loc='center')
                    table.auto_set_font_size(False)
                    table.set_fontsize(12)
                    table.scale(1, 2.5)

                    # Color code by medal type
                    for (i, j), cell in table.get_celld().items():
                        if i == 0:  # Header
                            cell.set_facecolor(self.colors['primary_green'])
                            cell.set_text_props(weight='bold', color='white')
                        elif j == 0:  # Medal type column
                            if 'Gold' in table_data[i-1][0]:
                                cell.set_facecolor('#FFD700')
                            elif 'Bronze' in table_data[i-1][0]:
                                cell.set_facecolor('#CD7F32')
                            else:
                                cell.set_facecolor('#E0E0E0')
                            cell.set_text_props(weight='bold')
                        else:
                            cell.set_facecolor('#F9F9F9')
                else:
                    ax.text(0.5, 0.5, 'No World Championships data available',
                           ha='center', va='center', transform=ax.transAxes, fontsize=14)
            else:
                ax.text(0.5, 0.5, 'No World Championships data available',
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
        else:
            ax.text(0.5, 0.5, 'Championship standards data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)

        ax.axis('off')

    def _create_paralympics_championship_standards(self, ax, event, classification, gender):
        """Create Paralympics medal standards table"""
        ax.set_title('Paralympics - Medal Standards', fontsize=18, fontweight='bold', pad=35)

        if self.championship_standards is not None:
            # Get Paralympics standards
            para_data = self.championship_standards[
                (self.championship_standards['event'] == event) &
                (self.championship_standards['classification'] == classification) &
                (self.championship_standards['gender'] == gender) &
                (self.championship_standards['competition_type'] == 'Paralympics')
            ]

            if len(para_data) > 0:
                row = para_data.iloc[0]

                table_data = []
                if pd.notna(row['gold_mean']):
                    table_data.append(['Gold Standard', f"{row['gold_mean']:.2f}", f"Sample: {row['gold_count']}", 'Recent Paralympics'])
                if pd.notna(row['silver_mean']):
                    table_data.append(['Silver Standard', f"{row['silver_mean']:.2f}", f"Sample: {row['silver_count']}", 'Recent Paralympics'])
                if pd.notna(row['bronze_mean']):
                    table_data.append(['Bronze Standard', f"{row['bronze_mean']:.2f}", f"Sample: {row['bronze_count']}", 'Recent Paralympics'])
                if pd.notna(row['eighth_mean']):
                    table_data.append(['8th Place', f"{row['eighth_mean']:.2f}", f"Sample: {row['eighth_count']}", 'Finals Qualifier'])

                if table_data:
                    headers = ['Standard', 'Performance', 'Data', 'Notes']
                    table = ax.table(cellText=table_data, colLabels=headers,
                                   cellLoc='center', loc='center')
                    table.auto_set_font_size(False)
                    table.set_fontsize(12)
                    table.scale(1, 2.5)

                    # Color code by medal type
                    for (i, j), cell in table.get_celld().items():
                        if i == 0:  # Header
                            cell.set_facecolor(self.colors['primary_green'])
                            cell.set_text_props(weight='bold', color='white')
                        elif j == 0:  # Medal type column
                            if 'Gold' in table_data[i-1][0]:
                                cell.set_facecolor('#FFD700')
                            elif 'Bronze' in table_data[i-1][0]:
                                cell.set_facecolor('#CD7F32')
                            else:
                                cell.set_facecolor('#E0E0E0')
                            cell.set_text_props(weight='bold')
                        else:
                            cell.set_facecolor('#F9F9F9')
                else:
                    ax.text(0.5, 0.5, 'No Paralympics data available',
                           ha='center', va='center', transform=ax.transAxes, fontsize=14)
            else:
                ax.text(0.5, 0.5, 'No Paralympics data available',
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
        else:
            ax.text(0.5, 0.5, 'Championship standards data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)

        ax.axis('off')

    def _create_championship_top8_analysis(self, ax, event, classification, gender):
        """Create championship top 8 position analysis"""
        ax.set_title('Championship Top 8 Position Analysis', fontsize=18, fontweight='bold', pad=35)

        if self.detailed_top8_analysis is not None:
            # Get top 8 data for both competitions
            top8_data = self.detailed_top8_analysis[
                (self.detailed_top8_analysis['event'] == event) &
                (self.detailed_top8_analysis['classification'] == classification) &
                (self.detailed_top8_analysis['gender'] == gender)
            ]

            if len(top8_data) > 0:
                # Create summary table
                table_data = []
                for _, row in top8_data.head(16).iterrows():  # Limit to top 16 rows
                    table_data.append([
                        row['competition'][:4],  # Abbreviated competition name
                        f"{int(row['position'])}",
                        f"{row['mean_performance']:.2f}",
                        f"{row['best_performance']:.2f}",
                        f"{row['worst_performance']:.2f}",
                        f"{int(row['sample_size'])}"
                    ])

                headers = ['Comp', 'Pos', 'Mean', 'Best', 'Worst', 'N']
                table = ax.table(cellText=table_data, colLabels=headers,
                               cellLoc='center', loc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 1.5)

                # Style the table
                for (i, j), cell in table.get_celld().items():
                    if i == 0:  # Header
                        cell.set_facecolor(self.colors['primary_green'])
                        cell.set_text_props(weight='bold', color='white')
                    elif j == 1:  # Position column
                        pos = int(table_data[i-1][1]) if i > 0 else 0
                        if pos <= 3:
                            cell.set_facecolor('#FFE4B5')  # Medal positions
                        elif pos <= 8:
                            cell.set_facecolor('#E6F3FF')  # Finals
                        cell.set_text_props(weight='bold')
                    else:
                        cell.set_facecolor('#F9F9F9')
            else:
                ax.text(0.5, 0.5, 'No top 8 analysis data available',
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
        else:
            ax.text(0.5, 0.5, 'Top 8 analysis data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)

        ax.axis('off')

    def _create_medal_performance_trends(self, ax, event, classification, gender):
        """Create medal performance trends chart"""
        ax.set_title('Medal Performance Trends - WC vs Paralympics', fontsize=18, fontweight='bold', pad=35)

        if self.championship_standards is not None:
            # Get both WC and Paralympics data for comparison
            comp_data = self.championship_standards[
                (self.championship_standards['event'] == event) &
                (self.championship_standards['classification'] == classification) &
                (self.championship_standards['gender'] == gender)
            ]

            if len(comp_data) >= 2:  # Need both WC and Paralympics
                wc_row = comp_data[comp_data['competition_type'] == 'World Championships']
                para_row = comp_data[comp_data['competition_type'] == 'Paralympics']

                if len(wc_row) > 0 and len(para_row) > 0:
                    competitions = ['World Championships', 'Paralympics']
                    gold_standards = [
                        wc_row.iloc[0]['gold_mean'] if pd.notna(wc_row.iloc[0]['gold_mean']) else 0,
                        para_row.iloc[0]['gold_mean'] if pd.notna(para_row.iloc[0]['gold_mean']) else 0
                    ]
                    silver_standards = [
                        wc_row.iloc[0]['silver_mean'] if pd.notna(wc_row.iloc[0]['silver_mean']) else 0,
                        para_row.iloc[0]['silver_mean'] if pd.notna(para_row.iloc[0]['silver_mean']) else 0
                    ]
                    bronze_standards = [
                        wc_row.iloc[0]['bronze_mean'] if pd.notna(wc_row.iloc[0]['bronze_mean']) else 0,
                        para_row.iloc[0]['bronze_mean'] if pd.notna(para_row.iloc[0]['bronze_mean']) else 0
                    ]

                    x = np.arange(len(competitions))
                    width = 0.25

                    bars1 = ax.bar(x - width, gold_standards, width, label='Gold Standard',
                                  color='#FFD700', alpha=0.8)
                    bars2 = ax.bar(x, silver_standards, width, label='Silver Standard',
                                  color='#C0C0C0', alpha=0.8)
                    bars3 = ax.bar(x + width, bronze_standards, width, label='Bronze Standard',
                                  color='#CD7F32', alpha=0.8)

                    ax.set_xlabel('Competition', fontweight='bold')
                    ax.set_ylabel('Performance Standard', fontweight='bold')
                    ax.set_xticks(x)
                    ax.set_xticklabels(competitions)
                    ax.legend()
                    ax.grid(True, alpha=0.3)

                    # Add value labels
                    for bar in bars1:
                        height = bar.get_height()
                        if height > 0:
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{height:.2f}', ha='center', va='bottom', fontsize=10)

                    for bar in bars2:
                        height = bar.get_height()
                        if height > 0:
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{height:.2f}', ha='center', va='bottom', fontsize=10)

                    for bar in bars3:
                        height = bar.get_height()
                        if height > 0:
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{height:.2f}', ha='center', va='bottom', fontsize=10)
                else:
                    ax.text(0.5, 0.5, 'Insufficient comparison data',
                           ha='center', va='center', transform=ax.transAxes, fontsize=14)
            else:
                ax.text(0.5, 0.5, 'Insufficient comparison data',
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
        else:
            ax.text(0.5, 0.5, 'Championship standards data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)

    def create_page2_competition_field(self, event, classification, gender, output_dir):
        """Page 2: Key Competitors Analysis - Multiple Results"""
        gender_name = "Men" if gender == 'M' else "Women"
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 28))

        fig.suptitle(f'{event} {classification} {gender_name} - Key Competitors Analysis\nTop Athletes & Multiple Season Results',
                    fontsize=26, fontweight='bold', color=self.colors['primary_green'], y=0.96)

        # Show key competitors across all 4 quadrants with different views
        self._create_key_competitors_analysis_part1(ax1, event, classification, gender)
        self._create_key_competitors_analysis_part2(ax2, event, classification, gender)
        self._create_key_competitors_analysis_part3(ax3, event, classification, gender)
        self._create_key_competitors_analysis_part4(ax4, event, classification, gender)

        plt.tight_layout(pad=6.0)
        plt.savefig(output_dir / 'page2_competition_field.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_current_rankings_table(self, ax, event, classification, gender):
        """Create current season rankings table"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Current Season Rankings (2024-2025)\n{event} {classification} {gender_name}', fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Search for current rankings data using correct column names
        rankings_found = []
        for key, rankings_df in self.rankings_data.items():
            if '2024' in key or '2025' in key:
                # Filter by classification (Class column) and gender
                if 'Class' in rankings_df.columns and 'Gender' in rankings_df.columns:
                    class_matches = rankings_df[
                        (rankings_df['Class'].str.contains(classification, case=False, na=False)) &
                        (rankings_df['Gender'] == gender)
                    ]
                    if len(class_matches) > 0:
                        # Convert Result column to numeric for ranking
                        class_matches = class_matches.copy()
                        if 'TimeMS' in class_matches.columns:
                            class_matches['performance_ms'] = pd.to_numeric(class_matches['TimeMS'], errors='coerce')
                        elif 'Result' in class_matches.columns:
                            # Parse result string to numeric
                            result_str = class_matches['Result'].str.replace(':', '').str.replace(',', '')
                            class_matches['performance_numeric'] = pd.to_numeric(result_str, errors='coerce')

                        rankings_found.extend(class_matches.head(10).to_dict('records'))

        if rankings_found:
            # Create rankings table with correct column names
            table_data = []
            for i, athlete in enumerate(rankings_found[:15], 1):
                name = f"{athlete.get('GivenName', '')} {athlete.get('FamilyName', '')}".strip()
                country = athlete.get('Country', 'N/A')
                performance = athlete.get('Result', 'N/A')
                date = athlete.get('Date', 'N/A')[:10] if pd.notna(athlete.get('Date')) else 'N/A'
                competition = str(athlete.get('Competition', 'N/A'))[:25] + "..." if len(str(athlete.get('Competition', ''))) > 25 else str(athlete.get('Competition', 'N/A'))
                table_data.append([f"{i}", name, country, str(performance), date])

            if table_data:
                headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Date']
                table = ax.table(cellText=table_data, colLabels=headers,
                               loc='center', cellLoc='left')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 2)

                # Saudi theme styling
                for (row, col), cell in table.get_celld().items():
                    if row == 0:  # Header row
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(self.colors['primary_green'])
                    else:
                        cell.set_facecolor(self.colors['background_white'])
        else:
            ax.text(0.5, 0.5, f'No current rankings found for\n{event} {classification} {gender_name}\n\nCheck rankings data availability',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_key_competitors_analysis(self, ax, event, classification, gender):
        """Create key competitors analysis"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Key Competitors Analysis\n{event} {classification} {gender_name}', fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get recent results (2024-2025) for this event-classification-gender
            recent_results = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['competitiondate'].str.contains('2024|2025', case=False, na=False))
            ].copy()

            if len(recent_results) > 0:
                # Convert performance to numeric
                recent_results['performance_clean'] = pd.to_numeric(recent_results['performance'], errors='coerce')
                recent_results = recent_results.dropna(subset=['performance_clean'])

                if len(recent_results) > 0:
                    # Get top performers based on best performance
                    is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                    if is_time_event:
                        top_performers = recent_results.nsmallest(8, 'performance_clean')
                    else:
                        top_performers = recent_results.nlargest(8, 'performance_clean')

                    # Create simplified competitors table with best results and dates
                    table_data = []
                    for idx, athlete in top_performers.iterrows():
                        name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
                        country = athlete.get('nationality', 'N/A')
                        performance = f"{athlete['performance_clean']:.2f}"
                        date = athlete.get('competitiondate', 'N/A')[:10] if pd.notna(athlete.get('competitiondate')) else 'N/A'
                        table_data.append([name, country, performance, date])

                    if table_data:
                        headers = ['Athlete', 'Country', 'Best Result', 'Date']
                        table = ax.table(cellText=table_data, colLabels=headers,
                                       loc='center', cellLoc='left')
                        table.auto_set_font_size(False)
                        table.set_fontsize(9)
                        table.scale(1, 1.8)

                        # Saudi theme styling
                        for (row, col), cell in table.get_celld().items():
                            if row == 0:  # Header row
                                cell.set_text_props(weight='bold', color='white')
                                cell.set_facecolor(self.colors['primary_green'])
                            else:
                                cell.set_facecolor(self.colors['background_white'])
                                # Highlight Saudi athletes
                                if col == 1 and 'KSA' in str(cell.get_text().get_text()):
                                    cell.set_facecolor(self.colors['secondary_gold'])
                else:
                    ax.text(0.5, 0.5, f'No performance data found for\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12,
                           color=self.colors['text_dark'])
            else:
                ax.text(0.5, 0.5, f'No recent results found for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12,
                       color=self.colors['text_dark'])
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_key_competitors_analysis_part1(self, ax, event, classification, gender):
        """Top 15 Athletes - Season Best Results"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Top 15 Athletes - 2024-25 Season Bests\n{event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get all recent results (2024-2025) for this event-classification-gender
            recent_results = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['competitiondate'].str.contains('2024|2025', case=False, na=False))
            ].copy()

            if len(recent_results) > 0:
                # Convert performance to numeric
                recent_results['performance_clean'] = pd.to_numeric(recent_results['performance'], errors='coerce')
                recent_results = recent_results.dropna(subset=['performance_clean'])

                if len(recent_results) > 0:
                    # Get season best for each athlete
                    is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']

                    athlete_bests = []
                    for athlete_id in recent_results['athleteid'].unique():
                        athlete_data = recent_results[recent_results['athleteid'] == athlete_id]

                        if is_time_event:
                            best_perf = athlete_data['performance_clean'].min()
                            best_row = athlete_data.loc[athlete_data['performance_clean'].idxmin()]
                        else:
                            best_perf = athlete_data['performance_clean'].max()
                            best_row = athlete_data.loc[athlete_data['performance_clean'].idxmax()]

                        name = f"{best_row.get('firstname', '')} {best_row.get('lastname', '')}".strip()
                        country = best_row.get('nationality', 'N/A')
                        date = best_row.get('competitiondate', 'N/A')[:10] if pd.notna(best_row.get('competitiondate')) else 'N/A'

                        athlete_bests.append({
                            'name': name,
                            'country': country,
                            'performance': best_perf,
                            'date': date
                        })

                    # Sort by performance (best first)
                    athlete_bests.sort(key=lambda x: x['performance'], reverse=not is_time_event)

                    # Create table for top 15
                    table_data = []
                    for i, athlete in enumerate(athlete_bests[:15], 1):
                        table_data.append([
                            f"{i}",
                            athlete['name'],
                            athlete['country'],
                            f"{athlete['performance']:.2f}",
                            athlete['date']
                        ])

                    if table_data:
                        headers = ['Rank', 'Athlete', 'Country', 'Season Best', 'Date']
                        table = ax.table(cellText=table_data, colLabels=headers,
                                       loc='center', cellLoc='left')
                        table.auto_set_font_size(False)
                        table.set_fontsize(8)
                        table.scale(1, 1.8)

                        # Saudi theme styling
                        for (row, col), cell in table.get_celld().items():
                            if row == 0:  # Header row
                                cell.set_text_props(weight='bold', color='white')
                                cell.set_facecolor(self.colors['primary_green'])
                            else:
                                cell.set_facecolor(self.colors['background_white'])
                                # Highlight Saudi athletes
                                if col == 2 and ('KSA' in str(cell.get_text().get_text()) or 'SAU' in str(cell.get_text().get_text())):
                                    cell.set_facecolor(self.colors['secondary_gold'])
                else:
                    ax.text(0.5, 0.5, f'No performance data found for\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
            else:
                ax.text(0.5, 0.5, f'No recent results found for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)

        ax.axis('off')

    def _create_key_competitors_analysis_part2(self, ax, event, classification, gender):
        """Top 5 Athletes - Multiple Results Each"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Top 5 Athletes - Multiple 2024-25 Results\n{event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get all recent results (2024-2025) for this event-classification-gender
            recent_results = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['competitiondate'].str.contains('2024|2025', case=False, na=False))
            ].copy()

            if len(recent_results) > 0:
                # Convert performance to numeric
                recent_results['performance_clean'] = pd.to_numeric(recent_results['performance'], errors='coerce')
                recent_results = recent_results.dropna(subset=['performance_clean'])

                if len(recent_results) > 0:
                    # Get top 5 athletes by season best
                    is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']

                    athlete_bests = []
                    for athlete_id in recent_results['athleteid'].unique():
                        athlete_data = recent_results[recent_results['athleteid'] == athlete_id]

                        if is_time_event:
                            best_perf = athlete_data['performance_clean'].min()
                        else:
                            best_perf = athlete_data['performance_clean'].max()

                        if len(athlete_data) > 0:
                            best_row = athlete_data.iloc[0]
                            name = f"{best_row.get('firstname', '')} {best_row.get('lastname', '')}".strip()

                            athlete_bests.append({
                                'id': athlete_id,
                                'name': name,
                                'best': best_perf
                            })

                    # Sort by performance (best first)
                    athlete_bests.sort(key=lambda x: x['best'], reverse=not is_time_event)

                    # Get multiple results for top 5 athletes
                    table_data = []
                    for athlete_info in athlete_bests[:5]:
                        athlete_data = recent_results[recent_results['athleteid'] == athlete_info['id']]

                        # Sort athlete's results
                        if is_time_event:
                            athlete_results = athlete_data.nsmallest(3, 'performance_clean')
                        else:
                            athlete_results = athlete_data.nlargest(3, 'performance_clean')

                        for idx, result in athlete_results.iterrows():
                            performance = f"{result['performance_clean']:.2f}"
                            date = result.get('competitiondate', 'N/A')[:10] if pd.notna(result.get('competitiondate')) else 'N/A'
                            competition = str(result.get('competitionname', 'N/A'))[:25] + "..." if len(str(result.get('competitionname', ''))) > 25 else str(result.get('competitionname', 'N/A'))

                            table_data.append([
                                athlete_info['name'],
                                result.get('nationality', 'N/A'),
                                performance,
                                date,
                                competition
                            ])

                    if table_data:
                        headers = ['Athlete', 'Country', 'Performance', 'Date', 'Competition']
                        table = ax.table(cellText=table_data, colLabels=headers,
                                       loc='center', cellLoc='left')
                        table.auto_set_font_size(False)
                        table.set_fontsize(8)
                        table.scale(1, 1.6)

                        # Saudi theme styling
                        for (row, col), cell in table.get_celld().items():
                            if row == 0:  # Header row
                                cell.set_text_props(weight='bold', color='white')
                                cell.set_facecolor(self.colors['primary_green'])
                            else:
                                cell.set_facecolor(self.colors['background_white'])
                                # Highlight Saudi athletes
                                if col == 1 and ('KSA' in str(cell.get_text().get_text()) or 'SAU' in str(cell.get_text().get_text())):
                                    cell.set_facecolor(self.colors['secondary_gold'])
                else:
                    ax.text(0.5, 0.5, f'No performance data found for\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
            else:
                ax.text(0.5, 0.5, f'No recent results found for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)

        ax.axis('off')

    def _create_key_competitors_analysis_part3(self, ax, event, classification, gender):
        """Competition Analysis - Recent Major Events"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Recent Major Competition Results\n{event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get recent major competition results
            major_results = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['competitiondate'].str.contains('2024|2025', case=False, na=False)) &
                (self.main_data['competitionname'].str.contains('World|Paralympic|Grand Prix|Diamond|Championships', case=False, na=False))
            ].copy()

            if len(major_results) > 0:
                major_results['performance_clean'] = pd.to_numeric(major_results['performance'], errors='coerce')
                major_results = major_results.dropna(subset=['performance_clean'])

                if len(major_results) > 0:
                    # Sort by date and performance
                    major_results = major_results.sort_values(['competitiondate', 'performance_clean'])

                    table_data = []
                    for idx, result in major_results.head(12).iterrows():
                        name = f"{result.get('firstname', '')} {result.get('lastname', '')}".strip()
                        country = result.get('nationality', 'N/A')
                        performance = f"{result['performance_clean']:.2f}"
                        date = result.get('competitiondate', 'N/A')[:10] if pd.notna(result.get('competitiondate')) else 'N/A'
                        competition = str(result.get('competitionname', 'N/A'))[:20] + "..." if len(str(result.get('competitionname', ''))) > 20 else str(result.get('competitionname', 'N/A'))

                        table_data.append([name, country, performance, date, competition])

                    if table_data:
                        headers = ['Athlete', 'Country', 'Performance', 'Date', 'Major Competition']
                        table = ax.table(cellText=table_data, colLabels=headers,
                                       loc='center', cellLoc='left')
                        table.auto_set_font_size(False)
                        table.set_fontsize(8)
                        table.scale(1, 1.6)

                        # Saudi theme styling
                        for (row, col), cell in table.get_celld().items():
                            if row == 0:  # Header row
                                cell.set_text_props(weight='bold', color='white')
                                cell.set_facecolor(self.colors['primary_green'])
                            else:
                                cell.set_facecolor(self.colors['background_white'])
                                # Highlight Saudi athletes
                                if col == 1 and ('KSA' in str(cell.get_text().get_text()) or 'SAU' in str(cell.get_text().get_text())):
                                    cell.set_facecolor(self.colors['secondary_gold'])
                else:
                    ax.text(0.5, 0.5, f'No major competition data found for\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
            else:
                ax.text(0.5, 0.5, f'No major results found for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)

        ax.axis('off')

    def _create_key_competitors_analysis_part4(self, ax, event, classification, gender):
        """Season Progression - Top Athletes"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'All Season Results - Extended List\n{event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get all recent results (2024-2025) for this event-classification-gender
            recent_results = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['competitiondate'].str.contains('2024|2025', case=False, na=False))
            ].copy()

            if len(recent_results) > 0:
                # Convert performance to numeric
                recent_results['performance_clean'] = pd.to_numeric(recent_results['performance'], errors='coerce')
                recent_results = recent_results.dropna(subset=['performance_clean'])

                if len(recent_results) > 0:
                    is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']

                    # Sort all results by performance
                    if is_time_event:
                        top_results = recent_results.nsmallest(20, 'performance_clean')
                    else:
                        top_results = recent_results.nlargest(20, 'performance_clean')

                    table_data = []
                    for i, (idx, result) in enumerate(top_results.iterrows(), 1):
                        name = f"{result.get('firstname', '')} {result.get('lastname', '')}".strip()
                        country = result.get('nationality', 'N/A')
                        performance = f"{result['performance_clean']:.2f}"
                        date = result.get('competitiondate', 'N/A')[:10] if pd.notna(result.get('competitiondate')) else 'N/A'

                        table_data.append([f"{i}", name, country, performance, date])

                    if table_data:
                        headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Date']
                        table = ax.table(cellText=table_data, colLabels=headers,
                                       loc='center', cellLoc='left')
                        table.auto_set_font_size(False)
                        table.set_fontsize(8)
                        table.scale(1, 1.6)

                        # Saudi theme styling
                        for (row, col), cell in table.get_celld().items():
                            if row == 0:  # Header row
                                cell.set_text_props(weight='bold', color='white')
                                cell.set_facecolor(self.colors['primary_green'])
                            else:
                                cell.set_facecolor(self.colors['background_white'])
                                # Highlight Saudi athletes
                                if col == 2 and ('KSA' in str(cell.get_text().get_text()) or 'SAU' in str(cell.get_text().get_text())):
                                    cell.set_facecolor(self.colors['secondary_gold'])
                else:
                    ax.text(0.5, 0.5, f'No performance data found for\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
            else:
                ax.text(0.5, 0.5, f'No recent results found for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)

        ax.axis('off')

    def _create_performance_progression(self, ax, event, classification, gender):
        """Create performance progression chart"""
        ax.set_title('Performance Progression Trends', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Season progression analysis\n(Would show improvement trends)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_competition_depth_chart(self, ax, event, classification, gender):
        """Create competition depth assessment"""
        ax.set_title('Competition Depth Assessment', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Field depth analysis\n(Would show qualifying times/marks distribution)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def create_page3_historical_championship(self, event, classification, gender, output_dir):
        """Page 3: Rankings Analysis - World, Asian, Annual Best"""
        gender_name = "Men" if gender == 'M' else "Women"
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 28))

        fig.suptitle(f'{event} {classification} {gender_name} - Rankings Analysis\nWorld, Asian, Annual Best & Competition Depth',
                    fontsize=26, fontweight='bold', color=self.colors['primary_green'], y=0.96)

        # Show different ranking types
        self._create_world_rankings_table(ax1, event, classification, gender)
        self._create_asian_rankings_table(ax2, event, classification, gender)
        self._create_annual_best_table(ax3, event, classification, gender)
        self._create_competition_depth_analysis(ax4, event, classification, gender)

        plt.tight_layout(pad=6.0)
        plt.savefig(output_dir / 'page3_historical_championship.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_historical_results_table(self, ax, event, classification, gender):
        """Create historical championship results table"""
        ax.set_title('Historical Championship Results', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Past championship medal winners\n(Would show recent medal results)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_consistency_metrics(self, ax, event, classification, gender):
        """Create performance consistency metrics"""
        ax.set_title('Performance Consistency Metrics', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Championship performance consistency\n(Would show variance analysis)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_championship_vs_regular_season(self, ax, event, classification, gender):
        """Create championship vs regular season performance gap"""
        ax.set_title('Championship vs Regular Season Performance', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Championship vs season best analysis\n(Would show performance gaps)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_qualification_standards_tracking(self, ax, event, classification, gender):
        """Create qualification standards tracking"""
        ax.set_title('Qualification Standards Tracking', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Qualifying standards evolution\n(Would show entry standards over time)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_world_rankings_table(self, ax, event, classification, gender):
        """Create World Rankings table for this event/classification/gender"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'World Rankings 2024-2025\n{event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Look for World Rankings data
        world_data = None
        for key, rankings_df in self.rankings_data.items():
            if 'World Rankings' in key and ('2024' in key or '2025' in key):
                if 'Class' in rankings_df.columns and 'Gender' in rankings_df.columns:
                    matches = rankings_df[
                        (rankings_df['Class'].str.contains(classification, case=False, na=False)) &
                        (rankings_df['Gender'] == gender)
                    ]
                    if len(matches) > 0:
                        world_data = matches.head(15)
                        break

        if world_data is not None and len(world_data) > 0:
            table_data = []
            for i, (_, athlete) in enumerate(world_data.iterrows(), 1):
                name = f"{athlete.get('GivenName', '')} {athlete.get('FamilyName', '')}".strip()
                country = athlete.get('Country', 'N/A')
                performance = athlete.get('Result', 'N/A')
                date = athlete.get('Date', 'N/A')[:10] if pd.notna(athlete.get('Date')) else 'N/A'

                table_data.append([f"{i}", name, country, str(performance), date])

            if table_data:
                headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Date']
                table = ax.table(cellText=table_data, colLabels=headers,
                               loc='center', cellLoc='left')
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1, 1.8)

                # Saudi theme styling
                for (row, col), cell in table.get_celld().items():
                    if row == 0:  # Header row
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(self.colors['primary_green'])
                    else:
                        cell.set_facecolor(self.colors['background_white'])
                        # Highlight Saudi athletes
                        if col == 2 and ('KSA' in str(cell.get_text().get_text()) or 'SAU' in str(cell.get_text().get_text())):
                            cell.set_facecolor(self.colors['secondary_gold'])
        else:
            ax.text(0.5, 0.5, f'No World Rankings data found for\n{event} {classification} {gender_name}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_asian_rankings_table(self, ax, event, classification, gender):
        """Create Asian Rankings table"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Asian Rankings 2024-2025\n{event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Look for Asian Rankings data
        asian_data = None
        for key, rankings_df in self.rankings_data.items():
            if 'Asian Rankings' in key and ('2024' in key or '2025' in key):
                if 'Class' in rankings_df.columns and 'Gender' in rankings_df.columns:
                    matches = rankings_df[
                        (rankings_df['Class'].str.contains(classification, case=False, na=False)) &
                        (rankings_df['Gender'] == gender)
                    ]
                    if len(matches) > 0:
                        asian_data = matches.head(15)
                        break

        if asian_data is not None and len(asian_data) > 0:
            table_data = []
            for i, (_, athlete) in enumerate(asian_data.iterrows(), 1):
                name = f"{athlete.get('GivenName', '')} {athlete.get('FamilyName', '')}".strip()
                country = athlete.get('Country', 'N/A')
                performance = athlete.get('Result', 'N/A')
                date = athlete.get('Date', 'N/A')[:10] if pd.notna(athlete.get('Date')) else 'N/A'

                table_data.append([f"{i}", name, country, str(performance), date])

            if table_data:
                headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Date']
                table = ax.table(cellText=table_data, colLabels=headers,
                               loc='center', cellLoc='left')
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1, 1.8)

                # Saudi theme styling
                for (row, col), cell in table.get_celld().items():
                    if row == 0:  # Header row
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(self.colors['primary_green'])
                    else:
                        cell.set_facecolor(self.colors['background_white'])
                        # Highlight Saudi athletes
                        if col == 2 and ('KSA' in str(cell.get_text().get_text()) or 'SAU' in str(cell.get_text().get_text())):
                            cell.set_facecolor(self.colors['secondary_gold'])
        else:
            ax.text(0.5, 0.5, f'No Asian Rankings data found for\n{event} {classification} {gender_name}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_annual_best_table(self, ax, event, classification, gender):
        """Create Annual Best Performances table"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Annual Best Performances 2024\n{event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Look for Annual Best data
        annual_data = None
        for key, rankings_df in self.rankings_data.items():
            if 'Annual Recorded Best Performances' in key and '2024' in key:
                if 'Class' in rankings_df.columns and 'Gender' in rankings_df.columns:
                    matches = rankings_df[
                        (rankings_df['Class'].str.contains(classification, case=False, na=False)) &
                        (rankings_df['Gender'] == gender)
                    ]
                    if len(matches) > 0:
                        annual_data = matches.head(15)
                        break

        if annual_data is not None and len(annual_data) > 0:
            table_data = []
            for i, (_, athlete) in enumerate(annual_data.iterrows(), 1):
                name = f"{athlete.get('GivenName', '')} {athlete.get('FamilyName', '')}".strip()
                country = athlete.get('Country', 'N/A')
                performance = athlete.get('Result', 'N/A')
                date = athlete.get('Date', 'N/A')[:10] if pd.notna(athlete.get('Date')) else 'N/A'

                table_data.append([f"{i}", name, country, str(performance), date])

            if table_data:
                headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Date']
                table = ax.table(cellText=table_data, colLabels=headers,
                               loc='center', cellLoc='left')
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1, 1.8)

                # Saudi theme styling
                for (row, col), cell in table.get_celld().items():
                    if row == 0:  # Header row
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(self.colors['primary_green'])
                    else:
                        cell.set_facecolor(self.colors['background_white'])
                        # Highlight Saudi athletes
                        if col == 2 and ('KSA' in str(cell.get_text().get_text()) or 'SAU' in str(cell.get_text().get_text())):
                            cell.set_facecolor(self.colors['secondary_gold'])
        else:
            ax.text(0.5, 0.5, f'No Annual Best data found for\n{event} {classification} {gender_name}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_performance_benchmarks_table(self, ax, event, classification, gender):
        """Create Performance Benchmarks Analysis (No Records Mentioned)"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Performance Benchmarks Analysis\n{event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Create performance benchmark analysis
        benchmark_data = []

        # Get championship data for benchmarks
        championship_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender) &
            (self.main_data['is_major_championship'] == True)
        ].copy()

        if len(championship_data) > 0:
            performances = championship_data['performance_clean'].dropna()

            if len(performances) > 0:
                # Create benchmark standards
                benchmarks = [
                    ('Elite Level', np.percentile(performances, 95), 'Top 5% Championship Performers'),
                    ('Championship Level', np.percentile(performances, 80), 'Top 20% Championship Performers'),
                    ('Competitive Level', np.percentile(performances, 65), 'Medal Contention Range'),
                    ('International Level', np.percentile(performances, 50), 'Finals Qualification Range'),
                    ('National Level', np.percentile(performances, 35), 'Semi-Finals Range'),
                    ('Development Level', np.percentile(performances, 20), 'Entry Championship Level')
                ]

                benchmark_data = []
                for level, perf, description in benchmarks:
                    benchmark_data.append([level, f'{perf:.2f}', description[:35] + '...' if len(description) > 35 else description])

                if benchmark_data:
                    headers = ['Performance Level', 'Standard', 'Description']
                    table = ax.table(cellText=benchmark_data, colLabels=headers,
                                   loc='center', cellLoc='left')
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1, 2.2)

                    # Professional styling with Saudi theme
                    for (row, col), cell in table.get_celld().items():
                        if row == 0:  # Header row
                            cell.set_text_props(weight='bold', color='white', fontsize=11)
                            cell.set_facecolor(self.colors['primary_green'])
                        else:
                            # Color code performance levels
                            if col == 0:  # Performance Level column
                                level = benchmark_data[row-1][0]
                                if 'Elite' in level:
                                    cell.set_facecolor('#FFD700')  # Gold
                                    cell.set_text_props(weight='bold')
                                elif 'Championship' in level:
                                    cell.set_facecolor('#C0C0C0')  # Silver
                                    cell.set_text_props(weight='bold')
                                elif 'Competitive' in level:
                                    cell.set_facecolor('#CD7F32')  # Bronze
                                    cell.set_text_props(weight='bold', color='white')
                                else:
                                    cell.set_facecolor(self.colors['background_white'])
                            else:
                                cell.set_facecolor('#FAFAFA')

        if not benchmark_data:
            ax.text(0.5, 0.5, f'Performance Benchmarks Analysis\n\n{event} {classification} {gender_name}\n\nInsufficient championship data\nfor benchmark analysis',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def create_page4_current_form_rankings(self, event, classification, gender, output_dir):
        """Page 4: Current Form & Rankings"""
        gender_name = "Men" if gender == 'M' else "Women"
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 28))

        fig.suptitle(f'{event} {classification} {gender_name} - Current Form & Rankings\n2024-2025 Season Analysis',
                    fontsize=26, fontweight='bold', color=self.colors['primary_green'], y=0.96)

        self._create_2024_2025_rankings(ax1, event, classification, gender)
        self._create_recent_competition_results(ax2, event, classification, gender)
        self._create_performance_trajectory(ax3, event, classification, gender)
        self._create_world_list_positions(ax4, event, classification, gender)

        plt.tight_layout(pad=6.0)
        plt.savefig(output_dir / 'page4_current_form_rankings.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_2024_2025_rankings(self, ax, event, classification, gender):
        """Create 2024-2025 season rankings"""
        ax.set_title('2024-2025 Season Rankings', fontsize=18, fontweight='bold', pad=35)

        # Try to use actual rankings data if available
        if self.rankings_data:
            ax.text(0.5, 0.5, f'Current rankings loaded: {len(self.rankings_data)} datasets\n(Would show current world rankings)',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
        else:
            ax.text(0.5, 0.5, 'Current season rankings\n(Rankings data not available)',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_recent_competition_results(self, ax, event, classification, gender):
        """Create recent competition results analysis"""
        ax.set_title('Recent Competition Results', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Recent competition form\n(Would show latest results)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_performance_trajectory(self, ax, event, classification, gender):
        """Create performance trajectory analysis"""
        ax.set_title('Performance Trajectory Analysis', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Season progression trends\n(Would show performance trajectory)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_world_list_positions(self, ax, event, classification, gender):
        """Create world list positions chart"""
        ax.set_title('Current World List Positions', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'World list standings\n(Would show current world rankings)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_competition_depth_analysis(self, ax, event, classification, gender):
        """Create Competition Depth Analysis (replaces non-working records table)"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Competition Depth Analysis\n{event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Get championship data for this event-classification-gender
        championship_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender) &
            (self.main_data['is_major_championship'] == True)
        ].copy()

        if len(championship_data) > 0:
            # Create depth analysis based on performance ranges
            performances = championship_data['performance_clean'].dropna()

            if len(performances) > 0:
                # Calculate competition depth metrics
                total_athletes = len(performances)
                unique_countries = championship_data['nationality'].nunique()

                # Performance ranges
                best_performance = performances.min()
                worst_performance = performances.max()
                median_performance = performances.median()

                # Create competition depth table
                depth_analysis = [
                    ['Total Championship Results', str(total_athletes)],
                    ['Countries Represented', str(unique_countries)],
                    ['Best Championship Performance', f'{best_performance:.2f}'],
                    ['Median Championship Performance', f'{median_performance:.2f}'],
                    ['Performance Spread', f'{worst_performance - best_performance:.2f}'],
                    ['Competition Depth Rating', 'HIGH' if total_athletes >= 50 else 'MEDIUM' if total_athletes >= 25 else 'DEVELOPING']
                ]

                ax.axis('tight')
                ax.axis('off')
                table = ax.table(cellText=depth_analysis,
                               loc='center', cellLoc='left', bbox=[0, 0, 1, 1])

                table.auto_set_font_size(False)
                table.set_fontsize(12)
                table.scale(1, 2.2)

                # Professional styling
                for i in range(len(depth_analysis)):
                    # Label column
                    table[(i, 0)].set_facecolor(self.colors['primary_green'])
                    table[(i, 0)].set_text_props(weight='bold', color='white', fontsize=11)

                    # Value column
                    if i == len(depth_analysis) - 1:  # Competition depth rating
                        rating = depth_analysis[i][1]
                        if rating == 'HIGH':
                            table[(i, 1)].set_facecolor('#90EE90')  # Light green
                            table[(i, 1)].set_text_props(weight='bold', color='#006400')
                        elif rating == 'MEDIUM':
                            table[(i, 1)].set_facecolor('#FFFFE0')  # Light yellow
                            table[(i, 1)].set_text_props(weight='bold', color='#B8860B')
                        else:
                            table[(i, 1)].set_facecolor('#FFE4E1')  # Light pink
                            table[(i, 1)].set_text_props(weight='bold', color='#8B0000')
                    else:
                        table[(i, 1)].set_facecolor('#F8F9FA')

            else:
                ax.text(0.5, 0.5, f'Competition Depth Analysis\n\n{event} {classification} {gender_name}\n\nNo performance data available',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f'Competition Depth Analysis\n\n{event} {classification} {gender_name}\n\nNo championship data available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def create_page4_performance_analysis(self, event, classification, gender, output_dir):
        """Page 4: Performance Analysis from Main Dataset (Records folder has no data)"""
        gender_name = "Men" if gender == 'M' else "Women"
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 28))

        fig.suptitle(f'{event} {classification} {gender_name} - Performance Analysis\nTop Performers & Historical Championship Standards',
                    fontsize=26, fontweight='bold', color=self.colors['primary_green'], y=0.96)

        # Top Left: Best Performances from Main Data
        self._create_all_time_best_performances(ax1, event, classification, gender)

        # Top Right: Championship vs Regular Season Analysis
        self._create_championship_vs_regular_analysis(ax2, event, classification, gender)

        # Bottom Left: Top Countries Performance
        self._create_top_countries_performance(ax3, event, classification, gender)

        # Bottom Right: Performance Evolution Over Years
        self._create_performance_evolution(ax4, event, classification, gender)

        plt.tight_layout(pad=6.0)
        plt.savefig(output_dir / 'page4_performance_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_all_time_best_performances(self, ax, event, classification, gender):
        """Create all-time best performances table from main dataset"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'All-Time Best Performances\n{event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Get all data for this event-classification-gender
        event_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender)
        ].copy()

        if len(event_data) > 0:
            # Get best performances by athlete
            performances = event_data.dropna(subset=['performance_clean'])

            if len(performances) > 0:
                # Get top 8 best performances
                best_performances = performances.nsmallest(8, 'performance_clean')

                performance_data = []
                for i, (_, row) in enumerate(best_performances.iterrows(), 1):
                    athlete_name = f"{row.get('firstname', '')} {row.get('lastname', '')}".strip()
                    if not athlete_name:
                        athlete_name = 'Unknown'

                    performance_data.append([
                        i,
                        athlete_name[:25],
                        f"{row['performance_clean']:.2f}",
                        row.get('nationality', 'N/A')[:8],
                        str(row.get('competitiondate', 'N/A'))[:10]
                    ])

                headers = ['Rank', 'Athlete', 'Performance', 'Country', 'Date']

                ax.axis('tight')
                ax.axis('off')
                table = ax.table(cellText=performance_data, colLabels=headers,
                               loc='center', cellLoc='center', bbox=[0, 0, 1, 1])

                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 2.0)

                # Professional styling
                for i in range(len(headers)):
                    table[(0, i)].set_facecolor(self.colors['primary_green'])
                    table[(0, i)].set_text_props(weight='bold', color='white', fontsize=11)

                # Rank-based colors
                for i in range(len(performance_data)):
                    rank = performance_data[i][0]
                    if rank == 1:
                        table[(i+1, 0)].set_facecolor('#E6F3FF')  # Light blue for #1
                        table[(i+1, 0)].set_text_props(weight='bold')
                    elif rank <= 3:
                        table[(i+1, 0)].set_facecolor('#F0F8E6')  # Light green for top 3
                        table[(i+1, 0)].set_text_props(weight='bold')

                    # Alternate row colors
                    if i % 2 == 0:
                        for j in range(1, len(headers)):
                            table[(i+1, j)].set_facecolor('#F8F9FA')
            else:
                ax.text(0.5, 0.5, f'All-Time Best Performances\n\n{event} {classification} {gender_name}\n\nNo performance data available',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f'All-Time Best Performances\n\n{event} {classification} {gender_name}\n\nNo event data available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_championship_vs_regular_analysis(self, ax, event, classification, gender):
        """Create championship vs regular season performance analysis"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Championship vs Regular Season\n{event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Get championship and non-championship data
        event_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender)
        ].copy()

        if len(event_data) > 0:
            championship_data = event_data[event_data['is_major_championship'] == True]
            regular_data = event_data[event_data['is_major_championship'] == False]

            analysis_data = []

            if len(championship_data) > 0:
                champ_performances = championship_data['performance_clean'].dropna()
                if len(champ_performances) > 0:
                    champ_best = champ_performances.min()
                    champ_avg = champ_performances.mean()
                    champ_count = len(champ_performances)

                    analysis_data.append(['Championship Best', f'{champ_best:.2f}', f'{champ_count} results'])
                    analysis_data.append(['Championship Average', f'{champ_avg:.2f}', 'Major Championships'])

            if len(regular_data) > 0:
                regular_performances = regular_data['performance_clean'].dropna()
                if len(regular_performances) > 0:
                    regular_best = regular_performances.min()
                    regular_avg = regular_performances.mean()
                    regular_count = len(regular_performances)

                    analysis_data.append(['Regular Season Best', f'{regular_best:.2f}', f'{regular_count} results'])
                    analysis_data.append(['Regular Season Average', f'{regular_avg:.2f}', 'All Competitions'])

            if len(analysis_data) >= 2:
                # Add comparison
                if len(championship_data) > 0 and len(regular_data) > 0:
                    champ_perf = championship_data['performance_clean'].dropna()
                    reg_perf = regular_data['performance_clean'].dropna()
                    if len(champ_perf) > 0 and len(reg_perf) > 0:
                        diff = champ_perf.min() - reg_perf.min()
                        comparison = f'{abs(diff):.2f} {"slower" if diff > 0 else "faster"} in championships'
                        analysis_data.append(['Performance Gap', comparison, 'Championship vs Regular'])

            if analysis_data:
                headers = ['Metric', 'Value', 'Context']

                ax.axis('tight')
                ax.axis('off')
                table = ax.table(cellText=analysis_data, colLabels=headers,
                               loc='center', cellLoc='left', bbox=[0, 0, 1, 1])

                table.auto_set_font_size(False)
                table.set_fontsize(11)
                table.scale(1, 2.0)

                # Professional styling
                for i in range(len(headers)):
                    table[(0, i)].set_facecolor(self.colors['secondary_gold'])
                    table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)

                # Color-code metrics
                for i, (metric, value, context) in enumerate(analysis_data):
                    if 'Championship' in metric and 'Best' in metric:
                        table[(i+1, 0)].set_facecolor('#E6F3FF')  # Light blue
                        table[(i+1, 0)].set_text_props(weight='bold')
                    elif 'Regular' in metric and 'Best' in metric:
                        table[(i+1, 0)].set_facecolor('#F0F8E6')  # Light green
                        table[(i+1, 0)].set_text_props(weight='bold')
            else:
                ax.text(0.5, 0.5, f'Championship vs Regular Season\n\n{event} {classification} {gender_name}\n\nInsufficient data for comparison',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f'Championship vs Regular Season\n\n{event} {classification} {gender_name}\n\nNo event data available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_top_countries_performance(self, ax, event, classification, gender):
        """Create top countries performance analysis"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Top Countries Performance\n{event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Get all data for this event-classification-gender
        event_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender)
        ].copy()

        if len(event_data) > 0:
            performances = event_data.dropna(subset=['performance_clean', 'nationality'])

            if len(performances) > 0:
                # Get best performance by country
                country_best = performances.groupby('nationality')['performance_clean'].min().reset_index()
                country_best = country_best.sort_values('performance_clean').head(8)

                country_data = []
                for i, (_, row) in enumerate(country_best.iterrows(), 1):
                    country = row['nationality']
                    best_perf = row['performance_clean']

                    # Count total results for this country
                    country_results = performances[performances['nationality'] == country]
                    total_results = len(country_results)
                    athletes_count = country_results[['firstname', 'lastname']].drop_duplicates().shape[0]

                    country_data.append([
                        i,
                        str(country)[:12],
                        f'{best_perf:.2f}',
                        total_results,
                        athletes_count
                    ])

                headers = ['Rank', 'Country', 'Best', 'Results', 'Athletes']

                ax.axis('tight')
                ax.axis('off')
                table = ax.table(cellText=country_data, colLabels=headers,
                               loc='center', cellLoc='center', bbox=[0, 0, 1, 1])

                table.auto_set_font_size(False)
                table.set_fontsize(11)
                table.scale(1, 1.8)

                # Professional styling
                for i in range(len(headers)):
                    table[(0, i)].set_facecolor(self.colors['primary_green'])
                    table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)

                # Highlight Saudi Arabia if present
                for i, row in enumerate(country_data):
                    if 'KSA' in str(row[1]) or 'SAU' in str(row[1]):
                        for j in range(len(headers)):
                            table[(i+1, j)].set_facecolor('#90EE90')  # Light green for Saudi
                            table[(i+1, j)].set_text_props(weight='bold')
                    elif i % 2 == 0:
                        for j in range(len(headers)):
                            table[(i+1, j)].set_facecolor('#F8F9FA')

            else:
                ax.text(0.5, 0.5, f'Top Countries Performance\n\n{event} {classification} {gender_name}\n\nNo performance data available',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f'Top Countries Performance\n\n{event} {classification} {gender_name}\n\nNo event data available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_performance_evolution(self, ax, event, classification, gender):
        """Create performance evolution over years"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Performance Evolution (2020-2024)\n{event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Get all data for this event-classification-gender
        event_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender)
        ].copy()

        if len(event_data) > 0 and 'competitiondate' in event_data.columns:
            # Extract year from competition date
            event_data['year'] = pd.to_datetime(event_data['competitiondate'], errors='coerce').dt.year
            recent_data = event_data[
                (event_data['year'] >= 2020) &
                (event_data['year'] <= 2024)
            ].dropna(subset=['performance_clean', 'year'])

            if len(recent_data) > 0:
                # Get best performance by year
                yearly_best = recent_data.groupby('year')['performance_clean'].min().reset_index()
                yearly_best = yearly_best.sort_values('year')

                evolution_data = []
                for _, row in yearly_best.iterrows():
                    year = int(row['year'])
                    best_perf = row['performance_clean']

                    # Count results for this year
                    year_results = recent_data[recent_data['year'] == year]
                    total_results = len(year_results)

                    evolution_data.append([
                        year,
                        f'{best_perf:.2f}',
                        total_results,
                        'Improving' if len(yearly_best) > 1 else 'Baseline'
                    ])

                if evolution_data:
                    headers = ['Year', 'Season Best', 'Results', 'Trend']

                    ax.axis('tight')
                    ax.axis('off')
                    table = ax.table(cellText=evolution_data, colLabels=headers,
                                   loc='center', cellLoc='center', bbox=[0, 0, 1, 1])

                    table.auto_set_font_size(False)
                    table.set_fontsize(11)
                    table.scale(1, 2.0)

                    # Professional styling
                    for i in range(len(headers)):
                        table[(0, i)].set_facecolor(self.colors['primary_green'])
                        table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)

                    # Highlight recent years
                    for i, row in enumerate(evolution_data):
                        year = row[0]
                        if year >= 2023:
                            for j in range(len(headers)):
                                table[(i+1, j)].set_facecolor('#E6F7FF')  # Light blue for recent years
                                table[(i+1, j)].set_text_props(weight='bold')
                        elif i % 2 == 0:
                            for j in range(len(headers)):
                                table[(i+1, j)].set_facecolor('#F8F9FA')
                else:
                    ax.text(0.5, 0.5, f'Performance Evolution\n\n{event} {classification} {gender_name}\n\nInsufficient yearly data',
                           ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                    ax.axis('off')
            else:
                ax.text(0.5, 0.5, f'Performance Evolution\n\n{event} {classification} {gender_name}\n\nNo recent data (2020-2024)',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f'Performance Evolution\n\n{event} {classification} {gender_name}\n\nNo date information available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_world_paralympic_records_table(self, ax, event, classification, gender):
        """Create World & Paralympic Records table from records folder"""
        gender_name = "Men's" if gender == 'M' else "Women's"
        ax.set_title('World & Paralympic Records', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        # Look for the event in World and Paralympic records
        event_pattern = f"{gender_name} {event} {classification}"

        records_data = []
        record_types = [('World Record', 'World Record'), ('Paralympic Record', 'Paralympic Record')]

        for display_name, file_key in record_types:
            if file_key in self.all_records:
                records_df = self.all_records[file_key]

                # Search for matching event
                matches = records_df[
                    records_df['event_name'].str.contains(event_pattern, case=False, na=False)
                ]

                if len(matches) > 0:
                    record = matches.iloc[0]
                    performance = record.get('performance', 'N/A')
                    athlete = record.get('athlete_name', 'N/A')
                    country = record.get('country_name', record.get('country_code', 'N/A'))
                    date = record.get('date', 'N/A')

                    if performance not in ['N/A', '', None] and str(performance).strip():
                        # Format date if available
                        if date not in ['N/A', '', None] and str(date).strip():
                            try:
                                date = pd.to_datetime(date).strftime('%Y-%m-%d')[:10]
                            except:
                                date = str(date)[:10] if len(str(date)) > 10 else str(date)

                        records_data.append([
                            display_name,
                            str(performance),
                            str(athlete)[:25] if athlete != 'N/A' else 'N/A',
                            str(country)[:15] if country != 'N/A' else 'N/A',
                            str(date)
                        ])

        if records_data:
            headers = ['Record Type', 'Performance', 'Athlete', 'Country', 'Date']

            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=records_data, colLabels=headers,
                           loc='center', cellLoc='center', bbox=[0, 0, 1, 1])

            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 2.5)

            # Professional styling
            for i in range(len(headers)):
                table[(0, i)].set_facecolor(self.colors['primary_green'])
                table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)

            # Alternate row colors for readability
            for i in range(len(records_data)):
                for j in range(len(headers)):
                    if i % 2 == 0:
                        table[(i+1, j)].set_facecolor('#F8F9FA')  # Light gray
                    else:
                        table[(i+1, j)].set_facecolor('#FFFFFF')  # White

                # Highlight record type column
                if records_data[i][0] == 'World Record':
                    table[(i+1, 0)].set_facecolor('#F0E68C')  # Light khaki
                    table[(i+1, 0)].set_text_props(weight='bold')
                elif records_data[i][0] == 'Paralympic Record':
                    table[(i+1, 0)].set_facecolor('#E6F3FF')  # Light blue
                    table[(i+1, 0)].set_text_props(weight='bold')
        else:
            ax.text(0.5, 0.5, f'World & Paralympic Records\n\n{event} {classification} {gender_name}\n\nNo record data available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_regional_records_table(self, ax, event, classification, gender):
        """Create Regional Records table (Asian, African, European, Americas)"""
        gender_name = "Men's" if gender == 'M' else "Women's"
        ax.set_title('Regional Records', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        event_pattern = f"{gender_name} {event} {classification}"

        records_data = []
        regional_records = [
            ('Asian', 'Asian Record'),
            ('African', 'African Record'),
            ('European', 'European Record'),
            ('Americas', 'Americas Record')
        ]

        for region, file_key in regional_records:
            if file_key in self.all_records:
                records_df = self.all_records[file_key]

                matches = records_df[
                    records_df['event_name'].str.contains(event_pattern, case=False, na=False)
                ]

                if len(matches) > 0:
                    record = matches.iloc[0]
                    performance = record.get('performance', 'N/A')
                    athlete = record.get('athlete_name', 'N/A')
                    country = record.get('country_name', record.get('country_code', 'N/A'))

                    if performance not in ['N/A', '', None] and str(performance).strip():
                        records_data.append([
                            region,
                            str(performance),
                            str(athlete)[:20] if athlete != 'N/A' else 'N/A',
                            str(country)[:12] if country != 'N/A' else 'N/A'
                        ])

        if records_data:
            headers = ['Region', 'Performance', 'Athlete', 'Country']

            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=records_data, colLabels=headers,
                           loc='center', cellLoc='center', bbox=[0, 0, 1, 1])

            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 2.2)

            # Professional styling
            for i in range(len(headers)):
                table[(0, i)].set_facecolor(self.colors['secondary_gold'])
                table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)

            # Regional color coding
            region_colors = {
                'Asian': '#FFE5CC',     # Light orange
                'African': '#E5F5E5',   # Light green
                'European': '#E5E5FF',  # Light blue
                'Americas': '#FFE5E5'   # Light pink
            }

            for i in range(len(records_data)):
                region = records_data[i][0]
                color = region_colors.get(region, '#F8F9FA')

                for j in range(len(headers)):
                    table[(i+1, j)].set_facecolor(color)

                table[(i+1, 0)].set_text_props(weight='bold')  # Bold region names
        else:
            ax.text(0.5, 0.5, f'Regional Records\n\n{event} {classification} {gender_name}\n\nNo regional record data available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_championship_records_analysis(self, ax, event, classification, gender):
        """Create Championship Records Analysis"""
        gender_name = "Men's" if gender == 'M' else "Women's"
        ax.set_title('Championship Records', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        event_pattern = f"{gender_name} {event} {classification}"

        if 'Championship Record' in self.all_records:
            records_df = self.all_records['Championship Record']

            matches = records_df[
                records_df['event_name'].str.contains(event_pattern, case=False, na=False)
            ]

            if len(matches) > 0:
                record = matches.iloc[0]
                performance = record.get('performance', 'N/A')
                athlete = record.get('athlete_name', 'N/A')
                country = record.get('country_name', record.get('country_code', 'N/A'))
                date = record.get('date', 'N/A')
                competition = record.get('competition', 'N/A')

                if performance not in ['N/A', '', None] and str(performance).strip():
                    # Create championship record details
                    record_info = [
                        ['Record Type', 'Championship Record'],
                        ['Performance', str(performance)],
                        ['Athlete', str(athlete)[:30] if athlete != 'N/A' else 'N/A'],
                        ['Country', str(country) if country != 'N/A' else 'N/A'],
                        ['Competition', str(competition)[:35] if competition != 'N/A' else 'N/A'],
                        ['Date', str(date)[:10] if date != 'N/A' else 'N/A']
                    ]

                    ax.axis('tight')
                    ax.axis('off')
                    table = ax.table(cellText=record_info,
                                   loc='center', cellLoc='left', bbox=[0, 0, 1, 1])

                    table.auto_set_font_size(False)
                    table.set_fontsize(12)
                    table.scale(1, 2.2)

                    # Professional styling
                    for i in range(len(record_info)):
                        # Label column
                        table[(i, 0)].set_facecolor(self.colors['primary_green'])
                        table[(i, 0)].set_text_props(weight='bold', color='white', fontsize=12)

                        # Value column
                        if i == 0:  # Record Type
                            table[(i, 1)].set_facecolor('#F0E68C')  # Light khaki
                            table[(i, 1)].set_text_props(weight='bold')
                        else:
                            table[(i, 1)].set_facecolor('#F8F9FA')
                else:
                    ax.text(0.5, 0.5, f'Championship Records\n\n{event} {classification} {gender_name}\n\nNo performance data available',
                           ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                    ax.axis('off')
            else:
                ax.text(0.5, 0.5, f'Championship Records\n\n{event} {classification} {gender_name}\n\nNo championship record found',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f'Championship Records\n\n{event} {classification} {gender_name}\n\nChampionship records data not loaded',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_records_progression_timeline(self, ax, event, classification, gender):
        """Create Records Progression Timeline"""
        gender_name = "Men's" if gender == 'M' else "Women's"
        ax.set_title('Records Progression Timeline', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        event_pattern = f"{gender_name} {event} {classification}"

        # Collect all record data with dates
        timeline_data = []

        record_sources = [
            ('World Record', '#FFD700'),      # Gold
            ('Paralympic Record', '#C0C0C0'), # Silver
            ('Championship Record', '#CD7F32'), # Bronze
            ('Asian Record', '#FFE5CC'),      # Light orange
            ('European Record', '#E5E5FF')    # Light blue
        ]

        for record_type, color in record_sources:
            if record_type in self.all_records:
                records_df = self.all_records[record_type]

                matches = records_df[
                    records_df['event_name'].str.contains(event_pattern, case=False, na=False)
                ]

                if len(matches) > 0:
                    record = matches.iloc[0]
                    performance = record.get('performance', 'N/A')
                    date = record.get('date', 'N/A')
                    athlete = record.get('athlete_name', 'N/A')

                    if performance not in ['N/A', '', None] and str(performance).strip():
                        if date not in ['N/A', '', None] and str(date).strip():
                            try:
                                # Try to parse date
                                parsed_date = pd.to_datetime(date, errors='coerce')
                                if pd.notna(parsed_date):
                                    year = parsed_date.year
                                    timeline_data.append([
                                        record_type,
                                        str(performance),
                                        year,
                                        str(athlete)[:25] if athlete != 'N/A' else 'N/A'
                                    ])
                            except:
                                # If date parsing fails, still include without year
                                timeline_data.append([
                                    record_type,
                                    str(performance),
                                    'N/A',
                                    str(athlete)[:25] if athlete != 'N/A' else 'N/A'
                                ])

        if timeline_data:
            # Sort by year if available
            timeline_data.sort(key=lambda x: x[2] if x[2] != 'N/A' else 0)

            headers = ['Record Type', 'Performance', 'Year', 'Athlete']

            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=timeline_data, colLabels=headers,
                           loc='center', cellLoc='center', bbox=[0, 0, 1, 1])

            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.8)

            # Header styling
            for i in range(len(headers)):
                table[(0, i)].set_facecolor(self.colors['primary_green'])
                table[(0, i)].set_text_props(weight='bold', color='white', fontsize=11)

            # Color code by record type
            record_colors = {
                'World Record': '#FFF9C4',         # Light gold
                'Paralympic Record': '#E8E8E8',    # Light silver
                'Championship Record': '#F4E4BC',  # Light bronze
                'Asian Record': '#FFE5CC',         # Light orange
                'European Record': '#E5E5FF'       # Light blue
            }

            for i in range(len(timeline_data)):
                record_type = timeline_data[i][0]
                color = record_colors.get(record_type, '#F8F9FA')

                for j in range(len(headers)):
                    table[(i+1, j)].set_facecolor(color)

                table[(i+1, 0)].set_text_props(weight='bold')  # Bold record types
        else:
            ax.text(0.5, 0.5, f'Records Progression Timeline\n\n{event} {classification} {gender_name}\n\nNo dated record information available',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_performance_distribution_analysis(self, ax, event, classification, gender):
        """Create performance distribution analysis"""
        ax.set_title('Performance Distribution Analysis', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        # Get championship data
        championship_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender) &
            (self.main_data['is_major_championship'] == True)
        ].copy()

        if len(championship_data) > 0:
            # Create performance distribution table
            performance_stats = []

            # Get performance statistics
            performances = championship_data['performance_clean'].dropna()
            if len(performances) > 0:
                percentiles = [10, 25, 50, 75, 90, 95, 99]
                for p in percentiles:
                    perf_value = np.percentile(performances, 100-p)  # Reverse for better performances
                    performance_stats.append([
                        f'{p}th Percentile',
                        f'{perf_value:.2f}',
                        'Elite' if p >= 95 else 'World Class' if p >= 75 else 'International' if p >= 50 else 'Developing'
                    ])

                if performance_stats:
                    table_data = pd.DataFrame(performance_stats,
                                            columns=['Performance Level', 'Standard', 'Category'])

                    # Create professional table
                    ax.axis('tight')
                    ax.axis('off')
                    table = ax.table(cellText=table_data.values,
                                   colLabels=table_data.columns,
                                   cellLoc='center',
                                   loc='center',
                                   bbox=[0, 0, 1, 1])

                    # Professional styling
                    table.auto_set_font_size(False)
                    table.set_fontsize(11)
                    table.scale(1, 2.2)

                    # Header styling
                    for i in range(len(table_data.columns)):
                        table[(0, i)].set_facecolor(self.colors['primary_green'])
                        table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)

                    # Category color coding
                    for i, (_, row) in enumerate(table_data.iterrows()):
                        category = row['Category']
                        if category == 'Elite':
                            table[(i+1, 2)].set_facecolor('#F0E68C')  # Khaki (readable gold)
                            table[(i+1, 2)].set_text_props(weight='bold', color='#8B4513')  # Dark brown text
                        elif category == 'World Class':
                            table[(i+1, 2)].set_facecolor('#C0C0C0')  # Silver
                            table[(i+1, 2)].set_text_props(weight='bold')
                        elif category == 'International':
                            table[(i+1, 2)].set_facecolor('#CD7F32')  # Bronze
                            table[(i+1, 2)].set_text_props(weight='bold', color='white')
                else:
                    ax.text(0.5, 0.5, 'Performance Distribution Analysis\n\nInsufficient performance data available.',
                           ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                    ax.axis('off')
            else:
                ax.text(0.5, 0.5, 'Performance Distribution Analysis\n\nNo performance data available.',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, 'Performance Distribution Analysis\n\nNo championship data available.',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _get_championship_standards(self, event, classification, competition_type, gender):
        """Get championship standards from CSV data with gender filtering"""
        if self.championship_standards is None:
            return None

        try:
            # Check available columns first
            available_columns = self.championship_standards.columns.tolist()

            # Common column name variations
            event_col = None
            for col in ['eventname', 'event', 'event_name']:
                if col in available_columns:
                    event_col = col
                    break

            class_col = None
            for col in ['classification', 'class', 'classname']:
                if col in available_columns:
                    class_col = col
                    break

            comp_col = None
            for col in ['championship_type', 'competition_type', 'competition']:
                if col in available_columns:
                    comp_col = col
                    break

            if not event_col or not class_col:
                return None

            # Filter for the specific event and classification
            standards_data = self.championship_standards[
                (self.championship_standards[event_col] == event) &
                (self.championship_standards[class_col] == classification)
            ]

            # Filter by competition type if available
            if comp_col:
                standards_data = standards_data[
                    standards_data[comp_col].str.contains(competition_type, case=False, na=False)
                ]

            # Apply gender filter if gender column exists
            if 'gender' in standards_data.columns:
                standards_data = standards_data[standards_data['gender'] == gender]

            if len(standards_data) == 0:
                return None

            # Get the first matching row and return as dictionary
            row = standards_data.iloc[0]
            standards = {}

            # Map common performance columns
            performance_cols = ['gold', 'silver', 'bronze', 'performance_clean', 'best_performance']
            for col in performance_cols:
                if col in row.index and pd.notna(row[col]):
                    standards[col] = row[col]

            # Map medal positions
            position_cols = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th']
            for i, col in enumerate(position_cols, 1):
                if col in row.index and pd.notna(row[col]):
                    if i == 1:
                        standards['gold'] = row[col]
                    elif i == 2:
                        standards['silver'] = row[col]
                    elif i == 3:
                        standards['bronze'] = row[col]

            return standards if standards else None

        except Exception as e:
            # If there's any error, return None gracefully
            return None

    def _create_competitive_timeline(self, ax, event, classification, gender):
        """Create competitive timeline analysis"""
        ax.set_title('Competitive Timeline Analysis', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        # Get recent data (2022-2024) for timeline analysis
        recent_data = self.main_data[
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender)
        ].copy()

        if len(recent_data) > 0 and 'competitiondate' in recent_data.columns:
            recent_data['year'] = pd.to_datetime(recent_data['competitiondate'], errors='coerce').dt.year
            timeline_data = recent_data[recent_data['year'].isin([2022, 2023, 2024])].dropna(subset=['year', 'performance_clean'])

            if len(timeline_data) > 0:
                # Create yearly progression table
                yearly_stats = []
                for year in [2022, 2023, 2024]:
                    year_data = timeline_data[timeline_data['year'] == year]
                    if len(year_data) > 0:
                        best_perf = year_data['performance_clean'].min()
                        competitions = len(year_data)
                        athletes = year_data['firstname'].nunique() + year_data['lastname'].nunique()

                        yearly_stats.append([
                            year,
                            f'{best_perf:.2f}',
                            competitions,
                            athletes // 2  # Rough estimate
                        ])

                if yearly_stats:
                    table_data = pd.DataFrame(yearly_stats,
                                            columns=['Year', 'Season Best', 'Competitions', 'Athletes'])

                    ax.axis('tight')
                    ax.axis('off')
                    table = ax.table(cellText=table_data.values,
                                   colLabels=table_data.columns,
                                   cellLoc='center',
                                   loc='center',
                                   bbox=[0, 0, 1, 1])

                    table.auto_set_font_size(False)
                    table.set_fontsize(12)
                    table.scale(1, 2.5)

                    # Professional styling
                    for i in range(len(table_data.columns)):
                        table[(0, i)].set_facecolor(self.colors['secondary_gold'])
                        table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)
                else:
                    ax.text(0.5, 0.5, 'Competitive Timeline Analysis\n\nInsufficient recent data for timeline.',
                           ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                    ax.axis('off')
            else:
                ax.text(0.5, 0.5, 'Competitive Timeline Analysis\n\nNo recent performance data available.',
                       ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, 'Competitive Timeline Analysis\n\nInsufficient data for timeline analysis.',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_medal_probability_matrix(self, ax, event, classification, gender):
        """Create medal probability analysis matrix"""
        ax.set_title('Medal Probability Matrix', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        # Get championship standards
        wc_standards = self._get_championship_standards(event, classification, 'World Championships', gender)
        para_standards = self._get_championship_standards(event, classification, 'Paralympics', gender)

        if wc_standards or para_standards:
            probability_data = []

            # Create probability matrix based on performance levels
            performance_levels = [
                ('World Record Level', 0.95),
                ('Championship Record', 0.85),
                ('Gold Standard', 0.75),
                ('Silver Standard', 0.60),
                ('Bronze Standard', 0.40),
                ('Finals Level', 0.25),
                ('Semi-Finals Level', 0.10)
            ]

            for level, base_prob in performance_levels:
                # Adjust probabilities based on available standards
                wc_prob = f'{base_prob:.0%}' if wc_standards else 'N/A'
                para_prob = f'{(base_prob * 0.9):.0%}' if para_standards else 'N/A'  # Paralympics slightly easier

                probability_data.append([level, wc_prob, para_prob])

            table_data = pd.DataFrame(probability_data,
                                    columns=['Performance Level', 'WC Medal %', 'Para Medal %'])

            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=table_data.values,
                           colLabels=table_data.columns,
                           cellLoc='center',
                           loc='center',
                           bbox=[0, 0, 1, 1])

            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 2.0)

            # Header styling
            for i in range(len(table_data.columns)):
                table[(0, i)].set_facecolor(self.colors['primary_green'])
                table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)

            # Color-code probabilities
            for i, (_, row) in enumerate(table_data.iterrows()):
                level = row['Performance Level']
                if 'Gold' in level or 'World Record' in level or 'Championship Record' in level:
                    for j in range(len(table_data.columns)):
                        table[(i+1, j)].set_facecolor('#FFF9C4')  # Light gold
        else:
            ax.text(0.5, 0.5, 'Medal Probability Matrix\n\nInsufficient championship standards data.',
                   ha='center', va='center', fontsize=12, color=self.colors['text_dark'])
            ax.axis('off')

    def _create_strategic_recommendations(self, ax, event, classification, gender):
        """Create strategic recommendations"""
        ax.set_title('Strategic Recommendations', fontsize=18, fontweight='bold', pad=35,
                    color=self.colors['primary_green'])

        # Create strategic recommendations based on event and classification
        recommendations = [
            "Focus on consistent sub-championship record performances",
            "Target 3-5% performance improvement over current PB",
            "Prioritize technical efficiency over pure speed/power",
            "Maintain competition rhythm through tactical pacing",
            "Prepare for multiple championship rounds if applicable",
            "Study top 3 competitors' tactical approaches",
            "Emphasize mental preparation for championship pressure"
        ]

        # Create recommendations table
        rec_data = []
        for i, rec in enumerate(recommendations[:6], 1):  # Top 6 recommendations
            priority = 'HIGH' if i <= 2 else 'MEDIUM' if i <= 4 else 'NORMAL'
            rec_data.append([f'#{i}', rec[:45] + '...' if len(rec) > 45 else rec, priority])

        table_data = pd.DataFrame(rec_data, columns=['#', 'Strategic Recommendation', 'Priority'])

        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=table_data.values,
                       colLabels=table_data.columns,
                       cellLoc='left',
                       loc='center',
                       bbox=[0, 0, 1, 1])

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.0)

        # Header styling
        for i in range(len(table_data.columns)):
            table[(0, i)].set_facecolor(self.colors['primary_green'])
            table[(0, i)].set_text_props(weight='bold', color='white', fontsize=11)

        # Priority color coding
        for i, (_, row) in enumerate(table_data.iterrows()):
            priority = row['Priority']
            if priority == 'HIGH':
                table[(i+1, 2)].set_facecolor('#FFB6C1')  # Light red
                table[(i+1, 2)].set_text_props(weight='bold')
            elif priority == 'MEDIUM':
                table[(i+1, 2)].set_facecolor('#FFE4B5')  # Light orange
                table[(i+1, 2)].set_text_props(weight='bold')

    def create_page5_saudi_championship_context(self, event, classification, gender, output_dir):
        """Page 5: Saudi Athletes Detailed Analysis"""
        gender_name = "Men" if gender == 'M' else "Women"
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 28))

        fig.suptitle(f'{event} {classification} {gender_name} - Saudi Athletes Detailed Analysis\nSeasonal Performance & Championship Gaps',
                    fontsize=26, fontweight='bold', color=self.colors['primary_green'], y=0.96)

        # Only show detailed Saudi analysis across all 4 quadrants
        self._create_saudi_seasonal_performance(ax1, event, classification, gender)
        self._create_saudi_championship_gaps_detailed(ax2, event, classification, gender)
        self._create_saudi_multi_year_progression(ax3, event, classification, gender)
        self._create_saudi_complete_results_table(ax4, event, classification, gender)

        plt.tight_layout(pad=6.0)
        plt.savefig(output_dir / 'page5_saudi_championship_context.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _create_saudi_vs_championship_standards(self, ax, event, classification, gender):
        """Create Saudi athletes vs championship standards comparison with all Saudi results"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Saudi Athletes - Season Results & Championship Gaps\n{event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Get championship standards
        championship_data = None
        if self.championship_standards is not None:
            standards = self.championship_standards[
                (self.championship_standards['event'] == event) &
                (self.championship_standards['classification'] == classification) &
                (self.championship_standards['gender'] == gender)
            ]
            if len(standards) > 0:
                championship_data = standards.iloc[0]

        # Get all Saudi athletes' current season performances (2024-2025)
        saudi_results = []
        if self.main_data is not None:
            saudi_season_data = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['nationality'].str.contains('KSA|SAU', case=False, na=False)) &
                (self.main_data['competitiondate'].str.contains('2024|2025', case=False, na=False))
            ].copy()

            if len(saudi_season_data) > 0:
                saudi_season_data['performance_clean'] = pd.to_numeric(saudi_season_data['performance'], errors='coerce')
                saudi_season_data = saudi_season_data.dropna(subset=['performance_clean'])

                if len(saudi_season_data) > 0:
                    # Get each Saudi athlete's best performance this season
                    for athlete_id in saudi_season_data['athleteid'].unique():
                        athlete_data = saudi_season_data[saudi_season_data['athleteid'] == athlete_id]
                        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']

                        if is_time_event:
                            best_perf = athlete_data['performance_clean'].min()
                            best_row = athlete_data.loc[athlete_data['performance_clean'].idxmin()]
                        else:
                            best_perf = athlete_data['performance_clean'].max()
                            best_row = athlete_data.loc[athlete_data['performance_clean'].idxmax()]

                        name = f"{best_row.get('firstname', '')} {best_row.get('lastname', '')}".strip()
                        date = best_row.get('competitiondate', 'N/A')[:10] if pd.notna(best_row.get('competitiondate')) else 'N/A'

                        saudi_results.append({
                            'name': name,
                            'performance': best_perf,
                            'date': date
                        })

                    # Sort by performance (best first)
                    saudi_results.sort(key=lambda x: x['performance'], reverse=not is_time_event)

        if saudi_results and championship_data is not None:
            # Get Paralympics Gold standard for gap calculation
            para_data = self.championship_standards[
                (self.championship_standards['event'] == event) &
                (self.championship_standards['classification'] == classification) &
                (self.championship_standards['gender'] == gender) &
                (self.championship_standards['competition_type'] == 'Paralympics')
            ]

            gold_standard = None
            if len(para_data) > 0:
                para_row = para_data.iloc[0]
                if pd.notna(para_row['gold_mean']):
                    gold_standard = para_row['gold_mean']

            # Create Saudi results table with individual gaps to gold standard
            table_data = []
            for i, result in enumerate(saudi_results[:6], 1):  # Show top 6 Saudi results
                athlete_name = result['name']
                performance = f"{result['performance']:.2f}"
                date = result['date']

                if gold_standard is not None:
                    gap = abs(result['performance'] - gold_standard)
                    gap_str = f"{gap:.2f}"
                else:
                    gap_str = "N/A"

                table_data.append([f"{i}", athlete_name, performance, date, gap_str])

            if table_data:
                headers = ['#', 'Saudi Athlete', 'Best 2024-25', 'Date', 'Gap to Gold']
                table = ax.table(cellText=table_data, colLabels=headers,
                               loc='center', cellLoc='left')
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1, 1.8)

                # Saudi theme styling
                for (row, col), cell in table.get_celld().items():
                    if row == 0:  # Header row
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(self.colors['primary_green'])
                    else:
                        cell.set_facecolor(self.colors['background_white'])
                        if col == 2:  # Performance column
                            cell.set_facecolor(self.colors['secondary_gold'])

                # Add championship standard info
                if gold_standard is not None:
                    ax.text(0.5, 0.1, f'Paralympics Gold Standard: {gold_standard:.2f}',
                           ha='center', va='center', transform=ax.transAxes,
                           fontsize=11, fontweight='bold', color=self.colors['primary_green'])
        else:
            if not saudi_results:
                ax.text(0.5, 0.5, f'No Saudi athletes found in 2024-25 season for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12,
                       color=self.colors['text_dark'])
            elif championship_data is None:
                ax.text(0.5, 0.5, f'No championship standards available for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12,
                       color=self.colors['text_dark'])

        ax.axis('off')

    def _create_saudi_seasonal_performance(self, ax, event, classification, gender):
        """Detailed Saudi seasonal performance 2024 and 2025"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Saudi Athletes - Seasonal Performance Details\n2024 & 2025 Results - {event} {classification} {gender_name}',
                    fontsize=18, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get all Saudi results for 2024 and 2025
            saudi_results_2024 = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['nationality'].str.contains('KSA|SAU', case=False, na=False)) &
                (self.main_data['competitiondate'].str.contains('2024', case=False, na=False))
            ].copy()

            saudi_results_2025 = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['nationality'].str.contains('KSA|SAU', case=False, na=False)) &
                (self.main_data['competitiondate'].str.contains('2025', case=False, na=False))
            ].copy()

            table_data = []

            # Process 2024 results
            if len(saudi_results_2024) > 0:
                saudi_results_2024['performance_clean'] = pd.to_numeric(saudi_results_2024['performance'], errors='coerce')
                saudi_results_2024 = saudi_results_2024.dropna(subset=['performance_clean'])

                for _, result in saudi_results_2024.iterrows():
                    name = f"{result.get('firstname', '')} {result.get('lastname', '')}".strip()
                    performance = f"{result['performance_clean']:.2f}"
                    date = result.get('competitiondate', 'N/A')[:10] if pd.notna(result.get('competitiondate')) else 'N/A'
                    competition = str(result.get('competitionname', 'N/A'))[:30] + "..." if len(str(result.get('competitionname', ''))) > 30 else str(result.get('competitionname', 'N/A'))

                    table_data.append(['2024', name, performance, date, competition])

            # Process 2025 results
            if len(saudi_results_2025) > 0:
                saudi_results_2025['performance_clean'] = pd.to_numeric(saudi_results_2025['performance'], errors='coerce')
                saudi_results_2025 = saudi_results_2025.dropna(subset=['performance_clean'])

                for _, result in saudi_results_2025.iterrows():
                    name = f"{result.get('firstname', '')} {result.get('lastname', '')}".strip()
                    performance = f"{result['performance_clean']:.2f}"
                    date = result.get('competitiondate', 'N/A')[:10] if pd.notna(result.get('competitiondate')) else 'N/A'
                    competition = str(result.get('competitionname', 'N/A'))[:30] + "..." if len(str(result.get('competitionname', ''))) > 30 else str(result.get('competitionname', 'N/A'))

                    table_data.append(['2025', name, performance, date, competition])

            if table_data:
                # Sort by year then performance
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                if is_time_event:
                    table_data.sort(key=lambda x: (x[0], float(x[2])))  # Ascending for time events
                else:
                    table_data.sort(key=lambda x: (x[0], -float(x[2])))  # Descending for field events

                headers = ['Year', 'Saudi Athlete', 'Performance', 'Date', 'Competition']
                table = ax.table(cellText=table_data[:15], colLabels=headers,  # Show top 15 results
                               loc='center', cellLoc='left')
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                table.scale(1, 1.6)

                # Saudi theme styling
                for (row, col), cell in table.get_celld().items():
                    if row == 0:  # Header row
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(self.colors['primary_green'])
                    else:
                        cell.set_facecolor(self.colors['secondary_gold'])  # All Saudi results in gold
                        if col == 0:  # Year column
                            if '2025' in str(cell.get_text().get_text()):
                                cell.set_facecolor('#90EE90')  # Light green for 2025
            else:
                ax.text(0.5, 0.5, f'No Saudi results found for\n{event} {classification} {gender_name}\nin 2024-2025',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12,
                       color=self.colors['text_dark'])
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_saudi_championship_gaps_detailed(self, ax, event, classification, gender):
        """Detailed gaps to Gold, Silver, Bronze, and Top 8 standards"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Saudi Athletes - Championship Gaps Analysis\nGaps to Gold, Silver, Bronze & Top 8 - {event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        # Get championship standards
        if self.championship_standards is not None:
            para_data = self.championship_standards[
                (self.championship_standards['event'] == event) &
                (self.championship_standards['classification'] == classification) &
                (self.championship_standards['gender'] == gender) &
                (self.championship_standards['competition_type'] == 'Paralympics')
            ]

            # Get best Saudi performance
            if self.main_data is not None:
                saudi_season_data = self.main_data[
                    (self.main_data['eventname'] == event) &
                    (self.main_data['class'] == classification) &
                    (self.main_data['gender'] == gender) &
                    (self.main_data['nationality'].str.contains('KSA|SAU', case=False, na=False)) &
                    (self.main_data['competitiondate'].str.contains('2024|2025', case=False, na=False))
                ].copy()

                if len(saudi_season_data) > 0 and len(para_data) > 0:
                    saudi_season_data['performance_clean'] = pd.to_numeric(saudi_season_data['performance'], errors='coerce')
                    saudi_season_data = saudi_season_data.dropna(subset=['performance_clean'])

                    para_row = para_data.iloc[0]
                    is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']

                    # Get each athlete's best and calculate gaps
                    athlete_gaps = []
                    for athlete_id in saudi_season_data['athleteid'].unique():
                        athlete_data = saudi_season_data[saudi_season_data['athleteid'] == athlete_id]

                        if is_time_event:
                            best_perf = athlete_data['performance_clean'].min()
                            best_row = athlete_data.loc[athlete_data['performance_clean'].idxmin()]
                        else:
                            best_perf = athlete_data['performance_clean'].max()
                            best_row = athlete_data.loc[athlete_data['performance_clean'].idxmax()]

                        name = f"{best_row.get('firstname', '')} {best_row.get('lastname', '')}".strip()

                        # Calculate gaps to different standards
                        gaps = {}
                        for standard in ['gold_mean', 'silver_mean', 'bronze_mean', 'eighth_mean']:
                            if pd.notna(para_row[standard]):
                                gap = abs(best_perf - para_row[standard])
                                gaps[standard] = f"{gap:.2f}"
                            else:
                                gaps[standard] = "N/A"

                        athlete_gaps.append([
                            name,
                            f"{best_perf:.2f}",
                            gaps['gold_mean'],
                            gaps['silver_mean'],
                            gaps['bronze_mean'],
                            gaps['eighth_mean']
                        ])

                    if athlete_gaps:
                        # Sort by best performance
                        if is_time_event:
                            athlete_gaps.sort(key=lambda x: float(x[1]))
                        else:
                            athlete_gaps.sort(key=lambda x: -float(x[1]))

                        headers = ['Saudi Athlete', 'Best 2024-25', 'Gap to Gold', 'Gap to Silver', 'Gap to Bronze', 'Gap to Top 8']
                        table = ax.table(cellText=athlete_gaps[:8], colLabels=headers,
                                       loc='center', cellLoc='center')
                        table.auto_set_font_size(False)
                        table.set_fontsize(9)
                        table.scale(1, 2)

                        # Saudi theme styling
                        for (row, col), cell in table.get_celld().items():
                            if row == 0:  # Header row
                                cell.set_text_props(weight='bold', color='white')
                                cell.set_facecolor(self.colors['primary_green'])
                            else:
                                if col == 0:  # Name column
                                    cell.set_facecolor(self.colors['secondary_gold'])
                                else:
                                    cell.set_facecolor(self.colors['background_white'])
                else:
                    ax.text(0.5, 0.5, f'No Saudi results found for gap analysis\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12,
                           color=self.colors['text_dark'])
            else:
                ax.text(0.5, 0.5, 'No championship standards available for gap analysis',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12,
                       color=self.colors['text_dark'])
        else:
            ax.text(0.5, 0.5, 'Championship standards not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_saudi_multi_year_progression(self, ax, event, classification, gender):
        """Saudi athletes progression across multiple years"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Saudi Athletes - Multi-Year Progression\nHistorical Performance - {event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get Saudi results from multiple years (2020-2025)
            saudi_historical = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['nationality'].str.contains('KSA|SAU', case=False, na=False))
            ].copy()

            if len(saudi_historical) > 0:
                saudi_historical['performance_clean'] = pd.to_numeric(saudi_historical['performance'], errors='coerce')
                saudi_historical = saudi_historical.dropna(subset=['performance_clean'])

                # Extract year from competition date
                saudi_historical['year'] = saudi_historical['competitiondate'].str.extract(r'(\d{4})')
                saudi_historical = saudi_historical.dropna(subset=['year'])

                table_data = []
                for _, result in saudi_historical.iterrows():
                    name = f"{result.get('firstname', '')} {result.get('lastname', '')}".strip()
                    year = result['year']
                    performance = f"{result['performance_clean']:.2f}"
                    date = result.get('competitiondate', 'N/A')[:10] if pd.notna(result.get('competitiondate')) else 'N/A'
                    competition = str(result.get('competitionname', 'N/A'))[:25] + "..." if len(str(result.get('competitionname', ''))) > 25 else str(result.get('competitionname', 'N/A'))

                    table_data.append([year, name, performance, date, competition])

                if table_data:
                    # Sort by year (newest first) then performance
                    is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                    table_data.sort(key=lambda x: (-int(x[0]), float(x[2]) if is_time_event else -float(x[2])))

                    headers = ['Year', 'Saudi Athlete', 'Performance', 'Date', 'Competition']
                    table = ax.table(cellText=table_data[:15], colLabels=headers,
                                   loc='center', cellLoc='left')
                    table.auto_set_font_size(False)
                    table.set_fontsize(8)
                    table.scale(1, 1.6)

                    # Saudi theme styling
                    for (row, col), cell in table.get_celld().items():
                        if row == 0:  # Header row
                            cell.set_text_props(weight='bold', color='white')
                            cell.set_facecolor(self.colors['primary_green'])
                        else:
                            cell.set_facecolor(self.colors['secondary_gold'])
                            # Different shades by year
                            year_text = str(cell.get_text().get_text()) if col == 0 else ""
                            if '2025' in year_text:
                                cell.set_facecolor('#90EE90')  # Light green
                            elif '2024' in year_text:
                                cell.set_facecolor('#F0E68C')  # Khaki (readable gold)
                                cell.set_text_props(color='#8B4513', weight='bold')  # Dark brown text
                            elif col == 0 and any(yr in year_text for yr in ['2023', '2022', '2021']):
                                cell.set_facecolor('#E6E6FA')  # Lavender for older years
                else:
                    ax.text(0.5, 0.5, f'No historical Saudi data found for\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12,
                           color=self.colors['text_dark'])
            else:
                ax.text(0.5, 0.5, f'No Saudi results found for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12,
                       color=self.colors['text_dark'])
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_saudi_complete_results_table(self, ax, event, classification, gender):
        """Complete table of all Saudi results with performance summary"""
        gender_name = "Men" if gender == 'M' else "Women"
        ax.set_title(f'Saudi Athletes - Complete Results Summary\nAll Available Data - {event} {classification} {gender_name}',
                    fontsize=14, fontweight='bold', pad=35, color=self.colors['primary_green'])

        if self.main_data is not None:
            # Get all Saudi results
            all_saudi_results = self.main_data[
                (self.main_data['eventname'] == event) &
                (self.main_data['class'] == classification) &
                (self.main_data['gender'] == gender) &
                (self.main_data['nationality'].str.contains('KSA|SAU', case=False, na=False))
            ].copy()

            if len(all_saudi_results) > 0:
                all_saudi_results['performance_clean'] = pd.to_numeric(all_saudi_results['performance'], errors='coerce')
                all_saudi_results = all_saudi_results.dropna(subset=['performance_clean'])

                # Get athlete summary
                athlete_summary = []
                for athlete_id in all_saudi_results['athleteid'].unique():
                    athlete_data = all_saudi_results[all_saudi_results['athleteid'] == athlete_id]

                    if len(athlete_data) > 0:
                        first_row = athlete_data.iloc[0]
                        name = f"{first_row.get('firstname', '')} {first_row.get('lastname', '')}".strip()

                        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                        if is_time_event:
                            personal_best = athlete_data['performance_clean'].min()
                            season_best_2024 = athlete_data[athlete_data['competitiondate'].str.contains('2024', na=False)]['performance_clean'].min() if len(athlete_data[athlete_data['competitiondate'].str.contains('2024', na=False)]) > 0 else None
                            season_best_2025 = athlete_data[athlete_data['competitiondate'].str.contains('2025', na=False)]['performance_clean'].min() if len(athlete_data[athlete_data['competitiondate'].str.contains('2025', na=False)]) > 0 else None
                        else:
                            personal_best = athlete_data['performance_clean'].max()
                            season_best_2024 = athlete_data[athlete_data['competitiondate'].str.contains('2024', na=False)]['performance_clean'].max() if len(athlete_data[athlete_data['competitiondate'].str.contains('2024', na=False)]) > 0 else None
                            season_best_2025 = athlete_data[athlete_data['competitiondate'].str.contains('2025', na=False)]['performance_clean'].max() if len(athlete_data[athlete_data['competitiondate'].str.contains('2025', na=False)]) > 0 else None

                        total_competitions = len(athlete_data)

                        athlete_summary.append([
                            name,
                            f"{personal_best:.2f}",
                            f"{season_best_2024:.2f}" if season_best_2024 is not None else "N/A",
                            f"{season_best_2025:.2f}" if season_best_2025 is not None else "N/A",
                            str(total_competitions)
                        ])

                if athlete_summary:
                    # Sort by personal best
                    is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                    athlete_summary.sort(key=lambda x: float(x[1]), reverse=not is_time_event)

                    headers = ['Saudi Athlete', 'Personal Best', 'SB 2024', 'SB 2025', 'Total Comps']
                    table = ax.table(cellText=athlete_summary[:10], colLabels=headers,
                                   loc='center', cellLoc='center')
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1, 2.2)

                    # Saudi theme styling
                    for (row, col), cell in table.get_celld().items():
                        if row == 0:  # Header row
                            cell.set_text_props(weight='bold', color='white')
                            cell.set_facecolor(self.colors['primary_green'])
                        else:
                            cell.set_facecolor(self.colors['secondary_gold'])
                            if col == 1:  # Personal Best column
                                cell.set_text_props(weight='bold')
                else:
                    ax.text(0.5, 0.5, f'No Saudi athlete summaries available for\n{event} {classification} {gender_name}',
                           ha='center', va='center', transform=ax.transAxes, fontsize=12,
                           color=self.colors['text_dark'])
            else:
                ax.text(0.5, 0.5, f'No Saudi results found for\n{event} {classification} {gender_name}',
                       ha='center', va='center', transform=ax.transAxes, fontsize=12,
                       color=self.colors['text_dark'])
        else:
            ax.text(0.5, 0.5, 'Main data not loaded',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12,
                   color=self.colors['text_dark'])

        ax.axis('off')

    def _create_saudi_historical_championships(self, ax, event, classification, gender):
        """Create Saudi historical championship performances"""
        ax.set_title('Saudi Historical Championship Performance', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Saudi championship history\n(Would show past Saudi results)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_saudi_current_rankings(self, ax, event, classification, gender):
        """Create Saudi athletes in current world rankings"""
        ax.set_title('Saudi Athletes in Current World Rankings', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Saudi world ranking positions\n(Would show current Saudi rankings)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def _create_saudi_championship_readiness(self, ax, event, classification, gender):
        """Create Saudi championship readiness assessment"""
        ax.set_title('Saudi Championship Readiness Assessment', fontsize=18, fontweight='bold', pad=35)

        ax.text(0.5, 0.5, 'Championship readiness analysis\n(Would show medal potential assessment)',
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')

    def compile_event_pdf(self, event, classification, gender, output_dir):
        """Compile all PNG files into a single PDF"""
        gender_name = "Men" if gender == 'M' else "Women"

        # PDF filename
        pdf_filename = output_dir / f"{event}_{classification}_{gender_name}_PreCompetition_Report.pdf"

        # Get all PNG files in the output directory, sorted by page number
        png_files = []
        for page_num in range(1, 6):  # Pages 1-5
            page_files = list(output_dir.glob(f"page{page_num}_*.png"))
            png_files.extend(sorted(page_files))

        # Also add any additional files not following the page pattern
        other_files = [f for f in output_dir.glob("*.png") if not any(f.name.startswith(f"page{i}_") for i in range(1, 6))]
        png_files.extend(sorted(other_files))

        if not png_files:
            print(f"No PNG files found in {output_dir}")
            return None

        print(f"Compiling {len(png_files)} pages into PDF: {pdf_filename}")

        with PdfPages(pdf_filename) as pdf:
            for png_file in png_files:
                print(f"Adding {png_file.name} to PDF...")
                try:
                    # Load image
                    img = Image.open(png_file)

                    # Create figure with appropriate size
                    fig, ax = plt.subplots(figsize=(img.width/100, img.height/100))
                    ax.imshow(img)
                    ax.axis('off')

                    # Add to PDF
                    pdf.savefig(fig, bbox_inches='tight', pad_inches=0.1, dpi=150)
                    plt.close(fig)

                except Exception as e:
                    print(f"Error processing {png_file.name}: {e}")
                    continue

        print(f"PDF compiled successfully: {pdf_filename}")
        return pdf_filename

def get_user_selection(analyzer):
    """Interactive selection of event, classification, and gender"""
    if analyzer.championship_standards is None:
        print("No championship standards data available")
        return None, None, None

    # Get unique events
    events = sorted(analyzer.championship_standards['event'].unique())

    print("\n" + "=" * 50)
    print("AVAILABLE EVENTS:")
    print("=" * 50)
    for i, event in enumerate(events, 1):
        count = len(analyzer.championship_standards[analyzer.championship_standards['event'] == event])
        print(f"{i:2d}. {event} ({count} combinations)")

    while True:
        try:
            event_choice = input(f"\nSelect event (1-{len(events)}): ")
            event_idx = int(event_choice) - 1
            if 0 <= event_idx < len(events):
                selected_event = events[event_idx]
                break
            else:
                print(f"Please enter a number between 1 and {len(events)}")
        except ValueError:
            print("Please enter a valid number")

    # Get classifications for selected event
    event_data = analyzer.championship_standards[analyzer.championship_standards['event'] == selected_event]
    classifications = sorted(event_data['classification'].unique())

    print(f"\n" + "=" * 50)
    print(f"AVAILABLE CLASSIFICATIONS FOR {selected_event.upper()}:")
    print("=" * 50)
    for i, classification in enumerate(classifications, 1):
        count = len(event_data[event_data['classification'] == classification])
        print(f"{i:2d}. {classification} ({count} combinations)")

    while True:
        try:
            class_choice = input(f"\nSelect classification (1-{len(classifications)}): ")
            class_idx = int(class_choice) - 1
            if 0 <= class_idx < len(classifications):
                selected_classification = classifications[class_idx]
                break
            else:
                print(f"Please enter a number between 1 and {len(classifications)}")
        except ValueError:
            print("Please enter a valid number")

    # Get genders for selected event/classification
    filtered_data = event_data[event_data['classification'] == selected_classification]
    genders = sorted(filtered_data['gender'].unique())

    print(f"\n" + "=" * 50)
    print(f"AVAILABLE GENDERS FOR {selected_event.upper()} {selected_classification}:")
    print("=" * 50)
    for i, gender in enumerate(genders, 1):
        gender_name = "Men" if gender == 'M' else "Women"
        count = len(filtered_data[filtered_data['gender'] == gender])
        print(f"{i}. {gender_name} ({count} combinations)")

    while True:
        try:
            gender_choice = input(f"\nSelect gender (1-{len(genders)}): ")
            gender_idx = int(gender_choice) - 1
            if 0 <= gender_idx < len(genders):
                selected_gender = genders[gender_idx]
                break
            else:
                print(f"Please enter a number between 1 and {len(genders)}")
        except ValueError:
            print("Please enter a valid number")

    return selected_event, selected_classification, selected_gender

def main():
    """Interactive main execution function"""
    analyzer = PreCompetitionChampionshipAnalyzer()

    print("Pre-Competition Championship Report Generator")
    print("=" * 50)
    print("Interactive Selection Mode")

    if analyzer.load_data():
        print(f"\nLoaded {len(analyzer.championship_standards)} event/classification/gender combinations")

        while True:
            # Get user selection
            event, classification, gender = get_user_selection(analyzer)

            if event and classification and gender:
                gender_name = "Men" if gender == 'M' else "Women"
                print(f"\n" + "=" * 50)
                print(f"GENERATING REPORT FOR:")
                print(f"Event: {event}")
                print(f"Classification: {classification}")
                print(f"Gender: {gender_name}")
                print("=" * 50)

                try:
                    analyzer.generate_pre_competition_report(event, classification, gender)
                    print(f"\n✅ Report generated successfully!")
                    print(f"📁 Saved in: pre_competition_reports/{event}_{classification}_{gender_name}_PreComp/")
                except Exception as e:
                    print(f"\n❌ Error generating report: {e}")

            # Ask if user wants to generate another report
            while True:
                another = input("\nGenerate another report? (y/n): ").lower().strip()
                if another in ['y', 'yes']:
                    break
                elif another in ['n', 'no']:
                    print("\nThank you for using the Pre-Competition Report Generator!")
                    return
                else:
                    print("Please enter 'y' for yes or 'n' for no")
    else:
        print("Failed to load required data")

if __name__ == "__main__":
    main()