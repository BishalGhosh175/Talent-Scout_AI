# app.py - Final Version with Interactive Quiz

import streamlit as st
import google.generativeai as genai
import json
import fitz  # PyMuPDF
from docx import Document

# --- Configuration and Initialization ---

st.set_page_config(page_title="TalentScout Assistant", page_icon="🤖", layout="centered")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (KeyError, AttributeError):
    st.error("🚨 **Error:** Gemini API Key not found. Please create a `.streamlit/secrets.toml` file.", icon="🔑")
    st.stop()

try:
    model = genai.GenerativeModel('gemini-2.5-pro')
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
        .stChatMessage {
            border-radius: 20px; padding: 1rem 1.5rem; margin-bottom: 1rem;
            box-shadow: 0 4px 6px 0 rgba(0,0,0,0.07); border: none;
            background-color: #E9E9EB;
        }
        /* FIX: Final, more specific selector to force black text color */
        div[data-testid="stMarkdownContainer"] * {
            color: black !important;
        }
        .stButton>button {
            width: 100%; border-radius: 20px; border: 1px solid #0A66C2;
            color: #0A66C2; background-color: white; transition: all 0.2s ease;
            padding: 0.75rem 0; font-weight: 600;
        }
        .stButton>button:hover {
            border-color: #004182; color: white; background-color: #0A66C2;
        }
    </style>
    """, unsafe_allow_html=True)
load_css()

# --- State Management ---
if "stage" not in st.session_state:
    st.session_state.stage = "GREETING"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {}
if "manual_entry_fields" not in st.session_state:
    st.session_state.manual_entry_fields = [
        "Full Name", "Email Address", "Phone Number", "Years of Experience",
        "Desired Position(s)", "Current Location", "Tech Stack"
    ]
if "current_field_index" not in st.session_state:
    st.session_state.current_field_index = 0
# New state variables for the interactive quiz
if "tech_questions" not in st.session_state:
    st.session_state.tech_questions = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0

# --- Helper & Prompt Functions ---

def display_chat():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def format_list_for_display(data_list):
    if isinstance(data_list, list) and data_list:
        return ', '.join(map(str, data_list))
    elif data_list: return str(data_list)
    return "N/A"

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            return "".join(page.get_text() for page in doc)
    elif uploaded_file.name.endswith('.docx'):
        doc = Document(uploaded_file)
        return "\n".join(para.text for para in doc.paragraphs)
    return uploaded_file.getvalue().decode("utf-8")

def parse_resume_with_llm(resume_text):
    prompt = f"""Analyze the resume text and extract info into a valid JSON object: {{"full_name": string, "email": string, "phone_number": string, "years_of_experience": integer, "desired_positions": list[string], "current_location": string, "tech_stack": list[string]}}. If info is missing, use null. Output ONLY the JSON object. Text: --- {resume_text} ---"""
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    except Exception: return None

# --- Main App Flow ---

st.title("🤖 TalentScout Hiring Assistant")
display_chat()

# State 1: Greeting
if st.session_state.stage == "GREETING":
    if not st.session_state.messages:
        add_message("assistant", "Hello! I'm Scout. To streamline your application, would you like to upload a resume?")
    st.session_state.stage = "AWAITING_RESUME_DECISION"
    st.rerun()

# State 2: Resume Decision
if st.session_state.stage == "AWAITING_RESUME_DECISION":
    col1, col2 = st.columns(2)
    if col1.button("✅ Yes, upload resume"):
        add_message("user", "Yes, I'll upload my resume.")
        add_message("assistant", "Great! Please use the file uploader below.")
        st.session_state.stage = "AWAITING_UPLOAD"
        st.rerun()
    if col2.button("❌ No, enter manually"):
        add_message("user", "No, I'll enter the details manually.")
        add_message("assistant", "Of course. We'll go through the details one by one.")
        st.session_state.stage = "MANUAL_GATHERING"
        st.rerun()

# ... (Stages for AWAITING_UPLOAD, VERIFY_EXTRACTED_DATA, and AWAITING_VERIFICATION_RESPONSE are largely the same)
if st.session_state.stage == "AWAITING_UPLOAD":
    uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx', 'txt'], label_visibility="collapsed")
    if uploaded_file:
        with st.spinner("Analyzing resume..."):
            text = extract_text_from_file(uploaded_file)
            if text and (data := parse_resume_with_llm(text)):
                st.session_state.candidate_data = data
                st.session_state.stage = "VERIFY_EXTRACTED_DATA"
                st.rerun()

if st.session_state.stage == "VERIFY_EXTRACTED_DATA":
    data = st.session_state.candidate_data
    msg = f"""Thanks! Please verify this information:
