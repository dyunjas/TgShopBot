import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";

const TYPE_OPTIONS = [
  { value: "main_menu", label: "Главное меню" },
  { value: "shop_menu", label: "Магазин — главная (категории)" },

  { value: "faq", label: "FAQ" },
  { value: "reviews", label: "Отзывы" },
  { value: "profile", label: "Профиль" },
  { value: "guarantees", label: "Гарантии" },
  { value: "support", label: "Поддержка" },

  { value: "orders_menu", label: "Заказы — список" },
  { value: "order_item_menu", label: "Заказы — карточка" },

  { value: "transactions_menu", label: "Транзакции — список" },
  { value: "transaction_item_menu", label: "Транзакции — карточка" },

  { value: "promocode_menu", label: "Промокод — ввод" },
  { value: "promocode_error_menu", label: "Промокод — ошибка" },
  { value: "promocode_success_menu", label: "Промокод — успех" },

  { value: "topup_balance_menu", label: "Пополнение — ввод суммы" },
  { value: "choose_payment_menu", label: "Пополнение — выбор платежки" },
  { value: "pally_payment_menu", label: "Пополнение — счёт PALLY" },
  { value: "lava_payment_menu", label: "Пополнение — счёт LAVA" },
  { value: "success_payment_menu", label: "Пополнение — успех" },
];

function isProbablyUrl(v) {
  if (!v) return false;
  return /^https?:\/\//i.test(v.trim());
}

