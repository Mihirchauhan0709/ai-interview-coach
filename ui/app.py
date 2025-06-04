import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(page_title="AI Interview Coach", layout="wide", initial_sidebar_state="expanded")

# --- Initialize Session State Variables ---
# Ensure all necessary session state variables are initialized once
default_states = {
    "memory": [],
    "followups": [],
    "answered_followups": {},
    "current_question_id": 1, # For test case mapping in standard mode
    "question": None,           # The current active question text
    "test_cases": None,         # Test cases for the current standard coding question
    "jd_questions_list": [],    # List of questions generated from JD
    "current_jd_question_index": -1, # Index of the current JD question (-1 if none active)
    "active_interaction_type": None, # "main_question" or "follow_up"
    "current_follow_up_index": -1 # Index of the currently active follow-up
}
for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Helper Function to Reset for New Question ---
def reset_for_new_main_question():
    st.session_state.question = None
    st.session_state.followups = []
    st.session_state.answered_followups = {}
    st.session_state.test_cases = None
    st.session_state.active_interaction_type = None
    st.session_state.current_follow_up_index = -1

def reset_jd_mode_state():
    st.session_state.jd_questions_list = []
    st.session_state.current_jd_question_index = -1

# --- Title ---
st.title("🚀 AI-Powered Interview Coach")

# --- Tabs for different modes ---
tab1, tab2 = st.tabs(["🎯 Standard Interview Practice", "📄 Job Description Mode"])

# --- TAB 1: Standard Interview Practice ---
with tab1:
    st.header("🎯 Standard Interview Practice")
    mode = st.selectbox(
        "Select Interview Topic:",
        ["Data Science & ML", "Software Engineering & System Design", "Data Structures & Algorithms", "Database & SQL Queries", "Networking & OS", "Behavioral & HR", "Cloud Computing & DevOps"],
        key="standard_topic_selector" # Unique key for selectbox
    )
    difficulty = st.selectbox(
        "Select Difficulty Level:",
        ["Easy", "Medium", "Hard", "Expert"],
        key="standard_difficulty_selector" # Unique key
    )

    if st.button("Generate Standard Question", key="gen_std_q_btn"):
        reset_for_new_main_question()
        reset_jd_mode_state() # Also clear JD mode state

        try:
            request_payload = {"mode": mode, "difficulty": difficulty}
            with st.spinner("Generating question..."):
                res = requests.post("http://localhost:8000/generate-question", json=request_payload)
            
            if res.status_code == 200:
                data = res.json()
                question_data = data.get("question")
                if question_data and question_data != "No question generated":
                    st.session_state.question = question_data
                    st.session_state.active_interaction_type = "main_question"
                    
                    question_id_map = {
                        "Data Structures & Algorithms": 1, "Database & SQL Queries": 2,
                        "Software Engineering & System Design": 3, "Data Science & ML": 4,
                        "Networking & OS": 5, "Behavioral & HR": 6, "Cloud Computing & DevOps": 7,
                    }
                    st.session_state.current_question_id = question_id_map.get(mode, 0) # Default to 0 if mode not found
                    
                    if mode in ["Data Structures & Algorithms", "Database & SQL Queries"] and st.session_state.current_question_id != 0:
                        try:
                            with st.spinner("Fetching test cases..."):
                                test_cases_res = requests.get(
                                    f"http://localhost:8000/get-test-cases/{st.session_state.current_question_id}"
                                )
                            if test_cases_res.status_code == 200:
                                st.session_state.test_cases = test_cases_res.json()
                            else:
                                st.warning(f"Could not fetch test cases (Status: {test_cases_res.status_code}). No pre-defined test cases for this one, or an error occurred.")
                        except requests.exceptions.RequestException as e_tc:
                            st.warning(f"Network error fetching test cases: {e_tc}")
                        except Exception as e_tc_generic:
                             st.warning(f"Error fetching test cases: {e_tc_generic}")
                else:
                    st.error("Failed to generate a valid question from the AI.")
                st.rerun()
            else:
                st.error(f"Error generating question: {res.status_code} - {res.text}")
        except requests.exceptions.RequestException as e_req:
            st.error(f"Network error: {e_req}")
        except Exception as e_gen:
            st.error(f"An unexpected error occurred during question generation: {e_gen}")
            
