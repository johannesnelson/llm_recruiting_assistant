

import openai
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks import get_openai_callback
import pandas as pd
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from json.decoder import JSONDecodeError

def prepare_LLM(llm_model = "gpt-3.5-turbo"):
    llm_model = llm_model
    chat = ChatOpenAI(temperature=0.0, model=llm_model)
    return chat



def prepare_template_string():
    
    template_string = """
    You are acting as a recruiting assistant. Your job is to carefully scan resumes and \
    identify the best candidates for the role. In order to do this, you will first need to \
    understand the job description, the required skills/experience, and the desired \
    skills\experience. You will be asked to first extract relevant information from each resume, \
    and then to rank the candidates fit on a scale from 1 - 10. 
 
    
    The job description, desired level of education, and desired skills/experience are delineated \
    by the triple backticks below. The candidate resume will be provided after this, and format instructions \
    will also be provided.
    
    ``` 
    Job description: {job_description}, Desired education level: {desired_education}, Desired experience: {desired_experience}, Desired skills: {desired_skills}
    ```
    
    Candidate resume: {resume}
    
    {format_instructions}
    """
    return template_string

def prepare_chat_schemas():
    
    candidate_name = ResponseSchema(name="name",
                                     description="Simply state the name of the candidate."
                                    )
    candidate_contact = ResponseSchema(name="contact",
                                     description="Simply copy the candidate's email address here."
                                    )        
    relevant_experience = ResponseSchema(name="relevant_experience",
                                     description="Based upon the job description, please extract any relevant experience from the resume and "
                                     "state it here. This experience should be relevant to the job description and the desired experience/skills. "
                                    )
    relevant_skills = ResponseSchema(name="relevant_skills",
                                     description="Based upon the job description, please extract any relevant skills from the resume and "
                                     "state it here. These skills should be relevant to the job description and the desired experience/skills."
                                     )
    
    
    relevant_education = ResponseSchema(name="relevant_education",
                                     description= "Based upon the job description, please extract information about relevant education from the resume and "
                                     "state it here. This information about education should be relevant to the job description and the desired level of education.")
    
    
    candidate_score = ResponseSchema(name="candidate_score",
                                          description="Here, you will rate the candidate on a scale from 1 - 10--with a 10 being a perfect fit (matches desired  "
                                          " perfectly). This should be a single number response only.")
    
    score_justification = ResponseSchema(name="score_justification",
                                          description="Here, you will justify your score, highlighting specific parts of the information that you extracted to "
                                          " make your case. This should be a brief, 1 - 5 sentence description for why this score was assigned that cites specific "
                                          " attributes from the candidate resume and the job description/desired qualifications.")
    
    response_schemas = [candidate_name,
                        candidate_contact,
                        relevant_experience, 
                        relevant_skills,
                        relevant_education,
                        candidate_score,
                        score_justification]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    return response_schemas, output_parser, format_instructions
