from gnews import GNews
import json
import time
from datetime import datetime, timezone
import os
import re
import google.generativeai as genai

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
MODEL = genai.GenerativeModel('gemini-pro')

def clean_title(title):
    """Remove source names and clean up the title"""
    # Remove everything after ' - ' or ' | ' if present
    title = re.split(' [-|] ', title)[0]
    return title.strip()

def clean_description(desc):
    """Clean up and expand the description"""
    if not desc:
        return ""
    desc = re.split(' [-|] ', desc)[0]
    desc = re.sub(r'http\S+', '', desc)
    return desc.strip()

def generate_trend_summary(news_articles, player_name, topic_title):
    """Generate a summary using Google Gemini"""
    print(f"\nGenerating summary for {topic_title}...")
    start_time = time.time()
    
    if not news_articles:
        print("No news articles found, returning default message")
        return "No recent news available."
    
    print(f"Found {len(news_articles)} articles to summarize")
    
    print("Preparing content...")
    news_content = "\n\n".join([
        f"Title: {article['title']}\nDescription: {article['description']}"
        for article in news_articles
    ])
    
    prompt = f"""Recent news about {topic_title}:

{news_content}

As an elite sports journalist, write a gripping 2-3 sentence summary that captures {topic_title}'s latest headlines.
IMPORTANT: Only include facts that are explicitly mentioned in the provided news articles.
Focus on the most newsworthy elements, such as:
- Match performances or key moments (be specific about competitions)
- Transfer rumors and contract talks
- Injuries or fitness updates
- Off-field developments or controversies
- Career milestones or achievements

Use powerful, journalistic language that draws readers in, but maintain strict factual accuracy.
Double-check all competition names, scores, and events against the source articles.

Summary:"""
    
    print("Calling Gemini API for summary...")
    api_start = time.time()
    
    try:
        response = MODEL.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=150,
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            )
        )
        if not response.candidates or response.candidates[0].finish_reason == "SAFETY":
            print(f"Content filtered by safety system for {player_name}")
            return f"Recent news available for {player_name}. Please check sports news websites for the latest updates."
            
        api_duration = time.time() - api_start
        print(f"API call took {api_duration:.2f} seconds")
        return response.text
        
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return "Unable to generate summary at this time."

def fetch_news_for_player(player_name, topic_title):
    """Fetch news for a specific player using their name and topic title"""
    print(f"\nFetching news for {player_name}...")
    start_time = time.time()
    
    print(f"Using topic title: {topic_title}")
    
    gn = GNews(
        period='1d',
        max_results=5,
        exclude_websites=[]
    )
    
    try:
        search_query = f'"{topic_title}" football'
        print(f"Searching with query: {search_query}")
        search_start = time.time()
        articles = gn.get_news(search_query)
        search_duration = time.time() - search_start
        print(f"Search took {search_duration:.2f} seconds")
        
        if not articles:
            print("No articles found with topic title, trying player name...")
            search_query = f'"{player_name}" football'
            print(f"New search query: {search_query}")
            search_start = time.time()
            articles = gn.get_news(search_query)
            search_duration = time.time() - search_start
            print(f"Second search took {search_duration:.2f} seconds")
            
        found_count = len(articles[:5]) if articles else 0
        print(f"Found {found_count} articles")
        
        total_duration = time.time() - start_time
        print(f"Total news fetch took {total_duration:.2f} seconds")
        
        return articles[:5] if articles else []
    except Exception as e:
        print(f"Error fetching news for {player_name}: {str(e)}")
        return []

def get_preferred_name(player_info):
    """Get the commonly used name for a player"""
    # If player_info is already a string, return it
    if isinstance(player_info, str):
        return player_info
        
    # Otherwise try to get components
    firstname = player_info.get('firstname', '')
    lastname = player_info.get('lastname', '')
    
    # Try to get common name if available
    name = player_info.get('name', {})
    if isinstance(name, dict):
        common_name = name.get('display', '')
        if common_name:
            return common_name
    
    # Fallback to first + last name
    return f"{firstname} {lastname}".strip()

def main():
    print("\nStarting news update process...")
    try:
        with open('public/trending_footballers.json', 'r') as f:
            data = json.load(f)
            print("Successfully loaded trending_footballers.json")
    except FileNotFoundError:
        print("ERROR: trending_footballers.json not found")
        return
    
    players = data.get('players', [])[:5]
    print(f"Processing top {len(players)} players")
    
    news_data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "player_news": []
    }
    
    for idx, player in enumerate(players, 1):
        print(f"\nProcessing player {idx} of {len(players)}...")
        player_info = player.get('player', {})
        player_name = get_preferred_name(player_info)
        topic_title = player.get('topic_title')
        
        if not topic_title:
            print(f"WARNING: Skipping {player_name} - missing topic title")
            continue
        
        news_articles = fetch_news_for_player(player_name, topic_title)
        trend_summary = generate_trend_summary(news_articles, player_name, topic_title)
        
        print(f"Adding news data for {player_name}")
        player_news = {
            "player_id": player_info.get('id'),
            "player_name": player_name,
            "trending_score": player.get('trending_score'),
            "trend_summary": trend_summary,
            "news": []
        }
        
        for article in news_articles:
            news_item = {
                "title": clean_title(article.get('title', '')),
                "description": clean_description(article.get('description', '')),
                "date": article.get('published date'),
            }
            player_news["news"].append(news_item)
        
        news_data["player_news"].append(player_news)
        print(f"Completed processing for {player_name}")
        time.sleep(2)
    
    output_path = 'public/player_news.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nProcess complete! News data saved to {output_path}")

if __name__ == "__main__":
    main() 