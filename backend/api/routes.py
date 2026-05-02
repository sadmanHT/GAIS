import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from ml.loader import get_models
from models.models import Interaction, KnowledgeState, Question, User, UserSettings


router = APIRouter()

TOPICS = ["Algebra", "Probability", "Geometry"]
DIFFICULTIES = ["easy", "medium", "hard"]


class SubmitAnswerRequest(BaseModel):
    user_id: str
    question_id: int
    correct: bool
    response_time_ms: int = Field(ge=0)
    confidence_score: float = Field(ge=1, le=5)


class SubmitAnswerResponse(BaseModel):
    user_id: str
    question_id: int
    engagement_score: float
    confusion_score: float
    retention_score: float
    mastery_probability: float


class NextQuestionResponse(BaseModel):
    question_id: int
    content: str
    topic: str
    difficulty: str
    hint: str


class ConceptProgress(BaseModel):
    concept: str
    mastery_probability: float


class UserProgressResponse(BaseModel):
    user_id: str
    concepts: list[ConceptProgress]
    weakest_concepts: list[ConceptProgress]
    overall_accuracy: float
    total_questions_answered: int


class StudyPlanItem(BaseModel):
    topic: str
    action: str
    reason: str
    urgency: str


class RecommendationResponse(BaseModel):
    user_id: str
    study_plan: list[StudyPlanItem]


class DiagnosticFinding(BaseModel):
    title: str
    detail: str
    severity: str


class DiagnosticResponse(BaseModel):
    user_id: str
    summary: str
    findings: list[DiagnosticFinding]


class MockTestQuestion(BaseModel):
    question_id: int
    content: str
    topic: str
    difficulty: str


class MockTestSection(BaseModel):
    title: str
    duration_minutes: int
    questions: list[MockTestQuestion]


class MockTestResponse(BaseModel):
    user_id: str
    sections: list[MockTestSection]


class UserSettingsResponse(BaseModel):
    user_id: str
    time_pressure: bool
    audio_cues: bool
    daily_session_minutes: int
    weekly_summary: bool
    target_score: int | None = None
    test_date: str | None = None
    weakest_area: str | None = None


class UserSettingsUpdate(BaseModel):
    time_pressure: bool | None = None
    audio_cues: bool | None = None
    daily_session_minutes: int | None = Field(default=None, ge=5, le=180)
    weekly_summary: bool | None = None
    target_score: int | None = Field(default=None, ge=260, le=340)
    test_date: str | None = None
    weakest_area: str | None = None


def _get_or_create_user(db: Session, user_id: str):
    user = None
    try:
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    except ValueError:
        pass

    if user is None:
        email = user_id if "@" in user_id else f"{user_id}@local.gais"
        user = db.query(User).filter(User.email == email).first()

    if user is None:
        email = user_id if "@" in user_id else f"{user_id}@local.gais"
        user = User(email=email)
        db.add(user)
        db.flush()

    return user


def _difficulty_to_int(difficulty):
    if isinstance(difficulty, int):
        return difficulty
    return DIFFICULTIES.index(difficulty)


def _difficulty_to_label(difficulty):
    if isinstance(difficulty, str):
        return difficulty
    return DIFFICULTIES[int(difficulty)]


def _concept_for_question(question: Question):
    return question.topic


def _seed_question(db: Session, encoded_id: int, topic=None, difficulty=None):
    topic = topic or TOPICS[(encoded_id - 1) % len(TOPICS)]
    difficulty_int = _difficulty_to_int(difficulty) if difficulty is not None else (encoded_id - 1) % 3
    question = Question(
        encoded_id=encoded_id,
        topic=topic,
        difficulty=difficulty_int,
        content=f"{topic} practice question {encoded_id}",
        correct_answer="synthetic_answer",
    )
    db.add(question)
    db.flush()
    return question


def _get_or_create_question(db: Session, encoded_id: int, topic=None, difficulty=None):
    question = db.query(Question).filter(Question.encoded_id == encoded_id).first()
    if question is None:
        question = _seed_question(db, encoded_id, topic=topic, difficulty=difficulty)
    return question


def _recent_interactions(db: Session, user: User, limit=50):
    return (
        db.query(Interaction)
        .filter(Interaction.user_id == user.id)
        .order_by(Interaction.timestamp.desc())
        .limit(limit)
        .all()
    )


