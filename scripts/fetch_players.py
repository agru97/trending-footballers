import requests
import time
import json
import urllib3
import os

urllib3.disable_warnings()

# Function to call the API
def call_api(endpoint, params=None):
    if params is None:
        params = {}
    base_url = "https://v3.football.api-sports.io/"
    headers = {
        "x-rapidapi-key": os.environ['FOOTBALL_API_KEY'],
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    try:
        response = requests.get(
            base_url + endpoint, 
            headers=headers, 
            params=params,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data and data["errors"]:
                print(f"API Error: {data['errors']}")
                return None
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return None

def players_data(league, season, page=1, all_players=None):
    if all_players is None:
        all_players = []
    
    print(f"Fetching players data - Page {page}")
    response = call_api("players", {"league": league, "season": season, "page": page})
    
    if response and "response" in response:
        current_page_players = response["response"]
        if not current_page_players:
            print("No more players found")
            return all_players
            
        all_players.extend(current_page_players)
        print(f"Found {len(current_page_players)} players on page {page}")
        
        if response["paging"]["current"] < response["paging"]["total"]:
            time.sleep(0.25)
            return players_data(league, season, page + 1, all_players)
    else:
        print("Failed to get response from API")
    
    return all_players

def get_current_season(league_id):
    """Get the current season for a league"""
    response = call_api("leagues", {"id": league_id})
    
    if response and "response" in response:
        league_data = response["response"][0]
        for season in league_data["seasons"]:
            if season["current"]:
                return season["year"]
        raise Exception("No current season found for league")
    else:
        raise Exception(f"Failed to get seasons for league {league_id}")

def main():
    # Test API connection
    status = call_api("status")
    if status:
        print("API Connection successful!")
        print(f"Account: {status['response']['account']['firstname']} {status['response']['account']['lastname']}")
        print(f"Plan: {status['response']['subscription']['plan']}")
        print(f"Requests today: {status['response']['requests']['current']}/{status['response']['requests']['limit_day']}")
    else:
        print("Failed to connect to API. Please check your API key.")
        exit(1)

    # Major 5 European leagues
    leagues = {
        'Premier League': 39,
        'La Liga': 140,
        'Bundesliga': 78,
        'Serie A': 135,
        'Ligue 1': 61
    }
    
    all_players = []
    
    for league_name, league_id in leagues.items():
        try:
            # Get current season
            season = get_current_season(league_id)
            print(f"\nFetching players for {league_name} season {season}")
            
            # Get players for this league
            league_players = players_data(league_id, season)
            if league_players:
                print(f"Found {len(league_players)} players in {league_name}")
                all_players.extend(league_players)
            else:
                print(f"Failed to fetch players for {league_name}")
                
        except Exception as e:
            print(f"Error processing {league_name}: {str(e)}")
    
    if all_players:
        # Create public directory if it doesn't exist
        os.makedirs('public', exist_ok=True)
        
        # Save to public directory
        with open("public/players1.json", "w") as file:
            json.dump(all_players, file, indent=4)
        print(f"\nTotal players saved to 'public/players.json': {len(all_players)} players")
    else:
        print("\nFailed to fetch any players data.")

if __name__ == "__main__":
    main() 