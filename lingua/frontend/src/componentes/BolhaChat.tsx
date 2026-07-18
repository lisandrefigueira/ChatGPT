import type { ReactNode } from "react";
import type { Role } from "../types";

interface BolhaChatProps {
  role: Role;
  children: ReactNode;
  rodape?: ReactNode;
}

export default function BolhaChat({ role, children, rodape }: BolhaChatProps) {
  const isUser = role === "user";
  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
          isUser
            ? "bg-sky-600 text-white rounded-br-sm"
            : "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-sm border border-slate-200 dark:border-slate-700"
        }`}
      >
        <div>{children}</div>
        {rodape && <div className="mt-1.5">{rodape}</div>}
      </div>
    </div>
  );
}
