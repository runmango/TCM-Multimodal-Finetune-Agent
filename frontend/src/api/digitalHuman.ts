import { DEFAULT_API_BASE_URL, normalizeBaseUrl, type ApiFriendlyError } from "@/api/tcmApi";

export interface DigitalHumanSubtitle {
  start: number;
  end: number;
  text: string;
}

export interface DigitalHumanResponse {
  scene: "constitution_result" | "knowledge_answer" | "general_notice";
  text: string;
  audio_url?: string | null;
  avatar: {
    closed: string;
    open: string;
    status: string;
  };
  subtitles: DigitalHumanSubtitle[];
  safety_notice: string;
  tts_status?: string;
  message?: string | null;
}

function buildApiUrl(baseUrl: string | undefined, path: string): string {
  return `${normalizeBaseUrl(baseUrl || DEFAULT_API_BASE_URL)}${path}`;
}

function normalizeDigitalHumanError(error: unknown): ApiFriendlyError {
  if (error && typeof error === "object" && "message" in error) {
    return error as ApiFriendlyError;
  }

  return {
    message: "数字人接口请求失败，请检查后端服务、端口或 CORS 配置。",
    detail: String(error),
  };
}

export function resolveBackendAssetUrl(path: string | null | undefined, baseUrl?: string): string {
  if (!path) return "";
  if (/^(https?:)?\/\//.test(path) || path.startsWith("data:")) return path;
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizeBaseUrl(baseUrl || DEFAULT_API_BASE_URL)}${cleanPath}`;
}

export async function talkToDigitalHuman(
  query: string,
  voice = "zh-CN-XiaoxiaoNeural",
  baseUrl?: string,
): Promise<DigitalHumanResponse> {
  try {
    const response = await fetch(buildApiUrl(baseUrl, "/api/v1/digital-human/talk"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        Accept: "application/json",
      },
      body: JSON.stringify({ query, voice }),
    });

    const text = await response.text();
    const data = text ? JSON.parse(text) : {};

    if (!response.ok) {
      throw {
        message: response.status === 404 ? "数字人接口不存在，请检查后端入口。" : "数字人接口返回异常。",
        status: response.status,
        detail: data,
        url: "/api/v1/digital-human/talk",
      } satisfies ApiFriendlyError;
    }

    return data as DigitalHumanResponse;
  } catch (error) {
    throw normalizeDigitalHumanError(error);
  }
}

export async function speakWithDigitalHuman(
  scene: "constitution_result" | "knowledge_answer" | "general_notice",
  text: string,
  voice = "zh-CN-XiaoxiaoNeural",
  baseUrl?: string,
): Promise<DigitalHumanResponse> {
  try {
    const response = await fetch(buildApiUrl(baseUrl, "/api/v1/digital-human/speak"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        Accept: "application/json",
      },
      body: JSON.stringify({ scene, text, voice }),
    });

    const responseText = await response.text();
    const data = responseText ? JSON.parse(responseText) : {};

    if (!response.ok) {
      throw {
        message: response.status === 404 ? "数字人播报接口不存在，请检查后端入口。" : "数字人播报接口返回异常。",
        status: response.status,
        detail: data,
        url: "/api/v1/digital-human/speak",
      } satisfies ApiFriendlyError;
    }

    return data as DigitalHumanResponse;
  } catch (error) {
    throw normalizeDigitalHumanError(error);
  }
}
