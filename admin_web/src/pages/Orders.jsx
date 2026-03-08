import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import FancySelect from "../components/FancySelect.jsx";

const ORDERS_URL = "/api/admin/my-orders";

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  if (data && Array.isArray(data.rows)) return data.rows;
  return [];
}

function fmtMoney(v) {
  if (v === null || v === undefined) return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return "—";
  return n.toLocaleString();
}

function fmtDate(v) {
  if (!v) return "—";
  try {
    return new Date(v).toLocaleString();
  } catch {
    return "—";
  }
}

const STATUS_LABEL = {
  all: "Все",
  open: "Новый",
  in_work: "В работе",
  done: "Выполнен",
  refunded: "Возврат",
  canceled: "Отменён",
};

const STATUS_BADGE_CLASS = {
  open: "statusBadge open",
  in_work: "statusBadge work",
  done: "statusBadge done",
  refunded: "statusBadge refund",
  canceled: "statusBadge cancel",
};

function statusText(code) {
  return STATUS_LABEL[code] || "—";
}

export default function Orders({ notify }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);

  async function loadOrders() {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set("status", status);
      qs.set("limit", String(limit));
      qs.set("offset", String(offset));

      const data = await api(`${ORDERS_URL}?${qs.toString()}`);
      setOrders(normalizeList(data));
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOrders();
  }, [status, limit, offset]);

  const filteredOrders = useMemo(() => {
    const qq = q.trim().toLowerCase();
    if (!qq) return orders;

    return orders.filter((o) => {
      const hay = [
        o.order_id ?? o.id,
        o.title,
        o.status,
        o.price,
        o.user_tg_id ?? o.tg_id,
        o.executor_name,
        o.created_at,
        o.shop_title,
        o.shop_id,
      ]
        .map((x) => (x === null || x === undefined ? "" : String(x)))
        .join(" ")
        .toLowerCase();

      return hay.includes(qq);
    });
  }, [orders, q]);

  const canNext = !loading && orders.length >= limit;

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0 }}>Заказы</h2>
          <div className="hint" style={{ marginTop: 6 }}>
            {loading ? "Загружаю..." : `Показано: ${filteredOrders.length}`}
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <input
            style={{ minWidth: 260 }}
            placeholder="Поиск по номеру заказа, ID пользователя, названию товара..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />

          <div style={{ minWidth: 220 }}>
            <FancySelect
              value={status}
              onChange={(v) => {
                setOffset(0);
                setStatus(v);
              }}
              options={[
                { value: "all", label: "Все статусы" },
                { value: "open", label: "Новые" },
                { value: "in_work", label: "В работе" },
                { value: "done", label: "Выполненные" },
                { value: "refunded", label: "Возвраты" },
                { value: "canceled", label: "Отменённые" },
              ]}
            />
          </div>

          <div style={{ minWidth: 170 }}>
            <FancySelect
              value={String(limit)}
              onChange={(v) => {
                setOffset(0);
                setLimit(Number(v));
              }}
              options={[
                { value: "20", label: "20 / стр." },
                { value: "50", label: "50 / стр." },
                { value: "100", label: "100 / стр." },
                { value: "200", label: "200 / стр." },
              ]}
            />
          </div>

          <button className="btn" onClick={loadOrders} disabled={loading}>
            Обновить
          </button>
        </div>
      </div>

      <div style={{ marginTop: 16, overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>№ заказа</th>
              <th>Дата</th>
              <th>Статус</th>
              <th>Товар</th>
              <th>Сумма</th>
              <th>Покупатель</th>
              <th>Исполнитель</th>
              <th>Магазин</th>
            </tr>
          </thead>

          <tbody>
            {!loading && filteredOrders.length === 0 && (
              <tr>
                <td colSpan={8} className="hint" style={{ padding: 16 }}>
                  Ничего не найдено
                </td>
              </tr>
            )}

            {filteredOrders.map((o, idx) => {
              const id = o.order_id ?? o.id ?? "—";
              const statusCode = o.status ?? "";
              const badgeCls = STATUS_BADGE_CLASS[statusCode] || "statusBadge";

              return (
                <tr key={`${id}-${idx}`}>
                  <td style={{ fontWeight: 900 }}>{id}</td>
                  <td>{fmtDate(o.created_at ?? o.createdAt)}</td>

                  <td>
                    <span className={badgeCls}>{statusText(statusCode)}</span>
                  </td>

                  <td>{o.title ?? "—"}</td>
                  <td style={{ fontWeight: 800 }}>{fmtMoney(o.price)}</td>
                  <td>{o.user_tg_id ?? o.tg_id ?? "—"}</td>
                  <td>{o.executor_name ?? "—"}</td>
                  <td>
                    {o.shop_title ? `${o.shop_title}` : (o.shop_id ?? "—")}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div className="row" style={{ marginTop: 12, gap: 8 }}>
          <button
            className="btn ghost"
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset <= 0 || loading}
          >
            ← Назад
          </button>

          <button
            className="btn ghost"
            onClick={() => setOffset(offset + limit)}
            disabled={!canNext}
          >
            Вперёд →
          </button>

          <div className="hint" style={{ marginLeft: "auto" }}>
            Страница: <b>{Math.floor(offset / limit) + 1}</b>
          </div>
        </div>
      </div>
    </div>
  );
}
