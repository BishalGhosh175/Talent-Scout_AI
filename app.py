# app.py - The Final, Polished, and Visually Correct Version

import streamlit as st
import google.generativeai as genai
import json
import re
import fitz  # PyMuPDF

# --- Configuration and Initialization ---

st.set_page_config(page_title="TalentScout Assistant", page_icon="🤖", layout="centered")
api_key=""
try:
    genai.configure(api_key)
except (KeyError, AttributeError):
    st.error("🚨 **Error:** Gemini API Key not found. Please create a `.streamlit/secrets.toml` file.", icon="🔑")
    st.stop()

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    generation_config = genai.types.GenerationConfig(temperature=0.4)
except Exception as e:
    st.error("🚨 **Error:** Failed to initialize the Generative Model.", icon="🔥")
    st.exception(e)
    st.stop()

# --- UI Styling ---
def load_css():
    st.markdown("""
    <style>
        .stApp { background-color: #F0F2F6; }
        [data-testid="stAppViewContainer"] > .main > div {
            padding: 2rem; background-color: white; border-radius: 25px;
            box-shadow: 0 8px 16px 0 rgba(0,0,0,0.1);
        }
        
        /* FIX: Specifically target the h1 title element to ensure it's dark */
        h1 {
            color: #31333F !important; /* A dark, professional color for the title */
        }

        .stChatMessage {
            border-radius: 20px; padding: 1rem 1.5rem; margin-bottom: 1rem;
            box-shadow: 0 4px 6px 0 rgba(0,0,0,0.07); border: none;
            background-color: #E9E9EB;
        }
        
        /* Specific selector for chat text, leaving other components alone */
        div[data-testid="stChatMessage"] p, 
        div[data-testid="stChatMessage"] li {
            color: black !important;
        }
        
        .stButton>button {
            width: 310px; border-radius: 20px; border: 1px solid #0A66C2;
            color: #0A66C2; background-color: white; transition: all 0.2s ease;
            padding: 0.75rem 0; font-weight: 600;
        }
        .stButton>button:hover { border-color: #004182; color: white; background-color: #0A66C2; }
    </style>
    """, unsafe_allow_html=True)

# --- App Constants & State ---
JOB_ROLES = [ "AI/ML Intern", "Data Scientist", "Software Engineer (Backend)", "Software Engineer (Frontend)", "DevOps Engineer", "Full-Stack Developer" ]
if "stage" not in st.session_state: st.session_state.stage = "GREETING"
if "messages" not in st.session_state: st.session_state.messages = []
if "candidate_data" not in st.session_state: st.session_state.candidate_data = {}
if "manual_entry_fields" not in st.session_state:
    st.session_state.manual_entry_fields = [ "Full Name", "Email Address", "Years of Experience", "Current Location", "Tech Stack" ]
if "current_field_index" not in st.session_state: st.session_state.current_field_index = 0
if "tech_questions" not in st.session_state: st.session_state.tech_questions = []
if "current_question_index" not in st.session_state: st.session_state.current_question_index = 0

# --- Helper Functions ---
def display_chat():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})
def format_list_for_display(data):
    if isinstance(data, list): return ', '.join(map(str, data)) if data else "N/A"
    return str(data) if data else "N/A"
def extract_json_from_string(text):
    match = re.search(r'\{.*\}', text, re.DOTALL); return json.loads(match.group()) if match else None
def extract_text_from_file(file):
    if file.name.endswith('.pdf'):
        with fitz.open(stream=file.read(), filetype="pdf") as doc: return "".join(p.get_text() for p in doc)
    elif file.name.endswith('.txt'):
        return file.getvalue().decode("utf-8")
    return None
def parse_resume_with_llm(resume_text):
    prompt = f"""Analyze this resume and extract info into a JSON object with keys: "full_name", "email", "years_of_experience", "current_location", "tech_stack". The tech_stack value must be a list of strings. Output ONLY the JSON object. Text: --- {resume_text} ---"""
    try:
        response = model.generate_content(prompt, generation_config=generation_config); return extract_json_from_string(response.text)
    except Exception: return None

# --- Main App Flow ---

load_css()
st.title("TalentScout Hiring Assistant")
display_chat()

if st.session_state.stage == "GREETING":
    if not st.session_state.messages: add_message("assistant", "Hello! I'm Scout. To streamline your application, would you like to upload a resume?")
    st.session_state.stage = "AWAITING_RESUME_DECISION"; st.rerun()
if st.session_state.stage == "AWAITING_RESUME_DECISION":
    col1, col2 = st.columns(2)
    if col1.button("✅ Yes, upload resume"): add_message("user", "Yes"); add_message("assistant", "Great! Please use the uploader below."); st.session_state.stage = "AWAITING_UPLOAD"; st.rerun()
    if col2.button("❌ No, enter manually"): add_message("user", "No"); add_message("assistant", "Of course."); st.session_state.stage = "MANUAL_GATHERING"; st.rerun()
if st.session_state.stage == "AWAITING_UPLOAD":
    uploaded_file = st.file_uploader("Upload your resume (PDF or TXT only)", type=['pdf', 'txt'], label_visibility="collapsed")
    if uploaded_file:
        with st.spinner("Analyzing resume..."):
            text = extract_text_from_file(uploaded_file)
            data = parse_resume_with_llm(text) if text else None
            if data:
                st.session_state.candidate_data = data
                msg = f"Thanks! I've extracted the following information. Please verify if it's correct:\n*   **Name:** {data.get('full_name', 'N/A')}\n*   **Email:** {data.get('email', 'N/A')}\n*   **Tech Stack:** {format_list_for_display(data.get('tech_stack'))}"
                add_message("assistant", msg); st.session_state.stage = "AWAITING_VERIFICATION_RESPONSE"; st.rerun()
            else: add_message("assistant", "Sorry, I had trouble reading that resume. Please try another file or choose to enter the details manually.")
