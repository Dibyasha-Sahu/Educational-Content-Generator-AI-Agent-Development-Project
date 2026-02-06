import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Edu-Agent Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. API KEY SETUP ---
GOOGLE_API_KEY = "AIzaSyCO4d6U-okdVTqkHj3UK60IYARfDzOiMeI"
genai.configure(api_key=GOOGLE_API_KEY)

# --- 3. AUTO-DETECT MODEL ---
def get_active_model_name():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
                if 'pro' in m.name: return m.name
        return "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

if "active_model" not in st.session_state:
    st.session_state.active_model = get_active_model_name()

# --- 4. SAFETY SETTINGS ---
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- 5. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "quiz_result" not in st.session_state:
    st.session_state.quiz_result = ""

# --- 6. MAIN LOGIC ---

# SCENARIO A: LANDING PAGE
if st.session_state.pdf_text == "":
    st.title("🎓 MCA Exam & Tutor System")
    st.markdown("#### The intelligent way to create semester exams and study aids.")
    st.caption(f"🚀 System Ready | Powered by {st.session_state.active_model.split('/')[-1]}")
    
    with st.container():
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("👆 **Start Here: Upload Syllabus or Chapter (PDF)**")
            uploaded_file = st.file_uploader("", type="pdf", key="main_uploader")
            
            if uploaded_file:
                with st.spinner("🚀 AI is analyzing the curriculum..."):
                    try:
                        reader = PdfReader(uploaded_file)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        
                        st.session_state.pdf_text = text
                        st.session_state.file_name = uploaded_file.name
                        st.success("✅ Analysis Complete!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
        st.markdown("---")

# SCENARIO B: MAIN DASHBOARD
else:
    # Sidebar
    with st.sidebar:
        st.header(f"📂 {st.session_state.file_name}")
        st.success("Status: Online")
        if st.button("📤 Upload Different File"):
            st.session_state.pdf_text = ""
            st.session_state.file_name = None
            st.session_state.messages = []
            st.session_state.quiz_result = ""
            st.rerun()
        
        st.divider()
        st.markdown("**Quick Actions**")
        if st.button("🧹 Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # Tabs
    tab_chat, tab_teacher, tab_study = st.tabs(["💬 Student Chat", "🎓 Exam Creator", "🧠 Study Aids"])

    # --- TAB 1: STUDENT CHAT ---
    with tab_chat:
        st.subheader("Interactive Tutor")
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask a question about the topic..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        model = genai.GenerativeModel(st.session_state.active_model, safety_settings=safety_settings)
                        full_prompt = f"Context: {st.session_state.pdf_text}\n\nQuestion: {prompt}"
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()
        if st.button("👶 Explain the last answer like I'm 5 years old"):
            if st.session_state.messages:
                last_response = st.session_state.messages[-1]["content"]
                with st.spinner("Simplifying..."):
                    model = genai.GenerativeModel(st.session_state.active_model, safety_settings=safety_settings)
                    simp_response = model.generate_content(f"Explain this simply for a child: {last_response}")
                    st.session_state.messages.append({"role": "assistant", "content": f"**Simplified:** {simp_response.text}"})
                    st.rerun()

    # --- TAB 2: EXAM CREATOR (UPDATED) ---
    with tab_teacher:
        st.subheader("🛠️ Semester Exam Generator")
        
        col_t1, col_t2 = st.columns([1, 1])
        
        with col_t1:
            st.markdown("### 📝 Configure Exam")
            
            # 1. Question Type Selection
            q_type = st.selectbox(
                "Select Question Type", 
                ["Multiple Choice (MCQ)", "Short Answer (2-5 Marks)", "Long Theory (10+ Marks)"]
            )
            
            # 2. Difficulty Slider
            difficulty = st.select_slider("Select Difficulty Level", options=["Easy", "Medium", "Hard"])
            
            # 3. Number of Questions (Increased Limit)
            num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5)
            
            if st.button("Generate Exam Paper"):
                with st.spinner(f"Creating {difficulty} {q_type} Exam..."):
                    try:
                        model = genai.GenerativeModel(st.session_state.active_model, safety_settings=safety_settings)
                        safe_text = st.session_state.pdf_text[:5000] # Increased context limit slightly
                        
                        # Dynamic Prompt based on selection
                        if "Multiple Choice" in q_type:
                            prompt_instruction = """
                            Format:
                            Q1. Question
                            A) Option
                            B) Option
                            C) Option
                            D) Option
                            *Correct Answer: X*
                            """
                        elif "Short Answer" in q_type:
                            prompt_instruction = """
                            Format:
                            Q1. Question
                            (Expected Answer Key: [Briefly explain the key points expected])
                            """
                        else: # Long Theory
                            prompt_instruction = """
                            Format:
                            Q1. Question (Detailed theoretical question suitable for long essay)
                            (Key Evaluation Points: [List 3-4 bullet points that must be in the answer])
                            """

                        final_prompt = f"""
                        Create {num_questions} {difficulty} level questions based on the text below.
                        Type: {q_type}
                        Target Audience: MCA (Masters in Computer Application) Students.
                        
                        {prompt_instruction}
                        
                        TEXT CONTENT: {safe_text}
                        """
                        
                        resp = model.generate_content(final_prompt)
                        st.session_state.quiz_result = resp.text
                        st.success("✅ Exam Paper Generated!")
                        
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_t2:
            st.markdown("### 📄 Preview & Download")
            if st.session_state.quiz_result:
                st.text_area("Exam Preview:", st.session_state.quiz_result, height=400)
                st.download_button(
                    label="💾 Download Exam as Text File",
                    data=st.session_state.quiz_result,
                    file_name="mca_exam_paper.txt",
                    mime="text/plain"
                )
            else:
                st.info("Configure the options on the left and click 'Generate Exam Paper' to see the result here.")

    # --- TAB 3: STUDY AIDS ---
    with tab_study:
        st.subheader("🧠 Student Revision Tools")
        
        if st.button("⚡ Generate Flashcards (Key Definitions)"):
            with st.spinner("Creating Flashcards..."):
                try:
                    model = genai.GenerativeModel(st.session_state.active_model, safety_settings=safety_settings)
                    safe_text = st.session_state.pdf_text[:4000]
                    resp = model.generate_content(f"Extract 5 key terms and their definitions from this text. Format as 'Term: Definition'. Text: {safe_text}")
                    
                    cards = resp.text.split('\n')
                    for card in cards:
                        if ":" in card:
                            term, definition = card.split(":", 1)
                            st.info(f"**{term.strip()}**\n\n{definition.strip()}")
                except Exception as e:
                    st.error(f"Error: {e}")