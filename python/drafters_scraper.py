import requests
import json
import pandas as pd
from time import sleep
from functions_libraries import headers_drafters, get_sport_selections

def flatten_player_data(player):
    """Flatten nested player data into a single dictionary"""
    flat_data = {
        'prop_id': player['prop_id'],
        'game_id': player['game_id'],
        'lock_time': player['lock_time'],
        'player_id': player['player_id'],
        'player_name': player['player_name'],
        'player_position': player['player_position'],
        'question': player['question'],
        'bid_stats_name': player['bid_stats_name'],
        'bid_stats_value': player['bid_stats_value'],
        'event_name': player['event_name'],
        'options': ','.join(player['options']),  # Convert options list to string
        
        # Event data
        'event_id': player['event']['event_id'],
        'home': player['event']['home'],
        'away': player['event']['away'],
        'own': player['event']['own'],
        'opponent': player['event']['opponent'],
        'time': player['event']['time'],
        'start_time': player['event']['start_time']
    }
    return flat_data

def fetch_props_games():
    # Get user's sport selections
    league_ids = get_sport_selections()
    
    # Base URL for the API
    base_url = "https://node.drafters.com/props-game/get-props-games/{league_id}?stats="
    
    # Store all player data
    all_players_data = []
    
    # Make requests for each game ID
    for league_id in league_ids:
        try:
            # Construct the URL
            url = base_url.format(league_id=league_id)
            
            # Make the request
            response = requests.get(url, headers=headers_drafters)
            if response.status_code == 200:
                data = response.json()
                # Check if the response has the expected structure
                if data.get('entities'):
                    for entity in data['entities']:
                        if 'players' in entity:
                            # Process each player in the entity
                            for player in entity['players']:
                                flat_player = flatten_player_data(player)
                                all_players_data.append(flat_player)
                
                print(f"Successfully fetched data for league ID: {league_id}")
            else:
                print(f"Failed to fetch data for league ID: {league_id}. Status code: {response.status_code}")
            
            # Add a small delay between requests
            sleep(1)
            
        except Exception as e:
            print(f"Error fetching game ID {league_id}: {str(e)}")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_players_data)
    
    # Define the mapping dictionary
    stats_mapping = {
        '3 Pointer Made': 'player_threes',
        '3 Pointers Made': 'player_threes',
        'Assists': 'player_assists',
        'Blocked Shots': 'player_blocked_shots',
        'Completions': 'player_pass_completions',
        'Field Goals Made': 'player_field_goals',
        'Interceptions Thrown': 'player_pass_interceptions',
        'Kicker Points': 'player_kicking_points',
        'Passing Touchdowns': 'player_pass_tds',
        'Passing Yards': 'player_pass_yds',
        'Points': 'player_points',
        'Pts+Rebs+Asts': 'player_points_rebounds_assists',
        'Rebounds': 'player_rebounds',
        'Receiving Yards': 'player_reception_yds',
        'Receptions': 'player_receptions',
        'Rush+Rec Yds': 'player_rush_reception_yds',
        'Rushing Yards': 'player_rush_yds',
        'Saves': 'player_total_saves',
        'Shots': 'player_shots_on_goal',
        'Points+Assists': 'player_points_assists',
        'Steals': 'player_steals',
        'Blocks': 'player_blocks',
        'Rebounds+Assists': 'player_rebounds_assists',
        'Goals Against': 'player_goals_against',
        'Blocks+Steals': 'player_blocks_steals',
        'Points+Rebounds': 'player_points_rebounds',
        'Turnovers': 'player_turnovers',
        'Longest Completion': 'player_pass_longest_completion',
        'Longest Reception': 'player_reception_longest',
        'Longest Rush': 'player_rush_longest'
    }
    # Find any bid_stats_name values not in the mapping
    unmapped_stats = set(df['bid_stats_name'].unique()) - set(stats_mapping.keys())
    if unmapped_stats:
        print("Warning: Found unmapped stats:")
        for stat in unmapped_stats:
            print(f"- {stat}")

    # Filter out rows with unmapped stats and map the rest
    df = df[df['bid_stats_name'].isin(stats_mapping.keys())]
    df['bid_stats_name'] = df['bid_stats_name'].map(stats_mapping)
    
    # Save to CSV
    df.to_csv('drafters_data.csv', index=False)
    print("Data saved to drafters_data.csv")
    
    return df

if __name__ == "__main__":
    # Fetch the data and create DataFrame
    df = fetch_props_games()

