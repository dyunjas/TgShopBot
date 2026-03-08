import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import ShopSelect from "../components/ShopSelect.jsx";
import FancySelect from "../components/FancySelect.jsx";

function fmtDate(v) {
  if (!v) return "—";
  try {
    return new Date(v).toLocaleString();
  } catch {
    return "—";
  }
}

function fmtMoney(v) {
  if (v === null || v === undefined) return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return n.toLocaleString();
}

const PAID_LABEL = {
  "": "Все",
  paid: "Только оплаченные",
  unpaid: "Только не оплаченные",
};

export default function Transactions({ notify }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  const [shopId, setShopId] = useState("");
  const [paidFilter, setPaidFilter] = useState("");

  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);

  const qs = useMemo(() => {
    const p = new URLSearchParams();
    p.set("limit", String(limit));
    p.set("offset", String(offset));
    if (shopId) p.set("shop_id", String(shopId));
    if (paidFilter === "paid") p.set("paid", "true");
    if (paidFilter === "unpaid") p.set("paid", "false");
    return p.toString();
  }, [shopId, paidFilter, limit, offset]);

  async function load() {
    setLoading(true);
    try {
      const data = await api(`/api/transactions?${qs}`);
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [qs]);

  const page = Math.floor(offset / limit) + 1;
  const canPrev = offset > 0 && !loading;
  const canNext = !loading && rows.length >= limit;

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0 }}>Платежи</h2>
          <div className="muted" style={{ marginTop: 6 }}>
            {loading ? "Загружаю…" : `Показано: ${rows.length}`}
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div style={{ minWidth: 260 }}>
            <ShopSelect
              value={shopId}
              onChange={(v) => {
                setOffset(0);
                setShopId(v);
              }}
              notify={notify}
              label="Магазин"
              allowEmpty
              emptyLabel="Все магазины"
              showRefresh={false}
            />
          </div>

          <div style={{ minWidth: 220 }}>
            <FancySelect
              value={paidFilter}
              onChange={(v) => {
                setOffset(0);
                setPaidFilter(v);
              }}
              options={[
                { value: "", label: PAID_LABEL[""] },
                { value: "paid", label: PAID_LABEL.paid },
                { value: "unpaid", label: PAID_LABEL.unpaid },
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

          <button className="btn" onClick={load} disabled={loading}>
            Обновить
          </button>
        </div>
      </div>

      <div className="hr" />

      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Сумма</th>
              <th>Статус</th>
              <th>Платёжная система</th>
              <th>Заказ</th>
              <th>Магазин</th>
              <th>Покупатель</th>
              <th>Операция</th>
            </tr>
          </thead>

          <tbody>
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={8} className="muted" style={{ padding: 16 }}>
                  Ничего не найдено
                </td>
              </tr>
            )}

            {rows.map((t) => {
              const paid = !!t.paid;
              const userText = [
                t.user_tg_id ? String(t.user_tg_id) : "",
                t.username ? `@${t.username}` : "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <tr key={t.id}>
                  <td className="mono">{fmtDate(t.created_at)}</td>
                  <td style={{ fontWeight: 900 }}>{fmtMoney(t.amount)}</td>

                  <td>
                    <span className={`statusPill ${paid ? "on" : "off"}`}>
                      {paid ? "Оплачено" : "Не оплачено"}
                    </span>
                    {paid ? (
                      <div className="small" style={{ marginTop: 6 }}>
                        Оплачено: <span className="mono">{fmtDate(t.paid_at)}</span>
                      </div>
                    ) : null}
                  </td>

                  <td>{t.payment_system || "—"}</td>
                  <td className="mono">{t.order_id || "—"}</td>
                  <td className="mono">{t.shop_id ?? "—"}</td>
                  <td className="mono">{userText || "—"}</td>

                  <td className="mono">{t.transaction_id || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="row" style={{ marginTop: 12, gap: 8 }}>
        <button
          className="btn ghost"
          onClick={() => setOffset(Math.max(0, offset - limit))}
          disabled={!canPrev}
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

        <div className="muted" style={{ marginLeft: "auto" }}>
          Страница: <b>{page}</b>
        </div>
      </div>
    </div>
  );
}

