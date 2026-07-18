import { useEffect, useRef, useState } from "react";
import type {
  CorrigirResponse,
  Mensagem,
  Nivel,
  No,
  PalavraAvaliada,
  PersonaConfig,
  Role,
  Trilha,
} from "../types";
import {
  ApiError,
  getTrilha,
  postAvaliarPronuncia,
  postConversa,
  postCorrigir,
  postStt,
  postTts,
} from "../api";
import { tocarBlobAudio } from "../audio/ttsPlayer";
import { registrarPratica } from "../lib/streak";
import BolhaChat from "../componentes/BolhaChat";
import BotaoGravar from "../componentes/BotaoGravar";
import PalavrasColoridas from "../componentes/PalavrasColoridas";
import CartaoCorrecao from "../componentes/CartaoCorrecao";

const NIVEIS: Nivel[] = ["A2", "B1", "B2"];

const PERSONA_PADRAO_LIVRE: PersonaConfig = {
  nome: "Alex",
  papel: "amigo(a) de intercâmbio",
  voz: "en-US-Neural2-F",
  estilo: "casual, paciente e encorajador",
};

let contadorId = 0;
function gerarId(): string {
  contadorId += 1;
  return `item-${Date.now()}-${contadorId}`;
}

interface ItemChat {
  id: string;
  role: Role;
  content: string;
  avaliacao?: PalavraAvaliada[];
  dicaPt?: string;
  correcao?: CorrigirResponse;
}

type Modo = "trilha" | "livre";

interface DialogoProps {
  modoInicial: Modo;
  trilhaId?: string;
  aoSair: () => void;
}

