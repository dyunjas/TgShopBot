import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";

const API_BASE = "/api/superadmin/operators";

const ROLE_LABEL = {
  superadmin: "Суперадмин",
  operator: "Оператор",
};

export default function Operators({ notify }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  const [tgId, setTgId] = useState("");
  const [username, setUsername] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const operators = useMemo(() => rows.filter((x) => x.role === "operator"), [rows]);
  const supers = useMemo(() => rows.filter((x) => x.role === "superadmin"), [rows]);

  async function load() {
    setLoading(true);
    try {
      const data = await api(API_BASE);
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  async function addOperator() {
    const cleanTg = String(tgId || "").replace(/[^\d]/g, "");
    if (!cleanTg) return notify?.("Ошибка", "Введите Telegram ID");

    setSubmitting(true);
    try {
      await api(API_BASE, {
        method: "POST",
        body: {
          tg_id: Number(cleanTg),
          username: username.trim() || null,
        },
      });

      setTgId("");
      setUsername("");
      notify?.("Готово", "Оператор назначен");
      await load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function removeOperator(op) {
    const ok = window.confirm(`Удалить оператора ${op.username || op.tg_id}?`);
    if (!ok) return;

    try {
      await api(`${API_BASE}/${op.id}`, { method: "DELETE" });
      notify?.("Готово", "Оператор удален");
      await load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="grid cols2">
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "baseline" }}>
          <div>
            <h2 style={{ margin: 0 }}>Операторы</h2>
            <div className="muted" style={{ marginTop: 6 }}>
              {loading ? "Загружаю..." : `Операторов: ${operators.length}, супер-админов: ${supers.length}`}
            </div>
          </div>

          <button className="btn" onClick={load} disabled={loading}>
            Обновить
          </button>
        </div>

        <div className="hr" />

        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>TG ID</th>
              <th>Username</th>
              <th>Роль</th>
              <th>Баланс</th>
              <th style={{ width: 180 }} />
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td className="mono">{a.id}</td>
                <td className="mono">{a.tg_id}</td>
                <td>{a.username || "-"}</td>
                <td>
                  <span className={`statusPill ${a.role === "superadmin" ? "info" : "on"}`}>
                    {ROLE_LABEL[a.role] || a.role}
                  </span>
                </td>
                <td className="mono">{a.balance ?? 0}</td>
                <td>
                  {a.role === "operator" ? (
                    <button className="btn danger" onClick={() => removeOperator(a)}>
                      Удалить
                    </button>
                  ) : (
                    <span className="small">Удаление недоступно</span>
                  )}
                </td>
              </tr>
            ))}

            {!loading && rows.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted" style={{ padding: 16 }}>
                  В базе пока нет админ-пользователей.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Назначить оператора</h2>
        <div className="muted" style={{ marginTop: 6 }}>
          Укажите Telegram ID. Если пользователь уже есть в базе, роль будет обновлена до оператора.
        </div>

        <div className="hr" />

        <div className="form">
          <div className="field">
            <label>Telegram ID</label>
            <input
              className="mono"
              value={tgId}
              onChange={(e) => setTgId(e.target.value.replace(/[^\d]/g, ""))}
              placeholder="Пример: 123456789"
            />
          </div>

          <div className="field">
            <label>Username (необязательно)</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Например: my_operator"
            />
          </div>

          <div className="row">
            <button className="btn ok" onClick={addOperator} disabled={submitting || !tgId.trim()}>
              {submitting ? "Назначаю..." : "Назначить оператором"}
            </button>
            <button
              className="btn ghost"
              onClick={() => {
                setTgId("");
                setUsername("");
              }}
              disabled={submitting}
            >
              Очистить
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
