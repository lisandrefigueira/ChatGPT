import { useRef, useState } from "react";
import { GravadorAudio } from "../audio/recorder";

interface BotaoGravarProps {
  onGravado: (blob: Blob) => void;
  desabilitado?: boolean;
}

/**
 * Botão "segurar para falar": pressiona e segura para gravar, solta para
 * parar e enviar. Funciona com mouse (pointer events) e toque.
 */
export default function BotaoGravar({ onGravado, desabilitado }: BotaoGravarProps) {
  const [gravando, setGravando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const gravadorRef = useRef<GravadorAudio | null>(null);
  const iniciandoRef = useRef(false);

  async function aoPressionar() {
    if (desabilitado || gravando || iniciandoRef.current) return;
    iniciandoRef.current = true;
    setErro(null);
    try {
      const gravador = new GravadorAudio();
      await gravador.iniciar();
      gravadorRef.current = gravador;
      setGravando(true);
    } catch (e) {
      setErro("Não foi possível acessar o microfone.");
      console.error(e);
    } finally {
      iniciandoRef.current = false;
    }
  }

  async function aoSoltar() {
    const gravador = gravadorRef.current;
    if (!gravador || !gravando) return;
    setGravando(false);
    gravadorRef.current = null;
    try {
      const blob = await gravador.parar();
      if (blob.size > 0) {
        onGravado(blob);
      }
    } catch (e) {
      setErro("Falha ao finalizar a gravação.");
      console.error(e);
    }
  }

  function aoCancelar() {
    if (gravadorRef.current && gravando) {
      gravadorRef.current.cancelar();
      gravadorRef.current = null;
      setGravando(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        disabled={desabilitado}
        onPointerDown={aoPressionar}
        onPointerUp={aoSoltar}
        onPointerLeave={aoCancelar}
        onContextMenu={(e) => e.preventDefault()}
        className={`select-none touch-none flex h-16 w-16 items-center justify-center rounded-full text-2xl shadow-lg transition-transform active:scale-95 disabled:opacity-40 ${
          gravando
            ? "bg-red-600 text-white scale-110 animate-pulse"
            : "bg-sky-600 text-white"
        }`}
        aria-pressed={gravando}
        aria-label={gravando ? "Gravando, solte para enviar" : "Segure para falar"}
      >
        {gravando ? "●" : "🎤"}
      </button>
      <span className="text-xs text-slate-500 dark:text-slate-400">
        {gravando ? "Solte para enviar" : "Segure para falar"}
      </span>
      {erro && <span className="text-xs text-red-600 dark:text-red-400">{erro}</span>}
    </div>
  );
}
