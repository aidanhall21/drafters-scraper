### Functions and libraries
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize empty lists/dictionaries
appearance_fees = {}
used_combinations = {}

# API Configuration
api_key = os.getenv('ODDS_API_KEY')  # API Key (from Odds API)
authorization_token = os.getenv('DRAFTERS_AUTH_TOKEN')
user_config = {
    "display_name": os.getenv('DISPLAY_NAME'),
    "public_ip": os.getenv('PUBLIC_IP'),
    "country_name": os.getenv('COUNTRY_NAME'),
    "state_name": os.getenv('STATE_NAME'),
    "user_dob": os.getenv('USER_DOB')
}

BASE_URL = "https://api.the-odds-api.com/v4/sports/"

entry_fee_drafters = 2

headers_drafters = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.9', 
    'Referer': 'https://www.google.com/',
    'Accept': 'application/json',
    'Authorization': authorization_token
}

default_col_names = ["player_name", "book_1_line", "book_1_under_price", "book_1_over_price", 
                     "book_2_line", "book_2_under_price", "book_2_over_price", 
                     "book_3_line", "book_3_under_price", "book_3_over_price", 
                     "game_id", "datetime", "hometeam", "awayteam"]

nba_market_keys = [
    # Standard markets
    "player_points",
    #"player_points_q1",
    "player_rebounds",
    #"player_rebounds_q1",
    "player_assists",
    #"player_assists_q1",
    "player_threes",
    #"player_blocks",
    #"player_steals",
    #"player_blocks_steals",
    #"player_turnovers",
    "player_points_rebounds_assists",
    #"player_points_rebounds",
    #"player_points_assists",
    #"player_rebounds_assists",
    #"player_field_goals",
    #"player_frees_made",
    #"player_frees_attempts",
    #"player_double_double",
    # Alternate markets
    "player_points_alternate",
    "player_rebounds_alternate",
    "player_assists_alternate",
    #"player_blocks_alternate",
    #"player_steals_alternate",
    #"player_turnovers_alternate",
    "player_threes_alternate",
    #"player_points_assists_alternate",
    #"player_points_rebounds_alternate",
    #"player_rebounds_assists_alternate",
    "player_points_rebounds_assists_alternate"
]

# NCAA Basketball market keys
ncaam_market_keys = [
    # Standard markets
    "player_points",
    #"player_points_q1",
    "player_rebounds",
    #"player_rebounds_q1",
    "player_assists",
    #"player_assists_q1",
    "player_threes",
    #"player_blocks",
    #"player_steals",
    #"player_blocks_steals",
    #"player_turnovers",
    #"player_points_rebounds_assists",
    #"player_points_rebounds",
    #"player_points_assists",
    #"player_rebounds_assists",
    #"player_field_goals",
    #"player_frees_made",
    #"player_frees_attempts",
    #"player_double_double",
    # Alternate markets
    #"player_points_alternate",
    #"player_rebounds_alternate",
    #"player_assists_alternate",
    #"player_blocks_alternate",
    #"player_steals_alternate",
    #"player_turnovers_alternate",
    #"player_threes_alternate",
    #"player_points_assists_alternate",
    #"player_points_rebounds_alternate",
    #"player_rebounds_assists_alternate",
    #"player_points_rebounds_assists_alternate"
]

# NHL market keys
nhl_market_keys = [
    # Standard markets
    "player_points",
    #"player_power_play_points",
    "player_assists",
    "player_blocked_shots",
    "player_shots_on_goal",
    "player_goals",
    "player_total_saves",
    #"player_goal_scorer_first",
    #"player_goal_scorer_last",
    #"player_goal_scorer_anytime",
    # Alternate markets
    "player_points_alternate",
    "player_assists_alternate",
    #"player_power_play_points_alternate",
    "player_goals_alternate",
    "player_shots_on_goal_alternate",
    "player_blocked_shots_alternate",
    "player_total_saves_alternate"
]

# NFL market keys
nfl_market_keys = [
    # Standard markets
    #"player_assists",
    #"player_defensive_interceptions",
    "player_field_goals",
    "player_kicking_points",
    "player_pass_attempts",
    "player_pass_completions",
    "player_pass_interceptions",
    #"player_pass_longest_completion",
    #"player_pass_rush_reception_tds",
    "player_pass_rush_reception_yds",
    "player_pass_tds",
    "player_pass_yds",
    #"player_pass_yds_q1",
    #"player_pats",
    "player_receptions",
    #"player_reception_longest",
    "player_reception_tds",
    "player_reception_yds",
    "player_rush_attempts",
    #"player_rush_longest",
    "player_rush_reception_tds",
    "player_rush_reception_yds",
    "player_rush_tds",
    "player_rush_yds",
    #"player_sacks",
    #"player_solo_tackles",
    #"player_tackles_assists",
    # Alternate markets
    #"player_assists_alternate",
    "player_field_goals_alternate",
    "player_kicking_points_alternate",
    "player_pass_attempts_alternate",
    "player_pass_completions_alternate",
    "player_pass_interceptions_alternate",
    #"player_pass_longest_completion_alternate",
    "player_pass_rush_reception_tds_alternate",
    "player_pass_rush_reception_yds_alternate",
    "player_pass_tds_alternate",
    "player_pass_yds_alternate",
    #"player_pats_alternate",
    "player_receptions_alternate",
    #"player_reception_longest_alternate",
    "player_reception_tds_alternate",
    "player_reception_yds_alternate",
    "player_rush_attempts_alternate",
    #"player_rush_longest_alternate",
    "player_rush_reception_tds_alternate",
    "player_rush_reception_yds_alternate",
    "player_rush_tds_alternate",
    "player_rush_yds_alternate",
    #"player_sacks_alternate",
    #"player_solo_tackles_alternate",
    #"player_tackles_assists_alternate"
]

