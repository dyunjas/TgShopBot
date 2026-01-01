import React, { useEffect, useState } from "react";
import { api } from "../api.js";

const ROLE_LABEL = {
  superadmin: "Администратор",
  operator: "Оператор",
};

export default function Profile({ notify }) {
  const [me, setMe] = useState(null);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const a = await api("/api/admin/me");
      const b = await api("/api/admin/balance");
      setMe(a);
      setBalance(b.balance);
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (!me) {
    return (
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Профиль</h2>
        <div className="muted">Загружаю данные…</div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Профиль</h2>

      <div className="row" style={{ marginTop: 8 }}>
        <div className="field">
          <label>Telegram ID</label>
          <div className="mono">{me.tg_id ?? "—"}</div>
        </div>

        <div className="field">
          <label>Имя пользователя</label>
          <div>{me.username || "Не указано"}</div>
        </div>
      </div>

      <div className="row">
        <div className="field">
          <label>Роль</label>
          <div>{ROLE_LABEL[me.role] || "—"}</div>
        </div>

        <div className="field">
          <label>Баланс</label>
          <div style={{ fontWeight: 900 }}>
            {balance ?? me.balance ?? "—"}
          </div>
        </div>
      </div>

      <div className="hr" />

      <button className="btn" onClick={load} disabled={loading}>
        {loading ? "Обновляю…" : "Обновить данные"}
      </button>
    </div>
  );
}
