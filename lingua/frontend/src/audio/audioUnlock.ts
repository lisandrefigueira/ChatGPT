// Desbloqueio de áudio para iOS/Android: o primeiro toque do usuário numa sessão
// precisa chamar audioContext.resume() de forma SÍNCRONA dentro do handler do
// toque, antes de qualquer `await`, senão o autoplay de áudio fica bloqueado
// no Safari iOS (e em navegadores mobile em geral).

let audioContextCompartilhado: AudioContext | null = null;
let desbloqueado = false;

function obterAudioContext(): AudioContext {
  if (!audioContextCompartilhado) {
    const AudioContextCtor =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    audioContextCompartilhado = new AudioContextCtor();
  }
  return audioContextCompartilhado;
}

/**
 * Deve ser chamada de forma síncrona dentro de um handler de clique/toque
 * (onClick, onPointerDown etc.) — NUNCA depois de um `await`.
 */
export function desbloquearAudio(): void {
  const ctx = obterAudioContext();
  if (ctx.state === "suspended") {
    void ctx.resume();
  }
  desbloqueado = true;
}

export function audioJaDesbloqueado(): boolean {
  return desbloqueado;
}

export function getAudioContextCompartilhado(): AudioContext {
  return obterAudioContext();
}
