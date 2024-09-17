import os
from openai import AzureOpenAI
from dotenv import dotenv_values
import time
from datetime import timedelta
import json
import streamlit as st
from PIL import Image
import base64
import requests
import io
from io import BytesIO
import autogen
from typing import Optional
from typing_extensions import Annotated
from streamlit import session_state as state
import azure.cognitiveservices.speech as speechsdk
from audiorecorder import audiorecorder
import pyaudio
import wave
import tempfile
import PyPDF2
from docx import Document
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from bs4 import BeautifulSoup
from datetime import datetime
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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
    description += soup.find('div').get_text() if soup.find('div') else 'No description available' 
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


def fetch_and_summarize(url):
    content = fetch_webpage(url)
    if content:
        summary = extract_and_summarize(content)
        return summary
    else:
        return None
    
#driver_path = r"C:\\Users\\babal\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe"
driver_path = r"C:\\Users\\babal\\Downloads\\chromedriver-win64-128\\chromedriver-win64\\chromedriver.exe"
    
def fetch_content(url):
    # Initialize WebDriver
    # Create a Service object with the driver path
    service = Service(driver_path)

    # driver = webdriver.Chrome(executable_path='C:\\Users\\babal\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')
    # Initialize WebDriver using the Service object
    driver = webdriver.Chrome(service=service)

    # Open the page
    #driver.get("https://newsroom.accenture.com/?year=2024")
    driver.get("https://newsroom.accenture.com/news")

    # Wait for the page to be fully loaded
    WebDriverWait(driver, 60).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )
    print("Page is fully loaded!")

    # Wait for the dynamic content to load
    #WebDriverWait(driver, 60).until(
    #    EC.presence_of_element_located((By.CLASS_NAME, "newslist"))
    #)
    # Increase the timeout to 120 seconds to give the page more time to load
    WebDriverWait(driver, 120).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "newslist"))
    )
    # Wait for network activity to cease
    WebDriverWait(driver, 60).until(
        lambda driver: driver.execute_script("return window.performance.getEntriesByType('resource').length > 0")
    )
    print("Network activity has ceased.")

    

    # Get the page's HTML after JavaScript has loaded the dynamic content
    html = driver.page_source

    # Pass the HTML to BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Parse the specific div with dynamic content
    div_content = soup.find("div", class_="newslist")
    # div_content = soup.find("div")
    print(div_content.text)

    # Close the browser
    driver.quit()
        
if __name__ == '__main__':
    url = 'https://newsroom.accenture.com/?year=2024'
    #summary = fetch_and_summarize(url)
    summary = fetch_content(url)
    print(summary)
    if summary:
        print(summary['Body'])
    else:
        print('Failed to fetch and summarize the webpage')