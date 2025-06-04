import subprocess
import tempfile
import sys
import importlib.util
import json

def evaluate_code(language: str, user_code: str, question_id: int):
    if language.lower() != "python":
        return {"error": "Currently, only Python evaluation is supported."}

    # Define test cases based on question_id
    test_cases = get_test_cases(question_id)
    
    # First run - just execute the code to catch syntax errors
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(user_code.encode())
        temp_file.flush()
        
        try:
            # Basic execution check
            result = subprocess.run([sys.executable, temp_file_path],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": "Code execution failed with errors."
                }
            
            # If basic execution succeeded, run test cases
            test_results = run_test_cases(temp_file_path, test_cases, question_id)
            return test_results
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Code execution timed out."}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

def get_test_cases(question_id):
    """Return test cases based on question ID."""
    test_case_map = {
        1: {  # Max subarray sum
            "function_name": "max_subarray_sum",
            "cases": [
                {"input": [[1, 2, 3, 4, 5]], "expected": 15},
                {"input": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
                {"input": [[-1, -2, -3, -4]], "expected": -1},
                {"input": [[5]], "expected": 5}
            ]
        },
        # Add more question IDs and their test cases here
    }
    
    return test_case_map.get(question_id, {"function_name": "", "cases": []})

def run_test_cases(module_path, test_cases, question_id):
    """Import the user's module and run test cases against it."""
    if not test_cases or "function_name" not in test_cases:
        return {"success": False, "error": f"No test cases defined for question ID {question_id}"}
    
    function_name = test_cases["function_name"]
    cases = test_cases["cases"]
    
    try:
        # Import the module
        spec = importlib.util.spec_from_file_location("user_module", module_path)
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        
        # Get the function
        if not hasattr(user_module, function_name):
            return {"success": False, "error": f"Function '{function_name}' not found in your code"}
        
        user_function = getattr(user_module, function_name)
        
        # Run test cases
        results = []
        passed = 0
        
        for i, case in enumerate(cases):
            try:
                actual_output = user_function(*case["input"])
                matches = actual_output == case["expected"]
                
                if matches:
                    passed += 1
                
                results.append({
                    "test_case": i + 1,
                    "input": case["input"],
                    "expected": case["expected"],
                    "actual": actual_output,
                    "passed": matches
                })
            except Exception as e:
                results.append({
                    "test_case": i + 1,
                    "input": case["input"],
                    "error": str(e),
                    "passed": False
                })
        
        return {
            "success": True,
            "passed": passed,
            "total": len(cases),
            "results": results
        }
    
    except Exception as e:
        return {"success": False, "error": f"Error running test cases: {str(e)}"}

# Example usage:
if __name__ == "__main__":
    # Example code for max_subarray_sum
    user_code = """
def max_subarray_sum(nums):
    if not nums:
        raise ValueError("Input array must contain at least one element.")
    
    max_current = max_global = nums[0]
    
    for num in nums[1:]:
        max_current = max(num, max_current + num)
        max_global = max(max_global, max_current)
    
    return max_global
"""
    
    result = evaluate_code("python", user_code, 1)
    print(json.dumps(result, indent=2))