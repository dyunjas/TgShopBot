import React, { useEffect, useState } from "react";
import { getToken, clearToken } from "./api.js";

import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";

function detectToastTone(title = "", message = "") {
  const s = `${title} ${message}`.toLowerCase();
  if (/(ошиб|error|fail|не удалось|нельзя|forbidden|not found|invalid)/.test(s)) return "error";
  if (/(готово|успех|успеш|saved|created|done|ok|вошли)/.test(s)) return "success";
  if (/(вниман|warning|предупрежд)/.test(s)) return "warn";
  return "info";
}

function toneMeta(tone) {
  if (tone === "error") return { icon: "⨯", actionClass: "btn danger", actionLabel: "Закрыть" };
  if (tone === "success") return { icon: "✓", actionClass: "btn ok", actionLabel: "Понятно" };
  if (tone === "warn") return { icon: "!", actionClass: "btn", actionLabel: "Понятно" };
  return { icon: "i", actionClass: "btn", actionLabel: "Ок" };
}

function AlertModal({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return;

    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toast, onClose]);

  if (!toast) return null;
  const tone = toast.tone || "info";
  const meta = toneMeta(tone);

  return (
    <div className="alertOverlay" onMouseDown={onClose}>
      <div className={`alertModal ${tone}`} onMouseDown={(e) => e.stopPropagation()}>
        <div className="alertHeader">
          <div className="alertTitleWrap">
            <span className={`alertIcon ${tone}`} aria-hidden="true">{meta.icon}</span>
            <div className="alertTitle">{toast.title || "Сообщение"}</div>
          </div>
          <button className="btn ghost sm" onClick={onClose} aria-label="Закрыть">
            ✕
          </button>
        </div>

        <div className="alertBody">{toast.message || "—"}</div>

        <div className="alertActions">
          <button className={meta.actionClass} onClick={onClose}>
            {meta.actionLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [toast, setToast] = useState(null);

  function notify(title, message) {
    const t = String(title ?? "Сообщение");
    const m = String(message ?? "");
    setToast({ title: t, message: m, tone: detectToastTone(t, m) });
  }

  function closeToast() {
    setToast(null);
  }

  function logout() {
    clearToken();
    setAuthed(false);
    notify("Выход", "Вы вышли из панели");
  }

  useEffect(() => {
    setAuthed(!!getToken());
  }, []);

  return (
    <div className="appRoot">
      <div className="appContent">
        {!authed ? (
          <div className="container">
            <Login onAuthed={() => setAuthed(true)} notify={notify} />
          </div>
        ) : (
          <div className="container">
            <Dashboard onLogout={logout} notify={notify} />
          </div>
        )}
      </div>

      <footer className="appFooter">© 2026 DP Shops</footer>

      <AlertModal toast={toast} onClose={closeToast} />
    </div>
  );
}