export default function Pages({ notify }) {
  const [shopId, setShopId] = useState("");

  const [pages, setPages] = useState([]);
  const [selectedType, setSelectedType] = useState("main_menu");
  const [current, setCurrent] = useState(null);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [image, setImage] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [sortOrder, setSortOrder] = useState("0");

  const selectedTypeLabel = useMemo(() => {
    return TYPE_OPTIONS.find((x) => x.value === selectedType)?.label ?? selectedType;
  }, [selectedType]);

  async function loadList() {
    if (!shopId) return;
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      const data = await api(`/api/pages?${qs.toString()}`);
      setPages(Array.isArray(data) ? data : []);
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function loadByType() {
    if (!shopId || !selectedType) return;
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId), page_type: selectedType });
      const data = await api(`/api/pages/by-type?${qs.toString()}`);

      setCurrent(data);
      setTitle(data.title || "");
      setContent(data.content || "");
      setImage(data.image || "");
      setIsActive(!!data.is_active);
      setSortOrder(String(data.sort_order ?? 0));

      notify("Готово", `Страница «${selectedTypeLabel}» загружена`);
    } catch (e) {
      setCurrent(null);
      setTitle("");
      setContent("");
      setImage("");
      setIsActive(true);
      setSortOrder("0");
      notify("Страница не найдена", `Можно создать страницу для «${selectedTypeLabel}»`);
    }
  }

  async function create() {
    if (!shopId) return notify("Ошибка", "Выберите магазин");
    if (!content.trim()) return notify("Ошибка", "Введите текст");

    try {
      const data = await api("/api/pages", {
        method: "POST",
        body: {
          shop_id: Number(shopId),
          page_type: selectedType,
          title: title?.trim() ?? "",
          content,
          image: image?.trim() ? image.trim() : null,
          is_active: isActive,
          sort_order: Number(sortOrder || 0),
        },
      });

      notify("Готово", "Страница создана");
      setCurrent(data);
      await loadList();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function update() {
    if (!current?.id) return;
    if (!shopId) return notify("Ошибка", "Выберите магазин");
    if (!content.trim()) return notify("Ошибка", "Введите текст");

    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      const data = await api(`/api/pages/${current.id}?${qs.toString()}`, {
        method: "PATCH",
        body: {
          title: title?.trim() ?? "",
          content,
          image: image?.trim() ? image.trim() : null,
          is_active: isActive,
          sort_order: Number(sortOrder || 0),
        },
      });

      notify("Готово", "Изменения сохранены");
      setCurrent(data);
      await loadList();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function del() {
    if (!current?.id) return;
    if (!shopId) return notify("Ошибка", "Выберите магазин");

    const ok = window.confirm(`Удалить страницу «${selectedTypeLabel}»?`);
    if (!ok) return;

    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      await api(`/api/pages/${current.id}?${qs.toString()}`, { method: "DELETE" });

      notify("Готово", "Страница удалена");
      setCurrent(null);
      setTitle("");
      setContent("");
      setImage("");
      setIsActive(true);
      setSortOrder("0");
      await loadList();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  useEffect(() => {
    loadList();
  }, [shopId]);

  return (
    <div className="grid cols2">
      <div className="card">
        <h2>Страницы магазина</h2>

        <div className="row" style={{ gap: 12, flexWrap: "wrap" }}>
          <div className="field">
            <label>ID магазина</label>
            <input
              value={shopId}
              onChange={(e) => setShopId(e.target.value.replace(/[^\d]/g, ""))}
              placeholder="Пример: 2"
            />
          </div>

          <div className="field" style={{ minWidth: 240 }}>
            <label>Раздел</label>
            <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
              {TYPE_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <button className="btn" onClick={loadList} disabled={!shopId}>
            Обновить список
          </button>
          <button className="btn ok" onClick={loadByType} disabled={!shopId}>
            Открыть раздел
          </button>
        </div>

        <div className="hr" />

        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Раздел</th>
              <th>Заголовок</th>
              <th>Статус</th>
              <th>Порядок</th>
            </tr>
          </thead>
          <tbody>
            {pages.map((p) => {
              const label = TYPE_OPTIONS.find((x) => x.value === p.page_type)?.label ?? p.page_type;
              return (
                <tr key={p.id}>
                  <td className="mono">{p.id}</td>
                  <td>{label}</td>
                  <td>{p.title}</td>
                  <td>{p.is_active ? "Активна" : "Скрыта"}</td>
                  <td className="mono">{p.sort_order}</td>
                </tr>
              );
            })}

            {!pages.length ? (
              <tr>
                <td colSpan={5} className="muted" style={{ padding: 12 }}>
                  Ничего не найдено
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>

        <div className="small" style={{ marginTop: 10, opacity: 0.9 }}>
          Подсказка: выберите «Раздел» и нажмите «Открыть раздел», чтобы редактировать или создать страницу.
        </div>
      </div>

      <div className="card">
        <h2>
          {current ? "Редактирование" : "Новая страница"} — {selectedTypeLabel}
        </h2>

        <div className="form">
          <div className="field">
            <label>Заголовок (необязательно)</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Можно оставить пустым" />
          </div>

          <div className="field">
            <label>Текст страницы</label>
            <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Текст страницы..." />
          </div>

          <div className="row" style={{ gap: 12, flexWrap: "wrap" }}>
            <div className="field" style={{ flex: 1, minWidth: 260 }}>
              <label>Картинка (URL)</label>
              <input value={image} onChange={(e) => setImage(e.target.value)} placeholder="https://..." />

              {isProbablyUrl(image) ? (
                <div style={{ marginTop: 10 }}>
                  <div className="muted" style={{ marginBottom: 6 }}>
                    Превью:
                  </div>
                  <img
                    src={image.trim()}
                    alt="preview"
                    style={{ width: 84, height: 84, objectFit: "cover", borderRadius: 10, display: "block" }}
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                    }}
                    onLoad={(e) => {
                      e.currentTarget.style.display = "block";
                    }}
                  />
                </div>
              ) : null}
            </div>

            <div className="field" style={{ width: 160 }}>
              <label>Порядок</label>
              <input value={sortOrder} onChange={(e) => setSortOrder(e.target.value.replace(/[^\d-]/g, ""))} />
            </div>
          </div>

          <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
            <button className={`btn ${isActive ? "ok" : "ghost"}`} onClick={() => setIsActive(!isActive)}>
              {isActive ? "Показывать пользователям" : "Скрыто от пользователей"}
            </button>

            {!current ? (
              <button className="btn ok" onClick={create} disabled={!shopId || !content.trim()}>
                Создать страницу
              </button>
            ) : (
              <>
                <button className="btn ok" onClick={update} disabled={!shopId || !content.trim()}>
                  Сохранить
                </button>
                <button className="btn danger" onClick={del}>
                  Удалить
                </button>
              </>
            )}
          </div>

          {current?.id ? (
            <div className="small" style={{ marginTop: 10, opacity: 0.85 }}>
              Текущая страница: <span className="mono">#{current.id}</span>
            </div>
          ) : (
            <div className="small" style={{ marginTop: 10, opacity: 0.85 }}>
              Страница для этого раздела ещё не создана.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