def _as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _sakt_history(db: Session, user: User):
    rows = (
        db.query(Interaction, Question)
        .join(Question, Interaction.question_id == Question.id)
        .filter(Interaction.user_id == user.id)
        .order_by(Interaction.timestamp.asc())
        .limit(200)
        .all()
    )
    q_seq = [question.encoded_id for _, question in rows if question.encoded_id]
    a_seq = [1.0 if interaction.correct else 0.0 for interaction, question in rows if question.encoded_id]
    return q_seq, a_seq


def _recent_stats(interactions):
    total = len(interactions)
    if total == 0:
        return {
            "retry_count": 0,
            "incorrect_streak": 0,
            "skip_rate": 0.0,
            "session_duration_minutes": 10.0,
            "recent_accuracy": 0.5,
        }

    correct_values = [1.0 if row.correct else 0.0 for row in interactions]
    incorrect_streak = 0
    for row in interactions:
        if row.correct:
            break
        incorrect_streak += 1

    retry_count = min(3, incorrect_streak)
    avg_response_time = sum(row.response_time_ms for row in interactions) / total
    skip_rate = min(0.4, sum(1 for row in interactions if row.response_time_ms < 3_500) / total)
    if total >= 2:
        newest = _as_utc(interactions[0].timestamp)
        oldest = _as_utc(interactions[-1].timestamp)
        session_duration_minutes = max((newest - oldest).total_seconds() / 60.0, 10.0)
    else:
        session_duration_minutes = 10.0

    return {
        "retry_count": retry_count,
        "incorrect_streak": incorrect_streak,
        "skip_rate": skip_rate,
        "session_duration_minutes": min(session_duration_minutes, 90.0),
        "recent_accuracy": sum(correct_values) / total,
        "avg_response_time": avg_response_time,
    }


def _get_or_create_knowledge_state(db: Session, user: User, concept: str):
    state = (
        db.query(KnowledgeState)
        .filter(KnowledgeState.user_id == user.id, KnowledgeState.concept == concept)
        .first()
    )
    if state is None:
        state = KnowledgeState(user_id=user.id, concept=concept)
        db.add(state)
        db.flush()
    return state


def _hours_since(last_reviewed_at):
    if last_reviewed_at is None:
        return 24.0
    now = datetime.now(timezone.utc)
    if last_reviewed_at.tzinfo is None:
        last_reviewed_at = last_reviewed_at.replace(tzinfo=timezone.utc)
    return max((now - last_reviewed_at).total_seconds() / 3600.0, 0.5)


def _state_vector_from_knowledge(db: Session, user: User):
    states = db.query(KnowledgeState).filter(KnowledgeState.user_id == user.id).all()
    interactions = _recent_interactions(db, user, limit=20)
    stats = _recent_stats(interactions)

    if states:
        knowledge_score = sum(s.mastery_probability for s in states) / len(states)
        engagement_score = sum(s.engagement_score for s in states) / len(states)
        confusion_score = sum(s.confusion_score for s in states) / len(states)
        retention_score = sum(s.retention_score for s in states) / len(states)
        recent_accuracy = sum(s.recent_accuracy for s in states) / len(states)
        questions_answered = sum(s.questions_answered for s in states)
        incorrect_streak = max(s.incorrect_streak for s in states)
        session_time = max(s.session_time_minutes for s in states)
    else:
        knowledge_score = 0.5
        engagement_score = 0.5
        confusion_score = 0.2
        retention_score = 0.5
        recent_accuracy = stats["recent_accuracy"]
        questions_answered = len(interactions)
        incorrect_streak = stats["incorrect_streak"]
        session_time = stats["session_duration_minutes"]

    return {
        "knowledge_score": min(max(knowledge_score, 0.0), 1.0),
        "engagement_score": min(max(engagement_score, 0.0), 1.0),
        "confusion_score": min(max(confusion_score, 0.0), 1.0),
        "retention_score": min(max(retention_score, 0.0), 1.0),
        "recent_accuracy": min(max(recent_accuracy, 0.0), 1.0),
        "questions_answered_normalized": min(questions_answered / 100.0, 1.0),
        "session_time_normalized": min(session_time / 90.0, 1.0),
        "incorrect_streak_normalized": min(incorrect_streak / 8.0, 1.0),
    }


