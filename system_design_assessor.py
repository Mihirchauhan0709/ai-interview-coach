# system_design_assessor.py
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)

def assess_design(user_response: dict):
    prompt = f"Evaluate the following system design responses: {user_response}. \
              Provide structured feedback on scalability, database choice, caching, API design, and load balancing."
    response = llm([HumanMessage(content=prompt)])
    return response.content
