# 🧠 AI-Powered Technical Interviewer.

This project is an AI-powered technical interviewer that conducts multi-stage interviews, scores candidate answers on clarity, accuracy, and depth, and provides intelligent feedback — all running locally using LangChain and Groq.


## 🛠️ Technologies Used

| Tech            | Purpose                                   |
|-----------------|-------------------------------------------|
| FastAPI         | Backend API framework                     |
| LangChain       | Prompt chaining and LLM orchestration     |
| Groq            | Ultra-fast LLM inference(LLaMA3 used here)|
| Python 3.10+    | Language for app logic                    |
| Pydantic        | Request/response models                   |
| Uvicorn         | ASGI server                               |


## 📦 Setup Instructions

### 1. Clone the Repository
git clone https://github.com/aimanmaniyar-123/AI-Interviewer.git
cd AI-Interviewer

### 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

### 3. Install Python Dependencies
pip install -r requirements.txt

### 4. Add .env file
create a .env file and set your Groq API key:
GROQ_API_KEY=your-groq-api-key

### 5. Start FastAPI Server
uvicorn interviewer_app:app --reload
visit: http://127.0.0.1:8000/docs

### API Usage
### POST /docs
Request Body:
{
  "session_id": "aiman_session1",
  "topic": "Python",
  "stage": 0,
  "user_response": ""
}
The stage should be incremented per question (0–5).
user_response is empty on first question and filled afterward.

### Example Q&A Flow
User sends request with stage: 0 → receives Q1.
User submits answer with stage: 1 → gets feedback + Q2.
After stage 5 → receives total average scores and summary.


### Design Decisions
LLM Execution: Powered by Groq and LLaMA3.
Plain Feedback Parsing: Uses regex to extract scores, allowing flexibility.
Follow-up Prompts: Automatically generated when scores fall below 6.
Evaluation Robustness: Falls back to default scoring if feedback parsing fails.
### Branching flow
Start Interview (stage = 0)
        ↓
Generate Q1 ➝ Return Q1 to user
        ↓
Receive Answer to Q1
        ↓
Evaluate Answer (stage ≥ 1):
   ├── Score (Clarity, Accuracy, Depth)
   ├── Extract Plain Feedback
   ├── If any score < 6 → Add Follow-up Prompt
   ↓
Generate Next Question
        ↓
Repeat until stage = 5
        ↓
✅ Interview Complete:
   ├── Average all scores
   ├── Return Summary + Feedback



### Optional Features Implemented
 Score Breakdown: Clarity, Accuracy, Depth (out of 10)
 Average Score Summary after 5 questions

🤝 Contact
Built by Aiman Maniyar.
Contributions & stars are welcome!