# --- TAB 2: Job Description Mode ---
with tab2:
    st.header("📄 Job Description Mode")
    jd_text = st.text_area("Paste Job Description Here:", height=250, key="jd_input_area")

    if st.button("Generate Questions from JD", key="gen_jd_q_btn"):
        if jd_text.strip():
            reset_for_new_main_question() # Reset standard interview state
            reset_jd_mode_state()

            try:
                request_payload = {"job_description": jd_text, "num_questions": 3}
                with st.spinner("Analyzing JD and generating questions..."):
                    res = requests.post("http://localhost:8000/generate-jd-questions", json=request_payload)
                
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.jd_questions_list = data.get("questions", [])
                    if st.session_state.jd_questions_list:
                        st.session_state.current_jd_question_index = 0
                        st.session_state.question = st.session_state.jd_questions_list[0]
                        st.session_state.active_interaction_type = "main_question"
                        st.success(f"Generated {len(st.session_state.jd_questions_list)} questions from the JD!")
                    else:
                        st.warning("The AI could not generate questions from this JD. Please try rephrasing or a different JD.")
                    st.rerun()
                else:
                    st.error(f"Error generating JD-based questions: {res.status_code} - {res.text}")
            except requests.exceptions.RequestException as e_req_jd:
                st.error(f"Network error: {e_req_jd}")
            except Exception as e_gen_jd:
                st.error(f"An unexpected error occurred during JD question generation: {e_gen_jd}")
        else:
            st.warning("Please paste a job description first.")

    if st.session_state.jd_questions_list and st.session_state.current_jd_question_index != -1:
        idx = st.session_state.current_jd_question_index
        if idx < len(st.session_state.jd_questions_list):
            # This ensures st.session_state.question is set for the current JD question
            st.session_state.question = st.session_state.jd_questions_list[idx]
            st.markdown(f"**Currently on JD Question {idx + 1} of {len(st.session_state.jd_questions_list)}**")
        # No "else" needed here as the main question display block handles if question is None


