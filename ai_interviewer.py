# ai_interviewer.py
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAIllm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)

def follow_up_questions(user_answer: str, original_question_text: str): # Updated signature
    prompt = f"""The candidate was asked: '{original_question_text}'
              The candidate responded with: '{user_answer}'.
              Generate two concise, clarifying or follow-up interview questions based on their response to the original question.
              Each follow-up question should be on a new line. Do not include any preamble, just the questions."""
    response = llm.invoke([HumanMessage(content=prompt)]) # Use invoke for newer Langchain
    # Ensure proper splitting and filtering of empty lines
    return [line.strip() for line in response.content.split("\n") if line.strip()]


def feedback_on_code(code: str, question: str):
    prompt = f"""You are an interview coach. Evaluate the following Python code written in response to a coding interview question.

    Question: {question}
    Code:
    ```python
    {code}
    ```

    First, provide constructive feedback on logic, efficiency, readability, and any improvements.
    Then, on new lines, provide exactly two follow-up or clarifying questions to ask the candidate, each prefixed with "Follow-up:".
    Ensure your response is structured so that feedback comes first, then the follow-up questions.

    Example of your output format:
    [Your constructive feedback here...]

    Follow-up: Could you explain the time complexity of your solution?
    Follow-up: How would you handle an empty input array?
    """
    response = llm.invoke([HumanMessage(content=prompt)]) # Use invoke
    response_content = response.content
    
    lines = response_content.splitlines()
    feedback_lines = []
    follow_ups = []
    
    for line in lines:
        if line.lower().startswith("follow-up:"):
            follow_ups.append(line.split(":", 1)[1].strip())
        else:
            feedback_lines.append(line)
            
    feedback_text = "\n".join(feedback_lines).strip()
    
    # If no follow-ups were parsed with "Follow-up:", try a fallback if the LLM missed the prefix
    if not follow_ups and len(feedback_lines) > 2: # Heuristic: if feedback is long, last lines might be implicit followups
        # This is a simple heuristic. More robust parsing might be needed if LLM is inconsistent.
        # For now, let's assume the LLM follows the "Follow-up:" prefix instruction.
        pass

    return {"feedback_text": feedback_text, "follow_up_questions": follow_ups}
