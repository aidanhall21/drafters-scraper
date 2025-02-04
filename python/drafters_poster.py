import pandas as pd
from drafters_scraper import fetch_props_games
from sports_main import process_all_sports
from functions_libraries import entry_fee_drafters, headers_drafters, user_config
import requests
from itertools import combinations
from time import sleep
import random
import sys

def combine_drafters_and_odds_data():

    drafters_df = fetch_props_games()
    league_ids = drafters_df['game_id'].unique().tolist()
    odds_df = process_all_sports(league_ids)  
    
    if odds_df is None or drafters_df.empty:
        print("No data available from one or both sources")
        return None

    # Check for missing players
    drafters_players = set(drafters_df['player_name'].unique())
    odds_players = set(odds_df['player_name'].unique())
    missing_players = drafters_players - odds_players
    
    if missing_players:
        print("Players in drafters_df but missing from odds_df:")
        for player in missing_players:
            print(f"- {player}")

    # For college sports I use betonlineag odds and for pro sports I use pinnacle odds
    # Create separate dataframes for game_ids 7,10 and others
    drafters_game7_10 = drafters_df[drafters_df['game_id'].isin([7,10])].copy()
    drafters_other = drafters_df[~drafters_df['game_id'].isin([7,10])].copy()

    # Merge game_ids 7,10 data with betonlineag_line
    merged_game7_10 = pd.merge(
        drafters_game7_10,
        odds_df,
        left_on=['player_name', 'bid_stats_name', 'bid_stats_value'],
        right_on=['player_name', 'market_key', 'betonlineag_line'],
        how='inner',
        suffixes=('_drafters', '_odds')
    )

    # Merge other games data with pinnacle_line
    merged_other = pd.merge(
        drafters_other,
        odds_df,
        left_on=['player_name', 'bid_stats_name', 'bid_stats_value'],
        right_on=['player_name', 'market_key', 'pinnacle_line'],
        how='inner',
        suffixes=('_drafters', '_odds')
    )

    # Combine the results
    combined_df = pd.concat([merged_game7_10, merged_other], ignore_index=True)

    # Save the combined data
    combined_df.to_csv('data/combined_props_data.csv', index=False)
    return combined_df

def calculate_no_vig_probabilities(df):
    # Function to convert decimal odds to probabilities and remove vig
    def devig_odds(over_decimal, under_decimal):
        over_prob = 1 / over_decimal
        under_prob = 1 / under_decimal
        total_prob = over_prob + under_prob
        
        # Normalize probabilities to remove vig
        no_vig_over = over_prob / total_prob
        no_vig_under = under_prob / total_prob
        
        return no_vig_over, no_vig_under

    # Create masks for basketball_ncaab and americanfootball_ncaaf
    ncaab_mask = df['sport'] == 'basketball_ncaab'
    ncaaf_mask = df['sport'] == 'americanfootball_ncaaf'
    
    # Initialize columns with None
    df['no_vig_over'] = None
    df['no_vig_under'] = None
    
    # Process NCAAB and NCAAF games using betonlineag odds
    betonline_rows = df[ncaab_mask | ncaaf_mask].index
    for idx in betonline_rows:
        over_odds = df.loc[idx, 'betonlineag_over_price']
        under_odds = df.loc[idx, 'betonlineag_under_price']
        no_vig_over, no_vig_under = devig_odds(over_odds, under_odds)
        df.loc[idx, 'no_vig_over'] = no_vig_over
        df.loc[idx, 'no_vig_under'] = no_vig_under
    
    # Process other sports using pinnacle odds
    other_rows = df[~(ncaab_mask | ncaaf_mask)].index
    for idx in other_rows:
        over_odds = df.loc[idx, 'pinnacle_over_price']
        under_odds = df.loc[idx, 'pinnacle_under_price']
        no_vig_over, no_vig_under = devig_odds(over_odds, under_odds)
        df.loc[idx, 'no_vig_over'] = no_vig_over
        df.loc[idx, 'no_vig_under'] = no_vig_under
    
    # Add play and direction columns based on probabilities
    df['play'] = 'no play'
    df['direction'] = None
    
    # Mask for plays where either probability exceeds 0.55
    play_mask = (df['no_vig_over'] > 0.55) | (df['no_vig_under'] > 0.55)
    df.loc[play_mask, 'play'] = 'PLAY'
    
    # Set direction based on which probability is higher
    df.loc[df['no_vig_over'] > df['no_vig_under'], 'direction'] = 'OVER'
    df.loc[df['no_vig_over'] <= df['no_vig_under'], 'direction'] = 'UNDER'
    
    return df

