export interface TalkResponse {
  text: string;
  constitution: string;
  audio_url: string | null;
  avatar: {
    closed: string;
    open: string;
    status: string;
  };
  subtitles: Array<{ start: number; end: number; text: string }>;
  safety_notice: string;
  tts_status: string;
  message?: string | null;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8010";

export async function talk(query: string, voice = "zh-CN-XiaoxiaoNeural"): Promise<TalkResponse> {
  const response = await fetch(`${API_BASE}/api/v1/digital-human/talk`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      Accept: "application/json",
    },
    body: JSON.stringify({ query, voice }),
  });
  if (!response.ok) {
    throw new Error(`接口请求失败：${response.status}`);
  }
  return response.json();
}

export function staticUrl(path: string | null): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

