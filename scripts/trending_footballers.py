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
from pytrends.request import TrendReq
import pandas as pd
import random

# Configuration
pd.set_option('future.no_silent_downcasting', True)

# Constants
PROXIES = os.environ['PROXY_LIST'].split(',') if 'PROXY_LIST' in os.environ else []
random.shuffle(PROXIES)  # Shuffle proxies for better load distribution
MIN_DELAY_BETWEEN_CALLS = 1.5  # Minimum seconds between API calls
RATE_LIMIT_PAUSE = 60  # Seconds to pause when hitting rate limit

# Initialize pytrends once
pytrends = TrendReq(
    timeout=(3.05, 30),
    retries=3,
    backoff_factor=3.0,
    proxies=PROXIES
)

# Utility Classes
class TimingStats:
    """Track timing statistics for API calls"""
    def __init__(self):
        self.start_time = None
        self.api_calls = []  # List to store duration of each call

    def start(self):
        self.start_time = datetime.now()
        
    def add_api_call(self, duration):
        self.api_calls.append(duration)
        
    def get_total_time(self):
        if self.start_time:
            return datetime.now() - self.start_time
        return timedelta(0)
        
    def get_avg_call_time(self):
        if not self.api_calls:
            return timedelta(0)
        return sum(self.api_calls, timedelta(0)) / len(self.api_calls)

# Global instances
api_calls_counter = 0
timing_stats = TimingStats()

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class ProgressDisplay:
    """Handle progress display and updates"""
    def __init__(self, total, desc="Processing"):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = datetime.now()
        self.last_api_call_time = None
        self.message = ""
        
    def start(self):
        self.start_time = datetime.now()
        print(f"\n{Colors.BLUE}=== {self.desc} ==={Colors.RESET}")
        self._print_progress_bar()
    
    def update(self, current):
        self.current = current
        # Don't print progress bar here - it will be printed after showing group result
    
    def set_api_call_time(self, duration):
        self.last_api_call_time = duration.total_seconds()
    
    def set_message(self, message, status="warning"):
        """Set a warning or error message"""
        color = Colors.RED if status == "error" else Colors.YELLOW
        # Only print error messages, not group member warnings
        if status == "error":
            print(f"\n{color}⚠ {message}{Colors.RESET}")
            self._print_progress_bar()
    
    def clear_message(self):
        pass
    
    def _print_progress_bar(self):
        """Print the progress bar"""
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
    
    def show_group_result(self, group_num, players, scores, winners):
        """Display results for a completed group"""
        # Format player scores more compactly
        player_scores = []
        for player in players:
            name = player['player']['name']
            score = scores.get(name, 0)
            if name in winners:
                player_scores.append(f"{Colors.GREEN}★{name}({score}){Colors.RESET}")
            else:
                player_scores.append(f"{name}({score})")
        
        print(f"\nGroup {group_num}: " + " | ".join(player_scores))
        self._print_progress_bar()  # Print progress bar after showing group result
    
    def finish(self):
        print('\n')  # Add extra line for spacing
        elapsed = datetime.now() - self.start_time
        print(f"{Colors.GREEN}✓ Done in {elapsed.total_seconds():.1f}s{Colors.RESET}\n")

# Utility Functions
def log_message(message, color=None):
    """Print a message with optional color"""
    if color:
        print(f"{color}{message}{Colors.RESET}")
    else:
        print(message)