if st.session_state.stage == "AWAITING_VERIFICATION_RESPONSE":
    col1, col2 = st.columns(2)
    if col1.button("👍 Yes, it's correct"): add_message("user", "Yes, that's correct."); st.session_state.stage = "AWAITING_ROLE_SELECTION"; st.rerun()
    if col2.button("👎 No, something's wrong"): add_message("user", "No, something is wrong."); add_message("assistant", "No problem, let's get the correct info."); st.session_state.stage = "MANUAL_GATHERING"; st.rerun()
if st.session_state.stage == "MANUAL_GATHERING":
    idx = st.session_state.current_field_index
    if idx < len(st.session_state.manual_entry_fields):
        if not st.session_state.messages or st.session_state.messages[-1]["role"] != "assistant":
            field_name = st.session_state.manual_entry_fields[idx]; question = f"Let's start with your **{field_name}**." if idx == 0 else f"Got it. What is your **{field_name}**?"; add_message("assistant", question)
        if prompt := st.chat_input(f"Your {st.session_state.manual_entry_fields[idx]}..."):
            add_message("user", prompt); field_key = st.session_state.manual_entry_fields[idx].lower().replace(" ", "_"); st.session_state.candidate_data[field_key] = prompt; st.session_state.current_field_index += 1; st.rerun()
    else: st.session_state.stage = "AWAITING_ROLE_SELECTION"; st.rerun()
if st.session_state.stage == "AWAITING_ROLE_SELECTION":
    if st.session_state.messages[-1]["role"] == "user": add_message("assistant", "Excellent. Now, please select the role you are applying for.")
    with st.form("role_selection_form"):
        selected_role = st.selectbox("Choose your role:", options=JOB_ROLES, index=None, placeholder="Select a role...")
        if st.form_submit_button("Confirm Role") and selected_role:
            add_message("user", f"Role: **{selected_role}**"); st.session_state.candidate_data['job_role'] = selected_role; st.session_state.stage = "GENERATING_QUESTIONS"; st.rerun()
if st.session_state.stage == "GENERATING_QUESTIONS":
    with st.chat_message("assistant"):
        with st.spinner("Perfect. Analyzing your skills and preparing relevant questions..."):
            tech_stack = format_list_for_display(st.session_state.candidate_data.get("tech_stack", "")); job_role = st.session_state.candidate_data.get("job_role", "general software role")
            prompt = f"""You are an expert interviewer for a "{job_role}". The candidate's skills are: "{tech_stack}".
            Based on the most relevant skills, generate a JSON object with a "questions" key.
            The value must be an array of 3 to 5 foundational screening questions. Each question should be a single, direct sentence.
            Example: {{"questions": ["What is the purpose of a constructor in a class?", "Explain what a foreign key is in a SQL database."]}}
            Output ONLY the raw JSON object."""
            try:
                response = model.generate_content(prompt, generation_config=generation_config)
                q_data = extract_json_from_string(response.text)
                if q_data and "questions" in q_data and q_data["questions"]:
                    st.session_state.tech_questions = q_data["questions"]; st.session_state.current_question_index = 0; st.session_state.stage = "DISPLAY_QUESTION"
                else: raise ValueError("Failed to get valid questions.")
            except Exception:
                add_message("assistant", "I had an issue preparing questions. A recruiter will follow up directly."); st.session_state.stage = "CONCLUDED"
    st.rerun()
if st.session_state.stage == "DISPLAY_QUESTION":
    q_index = st.session_state.current_question_index; question_list = st.session_state.tech_questions
    if q_index < len(question_list):
        intro = "Great, I have a few questions for you. Let's begin." if q_index == 0 else ""
        question_text = f"{intro}\n\n**Question {q_index + 1} of {len(question_list)}:**\n\n{question_list[q_index]}"
        add_message("assistant", question_text); st.session_state.stage = "ASKING_QUESTIONS"
    else: st.session_state.stage = "CONCLUDED"
    st.rerun()
if st.session_state.stage == "ASKING_QUESTIONS":
    with st.form("answer_form", clear_on_submit=True):
        answer = st.text_area("Your Answer:", height=150, placeholder="Type your detailed answer here...")
        submitted = st.form_submit_button("Send Answer")
        if submitted and answer:
            add_message("user", answer)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your answer..."):
                    q_index = st.session_state.current_question_index; question = st.session_state.tech_questions[q_index]
                    prompt = f"""As a concise interviewer, evaluate this answer. Question: "{question}" Answer: "{answer}". Provide a one-sentence critique/correction. Start with 'Correct.', 'Partially correct.', or 'Incorrect.'."""
                    feedback = model.generate_content(prompt, generation_config=generation_config).text
                    add_message("assistant", feedback); st.session_state.current_question_index += 1; st.session_state.stage = "DISPLAY_QUESTION"
            st.rerun()
if st.session_state.stage == "CONCLUDED":
    if not st.session_state.messages or "That concludes the technical screening" not in st.session_state.messages[-1].get('content', ''):
        add_message("assistant", "That concludes the technical screening. Thank you for your time! A recruiter will review your information and be in touch soon.")
        st.balloons()
    st.text_area("The screening is complete. You may now close the window.", disabled=True, height=150)
