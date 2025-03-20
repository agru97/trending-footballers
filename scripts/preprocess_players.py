"""
Player Preprocessing Script

This script processes football player data to:
1. Filter active players
2. Find Google Trends topic IDs for players
3. Save processed data to JSON
"""

import json
import os
import time
import unicodedata
from typing import Dict, List, Optional, Set, Any
from pytrends.request import TrendReq
import html
import requests
import random

# Constants
INPUT_FILE = 'public/players.json'
OUTPUT_FILE = 'public/preprocessed_players.json'
PROXIES = os.environ['PROXY_LIST'].split(',') if 'PROXY_LIST' in os.environ else []
random.shuffle(PROXIES)  # Shuffle proxies for better load distribution
MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]
MIN_DELAY_BETWEEN_CALLS = 1  # Minimum seconds between API calls

# Player type constants
VALID_PLAYER_TYPES = [
    # General player types
    'footballer', 'football player', 'soccer player',
    
    # Basic positions
    'goalkeeper', 'defender', 'midfielder', 'forward', 'striker', 'winger',
    
    # Specific positions
    'centre-back', 'center-back', 'centre forward', 'attacking midfielder', 'defensive midfielder',
    
    # Full backs
    'full-back', 'full back', 'left-back', 'left back', 'right-back', 'right back',
    
    # Wingers and wide positions
    'left-winger', 'left winger', 'right-winger', 'right winger',
    
    # Wide midfielders
    'left-midfielder', 'left midfielder', 'right-midfielder', 'right midfielder',
    
    # Wide forwards
    'left-forward', 'left forward', 'right-forward', 'right forward'
]

# Character normalization map
CHAR_MAP = {
    'ø': 'oe', 'æ': 'ae', 'å': 'aa', 'ö': 'oe', 'ä': 'ae', 'ü': 'ue', 'ß': 'ss',
    'ć': 'c', 'č': 'c', 'ş': 's', 'ğ': 'g', 'ı': 'i',
}

# Nickname mappings
NICKNAME_MAP = {
    # English nicknames
    'joshua': 'josh', 'benjamin': 'ben', 'matthew': 'matt', 'christopher': 'chris',
    'michael': 'mike', 'robert': 'rob', 'william': 'will', 'alexander': 'alex',
    'nicholas': 'nick', 'daniel': 'dan', 'anthony': 'tony', 'james': 'jim',
    'richard': 'rick', 'thomas': 'tom', 'tobias': 'toby', 'edward': 'ed',
    'timothy': 'tim', 'jonathan': 'jon', 'andrew': 'andy', 'samuel': 'sam',
    'joseph': 'joe', 'charles': 'charlie', 'david': 'dave', 'stephen': 'steve',
    'patrick': 'pat', 'frederick': 'fred', 'theodore': 'ted', 'oliver': 'ollie',
    'maximilian': 'max', 'gabriel': 'gabe',
    
    # Spanish/Latin nicknames
    'israel': 'isra', 'francisco': 'fran', 'santiago': 'santi', 'alejandro': 'alex',
    'eduardo': 'edu', 'ignacio': 'nacho', 'jose': 'pepe', 'roberto': 'beto',
    'alberto': 'beto', 'manuel': 'manu', 'emmanuel': 'manu', 'salvador': 'salva',
    'sebastian': 'seba', 'cristian': 'cris', 'fernando': 'fer', 'federico': 'fede',
    'ricardo': 'ricky', 'rodrigo': 'rodri', 'javier': 'javi'
}

# Initialize pytrends client
pytrends = TrendReq(
    hl='en-US',
    timeout=(3.05, 30),
    retries=MAX_RETRIES,
    backoff_factor=3.0,
    proxies=PROXIES
)

# Custom Exceptions
class RetryableError(Exception):
    """Exception for errors that can be retried"""
    pass

