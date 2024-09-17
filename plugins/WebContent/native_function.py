from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

class WebContent:    
    @kernel_function(
        name="fetch_url",
        description="Get text form url.",
    )
    def fetch_url(
        self,
        query: str,
    ) -> Annotated[str, "the output is a string"]:
        """Content from web page to process further."""
        summary = ""
        httpurl = "https://newsroom.accenture.com/news/2024/accenture-invests-in-martian-to-bring-dynamic-routing-of-large-language-queries-and-more-effective-ai-systems-to-clients"
        content = fetch_webpage(httpurl)
        if content:
            summary = extract_and_summarize(content)
            return summary
        else:
            return None
        return summary
    

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