def _overall_accuracy(interactions):
    if not interactions:
        return 0.0
    return sum(1 for row in interactions if row.correct) / len(interactions)


def _urgency_from_retention(retention_score):
    if retention_score < 0.55:
        return "high"
    if retention_score < 0.75:
        return "medium"
    return "low"


def _get_or_create_settings(db: Session, user: User):
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings is None:
        settings = UserSettings(
            user_id=user.id,
            target_score=332,
            test_date="March 17, 2026",
        )
        db.add(settings)
        db.flush()
    return settings


def _settings_response(user_id: str, settings: UserSettings):
    return UserSettingsResponse(
        user_id=user_id,
        time_pressure=settings.time_pressure,
        audio_cues=settings.audio_cues,
        daily_session_minutes=settings.daily_session_minutes,
        weekly_summary=settings.weekly_summary,
        target_score=settings.target_score,
        test_date=settings.test_date,
        weakest_area=settings.weakest_area,
    )


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
def submit_answer(req: SubmitAnswerRequest, db: Session = Depends(get_db)):
    models = get_models()
    user = _get_or_create_user(db, req.user_id)
    question = _get_or_create_question(db, req.question_id)
    concept = _concept_for_question(question)

    interaction = Interaction(
        user_id=user.id,
        question_id=question.id,
        correct=req.correct,
        response_time_ms=req.response_time_ms,
        confidence_score=req.confidence_score,
    )
    db.add(interaction)
    db.flush()

    recent = _recent_interactions(db, user, limit=20)
    stats = _recent_stats(recent)
    behaviour_scores = models.behaviour_model.score(
        response_time_ms=req.response_time_ms,
        retry_count=stats["retry_count"],
        incorrect_streak=stats["incorrect_streak"],
        skip_rate=stats["skip_rate"],
        session_duration_minutes=stats["session_duration_minutes"],
        time_of_day_hour=datetime.now().hour,
        recent_accuracy=stats["recent_accuracy"],
    )

    knowledge_state = _get_or_create_knowledge_state(db, user, concept)
    hours_since_review = _hours_since(knowledge_state.last_reviewed_at)
    review_count = max(knowledge_state.review_count + 1, 1)
    recent_accuracy = stats["recent_accuracy"]
    retention_score = models.forgetting_model.predict_retention(
        hours_since_last_review=hours_since_review,
        review_count=review_count,
        average_correctness=min(max(recent_accuracy, 0.3), 1.0),
    )

    q_seq, a_seq = _sakt_history(db, user)
    mastery_probability = models.sakt_model.predict_next(q_seq, a_seq, req.question_id)

    knowledge_state.mastery_probability = mastery_probability
    knowledge_state.engagement_score = behaviour_scores["engagement_score"]
    knowledge_state.confusion_score = behaviour_scores["confusion_score"]
    knowledge_state.retention_score = retention_score
    knowledge_state.recent_accuracy = recent_accuracy
    knowledge_state.review_count = review_count
    knowledge_state.questions_answered += 1
    knowledge_state.incorrect_streak = stats["incorrect_streak"]
    knowledge_state.session_time_minutes = stats["session_duration_minutes"]
    knowledge_state.last_reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return SubmitAnswerResponse(
        user_id=req.user_id,
        question_id=req.question_id,
        engagement_score=behaviour_scores["engagement_score"],
        confusion_score=behaviour_scores["confusion_score"],
        retention_score=round(float(retention_score), 3),
        mastery_probability=round(float(mastery_probability), 4),
    )


@router.get("/next-question", response_model=NextQuestionResponse)
def next_question(user_id: str, db: Session = Depends(get_db)):
    models = get_models()
    user = _get_or_create_user(db, user_id)
    state_vector = _state_vector_from_knowledge(db, user)
    recommendation = models.rl_recommender.recommend(state_vector)

    topic = recommendation["topic"]
    difficulty_label = recommendation["difficulty"]
    difficulty_int = _difficulty_to_int(difficulty_label)

    recent_question_ids = [
        row.question_id
        for row in _recent_interactions(db, user, limit=20)
    ]
    question = (
        db.query(Question)
        .filter(
            Question.topic == topic,
            Question.difficulty == difficulty_int,
            ~Question.id.in_(recent_question_ids) if recent_question_ids else True,
        )
        .order_by(Question.encoded_id.asc())
        .first()
    )

    if question is None:
        max_encoded = db.query(Question.encoded_id).order_by(Question.encoded_id.desc()).first()
        next_encoded = (max_encoded[0] if max_encoded and max_encoded[0] else 0) + 1
        question = _seed_question(db, next_encoded, topic=topic, difficulty=difficulty_int)
        db.commit()

    hint = f"Focus on {topic} fundamentals at {difficulty_label} difficulty."
    return NextQuestionResponse(
        question_id=question.encoded_id,
        content=question.content,
        topic=topic,
        difficulty=difficulty_label,
        hint=hint,
    )