# Name Processing Functions
def normalize_name(name: str) -> str:
    """Normalize special characters in names and decode HTML entities"""
    decoded = html.unescape(name)
    
    # Replace special characters with their equivalents
    for special, replacement in CHAR_MAP.items():
        decoded = decoded.replace(special, replacement)
        decoded = decoded.replace(special.upper(), replacement.upper())
    
    # Normalize remaining special characters
    return unicodedata.normalize('NFKD', decoded).encode('ASCII', 'ignore').decode('utf-8')

def normalize_for_comparison(text: str) -> str:
    """Normalize text for name comparison by handling special cases"""
    text = html.unescape(text)
    
    # Handle name prefixes and special characters
    replacements = [
        ("'", ""), ("O'", "o"), ("Mc", "mac"), ("Mac", "mac"),
        ("gui", "gi"), ("gue", "ge"), ("qui", "ki"), ("que", "ke"),
        ("-", " "), (".", "")
    ]
    
    for original, replacement in replacements:
        text = text.replace(original, replacement)
    
    # Normalize spaces and unicode characters
    text = ' '.join(text.split())
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    
    # Remove very short words (likely initials)
    words = [w for w in text.lower().split() if len(w) > 1]
    
    return ' '.join(words).strip()

def get_name_variations(name: str) -> Set[str]:
    """Get common variations of a name, including nicknames"""
    variations = {name.lower()}
    parts = name.lower().split()
    
    # Add variations without middle names
    if len(parts) > 2:
        variations.add(f"{parts[0]} {parts[-1]}")
    
    # Add nickname variations
    if parts[0] in NICKNAME_MAP:
        if len(parts) > 1:
            variations.add(f"{NICKNAME_MAP[parts[0]]} {' '.join(parts[1:])}")
            variations.add(f"{NICKNAME_MAP[parts[0]]} {parts[-1]}")
        else:
            variations.add(NICKNAME_MAP[parts[0]])
    
    return variations

def normalize_name_parts(name: str) -> Set[str]:
    """Split a name into normalized parts, handling middle names"""
    name = normalize_for_comparison(name)
    parts = name.split()
    
    variations = {' '.join(parts)}  # Full name
    
    if len(parts) > 2:
        # Add version without middle names
        variations.add(f"{parts[0]} {parts[-1]}")
        variations.add(f"{parts[0]} {' '.join(parts[1:])}")
        
        # Add versions with partial middle names
        for i in range(1, len(parts)-1):
            variations.add(f"{parts[0]} {parts[i]} {parts[-1]}")
            variations.add(f"{parts[0]} {' '.join(parts[1:i+1])} {parts[-1]}")
    
    # Always add first and last name if we have at least 2 parts
    if len(parts) >= 2:
        variations.add(f"{parts[0]} {parts[-1]}")
    
    return variations

def get_player_name_variations(player: Dict) -> Set[str]:
    """Get all possible name variations for a player"""
    name_variations = set()
    
    # Use full name if available
    if player['player']['firstname'] and player['player']['lastname']:
        full_name = f"{player['player']['firstname']} {player['player']['lastname']}"
        name_variations.update(normalize_name_parts(full_name))
        
        # Add nickname variations
        for nickname in get_name_variations(full_name):
            name_variations.update(normalize_name_parts(nickname))
    
    # Add display name variations
    display_name = player['player']['name']
    name_variations.update(normalize_name_parts(display_name))
    
    return name_variations

# Matching Functions
def is_name_match(player: Dict, suggestion: Dict) -> bool:
    """Determine if a suggestion matches the player's name"""
    title = normalize_for_comparison(suggestion['title'])
    name_variations = get_player_name_variations(player)
    
    # Check all variations against the title
    for variation in name_variations:
        if variation in title or title in variation:
            return True
    
    # Special handling for names with initials
    display_name = player['player']['name']
    if '.' in display_name:
        name_parts = display_name.replace('-', ' ').split()
        player_surname = normalize_for_comparison(' '.join(name_parts[1:]))
        player_initial = name_parts[0].replace('.', '').strip().lower()
        
        title_words = title.lower().split()
        for i, word in enumerate(title_words):
            if word.startswith(player_initial):
                remaining_text = ' '.join(title_words[i:])
                if player_surname in remaining_text:
                    return True
    
    return False

