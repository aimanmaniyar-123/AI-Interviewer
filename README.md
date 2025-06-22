# 🧠 AI-Powered Technical Interviewer.

This project is an AI-powered technical interviewer that conducts multi-stage interviews, scores candidate answers on clarity, accuracy, and depth, and provides intelligent feedback — all running locally using LangChain and Ollama.


## 🛠️ Technologies Used

| Tech            | Purpose                                   |
|-----------------|-------------------------------------------|
| FastAPI         | Backend API framework                     |
| LangChain       | Prompt chaining and LLM orchestration     |
| Ollama          | Local LLM execution (LLaMA3 used here)    |
| Python 3.10+    | Language for app logic                    |


## 📦 Setup Instructions

### 1. Clone the Repository
git clone https://github.com/aimanmaniyar-123/AI-Interviewer.git
cd AI-Interviewer

### 2. Install Python Dependencies
pip install -r requirements.txt
### 3. Run Ollama and Pull LLaMA Model
ollama run llama3
### 4. Start FastAPI Server
uvicorn interviewer_app:app --reload
http://127.0.0.1:8000/docs

✅ API Usage
POST /docs
Request Body:
{
  "session_id": "aiman_session1",
  "topic": "Python",
  "stage": 0,
  "user_response": ""
}
The stage should be incremented per question (0–5).
user_response is empty on first question and filled afterward.

🧩 Example Q&A Flow
User sends request with stage: 0 → receives Q1.
User submits answer with stage: 1 → gets feedback + Q2.
After stage 5 → receives total average scores and summary.

🤝 Contact
Built by Aiman Maniyar.
Contributions & stars are welcome!

