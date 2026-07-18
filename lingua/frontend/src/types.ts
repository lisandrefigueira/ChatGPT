// Espelha backend/schemas.py manualmente — projeto pequeno, sem geração de código.

export type Banda = "verde" | "amarelo" | "vermelho" | "cinza";
export type Nivel = "A2" | "B1" | "B2";
export type Role = "user" | "assistant";

export interface WordTiming {
  word: string;
  start: number;
  end: number;
  confidence?: number | null;
}

export interface STTResponse {
  text: string;
  words: WordTiming[];
  duration: number;
}

export interface Mensagem {
  role: Role;
  content: string;
}

export interface PersonaConfig {
  nome: string;
  papel: string;
  voz: string;
  estilo: string;
}

export interface ConversaRequest {
  mensagens: Mensagem[];
  persona: PersonaConfig;
  nivel: Nivel;
}

export interface ConversaResponse {
  resposta: string;
}

export interface CorrigirRequest {
  fala: string;
  contexto: Mensagem[];
}

export interface CorrigirResponse {
  tem_erro: boolean;
  original: string;
  sugestao: string | null;
  explicacao_pt: string | null;
}

export interface PalavraAvaliada {
  palavra: string;
  esperada: string;
  banda: Banda;
  score: number | null;
}

export interface AvaliarPronunciaResponse {
  palavras: PalavraAvaliada[];
}

export interface CustosResponse {
  tts_chars_mes: number;
  stt_segundos_mes: number;
  llm_tokens_mes: number;
  estimativa_mensal_brl: number;
  alerta_tts: boolean;
}

export interface Persona {
  nome: string;
  papel: string;
  voz: string;
  estilo: string;
}

export interface No {
  id: string;
  fala_ia: string;
  resposta_alvo: string;
  alternativas_aceitas: string[];
  dica_pt: string;
  proximo: Record<string, string>;
}

export interface Trilha {
  id: string;
  titulo: string;
  nivel: Nivel;
  persona: Persona;
  vocabulario_alvo: string[];
  nos: No[];
  modo_livre_seed: string;
}
