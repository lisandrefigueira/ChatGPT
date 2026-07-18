// Wrapper fino de fetch para o backend Lingua. Tipado contra src/types.ts.
import type {
  AvaliarPronunciaResponse,
  ConversaRequest,
  ConversaResponse,
  CorrigirRequest,
  CorrigirResponse,
  CustosResponse,
  STTResponse,
  Trilha,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");
const APP_TOKEN = import.meta.env.VITE_APP_TOKEN || "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function authHeaders(): HeadersInit {
  return { "X-App-Token": APP_TOKEN };
}

async function assertOk(res: Response): Promise<Response> {
  if (!res.ok) {
    let detalhe = res.statusText;
    try {
      const corpo = await res.text();
      if (corpo) detalhe = corpo;
    } catch {
      // ignora falha ao ler corpo do erro
    }
    throw new ApiError(res.status, `Falha na API (${res.status}): ${detalhe}`);
  }
  return res;
}

async function getJson<T>(caminho: string): Promise<T> {
  const res = await fetch(`${API_BASE}${caminho}`, { headers: authHeaders() });
  await assertOk(res);
  return (await res.json()) as T;
}

async function postJson<TReq, TRes>(caminho: string, corpo: TReq): Promise<TRes> {
  const res = await fetch(`${API_BASE}${caminho}`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  await assertOk(res);
  return (await res.json()) as TRes;
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/health`);
  await assertOk(res);
  return (await res.json()) as { status: string };
}

export async function postStt(audio: Blob): Promise<STTResponse> {
  const form = new FormData();
  const extensao = audio.type.includes("webm") ? "webm" : "audio";
  form.append("audio", audio, `gravacao.${extensao}`);
  const res = await fetch(`${API_BASE}/api/stt`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  await assertOk(res);
  return (await res.json()) as STTResponse;
}

export interface TtsParams {
  text: string;
  voice_id: string;
  slow: boolean;
}

export async function postTts(params: TtsParams): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/tts`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  await assertOk(res);
  return await res.blob();
}

export async function postConversa(req: ConversaRequest): Promise<ConversaResponse> {
  return postJson<ConversaRequest, ConversaResponse>("/api/conversa", req);
}

export async function postCorrigir(req: CorrigirRequest): Promise<CorrigirResponse> {
  return postJson<CorrigirRequest, CorrigirResponse>("/api/corrigir", req);
}

export interface AvaliarPronunciaRequest {
  esperado: string;
  transcrito: string;
}

export async function postAvaliarPronuncia(
  req: AvaliarPronunciaRequest,
): Promise<AvaliarPronunciaResponse> {
  return postJson<AvaliarPronunciaRequest, AvaliarPronunciaResponse>(
    "/api/avaliar-pronuncia",
    req,
  );
}

export async function getCustos(): Promise<CustosResponse> {
  return getJson<CustosResponse>("/api/custos");
}

export async function getTrilhas(): Promise<Trilha[]> {
  return getJson<Trilha[]>("/api/trilhas");
}

export async function getTrilha(id: string): Promise<Trilha> {
  return getJson<Trilha>(`/api/trilhas/${encodeURIComponent(id)}`);
}
