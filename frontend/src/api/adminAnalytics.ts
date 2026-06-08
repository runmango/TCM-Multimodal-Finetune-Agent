import { DEFAULT_API_BASE_URL, normalizeBaseUrl, type ApiFriendlyError } from "@/api/tcmApi";
import type {
  AnalyticsSummary,
  DistributionResponse,
  RecordDetail,
  RecordListResponse,
} from "@/types/adminRecords";

export interface RecordListParams {
  limit?: number;
  offset?: number;
  primary_constitution?: string;
  date_from?: string;
  date_to?: string;
}

function buildApiUrl(baseUrl: string | undefined, path: string): string {
  return `${normalizeBaseUrl(baseUrl || DEFAULT_API_BASE_URL)}${path}`;
}

function normalizeError(error: unknown): ApiFriendlyError {
  if (error && typeof error === "object" && "message" in error) {
    return error as ApiFriendlyError;
  }
  return {
    message: "后端连接失败，请确认 FastAPI 服务是否已启动。",
    detail: String(error),
  };
}

async function requestJson<T>(baseUrl: string | undefined, path: string): Promise<T> {
  try {
    const response = await fetch(buildApiUrl(baseUrl, path), {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};
    if (!response.ok) {
      throw {
        message: response.status === 404 ? "记录不存在或接口未找到。" : "后端接口返回异常。",
        status: response.status,
        detail: data,
        url: path,
      } satisfies ApiFriendlyError;
    }
    return data as T;
  } catch (error) {
    throw normalizeError(error);
  }
}

export function getAnalyticsSummary(baseUrl?: string): Promise<AnalyticsSummary> {
  return requestJson<AnalyticsSummary>(baseUrl, "/api/v1/constitution/analytics/summary");
}

export function getConstitutionDistribution(baseUrl?: string): Promise<DistributionResponse> {
  return requestJson<DistributionResponse>(baseUrl, "/api/v1/constitution/analytics/distribution");
}

export function getRecords(params: RecordListParams, baseUrl?: string): Promise<RecordListResponse> {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  if (params.primary_constitution) query.set("primary_constitution", params.primary_constitution);
  if (params.date_from) query.set("date_from", params.date_from);
  if (params.date_to) query.set("date_to", params.date_to);
  return requestJson<RecordListResponse>(baseUrl, `/api/v1/constitution/records?${query.toString()}`);
}

export function getRecordDetail(sessionId: string, baseUrl?: string): Promise<RecordDetail> {
  return requestJson<RecordDetail>(baseUrl, `/api/v1/constitution/records/${encodeURIComponent(sessionId)}`);
}