# --- COMMON UI FOR DISPLAYING MAIN QUESTION & HANDLING INPUT ---
if st.session_state.question and st.session_state.active_interaction_type == "main_question":
    current_main_question = st.session_state.question
    st.markdown("---")
    st.subheader("📝 Interview Question:")
    st.markdown(f"> {current_main_question}")

    # Dynamic key for radio button to reset its state when the question changes
    main_input_type_key = f"main_input_type_{hash(current_main_question)}"
    input_type = st.radio(
        "Choose your response type:",
        ["Text Response", "Code Editor"],
        key=main_input_type_key,
        horizontal=True
    )

    if input_type == "Code Editor":
        st.subheader("💻 Your Code Solution:")
        if st.session_state.test_cases and st.session_state.test_cases.get("status") == "success":
            test_case_data = st.session_state.test_cases
            with st.expander("View Test Cases"):
                st.write(f"**Function Name (if applicable)**: `{test_case_data.get('function_name')}`")
                st.write("Your code might be tested with inputs like these:")
                for case in test_case_data.get("test_cases", []):
                    st.code(f"Test {case.get('test_number')}: Input -> {json.dumps(case.get('input'))}")
        elif st.session_state.current_jd_question_index != -1:
             st.info("For JD-based coding questions, focus on clarity, efficiency, and correctness. Specific test cases are not pre-defined here.")

        # Dynamic key for text area
        main_code_area_key = f"main_code_area_{hash(current_main_question)}"
        user_code = st.text_area("Write your Python code here:", height=300, key=main_code_area_key)

        main_submit_code_key = f"main_submit_code_btn_{hash(current_main_question)}"
        if st.button("Submit Code Solution", key=main_submit_code_key):
            if user_code.strip():
                eval_results_display = None # To store formatted eval results for memory
                ai_feedback_text = "Could not get AI feedback." # Default

                # 1. Evaluate code with test cases (if applicable)
                # For JD mode, question_id might be 0 or irrelevant for specific test cases.
                # The backend /evaluate-code should handle question_id=0 gracefully (e.g., syntax check only)
                q_id_for_eval = st.session_state.current_question_id if st.session_state.current_jd_question_index == -1 else 0
                
                with st.spinner("Running your code against test cases..."):
                    eval_payload = {"language": "python", "user_code": user_code, "question_id": q_id_for_eval}
                    eval_response = requests.post("http://localhost:8000/evaluate-code", json=eval_payload)

                if eval_response.status_code == 200:
                    result = eval_response.json()
                    st.subheader(f"⚙️ Code Test Results:")
                    if result.get("status") == "success":
                        passed = result.get('passed', 0)
                        total = result.get('total', 0)
                        percentage = result.get('passed_percentage', 0)
                        st.success(f"{passed}/{total} Tests Passed ({percentage:.1f}%)")
                        eval_results_display = f"{passed}/{total} Tests Passed ({percentage:.1f}%)"
                        with st.expander("Detailed Test Results", expanded=not (passed == total and total > 0) ):
                            for test in result.get("results", []):
                                test_icon = "✅" if test.get("passed") else "❌"
                                color = "green" if test.get("passed") else "red"
                                st.markdown(f"<span style='color:{color};'>{test_icon} **Test {test.get('test_case')}**: Input: `{test.get('input')}`</span>", unsafe_allow_html=True)
                                if not test.get("passed"):
                                    st.markdown(f"    Expected: `{test.get('expected')}`, Got: `{test.get('actual')}`")
                                    if "error" in test and test.get("error"): st.error(f"    Error: {test.get('error')}")
                    elif "error" in result:
                        st.error(f"Code Execution Error: {result.get('error')}")
                        if "details" in result and result.get("details"): st.code(result.get("details"), language="text")
                        eval_results_display = f"Execution Error: {result.get('error')}"
                    else: # Fallback
                        st.json(result)
                        eval_results_display = "Evaluation response in unknown format."
                else:
                    st.error(f"Error evaluating code: {eval_response.status_code} - {eval_response.text}")
                    eval_results_display = f"Evaluation API Error {eval_response.status_code}"

                # 2. Get AI feedback on the code and potential follow-ups
                with st.spinner("Getting AI feedback on your code..."):
                    feedback_payload = {"user_code": user_code, "question": current_main_question}
                    ai_feedback_res = requests.post("http://localhost:8000/evaluate-code-ai", json=feedback_payload)
                
                if ai_feedback_res.status_code == 200:
                    ai_data = ai_feedback_res.json()
                    ai_feedback_text = ai_data.get("feedback_text", "Could not retrieve AI feedback text.")
                    generated_followups = ai_data.get("follow_up_questions", [])
                    
                    st.subheader("🤖 AI Code Feedback & Improvements")
                    st.markdown(ai_feedback_text)

                    if generated_followups:
                        st.session_state.followups.extend(generated_followups)
                else:
                    st.error(f"Failed to get AI code feedback: {ai_feedback_res.status_code} - {ai_feedback_res.text}")

                st.session_state.memory.append({
                    "question": current_main_question, "response": user_code, "type": "code",
                    "results": eval_results_display, "feedback": ai_feedback_text
                })
                
                st.session_state.active_interaction_type = "follow_up" # Move to follow-up phase
                st.session_state.current_follow_up_index = 0 if st.session_state.followups else -1
                st.rerun()
            else:
                st.warning("Please write some code before submitting.")

    elif input_type == "Text Response":
        st.subheader("🗣️ Your Text Answer:")
        # Dynamic key for text area
        main_text_area_key = f"main_text_area_{hash(current_main_question)}"
        user_answer = st.text_area("Write your answer here:", key=main_text_area_key)

        main_submit_text_key = f"main_submit_text_btn_{hash(current_main_question)}"
        if st.button("Submit Text Answer", key=main_submit_text_key):
            if user_answer.strip():
                ai_feedback_text = "Could not get AI feedback." # Default

                # 1. Get AI feedback on the text answer
                with st.spinner("Getting AI feedback on your answer..."):
                    feedback_payload = {"user_answer": user_answer, "question": current_main_question}
                    feedback_response = requests.post("http://localhost:8000/evaluate-text", json=feedback_payload)
                
                if feedback_response.status_code == 200:
                    ai_feedback_text = feedback_response.json().get("feedback", "Could not retrieve AI feedback.")
                    st.subheader("💡 AI Feedback on Your Answer")
                    st.markdown(ai_feedback_text)
                else:
                    st.error(f"Failed to get text feedback: {feedback_response.status_code} - {feedback_response.text}")

                # 2. Get follow-up questions
                with st.spinner("Generating follow-up questions..."):
                    followup_payload = {"user_answer": user_answer, "question_text": current_main_question}
                    followup_response = requests.post("http://localhost:8000/ai-follow-up", json=followup_payload)
                
                if followup_response.status_code == 200:
                    followups_data = followup_response.json().get("follow_up", [])
                    if followups_data: # Ensure it's a list and not empty
                        st.session_state.followups.extend(f for f in followups_data if f.strip()) # Add non-empty followups
                else:
                    st.warning(f"Could not fetch follow-up questions (Status: {followup_response.status_code}). Proceeding without them.")

                st.session_state.memory.append({
                    "question": current_main_question, "response": user_answer, "type": "text",
                    "feedback": ai_feedback_text
                })
                
                st.session_state.active_interaction_type = "follow_up" # Move to follow-up phase
                st.session_state.current_follow_up_index = 0 if st.session_state.followups else -1
                st.rerun()
            else:
                st.warning("Please write an answer before submitting.")


