import wikipedia
# import os
# import ast
# import openai
from dotenv import load_dotenv, find_dotenv
# import datetime
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks import get_openai_callback
# import json
import pandas as pd
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from json.decoder import JSONDecodeError
import streamlit as st

def fetch_species_info_wiki(species_name):
    # placeholder = st.empty()
    # placeholder.empty()
    print("Searching wikipedia for", species_name)
    
    try:
        # Search for the page title on Wikipedia
        search_results = wikipedia.search(species_name)
        

        if not search_results:
            # wiki_feedback = "No plant info found for " + species_name
            # placeholder.text(wiki_feedback)
            plant_info = f"No context provided for {species_name}. No decision is possible"

            return plant_info

        try:
            # Attempt to get the page content for the first result
            page_title = search_results[0]
            page_content = wikipedia.page(page_title).content
        except wikipedia.exceptions.DisambiguationError:
            # Skip disambiguation pages
            # wiki_feedback = "No plant info found for " + species_name
            # placeholder.text(wiki_feedback)
            plant_info = f"No context provided for {species_name}. No decision is possible"
            return plant_info

        # Define keywords for filtering
        keywords = [
            "native", "endemic", "introduced", "cultivated", "invasive",
            "cultivation", "cultivar", "occurring", "occurs", "range",
            "ranges", "distribution", "distributed", "originates", "origin",
            # Add other keywords as needed
        ]

        # Process the content to extract relevant information
        sentences = [sentence for sentence in page_content.split('. ') if any(keyword in sentence.lower() for keyword in keywords)]
        plant_info = ' '.join(sentences).replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
        if len(sentences) > 0:
            print("Plant info found!")
            # wiki_feedback = "Plant info found for " + species_name
        elif len(sentences) == 0:
            print("No information found.")
            # wiki_feedback = "No plant info found for " + species_name
            plant_info = "No context provided. No decision is possible"
        # placeholder = st.empty()
        # placeholder.empty()
        # placeholder.text(wiki_feedback)
        
        return plant_info

    except wikipedia.exceptions.PageError:
        print("No plant info found!")
        wiki_feedback = "No plant info found for " + species_name
        placeholder.text(wiki_feedback)
        plant_info = f"No context provided for {species_name}. No decision is possible"
        return plant_info


def process_species_data(df, chat, output_parser, template_string, format_instructions, progress_callback=None):
    """
    Processes a DataFrame containing species information using an AI chat model.

    Parameters:
    - df (pandas.DataFrame): The DataFrame containing species data.
    - chat (function): The AI chat function to be used for parsing.
    - output_parser (OutputParser): An instance of OutputParser for parsing the chat output.
    - template_string (str): The template string for chat prompts.
    - format_instructions (str): Instructions for formatting the chat messages.

    Returns:
    - pandas.DataFrame: The updated DataFrame with new columns for decision, information source,
                        reasoning, native range, and alien range.
    """
    updated_df = df.copy()
    results_decision = []
    results_information_source = []
    results_reasoning = []
    results_native_range = []
    results_alien_range = []
    total_rows = len(df)
    total_complete = 0

    placeholder = st.empty()

    updated_df['wiki_info'] = updated_df['species'].apply(fetch_species_info_wiki)
    updated_df['wiki_info'] = updated_df['wiki_info'].str.replace('\n', ' ', regex=False)
    updated_df['wiki_info'] = updated_df['wiki_info'].str.replace('\r', ' ', regex=False)
    updated_df['wiki_info'] = updated_df['wiki_info'].str.replace('=', ' ', regex=False)

    # placeholder = st.empty()
    for index, row in updated_df.iterrows():
        total_complete += 1
        species = row['species']
        country = row['country']
        context = row['wiki_info']
        print("Processing", total_complete, "out of", total_rows, ":\n", species, "in", country)

        # Trim the wiki_info if its length is greater than 10,000 characters
        context = context[:10000] if len(context) > 10000 else context

        prompt = ChatPromptTemplate.from_template(template=template_string)
        messages = prompt.format_messages(species=species, country=country, context=context, format_instructions=format_instructions)
        
        response = chat(messages)
        
        try:
            output_dict = output_parser.parse(response.content)
            decision = output_dict.get('decision', 'unknown')
            information_source = output_dict.get('information_source', 'unknown')
            reasoning = output_dict.get('reasoning', 'unknown')
            native_range = output_dict.get('native_range', 'unknown')
            alien_range = output_dict.get('alien_range', 'unknown')
        except JSONDecodeError:
            decision = 'Parsing error'
            information_source = 'Parsing error'
            reasoning = 'Parsing error'
            native_range = 'Parsing error'
            alien_range = 'Parsing error'
        if progress_callback:
            progress_callback((index + 1) / total_rows)

        print("Native range:", native_range, "\n Alien range:", alien_range, "\n Reasoning:", reasoning, "\nDecision: ", decision, "\n")
        # Append to results lists
        results_decision.append(decision)
        results_information_source.append(information_source)
        results_reasoning.append(reasoning)
        results_native_range.append(native_range)
        results_alien_range.append(alien_range)
        # placeholder.empty()
        # report_out = "Results for " + species + " in " + country + ":\n\nNative range: " + native_range + "\nAlien range: " + alien_range + "\nReasoning: " + reasoning + "\n\nDecision: " + decision + "\n"
        report_out = (
        f"### Results for {species} in {country}:\n\n"
        f"**Wikipedia Context:** {context}\n\n"
        f"**Native range:** {native_range}\n\n"
        f"**Alien range:** {alien_range}\n\n"
        f"**Context Citation:** {information_source}\n\n"
        f"**Reasoning:** {reasoning}\n\n"
        f"**Decision:** {decision}\n"
)
        placeholder.markdown(report_out)

    # Update DataFrame
    updated_df['decision'] = results_decision
    updated_df['information_source'] = results_information_source
    updated_df['reasoning'] = results_reasoning
    updated_df['native_range'] = results_native_range
    updated_df['alien_range'] = results_alien_range
    
    return updated_df
