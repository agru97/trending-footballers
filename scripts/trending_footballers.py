"""
Trending Footballers Script

This script runs a tournament-style competition to find the most trending footballers
using Google Trends data. It processes players in groups and ultimately determines
the top 5 trending players.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from pytrends.request import TrendReq
import pandas as pd
import random

# Configuration
pd.set_option('future.no_silent_downcasting', True)

# Constants
INPUT_FILE = 'public/preprocessed_players.json'
OUTPUT_FILE = 'public/trending_footballers.json'
PROXIES = os.environ['PROXY_LIST'].split(',') if 'PROXY_LIST' in os.environ else []
random.shuffle(PROXIES)  # Shuffle proxies for better load distribution
MIN_DELAY_BETWEEN_CALLS = 1  # Minimum seconds between API calls
RATE_LIMIT_PAUSE = 60  # Seconds to pause when hitting rate limit
MAX_RETRIES = 3
MAX_NO_DATA_RETRIES = 2
RETRY_DELAYS = [2, 5, 10]  # Increasing delays between retries
TOURNAMENT_THRESHOLD = 25  # When to switch to final round

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# Initialize global variables
api_calls_counter = 0
pytrends = TrendReq(
    timeout=(3.05, 30),
    retries=MAX_RETRIES,
    backoff_factor=3.0,
    proxies=PROXIES
)
get_trends_data_last_call = 0  # Track last API call time


class TimingStats:
    """Track timing statistics for API calls"""
    def __init__(self):
        self.start_time = None
        self.api_calls = []

    def start(self):
        self.start_time = datetime.now()
        
    def add_api_call(self, duration: timedelta):
        self.api_calls.append(duration)
        
    def get_total_time(self) -> timedelta:
        if self.start_time:
            return datetime.now() - self.start_time
        return timedelta(0)
        
    def get_avg_call_time(self) -> timedelta:
        if not self.api_calls:
            return timedelta(0)
        return sum(self.api_calls, timedelta(0)) / len(self.api_calls)


class ProgressDisplay:
    """Handle progress display and updates"""
    def __init__(self, total: int, desc: str = "Processing"):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = datetime.now()
        self.last_api_call_time = None
        
    def start(self):
        self.start_time = datetime.now()
        print(f"\n{Colors.BLUE}=== {self.desc} ==={Colors.RESET}")
    
    def update(self, current: int):
        self.current = current
        self._print_progress_bar()
    
    def set_api_call_time(self, duration: timedelta):
        self.last_api_call_time = duration.total_seconds()
    
    def set_message(self, message: str, status: str = "warning"):
        color = Colors.RED if status == "error" else Colors.YELLOW
        if status == "error":
            print(f"\n{color}⚠ {message}{Colors.RESET}")
            self._print_progress_bar()
    
    def clear_message(self):
        # No-op, kept for interface consistency
        pass
    
    def _print_progress_bar(self):
        elapsed = datetime.now() - self.start_time
        progress = int(50 * self.current / self.total)
        bar = Colors.GREEN + '=' * progress + Colors.RESET + '-' * (50 - progress)
        percent = int(100 * self.current / self.total)
        
        timing_info = []
        if self.last_api_call_time:
            timing_info.append(f"API: {self.last_api_call_time:.1f}s")
        timing_info.append(f"Total: {elapsed.total_seconds():.1f}s")
        
        print(f"\r{Colors.BLUE}▶{Colors.RESET} [{bar}] {percent}% ({self.current}/{self.total}) | "
              f"{' | '.join(timing_info)}", end='', flush=True)
    
    def show_group_result(self, group_num: int, players: List[Dict], 
                          scores: Dict[str, float], winners: List[str]):
        player_scores = []
        for player in players:
            name = player['player']['name']
            score = scores.get(name, 0)
            if name in winners:
                player_scores.append(f"{Colors.GREEN}★{name}({score}){Colors.RESET}")
            else:
                player_scores.append(f"{name}({score})")
        
        print(f"\rGroup {group_num}: " + " | ".join(player_scores))
    
    def finish(self):
        print('\n')  # Add extra line for spacing
        elapsed = datetime.now() - self.start_time
        print(f"{Colors.GREEN}✓ Done in {elapsed.total_seconds():.1f}s{Colors.RESET}\n")


# Utility Functions
def log_message(message: str, color: Optional[str] = None):
    """Print a message with optional color"""
    if color:
        print(f"{color}{message}{Colors.RESET}")
    else:
        print(message)


def format_player_name_with_score(player: Dict, score: float, prefix: str = "") -> str:
    """Format a player's name with score and team"""
    name = player['player']['name']
    team = player['statistics'][0]['team']['name']
    return f"{prefix}{name:<20} {score:>3} ({team})"


