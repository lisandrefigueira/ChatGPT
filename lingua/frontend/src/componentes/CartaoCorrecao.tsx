import { useState } from "react";
import type { CorrigirResponse } from "../types";

interface CartaoCorrecaoProps {
  correcao: CorrigirResponse;
}

/** Cartão de correção colapsado por padrão — expandido sob demanda. */
export default function CartaoCorrecao({ correcao }: CartaoCorrecaoProps) {
  const [aberto, setAberto] = useState(false);

  if (!correcao.tem_erro) {
    return (
      <div className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">✓ sem erros notáveis</div>
    );
  }

  return (
    <div className="mt-1 rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 text-xs">
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        className="flex w-full items-center justify-between gap-2 px-2.5 py-1.5 font-medium text-amber-800 dark:text-amber-300"
      >
        <span>💡 sugestão de correção</span>
        <span className="text-[10px]">{aberto ? "ocultar ▲" : "ver ▼"}</span>
      </button>
      {aberto && (
        <div className="space-y-1.5 border-t border-amber-200 dark:border-amber-800 px-2.5 py-2">
          <p className="text-slate-600 dark:text-slate-300">
            <span className="font-medium">Você disse: </span>
            {correcao.original}
          </p>
          {correcao.sugestao && (
            <p className="text-slate-800 dark:text-slate-100">
              <span className="font-medium">Melhor: </span>
              {correcao.sugestao}
            </p>
          )}
          {correcao.explicacao_pt && (
            <p className="text-slate-500 dark:text-slate-400">{correcao.explicacao_pt}</p>
          )}
        </div>
      )}
    </div>
  );
}
