import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

# Function to convert Unix timestamp to readable date
def convert_unix_to_date(timestamp):
    return datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')



# Function to fetch and parse the webpage
def fetch_webpage(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve page. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching the webpage: {e}")
        return None
    
# Function to extract content by sections and summarize
def extract_and_summarize(content):
    soup = BeautifulSoup(content, 'html.parser')
    summary = defaultdict(str)
    
    # Extract main title and description
    title = soup.find('h1').get_text() if soup.find('h1') else 'No Title'
    # description = soup.find('meta', attrs={'name': 'description'})
    description = soup.find('p').get_text() if soup.find('p') else 'No description available'
    #description += soup.find('div').get_text() if soup.find('div') else 'No description available' 
    # Step 3: Find the 'div' element with a specific class name
    class_name = "newslist"  # Replace with the actual class name
    div_content = soup.find_all('div', class_=class_name)
    for div in div_content:
        print(div.get_text(strip=True)) 
        description += div.get_text(strip=True)
    # description = description['content'] if description else 'No description available'
    summary['Title'] = title
    summary['Description'] = description
    #print('description:', description)
    
    # Extract and summarize main body content
    body_text = []
    for p in soup.find_all('p'):
        body_text.append(p.get_text())
    
    # Basic summarization by splitting the text into sections/topics
    summary['Body'] = ' '.join(body_text[:5]) + '...'

    return summary

# Function to process each article and extract information
def process_articles(data):
    articles = data.get('data', [])
    
    for article in articles:
        path = article.get('path')
        title = article.get('title')
        description = article.get('description')
        industries = article.get('industries')
        subjects = article.get('subjects')
        last_modified = convert_unix_to_date(article.get('lastModified'))
        published_date = convert_unix_to_date(article.get('publisheddateinseconds'))
        long_description = article.get('longdescriptionextracted')
        
        print(f"Title: {title}")
        print(f"Path: {path}")
        print(f"Description: {description}")
        print(f"Industries: {industries}")
        print(f"Subjects: {subjects}")
        print(f"Last Modified: {last_modified}")
        print(f"Published Date: {published_date}")
        print(f"Long Description (first 200 chars): {long_description[:200]}")
        print("="*80)
        httpurl = "https://newsroom.accenture.com/" + path
        content = fetch_webpage(httpurl)
        if content:
            summary = extract_and_summarize(content)
            print("Summary:")
            print(summary['Body'])
            print("="*80)
        print()

def get_data():
    # URL of the JSON data
    url = "https://newsroom.accenture.com/query-index.json?sheet=homepage&limit=10&offset=0&ts=28776829"

    # Fetch the data from the URL
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON content
        data = response.json()
        
        # Pretty-printing the JSON content
        # print(json.dumps(data, indent=4))
        
        # Process the data (example: extract titles and descriptions)
        #articles = data.get('data', [])
        
        #for article in articles:
        #    title = article.get('title', 'No title')
        #    description = article.get('description', 'No description')
        #    print(f"Title: {title}")
        #    print(f"Description: {description}")
        #    print("="*80)
        process_articles(data)
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

if __name__ == "__main__":
    get_data()