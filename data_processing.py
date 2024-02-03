import wikipedia

from dotenv import load_dotenv, find_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks import get_openai_callback
import pandas as pd
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from json.decoder import JSONDecodeError
import streamlit as st



def process_resume(resume, chat, output_parser, template_string, format_instructions, desired_education, desired_experience, desired_skills, job_description):

    
    prompt = ChatPromptTemplate.from_template(template=template_string)
    messages = prompt.format_messages(resume = resume, 
                                      desired_education=desired_education, 
                                      desired_experience=desired_experience,
                                      desired_skills = desired_skills,
                                      job_description=job_description, 
                                      format_instructions=format_instructions)
    
    response = chat(messages)
    output_dict = output_parser.parse(response.content)
    candidate_name = output_dict.get('name', 'unknown')
    candidate_contact = output_dict.get('contact', 'unknown')
    relevant_experience = output_dict.get('relevant_experience', 'unknown')
    relevant_skills = output_dict.get('relevant_skills', 'unknown')
    relevant_education = output_dict.get('relevant_education', 'unknown')
    candidate_score = output_dict.get('candidate_score', 'unknown')
    score_justification = output_dict.get('score_justification', 'unknown')


    return candidate_name, candidate_contact, relevant_experience, relevant_skills, relevant_education, candidate_score, score_justification




def process_folder(resume_directory, chat, output_parser, template_string, format_instructions, desired_education, desired_experience, job_description):
    # I need this to go through the list of files, check if it is doc or pdf, load text accordingly, create the
    # resume object, and pass it to process resume, using the returned values to populate the results df.
    results = {
        'file': [],
        'name': [],
        'contact':[],
        'experience': [],
        'skills': [],
        'education': [],
        'score': [],
        'justification': []
    }
    total_remaining = len(os.listdir(resume_directory))
    for filename in os.listdir(resume_directory):
        filepath = os.path.join(resume_directory, filename)
        if filename.endswith('.docx'):
            loader = Docx2txtLoader(filepath)
            resume = loader.load()
        elif filename.endswith('.pdf'):
            loader = PyPDFLoader(filepath)
            resume = loader.load_and_split()
        else:
            print(f"Unsupported file format for {filename}. Skipping.")
            continue
        
        name, contact, experience, skills, education, score, justification = process_resume(
            resume, chat, output_parser, template_string, format_instructions, 
            desired_education, desired_experience, job_description
        )
        results['file'].append(filename)
        results['name'].append(name)
        results['contact'].append(contact)
        results['experience'].append(experience)
        results['skills'].append(skills)
        results['education'].append(education)
        results['score'].append(score)
        results['justification'].append(justification)
        total_remaining -= 1
        print(total_remaining)

    results_df = pd.DataFrame(results)
    return results_df