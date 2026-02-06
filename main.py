import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time
import sqlite3
import io
from gtts import gTTS
import hashlib
from fpdf import FPDF
import scrapetube 
import random 

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
    except: return False

def login_user(username, password):
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, make_hashes(password)))
    return c.fetchall()

def save_material(username, file_name, topic, content, m_type):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO materials (user, file_name, topic, content, type) VALUES (?, ?, ?, ?, ?)", 
                  (username, file_name, topic, content, m_type))
    conn.commit()

# --- 2. THEME & UX (DM SANS & CUSTOM PALETTE) ---
def apply_custom_design():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'DM Sans', sans-serif;
            background-color: #280905;
        }

        h1, h2, h3, h4, h5, h6, label, .stMarkdown p {
            color: #FFFFFF !important;
        }

        [data-testid="stSidebar"] {
            background-color: #740A03 !important;
            border-right: 2px solid #E6501B;
        }

        input, textarea, [data-baseweb="select"] {
            background-color: #FFFFFF !important;
            color: #280905 !important;
            border-radius: 8px !important;
            font-weight: 500;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: #C3110C;
            padding: 8px;
            border-radius: 12px;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: white !important;
            border-radius: 8px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #E6501B !important;
            font-weight: bold;
        }

        .stButton>button {
            border-radius: 10px;
            background-color: #E6501B;
            color: white;
            border: none;
            padding: 10px 20px;
            font-weight: 600;
            transition: 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #FFFFFF;
            color: #E6501B;
        }

        /* --- Animation Logic --- */
        @keyframes popUp {
            0% { opacity: 0; transform: translateY(15px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        .greeting-container {
            margin-bottom: 10px;
        }

        .greet-text {
            display: block;
            font-size: 20px;
            font-weight: 500;
            color: #E6501B;
            animation: popUp 0.6s ease-out forwards;
            opacity: 0;
        }

        .constant-name {
            font-size: 36px;
            font-weight: 800;
            color: #FFFFFF;
            margin-top: 5px;
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. UTILS ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

def get_working_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
        return "models/gemini-1.5-flash"
    except: return "models/gemini-pro"

# --- 4. PAGE CONFIG ---
st.set_page_config(page_title="Edu-Agent Pro", page_icon="🎓", layout="wide")
apply_custom_design()

# --- 5. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""
if "pdf_library" not in st.session_state: st.session_state.pdf_library = {} 
if "active_pdf" not in st.session_state: st.session_state.active_pdf = None
if "messages" not in st.session_state: st.session_state.messages = []
if "quiz_result" not in st.session_state: st.session_state.quiz_result = ""

# --- 6. AUTH UI ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🎓 Student Hub</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        choice = st.radio("Access Mode", ["Login", "Sign Up"], horizontal=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if choice == "Login" and st.button("Access Dashboard"):
            if login_user(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Access Denied")
        elif choice == "Sign Up" and st.button("Register Profile"):
            if add_user(u, p): st.success("Profile Created!")
            else: st.error("Username already taken")
else:
    # --- 7. MAIN APP ---
    GOOGLE_API_KEY = "AIzaSyB7QsTbbyW7QEljmUZBPHE2U4QTrDIjoGU"
    genai.configure(api_key=GOOGLE_API_KEY)
    active_model = get_working_model()

    with st.sidebar:
        # --- Sequential Animated Greetings ---
        greetings = ["Hello", "Namaste", "Vanakkam", "Adaab", "Jai Jagannath", "Jai Shree Krishna"]
        
        greeting_html = "<div class='greeting-container'>"
        for i, text in enumerate(greetings):
            delay = i * 0.4  # Time between each pop-up
            greeting_html += f"<span class='greet-text' style='animation-delay: {delay}s;'>{text}</span>"
        
        # Adding the Constant Large Name at the bottom of the animation
        greeting_html += f"<div class='constant-name'>{st.session_state.username}</div>"
        greeting_html += "</div>"
        
        st.markdown(greeting_html, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("📁 Upload Syllabus")
        up_new = st.file_uploader("", type="pdf")
        if up_new:
            if up_new.name not in st.session_state.pdf_library:
                reader = PdfReader(up_new)
                st.session_state.pdf_library[up_new.name] = "".join([p.extract_text() for p in reader.pages])
                st.session_state.active_pdf = up_new.name
                st.rerun()

        if st.session_state.pdf_library:
            st.session_state.active_pdf = st.selectbox("Switch PDF:", options=list(st.session_state.pdf_library.keys()))
        
        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if not st.session_state.active_pdf:
        st.title("🚀 Select a PDF to Begin")
    else:
        current_text = st.session_state.pdf_library[st.session_state.active_pdf]
        tabs = st.tabs(["💬 Personal Tutor", "✍️ Assessment Architect", "💡 Study Cards", "🎬 Visual Studio", "🎧 Archives"])

        with tabs[0]:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.write(m["content"])
            if pr := st.chat_input("What would you like to discuss?"):
                st.session_state.messages.append({"role": "user", "content": pr})
                model = genai.GenerativeModel(active_model)
                res = model.generate_content(f"Context: {current_text[:4000]}\nQ: {pr}")
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.rerun()

        with tabs[1]:
            st.subheader("Professional Exam Generator")
            col_a, col_b = st.columns(2)
            with col_a:
                q_t = st.selectbox("Format", ["MCQ", "Short", "Long Theory"])
                count = st.number_input("Count", 1, 50, 20)
                if st.button("Generate Paper"):
                    model = genai.GenerativeModel(active_model)
                    res = model.generate_content(f"Create {count} {q_t} for MCA with answers. Context: {current_text[:6000]}")
                    st.session_state.quiz_result = res.text
                    save_material(st.session_state.username, st.session_state.active_pdf, f"{count} {q_t}", res.text, "Exam")
            with col_b:
                if st.session_state.quiz_result:
                    st.text_area("Preview", st.session_state.quiz_result, height=300)
                    st.download_button("💾 Save PDF", create_pdf(st.session_state.quiz_result), "paper.pdf")

        with tabs[2]:
            st.subheader("🧠 Core Concepts Flashcards")
            if st.button("Generate Professional Flashcards"):
                model = genai.GenerativeModel(active_model)
                prompt = (
                    "Act as an academic expert. Based on the syllabus provided, extract 10 core concepts. "
                    "Format them strictly as a bulleted list where each bullet starts with the term in bold, "
                    "followed by a colon and a professional, academic definition. "
                    "Example: '● **Term**: Definition.' "
                    "Ensure definitions are clear, academic, and do not mention marks or weightage. "
                    "Text: " + current_text[:5000]
                )
                res = model.generate_content(prompt)
                save_material(st.session_state.username, st.session_state.active_pdf, "Flashcards", res.text, "Flashcard")
                st.markdown(res.text)

        with tabs[3]:
            st.subheader("📺 Visual Studio")
            yt_input = st.text_input("Search Video Topic:")
            if st.button("Find Videos"):
                if yt_input:
                    final_q = f"{yt_input} professional tutorial {st.session_state.active_pdf}"
                    videos = scrapetube.get_search(final_q, limit=5)
                    for v in videos:
                        st.video(f"https://www.youtube.com/watch?v={v['videoId']}")

        with tabs[4]:
            st.subheader("📂 Audio Study Archive")
            c = conn.cursor()
            c.execute("SELECT id, topic, content FROM materials WHERE user=? ORDER BY timestamp DESC", (st.session_state.username,))
            for r in c.fetchall():
                with st.expander(f"📌 {r[1]}"):
                    st.write(r[2])
                    if st.button(f"🔊 Listen", key=f"aud_{r[0]}"):
                        tts = gTTS(r[2], lang='en')
                        af = io.BytesIO(); tts.write_to_fp(af); af.seek(0)
                        st.audio(af, format='audio/mp3')