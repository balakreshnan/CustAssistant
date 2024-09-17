import asyncio

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from dotenv import dotenv_values
import logging
import LightsPlugin
from typing import Annotated
from semantic_kernel.functions import kernel_function
from semantic_kernel import __version__

__version__
from services import Service
import os
import time

from service_settings import ServiceSettings
import streamlit as st
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from collections import defaultdict

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (AzureChatPromptExecutionSettings,)
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import KernelArguments
from service_settings import ServiceSettings

@st.cache_resource
def setup_kernel_and_agent():
    kernel = Kernel()
    service_settings = ServiceSettings.create()
    # Remove all services so that this cell can be re-run without restarting the kernel
    kernel.remove_all_services()
    print(os.getcwd())
    base_directory = os.getcwd()  # Gets the current working directory

    # Combine the base directory with the 'plugins' directory
    plugins_directory = os.path.join(base_directory, 'plugins')

    # Add a plugin (the LightsPlugin class is defined below)
    # plugin = kernel.add_plugin(parent_directory=base_directory, plugin_name="plugins")

    service_id = "default"
    kernel.add_service(AzureChatCompletion(service_id=service_id,),)
    #kernel.add_plugin(EmailPlugin(),plugin_name="Email",)
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="ProductSelector")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="Sales")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="TechnicalSupport")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="Selector")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="WebContent")
    chat_completion : AzureChatCompletion = kernel.get_service(type=ChatCompletionClientBase)

    return kernel, chat_completion

# Initialize kernel and function as global variables
# global_kernel, global_chat = setup_kernel_and_agent()

class HttpContentPlugin:
    
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
    
config = dotenv_values("env.env")

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



async def main():
    # Initialize the kernel
    kernel = Kernel()

    service_settings = ServiceSettings.create()

    # Select a service to use for this notebook (available services: OpenAI, AzureOpenAI, HuggingFace)
    selectedService = (
        Service.AzureOpenAI
        if service_settings.global_llm_service is None
        else Service(service_settings.global_llm_service.lower())
    )
    print(f"Using service type: {selectedService}")

    # Add Azure OpenAI chat completion
    kernel.add_service(AzureChatCompletion(
        deployment_name="gpt-4o-2",
        api_key=config["AZURE_OPENAI_API_KEY"],
        base_url=config["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-05-01-preview",
    ))

    # Set the logging level for  semantic_kernel.kernel to DEBUG.
    logging.basicConfig(
        format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("kernel").setLevel(logging.DEBUG)

    # Add a plugin (the LightsPlugin class is defined below)
    kernel.add_plugin(
        LightsPlugin(),
        plugin_name="Lights",
    )

    chat_completion : AzureChatCompletion = kernel.get_service(type=ChatCompletionClientBase)

    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings(tool_choice="auto")
    execution_settings.function_call_behavior = FunctionCallBehavior.EnableFunctions(auto_invoke=True, filters={})

    # Create a history of the conversation
    history = ChatHistory()

    # Initiate a back-and-forth chat
    userInput = None
    while True:
        # Collect user input
        userInput = input("User > ")

        # Terminate the loop if the user says "exit"
        if userInput == "exit":
            break

        # Add user input to the history
        history.add_user_message(userInput)

        # Get the response from the AI
        result = (await chat_completion.get_chat_message_contents(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel,
            arguments=KernelArguments(),
        ))[0]

        # Print the results
        print("Assistant > " + str(result))

        # Add the message from the agent to the chat history
        history.add_message(result)

async def main1(query):
    from semantic_kernel import Kernel

    kernel = Kernel()

    service_settings = ServiceSettings.create()

    # Select a service to use for this notebook (available services: OpenAI, AzureOpenAI, HuggingFace)
    selectedService = (
        Service.AzureOpenAI
        if service_settings.global_llm_service is None
        else Service(service_settings.global_llm_service.lower())
    )
    print(f"Using service type: {selectedService}")

    # Remove all services so that this cell can be re-run without restarting the kernel
    kernel.remove_all_services()

    service_id = None
    if selectedService == Service.OpenAI:
        from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

        service_id = "default"
        kernel.add_service(
            OpenAIChatCompletion(
                service_id=service_id,
            ),
        )
    elif selectedService == Service.AzureOpenAI:
        from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

        service_id = "default"
        kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
            ),
        )

    print(os.getcwd())
    base_directory = os.getcwd()  # Gets the current working directory

    # Combine the base directory with the 'plugins' directory
    plugins_directory = os.path.join(base_directory, 'plugins')
    print('plugins_directory:', plugins_directory)
    print('base_directory:', base_directory)

    # Add a plugin (the LightsPlugin class is defined below)
    plugin = kernel.add_plugin(parent_directory=base_directory, plugin_name="plugins")
    

    httpcontent_plugin = kernel.add_plugin(
        HttpContentPlugin(),
        plugin_name="HttpContentPlugin",
    )
    # joke_function = plugin["joke"]

    # joke = await kernel.invoke(
    #     joke_function,
    #     KernelArguments(input="time travel to dinosaur age", style="super silly"),
    # )
    # print(joke)
    # st.write(joke.value[0].inner_content.choices[0].message.content)

    product_plugin = plugin["ProductSelector"]
    product = await kernel.invoke(
        product_plugin,
        KernelArguments(input=query, style="super silly"),
    )
    print(product)
    st.write(product.value[0].inner_content.choices[0].message.content)



    select_plugin = plugin["Selector"]
    pluginselect = await kernel.invoke(
        select_plugin,
        KernelArguments(input=query, style="super silly"),
    )
    print(pluginselect)
    st.write(pluginselect.value[0].inner_content.choices[0].message.content)


    #result = await kernel.invoke(httpcontent_plugin["fetch_url"], query=query)
    #print(f"The http content is: {result}")
    #st.markdown(f"The http content is: {result}", unsafe_allow_html=True)
    #print('Plugin:', pluginselect.value[0].inner_content.choices[0].message.content)


    # time to run the selected plugin
    sel_plugin = plugin[pluginselect.value[0].inner_content.choices[0].message.content]
    pluginsel = await kernel.invoke(
        sel_plugin,
        KernelArguments(input=query, style="super silly"),
    )
    # print(pluginsel)
    st.markdown(pluginsel, unsafe_allow_html=True)
    #webcontent_plugin = plugin["WebContent"]
    webcontent_plugin = kernel.add_plugin(parent_directory=plugins_directory, plugin_name="WebContent")
    pluginselect1 = await kernel.invoke(
        webcontent_plugin["fetch_url"], query=query,
    )
    # print(pluginselect1)
    st.write(pluginselect1.value["Body"])

