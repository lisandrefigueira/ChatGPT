import { useEffect, useState } from "react";
import type { Trilha } from "../types";
import { ApiError, getTrilhas } from "../api";
import { desbloquearAudio } from "../audio/audioUnlock";
import { obterStreak } from "../lib/streak";
import CartaoTrilha from "../componentes/CartaoTrilha";

interface HomeProps {
  onAbrirTrilha: (id: string) => void;
  onConversaLivre: () => void;
}

export default function Home({ onAbrirTrilha, onConversaLivre }: HomeProps) {
  const [trilhas, setTrilhas] = useState<Trilha[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const streak = obterStreak();

  useEffect(() => {
    let cancelado = false;
    getTrilhas()
      .then((lista) => {
        if (!cancelado) setTrilhas(lista);
      })
      .catch((e) => {
        if (cancelado) return;
        console.error(e);
        setErro(e instanceof ApiError ? e.message : "Não foi possível carregar as trilhas.");
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  // IMPORTANTE: desbloquearAudio() precisa rodar de forma síncrona dentro do
  // handler de clique, antes de qualquer chamada assíncrona — é isso que
  // libera o autoplay de áudio no iOS Safari.
  function aoClicarTrilha(id: string) {
    desbloquearAudio();
    onAbrirTrilha(id);
  }

  function aoClicarConversaLivre() {
    desbloquearAudio();
    onConversaLivre();
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-4 py-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Lingua</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">pratique inglês falando</p>
        </div>
        <div className="flex items-center gap-1 rounded-full bg-orange-100 dark:bg-orange-900/40 px-3 py-1.5 text-sm font-medium text-orange-700 dark:text-orange-300">
          🔥 {streak}
        </div>
      </header>

      <button
        type="button"
        onClick={aoClicarConversaLivre}
        className="w-full rounded-xl bg-sky-600 px-4 py-3.5 text-left font-semibold text-white shadow-sm transition hover:bg-sky-700"
      >
        <span className="block text-base">💬 Conversa livre</span>
        <span className="block text-xs font-normal text-sky-100">
          converse sobre qualquer assunto, sem roteiro
        </span>
      </button>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Trilhas guiadas
        </h2>

        {carregando && (
          <p className="text-sm text-slate-500 dark:text-slate-400">Carregando trilhas…</p>
        )}

        {erro && !carregando && (
          <p className="rounded-lg bg-red-50 dark:bg-red-950/40 px-3 py-2 text-sm text-red-600 dark:text-red-400">
            {erro}
          </p>
        )}

        {!carregando && !erro && trilhas.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Nenhuma trilha disponível ainda.
          </p>
        )}

        <div className="flex flex-col gap-3">
          {trilhas.map((trilha) => (
            <CartaoTrilha
              key={trilha.id}
              trilha={trilha}
              onSelecionar={() => aoClicarTrilha(trilha.id)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
