from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_groq import ChatGroq  # ✅ new import
import re
import time
import os

load_dotenv()
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the Groq LLM model once at startup
@app.on_event("startup")
def load_model():
    print("⏳ Loading Groq LLaMA3 model...")
    t0 = time.time()
    _ = llm.invoke("Say hello")  # Warm-up
    print(f"✅ Groq LLM is ready. Load time: {time.time() - t0:.2f}s")

# Initialize Groq LLM (LLaMA3)
llm = ChatGroq(
    model="llama3-8b-8192",  # or try: "mixtral-8x7b-32768", "gemma-7b-it"
    groq_api_key=os.getenv("GROQ_API_KEY")
)

class InterviewRequest(BaseModel):
    session_id: str
    topic: str
    stage: int
    user_response: str = ""

class InterviewResponse(BaseModel):
    question: str
    feedback: str
    summary: str
    complete: bool
    score: dict = {}

interview_sessions = {}

def generate_question(topic: str, stage: int) -> str:
    prompt = ChatPromptTemplate.from_template(
        "You're a technical interviewer. Generate question {n} on {topic}. Ask coding or theory questions."
    )
    chain = prompt | llm
    result = chain.invoke({"n": stage + 1, "topic": topic})
    return result.content.strip()

def evaluate_answer(user_code: str, topic: str):
    eval_prompt = ChatPromptTemplate.from_template(
        """Evaluate the following Python answer to a technical question in {topic}.

Rate it out of 10 on:
- Clarity
- Accuracy
- Depth

Then provide a brief, plain-text feedback.
Answer:
```python
{user_code}
```"""
    )
    chain = eval_prompt | llm
    raw_result = chain.invoke({"user_code": user_code, "topic": topic}).content.strip()

    def extract_score(label):
        match = re.search(rf"{label}\s*[:\-]?\s*(\d+)", raw_result, re.IGNORECASE)
        return int(match.group(1)) if match else 6  # default score

    clarity = extract_score("Clarity")
    accuracy = extract_score("Accuracy")
    depth = extract_score("Depth")

    feedback_split = re.split(r"(?i)feedback\s*[:\-]?", raw_result)
    feedback = feedback_split[1].strip() if len(feedback_split) > 1 else "No specific feedback given."
    score = {"clarity": clarity, "accuracy": accuracy, "depth": depth}
    return feedback, score

def follow_up_if_needed(score: dict, topic: str) -> str:
    if any(s < 6 for s in score.values()):
        return f"\n💡 Follow-up: Can you improve your previous answer by handling edge cases or improving clarity in {topic}?"
    return ""

@app.post("/interview", response_model=InterviewResponse)
def interview(req: InterviewRequest):
    try:
        session = interview_sessions.setdefault(req.session_id, {
            "topic": req.topic,
            "stage": 0,
            "responses": [],
            "scores": [],
            "feedbacks": [],
            "questions": [],
            "complete": False
        })

        feedback, score = "", {}

        if req.stage > 0:
            feedback, score = evaluate_answer(req.user_response, req.topic)
            session["responses"].append(req.user_response)
            session["scores"].append(score)
            session["feedbacks"].append(feedback)

            if req.stage >= 5:
                avg_score = {
                    "clarity": sum(s["clarity"] for s in session["scores"]) // 5,
                    "accuracy": sum(s["accuracy"] for s in session["scores"]) // 5,
                    "depth": sum(s["depth"] for s in session["scores"]) // 5
                }
                summary = f"""✅ Interview Complete!

**Average Scores**:
- Clarity: {avg_score['clarity']}/10
- Accuracy: {avg_score['accuracy']}/10
- Depth: {avg_score['depth']}/10

**Feedback**:
You demonstrated solid reasoning and communication. To improve, practice edge cases, better structuring, and documenting your code."""
                session["complete"] = True
                return InterviewResponse(
                    question="", feedback=feedback, summary=summary, complete=True, score=avg_score
                )

        next_question = generate_question(req.topic, req.stage)
        session["questions"].append(next_question)
        session["stage"] = req.stage + 1

        feedback += follow_up_if_needed(score, req.topic)

        return InterviewResponse(
            question=next_question, feedback=feedback, summary="", complete=False, score=score
        )

    except Exception as e:
        return InterviewResponse(
            question="", feedback="❌ Internal error occurred.", summary=str(e), complete=True, score={}
        )
