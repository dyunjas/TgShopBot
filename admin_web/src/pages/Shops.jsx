import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";

const API_BASE = "/api/superadmin/shops"; 

function maskToken(t) {
  if (!t) return "—";
  const s = String(t);
  if (s.length <= 10) return "••••••••••";
  return `${s.slice(0, 6)}••••••••${s.slice(-4)}`;
}

function normalizeChannelId(v) {
  const s = String(v ?? "").trim();
  if (!s) return "";
  const cleaned = s.replace(/[^\d-]/g, "");
  return cleaned;
}

function toChannelIdForApi(v) {
  const s = String(v ?? "").trim();
  if (!s) return 0; 
  const n = Number(s);
  if (!Number.isFinite(n)) return 0;
  return Math.trunc(n);
}

export default function Shops({ notify }) {
  const [shops, setShops] = useState([]);
  const [loading, setLoading] = useState(false);

  const [title, setTitle] = useState("");
  const [token, setToken] = useState("");
  const [reviewsChannelId, setReviewsChannelId] = useState(""); 

  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [editToken, setEditToken] = useState("");
  const [editActive, setEditActive] = useState(true);
  const [editReviewsChannelId, setEditReviewsChannelId] = useState(""); 
  const editingShop = useMemo(
    () => shops.find((s) => Number(s.id) === Number(editingId)) || null,
    [shops, editingId]
  );

  async function load() {
    setLoading(true);
    try {
      const data = await api(API_BASE);
      setShops(Array.isArray(data) ? data : []);
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  function startEdit(s) {
    setEditingId(s.id);
    setEditTitle(s.title || "");
    setEditToken(s.bot_token || "");
    setEditActive(!!s.is_active);

    const cid = s.reviews_channel_id ?? 0;
    setEditReviewsChannelId(cid && Number(cid) !== 0 ? String(cid) : "");
  }

  function stopEdit() {
    setEditingId(null);
    setEditTitle("");
    setEditToken("");
    setEditActive(true);
    setEditReviewsChannelId("");
  }

  async function create() {
    try {
      await api(API_BASE, {
        method: "POST",
        body: {
          title: title.trim(),
          bot_token: token.trim(),
          reviews_channel_id: toChannelIdForApi(reviewsChannelId), 
          is_active: true,
        },
      });
      setTitle("");
      setToken("");
      setReviewsChannelId("");
      notify?.("Готово", "Магазин создан");
      load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function saveEdit() {
    if (!editingId) return;
    try {
      await api(`${API_BASE}/${editingId}`, {
        method: "PATCH",
        body: {
          title: editTitle.trim() || null,
          bot_token: editToken.trim() || null,
          reviews_channel_id: toChannelIdForApi(editReviewsChannelId), 
          is_active: editActive,
        },
      });
      notify?.("Готово", "Изменения сохранены");
      stopEdit();
      load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function toggleShop(s) {
    try {
      const res = await api(`${API_BASE}/${s.id}/toggle`, {
        method: "POST",
        body: { is_active: !s.is_active },
      });
      notify?.("Готово", res?.message || (!s.is_active ? "Магазин включён" : "Магазин выключен"));
      load();
    } catch (e) {
      notify?.("Ошибка", e.message);
    }
  }

  async function removeShop(s) {
    const ok = window.confirm(`Удалить магазин “${s.title}”? Это действие нельзя отменить.`);
    if (!ok) return;

    try {
      const res = await api(`${API_BASE}/${s.id}`, { method: "DELETE" });
      notify?.("Готово", res?.message || "Магазин удалён");
      if (editingId === s.id) stopEdit();
      load();
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
            <h2 style={{ margin: 0 }}>Магазины</h2>
            <div className="muted" style={{ marginTop: 6 }}>
              {loading ? "Загружаю…" : `Всего: ${shops.length}`}
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
              <th>Магазин</th>
              <th>Статус</th>
              <th>Токен</th>
              <th>Канал отзывов</th>
              <th style={{ width: 360 }} />
            </tr>
          </thead>
          <tbody>
            {shops.map((s) => (
              <tr key={s.id}>
                <td className="mono">{s.id}</td>
                <td style={{ fontWeight: 900 }}>{s.title}</td>
                <td>
                  <span className={`statusPill ${s.is_active ? "on" : "off"}`}>
                    {s.is_active ? "Включён" : "Выключен"}
                  </span>
                </td>
                <td className="mono">{maskToken(s.bot_token)}</td>
                <td className="mono">{s.reviews_channel_id && Number(s.reviews_channel_id) !== 0 ? s.reviews_channel_id : "—"}</td>
                <td>
                  <div className="row" style={{ gap: 8 }}>
                    <button className="btn ghost" onClick={() => startEdit(s)}>
                      Изменить
                    </button>

                    <button className="btn" onClick={() => toggleShop(s)}>
                      {s.is_active ? "Остановить" : "Запустить"}
                    </button>

                    <button className="btn danger" onClick={() => removeShop(s)}>
                      Удалить
                    </button>
                  </div>
                </td>
              </tr>
            ))}

            {!loading && shops.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted" style={{ padding: 16 }}>
                  Пока нет магазинов - создайте первый справа
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>{editingId ? "Редактирование магазина" : "Создать магазин"}</h2>
        <div className="muted" style={{ marginTop: 6 }}>
          {editingId ? `ID: ${editingId} • ${editingShop?.title || ""}` : "Введите название, токен и канал отзывов"}
        </div>

        <div className="hr" />

        <div className="form">
          <div className="field">
            <label>Название магазина</label>
            <input
              value={editingId ? editTitle : title}
              onChange={(e) => (editingId ? setEditTitle(e.target.value) : setTitle(e.target.value))}
              placeholder="Пример: Магазин#1"
            />
          </div>

          <div className="field">
            <label>Токен бота</label>
            <input
              value={editingId ? editToken : token}
              onChange={(e) => (editingId ? setEditToken(e.target.value) : setToken(e.target.value))}
              placeholder="123456:ABCDEF..."
            />
            <div className="small">Токен хранится в базе и нужен для запуска бота.</div>
          </div>

          <div className="field">
            <label>ID Telegram канала для отзывов</label>
            <input
              className="mono"
              value={editingId ? editReviewsChannelId : reviewsChannelId}
              onChange={(e) => {
                const v = normalizeChannelId(e.target.value);
                editingId ? setEditReviewsChannelId(v) : setReviewsChannelId(v);
              }}
              placeholder="-1001234567890"
            />
            <div className="small">
              Укажите chat_id канала (обычно начинается с <span className="mono">-100…</span>). Если оставить пустым — отзывы
              публиковаться не будут.
            </div>
          </div>

          {editingId ? (
            <div className="row" style={{ alignItems: "center" }}>
              <button
                className={`btn ${editActive ? "ok" : "ghost"}`}
                onClick={() => setEditActive(!editActive)}
                title="Включить / выключить магазин"
              >
                {editActive ? "Включён" : "Выключен"}
              </button>

              <button className="btn ok" onClick={saveEdit}>
                Сохранить
              </button>

              <button className="btn ghost" onClick={stopEdit}>
                Отмена
              </button>
            </div>
          ) : (
            <button className="btn ok" onClick={create} disabled={!title.trim() || !token.trim()}>
              Создать
            </button>
          )}

          {editingId ? (
            <div className="small" style={{ marginTop: 10 }}>
              Подсказка: “Остановить/Запустить” слева меняет статус магазина. “Перезапуск” доступен только для включённых.
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