def is_valid_player_type(type_lower: str) -> bool:
    """Check if the type indicates an active football player"""
    is_player = any(player_type in type_lower for player_type in VALID_PLAYER_TYPES)
    is_active = 'former' not in type_lower and 'retired' not in type_lower
    
    return is_player and is_active

def is_active_player(player: Dict) -> bool:
    """Determine if a player is active based on appearances or bench time"""
    games = player['statistics'][0]['games']
    has_appearances = games['appearences'] is not None and games['appearences'] > 0
    
    substitutes = player['statistics'][0]['substitutes']
    on_bench = substitutes['bench'] is not None and substitutes['bench'] > 0
    
    return has_appearances or on_bench

# API Functions
def get_topic_suggestions(pytrends_client, keyword: str, max_retries: int = MAX_RETRIES) -> List[Dict]:
    """Get topic suggestions with retry logic"""
    # Ensure minimum delay between API calls
    if hasattr(get_topic_suggestions, 'last_call'):
        time_since_last = time.time() - get_topic_suggestions.last_call
        if time_since_last < MIN_DELAY_BETWEEN_CALLS:
            time.sleep(MIN_DELAY_BETWEEN_CALLS - time_since_last)
    
    for attempt in range(max_retries):
        try:
            suggestions = pytrends_client.suggestions(keyword=keyword)
            get_topic_suggestions.last_call = time.time()
            return suggestions
            
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
            print(f"Timeout error on attempt {attempt + 1}/{max_retries}")
            print(f"Request details: keyword='{keyword}'")
            
            if attempt < max_retries - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
                
            raise RetryableError(f"Timeout error after {max_retries} attempts: {str(e)}")
            
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit error: {str(e)}")
                print(f"Attempt {attempt + 1}/{max_retries}, retrying in {RETRY_DELAYS[attempt]}s...")
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                raise RetryableError(f"Rate limit exceeded after {max_retries} attempts: {str(e)}")
            else:
                print(f"Non-retryable API error: {str(e)}")
                print(f"Request details: keyword='{keyword}', attempt={attempt + 1}")
                raise

def get_search_terms(player: Dict, team_name: str) -> List[str]:
    """Generate search terms for a player in priority order"""
    search_terms = []
    firstname = player['player']['firstname']
    lastname = player['player']['lastname']
    
    if firstname and lastname:
        full_name = f"{firstname} {lastname}"
        normalized_name = normalize_name(full_name)
        search_terms.extend([
            f"{normalized_name} {team_name}",
            f"{normalized_name} footballer",
            normalized_name
        ])
    
    # Add display name if different from full name
    display_name = player['player']['name']
    normalized_display = normalize_name(display_name)
    
    if display_name and normalized_display.lower() not in [term.lower() for term in search_terms]:
        search_terms.extend([
            f"{normalized_display} {team_name}",
            f"{normalized_display} footballer",
            normalized_display
        ])
    
    return search_terms

def find_player_topic(player: Dict, team_name: str) -> tuple:
    """Find Google Trends topic for a player, returning (topic, search_term)"""
    # Clean input names
    team_name = ' '.join(team_name.split())
    search_terms = get_search_terms(player, team_name)
    
    for search_term in search_terms:
        suggestions = get_topic_suggestions(pytrends, search_term)
        
        for suggestion in suggestions:
            type_lower = suggestion['type'].lower()
            
            if not is_valid_player_type(type_lower):
                continue
                
            if is_name_match(player, suggestion):
                return suggestion, search_term
                
    return None, None

def add_topic_to_player(player: Dict, topic: Dict) -> None:
    """Add topic data to player object"""
    player['topic_id'] = topic['mid']
    player['topic_title'] = topic['title']
    player['topic_type'] = topic['type']

def load_players() -> List[Dict]:
    """Load players data from file"""
    print("Loading players data...")
    with open(INPUT_FILE, 'r') as f:
        players = json.load(f)
    print(f"Loaded {len(players)} total players")
    return players

