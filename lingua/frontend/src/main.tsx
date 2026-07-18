import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Registra o service worker (cache de shell apenas — áudio/API nunca é
// cacheado, ver public/sw.js).
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((erro) => {
      console.warn("Falha ao registrar service worker", erro);
    });
  });
}
