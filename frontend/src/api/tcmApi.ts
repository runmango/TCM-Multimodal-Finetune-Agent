import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";

export const DEFAULT_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8010";

export interface RAGRequest {
  query: string;
  top_k: number;
}

export interface EvidenceItem {
  id?: string;
  title?: string;
  content?: string;
  tags?: string[];
  score?: number | string;
  source_type?: string;
  source_id?: string;
  type?: string;
  [key: string]: unknown;
}

export interface RAGResponse {
  query?: string;
  results?: EvidenceItem[];
  [key: string]: unknown;
}

export interface InferenceResponse {
  query?: string;
  constitution?: string;
  constitution_type?: string;
  result?: string;
  type?: string;
  confidence?: number | string;
  analysis?: string;
  conclusion?: string;
  answer?: string;
  symptoms?: string[];
  evidence?: EvidenceItem[];
  references?: EvidenceItem[];
  results?: EvidenceItem[];
  safety?: Record<string, unknown>;
  disclaimer?: string;
  [key: string]: unknown;
}

export interface DatasetBuildResponse {
  status?: string;
  summary?: Record<string, unknown>;
  exports?: Record<string, string>;
  report_path?: string;
  [key: string]: unknown;
}

export interface ApiFriendlyError {
  message: string;
  status?: number;
  detail?: unknown;
  url?: string;
}

export interface BackendStatus {
  connected: boolean;
  message: string;
  endpoint?: string;
  data?: unknown;
  error?: ApiFriendlyError;
}

export function normalizeBaseUrl(baseUrl?: string): string {
  const value = (baseUrl || DEFAULT_API_BASE_URL).trim();
  return value === "/" ? "" : value.replace(/\/+$/, "");
}

function createClient(baseUrl?: string): AxiosInstance {
  return axios.create({
    baseURL: normalizeBaseUrl(baseUrl),
    timeout: 10000,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      Accept: "application/json",
    },
  });
}

function normalizeApiError(error: unknown): ApiFriendlyError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    const status = axiosError.response?.status;
    const url = axiosError.config?.url;
    const detail = axiosError.response?.data || axiosError.message;

    if (!axiosError.response) {
      return {
        message: "后端未启动或网络连接失败，请先启动 FastAPI 服务。",
        detail,
        url,
      };
    }

    if (status === 404) {
      return { message: "接口不存在，请检查端口和路由配置。", status, detail, url };
    }

    if (status && status >= 500) {
      return { message: "后端服务内部错误，请查看 FastAPI 日志。", status, detail, url };
    }

    return { message: "后端接口返回异常。", status, detail, url };
  }

  return {
    message: "请求处理失败，可能是 JSON 解析失败或浏览器网络异常。",
    detail: String(error),
  };
}

async function requestWithHandling<T>(baseUrl: string | undefined, config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await createClient(baseUrl).request<T>(config);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function checkBackend(baseUrl?: string): Promise<BackendStatus> {
  try {
    const health = await requestWithHandling<unknown>(baseUrl, { method: "GET", url: "/api/v1/health", timeout: 2500 });
    return {
      connected: true,
      message: "后端已连接",
      endpoint: "/api/v1/health",
      data: health,
    };
  } catch (healthError) {
    try {
      const docs = await requestWithHandling<string>(baseUrl, {
        method: "GET",
        url: "/docs",
        timeout: 2500,
        headers: { Accept: "text/html,application/json" },
      });
      return {
        connected: true,
        message: "后端已连接",
        endpoint: "/docs",
        data: typeof docs === "string" ? "FastAPI docs is reachable" : docs,
      };
    } catch (docsError) {
      return {
        connected: false,
        message: "后端未连接，请先启动 FastAPI 服务。",
        error: {
          message: "后端状态检测失败。",
          detail: { healthError, docsError },
        },
      };
    }
  }
}

export function searchRag(payload: RAGRequest, baseUrl?: string): Promise<RAGResponse> {
  return requestWithHandling<RAGResponse>(baseUrl, {
    method: "POST",
    url: "/api/v1/rag/search",
    data: payload,
  });
}

export function inferConstitution(payload: RAGRequest, baseUrl?: string): Promise<InferenceResponse> {
  return requestWithHandling<InferenceResponse>(baseUrl, {
    method: "POST",
    url: "/api/v1/infer/constitution",
    data: payload,
  });
}

export function buildDataset(baseUrl?: string): Promise<DatasetBuildResponse> {
  return requestWithHandling<DatasetBuildResponse>(baseUrl, {
    method: "POST",
    url: "/api/v1/dataset/build",
    data: {},
  });
}

export function asList<T = unknown>(value: unknown): T[] {
  if (value == null) return [];
  if (Array.isArray(value)) return value as T[];
  return [value as T];
}

export function pickText(record: Record<string, unknown> | null | undefined, keys: string[], fallback = "-"): string {
  if (!record) return fallback;
  for (const key of keys) {
    const value = record[key];
    if (value == null) continue;
    if (Array.isArray(value)) {
      const text = value.map((item) => String(item)).filter(Boolean).join("、");
      if (text) return text;
      continue;
    }
    if (typeof value === "object") continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return fallback;
}

export function collectReferenceItems(data: InferenceResponse | RAGResponse | null): EvidenceItem[] {
  if (!data) return [];
  const source = data.results || (data as InferenceResponse).evidence || (data as InferenceResponse).references || [];
  return asList<EvidenceItem>(source).filter((item) => item && typeof item === "object");
}

export function looksLikeMojibake(payload: unknown): boolean {
  const text = typeof payload === "string" ? payload : JSON.stringify(payload || "");
  if (!text) return false;
  return /�|Ã|Â|ä|å|æ|ç|è|é|涓|鎴|璇|涔|绯|鐭|浣/.test(text);
}

