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

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
config = dotenv_values("env.env")

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

    # Add a plugin (the LightsPlugin class is defined below)
    plugin = kernel.add_plugin(parent_directory=base_directory, plugin_name="plugins")
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

    # time to run the selected plugin
    sel_plugin = plugin[pluginselect.value[0].inner_content.choices[0].message.content]
    pluginsel = await kernel.invoke(
        sel_plugin,
        KernelArguments(input=query, style="super silly"),
    )
    print(pluginsel)
    st.write(pluginsel.value[0].inner_content.choices[0].message.content)



def semroute():
    #asyncio.run(main1())
    #main()
    col1, col2 = st.columns([1, 1])
    with col1:
        query = st.text_area("User Input", "How is power apps used as generative ai application development")
        if st.button("Submit"):
            start_time = time.time()
            asyncio.run(main1(query))
            end_time = time.time()
            st.write(f"Time taken: {end_time - start_time} seconds")