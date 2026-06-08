from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.four_diagnosis import FourDiagnosisData


class QuestionOption(BaseModel):
    label: str
    score: int = Field(..., ge=1, le=5)


class QuestionnaireQuestion(BaseModel):
    id: str
    text: str
    constitution: str
    reverse: bool = False
    applies_to: Optional[Literal["male", "female"]] = None


class QuestionnaireResponse(BaseModel):
    questions: List[QuestionnaireQuestion]
    options: List[QuestionOption]


class QuestionnaireAnswer(BaseModel):
    question_id: str
    score: int = Field(..., ge=1, le=5)


class TongueFeatures(BaseModel):
    tongue_color: Optional[str] = None
    tongue_coating: Optional[str] = None
    teeth_marks: Optional[bool] = None
    tongue_shape: Optional[str] = None


class QuestionnaireSubmitRequest(BaseModel):
    answers: List[QuestionnaireAnswer]
    tongue_image_url: Optional[str] = None
    tongue_features: Optional[TongueFeatures] = None
    top_k: int = Field(3, ge=1, le=10)
    gender: Literal["unknown", "male", "female"] = "unknown"


class QuestionnaireRAGSource(BaseModel):
    source_type: str
    source_id: str
    title: Optional[str] = None
    score: Optional[float] = None


class QuestionnaireSubmitResponse(BaseModel):
    session_id: str
    primary_constitution: str
    secondary_constitutions: List[str]
    scores: Dict[str, float]
    constitution_judgements: Dict[str, str]
    algorithm_version: str
    retriever_type: str
    result_text: str
    safety_notice: str
    four_diagnosis: FourDiagnosisData
    rag_explanation: str
    rag_sources: List[QuestionnaireRAGSource]
    broadcast_text: str
