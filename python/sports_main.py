import pandas as pd
from functions_libraries import (
    # Functions
    get_events,
    get_upcoming_player_props_by_market,
    process_yes_no_market,
    # Variables
    api_key,
    nba_market_keys,
    ncaam_market_keys,
    nfl_market_keys,
    ncaaf_market_keys,
    default_col_names,
    nhl_market_keys
)

# Sport configurations
SPORT_CONFIGS = {
    'NBA': {
        'sport_key': 'basketball_nba',
        'market_keys': nba_market_keys
    },
    'NCAAM': {
        'sport_key': 'basketball_ncaab',
        'market_keys': ncaam_market_keys
    },
    'NFL': {
        'sport_key': 'americanfootball_nfl',
        'market_keys': nfl_market_keys
    },
    'NCAAF': {
        'sport_key': 'americanfootball_ncaaf',
        'market_keys': ncaaf_market_keys
    },
    'NHL': {
        'sport_key': 'icehockey_nhl',
        'market_keys': nhl_market_keys
    },
    #'MLB': {
    #    'sport_key': 'baseball_mlb',
    #    'market_keys': mlb_market_keys
    #}
}

# Add this mapping near SPORT_CONFIGS
LEAGUE_ID_TO_SPORT = {
    2: 'NFL',
    10: 'NCAAF',
    1: 'NHL',
    7: 'NCAAM',
    4: 'NBA',
    3: 'MLB'
}

def process_book_data(df_raw, book_name):
    """Helper function to process book data"""
    #print(f"\t\t\tProcessing data for book {book_name}...")
    
    if df_raw.empty:
        #print(f"\t\t\tNo data found for book {book_name}")
        cols = ['player_name', f'{book_name}_line', 
                f'{book_name}_under_price', f'{book_name}_over_price']
        return pd.DataFrame(columns=cols)
    
    if 'point' in df_raw.columns:
        if 'Under' in df_raw['name'].values:
            #print(f"\t\t\tProcessing Over/Under market for {book_name}")
            under_data = df_raw[df_raw['name'] == 'Under']
            over_data = df_raw[df_raw['name'] == 'Over']
            df_merge = pd.merge(under_data[['description', 'price', 'point']], 
                              over_data[['description', 'price', 'point']], 
                              on=['description', 'point'])
            df_merge.columns = ['player_name', 
                              f'{book_name}_under_price', f'{book_name}_line', f'{book_name}_over_price']
        else:
            #print(f"\t\t\tProcessing Over-only market for {book_name}")
            df_merge = df_raw[df_raw['name'] == 'Over'][['description', 'price', 'point']]
            df_merge['under_price'] = None
            df_merge.columns = ['player_name', f'{book_name}_over_price', 
                              f'{book_name}_line', f'{book_name}_under_price']
    else:
        #print(f"\t\t\tProcessing Yes/No market for {book_name}")
        df_merge = process_yes_no_market(df_raw, book_name)
    
    #print(f"\t\t\tFinished processing {book_name}")
    return df_merge

def create_market_dataframe(market_data, market_key, sport_key):
    """Creates a DataFrame for a specific market"""
    print(f"\tProcessing market: {market_key}")
    df = pd.DataFrame()
    
    for game_id, game_data in market_data.items():
        #print(f"\t\tProcessing game ID: {game_id}")
        market_df = pd.DataFrame()
        
        # The API returns bookmakers inside the market_key dictionary
        bookmakers = game_data.get(market_key, {}).get('bookmakers', [])
        #print(f"\t\tFound {len(bookmakers)} bookmakers")
        
        for bookmaker in bookmakers:
            outcomes = []
            book_name = bookmaker.get('key')
            for market in bookmaker.get('markets', []):
                if market.get('key') == market_key:
                    outcomes = market.get('outcomes', [])
                    break
            
            book_df = process_book_data(pd.DataFrame(outcomes), book_name)
            market_df = pd.merge(market_df, book_df, on='player_name', how='outer') if not market_df.empty else book_df
        
        # Add game information
        if not market_df.empty:
            market_df['game_id'] = game_id
            market_df['datetime'] = game_data[market_key].get('commence_time')
            market_df['hometeam'] = game_data[market_key].get('home_team')
            market_df['awayteam'] = game_data[market_key].get('away_team')
            market_df['market_key'] = market_key
            market_df['sport'] = sport_key
            
            df = pd.concat([df, market_df], ignore_index=True)

    #print(f"\tFinished processing market: {market_key}")
    return df