# --- COMMON UI FOR DISPLAYING AND HANDLING FOLLOW-UP QUESTIONS (ONE AT A TIME) ---
if st.session_state.active_interaction_type == "follow_up" and \
   st.session_state.followups and \
   0 <= st.session_state.current_follow_up_index < len(st.session_state.followups):

    st.markdown("---")
    st.subheader("🤔 Follow-Up Question")
    
    fup_idx = st.session_state.current_follow_up_index
    current_fup_question = st.session_state.followups[fup_idx]
    
    st.markdown(f"**Follow-Up Q{fup_idx + 1} of {len(st.session_state.followups)}:** {current_fup_question}")
    
    fup_response_type_key = f"fup_response_type_{fup_idx}_{hash(current_fup_question)}"
    fup_response_type = st.radio(
        f"Response type for this follow-up:",
        ["Text Response", "Code Editor"],
        key=fup_response_type_key,
        horizontal=True
    )
    
    if fup_response_type == "Code Editor":
        fup_code_reply_key = f"fup_code_reply_{fup_idx}_{hash(current_fup_question)}"
        fup_code_reply = st.text_area(f"Your code answer for follow-up:", key=fup_code_reply_key, height=150)
        fup_submit_code_key = f"fup_btn_code_submit_{fup_idx}_{hash(current_fup_question)}"
        
        if st.button(f"Submit Code for Follow-Up", key=fup_submit_code_key):
            if fup_code_reply.strip():
                ai_feedback_text = "Could not get feedback."
                with st.spinner("Processing your follow-up code..."):
                    # Re-use evaluate-code-ai; it gives feedback and can be prompted for more follow-ups if needed
                    # For now, its primary role here is feedback on the follow-up's code.
                    ai_feedback_res = requests.post(
                        "http://localhost:8000/evaluate-code-ai",
                        json={"user_code": fup_code_reply, "question": current_fup_question}
                    )
                if ai_feedback_res.status_code == 200:
                    ai_data = ai_feedback_res.json()
                    ai_feedback_text = ai_data.get("feedback_text", "Could not get feedback on follow-up code.")
                    # Note: We are not currently generating follow-ups to follow-ups from this call.
                else:
                    st.error(f"Failed to get feedback on follow-up code: {ai_feedback_res.status_code}")
                
                st.markdown(f"**AI Feedback on Follow-up Code:**\n{ai_feedback_text}")
                st.session_state.answered_followups[fup_idx] = {
                    "question": current_fup_question, "response": fup_code_reply, 
                    "feedback": ai_feedback_text, "type": "code"
                }
                st.session_state.memory.append({
                    "question": current_fup_question, "response": fup_code_reply, 
                    "type": "code_followup", "feedback": ai_feedback_text
                })
                
                st.session_state.current_follow_up_index += 1 # Move to next follow-up
                st.rerun()
            else:
                st.warning("Please enter your code for the follow-up.")
    else: # Text response for follow-up
        fup_text_reply_key = f"fup_text_reply_{fup_idx}_{hash(current_fup_question)}"
        fup_text_reply = st.text_area(f"Your text answer for follow-up:", key=fup_text_reply_key)
        fup_submit_text_key = f"fup_btn_text_submit_{fup_idx}_{hash(current_fup_question)}"
        
        if st.button(f"Submit Answer for Follow-Up", key=fup_submit_text_key):
            if fup_text_reply.strip():
                ai_feedback_text = "Could not get feedback."
                with st.spinner("Evaluating your follow-up answer..."):
                    response = requests.post(
                        "http://localhost:8000/evaluate-text",
                        json={"user_answer": fup_text_reply, "question": current_fup_question}
                    )
                if response.status_code == 200:
                    ai_feedback_text = response.json().get("feedback", "Could not get feedback on follow-up answer.")
                else:
                    st.error(f"Failed to get feedback on follow-up answer: {response.status_code}")

                st.markdown(f"**AI Feedback on Follow-up Answer:**\n{ai_feedback_text}")
                st.session_state.answered_followups[fup_idx] = {
                    "question": current_fup_question, "response": fup_text_reply, 
                    "feedback": ai_feedback_text, "type": "text"
                }
                st.session_state.memory.append({
                    "question": current_fup_question, "response": fup_text_reply, 
                    "type": "text_followup", "feedback": ai_feedback_text
                })
                
                st.session_state.current_follow_up_index += 1 # Move to next follow-up
                st.rerun()
            else:
                st.warning("Please enter your answer for the follow-up.")

