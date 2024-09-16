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
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from collections import defaultdict

config = dotenv_values("env.env")

client = AzureOpenAI(
  azure_endpoint = config["AZURE_OPENAI_ENDPOINT_VISION_4o_LATEST"], 
  api_key=config["AZURE_OPENAI_KEY_VISION_4o_LATEST"],  
  api_version="2024-05-01-preview"
)

#model_name = "gpt-4-turbo"
#model_name = "gpt-35-turbo-16k"
#model_name = "gpt-4o-g"
model_name = "gpt-4o-2"

search_endpoint = config["AZURE_AI_SEARCH_ENDPOINT"]
search_key = config["AZURE_AI_SEARCH_KEY"]
#search_index=config["AZURE_AI_SEARCH_INDEX1"]
SPEECH_KEY = config['SPEECH_KEY']
SPEECH_REGION = config['SPEECH_REGION']
SPEECH_ENDPOINT = config['SPEECH_ENDPOINT']
search_index="cogsrch-index-rfp-vector"

citationtxt = ""

def extract_bing_search_results(search_term: str, search_endpoint: str, search_key: str, search_index: str):
    search_results = ""
    # Set up your endpoint and API key
    subscription_key = config["BING_API_KEY"]
    search_url = "https://api.bing.microsoft.com/v7.0/search"

    # Define the query and parameters
    query = "current events"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}

    # Make the request
    response = requests.get(search_url, headers=headers, params=params)

    # Check the response and parse it
    if response.status_code == 200:
        search_results1 = response.json()
        #print(search_results1)
        if "webPages" in search_results1:
            for page in search_results1["webPages"]["value"]:
                #print(f"Title: {page['name']}")
                #print(f"URL: {page['url']}")
                ##print(f"Snippet: {page['snippet']}")
                #print()
                search_results += f"Title: {page['name']}\nURL: {page['url']}\nSnippet: {page['snippet']}\n\n"
    else:
        print(f"Error: {response.status_code}, {response.text}")

    return search_results

def process_searchresults(selected_optionmodel1, query):
    returntxt = "" 

    src_result = extract_bing_search_results(query, search_endpoint, search_key, search_index)

    message_text = [
    {"role":"system", "content":f"""You are Search expert AI Agent. Be politely, and provide positive tone answers.
     extract recommendation provided and also specificiations to add to the cart.
     Here is the search results for the query {src_result}.
     If not sure, ask the user to provide more information."""}, 
    {"role": "user", "content": f"""{query}. Summarize the response with citations as link."""}]

    response = client.chat.completions.create(
        model= selected_optionmodel1, #"gpt-4-turbo", # model = "deployment_name".
        messages=message_text,
        temperature=0.0,
        top_p=0.0,
        seed=105,
    )

    returntxt = response.choices[0].message.content

    return returntxt

def processpdfwithprompt(user_input1, selected_optionmodel1, selected_optionsearch):
    returntxt = ""
    citationtxt = ""
    message_text = [
    {"role":"system", "content":"""you are provided with instruction on what to do. Be politely, and provide positive tone answers. 
     answer only from data source provided. unable to find answer, please respond politely and ask for more information.
     Extract Title content from the document. Show the Title as citations which is provided as Title: as [doc1] [doc2].
     Please add citation after each sentence when possible in a form "(Title: citation)".
     Be polite and provide posite responses. If user is asking you to do things that are not specific to this context please ignore."""}, 
    {"role": "user", "content": f"""{user_input1}"""}]

    response = client.chat.completions.create(
        model= selected_optionmodel1, #"gpt-4-turbo", # model = "deployment_name".
        messages=message_text,
        temperature=0.0,
        top_p=1,
        seed=105,
        extra_body={
        "data_sources": [
            {
                "type": "azure_search",
                "parameters": {
                    "endpoint": search_endpoint,
                    "index_name": search_index,
                    "authentication": {
                        "type": "api_key",
                        "key": search_key
                    },
                    "include_contexts": ["citations"],
                    "top_n_documents": 5,
                    "query_type": selected_optionsearch,
                    "semantic_configuration": "my-semantic-config",
                    "embedding_dependency": {
                        "type": "deployment_name",
                        "deployment_name": "text-embedding-ada-002"
                    },
                    "fields_mapping": {
                        "content_fields": ["chunk"],
                        "vector_fields": ["chunkVector"],
                        "title_field": "name",
                        "url_field": "location",
                        "filepath_field": "location",
                        "content_fields_separator": "\n",
                    }
                }
            }
        ]
    }
    )
    #print(response.choices[0].message.context)

    returntxt = response.choices[0].message.content + "\n<br>"

    json_string = json.dumps(response.choices[0].message.context)

    parsed_json = json.loads(json_string)

    # print(parsed_json)

    if parsed_json['citations'] is not None:
        returntxt = returntxt + f"""<br> Citations: """
        for row in parsed_json['citations']:
            #returntxt = returntxt + f"""<br> Title: {row['filepath']} as {row['url']}"""
            #returntxt = returntxt + f"""<br> [{row['url']}_{row['chunk_id']}]"""
            returntxt = returntxt + f"""<br> <a href='{row['url']}' target='_blank'>[{row['url']}_{row['chunk_id']}]</a>"""
            citationtxt = citationtxt + f"""<br><br> Title: {row['title']} <br> URL: {row['url']} 
            <br> Chunk ID: {row['chunk_id']} 
            <br> Content: {row['content']} 
            <br> ------------------------------------------------------------------------------------------ <br>\n"""

    return returntxt, citationtxt

