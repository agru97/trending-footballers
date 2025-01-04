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
from datetime import datetime
from pytrends.request import TrendReq
import html
import requests
import random

# Constants
PROXIES = os.environ['PROXY_LIST'].split(',') if 'PROXY_LIST' in os.environ else []
random.shuffle(PROXIES)  # Shuffle proxies for better load distribution
MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]
MIN_DELAY_BETWEEN_CALLS = 1  # Minimum seconds between API calls

# Initialize pytrends once
pytrends = TrendReq(
    hl='en-US',
    timeout=(3.05, 30),
    retries=MAX_RETRIES,
    backoff_factor=3.0,
    proxies=PROXIES
)

# Custom Exceptions
class RetryableError(Exception):
    pass

# Name Processing Functions
def normalize_name(name):
    """Normalize special characters in names and decode HTML entities"""
    # First decode HTML entities (like &apos; -> ')
    decoded = html.unescape(name)
    
    # Map of special characters to their common equivalents
    char_map = {
        'ø': 'oe',
        'æ': 'ae',
        'å': 'aa',
        'ö': 'oe',
        'ä': 'ae',
        'ü': 'ue',
        'ß': 'ss',
        'ć': 'c',
        'č': 'c',
        'ş': 's',
        'ğ': 'g',
        'ı': 'i',
    }
    
    # Replace special characters with their equivalents
    for special, replacement in char_map.items():
        decoded = decoded.replace(special, replacement)
        decoded = decoded.replace(special.upper(), replacement.upper())
    
    # Then normalize remaining special characters
    normalized = unicodedata.normalize('NFKD', decoded).encode('ASCII', 'ignore').decode('utf-8')
    return normalized

def normalize_for_comparison(text):
    """Normalize text for name comparison by handling special cases"""
    # First decode HTML entities (like &apos; -> ')
    text = html.unescape(text)
    
    # Handle special cases for Irish/Scottish names
    text = text.replace("'", "")  # Remove apostrophes
    text = text.replace("O'", "o")  # Normalize O' prefix
    text = text.replace("Mc", "mac")  # Normalize Mc prefix
    text = text.replace("Mac", "mac")  # Normalize Mac prefix
    
    # Handle Basque/Spanish name variations
    text = text.replace("gui", "gi")  # Eguiluz -> Egiluz
    text = text.replace("gue", "ge")  # Miguel -> Migel
    text = text.replace("qui", "ki")  # Enrique -> Enrike
    text = text.replace("que", "ke")  # Quevedo -> Kevedo
    
    # First normalize the text
    text = text.replace('-', ' ')  # Replace hyphens with spaces
    text = text.replace('.', '')   # Remove dots from initials
    text = ' '.join(text.split())  # Handle all whitespace
    
    # Normalize unicode characters (like ć -> c)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    
    # Split into words and remove very short parts (likely initials)
    words = [w for w in text.lower().split() if len(w) > 1]
    
    return ' '.join(words).strip()

def get_name_variations(name):
    """Get common variations of a name, including nicknames"""
    variations = set()
    
    # Common nickname mappings
    nickname_map = {
        # English nicknames
        'joshua': 'josh',
        'benjamin': 'ben',
        'matthew': 'matt',
        'christopher': 'chris',
        'michael': 'mike',
        'robert': 'rob',
        'william': 'will',
        'alexander': 'alex',
        'nicholas': 'nick',
        'daniel': 'dan',
        'anthony': 'tony',
        'james': 'jim',
        'richard': 'rick',
        'thomas': 'tom',
        'tobias': 'toby',
        'edward': 'ed',
        'timothy': 'tim',
        'jonathan': 'jon',
        'andrew': 'andy',
        'samuel': 'sam',
        'joseph': 'joe',
        'charles': 'charlie',
        'david': 'dave',
        'stephen': 'steve',
        'patrick': 'pat',
        'frederick': 'fred',
        'theodore': 'ted',
        'oliver': 'ollie',
        'maximilian': 'max',
        'gabriel': 'gabe',
        
        # Spanish/Latin nicknames
        'israel': 'isra',
        'francisco': 'fran',
        'santiago': 'santi',
        'alejandro': 'alex',
        'eduardo': 'edu',
        'ignacio': 'nacho',
        'jose': 'pepe',
        'roberto': 'beto',
        'alberto': 'beto',
        'manuel': 'manu',
        'emmanuel': 'manu',
        'salvador': 'salva',
        'sebastian': 'seba',
        'cristian': 'cris',
        'fernando': 'fer',
        'federico': 'fede',
        'ricardo': 'ricky',
        'rodrigo': 'rodri',
        'javier': 'javi'
    }
    
    # Add the original name
    variations.add(name.lower())
    
    # Split the name into parts
    parts = name.lower().split()
    
    # Add variations without middle names
    if len(parts) > 2:
        variations.add(f"{parts[0]} {parts[-1]}")
    
    # Add nickname variations
    if parts[0] in nickname_map:
        if len(parts) > 1:
            variations.add(f"{nickname_map[parts[0]]} {' '.join(parts[1:])}")
            variations.add(f"{nickname_map[parts[0]]} {parts[-1]}")
        else:
            variations.add(nickname_map[parts[0]])
    
    return variations

