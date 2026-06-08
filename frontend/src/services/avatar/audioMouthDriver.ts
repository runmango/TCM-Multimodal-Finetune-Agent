export class AudioMouthDriver {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private dataArray: Uint8Array<ArrayBuffer> | null = null;
  private source: MediaElementAudioSourceNode | null = null;
  private mouthOpen = 0;

  attach(audioElement: HTMLAudioElement | null): void {
    if (!audioElement || this.source) return;

    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextCtor) return;

    try {
      this.audioContext = new AudioContextCtor();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.68;
      this.dataArray = new Uint8Array(new ArrayBuffer(this.analyser.frequencyBinCount));
      audioElement.crossOrigin = "anonymous";
      this.source = this.audioContext.createMediaElementSource(audioElement);
      this.source.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
    } catch (error) {
      this.dispose();
    }
  }

  async resume(): Promise<void> {
    if (this.audioContext?.state === "suspended") {
      await this.audioContext.resume().catch(() => undefined);
    }
  }

  update(speaking: boolean): number {
    if (!speaking || !this.analyser || !this.dataArray) {
      this.mouthOpen = this.smooth(this.mouthOpen, 0, 0.18);
      return this.mouthOpen;
    }

    this.analyser.getByteFrequencyData(this.dataArray);
    const sampleCount = Math.min(48, this.dataArray.length);
    let total = 0;
    for (let index = 0; index < sampleCount; index += 1) {
      total += this.dataArray[index];
    }
    const average = total / sampleCount;
    const normalizedVolume = Math.max(0, Math.min(1, (average - 8) / 80));
    this.mouthOpen = this.smooth(this.mouthOpen, normalizedVolume, 0.34);
    return this.mouthOpen;
  }

  dispose(): void {
    this.source?.disconnect();
    this.analyser?.disconnect();
    if (this.audioContext && this.audioContext.state !== "closed") {
      void this.audioContext.close();
    }
    this.source = null;
    this.analyser = null;
    this.dataArray = null;
    this.audioContext = null;
    this.mouthOpen = 0;
  }

  private smooth(previous: number, next: number, amount: number): number {
    return previous + (next - previous) * amount;
  }
}

declare global {
  interface Window {
    webkitAudioContext?: typeof AudioContext;
  }
}