def get_player_identifier(player: Dict) -> str:
    """Get the appropriate identifier for a player (topic ID or name)"""
    topic_id = player['topic_id']
    if topic_id.startswith('/m/') or topic_id.startswith('/g/'):
        return topic_id
    return player['player']['name']


def wait_between_api_calls():
    """Ensure minimum delay between API calls"""
    global get_trends_data_last_call
    time_since_last = time.time() - get_trends_data_last_call
    if time_since_last < MIN_DELAY_BETWEEN_CALLS:
        time.sleep(MIN_DELAY_BETWEEN_CALLS - time_since_last)


def get_trends_data(players_group: List[Dict], 
                    progress: Optional[ProgressDisplay] = None) -> Dict[str, float]:
    """Query Google Trends for a group of players"""
    global api_calls_counter, get_trends_data_last_call, timing_stats
    
    # Ensure minimum delay between API calls
    wait_between_api_calls()
    
    # Map players to their identifiers
    player_identifiers = {get_player_identifier(player): player for player in players_group}
    search_names = list(player_identifiers.keys())
    
    # Create mapping of topic IDs to player names for display
    player_names = {player['topic_id']: player['player']['name'] for player in players_group}
    
    # Display players in the current group
    if progress and players_group:
        names_list = [p['player']['name'] for p in players_group]
        progress.set_message(f"Group: {' | '.join(names_list)}")
    
    # Try to get data with retries
    for no_data_attempt in range(MAX_NO_DATA_RETRIES + 1):
        try:
            # Record API call timing
            call_start = datetime.now()
            time.sleep(MIN_DELAY_BETWEEN_CALLS)  # Add delay before API call
            
            # Make the API call
            pytrends.build_payload(
                search_names,
                timeframe='now 1-d',
                geo='',
                gprop=''
            )
            
            # Update counters and timing
            api_calls_counter += 1
            get_trends_data_last_call = time.time()
            interest_data = pytrends.interest_over_time()
            call_duration = datetime.now() - call_start
            timing_stats.add_api_call(call_duration)
            
            if progress:
                progress.set_api_call_time(call_duration)
            
            # Handle empty response
            if interest_data.empty:
                if no_data_attempt < MAX_NO_DATA_RETRIES:
                    delay = RETRY_DELAYS[no_data_attempt]
                    if progress:
                        names = [player_names.get(topic_id, topic_id) for topic_id in search_names]
                        progress.set_message(
                            f"No data received (attempt {no_data_attempt + 1}/{MAX_NO_DATA_RETRIES + 1}), "
                            f"retrying in {delay}s for: {', '.join(names)}",
                            status="warning"
                        )
                    time.sleep(delay)
                    continue
                else:
                    if progress:
                        names = [player_names.get(topic_id, topic_id) for topic_id in search_names]
                        progress.set_message(
                            f"No data after {MAX_NO_DATA_RETRIES + 1} attempts for: {', '.join(names)}",
                            status="error"
                        )
                    return {player['player']['name']: 0 for player in players_group}
            
            if progress:
                progress.clear_message()
            
            # Map scores back to original player names
            results = {}
            for search_name, player in player_identifiers.items():
                original_name = player['player']['name']
                score = round(interest_data[search_name].max(), 2)
                
                # If we already have a score for this player, take the higher one
                if original_name in results:
                    results[original_name] = max(results[original_name], score)
                else:
                    results[original_name] = score
            
            return results
            
        except Exception as e:
            # Handle rate limiting errors
            is_rate_limit = "429" in str(e)
            
            if no_data_attempt < MAX_NO_DATA_RETRIES:
                # Determine retry delay
                delay = RATE_LIMIT_PAUSE if is_rate_limit else RETRY_DELAYS[no_data_attempt]
                
                if progress:
                    error_msg = (
                        f"Rate limit hit, pausing for {delay}s before retry" 
                        if is_rate_limit else
                        f"Error occurred (attempt {no_data_attempt + 1}/{MAX_NO_DATA_RETRIES + 1}): {str(e)}, retrying in {delay}s"
                    )
                    progress.set_message(error_msg, status="warning")
                
                time.sleep(delay)
                continue
            
            # All retries failed
            error_msg = "Failed due to rate limiting (HTTP 429)" if is_rate_limit else f"All retries failed for group: {str(e)}"
            log_message(f"\n{error_msg}", Colors.RED)
            log_message(f"Failed players: {', '.join(search_names)}", Colors.RED)
            log_message("Stopping script due to repeated failures", Colors.RED)
            exit(1)


