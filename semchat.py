import streamlit as st
import asyncio
from typing import Annotated
import os
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
#from plugins.WebContent import WebContent
#from plugins.ProductSelector import ProductSelector
#from plugins.Sales import Sales
#from plugins.Selector import Selector
#from plugins.TechnicalSupport import TechnicalSupport

@st.cache_resource
def setup_kernel_and_chat():
    kernel = Kernel()
    service_settings = ServiceSettings.create()
    # Remove all services so that this cell can be re-run without restarting the kernel
    kernel.remove_all_services()
    base_directory = os.getcwd()  # Gets the current working directory

    # Combine the base directory with the 'plugins' directory
    plugins_directory = os.path.join(base_directory, 'plugins')

    service_id = "default"
    kernel.add_service(AzureChatCompletion(service_id=service_id,),)
    #kernel.add_plugin(WebContent(),plugin_name="WebContent",)
    #kernel.add_plugin(ProductSelector(),plugin_name="ProductSelector",)
    #kernel.add_plugin(Sales(),plugin_name="Sales",)
    #kernel.add_plugin(Selector(),plugin_name="Selector",)
    #kernel.add_plugin(TechnicalSupport(),plugin_name="TechnicalSupport",)
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="ProductSelector")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="Sales")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="TechnicalSupport")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="Selector")
    kernel.add_plugin(parent_directory=plugins_directory, plugin_name="WebContent")


    chat_completion : AzureChatCompletion = kernel.get_service(type=ChatCompletionClientBase)

    return kernel, chat_completion

global_kernel, global_chat = setup_kernel_and_chat()

# A helper method to invoke the agent with the user input
async def invoke_agent(input_text):
   
    
    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings(tool_choice="auto")
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()


    st.session_state["history"].add_user_message(input_text)

    result = (await global_chat.get_chat_message_contents(
            chat_history=st.session_state["history"],
            settings=execution_settings,
            kernel=global_kernel,
            arguments=KernelArguments(),
        ))[0]
    print(str(result))

    st.session_state["history"].add_assistant_message(str(result))
    return str(result)

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

def semchat():
    asyncio.run(run_app())