def process_sport(sport_name):
    """Process all markets for a specific sport"""
    #print(f"Starting to process {sport_name}...")
    sport_config = SPORT_CONFIGS[sport_name]
    sport_key = sport_config['sport_key']
    market_keys = sport_config['market_keys']
    
    # Get events
    print(f"Fetching events for {sport_name}...")
    events = pd.DataFrame(get_events(sport_key, api_key))
    if events.empty:
        print(f"No events found for {sport_name}")
        return {}
    
    #print(f"Found {len(events)} events for {sport_name}")
    events['commence_time'] = pd.to_datetime(events['commence_time']).dt.tz_convert('US/Central')
    events['live'] = events['commence_time'] < pd.Timestamp.now(tz='US/Central')
    
    # Calculate time threshold for filtering (16 hours from now)
    time_threshold = pd.Timestamp.now(tz='US/Central') + pd.Timedelta(hours=16)
    
    # Split into upcoming and live events, filtering out events >16 hours away
    upcoming_events = events[
        (~events['live']) & 
        (events['commence_time'] <= time_threshold)
    ]
    print(f"Processing {len(upcoming_events)} upcoming events for {sport_name} within next 16 hours")
    
    # Create dictionary to store player props data
    upcoming_player_props_data = {}

    # Fetch data for each event and market
    if not upcoming_events.empty:
        # Set to True to process all events, False for first event only
        process_all_events = True
        
        if process_all_events:
            event_ids = upcoming_events['id'].tolist()
            #print(f"Fetching markets for {len(event_ids)} events...")
            for event_id in event_ids:
                print(f"Fetching markets for event ID: {event_id}")
                upcoming_player_props_data[event_id] = {
                    market_key: get_upcoming_player_props_by_market(sport_key, api_key, event_id, market_key)
                    for market_key in market_keys
                }
        else:
            first_event_id = upcoming_events['id'].iloc[0]
            #print(f"Fetching markets for first event ID: {first_event_id}")
            upcoming_player_props_data[first_event_id] = {
                market_key: get_upcoming_player_props_by_market(sport_key, api_key, first_event_id, market_key)
                for market_key in market_keys
            }
    else:
        print(f"No upcoming events found for {sport_name}")

    if upcoming_player_props_data:
        #print(f"Creating DataFrames for {sport_name} markets...")
        # Create DataFrames for each market
        market_dataframes = {
            market_key: create_market_dataframe(upcoming_player_props_data, market_key, sport_key)
            for market_key in market_keys
        }
    else:
        print(f"No player props data found for {sport_name}, creating empty DataFrames")
        # Create empty DataFrames if no data
        market_dataframes = {
            market_key: pd.DataFrame(columns=default_col_names)
            for market_key in market_keys
        }
    
    #print(f"Finished processing {sport_name}")
    return market_dataframes

def process_all_sports(league_ids=None):
    """
    Process sports data for specified leagues.
    If league_ids is None, process all configured sports.
    """
    # Determine which sports to process
    if league_ids is not None:
        sports_to_process = [LEAGUE_ID_TO_SPORT[lid] for lid in league_ids 
                           if lid in LEAGUE_ID_TO_SPORT and LEAGUE_ID_TO_SPORT[lid] in SPORT_CONFIGS]
    else:
        sports_to_process = list(SPORT_CONFIGS.keys())
    
    print(f"Processing sports: {', '.join(sports_to_process)}")
    
    all_sports_data = {
        sport_name: process_sport(sport_name)
        for sport_name in sports_to_process
    }
    print("Finished processing all sports!")

    # Combine all dataframes into one
    print("Combining all data into one CSV file...")
    all_dfs = []
    for sport_name, market_data in all_sports_data.items():
        for market_key, df in market_data.items():
            if not df.empty:
                all_dfs.append(df)

    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df['market_key'] = combined_df['market_key'].str.replace('_alternate', '')

        # Replace names from odds api to match drafters
        name_replacements = {
            'Christopher Tanev': 'Chris Tanev',
            'Isaiah Stewart II': 'Isaiah Stewart',
            'Jonas Valanciunas': 'Jonas Valančiūnas', 
            'Tim Hardaway Jr': 'Tim Hardaway',
            'Alperen Sengun': 'Alperen Şengün',
            'Nicolas Claxton': 'Nic Claxton',
            'AJ Brown': 'A.J. Brown',
            'Nikola Jovic': 'Nikola Jović',
            'Nikola Vucevic': 'Nikola Vučević',
            'Michael Porter Jr': 'Michael Porter',
            'Kelly Oubre Jr': 'Kelly Oubre',
            'Wendell Carter Jr': 'Wendell Carter',
            'Nikola Jokic': 'Nikola Jokić',
            'Alexis Lafrenière': 'Alexis Lafreniere',
            'Gary Trent Jr': 'Gary Trent',
            'Jaime Jaquez Jr': 'Jaime Jaquez',
            'Vit Krejci': 'Vít Krejčí',
            'Bogdan Bogdanovic': 'Bogdan Bogdanović',
            'Nick Smith Jr': 'Nick Smith',
            'Trey Murphy III': 'Trey Murphy',
            'C.J. McCollum': 'CJ McCollum',
            'Zaon Collins': 'Zaon  Collins',
            'Kristaps Porzingis': 'Kristaps Porziņģis',
            'Dennis Schroder': 'Dennis Schröder',
            'Jaren Jackson Jr': 'Jaren Jackson',
        }
        combined_df['player_name'] = combined_df['player_name'].replace(name_replacements)

        filename = "data/all_sports_data.csv"
        combined_df.to_csv(filename, index=False)
        print(f"Saved combined data to {filename}")
        return combined_df
    else:
        print("No data to save")
        return None
    
if __name__ == "__main__":
    process_all_sports()