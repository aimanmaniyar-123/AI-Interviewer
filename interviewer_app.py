from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_community.llms import Ollama
import re

app = FastAPI()
llm = Ollama(model="llama3")  # Make sure Ollama is running with this model

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

# In-memory session storage
interview_sessions = {}

# Generate question from topic and stage
def generate_question(topic: str, stage: int) -> str:
    prompt = ChatPromptTemplate.from_template(
        "You're a technical interviewer. Generate question {n} on {topic}. Ask coding or theory questions."
    )
    chain = prompt | llm
    result = chain.invoke({"n": stage + 1, "topic": topic})
    return result.strip()

# Evaluate user's answer: extract scores and feedback
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
    raw_result = chain.invoke({"user_code": user_code, "topic": topic}).strip()

    # Extract numeric scores using regex
    def extract_score(label):
        match = re.search(rf"{label}\s*[:\-]?\s*(\d+)", raw_result, re.IGNORECASE)
        return int(match.group(1)) if match else 6  # Default to 6 if missing

    clarity = extract_score("Clarity")
    accuracy = extract_score("Accuracy")
    depth = extract_score("Depth")

    # Extract feedback (text after scores)
    feedback_split = re.split(r"(?i)feedback\s*[:\-]?", raw_result)
    feedback = feedback_split[1].strip() if len(feedback_split) > 1 else "No specific feedback given."

    score = {
        "clarity": clarity,
        "accuracy": accuracy,
        "depth": depth
    }

    return feedback, score

# Add follow-up prompt if any score < 6
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
        # Evaluate previous stage response if applicable
        if req.stage > 0:
            feedback, score = evaluate_answer(req.user_response, req.topic)
            session["responses"].append(req.user_response)
            session["scores"].append(score)
            session["feedbacks"].append(feedback)

        # End after 5 questions
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
                question="",
                feedback=feedback,
                summary=summary,
                complete=True,
                score=avg_score
            )

        # Generate the next question
        next_question = generate_question(req.topic, req.stage)
        session["questions"].append(next_question)
        session["stage"] = req.stage + 1

        # Add follow-up hint if weak performance
        feedback += follow_up_if_needed(score, req.topic)

        return InterviewResponse(
            question=next_question,
            feedback=feedback,
            summary="",
            complete=False,
            score=score
        )

    except Exception as e:
        return InterviewResponse(
            question="",
            feedback="❌ Internal error occurred.",
            summary=str(e),
            complete=True,
            score={}
        )
