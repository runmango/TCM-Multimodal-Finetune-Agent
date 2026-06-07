import { DEFAULT_API_BASE_URL, normalizeBaseUrl, type ApiFriendlyError } from "@/api/tcmApi";

export interface TtsResponse {
  audio_url?: string | null;
  text: string;
  tts_status: string;
  message?: string | null;
}

export async function generateTts(
  text: string,
  voice = "zh-CN-XiaoxiaoNeural",
  baseUrl?: string,
): Promise<TtsResponse> {
  try {
    const response = await fetch(`${normalizeBaseUrl(baseUrl || DEFAULT_API_BASE_URL)}/api/v1/tts/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        Accept: "application/json",
      },
      body: JSON.stringify({ text, voice }),
    });

    const raw = await response.text();
    const data = raw ? JSON.parse(raw) : {};
    if (!response.ok) {
      throw {
        message: response.status === 404 ? "TTS 接口不存在，请检查后端入口。" : "TTS 接口返回异常。",
        status: response.status,
        detail: data,
        url: "/api/v1/tts/generate",
      } satisfies ApiFriendlyError;
    }

    return data as TtsResponse;
  } catch (error) {
    if (error && typeof error === "object" && "message" in error) {
      throw error;
    }
    throw {
      message: "TTS 请求失败，请检查后端服务、端口或网络。",
      detail: String(error),
    } satisfies ApiFriendlyError;
  }
}