# Tournament Functions
def get_trends_data(players_group, progress=None):
    """Query Google Trends for a group of players"""
    global api_calls_counter, last_api_call
    max_retries = 3
    max_no_data_retries = 2
    
    # Ensure minimum delay between API calls
    if hasattr(get_trends_data, 'last_call'):
        time_since_last = time.time() - get_trends_data.last_call
        if time_since_last < MIN_DELAY_BETWEEN_CALLS:
            time.sleep(MIN_DELAY_BETWEEN_CALLS - time_since_last)
    
    # Use topic IDs for search but keep player names for display
    player_identifiers = {
        f"/m/{player['topic_id']}": player 
        for player in players_group
    }
    search_names = list(player_identifiers.keys())
    
    # For display purposes, create a mapping of topic IDs to player names
    player_names = {
        f"/m/{player['topic_id']}": player['player']['name']
        for player in players_group
    }
    
    if progress and len(players_group) > 0:
        names_list = [p['player']['name'] for p in players_group]
        progress.set_message(f"Group: {' | '.join(names_list)}")
    
    retry_delays = [2, 5, 10]  # Increasing delays between retries
    
    for no_data_attempt in range(max_no_data_retries + 1):
        try:
            call_start = datetime.now()
            
            # Add delay before API call
            time.sleep(MIN_DELAY_BETWEEN_CALLS)
            
            pytrends.build_payload(
                search_names,
                timeframe='now 1-d',
                cat=294,
                geo='',
                gprop=''
            )
            
            api_calls_counter += 1
            get_trends_data.last_call = time.time()  # Update last call time
            
            interest_data = pytrends.interest_over_time()
            
            call_duration = datetime.now() - call_start
            timing_stats.add_api_call(call_duration)
            
            if progress:
                progress.set_api_call_time(call_duration)
            
            if interest_data.empty:
                if no_data_attempt < max_no_data_retries:
                    delay = retry_delays[no_data_attempt]
                    if progress:
                        # Use player names instead of topic IDs in messages
                        names = [player_names[topic_id] for topic_id in search_names]
                        progress.set_message(
                            f"No data received (attempt {no_data_attempt + 1}/{max_no_data_retries + 1}), "
                            f"retrying in {delay}s for: {', '.join(names)}",
                            status="warning"
                        )
                    time.sleep(delay)
                    continue
                else:
                    if progress:
                        names = [player_names[topic_id] for topic_id in search_names]
                        progress.set_message(
                            f"No data after {max_no_data_retries + 1} attempts for: {', '.join(names)}",
                            status="error"
                        )
                    return {player['player']['name']: 0 for player in players_group}
            
            if progress:
                progress.clear_message()
            
            # Map the scores back to original player names
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
            if "429" in str(e):
                if no_data_attempt < max_no_data_retries:
                    # On rate limit, take a longer pause
                    if progress:
                        progress.set_message(
                            f"Rate limit hit, pausing for {RATE_LIMIT_PAUSE}s before retry",
                            status="warning"
                        )
                    time.sleep(RATE_LIMIT_PAUSE)
                    continue
            if no_data_attempt < max_no_data_retries:
                delay = retry_delays[no_data_attempt]
                if progress:
                    # Add specific handling for 429 errors
                    if "429" in str(e):
                        error_msg = f"Too Many Requests (HTTP 429) - Rate limit exceeded, retrying in {delay}s"
                    else:
                        error_msg = f"Error occurred (attempt {no_data_attempt + 1}/{max_no_data_retries + 1}): {str(e)}, retrying in {delay}s"
                    
                    progress.set_message(error_msg, status="warning")
                time.sleep(delay)
                continue
            
            # If all retries fail, add specific message for 429
            if "429" in str(e):
                log_message("\nFailed due to rate limiting (HTTP 429)", Colors.RED)
            else:
                log_message(f"\nAll retries failed for group: {str(e)}", Colors.RED)
            
            log_message(f"Failed players: {', '.join(search_names)}", Colors.RED)
            log_message("Stopping script due to repeated failures", Colors.RED)
            exit(1)

def filter_active_players(players):
    """Filter players who have been active in games"""
    active_players = []
    
    for player in players:
        games = player['statistics'][0]['games']
        # Check if player has any appearances or has been on the bench
        if (games['appearences'] is not None and games['appearences'] > 0) or \
           (player['statistics'][0]['substitutes']['bench'] is not None and 
            player['statistics'][0]['substitutes']['bench'] > 0):
            active_players.append(player)
    
    return active_players

def create_progress_bar(current, total, width=50):
    """Create a progress bar string"""
    filled = int(width * current / total)
    bar = '=' * filled + '-' * (width - filled)
    percent = int(100 * current / total)
    return f"[{bar}] {percent}% ({current}/{total})"

def run_tournament_round(players, players_to_keep=2, round_num=1):
    """Run one round of the tournament"""
    results = []
    total_groups = (len(players) + 4) // 5
    
    progress = ProgressDisplay(total_groups, desc=f"Round {round_num}")
    progress.start()
    
    for i in range(0, len(players), 5):
        group = players[i:min(i+5, len(players))]
        if len(group) < 2:
            results.extend(group)
            continue
        
        scores = get_trends_data(group, progress)
        sorted_group = sorted(group, key=lambda p: scores.get(p['player']['name'], 0), reverse=True)
        winners = [p['player']['name'] for p in sorted_group[:players_to_keep]]
        
        # Show group results
        group_num = (i + 5) // 5
        progress.show_group_result(group_num, group, scores, winners)
        
        results.extend(sorted_group[:players_to_keep])
        progress.update(group_num)
    
    progress.finish()
    
    # Before returning results, deduplicate players by name, keeping highest score
    seen_players = {}
    deduplicated_results = []
    
    for player in results:
        name = player['player']['name']
        if name not in seen_players:
            seen_players[name] = player
        else:
            # If we've seen this player before, keep the one with the higher score
            existing_score = scores.get(seen_players[name]['player']['name'], 0)
            new_score = scores.get(name, 0)
            if new_score > existing_score:
                seen_players[name] = player
    
    return list(seen_players.values())

