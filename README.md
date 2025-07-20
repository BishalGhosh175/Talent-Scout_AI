# TalentScout AI Hiring Assistant

## Project Overview
The TalentScout AI Hiring Assistant is an intelligent chatbot designed to streamline the initial candidate screening process for a technology recruitment agency. Built with Python, Streamlit, and Google's Gemini LLM, the chatbot interacts with candidates to gather essential information and pose relevant technical questions based on their declared tech stack.

The application offers two distinct pathways for data collection:
1.  **Automated Resume Parsing**: Candidates can upload their resume (PDF), which the chatbot analyzes to automatically extract key details like contact information, years of experience, and tech stack.
2.  **Manual Data Entry**: Candidates can opt to enter their information manually through a guided, step-by-step conversation.

After gathering the necessary information, the assistant generates a tailored set of technical questions to provide recruiters with initial insights into a candidate's proficiency.

---

## Technical Details

*   **Programming Language**: Python 3.10+
*   **Frontend Interface**: [Streamlit](https://streamlit.io/)
*   **Large Language Model**: Google Gemini (`gemini-2.5-flash`)
*   **Core Libraries**:
    *   `streamlit`: For building the interactive web UI.
    *   `google-generativeai`: The official Google client library for the Gemini API.
    *   `PyMuPDF` (`fitz`): For robust and efficient text extraction from PDF documents.

---

## Installation Instructions

Follow these steps to set up and run the application locally.

**1. Prerequisites:**
*   Python 3.10 or higher.
*   Git for cloning the repository.

**2. Clone the Repository:**
```bash
git clone https://github.com/BishalGhosh175/Talent-Scout_AI.git
cd talent-scout-chatbot
```

**3. Create a Virtual Environment (Recommended):**
*   **Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
*   **macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

**4. Install Dependencies:**
Install all the required libraries from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```
### 5. Set Up API Key

This application requires a Google Gemini API key to function.

*   **Get your API Key**: If you don't already have one, create a free key by visiting the **[Google AI Studio](https://aistudio.google.com/)**.

*   **Add the Key to the Project**:
    1.  In the project directory, locate the `.streamlit` folder.
    2.  Inside this folder, open the `secrets.toml` file.
    3.  Add your API key to the file. It should look exactly like this, with your key replacing the placeholder:

    ```toml
    # .streamlit/secrets.toml
    GEMINI_API_KEY="YOUR_ACTUAL_API_KEY_HERE"
    ```
---

**6. Run the Application:**
Once the setup is complete, run the following command in your terminal:
```bash
streamlit run app.py
```
The application will open in a new tab in your web browser.

## Usage Guide

The chatbot interface is designed to be clean and intuitive.

1.  **Greeting**: Upon starting, the chatbot greets you and asks if you'd like to upload a resume or fill in your details manually.
2.  **Resume Upload**:
    *   Click **"Yes, upload resume"**.
    *   An upload widget will appear. Select and upload your resume in PDF format.
    *   The chatbot will parse the document and display the extracted information for your review.
    *   You can then confirm if the details are correct or opt to fill them in manually if something is wrong.
3.  **Manual Entry**:
    *   Click **"No, fill manually"**.
    *   The chatbot will ask for one piece of information at a time (e.g., Full Name, Email, etc.).
    *   Type your answer in the input box at the bottom and press Enter.
4.  **Technical Questions**:
    *   Once all your information is gathered and confirmed, the chatbot analyzes your declared "Tech Stack".
    *   It then generates 3-5 technical questions tailored to those technologies.
5.  **Conclusion**: The chatbot thanks you for your time and concludes the automated screening process, informing you that a recruiter will be in touch.

---

## Architectural Decisions & Prompt Design

### Architecture: State Machine
The core of the chatbot's conversational logic is a **state machine** managed by `st.session_state.conversation_state`. This approach provides several key advantages:
*   **Clarity and Control**: It ensures the conversation follows a logical, predefined flow, preventing out-of-order questions or actions.
*   **Robustness**: It makes the application resilient to unexpected user inputs by controlling what the app should be doing at any given moment.
*   **Maintainability**: Adding new steps or altering the flow is as simple as defining a new state and the conditions for transitioning to it.

The primary states are: `GREETING`, `AWAITING_UPLOAD`, `CONFIRMING_DETAILS`, `GATHERING_MANUALLY`, `GENERATING_QUESTIONS`, and `CONCLUDED`.

### Prompt Engineering
Effective prompt design was crucial for guiding the LLM to produce the desired outputs accurately.

1.  **Resume Extraction Prompt (`get_resume_extraction_prompt`)**:
    *   **Role-Playing**: The prompt instructs the LLM to act as an "expert AI recruiting assistant."
    *   **Clear Instruction**: It explicitly asks for a **JSON object** and nothing else. This is reinforced by using the Gemini model's dedicated JSON output mode (`response_mime_type="application/json"`), which significantly improves reliability.
    *   **Field Specification**: It provides the exact field names to be extracted, ensuring consistent keys in the output.
    *   **Graceful Failure**: It instructs the model to use "Not Found" if a piece of information is missing, preventing errors and providing clarity.

2.  **Question Generation Prompt (`get_question_generation_prompt`)**:
    *   **Role-Playing**: The prompt assigns the role of a "Senior Technical Interviewer" to generate high-quality, relevant questions.
    *   **Contextual Input**: It feeds the candidate's specific `tech_stack` directly into the prompt.
    *   **Output Formatting**: It requests Markdown formatting for clear, readable presentation in the Streamlit UI.
    *   **Constraints**: It specifies the desired number of questions (3-5) to keep the screening concise.

---

## Data Handling & Privacy
Data privacy is a critical consideration.
*   **Secure Configuration**: The Gemini API key is managed securely using `st.secrets`, preventing it from being exposed in the source code.
*   **Ephemeral Data**: Candidate information is stored in `st.session_state`, which is ephemeral and exists only for the duration of a user's session. No data is written to a permanent database or disk in this implementation.
*   **Compliance**: For a production deployment, all data handling processes would need to be made fully compliant with standards like GDPR, including obtaining explicit user consent, encrypting data at rest and in transit, and establishing clear data retention policies.

---

## Challenges Faced & Solutions

1.  **Challenge: Reliably Extracting Structured Data from Unstructured Resumes.**
    *   **Problem**: Resumes have no standard format, making rule-based extraction (like regex) brittle and unreliable.
    *   **Solution**: Leveraged the `gemini-1.5-pro` model's advanced understanding and its native JSON output mode. By crafting a precise prompt that specified the required JSON structure and keys, I offloaded the complex parsing task to the LLM, resulting in a highly accurate and flexible extraction mechanism.

2.  **Challenge: Ensuring a Coherent and Error-Proof Conversation Flow.**
    *   **Problem**: A simple if-else structure would quickly become a tangled mess, unable to handle different user paths (upload vs. manual) or recover from errors.
    *   **Solution**: Implemented a formal state machine using `st.session_state`. This design choice provides a robust framework that dictates the application's behavior at every step. It also allowed for a seamless **fallback mechanism**: if the resume upload or parsing fails, the state transitions gracefully to `GATHERING_MANUALLY`, ensuring the user experience is never broken.

3.  **Challenge: Handling API Failures or Unexpected Model Outputs.**
    *   **Problem**: Network issues or unexpected API responses could crash the application. The LLM might not always return perfectly formatted JSON, despite instructions.
    *   **Solution**: The application wraps all API calls in `try...except` blocks. In the case of a JSON decoding error during resume parsing, the system catches the exception and, as mentioned above, intelligently pivots to the manual entry path, informing the user of the issue without halting the process.
