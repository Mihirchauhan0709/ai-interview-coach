# text_evaluator.py
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)

def evaluate_text_answer(answer: str, question: str):
    prompt = f"""Evaluate the following answer to a technical interview question:

    Question: "{question}"
    Answer: "{answer}"

    Provide structured feedback based on:
    - Relevance
    - Completeness
    - Clarity
    - Technical correctness

    Return a paragraph of feedback, and rate the answer from 1 to 10.
    """
    response = llm([HumanMessage(content=prompt)])
    return response.content
