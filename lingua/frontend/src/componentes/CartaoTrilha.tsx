import type { Trilha } from "../types";

interface CartaoTrilhaProps {
  trilha: Trilha;
  onSelecionar: () => void;
}

export default function CartaoTrilha({ trilha, onSelecionar }: CartaoTrilhaProps) {
  return (
    <button
      type="button"
      onClick={onSelecionar}
      className="w-full text-left rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 shadow-sm transition hover:shadow-md hover:border-sky-400 dark:hover:border-sky-500"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">{trilha.titulo}</h3>
        <span className="shrink-0 rounded-full bg-sky-100 dark:bg-sky-900 px-2 py-0.5 text-xs font-medium text-sky-700 dark:text-sky-300">
          {trilha.nivel}
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        com {trilha.persona.nome} · {trilha.persona.papel}
      </p>
      <div className="mt-2 flex flex-wrap gap-1">
        {trilha.vocabulario_alvo.slice(0, 4).map((palavra) => (
          <span
            key={palavra}
            className="rounded bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 text-[11px] text-slate-600 dark:text-slate-300"
          >
            {palavra}
          </span>
        ))}
      </div>
    </button>
  );
}