def run_final_round(players):
    """Run final round as a knockout system"""
    log_message("\n=== Final Round ===", Colors.GREEN)
    log_message(f"Starting final round with {len(players)} players", Colors.BLUE)
    
    # Initialize with first 5 players
    current_group = players[:5]
    challengers = players[5:]
    final_scores = {}
    best_fifth = None
    best_fifth_score = -1
    
    # Get initial scores
    scores = get_trends_data(current_group)
    final_scores.update(scores)
    
    # Sort initial group
    current_group.sort(key=lambda p: scores.get(p['player']['name'], 0), reverse=True)
    
    # Initialize best_fifth with 5th place from initial group
    best_fifth = current_group[4]
    best_fifth_score = scores[best_fifth['player']['name']]
    
    # Show initial group
    log_message("\nInitial Top 5:", Colors.BLUE)
    for i, player in enumerate(current_group, 1):
        name = player['player']['name']
        score = scores[name]
        team = player['statistics'][0]['team']['name']
        log_message(f"{i}. {name:<20} {score:>3} ({team})", Colors.BLUE)
    
    # Process remaining challengers
    progress = ProgressDisplay(len(challengers), desc="Processing challengers")
    progress.start()
    
    for i, challenger in enumerate(challengers):
        # Keep top 4 from previous round and add challenger
        comparison_group = current_group[:4] + [challenger]
        scores = get_trends_data(comparison_group)
        
        # Sort based on this comparison
        comparison_group.sort(key=lambda p: scores.get(p['player']['name'], 0), reverse=True)
        
        # Check if the 5th place (loser) of this round is better than our current best 5th
        current_fifth = comparison_group[4]
        current_fifth_score = scores[current_fifth['player']['name']]
        
        if current_fifth_score > best_fifth_score:
            best_fifth = current_fifth
            best_fifth_score = current_fifth_score
        
        # Update current group with top 4 from this comparison
        current_group = comparison_group[:4]
        
        # Show current standings after each comparison
        progress.show_group_result(i+1, comparison_group, scores, 
                                 [p['player']['name'] for p in comparison_group[:4]])
        progress.update(i+1)
    
    progress.finish()
    
    # Final comparison of top 4 plus best 5th place
    final_group = current_group[:4] + [best_fifth]
    final_scores = get_trends_data(final_group)
    final_group.sort(key=lambda p: final_scores.get(p['player']['name'], 0), reverse=True)
    
    # Now get detailed interest over time data for the final top 5
    log_message("\nGetting detailed data for final top 5...", Colors.BLUE)
    try:
        # Use topic IDs for the final 5
        top_5_topics = [f"/m/{player['topic_id']}" for player in final_group[:5]]  # Ensure only top 5
        
        # Debug log
        log_message(f"Fetching interest over time for topics: {top_5_topics}", Colors.BLUE)
        
        pytrends.build_payload(
            top_5_topics,
            timeframe='now 1-d',
            cat=294,
            geo='',
            gprop=''
        )
        
        interest_data = pytrends.interest_over_time()
        
        # Debug log
        log_message(f"Got interest data with columns: {interest_data.columns}", Colors.BLUE)
        
        # Convert to dictionary with player names as keys
        detailed_data = {}
        for player in final_group[:5]:  # Process only top 5
            topic_id = f"/m/{player['topic_id']}"
            player_name = player['player']['name']
            
            if topic_id in interest_data:
                # Debug log
                log_message(f"Processing data for {player_name}", Colors.BLUE)
                
                # Convert numpy values to native Python types
                values = [float(x) for x in interest_data[topic_id].values]
                dates = [d.strftime('%Y-%m-%d %H:%M:%S') for d in interest_data.index]
                
                detailed_data[player_name] = {
                    "values": values,
                    "dates": dates
                }
                
                # Debug log
                log_message(f"Added {len(values)} data points for {player_name}", Colors.BLUE)
        
        # Save results with detailed data
        save_results(final_group[:5], final_scores, interest_data=detailed_data)
        log_message(f"Successfully saved interest over time data for {len(detailed_data)} players", Colors.GREEN)
        
    except Exception as e:
        log_message(f"Warning: Could not fetch detailed data: {str(e)}", Colors.YELLOW)
        log_message(f"Full error: {type(e).__name__}: {str(e)}", Colors.YELLOW)
        # Fall back to saving without detailed data
        save_results(final_group[:5], final_scores)
        return final_group, final_scores
    
    return final_group, final_scores

