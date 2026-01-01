import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";

function Modal({ title, onClose, children }) {
  return (
    <div className="modalOverlay" onMouseDown={onClose}>
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="modalHeader">
          <div className="modalTitle">{title}</div>
          <button className="btn ghost sm" onClick={onClose}>
            Закрыть
          </button>
        </div>
        <div className="modalBody">{children}</div>
      </div>
    </div>
  );
}

export default function Broadcast({ notify }) {
  const [shopId, setShopId] = useState("");

  const [text, setText] = useState("");
  const [photoId, setPhotoId] = useState("");

  const [mode, setMode] = useState("all"); 
  const [tgIds, setTgIds] = useState("");
  const [lang, setLang] = useState("");
  const [minBalance, setMinBalance] = useState("");
  const [minOrders, setMinOrders] = useState("");

  const [buttons, setButtons] = useState([]);
  const [buttonsPerRow, setButtonsPerRow] = useState(2);

  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerTab, setPickerTab] = useState("categories"); 
  const [pickerBtnText, setPickerBtnText] = useState("");
  const [pickerParentId, setPickerParentId] = useState(""); 
  const [pickerCategoryId, setPickerCategoryId] = useState(""); 
  const [qCat, setQCat] = useState("");
  const [qItem, setQItem] = useState("");

  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [loadingCats, setLoadingCats] = useState(false);
  const [loadingItems, setLoadingItems] = useState(false);

  const [sending, setSending] = useState(false);

  const parsedTgIds = useMemo(() => {
    return tgIds
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => Number(s))
      .filter((n) => Number.isFinite(n) && n > 0);
  }, [tgIds]);

  async function loadCategories() {
    if (!shopId) return;
    try {
      setLoadingCats(true);
      const qs = new URLSearchParams();
      if (qCat.trim()) qs.set("q", qCat.trim());
      if (pickerParentId !== "") qs.set("parent_id", String(pickerParentId));
      qs.set("limit", "120");
      const data = await api(`/api/broadcast/shops/${shopId}/targets/categories?${qs.toString()}`);
      setCategories(Array.isArray(data) ? data : []);
    } catch (e) {
      notify?.("Ошибка", e?.message || String(e));
    } finally {
      setLoadingCats(false);
    }
  }

  async function loadItems() {
    if (!shopId) return;
    try {
      setLoadingItems(true);
      const qs = new URLSearchParams();
      if (qItem.trim()) qs.set("q", qItem.trim());
      if (pickerCategoryId !== "") qs.set("category_id", String(pickerCategoryId));
      qs.set("limit", "120");
      const data = await api(`/api/broadcast/shops/${shopId}/targets/items?${qs.toString()}`);
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      notify?.("Ошибка", e?.message || String(e));
    } finally {
      setLoadingItems(false);
    }
  }

  useEffect(() => {
    if (!pickerOpen || !shopId) return;
    if (pickerTab === "categories") loadCategories();
    if (pickerTab === "items") loadItems();
  }, [pickerOpen, pickerTab]);

  function openPicker(tab) {
    if (!shopId) return notify?.("Ошибка", "Укажитете ID магазина");
    if (!pickerBtnText.trim()) return notify?.("Ошибка", "Введите текст кнопки");
    setPickerTab(tab);
    setPickerOpen(true);
  }

  async function resolveAndAdd(target) {
    try {
      const payload = {
        text: pickerBtnText.trim(),
        target,
      };

      const resolved = await api(`/api/broadcast/shops/${shopId}/buttons/resolve`, {
        method: "POST",
        body: payload,
      });

      setButtons((prev) => [...prev, { text: resolved.text, callback_data: resolved.callback_data }]);

      setPickerOpen(false);
      setPickerBtnText("");
      notify?.("Готово", "Кнопка добавлена");
    } catch (e) {
      notify?.("Ошибка", e?.message || String(e));
    }
  }

  function removeButton(idx) {
    setButtons((prev) => prev.filter((_, i) => i !== idx));
  }

  async function sendBroadcast() {
    if (!shopId) return notify?.("Ошибка", "Укажите ID магазина");
    if (!text.trim()) return notify?.("Ошибка", "Текст рассылки пустой");

    const audience = { mode };

    if (mode === "by_ids") audience.tg_ids = parsedTgIds;

    if (mode === "segment") {
      if (lang.trim()) audience.lang = lang.trim();
      if (minBalance !== "") audience.min_balance = Number(minBalance) || 0;
      if (minOrders !== "") audience.min_orders = Number(minOrders) || 0;
    }

    const payload = {
      text: text.trim(),
      photo_id: photoId.trim() || null,
      audience,
      buttons,
      buttons_per_row: Number(buttonsPerRow) || 2,
      delay_sec: 0.06,
    };

    try {
      setSending(true);
      const res = await api(`/api/broadcast/shops/${shopId}/send`, {
        method: "POST",
        body: payload,
      });

      notify?.("Готово", `Целей: ${res.total_targeted}, отправлено: ${res.sent_ok}`);
    } catch (e) {
      notify?.("Ошибка", e?.message || String(e));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <div className="toolbar">
          <div>
            <h2 style={{ margin: 0 }}>Рассылка</h2>
            <div className="small" style={{ marginTop: 6 }}>
              Создайте сообщение, выберите аудиторию и нажмите «Отправить».
            </div>
          </div>

          <div className="row">
            <button className="btn ok" onClick={sendBroadcast} disabled={sending}>
              {sending ? "Отправка..." : "Отправить"}
            </button>
            <button
              className="btn ghost"
              onClick={() => {
                setText("");
                setPhotoId("");
                setButtons([]);
              }}
              disabled={sending}
            >
              Очистить
            </button>
          </div>
        </div>

        <div className="hr" />

        <div className="grid cols2">
          <div className="field">
            <label>ID магазина</label>
            <input value={shopId} onChange={(e) => setShopId(e.target.value)} placeholder="Пример: 2" />
          </div>

          <div className="field">
            <label>Ссылка на картинку (обязательно)</label>
            <input value={photoId} onChange={(e) => setPhotoId(e.target.value)} placeholder="https://..." />
          </div>

          <div className="field" style={{ gridColumn: "1 / -1" }}>
            <label>Текст</label>
            <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Сообщение рассылки…" />
          </div>
        </div>
      </div>

      <div className="grid cols2">
        <div className="card">
          <div className="panelTitle">Аудитория</div>
          <div className="form">
            <div className="field">
              <label>Режим</label>
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="all">Все</option>
                <option value="by_ids">По ID Telegram</option>
                <option value="segment">Доп. опции</option>
              </select>
            </div>

            {mode === "by_ids" && (
              <div className="field">
                <label>ID Telegram через запятую</label>
                <input value={tgIds} onChange={(e) => setTgIds(e.target.value)} placeholder="123, 456, 789" />
                <div className="small">Найдено ID: {parsedTgIds.length}</div>
              </div>
            )}

            {mode === "segment" && (
              <>
                <div className="field">
                  <label>Язык</label>
                  <input value={lang} onChange={(e) => setLang(e.target.value)} placeholder="ru" />
                </div>
                <div className="row">
                  <div className="field">
                    <label>Мин. баланс</label>
                    <input value={minBalance} onChange={(e) => setMinBalance(e.target.value)} placeholder="0" />
                  </div>
                  <div className="field">
                    <label>Мин. количество заказов</label>
                    <input value={minOrders} onChange={(e) => setMinOrders(e.target.value)} placeholder="1" />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="card">
          <div className="panelTitle">Кнопки</div>

          <div className="kv">
            <div className="small">Текст кнопки</div>
            <input
              value={pickerBtnText}
              onChange={(e) => setPickerBtnText(e.target.value)}
              placeholder="Пример: Открыть товар"
            />

            <div className="small">Кнопок в ряд</div>
            <select value={buttonsPerRow} onChange={(e) => setButtonsPerRow(e.target.value)}>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={4}>4</option>
            </select>
          </div>

          <div className="hr" />

          <div className="row">
            <button className="btn sm" onClick={() => openPicker("categories")}>
              Выбрать категорию
            </button>
            <button className="btn sm" onClick={() => openPicker("items")}>
              Выбрать товар
            </button>

            <button
              className="btn ghost sm"
              onClick={() => resolveAndAdd({ target_type: "main_menu" })}
              disabled={!shopId || !pickerBtnText.trim()}
              title="Системная кнопка"
            >
              Главное меню
            </button>

            <button
              className="btn ghost sm"
              onClick={() => resolveAndAdd({ target_type: "support" })}
              disabled={!shopId || !pickerBtnText.trim()}
              title="Системная кнопка"
            >
              Поддержка
            </button>

          </div>

          <div className="hr" />

          {buttons.length === 0 ? (
            <div className="small">Кнопок нет</div>
          ) : (
            <div className="list">
              {buttons.map((b, i) => (
                <div key={i} className="listItem">
                  <div className="listLeft">
                    <div className="listTitle">{b.text}</div>
                    <div className="listMeta">{b.callback_data}</div>
                  </div>
                  <div className="row">
                    <span className="tag">callback</span>
                    <button className="btn ghost sm" onClick={() => removeButton(i)}>
                      Удалить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {pickerOpen && (
        <Modal
          title={pickerTab === "categories" ? "Выбор категории" : "Выбор товара"}
          onClose={() => setPickerOpen(false)}
        >
          {pickerTab === "categories" && (
            <div className="modalGrid">
              <div className="card" style={{ boxShadow: "none" }}>
                <div className="panelTitle">Категории</div>

                <div className="row">
                  <input value={qCat} onChange={(e) => setQCat(e.target.value)} placeholder="поиск..." />
                  <input
                    value={pickerParentId}
                    onChange={(e) => setPickerParentId(e.target.value)}
                    placeholder="parent_id (опц.)"
                    style={{ maxWidth: 220 }}
                  />
                  <button className="btn sm" onClick={loadCategories} disabled={loadingCats}>
                    {loadingCats ? "..." : "Найти"}
                  </button>
                </div>

                <div className="hr" />

                <div className="list">
                  {categories.map((c) => (
                    <div
                      key={c.id}
                      className="listItem"
                      onClick={() => resolveAndAdd({ target_type: "category", target_id: c.id })}
                      title="Клик — выбрать"
                    >
                      <div className="listLeft">
                        <div className="listTitle">{c.title}</div>
                        <div className="listMeta">id: {c.id} · parent: {c.parent_id ?? "-"}</div>
                      </div>
                      <span className="tag">category</span>
                    </div>
                  ))}
                  {categories.length === 0 && <div className="small">Ничего не найдено</div>}
                </div>
              </div>

              <div className="card" style={{ boxShadow: "none" }}>
                <div className="panelTitle">Что получится</div>
                <div className="small">
                  callback_data будет: <span className="mono">category:&lt;id&gt;</span>
                </div>
              </div>
            </div>
          )}

          {pickerTab === "items" && (
            <div className="modalGrid">
              <div className="card" style={{ boxShadow: "none" }}>
                <div className="panelTitle">Товары</div>

                <div className="row">
                  <input value={qItem} onChange={(e) => setQItem(e.target.value)} placeholder="поиск..." />
                  <input
                    value={pickerCategoryId}
                    onChange={(e) => setPickerCategoryId(e.target.value)}
                    placeholder="category_id (опц.)"
                    style={{ maxWidth: 220 }}
                  />
                  <button className="btn sm" onClick={loadItems} disabled={loadingItems}>
                    {loadingItems ? "..." : "Найти"}
                  </button>
                </div>

                <div className="hr" />

                <div className="list">
                  {items.map((it) => (
                    <div
                      key={it.id}
                      className="listItem"
                      onClick={() => resolveAndAdd({ target_type: "item", target_id: it.id })}
                      title="Клик — выбрать"
                    >
                      <div className="listLeft">
                        <div className="listTitle">{it.title}</div>
                        <div className="listMeta">
                          id: {it.id} · cat: {it.category_id}
                          {it.price != null ? ` · price: ${it.price}` : ""}
                        </div>
                      </div>
                      <span className="tag">item</span>
                    </div>
                  ))}
                  {items.length === 0 && <div className="small">Ничего не найдено</div>}
                </div>
              </div>

              <div className="card" style={{ boxShadow: "none" }}>
                <div className="panelTitle">Что получится</div>
                <div className="small">
                  callback_data будет: <span className="mono">item:&lt;id&gt;</span>
                </div>
              </div>
            </div>
          )}
        </Modal>
      )}
    </div>
  );
}
