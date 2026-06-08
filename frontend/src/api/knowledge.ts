import { DEFAULT_API_BASE_URL, normalizeBaseUrl, type ApiFriendlyError } from "@/api/tcmApi";

export interface KnowledgeSource {
  source_type: string;
  source_id: string;
  title?: string | null;
  score?: number | null;
}

export interface KnowledgeAskResponse {
  answer: string;
  sources: KnowledgeSource[];
  safety_notice: string;
}

function buildApiUrl(baseUrl: string | undefined, path: string): string {
  return `${normalizeBaseUrl(baseUrl || DEFAULT_API_BASE_URL)}${path}`;
}

function normalizeError(error: unknown): ApiFriendlyError {
  if (error && typeof error === "object" && "message" in error) {
    return error as ApiFriendlyError;
  }
  return {
    message: "知识问答接口请求失败，请检查后端服务和端口配置。",
    detail: String(error),
  };
}

export async function askKnowledge(query: string, topK = 3, baseUrl?: string): Promise<KnowledgeAskResponse> {
  try {
    const response = await fetch(buildApiUrl(baseUrl, "/api/v1/knowledge/ask"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        Accept: "application/json",
      },
      body: JSON.stringify({ query, top_k: topK, backend: "rule" }),
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};

    if (!response.ok) {
      throw {
        message: response.status === 404 ? "知识问答接口不存在，请检查后端入口。" : "知识问答接口返回异常。",
        status: response.status,
        detail: data,
        url: "/api/v1/knowledge/ask",
      } satisfies ApiFriendlyError;
    }

    return data as KnowledgeAskResponse;
  } catch (error) {
    throw normalizeError(error);
  }
}
