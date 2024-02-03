import streamlit as st
import pandas as pd
import data_processing as dp
import prompt_chat_config as pcc
from dotenv import load_dotenv
import os
import openai
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import tempfile
from langchain.callbacks import get_openai_callback


# Load API key from .env
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")


def main():
    st.title("Resume Screener Prototype")

    uploaded_files = st.file_uploader(
        "Upload all resumes that you would like to screen",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
    
    with st.form("Position Details"):
        st.write("Position Details:")
        job_description = st.text_input("Job Description (be very specific)")
        desired_education = st.text_input("Desired Level of Education")
        desired_experience = st.text_input("Desired Experience")
        desired_skills = st.text_input("Desired Skills")
        submit_button = st.form_submit_button(label='Screen Resumes')

    if uploaded_files is not None and submit_button:
        chat = pcc.prepare_LLM(llm_model= 'gpt-4')
        template_string = pcc.prepare_template_string()
        response_schemas, output_parser, format_instructions = pcc.prepare_chat_schemas()

        results = {
            'file': [],
            'name': [],
            'contact': [],
            'experience': [],
            'skills': [],
            'education': [],
            'score': [],
            'justification': []
        }
        with get_openai_callback() as cb:

            for uploaded_file in uploaded_files:
                file_name = uploaded_file.name
                if file_name.endswith('.docx'):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpfile:
                        tmpfile.write(uploaded_file.getvalue())
                        tmpfile_path = tmpfile.name

                    loader = Docx2txtLoader(tmpfile_path)
                    resume = loader.load()

                    os.unlink(tmpfile_path)  # Clean up the temp file after use

                elif file_name.endswith('.pdf'):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                        tmpfile.write(uploaded_file.getvalue())
                        tmpfile_path = tmpfile.name

                    loader = PyPDFLoader(tmpfile_path)
                    resume = loader.load_and_split()

                    os.unlink(tmpfile_path)  # Clean up the temp file after use

                else:
                    st.warning(f"Unsupported file format for {file_name}. Skipping.")
                    continue  # Skip this iteration and continue with the next file

                # Process the resume content
                name, contact, experience, skills, education, score, justification = dp.process_resume(
                    resume, chat, output_parser, template_string, format_instructions, 
                    desired_education, desired_experience, desired_skills, job_description
                )
                
                results['file'].append(file_name)
                results['name'].append(name)
                results['contact'].append(contact)
                results['experience'].append(experience)
                results['skills'].append(skills)
                results['education'].append(education)
                results['score'].append(score)
                results['justification'].append(justification)
                print(cb)

        results_df = pd.DataFrame.from_dict(results)
        st.write(results_df)
        csv = results_df.to_csv(index=False).encode('utf-8')

        # Download button
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name='resume_screening_results.csv',
            mime='text/csv',
        )

if __name__ == "__main__":
    main()
