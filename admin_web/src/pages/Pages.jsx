import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import ShopSelect from "../components/ShopSelect.jsx";
import S3ImagePickerField from "../components/S3ImagePickerField.jsx";
import FancySelect from "../components/FancySelect.jsx";

const TYPE_OPTIONS = [
  { value: "main_menu", label: "Главное меню" },
  { value: "shop_menu", label: "Магазин - главная (категории)" },
  { value: "faq", label: "FAQ" },
  { value: "reviews", label: "Отзывы" },
  { value: "profile", label: "Профиль" },
  { value: "guarantees", label: "Гарантии" },
  { value: "support", label: "Поддержка" },
  { value: "orders_menu", label: "Заказы - список" },
  { value: "order_item_menu", label: "Заказы - карточка" },
  { value: "transactions_menu", label: "Транзакции - список" },
  { value: "transaction_item_menu", label: "Транзакции - карточка" },
  { value: "promocode_menu", label: "Промокод - ввод" },
  { value: "promocode_error_menu", label: "Промокод - ошибка" },
  { value: "promocode_success_menu", label: "Промокод - успех" },
  { value: "topup_balance_menu", label: "Пополнение - ввод суммы" },
  { value: "choose_payment_menu", label: "Пополнение - выбор платежки" },
  { value: "pally_payment_menu", label: "Пополнение - счет PALLY" },
  { value: "lava_payment_menu", label: "Пополнение - счет LAVA" },
  { value: "success_payment_menu", label: "Пополнение - успех" },
];

const PAGE_PLACEHOLDERS = {
  profile: ["{user_id}", "{orders_amount}", "{balance}", "{username}", "{shop_id}"],
  orders_menu: ["{order_title}", "{price}", "{created_at}", "{order_id}"],
  order_item_menu: ["{order_title}", "{price}", "{created_at}", "{order_id}"],
  transactions_menu: ["{amount}", "{created_at}", "{paid_at}", "{status}", "{payment_system}", "{order_id}", "{transaction_id}"],
  transaction_item_menu: ["{amount}", "{created_at}", "{paid_at}", "{status}", "{payment_system}", "{order_id}", "{transaction_id}"],
  promocode_success_menu: ["{amount}"],
};