@router.get("/user-progress", response_model=UserProgressResponse)
def user_progress(user_id: str, db: Session = Depends(get_db)):
    user = _get_or_create_user(db, user_id)
    states = (
        db.query(KnowledgeState)
        .filter(KnowledgeState.user_id == user.id)
        .order_by(KnowledgeState.concept.asc())
        .all()
    )
    interactions = (
        db.query(Interaction)
        .filter(Interaction.user_id == user.id)
        .all()
    )

    concepts = [
        ConceptProgress(
            concept=state.concept,
            mastery_probability=round(float(state.mastery_probability), 4),
        )
        for state in states
    ]
    weakest_concepts = sorted(concepts, key=lambda item: item.mastery_probability)[:3]

    return UserProgressResponse(
        user_id=user_id,
        concepts=concepts,
        weakest_concepts=weakest_concepts,
        overall_accuracy=round(_overall_accuracy(interactions), 4),
        total_questions_answered=len(interactions),
    )


@router.get("/recommendation", response_model=RecommendationResponse)
def recommendation(user_id: str, db: Session = Depends(get_db)):
    models = get_models()
    user = _get_or_create_user(db, user_id)
    states = (
        db.query(KnowledgeState)
        .filter(KnowledgeState.user_id == user.id)
        .order_by(KnowledgeState.retention_score.asc(), KnowledgeState.mastery_probability.asc())
        .all()
    )

    study_plan = []
    for state in states[:5]:
        urgency = _urgency_from_retention(state.retention_score)
        if state.retention_score < 0.75:
            action = "revise"
            reason = (
                f"Retention for {state.concept} is {state.retention_score:.2f}, "
                "so a review now should prevent forgetting."
            )
        elif state.mastery_probability < 0.6:
            action = "practice new"
            reason = (
                f"Mastery for {state.concept} is {state.mastery_probability:.2f}; "
                "practice should strengthen this concept."
            )
        else:
            action = "practice new"
            reason = (
                f"{state.concept} is stable enough for a fresh practice question."
            )

        study_plan.append(
            StudyPlanItem(
                topic=state.concept,
                action=action,
                reason=reason,
                urgency=urgency,
            )
        )

    if len(study_plan) < 5:
        state_vector = _state_vector_from_knowledge(db, user)
        rl_choice = models.rl_recommender.recommend(state_vector)
        existing_topics = {item.topic for item in study_plan}
        if rl_choice["topic"] not in existing_topics or not study_plan:
            study_plan.append(
                StudyPlanItem(
                    topic=rl_choice["topic"],
                    action="practice new",
                    reason=(
                        f"The RL recommender selected {rl_choice['topic']} at "
                        f"{rl_choice['difficulty']} difficulty for the current learner state."
                    ),
                    urgency="medium",
                )
            )

    return RecommendationResponse(user_id=user_id, study_plan=study_plan[:5])


@router.get("/plan", response_model=RecommendationResponse)
def plan(user_id: str, db: Session = Depends(get_db)):
    return recommendation(user_id=user_id, db=db)