def is_active_player(player: Dict) -> bool:
    """Determine if a player is active based on game appearances or bench time"""
    games = player['statistics'][0]['games']
    has_appearances = games['appearences'] is not None and games['appearences'] > 0
    
    substitutes = player['statistics'][0]['substitutes']
    on_bench = substitutes['bench'] is not None and substitutes['bench'] > 0
    
    return has_appearances or on_bench


def filter_active_players(players: List[Dict]) -> List[Dict]:
    """Filter to get only active players"""
    return [player for player in players if is_active_player(player)]


def run_tournament_round(players: List[Dict], 
                         players_to_keep: int = 2,
                         round_num: int = 1) -> List[Dict]:
    """Run one round of the tournament"""
    results = []
    total_groups = (len(players) + 4) // 5
    
    progress = ProgressDisplay(total_groups, desc=f"Round {round_num}")
    progress.start()
    
    for i in range(0, len(players), 5):
        group = players[i:min(i+5, len(players))]
        if len(group) < 2:  # Skip groups that are too small
            results.extend(group)
            continue
        
        # Get scores for this group
        scores = get_trends_data(group, progress)
        
        # Sort players by score and get winners
        sorted_group = sorted(group, key=lambda p: scores.get(p['player']['name'], 0), reverse=True)
        winners = [p['player']['name'] for p in sorted_group[:players_to_keep]]
        
        # Show group results
        group_num = (i + 5) // 5
        progress.show_group_result(group_num, group, scores, winners)
        
        # Keep top players from this group
        results.extend(sorted_group[:players_to_keep])
        progress.update(group_num)
    
    progress.finish()
    
    # Deduplicate players by name, keeping highest score
    seen_players = {}
    for player in results:
        name = player['player']['name']
        if name not in seen_players:
            seen_players[name] = player
    
    return list(seen_players.values())


def get_detailed_interest_data(players: List[Dict]) -> Dict[str, Dict]:
    """Get detailed interest over time data for players"""
    try:
        # Use appropriate identifiers for the players
        player_identifiers = [get_player_identifier(player) for player in players]
        
        # Log what we're fetching
        log_message(f"Fetching interest over time for topics: {player_identifiers}", Colors.BLUE)
        
        # Make API call
        pytrends.build_payload(
            player_identifiers,
            timeframe='now 1-d',
            geo='',
            gprop=''
        )
        
        interest_data = pytrends.interest_over_time()
        log_message(f"Got interest data with columns: {interest_data.columns}", Colors.BLUE)
        
        # Convert to dictionary with player names as keys
        result = {}
        player_map = {get_player_identifier(player): player for player in players}
        
        for topic_id, player in player_map.items():
            player_name = player['player']['name']
            
            if topic_id in interest_data:
                # Convert values to native Python types
                values = [float(x) for x in interest_data[topic_id].values]
                dates = [d.strftime('%Y-%m-%d %H:%M:%S') for d in interest_data.index]
                
                result[player_name] = {
                    "values": values,
                    "dates": dates
                }
                
                log_message(f"Added {len(values)} data points for {player_name}", Colors.BLUE)
            
        return result
        
    except Exception as e:
        log_message(f"Warning: Could not fetch detailed data: {str(e)}", Colors.YELLOW)
        log_message(f"Full error: {type(e).__name__}: {str(e)}", Colors.YELLOW)
        return {}


