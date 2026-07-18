// Contador de sequência de dias praticados, persistido em localStorage.
// Incrementa no máximo uma vez por dia civil (America ou fuso local do device).

const CHAVE = "lingua_streak_v1";

interface EstadoStreak {
  ultimaData: string; // YYYY-MM-DD
  dias: number;
}

function hojeIso(): string {
  const agora = new Date();
  const ano = agora.getFullYear();
  const mes = String(agora.getMonth() + 1).padStart(2, "0");
  const dia = String(agora.getDate()).padStart(2, "0");
  return `${ano}-${mes}-${dia}`;
}

function lerEstado(): EstadoStreak {
  try {
    const bruto = localStorage.getItem(CHAVE);
    if (!bruto) return { ultimaData: "", dias: 0 };
    const parsed = JSON.parse(bruto) as EstadoStreak;
    if (typeof parsed.dias !== "number" || typeof parsed.ultimaData !== "string") {
      return { ultimaData: "", dias: 0 };
    }
    return parsed;
  } catch {
    return { ultimaData: "", dias: 0 };
  }
}

/** Lê o streak atual sem modificá-lo. */
export function obterStreak(): number {
  return lerEstado().dias;
}

/**
 * Registra uma ação de prática. Se ainda não houve registro hoje, incrementa
 * o contador em 1. Chamadas repetidas no mesmo dia são no-ops.
 */
export function registrarPratica(): number {
  const estado = lerEstado();
  const hoje = hojeIso();
  if (estado.ultimaData === hoje) {
    return estado.dias;
  }
  const novoEstado: EstadoStreak = { ultimaData: hoje, dias: estado.dias + 1 };
  localStorage.setItem(CHAVE, JSON.stringify(novoEstado));
  return novoEstado.dias;
}