def filter_active_players(players: List[Dict]) -> List[Dict]:
    """Filter out inactive players"""
    print("\nFiltering active players...")
    active_players = [player for player in players if is_active_player(player)]
    print(f"Found {len(active_players)} active players")
    return active_players

def save_processed_players(processed_players: List[Dict]) -> None:
    """Save processed players to output file"""
    print("\nSaving preprocessed data...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(processed_players, f, indent=2)
    print(f"Saved {len(processed_players)} preprocessed players to {OUTPUT_FILE}")

def print_suggestions_for_player(player_name: str, search_terms: List[str]) -> None:
    """Print suggestions found for a player"""
    print("Tried following searches:")
    for search_term in search_terms:
        print(f"\nSearch term: '{search_term}'")
        suggestions = get_topic_suggestions(pytrends, search_term)
        if suggestions:
            print("Got suggestions:")
            for suggestion in suggestions:
                print(f"- {suggestion['title']} ({suggestion['type']}) [ID: {suggestion['mid']}]")
        else:
            print("No suggestions found")

def print_progress_update(current: int, total: int, processed_count: int, api_calls: int) -> None:
    """Print progress update"""
    success_rate = (processed_count/current*100)
    print(f"\n--- Progress Update ({current}/{total}) ---")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"API calls: {api_calls}\n")

def print_summary(processed_players: List[Dict], skipped_players: List[str], total: int, api_calls: int) -> None:
    """Print summary of processing results"""
    print(f"\n=== Processing Complete ===")
    print(f"Successfully processed: {len(processed_players)} players")
    print(f"Skipped: {len(skipped_players)} players")
    print(f"Success rate: {(len(processed_players)/total*100):.1f}%")
    print(f"Total API calls: {api_calls}")

def process_players(active_players: List[Dict]) -> tuple:
    """Process all active players to find their topic IDs"""
    print("\nSearching for player topic IDs...")
    processed_players = []
    skipped_players = []
    total = len(active_players)
    api_calls = 0
    
    for i, player in enumerate(active_players, 1):
        name = ' '.join(player['player']['name'].split())  # Clean name
        team = ' '.join(player['statistics'][0]['team']['name'].split())
        
        try:
            search_terms = get_search_terms(player, team)
            topic, found_with_term = find_player_topic(player, team)
            api_calls += len(search_terms)  # Count each search as an API call
            
            if topic:
                add_topic_to_player(player, topic)
                processed_players.append(player)
                print(f"[{i}/{total}] ✓ Found topic for {name}: {topic['title']} ({topic['type']}) [Search: {found_with_term}]")
            else:
                skipped_players.append(name)
                print(f"[{i}/{total}] ✗ No topic found for {name}")
                print_suggestions_for_player(name, search_terms)
                
        except RetryableError as e:
            print(f"[{i}/{total}] ! Retryable error processing {name} ({team})")
            print(f"Error details: {str(e)}")
            skipped_players.append(name)
        except Exception as e:
            print(f"[{i}/{total}] ! Fatal error processing {name} ({team})")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            print("Stack trace follows:")
            raise
        
        # Show stats every 100 players
        if i % 100 == 0:
            print_progress_update(i, total, len(processed_players), api_calls)
    
    print_summary(processed_players, skipped_players, total, api_calls)
    return processed_players, skipped_players, api_calls

def preprocess_players():
    """Main function to preprocess player data"""
    print("\n=== Starting Player Preprocessing ===")
    
    players = load_players()
    active_players = filter_active_players(players)
    processed_players, _, _ = process_players(active_players)
    
    if processed_players:
        save_processed_players(processed_players)
    else:
        print("\nFailed to process any players.")
    
    print("\n=== Preprocessing Complete ===")

if __name__ == "__main__":
    try:
        # Initialize the last call time
        get_topic_suggestions.last_call = 0
        preprocess_players()
    except Exception as e:
        print(f"\nError during preprocessing: {str(e)}")
        raise 