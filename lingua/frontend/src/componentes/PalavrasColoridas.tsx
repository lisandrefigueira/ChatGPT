import { useState } from "react";
import type { Banda, PalavraAvaliada } from "../types";
import { postTts } from "../api";
import { tocarBlobAudio } from "../audio/ttsPlayer";

interface PalavrasColoridasProps {
  palavras: PalavraAvaliada[];
  dicaPt: string;
  vozId: string;
}

const CORES_BANDA: Record<Banda, string> = {
  verde: "text-emerald-700 dark:text-emerald-400",
  amarelo: "text-amber-600 dark:text-amber-400",
  vermelho: "text-red-600 dark:text-red-400",
  cinza: "text-slate-400 dark:text-slate-500",
};

/**
 * Renderiza a transcrição do usuário palavra a palavra, colorida por banda de
 * pronúncia. Tocar em uma palavra amarela/vermelha abre um popover com dica
 * em português e um botão para ouvir a palavra isolada via TTS.
 */
export default function PalavrasColoridas({ palavras, dicaPt, vozId }: PalavrasColoridasProps) {
  const [indiceAberto, setIndiceAberto] = useState<number | null>(null);
  const [carregandoAudio, setCarregandoAudio] = useState(false);

  async function ouvirPalavraIsolada(palavra: string) {
    setCarregandoAudio(true);
    try {
      const blob = await postTts({ text: palavra, voice_id: vozId, slow: true });
      await tocarBlobAudio(blob);
    } catch (e) {
      console.error("Falha ao tocar palavra isolada", e);
    } finally {
      setCarregandoAudio(false);
    }
  }

  return (
    <div className="flex flex-wrap gap-x-1.5 gap-y-1 text-sm leading-relaxed">
      {palavras.map((p, i) => {
        const tocavel = p.banda === "amarelo" || p.banda === "vermelho";
        const aberto = indiceAberto === i;
        return (
          <span key={`${p.palavra}-${i}`} className="relative">
            <span
              role={tocavel ? "button" : undefined}
              tabIndex={tocavel ? 0 : undefined}
              onClick={() => tocavel && setIndiceAberto(aberto ? null : i)}
              className={`${CORES_BANDA[p.banda]} ${
                tocavel ? "cursor-pointer underline decoration-dotted" : ""
              }`}
            >
              {p.palavra}
            </span>
            {aberto && (
              <div className="absolute left-1/2 top-full z-10 mt-1 w-52 -translate-x-1/2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-xs shadow-lg">
                <p className="text-slate-600 dark:text-slate-300">
                  esperado: <span className="font-medium">{p.esperada}</span>
                </p>
                <p className="mt-1 text-slate-500 dark:text-slate-400">{dicaPt}</p>
                <button
                  type="button"
                  disabled={carregandoAudio}
                  onClick={() => ouvirPalavraIsolada(p.esperada)}
                  className="mt-2 rounded bg-sky-600 px-2 py-1 text-[11px] font-medium text-white disabled:opacity-50"
                >
                  🔊 ouvir palavra isolada
                </button>
              </div>
            )}
          </span>
        );
      })}
    </div>
  );
}
