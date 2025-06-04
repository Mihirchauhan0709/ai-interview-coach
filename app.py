# app.py (FastAPI Backend)
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from question_generator import generate_question, generate_jd_based_questions # Add new import
from typing import List # For response model
from code_evaluator import evaluate_code
from ai_interviewer import follow_up_questions, feedback_on_code
from system_design_assessor import assess_design
from fastapi.middleware.cors import CORSMiddleware
from text_evaluator import evaluate_text_answer
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


app = FastAPI()

# Allow frontend interaction (CORS settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to AI Interview Coach"}

@app.head("/")
def head():
    return


class QuestionRequest(BaseModel):
    mode: str
    difficulty: str
    
class CodeFeedbackRequest(BaseModel): # Ensure this is defined
    user_code: str
    question: str

class CodeEvaluationRequest(BaseModel):
    language: str
    user_code: str
    question_id: int

class TextEvaluationRequest(BaseModel):
    user_answer: str
    question: str
    
class FollowUpRequest(BaseModel): # For the /ai-follow-up endpoint
    user_answer: str
    question_text: str # Changed from question_id
    
class JDQuestionRequest(BaseModel):
    job_description: str
    num_questions: Optional[int] = 3
    
class JDQuestionsResponse(BaseModel):
    questions: List[str]

@app.post("/generate-question")
def generate(request: QuestionRequest):  
    try:
        mode = request.mode
        difficulty = request.difficulty
        print(f"🔹 Received Request -> Mode: {request.mode}, Difficulty: {request.difficulty}")

        question = generate_question(request.mode, request.difficulty)
        print(f"✅ Generated Question: {question}")

        return {"question": question}
    
    except Exception as e:
        print(f"🔥 ERROR processing request: {e}")
        return {"error": "Internal Server Error", "details": str(e)}

@app.post("/evaluate-code")
def evaluate(request: CodeEvaluationRequest):
    """
    Evaluate code submission using predefined test cases
    """
    try:
        evaluation = evaluate_code(request.language, request.user_code, request.question_id)
        
        # Format response based on evaluation result
        if "error" in evaluation:
            return {
                "status": "error",
                "message": evaluation["error"],
                "details": evaluation.get("stderr", "")
            }
        
        # For successful evaluations with test results
        if "success" in evaluation and evaluation["success"]:
            passed = evaluation.get("passed", 0)
            total = evaluation.get("total", 0)
            
            return {
                "status": "success",
                "passed": passed,
                "total": total,
                "passed_percentage": (passed / total * 100) if total > 0 else 0,
                "results": evaluation.get("results", [])
            }
        
        # For backward compatibility with original evaluator
        return {"evaluation": evaluation}
            
    except Exception as e:
        print(f"🔥 ERROR evaluating code: {str(e)}")
        return {"status": "error", "message": "Failed to evaluate code", "details": str(e)}

@app.post("/evaluate-text")
def evaluate_text(request: TextEvaluationRequest):
    feedback = evaluate_text_answer(request.user_answer, request.question)
    return {"feedback": feedback}

@app.post("/ai-follow-up") # Updated endpoint for text-based follow-ups
def follow_up(request: FollowUpRequest):
    # Pass the original question text to the follow_up_questions function
    followups = follow_up_questions(request.user_answer, request.question_text)
    return {"follow_up": followups}

@app.post("/assess-design")
def assess(user_response: dict):
    feedback = assess_design(user_response)
    return {"feedback": feedback}

@app.post("/evaluate-code-ai")
def evaluate_code_ai(request: CodeFeedbackRequest):
    # feedback_on_code now returns a dict
    structured_response = feedback_on_code(request.user_code, request.question)
    return structured_response # FastAPI will automatically convert this dict to JSON

@app.get("/get-test-cases/{question_id}")
def get_test_cases_for_question(question_id: int):
    """
    Get the test cases for a specific question ID.
    This helps frontend display what test cases will be used.
    """
    try:
        from code_evaluator import get_test_cases
        
        test_cases = get_test_cases(question_id)
        if not test_cases or "cases" not in test_cases:
            return {"status": "error", "message": f"No test cases found for question ID {question_id}"}
        
        # Format test cases for frontend display (remove expected answers if desired)
        formatted_cases = []
        for i, case in enumerate(test_cases["cases"]):
            formatted_cases.append({
                "test_number": i + 1,
                "input": case["input"],
                # Optional: include expected for practice mode, exclude for exam mode
                # "expected": case["expected"]  
            })
            
        return {
            "status": "success",
            "function_name": test_cases["function_name"],
            "test_cases": formatted_cases
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

# If you wish to keep backward compatibility with simple execution
@app.post("/execute-code")
def execute_code(language: str = Body(...), user_code: str = Body(...)):
    """
    Simple code execution without test cases - just runs the code
    """
    try:
        import subprocess
        import tempfile
        import sys
        
        if language.lower() != "python":
            return {"error": "Currently, only Python execution is supported."}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_file.write(user_code.encode())
            temp_file.flush()
            
            try:
                result = subprocess.run([sys.executable, temp_file.name],
                                      capture_output=True, text=True, timeout=10)
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
            except subprocess.TimeoutExpired:
                return {"error": "Code execution timed out."}
    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}
    
@app.post("/generate-jd-questions", response_model=JDQuestionsResponse)
async def generate_jd_questions_endpoint(request: JDQuestionRequest):
    try:
        print(f"🔹 Received JD Question Request for {request.num_questions} questions.")
        result = generate_jd_based_questions(request.job_description, request.num_questions)
        print(f"✅ Generated JD Questions: {result['questions']}")
        return result
    except Exception as e:
        print(f"🔥 ERROR processing JD question request: {e}")
        # Log the full error for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)