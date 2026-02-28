import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time
import sqlite3
import io
from gtts import gTTS
import hashlib
from fpdf import FPDF
import random 
import re

# --- 1. DATABASE & AUTH ---
def init_db():
    conn = sqlite3.connect('study_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS materials 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user TEXT, file_name TEXT, topic TEXT, 
                  content TEXT, type TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    return conn

conn = init_db()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password):
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except: 
        return False

def login_user(username, password):
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, make_hashes(password)))
    return c.fetchall()

def save_material(username, file_name, topic, content, m_type):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO materials (user, file_name, topic, content, type) VALUES (?, ?, ?, ?, ?)", 
                  (username, file_name, topic, content, m_type))
    conn.commit()

# --- 2. HIGH-FIDELITY SaaS UI ---
def apply_custom_design():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

        .stApp {
            font-family: 'DM Sans', sans-serif;
            background-color: #280905;
            background-image: radial-gradient(circle at 50% 50%, #3d0e08 0%, #280905 100%);
        }

        [data-testid="stSidebar"] {
            background-color: #740A03 !important;
            border-right: 1px solid rgba(230, 80, 27, 0.4);
        }

        .hero-container {
            text-align: center;
            padding: 80px 20px;
            background: transparent;
            margin-bottom: 20px;
        }

        .hero-greeting-box {
            position: relative;
            height: 100px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        @keyframes heroFadeInOut {
            0% { opacity: 0; transform: translateY(20px); }
            10% { opacity: 1; transform: translateY(0); }
            30% { opacity: 1; transform: translateY(0); }
            40% { opacity: 0; transform: translateY(-20px); }
            100% { opacity: 0; }
        }

        .greet-text {
            color: #FFFFFF !important;
            font-size: 72px;
            font-weight: 800;
            position: absolute;
            opacity: 0;
            animation: heroFadeInOut 6s linear infinite;
        }

        .secondary-headline {
            color: #E6501B !important;
            font-size: 24px;
            font-weight: 500;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 30px;
        }

        .stTabs [data-baseweb="tab-list"] {
            background: rgba(116, 10, 3, 0.3);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 10px;
        }

        .stButton>button {
            background: linear-gradient(135deg, #E6501B 0%, #740A03 100%);
            color: white;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            transition: 0.3s;
            width: 100%;
        }

        .stButton>button:hover {
            box-shadow: 0px 0px 20px rgba(230, 80, 27, 0.5);
            background: white;
            color: #E6501B;
        }

        .paper-preview-box {
            background-color: #ffffff;
            color: #1a1a1a;
            padding: 40px;
            border-radius: 8px;
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            border: 2px solid #333;
            white-space: pre-wrap;
        }

        .unit-summary-box {
            background: rgba(230, 230, 230, 0.1);
            border: 2px solid #E6501B;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            color: white;
        }
        
        .section-config-header {
            color: #E6501B;
            font-weight: bold;
            font-size: 18px;
            margin-top: 20px;
            border-bottom: 1px solid rgba(230, 80, 27, 0.3);
            padding-bottom: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. UTILS ---
def create_pdf(text, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 16)
    pdf.cell(0, 10, title.upper(), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Times", size=11)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. PAGE CONFIG ---
st.set_page_config(page_title="AI Faculty Support System", page_icon="🎓", layout="wide")
apply_custom_design()

# --- 5. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""
if "pdf_library" not in st.session_state: st.session_state.pdf_library = {} 
if "active_pdf" not in st.session_state: st.session_state.active_pdf = None
if "messages" not in st.session_state: st.session_state.messages = []
if "quiz_result" not in st.session_state: st.session_state.quiz_result = ""
if "final_paper_content" not in st.session_state: st.session_state.final_paper_content = ""
if "final_unit_summary" not in st.session_state: st.session_state.final_unit_summary = ""
if "lesson_plan_result" not in st.session_state: st.session_state.lesson_plan_result = ""
if "slide_result" not in st.session_state: st.session_state.slide_result = ""

# --- 6. AUTH UI ---
if not st.session_state.logged_in:
    st.markdown("<div class='hero-container'><h1 style='color:white; font-size:50px;'>🎓 Faculty Intelligence Hub</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        choice = st.radio("Access Mode", ["Login", "Sign Up"], horizontal=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if choice == "Login" and st.button("Enter Dashboard"):
            if login_user(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Access Denied")
        elif choice == "Sign Up" and st.button("Register Profile"):
            if add_user(u, p): st.success("Account Ready!")
            else: st.error("Username Taken")
else:
    # --- 7. MAIN APP ---
    GOOGLE_API_KEY = "Ur API KEY HERE"
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # EXACT MODEL FROM YOUR ORIGINAL LOGS
    FINAL_MODEL_NAME = "gemini-2.5-flash"

    # HERO HEADER
    greetings = ["Hello", "Namaste", "Jai Jagannath"]
    hero_html = """<div class="hero-container"><div class="hero-greeting-box">"""
    for i, text in enumerate(greetings):
        delay = i * 2 
        hero_html += f"<span class='greet-text' style='animation-delay: {delay}s;'>{text}</span>"
    hero_html += f"""</div><div class="secondary-headline">Your Intelligent Academic Partner</div>
    <div style="font-size: 20px; color: white; opacity: 0.7; margin-top: 15px;">Professor {st.session_state.username}</div></div>"""
    st.markdown(hero_html, unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("📁 Curriculum Upload")
        up_new = st.file_uploader("Upload Syllabus PDF", type="pdf")
        if up_new:
            if up_new.name not in st.session_state.pdf_library:
                reader = PdfReader(up_new)
                st.session_state.pdf_library[up_new.name] = "".join([p.extract_text() for p in reader.pages])
                st.session_state.active_pdf = up_new.name
                st.rerun()
        if st.session_state.pdf_library:
            st.session_state.active_pdf = st.selectbox("Switch PDF:", options=list(st.session_state.pdf_library.keys()))
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if not st.session_state.active_pdf:
        st.info("Upload your curriculum syllabus in the sidebar to activate AI support tools.")
    else:
        current_text = st.session_state.pdf_library[st.session_state.active_pdf]
        tabs = st.tabs(["💬 Tutor", "✍️ Assessment", "📜 Exam Paper", "📅 Lesson Plan", "📊 Slides", "🎧 Archive"])

        # Tab 1: Tutor
        with tabs[0]:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.write(m["content"])
            if pr := st.chat_input("Ask about the syllabus..."):
                st.session_state.messages.append({"role": "user", "content": pr})
                model = genai.GenerativeModel(FINAL_MODEL_NAME)
                res = model.generate_content(f"Context: {current_text[:4000]}\nQ: {pr}")
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.rerun()

        # Tab 2: Assessment Architect (FIXED FORMATTING FOR QUESTIONS & ANSWERS)
        with tabs[1]:
            st.subheader("Assessment Architect")
            col_a, col_b = st.columns(2)
            with col_a:
                q_t = st.selectbox("Format", ["MCQ", "2-Mark Short Questions", "3-Mark Mid-Questions", "5-Mark Long Questions"])
                diff_assess = st.select_slider("Difficulty Level", options=["Easy", "Medium", "Hard"], key="assess_diff")
                count = st.number_input("Count", 1, 50, 10)
                if st.button("Generate Questions"):
                    with st.spinner("Generating highly structured assessment..."):
                        model = genai.GenerativeModel(FINAL_MODEL_NAME)
                        prompt = (
                            f"Create {count} {q_t} questions at {diff_assess} level based on the following context.\n\n"
                            f"STRICT FORMATTING RULES:\n"
                            f"1. ALWAYS bold the question text and number it clearly (e.g., **Q1. What is...?**).\n"
                            f"2. If generating MCQs, list each option (A, B, C, D) on a completely new line.\n"
                            f"3. ALWAYS bold the answer prefix and leave a blank line before it (e.g., **Correct Answer:**).\n"
                            f"4. If an answer contains a list, use bullet points (-) instead of numbers. Do NOT use numbers inside answers to prevent confusion with question numbers.\n"
                            f"5. Leave two blank lines between the end of an answer and the start of the next question.\n\n"
                            f"Context: {current_text[:6000]}"
                        )
                        res = model.generate_content(prompt)
                        st.session_state.quiz_result = res.text
            with col_b:
                if st.session_state.quiz_result:
                    st.markdown(st.session_state.quiz_result)
                    st.download_button("💾 Export PDF", create_pdf(st.session_state.quiz_result, "Assessment"), "assessment.pdf")

        # Tab 3: Exam Paper Generator
        with tabs[2]:
            st.subheader("📜 Professional Exam Paper Generator")
            paper_name = st.text_input("Examination Name", value="Final_Term_Examination")
            st.markdown("---")
            levels = ["Very Easy", "Easy", "Moderate", "Difficult", "Very Difficult"]
            
            # Section A
            st.markdown("<div class='section-config-header'>Section A: Objective Type (1 Mark Each)</div>", unsafe_allow_html=True)
            col1a, col1b = st.columns([1, 2])
            with col1a:
                e_mcq = st.number_input("No. of MCQs", 0, 50, 10)
                e_fill = st.number_input("No. of Fill-ups", 0, 50, 5)
            with col1b:
                diff_a = st.select_slider("Difficulty for Section A", options=levels, value="Easy", key="diff_a")

            # Section B
            st.markdown("<div class='section-config-header'>Section B: Short Answer Type (3 Marks Each)</div>", unsafe_allow_html=True)
            col2a, col2b = st.columns([1, 2])
            with col2a:
                e_mid = st.number_input("No. of Questions", 0, 20, 5)
            with col2b:
                diff_b = st.select_slider("Difficulty for Section B", options=levels, value="Moderate", key="diff_b")

            # Section C
            st.markdown("<div class='section-config-header'>Section C: Long Answer Type (5 Marks Each)</div>", unsafe_allow_html=True)
            col3a, col3b = st.columns([1, 2])
            with col3a:
                e_long = st.number_input("No. of Questions", 0, 15, 3)
            with col3b:
                diff_c = st.select_slider("Difficulty for Section C", options=levels, value="Difficult", key="diff_c")

            st.markdown("---")
            if st.button("🚀 Generate Professional Exam Paper"):
                with st.spinner("Analyzing curriculum and drafting sections..."):
                    model = genai.GenerativeModel(FINAL_MODEL_NAME)
                    full_prompt = (
                        f"Act as a professional Academic Examiner. Create a formal question paper for '{paper_name}'.\n\n"
                        f"SECTION A (1 Mark Each): {e_mcq} MCQs and {e_fill} Fill-ups. DIFFICULTY: {diff_a}. Start numbering from 1.\n"
                        f"SECTION B (3 Marks Each): {e_mid} questions. DIFFICULTY: {diff_b}. Start numbering from 1.\n"
                        f"SECTION C (5 Marks Each): {e_long} questions. DIFFICULTY: {diff_c}. Start numbering from 1.\n\n"
                        f"RULES:\n"
                        f"- Reset numbering for each section. No answers.\n"
                        f"- Use formal academic language.\n"
                        f"- At the end, write '---SUMMARY---' and provide a Teacher's Unit Coverage Summary showing Unit mapping for each question.\n\n"
                        f"Syllabus Context: {current_text[:8000]}"
                    )
                    full_res = model.generate_content(full_prompt).text
                    if "---SUMMARY---" in full_res:
                        parts = full_res.split("---SUMMARY---")
                        st.session_state.final_paper_content = parts[0].strip()
                        st.session_state.final_unit_summary = parts[1].strip()
                    else:
                        st.session_state.final_paper_content = full_res
                        st.session_state.final_unit_summary = "Unit analysis currently unavailable."
                    st.rerun()

            if st.session_state.final_paper_content:
                st.markdown("#### 📄 University-Standard Paper Preview")
                st.markdown(f"<div class='paper-preview-box'>{st.session_state.final_paper_content}</div>", unsafe_allow_html=True)
                st.markdown("---")
                st.subheader("👨‍🏫 Teacher's Confidential Unit Guide")
                st.markdown(f"<div class='unit-summary-box'>{st.session_state.final_unit_summary}</div>", unsafe_allow_html=True)
                st.download_button("📥 Download Official PDF", create_pdf(st.session_state.final_paper_content, paper_name), f"{paper_name}.pdf")

        # Tab 4: Lesson Plan
        with tabs[3]:
            st.subheader("Automated Lesson Planner")
            plan_type = st.radio("Select Plan Duration:", ["Weekly Plan", "Daily Plan"], horizontal=True)
            
            if st.button("Create Planner"):
                with st.spinner(f"Drafting Professional {plan_type}..."):
                    model = genai.GenerativeModel(FINAL_MODEL_NAME)
                    prompt = (
                        f"Act as an expert Academic Curriculum Planner. Generate a professional {plan_type.lower()} for a teacher based on the syllabus below.\n\n"
                        f"CRITICAL RULES:\n"
                        f"1. Each teaching period is 40 minutes long. Break down the units logically so that the teacher does NOT cover an entire unit in one single period/day.\n"
                        f"2. DO NOT output specific timestamps or minute-by-minute breakdowns (e.g., avoid writing '10 mins on X').\n"
                        f"3. Structure the plan strictly 'Unit-wise' and then 'Topic-wise' for each teaching day.\n"
                        f"4. For each topic/day, include a section called 'Extra Beneficial Topic' (such as industry insights, advanced concepts, or practical examples) that the teacher can use to provide extra value to the students.\n\n"
                        f"Syllabus Context: {current_text[:6000]}"
                    )
                    res = model.generate_content(prompt)
                    st.session_state.lesson_plan_result = res.text
            
            if st.session_state.lesson_plan_result:
                st.markdown(f"<div class='paper-preview-box'>{st.session_state.lesson_plan_result}</div>", unsafe_allow_html=True)
                st.download_button(
                    "📥 Download Lesson Plan (PDF)", 
                    create_pdf(st.session_state.lesson_plan_result, f"Professional_{plan_type.replace(' ', '_')}"), 
                    f"Lesson_Plan.pdf"
                )

        # Tab 5: Slides 
        with tabs[4]:
            st.subheader("Presentation Outliner")
            slide_topic = st.text_input("Topic Name:")
            
            if st.button("Generate Slides"):
                with st.spinner("Structuring presentation slides..."):
                    model = genai.GenerativeModel(FINAL_MODEL_NAME)
                    prompt = f"Create a professional slide presentation outline for the topic '{slide_topic}' based on this syllabus context: {current_text[:6000]}"
                    res = model.generate_content(prompt)
                    st.session_state.slide_result = res.text
            
            if st.session_state.slide_result:
                st.markdown(f"<div class='paper-preview-box'>{st.session_state.slide_result}</div>", unsafe_allow_html=True)
                topic_filename = slide_topic.replace(' ', '_') if slide_topic else "Outline"
                st.download_button(
                    "📥 Download Slides Outline (PDF)", 
                    create_pdf(st.session_state.slide_result, f"{topic_filename}_Slides"), 
                    f"Slides_{topic_filename}.pdf"
                )

        # Tab 6: Archive
        with tabs[5]:
            st.subheader("Audio Study Archive")
            c = conn.cursor()
            c.execute("SELECT id, topic, content FROM materials WHERE user=? ORDER BY id DESC", (st.session_state.username,))
            for r in c.fetchall():
                with st.expander(f"📌 Archive {r[0]}"):
                    st.write(r[2])
                    if st.button(f"🔊 Listen", key=f"aud_{r[0]}"):
                        tts = gTTS(r[2][:500], lang='en')
                        af = io.BytesIO()
                        tts.write_to_fp(af)
                        af.seek(0)
                        st.audio(af)