def normalize_name_parts(name):
    """Split a name into normalized parts, handling middle names"""
    # First normalize the text
    name = normalize_for_comparison(name)
    parts = name.split()
    
    # Handle middle names - create variations with and without middle names
    variations = set()
    variations.add(' '.join(parts))  # Full name
    
    if len(parts) > 2:
        # Add version without middle names
        variations.add(f"{parts[0]} {parts[-1]}")  # First and last only
        variations.add(f"{parts[0]} {' '.join(parts[1:])}")  # First and rest
        
        # Add versions with partial middle names
        for i in range(1, len(parts)-1):
            # Include first name, current middle name, and last name
            variations.add(f"{parts[0]} {parts[i]} {parts[-1]}")
            # Include first name and all names up to current
            variations.add(f"{parts[0]} {' '.join(parts[1:i+1])} {parts[-1]}")
    
    # Always add first and last name if we have at least 2 parts
    if len(parts) >= 2:
        variations.add(f"{parts[0]} {parts[-1]}")
    
    return variations

# Matching Functions
def is_name_match(player, suggestion):
    """Determine if a suggestion matches the player's name"""
    # Normalize the suggestion title
    title = normalize_for_comparison(suggestion['title'])
    
    # Get all name variations to check
    name_variations = set()
    
    # 1. Try with full name if available
    if player['player']['firstname'] and player['player']['lastname']:
        full_name = f"{player['player']['firstname']} {player['player']['lastname']}"
        name_variations.update(normalize_name_parts(full_name))
        
        # Add nickname variations
        nickname_variations = get_name_variations(full_name)
        # Flatten the sets of name variations
        for nickname in nickname_variations:
            name_variations.update(normalize_name_parts(nickname))
    
    # 2. Add display name variations
    display_name = player['player']['name']
    name_variations.update(normalize_name_parts(display_name))
    
    # Check all variations against the title
    for variation in name_variations:
        if variation in title:
            return True
        # Also check if title is in any of our variations
        # This helps with cases where the suggestion is shorter than our name
        if title in variation:
            return True
    
    # Special handling for names with initials
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

def is_valid_player_type(type_lower):
    """Check if the type indicates an active football player"""
    
    # List of valid player type indicators
    valid_types = [
        # General player types
        'footballer',
        'football player',
        'soccer player',
        
        # Basic positions
        'goalkeeper',
        'defender',
        'midfielder',
        'forward',
        'striker',
        'winger',
        
        # Specific positions (with variations combined)
        'centre-back', 'center-back',
        'centre forward',
        'attacking midfielder',
        'defensive midfielder',
        
        # Full backs
        'full-back', 'full back',
        'left-back', 'left back',
        'right-back', 'right back',
        
        # Wingers and wide positions
        'left-winger', 'left winger',
        'right-winger', 'right winger',
        
        # Wide midfielders
        'left-midfielder', 'left midfielder',
        'right-midfielder', 'right midfielder',
        
        # Wide forwards
        'left-forward', 'left forward',
        'right-forward', 'right forward'
    ]
    
    # Check if any valid type is in the string
    is_player = any(t in type_lower for t in valid_types)
    
    # Check not retired/former
    is_active = 'former' not in type_lower and 'retired' not in type_lower
    
    return is_player and is_active

# API Functions
def get_topic_suggestions(pytrends, keyword, max_retries=MAX_RETRIES):
    """Get topic suggestions with retry logic"""
    # Ensure minimum delay between API calls
    if hasattr(get_topic_suggestions, 'last_call'):
        time_since_last = time.time() - get_topic_suggestions.last_call
        if time_since_last < MIN_DELAY_BETWEEN_CALLS:
            time.sleep(MIN_DELAY_BETWEEN_CALLS - time_since_last)
    
    for attempt in range(max_retries):
        try:
            suggestions = pytrends.suggestions(keyword=keyword)
            get_topic_suggestions.last_call = time.time()  # Update last call time
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

def get_search_terms(player, team_name):
    """Generate search terms for a player"""
    search_terms = []
    
    # Get the player's full name if available
    firstname = player['player']['firstname']
    lastname = player['player']['lastname']
    
    if firstname and lastname:
        # Try full name with team first
        full_name = f"{firstname} {lastname}"
        search_terms.append(f"{normalize_name(full_name)} {team_name}")
        search_terms.append(f"{normalize_name(full_name)} footballer")
        search_terms.append(normalize_name(full_name))
    
    # Fallback to display name if different
    display_name = player['player']['name']
    if display_name and display_name.lower() not in [term.lower() for term in search_terms]:
        search_terms.append(f"{normalize_name(display_name)} {team_name}")
        search_terms.append(f"{normalize_name(display_name)} footballer")
        search_terms.append(normalize_name(display_name))
    
    return search_terms

