import streamlit as st
import requests
import json

# ==========================
# Page Configuration & Style
# ==========================
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Global CSS (lightweight, no external deps) ---
CUSTOM_CSS = """
<style>
/* Hide default Streamlit chrome we do not need */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* App container spacing */
.block-container {padding-top: 1.5rem; padding-bottom: 3rem;}

/* Gradient title */
.app-title {
  font-weight: 800;
  font-size: 2.2rem;
  line-height: 1.1;
  background: linear-gradient(90deg, #6b8cff, #8a63d2 50%, #00c2ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.subtitle { color: rgba(49,51,63,.7); font-size: .95rem; margin-top: .25rem; }

/* Card component */
.card { 
  background: var(--background-color, #ffffff);
  border: 1px solid rgba(0,0,0,.06);
  border-radius: 16px; 
  padding: 1rem 1.1rem; 
  box-shadow: 0 2px 18px rgba(0,0,0,.06);
}
.card h3, .card h4 { margin: 0 0 .4rem 0; }
.card-muted { color: rgba(49,51,63,.7); }

/* Badge chips */
.badges { display:flex; gap:.5rem; flex-wrap: wrap; margin:.25rem 0 .5rem; }
.badge { font-size: .78rem; padding: .25rem .6rem; border-radius: 999px; border:1px solid rgba(0,0,0,.08); background: rgba(0,0,0,.04); }
.badge.primary { background: #eef2ff; color:#3b5bfd; border-color:#dfe5ff; }
.badge.success { background: #eafff3; color:#18a957; border-color:#c8ffd9; }
.badge.warn { background: #fff7e6; color:#b26b00; border-color:#ffe7b3; }

/* Pretty blockquote for questions */
.qblock { border-left: 4px solid #6b8cff; padding: .6rem .9rem; background: rgba(107,140,255,.06); border-radius: 8px; }

/* Make radios look like segmented controls */
[data-baseweb="radio"] label { 
  border: 1px solid rgba(0,0,0,.08); 
  padding: .35rem .75rem; 
  border-radius: 999px; 
  margin-right: .5rem; 
}

/* Buttons full width when desired */
.stButton>button.full { width: 100%; border-radius: 12px; padding:.7rem 1rem; font-weight:600; }
.stButton>button.primary { background: #3b5bfd; color: white; border: 0; }
.stButton>button.neutral { background: #f5f6ff; color: #2d2f3a; border: 1px solid #e6e6f2; }
.stButton>button.danger { background: #ffebee; color: #b00020; border: 1px solid #ffcdd2; }

/* Progress helper text */
.progress-note { font-size: .9rem; color: rgba(49,51,63,.7); }

/* Code block tweak */
pre, code { border-radius: 10px !important; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================
# Session State Bootstrap
# ==========================
default_states = {
    "memory": [],
    "followups": [],
    "answered_followups": {},
    "current_question_id": 1,
    "question": None,
    "test_cases": None,
    "jd_questions_list": [],
    "current_jd_question_index": -1,
    "active_interaction_type": None,
    "current_follow_up_index": -1
}
for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Helper state resets

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

# ==========================
# Header & KPIs
# ==========================
col_a, col_b = st.columns([3, 2])
with col_a:
    st.markdown('<div class="app-title">🚀 AI Interview Coach</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Practice smarter. Get structured feedback. Track your progress.</div>', unsafe_allow_html=True)
with col_b:
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            total_interactions = len(st.session_state.memory)
            st.metric("Interactions", total_interactions)
        with c2:
            cur_mode = st.session_state.get("standard_topic_selector", "Not set")
            st.metric("Mode", cur_mode)
        with c3:
            cur_diff = st.session_state.get("standard_difficulty_selector", "Not set")
            st.metric("Difficulty", cur_diff)

st.write("")

# ==========================
# Tabs
# ==========================
tab1, tab2 = st.tabs(["🎯 Standard Practice", "📄 JD Mode"])

# --------------------------
# TAB 1: Standard Interview
# --------------------------
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🎯 Standard Interview Practice</h3>", unsafe_allow_html=True)
    st.caption("Pick a topic and difficulty, then generate a realistic interview prompt.")

    left, right = st.columns(2)
    with left:
        mode = st.selectbox(
            "Select Interview Topic",
            [
                "Data Science & ML",
                "Software Engineering & System Design",
                "Data Structures & Algorithms",
                "Database & SQL Queries",
                "Networking & OS",
                "Behavioral & HR",
                "Cloud Computing & DevOps",
            ],
            key="standard_topic_selector",
        )
    with right:
        difficulty = st.selectbox(
            "Select Difficulty Level",
            ["Easy", "Medium", "Hard", "Expert"],
            key="standard_difficulty_selector",
        )

    st.markdown('<div class="badges">' \
                f'<span class="badge primary">{mode}</span>' \
                f'<span class="badge success">{difficulty}</span>' \
                '</div>', unsafe_allow_html=True)

    if st.button("✨ Generate Standard Question", key="gen_std_q_btn", type="primary"):
        reset_for_new_main_question()
        reset_jd_mode_state()
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
                        "Data Structures & Algorithms": 1,
                        "Database & SQL Queries": 2,
                        "Software Engineering & System Design": 3,
                        "Data Science & ML": 4,
                        "Networking & OS": 5,
                        "Behavioral & HR": 6,
                        "Cloud Computing & DevOps": 7,
                    }
                    st.session_state.current_question_id = question_id_map.get(mode, 0)

                    if mode in ["Data Structures & Algorithms", "Database & SQL Queries"] and st.session_state.current_question_id != 0:
                        try:
                            with st.spinner("Fetching test cases..."):
                                test_cases_res = requests.get(
                                    f"http://localhost:8000/get-test-cases/{st.session_state.current_question_id}"
                                )
                            if test_cases_res.status_code == 200:
                                st.session_state.test_cases = test_cases_res.json()
                            else:
                                st.warning(
                                    f"Could not fetch test cases (Status: {test_cases_res.status_code})."
                                )
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
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# TAB 2: Job Description Mode
# --------------------------
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>📄 Job Description Mode</h3>", unsafe_allow_html=True)
    st.caption("Paste a JD to auto-generate focused questions.")

    jd_text = st.text_area("Paste Job Description here", height=220, key="jd_input_area")

    cjd1, cjd2 = st.columns([1, 3])
    with cjd1:
        if st.button("🧩 Generate Questions from JD", key="gen_jd_q_btn"):
            if jd_text.strip():
                reset_for_new_main_question()
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
                            st.warning("Could not generate questions from this JD. Try a different JD.")
                        st.rerun()
                    else:
                        st.error(f"Error generating JD-based questions: {res.status_code} - {res.text}")
                except requests.exceptions.RequestException as e_req_jd:
                    st.error(f"Network error: {e_req_jd}")
                except Exception as e_gen_jd:
                    st.error(f"Unexpected error during JD question generation: {e_gen_jd}")
            else:
                st.warning("Please paste a job description first.")

    if st.session_state.jd_questions_list and st.session_state.current_jd_question_index != -1:
        idx = st.session_state.current_jd_question_index
        if idx < len(st.session_state.jd_questions_list):
            st.session_state.question = st.session_state.jd_questions_list[idx]
            st.markdown(f"<div class='badges'><span class='badge warn'>Currently on JD Question {idx + 1} of {len(st.session_state.jd_questions_list)}</span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================
# COMMON: Display Main Question & Handle Answer
# =============================================
if st.session_state.question and st.session_state.active_interaction_type == "main_question":
    current_main_question = st.session_state.question
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>📝 Interview Question</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='qblock'>{current_main_question}</div>", unsafe_allow_html=True)
    st.write("")

    main_input_type_key = f"main_input_type_{hash(current_main_question)}"
    input_type = st.radio(
        "Choose your response type",
        ["Text Response", "Code Editor"],
        key=main_input_type_key,
        horizontal=True,
    )

    if input_type == "Code Editor":
        st.subheader("💻 Your Code Solution")
        if st.session_state.test_cases and st.session_state.test_cases.get("status") == "success":
            test_case_data = st.session_state.test_cases
            with st.expander("View Test Cases"):
                st.write(f"**Function Name (if applicable)**: `{test_case_data.get('function_name')}`")
                st.write("Your code might be tested with inputs like these:")
                for case in test_case_data.get("test_cases", []):
                    st.code(f"Test {case.get('test_number')}: Input -> {json.dumps(case.get('input'))}")
        elif st.session_state.current_jd_question_index != -1:
            st.info("For JD-based coding questions, focus on clarity, efficiency, and correctness. No fixed test cases here.")

        main_code_area_key = f"main_code_area_{hash(current_main_question)}"
        user_code = st.text_area("Write your Python code here", height=300, key=main_code_area_key)

        main_submit_code_key = f"main_submit_code_btn_{hash(current_main_question)}"
        if st.button("▶️ Submit Code Solution", key=main_submit_code_key):
            if user_code.strip():
                eval_results_display = None
                ai_feedback_text = "Could not get AI feedback."
                q_id_for_eval = st.session_state.current_question_id if st.session_state.current_jd_question_index == -1 else 0

                with st.spinner("Running your code against test cases..."):
                    eval_payload = {"language": "python", "user_code": user_code, "question_id": q_id_for_eval}
                    eval_response = requests.post("http://localhost:8000/evaluate-code", json=eval_payload)

                if eval_response.status_code == 200:
                    result = eval_response.json()
                    st.subheader("⚙️ Code Test Results")
                    if result.get("status") == "success":
                        passed = result.get('passed', 0)
                        total = result.get('total', 0)
                        percentage = result.get('passed_percentage', 0)
                        if total > 0 and passed == total:
                            st.success(f"{passed}/{total} Tests Passed ({percentage:.1f}%)")
                        else:
                            st.info(f"{passed}/{total} Tests Passed ({percentage:.1f}%)")
                        eval_results_display = f"{passed}/{total} Tests Passed ({percentage:.1f}%)"
                        with st.expander("Detailed Test Results", expanded=not (passed == total and total > 0)):
                            for test in result.get("results", []):
                                test_icon = "✅" if test.get("passed") else "❌"
                                color = "green" if test.get("passed") else "red"
                                st.markdown(
                                    f"<span style='color:{color};'>{test_icon} **Test {test.get('test_case')}**: Input: `{test.get('input')}`</span>",
                                    unsafe_allow_html=True,
                                )
                                if not test.get("passed"):
                                    st.markdown(f"    Expected: `{test.get('expected')}`, Got: `{test.get('actual')}`")
                                    if "error" in test and test.get("error"):
                                        st.error(f"    Error: {test.get('error')}")
                    elif "error" in result:
                        st.error(f"Code Execution Error: {result.get('error')}")
                        if "details" in result and result.get("details"):
                            st.code(result.get("details"), language="text")
                        eval_results_display = f"Execution Error: {result.get('error')}"
                    else:
                        st.json(result)
                        eval_results_display = "Evaluation response in unknown format."
                else:
                    st.error(f"Error evaluating code: {eval_response.status_code} - {eval_response.text}")
                    eval_results_display = f"Evaluation API Error {eval_response.status_code}"

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
                    "question": current_main_question,
                    "response": user_code,
                    "type": "code",
                    "results": eval_results_display,
                    "feedback": ai_feedback_text,
                })

                st.session_state.active_interaction_type = "follow_up"
                st.session_state.current_follow_up_index = 0 if st.session_state.followups else -1
                st.rerun()
            else:
                st.warning("Please write some code before submitting.")

    else:  # Text Response
        st.subheader("🗣️ Your Text Answer")
        main_text_area_key = f"main_text_area_{hash(current_main_question)}"
        user_answer = st.text_area("Write your answer here", key=main_text_area_key)

        main_submit_text_key = f"main_submit_text_btn_{hash(current_main_question)}"
        if st.button("▶️ Submit Text Answer", key=main_submit_text_key):
            if user_answer.strip():
                ai_feedback_text = "Could not get AI feedback."
                with st.spinner("Getting AI feedback on your answer..."):
                    feedback_payload = {"user_answer": user_answer, "question": current_main_question}
                    feedback_response = requests.post("http://localhost:8000/evaluate-text", json=feedback_payload)

                if feedback_response.status_code == 200:
                    ai_feedback_text = feedback_response.json().get("feedback", "Could not retrieve AI feedback.")
                    st.subheader("💡 AI Feedback on Your Answer")
                    st.markdown(ai_feedback_text)
                else:
                    st.error(f"Failed to get text feedback: {feedback_response.status_code} - {feedback_response.text}")

                with st.spinner("Generating follow-up questions..."):
                    followup_payload = {"user_answer": user_answer, "question_text": current_main_question}
                    followup_response = requests.post("http://localhost:8000/ai-follow-up", json=followup_payload)

                if followup_response.status_code == 200:
                    followups_data = followup_response.json().get("follow_up", [])
                    if followups_data:
                        st.session_state.followups.extend(f for f in followups_data if f.strip())
                else:
                    st.warning(
                        f"Could not fetch follow-up questions (Status: {followup_response.status_code}). Proceeding without them."
                    )

                st.session_state.memory.append({
                    "question": current_main_question,
                    "response": user_answer,
                    "type": "text",
                    "feedback": ai_feedback_text,
                })

                st.session_state.active_interaction_type = "follow_up"
                st.session_state.current_follow_up_index = 0 if st.session_state.followups else -1
                st.rerun()
            else:
                st.warning("Please write an answer before submitting.")

    st.markdown('</div>', unsafe_allow_html=True)

# =============================================
# COMMON: Follow-up Flow
# =============================================
if (
    st.session_state.active_interaction_type == "follow_up"
    and st.session_state.followups
    and 0 <= st.session_state.current_follow_up_index < len(st.session_state.followups)
):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🤔 Follow-Up Question</h3>", unsafe_allow_html=True)

    fup_idx = st.session_state.current_follow_up_index
    current_fup_question = st.session_state.followups[fup_idx]

    st.markdown(f"**Follow-Up {fup_idx + 1} of {len(st.session_state.followups)}**")
    st.markdown(f"<div class='qblock'>{current_fup_question}</div>", unsafe_allow_html=True)

    fup_response_type_key = f"fup_response_type_{fup_idx}_{hash(current_fup_question)}"
    fup_response_type = st.radio(
        "Response type for this follow-up",
        ["Text Response", "Code Editor"],
        key=fup_response_type_key,
        horizontal=True,
    )

    if fup_response_type == "Code Editor":
        fup_code_reply_key = f"fup_code_reply_{fup_idx}_{hash(current_fup_question)}"
        fup_code_reply = st.text_area("Your code answer for follow-up", key=fup_code_reply_key, height=160)
        fup_submit_code_key = f"fup_btn_code_submit_{fup_idx}_{hash(current_fup_question)}"

        if st.button("✅ Submit Code for Follow-Up", key=fup_submit_code_key):
            if fup_code_reply.strip():
                ai_feedback_text = "Could not get feedback."
                with st.spinner("Processing your follow-up code..."):
                    ai_feedback_res = requests.post(
                        "http://localhost:8000/evaluate-code-ai",
                        json={"user_code": fup_code_reply, "question": current_fup_question},
                    )
                if ai_feedback_res.status_code == 200:
                    ai_data = ai_feedback_res.json()
                    ai_feedback_text = ai_data.get("feedback_text", "Could not get feedback on follow-up code.")
                else:
                    st.error(f"Failed to get feedback on follow-up code: {ai_feedback_res.status_code}")

                st.markdown(f"**AI Feedback on Follow-up Code:**\n{ai_feedback_text}")
                st.session_state.answered_followups[fup_idx] = {
                    "question": current_fup_question,
                    "response": fup_code_reply,
                    "feedback": ai_feedback_text,
                    "type": "code",
                }
                st.session_state.memory.append({
                    "question": current_fup_question,
                    "response": fup_code_reply,
                    "type": "code_followup",
                    "feedback": ai_feedback_text,
                })

                st.session_state.current_follow_up_index += 1
                st.rerun()
            else:
                st.warning("Please enter your code for the follow-up.")
    else:
        fup_text_reply_key = f"fup_text_reply_{fup_idx}_{hash(current_fup_question)}"
        fup_text_reply = st.text_area("Your text answer for follow-up", key=fup_text_reply_key)
        fup_submit_text_key = f"fup_btn_text_submit_{fup_idx}_{hash(current_fup_question)}"

        if st.button("✅ Submit Answer for Follow-Up", key=fup_submit_text_key):
            if fup_text_reply.strip():
                ai_feedback_text = "Could not get feedback."
                with st.spinner("Evaluating your follow-up answer..."):
                    response = requests.post(
                        "http://localhost:8000/evaluate-text",
                        json={"user_answer": fup_text_reply, "question": current_fup_question},
                    )
                if response.status_code == 200:
                    ai_feedback_text = response.json().get(
                        "feedback", "Could not get feedback on follow-up answer."
                    )
                else:
                    st.error(f"Failed to get feedback on follow-up answer: {response.status_code}")

                st.markdown(f"**AI Feedback on Follow-up Answer:**\n{ai_feedback_text}")
                st.session_state.answered_followups[fup_idx] = {
                    "question": current_fup_question,
                    "response": fup_text_reply,
                    "feedback": ai_feedback_text,
                    "type": "text",
                }
                st.session_state.memory.append({
                    "question": current_fup_question,
                    "response": fup_text_reply,
                    "type": "text_followup",
                    "feedback": ai_feedback_text,
                })

                st.session_state.current_follow_up_index += 1
                st.rerun()
            else:
                st.warning("Please enter your answer for the follow-up.")

    st.markdown('</div>', unsafe_allow_html=True)

# =============================================
# Advance or Clear after Follow-ups
# =============================================
if (
    st.session_state.active_interaction_type == "follow_up"
    and st.session_state.current_follow_up_index >= len(st.session_state.followups)
):
    st.success("All follow-ups for the current question are complete!")
    next_action_taken = False

    if st.session_state.current_jd_question_index != -1:
        temp_next_jd_idx = st.session_state.current_jd_question_index + 1
        if temp_next_jd_idx < len(st.session_state.jd_questions_list):
            reset_for_new_main_question()
            st.session_state.current_jd_question_index = temp_next_jd_idx
            st.session_state.question = st.session_state.jd_questions_list[st.session_state.current_jd_question_index]
            st.session_state.active_interaction_type = "main_question"
            next_action_taken = True
        else:
            reset_for_new_main_question()
            st.session_state.current_jd_question_index = temp_next_jd_idx
            st.session_state.question = None
            st.session_state.active_interaction_type = None
            next_action_taken = True
    else:
        reset_for_new_main_question()
        st.session_state.question = None
        st.session_state.active_interaction_type = None
        next_action_taken = True

    if next_action_taken:
        st.rerun()

# =============================================
# Answered Follow-ups Archive
# =============================================
if st.session_state.answered_followups:
    with st.expander("View Answered Follow-Up Questions", expanded=False):
        for idx, f_data in st.session_state.answered_followups.items():
            st.markdown(f"**Q{int(idx)+1}:** {f_data['question']}")
            st.markdown("Your Answer:")
            st.code(f_data['response'], language=f_data['type'] if f_data['type'] == 'code' else 'text')
            st.markdown(f"**Feedback:**\n{f_data['feedback']}")
            st.markdown("---")

# =============================================
# Final Interview Summary
# =============================================
can_conclude = False
if st.session_state.memory:
    all_current_followups_done = (
        not st.session_state.followups or
        st.session_state.current_follow_up_index >= len(st.session_state.followups)
    )
    condition1 = (
        st.session_state.current_jd_question_index == -1 and
        not st.session_state.question and
        all_current_followups_done
    )
    condition2 = (
        st.session_state.current_jd_question_index != -1 and
        st.session_state.current_jd_question_index >= len(st.session_state.jd_questions_list) and
        all_current_followups_done
    )
    if condition1 or condition2:
        can_conclude = True

if can_conclude:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🏁 Interview Progress & Conclusion</h3>", unsafe_allow_html=True)
    total_interactions = len(st.session_state.memory)
    st.progress(min(1.0, total_interactions / 5))
    st.markdown(
        f"<div class='progress-note'>You have completed {total_interactions} interaction(s). Click below to generate a final summary.</div>",
        unsafe_allow_html=True,
    )

    if st.button("🏆 Conclude Interview & Get Final Summary", key="conclude_interview_btn", type="primary"):
        with st.spinner("Generating final assessment..."):
            summary_prompt_parts = [
                "Summarize the candidate's interview performance based on these interactions. Provide an overall assessment, specific strengths, areas for improvement, and a concluding thought (e.g., leaning towards hire/no-hire with justification).\n"
            ]
            for i, entry in enumerate(st.session_state.memory):
                q_type_label = entry.get('type', 'N/A').replace('_', ' ').title()
                summary_prompt_parts.append(f"\nInteraction {i+1}:")
                summary_prompt_parts.append(f"  Type: {q_type_label}")
                summary_prompt_parts.append(f"  Question: {entry['question']}")
                summary_prompt_parts.append(f"  Candidate's Answer (first 200 chars): {entry['response'][:200]}...")
                if 'results' in entry and entry['results']:
                    summary_prompt_parts.append(f"  Test Results: {entry['results']}")
                if 'feedback' in entry and entry['feedback'] and entry['feedback'] != "Could not get AI feedback.":
                    summary_prompt_parts.append(f"  AI Feedback (first 150 chars): {entry['feedback'][:150]}...")

            summary_prompt_for_llm = "\n".join(summary_prompt_parts)

            response = requests.post(
                "http://localhost:8000/evaluate-text",
                json={
                    "user_answer": summary_prompt_for_llm,
                    "question": "Provide an overall interview summary based on the preceding interaction log.",
                },
            )
            final_summary = response.json().get("feedback", "Could not generate final summary.")

            st.subheader("🏆 Final Interview Assessment")
            st.markdown(final_summary)

            interview_text_report = (
                f"# AI Interview Coach - Interview Summary\n\n## Overall Assessment:\n{final_summary}\n\n## Detailed Interaction Log:\n\n"
            )
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
                label="⬇️ Download Interview Summary (Markdown)",
                data=interview_text_report,
                file_name="ai_interview_summary.md",
                mime="text/markdown",
                key="download_summary_btn",
            )
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.memory:
    st.sidebar.info("Continue with the current question or generate a new one to proceed.")

# ==========================
# Sidebar
# ==========================
with st.sidebar:
    st.header("📖 How to Use")
    st.markdown(
        """
        1. **Choose a Mode**
           * **Standard Practice** for topic based questions.
           * **JD Mode** to generate role specific questions.
        2. **Generate Question(s)**.
        3. **Respond** using text or code.
        4. **Submit** to see AI feedback and test results.
        5. **Follow-ups** are presented in sequence.
        6. **Conclude** to get a summary when done.
        """
    )

    st.header("⚙️ Actions")
    if st.button("♻️ Clear Session & Restart", key="clear_session_btn"):
        for key in default_states.keys():
            st.session_state[key] = default_states[key]
        keys_to_clear = list(st.session_state.keys())
        for key in keys_to_clear:
            if key not in ["query_params"]:
                try:
                    del st.session_state[key]
                except Exception:
                    pass
        st.rerun()

    st.header("💡 About")
    st.write(
        "This coach simulates interviews, evaluates code for DSA or SQL when available, and gives AI powered feedback so you can iterate fast."
    )
