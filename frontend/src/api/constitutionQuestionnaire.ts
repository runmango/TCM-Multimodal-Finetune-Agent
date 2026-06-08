import { DEFAULT_API_BASE_URL, normalizeBaseUrl, type ApiFriendlyError } from "@/api/tcmApi";

export interface QuestionnaireQuestion {
  id: string;
  text: string;
  constitution: string;
  reverse: boolean;
  applies_to?: "male" | "female" | null;
}

export interface QuestionOption {
  label: string;
  score: number;
}

export interface QuestionnaireResponse {
  questions: QuestionnaireQuestion[];
  options: QuestionOption[];
}

export interface TongueFeatures {
  tongue_color?: string | null;
  tongue_coating?: string | null;
  teeth_marks?: boolean | null;
  tongue_shape?: string | null;
}

export interface InspectionData {
  tongue_image_url?: string | null;
  tongue_color?: string | null;
  tongue_coating?: string | null;
  teeth_marks?: boolean | null;
  tongue_shape?: string | null;
  complexion?: string | null;
  body_shape?: string | null;
  skin?: string | null;
  spirit?: string | null;
}

export interface AuscultationOlfactionData {
  voice?: string | null;
  breath?: string | null;
  cough?: string | null;
  odor?: string | null;
}

export interface InquiryData {
  fatigue?: number | null;
  shortness_of_breath?: number | null;
  spontaneous_sweating?: number | null;
  easy_cold?: number | null;
  cold_intolerance?: number | null;
  sleep_quality?: number | null;
  diet_regular?: number | null;
  stool_regular?: number | null;
  mood_stability?: number | null;
  raw_answers: Record<string, number>;
}

export interface PalpationData {
  pulse_type?: string | null;
  pulse_rate?: string | null;
  pulse_strength?: string | null;
  abdominal_exam?: string | null;
}

export interface FourDiagnosisData {
  inspection: InspectionData;
  auscultation_olfaction: AuscultationOlfactionData;
  inquiry: InquiryData;
  palpation: PalpationData;
}

export interface QuestionnaireRAGSource {
  source_type: string;
  source_id: string;
  title?: string | null;
  score?: number | null;
}

export interface QuestionnaireSubmitRequest {
  answers: Array<{ question_id: string; score: number }>;
  tongue_image_url?: string | null;
  tongue_features?: TongueFeatures | null;
  top_k?: number;
  gender?: "unknown" | "male" | "female";
}

export interface QuestionnaireSubmitResponse {
  session_id: string;
  primary_constitution: string;
  secondary_constitutions: string[];
  scores: Record<string, number>;
  constitution_judgements: Record<string, string>;
  algorithm_version: string;
  retriever_type: string;
  result_text: string;
  safety_notice: string;
  four_diagnosis: FourDiagnosisData;
  rag_explanation: string;
  rag_sources: QuestionnaireRAGSource[];
  broadcast_text: string;
}

export interface TongueUploadResponse {
  url: string;
  filename: string;
  content_type: string;
  size: number;
}

function buildApiUrl(baseUrl: string | undefined, path: string): string {
  return `${normalizeBaseUrl(baseUrl || DEFAULT_API_BASE_URL)}${path}`;
}

function normalizeError(error: unknown): ApiFriendlyError {
  if (error && typeof error === "object" && "message" in error) {
    return error as ApiFriendlyError;
  }
  return {
    message: "体质问卷接口请求失败，请检查后端服务和端口配置。",
    detail: String(error),
  };
}

export async function getQuestionnaire(baseUrl?: string): Promise<QuestionnaireResponse> {
  try {
    const response = await fetch(buildApiUrl(baseUrl, "/api/v1/constitution/questionnaire"), {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};

    if (!response.ok) {
      throw {
        message: response.status === 404 ? "体质问卷接口不存在，请检查后端入口。" : "体质问卷接口返回异常。",
        status: response.status,
        detail: data,
        url: "/api/v1/constitution/questionnaire",
      } satisfies ApiFriendlyError;
    }

    return data as QuestionnaireResponse;
  } catch (error) {
    throw normalizeError(error);
  }
}

export async function submitQuestionnaire(
  payload: QuestionnaireSubmitRequest | Array<{ question_id: string; score: number }>,
  baseUrl?: string,
): Promise<QuestionnaireSubmitResponse> {
  const requestBody = Array.isArray(payload) ? { answers: payload } : payload;
  try {
    const response = await fetch(buildApiUrl(baseUrl, "/api/v1/constitution/full-infer"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        Accept: "application/json",
      },
      body: JSON.stringify(requestBody),
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};

    if (!response.ok) {
      throw {
        message: response.status === 404 ? "体质完整辨识接口不存在，请检查后端入口。" : "体质问卷提交失败。",
        status: response.status,
        detail: data,
        url: "/api/v1/constitution/full-infer",
      } satisfies ApiFriendlyError;
    }

    return data as QuestionnaireSubmitResponse;
  } catch (error) {
    throw normalizeError(error);
  }
}

export async function uploadTongueImage(file: File, baseUrl?: string): Promise<TongueUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(buildApiUrl(baseUrl, "/api/v1/uploads/tongue"), {
      method: "POST",
      headers: { Accept: "application/json" },
      body: formData,
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};

    if (!response.ok) {
      throw {
        message: response.status === 404 ? "舌象上传接口不存在，请检查后端入口。" : "舌象图片上传失败。",
        status: response.status,
        detail: data,
        url: "/api/v1/uploads/tongue",
      } satisfies ApiFriendlyError;
    }

    return data as TongueUploadResponse;
  } catch (error) {
    throw normalizeError(error);
  }
}
