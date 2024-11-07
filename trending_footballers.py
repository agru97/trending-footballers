import requests
import os
import google.generativeai as genai
from dotenv import load_dotenv
import datetime

# Load environment variables from .env file
load_dotenv()


# Get API keys from environment variables
serpapi_key = os.environ.get('SERPAPI_KEY')
gemini_api_key = os.environ.get('GEMINI_API_KEY')

if not serpapi_key or not gemini_api_key:
    raise Exception("Missing required API keys in environment variables")

def fetch_trending_footballers():
    # Fetch data from SerpApi
    serpapi_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": "footballer",
        "hl": "en",
        "data_type": "RELATED_TOPICS",
        "date": "now 1-d",
        "api_key": serpapi_key
    }

    response = requests.get(serpapi_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data from SerpApi: {response.text}")

    data = response.json()
    rising_topics = data.get('related_topics', {}).get('rising', [])
    
    if not rising_topics:
        raise Exception("No rising topics found.")

    # Prepare the list of entries
    entries = []
    for item in rising_topics:
        topic_title = item['topic']['title']
        extracted_value = item.get('extracted_value', '0')
        entries.append(f"{topic_title}: {extracted_value}")

    entries_text = "; ".join(entries)
    
    # Prepare the prompt for Gemini
    prompt = f"""
   Please analyze the following list of entries separated by semicolons (;). Each entry consists of two parts separated by a colon (:):

- The first part is a term from Google Trends related to footballers.
- The second part is a numerical value indicating search interest.

Here is the list:
{entries_text}

**Tasks:**

1. **Identify Entries**: From the list, identify entries where the first part is the name of an **active professional football (soccer) player**.

2. **Handle Duplicates**: If a player's name appears multiple times, **only count them once**, using the **highest numerical value** associated with them.

3. **Rank Players**: From these entries, select the **top 5 players** based on the highest numerical values.

4. **Output Format**:
   - Provide **only** the data in **CSV format** with **no headers**, **no explanations**, and **no additional text**.
   - Each line should contain the player's **full name** and their **score**, separated by a comma.
   - **Provide exactly 5 entries**—**no more, no less**.

**Example Output:**
Player Name 1,Score 1
Player Name 2,Score 2
Player Name 3,Score 3
Player Name 4,Score 4
Player Name 5,Score 5

**Important**: Do not include any explanations, headings, numbering, or extra text. Provide **only** the CSV data as specified, and **only the top 5 players**.
    """

    # Get response from Gemini
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(prompt)
    
    # Create public directory if it doesn't exist
    os.makedirs('public', exist_ok=True)
    
    # Write the response and timestamp to separate files
    csv_path = os.path.join('public', 'trending_footballers.csv')
    timestamp_path = os.path.join('public', 'last_update.txt')
    
    with open(csv_path, 'w', newline='') as f:
        f.write(response.text.strip())
    
    # Save current timestamp
    current_time = datetime.datetime.utcnow()
    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    print(f"Writing timestamp to: {timestamp_path}")  # Debug log
    print(f"Timestamp content: {formatted_time}")     # Debug log
    
    with open(timestamp_path, 'w') as f:
        f.write(formatted_time)

if __name__ == "__main__":
    try:
        fetch_trending_footballers()
        print("Successfully updated trending footballers data")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)