async def invoke_agent(query):
    
    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings(tool_choice="auto")
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    st.session_state["history"].add_user_message(query)

    result = (await global_chat.get_chat_message_contents(
            chat_history=st.session_state["history"],
            settings=execution_settings,
            kernel=global_kernel,
            arguments=KernelArguments(),
        ))[0]
    print(str(result))

    st.session_state["history"].add_assistant_message(str(result))

async def run_app():
    st.title("PlugIn Bot")
    st.write('gpt model with Email, Time, Weather, Wait, Color for locatoin Plugin')
    st.write('The known locations are: Boston, London, Miami, Paris, Tokyo, Sydney, Tel Aviv')

    reset = st.button('Reset Messages')

    if reset:
            st.write('Sure thing!')
            history = ChatHistory()
            st.session_state["history"] = history
            st.session_state["history"].add_system_message("You are a helpful assistant.") 
            print("completed reset")
            reset = False

    if "history" not in st.session_state:  
        history = ChatHistory()
        st.session_state["history"] = history
        st.session_state["history"].add_system_message("You are a helpful assistant.") 

    
 


    for msg in st.session_state["history"]:
        print(msg.role + ":" + msg.content)
        if msg.role != AuthorRole.TOOL and len(msg.content) > 0:
            with st.chat_message(msg.role):
                st.markdown(msg.content)

    # React to user input
    if prompt := st.chat_input("Tell me about an email you want to send...(or something else)"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        result = await invoke_agent( prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(result)

def semroute():
    #asyncio.run(main1())
    #main()
    col1, col2 = st.columns([1, 1])
    with col1:
        #query = st.text_area("User Input", "How is power apps used as generative ai application development")
        query = st.text_area("User Input", "show content from accenture web site")
        if st.button("Submit"):
            start_time = time.time()
            asyncio.run(main1(query))
            end_time = time.time()
            st.write(f"Time taken: {end_time - start_time} seconds")#
        # asyncio.run(run_app())  