# --- Logic to advance to next JD question OR clear main question after all follow-ups ---
if st.session_state.active_interaction_type == "follow_up" and \
   st.session_state.current_follow_up_index >= len(st.session_state.followups):
    
    # This block is entered only ONCE after all followups for a question are done.
    st.success("All follow-ups for the current question are complete!") # Good for debugging
    print("DEBUG: All followups done. Deciding next step.")

    next_action_taken = False
    # If in JD mode, advance to the next JD question
    if st.session_state.current_jd_question_index != -1: # Currently in JD mode
        # print(f"DEBUG: In JD mode, current_jd_question_index = {st.session_state.current_jd_question_index}")
        temp_next_jd_idx = st.session_state.current_jd_question_index + 1 # Tentative next index
        
        if temp_next_jd_idx < len(st.session_state.jd_questions_list):
            # print(f"DEBUG: Advancing to next JD question, index {temp_next_jd_idx}")
            reset_for_new_main_question() # Clears followups, active_interaction_type
            st.session_state.current_jd_question_index = temp_next_jd_idx # Set the new index
            st.session_state.question = st.session_state.jd_questions_list[st.session_state.current_jd_question_index]
            st.session_state.active_interaction_type = "main_question" # Set for the new main question
            next_action_taken = True
        else: # All JD questions done
            # print("DEBUG: All JD questions done.")
            reset_for_new_main_question() # Clear out current question state
            st.session_state.current_jd_question_index = temp_next_jd_idx # Mark as past the end
            st.session_state.question = None # Explicitly no question
            st.session_state.active_interaction_type = None
            # st.balloons() # Optional: celebrate
            next_action_taken = True
    else: # Standard mode, just clear the current question state
        # print("DEBUG: Standard mode, followups done. Clearing question.")
        reset_for_new_main_question()
        st.session_state.question = None
        st.session_state.active_interaction_type = None
        next_action_taken = True

    if next_action_taken:
        # print("DEBUG: Rerunning after advancing/clearing question.")
        st.rerun()


# --- Display Previously Answered Follow-ups (if any) ---
if st.session_state.answered_followups:
    st.markdown("---")
    with st.expander("View Answered Follow-Up Questions", expanded=False):
        for idx, f_data in st.session_state.answered_followups.items():
            st.markdown(f"**Q{int(idx)+1}:** {f_data['question']}")
            st.markdown(f"Your Answer ({f_data['type']}):")
            st.code(f_data['response'], language=f_data['type'] if f_data['type'] == 'code' else 'text')
            st.markdown(f"**Feedback:**\n{f_data['feedback']}")
            st.markdown("---")


# --- Final Interview Summary ---
# Conditions to show "Conclude Interview" button:
# 1. There must be some interaction in memory.
# 2. EITHER: No active main question AND all current follow-ups (if any) are answered.
# 3. OR: All JD questions are done.
can_conclude = False
if st.session_state.memory:
    all_current_followups_done = (
        not st.session_state.followups or # No followups to begin with
        st.session_state.current_follow_up_index >= len(st.session_state.followups)
    )
    # Condition 1: Standard mode, main question done, all its followups done
    condition1 = (
        st.session_state.current_jd_question_index == -1 and # Not in JD mode
        not st.session_state.question and # No active main question
        all_current_followups_done
    )
    # Condition 2: JD mode, all JD questions done, all followups for the last JD question done
    condition2 = (
        st.session_state.current_jd_question_index != -1 and
        st.session_state.current_jd_question_index >= len(st.session_state.jd_questions_list) and
        all_current_followups_done
    )
    if condition1 or condition2:
        can_conclude = True