# NCAA market keys
ncaaf_market_keys = [
    # Standard markets
    #"player_assists",
    #"player_defensive_interceptions",
    "player_field_goals",
    "player_kicking_points",
    "player_pass_attempts",
    "player_pass_completions",
    "player_pass_interceptions",
    #"player_pass_longest_completion",
    #"player_pass_rush_reception_tds",
    "player_pass_rush_reception_yds",
    "player_pass_tds",
    "player_pass_yds",
    #"player_pass_yds_q1",
    #"player_pats",
    "player_receptions",
    #"player_reception_longest",
    "player_reception_tds",
    "player_reception_yds",
    "player_rush_attempts",
    #"player_rush_longest",
    "player_rush_reception_tds",
    "player_rush_reception_yds",
    "player_rush_tds",
    "player_rush_yds",
    #"player_sacks",
    #"player_solo_tackles",
    #"player_tackles_assists",
    # Alternate markets
    #"player_assists_alternate",
    "player_field_goals_alternate",
    "player_kicking_points_alternate",
    "player_pass_attempts_alternate",
    "player_pass_completions_alternate",
    "player_pass_interceptions_alternate",
    #"player_pass_longest_completion_alternate",
    "player_pass_rush_reception_tds_alternate",
    "player_pass_rush_reception_yds_alternate",
    "player_pass_tds_alternate",
    "player_pass_yds_alternate",
    #"player_pats_alternate",
    "player_receptions_alternate",
    #"player_reception_longest_alternate",
    "player_reception_tds_alternate",
    "player_reception_yds_alternate",
    "player_rush_attempts_alternate",
    #"player_rush_longest_alternate",
    "player_rush_reception_tds_alternate",
    "player_rush_reception_yds_alternate",
    "player_rush_tds_alternate",
    "player_rush_yds_alternate",
    #"player_sacks_alternate",
    #"player_solo_tackles_alternate",
    #"player_tackles_assists_alternate"
]

# Sport league mappings
SPORT_LEAGUES = {
    'NFL': 2,
    'CFB': 10,
    'NHL': 1,
    'CBB': 7,
    'NBA': 4,
    'MLB': 3
}

def get_sport_selections():
    """Interactive function to get sport selections from user"""
    selected_leagues = []
    print("\nAvailable sports to scrape:")
    for sport in SPORT_LEAGUES:
        response = input(f"Do you want to scrape {sport}? (y/n): ").lower()
        if response == 'y':
            selected_leagues.append(SPORT_LEAGUES[sport])
    
    if not selected_leagues:
        print("No sports selected. Please select at least one sport.")
        return get_sport_selections()
    
    return selected_leagues

def get_events(sport_key, api_key):
    url = f"{BASE_URL}{sport_key}/odds/?apiKey={api_key}&regions=us_dfs&bookmakers=underdog&oddsFormat=decimal"
    response = requests.get(url)
    return response.json()

def get_upcoming_player_props_by_market(sport_key, api_key, event_id, market_key):
    books = "pinnacle,betonlineag"
    url = f"{BASE_URL}{sport_key}/events/{event_id}/odds?apiKey={api_key}&regions=eu&markets={market_key}&bookmakers={books}&oddsFormat=decimal"
    response = requests.get(url)
    return response.json()

def process_yes_no_market(df_raw, book_num):
    """Process Yes/No market data into a standardized format"""
    if df_raw.empty:
        cols = ['player_name', f'book_{book_num}_line', 
                f'book_{book_num}_under_price', f'book_{book_num}_over_price']
        return pd.DataFrame(columns=cols)
    
    if 'Yes' in df_raw['name'].values:
        yes_data = df_raw[df_raw['name'] == 'Yes']
        no_data = df_raw[df_raw['name'] == 'No']
        df_merge = pd.merge(yes_data[['description', 'price']], 
                          no_data[['description', 'price']], 
                          on='description')
        df_merge['line'] = 0.5  # Standard line for Yes/No markets
        df_merge.columns = ['player_name', f'book_{book_num}_over_price', 
                          f'book_{book_num}_under_price', f'book_{book_num}_line']
    else:
        # Handle yes-only case
        df_merge = df_raw[df_raw['name'] == 'Yes'][['description', 'price']]
        df_merge['under_price'] = None
        df_merge['line'] = 0.5
        df_merge.columns = ['player_name', f'book_{book_num}_over_price', 
                          f'book_{book_num}_under_price', f'book_{book_num}_line']
    
    return df_merge
