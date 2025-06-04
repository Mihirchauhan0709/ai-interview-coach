# question_generator.py
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)


def generate_question(mode: str, difficulty: str):
    print("mode:", mode)
    print("difficulty:", difficulty)
    prompt = f"Generate a {difficulty} level technical interview question for a {mode} role, suitable for top companies. The question should be clear, concise, and appropriate for a coding/technical interview. Aim for unique questions not commonly found with a quick search. Do not include any preamble, just the question itself."
    response = llm.invoke([HumanMessage(content=prompt)]) # Use invoke
    return response.content

def generate_jd_based_questions(job_description: str, num_questions: int = 3):
    prompt = f"""
    Analyze the following job description carefully.
    Based *only* on the skills, technologies, and responsibilities mentioned in this job description, generate {num_questions} distinct interview questions.
    The questions can be a mix of technical, behavioral (related to specific JD competencies), or scenario-based.
    For each question, ensure it directly assesses something stated or implied in the JD.
    Return the questions as a numbered list. Do not include any other text or preamble.

    Job Description:
    ---
    {job_description}
    ---

    Generated Questions:
    """
    response = llm.invoke([HumanMessage(content=prompt)]) # Use invoke
    questions = [q.strip() for q in response.content.splitlines() if q.strip() and q.strip()[0].isdigit()]
    if not questions: # Fallback if LLM doesn't number them or output is unexpected
        questions = [q.strip() for q in response.content.splitlines() if q.strip()]
    return {"questions": questions if questions else [response.content]} # Ensure it's always a list