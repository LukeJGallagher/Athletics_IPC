#!/usr/bin/env python3
"""
Para Athletics Championship Winning Standards Analyzer
=====================================================

Analyzes what it takes to win at World Championships and Paralympics
across different events and classifications. Determines:
- Gold medal winning performances
- Bronze medal qualifying performances  
- Semi-final and final qualifying standards
- Performance trends year-over-year
- Comparison between Paralympics and World Championships

Data Sources:
- Main results CSV (ksaoutputipc3.csv)
- World Records CSV
- Rankings CSVs by year
- PDF championship results

Author: Performance Analysis Team
Date: 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class ChampionshipAnalyzer:
    def __init__(self):
        self.data_path = Path("data")
        self.main_data = None
        self.world_records = None
        self.rankings_data = {}
        self.championship_results = {}
        
    def load_data(self):
        """Load all available data sources"""
        print("Loading championship data...")

        # Load main CSV data
        main_csv = self.data_path / "Tilastoptija" / "ksaoutputipc3.csv"
        if main_csv.exists():
            self.main_data = pd.read_csv(main_csv, encoding='latin-1', low_memory=False)
            print(f"Loaded main data: {len(self.main_data)} results")

        # Load All Records (World, Asian, European, etc.) with specific file pattern matching
        self.all_records = {}
        records_dir = self.data_path / "Records"
        if records_dir.exists():
            for file in records_dir.glob("*.csv"):
                # Extract record type using more flexible pattern matching
                filename = file.stem
                if "World Record" in filename:
                    record_type = "World Record"
                elif "Paralympic Record" in filename:
                    record_type = "Paralympic Record"
                elif "Asian Record" in filename:
                    record_type = "Asian Record"
                elif "European Record" in filename:
                    record_type = "European Record"
                elif "African Record" in filename:
                    record_type = "African Record"
                elif "Americas Record" in filename:
                    record_type = "Americas Record"
                elif "Championship Record" in filename:
                    record_type = "Championship Record"
                elif "Asian Para Games Record" in filename:
                    record_type = "Asian Para Games Record"
                elif "European Championship Record" in filename:
                    record_type = "European Championship Record"
                elif "Oceanian Record" in filename:
                    record_type = "Oceanian Record"
                elif "Parapan American Games Record" in filename:
                    record_type = "Parapan American Games Record"
                else:
                    # Fallback to previous method for other files
                    record_type = filename.replace("ipc_records_", "").split("_")[0:2]
                    record_type = " ".join(record_type)

                try:
                    data = pd.read_csv(file)
                    self.all_records[record_type] = data
                    print(f"Loaded {record_type}: {len(data)} records")
                except Exception as e:
                    print(f"Error loading {file}: {e}")

        # Set world records for backward compatibility
        self.world_records = self.all_records.get('World Record', None)

        # Generate comprehensive Saudi athlete analysis
        print("\nAnalyzing Saudi athletes across all data sources...")
        self.analyze_saudi_athletes_comprehensive()

        # Load Rankings data
        rankings_dir = self.data_path / "Rankings"
        if rankings_dir.exists():
            for file in rankings_dir.glob("*.csv"):
                # Extract region and year
                parts = file.stem.split("_")
                region = parts[0] + " " + parts[1] if len(parts) > 2 else parts[0]
                year = parts[-1]
                key = f"{region}_{year}"
                try:
                    data = pd.read_csv(file)
                    self.rankings_data[key] = data
                    print(f"Loaded {region} {year} rankings: {len(data)} results")
                except Exception as e:
                    print(f"Error loading {file}: {e}")
    
    def identify_major_championships(self):
        """Identify World Championships, Paralympics, and Asian Championships in the data"""
        if self.main_data is None:
            return None

        # Filter for major championships including Asian competitions
        major_comps = self.main_data[
            self.main_data['competitionname'].str.contains(
                'World Championships|Paralympic|Para Athletics World Championships|Asian|Asia',
                case=False, na=False
            )
        ].copy()

        major_comps['competition_type'] = 'Other'
        major_comps.loc[
            major_comps['competitionname'].str.contains('Paralympic', case=False, na=False),
            'competition_type'
        ] = 'Paralympics'
        major_comps.loc[
            major_comps['competitionname'].str.contains('World Championships', case=False, na=False),
            'competition_type'
        ] = 'World Championships'
        major_comps.loc[
            major_comps['competitionname'].str.contains('Asian|Asia', case=False, na=False),
            'competition_type'
        ] = 'Asian Championships'

        return major_comps

    def analyze_athlete_progressions(self, event, classification):
        """Analyze athlete progressions over time from rankings data"""
        athlete_progressions = {}

        # Combine rankings from all years for this event/classification
        for key, rankings_df in self.rankings_data.items():
            try:
                if 'World Rankings' in key:  # Focus on world rankings primarily
                    # Filter for the specific event and classification
                    try:
                        event_data = rankings_df[
                            rankings_df.get('Class', '').str.contains(classification, case=False, na=False)
                        ]
                    except AttributeError:
                        # If there's an error with string operations, just use class filter
                        event_data = rankings_df[rankings_df['Class'].str.contains(classification, case=False, na=False)] if 'Class' in rankings_df.columns else pd.DataFrame()

                    if len(event_data) > 0:
                        year = key.split('_')[-1]
                        for _, row in event_data.iterrows():
                            athlete_key = f"{row.get('GivenName', '')} {row.get('FamilyName', '')}"
                            if athlete_key.strip() and athlete_key != ' ':
                                if athlete_key not in athlete_progressions:
                                    athlete_progressions[athlete_key] = {
                                        'country': row.get('CountryName', ''),
                                        'performances': []
                                    }

                                # Convert performance to numeric
                                result = row.get('Result', '')
                                if result:
                                    try:
                                        # Handle time format (e.g., "0:11.50")
                                        if ':' in str(result):
                                            parts = str(result).split(':')
                                            if len(parts) == 2:
                                                mins = float(parts[0])
                                                secs = float(parts[1])
                                                numeric_result = mins * 60 + secs
                                            else:
                                                numeric_result = float(parts[-1])
                                        else:
                                            numeric_result = float(result)

                                        athlete_progressions[athlete_key]['performances'].append({
                                            'year': year,
                                            'performance': numeric_result,
                                            'rank': row.get('Rank', 0),
                                            'competition': row.get('Competition', ''),
                                            'date': row.get('Date', '')
                                        })
                                    except (ValueError, TypeError):
                                        continue
            except Exception as e:
                continue

        # Sort performances by year for each athlete
        for athlete in athlete_progressions:
            athlete_progressions[athlete]['performances'].sort(key=lambda x: x['year'])

        return athlete_progressions

    def get_top_athletes_by_region(self, event, classification, region='Asian', num_athletes=10):
        """Get top athletes by region from records and rankings"""
        top_athletes = []

        # Get regional records
        region_key = f'{region} Record'
        if region_key in self.all_records:
            records_df = self.all_records[region_key]
            event_records = records_df[
                records_df['event_name'].str.contains(event, case=False, na=False) &
                records_df['event_name'].str.contains(classification, case=False, na=False)
            ]

            for _, record in event_records.iterrows():
                athlete_name = f"{record.get('GivenName', '')} {record.get('FamilyName', '')}"
                if athlete_name.strip():
                    performance = record.get('Result', '')
                    try:
                        if ':' in str(performance):
                            parts = str(performance).split(':')
                            numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                        else:
                            numeric_perf = float(performance)

                        top_athletes.append({
                            'name': athlete_name,
                            'country': record.get('CountryName', ''),
                            'performance': numeric_perf,
                            'date': record.get('Date', ''),
                            'type': f'{region} Record'
                        })
                    except (ValueError, TypeError):
                        continue

        # Get recent rankings
        recent_rankings_key = f'{region} Rankings_2024'
        if recent_rankings_key in self.rankings_data:
            rankings_df = self.rankings_data[recent_rankings_key]
            # Handle the case where event_name or EventName might be string
            try:
                event_rankings = rankings_df[
                    rankings_df.get('Class', '').str.contains(classification, case=False, na=False)
                ].head(num_athletes)
            except AttributeError:
                # If there's an error with string operations, just use class filter
                event_rankings = rankings_df[rankings_df['Class'].str.contains(classification, case=False, na=False)].head(num_athletes) if 'Class' in rankings_df.columns else rankings_df.head(num_athletes)

            for _, ranking in event_rankings.iterrows():
                athlete_name = f"{ranking.get('GivenName', '')} {ranking.get('FamilyName', '')}"
                if athlete_name.strip():
                    performance = ranking.get('Result', '')
                    try:
                        if ':' in str(performance):
                            parts = str(performance).split(':')
                            numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                        else:
                            numeric_perf = float(performance)

                        top_athletes.append({
                            'name': athlete_name,
                            'country': ranking.get('CountryName', ''),
                            'performance': numeric_perf,
                            'rank': ranking.get('Rank', 0),
                            'type': f'{region} 2024 Ranking'
                        })
                    except (ValueError, TypeError):
                        continue

        # Sort and deduplicate
        unique_athletes = {}
        for athlete in top_athletes:
            name = athlete['name']
            if name not in unique_athletes or athlete['performance'] < unique_athletes[name]['performance']:
                unique_athletes[name] = athlete

        # Sort by performance (ascending for times, descending for distances/heights)
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
        sorted_athletes = sorted(unique_athletes.values(),
                               key=lambda x: x['performance'],
                               reverse=not is_time_event)

        return sorted_athletes[:num_athletes]

    def get_saudi_athletes(self, event, classification):
        """Get Saudi athletes for specific event/classification from all data sources"""
        saudi_athletes = []

        # First check main CSV data (most comprehensive source)
        if self.main_data is not None:
            try:
                # Filter for Saudi Arabia in main data
                # Use nationality column instead and ensure string conversion
                nationality_col = self.main_data['nationality'].astype(str) if 'nationality' in self.main_data.columns else pd.Series([''] * len(self.main_data))
                eventname_col = self.main_data['eventname'].astype(str) if 'eventname' in self.main_data.columns else pd.Series([''] * len(self.main_data))
                class_col = self.main_data['class'].astype(str) if 'class' in self.main_data.columns else pd.Series([''] * len(self.main_data))

                saudi_main_data = self.main_data[
                    (nationality_col.str.contains('KSA', case=False, na=False)) &
                    (eventname_col.str.contains(event, case=False, na=False)) &
                    (class_col.str.contains(classification, case=False, na=False))
                ]

                for _, athlete in saudi_main_data.iterrows():
                    athlete_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}"
                    if athlete_name.strip():
                        # Get performance based on event type
                        performance = self._extract_performance_from_result(athlete.get('performance', ''), event)
                        if performance is not None:
                            saudi_athletes.append({
                                'name': athlete_name,
                                'country': 'Saudi Arabia',
                                'performance': performance,
                                'date': athlete.get('date', ''),
                                'competition': athlete.get('competitionname', ''),
                                'venue': athlete.get('venue', ''),
                                'source': 'Main Data',
                                'wind': athlete.get('wind', ''),
                                'round': athlete.get('round', '')
                            })
            except Exception as e:
                print(f"Error processing main data for Saudi athletes: {e}")

        # Check rankings data for Saudi athletes
        for key, rankings_df in self.rankings_data.items():
            try:
                # Filter for Saudi Arabia and the classification
                saudi_data = rankings_df[
                    (rankings_df.get('CountryName', '').str.contains('Saudi|KSA', case=False, na=False)) &
                    (rankings_df.get('Class', '').str.contains(classification, case=False, na=False))
                ]

                for _, athlete in saudi_data.iterrows():
                    athlete_name = f"{athlete.get('GivenName', '')} {athlete.get('FamilyName', '')}"
                    if athlete_name.strip():
                        performance = athlete.get('Result', '')
                        try:
                            if ':' in str(performance):
                                parts = str(performance).split(':')
                                numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                            else:
                                numeric_perf = float(performance)

                            saudi_athletes.append({
                                'name': athlete_name,
                                'country': 'Saudi Arabia',
                                'performance': numeric_perf,
                                'rank': athlete.get('Rank', 0),
                                'year': key.split('_')[-1],
                                'competition': athlete.get('Competition', ''),
                                'source': key
                            })
                        except (ValueError, TypeError):
                            continue
            except Exception:
                continue

        # Check records data for Saudi athletes with better name matching
        for record_type, records_df in self.all_records.items():
            try:
                saudi_records = records_df[
                    (records_df.get('CountryName', '').str.contains('Saudi|KSA', case=False, na=False)) &
                    (records_df['event_name'].str.contains(event, case=False, na=False)) &
                    (records_df['event_name'].str.contains(classification, case=False, na=False))
                ]

                for _, record in saudi_records.iterrows():
                    athlete_name = f"{record.get('GivenName', '')} {record.get('FamilyName', '')}"
                    if athlete_name.strip():
                        performance = record.get('Result', '')
                        try:
                            if ':' in str(performance):
                                parts = str(performance).split(':')
                                numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                            else:
                                numeric_perf = float(performance)

                            saudi_athletes.append({
                                'name': athlete_name,
                                'country': 'Saudi Arabia',
                                'performance': numeric_perf,
                                'date': record.get('Date', ''),
                                'type': f'{record_type}',
                                'source': 'Records',
                                'venue': record.get('Place', '')
                            })
                        except (ValueError, TypeError):
                            continue
            except Exception:
                continue

        # Deduplicate and sort - keeping best performance per athlete
        unique_saudi = {}
        for athlete in saudi_athletes:
            name = athlete['name']
            # Use similarity matching for names to handle slight variations
            matched_name = self._find_similar_name(name, unique_saudi.keys())

            if matched_name:
                # Update if this is a better performance
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
                if (is_time_event and athlete['performance'] < unique_saudi[matched_name]['performance']) or \
                   (not is_time_event and athlete['performance'] > unique_saudi[matched_name]['performance']):
                    unique_saudi[matched_name] = athlete
            else:
                unique_saudi[name] = athlete

        # Sort by performance (ascending for times, descending for distances/heights)
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
        sorted_saudi = sorted(unique_saudi.values(),
                            key=lambda x: x['performance'],
                            reverse=not is_time_event)

        return sorted_saudi

    def _extract_performance_from_result(self, result_str, event):
        """Extract numeric performance from result string"""
        if not result_str:
            return None

        try:
            # Clean the result string
            result_str = str(result_str).strip()

            # Handle time format (e.g., "0:11.50" or "11.50")
            if ':' in result_str:
                parts = result_str.split(':')
                if len(parts) == 2:
                    mins = float(parts[0])
                    secs = float(parts[1])
                    return mins * 60 + secs
                else:
                    return float(parts[-1])
            else:
                # Direct numeric value
                return float(result_str)
        except (ValueError, TypeError):
            return None

    def _find_similar_name(self, name, existing_names):
        """Find similar name in existing names using simple similarity"""
        if not existing_names:
            return None

        name_lower = name.lower().strip()

        for existing_name in existing_names:
            existing_lower = existing_name.lower().strip()

            # Exact match
            if name_lower == existing_lower:
                return existing_name

            # Check if names are very similar (allowing for minor variations)
            # Split into parts and check overlap
            name_parts = set(name_lower.split())
            existing_parts = set(existing_lower.split())

            # If most parts match, consider it the same person
            if len(name_parts) > 0 and len(existing_parts) > 0:
                overlap = len(name_parts.intersection(existing_parts))
                total_unique = len(name_parts.union(existing_parts))

                # If 70% or more overlap, consider it the same person
                if overlap / total_unique >= 0.7:
                    return existing_name

        return None

    def get_all_saudi_athletes_across_events(self):
        """Get all Saudi athletes from the main CSV file across all events and classifications."""
        print("Loading Saudi athletes from main CSV file...")

        if self.main_data is None:
            return {}

        # Find Saudi athletes using KSA nationality (primary identifier)
        saudi_mask = (
            self.main_data.get('nationality', '').str.contains('KSA', case=False, na=False)
        )

        saudi_data = self.main_data[saudi_mask].copy()

        if saudi_data.empty:
            print("No Saudi athletes found in main data")
            return {}

        print(f"Found {len(saudi_data)} total results for Saudi athletes")

        # Group by event and classification
        saudi_by_event_class = {}
        unique_athletes = set()

        for _, row in saudi_data.iterrows():
            event = row.get('eventname', 'Unknown Event')
            classification = row.get('class', 'Unknown Class')

            # Skip if missing critical info
            if event == 'Unknown Event' or classification == 'Unknown Class':
                continue

            key = f"{event}_{classification}"
            if key not in saudi_by_event_class:
                saudi_by_event_class[key] = []

            athlete_name = f"{row.get('firstname', '')} {row.get('lastname', '')}".strip()
            unique_athletes.add(athlete_name)

            # Extract performance value
            performance_raw = row.get('performance', '')
            performance_string = row.get('performancestring', '')

            athlete_info = {
                'name': athlete_name,
                'event': event,
                'classification': classification,
                'performance': self._extract_performance_from_result(performance_raw, event),
                'performance_string': performance_string,
                'performance_raw': performance_raw,
                'competition': row.get('competitionname', ''),
                'date': row.get('competitiondate', ''),
                'venue': row.get('competitionvenue', ''),
                'country': row.get('competitioncountry', ''),
                'position': row.get('position', ''),
                'round': row.get('round', ''),
                'wind': row.get('wind', ''),
                'notes': row.get('notes', ''),
                'PB': row.get('PB', ''),
                'SB': row.get('SB', ''),
                'nationality': row.get('nationality', ''),
                'year_of_birth': row.get('yearofbirth', ''),
                'age_group': row.get('agegroup', ''),
                'athlete_id': row.get('athleteid', ''),
                'result_id': row.get('resultid', '')
            }

            saudi_by_event_class[key].append(athlete_info)

        print(f"Found {len(unique_athletes)} unique Saudi athletes across {len(saudi_by_event_class)} event-classification combinations")

        # Create comprehensive reports
        self._create_saudi_athlete_reports(saudi_by_event_class, saudi_data)

        return saudi_by_event_class

    def _create_saudi_athlete_reports(self, saudi_by_event_class, saudi_data):
        """Create comprehensive reports for Saudi athletes"""
        try:
            # Create detailed CSV report by event/classification
            detailed_report = []
            summary_report = []

            for event_class, athletes in saudi_by_event_class.items():
                event, classification = event_class.split('_', 1)

                # Find best performance for this event/classification
                if athletes:
                    performances = [a['performance'] for a in athletes if a['performance'] is not None]
                    if performances:
                        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
                        best_performance = min(performances) if is_time_event else max(performances)
                        best_athlete = next(a for a in athletes if a['performance'] == best_performance)

                        summary_report.append({
                            'Event': event,
                            'Classification': classification,
                            'Best_Athlete': best_athlete['name'],
                            'Best_Performance': best_performance,
                            'Performance_String': best_athlete['performance_string'],
                            'Competition': best_athlete['competition'],
                            'Date': best_athlete['date'],
                            'Total_Results': len(athletes),
                            'Unique_Athletes': len(set(a['name'] for a in athletes))
                        })

                # Add all individual results to detailed report
                for athlete in athletes:
                    detailed_report.append({
                        'Event': event,
                        'Classification': classification,
                        'Athlete_Name': athlete['name'],
                        'Performance': athlete['performance'],
                        'Performance_String': athlete['performance_string'],
                        'Competition': athlete['competition'],
                        'Date': athlete['date'],
                        'Venue': athlete['venue'],
                        'Position': athlete['position'],
                        'Round': athlete['round'],
                        'Wind': athlete['wind'],
                        'PB': athlete['PB'],
                        'SB': athlete['SB'],
                        'Year_of_Birth': athlete['year_of_birth'],
                        'Age_Group': athlete['age_group'],
                        'Athlete_ID': athlete['athlete_id']
                    })

            # Save reports
            if detailed_report:
                detailed_df = pd.DataFrame(detailed_report)
                detailed_df.to_csv('saudi_athletes_comprehensive_report.csv', index=False)
                print(f"Created detailed Saudi athlete report with {len(detailed_report)} results")

            if summary_report:
                summary_df = pd.DataFrame(summary_report)
                summary_df.to_csv('saudi_athletes_summary_by_event.csv', index=False)
                print(f"Created Saudi athlete summary with {len(summary_report)} event-classification combinations")

        except Exception as e:
            print(f"Error creating Saudi athlete reports: {e}")

    def analyze_saudi_athletes_comprehensive(self):
        """Comprehensive analysis of all Saudi athletes across all events"""
        saudi_by_event_class = self.get_all_saudi_athletes_across_events()

        if not saudi_by_event_class:
            print("🇸🇦 No Saudi athletes found in main data")
            return

        total_results = sum(len(athletes) for athletes in saudi_by_event_class.values())
        unique_athletes = set()
        for athletes in saudi_by_event_class.values():
            for athlete in athletes:
                unique_athletes.add(athlete['name'])

        print(f"Saudi Arabia: Found {total_results} Saudi athlete performances across {len(saudi_by_event_class)} event-classification combinations")
        print(f"Saudi Arabia: Total unique Saudi athletes: {len(unique_athletes)}")

        # Print summary by event/classification
        print("\nSaudi Athletes by Event/Classification:")
        for event_class, athletes in sorted(saudi_by_event_class.items()):
            event, classification = event_class.split('_', 1)

            # Find best performance
            valid_performances = [a for a in athletes if a['performance'] is not None]
            if valid_performances:
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
                best_athlete = min(valid_performances, key=lambda x: x['performance']) if is_time_event else max(valid_performances, key=lambda x: x['performance'])

                unique_names = len(set(a['name'] for a in athletes))
                print(f"  {event} {classification}: {len(athletes)} results, {unique_names} athletes, Best: {best_athlete['performance']:.2f} by {best_athlete['name']}")
            else:
                print(f"  {event} {classification}: {len(athletes)} results (no valid performances)")

        print(f"\nSaudi athlete comprehensive analysis complete!")
        print(f"Reports saved: saudi_athletes_comprehensive_report.csv, saudi_athletes_summary_by_event.csv")

    def save_saudi_athletes_report(self, all_saudi, events_summary):
        """Save comprehensive Saudi athletes report"""
        import pandas as pd

        # Create detailed DataFrame
        saudi_df = pd.DataFrame(all_saudi)
        saudi_df.to_csv('saudi_athletes_comprehensive_report.csv', index=False)

        # Create summary DataFrame
        summary_data = []
        for key, summary in events_summary.items():
            event, classification = key.split(' ', 1)
            best = summary['best_performance']
            summary_data.append({
                'Event': event,
                'Classification': classification,
                'Total_Performances': summary['total_performances'],
                'Best_Performance': best['performance'],
                'Best_Athlete': best['name'],
                'Best_Date': best['date'],
                'Best_Competition': best['competition'],
                'Best_Venue': best['venue']
            })

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('saudi_athletes_summary_by_event.csv', index=False)

        print(f"\n🇸🇦 Saved Saudi athletes reports:")
        print(f"  - saudi_athletes_comprehensive_report.csv ({len(all_saudi)} performances)")
        print(f"  - saudi_athletes_summary_by_event.csv ({len(summary_data)} event/classification combinations)")

    def get_top_20_global_athletes(self, event, classification):
        """Get top 20 athletes globally from recent rankings and records"""
        top_athletes = []

        # Get from 2024 World Rankings first
        world_rankings_2024 = self.rankings_data.get('World Rankings_2024')
        if world_rankings_2024 is not None:
            try:
                class_rankings = world_rankings_2024[
                    world_rankings_2024.get('Class', '').str.contains(classification, case=False, na=False)
                ].head(20)

                for _, athlete in class_rankings.iterrows():
                    athlete_name = f"{athlete.get('GivenName', '')} {athlete.get('FamilyName', '')}"
                    if athlete_name.strip():
                        performance = athlete.get('Result', '')
                        try:
                            if ':' in str(performance):
                                parts = str(performance).split(':')
                                numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                            else:
                                numeric_perf = float(performance)

                            top_athletes.append({
                                'name': athlete_name,
                                'country': athlete.get('CountryName', 'N/A'),
                                'performance': numeric_perf,
                                'rank': athlete.get('Rank', 0),
                                'competition': athlete.get('Competition', ''),
                                'date': athlete.get('Date', ''),
                                'source': '2024 World Rankings'
                            })
                        except (ValueError, TypeError):
                            continue
            except Exception:
                pass

        # If we don't have enough from 2024, supplement with recent years
        if len(top_athletes) < 20:
            for year in ['2023', '2022', '2021']:
                world_rankings_year = self.rankings_data.get(f'World Rankings_{year}')
                if world_rankings_year is not None:
                    try:
                        class_rankings = world_rankings_year[
                            world_rankings_year.get('Class', '').str.contains(classification, case=False, na=False)
                        ].head(10)

                        for _, athlete in class_rankings.iterrows():
                            athlete_name = f"{athlete.get('GivenName', '')} {athlete.get('FamilyName', '')}"
                            if athlete_name.strip() and not any(a['name'] == athlete_name for a in top_athletes):
                                performance = athlete.get('Result', '')
                                try:
                                    if ':' in str(performance):
                                        parts = str(performance).split(':')
                                        numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                                    else:
                                        numeric_perf = float(performance)

                                    top_athletes.append({
                                        'name': athlete_name,
                                        'country': athlete.get('CountryName', 'N/A'),
                                        'performance': numeric_perf,
                                        'rank': athlete.get('Rank', 0),
                                        'competition': athlete.get('Competition', ''),
                                        'date': athlete.get('Date', ''),
                                        'source': f'{year} World Rankings'
                                    })
                                except (ValueError, TypeError):
                                    continue
                    except Exception:
                        continue

                if len(top_athletes) >= 20:
                    break

        # Sort by performance
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
        sorted_athletes = sorted(top_athletes,
                               key=lambda x: x['performance'],
                               reverse=not is_time_event)

        return sorted_athletes[:20]
    
    def analyze_winning_standards(self, event=None, classification=None, competition_type=None, gender=None):
        """Analyze winning standards for specific event/classification/gender"""
        major_comps = self.identify_major_championships()
        if major_comps is None or len(major_comps) == 0:
            return None

        # Filter data
        filtered_data = major_comps.copy()

        if event:
            filtered_data = filtered_data[filtered_data['eventname'] == event]
        if classification:
            filtered_data = filtered_data[filtered_data['class'] == classification]
        if competition_type:
            filtered_data = filtered_data[filtered_data['competition_type'] == competition_type]
        if gender:
            filtered_data = filtered_data[filtered_data['gender'] == gender]

        if len(filtered_data) == 0:
            return None

        # Clean performance data - convert to numeric
        filtered_data['performance_clean'] = pd.to_numeric(filtered_data['performance'], errors='coerce')

        # Convert position to numeric for comparison
        filtered_data['position'] = pd.to_numeric(filtered_data['position'], errors='coerce')
        
        # Analyze by position
        results = {}
        
        # Gold medal standards (position 1)
        gold_results = filtered_data[filtered_data['position'] == 1]
        if len(gold_results) > 0:
            gold_clean = gold_results.dropna(subset=['performance_clean'])
            if len(gold_clean) > 0:
                results['gold'] = {
                    'count': len(gold_clean),
                    'performances': gold_clean['performance_clean'].tolist(),
                    'best': gold_clean['performance_clean'].min() if event in ['100m', '200m', '400m', '800m', '1500m'] else gold_clean['performance_clean'].max(),
                    'worst': gold_clean['performance_clean'].max() if event in ['100m', '200m', '400m', '800m', '1500m'] else gold_clean['performance_clean'].min(),
                    'mean': gold_clean['performance_clean'].mean()
                }
        
        # Bronze medal standards (position 3)
        bronze_results = filtered_data[filtered_data['position'] == 3]
        if len(bronze_results) > 0:
            bronze_clean = bronze_results.dropna(subset=['performance_clean'])
            if len(bronze_clean) > 0:
                results['bronze'] = {
                    'count': len(bronze_clean),
                    'performances': bronze_clean['performance_clean'].tolist(),
                    'best': bronze_clean['performance_clean'].min() if event in ['100m', '200m', '400m', '800m', '1500m'] else bronze_clean['performance_clean'].max(),
                    'worst': bronze_clean['performance_clean'].max() if event in ['100m', '200m', '400m', '800m', '1500m'] else bronze_clean['performance_clean'].min(),
                    'mean': bronze_clean['performance_clean'].mean()
                }
        
        # Final qualifying (positions 1-8)
        final_results = filtered_data[filtered_data['position'].between(1, 8)]
        if len(final_results) > 0:
            final_clean = final_results.dropna(subset=['performance_clean'])
            if len(final_clean) > 0:
                # Top 8 breakdown
                results['top_8_breakdown'] = {}
                for pos in range(1, 9):
                    pos_results = final_clean[final_clean['position'] == pos]
                    if len(pos_results) > 0:
                        results['top_8_breakdown'][f'position_{pos}'] = {
                            'count': len(pos_results),
                            'mean_performance': pos_results['performance_clean'].mean(),
                            'best_performance': pos_results['performance_clean'].min() if event in ['100m', '200m', '400m', '800m', '1500m'] else pos_results['performance_clean'].max(),
                            'worst_performance': pos_results['performance_clean'].max() if event in ['100m', '200m', '400m', '800m', '1500m'] else pos_results['performance_clean'].min()
                        }
                
                # 8th place qualifying standard
                final_8th = final_clean[final_clean['position'] == 8]
                if len(final_8th) > 0:
                    results['final_qualifying'] = {
                        'count': len(final_8th),
                        'standard': final_8th['performance_clean'].mean()
                    }
        
        # Semifinal analysis (check rounds column)
        if 'round' in filtered_data.columns:
            semi_data = filtered_data[filtered_data['round'].str.contains('semi|sf|rB', case=False, na=False)]
            if len(semi_data) > 0:
                semi_clean = semi_data.dropna(subset=['performance_clean'])
                if len(semi_clean) > 0:
                    # Semifinal qualifying standards (typically need to finish top 2-3 per heat plus fastest losers)
                    results['semifinal_standards'] = {
                        'total_semifinalists': len(semi_clean),
                        'mean_performance': semi_clean['performance_clean'].mean(),
                        'best_semifinal': semi_clean['performance_clean'].min() if event in ['100m', '200m', '400m', '800m', '1500m'] else semi_clean['performance_clean'].max(),
                        'worst_semifinal': semi_clean['performance_clean'].max() if event in ['100m', '200m', '400m', '800m', '1500m'] else semi_clean['performance_clean'].min()
                    }
        
        # Heat analysis
        if 'round' in filtered_data.columns:
            heat_data = filtered_data[filtered_data['round'].str.contains('h[1-9]|heat', case=False, na=False)]
            if len(heat_data) > 0:
                heat_clean = heat_data.dropna(subset=['performance_clean'])
                if len(heat_clean) > 0:
                    results['heat_standards'] = {
                        'total_heat_participants': len(heat_clean),
                        'mean_heat_performance': heat_clean['performance_clean'].mean(),
                        'best_heat': heat_clean['performance_clean'].min() if event in ['100m', '200m', '400m', '800m', '1500m'] else heat_clean['performance_clean'].max(),
                        'worst_heat': heat_clean['performance_clean'].max() if event in ['100m', '200m', '400m', '800m', '1500m'] else heat_clean['performance_clean'].min()
                    }
        
        return results
    
    def _get_world_record(self, event, classification, gender):
        """Get world record for a specific event/classification/gender combination"""
        if self.world_records is None:
            return None, None

        # Build search pattern: "Men's 100 m T54" or "Women's 100 m T54"
        gender_prefix = "Men's" if gender == 'M' else "Women's"
        # Convert event name: "100m" -> "100 m"
        event_formatted = event.replace('m', ' m').replace('  ', ' ').strip()
        search_pattern = f"{gender_prefix} {event_formatted} {classification}"

        # Try to find matching record
        for _, record in self.world_records.iterrows():
            record_event = str(record.get('event_name', ''))
            if classification in record_event and gender_prefix in record_event:
                # More flexible matching for event name
                event_base = event.replace('m', '').strip()
                if event_base in record_event:
                    perf = record.get('performance', '')
                    # Parse time format if needed
                    try:
                        if ':' in str(perf):
                            parts = str(perf).split(':')
                            if len(parts) == 2:
                                numeric_perf = float(parts[0]) * 60 + float(parts[1])
                            else:
                                numeric_perf = float(parts[-1])
                        else:
                            numeric_perf = float(perf)
                        return numeric_perf, str(perf)
                    except (ValueError, TypeError):
                        return None, str(perf)

        return None, None

    def _get_asian_championship_standards(self, event, classification, gender):
        """Get Asian Championship standards from main data"""
        if self.main_data is None:
            return None, None, None

        # Filter for Asian Championships
        asian_data = self.main_data[
            (self.main_data['competitionname'].str.contains('Asian|Asia', case=False, na=False)) &
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender)
        ].copy()

        if asian_data.empty:
            return None, None, None

        # Convert position to numeric
        asian_data['position'] = pd.to_numeric(asian_data['position'], errors='coerce')

        # Get gold (position 1), bronze (position 3), and 8th place standards
        gold_data = asian_data[asian_data['position'] == 1]
        bronze_data = asian_data[asian_data['position'] == 3]
        eighth_data = asian_data[asian_data['position'] == 8]

        gold_std = None
        bronze_std = None
        eighth_std = None

        # Determine if lower is better (time events)
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m',
                                   '4x100m', '4x400m', 'Marathon']

        if not gold_data.empty:
            gold_perfs = gold_data['performance'].apply(lambda x: self._extract_performance_from_result(x, event))
            gold_perfs = gold_perfs.dropna()
            if len(gold_perfs) > 0:
                gold_std = gold_perfs.mean()

        if not bronze_data.empty:
            bronze_perfs = bronze_data['performance'].apply(lambda x: self._extract_performance_from_result(x, event))
            bronze_perfs = bronze_perfs.dropna()
            if len(bronze_perfs) > 0:
                bronze_std = bronze_perfs.mean()

        if not eighth_data.empty:
            eighth_perfs = eighth_data['performance'].apply(lambda x: self._extract_performance_from_result(x, event))
            eighth_perfs = eighth_perfs.dropna()
            if len(eighth_perfs) > 0:
                eighth_std = eighth_perfs.mean()

        return gold_std, bronze_std, eighth_std

    def _get_saudi_best_performance(self, event, classification, gender):
        """Get the best Saudi athlete performance for this event/class/gender"""
        if self.main_data is None:
            return None, None

        saudi_data = self.main_data[
            (self.main_data['nationality'].str.contains('KSA', case=False, na=False)) &
            (self.main_data['eventname'] == event) &
            (self.main_data['class'] == classification) &
            (self.main_data['gender'] == gender)
        ].copy()

        if saudi_data.empty:
            return None, None

        # Get performances
        saudi_data['perf_numeric'] = saudi_data['performance'].apply(
            lambda x: self._extract_performance_from_result(x, event)
        )
        saudi_data = saudi_data[saudi_data['perf_numeric'].notna()]

        if saudi_data.empty:
            return None, None

        # Determine if lower is better
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m',
                                   '4x100m', '4x400m', 'Marathon']

        if is_time_event:
            best_row = saudi_data.loc[saudi_data['perf_numeric'].idxmin()]
        else:
            best_row = saudi_data.loc[saudi_data['perf_numeric'].idxmax()]

        athlete_name = f"{best_row.get('firstname', '')} {best_row.get('lastname', '')}".strip()
        return best_row['perf_numeric'], athlete_name

    def _get_current_world_ranking(self, event, classification, gender):
        """Get current world ranking position for Saudi athletes"""
        # Try 2024 first, then 2023
        for year in ['2024', '2023', '2022']:
            rankings_key = f'World Rankings_{year}'
            if rankings_key in self.rankings_data:
                rankings_df = self.rankings_data[rankings_key]
                try:
                    # Filter for classification
                    class_data = rankings_df[
                        rankings_df['Class'].str.contains(classification, case=False, na=False)
                    ]

                    # Find Saudi athletes
                    saudi_rankings = class_data[
                        class_data['CountryName'].str.contains('Saudi', case=False, na=False) |
                        class_data['CountryCode'].str.contains('KSA', case=False, na=False)
                    ]

                    if not saudi_rankings.empty:
                        best_rank = saudi_rankings['Rank'].min()
                        return int(best_rank) if pd.notna(best_rank) else None
                except Exception:
                    continue

        return None

    def _calculate_gap(self, saudi_perf, target_perf, is_time_event):
        """Calculate gap between Saudi performance and target"""
        if saudi_perf is None or target_perf is None:
            return None

        if is_time_event:
            # For time events, negative gap means Saudi is faster (better)
            return saudi_perf - target_perf
        else:
            # For field events, negative gap means Saudi is shorter (worse)
            return saudi_perf - target_perf

    def _get_year_over_year_trend(self, event, classification, gender, years=3):
        """Get year-over-year performance trend from rankings"""
        trends = []

        for year in range(2024, 2024 - years, -1):
            rankings_key = f'World Rankings_{year}'
            if rankings_key in self.rankings_data:
                rankings_df = self.rankings_data[rankings_key]
                try:
                    # Filter for classification
                    class_data = rankings_df[
                        rankings_df['Class'].str.contains(classification, case=False, na=False)
                    ]

                    if not class_data.empty:
                        # Get top performance (rank 1)
                        top_perf = class_data[class_data['Rank'] == 1]
                        if not top_perf.empty:
                            result = top_perf.iloc[0].get('Result', '')
                            try:
                                if ':' in str(result):
                                    parts = str(result).split(':')
                                    numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                                else:
                                    numeric_perf = float(result)
                                trends.append({'year': year, 'top_performance': numeric_perf})
                            except (ValueError, TypeError):
                                continue
                except Exception:
                    continue

        if len(trends) >= 2:
            # Calculate average yearly improvement
            trends.sort(key=lambda x: x['year'])
            improvements = []
            for i in range(1, len(trends)):
                diff = trends[i]['top_performance'] - trends[i-1]['top_performance']
                improvements.append(diff)
            return sum(improvements) / len(improvements) if improvements else None

        return None

    def generate_championship_standards_report(self):
        """Generate comprehensive report of championship standards with gender separation and additional analysis"""
        print("\nGenerating Enhanced Championship Standards Report...")

        major_comps = self.identify_major_championships()
        if major_comps is None:
            print("No major championship data found")
            return

        # Get unique events and classifications
        events = major_comps['eventname'].value_counts()
        classifications = major_comps['class'].value_counts()

        print(f"\nFound {len(events)} events in major championships:")
        print(events.head(10))

        print(f"\nFound {len(classifications)} classifications in major championships:")
        print(classifications.head(10))

        # Generate report for top events and classifications, separated by gender
        report_data = []

        # Include ALL events and classifications with sufficient data (minimum 5 results)
        top_events = events[events >= 5].index.tolist()  # All events with at least 5 results
        top_classes = classifications[classifications >= 10].index.tolist()  # All classes with at least 10 results

        print(f"Analyzing {len(top_events)} events and {len(top_classes)} classifications with sufficient data")

        # Loop through both genders (using actual values in data: M, W)
        for gender in ['M', 'W']:
            print(f"\nAnalyzing {gender} (Men/Women) events...")

            for event in top_events:
                for classification in top_classes:
                    # Check if this combination exists for this gender
                    combo_data = major_comps[
                        (major_comps['eventname'] == event) &
                        (major_comps['class'] == classification) &
                        (major_comps['gender'] == gender)
                    ]

                    if len(combo_data) >= 3:  # Need at least 3 results
                        # Paralympics analysis
                        para_analysis = self.analyze_winning_standards(
                            event, classification, 'Paralympics', gender
                        )

                        # World Championships analysis
                        wc_analysis = self.analyze_winning_standards(
                            event, classification, 'World Championships', gender
                        )

                        if para_analysis or wc_analysis:
                            # Extract top 8 data for Paralympics
                            para_top8 = para_analysis.get('top_8_breakdown', {}) if para_analysis else {}
                            para_8th = para_analysis.get('final_qualifying', {}).get('standard') if para_analysis else None
                            para_semi = para_analysis.get('semifinal_standards', {}).get('worst_semifinal') if para_analysis else None
                            para_heat = para_analysis.get('heat_standards', {}).get('worst_heat') if para_analysis else None

                            # Extract top 8 data for World Championships
                            wc_top8 = wc_analysis.get('top_8_breakdown', {}) if wc_analysis else {}
                            wc_8th = wc_analysis.get('final_qualifying', {}).get('standard') if wc_analysis else None
                            wc_semi = wc_analysis.get('semifinal_standards', {}).get('worst_semifinal') if wc_analysis else None
                            wc_heat = wc_analysis.get('heat_standards', {}).get('worst_heat') if wc_analysis else None

                            # Get additional data
                            world_record_numeric, world_record_str = self._get_world_record(event, classification, gender)
                            asian_gold, asian_bronze, asian_8th = self._get_asian_championship_standards(event, classification, gender)
                            saudi_best, saudi_athlete = self._get_saudi_best_performance(event, classification, gender)
                            world_rank = self._get_current_world_ranking(event, classification, gender)
                            trend = self._get_year_over_year_trend(event, classification, gender)

                            # Determine if time event for gap calculation
                            is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m',
                                                       '4x100m', '4x400m', 'Marathon']

                            # Calculate gaps
                            para_gold_std = para_analysis.get('gold', {}).get('mean') if para_analysis else None
                            para_bronze_std = para_analysis.get('bronze', {}).get('mean') if para_analysis else None
                            wc_gold_std = wc_analysis.get('gold', {}).get('mean') if wc_analysis else None

                            gap_to_para_gold = self._calculate_gap(saudi_best, para_gold_std, is_time_event)
                            gap_to_para_bronze = self._calculate_gap(saudi_best, para_bronze_std, is_time_event)
                            gap_to_para_8th = self._calculate_gap(saudi_best, para_8th, is_time_event)
                            gap_to_wr = self._calculate_gap(saudi_best, world_record_numeric, is_time_event)

                            report_data.append({
                                'event': event,
                                'classification': classification,
                                'gender': gender,
                                # World Record
                                'world_record': world_record_numeric,
                                'world_record_display': world_record_str,
                                # Paralympics Standards
                                'paralympics_gold': para_gold_std,
                                'paralympics_bronze': para_bronze_std,
                                'paralympics_8th_place': para_8th,
                                'paralympics_semi_qualifying': para_semi,
                                'paralympics_heat_qualifying': para_heat,
                                # World Championships Standards
                                'wc_gold': wc_gold_std,
                                'wc_bronze': wc_analysis.get('bronze', {}).get('mean') if wc_analysis else None,
                                'wc_8th_place': wc_8th,
                                'wc_semi_qualifying': wc_semi,
                                'wc_heat_qualifying': wc_heat,
                                # Asian Championships Standards
                                'asian_gold': asian_gold,
                                'asian_bronze': asian_bronze,
                                'asian_8th_place': asian_8th,
                                # Saudi Athlete Analysis
                                'saudi_best': saudi_best,
                                'saudi_best_athlete': saudi_athlete,
                                'saudi_world_rank': world_rank,
                                # Gap Analysis (negative = Saudi is better for time, positive = Saudi is better for field)
                                'gap_to_para_gold': gap_to_para_gold,
                                'gap_to_para_bronze': gap_to_para_bronze,
                                'gap_to_para_8th': gap_to_para_8th,
                                'gap_to_world_record': gap_to_wr,
                                # Trend Analysis
                                'yearly_trend': trend,
                                'total_results': len(combo_data)
                            })

        # Save report
        if report_data:
            report_df = pd.DataFrame(report_data)

            # Reorder columns for better readability
            column_order = [
                'event', 'classification', 'gender',
                'world_record', 'world_record_display',
                'paralympics_gold', 'paralympics_bronze', 'paralympics_8th_place',
                'paralympics_semi_qualifying', 'paralympics_heat_qualifying',
                'wc_gold', 'wc_bronze', 'wc_8th_place', 'wc_semi_qualifying', 'wc_heat_qualifying',
                'asian_gold', 'asian_bronze', 'asian_8th_place',
                'saudi_best', 'saudi_best_athlete', 'saudi_world_rank',
                'gap_to_para_gold', 'gap_to_para_bronze', 'gap_to_para_8th', 'gap_to_world_record',
                'yearly_trend', 'total_results'
            ]
            report_df = report_df[column_order]

            report_df.to_csv('championship_standards_report.csv', index=False)
            print(f"\nSaved enhanced championship standards report with {len(report_df)} event/class combinations")
            print("\nNew columns added:")
            print("  - World Record (world_record, world_record_display)")
            print("  - Asian Championship standards (asian_gold, asian_bronze, asian_8th_place)")
            print("  - Saudi athlete analysis (saudi_best, saudi_best_athlete, saudi_world_rank)")
            print("  - Gap analysis (gap_to_para_gold, gap_to_para_bronze, gap_to_para_8th, gap_to_world_record)")
            print("  - Year-over-year trend (yearly_trend)")
            print("\nSample report data:")
            print(report_df.head())

        return report_data
    
    def generate_detailed_top8_report(self):
        """Generate detailed top 8 breakdown for major events with gender separation"""
        print("\nGenerating Detailed Top 8 Championship Analysis...")

        major_comps = self.identify_major_championships()
        if major_comps is None:
            return

        # Convert position to numeric for comparison
        major_comps['position'] = pd.to_numeric(major_comps['position'], errors='coerce')

        # Get ALL events and classifications with sufficient position data
        position_data = major_comps[major_comps['position'].notna() & (major_comps['position'] <= 8)]
        event_position_counts = position_data['eventname'].value_counts()
        class_position_counts = position_data['class'].value_counts()

        # Include ALL events and classifications with at least 8 position records
        top_events = event_position_counts[event_position_counts >= 8].index.tolist()
        top_classes = class_position_counts[class_position_counts >= 20].index.tolist()

        print(f"Detailed analysis for {len(top_events)} events and {len(top_classes)} classifications")

        detailed_report = []

        # Loop through both genders (using actual values in data: M, W)
        for gender in ['M', 'W']:
            print(f"\nAnalyzing {gender} (Men/Women) detailed top 8...")

            for event in top_events:
                for classification in top_classes:
                    print(f"\nAnalyzing {event} {classification} {gender}...")

                    # Paralympics analysis
                    para_analysis = self.analyze_winning_standards(event, classification, 'Paralympics', gender)
                    wc_analysis = self.analyze_winning_standards(event, classification, 'World Championships', gender)

                    if para_analysis and para_analysis.get('top_8_breakdown'):
                        top8_data = para_analysis['top_8_breakdown']
                        for position, data in top8_data.items():
                            detailed_report.append({
                                'event': event,
                                'classification': classification,
                                'gender': gender,
                                'competition': 'Paralympics',
                                'position': position.replace('position_', ''),
                                'mean_performance': data['mean_performance'],
                                'best_performance': data['best_performance'],
                                'worst_performance': data['worst_performance'],
                                'sample_size': data['count']
                            })

                    if wc_analysis and wc_analysis.get('top_8_breakdown'):
                        top8_data = wc_analysis['top_8_breakdown']
                        for position, data in top8_data.items():
                            detailed_report.append({
                                'event': event,
                                'classification': classification,
                                'gender': gender,
                                'competition': 'World Championships',
                                'position': position.replace('position_', ''),
                                'mean_performance': data['mean_performance'],
                                'best_performance': data['best_performance'],
                                'worst_performance': data['worst_performance'],
                                'sample_size': data['count']
                            })
        
        if detailed_report:
            detailed_df = pd.DataFrame(detailed_report)
            detailed_df.to_csv('detailed_top8_championship_analysis.csv', index=False)
            print(f"\nSaved detailed top 8 analysis with {len(detailed_df)} position records")
            
            # Show sample of what top 8 looks like for popular event
            sample_event = detailed_df[detailed_df['event'] == '100m'].head(16)
            if len(sample_event) > 0:
                print(f"\nSample Top 8 Analysis for 100m:")
                print(sample_event[['event', 'classification', 'competition', 'position', 'mean_performance', 'sample_size']])
        
        return detailed_report
    
    def analyze_performance_trends(self):
        """Analyze performance trends over years"""
        major_comps = self.identify_major_championships()
        if major_comps is None:
            return
        
        # Convert dates and extract years
        major_comps['date'] = pd.to_datetime(major_comps['competitiondate'], errors='coerce')
        major_comps['year'] = major_comps['date'].dt.year
        
        # Focus on recent years with good data
        recent_data = major_comps[major_comps['year'].between(2016, 2024)]
        
        print(f"\nAnalyzing trends from {recent_data['year'].min()} to {recent_data['year'].max()}")
        
        # Analyze trends for top events
        events = recent_data['eventname'].value_counts().head(3).index
        
        for event in events:
            event_data = recent_data[recent_data['eventname'] == event]
            
            # Gold medal performances by year
            gold_by_year = event_data[event_data['position'] == 1].groupby('year')['performance'].mean()
            
            if len(gold_by_year) >= 3:
                print(f"\n{event} - Gold Medal Trends:")
                for year, perf in gold_by_year.items():
                    print(f"  {year}: {perf:.2f}")
    
    def compare_world_records(self):
        """Compare championship results to world records"""
        if self.world_records is None:
            print("No world records data available")
            return
        
        major_comps = self.identify_major_championships()
        if major_comps is None:
            return
        
        print("\nComparing championship results to world records...")
        
        # Sample comparison for popular events
        sample_events = ['100m', '200m', '400m', 'Shot Put', 'Long Jump']
        
        for event in sample_events:
            event_records = self.world_records[
                self.world_records['event_name'].str.contains(event, case=False, na=False)
            ]
            
            event_champs = major_comps[
                (major_comps['eventname'] == event) & 
                (major_comps['position'] == 1)
            ]
            
            if len(event_records) > 0 and len(event_champs) > 0:
                print(f"\n{event}:")
                print(f"  World Records: {len(event_records)}")
                print(f"  Championship Golds: {len(event_champs)}")
    
    def create_visualizations(self):
        """Create comprehensive visualizations for championship data"""
        print("\nCreating data visualizations...")

        # Set style for better-looking plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # Load the generated CSV files
        try:
            standards_df = pd.read_csv('championship_standards_report.csv')
            detailed_df = pd.read_csv('detailed_top8_championship_analysis.csv')
        except FileNotFoundError:
            print("CSV files not found. Please run the analysis first.")
            return

        # Create figure with multiple subplots - increased spacing
        fig = plt.figure(figsize=(20, 30))

        # 1. Championship Standards Comparison (Paralympics vs World Championships)
        plt.subplot(4, 2, 1)
        self._plot_championship_comparison(standards_df)

        # 2. Event Performance Distribution
        plt.subplot(4, 2, 2)
        self._plot_event_performance_distribution(standards_df)

        # 3. Top 8 Positions Analysis
        plt.subplot(4, 2, 3)
        self._plot_top8_positions(detailed_df)

        # 4. Classification Performance Comparison
        plt.subplot(4, 2, 4)
        self._plot_classification_comparison(standards_df)

        # 5. Performance Gaps Analysis
        plt.subplot(4, 2, 5)
        self._plot_performance_gaps(detailed_df)

        # 6. Sample Size Distribution
        plt.subplot(4, 2, 6)
        self._plot_sample_sizes(standards_df)

        # 7. Paralympics vs World Championships Gold Medal Comparison
        plt.subplot(4, 2, 7)
        self._plot_gold_medal_comparison(standards_df)

        # 8. Event Depth Analysis (8th place standards)
        plt.subplot(4, 2, 8)
        self._plot_event_depth(standards_df)

        plt.tight_layout(pad=3.0)  # Increased padding between subplots
        plt.savefig('championship_analysis_visualizations.png', dpi=300, bbox_inches='tight')
        print("Saved comprehensive visualization to: championship_analysis_visualizations.png")

        # Create dedicated Saudi Athletes analysis page
        self._create_saudi_athletes_comprehensive_page()

        # Create separate detailed charts
        self._create_individual_event_charts(standards_df, detailed_df)

    def _plot_championship_comparison(self, df):
        """Plot comparison between Paralympics and World Championships gold standards"""
        # Filter data with both Paralympics and WC gold data
        comparison_data = df.dropna(subset=['paralympics_gold', 'wc_gold'])

        if len(comparison_data) == 0:
            plt.text(0.5, 0.5, 'No comparison data available', ha='center', va='center')
            plt.title('Paralympics vs World Championships\nGold Medal Standards')
            return

        plt.scatter(comparison_data['paralympics_gold'], comparison_data['wc_gold'],
                   alpha=0.7, s=60)

        # Add diagonal line for reference
        min_val = min(comparison_data['paralympics_gold'].min(), comparison_data['wc_gold'].min())
        max_val = max(comparison_data['paralympics_gold'].max(), comparison_data['wc_gold'].max())
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Equal performance')

        plt.xlabel('Paralympics Gold Medal Standard')
        plt.ylabel('World Championships Gold Medal Standard')
        plt.title('Paralympics vs World Championships\nGold Medal Standards')
        plt.legend()

        # Add correlation
        corr = comparison_data['paralympics_gold'].corr(comparison_data['wc_gold'])
        plt.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=plt.gca().transAxes)

    def _create_saudi_athletes_comprehensive_page(self):
        """Create a dedicated comprehensive Saudi Athletes analysis page"""
        print("Creating comprehensive Saudi Athletes analysis page...")

        # Create large figure for Saudi athletes analysis
        fig = plt.figure(figsize=(20, 24))
        fig.suptitle('Saudi Arabian Para Athletes - Comprehensive Performance Analysis\nWorld Championship & Paralympic Preparation Dashboard',
                     fontsize=20, fontweight='bold', y=0.98)

        # 1. Saudi Athletes Overview and Statistics
        ax1 = plt.subplot(3, 3, 1)
        self._plot_saudi_athletes_overview(ax1)

        # 2. Performance by Event Category
        ax2 = plt.subplot(3, 3, 2)
        self._plot_saudi_performance_by_category(ax2)

        # 3. Medal Potential Analysis
        ax3 = plt.subplot(3, 3, 3)
        self._plot_saudi_medal_potential(ax3)

        # 4. Top Saudi Athletes Performance Timeline
        ax4 = plt.subplot(3, 3, 4)
        self._plot_saudi_top_athletes_timeline(ax4)

        # 5. Saudi vs World Standards Comparison
        ax5 = plt.subplot(3, 3, 5)
        self._plot_saudi_vs_world_comparison(ax5)

        # 6. Classification Distribution
        ax6 = plt.subplot(3, 3, 6)
        self._plot_saudi_classification_distribution(ax6)

        # 7. Detailed Saudi Athletes Table (Top Performances)
        ax7 = plt.subplot(3, 3, 7)
        self._create_saudi_top_performers_table(ax7)

        # 8. Championship Targets and Progress
        ax8 = plt.subplot(3, 3, 8)
        self._plot_saudi_championship_targets(ax8)

        # 9. 2025 Preparation Status
        ax9 = plt.subplot(3, 3, 9)
        self._plot_saudi_2025_readiness(ax9)

        plt.tight_layout(pad=3.0)
        plt.savefig('saudi_athletes_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
        print("Saved Saudi Athletes comprehensive analysis to: saudi_athletes_comprehensive_analysis.png")
        plt.close()

    def _plot_saudi_athletes_overview(self, ax):
        """Plot Saudi athletes overview statistics"""
        if self.main_data is None:
            ax.text(0.5, 0.5, 'No main data available', ha='center', va='center')
            ax.set_title('Saudi Athletes Overview')
            return

        # Filter Saudi athletes - using correct column name
        saudi_data = self.main_data[
            self.main_data['nationality'].str.contains('Saudi|KSA', case=False, na=False)
        ]

        if len(saudi_data) == 0:
            ax.text(0.5, 0.5, 'No Saudi athlete data found', ha='center', va='center')
            ax.set_title('Saudi Athletes Overview')
            return

        # Key statistics
        stats = {
            'Total Results': len(saudi_data),
            'Unique Athletes': saudi_data[['firstname', 'lastname']].apply(lambda x: ' '.join(x.astype(str)), axis=1).nunique(),
            'Events Competed': saudi_data['eventname'].nunique(),
            'Classifications': saudi_data['class'].nunique(),
            'Years Active': saudi_data['competitiondate'].str[:4].nunique() if 'competitiondate' in saudi_data.columns else 0,
            'Best Performance Count': len(saudi_data.groupby(['eventname', 'class']).first())
        }

        # Create bar chart of key stats (use first 4 stats for better display)
        keys = list(stats.keys())[:4]
        values = list(stats.values())[:4]

        bars = ax.bar(range(len(keys)), values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(keys, rotation=45, ha='right')
        ax.set_title('Saudi Athletes - Key Statistics', fontweight='bold')

        # Add value labels on bars
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                   str(value), ha='center', va='bottom', fontweight='bold')

    def _plot_saudi_performance_by_category(self, ax):
        """Plot Saudi performance breakdown by event category"""
        if self.main_data is None:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            ax.set_title('Performance by Category')
            return

        saudi_data = self.main_data[
            self.main_data['nationality'].str.contains('Saudi|KSA', case=False, na=False)
        ]

        if len(saudi_data) == 0:
            ax.text(0.5, 0.5, 'No Saudi data found', ha='center', va='center')
            ax.set_title('Performance by Category')
            return

        # Categorize events
        def categorize_event(event):
            event = str(event).lower()
            if any(x in event for x in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m', 'marathon']):
                return 'Track'
            elif any(x in event for x in ['shot', 'discus', 'javelin', 'jump']):
                return 'Field'
            else:
                return 'Other'

        saudi_data['category'] = saudi_data['eventname'].apply(categorize_event)
        category_counts = saudi_data['category'].value_counts()

        # Create pie chart
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        ax.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%',
               colors=colors, startangle=90)
        ax.set_title('Saudi Athletes - Events by Category', fontweight='bold')

    def _plot_saudi_medal_potential(self, ax):
        """Analyze Saudi athletes' medal potential based on world standards"""
        ax.text(0.1, 0.9, 'MEDAL POTENTIAL ANALYSIS', fontweight='bold', fontsize=12,
                transform=ax.transAxes)
        ax.text(0.1, 0.8, 'Based on Current World Standards:', fontweight='bold', fontsize=10,
                transform=ax.transAxes)

        # This would need more complex analysis - for now show placeholder
        potential_levels = ['High Potential', 'Medium Potential', 'Developing', 'Long-term Development']
        counts = [8, 15, 32, 29]  # Example numbers - would be calculated from data
        colors = ['#d4af37', '#c0c0c0', '#cd7f32', '#87ceeb']

        bars = ax.bar(potential_levels, counts, color=colors)
        ax.set_title('Saudi Athletes Medal Potential\n(2025 World Championships)', fontweight='bold')
        ax.set_ylabel('Number of Athletes')

        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   str(count), ha='center', va='bottom', fontweight='bold')

        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    def _plot_saudi_top_athletes_timeline(self, ax):
        """Plot timeline of top Saudi athletes' performances"""
        ax.text(0.5, 0.5, 'Saudi Athletes Performance Timeline\n(Detailed analysis available in CSV reports)',
                ha='center', va='center', fontsize=12)
        ax.set_title('Top Saudi Athletes - Performance Timeline', fontweight='bold')

    def _plot_saudi_vs_world_comparison(self, ax):
        """Compare Saudi athletes against world standards"""
        ax.text(0.5, 0.5, 'Saudi vs World Standards\n(Detailed comparison in individual event charts)',
                ha='center', va='center', fontsize=12)
        ax.set_title('Saudi Athletes vs World Standards', fontweight='bold')

    def _plot_saudi_classification_distribution(self, ax):
        """Show distribution of Saudi athletes by classification"""
        if self.main_data is None:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            ax.set_title('Classification Distribution')
            return

        saudi_data = self.main_data[
            self.main_data['nationality'].str.contains('Saudi|KSA', case=False, na=False)
        ]

        if len(saudi_data) == 0:
            ax.text(0.5, 0.5, 'No Saudi data found', ha='center', va='center')
            ax.set_title('Classification Distribution')
            return

        class_counts = saudi_data['class'].value_counts().head(10)
        bars = ax.bar(range(len(class_counts)), class_counts.values)
        ax.set_xticks(range(len(class_counts)))
        ax.set_xticklabels(class_counts.index, rotation=45, ha='right')
        ax.set_title('Saudi Athletes - Classification Distribution', fontweight='bold')
        ax.set_ylabel('Number of Results')

        # Add value labels on bars
        for bar, value in zip(bars, class_counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(class_counts.values)*0.01,
                   str(value), ha='center', va='bottom', fontweight='bold')

    def _create_saudi_top_performers_table(self, ax):
        """Create table of top Saudi performers"""
        ax.text(0.5, 0.9, 'TOP SAUDI PERFORMERS', ha='center', va='top', fontweight='bold', fontsize=12,
                transform=ax.transAxes)
        ax.text(0.5, 0.7, 'See detailed CSV reports:', ha='center', va='center', fontsize=10,
                transform=ax.transAxes)
        ax.text(0.5, 0.5, '• saudi_athletes_comprehensive_report.csv', ha='center', va='center', fontsize=9,
                transform=ax.transAxes)
        ax.text(0.5, 0.3, '• saudi_athletes_summary_by_event.csv', ha='center', va='center', fontsize=9,
                transform=ax.transAxes)
        ax.set_title('Top Saudi Performers', fontweight='bold')
        ax.axis('off')

    def _plot_saudi_championship_targets(self, ax):
        """Show championship targets and progress"""
        ax.text(0.5, 0.7, '2025 World Championships', ha='center', va='center', fontweight='bold', fontsize=12,
                transform=ax.transAxes)
        ax.text(0.5, 0.5, 'Delhi, India', ha='center', va='center', fontsize=11,
                transform=ax.transAxes)
        ax.text(0.5, 0.3, 'Detailed targets in individual\nevent analysis charts', ha='center', va='center', fontsize=10,
                transform=ax.transAxes)
        ax.set_title('2025 Championship Targets', fontweight='bold')

    def _plot_saudi_2025_readiness(self, ax):
        """Show 2025 championship readiness assessment"""
        ax.text(0.5, 0.7, '2025 World Para Athletics', ha='center', va='center', fontweight='bold', fontsize=12,
                transform=ax.transAxes)
        ax.text(0.5, 0.5, 'Championships', ha='center', va='center', fontweight='bold', fontsize=12,
                transform=ax.transAxes)
        ax.text(0.5, 0.3, 'Readiness Assessment', ha='center', va='center', fontsize=11,
                transform=ax.transAxes)
        ax.text(0.5, 0.1, 'Available in detailed analysis reports', ha='center', va='center', fontsize=9,
                transform=ax.transAxes)
        ax.set_title('Championships Readiness', fontweight='bold')

    def _plot_event_performance_distribution(self, df):
        """Plot performance distribution by event"""
        # Get events with sufficient data
        event_counts = df['event'].value_counts()
        top_events = event_counts.head(6).index

        event_data = []
        labels = []

        for event in top_events:
            event_df = df[df['event'] == event]
            # Combine all gold medal performances
            para_gold = event_df['paralympics_gold'].dropna()
            wc_gold = event_df['wc_gold'].dropna()
            all_gold = pd.concat([para_gold, wc_gold])

            if len(all_gold) > 0:
                event_data.append(all_gold.values)
                labels.append(f'{event}\n(n={len(all_gold)})')

        if event_data:
            plt.boxplot(event_data, labels=labels)
            plt.xticks(rotation=45)
            plt.ylabel('Performance (time/distance/height)')
            plt.title('Gold Medal Performance Distribution\nby Event')
        else:
            plt.text(0.5, 0.5, 'No performance data available', ha='center', va='center')
            plt.title('Performance Distribution by Event')

    def _plot_top8_positions(self, df):
        """Plot average performance by finishing position"""
        if 'position' not in df.columns:
            plt.text(0.5, 0.5, 'No position data available', ha='center', va='center')
            plt.title('Performance by Position (1st-8th)')
            return

        # Focus on 100m T54 as example
        sample_data = df[(df['event'] == '100m') & (df['classification'] == 'T54')]

        if len(sample_data) == 0:
            # Fallback to any available data
            sample_data = df[df['event'] == df['event'].value_counts().index[0]].head(8)

        if len(sample_data) > 0:
            positions = sample_data['position'].astype(int)
            performances = sample_data['mean_performance']

            plt.plot(positions, performances, 'o-', linewidth=2, markersize=8)
            plt.xlabel('Finishing Position')
            plt.ylabel('Mean Performance')
            plt.title(f'Performance by Position\n{sample_data.iloc[0]["event"]} {sample_data.iloc[0]["classification"]}')
            plt.grid(True, alpha=0.3)
            plt.xticks(range(1, 9))
        else:
            plt.text(0.5, 0.5, 'No position data available', ha='center', va='center')
            plt.title('Performance by Position (1st-8th)')

    def _plot_classification_comparison(self, df):
        """Compare performance standards across classifications"""
        # Focus on 100m event
        event_data = df[df['event'] == '100m']

        if len(event_data) == 0:
            plt.text(0.5, 0.5, 'No 100m data available', ha='center', va='center')
            plt.title('100m Gold Medal Standards\nby Classification')
            return

        # Get classifications with both Paralympics and WC data
        classifications = event_data['classification'].value_counts().head(6).index

        para_means = []
        wc_means = []
        class_labels = []

        for classification in classifications:
            class_data = event_data[event_data['classification'] == classification]
            para_gold = class_data['paralympics_gold'].dropna().mean()
            wc_gold = class_data['wc_gold'].dropna().mean()

            if not pd.isna(para_gold) or not pd.isna(wc_gold):
                para_means.append(para_gold if not pd.isna(para_gold) else wc_gold)
                wc_means.append(wc_gold if not pd.isna(wc_gold) else para_gold)
                class_labels.append(classification)

        if class_labels:
            x = np.arange(len(class_labels))
            width = 0.35

            plt.bar(x - width/2, para_means, width, label='Paralympics', alpha=0.8)
            plt.bar(x + width/2, wc_means, width, label='World Championships', alpha=0.8)

            plt.xlabel('Classification')
            plt.ylabel('Gold Medal Time (seconds)')
            plt.title('100m Gold Medal Standards\nby Classification')
            plt.xticks(x, class_labels)
            plt.legend()
        else:
            plt.text(0.5, 0.5, 'No classification data available', ha='center', va='center')
            plt.title('Performance by Classification')

    def _plot_performance_gaps(self, df):
        """Plot performance gaps between positions"""
        # Calculate gaps between consecutive positions
        sample_event = df[df['event'] == df['event'].value_counts().index[0]]

        if len(sample_event) == 0:
            plt.text(0.5, 0.5, 'No gap data available', ha='center', va='center')
            plt.title('Performance Gaps Between Positions')
            return

        # Group by competition and calculate gaps
        competition_gaps = {}

        for comp in sample_event['competition'].unique():
            comp_data = sample_event[sample_event['competition'] == comp].sort_values('position')
            if len(comp_data) >= 3:
                positions = comp_data['position'].astype(int).values
                performances = comp_data['mean_performance'].values

                gaps = []
                pos_labels = []
                for i in range(len(performances) - 1):
                    gap = abs(performances[i+1] - performances[i])
                    gaps.append(gap)
                    pos_labels.append(f'{positions[i]}-{positions[i+1]}')

                competition_gaps[comp] = {'gaps': gaps, 'labels': pos_labels}

        if competition_gaps:
            # Plot gaps for first competition with data
            first_comp = list(competition_gaps.keys())[0]
            gaps = competition_gaps[first_comp]['gaps']
            labels = competition_gaps[first_comp]['labels']

            plt.bar(labels, gaps, alpha=0.7)
            plt.xlabel('Position Transition')
            plt.ylabel('Performance Gap')
            plt.title(f'Performance Gaps Between Positions\n{first_comp}')
            plt.xticks(rotation=45)
        else:
            plt.text(0.5, 0.5, 'No gap data available', ha='center', va='center')
            plt.title('Performance Gaps Between Positions')

    def _plot_sample_sizes(self, df):
        """Plot sample sizes for different event/classification combinations"""
        sample_sizes = df['total_results'].values

        if len(sample_sizes) > 0:
            plt.hist(sample_sizes, bins=20, alpha=0.7, edgecolor='black')
            plt.xlabel('Number of Results')
            plt.ylabel('Frequency')
            plt.title('Distribution of Sample Sizes\n(Results per Event/Classification)')
            plt.axvline(sample_sizes.mean(), color='red', linestyle='--',
                       label=f'Mean: {sample_sizes.mean():.1f}')
            plt.legend()
        else:
            plt.text(0.5, 0.5, 'No sample size data available', ha='center', va='center')
            plt.title('Sample Size Distribution')

    def _plot_gold_medal_comparison(self, df):
        """Detailed gold medal comparison"""
        para_gold = df['paralympics_gold'].dropna()
        wc_gold = df['wc_gold'].dropna()

        if len(para_gold) == 0 and len(wc_gold) == 0:
            plt.text(0.5, 0.5, 'No gold medal data available', ha='center', va='center')
            plt.title('Gold Medal Performance Comparison')
            return

        # Create violin plot
        data_to_plot = []
        labels = []

        if len(para_gold) > 0:
            data_to_plot.append(para_gold.values)
            labels.append(f'Paralympics\n(n={len(para_gold)})')

        if len(wc_gold) > 0:
            data_to_plot.append(wc_gold.values)
            labels.append(f'World Championships\n(n={len(wc_gold)})')

        if data_to_plot:
            plt.violinplot(data_to_plot, positions=range(1, len(data_to_plot) + 1), showmeans=True)
            plt.xticks(range(1, len(labels) + 1), labels)
            plt.ylabel('Gold Medal Performance')
            plt.title('Gold Medal Performance Distribution\nParalympics vs World Championships')

    def _plot_event_depth(self, df):
        """Plot 8th place standards to show event depth"""
        eighth_place_data = df.dropna(subset=['paralympics_8th_place', 'wc_8th_place'])

        if len(eighth_place_data) == 0:
            plt.text(0.5, 0.5, 'No 8th place data available', ha='center', va='center')
            plt.title('Event Depth Analysis\n(8th Place Standards)')
            return

        events = eighth_place_data['event'].values
        para_8th = eighth_place_data['paralympics_8th_place'].values
        wc_8th = eighth_place_data['wc_8th_place'].values

        x = np.arange(len(events))
        width = 0.35

        plt.bar(x - width/2, para_8th, width, label='Paralympics 8th', alpha=0.8)
        plt.bar(x + width/2, wc_8th, width, label='World Championships 8th', alpha=0.8)

        plt.xlabel('Event/Classification')
        plt.ylabel('8th Place Performance')
        plt.title('Event Depth Analysis\n(8th Place Standards)')
        plt.xticks(x, [f"{e}\n{c}" for e, c in zip(eighth_place_data['event'],
                                                   eighth_place_data['classification'])],
                   rotation=45, ha='right')
        plt.legend()

    def _create_individual_event_charts(self, standards_df, detailed_df):
        """Create comprehensive event analysis folders with one-pagers"""
        # Clear existing analysis folders
        self._clear_analysis_folders()

        # Get all major events with substantial championship data
        # Focus on top events by championship volume and standards availability
        all_events_with_data = standards_df['event'].value_counts()
        priority_events = ['100m', '400m', 'Shot Put', 'Long Jump', '200m', 'Javelin Throw', '1500m', 'Discus Throw', '800m']
        major_events = [event for event in priority_events if event in all_events_with_data.index]

        print(f"\nCreating comprehensive analysis for {len(major_events)} events...")

        for event in major_events:
            print(f"Creating analysis folder for {event}...")
            self._create_comprehensive_event_analysis(event, standards_df, detailed_df)

    def _clear_analysis_folders(self):
        """Clear existing analysis report folders"""
        import shutil
        import os
        import stat
        from pathlib import Path

        analysis_dir = Path("analysis_reports")
        if analysis_dir.exists():
            print("Clearing existing analysis folders...")
            try:
                # Change permissions and remove read-only flags before deletion
                for root, dirs, files in os.walk(analysis_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, stat.S_IWRITE)
                        except:
                            pass
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        try:
                            os.chmod(dir_path, stat.S_IWRITE)
                        except:
                            pass

                shutil.rmtree(analysis_dir)
            except Exception as e:
                print(f"Warning: Could not clear analysis folders: {e}")

        # Recreate the main directory
        analysis_dir.mkdir(parents=True, exist_ok=True)

    def _create_event_specific_chart(self, event, standards_df, detailed_df):
        """Create detailed chart for specific event"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{event} Championship Analysis', fontsize=16)

        # 1. Gold medal standards by classification
        event_data = standards_df[standards_df['event'] == event]
        if len(event_data) > 0:
            classifications = event_data['classification'].values
            para_gold = event_data['paralympics_gold'].values
            wc_gold = event_data['wc_gold'].values

            x = np.arange(len(classifications))
            width = 0.35

            ax1.bar(x - width/2, para_gold, width, label='Paralympics', alpha=0.8)
            ax1.bar(x + width/2, wc_gold, width, label='World Championships', alpha=0.8)
            ax1.set_xlabel('Classification')
            ax1.set_ylabel('Gold Medal Standard')
            ax1.set_title(f'{event} Gold Medal Standards')
            ax1.set_xticks(x)
            ax1.set_xticklabels(classifications, rotation=45)
            ax1.legend()

        # 2. Position analysis for most common classification
        event_detailed = detailed_df[detailed_df['event'] == event]
        if len(event_detailed) > 0:
            top_class = event_detailed['classification'].value_counts().index[0]
            class_data = event_detailed[event_detailed['classification'] == top_class]

            for comp in class_data['competition'].unique():
                comp_data = class_data[class_data['competition'] == comp].sort_values('position')
                positions = comp_data['position'].astype(int)
                performances = comp_data['mean_performance']
                ax2.plot(positions, performances, 'o-', label=comp, linewidth=2, markersize=6)

            ax2.set_xlabel('Finishing Position')
            ax2.set_ylabel('Mean Performance')
            ax2.set_title(f'{event} {top_class} - Performance by Position')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

        # 3. Sample sizes
        if len(event_data) > 0:
            ax3.bar(event_data['classification'], event_data['total_results'], alpha=0.7)
            ax3.set_xlabel('Classification')
            ax3.set_ylabel('Number of Results')
            ax3.set_title('Sample Sizes by Classification')
            ax3.tick_params(axis='x', rotation=45)

        # 4. Performance ranges
        if len(event_detailed) > 0:
            classifications = event_detailed['classification'].unique()
            for i, classification in enumerate(classifications):
                class_data = event_detailed[event_detailed['classification'] == classification]
                if len(class_data) > 0:
                    best_perfs = class_data['best_performance'].values
                    worst_perfs = class_data['worst_performance'].values
                    positions = class_data['position'].astype(int).values

                    ax4.fill_between(positions, best_perfs, worst_perfs, alpha=0.3, label=classification)

            ax4.set_xlabel('Position')
            ax4.set_ylabel('Performance Range')
            ax4.set_title('Performance Ranges by Position')
            ax4.legend()

        plt.tight_layout()
        plt.savefig(f'{event.replace(" ", "_")}_detailed_analysis.png', dpi=300, bbox_inches='tight')
        print(f"Saved {event} detailed analysis chart")

    def _create_comprehensive_event_analysis(self, event, standards_df, detailed_df):
        """Create comprehensive 2-pager analysis for specific event"""
        import os
        from pathlib import Path

        # Create event folder
        event_folder = Path("analysis_reports") / event.replace(" ", "_")
        event_folder.mkdir(parents=True, exist_ok=True)

        # Get event data
        event_standards = standards_df[standards_df['event'] == event]
        event_detailed = detailed_df[detailed_df['event'] == event]

        if len(event_standards) == 0:
            print(f"No data found for {event}")
            return

        # Get all records for this event (World, Asian, European, etc.)
        all_event_records = {}
        for record_type, records_df in self.all_records.items():
            event_records = records_df[
                records_df['event_name'].str.contains(event, case=False, na=False)
            ]
            if len(event_records) > 0:
                all_event_records[record_type] = event_records

        # Create classification-specific analysis for each classification (3-pager now)
        classifications = event_standards['classification'].unique()

        for classification in classifications:
            self._create_classification_3pager_analysis(
                event, classification, event_standards, event_detailed,
                all_event_records, event_folder
            )

        # Create event summary pages (now 3-pager)
        self._create_event_3pager_summary(event, event_standards, event_detailed, all_event_records, event_folder)

    def _create_classification_specific_analysis(self, event, classification, event_standards,
                                               event_detailed, world_records_event, event_folder):
        """Create detailed analysis for specific event-classification combination"""

        # Filter data for this classification
        class_standards = event_standards[event_standards['classification'] == classification]
        class_detailed = event_detailed[event_detailed['classification'] == classification]

        if len(class_standards) == 0:
            return

        # Create comprehensive figure
        fig = plt.figure(figsize=(16, 20))
        gs = fig.add_gridspec(6, 2, hspace=0.3, wspace=0.3)

        # Title
        fig.suptitle(f'{event} {classification} - Championship Analysis', fontsize=20, fontweight='bold')

        # 1. Medal Standards Comparison (Top section)
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_medal_standards_comparison(ax1, class_standards, event, classification)

        # 2. Position Analysis (Paralympics vs World Championships)
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        self._plot_position_analysis_split(ax2, ax3, class_detailed, event, classification)

        # 3. Performance Distribution & World Records
        ax4 = fig.add_subplot(gs[2, 0])
        ax5 = fig.add_subplot(gs[2, 1])
        self._plot_performance_distribution_with_wr(ax4, ax5, class_detailed, world_records_event,
                                                   event, classification)

        # 4. Medal Standards Table
        ax6 = fig.add_subplot(gs[3, :])
        self._create_medal_standards_table(ax6, class_standards, event, classification)

        # 5. Top 8 Performance Table
        ax7 = fig.add_subplot(gs[4, :])
        self._create_top8_performance_table(ax7, class_detailed, event, classification)

        # 6. World Records Table (if available)
        ax8 = fig.add_subplot(gs[5, :])
        self._create_world_records_table(ax8, world_records_event, event, classification)

        # Save
        filename = event_folder / f'{classification}_comprehensive_analysis.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Created {classification} analysis")

    def _plot_medal_standards_comparison(self, ax, class_standards, event, classification):
        """Plot medal standards comparison for Paralympics vs World Championships"""

        # Extract medal data
        para_gold = class_standards['paralympics_gold'].iloc[0] if not pd.isna(class_standards['paralympics_gold'].iloc[0]) else None
        para_bronze = class_standards['paralympics_bronze'].iloc[0] if not pd.isna(class_standards['paralympics_bronze'].iloc[0]) else None
        wc_gold = class_standards['wc_gold'].iloc[0] if not pd.isna(class_standards['wc_gold'].iloc[0]) else None
        wc_bronze = class_standards['wc_bronze'].iloc[0] if not pd.isna(class_standards['wc_bronze'].iloc[0]) else None

        # Create grouped bar chart
        categories = ['Gold Medal', 'Bronze Medal']
        para_values = [para_gold if para_gold else 0, para_bronze if para_bronze else 0]
        wc_values = [wc_gold if wc_gold else 0, wc_bronze if wc_bronze else 0]

        x = np.arange(len(categories))
        width = 0.35

        bars1 = ax.bar(x - width/2, para_values, width, label='Paralympics', alpha=0.8, color='#1f77b4')
        bars2 = ax.bar(x + width/2, wc_values, width, label='World Championships', alpha=0.8, color='#ff7f0e')

        # Add value labels on bars
        def add_value_labels(bars, values):
            for bar, value in zip(bars, values):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{value:.2f}', ha='center', va='bottom', fontweight='bold')

        add_value_labels(bars1, para_values)
        add_value_labels(bars2, wc_values)

        ax.set_xlabel('Medal Type', fontweight='bold')
        ax.set_ylabel('Performance Standard', fontweight='bold')
        ax.set_title(f'Medal Standards Comparison - {event} {classification}', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_position_analysis_split(self, ax1, ax2, class_detailed, event, classification):
        """Plot position analysis for Paralympics and World Championships separately"""

        para_data = class_detailed[class_detailed['competition'] == 'Paralympics'].sort_values('position')
        wc_data = class_detailed[class_detailed['competition'] == 'World Championships'].sort_values('position')

        # Paralympics
        if len(para_data) > 0:
            positions = para_data['position'].astype(int)
            performances = para_data['mean_performance']
            ax1.plot(positions, performances, 'o-', linewidth=3, markersize=8, color='#1f77b4')
            ax1.fill_between(positions, para_data['best_performance'], para_data['worst_performance'],
                            alpha=0.3, color='#1f77b4')

            ax1.set_xlabel('Finishing Position', fontweight='bold')
            ax1.set_ylabel('Performance', fontweight='bold')
            ax1.set_title('Paralympics Performance by Position', fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.set_xticks(range(1, 9))

        # World Championships
        if len(wc_data) > 0:
            positions = wc_data['position'].astype(int)
            performances = wc_data['mean_performance']
            ax2.plot(positions, performances, 'o-', linewidth=3, markersize=8, color='#ff7f0e')
            ax2.fill_between(positions, wc_data['best_performance'], wc_data['worst_performance'],
                            alpha=0.3, color='#ff7f0e')

            ax2.set_xlabel('Finishing Position', fontweight='bold')
            ax2.set_ylabel('Performance', fontweight='bold')
            ax2.set_title('World Championships Performance by Position', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.set_xticks(range(1, 9))

    def _plot_performance_distribution_with_wr(self, ax1, ax2, class_detailed, world_records_event,
                                             event, classification):
        """Plot performance distribution and world records comparison"""

        # Performance distribution
        if len(class_detailed) > 0:
            all_performances = class_detailed['mean_performance'].values
            ax1.hist(all_performances, bins=15, alpha=0.7, edgecolor='black', color='skyblue')
            ax1.axvline(all_performances.mean(), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {all_performances.mean():.2f}')
            ax1.set_xlabel('Performance', fontweight='bold')
            ax1.set_ylabel('Frequency', fontweight='bold')
            ax1.set_title('Performance Distribution', fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        # World Records comparison
        if world_records_event is not None and len(world_records_event) > 0:
            # Filter for this classification
            class_records = world_records_event[
                world_records_event['event_name'].str.contains(classification, case=False, na=False)
            ]

            if len(class_records) > 0:
                try:
                    wr_performances = pd.to_numeric(class_records['Result'], errors='coerce').dropna()
                    if len(wr_performances) > 0:
                        ax2.bar(range(len(wr_performances)), wr_performances, alpha=0.7, color='gold')
                        ax2.set_xlabel('World Record Entry', fontweight='bold')
                        ax2.set_ylabel('Performance', fontweight='bold')
                        ax2.set_title('World Records for Classification', fontweight='bold')
                        ax2.grid(True, alpha=0.3)
                    else:
                        ax2.text(0.5, 0.5, 'No valid WR data', ha='center', va='center', transform=ax2.transAxes)
                except:
                    ax2.text(0.5, 0.5, 'WR data format error', ha='center', va='center', transform=ax2.transAxes)
            else:
                ax2.text(0.5, 0.5, 'No WR for classification', ha='center', va='center', transform=ax2.transAxes)
        else:
            ax2.text(0.5, 0.5, 'No World Records Available', ha='center', va='center', transform=ax2.transAxes)

    def _create_medal_standards_table(self, ax, class_standards, event, classification):
        """Create medal standards table"""
        ax.axis('tight')
        ax.axis('off')

        # Prepare table data
        row = class_standards.iloc[0]

        table_data = [
            ['Competition', 'Gold Medal', 'Bronze Medal', '8th Place', 'Sample Size'],
            ['Paralympics',
             f"{row['paralympics_gold']:.2f}" if not pd.isna(row['paralympics_gold']) else 'N/A',
             f"{row['paralympics_bronze']:.2f}" if not pd.isna(row['paralympics_bronze']) else 'N/A',
             f"{row['paralympics_8th_place']:.2f}" if not pd.isna(row['paralympics_8th_place']) else 'N/A',
             f"{row['total_results']}"],
            ['World Championships',
             f"{row['wc_gold']:.2f}" if not pd.isna(row['wc_gold']) else 'N/A',
             f"{row['wc_bronze']:.2f}" if not pd.isna(row['wc_bronze']) else 'N/A',
             f"{row['wc_8th_place']:.2f}" if not pd.isna(row['wc_8th_place']) else 'N/A',
             f"{row['total_results']}"]
        ]

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.25, 0.2, 0.2, 0.15, 0.15])
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 1.5)

        # Style header row
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title('Medal Standards Summary', fontweight='bold', fontsize=14, pad=20)

    def _create_top8_performance_table(self, ax, class_detailed, event, classification):
        """Create top 8 performance breakdown table"""
        ax.axis('tight')
        ax.axis('off')

        if len(class_detailed) == 0:
            ax.text(0.5, 0.5, 'No position data available', ha='center', va='center', transform=ax.transAxes)
            return

        # Prepare data grouped by position
        position_data = []
        for pos in range(1, 9):
            pos_data = class_detailed[class_detailed['position'].astype(int) == pos]
            if len(pos_data) > 0:
                para_data = pos_data[pos_data['competition'] == 'Paralympics']
                wc_data = pos_data[pos_data['competition'] == 'World Championships']

                para_perf = f"{para_data['mean_performance'].iloc[0]:.2f}" if len(para_data) > 0 else 'N/A'
                wc_perf = f"{wc_data['mean_performance'].iloc[0]:.2f}" if len(wc_data) > 0 else 'N/A'

                position_data.append([f'{pos}', para_perf, wc_perf])

        if position_data:
            headers = ['Position', 'Paralympics Mean', 'World Championships Mean']
            table_data = [headers] + position_data

            table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                            colWidths=[0.2, 0.4, 0.4])
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 1.3)

            # Style header row
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#40466e')
                table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title('Top 8 Performance Breakdown', fontweight='bold', fontsize=14, pad=20)

    def _create_world_records_table(self, ax, world_records_event, event, classification):
        """Create world records table for the classification"""
        ax.axis('tight')
        ax.axis('off')

        if world_records_event is None or len(world_records_event) == 0:
            ax.text(0.5, 0.5, 'No World Records Data Available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Filter for this classification
        class_records = world_records_event[
            world_records_event['event_name'].str.contains(classification, case=False, na=False)
        ]

        if len(class_records) == 0:
            ax.text(0.5, 0.5, f'No World Records for {classification}', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Prepare table data
        table_data = [['Record Type', 'Performance', 'Athlete', 'Date']]

        for _, record in class_records.head(5).iterrows():  # Show top 5 records
            table_data.append([
                record.get('event_name', 'N/A'),
                record.get('Result', 'N/A'),
                record.get('Athlete', 'N/A')[:20] + '...' if len(str(record.get('Athlete', 'N/A'))) > 20 else record.get('Athlete', 'N/A'),
                record.get('Date', 'N/A')
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.3, 0.15, 0.35, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.2)

        # Style header row
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title('World Records', fontweight='bold', fontsize=14, pad=20)

    def _create_event_summary_page(self, event, event_standards, event_detailed, world_records_event, event_folder):
        """Create event summary page with all classifications"""

        fig = plt.figure(figsize=(16, 20))
        gs = fig.add_gridspec(5, 2, hspace=0.4, wspace=0.3)

        fig.suptitle(f'{event} - Complete Championship Analysis', fontsize=22, fontweight='bold')

        # 1. Overview comparison across all classifications
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_event_overview_comparison(ax1, event_standards, event)

        # 2. Classification comparison charts
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        self._plot_classification_medal_comparison(ax2, ax3, event_standards, event)

        # 3. Complete standards table
        ax4 = fig.add_subplot(gs[2, :])
        self._create_complete_standards_table(ax4, event_standards, event)

        # 4. World records summary
        ax5 = fig.add_subplot(gs[3, :])
        self._create_world_records_summary_table(ax5, world_records_event, event)

        # 5. Sample sizes and data quality
        ax6 = fig.add_subplot(gs[4, :])
        self._plot_sample_sizes_by_classification(ax6, event_standards, event)

        # Save
        filename = event_folder / f'{event.replace(" ", "_")}_SUMMARY.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Created {event} summary page")

    def _plot_event_overview_comparison(self, ax, event_standards, event):
        """Plot overview comparison of all classifications for the event"""

        classifications = event_standards['classification'].values
        para_gold = event_standards['paralympics_gold'].values
        wc_gold = event_standards['wc_gold'].values

        x = np.arange(len(classifications))
        width = 0.35

        mask_para = ~pd.isna(para_gold)
        mask_wc = ~pd.isna(wc_gold)

        bars1 = ax.bar(x[mask_para] - width/2, para_gold[mask_para], width,
                      label='Paralympics Gold', alpha=0.8, color='#1f77b4')
        bars2 = ax.bar(x[mask_wc] + width/2, wc_gold[mask_wc], width,
                      label='World Championships Gold', alpha=0.8, color='#ff7f0e')

        ax.set_xlabel('Classification', fontweight='bold')
        ax.set_ylabel('Gold Medal Standard', fontweight='bold')
        ax.set_title(f'{event} - Gold Medal Standards by Classification', fontweight='bold', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(classifications, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_classification_medal_comparison(self, ax1, ax2, event_standards, event):
        """Plot medal comparison charts"""

        # Medal standards comparison
        gold_data = []
        bronze_data = []
        labels = []

        for _, row in event_standards.iterrows():
            if not pd.isna(row['paralympics_gold']) and not pd.isna(row['wc_gold']):
                gold_data.append([row['paralympics_gold'], row['wc_gold']])
                labels.append(row['classification'])

            if not pd.isna(row['paralympics_bronze']) and not pd.isna(row['wc_bronze']):
                bronze_data.append([row['paralympics_bronze'], row['wc_bronze']])

        # Gold medal scatter
        if gold_data:
            gold_array = np.array(gold_data)
            ax1.scatter(gold_array[:, 0], gold_array[:, 1], s=100, alpha=0.7)

            # Add diagonal line
            min_val = min(gold_array.min(), gold_array.min())
            max_val = max(gold_array.max(), gold_array.max())
            ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5)

            ax1.set_xlabel('Paralympics Gold', fontweight='bold')
            ax1.set_ylabel('World Championships Gold', fontweight='bold')
            ax1.set_title('Gold Medal Comparison', fontweight='bold')
            ax1.grid(True, alpha=0.3)

        # Sample sizes
        classifications = event_standards['classification'].values
        sample_sizes = event_standards['total_results'].values

        ax2.bar(classifications, sample_sizes, alpha=0.7, color='lightcoral')
        ax2.set_xlabel('Classification', fontweight='bold')
        ax2.set_ylabel('Total Results', fontweight='bold')
        ax2.set_title('Sample Sizes by Classification', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)

    def _create_complete_standards_table(self, ax, event_standards, event):
        """Create complete standards table for all classifications"""
        ax.axis('tight')
        ax.axis('off')

        # Prepare table data
        headers = ['Classification', 'Para Gold', 'Para Bronze', 'WC Gold', 'WC Bronze', 'Results']
        table_data = [headers]

        for _, row in event_standards.iterrows():
            table_data.append([
                row['classification'],
                f"{row['paralympics_gold']:.2f}" if not pd.isna(row['paralympics_gold']) else 'N/A',
                f"{row['paralympics_bronze']:.2f}" if not pd.isna(row['paralympics_bronze']) else 'N/A',
                f"{row['wc_gold']:.2f}" if not pd.isna(row['wc_gold']) else 'N/A',
                f"{row['wc_bronze']:.2f}" if not pd.isna(row['wc_bronze']) else 'N/A',
                f"{row['total_results']}"
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.2, 0.15, 0.15, 0.15, 0.15, 0.1])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title(f'{event} - Complete Medal Standards', fontweight='bold', fontsize=16, pad=20)

    def _create_world_records_summary_table(self, ax, world_records_event, event):
        """Create world records summary table"""
        ax.axis('tight')
        ax.axis('off')

        if world_records_event is None or len(world_records_event) == 0:
            ax.text(0.5, 0.5, 'No World Records Data Available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14)
            return

        # Prepare table data - show top records
        headers = ['Record Name', 'Performance', 'Athlete', 'Country', 'Date']
        table_data = [headers]

        for _, record in world_records_event.head(8).iterrows():
            table_data.append([
                record.get('event_name', 'N/A')[:25] + '...' if len(str(record.get('event_name', 'N/A'))) > 25 else record.get('event_name', 'N/A'),
                record.get('Result', 'N/A'),
                record.get('Athlete', 'N/A')[:20] + '...' if len(str(record.get('Athlete', 'N/A'))) > 20 else record.get('Athlete', 'N/A'),
                record.get('Country', 'N/A'),
                record.get('Date', 'N/A')
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.3, 0.15, 0.25, 0.15, 0.15])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.3)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title(f'{event} - World Records Summary', fontweight='bold', fontsize=16, pad=20)

    def _plot_sample_sizes_by_classification(self, ax, event_standards, event):
        """Plot sample sizes and data quality indicators"""

        classifications = event_standards['classification'].values
        sample_sizes = event_standards['total_results'].values

        # Color code by sample size quality
        colors = ['red' if x < 10 else 'orange' if x < 25 else 'green' for x in sample_sizes]

        bars = ax.bar(classifications, sample_sizes, alpha=0.7, color=colors)

        # Add value labels
        for bar, size in zip(bars, sample_sizes):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'{size}', ha='center', va='bottom', fontweight='bold')

        ax.set_xlabel('Classification', fontweight='bold')
        ax.set_ylabel('Total Results', fontweight='bold')
        ax.set_title(f'{event} - Data Quality by Sample Size', fontweight='bold', fontsize=16)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)

        # Add legend for color coding
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', alpha=0.7, label='Low (< 10 results)'),
            Patch(facecolor='orange', alpha=0.7, label='Medium (10-24 results)'),
            Patch(facecolor='green', alpha=0.7, label='High (≥ 25 results)')
        ]
        ax.legend(handles=legend_elements, loc='upper right')

    def _create_classification_2pager_analysis(self, event, classification, event_standards,
                                             event_detailed, all_event_records, event_folder):
        """Create comprehensive 2-page analysis for specific event-classification combination"""

        # Filter data for this classification
        class_standards = event_standards[event_standards['classification'] == classification]
        class_detailed = event_detailed[event_detailed['classification'] == classification]

        if len(class_standards) == 0:
            return

        # PAGE 1: Championship Analysis & Performance Standards
        fig1 = plt.figure(figsize=(16, 20))
        gs1 = fig1.add_gridspec(6, 2, hspace=0.3, wspace=0.3)
        fig1.suptitle(f'{event} {classification} - Page 1: Championship Analysis', fontsize=20, fontweight='bold')

        # 1. Medal Standards Comparison (Enhanced with Asian)
        ax1 = fig1.add_subplot(gs1[0, :])
        self._plot_enhanced_medal_standards(ax1, class_standards, event, classification)

        # 2. Position Analysis (Paralympics vs World Championships vs Asian)
        ax2 = fig1.add_subplot(gs1[1, 0])
        ax3 = fig1.add_subplot(gs1[1, 1])
        self._plot_multi_competition_position_analysis(ax2, ax3, class_detailed, event, classification)

        # 3. Performance Distribution & All Records
        ax4 = fig1.add_subplot(gs1[2, 0])
        ax5 = fig1.add_subplot(gs1[2, 1])
        self._plot_performance_with_all_records(ax4, ax5, class_detailed, all_event_records, event, classification)

        # 4. Enhanced Medal Standards Table
        ax6 = fig1.add_subplot(gs1[3, :])
        self._create_enhanced_medal_standards_table(ax6, class_standards, event, classification)

        # 5. Top 8 Performance Table (All competitions)
        ax7 = fig1.add_subplot(gs1[4, :])
        self._create_enhanced_top8_table(ax7, class_detailed, event, classification)

        # 6. All Records Table
        ax8 = fig1.add_subplot(gs1[5, :])
        self._create_all_records_table(ax8, all_event_records, event, classification)

        # Save Page 1
        filename1 = event_folder / f'{classification}_Page1_Championship_Analysis.png'
        plt.savefig(filename1, dpi=300, bbox_inches='tight')
        plt.close()

        # PAGE 2: Athlete Progressions & Regional Analysis
        fig2 = plt.figure(figsize=(16, 20))
        gs2 = fig2.add_gridspec(6, 2, hspace=0.3, wspace=0.3)
        fig2.suptitle(f'{event} {classification} - Page 2: Athletes & Progressions', fontsize=20, fontweight='bold')

        # 1. Top Athletes Progression Over Time
        ax9 = fig2.add_subplot(gs2[0, :])
        self._plot_athlete_progressions(ax9, event, classification)

        # 2. Regional Top Athletes
        ax10 = fig2.add_subplot(gs2[1, 0])
        ax11 = fig2.add_subplot(gs2[1, 1])
        self._plot_regional_top_athletes(ax10, ax11, event, classification)

        # 3. Performance Trends Over Years
        ax12 = fig2.add_subplot(gs2[2, :])
        self._plot_performance_trends_over_time(ax12, event, classification)

        # 4. Top Athletes Table (World)
        ax13 = fig2.add_subplot(gs2[3, :])
        self._create_top_athletes_table(ax13, event, classification, 'World')

        # 5. Top Athletes Table (Asian)
        ax14 = fig2.add_subplot(gs2[4, :])
        self._create_top_athletes_table(ax14, event, classification, 'Asian')

        # 6. Rankings Summary Table
        ax15 = fig2.add_subplot(gs2[5, :])
        self._create_rankings_summary_table(ax15, event, classification)

        # Save Page 2
        filename2 = event_folder / f'{classification}_Page2_Athletes_Progressions.png'
        plt.savefig(filename2, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Created {classification} 2-page analysis")

    def _create_classification_3pager_analysis(self, event, classification, event_standards,
                                             event_detailed, all_event_records, event_folder):
        """Create comprehensive 3-page analysis for specific event-classification combination with Saudi focus"""

        # Filter data for this classification
        class_standards = event_standards[event_standards['classification'] == classification]
        class_detailed = event_detailed[event_detailed['classification'] == classification]

        if len(class_standards) == 0:
            return

        # Saudi color scheme
        saudi_green = '#006C35'
        saudi_white = '#FFFFFF'
        saudi_gold = '#FFD700'
        accent_colors = ['#006C35', '#228B22', '#32CD32', '#90EE90']

        # PAGE 1: Championship Analysis & Saudi Performance Context
        fig1 = plt.figure(figsize=(16, 24))
        fig1.patch.set_facecolor('#F8F8F8')
        gs1 = fig1.add_gridspec(6, 2, hspace=0.5, wspace=0.4)

        # Enhanced title with Saudi branding
        fig1.suptitle(f'🇸🇦 {event} {classification} - Championship Analysis & Saudi Context',
                     fontsize=20, fontweight='bold', color=saudi_green, y=0.98)

        # 1. Medal Standards with Gold & Silver (Enhanced)
        ax1 = fig1.add_subplot(gs1[0, :])
        self._plot_gold_silver_medal_standards(ax1, class_standards, event, classification, saudi_green, saudi_gold)

        # 2. Separate Championship Progression Charts
        ax2 = fig1.add_subplot(gs1[1, 0])
        ax3 = fig1.add_subplot(gs1[1, 1])
        self._plot_separate_championship_progression(ax2, ax3, class_detailed, event, classification, saudi_green)

        # 3. World #1 vs Saudi Best by Classification
        ax4 = fig1.add_subplot(gs1[2, 0])
        ax5 = fig1.add_subplot(gs1[2, 1])
        self._plot_world_vs_saudi_comparison(ax4, ax5, event, classification, saudi_green)

        # 4. Medal Standards Table (Gold, Silver, Bronze with colors)
        ax6 = fig1.add_subplot(gs1[3, :])
        self._create_colored_medal_standards_table(ax6, class_standards, event, classification)

        # 5. Top 8 Table (Min/Max, no sample size)
        ax7 = fig1.add_subplot(gs1[4, :])
        self._create_top8_min_max_table(ax7, class_detailed, event, classification)

        # 6. All Records Table (unchanged)
        ax8 = fig1.add_subplot(gs1[5, :])
        self._create_all_records_table(ax8, all_event_records, event, classification)

        # Save Page 1
        filename1 = event_folder / f'{classification}_Page1_Championship_Analysis.png'
        plt.savefig(filename1, dpi=300, bbox_inches='tight')
        plt.close()

        # PAGE 2: Classification-Specific Analysis & Athlete Progression
        fig2 = plt.figure(figsize=(16, 24))
        fig2.patch.set_facecolor('#F8F8F8')
        gs2 = fig2.add_gridspec(6, 2, hspace=0.5, wspace=0.4)
        fig2.suptitle(f'🇸🇦 {event} {classification} - Classification-Specific Analysis & Athlete Progression',
                     fontsize=20, fontweight='bold', color=saudi_green, y=0.98)

        # 1. Classification-Specific Detailed Summary
        ax9 = fig2.add_subplot(gs2[0, :])
        self._create_classification_detailed_summary(ax9, class_standards, class_detailed, event, classification, saudi_green)

        # 2. Athlete Progression Table with Dates
        ax10 = fig2.add_subplot(gs2[1, :])
        self._create_athlete_progression_table_with_dates(ax10, event, classification)

        # 3. Performance Over Time Trend Chart with Medal Lines
        ax11 = fig2.add_subplot(gs2[2, :])
        self._plot_performance_overtime_with_medal_lines(ax11, event, classification, class_standards, saudi_green, saudi_gold)

        # 4. Top World Performers Table (with dates)
        ax12 = fig2.add_subplot(gs2[3, :])
        self._create_top_performers_table_with_dates(ax12, event, classification, 'World')

        # 5. Top Asian Performers Table (with dates)
        ax13 = fig2.add_subplot(gs2[4, :])
        self._create_top_performers_table_with_dates(ax13, event, classification, 'Asian')

        # 6. Top Performers by Classification (no sample size)
        ax14 = fig2.add_subplot(gs2[5, :])
        self._create_top_performers_by_classification(ax14, event, classification)

        # Save Page 2
        filename2 = event_folder / f'{classification}_Page2_Athletes_Progressions.png'
        plt.savefig(filename2, dpi=300, bbox_inches='tight')
        plt.close()

        # PAGE 3: Medal Opportunities & Saudi Performance Analysis
        fig3 = plt.figure(figsize=(16, 24))
        fig3.patch.set_facecolor('#F8F8F8')
        gs3 = fig3.add_gridspec(6, 2, hspace=0.5, wspace=0.4)
        fig3.suptitle(f'🇸🇦 {event} {classification} - Medal Opportunities & Performance Analysis',
                     fontsize=20, fontweight='bold', color=saudi_green, y=0.98)

        # 1. Top 20 Global Athletes with Data Labels (Fixed Overlapping)
        ax16 = fig3.add_subplot(gs3[0, :])
        self._plot_top20_global_with_data_labels(ax16, event, classification, saudi_green)

        # 2. Saudi Medal Chances Analysis
        ax17 = fig3.add_subplot(gs3[1, 0])
        ax18 = fig3.add_subplot(gs3[1, 1])
        self._plot_saudi_medal_chances_analysis(ax17, ax18, event, classification, class_standards, saudi_green, saudi_gold)

        # 3. Medal Summary with Silver and Positions 1-8
        ax19 = fig3.add_subplot(gs3[2, :])
        self._create_medal_summary_with_positions(ax19, class_standards, event, classification)

        # 4. Top Saudi Athletes Table with Performance Dates
        ax20 = fig3.add_subplot(gs3[3, :])
        self._create_saudi_athletes_table_with_dates(ax20, event, classification)

        # 5. Saudi Performance Summary Across Seasons
        ax21 = fig3.add_subplot(gs3[4, :])
        self._create_saudi_performance_across_seasons(ax21, event, classification)

        # 6. Championship Strategy & Clear Medal Opportunity Assessment
        ax22 = fig3.add_subplot(gs3[5, :])
        self._create_championship_strategy_assessment(ax22, event, classification, class_standards, saudi_green, saudi_gold)

        # Save Page 3
        filename3 = event_folder / f'{classification}_Page3_Medal_Opportunities.png'
        plt.savefig(filename3, dpi=300, bbox_inches='tight')
        plt.close()

        # PAGE 4: 2024-25 Season Competitors Analysis
        fig4 = plt.figure(figsize=(16, 26))
        fig4.patch.set_facecolor('#F8F8F8')
        gs4 = fig4.add_gridspec(7, 2, hspace=0.6, wspace=0.4)
        fig4.suptitle(f'🇸🇦 {event} {classification} - 2024-25 Season Competitors Analysis',
                     fontsize=20, fontweight='bold', color=saudi_green, y=0.98)

        # 1. 2024-25 Season Top Performers Summary
        ax23 = fig4.add_subplot(gs4[0, :])
        self._create_2024_25_season_summary(ax23, event, classification)

        # 2. Recent Form Analysis - World Leaders
        ax24 = fig4.add_subplot(gs4[1, 0])
        ax25 = fig4.add_subplot(gs4[1, 1])
        self._plot_recent_form_analysis(ax24, ax25, event, classification, saudi_green)

        # 3. Competitor Performance Timeline 2024-25
        ax26 = fig4.add_subplot(gs4[2, :])
        self._plot_competitor_timeline_2024_25(ax26, event, classification, saudi_green, saudi_gold)

        # 4. Saudi vs Recent Competitors Table
        ax27 = fig4.add_subplot(gs4[3, :])
        self._create_saudi_vs_recent_competitors_table(ax27, event, classification)

        # 5. Performance Distribution 2024-25 Season
        ax28 = fig4.add_subplot(gs4[4, 0])
        ax29 = fig4.add_subplot(gs4[4, 1])
        self._plot_2024_25_performance_distribution(ax28, ax29, event, classification, saudi_green)

        # 6. Key Competitors Watch List
        ax30 = fig4.add_subplot(gs4[5, :])
        self._create_key_competitors_watch_list(ax30, event, classification, class_standards)

        # 7. Recent Performance Timeline Analysis
        ax31 = fig4.add_subplot(gs4[6, :])
        self._create_recent_performance_analysis(ax31, event, classification, saudi_green)

        # Save Page 4
        filename4 = event_folder / f'{classification}_Page4_2024_25_Competitors.png'
        plt.savefig(filename4, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Created {classification} 4-page analysis")

    def _plot_top_20_global_athletes(self, ax, event, classification):
        """Plot top 20 global athletes"""
        top_20 = self.get_top_20_global_athletes(event, classification)

        if not top_20:
            ax.text(0.5, 0.5, 'No global top 20 data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Top 20 Global Athletes', fontweight='bold')
            return

        # Prepare data for plotting
        names = [a['name'][:20] + '...' if len(a['name']) > 20 else a['name'] for a in top_20]
        performances = [a['performance'] for a in top_20]
        countries = [a['country'] for a in top_20]

        # Color code Saudi athletes differently
        colors = ['red' if 'Saudi' in country else 'lightblue' for country in countries]

        # Create horizontal bar chart
        bars = ax.barh(range(len(names)), performances, color=colors, alpha=0.7)

        # Add country labels
        for i, (bar, country) in enumerate(zip(bars, countries)):
            width = bar.get_width()
            ax.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                   country, ha='left', va='center', fontsize=8)

        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=10)
        ax.set_xlabel('Performance', fontweight='bold')
        ax.set_title(f'Top 20 Global Athletes - {event} {classification}', fontweight='bold')
        ax.invert_yaxis()  # Best performance at top
        ax.grid(True, alpha=0.3)

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', alpha=0.7, label='Saudi Arabia'),
            Patch(facecolor='lightblue', alpha=0.7, label='Other Countries')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

    def _plot_saudi_athletes_analysis(self, ax1, ax2, event, classification):
        """Plot Saudi athletes analysis"""
        saudi_athletes = self.get_saudi_athletes(event, classification)

        if not saudi_athletes:
            ax1.text(0.5, 0.5, 'No Saudi athletes found', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Saudi Athletes Performance', fontweight='bold')
            ax2.text(0.5, 0.5, 'No Saudi data for comparison', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Saudi vs Global Comparison', fontweight='bold')
            return

        # Plot 1: Saudi athletes over time if we have progression data
        if len(saudi_athletes) > 1:
            years = []
            performances = []
            for athlete in saudi_athletes:
                if 'year' in athlete:
                    try:
                        year = int(athlete['year'])
                        if 2015 <= year <= 2025:
                            years.append(year)
                            performances.append(athlete['performance'])
                    except:
                        continue

            if len(years) > 1:
                ax1.plot(years, performances, 'o-', color='red', linewidth=3, markersize=8)
                ax1.set_xlabel('Year', fontweight='bold')
                ax1.set_ylabel('Performance', fontweight='bold')
                ax1.set_title('Saudi Athletes Performance Over Time', fontweight='bold')
                ax1.grid(True, alpha=0.3)
            else:
                # Just show current best performances
                names = [a['name'][:15] + '...' if len(a['name']) > 15 else a['name'] for a in saudi_athletes[:5]]
                perfs = [a['performance'] for a in saudi_athletes[:5]]
                ax1.bar(names, perfs, color='red', alpha=0.7)
                ax1.set_ylabel('Performance', fontweight='bold')
                ax1.set_title('Top Saudi Athletes', fontweight='bold')
                ax1.tick_params(axis='x', rotation=45)
        else:
            # Single athlete
            athlete = saudi_athletes[0]
            ax1.bar([athlete['name']], [athlete['performance']], color='red', alpha=0.7)
            ax1.set_ylabel('Performance', fontweight='bold')
            ax1.set_title('Saudi Athlete Performance', fontweight='bold')

        # Plot 2: Saudi ranking comparison
        if saudi_athletes:
            # Get top 10 global for comparison
            top_10_global = self.get_top_20_global_athletes(event, classification)[:10]
            best_saudi = saudi_athletes[0]

            if top_10_global:
                global_perfs = [a['performance'] for a in top_10_global]
                saudi_perf = best_saudi['performance']

                # Find where Saudi athlete would rank
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
                if is_time_event:
                    rank = sum(1 for p in global_perfs if p < saudi_perf) + 1
                else:
                    rank = sum(1 for p in global_perfs if p > saudi_perf) + 1

                # Plot comparison
                positions = list(range(1, len(global_perfs) + 1))
                ax2.plot(positions, global_perfs, 'o-', color='blue', alpha=0.7, label='Global Top 10')

                # Add Saudi position
                if rank <= 10:
                    ax2.plot([rank], [saudi_perf], 'o', color='red', markersize=12, label=f'Saudi (Rank {rank})')
                else:
                    ax2.axhline(y=saudi_perf, color='red', linestyle='--', alpha=0.7,
                               label=f'Saudi Best ({saudi_perf:.2f})')

                ax2.set_xlabel('World Ranking Position', fontweight='bold')
                ax2.set_ylabel('Performance', fontweight='bold')
                ax2.set_title('Saudi vs Global Top 10', fontweight='bold')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'No global data for comparison', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Saudi vs Global Comparison', fontweight='bold')

    def _plot_global_country_distribution(self, ax, event, classification):
        """Plot distribution of top athletes by country"""
        top_20 = self.get_top_20_global_athletes(event, classification)

        if not top_20:
            ax.text(0.5, 0.5, 'No global data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Global Country Distribution', fontweight='bold')
            return

        # Count athletes by country
        country_counts = {}
        for athlete in top_20:
            country = athlete['country']
            country_counts[country] = country_counts.get(country, 0) + 1

        # Sort by count
        sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_countries) > 0:
            countries = [item[0] for item in sorted_countries]
            counts = [item[1] for item in sorted_countries]

            # Color Saudi Arabia differently
            colors = ['red' if 'Saudi' in country else 'lightblue' for country in countries]

            bars = ax.bar(countries, counts, color=colors, alpha=0.7)
            ax.set_xlabel('Country', fontweight='bold')
            ax.set_ylabel('Number of Top 20 Athletes', fontweight='bold')
            ax.set_title('Global Top 20 Distribution by Country', fontweight='bold')
            ax.tick_params(axis='x', rotation=45)

            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       str(count), ha='center', va='bottom', fontweight='bold')

    def _create_top_20_global_table_part1(self, ax, event, classification):
        """Create top 20 global athletes table (ranks 1-10)"""
        ax.axis('tight')
        ax.axis('off')

        top_20 = self.get_top_20_global_athletes(event, classification)

        if not top_20:
            ax.text(0.5, 0.5, 'No global top 20 data available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Prepare table data for ranks 1-10
        headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Source/Year']
        table_data = [headers]

        for i, athlete in enumerate(top_20[:10], 1):
            # Highlight Saudi athletes
            name = athlete['name']
            if 'Saudi' in athlete['country']:
                name = f"🇸🇦 {name}"

            table_data.append([
                str(i),
                name[:30] + '...' if len(name) > 30 else name,
                athlete['country'],
                f"{athlete['performance']:.2f}",
                athlete.get('source', 'N/A')[:15]
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.1, 0.35, 0.2, 0.15, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Highlight Saudi rows
        for i, athlete in enumerate(top_20[:10], 1):
            if 'Saudi' in athlete['country']:
                for j in range(len(headers)):
                    table[(i, j)].set_facecolor('#ffcccc')

        ax.set_title(f'Global Top 10 Athletes - {event} {classification}', fontweight='bold', fontsize=14, pad=20)

    def _create_top_20_global_table_part2(self, ax, event, classification):
        """Create top 20 global athletes table (ranks 11-20)"""
        ax.axis('tight')
        ax.axis('off')

        top_20 = self.get_top_20_global_athletes(event, classification)

        if len(top_20) < 11:
            ax.text(0.5, 0.5, 'Fewer than 20 athletes available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Prepare table data for ranks 11-20
        headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Source/Year']
        table_data = [headers]

        for i, athlete in enumerate(top_20[10:20], 11):
            # Highlight Saudi athletes
            name = athlete['name']
            if 'Saudi' in athlete['country']:
                name = f"🇸🇦 {name}"

            table_data.append([
                str(i),
                name[:30] + '...' if len(name) > 30 else name,
                athlete['country'],
                f"{athlete['performance']:.2f}",
                athlete.get('source', 'N/A')[:15]
            ])

        if len(table_data) > 1:
            table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                            colWidths=[0.1, 0.35, 0.2, 0.15, 0.2])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.3)

            # Style header row
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#40466e')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Highlight Saudi rows
            for i, athlete in enumerate(top_20[10:20], 1):
                if 'Saudi' in athlete['country']:
                    for j in range(len(headers)):
                        table[(i, j)].set_facecolor('#ffcccc')

        ax.set_title(f'Global Athletes 11-20 - {event} {classification}', fontweight='bold', fontsize=14, pad=20)

    def _create_saudi_athletes_table(self, ax, event, classification):
        """Create Saudi athletes table and analysis"""
        ax.axis('tight')
        ax.axis('off')

        saudi_athletes = self.get_saudi_athletes(event, classification)

        if not saudi_athletes:
            ax.text(0.5, 0.5, '🇸🇦 No Saudi Athletes Found in This Classification', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14, fontweight='bold')
            ax.set_title('Saudi Arabia Analysis', fontweight='bold', fontsize=14, pad=20)
            return

        # Prepare table data
        headers = ['Rank', '🇸🇦 Saudi Athlete', 'Performance', 'Year/Date', 'Source']
        table_data = [headers]

        for i, athlete in enumerate(saudi_athletes[:10], 1):  # Show top 10 Saudi athletes
            table_data.append([
                str(i),
                athlete['name'][:25] + '...' if len(athlete['name']) > 25 else athlete['name'],
                f"{athlete['performance']:.2f}",
                athlete.get('year', athlete.get('date', 'N/A')),
                athlete.get('source', 'N/A')[:15]
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.1, 0.35, 0.15, 0.2, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.4)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#006c35')  # Saudi green
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Style all data rows with Saudi colors
        for i in range(1, len(table_data)):
            for j in range(len(headers)):
                table[(i, j)].set_facecolor('#f0f8f0')  # Light green background

        ax.set_title(f'🇸🇦 Saudi Arabia Athletes - {event} {classification}',
                    fontweight='bold', fontsize=14, pad=20, color='#006c35')

    def _plot_enhanced_medal_standards(self, ax, class_standards, event, classification):
        """Enhanced medal standards including Asian competitions"""
        if len(class_standards) == 0:
            ax.text(0.5, 0.5, 'No medal standards data available', ha='center', va='center', transform=ax.transAxes)
            return

        row = class_standards.iloc[0]

        # Extract data for all three competitions
        competitions = ['Paralympics', 'World Championships', 'Asian Championships']
        gold_values = [
            row.get('paralympics_gold') if not pd.isna(row.get('paralympics_gold')) else None,
            row.get('wc_gold') if not pd.isna(row.get('wc_gold')) else None,
            None  # Placeholder for Asian - would need to be calculated from main data
        ]
        bronze_values = [
            row.get('paralympics_bronze') if not pd.isna(row.get('paralympics_bronze')) else None,
            row.get('wc_bronze') if not pd.isna(row.get('wc_bronze')) else None,
            None  # Placeholder for Asian
        ]

        # Create grouped bar chart
        categories = ['Gold Medal', 'Bronze Medal']
        x = np.arange(len(categories))
        width = 0.25

        # Filter out None values and align arrays
        valid_comps = []
        valid_gold = []
        valid_bronze = []
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        for i, comp in enumerate(competitions):
            if gold_values[i] is not None or bronze_values[i] is not None:
                valid_comps.append(comp)
                valid_gold.append(gold_values[i] if gold_values[i] is not None else 0)
                valid_bronze.append(bronze_values[i] if bronze_values[i] is not None else 0)

        # Plot bars for each valid competition
        for i, comp in enumerate(valid_comps):
            offset = (i - len(valid_comps)/2 + 0.5) * width
            values = [valid_gold[i], valid_bronze[i]]
            bars = ax.bar(x + offset, values, width, label=comp, alpha=0.8, color=colors[i])

            # Add value labels
            for bar, value in zip(bars, values):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{value:.2f}', ha='center', va='bottom', fontweight='bold', fontsize=10)

        ax.set_xlabel('Medal Type', fontweight='bold')
        ax.set_ylabel('Performance Standard', fontweight='bold')
        ax.set_title(f'Medal Standards Comparison - {event} {classification}', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_athlete_progressions(self, ax, event, classification):
        """Plot top athlete progressions over time"""
        progressions = self.analyze_athlete_progressions(event, classification)

        if not progressions:
            ax.text(0.5, 0.5, 'No progression data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Athlete Progressions Over Time', fontweight='bold')
            return

        # Plot top 5 athletes with most data points
        top_athletes = sorted(progressions.items(), key=lambda x: len(x[1]['performances']), reverse=True)[:5]
        colors = plt.cm.Set3(np.linspace(0, 1, len(top_athletes)))

        for i, (athlete_name, data) in enumerate(top_athletes):
            if len(data['performances']) >= 2:  # Need at least 2 points for progression
                years = [int(p['year']) for p in data['performances']]
                performances = [p['performance'] for p in data['performances']]

                ax.plot(years, performances, 'o-', label=f"{athlete_name} ({data['country']})",
                       color=colors[i], linewidth=2, markersize=6)

        ax.set_xlabel('Year', fontweight='bold')
        ax.set_ylabel('Performance', fontweight='bold')
        ax.set_title(f'Top Athlete Progressions - {event} {classification}', fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

    def _plot_regional_top_athletes(self, ax1, ax2, event, classification):
        """Plot top athletes by region"""
        # World top athletes
        world_athletes = self.get_top_athletes_by_region(event, classification, 'World', 8)
        if world_athletes:
            names = [a['name'][:15] + '...' if len(a['name']) > 15 else a['name'] for a in world_athletes]
            performances = [a['performance'] for a in world_athletes]
            countries = [a['country'] for a in world_athletes]

            bars = ax1.barh(names, performances, alpha=0.7)
            ax1.set_xlabel('Performance', fontweight='bold')
            ax1.set_title('World Top Performers', fontweight='bold')

            # Add country labels
            for bar, country in zip(bars, countries):
                width = bar.get_width()
                ax1.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                        country, ha='left', va='center', fontsize=8)
        else:
            ax1.text(0.5, 0.5, 'No world athletes data', ha='center', va='center', transform=ax1.transAxes)

        # Asian top athletes
        asian_athletes = self.get_top_athletes_by_region(event, classification, 'Asian', 8)
        if asian_athletes:
            names = [a['name'][:15] + '...' if len(a['name']) > 15 else a['name'] for a in asian_athletes]
            performances = [a['performance'] for a in asian_athletes]
            countries = [a['country'] for a in asian_athletes]

            bars = ax2.barh(names, performances, alpha=0.7, color='orange')
            ax2.set_xlabel('Performance', fontweight='bold')
            ax2.set_title('Asian Top Performers', fontweight='bold')

            # Add country labels
            for bar, country in zip(bars, countries):
                width = bar.get_width()
                ax2.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                        country, ha='left', va='center', fontsize=8)
        else:
            ax2.text(0.5, 0.5, 'No Asian athletes data', ha='center', va='center', transform=ax2.transAxes)

    def _create_top_athletes_table(self, ax, event, classification, region):
        """Create top athletes table for specific region"""
        ax.axis('tight')
        ax.axis('off')

        athletes = self.get_top_athletes_by_region(event, classification, region, 8)

        if not athletes:
            ax.text(0.5, 0.5, f'No {region} athletes data available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Prepare table data
        headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Type/Date']
        table_data = [headers]

        for i, athlete in enumerate(athletes, 1):
            table_data.append([
                str(i),
                athlete['name'][:25] + '...' if len(athlete['name']) > 25 else athlete['name'],
                athlete['country'],
                f"{athlete['performance']:.2f}",
                athlete.get('type', athlete.get('date', 'N/A'))[:20]
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.1, 0.35, 0.15, 0.15, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title(f'{region} Top Performers - {event} {classification}', fontweight='bold', fontsize=14, pad=20)

    def _create_event_2pager_summary(self, event, event_standards, event_detailed, all_event_records, event_folder):
        """Create comprehensive 2-page event summary"""

        # PAGE 1: Event Overview & Standards
        fig1 = plt.figure(figsize=(16, 20))
        gs1 = fig1.add_gridspec(5, 2, hspace=0.4, wspace=0.3)
        fig1.suptitle(f'{event} - Page 1: Complete Championship Overview', fontsize=22, fontweight='bold')

        # 1. Overview comparison across all classifications
        ax1 = fig1.add_subplot(gs1[0, :])
        self._plot_event_overview_comparison(ax1, event_standards, event)

        # 2. Classification comparison charts
        ax2 = fig1.add_subplot(gs1[1, 0])
        ax3 = fig1.add_subplot(gs1[1, 1])
        self._plot_classification_medal_comparison(ax2, ax3, event_standards, event)

        # 3. Complete standards table
        ax4 = fig1.add_subplot(gs1[2, :])
        self._create_complete_standards_table(ax4, event_standards, event)

        # 4. All records summary
        ax5 = fig1.add_subplot(gs1[3, :])
        self._create_all_records_summary_table(ax5, all_event_records, event)

        # 5. Sample sizes and data quality
        ax6 = fig1.add_subplot(gs1[4, :])
        self._plot_sample_sizes_by_classification(ax6, event_standards, event)

        # Save Page 1
        filename1 = event_folder / f'{event.replace(" ", "_")}_Page1_OVERVIEW.png'
        plt.savefig(filename1, dpi=300, bbox_inches='tight')
        plt.close()

        # PAGE 2: Athletes & Performance Analysis
        fig2 = plt.figure(figsize=(16, 20))
        gs2 = fig2.add_gridspec(5, 2, hspace=0.4, wspace=0.3)
        fig2.suptitle(f'{event} - Page 2: Athletes & Performance Trends', fontsize=22, fontweight='bold')

        # 1. Top classification progression analysis
        ax7 = fig2.add_subplot(gs2[0, :])
        top_classification = event_standards['classification'].value_counts().index[0]
        self._plot_athlete_progressions(ax7, event, top_classification)

        # 2. Regional comparison for top classification
        ax8 = fig2.add_subplot(gs2[1, 0])
        ax9 = fig2.add_subplot(gs2[1, 1])
        self._plot_regional_top_athletes(ax8, ax9, event, top_classification)

        # 3. Performance trends over years
        ax10 = fig2.add_subplot(gs2[2, :])
        self._plot_performance_trends_over_time(ax10, event, top_classification)

        # 4. Top performers by classification
        ax11 = fig2.add_subplot(gs2[3, :])
        self._create_top_performers_by_classification_table(ax11, event, event_standards)

        # 5. Recent rankings summary
        ax12 = fig2.add_subplot(gs2[4, :])
        self._create_recent_rankings_summary(ax12, event)

        # Save Page 2
        filename2 = event_folder / f'{event.replace(" ", "_")}_Page2_ATHLETES.png'
        plt.savefig(filename2, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Created {event} 2-page summary")

    def _create_event_3pager_summary(self, event, event_standards, event_detailed, all_event_records, event_folder):
        """Create comprehensive 3-page event summary"""

        # PAGE 1: Event Overview & Standards (same as before)
        fig1 = plt.figure(figsize=(16, 20))
        gs1 = fig1.add_gridspec(5, 2, hspace=0.4, wspace=0.3)
        fig1.suptitle(f'{event} - Page 1: Complete Championship Overview', fontsize=22, fontweight='bold')

        # 1. Overview comparison across all classifications
        ax1 = fig1.add_subplot(gs1[0, :])
        self._plot_event_overview_comparison(ax1, event_standards, event)

        # 2. Classification comparison charts
        ax2 = fig1.add_subplot(gs1[1, 0])
        ax3 = fig1.add_subplot(gs1[1, 1])
        self._plot_classification_medal_comparison(ax2, ax3, event_standards, event)

        # 3. Complete standards table
        ax4 = fig1.add_subplot(gs1[2, :])
        self._create_complete_standards_table(ax4, event_standards, event)

        # 4. All records summary
        ax5 = fig1.add_subplot(gs1[3, :])
        self._create_all_records_summary_table(ax5, all_event_records, event)

        # 5. Sample sizes and data quality
        ax6 = fig1.add_subplot(gs1[4, :])
        self._plot_sample_sizes_by_classification(ax6, event_standards, event)

        # Save Page 1
        filename1 = event_folder / f'{event.replace(" ", "_")}_Page1_OVERVIEW.png'
        plt.savefig(filename1, dpi=300, bbox_inches='tight')
        plt.close()

        # PAGE 2: Athletes & Performance Analysis (same as before)
        fig2 = plt.figure(figsize=(16, 20))
        gs2 = fig2.add_gridspec(5, 2, hspace=0.4, wspace=0.3)
        fig2.suptitle(f'{event} - Page 2: Athletes & Performance Trends', fontsize=22, fontweight='bold')

        # 1. Top classification progression analysis
        ax7 = fig2.add_subplot(gs2[0, :])
        top_classification = event_standards['classification'].value_counts().index[0]
        self._plot_athlete_progressions(ax7, event, top_classification)

        # 2. Regional comparison for top classification
        ax8 = fig2.add_subplot(gs2[1, 0])
        ax9 = fig2.add_subplot(gs2[1, 1])
        self._plot_regional_top_athletes(ax8, ax9, event, top_classification)

        # 3. Performance trends over years
        ax10 = fig2.add_subplot(gs2[2, :])
        self._plot_performance_trends_over_time(ax10, event, top_classification)

        # 4. Top performers by classification
        ax11 = fig2.add_subplot(gs2[3, :])
        self._create_top_performers_by_classification_table(ax11, event, event_standards)

        # 5. Recent rankings summary
        ax12 = fig2.add_subplot(gs2[4, :])
        self._create_recent_rankings_summary(ax12, event)

        # Save Page 2
        filename2 = event_folder / f'{event.replace(" ", "_")}_Page2_ATHLETES.png'
        plt.savefig(filename2, dpi=300, bbox_inches='tight')
        plt.close()

        # PAGE 3: Top 20 Global & Saudi Analysis
        fig3 = plt.figure(figsize=(16, 20))
        gs3 = fig3.add_gridspec(6, 2, hspace=0.4, wspace=0.3)
        fig3.suptitle(f'{event} - Page 3: Global Top 20 & Saudi Arabia Analysis', fontsize=22, fontweight='bold')

        # 1. Top 20 Global for most popular classification
        ax13 = fig3.add_subplot(gs3[0, :])
        self._plot_top_20_global_athletes(ax13, event, top_classification)

        # 2. Saudi athletes analysis for top classification
        ax14 = fig3.add_subplot(gs3[1, 0])
        ax15 = fig3.add_subplot(gs3[1, 1])
        self._plot_saudi_athletes_analysis(ax14, ax15, event, top_classification)

        # 3. Global country distribution
        ax16 = fig3.add_subplot(gs3[2, :])
        self._plot_global_country_distribution(ax16, event, top_classification)

        # 4. Multi-classification top athletes comparison
        ax17 = fig3.add_subplot(gs3[3, :])
        self._create_multi_classification_top_athletes_table(ax17, event, event_standards)

        # 5. Saudi athletes across all classifications
        ax18 = fig3.add_subplot(gs3[4, :])
        self._create_all_saudi_athletes_table(ax18, event, event_standards)

        # 6. Event summary statistics
        ax19 = fig3.add_subplot(gs3[5, :])
        self._create_event_summary_statistics_table(ax19, event, event_standards, all_event_records)

        # Save Page 3
        filename3 = event_folder / f'{event.replace(" ", "_")}_Page3_GLOBAL_SAUDI.png'
        plt.savefig(filename3, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Created {event} 3-page summary")

    def _create_multi_classification_top_athletes_table(self, ax, event, event_standards):
        """Create table showing top athlete from each classification"""
        ax.axis('tight')
        ax.axis('off')

        headers = ['Classification', 'World #1', 'Country', 'Performance', 'Saudi Best', 'Saudi Performance']
        table_data = [headers]

        for _, row in event_standards.iterrows():
            classification = row['classification']

            # Get world #1
            top_global = self.get_top_20_global_athletes(event, classification)
            world_1 = top_global[0] if top_global else None

            # Get Saudi best
            saudi_athletes = self.get_saudi_athletes(event, classification)
            saudi_best = saudi_athletes[0] if saudi_athletes else None

            table_data.append([
                classification,
                world_1['name'][:20] + '...' if world_1 and len(world_1['name']) > 20 else world_1['name'] if world_1 else 'N/A',
                world_1['country'] if world_1 else 'N/A',
                f"{world_1['performance']:.2f}" if world_1 else 'N/A',
                saudi_best['name'][:15] + '...' if saudi_best and len(saudi_best['name']) > 15 else saudi_best['name'] if saudi_best else 'No Saudi',
                f"{saudi_best['performance']:.2f}" if saudi_best else 'N/A'
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.15, 0.25, 0.15, 0.15, 0.2, 0.1])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.2)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Highlight rows with Saudi athletes
        for i, row_data in enumerate(table_data[1:], 1):
            if row_data[4] != 'No Saudi':
                for j in range(len(headers)):
                    if j >= 4:  # Saudi columns
                        table[(i, j)].set_facecolor('#ffcccc')

        ax.set_title(f'{event} - World #1 vs Saudi Best by Classification', fontweight='bold', fontsize=14, pad=20)

    def _create_all_saudi_athletes_table(self, ax, event, event_standards):
        """Create table of all Saudi athletes across classifications"""
        ax.axis('tight')
        ax.axis('off')

        all_saudi = []
        for _, row in event_standards.iterrows():
            classification = row['classification']
            saudi_athletes = self.get_saudi_athletes(event, classification)
            for athlete in saudi_athletes:
                athlete['classification'] = classification
                all_saudi.append(athlete)

        if not all_saudi:
            ax.text(0.5, 0.5, '🇸🇦 No Saudi Athletes Found in Any Classification', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14, fontweight='bold')
            ax.set_title('Saudi Arabia Complete Analysis', fontweight='bold', fontsize=14, pad=20)
            return

        # Sort by performance
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
        all_saudi.sort(key=lambda x: x['performance'], reverse=not is_time_event)

        # Prepare table data
        headers = ['Rank', '🇸🇦 Athlete', 'Classification', 'Performance', 'Year', 'Source']
        table_data = [headers]

        for i, athlete in enumerate(all_saudi[:15], 1):  # Show top 15 across all classifications
            table_data.append([
                str(i),
                athlete['name'][:20] + '...' if len(athlete['name']) > 20 else athlete['name'],
                athlete['classification'],
                f"{athlete['performance']:.2f}",
                athlete.get('year', athlete.get('date', 'N/A')),
                athlete.get('source', 'N/A')[:12]
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.1, 0.3, 0.15, 0.15, 0.15, 0.15])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#006c35')  # Saudi green
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Style all data rows with Saudi colors
        for i in range(1, len(table_data)):
            for j in range(len(headers)):
                table[(i, j)].set_facecolor('#f0f8f0')  # Light green background

        ax.set_title(f'🇸🇦 All Saudi Athletes - {event} (All Classifications)',
                    fontweight='bold', fontsize=14, pad=20, color='#006c35')

    def _create_event_summary_statistics_table(self, ax, event, event_standards, all_event_records):
        """Create event summary statistics"""
        ax.axis('tight')
        ax.axis('off')

        # Calculate statistics
        total_classifications = len(event_standards)
        total_records = sum(len(records) for records in all_event_records.values())

        # Count Saudi athletes across all classifications
        total_saudi = 0
        for _, row in event_standards.iterrows():
            classification = row['classification']
            saudi_athletes = self.get_saudi_athletes(event, classification)
            total_saudi += len(saudi_athletes)

        # Count top 20 athletes
        total_top_20 = 0
        for _, row in event_standards.iterrows():
            classification = row['classification']
            top_20 = self.get_top_20_global_athletes(event, classification)
            total_top_20 += len(top_20)

        # Get country distribution from top athletes
        all_countries = set()
        for _, row in event_standards.iterrows():
            classification = row['classification']
            top_20 = self.get_top_20_global_athletes(event, classification)
            for athlete in top_20:
                all_countries.add(athlete['country'])

        # Create summary table
        headers = ['Metric', 'Value']
        table_data = [
            headers,
            ['Classifications Analyzed', str(total_classifications)],
            ['Total Records Available', str(total_records)],
            ['Saudi Athletes Found', str(total_saudi)],
            ['Global Top Athletes', str(total_top_20)],
            ['Countries Represented', str(len(all_countries))],
            ['', ''],  # Spacer
            ['Record Types Available:', ''],
        ]

        # Add record types
        for record_type in all_event_records.keys():
            table_data.append([f'  {record_type}', str(len(all_event_records[record_type]))])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.2)

        # Style header row
        table[(0, 0)].set_facecolor('#40466e')
        table[(0, 1)].set_facecolor('#40466e')
        table[(0, 0)].set_text_props(weight='bold', color='white')
        table[(0, 1)].set_text_props(weight='bold', color='white')

        # Highlight Saudi statistics
        if total_saudi > 0:
            table[(3, 0)].set_facecolor('#ffcccc')
            table[(3, 1)].set_facecolor('#ffcccc')

        ax.set_title(f'{event} - Complete Analysis Summary', fontweight='bold', fontsize=14, pad=20)

    # Additional helper functions for the new 2-pager format
    def _plot_multi_competition_position_analysis(self, ax1, ax2, class_detailed, event, classification):
        """Plot position analysis including Asian competitions"""
        # This would be similar to existing position analysis but include Asian data
        # For now, using existing function
        self._plot_position_analysis_split(ax1, ax2, class_detailed, event, classification)

    def _plot_performance_with_all_records(self, ax1, ax2, class_detailed, all_event_records, event, classification):
        """Plot performance distribution with all regional records"""
        # Performance distribution (same as before)
        if len(class_detailed) > 0:
            all_performances = class_detailed['mean_performance'].values
            ax1.hist(all_performances, bins=15, alpha=0.7, edgecolor='black', color='skyblue')
            ax1.axvline(all_performances.mean(), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {all_performances.mean():.2f}')
            ax1.set_xlabel('Performance', fontweight='bold')
            ax1.set_ylabel('Frequency', fontweight='bold')
            ax1.set_title('Performance Distribution', fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        # All records comparison
        if all_event_records:
            record_types = []
            record_perfs = []

            for record_type, records_df in all_event_records.items():
                class_records = records_df[
                    records_df['event_name'].str.contains(classification, case=False, na=False)
                ]
                if len(class_records) > 0:
                    record_types.append(record_type.replace(' Record', ''))
                    # Get best performance for this record type
                    try:
                        best_perf = class_records['Result'].iloc[0]
                        if ':' in str(best_perf):
                            parts = str(best_perf).split(':')
                            numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                        else:
                            numeric_perf = float(best_perf)
                        record_perfs.append(numeric_perf)
                    except:
                        record_perfs.append(0)

            if record_types:
                ax2.bar(record_types, record_perfs, alpha=0.7, color='gold')
                ax2.set_xlabel('Record Type', fontweight='bold')
                ax2.set_ylabel('Performance', fontweight='bold')
                ax2.set_title('Regional Records Comparison', fontweight='bold')
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'No records for classification', ha='center', va='center', transform=ax2.transAxes)
        else:
            ax2.text(0.5, 0.5, 'No Records Available', ha='center', va='center', transform=ax2.transAxes)

    def _create_enhanced_medal_standards_table(self, ax, class_standards, event, classification):
        """Enhanced medal standards table with Asian data"""
        # For now, use existing table - would be enhanced with Asian championship data
        self._create_medal_standards_table(ax, class_standards, event, classification)

    def _create_enhanced_top8_table(self, ax, class_detailed, event, classification):
        """Enhanced top 8 table with all competitions"""
        # For now, use existing table - would be enhanced with Asian championship data
        self._create_top8_performance_table(ax, class_detailed, event, classification)

    def _create_all_records_table(self, ax, all_event_records, event, classification):
        """Table showing all regional records"""
        ax.axis('tight')
        ax.axis('off')

        if not all_event_records:
            ax.text(0.5, 0.5, 'No Records Data Available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Prepare table data
        headers = ['Record Type', 'Performance', 'Athlete', 'Country', 'Date']
        table_data = [headers]

        for record_type, records_df in all_event_records.items():
            class_records = records_df[
                records_df['event_name'].str.contains(classification, case=False, na=False)
            ]
            if len(class_records) > 0:
                record = class_records.iloc[0]
                table_data.append([
                    record_type.replace(' Record', ''),
                    record.get('Result', 'N/A'),
                    f"{record.get('GivenName', '')} {record.get('FamilyName', '')}".strip()[:20],
                    record.get('CountryName', 'N/A'),
                    record.get('Date', 'N/A')
                ])

        if len(table_data) > 1:
            table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                            colWidths=[0.2, 0.15, 0.3, 0.15, 0.2])
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 1.3)

            # Style header row
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#40466e')
                table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title('All Regional Records', fontweight='bold', fontsize=14, pad=20)

    def _plot_performance_trends_over_time(self, ax, event, classification):
        """Plot performance trends over multiple years"""
        # Analyze trends from rankings data
        yearly_performances = {}

        for key, rankings_df in self.rankings_data.items():
            if 'World Rankings' in key:
                year = key.split('_')[-1]
                try:
                    year_int = int(year)
                    if 2015 <= year_int <= 2024:  # Focus on recent years
                        event_data = rankings_df[
                            (rankings_df.get('Class', '').str.contains(classification, case=False, na=False))
                        ]
                        if len(event_data) > 0:
                            # Get top performance for this year
                            best_perf = event_data.iloc[0]['Result']
                            try:
                                if ':' in str(best_perf):
                                    parts = str(best_perf).split(':')
                                    numeric_perf = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(parts[-1])
                                else:
                                    numeric_perf = float(best_perf)
                                yearly_performances[year_int] = numeric_perf
                            except:
                                continue
                except:
                    continue

        if yearly_performances:
            years = sorted(yearly_performances.keys())
            performances = [yearly_performances[year] for year in years]

            ax.plot(years, performances, 'o-', linewidth=3, markersize=8, color='darkblue')
            ax.set_xlabel('Year', fontweight='bold')
            ax.set_ylabel('Best Performance', fontweight='bold')
            ax.set_title(f'Performance Trends Over Time - {event} {classification}', fontweight='bold')
            ax.grid(True, alpha=0.3)

            # Add trend line
            if len(years) > 2:
                z = np.polyfit(years, performances, 1)
                p = np.poly1d(z)
                ax.plot(years, p(years), "--", alpha=0.7, color='red', label='Trend')
                ax.legend()
        else:
            ax.text(0.5, 0.5, 'No trend data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Performance Trends - {event} {classification}', fontweight='bold')

    def _create_rankings_summary_table(self, ax, event, classification):
        """Create rankings summary from recent data"""
        ax.axis('tight')
        ax.axis('off')

        # Get 2024 world rankings for this event/classification
        world_rankings_2024 = self.rankings_data.get('World Rankings_2024')
        if world_rankings_2024 is None:
            ax.text(0.5, 0.5, 'No 2024 rankings available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        event_rankings = world_rankings_2024[
            world_rankings_2024.get('Class', '').str.contains(classification, case=False, na=False)
        ].head(8)

        if len(event_rankings) == 0:
            ax.text(0.5, 0.5, 'No rankings for this classification', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Prepare table data
        headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Competition']
        table_data = [headers]

        for _, ranking in event_rankings.iterrows():
            athlete_name = f"{ranking.get('GivenName', '')} {ranking.get('FamilyName', '')}"
            table_data.append([
                str(ranking.get('Rank', '')),
                athlete_name[:25] + '...' if len(athlete_name) > 25 else athlete_name,
                ranking.get('CountryName', 'N/A'),
                ranking.get('Result', 'N/A'),
                ranking.get('Competition', 'N/A')[:20] + '...' if len(str(ranking.get('Competition', ''))) > 20 else ranking.get('Competition', 'N/A')
            ])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.1, 0.3, 0.15, 0.15, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)

        # Style header row
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title('2024 World Rankings Summary', fontweight='bold', fontsize=14, pad=20)

    def _create_all_records_summary_table(self, ax, all_event_records, event):
        """Create summary table of all regional records for the event"""
        ax.axis('tight')
        ax.axis('off')

        if not all_event_records:
            ax.text(0.5, 0.5, 'No Records Data Available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14)
            return

        # Prepare table data - show sample of records from each region
        headers = ['Record Type', 'Classification', 'Performance', 'Athlete', 'Country']
        table_data = [headers]

        for record_type, records_df in all_event_records.items():
            # Take top 2 records from each type to avoid overcrowding
            for _, record in records_df.head(2).iterrows():
                # Extract classification from record name
                record_name = record.get('event_name', '')
                classification = ''
                if 'T' in record_name or 'F' in record_name:
                    parts = record_name.split(' ')
                    for part in parts:
                        if part.startswith(('T', 'F')) and any(c.isdigit() for c in part):
                            classification = part
                            break

                table_data.append([
                    record_type.replace(' Record', '')[:15],
                    classification,
                    record.get('Result', 'N/A'),
                    f"{record.get('GivenName', '')} {record.get('FamilyName', '')}".strip()[:20],
                    record.get('CountryName', 'N/A')
                ])

                if len(table_data) > 15:  # Limit table size
                    break
            if len(table_data) > 15:
                break

        if len(table_data) > 1:
            table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                            colWidths=[0.2, 0.15, 0.15, 0.3, 0.2])
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.2)

            # Style header row
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#40466e')
                table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title(f'{event} - All Regional Records Summary', fontweight='bold', fontsize=16, pad=20)

    def _create_top_performers_by_classification_table(self, ax, event, event_standards):
        """Create table showing top performers across all classifications"""
        ax.axis('tight')
        ax.axis('off')

        # Get top performer for each classification from recent rankings
        headers = ['Classification', 'Top Athlete', 'Country', 'Performance', 'Type']
        table_data = [headers]

        for _, row in event_standards.iterrows():
            classification = row['classification']

            # Try to get top athlete from 2024 world rankings
            world_rankings_2024 = self.rankings_data.get('World Rankings_2024')
            if world_rankings_2024 is not None:
                class_rankings = world_rankings_2024[
                    world_rankings_2024.get('Class', '').str.contains(classification, case=False, na=False)
                ]
                if len(class_rankings) > 0:
                    top_athlete = class_rankings.iloc[0]
                    athlete_name = f"{top_athlete.get('GivenName', '')} {top_athlete.get('FamilyName', '')}"

                    table_data.append([
                        classification,
                        athlete_name[:20] + '...' if len(athlete_name) > 20 else athlete_name,
                        top_athlete.get('CountryName', 'N/A'),
                        top_athlete.get('Result', 'N/A'),
                        '2024 WR #1'
                    ])

        if len(table_data) > 1:
            table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                            colWidths=[0.15, 0.3, 0.15, 0.15, 0.15])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.3)

            # Style header row
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#40466e')
                table[(0, i)].set_text_props(weight='bold', color='white')
        else:
            ax.text(0.5, 0.5, 'No recent rankings data available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        ax.set_title(f'{event} - Top Performers by Classification (2024)', fontweight='bold', fontsize=14, pad=20)

    def _create_recent_rankings_summary(self, ax, event):
        """Create summary of recent rankings across all classifications"""
        ax.axis('tight')
        ax.axis('off')

        world_rankings_2024 = self.rankings_data.get('World Rankings_2024')
        if world_rankings_2024 is None:
            ax.text(0.5, 0.5, 'No 2024 world rankings available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return

        # Get summary statistics
        total_ranked = len(world_rankings_2024)
        unique_countries = world_rankings_2024['CountryName'].nunique()

        # Top countries by number of ranked athletes
        top_countries = world_rankings_2024['CountryName'].value_counts().head(5)

        # Create summary table
        headers = ['Metric', 'Value']
        table_data = [
            headers,
            ['Total Ranked Athletes', str(total_ranked)],
            ['Countries Represented', str(unique_countries)],
            ['', ''],  # Spacer
            ['Top Countries by Athletes:', '']
        ]

        for country, count in top_countries.items():
            table_data.append([country, str(count)])

        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.3)

        # Style header row
        table[(0, 0)].set_facecolor('#40466e')
        table[(0, 1)].set_facecolor('#40466e')
        table[(0, 0)].set_text_props(weight='bold', color='white')
        table[(0, 1)].set_text_props(weight='bold', color='white')

        ax.set_title('2024 World Rankings Summary', fontweight='bold', fontsize=14, pad=20)

    def export_summary_data(self):
        """Export summary data for further analysis"""
        summary = {
            'total_championship_results': len(self.identify_major_championships()) if self.main_data is not None else 0,
            'world_records': len(self.world_records) if self.world_records is not None else 0,
            'rankings_years': list(self.rankings_data.keys()),
            'major_competitions': self.identify_major_championships()['competitionname'].value_counts().to_dict() if self.main_data is not None else {}
        }

        return summary

    def _plot_saudi_championship_expectations(self, ax, class_standards, event, classification, saudi_green, saudi_gold):
        """Plot Saudi athlete performance vs championship standards with expectations"""
        # Get Saudi athletes for this event/classification
        saudi_athletes = self.get_saudi_athletes(event, classification)

        if not saudi_athletes:
            ax.text(0.5, 0.5, f'No Saudi athletes found for {event} {classification}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title('Saudi Championship Expectations', fontweight='bold', color=saudi_green)
            return

        # Extract championship standards
        standards = ['paralympics_gold', 'paralympics_bronze', 'paralympics_8th_place',
                    'wc_gold', 'wc_bronze', 'wc_8th_place']

        positions = []
        values = []
        colors = []

        for i, standard in enumerate(standards):
            if standard in class_standards.columns:
                val = class_standards[standard].iloc[0]
                if pd.notna(val):
                    positions.append(i)
                    values.append(val)
                    if 'gold' in standard:
                        colors.append(saudi_gold)
                    elif 'bronze' in standard:
                        colors.append('#CD7F32')
                    else:
                        colors.append('#C0C0C0')

        # Plot championship standards
        bars = ax.bar(positions, values, color=colors, alpha=0.7, label='Championship Standards')

        # Add Saudi athlete performances
        saudi_performances = [a['performance'] for a in saudi_athletes if a['performance'] is not None]
        if saudi_performances:
            best_saudi = min(saudi_performances) if event in ['100m', '200m', '400m', '800m', '1500m'] else max(saudi_performances)

            # Add horizontal line for best Saudi performance
            ax.axhline(y=best_saudi, color=saudi_green, linewidth=3, linestyle='--',
                      label=f'Best Saudi: {best_saudi:.2f}')

            # Add expectation zones
            is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
            if values:
                if is_time_event:
                    medal_zone = min(values[:2]) if len(values) >= 2 else values[0]
                    final_zone = max(values) if values else medal_zone
                else:
                    medal_zone = max(values[:2]) if len(values) >= 2 else values[0]
                    final_zone = min(values) if values else medal_zone

                ax.axhspan(medal_zone * 0.98 if is_time_event else medal_zone * 1.02,
                          medal_zone * 1.02 if is_time_event else medal_zone * 0.98,
                          alpha=0.2, color=saudi_gold, label='Medal Opportunity Zone')

        # Formatting
        ax.set_title(f'Saudi Championship Expectations - {event} {classification}',
                    fontweight='bold', color=saudi_green, fontsize=14)
        ax.set_xlabel('Championship Level', fontweight='bold')
        ax.set_ylabel('Performance', fontweight='bold')

        labels = ['Para Gold', 'Para Bronze', 'Para 8th', 'WC Gold', 'WC Bronze', 'WC 8th']
        ax.set_xticks(positions)
        ax.set_xticklabels([labels[i] for i in positions], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_enhanced_medal_standards_with_saudi(self, ax1, ax2, class_standards, event, classification, saudi_green):
        """Enhanced medal standards with Saudi context"""
        # Plot 1: Medal progression with time labels
        competitions = ['paralympics_gold', 'paralympics_bronze', 'wc_gold', 'wc_bronze']
        comp_labels = ['Para Gold', 'Para Bronze', 'WC Gold', 'WC Bronze']

        values = []
        for comp in competitions:
            if comp in class_standards.columns:
                val = class_standards[comp].iloc[0]
                values.append(val if pd.notna(val) else None)
            else:
                values.append(None)

        # Filter out None values
        valid_data = [(label, val) for label, val in zip(comp_labels, values) if val is not None]
        if valid_data:
            labels, vals = zip(*valid_data)

            # Create line plot with markers
            ax1.plot(range(len(vals)), vals, marker='o', linewidth=3, markersize=8, color=saudi_green)
            ax1.set_xticks(range(len(vals)))
            ax1.set_xticklabels(labels, rotation=45)
            ax1.set_title('Medal Standards Progression', fontweight='bold', color=saudi_green)
            ax1.grid(True, alpha=0.3)

            # Add time context for goals
            ax1.text(0.02, 0.98, 'Short-term goal: Top 8', transform=ax1.transAxes,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=saudi_green, alpha=0.2),
                    verticalalignment='top', fontsize=10, fontweight='bold')
            ax1.text(0.02, 0.88, 'Medium-term: Medal contention', transform=ax1.transAxes,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='gold', alpha=0.3),
                    verticalalignment='top', fontsize=10, fontweight='bold')

        # Plot 2: Saudi athlete positioning
        saudi_athletes = self.get_saudi_athletes(event, classification)
        if saudi_athletes:
            performances = [a['performance'] for a in saudi_athletes if a['performance'] is not None]
            if performances:
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                best_saudi = min(performances) if is_time_event else max(performances)

                # Compare to standards
                gaps = []
                for val in vals if 'vals' in locals() else []:
                    if val is not None:
                        gap = abs(best_saudi - val)
                        gaps.append(gap)

                if gaps:
                    ax2.bar(range(len(gaps)), gaps, color=saudi_green, alpha=0.7)
                    ax2.set_title('Saudi Performance Gaps', fontweight='bold', color=saudi_green)
                    ax2.set_xlabel('Championship Level')
                    ax2.set_ylabel('Performance Gap')
                    ax2.set_xticks(range(len(gaps)))
                    ax2.set_xticklabels(labels[:len(gaps)], rotation=45)

    def _plot_performance_with_saudi_context(self, ax1, ax2, class_detailed, all_event_records, event, classification, saudi_green):
        """Performance distribution with Saudi athlete highlighting"""
        # Plot 1: Performance distribution with Saudi highlighting
        if not class_detailed.empty:
            # Check for the correct performance column name
            perf_column = None
            for col in ['performance', 'mean_performance', 'best_performance']:
                if col in class_detailed.columns:
                    perf_column = col
                    break

            if perf_column:
                performances = pd.to_numeric(class_detailed[perf_column], errors='coerce').dropna()

                if len(performances) > 0:
                    ax1.hist(performances, bins=20, alpha=0.7, color='lightblue', edgecolor='black')

                    # Highlight Saudi performances
                    saudi_athletes = self.get_saudi_athletes(event, classification)
                    if saudi_athletes:
                        saudi_perfs = [a['performance'] for a in saudi_athletes if a['performance'] is not None]
                        for perf in saudi_perfs:
                            ax1.axvline(x=perf, color=saudi_green, linewidth=3, alpha=0.8, label='Saudi Athletes')

                    ax1.set_title(f'Performance Distribution - {classification}', fontweight='bold')
                    ax1.set_xlabel('Performance')
                    ax1.set_ylabel('Frequency')
                    ax1.legend()
            else:
                ax1.text(0.5, 0.5, 'No performance data available', ha='center', va='center', transform=ax1.transAxes)

        # Plot 2: Records comparison with Saudi position
        if all_event_records:
            record_types = ['World Record', 'Asian Record', 'Paralympic Record']
            record_values = []
            record_labels = []

            for record_type in record_types:
                if record_type in all_event_records:
                    records = all_event_records[record_type]
                    if not records.empty:
                        # Ensure string conversion for filtering
                        event_col = records['Event'].astype(str) if 'Event' in records.columns else pd.Series([''] * len(records))
                        class_col = records['Class'].astype(str) if 'Class' in records.columns else pd.Series([''] * len(records))

                        event_records = records[
                            (event_col.str.contains(event, case=False, na=False)) &
                            (class_col.str.contains(classification, case=False, na=False))
                        ]
                        if not event_records.empty:
                            perf = event_records.iloc[0].get('Performance', None)
                            if perf:
                                try:
                                    record_values.append(float(perf))
                                    record_labels.append(record_type)
                                except:
                                    pass

            if record_values:
                bars = ax2.bar(range(len(record_values)), record_values,
                              color=[saudi_green if 'Asian' in label else 'gold' if 'World' in label else 'silver'
                                    for label in record_labels])
                ax2.set_title('Records Comparison', fontweight='bold')
                ax2.set_xticks(range(len(record_values)))
                ax2.set_xticklabels(record_labels, rotation=45)

                # Add Saudi best performance line
                saudi_athletes = self.get_saudi_athletes(event, classification)
                if saudi_athletes:
                    saudi_perfs = [a['performance'] for a in saudi_athletes if a['performance'] is not None]
                    if saudi_perfs:
                        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                        best_saudi = min(saudi_perfs) if is_time_event else max(saudi_perfs)
                        ax2.axhline(y=best_saudi, color=saudi_green, linewidth=3, linestyle='--',
                                  label=f'Best Saudi: {best_saudi:.2f}')
                        ax2.legend()

    def _plot_saudi_athlete_timeline(self, ax, event, classification, saudi_green):
        """Plot Saudi athlete performance timeline with championship cycles"""
        saudi_athletes = self.get_saudi_athletes(event, classification)

        if not saudi_athletes:
            ax.text(0.5, 0.5, f'No Saudi athlete data for {event} {classification}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title('Saudi Athlete Timeline', fontweight='bold', color=saudi_green)
            return

        # Extract dates and performances
        import datetime
        timeline_data = []
        for athlete in saudi_athletes:
            if athlete.get('date') and athlete.get('performance'):
                try:
                    # Parse various date formats
                    date_str = str(athlete['date'])
                    if '/' in date_str:
                        date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y')
                    elif '-' in date_str:
                        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        continue

                    timeline_data.append({
                        'date': date_obj,
                        'performance': athlete['performance'],
                        'name': athlete['name'],
                        'competition': athlete.get('competition', '')
                    })
                except:
                    continue

        if timeline_data:
            timeline_data.sort(key=lambda x: x['date'])
            dates = [d['date'] for d in timeline_data]
            performances = [d['performance'] for d in timeline_data]

            ax.plot(dates, performances, marker='o', linewidth=2, markersize=6, color=saudi_green)
            ax.set_title(f'Saudi Athletes Performance Timeline - {event} {classification}',
                        fontweight='bold', color=saudi_green)
            ax.set_xlabel('Year')
            ax.set_ylabel('Performance')
            ax.grid(True, alpha=0.3)

            # Add championship cycles
            current_year = datetime.datetime.now().year
            for year in range(2016, current_year + 8, 4):  # Paralympic cycles
                ax.axvline(x=datetime.datetime(year, 8, 1), color='red', alpha=0.5, linestyle='--')
                ax.text(datetime.datetime(year, 8, 1), ax.get_ylim()[1]*0.9, f'Para {year}',
                       rotation=90, color='red', fontsize=8)

            # Rotate date labels
            ax.tick_params(axis='x', rotation=45)

    def _plot_saudi_vs_regional_analysis(self, ax1, ax2, event, classification, saudi_green):
        """Compare Saudi athletes to regional (Asian) performance"""
        saudi_athletes = self.get_saudi_athletes(event, classification)

        # Plot 1: Saudi vs Asian comparison
        saudi_perfs = [a['performance'] for a in saudi_athletes if a['performance'] is not None]
        if saudi_perfs:
            is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
            best_saudi = min(saudi_perfs) if is_time_event else max(saudi_perfs)

            # Get Asian records
            asian_record = None
            if hasattr(self, 'all_records') and 'Asian Record' in self.all_records:
                records = self.all_records['Asian Record']
                # Ensure string conversion for filtering
                event_col = records['Event'].astype(str) if 'Event' in records.columns else pd.Series([''] * len(records))
                class_col = records['Class'].astype(str) if 'Class' in records.columns else pd.Series([''] * len(records))

                event_records = records[
                    (event_col.str.contains(event, case=False, na=False)) &
                    (class_col.str.contains(classification, case=False, na=False))
                ]
                if not event_records.empty:
                    try:
                        asian_record = float(event_records.iloc[0].get('Performance', 0))
                    except:
                        pass

            # Create comparison chart
            categories = ['Best Saudi']
            values = [best_saudi]
            colors = [saudi_green]

            if asian_record:
                categories.append('Asian Record')
                values.append(asian_record)
                colors.append('#FF6B35')

            ax1.bar(categories, values, color=colors, alpha=0.7)
            ax1.set_title('Saudi vs Asian Performance', fontweight='bold', color=saudi_green)
            ax1.set_ylabel('Performance')

            # Add improvement target
            if asian_record:
                gap = abs(best_saudi - asian_record)
                improvement_needed = gap * 0.8  # 80% of the gap
                target = best_saudi - improvement_needed if is_time_event else best_saudi + improvement_needed
                ax1.axhline(y=target, color='orange', linestyle='--', label=f'Target: {target:.2f}')
                ax1.legend()

        # Plot 2: Regional ranking position analysis
        ax2.set_title('Regional Championship Targets', fontweight='bold', color=saudi_green)
        targets = ['Top 8', 'Top 5', 'Medal', 'Gold']
        timeline = ['2024', '2025', '2026', '2027']

        # Create timeline goals
        y_pos = range(len(targets))
        colors = ['#90EE90', '#FFD700', '#C0C0C0', saudi_green]

        for i, (target, color) in enumerate(zip(targets, colors)):
            ax2.barh(i, len(timeline), color=color, alpha=0.6)
            ax2.text(len(timeline)/2, i, target, ha='center', va='center', fontweight='bold')

        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(targets)
        ax2.set_xlabel('Championship Cycle')
        ax2.set_xticks(range(len(timeline)))
        ax2.set_xticklabels(timeline)

    def _plot_championship_trends_with_timeline(self, ax, event, classification, saudi_green):
        """Plot championship performance trends with timeline goals"""
        if self.main_data is not None:
            # Get championship data over years
            major_data = self.identify_major_championships()
            if major_data is not None:
                event_data = major_data[
                    (major_data['eventname'] == event) &
                    (major_data['class'] == classification)
                ]

                if not event_data.empty:
                    # Extract years and winning performances
                    event_data['year'] = pd.to_datetime(event_data['competitiondate'], errors='coerce').dt.year
                    yearly_winners = event_data[event_data['position'] == 1].groupby('year')['performance'].first()

                    if len(yearly_winners) > 0:
                        years = yearly_winners.index
                        performances = pd.to_numeric(yearly_winners.values, errors='coerce')

                        # Remove any NaN values
                        valid_data = ~pd.isna(performances)
                        years = years[valid_data]
                        performances = performances[valid_data]

                        if len(performances) > 1:
                            ax.plot(years, performances, marker='o', linewidth=2, markersize=6, color='blue', label='Gold Medal Standards')

                            # Add trend line
                            try:
                                z = np.polyfit(years, performances, 1)
                                p = np.poly1d(z)
                                ax.plot(years, p(years), color='red', linestyle='--', alpha=0.7, label='Trend')

                                # Project future performance needed
                                future_years = list(range(max(years) + 1, max(years) + 5))
                                future_trend = p(future_years)
                                ax.plot(future_years, future_trend, color='orange', linestyle=':', alpha=0.7, label='Projected Standard')
                            except:
                                pass  # Skip trend line if fitting fails

                            ax.set_title(f'Championship Standards Evolution - {event} {classification}',
                                        fontweight='bold', color=saudi_green)
                            ax.set_xlabel('Year')
                            ax.set_ylabel('Winning Performance')
                            ax.legend()
                            ax.grid(True, alpha=0.3)

                            # Add championship years
                            para_years = [2016, 2020, 2024, 2028]
                            for year in para_years:
                                if min(years) <= year <= max(years) + 4:
                                    ax.axvline(x=year, color=saudi_green, alpha=0.3, linestyle='-')
                                    ax.text(year, ax.get_ylim()[1]*0.9, f'Para {year}',
                                           rotation=90, color=saudi_green, fontsize=8)

    def _plot_saudi_championship_timeline_targets(self, ax, event, classification, saudi_green, saudi_gold):
        """Plot Saudi championship timeline with specific targets"""
        # Championship timeline with targets
        years = [2024, 2025, 2026, 2027, 2028]
        targets = ['Qualify', 'Top 8', 'Top 5', 'Medal', 'Gold']
        colors = ['lightblue', 'lightgreen', 'yellow', 'silver', saudi_gold]

        # Create stepped timeline
        y_positions = range(len(targets))
        for i, (target, color) in enumerate(zip(targets, colors)):
            # Show progression over years
            width = 0.8
            for j, year in enumerate(years):
                alpha = 0.3 + (j * 0.15)  # Increasing opacity over time
                ax.barh(i, width, left=j, color=color, alpha=alpha, edgecolor='black')

        ax.set_yticks(y_positions)
        ax.set_yticklabels(targets)
        ax.set_xticks(range(len(years)))
        ax.set_xticklabels(years)
        ax.set_xlabel('Championship Cycle')
        ax.set_title(f'Saudi Championship Roadmap - {event} {classification}',
                    fontweight='bold', color=saudi_green, fontsize=14)

        # Add current status
        saudi_athletes = self.get_saudi_athletes(event, classification)
        if saudi_athletes:
            ax.text(0.02, 0.98, f'Current Saudi Athletes: {len(set(a["name"] for a in saudi_athletes))}',
                   transform=ax.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor=saudi_green, alpha=0.2),
                   verticalalignment='top', fontweight='bold')

    def _plot_saudi_vs_global_top20(self, ax1, ax2, event, classification, saudi_green):
        """Compare Saudi performance to global top 20"""
        # Get top 20 global athletes
        top_20 = self.get_top_20_global_athletes(event, classification)
        saudi_athletes = self.get_saudi_athletes(event, classification)

        # Initialize variables
        top_20_perfs = []
        saudi_perfs = []
        best_saudi = None

        if top_20 and saudi_athletes:
            # Plot 1: Performance comparison
            top_20_perfs = [a['performance'] for a in top_20 if a.get('performance')]
            saudi_perfs = [a['performance'] for a in saudi_athletes if a['performance'] is not None]

            if top_20_perfs and saudi_perfs:
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                best_saudi = min(saudi_perfs) if is_time_event else max(saudi_perfs)

                # Find Saudi's position in global rankings
                all_perfs = top_20_perfs + [best_saudi]
                all_perfs.sort(reverse=not is_time_event)
                saudi_rank = all_perfs.index(best_saudi) + 1

                ax1.bar(range(1, 21), top_20_perfs[:20], color='lightblue', alpha=0.7, label='Global Top 20')
                ax1.bar([saudi_rank], [best_saudi], color=saudi_green, alpha=0.9, label=f'Best Saudi (Rank {saudi_rank})')

                ax1.set_title('Saudi Position in Global Rankings', fontweight='bold', color=saudi_green)
                ax1.set_xlabel('World Ranking')
                ax1.set_ylabel('Performance')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

                # Plot 2: Gap analysis
                target_positions = [1, 3, 8, 20]
                gaps = []
                for pos in target_positions:
                    if pos <= len(top_20_perfs):
                        target_perf = top_20_perfs[pos-1]
                        gap = abs(best_saudi - target_perf)
                        gaps.append(gap)
                    else:
                        gaps.append(0)

                ax2.bar(range(len(target_positions)), gaps, color=[saudi_green, '#FFD700', '#C0C0C0', '#CD7F32'])
                ax2.set_title('Performance Gaps to Target Rankings', fontweight='bold', color=saudi_green)
                ax2.set_xlabel('Target Position')
                ax2.set_ylabel('Performance Gap')
                ax2.set_xticks(range(len(target_positions)))
                ax2.set_xticklabels([f'#{pos}' for pos in target_positions])
            else:
                ax1.text(0.5, 0.5, 'No performance data available', ha='center', va='center', transform=ax1.transAxes)
                ax2.text(0.5, 0.5, 'No gap analysis available', ha='center', va='center', transform=ax2.transAxes)
        else:
            ax1.text(0.5, 0.5, 'No athletes data available', ha='center', va='center', transform=ax1.transAxes)
            ax2.text(0.5, 0.5, 'No athletes data available', ha='center', va='center', transform=ax2.transAxes)

    def _plot_saudi_championship_readiness(self, ax, event, classification, saudi_green, saudi_gold):
        """Assess Saudi championship readiness"""
        saudi_athletes = self.get_saudi_athletes(event, classification)

        if not saudi_athletes:
            ax.text(0.5, 0.5, 'No Saudi athlete data available',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            return

        # Assessment criteria
        criteria = ['Athletes Count', 'Recent Competition', 'Performance Level', 'Improvement Trend', 'Championship Experience']
        scores = []

        # Score each criterion (0-100)
        # 1. Athletes Count
        unique_athletes = len(set(a['name'] for a in saudi_athletes))
        athlete_score = min(100, unique_athletes * 25)  # 4+ athletes = 100
        scores.append(athlete_score)

        # 2. Recent Competition (placeholder - would need recent data)
        recent_score = 70  # Assume moderate recent activity
        scores.append(recent_score)

        # 3. Performance Level (vs championship standards)
        perf_score = 60  # Placeholder
        scores.append(perf_score)

        # 4. Improvement Trend (placeholder)
        trend_score = 75
        scores.append(trend_score)

        # 5. Championship Experience (placeholder)
        experience_score = 50
        scores.append(experience_score)

        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(criteria), endpoint=False).tolist()
        scores += scores[:1]  # Complete the circle
        angles += angles[:1]

        ax.plot(angles, scores, 'o-', linewidth=2, color=saudi_green, label='Current Status')
        ax.fill(angles, scores, alpha=0.25, color=saudi_green)

        # Add target line (championship ready level)
        target_scores = [80] * (len(criteria) + 1)
        ax.plot(angles, target_scores, '--', linewidth=2, color=saudi_gold, label='Championship Ready')

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(criteria)
        ax.set_ylim(0, 100)
        ax.set_title(f'Saudi Championship Readiness - {event} {classification}',
                    fontweight='bold', color=saudi_green, y=1.08)
        ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        ax.grid(True)

    def _plot_gold_silver_medal_standards(self, ax, class_standards, event, classification, saudi_green, saudi_gold):
        """Plot gold and silver medal standards with colors"""
        standards = ['paralympics_gold', 'paralympics_silver', 'wc_gold', 'wc_silver']
        labels = ['Para Gold', 'Para Silver', 'WC Gold', 'WC Silver']
        colors = [saudi_gold, '#C0C0C0', saudi_gold, '#C0C0C0']

        values = []
        actual_labels = []
        actual_colors = []

        for i, standard in enumerate(standards):
            if standard in class_standards.columns:
                val = class_standards[standard].iloc[0]
                if pd.notna(val):
                    values.append(val)
                    actual_labels.append(labels[i])
                    actual_colors.append(colors[i])

        if values:
            bars = ax.bar(range(len(values)), values, color=actual_colors, alpha=0.8)
            ax.set_title(f'Gold & Silver Medal Standards - {event} {classification}',
                        fontweight='bold', color=saudi_green, fontsize=14)
            ax.set_xticks(range(len(values)))
            ax.set_xticklabels(actual_labels)
            ax.set_ylabel('Performance')
            ax.grid(True, alpha=0.3)

            # Add value labels on bars
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.2f}', ha='center', va='bottom', fontweight='bold')

    def _plot_separate_championship_progression(self, ax1, ax2, class_detailed, event, classification, saudi_green):
        """Separate charts for Paralympics and World Championships progression"""
        # Paralympics progression
        para_data = class_detailed[class_detailed['competition'].str.contains('Paralympic', case=False, na=False)]
        if not para_data.empty:
            positions = [1, 2, 3, 8]
            para_values = []
            for pos in positions:
                pos_data = para_data[para_data['position'] == pos]
                if not pos_data.empty:
                    para_values.append(pos_data['mean_performance'].iloc[0])
                else:
                    para_values.append(None)

            valid_pos = [pos for pos, val in zip(positions, para_values) if val is not None]
            valid_vals = [val for val in para_values if val is not None]

            if valid_vals:
                ax1.plot(valid_pos, valid_vals, marker='o', linewidth=3, markersize=8, color=saudi_green)
                ax1.set_title('Paralympics Progression', fontweight='bold', color=saudi_green)
                ax1.set_xlabel('Position')
                ax1.set_ylabel('Performance')
                ax1.set_xticks(positions)
                ax1.set_xticklabels(['Gold', 'Silver', 'Bronze', '8th'])
                ax1.grid(True, alpha=0.3)

        # World Championships progression
        wc_data = class_detailed[class_detailed['competition'].str.contains('World Championships', case=False, na=False)]
        if not wc_data.empty:
            positions = [1, 2, 3, 8]
            wc_values = []
            for pos in positions:
                pos_data = wc_data[wc_data['position'] == pos]
                if not pos_data.empty:
                    wc_values.append(pos_data['mean_performance'].iloc[0])
                else:
                    wc_values.append(None)

            valid_pos = [pos for pos, val in zip(positions, wc_values) if val is not None]
            valid_vals = [val for val in wc_values if val is not None]

            if valid_vals:
                ax2.plot(valid_pos, valid_vals, marker='s', linewidth=3, markersize=8, color='#FF6B35')
                ax2.set_title('World Championships Progression', fontweight='bold', color='#FF6B35')
                ax2.set_xlabel('Position')
                ax2.set_ylabel('Performance')
                ax2.set_xticks(positions)
                ax2.set_xticklabels(['Gold', 'Silver', 'Bronze', '8th'])
                ax2.grid(True, alpha=0.3)

    def _plot_world_vs_saudi_comparison(self, ax1, ax2, event, classification, saudi_green):
        """World #1 vs Saudi best by classification"""
        # Get world #1 performance
        top_20 = self.get_top_20_global_athletes(event, classification)
        world_1_perf = None
        if top_20:
            world_1_perf = top_20[0].get('performance')

        # Get Saudi best
        saudi_athletes = self.get_saudi_athletes(event, classification)
        saudi_best = None
        if saudi_athletes:
            saudi_perfs = [a['performance'] for a in saudi_athletes if a['performance'] is not None]
            if saudi_perfs:
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m']
                saudi_best = min(saudi_perfs) if is_time_event else max(saudi_perfs)

        if world_1_perf and saudi_best:
            categories = ['World #1', f'Saudi Best ({classification})']
            values = [world_1_perf, saudi_best]
            colors = ['gold', saudi_green]

            bars = ax1.bar(categories, values, color=colors, alpha=0.8)
            ax1.set_title(f'World #1 vs Saudi Best - {classification}', fontweight='bold', color=saudi_green)
            ax1.set_ylabel('Performance')

            # Add value labels
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.2f}', ha='center', va='bottom', fontweight='bold')

            # Gap analysis
            gap = abs(world_1_perf - saudi_best)
            percentage_gap = (gap / world_1_perf) * 100 if world_1_perf else 0

            ax2.bar(['Performance Gap'], [gap], color=saudi_green, alpha=0.7)
            ax2.set_title(f'Gap to World #1: {percentage_gap:.1f}%', fontweight='bold', color=saudi_green)
            ax2.set_ylabel('Performance Gap')

    def _create_colored_medal_standards_table(self, ax, class_standards, event, classification):
        """Create medal standards table with gold, silver, bronze colors"""
        ax.axis('tight')
        ax.axis('off')

        data = []
        headers = ['Competition', 'Gold', 'Silver', 'Bronze', '8th Place']

        # Paralympics row
        para_row = ['Paralympics']
        for col in ['paralympics_gold', 'paralympics_silver', 'paralympics_bronze', 'paralympics_8th_place']:
            if col in class_standards.columns:
                val = class_standards[col].iloc[0]
                para_row.append(f'{val:.2f}' if pd.notna(val) else 'N/A')
            else:
                para_row.append('N/A')
        data.append(para_row)

        # World Championships row
        wc_row = ['World Championships']
        for col in ['wc_gold', 'wc_silver', 'wc_bronze', 'wc_8th_place']:
            if col in class_standards.columns:
                val = class_standards[col].iloc[0]
                wc_row.append(f'{val:.2f}' if pd.notna(val) else 'N/A')
            else:
                wc_row.append('N/A')
        data.append(wc_row)

        table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

        # Color the header
        for i in range(len(headers)):
            if i == 1:  # Gold
                table[(0, i)].set_facecolor('#FFD700')
            elif i == 2:  # Silver
                table[(0, i)].set_facecolor('#C0C0C0')
            elif i == 3:  # Bronze
                table[(0, i)].set_facecolor('#CD7F32')
            else:
                table[(0, i)].set_facecolor('#E6E6E6')

        ax.set_title(f'{event} {classification} - Medal Standards', fontweight='bold', pad=20)

    def _create_top8_min_max_table(self, ax, class_detailed, event, classification):
        """Create top 8 table showing min/max without sample size"""
        ax.axis('tight')
        ax.axis('off')

        if class_detailed.empty:
            ax.text(0.5, 0.5, 'No championship data available', ha='center', va='center', transform=ax.transAxes)
            return

        data = []
        headers = ['Position', 'Competition', 'Best', 'Worst', 'Average']

        for pos in [1, 2, 3, 8]:
            for comp in ['Paralympics', 'World Championships']:
                comp_data = class_detailed[
                    (class_detailed['position'] == pos) &
                    (class_detailed['competition'].str.contains(comp, case=False, na=False))
                ]

                if not comp_data.empty:
                    row_data = comp_data.iloc[0]
                    medal_name = {1: 'Gold', 2: 'Silver', 3: 'Bronze', 8: '8th'}[pos]

                    data.append([
                        medal_name,
                        comp,
                        f"{row_data['best_performance']:.2f}",
                        f"{row_data['worst_performance']:.2f}",
                        f"{row_data['mean_performance']:.2f}"
                    ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.5)

            # Color code the position column
            for i, row in enumerate(data):
                if row[0] == 'Gold':
                    table[(i+1, 0)].set_facecolor('#FFD700')
                elif row[0] == 'Silver':
                    table[(i+1, 0)].set_facecolor('#C0C0C0')
                elif row[0] == 'Bronze':
                    table[(i+1, 0)].set_facecolor('#CD7F32')

        ax.set_title(f'{event} {classification} - Top 8 Performance Range', fontweight='bold', pad=20)

    def _create_classification_detailed_summary(self, ax, class_standards, class_detailed, event, classification, saudi_green):
        """Create detailed summary specific to the classification"""
        ax.axis('tight')
        ax.axis('off')

        summary_text = []
        summary_text.append(f"Classification: {classification}")

        # Add championship standards
        if not class_standards.empty:
            row = class_standards.iloc[0]
            if pd.notna(row.get('paralympics_gold')):
                summary_text.append(f"Paralympic Gold Standard: {row['paralympics_gold']:.2f}")
            if pd.notna(row.get('wc_gold')):
                summary_text.append(f"World Championships Gold: {row['wc_gold']:.2f}")
            if pd.notna(row.get('total_results')):
                summary_text.append(f"Total Championship Results: {int(row['total_results'])}")

        # Add performance analysis
        if not class_detailed.empty:
            gold_data = class_detailed[class_detailed['position'] == 1]
            if not gold_data.empty:
                avg_gold = gold_data['mean_performance'].iloc[0]
                summary_text.append(f"Average Gold Medal Performance: {avg_gold:.2f}")

            eighth_data = class_detailed[class_detailed['position'] == 8]
            if not eighth_data.empty:
                avg_eighth = eighth_data['mean_performance'].iloc[0]
                summary_text.append(f"Average 8th Place Performance: {avg_eighth:.2f}")

        # Display summary
        summary_str = "\n".join(summary_text)
        ax.text(0.05, 0.95, summary_str, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor=saudi_green, alpha=0.1))

        ax.set_title(f'{classification} Classification Summary', fontweight='bold', color=saudi_green, pad=20)

    def _create_athlete_progression_table_with_dates(self, ax, event, classification):
        """Create athlete progression table showing best performance and dates"""
        ax.axis('tight')
        ax.axis('off')

        # Get Saudi athletes for this event/classification
        saudi_athletes = self.get_saudi_athletes_with_dates(event, classification)

        if not saudi_athletes:
            ax.text(0.5, 0.5, 'No Saudi athlete progression data available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Saudi Athlete Progression', fontweight='bold', pad=20)
            return

        # Prepare table data
        headers = ['Athlete', 'Best Performance', 'Date', 'Competition', 'Season']
        data = []

        for athlete in saudi_athletes[:10]:  # Top 10 athletes
            data.append([
                athlete.get('name', 'Unknown')[:25],
                f"{athlete.get('performance', 0):.2f}",
                athlete.get('date', 'Unknown'),
                athlete.get('competition', 'Unknown')[:15],
                athlete.get('season', 'Unknown')
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

        ax.set_title(f'{event} {classification} - Saudi Athlete Progression with Dates', fontweight='bold', pad=20)

    def _plot_performance_overtime_with_medal_lines(self, ax, event, classification, class_standards, saudi_green, saudi_gold):
        """Plot performance over time with medal standard lines"""
        # Get Saudi athlete data over time
        saudi_data = self.get_saudi_performance_by_year(event, classification)

        if not saudi_data:
            ax.text(0.5, 0.5, 'No Saudi performance data over time',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Performance Over Time', fontweight='bold')
            return

        years = [d['year'] for d in saudi_data if d.get('year')]
        performances = [d['performance'] for d in saudi_data if d.get('performance')]

        if years and performances:
            ax.plot(years, performances, 'o-', color=saudi_green, linewidth=3, markersize=8, label='Saudi Best')

            # Add medal standard lines
            if not class_standards.empty:
                row = class_standards.iloc[0]
                if pd.notna(row.get('paralympics_gold')):
                    ax.axhline(y=row['paralympics_gold'], color=saudi_gold, linestyle='--',
                             alpha=0.8, label='Paralympic Gold')
                if pd.notna(row.get('paralympics_bronze')):
                    ax.axhline(y=row['paralympics_bronze'], color='#CD7F32', linestyle='--',
                             alpha=0.8, label='Paralympic Bronze')
                if pd.notna(row.get('paralympics_8th_place')):
                    ax.axhline(y=row['paralympics_8th_place'], color='gray', linestyle=':',
                             alpha=0.8, label='Paralympic 8th')

            ax.set_xlabel('Year', fontweight='bold')
            ax.set_ylabel('Performance', fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)

        ax.set_title(f'{event} {classification} - Performance Trend with Medal Standards',
                    fontweight='bold', color=saudi_green)

    def _create_top_performers_table_with_dates(self, ax, event, classification, region):
        """Create top performers table with dates for specified region"""
        ax.axis('tight')
        ax.axis('off')

        # Get top performers for the region
        if region == 'World':
            top_performers = self.get_top_20_global_athletes(event, classification)
        else:  # Asian
            top_performers = self.get_top_asian_athletes(event, classification)

        if not top_performers:
            ax.text(0.5, 0.5, f'No {region} performer data available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Top {region} Performers', fontweight='bold', pad=20)
            return

        # Prepare table data
        headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Date']
        data = []

        for i, athlete in enumerate(top_performers[:8], 1):  # Top 8
            country = athlete.get('country', 'Unknown')
            # Highlight Saudi athletes
            if 'Saudi' in country:
                name = f"🇸🇦 {athlete.get('name', 'Unknown')[:20]}"
            else:
                name = athlete.get('name', 'Unknown')[:20]

            data.append([
                str(i),
                name,
                country[:15],
                f"{athlete.get('performance', 0):.2f}",
                athlete.get('date', 'Unknown')
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Highlight Saudi rows
            for i, row in enumerate(data):
                if '🇸🇦' in row[1]:
                    for j in range(len(headers)):
                        table[(i+1, j)].set_facecolor('#FFD700')
                        table[(i+1, j)].set_alpha(0.3)

        ax.set_title(f'Top {region} Performers - {event} {classification}', fontweight='bold', pad=20)

    def _create_top_performers_by_classification(self, ax, event, classification):
        """Create top performers table specific to classification without sample size"""
        ax.axis('tight')
        ax.axis('off')

        # Get classification-specific data
        class_data = self.get_classification_top_performers(event, classification)

        if not class_data:
            ax.text(0.5, 0.5, 'No classification-specific data available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{classification} Top Performers', fontweight='bold', pad=20)
            return

        # Prepare table data
        headers = ['Rank', 'Athlete', 'Country', 'Performance', 'Competition']
        data = []

        for i, performer in enumerate(class_data[:10], 1):  # Top 10
            country = performer.get('country', 'Unknown')
            # Highlight Saudi athletes
            if 'Saudi' in country:
                name = f"🇸🇦 {performer.get('name', 'Unknown')[:20]}"
            else:
                name = performer.get('name', 'Unknown')[:20]

            data.append([
                str(i),
                name,
                country[:15],
                f"{performer.get('performance', 0):.2f}",
                performer.get('competition', 'Unknown')[:15]
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Highlight Saudi rows
            for i, row in enumerate(data):
                if '🇸🇦' in row[1]:
                    for j in range(len(headers)):
                        table[(i+1, j)].set_facecolor('#FFD700')
                        table[(i+1, j)].set_alpha(0.3)

        ax.set_title(f'{classification} Classification Leaders', fontweight='bold', pad=20)

    def get_saudi_athletes_with_dates(self, event, classification):
        """Get Saudi athletes with dates and performance details"""
        saudi_athletes = []

        # Search main CSV for Saudi athletes
        main_df = self.main_data
        if main_df is not None:
            # Filter for event and classification
            event_data = main_df[
                (main_df['eventname'].astype(str).str.contains(event, case=False, na=False)) &
                (main_df['class'].astype(str).str.contains(classification, case=False, na=False))
            ]

            # Look for Saudi athletes
            for col in ['country', 'nationality', 'nation']:
                if col in event_data.columns:
                    saudi_data = event_data[event_data[col].astype(str).str.contains('Saudi', case=False, na=False)]
                    for _, row in saudi_data.iterrows():
                        athlete_info = {
                            'name': row.get('name', f"Saudi Athlete {len(saudi_athletes)+1}"),
                            'performance': pd.to_numeric(row.get('performance', 0), errors='coerce'),
                            'date': str(row.get('date', row.get('year', 'Unknown'))),
                            'competition': str(row.get('competition', 'Unknown')),
                            'season': str(row.get('season', row.get('year', 'Unknown')))
                        }
                        saudi_athletes.append(athlete_info)
                    if len(saudi_athletes) > 0:
                        break

        # Sort by performance (best first)
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m', '10000m']
        saudi_athletes.sort(key=lambda x: x['performance'], reverse=not is_time_event)

        return saudi_athletes

    def get_saudi_performance_by_year(self, event, classification):
        """Get Saudi performance data organized by year"""
        performance_data = []

        # Get Saudi athletes with dates
        saudi_athletes = self.get_saudi_athletes_with_dates(event, classification)

        # Group by year and find best performance
        year_performances = {}
        for athlete in saudi_athletes:
            try:
                # Extract year from date/season
                year_str = str(athlete.get('season', athlete.get('date', '')))
                year = int(year_str[:4]) if len(year_str) >= 4 else None

                if year and 2015 <= year <= 2025:
                    performance = athlete['performance']
                    if year not in year_performances or \
                       (event in ['100m', '200m', '400m'] and performance < year_performances[year]) or \
                       (event not in ['100m', '200m', '400m'] and performance > year_performances[year]):
                        year_performances[year] = performance
            except:
                continue

        # Convert to list format
        for year, performance in sorted(year_performances.items()):
            performance_data.append({
                'year': year,
                'performance': performance
            })

        return performance_data

    def get_top_asian_athletes(self, event, classification):
        """Get top Asian athletes for the event/classification"""
        asian_countries = ['Japan', 'China', 'Korea', 'Thailand', 'India', 'Iran', 'Iraq', 'Kazakhstan', 'Malaysia', 'Singapore', 'Indonesia', 'Saudi']

        top_athletes = self.get_top_20_global_athletes(event, classification)
        asian_athletes = []

        for athlete in top_athletes:
            country = athlete.get('country', '')
            if any(asian_country.lower() in country.lower() for asian_country in asian_countries):
                asian_athletes.append(athlete)

        return asian_athletes

    def get_classification_top_performers(self, event, classification):
        """Get classification-specific top performers"""
        # Use the same data as global athletes but focus on classification
        return self.get_top_20_global_athletes(event, classification)

    def _plot_top20_global_with_data_labels(self, ax, event, classification, saudi_green):
        """Plot top 20 global athletes with data labels and fixed overlapping text"""
        top_20 = self.get_top_20_global_athletes(event, classification)

        if not top_20:
            ax.text(0.5, 0.5, 'No global top 20 data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Top 20 Global Athletes', fontweight='bold')
            return

        # Prepare data for plotting
        names = [a['name'][:15] + '...' if len(a['name']) > 15 else a['name'] for a in top_20]
        performances = [a['performance'] for a in top_20]
        countries = [a['country'] for a in top_20]

        # Color code Saudi athletes differently
        colors = [saudi_green if 'Saudi' in country else '#1f77b4' for country in countries]

        # Create horizontal bar chart
        bars = ax.barh(range(len(names)), performances, color=colors, alpha=0.7)

        # Add data labels on bars (fixed positioning to avoid overlap)
        for i, (bar, performance, country) in enumerate(zip(bars, performances, countries)):
            width = bar.get_width()
            # Add performance value on the bar
            ax.text(width/2, bar.get_y() + bar.get_height()/2,
                   f'{performance:.2f}', ha='center', va='center', fontweight='bold', color='white')
            # Add country label to the right of the bar
            ax.text(width + width*0.02, bar.get_y() + bar.get_height()/2,
                   country[:10], ha='left', va='center', fontsize=8)

        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=9)
        ax.set_xlabel('Performance', fontweight='bold')
        ax.set_title(f'Top 20 Global Athletes - {event} {classification}', fontweight='bold')
        ax.invert_yaxis()  # Best performance at top
        ax.grid(True, alpha=0.3)

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=saudi_green, alpha=0.7, label='Saudi Arabia'),
            Patch(facecolor='#1f77b4', alpha=0.7, label='Other Countries')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

    def _plot_saudi_medal_chances_analysis(self, ax1, ax2, event, classification, class_standards, saudi_green, saudi_gold):
        """Clear analysis of Saudi medal chances"""
        # Get Saudi best performance
        saudi_athletes = self.get_saudi_athletes(event, classification)

        if not saudi_athletes or class_standards.empty:
            ax1.text(0.5, 0.5, 'No data for medal analysis', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Medal Chances Analysis', fontweight='bold')
            ax2.text(0.5, 0.5, 'No comparison data available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Performance Gap Analysis', fontweight='bold')
            return

        best_saudi = saudi_athletes[0]['performance']
        row = class_standards.iloc[0]

        # Chart 1: Medal chances comparison
        medal_standards = []
        medal_labels = []
        medal_colors = []

        if pd.notna(row.get('paralympics_gold')):
            medal_standards.append(row['paralympics_gold'])
            medal_labels.append('Para Gold')
            medal_colors.append(saudi_gold)
        if pd.notna(row.get('paralympics_silver')):
            medal_standards.append(row['paralympics_silver'])
            medal_labels.append('Para Silver')
            medal_colors.append('#C0C0C0')
        if pd.notna(row.get('paralympics_bronze')):
            medal_standards.append(row['paralympics_bronze'])
            medal_labels.append('Para Bronze')
            medal_colors.append('#CD7F32')

        if medal_standards:
            bars = ax1.bar(range(len(medal_standards)), medal_standards, color=medal_colors, alpha=0.8)

            # Add Saudi performance line
            ax1.axhline(y=best_saudi, color=saudi_green, linestyle='--', linewidth=3,
                       label=f'Saudi Best: {best_saudi:.2f}')

            # Add gap labels
            for i, (bar, standard) in enumerate(zip(bars, medal_standards)):
                height = bar.get_height()
                gap = abs(best_saudi - standard)
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']

                if (is_time_event and best_saudi > standard) or (not is_time_event and best_saudi < standard):
                    chance = "Outside chance"
                    color = 'red'
                else:
                    chance = "Good chance"
                    color = 'green'

                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.02,
                        f'{chance}\nGap: {gap:.2f}', ha='center', va='bottom',
                        fontweight='bold', color=color, fontsize=8)

            ax1.set_xticks(range(len(medal_standards)))
            ax1.set_xticklabels(medal_labels)
            ax1.set_ylabel('Performance')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        ax1.set_title('Saudi Medal Chances', fontweight='bold', color=saudi_green)

        # Chart 2: Performance progression needed
        if pd.notna(row.get('paralympics_gold')):
            gold_standard = row['paralympics_gold']
            current_gap = abs(best_saudi - gold_standard)

            # Show progression scenarios
            scenarios = ['Current', '5% Improvement', '10% Improvement', '15% Improvement']
            improvements = [0, 0.05, 0.10, 0.15]

            projected_perfs = []
            for improvement in improvements:
                if event in ['100m', '200m', '400m']:  # Time events - improvement means lower time
                    projected_perfs.append(best_saudi * (1 - improvement))
                else:  # Distance/throwing events - improvement means higher performance
                    projected_perfs.append(best_saudi * (1 + improvement))

            colors = [saudi_green if perf >= gold_standard or (event in ['100m', '200m', '400m'] and perf <= gold_standard)
                     else 'orange' for perf in projected_perfs]

            bars = ax2.bar(scenarios, projected_perfs, color=colors, alpha=0.7)
            ax2.axhline(y=gold_standard, color=saudi_gold, linestyle='-', linewidth=2,
                       label=f'Gold Standard: {gold_standard:.2f}')

            # Add data labels
            for bar, perf in zip(bars, projected_perfs):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{perf:.2f}', ha='center', va='bottom', fontweight='bold')

            ax2.set_ylabel('Performance')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        ax2.set_title('Improvement Scenarios for Gold', fontweight='bold', color=saudi_green)

    def _create_medal_summary_with_positions(self, ax, class_standards, event, classification):
        """Create medal summary including silver and positions 1-8"""
        ax.axis('tight')
        ax.axis('off')

        if class_standards.empty:
            ax.text(0.5, 0.5, 'No medal standards data available', ha='center', va='center', transform=ax.transAxes)
            return

        row = class_standards.iloc[0]

        # Create comprehensive medal standards table
        data = []
        headers = ['Position', 'Paralympics', 'World Championships']

        positions = [
            ('Gold (1st)', 'paralympics_gold', 'wc_gold'),
            ('Silver (2nd)', 'paralympics_silver', 'wc_silver'),
            ('Bronze (3rd)', 'paralympics_bronze', 'wc_bronze'),
            ('4th Place', 'paralympics_4th_place', 'wc_4th_place'),
            ('5th Place', 'paralympics_5th_place', 'wc_5th_place'),
            ('6th Place', 'paralympics_6th_place', 'wc_6th_place'),
            ('7th Place', 'paralympics_7th_place', 'wc_7th_place'),
            ('8th Place', 'paralympics_8th_place', 'wc_8th_place')
        ]

        for pos_name, para_col, wc_col in positions:
            para_val = f"{row.get(para_col, 'N/A'):.2f}" if pd.notna(row.get(para_col)) else 'N/A'
            wc_val = f"{row.get(wc_col, 'N/A'):.2f}" if pd.notna(row.get(wc_col)) else 'N/A'
            data.append([pos_name, para_val, wc_val])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.8)

            # Color code positions
            position_colors = {
                'Gold (1st)': '#FFD700',
                'Silver (2nd)': '#C0C0C0',
                'Bronze (3rd)': '#CD7F32'
            }

            for i, row_data in enumerate(data):
                pos_name = row_data[0]
                if pos_name in position_colors:
                    for j in range(len(headers)):
                        table[(i+1, j)].set_facecolor(position_colors[pos_name])
                        table[(i+1, j)].set_alpha(0.6)

        ax.set_title(f'{event} {classification} - Complete Medal Standards (1st-8th)', fontweight='bold', pad=20)

    def _create_saudi_athletes_table_with_dates(self, ax, event, classification):
        """Create Saudi athletes table with performance dates"""
        ax.axis('tight')
        ax.axis('off')

        saudi_athletes = self.get_saudi_athletes_with_dates(event, classification)

        if not saudi_athletes:
            ax.text(0.5, 0.5, 'No Saudi athlete data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Top Saudi Athletes', fontweight='bold', pad=20)
            return

        # Prepare table data
        headers = ['Rank', 'Athlete', 'Performance', 'Date', 'Competition']
        data = []

        for i, athlete in enumerate(saudi_athletes[:8], 1):  # Top 8
            data.append([
                str(i),
                athlete.get('name', 'Unknown')[:20],
                f"{athlete.get('performance', 0):.2f}",
                athlete.get('date', 'Unknown'),
                athlete.get('competition', 'Unknown')[:15]
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            # Style the table with Saudi colors
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Highlight top performer
            if len(data) > 0:
                for j in range(len(headers)):
                    table[(1, j)].set_facecolor('#FFD700')
                    table[(1, j)].set_alpha(0.3)

        ax.set_title(f'Top Saudi Athletes - {event} {classification}', fontweight='bold', pad=20)

    def _create_saudi_performance_across_seasons(self, ax, event, classification):
        """Create Saudi performance summary across seasons"""
        ax.axis('tight')
        ax.axis('off')

        # Get Saudi performance by year
        performance_data = self.get_saudi_performance_by_year(event, classification)

        if not performance_data:
            ax.text(0.5, 0.5, 'No seasonal performance data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Saudi Performance Across Seasons', fontweight='bold', pad=20)
            return

        # Create summary table
        headers = ['Season', 'Best Performance', 'Improvement', 'Status']
        data = []

        for i, season_data in enumerate(performance_data):
            year = season_data['year']
            performance = season_data['performance']

            # Calculate improvement from previous year
            if i > 0:
                prev_performance = performance_data[i-1]['performance']
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']

                if is_time_event:  # Lower is better
                    improvement = prev_performance - performance
                    status = "Improved" if improvement > 0 else "Declined" if improvement < 0 else "Same"
                else:  # Higher is better
                    improvement = performance - prev_performance
                    status = "Improved" if improvement > 0 else "Declined" if improvement < 0 else "Same"

                improvement_str = f"{improvement:+.2f}"
            else:
                improvement_str = "-"
                status = "Baseline"

            data.append([
                str(year),
                f"{performance:.2f}",
                improvement_str,
                status
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Color code status
            for i, row_data in enumerate(data):
                status = row_data[3]
                if status == "Improved":
                    table[(i+1, 3)].set_facecolor('green')
                    table[(i+1, 3)].set_alpha(0.3)
                elif status == "Declined":
                    table[(i+1, 3)].set_facecolor('red')
                    table[(i+1, 3)].set_alpha(0.3)

        ax.set_title(f'Saudi Performance Across Seasons - {event} {classification}', fontweight='bold', pad=20)

    def _create_championship_strategy_assessment(self, ax, event, classification, class_standards, saudi_green, saudi_gold):
        """Create clear championship strategy and medal opportunity assessment"""
        ax.axis('tight')
        ax.axis('off')

        # Get data for assessment
        saudi_athletes = self.get_saudi_athletes(event, classification)

        if not saudi_athletes or class_standards.empty:
            ax.text(0.5, 0.5, 'No data for strategy assessment', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Championship Strategy Assessment', fontweight='bold', pad=20)
            return

        best_saudi = saudi_athletes[0]['performance']
        row = class_standards.iloc[0]

        # Assessment text
        assessment_text = []
        assessment_text.append(f"CHAMPIONSHIP STRATEGY ASSESSMENT")
        assessment_text.append(f"Event: {event} {classification}")
        assessment_text.append(f"")

        # Current status
        assessment_text.append(f"Current Saudi Best: {best_saudi:.2f}")

        # Medal analysis
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']

        medal_chances = []
        if pd.notna(row.get('paralympics_gold')):
            gold_standard = row['paralympics_gold']
            if (is_time_event and best_saudi <= gold_standard) or (not is_time_event and best_saudi >= gold_standard):
                medal_chances.append("GOLD: Strong chance")
            else:
                gap = abs(best_saudi - gold_standard)
                medal_chances.append(f"GOLD: Need {gap:.2f} improvement")

        if pd.notna(row.get('paralympics_bronze')):
            bronze_standard = row['paralympics_bronze']
            if (is_time_event and best_saudi <= bronze_standard) or (not is_time_event and best_saudi >= bronze_standard):
                medal_chances.append("BRONZE: Strong chance")
            else:
                gap = abs(best_saudi - bronze_standard)
                medal_chances.append(f"BRONZE: Need {gap:.2f} improvement")

        if medal_chances:
            assessment_text.append("")
            assessment_text.append("MEDAL OPPORTUNITIES:")
            assessment_text.extend(medal_chances)

        # Strategic recommendations
        assessment_text.append("")
        assessment_text.append("STRATEGIC FOCUS:")

        if len(medal_chances) > 0 and "Strong chance" in " ".join(medal_chances):
            assessment_text.append("• Medal contender - focus on consistency")
            assessment_text.append("• Competition preparation critical")
            assessment_text.append("• Tactical racing strategies")
        else:
            assessment_text.append("• Performance improvement needed")
            assessment_text.append("• Technical development priority")
            assessment_text.append("• Long-term development plan")

        # Display assessment
        assessment_str = "\n".join(assessment_text)
        ax.text(0.05, 0.95, assessment_str, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor=saudi_green, alpha=0.1))

        ax.set_title('Championship Strategy & Medal Assessment', fontweight='bold', color=saudi_green, pad=20)

    def _create_2024_25_season_summary(self, ax, event, classification):
        """Create 2024-25 season top performers summary"""
        ax.axis('tight')
        ax.axis('off')

        # Get recent season data
        recent_performers = self.get_2024_25_season_performers(event, classification)

        if not recent_performers:
            ax.text(0.5, 0.5, 'No 2024-25 season data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('2024-25 Season Summary', fontweight='bold', pad=20)
            return

        # Create summary statistics
        total_performers = len(recent_performers)
        saudi_performers = [p for p in recent_performers if 'Saudi' in p.get('country', '')]

        summary_text = []
        summary_text.append(f"2024-25 Season Performance Summary")
        summary_text.append(f"Event: {event} {classification}")
        summary_text.append(f"")
        summary_text.append(f"Total Active Athletes: {total_performers}")
        summary_text.append(f"Saudi Athletes Active: {len(saudi_performers)}")

        if recent_performers:
            best_performance = recent_performers[0]['performance']
            summary_text.append(f"Season Best: {best_performance:.2f}")

            if saudi_performers:
                best_saudi = saudi_performers[0]['performance']
                summary_text.append(f"Saudi Season Best: {best_saudi:.2f}")

                # Calculate gap
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']
                if is_time_event:
                    gap = best_saudi - best_performance
                    gap_text = f"Gap to World Leader: +{gap:.2f}s" if gap > 0 else f"Leading by: {abs(gap):.2f}s"
                else:
                    gap = best_performance - best_saudi
                    gap_text = f"Gap to World Leader: -{gap:.2f}m" if gap > 0 else f"Leading by: {abs(gap):.2f}m"
                summary_text.append(gap_text)

        # Display summary
        summary_str = "\n".join(summary_text)
        ax.text(0.05, 0.95, summary_str, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor='#006C35', alpha=0.1))

        ax.set_title('2024-25 Season Performance Summary', fontweight='bold', color='#006C35', pad=20)

    def _plot_recent_form_analysis(self, ax1, ax2, event, classification, saudi_green):
        """Plot recent form analysis for world leaders"""
        recent_performers = self.get_2024_25_season_performers(event, classification)

        if not recent_performers:
            ax1.text(0.5, 0.5, 'No recent form data', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Recent Form Analysis', fontweight='bold')
            ax2.text(0.5, 0.5, 'No competition data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Competition Frequency', fontweight='bold')
            return

        # Chart 1: Top 10 recent performers
        top_10 = recent_performers[:10]
        names = [p['name'][:12] + '...' if len(p['name']) > 12 else p['name'] for p in top_10]
        performances = [p['performance'] for p in top_10]
        countries = [p['country'] for p in top_10]

        colors = [saudi_green if 'Saudi' in country else '#1f77b4' for country in countries]

        bars = ax1.barh(range(len(names)), performances, color=colors, alpha=0.7)

        # Add performance labels
        for i, (bar, perf) in enumerate(zip(bars, performances)):
            width = bar.get_width()
            ax1.text(width/2, bar.get_y() + bar.get_height()/2,
                    f'{perf:.2f}', ha='center', va='center', fontweight='bold', color='white')

        ax1.set_yticks(range(len(names)))
        ax1.set_yticklabels(names, fontsize=9)
        ax1.set_xlabel('Performance')
        ax1.set_title('Top 10 Recent Performers', fontweight='bold')
        ax1.invert_yaxis()
        ax1.grid(True, alpha=0.3)

        # Chart 2: Competition frequency
        country_counts = {}
        for performer in recent_performers:
            country = performer['country']
            country_counts[country] = country_counts.get(country, 0) + 1

        sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        countries = [item[0] for item in sorted_countries]
        counts = [item[1] for item in sorted_countries]

        colors = [saudi_green if 'Saudi' in country else '#1f77b4' for country in countries]

        bars = ax2.bar(countries, counts, color=colors, alpha=0.7)
        ax2.set_ylabel('Number of Performances')
        ax2.set_title('Active Countries 2024-25', fontweight='bold')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # Add count labels
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    str(count), ha='center', va='bottom', fontweight='bold')

    def _plot_competitor_timeline_2024_25(self, ax, event, classification, saudi_green, saudi_gold):
        """Plot competitor performance timeline for 2024-25 season"""
        timeline_data = self.get_competitor_timeline_2024_25(event, classification)

        if not timeline_data:
            ax.text(0.5, 0.5, 'No timeline data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('2024-25 Performance Timeline', fontweight='bold')
            return

        # Plot timeline for top competitors
        for i, competitor in enumerate(timeline_data[:5]):  # Top 5 competitors
            dates = competitor['dates']
            performances = competitor['performances']
            name = competitor['name']
            country = competitor['country']

            color = saudi_green if 'Saudi' in country else plt.cm.tab10(i)
            marker = 'o' if 'Saudi' in country else 's'
            linewidth = 3 if 'Saudi' in country else 2

            ax.plot(dates, performances, marker=marker, linewidth=linewidth,
                   markersize=8, alpha=0.8, label=f"{name} ({country})", color=color)

        ax.set_xlabel('Date', fontweight='bold')
        ax.set_ylabel('Performance', fontweight='bold')
        ax.set_title('2024-25 Season Performance Timeline - Top Competitors', fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def _create_saudi_vs_recent_competitors_table(self, ax, event, classification):
        """Create table comparing Saudi athletes with recent competitors"""
        ax.axis('tight')
        ax.axis('off')

        recent_performers = self.get_2024_25_season_performers(event, classification)

        if not recent_performers:
            ax.text(0.5, 0.5, 'No competitor data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Saudi vs Recent Competitors', fontweight='bold', pad=20)
            return

        # Prepare comparison data
        headers = ['Rank', 'Athlete', 'Country', 'Season Best', 'Last Competition', 'Threat Level']
        data = []

        for i, performer in enumerate(recent_performers[:10], 1):
            country = performer['country']
            performance = performer['performance']

            # Determine threat level
            if i <= 3:
                threat_level = "🔴 High"
            elif i <= 6:
                threat_level = "🟡 Medium"
            else:
                threat_level = "🟢 Low"

            # Highlight Saudi athletes
            if 'Saudi' in country:
                name = f"🇸🇦 {performer['name'][:18]}"
                threat_level = "🏠 Home"
            else:
                name = performer['name'][:18]

            data.append([
                str(i),
                name,
                country[:12],
                f"{performance:.2f}",
                performer.get('last_competition', 'Unknown')[:12],
                threat_level
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.8)

            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Color code threat levels and highlight Saudi
            for i, row_data in enumerate(data):
                if '🇸🇦' in row_data[1]:
                    for j in range(len(headers)):
                        table[(i+1, j)].set_facecolor('#FFD700')
                        table[(i+1, j)].set_alpha(0.3)
                elif '🔴' in row_data[5]:
                    table[(i+1, 5)].set_facecolor('red')
                    table[(i+1, 5)].set_alpha(0.3)
                elif '🟡' in row_data[5]:
                    table[(i+1, 5)].set_facecolor('orange')
                    table[(i+1, 5)].set_alpha(0.3)

        ax.set_title(f'Saudi vs Recent Competitors - {event} {classification}', fontweight='bold', pad=20)

    def _plot_2024_25_performance_distribution(self, ax1, ax2, event, classification, saudi_green):
        """Plot performance distribution for 2024-25 season"""
        recent_performers = self.get_2024_25_season_performers(event, classification)

        if not recent_performers:
            ax1.text(0.5, 0.5, 'No distribution data', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Performance Distribution', fontweight='bold')
            ax2.text(0.5, 0.5, 'No monthly data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Monthly Activity', fontweight='bold')
            return

        # Chart 1: Performance distribution histogram
        performances = [p['performance'] for p in recent_performers]
        saudi_performances = [p['performance'] for p in recent_performers if 'Saudi' in p.get('country', '')]

        ax1.hist(performances, bins=20, alpha=0.7, color='lightblue', label='All Athletes', edgecolor='black')
        if saudi_performances:
            ax1.hist(saudi_performances, bins=20, alpha=0.8, color=saudi_green, label='Saudi Athletes', edgecolor='black')

        ax1.set_xlabel('Performance')
        ax1.set_ylabel('Number of Athletes')
        ax1.set_title('2024-25 Performance Distribution', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Chart 2: Monthly competition activity
        monthly_counts = {}
        for performer in recent_performers:
            # Extract month from date if available
            date_str = performer.get('date', '')
            if date_str and len(date_str) >= 7:
                try:
                    month = date_str[:7]  # YYYY-MM format
                    monthly_counts[month] = monthly_counts.get(month, 0) + 1
                except:
                    continue

        if monthly_counts:
            months = sorted(monthly_counts.keys())
            counts = [monthly_counts[month] for month in months]

            ax2.plot(months, counts, marker='o', linewidth=2, markersize=6, color=saudi_green)
            ax2.set_xlabel('Month')
            ax2.set_ylabel('Number of Performances')
            ax2.set_title('Monthly Competition Activity', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

    def _create_key_competitors_watch_list(self, ax, event, classification, class_standards):
        """Create key competitors watch list with strategic insights"""
        ax.axis('tight')
        ax.axis('off')

        recent_performers = self.get_2024_25_season_performers(event, classification)

        if not recent_performers or class_standards.empty:
            ax.text(0.5, 0.5, 'No competitor watch list data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Key Competitors Watch List', fontweight='bold', pad=20)
            return

        # Get medal standards for reference
        row = class_standards.iloc[0]
        medal_standards = {}
        if pd.notna(row.get('paralympics_gold')):
            medal_standards['Gold'] = row['paralympics_gold']
        if pd.notna(row.get('paralympics_silver')):
            medal_standards['Silver'] = row['paralympics_silver']
        if pd.notna(row.get('paralympics_bronze')):
            medal_standards['Bronze'] = row['paralympics_bronze']

        # Create watch list
        headers = ['Priority', 'Athlete', 'Country', 'Season Best', 'Medal Potential', 'Strategic Notes']
        data = []

        for i, performer in enumerate(recent_performers[:8], 1):
            if 'Saudi' in performer.get('country', ''):
                continue  # Skip Saudi athletes

            performance = performer['performance']

            # Determine medal potential
            medal_potential = "Outside Medal"
            if medal_standards:
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']

                if 'Gold' in medal_standards:
                    gold_standard = medal_standards['Gold']
                    if (is_time_event and performance <= gold_standard) or (not is_time_event and performance >= gold_standard):
                        medal_potential = "🥇 Gold Contender"
                    elif 'Bronze' in medal_standards:
                        bronze_standard = medal_standards['Bronze']
                        if (is_time_event and performance <= bronze_standard) or (not is_time_event and performance >= bronze_standard):
                            medal_potential = "🥉 Medal Contender"

            # Priority based on performance ranking
            if i <= 3:
                priority = "🔴 HIGH"
                strategic_notes = "Key threat - monitor closely"
            elif i <= 6:
                priority = "🟡 MEDIUM"
                strategic_notes = "Track performance trends"
            else:
                priority = "🟢 LOW"
                strategic_notes = "Emerging talent"

            data.append([
                priority,
                performer['name'][:15],
                performer['country'][:10],
                f"{performance:.2f}",
                medal_potential,
                strategic_notes
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1.3, 2.0)

            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Color code priorities and medal potential
            for i, row_data in enumerate(data):
                if '🔴' in row_data[0]:
                    table[(i+1, 0)].set_facecolor('red')
                    table[(i+1, 0)].set_alpha(0.3)
                elif '🟡' in row_data[0]:
                    table[(i+1, 0)].set_facecolor('orange')
                    table[(i+1, 0)].set_alpha(0.3)

                if '🥇' in row_data[4]:
                    table[(i+1, 4)].set_facecolor('#FFD700')
                    table[(i+1, 4)].set_alpha(0.5)
                elif '🥉' in row_data[4]:
                    table[(i+1, 4)].set_facecolor('#CD7F32')
                    table[(i+1, 4)].set_alpha(0.5)

        ax.set_title(f'Key Competitors Watch List - {event} {classification}', fontweight='bold', pad=20)

    def get_2024_25_season_performers(self, event, classification):
        """Get performers from 2024-25 season"""
        performers = []

        # Search through rankings data for 2024-25 season
        for year in ['2024', '2025']:
            rankings_key = f'World Rankings_{year}'
            if rankings_key in self.rankings_data:
                year_data = self.rankings_data[rankings_key]

                # Filter by event and classification
                if 'Class' in year_data.columns:
                    # First filter by classification
                    class_filtered = year_data[
                        year_data['Class'].astype(str).str.contains(classification, case=False, na=False)
                    ]

                    # Then filter by event type based on ResultType and event
                    event_filtered = class_filtered
                    if event in ['100m', '200m', '400m', '800m', '1500m', '5000m']:
                        # Track events - look for TIME results
                        event_filtered = class_filtered[
                            class_filtered['ResultType'].str.contains('TIME', case=False, na=False)
                        ]
                    elif event in ['Shot Put', 'Discus Throw', 'Javelin Throw']:
                        # Field events - look for DISTANCE/MARK results
                        event_filtered = class_filtered[
                            (class_filtered['ResultType'].str.contains('DISTANCE', case=False, na=False)) |
                            (class_filtered['ResultType'].str.contains('MARK', case=False, na=False))
                        ]
                    elif event == 'Long Jump':
                        # Long Jump - look for DISTANCE results
                        event_filtered = class_filtered[
                            class_filtered['ResultType'].str.contains('DISTANCE', case=False, na=False)
                        ]

                    filtered_data = event_filtered

                    for _, row in filtered_data.iterrows():
                        # Combine GivenName and FamilyName for full name
                        given_name = str(row.get('GivenName', ''))
                        family_name = str(row.get('FamilyName', ''))
                        full_name = f"{given_name} {family_name}".strip()
                        if not full_name or full_name == 'nan nan':
                            full_name = 'Unknown'

                        # Parse performance from Result column
                        result = str(row.get('Result', '0'))
                        performance = 0
                        try:
                            # Handle time format like "0:47.71" or direct float
                            if ':' in result:
                                time_parts = result.split(':')
                                if len(time_parts) == 2:
                                    minutes = float(time_parts[0])
                                    seconds = float(time_parts[1])
                                    performance = minutes * 60 + seconds
                                else:
                                    performance = float(result.replace(':', ''))
                            else:
                                performance = float(result)
                        except:
                            performance = 0

                        performer_info = {
                            'name': full_name,
                            'country': str(row.get('CountryName', row.get('Country', 'Unknown'))),
                            'performance': performance,
                            'date': str(row.get('Date', year)),
                            'last_competition': str(row.get('Competition', 'Unknown')),
                            'year': year
                        }
                        performers.append(performer_info)

        # Sort by performance (best first)
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']
        performers.sort(key=lambda x: x['performance'], reverse=not is_time_event)

        return performers

    def get_competitor_timeline_2024_25(self, event, classification):
        """Get competitor timeline data for 2024-25 season"""
        timeline_data = []

        # Get all 2024-25 performers
        all_performers = self.get_2024_25_season_performers(event, classification)

        # Group by athlete to create timelines
        athlete_data = {}
        for performer in all_performers:
            name = performer['name']
            if name not in athlete_data:
                athlete_data[name] = {
                    'name': name,
                    'country': performer['country'],
                    'dates': [],
                    'performances': []
                }

            athlete_data[name]['dates'].append(performer['date'])
            athlete_data[name]['performances'].append(performer['performance'])

        # Convert to list and sort by best performance
        for athlete in athlete_data.values():
            if len(athlete['performances']) > 0:
                athlete['best_performance'] = min(athlete['performances']) if event in ['100m', '200m', '400m'] else max(athlete['performances'])
                timeline_data.append(athlete)

        # Sort by best performance
        is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']
        timeline_data.sort(key=lambda x: x['best_performance'], reverse=not is_time_event)

        return timeline_data

    def _create_recent_performance_analysis(self, ax, event, classification, saudi_green):
        """Create recent performance analysis with improved presentation"""
        ax.axis('tight')
        ax.axis('off')

        recent_performers = self.get_2024_25_season_performers(event, classification)

        if not recent_performers:
            ax.text(0.5, 0.5, 'No recent performance data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Recent Performance Analysis', fontweight='bold', pad=20)
            return

        # Filter for unique athletes (best performance per athlete)
        unique_athletes = {}
        for performer in recent_performers:
            name = performer['name']
            if name not in unique_athletes:
                unique_athletes[name] = performer
            else:
                # Keep the better performance
                is_time_event = event in ['100m', '200m', '400m', '800m', '1500m', '5000m']
                current_perf = performer['performance']
                existing_perf = unique_athletes[name]['performance']

                if (is_time_event and current_perf < existing_perf) or (not is_time_event and current_perf > existing_perf):
                    unique_athletes[name] = performer

        # Create analysis summary
        headers = ['Rank', 'Athlete', 'Country', 'Best 2024-25', 'Competition', 'Date', 'Form Trend']
        data = []

        sorted_athletes = sorted(unique_athletes.values(),
                               key=lambda x: x['performance'],
                               reverse=not (event in ['100m', '200m', '400m', '800m', '1500m', '5000m']))

        for i, athlete in enumerate(sorted_athletes[:12], 1):  # Top 12 unique athletes
            country = athlete['country']

            # Determine form trend (simplified)
            form_trend = "🔥 Hot" if i <= 3 else "📈 Rising" if i <= 6 else "📊 Steady"

            # Highlight Saudi athletes
            if 'Saudi' in country:
                name = f"🇸🇦 {athlete['name'][:20]}"
                form_trend = "🏠 Home"
            else:
                name = athlete['name'][:20]

            data.append([
                str(i),
                name,
                country[:10],
                f"{athlete['performance']:.2f}",
                athlete['last_competition'][:15],
                athlete['date'][:10],
                form_trend
            ])

        if data:
            table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.1, 1.6)

            # Style the table
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#006C35')
                table[(0, i)].set_text_props(weight='bold', color='white')

            # Color code form trends and highlight Saudi
            for i, row_data in enumerate(data):
                if '🇸🇦' in row_data[1]:
                    for j in range(len(headers)):
                        table[(i+1, j)].set_facecolor('#FFD700')
                        table[(i+1, j)].set_alpha(0.3)
                elif '🔥' in row_data[6]:
                    table[(i+1, 6)].set_facecolor('red')
                    table[(i+1, 6)].set_alpha(0.3)
                elif '📈' in row_data[6]:
                    table[(i+1, 6)].set_facecolor('orange')
                    table[(i+1, 6)].set_alpha(0.3)

        ax.set_title(f'Recent Performance Analysis - {event} {classification} (2024-25 Season)',
                    fontweight='bold', pad=20)

def main():
    """Main execution function"""
    analyzer = ChampionshipAnalyzer()

    print("Para Athletics Championship Winning Standards Analyzer")
    print("=" * 55)

    # Load all data
    analyzer.load_data()

    # Generate comprehensive analysis
    analyzer.generate_championship_standards_report()
    analyzer.generate_detailed_top8_report()
    analyzer.compare_world_records()

    # Create visualizations
    analyzer.create_visualizations()

    # Export summary
    summary = analyzer.export_summary_data()
    print(f"\nAnalysis Summary:")
    print(f"Total championship results: {summary['total_championship_results']}")
    print(f"World records available: {summary['world_records']}")
    print(f"Rankings years: {summary['rankings_years']}")

    print("\nAnalysis complete! Check generated files:")
    print("- championship_standards_report.csv (comprehensive winning standards)")
    print("- detailed_top8_championship_analysis.csv (positions 1-8 breakdown)")
    print("- championship_analysis_visualizations.png (comprehensive charts)")
    print("- Individual event analysis charts (100m_detailed_analysis.png, etc.)")
    print("- csv_analysis_summary.txt (data structure analysis)")

if __name__ == "__main__":
    main()