def fetch_trending_footballers(test_limit=None):
    """Main function to find trending footballers"""
    try:
        global api_calls_counter
        api_calls_counter = 0
        timing_stats.start()  # Start timing
        
        # Load preprocessed players
        with open('public/preprocessed_players.json', 'r') as f:
            active_players = json.load(f)
        
        log_message("\n=== Tournament Start ===", Colors.BLUE)
        log_message(f"Total active players: {len(active_players)}", Colors.BLUE)
        
        if test_limit:
            # In test mode, take first N players without shuffling
            active_players = active_players[:test_limit]
            log_message(f"TEST MODE: Limited to {test_limit} players\n", Colors.YELLOW)
        else:
            # In production mode, shuffle all players
            random.shuffle(active_players)
            log_message("Randomly shuffled players for fair competition\n", Colors.BLUE)

        # Tournament rounds
        current_players = active_players
        round_num = 1
        
        while len(current_players) > 25:
            log_message(f"\n=== Round {round_num} ===", Colors.BLUE)
            log_message(f"Processing {len(current_players)} players in {(len(current_players) + 4) // 5} groups", Colors.BLUE)
            current_players = run_tournament_round(current_players, players_to_keep=2, round_num=round_num)
            round_num += 1

        # Run final round with remaining players
        final_5, final_scores = run_final_round(current_players)
        
        # Don't save here - it's already saved in run_final_round
        # save_results(final_5, final_scores)  # Remove this line
        
        log_message("\n=== Final Results ===", Colors.GREEN)
        log_message("Top 5 Trending Footballers:", Colors.GREEN)
        for i, player in enumerate(final_5, 1):
            name = player['player']['name']
            score = final_scores[name]
            team = player['statistics'][0]['team']['name']
            log_message(f"{i}. {name:<20} {score:>3} ({team})", Colors.GREEN)
        
        # At the end, print timing statistics
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

def save_results(top_5, scores, interest_data=None):
    """Save the final results to JSON"""
    # Debug log at start
    log_message("Starting save_results...", Colors.BLUE)
    if interest_data:
        log_message(f"Interest data available for players: {list(interest_data.keys())}", Colors.BLUE)
    
    # Ensure directory exists
    os.makedirs('public', exist_ok=True)
    
    # Load preprocessed players to get full data
    with open('public/preprocessed_players.json', 'r') as f:
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
        
        # Get full player data from preprocessed JSON
        player_data = player_lookup[player_name]
        
        # Convert any numpy integers to Python integers
        trending_score = float(scores[player_name])  # Convert to float for safety
        
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
            player_entry["interest_over_time"] = {
                "values": interest_data[player_name]["values"],
                "dates": interest_data[player_name]["dates"]
            }
            log_message(f"Added interest data to {player_name} entry with {len(interest_data[player_name]['values'])} points", Colors.BLUE)
        else:
            log_message(f"No interest data available for {player_name}", Colors.YELLOW)
        
        result["players"].append(player_entry)
    
    # Debug log before saving
    log_message(f"Final JSON structure keys: {list(result.keys())}", Colors.BLUE)
    log_message(f"Number of players: {len(result['players'])}", Colors.BLUE)
    for p in result["players"]:
        log_message(f"Player {p['player']['name']} data keys: {list(p.keys())}", Colors.BLUE)
    
    # Save to JSON
    json_path = os.path.join('public', 'trending_footballers.json')
    tmp_json_path = json_path + '.tmp'
    
    try:
        with open(tmp_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        os.replace(tmp_json_path, json_path)
        log_message(f"Successfully saved JSON with {len(result['players'])} players to {json_path}", Colors.GREEN)
        
    except Exception as e:
        if os.path.exists(tmp_json_path):
            os.remove(tmp_json_path)
        raise e

# Initialize the last call time
get_trends_data.last_call = 0

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