# Main Processing Function
def preprocess_players():
    """Main function to preprocess player data"""
    print("\n=== Starting Player Preprocessing ===")
    
    # Load players data
    print("Loading players data...")
    with open('public/players.json', 'r') as f:
        players = json.load(f)
    print(f"Loaded {len(players)} total players")
    
    # Filter active players
    print("\nFiltering active players...")
    active_players = []
    for player in players:
        games = player['statistics'][0]['games']
        # Check if player has any appearances or has been on the bench
        if (games['appearences'] is not None and games['appearences'] > 0) or \
           (player['statistics'][0]['substitutes']['bench'] is not None and 
            player['statistics'][0]['substitutes']['bench'] > 0):
            active_players.append(player)
    
    print(f"Found {len(active_players)} active players")
    
    # Process players and find their topic IDs
    print("\nSearching for player topic IDs...")
    processed_players = []
    skipped_players = []
    total = len(active_players)
    api_calls = 0
    
    for i, player in enumerate(active_players, 1):
        name = player['player']['name']
        team = player['statistics'][0]['team']['name']
        
        try:
            # Clean the names first
            name = ' '.join(name.split())  # Remove tabs and normalize spaces
            team = ' '.join(team.split())  # Clean team name too
            
            # Get search terms in priority order
            search_terms = get_search_terms(player, team)
            
            footballer_topic = None
            found_with_term = None
            
            for search_term in search_terms:
                if footballer_topic:
                    break
                    
                suggestions = get_topic_suggestions(pytrends, search_term)
                api_calls += 1
                
                for suggestion in suggestions:
                    type_lower = suggestion['type'].lower()
                    
                    # First check: Must be a footballer/soccer player and not retired
                    is_active_player = is_valid_player_type(type_lower)
                    
                    if not is_active_player:
                        continue  # Skip to next suggestion if not an active player
                    
                    # Then check: Name must match using strict rules
                    name_matches = is_name_match(player, suggestion)
                    
                    if is_active_player and name_matches:
                        footballer_topic = suggestion
                        found_with_term = search_term
                        break
            
            if footballer_topic:
                # Add topic data to player
                player['topic_id'] = footballer_topic['mid']
                player['topic_title'] = footballer_topic['title']
                player['topic_type'] = footballer_topic['type']
                processed_players.append(player)
                print(f"[{i}/{total}] ✓ Found topic for {name}: {footballer_topic['title']} ({footballer_topic['type']}) [Search: {found_with_term}]")
            else:
                skipped_players.append(name)
                print(f"[{i}/{total}] ✗ No topic found for {name}")
                print("Tried following searches:")
                
                # Try each search term and show results
                for search_term in search_terms:
                    print(f"\nSearch term: '{search_term}'")
                    suggestions = get_topic_suggestions(pytrends, search_term)
                    if suggestions:
                        print("Got suggestions:")
                        for s in suggestions:
                            print(f"- {s['title']} ({s['type']}) [ID: {s['mid']}]")
                    else:
                        print("No suggestions found")
                
        except RetryableError as e:
            print(f"[{i}/{total}] ! Retryable error processing {name} ({team})")
            print(f"Error details: {str(e)}")
            skipped_players.append(name)
        except Exception as e:
            print(f"[{i}/{total}] ! Fatal error processing {name} ({team})")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            print("Stack trace follows:")
            raise  # Stop execution on fatal errors
        
        # Show stats every 100 players
        if i % 100 == 0:
            success_rate = (len(processed_players)/i*100)
            print(f"\n--- Progress Update ({i}/{total}) ---")
            print(f"Success rate: {success_rate:.1f}%")
            print(f"API calls: {api_calls}\n")
    
    print(f"\n=== Processing Complete ===")
    print(f"Successfully processed: {len(processed_players)} players")
    print(f"Skipped: {len(skipped_players)} players")
    print(f"Success rate: {(len(processed_players)/total*100):.1f}%")
    print(f"Total API calls: {api_calls}")
    
    # Save preprocessed data
    print("\nSaving preprocessed data...")
    output_file = 'public/preprocessed_players.json'
    with open(output_file, 'w') as f:
        json.dump(processed_players, f, indent=2)
    
    print(f"Saved {len(processed_players)} preprocessed players to {output_file}")
    print("\n=== Preprocessing Complete ===")

if __name__ == "__main__":
    try:
        # Initialize the last call time
        get_topic_suggestions.last_call = 0
        preprocess_players()
    except Exception as e:
        print(f"\nError during preprocessing: {str(e)}")
        raise 