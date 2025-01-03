import os
import json
import time
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import pandas as pd
import itertools
import threading
import sys
import random

# Configure pandas
pd.set_option('future.no_silent_downcasting', True)

# Globals
api_calls_counter = 0
PROXIES = os.environ['PROXY_LIST'].split(',') if 'PROXY_LIST' in os.environ else []

# Add timing stats
class TimingStats:
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

# Add to globals
timing_stats = TimingStats()

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_message(message, color=None):
    """Print a message with optional color"""
    if color:
        print(f"{color}{message}{Colors.RESET}")
    else:
        print(message)

def get_trends_data(players_group, progress=None):
    """Query Google Trends for a group of players and return their maximum scores"""
    global api_calls_counter
    max_retries = 3
    max_no_data_retries = 2
    
    # Create unique identifiers for players with same names
    player_identifiers = {}
    name_counts = {}
    duplicate_names = []
    
    for player in players_group:
        name = player['player']['name']
        if name in name_counts:
            name_counts[name] += 1
            # Track duplicates for warning message
            if name_counts[name] == 2:  # Only add to list first time we find duplicate
                duplicate_names.append(name)
            # Create unique name by adding team
            unique_name = f"{name} ({player['statistics'][0]['team']['name']})"
            player_identifiers[unique_name] = player
        else:
            name_counts[name] = 1
            player_identifiers[name] = player
    
    search_names = list(player_identifiers.keys())
    
    if progress and duplicate_names:
        progress.set_message(
            f"Found duplicate names: {', '.join(duplicate_names)} - using team names to differentiate",
            status="warning"
        )
    
    retry_delays = [2, 5, 10]  # Increasing delays between retries
    
    for no_data_attempt in range(max_no_data_retries + 1):
        try:
            call_start = datetime.now()
            pytrends = TrendReq(
                timeout=(3.05, 27),
                retries=max_retries,
                backoff_factor=2.0,
                proxies=PROXIES
            )
            
            pytrends.build_payload(
                search_names,
                timeframe='now 1-d',
                cat=294,
                geo='',
                gprop=''
            )
            
            api_calls_counter += 1
            interest_data = pytrends.interest_over_time()
            
            call_duration = datetime.now() - call_start
            timing_stats.add_api_call(call_duration)
            
            if progress:
                progress.set_api_call_time(call_duration)
            
            if interest_data.empty:
                if no_data_attempt < max_no_data_retries:
                    delay = retry_delays[no_data_attempt]
                    if progress:
                        progress.set_message(
                            f"No data received (attempt {no_data_attempt + 1}/{max_no_data_retries + 1}), "
                            f"retrying in {delay}s for: {', '.join(search_names)}",
                            status="warning"
                        )
                    time.sleep(delay)
                    continue
                else:
                    if progress:
                        progress.set_message(
                            f"No data after {max_no_data_retries + 1} attempts for: {', '.join(search_names)}",
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

class ProgressDisplay:
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
        self._print_progress_bar()
    
    def set_api_call_time(self, duration):
        self.last_api_call_time = duration.total_seconds()
    
    def set_message(self, message, status="warning"):
        """Set a warning or error message"""
        color = Colors.RED if status == "error" else Colors.YELLOW
        # Move to new line, print message, and restore progress bar
        print(f"\n{color}⚠ {message}{Colors.RESET}")
        self._print_progress_bar()
    
    def clear_message(self):
        pass
    
    def _print_progress_bar(self):
        """Print the progress bar"""
        elapsed = datetime.now() - self.start_time
        progress = int(50 * self.current / self.total)
        # Only color the completed portion green
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
        print('\n')  # Add extra line for spacing
        
        # Format player scores more compactly
        player_scores = []
        for player in players:
            name = player['player']['name']
            score = scores.get(name, 0)
            if name in winners:
                player_scores.append(f"{Colors.GREEN}★{name}({score}){Colors.RESET}")
            else:
                player_scores.append(f"{name}({score})")
        
        print(f"{Colors.BLUE}Group {group_num}:{Colors.RESET} " + " | ".join(player_scores))
        self._print_progress_bar()
    
    def finish(self):
        print('\n')  # Add extra line for spacing
        elapsed = datetime.now() - self.start_time
        print(f"{Colors.GREEN}✓ Done in {elapsed.total_seconds():.1f}s{Colors.RESET}\n")

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
    """
    Run final round as a knockout system:
    - Start with top 5
    - For each challenger:
      - Compare with current top 4
      - Keep best 4
      - Track best 5th place
    - Continue until all challengers are processed
    """
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
    
    # Return top 5
    return final_group, final_scores

def fetch_trending_footballers(test_limit=None):
    try:
        global api_calls_counter
        api_calls_counter = 0
        timing_stats.start()  # Start timing
        
        # Load and filter players
        with open('public/players.json', 'r') as f:
            all_players = json.load(f)
        
        active_players = filter_active_players(all_players)
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
        
        # Save results
        save_results(final_5, final_scores)
        
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

def save_results(top_5, scores):
    """Save the final top 5 results to CSV"""
    # Ensure directory exists
    os.makedirs('public', exist_ok=True)
    
    # Save to CSV
    csv_path = os.path.join('public', 'trending_footballers.csv')
    tmp_csv_path = csv_path + '.tmp'
    
    try:
        with open(tmp_csv_path, 'w', newline='') as f:
            # Write header
            f.write("name,trend_score,full_name,nationality,club,club_logo,player_photo\n")
            
            # Sort players by score
            sorted_players = sorted(top_5, key=lambda p: scores[p['player']['name']], reverse=True)
            
            # Write data
            for player in sorted_players:
                fields = [
                    player['player']['name'],
                    str(scores[player['player']['name']]),
                    f"{player['player']['firstname']} {player['player']['lastname']}",
                    player['player']['nationality'],
                    player['statistics'][0]['team']['name'],
                    player['statistics'][0]['team']['logo'],
                    player['player']['photo']
                ]
                f.write(','.join(f'"{field}"' for field in fields) + '\n')
        
        # Atomic rename
        os.replace(tmp_csv_path, csv_path)
        
    except Exception as e:
        if os.path.exists(tmp_csv_path):
            os.remove(tmp_csv_path)
        raise e
    
    # Save timestamp
    with open('public/last_update.txt', 'w') as f:
        f.write(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

if __name__ == "__main__":
    try:
        fetch_trending_footballers(20)
        log_message("Successfully updated top 5 footballers data", Colors.GREEN)
    except Exception as e:
        log_message(f"Error occurred: {str(e)}", Colors.RED)
        log_message(f"Error type: {type(e).__name__}", Colors.RED)
        import traceback
        log_message(f"Stack trace:\n{traceback.format_exc()}", Colors.RED)
        exit(1)