export default function Dialogo({ modoInicial, trilhaId, aoSair }: DialogoProps) {
  const [modo, setModo] = useState<Modo>(modoInicial);
  const [trilha, setTrilha] = useState<Trilha | null>(null);
  const [noAtualId, setNoAtualId] = useState<string | null>(null);
  const [persona, setPersona] = useState<PersonaConfig>(PERSONA_PADRAO_LIVRE);
  const [nivel, setNivel] = useState<Nivel>("B1");
  const [itens, setItens] = useState<ItemChat[]>([]);
  const [processando, setProcessando] = useState(false);
  const [carregandoTrilha, setCarregandoTrilha] = useState(modoInicial === "trilha");
  const [fimTrilha, setFimTrilha] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const fimListaRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (modoInicial !== "trilha" || !trilhaId) return;
    let cancelado = false;
    getTrilha(trilhaId)
      .then((t) => {
        if (cancelado) return;
        setTrilha(t);
        setPersona(t.persona);
        setNivel(t.nivel);
        const primeiroNo = t.nos[0];
        if (primeiroNo) {
          setNoAtualId(primeiroNo.id);
          setItens([{ id: gerarId(), role: "assistant", content: primeiroNo.fala_ia }]);
          tocarResposta(primeiroNo.fala_ia, false, t.persona.voz);
        }
      })
      .catch((e) => {
        if (cancelado) return;
        console.error(e);
        setErro(e instanceof ApiError ? e.message : "Não foi possível carregar a trilha.");
      })
      .finally(() => {
        if (!cancelado) setCarregandoTrilha(false);
      });
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modoInicial, trilhaId]);

  useEffect(() => {
    fimListaRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [itens]);

  async function tocarResposta(texto: string, lenta = false, vozOverride?: string) {
    try {
      const blob = await postTts({ text: texto, voice_id: vozOverride ?? persona.voz, slow: lenta });
      await tocarBlobAudio(blob);
    } catch (e) {
      console.error("Falha ao sintetizar/tocar áudio", e);
    }
  }

  function paraMensagens(lista: ItemChat[]): Mensagem[] {
    return lista.map((i) => ({ role: i.role, content: i.content }));
  }

  async function aoGravar(blob: Blob) {
    setErro(null);
    setProcessando(true);
    try {
      const stt = await postStt(blob);
      const texto = stt.text.trim();
      if (!texto) {
        setProcessando(false);
        return;
      }
      registrarPratica();
      const idItem = gerarId();
      const historicoAntes = itens;
      setItens((prev) => [...prev, { id: idItem, role: "user", content: texto }]);

      if (modo === "trilha") {
        await processarTurnoTrilha(texto, idItem);
      } else {
        await processarTurnoLivre(texto, idItem, historicoAntes);
      }
    } catch (e) {
      console.error(e);
      setErro(e instanceof ApiError ? e.message : "Falha ao processar áudio.");
    } finally {
      setProcessando(false);
    }
  }

  async function processarTurnoTrilha(texto: string, idItem: string) {
    if (!trilha || !noAtualId) return;
    const noAtual = trilha.nos.find((n) => n.id === noAtualId);
    if (!noAtual) return;

    try {
      const avaliacao = await postAvaliarPronuncia({
        esperado: noAtual.resposta_alvo,
        transcrito: texto,
      });
      setItens((prev) =>
        prev.map((it) =>
          it.id === idItem
            ? { ...it, avaliacao: avaliacao.palavras, dicaPt: noAtual.dica_pt }
            : it,
        ),
      );
    } catch (e) {
      console.error("Falha ao avaliar pronúncia", e);
    }

    // Simplificação: sempre segue a chave "padrao" do mapa `proximo` (o
    // roteamento por heurística de conteúdo da resposta está fora do escopo
    // do frontend). Se "padrao" não existir, usa a primeira chave disponível.
    const chaves = Object.keys(noAtual.proximo);
    const proximoId = noAtual.proximo["padrao"] ?? (chaves.length > 0 ? noAtual.proximo[chaves[0]] : undefined);
    const proximoNo: No | undefined = proximoId
      ? trilha.nos.find((n) => n.id === proximoId)
      : undefined;

    if (proximoNo) {
      setNoAtualId(proximoNo.id);
      setItens((prev) => [...prev, { id: gerarId(), role: "assistant", content: proximoNo.fala_ia }]);
      await tocarResposta(proximoNo.fala_ia);
    } else {
      setFimTrilha(true);
    }
  }

  async function processarTurnoLivre(texto: string, idItem: string, historicoAntes: ItemChat[]) {
    const mensagensContexto = paraMensagens(historicoAntes);
    const mensagensParaEnvio: Mensagem[] = [...mensagensContexto, { role: "user", content: texto }];

    try {
      const resposta = await postConversa({ mensagens: mensagensParaEnvio, persona, nivel });
      setItens((prev) => [...prev, { id: gerarId(), role: "assistant", content: resposta.resposta }]);
      void tocarResposta(resposta.resposta);
    } catch (e) {
      console.error("Falha ao obter resposta da conversa", e);
      setErro(e instanceof ApiError ? e.message : "Falha ao obter resposta.");
    }

    // Correção roda em paralelo/assíncrono e não bloqueia a resposta da IA.
    postCorrigir({ fala: texto, contexto: mensagensContexto })
      .then((correcao) => {
        setItens((prev) => prev.map((it) => (it.id === idItem ? { ...it, correcao } : it)));
      })
      .catch((e) => console.error("Falha ao obter correção", e));
  }

  function aoImprovisar() {
    if (!trilha) return;
    setModo("livre");
    setFimTrilha(false);
    setItens((prev) => [
      ...prev,
      { id: gerarId(), role: "assistant", content: trilha.modo_livre_seed },
    ]);
  }

  const emTrilha = modo === "trilha";
  const podeGravar = !processando && !carregandoTrilha && !(emTrilha && fimTrilha) && !(emTrilha && !trilha);

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col bg-slate-50 dark:bg-slate-950">
      <header className="sticky top-0 z-20 flex items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 px-4 py-3 backdrop-blur">
        <button
          type="button"
          onClick={aoSair}
          className="text-sm text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-100"
        >
          ← sair
        </button>
        <div className="flex-1 text-center">
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            {persona.nome} <span className="font-normal text-slate-400">· {persona.papel}</span>
          </p>
          <p className="text-[11px] text-slate-400 dark:text-slate-500">
            {emTrilha ? trilha?.titulo ?? "carregando…" : "conversa livre"}
          </p>
        </div>
        <select
          value={nivel}
          onChange={(e) => setNivel(e.target.value as Nivel)}
          className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-xs font-medium text-slate-700 dark:text-slate-200"
          aria-label="Nível"
        >
          {NIVEIS.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </header>

      <main className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {carregandoTrilha && (
          <p className="text-center text-sm text-slate-500 dark:text-slate-400">
            Carregando trilha…
          </p>
        )}

        {itens.map((item) => (
          <BolhaChat key={item.id} role={item.role}>
            {item.avaliacao ? (
              <PalavrasColoridas
                palavras={item.avaliacao}
                dicaPt={item.dicaPt ?? ""}
                vozId={persona.voz}
              />
            ) : (
              <span>{item.content}</span>
            )}
            {item.role === "assistant" && (
              <RodapeAssistente onOuvirLento={() => tocarResposta(item.content, true)} />
            )}
            {item.role === "user" && item.correcao && <CartaoCorrecao correcao={item.correcao} />}
          </BolhaChat>
        ))}

        {emTrilha && fimTrilha && (
          <div className="rounded-xl border border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/40 p-3 text-center text-sm text-emerald-700 dark:text-emerald-300">
            🎉 Trilha concluída! Volte para casa ou continue conversando livremente.
          </div>
        )}

        {erro && (
          <p className="rounded-lg bg-red-50 dark:bg-red-950/40 px-3 py-2 text-center text-xs text-red-600 dark:text-red-400">
            {erro}
          </p>
        )}

        <div ref={fimListaRef} />
      </main>

      <footer className="sticky bottom-0 flex flex-col items-center gap-3 border-t border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 px-4 py-4 backdrop-blur">
        {emTrilha && !fimTrilha && trilha && (
          <button
            type="button"
            onClick={aoImprovisar}
            className="text-xs font-medium text-sky-600 dark:text-sky-400 underline"
          >
            improvisar daqui →
          </button>
        )}
        <BotaoGravar onGravado={aoGravar} desabilitado={!podeGravar} />
      </footer>
    </div>
  );
}

function RodapeAssistente({ onOuvirLento }: { onOuvirLento: () => void }) {
  return (
    <button
      type="button"
      onClick={onOuvirLento}
      className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
      aria-label="Ouvir devagar"
      title="Ouvir devagar"
    >
      🐢 devagar
    </button>
  );
}
