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
    <div className="authWrap">
      <div className="authCard">
        <h2 style={{ margin: 0 }}>Вход в админку</h2>
        <div className="small">Введите Telegram ID и код из бота.</div>

        <div className="form" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Telegram ID</label>
            <input
              value={tgId}
              inputMode="numeric"
              autoComplete="off"
              onChange={(e) => setTgId(e.target.value.replace(/[^\d]/g, ""))}
              onKeyDown={(e) => onEnter(e, step === "tg" ? requestCode : verify)}
              placeholder="123456789"
            />
          </div>

          {step === "code" ? (
            <div className="field">
              <label>Код</label>
              <input
                value={code}
                autoComplete="one-time-code"
                onChange={(e) => setCode(e.target.value.trim())}
                onKeyDown={(e) => onEnter(e, verify)}
                placeholder="Код из Telegram"
              />
            </div>
          ) : null}

          <div className="row" style={{ justifyContent: "space-between" }}>
            {step === "code" ? (
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
            ) : (
              <span />
            )}
            {step === "tg" ? (
              <button className="btn ok" disabled={loading || !tgOk} onClick={requestCode}>
                {loading ? "Отправляем..." : "Отправить код"}
              </button>
            ) : (
              <button className="btn ok" disabled={loading || !codeOk} onClick={verify}>
                {loading ? "Проверяем..." : "Проверить"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
