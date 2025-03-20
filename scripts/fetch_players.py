import requests
import time
import json
import urllib3
import os
from typing import Dict, List, Optional, Any

urllib3.disable_warnings()

BASE_URL = "https://v3.football.api-sports.io/"
OUTPUT_FILE = "public/players.json"

def get_api_headers() -> Dict[str, str]:
    return {
        "x-rapidapi-key": os.environ['FOOTBALL_API_KEY'],
        "x-rapidapi-host": "v3.football.api-sports.io"
    }

def call_api(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
    params = params or {}
    
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=get_api_headers(),
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

def fetch_players(league_id: int, season: int, page: int = 1, 
                  accumulated_players: Optional[List] = None) -> List:
    accumulated_players = accumulated_players or []
    
    print(f"Fetching players data - Page {page}")
    response = call_api("players", {"league": league_id, "season": season, "page": page})
    
    if not response or "response" not in response:
        print("Failed to get response from API")
        return accumulated_players
    
    current_page_players = response["response"]
    if not current_page_players:
        print("No more players found")
        return accumulated_players
        
    accumulated_players.extend(current_page_players)
    print(f"Found {len(current_page_players)} players on page {page}")
    
    if response["paging"]["current"] < response["paging"]["total"]:
        time.sleep(0.25)  # Rate limiting
        return fetch_players(league_id, season, page + 1, accumulated_players)
    
    return accumulated_players

def get_current_season(league_id: int) -> int:
    response = call_api("leagues", {"id": league_id})
    
    if not response or "response" not in response:
        raise Exception(f"Failed to get seasons for league {league_id}")
    
    league_data = response["response"][0]
    for season in league_data["seasons"]:
        if season["current"]:
            return season["year"]
    
    raise Exception("No current season found for league")

def verify_api_connection():
    status = call_api("status")
    if not status:
        print("Failed to connect to API. Please check your API key.")
        exit(1)
        
    account = status["response"]["account"]
    subscription = status["response"]["subscription"]
    requests = status["response"]["requests"]
    
    print("API Connection successful!")
    print(f"Account: {account['firstname']} {account['lastname']}")
    print(f"Plan: {subscription['plan']}")
    print(f"Requests today: {requests['current']}/{requests['limit_day']}")

def save_players_data(players: List[Dict]) -> None:
    os.makedirs('public', exist_ok=True)
    
    with open(OUTPUT_FILE, "w") as file:
        json.dump(players, file, indent=4)
    
    print(f"\nTotal players saved to '{OUTPUT_FILE}': {len(players)} players")

def main():
    verify_api_connection()

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
            season = get_current_season(league_id)
            print(f"\nFetching players for {league_name} season {season}")
            
            league_players = fetch_players(league_id, season)
            if league_players:
                print(f"Found {len(league_players)} players in {league_name}")
                all_players.extend(league_players)
            else:
                print(f"Failed to fetch players for {league_name}")
                
        except Exception as e:
            print(f"Error processing {league_name}: {str(e)}")
    
    if all_players:
        save_players_data(all_players)
    else:
        print("\nFailed to fetch any players data.")

if __name__ == "__main__":
    main() 