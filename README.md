# Educational-Content-Generator-AI-Agent-Development-Project

# 🎓 Edu-Agent Pro: 

**Edu-Agent Pro** is a high-performance, AI-driven educational platform tailored for MCA students and technical scholars. It leverages Google's **Gemini 1.5 Flash** model to transform standard syllabus PDFs into a dynamic, multi-modal learning environment featuring automated assessments, intelligent tutoring, and multimedia study archives.

---

## 🚀 Core Features

### 💬 Personal AI Tutor
* **Context-Aware Intelligence:** Engage with an AI tutor that analyzes your specific PDF syllabus to provide accurate, relevant guidance.
* **Technical Deep-Dives:** Complex engineering and computer science topics are simplified into digestible explanations.

### ✍️ Assessment Architect
* **Automated Exam Builder:** Generate tailored MCQ, Short Answer, or Long Theory papers (up to 50 questions) from your syllabus.
* **Professional Export:** Instantly download generated papers as high-quality PDFs for offline practice.

### 🧠 Concept Flashcards
* **Syllabus Extraction:** Automatically identifies 10 core technical concepts from your document.
* **Professional Layout:** Zero exam weightage noise; just clean, bold terms and academic definitions in a line-by-line format.

### 🎬 Visual Learning Studio (YouTube Edu)
* **Syllabus-Sync Search:** AI-powered search that finds professional university tutorials based on your specific curriculum.
* **Smart Suggestions:** Provides one-click search buttons for the most important modules in your PDF.

### 🎧 Multimedia Study Archive
* **Audio History:** Convert saved study notes into high-quality speech with integrated Play/Pause controls.
* **SQLite Persistence:** Securely stores your study history and exams in a local database for long-term review.

---

## 🎨 Professional UI/UX
Designed with a modern **React/Next.js aesthetic**, the platform offers:
* **Exclusive Palette:** A sophisticated blend of **Earth Red (#E6501B)**, **Warm Clay (#C3110C)**, and **Deep Charcoal (#280905)**.
* **Typography:** Powered by the **DM Sans** font for a premium, readable student experience.
* **Sequential Animated Greetings:** A unique, rising multi-lingual welcome (**Namaste, Vanakkam, Adaab, Jai Jagannath, Jai Shree Krishna**) that pops up one by one above the user's name.
* **High-Contrast Clarity:** Crisp white input boxes and containers ensure all technical text is visible against the dark professional theme.

---

## 🛠️ Technology Stack

* **Frontend:** Streamlit (Python Web Framework)
* **AI Engine:** Google Gemini 1.5 Flash API
* **Database:** SQLite3
* **Speech Engine:** gTTS (Google Text-to-Speech)
* **Document Generation:** PyPDF & FPDF
* **Web Integration:** Scrapetube (YouTube Data Scraper)

---

## ⚙️ Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_FORKED_REPO.git](https://github.com/YOUR_USERNAME/YOUR_FORKED_REPO.git)
    cd Educational-Content-Generator-AI-Agent-Development-Project
    ```

2.  **Install Required Libraries:**
    ```bash
    pip install streamlit google-generativeai pypdf gTTS fpdf scrapetube
    ```

3.  **API Configuration:**
    * Obtain a Gemini API Key from Google AI Studio.
    * Update the `GOOGLE_API_KEY` variable in `main.py`.

4.  **Launch the App:**
    ```bash
    streamlit run main.py
    ```

---

## 📂 Project Structure
* `main.py`: The core application logic and UI.
* `study_data.db`: Local SQLite database for user profiles and saved content.
* `.venv/`: Virtual environment for isolated dependency management.

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.place GOOGLE_API_KEY with your valid Gemini API Key.