export default function Pages({ notify }) {
  const [shopId, setShopId] = useState("");

  const [pages, setPages] = useState([]);
  const [selectedType, setSelectedType] = useState("main_menu");
  const [loadingByType, setLoadingByType] = useState(false);
  const [current, setCurrent] = useState(null);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [image, setImage] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [sortOrder, setSortOrder] = useState("0");

  const selectedTypeLabel = useMemo(() => {
    return TYPE_OPTIONS.find((x) => x.value === selectedType)?.label ?? selectedType;
  }, [selectedType]);
  const placeholders = useMemo(() => PAGE_PLACEHOLDERS[selectedType] || [], [selectedType]);

  function resetEditor() {
    setCurrent(null);
    setTitle("");
    setContent("");
    setImage("");
    setIsActive(true);
    setSortOrder("0");
  }

  async function loadList() {
    if (!shopId) {
      setPages([]);
      return;
    }
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId) });
      const data = await api(`/api/pages?${qs.toString()}`);
      setPages(Array.isArray(data) ? data : []);
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  async function loadByType(typeValue = selectedType) {
    if (!shopId || !typeValue) return;
    setLoadingByType(true);
    try {
      const qs = new URLSearchParams({ shop_id: String(shopId), page_type: typeValue });
      const data = await api(`/api/pages/by-type?${qs.toString()}`);

      setSelectedType(typeValue);
      setCurrent(data);
      setTitle(data.title || "");
      setContent(data.content || "");
      setImage(data.image || "");
      setIsActive(!!data.is_active);
      setSortOrder(String(data.sort_order ?? 0));

      const typeLabel = TYPE_OPTIONS.find((x) => x.value === typeValue)?.label ?? typeValue;
      notify("Готово", `Страница «${typeLabel}» загружена`);
    } catch (e) {
      setSelectedType(typeValue);
      resetEditor();
      const typeLabel = TYPE_OPTIONS.find((x) => x.value === typeValue)?.label ?? typeValue;
      notify("Страница не найдена", `Можно создать страницу для «${typeLabel}»`);
    } finally {
      setLoadingByType(false);
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
      resetEditor();
      await loadList();
    } catch (e) {
      notify("Ошибка", e.message);
    }
  }

  useEffect(() => {
    loadList();
    resetEditor();
  }, [shopId]);

  return (
    <div className="grid cols2">
      <div className="card">
        <h2>Страницы магазина</h2>

        <div className="row controlRow" style={{ gap: 12, flexWrap: "wrap" }}>
          <ShopSelect value={shopId} onChange={setShopId} notify={notify} label="Магазин" showRefresh={false} />

          <div className="field" style={{ minWidth: 240 }}>
            <label>Раздел</label>
            <FancySelect
              value={selectedType}
              onChange={setSelectedType}
              options={TYPE_OPTIONS.map((t) => ({ value: t.value, label: t.label }))}
            />
          </div>

          <button className="btn" onClick={loadList} disabled={!shopId}>
            Обновить список
          </button>
          <button className="btn ok" onClick={() => loadByType()} disabled={!shopId || loadingByType}>
            {loadingByType ? "Открываю..." : "Открыть раздел"}
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
              <th style={{ width: 140 }}>Действие</th>
            </tr>
          </thead>
          <tbody>
            {pages.map((p) => {
              const label = TYPE_OPTIONS.find((x) => x.value === p.page_type)?.label ?? p.page_type;
              const isSelected = p.page_type === selectedType;
              return (
                <tr key={p.id} className={isSelected ? "tableRowActive" : ""}>
                  <td className="mono">{p.id}</td>
                  <td>{label}</td>
                  <td>{p.title}</td>
                  <td>{p.is_active ? "Активна" : "Скрыта"}</td>
                  <td className="mono">{p.sort_order}</td>
                  <td>
                    <button className="btn ghost sm" onClick={() => loadByType(p.page_type)} disabled={loadingByType}>
                      Открыть
                    </button>
                  </td>
                </tr>
              );
            })}

            {!pages.length ? (
              <tr>
                <td colSpan={6} className="muted" style={{ padding: 12 }}>
                  Ничего не найдено
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>

        <div className="small" style={{ marginTop: 10, opacity: 0.9 }}>
          Подсказка: можно выбрать раздел в списке и нажать «Открыть», чтобы сразу перейти к редактированию.
        </div>
      </div>

      <div className="card">
        <h2>
          {current ? "Редактирование" : "Новая страница"} - {selectedTypeLabel}
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
          <div className="small" style={{ marginTop: -6, opacity: 0.9 }}>
            Доступные константы для этого раздела:{" "}
            {placeholders.length ? placeholders.map((x) => <code key={x} style={{ marginRight: 8 }}>{x}</code>) : "нет"}
          </div>

          <div className="row" style={{ gap: 12, flexWrap: "wrap" }}>
            <div className="field" style={{ flex: 1, minWidth: 260 }}>
              <S3ImagePickerField
                shopId={shopId}
                entity="categories"
                value={image}
                onChange={setImage}
                notify={notify}
                label="Картинка"
                placeholder="https://..."
              />
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

            <button className="btn ghost" onClick={resetEditor}>
              Очистить форму
            </button>
          </div>

          {current?.id ? (
            <div className="small" style={{ marginTop: 10, opacity: 0.85 }}>
              Текущая страница: <span className="mono">#{current.id}</span>
            </div>
          ) : (
            <div className="small" style={{ marginTop: 10, opacity: 0.85 }}>
              Страница для этого раздела еще не создана.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