if can_conclude:
    st.markdown("---")
    st.header("🏁 Interview Progress & Conclusion")
    total_interactions = len(st.session_state.memory)
    # Simple progress, can be made more sophisticated
    st.progress(min(1.0, total_interactions / 5)) # Assuming ~5 good interactions make a session
    st.write(f"You've completed {total_interactions} interaction(s) (main questions and follow-ups).")
    
    if st.button("Conclude Interview & Get Final Summary", key="conclude_interview_btn"):
        with st.spinner("Generating final assessment..."):
            summary_prompt_parts = ["Summarize the candidate's interview performance based on these interactions. Provide an overall assessment, specific strengths, areas for improvement, and a concluding thought (e.g., leaning towards hire/no-hire with justification).\n"]
            for i, entry in enumerate(st.session_state.memory):
                q_type_label = entry.get('type', 'N/A').replace('_', ' ').title()
                summary_prompt_parts.append(f"\nInteraction {i+1}:")
                summary_prompt_parts.append(f"  Type: {q_type_label}")
                summary_prompt_parts.append(f"  Question: {entry['question']}")
                # Truncate response in prompt to manage token limits if necessary
                summary_prompt_parts.append(f"  Candidate's Answer (first 200 chars): {entry['response'][:200]}...")
                if 'results' in entry and entry['results']:
                    summary_prompt_parts.append(f"  Test Results: {entry['results']}")
                if 'feedback' in entry and entry['feedback'] and entry['feedback'] != "Could not get AI feedback.":
                     summary_prompt_parts.append(f"  AI Feedback (first 150 chars): {entry['feedback'][:150]}...")
            
            summary_prompt_for_llm = "\n".join(summary_prompt_parts)

            response = requests.post(
                "http://localhost:8000/evaluate-text", 
                json={"user_answer": summary_prompt_for_llm, "question": "Provide an overall interview summary based on the preceding interaction log."}
            )
            final_summary = response.json().get("feedback", "Could not generate final summary.")

            st.subheader("🏆 Final Interview Assessment")
            st.markdown(final_summary)
            
            # --- Download Button for Summary ---
            interview_text_report = f"# AI Interview Coach - Interview Summary\n\n## Overall Assessment:\n{final_summary}\n\n## Detailed Interaction Log:\n\n"
            for i, entry in enumerate(st.session_state.memory):
                q_type_label = entry.get('type', 'N/A').replace('_', ' ').title()
                interview_text_report += f"### Interaction {i+1}: {q_type_label}\n**Question:** {entry['question']}\n\n"
                interview_text_report += f"**Your Answer:**\n```\n{entry['response']}\n```\n\n"
                if 'results' in entry and entry['results']:
                    interview_text_report += f"**Test Results/Evaluation:** {entry['results']}\n\n"
                if 'feedback' in entry and entry['feedback'] and entry['feedback'] != "Could not get AI feedback.":
                    interview_text_report += f"**AI Feedback:**\n{entry['feedback']}\n\n"
                interview_text_report += "---\n\n"
            
            st.download_button(
                label="Download Interview Summary (Markdown)",
                data=interview_text_report,
                file_name="ai_interview_summary.md",
                mime="text/markdown",
                key="download_summary_btn"
            )
elif st.session_state.memory: # If there's memory but not ready to conclude
    st.sidebar.info("Continue with the current question or generate a new one to proceed.")


# --- Sidebar Instructions ---
with st.sidebar:
    st.header("📖 How to Use")
    st.markdown("""
    1.  **Choose an Interview Mode**:
        *   **Standard Practice**: Select topic & difficulty.
        *   **Job Description Mode**: Paste a JD.
    2.  **Generate Question(s)**.
    3.  **Respond**: Choose text or code.
    4.  **Submit**: Get AI feedback & code evaluation.
    5.  **Follow-Ups**: Answer AI's follow-up questions sequentially.
    6.  **Next Question/Conclude**:
        *   After follow-ups, the system might present the next JD question.
        *   Or, you can generate a new standard question.
        *   Once a session is complete (e.g., all JD questions answered, or you've had enough practice), the "Conclude Interview" button will appear.
    """)
    st.header("💡 About")
    st.write("This AI Interview Coach simulates interview scenarios, evaluates code against test cases (for standard DSA/SQL), and provides AI-driven feedback to help you ace your technical interviews!")

    if st.button("Clear Session & Restart", key="clear_session_btn"):
        for key in default_states.keys(): # Clears all defined session states
            st.session_state[key] = default_states[key]
        # Explicitly clear a few more if they were dynamically added or for safety
        keys_to_clear = list(st.session_state.keys())
        for key in keys_to_clear:
            if key not in ['query_params']: # Don't clear Streamlit internal states if any
                 del st.session_state[key]
        st.rerun()