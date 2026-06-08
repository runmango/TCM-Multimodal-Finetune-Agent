import type { DigitalHumanSubtitle } from "@/api/digitalHuman";

export type AvatarStatus = "idle" | "thinking" | "speaking" | "finished" | "error";

export type DigitalHumanScene = "constitution_result" | "knowledge_answer" | "general_notice";

export interface AvatarStageState {
  status: AvatarStatus;
  label: string;
  description: string;
}

export type { DigitalHumanSubtitle };
