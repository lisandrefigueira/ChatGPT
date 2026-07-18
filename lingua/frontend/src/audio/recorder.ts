// Wrapper simples sobre MediaRecorder: start/stop retornando um Blob (webm/opus).

function escolherMimeType(): string {
  const candidatos = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
  ];
  for (const tipo of candidatos) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported?.(tipo)) {
      return tipo;
    }
  }
  return "";
}

export class GravadorAudio {
  private mediaRecorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private pedacos: Blob[] = [];
  private mimeType = "";

  async iniciar(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.mimeType = escolherMimeType();
    this.pedacos = [];
    this.mediaRecorder = new MediaRecorder(
      this.stream,
      this.mimeType ? { mimeType: this.mimeType } : undefined,
    );
    this.mediaRecorder.ondataavailable = (evento: BlobEvent) => {
      if (evento.data.size > 0) this.pedacos.push(evento.data);
    };
    this.mediaRecorder.start();
  }

  /** Para a gravação e resolve com o Blob final (webm/opus). */
  parar(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const gravador = this.mediaRecorder;
      if (!gravador) {
        reject(new Error("Gravação não foi iniciada."));
        return;
      }
      gravador.onstop = () => {
        const tipoFinal = this.mimeType || "audio/webm";
        const blob = new Blob(this.pedacos, { type: tipoFinal });
        this.liberarStream();
        resolve(blob);
      };
      if (gravador.state === "inactive") {
        gravador.onstop(new Event("stop"));
        return;
      }
      gravador.stop();
    });
  }

  cancelar(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    this.liberarStream();
  }

  private liberarStream(): void {
    this.stream?.getTracks().forEach((faixa) => faixa.stop());
    this.stream = null;
    this.mediaRecorder = null;
  }
}
