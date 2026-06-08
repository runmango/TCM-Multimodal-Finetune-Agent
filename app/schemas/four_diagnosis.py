from typing import Dict, Optional

from pydantic import BaseModel, Field


class InspectionData(BaseModel):
    """望诊数据。第一版允许人工标签或 mock 标签为空。"""

    tongue_image_url: Optional[str] = None
    tongue_color: Optional[str] = None
    tongue_coating: Optional[str] = None
    teeth_marks: Optional[bool] = None
    tongue_shape: Optional[str] = None
    complexion: Optional[str] = None
    body_shape: Optional[str] = None
    skin: Optional[str] = None
    spirit: Optional[str] = None


class AuscultationOlfactionData(BaseModel):
    """闻诊数据。"""

    voice: Optional[str] = None
    breath: Optional[str] = None
    cough: Optional[str] = None
    odor: Optional[str] = None


class InquiryData(BaseModel):
    """问诊数据，保留原始问卷分数方便追溯。"""

    fatigue: Optional[int] = Field(None, ge=1, le=5)
    shortness_of_breath: Optional[int] = Field(None, ge=1, le=5)
    spontaneous_sweating: Optional[int] = Field(None, ge=1, le=5)
    easy_cold: Optional[int] = Field(None, ge=1, le=5)
    cold_intolerance: Optional[int] = Field(None, ge=1, le=5)
    sleep_quality: Optional[int] = Field(None, ge=1, le=5)
    diet_regular: Optional[int] = Field(None, ge=1, le=5)
    stool_regular: Optional[int] = Field(None, ge=1, le=5)
    mood_stability: Optional[int] = Field(None, ge=1, le=5)
    raw_answers: Dict[str, int] = Field(default_factory=dict)


class PalpationData(BaseModel):
    """切诊数据。"""

    pulse_type: Optional[str] = None
    pulse_rate: Optional[str] = None
    pulse_strength: Optional[str] = None
    abdominal_exam: Optional[str] = None


class FourDiagnosisData(BaseModel):
    inspection: InspectionData = Field(default_factory=InspectionData)
    auscultation_olfaction: AuscultationOlfactionData = Field(default_factory=AuscultationOlfactionData)
    inquiry: InquiryData = Field(default_factory=InquiryData)
    palpation: PalpationData = Field(default_factory=PalpationData)
