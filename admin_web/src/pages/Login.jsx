import React, { useMemo, useState } from "react";
import { api, setToken } from "../api.js";

export default function Login({ onAuthed, notify }) {
  const [tgId, setTgId] = useState("");
  const [step, setStep] = useState("tg");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);

  const tgOk = useMemo(() => /^\d{5,15}$/.test(tgId), [tgId]);
  const codeOk = useMemo(() => /^[A-Za-z0-9]{4,10}$/.test(code.trim()), [code]);

  async function requestCode() {
    if (!tgOk) return notify?.("Ошибка", "Введите корректный Telegram ID (только цифры).");

    setLoading(true);
    try {
      await api("/api/auth/request-code", {
        method: "POST",
        body: { tg_id: Number(tgId) },
        token: false,
      });
      notify?.("Код отправлен", "Откройте Telegram и найдите сообщение с кодом.");
      setStep("code");
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  async function verify() {
    if (!codeOk) return notify?.("Ошибка", "Введите код из Telegram.");

    setLoading(true);
    try {
      const data = await api("/api/auth/verify", {
        method: "POST",
        body: { tg_id: Number(tgId), code: code.trim() },
        token: false,
      });
      setToken(data.access_token);
      notify?.("Готово", "Вы вошли в админ-панель.");
      onAuthed?.();
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  function onEnter(e, fn) {
    if (e.key === "Enter") fn();
  }

  return (
    <div className="grid cols2">
      <div className="card">
        <div style={{ display: "grid", gap: 6 }}>
          <h2 style={{ margin: 0 }}>Вход</h2>
          <div className="small">Мы отправим код в Telegram. Затем введите его здесь.</div>
        </div>

        <div className="hr" />

        {step === "tg" && (
          <div className="form">
            <div className="field">
              <label>Telegram ID</label>
              <input
                value={tgId}
                inputMode="numeric"
                autoComplete="off"
                onChange={(e) => setTgId(e.target.value.replace(/[^\d]/g, ""))}
                onKeyDown={(e) => onEnter(e, requestCode)}
                placeholder="Пример: 123456789"
              />
              <div className="small">ID - это набор цифр. Если не знаете - напишите администратору.</div>
            </div>

            <div className="row" style={{ justifyContent: "flex-end" }}>
              <button className="btn ok" disabled={loading || !tgOk} onClick={requestCode}>
                {loading ? "Отправляем…" : "Получить код"}
              </button>
            </div>
          </div>
        )}

        {step === "code" && (
          <div className="form">
            <div className="row">
              <div className="field" style={{ minWidth: 260 }}>
                <label>Telegram ID</label>
                <input value={tgId} disabled />
              </div>

              <div className="field" style={{ minWidth: 220 }}>
                <label>Код из Telegram</label>
                <input
                  value={code}
                  autoComplete="one-time-code"
                  onChange={(e) => setCode(e.target.value.trim())}
                  onKeyDown={(e) => onEnter(e, verify)}
                  placeholder="Пример: 123456"
                />
              </div>
            </div>

            <div className="row" style={{ justifyContent: "space-between" }}>
              <button
                className="btn ghost"
                disabled={loading}
                onClick={() => {
                  setStep("tg");
                  setCode("");
                }}
              >
                Изменить ID
              </button>

              <button className="btn ok" disabled={loading || !codeOk} onClick={verify}>
                {loading ? "Проверяем…" : "Войти"}
              </button>
            </div>

            <div className="small">
              Не пришёл код? Проверьте, что вы открыли нужного бота и повторите отправку.
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Как войти</h2>
        <ol style={{ margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
          <li>Введите ваш Telegram ID.</li>
          <li>Нажмите «Получить код».</li>
          <li>Откройте Telegram и скопируйте код.</li>
          <li>Вернитесь сюда и нажмите «Войти».</li>
        </ol>
        <div className="hr" />
        <div className="small">
          Если доступ не выдан - попросите администратора добавить ваш Telegram ID в список сотрудников.
        </div>
      </div>
    </div>
  );
}
