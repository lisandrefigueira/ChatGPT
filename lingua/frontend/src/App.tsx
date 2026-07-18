import { useState } from "react";
import Home from "./telas/Home";
import Dialogo from "./telas/Dialogo";

type EstadoNavegacao =
  | { tela: "home" }
  | { tela: "dialogo"; modo: "trilha"; trilhaId: string }
  | { tela: "dialogo"; modo: "livre" };

export default function App() {
  const [nav, setNav] = useState<EstadoNavegacao>({ tela: "home" });

  if (nav.tela === "dialogo") {
    return (
      <Dialogo
        modoInicial={nav.modo}
        trilhaId={nav.modo === "trilha" ? nav.trilhaId : undefined}
        aoSair={() => setNav({ tela: "home" })}
      />
    );
  }

  return (
    <Home
      onAbrirTrilha={(id) => setNav({ tela: "dialogo", modo: "trilha", trilhaId: id })}
      onConversaLivre={() => setNav({ tela: "dialogo", modo: "livre" })}
    />
  );
}
