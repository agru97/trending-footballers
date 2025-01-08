from gnews import GNews
import json
import time
from datetime import datetime, timezone
import os
import re
from llama_cpp import Llama  # for direct GGUF usage

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

def generate_trend_summary(news_articles, llm, player_name):
    """Generate a summary using local LLM"""
    if not news_articles:
        return "No recent news available."
    
    # Combine all news content
    news_content = "\n\n".join([
        f"Title: {article['title']}\nDescription: {article['description']}"
        for article in news_articles
    ])
    
    prompt = f"""Recent news about {player_name}:

{news_content}

Write a concise 2-3 sentence summary highlighting the key developments or events involving {player_name}. 
Focus on what's making headlines - whether it's match performances, transfer news, or other significant events.
Be direct and engaging, avoid phrases like 'is trending' or 'is currently trending'.

Summary:"""

    try:
        response = llm(
            prompt,
            max_tokens=150,
            temperature=0.75,  # Slightly increased for more variety
            stop=["</s>", "\n\n"]
        )
        return response['choices'][0]['text'].strip()
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return "Unable to generate summary at this time."

def fetch_news_for_player(player_name, topic_title):
    """Fetch news for a specific player using their name and topic title"""
    gn = GNews(
        period='1d',
        max_results=5,
        exclude_websites=[]
    )
    
    try:
        search_query = f'"{topic_title}" football'
        articles = gn.get_news(search_query)
        
        if not articles:
            search_query = f'"{player_name}" football'
            articles = gn.get_news(search_query)
            
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
    # Initialize LLM
    model_path = './models/Llama-3.2-3B-Instruct-Q4_K_M.gguf'
    
    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,  # Context window
            n_threads=4   # CPU threads to use
        )
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return

    try:
        with open('public/trending_footballers.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("trending_footballers.json not found")
        return
    
    players = data.get('players', [])[:5]
    
    news_data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "player_news": []
    }
    
    for player in players:
        player_info = player.get('player', {})
        player_name = get_preferred_name(player_info)  # Use preferred name
        topic_title = player.get('topic_title')
        
        if not topic_title:
            print(f"Skipping {player_name} - missing topic title")
            continue
            
        print(f"Fetching news for {player_name} (Topic: {topic_title})...")
        
        news_articles = fetch_news_for_player(player_name, topic_title)
        
        # Generate trend summary from news articles
        trend_summary = generate_trend_summary(news_articles, llm, player_name)
        
        player_news = {
            "player_id": player_info.get('id'),
            "player_name": player_name,
            "trending_score": player.get('trending_score'),
            "trend_summary": trend_summary,  # Add the generated summary
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
        time.sleep(2)
    
    output_path = 'public/player_news.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"News data saved to {output_path}")

if __name__ == "__main__":
    main() 