def get_valid_combinations(plays_df):
    """
    Generate valid combinations of plays (3, 5, and 7 picks) ensuring no duplicate
    game_ids or players within each combination.
    """
    def is_valid_combination(combo):
        # Check for unique game_ids and players in the combination
        game_ids = set(row['game_id_odds'] for row in combo)
        player_ids = set(row['player_id'] for row in combo)
        return (len(game_ids) == len(combo) and 
                len(player_ids) == len(combo))
    
    def get_combo_key(combo):
        # Create a unique key for each combination using player_id and bid_stats_name
        sorted_plays = sorted([f"{row['prop_id']}" for row in combo])
        return '|'.join(sorted_plays)
    
    # Load previously submitted combinations
    submitted_combos = set()
    try:
        with open('data/submitted_combinations.txt', 'r') as f:
            submitted_combos = set(line.strip() for line in f)
    except FileNotFoundError:
        # File doesn't exist yet, that's okay
        pass
    
    # Convert DataFrame rows to dictionaries for easier handling
    plays_list = plays_df.to_dict('records')
    
    valid_combinations = {
        3: [],
        5: [],
        7: []
    }
    
    # Generate combinations for each size
    for size in [3, 5, 7]:
        for combo in combinations(plays_list, size):
            combo_key = get_combo_key(combo)
            if is_valid_combination(combo) and combo_key not in submitted_combos:
                valid_combinations[size].append(combo)
        
        # Randomize the order of combinations for each size
        random.shuffle(valid_combinations[size])
    
    # Print the number of valid combinations for each size
    for size, combos in valid_combinations.items():
        print(f"Found {len(combos)} valid {size}-pick combinations")
    
    return valid_combinations

def submit_drafters_entry(combined_df, user_config):
    """
    Submit entries to drafters.com based on the calculated plays.
    """
    # Filter for only PLAY rows
    plays_df = combined_df[combined_df['play'] == 'PLAY']
    
    # Get all valid combinations
    all_combinations = get_valid_combinations(plays_df)
    
    results = []
    newly_submitted = set()
    
    # Submit entries for each combination size and valid combination
    for size, combos in all_combinations.items():
        for combo in combos:
            # Create unique key for this combination
            combo_key = '|'.join(sorted([
                f"{row['prop_id']}" 
                for row in combo
            ]))
            
            # Create selections dictionary for this combination
            selections = {
                row['prop_id']: row['direction'].lower()
                for row in combo
            }
            
            payload = {
                "lg_name": "props-entry",
                "entry_fee": str(entry_fee_drafters),
                "selections": selections,
                "PublicIP": user_config['public_ip'],
                "country_name": user_config['country_name'],
                "state_name": user_config['state_name'],
                "user_dob": user_config['user_dob'],
                "display_name": user_config['display_name'],
                "ticket_id": 0,
                "safety": False
            }
            
            url = "https://node.drafters.com/props-game/join-props-game"

            try:
                response = requests.post(url, json=payload, headers=headers_drafters)
                response.raise_for_status()
                response_data = response.json()
                print(f"Response from drafters.com: {response_data}")
                
                # Check for failed status or market error in response
                if not response_data.get('status') or response_data.get('marketError'):
                    print(f"Error in submission: {response_data.get('message')}")
                    sys.exit(1)
                
                results.append({
                    'size': size,
                    'selections': selections,
                    'response': response_data
                })
                newly_submitted.add(combo_key)
                # Write this combo to file immediately after adding it
                with open('data/submitted_combinations.txt', 'a') as f:
                    f.write(f"{combo_key}\n")
                # Wait random time between 5-10 seconds after success
                sleep_time = random.uniform(5, 10)
                sleep(sleep_time)
            except requests.exceptions.RequestException as e:
                print(f"Fatal error occurred during submission process: {e}")
                sys.exit(1)  # This will completely exit the program
    
    return results

if __name__ == "__main__":
    combined_df = combine_drafters_and_odds_data()
    if combined_df is not None:
        combined_df = calculate_no_vig_probabilities(combined_df)
        combined_df.to_csv('data/combined_props_data.csv', index=False)
        print("Data successfully combined, no-vig probabilities added, and saved to data/combined_props_data.csv")
        
        result = submit_drafters_entry(combined_df, user_config)
        if result:
            print("Successfully submitted entry to drafters.com")