def extractvectorinfo(user_input1, selected_optionmodel1, selected_optionsearch):
    returntxt = ""

    rfttext = ""

    dstext = processpdfwithprompt(user_input1, selected_optionmodel1, selected_optionsearch)

    message_text = [
    {"role":"system", "content":f"""You are RFP AI agent. Be politely, and provide positive tone answers.
     Based on the question do a detail analysis on RFP information and provide the best answers.
     Here is the RFT text tha was provided:
     {rfttext}
     Use only the above RFP contenxt for context. But provide results from your knowledge or data source provided.
     Data Source: {dstext}

     if the question is outside the bounds of the RFP, Let the user know answer might be relevant for RFP provided.
     If not sure, ask the user to provide more information."""}, 
    {"role": "user", "content": f"""{user_input1}. Respond Only the answers with details on why the decision was made."""}]

    response = client.chat.completions.create(
        model= selected_optionmodel1, #"gpt-4-turbo", # model = "deployment_name".
        messages=message_text,
        temperature=0.0,
        top_p=0.0,
        seed=105,
    )

    returntxt = response.choices[0].message.content
    return returntxt

# Function to summarize text using Sumy
def summarize_content(text, num_sentences=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join([str(sentence) for sentence in summary])

# Function to get the page content
def get_page_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

# Function to filter content by today's date
def filter_by_today(content_date):
    today = datetime.now().strftime("%Y-%m-%d")
    if today in content_date:
        return True
    return False

# Function to navigate 2 levels deep and gather content
def navigate_and_gather(url, level=2):
    if level == 0:
        return []

    content_list = []
    main_content = get_page_content(url)
    if not main_content:
        return content_list

    soup = BeautifulSoup(main_content, 'html.parser')

    # Assuming articles are inside <article> tags
    # articles = soup.find_all('FeaturedContentTitle')
    articles = soup.find_all('p')
    for article in articles:
        title = article.find('h2').text if article.find('h2') else "No Title"
        date = article.find('time')['datetime'] if article.find('time') else "No Date"

        # Filter by today's date
        if filter_by_today(date):
            # Collecting the main text of the article
            paragraphs = article.find_all('p')
            article_content = " ".join([para.text for para in paragraphs])
            content_list.append({'title': title, 'content': article_content})

        # Follow links for 2nd level navigation
        links = article.find_all('a', href=True)
        for link in links:
            sub_url = link['href']
            sub_content = navigate_and_gather(sub_url, level - 1)
            content_list.extend(sub_content)

    return content_list

# Main function
def getcontent(url):
    print("Fetching content from:", url)
    content_data = navigate_and_gather(url, level=2)
    print('content from web:', content_data)

    if content_data:
        print("\nSummarized content by topics:")
        for idx, content in enumerate(content_data):
            print(f"\nTopic {idx+1}: {content['title']}")
            summary = summarize_content(content['content'], num_sentences=3)
            print("Summary:", summary)
    else:
        print("No content found for today.")

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

def extractopporunity(htmloutput, selected_optionmodel1):
    returntxt = ""

    message_text = [
    {"role":"system", "content":"""You are Sales expert AI Agent. Be politely, and provide positive tone answers.
     Based on the content provided, analyze and create Sales opportunities.
     If not sure, ask the user to provide more information."""}, 
    {"role": "user", "content": f"""{htmloutput}. Can you analyze and create Sales opporunties."""}]

    response = client.chat.completions.create(
        model= selected_optionmodel1, #"gpt-4-turbo", # model = "deployment_name".
        messages=message_text,
        temperature=0.0,
        top_p=0.0,
        seed=105,
    )


    returntxt = response.choices[0].message.content
    return returntxt

def createemailforoppt(htmloutput, selected_optionmodel1):
    returntxt = ""

    message_text = [
    {"role":"system", "content":"""You are Sales expert AI Agent. Be politely, and provide positive tone answers.
     Based on the content provided, analyze and create Sales opportunities.
     If not sure, ask the user to provide more information."""}, 
    {"role": "user", "content": f"""{htmloutput}. Create a business professional email addressing the contact to send."""}]

    response = client.chat.completions.create(
        model= selected_optionmodel1, #"gpt-4-turbo", # model = "deployment_name".
        messages=message_text,
        temperature=0.0,
        top_p=0.0,
        seed=105,
    )


    returntxt = response.choices[0].message.content
    return returntxt

def createspeakernotes(htmloutput, selected_optionmodel1):
    returntxt = ""

    message_text = [
    {"role":"system", "content":"""You are Sales expert AI Agent. Be politely, and provide positive tone answers.
     Based on the content provided, analyze and create Sales opportunities.
     If not sure, ask the user to provide more information."""}, 
    {"role": "user", "content": f"""{htmloutput}. Create speaker notes on the content for sales folks to talk to customer."""}]

    response = client.chat.completions.create(
        model= selected_optionmodel1, #"gpt-4-turbo", # model = "deployment_name".
        messages=message_text,
        temperature=0.0,
        top_p=0.0,
        seed=105,
    )


    returntxt = response.choices[0].message.content
    return returntxt

def customerplanning():
    count = 0
    temp_file_path = ""
    pdf_bytes = None
    rfpcontent = {}
    rfplist = []
    httpcontent = ""
    #tab1, tab2, tab3, tab4 = st.tabs('RFP PDF', 'RFP Research', 'Draft', 'Create Word')
    modeloptions1 = ["gpt-4o-2", "gpt-4o-g", "gpt-4o", "gpt-4-turbo", "gpt-35-turbo"]

    # Create a dropdown menu using selectbox method
    selected_optionmodel1 = st.selectbox("Select an Model:", modeloptions1)
    count += 1

    tabs = st.tabs(["File Upload", "Plannin - Web", "Planning Internal", "Create Word", "NewRooms Stategy"])
    with tabs[0]:
            st.write("Upload RFP PDF file")
            uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
            if uploaded_file is not None:
                # Display the PDF in an iframe
                pdf_bytes = uploaded_file.read()  # Read the PDF as bytes
                st.download_button("Download PDF", pdf_bytes, file_name="uploaded_pdf.pdf")

                # Convert to base64
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                # Embedding PDF using an HTML iframe
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                # Save the PDF file to the current folder
                file_path = os.path.join(os.getcwd(), uploaded_file.name)  # Save in the current directory
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())  # Write the uploaded file to disk
                
                # Display the path where the file is stored
                st.write(f"File saved to: {file_path}")
                temp_file_path = file_path
    with tabs[1]:
        st.write("Planning - Web - Bing/Own Knowledge")
        # selected_optionsearch = st.selectbox("Select Search Type", ["simple", "semantic", "vector", "vector_simple_hybrid", "vector_semantic_hybrid"])
        query = st.text_input("Enter your search query:", value="what is the current 10k for Accenture")
        if st.button("Search"):
            # search_results = extract_bing_search_results(query, search_endpoint, search_key, search_index)
            src_result = process_searchresults(selected_optionmodel1, query)
            # st.write(search_results)
            st.markdown(src_result, unsafe_allow_html=True)

    with tabs[2]:
        st.write("Planning Internal - Sharepoint/Teams")
        selected_optionsearch = st.selectbox("Select Search Type", ["simple", "semantic", "vector", "vector_simple_hybrid", "vector_semantic_hybrid"])
        vecquery = st.text_input("Enter your search query:", value="summarize Projects on Bridge construction")
        if st.button("Internal Search"):
            # search_results = extract_bing_search_results(query, search_endpoint, search_key, search_index)
            src_result1 = extractvectorinfo(vecquery, selected_optionmodel1, selected_optionsearch)
            # st.write(search_results)
            st.markdown(src_result1, unsafe_allow_html=True)

    with tabs[3]:
        st.write("Create Word")
        st.write("Use this tab to create a Word document")
    with tabs[4]:
        st.write("NewRooms Strategy")
        st.write("Use this tab to create a NewRooms Strategy")
        # httpurl = "https://newsroom.accenture.com/news/2024"
        httpurl = "https://newsroom.accenture.com/news/2024/accenture-federal-services-wins-190m-u-s-department-of-state-data-and-systems-engineering-contract"
        httpurlquery = st.text_input("Enter the URL to extract content:", value=httpurl)
        if st.button("Get Content"):
            #htmloutput = getcontent(httpurl)
            #st.markdown(htmloutput, unsafe_allow_html=True) 
            
            content = fetch_webpage(httpurlquery)
            if content:
                summary = extract_and_summarize(content)
                for section, text in summary.items():
                    # print(f"{section}:\n{text}\n")
                    httpcontent += f"{section}:\n{text}\n"
                st.markdown(httpcontent, unsafe_allow_html=True)

                st.write("Sales Opportunity")
                salesopp = extractopporunity(httpcontent, selected_optionmodel1)
                st.markdown(salesopp, unsafe_allow_html=True)

                st.write("Create Email")
                emailcontent = createemailforoppt(httpcontent, selected_optionmodel1)
                st.markdown(emailcontent, unsafe_allow_html=True)

                st.write("Speaker Notes")
                speakernotes = createspeakernotes(httpcontent, selected_optionmodel1)
                st.markdown(speakernotes, unsafe_allow_html=True)
