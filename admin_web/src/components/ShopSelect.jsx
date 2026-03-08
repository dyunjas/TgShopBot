import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import FancySelect from "./FancySelect.jsx";

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  if (data && Array.isArray(data.rows)) return data.rows;
  return [];
}

export default function ShopSelect({
  value,
  onChange,
  notify,
  label = "Магазин",
  allowEmpty = false,
  emptyLabel = "Все магазины",
  showRefresh = true,
}) {
  const [shops, setShops] = useState([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await api("/api/superadmin/shops");
      const list = normalizeList(data);
      setShops(list);
      if (!allowEmpty && !value && list[0]?.id) onChange(String(list[0].id));
    } catch (e) {
      notify?.("Ошибка", e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const options = [
    ...(allowEmpty ? [{ value: "", label: emptyLabel }] : []),
    ...shops.map((s) => ({ value: String(s.id), label: `${s.title} (ID ${s.id})` })),
  ];

  return (
    <div className="field">
      <label>{label}</label>
      {showRefresh ? (
        <div className="row" style={{ gap: 8 }}>
          <FancySelect
            value={value}
            onChange={onChange}
            options={options}
            placeholder={loading ? "Загрузка..." : "Выберите магазин"}
          />
          <button type="button" className="btn ghost sm" onClick={load} disabled={loading}>
            {loading ? "..." : "↻"}
          </button>
        </div>
      ) : (
        <FancySelect
          value={value}
          onChange={onChange}
          options={options}
          placeholder={loading ? "Загрузка..." : "Выберите магазин"}
        />
      )}
    </div>
  );
}
