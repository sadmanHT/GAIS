from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="GAIS Backend API")

class SubmitAnswerRequest(BaseModel):
    user_id: str
    question_id: str
    answer_id: str
    is_correct: bool

class SubmitAnswerResponse(BaseModel):
    status: str
    message: str

class NextQuestionResponse(BaseModel):
    question_id: str
    topic: str
    difficulty: int

class UserProgressResponse(BaseModel):
    user_id: str
    level: int
    score: float

class RecommendationResponse(BaseModel):
    user_id: str
    recommended_topics: list[str]

class DiagnosticsResponse(BaseModel):
    status: str
    version: str

@app.post("/submit-answer", response_model=SubmitAnswerResponse)
def submit_answer(req: SubmitAnswerRequest):
    return SubmitAnswerResponse(status="success", message="Answer recorded")

@app.get("/next-question", response_model=NextQuestionResponse)
def get_next_question():
    return NextQuestionResponse(question_id="q123", topic="math", difficulty=2)

@app.get("/user-progress", response_model=UserProgressResponse)
def get_user_progress():
    return UserProgressResponse(user_id="u123", level=5, score=0.85)

@app.get("/recommendation", response_model=RecommendationResponse)
def get_recommendation():
    return RecommendationResponse(user_id="u123", recommended_topics=["algebra", "geometry"])

@app.get("/diagnostics", response_model=DiagnosticsResponse)
def get_diagnostics():
    return DiagnosticsResponse(status="healthy", version="1.0.0")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
