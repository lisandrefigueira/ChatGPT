// Toca um Blob de áudio (MP3 retornado por /api/tts) via elemento <audio>,
// revogando a blob URL ao final para não vazar memória.

export async function tocarBlobAudio(blob: Blob): Promise<void> {
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  try {
    await audio.play();
  } finally {
    audio.addEventListener("ended", () => URL.revokeObjectURL(url));
    audio.addEventListener("error", () => URL.revokeObjectURL(url));
  }
}