def run_knockout_phase(top_4: List[Dict], challengers: List[Dict]) -> Tuple[Dict, float]:
    """Run the knockout phase to find the best 5th player"""
    progress = ProgressDisplay(len(challengers), desc="Processing challengers")
    progress.start()
    
    current_group = top_4.copy()
    best_fifth = None
    best_fifth_score = -1
    
    for i, challenger in enumerate(challengers):
        # Compare top 4 against this challenger
        comparison_group = current_group + [challenger]
        scores = get_trends_data(comparison_group, progress)
        
        # Sort based on this comparison
        comparison_group.sort(key=lambda p: scores.get(p['player']['name'], 0), reverse=True)
        
        # Check if challenger made it into top 4
        if challenger in comparison_group[:4]:
            # Challenger succeeded, update current top 4
            current_group = comparison_group[:4]
        else:
            # Challenger failed, check if they're better than current best 5th
            challenger_score = scores.get(challenger['player']['name'], 0)
            if challenger_score > best_fifth_score:
                best_fifth = challenger
                best_fifth_score = challenger_score
                log_message(f"\nNew best 5th: {challenger['player']['name']} ({challenger_score})", Colors.GREEN)
        
        # Show current standings
        winners = [p['player']['name'] for p in comparison_group[:4]]
        progress.show_group_result(i+1, comparison_group, scores, winners)
        progress.update(i+1)
    
    progress.finish()
    return best_fifth, best_fifth_score


def find_best_fifth(top_4: List[Dict], remaining_players: List[Dict]) -> Tuple[Dict, float]:
    """Find the best 5th place player from all remaining players"""
    log_message("\nFinding best 5th place from all remaining players...", Colors.BLUE)
    progress = ProgressDisplay(len(remaining_players), desc="Testing for 5th place")
    progress.start()
    
    best_fifth = None
    best_fifth_score = -1
    
    # Test each remaining player against the top 4
    for i, player in enumerate(remaining_players):
        comparison_group = top_4 + [player]
        scores = get_trends_data(comparison_group, progress)
        player_score = scores.get(player['player']['name'], 0)
        
        if player_score > best_fifth_score:
            best_fifth = player
            best_fifth_score = player_score
            log_message(f"\nNew best 5th: {player['player']['name']} ({player_score})", Colors.GREEN)
        
        # Show result
        winners = [p['player']['name'] for p in top_4]
        progress.show_group_result(i+1, comparison_group, scores, winners)
        progress.update(i+1)
    
    progress.update(len(remaining_players))
    progress.finish()
    
    return best_fifth, best_fifth_score


def run_final_round(players: List[Dict]) -> Tuple[List[Dict], Dict[str, float]]:
    """Run final round as a knockout system"""
    log_message("\n=== Final Round ===", Colors.GREEN)
    log_message(f"Starting final round with {len(players)} players", Colors.BLUE)
    
    # Initialize with first 5 players
    current_group = players[:5]
    challengers = players[5:]
    
    # Get initial scores and sort initial group
    initial_scores = get_trends_data(current_group)
    current_group.sort(key=lambda p: initial_scores.get(p['player']['name'], 0), reverse=True)
    
    # Show initial top 5
    log_message("\nInitial Top 5:", Colors.BLUE)
    for i, player in enumerate(current_group, 1):
        name = player['player']['name']
        score = initial_scores.get(name, 0)
        log_message(format_player_name_with_score(player, score, prefix=f"{i}. "), Colors.BLUE)
    
    # Process challengers to find top 4
    best_fifth, _ = run_knockout_phase(current_group[:4], challengers)
    top_4 = current_group[:4]
    
    # Find best 5th from all remaining players
    remaining_players = [p for p in players if p not in top_4]
    best_fifth, _ = find_best_fifth(top_4, remaining_players)
    
    # Final comparison of top 4 plus best 5th place
    final_group = top_4 + [best_fifth]
    final_scores = get_trends_data(final_group)
    final_group.sort(key=lambda p: final_scores.get(p['player']['name'], 0), reverse=True)
    
    # Get detailed data for the final top 5
    log_message("\nGetting detailed data for final top 5...", Colors.BLUE)
    detailed_data = get_detailed_interest_data(final_group[:5])
    
    # Save results
    save_results(final_group[:5], final_scores, interest_data=detailed_data)
    
    return final_group, final_scores