*   **Name:** {data.get('full_name', 'N/A')}
*   **Email:** {data.get('email', 'N/A')}
*   **Positions:** {format_list_for_display(data.get('desired_positions'))}
*   **Tech Stack:** {format_list_for_display(data.get('tech_stack'))}
Is this correct?"""
    add_message("assistant", msg)
    st.session_state.stage = "AWAITING_VERIFICATION_RESPONSE"
    st.rerun()

if st.session_state.stage == "AWAITING_VERIFICATION_RESPONSE":
    col1, col2 = st.columns(2)
    if col1.button("👍 Yes, it's correct"):
        add_message("user", "Yes, it's correct.")
        st.session_state.stage = "GENERATING_QUESTIONS"
        st.rerun()
    if col2.button("👎 No, something's wrong"):
        add_message("user", "No, something's wrong.")
        add_message("assistant", "Let's fix that. We'll go through the fields one by one.")
        st.session_state.stage = "MANUAL_GATHERING"
        st.rerun()

# State 5: Manual Data Gathering
if st.session_state.stage == "MANUAL_GATHERING":
    idx = st.session_state.current_field_index
    if idx < len(st.session_state.manual_entry_fields):
        if not st.session_state.messages or st.session_state.messages[-1]["role"] != "assistant":
            field_name = st.session_state.manual_entry_fields[idx]
            question = f"Let's start with your **{field_name}**." if idx == 0 else f"Got it. What is your **{field_name}**?"
            add_message("assistant", question)
        if prompt := st.chat_input("Your response..."):
            add_message("user", prompt)
            field_key = st.session_state.manual_entry_fields[idx].lower().replace(" ", "_")
            st.session_state.candidate_data[field_key] = prompt
            st.session_state.current_field_index += 1
            st.rerun()
    else:
        st.session_state.stage = "GENERATING_QUESTIONS" # All info gathered
        st.rerun()


# --- INTERACTIVE QUIZ LOGIC ---

# Stage 6: Generate Questions (Behind the scenes)
if st.session_state.stage == "GENERATING_QUESTIONS":
    with st.chat_message("assistant"):
        with st.spinner("Thank you. I'm now preparing a few technical questions based on your profile..."):
            tech_stack = format_list_for_display(st.session_state.candidate_data.get("tech_stack"))
            if tech_stack != "N/A":
                prompt = f"""Based on the tech stack "{tech_stack}", generate a JSON array of 3-4 technical interview questions. The JSON should be an array of strings. Example: {{"questions": ["What is a closure in JavaScript?", "Explain the main components of the Django architecture."]}}. Output ONLY the raw JSON object."""
                try:
                    response = model.generate_content(prompt)
                    q_data = json.loads(response.text)
                    st.session_state.tech_questions = q_data["questions"]
                    st.session_state.current_question_index = 0
                    add_message("assistant", "Great, I have a few questions for you. Let's start with the first one.")
                    st.session_state.stage = "ASKING_QUESTIONS"
                except (json.JSONDecodeError, KeyError) as e:
                    add_message("assistant", "I had an issue preparing the questions. A recruiter will follow up with you directly.")
                    st.session_state.stage = "CONCLUDED"
            else:
                add_message("assistant", "No tech stack was provided, so we'll skip the technical questions.")
                st.session_state.stage = "CONCLUDED"
    st.rerun()


# Stage 7: Ask Questions and Evaluate Answers
if st.session_state.stage == "ASKING_QUESTIONS":
    q_index = st.session_state.current_question_index
    # Ask the question if it hasn't been asked yet
    if q_index < len(st.session_state.tech_questions) and st.session_state.messages[-1]["role"] != "assistant":
        question = st.session_state.tech_questions[q_index]
        add_message("assistant", f"**Question {q_index + 1}:**\n\n{question}")

    # Wait for and process the answer
    if answer := st.chat_input("Your answer..."):
        add_message("user", answer)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your answer..."):
                question = st.session_state.tech_questions[q_index]
                prompt = f"""You are a senior technical interviewer. Your tone is professional and concise.
                The question was: "{question}"
                The candidate's answer is: "{answer}"
                Evaluate the answer. Is it correct, partially correct, or incorrect? Provide a one-sentence critique and a brief correction if needed. Start your response with 'Correct.', 'Partially correct.', or 'Incorrect.'."""
                
                evaluation_response = model.generate_content(prompt)
                feedback = evaluation_response.text
                add_message("assistant", feedback)

                # Move to the next question
                st.session_state.current_question_index += 1
                
                # Check if the quiz is over
                if st.session_state.current_question_index >= len(st.session_state.tech_questions):
                    st.session_state.stage = "CONCLUDED"
                    add_message("assistant", "That concludes the technical screening. Thank you for your detailed answers!")
        st.rerun()

# Stage 8: Conclude the Conversation
if st.session_state.stage == "CONCLUDED" and st.session_state.messages[-1]['role'] != 'final_message':
    add_message("assistant", "This completes the initial automated screening. A recruiter from TalentScout will review your information and be in touch soon. Thank you for your time!")
    st.session_state.messages[-1]['role'] = 'final_message' # Prevents re-adding this message
    st.balloons()
    st.rerun()