export interface RecordSummary {
  session_id: string;
  created_at: string;
  primary_constitution: string;
  secondary_constitutions: string[];
  algorithm_version: string;
  retriever_type: string;
  fallback_used: boolean;
  tongue_image_url?: string | null;
}

export interface RecordListResponse {
  total: number;
  limit: number;
  offset: number;
  items: RecordSummary[];
  records?: RecordSummary[];
}

export interface AnalyticsSummary {
  total_records: number;
  today_records: number;
  tongue_upload_count: number;
  rag_success_count: number;
  rag_fallback_count: number;
  digital_human_text_count: number;
}

export interface ConstitutionDistributionItem {
  name: string;
  count: number;
}

export interface DistributionResponse {
  constitution_distribution: ConstitutionDistributionItem[];
}

export interface FourDiagnosisData {
  inspection: Record<string, unknown>;
  auscultation_olfaction: Record<string, unknown>;
  inquiry: Record<string, unknown>;
  palpation: Record<string, unknown>;
}

export interface RagSource {
  source?: string | null;
  section?: string | null;
  chunk_id?: string | null;
  text?: string | null;
  title?: string | null;
  source_type?: string | null;
  source_id?: string | null;
  score?: number | null;
}

export interface RagTrace {
  query: string;
  top_k: number;
  sources: RagSource[];
  retriever_type: string;
  fallback_used: boolean;
  created_at: string;
}

export interface RecordDetail extends RecordSummary {
  scores: Record<string, number>;
  constitution_judgements: Record<string, string>;
  rag_explanation: string;
  rag_sources: RagSource[];
  rag_traces?: RagTrace[];
  broadcast_text: string;
  safety_disclaimer?: string;
  four_diagnosis?: FourDiagnosisData;
  tongue_features?: Record<string, unknown>;
}