def save_results(top_5: List[Dict], scores: Dict[str, float], 
                 interest_data: Optional[Dict] = None) -> None:
    """Save the final results to JSON"""
    # Create output directory
    os.makedirs('public', exist_ok=True)
    
    # Load preprocessed players to get full data
    with open(INPUT_FILE, 'r') as f:
        preprocessed_players = json.load(f)
    
    # Create lookup for preprocessed players
    player_lookup = {p['player']['name']: p for p in preprocessed_players}
    
    # Sort players by score
    sorted_players = sorted(top_5, key=lambda p: scores[p['player']['name']], reverse=True)
    
    # Prepare final data structure
    result = {
        "updated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        "players": []
    }
    
    # Add data for each player
    for rank, player in enumerate(sorted_players, 1):
        player_name = player['player']['name']
        player_data = player_lookup[player_name]
        trending_score = float(scores[player_name])
        
        # Create player entry with base data
        player_entry = {
            "rank": rank,
            "trending_score": trending_score,
            "player": player_data["player"],
            "statistics": player_data["statistics"],
            "topic_id": player_data["topic_id"],
            "topic_title": player_data["topic_title"],
            "topic_type": player_data["topic_type"]
        }
        
        # Add interest over time data if available
        if interest_data and player_name in interest_data:
            player_entry["interest_over_time"] = interest_data[player_name]
            log_message(f"Added interest data to {player_name} entry with "
                       f"{len(interest_data[player_name]['values'])} points", Colors.BLUE)
        
        result["players"].append(player_entry)
    
    # Save to JSON with atomic write
    json_path = OUTPUT_FILE
    tmp_json_path = json_path + '.tmp'
    
    try:
        with open(tmp_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        os.replace(tmp_json_path, json_path)
        log_message(f"Successfully saved JSON with {len(result['players'])} players to {json_path}", 
                   Colors.GREEN)
        
    except Exception as e:
        if os.path.exists(tmp_json_path):
            os.remove(tmp_json_path)
        raise e


def load_players() -> List[Dict]:
    """Load preprocessed players from file"""
    with open(INPUT_FILE, 'r') as f:
        return json.load(f)


def fetch_trending_footballers(test_limit: Optional[int] = None) -> None:
    """Main function to find trending footballers"""
    try:
        global api_calls_counter
        api_calls_counter = 0
        timing_stats.start()
        
        # Load players
        active_players = load_players()
        log_message("\n=== Tournament Start ===", Colors.BLUE)
        log_message(f"Total active players: {len(active_players)}", Colors.BLUE)
        
        # Handle test mode
        if test_limit:
            active_players = active_players[:test_limit]
            log_message(f"TEST MODE: Limited to {test_limit} players\n", Colors.YELLOW)
        else:
            random.shuffle(active_players)
            log_message("Randomly shuffled players for fair competition\n", Colors.BLUE)

        # Run tournament rounds until we reach the threshold
        current_players = active_players
        round_num = 1
        
        while len(current_players) > TOURNAMENT_THRESHOLD:
            log_message(f"\n=== Round {round_num} ===", Colors.BLUE)
            log_message(f"Processing {len(current_players)} players in "
                       f"{(len(current_players) + 4) // 5} groups", Colors.BLUE)
            current_players = run_tournament_round(current_players, players_to_keep=2, round_num=round_num)
            round_num += 1

        # Run final round with remaining players
        final_5, final_scores = run_final_round(current_players)
        
        # Display final results
        log_message("\n=== Final Results ===", Colors.GREEN)
        log_message("Top 5 Trending Footballers:", Colors.GREEN)
        for i, player in enumerate(final_5, 1):
            name = player['player']['name']
            score = final_scores[name]
            log_message(format_player_name_with_score(player, score, prefix=f"{i}. "), Colors.GREEN)
        
        # Show performance stats
        total_time = timing_stats.get_total_time()
        avg_call_time = timing_stats.get_avg_call_time()
        
        log_message("\n=== Performance Stats ===", Colors.YELLOW)
        log_message(f"Total time: {total_time.total_seconds():.1f}s", Colors.YELLOW)
        log_message(f"Total API calls: {api_calls_counter}", Colors.YELLOW)
        log_message(f"Average call time: {avg_call_time.total_seconds():.1f}s", Colors.YELLOW)
        log_message("=== Tournament Complete ===\n", Colors.BLUE)
        
    except Exception as e:
        log_message(f"Error: {str(e)}", Colors.RED)
        raise


# Initialize global timing stats
timing_stats = TimingStats()

if __name__ == "__main__":
    try:
        fetch_trending_footballers()
        log_message("Successfully updated top 5 footballers data", Colors.GREEN)
    except Exception as e:
        log_message(f"Error occurred: {str(e)}", Colors.RED)
        log_message(f"Error type: {type(e).__name__}", Colors.RED)
        import traceback
        log_message(f"Stack trace:\n{traceback.format_exc()}", Colors.RED)
        exit(1)
