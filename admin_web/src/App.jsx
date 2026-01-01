import React, { useEffect, useState } from "react";
import { getToken, clearToken } from "./api.js";

import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";

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

  return (
    <div className="alertOverlay" onMouseDown={onClose}>
      <div className="alertModal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="alertHeader">
          <div className="alertTitle">{toast.title || "Сообщение"}</div>
          <button className="btn ghost sm" onClick={onClose} aria-label="Закрыть">
            ✕
          </button>
        </div>

        <div className="alertBody">{toast.message || "—"}</div>

        <div className="alertActions">
          <button className="btn ok" onClick={onClose}>
            Ок
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
    setToast({ title: String(title ?? "Сообщение"), message: String(message ?? "") });
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
    <>
      {!authed ? (
        <div className="container">
          <Login onAuthed={() => setAuthed(true)} notify={notify} />
        </div>
      ) : (
        <div className="container">
          <Dashboard onLogout={logout} notify={notify} />
        </div>
      )}

      <AlertModal toast={toast} onClose={closeToast} />
    </>
  );
}