@router.get("/diagnostic", response_model=DiagnosticResponse)
def diagnostic(user_id: str, db: Session = Depends(get_db)):
    user = _get_or_create_user(db, user_id)
    states = (
        db.query(KnowledgeState)
        .filter(KnowledgeState.user_id == user.id)
        .order_by(KnowledgeState.mastery_probability.asc(), KnowledgeState.retention_score.asc())
        .all()
    )
    interactions = _recent_interactions(db, user, limit=40)
    mistakes = [row for row in interactions if not row.correct]
    stats = _recent_stats(interactions)

    if states:
        weakest = states[0]
        summary = (
            f"{weakest.concept} is the clearest opportunity right now: mastery is "
            f"{weakest.mastery_probability:.0%} and retention is {weakest.retention_score:.0%}."
        )
    else:
        summary = "Answer a few questions and GAIS will start finding reliable patterns."

    findings = []
    if states:
        weakest = states[0]
        findings.append(
            DiagnosticFinding(
                title=f"{weakest.concept} is costing the most points",
                detail=(
                    f"Current mastery is {weakest.mastery_probability:.0%}. "
                    "A short focused block here should improve the next recommendation cycle."
                ),
                severity="high",
            )
        )

        retention_risk = min(states, key=lambda state: state.retention_score)
        findings.append(
            DiagnosticFinding(
                title=f"{retention_risk.concept} is drifting from memory",
                detail=(
                    f"Retention is estimated at {retention_risk.retention_score:.0%}. "
                    "Review this before adding harder material."
                ),
                severity=_urgency_from_retention(retention_risk.retention_score),
            )
        )
    else:
        findings.append(
            DiagnosticFinding(
                title="No stable weakness detected yet",
                detail="Complete one study session so the knowledge tracing and behaviour models have signal.",
                severity="medium",
            )
        )

    if mistakes:
        findings.append(
            DiagnosticFinding(
                title="Recent mistakes are clustering",
                detail=(
                    f"{len(mistakes)} of the last {len(interactions)} answers were incorrect. "
                    f"Your current incorrect streak is {stats['incorrect_streak']}."
                ),
                severity="medium" if stats["incorrect_streak"] < 4 else "high",
            )
        )
    else:
        findings.append(
            DiagnosticFinding(
                title="Accuracy is stable in recent work",
                detail="There are no recent mistakes in the current window, so GAIS is leaning toward fresh practice.",
                severity="low",
            )
        )

    return DiagnosticResponse(user_id=user_id, summary=summary, findings=findings[:3])


@router.get("/mock-test", response_model=MockTestResponse)
def mock_test(user_id: str, db: Session = Depends(get_db)):
    _get_or_create_user(db, user_id)
    section_specs = [
        ("Verbal Reasoning", "Algebra", "easy", 30, 4),
        ("Quantitative Reasoning", "Probability", "medium", 35, 4),
        ("Adaptive Mixed", "Geometry", "hard", 35, 4),
    ]
    sections = []

    for section_index, (title, topic, difficulty, minutes, count) in enumerate(section_specs):
        difficulty_int = _difficulty_to_int(difficulty)
        questions = (
            db.query(Question)
            .filter(Question.topic == topic, Question.difficulty == difficulty_int)
            .order_by(Question.encoded_id.asc())
            .limit(count)
            .all()
        )
        while len(questions) < count:
            max_encoded = db.query(Question.encoded_id).order_by(Question.encoded_id.desc()).first()
            next_encoded = (max_encoded[0] if max_encoded and max_encoded[0] else 0) + 1
            questions.append(_seed_question(db, next_encoded, topic=topic, difficulty=difficulty_int))

        sections.append(
            MockTestSection(
                title=title,
                duration_minutes=minutes,
                questions=[
                    MockTestQuestion(
                        question_id=question.encoded_id,
                        content=question.content,
                        topic=question.topic,
                        difficulty=_difficulty_to_label(question.difficulty),
                    )
                    for question in questions[:count]
                ],
            )
        )

    db.commit()
    return MockTestResponse(user_id=user_id, sections=sections)


@router.get("/settings", response_model=UserSettingsResponse)
def get_settings(user_id: str, db: Session = Depends(get_db)):
    user = _get_or_create_user(db, user_id)
    settings = _get_or_create_settings(db, user)
    db.commit()
    return _settings_response(user_id, settings)


@router.put("/settings", response_model=UserSettingsResponse)
def update_settings(user_id: str, update: UserSettingsUpdate, db: Session = Depends(get_db)):
    user = _get_or_create_user(db, user_id)
    settings = _get_or_create_settings(db, user)
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return _settings_response(user_id, settings)


@router.post("/onboarding", response_model=UserSettingsResponse)
def onboarding(user_id: str, update: UserSettingsUpdate, db: Session = Depends(get_db)):
    user = _get_or_create_user(db, user_id)
    settings = _get_or_create_settings(db, user)
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return _settings_response(user_id, settings)
